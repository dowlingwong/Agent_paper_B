Verdict: CHANGES REQUIRED

# Independent review — P.4 P3 signature STOP and P5 timing capture (compute/20261128-19)

Reviewed deliverable `compute-p4-p5-timing-20261128` at
`dc725f894fb342f4062f815999e849a522953661` from a clean worktree at that tip. The task card is
`compute/20261128-19`, the accepted P5 smoke review is `f422df34`, the accepted E0 fresh record is
`c22ba021`, and local's STOP is `7f6db2c0`. This review was read-only: I ran no GPU job or host workload, read no
private key, and read no sealed label or test value. Host checks were `git config`/file-hash/`ls` reads only.

The deliverable commit itself adds exactly the 32 files under
`docs/r1/reports/trackp_p4_p5_timing_20261128/`; no code, config, spec, seed or micro-batch is touched.
`git diff --check 57e6d1ed..dc725f89` exits 0. The branch tip's parent is `66aa4e10`, not the record's stated
`57e6d1ed`; the two intervening commits are already on `origin/main`.

## P3 — confirmed STOP

| Check | Independent result |
|---|---|
| `git cat-file commit befb58c8` | one file, parent `0b46595418bb21dc0e8e5b234b30f2a84ac5082c`, no `gpgsig` header |
| `git show --stat befb58c8` | `r1/scripts/htcondor/trackp_p4/p4_spec_ada_phase1_20261127.json`, +128 lines |
| spec sha256 | `d9ab62698828adc459c8084c17e2ffd4ae000df71957a155d9e0cb83bf6d5ca6` |
| `git verify-commit befb58c8` | exit 1; no signature |
| Mac repo/global config | `user.signingkey`, `gpg.format`, `commit.gpgsign` all unset; repo-local config has no signing entry |
| Mac agent | `ssh-add -l` = "The agent has no identities" |
| TASL-2, TASL-7, deepthought, deepthought2, Ada | all three settings empty on all five; no agent identities |
| earlier launch key | embedded key in `7d0279d8` has fingerprint `SHA256:32dP45eSMmVSt/G/CGvcxl/P+MO3Nwj9xeTh/GSA2wc` |
| other public keys | Mac `SHA256:tDYAl/Xs8oqsvpNGqdNgyX8JsZwPauBPWrivkxJZ2w8`; TASL-2 `jy66…`; deepthought/2 `hxhO…`; Ada `EuLn…`, `OFqw…`, `V4xq…`; TASL-7 has no `~/.ssh/*.pub` |

No key with the `32dP45…` fingerprint is configured or present on any host reached. P3 is correctly left as a STOP
for the author, not resolved and not re-signed with a non-project key. One wording nit: for the unsigned
`befb58c8`, this git prints no `No signature` line; the unsigned fact is established by the missing `gpgsig` and
`verify-commit` exit 1.

## P5 — numbers reproduce, but the committed capture is incomplete

From the four committed `kernel_capture.json` files the walls and GPU-hours reproduce exactly:

| Arm | Wall s | GPU-h | Step median (ex first) | Step mean (ex first) | Step max (ex first) |
|---|---:|---:|---:|---:|---:|
| `kev-0.8b` | 120.242 | 0.0334 | 1.0230 | 1.1640 | 7.9047 |
| `qwen3.5-0.8b-base` | 117.882 | 0.0327 | 1.0528 | 1.1718 | 6.9628 |
| `kev-4b` | 488.017 | 0.1356 | 5.4855 | 5.5843 | 10.9226 |
| `qwen3.5-4b-base` | 437.816 | 0.1216 | 5.6378 | 5.8007 | 11.1622 |

Total `1163.957 s / 3600 = 0.3233 GPU-h`; the arm-rounded total is also 0.3233. All four captures bound
`causal_conv1d.causal_conv1d_interface.causal_conv1d_fn`,
`causal_conv1d.causal_conv1d_interface.causal_conv1d_update`,
`fla.ops.gated_delta_rule.chunk.chunk_gated_delta_rule` and
`fla.ops.gated_delta_rule.fused_recurrent.fused_recurrent_gated_delta_rule`; no capture contains the
`(torch path)` fallback. The accepted smoke review's mapping is the same.

The step statistics were recomputed from the raw `metrics.jsonl` on Ada
(`/data1/zli538/paperb_p4_20261127/p5_timing_20261128/jobs/<arm>/run/stage_s/metrics.jsonl`, read-only). The
record table matches the recomputation except the `kev-4b` median: the table says **5.4800**, while the raw data
and `timing_summary.json` say **5.4855**. The `timing_summary.json` values for median/mean/max all match the raw
data.

Card/runtime claims check out: all four captures and manifests show card 2
`GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154`, RTX 6000 Ada, `CUDA_VISIBLE_DEVICES=2`, torch `2.6.0+cu124`, CUDA
12.4, transformers `5.19.0`; the Ada venv Python is `3.12.10`; `/data1/zli538/paperb_p4_20261127/freeze.txt` is
121 lines, sha256 `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`. `gpu_before/after` are card
2 at 5 MiB / 8 MiB resident; the manifests show one visible card. All four manifests are `dirty: false`.

The paper-checkout claim is **not** correct as written. The record says all arms ran from `e92f3c73`; the manifests
show `91cfd48a67f8d62d4e20826976cbdbdbcfcaf505` for `kev-0.8b` and `qwen3.5-0.8b-base`, and `e92f3c73` only for
the two 4B arms. The two checkouts have identical `r1/c3/train/run.py`; `r1/scripts/trackp.py` differs only by the
4B gradient-checkpointing flag, which the 0.8B commands do not pass. The timing result is therefore not affected,
but the identity sentence is wrong.

The data-hash claim is also singular where the run is per-arm. `1d39f1ba6eb6cf1a042658571c15d5809a947c0bdd26a7aa61fb913985cfd37c`
is the `kev-4b` `sft_data.json`; the four per-arm values are `0088f559…` (`kev-0.8b`), `9b6552b4…`
(`qwen3.5-0.8b-base`), `1d39f1ba…` (`kev-4b`) and `f997e7fa…` (`qwen3.5-4b-base`), each matching that arm's
`report.json`. All four are accepted-probe synthetic data; only the record's blanket hash is wrong.

The per-card lease statement is plausible but not self-contained in the export. The host `/data1/zli538/r1_locks/gpu2.lock`
exists with mtime `2026-11-28 13:55:11Z` (the last arm's start), and each job directory has its job-local
`gpu0.lock`. The manifests' `gpu_lease` events carry PID and start/end but omit `gpu_index`/`gpu_uuid`, because the
direct path sets `_lease(..., check_processes=False)`; the exported capture therefore does not itself show the
outer `gpu2.lock` event. Citing or including the launcher's lease log would close this.

## Capture integrity — blocking

From a clean checkout of the tip, in the record directory:

```
$ shasum -a 256 -c SHA256SUMS
... 31 lines OK ...
shasum: ./kev-0.8b/metrics.jsonl: No such file or directory
... 8 listed files could not be read
WARNING: 8 listed files could not be read
EXIT=1
```

`SHA256SUMS` has 39 entries, but the commit contains no per-arm `metrics.jsonl` or `run.log`:
`.gitignore:3` excludes `*.log` and `.gitignore:49` excludes `*.jsonl`, so they were silently left out. The eight
missing files do exist on Ada, and their host sha256 values equal the `SHA256SUMS` lines exactly (metrics:
`49942e87…`, `ad1f8442…`, `4e1c169f…`, `a459e37d…`; logs: `88e42b5c…`, `c9c438ea…`, `16a78ba6…`, `bd3d0645…`).
They must still be committed (force-add, or add a negation for this directory) because the record's own statement
that `SHA256SUMS` binds them and that "all captures are the raw job files" is false as delivered, and the required
step-statistic recomputation is impossible from a clean checkout without `metrics.jsonl`.

## Overclaim check

Pass. The record explicitly says the timing run is a manual re-run, not a new formal probe; it leaves the accepted
probe charges at 3.10 GPU-h and the 40 GPU-h phase-1 threshold unchanged; it does not claim P3 is resolved; it
flags P3 for the author; it labels the work ENGINEERING_ONLY, synthetic labels only, no SFT evidence run. The
per-arm `report.json` files carry the same ENGINEERING_ONLY label and per-arm synthetic data hashes.

## Findings

- **Blocking B1.** The commit omits all four `metrics.jsonl` and all four `run.log` files that `SHA256SUMS` lists.
  `shasum -a 256 -c SHA256SUMS` is 31 OK / 8 FAILED (exit 1), and the raw step data cannot be verified from the
  deliverable. Fix by force-adding the eight files and re-running the check to 39/39.
- **Major M1.** The record generalises the 4B arm's paper checkout `e92f3c73` to all four arms. The manifests show
  `91cfd48a` for both 0.8B arms and `e92f3c73` for both 4B arms. State the per-arm commits; the effective runner
  path is otherwise identical.
- **Major M2.** The record gives `1d39f1ba…` as the run's `sft_data.json` hash, but that is only `kev-4b`. Give the
  four per-arm hashes (or point to the per-arm `report.json` values).
- **Minor m1.** The `kev-4b` step median in the record table is `5.4800`; the raw metrics and
  `timing_summary.json` give `5.4855`. Correct the table.
- **Minor m2.** The per-card lease is inferred from the host `gpu2.lock` and job-local `gpu0.lock`; the exported
  manifest events do not include the outer lease's card index/UUID. Add the launcher lease log or cite it.
- **Minor m3.** `git log --show-signature` on the unsigned `befb58c8` does not print `No signature` in this git;
  the unsigned conclusion is still correct by `cat-file`/`verify-commit`.
- **Minor m4.** The record says base `origin/main` `57e6d1ed`, but the tip's parent is `66aa4e10`; the deliverable
  commit still adds only its record directory.

## What remains

Re-commit the eight ignored raw files and regenerate/verify `SHA256SUMS` (39/39 OK), fix the paper/data identity
paragraph and the `kev-4b` median, then re-review. P3 remains a STOP for the author: sign the exact `befb58c8`
bytes with the project identity, or configure that identity for compute. No new formal probe run and no change to
the 3.10 GPU-h probe charge is needed.

## Commands used (representative)

```
git fetch origin --prune
git worktree add --detach <tmp> dc725f894fb342f4062f815999e849a522953661
git cat-file commit befb58c8
git show --stat befb58c8
git rev-parse befb58c8^
git show befb58c8:r1/scripts/htcondor/trackp_p4/p4_spec_ada_phase1_20261127.json | shasum -a 256
git verify-commit befb58c8; echo $?
git log -1 --show-signature 7d0279d8
ssh-keygen -lf ~/.ssh/id_ed25519.pub
ssh -o BatchMode=yes <host> 'git config --global --get user.signingkey; ...; ssh-add -l'
git diff --check 57e6d1ed..dc725f89
git show --name-only --format= dc725f89
cd docs/r1/reports/trackp_p4_p5_timing_20261128 && shasum -a 256 -c SHA256SUMS
python3  # recompute step median/mean/max from metrics.jsonl, excluding step 1
```
