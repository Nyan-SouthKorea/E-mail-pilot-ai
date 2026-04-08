# Logbook Archive Summary

> 이 문서는 2026-04-08 문서 체계 재편 직전에 active였던 canonical 문서들의 핵심 사실을 한 곳에서 다시 읽기 위한 summary다.
> 원문 전문은 같은 디렉토리의 `260408_0956_legacy_*.md`, `logbook_260408_0956_legacy_recent_log.md` 파일에 보존했다.

## archive 대상

- `260408_0956_legacy_docs_agent.md`
- `260408_0956_legacy_docs_readme.md`
- `260408_0956_legacy_status.md`
- `260408_0956_legacy_decisions.md`
- `260408_0956_legacy_development_policy.md`
- `logbook_260408_0956_legacy_recent_log.md`

## legacy 체계에서 가져온 현재도 유효한 핵심 사실

- 문서 역할 분리 자체는 유지 가치가 높았다.
  - 당시에는 `docs/AGENT.md -> docs/README.md -> docs/status.md` 순서가 시작 게이트였다.
  - 이번 재편에서는 이 원칙을 유지하되, 게이트를 루트 `AGENTS.md -> README.md -> docs/logbook.md`로 단순화했다.
- 제품 주경로는 이미 `이메일 수신 -> 분석 -> Excel 출력`으로 고정돼 있었다.
- 데이터 계약은 `MailBundle -> NormalizedMessage -> ExtractedRecord -> ExportRow` 4층으로 정리돼 있었다.
- 메일 설정 탐지는 `rule/probe-first`, LLM 보조 fallback 기준이 이미 정리돼 있었다.
- reference fixture와 runtime 산출물을 분리하는 기준은 이미 맞는 방향이었다.
  - `../secrets/사용자 설정/<이름>/참고자료/`는 읽기 전용 reference
  - `../secrets/사용자 설정/<이름>/실행결과/`는 실제 runtime 메일/엑셀/로그
- 현재 코드 모듈 경계 `mailbox / analysis / exports / llm`는 유지 가치가 높았다.
- 이미지 첨부와 스캔 문서를 포함한 multimodal 입력을 기본 전제로 두는 판단도 유지했다.
- GUI는 엔진 smoke가 먼저 선 뒤에 감싼다는 순서도 유지했다.

## legacy 체계에서 이번에 바뀐 점

- `docs/status.md`, `docs/decisions.md`, `docs/개발방침.md`, `docs/logbook.md`로 흩어져 있던 active truth를 `docs/logbook.md` 하나로 모았다.
- 시작 문서를 `docs/AGENT.md`에서 루트 `AGENTS.md`로 올리고, `docs/README.md`는 없앴다.
- 모듈별 active 상태는 이제 각 `<module>/docs/logbook.md`에서 관리한다.
- repo-local skill, 운영 tool, starter template, sibling `../secrets/README.local.md`를 정식 운영 요소로 승격했다.

## 당시 다음 작업에서 그대로 이어받은 항목

- 실제 이메일 계정 기준 mailbox auth probe 실행
- 실제 inbox fetch smoke로 `MailBundle` 저장 경로 연결
- 분석 품질과 export 정규화 품질 개선
- GUI 시작 시 `app/`, 장시간 실행 조율 시작 시 `runtime/` 경계 구체화
