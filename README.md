# cursor-agent-cjk-input-patch

Unofficial local patcher for Cursor Agent CLI Hangul Option/Ctrl+arrow
word motion, and for Up onto a blank line above a long wrapped URL.

Does **not** ship Cursor binaries. Rewrites patterns in your already-installed
text-input bundle (`4794.index.js` only). Does not move the terminal cursor.
Left/Right and IME candidate-window position are **not** patched. An earlier
IME cursor move hung `agent`; that code is gone. CJK display-width Up/Down is
also gone — the fake caret is 1 column per glyph and width-2 landed on the
wrong character.

```bash
python3 tests/test_behavior.py
python3 apply_patch.py             # latest CLI + IDE worker
python3 apply_patch.py --install   # once: zsh hook so `agent` auto-patches
python3 apply_patch.py --restore   # undo
```

Restart `agent` afterwards. After a CLI update the version folder is replaced;
`--install` re-applies on the next launch. One original backup per version:
`~/.local/share/cursor-agent-cjk-input-patch/backups/*.orig.bak`.

If a future minify no longer matches, the hook warns and still starts `agent`.
Last resort: `curl https://cursor.com/install -fsS | bash`.

Unofficial, MIT (this patcher only). Not affiliated with Cursor.
