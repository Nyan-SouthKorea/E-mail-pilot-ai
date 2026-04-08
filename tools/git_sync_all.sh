#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  tools/git_sync_all.sh "<commit message>" [--push]

Behavior:
  - prints git status
  - stages repo changes with git add -A
  - blocks obvious local-only files such as README.local.md or .env*
  - creates one commit when there are staged changes
  - pushes only when --push is given and the current branch already has an upstream
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

commit_message="$1"
push_flag="${2:-}"

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

echo "[git status]"
git status --short

if [[ -z "$(git status --porcelain)" ]]; then
  echo "No changes to sync."
  exit 0
fi

git add -A

staged_paths="$(git diff --cached --name-only)"
if [[ -z "$staged_paths" ]]; then
  echo "No staged changes after git add -A."
  exit 0
fi

if echo "$staged_paths" | grep -E '(^|/)(README\.local\.md|\.env($|\.)|secrets($|/))' >/dev/null; then
  echo "Refusing to commit local-only or secret paths:"
  echo "$staged_paths" | grep -E '(^|/)(README\.local\.md|\.env($|\.)|secrets($|/))' || true
  exit 1
fi

git commit -m "$commit_message"

if [[ "$push_flag" != "--push" ]]; then
  echo "Commit created. Push skipped."
  exit 0
fi

if ! git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  echo "Commit created. Push skipped because the current branch has no upstream."
  exit 0
fi

git push
