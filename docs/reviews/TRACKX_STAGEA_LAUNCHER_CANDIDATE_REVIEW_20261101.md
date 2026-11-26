# Track X Stage A — scoped review of the launcher `--candidate` delta (v7)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-01 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7/TASL-2 access was read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`ps`); local test runs as before.

**Verdict: `ACCEPT` of the v7 launcher `--candidate` delta, with the conditions in §6.** The delta is a
pre-manifest model-size-check narrowing for the one-model preflight only; it is fail-closed on unknown ids and
defaults to all model files; it does not weaken the Stage A manifest gate (the runtime re-verifies every
loaded model's size/SHA, the manifest still pins launcher/config/prompts/registry/code, and Stage A runs
without `--candidate`). The preflight model `qwen25_coder_7b` is verified on TASL-7, so the preflight manifest
can now be built; the other 19 models are still transferring and remain a hard Stage A condition.

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v7` |
| `SHA256SUMS` SHA-256 | `871375e22f58ab7c169e4a3757f6861af6e71f18f6bc5054d94ae4cc2c4302e1` — **verified**; 53/53 entries OK (51 `files/` + `tracked.patch` + `README.md`) |
| Base | published TASL-7 host-pin `4768393` + config binding `d636267` |
| Delta vs v6 | `r1/scripts/trackx_stagea_launch.py`, `r1/tests/test_trackx_stagea_launch.py` (the config difference vs v6 is the already-published TASL-7 binding, `paper_commit=4768393`) |
| Everything else | v7 `files/` == live worktree (0 mismatches); live HEAD `d636267` with the launcher/test delta uncommitted; all other accepted v6 bytes unchanged |

Delta hashes (SHA-256):
```
74f67d2cd309cd17c73011192d78ce58ca80fec59036154d6f471ea3b8d069e3  files/r1/scripts/trackx_stagea_launch.py
d8b3b065aa427e6c9fb0ac3a34e23a4af9ee2b5213007ed85377b0077c79a049  files/r1/tests/test_trackx_stagea_launch.py
fba8e4e667aefb1c6aadab4c4af155f38c759964d6d124f6a9e40923aa506c90  files/r1/scripts/configs/exam_portal.json
```

## 2. Launcher delta assessment (minimal, fail-closed)

- `--candidate <id>` (repeatable). The launcher now reads the registry once and builds
  `models = data['candidates'] + data.get('sensitivities', [])`; if `args.candidate` is non-empty it rejects
  unknown ids (`STOP: unknown --candidate ids: …`), filters to the selected specs, rejects an empty filtered
  set, and then runs the existing on-disk size check on those specs only. Without `--candidate` the default is
  **all** model specs. The flag is a launcher-only argument; it is not written into the guardian manifest.
- **Registry membership (verified against the real `r1/exam/registry.yaml`):** `models` = 22 specs —
  the 21 `candidates` (the 20 expected candidates plus `qwen25_coder_7b`, which is a candidate row with
  `role: anchor`) plus the one `sensitivities` model (`olmo31_32b_think`). The `software_anchors`
  (`random_valid`, `scripted`) are model-less and correctly excluded. So:
  `--candidate qwen25_coder_7b` is **known** and selects exactly that spec; `--candidate nope` is unknown and
  STOPs; no `--candidate` yields all 22. (Verified by importing `read_registry` and evaluating the exact
  expressions; the preflight model is not an "unknown" despite being an anchor, because it lives in
  `candidates`.)
- **No manifest-gate weakening.** The manifest `files` list still pins all `r1/**/*.py`, `r1/**/*.yaml`
  (registry), the config, the prompts, the guardian and the lock; the launcher/config/argv are unchanged by
  `--candidate`. The runtime `validate_spec` re-checks the selected/loaded model's `size_bytes` and SHA-256,
  and `llama_server_instance` re-verifies the GGUF digest; Stage A runs without `--candidate` (all 22 model
  files checked before the manifest) and each candidate's server start re-verifies its model. The launcher's
  size check is a pre-launch convenience/guard, not the security gate; the `--candidate` narrowing only
  applies to the one-model preflight, whose model is also checked by the preflight fixture
  (`size_bytes`) and by the runtime SHA. No path accepts a model without a SHA check.
- **Minor observations (non-blocking):** the `if not models` branch is effectively unreachable — `argparse`
  requires a value for `--candidate`, an empty value is an unknown id → STOP, and no `--candidate` means the
  default all; the branch is harmless. The new test
  `test_candidate_filter_is_parsed_and_validated` is **source-text only** (it greps for the parser line, the
  unknown-id message and `if args.candidate:`); it does not exercise the behaviour. I verified the behaviour
  against the real registry above; a behaviour test (unknown id STOP, selection narrows to the named model,
  default all) would be stronger.
- Relevant Mac CPU subset on v7: **375 passed, 1 skipped** — matches the claim.

## 3. TASL-7 environment — spot-checked read-only (observed 2026-11-01T11:23Z)

| Check | Observed |
|---|---|
| Binary | `build-exam/bin/llama-server` SHA-256 `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b` — **matches the accepted pin** |
| Frozen prompts | `prompts.jsonl` SHA-256 `70872a7702a36dc13b5612abd7a8580414f01c43bb8e19179942ca70a2ed510a` — **matches** |
| venv | `work/venv/bin/python` → uv Python 3.13.4; `sys.executable` = venv path; imports OK: numpy 2.4.4, PyYAML 6.0.3, transformers 5.20.2, tokenizers 0.23.3, jinja2 3.1.6, scipy 1.17.1 |
| HF cache | `work/hf` = 381 MB (hub cache present) |
| Code / harness | code clone `d636267…` clean; harness `897d83c8ef…` clean |
| Lock | `~/r1_locks/gpu0.lock` dev 66306, inode 56251186, nlink 1, size 0; `/proc/locks` has no line for it (free) |
| Models | **3/22 verified**, 0 failed: `qwen25_coder_7b`, `ornith10_9b`, `qwen35_9b`; transfer ongoing (18.1 GB / 343.9 GB; 6 `.gguf` files present, 27 GB); `transfer.log`/`transfer_status.json` present |

The preflight's model (`qwen25_coder_7b`) is verified; the preflight manifest can now be built with
`--candidate qwen25_coder_7b`. The other 19 models are still downloading with per-file size+SHA verification;
Stage A must wait for 22/22 `.verified` and no `.failed`.

## 4. TASL-2 state (re-verified untouched)

No `llama-server`/`exam_runner`/`trackx_lease` processes; STOP-1 pids 2576846/2611135 and STOP-2 pids
2920661/3005245 absent; `/proc/locks` free for inode 120090387; `gpu0.lock` unchanged (dev 66306, inode
120090387, nlink 1, size 0); STOP-1/STOP-2 `STOP.json` hashes unchanged (`2d38fece…`, `d1eddb9f…`);
stopped namespace fixture unchanged (`mtime = ctime = 1793446875`, mode 700). Neither stopped batch is
resumed or reused.

## 5. Host/environment context (from the accepted v6 review; unchanged by v7)

TASL-7 is `TASL-7` (Ubuntu 22.04.5, kernel 6.8.0-138, 24 cores, 62 GB RAM, 897 GB free), GPU
`GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` (RTX 4090 24564 MiB, compute cap 8.9, driver 580.178.04), Yama
ptrace_scope=1. B1/B2 remain hard STOP; the B1/B2 campaign worker is TASL-2-only; TASL-7 is a new environment
requiring its own preflight/Stage A evidence (TASL-2 evidence not reused); the paper pin and M1/M2/M3 apply.

## 6. Conditions

1. **Commit/bind:** commit the v7 launcher/test delta as the new code commit; rebind `paper_commit` (or rely on
   the launcher's ancestor rule — the launcher is not in the runtime no-diff list, but the printed manifest
   must pin the accepted launcher hash); verify the run checkout is clean and the manifest pins the
   launcher/config/prompts/registry/code (M1/M2 carry over; M3 on TASL-7).
2. **Preflight:** run the TASL-7 real-lock preflight with the launcher's `--candidate qwen25_coder_7b`
   **and** the preflight's own `--candidate qwen25_coder_7b` via `--runner-arg`; verify route (i) `log_line`,
   no fallback, FD/OFD chain (guardian→runner, runner→server kcmp rc 0, FD dev/ino/exact set), zero
   generation, validated release, M1/M2/M3 recorded, manifest pins.
3. **Stage A:** only after 22/22 models are `.verified` with no `.failed`; run the new, separately identified
   Stage A **without** `--candidate` (all 22 model files size-checked before the manifest), under the
   reviewed guardian, with each loaded model's SHA-256 re-verified by `validate_spec`; keep the TASL-2 STOP
   evidence untouched and do not resume/reuse either stopped batch; B1/B2 remain STOP.
4. **Optional:** add a behaviour test for the `--candidate` filter (unknown id STOP, selection narrows to the
   named model, default all 22) instead of the current source-text test.

## 7. NOT CHECKABLE in this scoped review

- The launcher's full `main` behaviour on TASL-7 (the preflight run will exercise it; the filter logic and
  registry membership were verified here).
- The remaining 19 model transfers and the 22/22 verification (in progress).
- The TASL-7 preflight/Stage A behaviour and evidence (not run).
- The future commit/binding/manifest bytes (M1).
- Same-UID non-interference, host-global single-server (carry over); B1/B2 on TASL-7 (not authorized; STOP).

## 8. Final verdict

**`ACCEPT`** of the frozen v7 launcher `--candidate` delta, with the §6 conditions. The flag is a narrow,
fail-closed pre-manifest size-check filter (unknown ids STOP, default all model files, one-model preflight
only); the preflight model `qwen25_coder_7b` is a known registry candidate and is verified on TASL-7, so the
preflight manifest can be built; the runtime re-verifies every loaded model's size/SHA and the manifest still
pins the launcher/config/prompts/registry/code, so the Stage A gate is not weakened. The remaining 19 model
transfers and the TASL-7 preflight/Stage A remain the gating conditions.
