Verdict: ACCEPTED WITH MINORS

# Independent review (re-check) — P.4 P3 signature STOP and P5 timing capture (compute/20261128-19)

Re-reviewed the corrected deliverable `compute-p4-p5-timing-20261128` at
`05e627099080bcbeba9083e418bf9fc344b07d87`, from a clean worktree at that tip. The prior review at
`6a301af6` (of `dc725f89`) is superseded by this re-check. No blocking or major finding remains; the
deliverable is accepted. This review was read-only: no GPU job or host workload, no private key, and no
sealed label or test value was read.

The new tip adds 14 files under `docs/r1/reports/trackp_p4_p5_timing_20261128/`: the four `metrics.jsonl`, four
`run.log`, four `lease.txt`, the revised record and the revised `SHA256SUMS`. It touches nothing outside that
directory.

## Prior findings closed

| Prior finding | Re-check |
|---|---|
| **B1** eight ignored raw files missing; `SHA256SUMS` failed | **closed**: all eight are committed; clean-checkout `shasum -a 256 -c SHA256SUMS` is **43/43 OK** (exit 0) |
| **M1** paper pin generalised to all arms | **closed**: record now states 0.8B `91cfd48a…` and 4B `e92f3c73…` |
| **M2** single data hash `1d39f1ba…` | **closed**: all four per-arm `sft_data.json` hashes are listed (`0088f559…`, `9b6552b4…`, `1d39f1ba…`, `f997e7fa…`) |
| **m1** `kev-4b` median `5.4800` | **closed**: record table now says `5.4855`, matching the raw metrics and `timing_summary.json` |
| **m3** unsigned wording | **closed**: record now says no `gpgsig` and `git verify-commit` exits 1 because there is no signature |
| **m4** base `57e6d1ed` | **closed in value**: record now says `66aa4e10`; see minor m2 below for the parenthetical wording |

## Integrity and raw-file provenance

From a clean checkout of the tip, in the record directory:

```
$ shasum -a 256 -c SHA256SUMS
... all 43 lines OK ...
EXIT=0
```

The eight newly committed raw files are **not** content-edited. Their sha256 values are identical to the
eight `metrics.jsonl`/`run.log` lines in the previous `SHA256SUMS` at `dc725f89` and to the files on Ada:

| Arm | `metrics.jsonl` | `run.log` |
|---|---|---|
| `kev-0.8b` | `49942e87…` | `88e42b5c…` |
| `qwen3.5-0.8b-base` | `ad1f8442…` | `c9c438ea…` |
| `kev-4b` | `4e1c169f…` | `16a78ba6…` |
| `qwen3.5-4b-base` | `a459e37d…` | `bd3d0645…` |

The old 39-line sums plus the four new `lease.txt` entries give the new 43 lines. The record's own hash was
updated in the new `SHA256SUMS` and verifies.

`git diff --check 66aa4e10..05e62709` reports trailing whitespace in `kev-4b/run.log` and
`qwen3.5-4b-base/run.log`. Those are raw captured console lines; the bytes must **not** be cleaned, or the
hashes above break. This is expected, not a defect.

## Record content

- **Base:** `git merge-base origin/main 05e62709` = `66aa4e10b107d81d6abc305fb1fa16879ff737d7`; record states
  `66aa4e10`. (The new tip's immediate parent is `dc725f89`; see minor m2.)
- **Paper pins:** record now splits 0.8B `91cfd48a67f8d62d4e20826976cbdbdbcfcaf505` and 4B
  `e92f3c7389e06347a0ff78f5f68971024133c670`. These match the four manifests.
- **Data:** the four per-arm `sft_data.json` hashes in the record match the four `report.json` files and the
  accepted probe data.
- **Median:** `kev-4b` median is `5.4855`; all four median/mean/max values recompute from the now-committed
  `metrics.jsonl`.
- **P3 wording:** `git cat-file commit befb58c8` has no `gpgsig`; `git verify-commit befb58c8` exits 1 with no
  signature. The record's sentence matches this. The P3 STOP is still correctly flagged for the author; it is
  not claimed resolved.

The P5 numbers are otherwise unchanged and still reproduce: walls `120.242 / 117.882 / 488.017 / 437.816 s`,
total `0.3233 GPU-h`, all four kernel mappings fast, no `(torch path)` fallback, card 2
`GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154`, torch `2.6.0+cu124`, CUDA 12.4, transformers `5.19.0`, Python
`3.12.10`, freeze sha256 `50238e5a…` (121 lines).

## Lease files

The four `lease.txt` files use the same card/times as the captures: `gpu_index=2`, UUID
`GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154`, and start/finish times equal to `started_utc.txt`/`finished_utc.txt`.
`lock=/data1/zli538/r1_locks/gpu2.lock` follows from the reviewed Ada config (`lock_dir` plus card 2), and the
host `gpu2.lock` exists with mtime `2026-11-28T13:55:11Z`, the last arm's start. The `mode=flock-exclusive`
description matches the direct-launch design. The final clause, "outer shell held fd 9 on the lock for the
whole python process", is an assertion about the launch wrapper and is not derivable from the named raw files;
no launcher log is in the commit. This is documentation-only (minor m1), not a contradiction of the captured
lease facts.

## Overclaim check

Still passes. The record does not claim a new formal probe run; it leaves the accepted probe charge at
3.10 GPU-h and the 40 GPU-h threshold unchanged; it does not claim P3 is resolved; and it keeps
ENGINEERING_ONLY with synthetic labels only, no SFT evidence run, no label/test/evaluation read.

## Findings

- **Blocking:** none.
- **Major:** none.
- **Minor m1.** `lease.txt`'s "outer shell held fd 9" clause is not derived from the listed raw captures and
  has no launcher artifact in the commit. Cite the exact launcher command/log, or drop the fd/`outer shell`
  detail and keep the captured card/times/lock path. The lease conclusion itself is supported.
- **Minor m2.** The record says `66aa4e10` is "the branch parent"; it is the branch's merge base with `main`.
  The new tip's parent is `dc725f89`. Say "branch base" or "the main commit the branch is based on".
- **Minor m3.** "The Track P runner path is identical between them" is too broad: the SFT training path
  `r1/c3/train/run.py` is identical, but `r1/scripts/trackp.py` differs by the 4B gradient-checkpointing flag
  (not passed by the 0.8B arms). State that qualification; the result is unaffected.
- **Note, not a finding.** `git diff --check` flags trailing whitespace in two raw `run.log` files. Preserve
  the raw bytes; do not clean them.

## Verdict

**ACCEPTED WITH MINORS.** The prior blocking and major findings are closed: the capture is complete and
self-consistent, the raw files are byte-identical to the previously recorded and host hashes, the identity
paragraph is correct, and the P3 STOP wording is accurate. The remaining items are documentation precision, not
evidence defects.

## Commands used (representative)

```
git fetch origin refs/heads/compute-p4-p5-timing-20261128
git worktree add --detach <tmp> 05e627099080bcbeba9083e418bf9fc344b07d87
cd docs/r1/reports/trackp_p4_p5_timing_20261128 && shasum -a 256 -c SHA256SUMS
git show dc725f89:docs/r1/reports/trackp_p4_p5_timing_20261128/SHA256SUMS
git diff --check 66aa4e10..05e62709
git merge-base origin/main 05e62709
git cat-file commit befb58c8; git verify-commit befb58c8; echo $?
python3  # recompute median/mean/max from the four metrics.jsonl
```
