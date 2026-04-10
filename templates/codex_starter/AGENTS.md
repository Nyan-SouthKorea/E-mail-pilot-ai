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
