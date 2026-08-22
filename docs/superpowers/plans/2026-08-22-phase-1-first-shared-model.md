# Phase 1 — First Shared Model: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in your own session (an **Opus** session on ahnoway). Steps use checkbox (`- [ ]`) syntax. Executor tags (package spec Appendix A): **`Opus`** = you, unattended; **`Opus (splx-root)`** = you through the solarplexus root path (preflight proves it); **`founder`** = stop, print the handoff block, wait for "done" + output, verify, continue. You never edit `docs/status.md`; evidence goes to `docs/runs/phase-1-<YYYY-MM-DD>.md`. **Prerequisite: the Phase 0 plan has been executed** — in particular step 0 (unattended access), step 2 (hub kernel-mode Tailscale + linger) and step 6 (ports free).

**Goal:** Serve Qwen3.8-27B Q8_0 — a model no single build node can hold — split across ahnoway, optiplex and solarplexus with llama.cpp RPC (Vulkan, tag b10581), behind an OpenAI-compatible endpoint and a friend-usable chat page on the hub, with tok/s and GB-per-node recorded and no prompt logging (ADR-0004 §2(i)).

**Architecture:** One pinned prebuilt llama.cpp tarball on every node; `ggml-rpc-server` user units on the two workers bound to their tailnet IPv4; `llama-server` user unit on the hub with `--rpc` to both workers; Caddy routes `/chat` and `/v1` to `:8090`; model weights on the hub's storage pool. Firewall rules on the workers are founder steps; demo-size caps are founder-granted exceptions.

**Tech Stack:** llama.cpp b10581 (Vulkan build; `ggml-rpc-server`, `llama-server`, `llama-bench`), systemd user units + linger, Tailscale, Caddy, bash/curl/jq, `nvidia-smi`, ufw (optiplex) / firewalld (ahnoway).

**Spec:** `docs/superpowers/specs/2026-08-22-phase-1-first-shared-model-design.md` — read first. **Also read:** `CLAUDE.md`, `docs/status.md`, `docs/research/R03-llamacpp-rpc-on-this-fleet.md`, `R04-model-selection-phase1.md`, `R08-chat-frontend-phase1.md`, ADR-0003, ADR-0004, spikes S-02/S-03 (cards + run files), the `remote-step` skill.

## Global Constraints

- Executor tags on every step; founder handoff protocol; preflight (Task 0) before anything unattended.
- **Tag b10581 everywhere** (RPC protocol must match). Tarball: `llama-b10581-bin-ubuntu-vulkan-x64.tar.gz` from `https://github.com/ggml-org/llama.cpp/releases/download/b10581/`; install dir `~/corvid/llama/b10581/` under the service user on each node; record sha256.
- Workers bind **tailnet IPv4 only** (`-H <dotted-ipv4>`; never `0.0.0.0`); the repo guard enforces. Port 50052.
- Caps: unit `CPUQuota=`/`MemoryMax=` = Appendix B defaults until the founder grants the **demo exception** (Task 5); VRAM bounded by `--tensor-split`/model; `GGML_VK_VISIBLE_DEVICES=0` everywhere (iGPUs out).
- Logging: never `-v`/`--log-verbose`/`--log-prompts-dir`; `--log-file` only; Caddy JSON access log without bodies.
- optiplex: user-level only, never its production services/Postgres/data disk; root there = founder.
- `-c 8192` always; models from `ggml-org/Qwen3.8-27B-GGUF` (Apache-2.0) — §4 rows added in the same commit as the download record (Task 3).
- Placeholders: `<ahnoway-ip>`, `<optiplex-ip>`, `<hub-ip>` = tailnet IPv4s from `tailscale ip -4` on each node; `<tailnet>` = MagicDNS suffix; `<pool>` = the hub storage pool path (founder's notes); `<svc-user>` = the unattended alias user. Resolve at runtime; never write IPs/usernames into the run file.
- Branch `phase-1-first-shared-model`; conventional commits + `Co-Authored-By` trailer; push at the end.

## File Structure

| Path | Responsibility | Task |
|---|---|---|
| `docs/runs/phase-1-<date>.md` | evidence | 0–8 |
| `deploy/phase-1/corvid-rpc.service` (template), `deploy/phase-1/corvid-llama-server.service` (template), `deploy/phase-1/Caddyfile.corvid` (snippet) | the unit/config texts committed to the repo (IP placeholders; real values only on the nodes) | 2, 4, 6 |
| `CLAUDE.md` §4 | model credit rows (same commit as Task 3) | 3 |
| `docs/research/spikes/S-04-thesis-split.md` (+ run file) | if S-04 was not run before, Task 7's numbers are filed as S-04 by the main session afterwards | 7 |

---

### Task 0: Preflight and run file

- [ ] **Step 1 (`executor: Opus`):** `cd ~/projects/corvid && git checkout -b phase-1-first-shared-model && D=$(date +%F) && printf '# Phase 1 — run %s\n\nExecutor: Opus on ahnoway + founder. Sanitised.\n\n' "$D" > docs/runs/phase-1-$D.md`
- [ ] **Step 2 (`executor: Opus`): Preflight**

```bash
ssh -o BatchMode=yes optiplex true; echo "optiplex rc=$?"
ssh -o BatchMode=yes <solarplexus alias> true; echo "hub rc=$?"
ssh -o BatchMode=yes splx-root true; echo "splx-root rc=$?"          # or the Tailscale-SSH root alias from Phase 0 step 0
ssh <solarplexus alias> 'ip -br link show tailscale0 >/dev/null && echo hub-kernel-mode && loginctl show-user $USER -p Linger && timeout 5 bash -c "cat </dev/null >/dev/tcp/<optiplex-ip>/22" && echo hub-can-dial'
ssh <solarplexus alias> "ss -tlnH | awk '{print \$4}' | grep -E ':(8090|8093)$' || echo ports-free"
grep -n 'Node in use by' docs/status.md
```
Expected: all `rc=0`; `hub-kernel-mode`, `Linger=yes`, `hub-can-dial`, `ports-free`; nobody else on the nodes. Any failure → stop (Phase 0 incomplete).

- [ ] **Step 3 (`executor: Opus`):** commit the run file skeleton.

### Task 1: Firewall rules on the workers (`executor: founder`)

- [ ] **Step 1:** handoff block:

> **Founder — optiplex (as root):** `ufw allow in on tailscale0 from 100.64.0.0/10 to any port 50052 proto tcp && ufw status | grep 50052` — paste the line.
> **Founder — ahnoway (as root):** `firewall-cmd --get-zone-of-interface=tailscale0` (if none: `firewall-cmd --permanent --zone=trusted --add-interface=tailscale0`), then `firewall-cmd --permanent --zone=<that zone> --add-port=50052/tcp && firewall-cmd --reload && firewall-cmd --zone=<that zone> --list-ports` — paste.
> Undo: `ufw delete allow in on tailscale0 from 100.64.0.0/10 to any port 50052 proto tcp`; `firewall-cmd --permanent --zone=<zone> --remove-port=50052/tcp && firewall-cmd --reload`.

- [ ] **Step 2 (`executor: Opus`): Verify from the other side** — run a 10 s throwaway listener on each worker and probe it:

```bash
ssh optiplex "timeout 12 python3 -c 'import socket,time; s=socket.socket(); s.bind((\"<optiplex-ip>\",50052)); s.listen(1); time.sleep(10)'" & sleep 2; timeout 4 bash -c 'cat </dev/null >/dev/tcp/<optiplex-ip>/50052' && echo "ahnoway→optiplex:50052 OPEN"; wait
( timeout 12 python3 -c 'import socket,time; s=socket.socket(); s.bind(("<ahnoway-ip>",50052)); s.listen(1); time.sleep(10)' & ) ; sleep 2; ssh optiplex "timeout 4 bash -c 'cat </dev/null >/dev/tcp/<ahnoway-ip>/50052' && echo 'optiplex→ahnoway:50052 OPEN'"
ssh <solarplexus alias> "timeout 4 bash -c 'cat </dev/null >/dev/tcp/<ahnoway-ip>/50052' && echo 'hub→ahnoway OPEN'; timeout 4 bash -c 'cat </dev/null >/dev/tcp/<optiplex-ip>/50052' && echo 'hub→optiplex OPEN'"
```
Expected: all OPEN (restart the throwaway listeners for the hub probes if they timed out). Record; commit.

### Task 2: Install llama.cpp b10581 on all three nodes

**Files:** none in repo (binaries live on nodes); run-file rows

- [ ] **Step 1 (`executor: Opus`): Download once on ahnoway, verify, install**

```bash
mkdir -p ~/corvid/llama && cd ~/corvid/llama && curl -sL -o llama-b10581-vulkan.tar.gz https://github.com/ggml-org/llama.cpp/releases/download/b10581/llama-b10581-bin-ubuntu-vulkan-x64.tar.gz && sha256sum llama-b10581-vulkan.tar.gz | tee sha256.txt && mkdir -p b10581 && tar -xzf llama-b10581-vulkan.tar.gz -C b10581 --strip-components=1 && ~/corvid/llama/b10581/llama-server --version
```
Expected: `version: 0.2.0-dev (build 10581, commit 2115b73d8)`.

- [ ] **Step 2 (`executor: Opus`): Copy + install on optiplex and the hub**

```bash
for h in optiplex "<solarplexus alias>"; do scp -q ~/corvid/llama/llama-b10581-vulkan.tar.gz "$h":/tmp/ && ssh "$h" 'mkdir -p ~/corvid/llama/b10581 ~/corvid/logs && tar -xzf /tmp/llama-b10581-vulkan.tar.gz -C ~/corvid/llama/b10581 --strip-components=1 && rm /tmp/llama-b10581-vulkan.tar.gz && ~/corvid/llama/b10581/llama-server --version && GGML_VK_VISIBLE_DEVICES=0 ~/corvid/llama/b10581/llama-server --list-devices 2>&1 | grep Vulkan0'; done
```
Expected: same version line on both; `Vulkan0: NVIDIA …` on both. Record; commit run file.

### Task 3: Model store on the hub + §4 credits

**Files:** Modify `CLAUDE.md` (§4 rows, same commit as the download record)

- [ ] **Step 1 (`executor: Opus`): Download both GGUFs to the pool (long-running; hub egress is VPN-limited — expect tens of minutes; use `nohup`)**

```bash
ssh <solarplexus alias> 'mkdir -p <pool>/corvid/models/Qwen3.8-27B && cd <pool>/corvid/models/Qwen3.8-27B && nohup bash -c "curl -sL -o Qwen3.8-27B-Q4_K_M.gguf https://huggingface.co/ggml-org/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-Q4_K_M.gguf && curl -sL -o Qwen3.8-27B-Q8_0.gguf https://huggingface.co/ggml-org/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-Q8_0.gguf && sha256sum *.gguf > sha256.txt" > dl.log 2>&1 &'
# later:
ssh <solarplexus alias> 'ls -l <pool>/corvid/models/Qwen3.8-27B/; cat <pool>/corvid/models/Qwen3.8-27B/sha256.txt 2>/dev/null'
```
Expected sizes: Q4_K_M 18,973,870,432 B; Q8_0 28,595,763,552 B (R04-F16). If HF paths changed, open `https://huggingface.co/ggml-org/Qwen3.8-27B-GGUF/tree/main` and use the current filenames; record.

- [ ] **Step 2 (`executor: Opus`): §4 rows via `add-dependency`** — append to CLAUDE.md §4: `| Qwen3.8-27B | Phase 1 model weights (GGUF Q8_0 / Q4_K_M) | Apache-2.0 | Alibaba Cloud / Qwen Team; GGUF conversion by ggml-org (ADR-0003, Phase 1) |`. Commit **with** the run-file download record: `deps: add Qwen3.8-27B (Apache-2.0) + §4 credit; model store on the hub`.

### Task 4: Worker units on ahnoway and optiplex

**Files:** Create `deploy/phase-1/corvid-rpc.service` (template with `<node-ip>`); install real copies on nodes

- [ ] **Step 1 (`executor: Opus`): Write the template to the repo**

```bash
mkdir -p deploy/phase-1 && cat > deploy/phase-1/corvid-rpc.service <<'UNIT'
[Unit]
Description=CORVID llama.cpp RPC worker (tailnet-bound)
After=network-online.target tailscaled.service

[Service]
Environment=GGML_VK_VISIBLE_DEVICES=0
ExecStart=%h/corvid/llama/b10581/ggml-rpc-server -H <node-tailnet-ipv4> -p 50052 -d Vulkan0 -t 4 -c
Restart=on-failure
RestartSec=5
# owner's slider (defaults = package spec Appendix B; raise only with a recorded exception)
CPUQuota=120%
MemoryMax=1.6G
Nice=19

[Install]
WantedBy=default.target
UNIT
bash scripts/lint-bind-targets.sh
```
Expected: `bind-target lint: ok` (the template binds a placeholder, not 0.0.0.0).

- [ ] **Step 2 (`executor: Opus`): Install on each worker with its tailnet IPv4 and its cap**

```bash
for h in ahnoway optiplex; do IP=$([ $h = ahnoway ] && tailscale ip -4 || ssh optiplex tailscale ip -4); MEM=$([ $h = ahnoway ] && echo 1.6G || echo 3.2G)
  sed "s/<node-tailnet-ipv4>/$IP/; s/MemoryMax=1.6G/MemoryMax=$MEM/" deploy/phase-1/corvid-rpc.service > /tmp/corvid-rpc.service
  if [ $h = ahnoway ]; then mkdir -p ~/.config/systemd/user && cp /tmp/corvid-rpc.service ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now corvid-rpc && sleep 2 && systemctl --user is-active corvid-rpc && ss -tln | grep ":50052"
  else scp -q /tmp/corvid-rpc.service optiplex:/tmp/ && ssh optiplex 'export XDG_RUNTIME_DIR=/run/user/1000; mkdir -p ~/.config/systemd/user && mv /tmp/corvid-rpc.service ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now corvid-rpc && sleep 2 && systemctl --user is-active corvid-rpc && ss -tln | grep ":50052"'; fi; done
```
Expected: `active` and a `<ip>:50052` listener on each worker (never `0.0.0.0`). Undo: `systemctl --user disable --now corvid-rpc; rm ~/.config/systemd/user/corvid-rpc.service`.

- [ ] **Step 3 (`executor: Opus`):** commit the template + run-file rows: `feat(phase-1): RPC worker unit template`.

### Task 5: Demo exception (`executor: founder`) and caps on the nodes

- [ ] **Step 1:** handoff block:

> **Founder:** Phase 1 needs more than the 10 % defaults to hold a 27 GB model. Please grant, for the demo window (≤ 3 h, today): ahnoway `CPUQuota=400% MemoryMax=10G` VRAM ≤ 7 GB; optiplex `CPUQuota=300% MemoryMax=12G` VRAM ≤ 5 GB; solarplexus `CPUQuota=200% MemoryMax=8G` VRAM ≤ 3.5 GB. Reply "granted <values> until <time>" (or your own numbers).

- [ ] **Step 2 (`executor: Opus`): Apply live (no restart) and record**

```bash
systemctl --user set-property corvid-rpc.service CPUQuota=<granted> MemoryMax=<granted>
ssh optiplex 'export XDG_RUNTIME_DIR=/run/user/1000; systemctl --user set-property corvid-rpc.service CPUQuota=<granted> MemoryMax=<granted>'
```
Append the exception text to the run file; the main session mirrors it to `status.md`.

### Task 6: Host unit and Caddy route on the hub

**Files:** Create `deploy/phase-1/corvid-llama-server.service`, `deploy/phase-1/Caddyfile.corvid`

- [ ] **Step 1 (`executor: Opus`): Write the host unit template and the Caddy snippet to the repo**

```bash
cat > deploy/phase-1/corvid-llama-server.service <<'UNIT'
[Unit]
Description=CORVID llama-server (host; OpenAI-compatible API + built-in web UI)
After=network-online.target tailscaled.service

[Service]
Environment=GGML_VK_VISIBLE_DEVICES=0
ExecStart=%h/corvid/llama/b10581/llama-server --host <hub-tailnet-ipv4> --port 8090 -m <pool>/corvid/models/Qwen3.8-27B/<gguf> -c 8192 -ngl 99 --rpc <ahnoway-tailnet-ipv4>:50052,<optiplex-tailnet-ipv4>:50052 --log-file %h/corvid/logs/llama-server.log
Restart=on-failure
RestartSec=10
CPUQuota=40%
MemoryMax=1.6G
Nice=19

[Install]
WantedBy=default.target
UNIT
cat > deploy/phase-1/Caddyfile.corvid <<'CADDY'
# CORVID front door (ADR-0003) — import this file from the hub's main Caddyfile
http://<hub-tailnet-ipv4>:80 {
    handle /v1* {
        reverse_proxy <hub-tailnet-ipv4>:8090
    }
    handle /chat* {
        reverse_proxy <hub-tailnet-ipv4>:8090
    }
    handle {
        respond "CORVID — private AI at /chat · API at /v1" 200
    }
    log {
        output file /var/log/caddy/corvid.log
        format json
    }
}
CADDY
bash scripts/lint-bind-targets.sh
```
(llama-server serves `/v1/...` itself, so `/v1` is proxied without path stripping; if the built-in UI expects to live at `/`, add `handle_path /chat* { reverse_proxy … }` instead and record which variant worked.)

- [ ] **Step 2 (`executor: Opus`): Install the host unit (smoke model first)** — substitute `<hub-tailnet-ipv4>`, worker IPs, `<pool>`, `<gguf>=Qwen3.8-27B-Q4_K_M.gguf`, and the granted caps; copy to the hub's `~/.config/systemd/user/corvid-llama-server.service`; `systemctl --user daemon-reload && systemctl --user enable --now corvid-llama-server`; wait for load: `until curl -s http://<hub-ip>:8090/health | grep -q ok; do sleep 10; done` (time-box 20 min); `journalctl --user -u corvid-llama-server -n 30 --no-pager` shows the RPC devices and layer split.

- [ ] **Step 3 (`executor: Opus (splx-root)`): Caddy route** — `cp deploy/phase-1/Caddyfile.corvid /etc/caddy/Caddyfile.corvid` (with IPs substituted), add `import /etc/caddy/Caddyfile.corvid` to `/etc/caddy/Caddyfile` (backup first: `cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak-<date>`), `caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy`. Undo: restore the backup + reload. Verify: `curl -s -o /dev/null -w '%{http_code}\n' http://solarplexus.<tailnet>.ts.net/chat/` → `200`; `curl -s http://solarplexus.<tailnet>.ts.net/v1/models | head -c 200`.

- [ ] **Step 4 (`executor: Opus`):** commit templates + run file: `feat(phase-1): host unit and Caddy front door templates`.

### Task 7: Thesis run (Q8_0) and measurements

- [ ] **Step 1 (`executor: Opus`): Smoke numbers with Q4_K_M (from Task 6 Step 2)** — on the hub: `GGML_VK_VISIBLE_DEVICES=0 ~/corvid/llama/b10581/llama-bench -m <pool>/corvid/models/Qwen3.8-27B/Qwen3.8-27B-Q4_K_M.gguf --rpc <ahnoway-ip>:50052,<optiplex-ip>:50052 -ngl 99 -p 128 -n 64 -r 2` (stop the server unit first to free VRAM, restart after); record backend `Vulkan,RPC`, tok/s, per-node `nvidia-smi --query-gpu=memory.used --format=csv,noheader` during the run; worker journals `journalctl --user -u corvid-rpc | grep -c 'Accepted client'` > 0.
- [ ] **Step 2 (`executor: Opus`): Switch the host unit to Q8_0** (`<gguf>=Qwen3.8-27B-Q8_0.gguf`), `systemctl --user daemon-reload && systemctl --user restart corvid-llama-server`, wait for `/health` ok (time-box 30 min — first load streams ~27 GB to workers; `-c` caches it).
- [ ] **Step 3 (`executor: Opus`): Thesis completion + numbers**

```bash
NONCE=corvid-$(date +%s)
curl -s http://<hub-ip>:8090/v1/chat/completions -H 'Content-Type: application/json' -d "{\"model\":\"qwen3.8-27b\",\"messages\":[{\"role\":\"user\",\"content\":\"($NONCE) In two sentences, what is a village utility?\"}],\"max_tokens\":96}" | jq '.choices[0].message.content, .usage'
for n in ahnoway optiplex "<solarplexus alias>"; do echo "== $n =="; if [ "$n" = ahnoway ]; then nvidia-smi --query-gpu=memory.used --format=csv,noheader; free -g | awk 'NR==2{print "ram used GiB:",$3}'; else ssh "$n" 'nvidia-smi --query-gpu=memory.used --format=csv,noheader; free -g | awk "NR==2{print \"ram used GiB:\",\$3}"'; fi; done
# bench (stop the unit, bench, restart):
~/corvid/llama/b10581/llama-bench -m <pool>/corvid/models/Qwen3.8-27B/Qwen3.8-27B-Q8_0.gguf --rpc <ahnoway-ip>:50052,<optiplex-ip>:50052 -ngl 99 -p 128 -n 64 -r 2   # on the hub
```
Expected: a sensible two-sentence answer; `usage` present; per-node memory within the granted exception; GB arithmetic in the run file: 26.6 GiB weights + ~0.5 GiB KV > 25 GiB. If the hybrid model fails over RPC, switch to Muse-Glimmer-30B Q8_0 (record) — the spec lists the order.

- [ ] **Step 4 (`executor: Opus`): No-logging check** — `grep -r "$NONCE" ~/corvid/logs` on the hub (via ssh) and `journalctl --user -u corvid-rpc | grep -c "$NONCE"` on both workers, `ssh <solarplexus alias> 'grep -c "'$NONCE'" /var/log/caddy/corvid.log'` → all `0`.

### Task 8: Acceptance, run file, hand back

- [ ] **Step 1 (`executor: Opus`):** run the eight acceptance checks of spec §7 exactly, paste outputs into the run file, and add the proposed status line: `Phase 1 — thesis: done <date> (<model> <quant>, <GiB> across 3 nodes, pp <x>/tg <y> t/s); across houses: pending (ADR-0004 ii)`.
- [ ] **Step 2 (`executor: Opus`): Restore default caps** — `systemctl --user set-property corvid-rpc.service CPUQuota=120% MemoryMax=1.6G` on ahnoway, the optiplex equivalent (`MemoryMax=3.2G`), hub `CPUQuota=40% MemoryMax=1.6G`; leave the units enabled (the pool stays up) unless the founder says otherwise.
- [ ] **Step 3 (`executor: Opus`):** sanitise the run file (`grep -nE '192\.168\.|@|id_[a-z]|/home/' docs/runs/phase-1-$D.md` → none), commit, `git push -u origin phase-1-first-shared-model`, **stop**. The main session merges, mirrors the summary into `status.md`, files S-04 from Task 7's numbers if S-04 had not run, and accepts ADR-0003's amendment.

---

## Self-review record (writing-plans checklist, 2026-08-22)

1. **Spec coverage:** D1/D2 → Task 2; D3 → Tasks 4/6; D4 → Task 3 + Task 7; D5/D6 → Task 6; D7 → Tasks 4/5/8; D8 → Task 7 Step 4 + unit flags; D9 → Task 1; D10 → binding checks; D11 → Task 3 Step 2; §6 error handling → Task 0 preflight, Task 7 fallback, Task 8 caps restore; §7 acceptance → Task 8.
2. **Placeholders:** none of the forbidden tokens; `<…>` are runtime inputs named in Global Constraints.
3. **Consistency:** ports 8090/8093 per ADR-0003; tag b10581 everywhere; unit names `corvid-rpc` / `corvid-llama-server` used identically in Tasks 4–8; caps match Appendix B defaults and the Task 5 exception.
