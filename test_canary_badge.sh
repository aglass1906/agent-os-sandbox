#!/bin/bash
set -euo pipefail

EXPECTED="[Phase 3 Canary: CANARY_RESOLVED]"
if grep -qFx "$EXPECTED" README.md; then
  echo "PASS: canary badge matches expected label"
  exit 0
else
  echo "FAIL: README.md does not contain exactly: $EXPECTED"
  grep -n "Phase 3 Canary" README.md || echo "(no canary line found)"
  exit 1
fi
