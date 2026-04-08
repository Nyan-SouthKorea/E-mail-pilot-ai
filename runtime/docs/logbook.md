# Runtime Logbook

> 이 문서는 `runtime` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 비사소한 작업 전에는 `../../AGENTS.md -> ../../README.md -> ../../docs/logbook.md -> ../README.md -> ./logbook.md` 순서로 다시 읽는다.

## 현재 스냅샷

- 공유 워크스페이스 manifest, 암호화 secret blob, sqlite state, write lock이 있다.
- 기존 엔진을 `workspace/profile` 기준으로 다시 돌리는 sync service가 있다.
- review report를 state DB로 ingest하고 회사 기준 dedupe를 적용한다.
- stable 운영 workbook을 다시 만들고 `검토_인덱스` 시트를 함께 쓴다.
- CLI로 workspace create / inspect / sync를 실행할 수 있다.

## 현재 활성 체크리스트

- [x] 공유 워크스페이스 manifest와 표준 폴더 구조 도입
- [x] 암호화 secret 저장 경로 도입
- [x] sqlite state DB와 write lock 도입
- [x] 기존 profile import 경로 도입
- [x] review report -> state DB ingest 경로 도입
- [x] 대표 신청 건 기준 stable 운영 workbook 재구성 경로 도입
- [ ] override 저장 후 UI에서 더 정교한 diff/재계산 표시 보강
- [ ] 증분 sync 성능과 장시간 heartbeat 운영성 보강

## 최근 로그

### 2026-04-08 | Human + Codex | 공유 워크스페이스 save v1 도입

- `workspace.epa-workspace.json`, `secure/secrets.enc.json`, `state/state.sqlite`, `locks/write.lock`, `profile/` 구조를 공유 save 기준으로 도입했다.
- 비밀값은 `AES-256-GCM + scrypt` 기반 암호화 blob에 저장하고, review state와 dedupe/representative 상태는 sqlite에 저장한다.
- `runtime/cli.py`로 workspace 생성, inspect, sync를 텍스트 기반으로 실행할 수 있게 했다.
- 기존 `mailbox` backfill, `analysis` review board, `exports` workbook append 경로를 그대로 재사용해 stable 운영 workbook과 `검토_인덱스` 시트 재구성 경로를 만들었다.
