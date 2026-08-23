# S-04 — thesis-split

- **Goal:** the thesis number — a model that is *impossible on one machine* (spec §7: weights +
  KV at chosen quant > largest single node's VRAM + free RAM ≈ 25 GiB) produces a completion
  split across the three nodes; record tok/s (pp/tg) and per-node GB. Model: **Qwen3.8-27B
  Q8_0** (~26.6 GiB weights + ~0.5 GiB KV at 8k); fallback order per Phase 1 spec
  (Muse-Glimmer-30B Q8_0 next).
- **Node(s):** ahnoway, solarplexus, optiplex
- **Executor:** main-session (+ founder for firewall/root steps)
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

- (pending)
- Raw evidence: `docs/runs/S-04-<date>.md` · `docs/runs/raw/` (git-ignored)

## Follow-ups

- File tok/s + GB into R03 (acceptance test 3's "within 20% of S-04" reference) and R04
  (placement arithmetic); decide ADR-0006 (topology) only if the hub bottleneck shows;
  Phase 1 plan Task 8 cites these numbers.
