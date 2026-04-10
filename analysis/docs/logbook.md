# Analysis Logbook

> 이 문서는 `analysis` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 작업 시작 게이트와 읽기 순서는 root `AGENTS.md`를 따른다.
- 새 로그를 쓰기 전에는 가능하면 `python tools/logbook_archive_guard.py --path analysis/docs/logbook.md --archive-if-needed`를 먼저 실행한다.

## 현재 스냅샷

- `NormalizedMessage -> ExtractedRecord` structured output 경로가 있다.
- fixture 기반 live 분석 smoke와 materialized bundle live 분석 smoke가 있다.
- 이미지 첨부가 있으면 `input_text + input_image` 경로로 보내는 multimodal 입력 builder가 있다.
- extraction prompt와 schema는 `analysis/llm_extraction.py`에서 관리한다.
- real bundle 1건에 대해 analysis -> exports handoff를 실제로 검증했다.
- real bundle 품질 회귀는 `real_bundle_quality_smoke.py`로 점검한다.
- 전체 bundle에 대해 `application / not_application / needs_human_review` triage와 HTML review board 생성 경로가 있다.
- 현재 남은 핵심 과제는 triage 품질을 더 많은 real bundle에 대해 안정화하고, runtime/app의 override 재반영 경험을 매끄럽게 만드는 것이다.

## 현재 활성 체크리스트

- [x] 분석 schema와 evidence 기반 결과 계약 고정
- [x] fixture live 분석 smoke 추가
- [x] materialized bundle live 분석 smoke 추가
- [x] multimodal 입력 builder 추가
- [x] 실제 inbox 메일 기준 품질 편차 점검
- [x] real bundle 1건 기준 summary와 normalization 후처리 개선
- [x] export 회귀 차이가 큰 필드와 unresolved 컬럼 중심 개선
- [x] real-bundle quality smoke 추가
- [x] 전체 bundle 3-way triage 추가
- [x] HTML review board와 application-only batch export 추가
- [ ] real bundle 2건 이상으로 품질 회귀 기준 확대

## 최근 로그

### 2026-04-08 | Human + Codex | runtime/app 공유 save 경로에 review state handoff 연결

- static HTML review board를 그대로 버리지 않고 fallback/debug 산출물로 유지하되, 사용자 검토의 active canonical 상태는 `runtime` sqlite state와 `app` 리뷰센터가 읽는 형태로 정리했다.
- 이후 analysis 배치 결과는 review JSON을 통해 `runtime` state DB로 ingest되어 dedupe와 운영 workbook 재구성의 입력이 된다.

### 2026-04-08 | Human + Codex | 전체 bundle triage와 HTML review board 추가

- `ExtractedRecord`에 triage top-level 필드를 추가하고, extraction prompt와 후처리가 `application / not_application / needs_human_review` 3분류를 항상 채우도록 맞췄다.
- `inbox_review_board_smoke.py`를 추가해 전체 valid runtime bundle을 재분석하고 projected row를 만든 뒤, 신청서만 workbook에 반영하고 HTML/JSON review board를 남기게 했다.
- export gate는 triage가 `application`이면서 기업명과 연락처 신호가 함께 있을 때만 통과하도록 고정했다.
- full runtime corpus `4692`건 기준 latest review board 결과는 `application=155`, `not_application=4526`, `needs_human_review=11`, `exported=153`, `failed=0`이었다.
- latest full-run 산출물은 sibling runtime 경로의 `260408_1505_inbox_review_board.html`, `260408_1505_inbox_review_board.json`, `260408_1505_기업_신청서_모음.xlsx`다.
- prefilter 결과 internal sender가 `application`으로 잘못 분류된 케이스는 없었고, 실제 신청/지원/참가신청 제목과 회신 메일이 주된 export 후보로 남았다.
- ZIP 내부 손상 XLSX는 요약 fallback 텍스트로 넘기고, HEIC 같은 unsupported image는 vision 입력에서 제외해 batch 전체 실패 없이 끝나도록 안정화했다.

### 2026-04-08 | Human + Codex | real bundle 품질 보정과 quality smoke 추가

- 전시회/안내형 메일에서도 workbook용 업무형 필드가 비지 않도록 prompt와 후처리를 보강했다.
- 현재 baseline real bundle에서는 `company_name`, `product_or_service`, `application_purpose`, `request_summary`가 모두 채워졌고 projected row의 unresolved 컬럼도 0개가 됐다.
- `real_bundle_quality_smoke.py`를 추가해 같은 bundle에 대해 expected semantic key, unresolved 컬럼, summary 존재 여부를 한 번에 확인할 수 있게 했다.

### 2026-04-08 | Human + Codex | real bundle 1건 handoff 검증

- 최신 real bundle 1건으로 materialized bundle analysis smoke를 실행해 runtime `extracted_record.json` 생성을 확인했다.
- 같은 bundle로 pipeline smoke를 이어 실행해 runtime `projected_row.json`과 새 workbook append 결과를 확인했다.
- 직접 CLI 실행 시 relative import로 막히던 `materialized_bundle_smoke.py` 진입 문제를 함께 정리했다.
- 이번 real bundle에서는 연락처, 이메일, 홈페이지, 산업군, 소개/사업내용 요약은 채워졌지만 `company_name`, `product_or_service`, `application_purpose`, `request_summary`는 unresolved 상태로 남았다.

### 2026-04-08 | Human + Codex | 모듈 logbook 체계 도입

- 프로젝트 전역 문서 체계가 바뀌면서 `analysis`의 active 상태 문서를 이 파일로 분리했다.
- README는 안정된 입력/출력 계약과 역할 설명을 유지하고, 현재 작업과 다음 개선 과제는 여기서 관리한다.
