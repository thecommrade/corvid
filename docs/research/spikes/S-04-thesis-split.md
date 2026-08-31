# S-04 — thesis-split

- **Goal:** the thesis number — a model that is *impossible on one machine* (spec §7: weights +
  KV at chosen quant > largest single node's VRAM + free RAM ≈ 25 GiB) produces a completion
  split across the three nodes; record tok/s (pp/tg) and per-node GB. Model: **Qwen3.8-27B
  Q8_0** (~26.6 GiB weights + ~0.5 GiB KV at 8k); fallback order per Phase 1 spec
  (Muse-Glimmer-30B Q8_0 next).
- **Node(s):** ahnoway, solarplexus, optiplex
- **Executor:** main-session (+ founder for firewall/root steps). *Completion attempt
  2026-08-31: Opus with the founder present throughout — a founder-granted exception to the
  main-session/founder-only rule, valid for that run only.*
- **Dependencies:** S-02/S-03 done (binaries at b10581 in `~/corvid-s02/` per node) · firewall:
  TCP 50052 in on `tailscale0` on ahnoway + optiplex (founder) · demo cap exception (below) ·
  hub able to dial 100.x (Phase 0 step 2 kernel-mode switch) — **if the hub is still userspace
  when this runs, record the blocker and stop; do not invert the topology without an ADR**
  (spec §7: llama-server anywhere but solarplexus = ADR).
- **Preconditions:** AC power on ahnoway · Plex/Immich idle (founder confirms) · optiplex 1-min
  load < 4 · disk free ≥ 35 GB on the hub pool (`/mnt/storage`) · `docs/status.md` "Node in
  use by" set to S-04 · model downloaded to `<pool>/corvid/models/Qwen3.8-27B/` with checksum.
- **Cap (Appendix B):** **demo exception** (not defaults): ahnoway `CPUQuota=400%
  MemoryMax=10G` VRAM ≤ 7 GB · optiplex `CPUQuota=300% MemoryMax=12G` VRAM ≤ 5 GB · solarplexus
  `CPUQuota=200% MemoryMax=8G` VRAM ≤ 3.5 GB · `nice -n 19` · network: model load streams the
  remote shards once (`-c` cache warms workers; subsequent runs local).
- **Exception record:** granted by founder 2026-08-23 (session prompt, "S-04 / Phase 1 demo"
  approved): the three per-node values above, window = the S-04 run (≤ 3 h).
  **Renewed 2026-08-31** for the completion attempt (same values, ≤ 3 h), with two amendments
  granted that day: optiplex `MemoryMax` 12G → **16G**, and **solarplexus withdrawn from the
  split entirely** (no VRAM, no RAM share) because it hosts Plex/Immich. Session ended early
  by founder call; the caps were never approached.
- **Time box:** 3 h (incl. ~30 GB model download)
- **Expected signal:** `llama-bench --rpc` (or `llama-cli` one completion) shows backend
  `Vulkan,RPC`; workers' journals count `Accepted client` > 0; per-node `nvidia-smi`
  memory.used within the granted VRAM; sensible completion text; pp/tg tok/s recorded at 8k
  context; GB arithmetic written out (>25 GiB proves §7).
- **Abort criteria / watch:** GPU temp > 85 °C any node (`nvidia-smi
  --query-gpu=temperature.gpu --format=csv,noheader`) · swap in use on solarplexus · load > 6
  on optiplex · Plex/Immich unhealthy → stop units, run undo.

## Commands (exact; every heavy command wrapped)

```bash
# workers (ahnoway local; optiplex via ssh with XDG_RUNTIME_DIR): transient unit, tailnet bind
systemd-run --user --unit=corvid-s04-rpc -p CPUQuota=<granted> -p MemoryMax=<granted> \
  nice -n 19 ~/corvid-s02/b10581/ggml-rpc-server -H <node-tailnet-ipv4> -p 50052 -d Vulkan0 -t 4 -c
# hub (after kernel-mode switch): bench, then one real completion
systemd-run --user --unit=corvid-s04-llama -p CPUQuota=200% -p MemoryMax=8G nice -n 19 \
  ~/corvid-s02/b10581/llama-bench -m <pool>/corvid/models/Qwen3.8-27B/Qwen3.8-27B-Q8_0.gguf \
  --rpc <ahnoway-100.x>:50052,<optiplex-100.x>:50052 -ngl 99 -p 128 -n 64 -r 2
# log hygiene check afterwards (spec: no prompt/completion text in any log)
journalctl --user -u corvid-s04-rpc --since -3h | grep -ci 'Accepted client'
```

## Undo (executed and confirmed at the end)

```bash
systemctl --user stop corvid-s04-rpc corvid-s04-llama 2>/dev/null
ss -tln | grep ':50052' || echo no-listener   # on each worker
# firewall rules STAY (Phase 1 reuses them; founder may delete: see run file for exact undo)
# then remove spike scratch fleet-wide: rm -rf ~/corvid-s02 ~/corvid-s03  (after results filed)
```

## Result

- **PARTIAL 2026-08-23** (`docs/runs/S-04-2026-08-23.md`): all prerequisites landed; 3-node
  mesh PROVEN with the tiny model (backend `Vulkan,RPC`, tg 31.75 t/s ≈ +4 RTT/token);
  Q4_K_M smoke failed at load — worker buffer alloc refused (suspected leaked buffers from
  two killed client runs; restart workers first on resume); Q8_0 not yet run. Binaries live
  at `~/corvid-s02/vulkan/llama-b10581/` (not the path above). Resume protocol in run file.
- **PARKED 2026-08-31** (`docs/runs/S-04-2026-08-31.md`): the failure is explained and the
  placement is specified, but **the thesis number is deliberately not taken.** Findings:
  (a) Aug-23's "leaked buffers" hypothesis is **refuted** — both worker caches were empty, so
  that run died at buffer allocation before any tensor moved; the real cause is
  **over-subscription**, because CPU devices exported via `-d Vulkan0,CPU` advertise
  *installed* RAM as free (15802 / 31890 MiB) and the default proportional split believes them.
  (b) F2 had been wiped by a reboot and was re-applied and verified with plain `ping`
  (100% loss → 0%, 1.9/5.1/9.5 ms) — ssh and `tailscale ping` had masked the outage entirely.
  (c) The hub's send ceiling is **5.0 MB/s**, so streaming Q8_0's 26.63 GiB is ≈ 91 min of
  saturated uplink on the node that serves Plex and Immich; the founder ruled that out.
  (d) The client role — not the split — is the load-bearing topology question (feeds ADR-0006):
  it memory-maps the whole model and needs `-lm dio` on any co-tenanted host.
  **Resume condition: the hub on Ethernet** (status.md finding 7), then run the specified
  `-ts 6.5/4/4.5/14` with `-dev RPC0/RPC1/RPC2/RPC3` per the run file.
- Raw evidence: `docs/runs/S-04-2026-08-23.md` · `docs/runs/S-04-2026-08-31.md` ·
  `docs/runs/raw/` (git-ignored)

## Follow-ups

- File tok/s + GB into R03 (acceptance test 3's "within 20% of S-04" reference) and R04
  (placement arithmetic); decide ADR-0006 (topology) only if the hub bottleneck shows;
  Phase 1 plan Task 8 cites these numbers.
