#!/usr/bin/env bash
# Real, minimal automated check: every game's JS must parse cleanly under
# Node. Not behavioral coverage, but genuine automated verification (catches
# real syntax errors) rather than a stub that always exits 0 -- see the
# no-op "true" test_policy this replaced.
set -uo pipefail

NODE_BIN="node"
if ! command -v "$NODE_BIN" >/dev/null 2>&1 && [ -x "$HOME/.local/bin/node" ]; then
  NODE_BIN="$HOME/.local/bin/node"
fi
if ! command -v "$NODE_BIN" >/dev/null 2>&1; then
  echo "FAIL: node not found on PATH or at \$HOME/.local/bin/node"
  echo "0 passed"
  echo "1 failed"
  exit 1
fi

passed=0
failed=0

while IFS= read -r -d '' file; do
  if "$NODE_BIN" --check "$file" >/dev/null 2>&1; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    echo "FAIL: $file"
    "$NODE_BIN" --check "$file" || true
  fi
done < <(find src/games -name "*.js" -print0 | sort -z)

echo "$passed passed"
echo "$failed failed"

if [ "$failed" -gt 0 ]; then
  exit 1
fi
exit 0
