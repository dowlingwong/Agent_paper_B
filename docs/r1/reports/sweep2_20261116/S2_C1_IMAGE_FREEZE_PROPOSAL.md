# S2-C1 — image freeze proposal for sweep 2 (cluster agent, 16 November 2026)

**Status: proposal for the author's authorization (P7). Nothing is switched.**

## Proposal

Freeze **one** GPU image digest for the whole sweep-2 table:

```
ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296
```

(the v1 gpu image, tag `20261114-74820315`; SIF `5,226,487,808 B`, SIF SHA-256 `f88382fd…`; verified by I3 on
NEMO2 L40S and TOpAS V100S, and by I4/S5: llama-server `620d2225…`, binary SHA-256 `f8d35fd3…`, build
`2026-11-14T23:10:24Z`). The CPU image for audits, if needed, is the matching v1
`ghcr.io/dowlingwong/r1-htc-cpu@sha256:221ca459d62723ec58219c37c71e1664846b135ff919ec59cf37ce57158f75aa`.

## Why v1 and not v2

- v1 is the digest with **end-to-end evidence** (I2/I3/S4/S5) and the one the B2 sweep/replay settings were pinned
  against; one image digest per table is required, so a mid-sweep v2 switch is not allowed.
- v2 is still being built (the gpu target currently fails at the `nvidia-smi` provisioning; a sidecar fix is in
  CI); it has no I2/I3-on-v2 evidence yet and the author has not approved a digest switch.
- The sweep-2 jobs need GPU compute + llama-server + the harness/tracks envs, which v1 provides; they do not need
  v2's env3/Track P freeze or `nvidia-smi` (the wrapper records the GPU/CPU/driver identity through torch and
  `/proc`, not through `nvidia-smi`).

## What the freeze binds (to be written into the authorization by S2-M1)

- the digest above (and the matching cpu digest for CPU-only audits, if used);
- `llama_server_sha256 = f8d35fd33e866808bc76457cf52cf1f8b1baafde9c2c8eebae51abf428843cc0`,
  `llama.cpp commit 620d2225…`, image `build_utc = 2026-11-14T23:10:24Z`;
- **every** sweep-2 job manifest records the digest, the image identity markers, and refuses a different image;
- the W2/C2 wrapper verifies the image identity from `/opt/r1/VERSIONS.txt` + the llama-server binary hash before
  any model/server start.

## If the author prefers v2

Then v2 must first pass: build (gpu target), I2/I3 on v2 (NEMO2 L40S + TOpAS), `trackp_gpu_smoke`/E0 only if
Track P data is involved, and the author's digest approval; after that S2-C1 is amended to the v2 digest **before**
any sweep-2 job is submitted, and one digest stays for the whole sweep. No mixed-digest table.
