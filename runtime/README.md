# Runtime

이 디렉토리는 공유 워크스페이스, 장시간 실행 조율, 상태 저장, 운영 workbook 재구성 계층 자리다.

현재 상태:

- 공유 워크스페이스 manifest `workspace.epa-workspace.json` 구조가 있다.
- `secure/secrets.enc.json`에 AES-GCM + scrypt 기반 암호화 secret 저장 경로가 있다.
- `state/state.sqlite`에 sync run, review state, canonical selection, override, workbook row 상태를 저장한다.
- `state/state.sqlite`에 feature run history도 함께 저장한다.
- `locks/write.lock` 기반 단일 작성자 잠금 경로가 있다.
- 기존 `mailbox / analysis / exports / llm` 엔진을 `mail / exports / logs` 기준의 v2 세이브 구조로 다시 묶는 sync service가 있다.
- sync service는 `최근 10 / 100 / 500 / 1000 / 직접 입력 / 전체` 범위를 같은 service 계약으로 처리한다.
- analysis 결과는 bundle fingerprint와 analysis revision이 같으면 기본적으로 재사용한다.
- 자동 canonical selection으로 고른 운영 엑셀에 들어간 메일만 stable 운영 workbook으로 다시 쓰고 `검토_인덱스` 시트를 추가하는 재구성 경로가 있다.
- `runtime/feature_registry.py`가 제품/운영 기능 카탈로그와 관리도구/CLI 실행 진입점을 같이 맡는다.
- `runtime service`는 `workspace / settings / mailbox / analysis / exports / pipeline / diagnostics` 7개 그룹으로 나눈다.
- 명시적 CLI는 `workspace`, `settings`, `mailbox`, `analysis`, `exports`, `pipeline`, `diagnostics` 하위 명령을 지원한다.
- 리뷰 조회는 `analysis.review-list`와 `analysis.review-item` service/CLI로 분리해, GUI가 목록 1페이지와 선택한 상세만 따로 읽을 수 있게 한다.
- 엑셀 쪽은 `exports.summary`로 운영본/스냅샷/운영 엑셀에 들어간 메일 수를 따로 읽어, 앱 안에서 엑셀을 보조 결과물로 설명할 수 있게 한다.
- `runtime/sample_workspace.py`가 repo-safe 샘플 세이브를 만든다.
- `runtime/feature_harness_smoke.py`가 sample workspace와 앱 UI를 묶어 반복 smoke를 수행한다.
- 새 세이브는 legacy `profile/참고자료/실행결과` 구조를 만들지 않고, v1 세이브는 자동 변환하지 않는다.
- 이 PC 전용 암호화 저장소를 통해 마지막 세이브와 기본 API key 자동 채움을 지원한다.

현재 구현 방향:

- 공유 세이브는 Samba로 보이는 폴더 하나를 canonical root로 사용한다.
- 공유 save 안에는 절대경로를 저장하지 않고, bundle/로그/workbook 링크는 모두 워크스페이스 상대경로로 저장한다.
- 민감한 값은 공유 save 안에 두되 평문 파일이 아니라 암호화 blob에만 둔다.
- 동시 편집은 허용하지 않고 단일 작성자 잠금으로 간다.
- 사용자 override는 state DB에 저장하고, 다음 재반영 때도 유지되는 구조를 기본으로 둔다.
- 기본 UI에서는 `중복/대표 메일 지정`을 숨기고, 필요한 경우에만 고급 복구 경로로 canonical selection을 다시 평가한다.
- 첫 동기화는 작은 recent scope부터 시작하고, 마지막에 `all` scope로 넓혀 가는 흐름을 기본으로 본다.
- 정적 HTML review board는 fallback/debug 산출물로 남기고, 사용자 검토의 active canonical 상태는 state DB와 앱 UI가 맡는다.
- 새 세이브 canonical 구조는 `workspace.epa-workspace.json + secure/ + state/ + locks/ + mail/ + exports/ + logs/`를 기준으로 본다.
- 리뷰 화면이 커져도 GUI가 전체 항목을 한 번에 렌더링하지 않도록, 목록 조회는 `page / page_size / sort / selected_bundle_id / artifact_kind / view_mode` 계약으로 가볍게 유지한다.
- `view_mode=all_virtual`은 true full DOM 렌더가 아니라 브라우저가 필요한 줄부터 그리는 가상 스크롤 성격의 계약으로 유지한다.
- 기본 개발/검증 루프는 `service + CLI + web UI`를 먼저 닫고, 공식 exe는 최신 pushed `main` 기준 마지막에만 다시 패키징한다.

운영 규칙과 읽기 게이트는 root [`../AGENTS.md`](../AGENTS.md)를, 현재 모듈 상태는 [`./docs/logbook.md`](./docs/logbook.md)를 기준으로 본다.
