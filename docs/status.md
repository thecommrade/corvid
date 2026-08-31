# CORVID — project status (living document)

> Read this right after `CLAUDE.md` at the start of every session. It records where we are,
> what is settled, and the exact next step. Update it at the end of every session.
> Access details (ssh users/keys) live in the founder's private notes, not here.

_Last updated: 2026-08-31 (session 5 — S-04 completion attempt: F2 re-applied and verified, Aug-23 failure explained by measurement, benchmark deliberately deferred to a wired hub; ADR-0008 accepted)._

## Phase

**Phase 0 — largely EXECUTED 2026-08-23** (ahead of the Opus dispatch; see
`docs/runs/phase-0-2026-08-23.md` + `phase0-inputs-2026-08-23.md`): hub switched to kernel
mode (can dial 100.x — the R01 blocker is gone), MagicDNS live on all three nodes, all six
directional pairs **direct** after two verified network fixes (F1 ahnoway 41641/udp; F2
optiplex pref-5205 rules — runtime only, persistence needs an ADR). LAN-trio name-ping
exit criterion effectively met; remaining Phase 0 debts are founder steps (below). Git repo
`main`, account `thecommrade`. ADRs: 0001 commons, 0002 membership (+amend.), 0003 endpoints
(Accepted +amend.), 0004 exit criteria, 0005 slider, 0007 presence & GPU.

## Where the conversation stopped

> **RESUME HERE.** **S-04 is parked deliberately: placement understood, number deferred.**
> The blocker is physical — the hub's send ceiling is **5.0 MB/s**, so streaming the 26.63 GiB
> Q8_0 is ≈ 91 min of saturated uplink on the node serving Plex/Immich. Founder ruled that out
> (containers are critical). **Next action: nothing, until the hub is on Ethernet after the
> move** (finding 7) — then rerun with `-ts 6.5/4/4.5/14 -dev RPC0/RPC1/RPC2/RPC3 -lm dio`
> per `docs/runs/S-04-2026-08-31.md`. Founder owes only the ADR-0008 `protonvpn.conf` edits
> (both hubs, inert until the next VPN cycle, exact lines in that run file); until applied,
> the second node loses tailnet reachability at its next reboot. Hub apt unwedge + Tailscale
> upgrade stay deferred to a maintenance window. Phase 1 is unblocked for *design* work only.
> **OPEN NEXT SESSION ON THE RETRO, not on CORVID work:** session 5 was meant to run unaided
> and interrupted the founder repeatedly. Cause is recorded — the plan was infeasible on
> arithmetic available before it was written (hub 40–65 Mbit/s × 26.63 GiB ≈ 91 min was never
> multiplied out), and its founder-gated root steps sat in the critical path, so no execution
> could have been autonomous. Fix the planning process before writing another plan.

**Node in use by:** none (2026-08-31: all units stopped, no :50052 listeners, GPUs at idle)

Execution state: **M0–M5 documents done. Spikes: S-02, S-03, S-05, S-06 done; S-01 substantially done (one LAN leg + wired re-run pending); S-04 PARKED 2026-08-31 — mesh proven, placement understood and specified, Q8 number blocked on the hub's 5.0 MB/s uplink until Ethernet.** Phase 0 largely executed 2026-08-23. Phase 1/2 plans exist but **Phase 1 execution is gated on wiring the hub** — its first model load has the same 91-minute cost, and §3.2's assignment of `llama-server` to the hub is now an open question (finding 15).

## Settled decisions (do not re-litigate without new information)

| # | Decision | Date |
|---|---|---|
| 1 | Planning scope = **Option A**: Phases 0–2 at full executable depth; Phases 3–5 as outlines + research questions. | 2026-08-22 |
| 2 | Predecessor crypto project's **code stays closed**; import facts/principles only via founder debrief + public page. | 2026-08-22 |
| 3 | **Build fleet = ahnoway + solarplexus + optiplex.** Friends' machines are future members, not build nodes. All three share one LAN, so "two houses" tests need a friend. | 2026-08-22 |
| 4 | **Plans are executed by another Claude model (not Fable; likely the latest Opus).** Granularity: fully specified steps + research dossiers; no Haiku-level hand-holding. | 2026-08-22 |
| 5 | **ADR-0001 — Compute is a commons.** One pool, no member owns a slice; fair share only as scheduling when contended; **no per-member quotas/caps, nothing tied to contribution history — trust is total and does not decay**; data hard-partitioned per member; owner wins locally (§5); honest privacy limit (§5.7). | 2026-08-22 |
| 6 | **Spikes allowed during research**, reversible and non-production, **default cap ~10% of each device**; anything needing more is a time-boxed per-spike exception the founder grants. | 2026-08-22 |
| 10 | **Contribution is a per-machine slider** (ask (c) confirmed 2026-08-22): each owner decides how much each machine contributes, live-adjustable; a future *optional* mode may link a machine's contribution to its owner's usage dynamically — always the owner's choice, never imposed; consumption is never limited by contribution (ADR-0001 stands). Becomes ADR-0005. optiplex contributes under its slider and CORVID never touches its production Postgres or its other data disk. | 2026-08-22 |
| 12 | **ADR-0002 Membership (Accepted):** friends join as tailnet *users* (sharing is one-directional, recipient is not a member); ceiling = Personal plan 6 users (dated 2026-08-22); ACL baseline `tag:hub`/`tag:member`, member↔member denied by default; key expiry off on build nodes. | 2026-08-22 |
| 13 | **ADR-0004 Exit criteria on a one-LAN fleet (Accepted):** Phase 0 = LAN trio all-pairs name-ping + one cross-house name-ping (founder phone call); Phase 1 = thesis on the LAN trio + cross-house completion as a named follow-on. Charter wording unchanged. | 2026-08-22 |
| 16 | **ADR-0005 Contribution is a slider (Accepted 2026-08-22):** per-machine owner slider (CPU/RAM/VRAM/IO/hours/roles), live within ≤ 5 s (S-06: ms), nothing offered by default, optional usage-linked mode later (never imposed; consumption never limited). | 2026-08-22 |
| 17 | **ADR-0007 Presence & GPU (Accepted 2026-08-22):** provider chain with UNKNOWN; UNKNOWN never counts as idle; pause on AC loss immediately; GPU sharing temporal (all-or-nothing), VRAM ceilings coordinator-planned. | 2026-08-22 |
| 18 | **Amendments:** ADR-0002 — member devices never tagged (tags only on hubs); ADR-0003 — Caddy is the only tailnet-facing listener on the hub, backends loopback, identity via forward_auth/whois (or serve headers per S-05). | 2026-08-22 |
| 19 | **Phase 1 spec + plan, Phase 2 spec + plan (Parts A/B), Phase 3–5 outline written** (M3–M5 documents). Phase 1 = Vulkan b10581 fleet-wide, Qwen3.8-27B Q8_0, built-in UI; Phase 2 = agent v0 (slice + presence chain + heartbeat) + Postgres/FastAPI coordinator + status page behind Caddy. | 2026-08-22 |
| 15 | **ADR-0003 Accepted (2026-08-22)** with the Phase 1 spec (amended: `/chat` → `:8090` built-in UI in Phase 1; `:8093` reserved for Phase 2 member chat); CLAUDE.md §3.2 endpoint line corrected (spec §3.9c). | 2026-08-22 |
| 14 | **ADR-0003 Endpoints (Proposed):** solarplexus ports 8090 inference / 8091 coordinator / 8092 status / 8093 chat, tailnet-bound; Caddy front door on `:80`/`:443` with `/chat` `/v1` `/api` `/status`; member URL `http://solarplexus.<tailnet>.ts.net/`; CLAUDE.md §4 row for Caddy (Apache-2.0) added. | 2026-08-22 |
| 11 | **Package spec approved** (v2.1) and **GitHub account = `thecommrade`** (repo-local git identity; global name/email stay unset). | 2026-08-22 |
| 9 | **Package design approved in five sections (layout/flow; Phase 0 scope; research sweep + spike protocol; specs/plans 1–2 + outlines 3–5; skills & processes)** — spec at `docs/superpowers/specs/2026-08-22-corvid-research-and-planning-design.md`. | 2026-08-22 |
| 8 | **Approach = hybrid** (founder picked the recommendation): Phase 0 spec+plan now; parallel, adversarially verified research sweep with spikes for Phases 1–2; then specs+plans 1–2; 3–5 outlines; repo skeleton/ADRs/skills alongside. | 2026-08-22 |
| 7 | **Owner caps must be adjustable on the fly** (no restart); default 10%. Sharpens §5.3; candidate ADR; Phase 2 agent requirement. | 2026-08-22 |
| 21 | **S-04 parked honestly: placement understood, benchmark deferred to a wired hub.** The Aug-23 alloc failure was **over-subscription**, not leaked buffers — worker caches were empty (it died before any tensor moved) and CPU devices exported with `-d Vulkan0,CPU` advertise *installed* RAM as free, which the default proportional split believes; `-ts` is therefore mandatory and the planned second-worker fallback is unnecessary. The hub is out of the split **and** out of the client role while it serves media on Wi-Fi (5.0 MB/s measured → ≈ 91 min saturated uplink for a 26.63 GiB stream). **ADR-0008 accepted** (PostUp/PreDown guard; not yet applied). Hub apt unwedge + Tailscale upgrade deferred to a maintenance window. Renewed cap exception 2026-08-31: optiplex `MemoryMax` 12G → 16G, solarplexus withdrawn from the split. | 2026-08-31 |
| 20 | **S-04 completion runs as an attended-Opus session** — founder exception to the spike executor rule + blanket preapprovals for the gated steps, granted 2026-08-31; plan `docs/superpowers/plans/2026-08-31-s04-completion-and-phase0-closeout.md`. Placement strategy: worker CPU devices join the split + `-ts` within caps (GPU-only split cannot fit Q4/Q8 in ~17 GiB free VRAM). ADR-0008 approach settled: PostUp/PreDown pair in both hubs' wg-quick conf (no static pref survives a reconnect — netns-proven). | 2026-08-31 |

## Predecessor: Commputer (commputer.xyz)

Founder's earlier attempt at the same goal as a Layer-1 blockchain (Rust, $COMME). Debrief:
"sharing resources is easy; the trustless implementation is almost not worth the effort —
saved for a later day." CORVID is the friends-trust version. Principles worth importing
(candidate ADRs / front-page copy):

- "No datacenters. No mining farms. No e-waste. Your existing computer is enough."
- **Thresholds, not timelines** — products ship only when pooled capacity supports them; the
  dashboard shows how close we are.
- In an emergency, **protect members' data first**.
- Agent runs in user space, no elevated permissions, uses only what you allocate; being offline
  never reduces your access.
- Honest tone ("your share might be a calculator's worth of compute").
- Packaging fact: single binaries for Linux/macOS/Windows + `curl | sh` + 5-minute operator
  guide were achievable → input to §9 Q4.

## Build fleet (inventoried 2026-08-22)

Tailnet `tail2990fc.ts.net`, MagicDNS enabled tailnet-wide. One home LAN; WAN is not CGNAT;
UPnP/NAT-PMP available; nearest DERP ~40 ms; Tailscale bypasses the hubs' VPNs (verified).

| Node | Role | OS | CPU | RAM | GPU / VRAM | Disk free | Network | Tailscale |
|---|---|---|---|---|---|---|---|---|
| **ahnoway** | founder laptop | EndeavourOS | i7-10750H 6c/12t | 16 GB | RTX 2070 Super 8 GB (cc 7.5) | 258 GB | Wi-Fi, battery | 1.102.3, MagicDNS **off** |
| **solarplexus** | hub, always-on | Ubuntu 24.04 | i5-4690K 4c/4t (2014) | 16 GB | GTX 970 4 GB (cc 5.2, driver 535 / CUDA 12.2) | 242 GB + 7 TB free across two data disks | **Wi-Fi 405 Mb/s; wired unplugged** | 1.98.4, MagicDNS **off**, Tailscale SSH on |
| **optiplex** | second node; *also* another project's production host | Ubuntu 24.04 | i7-8700 6c/12t | 32 GB | RTX 3050 6 GB (cc 8.6, driver 590 / CUDA 13.1) | 244 GB (its other data disk is off-limits) | **Wi-Fi 866 Mb/s; wired unplugged** | 1.102.3, **logged out** |

Aggregate ≈ 18 GB VRAM, ≈ 63 GB RAM. solarplexus is the weakest compute node → coordinator /
web host / few layers; optiplex contributes under caps; ahnoway is the strongest single GPU.

**Already running on solarplexus (relevant):** Docker + NVIDIA Container Toolkit; Plex and the
*arr stack; **Tdarr** (distributed transcoding — a ready-made Phase 3 workload); **Immich**
(server/redis/db, no ML container — the "photo brain" half exists; its ML can run remotely);
**Caddy** reverse proxy (active, custom port, path routes). No host Postgres, no llama.cpp,
no Ollama. **Port 8080 is taken (qbittorrent)** → `http://solarplexus:8080` in CLAUDE.md must
change or route through Caddy.
**Already running on optiplex:** host PostgreSQL 16 on localhost = production DB of another
project (never touch); steady load ~2.2; zero 0.0.0.0 listeners (good hygiene).

## Phase 0 findings (go into the Phase 0 plan)

1. ~~optiplex logged out of Tailscale~~ **fixed 2026-08-22** (re-authed; still: disable key
   expiry on hubs so it never recurs).
2. ~~MagicDNS disabled on ahnoway and solarplexus~~ **fixed 2026-08-23** (accept-dns on
   fleet-wide).
3. **ssh config pins LAN IPs that drifted** — standardize on MagicDNS / Tailscale IPs; DHCP
   reservations.
4. **Tailscale SSH owns port 22 on the tailnet IPs** of both hubs; non-interactive ssh stalls
   on ACL/check auth. Configure ACLs or use OpenSSH via LAN/MagicDNS. Never edit sshd blind
   (solarplexus was once locked out).
5. **Zach is a shared node, not a member user** → one-directional; ADR "invite vs share";
   verify free-plan user limit.
6. **Port 8080 conflict** on solarplexus (see above).
7. **Hubs on Wi-Fi** — wire at least solarplexus before RPC latency tests. **PROMOTED to
   blocker 2026-08-31:** its send ceiling measured 5.0 MB/s (40 Mbit/s) over the LAN — vs
   16.3 MB/s peer-to-peer — and `enp*: carrier=0`. This is why S-04's number cannot be taken
   and why Phase 1's first model load would run ~91 min. Wire it after the move, then resume.
8. Tailscale version skew (1.98.4 vs 1.102.3) — upgrade.
9. `corvid.commputer.xyz` → Cloudflare 525 (no origin) → Cloudflare Pages at $0 later.
10. ~~solarplexus Tailscale is in userspace-networking mode~~ **fixed 2026-08-23** (kernel
    mode; hub dials 100.x; guard rules added).
11. Both hubs are on Wi-Fi only for the house showing / move; Ethernet returns on re-plug.
12. Network is friendly: UDP ok, non-CGNAT, UPnP/NAT-PMP, ~40 ms DERP — no NAT blocker.
13. **Runtime routing fixes do not survive optiplex** (probe 2026-08-31): a reboot ~Aug 26
    wiped the F2 rule, and tailscaled-layer probes (`tailscale ping`, tailnet port 22) mask
    the breakage — test with plain `ping` / a user-space TCP port. Re-apply + persist via
    ADR-0008 (in the 2026-08-31 plan).
14. **Hub apt has been wedged since Jul 2** — apt-daily's `apt-get update` hung mid-download,
    holding the apt lock (blocks the Tailscale upgrade). Owner confirmed 2026-08-31:
    `apt-daily.service`, four hung http/https method children. Unwedge = stop that unit;
    never delete the lock file. **Deferred by founder to a maintenance window** — the
    Tailscale upgrade restarts `tailscaled` and would blip Plex/Immich over the tailnet.
15. **The client role is a load-bearing topology decision, not just the split** (2026-08-31).
    A llama.cpp client memory-maps the entire model: on the hub, against `MemoryMax=8G`, this
    reached 7.87 GiB RSS and uninterruptible disk wait, thrashing page cache against the media
    pool. Use `-lm dio` (direct I/O) on any host shared with other services; use `-dev` to
    keep the hub's GPU out of the split. Feeds reserved ADR-0006 — **do not write that ADR
    until the hub is wired**, or it settles the wrong problem.
16. **Runtime-only ip rules on the second node are still live and still fragile** — re-applied
    2026-08-31, verified with plain `ping` (100% loss → 0%, ~5 ms). ADR-0008 specifies the
    permanent fix; **until the founder applies it, the next reboot wipes them again.**

## Gates still closed

- No code, scaffolding, or system changes until the design is approved (brainstorming gate).
- Do not open github.com/thecommrade/commputer.
- Confirm the GitHub account before the first commit.
