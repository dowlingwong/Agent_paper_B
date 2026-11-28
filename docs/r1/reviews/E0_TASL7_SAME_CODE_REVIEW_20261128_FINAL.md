# Verdict: ACCEPTED

Final recheck of task `compute/20261128-01`, PLAN row `R1-P4-E0-SAME-CODE-REFERENCE`.
Rechecked tip: `compute-p5-tasl7-e0-20261128` @ `391c12bc4d654313bdf9d3da652f45fb0f4bee4e` (one new commit on
top of the previously reviewed `1d2153bdf18a97fdaa63020ceabe08131959add9`; base
`a98d2eff1d2847e34f00effe66b53bc00467e936`). Independent, read-only check in a fresh detached worktree at
`/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/e0tasl7review/final/tip`; no host login, no
run, no GPU job, no label read. This file is a new commit on the existing review branch; the earlier rounds are
`docs/r1/reviews/E0_TASL7_SAME_CODE_REVIEW_20261128.md` and `…_RECHECK.md`.

## Bottom line

The one remaining residue is fixed and nothing else moved. `SHA256SUMS` verifies for every listed file, the
record's cited `comparison_e0e.json` hash now equals both the actual file and `SHA256SUMS`, the record's own
sha256 is `d4b9f02c…`, and the STOP reading is unchanged. **No required finding remains.**

## Verified at this tip

1. **Scope.** `git diff --name-status 1d2153bd..391c12bc` is exactly two modified files, both in the record
   directory: `E0_TASL7_SAME_CODE_20261128.md` and `SHA256SUMS`. `git diff --name-status a98d2eff..391c12bc` is
   still 12 additions, all under `docs/r1/reports/trackp_p5_tasl7_20261128/`; no code, config, plan or
   `.gitignore` change. `git diff --check a98d2eff..391c12bc` exits 0.

2. **Twelve files and checksums.** The record directory has 12 tracked files. `shasum -a 256 -c SHA256SUMS`
   exits **0** and reports `OK` for all 11 listed files (the twelfth is `SHA256SUMS` itself, not listed).
   `gpu_lease.jsonl` is present at sha256
   `f71fa1e50cd8141e074a5a92e563f8737f19a5ef0ff4edc1b2032d69fdfe4114`, matching the previous rounds and the
   manifest's lease events.

3. **Record hash.** `E0_TASL7_SAME_CODE_20261128.md` computes to
   `d4b9f02cac8a99ec507ffa42802d67dc26481eae9472fd1c9eb810617855b10b`, exactly the value now listed in
   `SHA256SUMS` and the value named in the handover.

4. **The corrected comparison hash.** The record's "Files" paragraph now cites `comparison_e0e.json` as
   `715248d7…`. The actual file is
   `715248d7870a0a90075be5caf50f97fc1beb799793fadc90b844a7f87d54120e`, and `SHA256SUMS` line 2 carries the same
   value. Prose, file and checksum file agree; the stale `46805e6c…` citation is gone (grep finds no occurrence in
   the record directory).

5. **Corrected wording.** The record now says "the other differing fields are host/launcher/runtime and directory
   fields (`venv`, `image`, `direct`, lease, paths), plus the unused `sft` block, not the E0 recipe" — accurate for
   the config delta, with the unused `sft` block correctly separated. It also says "the manifest records hostname
   TASL-7 and the lease the same card UUID" — accurate: the manifest has `host.hostname: TASL-7`, and the lease
   carries `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, the same card UUID as the manifest.

6. **Comparator and result unchanged.** Re-running `python3 p5_compare_ada.py ada_reference_e0e_report.json
   e0e_report.json` still exits **1** and produces output byte-identical to `comparison_existing_comparator.json`
   (`e85aa003…`), `equivalent: false`. The criteria are unchanged: width delta `+0.0021793164792374142` (pass,
   0.05 abs), mean delta `−0.0014910816855873144` (pass, 0.05 abs), RPS relative `0.1909135626876941` (fail,
   0.10 rel). `comparison_e0e.json` still carries the same numbers with the corrected
   `reference_ada`/`candidate_tasl7` orientation.

7. **STOP unchanged.** The record still says the run completed cleanly but the three-criterion comparison is not
   equivalent, that the miss is a STOP, that no tolerance was widened, the reference was not changed, no
   better-value re-run was substituted, and the run is not a parity timing carry-forward. Lease span remains
   28 min 24 s = 1,704 s = 0.4733 GPU-h.

## Residual observations (non-blocking)

- The tolerance sentence in the record (line 58) is a long unwrapped line; purely cosmetic.
- The captures show 44 MiB total idle device use; the record's `0 MiB` is correctly qualified as foreign-process
  memory (`other_processes.memory_mib = 0`). Correct.
- The TASL-7 Python 3.12.15 value comes from the pinned config, not a runtime capture; the record discloses it as
  a host difference against Ada's 3.12.10, and the required torch/transformers/peft pins match.
- `origin/main` is now `73524055`, ahead of the declared base `a98d2eff`; the branch adds only the record
  directory, so it is merge-safe.

## STOP disposition

**The RPS criterion remains a real STOP: 1.163752e-4 vs Ada 1.438354e-4 is 19.09 % below, against a 10 % relative
tolerance, so `equivalent: false` and the Ada phase-1 note's `ada_smoke_e0` line and A5 SFT remain gated; no
tolerance, reference or result may be changed to turn the miss into a pass.**

## Limits

- No host access; the manifest, report, lease, config, comparator and comparison were verified from the committed
  copies. The training was not re-run; only the comparator was re-run.
- The review is of the record and its captures, not a re-execution of the TASL-7 training.
