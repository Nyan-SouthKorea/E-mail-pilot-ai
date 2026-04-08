# results-hygiene-and-cleanup

이 skill은 runtime 산출물과 repo-safe 산출물의 경계를 지키고, 임시 결과를 정리하는 절차를 정리한다.

## 언제 쓰나

- smoke 결과가 많이 생길 때
- workbook 비교나 diff 보고서를 남길 때
- 임시 디버그 결과를 정리할 때

## 기본 원칙

- 실제 사용자 메일, 첨부, workbook, profile 로그는 `../secrets/사용자 설정/<이름>/실행결과/`가 canonical이다.
- repo 내부 `<module>/results/`는 재현 가능한 smoke 결과, 소형 비교 자료, metadata에 한해 사용한다.
- reference fixture는 읽기 전용으로 유지한다.
- smoke/debug/failed 산출물은 필요한 사실을 logbook에 남긴 뒤 삭제 가능한 임시 자산으로 본다.

## 해야 할 일

1. 지금 결과물이 private runtime 자산인지 repo-safe한 재현 산출물인지 먼저 구분한다.
2. 공식 위치가 다르면 결과물을 옮기기보다 잘못된 위치 생성을 먼저 막는다.
3. 큰 결과물은 canonical 위치만 남기고 중복 복사본은 줄인다.
4. cleanup 뒤에는 logbook에 무엇을 남기고 무엇을 지웠는지 짧게 적는다.
