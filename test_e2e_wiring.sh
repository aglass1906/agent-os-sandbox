#!/usr/bin/env bash
# Real, minimal automated check: every game's index.html must actually
# reference its own game.js (and style.css, when one exists) by a relative
# <script src>/<link href>, and the referenced files must exist on disk.
# A genuine structural end-to-end check -- proves the shipped page and its
# script/style are actually wired together -- without needing a browser or
# Playwright. This is a canary proving the AgentOS test_policy "e2e" tier
# actually gets invoked and its output actually parses as evidence, not a
# stub that always exits 0. Swap in real Playwright/browser_observe checks
# once that's set up for this repo; this rule stays meaningful either way.
set -uo pipefail

passed=0
failed=0

while IFS= read -r -d '' html; do
  dir=$(dirname "$html")
  ok=1
  reasons=""

  if ! grep -qE '<script[^>]*src="game\.js"' "$html"; then
    ok=0
    reasons="$reasons missing <script src=\"game.js\">;"
  elif [ ! -f "$dir/game.js" ]; then
    ok=0
    reasons="$reasons game.js referenced but not on disk;"
  fi

  if [ -f "$dir/style.css" ] && ! grep -qE '<link[^>]*href="style\.css"' "$html"; then
    ok=0
    reasons="$reasons style.css exists but index.html does not link it;"
  fi

  if [ "$ok" -eq 1 ]; then
    passed=$((passed + 1))
  else
    failed=$((failed + 1))
    echo "FAIL: $html -$reasons"
  fi
done < <(find src/games -mindepth 2 -maxdepth 2 -name "index.html" -print0 | sort -z)

echo "$passed passed"
echo "$failed failed"

if [ "$failed" -gt 0 ]; then
  exit 1
fi
exit 0
