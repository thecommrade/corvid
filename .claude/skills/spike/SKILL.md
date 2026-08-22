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
