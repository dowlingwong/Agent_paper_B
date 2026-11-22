Reviewed base: published `main` `16e0b52c`; accepted at `eba9e0ff4b21d9ea56a3c87f56ac201491623853` (code and draft `b1962406`, dry-check output `eba9e0ff`)

# Independent review record — the G.1b TASL authorization note draft, the TASL launch binding, the dry launch check and the P.4 phase-1 decision list

**Unit.** On `mac-g1b-auth-20261121`: `docs/r1/proposals/G1B_T1_TASL_NOTE_DRAFT_20261121.md` (approved: false);
`sweep2/t1_tasl/g1b_tasl.py` (`verify_launch_tasl` in place of `g1b_lib.verify_launch`, P7 gate for TASL-7 nodes, `check_note`
checks of `run_id` and `harness_commit`); `sweep2/t1_tasl/g1b_tasl_authorization.template.md`; `r1/tests/test_t1_tasl_g1b.py`;
`sweep2/t1_tasl/g1b_note_dry_check.py` and `docs/r1/reports/g1b_tasl_note_20261121/dry_check.json`; the report
`docs/r1/reports/g1b_tasl_note_20261121/G1B_TASL_NOTE_20261121.md` (LB, XC, AR, RUNID; conditions of the earlier reviews);
`docs/r1/proposals/TRACKP_P4_PHASE1_DECISIONS_20261121.md`; the merged T1 TASL code-unit review record (`7060f90d`). Authority:
the queue of 21 Nov 2026 (20:57); rows R1-T1-HOST-TASL, R1-T1-TASL-ENV, R1-G1B-EDITS, R1-G1B-TIMEOUT, R1-TRACKG-G3-EARLY, R1-G1B-CAP.

**Process.** One independent reviewer for three rounds, read-only, synthetic and scratch repositories only, scratch under
`/tmp/rev_g1bnote/` moved to its `_to_delete/`. Round 1 confirmed that the shipped launch binding is unsatisfiable and found the
recommended cross-host route unworkable (blocking), an undisclosed code freeze, P4 citing reviews that held EVIDENCE blocked, and
a misframed alternative; round 2 accepted with four minors, fixed in `b1962406`; round 3 confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `031fc944` | NOT ACCEPTED (B1; M1–M3; 9 minors) |
| 2 | `2a7a39bb` | ACCEPTED (4 minors) |
| 3 | `eba9e0ff` | CONFIRMED |

**Open items.** Author decisions LB (A recommended), XC (A recommended: TASL-2 nodes under this note, TASL-7 nodes under a second note once the crosscheck unit is reviewed), AR (A: not in this run), RUNID (`g1b-tasl-20261121-b`); the eight P.4 phase-1 decisions. Engineering: the crosscheck unit (own spec and script; its PASS record a required input to `assemble` for the TASL-7 nodes); `g4_tasl.launch` and the sweep-2 kit's `g1b_switch.py` carry the same unsatisfiable binding. Noted (round 3): the origin check is skipped for a spec without `paper.repo` (the shipped spec has one).

## Round 1 (`031fc944`)

> **NOT ACCEPTED**: 1 BLOCKING, 3 MAJOR, 9 MINOR.
>
> The code works and the note's values are correct. The BLOCKING finding sits in decision XC and the wording of P7. The problem is the route the report recommends to the author, together with what P7 says it attests. Fixing it, and two of the MAJORs, is mostly a matter of rewriting text.
>
> ## What holds
> - **Circularity: confirmed.** `g1b_lib.verify_launch` (`sweep2/g1b/g1b_lib.py:264-285`) needs:
>   - HEAD = `spec.paper.commit`;
>   - that commit descending from `origin/main`;
>   - `docs/r1/authorizations` equal between the two.
>
>   So the commit's own tree contains the note, and the note names that commit. A commit cannot contain its own hash. It is also circular through the spec: the note binds `sha256(spec)`, and the spec contains that same hash.
> - **`verify_launch_tasl` is sound as a binding.** It checks that `ls-remote` equals `origin/main`, that HEAD is at `origin/main`, that the checkout is tracked-clean, and that the spec equals `HEAD:rel` (symlinks resolve; a path outside the repo STOPs). It also checks that the paper commit is an ancestor and that the trees are equal outside the excludes. I found no way to run code that differs from `paper_commit`.
> - **The `docs/` exclusion is safe for G.1b.** No G.1b code path reads `docs/` from the working tree. PLAN rows, the note and the host reports are read from `origin/main`, and HEAD equals main.
> - **Note values all match main `16e0b52c`** (checked by script):
>   - per-node kit pins and data manifests, the two full GPU UUIDs, both host-check sha256s (`681011b2…`, `09945c15…`), and the drivers (535.309.01 and 580.178.04, from the binding reports and the dry-run report);
>   - env freezes, census commit `76f1d7ba` and its report sha (`146b1114…` at the census commit, `d7f8f8aa…` on main), and harness `c025f89a`;
>   - all seven timeouts equal 3 × slowest, matching ROWS_DRAFT §2; I spot-checked ogbn E4 = 21.8 s in its U2 record;
>   - `validate --launch` reproduces 28.262 GPU-h (14.06 / 14.202), 41.644 at sensitivity, and 7.168 CPU core-hours;
>   - the cross-host check's "about 1 GPU-h" is right: 3 nodes × 10 default runs plus setup.
> - **Parsing.** 41 fields, no duplicates; no prose line matches the parser's regex.
> - **Tests and dry check.** The targeted tests pass (42). I re-ran the dry check: `ok: true`, same outcomes as the committed `dry_check.json`, only the commit shas differ. It writes only to its temp origin and clone, which borrow objects through alternates. The worktree stayed clean and no new `.pyc` was written.
> - **The review-record merge is sound.** It is docs only, the blob is identical to `7060f90d`, it is based on `021dbc26` (on main), and `g1b_tasl.py` is unchanged from `021dbc26` to main.
> - **RUNID reasoning is right.** The sealed, complete dry attempts under `-a` would make `next_attempt` refuse and could be assembled; this is dry-run review M2.
>
> ## BLOCKING
> **B1. The recommended XC-A route cannot complete one assemblable table, and P7 attests something that cannot exist before launch.**
> - `G1B_TASL_NOTE_20261121.md:89-94` says a second note with "same run id and spec, P7 PASS" releases the TASL-7 nodes. But:
>   - The crosscheck is new code. Once it reaches main, `verify_launch_tasl` STOPs (`g1b_tasl.py:959-960`, code differs from `paper_commit` M1) unless `spec.paper.commit` changes.
>   - The report also puts a TASL-2 `jax312` entry into the spec.
>   - Either change gives a new spec sha. `assemble` requires every job record's `spec_sha256` to equal the spec file's (`g1b_tasl.py:825`). The four TASL-2 nodes, about 14 GPU-h, could then not be assembled with the TASL-7 nodes.
> - P7 (`G1B_T1_TASL_NOTE_DRAFT_20261121.md:47`, gate at `g1b_tasl.py:973-976`) would attest "rerun their default parts on TASL-2 with identical metrics". The crosscheck compares against the sealed TASL-7 default rows (pre-launch review B1, and report line 92), which exist only after the TASL-7 nodes run. So P7 PASS before launch is the same chicken-and-egg problem this unit fixes.
> - **Fix.** Reword P7 as a precondition: "the crosscheck job is reviewed; no TASL-7 node is accepted or assembled without identical TASL-2 default-part metrics". Then either:
>   - recommend XC-B: build the crosscheck and finalise the spec, including TASL-2 `jax312`, before the single note; or
>   - spell out a workable XC-A: keep the G.1b spec final now, put the crosscheck in its own spec file, and keep its code off main until every G.1b node has launched. Otherwise state that the TASL-2 nodes would need re-measuring.
>
> ## MAJOR
> **M1. A code freeze on main is required and not disclosed** (`g1b_tasl.py:947`, `:958-960`). Every `run-node` call, seven nodes in series over about 14 h per host, needs `origin/main` freshly fetched and code-equal to `paper_commit` everywhere outside `docs/`. Any unrelated code merge stops all remaining launches: for example `mac-release-20261121` (`r1/c3/release.py`, `sft_data.py`) or `mac-trackp-p3`, both accepted and waiting to merge. Recovery then needs a new `paper.commit`, which brings back B1's spec-sha mismatch. **Fix:** either
> - state a main code freeze for the G.1b window in the note and report; or
> - narrow the equality to the executed paths (`sweep2/t1_tasl/{g1b_tasl.py,t1_tasl_node.sh}`, `sweep2/g1b/`, `r1/noise/`); or
> - allow HEAD to be the note-carrying commit M2, an ancestor of `origin/main`, provided the note and PLAN rows are byte-identical on `origin/main`.
>
> **M2. P4 says PASS but cites reviews whose verdict is "EVIDENCE BLOCKED"** (`G1B_T1_TASL_NOTE_DRAFT_20261121.md:44`). Both the pre-launch review (B1, M1, conditions m1/m3/m4/m7/m8/m9) and the dry-run review ("EVIDENCE status: BLOCKED", M2, carried conditions) say this. **Fix:** add a disposition table to the report:
> - B1 → P7 / XC;
> - M1 → closed by the dry run;
> - M2 → RUNID;
> - m3 → `verify_launch_tasl`;
> - m4 → the `harness_commit` line;
> - m8 → census line;
> - m9 → TASL2 precheck still stale, and P11 cites it;
> - m1 and m7 → their status.
>
> Have P4 cite that table.
>
> **M3. Option LB-B is misframed** (`G1B_TASL_NOTE_20261121.md:83-84`). It is presented as weaker but workable. It is still unsatisfiable: `verify_launch` needs `spec.paper.commit` = HEAD, and the note in HEAD's tree binds `sha256(spec)`, which contains that hash. **Fix:** say B would also need `paper.commit` removed from the spec, or the spec-sha binding dropped.
>
> ## MINOR
> 1. **The exclusion glob is wider than needed** (`g1b_tasl.py:931`). `*_spec.json` also excludes `g4_tasl_spec.json`; I verified this in a scratch repo. Exclude only the resolved spec `rel`.
> 2. **`g4_tasl.launch` has the same unsatisfiable binding** (`sweep2/t1_tasl/g4_tasl.py:733`), but the report (line 44) names only `g1b_switch.py`. Add it.
> 3. **The fill-in list is incomplete** (report line 20, note line 5). It names approved, `paper_commit` and `spec_sha256`, but P10 must also go from PENDING to PASS with its review path, and the note header's "three fill-in fields" is inconsistent with that.
> 4. **`check_note` does not verify `run_id` or `harness_commit`** against the spec. R1-T1-TASL-ENV says "harness at the commit the signed note names". Add equality checks, and make the `harness_commit` value a bare sha.
> 5. **AR framing** (report lines 100-102; note line 24). The status claim is true: R6 is NOT ACCEPTED with 0 BLOCKING and 3 record-only traceability MAJORs, and the U2 result is accepted conditional on C1–C5. But R1-TRACKG-G3-EARLY gates joining on "U2 passes" and does not wait for the census report. Give the real reasons instead: U2 conditions C1–C5 are only partly applied, and there is no reviewed spec entry. Also say R6's MAJORs are traceability only.
> 6. **Census records are not on main.** The note's `census_record` paths exist only at census commit `76f1d7ba`; annotate them as such. Also, "main's copy adds the autoresearch row only" is overstated: main's copy also rewrites prose and acceptance text. The seven node rows are unchanged.
> 7. **`node_split` wording** (note line 23). `mlgym_houseprice` (CPU) runs beside the GPU nodes with no GPU lease; it does not run "one after another under its GPU lease".
> 8. **`verify_launch_tasl`, pre-existing pattern.** It ignores untracked and ignored files (`-uno`), and it does not check `origin`'s URL against `spec.paper.repo`. Consider both. No test covers the "spec not committed" branch on its own: the last test matches `tracked-clean|not the committed`.
> 9. **P.4 list.** Its claims match `3eeccf9a`, `275d7dcb` and `84b86b83`; it gives one recommendation per decision and fits about one page (793 words). Three corrections:
>    - **P4-CAP arithmetic** (`TRACKP_P4_PHASE1_DECISIONS_20261121.md:18`). Under P3: 9 + 3×(750/590) = 12.81 full-run equivalents of about 3.87 min, which is 0.83 h per 0.8B base. That gives about 9.9 GPU-h at 5× and **about 14.9 at 8×**, not 19; 19 only fits if startup and probe are already included. State which. The 25 GPU-h STOP logic holds only if 19 includes them.
>    - **P4-JOB** (line 16). Under P3 B is 64 jobs and at most 32 GPU-h of startup, which does not break 40 "on startup alone"; it breaks 40 once training is added.
>    - **P4-LABELS** (line 13). The raw block is refused only until the T0 test release row, not permanently. P4-MB A also requires changing `trackp_htcondor_v2.json`'s `sft.micro_batch` from 16 to 8, which changes the host-config sha.
>
> ## Notes
> - My scratch is moved to `/tmp/rev_g1bnote/_to_delete/`; nothing was deleted, committed or modified in the worktree.
> - The dry check's own `TemporaryDirectory` removed its temp dir under my TMPDIR, as designed.
> - Nothing from memory was used.

## Round 2 (`2a7a39bb`)

> **ACCEPTED** (round 2, tip `2a7a39bb`): 0 BLOCKING, 0 MAJOR, 4 MINOR.
>
> Minor 1 is the one to fix before the note goes to the author, or at least qualify in the report. The other three can go in with the next code touch.
>
> ## Round-1 findings: all closed
> - **B1 (XC route and what P7 attests): closed.**
>   - The G.1b spec is now final and unchanged from main `16e0b52c`.
>   - The crosscheck gets its own spec, script and note.
>   - The second note carries the same `run_id`, `paper_commit` and `spec_sha256`, and TASL-7 launches from the same checkout `M2`. All job records then carry one spec sha, so `assemble` (`g1b_tasl.py:825`) can join all seven nodes.
>   - P7 now attests the reviewed job and the rule, not the comparison result. That removes the chicken-and-egg problem.
> - **M1 (code freeze): closed.**
>   - HEAD must be published (an ancestor of or equal to the fetched `origin/main`).
>   - Code must equal `paper_commit` outside `docs/` and the one spec file.
>   - The note, the PLAN rows and the host records are still read from `origin/main`, so removing the note on main stops launches.
>   - The dry check shows a checkout at a moved main STOPs, while the `M2` checkout passes: TASL-2 with the first note, TASL-7 with the second.
> - **M2 (conditions of the earlier reviews): closed.**
>   - The table covers every condition of the two earlier reviews, and P4 cites it.
>   - I checked P2's item-7 claim at harness `c025f89a` in `/tmp/pb/wt/t1h`. `cuda_share`/`cuda_open` are defined in each node's copied `ar_isolated.py` and in the library source, and called nowhere in the seven nodes. Only `autoresearch_fixedtokens`, which is not in this run, uses them.
> - **M3 (LB-B framing): closed.**
> - **Round-1 minors 1–9: addressed.**
>   - Only the spec file itself is excluded now; a test shows a G.4 spec change refuses.
>   - `g4_tasl.launch` is named; the fill-in list has four edits, P10 included.
>   - `check_note` checks `run_id` and the bare `harness_commit`.
>   - AR, census and houseprice wording is fixed; untracked code is refused.
>   - P.4 list: the arithmetic now checks out: 12.8 equivalents × 3.9 min ≈ 0.83 h per base; 9.9 / 14.9 GPU-h training, 14 / 19 with startup and probe; 64 jobs × 0.5 = 32, plus training > 40; 19 + 6.6 = 25.6 > 25. The LABELS and MB corrections are right, and the list is still one page (870 words).
>
> ## What I ran
> - Targeted tests (`r1/tests/test_t1_tasl_g1b.py` and `test_t1_tasl_g4.py`): 68 passed.
> - The dry check against `09d8d42d`: `ok: true`, 8/8 expectations. Same outcomes as the committed `dry_check.json`; only commit shas differ.
> - Note values re-checked by script against the main spec: all match, 43 fields, no duplicates.
> - The worktree stayed clean. I set PYTHONDONTWRITEBYTECODE for these runs.
>
> ## MINOR
> 1. **The origin URL check can be bypassed with `insteadOf`** (`sweep2/t1_tasl/g1b_tasl.py:962`).
>    - `git config --get remote.origin.url` returns the raw URL.
>    - With a `url.<x>.insteadOf` rewrite, for example in a host's global gitconfig, the check passes while `ls-remote` and fetch talk to another remote. I reproduced this: config gives the GitHub URL, `git remote get-url origin` gives the scratch path.
>    - The dry check passes only because of this bypass (`g1b_note_dry_check.py:137-143`), so report line 49 overstates the guarantee.
>    - **Fix:** compare `git remote get-url origin` (it expands `insteadOf`). In the dry check, inject the expected repo id instead, for example by monkeypatching `T._repo_id` or a resolver, and say so in its docstring.
> 2. **The spec exclusion uses default pathspec magic, so wildcards match** (`g1b_tasl.py:987`).
>    - If the spec's path contains `*`, `?` or `[`, the exclusion can hide code. I reproduced it: with a committed `sweep2/t1_tasl/g1b_tasl*`, a change to `g1b_tasl.py` passes, and `literal` refuses it.
>    - Reaching this needs a published oddly-named copy of the signed spec, so it is contrived.
>    - **Fix:** use `f":(exclude,literal){rel}"`, or require `rel == "sweep2/t1_tasl/g1b_tasl_spec.json"`, the path the note's `spec:` line names.
> 3. **The untracked-code scan skips ignored files** (`g1b_tasl.py:972`).
>    - `--exclude-standard` hides files matching `.gitignore`, which has `*.py[cod]`.
>    - A sourceless `.pyc` placed directly in `sweep2/t1_tasl/` (not in `__pycache__`) is importable and would shadow stdlib modules, because that directory comes before stdlib on `sys.path`. The scan would not see it.
>    - **Fix:** also scan `--others --ignored --exclude-standard` for `.pyc`/`.so`/`.py` outside `__pycache__/` and `docs/`, or add `.pyc` and drop `--exclude-standard` for code suffixes.
> 4. **The assemble-time half of P7's rule has no named enforcer** (report lines 99-109, note P7).
>    - P7 attests that "no TASL-7 node is accepted or assembled without identical TASL-2 default-part metrics". But `assemble` at `M2` has no such check.
>    - `assemble` is not launch-bound, and it checks only the spec sha. So the rule is procedural unless the crosscheck unit adds the check.
>    - **Fix:** in XC-A, say the crosscheck unit must make its PASS record a required input to `assemble` for TASL-7 nodes, run from a checkout that carries that check with the same spec file. Otherwise state that the author gates it by hand.
>
> ## Notes
> - My scratch is moved to `/tmp/rev_g1bnote/_to_delete/r2`, beside the round-1 `s` and `t`. Nothing was deleted, modified or committed.
> - Nothing from memory was used.

## Round 3 (`eba9e0ff`)

> **CONFIRMED** at tip `eba9e0ff`: all four round-2 minors are fixed. Nothing is open, and the round-2 ACCEPTED verdict stands.
>
> 1. **Origin check:** fixed.
>    - `_origin_url` (`sweep2/t1_tasl/g1b_tasl.py:944-946`) uses `git remote get-url origin`, which applies `insteadOf`. The new test shows such a rewrite is refused.
>    - The dry check no longer sets `insteadOf` or `pushurl`. Its clone's origin is the scratch path, and it aborts unless fetch and push both resolve there.
>    - `T._origin_url` is replaced only inside `_patched` and restored afterwards. The docstring and the report say this one check is not exercised for real in the dry run.
> 2. **Spec exclusion:** fixed. It is now `:(exclude,literal){rel}` (`:1000`), and `test_the_spec_exclusion_is_literal` refuses the `g1b_tasl*` case I reproduced.
> 3. **Ignored code files:** fixed.
>    - A second scan (`:984-986`) lists ignored files in `sweep2/t1_tasl` and `sweep2/g1b`. It flags code suffixes, `.pyc`/`.pyo` included, outside `__pycache__/`.
>    - The test refuses a sourceless `json.pyc` and accepts a normal `__pycache__` file.
>    - Limiting this scan to the two `sys.path` directories is reasonable; the non-ignored scan still covers the whole repository outside `docs/`.
>    - On the real worktree it finds nothing outside `__pycache__/`, so it would not falsely trip today.
> 4. **Assemble gate:** fixed. The note's P7 and the report's XC-A both say the crosscheck unit must make its PASS record a required input to `assemble` for the TASL-7 nodes. Until then the author gates assembly by hand.
>
> **What I re-ran**
> - The two targeted test files (`test_t1_tasl_g1b`, `test_t1_tasl_g4`): 69 passed.
> - The dry check against `b1962406`: `ok: true`, 8 of 8 expectations met, all five gate outcomes the same as the committed `dry_check.json`. The draft's sha matches the one recorded there, and it still parses to 43 fields with no duplicates.
> - The G.1b spec is still byte-identical to main `16e0b52c`.
>
> One small point, not one of the four: the origin check is skipped when the spec has no `paper.repo`. The shipped spec has one, so this does not affect this run.
>
> The worktree is clean. My scratch is moved to `/tmp/rev_g1bnote/_to_delete/r3`, beside `r2`, `s` and `t`; nothing was deleted, modified or committed. Nothing from memory was used.

---

Code-Commit: b19624067d178b40d1ff595fd46bee7c9512f126
Verdict: ACCEPTED

Accepted: the note draft (approved: false), the TASL launch binding and the dry launch check at `b1962406` (output at `eba9e0ff`), and the P.4 phase-1 decision list.
