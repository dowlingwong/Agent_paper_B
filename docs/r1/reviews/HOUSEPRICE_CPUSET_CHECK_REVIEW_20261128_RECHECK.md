# Verdict: ACCEPTED

Re-check of finding 1 of `HOUSEPRICE_CPUSET_CHECK_REVIEW_20261128.md`.
Task: `compute/20261127-33` item 1 (with the disposition `compute/20261128-05` item 2) — G.5 houseprice TASL-2
CPU-set rerun under R1-TASL2-CPU.
Re-checked tip: `compute-houseprice-cpuset-20261128` @ `e1a16d59e298d1fb869f535d04dee60627046fda`
(one commit on top of the previously reviewed `e62a9fc0`, no amend or force-push).
Base: `origin/main` `a98d2eff1d2847e34f00effe66b53bc00467e936`.

Method: read-only. A fresh worktree at `/tmp/hp_recheck` created from `e1a16d59` (not the author's checkout),
`git ls-tree`/`git show`/`git diff`, `sha256sum -c SHA256SUMS` inside that clean checkout, and a re-run of the
on-`main` consumer `g5_tasl.check_cpuset_record` at the new tip. No deliverable file was modified; nothing was
pushed or amended.

**Finding 1 is fully fixed.** The three seal receipts are now committed unchanged, the manifest verifies in a
clean checkout, the new commit touches nothing else, and the record's capture claim is accurate.

## Findings

1. **All 20 capture files are tracked at the new tip.** From the fresh worktree root:

   ```
   $ git ls-tree -r --name-only e1a16d59 -- docs/r1/reports/g5_cpuset_20261128 | wc -l
   20
   ```

   The list includes `seal_attempt_1.out`, `seal_attempt_2.out`, `seal_attempt_3.out` (blobs
   `fcda3ad8…`, `fc667697…`, `1c99a824…`), alongside the 17 files already present at `e62a9fc0`.

2. **`SHA256SUMS` verifies in the clean checkout.** `sha256sum -c SHA256SUMS` reports `OK` for all **19 listed
   entries** and exits `rc=0`, including the three seal receipts. The manifest deliberately does not list itself
   (standard), so the 20-file directory is fully accounted for: 19 data files hashed + `SHA256SUMS`. There is no
   missing or unlisted capture.

3. **The seal receipts are unchanged and consistent with the record.** Each file is 538 bytes and hashes to the
   value recorded in the pre-fix manifest — `a35e38d86baa18b544036e164d389d19898b2a9ff475bf2e9d4c13a12d505bb9`
   (attempt 1), `013b48fd366f69f862d51bec973c592b06e02ec677ed5d3eb9a76a2e1143d5b3` (attempt 2),
   `e187cc738798f441a82f13002323eab8fca3a3f3c7d18d3ee84c2ab6ed0a39af` (attempt 3) — identical to the copies
   the author had before the fix, i.e. no content was rewritten to make the manifest pass. Contents are valid
   `g1b_tasl_seal_receipt/1` receipts:
   - `run_id tasl2-cpuset-mlgym_houseprice-20261128`, `host TASL-2`, `attempt` 1/2/3, `stop: null`,
     `stop_class: null`;
   - `sealed_path` equals the record's `attempts[N].sealed` for each attempt;
   - `job_record_sha256` equals the record's per-attempt value (`042f227a…`, `a686578e…`, `dd69b01e…`);
   - three distinct `node_log_sha256` values (`bce87b6f…`, `912bad7b…`, `909c1152…`);
   - `sealed_utc` 00:14:32Z / 00:15:03Z / 00:15:34Z, consistent with `cpuset_driver.status` (`seal_N_rc=0`,
     logs at 00:14:01Z / 00:14:32Z / 00:15:03Z) and `driver_end 00:15:34Z`.

4. **The new commit changes nothing else.** `e1a16d59` has parent `e62a9fc0`, adds only the three `.out` files
   (3 files changed, 39 insertions, 0 deletions), and `git diff --name-status e62a9fc0..e1a16d59` lists only
   those three. The canonical record, the memo and `SHA256SUMS` are byte-unchanged (`git diff` over them is
   empty), so the record's sha256 is still
   `2447e4363976b6d5565f4b49efa079d35989f8cf8a284bb8190f6a43e4665c61`. `git status` in the fresh worktree is
   clean.

5. **The record's capture claim is now accurate.** `G5_TASL2_CPUSET_CHECK_20261128.md` lines 38–39 list the three
   `seal_attempt_{1,2,3}.{out,err}` and say `SHA256SUMS` binds them; all six files are tracked and every one is
   listed and verifies. The over-claim identified in the first review is resolved.

6. **The substantive result still holds at the new tip.** The record is unchanged, and
   `g5_tasl.check_cpuset_record(spec, "mlgym_houseprice", …)` at `e1a16d59` still returns OK with sha256
   `2447e436…`: `verdict: PASS`, `reason: null`, `complete: true`, 3 attempts, `cpus 0-7`, `g1b_cpus 8-15`,
   `budget_s 9.486`, max wall 3.810 / 3.858 / 3.848, affinity `[0..7]` each. Findings 2–10 of the first review
   are unaffected by this commit and remain as accepted there.

## Residual non-blocking observations

- `.gitignore:4 (*.out)` is still in place. The fix works because the three files were force-added, but a future
  driver capture with `seal_attempt_*.out` will be silently dropped the same way. The capture procedure (or the
  driver's documented handoff) should state the `git add -f` step for `*.out`, so this cannot recur.
- The sealed job records and node logs remain on TASL-2 and are not copied into the capture; the outcome-digest
  equality and timings are therefore confirmed as recorded (and as gate-accepted), not re-derived from the repo.
  This is the reviewed driver's behaviour, not a defect of this commit.
- The capture contains no copy/sha256 of `run_cpuset_check.sh`; its identity is established against published
  `main` (sha256 `8739bc67…`, identical at `b5626bf4`, `a98d2eff` and the accepted candidate `c5fd2afa`), not
  against the run.
- The 27 Nov STOP scene lives outside this repository, so "untouched" cannot be checked here; nothing in either
  commit touches it, and the distinct run id plus the driver's root guards prevent combination.
