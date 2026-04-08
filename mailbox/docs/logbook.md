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
- local-only 계정 정보 loader가 있다.
- 실제 계정 기준 auth probe와 최신 IMAP 1건 fetch smoke가 있다.
- 실제 fetch 결과를 runtime `MailBundle`, `preview.html`, `normalized.json`, `summary.md`까지 저장한다.

## 현재 활성 체크리스트

- [x] bundle schema와 기본 저장 레이아웃 고정
- [x] fixture materialize smoke 추가
- [x] bundle reader 추가
- [x] 메일 설정 후보 생성과 connect/auth probe smoke 추가
- [x] 실제 계정 기준 auth probe 실행
- [x] 최신 inbox 1건 fetch smoke 추가
- [x] fetch 결과를 `MailBundle` 저장과 `normalized.json` 생성까지 연결
- [ ] 저장된 최신 bundle 1건을 materialized analysis smoke와 연결
- [ ] 폴더 선택, unseen 우선순위, 다건/증분 fetch 기준 정리

## 최근 로그

### 2026-04-08 | Human + Codex | 실제 계정 auth probe와 latest IMAP fetch smoke 추가

- sibling `secrets` 아래 local-only 계정 문서를 읽는 helper를 추가했다.
- auth probe는 명시된 로그인 id를 먼저 시도하고, 실패 시 이메일 주소로 fallback 하도록 바꿨다.
- MX 레코드 기반 host 후보를 자동 설정 후보에 합쳐, generic host 패턴이 맞지 않는 계정도 probe할 수 있게 했다.
- 최신 메일 1건 fetch는 IMAP read-only `BODY.PEEK[]` 기준으로 구현했고, runtime bundle 저장과 `normalized.json` 생성까지 연결했다.
- 실제 smoke에서 auth probe와 latest fetch가 성공했고, 결과 산출물은 tracked repo가 아닌 sibling runtime 경로에만 저장했다.

### 2026-04-08 | Human + Codex | 모듈 logbook 체계 도입

- 프로젝트 전역 문서 체계가 루트 `AGENTS.md`, 루트 `README.md`, 프로젝트 `docs/logbook.md`, 모듈 `docs/logbook.md`로 재편되면서 `mailbox`의 active 상태 문서를 이 파일로 분리했다.
- 기존 모듈 README에 있던 현재 상태와 다음 작업 중 active 성격의 내용은 이 문서로 옮기고, README는 안정된 설명과 경계 설명 중심으로 유지했다.
