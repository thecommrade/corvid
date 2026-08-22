# ADR-0005 — Contribution is a slider

- **Status:** Accepted
- **Date:** 2026-08-22
- **Deciders:** founder
- **Related:** CLAUDE.md §5.1–§5.4 (opt-in, idle-only, owner-set caps, kill switch), §9 Q5 (the founder's own caps); ADR-0001 (commons — consumption is never limited by contribution); package spec Appendix B; spike S-06; Phase 2 spec D2/D13

## Context

The founder's decision on 2026-08-22 (status.md decision 10): "users should decide per machine how much they are contributing; eventually that may advance into how much they are using, and it could become dynamic — but that would also be a choice." CLAUDE.md §5.3 already requires owner-set caps enforced locally; the founder added that caps must be adjustable *on the fly*. S-06 measured the Linux mechanism: `systemctl --user set-property` on a running unit took 3 ms and CPU fell from 99 % to 29 %; the kill switch (`systemctl --user stop`) took 49 ms. The package spec's Appendix B defaults (~10 % of each device) are test defaults, not policy.

## Decision

1. **Each owner sets, per machine, how much it contributes** — the *slider*: CPU share of the whole machine (`cpu_quota_pct`), RAM (`mem_max_gb`), VRAM ceiling (`vram_cap_mb`, planned by the coordinator since consumer GPUs cannot be partitioned), IO class, allowed hours (`schedule`), and the roles offered (`offers`: inference host, batch jobs, GPU, disk) — all in the agent's config (`~/.config/corvid/agent.toml`) and, in Phase 4, in the tray UI.
2. **Changes apply live** — no restart: the agent watches the file and applies the new values to the CORVID slice within ≤ 5 s (measured ms on Linux). The same path implements the kill switch (everything in the slice stops within ≤ 2 s).
3. **Defaults:** on install **nothing is offered** (CLAUDE.md §5.1); when the owner opts in, the slider starts at the Appendix-B-equivalent (≈ 10 % CPU/RAM, a small VRAM ceiling) and the owner moves it from there. The founder's machines follow the same rule (CLAUDE.md §9 Q5).
4. **A future, optional, per-owner mode** may link a machine's contribution to its owner's usage dynamically ("contribute roughly what I use") — always the owner's choice, never imposed, and **never a limit on consumption** (ADR-0001 stands). It is not built in Phases 0–2; its hook is that the slider already has an *effective* value the agent reports every heartbeat.
5. Temporary increases for demos or spikes are **exceptions** requested from and granted by the owner (the founder for the build nodes), time-boxed and recorded (package spec §6.3).

## Consequences

- The agent config schema and heartbeat payload (Phase 2 spec D2/D6) carry the slider and its effective value; the status page shows capped capacity, never raw hardware.
- Phase 4's tray is a view on the same config file; there is no second source of truth.
- The coordinator never overrides a slider; it only plans within offered capacity (VRAM via tensor split).
- Reopening this ADR: if owners ask for per-role sliders (different caps for inference vs jobs) or the usage-linked mode becomes wanted.

## CLAUDE.md §4 rows added in this commit

none.
