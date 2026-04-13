# AGENTS

> 이 문서는 새 저장소에서 운영 규칙의 단일 기준으로 쓰는 starter template이다.

## 역할

- 운영 규칙, 작업 시작점, 검증 기준, 문서 역할 분리를 다룬다.
- 현재 상태는 `docs/logbook.md`, 프로젝트 소개와 구조는 `README.md`, 모듈 상세 기준은 각 모듈 `README.md`가 맡는다.

## 항상 읽는 순서

1. `AGENTS.md`
2. `README.md`
3. `docs/logbook.md`
4. `docs/feature_catalog.md`
5. 최신 `docs/logbook_archive/logbook_*.md` 1개
6. 관련 모듈 `README.md`
7. 관련 모듈 `docs/logbook.md`

## 재독 게이트

- 새 작업 시작, 단계 전환, 문서 구조 변경, 커밋 전, 푸시 전, 후속 실행 전에는 이 읽는 순서를 다시 통과한다.
- `/plan` 또는 그에 준하는 계획 수립을 시작할 때도 먼저 다시 읽는다.
- 새 plan을 실제 작업으로 받기 전에는 이전 active plan의 publish 상태를 먼저 확인한다.
- 계획에서 실제 구현이나 실행으로 넘어가기 직전에도 다시 읽는다.
- 완료 응답, 커밋, 푸시, 마감 정리를 시작하기 직전에도 다시 읽는다.

## 기본 원칙

- 같은 내용을 여러 상위 문서에 반복하지 않는다.
- active truth는 logbook에, stable truth는 README에 둔다.
- 승인된 상위 plan이 생기면 구현 전에 root `docs/logbook.md`의 `현재 실행 계획`에 전문을 먼저 반영한다.
- 구현은 `현재 체크포인트`와 `현재 활성 체크리스트`를 작은 작업 단위로 갱신하면서 진행한다.
- plan 마감의 기본 완료 조건은 `canonical 문서 반영 -> commit -> push -> clean status 확인`이다.
- 민감 정보와 실제 운영 자산은 tracked repo 밖 local 문서와 local 경로에서 관리한다.
- 새 기능 배치 기준은 root `README.md`에 둔다.
- 미래 상위 계층은 이름만 먼저 정하지 말고, 실제 코드가 처음 들어가는 턴에 `README.md`와 `docs/logbook.md`를 함께 만든다.
- 완료 보고 전에는 이번 턴에 `AGENTS.md`를 몇 번, 어느 게이트에서 읽었는지 간단한 재독 기록을 남긴다.
- 공식 exe가 있는 작업은 `최신 pushed main 기준 공식 exe 재빌드 + 공식 exe smoke`까지 닫히기 전에는 완료라고 보고하지 않는다.

## 완료 보고 형식

- 비사소한 작업의 완료 보고는 항상 아래 3단 구조를 따른다.
  1. `내가 요청한 내용`
  2. `그래서 세운 계획`
  3. `결과와 내가 스스로 평가한 내용`
- 3번에는 아래를 반드시 포함한다.
  - 자동 검증 완료 범위
  - 공식 exe 반영 여부
  - 수동 acceptance 필요 항목
  - 검증 중 새로 발견한 문제
  - 그 문제를 위해 추가로 수정한 내용
  - 그 수정 뒤 다시 돌린 검증
  - `AGENTS 확인 기록`

## 서브 에이전트 운영

- 비사소한 작업에서는 sub agent를 병렬 활용할 수 있는지 먼저 검토한다.
- 독립된 조사, 병렬 검증, write scope가 분리되는 구현 작업은 적극적으로 sub agent로 분해한다.
- immediate critical path에서 바로 다음 행동이 결과에 막혀 있으면 main agent가 직접 처리하고, sub agent는 sidecar 작업에 우선 쓴다.
- sub agent를 띄울 때는 역할, 책임 범위, 읽기/쓰기 소유 범위, 기대 산출물을 명시한다.
- 코드 변경 sub agent는 write scope가 겹치지 않게 나누고, 다른 agent의 변경을 되돌리지 않는다는 원칙을 함께 준다.
- 작은 작업 단위로 넘어갈 때마다 현재 살아 있는 sub agent를 점검하고, 필요 없는 agent는 바로 닫는다.
- 완료 보고에는 `sub agent 사용 여부`, `활성/종료 상태`, `남아 있는 agent가 없는지`를 함께 적는다.
