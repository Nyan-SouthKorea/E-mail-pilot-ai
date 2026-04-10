# E-mail-pilot-ai

이 저장소는 이메일을 받아 필요한 정보를 구조화하고 Excel로 반영하는 개인용 자동화 스택을 만드는 리포지토리다. 현재 주경로는 `이메일 수신 -> 구조화 분석 -> triage 검토 -> Excel 출력`이며, 실제 메일 계정과 프로필별 Excel 템플릿을 안전하게 다루는 방향을 우선한다.

처음 방문한 사람은 이 문서부터 읽으면 된다. 실제 작업을 시작하는 사람은 그다음 [AGENTS.md](./AGENTS.md), [docs/logbook.md](./docs/logbook.md), [docs/feature_catalog.md](./docs/feature_catalog.md), 최신 [docs/logbook_archive](./docs/logbook_archive) 1개, 관련 모듈 `README.md`, 관련 모듈 `docs/logbook.md` 순서로 들어간다.

비공개 자격증명, 실제 메일 원문, 실제 사용자 workbook, 공유 워크스페이스 운영이 포함된 작업은 tracked 문서만 보지 않고 sibling `../secrets/README.local.md`와 그 하위 로컬 문서를 함께 본다.

## 프로젝트 한눈에 보기

- 실제 메일 계정 연결은 `mailbox`가 맡는다.
- 구조화 분류, 필드 추출, 요약, 멀티모달 해석은 `analysis`가 맡는다.
- 프로필별 Excel 템플릿 해석과 workbook append는 `exports`가 맡는다.
- OpenAI 호출 transport, usage logging, 공용 설정은 `llm`이 맡는다.
- `app/`은 Windows 데스크톱 창과 로컬 Web UI를 맡고, `runtime/`은 공유 워크스페이스 save, 상태 저장, sync orchestration을 맡는다.

## 현재 구현 범위

| 모듈 | 역할 | 현재 상태 |
|---|---|---|
| [mailbox](./mailbox/README.md) | 메일 번들 보관, 자동 설정 후보 생성, probe, 정규화 입력 준비 | fixture materialize, bundle reader, connect/auth probe, real account latest IMAP fetch, INBOX read-only backfill smoke 구현 |
| [analysis](./analysis/README.md) | `NormalizedMessage -> ExtractedRecord` 해석, 분류, 요약, 멀티모달 추출 | fixture/runtime bundle smoke, real-bundle quality smoke, 3-way triage, HTML review board, application-only batch export 구현 |
| [exports](./exports/README.md) | 템플릿 해석, 열 의미 매핑, projection, workbook append | rule-first mapping, LLM fallback, workbook append, 회귀 guardrail 구현 |
| [llm](./llm/README.md) | OpenAI wrapper, usage logging, 비용 추정, structured output transport | 공용 wrapper와 usage log 골격 구현 |
| [runtime](./runtime/README.md) | 공유 워크스페이스 save, sqlite state, write lock, sync orchestration | workspace manifest, encrypted secrets, state DB, feature registry/run history, sample workspace, feature harness smoke, CLI 구현 |
| [app](./app/README.md) | Windows 데스크톱 셸과 로컬 Web UI | FastAPI UI, pywebview launcher, workspace open/create, settings, review center, 관리도구, UI smoke, 포터블 exe packaging/CI 기준 구현 |

## 새 기능을 어디에 둘까

새 기능 추가, 폴더 이동, 레이어 경계 판단이 필요한 작업에서는 이 섹션을 프로젝트 전역의 단일 기준으로 본다. 운영 규칙은 [`AGENTS.md`](./AGENTS.md)가 맡고, 실제 배치 기준은 이 섹션이 맡는다.

### 1. 먼저 소속부터 고른다

| 질문 | 위치 |
|---|---|
| 메일 서버 탐지, auth probe, inbox fetch, raw bundle 저장, attachment 추출인가 | [`mailbox/`](./mailbox/README.md) |
| 메일 본문/첨부 해석, 분류, 필드 추출, 요약, 이미지 입력 해석인가 | [`analysis/`](./analysis/README.md) |
| Excel 템플릿 해석, 열 의미 매핑, projection, workbook append, diff 검증인가 | [`exports/`](./exports/README.md) |
| 모델 설정, 호출 wrapper, usage logging, 공용 structured output transport인가 | [`llm/`](./llm/README.md) |
| GUI, 프로필 편집, 사용자 실행 진입점, 패키징 진입점인가 | [`app/`](./app/README.md) |
| 장시간 실행 조율, polling loop, queue worker, batch run, watchdog, 공유 상태 저장인가 | [`runtime/`](./runtime/README.md) |

### 2. 의존 방향은 아래를 기본으로 둔다

- `app -> runtime -> mailbox / analysis / exports / llm`
- `analysis -> llm`
- `exports -> llm`
- `mailbox`는 `analysis`와 `exports`를 직접 import하지 않는다.
- `llm`은 메일 도메인 규칙이나 Excel 규칙을 직접 알지 않는다.
- `runtime`은 UI 세부사항을 직접 알지 않고, `app`은 low-level mailbox probe 세부사항을 직접 구현하지 않는다.

### 3. 새 추상화는 아래 조건이 있을 때만 만든다

- 둘 이상의 실행 경로가 같은 기능을 공유한다.
- 같은 wiring 코드가 두 군데 이상 반복된다.
- 상태 원본이 둘 이상 생겨 충돌 위험이 있다.
- 위 조건이 약하면 새 계층을 만들지 말고 현재 계층 안에서 먼저 작게 정리한다.

### 4. 빠른 판단 체크리스트

- 이 기능은 메일 원본 보존과 설정 탐지 문제인가?
- 이 기능은 구조화 추출과 요약 문제인가?
- 이 기능은 Excel 양식 해석과 workbook 갱신 문제인가?
- 이 기능은 공용 LLM transport와 로그 문제인가?
- 이 기능은 GUI나 사용자 실행 흐름 문제인가?
- 이 기능은 장시간 실행 조율 문제인가?

## 처음 방문한 사람이 읽는 순서

### 1. 이 문서

- 프로젝트가 무엇인지
- 어떤 모듈이 있고 어디까지 왔는지
- 전체 구조와 기능 배치 기준이 어떻게 생겼는지

### 2. 작업을 실제로 시작할 때

1. [AGENTS.md](./AGENTS.md)
2. [docs/logbook.md](./docs/logbook.md)
3. [docs/feature_catalog.md](./docs/feature_catalog.md)
4. 최신 [docs/logbook_archive](./docs/logbook_archive) 안의 `logbook_*.md` 1개
5. 관련 모듈 `README.md`
6. 관련 모듈 `docs/logbook.md`

## 어디에 무엇이 기록되는가

| 위치 | 역할 |
|---|---|
| [README.md](./README.md) | 처음 방문자를 위한 프로젝트 소개, 전체 구조, 프로젝트 전역 고정 메모 |
| [AGENTS.md](./AGENTS.md) | 운영 정책과 작업 방법의 단일 기준 |
| [docs/logbook.md](./docs/logbook.md) | 현재 상태, 전역 결정, 최근 로그의 단일 기준 |
| [docs/feature_catalog.md](./docs/feature_catalog.md) | 현재 제품/운영 기능 카탈로그와 공식 접근점 인덱스 |
| [docs/logbook_archive](./docs/logbook_archive) | 이전 active logbook와 legacy 기준 문서 archive |
| `.agents/skills/` | 이 저장소 공용 반복 workflow skill 원본 |
| `templates/codex_starter/` | 새 저장소 시작 때 복사해 쓰는 공통 운영 팩 |
| 각 모듈 `README.md` | 해당 모듈의 안정된 설명, 고정 결정, 경로, 실행 절차 |
| 각 모듈 `docs/logbook.md` | 해당 모듈의 현재 상태, 최근 변경, 다음 작업 |
| 각 모듈 `docs/보고서/` | 외부 공유 또는 사용자 요청이 있을 때 만드는 요약 보고서의 공식 위치 |
| 각 모듈 `docs/환경/` | 설치, 재현, 운영 절차의 공식 위치 |
| 각 모듈 `results/` | repo-safe한 소형 실행 산출물의 공식 위치 |
| `assets/` | root `README.md`가 직접 참조하는 프로젝트 전역 공용 자산의 공식 위치 |
| `../secrets/README.local.md` | tracked repo에 적지 않는 비공개 자산과 자격증명 운영의 로컬 시작 문서 |

## 레포 구조

```text
.
├── .agents/skills/
├── AGENTS.md
├── analysis/
├── app/
├── docs/
│   └── logbook_archive/
├── exports/
├── llm/
├── mailbox/
├── runtime/
├── templates/
│   └── codex_starter/
└── tools/
```

## 로컬 워크스페이스와 산출물 규칙

- 로컬 워크스페이스는 기본적으로 `repo / envs / results / secrets` sibling 구조를 사용한다.
- 실제 사용자 메일, 첨부, workbook, profile 로그는 tracked repo가 아니라 sibling `../secrets/사용자 설정/<이름>/실행결과/`에서 관리한다.
- Windows 앱과 서버 검증을 같이 쓰는 경우에는 공유 워크스페이스 root 아래 `profile/`를 같은 canonical profile root로 사용한다.
- reference fixture는 sibling `../secrets/사용자 설정/<이름>/참고자료/`에서 읽기 전용으로 관리한다.
- repo 내부 `<module>/results/`는 재현 가능한 smoke 결과, 비교 요약, 소형 metadata만 둔다.
- 빠른 예시:
  - 실제 inbox fetch 결과 bundle, 실제 export workbook, 실제 OpenAI usage log는 `../secrets/사용자 설정/<이름>/실행결과/`에 둔다.
  - 분류 검토용 HTML 보드와 batch review JSON은 `../secrets/사용자 설정/<이름>/실행결과/로그/review/`에 둔다.
  - 공유 워크스페이스를 쓰면 같은 구조를 `workspace/profile/실행결과/` 아래에서 그대로 유지한다.
  - `auth probe` 요약 JSON, regression diff summary, deterministic smoke 보고서처럼 다시 만들 수 있는 작은 산출물만 `mailbox/results/`, `exports/results/`, `llm/results/` 같은 공식 위치 후보를 쓴다.
- 새 산출물 폴더와 시간이 지나며 누적되는 문서는 `YYMMDD_HHMM_설명` prefix를 사용한다.
- 새 파일이나 폴더를 만들기 전에는 `python tools/directory_inventory.py --module <module> --kind <kind> --candidate-name <name>`로 기존 구조를 먼저 확인한다.

## 프로젝트 전역 고정 메모

- 현재 주경로는 `이메일 수신 -> 구조화 분석 -> triage 검토 -> Excel 출력`이다.
- 제품 주 사용 흐름은 `exe 실행 -> 세이브 파일 불러오기 -> 워크스페이스 암호 입력 -> 동기화 -> 자동 수집/분류/정리/엑셀 반영 -> 같은 창에서 검토/수정`이다.
- 사용자는 세이브 파일 경로를 직접 외우기보다 앱의 `찾아보기` 버튼으로 고르고, 홈의 `세이브 파일 가이드`에서 폴더 기준을 확인하는 흐름을 기본으로 본다.
- Windows 실행의 공식 경로는 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe` 하나다.
- 제품/운영 기능의 canonical 카탈로그는 `docs/feature_catalog.md`와 `runtime/feature_registry.py`가 함께 맡는다.
- 반복 기능 검증은 `runtime/feature_harness_smoke.py`, `app/ui_smoke.py`, `runtime/cli.py feature-*` 명령을 기준으로 한다.
- `Z:` 공유 폴더에서는 세이브 파일만 열고, exe는 절대 실행하지 않는다.
- Windows 빌드는 `D:\EmailPilotAI\repo`에서 수행하고, 완료 후 최종 실행본은 `D:\EmailPilotAI\portable\EmailPilotAI\`만 남긴다.
- 서버와 Windows가 결과를 같이 보는 기준은 exe 위치가 아니라 같은 세이브 파일 폴더를 열었는지다.
- 메일 설정 탐지는 `도메인 규칙 -> provider preset -> autodiscover/autoconfig -> 실제 probe` 순서를 우선한다.
- `MailBundle -> NormalizedMessage -> ExtractedRecord -> ExportRow` 4층 계약은 유지한다.
- `ExtractedRecord`는 `application / not_application / needs_human_review` 3분류 triage를 기본으로 가진다.
- 입력 해석은 현재 fixture 2건에 과적합하지 않고, 이미지/스캔/ZIP 복합 첨부까지 포괄하는 방향을 유지한다.
- Excel 출력은 전역 고정 양식보다 프로필별 템플릿 해석을 우선한다.
- 자동 workbook 반영은 `application`이면서 `기업 식별 신호 + 연락처 신호`를 만족하는 메일만 대상으로 한다.
- root `README.md`에 직접 쓰이는 전역 공용 자산이 필요해질 때만 `assets/`를 만든다.
- 공유 워크스페이스 save는 `workspace.epa-workspace.json + secure/secrets.enc.json + state/state.sqlite + locks/write.lock + profile/` 구조를 기본으로 본다.
- static HTML review board는 fallback/debug 산출물이고, 사용자 검토의 active canonical 상태는 `runtime` state DB와 `app` 리뷰센터가 맡는다.
