#!/usr/bin/env bash
# PreToolUse hook on Bash. Closes the shell bypass that permission globs miss
# (e.g. `cat sim/_core.pack`, `python3 -c "...state.db..."`).
#
# Reads the PreToolUse JSON event on stdin, extracts the Bash command, and
# blocks (exit 2) if the command text references any forbidden sim internal.
# Allowed: everything else, including Read of sim/API.md.
#
# Forbidden paths (AGENTS.md "Do not read" rule):
#   *.pack  state.db  sim/affiliate_center.py  sim/pack.py
#
# AGENTS.md:104-109 — build-time discipline, defense-in-depth.

set -euo pipefail

payload="$(cat)"

# Pull the command string out of tool_input.command without needing jq.
if command -v jq >/dev/null 2>&1; then
  cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')"
else
  cmd="$(printf '%s' "$payload" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null || printf '')"
fi

# Allow the sanctioned way packs are touched: a `pack=<path>.pack` argument to
# the documented CLI (e.g. `python3 sim/simctl.py init runs/r2 pack=sim/round2.pack`,
# AGENTS.md:52). Scrub those tokens before matching, so passing a pack *path* to
# simctl is fine while reading pack *contents* (`cat`/`strings`/`xxd sim/*.pack`)
# is still blocked — a bare `.pack` reference not in `pack=` form stays caught.
scrubbed="$(printf '%s' "$cmd" | sed -E 's#pack=[^[:space:]]*\.pack##g')"

# Case-insensitive match on any forbidden reference.
if printf '%s' "$scrubbed" | grep -Eiq '\.pack([^a-z0-9]|$)|state\.db|sim/affiliate_center\.py|sim/pack\.py'; then
  echo "Blocked: command references a forbidden sim internal (*.pack / state.db / sim/affiliate_center.py / sim/pack.py). Talk to the sim only through sim/API.md (AGENTS.md:104-109)." >&2
  exit 2
fi

exit 0
