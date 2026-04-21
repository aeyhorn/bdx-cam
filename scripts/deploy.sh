#!/usr/bin/env bash
set -euo pipefail

BRANCH="${1:-main}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

git fetch --all --tags
git checkout "${BRANCH}"
git pull --ff-only

RELEASE_ID="$(git describe --tags --exact-match 2>/dev/null || git rev-parse --short=12 HEAD)"
export RELEASE_ID

echo "Deploying RELEASE_ID=${RELEASE_ID} on branch=${BRANCH}"
docker compose up -d --build
echo "Done."
