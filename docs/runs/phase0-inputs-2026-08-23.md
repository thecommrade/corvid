# Phase 0 inputs — collected 2026-08-23 (main session + founder)

Sanitised: no usernames, keys, LAN/public IPs; tailnet name → `<tailnet>`; founder login →
`<founder-login>`. Gathered ahead of the Phase 0 dispatch so the executing session starts with
its founder-input steps pre-satisfied (verify, don't redo).

## 1. Live tailnet policy (read from the compiled netmap on ahnoway, operator mode)

- **PacketFilter: default allow-all.** One rule — srcs = every tailnet device (5 devices),
  dsts = `<node>/32` all ports, protocols TCP/UDP/ICMP/ICMPv6. No tags, no restrictions.
  Consequence: none of the connectivity failures found today are ACL-caused; the ADR-0002
  baseline (tag:hub / tag:member, member↔member deny) is still a pre-first-member founder
  edit, not a Phase 0 blocker.
- **SSHPolicy: check mode for everyone.** One rule — principals = all devices; sshUsers
  `*→=`, `root→root`; action `holdAndDelegate` (interactive admin approval per session).
  Confirms R00's "Tailscale SSH stalls unattended ssh on tailnet IPs". Phase 0 Task 1's
  policy edit (accept for the founder's own devices) stands as written.

## 2. DNS state (admin page + `tailscale dns status` on all three build nodes)

- MagicDNS **enabled tailnet-wide**; suffix `<tailnet>.ts.net`; search domain = tailnet
  domain; split-DNS only the built-in `ts.net.` routes; **no global nameservers** (clients
  keep system DNS → Pi-hole/router unaffected); HTTPS certificates feature not enabled.
- Per-node `accept-dns`: optiplex ON; **ahnoway was OFF → enabled 2026-08-23** (operator,
  no sudo), verified: tailnet names and public names both resolve; **solarplexus OFF —
  deliberately deferred**: in userspace mode there is no route to `100.100.100.100`, so
  enabling accept-dns there risks breaking the hub's DNS. Order: kernel-mode switch first,
  then `tailscale set --accept-dns=true` (Phase 0 plan ordering note).

## 3. Routing reads (root on both hubs; founder ran the optiplex one)

- **solarplexus** (`wg show` + `ip rule` via splx-root): Proton WireGuard `protonvpn`,
  fwmark `0xca6c`, allowed-ips `0.0.0.0/0`; wg-quick-style rules at **32764/32765**
  (`lookup main suppress_prefixlength 0`; `not fwmark 0xca6c lookup 51820`); LAN /24 bypass
  rules at pref 10; **no 100.64.0.0/10 bypass**; no Tailscale rules (userspace mode — no
  tailscale0). Kernel-mode switch will install Tailscale's rules at pref 52xx — ABOVE
  Proton's 327xx — so no extra bypass rule should be needed there.
- **optiplex** (`wg show` founder; `ip rule`/tables unprivileged): Proton `protonvpn`,
  fwmark `0xca6c`, allowed-ips `0.0.0.0/0, ::/0`; Proton's rules renumbered to **5208/5209 —
  ABOVE Tailscale's 5210/5270**; table 51820 = `default dev protonvpn`; table 52 holds the
  per-peer `100.x/32 dev tailscale0` routes but is never consulted for locally-initiated
  traffic. See finding F below.

## 4. Today's fixes already applied (verify on dispatch, don't redo)

- ahnoway: operator mode set (`tailscale set --operator=<user>`); `tailscale0` in firewalld
  **trusted** zone (permanent; the `--reload` runtime-wipe gotcha is recorded in
  `docs/runs/S-05-2026-08-23.md`); `accept-dns=true`; MagicDNS name-ping ahnoway→hub works.
- optiplex: ufw `allow in on tailscale0 from 100.64.0.0/10 to any port 50052 proto tcp`
  (founder); iperf3 installed (founder, prompted).
- Firewalld ports 50052+5201/tcp were also added to the zone previously bound to tailscale0
  — now redundant (trusted zone covers it); safe to remove at leisure.

## F. New Phase 0 finding — the broken pair (full narrative in S-05 run file, finding 5)

optiplex cannot **dial** any tailnet IP (Proton rule 5209 swallows unmarked 100.x traffic
before table 52; Tailscale's rules there are dead code) and shows ahnoway only via DERP;
ahnoway additionally is suspected to block **inbound UDP 41641** on its Wi-Fi zone, so no
peer establishes inbound direct paths to it. Candidate fixes (adversarial verification in
flight; fold verdicts before executing):
- ahnoway: open `41641/udp` in the wlan zone (runtime + permanent, no reload).
- optiplex (founder, root): `ip rule add to 100.64.0.0/10 lookup 52 pref 5205` —
  non-persistent test first; persistence mechanism is a Phase 0 plan decision.

## Pre-satisfied Phase 0 founder steps (map for the executing session)

| Plan step | State |
|---|---|
| Paste policy `ssh` section + DNS page | satisfied by §1–§2 (netmap + dns status, better than a paste) |
| Root-only routing reads on both hubs | satisfied by §3 |
| One-time operator mode on ahnoway | done 2026-08-23 |
| ssh policy edit to `accept` | **still open** (founder, Task 1) |
| Kernel-mode switch on solarplexus | **still open** (founder-present step) |
| Key-expiry disable check | **still open** |
