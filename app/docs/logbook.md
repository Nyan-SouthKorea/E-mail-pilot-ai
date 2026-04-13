# App Logbook

> 이 문서는 `app` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 작업 시작 게이트와 읽기 순서는 root `AGENTS.md`를 따른다.

## 현재 스냅샷

- 로컬 FastAPI 서버와 pywebview launcher가 있다.
- 워크스페이스 열기/생성, 설정, 통합 리뷰센터, 동기화 시작 버튼이 있다.
- 관리도구 화면에서 현재 feature 카탈로그와 직접 실행 가능한 smoke/debug 기능을 보여준다.
- 리뷰센터는 sqlite state DB 기준으로 triage, dedupe, 대표 export 상태를 보여준다.
- 원본 열기 링크는 workspace 상대경로를 기준으로 OS 파일 열기를 시도한다.
- `app/ui_smoke.py`로 핵심 화면과 재반영 버튼까지 반복 검증할 수 있다.
- Windows portable exe는 Windows host build script 기준으로 빌드하고 `D:\EmailPilotAI\portable\EmailPilotAI\`에 단일 publish 한다.
- 공식 사용자 실행 경로는 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe` 하나다.
- 홈은 3단계 시작 마법사 + 세이브 오픈 후 작업 대시보드 2상태로 운영하고, 설정은 기본/고급, 동기화는 quick/full, 리뷰는 카드형 확장 리스트 기준으로 본다.

## 현재 활성 체크리스트

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
- [ ] 진행률 표시와 장시간 sync 폴링 UX 보강

## 최근 로그

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
