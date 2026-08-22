# ADR-0004 — Exit criteria on a one-LAN build fleet

- **Status:** Accepted
- **Date:** 2026-08-22
- **Deciders:** founder
- **Related:** CLAUDE.md §6 (Phase 0 and Phase 1 exits), §8 ("honesty over cheerleading"); ADR-0002; package spec §5, §7, §10; R00-F10

## Context

CLAUDE.md §6 defines the Phase 0 exit as "everyone pings everyone by MagicDNS name **across houses**" and the Phase 1 exit as "a friend gets a completion from a model spread across **two houses**." The founder decided that only three machines — ahnoway, solarplexus, optiplex — are used for *building*, and all three share one LAN (R00-F10). Friends' machines are future members, not build nodes, and installing CORVID software on a friend's machine is out of scope for the planning package. Read literally, neither exit can be declared inside the package; quietly redefining them would violate CLAUDE.md §8. One friend's Windows machine is already reachable (shared node, ADR-0002) and can answer a name-ping when online.

## Decision

1. **Phase 0 is complete when** (a) the three build nodes name-ping each other in all pairs over the tailnet (MagicDNS), **and** (b) at least one cross-house name-ping succeeds — from a build node to a friend's device (Zach's shared node while online, or any invited member's device under ADR-0002). (b) is an `executor: founder` step: a phone call — "install Tailscale / accept the invite" — no CORVID software, no written guide.
2. **Phase 1 splits into two recorded events:** (i) the **thesis** — a completion from a model that meets the "impossible on one machine" criterion (package spec §7: weights + KV cache at the chosen quantisation exceed the largest single node's VRAM + free RAM), split across the build nodes, with tok/s and GB numbers recorded — accepted on the LAN trio; (ii) the **cross-house completion** — a friend's machine hosts layers or a friend gets a completion from another house — a named follow-on owned by the founder, triggered by the first member machine coming online, and recorded in `docs/status.md` when it happens.
3. CLAUDE.md §6 wording is **not** edited; `docs/status.md` marks each phase with both halves ("mechanics: done / across houses: pending|done").

## Consequences

- The Phase 0 plan includes step 7(b) (cross-house ping) as a founder step with a copy-pasteable phone script.
- The Phase 1 spec's acceptance tests cover (i) only; (ii) is listed under "follow-ons" with its trigger.
- Nothing in the charter is weakened: both halves must eventually be true; what changes is *when* each half can be observed.
- If a friend's machine becomes a build node later, this ADR can be superseded by simply meeting the original wording.

## CLAUDE.md §4 rows added in this commit

none.
