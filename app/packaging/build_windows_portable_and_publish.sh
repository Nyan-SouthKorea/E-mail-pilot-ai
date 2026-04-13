#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

WINDOWS_HOST_ALIAS="nyan-pc-reverse"
WINDOWS_REPO_ROOT="D:\\EmailPilotAI\\repo"
WINDOWS_BUILD_SCRIPT="D:\\EmailPilotAI\\repo\\app\\packaging\\build_portable_exe.ps1"
WINDOWS_GIT_REF="$(git -C "${REPO_ROOT}" branch --show-current 2>/dev/null || printf 'main')"
WINDOWS_GIT_REMOTE_URL="$(git -C "${REPO_ROOT}" remote get-url origin 2>/dev/null || printf '')"
DO_BUILD=1
DO_SYNC=1
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
  --skip-sync                   Skip syncing the Windows build mirror from GitHub.
  --clean                       Pass -Clean to the Windows PowerShell build script.
  --skip-smoke                  Pass -SkipSmoke to the Windows PowerShell build script.
  --windows-host-alias <alias>  Reverse SSH alias for the Windows builder.
  --windows-repo-root <path>    Windows path to the build mirror root.
  --windows-build-script <path> Windows path to build_portable_exe.ps1.
  --git-ref <ref>               Git ref to sync on the Windows build mirror.
  --git-remote-url <url>        Git remote URL to sync on the Windows build mirror.
  --help                        Show this help.

Defaults:
  --windows-host-alias nyan-pc-reverse
  --windows-repo-root D:\EmailPilotAI\repo
  --windows-build-script D:\EmailPilotAI\repo\app\packaging\build_portable_exe.ps1
  --git-ref <current branch on Linux repo>
  --git-remote-url <origin URL on Linux repo>
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-build)
      DO_BUILD=0
      shift
      ;;
    --skip-sync)
      DO_SYNC=0
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
    --windows-repo-root)
      WINDOWS_REPO_ROOT="$2"
      shift 2
      ;;
    --windows-build-script)
      WINDOWS_BUILD_SCRIPT="$2"
      shift 2
      ;;
    --git-ref)
      WINDOWS_GIT_REF="$2"
      shift 2
      ;;
    --git-remote-url)
      WINDOWS_GIT_REMOTE_URL="$2"
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

sync_repo_to_windows() {
  local windows_repo_root="$1"
  local git_ref="$2"
  local git_remote_url="$3"

  if [[ -z "${git_remote_url}" ]]; then
    echo "[sync] Git remote URL is empty. Cannot sync Windows build mirror." >&2
    exit 1
  fi

  echo "[sync] Windows host alias: ${WINDOWS_HOST_ALIAS}"
  echo "[sync] Windows repo root: ${windows_repo_root}"
  echo "[sync] Git ref: ${git_ref}"
  echo "[sync] Git remote: ${git_remote_url}"

  ssh "${WINDOWS_HOST_ALIAS}" \
    "powershell -NoProfile -Command \"\
\$repoRoot = '${windows_repo_root}'; \
\$repoParent = Split-Path -Parent \$repoRoot; \
\$gitRef = '${git_ref}'; \
\$originUrl = '${git_remote_url}'; \
New-Item -ItemType Directory -Force -Path \$repoParent | Out-Null; \
if (Test-Path (Join-Path \$repoRoot '.git')) { \
  git -C \$repoRoot remote set-url origin \$originUrl; \
  git -C \$repoRoot fetch origin \$gitRef; \
  git -C \$repoRoot reset --hard ('origin/' + \$gitRef); \
  git -C \$repoRoot clean -fdx; \
} else { \
  if (Test-Path \$repoRoot) { \
    Remove-Item -LiteralPath \$repoRoot -Recurse -Force -ErrorAction Stop; \
  } \
  git clone --branch \$gitRef \$originUrl \$repoRoot; \
} \
\""

  echo "[sync] Windows build mirror synced from Git."
}

if [[ ${DO_SYNC} -eq 1 ]]; then
  sync_repo_to_windows "${WINDOWS_REPO_ROOT}" "${WINDOWS_GIT_REF}" "${WINDOWS_GIT_REMOTE_URL}"
else
  echo "[sync] Skipping Windows repo sync and reusing the existing Windows mirror."
fi

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
