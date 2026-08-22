#!/usr/bin/env bash
# CORVID CI: no placeholder tokens in docs/ (spec §3.2 — use UNVERIFIED in dossiers instead).
set -uo pipefail
hits=$(grep -rnE '\b(T[B]D|T[O]DO|F[I]XME|X[X]X)\b' docs/ --include='*.md' --exclude='TEMPLATE.md' --exclude-dir=raw 2>/dev/null || true)
if [ -n "$hits" ]; then echo "$hits"; echo "::error::placeholder tokens in docs/ — resolve them or mark UNVERIFIED"; exit 1; fi
echo "placeholder lint: ok"
