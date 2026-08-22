# S-06 — linux-idle-battery-livecaps

- **Goal:** Which idle / battery APIs work on the founder's Linux desktop (KDE Plasma on Wayland), and whether a cgroup cap on a running CORVID work unit can be changed live (no restart) — the CLAUDE.md §5.3 / ADR-0005 mechanism — plus kill-switch latency.
- **Node(s):** ahnoway
- **Executor:** main-session
- **Dependencies:** none
- **Preconditions:** AC power on ahnoway (`cat /sys/class/power_supply/{AC*,ADP*}/online 2>/dev/null` → 1) ✔ (ADP1 online=1) · no other spike ✔ · Tailscale mode: kernel
- **Cap (Appendix B):** `CPUQuota=120%` `MemoryMax=1.6G` on the transient unit · `nice -n 19` · no GPU · network: none
- **Exception record:** none
- **Time box:** 30 min (actual ≈ 1 min)
- **Expected signal:** one API returns session idle time / hint; AC/battery readable; CPU% tracks a `set-property` change within seconds; `systemctl --user stop` returns in < 2 s
- **Abort criteria / watch:** none needed (single busy loop, capped)

## Commands (exact; every heavy command wrapped)

```bash
# idle
loginctl show-session "$XDG_SESSION_ID" -p IdleHint -p IdleSinceHint
dbus-send --session --print-reply --dest=org.freedesktop.ScreenSaver /ScreenSaver org.freedesktop.ScreenSaver.GetSessionIdleTime
gdbus call --session --dest org.gnome.Mutter.IdleMonitor --object-path /org/gnome/Mutter/IdleMonitor/Core --method org.gnome.Mutter.IdleMonitor.GetIdletime
busctl --user list | grep -iE 'ScreenSaver|PowerDevil|Idle'
# battery / AC
for f in /sys/class/power_supply/*; do …online/status/capacity…; done; upower -i "$(upower -e | grep -m1 BAT)"
# live caps: transient user service, then change the quota while it runs; CPU% from CPUUsageNSec deltas over 5 s
systemd-run --user --unit=corvid-s06 -p CPUQuota=120% -p MemoryMax=1.6G nice -n 19 python3 -c 'while True: pass'
systemctl --user set-property corvid-s06.service CPUQuota=30%
systemctl --user stop corvid-s06.service   # timed
```

## Undo (executed and confirmed at the end)

```bash
systemctl --user stop corvid-s06.service; systemctl --user reset-failed corvid-s06.service; systemctl --user list-units --all | grep -c corvid-s06   # → 0 ✔
```

## Result

- **Idle:** `loginctl show-session … IdleHint` answers (`IdleHint=no`, `IdleSinceHint=0` while active) → candidate; `org.freedesktop.ScreenSaver.GetSessionIdleTime` → **NotSupported on this platform (KDE Wayland)**; GNOME Mutter IdleMonitor → service not present; `org.freedesktop.PowerManagement` is on the session bus (KDE). Follow-up for R05: confirm logind `IdleHint` flips after the KDE idle timeout, or use the Wayland `ext-idle-notify-v1` protocol / KDE's KIdleTime.
- **Battery/AC:** `/sys/class/power_supply/ADP1/online=1`, `BAT1 status=Not charging capacity=94`; `upower` reports `fully-charged 94%` → both sources work (adapter name is `ADP1` here, not `AC*`).
- **Live caps:** CPU **99%** under `CPUQuota=120%` (one busy loop) → `set-property CPUQuota=30%` returned in **3 ms** → CPU **29%** measured over the next 5 s; `CPUQuotaPerSecUSec=300ms`, `MemoryMax=1717986918` (1.6 GiB) confirmed. **Kill switch:** `systemctl --user stop` latency **49 ms**; unit gone afterwards.
- Versions: systemd 261 (ahnoway), Python 3.14.7.
- Raw evidence: `docs/runs/S-06-2026-08-22.md` (sanitised) · `docs/runs/raw/S-06-2026-08-22.log` (git-ignored)

## Follow-ups

- R05: Linux rows — idle via logind `IdleHint` (verify flip) or `ext-idle-notify-v1`; battery via sysfs (`ADP*`/`AC*`, `BAT*`) + upower; caps via `systemd-run --user` + `systemctl --user set-property` (live, ms); kill switch = `systemctl --user stop` (≈50 ms). Numbers feed the Phase 2 acceptance thresholds (≤ 5 s cap change, ≤ 2 s kill).
