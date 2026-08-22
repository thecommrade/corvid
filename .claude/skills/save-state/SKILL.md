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
