#!/usr/bin/env python3
"""Portable behavior checks (no Cursor install required)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apply_patch import (  # noqa: E402
    FORBIDDEN_MARKERS,
    ITERATOR_UPGRADES,
    LR_NEW,
    REPLACEMENTS,
    WORD_NEW,
    patch_input_bundle,
)


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
        WORD_NEW
        + r"""
const s = "hello 안녕하세요 world";
const path = [];
let p = s.length;
for (let i = 0; i < 3 && p > 0; i++) {
  p = l(s, p);
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


def test_hangul_display_width() -> None:
    out = run_node(
        r"""
function cw(t) {
  const e = t.codePointAt(0);
  if (e == null) return 1;
  if (/\p{Mn}|\p{Me}|\p{Cf}/u.test(t)) return 0;
  if (e >= 8203 && e <= 8205 || e === 65279) return 0;
  return e >= 4352 && e <= 4447 || e >= 11904 && e <= 40959 || e >= 44032 && e <= 55215 ||
    e >= 63744 && e <= 64255 || e >= 65072 && e <= 65103 || e >= 65280 && e <= 65376 ||
    e >= 65504 && e <= 65510 || e >= 127744 && e <= 129535 ? 2 : 1;
}
let w = 0;
for (const ch of "안녕") w += cw(ch);
console.log(String(w));
"""
    )
    assert int(out) == 4, out


def test_patcher_has_no_ime_cursor_hack() -> None:
    text = (ROOT / "apply_patch.py").read_text()
    for marker in FORBIDDEN_MARKERS:
        assert marker not in text, f"apply_patch.py still contains {marker!r}"
    assert "def patch_6260" not in text
    assert "log-update.js" not in text
    assert "e.write(" not in text
    assert "upFromBottom" not in text
    assert "[Symbol.iterator]().next()" in LR_NEW
    assert all(old in text for old, _new in ((u[1], u[2]) for u in ITERATOR_UPGRADES))


def test_grapheme_steps() -> None:
    out = run_node(
        r"""
function next(t, e) {
  const g = new Intl.Segmenter(void 0, { granularity: "grapheme" });
  const s = g.segment(t.slice(e))[Symbol.iterator]().next().value;
  return e + (s ? s.segment.length : 1);
}
function prev(t, e) {
  if (e <= 0) return 0;
  const g = new Intl.Segmenter(void 0, { granularity: "grapheme" });
  let p = 0;
  for (const s of g.segment(t.slice(0, e))) p = s.index;
  return p;
}
const t = "a👍한";
console.log(JSON.stringify({
  next0: next(t, 0),
  nextA: next(t, 1),
  prevEnd: prev(t, t.length),
  prevHan: prev(t, prev(t, t.length)),
}));
"""
    )
    got = json.loads(out)
    assert got["next0"] == 1, got
    assert got["nextA"] == 3, got  # thumbs-up is two UTF-16 units
    assert got["prevEnd"] == 3, got
    assert got["prevHan"] == 1, got


def test_iterator_upgrade_on_old_patch() -> None:
    stub = (
        "__wordSeg granularity:\"grapheme\" n.backspace&&B>0){const __g= function __cw( \\p{Mn}|\\p{Me}|\\p{Cf}"
        "__g.segment(__rest).next().value"
        "__g.segment(J.slice(B)).next().value"
    )
    updated, applied = patch_input_bundle(stub)
    assert "grapheme iterator (right)" in applied
    assert "grapheme iterator (delete)" in applied
    assert ".segment(__rest).next()" not in updated
    assert "[Symbol.iterator]().next()" in updated


def test_apply_on_fixture_is_unique_and_valid_js() -> None:
    pieces = ["exports.id=4794;exports.modules={};"]
    for _label, old, _new, _already in REPLACEMENTS:
        pieces.append(old)
    fixture = "".join(pieces)
    updated, applied = patch_input_bundle(fixture)
    assert applied == [label for label, *_ in REPLACEMENTS], applied
    for marker in FORBIDDEN_MARKERS:
        assert marker not in updated
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(updated)
        path = f.name
    try:
        subprocess.check_call(["node", "--check", path])
    finally:
        Path(path).unlink(missing_ok=True)


def test_latest_backup_prefers_newest() -> None:
    import apply_patch as ap

    tmp = Path(tempfile.mkdtemp())
    backup_dir = tmp / "backups"
    backup_dir.mkdir()
    target = tmp / "2026.08.11-e8db854" / "4794.index.js"
    target.parent.mkdir()
    target.write_text("patched")
    older = backup_dir / "4794.index.js.20200101-000000.bak"
    newer = backup_dir / "2026.08.11-e8db854-4794.index.js.20260821-000000-1.bak"
    older.write_text("old-original")
    newer.write_text("__wordSeg patched")
    previous = ap.BACKUP_DIR
    ap.BACKUP_DIR = backup_dir
    try:
        got = ap.latest_backup_for(target)
        assert got == older, got
    finally:
        ap.BACKUP_DIR = previous
        shutil.rmtree(tmp, ignore_errors=True)


def test_restore_rejects_dry_run_combo() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "apply_patch.py"), "--restore", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "use --restore or --dry-run" in result.stderr + result.stdout


def test_repo_privacy() -> None:
    # Concatenate so this file does not embed full forbidden tokens as literals.
    forbidden = (
        "crsr" + "_",
        "Bear" + "er ",
        "sk-" + "ant-",
        "sk-" + "proj-",
        "test1234" + "!",
        "/Users/" + "yoyo/",
    )
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".bak":
            raise AssertionError(f"do not ship backups: {path}")
        if path.name == Path(__file__).name:
            continue
        if path.suffix not in {".py", ".md", ".txt", ".gitignore"} and path.name != "LICENSE":
            continue
        text = path.read_text(errors="ignore")
        for needle in forbidden:
            assert needle not in text, f"{path.name} contains sensitive marker"


if __name__ == "__main__":
    test_word_boundaries()
    test_thai_width()
    test_hangul_display_width()
    test_patcher_has_no_ime_cursor_hack()
    test_grapheme_steps()
    test_iterator_upgrade_on_old_patch()
    test_apply_on_fixture_is_unique_and_valid_js()
    test_latest_backup_prefers_newest()
    test_restore_rejects_dry_run_combo()
    test_repo_privacy()
    print("ok")
    sys.exit(0)
