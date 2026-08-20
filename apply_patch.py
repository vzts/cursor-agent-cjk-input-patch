#!/usr/bin/env python3
"""Apply unofficial CJK / multi-byte input patches to a local Cursor Agent CLI install.

Does not redistribute Cursor binaries. See README.md.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path.home() / ".local/share/cursor-agent-cjk-input-patch" / "backups"
DEFAULT_VERSIONS = Path.home() / ".local/share/cursor-agent" / "versions"
WORKER_VERSIONS = (
    Path.home()
    / "Library/Application Support/Cursor/User/globalStorage"
    / "anysphere.cursor-agent-worker/agent-cli/.local/share/cursor-agent/versions"
)


def latest_version(root: Path) -> Path | None:
    if not root.exists():
        return None
    dirs = sorted(
        [p for p in root.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return dirs[0] if dirs else None


def backup(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / f"{path.name}.{datetime.now():%Y%m%d-%H%M%S}.bak"
    shutil.copy2(path, dest)
    return dest


def replace_once(text: str, old: str, new: str, label: str) -> tuple[str, bool]:
    if old not in text:
        # Already patched if distinctive marker from `new` is present
        marker = new[:48]
        if marker and marker in text:
            return text, False
        raise SystemExit(f"pattern not found: {label}")
    return text.replace(old, new, 1), True


def patch_4794(text: str) -> tuple[str, list[str]]:
    applied: list[str] = []

    old_word = (
        "function c(t){return/[A-Za-z0-9_]/.test(t)}function i(t){return/\\s/.test(t)}"
        "function u(t,e){let n=e;const r=\"\\n\"===t[n]&&(0===n||\"\\n\"===t[n-1]);"
        "if(n<t.length&&c(t[n]))for(;n<t.length&&c(t[n]);)n++;else r&&n++;"
        "for(;n<t.length&&!c(t[n]);){if(\"\\n\"===t[n]&&(0===n||\"\\n\"===t[n-1]))return n;"
        "if(\"\\n\"===t[n]&&n+1<t.length&&\"\\n\"===t[n+1])return n+1;n++}"
        "return Math.min(t.length,Math.max(0,n))}function l(t,e){let n=e;if(n<=0)return 0;"
        "for(n--;n>0&&!c(t[n]);){if(\"\\n\"===t[n]&&n>0&&\"\\n\"===t[n-1])return n;n--}"
        "for(;n>0&&c(t[n-1]);)n--;return n}"
    )
    new_word = (
        "function c(t){return/[A-Za-z0-9_]/.test(t)}function i(t){return/\\s/.test(t)}"
        "const __wordSeg=new Intl.Segmenter(void 0,{granularity:\"word\"});"
        "function __wordStarts(t){const e=[];for(const n of __wordSeg.segment(t))"
        "n.isWordLike&&e.push(n.index);return e}"
        "function u(t,e){let n=e;const r=\"\\n\"===t[n]&&(0===n||\"\\n\"===t[n-1]);"
        "if(r){n++;const o=__wordStarts(t);for(const t of o)if(t>=n)return t;"
        "return Math.min(t.length,Math.max(0,n))}const o=__wordStarts(t);"
        "for(const t of o)if(t>e)return t;for(let r=e;r<t.length;r++){"
        "if(\"\\n\"===t[r]&&(0===r||\"\\n\"===t[r-1]))return r;"
        "if(\"\\n\"===t[r]&&r+1<t.length&&\"\\n\"===t[r+1])return r+1}return t.length}"
        "function l(t,e){if(e<=0)return 0;let n=e-1;for(;n>0&&\"\\n\"===t[n];){"
        "if(\"\\n\"===t[n-1])return n;n--}const r=__wordStarts(t);let o=0;"
        "for(const t of r){if(!(t<e))break;o=t}return o}"
    )
    if "__wordSeg" in text and old_word not in text:
        pass
    else:
        text, ok = replace_once(text, old_word, new_word, "word helpers")
        if ok:
            applied.append("word helpers")

    new_lr = (
        "if(n.leftArrow){if(v&&Nt>0){const __g=new Intl.Segmenter(void 0,{granularity:\"grapheme\"});"
        "let __p=0;for(const __s of __g.segment(Ut.slice(0,Nt)))__p=__s.index;Nt=__p}}"
        "else if(n.rightArrow){if(v&&Nt<Ut.length){const __g=new Intl.Segmenter(void 0,{granularity:\"grapheme\"});"
        "const __rest=Ut.slice(Nt);const __s=__g.segment(__rest).next().value;Nt+=__s?__s.segment.length:1}}"
    )
    old_lr = "if(n.leftArrow)v&&Nt--;else if(n.rightArrow)v&&Nt++;"
    if old_lr in text:
        text = text.replace(old_lr, new_lr, 1)
        applied.append("grapheme left/right")

    old_bs = (
        "else n.backspace&&B>0?(Ut=J.slice(0,B-1)+J.slice(B,J.length),Nt--)"
        ":n.delete&&B<J.length&&(Ut=J.slice(0,B)+J.slice(B+1,J.length))"
    )
    new_bs = (
        "else if(n.backspace&&B>0){const __g=new Intl.Segmenter(void 0,{granularity:\"grapheme\"});"
        "let __p=0;for(const __s of __g.segment(J.slice(0,B)))__p=__s.index;"
        "Ut=J.slice(0,__p)+J.slice(B);Nt=__p}"
        "else if(n.delete&&B<J.length){const __g=new Intl.Segmenter(void 0,{granularity:\"grapheme\"});"
        "const __s=__g.segment(J.slice(B)).next().value;const __n=B+(__s?__s.segment.length:1);"
        "Ut=J.slice(0,B)+J.slice(__n);Nt=B}"
    )
    if old_bs in text:
        text, ok = replace_once(text, old_bs, new_bs, "grapheme backspace/delete")
        if ok:
            applied.append("grapheme backspace/delete")

    old_nav = (
        "function o(t,e){if(-1===t.indexOf(\"\\n\"))return null;const n=Math.min(Math.max(0,e),t.length),"
        "r=n<=0?-1:t.lastIndexOf(\"\\n\",n-1);if(-1===r)return null;const o=t.lastIndexOf(\"\\n\",Math.max(0,r-1)),"
        "s=-1===o?0:o+1,c=n-(r+1),i=r-s;return s+Math.min(c,i)}"
        "function s(t,e){if(-1===t.indexOf(\"\\n\"))return null;const n=Math.min(Math.max(0,e),t.length),"
        "r=t.indexOf(\"\\n\",n);if(-1===r)return null;const o=n<=0?-1:t.lastIndexOf(\"\\n\",n-1),"
        "s=n-(-1===o?0:o+1),c=r+1,i=t.indexOf(\"\\n\",c),u=(-1===i?t.length:i)-c;return c+Math.min(s,u)}"
    )
    new_nav = (
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
    if old_nav in text:
        text, ok = replace_once(text, old_nav, new_nav, "visual up/down")
        if ok:
            applied.append("visual up/down")
    elif "__cw" in text and "\\p{Mn}" not in text:
        old_cw = (
            "function __cw(t){const e=t.codePointAt(0);if(null==e)return 1;"
            "if(e>=768&&e<=879||e>=8203&&e<=8205||65279===e)return 0;"
            "return e>=4352&&e<=4447||e>=11904&&e<=40959||e>=44032&&e<=55215||e>=63744&&e<=64255||"
            "e>=65072&&e<=65103||e>=65280&&e<=65376||e>=65504&&e<=65510||e>=127744&&e<=129535?2:1}"
        )
        new_cw = (
            "function __cw(t){const e=t.codePointAt(0);if(null==e)return 1;"
            "if(/\\p{Mn}|\\p{Me}|\\p{Cf}/u.test(t))return 0;"
            "if(e>=8203&&e<=8205||65279===e)return 0;"
            "return e>=4352&&e<=4447||e>=11904&&e<=40959||e>=44032&&e<=55215||e>=63744&&e<=64255||"
            "e>=65072&&e<=65103||e>=65280&&e<=65376||e>=65504&&e<=65510||e>=127744&&e<=129535?2:1}"
        )
        text, ok = replace_once(text, old_cw, new_cw, "combining-mark width")
        if ok:
            applied.append("combining-mark width")

    old_tl = (
        "const r=(t,e)=>{const n=t.charCodeAt(0);return n>=768&&n<=879||n>=8203&&n<=8205||65279===n?0:"
        "n>=4352&&n<=4447||n>=11904&&n<=40959||n>=44032&&n<=55215||n>=63744&&n<=64255||n>=65072&&n<=65103||"
        "n>=65280&&n<=65376||n>=65504&&n<=65510||n>=127744&&n<=129535?2:1}"
    )
    new_tl = (
        "const r=(t,e)=>{const n=t.codePointAt(0);if(null==n)return 1;"
        "if(/\\p{Mn}|\\p{Me}|\\p{Cf}/u.test(t))return 0;"
        "return n>=8203&&n<=8205||65279===n?0:"
        "n>=4352&&n<=4447||n>=11904&&n<=40959||n>=44032&&n<=55215||n>=63744&&n<=64255||n>=65072&&n<=65103||"
        "n>=65280&&n<=65376||n>=65504&&n<=65510||n>=127744&&n<=129535?2:1}"
    )
    if old_tl in text:
        text, ok = replace_once(text, old_tl, new_tl, "text-layout width")
        if ok:
            applied.append("text-layout width")

    if "__CURSOR_AGENT_IME_CARET" not in text:
        old_ime = "const{isRawModeSupported:mt,setRawMode:gt}=(0,s.mT)();"
        new_ime = (
            "try{let __col=0,__i=0;const __cw=(t)=>{const e=t.codePointAt(0);if(null==e)return 1;"
            "if(/\\p{Mn}|\\p{Me}|\\p{Cf}/u.test(t))return 0;"
            "return e>=4352&&e<=4447||e>=11904&&e<=40959||e>=44032&&e<=55215||e>=63744&&e<=64255||"
            "e>=65072&&e<=65103||e>=65280&&e<=65376||e>=65504&&e<=65510||e>=127744&&e<=129535?2:1};"
            "for(const __ch of lt){if(__i>=at)break;if(\"\\n\"===__ch){__col=0}"
            "else __col+=__cw(__ch);__i+=__ch.length}let __after=0;"
            "for(let __j=at;__j<lt.length;__j++)\"\\n\"===lt[__j]&&__after++;"
            "const __foot=globalThis.__CURSOR_AGENT_FOOTER_LINES|0;"
            "const __extra=globalThis.__CURSOR_AGENT_BELOW_INPUT_LINES|0;"
            "globalThis.__CURSOR_AGENT_IME_CARET={upFromBottom:__foot+__extra+__after,col:__col}}"
            "catch(__e){}const{isRawModeSupported:mt,setRawMode:gt}=(0,s.mT)();"
        )
        text, ok = replace_once(text, old_ime, new_ime, "IME caret publish")
        if ok:
            applied.append("IME caret publish")

    return text, applied


def patch_6260(text: str) -> tuple[str, list[str]]:
    applied: list[str] = []
    if "__CURSOR_AGENT_FOOTER_LINES" not in text:
        old = "if(!e)return null;const T=Boolean(f),A=Boolean(b||p);"
        new = (
            "if(!e){globalThis.__CURSOR_AGENT_FOOTER_LINES=0;return null}"
            "const T=Boolean(f),A=Boolean(b||p);"
            "globalThis.__CURSOR_AGENT_FOOTER_LINES=(t?2:1)+(T?1:0)+(A?1:0)+(x?1:0);"
        )
        text, ok = replace_once(text, old, new, "footer lines")
        if ok:
            applied.append("footer lines")

    if "__CURSOR_AGENT_BELOW_INPUT_LINES" not in text:
        old = (
            'm.hD&&!uo&&Ur&&Rn.length>0?(0,r.jsx)(l.az,{marginTop:0,marginX:2,justifyContent:"flex-end",'
            'children:(0,r.jsx)(l.EY,{dimColor:!0,children:"ctrl+r to review changed files"})}):null,'
            '!Gr||uo||Xr?null:(0,r.jsx)(l.az,{marginX:2,marginTop:1,children:(0,r.jsx)(l.EY,{color:"blue",children:ko?'
        )
        new = (
            "globalThis.__CURSOR_AGENT_BELOW_INPUT_LINES=(m.hD&&!uo&&Ur&&Rn.length>0?1:0)+(!Gr||uo||Xr?0:1),"
            + old
        )
        if old in text:
            text, ok = replace_once(text, old, new, "below-input lines")
            if ok:
                applied.append("below-input lines")
    return text, applied


def patch_index(text: str) -> tuple[str, list[str]]:
    applied: list[str] = []
    if "__CURSOR_AGENT_IME_REPOSITION" in text:
        return text, applied

    helper = (
        "const __CURSOR_AGENT_IME_REPOSITION=(e,t)=>{try{const n=globalThis.__CURSOR_AGENT_IME_CARET;"
        "const r=Math.max(1,((null==n?void 0:n.upFromBottom)|0)+1);"
        "const i=Math.max(1,((null==n?void 0:n.col)|0)+1);"
        "e.write(`\\x1b[${r}A\\x1b[${i}G`)}catch{}};"
    )
    old_mod = '"../ink/build/log-update.js"(e,t,n){"use strict";n.d(t,{A:()=>s});'
    new_mod = '"../ink/build/log-update.js"(e,t,n){"use strict";' + helper + "n.d(t,{A:()=>s});"
    old_inc = "e.write(f.join(\"\")),s=c,n=u};return o.clear="
    new_inc = "e.write(f.join(\"\")),__CURSOR_AGENT_IME_REPOSITION(e,u.length),s=c,n=u};return o.clear="
    old_full = "if(e.write(b),s=l,C&&n)try{n()}"
    new_full = "if(e.write(b),__CURSOR_AGENT_IME_REPOSITION(e,u.length),s=l,C&&n)try{n()}"

    text, ok = replace_once(text, old_mod, new_mod, "log-update helper")
    if ok:
        applied.append("log-update helper")
    text, ok = replace_once(text, old_inc, new_inc, "log-update incremental CUP")
    if ok:
        applied.append("log-update incremental CUP")
    text, ok = replace_once(text, old_full, new_full, "log-update full CUP")
    if ok:
        applied.append("log-update full CUP")
    return text, applied


def patch_tree(root: Path, dry_run: bool = False) -> None:
    print("target:", root)
    jobs = (
        (root / "4794.index.js", patch_4794),
        (root / "6260.index.js", patch_6260),
        (root / "index.js", patch_index),
    )
    for path, fn in jobs:
        if not path.exists():
            print(f"  skip missing {path.name}")
            continue
        original = path.read_text()
        updated, applied = fn(original)
        if not applied:
            print(f"  {path.name}: already up to date")
            continue
        print(f"  {path.name}: {', '.join(applied)}")
        if dry_run:
            continue
        backup(path)
        path.write_text(updated)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version_dir",
        nargs="?",
        help="Cursor agent version directory (defaults to latest under ~/.local/share/cursor-agent/versions)",
    )
    parser.add_argument(
        "--worker",
        action="store_true",
        help="Also patch the Cursor IDE agent-worker install if present",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    args = parser.parse_args()

    roots: list[Path] = []
    if args.version_dir:
        roots.append(Path(args.version_dir).expanduser())
    else:
        latest = latest_version(DEFAULT_VERSIONS)
        if not latest:
            raise SystemExit(f"No agent versions under {DEFAULT_VERSIONS}")
        roots.append(latest)
        if args.worker:
            w = latest_version(WORKER_VERSIONS)
            if w:
                roots.append(w)
            else:
                print("note: --worker set but no worker install found")

    for root in roots:
        if not root.is_dir():
            raise SystemExit(f"Not a directory: {root}")
        patch_tree(root, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
