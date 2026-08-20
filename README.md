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
| IME preedit stuck at bottom-left | Ink `log-update` leaves VT cursor below the frame (`…\n`) while drawing a fake caret | Publish caret cell + CUP after each frame write |

Related public discussions (Cursor forum): word-motion / CJK IME / Thai caret threads. Same class of fix as [gemini-cli#14475](https://github.com/google-gemini/gemini-cli/pull/14475) (`Intl.Segmenter`).

## Requirements

- macOS or Linux with Cursor Agent CLI installed (`~/.local/share/cursor-agent/versions/…`)
- Python 3.9+
- Restart `cursor-agent` / `agent` after patching

## Usage

```bash
git clone https://github.com/vzts/cursor-agent-cjk-input-patch.git
cd cursor-agent-cjk-input-patch

# Patch latest install (+ optional IDE worker copy)
python3 apply_patch.py

# Or a specific version directory
python3 apply_patch.py ~/.local/share/cursor-agent/versions/2026.08.11-e8db854

# Also patch Cursor IDE agent-worker install
python3 apply_patch.py --worker
```

Backups go to `~/.local/share/cursor-agent-cjk-input-patch/backups/` (original file copies only on your machine).

## Privacy

This project intentionally contains:

- No API keys, tokens, emails, or account data
- No Cursor Agent source/bundles (proprietary)
- No local absolute paths beyond `$HOME`-relative defaults in the script

Do **not** commit `*.bak` files from your machine — they are full copies of Cursor’s JS bundles.

## Limits / disclaimer

- Unofficial. Not affiliated with Anysphere / Cursor.
- Patch patterns may break when Cursor renames webpack chunks or minifies differently. Re-run after CLI updates; if it fails, restore from backup.
- IME CUP uses a prompt-at-bottom layout heuristic (footer / extra rows). Better than bottom-left; may be ~1 line off with some UI chrome.
- Does not fix IDE Agents Window (Glass) input bugs — different surface.

## License

MIT (this patcher only). Cursor Agent remains proprietary to its owners.
