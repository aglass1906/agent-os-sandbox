#!/usr/bin/env bash
set -euo pipefail

EXPECTED="[Phase 3 Canary: take 3 on the release testing]"
ACTUAL=$(grep -E '^\[Phase 3 Canary:' README.md || true)

if [ "$ACTUAL" = "$EXPECTED" ]; then
  echo "PASS: canary badge label matches"
  exit 0
else
  echo "FAIL: expected exactly one line matching $EXPECTED"
  echo "  got: ${ACTUAL:-<no match>}"
  exit 1
fi
