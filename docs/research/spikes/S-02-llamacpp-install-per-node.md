# S-02 — llamacpp-install-per-node

- **Goal:** Which install path gives each build node a working `rpc-server`, `llama-server`, `llama-bench` at a pinned tag (release binary / Docker image / source build), which backend (CPU / CUDA + version), and the `rpc-server` flags at that version.
- **Node(s):** ahnoway, solarplexus, optiplex
- **Executor:** main-session (founder for any package install)
- **Dependencies:** none for branch 1 (done); R03 confirms the asset matrix
- **Preconditions:** disk ≥ 5 GB free in `~/corvid-s02` on each node · AC on ahnoway · no other spike on the node · Tailscale modes: ahnoway kernel, solarplexus userspace (until Phase 0 step 2), optiplex kernel
- **Cap (Appendix B):** builds wrapped `CPUQuota=120%`/`40%`/`120%`, `MemoryMax=1.6G`/`1.6G`/`3.2G`, `nice -n 19`; downloads unthrottled but sequential · no GPU during build
- **Exception record:** none
- **Time box:** 60 min per node
- **Expected signal:** `rpc-server --help` prints flags; `llama-bench` runs on a tiny model (S-03 follows)
- **Abort criteria / watch:** node load > 2× cores; disk < 2 GB free

## Commands (exact; every heavy command wrapped)

```bash
# 0) facts
nvidia-smi --query-gpu=name,driver_version,compute_cap --format=csv,noheader; for t in cmake nvcc gcc g++ git unzip; do printf '%s: ' $t; command -v $t || echo none; done
# 1) release binary (tag pinned from the GitHub API 'latest' at run time; asset names recorded on this card)
TAG=<tag>; mkdir -p ~/corvid-s02 && cd ~/corvid-s02 && curl -sL -o llama.zip "https://github.com/ggml-org/llama.cpp/releases/download/$TAG/<linux-asset>" && unzip -l llama.zip | grep -E 'rpc-server|llama-server|llama-bench'
# 2) docker (solarplexus only: NVIDIA container toolkit present): docker run --rm ghcr.io/ggml-org/llama.cpp:<tag> ls /app | grep rpc-server   (R03 says which image tags exist)
# 3) source build (needs cmake; CUDA needs nvcc matching the driver)
git clone --depth 1 --branch "$TAG" https://github.com/ggml-org/llama.cpp ~/corvid-s02/llama.cpp && cd ~/corvid-s02/llama.cpp
systemd-run --user --scope -p CPUQuota=<B> -p MemoryMax=<B> nice -n 19 bash -c 'cmake -B build -DGGML_RPC=ON && cmake --build build --config Release -j2 --target rpc-server llama-server llama-bench'
# CUDA: add -DGGML_CUDA=ON [-DCMAKE_CUDA_ARCHITECTURES=52 on the GTX 970]
./build/bin/rpc-server --help | head -30
```

## Undo (executed and confirmed at the end)

```bash
rm -f ~/corvid-s02/llama.zip ~/corvid-s02/latest.json; rm -rf ~/corvid-s02/llama.cpp/build/CMakeFiles   # binaries stay for S-03/S-04; removed after S-04
```

## Result

- **Branch 1 (prebuilt Vulkan tarball) works on all three nodes** — tag `b10581` (`0.2.0-dev`, commit `2115b73d8`, built 2026-08-22); Linux releases ship CPU + Vulkan builds (no Linux CUDA prebuilt); binaries include `ggml-rpc-server` (renamed), `llama-server`, `llama-bench`; every node's NVIDIA GPU is detected as `Vulkan0` (2070S 7577 MiB free · GTX 970 4247 MiB free · 3050 5568 MiB free); iGPUs appear as `Vulkan1` (exclude with `-d Vulkan0`). **`ggml-rpc-server` has no `--mem` flag at this version** (flags: `-t -d -H -p -c`) → VRAM caps via host-side split/layers. Full table: `docs/runs/S-02-2026-08-22.md`.
- Raw evidence: `docs/runs/S-02-2026-08-22.md` · `docs/runs/raw/`

## Follow-ups

- R03: release asset matrix for Linux; whether `rpc-server` ships prebuilt; CUDA toolkit/driver constraints per node.
