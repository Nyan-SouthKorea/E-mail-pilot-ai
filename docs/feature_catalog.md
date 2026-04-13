# Feature Catalog

> 이 문서는 현재 제품/운영 기능의 canonical 인덱스다.
> 코드 기준 registry는 `runtime/feature_registry.py`이고, GUI/CLI/service 계약은 이 문서와 함께 유지한다.

## 운영 원칙

- 비사소한 변경은 항상 `AGENTS.md -> README.md -> docs/logbook.md -> docs/feature_catalog.md` 순서로 다시 읽는다.
- 기능을 새로 추가하거나 기존 동작을 바꾸면 같은 턴에 이 문서를 함께 갱신한다.
- GUI는 제품용 wrapper고, 공용 실행 진실은 `runtime service + 명시적 CLI`다.
- 자동 검증 가능한 기능은 CLI/service smoke로 확인하고, Windows 수동 acceptance가 필요한 항목은 별도로 표시한다.
- 완료 보고 전에는 반드시 `source 반영 -> CLI/service 검증 -> 공식 exe 반영 -> 수동 acceptance 필요 항목 분리` 4단을 확인한다.

## 현재 변경 검증 4단

| 단계 | 의미 | 완료 기준 |
|---|---|---|
| `source 반영` | repo 소스와 canonical 문서가 최신 요구를 반영함 | 코드 + `README/logbook/feature_catalog` 동시 갱신 |
| `CLI/service 검증` | GUI 없이도 핵심 기능이 공용 service와 명시적 CLI로 재현됨 | `runtime.cli`, `feature-harness-smoke`, 관련 smoke 통과 |
| `공식 exe 반영` | Windows 공식 실행본이 현재 source commit 기준으로 다시 빌드됨 | 공식 exe 재빌드 + packaged smoke 통과 |
| `수동 acceptance` | 자동화하기 어려운 Windows 셸/네이티브 UI가 실제로 보이는지 최종 확인 | 파일 탐색기 dialog, exe 아이콘/창 브랜딩 등 사용자 눈검증 |

## 제품 핵심 기능

| feature_id | 제목 | UI | CLI | service_entry | 저장/출력 위치 | 검증 방식 |
|---|---|---|---|---|---|---|
| `workspace.create` | 새 세이브 만들기 | `/` | `python -m runtime.cli workspace create ...` | `runtime.workspace_service:create_workspace_entry` | `workspace.epa-workspace.json`, `secure/`, `state/`, `mail/`, `exports/`, `logs/` | smoke-safe |
| `workspace.open` | 기존 세이브 열기 | `/` | `python -m runtime.cli workspace open ...` | `runtime.workspace_service:open_workspace_entry` | 현재 세션, 로컬 최근 세이브 목록 | smoke-safe |
| `workspace.close` | 세이브 닫기 | `/workspace/close` | `python -m runtime.cli workspace close ...` | `runtime.workspace_service:close_workspace_entry` | 로컬 최근 세이브/자동 재개 정보 | smoke-safe |
| `workspace.status` | 세이브 상태 점검 | `관리도구` | `python -m runtime.cli workspace status ...` | `runtime.workspace_service:inspect_workspace_entry` | `state/state.sqlite`, `secure/secrets.enc.json` 요약 | smoke-safe |
| `workspace.recent` | 최근 세이브 목록 | `/` | `python -m runtime.cli workspace recent` | `runtime.workspace_service:list_recent_workspaces` | 로컬 설정 저장소 | smoke-safe |
| `settings.show` | 현재 설정 읽기 | `/settings` | `python -m runtime.cli settings show ...` | `runtime.settings_service:load_workspace_settings_summary` | masked settings summary | smoke-safe |
| `settings.save` | 설정 저장 | `/settings` | `python -m runtime.cli settings save ...` | `runtime.settings_service:save_workspace_settings` | `secure/secrets.enc.json`, 로컬 기본 API key | smoke-safe |
| `mailbox.connect_check` | 계정 연결 확인 | `/settings` | `python -m runtime.cli mailbox connect-check ...` | `runtime.mailbox_service:run_mailbox_connection_check_service` | mailbox status, 추천 받은편지함, 폴더 목록 | live-required |
| `mailbox.fetch` | 메일 가져오기 | `/sync` | `python -m runtime.cli mailbox fetch ... --limit N|--all` | `runtime.mailbox_service:run_mailbox_fetch_service` | `mail/bundles/`, `logs/mailbox/` | live-required |
| `analysis.review_refresh` | 리뷰/분석 재생성 | `/review`, `관리도구` | `python -m runtime.cli analysis review-refresh ... --limit N|--all` | `runtime.analysis_service:refresh_review_board_service` | `logs/review/`, `state/state.sqlite` | smoke-safe, live-optional |
| `analysis.review_list` | 리뷰 목록 조회 | `/review` | `python -m runtime.cli analysis review-list ... --page 1 --page-size 50 --sort received_desc` | `runtime.analysis_service:load_review_center_page_service` | `state/state.sqlite` 읽기 | smoke-safe |
| `analysis.review_item` | 리뷰 상세 조회 | `/review` | `python -m runtime.cli analysis review-item ... --bundle-id <id>` | `runtime.analysis_service:load_review_detail_service` | `state/state.sqlite`, `mail/bundles/`, `logs/analysis/` 읽기 | smoke-safe |
| `exports.rebuild` | 운영 엑셀 재반영 | `/review` | `python -m runtime.cli exports rebuild ...` | `runtime.exports_service:rebuild_operating_workbook_service` | `exports/output/operating_workbook.xlsx`, `exports/output/snapshots/` | smoke-safe |
| `exports.summary` | 엑셀 반영 요약 | `/review` | `python -m runtime.cli exports summary ...` | `runtime.exports_service:load_exports_summary_service` | `exports/output/`, `state/state.sqlite` 읽기 | smoke-safe |
| `pipeline.sync.recent` | 최근 N건 동기화 | `/sync` | `python -m runtime.cli pipeline sync ... --scope recent --limit N` | `runtime.pipeline_service:run_pipeline_sync_service` | fetch/report/review/workbook 종합 결과 | live-required |
| `pipeline.sync.all` | 전체 동기화 | `/sync` | `python -m runtime.cli pipeline sync ... --all` | `runtime.pipeline_service:run_pipeline_sync_service` | fetch/report/review/workbook 종합 결과 | live-required |
| `diagnostics.picker_bridge` | 파일 탐색기 진단 | `/`, `/settings` | `python -m runtime.cli diagnostics picker-bridge` | `runtime.diagnostics_service:picker_bridge_self_test` | diagnostics payload only | smoke-safe |
| `diagnostics.pick_folder` | 폴더 선택 호출 | `찾아보기` 버튼 | `python -m runtime.cli diagnostics pick-folder ...` | `runtime.diagnostics_service:pick_folder_native` | 선택 경로 결과 | smoke-safe with test override, manual acceptance on Windows |
| `diagnostics.pick_file` | 파일 선택 호출 | `엑셀 양식 찾아보기` | `python -m runtime.cli diagnostics pick-file ...` | `runtime.diagnostics_service:pick_file_native` | 선택 경로 결과 | smoke-safe with test override, manual acceptance on Windows |
| `app.meta` | 앱 정체성 확인 | 내부 diagnostics | `GET /app-meta` | `app.server:app_meta` | app id, version, shell mode | smoke-safe |

## 운영/검증 기능

| feature_id | 제목 | 접근 | CLI | service_entry / 코드 기준 | 검증 방식 |
|---|---|---|---|---|---|
| `runtime.workspace.create_sample` | 샘플 세이브 생성 | CLI | `python -m runtime.cli create-sample-workspace ...` | `runtime.sample_workspace:create_sample_workspace` | smoke-safe |
| `runtime.feature.check_all` | feature prerequisite 전량 점검 | CLI, 관리도구 | `python -m runtime.cli feature-check-all ...` | `runtime.feature_registry:check_feature` | smoke-safe |
| `runtime.feature.harness_smoke` | 전기능 smoke 하네스 | CLI | `python -m runtime.cli feature-harness-smoke ...` | `runtime.feature_harness_smoke:run_feature_harness_smoke` | smoke-safe |
| `app.ui_smoke` | 앱 UI 반복 smoke | CLI | `python -m app.ui_smoke ...` | `app.ui_smoke:run_app_ui_smoke` | smoke-safe |
| `packaging.portable_exe.build` | Windows 포터블 exe 빌드 | 문서, 관리도구, CLI | `bash app/packaging/build_windows_portable_and_publish.sh --clean` | `app/packaging/*` | Windows host required, pushed Git required |
| `app.desktop.launch` | 데스크톱 앱 실행 | exe, CLI | `python app/main.py` | `app.main:main` | manual acceptance 포함 |

## 동기화 범위 계약

- GUI preset:
  - `최근 10건`
  - `최근 100건`
  - `최근 500건`
  - `최근 1000건`
  - `직접 입력`
  - `전체`
- CLI 계약:
  - `python -m runtime.cli pipeline sync --workspace-root <path> --workspace-password <pw> --scope recent --limit 10`
  - `python -m runtime.cli pipeline sync --workspace-root <path> --workspace-password <pw> --scope recent --limit 500`
  - `python -m runtime.cli pipeline sync --workspace-root <path> --workspace-password <pw> --all`
- 동작 기준:
  - 이미 fetch한 UID는 다시 가져오지 않는다.
  - 같은 bundle fingerprint + `analysis_revision`이면 분석 결과를 재사용한다.
  - fetch만 성공하고 후속 단계가 실패하면 `partial_success`로 남긴다.

## 리뷰센터 계약

- 기본 구조:
  - `페이지 기반 목록 + 우측 상세패널`
  - 기본 페이지 크기 `50`, 옵션 `25 / 50 / 100`
- 목록 조회 입력:
  - `search`
  - `triage_label`
  - `export_only`
  - `page`
  - `page_size`
  - `sort`
  - `selected_bundle_id`
- 정렬 옵션:
  - `received_desc`
  - `company_asc`
  - `sender_asc`
- 사용자 노출 용어:
  - `대표 export만` -> `엑셀 반영 대상만`
  - `preview` -> `메일 미리보기`
  - `raw.eml` -> `원본 메일 파일`
  - `summary` -> `요약 메모`
  - `record` -> `추출 결과 원본`
  - `projected` -> `엑셀 반영 미리보기`
  - `attachments` -> `첨부파일 폴더`
- 상태 유지 기준:
  - 필터, 현재 페이지, 정렬, 선택 항목은 URL query와 로컬 설정 둘 다에 저장한다.
  - 외부 파일 열기 뒤에도 같은 리뷰 상태로 돌아와야 한다.
- 자동 canonical selection 기준:
  - 사용자 화면에는 `중복` 열과 `대표 메일 지정` 액션을 두지 않는다.
  - 내부적으로는 `application_group_id`, `canonical_bundle_id`, `included_in_export`, `canonical_selection_reason`, `canonical_selection_confidence`를 저장한다.
  - 기본 UI에는 `엑셀 반영됨 / 보류 / 검토 필요`만 노출하고, 필요할 때만 고급 복구 경로를 사용한다.

## 엑셀 역할 계약

- 앱이 검토의 정본이고, 엑셀은 외부 전달/참고용 보조 산출물이다.
- 앱 안에서는 아래를 분리해 설명한다.
  - `기본 양식`
  - `현재 운영본`
  - `스냅샷`
- `엑셀 반영 대상만`은 같은 신청 흐름 안에서 자동 canonical selection을 거쳐 실제 운영 엑셀에 포함되는 메일만 뜻한다.

## 저장 위치 계약

- 세이브 내부 canonical 구조:
  - `workspace.epa-workspace.json`
  - `secure/secrets.enc.json`
  - `state/state.sqlite`
  - `locks/write.lock`
  - `mail/bundles/`
  - `exports/template/export_template.xlsx`
  - `exports/output/operating_workbook.xlsx`
  - `exports/output/snapshots/`
  - `logs/app/`
  - `logs/mailbox/`
  - `logs/analysis/`
  - `logs/review/`
  - `logs/llm/`
- 더 이상 새 세이브에서 만들지 않는 legacy 구조:
  - `profile/`
  - `참고자료/`
  - `실행결과/`
  - `기대되는 산출물/`

## 검증 계약

- smoke-safe 자동 검증:
  - 세이브 생성/열기/닫기/최근 세이브
  - 설정 저장/읽기
  - picker diagnostics + picker route test override
  - review refresh
  - workbook rebuild
  - UI smoke
  - feature harness smoke
- live-required 검증:
  - 실제 계정 연결 확인
  - 실제 메일 fetch
  - 실제 OpenAI 호출
  - 실제 recent N / all sync
- Windows 수동 acceptance 2개:
  - `찾아보기`를 눌렀을 때 실제 폴더/파일 선택창이 뜨는지
  - exe 아이콘/창 브랜딩이 새 기준대로 보이는지
- Windows 빌드 전제:
  - `build_windows_portable_and_publish.sh`는 GitHub 기준 mirror sync를 쓰므로, dirty working tree 또는 미push HEAD 상태에서는 빌드를 거부한다.
  - launcher는 고정 포트가 점유돼 있으면 다른 로컬 포트를 자동 선택하고, `/app-meta`로 실제 Email Pilot AI 서버인지 확인한 뒤 창을 연다.
  - packaged smoke는 `/app-meta`의 `build_commit`, `build_time`, `official_exe_path`가 현재 repo HEAD와 공식 exe 경로를 가리키는지도 함께 확인해야 한다.

## 반복 검증 명령

- 기능 목록:
  - `python -m runtime.cli feature-list`
- 세이브 상태:
  - `python -m runtime.cli workspace status --workspace-root <path> --workspace-password <pw>`
- 설정 요약:
  - `python -m runtime.cli settings show --workspace-root <path> --workspace-password <pw>`
- picker 진단:
  - `python -m runtime.cli diagnostics picker-bridge`
- picker route smoke:
  - `EPA_PICKER_TEST_RESPONSE=<path> python -m runtime.cli diagnostics pick-folder --workspace-root <path>`
- 리뷰 재생성:
  - `python -m runtime.cli analysis review-refresh --workspace-root <path> --workspace-password <pw> --limit 10`
- 리뷰 목록 1페이지:
  - `python -m runtime.cli analysis review-list --workspace-root <path> --page 1 --page-size 50 --sort received_desc`
- 리뷰 상세 1건:
  - `python -m runtime.cli analysis review-item --workspace-root <path> --bundle-id <bundle_id>`
- 엑셀 재반영:
  - `python -m runtime.cli exports rebuild --workspace-root <path> --workspace-password <pw>`
- 엑셀 요약:
  - `python -m runtime.cli exports summary --workspace-root <path>`
- 전체 smoke:
  - `EPA_PICKER_TEST_RESPONSE=<path> python -m runtime.cli feature-harness-smoke --workspace-root <path> --workspace-password <pw> --create-sample-if-missing`
