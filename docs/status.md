# CORVID — project status (living document)

> Read this right after `CLAUDE.md` at the start of every session. It records where we are,
> what is settled, and the exact next step. Update it at the end of every session.
> Access details (ssh users/keys) live in the founder's private notes, not here.

_Last updated: 2026-08-22 (end of session 2 — package documents complete; founder-gated items listed)._

## Phase

**Phase 0 — mostly done, with debts.** Tailscale is on all three build nodes and one friend's
Windows box, but the exit criterion ("everyone pings everyone by MagicDNS name") is not met —
see findings below. No code yet. Git repo initialised 2026-08-22 (branch `main`, account `thecommrade`). ADRs: 0001 commons, 0002 membership (+amend.), 0003 endpoints (Accepted +amend.), 0004 exit criteria, 0005 slider, 0007 presence & GPU.

## Where the conversation stopped

> **RESUME HERE (founder instruction 2026-08-22: "begin next session with exactly this, even
> after compact").** **The research & planning package documents are complete** (M0 skeleton;
> R00–R10; Phase 0/1/2 specs + plans (Phase 2 = Part A agent + Part B coordinator); Phase 3–5
> outline; ADR-0001…0005 + 0007; DoD run `docs/runs/package-dod-2026-08-22.md`; CI green).
> **Open items — all founder-gated:** (1) approve the guard-hook false-positive fix; (2) S-01
> bandwidth exception + Plex/Immich idle; (3) S-05 operator mode on ahnoway; (4) S-04/Phase 1
> firewall rules (TCP 50052 in on `tailscale0`) + demo cap exceptions; (5) Phase 0 inputs (ACL
> `ssh` paste + DNS page state, root-only `wg` reads, `ssh-add` before step 2). **Then:** fold the
> research-sweep completeness re-run (run `wf_736a0d16-37b`) into R01/R03/R05/R07/R08/R09/R10,
> run the pending spikes, tag `m2` → `package-v1`, dispatch the Phase 0 plan to an Opus session.
> Scratch left on the nodes for S-04: `~/corvid-s02/`, `~/corvid-s03/` (cards say remove after).

**Node in use by:** none (S-03 done; research-sweep workflow running — no node use)

Execution state: **M0, M1 done; M2 documents done (spikes S-01/S-04/S-05 pending founder); M3, M4, M5 documents done.** Phase 0/1/2 plans are ready for Opus; none executed yet.

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
2. **MagicDNS disabled on ahnoway and solarplexus** — `tailscale set --accept-dns=true`.
3. **ssh config pins LAN IPs that drifted** — standardize on MagicDNS / Tailscale IPs; DHCP
   reservations.
4. **Tailscale SSH owns port 22 on the tailnet IPs** of both hubs; non-interactive ssh stalls
   on ACL/check auth. Configure ACLs or use OpenSSH via LAN/MagicDNS. Never edit sshd blind
   (solarplexus was once locked out).
5. **Zach is a shared node, not a member user** → one-directional; ADR "invite vs share";
   verify free-plan user limit.
6. **Port 8080 conflict** on solarplexus (see above).
7. **Hubs on Wi-Fi** — wire at least solarplexus before RPC latency tests.
8. Tailscale version skew (1.98.4 vs 1.102.3) — upgrade.
9. `corvid.commputer.xyz` → Cloudflare 525 (no origin) → Cloudflare Pages at $0 later.
10. **solarplexus Tailscale is in userspace-networking mode** — it can accept tailnet
    connections but cannot *dial* tailnet IPs; a coordinator there cannot reach workers until
    it is switched to kernel mode with the VPN-bypass routing optiplex already has.
11. Both hubs are on Wi-Fi only for the house showing / move; Ethernet returns on re-plug.
12. Network is friendly: UDP ok, non-CGNAT, UPnP/NAT-PMP, ~40 ms DERP — no NAT blocker.

## Gates still closed

- No code, scaffolding, or system changes until the design is approved (brainstorming gate).
- Do not open github.com/thecommrade/commputer.
- Confirm the GitHub account before the first commit.
