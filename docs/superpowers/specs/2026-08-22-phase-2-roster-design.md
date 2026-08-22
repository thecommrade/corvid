# Phase 2 — The Roster: Design Spec

- **Date:** 2026-08-22
- **Status:** Ready for execution (scope approved as package spec §7 on 2026-08-22; decisions grounded in R05, R06, R07, R02, S-06, R00)
- **Author:** main-session (Fable) with the founder · **Executor of the plan:** Opus session + founder steps
- **Related:** `CLAUDE.md` §3.3 (agent + coordinator), §3.4 (observability), §5 (politeness), §6 (Phase 2), §11 (zero-login); ADR-0001 (commons, no quotas, no logging), ADR-0002 (membership; amended here: member devices untagged), ADR-0003 (endpoints; amended here: loopback backends behind Caddy), ADR-0005 (contribution is a slider — written with this spec), ADR-0007 (presence & GPU sharing — written with this spec); dossiers `R05`, `R06`, `R07`, `R02`; spike `S-06`; pending `S-05`
- **Notation:** `Rnn-Fk` = dossier facts; "§N" = this spec; "CLAUDE.md §N" = the charter.

## 1. Goal and exit criterion

A live map of the co-op: an agent on each build node reports liveness and *opted-in* capabilities into a Postgres roster on the hub, a status page shows the pool, the owner's slider changes caps live, and the kill switch stops all CORVID work on a machine instantly.

**Exit (CLAUDE.md §6 Phase 2, with numbers):** all three build nodes on the map with capabilities; **heartbeat every 10 s; `live` < 10 s, `stale` < 30 s, `down` ≥ 30 s (N = 3 × interval)**; a cap change takes effect **≤ 5 s** (S-06 measured 3 ms); the kill switch stops all CORVID work **≤ 2 s** (S-06: 49 ms) and nothing survives (control-group kill); a fresh agent reports `offers: none`; no prompt/content text in any log.

## 2. Evidence this spec stands on

| Fact | Source |
|---|---|
| Per-user systemd service + `loginctl enable-linger`; all work in one user slice (`corvid.slice`, `KillMode=control-group`); jobs as transient units `systemd-run --user --slice=corvid.slice -p CPUQuota… -p CPUWeight=idle -p IOSchedulingClass=idle -p Nice=19`; live slider = `systemctl --user set-property corvid.slice …` (immediate, persisted) | R05 rec 1–3; S-06 (3 ms; 99 % → 29 %; stop 49 ms) |
| Idle detection is desktop-specific: logind `IdleHint` (works on the founder's KDE Wayland session as a hint), `org.freedesktop.ScreenSaver.GetSessionIdleTime` unsupported on KDE Wayland, GNOME Mutter D-Bus where present, `ext-idle-notify-v1` for Wayland generally, `xprintidle` on X11 → provider chain with an explicit **UNKNOWN** state | R05 rec 4; S-06; R05 open questions |
| Battery/AC: `psutil.sensors_battery()` with sysfs fallback (`ADP*`/`AC*` online, `BAT*` status) | R05 rec 5; S-06 |
| GPU is all-or-nothing per job/time window on consumer NVIDIA (no MIG/MPS/cgroup GPU controller); VRAM ceilings are coordinator-planned | R05 rec 6 |
| Postgres as its own compose project, pinned full tag, bind mount, `deploy.resources.limits`, `pg_isready` healthcheck, migrations outside `initdb.d`, never publish `5432` to all interfaces | R06 rec 1–5 |
| Queue: `UPDATE … WHERE id = (SELECT … FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *`, partial index, `NOTIFY job_queued`, lease + reaper, `timestamptz` everywhere, `clock_timestamp()` in long transactions | R06 rec 6–10 |
| Fair share with no quotas = per-member round-robin at claim (max-min); one member alone gets the whole pool | R06 rec 11; ADR-0001 |
| Identity: trust Tailscale identity (serve headers strip spoofed copies; `whois` by source IP only when the hub is in kernel mode); tagged devices get no identity → member devices must stay untagged; coordinator listens on loopback; log metadata only | R06 rec 12–14; R07 rec 3–4; R07-F21/F22/F24/F26 |
| Status page v0 = server-rendered (FastAPI + Jinja2), not Grafana; live/stale/down by heartbeat age; pool capacity = Σ offered (capped) resources over live nodes; no per-member sortable tables; Caddy on the hub is a host package (admin `:2019`, active) → `import` drop-in + `systemctl reload caddy` | R07 rec 1–2, 5; R00-F7 |
| Ports 8091 (API) and 8092 (status) on the hub (ADR-0003); hub kernel-mode + linger after Phase 0 step 2 | ADR-0003; R00-F8 |

## 3. Decisions

1. **Agent v0 — Linux only in this package** (macOS/Windows validated with the first such member, Phase 4). Python ≥ 3.12; per-user service `~/.config/systemd/user/corvid-agent.service` (`WantedBy=default.target`, linger on always-on nodes); **all CORVID work lives in `corvid.slice`**; the agent itself runs in `corvid.slice` too so the kill switch takes it down. Dev install from the repo (`.venv`, editable); packaging v1 for members (`uv tool install corvid-agent`, one install script per OS) is Phase 4's problem — recorded in R05 rec 9.
2. **Config** `~/.config/corvid/agent.toml` (BOINC-style names, ADR-0005):
   ```toml
   [offers]      # CLAUDE.md §5.1 — nothing on by default
   inference_host = false
   batch_jobs = false
   gpu_allowed = false
   disk_donate = false
   [caps]        # the slider (ADR-0005); percentages are of the whole machine
   cpu_quota_pct = 10
   mem_max_gb = 1.6
   vram_cap_mb = 800
   io_idle = true
   [politeness]  # CLAUDE.md §5.2
   run_if_user_active = false
   idle_minutes = 5
   run_on_batteries = false
   suspend_cpu_usage_pct = 25
   schedule = []            # e.g. ["22:00-07:00"]
   [coordinator]
   url = "http://solarplexus.<tailnet>.ts.net"
   heartbeat_seconds = 10
   ```
   **Live reload:** the agent watches the file (inotify, mtime poll every 2 s as backstop) and applies `caps` with `systemctl --user set-property corvid.slice CPUQuota=<pct×cores>% MemoryMax=<gb>G` — takes effect within ≤ 5 s (S-06: ms). Invalid config → keep last good, log, report `config_error` in the heartbeat.
3. **Kill switch** (`corvid stop`, and a tray action in Phase 4): writes `~/.config/corvid/KILL`, then `systemctl --user stop corvid.slice` — every CORVID process on the machine is gone within ≤ 2 s; the agent refuses to start work while the flag exists; `corvid start` removes it. A second path for the paranoid: `systemctl --user stop corvid.slice` alone is enough.
4. **Presence (ADR-0007):** provider chain → logind `IdleHint`/`IdleSinceHint`; `ext-idle-notify-v1` helper (Wayland; the plan spikes pywayland vs a tiny helper); GNOME Mutter `IdleMonitor`; `xprintidle` (X11); otherwise **UNKNOWN**. **UNKNOWN never counts as idle** (work only runs when a provider reports idle ≥ `idle_minutes`, or the owner set `run_if_user_active=true`). Battery: `psutil.sensors_battery()` → sysfs fallback; on AC loss with `run_on_batteries=false` the agent pauses work immediately (stops job units, keeps heartbeating with `on_battery=true`).
5. **GPU policy (ADR-0007):** temporal, all-or-nothing per job; `gpu_allowed=false` by default; the coordinator plans VRAM via `--tensor-split`/model choice (no server-side cap at b10581). Phase 2 only *reports* GPU (name, VRAM total/free, driver) when `gpu_allowed=true`.
6. **Heartbeat:** `POST /api/v1/heartbeat` every 10 s with `{node_id, agent_version, os, arch, hostname_alias, offers, caps_effective, presence: idle|active|unknown, on_battery, gpu?, load1, mem_free_gb, disk_free_gb?, state: ok|paused|killed|config_error}` — capabilities carry **only opted-in roles**; a fresh install sends `offers: {}` (reported as `offers: none`). `node_id` is generated once (`uuid4`) and stored in `~/.config/corvid/node_id`; the owner identity comes from the request's Tailscale identity, never from the payload.
7. **Coordinator — separate compose project** `corvid-coordinator` on the hub (`deploy/coordinator/compose.yaml`, `name: corvid-coordinator`): `db` = `postgres:18.x` pinned full tag, bind mount `/srv/corvid/pg:/var/lib/postgresql`, `shm_size: 256mb`, `deploy.resources.limits: {cpus: "1.0", memory: 1g, pids: 200}`, healthcheck `pg_isready -U corvid -d corvid`, `command:` with `-c log_statement=none -c log_min_duration_statement=-1 -c log_connections=off -c log_disconnections=off`, **no published port** (internal network only); `api` = FastAPI + uvicorn + psycopg 3, `ports: "127.0.0.1:8091:8091"` (loopback only — behind Caddy), `depends_on: db: condition: service_healthy`, `deploy.resources.limits: {cpus: "1.0", memory: 512m}`; secrets in `/srv/corvid/coordinator.env` (mode 0600, outside git). Migrations: plain SQL in `db/NNNN_*.sql` applied by the API at startup in order with a `schema_migrations` table (idempotent); `initdb.d` only creates role/db.
8. **Schema v0** (all times `timestamptz`):
   - `node(node_id uuid PK, owner_login text NOT NULL, display_name text, os text, arch text, agent_version text, offers jsonb NOT NULL DEFAULT '{}', caps jsonb NOT NULL DEFAULT '{}', presence text, on_battery bool, gpu jsonb, load1 real, mem_free_gb real, state text, first_seen timestamptz NOT NULL DEFAULT now(), last_seen timestamptz NOT NULL)`; upsert `INSERT … ON CONFLICT (node_id) DO UPDATE SET last_seen=EXCLUDED.last_seen, …`; state derived at read time: `CASE WHEN last_seen > now()-interval '10 seconds' THEN 'live' WHEN last_seen > now()-interval '30 seconds' THEN 'stale' ELSE 'down' END`.
   - `heartbeat(node_id uuid, at timestamptz, payload jsonb)` — 7-day retention (reaper), used for the thank-you board and charts later; payload = metadata only.
   - `job(id bigserial PK, owner_login text NOT NULL, kind text NOT NULL, spec jsonb NOT NULL, state text NOT NULL DEFAULT 'queued', priority int NOT NULL DEFAULT 0, run_after timestamptz, claimed_by uuid, claimed_at timestamptz, lease_until timestamptz, attempt int NOT NULL DEFAULT 0, created_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz, result jsonb)` with partial index `job_queued_idx ON job (priority DESC, created_at) WHERE state='queued'`; claim = R06 rec 6's single statement; `AFTER INSERT` trigger `NOTIFY job_queued`; reaper re-queues expired leases (`attempt+1`). **Phase 2 builds the queue shape and claim; execution is Phase 3.**
   - **Fair share (ADR-0001):** the claim picks the next job from the member with the **fewest running jobs** (tie → oldest) = per-member round-robin / max-min; no quotas, no limits per member; one member alone gets everything.
   - `threshold(name text PK, needs jsonb, product text, note text)` — the "thresholds, not timelines" table the status page reads (e.g. `{"name":"27B model","needs":{"vram_plus_ram_gb":30},"product":"private AI (Phase 1 model)"}`).
   - `schema_migrations(version int PK, applied_at timestamptz)`.
9. **API** (FastAPI, loopback `:8091`): `POST /api/v1/heartbeat`, `GET /api/v1/nodes`, `GET /api/v1/pool` (capacity/utilisation/thresholds), `POST /api/v1/jobs`, `GET /api/v1/jobs?mine`, `GET /api/v1/whoami` (returns the caller identity; also the Caddy `forward_auth` target), `GET /health`, `GET /metrics` (aggregate counters only). Every route except `/health` requires an identity.
10. **Identity plumbing (ADR-0002/0003 amendments):** **Caddy is the only tailnet-facing listener** on the hub (after Phase 0 step 2: `bind <hub-tailnet-ipv4>`); backends bind `127.0.0.1` (`:8090`–`:8093`). Caddy `forward_auth` → `/api/v1/whoami`, which resolves the client's tailnet IP with `tailscale whois --json <ip>` (local tailscaled socket; kernel mode required) and injects `X-Corvid-User` (login) and `X-Corvid-Name` for downstream apps; no header → **401**. Fallback if S-05 shows it is simpler and reliable: `tailscale serve` identity headers (`Tailscale-User-Login`) with Caddy behind it. **Member devices are never tagged** (tags suppress identity); tags go on hubs only — ADR-0002's ACL baseline is expressed with users/`autogroup:member` for member devices. Agents authenticate as their owner via the same mechanism (heartbeats come from the member's own machine on the tailnet).
11. **Status page v0** (FastAPI + Jinja2 template, loopback `:8092`, Caddy `/status`): panels — **live map** (node alias, owner display name, state live/stale/down, presence/battery flags, opted-in offers and capped capabilities), **pool capacity** (Σ over live nodes of offered, capped CPU cores / RAM / VRAM) and **utilisation** (running jobs, inference slots busy), **distance to next threshold** (from `threshold`), **thank-you list** (member display names who contributed in the last 7 days — names only, no numbers, no ranks; ADR-0001). Refresh every 10 s (`<meta http-equiv="refresh">` or htmx). No per-member sortable tables, ever.
12. **Logging posture:** Postgres settings as in D7; API/status/agent logs carry metadata only (timestamp, path, status, latency, node_id) — never bodies, never identity values beyond Caddy's default access log; Caddy JSON log without bodies; agent never logs job payloads.
13. **Caps mechanics on Linux:** `corvid.slice` unit file (`~/.config/systemd/user/corvid.slice`) holds `CPUQuota`/`MemoryHigh`/`MemoryMax` from the slider; jobs run as transient units in the slice with `CPUWeight=idle IOSchedulingClass=idle Nice=19`; IO bandwidth caps need a one-time **root drop-in** `/etc/systemd/system/user@.service.d/corvid.conf` (`[Service]\nDelegate=pids memory cpu io`) — optional founder step; until then `IOSchedulingClass=idle` suffices.
14. **§4 credits (same commit as the dependency):** PostgreSQL (PostgreSQL License) · postgres Docker Official Image (MIT Dockerfiles) · Docker Compose (Apache-2.0) · psycopg 3 (LGPL-3.0, dynamic import) · FastAPI (MIT) · uvicorn (BSD-3) · Jinja2 (BSD-3) · psutil (BSD-3) · uv (MIT/Apache-2.0) · htmx (0BSD) if used · idea credits: BOINC (preferences names), Hadoop Fair Scheduler / DRF (fair share), Kubernetes leases.
15. **Founder runbook** `docs/runbooks/coordinator.md`: start/stop/backup (`pg_dump` nightly to the pool), migrations, logs, how to read the map; access details stay in the founder's private notes.

## 4. Components

| Where | Component | Path / unit | Binds | Caps |
|---|---|---|---|---|
| each node | agent v0 (`corvid-agent`) | repo `agent/` (package `corvid_agent`: `config.py`, `presence.py` (providers), `power.py`, `caps.py` (slice control), `heartbeat.py`, `killswitch.py`, `cli.py` → `corvid` entrypoint); unit `~/.config/systemd/user/corvid-agent.service` in `corvid.slice`; slice `~/.config/systemd/user/corvid.slice` | outbound only | slider |
| hub | coordinator | repo `coordinator/` (FastAPI app: `main.py`, `identity.py`, `db.py`, `roster.py`, `queue.py`, `status.py` + `templates/status.html`), `db/0001_roster.sql`, `0002_queue.sql`, `0003_thresholds.sql`; `deploy/coordinator/compose.yaml`, `deploy/coordinator/Dockerfile`; secrets `/srv/corvid/coordinator.env` | `127.0.0.1:8091` (api), `127.0.0.1:8092` (status, same process or second route) | compose limits |
| hub | Postgres 18 | same compose project, `/srv/corvid/pg` | internal network only | cpus 1.0 / 1 g |
| hub | Caddy front door | `deploy/caddy/corvid.caddy` (imported by the hub Caddyfile): `/api*` → `:8091`, `/status*` → `:8092`, `/chat*`, `/v1*` → `:8090`, `forward_auth` to `/api/v1/whoami` | hub tailnet IPv4 `:80` | — |
| repo | tests | `tests/` (pytest: config reload, presence chain with fakes, slice commands behind an interface, claim fairness with a Postgres test container or `pytest-postgresql`, identity dependency) | — | — |

## 5. Data flow

Owner edits `agent.toml` → agent reloads → `set-property corvid.slice` (≤ 5 s) → next heartbeat carries `caps_effective`. Agent → (tailnet) → Caddy → `forward_auth /api/v1/whoami` (whois) → API → `node` upsert + `heartbeat` row → status page renders from `node` + `threshold`. Member browser → Caddy `/status` → page. Jobs: `POST /api/v1/jobs` → `job` row + `NOTIFY` → (Phase 3) an agent with `batch_jobs=true` claims via SKIP LOCKED with the fair-share rule.

## 6. Error handling

| Failure | Detection | Response |
|---|---|---|
| Coordinator unreachable | heartbeat POST fails | agent keeps enforcing local policy, keeps trying with backoff (5 s → 60 s), never queues heartbeats; owner controls never depend on the hub |
| Postgres down | API health fails | API returns 503; status page shows a "stale data" badge; compose restarts db |
| Malformed `agent.toml` | parse/validation error | keep last good config; log; heartbeat `state=config_error`; page shows a warning icon |
| Identity missing/unknown | no `X-Corvid-User` | 401; page says "open this from a tailnet device" |
| Presence UNKNOWN | provider chain exhausted | treated as active (no work) and shown on the page; ADR-0007 |
| AC lost | power provider | pause immediately (stop job units); heartbeat `on_battery=true` |
| Clock skew on a node | server-side `now()` used for ages | agent timestamps are informational only |
| Kill flag present at boot | `~/.config/corvid/KILL` exists | agent starts, heartbeats `state=killed`, runs nothing until `corvid start` |

## 7. Acceptance tests (the plan's final block)

1. `curl -s -H 'X-Corvid-User: <founder>' http://127.0.0.1:8091/api/v1/nodes` on the hub (via ssh) lists **three** nodes with `state: live` and their opted-in offers; the status page at `http://solarplexus.<tailnet>.ts.net/status` renders them (founder eyeballs).
2. **Node-down:** `systemctl --user stop corvid-agent` on optiplex → within **≤ 30 s** the API/page shows `down` (`watch -n 5 curl …`); restart → `live` within 10 s.
3. **Live cap:** edit `cpu_quota_pct` 10 → 5 on ahnoway → `systemctl --user show corvid.slice -p CPUQuotaPerSecUSec` changes within **≤ 5 s**; the next heartbeat's `caps_effective` matches.
4. **Kill switch:** `corvid stop` on ahnoway → `systemctl --user is-active corvid.slice` reports inactive within **≤ 2 s**, no `corvid-*` processes remain (`pgrep -f corvid_agent` empty), the node shows `state=killed` then `down`; `corvid start` recovers.
5. **Opt-in default:** fresh config (move `agent.toml` aside, restart agent) → heartbeat `offers: {}`; page shows "offers: none"; restore.
6. **No logging:** a nonce in a job `spec` and a heartbeat field → `grep` across API logs, Postgres logs (`docker compose logs db`), agent journals → 0 hits for the nonce in logs (it may exist in DB rows by design — jobs are metadata; the *spec* is the member's; check the logs only).
7. **Bind check:** on the hub `ss -tln` shows `127.0.0.1:8091`, `127.0.0.1:8092`, and Caddy on `<hub-tailnet-ipv4>:80`; nothing CORVID on `0.0.0.0`; `5432` not published.
8. **Fair share (unit test):** two members enqueue 10 jobs each → 20 claims alternate owners (max run-length 1 while both have queued work); a single member's 10 jobs are all claimed when alone.
9. **Identity:** `curl` to Caddy from a non-tailnet path or without identity → 401; from a member device the page greets the member by display name (founder check); `X-Corvid-User` never appears in the access log.
10. `pytest -q` green; `ruff` clean; CI green.

## 8. Out of scope

Job execution (Phase 3), macOS/Windows agents and installers (Phase 4), member guides (Phase 4), Open WebUI member chat (stretch task in the plan — its ADR "chat front-end" lands when it is deployed; `:8093` stays reserved), Grafana (deferred; R07), IO bandwidth caps (optional root drop-in).

## 9. ADRs

ADR-0005 — Contribution is a slider (Accepted with this spec); ADR-0007 — Presence is best-effort (UNKNOWN never idle) and GPU sharing is temporal (Accepted with this spec); amendments recorded in `status.md`: ADR-0002 (member devices untagged; tags on hubs only), ADR-0003 (backends loopback behind Caddy; Caddy is the tailnet-facing listener).
