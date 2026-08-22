# CORVID — Research & Planning Package: Design Spec

- **Date:** 2026-08-22 (v2.1 — after a three-lens adversarial self-review and a verification pass)
- **Status:** **Approved by the founder 2026-08-22** (v2.1). All five design sections were
  approved in conversation the same day (recorded in `docs/status.md`).
- **Author:** Claude (Fable 5, "the main session") with the founder
- **Executor of the resulting plans:** another Claude model — not Fable; likely the latest Opus
- **Related:** `CLAUDE.md` (the charter), `docs/status.md` (living resume point),
  `docs/adr/0001-compute-is-a-commons.md`
- **Notation:** "§N" alone means a section of *this* spec; "CLAUDE.md §N" means the charter.
  "Design section 1–5" are the five blocks approved in conversation and map to §4–§8 here.

---

## 1. Purpose and scope

This package is the set of documents that lets a capable-but-context-free model (Opus) build
CORVID Phases 0–2 without re-researching anything or asking the founder what a machine is.
It consists of:

1. **Research dossiers** (`docs/research/R00…R10`) — verified facts, measured numbers from
   spikes, sources with dates and pinned versions, open questions, and the CLAUDE.md §4
   credit rows each dependency needs.
2. **Design specs** per phase (`docs/superpowers/specs/`) — Phase 0, Phase 1, Phase 2.
3. **Executable plans** per phase (`docs/superpowers/plans/`) — `writing-plans` format.
4. **Outlines** for Phases 3–5 — goals, decisions needed, research questions; no plans.
5. **ADRs** created as decisions land (`docs/adr/`).
6. **Project skills, hooks, workflows, CI** that make the charter's rules mechanical.

**Scope decision (settled 2026-08-22):** Option A — Phases 0–2 at full executable depth;
Phases 3–5 as outlines, because Phase 1 field results will change them.

**Approach (settled 2026-08-22):** the hybrid — Phase 0 spec + plan first; then one parallel,
adversarially verified research sweep with spikes for Phases 1–2; then Phase 1 and Phase 2
specs and plans written against the dossier facts; Phases 3–5 outlines; repo skeleton, ADRs,
skills/hooks built alongside. Sequencing constraints are in §9.

**What this package does and does not execute.** The package is documents. Executing the
Phase 0 plan is *not* required for the package's definition of done (§12) — but Phase 0
steps 0–2 (§5) must be executed before the research sweep's tailnet-path spikes (§6.3), so in
practice they run during M1/M2 (step 3, key expiry, is independent). Evidence from any execution goes to `docs/runs/` (§3.4).

## 2. Context (established; do not re-derive)

- **Charter:** `CLAUDE.md` §1–§11 stand. Friends-scale, crash-not-Byzantine; no blockchain;
  credit before copy; politeness non-negotiable; $0 recurring; Tailscale mesh; llama.cpp RPC
  backbone; Python agent + Postgres coordinator; ship URLs not installers.
- **Phase:** Phase 0 mostly done with debts (see `docs/status.md` "Phase 0 findings").
- **Build fleet** (all Linux, one LAN): **ahnoway** (founder laptop, RTX 2070S 8 GB, 16 GB
  RAM, 12 threads), **solarplexus** (hub, GTX 970 4 GB Maxwell cc 5.2 on driver 535/CUDA 12.2,
  16 GB RAM, 4 threads — weakest compute; 15 TB mergerfs pool; Docker compose media stack incl.
  Immich/Tdarr; Caddy on the host; **Tailscale in userspace mode**; port 8080 taken),
  **optiplex** (i7-8700 12 threads, 32 GB, RTX 3050 6 GB on CUDA 13.1; **another project's
  production host**: localhost Postgres, steady load, a data disk that is off-limits).
  Aggregate ≈ 18 GB VRAM / 63 GB RAM. LAN DNS is a Pi-hole (hostname only in this repo; its
  address lives in the founder's private notes). Friends' machines are future members, not
  build nodes; one friend (Zach) already has a Windows box *shared into* the tailnet from his
  own tailnet; a phone (consumer device) is a tailnet member.
- **Settled decisions:** ADR-0001 *Compute is a commons* (pool; fair share only as scheduling
  when contended; **no per-member quotas/caps or anything tied to contribution — trust is total
  and does not decay**; data hard-partitioned per member; owner wins locally per CLAUDE.md §5;
  honest privacy limit CLAUDE.md §5.7; **no prompt/content logging by default**). Spikes
  allowed at a **~10% per-device default cap** (Appendix B), exceptions granted per spike or
  per plan step by the founder, time-boxed. **Owner caps must be adjustable on the fly** (no
  restart) — sharpens CLAUDE.md §5.3; becomes **ADR-0005 "Contribution is a slider"** in M4
  and a Phase 2 agent requirement: each owner sets, per machine, how much it contributes
  (the cap table values are only the test defaults); a future *optional* mode may link a
  machine's contribution to its owner's usage dynamically — always the owner's choice, never
  imposed; consumption is never limited by contribution (ADR-0001 stands).
  Predecessor (Commputer) code stays closed; its principles are imported (see `status.md`).
- **optiplex participation (ask (c) — confirmed by the founder 2026-08-22):** optiplex
  contributes GPU + spare CPU under its owner-set slider, and CORVID never touches its
  production Postgres or its other data disk. Nothing is blocked on (c) any more.
- **Access:** documented in the founder's private `networkdocs` repo and Claude's memory.
  Summary that may live in this repo: unattended user-level access exists to both hubs via
  documented ssh aliases; root on solarplexus via the `splx-root` alias once the founder has
  loaded the passphrase-protected key into ssh-agent; no unattended root path on optiplex.
  Usernames, key file names, LAN/public IPs, and VPN configuration are **never** written into
  this repo (see §3.8).

## 3. Design principles for the package

1. **Self-contained plans.** A plan is executable with `CLAUDE.md` + `docs/status.md` + the
   dossiers it links. No hidden context, no "ask the founder what X is". (Phase 0's plan links
   R00, which is written for exactly this purpose.)
2. **Facts carry provenance.** Every dossier fact has a primary-source URL + *date verified*
   + the version/commit it applies to when version-dependent, or a spike ID. Unverified =
   marked `UNVERIFIED`, never smoothed over.
3. **Executor tags on every step** — exactly one of the three values defined in Appendix A:
   `executor: main-session`, `executor: Opus` (optionally qualified `Opus (splx-root)` for
   root-on-solarplexus steps), `executor: founder`. Appendix A also defines
   the **founder handoff protocol** and the **preflight**.
4. **Evidence before "done".** Every plan and spike ends with a verification checklist. Full
   outputs go to `docs/runs/<plan-or-spike>-<YYYY-MM-DD>.md`; `docs/status.md` gets one
   summary line + link per verification. `status.md` has a single writer (the main session, or
   the founder); Opus proposes its summary line in the run file. Raw captures too large for a
   run file go to `docs/runs/raw/` (git-ignored). The "node in use by" line (§9) is written and
   cleared by the main session only.
5. **Politeness applies to the build.** Spikes and plan steps respect the cap table (Appendix
   B), bind only to the tailnet interface (S-01's LAN-IP exception is written on its card),
   never touch optiplex's production surface, and carry a one-line undo.
6. **Honesty over cheerleading.** Where the fleet or the ecosystem contradicts the charter,
   the dossier says so and the resolution is recorded: architectural conflicts get an ADR
   (ADR-0002 membership, ADR-0003 endpoints, ADR-0004 exit criteria on a one-LAN fleet,
   ADR-0005 live-adjustable caps, and a topology ADR if R03 places `llama-server` anywhere but
   solarplexus); operational fixes (the userspace→kernel Tailscale switch, the GTX 970 build
   path) are recorded in their dossier + `status.md` without an ADR. **Numbering:** 0002–0005
   are reserved for the ADRs named here regardless of landing order; a topology ADR, if needed,
   takes 0006; `new-adr` honours reservations.
7. **YAGNI.** No quota tables, no credit weighting, no scheduler cleverness, no installers
   beyond the agent, no member guides before Phase 4.
8. **What may appear in this repo.** Allowed: hostnames, roles, MagicDNS names, ssh *alias*
   names, the executor table, network interface names, and the policy-routing recipe **stored
   with placeholders** (`<lan-gw>`, `<vpn-if>`, `<table>`; concrete values in `networkdocs`).
   Not allowed: usernames, key file names, LAN or public IPs, passwords, and VPN configs —
   meaning provider configs, credentials, endpoints and IPs. Hook patterns that need
   hostnames/IPs live in the git-ignored `.claude/settings.local.json`.
9. **CLAUDE.md edit policy (single allow-list, used by §4, §8, §11).** Pre-approved edits:
   (a) CLAUDE.md §4 credit rows, in the same commit as the dependency, via `add-dependency`;
   (b) phase-complete marks in CLAUDE.md §6; (c) the CLAUDE.md §3.2 endpoint line, when
   ADR-0003 is Accepted; (d) one-line pointers to `status.md` or a new ADR. Anything else
   needs the founder's explicit ok.

## 4. Repo layout & flow (design section 1, approved)

```
corvid/
├── CLAUDE.md                        charter (edits per §3.9 only)
├── .gitignore                       from M0: .claude/settings.local.json, scratch, models, docs/runs/raw/
├── mkdocs.yml                       MkDocs Material (CLAUDE.md §8), created in M0
├── docs/
│   ├── status.md                    living resume point (single writer)
│   ├── adr/                         TEMPLATE.md + NNNN-slug.md (0001 exists)
│   ├── research/                    R00-phase0-facts.md, R01-fleet-and-network.md … R10-…
│   │   └── spikes/                  TEMPLATE.md + S-nn-slug.md (+ S-nn/ scratch snippets)
│   ├── runs/                        evidence: <plan-or-spike>-<YYYY-MM-DD>.md (full outputs); raw/ git-ignored
│   ├── runbooks/                    founder-facing runbooks (Phase 2 writes the first)
│   ├── superpowers/specs/           YYYY-MM-DD-<slug>-design.md (this spec; one per phase;
│   │                                phase-3-5-outline.md)
│   ├── superpowers/plans/           YYYY-MM-DD-<slug>.md (one executable plan per phase)
│   └── members/                     later (Phase 4): per-OS setup guides, Plex-guide tone
├── .claude/skills/                  save-state, new-adr, add-dependency, spike, remote-step
├── .claude/settings.json            hooks (committed; no IPs)
├── .claude/settings.local.json      hook patterns that need hostnames/IPs (git-ignored)
├── .claude/workflows/               Claude Code Workflow-tool scripts (*.js with `meta`):
│                                    research-sweep (M2); code-review arrives with Phase 2 code
├── .github/workflows/ci.yml         ruff; pytest (smoke until agent/ exists); mkdocs build;
│                                    bind-target lint (§8)
└── agent/ coordinator/ db/ …        created only when a phase's plan says so
```

**Flow per phase:** dossiers → spec → plan → Opus executes → run file in `docs/runs/` →
`status.md` summary line → ADRs as decisions arise. **Git:** `git init` and first commit when
this spec is accepted and after the founder names the git identity + GitHub account (global
rule — **named 2026-08-22: GitHub `thecommrade`**, repo-local git identity, remote URL
carrying the username so the credential helper picks that account); creating the remote and
the first push are founder-approved steps; conventional commits; small branches even solo; worktrees for plan execution.

## 5. Phase 0 spec + plan scope (design section 2, approved)

Charter exit (CLAUDE.md §6): *everyone pings everyone by MagicDNS name across houses.*
**ADR-0004 (authored in M1) splits it honestly:** Phase 0 is *complete* when (a) the LAN trio
name-pings all pairs and (b) at least one cross-house name-ping succeeds — Zach's shared node
when online, or an invited member's device under ADR-0002 — with (b) an `executor: founder`
step (a phone call: "install Tailscale / accept the invite"; no CORVID software, no guide
document). The same ADR records Phase 1's split (§7).

The Phase 0 plan links **R00 — Phase 0 facts** (authored by the main session in M1 from
read-only inspection + dated Tailscale docs): current DNS state per node, `tailscaled`
flags/mode per node, Tailscale versions, Tailscale SSH/ACL state, optiplex's exact VPN-bypass
policy routing (ip rule / ip route tables, units, interface names — with §3.8 placeholders)
and solarplexus's routing/tailscaled state (VPN provider details stay in `networkdocs`),
producing the verified kernel-mode switch + rollback sequence.
Steps, in order, each with executor / expected output / undo:

0. **Unattended access path (first, before anything unattended).** Decide and record how
   `executor: Opus` reaches each hub non-interactively: Tailscale SSH with an ACL `accept`
   rule for the founder's own devices (founder, admin console; works away from home; may grant
   root on solarplexus by ACL), or OpenSSH over LAN with the documented key (works today for
   user level; root only via `splx-root`). R00 records the current Tailscale SSH/ACL state and
   the plan writer picks one; the OpenSSH-over-LAN option additionally requires stable LAN
   addressing (DHCP reservations or Pi-hole names for both hubs — `executor: founder`, router
   admin). Verification: `ssh -o BatchMode=yes <alias> true` from ahnoway to both hubs, plus
   `splx-root`. Recorded in `remote-step` and `status.md`.
   Also: one-time `executor: founder` step on ahnoway `sudo tailscale set --operator=$USER`
   so Opus can run `tailscale set` there unprivileged.
1. **MagicDNS on ahnoway + solarplexus** (`tailscale set --accept-dns=true`; ahnoway via
   operator mode, solarplexus via `splx-root`). Mechanism: with no global nameservers
   configured in the tailnet, Tailscale's resolver answers `*.ts.net` and forwards everything
   else to the node's existing DNS (the Pi-hole on LAN; optiplex's VPN DNS) — **no admin-console
   change expected**; R00 confirms. Verify with `resolvectl status` and `resolvectl query
   <peer>.<tailnet>.ts.net` on ahnoway and optiplex; solarplexus is verified in step 7 (it
   cannot dial until step 2).
2. **solarplexus Tailscale: userspace → kernel mode** with the VPN-bypass policy routing
   captured in R00, so the hub can *dial* workers; upgrade to current. **Safety:** founder
   present (local console or a root `tmux` on solarplexus that Opus issues commands into);
   timed auto-rollback armed before the change (e.g. `systemd-run --on-active=10m <rollback>`,
   cancelled on success); precondition: no active Plex streams / Immich jobs (founder confirms).
   Never run unattended.
3. **Key expiry off** for the three build nodes (`executor: founder`, admin console).
4. **ADR-0002 — Membership:** invite friends as tailnet *users* vs node sharing. Step 4
   verifies the current free-plan user/device limits at the primary source (dated) and asks:
   does node sharing yield a per-request member identity usable for zero-login (CLAUDE.md §11)
   and ADR-0001 data partitioning? If not, sharing is disqualified for members (may remain for
   devices). ADR-0002 is **Accepted in M1**; R02 re-checks later. ACL baseline included.
5. **SSH hygiene:** aliases by MagicDNS name / Tailscale IP if step 0 chose Tailscale SSH, or
   by reserved LAN name/IP if it chose OpenSSH-over-LAN; stale alias removed (founder's
   `networkdocs` is theirs to edit; we note it).
6. **ADR-0003 — Endpoints (Proposed in M1, Accepted with the Phase 1 spec):** CORVID ports on
   solarplexus (not 8080) and the Caddy route for the tailnet landing page / API. **Caddy gets
   its CLAUDE.md §4 row in the ADR-0003 commit** (Apache-2.0; Matt Holt & the Caddy
   contributors) via `add-dependency`. Rule: any dependency a Phase 0 step introduces gets its
   row in that plan, not "later in a dossier". On acceptance, CLAUDE.md §3.2's `:8080` line is
   corrected (§3.9c).
7. **Verification:** all-pairs name-ping (all three nodes, after step 2); a throwaway
   tailnet-bound test listener curl'd from the other two; one cross-house name-ping (ADR-0004
   (b)); outputs to `docs/runs/`, summary to `status.md`.

Out of scope: llama.cpp (Phase 1), the agent (Phase 2). No spikes. Tools used only inside
spikes/plans (e.g. iperf3) are credited on the spike card, not in CLAUDE.md §4; anything
CORVID ships or relies on gets a CLAUDE.md §4 row.

## 6. Research sweep + spike protocol (design section 3, approved)

### 6.1 Dossiers (`docs/research/`)

"Depth": **full** = adversarially fact-checked; **outline** = dated facts, not fact-checked
beyond dates/licences (keeps Option A honest).

| # | Dossier | Key questions (must yield citable facts) | Depth | Spikes |
|---|---|---|---|---|
| R00 | Phase 0 facts | see §5 (DNS state, tailscaled modes/flags/versions, Tailscale SSH/ACL state, VPN-bypass routing recipe + rollback) — authored in M1 by the main session | full | — |
| R01 | Fleet & network | consolidated inventory incl. Pi-hole (hostname/role), model-store path + disk + free GB, scratch paths; measured LAN-path and tailnet-path throughput/latency all pairs (Wi-Fi now; again when wired — Phase 1 cites the wired number if it exists, else the Wi-Fi number flagged); DERP/NAT facts; cross-house path recorded `UNVERIFIED` with `tailscale netcheck` DERP figures as the worst-case bound, re-measured at first member onboarding | full | S-01 |
| R02 | Tailscale: membership, ACLs, DNS, identity | free-plan limits (primary source, dated); invite vs share semantics and whether sharing yields per-request identity; ACL baseline; MagicDNS + split DNS with the Pi-hole; key expiry; Tailscale SSH check/accept modes; zero-login mechanism for web apps (`tailscale serve` identity headers vs `whois`), with version pinned | full | S-05 |
| R03 | llama.cpp RPC on this fleet | install/build per node at a pinned tag/commit (release binaries allowed where they fit; GTX 970 Maxwell cc 5.2 on driver 535/CUDA 12.2 = hard case; RTX 3050 CUDA 13.1; RTX 2070S); `rpc-server` flags at that version (tailnet bind, `--mem`, cache dir/size); `llama-server --rpc` split behaviour; **which flags suppress prompt logging**; linger state per node + executor to enable; `/dev/nvidia*` access for the service user; security posture; measured tok/s at 10% and under exception | full | S-02, S-03, S-04 |
| R04 | Model selection for Phase 1 | candidates ranked on a named, dated basis (leaderboard(s) and/or a fixed prompt set) that satisfy the Phase 1 "impossible on one machine" criterion (§7) with the GB numbers (weights + KV at the chosen quant); model licences → CLAUDE.md §4 rows; if no candidate is both impossible-on-one and worth demoing, say so and propose an ADR | full | uses R03 |
| R05 | Agent platform matrix | per OS: service install (systemd user / launchd / Task Scheduler or service), idle detection, battery, **opt-in model** (per-role toggles: inference host / batch / hours; default nothing enabled — CLAUDE.md §5.1), cap enforcement (cgroups v2; macOS/Windows equivalents; GPU caps are blunt), **live-adjustable caps**, kill switch, Python baseline per node. Linux rows full depth; **macOS/Windows rows docs-only** (validated with the first such member, Phase 4); packaging (Python + uv/pipx vs single binary; code-signing cost) at outline depth (Phase 4) | full (Linux) / outline | S-06 |
| R06 | Coordinator & schema | Postgres as a **separate compose project** on solarplexus (not the media stack; decide reuse-vs-new vs Immich's Postgres and record it), data dir disk, port, rights of the unattended user (docker group?); roster/heartbeat/capability schema (capability report carries only what the owner opted in); heartbeat interval → node-down threshold; queue pattern (`SKIP LOCKED`); fair share when contended per ADR-0001 (no quotas); identity-attributed API; **log policy: metadata only, never bodies** | full | — |
| R07 | Status page & identity | Grafana vs simple page; Caddy integration + config location; how identity headers reach the app; **required panels per ADR-0001**: pool capacity, utilisation, distance to next product threshold; contributions as thanks only, never counts or ranks; log policy as R06 | full | — |
| R08 | Chat front-end for Phase 1 | candidates with *current* licences at a pinned version (Open WebUI changed; LibreChat; others); zero-login via Tailscale identity; per-member history separation (ADR-0001); no prompt logging; deployable as a compose service behind Caddy. **Consumer: Phase 1 ships the chosen UI** (a friend cannot curl an API) | full | — |
| R09 | SharedLLM & alternatives | for SharedLLM, exo, GPUStack, prima.cpp, Ollama: latest release tag + date, licence at that tag, OS/GPU support matrix, whether it coordinates llama.cpp RPC workers, last-commit date — pre-work for the CLAUDE.md §6 Phase 5 mandate | outline | — |
| R10 | Hub integration points + Phase 3–5 outlines | Tdarr nodes, Immich ML offload, container caps on Linux/WSL2, politeness UI, dashboard; research-question lists for Phases 3–5 | outline | — |

### 6.2 Dossier template

Purpose → Facts (each: statement · source URL · date verified · version/commit if
version-dependent, or spike ID) → Spike results (summary + link to card and run file) →
Recommendations for the spec → Open questions → CLAUDE.md §4 credit rows to add (name · what
we take · license · author) → Change log.

### 6.3 Spike protocol (`docs/research/spikes/S-nn-slug.md`; `TEMPLATE.md` created in M0)

Card fields: ID · goal · node(s) · executor (`main-session` or `founder`) · **preconditions**
(AC power on ahnoway; Plex/Immich idle; optiplex 1-min load below the ceiling on the card; disk
free; no other spike running; Tailscale mode of each node recorded) · dependencies (which
Phase 0 steps / other spikes must be done) · exact commands · **cap** (values from Appendix B
and how enforced) · exception record (requested amount · duration · granted by · when) ·
expected signal · **abort criteria and what to watch** (load, temperature, `nvidia-smi`
memory, swap, Plex/Immich health) · **undo** (executed and confirmed at the end) · time box ·
result (numbers, version/commit pinned) · raw-evidence location (`docs/runs/S-nn-<date>.md`) ·
follow-ups.

Default caps are the Appendix B table. **Exceptions above the default** are requested per spike
*or per plan step*, granted by the founder, time-boxed, and written on the card / in the run
file and `status.md`. Spike code is **throwaway scratch** — it lives under the spike card's
folder or uncommitted scratch and is never committed under `agent/` or `coordinator/`.

Standing rules: optiplex production services, Postgres, and data disk are never touched;
listeners bind to the tailnet interface only (S-01 exception: iperf3 bound to the specific LAN
IP, never `0.0.0.0`, stopped after the run, recorded on the card); root on solarplexus only via
`splx-root`; root on optiplex is the founder's.

Planned spikes (prerequisites in brackets):
- **S-01** iperf3 + latency, all pairs, LAN path and tailnet path [tailnet leg after Phase 0
  steps 0–2; bandwidth exception: ≤60 s per pair, Plex idle; repeat when wired].
- **S-02** llama.cpp build/install per node at a pinned tag incl. GTX 970 on CUDA 12.2
  [ask (c) confirmed; optiplex leg allowed under Appendix B caps].
- **S-03** tiny-model RPC split ahnoway↔optiplex at default caps — mechanics + overhead vs a
  local run [S-02; (c)].
- **S-04** *thesis spike* [S-03; **exception required per node**]: a model that meets the §7
  criterion, split across 2–3 nodes; tok/s and GB numbers recorded.
- **S-05** Tailscale identity headers via `tailscale serve` on ahnoway (operator mode) [Phase 0
  step 0].
- **S-06** Linux mechanism probes on ahnoway at default caps: idle (logind / xprintidle),
  battery (upower), cgroup caps via `systemd-run --user`, live reload of a cap value — commands
  and measurements, **not an agent** [none].

### 6.4 Execution and verification

One researcher agent per dossier working from primary sources (web); **spikes are run by the
main session only** (agents do not get shells on the nodes); then adversarial fact-checkers
attempt to refute every dated claim (versions, flags, licence terms, plan limits), and a
completeness critic asks what is missing; the main session consolidates. Saved as
`.claude/workflows/research-sweep.js` (a Workflow-tool script) so a stale dossier can be re-run.
While spikes or plans run, `status.md` carries a "node in use by" line (written by the main
session, §9). Deliverable: dossiers
R00–R10 + spike cards + run files + a one-screen summary table in `docs/status.md`.

## 7. Specs & plans for Phases 1–2; outlines for 3–5 (design section 4, approved)

**Spec skeleton (all phases):** goal + exit criterion (CLAUDE.md's, sharpened into numbers
from dossiers) → architecture → components → data flow → error handling → acceptance tests →
out of scope → ADRs created/referenced.

- **Phase 1 — First shared model.** Topology from R03 (which node runs `llama-server`, which
  run `rpc-server`; solarplexus hosts the endpoint via Caddy even if the heavy lifting runs
  elsewhere; **if `llama-server` lands anywhere but solarplexus, that is an ADR** noting the
  CLAUDE.md §5.2 battery/idle implications for the endpoint node); model from R04; the chat UI
  from R08 as a compose service behind Caddy; `rpc-server` as user-level systemd units bound
  to the tailnet IP with linger enabled (executor per node from R03); caps default, raised by
  the owner for the demo via the exception mechanism; OpenAI-compatible endpoint on the
  ADR-0003 port. **"Impossible on one machine" (one definition, used by R04, S-04 and this
  acceptance):** model weights + KV cache at the chosen quantisation exceed the largest single
  node's VRAM + free RAM at demo time (today ≈ optiplex's 6 GB + ~19 GB). **Acceptance:** a
  completion from such a model, tok/s and GB numbers recorded; **no prompt or completion text
  in any log on any node** (grep after the test); **ADR-0004 split:** thesis accepted on the
  LAN trio; "a friend gets a completion across two houses" is the named follow-on, owner =
  founder, trigger = first member machine online.
- **Phase 2 — The roster.** Agent v0 in Python, **Linux only in this package** (macOS/Windows
  validated with the first such member, Phase 4): heartbeat + capability report (only what the
  owner opted in — a fresh agent reports `offers: none`); caps in a config file live-reloaded
  (ADR-0005); idle/battery detection; kill switch (`corvid stop` + a file flag). Coordinator
  v0: Postgres in a separate compose project on solarplexus + a small API; identity via
  Tailscale; log policy per R06. Status page v0 per R07. **Acceptance (numbers the Phase 2
  spec may tighten, not loosen):** all three nodes live on the map with capabilities; node-down
  visible within N = 3 × the heartbeat interval chosen in R06; a cap change takes effect
  within ≤ 5 s (measured with `systemd-cgtop`); kill switch stops all CORVID work within ≤ 2 s
  (cgroup empty); fresh agent reports `offers: none`; no prompt/content text in any log.
  Hub services (Postgres, API, status page, Caddy route, chat UI) are infrastructure, bounded
  by compose `cpus:`/`mem_limit:` set in the Phase 2 spec — the 10% default cap applies to
  CORVID *compute work* (inference, jobs, spikes), not to these. Member-facing guides wait for
  Phase 4; Phase 2 writes the founder runbook (`docs/runbooks/`).

**Plan format (`writing-plans`):** bite-sized tasks with exact paths, commands, expected
outputs; TDD for any code; each task tagged with an Appendix A executor; checkpoints; rollback
for any system change. Every plan opens with "Read: CLAUDE.md, docs/status.md, R0x…" (Phase 0
reads R00) + the Appendix A preflight, and closes with a verification checklist whose outputs
go to `docs/runs/` with a one-line summary proposed for `status.md`.

**Phases 3–5 outline** (`docs/superpowers/specs/phase-3-5-outline.md`): per phase — goal,
likely components, decisions required, research-question list, and what Phase 1–2 results will
probably change. No plans.

## 8. Skills & processes (design section 5, approved)

**Project skills (`.claude/skills/`):** `save-state` (rewrite the RESUME block + decisions
table in `status.md`; single-writer rule), `new-adr` (next-numbered ADR from
`docs/adr/TEMPLATE.md`, linked from `status.md`), `add-dependency` (licence + author looked
up; **CLAUDE.md §4 row added in the same commit**; compatibility noted), `spike` (card from
`docs/research/spikes/TEMPLATE.md`; enforces preconditions/cap/undo/tailnet bind; files results
into the dossier and `docs/runs/`), `remote-step` (the executor table, alias *names*, gotchas
such as `XDG_RUNTIME_DIR` for user units, and "root on optiplex = founder"; points to the
founder's private notes for everything §3.8 excludes).

**Hooks:** committed `.claude/settings.json` — `SessionStart` prints the top of
`docs/status.md`; `PostToolUse` on `*.py` edits runs `ruff format` + `ruff check`;
`PreToolUse` on Bash blocks **bind-like** uses of all-interfaces (`--host 0.0.0.0`,
`-H/--bind 0.0.0.0`, `0.0.0.0:`, unqualified `-p/--publish`, compose `ports:` without a host
IP) with the charter's "ADR or it doesn't ship" message, while allowing audits (`grep`, `rg`,
`ss`). Git-ignored `.claude/settings.local.json` — the optiplex guard: for commands addressed
to any of optiplex's names/IPs, block `sudo`, `su`, `doas`, `pkexec`, `psql`, `pg_*`, and
`:5432`, and any path on its off-limits disk. Hooks are guards, not proof.

**CI (`.github/workflows/ci.yml`, created in M0):** ruff; pytest as a smoke run until `agent/`
exists; `mkdocs build`; a bind-target lint over code/config dirs (compose `ports:` must carry a
host IP; systemd units and Python bind calls checked) with an allowlist keyed to an ADR number.

**Processes:** the superpowers chain — brainstorming (done) → `writing-plans` → **default:**
Opus runs `executing-plans` in its own session with checkpoints; `subagent-driven-development`
is allowed only for tasks with no node access (pure repo docs/code) → `verification-before-
completion` (run files + `status.md` summary) → `finishing-a-development-branch`. TDD for all
agent/coordinator code. Saved workflow `research-sweep` (M2); a `code-review` workflow arrives
with the first code (Phase 2 plan), not in this package. Git/CI at $0; docs-as-code (MkDocs
Material, ADRs, `status.md` as the single resume point; CLAUDE.md edits per §3.9); secrets and
§3.8 items never in this repo.

## 9. Sequencing and milestones

| # | Milestone | Output | Authored by | Plan executed by |
|---|---|---|---|---|
| M0 | Package accepted; repo initialised | this spec; `.gitignore`; `mkdocs.yml`; ADR + spike templates; skills + hooks scaffolded; CI; `.claude/workflows/` dir; first commit; **founder:** names identity/account, creates remote, first push | main session (+ founder steps) | — |
| M1 | Phase 0 | R00; `specs/…phase-0-handshake-design.md`; `plans/…phase-0-handshake.md`; ADR-0002 (Accepted); ADR-0003 (Proposed); ADR-0004 (Accepted) | main session | Opus (+ founder steps) |
| M2 | Research sweep | R01–R10; spike cards S-01…S-06; run files; `.claude/workflows/research-sweep.js`; `status.md` summary | main session (agents research; main session spikes) | — |
| M3 | Phase 1 | `specs/…phase-1-first-shared-model-design.md`; `plans/…phase-1…md`; ADR-0003 Accepted; topology ADR if needed | main session | Opus (+ founder) |
| M4 | Phase 2 | `specs/…phase-2-roster-design.md`; `plans/…phase-2…md`; ADR-0005 (contribution is a slider) | main session | Opus (+ founder) |
| M5 | Phase 3–5 outline | `specs/phase-3-5-outline.md` | main session | — |

**Ordering rules:** Phase 0 steps 0–2 execute **before** S-01's tailnet leg, S-05, and anything
that dials from solarplexus (step 3 is independent); M3/M4 wait for M2. M1's plan may otherwise be executed by Opus while M2 runs,
with the single-writer rule for `status.md` and the "node in use by" line: **before dispatching
a plan to Opus, the main session writes "node in use by: Opus (<plan>)" and clears it when the
run file lands; Opus never edits that line.**

## 10. Risks and open questions

- **GTX 970 / driver 535:** current llama.cpp CUDA builds may not support Maxwell with the
  installed driver; S-02 decides whether solarplexus runs CUDA layers, CPU layers, or only the
  endpoint. A driver upgrade is a founder decision (the media stack depends on it).
- **optiplex is production for another project:** every step there is capped and user-level;
  root steps are the founder's (ask (c) confirmed 2026-08-22).
- **House move (~late Aug/Sep 2026):** both hubs are on Wi-Fi until the founder re-plugs
  Ethernet after the move (date: founder's call). Wi-Fi numbers are worst-case for latency
  and lower bounds for throughput; S-01 repeats when wired.
- **Tailscale free-plan limits and the membership model:** verified at primary source in Phase 0
  step 4 / R02; may force ADR-0002 one way.
- **Unattended access on the hubs:** Tailscale SSH check-mode stalls non-interactive ssh today;
  Phase 0 step 0 decides the path before anything unattended runs.
- **Lock-out risk on the solarplexus Tailscale switch:** mitigated by founder presence, armed
  auto-rollback, and preconditions (§5 step 2).
- **macOS/Windows agent rows are unspiked** until a member with that OS volunteers.
- **Licences move** (e.g. chat front-ends): dossiers carry dates + versions; `add-dependency`
  re-checks.
- **Name:** CORVID is the working title; `corvid.commputer.xyz` is the public page slot
  (Cloudflare, currently 525/no origin). Decision parked; does not block the package.

## 11. Out of scope

Writing agent/coordinator code (spike scratch excepted, never committed under `agent/`);
installing CORVID software on a friend's machine (a friend installing Tailscale on a phone
call is in scope for ADR-0004(b)); member-facing guides; Phase 3–5 plans; native apps; any
CLAUDE.md edit outside §3.9.

## 12. Definition of done (for this package)

- R00–R10 exist, every fact sourced + dated (+ version where relevant) or spiked, `UNVERIFIED`
  items listed, CLAUDE.md §4 rows drafted.
- Phase 0, 1, 2 specs exist and each names measurable acceptance tests.
- Phase 0, 1, 2 plans exist, pass the `writing-plans` checklist, are self-contained, and every
  step carries an Appendix A executor / expected output / undo where applicable.
- Phase 3–5 outline exists.
- ADR-0002, ADR-0003, ADR-0004, ADR-0005 exist (status as in §9).
- Skills, hooks, CI, and the `research-sweep` workflow exist and have each been exercised once.
- `docs/status.md` summarises all of it and names the next step.

## Appendix A — Executors, handoff protocol, preflight (copy into every plan)

**Executor tags (exactly one per step):**
- `executor: main-session` — this (Fable) session: authors the package (M0, M2, M5, all specs
  and plans), runs spikes, writes `status.md`.
- `executor: Opus` — an Opus session on ahnoway running a plan unattended: user-level on
  ahnoway (incl. `tailscale set` via operator mode) and on optiplex; on solarplexus, user-level
  via the unattended alias **and root via `splx-root`** once the founder has loaded the key
  (steps needing it are tagged `executor: Opus (splx-root)`); Caddy and compose edits on
  solarplexus fall under that tag.
- `executor: founder` — sudo on ahnoway (beyond operator mode) and on optiplex; admin-console
  and browser actions; physical actions (Ethernet, console presence); granting cap exceptions;
  loading the ssh-agent key; naming the git identity / GitHub account, creating the remote,
  first push; phone calls to friends.

**Founder handoff protocol:** an Opus session reaching an `executor: founder` step halts and
prints a copy-pasteable block (what to run/do, where, expected output); the founder replies
"done" + output; Opus verifies with the named command before continuing, and the exchange goes
into the run file.

**Preflight (start of every plan):** `ssh -o BatchMode=yes <optiplex alias> true` → exit 0;
`ssh -o BatchMode=yes <solarplexus alias> true` → exit 0; for plans with `(splx-root)` steps,
`ssh -o BatchMode=yes splx-root true` → exit 0 (else founder loads the key); cap values for
this plan's scopes taken from Appendix B; `docs/status.md` "node in use by" shows no other
executor on the same node.

## Appendix B — Default cap table (~10% of each device; systemd `CPUQuota` is percent of one core)

| Node | CPU (`CPUQuota=`) | RAM (`MemoryMax=`) | VRAM (incl. CUDA context, as reported by `nvidia-smi`) | Other |
|---|---|---|---|---|
| ahnoway (12 threads, 16 GB, 8 GB VRAM) | `120%` | `1.6G` | ≤ 800 MB (`rpc-server --mem 800` / layer count) | `nice -n 19`; **AC power required**; scratch under the runner's home |
| solarplexus (4 threads, 16 GB, 4 GB VRAM) | `40%` | `1.6G` | ≤ 400 MB | `nice -n 19`; Plex/Immich idle for spikes; scratch on the storage pool, path on the card |
| optiplex (12 threads, 32 GB, 6 GB VRAM) | `120%` | `3.2G` | ≤ 600 MB | `nice -n 19`; 1-min load ceiling on the card; never its production surface |

Network: spikes that saturate the link (S-01) are an explicit, time-boxed exception (≤60 s per
pair, Plex idle). Disk: scratch only, sizes on the card, cleaned by the undo step. Anything
above these values is an exception (§6.3).
