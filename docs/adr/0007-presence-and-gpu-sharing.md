# ADR-0007 — Presence is best-effort (UNKNOWN never counts as idle); GPU sharing is temporal

- **Status:** Accepted
- **Date:** 2026-08-22
- **Deciders:** founder (via the Phase 2 spec, 2026-08-22)
- **Related:** CLAUDE.md §5.2 (idle-only by default; battery), §3.3; ADR-0005; dossier R05 (recs 4, 6, 11; open questions on KDE/GNOME idle); spike S-06; Phase 2 spec D4/D5

## Context

Idle detection differs per desktop: on the founder's KDE Plasma Wayland session logind's `IdleHint` answers while `org.freedesktop.ScreenSaver.GetSessionIdleTime` is unsupported (S-06); GNOME exposes a Mutter D-Bus idle monitor; Wayland compositors offer `ext-idle-notify-v1`; X11 has `xprintidle`; macOS and Windows have their own APIs (R05). No single provider is universal, and a wrong "idle" verdict would violate CLAUDE.md §5.2 by running work while a friend is at the keyboard. Consumer NVIDIA GPUs cannot be partitioned (no MIG; MPS targets datacenter parts; cgroup v2 has no GPU controller), so "10 % of the GPU" has no enforceable meaning (R05 rec 6).

## Decision

1. **Presence is computed by a provider chain with an explicit UNKNOWN state.** Providers are tried in order (Wayland `ext-idle-notify-v1` helper, logind `IdleHint`, GNOME Mutter, `xprintidle`; macOS `HIDIdleTime` and Windows `GetLastInputInfo` later). The first provider that answers wins.
2. **UNKNOWN never counts as idle.** With no provider answer, the agent treats the machine as *active* and runs no idle-gated work; the status page shows "presence unknown". Owners may still opt in to `run_if_user_active=true` per machine.
3. **Battery:** on AC loss with `run_on_batteries=false` (default) the agent pauses work immediately, not at the next heartbeat.
4. **GPU sharing is temporal, not spatial:** a job or an inference host gets the whole GPU for a time window or not at all (`gpu_allowed` per machine; `DeviceAllow`/visible-devices for "GPU off"); VRAM ceilings are planned by the coordinator (tensor split, model choice) and reported as the slider's `vram_cap_mb`, not enforced by a driver cap.

## Consequences

- Agent v0 implements the chain (Phase 2 Part A, `presence.py`) and the `is_idle_enough` rule; R05's open questions (does KDE set `IdleHint` after its timeout? which `ext-idle-notify-v1` client route?) are spiked in Phase 2/4.
- The politeness UI (Phase 4) shows the provider in use and "unknown" honestly.
- Inference hosting on a member GPU means that GPU is *busy* for the duration — the status page's capacity maths treats VRAM as all-or-nothing per node.
- Reopening: a reliable cross-desktop presence API, or NVIDIA consumer-GPU partitioning, would change 2 or 4.

## CLAUDE.md §4 rows added in this commit

none.
