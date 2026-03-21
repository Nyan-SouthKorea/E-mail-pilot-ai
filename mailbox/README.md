# Mailbox

이 디렉토리는 이메일 수집과 입력 정규화 계층 자리다.

현재 상태:

- 구현 시작 전
- 프로젝트의 첫 런타임 진입점이 될 가능성이 가장 높다

예상 역할:

- IMAP, Gmail API, Outlook API 같은 provider 연결
- inbox polling 또는 webhook 수신
- message, thread, attachment 메타데이터 수집
- cursor / checkpoint / dedup key 관리
- raw provider payload를 내부 공통 schema로 정규화

현재 구현 방향:

- provider별 구현은 갈아끼울 수 있게 분리한다.
- 상위 계층에는 `새 메시지 묶음`, `정규화된 thread`, `attachment inventory` 같은 공통 계약만 노출한다.
- 인증 정보와 실제 메일 원문은 리포 밖 로컬 경로에서 관리한다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)
