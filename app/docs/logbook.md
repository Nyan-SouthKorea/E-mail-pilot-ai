# App Logbook

> 이 문서는 `app` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 작업 시작 게이트와 읽기 순서는 root `AGENTS.md`를 따른다.

## 현재 스냅샷

- 로컬 FastAPI 서버와 pywebview launcher가 있다.
- 워크스페이스 열기/생성, 설정, 통합 리뷰센터, 동기화 시작 버튼이 있다.
- 최근 세이브 바로 다시 열기, 세이브 닫기, 다른 세이브 열기, 마지막 세이브 자동 재개가 있다.
- 관리도구 화면에서 현재 feature 카탈로그와 직접 실행 가능한 smoke/debug 기능을 보여준다.
- 리뷰센터는 sqlite state DB 기준으로 triage와 자동 canonical selection 결과, 엑셀 반영 대상 상태를 보여준다.
- 원본 열기 링크는 workspace 상대경로를 기준으로 OS 파일 열기를 시도한다.
- `app/ui_smoke.py`로 핵심 화면과 재반영 버튼까지 반복 검증할 수 있다.
- Windows portable exe는 Windows host build script 기준으로 빌드하고 `D:\EmailPilotAI\portable\EmailPilotAI\`에 단일 publish 한다.
- 공식 사용자 실행 경로는 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe` 하나다.
- 홈은 3단계 시작 마법사 + 세이브 오픈 후 작업 대시보드 2상태로 운영하고, 설정은 기본/고급, 동기화는 quick/full, 리뷰는 페이지 기반 목록 + 우측 상세패널 기준으로 본다.
- 새 세이브는 v2 영문 구조를 만들고, `찾아보기`는 pywebview native dialog를 우선 시도하고 필요 시 diagnostics route로 fallback 한다.
- 동기화 범위는 `최근 10 / 100 / 500 / 1000 / 직접 입력 / 전체` 프리셋을 지원한다.

## 현재 활성 체크리스트

- [x] blocker hotfix: picker self-test / server-side diagnostics route 도입
- [x] blocker hotfix: quick sync `notes referenced before assignment` 예외 복구
- [x] blocker hotfix: pushed head 기준 Windows 재빌드와 실제 exe blocker 재검증
- [x] 데스크톱 셸과 로컬 Web UI 골격 도입
- [x] 세이브 파일 불러오기 / 새 워크스페이스 만들기 화면 도입
- [x] 설정 화면과 저장 위치 안내 도입
- [x] 통합 리뷰센터 기본 리스트 화면 도입
- [x] 관리도구 화면과 feature run 연결
- [x] 오프라인 static 자산과 포터블 exe spec 추가
- [x] UI smoke와 Windows CI runner build workflow 추가
- [x] Windows packaged smoke와 `backports.tarfile` 기반 부팅 복구 기준 추가
- [x] 세이브 파일 파일탐색기 선택과 세이브 파일 가이드 추가
- [x] 설정 저장 성공/실패 배너와 마지막 저장 요약 추가
- [x] 관리도구 렌더링 예외 복구와 Windows host 실제 빌드 smoke 정리
- [x] Windows build -> Linux 공유 미러 운영 스크립트와 Samba 실행 기준 정리
- [x] portable bundle manifest, 필수 DLL 검사, 공식 로컬 cache fallback helper 추가
- [x] `AGENTS.md` 재독 게이트를 `/plan`, 실행 직전, 완료 직전까지 명시적으로 강화
- [x] onedir 수동 복사 기준과 build 부산물 cleanup helper 정리
- [x] 파일 탐색기 브리지 상태 기계와 로컬 실행 전용 정책 정리
- [x] Windows 로컬 D 단일 실행본 publish와 C/D/Z 포터블 산출물 cleanup 정리
- [x] 서비스형 홈/동기화/설정/리뷰 UI 1차 개편
- [x] 세이브 파일 가이드 모달과 외부 사용자 가이드 분리
- [x] 계정 연결 확인, 폴더 추천, quick/full sync 화면 도입
- [x] 첫실행 홈을 3단계 마법사 구조로 재설계
- [x] 찾아보기 버튼을 기본 활성 + 클릭 시도 방식으로 전환
- [x] 프로앱 디자인 토큰과 제품형 쉘 적용
- [x] 리뷰/동기화/설정 화면의 고객용 카피와 레이아웃 정리
- [x] 최근 세이브 바로 다시 열기와 세이브 닫기/전환 UX 추가
- [x] 설정 도움말 tooltip/popover와 진행 카드 UX 추가
- [x] 진행률 표시와 장시간 sync 폴링 UX 보강
- [x] picker self-test / pick-folder / pick-file route 도입
- [x] sync 최근 N 프리셋 UI와 서버 파라미터 반영
- [x] launcher `/app-meta` 확인과 동적 포트 fallback 도입
- [x] pushed head 기준 Windows 공식 exe 재빌드와 packaged smoke 재검증
- [x] 실제 세이브 기준 Windows quick sync 자동 검증
- [ ] Windows 실제 native dialog 수동 acceptance
- [ ] launcher app-meta 확인 포함 Windows 공식 exe 최종 acceptance
- [x] 리뷰센터를 페이지 기반 목록 + 우측 상세패널로 전환
- [x] 리뷰 필터/페이지/선택 상태 유지와 외부 파일 열기 복귀 경로 정리
- [x] 한국어 artifact 용어와 엑셀 보조화 패널 정리
- [x] service/CLI 전환 완료 기준으로 app 문서/diagnostics 문구 최종 정리
- [ ] Windows 실제 native dialog 수동 acceptance 재확인
- [x] 리뷰 상세 외부 열기 후 필터/페이지/선택 상태 보존 강화
- [x] build commit / build time / 공식 exe 경로를 고급 진단에 노출
- [x] review 첫 진입 기본 artifact를 `검토 개요`로 바꿔 무거운 iframe 선로딩 제거
- [ ] 공식 Windows exe 재빌드 후 최신 UI/CTA/리뷰 반영 수동 확인

## 최근 로그

### 2026-04-13 | Human + Codex | review detail 기본 탭 경량화와 partial history 보정

- review 상세패널의 기본 artifact를 `검토 개요`로 바꾸고, 첫 진입 시에는 파일 iframe 대신 가벼운 상태 요약만 먼저 보여주게 했다.
- 목록 row와 상세 탭의 htmx partial update는 이제 `/review/detail`이 아니라 현재 `/review` query 상태를 browser URL로 유지한다.
- 즉, 상세를 바꾸더라도 필터/정렬/페이지/선택 bundle 맥락이 히스토리에 남고, 외부 파일 열기 후에도 같은 review 상태로 돌아오기 쉬운 구조로 다시 맞췄다.
- `찾아보기`는 pywebview bridge를 우선 사용하고, bridge가 바로 붙은 경우 `desktop_ready`를 즉시 판정하도록 JS에서 다시 보강했다.
- Windows packaged smoke는 `/app-meta`의 build metadata가 비어 있는 문제를 다시 잡아냈고, `portable_build_info.json`을 UTF-8 without BOM으로 쓰고 읽는 방향으로 packaging helper를 보강했다.

### 2026-04-13 | Human + Codex | 리뷰센터를 페이지 기반 목록 + 상세패널로 재편

- `review` 화면을 전체 카드 렌더에서 페이지 기반 목록 + 우측 상세패널 구조로 바꿨다.
- 기본 50건만 먼저 렌더링하고, 상세는 선택한 메일만 따로 읽어 앱 안 미리보기 탭으로 보여준다.
- `대표 export만`을 `엑셀 반영 대상만`으로 바꾸고, 원본/산출물 버튼은 한국어 이름으로 정리했다.
- 외부 파일 열기 뒤에도 필터/페이지/선택 상태가 유지되도록 `return_to`와 URL query 보존 흐름을 도입했다.
- `찾아보기`는 pywebview native dialog를 우선 시도하도록 bridge를 보강했다.

### 2026-04-13 | Human + Codex | 리뷰 상태 유지와 build metadata 진단 강화

- 리뷰 목록 row 자체도 선택 가능하게 바꾸고, 상세패널 partial swap 뒤 현재 선택 행을 다시 강조하게 했다.
- 외부 파일 열기와 artifact 탭 전환 전후의 현재 리뷰 URL/스크롤을 세션 상태로 기억해, 화면 맥락이 최대한 유지되도록 보강했다.
- 홈/설정/고급 도구의 진단 패널에 `build commit`, `build time`, `공식 실행 파일`을 함께 노출해, stale exe 여부를 눈으로 바로 확인할 수 있게 했다.

### 2026-04-13 | Human + Codex | Windows 공식 exe 재빌드와 실제 세이브 quick sync 자동 검증

- `build_windows_portable_and_publish.sh --clean`을 pushed head 기준으로 다시 실행했고, 공식 runtime `D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe`를 최신 코드로 다시 publish 했다.
- packaged smoke는 `/jobs/current`, `/app-meta`, GUI startup log를 모두 통과했다.
- startup log에는 `preferred port 8765 is occupied by another process`, `selected fallback port 51051`, `confirmed app-meta at http://127.0.0.1:51051`이 남아, 다른 로컬 앱과의 포트 충돌을 자동으로 피해 간 것을 확인했다.
- Windows service self-test로는 `diagnostics picker-bridge`가 `powershell-native`, `native_dialog_supported=true`로 통과했다.
- 실제 저장된 세이브 기준 `run_pipeline_sync_service(scope='recent', limit=10)`도 Windows에서 직접 실행해 `status=completed`, `skipped_existing_count=10`까지 확인했다.
- 따라서 자동 검증 범위 안에서 남아 있는 blocker는 아니고, 실제 사용자가 `찾아보기`를 눌렀을 때 폴더 선택창이 보이는지의 수동 acceptance만 남았다.

### 2026-04-13 | Human + Codex | Windows picker blocker 재추적: 고정 포트 충돌과 stale exe 원인 확인

- 사용자 검증에서는 `찾아보기`가 여전히 안 열렸고, 역추적 결과 Windows localhost의 고정 포트 `8765`에 다른 앱 `voice_clone_desktop_sidecar`가 붙어 있을 수 있음을 확인했다.
- 따라서 기존 launcher는 올바른 FastAPI 앱이 아니라 다른 로컬 앱에 연결될 가능성이 있었고, 이 경우 최신 diagnostics/picker 코드가 있어도 실제 창은 오래된 동작처럼 보일 수 있었다.
- `app/server.py`에는 `/app-meta`를 추가해 현재 창이 실제 Email Pilot AI 서버인지 확인할 수 있게 했고, `app/main.py`는 포트가 점유돼 있으면 다른 로컬 포트를 자동 선택한 뒤 `/app-meta`의 `app_id=email_pilot_ai_desktop`를 확인해야만 창을 연다.
- `app/packaging/smoke_portable_exe.ps1`도 `/jobs/current`뿐 아니라 `/app-meta`까지 검사하게 바꿨고, GUI startup log에는 `launcher: confirmed app-meta ...` 로그가 남아야 packaged smoke를 통과한다.
- 이 수정은 아직 local batch 상태이므로, current plan commit/push 후 Windows 공식 exe를 다시 빌드해야 사용자 눈검증과 실제 picker acceptance를 닫을 수 있다.

### 2026-04-13 | Human + Codex | picker route와 sync 프리셋 기준으로 app wrapper 재정리

- `app/static/js/app.js`는 더 이상 pywebview bridge 존재 여부만 보고 `찾아보기` 가능 여부를 추정하지 않고, 로컬 서버의 diagnostics route를 호출해 picker self-test와 실제 pick 요청을 보낸다.
- 홈/설정의 `찾아보기`는 경로 선입력 없이도 route 호출을 먼저 시도하고, 실패 시 인라인 상태 메시지와 직접 입력 대안을 보여준다.
- `/sync` 화면은 `최근 10 / 100 / 500 / 1000 / 직접 입력 / 전체` 범위를 선택하게 바뀌었고, 서버도 같은 계약으로 받는다.
- `app.ui_smoke`는 picker diagnostics route, picker folder route, sync preset UI까지 자동 검증한다.

### 2026-04-13 | Human + Codex | blocker hotfix 완료

- `app/main.py`는 pywebview 창 생성 직후 서버 상태를 `desktop_ready`로 올리지 않고 `desktop_pending`으로 유지해, 브리지 준비 오진을 줄였다.
- `app/static/js/app.js`는 `dialog_capabilities`, `pick_folder`, `pick_file` 3개 메서드가 모두 붙었는지 확인하는 브리지 준비 판정을 추가했고, `찾아보기` 클릭 시 입력칸이 비어 있어도 바로 브라우징을 시도하게 바꿨다.
- 브리지 호출이 아직 준비되지 않았거나 실패하면 사용자는 죽은 버튼이 아니라 짧은 인라인 실패 안내를 보게 된다.
- `app/server.py`의 sync partial-success 카드 문구는 raw Python 예외를 전면에 노출하지 않고, `메일 저장 완료 / 실패 단계 / 다음 행동 / 기술 상세` 순으로 정리했다.
- `app/ui_smoke.py`는 홈/설정의 `찾아보기` 버튼이 기본 disabled가 아닌지까지 확인하도록 다시 강화했고, Windows packaged smoke는 pywebview bridge attach 로그도 함께 검사한다.
- Windows 공식 실행본 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`는 이 hotfix 기준으로 다시 빌드했다.

### 2026-04-13 | Human + Codex | blocker hotfix 착수

- 현재 사용자 blocker를 `찾아보기` 브리지 복구와 quick sync `notes` 예외 복구로 다시 좁혔다.
- 브리지 쪽은 런처가 `desktop_ready`를 너무 일찍 선언하고, 프런트엔드가 `window.pywebview.api` 객체 존재만으로 준비 완료로 보던 점을 원인 후보로 확정했다.
- quick sync 쪽은 `analysis/inbox_review_board_smoke.py`의 `bundle_limit` 경로에서 `notes`를 초기화하기 전에 `notes.append(...)`가 먼저 호출되는 결함을 확인했다.

### 2026-04-13 | Human + Codex | 고객 서비스형 UI/세이브 구조 리팩터 v3

- 홈의 최근 세이브 영역을 `이 PC에서 바로 다시 열기`와 `암호를 확인한 뒤 다시 열기` 두 흐름으로 정리해, 최근 항목이 실제로 클릭 가능한 행동이 되도록 고쳤다.
- `설정`과 `동기화` 화면의 job 진행 카드는 상태, 현재 단계, 진행률, 다음 행동, 세부 로그를 함께 보여주는 실제 서비스형 진행 카드로 정리했다.
- `(i)` 버튼과 disabled CTA 이유 안내는 공통 tooltip/popover로 묶고, `계정 연결 확인`, `비밀번호 또는 앱 비밀번호`, `로그인 ID`, `엑셀 양식` 도움말을 같은 방식으로 노출하게 했다.
- 고객용 UI 용어를 `세이브 파일`, `기본 받은편지함`, `엑셀 양식` 중심으로 다시 다듬고, 홈/설정/동기화의 긴 설명 대신 다음 행동 위주 안내로 줄였다.
- 앱 브랜딩 자산으로 네이비/청록 기준 로고 마크를 추가했고, sidebar 브랜드와 favicon, Windows exe 아이콘 자산을 같은 계열로 맞췄다.
- `app.ui_smoke`는 최근 세이브 바로 다시 열기까지 포함해 다시 통과했고, 핵심 화면과 job polling 흐름을 계속 반복 검증할 수 있는 상태를 유지했다.

### 2026-04-13 | Human + Codex | 서비스형 고객 UI 리팩터 v2

- 홈 미오픈 상태를 `기존 세이브 열기 / 새 세이브 만들기` 탭이 있는 3단계 시작 마법사로 재구성했다.
- `찾아보기` 버튼은 exe 기준에서 기본 클릭 가능 상태로 두고, pywebview 연결이 늦을 때는 내부 재시도 후 짧은 실패 안내를 보여주게 바꿨다.
- 앱 셸은 `좌측 사이드바 + 상단 작업 헤더` 구조로 바꾸고, 메뉴 순서를 `홈 / 동기화 / 리뷰 / 설정 / 고급 도구`로 정리했다.
- 디자인 토큰을 슬레이트/네이비 기반 업무용 프로앱 톤으로 교체하고, 홈/설정/동기화/리뷰의 카피를 고객용 흐름 중심으로 다시 정리했다.
- 세이브 파일 오픈/생성 후에는 `/settings`로 이어지게 바꿔, 첫실행 Step 2인 계정 연결 설정으로 곧바로 넘어가게 했다.
- `app/ui_smoke.py`는 새 홈 문자열과 활성화된 `찾아보기` 버튼 기준을 검사하도록 갱신했고, 샘플 세이브 기준 smoke를 다시 통과했다.

### 2026-04-13 | Human + Codex | Windows 빌드 소스 stale 문제 복구

- 사용자 피드백 기준으로 실제 실행 중인 프로세스 경로와 runtime bundle의 템플릿 내용을 확인해 보니, 공식 D runtime exe 자체는 맞았지만 Windows 빌드 미러 `D:\EmailPilotAI\repo`가 예전 소스로 남아 있던 것이 원인이었다.
- Windows 빌드 미러를 최신 `main` 기준 소스로 다시 맞춘 뒤 `build_portable_exe.ps1 -Clean`을 재실행했고, `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`를 새 UI 기준으로 다시 publish 했다.
- `build_windows_portable_and_publish.sh`는 이제 Windows 빌드 전에 Git 기준 mirror sync를 먼저 수행하고, `publish_portable_to_runtime.ps1`는 공식 runtime 프로세스를 정리한 뒤 교체하도록 보강했다.

### 2026-04-10 | Human + Codex | Windows 로컬 D 단일 실행본 publish와 cleanup 재정리

- `runtime.local_settings`의 공식 portable 경로를 `D:\EmailPilotAI\portable\EmailPilotAI\`로 바꾸고, 앱 진단에는 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`를 공식 실행 파일로 보여주게 했다.
- frozen exe preflight는 이제 공유 드라이브/UNC뿐 아니라 repo 내부 `dist/` 임시 산출물이나 비공식 복사본에서의 실행도 차단하고, 세이브 파일은 공유 폴더에서 열 수 있지만 exe는 D 경로에서만 실행하라는 메시지를 띄운다.
- `publish_portable_to_runtime.ps1`를 추가해 최신 `dist\EmailPilotAI` bundle만 D runtime 폴더로 publish 하고, manifest 비교와 packaged smoke를 같은 흐름에서 수행하게 했다.
- `build_portable_exe.ps1`는 publish 성공 후 `repo\build\EmailPilotAI`, `repo\dist\EmailPilotAI`, `repo\dist\windows-portable\EmailPilotAI`, `%LOCALAPPDATA%\EmailPilotAI\portable\EmailPilotAI`를 지워서 오래된 실행본이 다시 남지 않게 했다.
- A100 원격 빌드 helper는 `build_windows_portable_and_publish.sh`로 교체했고, Linux repo의 `dist/windows-portable/EmailPilotAI`도 기본 cleanup 대상으로 바꿨다.
- 샘플 워크스페이스 기준 `app.ui_smoke`를 다시 통과시켰고, Windows 실제 빌드 후 `D:\EmailPilotAI` 아래 `EmailPilotAI.exe`는 공식 runtime 1개만 남는 것도 확인했다.

### 2026-04-10 | Human + Codex | 서비스형 UI 1차 전환

- 홈 화면을 `세이브 파일 열기/만들기 -> 계정 연결 -> 빠른 테스트 동기화 -> 전체 동기화 -> 리뷰` 순서가 보이는 서비스형 대시보드로 재구성했다.
- `세이브 파일 가이드`는 홈에서 바로 여닫는 모달로 먼저 제공하고, 기존 guide route는 fallback 문서 경로로 유지했다.
- 설정은 기본/고급으로 분리했고, 모델 선택형 UI와 `계정 연결 확인` 버튼, 폴더 목록 추천, 템플릿 고급 설정을 붙였다.
- 동기화는 별도 `/sync` 화면에서 `빠른 테스트 동기화`와 `전체 동기화`를 구분해 실행하게 했다.
- 리뷰센터는 테이블 대신 카드형 확장 리스트로 바꾸고, 원본 링크/분류 override/대표 메일 지정 흐름을 한 카드 안에 모았다.
- `app/ui_smoke.py`는 새 홈, sync, settings, review 구조를 기준으로 다시 통과했다.

### 2026-04-10 | Human + Codex | 파일 탐색기 브리지 복구와 로컬 실행 전용 정책 정리

- `app/main.py`에 Windows 실행 경로 preflight를 넣어, 공유 드라이브나 UNC 경로에서 직접 실행하면 `pythonnet` 예외 전에 친절한 안내 대화상자로 로컬 실행 경로와 `startup.log` 위치를 보여주고 종료하게 했다.
- 런처와 서버 사이에 `shell_mode`, `native_dialog_state`, `startup_log_path`, `official_local_bundle_path`, `unsupported_launch_reason`를 공유하는 실행 컨텍스트를 추가했다.
- 프런트엔드 `app/static/js/app.js`는 더 이상 `window.pywebview` 부재를 즉시 `브라우저 fallback`으로 단정하지 않고, `desktop_pending -> desktop_ready` 재시도 흐름과 `desktop_failed` fallback 안내를 함께 처리한다.
- 홈, 설정, 관리도구에는 `앱 실행 진단` 블록을 추가해 현재 실행 모드, 파일 탐색기 상태, 현재 실행 경로, 공식 로컬 실행 폴더, `startup.log` 위치를 바로 볼 수 있게 했다.
- `찾아보기` 버튼은 기본 비활성화 상태로 렌더링하고, `desktop_ready`일 때만 켜지게 바꿨다.
- Windows 포터블 문서는 공유 폴더를 `배포본 보관용`, 실제 실행은 `%LOCALAPPDATA%\\EmailPilotAI\\portable\\EmailPilotAI\\` 로컬 복사본으로 고정하도록 다시 정리했다.

### 2026-04-09 | Human + Codex | `python310.dll` 부팅 오류 복구와 AGENTS 재독 게이트 강화

- `EmailPilotAI.spec`에서 `UPX`를 꺼서 Windows portable onedir bundle을 안정성 우선 기준으로 다시 빌드하게 했다.
- `portable_bundle_manifest.py`를 추가해 필수 DLL 검사, sha256 manifest 생성, manifest 비교를 공용 helper로 만들었다.
- `build_portable_exe.ps1`는 이제 필수 DLL 검사와 `portable_bundle_manifest.json` 생성까지 성공해야 빌드 완료로 본다.
- `sync_portable_to_local_cache.ps1`를 추가해 공유 미러 또는 로컬 build bundle을 공식 Windows 로컬 cache 경로로 동기화하고, integrity 비교와 packaged smoke까지 한 번에 수행하게 했다.
- Samba 공유 실행에서 `python310.dll`이 `Access denied`로 막히는 증상을 반영해, Linux 공유 미러를 만들 때 `.exe`, `.dll`, `.pyd`에 실행 비트를 주도록 `mirror_portable_to_linux.sh`를 보강했다.
- onedir 수동 복사는 `dist/windows-portable/EmailPilotAI/` 폴더 전체를 통째로 옮기는 것으로 고정했고, `cleanup_portable_artifacts.sh`로 Linux repo의 혼동되는 build 부산물만 지우게 했다.
- packaging 문서와 Windows 실행 가이드는 공식 지원 경로를 `공유 폴더 직접 실행 / 공식 로컬 cache 복사본` 두 가지로 고정하고, `D:\\#EmailPilotAI` 같은 임의 수동 복사 경로는 비공식으로 정리했다.
- `AGENTS.md`, starter `AGENTS.md`, `repo-orient-and-ground`, `checklist-and-canonical-doc-sync`에는 `/plan 시작`, `실행 직전`, `완료 직전` 재독 게이트를 명시적으로 추가했다.

### 2026-04-09 | Human + Codex | Windows shared mirror와 Samba 실행 기준 정리

- `app/packaging/build_windows_portable_and_mirror.sh`와 `app/packaging/mirror_portable_to_linux.sh`를 추가해, A100에서 reverse SSH로 Windows onedir bundle을 빌드하고 Linux 공유 경로 `repo/dist/windows-portable/EmailPilotAI/`로 다시 미러링하는 운영 경로를 만들었다.
- 이 경로는 Windows SSH 세션에서 `Z:` 네트워크 드라이브가 보이지 않는 제약을 우회하기 위해, A100이 Windows 산출물을 tar 스트림으로 다시 끌어오는 방식으로 고정했다.
- `app/packaging/README.md`에는 공유 폴더 비실행, exe 위치와 세이브 파일 위치 분리, 공식 Windows 로컬 실행 기준을 정리했다.

### 2026-04-09 | Human + Codex | 세이브 파일 파일탐색기와 설정/관리도구 UX 복구

- 홈 화면에서 세이브 파일 열기/생성, 기존 profile import, 설정의 템플릿 경로에 `찾아보기` 버튼을 추가하고, Windows exe에서는 pywebview 네이티브 파일 탐색기를 쓰도록 JS bridge를 연결했다.
- 홈에 `세이브 파일 가이드`와 경로 상태 분류를 추가해, 사용자가 manifest가 있는 기존 세이브/새 세이브 가능/잘못된 경로를 바로 구분할 수 있게 했다.
- 설정 저장은 이제 성공/실패 배너와 마지막 저장 시각, 템플릿 경로 상태를 함께 보여준다.
- `/admin/features`는 packaging prerequisite 예외가 나더라도 페이지 전체가 죽지 않고 check 결과만 렌더링하도록 복구했다.
- 새 샘플 세이브 기준 `app.ui_smoke`를 다시 통과시켰고, Windows remote build도 재실행해 `EmailPilotAI.exe` packaged smoke까지 완료했다.

### 2026-04-08 | Human + Codex | 관리도구 화면과 오프라인 앱 자산 추가

- 앱 상단 내비게이션에 `관리도구`를 추가하고, 기능 카탈로그/최근 실행/직접 실행 버튼을 한 화면에 모았다.
- `review` 화면에는 `운영 workbook 재반영` 버튼과 작업 상태 strip을 추가했다.
- CDN 대신 `app/static/` 로컬 자산을 읽도록 바꿔 오프라인 UI 기준을 맞췄다.
- 포터블 exe 기준 파일은 `app/packaging/` 아래 `EmailPilotAI.spec`, `build_portable_exe.ps1`, `README.md`에 정리했다.

### 2026-04-08 | Human + Codex | UI smoke와 Windows portable exe workflow 추가

- `app/ui_smoke.py`를 추가해 홈, 설정, 리뷰센터, 관리도구, workbook 재반영 버튼까지 FastAPI `TestClient` 기준으로 반복 검증할 수 있게 했다.
- 당시에는 GitHub Actions 기반 Windows artifact 경로도 열었지만, 현재 active tracked 기준에서는 workflow scope 제약 때문에 CI workflow 파일을 canonical 경로에서 제외했다.
- Windows 포터블 build와 smoke 기준은 `app/packaging/README.md` 한 곳으로 정리했다.

### 2026-04-08 | Human + Codex | Windows exe 부팅 오류 복구와 packaged smoke 추가

- Windows `.exe`가 `pkg_resources -> setuptools._vendor.jaraco.context` 경로에서 `backports.tarfile` 누락으로 죽던 문제를 복구 기준에 반영했다.
- `requirements-dev.txt`와 `EmailPilotAI.spec`에 `backports.tarfile` 대응을 추가하고, `smoke_portable_exe.ps1`로 packaged exe의 `/jobs/current` endpoint 기동을 자동 확인하게 했다.
- 사용자 실행 기준은 `EmailPilotAI.exe` 더블클릭 하나로 고정하고, reverse SSH 스크립트는 개발자 원격 유지보수용으로만 분리한다.

### 2026-04-08 | Human + Codex | 데스크톱 리뷰센터 앱 골격 도입

- FastAPI + Jinja 템플릿 기반 로컬 UI 서버를 추가했다.
- pywebview launcher를 추가해 전용 창으로 띄우는 엔트리포인트를 만들었다.
- `세이브 파일 불러오기`, `새 워크스페이스 만들기`, `설정`, `통합 리뷰센터`, `동기화` 흐름을 앱 골격에 맞춰 연결했다.
