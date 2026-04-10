# App

이 디렉토리는 Windows exe/installer에서 열릴 전용 데스크톱 창과 로컬 Web UI 진입점 자리다.

비사소한 작업 전에는 항상 `../AGENTS.md -> ../README.md -> ../docs/logbook.md -> ../docs/feature_catalog.md -> ./README.md -> ./docs/logbook.md` 순서로 다시 읽는다.

현재 상태:

- FastAPI 기반 로컬 UI 서버가 있다.
- `세이브 파일 불러오기`, `새 세이브 파일 만들기`, `설정`, `동기화`, `리뷰`, `고급 도구` 화면이 있다.
- 세이브 파일과 템플릿 경로는 Windows exe에서 `찾아보기` 버튼으로 고를 수 있고, 브리지가 `desktop_ready`일 때만 버튼이 활성화된다.
- 홈 화면은 서비스형 온보딩 대시보드이고, `세이브 파일 가이드`는 별도 페이지 대신 모달로 먼저 보여준다.
- 홈은 `세이브 파일 -> 계정 연결 -> 빠른 테스트 동기화 -> 전체 동기화 -> 리뷰` 흐름을 기준으로 다음 행동을 안내한다.
- `관리도구` 화면에서 feature 카탈로그, prerequisite check, 최근 실행 결과, 직접 실행 버튼을 본다.
- pywebview launcher가 있고, 전용 창 연결이 준비되기 전에는 `브라우저 fallback`으로 단정하지 않고 `앱 전용 창 연결 확인 중` 상태를 먼저 보여준다.
- 설정 화면은 기본/고급으로 나뉘고, 기본 설정만으로 계정 연결 확인과 빠른 테스트 동기화를 시작할 수 있게 한다.
- 리뷰센터는 sqlite state DB 기준으로 메일 목록, 분류, 대표 export 상태, 원본 링크, override를 카드형 확장 리스트로 보여준다.
- 오프라인 포터블 exe를 위해 프런트 자산은 `app/static/` 로컬 자산 기준으로 제공한다.
- `app/ui_smoke.py`로 홈, 설정, 리뷰센터, 관리도구, 재반영 버튼까지 반복 검증할 수 있다.
- Windows 포터블 exe 빌드 기준은 `app/packaging/` 문서와 스크립트에 정리한다.
- Windows build는 `D:\\EmailPilotAI\\repo`에서 수행하되, 최종 사용자 실행본은 `D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe` 하나로 publish 한다.
- `Z:` 공유 폴더의 exe, repo 내부 `dist/` 임시 산출물, 임의 수동 복사 폴더는 공식 실행 경로로 보지 않는다.

현재 구현 방향:

- 최종 사용자에게는 브라우저 탭이 아니라 전용 앱 창을 보여준다.
- 최종 사용자 실행 기준은 Windows에서 `EmailPilotAI.exe`를 더블클릭하는 단일 경로다.
- 다만 실행 파일 위치와 세이브 파일 연결은 분리한다. 실행 파일은 항상 Windows 로컬 D 경로에서 열고, 세이브 파일은 공유 폴더의 같은 workspace를 열어 동일 상태를 본다.
- 내부 UI는 Web UI로 렌더링하되, Node/React 빌드 체인은 v1에 넣지 않는다.
- 앱 내부 설명은 짧게 유지하고, 자세한 사용자 개념 설명은 `docs/환경/first_user_save_file_guide.md` 같은 외부 안내 문서로 분리한다.
- 동기화는 `빠른 테스트`와 `전체 동기화` 두 흐름으로 나누고, quick smoke를 기본 첫 진입점으로 둔다.
- workbook과 원본 메일 검토의 canonical 상태는 runtime state DB와 workspace 상대경로 링크를 기준으로 본다.

현재 참고 기준:

- [`../AGENTS.md`](../AGENTS.md)
- [`../README.md`](../README.md)
- [`../docs/logbook.md`](../docs/logbook.md)
- [`../docs/feature_catalog.md`](../docs/feature_catalog.md)
- [`./docs/logbook.md`](./docs/logbook.md)
