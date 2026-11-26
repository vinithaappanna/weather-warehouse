#!/usr/bin/env bash
# Fail-closed commit: run the test suite first and commit only if it passes.
#   scripts/safe_commit.sh "Commit message"
# Nothing is staged or committed when pytest fails, errors, collects nothing,
# or cannot run. Does not push.
set -u
cd "$(dirname "$0")/.." || exit 1
[ $# -ge 1 ] && [ -n "$1" ] || { echo "usage: scripts/safe_commit.sh \"message\"" >&2; exit 2; }
out=$(python -m pytest -q 2>&1); rc=$?
echo "$out" | tail -3
if [ "$rc" -ne 0 ]; then
  echo "BLOCKED: pytest exit code $rc, nothing committed" >&2
  exit 1
fi
echo "$out" | grep -Eq '[0-9]+ passed' || { echo "BLOCKED: no passing tests reported, nothing committed" >&2; exit 1; }
git add -A || exit 1
git -c user.name="Vinitha Appanna" -c user.email="vinithaappanna@users.noreply.github.com" commit -q -m "$1" || { echo "BLOCKED: git commit failed" >&2; exit 1; }
git log --oneline | head -1
