# cursor-agent-cjk-input-patch

Unofficial local patcher for Cursor Agent CLI CJK / Hangul / Thai prompt input.

Does **not** ship Cursor binaries. Patches `4794.index.js` only (word / grapheme /
display width). Does not move the terminal cursor. IME candidate-window position
is not patched — that previously hung `agent`.

```bash
python3 apply_patch.py --install   # once: zsh hook so `agent` auto-patches
python3 apply_patch.py             # or just ensure latest CLI + IDE worker
python3 apply_patch.py --restore   # undo
```

After a Cursor CLI update the version folder is replaced, so the patch has to
be applied again. With `--install`, the next `agent` / `cursor-agent` launch
does that. Already-patched installs are a no-op. One original backup is kept
per version (`~/.local/share/cursor-agent-cjk-input-patch/backups/*.orig.bak`).

If a future CLI minify no longer matches, the hook warns and still starts
`agent`. Do not force it. Last resort: `curl https://cursor.com/install -fsS | bash`.

Unofficial, MIT (this patcher only). Not affiliated with Cursor.
