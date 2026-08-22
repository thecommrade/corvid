#!/usr/bin/env python3
"""CORVID PostToolUse hook: ruff format + check --fix on edited .py files. Never blocks."""
import json, os, shutil, subprocess, sys
d = json.load(sys.stdin)
fp = (d.get("tool_input") or {}).get("file_path") or ""
if not fp.endswith(".py") or not os.path.exists(fp):
    sys.exit(0)
root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
ruff = os.path.join(root, ".venv", "bin", "ruff")
if not os.path.exists(ruff):
    ruff = shutil.which("ruff")
if not ruff:
    print("ruff not found (.venv/bin/ruff or PATH) — skipped")
    sys.exit(0)
for args in (["format", fp], ["check", "--fix", fp]):
    r = subprocess.run([ruff, *args], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if out:
        print(f"ruff {args[0]}: {out[-800:]}")
sys.exit(0)
