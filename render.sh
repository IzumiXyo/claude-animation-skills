#!/usr/bin/env bash
# Render one of the quick animation skills on GitHub Actions and download the result.
#
#   ./render.sh <skill> <spec.json|inline-json> [output-name]
#
# Examples:
#   ./render.sh graph examples/graph.json followers
#   ./render.sh map-route '{"destination":"Monas","minutes":18,"distance":6.4}' monas
#
# Env: REPO=owner/repo (default IzumiXyo/claude-animation-skills), REF=main
set -euo pipefail

REPO="${REPO:-IzumiXyo/claude-animation-skills}"
REF="${REF:-main}"
SKILL="${1:-}"
SPEC_ARG="${2:-}"
NAME="${3:-}"

if [ -z "$SKILL" ] || [ -z "$SPEC_ARG" ]; then
  echo "usage: ./render.sh <skill> <spec.json|inline-json> [output-name]" >&2
  exit 1
fi

if [ -f "$SPEC_ARG" ]; then
  SPEC="$(cat "$SPEC_ARG")"
  [ -n "$NAME" ] || NAME="$(basename "${SPEC_ARG%.json}")"
else
  SPEC="$SPEC_ARG"
fi

[ -n "$NAME" ] || NAME="$SKILL"

python3 -c 'import json,sys; json.loads(sys.argv[1])' "$SPEC" >/dev/null || {
  echo "error: spec is not valid JSON" >&2
  exit 1
}

gh auth status >/dev/null 2>&1 || {
  echo "error: gh is not logged in. Run: gh auth login" >&2
  exit 1
}

echo "triggering $SKILL -> $NAME on $REPO ..."
gh workflow run render.yml -R "$REPO" --ref "$REF" \
  -f skill="$SKILL" -f name="$NAME" -f spec="$SPEC"

sleep 3
RUN_ID="$(gh run list -R "$REPO" --workflow render.yml --event workflow_dispatch \
  --limit 1 --json databaseId --jq '.[0].databaseId')"

if [ -z "$RUN_ID" ] || [ "$RUN_ID" = "null" ]; then
  echo "error: could not find the workflow run" >&2
  exit 1
fi

echo "run: https://github.com/$REPO/actions/runs/$RUN_ID"
gh run watch "$RUN_ID" -R "$REPO" --exit-status

DEST="renders/$NAME"
rm -rf "$DEST"
mkdir -p "$DEST"
gh run download "$RUN_ID" -R "$REPO" -D "$DEST"

MP4="$(find "$DEST" -name '*.mp4' -type f | head -1)"
SHEET="$(find "$DEST" -name '*.sheet.jpg' -type f | head -1)"

if [ -n "$MP4" ]; then
  cp "$MP4" "$DEST/$NAME.mp4"
  echo "video: $DEST/$NAME.mp4"
fi
if [ -n "$SHEET" ]; then
  cp "$SHEET" "$DEST/$NAME.sheet.jpg"
  echo "sheet: $DEST/$NAME.sheet.jpg"
fi
