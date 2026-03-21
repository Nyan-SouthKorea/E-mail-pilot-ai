# Analysis

이 디렉토리는 이메일 해석 계층 자리다.

현재 상태:

- 기본 schema 클래스 골격 정의 완료
- fixture 기반 첫 LLM 분석 smoke 입력 골격 추가
- fixture 이메일에서 workbook append까지 이어지는 end-to-end smoke 진입점 추가
- materialized bundle의 `normalized.json`을 직접 읽는 live 분석 smoke 추가
- materialized bundle에서 workbook append까지 이어지는 end-to-end smoke 진입점 추가

현재 입력 계약:

- `NormalizedMessage`: 본문, 참여자, artifact inventory를 정규화한 공통 입력
- `EvidenceRef`: 본문, 첨부, OCR, 표 추출 등 근거 위치를 가리키는 단위
- 현재 구현 형태는 재사용성과 유지보수성을 위한 class 중심 schema 기준이다.

기본 산출 계약:

- `ExtractedField`: 필드 값과 근거 id 묶음
- `ExtractedRecord`: 분류, 요약, confidence, action hint, unresolved question을 담는 분석 결과
- `ExtractedRecord`는 프로필 템플릿과 무관한 공통 의미 필드를 유지하는 기준 계약이다.
- 가능하면 `ExtractedField.field_name`은 `company_name`, `business_summary` 같은 공통 의미 키와 가깝게 유지하고, 초기 변형은 export 계층 alias 규칙이 흡수한다.

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
- 현재 단계에서는 과한 추상화는 피하되, 반복해서 쓰일 분석 계약은 class로 유지한다.
- 템플릿별 열 구조가 달라도, analysis 계층은 가능한 한 공통 의미 필드를 안정적으로 뽑아내는 데 집중한다.
- 요약은 신청서와 이메일 본문 기준으로 중복 표현을 줄이고, 보고용 가독성을 높이는 방향을 기본으로 둔다.
- 본문이 비어 있거나 약해도 inline 이미지, 첨부 이미지, 스캔 PDF, 이미지 속 표에서 근거를 끌어올 수 있게 설계한다.
- 초기 smoke 단계에서는 fixture 디렉토리의 이메일 본문과 ZIP 내부 XLSX 요약을 합쳐 structured output 기반 첫 분석 호출을 준비한다.
- extraction prompt와 structured output schema는 [`llm_extraction.py`](llm_extraction.py)에서 같이 관리한다.
- runtime bundle을 다시 읽는 분석에서는 bundle 루트의 `normalized.json`을 canonical `NormalizedMessage` 입력으로 사용한다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)
- [`../llm/README.md`](../llm/README.md)
