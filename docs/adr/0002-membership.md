# ADR-0002 — Membership: friends join as tailnet users, not shared nodes

- **Status:** Accepted
- **Date:** 2026-08-22
- **Deciders:** founder
- **Related:** CLAUDE.md §3.1 (Tailscale first; Headscale escape hatch), §5 (politeness), §11 (zero-login identity); ADR-0001 (data partition per member); R00-D6/D7/D8/D9/D12, R00-F6; package spec §5 step 4

## Context

CORVID members must be *identities on the mesh*: CLAUDE.md §11 promises zero-login ("Tailscale identity tells the server who is connecting") and ADR-0001 partitions data per member. Two ways exist to put a friend's machine on the tailnet: **invite them as a tailnet user**, or **share** a node from their own tailnet. R00-D8 (Tailscale docs, verified 2026-08-22): sharing is one-directional — "Shared machines are quarantined by default. They can respond to incoming connections from the tailnet they're shared to, but cannot start connections on their own" — the recipient does not become a member, and shared users appear as `autogroup:shared`. A member's agent must *initiate* heartbeats to the hub (CLAUDE.md §3.3), and a member's browser must reach the hub's services; both fail for a shared-in node. R00-D9: the Personal (free) plan allows **up to 6 users, unlimited user devices**. R00-D7: node keys expire after 180 days by default; R00-D6: Tailscale SSH default policy is check-mode to one's own devices. One friend (Zach) currently reaches the tailnet via a shared node; a phone (consumer device) is a member device already.

## Decision

1. **Members are invited as tailnet users.** Node sharing is not used for membership (it may remain for one-off device access). A friend joins by accepting the invite and installing Tailscale on the machines they choose — the first line of the onboarding index card (CLAUDE.md §11).
2. **Ceiling:** the Personal plan's 6 users (dated 2026-08-22). When the 7th member appears, revisit: Personal-plan change, a paid tier (breaks the $0 rule → needs a decision), or the documented **Headscale** escape hatch (CLAUDE.md §3.1). Record the choice in a new ADR then.
3. **ACL baseline (privacy between friends' machines):** tags `tag:hub` (solarplexus, optiplex, ahnoway-as-builder) and `tag:member` (members' contributing machines); rules allow `tag:member → tag:hub` on CORVID service ports (ADR-0003) and `tag:hub → tag:member` on agent/rpc ports; **member ↔ member is denied by default**. Consumer-only devices (phones) reach `tag:hub` service ports only. The ssh section keeps the default check-mode for users' own devices; the founder's own devices may use `accept` for unattended automation (Phase 0 step 0 decides; founder edits the policy). The live policy text is recorded in R00 once the founder pastes it (open question).
4. **Key expiry is disabled on the three build nodes** (admin console, `executor: founder`); members keep the default 180-day expiry and re-authenticate (their agent/tray will say so in Phase 4).
5. **Zach:** invited as a user when he is ready (founder phone call); his shared node can still satisfy ADR-0004's cross-house name-ping until then.

## Consequences

- Phase 0 step 4 (package spec §5) is this ADR; Phase 0 step 3 is decision 4; the onboarding card's step 1 is decision 1.
- Zero-login and per-member data partition are feasible as designed: every request from a member device carries a tailnet identity (R00-D11 headers / `whois`).
- The ACL must be edited by the founder (admin console) before the first member joins; until then the default allow-all (R00-D12) is acceptable for the founder's own three nodes.
- Member count is capped at 6 on the free plan; CORVID's "friends-scale" fits, but a 7th friend forces the next decision (see 2).

## CLAUDE.md §4 rows added in this commit

none (Tailscale is already credited).

## Amendment (2026-08-22, with the Phase 2 spec)

**Member devices are never tagged.** Tagged Tailscale nodes carry no user identity (serve headers and `whois` return tags, not a login — R07-F21/F22/F24), which would break zero-login and ADR-0001's per-member partition. Tags go on hubs only (`tag:hub`); the member side of the ACL baseline in decision 3 is expressed with users / `autogroup:member` rather than `tag:member`. Agents authenticate as their owner by running on the owner's untagged device.

