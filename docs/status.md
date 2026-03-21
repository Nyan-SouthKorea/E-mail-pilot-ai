# Status

> 마지막 업데이트: 2026-03-21

## 현재 작업 모드

- `에이전트 모드`
- 의미:
  - 사용자가 자리를 비웠을 가능성을 기본 전제로, 문서에 기록된 목표와 규칙을 기준으로 스스로 이어서 진행한다.
  - 비사소한 작업 단위의 시작 게이트는 항상 `docs/AGENT.md`다.
  - 명시적인 중단 지시가 없는 한 이미 시작한 수집, 설계, 문서화, 실행 준비 작업을 끊지 않는다.
  - 새 단계 착수 전, 결과 정리 전, 후속 실행 시작 전에는 `docs/README.md`와 이 문서를 다시 읽고 기준을 맞춘다.

## 현재 목표

- 이메일 자동화 프로젝트의 운영 문서 체계와 모듈 구조를 먼저 고정한다.
- v1 전달 범위를 `이메일 수신 -> 분석 -> Excel 출력` 경로로 명확히 잡는다.
- reply draft / 자동 발송 / 외부 알림은 위 기본 경로가 실제로 선 뒤에 붙인다.
- mailbox provider, 내부 데이터 계약, Excel row schema, action policy를 순서대로 설계할 준비를 한다.

## 현재 고정 기준

- 문서 시작 게이트: `docs/AGENT.md -> docs/README.md -> docs/status.md`
- 현재 활성 모드: `에이전트 모드`
- 제품 기본 방향: `이메일 수신 -> 구조화 분석 -> Excel 출력`을 먼저 완성하고, 답장/알림은 다음 단계로 둔다.
- LLM 기본 방향: ChatGPT API 기반 structured output 우선
- 워크스페이스 기준: `repo / envs / results / secrets` sibling 구조를 지향
- 민감 정보 기준: 실제 메일 원문, 첨부파일, 계정 정보, API 키는 리포 밖 로컬 경로에서만 관리

## 모듈 상태

| 모듈 | 상태 | 메모 |
|---|---|---|
| Mailbox | 설계 전 | inbox sync, thread fetch, attachment ingestion 담당 |
| Analysis | 설계 전 | 분류, 추출, 요약, schema 정규화 담당 |
| Exports | 설계 전 | Excel row mapping, workbook update 담당 |
| LLM | 설계 전 | OpenAI client, prompt, structured response 담당 |

## 핵심 메모

- 현재 리포는 코드보다 운영 틀을 먼저 고정하는 초기 단계다.
- 레퍼런스 레포에서 가져온 핵심 철학은 아래다.
  - 문서 역할 분리
  - 시작 게이트 고정
  - status를 현재 상태의 단일 기준으로 유지
  - 장시간 작업의 detached 운영과 smoke-first
  - 과도한 추상화보다 주경로 우선
- 현재 제품 요구는 아직 넓게 열려 있으므로, provider와 세부 taxonomy를 성급히 고정하지 않는다.
- workflow, reply, notification 같은 후속 계층은 실제 구현이 시작될 때 디렉토리와 문서를 추가한다.
- 단, 답장 자동화는 안전성 때문에 기본적으로 `draft 우선` 기준을 유지한다.

## 다음 작업

1. mailbox provider 후보와 인증 방식을 정리한다.
2. 내부 데이터 계약을 `message / thread / extracted_record` 단위로 먼저 설계한다.
3. Excel 출력의 canonical row schema와 템플릿 전략을 정한다.
4. mailbox -> analysis -> exports 주경로의 첫 runnable smoke를 만든다.
5. 그 다음에만 reply draft와 notification 경계를 별도 층으로 분리한다.
