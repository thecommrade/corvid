# R00 — Phase 0 facts

- **Depth:** full (spec §6.1)
- **Written:** 2026-08-22 by main-session · **Verified:** 2026-08-22 (adversarial pass: no — inspection facts are direct observations; doc facts quote primary sources)
- **Feeds:** Phase 0 spec + plan (package spec §5), ADR-0002 (membership), ADR-0003 (endpoints), ADR-0004 (exit criteria), S-01/S-05 prerequisites

## Purpose

Everything the Phase 0 plan needs so an Opus session can execute it with no hidden context: the current DNS / tailscaled / routing / Tailscale-SSH state of the three build nodes, the verified kernel-mode switch + rollback sequence for solarplexus, ports in use on the hub (for ADR-0003), and the dated Tailscale documentation facts behind each step. Addresses use placeholders (spec §3.8); concrete values are in the founder's private notes.

## Facts

### Observed on the fleet (source: `../runs/R00-inspection-2026-08-22.md`)

| ID | Statement | Source (URL) | Date verified | Version/commit | Status |
|---|---|---|---|---|---|
| R00-F1 | **ahnoway** runs Tailscale 1.102.3 in kernel mode (`tailscale0`, packaged ExecStart, `FLAGS=""`), `RunSSH=false`, **Tailscale DNS disabled** (`CorpDNS=false`); its ip rules place Tailscale's 5210–5270 before the VPN app's 30780/30781, and `tailscale netcheck` shows the home WAN as IPv4 endpoint while `curl` egresses via the VPN → Tailscale bypasses the VPN in kernel mode here. | run file | 2026-08-22 | tailscale 1.102.3 | verified |
| R00-F2 | **solarplexus** runs Tailscale 1.98.4 in **userspace-networking mode**, set by the drop-in `/etc/systemd/system/tailscaled.service.d/override.conf` (`ExecStart=… --port=0 --tun=userspace-networking`, file dated Feb 24); `/etc/default/tailscaled` still says `PORT="41641"`, `FLAGS=""`; there is no `tailscale0`; `RunSSH=true`; `CorpDNS=false`. A native TCP dial to a peer's tailnet IP **fails** (no OS route); `tailscale netcheck` is healthy (UDP true, home-WAN IPv4, nearest DERP NYC) — the `Relay: fra` in `status --self` is stale. | run file | 2026-08-22 | tailscale 1.98.4 | verified |
| R00-F3 | **solarplexus routing:** rules `10 to <lan-subnet> → main`, `10 to <docker-net> → main`, `100 from <docker-net> → <vpn-table>`, `32764 main suppress_prefixlength 0`, `32765 not fwmark <vpn-mark> → <vpn-table>`; table `<vpn-table>` = `default dev <vpn-if>`; main default via `<lan-gw>` on `<wifi-if>`. In kernel mode tailscaled inserts rules at 5210/5230/5250 (fwmark 0x80000 → main/default/unreachable) and 5270 (→ table 52), i.e. **before** 32764/32765 — the same ordering that bypasses the VPN on ahnoway — so no extra routing config is expected; Phase 0 step 2 must still verify it (netcheck + direct path + dial test). | run file | 2026-08-22 | — | verified (observation); bypass-after-switch is a prediction → test |
| R00-F4 | **optiplex** runs Tailscale 1.102.3 in kernel mode, `RunSSH=true`, `CorpDNS=true`; systemd-resolved shows `tailscale0` with DNS `100.100.100.100` and **DNS Domain = `tail2990fc.ts.net`** (split DNS) while the VPN link keeps the default route `~.` — i.e. MagicDNS coexists with a full-tunnel VPN's DNS. Its VPN rules sit at 5208/5209 (*before* Tailscale's), yet `netcheck` shows the home WAN as IPv4 endpoint → Tailscale bypasses the VPN in practice; the exact rule interplay needs the root-only `wg show` reads. | run file | 2026-08-22 | tailscale 1.102.3 | verified (observation); mechanism UNVERIFIED |
| R00-F5 | DNS per node: ahnoway — the VPN app link holds the default DNS (`~.` → `<vpn-dns>`), `tailscale0` has none; solarplexus — Wi-Fi link DNS = the Pi-hole + 8.8.8.8, `/etc/resolv.conf` is the resolved stub; optiplex — as F4 (VPN DNS default, Tailscale split domain). | run file | 2026-08-22 | — | verified |
| R00-F6 | Tailscale SSH is on (`RunSSH=true`) on both hubs and OpenSSH listens on `<lan-ip>:22` and `<tailnet-ip>:22` on both; per R00-D6 the tailnet `:22` is claimed by Tailscale SSH, which explains the earlier observation that non-interactive ssh to the hubs' tailnet IPs stalls (check-mode prompt). ahnoway's `0.0.0.0:22` sshd is a pre-existing, restricted notify-only service, not CORVID's. | run file | 2026-08-22 | — | verified |
| R00-F7 | **Ports listening on solarplexus:** 22 53 139 445 631 1492 2019 2283 4533 5055 5109 6767 6789 6881 7474 7878 **8080** 8191 8265 8266 8686 8989 9696 23959 32400 32401 32469 32600 34254 54774 → **8090–8093 are free** (ADR-0003 candidates). optiplex: 22 53 5432 8000 8100 8501 8503 8600 8700 20241 (+ephemeral). ahnoway: 22 53 631 1716 5432 6463 (+ephemeral). | run file | 2026-08-22 | — | verified |
| R00-F8 | Linger: ahnoway yes; **solarplexus no** (Phase 1 user units there need `loginctl enable-linger <user>`, `executor: Opus (splx-root)`); optiplex yes. | run file | 2026-08-22 | — | verified |
| R00-F9 | Versions: Python 3.14.7 / 3.12.3 / 3.12.3; Docker 29.7.2 / 29.1.3 / 29.1.3; systemd 261 / 255 / 255 (ahnoway / solarplexus / optiplex). GPU drivers: 610.57.04 (RTX 2070 Super, cc 7.5), 535.309.01 (GTX 970, cc 5.2), 590.48.01 (RTX 3050, cc 8.6). | run file | 2026-08-22 | — | verified |
| R00-F10 | Both hubs have their wired NIC unplugged (`NO-CARRIER`) and run on Wi-Fi (house-showing period); MagicDNS is enabled tailnet-wide with suffix `tail2990fc.ts.net`. | run file | 2026-08-22 | — | verified |

### Documentation (primary sources, fetched 2026-08-22)

| ID | Statement | Source (URL) | Date verified | Version/commit | Status |
|---|---|---|---|---|---|
| R00-D1 | "By default, devices in your tailnet prefer their local DNS settings and only use the tailnet's DNS servers when needed." "Override DNS servers": "When enabled, devices … ignore their local DNS settings and always use the global nameservers defined for the tailnet." | https://tailscale.com/kb/1054/dns | 2026-08-22 | page validated 2025-12-22 | verified |
| R00-D2 | "A restricted nameserver only applies to DNS queries matching a specific search domain. Using a restricted nameserver is also known as split DNS." | https://tailscale.com/kb/1054/dns | 2026-08-22 | page validated 2025-12-22 | verified |
| R00-D3 | `--accept-dns`: "Accept DNS configuration from the admin console. Defaults to accepting DNS settings." On Linux, stop with `tailscale set --accept-dns=false`; MagicDNS "does not require a DNS nameserver if running Tailscale v1.20 or later". | https://tailscale.com/kb/1080/cli ; https://tailscale.com/kb/1081/magicdns | 2026-08-22 | CLI page validated 2026-07-30; MagicDNS page 2026-01-05 | verified |
| R00-D4 | `tailscale set --operator=<user>`: "A Unix username other than root to operate tailscaled." | https://tailscale.com/kb/1080/cli | 2026-08-22 | validated 2026-07-30 | verified |
| R00-D5 | Userspace networking (`--tun=userspace-networking`) is for environments without `/dev/net/tun`; outbound from other programs to tailnet IPs is not routed — "tailscaled functions as a SOCKS5 or HTTP proxy which other processes … can connect through" (`--socks5-server`, `--outbound-http-proxy-listen`, `ALL_PROXY`/`HTTP_PROXY`). | https://tailscale.com/kb/1112/userspace-networking | 2026-08-22 | validated 2025-11-12 | verified |
| R00-D6 | Tailscale SSH authenticates with tailnet identity (node keys), "claims port 22 for the Tailscale IP address"; ssh rules have `action` `accept` or `check`; check mode re-auth is cached "for the next 12 hours, or a specified check period" (1 min–168 h); default policy (no custom rules): users may "access their own devices using check mode, as either root or non-root"; root allowed by listing `root` in `users`; non-Tailscale SSH connections unaffected. | https://tailscale.com/kb/1193/tailscale-ssh | 2026-08-22 | validated 2026-01-05 | verified |
| R00-D7 | Key expiry: "By default, new domains are set with an expiry period of 180 days." On expiry "connections to/from the given endpoint will stop working." Disable per device: admin console → Machines → device menu → "Disable Key Expiry". | https://tailscale.com/kb/1028/key-expiry | 2026-08-22 | validated 2026-01-05 | verified |
| R00-D8 | Node sharing is one-directional: "Shared machines are quarantined by default. They can respond to incoming connections from the tailnet they're shared to, but cannot start connections on their own." A shared machine is visible only to the recipient user; the recipient does not become a member of the sharer's tailnet; shared users are addressable via `autogroup:shared`; "Sharing is available for all plans." | https://tailscale.com/kb/1084/sharing | 2026-08-22 | validated 2026-01-05 | verified |
| R00-D9 | Personal plan: "Up to 6 users", "Unlimited user devices", free indefinitely; next tier Standard "$8 per user, per month", unlimited users. | https://tailscale.com/pricing | 2026-08-22 | no date on page | verified |
| R00-D10 | Other VPNs: "Most VPNs set aggressive firewall rules … This can result in the other VPN dropping all Tailscale traffic"; CGNAT-range IP conflicts; suggested workarounds are userspace networking (SOCKS5) or split-tunnel DNS. (Likely why solarplexus was put in userspace mode; F1/F4 show kernel mode coexisting with this VPN on the other two nodes.) | https://tailscale.com/kb/1105/other-vpns | 2026-08-22 | validated 2026-01-12 | verified |
| R00-D11 | `tailscale serve` injects `Tailscale-User-Login`, `Tailscale-User-Name`, `Tailscale-User-Profile-Pic` into proxied requests; "Tailscale Serve requires you to enable HTTPS certificates in your tailnet." Whether a plain `--http=<port>` frontend is supported is not stated on the page. | https://tailscale.com/kb/1312/serve | 2026-08-22 | updated 2026-01-20 | verified; `--http` UNVERIFIED → S-05 |
| R00-D12 | Default ACL: "When you first create your tailnet, the default tailnet policy file enables communication between all devices within the tailnet"; with no `acls` section the default allow-all applies. The `ssh` section syntax was not on the fetched page. | https://tailscale.com/kb/1018/acls | 2026-08-22 | validated 2026-01-05 | verified; ssh-section syntax UNVERIFIED (founder pastes the live policy) |

## Kernel-mode switch + rollback for solarplexus (Phase 0 step 2)

`executor: Opus (splx-root)` issuing commands into a root shell the founder is watching (console or `tmux`); precondition: Plex/Immich idle; time box 20 min. Do this **before** enabling Tailscale DNS on solarplexus (step 1), because DNS is configured per link and userspace mode has no `tailscale0` link.

```bash
# 0) snapshot + armed auto-rollback (fires in 10 min unless disarmed)
cp /etc/systemd/system/tailscaled.service.d/override.conf /root/tailscaled-override.conf.bak
systemd-run --on-active=10m --unit=corvid-ts-rollback bash -c 'cp /root/tailscaled-override.conf.bak /etc/systemd/system/tailscaled.service.d/override.conf && systemctl daemon-reload && systemctl restart tailscaled'
# 1) remove the userspace drop-in → packaged ExecStart (PORT=41641, FLAGS="" from /etc/default/tailscaled)
rm /etc/systemd/system/tailscaled.service.d/override.conf
systemctl daemon-reload && systemctl restart tailscaled && sleep 5
# 2) verify kernel mode, rules, bypass, reachability
tailscale status --self --json | python3 -c 'import json,sys; s=json.load(sys.stdin)["Self"]; print("Online", s["Online"])'   # True
ip -br link show tailscale0                                  # present, UP
ip rule | grep -E '^(5210|5230|5250|5270):'                  # four tailscale rules, all before 32764/32765
tailscale netcheck | grep -E 'UDP|IPv4'                      # UDP: true; IPv4 = home WAN (not the VPN egress shown by: curl -s https://api.ipify.org)
tailscale ping <optiplex-magicdns-name>                      # pong, direct
timeout 6 bash -c 'cat </dev/null >/dev/tcp/<optiplex-tailnet-ip>/22' && echo dial-ok   # native dial now works
# 3) disarm the auto-rollback
systemctl stop corvid-ts-rollback.timer 2>/dev/null; systemctl stop corvid-ts-rollback.service 2>/dev/null
# rollback (manual, any time): cp /root/tailscaled-override.conf.bak /etc/systemd/system/tailscaled.service.d/override.conf && systemctl daemon-reload && systemctl restart tailscaled
```
Also upgrade Tailscale on solarplexus to current (1.98.4 → ≥ 1.102) in the same window (`executor: Opus (splx-root)`, apt), and re-run the verification block.

## Recommendations for the spec

1. Phase 0 order on solarplexus: step 0 (access path) → step 2 (kernel mode + upgrade) → step 1 (DNS) → rest; on ahnoway step 1 needs operator mode (`sudo tailscale set --operator=$USER`, founder) or sudo.
2. Unattended access path (step 0): Tailscale SSH with `action: accept` for the founder's own devices is the cleanest (R00-D6; works away from home; can grant root on solarplexus by ACL) — decide after the founder pastes the live `ssh` policy; until then OpenSSH over LAN/`splx-root` remains the path.
3. ADR-0003: reserve 8090–8093 on solarplexus (R00-F7).
4. Phase 1 plan: `loginctl enable-linger` on solarplexus (R00-F8).
5. ADR-0002: invite members as users (R00-D8/D9: sharing is one-directional and the recipient is not a member; Personal plan = 6 users).

## Open questions

- Root-only reads on both hubs (`wg show` fwmark/table; conf lines `Table/FwMark/PostUp/PostDown`) to explain R00-F4's bypass — `executor: founder` on optiplex, `Opus (splx-root)` on solarplexus.
- The live tailnet policy `ssh` section and DNS page state (global nameservers? HTTPS certs enabled?) — founder paste.
- Does Tailscale DNS (`--accept-dns=true`) on ahnoway coexist with the Proton app's `~.` default DNS without the app re-asserting? (Phase 0 step 1 verifies; fallback `--accept-dns=false`.)
- `tailscale serve --http=<port>` support (S-05).

## CLAUDE.md §4 credit rows to add

| Name | What we take | License | Author |
|---|---|---|---|
| (none — Tailscale is already credited in §4) | | | |

## Change log

- 2026-08-22 — created from the inspection run and nine Tailscale KB pages.
