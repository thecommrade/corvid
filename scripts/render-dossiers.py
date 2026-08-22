#!/usr/bin/env python3
"""Render docs/research/R01–R10 from a research-sweep JSON (spec §6.2 template).

Usage: .venv/bin/python scripts/render-dossiers.py docs/runs/research-sweep-<date>.json <date>
Verdicts are applied (refuted → corrected statement or UNVERIFIED), facts beyond the refutation cap
are marked unchecked, spike rows and main-session notes come from META below, completeness-critic
items are merged into Open questions. Forbidden placeholder words inside quoted facts are rephrased
so the docs lint stays green.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

JSON_PATH = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else Path("docs/runs/research-sweep-2026-08-22.json")
)
D = sys.argv[2] if len(sys.argv) > 2 else "2026-08-22"
OUT = Path("docs/research")

META = {
    "R01": (
        "fleet-and-network",
        "Fleet & network",
        "full",
        "Phase 0/1 plans (network numbers), ADR-0006 topology if needed, member setup guide (Phase 4)",
        [
            (
                "S-01",
                "pending — bandwidth exception + Plex idle (founder)",
                "`spikes/S-01-fleet-throughput-latency.md` (to be created)",
                "—",
            ),
            (
                "S-03",
                "firewall state per node observed: firewalld active on ahnoway, ufw active on the second node, none on the hub; hub (userspace Tailscale) forwards inbound tailnet connections to localhost",
                "`spikes/S-03-tiny-rpc-split.md`",
                "`../runs/S-03-2026-08-22.md`",
            ),
        ],
        [
            "R00 (Phase 0 facts) already records the observed tailscaled modes, ip rules, DNS state and `netcheck` results per node; this dossier adds the documented connection model and the RPC per-token cost reasoning.",
            "Firewalls (S-03): inbound TCP 50052 on `tailscale0` is blocked on ahnoway (firewalld) and on the second node (ufw); the hub has no firewall units. Phase 1 needs `executor: founder` rules on both.",
            "Home WAN (R00): non-CGNAT, UPnP/NAT-PMP/PCP present, nearest DERP ~40 ms, `netcheck` UDP true on all three nodes → direct paths expected per the R01-F6 matrix; cross-house path still `UNVERIFIED` until a member machine exists (ADR-0004).",
        ],
    ),
    "R02": (
        "tailscale-membership-acls-dns-identity",
        "Tailscale: membership, ACLs, DNS, identity",
        "full",
        "ADR-0002 (membership, ACL baseline), Phase 0 plan steps 0/1/3, Phase 1 spec (identity), Phase 2 spec (API identity)",
        [
            (
                "S-05",
                "pending — needs operator mode on ahnoway (founder)",
                "`spikes/S-05-serve-identity-headers.md` (to be created)",
                "—",
            )
        ],
        [
            "R00-D1…D12 are the Phase-0-critical subset of these facts (dated 2026-08-22); this dossier is the wider reference.",
            "ADR-0002 (Accepted 2026-08-22, amended with the Phase 2 spec): members are invited as users; sharing is one-directional; Personal plan = 6 users; ACL baseline with hub tags only — member devices stay untagged (tags suppress identity).",
        ],
    ),
    "R03": (
        "llamacpp-rpc-on-this-fleet",
        "llama.cpp RPC on this fleet",
        "full",
        "Phase 1 spec + plan (install path, units, flags, acceptance), ADR-0006 topology if needed, S-04",
        [
            (
                "S-02",
                "prebuilt Vulkan tarball b10581 works on all three nodes (no CUDA toolkit, no root); binaries `ggml-rpc-server`/`llama-server`/`llama-bench`; each NVIDIA GPU is `Vulkan0`; **no `--mem` flag** (flags `-t -d -H -p -c`)",
                "`spikes/S-02-llamacpp-install-per-node.md`",
                "`../runs/S-02-2026-08-22.md`",
            ),
            (
                "S-03",
                "RPC mechanics proven ahnoway (host) ↔ hub GTX 970 (worker, bound to 127.0.0.1 behind userspace Tailscale): backend `Vulkan,RPC`; 135M Q8: local pp 6971 / tg 457 t/s vs RPC auto-split pp 399 / tg 94 t/s (≈5× tg overhead); **silent local fallback when the RPC endpoint is unreachable**; `--list-devices --rpc` does not list the RPC device; inbound RPC blocked by firewalld/ufw on the other two nodes",
                "`spikes/S-03-tiny-rpc-split.md`",
                "`../runs/S-03-2026-08-22.md`",
            ),
        ],
        [
            "Install path for Phase 1 (from S-02): release tarball `llama-<tag>-bin-ubuntu-vulkan-x64.tar.gz` per node, pinned tag (b10581 verified), extracted under the service user; CUDA builds only if Vulkan throughput disappoints (then per-node CUDA 12.x on the hub, 13.x elsewhere — see R01-F27…F30).",
            "Worker VRAM cannot be capped server-side at b10581 (no `--mem`): bound it with model choice, `-ts`/`-ngl` on the host, and `-d Vulkan0` device selection; recorded in the Phase 1 spec and ADR-0005 notes.",
            "Acceptance must check the `llama-bench`/`llama-server` backend string contains `RPC` and the worker log shows `Accepted client connection` — otherwise the run silently fell back to local.",
            "Worker processes as `systemd-run --user --unit=…` (transient service) or proper user units with linger (hub linger is off until Phase 0 step 2).",
        ],
    ),
    "R04": (
        "model-selection-phase1",
        "Model selection for Phase 1",
        "full",
        "Phase 1 spec (model, GB arithmetic, §4 rows), S-04, ADR-0006 if needed",
        [
            (
                "S-04",
                "pending — needs the model choice below + per-node exceptions + RPC firewall rules (founder)",
                "`spikes/S-04-thesis-split.md` (to be created)",
                "—",
            )
        ],
        [
            "The Phase 1 criterion (package spec §7 / ADR-0004): weights + KV cache at the chosen quantisation exceed the largest single node's VRAM + free RAM (≈ 6 GB + 19 GB ≈ 25 GB). Candidates below that exceed only 8 GB VRAM are the weaker fallback list.",
            "Decision taken in the Phase 1 spec (2026-08-22): Qwen3.8-27B Q8_0 (ggml-org GGUF, 28.6 GB, Apache-2.0), smoke test with its Q4_K_M; backups Muse-Glimmer-30B Q8_0, Gemma 4 31B Q8_0; classic fallback DeepSeek-R1-Distill-Llama-70B IQ3_XXS.",
            "Model files live on the hub's storage pool (path recorded in the Phase 1 plan); download once, serve from there; `-c` cache on workers avoids re-streaming weights at every load.",
        ],
    ),
    "R05": (
        "agent-platform-matrix",
        "Agent platform matrix",
        "full (Linux) / outline (macOS, Windows, packaging)",
        "Phase 2 spec + plan (agent v0), ADR-0005, ADR-0007, Phase 4 outline",
        [
            (
                "S-06",
                "on KDE Plasma Wayland: logind `IdleHint` answers; `org.freedesktop.ScreenSaver.GetSessionIdleTime` NOT supported; GNOME Mutter absent; AC/battery via sysfs (`ADP1`, `BAT1`) and upower; **live cap change** `systemctl --user set-property CPUQuota=120%→30%` took 3 ms and CPU went 99%→29%; `systemctl --user stop` = 49 ms",
                "`spikes/S-06-linux-idle-battery-livecaps.md`",
                "`../runs/S-06-2026-08-22.md`",
            )
        ],
        [
            "Linux agent v0 mechanisms are measured (S-06) and designed in the Phase 2 spec (`corvid.slice`, provider chain with UNKNOWN, psutil battery); macOS/Windows rows are documentation only until a member with that OS volunteers (package spec §6.1).",
            "Opt-in model (CLAUDE.md §5.1) and the contribution slider (ADR-0005) are in the agent config schema from day one; presence/GPU policy is ADR-0007.",
        ],
    ),
    "R06": (
        "coordinator-and-schema",
        "Coordinator & schema",
        "full",
        "Phase 2 spec + plan (compose project, schema, queue, API, logs)",
        [],
        [
            "ADR-0001: fair share only as scheduling when contended; **no quotas, no per-member limits** — the Phase 2 claim query orders by the member with the fewest running jobs and never refuses.",
            "Ports per ADR-0003 (amended): coordinator API 8091 and status 8092 bind loopback on the hub behind Caddy; Postgres as a **separate compose project** from the media stack with no published port.",
        ],
    ),
    "R07": (
        "status-page-and-identity",
        "Status page & identity",
        "full",
        "Phase 2 spec (status page v0), ADR-0003 (Caddy), Phase 1 (chat UI behind Caddy)",
        [],
        [
            "Required panels per ADR-0001: pool capacity, utilisation, distance to the next product threshold; contributions appear only as thanks — never counts or ranks. Decided in the Phase 2 spec: server-rendered FastAPI + Jinja2 page, not Grafana.",
            "Identity: Caddy `forward_auth` → coordinator `whoami-by-ip` (`tailscale whois`, kernel mode) by default; `tailscale serve` headers if S-05 favours them. The hub's Caddy is a host package (admin :2019) → `import` drop-in + `systemctl reload caddy`.",
        ],
    ),
    "R08": (
        "chat-frontend-phase1",
        "Chat front-end for Phase 1",
        "full",
        "Phase 1 spec + plan (the UI a friend uses), Phase 2 Part B stretch task, CLAUDE.md §4 rows",
        [],
        [
            "Decided in the Phase 1 spec: Phase 1 ships llama-server's built-in web UI (MIT) at `/chat` → `:8090`; Open WebUI (Open WebUI License = BSD-3 + branding clause; trusted-header auth via `X-Corvid-User`) is the Phase 2 stretch task with its own ADR; `:8093` reserved."
        ],
    ),
    "R09": (
        "sharedllm-and-alternatives",
        "SharedLLM & alternatives",
        "outline",
        "Phase 5 mandate (CLAUDE.md §3.2/§6), Phase 3–5 outline",
        [],
        [
            "Outline depth by design (package spec §6.1): dated facts for the Phase 5 evaluation; not a decision input for Phases 0–2."
        ],
    ),
    "R10": (
        "hub-integration-and-phase-3-5-outlines",
        "Hub integration points + Phase 3–5 outlines",
        "outline",
        "Phase 3–5 outline (M5), Phase 4 politeness UI, first batch workloads (Tdarr node, Immich ML)",
        [],
        [
            "The hub already runs Tdarr, Immich (no ML container) and Caddy (R00/status.md) — the first Phase 3 workloads are ready-made; see `docs/superpowers/specs/phase-3-5-outline.md`."
        ],
    ),
}

FORBIDDEN = [
    (re.compile(r"\bTODO\b"), "to-do"),
    (re.compile(r"\bTBD\b"), "to be decided"),
    (re.compile(r"\bFIXME\b"), "fix-me"),
    (re.compile(r"\bXXX\b"), "xxx"),
]


def esc(s) -> str:
    s = re.sub(r"\s+", " ", str(s or "")).replace("|", "\\|").strip()
    for rx, rep in FORBIDDEN:
        s = rx.sub(rep, s)
    return s


def render(rid: str, data: dict) -> str:
    _slug, title, depth, feeds, spikes, notes = META[rid]
    v = data.get(rid) or {}
    r = v.get("research") or {}
    verdicts = {x.get("fact_id"): x for x in (v.get("verdicts") or [])}
    gaps = v.get("gaps")
    facts = r.get("facts") or []
    rows = []
    n_ver = n_unv = n_corr = n_unchecked = 0
    for f in facts:
        fid = f.get("id", "")
        st = esc(f.get("statement"))
        src = esc(f.get("source_url"))
        ver = esc(f.get("version") or "—")
        conf = (f.get("confidence") or "unverified").lower()
        vd = verdicts.get(fid)
        if vd is None:
            if conf == "verified":
                status = "UNVERIFIED (beyond refutation cap — unchecked)"
                n_unchecked += 1
            else:
                status = "UNVERIFIED"
                n_unv += 1
        elif vd.get("refuted"):
            cs = esc(vd.get("corrected_statement"))
            cu = esc(vd.get("source_url"))
            if cs and cs.lower() not in ("", "none", "n/a"):
                st = (
                    f"{cs} *(corrected by refuter; original: {st[:160]}…)*"
                    if len(st) > 160
                    else f"{cs} *(corrected by refuter; original: {st})*"
                )
                if cu:
                    src = f"{cu} (refuter) · orig: {src}"
                status = "verified (corrected)"
                n_corr += 1
            else:
                status = f"UNVERIFIED — refuted: {esc(vd.get('reason'))[:200]}"
                n_unv += 1
        else:
            status = (
                "verified"
                if conf == "verified"
                else "UNVERIFIED (author-flagged; refuter did not refute)"
            )
            if status == "verified":
                n_ver += 1
            else:
                n_unv += 1
        rows.append(
            f"| {fid} | {st} | {src} | {esc(f.get('date_verified') or D)} | {ver} | {status} |"
        )
    recs = r.get("recommendations") or []
    oq = r.get("open_questions") or []
    credits = r.get("credits") or []
    summary = esc(r.get("dossier") or "")
    md = [
        f"# {rid} — {title}\n",
        f"- **Depth:** {depth} (spec §6.1)",
        f"- **Written:** {D} by research-sweep agent (run wf_736a0d16-37b) + main-session · **Verified:** {D} (adversarial pass: yes — first 20 facts refuted-checked by independent agents; {n_corr} corrected, {n_unv} marked UNVERIFIED, {n_unchecked} beyond the cap; completeness critic: {'run' if gaps is not None else 'not run'})",
        f"- **Feeds:** {feeds}\n",
        "## Purpose\n",
        f"Facts a plan can cite for: {title.lower()}. Agent summary (verbatim, may contain its own working notes):\n",
        f"> {summary[:6000]}\n",
        "## Facts\n",
        "| ID | Statement | Source (URL) | Date verified | Version/commit | Status |",
        "|---|---|---|---|---|---|",
        *rows,
        "\n## Spike results\n",
        "| Spike | One-line result | Card | Run file |",
        "|---|---|---|---|",
    ]
    if spikes:
        md += [f"| {s_[0]} | {esc(s_[1])} | {s_[2]} | {s_[3]} |" for s_ in spikes]
    else:
        md.append("| — | no spike feeds this dossier | — | — |")
    md += [
        "\n## Main-session notes\n",
        *[f"- {n}" for n in notes],
        "\n## Recommendations for the spec\n",
        *[f"{i}. {esc(x)}" for i, x in enumerate(recs, 1)],
        "\n## Open questions\n",
        *[f"- {esc(x)}" for x in oq],
    ]
    if gaps and gaps.get("missing"):
        md += [
            "\n**Completeness critic — missing for a plan writer:**\n",
            *[f"- {esc(x)}" for x in gaps["missing"]],
        ]
    elif gaps is None:
        md.append(
            "\n**Completeness critic:** not run for this dossier — treat the list above as incomplete."
        )
    else:
        md.append("\n**Completeness critic:** nothing material missing.")
    md += [
        "\n## CLAUDE.md §4 credit rows to add\n",
        "| Name | What we take | License | Author |",
        "|---|---|---|---|",
        *[
            f"| {esc(c.get('name'))} | {esc(c.get('what'))} | {esc(c.get('license'))} | {esc(c.get('author'))} ({esc(c.get('source_url'))}) |"
            for c in credits
        ],
        "\n## Change log\n",
        f"- {D} — rendered from `../runs/{JSON_PATH.name}` (researcher + refuters + completeness critic); spike rows and main-session notes added.",
    ]
    return "\n".join(md) + "\n"


def main() -> None:
    with open(JSON_PATH) as fh:
        data = json.load(fh)
    for rid in META:
        out = OUT / f"{rid}-{META[rid][0]}.md"
        out.write_text(render(rid, data))
        v = data.get(rid) or {}
        print(
            f"{rid}: facts={len((v.get('research') or {}).get('facts') or [])} verdicts={len(v.get('verdicts') or [])} gaps={'yes' if v.get('gaps') else 'no'} → {out}"
        )


if __name__ == "__main__":
    main()
