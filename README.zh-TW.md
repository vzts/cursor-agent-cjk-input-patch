<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.zh-TW.md"><strong>繁體中文</strong></a>
</p>

<p align="center">
  <img src="assets/banner.png" alt="含韓文與英文的 Cursor CLI 提示符" width="100%">
</p>

<h1 align="center">cursor-cli-input-patch</h1>

<p align="center">
  <strong><a href="https://cursor.com/docs/cli/overview">Cursor CLI</a> Unicode 輸入修補</strong><br>
  <sub>依詞移動 · 空行捲動 · 本機 · 可還原 · 非官方</sub>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="macOS">
  <img src="https://img.shields.io/badge/Cursor%20CLI-unofficial-orange?style=flat-square" alt="Unofficial">
  <img src="https://img.shields.io/badge/python-3+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3">
</p>

<br>

> **命名：** 官方產品名為 [**Cursor CLI**](https://cursor.com/cli)，執行命令為 **`agent`**（`cursor-agent` 為舊別名）。本 repo 只修補已安裝的 CLI 套件，不含 Cursor 二進位檔。

<table>
<tr>
<td width="50%" valign="top">

### 修補前

**`agent`** 提示符中:

- **Option/Alt + ← / →** 僅辨識 ASCII 「詞」(`[A-Za-z0-9_]`)
- 在換行 URL 上方 **空行按 ↑** 會捲動跳動

</td>
<td width="50%" valign="top">

### 修補後

- `Intl.Segmenter`（UAX #29）詞邊界
- 空行對應到正確的視覺行

</td>
</tr>
</table>

<p align="center">
  <img src="assets/before-after.png" alt="空行導覽" width="88%">
</p>

<br>

## 影響哪些語言？

不限 CJK：

| Fix | 影響 |
|:----|:-----|
| **Option/Ctrl + ← / →** | **`[A-Za-z0-9_]` 以外** — 韓/日/中、西里爾、阿拉伯、希伯來、泰語等。純 ASCII 英文通常無感。與 [Codex CLI #16584](https://github.com/openai/codex/issues/16584) 等同類問題 |
| **空行 ↑** | **與語言無關** — 長 URL 軟換行 + 上方空行 |

<br>

## 快速開始

```bash
git clone https://github.com/vzts/cursor-cli-input-patch.git
cd cursor-cli-input-patch
python3 tests/test_behavior.py
python3 apply_patch.py
python3 apply_patch.py --install
```

<details>
<summary><strong>環境需求</strong></summary>
Python 3 · Node.js · macOS · 已安裝 Cursor CLI
</details>

<br>

## 修補範圍 · 命令

僅 `4794.index.js`。備份：`~/.local/share/cursor-cli-input-patch/backups/`

```bash
python3 apply_patch.py --restore
python3 apply_patch.py --ensure
```

<br>

<p align="center">
  <sub>非官方 · 與 Cursor 無關 · <a href="LICENSE">MIT</a> © 2026 <a href="https://github.com/vzts">vzts</a></sub>
</p>
