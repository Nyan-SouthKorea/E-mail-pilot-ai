# Mailbox Logbook

> 이 문서는 `mailbox` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 작업 시작 게이트와 읽기 순서는 root `AGENTS.md`를 따른다.
- 새 로그를 쓰기 전에는 가능하면 `python tools/logbook_archive_guard.py --path mailbox/docs/logbook.md --archive-if-needed`를 먼저 실행한다.

## 현재 스냅샷

- `MailBundle`, `NormalizedMessage`, bundle path helper가 있다.
- fixture를 실제 runtime bundle 구조로 materialize 하는 smoke가 있다.
- runtime bundle의 `normalized.json`을 다시 읽는 bundle reader가 있다.
- provider preset, generic domain pattern, Mozilla autoconfig, connect/auth probe를 묶은 자동 설정 경로가 있다.
- local-only 계정 정보 loader가 있다.
- 실제 계정 기준 auth probe와 최신 IMAP 1건 fetch smoke가 있다.
- 실제 fetch 결과를 runtime `MailBundle`, `preview.html`, `normalized.json`, `summary.md`까지 저장한다.
- 실제 계정 `INBOX` 전체를 read-only로 backfill 하는 smoke가 있다.
- 공유 워크스페이스 sync에서는 같은 mailbox 엔진을 `workspace/profile` 기준으로 다시 호출할 수 있다.

## 현재 활성 체크리스트

- [x] bundle schema와 기본 저장 레이아웃 고정
- [x] fixture materialize smoke 추가
- [x] bundle reader 추가
- [x] 메일 설정 후보 생성과 connect/auth probe smoke 추가
- [x] 실제 계정 기준 auth probe 실행
- [x] 최신 inbox 1건 fetch smoke 추가
- [x] fetch 결과를 `MailBundle` 저장과 `normalized.json` 생성까지 연결
- [x] 저장된 최신 bundle 1건을 materialized analysis smoke와 연결
- [x] INBOX 전체 read-only backfill smoke 추가
- [ ] 폴더 선택, unseen 우선순위, 증분 fetch 기준 정리

## 최근 로그

### 2026-04-08 | Human + Codex | 공유 워크스페이스 sync 경로 연결

- mailbox 계정 설정을 로컬 파일 대신 공유 워크스페이스 암호화 설정으로도 공급할 수 있게 `LocalMailboxAccountConfig` 명시 생성 helper를 추가했다.
- `run_imap_latest_mail_fetch_smoke`, `run_imap_inbox_backfill_smoke`는 파일 경로 대신 이미 구성된 account config도 받아 shared workspace sync에서 재사용할 수 있게 맞췄다.

### 2026-04-08 | Human + Codex | INBOX 전체 read-only backfill smoke 추가

- 최신 1건 fetch에서 검증한 auth probe와 materialize 경로를 재사용해, 실제 계정 `INBOX` 전체를 UID 순서로 읽는 backfill smoke를 추가했다.
- 기존 valid bundle id와 같은 메일은 skip하고, 실패 항목은 JSON report에 개별 uid와 함께 남긴다.
- 전체 backfill도 계속 read-only IMAP `BODY.PEEK[]` 기준을 유지한다.
- runtime bundle에 이미 저장된 IMAP UID를 먼저 읽어 skip하는 resume 경로와 100건 단위 checkpoint report 저장을 추가해, 긴 backfill을 중간부터 이어서 끝낼 수 있게 했다.
- `Received:` 헤더로 시작하는 오래된 메일도 raw RFC822 원문으로 인식하도록 fetch payload 판별기를 넓혀, 초기 backfill에서 실패하던 다수 메일을 정상 materialize 하도록 고쳤다.
- 실제 full INBOX run 결과 `4690`개 메시지 중 새 fetch `3108`, 기존 skip `1582`, failed `0`으로 마무리했고, runtime 기준 valid bundle은 총 `4692`건이 됐다.

### 2026-04-08 | Human + Codex | 실제 계정 auth probe와 latest IMAP fetch smoke 추가

- sibling `secrets` 아래 local-only 계정 문서를 읽는 helper를 추가했다.
- auth probe는 명시된 로그인 id를 먼저 시도하고, 실패 시 이메일 주소로 fallback 하도록 바꿨다.
- MX 레코드 기반 host 후보를 자동 설정 후보에 합쳐, generic host 패턴이 맞지 않는 계정도 probe할 수 있게 했다.
- 최신 메일 1건 fetch는 IMAP read-only `BODY.PEEK[]` 기준으로 구현했고, runtime bundle 저장과 `normalized.json` 생성까지 연결했다.
- 실제 smoke에서 auth probe와 latest fetch가 성공했고, 결과 산출물은 tracked repo가 아닌 sibling runtime 경로에만 저장했다.

### 2026-04-08 | Human + Codex | 모듈 logbook 체계 도입

- 프로젝트 전역 문서 체계가 루트 `AGENTS.md`, 루트 `README.md`, 프로젝트 `docs/logbook.md`, 모듈 `docs/logbook.md`로 재편되면서 `mailbox`의 active 상태 문서를 이 파일로 분리했다.
- 기존 모듈 README에 있던 현재 상태와 다음 작업 중 active 성격의 내용은 이 문서로 옮기고, README는 안정된 설명과 경계 설명 중심으로 유지했다.
