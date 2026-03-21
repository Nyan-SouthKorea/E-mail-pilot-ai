# Mailbox

이 디렉토리는 이메일 수집과 입력 정규화 계층 자리다.

현재 상태:

- 구현 시작 전
- 프로젝트의 첫 런타임 진입점이 될 가능성이 가장 높다

예상 역할:

- IMAP, Gmail API, Outlook API 같은 provider 연결
- 도메인 규칙, provider 프리셋, autodiscover/autoconfig 기반 메일 설정 후보 탐지
- IMAP / POP / SMTP host / port / security probe와 접속 검증
- inbox polling 또는 webhook 수신
- message, thread, attachment 메타데이터 수집
- raw email `.eml` 보존과 human preview `.html` 생성
- inline image / attachment 추출과 메일별 artifact bundle 관리
- text/html 본문뿐 아니라 이미지형 본문 자산과 첨부를 후속 해석 계층으로 넘길 수 있는 입력 정리
- cursor / checkpoint / dedup key 관리
- raw provider payload를 내부 공통 schema로 정규화

현재 구현 방향:

- provider별 구현은 갈아끼울 수 있게 분리한다.
- 상위 계층에는 `새 메시지 묶음`, `정규화된 thread`, `attachment inventory` 같은 공통 계약만 노출한다.
- 메일 설정 자동 탐지는 mailbox 계층의 1차 책임으로 두고, 성공한 설정값을 GUI와 프로필 저장 계층에 함께 전달한다.
- 자동 설정은 도메인 규칙 -> provider 프리셋 -> autodiscover/autoconfig -> 접속 테스트 순으로 시도한다.
- 실제 수신 메일은 reference fixture와 섞지 않고 별도 런타임 경로에 저장한다.
- 메일 원본 보존은 `.eml`, 빠른 열람은 `.html` preview를 기본 조합으로 둔다.
- 현재 샘플 메일 형식에 맞춘 특수 분기보다, 다양한 MIME 구조와 첨부 구성을 가능한 한 보편적으로 정규화하는 쪽을 우선한다.
- 인증 정보와 실제 메일 원문은 문서나 Git 추적 자산이 아닌 로컬 런타임 경로에서 관리한다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)
