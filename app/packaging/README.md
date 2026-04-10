# Portable EXE Packaging

이 폴더는 Windows에서 검증용 포터블 exe를 만드는 기준 파일을 둔다.

현재 기준:

- 출력 형태: `PyInstaller onedir`
- 최종 실행 파일: `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`
- UI 자산: `app/templates/`, `app/static/`를 exe bundle 안에 포함
- 목표: 인터넷 없이도 전용 창 UI가 뜨는 검증용 포터블 bundle
- 사용자 기준 실행 방법은 `EmailPilotAI.exe` 더블클릭 하나다.
- reverse SSH 터널 스크립트는 앱 실행용이 아니라 개발자 원격 빌드/지원용 도구다.
- `PyInstaller onedir`이므로 `EmailPilotAI.exe`만 따로 옮기지 않고 `dist/EmailPilotAI/` 폴더 전체를 함께 다룬다.
- 공식 지원 경로는 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe` 하나다.
- `Z:` 공유 폴더의 exe, repo 내부 `dist/` 임시 산출물, 임의 수동 복사 폴더는 공식 지원 경로가 아니다.

정확히 무엇을 실행하나:

- 사용자가 여는 파일은 아래 하나다.
  - `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe`
- 같은 폴더 안에 아래 핵심 항목이 함께 있어야 한다.
  - `EmailPilotAI.exe`
  - `_internal/` 전체
  - `portable_bundle_manifest.json`
- `portable_bundle_manifest.json`은 런타임 필수 파일은 아니지만, 같은 bundle인지 검증하는 기준 파일이므로 그대로 유지한다.
- `EmailPilotAI.exe`만 단독 복사하는 방식은 지원하지 않는다.

빌드 순서:

1. Windows PowerShell에서 repo root로 이동한다.
2. 필요하면 개발 의존성을 설치한다.
   - `python -m pip install -r requirements.txt -r requirements-dev.txt`
3. 빌드를 실행한다.
   - `powershell -ExecutionPolicy Bypass -File .\\app\\packaging\\build_portable_exe.ps1`
4. build script는 최종 실행본을 아래 경로로 publish 한다.
   - `D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe`
5. build script가 끝나면 publish된 실행본 기준 packaged smoke가 자동으로 실행된다.
   - `--no-window` endpoint smoke
   - 로컬 GUI startup log smoke
6. build script는 필수 DLL 존재 검사, `portable_bundle_manifest.json` 생성, 기존 C/D 임시 산출물 cleanup까지 함께 수행한다.

Linux에서 Windows 빌드와 로컬 publish를 한 번에 처리할 때:

1. A100 서버에서 reverse SSH alias가 살아 있는지 확인한다.
   - `ssh nyan-pc-reverse whoami`
2. Windows build와 로컬 publish를 한 번에 실행한다.
   - `bash ./app/packaging/build_windows_portable_and_publish.sh`
3. 기존 Windows 산출물만 다시 publish할 때는 아래 helper를 쓴다.
   - `powershell -ExecutionPolicy Bypass -File .\\app\\packaging\\publish_portable_to_runtime.ps1`
4. Linux repo 안의 혼동되는 이전 공유 미러 부산물을 정리할 때는 아래 helper를 쓴다.
   - `bash ./app/packaging/cleanup_portable_artifacts.sh`

비고:

- Windows 포터블 exe는 Windows 호스트 또는 Windows CI runner에서 빌드하는 것을 기본으로 본다.
- Linux 서버에서는 spec, 오프라인 자산, 런처 구조 검증까지만 수행한다. Linux에서 빌드된 ELF 산출물은 Windows에서 실행할 수 없다.
- 앱 내부 FastAPI 서버는 항상 해당 Windows 프로세스 안에서 로컬로 뜬다. 서버와 Windows 검증의 연동성은 exe 위치가 아니라 같은 세이브 파일 폴더를 열었는지로 결정된다.
- 공유 폴더 직접 실행은 `pythonnet / Python.Runtime.dll` 계층에서 불안정할 수 있어 공식 지원 경로에서 제외한다.
- 실제 실행은 `D:\EmailPilotAI\portable\EmailPilotAI\EmailPilotAI.exe` 하나를 기준으로 한다.
- `portable_bundle_manifest.json`은 Windows build 임시 폴더와 공식 D runtime publish 결과가 같은 bundle인지 확인하는 기준 파일이다.
- 기본 cleanup 대상은 아래 세 가지다.
  - `build/EmailPilotAI/`
  - `dist/EmailPilotAI/`
  - `dist/windows-portable.precheck/`
  - `dist/windows-portable/EmailPilotAI/`
- 설치형 installer는 다음 단계 범위다. 현재는 더블클릭 가능한 포터블 bundle을 first-class 검증 대상으로 본다.
