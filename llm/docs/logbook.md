# LLM Logbook

> 이 문서는 `llm` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 비사소한 작업 전에는 `../../AGENTS.md -> ../../README.md -> ../../docs/logbook.md -> ../README.md -> ./logbook.md` 순서로 다시 읽는다.
- 새 로그를 쓰기 전에는 가능하면 `python tools/logbook_archive_guard.py --path llm/docs/logbook.md --archive-if-needed`를 먼저 실행한다.

## 현재 스냅샷

- OpenAI Responses wrapper가 있다.
- usage token과 가격표 snapshot 기반 비용 추정이 있다.
- usage log는 JSONL로 남긴다.
- 실제 prompt와 schema는 작업 소유 모듈 옆에서 관리하고, `llm`은 transport와 logging에 집중한다.
- 현재 남은 핵심 과제는 프로필 없는 일회성 실험 fallback 경로와 호출 실패 관측성을 더 정리하는 것이다.

## 현재 활성 체크리스트

- [x] 공용 wrapper 추가
- [x] usage log와 비용 추정 추가
- [x] analysis/export용 structured output transport 연결
- [ ] 실패 유형별 logging 보강
- [ ] 프로필 없는 실험 경로의 fallback 정리
- [ ] 장시간 batch run에서의 usage 요약 방식 정리

## 최근 로그

### 2026-04-08 | Human + Codex | 모듈 logbook 체계 도입

- 프로젝트 전역 문서 체계가 바뀌면서 `llm`의 active 상태 문서를 이 파일로 분리했다.
- README는 공용 wrapper와 logging 책임을 설명하고, 실제 운영 중 보강할 관찰 포인트는 여기서 관리한다.
