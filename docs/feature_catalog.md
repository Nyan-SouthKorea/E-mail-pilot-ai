# Feature Catalog

> 이 문서는 현재 제품/운영 기능의 canonical 카탈로그다.
> 세부 runtime registry의 코드 기준은 `runtime/feature_registry.py`이고, 이 문서는 사람이 빠르게 읽는 인덱스 역할을 맡는다.

## 읽기 위치

- 비사소한 작업에서는 `AGENTS.md -> README.md -> docs/logbook.md -> docs/feature_catalog.md` 순서로 읽는다.
- 새 기능 추가나 리팩토링은 이 문서와 `runtime/feature_registry.py`가 함께 갱신되어야 완료로 본다.

## 현재 기준

| feature_id | 제목 | 소유 모듈 | 접근 | 핵심 출력 |
|---|---|---|---|---|
| `app.desktop.launch` | 데스크톱 앱 실행 | `app` | UI, CLI | 전용 창, 파일 탐색기 브리지, 실행 진단 |
| `runtime.workspace.create_sample` | 샘플 워크스페이스 생성 | `runtime` | CLI | repo-safe sample save, review board, workbook |
| `runtime.workspace.inspect` | 워크스페이스 점검 | `runtime` | 관리도구, CLI | manifest/state/settings 요약 |
| `mailbox.live_backfill` | 실메일 INBOX backfill | `mailbox` | 관리도구, CLI | mailbox report, runtime bundles |
| `analysis.review_board_refresh` | 리뷰보드 재생성 | `analysis` | 관리도구, CLI | review JSON/HTML, sqlite review state |
| `exports.operating_workbook.rebuild` | 운영 workbook 재반영 | `exports` | UI, 관리도구, CLI | 운영 workbook, 검토 인덱스 |
| `runtime.workspace.sync` | 전체 동기화 | `runtime` | UI, 관리도구, CLI | backfill + review board + workbook |
| `packaging.portable_exe.build` | 포터블 exe 빌드 | `app` | 관리도구, CLI, 문서 | Windows onedir bundle, D 로컬 publish runtime, bundle manifest |

## 기능 접근 원칙

- 사용자 핵심 흐름은 UI에서 접근한다.
  - `세이브 파일 불러오기`
  - `세이브 파일 가이드`
  - `설정`
  - `동기화`
  - `통합 리뷰센터`
  - `운영 workbook 재반영`
- 세부 smoke/debug 기능은 관리도구와 CLI에서 접근한다.
  - `실메일 backfill`
  - `review board 재생성`
  - `workspace 점검`
  - `샘플 워크스페이스 생성`
  - `포터블 exe 빌드`
- 기능 실행 이력은 공유 워크스페이스 `state/state.sqlite`의 `feature_runs`를 기준으로 남긴다.

## 반복 검증 명령

- feature 카탈로그 목록:
  - `python -m runtime.cli feature-list`
- feature prerequisite 전량 점검:
  - `python -m runtime.cli feature-check-all --workspace-root <path> --workspace-password <pw>`
- feature 단건 실행:
  - `python -m runtime.cli feature-run --feature-id <id> --workspace-root <path> --workspace-password <pw>`
- 샘플 워크스페이스 기반 전체 smoke:
  - `python -m runtime.cli feature-harness-smoke --workspace-root <path> --workspace-password <pw> --create-sample-if-missing`
- 앱 UI smoke:
  - `python -m app.ui_smoke --workspace-root <path> --workspace-password <pw>`

## 테스트 기준

- 모든 기능은 최소 하나의 실제 접근점이 있어야 한다.
  - UI 경로
  - 관리도구 경로
  - CLI 명령
- 모든 기능은 최소 하나의 결과 위치 또는 상태 저장 위치가 있어야 한다.
- 구현은 있는데 카탈로그에 없는 기능, 카탈로그는 있는데 실행 진입점이 없는 기능은 허용하지 않는다.
- 샘플 워크스페이스만으로 재현 가능한 기능과 실메일/API key가 필요한 live 기능을 구분해 적는다.

## 샘플 워크스페이스 기준

- 샘플 세이브는 실메일과 비밀값 없이도 리뷰센터, dedupe, workbook 재반영, 관리도구 동작을 검증하는 기본 fixture다.
- live 의존 기능은 아래처럼 명시한다.
  - `mailbox.live_backfill`: 실메일 credential 필요
  - `analysis.review_board_refresh`: OpenAI API key 필요
  - `runtime.workspace.sync`: 실메일 credential + OpenAI API key 필요
- Windows 포터블 exe는 아래 중 하나로 검증한다.
  - Windows host에서 `packaging.portable_exe.build` 실행
  - A100에서 `bash ./app/packaging/build_windows_portable_and_publish.sh` 실행
- 공식 실행 경로는 `D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe` 하나다.
- `Z:` 공유 폴더의 exe, repo 내부 `dist/` 임시 산출물, 임의 수동 복사 폴더는 공식 지원 경로가 아니다.
