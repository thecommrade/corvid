# ADR-0003 — Endpoints: CORVID ports and the Caddy front door on the hub

- **Status:** Proposed (Accepted with the Phase 1 spec, M3)
- **Date:** 2026-08-22
- **Deciders:** founder
- **Related:** CLAUDE.md §3.2 (the `solarplexus:8080` line), §5.6 (tailnet-bound listeners), §11 (URLs not installers); ADR-0001; R00-F7 (ports in use), R00-D11 (identity headers); package spec §3.9c, §5 step 6, §7

## Context

CLAUDE.md §3.2 says friends get private AI at `http://solarplexus:8080`, but **port 8080 on solarplexus is already taken** by a pre-existing service (R00-F7: ports 22 53 139 445 631 1492 2019 2283 4533 5055 5109 6767 6789 6881 7474 7878 8080 8191 8265 8266 8686 8989 9696 23959 32400 32401 32469 32600 34254 54774 are listening). Caddy already runs on the hub as a reverse proxy (admin API on 2019). CLAUDE.md §11 wants one landing URL and per-service paths; §5.6 wants every listener bound to the tailnet interface only.

## Decision (proposed)

1. **Ports on solarplexus, bound to the tailnet IP only** (8090–8093 are free per R00-F7; if a later check finds one taken, shift the whole block by +10 and update this ADR):
   - `8090` — inference endpoint (`llama-server`, OpenAI-compatible `/v1`)
   - `8091` — coordinator API (Phase 2)
   - `8092` — status page (Phase 2)
   - `8093` — chat UI (Phase 1, R08 choice)
2. **Caddy is CORVID's front door**, listening on the hub's tailnet IP `:80` (and `:443` via `tailscale cert` once HTTPS certificates are enabled on the tailnet), routing `/` → landing page (static, CLAUDE.md §10 copy), `/chat` → `:8093`, `/v1` → `:8090`, `/api` → `:8091`, `/status` → `:8092`. Caddy access logs carry metadata only — never request bodies (ADR-0001 no-logging posture).
3. **The member URL is `http://solarplexus.<tailnet>.ts.net/`** (MagicDNS). Identity reaches the apps via Tailscale (headers when fronted by `tailscale serve`, else `whois` from the connecting IP — R00-D11; S-05 decides which the Phase 1 spec uses).
4. On acceptance, CLAUDE.md §3.2's `:8080` sentence is replaced by the Caddy URL + `:8090` (package spec §3.9c).

## Consequences

- Phase 0 step 6 reserves the ports (no service yet); Phase 1 deploys `llama-server` on `8090` and the chat UI on `8093` behind Caddy; Phase 2 adds `8091`/`8092`.
- Caddy becomes a CORVID dependency → its CLAUDE.md §4 row is added in this commit (below).
- Pre-existing `0.0.0.0` listeners of the media stack on the hub are not CORVID's and are out of scope; CORVID's own listeners are tailnet-bound (CI lint enforces for repo-managed services).

## CLAUDE.md §4 rows added in this commit

| Caddy | Reverse proxy / front door for CORVID's tailnet web apps (already on the hub) | Apache-2.0 (verified at github.com/caddyserver/caddy LICENSE, 2026-08-22) | Matt Holt & the Caddy contributors (a ZeroSSL project) |
