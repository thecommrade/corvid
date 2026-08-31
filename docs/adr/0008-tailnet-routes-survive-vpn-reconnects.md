# ADR-0008 — Tailnet routes survive VPN reconnects

- **Status:** Accepted
- **Date:** 2026-08-31
- **Deciders:** founder
- **Related:** CLAUDE.md §2 (zero open ports; all traffic rides the mesh), §3.1 · ADR-0004
  (exit criteria) · `docs/runs/phase-0-2026-08-23.md` (F2 discovery + netns experiment) ·
  `docs/runs/S-04-2026-08-31.md` (the reboot that proved the need) · status.md finding 13

## Context

Both hubs run a commercial VPN as a wg-quick full tunnel (`protonvpn.conf`). wg-quick
installs policy-routing rules that send *everything* into the tunnel table. Tailnet traffic
must bypass that, or CORVID's own mesh breaks on the machines that host it.

Facts this decision rests on:

- **The fix itself** (Phase 0, 2026-08-23, "F2"): two ip rules per hub, matching the tailnet
  ranges and pointing at the Tailscale table, ranked above the VPN's rules —
  `to 100.64.0.0/10 lookup 52 pref 5205` and `to fd7a:115c:a1e0::/48 lookup 52 pref 5205`.
  Both are public well-known ranges (RFC 6598 CGNAT space and Tailscale's ULA prefix).
- **Runtime rules do not survive** (2026-08-31): a reboot of the second node around Aug 26
  wiped both rules. The VPN's own rules were re-created at prefs 5208/5209; ours were gone.
  Plain `ping` across the tailnet to that node was **100% loss** until they were re-added by
  hand, at which point loss went to 0% at ~5 ms RTT.
- **A "winning" static preference does not exist** (netns experiment, 2026-08-23):
  wg-quick re-adds its rules at the kernel default preference, which is
  *lowest-existing minus one*, and that walk reaches pref 0. Any fixed number we choose can
  therefore be undercut on the next reconnect. Preference alone is not a defence.
- **The breakage is invisible to the obvious probes** (2026-08-31): `tailscale ping` and ssh
  to port 22 on a tailnet IP are serviced by tailscaled itself — disco packets carry a socket
  mark, and Tailscale SSH terminates in-process — so both keep working while ordinary traffic
  is black-holed. Only plain `ping` or a user-space TCP listener tells the truth.

## Decision

1. **Both hubs carry the guard in their wg-quick configuration**, not merely at runtime.
   Under `[Interface]` in each hub's `protonvpn.conf`:

   ```
   PostUp = ip rule add to 100.64.0.0/10 lookup 52 pref 5205 2>/dev/null || true; ip -6 rule add to fd7a:115c:a1e0::/48 lookup 52 pref 5205 2>/dev/null || true
   PreDown = ip rule del to 100.64.0.0/10 lookup 52 pref 5205 2>/dev/null || true; ip -6 rule del to fd7a:115c:a1e0::/48 lookup 52 pref 5205 2>/dev/null || true
   ```

   `PostUp` runs *after* wg-quick has installed its own rules, so the guard is re-asserted
   above them on every clean cycle. `PreDown` removes it so the pair stays idempotent and the
   next `PostUp` lands on a clean slate. Both lines are failure-tolerant: a duplicate add or a
   missing delete must never abort the tunnel.

2. **Preference 5205 is retained** across the fleet — for symmetry and legibility, explicitly
   *not* as the protection. The protection is the PostUp/PreDown pair.

3. **Reachability is verified with unmarked traffic only.** Any check that a node is reachable
   over the tailnet uses plain `ping` or a user-space TCP port. `tailscale ping`, `tailscale
   status` and ssh on port 22 are not evidence and must not be cited as such in a run file.

4. **A reboot is treated as a routing event.** After any hub reboot, the guard is verified
   before the node is used for CORVID work; `ip rule show` and `ip -6 rule show` must both
   list the pref-5205 entry.

## Consequences

- Tailnet reachability now survives the routine case: a clean VPN reconnect or a reboot that
  brings the tunnel up through wg-quick.
- **An unclean re-up is still a gap, and we accept it.** If the tunnel dies without `PreDown`
  running — a crash, a hard power loss — the stale guard can be left below the VPN's fresh
  rules until the next clean cycle. Recovery is the same two `ip rule add` lines by hand. We
  are choosing not to build a watchdog for a friends-scale fleet; if this bites more than
  once, a systemd path/timer unit that asserts the rules is the escalation.
- **The edits are inert until the next wg-quick cycle**, so applying them never disturbs a
  running tunnel — but it also means applying them proves nothing. The live test is a
  deliberate `systemctl restart wg-quick@<conf>` in a maintenance window.
- **Root, and therefore founder-gated on at least one hub.** The second node has no
  unattended root path for Claude; that edit is always a founder step.
- CORVID's guard covers the tailnet only. On the always-on hub, a VPN reconnect will also
  land the VPN's rules above that host's own LAN rule. Fixing that is the founder's
  infrastructure call, not CORVID's; the analogous `PostUp` line for the LAN subnet is
  recommended and deliberately left out of this ADR's scope.
- Every plan that brings a hub into a run must budget a verification step, because the guard
  can be absent for reasons no CORVID document will record — someone else's reboot.

## Implementation status (2026-08-31)

Decided and specified here; **not yet applied on either hub.** The founder holds the exact
lines (run file, "Founder handoff — pending"). Until they are applied, the runtime rules on
the second node are the only thing keeping it reachable, and the next reboot removes them.

## CLAUDE.md §4 rows added in this commit

none
