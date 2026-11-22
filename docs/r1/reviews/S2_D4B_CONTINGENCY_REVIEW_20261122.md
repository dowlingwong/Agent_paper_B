Reviewed base: `9c2979a2` (published `main`); accepted at `dfc4b46e547d9bd3b3840f929cab42a66e2ddfaf`

# Independent review record — the sweep-2 audit's D4 option-B contingency (R1-BX-PROPOSED-CONFIRM REVISIONS (c), E5 partial labels), implemented and kept OFF

**Unit.** On `mac-s2-d4b-20261122`: `r1/c3/audit_d4b.py` (new), the inert hooks in `r1/c3/audit.py` (`run_config`, `evidence_run`,
`verify_evidence_completion`, CLI `--d4b-after-stop`), the `/5` refusal in `r1/c3/train/sft_data.py`, `r1/tests/test_c3_sweep2_d4b.py` and
`docs/r1/reports/s2_d4b_20261122/S2_D4B_CONTINGENCY_20261122.md`. Authority: R1-SWEEP2-B2-DECISIONS (D4 A; the contingency "implemented now,
as an independently reviewed code path that stays unused ... used only after a D4 STOP and a further author row"); R1-BX-PROPOSED-CONFIRM
REVISIONS (c); the signed sweep-2 preregistration (PRE-DIV A, the gate-input builder pinned by sha256); the queue of 22 Nov 2026 (01:22), item 1.

**Process.** One independent reviewer for all three rounds, read-only, synthetic data only (no label, evaluation, sealed or secrets
file opened), scratch under `/tmp/rev_d4b/` moved to its `_to_delete/`. Round 1 found one blocking defect (the rows did not have the frozen
gate-input builder's shapes), two majors (divergence read too broadly; the verify path untested) and eight minors; round 2 found one major
(the non-finite word searched across the whole log tail) and three minors; round 3 accepted with one note for the author row.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `d7d73bb8` | NOT ACCEPTED (B1; M2, M3; minors 4–11) |
| 2 | `03e643fb` | NOT ACCEPTED (M1; minors 2–4) |
| 3 | `dfc4b46e` | ACCEPTED (one note for the author row) |

**Open items.** The contingency stays OFF: no row `R1-SWEEP2-B2-D4B` exists. If a D4 STOP happens, the author row names the sweep-2 run id, REVISIONS (c) and the STOP's sha256, and confirms or amends the two readings listed in the report (divergence from the final error only; an incumbent's divergent run is a STOP). Before any contingency label is used, a reviewed change of `release_checks.sweep2_integrity` and `sft_data.LabelBlockSource` is needed (both refuse `/5` today). The scratch estimate of a contingency run should allow one extra node copy per divergent run.

## Round 1 (`d7d73bb8`)

> **NOT ACCEPTED**
>
> Unit: `mac-s2-d4b-20261122` @ `d7d73bb8`, compared with `9c2979a2`. I changed nothing under /tmp/pb, and the worktree is clean (`git status --short | wc -l` gives 0). I opened no label, evaluation, sealed or secrets file.
>
> ## BLOCKING
>
> **1. The label and evaluation rows don't match the frozen gate-input builder (PRE-DIV A), so a contingency audit could never feed the preregistered gate.**
> - Where: `r1/c3/audit_d4b.py:180-198` (label and evaluation rows in `blocks`) and `:139-146` (`block_label`).
> - What is wrong:
>   - The signed preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, frozen_utc 2026-11-21T21:41:44Z) pins `gate_input_builder_sha256: f67ee5e7…`. That equals `sha256sum r1/c3/gate_input_builder.py`.
>   - That builder already defines how partial and divergent rows look:
>     - labels have `label_kind` "audit" (partial means `soft_parameters.k_label` < 5, with n−k ≤ n/2) or "divergent" (`_label_ok`, gate_input_builder.py:153-177);
>     - evaluation rows carry `divergent_seeds` and `k_evaluation` = n − len(divergent_seeds), "both or neither" (`_evaluation`, :180-200).
>   - D4B instead emits `label_kind: "audit_partial"`, and evaluation rows with `k_evaluation`, `divergent`, `candidate_diverged_seeds` and `incumbent_diverged_seeds`, but no `divergent_seeds`.
>   - It also allows k = 2 partial labels: 2 candidate plus 1 incumbent divergence at distinct seeds gives k = 2. The builder refuses k_label = 2.
> - Probe output (synthetic rows fed to `B._label_ok` and `B._evaluation`):
>   - complete: label "accepted audit"; eval "REFUSED: p: divergent_seeds and k_evaluation come together"
>   - one label seed divergent: label "REFUSED: p: label kind 'audit_partial' is not audit/divergent"
>   - `block_label([None,None,.9,.9,.9],[.8,.8,None,.8,.8])` gives divergent=False, k=2, partial=True
> - Failure scenario: a D4 STOP happens, the author writes R1-SWEEP2-B2-D4B, and the contingency audit runs and is released after a consumer change. The frozen builder then refuses every evaluation row, including complete ones, and every partial label. The only way forward is to edit a sha-pinned, frozen preregistration file after divergence has been seen.
> - The report's "Consumers" section doesn't mention this. It says consumers need a change to "add divergent and partial labels", but the frozen builder already defines them.
> - Fix:
>   - emit the builder's shapes: `label_kind` "audit" with `k_label` in `soft_parameters` (and no foreign top-level keys), or "divergent";
>   - give evaluation rows `divergent_seeds` and `k_evaluation` (= 5 − len) and `delta_evaluation: null` when divergent;
>   - write down how incumbent divergence maps onto `divergent_seeds`, or STOP on it;
>   - require k_label ≥ 3;
>   - add a test that runs D4B rows through `gate_input_builder._label_ok` and `_evaluation`.
>
> ## MAJOR
>
> **2. The reading of "divergence" is too broad and fails open (it turns non-divergence failures into labels).**
> - Where: `r1/c3/audit_d4b.py:55,63-69`; test at `r1/tests/test_c3_sweep2_d4b.py:49`.
> - What is wrong: any `exit code -?\d+` counts as divergence. At harness 6adf385:
>   - `local_worker._run_command` sets `failure_msg = f"exit code {result.returncode}"` for every non-zero exit (shell=True);
>   - openml nodes' `train.py` return 2 for `ConfigError`, logged as `FAILURE_CATEGORY=invalid_config` (a deterministic config rejection);
>   - they return 1 for any runtime error, including data loading;
>   - OOM-kill or SIGKILL shows up as 137 or −9, and SIGABRT as −6.
> - The test explicitly asserts that "exit code -6" is divergent.
> - E5 says "a non-finite loss, or no metric **at the fixed budget**". A crash before the budget is not obviously that.
> - `run_config` (audit.py, the row dict) doesn't record `failure_category` or a log tail, so a D4B audit can't tell these cases apart afterwards.
> - Failure scenario: memory pressure on deepthought OOM-kills 3 of 5 candidate seed runs. Under D4 A that is a STOP. Under D4B the proposal becomes "divergent" (u = −g) and is counted as a property of the proposal.
> - Fix:
>   - record `failure_category` (from `res.extra`) and a short log tail in the row;
>   - exclude `invalid_config` / exit 2 and signal exits (negative, or ≥ 128) from divergence;
>   - ideally require a non-finite signature (for example sklearn's "non-finite parameter weights", or the `nan` metric line) for exit 1;
>   - name the chosen reading explicitly in the author-row section.
>
> **3. The consumption-time re-check in `verify_evidence_completion` has no test.**
> - Where: `r1/c3/audit.py:1335-1350` and `:1386`; `r1/tests/test_c3_sweep2_d4b.py:249`.
> - The report claims verify re-checks the record against the row and the STOP and re-derives both blocks. No test calls verify on a /5 audit. The only consumer test monkeypatches `verify_evidence_completion` away before calling `release_checks.sweep2_integrity`.
> - My scratch probe, built on `test_sweep2_completion_verifies_end_to_end`, shows the code behaves correctly:
>   - positive round trip passes (label `audit_partial`, k 4);
>   - completion has d4b but the environment lacks it: "a D4B contingency record outside a sweep-2 contingency audit";
>   - environment has it but the completion lacks it: "evidence completion metadata mismatch";
>   - row withdrawn: "D4B is OFF: …";
>   - STOP.json moved: "D4B: the stopped audit has no STOP.json/environment.json, or completed".
> - Fix: add these cases to `test_c3_sweep2_d4b.py`, plus a release-check test that does not mock verify.
>
> ## MINOR
>
> 4. **The author-row section doesn't surface the incumbent-divergence rule** (`audit_d4b.py:141-143`). Dropping a pair because the incumbent diverged, marking the label partial, and STOPping below 2 usable pairs are not in E5 or PRE-DIV A. Fix: list this rule in the report's "For the author row" section, and see finding 1 for the conflict with the builder.
>
> 5. **The report's claim that "the label readers accept only /4" is inaccurate for `sft_data.LabelBlockSource`.**
>    - It checks only the prefix `"r1.c3_audit_completion/"` (`r1/c3/train/sft_data.py:226,259`).
>    - A /5 block is refused only because D4B rows carry keys outside `LABEL_ROW_KEYS` (:112). A block holding only rule_noop rows would load.
>    - `release.evidence_tier` (release.py:430) treats /5 as T0, which fails closed.
>    - Fix: pin the accepted schemas in sft_data (or correct the claim) and add a test.
>
> 6. **A relative stopped-audit path isn't resolved, so a symlinked directory is followed** (`audit_d4b.py:82-86`).
>    - Probe: a symlinked `results/r1/evidence/C3_audit_EVIDENCE_link` pointing outside paper_root was accepted.
>    - An absolute path to it fails with a generic `relative_to` error.
>    - The STOP sha binding limits the harm.
>    - Fix: refuse symlinks in the path, as `evidence_output_path` (audit.py:794-803) does.
>
> 7. **Evaluation-block counts are missing** (`audit_d4b.py:205-209`). `counts()` covers the label block only; divergent and partial evaluation rows are not counted in the completion. PRE-DIV A asks for them to be counted. Fix: add evaluation counts.
>
> 8. **Verifying a /5 audit depends forever on outside state.** It needs the stopped audit directory (STOP.json unchanged, no completion) and the exact row text on origin/main. Archiving the directory or fixing a typo in the row makes the audit unverifiable. Fix: document this, or bind the STOP bytes inside the contingency audit.
>
> 9. **A STOP of a contingency audit itself qualifies as "the D4 STOP"** (`audit_d4b.py:92-95`). Its environment carries `d4b_contingency`. Fix: require the stopped audit's environment to lack `d4b_contingency`, so that only a D4 A STOP counts.
>
> 10. **New run condition after a crash** (audit.py `run_config`). With `continue_on_divergence`, later seeds reuse the same `node_dir` after a non-zero-exit run, for example a failed `artifacts/metrics.json`. D4 A never did this. Fix: disclose it, or use a fresh copy after a divergent run.
>
> 11. **Test gaps:**
>     - the evidence_run fixture never produces `success: False` / "exit code N" rows (its Future always returns success True);
>     - the `--d4b-after-stop` CLI flag is untested;
>     - absolute-path and symlink cases are untested.
>
> ## Verified sound
>
> - **(a) The default path is unchanged:**
>   - `_seed_ends_config(row, False)` is the De Morgan equivalent of the old inline condition, with the same evaluation and short-circuit order (`float(value)` is reached under the same conditions, and missing keys fail the same way);
>   - in `evidence_run`, no keyword is passed and the `bad` expression is byte-for-byte the old one;
>   - `_completion(d4b=None)` returns the same dict with the same key order for sweeps 1 and 2;
>   - in `verify_evidence_completion`, D4 A checks keep their order, the new branch only runs if the key is present, and the recompute stays at the same point.
> - **(b) The enabling check:**
>   - `check_contingency` is called first in `evidence_run`, before provenance or mkdir (the test confirms nothing is written);
>   - the row is found through `release.author_rows` with an exact id match, `len(rows) == 1`, and must contain the run id `s2ev-20261119-a`, the rule and the STOP sha;
>   - a relative path cannot contain `..` (the first parts are fixed, there are exactly 4 parts, and the last starts with `C3_audit_EVIDENCE_`);
>   - verify re-derives the record, including `row_sha256`, and catches mismatches between environment and completion in both directions (probe);
>   - the row is absent from the worktree PLAN, from `9c2979a2` and from origin/main (count 0 in each).
> - **(c) E5 core rules:** 3 or more of 5 divergent seeds makes the proposal divergent per block; partial μ comes from the usable pairs; `delta_label` null and `soft_parameters` null for divergent; the rule_noop shape matches D4 A; the Student-t omission is documented. Timeouts and "run_command raised" are correctly STOPs. A NaN metric line can't be parsed by `_parse_metrics_from_log`, so exit 0 with metric None is divergence, which is right for the MLP nodes.
> - **(d) Other consumers:**
>   - `release_checks.sweep2_integrity` refuses anything but /4 (release_checks.py:60);
>   - the sweep-1 integrity check and `offline_eval.assemble` refuse a sweep-2 or d4b environment;
>   - partitions and receipts only come from the release step.
> - **Tests:** the 22 new tests pass. The report's 131 figure is exact (d4b + sweep2_audit + split_blocks + authorization + guards + release: "131 passed"). Also run: attestation_stop, other_boundaries, seed_isolation, release and test_c3_audit, 116 passed.
>
> ## Scratch
>
> Everything is in `/tmp/rev_d4b/_to_delete/`:
> - `scripts/builder_compat.py`: the builder-compatibility probe;
> - `scripts/test_rev_d4b_verify.py`: the verify and symlink probe;
> - `t/`: TMPDIR and pytest basetemp.
>
> Nothing was deleted.

## Round 2 (`03e643fb`)

> **NOT ACCEPTED** (round 2: `mac-s2-d4b-20261122` @ `03e643fb`, compared with `9c2979a2` and `d7d73bb8`)
>
> Ten of the eleven round-1 findings are fixed. One major problem remains: the narrowed divergence test still lets some infrastructure failures count as divergence, which the module docstring says it prevents.
>
> ## MAJOR
>
> **1. The non-finite word is searched across the whole log tail, so some infrastructure failures still become labels.**
> - Where: `r1/c3/audit_d4b.py:77` (`NONFINITE`), `:94-95` (`is_divergent`), `:111` (the 4,000-character `log_tail`).
> - What is wrong: an exit-1 run counts as divergent if `nan`, `inf`, `infinity`, `non-finite` or `not finite` appears anywhere in its last 4,000 characters. The worker writes stdout and then stderr, so the tail usually ends with tracebacks and warnings. The word can therefore come from:
>   - a traceback line quoting source code, such as `best = -np.inf` (very common in sklearn and numpy frames);
>   - an earlier warning that has nothing to do with the final error;
>   - a file path.
> - Probe (synthetic rows run through `X.is_divergent`):
>   - a traceback whose source line reads `best = -np.inf`, ending in `KeyError: 'x'`: True
>   - an openml failure (`FAILURE_CATEGORY=runtime_error`, `FAILURE_MESSAGE=MemoryError:`) after a warning that mentions NaN: True
>   - `FileNotFoundError: /data/nan/cache.parquet`: True
> - Failure scenario: a numpy allocation failure (OOM) or a `KeyError` in an MLP node prints a traceback through sklearn frames that quote `np.inf`. The seed counts as divergent instead of a STOP. If this happens on 3 of 5 candidate seeds, the proposal becomes "divergent" (u = −g).
> - Fix:
>   - search only the final exception line (the last `<Type>: message` line), or the `FAILURE_MESSAGE=` line on openml nodes;
>   - exclude memory and OS exception types (`MemoryError`, numpy's `_ArrayMemoryError`, `OSError` and its subclasses);
>   - add these three tails to `test_divergence_reading` as non-divergent.
>
> ## MINOR
>
> 2. **The scratch estimate doesn't cover the fresh node copies** (`r1/c3/audit.py`, the new block in `run_config` after the seed rule). Each divergent run keeps the used copy (`<node>.diverged_seed<N>`) and makes a new one, so scratch use goes beyond the independently estimated `required_scratch_bytes`. The resource monitor STOPs if scratch runs low, so this fails closed. Fix: mention it in the report's author-row section, or in the projection.
> 3. **Two wording errors in the report and docstring.**
>    - `release.evidence_tier` does not refuse /5. It classifies any `r1.c3_audit_completion/` schema as T0, which guards the directory; the refusal comes from `release_checks`.
>    - So `evidence_tier` does not need the "reviewed update" that the author-row section lists.
> 4. **A half-created directory can be left behind.** If the stopped `STOP.json` changes between the check and the copy (`stopped_bytes`, called after `out.mkdir`), the run raises and leaves an output directory with no `STOP.json` and no completion. It can't be used to enable anything. Fix: copy the bytes before `mkdir`, or write a STOP.
>
> ## Verified sound
>
> - **Round 1 #1 (builder shapes), fixed.**
>   - Label rows are now `audit` with `k_label` 3–5, or `divergent` with null values. Evaluation rows carry `divergent_seeds` and `k_evaluation` only when the row is not complete. Complete rows match D4 A's rows key for key.
>   - The test runs every case through the frozen builder's `_label_ok` and `_evaluation` and checks the preregistration's pin of the builder's sha256.
>   - Incumbent divergence is a STOP, so k = 2 can no longer happen, and the author-row section lists this rule.
>   - The frozen builder handles divergent label rows correctly: `fit_a2` leaves out rows with no soft label (gate_input_builder.py:296-304).
> - **Default path still unchanged.** Under D4 A, `run_config` adds no diagnostics and makes no fresh copy; the test with `continue_on_divergence` off confirms the rows are unchanged and it ends at the failure. `_seed_ends_config` and the D4 A branches of `evidence_run` and verify are as I accepted them in round 1.
> - **Round 1 #3 (verify untested), fixed.** There is a positive round trip, which also passes after the stopped directory is archived, and 9 refusal cases: completion-only, environment-only, row withdrawn, row text changed, STOP copy changed or missing, record changed, `stop_sha` changed, and runs re-labelled as exit 137. The release check now runs with the real verifier and refuses /5.
> - **Round 1 #8 and #9, fixed.**
>   - `recheck_contingency` checks the record's exact key set, refuses a symlinked or missing STOP copy, and re-derives the row and the STOP. The STOP copy is tied to the environment record by its sha256, and the environment is bound in the completion.
>   - A stopped audit that is itself a contingency audit is refused.
>   - A `D4B blocks:` STOP cannot enable anything later.
> - **Round 1 #6, fixed.** `_stopped_dir` refuses a symlink in any path component and an absolute path outside the paper root.
> - **Round 1 #5, fixed.** `sft_data.LabelBlockSource` refuses /5 and `d4b_contingency` in both load paths, which is tested.
> - **Round 1 #7, fixed.** `counts(labels, evaluations)` counts both blocks.
> - **Round 1 #10, fixed.** The fresh-copy behaviour is tested.
> - **Round 1 #11, fixed.** The CLI flag and the absolute-path and symlink cases are tested.
> - **Narrowing of divergence (the part of #2 that is fixed).** Exit 2, `invalid_config`, signals, 137, timeouts, worker exceptions and unreadable logs are all STOPs, which is tested.
> - **Tests:** 206 passed across `test_c3_sweep2_d4b`, `sweep2_audit`, all seven `evidence_*` files, `release` and `test_c3_audit`. The worktree stayed clean (`git status --short` gives 0 lines). I changed nothing under /tmp/pb and opened no label, evaluation or sealed file.
>
> ## Scratch
>
> Round-2 scratch is in `/tmp/rev_d4b/_to_delete/r2/`; the divergence probe is `scripts/tail_probe.py`. Round-1 scratch is still in `/tmp/rev_d4b/_to_delete/`. Nothing was deleted.

## Round 3 (`dfc4b46e`)

> **ACCEPTED** (round 3: `mac-s2-d4b-20261122` @ `dfc4b46e`, compared with `03e643fb`)
>
> All four round-2 findings are fixed. I have no blocking or major findings left.
>
> ## MINOR (no change needed)
>
> 1. **The author row should confirm the reading of divergence.**
>    - A `ValueError` or `RuntimeError` whose final message names nan or inf as a word is classified as divergence. That fits E5's "a non-finite loss".
>    - Every openml node puts a `SimpleImputer` in front of the model (benchmark.py:187-199 at harness 6adf385). So "Input contains NaN" can't come from missing values in the data. It points to non-finite model outputs.
>    - This reading is already in the report's author-row section for the author to confirm or amend.
>
> ## Verified sound
>
> - **Round 2 #1 is fixed.** `final_error` reads the last `FAILURE_MESSAGE=` line, or else the last Python exception line. The exception type must be in `DIVERGENT_EXCEPTIONS`, and the word must appear in the message.
>   - My three round-2 tails are now not divergent: the `KeyError` with an `np.inf` source line, the openml `MemoryError` after a NaN warning, and the `nan` path segment.
>   - These are also not divergent: `_ArrayMemoryError` (its type is not in the list), `nan.parquet`, and `np.inf` (the lookarounds exclude it).
>   - My extra probes were all classified correctly:
>     - "Solver produced non-finite parameter weights…": True
>     - "Input contains NaN." followed by a note line: True
>     - "got -inf": True
>     - "array=nan.": True
>   - `final_error` is tested directly, including that the `FAILURE_MESSAGE` line takes priority and that a line with no exception gives None.
>   - The rows built by the round-2 verify and evidence fixtures (`NAN_TAIL`) still count as divergent.
> - **Round 2 #2 is fixed.** The scratch note is in the docstring, in the report's "Scratch" section and in the author-row section.
> - **Round 2 #3 is fixed.** The `evidence_tier` wording is correct.
> - **Round 2 #4 is fixed.** `stopped_bytes` now runs before `out.mkdir` (audit.py, `evidence_run`). The test confirms that no output directory is left when the STOP changes after the check.
> - **The default D4 A path is unchanged.** `stopped_stop` stays None without the contingency, and the other D4 A code is untouched since round 2.
> - **Tests:**
>   - `test_c3_sweep2_d4b`: 75 tests collected.
>   - The targeted set (d4b, `sweep2_audit`, all seven `evidence_*` files, `release`, `test_c3_audit`): 219 passed.
>   - The worktree stayed clean (`git status --short` gives 0 lines). I changed nothing under /tmp/pb and opened no label, evaluation or sealed file.
>
> ## Scratch
>
> Round-3 scratch is in `/tmp/rev_d4b/_to_delete/r3/`. Earlier rounds are in `/tmp/rev_d4b/_to_delete/` (`r2`, `scripts`, `t`). Nothing was deleted.

---

Code-Commit: dfc4b46e547d9bd3b3840f929cab42a66e2ddfaf
Verdict: ACCEPTED

Accepted: the D4 option-B contingency at `dfc4b46e`, OFF by default and refused without its author row; the default D4 A path unchanged.
