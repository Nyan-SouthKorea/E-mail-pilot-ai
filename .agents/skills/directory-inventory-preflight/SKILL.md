# directory-inventory-preflight

이 skill은 새 파일, 새 폴더, 새 결과물, 새 문서를 만들기 전에 기존 구조를 먼저 점검하는 절차를 정리한다.

## 언제 쓰나

- 새 문서를 만들 때
- 새 로그나 보고서를 만들 때
- 새 결과물 루트를 만들 때
- 파일 복사, 이동, archive 전에 기존 구조를 확인할 때

## 기본 명령

- `python tools/directory_inventory.py --module <module> --kind <kind> --candidate-name <name>`

## 해야 할 일

1. 관련 모듈 `README.md`와 `docs/logbook.md`를 먼저 읽는다.
2. 위 명령으로 기존 디렉토리와 비슷한 이름이 이미 있는지 확인한다.
3. 공식 위치만 정의돼 있고 아직 실제 폴더가 없어도, 필요 없는 빈 디렉토리는 만들지 않는다.
4. 실제로 만들어야 하는 위치가 맞는지 확인한 뒤에만 파일이나 폴더를 만든다.
