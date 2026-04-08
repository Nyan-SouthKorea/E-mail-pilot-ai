# logbook-maintenance

이 skill은 active logbook를 적당한 크기로 유지하고 archive를 정리하는 절차를 정리한다.

## 언제 쓰나

- 새 로그를 추가할 때
- active logbook가 길어졌을 때
- legacy 문서를 archive로 내릴 때

## 기본 명령

- `python tools/logbook_archive_guard.py --archive-if-needed`
- `python tools/logbook_archive_all.py --archive-if-needed`

## 기본 원칙

- active logbook는 현재 스냅샷, 현재 전역 결정, active checklist, 최근 로그만 유지한다.
- 오래된 상세 기록은 `docs/logbook_archive/`로 보낸다.
- README에는 최근 작업 로그를 길게 쌓지 않는다.

## 해야 할 일

1. 새 로그를 쓰기 전에 archive guard를 먼저 돌린다.
2. `1000`줄을 넘으면 archive한 뒤 active logbook를 고정 섹션 중심으로 다시 시작한다.
3. legacy 문서를 내릴 때는 archive 파일 이름에 날짜 prefix를 붙인다.
4. archive 뒤에는 active logbook에서 현재도 유효한 사실만 남겼는지 확인한다.
