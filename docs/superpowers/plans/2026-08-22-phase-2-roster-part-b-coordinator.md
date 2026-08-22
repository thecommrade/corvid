# Phase 2 — The Roster, Part B (coordinator, status page, front door, deployment): Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (or subagent-driven-development for repo-only tasks 1–6) in an **Opus** session on ahnoway. Executor tags: **`Opus`**, **`Opus (splx-root)`**, **`founder`** (handoff protocol). TDD for code. **Prerequisites:** Part A merged (agent v0), Phase 0 executed (hub kernel-mode Tailscale + linger; unattended access), Phase 1 executed or at least its Caddy front door present (`/etc/caddy/Caddyfile.corvid`).

**Goal:** The coordinator (Postgres 18 + FastAPI API + status page) running as a separate compose project on the hub behind Caddy with Tailscale identity, agents on all three build nodes heartbeating into it, the live map rendering, and the Phase 2 acceptance tests passing.

**Architecture:** `deploy/coordinator/compose.yaml` (db + api), SQL migrations in `db/`, FastAPI app in `coordinator/` (roster upsert, pool math, queue shape with SKIP-LOCKED claim and per-member round-robin, identity dependency, status page template), Caddy `forward_auth` to `/api/v1/whoami` (whois), tests with a Postgres service container in CI.

**Tech Stack:** Postgres 18 (official image), Docker Compose v2+, Python 3.12, FastAPI, uvicorn, psycopg 3, Jinja2, pytest (+ `pytest-asyncio` not needed: use the sync TestClient), ruff; Caddy; Tailscale CLI (`tailscale whois --json`).

**Spec:** `docs/superpowers/specs/2026-08-22-phase-2-roster-design.md` §3 D7–D15, §4, §7; **read also** `R06`, `R07`, `R02`, ADR-0001/0002/0003/0005/0007, `remote-step`, Part A.

## Global Constraints

- Backends bind **`127.0.0.1` only** on the hub (`:8091` api, `:8092` status) — Caddy is the tailnet-facing listener; the bind lint enforces compose `ports:` carry a host IP.
- Postgres: no published port; `log_statement=none` etc. (spec D7); secrets in `/srv/corvid/coordinator.env` (0600) — never in git; bind mount `/srv/corvid/pg`.
- Every API route except `/health` requires identity (`X-Corvid-User` injected by Caddy `forward_auth`; direct loopback calls in tests set the header themselves).
- Logs: metadata only (ts, path, status, latency, node_id); never bodies, never the identity header value.
- All times `timestamptz`; server-side `now()` for ages; heartbeat 10 s → live < 10 s / stale < 30 s / down ≥ 30 s.
- §4 rows (`add-dependency`, same commit as `pyproject`/compose): PostgreSQL, postgres image, Docker Compose, psycopg 3 (LGPL-3.0, dynamic), FastAPI (MIT), uvicorn (BSD-3), Jinja2 (BSD-3), htmx (0BSD) if used; idea credits BOINC / Hadoop Fair Scheduler & DRF / Kubernetes leases.
- Branch `phase-2-coordinator`; conventional commits + trailer.

## File Structure

| Path | Responsibility |
|---|---|
| `coordinator/pyproject.toml` | package `corvid-coordinator`; deps fastapi, uvicorn, psycopg[binary], jinja2; dev pytest, httpx, ruff |
| `coordinator/src/corvid_coordinator/{__init__,settings,db,identity,roster,queue,pool,status,main}.py`, `templates/status.html` | the app |
| `db/0001_roster.sql`, `db/0002_queue.sql`, `db/0003_thresholds.sql` | migrations (idempotent, applied in order by `db.migrate()`) |
| `deploy/coordinator/compose.yaml`, `deploy/coordinator/Dockerfile`, `deploy/coordinator/coordinator.env.example` | runtime on the hub |
| `deploy/caddy/corvid.caddy` | front door routes + forward_auth (replaces the Phase 1 `Caddyfile.corvid` snippet) |
| `coordinator/tests/test_*.py` | unit + DB tests (CI: Postgres service container) |
| `.github/workflows/ci.yml` | add a `services: postgres` job for coordinator tests |
| `docs/runbooks/coordinator.md` | founder runbook |
| `docs/runs/phase-2-<date>.md` | evidence |

---

### Task 0: Branch, package skeleton, §4 rows, CI Postgres service

**Files:** Create `coordinator/pyproject.toml`, `coordinator/src/corvid_coordinator/__init__.py`, `coordinator/tests/__init__.py`, `coordinator/tests/conftest.py`; Modify `CLAUDE.md` §4, `.github/workflows/ci.yml`

- [ ] **Step 1 (`executor: Opus`):** `git checkout -b phase-2-coordinator`
- [ ] **Step 2: `coordinator/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
[project]
name = "corvid-coordinator"
version = "0.1.0"
description = "CORVID coordinator v0: roster, pool, queue shape, status page"
requires-python = ">=3.12"
license = { text = "MIT" }
dependencies = ["fastapi>=0.115", "uvicorn[standard]>=0.30", "psycopg[binary]>=3.2", "jinja2>=3.1"]
[project.optional-dependencies]
dev = ["pytest>=8", "httpx>=0.27", "ruff>=0.6"]
[tool.setuptools.packages.find]
where = ["src"]
[tool.setuptools.package-data]
corvid_coordinator = ["templates/*.html"]
[tool.ruff]
line-length = 100
target-version = "py312"
[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3: `conftest.py` (DB fixture from `CORVID_TEST_DSN`; tests that need a DB skip when unset)**

```python
# coordinator/tests/conftest.py
import os, pytest, psycopg
DSN = os.environ.get("CORVID_TEST_DSN")   # e.g. postgresql://corvid:corvid@127.0.0.1:5432/corvid_test (CI service container)

@pytest.fixture
def dsn():
    if not DSN:
        pytest.skip("CORVID_TEST_DSN not set")
    from corvid_coordinator.db import migrate, reset_for_tests
    reset_for_tests(DSN); migrate(DSN)
    return DSN
```

- [ ] **Step 4: CI** — add to `.github/workflows/ci.yml` a second job:

```yaml
  coordinator-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:18
        env: { POSTGRES_USER: corvid, POSTGRES_PASSWORD: corvid, POSTGRES_DB: corvid_test }
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U corvid -d corvid_test" --health-interval 5s --health-timeout 5s --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: |
          if [ -d coordinator ]; then pip install --quiet -e './coordinator[dev]' -e './agent[dev]' && CORVID_TEST_DSN=postgresql://corvid:corvid@127.0.0.1:5432/corvid_test pytest -q coordinator agent; else echo "no coordinator yet"; fi
```
(The `ports: ["5432:5432"]` in the CI job is GitHub's service container on the runner, not a CORVID listener — the bind lint only scans repo compose files named `compose*.y*ml`, so `.github/workflows/ci.yml` is not linted; note this in the run file.)

- [ ] **Step 5: §4 rows (`add-dependency`)** — append: `| PostgreSQL | Roster, queue, thresholds (coordinator DB) | PostgreSQL License | PostgreSQL Global Development Group |`, `| postgres (Docker Official Image) | DB container on the hub | MIT (Dockerfiles) | Docker Official Images maintainers |`, `| Docker Compose | Coordinator project on the hub | Apache-2.0 | Docker, Inc. |`, `| psycopg 3 | Postgres driver (dynamic import) | LGPL-3.0 | Daniele Varrazzo & contributors |`, `| FastAPI | Coordinator API + status page | MIT | Sebastián Ramírez |`, `| uvicorn | ASGI server | BSD-3-Clause | Encode OSS |`, `| Jinja2 | Status page templates | BSD-3-Clause | Pallets |`, `| BOINC / Hadoop Fair Scheduler & DRF / Kubernetes leases | Preference names; max-min fair share; lease pattern (ideas) | — | D. P. Anderson; Zaharia et al., Ghodsi et al.; CNCF |`.
- [ ] **Step 6:** `.venv/bin/pip install -e './coordinator[dev]'`; `git add coordinator CLAUDE.md .github && git commit -m "feat(coordinator): skeleton, CI Postgres job, §4 credits"` (+ trailer).

### Task 1: Migrations + db module

**Files:** Create `db/0001_roster.sql`, `db/0002_queue.sql`, `db/0003_thresholds.sql`, `coordinator/src/corvid_coordinator/db.py`, `coordinator/tests/test_db.py`

- [ ] **Step 1: Failing test**

```python
# coordinator/tests/test_db.py
import psycopg
from corvid_coordinator.db import migrate, applied_versions

def test_migrations_apply_and_are_idempotent(dsn):
    migrate(dsn); migrate(dsn)
    assert applied_versions(dsn) == [1, 2, 3]
    with psycopg.connect(dsn) as c:
        names = {r[0] for r in c.execute("select table_name from information_schema.tables where table_schema='public'")}
    assert {"node", "heartbeat", "job", "threshold", "schema_migrations"} <= names
```

- [ ] **Step 2:** FAIL. **Step 3: SQL + module**

```sql
-- db/0001_roster.sql
CREATE TABLE IF NOT EXISTS node (
  node_id uuid PRIMARY KEY,
  owner_login text NOT NULL,
  display_name text,
  os text, arch text, agent_version text,
  offers jsonb NOT NULL DEFAULT '{}'::jsonb,
  caps jsonb NOT NULL DEFAULT '{}'::jsonb,
  presence text, on_battery boolean, gpu jsonb, load1 real, mem_free_gb real,
  state text NOT NULL DEFAULT 'ok',
  first_seen timestamptz NOT NULL DEFAULT now(),
  last_seen timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS heartbeat (
  node_id uuid NOT NULL REFERENCES node(node_id) ON DELETE CASCADE,
  at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS heartbeat_node_at_idx ON heartbeat (node_id, at DESC);
```

```sql
-- db/0002_queue.sql
CREATE TABLE IF NOT EXISTS job (
  id bigserial PRIMARY KEY,
  owner_login text NOT NULL,
  kind text NOT NULL,
  spec jsonb NOT NULL,
  state text NOT NULL DEFAULT 'queued',          -- queued | running | done | failed
  priority int NOT NULL DEFAULT 0,
  run_after timestamptz,
  claimed_by uuid REFERENCES node(node_id),
  claimed_at timestamptz, lease_until timestamptz,
  attempt int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  result jsonb
);
CREATE INDEX IF NOT EXISTS job_queued_idx ON job (priority DESC, created_at) WHERE state = 'queued';
CREATE INDEX IF NOT EXISTS job_running_owner_idx ON job (owner_login) WHERE state = 'running';
CREATE OR REPLACE FUNCTION job_notify() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_notify('job_queued', ''); RETURN NULL; END $$;
DROP TRIGGER IF EXISTS job_queued_trg ON job;
CREATE TRIGGER job_queued_trg AFTER INSERT ON job FOR EACH STATEMENT EXECUTE FUNCTION job_notify();
```

```sql
-- db/0003_thresholds.sql
CREATE TABLE IF NOT EXISTS threshold (
  name text PRIMARY KEY,
  needs jsonb NOT NULL,          -- e.g. {"vram_plus_ram_gb": 30}
  product text NOT NULL,
  note text
);
INSERT INTO threshold (name, needs, product, note) VALUES
  ('Phase 1 model', '{"vram_plus_ram_gb": 30}', 'private AI — Qwen3.8-27B Q8_0', 'weights 26.6 GiB + KV; pool must offer ≥ 30 GB of VRAM+RAM')
ON CONFLICT (name) DO NOTHING;
```

```python
# coordinator/src/corvid_coordinator/db.py
from __future__ import annotations
import re
from pathlib import Path
import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "db"

def _files() -> list[tuple[int, Path]]:
    out = []
    for p in sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9][0-9]_*.sql")):
        out.append((int(p.name[:4]), p))
    return out

def migrate(dsn: str) -> list[int]:
    applied = []
    with psycopg.connect(dsn, autocommit=False) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version int PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())")
        done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
        for v, p in _files():
            if v in done: continue
            conn.execute(p.read_text())
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (v,))
            applied.append(v)
        conn.commit()
    return applied

def applied_versions(dsn: str) -> list[int]:
    with psycopg.connect(dsn) as conn:
        return [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]

def reset_for_tests(dsn: str) -> None:
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
```

- [ ] **Step 4:** `CORVID_TEST_DSN=… .venv/bin/pytest -q coordinator/tests/test_db.py` → PASS (locally: run a throwaway Postgres with `docker run --rm -d --name corvid-testpg -e POSTGRES_USER=corvid -e POSTGRES_PASSWORD=corvid -e POSTGRES_DB=corvid_test -p 127.0.0.1:5433:5432 postgres:18` and DSN `postgresql://corvid:corvid@127.0.0.1:5433/corvid_test`; `docker rm -f corvid-testpg` afterwards). **Step 5:** commit `feat(coordinator): migrations + db module (TDD)`.

### Task 2: Roster upsert + pool math

**Files:** Create `coordinator/src/corvid_coordinator/roster.py`, `pool.py`, `coordinator/tests/test_roster.py`

**Interfaces:** `upsert_heartbeat(conn, owner_login, payload) -> None`; `list_nodes(conn) -> list[dict]` (each with `state_derived`: live/stale/down); `pool_summary(nodes) -> dict(capacity={cores, ram_gb, vram_mb}, live=n)`; `thresholds(conn, pool) -> list[dict(name, product, needs, met: bool, distance: dict)]`.

- [ ] **Step 1: Failing tests**

```python
# coordinator/tests/test_roster.py
import json, uuid, psycopg
from corvid_coordinator.roster import upsert_heartbeat, list_nodes
from corvid_coordinator.pool import pool_summary, thresholds

def _hb(nid, **o):
    p = {"node_id": nid, "agent_version": "0.1.0", "os": "linux", "arch": "x86_64", "offers": {}, "caps_effective": {"cpu_quota_pct": 10, "mem_max_gb": 1.6, "vram_cap_mb": 800}, "presence": "unknown", "on_battery": None, "state": "ok"}
    p.update(o); return p

def test_upsert_then_live(dsn):
    nid = str(uuid.uuid4())
    with psycopg.connect(dsn) as c:
        upsert_heartbeat(c, "alice@example.com", _hb(nid)); upsert_heartbeat(c, "alice@example.com", _hb(nid, presence="idle")); c.commit()
        nodes = list_nodes(c)
    assert len(nodes) == 1 and nodes[0]["state_derived"] == "live" and nodes[0]["presence"] == "idle" and nodes[0]["offers"] == {}

def test_down_after_30s(dsn):
    nid = str(uuid.uuid4())
    with psycopg.connect(dsn) as c:
        upsert_heartbeat(c, "bob@example.com", _hb(nid)); c.execute("UPDATE node SET last_seen = now() - interval '31 seconds'"); c.commit()
        assert list_nodes(c)[0]["state_derived"] == "down"

def test_pool_counts_only_live_and_opted_in():
    nodes = [
        {"state_derived": "live", "offers": {"inference_host": True, "gpu_allowed": True}, "caps": {"cpu_quota_pct": 10, "mem_max_gb": 1.6, "vram_cap_mb": 800}, "cores": 12, "gpu": {"vram_total_mb": 8192}},
        {"state_derived": "live", "offers": {}, "caps": {"cpu_quota_pct": 10, "mem_max_gb": 3.2, "vram_cap_mb": 600}, "cores": 12, "gpu": None},
        {"state_derived": "down", "offers": {"inference_host": True}, "caps": {"cpu_quota_pct": 50, "mem_max_gb": 8}, "cores": 4, "gpu": None},
    ]
    s = pool_summary(nodes)
    assert s["live"] == 2 and s["offering"] == 1 and s["capacity"]["ram_gb"] == 1.6 and s["capacity"]["vram_mb"] == 800 and s["capacity"]["cores"] == 1.2

def test_threshold_distance(dsn):
    with psycopg.connect(dsn) as c:
        t = thresholds(c, {"capacity": {"ram_gb": 4.0, "vram_mb": 2048}})
    assert t[0]["name"] == "Phase 1 model" and t[0]["met"] is False and t[0]["distance"]["vram_plus_ram_gb"] == 24.0
```

- [ ] **Step 2:** FAIL. **Step 3: Implement**

```python
# coordinator/src/corvid_coordinator/roster.py
from __future__ import annotations
import json, os
import psycopg
from psycopg.types.json import Jsonb

STATE_SQL = "CASE WHEN last_seen > now() - interval '10 seconds' THEN 'live' WHEN last_seen > now() - interval '30 seconds' THEN 'stale' ELSE 'down' END"

def upsert_heartbeat(conn: psycopg.Connection, owner_login: str, p: dict) -> None:
    nid = p["node_id"]
    conn.execute(
        """INSERT INTO node (node_id, owner_login, os, arch, agent_version, offers, caps, presence, on_battery, gpu, load1, mem_free_gb, state, last_seen)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
           ON CONFLICT (node_id) DO UPDATE SET owner_login=EXCLUDED.owner_login, os=EXCLUDED.os, arch=EXCLUDED.arch, agent_version=EXCLUDED.agent_version,
             offers=EXCLUDED.offers, caps=EXCLUDED.caps, presence=EXCLUDED.presence, on_battery=EXCLUDED.on_battery, gpu=EXCLUDED.gpu,
             load1=EXCLUDED.load1, mem_free_gb=EXCLUDED.mem_free_gb, state=EXCLUDED.state, last_seen=now()""",
        (nid, owner_login, p.get("os"), p.get("arch"), p.get("agent_version"), Jsonb(p.get("offers") or {}), Jsonb(p.get("caps_effective") or {}),
         p.get("presence"), p.get("on_battery"), Jsonb(p.get("gpu")) if p.get("gpu") is not None else None, p.get("load1"), p.get("mem_free_gb"), p.get("state", "ok")))
    meta = {k: p.get(k) for k in ("presence", "on_battery", "state", "load1", "mem_free_gb", "idle_enough")}   # metadata only
    conn.execute("INSERT INTO heartbeat (node_id, payload) VALUES (%s, %s)", (nid, Jsonb(meta)))

def list_nodes(conn: psycopg.Connection) -> list[dict]:
    cols = ["node_id", "owner_login", "display_name", "os", "arch", "agent_version", "offers", "caps", "presence", "on_battery", "gpu", "load1", "mem_free_gb", "state", "first_seen", "last_seen", "state_derived"]
    rows = conn.execute(f"SELECT node_id::text, owner_login, display_name, os, arch, agent_version, offers, caps, presence, on_battery, gpu, load1, mem_free_gb, state, first_seen, last_seen, {STATE_SQL} FROM node ORDER BY owner_login, first_seen").fetchall()
    out = []
    for r in rows:
        d = dict(zip(cols, r)); d["cores"] = os.cpu_count() or 1   # v0: cores reported by the agent later; placeholder constant only for capacity maths
        out.append(d)
    return out
```

```python
# coordinator/src/corvid_coordinator/pool.py
from __future__ import annotations
import psycopg

def pool_summary(nodes: list[dict]) -> dict:
    live = [n for n in nodes if n.get("state_derived") == "live"]
    offering = [n for n in live if any((n.get("offers") or {}).values())]
    cores = sum((n.get("caps") or {}).get("cpu_quota_pct", 0) / 100 * (n.get("cores") or 1) for n in offering)
    ram = sum(float((n.get("caps") or {}).get("mem_max_gb", 0)) for n in offering)
    vram = sum(int((n.get("caps") or {}).get("vram_cap_mb", 0)) for n in offering if (n.get("offers") or {}).get("gpu_allowed") and n.get("gpu"))
    return {"live": len(live), "offering": len(offering), "capacity": {"cores": round(cores, 2), "ram_gb": round(ram, 2), "vram_mb": vram}}

def thresholds(conn: psycopg.Connection, pool: dict) -> list[dict]:
    cap = pool["capacity"]; have = {"vram_plus_ram_gb": cap.get("ram_gb", 0) + cap.get("vram_mb", 0) / 1024, "ram_gb": cap.get("ram_gb", 0), "vram_mb": cap.get("vram_mb", 0), "cores": cap.get("cores", 0)}
    out = []
    for name, needs, product, note in conn.execute("SELECT name, needs, product, note FROM threshold ORDER BY name"):
        dist = {k: round(max(0.0, float(v) - float(have.get(k, 0))), 2) for k, v in needs.items()}
        out.append({"name": name, "product": product, "note": note, "needs": needs, "met": all(d == 0 for d in dist.values()), "distance": dist})
    return out
```

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(coordinator): roster upsert, derived state, pool + thresholds (TDD)`.

### Task 3: Queue shape — claim with SKIP LOCKED and per-member round-robin; leases; reaper

**Files:** Create `coordinator/src/corvid_coordinator/queue.py`, `coordinator/tests/test_queue.py`

**Interfaces:** `enqueue(conn, owner_login, kind, spec, priority=0) -> int`; `claim(conn, node_id, lease_seconds=120) -> dict|None` (fair: owner with the fewest running jobs first, then priority, then age); `renew(conn, job_id, node_id, lease_seconds)`; `finish(conn, job_id, ok: bool, result_meta: dict)`; `reap_expired(conn) -> int`.

- [ ] **Step 1: Failing tests**

```python
# coordinator/tests/test_queue.py
import uuid, psycopg
from corvid_coordinator.queue import enqueue, claim, finish, reap_expired, renew
from corvid_coordinator.roster import upsert_heartbeat

def _node(c):
    nid = str(uuid.uuid4()); upsert_heartbeat(c, "w@example.com", {"node_id": nid, "offers": {"batch_jobs": True}, "caps_effective": {}, "state": "ok"}); return nid

def test_round_robin_between_members(dsn):
    with psycopg.connect(dsn) as c:
        nid = _node(c)
        for i in range(10): enqueue(c, "alice@example.com", "noop", {"i": i}); enqueue(c, "bob@example.com", "noop", {"i": i})
        c.commit()
        owners = []
        for _ in range(20):
            j = claim(c, nid); owners.append(j["owner_login"]); c.commit()
        assert max(len(list(g)) for _, g in __import__("itertools").groupby(owners)) == 1   # strictly alternating while both have work
        assert claim(c, nid) is None

def test_single_member_gets_everything(dsn):
    with psycopg.connect(dsn) as c:
        nid = _node(c)
        for i in range(5): enqueue(c, "solo@example.com", "noop", {"i": i})
        c.commit(); got = [claim(c, nid) for _ in range(5)]; c.commit()
        assert all(j and j["owner_login"] == "solo@example.com" for j in got)

def test_lease_reaper_requeues(dsn):
    with psycopg.connect(dsn) as c:
        nid = _node(c); enqueue(c, "a@example.com", "noop", {}); c.commit(); j = claim(c, nid, lease_seconds=1); c.commit()
        c.execute("UPDATE job SET lease_until = now() - interval '1 second' WHERE id=%s", (j["id"],)); c.commit()
        assert reap_expired(c) == 1; c.commit()
        j2 = claim(c, nid); assert j2["id"] == j["id"] and j2["attempt"] == 2

def test_finish_records_metadata_only(dsn):
    with psycopg.connect(dsn) as c:
        nid = _node(c); enqueue(c, "a@example.com", "noop", {}); c.commit(); j = claim(c, nid); c.commit()
        finish(c, j["id"], ok=True, result_meta={"exit": 0, "seconds": 1.2}); c.commit()
        assert c.execute("SELECT state, result->>'exit' FROM job WHERE id=%s", (j["id"],)).fetchone() == ("done", "0")
```

- [ ] **Step 2:** FAIL. **Step 3: Implement**

```python
# coordinator/src/corvid_coordinator/queue.py
from __future__ import annotations
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

def enqueue(conn: psycopg.Connection, owner_login: str, kind: str, spec: dict, priority: int = 0) -> int:
    return conn.execute("INSERT INTO job (owner_login, kind, spec, priority) VALUES (%s,%s,%s,%s) RETURNING id", (owner_login, kind, Jsonb(spec), priority)).fetchone()[0]

CLAIM_SQL = """
UPDATE job SET state='running', claimed_by=%(node)s, claimed_at=clock_timestamp(), lease_until=clock_timestamp() + make_interval(secs => %(lease)s), attempt=attempt+1
WHERE id = (
  SELECT j.id FROM job j
  LEFT JOIN (SELECT owner_login, count(*) AS running FROM job WHERE state='running' GROUP BY owner_login) r ON r.owner_login = j.owner_login
  WHERE j.state='queued' AND (j.run_after IS NULL OR j.run_after <= now())
  ORDER BY COALESCE(r.running, 0) ASC, j.priority DESC, j.created_at ASC
  FOR UPDATE OF j SKIP LOCKED LIMIT 1)
RETURNING id, owner_login, kind, spec, priority, attempt, claimed_by::text, lease_until
"""

def claim(conn: psycopg.Connection, node_id: str, lease_seconds: int = 120) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(CLAIM_SQL, {"node": node_id, "lease": lease_seconds}); return cur.fetchone()

def renew(conn: psycopg.Connection, job_id: int, node_id: str, lease_seconds: int = 120) -> bool:
    return conn.execute("UPDATE job SET lease_until = clock_timestamp() + make_interval(secs => %s) WHERE id=%s AND claimed_by=%s AND state='running'", (lease_seconds, job_id, node_id)).rowcount == 1

def finish(conn: psycopg.Connection, job_id: int, ok: bool, result_meta: dict) -> None:
    conn.execute("UPDATE job SET state=%s, finished_at=now(), result=%s WHERE id=%s", ("done" if ok else "failed", Jsonb(result_meta), job_id))

def reap_expired(conn: psycopg.Connection) -> int:
    return conn.execute("UPDATE job SET state='queued', claimed_by=NULL, claimed_at=NULL, lease_until=NULL WHERE state='running' AND lease_until < now()").rowcount
```
Note: the fairness test's strict alternation holds because `running` counts update as each claim commits; a real agent `finish`es jobs, which the Phase 3 executor does. (ADR-0001: no quotas — the ORDER BY only *orders*, it never refuses.)

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(coordinator): queue claim (SKIP LOCKED, per-member round-robin), leases, reaper (TDD)`.

### Task 4: Identity dependency + API + status page

**Files:** Create `coordinator/src/corvid_coordinator/{settings,identity,status,main}.py`, `templates/status.html`, `coordinator/tests/test_api.py`

**Interfaces:** `Settings` (env: `CORVID_DSN`, `CORVID_IDENTITY_HEADER=X-Corvid-User`, `CORVID_NAME_HEADER=X-Corvid-Name`, `CORVID_WHOIS_CMD=tailscale whois --json {ip}`); `current_user(request) -> Identity(login, name)` (401 if absent); routes per spec D9; `render_status(nodes, pool, thresholds, thanks) -> html`.

- [ ] **Step 1: Failing tests**

```python
# coordinator/tests/test_api.py
import os, uuid
from fastapi.testclient import TestClient

def _client(dsn, monkeypatch):
    monkeypatch.setenv("CORVID_DSN", dsn)
    from corvid_coordinator.main import create_app
    return TestClient(create_app())

def test_requires_identity(dsn, monkeypatch):
    c = _client(dsn, monkeypatch)
    assert c.get("/api/v1/nodes").status_code == 401 and c.get("/health").status_code == 200

def test_heartbeat_roundtrip_and_status_page(dsn, monkeypatch):
    c = _client(dsn, monkeypatch); h = {"X-Corvid-User": "alice@example.com", "X-Corvid-Name": "Alice"}
    nid = str(uuid.uuid4())
    r = c.post("/api/v1/heartbeat", json={"node_id": nid, "offers": {"inference_host": True}, "caps_effective": {"cpu_quota_pct": 10, "mem_max_gb": 1.6, "vram_cap_mb": 800}, "presence": "idle", "state": "ok"}, headers=h)
    assert r.status_code == 200
    nodes = c.get("/api/v1/nodes", headers=h).json()
    assert nodes[0]["node_id"] == nid and nodes[0]["state_derived"] == "live" and nodes[0]["owner_login"] == "alice@example.com"
    page = c.get("/status", headers=h)
    assert page.status_code == 200 and "Alice" in page.text and "live" in page.text and "offers" in page.text
    assert "alice@example.com" not in page.text          # logins never rendered; display names only

def test_whoami(dsn, monkeypatch):
    c = _client(dsn, monkeypatch)
    r = c.get("/api/v1/whoami", headers={"X-Corvid-User": "bob@example.com", "X-Corvid-Name": "Bob"})
    assert r.status_code == 200 and r.json() == {"login": "bob@example.com", "name": "Bob"}

def test_offers_none_rendered(dsn, monkeypatch):
    c = _client(dsn, monkeypatch); h = {"X-Corvid-User": "z@example.com", "X-Corvid-Name": "Z"}
    c.post("/api/v1/heartbeat", json={"node_id": str(uuid.uuid4()), "offers": {}, "caps_effective": {}, "presence": "unknown", "state": "ok"}, headers=h)
    assert "offers: none" in c.get("/status", headers=h).text
```

- [ ] **Step 2:** FAIL. **Step 3: Implement**

```python
# coordinator/src/corvid_coordinator/settings.py
import os
from dataclasses import dataclass
@dataclass(frozen=True)
class Settings:
    dsn: str = os.environ.get("CORVID_DSN", "")
    identity_header: str = os.environ.get("CORVID_IDENTITY_HEADER", "X-Corvid-User")
    name_header: str = os.environ.get("CORVID_NAME_HEADER", "X-Corvid-Name")
    heartbeat_seconds: int = int(os.environ.get("CORVID_HEARTBEAT_SECONDS", "10"))
```

```python
# coordinator/src/corvid_coordinator/identity.py
from __future__ import annotations
from dataclasses import dataclass
from fastapi import HTTPException, Request
from .settings import Settings

@dataclass(frozen=True)
class Identity:
    login: str
    name: str

def current_user(request: Request) -> Identity:
    s: Settings = request.app.state.settings
    login = request.headers.get(s.identity_header, "").strip()
    if not login:
        raise HTTPException(status_code=401, detail="open this from a tailnet device (no identity)")
    return Identity(login=login, name=request.headers.get(s.name_header, "").strip() or login.split("@")[0])
```

```python
# coordinator/src/corvid_coordinator/status.py
from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
_env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")), autoescape=select_autoescape(["html"]))

def render_status(nodes: list[dict], pool: dict, thresholds: list[dict], thanks: list[str], refresh: int = 10) -> str:
    for n in nodes:
        n["offers_text"] = ", ".join(k for k, v in (n.get("offers") or {}).items() if v) or "none"
        n["owner_display"] = n.get("display_name") or (n.get("owner_login") or "").split("@")[0]
    return _env.get_template("status.html").render(nodes=nodes, pool=pool, thresholds=thresholds, thanks=thanks, refresh=refresh)
```

```html
<!-- coordinator/src/corvid_coordinator/templates/status.html -->
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="{{ refresh }}"><title>CORVID — status</title>
<style>body{font:15px/1.4 system-ui,sans-serif;margin:2rem;max-width:60rem}table{border-collapse:collapse;width:100%}td,th{padding:.35rem .6rem;border-bottom:1px solid #ddd;text-align:left}.live{color:#1a7f37}.stale{color:#9a6700}.down{color:#b42318}.muted{color:#666}</style></head><body>
<h1>CORVID — the pool right now</h1>
<p class="muted">A village utility. Everything here is opt-in; each owner's slider sets what their machine offers.</p>
<h2>Live map</h2>
<table><tr><th>Node</th><th>Owner</th><th>State</th><th>Presence</th><th>Offers</th><th>Caps (slider)</th></tr>
{% for n in nodes %}<tr><td>{{ n.node_id[:8] }}</td><td>{{ n.owner_display }}</td><td class="{{ n.state_derived }}">{{ n.state_derived }}</td><td>{{ n.presence or "?" }}{% if n.on_battery %} · on battery{% endif %}</td><td>offers: {{ n.offers_text }}</td><td>cpu {{ n.caps.cpu_quota_pct if n.caps and n.caps.cpu_quota_pct is defined else "?" }}% · ram {{ n.caps.mem_max_gb if n.caps and n.caps.mem_max_gb is defined else "?" }} GB{% if n.gpu %} · vram ≤ {{ n.caps.vram_cap_mb }} MB{% endif %}</td></tr>{% endfor %}
</table>
<h2>Pool</h2>
<p>{{ pool.live }} live node(s), {{ pool.offering }} offering · capacity offered: {{ pool.capacity.cores }} cores · {{ pool.capacity.ram_gb }} GB RAM · {{ pool.capacity.vram_mb }} MB VRAM</p>
<h2>Thresholds, not timelines</h2>
<ul>{% for t in thresholds %}<li><strong>{{ t.product }}</strong> — {% if t.met %}<span class="live">unlocked</span>{% else %}needs {% for k, v in t.distance.items() %}{{ v }} more {{ k }}{% if not loop.last %}, {% endif %}{% endfor %}{% endif %}{% if t.note %} <span class="muted">({{ t.note }})</span>{% endif %}</li>{% endfor %}</ul>
<h2>Thank you</h2>
<p>{% if thanks %}{{ thanks|join(", ") }}{% else %}nobody is offering yet — and that is fine{% endif %}</p>
</body></html>
```

```python
# coordinator/src/corvid_coordinator/main.py
from __future__ import annotations
import logging, time
import psycopg
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from .db import migrate
from .identity import Identity, current_user
from .pool import pool_summary, thresholds
from .queue import enqueue
from .roster import list_nodes, upsert_heartbeat
from .settings import Settings
from .status import render_status

log = logging.getLogger("corvid.api")

def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or Settings()
    app = FastAPI(title="CORVID coordinator", version="0.1.0", docs_url=None, redoc_url=None)
    app.state.settings = s
    if s.dsn:
        migrate(s.dsn)

    @app.middleware("http")
    async def meta_log(request: Request, call_next):
        t0 = time.monotonic(); resp = await call_next(request)
        log.info("%s %s %d %dms", request.method, request.url.path, resp.status_code, int((time.monotonic() - t0) * 1000))   # metadata only
        return resp

    def conn():
        return psycopg.connect(s.dsn)

    @app.get("/health")
    def health():
        try:
            with conn() as c: c.execute("SELECT 1")
            return {"ok": True}
        except Exception:
            return JSONResponse({"ok": False}, status_code=503)

    @app.get("/api/v1/whoami")
    def whoami(user: Identity = Depends(current_user)):
        return {"login": user.login, "name": user.name}

    @app.post("/api/v1/heartbeat")
    def heartbeat(payload: dict, user: Identity = Depends(current_user)):
        with conn() as c:
            upsert_heartbeat(c, user.login, payload); c.commit()
        return {"ok": True, "heartbeat_seconds": s.heartbeat_seconds}

    @app.get("/api/v1/nodes")
    def nodes(user: Identity = Depends(current_user)):
        with conn() as c: return list_nodes(c)

    @app.get("/api/v1/pool")
    def pool(user: Identity = Depends(current_user)):
        with conn() as c:
            ns = list_nodes(c); p = pool_summary(ns); return {"pool": p, "thresholds": thresholds(c, p)}

    @app.post("/api/v1/jobs")
    def post_job(body: dict, user: Identity = Depends(current_user)):
        with conn() as c:
            jid = enqueue(c, user.login, body.get("kind", "noop"), body.get("spec", {}), int(body.get("priority", 0))); c.commit()
        return {"id": jid, "state": "queued"}

    @app.get("/status", response_class=HTMLResponse)
    def status(user: Identity = Depends(current_user)):
        with conn() as c:
            ns = list_nodes(c); p = pool_summary(ns); th = thresholds(c, p)
            thanks = sorted({(n.get("display_name") or n["owner_login"].split("@")[0]) for n in ns if any((n.get("offers") or {}).values())})
        return render_status(ns, p, th, thanks, refresh=s.heartbeat_seconds)

    return app

app = create_app() if Settings().dsn else None
```

- [ ] **Step 4:** PASS (`CORVID_TEST_DSN=… pytest -q coordinator`). **Step 5:** `ruff` clean; commit `feat(coordinator): identity dependency, API, status page (TDD)`.

### Task 5: Compose project, Dockerfile, env example, runbook

**Files:** Create `deploy/coordinator/compose.yaml`, `deploy/coordinator/Dockerfile`, `deploy/coordinator/coordinator.env.example`, `docs/runbooks/coordinator.md`

- [ ] **Step 1: Files**

```yaml
# deploy/coordinator/compose.yaml  — separate project from the hub's media stack (spec D7)
name: corvid-coordinator
services:
  db:
    image: postgres:18.1-trixie          # pin to the full tag current at deploy time (record it in the run file)
    restart: unless-stopped
    env_file: [/srv/corvid/coordinator.env]   # POSTGRES_USER=corvid POSTGRES_PASSWORD=… POSTGRES_DB=corvid
    command: ["postgres", "-c", "log_statement=none", "-c", "log_min_duration_statement=-1", "-c", "log_connections=off", "-c", "log_disconnections=off"]
    volumes: ["/srv/corvid/pg:/var/lib/postgresql"]
    shm_size: 256mb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U corvid -d corvid"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 1g, pids: 200 }
  api:
    build: { context: ../.., dockerfile: deploy/coordinator/Dockerfile }
    restart: unless-stopped
    env_file: [/srv/corvid/coordinator.env]   # CORVID_DSN=postgresql://corvid:…@db:5432/corvid
    depends_on:
      db: { condition: service_healthy }
    ports: ["127.0.0.1:8091:8091"]            # loopback only — Caddy is the tailnet-facing listener
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 512m }
```

```dockerfile
# deploy/coordinator/Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY coordinator/ /app/coordinator/
COPY db/ /app/db/
RUN pip install --no-cache-dir /app/coordinator
EXPOSE 8091
CMD ["uvicorn", "corvid_coordinator.main:app", "--host", "0.0.0.0", "--port", "8091", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
# NOTE: 0.0.0.0 here is the container-internal bind; the published port is 127.0.0.1-only (compose). Allowlisted in docs/adr/bind-allowlist.txt with this comment. # allow-bind
```

```bash
# deploy/coordinator/coordinator.env.example  (copy to /srv/corvid/coordinator.env, chmod 600; never commit the real one)
POSTGRES_USER=corvid
POSTGRES_PASSWORD=change-me
POSTGRES_DB=corvid
CORVID_DSN=postgresql://corvid:change-me@db:5432/corvid
CORVID_HEARTBEAT_SECONDS=10
```

Add `deploy/coordinator/Dockerfile` to `docs/adr/bind-allowlist.txt` with the comment `# ADR-0003: container-internal bind; published on 127.0.0.1 only`, then `bash scripts/lint-bind-targets.sh` → ok.

`docs/runbooks/coordinator.md` (founder-facing): where it lives (`deploy/coordinator/` + `/srv/corvid/`), `docker compose -f deploy/coordinator/compose.yaml up -d|ps|logs|down`, nightly backup `docker compose exec db pg_dump -U corvid corvid | gzip > <pool>/corvid/backups/corvid-$(date +%F).sql.gz` (add a user timer), migrations (automatic at API start; files in `db/`), reading the map, what the thresholds mean, "if the page is stale" (db health), and that access details stay in the private notes.

- [ ] **Step 2:** commit `feat(coordinator): compose project, Dockerfile, env example, runbook`.

### Task 6: Caddy front door with forward_auth (hub)

**Files:** Create `deploy/caddy/corvid.caddy` (supersedes `deploy/phase-1/Caddyfile.corvid`)

- [ ] **Step 1: Snippet**

```caddyfile
# deploy/caddy/corvid.caddy — CORVID front door (ADR-0003). Import from the hub's Caddyfile.
http://<hub-tailnet-ipv4>:80 {
    # identity for everything below: whois on the client's tailnet IP via the coordinator
    forward_auth 127.0.0.1:8091 {
        uri /api/v1/whoami-by-ip
        copy_headers X-Corvid-User X-Corvid-Name
    }
    handle /api* { reverse_proxy 127.0.0.1:8091 }
    handle /status* { reverse_proxy 127.0.0.1:8092 }
    handle /v1* { reverse_proxy 127.0.0.1:8090 }
    handle /chat* { reverse_proxy 127.0.0.1:8090 }
    handle { respond "CORVID — /chat · /status · /v1 · /api" 200 }
    log {
        output file /var/log/caddy/corvid.log
        format json
    }
}
```
Add to the API (`main.py`) the route `GET /api/v1/whoami-by-ip`: reads `X-Forwarded-For` (set by Caddy's forward_auth), runs `tailscale whois --json <ip>` via a `Runner` (configurable command for tests), returns 200 with headers `X-Corvid-User: <UserProfile.LoginName>`, `X-Corvid-Name: <UserProfile.DisplayName>` (401 when whois fails or the node is tagged). Unit test with a fake runner returning a canned whois JSON (`{"UserProfile":{"LoginName":"alice@example.com","DisplayName":"Alice"},"Node":{"Tags":null}}`).
**S-05 note:** if S-05 showed `tailscale serve` headers are the simpler path, replace `forward_auth` by putting Caddy behind `tailscale serve` and mapping `Tailscale-User-Login` → `X-Corvid-User`; record which path was used in the run file and amend ADR-0003.

- [ ] **Step 2 (`executor: Opus (splx-root)`): Install on the hub** — `cp deploy/caddy/corvid.caddy /etc/caddy/corvid.caddy` (IP substituted), replace the Phase 1 import with `import /etc/caddy/corvid.caddy` (backup Caddyfile first), `caddy validate --config /etc/caddy/Caddyfile && systemctl reload caddy`. Undo: restore backup + reload.
- [ ] **Step 3:** commit `feat(caddy): front door with forward_auth identity`.

### Task 7: Deploy the coordinator on the hub

- [ ] **Step 1 (`executor: Opus (splx-root)`):** `mkdir -p /srv/corvid/pg && cp deploy/coordinator/coordinator.env.example /srv/corvid/coordinator.env && chmod 600 /srv/corvid/coordinator.env` — then **`executor: founder`** handoff: "edit `/srv/corvid/coordinator.env` and set a real `POSTGRES_PASSWORD` (and the same in `CORVID_DSN`); reply done."
- [ ] **Step 2 (`executor: Opus`, as the docker-group user or via `splx-root`):** copy the repo's `deploy/coordinator/`, `coordinator/`, `db/` to the hub (`rsync -a --exclude .venv ./ <solarplexus alias>:~/corvid/repo/`), then `cd ~/corvid/repo && docker compose -f deploy/coordinator/compose.yaml up -d --build && docker compose -f deploy/coordinator/compose.yaml ps` → both `running (healthy)`; `curl -s http://127.0.0.1:8091/health` → `{"ok":true}`; `ss -tln | grep 8091` → `127.0.0.1:8091`; `docker compose … ps` shows no `0.0.0.0:5432`.
- [ ] **Step 3:** run file + commit.

### Task 8: Agents on the three nodes pointing at the hub

- [ ] **Step 1 (`executor: Opus`):** on each node, `agent.toml` `[coordinator] url = "http://solarplexus.<tailnet>.ts.net"`; install per Part A Task 7 (ahnoway already); on optiplex and the hub: `rsync` the repo's `agent/` + `deploy/agent/`, `python3 -m venv ~/corvid/venv && ~/corvid/venv/bin/pip install -e ~/corvid/repo/agent && bash ~/corvid/repo/deploy/agent/install-linux.sh ~/corvid/venv/bin/corvid`; `export XDG_RUNTIME_DIR=/run/user/1000` before `systemctl --user` on optiplex; hub needs linger (Phase 0 step 2).
- [ ] **Step 2:** `curl -s -H 'X-Corvid-User: <founder-login>' http://127.0.0.1:8091/api/v1/nodes` on the hub → three nodes `live`; from ahnoway `curl -s -o /dev/null -w '%{http_code}\n' http://solarplexus.<tailnet>.ts.net/status` → `200` (identity via forward_auth); the founder opens the page in a browser.

### Task 9: Acceptance (spec §7), ADR-0005/0007 references, hand back

- [ ] **Step 1 (`executor: Opus`):** run all ten acceptance checks exactly as written in spec §7 (node-down timing with `date` stamps; live cap with `systemctl --user show corvid.slice`; kill switch timing; fresh-config `offers: none`; nonce grep across `docker compose logs api db`, agent journals, Caddy log; bind check; fairness pytest; identity 401; CI green). Paste into `docs/runs/phase-2-<date>.md`; propose the status line `Phase 2 — roster: done <date> (3 nodes live; cap change <x> ms; kill <y> ms; no logging verified)`.
- [ ] **Step 2:** sanitise the run file; commit; `git push -u origin phase-2-coordinator`; **stop** (main session merges, updates `status.md`, marks CLAUDE.md §6 Phase 2).

### Task 10 (stretch, optional): Member chat — Open WebUI behind the front door + ADR "chat front-end"

- [ ] Only after Task 9 passes and the founder says go: write ADR-0008 "Chat front-end: Open WebUI" (licence = Open WebUI License, BSD-3 + branding clause; ≤ 50 users exemption; never rebrand; trusted-header auth `WEBUI_AUTH_TRUSTED_EMAIL_HEADER=X-Corvid-User`, `WEBUI_AUTH_TRUSTED_NAME_HEADER=X-Corvid-Name`; `ENABLE_ADMIN_CHAT_ACCESS=false`; `ENABLE_COMMUNITY_SHARING=false`; `ENABLE_VERSION_UPDATE_CHECK=false`; telemetry env per R08-F8; `OPENAI_API_BASE_URL=http://127.0.0.1:8090/v1`), add it to the compose project on `127.0.0.1:8093`, route `/chat*` → `:8093` (amend ADR-0003), `add-dependency` row, acceptance: a member sees only their own chats; header spoofing from outside Caddy is impossible (backend loopback-only).

---

## Self-review record (writing-plans checklist, 2026-08-22)

1. **Spec coverage:** D7 → Tasks 1, 5, 7; D8 → Tasks 1–3; D9 → Task 4; D10 → Task 6 (+ forward_auth route); D11 → Task 4 (template/pool); D12 → middleware + compose `command:` + Caddy log; D13 → Part A; D14 → Task 0 rows; D15 → Task 5 runbook; §7 acceptance → Task 9; stretch Open WebUI → Task 10.
2. **Placeholders:** none of the forbidden tokens; every code step shows code; `<…>` are runtime inputs.
3. **Consistency:** route names, header names (`X-Corvid-User`/`X-Corvid-Name`), ports (8090–8093), unit/slice names match Part A and the spec; `claim()` ORDER BY implements the fair-share rule as spec D8 states (orders, never refuses).
