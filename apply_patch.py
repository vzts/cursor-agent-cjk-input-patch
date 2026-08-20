#!/usr/bin/env python3
"""Apply unofficial CJK input patches to a local Cursor Agent CLI install.

Patches only the text-input bundle (word / grapheme / display-width).
Does not touch Ink log-update or move the real terminal cursor.

Does not redistribute Cursor binaries. See README.md.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

BACKUP_DIR = Path.home() / ".local/share/cursor-agent-cjk-input-patch" / "backups"
DEFAULT_VERSIONS = Path.home() / ".local/share/cursor-agent" / "versions"
WORKER_VERSIONS = (
    Path.home()
    / "Library/Application Support/Cursor/User/globalStorage"
    / "anysphere.cursor-agent-worker/agent-cli/.local/share/cursor-agent/versions"
)
REINSTALL_HINT = "curl https://cursor.com/install -fsS | bash"

# Unique original snippets from agent 2026.08.11-e8db854 `4794.index.js`.
# If Cursor remintifies these, the patcher must fail closed rather than guess.
WORD_OLD = (
    "function c(t){return/[A-Za-z0-9_]/.test(t)}function i(t){return/\\s/.test(t)}"
    "function u(t,e){let n=e;const r=\"\\n\"===t[n]&&(0===n||\"\\n\"===t[n-1]);"
    "if(n<t.length&&c(t[n]))for(;n<t.length&&c(t[n]);)n++;else r&&n++;"
    "for(;n<t.length&&!c(t[n]);){if(\"\\n\"===t[n]&&(0===n||\"\\n\"===t[n-1]))return n;"
    "if(\"\\n\"===t[n]&&n+1<t.length&&\"\\n\"===t[n+1])return n+1;n++}"
    "return Math.min(t.length,Math.max(0,n))}function l(t,e){let n=e;if(n<=0)return 0;"
    "for(n--;n>0&&!c(t[n]);){if(\"\\n\"===t[n]&&n>0&&\"\\n\"===t[n-1])return n;n--}"
    "for(;n>0&&c(t[n-1]);)n--;return n}"
)
WORD_NEW = (
    "function c(t){return/[A-Za-z0-9_]/.test(t)}function i(t){return/\\s/.test(t)}"
    "const __wordSeg=new Intl.Segmenter(void 0,{granularity:\"word\"});"
    "function __wordStarts(t){const e=[];for(const n of __wordSeg.segment(t))"
    "n.isWordLike&&e.push(n.index);return e}"
    "function u(t,e){let n=e;const r=\"\\n\"===t[n]&&(0===n||\"\\n\"===t[n-1]);"
    "if(r){n++;const o=__wordStarts(t);for(const s of o)if(s>=n)return s;"
    "return Math.min(t.length,Math.max(0,n))}const o=__wordStarts(t);"
    "for(const s of o)if(s>e)return s;for(let r=e;r<t.length;r++){"
    "if(\"\\n\"===t[r]&&(0===r||\"\\n\"===t[r-1]))return r;"
    "if(\"\\n\"===t[r]&&r+1<t.length&&\"\\n\"===t[r+1])return r+1}return t.length}"
    "function l(t,e){if(e<=0)return 0;let n=e-1;for(;n>0&&\"\\n\"===t[n];){"
    "if(\"\\n\"===t[n-1])return n;n--}const r=__wordStarts(t);let o=0;"
    "for(const s of r){if(!(s<e))break;o=s}return o}"
)

LR_OLD = "if(n.leftArrow)v&&Nt--;else if(n.rightArrow)v&&Nt++;"
LR_NEW = (
    "if(n.leftArrow){if(v&&Nt>0){const __g=new Intl.Segmenter(void 0,{granularity:\"grapheme\"});"
    "let __p=0;for(const __s of __g.segment(Ut.slice(0,Nt)))__p=__s.index;Nt=__p}}"
    "else if(n.rightArrow){if(v&&Nt<Ut.length){const __g=new Intl.Segmenter(void 0,{granularity:\"grapheme\"});"
    "const __rest=Ut.slice(Nt);const __s=__g.segment(__rest)[Symbol.iterator]().next().value;"
    "Nt+=__s?__s.segment.length:1}}"
)

BS_OLD = (
    "else n.backspace&&B>0?(Ut=J.slice(0,B-1)+J.slice(B,J.length),Nt--)"
    ":n.delete&&B<J.length&&(Ut=J.slice(0,B)+J.slice(B+1,J.length))"
)
BS_NEW = (
    "else if(n.backspace&&B>0){const __g=new Intl.Segmenter(void 0,{granularity:\"grapheme\"});"
    "let __p=0;for(const __s of __g.segment(J.slice(0,B)))__p=__s.index;"
    "Ut=J.slice(0,__p)+J.slice(B);Nt=__p}"
    "else if(n.delete&&B<J.length){const __g=new Intl.Segmenter(void 0,{granularity:\"grapheme\"});"
    "const __s=__g.segment(J.slice(B))[Symbol.iterator]().next().value;const __n=B+(__s?__s.segment.length:1);"
    "Ut=J.slice(0,B)+J.slice(__n);Nt=B}"
)

NAV_OLD = (
    "function o(t,e){if(-1===t.indexOf(\"\\n\"))return null;const n=Math.min(Math.max(0,e),t.length),"
    "r=n<=0?-1:t.lastIndexOf(\"\\n\",n-1);if(-1===r)return null;const o=t.lastIndexOf(\"\\n\",Math.max(0,r-1)),"
    "s=-1===o?0:o+1,c=n-(r+1),i=r-s;return s+Math.min(c,i)}"
    "function s(t,e){if(-1===t.indexOf(\"\\n\"))return null;const n=Math.min(Math.max(0,e),t.length),"
    "r=t.indexOf(\"\\n\",n);if(-1===r)return null;const o=n<=0?-1:t.lastIndexOf(\"\\n\",n-1),"
    "s=n-(-1===o?0:o+1),c=r+1,i=t.indexOf(\"\\n\",c),u=(-1===i?t.length:i)-c;return c+Math.min(s,u)}"
)
NAV_NEW = (
    "function __cw(t){const e=t.codePointAt(0);if(null==e)return 1;"
    "if(/\\p{Mn}|\\p{Me}|\\p{Cf}/u.test(t))return 0;"
    "if(e>=8203&&e<=8205||65279===e)return 0;"
    "return e>=4352&&e<=4447||e>=11904&&e<=40959||e>=44032&&e<=55215||e>=63744&&e<=64255||"
    "e>=65072&&e<=65103||e>=65280&&e<=65376||e>=65504&&e<=65510||e>=127744&&e<=129535?2:1}"
    "function __col(t,e,n){let r=0;for(let o=e;o<n;){const e=t.codePointAt(o);if(null==e)break;"
    "r+=__cw(String.fromCodePoint(e));o+=e>65535?2:1}return r}"
    "function __atCol(t,e,n,r){let o=0,s=e;for(;s<n;){const e=t.codePointAt(s);if(null==e)break;"
    "const n=__cw(String.fromCodePoint(e)),c=e>65535?2:1;if(o+n>r)break;o+=n;s+=c}return s}"
    "function o(t,e){if(-1===t.indexOf(\"\\n\"))return null;const n=Math.min(Math.max(0,e),t.length),"
    "r=n<=0?-1:t.lastIndexOf(\"\\n\",n-1);if(-1===r)return null;const s=t.lastIndexOf(\"\\n\",Math.max(0,r-1)),"
    "c=-1===s?0:s+1,i=__col(t,r+1,n);return __atCol(t,c,r,i)}"
    "function s(t,e){if(-1===t.indexOf(\"\\n\"))return null;const n=Math.min(Math.max(0,e),t.length),"
    "r=t.indexOf(\"\\n\",n);if(-1===r)return null;const o=n<=0?-1:t.lastIndexOf(\"\\n\",n-1),"
    "c=-1===o?0:o+1,i=__col(t,c,n),u=r+1,l=t.indexOf(\"\\n\",u),a=-1===l?t.length:l;return __atCol(t,u,a,i)}"
)

TL_OLD = (
    "const r=(t,e)=>{const n=t.charCodeAt(0);return n>=768&&n<=879||n>=8203&&n<=8205||65279===n?0:"
    "n>=4352&&n<=4447||n>=11904&&n<=40959||n>=44032&&n<=55215||n>=63744&&n<=64255||n>=65072&&n<=65103||"
    "n>=65280&&n<=65376||n>=65504&&n<=65510||n>=127744&&n<=129535?2:1}"
)
TL_NEW = (
    "const r=(t,e)=>{const n=t.codePointAt(0);if(null==n)return 1;"
    "if(/\\p{Mn}|\\p{Me}|\\p{Cf}/u.test(t))return 0;"
    "return n>=8203&&n<=8205||65279===n?0:"
    "n>=4352&&n<=4447||n>=11904&&n<=40959||n>=44032&&n<=55215||n>=63744&&n<=64255||n>=65072&&n<=65103||"
    "n>=65280&&n<=65376||n>=65504&&n<=65510||n>=127744&&n<=129535?2:1}"
)

REPLACEMENTS: tuple[tuple[str, str, str, str], ...] = (
    ("word helpers", WORD_OLD, WORD_NEW, "__wordSeg"),
    ("grapheme left/right", LR_OLD, LR_NEW, 'granularity:"grapheme"'),
    ("grapheme backspace/delete", BS_OLD, BS_NEW, "n.backspace&&B>0){const __g="),
    ("visual up/down", NAV_OLD, NAV_NEW, "function __cw("),
    ("text-layout width", TL_OLD, TL_NEW, "\\p{Mn}|\\p{Me}|\\p{Cf}"),
)

# Upgrade installs that used Segments.next(), which is not an iterator method.
ITERATOR_UPGRADES: tuple[tuple[str, str, str], ...] = (
    (
        "grapheme iterator (right)",
        "__g.segment(__rest).next().value",
        "__g.segment(__rest)[Symbol.iterator]().next().value",
    ),
    (
        "grapheme iterator (delete)",
        "__g.segment(J.slice(B)).next().value",
        "__g.segment(J.slice(B))[Symbol.iterator]().next().value",
    ),
)

# Split so this file does not embed the old IME-hack payloads as contiguous literals.
FORBIDDEN_MARKERS = (
    "__CURSOR_AGENT_IME_" + "REPOSITION",
    "__CURSOR_AGENT_IME_" + "CARET",
    "__CURSOR_AGENT_FOOTER_" + "LINES",
)


HOOK_BEGIN = "# cursor-agent-cjk-input-patch begin"
HOOK_END = "# cursor-agent-cjk-input-patch end"


def latest_version(root: Path) -> Path | None:
    if not root.exists():
        return None
    dirs = sorted(
        [p for p in root.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return dirs[0] if dirs else None


def install_kind(path: Path) -> str:
    return "worker" if "cursor-agent-worker" in path.parts else "cli"


def orig_backup_path(path: Path) -> Path:
    return BACKUP_DIR / f"{install_kind(path)}-{path.parent.name}-{path.name}.orig.bak"


def is_original_text(text: str) -> bool:
    return "__wordSeg" not in text


def ensure_original_backup(path: Path, original_text: str) -> Path | None:
    """Keep one unpatched copy per CLI/worker version. Never overwrite."""
    dest = orig_backup_path(path)
    if not is_original_text(original_text):
        return dest if dest.exists() else None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copy2(path, dest)
    return dest


def original_backup_for(path: Path) -> Path | None:
    dest = orig_backup_path(path)
    if dest.exists() and is_original_text(dest.read_text()):
        return dest
    fallback = BACKUP_DIR / f"cli-{path.parent.name}-{path.name}.orig.bak"
    if fallback.exists() and is_original_text(fallback.read_text()):
        return fallback
    if not BACKUP_DIR.exists():
        return None
    legacy = [
        bak
        for bak in BACKUP_DIR.glob("*.bak")
        if not bak.name.endswith(".orig.bak")
        and (bak.name.startswith(f"{path.parent.name}-{path.name}.") or bak.name.startswith(f"{path.name}."))
        and is_original_text(bak.read_text())
    ]
    if not legacy:
        return None
    return max(legacy, key=lambda p: p.stat().st_mtime)


def migrate_legacy_backups() -> None:
    if not BACKUP_DIR.exists():
        return
    latest = latest_version(DEFAULT_VERSIONS)
    latest_name = latest.name if latest else "unknown"
    for bak in list(BACKUP_DIR.glob("*.bak")):
        if bak.name.endswith(".orig.bak"):
            continue
        try:
            text = bak.read_text()
        except OSError:
            continue
        if not is_original_text(text):
            bak.unlink(missing_ok=True)
            continue
        marker = "-4794.index.js."
        if marker in bak.name:
            version = bak.name.split(marker, 1)[0]
            fname = "4794.index.js"
        elif bak.name.startswith("4794.index.js."):
            version = latest_name
            fname = "4794.index.js"
        else:
            bak.unlink(missing_ok=True)
            continue
        dest = BACKUP_DIR / f"cli-{version}-{fname}.orig.bak"
        if dest.exists():
            bak.unlink(missing_ok=True)
        else:
            bak.rename(dest)


def list_backups() -> None:
    migrate_legacy_backups()
    if not BACKUP_DIR.exists():
        print(f"no backups at {BACKUP_DIR}")
        return
    files = sorted(BACKUP_DIR.glob("*.orig.bak"))
    if not files:
        print(f"no backups at {BACKUP_DIR}")
        return
    print(f"original backups in {BACKUP_DIR}:")
    for bak in files:
        print(f"  {bak.name}")


def replace_unique(text: str, old: str, new: str, label: str, already: str) -> tuple[str, bool]:
    count = text.count(old)
    if count == 0:
        if already in text:
            return text, False
        raise SystemExit(f"pattern not found: {label}")
    if count != 1:
        raise SystemExit(f"pattern not unique ({count}): {label}")
    if new in FORBIDDEN_MARKERS or any(m in new for m in FORBIDDEN_MARKERS):
        raise SystemExit(f"refusing to insert cursor-reposition code: {label}")
    return text.replace(old, new, 1), True


def patch_input_bundle(text: str) -> tuple[str, list[str]]:
    applied: list[str] = []
    for label, old, new, already in REPLACEMENTS:
        text, ok = replace_unique(text, old, new, label, already)
        if ok:
            applied.append(label)
    for label, old, new in ITERATOR_UPGRADES:
        if old in text:
            text, ok = replace_unique(text, old, new, label, already=new)
            if ok:
                applied.append(label)
    for marker in FORBIDDEN_MARKERS:
        if marker in text:
            raise SystemExit(
                f"refusing to write bundle that still contains {marker!r} "
                "(old IME cursor patch). Restore the official file first."
            )
    return text, applied


def find_input_bundle(root: Path, *, restoring: bool = False) -> Path:
    preferred = root / "4794.index.js"
    if restoring and preferred.exists():
        return preferred

    needle = WORD_OLD
    if preferred.exists():
        sample = preferred.read_text()
        if needle in sample or "__wordSeg" in sample:
            return preferred

    matches: list[Path] = []
    for path in root.glob("*.index.js"):
        if path.name == "index.js" or path.stat().st_size > 2_000_000:
            continue
        sample = path.read_text()
        if needle in sample or "__wordSeg" in sample:
            matches.append(path)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(f"No text-input bundle with expected word helpers under {root}")
    names = ", ".join(p.name for p in matches)
    raise SystemExit(f"Multiple candidate input bundles: {names}")


def node_check(path: Path) -> None:
    result = subprocess.run(
        ["node", "--check", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"node --check failed for {path.name}:\n{result.stderr or result.stdout}"
        )


def warn_old_ime(root: Path) -> None:
    leftover = []
    for name in ("index.js", "6260.index.js"):
        path = root / name
        if not path.exists():
            continue
        text = path.read_text()
        if any(marker in text for marker in FORBIDDEN_MARKERS):
            leftover.append(name)
    if leftover:
        print(
            "warning: old IME cursor patch still present in "
            + ", ".join(leftover)
            + f"\n  reinstall the official CLI: {REINSTALL_HINT}"
        )


def patch_tree(root: Path, dry_run: bool = False, verbose: bool = False) -> bool:
    if verbose:
        print("target:", root)
        warn_old_ime(root)
    path = find_input_bundle(root)
    original = path.read_text()
    updated, applied = patch_input_bundle(original)
    if not applied:
        if verbose:
            print(f"  {path.name}: already up to date")
        return False
    kind = install_kind(root)
    print(f"patched {kind} {root.name}")
    if verbose:
        print(f"  {path.name}: {', '.join(applied)}")
    if dry_run:
        return True
    bak = ensure_original_backup(path, original)
    path.write_text(updated)
    try:
        node_check(path)
    except SystemExit:
        if bak and bak.exists():
            shutil.copy2(bak, path)
        else:
            path.write_text(original)
        print(f"  rolled back {path.name}", file=sys.stderr)
        raise
    return True


def restore_tree(root: Path) -> None:
    print("restore target:", root)
    path = find_input_bundle(root, restoring=True)
    bak = original_backup_for(path)
    if not bak:
        raise SystemExit(
            f"No original backup for {path.name} under {BACKUP_DIR}\n"
            f"Reinstall the official CLI instead:\n  {REINSTALL_HINT}"
        )
    shutil.copy2(bak, path)
    node_check(path)
    print(f"  restored {path.name} from {bak.name}")
    warn_old_ime(root)


def resolve_roots(version_dir: str | None, worker: bool) -> list[Path]:
    if version_dir:
        return [Path(version_dir).expanduser()]
    latest = latest_version(DEFAULT_VERSIONS)
    if not latest:
        raise SystemExit(f"No agent versions under {DEFAULT_VERSIONS}")
    roots = [latest]
    if worker:
        w = latest_version(WORKER_VERSIONS)
        if w:
            roots.append(w)
    return roots


def shell_hook(script: Path) -> str:
    return (
        f"{HOOK_BEGIN}\n"
        f"agent() {{ python3 \"{script}\" --ensure; command agent \"$@\"; }}\n"
        f"cursor-agent() {{ python3 \"{script}\" --ensure; command cursor-agent \"$@\"; }}\n"
        f"{HOOK_END}\n"
    )


def install_shell_hook() -> Path:
    rc = Path.home() / ".zshrc"
    script = Path(__file__).resolve()
    block = shell_hook(script)
    text = rc.read_text() if rc.exists() else ""
    if HOOK_BEGIN in text:
        text = re.sub(
            rf"{re.escape(HOOK_BEGIN)}.*?{re.escape(HOOK_END)}\n?",
            block,
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = text.rstrip() + "\n\n" + block
    rc.write_text(text)
    print(f"installed shell hook in {rc}")
    print("open a new terminal (or `source ~/.zshrc`) so `agent` auto-patches on launch")
    return rc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version_dir",
        nargs="?",
        help="Cursor agent version directory (defaults to latest CLI + IDE worker)",
    )
    parser.add_argument(
        "--worker",
        action="store_true",
        help="Deprecated: worker is patched by default. Ignored.",
    )
    parser.add_argument("--no-worker", action="store_true", help="Skip the IDE agent-worker copy")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore the original text-input bundle from the saved .orig.bak",
    )
    parser.add_argument("--list-backups", action="store_true", help="Show original backups and exit")
    parser.add_argument(
        "--ensure",
        action="store_true",
        help="Quiet no-op if already patched; if a CLI update cannot be patched, warn and exit 0",
    )
    parser.add_argument("--install", action="store_true", help="Install a zsh hook so `agent` auto-patches")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print per-file details")
    args = parser.parse_args()

    migrate_legacy_backups()

    if args.list_backups:
        list_backups()
        return
    if args.install:
        install_shell_hook()
        args.ensure = True
    if args.restore and args.dry_run:
        raise SystemExit("use --restore or --dry-run, not both")

    worker = not args.no_worker
    for root in resolve_roots(args.version_dir, worker):
        if not root.is_dir():
            raise SystemExit(f"Not a directory: {root}")
        if args.restore:
            restore_tree(root)
            continue
        try:
            patch_tree(root, dry_run=args.dry_run, verbose=args.verbose)
        except SystemExit as exc:
            if args.ensure:
                print(f"cjk patch skipped ({root.name}): {exc}", file=sys.stderr)
                continue
            raise


if __name__ == "__main__":
    main()
