# Analysis

이 디렉토리는 이메일 해석 계층 자리다.

현재 상태:

- 기본 schema 골격 정의 완료
- 실제 LLM 추출 파이프라인은 아직 시작 전

현재 입력 계약:

- `NormalizedMessage`: 본문, 참여자, artifact inventory를 정규화한 공통 입력
- `EvidenceRef`: 본문, 첨부, OCR, 표 추출 등 근거 위치를 가리키는 단위

기본 산출 계약:

- `ExtractedField`: 필드 값과 근거 id 묶음
- `ExtractedRecord`: 분류, 요약, confidence, action hint, unresolved question을 담는 분석 결과

예상 역할:

- 이메일 분류
- 필요한 필드 추출
- 요약 생성
- 첨부파일 설명 또는 핵심 정보 추출
- 이미지, 표, 스캔 문서 기반 정보 추출
- 내부 schema로 결과 정규화

현재 구현 방향:

- 자유서술보다 structured output을 우선한다.
- `분류`, `추출`, `요약`, `confidence`, `action hints`를 구분해 다룬다.
- 모델 교체보다 먼저 출력 계약을 고정한다.
- 필드 값만 따로 떼지 않고, 가능한 한 evidence id를 함께 남긴다.
- 요약은 신청서와 이메일 본문 기준으로 중복 표현을 줄이고, 보고용 가독성을 높이는 방향을 기본으로 둔다.
- 본문이 비어 있거나 약해도 inline 이미지, 첨부 이미지, 스캔 PDF, 이미지 속 표에서 근거를 끌어올 수 있게 설계한다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)
- [`../llm/README.md`](../llm/README.md)
