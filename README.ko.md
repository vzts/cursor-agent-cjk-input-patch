<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.ko.md"><strong>한국어</strong></a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.zh-TW.md">繁體中文</a>
</p>

<p align="center">
  <img src="assets/banner.png" alt="한글과 영어가 섞인 Cursor CLI 프롬프트" width="100%">
</p>

<h1 align="center">cursor-cli-input-patch</h1>

<p align="center">
  <strong><a href="https://cursor.com/docs/cli/overview">Cursor CLI</a> 유니코드 입력 패치</strong><br>
  <sub>단어 이동 · 빈 줄 스크롤 · 로컬 · 되돌리기 가능 · 비공식</sub>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT"></a>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey?style=flat-square" alt="macOS">
  <img src="https://img.shields.io/badge/Cursor%20CLI-unofficial-orange?style=flat-square" alt="Unofficial">
  <img src="https://img.shields.io/badge/python-3+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3">
</p>

<br>

> **명칭:** 공식 제품명은 [**Cursor CLI**](https://cursor.com/cli)이고, 실행 명령은 **`agent`**입니다 (`cursor-agent`는 구 alias). 이 repo는 설치된 CLI 번들을 패치하며 Cursor 바이너리를 포함하지 않습니다.

<table>
<tr>
<td width="50%" valign="top">

### 패치 전

**`agent`** 프롬프트에서 두 가지가 어색합니다:

- **Option/Alt + ← / →** 가 ASCII “단어”(`[A-Za-z0-9_]`)만 인식하고 나머지는 건너뜀
- 긴 URL 위 **빈 줄에서 ↑** 하면 스크롤이 튀고 URL 줄로 커서 이동

</td>
<td width="50%" valign="top">

### 패치 후

같은 키, 예측 가능한 동작:

- `Intl.Segmenter`로 유니코드(UAX #29) 단어 경계 인식
- 빈 줄이 올바른 시각적 줄에 매핑 — 스크롤 점프 없음

</td>
</tr>
</table>

<p align="center">
  <img src="assets/before-after.png" alt="빈 줄 이동: 공식 vs 패치" width="88%">
</p>

<br>

## 어떤 언어·사용자에게 영향?

CJK 한정이 아닙니다. 두 fix의 범위가 다릅니다:

| Fix | 영향 받는 사용자 |
|:----|:----------------|
| **Option/Ctrl + ← / →** (단어 이동) | **`[A-Za-z0-9_]` 밖 문자**를 쓰는 경우 — 한국어, 일본어, 중국어, 키릴, 아랍어, 히브리어, 태국어, 그리스어, 데바나가리 등. 순수 ASCII 영어만 쓰면 대체로 문제 없음. [Codex CLI](https://github.com/openai/codex/issues/16584), [Claude Code](https://github.com/anthropics/claude-code/issues/11099) 등에서도 유사 이슈 보고됨. |
| **줄바꿈된 긴 줄 위 빈 줄에서 ↑** | **언어 무관** — URL·경로 등 소프트 줄바꿈 + 그 위 빈 줄 |

한국어/CJK 불편에서 시작했지만, 단어 이동 패치는 stock ASCII regex가 건너뛰는 **모든 비ASCII 문자**에 도움이 됩니다.

<br>

## 빠른 시작

```bash
git clone https://github.com/vzts/cursor-cli-input-patch.git
cd cursor-cli-input-patch

python3 tests/test_behavior.py
python3 apply_patch.py
python3 apply_patch.py --install   # 선택: `agent` 실행마다 자동 패치
```

패치 후 **`agent`** 세션을 재시작하세요.

<details>
<summary><strong>필요 환경</strong></summary>

<br>

- **Python 3**, **Node.js**, **macOS**
- **Cursor CLI** 로컬 설치 (`curl https://cursor.com/install -fsS | bash`)

</details>

<br>

## 패치 대상

**`4794.index.js`** (텍스트 입력 번들)만 수정.

| | |
|:--|:--|
| **단어 이동** | `Intl.Segmenter` (`granularity: "word"`) |
| **빈 줄** | `findLine` — 빈 줄·EOL이 line 0으로 떨어지지 않음 |

디스크 경로(내부명 `cursor-agent`):

```
~/.local/share/cursor-agent/versions/<최신>/
~/Library/Application Support/Cursor/.../cursor-agent-worker/.../versions/<최신>/
```

<br>

## 패치하지 않음

| 영역 | 이유 |
|:-----|:-----|
| 일반 **← / →** | NFC 한글은 이미 음절 단위 |
| **Backspace / Delete** grapheme | 동일 |
| CJK **표시 폭 ↑ / ↓** | 터미널 1칸/코드포인트 |
| **IME** 후보창 | `agent` 멈춤 유발 — 제거 |

<br>

## 명령어 · 백업

```bash
python3 apply_patch.py --restore
python3 apply_patch.py --ensure
python3 apply_patch.py --list-backups
```

백업: `~/.local/share/cursor-cli-input-patch/backups/*.orig.bak`  
(구 경로 `cursor-agent-cjk-input-patch`는 자동 이전)

<br>

## 테스트

```bash
python3 tests/test_behavior.py
python3 tests/test_pty_arrows.py
```

<br>

<p align="center">
  <sub>비공식 · Cursor와 무관 · <a href="LICENSE">MIT</a> © 2026 <a href="https://github.com/vzts">vzts</a></sub>
</p>
