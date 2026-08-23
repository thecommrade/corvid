# S-01 — fleet-throughput-latency

- **Goal:** measured throughput + RTT for all three node pairs on the LAN path and the tailnet
  path (Wi-Fi today; repeat when wired), per-node `tailscale netcheck` facts, and — piggybacked
  on a small RPC run — `GGML_RPC_DEBUG=1` blocking-calls-per-token with simultaneous RTT to
  calibrate R01-F24 (R01 rec 3; completeness-critic HIGH item).
- **Node(s):** ahnoway, solarplexus, optiplex (all pairs)
- **Executor:** main-session
- **Dependencies:** LAN leg: none. Tailnet leg: Phase 0 steps 0–2 (hub in kernel mode) — until
  then only pairs that can dial 100.x run (ahnoway↔optiplex; inbound-to-hub via userspace
  forwarding).
- **Preconditions:** AC power on ahnoway · Plex/Immich idle (founder confirms) · optiplex 1-min
  load < 4 (`cut -d' ' -f1 /proc/loadavg`) · `docs/status.md` "Node in use by" empty ·
  Tailscale modes recorded: ahnoway kernel 1.102.3, solarplexus **userspace** 1.98.4,
  optiplex kernel 1.102.3 · iperf3 present on all three (else founder installs — prompts on).
- **Cap (Appendix B):** CPU negligible; **network exception: ≤ 60 s of saturating traffic per
  node pair** (spec §6.3). iperf3 server binds the specific LAN or tailnet IP of the node under
  test — never `0.0.0.0`. Firewalls: 5201/tcp opened runtime-only on ahnoway for its server
  legs (reverts on reload/reboot); solarplexus has no UFW.
- **Exception record:** network exception granted by founder 2026-08-23 (session prompt,
  "S-01 bandwidth spike" approved); ≤ 60 s per pair, Plex/Immich idle confirmed at run time.
- **Time box:** 30 min (LAN leg) + 30 min (tailnet leg, later)
- **Expected signal:** per pair/direction: iperf3 Mbit/s (10 s TCP, both directions via `-R`);
  `ping -c 20` min/avg/max/mdev; tailnet: `tailscale ping --until-direct` outcome + steady RTT,
  `tailscale status --json` `.Peer[].Relay`/`CurAddr`, `tailscale netcheck` (UDP,
  MappingVariesByDestIP, PortMapping, nearest DERP + latency). RPC calibration: count of
  blocking GET_TENSOR/SET_TENSOR_HASH per generated token (SmolLM2-135M, S-03 binaries) with
  ICMP RTT sampled on the same path during the run.
- **Abort criteria / watch:** Plex/Immich stream starts or containers unhealthy → stop, run
  undo · any iperf3 run past 60 s · load > 6 on either hub.

## Commands (exact; every heavy command wrapped)

```bash
# server (on the node under test; bind ONE specific IP, LAN shown; tailnet leg uses the 100.x IP)
systemd-run --user --unit=corvid-s01-iperf -p CPUQuota=100% iperf3 -s -B <that-node-lan-ip> -1
# client (from the peer; 10 s each direction, well under the 60 s cap)
iperf3 -c <that-node-lan-ip> -t 10 && iperf3 -c <that-node-lan-ip> -t 10 -R
ping -c 20 <that-node-lan-ip> | tail -2
# tailnet facts per node
tailscale netcheck; tailscale ping --until-direct <peer>; tailscale status --json | jq '.Peer[].Relay'
# RPC calibration leg (reuses ~/corvid-s02 binaries + S-03 tiny model; worker at default caps)
GGML_RPC_DEBUG=1 <s03 llama-cli one-prompt run> 2> rpc-debug.log &  (ping -i 0.2 -c 100 <worker> > rtt.log)
```

## Undo (executed and confirmed at the end)

```bash
systemctl --user stop corvid-s01-iperf 2>/dev/null; pgrep -af '[i]perf3' || echo no-iperf3
# ahnoway runtime firewall opening reverts on reload: sudo firewall-cmd --reload  (founder)
```

## Result

- (pending)
- Raw evidence: `docs/runs/S-01-<date>.md` · `docs/runs/raw/` (git-ignored)

## Follow-ups

- File numbers into R01 (facts table + spike row); recalibrate R01-F24; re-run when the hubs
  are re-wired to Ethernet (post-move) and at first member onboarding (cross-house,
  ADR-0004 follow-on).
