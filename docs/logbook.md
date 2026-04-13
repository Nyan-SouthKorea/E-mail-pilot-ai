# Logbook

> 이 문서는 프로젝트 레벨의 단일 기록 문서다.
> 읽을 때는 항상 현재 `docs/logbook.md`와 최신 `docs/logbook_archive/logbook_*.md` 1개를 함께 본다.

## 읽기 규칙

- 이 문서는 `현재 프로젝트 스냅샷`, `현재 전역 결정`, `현재 실행 계획`, `현재 체크포인트`, `현재 활성 체크리스트`, `최근 로그`를 함께 유지한다.
- 새 로그를 쓰기 전에는 항상 아래 명령을 먼저 실행한다.
  - `python tools/logbook_archive_guard.py --archive-if-needed`
- active logbook 줄 수가 `1000`을 넘으면 현재 파일을 `docs/logbook_archive/logbook_YYMMDD_HHMM_*.md`로 archive하고, active logbook는 고정 섹션만 남긴 채 다시 시작한다.
- 에이전트는 비사소한 작업에서 항상 아래 순서로 문서를 읽는다.
  1. `AGENTS.md`
  2. `README.md`
  3. `docs/logbook.md`
  4. `docs/feature_catalog.md`
  5. 최신 `docs/logbook_archive/logbook_*.md` 1개
  6. 관련 모듈 `README.md`
  7. 관련 모듈 `docs/logbook.md`
- 새 파일, 새 폴더, 새 문서, 복사본, 이동 결과, 다운로드 자산처럼 실제 산출물을 만들기 전에는 관련 기준 문서와 디렉토리 인벤토리 출력을 먼저 확인한다.
- 이 문서에는 프로젝트 레벨 현재 상태와 전역 결정만 둔다.
- 모듈별 상세 아키텍처, 고정 경로, 비채택 결정, 세부 실행 절차는 각 모듈 `README.md`에 둔다.

## 현재 프로젝트 스냅샷

- 상위 목표:
  - 이메일을 받아 구조화된 결과로 정리하고 Excel로 안전하게 누적하는 자동화 스택을 만든다.
  - 현재 우선 주경로는 `이메일 수신 -> 구조화 분석 -> triage 검토 -> Excel 출력`이다.
- 현재 작업 모드:
  - `협업 모드`
- 현재 전역 운영 문서:
  - 운영 방법과 정책: `AGENTS.md`
  - 프로젝트 소개, 전체 구조, 기능 배치 기준: `README.md`
  - 프로젝트 레벨 현재 상태와 최근 기록: `docs/logbook.md`
  - 제품/운영 기능 카탈로그: `docs/feature_catalog.md`
  - 저장소 공용 반복 workflow skill 원본: `.agents/skills/`
  - 새 저장소 시작용 공통 운영 팩: `templates/codex_starter/`
  - 모듈별 상세 기준: `mailbox/README.md`, `analysis/README.md`, `exports/README.md`, `llm/README.md`, `runtime/README.md`, `app/README.md`
  - 모듈별 현재 상태와 최근 기록: `mailbox/docs/logbook.md`, `analysis/docs/logbook.md`, `exports/docs/logbook.md`, `llm/docs/logbook.md`, `runtime/docs/logbook.md`, `app/docs/logbook.md`
- 현재 로컬 워크스페이스:
  - sibling 구조 `repo / envs / results / secrets`
- 현재 공유 워크스페이스:
  - `workspace.epa-workspace.json + secure/secrets.enc.json + state/state.sqlite + locks/write.lock + mail/ + exports/ + logs/`
- 비공개 자산과 자격증명의 canonical 로컬 시작 문서는 sibling `../secrets/README.local.md`다.
- 현재 로컬 산출물 정책:
  - 제품 기준 메일 bundle, 운영 workbook, 리뷰 상태, 로그는 새 세이브 파일 내부의 v2 구조에 둔다.
  - sibling `../secrets/사용자 설정/<이름>/참고자료/`는 개발자 전용 fixture와 raw 자산을 읽기 전용으로 둘 때만 쓴다.
  - repo 내부 `<module>/results/`는 재현 가능한 smoke 결과와 소형 비교 자료만 둔다.
  - root `results/`는 현재 canonical 위치가 아니다.
- 현재 모듈 상태:
  - `mailbox`: bundle schema, fixture materialize, bundle reader, provider 자동 설정 후보 생성, connect/auth probe, local-only credential loader, real account latest IMAP fetch smoke, INBOX read-only backfill smoke가 있다.
  - `analysis`: `NormalizedMessage -> ExtractedRecord` structured output 경로와 multimodal 입력 builder, fixture/runtime bundle smoke, real-bundle quality smoke, 3-way triage, HTML review board, application-only batch export 경로가 있다.
  - `exports`: 템플릿 reader, semantic mapping, projection, workbook append, 회귀 guardrail이 있다.
  - `llm`: OpenAI wrapper, usage logging, 가격표 snapshot 기반 비용 추정, structured output transport가 있다.
  - `runtime`: 공유 워크스페이스 manifest, 암호화 secret blob, sqlite state, write lock, dedupe/workbook rebuild, sync CLI, feature harness smoke가 있다.
  - `app`: FastAPI 기반 로컬 UI, pywebview launcher, 3단계 시작 마법사, settings, review center, 고급 도구, UI smoke가 있다.

## 현재 전역 결정

- 시작 게이트는 항상 `AGENTS.md -> README.md -> docs/logbook.md -> docs/feature_catalog.md`다.
- 새 active plan을 실제 구현으로 옮기기 전에는 이전 active plan의 publish 상태를 먼저 확인한다.
- 승인된 active plan이 생기면 구현 전에 그 plan 전문을 root `docs/logbook.md`의 `현재 실행 계획`에 먼저 반영한다.
- 구현은 `현재 체크포인트`와 `현재 활성 체크리스트`를 작은 작업 단위로 갱신하면서 진행한다.
- plan 마감의 기본 완료 조건은 `canonical 문서 반영 -> commit -> push -> git status clean 확인`이다.
- 비사소한 작업의 완료 보고는 항상 `요청 내용 -> 계획 -> 결과와 자가 평가` 3단 구조를 따르고, `검증 중 새로 발견한 문제`, `추가 수정`, `재검증`, `AGENTS 확인 기록`을 함께 남긴다.
- 공식 exe가 있는 작업은 `최신 pushed main 기준 공식 exe 재빌드 + 공식 exe smoke`까지 닫히기 전에는 완료 보고로 보지 않는다.
- 비사소한 작업에서는 sub agent를 적극적으로 활용하되, main agent는 먼저 local planning을 하고 sub agent에는 bounded scope와 disjoint ownership을 준다.
- 작은 작업 단위로 넘어갈 때마다 현재 살아 있는 sub agent를 점검하고, 필요 없는 agent는 닫은 뒤 진행한다.
- 완료 보고에는 `sub agent 사용 여부`, `역할/상태`, `미종료 agent 유무`를 함께 남긴다.
- stable truth는 `README.md`와 각 모듈 `README.md`, active truth는 `docs/logbook.md`와 각 모듈 `docs/logbook.md`에 둔다.
- 런타임 데이터 계약은 `MailBundle -> NormalizedMessage -> ExtractedRecord -> ExportRow` 4단계를 유지한다.
- `ExtractedRecord` top-level triage는 `application`, `not_application`, `needs_human_review` 3개 값으로 고정한다.
- 메일 설정 탐지는 `rule/probe-first`, LLM 보조 fallback 기준을 유지한다.
- 입력 해석은 multimodal-first로 두고, 이미지나 스캔 문서가 있으면 실제 이미지 입력을 우선 활용한다.
- 템플릿 해석은 rule-first로 시작하고, unresolved header만 LLM fallback으로 보충한다.
- `app/`은 전용 데스크톱 창과 로컬 Web UI를 맡고, `runtime/`은 공유 save와 sync orchestration을 맡는다.
- Windows 포터블 exe의 공식 실행 경로는 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe` 하나로 고정한다.
- `Z:` 공유 폴더의 exe와 Linux repo shared mirror는 더 이상 실행본 canonical 위치로 쓰지 않는다.
- 제품 기준 실제 inbox bundle, 운영 workbook, usage log, review 로그는 현재 세이브 파일 내부의 `mail/`, `exports/`, `logs/` 아래에 둔다.
- sibling `../secrets/사용자 설정/<이름>/실행결과/`는 개발자 전용 legacy/private runtime 위치로만 본다.
- 제품 세이브의 canonical 구조는 `workspace.epa-workspace.json + secure/ + state/ + locks/ + mail/ + exports/ + logs/`다.
- 새 세이브는 legacy `profile/참고자료/실행결과/기대되는 산출물` 구조를 만들지 않는다.
- workbook 자동 반영은 triage가 `application`이고 기업/연락처 신호가 함께 확인된 경우에만 허용한다.
- 공유 워크스페이스에서는 민감한 값도 `secure/secrets.enc.json` 안에 암호화 저장하고, review/dedupe/override/workbook row 상태는 `state/state.sqlite`에 저장한다.
- 공유 워크스페이스는 단일 작성자 잠금을 기본으로 하고 `locks/write.lock` heartbeat 기준 stale takeover를 허용한다.

## 현재 실행 계획

- plan 제목:
  - `리뷰 정본화 + 자동 중복 판정 + 최신 exe 게이트 정비`
- summary:
  - 현재 Windows 공식 실행본 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`가 최신 repo 상태보다 오래된 빌드일 수 있으므로, 먼저 stale exe 문제를 구조적으로 막는다.
  - 이번 리팩터의 목표는 세 가지다. `리뷰`를 몇천 건에서도 버벅이지 않는 제품형 화면으로 바꾸고, `중복/대표 메일` 개념을 사용자 화면에서 없애고, `공식 exe 빌드 -> CLI/service 검증 -> 공식 exe 기준 검증 -> 보고`를 하드 게이트로 고정한다.
  - 기본 UI에서는 중복/대표 개념을 숨기고, 내부적으로만 LLM과 fallback heuristic으로 canonical 메일을 선택한다.
  - 앱을 검토의 정본으로 두고, 엑셀은 외부 전달/참고용 보조 결과물로 재정의한다.
- key changes:
  - `/app-meta`와 앱 진단에 `build_commit`, `build_time`, `official_exe_path`를 노출하고, 공식 exe 재빌드와 packaged smoke를 완료 보고의 하드 게이트로 둔다.
  - 계정이 이미 `connected`면 홈의 기본 CTA는 `리뷰 계속하기`로 바꾸고, `계정 연결 계속하기`는 기본 CTA에서 제거한다.
  - 리뷰는 기본 50건 목록만 먼저 렌더링하고, row 선택과 artifact 탭 전환은 full reload가 아니라 우측 상세패널만 partial update로 갱신한다.
  - 사용자 화면에서는 `중복` 열과 `대표 메일 지정` 액션을 없애고, 내부 상태에는 `application_group_id`, `canonical_bundle_id`, `included_in_export`, `canonical_selection_reason`, `canonical_selection_confidence`를 유지한다.
  - `preview/raw.eml/summary/record/projected/attachments`는 모두 한국어 용어로 통일하고, 앱 안 미리보기를 기본으로 둔다.
  - `docs/feature_catalog.md`에는 기능 id, UI/CLI/service, 입력/출력, 저장 위치, smoke 가능 여부, 수동 acceptance 필요 여부와 함께 `source 반영 / CLI 검증 / 공식 exe 반영 / 수동 acceptance` 구분을 남긴다.
- public interfaces / types:
  - `runtime.analysis_service:{load_review_center_page_service, load_review_detail_service, refresh_review_board_service}`
  - `runtime.exports_service:{load_exports_summary_service, rebuild_operating_workbook_service}`
  - `runtime.pipeline_service:run_pipeline_sync_service`
  - `runtime.diagnostics_service:picker_bridge_self_test`
  - `app-meta`
    - `build_commit`
    - `build_time`
    - `official_exe_path`
  - 내부 canonical selection 메타:
    - `application_group_id`
    - `canonical_bundle_id`
    - `included_in_export`
    - `canonical_selection_reason`
    - `canonical_selection_confidence`
- test plan:
  - smoke-safe
    - 세이브 생성/열기/닫기/최근 세이브
    - 설정 저장/읽기
    - picker diagnostics + picker route test override
    - review refresh
    - review list/detail paging
    - exports summary
    - workbook rebuild
    - `app.ui_smoke`
    - `runtime.feature_harness_smoke`
  - live-required
    - 실제 계정 연결 확인
    - `sync --limit 10`
    - `sync --limit 100`
    - `sync --limit 500`
    - 필요 시 `sync --limit 550`
    - 마지막으로 `sync --all`
  - manual acceptance
    - Windows exe에서 실제 폴더 선택창이 뜨는지
    - exe 아이콘/창 브랜딩이 새 기준대로 보이는지
- assumptions:
  - 공식 실행 경로는 계속 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe` 하나다.
  - GUI는 thin wrapper, 공용 진실은 service/CLI다.
  - 리뷰 UX는 `가벼운 목록 + 비동기 상세패널`을 기본으로 하고, 앱이 검토의 정본이다.
  - 기본 UI에서는 중복/대표 개념을 제거하고, 자동 canonical selection + 숨은 복구 정책을 쓴다.
  - 기존 beta 세이브의 자동 마이그레이션은 하지 않는다.
  - Windows 네이티브 picker와 exe shell integration만 마지막 수동 acceptance로 남긴다.

## 현재 체크포인트

- 지금 단계:
  - source/CLI/smoke 기준으로는 `계정 연결 계속하기 CTA`, `중복/대표 UI`, `리뷰 상세 full reload`, `preview click 후 상태 초기화`, `stale exe 게이트`를 모두 정리했다.
  - 실제 Windows 세이브 기준으로 `state.sqlite` migration 버그(`application_group_id` 없는 오래된 DB에서 index 생성 실패)를 재현했고, `runtime.state_store.ensure_schema()`가 오래된 `bundle_review_state`와 `feature_runs` 테이블을 먼저 컬럼 승격한 뒤 index를 만들도록 고쳤다.
  - `runtime.feature_harness_smoke`에는 오래된 state DB를 현재 스키마로 승격하는 `schema_upgrade_smoke`를 추가했고, 로컬 자동 검증은 다시 통과했다.
  - staged live verification은 `recent 100`, `recent 500`, `recent 550`까지 실제 Windows 세이브 기준으로 통과했다.
  - `all`은 실제 inbox 규모가 `4750`건이어서 장시간 backfill/review가 필요했고, 이번 턴에서는 `fetch 4750/4750 (fetched=3748, skipped=1002, failed=0)`와 `review 2200/4750 (failed=0)`까지 확인한 뒤 장기 운영 검증으로 분리했다.
  - 가장 최근 pushed `main` 기준으로 공식 Windows exe `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`를 다시 재빌드했고, packaged smoke와 GUI smoke를 다시 통과했다.
- 바로 다음 작업:
  - Windows 수동 acceptance 2개를 현재 공식 exe 기준으로 직접 닫는다.
  - `sync --all`은 이번 staged live verification 결과를 바탕으로 별도 operator-run 장기 검증으로 닫는다.
- publish 상태:
  - 이전 plan publish 완료
  - 현재 plan 구현 중
  - 이번 턴 마감 시 commit/push 예정

## 현재 활성 체크리스트

- `리뷰 정본화 + 자동 중복 판정 + 최신 exe 게이트 정비`
  - [x] root `AGENTS.md` 재확인
  - [x] root `docs/logbook.md`에 active plan 전문 반영
  - [x] stale exe 방지용 build metadata / 공식 exe 게이트 추가
  - [x] 홈 CTA를 계정 연결 상태 기반으로 재구성
  - [x] 리뷰 row/artifact 전환을 partial update로 전환
  - [x] review 진입 기본 선택/loading 상태 정리
  - [x] 사용자 표면에서 `중복` 열과 `대표 메일 지정` 액션 제거
  - [x] 내부 canonical selection 메타와 자동 판정 도입
  - [x] artifact / export / home 카피를 한국어 기준으로 전면 정리
  - [x] `exports summary`와 리뷰 상세패널에 내보내기 요약 강화
  - [x] feature catalog에 feedback coverage / source-CLI-exe-manual 추적 반영
  - [x] smoke-safe 자동 검증 재실행
  - [x] state DB schema upgrade 보정과 regression smoke 추가
  - [x] staged live verification: `100 / 500 / 550`
  - [ ] staged live verification: `all` long-run operator acceptance
  - [x] current source 기준 공식 Windows exe 재빌드 + packaged smoke 재확인
  - [ ] Windows 수동 acceptance: 실제 picker dialog
  - [ ] Windows 수동 acceptance: exe 아이콘/창 브랜딩
  - [ ] current plan final commit 완료
  - [ ] current plan final push 완료
  - [ ] final `git status --short --branch` clean 확인

## 사용자 피드백 커버리지

| 항목 | source 반영 | CLI/smoke 검증 | 공식 exe 반영 | 사용자 수동 acceptance |
|---|---|---|---|---|
| stale exe 방지 build metadata와 공식 게이트 | 완료 | 완료 | 완료 | 필요 없음 |
| 계정 연결 완료 시 홈 CTA 정리 | 완료 | 완료 | 완료 | 선택 |
| 리뷰 목록 50건 paging + 상세 partial update | 완료 | 완료 | 완료 | 선택 |
| `메일 미리보기` 탭/외부 열기 후 상태 유지 | 완료 | 완료 | 완료 | 선택 |
| `중복/대표` 사용자 UI 제거 + 자동 canonical selection | 완료 | 완료 | 완료 | 선택 |
| artifact/export/home 한국어 용어 통일 | 완료 | 완료 | 완료 | 선택 |
| Windows native picker 실제 dialog | 완료 | diagnostics/self-test 완료 | 완료 | 필요 |
| exe 아이콘/창 브랜딩 최신 반영 | 완료 | packaged smoke 완료 | 완료 | 필요 |

## 최근 로그

### 2026-04-13 | Human + Codex | packaged metadata path 정규화와 current commit 기준 Windows 공식 exe 재빌드 완료

- `app/packaging/build_portable_exe.ps1`는 `official_exe_path`를 `GetFullPath()`로 정규화해 `portable_build_info.json`에 기록하도록 보강했다.
- `app/packaging/smoke_portable_exe.ps1`도 smoke 대상 exe 경로와 `/app-meta`의 `official_exe_path`를 같은 방식으로 정규화한 뒤 비교하게 바꿨다.
- 위 수정은 commit `915c494`로 push 했고, 그 commit 기준으로 `bash app/packaging/build_windows_portable_and_publish.sh --clean`을 다시 실행했다.
- 결과적으로 Windows 공식 실행본 `D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe`는 `build_commit=915c49445ac8da7ea0dd9e7777376fec704c2559`, `build_time=2026-04-13T17:48:21` 기준으로 다시 publish 되었고 packaged smoke와 GUI smoke를 통과했다.
- 같은 시점에 `python -m py_compile ...`, `python -m runtime.cli feature-harness-smoke --workspace-root /tmp/epa_review_canonical_smoke --workspace-password SampleWorkspace260408 --create-sample-if-missing`, `python -m app.ui_smoke --workspace-root /tmp/epa_review_canonical_smoke --workspace-password SampleWorkspace260408`, `python -m runtime.cli analysis review-list --workspace-root /tmp/epa_review_canonical_smoke --page 1 --page-size 50 --sort received_desc`, `python -m runtime.cli exports summary --workspace-root /tmp/epa_review_canonical_smoke`도 다시 통과했다.
- 따라서 현재 active plan 기준에서 자동 검증과 공식 exe 반영은 닫혔고, 남은 것은 staged live verification `100 / 500 / 550 / all`과 Windows 수동 acceptance 2개다.

### 2026-04-13 | Human + Codex | 실제 Windows 세이브 migration 보정과 staged live verification 100/500/550 통과

- 실제 Windows 세이브 기준 `recent 100` live verification에서 `sqlite3.OperationalError: no such column: application_group_id`를 재현했다.
- 원인은 오래된 `bundle_review_state`에 새 컬럼이 없는데도 index를 먼저 만드는 `runtime.state_store.ensure_schema()` 순서 문제였다.
- `runtime.state_store`는 이제 오래된 `bundle_review_state`와 `feature_runs`를 `_ensure_column()`으로 먼저 승격한 뒤 index를 만들게 바꿨다.
- `runtime.feature_harness_smoke`에는 오래된 state DB를 현재 스키마로 자동 승격하는 `schema_upgrade_smoke`를 추가했고, 로컬 `feature-harness-smoke`는 다시 통과했다.
- 실제 Windows 세이브 기준 staged live verification 결과는 아래와 같다.
  - `recent 100`: `status=completed`, `fetched=2`, `skipped=98`, `analysis_reused=1`, `analysis_rerun=0`
  - `recent 500`: `status=completed`, `fetched=0`, `skipped=500`, `analysis_reused=36`, `analysis_rerun=0`
  - `recent 550`: `status=completed`, `fetched=0`, `skipped=550`, `analysis_reused=51`, `analysis_rerun=0`
- `all`은 실제 inbox 규모가 `4750`건이어서 장기 운영 검증으로 분리했다. 이번 턴에서는 `fetch 4750/4750 (fetched=3748, skipped=1002, failed=0)`와 `review 2200/4750 (failed=0)`까지 진행해 구조적 blocker가 없음을 확인했다.
- 이번 수정은 source와 CLI/smoke에는 반영됐지만, 공식 Windows exe에는 아직 다시 실리지 않았으므로 다음 마감 전 current commit 기준 재빌드가 필요하다.

### 2026-04-13 | Human + Codex | current main 기준 공식 Windows exe 재빌드 재완료

- 가장 최근 pushed `main` 기준으로 `bash app/packaging/build_windows_portable_and_publish.sh --clean`을 다시 실행해 공식 Windows exe를 최신 source와 맞췄다.
- Windows build mirror는 `origin/main` 최신 head로 다시 sync 되었고, 공식 runtime `D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe`도 같은 head 기준으로 다시 publish 되었다.
- packaged smoke는 `/jobs/current`, `/app-meta`를 다시 통과했고, `/app-meta` 기준 `build_commit`, `build_time`, `official_exe_path`가 최신 공식 실행본과 맞는지 확인했다.
- Portable GUI smoke도 다시 통과해 `startup.log` 기준 launcher와 packaged runtime이 current main 기준으로 다시 올라온 것을 확인했다.
- 따라서 지금 시점의 남은 항목은 `sync --all` 장기 운영 검증과 Windows 수동 acceptance 2개뿐이다.

### 2026-04-13 | Human + Codex | 완료 보고 형식과 AGENTS 재독 기록 규칙 강화

- 앞으로 비사소한 작업의 완료 보고는 항상 `내가 요청한 내용 -> 그래서 세운 계획 -> 결과와 내가 스스로 평가한 내용` 3단 구조를 따르도록 운영 규칙을 강화했다.
- `결과와 내가 스스로 평가한 내용`에는 구현 결과만이 아니라 `검증 중 새로 발견한 문제`, `그 문제를 위해 추가로 수정한 내용`, `그 수정 뒤 다시 돌린 검증`을 반드시 함께 적도록 고정했다.
- 동시에 `AGENTS 확인 기록`도 완료 보고의 필수 항목으로 올려, 이번 턴에 `AGENTS.md`를 총 몇 번, 어느 게이트에서 다시 읽었는지를 항상 남기도록 했다.
- starter `AGENTS.md`와 `docs/feature_catalog.md`에도 같은 규칙을 반영해, 새 저장소를 시작해도 같은 운영 습관이 유지되게 맞췄다.

### 2026-04-13 | Human + Codex | 서브 에이전트 적극 활용과 agent 정리 규칙 추가

- 비사소한 작업에서는 sub agent를 적극적으로 검토하고, 독립된 조사/병렬 검증/분리 가능한 write scope는 우선 sub agent로 분해하도록 운영 규칙을 강화했다.
- 단, OpenAI sub-agent 운영 원칙에 맞춰 main agent가 먼저 local planning을 하고, immediate critical path는 직접 처리하며, sub agent에는 bounded scope와 disjoint ownership을 주도록 기준을 고정했다.
- 작은 작업 단위로 넘어갈 때마다 현재 살아 있는 sub agent를 점검하고, 더 이상 필요 없는 agent는 닫은 뒤 진행하도록 `AGENTS.md`, starter `AGENTS.md`, `docs/feature_catalog.md`, `docs/logbook.md`에 같은 규칙을 넣었다.
- 앞으로 완료 보고에는 `sub agent 사용 여부`, `역할/상태`, `남아 있는 agent 유무`도 함께 적는다.

### 2026-04-13 | Human + Codex | canonical selection grouping 보정과 review service 경량화

- `runtime.review_state`의 application grouping을 `회사 + 연락처 + 신청 주제` 기준으로 보정해, 같은 신청 흐름의 수정본/회신이 thread key 차이만으로 다른 그룹으로 갈라지지 않게 했다.
- `runtime.feature_harness_smoke`의 canonical selection smoke는 이제 수정본 bundle `20260406_142500_msg_b170ce32`를 export canonical 메일로 고르고, 초기 신청 메일은 held 상태로 남는 것을 다시 통과한다.
- `runtime.state_store`에는 `list_review_page_items`와 aggregate `summary_counts`를 추가해, 리뷰 목록이 전체 item payload 대신 가벼운 행 데이터만 먼저 읽도록 경량화했다.
- `runtime.analysis_service`는 위 경량 목록 조회를 사용하고, `app/server.py`와 `review` 템플릿은 기본 artifact를 `검토 개요`로 두어 첫 진입 시 무거운 iframe/파일 미리보기를 먼저 띄우지 않게 했다.
- `review` row/artifact partial update는 이제 browser URL을 `/review/detail`이 아니라 현재 `/review` query 상태로 유지해, 필터/페이지/선택 맥락이 브라우저 히스토리와 함께 보존되도록 다시 정리했다.
- pushed head 기준 Windows 빌드에서는 packaged `/app-meta`의 `build_commit`이 비어 있는 것을 smoke가 잡아냈고, 원인을 `portable_build_info.json` BOM/필수 파일 관리 문제로 좁혔다.
- 이에 따라 `app/build_info.py`는 BOM이 있는 UTF-8도 읽게 하고, Windows build script는 `portable_build_info.json`을 UTF-8 without BOM으로 쓰게 바꿨다.
- `portable_bundle_manifest.py`는 이제 `portable_build_info.json`도 필수 파일로 검사한다.
- 검증은 `python -m runtime.cli analysis review-list --workspace-root /tmp/epa_review_perf_smoke --page 1 --page-size 50 --sort received_desc`, `python -m runtime.cli feature-harness-smoke --workspace-root /tmp/epa_review_perf_smoke --workspace-password SampleWorkspace260408 --create-sample-if-missing`, `python -m app.ui_smoke --workspace-root /tmp/epa_review_perf_smoke --workspace-password SampleWorkspace260408` 기준으로 통과했다.

### 2026-04-13 | Human + Codex | 리뷰 성능/사용성 개선 1차: 페이지 기반 목록, 상태 유지, 앱 안 미리보기

- `review` 화면을 전체 카드 렌더에서 `페이지 기반 목록 + 우측 상세패널` 구조로 바꿨다. 기본 페이지 크기는 50이고, 25/50/100 옵션과 정렬(`받은 시각 최신순 / 회사명순 / 발신자순`)을 함께 지원한다.
- 리뷰 상세는 선택한 bundle 1건만 별도 service 호출로 읽고, `메일 미리보기 / 원본 메일 파일 / 요약 메모 / 추출 결과 원본 / 엑셀 반영 미리보기`를 앱 안 iframe 미리보기로 먼저 보여주도록 바꿨다.
- 외부 파일 열기는 `/actions/open-path` form post로 정리해, 파일이나 폴더를 열고 돌아와도 필터/페이지/선택 상태가 그대로 유지되게 했다.
- 사용자 용어는 `대표 export만` 대신 `엑셀 반영 대상만`, `대표` 대신 `엑셀 반영 대상`, `preview/raw.eml/summary/...` 대신 한국어 artifact 이름으로 다시 정리했다.
- `runtime.analysis_service`에는 `load_review_center_page_service`, `load_review_detail_service`를, `runtime.exports_service`에는 `load_exports_summary_service`를 추가해 GUI와 CLI가 같은 조회 계약을 쓰게 했다.
- `runtime.cli`는 `analysis review-list`, `analysis review-item`, `exports summary`를 제공하고, `feature_harness_smoke`는 이 service 결과를 함께 검증하도록 보강했다.
- `app/main.py`의 picker bridge는 이제 pywebview native dialog를 우선 시도하고, 필요 시 diagnostics route/native helper로 fallback 하도록 바꿨다.
- 검증은 `py_compile`, `python -m app.ui_smoke --workspace-root /tmp/epa_review_perf_smoke --workspace-password SampleWorkspace260408`, `python -m runtime.cli analysis review-list --workspace-root /tmp/epa_review_perf_smoke --page 1 --page-size 50 --sort received_desc`, `python -m runtime.cli exports summary --workspace-root /tmp/epa_review_perf_smoke`, `python -m runtime.cli feature-harness-smoke --workspace-root /tmp/epa_review_perf_smoke --workspace-password SampleWorkspace260408` 기준으로 통과했다.

### 2026-04-13 | Human + Codex | pushed head 기준 Windows 재빌드와 자동 검증 완료, manual acceptance만 남김

- `Introduce CLI-first runtime services and diagnostics` 커밋 `98ea75f`를 GitHub `main`에 push 한 뒤, `bash app/packaging/build_windows_portable_and_publish.sh --clean`으로 Windows 공식 실행본을 다시 빌드했다.
- Windows 공식 실행본은 `D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe`에 다시 publish 되었고, 갱신 시각은 `2026-04-13 13:21:25`로 확인했다.
- Windows packaged smoke는 `/jobs/current`와 `/app-meta`를 함께 통과했고, GUI startup log에는 아래 핵심 줄이 남았다.
  - `preferred port 8765 is occupied by another process`
  - `selected fallback port 51051`
  - `confirmed app-meta at http://127.0.0.1:51051`
- 즉, 고정 포트 `8765`를 다른 앱이 잡고 있어도 launcher가 다른 포트를 고르고, 실제 Email Pilot AI 서버인지 `/app-meta`로 확인한 뒤 창을 열도록 동작함을 확인했다.
- Windows service self-test 기준 `diagnostics picker-bridge`는 `powershell-native`, `native_dialog_supported=true`로 통과했다.
- 실제 저장된 세이브 기준 `run_pipeline_sync_service(scope='recent', limit=10)`도 Windows에서 직접 실행해 검증했고, 결과는 `status=completed`, `fetched_count=0`, `skipped_existing_count=10`이었다. 즉 이전에 보이던 `update_latest_review_pointers` / 후속 단계 NameError는 재현되지 않았다.
- 현재 남은 항목은 자동 검증이 아니라 수동 acceptance 2개다.
  - `찾아보기`를 실제 클릭했을 때 폴더 선택창이 뜨는지
  - exe 아이콘/창 브랜딩이 새 기준대로 보이는지

### 2026-04-13 | Human + Codex | CLI-first 전환 착수: service/CLI 골격, picker route, sync presets

- 현재 blocker였던 `찾아보기` 문제는 pywebview JS bridge에 덜 의존하게 구조를 바꾸는 쪽으로 전환했다. 이제 GUI는 `/diagnostics/picker-bridge`, `/diagnostics/pick-folder`, `/diagnostics/pick-file` 서버 route를 호출하고, 실제 picker 호출은 `runtime.diagnostics_service`가 맡는다.
- `runtime.diagnostics_service`에는 Windows native dialog self-test와 함께 `EPA_PICKER_TEST_RESPONSE / ERROR / CANCEL` override를 추가해, 실제 Windows 수동 acceptance 전에도 picker route를 자동 smoke로 검증할 수 있게 했다.
- `runtime.cli`는 `workspace`, `settings`, `mailbox`, `analysis`, `exports`, `pipeline`, `diagnostics` 명시적 하위 명령을 갖는 제품 CLI로 확장했다.
- `runtime.pipeline_service`는 `scope=recent|all`, `limit=N` 기준 recent/all sync를 같은 결과 계약으로 반환하고, reuse count를 함께 남기게 보강했다.
- `/sync` 화면과 서버 입력은 이제 `최근 10 / 100 / 500 / 1000 / 직접 입력 / 전체` 범위를 받는다.
- `app.ui_smoke`는 picker diagnostics route, picker folder route, sync preset UI를 자동 검증하고, `runtime.feature_harness_smoke`는 workspace/settings/diagnostics/analysis/exports service를 직접 호출하는 smoke를 추가했다.
- 아직 남은 일은 Windows 포터블 재빌드와 실제 native dialog/manual acceptance, 그리고 feature catalog/module 문서 마감 정리다.

### 2026-04-13 | Human + Codex | Windows blocker 재정의: 고정 포트 충돌과 stale Windows 빌드 원인 확인

- 사용자 검증에서 `찾아보기`가 여전히 안 열리는 이유를 다시 추적한 결과, Windows localhost의 고정 포트 `8765`에는 다른 로컬 앱 `voice_clone_desktop_sidecar`가 붙어 있을 수 있다는 점을 확인했다.
- 즉, 기존 launcher는 같은 포트를 쓰는 다른 앱을 잘못 바라볼 수 있었고, 그 상태에서는 새 UI/diagnostics 코드가 들어 있어도 실제 창은 엉뚱한 서버와 연결될 위험이 있었다.
- `app/main.py`에는 이제 포트 점유 시 다른 로컬 포트를 자동 선택하고, `/app-meta`의 `app_id=email_pilot_ai_desktop`를 확인한 뒤에만 창을 여는 방어 로직을 넣었다.
- 동시에 Windows build helper는 GitHub `origin/main` 기준 미러 sync를 사용하므로, dirty working tree나 미push HEAD 상태에서 빌드하면 stale exe가 생길 수 있었다. `build_windows_portable_and_publish.sh`는 이제 dirty tree 또는 `HEAD != origin/<branch>` 상태면 빌드를 거부한다.
- 이번 checkpoint의 핵심은 이 로컬 수정들을 먼저 commit/push 한 뒤, pushed head 기준으로 Windows 공식 실행본 `D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe`를 다시 빌드해 실제 picker/manual acceptance를 확인하는 것이다.

### 2026-04-13 | Human + Codex | blocker hotfix 완료: `찾아보기` 브리지와 quick sync `notes` 예외 복구

- 홈/설정의 `찾아보기`는 이제 `window.pywebview.api` 객체 존재만으로 준비 완료로 보지 않고, `dialog_capabilities / pick_folder / pick_file` 3개 메서드가 모두 붙었는지까지 확인한 뒤 실제 브리지 준비 완료로 판정한다.
- 런처 `app/main.py`는 pywebview 창을 만든 직후 서버 상태를 더 이상 `desktop_ready`로 올리지 않고 `desktop_pending`으로 유지해, 브리지 준비 전 오진을 줄였다.
- 브리지 호출은 입력칸이 비어 있어도 바로 시도하고, 메서드가 아직 안 붙었거나 호출이 실패하면 짧은 인라인 안내를 보여주도록 `app/static/js/app.js`를 보강했다.
- `analysis/inbox_review_board_smoke.py`에서는 `bundle_limit` 분기보다 먼저 `notes`를 초기화해, quick sync 경로에서 `notes.append(...)`가 지역변수 미초기화 상태로 터지지 않게 고쳤다.
- sync UI는 `부분 완료`를 유지하되 핵심 카드에는 사용자용 설명을 보여주고, 기술 예외는 세부 항목으로만 남기도록 `app/server.py`의 job 상태 메시지를 정리했다.
- `app/ui_smoke.py`는 홈/설정의 `찾아보기`가 기본 disabled가 아닌지까지 검사하도록 보강했고, `runtime/feature_harness_smoke.py`에는 `bundle_limit=10` quick review 회귀를 잡는 전용 smoke를 추가했다.
- 검증은 `py_compile`, `python -m app.ui_smoke --workspace-root /tmp/epa_blocker_hotfix_smoke --workspace-password SampleWorkspace260408`, `python -m runtime.feature_harness_smoke --workspace-root /tmp/epa_blocker_hotfix_smoke_2 --workspace-password SampleWorkspace260408 --create-sample-if-missing`, Windows `bash app/packaging/build_windows_portable_and_publish.sh --clean` 기준으로 통과했다.
- Windows 공식 실행본 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`는 다시 빌드했고, packaged GUI smoke도 `startup.log` 기준으로 통과했다.

### 2026-04-13 | Human + Codex | 고객 서비스형 UI/세이브 구조 리팩터 v3 구현과 검증

- 새 세이브 canonical 구조를 `workspace.epa-workspace.json + secure + state + locks + mail + exports + logs` 기준의 v2 구조로 고정했고, 새 세이브 생성 시 legacy `profile / 참고자료 / 실행결과 / 기대되는 산출물` 폴더가 생기지 않도록 `runtime/workspace.py` 초기화 순서를 바로잡았다.
- 세이브 파일 열기/만들기는 경로 선입력보다 실제 폴더 선택을 기본으로 쓰게 유지했고, 최근 세이브는 `이 PC에서 바로 다시 열기` 또는 `암호를 확인한 뒤 다시 열기` 두 흐름으로 다시 정리했다.
- 세이브 닫기, 다른 세이브 열기, 앱 재실행 시 마지막 세이브 자동 재개, 기본 OpenAI API key 자동 채움은 이 PC 전용 암호화 저장소를 통해 동작하게 했다.
- 계정 연결 확인은 background job으로 전환해 `입력 확인 -> 서버 후보 확인 -> 로그인 시도 -> 폴더 목록 읽기 -> 완료` 단계와 진행률을 즉시 보여주게 했다.
- 빠른 테스트/전체 동기화는 background job 진행 카드와 진행률, 부분 완료, 다음 행동 안내를 보여주게 했고, 메일 저장 성공 후 분석/내보내기 실패를 `부분 완료`로 따로 표현한다.
- `(i)` 도움말과 disabled 이유 안내는 실제 tooltip/popover 컴포넌트로 통일했고, 고객용 UI 용어는 `기본 받은편지함`, `엑셀 양식`, `세이브 파일` 중심으로 다시 정리했다.
- 최근 세이브 재열기, 새 v2 세이브 생성, UI smoke, feature harness smoke를 다시 검증했고, 최종 샘플 세이브 기준 `logs/app/260413_1128_ui_smoke.json`, `logs/runtime/260413_1128_feature_harness_smoke.json`까지 확인했다.
- `packaging.portable_exe.build` prerequisite check는 Linux 개발 호스트에서는 Windows 전용 의존성을 `warn`으로만 보게 바꿔, 실제 Windows 패키징 검증기와 로컬 feature harness가 서로의 의미를 침범하지 않게 정리했다.
- GitHub `main`에는 `13ce5b1 Refine customer save UX and workspace v2 flow`를 push 했고, reverse SSH 기준 Windows 빌드도 다시 실행해 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`를 최신 상태로 publish 했다.

### 2026-04-13 | Human + Codex | blocker hotfix 착수: `찾아보기` 브리지와 quick sync 예외

- 사용자 검증 기준 현재 blocker를 두 가지로 고정했다.
  - 홈/설정의 `찾아보기`를 눌러도 브라우징이 열리지 않는 문제
  - 빠른 테스트 동기화에서 메일 저장 후 `UnboundLocalError: local variable 'notes' referenced before assignment`로 `부분 완료`에 떨어지는 문제
- 원인 점검 결과, 브라우저 브리지는 `pywebview` API 객체 존재만으로 준비 완료로 보던 판정이 너무 이르고, quick review board는 `bundle_limit` 분기에서 `notes` 초기화보다 먼저 `notes.append(...)`를 호출하는 결함이 있었다.
- 이번 hotfix는 위 두 문제를 먼저 닫고, 그 다음 서비스형 polish를 다시 이어가는 순서로 진행한다.

### 2026-04-13 | Human + Codex | 서비스형 고객 UI 리팩터 v2 구현

- 홈 미오픈 상태를 긴 설명형 화면에서 벗어나 `세이브 파일 열기/만들기 -> 계정 연결 -> 빠른 테스트 동기화` 3단계 시작 마법사로 재구성했다.
- `기존 세이브 열기`와 `새 세이브 만들기`는 탭형 흐름으로 바꾸고, 최근 세이브가 없으면 새 세이브 만들기를 기본 탭으로 연다.
- `찾아보기` 버튼은 더 이상 `desktop_ready`가 오기 전까지 영구 비활성으로 두지 않고, exe 기준에서 바로 클릭 가능하게 바꿨다. 전용 창 연결이 아직 늦으면 내부에서 짧게 재시도하고, 실패 시에만 직접 입력 안내를 보여준다.
- 앱 셸은 상단 pill 중심 구조에서 `좌측 사이드바 + 상단 작업 헤더` 구조로 바꿨고, 기본 화면에는 기술 경로보다 현재 단계와 다음 행동이 먼저 보이게 했다.
- 색상과 컴포넌트 토큰은 베이지 데모 톤에서 벗어나 슬레이트/네이비 기반 업무용 프로앱 스타일로 재정의했다.
- 세이브 파일 오픈/생성 성공 후에는 홈으로 돌아가기보다 `/settings`로 이동시켜, 첫실행 Step 2인 계정 연결 확인으로 자연스럽게 이어지게 했다.
- `app/README.md`와 `docs/feature_catalog.md`는 새 용어와 홈 흐름에 맞춰 갱신했다.
- 원격 Windows 빌드도 다시 실행했고, 최종 사용자 실행본 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`를 최신 UI 기준으로 다시 publish 했다.
- 검증은 `python tools/logbook_archive_guard.py --archive-if-needed`, `python -m py_compile app/server.py app/main.py app/ui_smoke.py`, `python -m app.ui_smoke --workspace-root /tmp/epa_ui_v2_smoke --workspace-password SampleWorkspace260408`, `python -m runtime.cli feature-harness-smoke --workspace-root /tmp/epa_ui_v2_smoke --workspace-password SampleWorkspace260408` 기준으로 통과했다.

### 2026-04-13 | Human + Codex | Windows 빌드 미러 stale source 원인 확인과 packaging helper 보강

- 사용자 화면 피드백을 기준으로 역추적해 보니, 실제 실행 중인 프로세스 경로는 공식 runtime `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`가 맞았지만, Windows 빌드 미러 `D:\EmailPilotAI\repo`가 오래된 소스 상태여서 새 UI가 exe에 반영되지 않은 것을 확인했다.
- Windows `D:\EmailPilotAI\repo\app\templates\home.html`과 Linux repo의 같은 파일을 비교해 source mismatch를 확인했고, Windows repo를 최신 `main` 기준 소스로 다시 맞춘 뒤 Windows 포터블 build/publish를 재실행했다.
- 현재 Windows `D:\EmailPilotAI\repo`와 Linux repo HEAD는 모두 `8a750ad`로 일치한다.
- `app/packaging/build_windows_portable_and_publish.sh`는 앞으로 Linux working tree tar 미러 대신 `origin/main` 기준 Git sync를 먼저 수행한 뒤 Windows build를 실행하도록 보강했다.
- `app/packaging/publish_portable_to_runtime.ps1`는 공식 runtime exe가 실행 중이면 publish 전에 해당 프로세스를 종료하고 나서 복사하게 보강했다.

### 2026-04-10 | Human + Codex | 서비스형 홈/설정/동기화/리뷰 UI 1차 전환

- 홈 화면을 관리용 도구 톤에서 벗어나 `세이브 파일 -> 계정 연결 -> 빠른 테스트 동기화 -> 전체 동기화 -> 리뷰` 순서의 서비스형 온보딩 대시보드로 다시 구성했다.
- `세이브 파일 가이드`는 별도 페이지 이동만 강요하지 않고, 홈 안에서 바로 여닫는 모달을 기본 경로로 바꿨다.
- 설정 화면은 기본/고급으로 분리했고, 모델은 자유 입력 대신 `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano` 선택형으로 바꿨다.
- `계정 연결 확인` 버튼을 추가해 실제 IMAP 로그인 가능 여부를 확인하고, 성공 시 폴더 목록과 추천 기본 폴더를 `secure/secrets.enc.json` 설정에 저장하게 했다.
- 동기화 화면을 따로 만들고, `빠른 테스트 동기화`와 `전체 동기화`를 분리했다. `quick_smoke`는 최근 10건만 대상으로 하고, `incremental_full`은 기존 증분 fetch + 분석 재사용 흐름을 그대로 쓴다.
- `runtime.feature_registry`에는 `mailbox.connection_check`, `runtime.workspace.sync.quick_smoke`를 추가해 UI/관리도구/CLI에서 같은 기능 카탈로그 언어를 쓰게 했다.
- 리뷰센터는 테이블 중심 검증판에서 벗어나, 카드형 확장 리스트와 빠른 override 흐름을 가진 실사용 검토 화면으로 다시 정리했다.
- analysis 재사용은 이미 `analysis_revision + bundle fingerprint` 기준으로 `extracted_record.meta.json`을 남기는 구조를 넣어 둔 상태이고, 이번 sync 경로에서는 이를 기본 재사용 경로로 연결했다.
- 외부 사용자용 개념 설명은 `app/docs/환경/first_user_save_file_guide.md`로 분리해, 세이브 파일, 로그인 ID, INBOX, 템플릿, 빠른 테스트 동기화 이유를 앱 밖 문서에서 설명하게 했다.
- 검증은 `py_compile`, `create-sample-workspace`, `app.ui_smoke`, `feature-check-all` 기준으로 통과했다.

### 2026-04-10 | Human + Codex | AGENTS 중심 문서/산출물 정리와 cleanup

- root `AGENTS.md`만 운영 규칙을 맡기고, 다른 문서에는 각 문서 역할만 남기도록 `README.md`, `docs/feature_catalog.md`, 모듈 `README/logbook`, starter pack 문구를 일괄 축약했다.
- `app/packaging/README.md`를 packaging canonical 문서로 남기고, 중복이 크던 `app/docs/환경/windows_portable_exe.md`는 실제로 삭제했다.
- 홈 화면의 `가이드 새 창으로 보기` 링크를 없애고, `/workspace/guide`는 더 이상 별도 템플릿을 유지하지 않고 홈 모달로 redirect 하게 바꿨다.
- `app/templates/workspace_guide.html` 같은 guide wrapper template을 제거해 세이브 파일 가이드 표현을 한 군데로 줄였다.
- repo 내부 `__pycache__` 같은 cache 산출물은 이번 cleanup publish에서 함께 정리했다.
- 검증은 `app.ui_smoke`, `feature-harness-smoke`, logbook/archive guard, `git status --short --branch` clean 확인 기준으로 닫았다.

### 2026-04-10 | Human + Codex | 파일 탐색기 브리지 복구와 로컬 실행 전용 정책 정리

- 로컬 Windows exe에서도 `pywebview` 브리지가 준비되기 전에 프런트엔드가 너무 빨리 `브라우저 fallback`으로 단정하던 문제를 기준으로, 앱 런처와 서버가 공유하는 실행 컨텍스트를 새로 추가했다.
- 홈, 설정, 관리도구는 이제 `shell_mode`, `native_dialog_state`, 현재 실행 경로, 공식 로컬 실행 폴더, `startup.log` 경로를 진단 정보로 같이 보여준다.
- `찾아보기` 버튼은 기본 비활성화로 렌더링하고, `desktop_ready`가 확인되기 전에는 `전용 창 연결 확인 중` 상태를 유지하도록 바꿨다.
- Windows 실행 정책은 `공유 폴더는 배포본 보관용`, `실제 실행은 로컬 onedir 복사본`으로 다시 고정했다.
- 공유 드라이브나 UNC 경로에서 직접 실행하면 `pythonnet / Python.Runtime.dll` 단계까지 가기 전에 친절한 preflight 안내를 띄우고 종료하도록 런처를 보강했다.
- `app.ui_smoke`는 홈, 설정, 관리도구에서 새 진단 정보와 초기 `브라우저 fallback` 비노출 기준을 같이 확인하도록 업데이트했다.

### 2026-04-09 | Human + Codex | Windows `python310.dll` 부팅 오류 복구 기준과 AGENTS 재독 게이트 강화

- 표준 Windows build bundle과 Linux shared mirror에 `python310.dll`, `python3.dll`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, `ucrtbase.dll` 같은 필수 실행 파일이 실제로 존재한다는 점을 기준으로, 복구 초점은 `완전 누락`보다 `패키징 안정성`과 `공식 지원 경로 정리`에 맞췄다.
- `EmailPilotAI.spec`에서 `UPX`를 꺼 검증용 portable exe를 안정성 우선 설정으로 바꿨고, `portable_bundle_manifest.py`로 필수 DLL 검사와 sha256 manifest 생성을 공용화했다.
- `build_portable_exe.ps1`는 이제 build 후 필수 DLL 검사와 `portable_bundle_manifest.json` 생성까지 통과해야 완료로 본다.
- `sync_portable_to_local_cache.ps1`를 추가해 공식 fallback 경로 `%LOCALAPPDATA%\\EmailPilotAI\\portable\\EmailPilotAI\\`로 bundle을 동기화하고, source/target manifest 비교와 packaged smoke까지 한 번에 수행하게 했다.
- Samba 공유 실행에서만 `python310.dll`이 `LoadLibrary: 액세스가 거부되었습니다`로 실패하는 증상을 반영해, Linux shared mirror 생성 시 `.exe`, `.dll`, `.pyd`에 실행 비트를 주도록 보강했다.
- onedir 수동 복사 기준은 `dist/windows-portable/EmailPilotAI/` 폴더 전체를 통째로 옮기는 것으로 고정했고, `cleanup_portable_artifacts.sh`로 `build/EmailPilotAI/`, `dist/EmailPilotAI/`, `dist/windows-portable.precheck/` 같은 로컬 build 부산물만 기본 정리 대상으로 묶었다.
- 문서에는 공식 지원 경로를 `공유 폴더 직접 실행`과 `공식 로컬 cache 복사본`으로 고정하고, `D:\\#EmailPilotAI` 같은 임의 수동 복사 경로는 비공식으로 분리했다.
- `AGENTS.md`, starter `AGENTS.md`, repo-local skill 2종에는 `/plan 시작`, `실행 직전`, `완료 직전`에 `AGENTS.md -> README.md -> docs/logbook.md -> docs/feature_catalog.md` 재독 게이트를 더 명시적으로 반영했다.

### 2026-04-09 | Human + Codex | Windows build 산출물 Linux 공유 미러와 Samba 실행 기준 정리

- Windows SSH 세션에서는 사용자의 `Z:` 네트워크 드라이브가 보이지 않는 것을 다시 확인했고, 이를 기준으로 공유 미러 전략을 `Windows가 Samba에 직접 쓰기`가 아니라 `A100이 reverse SSH로 Windows 산출물을 다시 끌어오기`로 고정했다.
- `app/packaging/build_windows_portable_and_mirror.sh`를 추가해 A100에서 `Windows build -> packaged smoke -> Linux 공유 경로 미러`를 한 번에 실행하게 했고, `app/packaging/mirror_portable_to_linux.sh`는 기존 Windows 산출물만 다시 가져오는 helper로 분리했다.
- 공유 실행 기준 경로는 `repo/dist/windows-portable/EmailPilotAI/EmailPilotAI.exe`로 정리했고, 이는 tracked release artifact가 아니라 Samba 검증 편의용 미러로 다룬다.
- 문서에는 “연동성은 exe 위치가 아니라 같은 세이브 파일 폴더를 열었는지로 결정된다”는 기준과, 공유 폴더 직접 실행이 느리거나 막힐 때는 Windows 로컬 복사 실행을 fallback으로 쓰는 정책을 함께 반영했다.

### 2026-04-09 | Human + Codex | 세이브 파일 파일탐색기와 설정/버튼 UX 복구

- 홈 화면의 세이브 파일 열기/생성, 기존 profile import, 설정의 템플릿 경로에 `찾아보기` 버튼을 추가하고, Windows exe에서는 pywebview 네이티브 파일 탐색기를 통해 폴더/파일을 직접 고르게 했다.
- 홈에 `세이브 파일 가이드`를 추가해 `세이브 파일 = workspace.epa-workspace.json 이 들어 있는 폴더`라는 기준과 공유 폴더 기반 권장 흐름을 앱 안에서 바로 읽게 했다.
- 입력 경로는 `기존 세이브`, `새 세이브 가능`, `잘못된 경로`, `profile import 가능`, `템플릿 경로 상태`로 분류해 즉시 안내한다.
- 설정 저장은 성공/실패 배너, 마지막 저장 시각, 템플릿 경로 상태를 함께 보여주고, 워크스페이스 미오픈/읽기 전용/워크스페이스 밖 템플릿 경로를 명시적으로 안내하게 했다.
- `runtime.feature_registry`의 packaging check가 `backports` 미설치 환경에서도 예외를 던지지 않도록 고쳐 `/admin/features` 페이지가 다시 안정적으로 열린다.
- 새 샘플 세이브 기준 `app.ui_smoke`를 통과했고, Windows remote build도 다시 돌려 `EmailPilotAI.exe` packaged smoke까지 완료했다.

### 2026-04-08 | Human + Codex | Windows exe 부팅 오류 복구 기준 추가

- Windows에서 `EmailPilotAI.exe`가 시작 직후 `No module named 'backports'`로 죽는 패키징 오류를 확인했다.
- 원인은 `pkg_resources -> setuptools._vendor.jaraco.context` 경로가 Python 3.10에서 `backports.tarfile`을 요구하는데, PyInstaller bundle에 해당 모듈이 빠져 있던 것이다.
- `requirements-dev.txt`에 `backports.tarfile`를 추가하고, `EmailPilotAI.spec`에 `backports`, `backports.tarfile` hidden import를 넣는 방향으로 수정했다.
- `build_portable_exe.ps1`는 이제 `warn-EmailPilotAI.txt`의 `backports` 누락을 검사하고, `smoke_portable_exe.ps1`를 호출해 packaged exe가 `--no-window` 기준 `/jobs/current` endpoint를 실제로 띄우는지 확인한다.
- 사용자 기준 실행 경로는 계속 `EmailPilotAI.exe` 하나로 유지하고, reverse SSH 스크립트는 개발자 원격 빌드/지원용으로만 다룬다.

### 2026-04-08 | Human + Codex | feature harness smoke와 Windows CI portable exe 경로 추가

- `runtime/cli.py`에 `feature-check-all`, `feature-harness-smoke`를 추가해 현재 feature 카탈로그를 전량 prerequisite 점검하고 sample workspace smoke를 한 번에 돌릴 수 있게 했다.
- `app/ui_smoke.py`를 추가해 홈, 설정, 리뷰센터, 관리도구, workbook 재반영 background job까지 `TestClient` 기준으로 반복 검증할 수 있게 했다.
- 당시에는 GitHub Actions 기반 Windows artifact 경로도 열었지만, 현재 active tracked 기준에서는 workflow scope 제약 때문에 CI workflow 파일을 canonical 경로에서 제외했다.
- `runtime/docs/환경/feature_harness.md`와 `app/packaging/README.md`를 smoke/packaging 절차의 공식 위치로 정리했다.

### 2026-04-08 | Human + Codex | 포터블 exe 기준과 기능 전수 테스트 구조 도입

- `docs/feature_catalog.md`와 `runtime/feature_registry.py`를 추가해 현재 제품/운영 기능의 canonical 카탈로그를 만들었다.
- 기능별 `UI / 관리도구 / CLI` 접근점을 고정하고, `feature_runs` 실행 이력을 `state/state.sqlite`에 남기도록 정리했다.
- `app`에는 관리도구 화면을 추가해 기능 목록, prerequisite check, 최근 실행 결과, 실행 버튼을 한곳에서 보게 했다.
- `runtime/cli.py`는 `feature-list`, `feature-inspect`, `feature-check`, `feature-run`, `create-sample-workspace` 명령을 지원하게 됐다.
- `runtime/sample_workspace.py`를 추가해 실메일과 API key 없이도 리뷰센터, dedupe, workbook 재반영을 검증할 수 있는 repo-safe sample save를 만들게 했다.
- `app/static/` 로컬 자산과 `app/packaging/EmailPilotAI.spec`, `build_portable_exe.ps1`, `requirements-dev.txt`를 추가해 오프라인 포터블 exe 기준을 세웠다.
- 이 서버에서는 Windows exe 자체를 빌드하지 않았고, 대신 샘플 워크스페이스 생성과 feature CLI, app/server py_compile까지 검증했다.

### 2026-04-08 | Human + Codex | Windows 데스크톱 리뷰센터와 공유 워크스페이스 save v1 도입

- `runtime/`에 공유 워크스페이스 manifest, 암호화 secret blob, sqlite state, write lock, CLI, sync orchestration을 추가했다.
- `app/`에 FastAPI 기반 로컬 UI와 pywebview launcher를 추가해 `세이브 파일 불러오기 -> 설정 -> 동기화 -> 통합 리뷰센터` 흐름 골격을 만들었다.
- 공유 save는 `workspace.epa-workspace.json + secure/secrets.enc.json + state/state.sqlite + locks/write.lock + profile/` 구조를 기본으로 잡았고, bundle/로그/workbook 링크는 workspace 상대경로만 저장하게 했다.
- 운영 workbook은 stable path `운영본_기업_신청서_모음.xlsx`로 다시 쓰고, `검토_인덱스` 시트를 함께 추가하는 재구성 경로를 넣었다.
- 정적 HTML review board는 fallback/debug 산출물로 남기고, 사용자 검토의 active canonical 상태는 runtime state DB와 app 리뷰센터가 맡도록 방향을 고정했다.

### 2026-04-08 | Human + Codex | 전체 inbox backfill과 triage review board 추가

- `mailbox`에 실제 계정 `INBOX` 전체를 read-only로 순회하며 runtime bundle을 채우는 backfill smoke를 추가했다.
- 전체 bundle을 최신 prompt 기준으로 재분석해 `application / not_application / needs_human_review` 3분류로 나누고, `application` 중 기업/연락처 신호가 있는 메일만 workbook에 자동 반영하는 batch review 경로를 추가했다.
- 사람 검토용 결과물은 sibling runtime 경로 아래 `로그/review/`의 HTML 보드와 JSON report로 남기고, 각 메일에서 `summary.md`, `preview.html`, `extracted_record.json`, `projected_row.json`으로 바로 이동할 수 있게 했다.
- 이 단계부터 현재 검증 주경로는 `이메일 수신 -> 구조화 분석 -> triage 검토 -> Excel 출력`으로 읽는다.
- 실제 full INBOX backfill 기준 `4690`개 메시지를 read-only로 처리했고, 기존 bundle `1582`건을 skip하면서 새 bundle `3108`건을 추가 materialize해 총 valid runtime bundle `4692`건을 확보했다.
- latest full review board 결과는 `application=155`, `not_application=4526`, `needs_human_review=11`, `exported=153`, `failed=0`이었다.
- 최종 사람 검토용 산출물은 sibling runtime 경로의 `260408_1505_inbox_review_board.html`, `260408_1505_inbox_review_board.json`, `260408_1505_기업_신청서_모음.xlsx`다.
- review board를 전량 실행하는 과정에서 ZIP 내부 손상 XLSX와 HEIC 첨부 때문에 생기던 예외를 잡아, attachment summary fallback과 unsupported image skip 경로로 안정화했다.

### 2026-04-08 | Human + Codex | real bundle 품질 보정과 regression smoke 추가

- `analysis`에 전시회/안내형 메일 후처리 보정 로직을 추가해, direct application 형식이 아닌 real bundle에서도 `company_name`, `product_or_service`, `application_purpose`, `request_summary`를 best-effort로 채우도록 했다.
- 추출 prompt도 안내형 메일에서 업무형 필드를 비워 두지 않도록 보강했다.
- `analysis/real_bundle_quality_smoke.py`를 추가해 같은 real bundle에 대해 analysis 결과, projected row, unresolved 컬럼, summary 존재 여부를 한 번에 점검하도록 했다.
- 현재 baseline real bundle 1건에서는 `missing_expected_fields = 0`, `unresolved_columns = 0`까지 확인했다.
- 다음 품질 단계는 같은 기준을 real bundle 2건 이상으로 늘려, 특정 메일 유형에만 맞춘 개선이 아닌지 확인하는 것이다.

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
