# Runtime Logbook

> 이 문서는 `runtime` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 작업 시작 게이트와 읽기 순서는 root `AGENTS.md`를 따른다.

## 현재 스냅샷

- 공유 워크스페이스 manifest, 암호화 secret blob, sqlite state, write lock이 있다.
- 기존 엔진을 `mail / exports / logs` 기준의 v2 세이브 구조로 다시 돌리는 sync service가 있다.
- review report를 state DB로 ingest하고 회사 기준 dedupe를 적용한다.
- stable 운영 workbook을 다시 만들고 `검토_인덱스` 시트를 함께 쓴다.
- CLI로 workspace create / inspect / sync를 실행할 수 있다.
- feature registry와 feature run history가 있다.
- repo-safe 샘플 워크스페이스 seed를 만들 수 있다.
- `feature-check-all`과 `feature-harness-smoke`로 카탈로그 전량 점검과 반복 smoke를 수행할 수 있다.
- sync는 `quick_smoke`와 `incremental_full` 두 모드를 지원하고, analysis revision/fingerprint가 같으면 기존 분석 결과를 재사용한다.
- 새 세이브는 legacy `profile/참고자료/실행결과` 구조를 만들지 않고, v1 세이브는 unsupported로 안내한다.

## 현재 활성 체크리스트

- [x] 공유 워크스페이스 manifest와 표준 폴더 구조 도입
- [x] 암호화 secret 저장 경로 도입
- [x] sqlite state DB와 write lock 도입
- [x] 이전 beta 세이브 차단과 새 v2 세이브 구조 정리
- [x] review report -> state DB ingest 경로 도입
- [x] 대표 신청 건 기준 stable 운영 workbook 재구성 경로 도입
- [x] feature 카탈로그와 feature run history 도입
- [x] repo-safe sample workspace seed 도입
- [x] feature-check-all, feature-harness-smoke, app UI smoke 연동
- [x] quick/full sync 모드와 analysis 재사용 기준 도입
- [ ] override 저장 후 UI에서 더 정교한 diff/재계산 표시 보강
- [ ] 증분 sync 성능과 장시간 heartbeat 운영성 보강

## 최근 로그

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
