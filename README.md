# cursor-agent-cjk-input-patch

Unofficial local patcher for **Cursor Agent CLI** prompt input when editing
Korean / CJK / Thai (and other multi-byte) text.

Cursor Agent CLI is closed-source. This repo does **not** ship Cursor binaries
or patched bundles — only a small Python script that rewrites patterns in your
already-installed agent files.

## What it fixes

| Symptom | Cause | Fix |
|---|---|---|
| Option/Ctrl+Arrow skips Hangul, jumps to English words | Word class was `/[A-Za-z0-9_]/` | `Intl.Segmenter` word boundaries |
| Left/Right / Backspace break grapheme clusters (Thai, emoji) | UTF-16 code-unit steps | Grapheme moves / deletes |
| Up/Down column drifts on Hangul | Code-unit column | Display width (CJK = 2, Mn/Me = 0) |
| Thai caret desync | Combining marks counted as width 1 | `\p{Mn}\|\p{Me}\|\p{Cf}` → width 0 |

Same class of fix as [gemini-cli#14475](https://github.com/google-gemini/gemini-cli/pull/14475) (`Intl.Segmenter`).

The script only rewrites the text-input webpack chunk (currently `4794.index.js`).
It does **not** patch Ink `log-update` or move the real terminal cursor.

## What it does not fix

IME candidate windows that stick to the bottom-left. An earlier version tried to
fix that by sending CSI cursor moves after every Ink frame. That desynced Ink’s
`log-update` cursor tracking and could make `agent` spew garbage / hang. That
code is removed.

## Requirements

- macOS or Linux with Cursor Agent CLI installed (`~/.local/share/cursor-agent/versions/…`)
- Python 3.9+ and `node` on PATH (`node --check` runs after writing)
- Restart `cursor-agent` / `agent` after patching

## Usage

```bash
git clone https://github.com/vzts/cursor-agent-cjk-input-patch.git
cd cursor-agent-cjk-input-patch
python3 tests/test_behavior.py
python3 apply_patch.py
```

Then **restart** any running `agent` / `cursor-agent` session so it reloads the
patched files.

```bash
# Preview without writing
python3 apply_patch.py --dry-run

# Specific version directory
python3 apply_patch.py ~/.local/share/cursor-agent/versions/2026.08.11-e8db854

# Also patch the Cursor IDE agent-worker copy
python3 apply_patch.py --worker
```

If a previous IME patch left `index.js` / `6260.index.js` modified, restore those
from a backup or reinstall the CLI first. This script will refuse to write a
bundle that still contains the old IME cursor markers, and it prints a warning
if those files are still patched.

Backups go to `~/.local/share/cursor-agent-cjk-input-patch/backups/` (original
file copies only on your machine). If `node --check` fails after a write, the
script restores that backup immediately.

## If something goes wrong

Typical signs: `agent` prints a flood of text, the prompt never settles, or the
process looks hung. Stop it first, then restore.

### 1. Stop the running CLI

In the stuck terminal: `Ctrl+C`. If it keeps going:

```bash
pkill -f cursor-agent
pkill -f '/agent'
```

Do not keep re-running `agent` until the files are restored.

### 2. Restore this patcher’s backup (usual case)

From a **new** terminal:

```bash
cd cursor-agent-cjk-input-patch
python3 apply_patch.py --list-backups
python3 apply_patch.py --restore
# if you also patched the IDE worker copy:
python3 apply_patch.py --restore --worker
```

`--restore` copies the newest matching `.bak` over the installed text-input
bundle, then runs `node --check`. Restart `agent` afterwards.

```bash
agent --version
agent
```

### 3. No backup, or it still spews garbage

That usually means `index.js` / `6260.index.js` were changed by the **old IME
cursor patch** (this repo no longer writes those files). Reinstall the official
CLI:

```bash
pkill -f cursor-agent; pkill -f '/agent'
curl https://cursor.com/install -fsS | bash
agent --version
```

If the IDE agent-worker copy is still broken, copy the three files from the
fresh CLI version directory into the worker version directory, or just let
Cursor refresh that worker on its own after a reinstall.

After a clean reinstall you can apply **this** patcher again. Do not use an
older clone of this repo that still patches `index.js`.

### 4. After a Cursor CLI update

Cursor may replace the version folder. Re-run `python3 apply_patch.py`. If it
exits with `pattern not found`, the minified bundle changed — do **not** force
it. Use `--restore` or reinstall, and wait for this patcher to be updated.

## Privacy

This project intentionally contains:

- No API keys, tokens, emails, or account data
- No Cursor Agent source/bundles (proprietary)
- No local absolute paths beyond `$HOME`-relative defaults in the script

Do **not** commit `*.bak` files from your machine — they are full copies of Cursor’s JS bundles.

## Limits / disclaimer

- Unofficial. Not affiliated with Anysphere / Cursor.
- Patch patterns may break when Cursor renames webpack chunks or minifies differently. Re-run after CLI updates; if it fails, restore from backup or reinstall.
- Does not fix IDE Agents Window (Glass) input bugs — different surface.

## License

MIT (this patcher only). Cursor Agent remains proprietary to its owners.
