# CORVID Research & Planning Package — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **This plan is executed by the main session (Fable) with the founder; tasks that produce plans for Opus say so.** Subagents may do repo-only tasks (docs/code inside this repo); **no subagent ever gets a shell on a node** (spec §6.4).

**Goal:** Produce the CORVID research + planning package — dossiers R00–R10 (with spikes), Phase 0/1/2 specs and executable plans, ADR-0002…0005, the Phase 3–5 outline, and the repo skeleton (templates, skills, hooks, CI, workflow) — per the approved spec.

**Architecture:** Milestones M0–M5 from spec §9. M0 builds the repo skeleton so every later artifact has a template, a lint, and a skill. M1 writes R00 and the Phase 0 spec/plan + ADR-0002/0003/0004 so Opus can start executing Phase 0. M2 runs the adversarially verified research sweep (a Workflow-tool script) and the six spikes (main session only, capped) and renders R01–R10. M3/M4 write Phase 1/2 specs + plans against the dossiers (+ ADR-0005). M5 writes the Phase 3–5 outline and runs the definition-of-done checklist.

**Tech Stack:** Markdown docs (MkDocs Material), ADRs, Claude Code project skills/hooks/workflows (`.claude/`), GitHub Actions, Python 3 for hook scripts, bash for lint scripts, project `.venv` for `ruff`/`mkdocs-material`/`pytest` (no root needed), Tailscale CLI, llama.cpp (spikes), systemd-run (caps).

**Spec:** `docs/superpowers/specs/2026-08-22-corvid-research-and-planning-design.md` (v2.1, approved 2026-08-22). Read it first; every task below cites its sections.

## Global Constraints

- Executor tags: exactly one of `executor: main-session` / `executor: Opus` (optionally `Opus (splx-root)`) / `executor: founder` on every step of every plan produced (spec §3.3, Appendix A).
- Nothing private in the repo: no usernames, key file names, LAN/public IPs, passwords, VPN provider configs; recipes use placeholders `<lan-gw>`, `<vpn-if>`, `<table>` (spec §3.8). Hook patterns needing IPs live in git-ignored `.claude/settings.local.json`.
- CLAUDE.md edits only per spec §3.9: §4 credit rows (same commit as the dependency), phase-complete marks, the §3.2 endpoint line when ADR-0003 is Accepted, one-line pointers.
- Default caps for any work on a node = spec Appendix B: ahnoway `CPUQuota=120%` `MemoryMax=1.6G` VRAM ≤ 800 MB AC power required; solarplexus `CPUQuota=40%` `MemoryMax=1.6G` VRAM ≤ 400 MB; optiplex `CPUQuota=120%` `MemoryMax=3.2G` VRAM ≤ 600 MB; `nice -n 19`; exceptions requested per spike/step, granted by the founder, time-boxed, recorded.
- Listeners bind to the tailnet interface only; never `0.0.0.0` (S-01 may bind a specific LAN IP; card records it).
- optiplex: never its production services, Postgres, or its other data disk; no root there except the founder.
- `docs/status.md` has one writer (main session or founder); Opus proposes lines in run files; evidence to `docs/runs/`, raw captures to git-ignored `docs/runs/raw/`.
- Every fact in a dossier: source URL + date verified (+ version/commit when version-dependent) or spike ID; otherwise `UNVERIFIED`.
- Placeholder tokens forbidden in `docs/` (the three words `scripts/lint-placeholders.sh` checks); templates are exempt by filename.
- Git: branch `main`, repo-local identity `thecommrade`, conventional commits, `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` trailer, small commits; remote URL carries `thecommrade@` so the gh credential helper picks that account; never switch the global gh account.
- ADR numbers 0002–0005 are reserved (membership, endpoints, exit criteria, contribution slider); a topology ADR takes 0006.
- Spike code is throwaway; never committed under `agent/` or `coordinator/`.

## File Structure (what each task creates)

| Path | Responsibility | Task |
|---|---|---|
| `docs/adr/TEMPLATE.md` | ADR skeleton | T1 |
| `docs/research/TEMPLATE.md` | dossier skeleton (spec §6.2) | T1 |
| `docs/research/spikes/TEMPLATE.md` | spike card skeleton (spec §6.3) | T1 |
| `docs/runs/README.md`, `docs/runbooks/README.md`, `docs/research/README.md` | what lives where | T1 |
| `.venv/` (git-ignored), `mkdocs.yml`, `docs/index.md` | docs build | T2 |
| `.claude/skills/{save-state,new-adr,add-dependency,spike,remote-step}/SKILL.md` | project skills (spec §8) | T3 |
| `.claude/settings.json`, `.claude/hooks/guard_bash.py`, `.claude/hooks/ruff_on_py.py`, `.claude/settings.local.json.example`, `.claude/settings.local.json` (git-ignored) | hooks (spec §8) | T4 |
| `scripts/lint-bind-targets.sh`, `scripts/lint-placeholders.sh`, `docs/adr/bind-allowlist.txt`, `.github/workflows/ci.yml` | CI (spec §8) | T5 |
| `.claude/workflows/README.md` | workflow-script convention | T6 |
| `docs/status.md` (update), remote + push | M0 close | T7, T8 |
| `docs/research/R00-phase0-facts.md`, `docs/runs/R00-inspection-<date>.md` | Phase 0 facts | T9 |
| `docs/adr/0002-membership.md`, `0004-exit-criteria-one-lan-fleet.md`, `0003-endpoints.md` (+ CLAUDE.md §4 Caddy row) | Phase 0 ADRs | T10–T12 |
| `docs/superpowers/specs/<date>-phase-0-handshake-design.md`, `docs/superpowers/plans/<date>-phase-0-handshake.md` | Phase 0 spec + plan for Opus | T13, T14 |
| `.claude/workflows/research-sweep.js` | research sweep workflow | T16 |
| `docs/research/spikes/S-01…S-06-*.md`, `docs/runs/S-0n-<date>.md` | spikes | T17–T22 |
| `docs/research/R01…R10-*.md` | dossiers | T23 |
| Phase 1/2 specs + plans, ADR-0003 (Accepted), ADR-0005, topology ADR if needed, `docs/superpowers/specs/phase-3-5-outline.md` | M3–M5 | T25–T31 |

---

# M0 — Repo skeleton

### Task 1: Templates and directory READMEs

**Files:**
- Create: `docs/adr/TEMPLATE.md`, `docs/research/TEMPLATE.md`, `docs/research/spikes/TEMPLATE.md`, `docs/research/README.md`, `docs/runs/README.md`, `docs/runbooks/README.md`, `docs/runs/raw/.gitkeep` is NOT created (directory is git-ignored; README explains)

**Interfaces:**
- Produces: the three templates every later task copies; field names used verbatim by the `new-adr` and `spike` skills (Task 3) and by dossier rendering (Task 23).

- [ ] **Step 1: Create the ADR template**

```bash
mkdir -p docs/adr docs/research/spikes docs/runs docs/runbooks
cat > docs/adr/TEMPLATE.md <<'MD'
# ADR-NNNN — <Title>

- **Status:** Proposed | Accepted | Superseded by ADR-XXXX
- **Date:** YYYY-MM-DD
- **Deciders:** founder
- **Related:** CLAUDE.md §…, ADR-…, spec §…

## Context

<What forces are at play; what question had to be answered; facts with sources (dossier/spike IDs).>

## Decision

<The decision, stated so it can be tested. Numbered if several parts.>

## Consequences

<What becomes easier/harder; what the plans must now do; what would reopen this ADR.>

## CLAUDE.md §4 rows added in this commit

<`| Name | What we take | License | Author |` — or "none".>
MD
```

- [ ] **Step 2: Create the dossier template (spec §6.2)**

```bash
cat > docs/research/TEMPLATE.md <<'MD'
# Rnn — <Dossier title>

- **Depth:** full | outline (spec §6.1)
- **Written:** YYYY-MM-DD by <main-session | agent id> · **Verified:** YYYY-MM-DD (adversarial pass: yes/no)
- **Feeds:** <which spec/plan sections cite this>

## Purpose

<One paragraph: what decisions this dossier exists to inform.>

## Facts

| ID | Statement | Source (URL) | Date verified | Version/commit | Status |
|---|---|---|---|---|---|
| Rnn-F1 | … | … | YYYY-MM-DD | … | verified \| UNVERIFIED |

## Spike results

| Spike | One-line result | Card | Run file |
|---|---|---|---|
| S-nn | … | `spikes/S-nn-….md` | `../runs/S-nn-<date>.md` |

## Recommendations for the spec

1. …

## Open questions

- …

## CLAUDE.md §4 credit rows to add

| Name | What we take | License | Author |
|---|---|---|---|

## Change log

- YYYY-MM-DD — created.
MD
```

- [ ] **Step 3: Create the spike card template (spec §6.3)**

```bash
cat > docs/research/spikes/TEMPLATE.md <<'MD'
# S-nn — <slug>

- **Goal:** <the one fact this spike produces>
- **Node(s):** ahnoway | solarplexus | optiplex
- **Executor:** main-session | founder   (never Opus)
- **Dependencies:** <Phase 0 steps / spikes that must be done first; "none">
- **Preconditions:** AC power on ahnoway (`cat /sys/class/power_supply/{AC*,ADP*}/online 2>/dev/null` → 1) · Plex/Immich idle (founder confirms) · optiplex 1-min load < <ceiling> (`cut -d' ' -f1 /proc/loadavg`) · disk free ≥ <GB> on <path> · `docs/status.md` "Node in use by" empty · Tailscale mode per node recorded: <userspace|kernel>
- **Cap (Appendix B):** `CPUQuota=<…>` `MemoryMax=<…>` VRAM ≤ <…> MB via <`--mem`/layers> · `nice -n 19` · network: <default | exception>
- **Exception record:** none | requested <amount> for <duration>; granted by founder on <date/time>
- **Time box:** <minutes>
- **Expected signal:** <what a successful run prints/measures>
- **Abort criteria / watch:** load > <n> · GPU temp > <°C> (`nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader`) · swap in use · Plex/Immich unhealthy → stop and run undo

## Commands (exact; every heavy command wrapped)

```bash
systemd-run --user --scope -p CPUQuota=<…> -p MemoryMax=<…> nice -n 19 <command>
```

## Undo (executed and confirmed at the end)

```bash
<kill processes; remove scratch; close ports> ; <verification that undo worked>
```

## Result

- <numbers, with units; version/commit pinned>
- Raw evidence: `docs/runs/S-nn-<date>.md` (sanitised) · `docs/runs/raw/` (git-ignored)

## Follow-ups

- <facts filed into Rnn; new questions>
MD
```

- [ ] **Step 4: Create the READMEs**

```bash
cat > docs/research/README.md <<'MD'
# Research dossiers

One file per dossier, `Rnn-<slug>.md`, from `TEMPLATE.md` (spec §6.1–6.2). Facts carry a source URL + date verified (+ version) or a spike ID; anything else is marked `UNVERIFIED`. Spike cards live in `spikes/`.
MD
cat > docs/runs/README.md <<'MD'
# Runs (evidence)

One file per plan run or spike: `<plan-or-spike>-<YYYY-MM-DD>.md`, sanitised (no usernames, keys, LAN/public IPs). Raw captures go to `raw/` (git-ignored). `docs/status.md` gets one summary line + link per run (spec §3.4).
MD
cat > docs/runbooks/README.md <<'MD'
# Founder runbooks

Operational notes for the founder per component (first one arrives with Phase 2). Access details stay in the founder's private notes.
MD
```

- [ ] **Step 5: Verify and commit**

Run: `ls docs/adr/TEMPLATE.md docs/research/TEMPLATE.md docs/research/spikes/TEMPLATE.md docs/research/README.md docs/runs/README.md docs/runbooks/README.md`
Expected: six paths printed, no error.

```bash
git add docs/adr/TEMPLATE.md docs/research docs/runs/README.md docs/runbooks/README.md
git commit -m "docs: ADR, dossier, and spike templates + directory READMEs

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 2: Project venv, MkDocs Material, docs index

**Files:**
- Create: `mkdocs.yml`, `docs/index.md`; `.venv/` (git-ignored)

**Interfaces:**
- Produces: `.venv/bin/{mkdocs,ruff,pytest}` used by Task 4's ruff hook, Task 5's CI parity, and every "mkdocs build" verification below.

- [ ] **Step 1: Create the venv and install tools (user-level, no root)**

```bash
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet mkdocs-material ruff pytest
.venv/bin/mkdocs --version && .venv/bin/ruff --version
```
Expected: two version lines, no error. (`.venv/` is already in `.gitignore`.)

- [ ] **Step 2: Write `mkdocs.yml`**

```bash
cat > mkdocs.yml <<'YML'
site_name: CORVID
site_description: A friends-scale compute co-op — planning docs
repo_url: https://github.com/thecommrade/corvid
docs_dir: docs
site_dir: site
theme:
  name: material
  features:
    - navigation.sections
    - navigation.indexes
    - content.code.copy
    - search.suggest
markdown_extensions:
  - admonition
  - tables
  - toc:
      permalink: true
  - pymdownx.superfences
exclude_docs: |
  **/TEMPLATE.md
  runs/raw/
YML
```

- [ ] **Step 3: Write `docs/index.md`**

```bash
cat > docs/index.md <<'MD'
# CORVID — planning docs

CORVID is a friends-scale compute co-op: the machines a group of friends already own, pooled over a private Tailscale mesh into shared AI inference, compute, and storage — metered by no one. The charter is [`CLAUDE.md`](https://github.com/thecommrade/corvid/blob/main/CLAUDE.md) in the repo root.

- **Start here:** [status](status.md) — where the project is and the exact next step.
- [ADRs](adr/0001-compute-is-a-commons.md) — decisions of record.
- [Research](research/README.md) — dossiers and spikes.
- Specs and plans live under `superpowers/` (design specs; executable plans).
- [Runs](runs/README.md) — evidence from plan runs and spikes. [Runbooks](runbooks/README.md) — founder notes.
MD
```

- [ ] **Step 4: Build and verify**

Run: `.venv/bin/mkdocs build 2>&1 | tail -3`
Expected: ends with `INFO    -  Documentation built in …` and no `ERROR`. (`site/` is git-ignored.)

- [ ] **Step 5: Commit**

```bash
git add mkdocs.yml docs/index.md
git commit -m "docs: MkDocs Material config and index page

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 3: Project skills (spec §8)

**Files:**
- Create: `.claude/skills/save-state/SKILL.md`, `.claude/skills/new-adr/SKILL.md`, `.claude/skills/add-dependency/SKILL.md`, `.claude/skills/spike/SKILL.md`, `.claude/skills/remote-step/SKILL.md`

**Interfaces:**
- Consumes: templates from Task 1; lint scripts from Task 5 (skills reference them by path; they exist after Task 5 — run skills only after M0 completes).
- Produces: skill names `save-state`, `new-adr`, `add-dependency`, `spike`, `remote-step` referenced by every later task and by the Phase 0/1/2 plans.

- [ ] **Step 1: Write `save-state`**

```bash
mkdir -p .claude/skills/{save-state,new-adr,add-dependency,spike,remote-step}
cat > .claude/skills/save-state/SKILL.md <<'MD'
---
name: save-state
description: Use at the end of every CORVID session, before context compaction, or whenever a decision lands — rewrites the RESUME HERE block and the decisions table in docs/status.md so the next session (or a post-compaction continuation) starts exactly here. docs/status.md has ONE writer (the main session or the founder); Opus sessions propose lines in docs/runs/ instead.
---

# save-state

1. Read `docs/status.md` top to bottom.
2. Rewrite the `> **RESUME HERE …` blockquote (≤ 8 lines): what is settled since last time · the exact next action · anything the founder owes.
3. Update: "Where the conversation stopped" (1–2 paragraphs); the **Settled decisions** table (append rows, never renumber); **Phase 0 findings** (strike fixed items `~~…~~ fixed <date>`); `_Last updated:_`.
4. If a spike or plan run is in progress or about to be dispatched, write or clear the line `**Node in use by:** <executor> (<what>)` directly under the RESUME block (spec §9).
5. Run `bash scripts/lint-placeholders.sh` → `placeholder lint: ok`.
6. Commit: `git add docs/status.md && git commit -m "docs(status): <what changed>"` (+ Co-Authored-By trailer).
7. If you are the main session, mirror the resume point into Claude memory (`corvid-session-state.md`).

Never write usernames, key names, LAN/public IPs, or VPN details into status.md (spec §3.8).
MD
```

- [ ] **Step 2: Write `new-adr`**

```bash
cat > .claude/skills/new-adr/SKILL.md <<'MD'
---
name: new-adr
description: Create the next ADR in docs/adr/ from TEMPLATE.md, honouring reserved numbers (0002 membership, 0003 endpoints, 0004 exit criteria on a one-LAN fleet, 0005 contribution slider; a topology ADR takes 0006), link it from docs/status.md, and — when the decision introduces a dependency — add the CLAUDE.md §4 row in the same commit via add-dependency.
---

# new-adr

1. Number: if the title matches a reserved slot use that number; else `printf '%04d' $(( $(ls docs/adr | grep -oE '^[0-9]{4}' | sort -n | tail -1 | sed 's/^0*//') + 1 ))`.
2. `cp docs/adr/TEMPLATE.md docs/adr/NNNN-<slug>.md`; fill **every** section (Status, Date, Deciders, Related, Context with sourced facts, Decision as testable statements, Consequences, §4 rows or "none"). No empty sections.
3. Dependency introduced? Run the `add-dependency` skill now (same commit).
4. Append a row to the decisions table in `docs/status.md` (use `save-state`).
5. `bash scripts/lint-placeholders.sh` → ok.
6. Commit: `git add docs/adr/NNNN-<slug>.md docs/status.md [CLAUDE.md] && git commit -m "docs(adr): ADR-NNNN <title>"` (+ Co-Authored-By trailer).
MD
```

- [ ] **Step 3: Write `add-dependency`**

```bash
cat > .claude/skills/add-dependency/SKILL.md <<'MD'
---
name: add-dependency
description: Before adding ANY dependency CORVID ships or relies on (library, service, container image, model weights, tool) — look up the licence and author at the primary source for the pinned version, check compatibility, and add the CLAUDE.md §4 credit row in the SAME commit as the dependency. "Credit before we copy" (CLAUDE.md §1, §4, §8).
---

# add-dependency

1. Identify: name · what we take · version/tag pinned.
2. Primary source: the repo's LICENSE at that tag (or the model card); author/org.
3. Compatibility: permissive or weak copyleft → ok; AGPL → ok when network-served, say so in the row; source-available / BUSL / non-commercial → needs an ADR before use; model weights → licence name + whether gated.
4. Edit the CLAUDE.md §4 table: append `| <Name> | <What we take> | <License> | <Author> |`.
5. Tools used only inside a spike are credited on the spike card, not in §4.
6. Commit together: `git add CLAUDE.md <files that introduce the dependency> && git commit -m "deps: add <name> (<license>) + §4 credit"` (+ Co-Authored-By trailer).
MD
```

- [ ] **Step 4: Write `spike`**

```bash
cat > .claude/skills/spike/SKILL.md <<'MD'
---
name: spike
description: Run a research spike on a CORVID build node under the spike protocol (spec §6.3, Appendix B) — card from docs/research/spikes/TEMPLATE.md, preconditions, caps via systemd-run, undo, evidence to docs/runs/. Executor is main-session or founder only; never an unattended Opus session.
---

# spike

1. `cp docs/research/spikes/TEMPLATE.md docs/research/spikes/S-nn-<slug>.md`; fill **all** fields (write `none` explicitly where empty).
2. Preconditions: AC on ahnoway `cat /sys/class/power_supply/{AC*,ADP*}/online 2>/dev/null` → `1`; Plex/Immich idle (founder confirms); optiplex load `ssh <optiplex alias> "cut -d' ' -f1 /proc/loadavg"` below the card's ceiling; `docs/status.md` "Node in use by" empty; Tailscale mode per node noted on the card.
3. `save-state`: write `**Node in use by:** main-session (S-nn)`.
4. Wrap every heavy command: `systemd-run --user --scope -p CPUQuota=<B> -p MemoryMax=<B> nice -n 19 <cmd>`; GPU via `--mem`/layer count (Appendix B). Remote: same wrapper inside the ssh command.
5. Capture raw output to `docs/runs/raw/S-nn-<date>.log` (e.g. `… 2>&1 | tee docs/runs/raw/S-nn-<date>.log`); write the sanitised `docs/runs/S-nn-<date>.md` (no usernames/keys/IPs).
6. Need more than the cap? **Stop**, ask the founder, record amount/duration/grant on the card, then continue.
7. Run the undo block; verify (ports closed: `ss -tln | grep -c <port>` → 0; scratch removed).
8. Fill Result + Follow-ups; file the facts into the dossier; `save-state` to clear "Node in use by"; commit card + run file: `docs(spike): S-nn <slug> — <one-line result>`.
MD
```

- [ ] **Step 5: Write `remote-step`**

```bash
cat > .claude/skills/remote-step/SKILL.md <<'MD'
---
name: remote-step
description: How an executor reaches a CORVID build node — executor tags (main-session / Opus / Opus (splx-root) / founder), alias names, the BatchMode preflight, the founder handoff protocol, and gotchas. Read before any remote command. Usernames, key files, IPs and VPN details live in the founder's private notes (networkdocs), never here.
---

# remote-step

| Node | User-level, unattended | Root | Gotchas |
|---|---|---|---|
| ahnoway (build laptop, where sessions run) | local shell | `executor: founder` (sudo); `tailscale set` works unprivileged after the one-time `sudo tailscale set --operator=$USER` | laptop: AC power for spikes; Wayland session |
| solarplexus (hub) | the documented unattended alias (founder's notes) | `ssh splx-root` — only after the founder has loaded the agent key (`ssh -o BatchMode=yes splx-root true` → 0) | Tailscale in userspace mode until Phase 0 step 2; Tailscale SSH owns port 22 on the tailnet IP (non-interactive ssh stalls) until Phase 0 step 0; Plex/Immich/Caddy live here |
| optiplex (second node; another project's production host) | `ssh optiplex` / `ssh oplx` (unattended; BatchMode ok) | **founder only** | `export XDG_RUNTIME_DIR=/run/user/1000` before `systemctl --user`; never its Postgres / data disk; steady load from production |

**Preflight (every plan):** `ssh -o BatchMode=yes <optiplex alias> true`; `ssh -o BatchMode=yes <solarplexus alias> true`; for `(splx-root)` steps `ssh -o BatchMode=yes splx-root true`; caps from spec Appendix B; `docs/status.md` "Node in use by" shows nobody else on the node.

**Founder handoff:** at an `executor: founder` step, stop and print a copy-pasteable block (what, where, expected output); wait for "done" + output; verify with the named command; put the exchange in the run file.

**Exceptions above caps:** request → founder grants (amount, duration) → record in run file + status.md.
MD
```

- [ ] **Step 6: Verify frontmatter and commit**

Run: `for f in .claude/skills/*/SKILL.md; do head -1 "$f" | grep -q '^---$' && grep -q '^name: ' "$f" && grep -q '^description: ' "$f" && echo "ok $f" || echo "BAD $f"; done`
Expected: five `ok` lines.

```bash
git add .claude/skills
git commit -m "chore(skills): save-state, new-adr, add-dependency, spike, remote-step

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 4: Hooks (spec §8)

**Files:**
- Create: `.claude/settings.json`, `.claude/hooks/guard_bash.py`, `.claude/hooks/ruff_on_py.py`, `.claude/settings.local.json.example`, `.claude/settings.local.json` (git-ignored; real names)
- Test: run the guard with sample stdin (Step 5)

**Interfaces:**
- Consumes: `.venv/bin/ruff` (Task 2).
- Produces: guard behaviour every later session relies on: exit 2 + stderr reason blocks a Bash command.

- [ ] **Step 1: Write the Bash guard**

```bash
mkdir -p .claude/hooks
cat > .claude/hooks/guard_bash.py <<'PY'
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
PY
chmod +x .claude/hooks/guard_bash.py
```

- [ ] **Step 2: Write the ruff hook**

```bash
cat > .claude/hooks/ruff_on_py.py <<'PY'
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
PY
chmod +x .claude/hooks/ruff_on_py.py
```

- [ ] **Step 3: Write `settings.json` (committed) and the local example**

```bash
cat > .claude/settings.json <<'JSON'
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": "head -45 \"$CLAUDE_PROJECT_DIR/docs/status.md\"" } ] }
    ],
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [ { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard_bash.py\"" } ] }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write", "hooks": [ { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/ruff_on_py.py\"" } ] }
    ]
  }
}
JSON
cat > .claude/settings.local.json.example <<'JSON'
{
  "guards": {
    "optiplex_hosts": ["optiplex", "oplx", "<optiplex-magicdns-name>", "<optiplex-tailscale-ip>", "<optiplex-lan-ip>"],
    "optiplex_forbidden": ["sudo", " su ", "doas", "pkexec", "psql", "pg_", ":5432"],
    "forbidden_paths": ["<optiplex-data-disk-mount>"]
  }
}
JSON
```

- [ ] **Step 4: Write the real `.claude/settings.local.json` (git-ignored; `executor: main-session`)**

Copy the example and replace the `<…>` placeholders with the real optiplex MagicDNS name, Tailscale IP, LAN IP, and the data-disk mount path from the founder's private notes. Do **not** commit it.

Run: `git check-ignore .claude/settings.local.json && python3 -c "import json;json.load(open('.claude/settings.local.json'))" && echo "local guards ok"`
Expected: the path printed (ignored) and `local guards ok`.

- [ ] **Step 5: Test the guard**

```bash
g() { printf '%s' "$1" | python3 .claude/hooks/guard_bash.py; echo "exit=$?"; }
g '{"tool_name":"Bash","tool_input":{"command":"python3 -m http.server --bind 0.0.0.0 8000"}}'     # expect exit=2
g '{"tool_name":"Bash","tool_input":{"command":"docker run -p 8080:8080 nginx"}}'                  # expect exit=2
g '{"tool_name":"Bash","tool_input":{"command":"ss -tlnp | grep 0.0.0.0"}}'                        # expect exit=0
g '{"tool_name":"Bash","tool_input":{"command":"docker run -p 127.0.0.1:8080:8080 nginx"}}'        # expect exit=0
g '{"tool_name":"Bash","tool_input":{"command":"ssh optiplex sudo systemctl restart foo"}}'         # expect exit=2 (local guards)
g '{"tool_name":"Bash","tool_input":{"command":"ssh optiplex uptime"}}'                             # expect exit=0
```
Expected: exit codes as commented (2,2,0,0,2,0); a one-line reason on stderr for each 2.

- [ ] **Step 6: Commit (not the local file)**

```bash
git add .claude/settings.json .claude/hooks .claude/settings.local.json.example
git commit -m "chore(hooks): status-on-start, ruff on edit, bind/optiplex guards

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 5: Lint scripts and CI

**Files:**
- Create: `scripts/lint-bind-targets.sh`, `scripts/lint-placeholders.sh`, `docs/adr/bind-allowlist.txt`, `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `bash scripts/lint-placeholders.sh` and `bash scripts/lint-bind-targets.sh` — called by skills, by every verification step below, and by CI.

- [ ] **Step 1: Write the bind-target lint**

```bash
mkdir -p scripts .github/workflows
cat > scripts/lint-bind-targets.sh <<'SH'
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
SH
chmod +x scripts/lint-bind-targets.sh
printf '# repo-relative paths allowed to bind all interfaces, one per line, each justified by an ADR\n' > docs/adr/bind-allowlist.txt
```

- [ ] **Step 2: Write the placeholder lint** (the three forbidden words are spelled with brackets so this file and the plans that quote it never trip the lint themselves)

```bash
cat > scripts/lint-placeholders.sh <<'SH'
#!/usr/bin/env bash
# CORVID CI: no placeholder tokens in docs/ (spec §3.2 — use UNVERIFIED in dossiers instead).
set -uo pipefail
hits=$(grep -rnE '\b(T[B]D|T[O]DO|F[I]XME|X[X]X)\b' docs/ --include='*.md' --exclude='TEMPLATE.md' --exclude-dir=raw 2>/dev/null || true)
if [ -n "$hits" ]; then echo "$hits"; echo "::error::placeholder tokens in docs/ — resolve them or mark UNVERIFIED"; exit 1; fi
echo "placeholder lint: ok"
SH
chmod +x scripts/lint-placeholders.sh
```

- [ ] **Step 3: Write CI**

```bash
cat > .github/workflows/ci.yml <<'YML'
name: ci
on: [push, pull_request]
jobs:
  docs-and-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install --quiet ruff mkdocs-material pytest
      - name: ruff (when Python exists)
        run: |
          if git ls-files '*.py' | grep -qv '^\.claude/hooks/'; then ruff format --check . && ruff check .; else echo "no project python yet"; fi
      - name: pytest (smoke until agent/ or coordinator/ exists)
        run: |
          if [ -d agent ] || [ -d coordinator ]; then pytest -q; else echo "no code yet — smoke ok"; fi
      - name: bind-target lint
        run: bash scripts/lint-bind-targets.sh
      - name: placeholder lint (docs)
        run: bash scripts/lint-placeholders.sh
      - name: mkdocs build
        run: mkdocs build
YML
```

- [ ] **Step 4: Run both lints and the build locally**

Run: `bash scripts/lint-bind-targets.sh && bash scripts/lint-placeholders.sh && .venv/bin/mkdocs build 2>&1 | tail -1`
Expected: `bind-target lint: ok`, `placeholder lint: ok`, `INFO    -  Documentation built in …`. If the placeholder lint fails, fix the offending doc (never relax the lint).

- [ ] **Step 5: Commit**

```bash
git add scripts docs/adr/bind-allowlist.txt .github/workflows/ci.yml
git commit -m "ci: ruff, pytest smoke, mkdocs build, bind-target and placeholder lints

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 6: Workflow directory convention

**Files:**
- Create: `.claude/workflows/README.md`

- [ ] **Step 1: Write the README**

```bash
mkdir -p .claude/workflows
cat > .claude/workflows/README.md <<'MD'
# Workflows

Claude Code **Workflow-tool scripts** (plain JavaScript, each beginning with `export const meta = {…}`), invoked by name with the Workflow tool. `research-sweep.js` (M2) runs the adversarially verified research sweep for the dossiers (spec §6.4); a `code-review.js` arrives with the first code (Phase 2). Scripts never run spikes on nodes — the main session does (spec §6.4).
MD
git add .claude/workflows/README.md
git commit -m "chore(workflows): directory convention

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 7: M0 status update

**Files:**
- Modify: `docs/status.md`

- [ ] **Step 1: Run `save-state`** — RESUME block: "M0 repo skeleton done (templates, skills, hooks, CI, mkdocs); next = M1 (R00, Phase 0 spec/plan, ADR-0002/0003/0004)"; add "node in use by" line = none; `_Last updated:_` today.
- [ ] **Step 2: Verify** — Run: `bash scripts/lint-placeholders.sh && git status --short | wc -l` → `placeholder lint: ok` and `0` after commit.
- [ ] **Step 3: Commit** — `docs(status): M0 complete` (+ trailer).

### Task 8: Remote and first push (`executor: founder` approval; main session runs the commands)

**Files:** none (GitHub side)

- [ ] **Step 1: Founder decides private vs public** (handoff block: "thecommrade/corvid — private or public?"). Default if asked to choose: **private**.
- [ ] **Step 2: Create the repo and the remote without switching the global gh account**

```bash
GH_TOKEN="$(gh auth token --user thecommrade)" gh repo create thecommrade/corvid --private --description "CORVID — a friends-scale compute co-op (planning)" --disable-wiki
git remote add origin https://thecommrade@github.com/thecommrade/corvid.git
git push -u origin main
```
(Replace `--private` with `--public` if the founder chose public.)

- [ ] **Step 3: Verify**

Run: `git remote -v | head -1 && GH_TOKEN="$(gh auth token --user thecommrade)" gh run list --repo thecommrade/corvid --limit 1`
Expected: remote URL with `thecommrade@`; the CI run listed (queued/running/completed). If CI fails, read the log (`gh run view --log-failed`) and fix in a follow-up commit — do not disable checks.

---

# M1 — Phase 0 package (R00, ADR-0002/0003/0004, Phase 0 spec + plan)

### Task 9: R00 — Phase 0 facts dossier

**Files:**
- Create: `docs/research/R00-phase0-facts.md`, `docs/runs/R00-inspection-<YYYY-MM-DD>.md`; raw capture in `docs/runs/raw/` (git-ignored)

**Interfaces:**
- Consumes: `remote-step` (aliases), templates (Task 1).
- Produces: fact IDs `R00-F1…Fn` cited by ADR-0002/0003/0004, the Phase 0 spec, and the Phase 0 plan; the **kernel-mode switch + rollback sequence** (with `<placeholders>`); the **Tailscale SSH/ACL state** used by Phase 0 step 0.

- [ ] **Step 1: Read-only inspection on all three nodes (`executor: main-session`; root-only reads are founder/`splx-root` steps)**

Save this as `docs/runs/raw/inspect.sh` (git-ignored) and run it locally and via each alias (`bash inspect.sh` locally; `ssh <alias> 'bash -s' < inspect.sh` remotely), teeing into `docs/runs/raw/R00-<node>-<date>.log`:

```bash
#!/usr/bin/env bash
# R00 read-only inspection. No state changes.
echo "HOST $(hostname)  DATE $(date -Is)"
echo "== tailscale =="; tailscale version | head -1; tailscale status --self --json 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); s=d["Self"]; print("BackendState",d.get("BackendState"),"| Online",s.get("Online"),"| caps-ssh", [c for c in (s.get("CapMap") or {}) if "ssh" in c.lower()])'
tailscale debug prefs 2>/dev/null | grep -E '"(RunSSH|CorpDNS|ExitNodeID|ShieldsUp|AdvertiseRoutes|NetfilterMode|NoSNAT|Hostname)"' | tr -d ' \t' | tr '\n' ' '; echo
tailscale dns status 2>/dev/null | grep -E 'Tailscale DNS:|MagicDNS:|^  - |Search Domains' | head -12
echo "-- tailscaled unit/flags --"; systemctl show tailscaled -p ExecStart --no-pager 2>/dev/null | cut -c1-300; grep -E '^(FLAGS|PORT)=' /etc/default/tailscaled 2>/dev/null; ls -l /dev/net/tun 2>/dev/null; ip -br link show tailscale0 2>/dev/null || echo "no tailscale0 (userspace mode?)"
echo "== dns =="; resolvectl status 2>/dev/null | grep -E 'Link|Current DNS|DNS Servers|DNS Domain|Protocols|Default Route' | head -30; grep -E '^nameserver' /etc/resolv.conf
echo "== routing (ip rule / tables) =="; ip rule; for t in $(ip rule | grep -oE 'lookup [0-9a-z]+' | awk '{print $2}' | sort -u); do echo "-- table $t --"; ip route show table "$t" 2>/dev/null | head -20; done
echo "== vpn units/ifaces (names only) =="; ip -br link | awk '$1 !~ /^(veth|br-|docker|lo)/'; systemctl list-units --type=service --state=running --no-pager 2>/dev/null | grep -iE 'proton|wg-quick|wireguard|openvpn' | awk '{print $1}'
echo "== ssh listeners =="; ss -tlnH 2>/dev/null | awk '$4 ~ /:22$/{print $4}'
echo "== ports in use (for ADR-0003) =="; ss -tlnH 2>/dev/null | awk '{print $4}' | sed 's/.*://' | sort -un | tr '\n' ' '; echo
echo "== versions =="; python3 --version; docker --version 2>/dev/null; systemctl --version | head -1
echo "== linger (for Phase 1 user units) =="; loginctl show-user "$USER" -p Linger 2>/dev/null
echo "== gpu =="; nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader 2>/dev/null || echo none
```

Root-only reads (no keys ever): on solarplexus `executor: Opus (splx-root)`/main-session with the agent key loaded; on optiplex `executor: founder`:
```bash
sudo wg show 2>/dev/null | grep -E '^interface|fwmark|listening' ; sudo grep -hE '^(Table|FwMark|PostUp|PostDown|PreUp|PreDown|AllowedIPs)\s*=' /etc/wireguard/*.conf 2>/dev/null
```
(Lines beginning `PrivateKey`/`PublicKey`/`Endpoint`/`Address` are deliberately not read.)

- [ ] **Step 2: Founder pastes the tailnet ACL `ssh` section and the DNS settings page state (`executor: founder`, admin console)** — handoff block: "Admin console → Access controls: paste the `ssh` block and any `tagOwners`; DNS page: are global nameservers set? MagicDNS on? HTTPS certificates enabled?" Record in the run file.

- [ ] **Step 3: Dated documentation facts (`executor: main-session`, WebFetch)** — fetch each and record statement + URL + date verified in R00 (if a page moved, find the current one on tailscale.com/kb and note it):

| Fact needed | Primary source to fetch |
|---|---|
| `--accept-dns` / MagicDNS behaviour: with no global nameserver configured, `*.ts.net` resolves via 100.100.100.100 and other queries use the OS resolver | https://tailscale.com/kb/1081/magicdns and https://tailscale.com/kb/1235/resolv-conf |
| Userspace networking mode: what it can/cannot do (no dialing tailnet IPs from the OS; SOCKS5/HTTP proxy) | https://tailscale.com/kb/1112/userspace-networking |
| `tailscale set --operator=` semantics | https://tailscale.com/kb/1080/cli |
| Tailscale SSH: `check` vs `accept`, check period, root by ACL | https://tailscale.com/kb/1193/tailscale-ssh and https://tailscale.com/kb/1018/acls (ssh section) |
| Key expiry default and "disable key expiry" | https://tailscale.com/kb/1028/key-expiry |
| Node sharing: one-directional; sharee identity | https://tailscale.com/kb/1084/sharing |
| Personal plan user/device limits (today's numbers) | https://tailscale.com/pricing |
| Tailscale + full-tunnel VPN coexistence / fwmark guidance | https://tailscale.com/kb/1105/other-vpns |
| `tailscale serve` identity headers (for S-05 later) | https://tailscale.com/kb/1312/serve |

- [ ] **Step 4: Write R00 from the template** — sections: Purpose; Facts table (inspection facts with spike-style IDs `R00-F…` sourced to the run file, doc facts with URLs); **"Kernel-mode switch + rollback (solarplexus)"** — the exact sequence derived from Step 1 with `<placeholders>` for addresses/tables, e.g.:

```bash
# precondition: founder present; root tmux on solarplexus; Plex/Immich idle
systemd-run --on-active=10m --unit=corvid-ts-rollback bash -c 'cp /etc/default/tailscaled.bak /etc/default/tailscaled && systemctl restart tailscaled'   # armed auto-rollback
cp /etc/default/tailscaled /etc/default/tailscaled.bak
sed -i 's/--tun=userspace-networking//' /etc/default/tailscaled       # only if FLAGS had it (R00-F?)
systemctl restart tailscaled && sleep 5 && tailscale status --self --json | grep -m1 '"Online"'
# VPN bypass: Tailscale's own rules (fwmark 0x80000 → main/default) must be consulted before the VPN's
# "not fwmark <vpn-mark> lookup <table>" rule; record the priorities seen on optiplex and replicate (R00-F?)
ip rule                                                                 # verify order
tailscale ping <peer-magicdns-name> && curl -s --max-time 5 http://<peer-tailnet-ip>:<closed-port> ; echo "dial test rc=$?"
systemctl stop corvid-ts-rollback.timer corvid-ts-rollback.service 2>/dev/null   # success → disarm
# rollback (manual): cp /etc/default/tailscaled.bak /etc/default/tailscaled && systemctl restart tailscaled
```
plus "Tailscale SSH/ACL state", "DNS state per node", "Ports in use on solarplexus", "Linger + GPU per node", Open questions, Change log. Mark anything not observed `UNVERIFIED`.

- [ ] **Step 5: Sanitise and verify**

Run: `grep -nE '192\.168\.|100\.[0-9]+\.[0-9]+\.[0-9]+|@|id_[a-z]|/home/[a-z]' docs/research/R00-phase0-facts.md docs/runs/R00-inspection-*.md || echo "sanitised"; bash scripts/lint-placeholders.sh; .venv/bin/mkdocs build 2>&1 | tail -1`
Expected: `sanitised`, `placeholder lint: ok`, build OK. Every Facts row has a URL or run-file reference and a date.

- [ ] **Step 6: Commit** — `git add docs/research/R00-phase0-facts.md docs/runs/R00-inspection-*.md && git commit -m "docs(research): R00 Phase 0 facts (DNS, tailscaled modes, routing recipe, ACL state)"` (+ trailer).

### Task 10: ADR-0002 — Membership (Accepted)

**Files:**
- Create: `docs/adr/0002-membership.md`; Modify: `docs/status.md` (row)

- [ ] **Step 1: Write the ADR with `new-adr`** — Context: R00 facts on sharing (one-directional; sharee is not a member identity), free-plan limits (number + date), zero-login needs identity (CLAUDE.md §11, ADR-0001). Decision: (1) members are **invited as tailnet users** (not shared nodes); node sharing is not used for members (may be used for devices); (2) ACL baseline: tags `tag:hub` (solarplexus, optiplex, ahnoway-as-builder) and `tag:member`; allow `member → hub` on CORVID service ports only, `hub → member` on agent/rpc ports only, **deny member ↔ member by default** (privacy between friends' machines); Tailscale SSH `accept` for the founder's own devices per Phase 0 step 0; (3) key expiry disabled on hub nodes; members keep default expiry; (4) Zach is invited as a user when he is ready (founder phone call). Consequences: invite flow = the first line of the onboarding index card; the member count ceiling = the free-plan number (dated) → revisit (Headscale escape hatch in CLAUDE.md §3.1) if exceeded. §4 rows: none.
- [ ] **Step 2: Verify** — `bash scripts/lint-placeholders.sh` ok; no IPs; commit `docs(adr): ADR-0002 membership` (+ trailer).

### Task 11: ADR-0004 — Exit criteria on a one-LAN build fleet (Accepted)

**Files:**
- Create: `docs/adr/0004-exit-criteria-one-lan-fleet.md`; Modify: `docs/status.md`

- [ ] **Step 1: Write with `new-adr`** — Context: CLAUDE.md §6 Phase 0/1 exits say "across houses"; build fleet shares one LAN; friends' machines are members not build nodes; Zach's shared node exists. Decision: Phase 0 complete = (a) LAN trio all-pairs name-ping + (b) ≥ 1 cross-house name-ping (Zach's node when online, or an invited member's device), (b) is `executor: founder` (phone call, "install Tailscale / accept invite", no CORVID software). Phase 1 complete = thesis on the LAN trio (a completion from a model meeting the §7 criterion, tok/s recorded) + the cross-house completion as a **named follow-on** (owner founder, trigger = first member machine online, recorded in status.md when done). Consequences: CLAUDE.md §6 wording is not edited; status.md marks each phase with both halves.
- [ ] **Step 2: Verify + commit** — lint ok; `docs(adr): ADR-0004 exit criteria on a one-LAN fleet` (+ trailer).

### Task 12: ADR-0003 — Endpoints (Proposed) + Caddy §4 row

**Files:**
- Create: `docs/adr/0003-endpoints.md`; Modify: `CLAUDE.md` (§4 row only), `docs/status.md`

- [ ] **Step 1: Write with `new-adr` + `add-dependency`** — Context: port 8080 on solarplexus is taken (R00 "ports in use"); Caddy already runs on the host; members reach services by URL (CLAUDE.md §11). Decision (Proposed until the Phase 1 spec): CORVID services on solarplexus bind the **tailnet IP only**: inference (llama-server OpenAI API) `:8090`, coordinator API `:8091`, status page `:8092`, chat UI `:8093` (confirm free in R00; shift by +10 if not); Caddy front door on the tailnet IP `:80` (and `:443` with `tailscale cert` when HTTPS is enabled) routing `/` → landing, `/chat` → `:8093`, `/v1` → `:8090`, `/api` → `:8091`, `/status` → `:8092`; the member URL is `http://solarplexus.<tailnet>.ts.net/`. On acceptance (M3) CLAUDE.md §3.2's `:8080` line changes to the Caddy URL + `:8090`. §4 row added **now**: `| Caddy | Reverse proxy / front door for tailnet web apps | Apache-2.0 | Matt Holt & the Caddy contributors |` (verify licence at github.com/caddyserver/caddy LICENSE, date it in the ADR).
- [ ] **Step 2: Verify + commit (one commit: ADR + CLAUDE.md row + status row)** — `git add docs/adr/0003-endpoints.md CLAUDE.md docs/status.md && git commit -m "docs(adr): ADR-0003 endpoints (Proposed) + §4 credit for Caddy"` (+ trailer). Run `git diff HEAD~1 -- CLAUDE.md | grep '^+' | grep -c '| Caddy' ` → `1` (only the row changed).

### Task 13: Phase 0 spec

**Files:**
- Create: `docs/superpowers/specs/<YYYY-MM-DD>-phase-0-handshake-design.md`

- [ ] **Step 1: Write the spec** using the skeleton (package spec §7): **Goal/exit** = ADR-0004 Phase 0 definition; **Architecture** = tailnet state after Phase 0: MagicDNS on all build nodes, solarplexus kernel-mode with VPN bypass, key expiry off, ACL baseline per ADR-0002, unattended access path per step 0, endpoint/port reservations per ADR-0003; **Components** = the eight steps 0–7 of package spec §5, each with executor + R00 fact IDs; **Data flow** = DNS resolution path per node (diagram in words), ssh paths; **Error handling** = rollback for step 2, "what if MagicDNS breaks Pi-hole resolution" (revert `--accept-dns=false`), "what if Tailscale SSH ACL change locks out" (LAN path remains); **Acceptance tests** = all-pairs `ping -c 2 <name>` from each node, `ssh -o BatchMode=yes` preflight to both hubs, tailnet-bound test listener curl'd from both peers, one cross-house name-ping, `tailscale status` shows no key expiry for hubs (founder screenshot/paste), `resolvectl query` shows Pi-hole still serving non-ts.net on LAN nodes; **Out of scope** = llama.cpp, agent; **ADRs** = 0002, 0003 (Proposed), 0004.
- [ ] **Step 2: Verify + commit** — placeholder lint ok; mkdocs build ok; `docs(spec): Phase 0 handshake design` (+ trailer).

### Task 14: Phase 0 plan (for Opus)

**Files:**
- Create: `docs/superpowers/plans/<YYYY-MM-DD>-phase-0-handshake.md`

- [ ] **Step 1: Invoke `superpowers:writing-plans` against the Phase 0 spec** and produce the plan with: the header (goal, architecture, tech stack, spec path, **Read: CLAUDE.md, docs/status.md, R00, ADR-0002/0003/0004**); the Appendix A preflight as Task 0; one task per step 0–7 with bite-sized steps, every step tagged `executor:`; exact commands — e.g. step 1 `tailscale set --accept-dns=true` then `resolvectl status | grep -A3 tailscale0` and `resolvectl query solarplexus.<tailnet>.ts.net`; step 2 = the R00 sequence verbatim with the founder-presence precondition and armed auto-rollback; step 3 founder handoff block; step 4/6 link ADRs; step 5 alias edits (founder's `networkdocs`; plan only notes); step 7 verification block:

```bash
for h in ahnoway solarplexus optiplex; do for t in ahnoway solarplexus optiplex; do [ "$h" = "$t" ] && continue; printf '%s -> %s: ' "$h" "$t"; ssh -o BatchMode=yes "$h" "ping -c 2 -W 2 $t >/dev/null && echo ok || echo FAIL" 2>/dev/null || (ping -c 2 -W 2 "$t" >/dev/null && echo ok || echo FAIL); done; done
# throwaway tailnet-bound listener on solarplexus (tailnet IP only; never 0.0.0.0), curl from the other two, then kill it
```
with expected outputs and the run-file + status-summary closing steps.

- [ ] **Step 2: Self-review per the writing-plans checklist** (spec coverage, placeholder scan via `bash scripts/lint-placeholders.sh`, consistency of names/ports with ADR-0003 and R00).
- [ ] **Step 3: Commit** — `docs(plan): Phase 0 handshake (executor: Opus + founder)` (+ trailer).

### Task 15: M1 close

- [ ] **Step 1: `save-state`** — RESUME: "M1 done; Phase 0 plan ready for Opus (`docs/superpowers/plans/…phase-0-handshake.md`); next = M2 research sweep (Phase 0 steps 0–2 must land before S-01 tailnet leg / S-05)"; add the "Node in use by" line when Opus is dispatched.
- [ ] **Step 2: Tag and push** — `git tag -a m1 -m "M1: Phase 0 package" && git push --follow-tags` (after Task 8).

---

# M2 — Research sweep + spikes

### Task 16: `research-sweep.js` (Workflow-tool script)

**Files:**
- Create: `.claude/workflows/research-sweep.js`

**Interfaces:**
- Consumes: the dossier definitions (spec §6.1); the Workflow tool (`agent`, `pipeline`, `parallel`, `phase`, `log`, `args`).
- Produces: a JSON object `{ <Rnn>: { research, verdicts, gaps } }` returned by the workflow, which Task 23 renders into dossiers. `args` = `{ dossiers: ["R01", …] , date: "YYYY-MM-DD", maxFactsRefuted: 20 }`.

- [ ] **Step 1: Write the script**

```bash
cat > .claude/workflows/research-sweep.js <<'JS'
export const meta = {
  name: 'research-sweep',
  description: 'CORVID research sweep: one researcher per dossier, adversarial refutation of every dated fact, completeness critic (spec §6.4)',
  whenToUse: 'Run for M2, or to refresh a stale dossier: args = { dossiers: ["R03"], date: "YYYY-MM-DD" }',
  phases: [
    { title: 'Research', detail: 'one agent per dossier, primary sources only' },
    { title: 'Refute', detail: 'one skeptic per fact' },
    { title: 'Gaps', detail: 'completeness critic per dossier' },
  ],
}
const DATE = (args && args.date) || 'UNDATED'
const MAX_REFUTED = (args && args.maxFactsRefuted) || 20
const ONLY = (args && args.dossiers) || null

const FACTS = { type: 'object', properties: {
  dossier: { type: 'string' },
  facts: { type: 'array', items: { type: 'object', properties: {
    id: { type: 'string' }, statement: { type: 'string' }, source_url: { type: 'string' },
    date_verified: { type: 'string' }, version: { type: 'string' },
    confidence: { type: 'string', enum: ['verified', 'unverified'] } },
    required: ['id', 'statement', 'source_url', 'date_verified', 'confidence'] } },
  recommendations: { type: 'array', items: { type: 'string' } },
  open_questions: { type: 'array', items: { type: 'string' } },
  credits: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, what: { type: 'string' }, license: { type: 'string' },
    author: { type: 'string' }, source_url: { type: 'string' } },
    required: ['name', 'what', 'license', 'author', 'source_url'] } } },
  required: ['dossier', 'facts', 'recommendations', 'open_questions', 'credits'] }
const VERDICT = { type: 'object', properties: {
  fact_id: { type: 'string' }, refuted: { type: 'boolean' }, reason: { type: 'string' },
  corrected_statement: { type: 'string' }, source_url: { type: 'string' } },
  required: ['fact_id', 'refuted', 'reason'] }
const GAPS = { type: 'object', properties: { missing: { type: 'array', items: { type: 'string' } } }, required: ['missing'] }

const COMMON = `You are researching for CORVID, a friends-scale compute co-op (Tailscale mesh; llama.cpp RPC inference; Python agent + Postgres coordinator; Linux build fleet: a laptop with an RTX 2070 Super 8 GB, a hub with a GTX 970 4 GB on driver 535/CUDA 12.2 and Tailscale in userspace mode, a second node with an RTX 3050 6 GB on CUDA 13.1; friends on macOS/Windows later). Use PRIMARY sources only (official docs, the project's own repo/README/LICENSE at a pinned tag, vendor pricing pages). For every fact give: a precise statement, the exact source URL, today's date ${DATE} as date_verified, and the version/tag/commit it applies to when version-dependent. If you could not verify something from a primary source, include it with confidence "unverified" — never guess silently. Prefer fewer, sharper facts a plan can cite over many vague ones. Also list recommendations for the spec, open questions, and the credit rows (name, what we take, license at that tag, author, source URL) for anything CORVID would ship or rely on.`

const DOSSIERS = [
  { id: 'R01', title: 'Fleet & network', qs: `Only the documentation part of R01 (measurements come from spike S-01): Tailscale DERP/NAT facts relevant to home networks (direct vs relayed, UPnP/NAT-PMP, what 'tailscale netcheck' fields mean); what latency/bandwidth llama.cpp RPC needs per token (from the llama.cpp RPC README); how Wi-Fi vs wired affects that. Seeds: https://tailscale.com/kb/1257/connection-types , https://tailscale.com/kb/1232/derp-servers , https://github.com/ggml-org/llama.cpp/blob/master/tools/rpc/README.md` },
  { id: 'R02', title: 'Tailscale: membership, ACLs, DNS, identity', qs: `Personal plan user and device limits today; invite vs node-sharing semantics (is sharing one-directional? does a sharee get a per-request identity usable for zero-login?); ACL basics incl. tags, ssh section check vs accept; MagicDNS + split DNS behaviour with an existing LAN resolver; key expiry default and disabling; 'tailscale serve' identity headers (exact header names) vs 'tailscale whois'; 'tailscale set --operator'; userspace networking limits; Tailscale SSH. Seeds: https://tailscale.com/pricing , https://tailscale.com/kb/1084/sharing , https://tailscale.com/kb/1018/acls , https://tailscale.com/kb/1081/magicdns , https://tailscale.com/kb/1028/key-expiry , https://tailscale.com/kb/1312/serve , https://tailscale.com/kb/1080/cli , https://tailscale.com/kb/1112/userspace-networking , https://tailscale.com/kb/1193/tailscale-ssh` },
  { id: 'R03', title: 'llama.cpp RPC on this fleet', qs: `Latest release tag and date; whether release binaries for Linux include rpc-server (and which CUDA versions/backends they ship for Linux), and whether the official Docker images include rpc-server; how to build with -DGGML_RPC=ON (+CUDA) and the CUDA toolkit/driver requirements; CUDA support for Maxwell cc 5.2 in current builds and what CUDA 12.x toolkit still supports it; rpc-server flags at that tag (host/port/mem/threads/cache) and the security warning; llama-server --rpc semantics and how layers are split across RPC devices; which llama-server/rpc-server flags disable request/prompt logging; llama-bench --rpc; systemd user unit + linger requirements; /dev/nvidia* permissions for a non-root service user. Seeds: https://github.com/ggml-org/llama.cpp/releases , https://github.com/ggml-org/llama.cpp/blob/master/tools/rpc/README.md , https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md , https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md , https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/` },
  { id: 'R04', title: 'Model selection for Phase 1', qs: `Candidate open-weight instruct models and their GGUF quantisations with file sizes, ranked on a NAMED dated basis (e.g. the current Open LLM Leaderboard or LMArena/Artificial Analysis snapshot — cite which), that satisfy: weights + KV cache at the chosen quant EXCEED ~25 GB (the largest single node's 6 GB VRAM + ~19 GB free RAM) so the model is impossible on one node, yet fit the pool (≈18 GB VRAM + ≈63 GB RAM) — give the GB arithmetic incl. KV cache for 4k and 8k context; plus a fallback list of models that exceed 8 GB VRAM; model licences (name, gated?) for §4 rows. Seeds: https://huggingface.co/models?library=gguf&sort=trending , model cards of Llama 3.x 70B, Qwen3 32B/30B-A3B, Gemma 3 27B, Mistral Small, DeepSeek-R1 distills; https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md for KV sizing notes` },
  { id: 'R05', title: 'Agent platform matrix', qs: `Linux (full depth): systemd user services + linger; idle detection on Wayland (logind IdleHint, org.freedesktop.ScreenSaver GetSessionIdleTime, KDE/GNOME specifics) and X11 (xprintidle); battery/AC via upower or /sys/class/power_supply; cgroup v2 resource control via systemd-run --user (CPUQuota, MemoryMax, IOWeight) and LIVE changes via systemctl set-property; GPU caps realities (no compute-share on consumer NVIDIA; VRAM via app limits); kill switch patterns. macOS and Windows (docs-only): launchd LaunchAgents; Task Scheduler / Windows service; idle (IOKit HIDIdleTime; GetLastInputInfo); battery (pmset; SYSTEM_POWER_STATUS); caps (taskpolicy/nice; Job Objects). Opt-in model design notes. Packaging at outline depth: Python + uv/pipx vs PyInstaller single binary; macOS notarization and Windows code-signing costs. Seeds: https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html , https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html , https://www.freedesktop.org/software/systemd/man/latest/loginctl.html , https://upower.freedesktop.org/docs/ , https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html , https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-getlastinputinfo , https://learn.microsoft.com/windows/win32/procthread/job-objects , https://docs.astral.sh/uv/` },
  { id: 'R06', title: 'Coordinator & schema', qs: `Postgres in Docker Compose as a separate project (resource limits via deploy.resources / cpus / mem_limit, data dir bind mounts, healthchecks); queue pattern with SELECT ... FOR UPDATE SKIP LOCKED; heartbeat/roster schema patterns; fair-share when contended (max-min) with NO quotas; identity from Tailscale (whois/headers) for an API; log policy (metadata only). Seeds: https://docs.docker.com/reference/compose-file/deploy/ , https://docs.docker.com/reference/compose-file/services/ , https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE , https://hub.docker.com/_/postgres` },
  { id: 'R07', title: 'Status page & identity', qs: `Grafana licence (AGPL) and OSS vs Enterprise features; lightweight alternatives; how identity headers from 'tailscale serve' or whois reach an app behind Caddy; Caddy reverse_proxy + handle_path basics and its licence; what a 'live map' of nodes needs (heartbeat age, capabilities, pool capacity/utilisation/threshold panels per ADR-0001). Seeds: https://github.com/grafana/grafana/blob/main/LICENSE , https://caddyserver.com/docs/caddyfile/directives/reverse_proxy , https://github.com/caddyserver/caddy/blob/master/LICENSE` },
  { id: 'R08', title: 'Chat front-end for Phase 1', qs: `Current licences (at a pinned version) of Open WebUI, LibreChat, Lobe Chat, Hollama, and any other mature OpenAI-compatible chat UI; whether each supports header-based/trusted-proxy auth (zero-login via Tailscale identity headers); per-user history isolation; disabling prompt logging/telemetry; deployable as a single compose service. Seeds: https://github.com/open-webui/open-webui/blob/main/LICENSE , https://docs.openwebui.com/ , https://github.com/danny-avila/LibreChat/blob/main/LICENSE , https://www.librechat.ai/docs , https://github.com/lobehub/lobe-chat/blob/main/LICENSE` },
  { id: 'R09', title: 'SharedLLM & alternatives', qs: `For each of SharedLLM, exo, GPUStack, prima.cpp, Ollama: latest release tag + date, licence at that tag, OS/GPU support matrix, whether it coordinates llama.cpp RPC workers or has its own sharding, last-commit date, maturity signals. Seeds: the projects' GitHub repos (search them), https://github.com/exo-explore/exo , https://github.com/gpustack/gpustack , https://github.com/Lizonghang/prima.cpp , https://github.com/ollama/ollama` },
  { id: 'R10', title: 'Hub integration points + Phase 3–5 outlines', qs: `Tdarr node model (how a remote Tdarr node joins a server; licence/terms — Tdarr is not open source; what that means for §4); Immich machine-learning container run remotely (config, GPU support, licence AGPL); Docker resource caps for batch jobs (cpus, memory, gpus, no host mounts beyond scratch); WSL2 + Docker + CUDA on Windows; gVisor as an upgrade path; Folding@home team setup basics. Seeds: https://docs.tdarr.io/ , https://immich.app/docs/guides/remote-machine-learning , https://docs.docker.com/engine/containers/resource_constraints/ , https://docs.nvidia.com/cuda/wsl-user-guide/ , https://gvisor.dev/docs/ , https://foldingathome.org/` },
]
const todo = ONLY ? DOSSIERS.filter(d => ONLY.includes(d.id)) : DOSSIERS
log(`research-sweep: ${todo.map(d => d.id).join(', ')} (date ${DATE})`)

const researchPrompt = d => `${COMMON}\n\nDOSSIER ${d.id} — ${d.title}.\nKey questions (each must yield citable facts): ${d.qs}\nReturn the structured output; fact ids must be ${d.id}-F1, ${d.id}-F2, …`
const refutePrompt = (d, f) => `You are an adversarial fact-checker. Try to REFUTE this claim using the cited primary source (fetch it) and, if needed, one other primary source. Claim (${f.id}, from dossier ${d.id} ${d.title}): "${f.statement}" — cited source: ${f.source_url} — version: ${f.version || 'n/a'}. Decide refuted=true if the source does not support the claim as stated, the claim is outdated for the stated version, or the source is not primary. If refuted, give the corrected statement and the URL that supports it. If you cannot reach the source, refuted=true with reason "source unreachable". Be strict.`
const gapsPrompt = (d, r) => `You are a completeness critic for dossier ${d.id} — ${d.title}. Key questions it had to answer: ${d.qs}\nHere are the facts it produced:\n${r.facts.map(f => `- ${f.id}: ${f.statement} [${f.confidence}]`).join('\n')}\nList what is MISSING for a plan writer to use this dossier without further research (specific questions, not generalities). If nothing material is missing, return an empty list.`

const results = await pipeline(
  todo,
  d => agent(researchPrompt(d), { label: `research:${d.id}`, phase: 'Research', schema: FACTS }),
  (r, d) => {
    if (!r) return null
    const facts = r.facts.slice(0, MAX_REFUTED)
    if (r.facts.length > MAX_REFUTED) log(`${d.id}: ${r.facts.length - MAX_REFUTED} facts beyond the refutation cap are left unverified`)
    return parallel(facts.map(f => () => agent(refutePrompt(d, f), { label: `refute:${f.id}`, phase: 'Refute', schema: VERDICT })))
      .then(vs => ({ research: r, verdicts: vs.filter(Boolean) }))
  },
  (x, d) => x ? agent(gapsPrompt(d, x.research), { label: `gaps:${d.id}`, phase: 'Gaps', schema: GAPS }).then(g => ({ ...x, gaps: g })) : null,
)
const out = {}
todo.forEach((d, i) => { out[d.id] = results[i] })
return out
JS
```

- [ ] **Step 2: Syntax check and commit**

Run: `node --check .claude/workflows/research-sweep.js 2>/dev/null && echo "syntax ok" || python3 -c "print('node not installed — the Workflow tool parses the script; proceed')"`
Expected: `syntax ok` or the proceed message.

```bash
git add .claude/workflows/research-sweep.js
git commit -m "chore(workflows): research-sweep (researchers → refuters → completeness critic)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 3: Run it** (`executor: main-session`) — Workflow tool with `name: "research-sweep"` (or the script path) and `args: { "dossiers": ["R01","R02","R03","R04","R05","R06","R07","R08","R09","R10"], "date": "<today>", "maxFactsRefuted": 20 }`. Save the returned JSON to `docs/runs/research-sweep-<date>.json` (sanitise nothing needed — it contains only public facts; still grep for IPs). This can run while spikes S-01…S-06 execute.

### Task 17: S-01 — throughput and latency between all three nodes

**Files:**
- Create: `docs/research/spikes/S-01-fleet-throughput-latency.md`, `docs/runs/S-01-<date>.md`

- [ ] **Step 1: Card from template** — Node(s): all three; Executor: main-session; Dependencies: LAN leg none; tailnet leg after Phase 0 steps 0–2; Preconditions: Plex idle (founder), AC on ahnoway, no other spike; Cap: Appendix B per node + **network exception** (≤ 60 s per pair per leg, off-peak, Plex idle — request from founder); Time box: 30 min; Abort: Plex stream starts.
- [ ] **Step 2: Commands** (python method needs no installs; use `iperf3` where present on both ends — it is on ahnoway)

```bash
# on the SERVER node (bind a specific IP: tailnet IP for the tailnet leg, LAN IP for the LAN leg — never 0.0.0.0)
mkdir -p ~/corvid-s01 && head -c 200M /dev/urandom > ~/corvid-s01/blob.bin
cd ~/corvid-s01 && systemd-run --user --scope -p CPUQuota=<B> -p MemoryMax=<B> nice -n 19 python3 -m http.server --bind <server-ip> 18080 &
# on the CLIENT node
for i in 1 2 3; do curl -s -o /dev/null -w '%{speed_download}\n' http://<server-ip>:18080/blob.bin; done   # bytes/s, take the median
ping -c 20 -i 0.2 <server-ip> | tail -1                                                                    # rtt min/avg/max/mdev
# iperf3 variant when present on both ends: server `iperf3 -s -B <server-ip> -1`; client `iperf3 -c <server-ip> -t 10 -J | jq '.end.sum_received.bits_per_second'`
```
Run every ordered pair (6) on the LAN leg, and again on the tailnet leg after Phase 0 step 2; record Tailscale mode per node and whether the path was direct (`tailscale status` shows `direct`).
- [ ] **Step 3: Undo** — `pkill -f 'http.server --bind <server-ip> 18080'; rm -rf ~/corvid-s01; ss -tln | grep -c ':18080' ` → `0` on each server node.
- [ ] **Step 4: Result** — table: pair · leg · Mbit/s (median) · rtt avg/mdev · direct? · Tailscale mode. Sanitise IPs to node names in the run file. File into R01 (and note "repeat when wired").
- [ ] **Step 5: Commit** — `docs(spike): S-01 fleet throughput/latency — <headline numbers>` (+ trailer).

### Task 18: S-02 — llama.cpp build/install per node

**Files:**
- Create: `docs/research/spikes/S-02-llamacpp-install-per-node.md`, `docs/runs/S-02-<date>.md`

- [ ] **Step 1: Card** — Node(s): all three; Executor: main-session (founder for any package install); Dependencies: R03's release/Docker facts (Task 16 output) — if R03 is not done yet, run the decision tree below and file the facts into R03; Cap: Appendix B (builds are CPU-heavy: `CPUQuota` per node; time box 60 min per node); Preconditions: disk ≥ 5 GB free in scratch; AC on ahnoway.
- [ ] **Step 2: Decision tree (record which branch each node took, with versions)**

```bash
# 0) facts first
nvidia-smi --query-gpu=name,driver_version,compute_cap --format=csv,noheader; command -v cmake nvcc gcc g++ git | xargs -n1 echo found:
# 1) release binary: does the latest Linux zip contain rpc-server? (R03-F? says) — if yes:
TAG=<pinned tag>; mkdir -p ~/corvid-s02 && cd ~/corvid-s02 && curl -sL -o llama.zip "https://github.com/ggml-org/llama.cpp/releases/download/$TAG/llama-$TAG-bin-ubuntu-x64.zip" && unzip -q llama.zip && ls */rpc-server */llama-server */llama-bench
# 2) docker (only where the NVIDIA container toolkit exists — solarplexus): does ghcr.io/ggml-org/llama.cpp:server-cuda* ship rpc-server? (R03-F?)
# 3) source build (needs cmake; CUDA needs nvcc + a toolkit matching the driver):
git clone --depth 1 --branch "$TAG" https://github.com/ggml-org/llama.cpp ~/corvid-s02/llama.cpp && cd ~/corvid-s02/llama.cpp
systemd-run --user --scope -p CPUQuota=<B> -p MemoryMax=<B> nice -n 19 bash -c 'cmake -B build -DGGML_RPC=ON && cmake --build build --config Release -j2 --target rpc-server llama-server llama-bench'   # CPU backend
# CUDA variant (only if nvcc present and its version is supported by the driver): add -DGGML_CUDA=ON [-DCMAKE_CUDA_ARCHITECTURES=52 on the GTX 970]
./build/bin/rpc-server --help | head -30   # record flags: host/port/mem/threads/cache
```
Installs of `cmake`/CUDA toolkit are `executor: founder` (ahnoway: pacman, no auto-confirm flags; optiplex: apt; solarplexus: `splx-root`) and happen only if the founder agrees — otherwise record `UNVERIFIED: CUDA build on <node>` and use the CPU backend for S-03.
- [ ] **Step 3: Undo** — keep the built binaries under `~/corvid-s02/` for S-03/S-04 (documented on the card; removed after S-04); remove zips/`build/` intermediates: `rm -rf ~/corvid-s02/llama.zip ~/corvid-s02/llama.cpp/build/CMakeFiles`.
- [ ] **Step 4: Result + commit** — table: node · branch taken (release/docker/source) · tag · backend (CPU/CUDA+version) · rpc-server flags observed · build time. File into R03. `docs(spike): S-02 llama.cpp per node — <branches>` (+ trailer).

### Task 19: S-03 — tiny-model RPC split ahnoway ↔ optiplex

**Files:**
- Create: `docs/research/spikes/S-03-tiny-rpc-split.md`, `docs/runs/S-03-<date>.md`

- [ ] **Step 1: Card** — Nodes: ahnoway (llama-server/bench) + optiplex (rpc-server); Executor: main-session; Dependencies: S-02 on both; Cap: Appendix B (`--mem 600` on optiplex rpc-server, `--mem 800`-equivalent via `-ngl` on ahnoway); Preconditions: optiplex load < 4.0, AC on ahnoway; Time box: 45 min.
- [ ] **Step 2: Commands**

```bash
# model (≈ 270–500 MB; record the exact URL used + sha256 on the card; both Apache-2.0 — credit on the card, not §4)
mkdir -p ~/corvid-s03 && cd ~/corvid-s03
curl -sL -o model.gguf "https://huggingface.co/bartowski/SmolLM2-360M-Instruct-GGUF/resolve/main/SmolLM2-360M-Instruct-Q8_0.gguf" || curl -sL -o model.gguf "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
sha256sum model.gguf; scp model.gguf <optiplex alias>:~/corvid-s03/   # not needed for rpc (weights stream from the host) — only if benching locally there
# optiplex: rpc-server on the TAILNET IP only (flags per S-02 output)
ssh <optiplex alias> 'systemd-run --user --scope -p CPUQuota=120% -p MemoryMax=3.2G nice -n 19 ~/corvid-s02/<path>/rpc-server -H <optiplex-tailnet-ip> -p 50052 --mem 600 -t 4' &
# ahnoway: local baseline vs RPC
systemd-run --user --scope -p CPUQuota=120% -p MemoryMax=1.6G nice -n 19 ~/corvid-s02/<path>/llama-bench -m ~/corvid-s03/model.gguf -ngl 99 -p 128 -n 64 -r 3
systemd-run --user --scope -p CPUQuota=120% -p MemoryMax=1.6G nice -n 19 ~/corvid-s02/<path>/llama-bench -m ~/corvid-s03/model.gguf --rpc <optiplex-tailnet-ip>:50052 -ngl 99 -p 128 -n 64 -r 3
nvidia-smi --query-compute-apps=pid,used_memory --format=csv   # on both nodes during the run → VRAM under caps
```
- [ ] **Step 3: Undo** — `ssh <optiplex alias> 'pkill -f "rpc-server -H"'; ssh <optiplex alias> 'ss -tln | grep -c 50052'` → `0`; keep model for S-04; `rm -rf ~/corvid-s03` after S-04.
- [ ] **Step 4: Result + commit** — pp/tg tok/s local vs RPC (Wi-Fi, direct path?), VRAM used per node, any errors. File into R03. `docs(spike): S-03 tiny RPC split — local <x> t/s vs rpc <y> t/s` (+ trailer).

### Task 20: S-04 — thesis spike (exception required)

**Files:**
- Create: `docs/research/spikes/S-04-thesis-split.md`, `docs/runs/S-04-<date>.md`

- [ ] **Step 1: Card** — Nodes: 2–3 of the fleet per R04's recommendation; Executor: main-session; Dependencies: S-03, R04 recommendation (model + GB arithmetic); **Exception record:** request per node (e.g. ahnoway VRAM ≤ 7 GB / RAM ≤ 10 GB; optiplex VRAM ≤ 5 GB / RAM ≤ 12 GB; solarplexus VRAM ≤ 3 GB / RAM ≤ 8 GB; CPUQuota up to 400%/300%/200%) for ≤ 90 min, granted by the founder in writing on the card; Preconditions: Plex/Immich idle, optiplex load < 3.0, AC on ahnoway, disk on the model-store path ≥ model size + 2 GB; Time box: 90 min; Abort: any node swapping, GPU temp > 85 °C, Plex stream starts.
- [ ] **Step 2: Commands**

```bash
# model store on the hub's storage pool (R01 records the path); download once there, serve from it
ssh <solarplexus alias> 'mkdir -p <model-store>/<model> && cd <model-store>/<model> && curl -L -o model.gguf "<R04 URL>" && sha256sum model.gguf'
# rpc-servers on the worker nodes (tailnet IP only), caps = the granted exception
ssh <optiplex alias> 'systemd-run --user --scope -p CPUQuota=<granted> -p MemoryMax=<granted> nice -n 19 ~/corvid-s02/<path>/rpc-server -H <optiplex-tailnet-ip> -p 50052 --mem <granted-MB>' &
systemd-run --user --scope -p CPUQuota=<granted> -p MemoryMax=<granted> nice -n 19 ~/corvid-s02/<path>/rpc-server -H <ahnoway-tailnet-ip> -p 50052 --mem <granted-MB> &   # if ahnoway is a worker
# llama-server on the host node chosen by R03/R04 (solarplexus needs kernel-mode Tailscale to dial — Phase 0 step 2 — else host on ahnoway)
systemd-run --user --scope -p CPUQuota=<granted> -p MemoryMax=<granted> nice -n 19 <path>/llama-server -m <model-store>/<model>/model.gguf --rpc <worker1-tailnet-ip>:50052,<worker2-tailnet-ip>:50052 -ngl 99 -c 4096 --host <host-tailnet-ip> --port 8090 --log-disable &
curl -s http://<host-tailnet-ip>:8090/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"x","messages":[{"role":"user","content":"In two sentences, what is a village utility?"}],"max_tokens":96}' | jq '.choices[0].message.content, .usage'
<path>/llama-bench -m <model-store>/<model>/model.gguf --rpc <worker1>:50052,<worker2>:50052 -ngl 99 -p 128 -n 64 -r 2
nvidia-smi --query-compute-apps=pid,used_memory --format=csv; free -g | head -2     # on every node during the run
```
Also run the single-node comparison R04 asks for: the same model on optiplex alone with CPU offload (`-ngl` as fits) — expect failure or unusable tok/s; record it. (The flag that disables request logging is the one R03 found; `--log-disable` is the placeholder name to confirm against R03.)
- [ ] **Step 3: Undo** — kill all llama/rpc processes on all nodes (`pkill -f rpc-server; pkill -f llama-server`), confirm ports closed, remove `~/corvid-s02 ~/corvid-s03` scratch on all nodes; the model may stay in the model store (it is Phase 1's model) — note it on the card.
- [ ] **Step 4: Result + commit** — GB per node (VRAM/RAM), tok/s (pp/tg), the completion text (proof), the single-node comparison, the exception record. File into R03/R04. `docs(spike): S-04 thesis split — <model> across <n> nodes at <y> t/s` (+ trailer).

### Task 21: S-05 — Tailscale identity headers via `tailscale serve`

**Files:**
- Create: `docs/research/spikes/S-05-serve-identity-headers.md`, `docs/runs/S-05-<date>.md`

- [ ] **Step 1: Card** — Node: ahnoway (serve) + optiplex (client); Executor: main-session; Dependencies: Phase 0 step 0 (operator mode on ahnoway: `sudo tailscale set --operator=$USER`, founder); Cap: trivial (`nice`); Time box: 20 min.
- [ ] **Step 2: Commands**

```bash
python3 - <<'PY' &
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        body = "\n".join(f"{k}: {v}" for k, v in self.headers.items()).encode()
        self.send_response(200); self.send_header("Content-Type", "text/plain"); self.end_headers(); self.wfile.write(body)
HTTPServer(("127.0.0.1", 8090), H).serve_forever()
PY
tailscale serve --bg --http=8081 http://127.0.0.1:8090 && tailscale serve status
ssh <optiplex alias> "curl -s http://ahnoway.<tailnet>.ts.net:8081/ | grep -i '^tailscale-'"   # expect Tailscale-User-Login / -Name / -Profile-Pic
tailscale whois <optiplex-tailnet-ip> | head -8                                                  # the whois alternative
```
- [ ] **Step 3: Undo** — `tailscale serve reset; pkill -f 'HTTPServer(("127.0.0.1", 8090)'; tailscale serve status` → empty.
- [ ] **Step 4: Result + commit** — exact header names seen, whether `--http` worked or HTTPS was required, whois output shape. File into R02 (+ R07). `docs(spike): S-05 serve identity headers — <headers seen>` (+ trailer).

### Task 22: S-06 — Linux mechanism probes (idle, battery, live caps)

**Files:**
- Create: `docs/research/spikes/S-06-linux-idle-battery-livecaps.md`, `docs/runs/S-06-<date>.md`

- [ ] **Step 1: Card** — Node: ahnoway; Executor: main-session; Dependencies: none; Cap: Appendix B; Time box: 30 min; throwaway only (nothing committed under `agent/`).
- [ ] **Step 2: Commands**

```bash
# idle (Wayland session): which of these answers?
loginctl show-session "${XDG_SESSION_ID:-$(loginctl | awk 'NR==2{print $1}')}" -p IdleHint -p IdleSinceHint
dbus-send --session --print-reply --dest=org.freedesktop.ScreenSaver /ScreenSaver org.freedesktop.ScreenSaver.GetSessionIdleTime 2>&1 | tail -1
command -v qdbus6 >/dev/null && qdbus6 org.freedesktop.ScreenSaver /ScreenSaver GetSessionIdleTime
# battery / AC
cat /sys/class/power_supply/{AC*,ADP*}/online 2>/dev/null; cat /sys/class/power_supply/BAT*/status /sys/class/power_supply/BAT*/capacity 2>/dev/null
upower -i "$(upower -e | grep -m1 BAT)" 2>/dev/null | grep -E 'state|percentage|time to'
# live-adjustable caps: transient user service, then change the quota while it runs
systemd-run --user --unit=corvid-s06 -p CPUQuota=120% -p MemoryMax=1.6G nice -n 19 python3 -c 'while True: pass'
sleep 5; systemd-cgtop --user -b -n 1 2>/dev/null | grep corvid-s06 || top -b -n 1 | grep -m1 python3     # ≈ 100% of one core (≤ 120%)
systemctl --user set-property corvid-s06.service CPUQuota=30%; sleep 5; systemd-cgtop --user -b -n 1 2>/dev/null | grep corvid-s06 || top -b -n 1 | grep -m1 python3   # ≈ 30%
systemctl --user show corvid-s06.service -p CPUQuotaPerSecUSec -p MemoryMax
# kill-switch timing: time from stop to cgroup empty
date +%s.%N; systemctl --user stop corvid-s06.service; date +%s.%N
```
- [ ] **Step 3: Undo** — `systemctl --user stop corvid-s06.service 2>/dev/null; systemctl --user reset-failed corvid-s06.service 2>/dev/null; systemctl --user list-units | grep -c corvid-s06` → `0`.
- [ ] **Step 4: Result + commit** — which idle API works on this Wayland desktop, battery sources, measured CPU% before/after the live change, stop latency. File into R05. `docs(spike): S-06 Linux idle/battery/live caps — <findings>` (+ trailer).

### Task 23: Render dossiers R01–R10

**Files:**
- Create: `docs/research/R01-fleet-and-network.md` … `docs/research/R10-hub-integration-and-phase-3-5-outlines.md`

**Interfaces:**
- Consumes: `docs/runs/research-sweep-<date>.json` (Task 16), spike cards S-01…S-06.
- Produces: fact IDs `Rnn-Fk` cited by the Phase 1/2 specs and plans.

- [ ] **Step 1: For each dossier, apply verdicts** — a fact whose verdict is `refuted=true` becomes either the `corrected_statement` (with the refuter's URL, Status verified) or Status `UNVERIFIED` (reason in the row); facts beyond the refutation cap → `UNVERIFIED`; append the completeness critic's `missing` items to Open questions (research them now if a plan needs them; else leave listed).
- [ ] **Step 2: Write each file from the template** — Depth per spec §6.1 table; Spike results rows for R01 (S-01), R02 (S-05), R03 (S-02/S-03/S-04), R04 (S-04), R05 (S-06); Recommendations; §4 credit rows from `credits`; Change log.
- [ ] **Step 3: Verify each dossier**

Run (per file): `f=docs/research/R03-*.md; grep -c '^| R03-F' "$f"; grep -cE '\| (verified|UNVERIFIED) \|' "$f"; grep -nE 'https?://' "$f" | wc -l; bash scripts/lint-placeholders.sh`
Expected: fact-row count equals status-cell count (every row has a status), URL count ≥ verified rows, lint ok. Then `.venv/bin/mkdocs build 2>&1 | tail -1` OK.

- [ ] **Step 4: Commit per dossier** — `docs(research): R0n <title>` (+ trailer).

### Task 24: M2 close

- [ ] **Step 1: `save-state`** — add the one-screen summary table to `status.md` (dossier · depth · verified/unverified counts · spikes · headline numbers), clear "Node in use by", RESUME: "M2 done; next = M3 Phase 1 spec + plan".
- [ ] **Step 2: Tag + push** — `git tag -a m2 -m "M2: research sweep + spikes" && git push --follow-tags`.

---

# M3 — Phase 1 spec + plan

### Task 25: Phase 1 spec

**Files:**
- Create: `docs/superpowers/specs/<YYYY-MM-DD>-phase-1-first-shared-model-design.md`

**Interfaces:**
- Consumes: R01 (numbers), R02 (identity), R03 (topology, flags, logging, linger), R04 (model + GB), R08 (chat UI), ADR-0003 (ports), ADR-0004 (exit split), S-03/S-04 results.
- Produces: the acceptance tests and component list the Phase 1 plan implements; the decision whether a topology ADR (0006) is needed.

- [ ] **Step 1: Write the spec (package spec §7 skeleton)** — **Goal/exit:** ADR-0004's Phase 1 definition with the §7 criterion written as numbers from R04 (model, quant, weights GB, KV GB at 4k, total vs the largest node's VRAM + free RAM). **Architecture:** which node runs `llama-server` (R03 recommendation; if not solarplexus → write ADR-0006 "hub-vs-worker topology" in Task 27 noting CLAUDE.md §5.2 battery/idle implications); `rpc-server` user units with linger on the worker nodes bound to tailnet IPs; the chat UI (R08 choice, licence) as a compose service on solarplexus behind Caddy; Caddy routes per ADR-0003; model store path (R01). **Components:** per node: unit files (exact `ExecStart` lines from R03 flags incl. the no-logging flag), caps (`CPUQuota`/`MemoryMax` in the unit = the owner's slider value; default = Appendix B; demo = the exception), model download, Caddy config snippet, chat UI compose snippet (ports bound to the tailnet IP only; `cpus`/`mem_limit` set). **Data flow:** member → Caddy → chat UI → llama-server `/v1` → rpc-servers. **Error handling:** a worker drops (llama-server behaviour per R03; restart policy); laptop on battery (§5.2: worker unit stops — how, from R05/S-06); model missing. **Acceptance:** (1) `curl …/v1/chat/completions` returns a completion from the chosen model; (2) `llama-bench --rpc` tok/s recorded ≥ the S-04 number within 20 %; (3) `nvidia-smi` on each node during the run shows usage within the slider/exception; (4) `grep -r "<a unique prompt string>" <all log locations on all nodes>` → no hits (no prompt logging); (5) a friend-usable URL: chat UI answers at `http://solarplexus.<tailnet>.ts.net/chat` with zero login and shows the member's identity (S-05 mechanism); (6) cross-house completion recorded as the follow-on per ADR-0004. **Out of scope:** agent, coordinator, status page (Phase 2). **ADRs:** 0003 → Accepted (Task 27), 0006 if needed.
- [ ] **Step 2: Verify + commit** — placeholder lint; mkdocs build; every number cites an `Rnn-Fk` or `S-nn`; `docs(spec): Phase 1 first shared model design` (+ trailer).

### Task 26: Phase 1 plan (for Opus)

**Files:**
- Create: `docs/superpowers/plans/<YYYY-MM-DD>-phase-1-first-shared-model.md`

- [ ] **Step 1: Invoke `superpowers:writing-plans` against the Phase 1 spec** — header with "Read: CLAUDE.md, docs/status.md, R01, R02, R03, R04, R08, ADR-0003, ADR-0004"; Task 0 = Appendix A preflight + `remote-step`; tasks: install/verify llama.cpp binaries per node (from S-02's branch per node; founder steps for any package install), create the rpc-server user units (full unit file text; `loginctl enable-linger` = `executor: founder` on optiplex / `Opus (splx-root)` on solarplexus), model download to the model store, llama-server unit on the host node, Caddy route (`Opus (splx-root)`; exact Caddyfile snippet; `caddy validate` then reload), chat UI compose service (exact compose file with tailnet-IP port binding and `cpus`/`mem_limit`), the exception request step for the demo (founder handoff block), the acceptance test block (commands + expected outputs), run file + status summary line, the `add-dependency` step for the chat UI and llama.cpp (+ model licence) §4 rows. Every step has `executor:`; every system change has an undo.
- [ ] **Step 2: Self-review per writing-plans checklist**; `bash scripts/lint-placeholders.sh` ok.
- [ ] **Step 3: Commit** — `docs(plan): Phase 1 first shared model (executor: Opus + founder)` (+ trailer).

### Task 27: ADR-0003 Accepted (+ CLAUDE.md §3.2 line) and ADR-0006 if needed

**Files:**
- Modify: `docs/adr/0003-endpoints.md` (Status → Accepted; final ports), `CLAUDE.md` §3.2 (the `http://solarplexus:8080` line → the Caddy URL + `:8090`), `docs/status.md`
- Create (conditional): `docs/adr/0006-inference-topology.md`

- [ ] **Step 1: Edit ADR-0003** — Status Accepted, date, ports as finally chosen in the Phase 1 spec; consequences updated.
- [ ] **Step 2: Edit CLAUDE.md §3.2** — replace the sentence "Exposes an OpenAI-compatible API on the tailnet: every friend gets private AI at `http://solarplexus:8080`." with "Exposes an OpenAI-compatible API on the tailnet behind Caddy: every friend gets private AI at `http://solarplexus.<tailnet>.ts.net/` (chat) and `/v1` (API; llama-server on `:8090`) — see ADR-0003." (spec §3.9c — the only §3.2 edit).
- [ ] **Step 3: ADR-0006 (only if the Phase 1 spec places `llama-server` off solarplexus)** — `new-adr` with Context (R03 numbers: solarplexus 4 threads/GTX 970; S-04 result), Decision (host node; what happens when the host is a laptop on battery — CLAUDE.md §5.2), Consequences (the endpoint stays on solarplexus via Caddy; failover later).
- [ ] **Step 4: Verify + commit** — `git diff HEAD -- CLAUDE.md | grep '^[-+]' | grep -vE '^(\+\+\+|---)' | wc -l` → exactly 2 lines changed (one −, one +) plus any §4 rows from Task 26's `add-dependency`; placeholder lint ok; commit `docs(adr): ADR-0003 accepted; CLAUDE.md §3.2 endpoint line; [ADR-0006 topology]` (+ trailer).

# M4 — Phase 2 spec + plan

### Task 28: Phase 2 spec

**Files:**
- Create: `docs/superpowers/specs/<YYYY-MM-DD>-phase-2-roster-design.md`

**Interfaces:**
- Consumes: R05 (idle/battery/caps/live caps/opt-in), R06 (schema, compose, queue, fair share, log policy), R07 (status page, identity), R02 (identity), ADR-0001, ADR-0005 (Task 30 — written alongside), S-06.
- Produces: agent/coordinator/status-page component boundaries and acceptance numbers for the Phase 2 plan.

- [ ] **Step 1: Write the spec** — **Goal/exit:** CLAUDE.md §6 Phase 2 ("a live map of the co-op") with numbers: all three build nodes live; node-down visible within N = 3 × heartbeat interval (R06 chooses the interval; write N); cap change effective ≤ 5 s; kill switch ≤ 2 s; fresh agent reports `offers: none`; no prompt/content text in any log. **Architecture:** agent v0 (Python 3.12+, runs as the owner's user under systemd user unit with linger; config file `~/.config/corvid/agent.toml` with `offers` (inference_host/batch/hours; default all off), `caps` (cpu_percent, ram_gb, vram_mb — the slider), `kill` flag file path; live reload via inotify or mtime poll every 2 s; enforcement via `systemctl --user set-property` on the CORVID work slice (S-06 mechanism); idle/battery detection via the S-06 APIs; heartbeat POST every 15 s with capabilities filtered by `offers`); coordinator v0 (compose project `corvid-coordinator` on solarplexus: Postgres 16 + a FastAPI service bound to the tailnet IP `:8091`, identity from `tailscale whois` or serve headers per S-05/R02, tables `node`, `heartbeat`, `capability`, `job` (queue with `SKIP LOCKED`), `run`; fair-share when contended — no quotas per ADR-0001; logs metadata only); status page v0 (R07 choice: a server-rendered page at `:8092` or Grafana; panels: node liveness map, pool capacity/utilisation, distance to next threshold, thank-you list — never counts/ranks). **Data flow:** agent → API → Postgres → status page; owner edits config → agent applies ≤ 5 s → next heartbeat reflects. **Error handling:** coordinator down (agent keeps enforcing local policy; queues heartbeats? no — drops them; owner controls never depend on the hub); Postgres down (API 503; page shows stale badge); malformed config (keep last good, log, report). **Acceptance tests:** exact commands (heartbeat age query; kill-switch timing script; `set-property` observation; `offers: none` on a fresh config; log grep). **Out of scope:** macOS/Windows agents (Phase 4), job execution (Phase 3), member guides. **ADRs:** 0005.
- [ ] **Step 2: Verify + commit** — lint; build; `docs(spec): Phase 2 roster design` (+ trailer).

### Task 29: Phase 2 plan (for Opus)

**Files:**
- Create: `docs/superpowers/plans/<YYYY-MM-DD>-phase-2-roster.md`

- [ ] **Step 1: Invoke `superpowers:writing-plans` against the Phase 2 spec** — code tasks are TDD (pytest; `.venv`): `agent/` (config loader + validation; idle/battery probes behind an interface with a fake for tests; cap enforcer calling `systemctl --user set-property` behind an interface; heartbeat client; kill-switch watcher), `coordinator/` (FastAPI app; `db/` migrations as plain SQL files `db/0001_roster.sql` …; queue functions; identity dependency), `site/status/` (page), compose file (`deploy/compose.coordinator.yml`, ports bound to the tailnet IP — the bind lint enforces), systemd user unit files + install scripts, founder runbook `docs/runbooks/coordinator.md`; `add-dependency` steps for FastAPI/psycopg/uvicorn/Postgres image (+ Grafana if chosen) with §4 rows; acceptance block; run file + status line. Every step has `executor:`; every system change an undo.
- [ ] **Step 2: Self-review**; lint ok. **Step 3: Commit** — `docs(plan): Phase 2 roster (executor: Opus + founder)` (+ trailer).

### Task 30: ADR-0005 — Contribution is a slider (Accepted)

**Files:**
- Create: `docs/adr/0005-contribution-is-a-slider.md`; Modify: `docs/status.md`

- [ ] **Step 1: `new-adr`** — Context: CLAUDE.md §5.3 (owner-set caps) and the founder's 2026-08-22 decision; S-06 proves live adjustment on Linux; ADR-0001 (consumption never limited). Decision: (1) each owner sets, per machine, how much it contributes (CPU %, RAM, VRAM, hours, roles) — **the slider**; (2) changes apply live (≤ 5 s) without restart; (3) defaults on install = nothing offered, slider at the Appendix B-equivalent 10 % once the owner opts in; (4) a future *optional* mode may link a machine's contribution to its owner's usage dynamically — always the owner's choice, never imposed, and never a limit on consumption (ADR-0001). Consequences: the agent config schema (Phase 2 spec), the tray/CLI surface (Phase 4), dashboard copy.
- [ ] **Step 2: Verify + commit** — lint; `docs(adr): ADR-0005 contribution is a slider` (+ trailer).

# M5 — Phase 3–5 outline and package close

### Task 31: Phase 3–5 outline

**Files:**
- Create: `docs/superpowers/specs/phase-3-5-outline.md`

- [ ] **Step 1: Write the outline from R10 (+ R05 packaging, R09)** — per phase: **goal** (CLAUDE.md §6 wording), **likely components** (Phase 3: job queue execution on Linux/WSL2 nodes in capped containers — Tdarr node and Immich ML as first workloads; Phase 4: idle/battery UI, tray/menu-bar, kill switch surface, member guides per OS, Folding@home team; Phase 5: SharedLLM/Nomad evaluation ADRs), **decisions required** (container runtime caps; gVisor?; Tdarr licence stance; macOS agent packaging; Headscale trigger), **research questions** (one list each, ≥ 5 items, specific), **what Phase 1–2 results will probably change** (e.g. if RPC tok/s is poor, Phase 3's "big model overnight" becomes a batch job; if identity headers fail, zero-login design shifts). No plans.
- [ ] **Step 2: Verify + commit** — lint; build; `docs(spec): Phase 3–5 outline` (+ trailer).

### Task 32: Definition-of-done checklist and close

**Files:**
- Modify: `docs/status.md`; tags

- [ ] **Step 1: Run the DoD (package spec §12) as commands and paste into `docs/runs/package-dod-<date>.md`**

```bash
ls docs/research/R0*.md docs/research/R10-*.md | wc -l                                   # 11 (R00–R10)
for f in docs/research/R*.md; do printf '%s UNVERIFIED=%s\n' "$f" "$(grep -c 'UNVERIFIED' "$f")"; done
ls docs/superpowers/specs/*phase-0* docs/superpowers/specs/*phase-1* docs/superpowers/specs/*phase-2* docs/superpowers/specs/phase-3-5-outline.md
ls docs/superpowers/plans/*phase-0* docs/superpowers/plans/*phase-1* docs/superpowers/plans/*phase-2*
grep -L 'executor:' docs/superpowers/plans/*phase-*.md                                     # expect no output (every plan tags executors)
ls docs/adr/000[2-5]-*.md
ls .claude/skills/*/SKILL.md | wc -l; ls .claude/workflows/research-sweep.js .github/workflows/ci.yml
bash scripts/lint-placeholders.sh && bash scripts/lint-bind-targets.sh && .venv/bin/mkdocs build 2>&1 | tail -1
GH_TOKEN="$(gh auth token --user thecommrade)" gh run list --repo thecommrade/corvid --limit 3   # CI green on main
```
Expected: 11 dossiers; counts listed; all spec/plan files present; no untagged plan; ADR-0002…0005 present; 5 skills; lints ok; build ok; latest CI run `completed success`.
- [ ] **Step 2: `save-state`** — RESUME: "Package complete (M0–M5). Next: dispatch the Phase 0 plan to an Opus session (`executing-plans`), founder executes founder steps; then Phase 1." Mark CLAUDE.md §6 Phase 0 status only when its run file shows the ADR-0004 criteria met (spec §3.9b).
- [ ] **Step 3: Tag + push** — `git tag -a package-v1 -m "Research & planning package complete" && git push --follow-tags`.

---

## Self-review record (writing-plans checklist, run 2026-08-22)

1. **Spec coverage:** §4 layout → T1–T6; §5 Phase 0 → T9–T14; §6.1 dossiers R00–R10 → T9, T16, T23; §6.3 spikes S-01…S-06 → T17–T22; §6.4 workflow + main-session-only spikes → T16 (+ executor lines on every spike card); §7 Phase 1/2 specs + plans and Phase 3–5 outline → T25, T26, T28, T29, T31; §8 skills/hooks/CI/processes → T3–T5, T8; §9 milestones + ordering → section headers M0–M5, T15/T24 ordering notes, S-01/S-05 dependencies; §10 risks → T18 (GTX 970 branch), T20 (exception), T9 step 2 (ACL), T17 (Wi-Fi repeat); §12 DoD → T32; Appendix A → Task 9 executor lines, `remote-step` (T3); Appendix B → Global Constraints + every spike card. ADR-0002/0003/0004/0005 → T10–T12, T27, T30; ADR-0006 conditional → T27.
2. **Placeholder scan:** the three forbidden tokens appear nowhere in this file (the lint's regex is spelled with brackets); angle-bracket `<…>` items are deliberate inputs that earlier tasks or the founder's private notes supply (node names, granted cap values, R-fact IDs, the chosen model URL), each named at its source.
3. **Consistency:** ports 8090/8091/8092/8093 (ADR-0003) used in T12, T20, T25, T28; alias names `splx-root`, `optiplex`/`oplx` match `remote-step`; spike IDs and R-numbers match spec §6.1/§6.3; executor vocabulary matches Appendix A; the AC-adapter glob `{AC*,ADP*}` is the same in the template, the `spike` skill and S-06; `docs/runs/raw/` is git-ignored in `.gitignore` (already committed) and named the same everywhere.
