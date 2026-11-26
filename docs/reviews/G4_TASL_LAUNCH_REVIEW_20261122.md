Reviewed base: `985dd45d` (published `main`); accepted at `874e70f6f69a9334b1e9ceaeb671c6779e2a7d4f`

# Independent review record — G.4 on the TASL pair: the launch-binding fix (serve and run-node) and the G.4 note draft

**Unit.** On `mac-g4-auth-20261121`: `sweep2/t1_tasl/g4_tasl.py` (`launch` and new `serve_launch` behind the note, both keys,
the import-source check and `g1b_tasl.verify_launch_tasl`; `check_note` binding run_id and harness commit, refusing `<…>`
placeholders and requiring P4's reviews on main; `serve` writing nothing before the lease and its checks), `r1/tests/test_t1_tasl_g4.py`,
the G.4 block of `sweep2/t1_tasl/g1b_tasl_authorization.template.md`, `docs/r1/proposals/G4_T1_TASL_NOTE_DRAFT_20261121.md`
(approved: false; author decisions G4-LB, G4-ORDER, G4-NODE3) and `docs/r1/reports/g4_auth_20261121/G4_AUTH_20261121.md`.
Authority: R1-T1-HOST-TASL, R1-T1-TASL-ENV, R1-TRACKG-G3-EARLY, R1-G1B-TIMEOUT, R1-G1B-TASL-DECISIONS (LB A, for G.1b; its use for G.4 is
decision G4-LB); the queue of 21 Nov 2026 (22:44), item 3.

**Process.** One independent reviewer for all four rounds, read-only, synthetic data only, scratch under `/tmp/rev_g4/` moved to its
`_to_delete/`. Round 1 found a blocking defect (a refused `serve` left the run directory behind, so no later `serve` could start) and
three majors (untagged placeholders passed, the stray-code guard did not cover `sweep2/g4`, LB A presented as decided for G.4); round 2
accepted with four minors (fixed in `9ee5309a`); round 3 confirmed them with one wording correction (fixed in `874e70f6`); round 4
confirmed that.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `ded091a0` | NOT ACCEPTED (B1; M1–M3; minors 1–11) |
| 2 | `9ac5b726` | ACCEPTED (minors 1–5) |
| 3 | `9ee5309a` | CONFIRMED (one wording correction) |
| 4 | `874e70f6` | CONFIRMED |

**Open items.** Author decisions G4-LB (A: LB A applied to G.4), G4-ORDER (B: lease order only), G4-NODE3 (A: mlgym_breakout_minatar). Before signature: the spec's `paper.commit` set to the launch commit; the note filled (`paper_commit`, `spec_sha256`, P3 per G4-ORDER, P4 citing this review) and published with it; the jax312 re-check on TASL-2. Left open (round-1 minor 10): the binding result and the note sha256 are returned but not written into the job or server record. G.1b launches stay on exactly `985dd45d` (or its docs-only child `dbdbd2b6`).

## Round 1 (`ded091a0`)

> **NOT ACCEPTED**
>
> Unit: `mac-g4-auth-20261121` @ `ded091a06ec58c119b024b2ac09cc6365a8bab75` against base `985dd45d`, worktree `/tmp/pb/wt/g4auth`. The worktree is unchanged: `git status` is empty and HEAD is still ded091a0.
>
> What the unit gets right: both `serve` and `run-node` are now behind the note, both keys and `verify_launch_tasl`, and the G.4 gate can be met with the same launch sequence G.1b used. It is not accepted because of one blocking defect in the `serve` path the unit now gates and recommends (B1), and three gaps in the gate itself (M1–M3).
>
> ## BLOCKING
>
> **B1. A refused `serve` can never be retried.** Where: `sweep2/t1_tasl/g4_tasl.py:338-343`, reached through `serve_launch` at :758 and the CLI at :815.
> - **What is wrong:** `serve` runs `run_dir.mkdir(parents=True, exist_ok=False)` before it takes the lease and before any of its checks (foreign process, binary, manifest, ldd, GGUF, build). Any STOP in that path leaves `<proposer.run_dir>/<run_id>/` behind. After that, every later `serve` call fails with `FileExistsError`. That is not a `Stop`, so `main` (:835) does not catch it: the CLI crashes with a traceback and exit 1.
> - **Reproduced in scratch:** with HOME, run_dir and hostname redirected, and the lease held by another fd, the first call gave "STOP: the GPU lease ... is held by another job". After releasing the lease, the second call gave `FileExistsError [Errno 17] File exists: '.../proposer/g4-tasl-20261121-a'`.
> - **Failure scenario:** under the recommended G4-ORDER B, the server starts "before or between" TASL-7's cross-check and G.1b jobs. One busy lease, or one foreign process (for example the Track X exam server still on the card), makes the run unservable. The rules ("nothing is deleted or silently retried") forbid removing the directory. Recovery then needs a new run_id, which means a new spec sha256, a new note and a new review cycle.
> - **Fix:** make the directory and write records only after the lease and all checks pass. Write refusals under `<run_id>/_refusals/` and serve under `attempt-N` (as `run_node_job` does with `G.write_refusal` / `G.next_attempt`), or at minimum turn `FileExistsError` into a `Stop`. Add a test: a busy lease, then a second `serve` that gets past the mkdir.
>
> ## MAJOR
>
> **M1. `check_note` accepts placeholders that are not tagged `<FILL`.**
> - **Where:**
>   - code: `g4_tasl.py:718-729`
>   - draft: `docs/r1/proposals/G4_T1_TASL_NOTE_DRAFT_20261121.md:89`
>   - template: `sweep2/t1_tasl/g1b_tasl_authorization.template.md:37-39`
> - **What is wrong:** only `<FILL` is refused, and the cite checks are plain substring checks. Untagged placeholders therefore pass:
>   - the draft's P4 still holds `docs/r1/reviews/<the G.4 launch-binding review>.md`, with no `<FILL` tag;
>   - the template's P2 holds `<autoresearch_fixedtokens | mlgym_breakout_minatar>`;
>   - the template's P3 holds `<docs/r1/authorizations/g1b_t1_tasl_<date>.md ...>`, which contains `g1b_t1_tasl_`;
>   - the template's P4 holds `docs/r1/reviews/<...>.md`.
> - **Reproduced:** I filled only approved, paper_commit, spec_sha256 and P3 in the draft. `check_note(..., spec=SPEC)` passed with P4 unfilled. The template's P3 placeholder also passed.
> - **Why the tests miss it:** the dry check (`r1/tests/test_t1_tasl_g4.py`, `test_note_draft_parses_as_check_note_reads_it`) fills P4 itself.
> - **Report claim it contradicts:** `G4_AUTH_20261121.md:26` says "an unfilled template cannot pass".
> - **Failure scenario:** the author signs with P4 left as the placeholder. The gate passes without any G.4 launch-binding review being cited.
> - **Fix:**
>   - refuse any key-field value that matches `<[^>]*>`, or tag every placeholder `<FILL`;
>   - optionally require that P4's `docs/r1/reviews/...md` path exists on origin/main;
>   - add a test where P4 is left unfilled.
>
> **M2. The stray-code guard does not cover `sweep2/g4`, which `g4_tasl.py` puts first on `sys.path`.**
> - **Where:** `g4_tasl.py:63-64`; `g1b_tasl.py:949` (`SYS_PATH_DIRS = ('sweep2/t1_tasl', 'sweep2/g1b')`).
> - **What is wrong:**
>   - `verify_launch_tasl` scans ignored files only in the G.1b sys.path directories.
>   - `g4_tasl.py` inserts `sweep2/g4` at `sys.path[0]`, ahead of `sweep2/t1_tasl`.
>   - `.gitignore:21` (`*.py[cod]`) ignores a sourceless `sweep2/g4/g1b_tasl.pyc` (confirmed with `git check-ignore -v`).
> - **Reproduced:** in a scratch copy of sweep2/, a planted `sweep2/g4/g1b_tasl.pyc` was imported by `g4_tasl.py` in place of the reviewed `g1b_tasl.py`, along with its `verify_launch_tasl`. The guard the G.1b review asked for therefore does not hold for G.4.
> - **Fix:** give `verify_launch_tasl` a `sys_path_dirs=` keyword that defaults to `SYS_PATH_DIRS`, so G.1b behaviour does not change. Pass `("sweep2/t1_tasl", "sweep2/g4", "sweep2/g1b", "sweep2")` from `g4_tasl._binding`. Alternatively, assert `Path(G.__file__)` after import. Add a test.
>
> **M3. Using LB A for G.4 is presented as already decided, but the row covers G.1b only.**
> - **Where:**
>   - `G4_AUTH_20261121.md:18`
>   - draft :17 and :73
>   - `g4_tasl.py:30` and :743
> - **What is wrong:** R1-G1B-TASL-DECISIONS (PLAN.md:1370) reads "G.1b on the TASL pair ...: LB A (the TASL-only launch binding `verify_launch_tasl` ...)". No PLAN row or author decision extends that binding to G.4. The draft does not list it under "Author decisions".
> - **Failure scenario:** the author signs the G.4 note thinking the binding was decided earlier. The authority trail for G.4's launch binding then rests on a row whose scope does not include G.4.
> - **Fix:** add an explicit author decision (for example G4-LB, applying LB A to G.4 serve and run-node), or a note line or P-line naming it, or amend the PLAN row.
>
> ## MINOR
>
> 1. **The code docstrings describe P3 as if G4-ORDER A were already chosen.** Where: `g4_tasl.py:28-29` ("P3 citing the signed G.1b note(s) whose TASL-7 jobs are sealed") and :703-704. The draft recommends B (no sealing), and the code only checks that P3 contains the substring `g1b_t1_tasl_`. Fix: word both docstrings neutrally, as "P3 per G4-ORDER".
>
> 2. **Merging this unit changes how G.1b must be launched, and nothing says so.** G.1b code is unchanged (`g1b_tasl.py` is not in the diff, its template block is untouched, and the G.1b tests pass). But:
>    - `git diff --stat 10fd3343 ded091a0 -- . ':(exclude)docs/' ':(exclude,literal)sweep2/t1_tasl/g1b_tasl_spec.json'` shows 3 code files. Once this merges, any G.1b launch from a fresh main stops with "differs from the paper commit".
>    - R1-G1B-TASL-DECISIONS XC A says the second G.1b note keeps paper_commit `10fd3343`. Those launches must therefore come from a checkout at or before `985dd45d` (the diff 10fd3343..985dd45d outside docs/ is empty), with the second note placed as an untracked file under docs/.
>    - Draft :73 says only "a checkout separate from the G.1b launch checkout".
>    - Fix: state the G.1b checkout rule in the report and in the operator steps.
>
> 3. **G4-ORDER framing.**
>    - B's cost leaves out the B1 risk.
>    - It does not say that two of the three pilot nodes (`mlab_cifar10`, `mlgym_breakout_minatar`) are TASL-7 G.1b nodes, so under B their noise floors come after the pilot. The claim that this does not matter is supported: `pilot_g4.py` imports only noise_floor functions, and `g4_lib` reads no G.1b output.
>    - It does not cite R1-TRACKG-G3-EARLY's "G.1b and G.4 start on these six now", which supports B.
>    - A's statement that the slack is "likely spent" is not quantified.
>
> 4. **G4-NODE3 framing.**
>    - Option A states no cost: the pilot would measure no autoresearch-suite node.
>    - The reason "C1–C5 only partly applied" cites a cross-check report that is not on main: commit `3a9a0a20` on `mac-g1b-xc-20261121`.
>    - The cond7a claim is correct: `7330338` is not an ancestor of `c025f89a`.
>
> 5. **The draft's "spec:" line (:70) calls `d47d1008` "a placeholder".** It is a real merge commit, and `validate --launch` accepts it. Call it "the stale pre-unit commit".
>
> 6. **The draft's STOP list (:93, :102) claims checks the code does not make.**
>    - "driver other than above": `G.gpu_check` (`g1b_tasl.py:355-365`) records the driver but never compares it.
>    - "GPU-hours consumed passing 20 GPU-h": no consumption meter exists; only the projection is checked.
>    - The G.1b note has the same wording. Fix: enforce both, or reword them as checks the operator makes.
>
> 7. **One "Before signature" item is already done.** `G4_AUTH_20261121.md:60` lists "jax312 is installed on TASL-2" as pending. `TASL2_T1_PRECHECK_20261121.md` §2.3 (line 66) and item 5 (line 110) already record it as PASS. Call it a re-check.
>
> 8. **Draft :13/:16 ("launch from a published checkout of that commit") is ambiguous.** The paper commit itself cannot hold the signed spec. Say "a published checkout at or after the commit that publishes the note and the spec, whose code equals paper_commit".
>
> 9. **Test gaps.**
>    - The binding stubs return `{}`, so no test shows that the key refusal comes before the binding in `serve_launch` or `launch`.
>    - No test shows that `serve_launch` refuses a spec that fails `validate_spec(launch=True)`.
>    - No test covers untagged placeholders (M1), the `serve` retry (B1) or `sys_path_dirs` (M2).
>
> 10. **The binding result is not saved.** For `run-node`, the CLI prints only `summary`. For `serve`, it prints only after the server exits. Neither the job record nor the server record holds the note sha or the binding's head/main. This matches G.1b, but it is worth adding `launch` and `note_sha256` to the records.
>
> 11. **P1's reasoning about untested CUDA IPC is copied from G.1b** (draft :86, "no pilot node uses cuda_share or cuda_open"). G.1b ran only declared edits; in G.4 the LLM writes `train.py` freely, and it can import the frozen `ar_isolated.py`. Restate the reasoning for model-written edits, for example that the frozen parent never calls `cuda_share`, or have the author accept the risk.
>
> ## Verified sound
> - **Tests:** `test_t1_tasl_g4.py` and `test_t1_tasl_g1b.py` give 72 passed, as the report says.
> - **Projection:** `g4_tasl.py validate` and `validate --launch` both return ok, run_id `g4-tasl-20261121-a`. Per node: mlab_cifar10 2.864, mlgym_fmnist 3.636, mlgym_breakout_minatar 4.577; total 11.077 GPU-h. Spans 1.432 + 1.818 + 2.289 ≈ 5.5 h; 180 proposals; cap 20. All match draft :77 and :81.
> - **Spec sha256:** `fd5a14b51463d5658dc1833b1e6805f5b4241078ec3fa813a9a14df833ba1b6b` is the same at 985dd45d and ded091a0. The unit does not change the spec.
> - **Draft values against spec and main:**
>   - GPU UUIDs `GPU-4d623e76-…0d94` and `GPU-ab72fb4a-…abb1`, the hosts, cpus 0-7 and the leases;
>   - binary `b70f4882…7d8b`, build `0.7.0-dev (build 1, commit 620d222)`, manifest `a29c667f…e170` (evidence in the TASL7_T1_PRECHECK captures);
>   - GGUF `2959c1b0…1b75`, URL `tasl-7.tail119748.ts.net:8095`;
>   - node and env shas; harness `c025f89aeafc2199bf3487b4bcaa16678273c702`;
>   - drivers as in R1-T1-TASL-ENV;
>   - host check `681011b2…b6b6d`, which equals the file on main and shows `host_check_*` TASL-2 / c025f89a / 1-7 PASS / PASS.
>   - The review files cited in P1 and P4 exist on main.
> - **Gate coverage and order:** both `serve` and `run-node` are bound to the note, run_id, harness_commit, both keys and `verify_launch_tasl` with `PLAN_ROWS`. `g1b_lib.verify_launch` is no longer used. The order is validate → note → keys → (host record) → binding → lease/runner, and the Python gate has no side effect before a refusal (apart from B1, and the wrapper's log, which predates this unit).
> - **Satisfiability:** the gate can be met with the G.1b sequence, because the exclusion uses the given spec's path and all four PLAN rows are on main in the `| ROW |` form.
> - **CLI paths:** only `serve` and `run-node` launch anything, and `t1_tasl_node.sh g4` calls `run-node`. The other subcommands do not launch, and `dry_run_node.py` is G.1b-only.
> - **G.1b unchanged:** `g1b_tasl.py` and the G.1b template block are unchanged.
>
> ## Scratch
> Everything is in `/tmp/rev_g4/_to_delete/`:
> - `scripts/p4_hole.py` (the M1 reproduction)
> - `scripts/serve_retry.py` (the B1 reproduction)
> - `demo/` (the M2 shadowing copy)
> - `x/`, `home/`, `t/`
>
> Nothing was deleted, and nothing in `/tmp/pb` was modified.

## Round 2 (`9ac5b726`)

> **ACCEPTED**
>
> Round 2 reviewed: `mac-g4-auth-20261121` @ `9ac5b726eb598b1f22796acf52c3f35f504bdbbf`, diff `ded091a0..9ac5b726`, in `/tmp/pb/wt/g4auth`. The worktree is unchanged (`git status` is empty, HEAD = 9ac5b726). All four round-1 findings (B1, M1, M2, M3) are fixed, and I re-ran each round-1 reproduction against the new code. The five MINOR items below are left; none blocks.
>
> ## BLOCKING
> None.
>
> ## MAJOR
> None.
>
> ## MINOR
>
> 1. **The G.1b checkout rule is stated wrongly.** Where: `docs/r1/proposals/G4_T1_TASL_NOTE_DRAFT_20261121.md:28-29` and :106 (the `launch:` line); `docs/r1/reports/g4_auth_20261121/G4_AUTH_20261121.md:82-84`.
>    - **What is wrong:**
>      - "At or before `985dd45d`" is wrong. Commits before 985dd45d hold the `-a` G.1b spec: at 10fd3343 its sha256 is `2f0bdd70…`, while the note binds `060aac91…`. So `check_note` stops on any of them.
>      - "From the merge on, a fresh main is no longer code-equal" is already untrue. Local origin/main is `adeccc29`, and its `7219a57a` changes `sweep2/s2_c5_authorization.template.md`, which is outside docs/.
>      - So the only commit G.1b can launch from is exactly `985dd45d`.
>    - **Failure scenario:** an operator follows the text and picks an earlier commit, or the current main. The launch STOPs, so nothing unsafe happens, but time is lost.
>    - **Fix:** write "exactly `985dd45d` (the only published commit that holds the signed G.1b spec and whose code equals `10fd3343`; main already differs outside docs/ from `7219a57a` on)".
>
> 2. **The binding checks imports after it has already run the imported code.** Where: `sweep2/t1_tasl/g4_tasl.py:801`.
>    - **What is wrong:** `{**G.verify_launch_tasl(...), "imports": check_import_sources(repo)}` evaluates left to right. A shadowed `verify_launch_tasl` therefore runs before the shadow is detected. The docstring at :798 says the reverse ("after the import-source check").
>    - **Failure scenario:** a stray module's `verify_launch_tasl` runs, which only means git commands, and then the import check STOPs.
>    - **Fix:** run `imports = check_import_sources(repo)` first, then the binding.
>
> 3. **`serve` writes a refusal only for `Stop`.** Where: `g4_tasl.py:406-408`.
>    - **What is wrong:** under the lease, other exceptions are not caught, for example `FileNotFoundError` from `sha` or `manifest` on a missing path, or `subprocess.TimeoutExpired` from `smi`. They write no refusal and leave the CLI with a traceback and exit 1.
>    - **Reproduced:** an `smi` that raises `FileNotFoundError` gave a non-Stop exception, and `_refusals` held only the earlier busy-lease refusal.
>    - **Still OK:** no `server-*` directory is left behind, so a retry still works.
>    - **Fix:** catch `Exception`, write the refusal, and raise it again as a `Stop`, as `run_node_job` does at :529-534.
>
> 4. **P1 gets the CUDA IPC roles backwards.** Where: draft :119.
>    - **What is wrong:** in `ar_isolated.py` at c025f89a, `cuda_share` is the side that shares a tensor (the parent; `cuda_share` at :615) and `cuda_open` is the worker side (:626). So "no CUDA IPC handle is ever accepted by a parent" has it the wrong way round.
>    - **The claim itself is right:** no frozen file of the three pilot nodes other than `ar_isolated.py` references either function (`git grep` at c025f89a).
>    - **Fix:** write "no frozen parent ever exports a tensor with `cuda_share`, so a worker has no parent handle to open".
>
> 5. **Information only: another branch edits the G.4 run-node wrapper.** `mac-g1b-xc-20261121` @ `c1d270e7` changes `sweep2/t1_tasl/t1_tasl_node.sh`. Whichever of the two units merges second moves main's code away from the other's `paper_commit`. Each launch then has to keep to its own checkout, as the draft already says for G.4. The G.4-ORDER A figure (cross-check about 2.1 GPU-h) is supported by `G1B_CROSSCHECK_20261121.md:70` at c1d270e7, which is not on main.
>
> ## Verified sound
> - **Tests:** `test_t1_tasl_g4.py` and `test_t1_tasl_g1b.py` give 73 passed, as the report says.
> - **Spec and projection:** `validate` gives total 11.077 GPU-h. The spec sha256 is still `fd5a14b51463d5658dc1833b1e6805f5b4241078ec3fa813a9a14df833ba1b6b`. `g1b_tasl.py`, both specs and `t1_tasl_node.sh` are unchanged since 985dd45d.
> - **B1:**
>   - `serve` creates nothing before the lease and the checks.
>   - Reproduced with the lease held: STOP, with only `_refusals/` written (no `server-*`). The test then starts `server-1` and `server-2`.
>   - `check_server_record` and `seal` work with the new `server-N` layout, which adds only the `server_dir` key.
> - **M1:**
>   - The draft's unfilled P4 is refused: `STOP: note fields not filled (a <...> placeholder): ['P4']`.
>   - A P4 naming a review that is not on origin/main is refused: `STOP: P4 must name review files on origin/main (missing: [...])`.
>   - `launch` and `serve_launch` pass `read_main`.
>   - The template's P2–P4 placeholders are now refused too.
> - **M2:**
>   - A real sourceless `sweep2/g4/g1b_tasl.pyc`, compiled from the reviewed source, is caught: `STOP: module g1b_tasl was imported from .../sweep2/g4/g1b_tasl.pyc, not the reviewed sweep2/t1_tasl/g1b_tasl.py`.
>   - With the script's own import order, the only local modules first imported after `sweep2/g4` joins `sys.path` are the four the check covers.
>   - G.1b's guard is unchanged.
> - **M3:** G4-LB is framed fairly, with options and a recommendation. The `launch:` line, the docstrings and the report all name it.
> - **Gate order:** `serve_launch` and `launch` check the keys before the binding, and both paths are tested. `serve_launch` refuses a spec that fails `validate_spec(launch=True)`.
> - **Earlier minors:**
>   - Minor 1 (docstrings): both are now neutral.
>   - Minors 3–4: G4-ORDER and G4-NODE3 now state benefit, cost, results order and risk. The A path is quantified, using the 14.202 TASL-7 GPU wall-hours from the signed G.1b note.
>   - Minors 5–8: the stale-commit wording, the operator checks for the driver and consumed GPU-hours, the jax312 re-check and the launch-checkout wording are fixed.
>   - Minor 10 is disclosed as left open.
>   - The draft has no remaining `<…>` in any field except the intended `<FILL` lines and P4, which is refused.
>
> ## Scratch
> Everything is in `/tmp/rev_g4/_to_delete/`. Round 2 is in `r2/`: `recheck.py`, `newmods.py`, `src/`, `x/`, `home/`, `t/`. The round-1 `demo/` copy was refreshed with the new `g4_tasl.py`. Nothing was deleted, and nothing in `/tmp/pb` was modified.

## Round 3 (`9ee5309a`)

> **CONFIRMED**, with one wording correction that does not block.
>
> I reviewed the diff `9ac5b726..9ee5309a` on `mac-g4-auth-20261121`. HEAD is `9ee5309ac3cef8e4623d24eeda038ef3f4404b5c` and the worktree is clean. `test_t1_tasl_g4.py` plus `test_t1_tasl_g1b.py` give 73 passed. This commit does not touch `g1b_tasl.py` or either spec.
>
> All four round-2 fixes are correct:
>
> 1. **G.1b checkout.** "Exactly 985dd45d" is in the draft (the checkout paragraph and the `launch:` line) and in the report. The reasons given are right: earlier commits hold the `-a` spec `2f0bdd70…`, and main differs outside `docs/` through `sweep2/s2_c5_authorization.template.md`. The note about the cross-check unit's `t1_tasl_node.sh` change covers my old item 5.
> 2. **Import check order.** In `g4_tasl.py:807-809`, `bind` now runs `check_import_sources(repo)` before `verify_launch_tasl`, as the docstring says.
> 3. **`serve` failures.** In `g4_tasl.py:410-415`, any exception other than `Stop` before a server starts is written as a refusal and raised again as "STOP: the proposer server could not be started: <type>: …". Two details are right:
>    - `Stop` is still caught first by the earlier `except` clause.
>    - Once `server_dir` is set, the exception is passed on unchanged, so nothing tries to record a refusal against a started server.
>    - The test checks it: an `smi` that raises `FileNotFoundError` gives 3 refusals and still only 2 `server-*` directories.
> 4. **P1 wording.** P1 now has the roles the right way round: `cuda_share` is the sharing (parent) side and `cuda_open` the worker side. This matches `ar_isolated.py` at `c025f89a`.
>
> **The wording correction.** Where: `docs/r1/proposals/G4_T1_TASL_NOTE_DRAFT_20261121.md` (the "The G.1b checkout" paragraph) and `docs/r1/reports/g4_auth_20261121/G4_AUTH_20261121.md` (the same section).
> - **What is wrong:** both say `985dd45d` is "the only published commit" that holds the signed G.1b spec with code equal to `10fd3343`. That is not quite true. `dbdbd2b6` is a published docs-only child of `985dd45d`: its G.1b spec sha256 starts `060aac91`, and its diff from `10fd3343` outside `docs/` and the spec is empty. The difference on main actually arrives at merge `adeccc29`, which brings in `7219a57a` from a side branch.
> - **This came from me:** my round-2 suggested text said "the only published commit".
> - **No effect on what operators do:** launching from exactly `985dd45d` is still valid and safe.
> - **Suggested fix:** write "`985dd45d` (or the docs-only `dbdbd2b6`); main differs outside `docs/` from merge `adeccc29` on". Alternatively, keep the instruction and drop the word "only".
>
> Scratch: I added nothing new in this round except pytest temp files under `/tmp/rev_g4/_to_delete/r2/t`. All scratch remains in `/tmp/rev_g4/_to_delete/`. Nothing was deleted, and nothing in `/tmp/pb` was modified.

## Round 4 (`874e70f6`)

> CONFIRMED: commit 874e70f6f69a9334b1e9ceaeb671c6779e2a7d4f changes only the two "The G.1b checkout" paragraphs (draft and report), and they now name `985dd45d` or its docs-only child `dbdbd2b6`, no longer say "only published commit", and say main differs outside `docs/` from merge `adeccc29` (bringing in `7219a57a`); this matches what I checked in git last round, the worktree is clean, nothing in `/tmp/pb` was modified, and I wrote no new scratch.

---

Code-Commit: 874e70f6f69a9334b1e9ceaeb671c6779e2a7d4f
Verdict: ACCEPTED

Accepted: the G.4 launch binding (serve and run-node) and `serve`'s refusal handling at `874e70f6`; the G.4 note remains a draft (approved: false).
