# private-assets-and-secrets-boundary

이 skill은 민감 정보와 private runtime 자산의 경계를 지키는 절차를 정리한다.

## 언제 쓰나

- 실제 이메일 계정, 앱 비밀번호, API 키를 다룰 때
- 실제 메일 원문, 첨부 원본, 실제 workbook, 사용자 로그를 다룰 때
- tracked 문서에 어떤 경로까지 써도 되는지 판단할 때

## 기본 경계

- tracked repo에는 secret 값, 실제 메일 내용, 실제 첨부 원본을 넣지 않는다.
- canonical 로컬 시작 문서는 sibling `../secrets/README.local.md`다.
- reference fixture는 `../secrets/사용자 설정/<이름>/참고자료/`에 둔다.
- 실제 runtime 메일, 첨부, workbook, 로그는 `../secrets/사용자 설정/<이름>/실행결과/`에 둔다.

## 해야 할 일

1. 지금 작업이 private boundary를 건드리는지 먼저 판단한다.
2. tracked 문서에는 경로와 운영 원칙만 쓰고, secret 값과 실제 데이터는 쓰지 않는다.
3. repo 내부 결과물로 옮겨도 되는지 애매하면 `module/results/` 대신 `../secrets/`를 우선한다.
4. 커밋 전에는 `README.local.md`, `.env`, secret 경로가 staging에 섞이지 않았는지 다시 확인한다.
