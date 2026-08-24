<p align="center">
  <a href="README.md"><strong>English</strong></a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <img src="assets/banner.png" alt="Cursor CLI prompt with Korean and English text" width="100%">
</p>

<h1 align="center">cursor-cli-input-patch</h1>

<p align="center">
  <strong>Unicode input fixes for <a href="https://cursor.com/docs/cli/overview">Cursor CLI</a></strong><br>
  <sub>word navigation · blank-line scroll · local · reversible · unofficial</sub>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="macOS">
  <img src="https://img.shields.io/badge/Cursor%20CLI-unofficial-orange?style=flat-square" alt="Unofficial">
  <img src="https://img.shields.io/badge/python-3+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3">
</p>

<br>

> **Naming:** Cursor’s official product is [**Cursor CLI**](https://cursor.com/cli). The command you run is **`agent`** (`cursor-agent` is a legacy alias). This repo patches the installed CLI bundle — it does not ship Cursor binaries.

<table>
<tr>
<td width="50%" valign="top">

### Before

In the **`agent`** prompt, two things feel wrong:

- **Option/Alt + ← / →** only recognizes ASCII “words” (`[A-Za-z0-9_]`) and skips everything else
- **↑** onto a blank line above a wrapped URL scrolls away and snaps the caret to the URL

</td>
<td width="50%" valign="top">

### After

Same keys, predictable behavior:

- Word jump uses `Intl.Segmenter` (Unicode / UAX #29 word boundaries)
- Blank lines map to the correct visual row — no scroll jump

</td>
</tr>
</table>

<p align="center">
  <img src="assets/before-after.png" alt="Blank-line navigation: stock vs patched" width="88%">
</p>

<br>

## Who is affected?

Not CJK-only — the two fixes have different scopes:

| Fix | Affected users |
|:----|:----------------|
| **Option/Ctrl + ← / →** (word jump) | Anyone typing scripts **outside `[A-Za-z0-9_]`** — Korean, Japanese, Chinese, Cyrillic, Arabic, Hebrew, Thai, Greek, Devanagari, etc. Mostly fine if you only type English words in plain ASCII. Same class of bug reported in other terminal agents ([Codex CLI](https://github.com/openai/codex/issues/16584), [Claude Code](https://github.com/anthropics/claude-code/issues/11099)). |
| **↑ on a blank line** above a wrapped row | **Language-agnostic** — long URLs/paths that soft-wrap, with empty lines above. |

This repo was built around Korean/CJK pain points, but the word-motion patch helps **any non-ASCII script** the stock ASCII regex skips.

<br>

## Quick start

```bash
git clone https://github.com/vzts/cursor-cli-input-patch.git
cd cursor-cli-input-patch

python3 tests/test_behavior.py   # sanity check — no Cursor install needed
python3 apply_patch.py           # patch latest CLI + IDE worker
python3 apply_patch.py --install # optional: auto-patch on every `agent` launch
```

Restart **`agent`** after patching.

<details>
<summary><strong>Requirements</strong></summary>

<br>

- **Python 3** — runs the patcher
- **Node.js** — `node --check` before writing
- **macOS** — paths match the Cursor CLI install layout
- **Cursor CLI** — already installed (`curl https://cursor.com/install -fsS | bash`)

</details>

<br>

## What it patches

Only **`4794.index.js`** — the text-input bundle under your existing install.

| | |
|:--|:--|
| **Word motion** | ASCII-only helpers → `Intl.Segmenter` (`granularity: "word"`) for Option/Ctrl + arrow |
| **Empty lines** | `findLine` fix so blank rows and wrap EOL don't fall back to line 0 |

Auto-targets (Cursor’s internal paths — still named `cursor-agent` on disk):

```
~/.local/share/cursor-agent/versions/<latest>/
~/Library/Application Support/Cursor/.../cursor-agent-worker/.../versions/<latest>/
```

<br>

## What it deliberately skips

| Area | Reason |
|:-----|:-------|
| Plain **← / →** | NFC Hangul is already one UTF-16 step per syllable |
| **Backspace / Delete** grapheme | Same — no patch needed |
| CJK **display-width ↑ / ↓** | Terminal caret is 1 column per code point; width-2 math lands wrong |
| **IME** candidate position | Old reposition patch hung `agent` — removed and refused |

The patcher never moves the terminal cursor with escape sequences.

<br>

## Commands

```bash
python3 apply_patch.py              # patch
python3 apply_patch.py --install    # zsh hook → auto-patch on `agent` launch
python3 apply_patch.py --ensure     # quiet skip if done; warn on mismatch
python3 apply_patch.py --restore    # rollback from .orig.bak
python3 apply_patch.py --list-backups
python3 apply_patch.py --dry-run -v
python3 apply_patch.py --no-worker  # CLI only, skip IDE worker copy
```

<details>
<summary><strong>After a CLI update · backups · reinstall</strong></summary>

<br>

Cursor updates replace the version folder. Re-run `python3 apply_patch.py` (or just launch `agent` if `--install` is set).

Backups — one pristine original per version, never overwritten:

```
~/.local/share/cursor-cli-input-patch/backups/*.orig.bak
```

(Older clones used `~/.local/share/cursor-agent-cjk-input-patch/backups/` — migrated automatically.)

If a future minify no longer matches, the patcher **fails closed** (`--ensure` warns and still starts `agent`). Last resort:

```bash
curl https://cursor.com/install -fsS | bash
```

</details>

<br>

## How it works

```mermaid
flowchart LR
  A[agent launch] --> B{zsh hook?}
  B -->|yes| C[apply_patch.py --ensure]
  B -->|no| D[manual run]
  C --> E[find 4794.index.js]
  D --> E
  E --> F[replace pinned snippets]
  F --> G{node --check}
  G -->|ok| H[write + backup]
  G -->|fail| I[rollback]
```

Patterns are pinned to a specific minified shape — the patcher refuses to guess if Cursor re-minifies differently.

<br>

## Tests

```bash
python3 tests/test_behavior.py    # portable, no Cursor needed
python3 tests/test_pty_arrows.py  # PTY checks (needs patched CLI)
```

<br>

<p align="center">
  <sub>Unofficial community tool · not affiliated with Cursor · <a href="LICENSE">MIT</a> © 2026 <a href="https://github.com/vzts">vzts</a></sub>
</p>
