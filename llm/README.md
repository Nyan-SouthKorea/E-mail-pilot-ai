# LLM

이 디렉토리는 language model orchestration 계층 자리다.

현재 상태:

- OpenAI Responses wrapper 골격 추가
- JSONL usage log와 가격표 snapshot 기반 비용 추정 추가
- 템플릿 unresolved header 의미 보충용 fallback 호출 경로 추가

예상 역할:

- OpenAI client 구성
- prompt template 관리
- structured response schema 연결
- usage / latency / failure handling 정리
- usage 토큰과 예상 비용 집계
- 예외적인 provider 힌트 보조 추론이나 사용자 안내 문구 생성

현재 구현 방향:

- 모델 이름보다 먼저 입력 계약과 출력 schema를 고정한다.
- 분류, 추출, 요약, 답장 draft는 같은 호출로 억지로 합치지 않고 역할별로 나눈다.
- 메일 연결 설정 탐지는 기본적으로 LLM 문제가 아니라 mailbox 계층의 룰베이스 / probe 문제로 본다.
- LLM은 메일 설정 자동 탐지의 주수단이 아니라, 예외 케이스 설명과 보조 추론에만 제한적으로 사용한다.
- 민감한 원문은 로그에 과도하게 남기지 않는다.
- 모든 OpenAI 호출은 wrapper를 거친다.
- 프로필 기반 실행의 기본 로그는 `../secrets/사용자 설정/<이름>/실행결과/로그/llm/openai_usage.jsonl`에 JSONL로 남긴다.
- 프로필이 아직 없는 일회성 실험에서는 필요할 때만 `../results/llm/openai_usage.jsonl` fallback을 쓸 수 있다.
- 예상 비용은 API 응답의 `usage` 토큰과 가격표 snapshot으로 계산한다.
- 비용 로그는 관찰용으로 유지하되, 실제 설계 판단은 비용보다 성능과 정확도를 우선한다.
- structured output이 필요한 호출은 Responses API 기준으로 설계한다.
- 템플릿 헤더 의미 해석은 rule로 먼저 처리하고, unresolved header만 작은 structured output 요청으로 fallback 한다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)
