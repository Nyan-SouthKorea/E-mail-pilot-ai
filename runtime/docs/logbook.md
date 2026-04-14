# Runtime Logbook

> 이 문서는 `runtime` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 작업 시작 게이트와 읽기 순서는 root `AGENTS.md`를 따른다.

## 현재 스냅샷

- 공유 워크스페이스 manifest, 암호화 secret blob, sqlite state, write lock이 있다.
- 기존 엔진을 `mail / exports / logs` 기준의 v2 세이브 구조로 다시 돌리는 sync service가 있다.
- review report를 state DB로 ingest하고, 내부 canonical selection 기준으로 엑셀 반영 대상을 자동 고른다.
- stable 운영 workbook을 다시 만들고 `검토_인덱스` 시트를 함께 쓴다.
- CLI로 workspace/settings/mailbox/analysis/exports/pipeline/diagnostics 명령을 실행할 수 있다.
- analysis service는 리뷰 목록 1페이지와 선택 상세 1건을 따로 읽는 조회 계약을 지원한다.
- exports service는 운영본/스냅샷/반영 대상 수를 따로 읽는 요약 계약을 지원한다.
- feature registry와 feature run history가 있다.
- repo-safe 샘플 워크스페이스 seed를 만들 수 있다.
- `feature-check-all`과 `feature-harness-smoke`로 카탈로그 전량 점검과 반복 smoke를 수행할 수 있다.
- sync는 `최근 10 / 100 / 500 / 1000 / 직접 입력 / 전체` 범위를 같은 pipeline service 계약으로 처리하고, analysis revision/fingerprint가 같으면 기존 분석 결과를 재사용한다.
- 새 세이브는 legacy `profile/참고자료/실행결과` 구조를 만들지 않고, v1 세이브는 unsupported로 안내한다.

## 현재 활성 체크리스트

- [x] 공유 워크스페이스 manifest와 표준 폴더 구조 도입
- [x] 암호화 secret 저장 경로 도입
- [x] sqlite state DB와 write lock 도입
- [x] 이전 beta 세이브 차단과 새 v2 세이브 구조 정리
- [x] review report -> state DB ingest 경로 도입
- [x] 자동 canonical selection 기준 stable 운영 workbook 재구성 경로 도입
- [x] feature 카탈로그와 feature run history 도입
- [x] repo-safe sample workspace seed 도입
- [x] feature-check-all, feature-harness-smoke, app UI smoke 연동
- [x] quick/full sync 모드와 analysis 재사용 기준 도입
- [x] workspace/settings/mailbox/analysis/exports/pipeline/diagnostics service 골격 도입
- [x] 명시적 CLI 하위 명령 도입
- [x] diagnostics picker self-test/test override 도입
- [x] feature harness에 service smoke 추가
- [x] review list/detail paging service와 exports summary service 추가
- [x] canonical selection smoke가 수정본 canonical 선택을 안정적으로 검증하도록 grouping 기준 보정
- [x] review list 조회를 경량 row 전용 쿼리로 최적화
- [x] Windows saved workspace 기준 `pipeline sync --scope recent --limit 10` 자동 검증
- [x] 오래된 state DB schema upgrade 보정과 regression smoke 추가
- [x] staged live verification `recent 100 / 500 / 550` 결과를 누적 기록
- [x] Windows stale lock pid probe가 홈 화면 500을 내지 않도록 보강
- [ ] staged live verification `all` 장기 운영 검증 결과 누적
- [ ] override 저장 후 UI에서 더 정교한 diff/재계산 표시 보강
- [ ] 증분 sync 성능과 장시간 heartbeat 운영성 보강
- [ ] live-required staged verification `all` 최종 완료 결과 축적

## 최근 로그

### 2026-04-14 | Human + Codex | Windows stale lock pid probe 500 hotfix

- 사용자가 올린 흰 화면을 실제 Windows 공식 exe 기준으로 재현했고, launcher가 아니라 홈 화면 첫 route에서 500이 나는 것을 확인했다.
- Windows 쪽 traceback으로 원인을 고정했다. `_try_restore_last_workspace_session()`가 `acquire_workspace_write_lock()`를 부르고, 그 안의 `_is_local_dead_process()`가 Windows `os.kill(pid, 0)` 계열 pid probe에서 `SystemError`를 던져 홈 전체를 깨뜨리고 있었다.
- `runtime.lockfile`은 이제 Windows에서는 `tasklist` 기반으로 local pid 존재를 보수적으로 확인하고, 예외가 나도 stale 여부는 heartbeat fallback만 보게 바꿨다.
- `feature_harness_smoke`에는 `lockfile_windows_safety_smoke`를 추가해, stale lock local pid 확인 중 예외가 나도 `False`로 안전 종료하는 회귀를 고정했다.
- 이 수정은 commit `d615cbb`로 push 되었고, 같은 commit 기준 공식 Windows exe 재빌드 뒤 packaged smoke와 Windows route 재검증까지 다시 닫았다.

### 2026-04-13 | Human + Codex | canonical selection grouping 보정과 review list 경량화

- `runtime.review_state`의 application grouping 기준을 `회사 + 연락처 + 신청 주제` 우선으로 보정해, 같은 신청 흐름의 수정본/회신이 서로 다른 thread key 때문에 별도 그룹으로 갈라지지 않게 했다.
- `runtime.feature_harness_smoke`의 canonical selection smoke는 이제 수정본 신청 메일을 canonical bundle로 고르고, 초기 신청 메일은 held 상태로 남기는 경로를 다시 통과한다.
- `runtime.state_store.summary_counts()`는 단일 aggregate query로 바꾸고, `list_review_page_items()`를 추가해 review 목록은 전체 payload가 아니라 가벼운 행 데이터만 먼저 읽도록 최적화했다.
- `runtime.analysis_service.load_review_center_page_service()`는 위 경량 목록 조회를 사용하게 바뀌어, review 기본 진입 시 선택되지 않은 상세 payload까지 함께 읽지 않게 됐다.

### 2026-04-13 | Human + Codex | 리뷰 목록/상세/엑셀 요약 조회 계약 추가

- `runtime.analysis_service`에 `load_review_center_page_service`, `load_review_detail_service`를 추가해 GUI와 CLI가 같은 페이지 기반 리뷰 조회 계약을 쓰게 했다.
- `runtime.exports_service`에는 `load_exports_summary_service`를 추가해 운영본/스냅샷/반영 대상 수를 별도 조회할 수 있게 했다.
- `runtime.cli`는 `analysis review-list`, `analysis review-item`, `exports summary` 명령을 지원하게 됐다.
- `feature_harness_smoke`는 위 service 결과를 함께 확인하도록 보강했고, 샘플 세이브 기준 자동 검증도 다시 통과했다.

### 2026-04-13 | Human + Codex | canonical selection 메타와 review/export 기준 정리

- review state에는 `application_group_id`, `canonical_bundle_id`, `included_in_export`, `canonical_selection_reason`, `canonical_selection_confidence`를 저장하게 했다.
- 기본 UI에서는 `중복`과 `대표 메일 지정`을 숨기고, 엑셀 반영 대상 여부만 노출한다.
- feature harness smoke에는 같은 회사 신청 메일 2건에서 수정본이 canonical로 선택되는지 확인하는 smoke를 추가했다.

### 2026-04-13 | Human + Codex | Windows saved workspace 기준 service 자동 검증

- Windows 로컬 장치 비밀 저장소에서 마지막 세이브 경로와 암호를 읽고, 같은 값으로 `run_pipeline_sync_service(scope='recent', limit=10)`를 직접 실행했다.
- 결과는 `status=completed`, `fetched_count=0`, `skipped_existing_count=10`, `analysis_reused_count=0`, `analysis_rerun_count=0`이었다.
- 즉 실제 세이브 기준으로도 pipeline service가 끝까지 실행됐고, 이전에 보이던 `update_latest_review_pointers` / 후속 단계 NameError는 재현되지 않았다.
- 아직 누적해야 할 것은 staged live verification `100 / 500 / 550 / all` 결과다.

### 2026-04-13 | Human + Codex | 실제 Windows 세이브 migration 보정과 staged live verification 100/500/550 통과

- 실제 Windows 세이브 기준 `recent 100` sync에서 `application_group_id` 없는 오래된 `bundle_review_state`에 index를 먼저 만들다 실패하는 migration bug를 재현했다.
- `runtime.state_store.ensure_schema()`는 이제 `bundle_review_state`와 `feature_runs`의 누락 컬럼을 먼저 `_ensure_column()`으로 승격한 뒤 index를 만들게 바뀌었다.
- `runtime.feature_harness_smoke`에는 오래된 state DB를 현재 스키마로 올리는 `schema_upgrade_smoke`를 추가했고, 로컬 하네스는 다시 통과했다.
- staged live verification은 실제 Windows 세이브 기준 아래 범위까지 통과했다.
  - `recent 100`: `fetched=2`, `skipped=98`, `analysis_reused=1`, `analysis_rerun=0`
  - `recent 500`: `fetched=0`, `skipped=500`, `analysis_reused=36`, `analysis_rerun=0`
  - `recent 550`: `fetched=0`, `skipped=550`, `analysis_reused=51`, `analysis_rerun=0`
- `all`은 실제 inbox 규모 `4750`건 기준 장기 운영 검증으로 돌렸고, 이번 턴에서는 `fetch 4750/4750 (fetched=3748, skipped=1002, failed=0)`와 `review 2200/4750 (failed=0)`까지 확인했다.
- 이 단계는 source/service 기준 구조적 blocker가 없음을 확인하는 데는 충분했지만, 전체 완료까지는 시간이 길어 current turn 마감용 long-run acceptance로 분리해 둔다.

### 2026-04-13 | Human + Codex | service/CLI 단일 진실 강화와 picker diagnostics 계약 정리

- `runtime`에는 `workspace / settings / mailbox / analysis / exports / pipeline / diagnostics` 7개 service 그룹이 실제 공용 진실 계층으로 올라왔다.
- `runtime.cli`는 위 service를 직접 호출하는 명시적 하위 명령을 제공하고, `workspace create/open/close/status/recent`, `settings show/save`, `mailbox connect-check/fetch`, `analysis review-refresh`, `exports rebuild`, `pipeline sync`, `diagnostics picker-bridge/pick-folder/pick-file` 계약을 갖는다.
- picker는 이제 GUI 전용 JS 추정이 아니라 `runtime.diagnostics_service`를 통해 self-test와 실제 호출 결과를 같은 payload 형태로 받는다.
- `runtime.feature_harness_smoke`는 workspace/settings/diagnostics/analysis/exports service를 직접 호출하고, `app.ui_smoke`와 함께 같은 save에서 반복 검증한다.
- 남은 일은 live-required staged verification `10/100/500/550/all` 범위를 실제 계정 기준으로 순서대로 누적 기록하는 것이다.

### 2026-04-13 | Human + Codex | CLI-first 구조 전환: service 7개 그룹과 diagnostics route 기준 정리

- `runtime`에는 `workspace / settings / mailbox / analysis / exports / pipeline / diagnostics` 7개 service 그룹을 추가했다.
- `runtime.cli`는 위 service를 반영한 명시적 하위 명령을 지원한다.
- `runtime.diagnostics_service`는 picker self-test와 native picker 호출을 맡고, `EPA_PICKER_TEST_RESPONSE / ERROR / CANCEL` override로 자동 smoke를 재현할 수 있게 했다.
- `runtime.pipeline_service`는 `scope=recent|all`, `limit=N` 기준 sync 결과와 reuse count를 함께 반환한다.
- `runtime.feature_harness_smoke`는 이제 workspace/settings/diagnostics/analysis/exports service를 직접 호출해 결과 계약도 함께 검증한다.

### 2026-04-13 | Human + Codex | v2 세이브 구조 고정과 로컬 장치 전용 보조 저장소 추가

- 새 세이브 생성 시 manifest를 먼저 쓴 뒤 디렉토리를 만들도록 순서를 고쳐, 새 세이브가 더 이상 legacy `참고자료 / 실행결과 / 기대되는 산출물` 폴더를 만들지 않게 했다.
- canonical save 구조는 `mail / exports / logs / secure / state / locks`로 다시 고정했고, sample workspace도 같은 구조로만 생성되도록 맞췄다.
- 이 PC 전용 암호화 저장소를 추가해 마지막 세이브 경로, 마지막 세이브 암호, 기본 OpenAI API key를 세이브 파일과 분리된 장치 로컬 비밀값으로 관리하게 했다.
- 최근 세이브 바로 다시 열기와 앱 재실행 자동 재개는 이 로컬 비밀값과 local settings를 함께 써서 동작하게 했다.
- feature harness smoke는 새 v2 샘플 세이브 기준으로 다시 통과했고, Linux 개발 호스트에서는 Windows 전용 packaging prerequisite를 `warn`으로만 보여주도록 정리했다.

### 2026-04-08 | Human + Codex | feature registry와 샘플 워크스페이스 seed 추가

- `runtime/feature_registry.py`를 추가해 현재 제품/운영 기능의 canonical registry를 만들고, 관리도구/CLI에서 같은 정의를 재사용하게 했다.
- `feature_runs`를 sqlite에 추가해 기능별 최근 실행 상태와 산출물 요약을 저장하게 했다.
- `runtime/cli.py`는 `feature-list`, `feature-inspect`, `feature-check`, `feature-run`, `create-sample-workspace` 명령을 지원하게 됐다.
- `runtime/sample_workspace.py`는 합성 메일 4건으로 review board, dedupe, 운영 workbook을 채운 repo-safe sample save를 생성한다.

### 2026-04-08 | Human + Codex | feature harness smoke와 전체 prerequisite 점검 추가

- `runtime/cli.py`에 `feature-check-all`, `feature-harness-smoke` 명령을 추가해 현재 feature 카탈로그를 전량 점검하고 샘플 워크스페이스 smoke를 한 번에 돌릴 수 있게 했다.
- `runtime/feature_harness_smoke.py`는 sample workspace와 `app/ui_smoke.py`를 묶어 review center, admin tool, workbook 재반영까지 반복 검증한다.
- `runtime/docs/환경/feature_harness.md`에 샘플 세이브 생성, 전체 smoke, UI smoke 단독 실행 절차를 정리했다.

### 2026-04-08 | Human + Codex | 공유 워크스페이스 save v1 도입

- `workspace.epa-workspace.json`, `secure/secrets.enc.json`, `state/state.sqlite`, `locks/write.lock`, `profile/` 구조를 공유 save 기준으로 도입했다.
- 비밀값은 `AES-256-GCM + scrypt` 기반 암호화 blob에 저장하고, review state와 dedupe/representative 상태는 sqlite에 저장한다.
- `runtime/cli.py`로 workspace 생성, inspect, sync를 텍스트 기반으로 실행할 수 있게 했다.
- 기존 `mailbox` backfill, `analysis` review board, `exports` workbook append 경로를 그대로 재사용해 stable 운영 workbook과 `검토_인덱스` 시트 재구성 경로를 만들었다.

### 2026-04-10 | Human + Codex | quick/full sync와 analysis 재사용 기본화

- `run_workspace_sync`는 이제 `quick_smoke`, `incremental_full` 두 모드를 지원한다.
- `quick_smoke`는 IMAP backfill과 review refresh를 최근 10건으로 제한해 첫 연결 확인용 흐름을 빠르게 점검한다.
- `analysis/materialized_bundle_smoke.py`는 `analysis_revision + bundle fingerprint` 기준 meta sidecar를 남기고, 같은 입력이면 기존 추출 결과를 재사용한다.
- `analysis.review_board_refresh`와 runtime sync 경로도 이제 기본적으로 `reuse_existing_analysis=True`를 사용해 unchanged bundle의 LLM 재호출을 줄인다.
- `runtime.feature_registry.py`에는 `mailbox.connection_check`, `runtime.workspace.sync.quick_smoke`를 추가해 UI와 관리도구가 같은 카탈로그 언어를 쓰게 했다.
