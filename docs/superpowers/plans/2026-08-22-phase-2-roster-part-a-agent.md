# Phase 2 — The Roster, Part A (agent v0): Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (or superpowers:subagent-driven-development for the pure-repo tasks 1–6) in an **Opus** session on ahnoway. Steps use checkbox (`- [ ]`) syntax. Executor tags: **`Opus`** (unattended), **`Opus (splx-root)`**, **`founder`** (handoff protocol). TDD: write the failing test, run it, implement, run it, commit. Part B (coordinator, status page, Caddy, deployment, acceptance) is `2026-08-22-phase-2-roster-part-b-coordinator.md`; Part A's deliverable is an agent that is fully tested locally and can run against a fake coordinator.

**Goal:** A Linux agent (`corvid-agent`, Python ≥ 3.12) that loads/validates/live-reloads `~/.config/corvid/agent.toml`, reports presence/power/capabilities, enforces the owner's slider on `corvid.slice`, heartbeats to the coordinator with only opted-in roles, and provides the kill switch — with unit tests and a user service unit.

**Architecture:** Small modules behind interfaces (`Runner` for subprocesses, `Provider` for presence/power, `HttpPoster` for heartbeats) so tests use fakes; a single `corvid` CLI (`run`, `stop`, `start`, `status`, `config-check`); a `corvid.slice` + `corvid-agent.service` pair of user units; no root anywhere.

**Tech Stack:** Python 3.12+ (stdlib `tomllib`, `urllib.request`, `subprocess`, `uuid`), `psutil` (battery), `pytest`, `ruff`; systemd user units (`systemd-run`, `systemctl --user set-property`), `loginctl`.

**Spec:** `docs/superpowers/specs/2026-08-22-phase-2-roster-design.md` §3 D1–D6, D13; **read also** `CLAUDE.md`, `docs/status.md`, `R05`, spike `S-06`, ADR-0005, ADR-0007, package spec Appendix A/B.

## Global Constraints

- Python 3.12+; project venv `.venv` (`.venv/bin/pip install -e './agent[dev]'`); `ruff format` + `ruff check` clean (the PostToolUse hook runs ruff on every `.py` edit); `pytest -q` green before each commit.
- Never require root; never bind a port (the agent is outbound-only); never log job payloads or identity values.
- Config defaults = spec D2 (`offers` all false; `cpu_quota_pct=10`; `mem_max_gb=1.6`; `vram_cap_mb=800`; `io_idle=true`; `run_if_user_active=false`; `idle_minutes=5`; `run_on_batteries=false`; `suspend_cpu_usage_pct=25`; `schedule=[]`; `heartbeat_seconds=10`).
- `CPUQuota` for the slice = `cpu_quota_pct × os.cpu_count()` percent (10 % of 12 threads → `120%`), `MemoryMax=<mem_max_gb>G`.
- Branch `phase-2-agent`; conventional commits + `Co-Authored-By` trailer; `add-dependency` §4 rows in the same commit as `pyproject.toml` (psutil BSD-3; pytest/ruff are dev tools — credited in the tool row, no §4 row needed unless shipped).
- Placeholders `<…>` are runtime inputs; never write IPs/usernames into the repo.

## File Structure

| Path | Responsibility |
|---|---|
| `agent/pyproject.toml` | package `corvid-agent`, entrypoint `corvid = corvid_agent.cli:main`, deps `psutil`; dev `pytest`, `ruff` |
| `agent/src/corvid_agent/__init__.py` | version string |
| `agent/src/corvid_agent/config.py` | `AgentConfig` dataclass, `load(path) -> AgentConfig`, validation, `ConfigWatcher` (mtime poll) |
| `agent/src/corvid_agent/runner.py` | `Runner` protocol + `SubprocessRunner`; tests use `FakeRunner` |
| `agent/src/corvid_agent/caps.py` | `SliceController.apply(cfg)` → `systemctl --user set-property corvid.slice CPUQuota=… MemoryMax=…`; `cpu_quota_percent(pct, cores)` |
| `agent/src/corvid_agent/presence.py` | `Presence` enum (IDLE/ACTIVE/UNKNOWN), providers: `LogindProvider`, `XprintidleProvider`, `WaylandIdleProvider` (UNKNOWN until the helper exists), `PresenceChain` |
| `agent/src/corvid_agent/power.py` | `PowerState(on_battery: bool|None, percent)` via psutil → sysfs fallback |
| `agent/src/corvid_agent/heartbeat.py` | `build_payload(cfg, presence, power, gpu, node_id, version)`, `HttpPoster`, `HeartbeatLoop` with backoff |
| `agent/src/corvid_agent/gpu.py` | `nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader,nounits` → dict or None |
| `agent/src/corvid_agent/killswitch.py` | `KILL` flag path, `stop()`/`start()`/`is_killed()` |
| `agent/src/corvid_agent/cli.py` | `corvid run|stop|start|status|config-check` |
| `agent/tests/test_*.py` | unit tests with fakes |
| `deploy/agent/corvid.slice`, `deploy/agent/corvid-agent.service`, `deploy/agent/install-linux.sh` | units + installer (user-level) |

---

### Task 0: Branch, package skeleton, dev install

**Files:** Create `agent/pyproject.toml`, `agent/src/corvid_agent/__init__.py`, `agent/tests/__init__.py`, `agent/README.md`; Modify `CLAUDE.md` §4 (psutil row)

- [ ] **Step 1 (`executor: Opus`):** `git checkout -b phase-2-agent`
- [ ] **Step 2 (`executor: Opus`): Write `agent/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "corvid-agent"
version = "0.1.0"
description = "CORVID node agent v0 (Linux): presence, power, slider caps, heartbeat, kill switch"
requires-python = ">=3.12"
license = { text = "MIT" }
dependencies = ["psutil>=5.9"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6"]

[project.scripts]
corvid = "corvid_agent.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 3 (`executor: Opus`):** `mkdir -p agent/src/corvid_agent agent/tests && printf '__version__ = "0.1.0"\n' > agent/src/corvid_agent/__init__.py && touch agent/tests/__init__.py && printf '# corvid-agent\n\nLinux node agent v0 — see docs/superpowers/specs/2026-08-22-phase-2-roster-design.md.\n' > agent/README.md`
- [ ] **Step 4 (`executor: Opus`):** `.venv/bin/pip install --quiet -e './agent[dev]' && .venv/bin/python -c 'import corvid_agent, psutil; print(corvid_agent.__version__)'` → `0.1.0`
- [ ] **Step 5 (`executor: Opus`): §4 row (`add-dependency`)** — append to CLAUDE.md §4: `| psutil | Cross-platform battery/AC and process info in the agent | BSD-3-Clause | Giampaolo Rodola & contributors |`
- [ ] **Step 6 (`executor: Opus`):** `git add agent CLAUDE.md && git commit -m "feat(agent): package skeleton + psutil §4 credit"` (+ trailer)

### Task 1: Config load / validate / defaults

**Files:** Create `agent/src/corvid_agent/config.py`, `agent/tests/test_config.py`

**Interfaces:** Produces `AgentConfig` (dataclass with `offers`, `caps`, `politeness`, `coordinator` sub-dataclasses), `load(path: Path) -> AgentConfig`, `ConfigError`, `ConfigWatcher(path).changed() -> bool`.

- [ ] **Step 1: Failing tests**

```python
# agent/tests/test_config.py
from pathlib import Path
import pytest
from corvid_agent.config import AgentConfig, ConfigError, load, ConfigWatcher

def test_defaults_when_file_missing(tmp_path: Path):
    cfg = load(tmp_path / "agent.toml")
    assert cfg.offers.inference_host is False and cfg.offers.batch_jobs is False
    assert cfg.offers.gpu_allowed is False and cfg.offers.disk_donate is False
    assert cfg.caps.cpu_quota_pct == 10 and cfg.caps.mem_max_gb == 1.6 and cfg.caps.vram_cap_mb == 800
    assert cfg.politeness.run_if_user_active is False and cfg.politeness.idle_minutes == 5
    assert cfg.politeness.run_on_batteries is False and cfg.coordinator.heartbeat_seconds == 10

def test_parses_overrides(tmp_path: Path):
    p = tmp_path / "agent.toml"
    p.write_text('[offers]\ninference_host = true\n[caps]\ncpu_quota_pct = 25\nmem_max_gb = 4\n[coordinator]\nurl = "http://hub.example"\n')
    cfg = load(p)
    assert cfg.offers.inference_host is True and cfg.caps.cpu_quota_pct == 25 and cfg.caps.mem_max_gb == 4.0
    assert cfg.coordinator.url == "http://hub.example"

@pytest.mark.parametrize("body", ['[caps]\ncpu_quota_pct = 0\n', '[caps]\ncpu_quota_pct = 101\n', '[caps]\nmem_max_gb = -1\n', '[politeness]\nidle_minutes = -5\n', 'not = [toml'])
def test_rejects_invalid(tmp_path: Path, body: str):
    p = tmp_path / "agent.toml"; p.write_text(body)
    with pytest.raises(ConfigError):
        load(p)

def test_offers_none_when_all_false(tmp_path: Path):
    assert load(tmp_path / "agent.toml").offers.enabled() == []

def test_watcher_detects_change(tmp_path: Path):
    p = tmp_path / "agent.toml"; p.write_text("[caps]\ncpu_quota_pct = 10\n")
    w = ConfigWatcher(p); assert w.changed() is False
    import os, time; time.sleep(0.01); p.write_text("[caps]\ncpu_quota_pct = 20\n"); os.utime(p, None)
    assert w.changed() is True and w.changed() is False
```

- [ ] **Step 2:** `.venv/bin/pytest -q agent/tests/test_config.py` → FAIL (`ModuleNotFoundError`/`ImportError`).
- [ ] **Step 3: Implement**

```python
# agent/src/corvid_agent/config.py
from __future__ import annotations
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

class ConfigError(ValueError):
    pass

@dataclass
class Offers:
    inference_host: bool = False
    batch_jobs: bool = False
    gpu_allowed: bool = False
    disk_donate: bool = False
    def enabled(self) -> list[str]:
        return [k for k, v in self.__dict__.items() if v]

@dataclass
class Caps:
    cpu_quota_pct: int = 10      # percent of the whole machine
    mem_max_gb: float = 1.6
    vram_cap_mb: int = 800
    io_idle: bool = True

@dataclass
class Politeness:
    run_if_user_active: bool = False
    idle_minutes: int = 5
    run_on_batteries: bool = False
    suspend_cpu_usage_pct: int = 25
    schedule: list[str] = field(default_factory=list)

@dataclass
class Coordinator:
    url: str = ""
    heartbeat_seconds: int = 10

@dataclass
class AgentConfig:
    offers: Offers = field(default_factory=Offers)
    caps: Caps = field(default_factory=Caps)
    politeness: Politeness = field(default_factory=Politeness)
    coordinator: Coordinator = field(default_factory=Coordinator)

def _section(data: dict, name: str, cls):
    raw = data.get(name, {})
    if not isinstance(raw, dict):
        raise ConfigError(f"[{name}] must be a table")
    unknown = set(raw) - set(cls.__dataclass_fields__)
    if unknown:
        raise ConfigError(f"[{name}] unknown keys: {sorted(unknown)}")
    try:
        return cls(**raw)
    except TypeError as e:
        raise ConfigError(f"[{name}] {e}") from e

def _validate(cfg: AgentConfig) -> None:
    c, p, co = cfg.caps, cfg.politeness, cfg.coordinator
    if not (1 <= int(c.cpu_quota_pct) <= 100): raise ConfigError("caps.cpu_quota_pct must be 1..100")
    if float(c.mem_max_gb) <= 0: raise ConfigError("caps.mem_max_gb must be > 0")
    if int(c.vram_cap_mb) < 0: raise ConfigError("caps.vram_cap_mb must be >= 0")
    if int(p.idle_minutes) < 0: raise ConfigError("politeness.idle_minutes must be >= 0")
    if not (0 <= int(p.suspend_cpu_usage_pct) <= 100): raise ConfigError("politeness.suspend_cpu_usage_pct must be 0..100")
    if int(co.heartbeat_seconds) < 1: raise ConfigError("coordinator.heartbeat_seconds must be >= 1")
    for w in p.schedule:
        if not isinstance(w, str) or "-" not in w: raise ConfigError(f"politeness.schedule window invalid: {w!r}")
    c.cpu_quota_pct = int(c.cpu_quota_pct); c.mem_max_gb = float(c.mem_max_gb); c.vram_cap_mb = int(c.vram_cap_mb)

def load(path: Path) -> AgentConfig:
    path = Path(path)
    if not path.exists():
        cfg = AgentConfig(); _validate(cfg); return cfg
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path}: {e}") from e
    cfg = AgentConfig(offers=_section(data, "offers", Offers), caps=_section(data, "caps", Caps),
                      politeness=_section(data, "politeness", Politeness), coordinator=_section(data, "coordinator", Coordinator))
    _validate(cfg)
    return cfg

class ConfigWatcher:
    """mtime-poll watcher (inotify is an optional upgrade); changed() is True once per modification."""
    def __init__(self, path: Path):
        self.path = Path(path); self._last = self._stamp()
    def _stamp(self):
        try:
            st = self.path.stat(); return (st.st_mtime_ns, st.st_size)
        except FileNotFoundError:
            return None
    def changed(self) -> bool:
        now = self._stamp()
        if now != self._last:
            self._last = now; return True
        return False
```

- [ ] **Step 4:** `.venv/bin/pytest -q agent/tests/test_config.py` → PASS (all).
- [ ] **Step 5:** `git add agent && git commit -m "feat(agent): config load/validate/defaults + watcher (TDD)"` (+ trailer)

### Task 2: Runner interface + slice controller (caps)

**Files:** Create `agent/src/corvid_agent/runner.py`, `agent/src/corvid_agent/caps.py`, `agent/tests/test_caps.py`

**Interfaces:** `Runner.run(args: list[str]) -> tuple[int, str, str]`; `cpu_quota_percent(pct, cores) -> int`; `SliceController(runner, slice_name="corvid.slice").apply(caps) -> list[str]` (returns the argv used); `SliceController.stop_all()`.

- [ ] **Step 1: Failing tests**

```python
# agent/tests/test_caps.py
from corvid_agent.config import Caps
from corvid_agent.caps import SliceController, cpu_quota_percent

class FakeRunner:
    def __init__(self): self.calls = []
    def run(self, args):
        self.calls.append(list(args)); return (0, "", "")

def test_cpu_quota_percent_scales_with_cores():
    assert cpu_quota_percent(10, 12) == 120 and cpu_quota_percent(10, 4) == 40 and cpu_quota_percent(100, 1) == 100

def test_apply_sets_properties_live():
    r = FakeRunner(); sc = SliceController(r, cores=12)
    argv = sc.apply(Caps(cpu_quota_pct=10, mem_max_gb=1.6))
    assert argv[:4] == ["systemctl", "--user", "set-property", "corvid.slice"]
    assert "CPUQuota=120%" in argv and "MemoryMax=1.6G" in argv and r.calls == [argv]

def test_stop_all_stops_slice():
    r = FakeRunner(); SliceController(r, cores=4).stop_all()
    assert r.calls == [["systemctl", "--user", "stop", "corvid.slice"]]
```

- [ ] **Step 2:** run → FAIL. **Step 3: Implement**

```python
# agent/src/corvid_agent/runner.py
from __future__ import annotations
import subprocess
from typing import Protocol

class Runner(Protocol):
    def run(self, args: list[str]) -> tuple[int, str, str]: ...

class SubprocessRunner:
    def run(self, args: list[str]) -> tuple[int, str, str]:
        p = subprocess.run(args, capture_output=True, text=True, timeout=20)
        return p.returncode, p.stdout, p.stderr
```

```python
# agent/src/corvid_agent/caps.py
from __future__ import annotations
import os
from .config import Caps
from .runner import Runner

def cpu_quota_percent(pct: int, cores: int) -> int:
    return max(1, int(round(pct * cores)))

class SliceController:
    def __init__(self, runner: Runner, slice_name: str = "corvid.slice", cores: int | None = None):
        self.runner = runner; self.slice = slice_name; self.cores = cores or (os.cpu_count() or 1)
    def apply(self, caps: Caps) -> list[str]:
        argv = ["systemctl", "--user", "set-property", self.slice,
                f"CPUQuota={cpu_quota_percent(caps.cpu_quota_pct, self.cores)}%", f"MemoryMax={caps.mem_max_gb}G"]
        rc, _, err = self.runner.run(argv)
        if rc != 0:
            raise RuntimeError(f"set-property failed rc={rc}: {err.strip()[:200]}")
        return argv
    def stop_all(self) -> None:
        self.runner.run(["systemctl", "--user", "stop", self.slice])
```

- [ ] **Step 4:** run → PASS. **Step 5:** commit `feat(agent): slice controller for live caps (TDD)`.

### Task 3: Presence providers with UNKNOWN (ADR-0007)

**Files:** Create `agent/src/corvid_agent/presence.py`, `agent/tests/test_presence.py`

**Interfaces:** `Presence` enum (`IDLE`, `ACTIVE`, `UNKNOWN`); `Provider.sample() -> tuple[Presence, int|None]` (idle seconds when known); `LogindProvider(runner, session_id)`, `XprintidleProvider(runner)`, `WaylandIdleProvider()` (returns UNKNOWN until the helper exists — documented), `PresenceChain(providers).sample()` returns the first non-UNKNOWN result; `is_idle_enough(sample, idle_minutes) -> bool` (UNKNOWN → False).

- [ ] **Step 1: Failing tests**

```python
# agent/tests/test_presence.py
from corvid_agent.presence import Presence, LogindProvider, XprintidleProvider, WaylandIdleProvider, PresenceChain, is_idle_enough

class R:
    def __init__(self, out, rc=0): self.out, self.rc = out, rc
    def run(self, args): return (self.rc, self.out, "")

def test_logind_idle_hint_yes_with_since():
    p = LogindProvider(R("IdleHint=yes\nIdleSinceHint=1700000000000000\n"), session_id="2", now_us=lambda: 1700000600000000)
    assert p.sample() == (Presence.IDLE, 600)

def test_logind_idle_hint_no():
    assert LogindProvider(R("IdleHint=no\nIdleSinceHint=0\n"), session_id="2").sample() == (Presence.ACTIVE, 0)

def test_logind_failure_is_unknown():
    assert LogindProvider(R("", rc=1), session_id="2").sample()[0] is Presence.UNKNOWN

def test_xprintidle_ms_to_seconds():
    assert XprintidleProvider(R("125000\n")).sample() == (Presence.ACTIVE, 125)  # 125 s idle reported; idle-enough decided by the chain

def test_wayland_helper_missing_is_unknown():
    assert WaylandIdleProvider(helper_path="/nonexistent").sample()[0] is Presence.UNKNOWN

def test_chain_takes_first_known():
    chain = PresenceChain([WaylandIdleProvider(helper_path="/nonexistent"), LogindProvider(R("IdleHint=yes\nIdleSinceHint=0\n"), "2")])
    assert chain.sample()[0] is Presence.IDLE

def test_unknown_never_counts_as_idle():
    assert is_idle_enough((Presence.UNKNOWN, None), idle_minutes=0) is False
    assert is_idle_enough((Presence.IDLE, 600), idle_minutes=5) is True
    assert is_idle_enough((Presence.IDLE, 60), idle_minutes=5) is False
    assert is_idle_enough((Presence.ACTIVE, 700), idle_minutes=5) is True   # xprintidle style: seconds since input
```

- [ ] **Step 2:** run → FAIL. **Step 3: Implement**

```python
# agent/src/corvid_agent/presence.py
from __future__ import annotations
import os, time
from enum import Enum
from typing import Callable, Iterable, Protocol
from .runner import Runner

class Presence(Enum):
    IDLE = "idle"; ACTIVE = "active"; UNKNOWN = "unknown"

Sample = tuple[Presence, int | None]   # (state, idle seconds if known)

class Provider(Protocol):
    def sample(self) -> Sample: ...

class LogindProvider:
    """logind IdleHint/IdleSinceHint for the current session (observed to answer on KDE Wayland, S-06)."""
    def __init__(self, runner: Runner, session_id: str | None = None, now_us: Callable[[], int] | None = None):
        self.runner = runner; self.session = session_id or os.environ.get("XDG_SESSION_ID", "")
        self.now_us = now_us or (lambda: int(time.time() * 1_000_000))
    def sample(self) -> Sample:
        if not self.session: return (Presence.UNKNOWN, None)
        rc, out, _ = self.runner.run(["loginctl", "show-session", self.session, "-p", "IdleHint", "-p", "IdleSinceHint"])
        if rc != 0: return (Presence.UNKNOWN, None)
        kv = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
        hint = kv.get("IdleHint", "").strip()
        if hint == "yes":
            try: since = int(kv.get("IdleSinceHint", "0")); idle_s = max(0, (self.now_us() - since) // 1_000_000) if since else 0
            except ValueError: idle_s = 0
            return (Presence.IDLE, idle_s)
        if hint == "no": return (Presence.ACTIVE, 0)
        return (Presence.UNKNOWN, None)

class XprintidleProvider:
    def __init__(self, runner: Runner): self.runner = runner
    def sample(self) -> Sample:
        rc, out, _ = self.runner.run(["xprintidle"])
        if rc != 0 or not out.strip().isdigit(): return (Presence.UNKNOWN, None)
        return (Presence.ACTIVE, int(out.strip()) // 1000)   # seconds since last input; the chain decides idle-enough

class WaylandIdleProvider:
    """ext-idle-notify-v1 via a small helper binary (to be spiked); UNKNOWN until it exists."""
    def __init__(self, helper_path: str = os.path.expanduser("~/.local/bin/corvid-idle-helper"), runner: Runner | None = None):
        self.helper = helper_path; self.runner = runner
    def sample(self) -> Sample:
        if not (self.runner and os.path.exists(self.helper)): return (Presence.UNKNOWN, None)
        rc, out, _ = self.runner.run([self.helper])
        if rc != 0 or not out.strip().isdigit(): return (Presence.UNKNOWN, None)
        return (Presence.ACTIVE, int(out.strip()))

class PresenceChain:
    def __init__(self, providers: Iterable[Provider]): self.providers = list(providers)
    def sample(self) -> Sample:
        for p in self.providers:
            s = p.sample()
            if s[0] is not Presence.UNKNOWN: return s
        return (Presence.UNKNOWN, None)

def is_idle_enough(sample: Sample, idle_minutes: int) -> bool:
    state, secs = sample
    if state is Presence.UNKNOWN: return False          # ADR-0007: UNKNOWN never counts as idle
    if secs is None: return state is Presence.IDLE and idle_minutes == 0
    return secs >= idle_minutes * 60
```

- [ ] **Step 4:** run → PASS. **Step 5:** commit `feat(agent): presence provider chain with UNKNOWN (ADR-0007) (TDD)`.

### Task 4: Power + GPU probes

**Files:** Create `agent/src/corvid_agent/power.py`, `agent/src/corvid_agent/gpu.py`, `agent/tests/test_power_gpu.py`

- [ ] **Step 1: Failing tests**

```python
# agent/tests/test_power_gpu.py
from pathlib import Path
from corvid_agent.power import read_power, PowerState
from corvid_agent.gpu import parse_nvidia_smi

def test_sysfs_fallback_detects_battery(tmp_path: Path):
    (tmp_path / "ADP1").mkdir(); (tmp_path / "ADP1" / "online").write_text("0\n")
    (tmp_path / "BAT1").mkdir(); (tmp_path / "BAT1" / "capacity").write_text("57\n")
    assert read_power(sysfs_root=tmp_path, psutil_battery=lambda: None) == PowerState(on_battery=True, percent=57)

def test_sysfs_ac_online(tmp_path: Path):
    (tmp_path / "AC").mkdir(); (tmp_path / "AC" / "online").write_text("1\n")
    assert read_power(sysfs_root=tmp_path, psutil_battery=lambda: None).on_battery is False

def test_psutil_preferred():
    class B: power_plugged = False; percent = 42.0
    assert read_power(sysfs_root=Path("/nonexistent"), psutil_battery=lambda: B()) == PowerState(on_battery=True, percent=42)

def test_unknown_when_nothing(tmp_path: Path):
    assert read_power(sysfs_root=tmp_path, psutil_battery=lambda: None).on_battery is None

def test_parse_nvidia_smi():
    assert parse_nvidia_smi("NVIDIA GeForce RTX 2070 Super, 8192, 7500, 610.57.04\n") == {"name": "NVIDIA GeForce RTX 2070 Super", "vram_total_mb": 8192, "vram_free_mb": 7500, "driver": "610.57.04"}
    assert parse_nvidia_smi("") is None
```

- [ ] **Step 2:** FAIL. **Step 3: Implement**

```python
# agent/src/corvid_agent/power.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

@dataclass(frozen=True)
class PowerState:
    on_battery: bool | None     # None = unknown
    percent: int | None

def _psutil_battery():
    try:
        import psutil; return psutil.sensors_battery()
    except Exception:
        return None

def read_power(sysfs_root: Path = Path("/sys/class/power_supply"), psutil_battery: Callable = _psutil_battery) -> PowerState:
    b = psutil_battery()
    if b is not None:
        return PowerState(on_battery=not bool(getattr(b, "power_plugged", True)), percent=int(getattr(b, "percent", 0) or 0))
    online = None; percent = None
    if sysfs_root.exists():
        for d in sysfs_root.iterdir():
            n = d.name
            if (n.startswith("AC") or n.startswith("ADP")) and (d / "online").exists():
                online = (d / "online").read_text().strip() == "1"
            if n.startswith("BAT") and (d / "capacity").exists():
                try: percent = int((d / "capacity").read_text().strip())
                except ValueError: percent = None
    if online is None: return PowerState(on_battery=None, percent=percent)
    return PowerState(on_battery=not online, percent=percent)
```

```python
# agent/src/corvid_agent/gpu.py
from __future__ import annotations
from .runner import Runner

QUERY = ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", "--format=csv,noheader,nounits"]

def parse_nvidia_smi(out: str) -> dict | None:
    line = (out or "").strip().splitlines()
    if not line: return None
    parts = [p.strip() for p in line[0].split(",")]
    if len(parts) < 4: return None
    try:
        return {"name": parts[0], "vram_total_mb": int(float(parts[1])), "vram_free_mb": int(float(parts[2])), "driver": parts[3]}
    except ValueError:
        return None

def read_gpu(runner: Runner) -> dict | None:
    try:
        rc, out, _ = runner.run(QUERY)
    except Exception:
        return None
    return parse_nvidia_smi(out) if rc == 0 else None
```

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(agent): power (psutil→sysfs) and GPU probes (TDD)`.

### Task 5: Heartbeat payload + poster + loop; kill switch; node id

**Files:** Create `agent/src/corvid_agent/heartbeat.py`, `agent/src/corvid_agent/killswitch.py`, `agent/tests/test_heartbeat.py`

**Interfaces:** `build_payload(cfg, presence_sample, power, gpu, node_id, version, state) -> dict` (only opted-in offers; `gpu` only when `gpu_allowed`); `HttpPoster(url).post(payload) -> int` (status code; `urllib`); `HeartbeatLoop(cfg_path, poster, runner, clock, sleep).run_once()`; `KillSwitch(dir).is_killed()/stop()/start()`; `node_id(dir) -> str` (uuid4 persisted).

- [ ] **Step 1: Failing tests**

```python
# agent/tests/test_heartbeat.py
from pathlib import Path
from corvid_agent.config import AgentConfig, Offers
from corvid_agent.presence import Presence
from corvid_agent.power import PowerState
from corvid_agent.heartbeat import build_payload, node_id
from corvid_agent.killswitch import KillSwitch

def test_payload_offers_none_by_default():
    p = build_payload(AgentConfig(), (Presence.UNKNOWN, None), PowerState(None, None), {"name": "x"}, "nid", "0.1.0", "ok")
    assert p["offers"] == {} and "gpu" not in p and p["presence"] == "unknown" and p["node_id"] == "nid"
    assert p["caps_effective"]["cpu_quota_pct"] == 10 and p["state"] == "ok"

def test_payload_includes_gpu_only_when_allowed():
    cfg = AgentConfig(offers=Offers(gpu_allowed=True))
    p = build_payload(cfg, (Presence.IDLE, 900), PowerState(False, 90), {"name": "g", "vram_total_mb": 1, "vram_free_mb": 1, "driver": "d"}, "n", "v", "ok")
    assert p["offers"] == {"gpu_allowed": True} and p["gpu"]["name"] == "g" and p["on_battery"] is False and p["presence"] == "idle"

def test_payload_never_contains_paths_or_identity(tmp_path: Path):
    p = build_payload(AgentConfig(), (Presence.ACTIVE, 0), PowerState(True, 10), None, "n", "v", "killed")
    assert "owner" not in p and "home" not in str(p).lower()

def test_node_id_persists(tmp_path: Path):
    a = node_id(tmp_path); b = node_id(tmp_path)
    assert a == b and len(a) == 36 and (tmp_path / "node_id").exists()

def test_killswitch(tmp_path: Path):
    k = KillSwitch(tmp_path)
    assert k.is_killed() is False; k.stop(); assert k.is_killed() is True; k.start(); assert k.is_killed() is False
```

- [ ] **Step 2:** FAIL. **Step 3: Implement**

```python
# agent/src/corvid_agent/killswitch.py
from __future__ import annotations
from pathlib import Path

class KillSwitch:
    def __init__(self, config_dir: Path): self.flag = Path(config_dir) / "KILL"
    def is_killed(self) -> bool: return self.flag.exists()
    def stop(self) -> None: self.flag.parent.mkdir(parents=True, exist_ok=True); self.flag.write_text("stopped by owner\n")
    def start(self) -> None:
        try: self.flag.unlink()
        except FileNotFoundError: pass
```

```python
# agent/src/corvid_agent/heartbeat.py
from __future__ import annotations
import json, os, platform, time, uuid, urllib.request, urllib.error
from dataclasses import asdict
from pathlib import Path
from typing import Callable
from .caps import SliceController
from .config import AgentConfig, ConfigError, ConfigWatcher, load
from .gpu import read_gpu
from .killswitch import KillSwitch
from .power import PowerState, read_power
from .presence import Presence, PresenceChain, Sample, is_idle_enough
from .runner import Runner

def node_id(config_dir: Path) -> str:
    p = Path(config_dir) / "node_id"
    if p.exists():
        v = p.read_text().strip()
        if len(v) == 36: return v
    p.parent.mkdir(parents=True, exist_ok=True); v = str(uuid.uuid4()); p.write_text(v + "\n"); return v

def build_payload(cfg: AgentConfig, presence: Sample, power: PowerState, gpu: dict | None, nid: str, version: str, state: str) -> dict:
    offers = {k: True for k in cfg.offers.enabled()}
    payload = {
        "node_id": nid, "agent_version": version, "os": platform.system().lower(), "arch": platform.machine(),
        "offers": offers, "caps_effective": asdict(cfg.caps), "presence": presence[0].value,
        "idle_seconds": presence[1], "on_battery": power.on_battery, "battery_percent": power.percent,
        "load1": os.getloadavg()[0] if hasattr(os, "getloadavg") else None, "state": state,
    }
    if cfg.offers.gpu_allowed and gpu: payload["gpu"] = gpu
    return payload

class HttpPoster:
    def __init__(self, base_url: str, timeout: float = 5.0): self.url = base_url.rstrip("/") + "/api/v1/heartbeat"; self.timeout = timeout
    def post(self, payload: dict) -> int:
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r: return r.status
        except urllib.error.HTTPError as e: return e.code
        except Exception: return 0

class HeartbeatLoop:
    """One tick = reload config if changed → apply slice caps → sample presence/power/gpu → post. Backoff on failures (5 s → 60 s)."""
    def __init__(self, cfg_path: Path, runner: Runner, chain: PresenceChain, poster_factory: Callable[[str], HttpPoster] = HttpPoster,
                 version: str = "0.1.0", config_dir: Path | None = None, sleep: Callable[[float], None] = time.sleep):
        self.cfg_path = Path(cfg_path); self.config_dir = Path(config_dir or self.cfg_path.parent)
        self.runner = runner; self.chain = chain; self.poster_factory = poster_factory; self.version = version; self.sleep = sleep
        self.cfg = AgentConfig(); self.watcher = ConfigWatcher(self.cfg_path); self.slice = SliceController(runner)
        self.kill = KillSwitch(self.config_dir); self.nid = node_id(self.config_dir); self.backoff = 5; self.state = "ok"
        self._reload(force=True)
    def _reload(self, force: bool = False) -> None:
        if force or self.watcher.changed():
            try:
                self.cfg = load(self.cfg_path); self.slice.apply(self.cfg.caps); self.state = "ok" if self.state != "killed" else "killed"
            except (ConfigError, RuntimeError):
                self.state = "config_error"     # keep last good config
    def run_once(self) -> int:
        self._reload()
        if self.kill.is_killed():
            self.state = "killed"; self.slice.stop_all()
        presence = self.chain.sample(); power = read_power()
        if power.on_battery and not self.cfg.politeness.run_on_batteries and self.state == "ok": self.state = "paused"
        elif self.state == "paused" and not power.on_battery: self.state = "ok"
        gpu = read_gpu(self.runner) if self.cfg.offers.gpu_allowed else None
        payload = build_payload(self.cfg, presence, power, gpu, self.nid, self.version, self.state)
        payload["idle_enough"] = is_idle_enough(presence, self.cfg.politeness.idle_minutes)
        status = self.poster_factory(self.cfg.coordinator.url).post(payload) if self.cfg.coordinator.url else 0
        self.backoff = 5 if status in (200, 201, 202, 204) else min(60, self.backoff * 2)
        return status
    def run_forever(self) -> None:
        while True:
            status = self.run_once()
            self.sleep(self.cfg.coordinator.heartbeat_seconds if status in (200, 201, 202, 204) else self.backoff)
```

- [ ] **Step 4:** PASS. **Step 5:** commit `feat(agent): heartbeat payload/loop, kill switch, node id (TDD)`.

### Task 6: CLI

**Files:** Create `agent/src/corvid_agent/cli.py`, `agent/tests/test_cli.py`

- [ ] **Step 1: Failing tests**

```python
# agent/tests/test_cli.py
from pathlib import Path
from corvid_agent.cli import main

def test_config_check_ok(tmp_path: Path, capsys):
    (tmp_path / "agent.toml").write_text("[caps]\ncpu_quota_pct = 15\n")
    assert main(["--config-dir", str(tmp_path), "config-check"]) == 0
    assert "cpu_quota_pct=15" in capsys.readouterr().out

def test_config_check_bad(tmp_path: Path):
    (tmp_path / "agent.toml").write_text("[caps]\ncpu_quota_pct = 0\n")
    assert main(["--config-dir", str(tmp_path), "config-check"]) == 2

def test_stop_start_flag(tmp_path: Path, monkeypatch):
    calls = []
    monkeypatch.setattr("corvid_agent.cli.SubprocessRunner.run", lambda self, a: (calls.append(a) or (0, "", "")))
    assert main(["--config-dir", str(tmp_path), "stop"]) == 0 and (tmp_path / "KILL").exists()
    assert ["systemctl", "--user", "stop", "corvid.slice"] in calls
    assert main(["--config-dir", str(tmp_path), "start"]) == 0 and not (tmp_path / "KILL").exists()
```

- [ ] **Step 2:** FAIL. **Step 3: Implement**

```python
# agent/src/corvid_agent/cli.py
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
from . import __version__
from .caps import SliceController
from .config import ConfigError, load
from .heartbeat import HeartbeatLoop
from .killswitch import KillSwitch
from .presence import LogindProvider, PresenceChain, WaylandIdleProvider, XprintidleProvider
from .runner import SubprocessRunner

def default_config_dir() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "corvid"

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="corvid", description="CORVID node agent v0")
    ap.add_argument("--config-dir", default=str(default_config_dir()))
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("run", "stop", "start", "status", "config-check"): sub.add_parser(c)
    a = ap.parse_args(argv); cdir = Path(a.config_dir); cfg_path = cdir / "agent.toml"; runner = SubprocessRunner()
    if a.cmd == "config-check":
        try:
            cfg = load(cfg_path)
        except ConfigError as e:
            print(f"config error: {e}", file=sys.stderr); return 2
        print(f"ok: offers={cfg.offers.enabled() or 'none'} cpu_quota_pct={cfg.caps.cpu_quota_pct} mem_max_gb={cfg.caps.mem_max_gb} "
              f"idle_minutes={cfg.politeness.idle_minutes} run_on_batteries={cfg.politeness.run_on_batteries}"); return 0
    if a.cmd == "stop":
        KillSwitch(cdir).stop(); SliceController(runner).stop_all(); print("CORVID work stopped on this machine (flag set)."); return 0
    if a.cmd == "start":
        KillSwitch(cdir).start(); print("kill flag cleared; the agent resumes on its next tick."); return 0
    if a.cmd == "status":
        k = KillSwitch(cdir); print(f"agent {__version__} · config {cfg_path} · killed={k.is_killed()} · node_id={(cdir / 'node_id').read_text().strip() if (cdir / 'node_id').exists() else 'unset'}"); return 0
    if a.cmd == "run":
        chain = PresenceChain([WaylandIdleProvider(runner=runner), LogindProvider(runner), XprintidleProvider(runner)])
        HeartbeatLoop(cfg_path, runner, chain, version=__version__, config_dir=cdir).run_forever(); return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4:** PASS; `.venv/bin/ruff check agent && .venv/bin/ruff format --check agent`. **Step 5:** commit `feat(agent): corvid CLI (run/stop/start/status/config-check) (TDD)`.

### Task 7: Units, installer, local run against a fake coordinator

**Files:** Create `deploy/agent/corvid.slice`, `deploy/agent/corvid-agent.service`, `deploy/agent/install-linux.sh`, `agent/tests/test_fake_coordinator.py`

- [ ] **Step 1 (`executor: Opus`): Unit files**

```ini
# deploy/agent/corvid.slice
[Unit]
Description=CORVID work slice — all CORVID processes on this machine live here (kill: systemctl --user stop corvid.slice)
[Slice]
CPUQuota=120%
MemoryMax=1.6G
```

```ini
# deploy/agent/corvid-agent.service
[Unit]
Description=CORVID node agent v0 (presence, power, slider, heartbeat)
After=network-online.target
[Service]
Slice=corvid.slice
ExecStart=%h/.local/bin/corvid run
Restart=always
RestartSec=5
KillMode=control-group
Nice=19
[Install]
WantedBy=default.target
```

```bash
#!/usr/bin/env bash
# deploy/agent/install-linux.sh — user-level install (no root). Usage: bash install-linux.sh [path-to-corvid-entrypoint]
set -euo pipefail
BIN="${1:-$(command -v corvid || echo "$PWD/.venv/bin/corvid")}"
mkdir -p ~/.local/bin ~/.config/systemd/user ~/.config/corvid
ln -sf "$BIN" ~/.local/bin/corvid
cp "$(dirname "$0")/corvid.slice" "$(dirname "$0")/corvid-agent.service" ~/.config/systemd/user/
[ -f ~/.config/corvid/agent.toml ] || printf '[offers]\n# nothing is offered until you say so (CLAUDE.md §5.1)\n[caps]\ncpu_quota_pct = 10\nmem_max_gb = 1.6\n[coordinator]\nurl = ""\n' > ~/.config/corvid/agent.toml
systemctl --user daemon-reload && systemctl --user enable --now corvid-agent.service
systemctl --user is-active corvid-agent.service && echo "corvid-agent running in corvid.slice (edit ~/.config/corvid/agent.toml; 'corvid stop' is the kill switch)"
```

- [ ] **Step 2 (`executor: Opus`): Fake-coordinator test (end-to-end, no network outside loopback)**

```python
# agent/tests/test_fake_coordinator.py
import json, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from corvid_agent.heartbeat import HeartbeatLoop, HttpPoster
from corvid_agent.presence import PresenceChain

class FakeRunner:
    def run(self, a): return (0, "", "")

def test_heartbeat_reaches_fake_coordinator(tmp_path: Path):
    got = []
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers["Content-Length"]); got.append(json.loads(self.rfile.read(n))); self.send_response(200); self.end_headers()
        def log_message(self, *a): pass
    srv = HTTPServer(("127.0.0.1", 0), H); t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    (tmp_path / "agent.toml").write_text(f'[coordinator]\nurl = "http://127.0.0.1:{srv.server_port}"\n')
    loop = HeartbeatLoop(tmp_path / "agent.toml", FakeRunner(), PresenceChain([]), config_dir=tmp_path)
    assert loop.run_once() == 200 and got[0]["offers"] == {} and got[0]["presence"] == "unknown"
    srv.shutdown()
```
Run `.venv/bin/pytest -q agent` → PASS (all).

- [ ] **Step 3 (`executor: Opus`): Install on ahnoway and watch it tick (against the fake: leave `url = ""` so it only applies caps)**

```bash
bash deploy/agent/install-linux.sh "$PWD/.venv/bin/corvid"
systemctl --user show corvid.slice -p CPUQuotaPerSecUSec -p MemoryMax          # 1.2s / 1.6G-equivalent
sed -i 's/cpu_quota_pct = 10/cpu_quota_pct = 5/' ~/.config/corvid/agent.toml; sleep 6; systemctl --user show corvid.slice -p CPUQuotaPerSecUSec   # 600ms within ≤ 5 s
corvid stop; systemctl --user is-active corvid.slice || echo "slice inactive"; pgrep -f corvid_agent || echo "no agent processes"; corvid start; systemctl --user start corvid-agent
```
Expected: quota follows the file edit; `corvid stop` empties the slice within ~50 ms (S-06); restart clean. Record in the run file.

- [ ] **Step 4 (`executor: Opus`):** `bash scripts/lint-bind-targets.sh && .venv/bin/ruff check agent && .venv/bin/pytest -q agent` → all ok; commit `feat(agent): units, installer, fake-coordinator e2e`; push branch; **hand to Part B**.

---

## Self-review record (writing-plans checklist, 2026-08-22)

1. **Spec coverage:** D1 (service + slice + kill) → Tasks 2, 5, 6, 7; D2 (config + live reload) → Tasks 1, 5; D3 (kill switch) → Tasks 5, 6, 7; D4 (presence chain, UNKNOWN, battery) → Tasks 3, 4, 5; D5 (GPU report only) → Task 4/5; D6 (heartbeat payload, node_id) → Task 5; D13 (caps mechanics) → Task 2/7; D14 psutil row → Task 0. Spec §7 acceptance 3/4/5 are exercised in Task 7 Step 3; the rest need Part B.
2. **Placeholders:** none of the forbidden tokens; every code step shows the code.
3. **Consistency:** names `AgentConfig/Offers/Caps/Politeness/Coordinator`, `SliceController.apply/stop_all`, `PresenceChain.sample`, `KillSwitch.is_killed/stop/start`, `node_id`, `build_payload`, `HttpPoster.post`, `HeartbeatLoop.run_once/run_forever` are used identically across tasks; unit names `corvid.slice`/`corvid-agent.service` match the spec and `deploy/agent/`.
