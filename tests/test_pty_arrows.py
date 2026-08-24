#!/usr/bin/env python3
"""Drive the Cursor CLI (`agent`) TUI over a PTY and locate the inverse caret."""
from __future__ import annotations

import errno
import fcntl
import os
import pty
import select
import shutil
import signal
import struct
import termios
import time

ROWS, COLS = 24, 100


class TinyVT:
    def __init__(self, rows: int = ROWS, cols: int = COLS) -> None:
        self.rows = rows
        self.cols = cols
        self.row = 0
        self.col = 0
        self.inverse = False
        self.cells = [[" "] * cols for _ in range(rows)]
        self.flags = [[False] * cols for _ in range(rows)]
        self._esc = ""

    def _put(self, ch: str) -> None:
        if ch == "\n":
            self.row = min(self.rows - 1, self.row + 1)
            self.col = 0
            return
        if ch == "\r":
            self.col = 0
            return
        if ch == "\b":
            self.col = max(0, self.col - 1)
            return
        if self.row >= self.rows or self.col >= self.cols:
            return
        self.cells[self.row][self.col] = ch
        self.flags[self.row][self.col] = self.inverse
        self.col += 1
        if self.col >= self.cols:
            self.col = 0
            self.row = min(self.rows - 1, self.row + 1)

    def _csi(self, body: str, cmd: str) -> None:
        if body[:1] in "?>=":
            return
        nums = [int(p) if p else 0 for p in body.split(";")] if body else []
        n = nums[0] if nums else 0
        if cmd == "H" or cmd == "f":
            r = (nums[0] - 1) if nums and nums[0] else 0
            c = (nums[1] - 1) if len(nums) > 1 and nums[1] else 0
            self.row = min(max(0, r), self.rows - 1)
            self.col = min(max(0, c), self.cols - 1)
        elif cmd == "A":
            self.row = max(0, self.row - (n or 1))
        elif cmd == "B":
            self.row = min(self.rows - 1, self.row + (n or 1))
        elif cmd == "C":
            self.col = min(self.cols - 1, self.col + (n or 1))
        elif cmd == "D":
            self.col = max(0, self.col - (n or 1))
        elif cmd == "G":
            self.col = min(max(0, (n or 1) - 1), self.cols - 1)
        elif cmd == "J":
            mode = n
            if mode in (0, 2, 3):
                start = 0 if mode else self.row
                for r in range(start, self.rows):
                    c0 = self.col if (mode == 0 and r == self.row) else 0
                    for c in range(c0, self.cols):
                        self.cells[r][c] = " "
                        self.flags[r][c] = False
                if mode in (2, 3):
                    self.row = 0
                    self.col = 0
        elif cmd == "K":
            c0 = 0 if n == 1 else self.col
            c1 = self.col + 1 if n == 1 else self.cols
            if n == 2:
                c0, c1 = 0, self.cols
            for c in range(c0, c1):
                self.cells[self.row][c] = " "
                self.flags[self.row][c] = False
        elif cmd == "m":
            vals = nums or [0]
            if 0 in vals or 27 in vals:
                self.inverse = False
            if 7 in vals:
                self.inverse = True

    def feed(self, data: str) -> None:
        i = 0
        buf = self._esc + data
        self._esc = ""
        while i < len(buf):
            ch = buf[i]
            if ch == "\x1b":
                if i + 1 >= len(buf):
                    self._esc = buf[i:]
                    return
                nxt = buf[i + 1]
                if nxt == "[":
                    j = i + 2
                    while j < len(buf) and buf[j] in "0123456789;?>=:":
                        j += 1
                    if j >= len(buf):
                        self._esc = buf[i:]
                        return
                    self._csi(buf[i + 2 : j], buf[j])
                    i = j + 1
                    continue
                if nxt == "]":
                    j = i + 2
                    while j < len(buf) and buf[j] not in "\x07":
                        if buf[j] == "\x1b" and j + 1 < len(buf) and buf[j + 1] == "\\":
                            j += 2
                            break
                        j += 1
                    else:
                        if j >= len(buf):
                            self._esc = buf[i:]
                            return
                        j += 1
                    i = j
                    continue
                i += 2
                continue
            if ch == "\x9b":
                i += 1
                continue
            self._put(ch)
            i += 1

    def lines(self) -> list[str]:
        return ["".join(row).rstrip() for row in self.cells]

    def inverse_chars(self) -> list[tuple[int, int, str]]:
        out = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.flags[r][c]:
                    out.append((r, c, self.cells[r][c]))
        return out

    def prompt_caret(self) -> str | None:
        """Prompt line with | immediately before the first inverse cell."""
        for r, line in enumerate(self.lines()):
            if "안녕" not in line and "hello" not in line:
                continue
            marks = [c for rr, c, _ch in self.inverse_chars() if rr == r]
            raw = "".join(self.cells[r])
            if not marks:
                return raw.rstrip()
            c0 = min(marks)
            return (raw[:c0] + "|" + raw[c0:]).rstrip()
        return None


def set_winsize(fd: int, rows: int = ROWS, cols: int = COLS) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


def run_agent_keys(text: str, keys: bytes, wait_s: float = 6.0) -> TinyVT:
    agent = shutil.which("agent")
    if not agent:
        raise FileNotFoundError("agent not on PATH")
    pid, fd = pty.fork()
    if pid == 0:
        set_winsize(0)
        os.chdir("/tmp")
        os.environ["TERM"] = "xterm-256color"
        os.environ["COLORTERM"] = "truecolor"
        os.environ["FORCE_COLOR"] = "1"
        os.environ.pop("NO_COLOR", None)
        os.execvp(agent, [agent, "--trust", "-f", "--mode", "ask"])
    set_winsize(fd)
    vt = TinyVT()

    def drain(timeout: float) -> None:
        end = time.time() + timeout
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.05)
            if fd not in r:
                continue
            try:
                chunk = os.read(fd, 65536)
            except OSError as exc:
                if exc.errno == errno.EIO:
                    break
                raise
            if not chunk:
                break
            vt.feed(chunk.decode("utf-8", "replace"))
            end = time.time() + 0.2

    try:
        drain(wait_s)
        os.write(fd, text.encode())
        drain(1.2)
        os.write(fd, keys)
        drain(1.0)
    finally:
        try:
            os.kill(pid, signal.SIGINT)
        except OSError:
            pass
        time.sleep(0.2)
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
    return vt


def test_pty_option_left_stops_on_hangul() -> None:
    sample = "hello 안녕하세요"
    vt = run_agent_keys(sample, b"\x1b[1;3D")
    caret = vt.prompt_caret()
    joined = "\n".join(vt.lines())
    assert "안녕" in joined or (caret and "안녕" in caret), joined[-1500:]
    if caret is None:
        raise AssertionError("no inverse caret on prompt line:\n" + joined[-1500:])
    # Option+Left from end should land at the start of 안녕하세요, not skip it.
    assert "hello |안" in caret, caret


def test_pty_plain_left_moves_one_hangul() -> None:
    sample = "hello 안녕하세요"
    vt = run_agent_keys(sample, b"\x1b[D")
    caret = vt.prompt_caret()
    assert caret is not None, "\n".join(vt.lines())[-1500:]
    assert "세|요" in caret or "하세|요" in caret or "|요" in caret, caret


if __name__ == "__main__":
    test_pty_option_left_stops_on_hangul()
    test_pty_plain_left_moves_one_hangul()
    print("pty ok")
