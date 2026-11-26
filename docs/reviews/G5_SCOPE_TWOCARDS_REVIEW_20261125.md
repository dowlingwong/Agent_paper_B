Reviewed base: origin/main `912a7e027` (scope `git diff 912a7e02 <tip>`); accepted at `8b3633748` (code `7146197e`)

# Independent review record — G.5 before the launch: R1-T1-D21-SCOPE (a D21 non-qualifier is recorded, not STOPped) and R1-G5-AUDIT-TWO-CARDS (TASL-7 audit chunks under the leases, per-node cross-host PASS), G.5 draft revision 11

**Unit.** On `mac-g5-scope-twocards-20261125` (READY 104's tip merged with main 5d4f1b09 and 912a7e02): `sweep2/t1_tasl/g5_tasl.py`,
`g5_tasl_spec.json`, `g5_job.py`, `g5_assemble.py`, `g5_noise.py` (docstring), `g5_seal.py`, `t1_tasl_node.sh`; tests `test_t1_g5_tasl.py`,
`test_t1_g5_job.py`, `test_t1_g5_seal.py`, `test_t1_features.py` (fixture); the G.5 authorization draft revision 11 (`approved: false`), the T1
release rows draft (row texts unchanged) and the report `docs/r1/reports/g5_code_20261123/G5_SCOPE_TWOCARDS_20261125.md`. Authority:
R1-T1-D21-SCOPE, R1-G5-AUDIT-TWO-CARDS (amending G5-SLOT A); the queue of 25 Nov 2026 (12:00), items 2(a) and 2(b).

**Process.** One independent reviewer for all rounds, read-only, synthetic data only, no label, evaluation, sealed or secrets file opened,
scratch moved to its `_to_delete/`. Part (a) was acceptable from round 1. Round 1 found three majors in part (b): a claim for a node that cannot
run on TASL-7 deadlocked the wave; TASL-7 attempts could escape the GPU-hour meter and the seal; XC3-FAIL was enforced only as A. Round 2
found that a node STOPped under B after it had run could never be sealed (so the run could not be sealed), plus three minors. Round 3 accepted;
the reviewer ran the local copy of the xc3 note rules against the final xc3 code (`b14cb887`, READY 107) on 29 cases with no mismatch.

**Full suite** (author, default options, lightgbm absent, one run at a time): base `912a7e02` 58 failed, 3972 passed, 197 skipped, 3 errors;
code tip `7146197e` 58 failed, 4014 passed, 197 skipped, 3 errors; `FULLSUITE_TIP_SCOPE_TWOCARDS_R2_DEFAULT_FAILED.txt` equals the default base
list (61 entries, the standard list). An earlier round used pytest's `tmp_path_retention_policy=failed`, which adds one teardown error to base and
tip alike; those lists are kept beside the report and are superseded.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `e7ab0c36` | NOT ACCEPTED (M1–M3; m1–m8; n1–n6) |
| 2 | `f7c90620` | NOT ACCEPTED (new MAJOR N1; minors N2–N4) |
| 3 | `8b363374` | ACCEPTED |

**Open items for the author.** XC3-FAIL (A by default; B built behind the value the switch reads from the signed xc3 note and the PLAN row
R1-XC3-FAIL-READING on main); how the 425 GPU-h cap counts TASL-7 audit hours (counted, the conservative reading); the CUDA-IPC acceptance line
names TASL-2 only; R1-T1-NODE-EXPANSION candidates are not covered. Follow-up before the G.5 code freeze if xc3 is on main by then: replace the
local copy of the xc3 note rules with imports or a pinning test. The four `PENDING short cross-check: <node>` placeholders and the harness
`g5_commit` PENDING values stay.

## Round 1 (`e7ab0c36`)

> ## Round 1, `e7ab0c36` (scope `git diff 912a7e02 e7ab0c36`): NOT ACCEPTED
>
> 3 MAJOR, 8 minor, 6 nits; nothing BLOCKING. Part (a) D21 scope is correct and acceptable as is. Part (b) has three problems: a bad claim can deadlock a wave; TASL-7 attempts can escape the GPU-hour meter and the seal; XC3-FAIL can be signed B in the xc3 note while G.5 runs A.
>
> ### Verified
> - Tests one file at a time: test_t1_g5_tasl 135, test_t1_g5_job 42, test_t1_g5_seal 38, test_t1_features 30 (+1 skipped), test_t1_tasl_g1b 45, test_t1_tasl_crosscheck 30 passed.
> - Full-suite lists: base-2 and tip byte-identical; base-1 differs only by the retention-option teardown ERROR. Comparison sound; coordinator's default-option run pending.
> - Scope: gate.py, gate_input_builder.py, release.py, preregistration, g1b_crosscheck.py, g5_relcopy.py, trackg/, g1b_lib, g1b_tasl_join untouched; no `approved: true`; g5_noise docstring only.
> - The six xc2 verdicts and the host check record on main `912a7e02` match the spec sha256s; `check_crosshost_pass` passes the three TASL-7 nodes (both steps), refuses the four PENDING nodes and autoresearch.
> - §5 key-lines block equals a fresh render (55 lines, spec `eef8f5eb…`).
> - D21 scope: no remaining `qualifies_D21` gate; `noise_by_node` is `require_deterministic`; determinism test strict; cross-host gate structural; σ̂ is T0's `dataset.noise_table` rule; `check_usable` pre-existing (no new threshold); `d21` reaches build.json and the noise record, JSON-safe.
> - Leases: non-blocking flock on the server's own lease + `/health` + `check_no_foreign`; crash releases the flock; orphaned llama-server caught by `/health`/foreign check.
> - xc3 interface fields and paths match `mac-xc3-short-crosscheck-20261125b`. Autoresearch refused at the switch, `claim_chunk` and `worker_shim`.
> - Synthetic adversarial checks confirmed five gaps (below).
>
> ### MAJOR
> - **M1.** `claim_chunk` (`g5_job.py:900-943`) accepts a claim for a node that cannot run on TASL-7 (no cross-host PASS, placeholder `node_extra_env`, no host check, GPUH B), and claims are permanent: the wave's E5 chunk waits forever and every other claim is blocked (reproduced). Fix: check `S.check_crosshost_pass`, `S.tasl7_host_check`, placeholders and GPUH B in `claim_chunk`; add a reviewed `abandon-claim` (only with no registered complete attempt, with a reason, after registering TASL-7's access log), or state the resolution in the draft.
> - **M2.** TASL-7 attempts can escape the meter and the seal (`register_attempt` `g5_job.py:977-1036`; `seal_node` `g5_seal.py:317-351`; `seal_run` 354-372): registration does not require earlier attempts first; no check for open claims or post-seal registrations; `node_finished` lets a node seal with an open claim; no final access-log registration. Scenarios reproduced: an unregistered infra-STOP attempt's hours never reach STOP 9 and are never sealed; registration accepted after a node STOP. Fix: (a) attempt N = 1 + highest registered; (b) refuse registering into a closed claim; (c) `seal_node` refuses with an open claim on the node, `seal_run` with any open claim; (d) `seal_run` requires a final TASL-7 access-log registration; draft: "every TASL-7 attempt must be registered".
> - **M3.** XC3-FAIL decided in two places, only A enforced (`g5_tasl.py` `XC3_FAIL = "A"`); the xc3 note carries `xc3_fail: A|B`. Signing B there would leave G.5 failing open. Fix: the switch reads the signed xc3 note's `xc3_fail` (or the PLAN row) from main and STOPs affected nodes or the launch if not A, until B is built; or build B behind that switch; name the coupling in draft §2.10 and §11 20a.
>
> ### minor
> - m1. A second complete attempt registered after the claim closed is counted twice (fixed by M2(b)).
> - m2. `register_attempt` does not check `crosshost_pass` non-null nor re-check it on main.
> - m3. xc3 reader looser than the writer: `crosscheck_run_id` any string; sides' `run_id`s unbound; `label`/`complete` optional.
> - m4. TOCTOU: `claim_chunk` between TASL-2's `next_chunk` and `next_attempt`; two concurrent claims. Fix: flock `_remote/claims.lock`.
> - m5. `check_order_tasl7` double-counts registered TASL-7 hours; spurious STOP 9 late in the table.
> - m6. Mixed-host labels within a group and E5 rows not disclosed; say so in draft §2.10/§3 and the funnel disclosure.
> - m7. TASL-7's node wrapper log and refusals never sealed; register or disclose.
> - m8. Near-miss rule refuses a node if any file under docs/r1/reports contains `G1B_XC3_SHORT_VERDICT_<node>_`; restrict to `.json`.
>
> ### nit
> n1 houseprice `node_extra_env` placeholder: the xc3 spec has the value; n2 g5t7 `cpus`/`logdir` ignore TASL-7; n3 raw `FileNotFoundError` in `register_attempt`; n4 draft §11 "20a" before "20", ambiguous "that node" in release-rows draft; n5 §5 lead wording; n6 add an operator fetch to C16 or the schedule.
>
> ### Draft revision 11
> Accurate; P1 cites the host check; no result claimed; XC3-FAIL presented as an author decision; stale revision-10 text can wait.

## Round 2 (`f7c90620`)

> ## Round 2, `f7c90620` (code `f8da2c5b`): NOT ACCEPTED
>
> All round-1 findings are fixed and verified. The M3 fix (XC3-FAIL B) opens one new MAJOR; the local copy of the xc3 note rules diverges slightly from the xc3 branch.
>
> ### Verified
> - Tests one file at a time: test_t1_g5_tasl 138, test_t1_g5_job 50, test_t1_g5_seal 38, test_t1_features 30 (+1 skipped), test_t1_tasl_g1b 45, test_t1_tasl_crosscheck 30 passed. Default-option full-suite list byte-identical to the base list. Spec `a80b16e2…`; §5 equals a fresh render (55 lines). Scope unchanged; no `approved: true`.
> - Round-1 scenarios rerun: M1 claim without PASS refused; M2(a) out-of-order refused; M2(b)/m1 second complete attempt into a closed claim refused; M2(c) sealing with an open claim refused; M2(d) claim/abandon after finalize refused, `seal_run` needs finalize; m4 lock blocks `claim_chunk` (thread test) and covers `next_chunk`…`next_attempt`; m5, m7 present and tested.
> - Option B: skipped and xc2 nodes untouched; unreadable verdict or `verdict: FAIL` refuses; note A with row B, and two notes, STOP the short-check nodes.
> - Reader against the xc3 writer on `20261125c`: `label`, `complete`, `crosscheck_run_id`, side `run_id`s match; houseprice path equals the xc3 spec's `extra_env_additions`.
>
> ### NEW MAJOR
> - **N1.** A node stopped under B after it has run cannot be sealed, so the run cannot be sealed (`g5_tasl.py` `xc3_b_check`; `g5_seal.py` `node_finished`, `seal_node`, `seal_run`): the switch raises STOP 5 but writes nothing into the runs tree, `node_finished` stays None, `seal_node` refuses "has not ended", `seal_run --not-run` rejected because the node has a directory. Reproduced; blocks the T1 release for all nodes. Fix: write a node STOP record (e.g. `<run_id>/<node>/_switch_stop.json`, `stop_class` node, verdict path and sha256, rule XC3-FAIL B) read by `node_stopped`/`node_finished`, or have `node_finished` call `xc3_b_check`; update draft §4 and the release-rows sentence.
>
> ### minor
> - **N2.** The registration recheck on main can strand a completed TASL-7 attempt (main moves between run and registration → refused; only exit `abandon-claim`, so hours escape and data stays unsealed). Fix: compare with the claim's `crosshost_pass`; record the fresh main check for information, or register for accounting and mark for re-run.
> - **N3.** An abandoned claim can still run on TASL-7 (reproduced). Fix: `check_order_tasl7` refuses when a copied `_remote/abandoned/...` record is present; add the copy step to the abandon procedure (at minimum, state it in draft step 5).
> - **N4.** Local xc3 rules diverge from `20261125c`: (a) empty `skip_nodes` entry accepted by G.5, refused by xc3; (b) `xc3_cap` not checked; (c) PLAN row: G.5 looks for any `xc3_fail: X` mention, xc3 requires exactly one sentence `The xc3 note carries xc3_fail: ([AB])\.` (both-options row: G.5 STOP, xc3 B; missing/twice: G.5 B, xc3 STOP). Same: parser, case, missing `skip_nodes`, note path, `approved: true`, `run_id`/`xc_spec_sha256` binding. Fix: use xc3's sentence regex exactly once, refuse empty entries, check `xc3_cap`. View: duplication acceptable for launch if aligned now; replace by import, or add a pinning test, once xc3 is on main.
>
> ### nits
> Abandon/registration race outside `claims_lock` (harmless; move the check inside and lock registration); `xc3_reading` STOPs TASL-2 jobs of the four nodes even under A on two notes / unapproved note / unbound spec: say in the draft that xc3 must not commit a second note or change its spec during G.5; same-second timestamps in `check_remote_final` (covered by `_require_not_final`).
>
> ### Draft revision 11
> Accurate; only N1 (and N3 if fixed in code) needs wording.

## Round 3 (`8b363374`)

> ## Round 3, `8b363374` (code `7146197e`): ACCEPTED
>
> All four round-2 findings (N1–N4) and the nits are fixed and verified; no new BLOCKING, MAJOR or minor issue.
>
> - Tests one file at a time: test_t1_g5_tasl 140, test_t1_g5_job 51, test_t1_g5_seal 40, test_t1_features 30 (+1 skipped), test_t1_tasl_g1b 45, test_t1_tasl_crosscheck 30 passed. `FULLSUITE_TIP_SCOPE_TWOCARDS_R2_DEFAULT_FAILED.txt` byte-identical to the default base list. Spec unchanged; §5 equals a fresh render (55 lines, `a80b16e2…`). Scope unchanged; no `approved: true`.
> - **N1.** `write_switch_stop` writes `<run_id>/<node>/_switch_stop.json` (schema `g5_tasl_switch_stop/1`) only on TASL-2 launches, after the enable keys, only on a NodeStop from `xc3_b_check`; once, never overwritten; an unreadable verdict raises a plain Stop and writes nothing. Cannot be forged from TASL-7 (TASL-7 writes nothing; separate tree). With an open TASL-7 claim on the node: `node_finished` None, `seal_node` refuses, new claims and TASL-2 jobs refused, the TASL-7 attempt can still be registered (metered), then the node seals with the record copied into `_node` (reviewer's test). An in-flight TASL-2 attempt is untouched; `seal_node` waits for its job record. A first-job STOP is sealed with `seal-node`; draft §4 and the release-rows sentence separate the cases.
> - **N2.** Registration compares `crosshost_pass.records` with the claim's; the main check is information only (try/except).
> - **N3.** `check_order_tasl7` refuses a chunk whose abandon record was copied; draft step 5 says to copy it.
> - **Nits.** Abandon check inside `claims_lock`; `register_attempt` fully under the lock; draft states the xc3 constraint.
> - **N4.** xc3 changed only docs and lists between `55f23299` and `b14cb887`. `xc3_note_decisions` ≡ `short_decisions`, `xc3_row_option` ≡ `xc3_fail_row_option`, constants match, same parser. The reviewer ran 29 cases (author's 20 plus 9 adversarial) through both rule sets with `b14cb887`'s file loaded: 0 mismatches. The local reader is a subset of `check_xc_note` (P1–P4, `paper_commit`, `labels_read`), acceptable because the note must pass xc3's strict check to launch xc3. Duplication acceptable for the G.5 launch; replacing with imports once xc3 is on main is a good follow-up, not a launch condition.
> - Informational: a B STOP record outlives a later XC3-FAIL change (node stays stopped until an author row); the reader still matches the xc3 writer on `20261125c`.

---

Code-Commit: 7146197e
Verdict: ACCEPTED

Accepted 25 Nov 2026.
