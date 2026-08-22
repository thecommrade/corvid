#!/usr/bin/env python3
"""CORVID PreToolUse guard for Bash (CLAUDE.md §5.6; spec §8).
Blocks (exit 2) bind-to-all-interfaces commands and forbidden actions on optiplex.
Audit commands (grep/ss/...) that merely mention 0.0.0.0 are allowed.
Hosts/paths that must not appear in the repo come from .claude/settings.local.json."""
import json, os, re, sys

data = json.load(sys.stdin)
if data.get("tool_name") != "Bash":
    sys.exit(0)
cmd = (data.get("tool_input") or {}).get("command") or ""

AUDIT = {"grep", "rg", "egrep", "fgrep", "ss", "netstat", "lsof", "awk", "sed", "cat", "head",
         "tail", "less", "more", "echo", "printf", "wc", "sort", "uniq", "cut", "tr", "find",
         "ls", "stat", "diff", "comm", "jq", "git", "journalctl", "nvidia-smi"}
SKIP = {"sudo", "timeout", "nice", "env", "time", "ionice", "systemd-run"}
BIND = [
    r"(?:--host|--bind|--bind-address|--listen|--listen-address|--address|--addr|--http-addr|--server-host|-H|-b)[= ]+[\"']?(?:0\.0\.0\.0|\[?::\]?)(?:[\"'\s:]|$)",
    r"\b(?:host|bind|listen|address)\s*=\s*[\"']?0\.0\.0\.0",
    r"(?<![\d.])0\.0\.0\.0:\d+",
    r"(?:^|\s)(?:-p|--publish)[= ]+[\"']?\d+:\d+",
    r"(?:^|\s)(?:-P|--publish-all)(?:\s|$)",
]

def first_token(seg):
    toks = seg.strip().split()
    i = 0
    while i < len(toks) and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[i]) or toks[i] in SKIP
                             or (i > 0 and toks[i-1] == "timeout" and re.match(r"^\d", toks[i]))
                             or toks[i].startswith("-")):
        i += 1
    return toks[i] if i < len(toks) else ""

for seg in re.split(r"\|\||&&|\||;|\n", cmd):
    if first_token(seg) in AUDIT:
        continue
    for pat in BIND:
        if re.search(pat, seg):
            sys.stderr.write("CORVID guard: this command binds a service to all interfaces "
                             "(or publishes a port unqualified). Bind to the tailnet IP; "
                             "0.0.0.0 needs an ADR + allowlist entry (CLAUDE.md §5.6).\n")
            sys.exit(2)

root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
cfg_path = os.path.join(root, ".claude", "settings.local.json")
guards = {}
if os.path.exists(cfg_path):
    try:
        guards = (json.load(open(cfg_path)) or {}).get("guards", {}) or {}
    except Exception:
        guards = {}
hosts = [h for h in guards.get("optiplex_hosts", []) if h]
forbidden = guards.get("optiplex_forbidden", [])
paths = guards.get("forbidden_paths", [])
for p in paths:
    if p and p in cmd:
        sys.stderr.write(f"CORVID guard: '{p}' is off-limits (another project's data).\n")
        sys.exit(2)
if hosts and any(re.search(r"(?<![\w.-])" + re.escape(h) + r"(?![\w-])", cmd) for h in hosts):
    for f in forbidden:
        if f and f in cmd:
            sys.stderr.write(f"CORVID guard: '{f.strip()}' is not allowed on optiplex from an "
                             "unattended session (production host; root/Postgres = founder only).\n")
            sys.exit(2)
sys.exit(0)
