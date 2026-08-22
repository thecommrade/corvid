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
