# Verdict: CHANGES REQUIRED

Task: `compute/20261127-33` item 1 (with the disposition `compute/20261128-05` item 2) — the G.5 houseprice
TASL-2 CPU-set rerun under R1-TASL2-CPU, `sweep2/t1_tasl/run_cpuset_check.sh` at `b5626bf4`.
Reviewed tip: `compute-houseprice-cpuset-20261128` @ `e62a9fc0bd657c06179a795639bd7aec3fda9015`
(base `origin/main` `a98d2eff1d2847e34f00effe66b53bc00467e936`).

Method: read-only. A separate worktree of the reviewed tip, `git diff`/`git ls-tree`/`git show`, `shasum -a 256 -c`,
local regeneration of the derived check spec and a recomputation of the verdict consumer
(`g5_tasl.check_cpuset_record`) at the tip. No file of the deliverable was modified; no host was contacted; no
job was launched; no label or evaluation value was read.

The substantive result is sound: the canonical record is a genuine R1-TASL2-CPU PASS that the on-`main` consumer
accepts, and every number in the report matches it. **One packaging defect blocks acceptance:** the three seal
receipts the manifest lists (`seal_attempt_{1,2,3}.out`) are **not on the branch** — a blanket `*.out` rule in
`.gitignore` silently excluded them — so `SHA256SUMS` fails on a clean checkout and the per-attempt seal
evidence is absent from the deliverable.

## Findings

1. **BLOCKING — missing capture: the three seal receipts are not committed.** The branch tip tracks 17 files in
   `docs/r1/reports/g5_cpuset_20261128/`, but the directory the author captured has 20 and `SHA256SUMS` lists 19.
   The three `seal_attempt_{1,2,3}.out` files are present only as **ignored** files in the author's worktree:

   ```
   $ git ls-tree -r --name-only e62a9fc0 docs/r1/reports/g5_cpuset_20261128/ | wc -l
   17
   $ git status --short --ignored docs/r1/reports/g5_cpuset_20261128/
   !! docs/r1/reports/g5_cpuset_20261128/seal_attempt_1.out
   !! docs/r1/reports/g5_cpuset_20261128/seal_attempt_2.out
   !! docs/r1/reports/g5_cpuset_20261128/seal_attempt_3.out
   $ git check-ignore -v docs/r1/reports/g5_cpuset_20261128/seal_attempt_1.out
   .gitignore:4:*.out	docs/r1/reports/g5_cpuset_20261128/seal_attempt_1.out
   ```

   On a clean checkout of `e62a9fc0` (fresh worktree) the manifest does not verify:

   ```
   $ shasum -a 256 -c SHA256SUMS        # in the clean worktree
   ...
   shasum: seal_attempt_1.out: No such file or directory
   seal_attempt_1.out: FAILED open or read
   shasum: seal_attempt_2.out: No such file or directory
   seal_attempt_2.out: FAILED open or read
   shasum: seal_attempt_3.out: No such file or directory
   seal_attempt_3.out: FAILED open or read
   shasum: WARNING: 3 listed files could not be read
   rc=1
   ```

   (`shasum -c` passes in the author's own worktree only because the ignored copies still sit there — the hash
   `a35e38d8…`, `013b48fd…`, `e187cc73…` match, but they are not in the commit.) The `.out` files are the only
   per-attempt seal evidence: the corresponding `.err` files are intentionally empty (`e3b0c442…`), so without
   them the branch carries no committed receipt for any attempt, only the aggregate record.
   The report also over-claims at this tip: `G5_TASL2_CPUSET_CHECK_20261128.md` lines 38–39 list "the three
   `seal_attempt_{1,2,3}.{out,err}`" and say "`SHA256SUMS` binds them".
   **Fix:** force-add the three files unchanged on the deliverable branch (`git add -f`, as done for the ignored
   capture in `28e451ea`), commit without amending/force-pushing, and re-run `shasum -a 256 -c SHA256SUMS` in a
   fresh worktree of the new tip. No content change is needed.

2. **Diff scope is otherwise exactly what is claimed.** `git diff --name-status origin/main..HEAD` shows 17
   additions and no modification or deletion; a single commit (`e62a9fc0`, parent `a98d2eff`), 496 insertions.
   Every path is under `docs/r1/reports/g5_cpuset_20261128/`:
   `git diff --name-only origin/main..HEAD | grep -v '^docs/r1/reports/g5_cpuset_20261128/'` is empty.
   `git diff --check origin/main..HEAD` is clean. Nothing outside the new directory changed.

3. **Manifest contents, for the files that are tracked.** All 16 tracked data files plus the record and the memo
   verify (`shasum -a 256 -c` → `OK` each); the record and spec hashes were recomputed independently with
   Python `hashlib`:
   - `G5_TASL2_CPUSET_CHECK_mlgym_houseprice_20261128.json` = `2447e4363976b6d5565f4b49efa079d35989f8cf8a284bb8190f6a43e4665c61`
   - `cpuset_spec.mlgym_houseprice.json` = `323434a3d597f4a2900816ffff1d32cadbc7f3b6848b4c2bfad00da22334652d`
   - `cpuset_spec.err`, `cpuset_verdict.err`, `cpuset.checkout.status.txt`, and the three `seal_attempt_*.err`
     are zero bytes (`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
   `SHA256SUMS` correctly lists every captured file except itself. Only finding 1 separates this from a fully
   self-verifying manifest.

4. **Canonical record recomputed and accepted by the consumer.** At the tip, with the record bytes supplied through
   a `read_main` stub, `g5_tasl.check_cpuset_record(spec, "mlgym_houseprice", …)` returns
   `{'node': 'mlgym_houseprice', 'cpus': '0-7', 'record': …/G5_TASL2_CPUSET_CHECK_mlgym_houseprice_20261128.json,
   'sha256': '2447e436…'}` — i.e. the record would pass the on-`main` gate. The recorded fields are internally
   consistent and match the task:
   - `verdict: PASS`, `reason: null`, `complete: true`, `repeats: 3`, three attempts, `schema:
     g5_tasl2_cpuset_check/1`, `label: ENGINEERING_ONLY`, `rule: R1-TASL2-CPU`, `host: TASL-2`, `node:
     mlgym_houseprice`, `cpus: 0-7`, `g1b_cpus: 8-15`, `configs: c0…c4`.
   - `budget_s: 9.486` — recomputed as `round(5.059 × 1.25 × 1.5, 3)` from the `mlgym_houseprice` `run_seconds`
     in `sweep2/t1_tasl/g5_tasl_spec.json` (matches `cpuset_budget_s` at line 960 of `g5_tasl.py`).
   - `max_wall_s` = **3.810 / 3.858 / 3.848**, all ≤ 9.486 (`within_budget: true` each); `c0_median_wall_s` =
     2.878 / 2.856 / 2.860; `affinity` = `[0,1,2,3,4,5,6,7]` and `affinity_ok: true` for all three.
   - `harness_commit c025f89aeafc2199bf3487b4bcaa16678273c702` = the G5-7 `g1b_pin`;
     `g1b_run_id g1b-tasl-20261121-b` and `g1b_spec_sha256 7ff3c95b963a2f1690461ca58dc98bec7ad79e31ccbbe159c57004716a8cc5f7`
     = the signed spec, whose file `sweep2/t1_tasl/g1b_tasl_spec.json` I re-hashed to the same
     `7ff3c95b…`.
   - `check_spec_sha256 323434a3…` was **re-derived, not just read**: calling
     `g5_tasl.cpuset_spec(spec, "mlgym_houseprice", "tasl2-cpuset-mlgym_houseprice-20261128")` at `a98d2eff`
     produces bytes byte-identical to the committed `cpuset_spec.mlgym_houseprice.json`, sha256 `323434a3…`.

5. **The seal receipts bind to the record (where present).** In the author's worktree, each
   `seal_attempt_N.out` has `run_id tasl2-cpuset-mlgym_houseprice-20261128`, `host TASL-2`, `attempt N`,
   `stop: null`, `stop_class: null`; its `job_record_sha256` equals the record's per-attempt value
   (`042f227a…`, `a686578e…`, `dd69b01e…`) and its `sealed_path` equals `attempts[N].sealed`; the three
   `node_log_sha256` values are distinct (`bce87b6f…`, `912bad7b…`, `909c1152…`). `cpuset_driver.status` records
   `try_N_rc=0`, `attempt_N_stop_class=None`, `seal_N_rc=0` for 1–3, one launch per attempt. This is exactly
   right in content — it is only not committed (finding 1).

6. **Reference identity is the declared G.1b TASL-2 attempt and the comparison is defined correctly.** The
   record's `reference` is `{attempt: 1, job_record_sha256:
   15b7beea61f7829d396a9aa0415462e80c3aabd6c62c9c3327b2528af2a690aa, sealed:
   …/sealed_g1b/g1b-tasl-20261121-b/mlgym_houseprice/attempt-1}`, identical to `g1b_tasl2_attempts.mlgym_houseprice`
   in `sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json` and to the reference block of the pre-existing 26 Nov STOP
   record. `identical_to_reference` is computed at `g5_tasl.py:2086-2179` as equality of the per-(config,
   condition) `g1b_lib._outcome` digests against the sealed reference rows; the per-attempt `job_record_sha256`
   differ by design (run-specific ids/timestamps) and the report does not claim they are equal. "Bit-identical
   outcomes" is therefore used in its correct, digest-level sense.
   Non-blocking reviewability limit: the sealed attempts' job records and node logs stay on TASL-2 and are not
   copied into the capture, so the booleans and timings can be confirmed as recorded and as gate-accepted, but
   not re-derived from repository artifacts. That is the reviewed driver's capture behaviour, unchanged here.

7. **ENGINEERING only; no sealed/test labels or evaluation values.** A case-insensitive scan of the whole capture
   directory for `label|eval|test|score|metric|target|oracle|secret` returns only `ENGINEERING_ONLY`, the
   "no label" phrases in `cpuset_check.output_use` (spec) and the memo, and node/run identifiers. The record
   carries no metric value — only booleans, timing, affinity and sha256 values (its key set is exactly
   `attempts, budget_s, check_run_id, check_spec_sha256, complete, configs, cpus, g1b_cpus, g1b_run_id,
   g1b_spec_sha256, harness_commit, host, label, node, reason, reference, repeats, rule, schema, verdict`). The
   derived spec contains only the signed G.1b engineering inputs (hosts, node specs, seeds, env pins, census),
   with `label: ENGINEERING_ONLY`. No class label, split label or evaluation value is read or leaked.

8. **Run id, dates and timestamps are internally consistent.** `check_run_id`
   `tasl2-cpuset-mlgym_houseprice-20261128` equals the spec `run_id` and every seal receipt's `run_id`.
   `driver_start 00:14:01Z` → `host_before 00:14:01Z` → attempt logs `00:14:01Z/00:14:32Z/00:15:03Z` → seals
   `00:14:32Z/00:15:03Z/00:15:34Z` → `leases_released`/`driver_end 00:15:34Z`, monotone at ~31 s per attempt.
   The host listings' local mtimes (27 Nov 16:14–16:15) are the same instants on the host's UTC-8 clock, so the
   UTC date at run time is 2026-11-28; the memo's "first unused UTC date" is correct and avoids the 20261127
   root. The driver refuses an existing run root or sealed run (`run_cpuset_check.sh` line 38; again at line 70), and
   the status records no STOP, so the date choice is evidenced as unused.

9. **Earlier scenes are untouched.** The diff is add-only (finding 2); the 26 Nov scene still exists unmodified:
   `docs/r1/reports/tasl_chain_20261122/G5_TASL_PREP_20261126_captures/tasl2/G5_TASL2_CPUSET_CHECK_mlgym_houseprice_20261126.STOP.json`
   (sha256 `507ba854d5b27dbbd977c5dd0c21440d99b7a3e98618913fb8afb4bd620c2a0a`), with its own
   `check_spec_sha256 2a5da2e8…`, `reason too_few_attempts` and attempt hash `c92de70e…` — none of which is
   folded into the new record. No 27 Nov cpuset file exists in this repository, so the "27 Nov STOP scene
   untouched" statement cannot be checked from the repo; nothing in the diff touches it, and the distinct run id
   plus the driver's root guards make combination impossible.

10. **Driver identity, affinity and lease evidence hold.** `git diff b5626bf4 a98d2eff --
    sweep2/t1_tasl/run_cpuset_check.sh` is empty; the script is sha256
    `8739bc67a455ea6b4fc67109eb2bb9d064d2010c92961879be235a970f952608` at both tips and at the accepted
    candidate `c5fd2afa`, and `bash -n` passes. The memo's "CPUs 0-7 on physical cores 0-3" matches
    `docs/r1/reports/tasl_chain_20261122/TASL2_CPU_STABILITY_20261125.md` (CPUs 0–7 = `core_id` 0, 4, 8, 12 —
    four physical cores, two SMT threads each). `cpuset_lease_state.txt` shows driver fds 7/8/9 →
    `gpu0.lock` / `cpus-0-3.lock` / `cpus-4-7.lock` with inodes 120088542 / 120088404 / 120088438, matching the
    `/proc/locks` entries; `cpuset_host_after.txt` lists the three sealed attempt directories.
    Non-blocking: the capture does not include a copy or sha256 of the driver script (the 26 Nov scene did), so
    its identity is established against published `main` rather than against the run; the status/spec/seal
    formats are consistent with that script.

## STOP conditions

One: finding 1 — the deliverable is missing the three seal-receipt captures that its own `SHA256SUMS` and memo
claim, and the manifest does not verify on a clean checkout. Everything else passes; no over-claim, mismatch or
STOP was found in the record's result, hashes, dates or scope. Acceptance should follow a force-add of the three
unchanged `seal_attempt_{1,2,3}.out` files and a re-verified manifest.
