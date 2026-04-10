# Windows Portable EXE

이 문서는 Windows에서 검증용 포터블 exe를 만들고 확인하는 절차를 적는다.

## 읽기 순서

- 비사소한 작업 전에는 `../../../AGENTS.md -> ../../../README.md -> ../../../docs/logbook.md -> ../../../docs/feature_catalog.md -> ../../README.md -> ../logbook.md -> ./windows_portable_exe.md` 순서로 다시 읽는다.

## 현재 기준

- 출력 형태는 `PyInstaller onedir`이다.
- 목표 실행 파일은 `dist/EmailPilotAI/EmailPilotAI.exe`다.
- 최종 사용자 실행 파일은 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`다.
- UI 자산은 `app/templates/`, `app/static/`를 bundle 안에 포함한다.
- 로컬 브라우저 fallback은 디버그용이고, 사용자 검증 기준은 `pywebview` 전용 창이다.
- 사용자는 `EmailPilotAI.exe`만 실행한다. reverse SSH 터널 스크립트는 개발자 유지보수용이다.
- Linux에서 만든 ELF 산출물은 Windows에서 실행할 수 없다.
- `PyInstaller onedir`이므로 `exe` 단독 복사가 아니라 `dist/EmailPilotAI/` 폴더 전체를 같이 옮겨야 한다.
- 공식 지원 실행 경로는 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe` 하나다.
- `Z:` 공유 폴더의 exe, repo 내부 `dist/` 임시 산출물, 임의 수동 복사 폴더는 공식 지원 경로가 아니다.

## 지금 정확히 무엇을 실행하나

- 사용자가 열 파일은 아래 하나다.
  - `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`
- 이 onedir 폴더 안에는 아래 핵심 항목이 함께 있어야 한다.
  - `EmailPilotAI.exe`
  - `_internal/` 전체
  - `portable_bundle_manifest.json`
- `EmailPilotAI.exe`만 따로 떼어 실행하면 안 된다.

## Windows에서 직접 빌드

1. PowerShell에서 repo root로 이동한다.
2. 의존성을 설치한다.
   - `python -m pip install -r requirements.txt -r requirements-dev.txt`
3. 포터블 bundle을 빌드한다.
   - `powershell -ExecutionPolicy Bypass -File .\\app\\packaging\\build_portable_exe.ps1`
4. build script가 최종 실행본을 아래 경로로 publish 한다.
   - `D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe`
5. build script가 publish된 실행본 기준 packaged smoke를 자동 실행한다.
   - `app\\packaging\\smoke_portable_exe.ps1`
   - 기준:
     - `EmailPilotAI.exe --no-window`가 `/jobs/current` endpoint를 띄워야 한다.
     - 로컬 GUI 기동 후 `startup.log`에 `launcher: imported pywebview`가 남고 `launcher: pywebview failed`는 없어야 한다.
6. build script는 publish 후 아래를 정리한다.
   - `D:\\EmailPilotAI\\repo\\build\\EmailPilotAI\\`
   - `D:\\EmailPilotAI\\repo\\dist\\EmailPilotAI\\`
   - `D:\\EmailPilotAI\\repo\\dist\\windows-portable\\EmailPilotAI\\`
   - `%LOCALAPPDATA%\\EmailPilotAI\\portable\\EmailPilotAI\\`
7. build script는 필수 DLL 검사와 `portable_bundle_manifest.json` 생성도 수행한다.

## A100에서 Windows 빌드 후 로컬 실행본까지 publish

1. 사용자가 Windows에서 reverse SSH 터널 창을 열어 둔다.
2. A100 서버에서 Windows 접속이 되는지 확인한다.
   - `ssh nyan-pc-reverse whoami`
3. Windows 빌드와 로컬 publish를 한 번에 실행한다.
   - `bash ./app/packaging/build_windows_portable_and_publish.sh`
4. 이미 만들어진 Windows onedir bundle만 다시 publish할 때는 아래 helper를 쓴다.
   - `powershell -ExecutionPolicy Bypass -File .\\app\\packaging\\publish_portable_to_runtime.ps1`
5. Linux repo 안의 혼동되는 이전 공유 미러 부산물을 정리할 때는 아래 helper를 쓴다.
   - `bash ./app/packaging/cleanup_portable_artifacts.sh`

이제 `Z:` 공유 폴더는 세이브 파일 공유용으로만 쓰고, exe 보관/실행용으로는 쓰지 않는다.

## CI와 빌드 기준

- Linux 개발 서버에서는 spec과 오프라인 자산 검증만 하고, 실제 Windows exe 생성은 Windows host를 기준으로 본다.
- CI workflow는 현재 tracked 기준에서 active canonical 경로가 아니다. 자동화가 다시 필요해지면 별도 GitHub 권한 범위를 확인한 뒤 복구한다.

## 검증 기준

- 인터넷 없이도 홈, 설정, 리뷰센터, 관리도구 화면이 열려야 한다.
- `세이브 파일 불러오기`, `설정 저장`, `운영 workbook 재반영`이 동작해야 한다.
- 앱 UI smoke는 `python -m app.ui_smoke --workspace-root <path> --workspace-password <pw>`로 반복 점검한다.
- `build\\EmailPilotAI\\warn-EmailPilotAI.txt`에 `missing module named backports`가 남아 있으면 build 실패로 본다.
- `dist\\EmailPilotAI\\portable_bundle_manifest.json`이 생성되고, 필수 DLL 검사도 pass 해야 한다.

## Samba와 세이브 파일 기준

- `Z:` 공유 폴더의 exe는 실행하지 않는다.
- 실제 실행은 항상 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`를 기준으로 한다.
- 이때 앱 내부 FastAPI 서버는 Linux 개발 서버를 쓰지 않고, exe를 실행한 Windows 프로세스 안에서 로컬로 뜬다.
- 서버와 Windows exe가 같은 결과를 보려면 같은 세이브 파일 폴더를 열어야 한다.
  - 추천: 공유 폴더 안의 `shared_saves/<이름>/` 또는 동등한 전용 세이브 폴더
- exe 위치와 세이브 파일 위치는 분리한다.
  - exe는 Windows 로컬 D 경로
  - 세이브 파일은 공유 폴더 안의 같은 workspace
- 공유 폴더 직접 실행은 `pythonnet / Python.Runtime.dll` 계층에서 불안정하므로 공식 지원 경로에서 제외한다.

## 어떤 폴더가 불필요한가

- 아래는 build 과정에서 생긴 로컬 부산물이라 지워도 된다.
  - `build/EmailPilotAI/`
  - `dist/EmailPilotAI/`
  - `dist/windows-portable.precheck/`
  - `dist/windows-portable/.portable-mirror.*/`
  - `dist/windows-portable/EmailPilotAI/`
  - `%LOCALAPPDATA%\\EmailPilotAI\\portable\\EmailPilotAI\\`
- 아래는 지우면 안 된다.
  - `D:\\EmailPilotAI\\portable\\EmailPilotAI\\`
