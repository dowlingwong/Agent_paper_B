# Track X Stage A — scoped review of the TASL-7 host-pin delta (v6)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-01 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7 access was read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`nvidia-smi`/`ps`); TASL-2 access was read-only (`/proc`, `/proc/locks`, `stat`, `sha256sum`).

**Verdict: `ACCEPT` of the v6 host-pin code/config delta, with the environment-completion conditions in §8.**
The delta is minimal and fail-closed: an explicit approved-host allowlist with `cfg['host'] == node`, the same
approved `/home/dowling/exam-x` root made an explicit constant, the preflight using the same gate, a real test,
and only the TASL-7 host/GPU/config pins. B1/B2 remain hard STOP; the B1/B2 campaign worker remains
TASL-2-only. TASL-7's identity, GPU, lock and code/harness pins verify; the environment replication
(binary/prompts/venv/HF) and the 22-model transfer are **still in progress** and are hard conditions before the
preflight/Stage A. The re-download provenance for the models is acceptable (content-addressed by the accepted
registry SHA, verified by the transfer and re-verified by `validate_spec`), subject to the conditions.

---

## 1. Frozen delta identity (verified)

| Item | Value |
|---|---|
| Snapshot | `/private/tmp/paper-b-stagea-cooperative-review-20261031-v6` |
| `SHA256SUMS` SHA-256 | `33f78b93fdbaf1c0520c82aa82b730de551ff43bede6639acb96beb6b9259ba2` — **verified**; 53/53 entries OK (51 `files/` + `tracked.patch` + `README.md`) |
| Base | published census-gap fix `0d9e4ed` + config binding `4722e10` |
| Delta vs v5 | exactly `r1/exam/runtime.py`, `r1/tests/stagea_lease_preflight.py`, `r1/tests/test_exam_core.py`, `r1/scripts/configs/exam_portal.json` |
| Everything else | v6 `files/` == live worktree (0 mismatches); live HEAD `4722e10` with the host-pin delta uncommitted; all non-delta accepted bytes are v5-identical |

Delta hashes (SHA-256):
```
67978bb9200dcc77dc42f9ec52cd13deb5656b2a043bef1b0758ec11a5da6a5c  files/r1/exam/runtime.py
3c3094e4f3d45b85de7ad89c6aafbe6306b9ae9caf8ff905df2450321740d60c  files/r1/scripts/configs/exam_portal.json
8f0ea74c8b317c87621c50373679d8cae142f50b038c1152eb3a339398d6dc41  files/r1/tests/stagea_lease_preflight.py
cf9551360340d4efbfe0797036ec8c218db64e1aa63b974a904e4c9a6fdd0af0  files/r1/tests/test_exam_core.py
```

## 2. Host-pin code/config assessment (minimal, fail-closed)

- `runtime.py`: `APPROVED_EXAM_HOSTS = frozenset({'TASL-2','TASL-7'})`; `EXAM_X_ROOT = Path('/home/dowling/exam-x')`; `host_check` now requires `node in APPROVED_EXAM_HOSTS and cfg['host'] == node` (Mac and any other node STOP; a config host that does not equal the node STOPs), then checks `models_dir`/`work_dir` against `EXAM_X_ROOT`. The dryrun branch is unchanged; the rest of `runtime.py` is v5-identical.
- `stagea_lease_preflight.py`: same `APPROVED_EXAM_HOSTS`/`cfg['host'] == node` gate; otherwise unchanged.
- `exam_portal.json`: `host: "TASL-7"`, `gpu_uuid: "GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1"`; all other pins unchanged (`harness_commit 897d83c8…`, `prompts_sha256 70872a77…`, `binary_sha256 b70f4882…`, build `620d222`, `cache_prompt:false`, `d3_policy`). `paper_commit` is still `0d9e4ed` (the current published base); it must be rebound to the new host-pin code commit (condition).
- `test_exam_core.py`: new `test_host_check_allows_the_two_approved_portals_and_pins_config_host` — accepted on a matching approved host (TASL-7), rejected on host mismatch (`cfg.host=TASL-2` on node TASL-7) and on the Mac. This is a genuine test (it exercises `host_check`, not just source text).
- **Fail-closed / B1/B2:** `ExamRunner.start` still raises for `b1`/`b2` (B1/B2 reviewed harness pin not implemented); `exam_runner.main` and `campaign.collect` still STOP B1/B2; the B1/B2 campaign worker keeps its own `platform.node().split('.')[0] != 'TASL-2'` check (`campaign.py:73`) and is not exercised by Stage A. The host allowlist does not enable B1/B2.
- Relevant Mac CPU subset on v6: **374 passed, 1 skipped** — matches the claim.

## 3. TASL-7 environment — what is verified now

Read-only, `ssh -o BatchMode=yes tasl7`; observed 2026-11-01T11:00–11:01Z (UTC):

| Check | Observed |
|---|---|
| Host / platform node | `TASL-7`; `platform.node()` = `'TASL-7'` → the allowlist/config pin passes |
| OS / kernel / CPU / RAM / disk | Ubuntu 22.04.5 LTS; `6.8.0-138-generic`; 24 cores; 62 GB RAM; `/home/dowling` 897 GB free |
| Kernel hardening | Yama `ptrace_scope = 1` (same mode as TASL-2; patch level differs 6.8.0-138 vs -136) |
| GPU | `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, RTX 4090, 24564 MiB, compute cap 8.9, driver 580.178.04 — matches the config |
| Lock | `/home/dowling/r1_locks/gpu0.lock` exists, dev 66306, inode 56251186, nlink 1, size 0; `/proc/locks` has no line for it (free); no experiment processes |
| Code clone | `/home/dowling/exam-x/work/agent_paper_B` HEAD `4722e10d77cd…`, clean (published base) |
| Harness | `/home/dowling/exam-x/work/autoresearch_harness` HEAD `897d83c8ef…`, clean |

**Still in progress / NOT yet verifiable at freeze** (the tar extraction and model transfer are running):
- `~/exam-x/work/llama.cpp/build-exam/bin/llama-server` — not yet present (must be SHA `b70f4882…` when complete).
- `~/exam-x/frozen_inputs/trackx_stagea_promptset_20261031/prompts.jsonl` — not yet present (must be SHA `70872a77…`).
- `~/exam-x/work/venv/bin/python` — currently a 0-byte in-extraction file (permission-denied); the copied uv Python target exists but the venv is not usable yet. Venv imports (numpy/scipy/transformers/yaml/jinja2/tokenizers) are not yet verifiable.
- `~/exam-x/work/hf` tokenizer/template cache — not yet present.
- 22 model GGUFs — 0 `.verified`, 0 `.failed` at freeze; three small files are being written; the transfer is ~18 min into an expected ~8–9 h.
- `tar -C /home/dowling -xf -` (pid 2093779) and `python3 model_transfer.py` (pid 2092911) are still running. The tar may also overwrite `~/exam-x/work/agent_paper_B` / `autoresearch_harness`; the code/harness pins must be re-verified after the tar completes.

## 4. TASL-7 model re-download provenance — acceptable (with conditions)

- The transfer manifest `~/exam-x/work/r1_stagea_transfer_manifest.json` has **22 entries**; for all 22 the
  `size`, `sha256` and URL match the accepted registry `quant_source` exactly (checked programmatically against
  `r1/exam/registry.yaml` at `4722e10`: **22/22 match, 0 mismatches**), and all 22 URLs are
  `https://huggingface.co/<repo>/resolve/<40-hex revision>/<file>` — the pinned repo@commit, not a moving
  branch/tag.
- `model_transfer.py` downloads from those URLs (3 workers, HTTP Range resume), verifies the file size and then
  the SHA-256, unlinks on a SHA mismatch, writes a `.verified` marker only after the SHA match, logs to
  `transfer.log`/`transfer_status.json`, and records `.failed` after 3 attempts. The runtime
  `validate_spec` **re-verifies** the model SHA (`digest_file(model) == spec['quant_source']['sha256']`) at
  Stage A server start, so the actual bytes used by the run are SHA-bound to the accepted registry pin
  regardless of the transfer tool's marker caching.
- **Assessment:** re-downloading the GGUF bytes from the pinned HF `repo@revision` sources with size+SHA-256
  verification is **acceptable provenance** for the model content: the accepted registry pins the exact
  repo/commit/file/size/SHA, the downloaded bytes are content-addressed by that SHA, and the runtime re-checks
  it. It is not a weaker provenance than a copy, provided the conditions below hold.
- Conditions: the transfer completes with **22/22 `.verified` and no `.failed`**; the transfer manifest remains
  the accepted registry pins (22/22 checked here); `validate_spec` re-verifies each model SHA at the run;
  retain `transfer.log`/`transfer_status.json` with the run evidence. A final re-SHA pass is recommended (the
  `.verified` cached path trusts the marker; the runtime SHA is the real safeguard).

## 5. TASL-2 state (verified untouched)

- No `llama-server`/`exam_runner`/`trackx_lease`/guardian processes on TASL-2; the STOP-1 pids 2576846/2611135
  and STOP-2 pids 2920661/3005245 are all absent; `/proc/locks` has no line for the lock inode 120090387.
- STOP-1 evidence unchanged (`STOP.json 2d38fece…`, `batch_state.json aa2e953b…`); STOP-2 evidence unchanged
  (`STOP.json d1eddb9f…`, `batch_state.json b27373ce…`); the stopped namespace fixture unchanged
  (`mtime = ctime = 1793446875`, mode 700); `gpu0.lock` unchanged (dev 66306, inode 120090387, nlink 1, size 0).
- No new Stage A attempt after STOP-2 on TASL-2 (the only new dirs are the STOP-2 run/preflight/lease dirs).
  Neither stopped batch is resumed, reused or counted as evidence.

## 6. Host-move consequences to record

- **B1/B2 remain hard STOP everywhere.** The host allowlist does not enable B1/B2; the B1/B2 campaign worker
  still refuses any non-TASL-2 node (`campaign.py:73`). If the author ever wants B1/B2 on TASL-7, that is a
  separate authorization/review of the B1/B2 host gate (and the B1/B2 harness pin), not covered by this delta.
- **New environment, new evidence.** The accepted TASL-2 preflight/STOP evidence is TASL-2-specific and is not
  reused. TASL-7 needs its own real-lock preflight (route (i) `log_line`, no fallback, FD/OFD chain, zero
  generation, validated release, M3 environment recorded) and its own separately identified Stage A attempt;
  that evidence belongs to a new receiving review.
- **Host/kernel difference.** TASL-7 is kernel `6.8.0-138` (Yama 1) vs TASL-2 `6.8.0-136` (Yama 1); the
  descendant→ancestor kcmp permissiveness noted earlier is host/kernel dependent and is **not** relied on by
  the code; the TASL-7 preflight must re-verify the ancestor→descendant kcmp/FD/OFD chain on the real host.
- **Interpreter/env.** The copied venv/uv Python and the copied `build-exam` binary must run on TASL-7's
  driver/CUDA; the preflight (real binary, real lock) is the check. M3 (interpreter/venv/dependency versions)
  must be recorded on TASL-7 as on TASL-2.
- **Paper pin.** The v6 config's `paper_commit` is `0d9e4ed`, not the new host-pin code commit; it must be
  rebound so the launcher's ancestor + runtime-path no-diff rule passes (the host-pin change is in
  `r1/exam/runtime.py`, a runtime-checked path, so the binding must name the new code commit, with a separate
  config-binding commit changing only `paper_commit`).
- **Record the author's TASL-7 decision** and the new Stage A attempt in the coordinator docs (PLAN/STATUS), as
  was done for the earlier decisions; the TASL-2 records stay as historical evidence.

## 7. Conditions (hard gates before the preflight/Stage A)

1. **Complete the environment copy:** the tar finishes; verify `build-exam/bin/llama-server` SHA
   `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`, prompts SHA
   `70872a7702a36dc13b5612abd7a8580414f01c43bb8e19179942ca70a2ed510a`, the venv Python 3.13.4 imports
   (numpy/scipy/transformers/yaml/jinja2/tokenizers), the HF tokenizer/template cache; re-verify the code clone
   at the new host-pin commit and the harness at `897d83c8…`, clean (the tar may overwrite them); record all
   hashes.
2. **Complete the model transfer:** 22/22 `.verified`, no `.failed`; the transfer manifest remains the accepted
   registry pins (22/22 matched here); `validate_spec` re-verifies each SHA; retain `transfer.log`/
   `transfer_status.json` with the run evidence.
3. **Commit/bind:** commit the v6 delta (runtime/preflight/config/test) as the new code commit; rebind
   `paper_commit` to it in a separate config commit; verify the only config change is `paper_commit`, the
   launcher's ancestor+no-diff over the runtime-checked paths is empty, the run checkout is clean, and the
   guardian manifest pins the accepted bytes (M1/M2 carry over; M3 on TASL-7).
4. **Fresh TASL-7 preflight** under the reviewed guardian with the real lock: route (i) `log_line`, no
   fallback, FD/OFD chain (guardian→runner, runner→server kcmp rc 0, FD dev/ino/exact set), zero generation,
   validated release, M3 environment recorded, manifest pins; only then the new, separately identified Stage A.
5. Keep the TASL-2 STOP evidence untouched; do not resume/reuse either stopped batch; B1/B2 remain STOP.

## 8. NOT CHECKABLE in this scoped review

- The TASL-7 binary/prompts/venv/HF artifacts and the 22 model files at freeze (copy/transfer still running).
- The TASL-7 preflight/Stage A behaviour and evidence (not run); TASL-7 binary/CUDA compatibility with the
  copied build (preflight will establish).
- The exact TASL-7 environment hashes until the tar and model transfers complete.
- The future host-pin code commit/config binding and manifest (M1).
- Same-UID non-interference, host-global single-server (carry over); B1/B2 on TASL-7 (not authorized; hard
  STOP; the campaign worker is TASL-2-only).
- Real Stage A request/cache evidence (not yet produced on TASL-7).

## 9. Final verdict

**`ACCEPT`** of the frozen v6 host-pin code/config delta (with the §7 conditions). The delta is minimal and
fail-closed: approved-host allowlist + `cfg.host == node`, explicit `EXAM_X_ROOT`, the preflight using the same
gate, a real test, and only the TASL-7 host/GPU pins; B1/B2 remain hard STOP and the B1/B2 worker stays
TASL-2-only. TASL-7's identity, GPU, lock and code/harness pins verify; the model re-download provenance is
acceptable (22/22 manifest entries match the accepted registry size/SHA/repo@40-hex-revision, SHA-verified by
the transfer and re-verified at runtime). The environment copy and the 22-model verification are still in
progress and are **hard conditions** before the TASL-7 preflight and the new, separately identified Stage A;
the TASL-2 STOP evidence is untouched and neither stopped batch is reused.
