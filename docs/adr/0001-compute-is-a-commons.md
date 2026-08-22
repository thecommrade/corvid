# ADR-0001 — Compute is a commons

- **Status:** Accepted (founder, 2026-08-22)
- **Deciders:** founder
- **Supersedes / related:** CLAUDE.md §1 (friends-scale trust), §3.4 (thank-you board, never a
  currency), §5 (politeness policy), §7 (non-goals), §10 (front-page contract)

## Context

The first design question for the pool was whether shared capacity is **allocated per member**
(everyone gets a slice, sized evenly or by contribution) or **pooled** (everyone draws from one
shared pool as needed). The founder's stated goals: the number of members should grow, the
pooled compute should grow with it, privacy is key, and member data must stay separated —
while developers need a simple target to build member-facing software for non-technical users.

## Decision

1. **Compute is one shared pool. No member owns a slice.** When the pool is idle anyone may
   use all of it. When it is contended, the scheduler shares it fairly (max-min fair share);
   fairness is a *scheduling* behaviour, not an entitlement or an account.
2. **No per-member quotas, concurrency caps, anti-starvation limits, or anything tied to
   contribution history.** Every member is fully trusted, for as long as they are a member,
   regardless of how long since — or whether — they have contributed a machine.
   Contributions are thanked (CLAUDE.md §3.4), never counted against anyone.
3. **Data is hard-partitioned per member.** Identity comes from the mesh on every request
   (zero-login). Each member's chats, jobs and results, photo library, and backups are owned
   by that member and invisible to other members. Default posture: no prompt/content logging
   anywhere; backups are client-side encrypted with keys the member holds.
4. **The host owner's own machine always wins locally** (CLAUDE.md §5: opt-in, idle-only,
   owner-set caps, instant kill switch). This is a member's control over their *own* hardware,
   not a limit on anyone's use of the pool.
5. **Honest privacy limit (CLAUDE.md §5.7):** the node running a model sees that request in
   memory. CORVID offers friends-trust and data separation, not confidential compute, and says
   so to members in plain language.

## Why pooling (and not allocation)

- A model too large for any single machine needs the *whole* pool at once; per-member slices
  make the pool's defining capability structurally impossible.
- The project's arithmetic ("20 machines at 20% ≈ 4 flat-out") is statistical multiplexing of
  idle time; fixed slices sit idle while their owner sleeps and the gain evaporates.
- Allocation is the slope toward accounting → ledger → currency, which §7 forbids.
- "Thresholds, not timelines" — products unlock *for everyone* when the pool reaches a
  capacity — is a statement about a commons.
- Consumers who contribute nothing (phones, non-technical members) are welcome without an
  awkward "what do non-contributors get?" rule.

## Consequences

- The coordinator needs a fair-share queue, not a quota system. No quota tables, no per-member
  limits, no credit weighting — YAGNI until the founder says otherwise.
- Every member-facing service must attribute requests to a member identity and isolate data
  per member (per-member accounts in apps such as Immich; per-member chat history; member-held
  backup keys).
- Developer experience: one pool API (inference endpoint, job queue, later storage) with
  identity already attached; separation is per-service accounts, not per-app quota logic.
- The dashboard shows pool capacity, utilisation, and how close the next product threshold is;
  contributions appear only as thanks.
- If hogging ever becomes a real problem, the answer is a conversation between friends — and
  only if that fails, a new ADR. Not a silent limit.
