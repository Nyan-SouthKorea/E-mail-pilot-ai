# Runtime

이 디렉토리는 공유 워크스페이스, 장시간 실행 조율, 상태 저장, 운영 workbook 재구성 계층 자리다.

비사소한 작업 전에는 항상 `../AGENTS.md -> ../README.md -> ../docs/logbook.md -> ../docs/feature_catalog.md -> ./README.md -> ./docs/logbook.md` 순서로 다시 읽는다.

현재 상태:

- 공유 워크스페이스 manifest `workspace.epa-workspace.json` 구조가 있다.
- `secure/secrets.enc.json`에 AES-GCM + scrypt 기반 암호화 secret 저장 경로가 있다.
- `state/state.sqlite`에 sync run, review state, dedupe, representative, override, workbook row 상태를 저장한다.
- `state/state.sqlite`에 feature run history도 함께 저장한다.
- `locks/write.lock` 기반 단일 작성자 잠금 경로가 있다.
- 기존 `mailbox / analysis / exports / llm` 엔진을 `workspace/profile` 기준으로 다시 묶는 sync service가 있다.
- sync service는 `빠른 테스트 동기화(최근 10건)`와 `전체 동기화(증분)` 두 실행 모드를 가진다.
- analysis 결과는 bundle fingerprint와 analysis revision이 같으면 기본적으로 재사용한다.
- 대표 신청 건만 stable 운영 workbook으로 다시 쓰고 `검토_인덱스` 시트를 추가하는 재구성 경로가 있다.
- `runtime/feature_registry.py`가 제품/운영 기능 카탈로그와 관리도구/CLI 실행 진입점을 같이 맡는다.
- `runtime/sample_workspace.py`가 repo-safe 샘플 세이브를 만든다.
- `runtime/feature_harness_smoke.py`가 sample workspace와 앱 UI를 묶어 반복 smoke를 수행한다.

현재 구현 방향:

- 공유 세이브는 Samba로 보이는 폴더 하나를 canonical root로 사용한다.
- 공유 save 안에는 절대경로를 저장하지 않고, bundle/로그/workbook 링크는 모두 워크스페이스 상대경로로 저장한다.
- 민감한 값은 공유 save 안에 두되 평문 파일이 아니라 암호화 blob에만 둔다.
- 동시 편집은 허용하지 않고 단일 작성자 잠금으로 간다.
- 사용자 override는 state DB에 저장하고, 다음 재반영 때도 유지되는 구조를 기본으로 둔다.
- 첫 동기화는 `quick_smoke`, 운영 동기화는 `incremental_full`을 기본 모드로 본다.
- 정적 HTML review board는 fallback/debug 산출물로 남기고, 사용자 검토의 active canonical 상태는 state DB와 앱 UI가 맡는다.

현재 참고 기준:

- [`../AGENTS.md`](../AGENTS.md)
- [`../README.md`](../README.md)
- [`../docs/logbook.md`](../docs/logbook.md)
- [`../docs/feature_catalog.md`](../docs/feature_catalog.md)
- [`./docs/logbook.md`](./docs/logbook.md)
