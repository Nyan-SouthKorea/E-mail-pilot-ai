# Exports

이 디렉토리는 구조화된 결과를 Excel과 다른 산출물로 내보내는 계층 자리다.

현재 상태:

- 구현 시작 전

예상 역할:

- canonical row schema 정의
- workbook template 매핑
- sheet별 append / update 정책 관리
- 결과물 경로와 파일명 규칙 관리

현재 구현 방향:

- 먼저 Excel v1 경로를 기준 출력으로 고정한다.
- 사람이 실제로 쓰는 열 구조와 key 컬럼을 먼저 정하고, 코드가 그 계약을 따르게 한다.
- generated 파일은 리포 안이 아니라 로컬 `results/` 계층을 기본 출력으로 본다.

현재 참고 기준:

- [`../docs/status.md`](../docs/status.md)
- [`../docs/개발방침.md`](../docs/개발방침.md)
