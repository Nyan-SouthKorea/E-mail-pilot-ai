# Analysis Logbook

> 이 문서는 `analysis` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 비사소한 작업 전에는 `../../AGENTS.md -> ../../README.md -> ../../docs/logbook.md -> ../README.md -> ./logbook.md` 순서로 다시 읽는다.
- 새 로그를 쓰기 전에는 가능하면 `python tools/logbook_archive_guard.py --path analysis/docs/logbook.md --archive-if-needed`를 먼저 실행한다.

## 현재 스냅샷

- `NormalizedMessage -> ExtractedRecord` structured output 경로가 있다.
- fixture 기반 live 분석 smoke와 materialized bundle live 분석 smoke가 있다.
- 이미지 첨부가 있으면 `input_text + input_image` 경로로 보내는 multimodal 입력 builder가 있다.
- extraction prompt와 schema는 `analysis/llm_extraction.py`에서 관리한다.
- 현재 남은 핵심 과제는 실제 inbox에서 들어온 bundle의 품질 편차를 흡수하는 정규화와 요약 품질 개선이다.

## 현재 활성 체크리스트

- [x] 분석 schema와 evidence 기반 결과 계약 고정
- [x] fixture live 분석 smoke 추가
- [x] materialized bundle live 분석 smoke 추가
- [x] multimodal 입력 builder 추가
- [ ] 실제 inbox 메일 기준 품질 편차 점검
- [ ] summary와 normalization 후처리 개선
- [ ] export 회귀 차이가 큰 필드 중심 개선

## 최근 로그

### 2026-04-08 | Human + Codex | 모듈 logbook 체계 도입

- 프로젝트 전역 문서 체계가 바뀌면서 `analysis`의 active 상태 문서를 이 파일로 분리했다.
- README는 안정된 입력/출력 계약과 역할 설명을 유지하고, 현재 작업과 다음 개선 과제는 여기서 관리한다.
