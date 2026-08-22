# Phase 0 — The Handshake: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task in your own session (an **Opus** session on ahnoway). Steps use checkbox (`- [ ]`) syntax for tracking. Every step carries an `executor:` tag (package spec Appendix A): **`Opus`** = you, unattended; **`Opus (splx-root)`** = you, through the root path on solarplexus — only after the preflight shows it works; **`founder`** = stop, print the handoff block, wait for "done" + output, verify, continue. You never edit `docs/status.md`; you write `docs/runs/phase-0-<YYYY-MM-DD>.md` and propose one summary line in it.

**Goal:** Finish CORVID's Phase 0 — all three build nodes reach each other by MagicDNS name over the tailnet, solarplexus runs kernel-mode Tailscale and can dial workers, key expiry is off, an unattended access path is recorded, endpoint ports are confirmed free, and one cross-house name-ping is recorded (ADR-0004).

**Architecture:** Tailscale-only changes on three Linux nodes: DNS acceptance (`--accept-dns`), a systemd drop-in removal + restart on the hub (with armed auto-rollback), admin-console toggles by the founder, and verification. No CORVID software is installed; nothing binds a port except a 60-second throwaway listener.

**Tech Stack:** Tailscale CLI 1.102+, systemd (`systemd-run`, `loginctl`), systemd-resolved (`resolvectl`), iproute2, OpenSSH, bash, python3 (stdlib only).

**Spec:** `docs/superpowers/specs/2026-08-22-phase-0-handshake-design.md` (read it first). **Also read:** `CLAUDE.md`, `docs/status.md`, `docs/research/R00-phase0-facts.md`, ADR-0002, ADR-0003, ADR-0004, and the `remote-step` skill (`.claude/skills/remote-step/SKILL.md`).

## Global Constraints

- Executor tags on every step; founder handoff protocol for every `executor: founder` step (Appendix A of the package spec).
- Unattended ssh aliases: `<optiplex alias>` = `optiplex` (or `oplx`); `<solarplexus alias>` = the documented unattended alias from the founder's private notes (the `remote-step` skill says which); root on solarplexus = `splx-root` (agent key loaded by the founder) or the Tailscale-SSH root path once Task 1 grants it; **never root on optiplex**.
- Placeholders: `<tailnet>` = the tailnet's MagicDNS suffix (shown by `tailscale dns status`), `<optiplex-tailnet-ip>` / `<hub-tailnet-ip>` = from `tailscale status`, `<service-user>` = the unix user the unattended aliases log in as (from `whoami` over the alias). Resolve them at runtime; do not write LAN/public IPs, usernames or key names into the run file.
- Caps (package spec Appendix B) apply to the one throwaway listener: wrap it in `systemd-run --user --scope -p CPUQuota=40% -p MemoryMax=1.6G nice -n 19` on the hub.
- Nothing binds `0.0.0.0`; the throwaway listener binds the hub's tailnet IP only.
- Every system change has an undo written before it runs; solarplexus step 2 runs only with the founder present and the auto-rollback armed.
- Evidence: append each task's outputs to `docs/runs/phase-0-<YYYY-MM-DD>.md` as you go (sanitised); commit on a branch `phase-0-handshake`; conventional commits with the `Co-Authored-By` trailer.

## File Structure

| Path | Responsibility | Task |
|---|---|---|
| `docs/runs/phase-0-<date>.md` | run evidence (create in Task 0, append throughout) | 0–8 |
| `.claude/skills/remote-step/SKILL.md` | records the chosen unattended transport (alias names only) | 1, 6 |
| `docs/research/R00-phase0-facts.md` | open questions closed (ACL paste, wg reads) | 1 |
| `docs/adr/0002-membership.md`, `0003-endpoints.md` | unchanged (0003 port confirmation noted in run file) | 7 |

---

### Task 0: Preflight and run file

**Files:** Create `docs/runs/phase-0-<YYYY-MM-DD>.md`

- [ ] **Step 1 (`executor: Opus`): Create the run file**

```bash
cd ~/projects/corvid && git checkout -b phase-0-handshake
D=$(date +%F); printf '# Phase 0 handshake — run %s\n\nExecutor: Opus session on ahnoway (+ founder steps). Sanitised: no usernames, keys, LAN/public IPs.\n\n' "$D" > docs/runs/phase-0-$D.md
```

- [ ] **Step 2 (`executor: Opus`): Preflight (package spec Appendix A)**

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 optiplex true; echo "optiplex rc=$?"
ssh -o BatchMode=yes -o ConnectTimeout=8 <solarplexus alias> true; echo "solarplexus rc=$?"
ssh -o BatchMode=yes -o ConnectTimeout=8 splx-root true; echo "splx-root rc=$?"
grep -n 'Node in use by' docs/status.md
tailscale status | head -5
```
Expected: `optiplex rc=0`, `solarplexus rc=0`; `splx-root rc=0` **or** rc≠0 → stop and hand off: "**Founder:** run `ssh-add ~/.ssh/<the key the splx-root alias uses>` on ahnoway, then reply done" and re-run; `Node in use by: none`; all three nodes online in `tailscale status`. Append the outputs to the run file.

- [ ] **Step 3 (`executor: Opus`): Commit the run file skeleton**

```bash
git add docs/runs/phase-0-$D.md && git commit -m "docs(runs): Phase 0 run file (preflight)

Co-Authored-By: Claude Opus <noreply@anthropic.com>"
```

### Task 1: Unattended access path (spec §4 step 0)

**Files:** Modify `.claude/skills/remote-step/SKILL.md`; Modify `docs/research/R00-phase0-facts.md` (close open questions)

- [ ] **Step 1 (`executor: founder`): Paste the live tailnet policy `ssh` section and the DNS page state** — handoff block:

> **Founder:** In the Tailscale admin console → *Access controls*, copy the `"ssh": [ … ]` block (and `"tagOwners"` if present) and paste it here. Then → *DNS*: tell me (a) are any **global nameservers** set? (b) is **MagicDNS** on? (c) is **HTTPS certificates** enabled? Reply with the paste + three answers.

Record the paste (it contains no secrets; replace your login email with `<founder-login>`) in the run file and close R00's open question.

- [ ] **Step 2 (`executor: founder`): Root-only routing reads (explain R00-F4; no keys are read)** — handoff block:

> **Founder:** on optiplex run: `sudo wg show 2>/dev/null | grep -E '^interface|fwmark|listening'; sudo grep -hE '^(Table|FwMark|PostUp|PostDown|PreUp|PreDown|AllowedIPs)\s*=' /etc/wireguard/*.conf` and paste the output (it contains no keys/endpoints). On solarplexus the same command through your root session (or tell me to run it via `splx-root`).

Append (with `<placeholders>` for any IPs) to the run file; add the fact to R00 as `R00-F11` with Status verified.

- [ ] **Step 3 (`executor: founder`): Edit the ssh policy — recommended transport** — handoff block (adapt to the pasted policy's syntax):

> **Founder:** add an `accept` rule for your own devices ahead of the default check rule, e.g.
> ```jsonc
> { "action": "accept", "src": ["<your-login>"], "dst": ["autogroup:self"], "users": ["autogroup:nonroot", "root"] },
> ```
> Save the policy. (Root via Tailscale SSH is used only for solarplexus; optiplex root stays yours.) If you prefer **not** to grant this, say "fallback" and we keep OpenSSH-over-LAN + `splx-root` (then add DHCP reservations for both hubs on the router).

- [ ] **Step 4 (`executor: Opus`): Verify the chosen transport**

```bash
# Tailscale-SSH path (if accept was granted): identity auth, no keys, no browser check
ssh -o BatchMode=yes -o ConnectTimeout=8 <service-user>@optiplex.<tailnet>.ts.net true; echo "ts-ssh optiplex rc=$?"
ssh -o BatchMode=yes -o ConnectTimeout=8 <service-user>@solarplexus.<tailnet>.ts.net true; echo "ts-ssh solarplexus rc=$?"
ssh -o BatchMode=yes -o ConnectTimeout=8 root@solarplexus.<tailnet>.ts.net true; echo "ts-ssh root@solarplexus rc=$?"
# Fallback path: the preflight aliases already proved rc=0
```
Expected: all `rc=0` within ~5 s (no stall). If a command stalls > 20 s, the policy is still in check mode → ask the founder to re-check the edit.

- [ ] **Step 5 (`executor: Opus`): Record the decision in `remote-step` and commit**

Edit `.claude/skills/remote-step/SKILL.md`: under the table add one line — "**Unattended transport (decided <date>):** Tailscale SSH `accept` for the founder's own devices — aliases `ts-optiplex` / `ts-splx` / `ts-splx-root` = `ssh <service-user>@optiplex.<tailnet>.ts.net` etc." (or the fallback wording). Alias *names* only.

```bash
git add .claude/skills/remote-step/SKILL.md docs/research/R00-phase0-facts.md docs/runs/phase-0-$D.md
git commit -m "docs: Phase 0 step 0 — unattended access path decided and verified

Co-Authored-By: Claude Opus <noreply@anthropic.com>"
```

### Task 2: solarplexus — kernel mode, upgrade, linger (spec §4 step 2; BEFORE its DNS step)

**Files:** none in repo (run file only)

- [ ] **Step 1 (`executor: founder`): Presence + idle check** — handoff block:

> **Founder:** open a root shell on solarplexus (`ssh splx-root` from ahnoway, ideally inside `tmux new -s corvid`) and keep it open; confirm no Plex stream / Immich job is running. Reply "ready" with the tmux session name (or "console").

- [ ] **Step 2 (`executor: Opus (splx-root)`): Snapshot + arm the 10-minute auto-rollback**

```bash
ssh splx-root 'cp /etc/systemd/system/tailscaled.service.d/override.conf /root/tailscaled-override.conf.bak && ls -l /root/tailscaled-override.conf.bak'
ssh splx-root "systemd-run --on-active=10m --unit=corvid-ts-rollback bash -c 'cp /root/tailscaled-override.conf.bak /etc/systemd/system/tailscaled.service.d/override.conf && systemctl daemon-reload && systemctl restart tailscaled' && systemctl list-timers corvid-ts-rollback.timer --no-pager | head -3"
```
Expected: backup listed; timer shows `corvid-ts-rollback.timer` with ~10 min left.

- [ ] **Step 3 (`executor: Opus (splx-root)`): Remove the userspace drop-in and restart**

```bash
ssh splx-root 'rm /etc/systemd/system/tailscaled.service.d/override.conf && systemctl daemon-reload && systemctl restart tailscaled && sleep 5 && systemctl is-active tailscaled'
```
Expected: `active`. If the ssh session itself drops (you were using Tailscale SSH over the tailnet), wait 15 s and reconnect via the LAN/`splx-root` path; the service restart is quick.

- [ ] **Step 4 (`executor: Opus (splx-root)`): Verify kernel mode, rules, bypass, reachability**

```bash
ssh splx-root 'tailscale status --self --json | python3 -c "import json,sys; s=json.load(sys.stdin)[\"Self\"]; print(\"Online\", s[\"Online\"])"; ip -br link show tailscale0; ip rule | grep -E "^(5210|5230|5250|5270):"; tailscale netcheck 2>/dev/null | grep -E "UDP|IPv4"; echo "vpn-egress: $(curl -s --max-time 6 https://api.ipify.org)"; tailscale ping -c 2 optiplex.<tailnet>.ts.net; timeout 6 bash -c "cat </dev/null >/dev/tcp/<optiplex-tailnet-ip>/22" && echo dial-ok'
```
Expected: `Online True`; `tailscale0 … UP`; four rules 5210/5230/5250/5270; `UDP: true` and an `IPv4:` endpoint that is **not** the `vpn-egress` IP; `pong … direct`; `dial-ok`. Record in the run file (replace IPs by `<wan>`/`<vpn-egress>`).

- [ ] **Step 5 (`executor: Opus (splx-root)`): Disarm the rollback (only if Step 4 passed)**

```bash
ssh splx-root 'systemctl stop corvid-ts-rollback.timer 2>/dev/null; systemctl stop corvid-ts-rollback.service 2>/dev/null; systemctl list-timers corvid-ts-rollback.timer --no-pager | grep -c corvid || echo disarmed'
```
Expected: `disarmed` (or `0`). **If Step 4 failed:** do nothing — the timer restores the drop-in within 10 min; then run the manual rollback `ssh splx-root 'cp /root/tailscaled-override.conf.bak /etc/systemd/system/tailscaled.service.d/override.conf && systemctl daemon-reload && systemctl restart tailscaled'`, record the failure, stop and ask the founder.

- [ ] **Step 6 (`executor: Opus (splx-root)`): Upgrade Tailscale and re-verify**

```bash
ssh splx-root 'apt-get update -qq && apt-get install -y --only-upgrade tailscale 2>&1 | tail -2 && tailscale version | head -1 && systemctl cat tailscaled | grep -E "^ExecStart" && cat /etc/default/tailscaled | grep -E "^(PORT|FLAGS)="'
```
Expected: version ≥ 1.102; a single packaged `ExecStart=` line (no `--tun=userspace-networking`); `PORT="41641"`, `FLAGS=""`. Re-run Step 4's block → same expectations.

- [ ] **Step 7 (`executor: Opus (splx-root)`): Enable linger for the service user (Phase 1 needs it)**

```bash
ssh splx-root 'loginctl enable-linger <service-user> && loginctl show-user <service-user> -p Linger'
```
Expected: `Linger=yes`. Undo: `loginctl disable-linger <service-user>`.

- [ ] **Step 8 (`executor: Opus`): Commit run-file progress** — `git add docs/runs/phase-0-$D.md && git commit -m "docs(runs): Phase 0 step 2 — solarplexus kernel mode, upgrade, linger" ` (+ trailer).

### Task 3: Tailscale DNS on ahnoway and solarplexus (spec §4 step 1)

- [ ] **Step 1 (`executor: founder`): One-time operator mode on ahnoway** — handoff block:

> **Founder:** on ahnoway run `sudo tailscale set --operator=$USER` (R00-D4) and reply done.

- [ ] **Step 2 (`executor: Opus`): Enable on ahnoway and verify**

```bash
tailscale set --accept-dns=true && sleep 2 && tailscale dns status | head -1
resolvectl status tailscale0 | grep -E 'DNS Servers|DNS Domain'
resolvectl query optiplex.<tailnet>.ts.net | head -1
resolvectl query tailscale.com | head -1
```
Expected: `Tailscale DNS: enabled.`; `DNS Servers: 100.100.100.100`, `DNS Domain: <tailnet>.ts.net`; the peer's tailnet IP; a public answer (via the existing resolver). Undo: `tailscale set --accept-dns=false`.

- [ ] **Step 3 (`executor: Opus (splx-root)`): Enable on solarplexus and verify (after Task 2)**

```bash
ssh splx-root 'tailscale set --accept-dns=true && sleep 2 && tailscale dns status | head -1 && resolvectl status tailscale0 | grep -E "DNS Servers|DNS Domain" && resolvectl query optiplex.<tailnet>.ts.net | head -1 && resolvectl query tailscale.com | head -1'
```
Expected: as Step 2; the public answer still comes from the Pi-hole path (`resolvectl status` shows the Wi-Fi link's DNS unchanged). Undo: `ssh splx-root 'tailscale set --accept-dns=false'`.

- [ ] **Step 4 (`executor: Opus`): Commit** — run file append + commit `docs(runs): Phase 0 step 1 — Tailscale DNS on ahnoway and solarplexus` (+ trailer).

### Task 4: Key expiry off (spec §4 step 3)

- [ ] **Step 1 (`executor: founder`):** handoff block:

> **Founder:** admin console → *Machines* → for **ahnoway**, **solarplexus**, **optiplex**: menu (⋯) → **Disable Key Expiry**. Reply done.

- [ ] **Step 2 (`executor: Opus`): Verify and record**

```bash
tailscale status --json | python3 -c 'import json,sys; d=json.load(sys.stdin); ns=[d["Self"],*d["Peer"].values()]; print({n["HostName"]: n.get("KeyExpiry") for n in ns if n["HostName"] in ("ahnoway","solarplexus","optiplex")})'
```
Expected: `None`/empty expiry for the three (or the founder's paste of the Machines page saying "Expiry disabled"). Append; commit `docs(runs): Phase 0 step 3 — key expiry disabled` (+ trailer).

### Task 5: Membership (spec §4 step 4) — record only

- [ ] **Step 1 (`executor: Opus`):** Append to the run file: "ADR-0002 Accepted 2026-08-22; ACL baseline (tags, member↔member deny) is a founder edit before the first member joins — not part of Phase 0." No command.

### Task 6: SSH hygiene (spec §4 step 5)

- [ ] **Step 1 (`executor: founder`):** handoff block: "Update `~/.ssh/config` aliases (and `networkdocs`) to the transport chosen in Task 1; remove the stale alias that points at the old LAN address. Reply done."
- [ ] **Step 2 (`executor: Opus`):** `ssh -o BatchMode=yes optiplex true && ssh -o BatchMode=yes <solarplexus alias> true && echo aliases-ok` → `aliases-ok`; confirm `remote-step` matches (edited in Task 1). Commit if anything changed.

### Task 7: Endpoints (spec §4 step 6) — confirm ports free

- [ ] **Step 1 (`executor: Opus`):**

```bash
ssh <solarplexus alias> "ss -tlnH | awk '{print \$4}' | grep -E ':(8090|8091|8092|8093)$' || echo 'ports 8090-8093 free'"
```
Expected: `ports 8090-8093 free`. If not, note the taken port(s) in the run file and flag: ADR-0003 says shift the block by +10 — **do not edit the ADR yourself**; the main session does in M3. Commit the run-file line.

### Task 8: Verification + cross-house (spec §4 step 7; acceptance §7)

- [ ] **Step 1 (`executor: Opus`): All-pairs name-ping over the tailnet**

```bash
N="ahnoway solarplexus optiplex"; T=<tailnet>
for h in $N; do for t in $N; do [ "$h" = "$t" ] && continue
  if [ "$h" = ahnoway ]; then r=$(ping -c 2 -W 2 $t.$T.ts.net >/dev/null && echo ok || echo FAIL)
  else r=$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$h" "ping -c 2 -W 2 $t.$T.ts.net >/dev/null && echo ok || echo FAIL" 2>/dev/null || echo SSH-FAIL); fi
  echo "$h -> $t: $r"; done; done
```
(Use the hub's unattended alias in place of the hostname for `ssh` if the MagicDNS ssh path was not chosen.) Expected: six `ok` lines.

- [ ] **Step 2 (`executor: Opus`): Throwaway tailnet-bound listener on the hub, curl from both peers, then kill**

```bash
ssh <solarplexus alias> 'HIP=$(tailscale ip -4); mkdir -p ~/corvid-p0 && cd ~/corvid-p0 && echo ok > index.html && systemd-run --user --scope -p CPUQuota=40% -p MemoryMax=1.6G nice -n 19 timeout 60 python3 -m http.server --bind "$HIP" 8099 >/dev/null 2>&1 & sleep 2; ss -tln | grep -c ":8099"'
curl -s -o /dev/null -w 'ahnoway -> hub: %{http_code}\n' http://solarplexus.<tailnet>.ts.net:8099/
ssh -o BatchMode=yes optiplex "curl -s -o /dev/null -w 'optiplex -> hub: %{http_code}\n' http://solarplexus.<tailnet>.ts.net:8099/"
sleep 60; ssh <solarplexus alias> 'pkill -f "http.server --bind" ; rm -rf ~/corvid-p0; ss -tln | grep -c ":8099"'
```
Expected: `1` (listening), two `200` lines, then `0` (closed, scratch removed). The listener is bound to the tailnet IP — the repo's Bash guard would block `0.0.0.0`; this is the allowed form.

- [ ] **Step 3 (`executor: founder`): Cross-house name-ping (ADR-0004 §1(b))** — handoff block:

> **Founder:** call the friend whose machine is shared into (or invited to) the tailnet and ask them to turn it on with Tailscale running. Reply with the device's name as `tailscale status` shows it.

- [ ] **Step 4 (`executor: Opus`): Ping it**

```bash
ping -c 3 -W 3 <friend-device-name-from-tailscale-status> | tail -2
```
Expected: replies (record date/time + "direct/relay" from `tailscale ping -c 1 <name>`). If the device is offline after two tries on different days, record "across houses: pending" per ADR-0004.

- [ ] **Step 5 (`executor: Opus`): Acceptance checklist + sanitise + propose the status line**

```bash
for n in ahnoway; do tailscale dns status | head -1; done; ssh <solarplexus alias> 'tailscale dns status | head -1'; ssh optiplex 'tailscale dns status | head -1'
tailscale version | head -1; ssh <solarplexus alias> 'tailscale version | head -1'; ssh optiplex 'tailscale version | head -1'
grep -nE '192\.168\.|@|id_[a-z]|/home/' docs/runs/phase-0-$D.md || echo "run file sanitised"
```
Expected: three `Tailscale DNS: enabled.`; three versions ≥ 1.102; `run file sanitised`. Append to the run file the proposed line: `Phase 0 — mechanics: done <date> (all-pairs MagicDNS, hub kernel-mode + dial, DNS on all, key expiry off, unattended path = <transport>); across houses: <done <date> | pending>` and commit: `docs(runs): Phase 0 verification — acceptance <n>/9 passed` (+ trailer). Push the branch: `git push -u origin phase-0-handshake`. **Stop.** The main session merges, updates `docs/status.md`, and marks CLAUDE.md §6 when ADR-0004's criteria are met.

---

## Self-review record (writing-plans checklist, 2026-08-22)

1. **Spec coverage:** §4 step 0 → Task 1; step 1 → Task 3; step 2 → Task 2; step 3 → Task 4; step 4 → Task 5; step 5 → Task 6; step 6 → Task 7; step 7 + §7 acceptance → Task 8; §6 error handling → Task 2 Steps 2/5 (rollback), Task 3 undo lines, Task 1 fallback.
2. **Placeholders:** none of the three forbidden tokens; `<…>` items are runtime inputs named in Global Constraints.
3. **Consistency:** `splx-root`, `optiplex`, `<solarplexus alias>` as in `remote-step`; ports 8090–8093 as ADR-0003; rollback sequence identical to R00; listener cap = Appendix B solarplexus row.
