# AGENTS

> 이 문서는 이 저장소의 단일 운영 기준 문서다.
> 비사소한 작업, 질문 응답, 문서 수정, 구조 변경, 장시간 실행을 시작하기 전에 항상 가장 먼저 다시 읽는다.

## 1. 이 문서의 역할

- 이 문서는 저장소 운영 규칙, 작업 시작점, 검증 기준, 금지 사항, 문서 역할 분리를 다룬다.
- 이 문서는 프로젝트 현재 상태를 오래 쌓아두는 문서가 아니다.
- 프로젝트 현재 상태와 최근 기록은 `docs/logbook.md`가 맡는다.
- 프로젝트 소개와 전역 구조 설명은 `README.md`가 맡는다.
- 모듈 상세 기준과 실행 절차는 각 모듈 `README.md`가 맡는다.
- 민감한 자격증명, 실제 메일 원문, 첨부 원본, 실제 사용자 workbook, 로컬 publish 운영은 tracked repo에 쓰지 않고 sibling `../secrets/README.local.md`와 그 하위 로컬 문서에만 둔다.

## 2. 항상 읽는 순서

- 비사소한 작업에서는 아래 순서를 항상 다시 통과한다.
  1. `AGENTS.md`
  2. `README.md`
  3. `docs/logbook.md`
  4. `docs/feature_catalog.md`
  5. 최신 `docs/logbook_archive/logbook_*.md` 1개
  6. 관련 모듈 `README.md`
  7. 관련 모듈 `docs/logbook.md`
- 이 순서는 새 작업 시작, 단계 전환, 문서 구조 변경, 커밋 전, 푸시 전, 후속 실행 전에도 다시 적용한다.
- `/plan` 또는 그에 준하는 계획 수립을 시작할 때도 먼저 다시 적용한다.
- 새 plan을 실제 active 작업으로 받아들이기 전에는 이전 active plan의 publish 상태를 먼저 확인한다.
- 이전 active plan이 아직 `commit + push + clean status`까지 닫히지 않았다면, 특별히 보류하기로 한 경우가 아니면 먼저 그 publish를 끝낸다.
- 계획을 실제 구현이나 실행으로 넘기는 직전에도 다시 적용한다.
- 완료 응답 작성, 커밋, 푸시, 마감 정리를 시작하기 직전에도 다시 적용한다.
- 새 기능 추가, 폴더 이동, 레이어 경계 판단이 포함된 작업은 `README.md`의 `새 기능을 어디에 둘까` 섹션을 반드시 다시 확인한다.
- 비공개 자산, 계정 정보, 실제 메일/엑셀/로그 경계가 관련된 작업은 sibling `../secrets/README.local.md`를 함께 다시 읽는다.

## 3. 문서 체계와 단일 역할

- `AGENTS.md`
  - 저장소 운영 규칙의 단일 기준
- `README.md`
  - 프로젝트 소개, 전체 구조, 전역 고정 메모, 기능 배치 기준
- `docs/logbook.md`
  - 프로젝트 레벨 현재 상태, 전역 결정, 활성 체크리스트, 최근 로그
- `docs/feature_catalog.md`
  - 현재 제품/운영 기능 카탈로그와 공식 접근점 인덱스
- `docs/logbook_archive/`
  - 이전 active logbook와 legacy 기준 문서 archive
- `<module>/README.md`
  - 해당 모듈의 상세 기준, 고정 결정, 경로, 실행 절차
- `<module>/docs/logbook.md`
  - 해당 모듈의 현재 상태, 활성 체크리스트, 최근 기록
- `<module>/docs/보고서/`
  - 외부 공유 또는 사용자 요청이 있는 큰 요약만 둘 공식 위치
- `<module>/docs/환경/`
  - 설치, 재현, 운영 절차를 둘 공식 위치
- `<module>/results/`
  - repo-safe한 smoke 결과, 비교 요약, 재현 가능한 소형 산출물을 둘 공식 위치
- `assets/`
  - root `README.md`가 직접 참조하는 프로젝트 전역 공용 자산을 둘 공식 위치
- `templates/codex_starter/`
  - 새 저장소 시작용 공통 운영 팩 복사본
- 같은 내용을 여러 상위 문서에 반복하지 않는다.
- 로그성 데이터는 `logbook`에만 쌓고, `README.md`는 current truth만 남긴다.

## 4. 답변과 작업 방식

- 사용자 설명은 쉬운 한국어를 먼저 쓴다.
- 기술 용어가 필요하면 먼저 쉬운 설명을 붙이고, 그 다음에 최소한으로 쓴다.
- 현재 무엇이 실제로 돌고 있는지는 대화 맥락이 아니라 `ps`, `pid`, 상태 파일, 진행률 파일을 먼저 확인한다.
- 사용자가 비효율적인 순서로 요청하면 그대로 잘게 쪼개기보다 더 나은 큰 그림과 권장 순서를 먼저 제안한다.
- 비사소한 작업을 마칠 때는 active checklist 반영 여부와 canonical 문서 반영 여부를 다시 점검한다.
- 즉, 계획을 세울 때 시작 게이트, 실행 시작 직전 게이트, 완료 직전 final gate를 모두 통과한 뒤에만 응답을 마무리한다.
- 승인된 상위 plan이 생기면 구현 전에 반드시 root `docs/logbook.md`의 `현재 실행 계획` 섹션에 plan 전문과 성공 기준을 먼저 반영한다.
- 같은 logbook 아래 `현재 체크포인트`와 `현재 활성 체크리스트`를 작은 작업 단위로 분해해 두고, 실제 구현은 그 체크리스트 1개씩만 기준으로 진행한다.
- 작은 작업을 시작할 때마다 다시 `AGENTS.md`와 `docs/logbook.md`를 읽고, 현재 체크포인트와 다음 체크 항목을 확인한 뒤 진행한다.
- 작은 작업을 끝낼 때마다 checklist 상태, 현재 체크포인트, 최근 로그를 즉시 갱신한다.
- 기능을 새로 추가하거나 기존 동작/입출력/검증 방식을 바꾸면 같은 턴에 반드시 `docs/feature_catalog.md`와 관련 `README/logbook`를 함께 갱신한다.
- 완료 보고 전에는 이번 턴에 `AGENTS.md`를 언제 다시 읽었는지 간단한 재독 기록을 남긴다.
- 재독 기록은 최소 `총 몇 번 읽었는지`와 `어느 게이트에서 읽었는지`를 포함한다.
- 사용자가 UI 문제 하나를 말하면 그 control만 고치고 끝내지 않는다.
- 같은 흐름의 loading, empty, error, success, persistence, scale, copy, adjacent action까지 함께 점검하고 닫아야 완료로 본다.
- 기본 제품 개발 루프는 `runtime service / CLI / web UI`를 먼저 닫고, 공식 Windows exe는 마지막 패키징 단계에서만 다시 만든다.
- 즉, 평소 구현/검증은 web-first로 진행하고, exe는 native picker, launcher, 아이콘/창 브랜딩, packaged smoke 같은 shell-specific acceptance만 맡는다.
- 예:
  - `AGENTS 확인 기록: 총 3회 (시작 게이트 / 실행 직전 / 완료 직전)`

## 4-1. 완료 보고 형식

- 비사소한 작업의 완료 보고는 항상 아래 3단 구조를 따른다.
  1. `내가 요청한 내용`
  2. `그래서 세운 계획`
  3. `결과와 내가 스스로 평가한 내용`
- 3번에는 아래를 반드시 포함한다.
  - 자동 검증 완료 범위
  - 공식 exe 반영 여부
  - 아직 사용자가 직접 확인해야 하는 수동 acceptance 항목
  - 검증 중 새로 발견한 문제
  - 그 문제를 위해 추가로 수정한 내용
  - 그 수정 뒤 다시 돌린 검증
  - `AGENTS 확인 기록`
- 즉, 구현 결과만 보고하지 않고, 검증 과정에서 드러난 실제 문제와 그 뒤의 추가 수정 흐름도 함께 보고한다.
- 공식 exe가 있는 작업은 `최신 pushed main 기준 공식 exe 재빌드 + 공식 exe smoke`까지 닫히기 전에는 완료라고 보고하지 않는다.

## 4-2. 서브 에이전트 운영

- 비사소한 작업에서는 항상 `지금 sub agent를 병렬로 써서 더 안전하고 빠르게 닫을 수 있는지`를 먼저 검토한다.
- 독립된 하위 질문, 병렬 검증, 쓰기 범위가 분리되는 구현 작업, 문서 동기화, 회귀 확인은 가능한 한 적극적으로 sub agent를 활용한다.
- 단, immediate critical path에서 바로 다음 행동이 그 결과에 막혀 있으면 main agent가 직접 처리하고, sub agent는 sidecar/병렬 작업에 우선 배치한다.
- sub agent를 띄울 때는 아래를 반드시 명시한다.
  - 역할
  - 책임 범위
  - 읽기/쓰기 소유 범위
  - 기대 산출물
  - 다른 agent와 충돌하면 안 되는 파일 또는 모듈
- 코드 변경을 맡기는 sub agent는 서로 write scope가 겹치지 않게 나눈다.
- 각 sub agent에는 `다른 agent도 같은 코드베이스에서 일하고 있으니, 남의 변경을 되돌리지 말고 현재 상태를 존중하라`는 원칙을 같이 준다.
- explorer 성격의 sub agent는 코드베이스 질문, bounded 조사, 비교 검증에 우선 쓰고, worker 성격의 sub agent는 실제 수정/실행/테스트에 쓴다.
- 완료가 급하지 않은 장기 작업을 맡긴 sub agent는 background로 돌리고, main agent는 기다리지 말고 다른 비충돌 작업을 바로 진행한다.
- wait는 정말로 막혔을 때만 한다. reflex처럼 반복 대기하지 않는다.
- 작은 작업 단위로 넘어갈 때마다 현재 살아 있는 sub agent를 점검한다.
  - 아직 필요한 agent인지
  - 막혀 있는지
  - 이미 결과가 충분한지
  - write scope 충돌 위험이 없는지
- 더 이상 필요 없는 sub agent는 바로 정리한다. 열어둔 agent를 습관적으로 방치하지 않는다.
- 기본 운영 기록에는 최소 아래를 남긴다.
  - 현재 활성 sub agent 수
  - 각 agent의 역할
  - 상태(`running / blocked / completed / closed`)
  - main agent와의 충돌 여부
- 비사소한 완료 보고에는 `sub agent 사용 여부`와 `닫지 않은 agent가 남아 있지 않은지`를 함께 적는다.
- 이 규칙은 OpenAI sub-agent 운영 원칙에 맞춰 `local planning first`, `bounded delegation`, `disjoint ownership`, `wait sparingly`, `close idle agents`를 지키는 방식으로 해석한다.

## 5. 핵심 개발 원칙

- 운영 규칙은 `AGENTS.md`, 현재 상태는 `docs/logbook.md`, 프로젝트 구조는 `README.md`, 모듈 상세 기준은 각 모듈 `README.md`로 분리한다.
- 주경로는 `이메일 수신 -> 구조화 분석 -> Excel 출력`이다.
- 현재 코드 소유 경계는 `mailbox / analysis / exports / llm`를 유지한다.
- 앞으로 GUI, 프로필 편집, 실행 진입점은 `app/`에 두고, 장시간 실행 조율과 배치 런타임은 `runtime/`에 둔다.
- `app/`과 `runtime/`은 실제 코드가 처음 들어가는 턴에만 만든다. 그때는 해당 디렉토리 `README.md`와 `docs/logbook.md`를 같은 턴에 함께 만든다.
- 처음부터 과도한 추상화, 미사용 옵션, 추측성 fallback을 넣지 않는다.
- 먼저 주경로를 단순하게 완성하고, 실제 문제가 확인된 뒤 필요한 만큼만 확장한다.
- 민감한 운영 정보는 tracked repo 밖 `../secrets/`에서만 관리한다.

## 6. 산출물과 네이밍 기준

- 로컬 워크스페이스는 `repo / envs / results / secrets` sibling 구조를 기본으로 본다.
- 실제 사용자 메일, 첨부, workbook, profile 로그의 canonical 위치는 `../secrets/사용자 설정/<이름>/실행결과/`다.
- reference fixture는 `../secrets/사용자 설정/<이름>/참고자료/`에 두고 읽기 전용으로 취급한다.
- repo 내부 `<module>/results/`는 재현 가능한 smoke 결과, 비교 요약, 소형 metadata에 한해 사용한다.
- root `results/`를 새로 운영 기준으로 삼지 않는다.
- 예시:
  - 실제 inbox에서 받아 저장한 `raw.eml`, 첨부 원본, 생성 workbook, 프로필별 usage log는 `../secrets/사용자 설정/<이름>/실행결과/`에 둔다.
  - 재현 가능한 auth probe 요약 JSON, workbook diff summary, smoke report 같은 소형 결과만 `mailbox/results/`, `exports/results/` 같은 repo 내부 공식 위치 후보를 쓴다.
- 새 산출물 루트와 시간이 지나며 누적되는 문서는 `YYMMDD_HHMM_설명` prefix를 사용한다.
- 장기 작업 안의 하위 단계 폴더는 `01_`, `02_`, `03_` 순서 prefix를 함께 쓴다.
- smoke, debug, failed run 산출물은 최종 canonical 결과가 확보되면 삭제 가능한 임시 자산으로 본다.

## 7. 반복 작업은 skill을 쓴다

- 이 저장소의 공용 skill 원본은 `repo/.agents/skills/` 아래에 둔다.
- 이 저장소에서 자주 쓰는 반복 절차는 아래 skill로 분리한다.
  - `repo-orient-and-ground`
  - `checklist-and-canonical-doc-sync`
  - `feature-placement-and-boundary-review`
  - `private-assets-and-secrets-boundary`
  - `directory-inventory-preflight`
  - `logbook-maintenance`
  - `long-run-watchdog`
  - `results-hygiene-and-cleanup`

## 8. 실무 기본 명령

- 새 파일/폴더 생성 전 구조 점검
  - `python tools/directory_inventory.py --module <module> --kind <kind> --candidate-name <name>`
- logbook archive 점검
  - `python tools/logbook_archive_guard.py --archive-if-needed`
- root와 모듈 active logbook 일괄 점검
  - `python tools/logbook_archive_all.py --archive-if-needed`
- 반복 git 동기화
  - `tools/git_sync_all.sh "<커밋 메시지>" [--push]`

## 9. 완료 기준

- 관련 검증 명령을 실제로 돌려 결과를 확인한다.
- 코드나 문서만 끝내지 않고 관련 canonical 문서를 같은 턴에 함께 갱신한다.
- 산출물 경로, 다음 연결점, 삭제된 임시 자산이 있으면 logbook에 남긴다.
- plan 마감의 기본 완료 조건은 `canonical 문서 반영 -> commit -> push -> git status clean 확인`이다.
- 기본 publish 단위는 `승인된 상위 plan 1개`다. 작은 step마다 push하지는 않되, 사용자 검증 가치가 큰 안정 마일스톤이면 plan 중간 publish는 허용한다.
- 질문 답변만 한 경우, 탐색만 한 경우, 사용자가 push 보류를 요청한 경우, secret 경계 때문에 범위 분리가 필요한 경우만 publish gate 예외로 둔다.

## 10. 새 저장소 시작용 복사본

- 이 저장소의 공통 운영 팩 복사본은 `templates/codex_starter/` 아래에 둔다.
- 새 저장소를 시작할 때는 여기서 `AGENTS.md`, `docs/logbook.md`, `.agents/skills/`를 복사해 시작한다.
- 복사 후에는 해당 저장소의 구조, 실행 명령, 검증 기준, 민감 정보 경계를 그 저장소에 맞게 수정한다.
