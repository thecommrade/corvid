# Phase 1 — First Shared Model: Design Spec

- **Date:** 2026-08-22
- **Status:** Ready for execution (scope approved as package spec §7 on 2026-08-22; decisions below are grounded in R00–R04, R08, S-02, S-03; S-04 pending)
- **Author:** main-session (Fable) with the founder · **Executor of the plan:** Opus session + founder steps
- **Related:** `CLAUDE.md` §3.2 (backbone), §5 (politeness), §6 (Phase 1), §3.3; ADR-0001 (commons; no logging), ADR-0003 (endpoints — Accepted with this spec), ADR-0004 (exit split), ADR-0005 (slider, M4); dossiers `R01`, `R03`, `R04`, `R08` (+ `R00`, `R02`); spikes `S-02`, `S-03` (done), `S-04` (pending)
- **Notation:** `Rnn-Fk` = dossier facts; "§N" = this spec; "CLAUDE.md §N" = the charter.

## 1. Goal and exit criterion

Run one model that **no single build node can hold** across the three build nodes with llama.cpp RPC, expose it as an OpenAI-compatible endpoint plus a friend-usable chat page on the hub, and measure it honestly.

**Exit (ADR-0004 §2):** (i) **the thesis** — a completion from a model whose weights + KV cache at the chosen quantisation exceed the largest single node's VRAM + free RAM (≈ 6 GB + 19 GB ≈ 25 GB; R04 recommends a ≥ 3 GB margin), split across the build nodes, with GB-per-node and tok/s recorded; (ii) **the cross-house completion** — the named follow-on, owner founder, trigger = first member machine online. `status.md` marks both halves.

## 2. Evidence this spec stands on

| Fact | Source |
|---|---|
| Prebuilt llama.cpp **Vulkan** tarball (tag **b10581**, `0.2.0-dev`, commit `2115b73d8`) runs on all three nodes and sees each NVIDIA GPU as `Vulkan0`; binaries `ggml-rpc-server`, `llama-server`, `llama-bench`; **no `--mem` flag**; no Linux CUDA prebuilt exists | S-02 · R03-F8/F9 · R01-F17 |
| RPC mechanics work across nodes (backend `Vulkan,RPC`); **silent local fallback** when the endpoint is unreachable; **inbound RPC is blocked by firewalld (ahnoway) and ufw (optiplex)**; hub in userspace mode forwards inbound tailnet connections to localhost; tiny-model overhead ≈ 5× on tg over Wi-Fi | S-03 |
| Layers + KV split across local and remote devices in proportion to free memory; override with `--tensor-split`; `-H` must be a dotted IPv4; client and servers must share the RPC protocol version → **one pinned tag fleet-wide**; RPC is unauthenticated ("never run on an open network") | R03-F10/F11/F12/F8 |
| `llama-server` at b10581 does **not** log request/response bodies at default verbosity; `-v` logs tokens; `--log-prompts-dir` exists (never set); `--log-disable`, `--log-file` available | R03-F13/F14 |
| `-c` must be explicit: default `-c 0` loads the model's max context (262 144 for Qwen3.8-27B → 16 GiB KV) | R04 rec 6 / R04-F19 |
| Model: **Qwen/Qwen3.8-27B**, Apache-2.0, ungated; ggml-org GGUF **Q8_0 = 28,595,763,552 B (28.60 GB / 26.63 GiB)**, Q4_K_M = 18.97 GB; KV ≈ 64 KiB/token → 0.54 GB at 8k; Artificial Analysis Intelligence Index 52 (#1/137, 2026-08-22); hybrid (48 linear-attention + 16 full-attention layers) | R04-F3/F13/F14/F15/F16/F19 |
| llama-server ships a built-in web UI (MIT); Open WebUI licence = BSD-3-Clause + branding clause (≤ 50 end users exempt), supports trusted-header auth via `tailscale serve` headers; LibreChat lacks trusted-header auth; Hollama = MIT fallback | R08 rec 1–3, R08-F2/F4/F5/F6/F14/F15/F25 |
| Hub: Tailscale userspace mode today → cannot dial workers until Phase 0 step 2; linger off until Phase 0 step 2; ports 8090–8093 free; 15 TB storage pool | R00-F2/F7/F8, R03 rec 6 |
| Home WAN non-CGNAT, UPnP/NAT-PMP present, direct paths observed on the LAN; cross-house path `UNVERIFIED` until a member exists | R00, R01 notes |

## 3. Decisions

1. **Pinned tag:** llama.cpp **b10581** on every node (protocol must match; R03 rec 1). Install = the prebuilt `llama-b10581-bin-ubuntu-vulkan-x64.tar.gz` extracted to `~/corvid/llama/b10581/` under the service user on each node; sha256 of the tarball recorded in the run file. (R04 suggested "v0.2.0": that tag is a nightly pointer with no binaries — S-02.)
2. **Backend:** **Vulkan** on all three GPUs (no CUDA toolkit, no root, one artifact). CUDA per-node source builds (hub: CUDA 12.x with `-DCMAKE_CUDA_ARCHITECTURES=52-real`; RTX 3050 node: CUDA 13.1; R03 rec 2–4) are the documented **optimisation path** if S-04 throughput is unacceptable — not the default.
3. **Topology (default):** `llama-server` (host) on **solarplexus** after Phase 0 step 2 (kernel-mode Tailscale); `ggml-rpc-server` workers on **ahnoway** and **optiplex** bound to their tailnet IPv4 `:50052` with `-d Vulkan0`; the hub's GTX 970 joins the split as the host's local `Vulkan0`. **If S-04 shows the hub (4 threads) is the bottleneck, ADR-0006 moves `llama-server` to optiplex or ahnoway while the endpoint stays on the hub via Caddy** (CLAUDE.md §5.2 battery/idle caveat for a laptop host).
4. **Model:** **Qwen3.8-27B Q8_0** (ggml-org GGUF) — 26.6 GiB weights + ≈ 0.5 GiB KV at `-c 8192` ≈ 27.3 GiB > the 25 GiB ceiling, far below the pool's ≈ 81 GB. **Smoke test first:** Qwen3.8-27B **Q4_K_M** (18.97 GB) — exceeds the laptop's 8 GB VRAM, fits 8 + 6 + 4 GB of pooled VRAM (+ 0.5 GB KV) → proves the RPC split before touching CPU RAM. Backups, in order: Muse-Glimmer-30B Q8_0 (29.6 GB, Apache-2.0), Gemma 4 31B-it Q8_0 (32.6 GB, Apache-2.0); classic fallback if hybrid layers misbehave over RPC: DeepSeek-R1-Distill-Llama-70B IQ3_XXS (27.5 GB). Always pass `-c 8192` (or 4096) explicitly. Model store: the hub's storage pool, `<storage-pool>/corvid/models/<model>/` (path in the founder's notes; Phase 1 plan records it), downloaded once; workers use `-c` (cache) so weights stream only on first load.
5. **Endpoint (ADR-0003, Accepted with this spec):** `llama-server --host <hub-tailnet-ipv4> --port 8090 -c 8192 -ngl 99 --rpc <ahnoway-tailnet-ipv4>:50052,<optiplex-tailnet-ipv4>:50052 -m <model>`; Caddy on the hub's tailnet IP `:80`: `/v1*` → `:8090`, **`/chat*` → `:8090`** (built-in web UI) in Phase 1; `:8093` stays reserved for the Phase 2 member chat (Open WebUI). Member URL: `http://solarplexus.<tailnet>.ts.net/chat`.
6. **Chat UI in Phase 1 = llama-server's built-in web UI** (MIT, inside the binary; history lives in the member's browser = per-member separation without a server database; nothing logged). **Open WebUI is deferred to Phase 2** with its own ADR (licence BSD-3 + branding clause — never rebrand; trusted-header auth via `tailscale serve`, header-spoofing guard, `ENABLE_ADMIN_CHAT_ACCESS=false`, telemetry off). This deliberately narrows package spec §7's "ships the chosen UI" to the zero-dependency option — R08 rec 1 + YAGNI; recorded here, not silently.
7. **Caps / slider:** worker units carry `CPUQuota=`/`MemoryMax=` = the owner's slider (defaults = package spec Appendix B); VRAM bounded by `--tensor-split` on the host and model choice (no `--mem`); the demo runs under **per-node exceptions granted by the founder** (e.g. ahnoway ≤ 7 GB VRAM / 10 GB RAM / `CPUQuota=400%`; optiplex ≤ 5 GB VRAM / 12 GB RAM / `300%`; hub ≤ 3.5 GB VRAM / 8 GB RAM / `200%`), recorded in the run file and `status.md`; workers are **user units with linger** (`~/.config/systemd/user/corvid-rpc.service`), `-d Vulkan0`; a laptop worker stops on battery (manual in Phase 1; the agent automates it in Phase 2).
8. **Logging posture (ADR-0001):** default verbosity; **never** `-v`/`--log-verbose`, never `--log-prompts-dir`; `--log-file` metadata only; Caddy access log without bodies; acceptance greps all logs for a unique prompt string.
9. **Firewalls (`executor: founder`):** allow inbound TCP 50052 from the tailnet on `tailscale0` — optiplex `ufw allow in on tailscale0 from 100.64.0.0/10 to any port 50052 proto tcp`; ahnoway `firewall-cmd --permanent --zone=<tailscale zone> --add-port=50052/tcp` (or bind `tailscale0` to the `trusted` zone) + `--reload`; hub: no firewall units. Undo lines in the plan.
10. **Security:** RPC is unauthenticated — the tailnet is the boundary (CLAUDE.md §3.2); ACL baseline (ADR-0002) later narrows to `tag:hub ↔ tag:member`. Workers bind the tailnet IPv4 only (never `0.0.0.0`; the repo guard enforces).
11. **§4 credits (same commit as the download):** `| Qwen3.8-27B | Phase 1 model weights (GGUF) | Apache-2.0 | Alibaba Cloud / Qwen Team; GGUF conversion by ggml-org |` (+ backups when used). llama.cpp is already credited.

## 4. Components

| Node | Unit / artifact | Exact invocation (plan fills `<…>` from the founder's notes) |
|---|---|---|
| ahnoway (worker) | `~/.config/systemd/user/corvid-rpc.service` | `ExecStart=%h/corvid/llama/b10581/ggml-rpc-server -H <ahnoway-tailnet-ipv4> -p 50052 -d Vulkan0 -t 4 -c` · `Environment=GGML_VK_VISIBLE_DEVICES=0` · `CPUQuota=`/`MemoryMax=` per slider · `Restart=on-failure` · `WantedBy=default.target` |
| optiplex (worker) | same unit name | same shape with `<optiplex-tailnet-ipv4>`; `-t 4`; `MemoryMax=` per slider; never touches its production services |
| solarplexus (host) | `~/.config/systemd/user/corvid-llama-server.service` (linger on after Phase 0 step 2) | `ExecStart=%h/corvid/llama/b10581/llama-server --host <hub-tailnet-ipv4> --port 8090 -m <storage-pool>/corvid/models/Qwen3.8-27B/Qwen3.8-27B-Q8_0.gguf -c 8192 -ngl 99 --rpc <ahnoway-tailnet-ipv4>:50052,<optiplex-tailnet-ipv4>:50052 --log-file %h/corvid/logs/llama-server.log` · `Environment=GGML_VK_VISIBLE_DEVICES=0` · caps per slider/exception |
| solarplexus (front door) | Caddyfile site block (ADR-0003) | `http://<hub-tailnet-ipv4>:80 { handle_path /v1* { reverse_proxy <hub-tailnet-ipv4>:8090 } handle /chat* { reverse_proxy <hub-tailnet-ipv4>:8090 } handle { respond "CORVID — see /chat" } log { output file /var/log/caddy/corvid.log format json } }` (no request bodies are logged by Caddy by default) |
| hub storage | model store | `<storage-pool>/corvid/models/Qwen3.8-27B/` with `Qwen3.8-27B-Q8_0.gguf` (+ `Qwen3.8-27B-Q4_K_M.gguf` for the smoke test), sha256 files |

## 5. Data flow

Member browser → `http://solarplexus.<tailnet>.ts.net/chat` → Caddy (hub tailnet IP `:80`) → `llama-server :8090` (built-in UI / `/v1`) → RPC over the tailnet to `ggml-rpc-server` on ahnoway and optiplex (Vulkan0 each) + the hub's own Vulkan0 → tokens stream back. Weights are read from the hub's pool; workers cache them locally (`-c`). Identity is implicit (tailnet membership); no accounts in Phase 1.

## 6. Error handling

| Failure | Detection | Response |
|---|---|---|
| A worker is unreachable at start | `llama-server --list-devices` shows no `RPC…` device / backend column lacks `RPC`; worker journal has no "Accepted client connection" | stop: firewall (D9) or unit down; never accept a silent local fallback as a pass |
| A worker drops mid-run | requests fail / server exits (`Restart=on-failure` restarts it; RPC backend behaviour on disconnect is `UNVERIFIED` — S-04 observes and records) | plan records the behaviour; Phase 2's agent will report node state |
| Laptop on battery | founder/owner notices (Phase 1) | stop `corvid-rpc.service` on the laptop; the hub + optiplex continue only if the model still fits (it does not for Q8_0 → the service fails loudly) |
| Hub cannot dial workers | `ssh` to hub: `timeout 5 bash -c 'cat </dev/null >/dev/tcp/<worker-ip>/50052'` fails | Phase 0 step 2 not done → stop |
| Model too slow to be usable | S-04 tok/s | accept for the thesis (RPC fits, not speeds), record, and let R04's smaller candidates or CUDA builds be Phase 1.1 |
| Prompt text found in a log | acceptance grep | fix flags, rotate logs, re-run |

## 7. Acceptance tests (the plan's final block)

1. **Split proof:** on the hub, `llama-server --list-devices --rpc <w1>:50052,<w2>:50052` lists RPC devices (or `llama-bench --rpc …` backend column shows `Vulkan,RPC`), and both worker journals show `Accepted client connection` during a request.
2. **Thesis completion:** `curl -s http://<hub-tailnet-ipv4>:8090/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"qwen3.8-27b","messages":[{"role":"user","content":"In two sentences, what is a village utility?"}],"max_tokens":96}'` returns text; `usage` recorded.
3. **Numbers:** `llama-bench -m <Q8_0> --rpc <w1>:50052,<w2>:50052 -ngl 99 -p 128 -n 64 -r 2` pp/tg tok/s recorded; per-node `nvidia-smi --query-gpu=memory.used` and `free -g` during the run recorded; the GB arithmetic in the run file shows weights + KV > 25 GiB. (Once S-04 exists, tok/s must be within 20 % of its measurement.)
4. **Caps/exceptions:** measured usage per node ≤ the granted exception; exception text in the run file.
5. **No logging:** `grep -r "<unique nonce from the test prompt>" ~/corvid/logs /var/log/caddy` on the hub and the worker journals → no hits.
6. **Friend-usable URL:** `curl -s -o /dev/null -w '%{http_code}' http://solarplexus.<tailnet>.ts.net/chat/` → `200` from ahnoway and optiplex; a human loads it in a browser and gets an answer (founder confirms).
7. **Binding:** `ss -tln` on each node shows `<tailnet-ip>:50052` / `<hub-tailnet-ip>:8090` and nothing on `0.0.0.0` for CORVID processes.
8. **ADR-0004 (ii):** recorded as "pending" with trigger, or done with date.

## 8. Out of scope

Open WebUI / accounts / per-member server-side history (Phase 2), the agent and coordinator (Phase 2), member guides (Phase 4), CUDA builds (optimisation path), any model above the pool's RAM+VRAM.

## 9. ADRs

ADR-0003 → Accepted (with the Phase 1 `/chat → :8090` amendment); ADR-0006 (inference topology) only if S-04 moves the host off the hub; "chat front-end" ADR arrives with Phase 2.
