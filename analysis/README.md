# Analysis

이 디렉토리는 이메일 해석 계층 자리다.

현재 상태:

- 구현 시작 전
- LLM 기반 구조화 분석의 중심 모듈로 계획 중이다

예상 역할:

- 이메일 분류
- 필요한 필드 추출
- 요약 생성
- 첨부파일 설명 또는 핵심 정보 추출
- 내부 schema로 결과 정규화

현재 구현 방향:

- 자유서술보다 structured output을 우선한다.
- `분류`, `추출`, `요약`, `confidence`, `action hints`를 구분해 다룬다.
- 모델 교체보다 먼저 출력 계약을 고정한다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)
- [`../llm/README.md`](../llm/README.md)

