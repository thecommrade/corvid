# S-04 Completion & Phase 0 Closeout: Implementation Plan (one 3-hour Opus session)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement
> this plan task-by-task in your own session (an **Opus 5** session on ahnoway, founder
> present). Steps use checkbox (`- [ ]`) syntax. Executor tags (package spec Appendix A):
> **`Opus`** = you; **`Opus (splx-root)`** = you through the solarplexus root path (preflight
> proves it); **`founder`** = stop, print the handoff block, wait for "done" + pasted output,
> verify with the named command, continue. You never edit `docs/status.md`; all evidence goes
> to `docs/runs/S-04-<YYYY-MM-DD>.md` (raw logs to `docs/runs/raw/`, git-ignored).
> **Prerequisite:** the founder (or main session) has set `docs/status.md` to
> `**Node in use by:** Opus (S-04)` (check: the line mentions both) before you start; the
> founder is reachable for the whole session.

**Goal:** Finish spike S-04 — the thesis number: a Q8_0 model too big for any single node
produces a benchmarked completion split across all three nodes — then bank the results,
land the F2-persistence ADR, and close out the remaining pre-approved Phase 0 debts.

**Architecture:** Same S-04 topology as 2026-08-23 — `ggml-rpc-server` workers on ahnoway
and optiplex (tailnet-IPv4-bound, capped transient user units), `llama-bench`/`llama-cli`
client on solarplexus — **plus the fix the 2026-08-23 failure demanded: worker RAM must join
the split.** Total reported free VRAM is ~17 GiB (S-02: 7577 + 5568 + 4247 MiB) vs Q4 ≈ 17.7
GiB and Q8 ≈ 26.6 GiB, so a GPU-only split cannot fit either model; Task 3 makes placement
explicit (CPU devices exported + `-ts` shaped to the caps). The Q4 and Q8 load windows are
used for the paper work (ADR-0008, §4 credit row, persistence edits) so the 3-hour box holds.

**Tech Stack:** llama.cpp b10581 Vulkan prebuilts (pinned fleet-wide; RPC protocol rejects
mismatches) · systemd-run transient user units · Tailscale kernel mode on all three nodes.

**Spec:** `docs/research/spikes/S-04-thesis-split.md` — read first, then
`docs/runs/S-04-2026-08-23.md` (the parked state this plan resumes).
**Also read:** `CLAUDE.md` (§5, §7), `docs/status.md` (do not edit), the `remote-step`,
`spike`, `new-adr`, `add-dependency` skills, `docs/runs/phase-0-2026-08-23.md` (F1/F2
mechanics), `docs/research/R03-llamacpp-rpc-on-this-fleet.md` (F8/F9 rpc cache, F12 split
behaviour, the S-02 `--list-devices` figures) + `R04-model-selection-phase1.md` (F16 model
sizes, backup-model ladder).

## Approvals granted (founder, 2026-08-31 — "If anything needs my preapproval during that period, I'll sign off on it")

- **Executor:** the spike skill restricts spike executors to main-session/founder; the
  founder's 2026-08-31 approval grants an **attended-Opus exception for this run** (recorded
  here, on the S-04 card in Task 8, and in the run file). All root steps remain `founder` or
  `Opus (splx-root)`.
- **Caps:** the 2026-08-23 demo exception is **renewed** for this run (≤ 3 h): ahnoway
  `CPUQuota=400% MemoryMax=10G` VRAM ≤ 7 GB · optiplex `CPUQuota=300% MemoryMax=12G` VRAM
  ≤ 5 GB · solarplexus `CPUQuota=200% MemoryMax=8G` VRAM ≤ 3.5 GB · `nice -n 19`.
  MemoryMax is per NODE: if a node runs two rpc units (Task 3 fallback), their combined
  MemoryMax stays within that node's grant. Exceeding 3 h or any cap ⇒ stop and ask the
  founder for a fresh grant — pre-approval does not stretch the caps.
- **Founder-gated actions pre-approved:** hub apt unwedge + Tailscale upgrade (interactive,
  no `-y` — package prompts stay visible); optiplex F2 rule re-apply; `protonvpn.conf`
  PostUp/PreDown persistence edit on both hubs; a 50053/tcp tailnet-scoped opening on
  optiplex if Task 3's fallback needs it; ssh-policy → accept; key-expiry check.
  Pre-approval means don't stop to ask — but every root command still lands on the
  founder's keyboard (or splx-root), with its handoff block printed first.

## Live-state snapshot (read-only probe, 2026-08-31 — trust but re-verify in Task 1)

| Node | State |
|---|---|
| ahnoway | binaries at `~/corvid-s02/vulkan/llama-b10581/` ✓ · GPU baseline **548 MiB used / 8192, 71 °C at idle** (desktop session — "near-zero VRAM" means ≈ this baseline, not 0) · RAM: only ~6 G available (desktop uses ~9 G) — CPU-device share must stay small here · on AC · no 50052/5201 listeners · Tailscale 1.102.3 · tailscale0 lives in firewalld zone **trusted** (permanent) |
| solarplexus | both GGUFs + `sha256.txt` at `<pool>/corvid/models/Qwen3.8-27B/` ✓ (Q4_K_M ≈ 17.7 GiB, Q8_0 ≈ 26.6 GiB) · 7.1 T free · binaries ✓ · guard rules pref 5205 (v4+v6) intact · **apt-get PID 386894 still wedged (60 days)** · Tailscale **1.98.4** (behind) · no stray listeners · ~12 G RAM available |
| optiplex | **REBOOTED ~Aug 26 → F2 fix rule GONE (v4+v6)**; Proton rules re-created at prefs 5208/5209 · iperf3 daemon on \*:5201 gone (that founder chore is moot — verify only) · binaries ✓ · Tailscale 1.102.3 · ~20 G RAM available (the CPU-device workhorse) · baseline load ≈ 2–3 (production; abort threshold stays > 6) |
| paths | tailscale ping direct to both, BUT first-pong RTT to optiplex was 149 ms via an unexpected subnet — Task 2 measures steady-state RTT (plain `ping`, post-F2) before benching |

**Why "it still pings" proves nothing:** `tailscale ping` and TCP :22 on tailnet IPs are
handled by tailscaled itself (marked traffic; Tailscale SSH intercepts :22 in-process).
An unmarked user-space listener like rpc-server:50052 — and even kernel SYN-ACK/ICMP replies —
still route through Proton's rules and die without F2. **Verify F2 with plain `ping` and
TCP :50052, never with ssh or `tailscale ping`.**

## Global Constraints

- Executor tags + founder handoff protocol + BatchMode preflight: per the `remote-step`
  skill. Resolve node addressing at runtime: `<ahnoway-100.x>`/`<optiplex-100.x>`/
  `<hub-100.x>` from `tailscale status` on ahnoway; `<pool>` and the unattended solarplexus
  ssh invocation from the founder's private notes per `remote-step`.
- **Privacy in committed files:** never write resolved 100.x device IPs, usernames, account
  emails, key names, or LAN details into the committed run file or any doc — raw command
  output containing them (e.g. `tailscale status`, founder paste-backs) goes to
  `docs/runs/raw/` (git-ignored) or a scratch note; committed text keeps the `<…-100.x>`
  placeholders and sanitised excerpts. The literals `100.64.0.0/10` and
  `fd7a:115c:a1e0::/48` are public well-known ranges and fine to commit.
- llama.cpp **b10581** everywhere; binaries at `~/corvid-s02/vulkan/llama-b10581/` (the S-04
  card's `~/corvid-s02/b10581/` is stale). Workers bind `-H <their tailnet IPv4>` only —
  never 0.0.0.0 (repo guard + `scripts/lint-bind-targets.sh` enforce).
- Every heavy command wrapped in `systemd-run --user` with the granted caps + `nice -n 19`;
  `systemctl --user reset-failed <unit>` before every transient-unit name reuse. On
  optiplex, `export XDG_RUNTIME_DIR=/run/user/1000` before any `systemctl --user`.
- optiplex: user-level only for Opus; root = founder; never touch its Postgres
  (127.0.0.1:5432), its services, or /mnt/crowdata. Ignore tailnet peers `void`, `fud-pi`,
  `jacobs-s25`.
- Log hygiene: no prompt/completion text in any log. `-v` is permitted ONCE, on the Q4 smoke
  bench (diagnosis, not serving). The Task 7 nonce grep must return 0 everywhere.
- Gotchas that already cost hours — do not relearn them: `pkill -x`, never `pkill -f`, from a
  compound naming the target · llama-cli needs `-st --single-turn` + explicit `-c` (never
  `-no-cnv`; default `-c 0` = model-max ctx ≈ 16 GiB KV) · `GGML_RPC_DEBUG=1` is silent on
  these prebuilts · **never run `firewall-cmd --reload`** (wipes runtime state) ·
  `tailscale ping` exits on the first direct pong (`--until-direct` defaults true) — it
  cannot measure steady-state RTT.
- Abort criteria (any → stop units, run undo, record): GPU > 85 °C any node · swap in use on
  solarplexus · optiplex load > 6 · Plex/Immich unhealthy.
- **Time gate:** if the Q8_0 bench has not STARTED by T+90 min, cut Task 6 Step 3's rerun
  and Task 9 Step 1, and protect Tasks 7–8. The 3-hour box is a cap condition, not a wish.
- Git: repo-local identity `thecommrade` (verify before first commit). Conventional commits
  + Co-Authored-By trailer, small; branch `run/s04-completion`; push the branch at the end
  and **stop** — the main session merges, runs save-state, and tags `m2` → `package-v1`.
- If the Q4 smoke fails its gate (Task 4), do NOT burn the session retrying: run the
  2-minute arithmetic, file the evidence, and pivot to Tasks 5 + 9 — the session still
  banks the ADR, credit row, persistence, and closeout.

## File Structure

| Path | Responsibility | Task |
|---|---|---|
| `docs/runs/S-04-<date>.md` | tonight's evidence: numbers, VRAM table, GB arithmetic, handoffs, proposed status.md lines | 1–9 |
| `docs/runs/raw/S-04-<date>-*.log` | raw bench/cli output + anything with real IPs (git-ignored) | 1–7 |
| `docs/adr/0008-tailnet-routes-survive-vpn-reconnects.md` | F2 persistence decision | 5 |
| `CLAUDE.md` §4 | Qwen3.8-27B credit row | 5 |
| `docs/research/spikes/S-04-thesis-split.md` | Result → DONE; renewed exception + executor note | 8 |
| `docs/research/R03-…` / `R04-…` / `R01-…` | spike-result rows + F24 cross-ref | 8 |

---

### Task 1: Preflight and baselines (~10 min)

- [ ] **Step 1 (`executor: Opus`):** Read the Spec + Also-read list. Confirm
  `docs/status.md`'s "Node in use by" line mentions both `Opus` and `S-04` (if not: stop,
  ask founder). `git -C ~/projects/corvid config user.name` → `thecommrade`, then
  `git switch -c run/s04-completion`. Ask the founder one line: "Plex/Immich idle — OK to
  bench?" (precondition on the card).
- [ ] **Step 2 (`executor: Opus`):** BatchMode preflights + baselines. Raw output (contains
  real IPs) → `docs/runs/raw/`; the committed run file gets placeholders only.

```bash
ssh -o BatchMode=yes optiplex true && echo optiplex-ok
ssh -o BatchMode=yes splx-root true && echo splx-root-ok   # fails → founder loads the agent key NOW (remote-step), before Task 2
# solarplexus user-level: the unattended invocation per remote-step → run `true`, expect ok
nvidia-smi --query-gpu=memory.used,memory.total,temperature.gpu --format=csv,noheader  # ahnoway baseline (~548 MiB; note temp)
tailscale ip -4   # + `tailscale status` → resolve <ahnoway-100.x>, <optiplex-100.x>, <hub-100.x> (raw only)
```

### Task 2: Founder unblock block (~15 min, all pre-approved)

- [ ] **Step 1 (`executor: Opus (splx-root)`):** Unwedge hub apt (the July 2 zombie).
  First learn which unit actually owns it — then stop that unit (kills only its cgroup;
  Plex/Docker untouched). Never delete the lock file.

```bash
ps -o unit=,cmd= -p 386894        # via splx-root → expect apt-daily.service; stop the unit it names:
systemctl stop apt-daily.service
ps -p 386894 -o pid,cmd 2>&1      # Expected: no such process
```

- [ ] **Step 2 (`executor: founder`):** Hub Tailscale upgrade, interactive so the package
  prompt is readable (global rule: no `-y`). Handoff block:

> On solarplexus: `sudo apt-get update` (expect clean), then
> `sudo apt-get install --only-upgrade tailscale` — read the prompt, confirm manually.
> Then paste: `tailscale version` (paste goes to raw/scratch, not the committed run file)

Verify (`Opus`, via the user-level alias — no root needed): version ≥ 1.102; from ahnoway
`tailscale ping -c 2 <hub-100.x>` → direct; on the hub
`ip rule show | grep 5205; ip -6 rule show | grep 5205` → BOTH guard rules present (they
survive a tailscaled restart; only a reboot clears them). **Do this before any bench — a
tailscaled restart mid-load would sever the RPC streams.**

- [ ] **Step 3 (`executor: Opus`, then `founder`):** F2 on optiplex — demonstrate broken,
  then re-apply the same guard as 2026-08-23 (pref 5205, matching the hub; the pref value is
  hygiene, not the protection — see ADR-0008 in Task 5: no static pref survives an unguarded
  wg-quick reconnect, durability comes from PostUp/PreDown).

```bash
ping -c 2 -W 2 <optiplex-100.x>   # from ahnoway. Expected NOW: 100% loss (F2 gone)
```

Founder handoff (on optiplex):

> `sudo ip rule add to 100.64.0.0/10 lookup 52 pref 5205`
> `sudo ip -6 rule add to fd7a:115c:a1e0::/48 lookup 52 pref 5205`
> Paste back: `ip rule show | head -6; ip -6 rule show | head -6`

Verify (`Opus`): `ping -c 10 <optiplex-100.x>` from ahnoway now succeeds — record loss = 0
AND the median RTT (this is the steady-state number that sets tg expectations: decode ≈
4 blocking RTTs/token, R01-F24; if median > 30 ms, don't abort — record
"expected tg ≈ 1/(local-tg⁻¹ + 4·RTT)" and proceed; RPC exists to *fit* models, CLAUDE.md
§3.2). Record the before/after pair — live F2 evidence. (If the "before" ping unexpectedly
succeeds, note it — Proton's current accidental ordering — and apply the guard anyway.)

- [ ] **Step 4 (`executor: Opus`):** Confirm the iperf3 daemon stayed dead post-reboot:
  `ssh optiplex 'ss -tln | grep :5201 || echo clear; systemctl is-enabled iperf3 2>&1'`.
  If `enabled`: founder handoff `sudo systemctl disable iperf3` (disable only — nothing is
  running). Otherwise this leftover is closed; say so in the run file.

### Task 3: Workers up with a placement that fits (~20 min)

**Why this task exists:** the 2026-08-23 Q4 failure has two candidate causes and the plan
tests both. (H1) leaked buffers from two killed clients — delta was only ~155 MiB. (H2)
**over-subscription**: default split places ALL weights across the exported GPU devices in
proportion to free memory (R03-F12); free VRAM totals ~17 GiB (S-02) vs Q4 ≈ 17.7 GiB —
ahnoway's proportional share (~7.7 GiB) exceeds its ~7.5 GiB free, matching the refused
~254 MB buffer on RPC0[ahnoway]. H2 is favoured by the arithmetic; fresh workers (cheap)
rule H1 in or out as a compounding factor. **The fix for H2 is to bring worker RAM into the
split and steer shares with `-ts`.**

- [ ] **Step 1 (`executor: Opus`):** Launch workers exporting **GPU + CPU** devices.
  Preferred: one unit per node with `-d Vulkan0,CPU`. First check acceptance:
  `~/corvid-s02/vulkan/llama-b10581/ggml-rpc-server --help | grep -A2 -- -d` — if `-d` takes
  a comma list, use it; if not, use the fallback in Step 2.

```bash
# ahnoway (local):
systemctl --user reset-failed corvid-s04-rpc 2>/dev/null
systemd-run --user --unit=corvid-s04-rpc -p CPUQuota=400% -p MemoryMax=10G \
  --setenv=GGML_VK_VISIBLE_DEVICES=0 \
  nice -n 19 "$HOME/corvid-s02/vulkan/llama-b10581/ggml-rpc-server" \
  -H <ahnoway-100.x> -p 50052 -d Vulkan0,CPU -t 4 -c
# optiplex (one ssh, user-level):
ssh optiplex 'export XDG_RUNTIME_DIR=/run/user/1000; \
  systemctl --user reset-failed corvid-s04-rpc 2>/dev/null; \
  systemd-run --user --unit=corvid-s04-rpc -p CPUQuota=300% -p MemoryMax=12G \
  --setenv=GGML_VK_VISIBLE_DEVICES=0 \
  nice -n 19 "$HOME/corvid-s02/vulkan/llama-b10581/ggml-rpc-server" \
  -H <optiplex-100.x> -p 50052 -d Vulkan0,CPU -t 4 -c'
```

Check each worker's journal (`journalctl --user -u corvid-s04-rpc -n 20`) for BOTH devices
being served.
- [ ] **Step 2 (`executor: Opus`, only if `-d` refuses a list):** Fallback — a SECOND
  rpc-server unit per worker, `corvid-s04-rpc-cpu`, on port **50053** with `-d CPU`, same
  shape. Split each node's MemoryMax across its two units (the CPU unit gets the bulk:
  ahnoway 3G+7G, optiplex 2G+10G). Firewall: ahnoway needs nothing (tailscale0 is in the
  trusted zone); optiplex needs the founder to mirror the existing tailnet-scoped 50052 ufw
  rule for 50053/tcp (pre-approved; handoff block with the existing rule as template). The
  hub's `--rpc` list then carries all four `host:port` entries, GPU endpoints first.
- [ ] **Step 3 (`executor: Opus`):** Enumerate the pool from the HUB — this doubles as the
  honest F2/firewall test (real user-space sockets):

```bash
# on solarplexus: nc -z -w 3 <ahnoway-100.x> 50052; echo ahnoway=$?
#                 nc -z -w 3 <optiplex-100.x> 50052; echo optiplex=$?   (and :50053s if Step 2 ran)
# then the same --list-devices invocation S-02 used (see R03), with --rpc <all endpoints>
```

Expected: rc=0 everywhere; the device list shows the RPC Vulkan devices AND the RPC CPU
device(s) with sensible free-memory figures — record them (they refresh S-02's numbers).
If ahnoway's port refuses → `firewall-cmd --get-zone-of-interface=tailscale0` should say
`trusted`; if a reboot lost the binding, founder handoff re-adds the interface to trusted
(NO per-port rule in `public`, NO `--reload`). If optiplex's port refuses → back to Task 2
Step 3; do not proceed until every endpoint answers.
- [ ] **Step 4 (`executor: Opus`):** Compute `-ts` from the live device list, in the exact
  device-enumeration order it prints (do not assume; RPC and local device order must be read
  off the output). Budget per the caps — worked example to adapt (Q8 ≈ 26.6 GiB + ~1 GiB
  KV/overhead): Vulkan shares ahnoway 6.5 / optiplex 4.5 / hub 3.0 (within 7/5/3.5), CPU
  shares optiplex ~10 / ahnoway ~3 (within MemoryMax and the nodes' available RAM — ahnoway
  has only ~6 G free, keep its CPU share small). Record the chosen `-ts` and the arithmetic
  in the run file. If it cannot fit within the caps, ask the founder for a one-line bump
  (optiplex has ~20 G available) rather than silently exceeding a cap.

### Task 4: Q4_K_M smoke — the gate (~15–35 min; start Task 5 as soon as the load begins)

- [ ] **Step 1 (`executor: Opus`):** On the hub, detached capped unit, output to a file on
  the hub (never trust a long ssh pipe on Wi-Fi); `-v` allowed here only:

```bash
systemctl --user reset-failed corvid-s04-llama 2>/dev/null
systemd-run --user --unit=corvid-s04-llama -p CPUQuota=200% -p MemoryMax=8G \
  --setenv=GGML_VK_VISIBLE_DEVICES=0 \
  bash -c 'cd ~/corvid-s02/vulkan/llama-b10581 && nice -n 19 ./llama-bench \
    -m <pool>/corvid/models/Qwen3.8-27B/Qwen3.8-27B-Q4_K_M.gguf \
    --rpc <endpoints-from-task-3> -ngl 99 -ts <from-task-3-step-4> \
    -p 128 -n 64 -r 2 -v > ~/s04-q4-smoke.log 2>&1'
```

Worker shards (~13 GB) stream at the hub's 40–65 Mbit/s send ceiling (S-01) ≈ 25–45 min.
Poll `tail -20 ~/s04-q4-smoke.log` every ~3 min; transfer progress must be visible in `-v`
output within 5 min. **Work Task 5 during the wait.**
- [ ] **Step 2 (`executor: Opus`) — GATE:**
  - **PASS** (backend `Vulkan,RPC`, pp/tg rows): record numbers + per-device VRAM/RAM, scp
    the log to `docs/runs/raw/`, name which hypothesis the pass supports (fresh workers +
    new placement → likely H2; say so honestly — the record currently blames H1), go to
    Task 6.
  - **FAIL** (alloc error): 2-minute arithmetic FIRST — refused buffer size + per-device
    shares from the `-v` tail vs the Step 3 free-memory figures. If the shares exceed a
    device's memory, it's placement: fix `-ts` once and rerun (model already cached on
    workers via `-c` — the retry load is fast). If shares fit and it still refuses, check
    worker journals (`journalctl --user -u corvid-s04-rpc -n 50`) and per-node free memory;
    ONE more `-ts` adjustment max. Still failing → stop, file everything, **pivot to Tasks
    5 + 9**. Do not attempt Q8_0. (Single-worker isolation runs prove nothing here — Q4
    cannot fit any two-device subset of this fleet; don't run them.)

### Task 5: The load-window work (start during Task 4's load; finish during Task 6's)

- [ ] **Step 1 (`executor: Opus`):** ADR-0008 via the `new-adr` skill (0006 stays reserved
  for topology): **"Tailnet routes survive VPN reconnects (PostUp/PreDown guard)"**.
  Decision: on BOTH hubs, the wg-quick `protonvpn.conf` `[Interface]` gains
  `PostUp = ip rule add to 100.64.0.0/10 lookup 52 pref 5205 2>/dev/null || true; ip -6 rule add to fd7a:115c:a1e0::/48 lookup 52 pref 5205 2>/dev/null || true`
  and the matching `PreDown = ip rule del … || true` pair. Rationale (get this right — it
  was mis-drafted once): the 2026-08-23 netns experiment proved wg-quick re-adds its rules
  at kernel-default preference = lowest-existing−1, which reaches pref 0, so **no static
  pref survives an unguarded reconnect**; durability rests entirely on the PreDown-delete +
  PostUp-re-add pair running on every clean wg-quick cycle (PostUp runs after wg-quick's own
  rules land, so the guard is re-asserted above them each time). Pref 5205 is kept for
  fleet symmetry with the hub's existing guard. Consequences must note honestly: (a) an
  UNCLEAN re-up (crash where PreDown never ran) leaves the stale guard below Proton's fresh
  rules until the next clean cycle — manual recovery is the same two `ip rule add` lines;
  (b) on solarplexus a Proton reconnect would also land rules above the hub's own LAN rule
  (pref 10) — CORVID's guard protects only the tailnet; recommend (founder's infra,
  founder's call) an analogous `to <lan-subnet>/24 lookup main` PostUp line. Alternatives
  rejected: a "winning" static pref (netns-refuted), NM dispatcher (Proton runs as wg-quick
  here). **new-adr steps that touch `docs/status.md` (decisions-table row via save-state,
  staging status.md) are NOT yours** — write the proposed decisions-table row into the run
  file instead and commit the ADR alone; the ADR's "§4 rows added in this commit" section
  says "none". Commit: `docs(adr): ADR-0008 tailnet routes survive VPN reconnects`.
- [ ] **Step 2 (`executor: founder`, optiplex) + (`executor: Opus (splx-root)`, hub):**
  Apply the conf edit on both hubs. Founder handoff (optiplex):

> `sudo cp /etc/wireguard/protonvpn.conf /etc/wireguard/protonvpn.conf.bak-<date>`
> `sudoedit /etc/wireguard/protonvpn.conf` → add the two ADR-0008 lines under `[Interface]`
> Paste back: `sudo grep -c "lookup 52 pref 5205" /etc/wireguard/protonvpn.conf` (expect 2)

On the hub via splx-root: first `systemctl list-units "wg-quick@*"` to learn the actual conf
name, back it up, add the same pair, same grep check. **Edits are inert until the next
`wg-quick` cycle — do NOT bounce the VPN while benches run.** (Live test: Task 9, only.)
- [ ] **Step 3 (`executor: Opus`):** Qwen3.8-27B credit row, per the `add-dependency` skill:
  verify licence + author at the model's primary download source (expected Apache-2.0, Qwen
  team / Alibaba Cloud — verify, don't assume), add the CLAUDE.md §4 row (Phase 1 plan Task
  3 Step 2 has the row shape), note both quants + sha256s already on the pool with the
  download recorded in `docs/runs/S-04-2026-08-23.md`. Commit:
  `docs(credits): §4 row for Qwen3.8-27B weights (add-dependency)`.

### Task 6: Q8_0 thesis bench (~60–90 min wall, mostly load wait)

- [ ] **Step 1 (`executor: Opus`):** Same launcher as Task 4 but: Q8_0 file, `-ts` rescaled
  to Q8's ~27.6 GiB total (Task 3 Step 4's example), log `~/s04-q8-bench.log`, **no `-v`**.
  First load streams ~19+ GB to workers (the Q4 `-c` cache does NOT warm Q8 — different
  tensors, R03-F8/F9): budget 40–70 min. Poll every ~10 min while finishing Task 5:

```bash
# hub: tail -5 ~/s04-q8-bench.log ; free -g | head -2   (no swap!)
# ahnoway + optiplex: nvidia-smi --query-gpu=memory.used,temperature.gpu --format=csv,noheader
# optiplex: uptime   (load must stay < 6)
```

- [ ] **Step 2 (`executor: Opus`) — GATE:** on an alloc failure, run the same 2-minute
  arithmetic as Task 4's gate; ONE `-ts` correction is allowed (the retry load is fast —
  Q8 is now in the workers' `-c` cache); a second failure → stop, file the evidence, pivot
  to Tasks 5 remainder + 9. No other retries.
- [ ] **Step 3 (`executor: Opus`):** When the table prints: record backend (`Vulkan,RPC`),
  pp/tg ± σ, per-node peak VRAM vs caps (7/5/3.5), and worker journal
  `grep -ci 'Accepted client'` (> 0 on both). scp the log to `docs/runs/raw/`.
  Time-permitting only (after Task 7, and only if the T+90 gate never fired): one
  `-p 2048 -n 64 -r 1` rerun for a realistic prefill number.

### Task 7: One real completion + log hygiene (~10 min)

- [ ] **Step 1 (`executor: Opus`):** On the hub (explicit `-c 8192`, never default ctx):

```bash
systemctl --user reset-failed corvid-s04-llama 2>/dev/null
systemd-run --user --unit=corvid-s04-llama -p CPUQuota=200% -p MemoryMax=8G \
  --setenv=GGML_VK_VISIBLE_DEVICES=0 \
  bash -c 'cd ~/corvid-s02/vulkan/llama-b10581 && nice -n 19 ./llama-cli \
    -m <pool>/corvid/models/Qwen3.8-27B/Qwen3.8-27B-Q8_0.gguf \
    --rpc <endpoints-from-task-3> -ngl 99 -ts <q8-ts> -c 8192 -n 256 \
    -st --single-turn \
    -p "Explain in three sentences why a village-scale compute co-op needs no blockchain. End with the token XKCD-CORVID-0831." \
    > ~/s04-completion.log 2>&1'
```

Expected: sensible text ending in the token; load is fast (worker `-c` cache).
- [ ] **Step 2 (`executor: Opus`):** Hygiene grep — the nonce must appear ONLY in the hub's
  own output log, never in any journal:

```bash
journalctl --user -u corvid-s04-rpc --since -3h | grep -c 'XKCD-CORVID-0831'   # each worker → 0 (also -rpc-cpu if it ran)
journalctl --user -u corvid-s04-rpc --since -3h | grep -ci 'Accepted client'    # each worker → >0
```

Paste the (sanitised) completion text into the run file.

### Task 8: Arithmetic, undo, filing (~30 min)

- [ ] **Step 1 (`executor: Opus`):** GB arithmetic in the run file: Q8_0 weights (bytes from
  `ls -l`, ≈ 26.6 GiB) + KV at 8k ctx vs the largest single node's ~25 GiB ceiling →
  **§7 proven**; plus the per-node VRAM/RAM placement table from Task 6.
- [ ] **Step 2 (`executor: Opus`):** Undo, in this order — file/scp everything FIRST:

```bash
# workers: systemctl --user stop corvid-s04-rpc (and corvid-s04-rpc-cpu if it ran); ss -tln | grep -E ':5005[23]' || echo no-listener
# hub: systemctl --user stop corvid-s04-llama 2>/dev/null; rm ~/s04-*.log (after scp)
# THEN, all three nodes: rm -rf ~/corvid-s02 ~/corvid-s03
```

Deliberate retentions, stated in the run file: firewall rules STAY (Phase 1 reuses them);
model weights + sha256 STAY on the pool; the workers' rpc tensor cache at
`~/.cache/llama.cpp/rpc` STAYS (record its size with `du -sh` — Phase 1 reuses the same
b10581 + GGUFs; R03 notes no eviction mechanism).
- [ ] **Step 3 (`executor: Opus`):** File the numbers: S-04 card Result → DONE (append
  under the PARTIAL entry) **and update the card's Exception record** (renewed grant:
  values, ≤3 h window, granted by founder 2026-08-31) **and Executor field** (append:
  "completion run <date>: Opus with founder present — founder-granted exception to the
  main-session/founder-only rule") · new S-04 row in R03's `## Spike results` (acceptance
  test 3's "within 20% of S-04" reference) · replace R04's pending S-04 row (placement
  arithmetic + measured per-node GB; note which placement strategy won — this answers R03/
  R04's open question about worker RAM in the split) · one cross-ref line at R01's S-01
  spike row (F24 calibration vs tonight's measured tg). Note in R03 whether the hub looked
  like the bottleneck (feeds reserved ADR-0006 — record the observation, do not write that
  ADR tonight).
- [ ] **Step 4 (`executor: Opus`):** Sanitise + commit + push. Run over EVERYTHING staged;
  inspect every hit (expected legitimate hits: `wg-quick@…` unit names, `100.64.0.0/10`):

```bash
grep -nE '192\.168\.|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|id_[a-z]|/home/|100\.[0-9]+\.[0-9]+\.[0-9]+' \
  docs/runs/S-04-*.md docs/adr/0008-*.md docs/research/R0{1,3,4}-*.md \
  docs/research/spikes/S-04-thesis-split.md CLAUDE.md | grep -v '100\.64\.0\.0/10'
git add -A && git commit -m "docs(research): S-04 complete — Q8_0 thesis split benched across three nodes"
git push -u origin run/s04-completion
```

(The ADR and credit-row commits from Task 5 land separately; this is the final commit.
All commits carry the Co-Authored-By trailer.)

### Task 9: Time-permitting closeout (in value order)

- [ ] **Step 1 (`executor: founder`, ≥ 20 min left AND benches done):** Live ADR-0008 test
  on optiplex: `sudo systemctl restart wg-quick@protonvpn` → `ip rule show | head -6` shows
  the pref-5205 guard back; from ahnoway `ping -c 3 <optiplex-100.x>` succeeds. Record.
- [ ] **Step 2 (`executor: founder`):** Tailscale admin console: ssh-policy check-mode →
  `accept` (unattended tailnet ssh stops stalling); key-expiry disabled on the three build
  nodes (ADR-0002).
- [ ] **Step 3 (`executor: Opus`):** Print the handback block for the main session:
  what landed; what's open (S-01 LAN leg + wired re-runs; cross-house name-ping, ADR-0004
  §1(b)); and the main session's list — merge `run/s04-completion`, save-state (rewrite
  RESUME, append the **ADR-0008 decisions-table row** and the **renewed cap-exception
  mirror line** — proposed text is in the run file), tag `m2` → `package-v1`. Then stop.

---

## Self-review record (writing-plans checklist + adversarial review, 2026-08-31)

- **Spec coverage:** every "Still to run" item of `S-04-2026-08-23.md` has a task (smoke →
  T4, Q8 → T6, completion → T7, arithmetic/hygiene → T7–T8, undo → T8, R03/R04 filing →
  T8); status.md's founder leftovers all appear (apt/upgrade T2.1–2, F2 T2.3, iperf3 T2.4,
  ssh-policy/key-expiry T9.2, ADR-0008 T5, §4 row T5.3). Deliberately excluded, named in
  the handback: S-01 remainders, cross-house ping, ADR-0006 (reserved; observation only),
  tags/merge/save-state (main-session work).
- **Adversarial review (2-agent workflow, ops + rules lenses) — all findings applied:**
  the placement blocker (GPU-only split can't fit Q4/Q8 in ~17 GiB free VRAM → new Task 3:
  CPU devices + `-ts`, dual-hypothesis gates, no single-worker reruns); pref-1 rationale
  corrected to the netns-verified mechanism (no static pref survives; PostUp/PreDown is the
  protection; pref 5205 kept for symmetry); timeline honesty (T4 relabeled, T+90 gate,
  designated cuts); reset-failed on every unit reuse; RTT via plain post-F2 ping (tailscale
  ping exits at first direct pong); splx-root preflight; trusted-zone (not public) firewall
  contingency; privacy — raw IP-bearing output to raw/ only, 100.x added to the widened
  sanitise grep; new-adr/status.md single-writer conflict resolved (propose in run file,
  handback line); renewed exception + executor deviation recorded on the card; rpc cache
  retention declared; Co-Authored-By; "Node in use by: Opus (S-04)" format.
- **Consistency:** unit names `corvid-s04-rpc`/`-rpc-cpu`/`corvid-s04-llama` consistent
  incl. undo; binary path `~/corvid-s02/vulkan/llama-b10581/` everywhere; caps match the
  renewed exception; `<endpoints-from-task-3>`/`<q8-ts>` resolved by Task 3 Step 4 and
  echoed in T4/T6/T7.
