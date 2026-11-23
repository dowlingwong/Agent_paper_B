Reviewed base: `3c3f822a` (published `main`); first delivery (a)–(c) accepted at `cd50e36f`, confirmed at `e740dae7` (chain commits (a) `34a5b1d6`, (b) `b5824240`, (c) `6ad899e0`); second delivery (d) accepted at `bd924c58`, confirmed at `8c9611c1eedf9f8aa8796caddd6dfc54d39658c1` ((d) `d52c9d9d` on `570ae410`)

# Independent review record — the TASL launch chain of R1-T1-DATA-MANIFEST: first delivery (a)–(c) (G.1b amendment and note 2, cross-check re-issue, G.4 re-issue; decision G1B-JOIN, the builder and the publication check) and second delivery (d) (the AR spec and the third-note draft)

**Unit.** On `mac-tasl-chain-20261122` over published `main` `3c3f822a`: three chain commits, each changing exactly one
spec with `paper.commit` = its parent — (a) `sweep2/t1_tasl/g1b_tasl_spec.json` (the corrected `mlgym_fmnist` and `mlgym_cifar10`
manifests), (b) `g1b_crosscheck_spec.json` (run `g1b-tasl-20261121-b-xc2`, binds the amended G.1b spec), (c) `g4_tasl_spec.json`
(the corrected `mlgym_fmnist` manifest) — with the note drafts in `docs/r1/proposals/` (amendment, note 2, cross-check and G.4
re-issues; all `approved: false`, citing the reviewed census erratum record); then the tail: `sweep2/t1_tasl/g1b_tasl_join.py`
(decision G1B-JOIN, inert without its row; `publication-check`), `sweep2/t1_tasl/build_launch_chain.py` (deterministic `build`),
`r1/tests/test_t1_tasl_chain.py`, adjusted existing tests, and the report `docs/r1/reports/tasl_chain_20261122/` (with
`build_config.json` and the generated launch table). (d), the AR spec, is a later delivery: the TASL-2 host check at the AR pin
STOPped. Authority: R1-T1-DATA-MANIFEST (option A), R1-G1B-AR-ENV, R1-G5-DECISIONS on `main`; the queue of 22 Nov 2026 (11:33),
item 1, and the coordinator's message of 22 Nov 2026 (15:39) with the reviewed erratum values and the split into two deliveries.

**Process.** One independent reviewer, read-only, synthetic data only (no label, evaluation, sealed or secrets file opened), scratch
under `/tmp/chainrev/` moved to its `_to_delete/`. Rounds 1–2 and three confirmations covered the four-commit chain with provisional
values (round 1: three majors; round 2: accepted with five minors; confirmations: the publication check replaced by a field-scoped
code check and hardened). The chain was then restructured to (a)–(c) with the reviewed erratum record cited. Round 3 found that a
note could cite erratum bytes no review fixed (M1) and three minors; round 4 accepted with two minors, which were confirmed. In every
round the reviewer reproduced the tip exactly from the committed `build_config.json`.

**Second delivery (d).** On `mac-tasl-chain-ar-20261122` over the delivered first delivery `570ae410`: one launch commit (d) changing only `sweep2/t1_tasl/g1b_tasl_ar_spec.json` outside `docs/` (the re-issued seven-node spec, R1-G1B-AR-ENV with the 3.12.15 interpreter of R1-G1B-AR-PY, the TASL-2 host-check sha256 `cce9b8fb…` of the reviewed binding record at harness `2d09f9a9`, `paper.commit` = its parent) with the third-note draft bound (P1–P8 PASS, `approved: false`), then the tail (`build_launch_chain_ar.py`, `build_config_ar.json`, tests, report §7) and the launch table. Input: the coordinator's message of 22 Nov 2026 (17:47). Round 9 accepted with three minors (the cap sum stated; P2 citing the record's review; P4's review file to cover (d), by this record); the confirmation round confirmed them, (d) rebuilt with the AR spec bytes unchanged.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `ec7bb084` | NOT ACCEPTED (M1–M3; minors m1–m8) |
| 2 | `48cbe5cc` | ACCEPTED (minors m1–m5) |
| 3 | `e320dfb2` | NOT CONFIRMED (C1: the publication grep could never pass) |
| 4 | `651dabd6` | CONFIRMED (two optional hardenings) |
| 5 | `806fd54d` | CONFIRMED (one cosmetic nit) |
| 6 | `102a1cea` | NOT ACCEPTED (M1: cited erratum bytes must be reviewed ones; minors m1–m3) — first delivery (a)–(c) |
| 7 | `cd50e36f` | ACCEPTED (minors m1–m2) |
| 8 | `e740dae7` | CONFIRMED (one optional residual gap) |
| 9 | `bd924c58` | ACCEPTED (minors m1–m3) — second delivery (d) |
| 10 | `8c9611c1` | CONFIRMED (on condition that this record covers (d)) |

**Open items.** (1) Publication (path (i)): the erratum record is published on `main` byte-identical at sha256 `9b40944b…` with the chain, its review's editorial conditions C1–C3 in a separate addendum beside it; the cited sha256 must be one a review fixes, otherwise STOP. (2) The notes are published after the chain: `g1b_tasl_join.py publication-check <note>` (`--p4` for the amendment and note 2) must exit 0; it fetches origin, reads the published launch table's erratum and checks every cited record. Residual gap noted by the reviewer (optional): a citation of the erratum under another `docs/r1/…` path with matching bytes is not compared with the reviewed sha256. (3) Decision G1B-JOIN needs the author row R1-G1B-JOIN (option A recommended); without it the joined assembly refuses. (4) Signatures: the amendment, note 2 and the cross-check and G.4 re-issues by the coordinating chat under R1-T1-DATA-MANIFEST. (5) (d) and the third note are a separately built and reviewed delivery on top of the published (a)–(c), after the AR host-check STOP is resolved; until then the AR spec on `main` refuses to validate. (6) The sealed TASL-2 nodes of the first note are held only by host state: their runs-tree attempts must be kept. (7) Never rerun `build` after any launch; publish by merge, never squash or rebase. (8) For (d): merge `main-t1-ar-pin-binding-20261122` @ `ebb86248` (the binding record byte-identical, sha256 `cce9b8fb…`, its captures and reviews) before or with the chain; merge `mac-tasl-chain-ar-20261122` (which contains (a)–(c)) by a merge commit; the author signs note 3 (`check-note-ar --draft`, publish byte-identically, strict check); launch from (d) or a docs-only descendant; the AR job holds TASL-2's GPU lease about 28 wall-hours (a busy lease is a STOP): schedule it around the `mlgym_fmnist` amendment, `xc2`'s TASL-2 side and the G.4 pilot.

## Round 1 (`ec7bb084`)

> Reviewed base: ec7bb08410657646c0a8f329b07b135a893258c6
>
> ## Summary
>
> **Verdict: NOT ACCEPTED.** There are no blocking findings and three major ones. All three can be fixed in docs or the tail commit, so the four chain commits (a)–(d) can stay as they are: the note drafts are not part of the launch binding, and the signed copy is what gets checked.
>
> **What is right in the chain itself:**
> - **One spec per commit.** Each of the four chain commits changes exactly one spec file outside `docs/`, and that spec's `paper.commit` is the commit's parent. I checked this against `launch_table.json`: every spec sha256 and every paper commit matches.
> - **No code changes.** Inside the chain only JSON specs and docs change.
> - **Spec changes are the ones the rows require.**
>   - G.1b: `paper.commit` plus the two manifests.
>   - Cross-check: `run_id` → `-xc2`, `g1b_spec.sha256`, `paper.commit`.
>   - G.4: the `mlgym_fmnist` manifest plus `paper.commit`.
>   - AR: `seven_node_spec.sha256`, `paper.commit`, `env_decision.authority`, `env_python_comment`.
> - **Provisional manifest values are correct.** `24cb3448…` and `54d3a74d…` are the sha256 of `produced_mlgym_{fmnist,cifar10}.json` at `b77a2ef79`.
> - **Re-issued notes.** The cross-check and G.4 notes change only what they say they change.
> - **Targeted tests.** 183 passed at the tip.
> - **Publication.** `origin/main` is still `3c3f822a`, so a fast-forward merge keeps the launch shas.
> - **Launches fail closed.** With a local origin, each run passes `verify_launch_tasl` only from its own commit. A squash or rebase would make every launch refuse, not launch the wrong thing.
>
> **Rebuild check.** I ran the builder in a scratch clone from the committed config. Tree (a) came out identical; trees (b)–(d) differ, because commit dates are not pinned and so the parent shas written into `paper.commit` change. The tail it cherry-picked is the wrong commit (see M3).
>
> ## Findings
>
> **M1. The G1B-JOIN rule does not pin the predecessor spec. The joined row mixes two code versions without saying so, and note 2 changes `paper_commit` without the row amending that.**
> - **Where:** `sweep2/t1_tasl/g1b_tasl_join.py` (`spec_difference`, `assemble_join`); `TASL_CHAIN_20261122.md` §4; the note-2 draft header.
> - **Problem 1, any `paper.commit` passes.** `spec_difference` accepts any value of `paper.commit`, and the predecessor is a free CLI file argument; neither is checked against `060aac91…` or the first note.
>   - Failure scenario: a sealed attempt under run id `g1b-tasl-20261121-b` from a spec variant that differs only in `paper.commit` would be accepted as "predecessor".
>   - Such a variant could come from a manual `run_node_job` or a dev checkout, and its `paper.commit` can point at a commit with different code.
>   - This breaks the "no way to smuggle in a different spec" claim.
> - **Problem 2, two code versions.** The three sealed attempts ran code at `10fd3343` (checkout `985dd45d`). The four new attempts run code at `3c3f822a`.
>   - I checked the actual difference and it is benign: `g1b_lib.py` and `r1/noise` are unchanged. In `g1b_tasl.py`, `run_node_job` differs only by the `is_ar` branch, plus AR validation and a schema check in `summarise`. `t1_tasl_node.sh` only adds the `xc` kind.
>   - But neither the decision text, the proposed row nor `ASSEMBLY.join` records this.
> - **Problem 3, note 2.** R1-G1B-NOTE2-DECISIONS fixes "same run_id, paper_commit and spec_sha256". The report says only "same spec_sha256" is amended. Note 2 also moves `paper_commit` from `10fd3343` to `3c3f822a`.
>   - This is arguably covered by R1-T1-DATA-MANIFEST's "the paper_commit its launch binding needs", but it is not stated.
> - **Option not posed.** Basing (a) on `10fd3343` (a side branch, merged) would give identical code for all seven nodes. It is ruled out by the coordinator's linear-chain constraint, but the decision should say so.
> - **Fix:**
>   - In `assemble_join`, require `sha_old` to equal the `spec_sha256` of `docs/r1/authorizations/g1b_t1_tasl_20261121.md` on `origin/main`, and the predecessor's `paper.commit` to equal that note's `paper_commit`.
>   - Require `sha_new` to equal the cross-check spec's `g1b_spec.sha256` (or the launch table's value).
>   - Record both paper commits in `join`, with the job-code diff between them (`git diff --stat 10fd3343 3c3f822a -- sweep2/t1_tasl/g1b_tasl.py sweep2/g1b r1/noise`).
>   - In §4, the proposed row and the note-2 header, state the paper_commit change and the reviewed diff ("seven-node path unchanged", as `G1B_AR_SPEC_SUPPORT_REVIEW_20261122.md` says).
>   - Add a test for a predecessor that differs only in `paper.commit`.
>
> **M2. The amendment note, and note 2, can launch with `census_erratum` unfilled, and the note's scope is not enforced.**
> - **Where:** `g1b_tasl.launch` → `check_note` (`g1b_tasl.py:1025ff`); drafts `G1B_T1_TASL_AMEND_FMNIST_DRAFT_20261122.md` and `G1B_T1_TASL_NOTE2_DRAFT_20261121.md`.
> - **The gap.** `check_note` checks only the approved/label/commit/sha/run/harness fields, the P1–P6 prefixes and citations, and `host_row`. It never looks at `census_erratum`, `amends` or `scope`. `check-note2` is a separate recorded step and is not enforced by `launch`.
> - **Failure scenario.** The coordinating chat signs the amendment with `approved: true` and forgets the erratum. The launch check passes, and `mlgym_fmnist` runs under the corrected manifest without the independently reviewed record that R1-T1-DATA-MANIFEST requires. The report acknowledges this ("fills census_erratum by hand"), but nothing stops it mechanically.
> - **Scope.** The amendment can launch any TASL-2 node of the re-issued spec. The three sealed nodes are held back only by `next_attempt` on TASL-2's runs tree; if that tree is cleaned after sealing, they are relaunchable. Note 2 (P7 PASS) can likewise launch `mlgym_fmnist`.
> - **Fix (no code change):**
>   - In both drafts, put the erratum into a field `check_note` enforces. For example, make P4 read `PENDING — … census erratum record <FILL path> sha256 <FILL> (review docs/r1/reviews/…)` and set it to PASS at signature. P4 must start with "PASS — " and cite `docs/r1/reviews/`, so an unfilled P4 STOPs the launch.
>   - Add a chain test showing that `T.launch` refuses the amendment note while its erratum is unfilled.
>   - State in the report that the three sealed nodes are refused only by host state, and that the runs-tree attempts must be kept.
>
> **M3. The builder cannot reproduce the published chain from its committed config.**
> - **Where:** `docs/r1/reports/tasl_chain_20261122/build_config.json`; `sweep2/t1_tasl/build_launch_chain.py`.
> - **Wrong tail.** `tail_commits` is `e71837111…`. That commit is not reachable from any ref (dangling), and it is not the published tail `35c5bce23`. It lacks `build_launch_chain.py` and `build_config.json`, and it carries an older report naming `/tmp/chainbuild/build.py`.
> - **Failure scenarios.**
>   - From the published repository, the rebuild fails at the cherry-pick (object missing).
>   - On this machine, it silently produces a chain whose tail drops the builder and config. The chain tests still pass on that output (I ran them: 12 passed), so nothing catches it.
> - **Not deterministic.** Commit dates are not pinned, so the shas of (b) onward differ on every run. The "deterministically" claim in the docstring is false; only tree (a) is reproducible.
> - **No completion mode.** There is no way to finish (d) by appending one commit on top of published main. Re-running with `ar_host_check` set rebuilds (a)–(c) with new shas. If (a)–(c) are already published or launched, that produces a parallel chain, and the builder also force-resets the branch with `checkout -f -B`.
> - **Fix:**
>   - Pin `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` from the config.
>   - Make the tail a published ref, or have the builder apply the tail's tree as a path list rather than cherry-pick a sha.
>   - Add an `--append-ar` mode: given the main tip, write one commit that fills the host-check sha256 and sets `paper.commit` to its parent.
>   - Add an `if __name__ == "__main__"` guard (the file sits in a directory on `sys.path`), and drop the machine paths (`worktree`, `table_out`) from the committed config.
>   - Document that the builder must not be re-run after any launch.
>
> **m1. The launch matrix does not exercise two of its claims.** (`r1/tests/test_t1_tasl_chain.py::test_each_run_launches_from_its_own_commit_and_from_no_other`)
> - **Docs-only descendants.** That check is skipped silently: between (c) and the tip there are the AR spec and code changes. No test shows a docs-only descendant launching.
> - **Different-spec cells.** Commits holding a different spec are only labelled "not this run's spec"; no refusal is run for them.
> - **Fix:** in the scratch origin, create a docs-only child of each launch commit and make `main` a merge that contains it, then assert pass. For the different-spec cells, call `check_note` with the signed-form draft and assert the `spec_sha256` STOP.
>
> **m2. Note texts are unclear about how to launch from a chain commit.**
> - The G.4 draft's `launch:` field still says the launch is "at or after the commit that publishes this note and the spec". Under the chain, that commit is not a docs-only descendant of (c), so following the text literally STOPs (it fails closed).
> - The amendment draft does not say that the signed note must be copied from `origin/main` into the launch checkout's `docs/r1/authorizations/` as an untracked file. Note 2 does say this.
> - **Fix:** reword the G.4 `launch:` line to "from the launch commit (or a docs-only descendant), with the signed note copied from origin/main into its docs/r1/authorizations/", and add the same sentence to the amendment draft.
>
> **m3. Note 2 has changes beyond the list in §3.** P12 goes from PENDING to a new PASS text, and the `nodes` and `scope` lines are rewritten. These are justified by R1-G1B-NOTE2-DECISIONS (NOTE2-AR A), but they are not listed. **Fix:** list them in §3 and in the draft header.
>
> **m4. Intermediate chain commits fail their own test suites.** On the four G.1b/cross-check/G.4/AR test files:
>
> | commit | failures |
> |---|---|
> | (a) | 56 |
> | (b) | 55 |
> | (c) | 36 |
> | (d) | 6 |
>
> The causes: at (a)/(b) the G.4 spec mismatches the re-issued G.1b spec; at (a)–(c) the AR binding is stale; and the old pinned tests were only updated in the tail. This is harmless for `verify_launch_tasl`, but a host preflight that runs the tests in the launch checkout will fail. **Fix:** disclose this in the report and the launch table, and say that preflight tests run at the tip.
>
> **m5. Two of the changed existing tests are weaker than before.**
> - In `test_t1_tasl_g1b_ar.py::test_seven_node_spec_is_the_signed_one_and_still_validates`, the `corrected` check is a tautology: both nodes are always in the node list, whatever their values.
>   - **Fix:** compare against `git show 3c3f822a:` with `J.spec_difference`, or assert both manifests differ from the old values.
> - `test_t1_tasl_crosscheck.py::test_xc_note_draft_parses` now rewrites the obsolete first draft's `g1b_spec_sha256` and `run_id`, so it tests a document that never existed. `xc_path` is also assigned twice.
>   - **Fix:** retire the test, or point it at the re-issued draft.
> - The other two changes are faithful: the census_erratum fill in the two note-2 tests, and the broadened match plus synthetic TODO in the shipped-AR-spec test.
>
> **m6. The join and the floor-by-node step leave gaps in what they record.**
> - `ASSEMBLY.join` does not record `mlgym_fmnist`'s two unsealed old-spec infrastructure attempts. They sit in the runs tree, not the sealed tree, so `infrastructure_attempts_not_used` is empty, even though R1-T1-DATA-MANIFEST says the correction is "disclosed in the T1 report".
> - `noise_floor_by_node` does not check the expected run ids (`g1b-tasl-20261121-b`, `g1b-ar-tasl-20261122-a`), nor that the seven-node summary came from a gated assembly.
> - **Fix:** add the unsealed attempt records (path and sha256) to `join`, and check the run ids.
>
> **m7. The superseded signed notes can still launch.**
> - `g4_t1_tasl_20261122.md` (old spec, same run id `g4-tasl-20261121-a`) can still launch `mlab_cifar10` or `mlgym_breakout_minatar` from `02abb367`.
> - A complete attempt made that way would then make `next_attempt` refuse the re-issued pilot for that node.
> - The old cross-check note can still launch `breakout` under `-b-xc`.
> - **Fix:** state the supersession in the re-issued notes and the report, and in the coordinating chat's publication commit. Optionally give G.4 a new run id.
>
> **m8. Stale comment in the cross-check spec.** Its `comment` still says `paper.commit` "names the signed G.1b paper commit and a launch refuses". Note it for the next re-issue.
>
> **Answers to the specific questions:**
> - **Unfilled `census_erratum`.** Yes, `g1b_tasl.check_note` would let an amendment note launch with it unfilled (M2).
> - **Amendment scope.** The amendment note launches only `mlgym_fmnist` given the current TASL-2 runs-tree state, not by its own text.
> - **Note naming.** It is consistent with the one-note-per-date-per-kind regex. A re-issue signed on 22 Nov would take a future date such as 20261123, which the report discloses.
> - **Inertness.** `g1b_tasl_join` is inert without the `R1-G1B-JOIN` row: the assembly checks the row before it writes anything.
> - **Compatibility.** The merged `ASSEMBLY.json` works with `g1b_tasl.summarise` and `summarise_gated`. Its schema and `spec_json_sha256` are the re-issued spec's, and `e1_report` reads only `runs.jsonl` and `edits.json`.
> - **Gate and sibling rules.** The gated join's gate is a faithful copy of `assemble_gated`, and the sibling-attempt rules are kept, since `G.assemble` runs per group.
>
> ## Verdict
>
> NOT ACCEPTED (M1, M2, M3; minors m1–m8).
>
> Scratch (327 MB: a rebuild clone plus pytest tmp) has been moved to `/tmp/chainrev/_to_delete/`. Nothing was written in `/tmp/pb/wt/chain`, `/tmp/pb/repo` or `/tmp/pb/wt/t1h`, apart from the ignored `__pycache__` that the prescribed pytest command produces; HEAD is unchanged at `ec7bb084`.

## Round 2 (`48cbe5cc`)

> Reviewed base: 48cbe5cc380fca14255b056c6caec85a7a532eea
>
> ## Summary (round 2)
>
> **Verdict: ACCEPTED, with minors.** All three round-1 majors are resolved. Of the eight round-1 minors, every one is resolved or properly disclosed, except a small leftover from m1 (new m1 below).
>
> **What I re-checked against the new chain (`3c3f822a..48cbe5cc`):**
> - **Chain shape.** (a) `239281ab`, (b) `2c8b7902`, (c) `07a6c7f6` and (d) `462c29bf` each change exactly one spec file outside `docs/`, and each spec's `paper.commit` is its parent.
> - **Spec changes.** They are the round-1 set. The only addition is the cross-check spec's rewritten `comment` (round-1 m8), which is inside (b) and declared in the chain test.
> - **Code.** Nothing in the chain changes code.
> - **Manifest values.** They are unchanged and equal the sha256 of the produced manifests at `b77a2ef79`.
> - **Targeted tests.** 184 passed at the tip.
>
> **Reproducibility.** In a scratch clone of `/tmp/pb/repo`, I ran `build_launch_chain.py build` with the committed `build_config.json`. It reproduced `48cbe5cc380fca14255b056c6caec85a7a532eea` exactly, every commit sha included. The tail files at `wip-tasl-chain-tcode` (`ba2467d2`) are byte-identical to those in the tail commit `75aa71710`. So after publication, setting `tail_ref` to `75aa71710` or the tip gives the same tree and the same shas.
>
> **append-ar.** I ran it on the tip in the scratch clone. It added one AR commit, with `paper.commit` = the old tip and only the AR spec changed outside `docs/`, then a docs commit. In that state `test_t1_tasl_g1b_ar.py` and `test_t1_tasl_chain.py` pass (81 passed), and the AR run is in the launch matrix.
>
> ## How the round-1 findings were handled
>
> **M1 (resolved).** `assemble_join` now:
> - reads the signed first note from `origin/main`, requires it to read `approved: true`, and requires the predecessor's sha256 and `paper.commit` to match that note;
> - requires the expected re-issued sha256, which the gated path takes from the cross-check's `g1b_spec.sha256`;
> - records both paper commits, the job-code files that differ between them, and the unsealed attempts it is given.
>
> The tests cover a predecessor that differs only in `paper.commit` and a wrong re-issued sha256. A second test checks the real `10fd3343..3c3f822a` difference: it is only `g1b_tasl.py`, `t1_tasl_node.sh` and the `ar-cond7a` freeze, with `g1b_lib.py` and `r1/noise` unchanged.
>
> `JOB_CODE_PATHS` covers what the job imports (`g1b_tasl.py` → `g1b_lib`; `g1b_lib` → `r1.noise`) plus `t1_tasl_node.sh` and `r1/harness.py`. The harness and node kits are pinned separately by the spec. The note-2 header and the decision text now state the `paper_commit` change and the code difference, and the proposed row names both paper commits. The one-code-version option is noted, not posed, with the reason given.
>
> **M2 (resolved, small leftover in m1 below).** In both the amendment and note 2, the census erratum is now part of P4, which reads `P4: PENDING — … <FILL …>`. A test shows that `g1b_tasl.launch` refuses the amendment with "P4 is not PASS", and `check_note` refuses note 2 the same way. The report now says the sealed TASL-2 nodes are held only by host state (the runs-tree attempts must be kept) and that note 2 could also launch `mlgym_fmnist` under the same spec.
>
> **M3 (resolved).**
> - Author and committer dates are pinned.
> - The tail is taken as files from a ref.
> - `append-ar` exists.
> - There is a main guard.
> - The committed config has no machine paths.
> - The report and the docstring say `build` is never run again after a launch.
>
> **Round-1 minors:**
> - **m1 (launch matrix).** The matrix now adds a docs-only child of every launch commit, reachable through a merge on `main`. Each run passes from its own child and is refused from every other child. Cells where the checkout holds a different spec now run the run's own note check and expect a spec_sha256/paper_commit STOP.
> - **m2 (launch wording).** The G.4 and amendment drafts now say to launch from the chain commit or a docs-only descendant, with the note copied in.
> - **m3 (note-2 changes).** They are listed.
> - **m4 (intermediate test failures).** Disclosed, with a small wording slip (new m2 below).
> - **m5 (weakened tests).** Both tests are repaired: the corrected values are now compared with the census values, and the old cross-check draft is now shown to be refused.
> - **m6 (join records).** The unsealed attempts are recorded, and floor-by-node checks the run ids and the cross-check gate record beside the summary. `g1b_tasl.summarise` writes `summary.json` into the run directory, so the gate check finds it.
> - **m7 (superseded notes).** The supersession is stated in the re-issued cross-check and G.4 drafts and in the report.
> - **m8 (cross-check comment).** Rewritten.
>
> ## Findings (round 2)
>
> **m1. The P4 gate depends on the signer replacing PENDING, not on filling the fields.**
> - **Where:** amendment draft P4; `g1b_tasl.check_note`.
> - **Problem:** `check_note` checks only that P4 starts with "PASS — " and cites `docs/r1/reviews/`.
> - **Failure scenario:** the signer changes `PENDING` to `PASS` but leaves the `<FILL: the path on main> sha256 <FILL>` text. The amendment then launches. For note 2 this is caught, because `check-note2` refuses `<FILL`, and that check is a required pre-publication step. The amendment has no such step.
> - **Fix:** add a step to the signature instructions in the amendment draft and report §3: run `grep -n '<FILL' <note>`, which must print nothing, before publishing. Or require the same `check-note2`-style `<FILL` scan for the amendment in the coordinating chat's publication checklist.
>
> **m2. The intermediate-commit disclosure is slightly wrong.**
> - **Where:** `LAUNCH_TABLE.md` (generated by `build_launch_chain.py`).
> - **Problem:** it says "at (a) and (b) the G.4 and AR specs still bind the old G.1b spec". The AR spec still binds the old spec at (c) as well; the round-1 measurement showed AR test failures at (c).
> - **Fix:** write "at (a)–(c) the AR spec, and at (a)–(b) the G.4 spec, …". This is a tail/table-only change.
>
> **m3. `append-ar` does not check its inputs against `main`.**
> - **Problem:** it accepts a record path that does not exist; I tested `DOES_NOT_EXIST.md` and it went through. It also does not check that HEAD equals a freshly fetched `origin/main`. Both would fail closed later, at the launch's `check_host_record` and `verify_launch_tasl`.
> - **Fix:** before committing, require that `git show HEAD:<record>` exists with the given sha256 and that HEAD equals `origin/main`.
>
> **m4. `build` still force-resets the branch without checking for local changes.** It runs `checkout -q -f -B` with no dirty-worktree check. This is mitigated by the documented "never rerun after launch". **Fix:** refuse when `status --porcelain` is non-empty, as `append-ar` already does.
>
> **m5. Report §4, option A, has a formatting slip.** The two bullets added for M1 sit after a blank line, apart from the first list. **Fix:** merge them into the list.
>
> **Note, not a finding.** The round-1 scratch directory `/tmp/chainrev/_to_delete/` was gone when I started this round; someone else removed it. This round's scratch is in `/tmp/chainrev/_to_delete/round2/`. Nothing was written in `/tmp/pb/wt/chain`, `/tmp/pb/repo` or `/tmp/pb/wt/t1h` apart from the ignored `__pycache__` that the prescribed pytest command produces. The worktree HEAD is unchanged at `48cbe5cc`.
>
> ## Verdict
>
> ACCEPTED (minors m1–m5; none of them needs a rebuild of the chain commits (a)–(d)).

## Round 3 (`e320dfb2`)

> Reviewed base: e320dfb200ec19f4d5fd1fd8433a288ac3a34452
>
> ## Confirmation round: verdict NOT CONFIRMED
>
> The new m1 publication check can never pass for the amendment or note 2. That is the only remaining issue, and the fix is a few lines of report text.
>
> **What I checked:**
> - **Chain commits unchanged.** (a) `239281ab`, (b) `2c8b7902`, (c) `07a6c7f6` and (d) `462c29bf` are unchanged ancestors of the new tip. `e320dfb2~2` = `462c29bf`.
> - **Scope of the diff.** `git diff 48cbe5cc e320dfb2` touches only four files:
>   - `LAUNCH_TABLE.md`
>   - the report (`TASL_CHAIN_20261122.md`)
>   - `r1/tests/test_t1_tasl_chain.py`
>   - `sweep2/t1_tasl/build_launch_chain.py`
> - **Targeted tests.** 185 passed. The worktree is clean and HEAD is unchanged.
> - **Reproducibility.** In a scratch clone, `build` with the committed `build_config.json` and `tail_ref` = `wip-tasl-chain-tcode` (now `664ac185`) reproduced `e320dfb200ec19f4d5fd1fd8433a288ac3a34452` exactly.
>
> ## Round-2 minors
>
> - **m2 confirmed.** The LAUNCH_TABLE.md wording is corrected, both in the builder and in the generated table.
> - **m3 confirmed.** Before writing anything, `append-ar` now fetches `origin` and requires HEAD == `origin/main`. It then requires `git show HEAD:<record>` to exist with the given sha256. The new test covers the missing record, the wrong sha256 and HEAD ahead of `origin/main`, and shows HEAD and the worktree unchanged afterwards.
> - **m4 confirmed.** `build` refuses a dirty worktree (`status --porcelain`) before `checkout -f -B`. This is tested.
> - **m5 confirmed.** The report §4 option A list is merged.
> - **m1 not confirmed** (finding C1 below).
>
> ## Finding
>
> **C1 (major). The new publication check, `grep -n '<FILL\|PENDING' <note>` must print nothing, can never pass for the amendment or note 2.**
> - **Where:** report §3, "Before publishing a signed note".
> - **Amendment:** the grep always matches.
>   - P7 stays PENDING by design; that is what refuses the TASL-7 nodes under this note.
>   - The prose at lines 15–16 says "PENDING".
>   - P11 contains "its "spec sha PENDING" line predates the spec".
> - **Note 2:** the prose at lines 21 and 28 and the same P11 text always match.
> - **Third note:** the prose at line 14 ("Each is marked `<FILL …>` or `PENDING`") and line 32 also match. That note is checked by `check_note_ar` anyway.
> - **Why it matters:** the check is meant to be the only guard against an amendment signed with the erratum `<FILL …>` text still in P4. As written, it either blocks every G.1b publication or teaches the signer to ignore its output. Either way the round-2 m1 gap is still open.
> - **Fix (report text only; no rebuild of (a)–(d)):**
>   - For every note, a field-scoped scan that prose cannot trip: `grep -nE '^[A-Za-z0-9_]+ *:.*<FILL' <note>` must print nothing. No current prose line starts with a `key:` field, and the P7 template's `<path>`/`<date>` placeholders do not match `<FILL`.
>   - For the amendment and note 2 in addition: `grep -c '^P4: PASS — ' <note>` must print 1.
>   - Optionally add a chain test that runs this scan on the signed-form drafts: it should pass once P4 is filled and fail on a P4 that reads "PASS — …<FILL…".
>
> ## Verdict
>
> NOT CONFIRMED (C1 only; everything else is confirmed).
>
> On the scratch directory: thank you for clarifying. My round-2 remark about the missing round-1 scratch is withdrawn. This round's scratch is in `/tmp/chainrev/_to_delete/round3/`; round 2's is in `/tmp/chainrev/_to_delete/round2/`.

## Round 4 (`651dabd6`)

> Reviewed base: 651dabd68ff8079a2764618316d9c590c677b7c7
>
> ## Confirmation round 2: verdict CONFIRMED
>
> C1 is fixed: the new publication check is usable and closes the amendment gap from round-2 m1.
>
> **What I checked:**
> - **Chain commits unchanged.** (a) `239281ab`, (b) `2c8b7902`, (c) `07a6c7f6` and (d) `462c29bf` are the same commits, with tail `59ec0b8d` and table commit `651dabd6` on top.
> - **Scope of the diff.** `git diff e320dfb2 651dabd6` touches only three files:
>   - report §3 (`TASL_CHAIN_20261122.md`)
>   - `sweep2/t1_tasl/g1b_tasl_join.py`
>   - `r1/tests/test_t1_tasl_chain.py`
> - **No launch-path or spec change.** Nothing in `g1b_tasl.py`, `t1_tasl_node.sh` or the specs changed.
> - **Targeted tests.** 186 passed. The worktree is clean and HEAD is unchanged.
> - **Reproducibility.** In a scratch clone, `build` with the committed `build_config.json` (tail_ref `wip-tasl-chain-tcode`) reproduced `651dabd68ff8079a2764618316d9c590c677b7c7` exactly.
>
> **How the new check behaves:**
> - **What it refuses.** `g1b_tasl_join.publication_check` and its `publication-check` CLI refuse any `key:` field line that still has `<FILL`, using the field-scoped pattern. With `--p4` they also require exactly one `P4: PASS — ` line. Any problem gives exit code 2.
> - **Prose is ignored.** The prose lines in the drafts, P11's "spec sha PENDING" text and the amendment's intended PENDING P7 do not trip it.
> - **The test covers the needed cases:**
>   - the amendment and note 2 pass once P4 is filled;
>   - they are refused unfilled, and refused for "PASS — … <FILL: path>", through both the function and the CLI;
>   - the cross-check and G.4 drafts pass with `census_erratum` filled and are refused unfilled.
> - **The AR note.** Its `<FILL>` fields (`paper_commit`, `spec_sha256`, P2) are refused too, on top of `check_note_ar`.
> - **Report §3** prescribes the check for every note, with `--p4` for the amendment and note 2, and explains why a plain grep cannot serve.
>
> **Optional hardening (not blocking):**
> - `--p4` checks only that P4 reads PASS and has no `<FILL`. A signer could delete the erratum clause instead of filling it. It could also require P4 to cite `census erratum record docs/r1/…` with a 64-hex sha256.
> - The field regex uses ` *:`, while `g1b_tasl._note_fields` accepts `\s*:`. Using `\s*` would match exactly what the parser reads.
>
> ## Verdict
>
> CONFIRMED.
>
> Scratch for this round is in `/tmp/chainrev/_to_delete/round4/`; nothing was written in `/tmp/pb/wt/chain`, `/tmp/pb/repo` or `/tmp/pb/wt/t1h`.

## Round 5 (`806fd54d`)

> Reviewed base: 806fd54d67513e9da7bb191c3b44431c70becc8c
>
> ## Confirmation round 3: verdict CONFIRMED
>
> Both optional hardenings are in place, and nothing outside the tail changed.
>
> **Scope.** `git diff 651dabd6 806fd54d` touches only three files:
> - report §3 (`TASL_CHAIN_20261122.md`)
> - `sweep2/t1_tasl/g1b_tasl_join.py`
> - `r1/tests/test_t1_tasl_chain.py`
>
> (a) `239281ab`, (b) `2c8b7902`, (c) `07a6c7f6` and (d) `462c29bf` are unchanged. The new tail is `a3695aeb` and the table commit is `806fd54d`.
>
> **The field scan.** The pattern is `^[A-Za-z0-9_]+[^\S\n]*:.*<FILL` with `re.M`. It reads a key with any spacing before the colon, as `_note_fields` does, but cannot run onto the next line.
>
> **The P4 check (`--p4`).**
> - It needs exactly one `P4\s*: PASS — ` line.
> - That line must also cite `census erratum record docs/r1/\S+ sha256 [0-9a-f]{64}\b`.
> - When signed as instructed, the drafts' P4 text matches. The template "census erratum record <FILL: the path on main> sha256 <FILL> …" becomes "census erratum record docs/r1/reports/… sha256 <hex> …".
> - A deleted clause is refused, and so is a `<FILL` left in.
> - It stays fail-closed for spellings `check_note` would accept: "PASS - " with a hyphen is refused here.
>
> **Tests.** The new deleted-clause case returns exactly the expected single problem, and the `P4 :` spaced-key case is caught. The chain test passes (15 passed). The report wording matches the code.
>
> **One cosmetic nit (not blocking).** The changed docstring line in `publication_check` and the changed report §3 line run past the usual line width.
>
> ## Verdict
>
> CONFIRMED.
>
> Scratch for this round is in `/tmp/chainrev/_to_delete/round5/`; nothing was written in `/tmp/pb/wt/chain`, `/tmp/pb/repo` or `/tmp/pb/wt/t1h`, and HEAD is unchanged.

## Round 6 (`102a1cea`)

> Reviewed base: 102a1cea97c519582b4fe24f2aa1eb9a8a2272be
>
> ## Summary: verdict NOT ACCEPTED (one major, M1)
>
> The chain itself is correct, reproducible and refuses every AR launch. The one major finding is in the publication procedure, not in the chain: the notes could end up citing erratum-record bytes that no review covers. The fix is report text only. If the record is published byte-identical, (a)–(c) need not change.
>
> **Delivery shape (`git diff 3c3f822a 102a1cea`):**
> - (a) `dea2d4aa`, (b) `46a9dcd8` and (c) `09211381` each change exactly one spec file outside `docs/`, and each spec's `paper.commit` is its parent.
> - The spec changes are identical to the earlier accepted versions. Only the note drafts inside the commits changed, now carrying the erratum.
> - No code changes inside the chain.
> - The tail is `40599686` and the table commit is `102a1cea`.
>
> **Tests and reproducibility:**
> - Targeted tests: 186 passed. The worktree is clean and HEAD is unchanged.
> - In a scratch clone, `build` with the committed `build_config.json` and `tail_ref` = `wip-tasl-chain-tcode` (now `4198fa71`) reproduced `102a1cea97c519582b4fe24f2aa1eb9a8a2272be` exactly.
>
> **Launch matrix (four rows).** `launch_table.json` has four runs on three launch commits:
> - g1b-amendment and g1b-note2 on (a);
> - crosscheck on (b);
> - g4-pilot on (c).
>
> The matrix test checks all four rows from the base, from each launch commit and from docs-only children of each launch commit (reachable through a merge on `main`). Each run passes only from its own commit or that commit's docs-only child. Same-spec cells are refused by the tree rule; different-spec cells are refused by the run's own note check.
>
> **No AR launch from (a)–(c) or the tip.** The AR spec and the third-note draft are byte-identical to `main`'s, as the chain test asserts. Several independent layers refuse an AR launch:
> - `validate_spec` on the shipped AR spec STOPs with "the seven-node spec differs from the one the AR spec binds". I re-ran it.
> - With `launch=True` it first STOPs on `paper.commit` (still "TODO").
> - `verify_launch_tasl` needs a full paper commit.
> - `env_decision` and the host-check sha256 are still TODO.
> - The third-note draft keeps its `<FILL>` fields, which `check_note_ar` refuses.
> - `check_note` refuses an AR spec.
>
> Nothing else on `main` loads the AR spec; it is read only by `g1b_tasl.py`, the builder and the two test files.
>
> **Erratum citation:**
> - The record at `ac298f25` (`docs/r1/reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md`) has sha256 `9b40944be4df…`. That matches the config and every note.
> - Its values equal the chain's: `24cb3448…` (951 B) and `54d3a74d…` (959 B).
> - The review `T1_DATA_MANIFEST_ERRATUM_REVIEW_20261122.md` reads ACCEPTED and fixes the reviewed sha `9b40944b…`.
> - The amendment and note 2 cite record, sha256 and review in P4, which is now PASS. The cross-check and G.4 notes cite record and sha256 in `census_erratum`.
>
> **Signability.** Open fields are now only P7 (amendment and note 2) and none for the cross-check and G.4. `publication-check` passes all four drafts as shipped once signed.
>
> ## Findings
>
> **M1. The signature rule lets a note cite record bytes that no review fixed, and the review's conditions C1–C3 are not addressed.**
> - **Where:** report §2 ("If the published bytes differ from `ac298f25`'s, that sha256 is corrected in the notes at signature"), and the matching header bullet in the amendment and note-2 drafts ("correct P4 if the published bytes differ").
> - **The conflict:**
>   - The erratum review is ACCEPTED with editorial conditions. Its C1 reads: "If the record is published as the reviewed artifact, correct the node-file hash attribution (fmnist `e5005358…`, cifar10 `6ff99228…`) …". C2 asks for the §6 reproducibility sentence to be narrowed.
>   - The review fixes only `9b40944b…` ("this review fixes the reviewed sha `9b40944b…` only").
>   - Publishing the record unchanged leaves C1–C2 undone. Applying them changes the bytes.
>   - The current rule would then have the signer put the new, unreviewed sha into P4 and `census_erratum`. R1-T1-DATA-MANIFEST requires "an independently reviewed record".
> - **Fix (report and procedure text only):** state one of these two paths in §2/§3 before publication.
>   - **(i)** Publish the record byte-identical at `9b40944b…`, and handle C1–C3 in a separate addendum file beside it (confirmed by the erratum reviewer, or explicitly noted as editorial). The chain stays as built.
>   - **(ii)** Apply C1–C2 to the record, have the erratum reviewer confirm the new sha, then update `build_config.json` `erratum.sha256` and rebuild before publication. Nothing is published or launched yet, so a rebuild costs nothing.
>
>   In either case, replace "correct the sha256 at signature" with "the cited sha256 must be one a review fixes; otherwise STOP".
>
> **m1. The intermediate-commit disclosure omits the AR tests.**
> - **Where:** LAUNCH_TABLE.md (generated by the builder), which says "at (a)–(b) the G.4 spec still binds the old G.1b spec".
> - **Problem:** at (a)–(c), `main`'s own `test_t1_tasl_g1b_ar.py` also fails. It asserts that the seven-node spec's sha is `060aac91…`, and its "(d) deferred" adjustment arrives only in the tail.
> - **Fix:** add "and `test_t1_tasl_g1b_ar.py` (updated in the tail) at (a)–(c)".
>
> **m2. `publication-check` does not verify the cited record against `main`.**
> - Now that the drafts are fully filled, the one fact a signer must still check by hand is that the cited record exists on `origin/main` with the cited sha256. The draft bullet says to do this, but nothing mechanical does it.
> - **Fix:** have `publication-check` take every `docs/r1/… sha256 <64 hex>` citation in P4 / `census_erratum` and compare it with `git show origin/main:<path> | sha256sum`; exit 2 on a mismatch or a missing file. This also enforces M1's "STOP" mechanically.
>
> **m3 (informational). The report still says (d) follows "as one commit on top of the published (a)–(c)", but `append-ar` has been removed.** The (d) delivery therefore needs its own tooling and review. Until then, `main` after publication carries an AR spec that refuses to validate (this is disclosed). A sentence saying (d) is a separately reviewed delivery would help.
>
> ## Verdict
>
> NOT ACCEPTED (M1; minors m1–m3). M1 and m1 are report or table text only and need no change to (a)–(c) if path (i) is taken; m2 is a small tail-code addition.
>
> Scratch for this round is in `/tmp/chainrev/_to_delete/round6/`; nothing was written in `/tmp/pb/wt/chain`, `/tmp/pb/repo` or `/tmp/pb/wt/t1h`.

## Round 7 (`cd50e36f`)

> Reviewed base: cd50e36f55d45ad2aaeedc121d5dc11cb9c84718
>
> ## Summary: verdict ACCEPTED
>
> All round-3 findings are resolved; two small minors remain, neither needing a rebuild.
>
> **Delivery shape:**
> - (a) `34a5b1d6`, (b) `b5824240` and (c) `6ad899e0` each change exactly one spec file outside `docs/`, and each spec's `paper.commit` is its parent.
> - The spec content is unchanged from round 3 except for `paper.commit` following the new parent shas.
> - (a) changed only in the drafts' erratum header bullet.
> - No code changes inside the chain. The tail is `7ce11040` and the table commit is `cd50e36f`.
>
> **Tests and reproducibility:**
> - Targeted tests: 187 passed. The worktree is clean and HEAD is unchanged.
> - In a scratch clone, `build` with the committed `build_config.json` and `tail_ref` = `wip-tasl-chain-tcode` reproduced `cd50e36f55d45ad2aaeedc121d5dc11cb9c84718` exactly.
>
> **Live check of the record citation.** I signed a scratch copy of the amendment and ran `publication_check(..., main_sha256=_main_sha256)` against this repo's real `origin/main` (`3c3f822a`, record not yet published), read-only through `git show`. It correctly reports "P4 cites …T1_DATA_MANIFEST_ERRATUM_20261122.md, which is not on origin/main". I did not run the CLI, because its fetch would write refs in `/tmp/pb/repo`.
>
> ## Round-3 findings
>
> **M1 resolved (path (i)).**
> - Report §2 now says the record is published byte-identical at `9b40944b…`, with C1–C3 in a separate addendum.
> - It also says the cited sha256 must be one a review fixes; otherwise STOP, with no correction at signature.
> - Path (ii) is offered to the author as an alternative.
> - The amendment and note-2 header bullets say the same, and "correct P4 if the published bytes differ" is gone.
>
> **m2 resolved.** `publication_check` checks every `docs/r1/… sha256 <64 hex>` citation in P4 or `census_erratum` against `origin/main`. A missing file or other bytes is a problem. Citations without a sha256 (the review paths) are ignored. The new test covers match, missing, other bytes and CLI exit 2.
>
> **m1 resolved.** The report and LAUNCH_TABLE.md now also name `test_t1_tasl_g1b_ar.py` failing at (a)–(c).
>
> **m3 resolved.** (d) is described as a separately built and reviewed delivery, and the report says the AR spec on `main` refuses until then.
>
> **Unchanged from round 3 and re-verified:**
> - **Launch matrix.** Four rows on three launch commits, with docs-only children and both refusal paths exercised.
> - **No AR launch.** The AR spec and the third-note draft are byte-identical to `main`'s; the AR spec refuses on the seven-node binding and on `paper.commit`.
> - **Signability.** The open fields are P7 only (amendment and note 2) and none for the cross-check and G.4.
>
> ## Minors (not blocking; tail only)
>
> **m1. `_fetch_origin` ignores a failed fetch.** It runs `git fetch` without checking the return code, so a failed fetch silently checks against a stale `origin/main`. A record that was present and matching on the stale `main` would then pass even if `main` has since changed. **Fix:** exit 2 when the fetch fails.
>
> **m2. The check proves the bytes on `main` match the note, not that they are the reviewed bytes.** A signer who edits the cited sha256 to match a changed record still passes; the "must be one a review fixes" rule is procedural. **Optional hardening:** also require the P4 / `census_erratum` sha256 to equal `erratum.sha256` in `docs/r1/reports/tasl_chain_20261122/launch_table.json` on `origin/main`. That would make the STOP mechanical.
>
> ## Verdict
>
> ACCEPTED (minors m1–m2, tail only; (a)–(c) need not change).
>
> Scratch for this round is in `/tmp/chainrev/_to_delete/round7/`; nothing was written in `/tmp/pb/wt/chain`, `/tmp/pb/repo` or `/tmp/pb/wt/t1h`.

## Round 8 (`e740dae7`)

> Reviewed base: e740dae7c21aba456a07e1a5b30733e7a61d3711
>
> ## Verdict: CONFIRMED
>
> Both round-4 minors are fixed correctly, and nothing else moved.
>
> **Scope:**
> - (a) `34a5b1d6`, (b) `b5824240` and (c) `6ad899e0` are unchanged.
> - `git diff cd50e36f e740dae7` touches only three tail files: `sweep2/t1_tasl/g1b_tasl_join.py`, `r1/tests/test_t1_tasl_chain.py` and report §3.
> - The targeted chain test passes (15 passed). The worktree is clean and HEAD is unchanged.
>
> **m1 (failed fetch).** `_fetch_origin()` now returns whether the fetch succeeded. The CLI stops with exit 2 and "git fetch origin failed" before checking anything. This is tested.
>
> **m2 (edited sha256).**
> - The CLI reads `erratum` from the published chain's `launch_table.json` on `origin/main`.
> - If that file is missing, it exits 2, which means the notes must be published after the chain.
> - `publication_check(..., erratum=…)` refuses a citation of the erratum record whose sha256 is not the reviewed one, even when `main`'s bytes match the edited sha256.
> - Tests cover the edited sha256 matching changed bytes (function and CLI), the chain not yet on `main`, and a failed fetch.
> - Report §3 matches the code.
>
> **One residual gap (optional, not blocking).** The reviewed-sha comparison runs only when the citation names exactly `erratum.record`. A note that cited the erratum under a different `docs/r1/…` path, with matching bytes on `main`, would pass. Fix: require P4's `census erratum record …` clause and the `census_erratum` field to name exactly `erratum.record`.
>
> Scratch for this round is in `/tmp/chainrev/_to_delete/round8/`; nothing was written in `/tmp/pb/wt/chain`, `/tmp/pb/repo` or `/tmp/pb/wt/t1h`.

## Round 9 (`bd924c58`)

> Reviewed base: bd924c5862c98f2770e6b5d353d0240b3bcfd06d
>
> ## Summary: verdict ACCEPTED
>
> (d) is correct and launchable once published; there are three minors and a list of publication actions below.
>
> **Branch shape.** The branch adds three commits on `570ae410`, which is the delivered (a)–(c) plus the review record:
> - (d) `aa01bbc7`
> - tail `94cb31b9`
> - table `bd924c58`
>
> **(a)–(c) unchanged.** `34a5b1d6`, `b5824240`, `6ad899e0` and `e740dae7` are ancestors of the tip. `570ae410` adds only the review record under `docs/`.
>
> **Tests and reproducibility:**
> - Targeted tests: 188 passed. The worktree is clean and HEAD is unchanged.
> - In a scratch clone, `build_launch_chain_ar.py build` with the committed `build_config_ar.json` (`tail_ref` = `wip-tasl-chain-ar` @ `3a8ea522`, record read from `ebb86248`) reproduced `bd924c5862c98f2770e6b5d353d0240b3bcfd06d` exactly.
> - The builder checks the record's bytes, its sha256, the PASS fields, and that the harness pin equals the AR spec's, all before writing.
>
> **The (d) spec change.** (d) changes only `sweep2/t1_tasl/g1b_tasl_ar_spec.json` outside `docs/`, in exactly five fields:
> - `seven_node_spec.sha256` → `7ff3c95b…` ((a)'s re-issued spec);
> - `paper.commit` → `570ae410` (= (d)'s parent);
> - `env_decision.authority` → R1-G1B-AR-ENV, with the 3.12.15 interpreter per R1-G1B-AR-PY;
> - `hosts.TASL-2.env_python_comment` → the same, in words;
> - `hosts.TASL-2.isolation_host_check.sha256` → `cce9b8fb…` (the record path was already in the spec).
>
> The environment fields themselves are untouched: `env_python` `…/ar-cond7a/bin/python`, `python: 3.12.15`, and `freeze: env/ar-cond7a.freeze.txt`.
>
> **R1-G1B-AR-PY.** I read the row on `main` `52f4e3e5`. It re-points the venv's interpreter symlinks to uv's versioned CPython 3.12.15, and says "the freeze, spec, note and procedure stay unchanged (Python 3.12.15)". (d) changes only comment and authority text to mention it. `ROW_ID` parses the authority to R1-G1B-AR-ENV, the row `launch` checks with `check_env_row`.
>
> **Host-check record.**
> - At `ebb86248` its sha256 is `cce9b8fb…`.
> - Lines 9–12 are exactly `host_check_host: TASL-2`, `host_check_harness_commit: 2d09f9a9…`, `host_check_items: 1-7 PASS` and `host_check_verdict: PASS`.
> - With a stubbed `main` holding those bytes, `T.check_host_record` passes for the shipped spec.
> - Its own review chain ends with R4: ACCEPTED for exactly sha `cce9b8fb…`.
>
> **Note 3.**
> - With a stubbed `main` (the record plus `PLAN.md` from `c870179d`), `validate_spec(launch=True)` passes and `check_env_row('R1-G1B-AR-ENV')` passes.
> - `check_note_ar --draft` passes on the shipped draft, and `check_note_ar` strict passes once `approved: true`.
> - Every launch row is on `main` `c870179d`: the AR_PLAN_ROWS, R1-G1B-NOTE2-DECISIONS, R1-G1B-AR-ENV and R1-G1B-AR-PY.
> - P3 cites `TRACKG_T1_AR_HARNESS_REVIEW_20261122.md` (ACCEPTED, on `main`).
> - P4 cites `G1B_AR_SPEC_SUPPORT_REVIEW_20261122.md` (ACCEPTED at `6617d8cb`, confirmed at `740c48f3`, on `main`) plus the chain review.
> - P7 cites R1-G1B-AR-ENV "amended by R1-G1B-AR-PY", which satisfies the env_row citation `check_note_ar` requires.
>
> **Launch matrix.** The test now has five rows. `g1b-ar` passes only from (d) and its docs-only child; it is refused from the base, (a), (b) and (c) (different spec → note refusal) and from the other runs' children.
>
> ## Findings
>
> **m1. The R1-G1B-CAP sum is not stated in terms of what will actually run.**
> - **Where:** report §7, and the note-3 P8 / projection line.
> - **Problem:** the AR projection's total (58.589; sensitivity 85.96) uses the code constant `crosscheck 2.1`. That figure now stands for xc2, the full rerun. The GPU time the first cross-check already spent is outside the sum, as are `mlgym_fmnist`'s two infrastructure attempts (0.0128 GPU-h). The first cross-check spend is one sealed 10-run default part on TASL-7 plus one zero-row attempt; the STOP memo gives no GPU-h figure, but it is minutes.
> - **Effect:** the total is still well within 100 GPU-h, including under sensitivity, but nothing says so.
> - **Fix:** one sentence in §7 saying that 2.1 is xc2 and that the spent first cross-check and fmnist attempts add under 0.2 GPU-h, so the total stays within cap.
>
> **m2. P2 does not cite the host-check record's review.**
> - P2 cites the record and its procedure, but not the record's own review chain: `TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_REVIEW_R4_20261122.md`, which ACCEPTED sha `cce9b8fb…`. The first note's P2 cited its host-check review.
> - **Fix:** add "(review …_R4_20261122.md, ACCEPTED for this sha)" to P2 in the signed copy, or in a docs-only update of the draft. Neither changes the launch binding.
>
> **m3. P4 cites a review file that does not yet cover (d).**
> - P4 cites `docs/r1/reviews/TASL_LAUNCH_CHAIN_REVIEW_20261122.md` for "the spec's re-binding". At `570ae410` that file covers only (a)–(c).
> - **Fix:** append this (d) review to it, or add a sibling review file and cite that, before the author signs note 3.
>
> ## What the coordinating chat must do at publication
>
> 1. Publish the host-check record byte-identical (`cce9b8fb…`) on `main`, with its captures and the R1–R4 and STOP reviews: merge `main-t1-ar-pin-binding-20261122` @ `ebb86248`. It sits on `52f4e3e5`, so this is a merge, not a fast-forward, onto `c870179d`. `check_host_record` reads the record from `origin/main` at launch.
> 2. Merge `mac-tasl-chain-ar-20261122` into `main` with a merge commit, never squash or rebase. This publishes (a)–(c) and the review record unchanged, together with (d).
>    - The first delivery's publication rules still apply: the erratum record byte-identical at `9b40944b…` plus its addendum, and `publication-check` for the amendment, note 2, the cross-check and G.4.
>    - (d)'s code equals the base's, so `verify_launch_tasl` from (d) needs only (d) to be an ancestor of `origin/main`.
> 3. Put the (d) review on `main` (m3).
> 4. Note 3 is the author's signature:
>    - first `g1b_tasl.py check-note-ar <spec> --note <unsigned copy> --draft`;
>    - then publish it byte-identical as `docs/r1/authorizations/g1b_ar_t1_tasl_<date>.md`;
>    - then run the strict check;
>    - then launch from (d) or a docs-only descendant, with the note copied from `origin/main` into `docs/r1/authorizations/`.
> 5. **Operational (informational).** The AR job holds TASL-2's GPU lease for about 28 wall-hours. A busy lease is a STOP, not a wait, so schedule it around the `mlgym_fmnist` amendment, xc2's TASL-2 side and the G.4 pilot.
>
> ## Verdict
>
> ACCEPTED (minors m1–m3; none needs a rebuild of (d), and m2/m3 are docs-only).
>
> Scratch for this round is in `/tmp/chainrev/_to_delete/round9/`. Nothing was written in `/tmp/pb/wt/chainar` or `/tmp/pb/repo`; no fetch was run.

## Round 10 (`8c9611c1`)

> Reviewed base: 8c9611c1eedf9f8aa8796caddd6dfc54d39658c1
>
> ## Confirmation round for (d): verdict CONFIRMED
>
> All three minors are handled, and nothing else changed.
>
> **Scope:**
> - (d) `d52c9d9d` sits on `570ae410`, followed by tail `a2b8c539` and table `8c9611c1`.
> - The AR spec bytes are identical to round 9's: the diff over `sweep2/` against `aa01bbc7` is empty, with `paper.commit` still `570ae410` and spec sha256 still `65da95db…`.
> - (d) differs only in the note-3 draft: P2 now also cites `TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_REVIEW_R4_20261122.md` "ACCEPTED for this sha256".
> - The tree diff against `bd924c58` is limited to:
>   - that P2 line;
>   - the builder's matching `REVIEW_HC` constant;
>   - one test assertion;
>   - the (d) commit sha in `LAUNCH_TABLE.md` and `launch_table.json`;
>   - report §7.
>
> **Tests and reproducibility:**
> - The targeted g1b_ar and chain tests pass (85 passed). The worktree is clean and HEAD is unchanged.
> - In a scratch clone, `build_launch_chain_ar.py build` with the committed `build_config_ar.json` reproduced `8c9611c1eedf9f8aa8796caddd6dfc54d39658c1` exactly.
>
> **The minors:**
> - **m1 (cap):** confirmed. Report §7's new "R1-G1B-CAP" paragraph says the 2.1 is xc2. It adds that the already-spent first cross-check part and the `mlgym_fmnist` attempts come to under 0.2 GPU-h, so the total stays within 100 GPU-h, also under sensitivity.
> - **m2 (P2 review citation):** confirmed. The note-3 test asserts the new citation.
> - **m3 (P4 review file):** accepted as a condition. P4 still cites `TASL_LAUNCH_CHAIN_REVIEW_20261122.md`. §7 already says that file covers (d), which is true only once you append round 9 and this confirmation to it, as you plan, before delivery and before the author signs note 3.
> - **Publication items:** merging `ebb86248` (the record and its R1–R4/STOP reviews) and the TASL-2 lease scheduling are now in §7.
>
> ## Verdict
>
> CONFIRMED, on condition that the (d) review is appended to `TASL_LAUNCH_CHAIN_REVIEW_20261122.md` before delivery.
>
> Scratch for this round is in `/tmp/chainrev/_to_delete/round10/`; nothing was written in `/tmp/pb/wt/chainar` or `/tmp/pb/repo`, and no fetch was run.

---

Code-Commit: 8c9611c1eedf9f8aa8796caddd6dfc54d39658c1
Verdict: ACCEPTED

Accepted: the first delivery (a)–(c) at `cd50e36f` (confirmed `e740dae7`) and the second delivery (d) at `bd924c58` (confirmed `8c9611c1`); every note stays `approved: false`.
