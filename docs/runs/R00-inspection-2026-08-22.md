# R00 inspection run — 2026-08-22 (sanitised)

Read-only inspection of the three build nodes with `docs/runs/raw/inspect.sh` (raw logs in `docs/runs/raw/`, git-ignored). Addresses replaced by placeholders per spec §3.8. Executor: main-session.

| Item | ahnoway | solarplexus | optiplex |
|---|---|---|---|
| Tailscale version | 1.102.3 | 1.98.4 | 1.102.3 |
| tailscaled mode | kernel (`tailscale0` present; packaged ExecStart, `FLAGS=""`) | **userspace** — drop-in `/etc/systemd/system/tailscaled.service.d/override.conf` (dated Feb 24) sets `ExecStart=… --port=0 --tun=userspace-networking`; no `tailscale0`; `/etc/default/tailscaled` = `PORT="41641"`, `FLAGS=""` | kernel (`tailscale0` present; packaged ExecStart) |
| BackendState / Online | Running / true | Running / true | Running / true |
| RunSSH (Tailscale SSH) | false | **true** | **true** |
| CorpDNS (accept-dns) | **false** | **false** | true |
| MagicDNS tailnet-wide | enabled (suffix `tail2990fc.ts.net`); ts.net → Tailscale resolvers; search domain set | same | same |
| Netfilter mode | 2 (on) | 2 | 2 |
| systemd-resolved links | VPN app link `proton0` holds default DNS (`~.`) → `<vpn-dns>`; `tailscale0` has no DNS config; Wi-Fi/Ethernet links no DNS | Wi-Fi link DNS = `<pi-hole>` + `8.8.8.8` (default route link); `/etc/resolv.conf` → stub 127.0.0.53 | `tailscale0` link: DNS `100.100.100.100`, **DNS Domain = `tail2990fc.ts.net` (split DNS)**; `protonvpn` link: `<vpn-dns>` with `~.` (default); Ethernet (down) link lists public resolvers |
| ip rules (priority → action) | 0 local; **5210/5230/5250 tailscale fwmark 0x80000 → main/default/unreachable; 5270 → table 52**; 30780 main suppress_prefixlength 0; 30781 not fwmark `<vpn-app-mark>` → `<vpn-app-table>`; 32766 main | 0 local; 10 to `<lan-subnet>` → main; 10 to `<docker-net>` → main; 100 from `<docker-net>` → table `<vpn-table>`; 32764 main suppress_prefixlength 0; 32765 not fwmark `<vpn-mark>` → `<vpn-table>`; 32766 main (no tailscale rules — userspace mode) | 0 local; **5208 main suppress_prefixlength 0; 5209 not fwmark `<vpn-mark>` → `<vpn-table>`** (VPN rules placed *before* tailscale's); 5210/5230/5250 tailscale; 5270 → table 52; 32766 main |
| table `<vpn-table>` | n/a (app-managed) | `default dev <vpn-if> scope link` | `default dev <vpn-if> scope link` |
| table 52 (tailscale) | peers + 100.100.100.100 via tailscale0 | none | peers + 100.100.100.100 via tailscale0 |
| main default route | via `<vpn-app>` (app) | via `<lan-gw>` dev `<wifi-if>` | via `<lan-gw>` dev `<wifi-if>` |
| Wired NIC | n/a (laptop) | `enp3s0` NO-CARRIER (unplugged) | `eno1` NO-CARRIER (unplugged) |
| VPN | Proton app (`proton0`, `ipv6leakintrf0`) | wg-quick `protonvpn` (full tunnel via rules above) | wg-quick `protonvpn` |
| sshd listeners (:22) | `0.0.0.0:22` (pre-existing, notify-only sshd — not CORVID's) | `<lan-ip>:22` and `<tailnet-ip>:22` (tailnet :22 is claimed by Tailscale SSH) | `<lan-ip>:22` and `<tailnet-ip>:22` |
| Native dial to a tailnet IP | works | **fails** (`/dev/tcp/<peer-tailnet-ip>/22` → no route) | works |
| `tailscale netcheck` | UDP true; IPv4 = home WAN (not VPN egress); nearest DERP Ashburn/NYC | UDP true; IPv4 = home WAN; nearest DERP NYC; `Relay` field stale `fra` | UDP true; IPv4 = home WAN; nearest DERP NYC |
| `curl api.ipify.org` | VPN egress IP | VPN egress IP | VPN egress IP |
| TCP ports listening | 22 53 631 1716 5432 6463 + ephemeral | 22 53 139 445 631 1492 2019 2283 4533 5055 5109 6767 6789 6881 7474 7878 **8080** 8191 8265 8266 8686 8989 9696 23959 32400 32401 32469 32600 34254 54774 | 22 53 5432 8000 8100 8501 8503 8600 8700 20241 + ephemeral |
| Linger | yes | **no** | yes |
| Python / Docker / systemd | 3.14.7 / 29.7.2 / 261 | 3.12.3 / 29.1.3 / 255 | 3.12.3 / 29.1.3 / 255 |
| GPU (driver, cc) | RTX 2070 Super 8 GB (610.57.04, 7.5) | GTX 970 4 GB (535.309.01, 5.2) | RTX 3050 6 GB (590.48.01, 8.6) |

Pending (founder): root-only `wg show`/conf-line reads on both hubs; admin-console ACL `ssh` section + DNS page state.
