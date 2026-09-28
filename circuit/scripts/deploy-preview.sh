#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" != 1 || ! "$1" =~ ^[1-9][0-9]*$ ]]; then
  echo "usage: deploy-preview.sh <pull-request-number>" >&2
  exit 2
fi
: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required for the CI preview gate}"
ALIAS="pr-$1"
DEPLOY_LOG=$(mktemp)
trap 'rm -f "$DEPLOY_LOG"' EXIT

upload_version() {
  npx --yes wrangler@4 versions upload --env "" --preview-alias "$ALIAS" \
    2>&1 | tee "$DEPLOY_LOG"
}

if upload_version; then
  :
else
  status=$?
  if ! grep -Fq 'You cannot upload a new version of a Worker that does not yet exist.' "$DEPLOY_LOG"; then
    exit "$status"
  fi
  # The top-level worker has only a workers.dev route; production is the
  # separate --env production worker with its custom-domain route.
  echo "Bootstrapping the top-level preview Worker before its first version upload."
  npx --yes wrangler@4 deploy --env ""
  upload_version
fi

DEPLOY_URL=$(grep -oE "https://${ALIAS}-[a-z0-9.-]+\.workers\.dev" "$DEPLOY_LOG" | head -1 || true)
if [[ -z "$DEPLOY_URL" ]]; then
  echo "::error::Version upload returned no preview-alias URL; preview verification cannot run."
  exit 1
fi
echo "deploy_url=$DEPLOY_URL" >> "$GITHUB_OUTPUT"
echo "Preview URL: $DEPLOY_URL"
