# cursor-agent-cjk-input-patch

Unofficial local patcher for Cursor Agent CLI CJK / Hangul / Thai prompt input.

Does **not** ship Cursor binaries. Rewrites patterns in your already-installed
text-input bundle (`4794.index.js` only). Does not move the terminal cursor.

- Option/Ctrl+Arrow: `Intl.Segmenter` word boundaries (Hangul is a word)
- Left/Right / Backspace / Delete: grapheme steps
- Up/Down + Thai: display width (CJK = 2, combining marks = 0)

IME candidate-window position is **not** patched. An earlier version did that
via Ink cursor moves and could hang `agent`; that code is gone.

```bash
python3 tests/test_behavior.py
python3 apply_patch.py          # latest CLI install
python3 apply_patch.py --worker # also IDE worker copy
```

Restart `agent` afterwards. Python 3.9+ and `node` required.

```bash
python3 apply_patch.py --dry-run
python3 apply_patch.py --restore          # undo from local backup
python3 apply_patch.py --restore --worker
```

Backups: `~/.local/share/cursor-agent-cjk-input-patch/backups/`.  
If `--restore` is not enough (or `agent` still dumps garbage):

```bash
curl https://cursor.com/install -fsS | bash
```

Then apply this patcher again. If `pattern not found` after a CLI update, do
not force it.

Unofficial, MIT (this patcher only). Not affiliated with Cursor.
