# Review: R1-TASL2-CPU check repeats (local/20261126-01)

- **Unit:** local/20261126-01. The houseprice TASL-2 CPU-set check now gets three complete attempts in one check run.
- **Branch:** `mac-cpuset-repeats-20261126`. Reviewed tip `0c1a9b7f` (commits `32da3235` fix, `0c1a9b7f` driver). The re-check covered `198c6a44` (the minors).
- **Base:** `54082a05` (origin/main)
- **Files:** `sweep2/t1_tasl/dry_run_node.py`, `r1/tests/test_t1_cpuset_repeats.py`, `sweep2/t1_tasl/run_cpuset_check.sh`
- **Reviewer:** a fresh tier-E reviewer, a Claude subagent that did not write the unit. It modified no file and opened no label, test-partition or evaluation file. The author of the unit transcribed this record from the reviewer's hand-back.

## Round 1 (tip 0c1a9b7f): accepted with minors

**Summary.** The fix is small and well placed. The diff touches nothing under `docs/`, `g5_tasl.py` or `g1b_tasl.py`, so the signed `tasl2_cpuset_check` key line stays byte-identical. `cpuset_verdict` and `check_cpuset_record` are unchanged. They still need at least three distinct, complete, deterministic, reference-identical attempts within 9.486 s, all under the same derived spec. The changed behaviour only applies when the spec carries a `cpuset_check` block. Every other spec still uses `g1b_tasl.next_attempt`.

### Points checked

1. **`check_next_attempt` vs G.1b's `next_attempt`.**
   - It creates the attempt directory and `attempt.json` the same way G.1b does: same keys, `exist_ok=False`, `open("x")`.
   - It uses the same `attempts()` scan, so stray entries and symlinks are still refused.
   - A missing job record is refused, as in G.1b. A `node` or `timing` stop is refused, as in G.1b.
   - It is stricter than G.1b in one place: any stop class other than `None` or `infrastructure` is refused. This fails closed.
   - It refuses after 3 complete attempts.
   - `run_node_job` reads `next_attempt` from module globals at line 1246, so the swap made in `main` takes effect. A refusal there still goes to `_refusals/` under the lease.
2. **`is_cpuset_check` misfire.**
   - It only activates when all of these hold: a `cpuset_check` block exists, its `rule` is R1-TASL2-CPU, its node is the argv node, and the run id fully matches `tasl2-cpuset-<node>-YYYYMMDD` for that node.
   - A block that is present but malformed is a STOP before any run.
   - The constants match `g5_tasl` (enforced by a test).
   - A hand-made look-alike spec could get three attempts, but it can never yield a PASS: `cpuset_verdict` requires the derived spec byte for byte.
3. **Other one-attempt assumptions:** none in the check path.
   - `seal` targets `attempt-N` per attempt and refuses to overwrite.
   - `assemble` does refuse several sealed attempts per node, but it is not used by the check.
4. **The tests use the real `run_node_job`.**
   - With `dry_run_node.py` reverted to base, all 6 new tests fail.
   - Removing only the `G.next_attempt = check_next_attempt` line makes the end-to-end test fail with the field STOP message.
   - The `next_attempt` signature test still passes.
5. **Driver vs the original captured driver.**
   - The nested `bash -c` quoting is equivalent.
   - Scope, environment, `taskset`, log placement and leases are unchanged.
   - New and correct: the clean-checkout check, the fix-ancestor check, the refusal of an existing dated run, sealing only on rc 0 with stop_class None, retry only on infrastructure, and the verdict run only over the attempts actually sealed.
6. **Evidence, caps, signed files:** nothing changed.

**Blocking findings:** none.

### Minor findings

- **M1:** the unit never stated whether the 20261126 sealed attempt 1 counts or is superseded. It must not be combined with new attempts.
- **M2:** attempt discovery takes the highest attempt number, so a try refused before the run can blame the previous attempt.
- **M3:** the driver's exit status ignores the verdict.
- **M4:** the "published main" requirement is not enforced.

### Nits

- **N1:** the run root is created before the spec is derived and the leases are taken, so a failure there uses up the day's run id.
- **N2:** a capture directory inside the checkout always fails the clean-tree check.
- **N3:** the driver file is not executable.
- **N4:** the spec is read twice (harmless).
- **N5:** the fix-ancestor check assumes merge commits.

### What the reviewer ran

- **Tip:** `test_t1_cpuset_repeats.py`, `test_t1_g5_tasl.py`, `test_t1_tasl_g1b.py` and `test_t1_tasl_g1b_x.py` gave 413 passed, 2 skipped, 3 failed.
- **Base, same modules:** 407 passed, 2 skipped, and the same 3 failures. They come from macOS (no `/proc`, `/home/dowling` not writable, one 448.4 vs 448.3 rounding).
- **Reverse check and narrow mutation:** as described in point 4.
- `git diff --stat 54082a05..0c1a9b7f -- docs sweep2/t1_tasl/g5_tasl.py sweep2/t1_tasl/g1b_tasl.py` is empty.

**Verdict, round 1: accepted with minors (M1–M4)**

## Re-check (commit 198c6a44): accepted

Only `run_cpuset_check.sh` changed (now mode 755). `bash -n` passes.

- **M1 (fixed):** the header states that the 20261126 attempt 1 is superseded and never combined. The existing run root and the sealed run are refused.
- **M2 (fixed):** the driver counts attempts before and after each try. If a try made no new attempt, the loop stops with a STOP that points to `_refusals/`.
- **M3 (fixed):** exit 0 only when the verdict rc is 0 and the verdict is PASS.
- **M4 (fixed):** `git fetch origin main` runs first, and HEAD must be an ancestor of `origin/main`.
- **N1 (fixed):** the spec is derived into the capture directory first. The run root is created only after the leases are held, and the copied spec's sha256 is checked. Byte-identity of the spec seen by the attempts, the seal and the verdict still holds.
- **N2, N3 (fixed).**
- **New nits, optional:**
  - **A1:** a reused capture directory makes `cpuset-spec` refuse (no overwrite). This fails closed; use a fresh capture directory per run.
  - **A2:** the run date stays the one taken at the start, even if the lease wait crosses midnight. This is consistent.

**Re-check verdict: accepted**
