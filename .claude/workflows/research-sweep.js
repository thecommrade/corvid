export const meta = {
  name: 'research-sweep',
  description: 'CORVID research sweep: one researcher per dossier, adversarial refutation of every dated fact, completeness critic (spec §6.4)',
  whenToUse: 'Run for M2, or to refresh a stale dossier: args = { dossiers: ["R03"], date: "YYYY-MM-DD" }',
  phases: [
    { title: 'Research', detail: 'one agent per dossier, primary sources only' },
    { title: 'Refute', detail: 'one skeptic per fact' },
    { title: 'Gaps', detail: 'completeness critic per dossier' },
  ],
}
const DATE = (args && args.date) || 'UNDATED'
const MAX_REFUTED = (args && args.maxFactsRefuted) || 20
const ONLY = (args && args.dossiers) || null

const FACTS = { type: 'object', properties: {
  dossier: { type: 'string' },
  facts: { type: 'array', items: { type: 'object', properties: {
    id: { type: 'string' }, statement: { type: 'string' }, source_url: { type: 'string' },
    date_verified: { type: 'string' }, version: { type: 'string' },
    confidence: { type: 'string', enum: ['verified', 'unverified'] } },
    required: ['id', 'statement', 'source_url', 'date_verified', 'confidence'] } },
  recommendations: { type: 'array', items: { type: 'string' } },
  open_questions: { type: 'array', items: { type: 'string' } },
  credits: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, what: { type: 'string' }, license: { type: 'string' },
    author: { type: 'string' }, source_url: { type: 'string' } },
    required: ['name', 'what', 'license', 'author', 'source_url'] } } },
  required: ['dossier', 'facts', 'recommendations', 'open_questions', 'credits'] }
const VERDICT = { type: 'object', properties: {
  fact_id: { type: 'string' }, refuted: { type: 'boolean' }, reason: { type: 'string' },
  corrected_statement: { type: 'string' }, source_url: { type: 'string' } },
  required: ['fact_id', 'refuted', 'reason'] }
const GAPS = { type: 'object', properties: { missing: { type: 'array', items: { type: 'string' } } }, required: ['missing'] }

const COMMON = `You are researching for CORVID, a friends-scale compute co-op (Tailscale mesh; llama.cpp RPC inference; Python agent + Postgres coordinator; Linux build fleet: a laptop with an RTX 2070 Super 8 GB, a hub with a GTX 970 4 GB on driver 535/CUDA 12.2 and Tailscale in userspace mode, a second node with an RTX 3050 6 GB on CUDA 13.1; friends on macOS/Windows later). Use PRIMARY sources only (official docs, the project's own repo/README/LICENSE at a pinned tag, vendor pricing pages). For every fact give: a precise statement, the exact source URL, today's date ${DATE} as date_verified, and the version/tag/commit it applies to when version-dependent. If you could not verify something from a primary source, include it with confidence "unverified" — never guess silently. Prefer fewer, sharper facts a plan can cite over many vague ones. Also list recommendations for the spec, open questions, and the credit rows (name, what we take, license at that tag, author, source URL) for anything CORVID would ship or rely on.`

const DOSSIERS = [
  { id: 'R01', title: 'Fleet & network', qs: `Only the documentation part of R01 (measurements come from spike S-01): Tailscale DERP/NAT facts relevant to home networks (direct vs relayed, UPnP/NAT-PMP, what 'tailscale netcheck' fields mean); what latency/bandwidth llama.cpp RPC needs per token (from the llama.cpp RPC README); how Wi-Fi vs wired affects that. Seeds: https://tailscale.com/kb/1257/connection-types , https://tailscale.com/kb/1232/derp-servers , https://github.com/ggml-org/llama.cpp/blob/master/tools/rpc/README.md` },
  { id: 'R02', title: 'Tailscale: membership, ACLs, DNS, identity', qs: `Personal plan user and device limits today; invite vs node-sharing semantics (is sharing one-directional? does a sharee get a per-request identity usable for zero-login?); ACL basics incl. tags, ssh section check vs accept; MagicDNS + split DNS behaviour with an existing LAN resolver; key expiry default and disabling; 'tailscale serve' identity headers (exact header names) vs 'tailscale whois'; 'tailscale set --operator'; userspace networking limits; Tailscale SSH. Seeds: https://tailscale.com/pricing , https://tailscale.com/kb/1084/sharing , https://tailscale.com/kb/1018/acls , https://tailscale.com/kb/1081/magicdns , https://tailscale.com/kb/1028/key-expiry , https://tailscale.com/kb/1312/serve , https://tailscale.com/kb/1080/cli , https://tailscale.com/kb/1112/userspace-networking , https://tailscale.com/kb/1193/tailscale-ssh` },
  { id: 'R03', title: 'llama.cpp RPC on this fleet', qs: `Latest release tag and date; whether release binaries for Linux include rpc-server (and which CUDA versions/backends they ship for Linux), and whether the official Docker images include rpc-server; how to build with -DGGML_RPC=ON (+CUDA) and the CUDA toolkit/driver requirements; CUDA support for Maxwell cc 5.2 in current builds and what CUDA 12.x toolkit still supports it; rpc-server flags at that tag (host/port/mem/threads/cache) and the security warning; llama-server --rpc semantics and how layers are split across RPC devices; which llama-server/rpc-server flags disable request/prompt logging; llama-bench --rpc; systemd user unit + linger requirements; /dev/nvidia* permissions for a non-root service user. Seeds: https://github.com/ggml-org/llama.cpp/releases , https://github.com/ggml-org/llama.cpp/blob/master/tools/rpc/README.md , https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md , https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md , https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/` },
  { id: 'R04', title: 'Model selection for Phase 1', qs: `Candidate open-weight instruct models and their GGUF quantisations with file sizes, ranked on a NAMED dated basis (e.g. the current Open LLM Leaderboard or LMArena/Artificial Analysis snapshot — cite which), that satisfy: weights + KV cache at the chosen quant EXCEED ~25 GB (the largest single node's 6 GB VRAM + ~19 GB free RAM) so the model is impossible on one node, yet fit the pool (≈18 GB VRAM + ≈63 GB RAM) — give the GB arithmetic incl. KV cache for 4k and 8k context; plus a fallback list of models that exceed 8 GB VRAM; model licences (name, gated?) for §4 rows. Seeds: https://huggingface.co/models?library=gguf&sort=trending , model cards of Llama 3.x 70B, Qwen3 32B/30B-A3B, Gemma 3 27B, Mistral Small, DeepSeek-R1 distills; https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md for KV sizing notes` },
  { id: 'R05', title: 'Agent platform matrix', qs: `Linux (full depth): systemd user services + linger; idle detection on Wayland (logind IdleHint, org.freedesktop.ScreenSaver GetSessionIdleTime, KDE/GNOME specifics) and X11 (xprintidle); battery/AC via upower or /sys/class/power_supply; cgroup v2 resource control via systemd-run --user (CPUQuota, MemoryMax, IOWeight) and LIVE changes via systemctl set-property; GPU caps realities (no compute-share on consumer NVIDIA; VRAM via app limits); kill switch patterns. macOS and Windows (docs-only): launchd LaunchAgents; Task Scheduler / Windows service; idle (IOKit HIDIdleTime; GetLastInputInfo); battery (pmset; SYSTEM_POWER_STATUS); caps (taskpolicy/nice; Job Objects). Opt-in model design notes. Packaging at outline depth: Python + uv/pipx vs PyInstaller single binary; macOS notarization and Windows code-signing costs. Seeds: https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html , https://www.freedesktop.org/software/systemd/man/latest/systemd-run.html , https://www.freedesktop.org/software/systemd/man/latest/loginctl.html , https://upower.freedesktop.org/docs/ , https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html , https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-getlastinputinfo , https://learn.microsoft.com/windows/win32/procthread/job-objects , https://docs.astral.sh/uv/` },
  { id: 'R06', title: 'Coordinator & schema', qs: `Postgres in Docker Compose as a separate project (resource limits via deploy.resources / cpus / mem_limit, data dir bind mounts, healthchecks); queue pattern with SELECT ... FOR UPDATE SKIP LOCKED; heartbeat/roster schema patterns; fair-share when contended (max-min) with NO quotas; identity from Tailscale (whois/headers) for an API; log policy (metadata only). Seeds: https://docs.docker.com/reference/compose-file/deploy/ , https://docs.docker.com/reference/compose-file/services/ , https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE , https://hub.docker.com/_/postgres` },
  { id: 'R07', title: 'Status page & identity', qs: `Grafana licence (AGPL) and OSS vs Enterprise features; lightweight alternatives; how identity headers from 'tailscale serve' or whois reach an app behind Caddy; Caddy reverse_proxy + handle_path basics and its licence; what a 'live map' of nodes needs (heartbeat age, capabilities, pool capacity/utilisation/threshold panels per ADR-0001). Seeds: https://github.com/grafana/grafana/blob/main/LICENSE , https://caddyserver.com/docs/caddyfile/directives/reverse_proxy , https://github.com/caddyserver/caddy/blob/master/LICENSE` },
  { id: 'R08', title: 'Chat front-end for Phase 1', qs: `Current licences (at a pinned version) of Open WebUI, LibreChat, Lobe Chat, Hollama, and any other mature OpenAI-compatible chat UI; whether each supports header-based/trusted-proxy auth (zero-login via Tailscale identity headers); per-user history isolation; disabling prompt logging/telemetry; deployable as a single compose service. Seeds: https://github.com/open-webui/open-webui/blob/main/LICENSE , https://docs.openwebui.com/ , https://github.com/danny-avila/LibreChat/blob/main/LICENSE , https://www.librechat.ai/docs , https://github.com/lobehub/lobe-chat/blob/main/LICENSE` },
  { id: 'R09', title: 'SharedLLM & alternatives', qs: `For each of SharedLLM, exo, GPUStack, prima.cpp, Ollama: latest release tag + date, licence at that tag, OS/GPU support matrix, whether it coordinates llama.cpp RPC workers or has its own sharding, last-commit date, maturity signals. Seeds: the projects' GitHub repos (search them), https://github.com/exo-explore/exo , https://github.com/gpustack/gpustack , https://github.com/Lizonghang/prima.cpp , https://github.com/ollama/ollama` },
  { id: 'R10', title: 'Hub integration points + Phase 3–5 outlines', qs: `Tdarr node model (how a remote Tdarr node joins a server; licence/terms — Tdarr is not open source; what that means for §4); Immich machine-learning container run remotely (config, GPU support, licence AGPL); Docker resource caps for batch jobs (cpus, memory, gpus, no host mounts beyond scratch); WSL2 + Docker + CUDA on Windows; gVisor as an upgrade path; Folding@home team setup basics. Seeds: https://docs.tdarr.io/ , https://immich.app/docs/guides/remote-machine-learning , https://docs.docker.com/engine/containers/resource_constraints/ , https://docs.nvidia.com/cuda/wsl-user-guide/ , https://gvisor.dev/docs/ , https://foldingathome.org/` },
]
const todo = ONLY ? DOSSIERS.filter(d => ONLY.includes(d.id)) : DOSSIERS
log(`research-sweep: ${todo.map(d => d.id).join(', ')} (date ${DATE})`)

const researchPrompt = d => `${COMMON}\n\nDOSSIER ${d.id} — ${d.title}.\nKey questions (each must yield citable facts): ${d.qs}\nReturn the structured output; fact ids must be ${d.id}-F1, ${d.id}-F2, …`
const refutePrompt = (d, f) => `You are an adversarial fact-checker. Try to REFUTE this claim using the cited primary source (fetch it) and, if needed, one other primary source. Claim (${f.id}, from dossier ${d.id} ${d.title}): "${f.statement}" — cited source: ${f.source_url} — version: ${f.version || 'n/a'}. Decide refuted=true if the source does not support the claim as stated, the claim is outdated for the stated version, or the source is not primary. If refuted, give the corrected statement and the URL that supports it. If you cannot reach the source, refuted=true with reason "source unreachable". Be strict.`
const gapsPrompt = (d, r) => `You are a completeness critic for dossier ${d.id} — ${d.title}. Key questions it had to answer: ${d.qs}\nHere are the facts it produced:\n${r.facts.map(f => `- ${f.id}: ${f.statement} [${f.confidence}]`).join('\n')}\nList what is MISSING for a plan writer to use this dossier without further research (specific questions, not generalities). If nothing material is missing, return an empty list.`

const results = await pipeline(
  todo,
  d => agent(researchPrompt(d), { label: `research:${d.id}`, phase: 'Research', schema: FACTS }),
  (r, d) => {
    if (!r) return null
    const facts = r.facts.slice(0, MAX_REFUTED)
    if (r.facts.length > MAX_REFUTED) log(`${d.id}: ${r.facts.length - MAX_REFUTED} facts beyond the refutation cap are left unverified`)
    return parallel(facts.map(f => () => agent(refutePrompt(d, f), { label: `refute:${f.id}`, phase: 'Refute', schema: VERDICT })))
      .then(vs => ({ research: r, verdicts: vs.filter(Boolean) }))
  },
  (x, d) => x ? agent(gapsPrompt(d, x.research), { label: `gaps:${d.id}`, phase: 'Gaps', schema: GAPS }).then(g => ({ ...x, gaps: g })) : null,
)
const out = {}
todo.forEach((d, i) => { out[d.id] = results[i] })
return out
