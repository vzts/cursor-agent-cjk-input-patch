#!/usr/bin/env python3
"""Portable behavior checks (no Cursor install required)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_node(script: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as f:
        f.write(script)
        path = f.name
    try:
        out = subprocess.check_output(["node", path], text=True)
    finally:
        Path(path).unlink(missing_ok=True)
    return out.strip()


def test_word_boundaries() -> None:
    out = run_node(
        r"""
const seg = new Intl.Segmenter(undefined, { granularity: "word" });
function starts(t) {
  return [...seg.segment(t)].filter((s) => s.isWordLike).map((s) => s.index);
}
function left(t, e) {
  if (e <= 0) return 0;
  let o = 0;
  for (const s of starts(t)) {
    if (!(s < e)) break;
    o = s;
  }
  return o;
}
const s = "hello 안녕하세요 world";
const path = [];
let p = s.length;
for (let i = 0; i < 3 && p > 0; i++) {
  p = left(s, p);
  path.push(s.slice(0, p) + "|" + s.slice(p));
}
console.log(JSON.stringify(path));
"""
    )
    expected = [
        "hello 안녕하세요 |world",
        "hello |안녕하세요 world",
        "|hello 안녕하세요 world",
    ]
    got = json.loads(out)
    assert got == expected, got


def test_thai_width() -> None:
    out = run_node(
        r"""
function cw(t) {
  const e = t.codePointAt(0);
  if (e == null) return 1;
  if (/\p{Mn}|\p{Me}|\p{Cf}/u.test(t)) return 0;
  return 1;
}
const thai = "ที่นี่จ้า";
let w = 0;
for (const ch of thai) w += cw(ch);
console.log(String(w));
"""
    )
    assert int(out) == 4, out


def test_repo_privacy() -> None:
    root = Path(__file__).resolve().parents[1]
    forbidden = ("crsr_", "Bearer ", "sk-ant-", "sk-proj-", "test1234!", "/Users/yoyo/")
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".bak":
            raise AssertionError(f"do not ship backups: {path}")
        if path.suffix not in {".py", ".md", ".txt", ".gitignore"} and path.name != "LICENSE":
            continue
        text = path.read_text(errors="ignore")
        for needle in forbidden:
            assert needle not in text, f"{path.name} contains {needle!r}"


if __name__ == "__main__":
    test_word_boundaries()
    test_thai_width()
    test_repo_privacy()
    print("ok")
    sys.exit(0)
