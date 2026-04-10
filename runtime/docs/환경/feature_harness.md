# Feature Harness

이 문서는 공유 워크스페이스 기준 기능 smoke와 샘플 세이브 반복 검증 절차를 적는다.

## 읽기 순서

- 비사소한 작업 전에는 `../../../AGENTS.md -> ../../../README.md -> ../../../docs/logbook.md -> ../../../docs/feature_catalog.md -> ../../README.md -> ../logbook.md -> ./feature_harness.md` 순서로 다시 읽는다.

## 현재 기준

- canonical 기능 카탈로그:
  - `docs/feature_catalog.md`
  - `runtime/feature_registry.py`
- 반복 검증 기본 세이브:
  - `runtime/sample_workspace.py`
- 관리도구/CLI 접근:
  - `python -m runtime.cli feature-list`
  - `python -m runtime.cli feature-check-all --workspace-root <path> --workspace-password <pw>`
  - `python -m runtime.cli feature-run --feature-id <id> --workspace-root <path> --workspace-password <pw>`

## 샘플 워크스페이스 생성

```bash
python -m runtime.cli create-sample-workspace \
  --workspace-root /path/to/sample_workspace \
  --workspace-password sample-pass
```

## 전체 smoke

```bash
python -m runtime.cli feature-harness-smoke \
  --workspace-root /path/to/sample_workspace \
  --workspace-password sample-pass \
  --create-sample-if-missing
```

- 이 smoke는 다음을 함께 확인한다.
  - feature prerequisite check 전량
  - workspace inspect run
  - operating workbook rebuild run
  - app UI smoke
- 결과 JSON은 workspace 상대경로 기준 `profile/실행결과/로그/runtime/` 아래에 남긴다.

## UI smoke 단독 실행

```bash
python -m app.ui_smoke \
  --workspace-root /path/to/sample_workspace \
  --workspace-password sample-pass
```

- 홈, 설정, 리뷰센터, 관리도구, background job polling, workbook 재반영 버튼까지 함께 점검한다.
