#!/usr/bin/env bash
# CORVID CI: no service binds to all interfaces without an ADR (CLAUDE.md §5.6; spec §8).
set -uo pipefail
ALLOW="docs/adr/bind-allowlist.txt"   # one repo-relative path per line; comment with the ADR number
fail=0
allowed() { grep -qxF -- "$1" "$ALLOW" 2>/dev/null; }
dirs=(); for d in agent coordinator db deploy site scripts; do [ -d "$d" ] && dirs+=("$d"); done
if [ ${#dirs[@]} -gt 0 ]; then
  while IFS=: read -r f ln _; do
    [ -z "$f" ] && continue; allowed "$f" && continue
    echo "::error file=$f,line=$ln::binds to all interfaces — bind to the tailnet IP or add an ADR + allowlist entry"; fail=1
  done < <(grep -rnE '0\.0\.0\.0|\[::\]|"::"' "${dirs[@]}" --include='*.py' --include='*.sh' --include='*.service' --include='*.toml' --include='*.yml' --include='*.yaml' --include='*.json' --include='*.env' 2>/dev/null | grep -v 'lint-bind-targets.sh' | grep -v 'guard_bash.py')
fi
while IFS= read -r f; do
  [ -z "$f" ] && continue; allowed "$f" && continue
  while IFS=: read -r ln _; do
    echo "::error file=$f,line=$ln::compose port mapping without host IP — use \"<tailnet-ip>:host:container\""; fail=1
  done < <(grep -nE '^\s*-\s*"?[0-9]+:[0-9]+"?\s*$' "$f")
done < <(git ls-files | grep -E '(^|/)(docker-)?compose[^/]*\.ya?ml$')
[ "$fail" -eq 0 ] && echo "bind-target lint: ok"
exit "$fail"
