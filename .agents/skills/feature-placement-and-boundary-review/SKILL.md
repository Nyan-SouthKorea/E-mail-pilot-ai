# feature-placement-and-boundary-review

이 skill은 새 기능, 새 폴더, 파일 이동, 레이어 경계 판단이 있을 때 기능 소속을 정하는 절차를 정리한다.

## 언제 쓰나

- 새 기능을 추가할 때
- 파일이나 폴더를 다른 모듈로 옮길 때
- `app/`, `runtime/` 같은 새 상위 계층 도입을 검토할 때

## 먼저 보는 기준

- `README.md`의 `새 기능을 어디에 둘까`
- 관련 모듈 `README.md`
- 관련 모듈 `docs/logbook.md`

## 빠른 판단 질문

- 메일 서버 탐지, probe, fetch, bundle 저장 문제인가
- 구조화 추출, 요약, 이미지 해석 문제인가
- 템플릿 해석, projection, workbook append 문제인가
- 공용 모델 호출과 usage logging 문제인가
- GUI나 사용자 실행 흐름 문제인가
- 장시간 배치와 watchdog 문제인가

## 경계 원칙

- `mailbox`는 메일 원본과 설정 탐지 책임을 가진다.
- `analysis`는 값 추출과 요약 책임을 가진다.
- `exports`는 템플릿과 workbook 책임을 가진다.
- `llm`은 transport와 logging 책임만 가진다.
- `app`과 `runtime`은 필요가 생길 때만 만들고, 모듈 경계를 흐리지 않는다.
