# LLM

이 디렉토리는 language model orchestration 계층 자리다.

현재 상태:

- 구현 시작 전
- 현재 기본 후보는 ChatGPT API다

예상 역할:

- OpenAI client 구성
- prompt template 관리
- structured response schema 연결
- usage / latency / failure handling 정리

현재 구현 방향:

- 모델 이름보다 먼저 입력 계약과 출력 schema를 고정한다.
- 분류, 추출, 요약, 답장 draft는 같은 호출로 억지로 합치지 않고 역할별로 나눈다.
- 민감한 원문은 로그에 과도하게 남기지 않는다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)

