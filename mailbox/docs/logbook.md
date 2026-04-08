# Mailbox Logbook

> 이 문서는 `mailbox` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 비사소한 작업 전에는 `../../AGENTS.md -> ../../README.md -> ../../docs/logbook.md -> ../README.md -> ./logbook.md` 순서로 다시 읽는다.
- 새 로그를 쓰기 전에는 가능하면 `python tools/logbook_archive_guard.py --path mailbox/docs/logbook.md --archive-if-needed`를 먼저 실행한다.

## 현재 스냅샷

- `MailBundle`, `NormalizedMessage`, bundle path helper가 있다.
- fixture를 실제 runtime bundle 구조로 materialize 하는 smoke가 있다.
- runtime bundle의 `normalized.json`을 다시 읽는 bundle reader가 있다.
- provider preset, generic domain pattern, Mozilla autoconfig, connect/auth probe를 묶은 자동 설정 경로가 있다.
- 아직 실제 inbox에서 최신 메일을 가져와 bundle로 저장하는 fetch smoke는 없다.

## 현재 활성 체크리스트

- [x] bundle schema와 기본 저장 레이아웃 고정
- [x] fixture materialize smoke 추가
- [x] bundle reader 추가
- [x] 메일 설정 후보 생성과 connect/auth probe smoke 추가
- [ ] 실제 계정 기준 auth probe 실행
- [ ] 최신 inbox 1건 fetch smoke 추가
- [ ] fetch 결과를 `MailBundle` 저장과 `normalized.json` 생성까지 연결

## 최근 로그

### 2026-04-08 | Human + Codex | 모듈 logbook 체계 도입

- 프로젝트 전역 문서 체계가 루트 `AGENTS.md`, 루트 `README.md`, 프로젝트 `docs/logbook.md`, 모듈 `docs/logbook.md`로 재편되면서 `mailbox`의 active 상태 문서를 이 파일로 분리했다.
- 기존 모듈 README에 있던 현재 상태와 다음 작업 중 active 성격의 내용은 이 문서로 옮기고, README는 안정된 설명과 경계 설명 중심으로 유지했다.
