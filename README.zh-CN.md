<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh-CN.md"><strong>简体中文</strong></a> ·
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <img src="assets/banner.png" alt="含韩文与英文的 Cursor CLI 提示符" width="100%">
</p>

<h1 align="center">cursor-cli-input-patch</h1>

<p align="center">
  <strong><a href="https://cursor.com/docs/cli/overview">Cursor CLI</a> Unicode 输入补丁</strong><br>
  <sub>按词移动 · 空行滚动 · 本地 · 可撤销 · 非官方</sub>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="macOS">
  <img src="https://img.shields.io/badge/Cursor%20CLI-unofficial-orange?style=flat-square" alt="Unofficial">
  <img src="https://img.shields.io/badge/python-3+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3">
</p>

<br>

> **命名：** 官方产品名为 [**Cursor CLI**](https://cursor.com/cli)，运行命令为 **`agent`**（`cursor-agent` 为旧别名）。本仓库只补丁已安装的 CLI 包，不包含 Cursor 二进制。

<table>
<tr>
<td width="50%" valign="top">

### 补丁前

**`agent`** 提示符中:

- **Option/Alt + ← / →** 仅识别 ASCII “词” (`[A-Za-z0-9_]`)
- 在换行 URL 上方 **空行按 ↑** 会滚动跳动

</td>
<td width="50%" valign="top">

### 补丁后

- `Intl.Segmenter`（UAX #29）词边界
- 空行映射到正确的视觉行

</td>
</tr>
</table>

<p align="center">
  <img src="assets/before-after.png" alt="空行导航" width="88%">
</p>

<br>

## 影响哪些语言？

不限于 CJK：

| Fix | 影响 |
|:----|:-----|
| **Option/Ctrl + ← / →** | **`[A-Za-z0-9_]` 以外** — 韩/日/中、西里尔、阿拉伯、希伯来、泰语等。纯 ASCII 英文通常无感。与 [Codex CLI #16584](https://github.com/openai/codex/issues/16584) 等同类问题 |
| **空行 ↑** | **与语言无关** — 长 URL 软换行 + 上方空行 |

<br>

## 快速开始

```bash
git clone https://github.com/vzts/cursor-cli-input-patch.git
cd cursor-cli-input-patch
python3 tests/test_behavior.py
python3 apply_patch.py
python3 apply_patch.py --install
```

<details>
<summary><strong>环境要求</strong></summary>
Python 3 · Node.js · macOS · 已安装 Cursor CLI
</details>

<br>

## 补丁范围 · 命令

仅 `4794.index.js`。备份：`~/.local/share/cursor-cli-input-patch/backups/`

```bash
python3 apply_patch.py --restore
python3 apply_patch.py --ensure
```

<br>

<p align="center">
  <sub>非官方 · 与 Cursor 无关 · <a href="LICENSE">MIT</a> © 2026 <a href="https://github.com/vzts">vzts</a></sub>
</p>
