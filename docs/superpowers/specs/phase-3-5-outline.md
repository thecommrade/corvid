# Phases 3–5 — Outline (not plans)

- **Date:** 2026-08-22 · **Status:** outline by design (package spec: Option A — Phases 0–2 at full depth; 3–5 as goals, likely components, decisions required, research questions, and what Phase 1–2 results will probably change)
- **Inputs:** `CLAUDE.md` §6 (phase definitions), §3.3 (job execution by node role), §5 (politeness), §10 (member promises); dossiers `R10` (hub integration points, container caps, WSL2/CUDA, gVisor, Folding@home), `R05` (agent platform matrix; packaging at outline depth), `R09` (SharedLLM, exo, GPUStack, prima.cpp, Ollama); ADR-0001/0003/0005/0007; spikes S-02/S-03/S-06.
- **Rule:** each phase below gets its own spec + plan (brainstorming → writing-plans) only when the previous phase's run file shows its acceptance met. Nothing here is a commitment to a mechanism.

## Phase 3 — Batch jobs ("the pool does work")

**Goal (CLAUDE.md §6):** submit → runs on someone else's idle machine, in a capped container → results back. First real workloads: a member's media transcode or a data pipeline.

**Likely components**
- **Executor inside the agent** (Linux first): claims from the Phase 2 queue (`claim()` with the fair-share rule), runs each job as a transient unit in `corvid.slice` that launches a container with `docker run --rm --cpus --memory --pids-limit --read-only -v <scratch>:/scratch --network none|tailnet-only` (R10 facts on `docker run` resource constraints), renews the lease, reports metadata-only results (exit code, seconds, bytes) — never stdout/stderr bodies.
- **Job kinds v1:** (a) `tdarr-node` — run the Tdarr Node container against the hub's existing Tdarr server (the hub already runs Tdarr; nodes join by `serverURL`; Tdarr is free but **not open source** → needs its own licence ADR before §4 lists it; R10); (b) `immich-ml` — run `immich-machine-learning` remotely and point the hub's Immich at it (AGPL; R10 facts on remote ML); (c) `ffmpeg` one-shots for a member's media; (d) `shell` jobs from an allow-listed image.
- **Result transport:** scratch dir on the worker → rsync/scp back to the hub's pool (or the member's chosen destination later); artifacts never in Postgres.
- **Windows/WSL2 nodes:** agent runs in WSL2 with Docker + CUDA (R10 WSL2 facts); macOS nodes do not run containers (CLAUDE.md §3.3) — CPU-only sandboxed jobs later.
- **Politeness enforcement for jobs:** run only when `is_idle_enough` (ADR-0007), never on battery unless allowed, pause on AC loss, hard kill via slice.

**Decisions required (ADRs):** container runtime and isolation level (Docker + caps v1; gVisor as the upgrade path when less-trusted workloads arrive — R10); the Tdarr licence stance; result storage layout on the pool; job kinds allow-list and who may submit which kind (ADR-0001: everyone, no quotas); Windows packaging (Task Scheduler per R05) vs WSL2-only for jobs.

**Research questions:** exact `docker run` flags that bind-mount only scratch and drop host access (`--security-opt no-new-privileges`, `--cap-drop ALL`, user namespaces?); GPU passthrough in containers on the RTX nodes (`--gpus`, NVIDIA container toolkit exists only on the hub today); Tdarr node auth/API keys and whether a node can be capped; Immich ML container RAM/VRAM needs; transfer sizes for transcodes over home uplinks (S-01 numbers); how the Phase 2 executor reports progress without logging content.

**What Phase 1–2 results will change:** if S-01/S-03 show Wi-Fi/tailnet throughput is low, media jobs must stage inputs locally first (pull from the hub once) — design jobs around *compute-heavy, transfer-light*; if Phase 2's fairness/lease code proves solid, Phase 3 is mostly the executor + one container profile.

## Phase 4 — Politeness UI + dashboard + members ("the pool is trustworthy")

**Goal:** a non-technical friend installs the agent, understands it, and controls it without the founder present; the thank-you board exists; idle/battery/kill are visible.

**Likely components**
- **Tray / menu-bar presence** showing state (idle/active/paused/killed), the slider (ADR-0005) and the kill switch (CLAUDE.md §11) — Linux (tray via AppIndicator/StatusNotifier), macOS (menu bar; LaunchAgent per R05), Windows (tray; Scheduled Task per R05; Job Objects for caps).
- **Installers:** one per OS (R05 packaging at outline depth: `uv tool install corvid-agent` + a script that registers the unit/LaunchAgent/Task; no code signing in v1 → Gatekeeper/SmartScreen copy in the guide); the onboarding index card: 1) Tailscale invite, 2) agent installer, 3) bookmark the site.
- **Member guides** (`docs/members/`, Plex-guide tone, one page per OS, screenshots).
- **Dashboard:** the Phase 2 status page grows the thank-you board (names only), history charts from `heartbeat` (7-day), per-owner private view ("your machines") — never per-member public counts (ADR-0001); Grafana stays deferred unless the founder wants it (R07).
- **Presence providers for macOS (IOKit `HIDIdleTime`) and Windows (`GetLastInputInfo`)**, battery via psutil on both (R05); `ext-idle-notify-v1` helper for Wayland.
- **Leftovers:** Folding@home team CORVID as an opt-in job kind (R10; CLAUDE.md §10).

**Decisions required:** tray toolkit per OS; signing (stay $0 and document the warnings, or pay later); default slider after opt-in (ADR-0005 says 10 %); what the public landing page at `corvid.commputer.xyz` says (CLAUDE.md §10 copy; Cloudflare Pages at $0 — status.md finding 9).

**Research questions:** Gatekeeper/SmartScreen behaviour for unsigned `uv`-installed tools; macOS TCC prompts for idle detection; Windows Task Scheduler + tray interaction in user session; how members see *their* heartbeat data privately; accessibility of the tray UI.

**What Phase 1–3 results will change:** the agent's config schema (Phase 2) must already hold every knob the tray exposes — if Phase 2 found the schema lacking, Phase 4 starts with a schema ADR.

## Phase 5 — Converge, don't diverge

**Goal:** decide whether CORVID adopts/contributes to SharedLLM for inference coordination and Nomad for scheduling, or keeps its tiny coordinator — with an ADR either way (CLAUDE.md §3.2/§3.3 mandate).

**Likely components:** evaluation matrix from `R09` (licence at tag, OS/GPU support, does it coordinate llama.cpp RPC workers, last-commit date, maturity) refreshed at decision time; a spike running SharedLLM against the Phase 1 fleet; a Nomad single-binary trial on the three build nodes (BUSL 1.1 note); a contribution plan (issues/PRs) if adopted.

**Decisions required (ADRs):** SharedLLM adopt/contribute/decline; Nomad adopt/decline; whether CORVID's coordinator stays a "table and a loop" (CLAUDE.md §3.3) — only pain justifies more.

**Research questions:** SharedLLM's current release cadence and whether it speaks the same llama.cpp RPC protocol version we pin; exo's NVIDIA status (community fork) and macOS-only strengths for member Macs; GPUStack's macOS worker support (watch list); prima.cpp maturity; Ollama's RPC story (the UX bar to meet); Headscale readiness if the 6-user ceiling is hit (ADR-0002).

**What Phase 1–4 results will change:** everything here keys off Phase 1's measured RPC numbers and Phase 2/3's operational pain; if the tiny coordinator never hurts, Phase 5 may be a one-paragraph ADR.

## Cross-phase research list (open, to be scheduled)

- ACL baseline edit before the first member (ADR-0002; R02) and member-device tagging stance (ADR-0002 amendment: untagged).
- Cross-house path numbers (S-01 `UNVERIFIED` until a member machine exists; ADR-0004).
- CUDA per-node builds vs Vulkan prebuilt for Phase 1.1 (R03 rec 2–4 vs S-02 evidence).
- IO caps via the user@.service delegation drop-in (R05 rec 3).
- Hub Ethernet after the move (R00/R01) — re-measure S-01.
- Open WebUI member chat (Part B Task 10) and its ADR.
