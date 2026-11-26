Reviewed base: `9c2979a2` (published `main`); accepted at `6617d8cbbf47e5f513342092b09c6528c581ea79`, confirmed at `740c48f305be3f763008a1f74dff9bde48b43088`

# Independent review record — autoresearch_fixedtokens under its own G.1b spec: the spec support in g1b_tasl.py, the AR spec and freeze, the third-note draft and the TASL-2 host-check procedure

**Unit.** On `mac-g1b-ar-20261122`: the autoresearch-only spec kind in `sweep2/t1_tasl/g1b_tasl.py` (schema `g1b_tasl_ar_job/v1`, `validate_ar`,
`check_note_ar` / `check-note-ar`, `check_env_row`, its assembly and summary schemas), `sweep2/t1_tasl/g1b_tasl_ar_spec.json`, `sweep2/g1b/env/ar-cond7a.freeze.txt`,
`r1/tests/test_t1_tasl_g1b_ar.py`, `docs/r1/proposals/G1B_AR_T1_TASL_NOTE3_DRAFT_20261122.md` (approved: false; decision AR-ENV),
`docs/r1/reports/g1b_ar_20261122/` (unit report and the TASL-2 host-check procedure at harness `2d09f9a9`). Authority: R1-G1B-NOTE2-DECISIONS (NOTE2-AR A),
R1-T1-HOST-TASL, R1-T1-TASL-ENV, R1-TRACKG-AR-U2-TASL2, R1-G1B-CAP, R1-G1B-TIMEOUT; the queue of 22 Nov 2026 (01:22), item 2. The harness pin itself has its own
review record (`TRACKG_T1_AR_HARNESS_REVIEW_20261122.md`).

**Process.** One independent reviewer for all three rounds, read-only, no host access; scratch under `/tmp/rev_g1bar/` moved to its `_to_delete/`.
Round 1 found two majors (the draft could not pass its own check; the environment row only had to look like a row id) and ten minors; round 2
accepted with one minor (the procedure could pass as a host record); round 3 confirmed its fix and the harness-review citations.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `7d23d32c` | NOT ACCEPTED (M1, M2; minors 1–10) |
| 2 | `6617d8cb` | ACCEPTED (minor N1) |
| 3 | `740c48f3` | CONFIRMED |

**Open items.** Before the third note: the TASL-2 host check at `2d09f9a9` (the procedure; binding record committed by the lead, its sha256 into the spec, P2); the author's decision AR-ENV and its row (into `env_decision.authority`, `env_row`, P7; the row's line must name `ar-cond7a`); this review record and the harness review record on main (P3, P4); `paper.commit` = the merge; then `check-note-ar --draft`, signature, `check-note-ar`. Each TASL-2 launch runs from its own paper checkout equal outside `docs/` to its own `paper_commit`.

## Round 1 (`7d23d32c`)

> # Review of `mac-g1b-ar-20261122` @ `7d23d32c` against `main` `9c2979a2`
>
> ## Verdict: NOT ACCEPTED
>
> There are no BLOCKING findings and two MAJOR ones. Both are small to fix. The code fails closed in every place I attacked except the environment-row gate (M2). The seven-node path is unchanged.
>
> ## BLOCKING
>
> None.
>
> ## MAJOR
>
> **M1. The third-note draft cannot pass `check_note_ar`, even after every field it lists as open is filled.**
> - **Where:** `docs/r1/proposals/G1B_AR_T1_TASL_NOTE3_DRAFT_20261122.md:60` (`data: <base>/data/…`) and `:64` (`outputs: … <runs_root>/g1b-ar-…`).
> - **What is wrong:** `check_note_ar` reads every `key: value` line as a field. It refuses any field that matches `<[^>]*>` (`g1b_tasl.py:1110`). `<base>` and `<runs_root>` match.
> - **Failure scenario (reproduced):**
>   - I used a spec with its three TODO fields filled and copied the draft to `docs/r1/authorizations/g1b_ar_t1_tasl_20261123.md`.
>   - I filled `paper_commit`, `spec_sha256` and `env_row`, and set P2, P3, P4 and P7 to PASS with their citations.
>   - `check_note_ar(draft=True)` still stops with `note fields not filled (placeholder or PENDING): ['data', 'outputs']`.
>   - Once those two lines hold literal paths, it passes. The signing step would therefore fail on two lines the draft never flags as open.
> - **Why the tests miss it:** `test_the_shipped_draft_binds_the_ar_spec_and_is_not_signable_yet` only parses the draft. It never runs a completed copy through `check_note_ar`.
> - **Fix:**
>   - Write the literal paths: `/home/dowling/r1_tracks/t1_tasl/data/autoresearch_fixedtokens` and `/home/dowling/r1_tracks/t1_tasl/runs/g1b-ar-tasl-20261122-a/…`.
>   - Add a test that fills only the declared open fields of the shipped draft and asserts that `check_note_ar(draft=True)` passes.
>
> **M2. The environment-row gate checks only that the value looks like a row ID. It does not require a row that actually admits `ar-cond7a`.**
> - **Where:** `g1b_tasl.py:414-416` (`validate_ar`), `:1098-1103` (`check_note_ar`) and `:1211` (`launch`).
> - **What is wrong:** `env_decision.authority` only has to match `ROW_ID`. I confirmed that a filled spec with `env_decision.authority = "R1-T1-TASL-ENV"` (or `"R1-G1B-CAP"`) passes `validate_spec(launch=True)`. Those rows are already in `AR_PLAN_ROWS`, so `verify_launch_tasl` finds them on main, and `env_row`/P7 just have to repeat the same ID. The unit's own reasoning is that R1-T1-TASL-ENV names only torch312/jax312.
> - **Failure scenario:** the lead fills `env_decision.authority` with `R1-T1-TASL-ENV …`, which is an easy slip because that is `host_row`. The author signs, and the job launches with no PLAN row ever admitting `ar-cond7a`. This is exactly the gap that decision AR-ENV exists to close.
> - **Fix:**
>   - In `validate_ar` at launch, and in `check_note_ar`, refuse an env row that is in `AR_PLAN_ROWS`.
>   - Preferably also have `launch` (or `verify_launch_tasl`) check that the env row's PLAN line on `origin/main` mentions `ar-cond7a`.
>   - Add tests for both.
>
> ## MINOR
>
> 1. **The AR harness pin is not bound** (`g1b_tasl.py:379-432`).
>    - The `validate_ar` docstring says "the pins differ", but nothing checks it. `harness.commit = c025f89a…` is accepted (tested).
>    - The engine's committed-pin check would stop at run time, and the note binds the pin, so this does not open a hole.
>    - Fix: refuse `harness.commit == seven["harness"]["commit"]`. Optionally, require it to equal the PLAN-named `2d09f9a9…`.
> 2. **The shared cap ignores the spec's own cap** (`g1b_tasl.py:425`).
>    - The total is compared with `L.CAP_TOTAL_GPU_HOURS`, not `caps.max_total_gpu_hours`. A spec declaring 30 GPU-h passes with a G.1b total of 58.589.
>    - The test monkeypatches both values at once, so it cannot tell which one is enforced.
>    - Fix: compare with `min(caps.max_total_gpu_hours, L.CAP_TOTAL_GPU_HOURS)`.
> 3. **Only `harness_dir` is checked for separation from the seven-node checkout.**
>    - `base`, `data_root`, `runs_root`, `sealed_root` and the `env_python` paths are not.
>    - I set `base` inside `/home/dowling/r1_tracks/t1_tasl/harness` and it was accepted. `run_setup` would then create `harness/data` and `harness/hf` there, and every seven-node TASL-2 job would stop at `harness_checkout` on the untracked files. This needs a deliberately wrong spec.
>    - Fix: refuse any host path that is inside or above either checkout.
> 4. **Smaller spec checks:**
>    - `seven_node_spec.run_id` is informational and never compared; a stale value passes.
>    - `note_rule` is checked with `startswith`, so `R1-G1B-NOTE2-DECISIONSX` passes.
>    - The AR `run_id` is not checked against G.4's `g4-tasl-20261121-a`, which shares `runs_root`.
>    - `timeout_decision.basis = census_baseline_x3` is accepted, as it already is for the seven-node spec, although R1-G1B-TIMEOUT fixes slowest_x3 and P6 states 767.748 s.
> 5. **Procedure, CPU use while seven-node jobs run** (`TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md` §0/§4/§5).
>    - Data staging uses about 3 cores (tokenizer training). The checks and the supplementary pytest are also CPU-heavy.
>    - All of these may run while a seven-node G.1b job is live on cpus 0-7 or 8-15 (TASL-2 has 32 CPUs).
>    - Fix: `taskset -c 16-31` for every non-GPU step, or wait for idle.
> 6. **Procedure, conflicting lease rules.** §0 says a busy lease is a STOP, while "Order" says to wait for a seven-node job. Fix: state that a seven-node, cross-check or G.4 holder means wait, and anything else means STOP.
> 7. **Procedure, wording and robustness:**
>    - §6: say the four key lines go at column 0. `check_host_record` matches with `^host_check_`, and they are shown indented inside a list's code fence.
>    - §5 C7: "both checkouts clean" should say "the AR checkout clean except `nodes/autoresearch_fixedtokens/data`".
>    - §1: `git clone` from the READY 78 bundle fails if the bundle is incremental (prerequisite `c025f89a`). Prefer cloning from GitHub (as on 21 Nov), then fetching the bundle.
>    - §2, §3, §5: set `PYTHONDONTWRITEBYTECODE=1`, as the 21 Nov precheck did. Otherwise probes may write `__pycache__` into the Track P-tree venv. `__pycache__` is git-ignored and excluded from the frozen pin, so this is hygiene only.
> 8. **Operational point missing from the report and note.** After this merge, `verify_launch_tasl` requires each launch's non-docs tree to equal its own `paper.commit`. That means:
>    - the seven-node run must launch from a checkout matching `10fd3343`;
>    - the cross-check from `ea34b1ab`;
>    - G.4 from `02abb367`/`9c2979a2`;
>    - the AR job from its own commit.
>
>    Say that one paper checkout on TASL-2 cannot serve all of them, and that it must not be switched under a running or unsealed job.
> 9. **Draft wording:**
>    - Line 41 already says "independently reviewed". It should say "to be reviewed".
>    - AR-ENV says "plus the node's packages (tiktoken, rustbpe, pyarrow) installed". The smoke report shows that the install also changed numpy 2.4.4→2.5.4 and pyarrow 26.0.0→26.0.1.
>    - Option A should also say that the venv sits in the Track P tree, outside the T1 base, so a later Track P action could change it. The freeze check would then stop the table.
> 10. **Test gaps** (`r1/tests/test_t1_tasl_g1b_ar.py`):
>     - **:322-325:** the "host record at the old pin" test passes because of the sha256 mismatch. The pin comparison is never reached. Set the spec's sha to the stale report's sha.
>     - **:339:** the strict CLI case accepts any rc 2. Assert the reason.
>     - **:220-222:** the seven-node assemble refusal fires on receipt, run_id and spec-sha mismatches, not on spec kind.
>     - **No test for:**
>       - an AR assembly summarised with the seven-node spec;
>       - the env row being an already-required row (M2);
>       - harness pin equal to `c025f89a`;
>       - a spec cap below the shared total;
>       - a completed shipped draft passing `check_note_ar` (M1).
>
> ## Verified as sound
>
> - **Tests:** these pass with `-p no:cacheprovider`, and the counts match the report:
>   - `test_t1_tasl_g1b_ar` + `test_t1_tasl_g1b` + `test_t1_tasl_crosscheck` + `test_t1_tasl_g4`: 155 passed;
>   - `test_p3_split` + `htcondor/test_g1b_h200` + `test_g4_h200`: 180 passed;
>   - the new file collects 52 tests.
> - **Seven-node path (item 1):**
>   - The signed spec is sha256 `060aac91…`.
>   - Its `validate_spec(launch=True)` projection, and the cross-check derived specs for all six (node, host) pairs, are byte-identical between `9c2979a2` and `7d23d32c`. I compared them by importing both trees.
>   - The only behaviour changes are:
>     - `autoresearch_fixedtokens` is refused;
>     - `summarise` requires `g1b_tasl_assembly/1`, which `G.assemble`, and therefore the cross-check `assemble_gated`, still writes;
>     - `check_note` refuses an AR spec.
>   - The `launch` refactor keeps the same order and rows. `g4_tasl.py`, `g1b_note_dry_check.py` and `dry_run_node.py` use no changed function in a changed way. The wrapper needs no change.
> - **AR kind (item 2):**
>   - **Run_id:** equal or `<seven>-…` is refused.
>   - **Checkout:** a `harness_dir` that is equal, inside, above, or written with a trailing slash, `//` or `/./` is refused.
>   - **Environment:** exactly `ar-cond7a` at Python 3.12.15, with the freeze bound by sha256.
>   - **Host:** TASL-2 only.
>   - **Other refusals:** the hostname or GPU UUID equal to the seven-node spec's, lease `gpu0`, the census GPU model and ratio 1.0, and a cross-check hours value of NaN, `True`, 0 or 11.
>   - **Shared cap:** 28.227 + 28.262 + 2.1 = 58.589 (sensitivity 42.216 + 41.644 + 2.1 = 85.96).
>   - **Launch:** the env row is added to the PLAN rows, and only TASL-2's host record is checked.
>   - **Records:** the record, assembly and summary schemas are kept apart. `L.summarise` additionally binds `spec_json_sha256`, and e1_report needs no per-node metric direction.
> - **AR spec values (item 3):**
>   - At `3c6ce37a` (an ancestor of `origin/ops-tasl-20261116`): U2 result `8f872f2d…`, smoke report `8814eecc…`, data manifest `ab7186d2…` (13 manifest files), HF revision `915333b4…`.
>   - Census times: B1 218.951, B2 218.443, E1 219.565, E2 255.916, E3 217.516, E4 222.584. The timeout is 767.748 s, and the smoke runs s001–s003 are correctly excluded.
>   - The freeze `env_freeze_live.txt` = `env_freeze.txt` = committed `sweep2/g1b/env/ar-cond7a.freeze.txt`: sha256 `11def6ad…`, 122 lines, including torch 2.6.0+cu124 and three `git+https` packages.
>   - Pins recomputed at `2d09f9a9` in `/tmp/pb/wt/t1ar`: raw `5c1bdf3d…`, file `5bdce00a…`, committed pin `147f0d35…`, edits manifest `55f2666a…` (4 edits, bound to the raw sha).
>   - The projection and the 84.9 h deadline are correct. The errata ref `245fba8f` exists and is the commit the cross-check review accepted.
> - **Draft (item 4):**
>   - It reads `approved: false`. Its facts (pins, times, hashes, driver, freeze, projection, P1 citations) are correct, apart from M1 and the wording points in minor 9.
>   - AR-ENV is a fair write-up of A/B/C with a reasoned recommendation of A.
> - **Procedure (item 5):**
>   - It leaves the seven-node checkout, its runs and sealed trees, and the Track P archive `/home/dowling/r1_trackp/runs/p3a_operator_20261027` alone; it deletes nothing; it pushes nothing.
>   - The commands are right: the pin snippet matches `check_node_pins` and `load_node`; `prepare_data.py` re-checks and re-links an existing `--out`; the harness `.gitignore` covers `__pycache__` and `.pytest_cache`; `frozen_file_hashes` skips `__pycache__`.
>   - The four key lines match `check_host_record` and the layout of the 21 Nov record.
>
> ## Housekeeping
>
> I modified nothing under `/tmp/pb`; both worktrees show no new or changed files. My scratch is in `/tmp/rev_g1bar/_to_delete/`.

## Round 2 (`6617d8cb`)

> # Round 2 review: `mac-g1b-ar-20261122` @ `6617d8cb` (diff `7d23d32c..6617d8cb`)
>
> ## Verdict: ACCEPTED
>
> All round-1 findings are fixed: M1, M2 and minors 1–10. I found no BLOCKING or MAJOR issue in the revision. There is one new MINOR, which I recommend fixing before the experiment agent runs the procedure.
>
> ## BLOCKING
>
> None.
>
> ## MAJOR
>
> None.
>
> ## MINOR
>
> **N1. The procedure file now passes `check_host_record` as a host-check PASS record by itself.** This is new in round 2.
> - **Where:** `docs/r1/reports/g1b_ar_20261122/TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md`, §6.
> - **What is wrong:** the minor-7 fix put the four `host_check_*` lines at column 0 in the procedure itself.
> - **What I saw:** I pointed `isolation_host_check` at the procedure, with that file's own sha256 (`1df5cb9a…`), host `TASL-2` and pin `2d09f9a9…`. `check_host_record` returns success.
> - **Failure scenario:** the spec's `record` names the procedure instead of the binding record, and P2 cites it. The launch's host-check gate then passes with no host check ever run.
> - **How likely:** low. The lead and the author would both have to change a field that is not marked TODO.
> - **Fix, either of:**
>   - Show the lines in the procedure with a visible prefix (for example inside a `>` quote block) and say "remove the prefix in the record".
>   - Have `check_host_record` refuse a record that is not under `docs/r1/reports/trackg_g0_20261117/`, or whose name contains `PROCEDURE`.
>
>   Either way, add a test that the procedure file is refused.
>
> ## Round-1 findings: verified fixed
>
> - **M1:**
>   - The draft's `data:` and `outputs:` lines now hold literal paths.
>   - I filled only the declared open fields of the shipped draft. `check_note_ar(draft=True)` passes against a filled spec.
>   - The new test does the same thing, and passes.
> - **M2:**
>   - Every row already in `AR_PLAN_ROWS` is refused as the env row, both in `validate_ar` at launch and in `check_note_ar`. I tried R1-T1-TASL-ENV, R1-G1B-CAP, R1-TRACKG-AR-U2-TASL2 and R1-G1B-NOTE2-DECISIONS.
>   - `check_env_row` refuses a PLAN that is missing, a row line without `ar-cond7a`, and a duplicated row line. It accepts a single line that names `ar-cond7a`.
>   - On today's PLAN, the only row containing the text `ar-cond7a` is R1-TRACKG-AR-U2-TASL2. It contains it only inside a kit name, and it is already refused.
> - **Minor 1:** `harness.commit` must equal `2d09f9a9…` and must not be `c025f89a`. Another commit is refused. A placeholder is allowed only when not launching.
> - **Minor 2:** a spec cap of 30 or 40 now stops the run at a shared total of 58.589. The cap used is `min(spec cap, 100)`.
> - **Minor 3:** each of these is refused:
>   - base, runs root or interpreter inside either checkout;
>   - a sealed root above both checkouts;
>   - any path containing `..`.
>
>   Base itself correctly stays allowed to contain both checkouts.
> - **Minor 4:**
>   - A stale `seven_node_spec.run_id` is refused.
>   - `R1-G1B-NOTE2-DECISIONSX` and `host_row R1-T1-TASL-ENVX` are refused.
>   - A run_id outside `g1b-ar-`, including the G.4 id and a prefix of the seven-node id, is refused.
>   - A `census_baseline_x3` timeout basis is refused.
> - **Minors 5–9:** the procedure and draft text changes are as listed in the dispositions table:
>   - `taskset -c 16-31` for non-GPU steps;
>   - the wait-or-STOP lease rule;
>   - C7 allows the AR checkout's data link;
>   - clone from GitHub, then fetch from the bundle;
>   - `PYTHONDONTWRITEBYTECODE=1` throughout;
>   - the per-launch paper checkouts (`10fd3343`, `ea34b1ab`, `02abb367`, and the AR note's own commit);
>   - the draft wording.
>
>   I could not check the procedure's claim that the READY 78 bundle is incremental with prerequisite `c025f89a`, because READY 78 is not on record in the repo. The `git bundle verify` step covers it.
> - **Minor 10:**
>   - The old-pin launch test now fails on the pin line, with the sha256 deliberately matching.
>   - The CLI test asserts the reason.
>   - The kind refusal is tested both ways.
>   - The env-row, pin, own-cap and completed-draft tests are added.
>
> ## Also re-verified
>
> - **Tests:** 350 passed across all four `test_t1_tasl_*` files, `test_p3_split`, `htcondor/test_g1b_h200` and `test_g4_h200`. The new file collects 67 tests.
> - **Seven-node path:**
>   - The signed spec is still `060aac91…`. The AR spec and the freeze are unchanged in this round.
>   - The seven-node `validate_spec(launch=True)` projection, and all six cross-check derived specs, are still byte-identical to `9c2979a2`.
>
> ## Housekeeping
>
> - I modified nothing under `/tmp/pb`; the worktree is clean.
> - Scratch is in `/tmp/rev_g1bar/_to_delete/`, round 2 under `round2/`. The one exception to "delete nothing": I removed my own empty, freshly created `/tmp/rev_g1bar/r2` folder after moving its contents into `_to_delete/round2/`.

## Round 3 (`740c48f3`)

> # Confirmation round: `mac-g1b-ar-20261122` @ `740c48f3` (diff `6617d8cb..740c48f3`)
>
> ## Verdict: CONFIRMED
>
> N1 is fixed, and the harness-review citations added to the note draft are accurate. Nothing new is open, and no BLOCKING, MAJOR or MINOR findings remain.
>
> **N1, the procedure passing as a host record.**
> - In §6 of the procedure, the four key lines now sit behind `> `, and the text tells the reader to remove the prefix in the record.
> - No line starting with `host_check_` is left at column 0, either in the procedure or in the report or draft.
> - The new test `test_the_procedure_file_cannot_pass_as_a_host_check_record` passes. It points `check_host_record` at the procedure, with the procedure's own sha256, and gets a refusal.
>
> **The harness review record** (`docs/r1/reviews/TRACKG_T1_AR_HARNESS_REVIEW_20261122.md`):
> - It is ACCEPTED at `2d09f9a9` in one round, with minors 1–4. Its open items match what was carried into the draft.
>
> **The new citations in the note draft**, checked against git in the harness worktree:
> - **The code-unit report** `docs/r1/reports/trackg_g0_20261117/TRACKG_AR_COND7A_CODE_UNIT_20261120.md`:
>   - it is blob `ee7a0c53` at `7330338`;
>   - inside the pin `2d09f9a9` it is blob `79aeecf0`, the version-1 copy.
> - **The earlier edit manifest:** at `c025f89a` it hashes to sha256 `02e05d06…`, and the review records the old raw value as `5f48b86f…`.
> - **The node line:** `node_spec_sha256` is the raw value `5c1bdf3d…` that the engine checks, and `5bdce00a…` is labelled as the spec file's sha256. Both match what I recomputed in round 1.
> - **P3** cites the review record and stays PENDING until that record is on main. That is correct: `check_note_ar` needs PASS plus `docs/r1/reviews/` plus the pin, and this field carries both of the latter.
> - **The `harness_report:` line** contains no `<…>` placeholder, so it does not trip `check_note_ar`. The completed-draft test still passes.
>
> **Scope of the change.** This round touches no code under `sweep2/`. The spec, the freeze and `g1b_tasl.py` are unchanged from round 2, which I accepted.
>
> **Tests.**
> - The four `test_t1_tasl_*` files: 171 passed.
> - `test_p3_split` + `htcondor/test_g1b_h200` + `test_g4_h200`: 180 passed.
>
> **Housekeeping.** I modified nothing under `/tmp/pb`; the worktree is clean. This round's scratch is in `/tmp/rev_g1bar/_to_delete/round3/`, beside rounds 1 and 2.

---

Code-Commit: 740c48f305be3f763008a1f74dff9bde48b43088
Verdict: ACCEPTED

Accepted: the autoresearch-only G.1b spec support, the AR spec and freeze at `740c48f3`; the third note remains a draft (approved: false); the seven-node spec's validation and run unchanged.
