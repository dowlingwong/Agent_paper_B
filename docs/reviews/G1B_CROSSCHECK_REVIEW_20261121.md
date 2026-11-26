Reviewed base: `985dd45d` (published `main`), harness `c025f89a`, `ops-tasl-20261116` `dc0c559e`; accepted at paper `5daee7320cb61629058e950032e6eb8d197a1964`, harness `2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe`, errata `245fba8f45a8f4ffd1ec5665f5fefb2a1fa44069`

# Independent review record — the G.1b cross-host check (R1-T1-TASL-ENV), its gated assembly, the cross-check note and the second G.1b note drafts, the autoresearch harness basis and the U2 errata

**Unit.** Three branches:
- paper `mac-g1b-xc-20261121`: `sweep2/t1_tasl/g1b_crosscheck.py` (derived specs, the default-part job, `compare --mode xc|preassembly`,
  `check-note2 [--draft]`, the gated `assemble` and `summarise`), the cross-check spec, the `xc` kind of `t1_tasl_node.sh`,
  `r1/tests/test_t1_tasl_crosscheck.py`, the drafts `G1B_XC_NOTE_DRAFT_20261121.md` and `G1B_T1_TASL_NOTE2_DRAFT_20261121.md`
  (approved: false) and the report `docs/r1/reports/g1b_crosscheck_20261121/G1B_CROSSCHECK_20261121.md`;
- harness `mac-trackg-t1-ar-20261121`: `c025f89a` plus the autoresearch option-A kit (`eb14ed61`) and the port check's declared
  earlier-master allowance keyed to the seven T1 nodes;
- `mac-ar-u2-text-20261121` over `ops-tasl-20261116`: the errata to the U2 result (`8f872f2d…`, not edited because main binds it).
Authority: R1-T1-TASL-ENV, R1-G1B-TASL-DECISIONS (XC A; AR as changed by the author), the signed G.1b note; the queue of
21 Nov 2026 (22:44), item 2.

**Process.** One independent reviewer for all four rounds, read-only, synthetic data only, scratch under `/tmp/rev_xc/` moved to its
`_to_delete/`. Round 1 found two blocking defects (no way to start the job in the delegated scope; the assembly gate XC A assigns to
the unit missing) and five majors (compare not binding the attempts, P7 claiming PASS before any run, the re-measure remedy not
executable under one spec sha, the harness basis failing seven port checks, C1–C5 only partly applied); round 2 accepted the harness
and left one major each on the paper code (check-note2 could not run before signature) and the errata (the smoke-report median);
round 3 accepted all three with optional minors (fixed in `5daee732` and `245fba8f`); round 4 confirmed them.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `3a9a0a20 / eb14ed61` | NOT ACCEPTED (B1, B2; M1–M5; minors 1–9) |
| 2 | `c1d270e7 / fb3ad64f / 0e5972b6` | NOT ACCEPTED (paper: 1 major; harness: accepted; errata: 1 major) |
| 3 | `2e96bdf6 / 2d09f9a9 / ce19452b` | ACCEPTED (optional minors) |
| 4 | `5daee732 / 245fba8f` | CONFIRMED (cite this record) |

**Open items.** Author decisions NOTE2-AR (A: TASL-7 nodes under note 2, autoresearch under a third note), XC-REMEASURE (A: decide if a cross_host_mismatch occurs), XC-NONDET (A: decide if it occurs). Before the TASL-7 nodes: the cross-check note signed with the launch commit; six default-part jobs; three step-1 verdicts committed; note 2's P7 completed, `check-note2 --draft` recorded, signed, strict `check-note2` recorded. Assembly only through `g1b_crosscheck.py assemble`, summary through `g1b_crosscheck.py summarise`. Autoresearch: the harness commit `2d09f9a9` needs its own review before an autoresearch spec pins it; C3/C4 (executed and reviewed unit bytes not preserved) stay open. The gate record is a procedural guard, not tamper-proof (round 3).

## Round 1 (`3a9a0a20 / eb14ed61`)

> **NOT ACCEPTED**
>
> I reviewed `/tmp/pb/wt/g1bxc` (diff `985dd45d..3a9a0a20`) and the harness worktree `/tmp/pb/wt/t1ar` (`eb14ed61`). I changed nothing. The targeted tests pass: `test_t1_tasl_crosscheck.py` and `test_t1_tasl_g1b.py`, 67 passed. In the harness, I ran only the port `test_static` tests: 7 failed, 1 passed. My scratch files are in `/tmp/rev_xc/_to_delete/`.
>
> ## BLOCKING
>
> **B1. There is no way to start the cross-check job inside the delegated scope.**
> - Where: `sweep2/t1_tasl/t1_tasl_node.sh:13-28` and `sweep2/t1_tasl/g1b_crosscheck.py:270-303`.
> - The wrapper only knows `g1b` (which calls `g1b_tasl.py`) and `g4`. It calls `<script> cpus` and `<script> logdir` and passes `run-node SPEC --node --note`.
> - `g1b_crosscheck.py` has no `cpus` or `logdir` subcommand, and its `run-node` needs `--host`.
> - Started directly instead, `preflight` refuses: `scope_cgroup` and `check_affinity` both stop it. Even if an operator worked around that, the job would have no node log under `<runs_root>/<xc run id>-<host>/_logs`, so `seal` would bind no log.
> - So the docstring's "same lease, delegated scope, preflight" cannot actually be run.
> - Fix:
>   - Add an `xc` kind to the wrapper (`SCRIPT=g1b_crosscheck.py`, `ARGS=(run-node XC --node N --host H --note NOTE [--enable])`).
>   - Add `cpus` and `logdir` subcommands with `--host` to `g1b_crosscheck.py`. They should derive the spec and return `G.node_cpus` and `<runs_root>/<run_id>-<host>/_logs`.
>   - Add a wrapper test like `test_t1_tasl_g1b.py:581-604`.
>
> **B2. The assembly gate that decision XC A assigns to this unit is missing.**
> - XC A (`docs/r1/reports/g1b_tasl_note_20261121/G1B_TASL_NOTE_20261121.md:114-116`) and the signed note's P7 (`docs/r1/authorizations/g1b_t1_tasl_20261121.md:50`) both say: "the crosscheck unit must make its PASS record a required input to `assemble` for the TASL-7 nodes, run from a checkout that carries that check, with the same spec file."
> - The report instead says "`assemble` at `10fd3343` does not run this comparison, so it is a recorded step" (`G1B_CROSSCHECK_20261121.md:53-57,113`). That constraint is false. `assemble` is not bound to any launch commit and only checks the spec sha, so a checkout at M with the signed spec file can carry the gate.
> - Fix: add a gated assembly command to `g1b_crosscheck.py`, for example `assemble`. It takes the signed G.1b spec, the seven sealed attempts and three committed step-2 verdict files. For each TASL-7 node it checks:
>   - the verdict is PASS;
>   - the verdict's TASL-7 `job_record_sha256` equals the sealed attempt being assembled;
>   - that side's `run_id` is `g1b-tasl-20261121-b` and its `spec_sha256` is `060aac91…`;
>   - the TASL-2 side's `run_id` is `<xc>-TASL-2`.
>
>   Then it calls `G.assemble`. Add tests, and update report §6 and the second note's P7.
>
> ## MAJOR
>
> **M1. `compare` does not check which attempts it is comparing** (`g1b_crosscheck.py:163-221`). Synthetic probes confirmed each of these:
> - Any run ids and any spec shas give PASS. Nothing ties step 1 to the cross-check runs, or step 2 to the G.1b TASL-7 attempt.
> - A `SHA256SUMS` that omits `out.tar` is accepted, so `out.tar` goes unverified. The receipt binds only `job_record`.
> - If both sides lack the same config (c4), the result is PASS with `complete: true` and 8 rows.
> - Rows naming another node give PASS.
> - The receipt's host and attempt are not checked, and the harness is compared side to side, not against the pin.
> - Fix:
>   - Give `compare` a mode. In xc mode the run ids must be `<xc>-TASL-7` and `<xc>-TASL-2`, with spec shas recomputed from the committed derived specs. In pre-assembly mode the TASL-7 side must be the G.1b run id with the signed spec sha.
>   - Require `SHA256SUMS` to list exactly `out.tar` and `job_record.json`.
>   - Check the receipt's host and attempt, the row `node`, configs equal to c0..cN (N from the spec), and the harness against the pin.
>
> **M2. The second note's P7 claims PASS before any run** (`G1B_T1_TASL_NOTE2_DRAFT_20261121.md`, P7).
> - It says "ran … and PASSED … (verdicts <FILL…>)".
> - `check_note` accepts the signed copy with the `<FILL>` still unfilled; `test_t1_tasl_crosscheck.py:279-281` shows exactly this.
> - The TASL-7 launch code (`10fd3343`) only checks the PASS string, so the gate rests entirely on the text.
> - Fix: draft P7 as `PENDING` with a template. Add a `check-note2` command to `g1b_crosscheck.py` that checks P7 cites three verdict files on `origin/main` (sha256, PASS, the three nodes, the run ids) and refuses `<FILL`. Run it and record the output before signature, and test it.
>
> **M3. The rule's STOP remedy cannot be carried out under one spec sha.**
> - Re-measuring a TASL-7 node on TASL-2 needs a spec that puts that node on TASL-2, which means a different sha.
> - `G.assemble` (`g1b_tasl.py:822-831`) requires `receipt.host == node.host` and a single `spec_sha256`, so the re-measured node cannot join the seven-node table.
> - The report (:55) and P7 present the remedy as a simple step.
> - Fix: say so, and settle it in advance. Either the B2 gated assembler accepts a note-bound re-measure spec for named nodes, or the author decides.
>
> **M4. Harness `eb14ed61` is not yet a correct basis.**
> - `node_lib/ar_isolated.py` is now `3ba34c67…`, while the seven other nodes' copies stay `37d99ab0…`. At `c025f89a` they were equal.
> - `tests/trackg/port_support.py:199` (`check_isolated`, master equality) therefore fails for all seven nodes: `test_port_mlgym` ×4 and `test_port_mlagentbench` ×3. Autoresearch passes.
> - Runtime is unaffected: `node_lib` is used only by the sandbox probe (`isolation.py:351-369`), and the change is a docstring plus `torch.cuda.init()` in the unused `cuda_open`.
> - Syncing the seven copies would change their frozen pins, and with them the signed spec's `committed_pin_sha256`.
> - Verified correct: the autoresearch code at `eb14ed61` equals `7330338`, and the other nodes' files are unchanged.
> - Fix: change the harness test, reviewed (for example, compare each copy against the master version the node pins, or keep an allow-list). Add this as a blocker in the readiness table at report :67.
>
> **M5. U2 conditions C1–C5 are only partly applied** in the U2 result on `ops-tasl-20261116` (sha `8f872f2d…`). The report lists what was added and leaves out what is still open:
> - **C4, median:** "B1/B2 median 218.7935 s" is wrong. The B1/B2 median is 218.697; 218.7935 is the median of the 8 executed runs.
> - **C4, wall time:** "1,791.0 s (29:49)" is still in the table.
> - **C1:** the result says the executed unit "with TASL-2 adaptations" is preserved as `_unit.md` (`b83d9159`). That file actually targets Ada, `torch312` 3.12.16, the Ada data root, the Paper A gate and ≥40 GiB, and the result's own revision note says it is byte-identical to the Ada unit. The adaptations are only listed in the result's prose.
> - **C3/C4:** the result itself lists open residuals. It still says `R1-TRACKG-AR-U2-TASL2` "reaches main after the sweep-2 launch", but that row is now on main (PLAN :1342).
> - **Stale text:** "T1 labels run on H200" appears twice, contrary to R1-T1-HOST-TASL.
> - **Smoke report:** the cited `8814eecc` still carries the m6–m9 errors (median 218.951, "16.6 KB", 161,531,825 B, the `slowdown.stderr` wording). They are corrected only as errata in the U2 text.
> - **Applied:** the 20,000 MiB floor, the parent peak 6,560.3 MB, the cross-host label, the no-evidence statement, and the s001 and bundle bytes (in the U2 text). The C5 sha pair is unchanged, there is no CUDA-IPC claim, and the one-smoke rule holds.
> - Fix: make these text fixes on that branch, get a short re-review, and list them as open in the report.
>
> ## MINOR
>
> 1. **Second-note draft has stale copied lines.** "nodes:" says autoresearch is "not in this run … decision AR" (the author has since changed AR). P10 carries the first note's "22:37 CET" signature, and "scope:" uses the past tense. The draft as written assumes option A; label it so, or update it.
> 2. **NOTE2-AR framing is fair but incomplete.** It does not mention two things:
>    - an autoresearch-only spec means a separate `assemble`/`summarise`, because `L.summarise` requires every spec node;
>    - TASL-2 needs a second harness checkout at the new pin (`harness_checkout` requires HEAD equal to the pin, and `harness_dir` is shared with the four `c025f89a` nodes).
>
>    Add both to the readiness list.
> 3. **The verdict does not separate non-determinism from a cross-host mismatch.** `on_stop` always says "re-measured on TASL-2", so a non-deterministic TASL-7 node would get a second draw. Add a reason field.
> 4. **Tar handling** (`g1b_crosscheck.py:177-182`): `lstrip("./")` strips a character set; an absolute member name is read via `Path(tmp)/abs`, i.e. outside tmp; with duplicate members compare takes the first and `assemble` the last; tarfile errors are not turned into Stop. Require the exact unique name `out/default/runs.jsonl` and read the path that was actually extracted.
> 5. **Projection is understated.** The cross-check note says "about 1 GPU-h". By the spec's own accounting it is about 2.1 GPU-h: 0.58 h of runs plus 6 × 900 s of setup. The job record's `projection` and `deadline_s` also use the full 460 runs.
> 6. **XLA_FLAGS:** Breakout on TASL-2 runs without TASL-7's `XLA_FLAGS`. Disclose this in the cross-check note, which currently says "nothing else changes".
> 7. **`run_xc` patching** (`:155-160`) is safe for the single-threaded CLI: `run_node_job` reads `L.PARTS` (`g1b_tasl.py:708`) and `L.merge_parts` (`:746`) at call time, and `finally` restores both. It is not thread-safe, and restoration after a Stop is untested. Add a re-entrancy guard and a test.
> 8. **Tests do not cover everything claimed.** The report says "unsealed" attempts are refused, but no test removes `SEAL_RECEIPT.json`. Receipt mismatch is untested. The real `verify_launch_tasl` with the cross-check spec is untested (an edit to the cross-check spec allowed; any change to the G.1b spec or code after M refused). The "nothing else changes" test checks only nodes, harness and envs.
> 9. **Separate checkouts.** Each host will use two launch commits (L for the cross-check, `985dd45d` for G.1b). Recommend a separate checkout per launch commit.
>
> ## Verified sound
>
> - The derived specs change only `run_id`, the node's host, TASL-2's `jax312`, and an added `crosscheck` key; `paper` changes at launch.
> - The `load_xc` refusals work.
> - The launch sequence works:
>   - With paper commit M and the cross-check spec excluded, `verify_launch_tasl` passes at the launch commit and refuses at today's value.
>   - `985dd45d` is code-equal to `10fd3343` (diff rc 0) and is published, so TASL-7 can launch from it with the second note copied in as an untracked docs file.
>   - `assemble` accepts all seven nodes with one spec sha.
> - The second note carries the first note's binding.
> - The report's autoresearch blockers are correct: `validate_spec` rules, the harness binding in `check_host_record`, and the env/data layout.
> - All autoresearch values match the captures:
>   - census times B1 218.951, B2 218.443, E1–E4 219.565 / 255.916 / 217.516 / 222.584;
>   - timeout 767.748;
>   - node spec `5bdce00a`, edits manifest `55f2666a`, pin `147f0d35`, data manifest `ab7186d2`;
>   - freeze `11def6ad` (122 lines), Python 3.12.15;
>   - projection 28.2 / 42.2 GPU-h. The seven-node total is 56.49, which rounds to 56.5, not 56.4.
>
> All findings come from the files and branches named in the task; nothing here comes from memory.

## Round 2 (`c1d270e7 / fb3ad64f / 0e5972b6`)

> **NOT ACCEPTED** (round 2). Of the three commits, the harness commit is accepted; the paper commit and the errata each have one MAJOR finding left. Both fixes are small.
>
> What I checked, all read-only:
> - **Paper repo:** I reviewed `3a9a0a20..c1d270e7`. The targeted tests pass: `test_t1_tasl_crosscheck.py` and `test_t1_tasl_g1b.py`, 74 passed.
> - **Harness:** I reviewed `eb14ed61..fb3ad64f` and ran the port `test_static` tests plus `test_port_node_lib` with `PYTHONPATH=src`: 9 passed.
> - **Errata:** I checked `0e5972b6` against the result `8f872f2d`, the smoke report `8814eecc` and the captures.
>
> All worktrees are clean. My scratch is in `/tmp/rev_xc/_to_delete/`.
>
> ## 1. Paper commit `c1d270e7` — NOT ACCEPTED
>
> The round-1 BLOCKING and MAJOR findings are resolved:
> - **B1, resolved.** `t1_tasl_node.sh` now has the `xc` kind: `--host` goes to the `cpus`/`logdir` queries and to `run-node`, an unknown host is refused, and the log lands in the derived run's `_logs` (so `seal` binds it). Under `set -u`, `XHOST` is only read for `xc`. The `g1b` kind still passes its tests.
> - **B2, resolved.** `assemble_gated` recomputes the preassembly comparison from the attempts given and requires `_verdict_core` to equal the committed step-2 PASS. That binds both job-record shas, the run ids, the spec shas, the attempts and the rows. It then calls `G.assemble` with the signed sha, and refuses an xc-mode verdict or one for other attempts (tested).
> - **M1, resolved.**
>   - `expected_sides` recomputes the derived-spec sha in xc mode and uses the G.1b run id and signed sha for TASL-7 in preassembly mode.
>   - `SHA256SUMS` must list exactly the two files, and the receipt binds host, attempt and the directory name.
>   - Every row must be of the node, configs must be exactly c0..cN, and the harness must be the pin.
>   - The tar must hold one unique regular member, read through `extractfile`; tar errors become Stop.
>   - Each STOP now carries a reason.
> - **M3, resolved.** XC-REMEASURE is stated and framed fairly.
> - **Minors 1–9, resolved.** Also verified: the run_xc re-entrancy guard and restoration after a Stop, the real `verify_launch_tasl` test, and the corrected 56.5 GPU-h figure.
>
> **MAJOR — the documented order for `check-note2` cannot be followed.**
> - Where: `sweep2/t1_tasl/g1b_crosscheck.py:387-412`, report §5 (`G1B_CROSSCHECK_20261121.md:74-75`, and :21), and the note2 draft header ("its output is recorded before signature").
> - `check_note2` calls `G.check_note`, which first requires the note to be byte-identical on `origin/main` and then requires `approved: true` (`g1b_tasl.py:895-909`). The CLI has no way to override that.
> - So `check-note2` can only pass after the note is signed and published. If it fails then, a signed note with P7 PASS is already on main, and the TASL-7 launch code at `10fd3343` checks only the P7 string. The tests pass only because they inject `on_main=yes` and use an approved note.
> - Fix:
>   - Add `check-note2 --draft`, which skips the on-main check and accepts `approved: false` but runs every other check. Record its output before signature.
>   - Keep strict mode as a second recorded step after publication and before any TASL-7 launch.
>   - Update report §5, the docstring and the note2 header to match, and add a test that runs the CLI on the unsigned draft.
>
> **MINOR**
> 1. **Placeholders.** `check_note2` refuses `<FILL` but not the template's own `<date>`, `<path>` and `<sha256>` (in the note2 P7 template). Cited verdict paths and shas are enforced, but a leftover `g1b_xc_t1_tasl_<date>.md` would pass. Fix: refuse any `<…>` placeholder in P7, or check that the cited cross-check note exists on main.
> 2. **What `crosscheck_gate.json` binds.** It is written after `G.assemble` (`:450-452`) and does not record the `ASSEMBLY.json` or `runs.jsonl` sha256. Nothing at summarise time requires the gate, and `g1b_tasl.py summarise` still works without it. Fix: add those shas to the gate record. Optionally add a gated `summarise` that refuses without a matching gate.
> 3. **Checkout for `assemble`.** Report step 7 says to run it "from a checkout carrying this unit". It must be at or after the launch commit L, where the cross-check spec's `paper.commit` is M. At M itself the recomputed derived sha differs, and the gate refuses. That is fail-closed, so it only needs stating.
> 4. **A non-deterministic TASL-7 node blocks the whole table.** Such a node (G.1b `stop_class: node`) gets a step-2 STOP with reason `nondeterministic`. `assemble_gated` then refuses the entire seven-node table, although `G.assemble` itself supports node-STOP attempts. Fix: say this in the report next to XC-REMEASURE, as an author decision.
> 5. **Missing sums file.** `_sealed_rows` (`:197`) raises a raw `FileNotFoundError`, not a Stop, when `SHA256SUMS` is missing. This is fail-closed; for consistency, convert it to a Stop.
>
> ## 2. Harness commit `fb3ad64f` — ACCEPTED
>
> - `node_lib_copy_ok` accepts either the current master or the sha listed in `NODE_LIB_EARLIER`. That sha is `37d99ab0…`, which I confirmed is the master at `c025f89a` and the seven nodes' copies.
> - `autoresearch_fixedtokens` must carry the current master. The new test covers the master, the earlier master, the AR node refusing the earlier master, and an undeclared edit.
> - The change touches tests only. At runtime, `node_lib` is used only by the sandbox probe, and the seven nodes' files and pins are unchanged.
>
> **MINOR**
> - The allowance is global: any node other than `autoresearch_fixedtokens` may carry `37d99ab0…`, including a future node. Fix: key `NODE_LIB_EARLIER` to the seven named nodes.
> - The new test needs the `c025f89a` object in the clone (`git show`), so a shallow clone would fail it.
>
> ## 3. Errata `0e5972b6` — NOT ACCEPTED
>
> These items are correct:
> - the three bindings of `8f872f2d` (each found on `origin/main`);
> - the row being on main (PLAN §10);
> - the T1 table running on the TASL pair, as R1-T1-HOST-TASL;
> - C1: `b83d9159` really is the Ada-targeted unit;
> - the B1/B2 median of 218.697 s;
> - 1,791.0 s = 29 min 51 s, and 29:49 = `time -v`'s 1,789.26 s;
> - `s001` = 166,300 B;
> - the empty stderr (`slowdown.stderr.txt` is 0 B);
> - the honest "still open" C3/C4 residual.
>
> **MAJOR — the median correction for the smoke report is wrong.**
> - Where: errata, smoke-report section, first bullet.
> - The smoke report's "median 218.951 s" is the median of the 8 executed runs, next to "mean 223.547 s" (smoke report :127 and :166). The captures confirm this: `slowdown.json` has `median_executed_run_seconds` 218.951 over 8 records, with a mean of 223.547.
> - 218.951 is the upper middle of those 8 values. The true median is 218.7935, which is review m6.
> - The errata instead calls it "B1 alone" and swaps in the B1/B2 median of 218.697, a different quantity.
> - Fix: "median of the 8 executed runs is 218.7935 s; 218.951 s is the upper-middle value (`vals[len//2]`)".
>
> **MINOR**
> - **Bundle bytes.** The errata repeats "161,531,825 B is the Mac bundle/packaging size". Review m8 found that figure not reproducible: content is 152,751,278 B and the live `du -sb` is 161,534,003 B. Fix: write "not reproducible from the bundle; content 152,751,278 B; apparent size 161,534,003 B".
> - **stderr evidence.** The stderr bullet should say that `slowdown.stderr.txt` is 0 B, and that the false STOP is evidenced only by `RESULT_STATUS.initial_false_stop.txt` and `DONE.initial_false_stop`.
>
> Nothing in this report comes from memory.

## Round 3 (`2e96bdf6 / 2d09f9a9 / ce19452b`)

> **ACCEPTED** (round 3). All three commits are accepted, and none has a BLOCKING or MAJOR finding left. The remaining minor points are optional polish.
>
> What I checked, all read-only:
> - **Paper:** I reviewed `c1d270e7..2e96bdf6`. The targeted tests pass: `test_t1_tasl_crosscheck.py` and `test_t1_tasl_g1b.py`, 75 passed.
> - **Harness:** I reviewed `fb3ad64f..2d09f9a9`. The port `test_static` tests and `test_port_node_lib` pass with `PYTHONPATH=src`: 9 passed.
> - **Errata:** I reviewed `0e5972b6..ce19452b` against the smoke report and the captures on `ops-tasl-20261116`.
>
> All worktrees are clean. My scratch is in `/tmp/rev_xc/_to_delete/`; I deleted nothing.
>
> ## 1. Paper commit `2e96bdf6` — ACCEPTED
>
> - **Round-2 MAJOR, resolved.** `check_note2(draft=True)` now works as a before-signature check:
>   - it requires exactly one line `approved: false`;
>   - it runs `G.check_note` on a temporary copy that reads `approved: true`, with the on-main check skipped;
>   - it then runs every other check, still reading the cross-check note and the verdicts from main.
>
>   Strict mode is unchanged. The order now works: draft check, then sign and publish, then strict check, then the TASL-7 launch. The docstring, report §5 and step 5, and the note2 header all say this. Tests cover draft mode passing, strict mode refusing the unsigned note, draft mode refusing a signed note, and the CLI run on the real draft.
> - **Minor 1, resolved.** P7 now refuses any `<…>` placeholder and must cite exactly one `g1b_xc_t1_tasl_<8 digits>.md` that is on main.
> - **Minor 2, resolved.** The gate record now binds the `ASSEMBLY.json` and `runs.jsonl` sha256s, the G.1b spec sha and the cross-check run id. `summarise_gated` refuses a run with no gate record or one that does not match (tested).
> - **Minor 3, resolved.** Report step 7 now says the assembly checkout must be at or after the launch commit L; at M the gate refuses.
> - **Minor 4, resolved.** Decision XC-NONDET is in the report.
> - **Minor 5, resolved.** A missing `SHA256SUMS` now raises a Stop (tested).
>
> **MINOR (optional)**
> 1. **Draft check needs the final file name.** Draft mode still applies `check_note`'s name rule to `note_path.name`. Run on `docs/r1/proposals/G1B_T1_TASL_NOTE2_DRAFT_20261121.md`, it stops on the name, not on content. The CLI test copies the draft to `g1b_t1_tasl_20261122.md` first. Fix: add to the note2 header that the draft must be copied to its final `g1b_t1_tasl_<date>.md` name before `--draft`.
> 2. **Cross-check note citation is only checked for existence.** P7's citation of the cross-check note (`g1b_crosscheck.py`, `check_note2`) only confirms the file is on main. It does not check that note's fields: `approved: true`, the `run_id`, `xc_spec_sha256`. Fix: optionally run `check_xc_note`'s field checks on the bytes read from main.
> 3. **Fallback replace in draft mode.** If the approved line is the file's first line, the fallback replaces the first `approved: false` anywhere in the text. The draft does not hit this, and the result fails closed (duplicate-field or approved error).
> 4. **Gate record is not tamper-proof.** `summarise_gated` does not check the gate's `crosscheck_run_id`, and a gate record can be written by hand. It guards against accidents, not tampering. Acceptable as a procedural gate.
>
> ## 2. Harness commit `2d09f9a9` — ACCEPTED
>
> - The earlier-master allowance is now keyed to the seven named T1 nodes (`NODE_LIB_EARLIER_NODES`). A future node or `autoresearch_fixedtokens` carrying the old copy is refused, and so is an undeclared edit (tested).
> - The test now reads the frozen copy from `nodes/mlab_cifar10/ar_isolated.py`, so it no longer needs the `c025f89a` git object. In round 2 I confirmed that `37d99ab0…` is the `c025f89a` master.
>
> ## 3. Errata commit `ce19452b` — ACCEPTED
>
> Each corrected bullet checks out against the captures:
> - **Median.** 218.951 s is the upper-middle of the 8 executed runs; the captures' `slowdown.json` has `median_executed_run_seconds` 218.951 over 8 records, with mean 223.547. The true median is 218.7935 s, and 218.697 s is correctly named the B1/B2 median, a different quantity.
> - **Bundle bytes.** It now says the figure is not reproducible, gives content 152,751,278 B and apparent size 161,534,003 B (the review's measurements), and calls the result's "packaging size" explanation unverified.
> - **stderr.** `slowdown.stderr.txt` is 0 B, and the false STOP is evidenced only by `RESULT_STATUS.initial_false_stop.txt` and `DONE.initial_false_stop`. All three facts match the captures.
>
> **MINOR (optional)**
> - **The 152,751,278 B figure is for the full bundle.** It is the Mac and live bundle the U2 review measured. The committed capture tree on `ops-tasl-20261116` has 7,024 entries; 49 files listed in its `SHA256SUMS` are not committed (for example `logs/*.log` and `gpu/co_tenant_monitor.log`). So the figure cannot be reproduced from the branch alone. Fix: add "(the full bundle; the committed tree omits 49 listed files)".
> - **"Still open" is now stale.** Its last bullet ("needs a short independent re-review") can cite this acceptance once it is recorded.
>
> Nothing in this report comes from memory.

## Round 4 (`5daee732 / 245fba8f`)

> **CONFIRMED.** I confirm both commits, with one thing to do before merging: the review file the errata cites does not exist yet.
>
> **1. Paper commit `5daee732` (diff `2e96bdf6..5daee732`): CONFIRMED.** The targeted tests pass: `test_t1_tasl_crosscheck.py` and `test_t1_tasl_g1b.py`, 75 passed. The worktree is clean.
> - **Cited cross-check note:** `check_note2` now reads the cited note's bytes from main, writes them to a temp copy under `docs/r1/authorizations/`, and runs `check_xc_note` on that copy with `on_main` bound to those bytes. That checks `approved`, `paper_commit`, `xc_spec_sha256`, the G.1b spec sha, `run_id`, the harness pin and P1–P4. The new test case refuses a cross-check note on main that is not signed.
> - **Draft copy:** only a line that is exactly `approved: false` becomes `approved: true`, and this holds for CRLF files too. The earlier check still requires exactly one `approved:` line.
> - **`summarise_gated`:** it now also checks the gate's `crosscheck_run_id`.
> - **Note2 header:** it now says to copy the draft to its final `g1b_t1_tasl_<YYYYMMDD>.md` name under `docs/r1/authorizations/` before running `--draft`.
>
> **2. Errata commit `245fba8f` (diff `ce19452b..245fba8f`): CONFIRMED, with one condition.**
> - **Full-bundle qualifier:** the 152,751,278 B and 161,534,003 B figures are now marked as full-bundle values, and the text notes that the committed tree omits the 49 listed files (for example `logs/*.log`). This matches what I found in round 3.
> - **Condition:** the new "Still open" line cites `docs/r1/reviews/G1B_CROSSCHECK_REVIEW_20261121.md` on `mac-g1b-xc-20261121` as the record of acceptance. That file is not in the branch at `5daee732`. The note drafts cite the same path (the cross-check note's P4 and note2's P10). Commit the review file, carrying these review rounds, to that branch before or together with the errata reaching main, or the citation points to nothing.
>
> All my work was read-only, and I deleted nothing. Scratch is in `/tmp/rev_xc/_to_delete/`. Nothing in this report comes from memory.

---

Code-Commit: 5daee7320cb61629058e950032e6eb8d197a1964
Verdict: ACCEPTED

Accepted: the cross-host check, its gated assembly and summary, and the drafts at paper `5daee732`; the port-check allowance at harness `2d09f9a9`; the U2 errata at `245fba8f`. Both notes remain drafts (approved: false).
