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
