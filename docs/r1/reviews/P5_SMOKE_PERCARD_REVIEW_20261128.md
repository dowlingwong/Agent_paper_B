# Independent review — P5 staged Track P smoke on the per-card lease (compute/20261127-33 item 2)

Verdict: ACCEPTED

Reviewed deliverable tip `1e8b4aecf31ee4f240e697dc6b3e8f355e78bfd4` on
`compute-p5-smoke-percard-20261128`, whose parent is exactly `origin/main`
`d25938ed46953bd0ecd2d467aebd94a862e657dc`. The branch is one commit and adds only the eight files under
`docs/r1/reports/trackp_p5_smoke_percard_20261128/`; no code, config, plan, tolerance or model file is touched.
This review was read-only; no host workload was run or touched. `origin/main` advanced to `c11ce78b` while the
review was in progress, merging the accepted E0 review (`d9ccf79a`) and then this deliverable; the reviewed tip
`1e8b4aec` is unchanged.

## Numbers recomputed from the captures

Loaded `smoke_report.json` and recomputed every pass against the script's own rule (`tol = max(2 ×
calibration_vs_ref, 1e-3)`; bf16 matmul pass if rel err < 1e-2; argmax agreement ≥ 0.99):

| Check | Capture value | Criterion / derivation | Record | Match |
|---|---|---|---|---:|---|
| `pass` | `true` | all three checks pass | true | yes |
| Device / capability | `NVIDIA RTX 6000 Ada Generation`, `[8, 9]` | — | same | yes |
| bf16 matmul rel err | 0.002875031204894185 | < 1e-2 | 0.002875 | yes |
| fp32 tolerance | 0.04025459289550781 | 2 × 0.020127296447753906 | 0.04025 | yes |
| fp32 `fast_vs_ref` | 0.02801513671875 | ≤ 0.04025459289550781 | 0.02802 | yes |
| fp32 argmax agreement | 1.0 | ≥ 0.99 | 1.0 | yes |
| bf16 tolerance | 0.6332693099975586 | 2 × 0.3166346549987793 | 0.63327 | yes |
| bf16 `fast_vs_ref` | 0.271634578704834 | ≤ 0.6332693099975586 | 0.27163 | yes |
| bf16 argmax agreement | 0.995110034942627 | ≥ 0.99 | 0.99511 | yes |
| Peak allocated | 3,345.16748046875 MiB (fp32 check; bf16 2,095.94) | — | 3,345 MiB | yes |
| Kernels bound | `causal_conv1d_fn`/`causal_conv1d_update` (`causal_conv1d.causal_conv1d_interface`), `torch_chunk_gated_delta_rule` (`fla.ops.gated_delta_rule.chunk`), `torch_recurrent_gated_delta_rule` (`fla.ops.gated_delta_rule.fused_recurrent`) | none reports the "(torch path)" fallback | all four fast | yes |

`seq_len` 409, torch `2.6.0+cu124`, transformers `5.19.0`, CUDA runtime 12.4, fla `0.5.2`, causal_conv1d `1.7.0`
all match the record's host paragraph. Every rounded number in the record is a correct truncation/rounding of
the captured value.

## Per-card lease and card identity

Parsed `smoke_lease.jsonl` (2 events) and confirmed the report's `lease` array equals it element for element:

- Start 12:15:18Z, end 12:15:44Z = **26 s**, same PID 125535 in both events.
- `gpu_index` **2** and `gpu_uuid` `GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154` in both; this is exactly the
  card named by line 2 of `gpu_before.txt`/`gpu_after.txt` and by `--gpu` in `smoke_command.txt`.
- `other_processes` `{count: 0, memory_mib: 0}` at both start and end; `trackx_marker` absent at
  `/home/zli538/r1_locks/trackx_evidence.active`, matching the code default `Path.home()/r1_locks`.

The events carry `gpu_index`/`gpu_uuid`, fields only the per-card contract emits, so the capture itself shows the
new code path ran. Paper `c80f83bc` also contains merge `1f1b5d41` (per-card lease, reviewed ACCEPTED at
`fc95186b`), and its `r1/c3/train/run.py` and `r1/scripts/trackp_gpu_smoke.py` are byte-identical to this tip
(sha256 `51170b0c…` and `ab04bc8e…`). With `--gpu <full UUID> --lock /data1/zli538/r1_locks/gpu0.lock`, the lease
resolves `lock_path.with_name(f"gpu{index}.lock")` to **gpu2.lock**, which is precisely the reviewed handoff
("the smoke handoff must pass `--lock /data1/zli538/r1_locks/gpu0.lock` so both commands resolve the same
per-index lock"). CUDA is bound to the UUID and `_check_cuda_card` re-verifies that the process sees exactly that
UUID before any model or kernel work.

`gpu_before.txt` and `gpu_after.txt` both show card 2 at 5 MiB used / 48,427 MiB free with no foreign
compute-process line; unleased cards 0, 1 and 3–5 are unchanged, and 6–7 moved (other users, not leased). The
5 MiB is a non-compute/display context: the lease counts compute applications only, and the record's "(0 foreign
compute processes, 0 MiB)" is accurate in that sense.

## Pins

- **Paper** `c80f83bc`: the command runs in `/data1/zli538/paperb_p4_20261127/p5_20261127_b/paper_c80f83bc`, and
  the accepted fresh E0 unit for that same path records paper `c80f83bc5bc93356dfacadbcb5b186dfb59d028f`, clean,
  at 10:13–12:03Z on this host (`c22ba021`, Ada `e0e1/e0e2` manifests). The smoke started 12 min later.
- **Config** `trackp_ada_v1.json` sha256 `bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908`:
  matches `r1/scripts/configs/trackp_ada_v1.json` at this tip and at `c80f83bc`. It is an environment pin only —
  `trackp_gpu_smoke.py` never opens it; the command sets `--model`/`--lock` explicitly and the values agree with
  the config (`models/qwen3.5-0.8b-base`, `gpu0.lock` template).
- **Harness** `897d83c8`: the record states no harness pin. The command sets
  `AR_HARNESS_ROOT=/data1/zli538/paperb_p4_20261127/p5_20261127_b/harness` (not the `/data1/zli538/paperb_p4_20261127/harness`
  that the accepted E0 manifests bind), and the smoke imports only the paper tree; `r1.harness.harness_root()` is
  imported but never called. Harness bytes therefore cannot change this result.
- **Model**: cited as `models/qwen3.5-0.8b-base` "the reviewed P5 model". This run captures no model hash; the
  earlier P5 record bound config `b90b86f3…` and weights `c2b1e5a1…`.

## Capture integrity

From a clean checkout of the tip, `shasum -a 256 -c SHA256SUMS` in the record directory is **7/7 `OK`**. The
directory has 8 tracked files (`git ls-files`), the only unlisted one being `SHA256SUMS` itself; `git status`
including ignored files is empty. The recorded report hash `dd0944fa…` and lease hash `9d5cd323…` match the
files. `smoke.log`'s embedded JSON is byte-identical to `smoke_report.json` plus the trailing newline `print`
adds, so the log corroborates rather than independently duplicates the report.

## Honesty of the E0 and timing statements

The record does not claim to re-run E0 and says so explicitly. It cites `compute/20261128-16`, accepted at
`c22ba021` with review `0bd80f7a` (I checked that review file: `Verdict: ACCEPTED`, PASS on both slope and RPS
parts). It labels the earlier 25.9 %-RPS miss as superseded rather than reinterpreting it. The timing paragraph
cites the fresh E0 GPU-hours (0.9211/0.9142 Ada, 0.4747/0.4836 TASL-7, which match that record's table) and says
the reviewed timing carry-forward remains the next P.4 step; it makes no timing change. This satisfies the
honesty requirement for item 2.

## Findings

- **B (blocking):** none.
- **M (major):** none. The smoke evidence, the four kernel bindings, the per-card lease events, the card identity,
  the 26 s window and the capture integrity all reproduce.
- **m (minor, non-blocking; documentation only unless stated):**
  1. **Harness pin absent.** The record never states `897d83c8`, and the command's `AR_HARNESS_ROOT` names a
     different directory from the accepted E0 unit's harness path. The smoke does not use the harness, so this
     does not affect the result, but the companion compute report attributes `897d83c8` to this unit without
     support in this record. One line in the record (pin plus path) would close it.
  2. **Paper/model provenance is indirect.** No git or model hash is captured for this run; paper `c80f83bc` is
     established by the command path plus the accepted E0 manifests for the same path, and the model by path
     only. Stating the earlier record's config/weights hashes, or capturing `git rev-parse HEAD` and the model
     hashes beside the report, would make the pin self-contained.
  3. **"Empty card" wording.** `gpu_before/after` show 5 MiB resident on card 2 (non-compute); the lease's 0 MiB
     is foreign-*process* memory. The prior records handled this the same way, but saying "0 foreign compute
     processes, 5 MiB resident context" would be exact.
  4. **"Exact command" and the config.** `smoke_command.txt` uses `<capture>` placeholders, and the cited config is
     not read by the smoke script. Both are harmless; "the command, with the capture directory placeholder" and
     "environment pin" would be precise.
  5. **Merge ordering (resolved during review).** At the reviewed base `d25938ed`, `c22ba021`/`0bd80f7a` were
     accepted but not yet ancestors of `origin/main`; `origin/main` then advanced to `c11ce78b`, merging the E0
     review (`d9ccf79a`) and then this deliverable, so the citation now resolves from `main`. No action remains.
  6. **`pass` does not gate on kernel binding.** The script records `kernels_bound` but its `pass` covers only the
     three numeric checks. The record's "four fast kernels bound" claim is true from the captured module strings
     (none is the torch fallback), but it rests on those strings, not on the pass flag.

No blocking or major finding. The record's verdict — the staged Track P smoke passes on Ada card 2 under the
per-card lease, with the E0 part carried by the accepted fresh unit and the timing disposition still open — is
correct and honestly scoped.

Verdict: ACCEPTED
