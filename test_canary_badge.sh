#!/usr/bin/env bash
set -euo pipefail

# AGENTS.md test policy: the release canary marker must appear EXACTLY once in
# README.md. Count every matching line first so stale duplicates cannot mask a
# bad marker (the old script only kept the last match).
EXPECTED="[Phase 3 Canary: take 3 on the release testing]"
MATCH_COUNT=0
ACTUAL=""
while IFS= read -r line; do
  if [[ "$line" == "[Phase 3 Canary:"* ]]; then
    MATCH_COUNT=$((MATCH_COUNT + 1))
    ACTUAL="$line"
  fi
done < README.md

if [ "$MATCH_COUNT" -ne 1 ]; then
  echo "FAIL: expected exactly one line matching $EXPECTED"
  echo "  got $MATCH_COUNT matching line(s)"
  exit 1
fi

if [ "$ACTUAL" = "$EXPECTED" ]; then
  echo "PASS: canary badge label matches"
  exit 0
else
  echo "FAIL: expected line matching $EXPECTED"
  echo "  got: ${ACTUAL:-<no match>}"
  exit 1
fi
