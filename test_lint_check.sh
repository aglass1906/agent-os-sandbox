#!/usr/bin/env bash
# Real, minimal automated check: no committed game.js may contain a leftover
# console.log(...) or debugger; statement. A genuine, common lint rule
# (no-console / no-debugger) that can actually fail -- this is a canary
# proving the AgentOS test_policy "lint_quality" tier actually gets invoked
# and its output actually parses as evidence, not a stub that always exits 0.
# Swap in a real linter (eslint, etc.) once one is set up for this repo;
# this rule stays meaningful on its own either way.
set -uo pipefail

passed=0
failed=0

while IFS= read -r -d '' file; do
  hits=$(grep -nE 'console\.log\(|debugger;' "$file" || true)
  if [ -z "$hits" ]; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    echo "FAIL: $file"
    echo "$hits"
  fi
done < <(find src/games -name "*.js" -print0 | sort -z)

echo "$passed passed"
echo "$failed failed"

if [ "$failed" -gt 0 ]; then
  exit 1
fi
exit 0
