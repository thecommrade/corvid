# S-03 — tiny-rpc-split

- **Goal:** Prove llama.cpp RPC mechanics between two build nodes over the tailnet and measure the overhead (local vs RPC) for a tiny model, within default caps.
- **Node(s):** ahnoway (host: `llama-bench`) + optiplex (planned worker) → **actual worker: solarplexus** (see Result — both ahnoway and optiplex block inbound RPC today)
- **Executor:** main-session
- **Dependencies:** S-02 (prebuilt Vulkan b10581 on all nodes) ✔
- **Preconditions:** AC on ahnoway ✔ · optiplex load1 2.89 (< 4.0) ✔ · solarplexus GPU idle before the hub leg: `nvidia-smi` util 0 %/0 %, 18 MiB used, 0 encoder sessions, load1 0.10 (Plex/Immich idle by measurement; founder to confirm retroactively) · `docs/status.md` "Node in use by" set ✔ · Tailscale modes: ahnoway kernel, optiplex kernel, solarplexus **userspace**
- **Cap (Appendix B):** ahnoway `CPUQuota=120%` `MemoryMax=1.6G`; optiplex `CPUQuota=120%` `MemoryMax=3.2G`; solarplexus `CPUQuota=40%` `MemoryMax=1.6G`; `nice -n 19`; VRAM by model size (no `--mem` in b10581): 360 M-Q8 ≈ 367 MiB, 135 M-Q8 ≈ 136 MiB; device selection `-d Vulkan0` (iGPUs excluded); `GGML_VK_VISIBLE_DEVICES=0` on the host
- **Exception record:** none
- **Time box:** 45 min (actual ≈ 40 min incl. diagnosis)
- **Expected signal:** `llama-bench` backend shows `Vulkan,RPC`; worker log shows client connections; tok/s for local vs RPC
- **Abort criteria / watch:** node swapping, Plex stream (GPU util/encoder sessions on the hub), load > 2× cores — none triggered

## Commands (exact; every heavy command wrapped)

```bash
# worker (optiplex, planned): transient USER SERVICE (survives ssh exit; linger=yes there), tailnet IP only, Vulkan0 only
ssh optiplex 'export XDG_RUNTIME_DIR=/run/user/1000; systemd-run --user --unit=corvid-s03-rpc -p CPUQuota=120% -p MemoryMax=3.2G nice -n 19 ~/corvid-s02/vulkan/llama-b10581/ggml-rpc-server -H <optiplex-tailnet-ip> -p 50052 -d Vulkan0 -t 4'
# worker (solarplexus, actual): userspace-mode Tailscale forwards inbound tailnet connections to localhost → bind 127.0.0.1 (never 0.0.0.0); scope held by the ssh session
ssh <solarplexus alias> 'systemd-run --user --scope -p CPUQuota=40% -p MemoryMax=1.6G nice -n 19 ~/corvid-s02/vulkan/llama-b10581/ggml-rpc-server -H 127.0.0.1 -p 50052 -d Vulkan0 -t 2' &
# host (ahnoway)
GGML_VK_VISIBLE_DEVICES=0 systemd-run --user --scope -p CPUQuota=120% -p MemoryMax=1.6G nice -n 19 ./llama-bench -m model.gguf -ngl 99 -p 128 -n 64 -r 3                       # local
GGML_VK_VISIBLE_DEVICES=0 systemd-run --user --scope -p CPUQuota=120% -p MemoryMax=1.6G nice -n 19 ./llama-bench -m model.gguf --rpc <worker-tailnet-ip>:50052 -ngl 99 -p 128 -n 64 -r 3   # auto split (by free memory)
# connectivity probes: timeout 5 bash -c 'cat </dev/null >/dev/tcp/<worker-tailnet-ip>/50052'
```

## Undo (executed and confirmed at the end)

```bash
ssh optiplex 'export XDG_RUNTIME_DIR=/run/user/1000; systemctl --user stop corvid-s03-rpc; systemctl --user reset-failed corvid-s03-rpc'; ssh optiplex 'ss -tln | grep -c :50052'   # → 0 ✔
systemctl --user stop corvid-s03-rpc (ahnoway)                                                                                               # → port closed ✔
kill <ssh holding the hub scope>; ssh <solarplexus alias> 'pkill -f "[g]gml-rpc-server -H 127.0.0.1"; ss -tln | grep -c :50052'             # → 0 ✔
# models kept under ~/corvid-s03 on ahnoway (+ 360M copy on optiplex) for S-04; removed after S-04
```

## Result

- **Firewalls block inbound RPC on two of three nodes:** `ahnoway → optiplex:50052` CLOSED/FILTERED while `:22` OPEN (**ufw active** on optiplex; self-connect OK); `optiplex → ahnoway:50052` CLOSED (**firewalld active** on ahnoway). solarplexus has no firewall units and, in userspace mode, **forwards inbound tailnet connections to localhost** — `ahnoway → solarplexus:50052` OPEN with the worker bound to `127.0.0.1`. → Phase 1 plan: allow the RPC port on `tailscale0` on optiplex (ufw) and ahnoway (firewalld), `executor: founder`.
- **Silent-fallback hazard:** when the RPC endpoint is unreachable, `llama-bench --rpc …` runs locally without error (backend column shows `Vulkan` only) — the first two "RPC" runs were invalid for that reason. Always check the backend column reads `Vulkan,RPC` and the worker log shows `Accepted client connection`.
- **`llama-cli --list-devices --rpc host:port` does not list the RPC device** at b10581 even when reachable; `-dev RPC0` is rejected (the `-dev` name for RPC devices is `UNVERIFIED` → R03); the default auto-split (no `-dev`) used it.
- **Numbers (SmolLM2-135M-Instruct Q8_0, 136 MiB, pp128/tg64, r=3):** local RTX 2070 Super (Vulkan): **pp 6971 ± 502 t/s, tg 457 ± 36 t/s**; auto-split ahnoway Vulkan0 + solarplexus GTX 970 via RPC over Wi-Fi/userspace forwarding: **pp 399 ± 27 t/s, tg 94 ± 21 t/s** (backend `Vulkan,RPC`; hub log 80 client connections; hub GPU 29 → 81 MiB, util samples up to 100 %). For a latency-bound tiny model the RPC path costs ≈ 5× on tg and ≈ 17× on pp — consistent with CLAUDE.md §3.2's warning that RPC exists to *fit*, not to speed up.
- Earlier local baselines: SmolLM2-360M Q8 on the 2070S pp 1470→9820 (cold→warm) / tg 303–348 t/s; on the RTX 3050 (optiplex) pp 5700 / tg 224 t/s.
- **Pattern for Phase 1 workers:** `systemd-run --user --unit=<name>` (transient service) — a `--scope` dies with the ssh session; on the hub `linger` is off (Phase 0 step 2 enables it).
- Raw evidence: `docs/runs/S-03-2026-08-22.md` · scratch logs under the session scratchpad

## Follow-ups

- R03: `ggml-rpc-server` flags at b10581 (`-t -d -H -p -c`; no `--mem`); RPC device naming for `-dev`; silent local fallback; userspace-mode forwarding to localhost; overhead numbers. R01: firewall state per node (firewalld / ufw / none). Phase 1 plan: firewall rules (founder), transient services, check `Vulkan,RPC` in acceptance.
- S-04 needs the firewall rules first (worker on optiplex) or uses solarplexus as the only worker (4 GB VRAM) — decide with R04's model.
