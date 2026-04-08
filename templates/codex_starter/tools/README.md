# Tools Starter Notes

이 디렉토리는 starter pack에 포함할 운영 도구의 사용 규약을 설명한다.

## 권장 도구

- `directory_inventory.py`
  - 새 파일이나 폴더를 만들기 전에 기존 구조를 점검한다.
- `logbook_archive_guard.py`
  - active logbook가 길어졌을 때 archive를 수행한다.
- `logbook_archive_all.py`
  - root와 모듈 logbook를 일괄 점검한다.
- `git_sync_all.sh`
  - 반복 git 동기화를 표준화한다.

## 권장 CLI 계약

- `python tools/directory_inventory.py --module <module> --kind <kind> --candidate-name <name>`
- `python tools/logbook_archive_guard.py --archive-if-needed`
- `python tools/logbook_archive_all.py --archive-if-needed`
- `tools/git_sync_all.sh "<commit message>" [--push]`
