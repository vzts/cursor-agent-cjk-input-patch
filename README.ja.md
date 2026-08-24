<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.ja.md"><strong>日本語</strong></a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <img src="assets/banner.png" alt="韓国語と英語の Cursor CLI プロンプト" width="100%">
</p>

<h1 align="center">cursor-cli-input-patch</h1>

<p align="center">
  <strong><a href="https://cursor.com/docs/cli/overview">Cursor CLI</a> Unicode 入力パッチ</strong><br>
  <sub>単語移動 · 空行スクロール · ローカル · 可逆 · 非公式</sub>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="macOS">
  <img src="https://img.shields.io/badge/Cursor%20CLI-unofficial-orange?style=flat-square" alt="Unofficial">
  <img src="https://img.shields.io/badge/python-3+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3">
</p>

<br>

> **名称:** 公式製品名は [**Cursor CLI**](https://cursor.com/cli)。実行コマンドは **`agent`**（`cursor-agent` はレガシー alias）。本 repo はインストール済み CLI バンドルをパッチします。

<table>
<tr>
<td width="50%" valign="top">

### パッチ前

**`agent`** プロンプトで:

- **Option/Alt + ← / →** が ASCII 単語 (`[A-Za-z0-9_]`) のみ認識
- 折り返し URL 上の **空行で ↑** するとスクロールが飛ぶ

</td>
<td width="50%" valign="top">

### パッチ後

- `Intl.Segmenter`（UAX #29）で単語境界
- 空行が正しい視覚行にマップ

</td>
</tr>
</table>

<p align="center">
  <img src="assets/before-after.png" alt="空行ナビ" width="88%">
</p>

<br>

## 影響する言語・ユーザー

CJK 限定ではありません:

| Fix | 影響 |
|:----|:-----|
| **Option/Ctrl + ← / →** | **`[A-Za-z0-9_]` 外** — 韓国語、日本語、中国語、キリル、アラビア語、ヘブライ語、タイ語など。[Codex CLI #16584](https://github.com/openai/codex/issues/16584) 等と同種 |
| **空行で ↑** | **言語非依存** — 長い URL の折り返し + 上の空行 |

<br>

## クイックスタート

```bash
git clone https://github.com/vzts/cursor-cli-input-patch.git
cd cursor-cli-input-patch
python3 tests/test_behavior.py
python3 apply_patch.py
python3 apply_patch.py --install
```

<details>
<summary><strong>必要環境</strong></summary>
Python 3 · Node.js · macOS · Cursor CLI インストール済み
</details>

<br>

## パッチ対象 · スキップ · コマンド

`4794.index.js` のみ。バックアップ: `~/.local/share/cursor-cli-input-patch/backups/`

```bash
python3 apply_patch.py --restore
python3 apply_patch.py --ensure
```

<br>

<p align="center">
  <sub>非公式 · Cursor とは無関係 · <a href="LICENSE">MIT</a> © 2026 <a href="https://github.com/vzts">vzts</a></sub>
</p>
