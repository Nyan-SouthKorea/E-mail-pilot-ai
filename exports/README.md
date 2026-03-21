# Exports

이 디렉토리는 구조화된 결과를 Excel과 다른 산출물로 내보내는 계층 자리다.

현재 상태:

- template schema/reader, semantic mapping, record projection schema 정의 완료

예상 역할:

- 프로필별 레퍼런스 Excel을 `TemplateProfile`로 해석
- 공통 의미 키 catalog와 템플릿 열 semantic mapping 관리
- `ExtractedRecord` 필드 alias 해석과 템플릿 열 projection
- canonical row schema 정의
- workbook template 매핑
- sheet별 append / update 정책 관리
- 결과물 경로와 파일명 규칙 관리
- 기존 workbook 스타일, 수식, 정렬, 줄바꿈 보존 전략 관리

현재 구현 방향:

- 프로젝트 전체에 하나의 고정 열 구조를 먼저 박아두기보다, 프로필별 레퍼런스 Excel 문서를 읽어 템플릿 규칙으로 해석하는 방식을 우선한다.
- 템플릿 해석 객체는 우선 `TemplateProfile -> TemplateSheet -> TemplateColumn` 구조로 둔다.
- 열 의미 해석 결과는 `TemplateSemanticMapping`으로 분리해 rule 기반, LLM 기반, 수동 보정 결과를 같은 형식으로 다룰 수 있게 한다.
- 입력 계약은 우선 `ExtractedRecord`를 기준으로 받는다.
- `ExtractedRecord`의 필드명이 바로 의미 키와 같지 않아도 alias와 summary fallback으로 공통 의미 키를 먼저 해석한 뒤, 템플릿 열 순서로 projection 한다.
- 공통 의미 필드는 `ExtractedRecord`에 유지하고, 실제 workbook 열 순서와 헤더 이름은 프로필별 템플릿에서 가져온다.
- 템플릿 열 이름이 비정형이면 LLM으로 의미를 해석하고, 실제 셀 위치 계산과 쓰기는 코드가 담당한다.
- 사용자가 직접 수정한 workbook을 전제로, AI는 마지막 사용 행 다음으로 append하는 정책을 기본으로 둔다.
- 새로 쓰는 셀은 기존 폰트, 정렬, 줄바꿈, 수식, 셀 너비를 최대한 이어받아 사람이 이어서 작성한 것처럼 보이게 한다.
- generated 파일은 리포 안이 아니라 로컬 `results/` 계층을 기본 출력으로 본다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)
