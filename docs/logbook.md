# Logbook

> 이 문서는 프로젝트 레벨의 단일 기록 문서다.
> 읽을 때는 항상 현재 `docs/logbook.md`와 최신 `docs/logbook_archive/logbook_*.md` 1개를 함께 본다.

## 읽기 규칙

- 이 문서는 `현재 프로젝트 스냅샷`, `현재 전역 결정`, `현재 활성 체크리스트`, `최근 로그`를 함께 유지한다.
- 새 로그를 쓰기 전에는 항상 아래 명령을 먼저 실행한다.
  - `python tools/logbook_archive_guard.py --archive-if-needed`
- active logbook 줄 수가 `1000`을 넘으면 현재 파일을 `docs/logbook_archive/logbook_YYMMDD_HHMM_*.md`로 archive하고, active logbook는 고정 섹션만 남긴 채 다시 시작한다.
- 에이전트는 비사소한 작업에서 항상 아래 순서로 문서를 읽는다.
  1. `AGENTS.md`
  2. `README.md`
  3. `docs/logbook.md`
  4. 최신 `docs/logbook_archive/logbook_*.md` 1개
  5. 관련 모듈 `README.md`
  6. 관련 모듈 `docs/logbook.md`
- 새 파일, 새 폴더, 새 문서, 복사본, 이동 결과, 다운로드 자산처럼 실제 산출물을 만들기 전에는 관련 기준 문서와 디렉토리 인벤토리 출력을 먼저 확인한다.
- 이 문서에는 프로젝트 레벨 현재 상태와 전역 결정만 둔다.
- 모듈별 상세 아키텍처, 고정 경로, 비채택 결정, 세부 실행 절차는 각 모듈 `README.md`에 둔다.

## 현재 프로젝트 스냅샷

- 상위 목표:
  - 이메일을 받아 구조화된 결과로 정리하고 Excel로 안전하게 누적하는 자동화 스택을 만든다.
  - 현재 우선 주경로는 `이메일 수신 -> 구조화 분석 -> Excel 출력`이다.
- 현재 작업 모드:
  - `협업 모드`
- 현재 전역 운영 문서:
  - 운영 방법과 정책: `AGENTS.md`
  - 프로젝트 소개, 전체 구조, 기능 배치 기준: `README.md`
  - 프로젝트 레벨 현재 상태와 최근 기록: `docs/logbook.md`
  - 저장소 공용 반복 workflow skill 원본: `.agents/skills/`
  - 새 저장소 시작용 공통 운영 팩: `templates/codex_starter/`
  - 모듈별 상세 기준: `mailbox/README.md`, `analysis/README.md`, `exports/README.md`, `llm/README.md`
  - 모듈별 현재 상태와 최근 기록: `mailbox/docs/logbook.md`, `analysis/docs/logbook.md`, `exports/docs/logbook.md`, `llm/docs/logbook.md`
- 현재 로컬 워크스페이스:
  - sibling 구조 `repo / envs / results / secrets`
- 비공개 자산과 자격증명의 canonical 로컬 시작 문서는 sibling `../secrets/README.local.md`다.
- 현재 로컬 산출물 정책:
  - 실제 사용자 메일, 첨부, workbook, 로그는 `../secrets/사용자 설정/<이름>/실행결과/` 아래에 둔다.
  - reference fixture는 `../secrets/사용자 설정/<이름>/참고자료/` 아래에서 읽기 전용으로 관리한다.
  - repo 내부 `<module>/results/`는 재현 가능한 smoke 결과와 소형 비교 자료만 둔다.
  - root `results/`는 현재 canonical 위치가 아니다.
- 현재 모듈 상태:
  - `mailbox`: bundle schema, fixture materialize, bundle reader, provider 자동 설정 후보 생성, connect/auth probe, local-only credential loader, real account latest IMAP fetch smoke가 있다.
  - `analysis`: `NormalizedMessage -> ExtractedRecord` structured output 경로와 multimodal 입력 builder, fixture/runtime bundle smoke가 있고, real bundle 1건의 analysis/export handoff를 검증했다.
  - `exports`: 템플릿 reader, semantic mapping, projection, workbook append, 회귀 guardrail이 있다.
  - `llm`: OpenAI wrapper, usage logging, 가격표 snapshot 기반 비용 추정, structured output transport가 있다.

## 현재 전역 결정

- 시작 게이트는 항상 `AGENTS.md -> README.md -> docs/logbook.md`다.
- stable truth는 `README.md`와 각 모듈 `README.md`, active truth는 `docs/logbook.md`와 각 모듈 `docs/logbook.md`에 둔다.
- 런타임 데이터 계약은 `MailBundle -> NormalizedMessage -> ExtractedRecord -> ExportRow` 4단계를 유지한다.
- 메일 설정 탐지는 `rule/probe-first`, LLM 보조 fallback 기준을 유지한다.
- 입력 해석은 multimodal-first로 두고, 이미지나 스캔 문서가 있으면 실제 이미지 입력을 우선 활용한다.
- 템플릿 해석은 rule-first로 시작하고, unresolved header만 LLM fallback으로 보충한다.
- GUI와 프로필 편집은 향후 `app/`에 두고, 장시간 실행 조율과 배치 런타임은 향후 `runtime/`에 둔다.
- `app/`과 `runtime/`은 실제 코드가 처음 들어가는 턴에만 만들고, 그때 각 디렉토리 `README.md`와 `docs/logbook.md`를 함께 연다.
- 실제 inbox bundle, 실제 workbook, 실제 usage log는 `../secrets/사용자 설정/<이름>/실행결과/`에 두고, 재현 가능한 작은 smoke 결과와 비교 요약만 repo 내부 공식 위치 후보를 쓴다.

## 현재 활성 체크리스트

- 현재 문서 운영 체계 재편:
  - 관련 기준 문서:
    - [`../AGENTS.md`](../AGENTS.md)
    - [`../README.md`](../README.md)
    - [`./logbook_archive/logbook_260408_0956_pre_golden_refactor_summary.md`](./logbook_archive/logbook_260408_0956_pre_golden_refactor_summary.md)
  - 체크리스트:
    - [x] 루트 운영 문서를 `AGENTS.md + README.md + docs/logbook.md` 체계로 재편
    - [x] legacy `docs/*` 기준 문서를 archive로 보존
    - [x] 모듈별 `docs/logbook.md` 시드 추가
    - [x] repo-local skill 8종 도입
    - [x] 운영 보조 tool 4종 도입
    - [x] starter template 운영 팩 추가
    - [x] sibling `../secrets/README.local.md` 시작 문서 추가
- 다음 제품 작업:
  - [x] 실제 이메일 계정 기준 mailbox auth probe 실행
  - [x] 최신 inbox 1건 fetch smoke로 `MailBundle` 저장 경로 연결
  - [x] 저장된 최신 bundle 1건을 materialized analysis smoke와 handoff 기준으로 연결
  - [ ] real bundle 기준 unresolved export 컬럼과 summary 품질 개선
  - [ ] `app/`과 `runtime/`의 실제 디렉토리 도입 시점과 경계 구체화

## 최근 로그

### 2026-04-08 | Human + Codex | real bundle analysis/export handoff 검증

- 방금 저장한 최신 real bundle 1건을 기준으로 `analysis/materialized_bundle_smoke.py`와 `analysis/materialized_bundle_pipeline_smoke.py`를 실제 실행해 `ExtractedRecord` 생성과 workbook append까지 확인했다.
- analysis smoke는 runtime `extracted_record.json`을 남겼고, pipeline smoke는 runtime `projected_row.json`과 새 결과 workbook을 남겼다.
- handoff 과정에서 `analysis/materialized_bundle_smoke.py`가 직접 스크립트 실행 시 relative import로 실패하던 문제를 고쳐 CLI 진입이 바로 되도록 맞췄다.
- 첫 real bundle 품질 확인 결과 `contact_name`, `phone_number`, `email_address`, `website_or_social`, `industry`, 소개/사업내용 요약은 채워졌고 workbook append도 성공했다.
- 다만 `company_name`, `product_or_service`, `application_purpose`, `request_summary`는 이번 메일 성격상 또는 현재 추출 규칙 한계로 비어 있어, 다음 개선 초점은 real bundle 기준 unresolved export 컬럼과 summary 품질 보강으로 잡는다.

### 2026-04-08 | Human + Codex | 실제 이메일 연동 1단계 완료

- `mailbox`에 local-only 계정 정보 loader를 추가해 sibling `secrets` 아래의 로컬 계정 문서에서 이메일 주소, 로그인 id, 비밀번호, 프로필 루트를 읽게 했다.
- mailbox auth probe는 명시된 로그인 id를 먼저 시도하고, 실패하면 이메일 주소로 자동 fallback 하도록 확장했다.
- generic host 패턴만으로 잡히지 않는 계정을 위해 MX 레코드 기반 mail host 후보 생성 경로를 추가했다.
- 실제 최신 메일 1건 fetch는 IMAP read-only `BODY.PEEK[]` 기준으로 구현했고, 결과를 로컬 runtime bundle 아래 `raw.eml`, `preview.html`, `normalized.json`, `summary.md`, `attachments/` 구조로 저장했다.
- tracked 문서에는 실제 주소, 비밀번호, 메일 원문을 남기지 않고, 성공 bundle과 report는 모두 sibling `../secrets/사용자 설정/<이름>/실행결과/` 아래 로컬 경로에만 남겼다.
- 성공한 bundle 1건에 대해 `normalized.json` 재읽기까지 확인해 다음 analysis smoke로 넘길 준비를 마쳤다.

### 2026-04-08 | Human + Codex | 골든 레퍼런스 기반 운영 문서 체계로 재편

- 기준 문서는 골든 레퍼런스 운영 팩과 기존 legacy canonical 문서 묶음, 각 모듈 `README.md`였다.
- 기존 레포는 legacy status 중심 체계였고, 새 운영 기준은 루트 `AGENTS.md`, 루트 `README.md`, 프로젝트 `docs/logbook.md`, 모듈 `docs/logbook.md`, repo-local skill, 운영 tool, starter template을 중심으로 다시 세우는 방향으로 정리했다.
- 골든 레퍼런스의 원본 프로젝트 도메인 표현은 남기지 않고, 현재 이메일 자동화 프로젝트 기준으로 전면 재작성했다.
- 기존 legacy canonical 문서와 기존 최근 로그는 active에서 내리고 `docs/logbook_archive/`에 legacy archive로 보존했다.
- 새 canonical 경로는 `AGENTS.md`, `README.md`, `docs/logbook.md`, 각 모듈 `README.md`, 각 모듈 `docs/logbook.md`로 고정했다.
- 반복 절차를 repo-local skill 8종으로 옮겼고, 누락되어 있던 `directory_inventory.py`, `logbook_archive_guard.py`, `logbook_archive_all.py`, `git_sync_all.sh`를 현재 레포 기준 대체 구현으로 추가했다.
- 새 저장소에 복사해 쓸 수 있는 generic 운영 팩은 `templates/codex_starter/`에 따로 정리했다.
- local private boundary의 시작 문서는 sibling `../secrets/README.local.md`로 세웠다.

### 2026-04-08 | Human + Codex | legacy 운영 문서 archive 정리

- 이전 active 기준 문서 묶음과 기존 최근 로그를 `docs/logbook_archive/` 아래로 보존했다.
- 기존 최근 로그 전문은 `logbook_260408_0956_legacy_recent_log.md`에 그대로 보관했다.
- legacy canonical 문서의 핵심 판단과 경로는 `logbook_260408_0956_pre_golden_refactor_summary.md`로 묶어 현재 체계에서 다시 읽을 수 있게 정리했다.

### 2026-04-08 | Human + Codex | 산출물 경계 예시와 미래 계층 도입 규칙 명확화

- 문서 체계가 바뀐 뒤에도 `repo 내부 결과물`과 `실사용 runtime 결과물`의 경계가 아직 추상적으로 보일 수 있어, 실제 예시를 추가해 기준을 더 분명하게 적었다.
- 실제 inbox bundle, 실제 workbook, 실제 usage log는 계속 sibling `../secrets/사용자 설정/<이름>/실행결과/`에 두고, 재현 가능한 small smoke 보고서와 diff summary만 repo 내부 공식 위치 후보를 쓰는 기준을 다시 적었다.
- `app/`과 `runtime/`은 이름만 먼저 정해 두고, 실제 코드가 처음 들어가는 턴에만 디렉토리를 만들며 같은 턴에 `README.md`와 `docs/logbook.md`를 함께 연다는 규칙도 추가했다.

### 2026-04-08 | Human + Codex | 골든 레퍼런스 검토 폴더 정리

- 골든 레퍼런스의 운영 규칙, skill, tool, starter template 내용을 현재 레포 기준으로 모두 옮긴 뒤, 상위 워크스페이스에 임시로 두었던 `새로 업데이트된 문서 정책 골든 레퍼런스` 폴더를 삭제했다.
- 이후 기준 문서는 현재 레포의 `AGENTS.md`, `README.md`, `docs/logbook.md`, `.agents/skills/`, `tools/`, `templates/codex_starter/`만 보면 된다.
