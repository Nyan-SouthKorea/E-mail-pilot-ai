#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

WINDOWS_HOST_ALIAS="nyan-pc-reverse"
WINDOWS_BUILD_SCRIPT="D:\\EmailPilotAI\\repo\\app\\packaging\\build_portable_exe.ps1"
DO_BUILD=1
BUILD_ARGS=()

join_windows_args() {
  local joined=""
  local arg
  for arg in "$@"; do
    joined+=" ${arg}"
  done
  printf '%s' "${joined}"
}

usage() {
  cat <<'EOF'
Usage:
  bash app/packaging/build_windows_portable_and_publish.sh [options]

Options:
  --skip-build                  Reuse the existing Windows published runtime bundle.
  --clean                       Pass -Clean to the Windows PowerShell build script.
  --skip-smoke                  Pass -SkipSmoke to the Windows PowerShell build script.
  --windows-host-alias <alias>  Reverse SSH alias for the Windows builder.
  --windows-build-script <path> Windows path to build_portable_exe.ps1.
  --help                        Show this help.

Defaults:
  --windows-host-alias nyan-pc-reverse
  --windows-build-script D:\EmailPilotAI\repo\app\packaging\build_portable_exe.ps1
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-build)
      DO_BUILD=0
      shift
      ;;
    --clean)
      BUILD_ARGS+=("-Clean")
      shift
      ;;
    --skip-smoke)
      BUILD_ARGS+=("-SkipSmoke")
      shift
      ;;
    --windows-host-alias)
      WINDOWS_HOST_ALIAS="$2"
      shift 2
      ;;
    --windows-build-script)
      WINDOWS_BUILD_SCRIPT="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ${DO_BUILD} -eq 1 ]]; then
  echo "[build] Windows host alias: ${WINDOWS_HOST_ALIAS}"
  echo "[build] Windows build script: ${WINDOWS_BUILD_SCRIPT}"
  WINDOWS_BUILD_ARGS_STRING="$(join_windows_args "${BUILD_ARGS[@]}")"
  ssh "${WINDOWS_HOST_ALIAS}" \
    "powershell -NoProfile -ExecutionPolicy Bypass -File \"${WINDOWS_BUILD_SCRIPT}\"${WINDOWS_BUILD_ARGS_STRING}"
else
  echo "[build] Skipping Windows build and reusing the existing published runtime bundle."
fi

bash "${SCRIPT_DIR}/cleanup_portable_artifacts.sh"

echo "[done] Official Windows runtime executable:"
echo "D:\\EmailPilotAI\\portable\\EmailPilotAI\\EmailPilotAI.exe"
