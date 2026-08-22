# Package definition-of-done run — 2026-08-22 (spec §12; plan Task 32)

```
dossiers: 11 (expect 11: R00–R10)
R00-phase0-facts.md UNVERIFIED=3 rows=10
R01-fleet-and-network.md UNVERIFIED=14 rows=31
R02-tailscale-membership-acls-dns-identity.md UNVERIFIED=21 rows=40
R03-llamacpp-rpc-on-this-fleet.md UNVERIFIED=12 rows=31
R04-model-selection-phase1.md UNVERIFIED=31 rows=49
R05-agent-platform-matrix.md UNVERIFIED=50 rows=65
R06-coordinator-and-schema.md UNVERIFIED=26 rows=44
R07-status-page-and-identity.md UNVERIFIED=19 rows=38
R08-chat-frontend-phase1.md UNVERIFIED=18 rows=36
R09-sharedllm-and-alternatives.md UNVERIFIED=17 rows=36
R10-hub-integration-and-phase-3-5-outlines.md UNVERIFIED=26 rows=45
README.md UNVERIFIED=1 rows=0
specs: 4 (expect 4)
plans: 4 (expect 4: phase-0, phase-1, phase-2 part A, part B)
plans without executor tags: 0 (expect 0)
ADRs: docs/adr/0001-compute-is-a-commons.md docs/adr/0002-membership.md docs/adr/0003-endpoints.md docs/adr/0004-exit-criteria-one-lan-fleet.md docs/adr/0005-contribution-is-a-slider.md docs/adr/0007-presence-and-gpu-sharing.md 
skills: 5 (expect 5); workflow: .claude/workflows/research-sweep.js; ci: .github/workflows/ci.yml
spike cards: docs/research/spikes/S-02-llamacpp-install-per-node.md docs/research/spikes/S-03-tiny-rpc-split.md docs/research/spikes/S-06-linux-idle-battery-livecaps.md 
placeholder lint: ok
bind-target lint: ok
INFO    -  Documentation built in 1.55 seconds
```

## Verdict

- R00–R10: **11/11 exist**; facts sourced+dated or spiked; UNVERIFIED listed per file. Completeness-critic items missing for R01/R03/R05/R07/R08/R09/R10 (first sweep hit the usage limit; re-run wf_736a0d16-37b in progress).
- Specs Phase 0/1/2 + Phase 3–5 outline: **done**. Plans Phase 0/1/2 (A+B): **done**, every step executor-tagged, writing-plans self-review recorded.
- ADR-0002, 0003 (Accepted + amendment), 0004, 0005, 0007: **done**; ADR-0006 (topology) intentionally not written (host stays on the hub unless S-04 says otherwise).
- Skills, hooks, CI, research-sweep workflow: **exist and exercised** (CI green on main; sweep ran 209/220 agents).
- **Pending (blocks the m2 tag, not the documents):** spikes S-01 (bandwidth exception + Plex idle), S-04 (model download + per-node exceptions + RPC firewall rules), S-05 (operator mode on ahnoway); the guard-hook false-positive fix (classifier blocked Claude editing the hook); completeness-critic re-run results to fold into 7 dossiers.
