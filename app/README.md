# App

이 디렉토리는 Windows exe/installer에서 열릴 전용 데스크톱 창과 로컬 Web UI 진입점 자리다.

비사소한 작업 전에는 항상 `../AGENTS.md -> ../README.md -> ../docs/logbook.md -> ./README.md -> ./docs/logbook.md` 순서로 다시 읽는다.

현재 상태:

- FastAPI 기반 로컬 UI 서버가 있다.
- `세이브 파일 불러오기`, `새 워크스페이스 만들기`, `설정`, `통합 리뷰센터`, `동기화` 화면 골격이 있다.
- pywebview launcher가 있고, pywebview 사용이 안 되는 환경에서는 로컬 브라우저 fallback으로 열린다.
- 설정 화면은 공유 저장과 로컬 저장, 암호화 저장의 경계를 같이 안내한다.
- 리뷰센터는 sqlite state DB 기준으로 메일 목록, 분류, 대표 export 상태, 원본 링크를 보여준다.

현재 구현 방향:

- 최종 사용자에게는 브라우저 탭이 아니라 전용 앱 창을 보여준다.
- 내부 UI는 Web UI로 렌더링하되, Node/React 빌드 체인은 v1에 넣지 않는다.
- 설정, 세이브 불러오기, 리뷰센터, 동기화는 같은 창 안에서 이어지게 한다.
- workbook과 원본 메일 검토의 canonical 상태는 runtime state DB와 workspace 상대경로 링크를 기준으로 본다.

현재 참고 기준:

- [`../AGENTS.md`](../AGENTS.md)
- [`../README.md`](../README.md)
- [`../docs/logbook.md`](../docs/logbook.md)
- [`./docs/logbook.md`](./docs/logbook.md)
