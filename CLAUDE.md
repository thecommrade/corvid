# CORVID — a friends-scale compute co-op
### (working title — crows share food; rename at will)

> **Mission:** Pool the machines our friends already own into one private network
> that gives every member shared compute, storage, and AI inference that no
> corporation meters, logs, or owns. Built on trust between people who know each
> other. Nothing here exists to make some dumb guy richer.

This file is the project's memory. Claude Code reads it at the start of every
session (docs: https://docs.claude.com/en/docs/claude-code/overview). Keep it
current: when a decision is made, record it here or in `docs/adr/`. When a
phase completes, mark it. Future sessions should never re-litigate settled
decisions without new information.

---

## 1. Ground truth & values

- **Friends-scale, not internet-scale.** Members are people the founder knows
  personally. We assume machines can *crash* but never *lie* (crash fault
  tolerance, not Byzantine). This single assumption is why the project is
  buildable in weekends instead of years.
- **No blockchain. No token. No coin. Ever.** Consensus-among-strangers
  machinery is the wrong tool when the trust already exists in the humans.
- **Credit before we copy.** Every borrowed idea, pattern, or dependency gets
  named in §4 with its license and author. If we can use or contribute to an
  existing project instead of rebuilding it, that is the default choice.
- **Consent and courtesy are features, not paperwork.** Nothing runs on a
  friend's machine without their explicit opt-in, visible controls, and an
  instant kill switch. (BOINC proved this is what makes volunteer computing
  survive; see §4.)
- **Something must work at the end of every phase.** No six-month dark tunnels.

## 2. Hard constraints

- **Mixed fleet:** members run mostly **Windows** and **macOS**; founder runs
  Linux (Ubuntu Server "solarplexus" = always-on hub; EndeavourOS + Arch
  laptops). Plan for Apple Silicon Macs, Windows/NVIDIA gaming PCs, and
  miscellaneous laptops.
- **Home networks:** CGNAT, dynamic IPs, consumer routers. **Zero open ports
  to the internet, ever.** All traffic rides the private mesh (§3.1).
- **Home bandwidth:** fine for control traffic and inference token streams;
  NOT fine for gradient synchronization. Therefore: **inference yes, training
  no** (non-goal, §7).
- **Budget: $0** in recurring costs for v1. Free tiers and open source only.
- **Founder's stack:** Python, PostgreSQL, Docker, SQL/BI — lean into these.

## 3. Architecture (v1)

### 3.1 Layer 0 — the mesh (buy, don't build)
**Tailscale** on every member device. Solves NAT traversal, WireGuard
encryption, stable private IPs, MagicDNS names, and identity (friends log in
with existing Google/GitHub/etc. accounts). As of mid-2026 the free Personal
plan covers **6 users, unlimited user devices** — sized exactly like a friends
co-op. If we outgrow it or want full self-hosting later: **Headscale**
(open-source control server). Decision: Tailscale first; Headscale is a
documented escape hatch, not a v1 task.

### 3.2 Layer 1 — AI inference (assemble, credit, don't rebuild)
**Backbone: llama.cpp RPC backend** (MIT). Runs natively on macOS (Metal),
Windows (CUDA/Vulkan/CPU), Linux (CUDA/CPU). `rpc-server` on each worker;
`llama-server` on solarplexus with `--rpc host:port,...` splits one model's
layers across all workers **in proportion to each device's free memory** —
mismatched hardware handled automatically. Exposes an OpenAI-compatible API on
the tailnet behind Caddy: every friend gets private AI at
`http://solarplexus.<tailnet>.ts.net/chat` (API at `/v1`; llama-server on `:8090`) —
see ADR-0003.
- **Security note (upstream's own warning):** RPC is *not secure by default*
  and must never touch the public internet. Our rule: rpc-server binds to the
  Tailscale interface **only**. The mesh is the security boundary.
- **Known limitation:** RPC exists to *fit* models too big for one machine,
  not to make small models faster. Set expectations accordingly.
- **Mac-heavy alternative: exo** (Apache 2.0) — MLX-based, auto-discovery,
  topology-aware sharding; brilliant on Apple Silicon clusters, but NVIDIA
  support currently lives in a community fork (exo-cuda) and releases break.
  Decision: llama.cpp RPC is the default; exo is an experiment branch.
- **Coordinator gap:** raw RPC means hand-editing IP lists and restarting dead
  workers. **SharedLLM** (AGPL-3.0) already builds exactly this: worker
  discovery, memory tracking, split planning, re-planning on node drop,
  HMAC-authenticated proxy. **Phase 5 mandate: evaluate adopting/contributing
  to SharedLLM before extending our own coordinator.** No double work.
- Watch list: **GPUStack** (currently Linux/WSL2-only workers, no macOS —
  revisit if their platform support changes), **prima.cpp**, **Ollama** (the
  single-node UX bar to meet), **Petals/Hivemind** (internet-scale public
  swarms — wrong trust model for us, right people to learn from).

### 3.3 Layer 2 — general compute (small custom build)
- **Agent** (Python; the founder's language): a small service on each node —
  launchd (macOS), Task Scheduler/service (Windows), systemd (Linux). Reports
  capabilities + liveness heartbeat; starts/stops work on command; enforces
  the politeness policy (§5) locally, so a member's own machine is always the
  final authority.
- **Coordinator** (solarplexus): PostgreSQL roster of nodes/capabilities/
  status + a dumb job queue. At friends-scale a scheduler is a table and a
  loop. Resist cleverness until pain demands it. (If real orchestration is
  ever needed: HashiCorp **Nomad** — single binary, all three OSes — noting
  its BUSL 1.1 source-available license.)
- **Job execution by node role, not uniformity:**
  - **Linux + Windows/WSL2 nodes:** Docker containers, resource-capped
    (cgroups). WSL2 gives Windows real Linux + CUDA.
  - **macOS nodes:** containers can't reach the GPU, so Macs don't run
    containers. Macs are premium **inference** nodes (unified memory is their
    superpower) and may accept CPU-only sandboxed jobs later. Play to
    strengths; don't sand every OS down to the same shape.
- **Storage:** models live on solarplexus (already serving media — same
  pattern). Member file sync later via **Syncthing** (MPL-2.0) if wanted.

### 3.4 Observability
Node status, job history, "who contributed what" — first as a Postgres schema
(founder's home turf), surfaced via Grafana or Power BI. Contribution ledger
is a *thank-you board*, never a currency.

## 4. Prior art & credits (the shoulders we stand on)

| Project | What we take | License | Credit |
|---|---|---|---|
| llama.cpp + RPC backend | The entire cross-platform inference backbone | MIT | Georgi Gerganov & ggml-org; RPC by Radoslav Gerganov |
| Tailscale / WireGuard | Mesh networking, identity, NAT traversal | BSD (clients) / GPLv2 (WireGuard) | Tailscale Inc.; WireGuard by Jason A. Donenfeld |
| Headscale | Self-hosted control plane (escape hatch) | BSD-3 | Juan Font & community |
| SharedLLM | Coordinator design; candidate to adopt/contribute | AGPL-3.0 | SharedLLM project |
| exo | Heterogeneous auto-sharding ideas; Mac experiments | Apache 2.0 | EXO Labs (exo-explore/exo); CUDA fork by Scottcjn |
| BOINC | The politeness model: idle-only, owner-set limits, opt-in | LGPL | David P. Anderson, UC Berkeley |
| Folding@home / SETI@home | Proof that volunteer compute works at planet scale | — | Pande Lab et al. |
| GPUStack | Cluster-manager patterns; Grafana/Prometheus pairing | Apache 2.0 | gpustack project |
| Petals / Hivemind | Internet-scale swarm inference research | Apache 2.0 | learning-at-home; Borzunov et al. |
| Syncthing | Member file sync (future) | MPL-2.0 | Jakob Borg & community |
| Ollama | The single-machine UX bar our friends will compare us to | MIT | Ollama team |
| Kubernetes / Raft / etcd | The conceptual lineage (declarative desired state) | Apache 2.0 | CNCF; Ongaro & Ousterhout (Raft) |
| Caddy | Reverse proxy / front door for CORVID's tailnet web apps (already on the hub) | Apache-2.0 | Matt Holt & the Caddy contributors (ZeroSSL); ADR-0003 |
| Qwen3.8-27B (model weights; ggml-org GGUF conversion, Q8_0 + Q4_K_M) | The Phase 1 model — the one large enough to be impossible on any single node and so to prove the pool's reason for existing | Apache-2.0 (LICENSE at repo main: "Copyright 2026 Alibaba Cloud"; not gated) | Qwen team, Alibaba Cloud; GGUF conversion by ggml-org (R04-F13/F15/F16) |

**Rule:** new dependency ⇒ new row in this table, same commit.

## 5. Politeness & safety policy (non-negotiable)

1. **Opt-in everything.** A node joins nothing by default. Each member chooses:
   inference host? batch jobs? hours? caps?
2. **Idle-only by default.** Work pauses on user activity; on laptops, pauses
   on battery. (BOINC's 25-year-old lesson.)
3. **Hard resource caps** per node: CPU %, RAM, disk, GPU — set by the owner,
   enforced by the *agent locally*, not trusted to the coordinator.
4. **Kill switch:** one visible command/tray action stops all co-op work on a
   machine instantly. No arguments, no grace period.
5. **Host protection:** batch jobs run in containers with no host filesystem
   access beyond a scratch dir; treat gVisor/Firecracker as the upgrade path
   if we ever accept less-trusted workloads.
6. **Zero public exposure:** every listener binds to the tailnet interface.
   CI check: no service on 0.0.0.0 without an ADR explaining why.
7. **Privacy inside the pool:** friends-trust means hosts *can* see jobs they
   run. Document this honestly for members; don't promise confidential
   compute we can't deliver.

## 6. Roadmap — something works at every phase

- **Phase 0 — The handshake (a weekend).** Tailscale on solarplexus + founder's
  laptop + 1–2 friends' machines. Exit: everyone pings everyone by MagicDNS
  name across houses. *The network exists.*
- **Phase 1 — First shared model (a weekend).** llama.cpp on two nodes;
  rpc-server on the friend's box (tailnet-bound); llama-server on solarplexus
  splits a model that fits on neither machine alone. Exit: a friend gets a
  completion from a model spread across two houses. *The thesis is proven.*
- **Phase 2 — The roster (1–2 weekends).** Python agent v0: heartbeat +
  capability report into Postgres on solarplexus. Tiny status page. Exit:
  a live map of the co-op. *The pool is visible.*
- **Phase 3 — Batch jobs (2–3 weekends).** Queue table + agent job execution
  in capped containers on Linux/WSL2 nodes. First real workload: a member's
  media transcode or a data pipeline. Exit: submit → runs on someone else's
  idle machine → results back. *The pool does work.*
- **Phase 4 — Politeness + dashboard (ongoing).** Idle detection, battery
  awareness, caps UI, kill switch, contribution thank-you board (Grafana or
  Power BI). Exit: a non-technical friend installs, understands, and controls
  it without the founder present. *The pool is trustworthy.*
- **Phase 5 — Converge, don't diverge.** Formal evaluation: adopt/contribute
  to SharedLLM for inference coordination? Adopt Nomad for scheduling? Write
  an ADR either way. *The pool joins the commons instead of forking it.*

## 7. Non-goals (write once, save months)

- No blockchain, tokens, coins, or on-chain anything.
- No anonymous/stranger participation. Friends-of-friends require a decision.
- No distributed *training* — home bandwidth physics says no. (If that ever
  changes, the DiLoCo line of research is the door; not a v1 concern.)
- No confidential computing / protecting jobs from hosts (wrong trust model).
- No hand-rolled crypto, consensus, or schedulers where a credited project
  already does it well.
- No monetization. If costs ever need sharing, it's a potluck, not a market.

## 8. Working agreements for Claude Code sessions

- **Session start:** read this file; check `docs/adr/` and the phase status
  above; state which phase we're in before writing code.
- **Resume point:** `docs/status.md` is the living status + exact next topic
  (updated at every session end; survives context compaction). Read it right after
  this file and open the session on the topic it names.
- **Docs-as-code:** MkDocs Material in `docs/`; every component gets a page
  when it gets a repo directory. Decisions → short ADRs (`docs/adr/NNNN-*.md`).
- **Style:** Python typed + ruff-formatted; SQL migrations under `db/`;
  conventional commits; small PR-sized changes even solo.
- **Honesty over cheerleading:** if a phase's approach conflicts with
  something learned mid-build, say so and propose the ADR — don't quietly
  comply.
- **Member-facing copy** (setup guides for friends) is written for smart
  non-engineers, one page per OS, screenshots welcome. The Plex family setup
  guide is the house standard for tone.
- **License hygiene:** before importing anything, add its row to §4 and check
  compatibility (nb: AGPL components stay network-served, which suits us).

## 9. Open questions (fodder for session one)

1. Real name for the project? (Domain commputer.xyz already in hand.)
2. First two friend machines: exact specs/OS, so Phase 1's model is chosen to
   *require* both (the demo must be impossible on one machine).
3. Which model for the Phase 1 demo? (Pick for wow-per-gigabyte.)
4. Agent packaging for friends: Python + installer script vs. a compiled
   single binary later?
5. What does the *founder's* machine owe the pool while job hunting? (Set his
   own caps too — the politeness policy applies to everyone.)

## 10. The front page — what corvid.commputer.xyz says

> **This section is the canonical public copy** for the project's home at
> `corvid.commputer.xyz` (subdomain of the founder's commputer.xyz). It is the
> plain-language contract with members and the flag planted for anyone who
> might join. Build the site to say this. Change the site only by changing
> this section first.

---

**CORVID is a village utility.**

Your computer sits idle for most of its life. So does your neighbor's. CORVID
pools that idle time across a group of friends into one private network —
shared compute, shared storage, shared AI — owned by its members, metered by
no one, and built so it doesn't make some dumb guy richer.

**The arithmetic, honestly.** Twenty everyday computers each giving 20% of
their time is, in effect, four machines running flat-out around the clock.
Priced the way the cloud prices it, that's roughly $10–15K a year of compute —
produced for about $20–40 per machine per year in electricity, on hardware we
already own. That gap between what idle silicon costs and what compute sells
for is the entire engine. No token required. No company required. Just friends
and physics.

**What members get:**

- **Private AI.** One endpoint on our own network. The models run on *our*
  machines — the strongest nodes host them, and the network routes your
  request to whichever one is free. Nobody logs it. Nobody meters it. Nobody
  sells it back to us at $20 a month.
- **A community photo brain.** Face search and "find that picture from the
  lake" across your own library — computed on the pool, stored by you.
- **A mutual backup pact.** Donate a slice of disk, and the photos you can't
  replace live in three houses instead of one.
- **The boring miracles.** Media transcoding in days instead of months, audio
  transcription, big batch jobs, and overnight runs of models too large for
  any single machine in the group — the pool's party trick.
- **Leftovers do good.** Idle cycles nobody claims fold proteins for disease
  research (Folding@home, team CORVID) instead of doing nothing.

**What CORVID is not.** Not a blockchain. Not a coin. Not a startup. Not open
to strangers. It's built by friends, on trust that already exists, out of
parts made by people we name and thank (§4). If it ever costs money, it's a
potluck, not a market.

**The rules we run on.** Everything is opt-in. Your machine obeys you first,
always. One click stops all of it, instantly. And the founder's caps are set
the same way yours are.

## 11. How members touch it — the interface decision

**Decision: one central web app on the tailnet + one per-machine agent.
No native consumer apps. No per-user local sites.**

- **Consuming = URLs.** All member-facing services are web apps served from
  solarplexus, reachable only over the tailnet: the AI chat, the photo brain,
  the status dashboard, behind one CORVID landing page. Because members are
  on the mesh, a private site feels exactly like a normal website — from
  laptops *and* phones (Tailscale runs on iOS/Android; phones consume, never
  contribute).
- **Zero-login by design.** Tailscale identity tells the server who is
  connecting. No accounts, no passwords, no reset-my-password support burden.
  A member is recognized because they're on the network. (Implementation:
  Tailscale serve/identity headers or whois-on-IP — verify current mechanism
  at build time.)
- **Contributing = the one installer.** The agent (§3.3) is the only software
  CORVID ships: background service + tray/menu-bar presence showing status,
  the owner's caps, and the kill switch — §5 given a face. Physics forces
  this one; nothing else gets an installer.
- **The rule for all future interface questions: ship URLs, not installers.**
  Every installer is a support burden × 20 friends × 3 OSes. Every URL is
  free, updates once for everyone, and works on devices we've never seen.
  Native apps also break the $0 budget (code signing, store fees) and scare
  non-technical members (unsigned-app warnings).
- **Assemble the site, don't write it.** Mature open-source frontends exist
  for every consuming service (chat UIs, Immich for photos, Grafana for
  status). Session one picks them, checks each license, and adds §4 rows on
  adoption — per the §8 hygiene rule. The landing page itself says what §10
  says, and nothing else.
- **Onboarding fits on an index card:** 1) install Tailscale, 2) install the
  CORVID agent, 3) bookmark the site. If a step four ever appears, something
  has gone wrong.
