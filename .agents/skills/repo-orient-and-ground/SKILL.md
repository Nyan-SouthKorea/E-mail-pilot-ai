# repo-orient-and-ground

이 skill은 비사소한 작업을 시작하기 전에 현재 기준 문서와 현재 truth를 다시 맞추는 절차를 정리한다.

## 언제 쓰나

- 새 작업을 시작할 때
- `/plan` 또는 그에 준하는 계획 수립을 시작할 때
- 단계가 바뀔 때
- 계획에서 실제 구현이나 실행으로 넘어가기 직전
- 커밋 전, 푸시 전, 후속 실행 전
- 문서 구조나 레이어 경계를 판단할 때

## 읽는 순서

1. `AGENTS.md`
2. `README.md`
3. `docs/logbook.md`
4. `docs/feature_catalog.md`
5. 최신 `docs/logbook_archive/logbook_*.md` 1개
6. 관련 모듈 `README.md`
7. 관련 모듈 `docs/logbook.md`
8. 민감 정보 경계가 중요하면 sibling `../secrets/README.local.md`

## 해야 할 일

- 지금 작업의 목표, 성공 기준, 관련 모듈, 민감 정보 경계를 짧게 요약한다.
- 이미 있는 구조와 경로를 먼저 확인하고, 없는 구조를 상상으로 채우지 않는다.
- 현재 active checklist에서 이미 열려 있는 항목이 있는지 먼저 확인한다.
- root `docs/logbook.md`의 `현재 실행 계획`, `현재 체크포인트`, `publish 상태`를 먼저 확인한다.
- 새 plan을 시작하려면 이전 active plan의 publish 상태가 닫혔는지 먼저 확인한다.
- 현재 truth를 한두 문장으로 다시 말한 뒤에만 구현이나 수정에 들어간다.
- 승인된 plan이 있으면 구현 전에 그 plan 전문이 root logbook에 올라와 있는지 먼저 확인한다.
- 완료 응답, 커밋, 푸시, 마감 정리 직전에도 같은 읽는 순서를 다시 통과한다.
