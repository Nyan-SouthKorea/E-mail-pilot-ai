# Exports Logbook

> 이 문서는 `exports` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 비사소한 작업 전에는 `../../AGENTS.md -> ../../README.md -> ../../docs/logbook.md -> ../../docs/feature_catalog.md -> ../README.md -> ./logbook.md` 순서로 다시 읽는다.
- 새 로그를 쓰기 전에는 가능하면 `python tools/logbook_archive_guard.py --path exports/docs/logbook.md --archive-if-needed`를 먼저 실행한다.

## 현재 스냅샷

- `TemplateProfile` 기반 템플릿 reader와 semantic mapping이 있다.
- rule-first exact/partial match와 unresolved header용 LLM fallback이 있다.
- `ExtractedRecord -> projected row -> workbook append` 경로가 있다.
- workbook diff는 품질 목표가 아니라 guardrail로만 사용한다.
- 현재 남은 핵심 과제는 템플릿 해석의 애매한 헤더와 projection 품질 차이를 더 줄이는 것이다.

## 현재 활성 체크리스트

- [x] 템플릿 reader와 semantic mapping 추가
- [x] rule-first + LLM fallback 절차 추가
- [x] workbook append와 스타일 상속 규칙 추가
- [x] regression guardrail 경로 추가
- [ ] 차이가 큰 필드 중심 projection 정밀화
- [ ] 실제 프로필 템플릿 변형 추가 수집
- [ ] repo-safe 비교 요약 산출물 기준 정리

## 최근 로그

### 2026-04-08 | Human + Codex | 모듈 logbook 체계 도입

- 프로젝트 전역 문서 체계가 바뀌면서 `exports`의 active 상태 문서를 이 파일로 분리했다.
- README는 템플릿 해석과 workbook append의 안정된 기준을 유지하고, 현재 차이 보정 작업은 여기서 관리한다.
