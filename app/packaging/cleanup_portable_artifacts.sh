#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

usage() {
  cat <<'EOF'
Usage:
  bash app/packaging/cleanup_portable_artifacts.sh [options]

Options:
  --help                   Show this help.

Default cleanup targets:
  - build/EmailPilotAI
  - dist/EmailPilotAI
  - dist/windows-portable.precheck
  - dist/windows-portable/.portable-mirror.*
  - dist/windows-portable/EmailPilotAI
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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

remove_path() {
  local target="$1"
  if [[ -e "${target}" ]]; then
    rm -rf -- "${target}"
    echo "[removed] ${target}"
  else
    echo "[skip-missing] ${target}"
  fi
}

remove_path "${REPO_ROOT}/build/EmailPilotAI"
remove_path "${REPO_ROOT}/dist/EmailPilotAI"
remove_path "${REPO_ROOT}/dist/windows-portable.precheck"

if [[ -d "${REPO_ROOT}/dist/windows-portable" ]]; then
  while IFS= read -r mirror_dir; do
    remove_path "${mirror_dir}"
  done < <(find "${REPO_ROOT}/dist/windows-portable" -maxdepth 1 -type d -name '.portable-mirror.*' -print)
fi

remove_path "${REPO_ROOT}/dist/windows-portable/EmailPilotAI"

if [[ -d "${REPO_ROOT}/dist/windows-portable" ]] && [[ -z "$(find "${REPO_ROOT}/dist/windows-portable" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  remove_path "${REPO_ROOT}/dist/windows-portable"
fi

if [[ -d "${REPO_ROOT}/dist" ]] && [[ -z "$(find "${REPO_ROOT}/dist" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  remove_path "${REPO_ROOT}/dist"
fi

if [[ -d "${REPO_ROOT}/build" ]] && [[ -z "$(find "${REPO_ROOT}/build" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  remove_path "${REPO_ROOT}/build"
fi
