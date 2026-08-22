# Phase 0 — The Handshake: Design Spec

- **Date:** 2026-08-22
- **Status:** Ready for execution (scope approved as package spec §5 on 2026-08-22; this document fills it in from R00 and ADR-0002/0003/0004)
- **Author:** main-session (Fable) with the founder · **Executor of the plan:** Opus session + founder steps
- **Related:** `CLAUDE.md` §3.1, §5.6, §6 (Phase 0), §8; package spec `2026-08-22-corvid-research-and-planning-design.md` §5, Appendix A/B; `docs/research/R00-phase0-facts.md`; ADR-0002 (membership), ADR-0003 (endpoints, Proposed), ADR-0004 (exit criteria)
- **Notation:** R00-Fn / R00-Dn = facts in R00; "§N" = this spec; "CLAUDE.md §N" = the charter.

## 1. Goal and exit criterion

Finish the handshake: every build node reaches every other by MagicDNS name over the tailnet, the hub can *dial* workers, nothing silently expires, unattended automation has a documented path, and the endpoint/port plan is reserved — so Phase 1 can start without touching the mesh again.

**Exit (ADR-0004 §1):** (a) ahnoway, solarplexus, optiplex name-ping each other in all six ordered pairs over the tailnet; **and** (b) at least one cross-house name-ping from a build node to a friend's device succeeds (Zach's shared node while online, or an invited member's device). (b) is an `executor: founder` phone-call step. Status.md records both halves.

## 2. Current state (R00, 2026-08-22)

| | ahnoway | solarplexus | optiplex |
|---|---|---|---|
| Tailscale | 1.102.3, kernel mode, DNS **off**, SSH off | **1.98.4, userspace mode** (drop-in `override.conf`), DNS **off**, Tailscale SSH on | 1.102.3, kernel mode, DNS on (split DNS working), Tailscale SSH on |
| Can dial tailnet IPs natively | yes | **no** (R00-F2) | yes |
| VPN | Proton app; Tailscale rules precede it; bypass observed | wg-quick full tunnel; Tailscale rules would precede it once kernel-mode (R00-F3, prediction) | wg-quick; bypass observed (R00-F4) |
| Linger | yes | **no** | yes |
| Key expiry | default 180 d (R00-D7) on all three — founder to disable | | |
| Unattended ssh | local | user-level via the documented alias; root via `splx-root` after the founder loads the agent key; **tailnet-IP :22 = Tailscale SSH (check mode → stalls non-interactively)** | user-level via `ssh optiplex` (works); root = founder |

## 3. Target state (after Phase 0)

- All three nodes: kernel-mode Tailscale ≥ 1.102, Tailscale DNS **on** (`*.<tailnet>.ts.net` via `100.100.100.100`, everything else via each node's existing resolver — R00-D1, observed on optiplex R00-F4), key expiry **disabled** (R00-D7), name-ping all pairs.
- solarplexus: `tailscale0` present; native dial to tailnet IPs works; VPN bypass verified (netcheck WAN vs curl VPN egress); linger enabled for the service user (Phase 1 needs it; doing it here avoids a second root window).
- Unattended access path recorded in `remote-step` and `status.md` (§4 step 0).
- ADR-0002 Accepted (done), ADR-0003 Proposed with ports 8090–8093 confirmed free on the hub (R00-F7), ADR-0004 Accepted (done).
- One cross-house name-ping recorded.

## 4. Components — the steps (package spec §5, filled in)

Each step names executor, inputs, verification, undo. Order on **solarplexus: 0 → 2 → 1 → rest** (DNS needs the `tailscale0` link, R00 recommendation 1).

**Step 0 — Unattended access path** (`executor: founder` for the policy edit; `main-session`/`Opus` verify).
*Decision (recommended):* Tailscale SSH with `action: accept` for the **founder's own devices only**, users `autogroup:nonroot` + `root` on solarplexus (so `Opus (splx-root)` steps can run unattended over the tailnet, at home or away), `autogroup:nonroot` only on optiplex (root there stays the founder's). Policy snippet (placeholder for the founder's login; syntax to be confirmed against the live policy the founder pastes — R00-D12 open question):

```jsonc
"ssh": [
  // founder's own devices: no browser check for automation
  { "action": "accept", "src": ["<founder-login>"], "dst": ["autogroup:self"], "users": ["autogroup:nonroot", "root"] },
  // everyone else (future members): default check mode to their own devices
  { "action": "check", "src": ["autogroup:member"], "dst": ["autogroup:self"], "users": ["autogroup:nonroot", "root"] }
]
```
*Fallback:* keep OpenSSH over LAN (user-level via the documented alias, root via `splx-root` after `ssh-add`) and add DHCP reservations for both hubs (`executor: founder`, router) — works today, not away from home.
*Verification:* from ahnoway, `ssh -o BatchMode=yes <alias> true` for the chosen transport to both hubs (and `root@<solarplexus-magicdns>` if Tailscale-SSH root was granted) → exit 0 within 5 s. *Undo:* revert the policy edit / remove reservations.

**Step 1 — Tailscale DNS on ahnoway and solarplexus** (`executor: Opus` — on ahnoway after the one-time `sudo tailscale set --operator=$USER` (`executor: founder`, R00-D4); on solarplexus `Opus (splx-root)` after step 2). Command: `tailscale set --accept-dns=true`. Expected mechanism (R00-D1/D3, observed R00-F4): resolved gets a `tailscale0` link entry DNS `100.100.100.100`, DNS Domain `<tailnet>.ts.net`; the existing default resolver (Proton app DNS on ahnoway, Pi-hole on solarplexus) stays. *Verification:* `tailscale dns status | head -3` → `Tailscale DNS: enabled.`; `resolvectl status tailscale0 | grep -E 'DNS Servers|DNS Domain'`; `resolvectl query optiplex.<tailnet>.ts.net` → the peer's tailnet IP; `resolvectl query <any public name>` still answers via the old resolver. *Undo:* `tailscale set --accept-dns=false`. *Risk:* the Proton app on ahnoway re-asserting `~.` — harmless to split-DNS; if MagicDNS answers vanish, undo and file an open question.

**Step 2 — solarplexus: userspace → kernel mode + upgrade** (`executor: Opus (splx-root)` with **founder present** at a console or a root `tmux` that Opus issues commands into; precondition Plex/Immich idle; armed 10-minute auto-rollback). Sequence = R00 "Kernel-mode switch + rollback" verbatim (snapshot `override.conf` → `systemd-run --on-active=10m` rollback → remove drop-in → `daemon-reload` + restart → verify `tailscale0`, ip rules 5210–5270 before 32764/32765, `netcheck` IPv4 = WAN while `curl api.ipify.org` = VPN egress, `tailscale ping <optiplex>` direct, native `/dev/tcp` dial ok → disarm). Then `apt-get install --only-upgrade tailscale` (or the Tailscale repo's current package) and re-run the verification block. Also `loginctl enable-linger <service-user>` (R00-F8) in the same root window. *Undo:* restore `override.conf` + restart (manual) — or the armed rollback fires.

**Step 3 — Key expiry off** (`executor: founder`, admin console → Machines → each of ahnoway / solarplexus / optiplex → "Disable Key Expiry", R00-D7). *Verification:* `tailscale status --json | python3 -c 'import json,sys; d=json.load(sys.stdin); print({p["HostName"]: p.get("KeyExpiry") for p in [d["Self"], *d["Peer"].values()]})'` shows no expiry for the three nodes (founder may also paste the Machines page).

**Step 4 — Membership** = ADR-0002 (Accepted, done in M1). Phase 0 action: none required before the first member; the ACL baseline (tags, member↔member deny) is edited by the founder **before inviting the first member** (Phase 1 follow-on), not in Phase 0.

**Step 5 — SSH hygiene** (`executor: founder` for `~/.ssh/config` and `networkdocs`; `executor: main-session` for `remote-step`): aliases by MagicDNS name or Tailscale IP if step 0 chose Tailscale SSH, or by reserved LAN name/IP if OpenSSH; remove the stale alias; update `.claude/skills/remote-step/SKILL.md` to state the chosen transport (alias names only).

**Step 6 — Endpoints** = ADR-0003 (Proposed, done). Phase 0 action (`executor: Opus`): confirm 8090–8093 still free on the hub — `ss -tlnH | awk '{print $4}' | grep -E ':(8090|8091|8092|8093)$'` → no output; record in the run file. No service is started.

**Step 7 — Verification + cross-house** (`executor: Opus` for (a), `founder` for (b)): all-pairs name-ping block (package plan), a throwaway tailnet-bound listener on the hub curl'd from both peers, then (b) a phone-call script for the friend and `ping -c 3 <friend-device-magicdns-or-shared-name>` from ahnoway. Outputs → `docs/runs/phase-0-<date>.md`; one summary line proposed for `status.md`.

## 5. Data flow

- **Names:** `<node>.<tailnet>.ts.net` → resolved per-link route → `100.100.100.100` (tailscaled) → tailnet IP. Everything else → the node's pre-existing resolver (Proton DNS on ahnoway/optiplex, Pi-hole on solarplexus). No admin-console DNS change (R00-D1).
- **Packets:** tailnet IPs → table 52 → `tailscale0`; tailscaled's own UDP (fwmark 0x80000) → main → WAN, ahead of each VPN's catch-all rule; all other traffic → VPN as before.
- **Unattended ssh:** Opus on ahnoway → (Tailscale SSH over the tailnet, identity = the founder's) or (OpenSSH over LAN with the documented key) → hub shell; root on solarplexus only via the chosen root path; never root on optiplex.

## 6. Error handling and rollback

| Failure | Detection | Response |
|---|---|---|
| Step 2 loses the hub's tailnet connectivity or Plex/Immich | `tailscale status` not Online; founder watching | armed auto-rollback restores `override.conf` within 10 min; manual rollback line in R00; founder has console |
| Step 1 breaks local resolution (Pi-hole / VPN DNS) | `resolvectl query <public name>` fails | `tailscale set --accept-dns=false`; record; try `resolvectl` link inspection |
| Tailscale SSH `accept` policy typo locks out | `ssh -o BatchMode=yes` fails after edit | LAN/OpenSSH path still works; founder reverts policy in the console |
| Upgrade changes tailscaled flags | `systemctl cat tailscaled` differs from packaged | keep packaged ExecStart; `/etc/default/tailscaled` PORT/FLAGS as recorded |
| Cross-house device offline for days | ping fails | (b) stays pending; status.md shows "across houses: pending" (ADR-0004) |

## 7. Acceptance tests (the plan's final block)

1. All-pairs: for each ordered pair of the three nodes, `ping -c 2 -W 2 <peer>.<tailnet>.ts.net` → 0 % loss (run from each node via the chosen unattended path).
2. `tailscale dns status | head -1` → `Tailscale DNS: enabled.` on all three.
3. On solarplexus: `ip -br link show tailscale0` up; `tailscale netcheck | grep IPv4` shows the WAN endpoint; `curl -s https://api.ipify.org` still shows the VPN egress; native `/dev/tcp/<optiplex-tailnet-ip>/22` opens.
4. `tailscale version` ≥ 1.102 on all three.
5. Key expiry: founder confirms "Disable Key Expiry" on the three machines (paste or screenshot reference in the run file).
6. Unattended: `ssh -o BatchMode=yes <hub alias> true` → 0 for both hubs (+ root path on solarplexus).
7. Throwaway listener: on the hub `python3 -m http.server --bind <hub-tailnet-ip> 8099` (scope-wrapped, ≤ 60 s), `curl -s -o /dev/null -w '%{http_code}\n' http://solarplexus.<tailnet>.ts.net:8099/` from both peers → `200`; then killed; `ss -tln | grep -c ':8099'` → 0.
8. Cross-house: `ping -c 3 <friend device name>` from ahnoway → replies (recorded with date); or "pending" per ADR-0004.
9. `grep -c` of the run file for any of: usernames, key names, LAN/public IPs → 0 (sanitised).

## 8. Out of scope

llama.cpp (Phase 1), agent/coordinator (Phase 2), member guides (Phase 4), ACL baseline edit (before first member — Phase 1 follow-on), wiring the hubs (founder, after the move).

## 9. ADRs

ADR-0002 (Accepted), ADR-0003 (Proposed → Accepted in M3), ADR-0004 (Accepted). None new.
