# Logbook

> 이 문서는 프로젝트 레벨의 단일 기록 문서다.
> 읽을 때는 항상 현재 `docs/logbook.md`와 최신 `docs/logbook_archive/logbook_*.md` 1개를 함께 본다.

## 읽기 규칙

- 이 문서는 `현재 프로젝트 스냅샷`, `현재 전역 결정`, `현재 실행 계획`, `현재 체크포인트`, `현재 활성 체크리스트`, `최근 로그`를 함께 유지한다.
- 새 로그를 쓰기 전에는 항상 아래 명령을 먼저 실행한다.
  - `python tools/logbook_archive_guard.py --archive-if-needed`
- active logbook 줄 수가 `1000`을 넘으면 현재 파일을 `docs/logbook_archive/logbook_YYMMDD_HHMM_*.md`로 archive하고, active logbook는 고정 섹션만 남긴 채 다시 시작한다.
- 에이전트는 비사소한 작업에서 항상 아래 순서로 문서를 읽는다.
  1. `AGENTS.md`
  2. `README.md`
  3. `docs/logbook.md`
  4. `docs/feature_catalog.md`
  5. 최신 `docs/logbook_archive/logbook_*.md` 1개
  6. 관련 모듈 `README.md`
  7. 관련 모듈 `docs/logbook.md`
- 새 파일, 새 폴더, 새 문서, 복사본, 이동 결과, 다운로드 자산처럼 실제 산출물을 만들기 전에는 관련 기준 문서와 디렉토리 인벤토리 출력을 먼저 확인한다.
- 이 문서에는 프로젝트 레벨 현재 상태와 전역 결정만 둔다.
- 모듈별 상세 아키텍처, 고정 경로, 비채택 결정, 세부 실행 절차는 각 모듈 `README.md`에 둔다.

## 현재 프로젝트 스냅샷

- 상위 목표:
  - 이메일을 받아 구조화된 결과로 정리하고 Excel로 안전하게 누적하는 자동화 스택을 만든다.
  - 현재 우선 주경로는 `이메일 수신 -> 구조화 분석 -> triage 검토 -> Excel 출력`이다.
- 현재 작업 모드:
  - `협업 모드`
- 현재 전역 운영 문서:
  - 운영 방법과 정책: `AGENTS.md`
  - 프로젝트 소개, 전체 구조, 기능 배치 기준: `README.md`
  - 프로젝트 레벨 현재 상태와 최근 기록: `docs/logbook.md`
  - 제품/운영 기능 카탈로그: `docs/feature_catalog.md`
  - 저장소 공용 반복 workflow skill 원본: `.agents/skills/`
  - 새 저장소 시작용 공통 운영 팩: `templates/codex_starter/`
  - 모듈별 상세 기준: `mailbox/README.md`, `analysis/README.md`, `exports/README.md`, `llm/README.md`, `runtime/README.md`, `app/README.md`
  - 모듈별 현재 상태와 최근 기록: `mailbox/docs/logbook.md`, `analysis/docs/logbook.md`, `exports/docs/logbook.md`, `llm/docs/logbook.md`, `runtime/docs/logbook.md`, `app/docs/logbook.md`
- 현재 로컬 워크스페이스:
  - sibling 구조 `repo / envs / results / secrets`
- 현재 공유 워크스페이스:
  - `workspace.epa-workspace.json + secure/secrets.enc.json + state/state.sqlite + locks/write.lock + mail/ + exports/ + logs/`
- 비공개 자산과 자격증명의 canonical 로컬 시작 문서는 sibling `../secrets/README.local.md`다.
- 현재 로컬 산출물 정책:
  - 제품 기준 메일 bundle, 운영 workbook, 리뷰 상태, 로그는 새 세이브 파일 내부의 v2 구조에 둔다.
  - sibling `../secrets/사용자 설정/<이름>/참고자료/`는 개발자 전용 fixture와 raw 자산을 읽기 전용으로 둘 때만 쓴다.
  - repo 내부 `<module>/results/`는 재현 가능한 smoke 결과와 소형 비교 자료만 둔다.
  - root `results/`는 현재 canonical 위치가 아니다.
- 현재 모듈 상태:
  - `mailbox`: bundle schema, fixture materialize, bundle reader, provider 자동 설정 후보 생성, connect/auth probe, local-only credential loader, real account latest IMAP fetch smoke, INBOX read-only backfill smoke가 있다.
  - `analysis`: `NormalizedMessage -> ExtractedRecord` structured output 경로와 multimodal 입력 builder, fixture/runtime bundle smoke, real-bundle quality smoke, 3-way triage, HTML review board, application-only batch export 경로가 있다.
  - `exports`: 템플릿 reader, semantic mapping, projection, workbook append, 회귀 guardrail이 있다.
  - `llm`: OpenAI wrapper, usage logging, 가격표 snapshot 기반 비용 추정, structured output transport가 있다.
  - `runtime`: 공유 워크스페이스 manifest, 암호화 secret blob, sqlite state, write lock, dedupe/workbook rebuild, sync CLI, feature harness smoke가 있다.
  - `app`: FastAPI 기반 로컬 UI, pywebview launcher, 3단계 시작 마법사, settings, review center, 고급 도구, UI smoke가 있다.

## 현재 전역 결정

- 시작 게이트는 항상 `AGENTS.md -> README.md -> docs/logbook.md -> docs/feature_catalog.md`다.
- 새 active plan을 실제 구현으로 옮기기 전에는 이전 active plan의 publish 상태를 먼저 확인한다.
- 승인된 active plan이 생기면 구현 전에 그 plan 전문을 root `docs/logbook.md`의 `현재 실행 계획`에 먼저 반영한다.
- 구현은 `현재 체크포인트`와 `현재 활성 체크리스트`를 작은 작업 단위로 갱신하면서 진행한다.
- plan 마감의 기본 완료 조건은 `canonical 문서 반영 -> commit -> push -> git status clean 확인`이다.
- stable truth는 `README.md`와 각 모듈 `README.md`, active truth는 `docs/logbook.md`와 각 모듈 `docs/logbook.md`에 둔다.
- 런타임 데이터 계약은 `MailBundle -> NormalizedMessage -> ExtractedRecord -> ExportRow` 4단계를 유지한다.
- `ExtractedRecord` top-level triage는 `application`, `not_application`, `needs_human_review` 3개 값으로 고정한다.
- 메일 설정 탐지는 `rule/probe-first`, LLM 보조 fallback 기준을 유지한다.
- 입력 해석은 multimodal-first로 두고, 이미지나 스캔 문서가 있으면 실제 이미지 입력을 우선 활용한다.
- 템플릿 해석은 rule-first로 시작하고, unresolved header만 LLM fallback으로 보충한다.
- `app/`은 전용 데스크톱 창과 로컬 Web UI를 맡고, `runtime/`은 공유 save와 sync orchestration을 맡는다.
- Windows 포터블 exe의 공식 실행 경로는 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe` 하나로 고정한다.
- `Z:` 공유 폴더의 exe와 Linux repo shared mirror는 더 이상 실행본 canonical 위치로 쓰지 않는다.
- 제품 기준 실제 inbox bundle, 운영 workbook, usage log, review 로그는 현재 세이브 파일 내부의 `mail/`, `exports/`, `logs/` 아래에 둔다.
- sibling `../secrets/사용자 설정/<이름>/실행결과/`는 개발자 전용 legacy/private runtime 위치로만 본다.
- 제품 세이브의 canonical 구조는 `workspace.epa-workspace.json + secure/ + state/ + locks/ + mail/ + exports/ + logs/`다.
- 새 세이브는 legacy `profile/참고자료/실행결과/기대되는 산출물` 구조를 만들지 않는다.
- workbook 자동 반영은 triage가 `application`이고 기업/연락처 신호가 함께 확인된 경우에만 허용한다.
- 공유 워크스페이스에서는 민감한 값도 `secure/secrets.enc.json` 안에 암호화 저장하고, review/dedupe/override/workbook row 상태는 `state/state.sqlite`에 저장한다.
- 공유 워크스페이스는 단일 작성자 잠금을 기본으로 하고 `locks/write.lock` heartbeat 기준 stale takeover를 허용한다.

## 현재 실행 계획

- plan 제목:
  - `고객 서비스형 UI/세이브 구조 리팩터 v3`
- plan 요약:
  - 세이브 파일 열기/만들기를 경로 입력형이 아니라 실제 폴더 선택 기반으로 바꾸고, 새 세이브는 v2 영문 구조만 사용한다.
  - 설정, 계정 연결 확인, 빠른 테스트/전체 동기화는 오래 걸려도 상태가 보이는 서비스형 진행 카드와 진행률을 가진다.
  - 로컬 장치 전용 암호화 저장소를 도입해 마지막 세이브 파일과 암호, 기본 OpenAI API key를 이 PC에만 저장하고 자동 재개/자동 채움을 지원한다.
  - 앱을 다시 켜면 마지막 세이브를 자동으로 다시 열고, 현재 세이브 닫기/다른 세이브 열기/최근 세이브 선택을 자연스럽게 지원한다.
- 이번 plan의 성공 기준:
  - `찾아보기`는 경로 선입력 없이도 바로 폴더 선택기가 열려야 하고, 최근 세이브는 클릭 가능한 목록이어야 한다.
  - 새 세이브는 `mail / exports / logs / secure / state / locks` 기준의 v2 구조만 만들고 legacy `profile/참고자료/실행결과/기대되는 산출물`은 만들지 않는다.
  - `(i)` 도움말은 hover/focus/click 모두 동작하는 실제 tooltip/popover가 되어야 한다.
  - 계정 연결 확인과 동기화는 진행 상태, 단계, 진행률, 부분 완료/실패 이유와 다음 행동을 보여야 한다.
  - 앱 재실행 시 마지막 세이브 자동 재개, OpenAI API key 자동 채움, 세이브 닫기/전환이 동작해야 한다.
  - exe 아이콘과 전체 톤이 실제 고객 서비스용 Windows 프로그램처럼 정리돼야 한다.

## 현재 체크포인트

- 지금 단계:
  - v3 구현과 검증을 마쳤고, publish 마감만 남은 단계
- 바로 다음 작업:
  - current plan commit, push, clean status 확인으로 마감한다
- publish 상태:
  - 이전 plan publish 완료
  - current plan 작업 중

## 현재 활성 체크리스트

- `고객 서비스형 UI/세이브 구조 리팩터 v3`
  - [x] root `AGENTS.md` 재확인
  - [x] root `docs/logbook.md`에 active plan 전문 반영
  - [x] v2 세이브 구조 helper와 manifest 버전 교체
  - [x] 로컬 장치 전용 암호화 저장소 추가
  - [x] 홈의 세이브 열기/만들기 흐름 재설계
  - [x] 최근 세이브 파일 클릭/정리 동작 추가
  - [x] `(i)` tooltip/popover 시스템 전역 적용
  - [x] 계정 연결 확인 background job + 진행 카드
  - [x] 빠른 테스트/전체 동기화 진행 카드 + 부분 완료 처리
  - [x] 세이브 닫기/전환/자동 재개 추가
  - [x] OpenAI API key 자동 채움 추가
  - [x] legacy 내부 폴더 제거와 문서/가이드 반영
  - [x] exe 아이콘 및 브랜딩 갱신
  - [x] `app.ui_smoke`와 관련 검증 갱신
  - [x] canonical 문서 반영
  - [ ] current plan commit 완료
  - [ ] current plan push 완료
  - [ ] `git status --short --branch` clean 확인

## 최근 로그

### 2026-04-13 | Human + Codex | 고객 서비스형 UI/세이브 구조 리팩터 v3 구현과 검증

- 새 세이브 canonical 구조를 `workspace.epa-workspace.json + secure + state + locks + mail + exports + logs` 기준의 v2 구조로 고정했고, 새 세이브 생성 시 legacy `profile / 참고자료 / 실행결과 / 기대되는 산출물` 폴더가 생기지 않도록 `runtime/workspace.py` 초기화 순서를 바로잡았다.
- 세이브 파일 열기/만들기는 경로 선입력보다 실제 폴더 선택을 기본으로 쓰게 유지했고, 최근 세이브는 `이 PC에서 바로 다시 열기` 또는 `암호를 확인한 뒤 다시 열기` 두 흐름으로 다시 정리했다.
- 세이브 닫기, 다른 세이브 열기, 앱 재실행 시 마지막 세이브 자동 재개, 기본 OpenAI API key 자동 채움은 이 PC 전용 암호화 저장소를 통해 동작하게 했다.
- 계정 연결 확인은 background job으로 전환해 `입력 확인 -> 서버 후보 확인 -> 로그인 시도 -> 폴더 목록 읽기 -> 완료` 단계와 진행률을 즉시 보여주게 했다.
- 빠른 테스트/전체 동기화는 background job 진행 카드와 진행률, 부분 완료, 다음 행동 안내를 보여주게 했고, 메일 저장 성공 후 분석/내보내기 실패를 `부분 완료`로 따로 표현한다.
- `(i)` 도움말과 disabled 이유 안내는 실제 tooltip/popover 컴포넌트로 통일했고, 고객용 UI 용어는 `기본 받은편지함`, `엑셀 양식`, `세이브 파일` 중심으로 다시 정리했다.
- 최근 세이브 재열기, 새 v2 세이브 생성, UI smoke, feature harness smoke를 다시 검증했고, 샘플 세이브 기준 `logs/app/260413_1122_ui_smoke.json`, `logs/runtime/260413_1122_feature_harness_smoke.json`까지 확인했다.
- `packaging.portable_exe.build` prerequisite check는 Linux 개발 호스트에서는 Windows 전용 의존성을 `warn`으로만 보게 바꿔, 실제 Windows 패키징 검증기와 로컬 feature harness가 서로의 의미를 침범하지 않게 정리했다.

### 2026-04-13 | Human + Codex | 서비스형 고객 UI 리팩터 v2 구현

- 홈 미오픈 상태를 긴 설명형 화면에서 벗어나 `세이브 파일 열기/만들기 -> 계정 연결 -> 빠른 테스트 동기화` 3단계 시작 마법사로 재구성했다.
- `기존 세이브 열기`와 `새 세이브 만들기`는 탭형 흐름으로 바꾸고, 최근 세이브가 없으면 새 세이브 만들기를 기본 탭으로 연다.
- `찾아보기` 버튼은 더 이상 `desktop_ready`가 오기 전까지 영구 비활성으로 두지 않고, exe 기준에서 바로 클릭 가능하게 바꿨다. 전용 창 연결이 아직 늦으면 내부에서 짧게 재시도하고, 실패 시에만 직접 입력 안내를 보여준다.
- 앱 셸은 상단 pill 중심 구조에서 `좌측 사이드바 + 상단 작업 헤더` 구조로 바꿨고, 기본 화면에는 기술 경로보다 현재 단계와 다음 행동이 먼저 보이게 했다.
- 색상과 컴포넌트 토큰은 베이지 데모 톤에서 벗어나 슬레이트/네이비 기반 업무용 프로앱 스타일로 재정의했다.
- 세이브 파일 오픈/생성 성공 후에는 홈으로 돌아가기보다 `/settings`로 이동시켜, 첫실행 Step 2인 계정 연결 확인으로 자연스럽게 이어지게 했다.
- `app/README.md`와 `docs/feature_catalog.md`는 새 용어와 홈 흐름에 맞춰 갱신했다.
- 원격 Windows 빌드도 다시 실행했고, 최종 사용자 실행본 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`를 최신 UI 기준으로 다시 publish 했다.
- 검증은 `python tools/logbook_archive_guard.py --archive-if-needed`, `python -m py_compile app/server.py app/main.py app/ui_smoke.py`, `python -m app.ui_smoke --workspace-root /tmp/epa_ui_v2_smoke --workspace-password SampleWorkspace260408`, `python -m runtime.cli feature-harness-smoke --workspace-root /tmp/epa_ui_v2_smoke --workspace-password SampleWorkspace260408` 기준으로 통과했다.

### 2026-04-13 | Human + Codex | Windows 빌드 미러 stale source 원인 확인과 packaging helper 보강

- 사용자 화면 피드백을 기준으로 역추적해 보니, 실제 실행 중인 프로세스 경로는 공식 runtime `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`가 맞았지만, Windows 빌드 미러 `D:\EmailPilotAI\repo`가 오래된 소스 상태여서 새 UI가 exe에 반영되지 않은 것을 확인했다.
- Windows `D:\EmailPilotAI\repo\app\templates\home.html`과 Linux repo의 같은 파일을 비교해 source mismatch를 확인했고, Windows repo를 최신 `main` 기준 소스로 다시 맞춘 뒤 Windows 포터블 build/publish를 재실행했다.
- 현재 Windows `D:\EmailPilotAI\repo`와 Linux repo HEAD는 모두 `8a750ad`로 일치한다.
- `app/packaging/build_windows_portable_and_publish.sh`는 앞으로 Linux working tree tar 미러 대신 `origin/main` 기준 Git sync를 먼저 수행한 뒤 Windows build를 실행하도록 보강했다.
- `app/packaging/publish_portable_to_runtime.ps1`는 공식 runtime exe가 실행 중이면 publish 전에 해당 프로세스를 종료하고 나서 복사하게 보강했다.

### 2026-04-10 | Human + Codex | 서비스형 홈/설정/동기화/리뷰 UI 1차 전환

- 홈 화면을 관리용 도구 톤에서 벗어나 `세이브 파일 -> 계정 연결 -> 빠른 테스트 동기화 -> 전체 동기화 -> 리뷰` 순서의 서비스형 온보딩 대시보드로 다시 구성했다.
- `세이브 파일 가이드`는 별도 페이지 이동만 강요하지 않고, 홈 안에서 바로 여닫는 모달을 기본 경로로 바꿨다.
- 설정 화면은 기본/고급으로 분리했고, 모델은 자유 입력 대신 `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano` 선택형으로 바꿨다.
- `계정 연결 확인` 버튼을 추가해 실제 IMAP 로그인 가능 여부를 확인하고, 성공 시 폴더 목록과 추천 기본 폴더를 `secure/secrets.enc.json` 설정에 저장하게 했다.
- 동기화 화면을 따로 만들고, `빠른 테스트 동기화`와 `전체 동기화`를 분리했다. `quick_smoke`는 최근 10건만 대상으로 하고, `incremental_full`은 기존 증분 fetch + 분석 재사용 흐름을 그대로 쓴다.
- `runtime.feature_registry`에는 `mailbox.connection_check`, `runtime.workspace.sync.quick_smoke`를 추가해 UI/관리도구/CLI에서 같은 기능 카탈로그 언어를 쓰게 했다.
- 리뷰센터는 테이블 중심 검증판에서 벗어나, 카드형 확장 리스트와 빠른 override 흐름을 가진 실사용 검토 화면으로 다시 정리했다.
- analysis 재사용은 이미 `analysis_revision + bundle fingerprint` 기준으로 `extracted_record.meta.json`을 남기는 구조를 넣어 둔 상태이고, 이번 sync 경로에서는 이를 기본 재사용 경로로 연결했다.
- 외부 사용자용 개념 설명은 `app/docs/환경/first_user_save_file_guide.md`로 분리해, 세이브 파일, 로그인 ID, INBOX, 템플릿, 빠른 테스트 동기화 이유를 앱 밖 문서에서 설명하게 했다.
- 검증은 `py_compile`, `create-sample-workspace`, `app.ui_smoke`, `feature-check-all` 기준으로 통과했다.

### 2026-04-10 | Human + Codex | AGENTS 중심 문서/산출물 정리와 cleanup

- root `AGENTS.md`만 운영 규칙을 맡기고, 다른 문서에는 각 문서 역할만 남기도록 `README.md`, `docs/feature_catalog.md`, 모듈 `README/logbook`, starter pack 문구를 일괄 축약했다.
- `app/packaging/README.md`를 packaging canonical 문서로 남기고, 중복이 크던 `app/docs/환경/windows_portable_exe.md`는 실제로 삭제했다.
- 홈 화면의 `가이드 새 창으로 보기` 링크를 없애고, `/workspace/guide`는 더 이상 별도 템플릿을 유지하지 않고 홈 모달로 redirect 하게 바꿨다.
- `app/templates/workspace_guide.html` 같은 guide wrapper template을 제거해 세이브 파일 가이드 표현을 한 군데로 줄였다.
- repo 내부 `__pycache__` 같은 cache 산출물은 이번 cleanup publish에서 함께 정리했다.
- 검증은 `app.ui_smoke`, `feature-harness-smoke`, logbook/archive guard, `git status --short --branch` clean 확인 기준으로 닫았다.

### 2026-04-10 | Human + Codex | 파일 탐색기 브리지 복구와 로컬 실행 전용 정책 정리

- 로컬 Windows exe에서도 `pywebview` 브리지가 준비되기 전에 프런트엔드가 너무 빨리 `브라우저 fallback`으로 단정하던 문제를 기준으로, 앱 런처와 서버가 공유하는 실행 컨텍스트를 새로 추가했다.
- 홈, 설정, 관리도구는 이제 `shell_mode`, `native_dialog_state`, 현재 실행 경로, 공식 로컬 실행 폴더, `startup.log` 경로를 진단 정보로 같이 보여준다.
- `찾아보기` 버튼은 기본 비활성화로 렌더링하고, `desktop_ready`가 확인되기 전에는 `전용 창 연결 확인 중` 상태를 유지하도록 바꿨다.
- Windows 실행 정책은 `공유 폴더는 배포본 보관용`, `실제 실행은 로컬 onedir 복사본`으로 다시 고정했다.
- 공유 드라이브나 UNC 경로에서 직접 실행하면 `pythonnet / Python.Runtime.dll` 단계까지 가기 전에 친절한 preflight 안내를 띄우고 종료하도록 런처를 보강했다.
- `app.ui_smoke`는 홈, 설정, 관리도구에서 새 진단 정보와 초기 `브라우저 fallback` 비노출 기준을 같이 확인하도록 업데이트했다.

### 2026-04-09 | Human + Codex | Windows `python310.dll` 부팅 오류 복구 기준과 AGENTS 재독 게이트 강화

- 표준 Windows build bundle과 Linux shared mirror에 `python310.dll`, `python3.dll`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, `ucrtbase.dll` 같은 필수 실행 파일이 실제로 존재한다는 점을 기준으로, 복구 초점은 `완전 누락`보다 `패키징 안정성`과 `공식 지원 경로 정리`에 맞췄다.
- `EmailPilotAI.spec`에서 `UPX`를 꺼 검증용 portable exe를 안정성 우선 설정으로 바꿨고, `portable_bundle_manifest.py`로 필수 DLL 검사와 sha256 manifest 생성을 공용화했다.
- `build_portable_exe.ps1`는 이제 build 후 필수 DLL 검사와 `portable_bundle_manifest.json` 생성까지 통과해야 완료로 본다.
- `sync_portable_to_local_cache.ps1`를 추가해 공식 fallback 경로 `%LOCALAPPDATA%\\EmailPilotAI\\portable\\EmailPilotAI\\`로 bundle을 동기화하고, source/target manifest 비교와 packaged smoke까지 한 번에 수행하게 했다.
- Samba 공유 실행에서만 `python310.dll`이 `LoadLibrary: 액세스가 거부되었습니다`로 실패하는 증상을 반영해, Linux shared mirror 생성 시 `.exe`, `.dll`, `.pyd`에 실행 비트를 주도록 보강했다.
- onedir 수동 복사 기준은 `dist/windows-portable/EmailPilotAI/` 폴더 전체를 통째로 옮기는 것으로 고정했고, `cleanup_portable_artifacts.sh`로 `build/EmailPilotAI/`, `dist/EmailPilotAI/`, `dist/windows-portable.precheck/` 같은 로컬 build 부산물만 기본 정리 대상으로 묶었다.
- 문서에는 공식 지원 경로를 `공유 폴더 직접 실행`과 `공식 로컬 cache 복사본`으로 고정하고, `D:\\#EmailPilotAI` 같은 임의 수동 복사 경로는 비공식으로 분리했다.
- `AGENTS.md`, starter `AGENTS.md`, repo-local skill 2종에는 `/plan 시작`, `실행 직전`, `완료 직전`에 `AGENTS.md -> README.md -> docs/logbook.md -> docs/feature_catalog.md` 재독 게이트를 더 명시적으로 반영했다.

### 2026-04-09 | Human + Codex | Windows build 산출물 Linux 공유 미러와 Samba 실행 기준 정리

- Windows SSH 세션에서는 사용자의 `Z:` 네트워크 드라이브가 보이지 않는 것을 다시 확인했고, 이를 기준으로 공유 미러 전략을 `Windows가 Samba에 직접 쓰기`가 아니라 `A100이 reverse SSH로 Windows 산출물을 다시 끌어오기`로 고정했다.
- `app/packaging/build_windows_portable_and_mirror.sh`를 추가해 A100에서 `Windows build -> packaged smoke -> Linux 공유 경로 미러`를 한 번에 실행하게 했고, `app/packaging/mirror_portable_to_linux.sh`는 기존 Windows 산출물만 다시 가져오는 helper로 분리했다.
- 공유 실행 기준 경로는 `repo/dist/windows-portable/EmailPilotAI/EmailPilotAI.exe`로 정리했고, 이는 tracked release artifact가 아니라 Samba 검증 편의용 미러로 다룬다.
- 문서에는 “연동성은 exe 위치가 아니라 같은 세이브 파일 폴더를 열었는지로 결정된다”는 기준과, 공유 폴더 직접 실행이 느리거나 막힐 때는 Windows 로컬 복사 실행을 fallback으로 쓰는 정책을 함께 반영했다.

### 2026-04-09 | Human + Codex | 세이브 파일 파일탐색기와 설정/버튼 UX 복구

- 홈 화면의 세이브 파일 열기/생성, 기존 profile import, 설정의 템플릿 경로에 `찾아보기` 버튼을 추가하고, Windows exe에서는 pywebview 네이티브 파일 탐색기를 통해 폴더/파일을 직접 고르게 했다.
- 홈에 `세이브 파일 가이드`를 추가해 `세이브 파일 = workspace.epa-workspace.json 이 들어 있는 폴더`라는 기준과 공유 폴더 기반 권장 흐름을 앱 안에서 바로 읽게 했다.
- 입력 경로는 `기존 세이브`, `새 세이브 가능`, `잘못된 경로`, `profile import 가능`, `템플릿 경로 상태`로 분류해 즉시 안내한다.
- 설정 저장은 성공/실패 배너, 마지막 저장 시각, 템플릿 경로 상태를 함께 보여주고, 워크스페이스 미오픈/읽기 전용/워크스페이스 밖 템플릿 경로를 명시적으로 안내하게 했다.
- `runtime.feature_registry`의 packaging check가 `backports` 미설치 환경에서도 예외를 던지지 않도록 고쳐 `/admin/features` 페이지가 다시 안정적으로 열린다.
- 새 샘플 세이브 기준 `app.ui_smoke`를 통과했고, Windows remote build도 다시 돌려 `EmailPilotAI.exe` packaged smoke까지 완료했다.

### 2026-04-08 | Human + Codex | Windows exe 부팅 오류 복구 기준 추가

- Windows에서 `EmailPilotAI.exe`가 시작 직후 `No module named 'backports'`로 죽는 패키징 오류를 확인했다.
- 원인은 `pkg_resources -> setuptools._vendor.jaraco.context` 경로가 Python 3.10에서 `backports.tarfile`을 요구하는데, PyInstaller bundle에 해당 모듈이 빠져 있던 것이다.
- `requirements-dev.txt`에 `backports.tarfile`를 추가하고, `EmailPilotAI.spec`에 `backports`, `backports.tarfile` hidden import를 넣는 방향으로 수정했다.
- `build_portable_exe.ps1`는 이제 `warn-EmailPilotAI.txt`의 `backports` 누락을 검사하고, `smoke_portable_exe.ps1`를 호출해 packaged exe가 `--no-window` 기준 `/jobs/current` endpoint를 실제로 띄우는지 확인한다.
- 사용자 기준 실행 경로는 계속 `EmailPilotAI.exe` 하나로 유지하고, reverse SSH 스크립트는 개발자 원격 빌드/지원용으로만 다룬다.

### 2026-04-08 | Human + Codex | feature harness smoke와 Windows CI portable exe 경로 추가

- `runtime/cli.py`에 `feature-check-all`, `feature-harness-smoke`를 추가해 현재 feature 카탈로그를 전량 prerequisite 점검하고 sample workspace smoke를 한 번에 돌릴 수 있게 했다.
- `app/ui_smoke.py`를 추가해 홈, 설정, 리뷰센터, 관리도구, workbook 재반영 background job까지 `TestClient` 기준으로 반복 검증할 수 있게 했다.
- 당시에는 GitHub Actions 기반 Windows artifact 경로도 열었지만, 현재 active tracked 기준에서는 workflow scope 제약 때문에 CI workflow 파일을 canonical 경로에서 제외했다.
- `runtime/docs/환경/feature_harness.md`와 `app/packaging/README.md`를 smoke/packaging 절차의 공식 위치로 정리했다.

### 2026-04-08 | Human + Codex | 포터블 exe 기준과 기능 전수 테스트 구조 도입

- `docs/feature_catalog.md`와 `runtime/feature_registry.py`를 추가해 현재 제품/운영 기능의 canonical 카탈로그를 만들었다.
- 기능별 `UI / 관리도구 / CLI` 접근점을 고정하고, `feature_runs` 실행 이력을 `state/state.sqlite`에 남기도록 정리했다.
- `app`에는 관리도구 화면을 추가해 기능 목록, prerequisite check, 최근 실행 결과, 실행 버튼을 한곳에서 보게 했다.
- `runtime/cli.py`는 `feature-list`, `feature-inspect`, `feature-check`, `feature-run`, `create-sample-workspace` 명령을 지원하게 됐다.
- `runtime/sample_workspace.py`를 추가해 실메일과 API key 없이도 리뷰센터, dedupe, workbook 재반영을 검증할 수 있는 repo-safe sample save를 만들게 했다.
- `app/static/` 로컬 자산과 `app/packaging/EmailPilotAI.spec`, `build_portable_exe.ps1`, `requirements-dev.txt`를 추가해 오프라인 포터블 exe 기준을 세웠다.
- 이 서버에서는 Windows exe 자체를 빌드하지 않았고, 대신 샘플 워크스페이스 생성과 feature CLI, app/server py_compile까지 검증했다.

### 2026-04-08 | Human + Codex | Windows 데스크톱 리뷰센터와 공유 워크스페이스 save v1 도입

- `runtime/`에 공유 워크스페이스 manifest, 암호화 secret blob, sqlite state, write lock, CLI, sync orchestration을 추가했다.
- `app/`에 FastAPI 기반 로컬 UI와 pywebview launcher를 추가해 `세이브 파일 불러오기 -> 설정 -> 동기화 -> 통합 리뷰센터` 흐름 골격을 만들었다.
- 공유 save는 `workspace.epa-workspace.json + secure/secrets.enc.json + state/state.sqlite + locks/write.lock + profile/` 구조를 기본으로 잡았고, bundle/로그/workbook 링크는 workspace 상대경로만 저장하게 했다.
- 운영 workbook은 stable path `운영본_기업_신청서_모음.xlsx`로 다시 쓰고, `검토_인덱스` 시트를 함께 추가하는 재구성 경로를 넣었다.
- 정적 HTML review board는 fallback/debug 산출물로 남기고, 사용자 검토의 active canonical 상태는 runtime state DB와 app 리뷰센터가 맡도록 방향을 고정했다.

### 2026-04-08 | Human + Codex | 전체 inbox backfill과 triage review board 추가

- `mailbox`에 실제 계정 `INBOX` 전체를 read-only로 순회하며 runtime bundle을 채우는 backfill smoke를 추가했다.
- 전체 bundle을 최신 prompt 기준으로 재분석해 `application / not_application / needs_human_review` 3분류로 나누고, `application` 중 기업/연락처 신호가 있는 메일만 workbook에 자동 반영하는 batch review 경로를 추가했다.
- 사람 검토용 결과물은 sibling runtime 경로 아래 `로그/review/`의 HTML 보드와 JSON report로 남기고, 각 메일에서 `summary.md`, `preview.html`, `extracted_record.json`, `projected_row.json`으로 바로 이동할 수 있게 했다.
- 이 단계부터 현재 검증 주경로는 `이메일 수신 -> 구조화 분석 -> triage 검토 -> Excel 출력`으로 읽는다.
- 실제 full INBOX backfill 기준 `4690`개 메시지를 read-only로 처리했고, 기존 bundle `1582`건을 skip하면서 새 bundle `3108`건을 추가 materialize해 총 valid runtime bundle `4692`건을 확보했다.
- latest full review board 결과는 `application=155`, `not_application=4526`, `needs_human_review=11`, `exported=153`, `failed=0`이었다.
- 최종 사람 검토용 산출물은 sibling runtime 경로의 `260408_1505_inbox_review_board.html`, `260408_1505_inbox_review_board.json`, `260408_1505_기업_신청서_모음.xlsx`다.
- review board를 전량 실행하는 과정에서 ZIP 내부 손상 XLSX와 HEIC 첨부 때문에 생기던 예외를 잡아, attachment summary fallback과 unsupported image skip 경로로 안정화했다.

### 2026-04-08 | Human + Codex | real bundle 품질 보정과 regression smoke 추가

- `analysis`에 전시회/안내형 메일 후처리 보정 로직을 추가해, direct application 형식이 아닌 real bundle에서도 `company_name`, `product_or_service`, `application_purpose`, `request_summary`를 best-effort로 채우도록 했다.
- 추출 prompt도 안내형 메일에서 업무형 필드를 비워 두지 않도록 보강했다.
- `analysis/real_bundle_quality_smoke.py`를 추가해 같은 real bundle에 대해 analysis 결과, projected row, unresolved 컬럼, summary 존재 여부를 한 번에 점검하도록 했다.
- 현재 baseline real bundle 1건에서는 `missing_expected_fields = 0`, `unresolved_columns = 0`까지 확인했다.
- 다음 품질 단계는 같은 기준을 real bundle 2건 이상으로 늘려, 특정 메일 유형에만 맞춘 개선이 아닌지 확인하는 것이다.

### 2026-04-08 | Human + Codex | real bundle analysis/export handoff 검증

- 방금 저장한 최신 real bundle 1건을 기준으로 `analysis/materialized_bundle_smoke.py`와 `analysis/materialized_bundle_pipeline_smoke.py`를 실제 실행해 `ExtractedRecord` 생성과 workbook append까지 확인했다.
- analysis smoke는 runtime `extracted_record.json`을 남겼고, pipeline smoke는 runtime `projected_row.json`과 새 결과 workbook을 남겼다.
- handoff 과정에서 `analysis/materialized_bundle_smoke.py`가 직접 스크립트 실행 시 relative import로 실패하던 문제를 고쳐 CLI 진입이 바로 되도록 맞췄다.
- 첫 real bundle 품질 확인 결과 `contact_name`, `phone_number`, `email_address`, `website_or_social`, `industry`, 소개/사업내용 요약은 채워졌고 workbook append도 성공했다.
- 다만 `company_name`, `product_or_service`, `application_purpose`, `request_summary`는 이번 메일 성격상 또는 현재 추출 규칙 한계로 비어 있어, 다음 개선 초점은 real bundle 기준 unresolved export 컬럼과 summary 품질 보강으로 잡는다.

### 2026-04-08 | Human + Codex | 실제 이메일 연동 1단계 완료

- `mailbox`에 local-only 계정 정보 loader를 추가해 sibling `secrets` 아래의 로컬 계정 문서에서 이메일 주소, 로그인 id, 비밀번호, 프로필 루트를 읽게 했다.
- mailbox auth probe는 명시된 로그인 id를 먼저 시도하고, 실패하면 이메일 주소로 자동 fallback 하도록 확장했다.
- generic host 패턴만으로 잡히지 않는 계정을 위해 MX 레코드 기반 mail host 후보 생성 경로를 추가했다.
- 실제 최신 메일 1건 fetch는 IMAP read-only `BODY.PEEK[]` 기준으로 구현했고, 결과를 로컬 runtime bundle 아래 `raw.eml`, `preview.html`, `normalized.json`, `summary.md`, `attachments/` 구조로 저장했다.
- tracked 문서에는 실제 주소, 비밀번호, 메일 원문을 남기지 않고, 성공 bundle과 report는 모두 sibling `../secrets/사용자 설정/<이름>/실행결과/` 아래 로컬 경로에만 남겼다.
- 성공한 bundle 1건에 대해 `normalized.json` 재읽기까지 확인해 다음 analysis smoke로 넘길 준비를 마쳤다.

### 2026-04-08 | Human + Codex | 골든 레퍼런스 기반 운영 문서 체계로 재편

- 기준 문서는 골든 레퍼런스 운영 팩과 기존 legacy canonical 문서 묶음, 각 모듈 `README.md`였다.
- 기존 레포는 legacy status 중심 체계였고, 새 운영 기준은 루트 `AGENTS.md`, 루트 `README.md`, 프로젝트 `docs/logbook.md`, 모듈 `docs/logbook.md`, repo-local skill, 운영 tool, starter template을 중심으로 다시 세우는 방향으로 정리했다.
- 골든 레퍼런스의 원본 프로젝트 도메인 표현은 남기지 않고, 현재 이메일 자동화 프로젝트 기준으로 전면 재작성했다.
- 기존 legacy canonical 문서와 기존 최근 로그는 active에서 내리고 `docs/logbook_archive/`에 legacy archive로 보존했다.
- 새 canonical 경로는 `AGENTS.md`, `README.md`, `docs/logbook.md`, 각 모듈 `README.md`, 각 모듈 `docs/logbook.md`로 고정했다.
- 반복 절차를 repo-local skill 8종으로 옮겼고, 누락되어 있던 `directory_inventory.py`, `logbook_archive_guard.py`, `logbook_archive_all.py`, `git_sync_all.sh`를 현재 레포 기준 대체 구현으로 추가했다.
- 새 저장소에 복사해 쓸 수 있는 generic 운영 팩은 `templates/codex_starter/`에 따로 정리했다.
- local private boundary의 시작 문서는 sibling `../secrets/README.local.md`로 세웠다.

### 2026-04-08 | Human + Codex | legacy 운영 문서 archive 정리

- 이전 active 기준 문서 묶음과 기존 최근 로그를 `docs/logbook_archive/` 아래로 보존했다.
- 기존 최근 로그 전문은 `logbook_260408_0956_legacy_recent_log.md`에 그대로 보관했다.
- legacy canonical 문서의 핵심 판단과 경로는 `logbook_260408_0956_pre_golden_refactor_summary.md`로 묶어 현재 체계에서 다시 읽을 수 있게 정리했다.

### 2026-04-08 | Human + Codex | 산출물 경계 예시와 미래 계층 도입 규칙 명확화

- 문서 체계가 바뀐 뒤에도 `repo 내부 결과물`과 `실사용 runtime 결과물`의 경계가 아직 추상적으로 보일 수 있어, 실제 예시를 추가해 기준을 더 분명하게 적었다.
- 실제 inbox bundle, 실제 workbook, 실제 usage log는 계속 sibling `../secrets/사용자 설정/<이름>/실행결과/`에 두고, 재현 가능한 small smoke 보고서와 diff summary만 repo 내부 공식 위치 후보를 쓰는 기준을 다시 적었다.
- `app/`과 `runtime/`은 이름만 먼저 정해 두고, 실제 코드가 처음 들어가는 턴에만 디렉토리를 만들며 같은 턴에 `README.md`와 `docs/logbook.md`를 함께 연다는 규칙도 추가했다.

### 2026-04-08 | Human + Codex | 골든 레퍼런스 검토 폴더 정리

- 골든 레퍼런스의 운영 규칙, skill, tool, starter template 내용을 현재 레포 기준으로 모두 옮긴 뒤, 상위 워크스페이스에 임시로 두었던 `새로 업데이트된 문서 정책 골든 레퍼런스` 폴더를 삭제했다.
- 이후 기준 문서는 현재 레포의 `AGENTS.md`, `README.md`, `docs/logbook.md`, `.agents/skills/`, `tools/`, `templates/codex_starter/`만 보면 된다.
