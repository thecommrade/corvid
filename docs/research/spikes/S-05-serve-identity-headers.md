# S-05 — serve-identity-headers

- **Goal:** runtime truth for zero-login (R07 rec 6, five steps): (1) do
  `Tailscale-User-Login/-Name/-Profile-Pic` headers appear on `tailscale serve --http=<port>`
  (no HTTPS feature, no CT-log exposure)? (2) does the HTTPS-cert prompt fire only for
  `--https`? (note, do not enable) (3) what source ip:port does a backend see behind serve?
  (4) does `tailscale whois <that ip:port>` resolve the peer while connected? (5) exact
  header names + LoginName format (email vs `user@github`). Solarplexus userspace leg
  (serve in userspace mode; whois on `127.0.0.1:<srcport>`) runs after Phase 0 step 2 work.
- **Node(s):** ahnoway (kernel mode, 1.102.3) now; solarplexus (userspace, 1.98.4) later
- **Executor:** main-session
- **Dependencies:** operator mode on ahnoway: founder runs `sudo tailscale set
  --operator=piratejohn` once (granted 2026-08-23). Peer requests come from optiplex
  (unprivileged curl over the tailnet).
- **Preconditions:** `docs/status.md` "Node in use by" empty · `tailscale serve status` empty
  on ahnoway before start (nothing else being served).
- **Cap (Appendix B):** trivial — a Python echo server on `127.0.0.1:8099` (loopback only;
  serve is the tailnet-facing listener). No exception needed.
- **Exception record:** none (operator-mode grant recorded above).
- **Time box:** 20 min
- **Expected signal:** curl from optiplex to `http://<ahnoway-100.x>:8099/` returns the echo
  page listing request headers incl. `Tailscale-User-Login`; whois resolves the connection to
  the founder's identity; header-squatting test: a client-sent `Tailscale-User-Login` header
  is deleted/replaced by serve.
- **Abort criteria / watch:** none beyond time box; nothing heavy runs.

## Commands (exact; every heavy command wrapped)

```bash
# echo server, loopback only (prints method, path, all headers as the response body)
python3 -c 'from http.server import *; \
  H=type("H",(BaseHTTPRequestHandler,),{"do_GET":lambda s:(s.send_response(200),s.end_headers(), \
  s.wfile.write(("\n".join(f"{k}: {v}" for k,v in s.headers.items())+f"\nclient={s.client_address}").encode()))}); \
  HTTPServer(("127.0.0.1",8099),H).serve_forever()' &
tailscale serve --bg --http=8099 http://127.0.0.1:8099
tailscale serve status
# from optiplex (unprivileged):
curl -s http://<ahnoway-100.x>:8099/            # headers present?
curl -s -H 'Tailscale-User-Login: fake@evil' http://<ahnoway-100.x>:8099/   # squat deleted?
# back on ahnoway, while a connection is open:
tailscale whois --json <client ip:port from the echo output>
```

## Undo (executed and confirmed at the end)

```bash
tailscale serve --http=8099 off; tailscale serve status   # expect empty
pkill -f '[h]ttp.server|[H]TTPServer' 2>/dev/null; ss -tln | grep ':8099' || echo no-listener
```

## Result

- **Ahnoway leg done 2026-08-23** (peer = the hub via `tailscale nc`; optiplex data path was
  broken — see run file finding 5): (1) headers injected on `--http` — Login (email format),
  Name, Profile-Pic, Headers-Info, X-Forwarded-For/-Host; (2) no HTTPS prompt for `--http`;
  (3) backend sees `127.0.0.1:<srcport>`; serve 404s requests whose Host isn't the MagicDNS
  name; (4) whois on the loopback proxy pair: peer not found; whois on a direct tailnet
  connection: resolves machine + user; (5) squatted identity headers are stripped/replaced.
- Solarplexus (userspace serve) leg: pending Phase 0 step 2.
- Raw evidence: `docs/runs/S-05-2026-08-23.md` (sanitised; header values withheld)

## Follow-ups

- File into R02 (zero-login mechanism, version-pinned) and R07 (identity plumbing; resolves
  the Phase 2 Part B Task 6 conditional branch: serve headers vs whois forward_auth).
- Solarplexus leg → R07 userspace/kernel whois facts; feeds ADR-0003 amendment if needed.
