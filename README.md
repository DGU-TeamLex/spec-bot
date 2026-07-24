# TeamLex spec-bot

TeamLex 기능명세서 메일이 도착하면 자동으로 **frontend / backend 레포에 Draft PR** 을 만드는
GitHub Actions 자동화. **사용자 맥북과 무관하게 GitHub 서버(클라우드)에서 cron 으로 실행**된다.

## 동작 흐름

1. **메일 탐지** — Gmail(IMAP)에서 최근 60일 메일 중 제목/본문에 `기능명세서`·`기능정의` 등
   키워드가 포함되고 아직 처리 안 된(`TeamLex-Processed` 라벨 없는) 메일을 찾는다.
   *발신자 조건은 보지 않는다 — 내용만 본다.*
2. **코드 생성** — Anthropic API(Claude)로 명세 → FE/BE 파일 초안을 JSON 으로 생성.
3. **Draft PR** — 각 레포에 `feat/spec-<날짜>-<기능>` 브랜치 + 커밋 + **Draft PR**.
   `main` 에 직접 푸시하지 않는다. (FE PR 은 "참고용 초안"으로 표시 — FE 는 직접 작성하는 영역)
4. **중복 방지** — 처리한 메일에 Gmail 라벨 `TeamLex-Processed` 부착.

## 필요한 설정 (한 번만)

이 레포 **Settings → Secrets and variables → Actions** 에 아래 **Secrets** 추가:

| Secret | 값 | 발급 방법 |
|---|---|---|
| `GMAIL_ADDRESS` | `choigod10234@gmail.com` | 본인 Gmail 주소 |
| `GMAIL_APP_PASSWORD` | 16자리 앱 비밀번호 | 아래 ① |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | 아래 ② |
| `GH_PAT` | GitHub 토큰 | 아래 ③ |

(선택) **Variables** 에 `ANTHROPIC_MODEL` 을 추가하면 모델 변경 가능. 기본값 `claude-sonnet-4-6`.
더 높은 품질이 필요하면 `claude-opus-4-8`.

### ① Gmail 앱 비밀번호 (IMAP 읽기용)
1. Google 계정에 **2단계 인증** 활성화 (필수 선행 조건).
2. https://myaccount.google.com/apppasswords 접속 → 앱 이름 입력(예: `teamlex-spec-bot`) → 생성.
3. 나온 **16자리** 를 공백 없이 `GMAIL_APP_PASSWORD` 에 넣는다.
> IMAP 사용을 위해 Gmail 설정 → "전달 및 POP/IMAP" 에서 IMAP 이 켜져 있어야 한다.

### ② Anthropic API 키
1. https://console.anthropic.com → API Keys → Create Key.
2. 값을 `ANTHROPIC_API_KEY` 에 넣는다. (사용량만큼 과금됨)

### ③ GitHub PAT (두 레포에 push/PR)
기본 `GITHUB_TOKEN` 은 이 레포에만 권한이 있어 **다른 레포(frontend/backend)** 에 PR 을 못 만든다.
그래서 조직 레포 접근 권한이 있는 토큰이 필요하다.
- **Fine-grained PAT** (권장): https://github.com/settings/tokens?type=beta →
  Resource owner = `DGU-TeamLex`, Repository access = `frontend`, `backend` →
  Permissions: **Contents: Read and write**, **Pull requests: Read and write** → 생성.
- 값을 `GH_PAT` 에 넣는다.

## 실행

- **자동**: 매일 KST 09:07 (cron). 새 명세서 메일이 있을 때만 PR 생성.
- **수동 테스트**: Actions 탭 → "TeamLex 기능명세서 → Draft PR" → **Run workflow**.

## 보안 메모

- 메일 본문은 신뢰할 수 없는 입력으로 취급한다. 본문에 든 "명령 실행/토큰 유출/다른 레포 변경"
  류의 지시는 코드 생성 시 무시하도록 시스템 프롬프트에 못박혀 있다.
- 모든 산출물은 **Draft PR** 이라 사람이 검토 후에만 머지된다. main 직접 변경 없음.
- 비밀값은 전부 GitHub Secrets 에 저장되며 코드/로그에 노출되지 않는다.

## 한계

- 첨부파일(.hwp/.pdf/.docx) 본문은 현재 자동 파싱하지 않는다. **메일 본문 텍스트** 기준으로
  생성하며, 첨부에 상세가 있으면 PR 본문에 그 사실을 표기한다. (필요 시 파서 추가 가능)
- 생성 코드는 "초안"이다. 빌드·테스트는 사람이 PR 에서 확인한다.

## 📁 구조

```
.
├── spec_bot.py                    # 메인 파이프라인 (IMAP 탐지 → Claude 코드 생성 → Draft PR)
│                                  #   SPEC_KEYWORDS / LOOKBACK_DAYS(60일) / PROCESSED_LABEL 상수,
│                                  #   safe_path() 로 레포 밖 경로 쓰기 차단
├── scripts/
│   ├── fetch_specs.py             # 미처리 명세서 메일을 JSON 배열로 출력 (에이전트 루틴용)
│   └── mark_processed.py          # 처리한 메일에 TeamLex-Processed 라벨 부착
├── .github/workflows/spec-to-pr.yml  # 매일 KST 09:07 cron + workflow_dispatch, concurrency 로 중복 실행 방지
├── ROUTINE_PROMPT.md              # 명세서 메일 → Draft PR 을 에이전트 루틴으로 돌릴 때의 실행 지시
├── ISSUE_ROUTINE_PROMPT.md        # GitHub 이슈 → 코드 수정 → Draft PR 루틴 실행 지시 (라벨 `claude-처리완료`)
├── HANDOFF.md                     # 맥락 없이 이어받을 수 있게 정리한 인수인계 문서
└── requirements.txt               # anthropic
```

`spec_bot.py`(GitHub Actions 경로)와 `scripts/` + `*_ROUTINE_PROMPT.md`(에이전트 루틴 경로)는
같은 목표를 서로 다른 실행 환경에서 수행하는 두 갈래다. 어느 쪽이든 **결과물은 항상 Draft PR** 이며
`main` 에 직접 push 하지 않는다.

## 👤 기여도 & 개발 환경

| 항목 | 내용 |
|---|---|
| **기여 비율** | **100%** (단독 개발) |
| **커밋** | 2 / 2 (본인 / 전체 사람 커밋) |
| **참여 인원** | 1명 |
| **AI 코딩 도구** | Claude Code |

<sub>기여 비율은 커밋 author 이메일 기준 집계이며 봇·자동화 커밋은 제외했습니다.</sub>
