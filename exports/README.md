# Exports

이 디렉토리는 구조화된 결과를 Excel과 다른 산출물로 내보내는 계층 자리다.

현재 상태:

- 구현 시작 전

예상 역할:

- canonical row schema 정의
- workbook template 매핑
- sheet별 append / update 정책 관리
- 결과물 경로와 파일명 규칙 관리
- 기존 workbook 스타일, 수식, 정렬, 줄바꿈 보존 전략 관리

현재 구현 방향:

- 먼저 Excel v1 경로를 기준 출력으로 고정한다.
- 입력 계약은 우선 `ExtractedRecord`를 기준으로 받는다.
- 사람이 실제로 쓰는 열 구조와 key 컬럼을 먼저 정하고, 코드가 그 계약을 따르게 한다.
- 사용자가 직접 수정한 workbook을 전제로, AI는 마지막 사용 행 다음으로 append하는 정책을 기본으로 둔다.
- 새로 쓰는 셀은 기존 폰트, 정렬, 줄바꿈, 수식, 셀 너비를 최대한 이어받아 사람이 이어서 작성한 것처럼 보이게 한다.
- generated 파일은 리포 안이 아니라 로컬 `results/` 계층을 기본 출력으로 본다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)
