#!/usr/bin/env bash
set -euo pipefail

EXPECTED="[Phase 3 Canary: take 3 on the release testing]"
ACTUAL=""
while IFS= read -r line; do
  if [[ "$line" == "[Phase 3 Canary:"* ]]; then
    ACTUAL="$line"
  fi
done < README.md

if [ "$ACTUAL" = "$EXPECTED" ]; then
  echo "PASS: canary badge label matches"
  exit 0
else
  echo "FAIL: expected exactly one line matching $EXPECTED"
  echo "  got: ${ACTUAL:-<no match>}"
  exit 1
fi
