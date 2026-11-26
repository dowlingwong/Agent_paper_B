Reviewed base: `0de83108` (the accepted P.4 H200 draft line `3eeccf9a` merged with published `main` `adeccc29`); accepted at `48592edd69180f0a0490b05584d4c972fd2d3ab0`

# Independent review record — Track P P.4 phase 1: the draft edits of R1-TRACKP-P4-DECISIONS (revision 4.2), micro-batch 8, and the evaluator tests after the merge

**Unit.** On `mac-trackp-p4-p1-20261121`: `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md` (revision 4.2, approved: false),
`r1/scripts/configs/trackp_htcondor_v2.json` (`sft.micro_batch` 16 → 8), `r1/tests/test_trackp_sft_test_eval.py` (main's release-lock and
P3-gate fixtures) and `docs/r1/reports/trackp_p4_p1_20261122/TRACKP_P4_P1_EDITS_20261122.md`. Authority: R1-TRACKP-P4-DECISIONS and the decision
list `TRACKP_P4_PHASE1_DECISIONS_20261121.md`, R1-TRACKP-IMAGE-V21, R1-S2-LABELS-TRAINDEV-RELEASE, R1-SWEEP2-RELEASE-DECISIONS, the frozen
sweep-2 preregistration (PRE-SPLIT A, PRE-STAGE A); the queue of 21 Nov 2026 (22:44), item 4.

**Process.** One independent reviewer for all three rounds (round 1 resumed after an API limit), read-only, synthetic data only, scratch
under `/tmp/rev_p4p1/` moved to its `_to_delete/`. Round 1 found two majors (nothing tied the receipted partition to the frozen block or to
the note's `labels:` lines; three evaluator tests failed after the merge with main) and eleven minors; round 2 accepted with two wording
leftovers (fixed in `48592edd`); round 3 confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `1fd7dd20` | NOT ACCEPTED (M1, M2; minors 1–11) |
| 2 | `ccadcedc` | ACCEPTED (n1, n2) |
| 3 | `48592edd` | CONFIRMED |

**Open items.** The prerequisites of §7 before signature: P1 (the sweep-1 label freeze and the train/dev release receipt, its source block equal to `cdae9c3f…`), P2 (per-base P.3a records), P3 (the P.4 runner unit, pinning `labels:`, `label_receipt:` and the source block; full clone), P5 (image v2.1: diagnostic job, I2/I3, the staged smoke and E0, the SFT probe at micro-batch 8), P7 (config check; the host config's image fields updated to the v2.1 digest). Author question if a prebuilt `causal_conv1d` wheel changes the env3 freeze line.

## Round 1 (`1fd7dd20`)

> **NOT ACCEPTED**
>
> Unit: `mac-trackp-p4-p1-20261121` @ `1fd7dd2045dea42c595e9efb6af2264b74c45bf5`. I reviewed `git diff 0de83108 1fd7dd20`, which touches 3 files: the draft (213 lines changed), the edits report (+61) and `trackp_htcondor_v2.json` (±4). The worktree is still clean at that commit.
>
> The draft edits themselves are mostly correct and complete. There are no BLOCKING findings. Two MAJOR findings need fixing before acceptance:
> - **M1:** a gap in the new label-source STOP and in the P3 binding.
> - **M2:** a test regression created by the merge. The draft's §5 cites those tests as passing.
>
> ## BLOCKING
> None.
>
> ## MAJOR
>
> **M1. The new label-source STOP mixes code refusals with checks no code makes, and nothing ties the partition to the frozen block.**
> - **Where:** `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md:230-233` (§4) and `:310` (P3).
> - **What `LabelBlockSource` → `release.open_partition` actually refuses** (`r1/c3/train/sft_data.py:198-276`, `r1/c3/release.py:602-647`):
>   - a file name other than `label_block.jsonl` or `label_block.traindev.jsonl`;
>   - a raw block, through `guard_raw_label_path(...,"T0")`, until the T0 test row exists;
>   - a missing or invalid `RECEIPT.json`: schema, source, stage or tier, the outputs set, or the release-row bindings (`decision_sha256`, `prereg_sha256`, `builder_sha256`, `gate_sha256`, `split_sha256`, `release_commit`);
>   - an output sha256 that differs from the receipt;
>   - P3 membership, or counts that differ;
>   - `completion.label_block_sha256 != receipt.inputs.label_block_sha256`.
> - **What it does not check:**
>   - That the partition or receipt sha256 equals the note's `labels:` / `label_receipt:` lines. `LabelBlockSource` never passes `receipt_sha256` to `open_partition`.
>   - That `receipt.inputs.label_block_sha256` equals the frozen `cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca`. The receipt "source block by sha256" is only checked against itself.
> - **Line 230 is ambiguous now.** It still says "The label block's sha256 differs from its freeze record", but phase 1 never reads that block.
> - **Why it matters:** the link from the frozen labels to the rows the job trains on is enforced by no code and by no explicit STOP or prerequisite. A partition released from another (unfrozen) block with a valid receipt would pass every code check.
> - **Fix:**
>   - Reword line 230: "the release receipt's `inputs.label_block_sha256` differs from the freeze record (`cdae9c3f…`), or the freeze is not signed."
>   - In the new STOP, mark which refusals `LabelBlockSource` makes and which the job makes.
>   - Add to P3: the runner pins the note's `labels:` sha256, the `label_receipt:` sha256 (for example through `open_partition(receipt_sha256=…)`) and the source block `cdae9c3f…`, and STOPs on any mismatch.
>
> **M2. After the merge, 3 of the 48 evaluator tests fail. §5 still says the evaluator is "implemented and tested (48 tests)".**
> - **Where:** `r1/tests/test_trackp_sft_test_eval.py` (draft line, unchanged by the merge); draft `:254-257`.
> - **Command:** `AR_HARNESS_ROOT=/tmp/pb/wt/t1h TMPDIR=… pytest -q r1/tests/test_trackp_sft_test_eval.py`
> - **Result:** 3 failed, 45 passed.
>   - `test_policy_version_sweep_and_completion_refusals`
>   - `test_phase1_refuses_a_real_label_test_read_and_the_real_path_opens_no_evaluation_file`
>   - `test_real_labels_need_a_recorded_sweep_index`
> - **First error:** `ReleaseStop: raw audit files (label_block.jsonl) are not read before R1-S2-LABELS-TEST-RELEASE (PRE-STAGE A)`. The release lock came from main: `guard_raw_label_path` appears 0 times in `3eeccf9a`'s sft_data.py and 2 times in `adeccc29`'s.
> - **Second error:** with that lock bypassed, the same tests fail with `SFTDataError: real labels are built only on the signed P3 split file`.
> - **Cause:** main's `test_trackp_sft.py` has the autouse `_after_test_release` fixture and the `p3_gate_bypassed` fixture. The evaluator tests have neither.
> - **Check:** in a scratch copy with both fixtures added, all 48 pass. So the evaluator code is fine; the tests are stale.
> - **Why it matters:** one of the failing tests checks the enforcement of P4-PHASE1-TEST A ("the evaluator enforces this", draft §2). Publishing this branch would put failing tests on main. The edits report records no test run.
> - **Fix:** a small reviewed test edit that adds the two fixtures, as `test_trackp_sft.py` does. Then rerun the file and keep or correct the "48 tests" claim.
>
> ## MINOR
>
> **m1. Stale "proposed"/"recommended" text contradicts "decided".**
> - `:206`: "*(proposed)* 1.6 × the cap". The slot-hour bound is decided by P4-CAP A, and line 24 says "(proposed)" values are replaced by measurements, which this one is not.
> - `:201`: "one reason A is recommended".
> - `:149`: P4-MB B says "16 … as the config has it". The config now says 8.
> - Fix: say decided (P4-CAP A, P4-JOB A), and for B say "as the config had it".
>
> **m2.** `:242-243` (identity STOP): "a … label-block sha256 that differs from the job spec" should name the receipted partition and its receipt.
>
> **m3.** `:109` and `:304`: "`r1/c3/release.py --stage traindev --source sweep1`" is not a runnable command. The real form is `python -m r1.c3.release --stage traindev --source sweep1 --table … --audit … --out <release root> --paper-root … --index … --classification …`; the sweep-1 integrity check needs the last three (`release.py:678-696`). Give the full form, or say "the release step for sweep1/traindev".
>
> **m4. The job's repo checkout must be a full clone.**
> - `:157` (P4-JOB) and P3: on every open, `open_partition` → `release_row` runs `git ls-tree`/`show` at HEAD and `git merge-base --is-ancestor <release_commit> refs/remotes/origin/main` (`release.py:142-176`, `:345-351`).
> - So the clone inside the HTCondor job must not be shallow and must have `origin/main` fetched; otherwise every label read STOPs.
> - Add this to P3/P4-JOB.
>
> **m5. The host config's image fields still say v2.**
> - `trackp_htcondor_v2.json` still has `image.gpu` = `sha256:b1144ece…`, `"host": "HTCondor GPU (image v2)"`, and v2 comments.
> - The draft (`:66-67`) only says "the image named in the job spec becomes v2.1". No Python reads `image`, so nothing breaks. But the host-config sha256 that the note records would describe a v2 image.
> - Add to P7: update `image.gpu` and the comments to the v2.1 digest before the launch commit.
>
> **m6. R1-TRACKP-IMAGE-V21 is not carried over completely.**
> - Its "If the diagnosis points elsewhere, STOP and return to the author" is missing from §4/P5. `grep diagnos` finds only the diagnostic job.
> - Its "no other dependency change" is also not stated. §1 has it only implicitly, through the env3 STOP.
> - If v2.1 adds a prebuilt `causal_conv1d` wheel, say how the R1-HTC-QTORCH "sorted diff empty" freeze check applies. It is an author question if the wheel changes the freeze line.
> - `:349`'s placeholder and `:129` say only "v2 plus a C compiler"; add "(and a prebuilt causal_conv1d wheel if one fits)".
>
> **m7. E0 never ran on v2.**
> - `:64`, `:44` and P5 `:318-320` say v2.1 "reruns … the smoke and E0". But c33aa647's message says "E0 not run" on v2.
> - Say "E0 runs on v2.1 for the first time (not run on v2)", or use the PLAN wording ("the staged smoke and E0 unchanged").
>
> **m8.** `:328`: "on `main` since `16e0b52c`" is wrong. R1-T1-HOST-TASL was already in PLAN at the first-parent commit before `16e0b52c` and first appears on main's first-parent line at `e5e452a0`; `eb8b21cf` and `4aac5209` lack it. Write "on main (since `e5e452a0`; verified at `adeccc29`)".
>
> **m9. Universe wording.**
> - `:99` says "the file is both the universe and the assignment (9 test, 3 dev, 6 train per node)". The file holds 240 instances, with 6/2/4 on the T1 nodes.
> - A build's universe is the file's instances of the table's nodes (`sft_data.p3_universe`): 144 = 8 × 18 for T0, as §3 `:213` correctly says. Reword to match.
>
> **m10. Two small §1 omissions.**
> - `:39` R1-SWEEP2-PREREG row: "a reader opens only a receipted partition" should add "until the T0 test release row" (as `:69-70` does).
> - §1 does not cite R1-SWEEP2-RELEASE-DECISIONS (REL-SCOPE A, REL-CODE A; sweep 1 releasable now), which governs the release step P1 depends on.
>
> **m11. Edits report wording.**
> - `TRACKP_P4_P1_EDITS_20261122.md:49` says "No code path reads the host config's micro-batch at desk time".
> - `trackp.py:357-367` (`sft-dev`) does read `sft.micro_batch` from the `--config` file at run time, and the SFT probe will use it. Not wrong, but say so.
>
> ## Verified sound
>
> **Decision list and PLAN row coverage.**
> - All 8 decisions are marked decided, as recommended.
> - P4-LABELS is a new section; B of P4-P1SPLIT is marked not buildable on real labels.
> - §1's base is `adeccc29`, which equals current `origin/main`.
> - `split:` and `split_file:` say P3 only.
> - `labels:` gives the release partition with a receipt line and the source block.
> - The new §4 STOP exists (but see M1).
> - P1 adds the release receipt; P3 binds `split_file` and `LabelBlockSource`; P8 is PASS; P2, P4, P5 and P7 otherwise carry over. P6 is PASS.
> - R1-TRACKP-P4-DECISIONS: decisions, the "14–19" projection and the start gate are reflected.
>
> **No salt-mode wording.** `grep salt|c3_p3_split/v1|fixed instance` on the draft finds nothing. The only `trackp_sft/v1` hit is option B, marked not buildable.
>
> **Split file and prereg.**
> - `sha256sum r1/c3/splits/c3_p3_split_v1.json` = `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`. This equals `SIGNED_SPLIT_FILE` (`sft_data.py:466-467`), `p3_split.P3_SPLIT_SHA256`, the prereg's final block and the PLAN release row.
> - Prereg sha256 = `aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5`. Its block has `frozen: true` and `pre_stage: A`.
> - The release commit `a9d8ff5e…` is an ancestor of main.
>
> **Release layout and receipt fields match release.py.**
> - Layout: `out_root/<source>/<stage>/label_block.traindev.jsonl` + `RECEIPT.json` (`release.py:513`, `:595`).
> - The receipt binds the decision text, prereg, split and source block by sha256 (`decision_sha256`, `prereg_sha256`, `split_sha256`, `inputs.label_block_sha256`). The partition sha256 is in `outputs`.
>
> **Cap arithmetic, recomputed.**
> - 9 + 3 × 750/590 = 12.81 full-run equivalents.
> - One full run: 590 × 5/16 = 184 steps × 1.26 s ≈ 3.87 min.
> - That gives 0.826 h per 0.8B base. Training total: 1.65 + 8.26 = 9.9 GPU-h at 5×, and 1.65 + 13.2 = 14.9 at 8×.
> - Adding startup (≤ 2) and the probe (≤ 2) gives ≈ 14 / ≈ 19.
> - A repeated 4B job: 0.826 × 8 = 6.6 GPU-h.
> - `slot_hours_cap` 64 = 1.6 × 40.
>
> **Image v2.1.** No v2.1 digest is invented. §8 keeps a placeholder, and "No v2.1 digest exists yet" is stated. §1, §2 host, §4, P5 and §10 all point to v2.1 under R1-TRACKP-IMAGE-V21.
>
> **Claims of what exists.**
> - I2/I3 v2 passed and the smoke failed `kernels_bound`: supported on main by the R1-TRACKP-IMAGE-V21 PLAN row text. The records themselves (`6de736bd`, `c33aa647`) are on `origin/trackp-h200-20261118` only, not on main; the draft attributes them correctly.
> - The P3 unit `84b86b83`, the release unit `275d7dcb` and `16e0b52c` are all ancestors of `adeccc29`. The locks are in main's code.
>
> **Placeholders in §8** (release root, partition and receipt sha256, freeze record, host-config sha256, v2.1 digest, `VERSIONS.txt` sha256, smoke/E0 and probe records, `code_commit`) are all values known only later. Legitimate.
>
> **Config change.**
> - The JSON parses. `micro_batch` 8 divides effective 16.
> - The `sft` keys `micro_batch` and `comment` are the only ones `trackp.py` allows.
> - Host-config sha256: `ef9d356aa7e7e5387254d1b31eaca99865783129483231d17a18ce0132728525` (before) → `d53681c91a18859113fa36aad6ca9529f73bf8ee8587ae7ce385c1dbf0a7ef68` (after).
> - Readers: `r1/scripts/trackp.py` (`--config`) and `r1/tests/test_trackp_sft.py:593`, which does not pin `micro_batch`. No other code reads the file.
> - `pytest -q r1/tests/test_trackp_sft.py`: **35 passed**.
>
> **Merge 0de83108.**
> - Parents are `3eeccf9a` and `adeccc29`.
> - `git diff adeccc29 0de83108` shows exactly the 5 draft-line files. Their blobs are identical to `3eeccf9a`'s.
> - No file was changed on both sides. Main's content only, with no conflict edits. The one consequence is M2.
>
> ## Scratch
> Everything is in `/tmp/rev_p4p1/_to_delete/`:
> - `t/` is the TMPDIR.
> - `tcopy/test_eval_fixed.py` is the evaluator test copy with the two fixtures added, used for M2.
>
> Nothing under /tmp/pb was modified, committed or deleted. I opened no label, evaluation, sealed or secret file. No memory content was used.

## Round 2 (`ccadcedc`)

> **ACCEPTED**
>
> Round 2 covers `mac-trackp-p4-p1-20261121` @ `ccadcedc112b4ee249790c6a2c5cd3d8f2c0f52a`. I reviewed `git diff 1fd7dd20 ccadcedc`, which changes 3 files (+83/−31): the draft, the edits report and `r1/tests/test_trackp_sft_test_eval.py`. The worktree is clean at `ccadcedc`.
>
> All round-1 findings are resolved. Two small wording leftovers remain; neither blocks acceptance.
>
> ## BLOCKING
> None.
>
> ## MAJOR
> None.
>
> ## MINOR (new or leftover; optional)
>
> **n1. "reruns … E0" is still in two places** (rest of m7).
> - `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md:45`: the §1 R1-TRACKP-IMAGE-V21 row says "v2.1 reruns I2, I3, the smoke and E0 unchanged".
> - `:140`: the host paragraph says the smoke and E0 are "rerun on image v2.1".
> - The fixed places (`:64` and P5) now correctly say that E0 runs on v2.1 for the first time.
> - **Fix:** write "reruns I2 and I3, then runs the staged smoke and E0 unchanged", as the PLAN row has it.
>
> **n2. One item in the §4 list is slightly wrong** (`:238-242`, the "refused by `LabelBlockSource`" list).
> - It says "P3 membership or counts other than the split file's".
> - `open_partition` checks membership against the split file, but it checks counts against the receipt's `counts.released_label_rows` (`release.py:642-645`), not the split file.
> - **Fix:** "P3 membership other than the split file's, or row counts other than the receipt's".
> - The list also leaves out some refusals: label seeds other than 7001–7005, a sweep or index mismatch, and a classification mismatch. That is acceptable for a summary list.
>
> ## Round-1 findings, checked
>
> **M1, resolved.**
> - §4's freeze STOP now applies to the receipt's `inputs.label_block_sha256`, which must match `cdae9c3f…9aca`; the job checks it.
> - The label-source STOP is split. The `LabelBlockSource`/`open_partition` half matches the code (`sft_data.py:198-276`, `release.py:602-647`), apart from n2. The job half covers `labels:`, `label_receipt:` and the source block equal to the freeze.
> - P1 records the receipt sha256, and its source block must equal the freeze.
> - P3 makes the job pin all three, for example with `open_partition(receipt_sha256=…)`, and STOP on any mismatch. The `receipt_sha256` parameter exists (`release.py:602-616`).
>
> **M2, resolved.**
> - The test file imports `_after_test_release` (autouse) and `p3_gate_bypassed`, and applies the second to the whole module through `pytestmark`.
> - No test in that file uses `split_file`, `_signed_split` or the release lock, so the module-wide bypass does not hide a gate test. The gate is tested in `test_trackp_p3.py` and the lock in `test_c3_release.py`.
> - Test results:
>   - `pytest -q r1/tests/test_trackp_sft_test_eval.py r1/tests/test_trackp_sft.py`: **83 passed**.
>   - `test_trackp_sft_test_eval.py` alone: **48 passed**, so the imported autouse fixture works on its own.
>
> **Minor findings m1–m11, resolved.**
> - m1: no stale "(proposed)" or "recommended" text is left outside §9. The remaining hits at `:390` and `:397` are §9's open evidence-phase items, which is correct. Slot-hours read "1.6 × the cap (64; P4-CAP A)". P4-JOB reads "A was chosen". P4-MB B reads "as the config had it".
> - m2: the identity STOP names the receipted partition and the release receipt.
> - m3: the full `python -m r1.c3.release` command matches `main()`'s arguments.
> - m4: the full clone with `origin/main` fetched is stated in P4-JOB and P3, with the right reason.
> - m5: the host config's v2 `image` fields are listed in "What exists" and in P7.
> - m6: the diagnosis STOP, the rule of no other dependency change and the wheel/freeze author question are in §4, P5 and the host paragraph, and the wheel is in the §8 placeholder.
> - m7: fixed at `:64` and in P5, with the leftovers in n1.
> - m8: P8 reads "since `e5e452a0`; verified at `adeccc29`", which matches main's first-parent history.
> - m9: the universe wording matches the file (240 instances: 9/3/6 per T0 node, 6/2/4 per T1 node) and `p3_universe` (144 = 8 × 18).
> - m10: the prereg row now says "until the T0 test release row exists". The new R1-SWEEP2-RELEASE-DECISIONS row matches PLAN.
> - m11: the report's wording on the micro-batch reader is corrected.
>
> ## Verified sound (unchanged from round 1)
> - Split file sha256: `b5967dd7…e569`. Prereg sha256: `aa1a961b…7cc5`.
> - The cap arithmetic: ≈ 9.9 / 14.9 GPU-h of training, ≈ 14–19 GPU-h in total.
> - No v2.1 digest is invented.
> - The config is `micro_batch` 8.
> - Merge `0de83108` brought in main's content only.
> - No salt-mode wording is left in the draft.
>
> ## Scratch
> All scratch is in `/tmp/rev_p4p1/_to_delete/`: `t/` and `tcopy/` from round 1, and `t2/` (this round's TMPDIR). Nothing under /tmp/pb was modified, committed or deleted. I opened no label, evaluation, sealed or secrets file.

## Round 3 (`48592edd`)

> CONFIRMED: commit 48592edd69180f0a0490b05584d4c972fd2d3ab0 changes only 3 lines of the draft, and they fix n1 (lines 45 and 140) and n2 (§4) as described; no "reruns … E0" wording is left, the worktree is clean, and nothing was modified or deleted.

---

Code-Commit: 48592edd69180f0a0490b05584d4c972fd2d3ab0
Verdict: ACCEPTED

Accepted: the P.4 phase-1 draft revision 4.2, the micro-batch change and the evaluator test fixtures at `48592edd`; the note remains a draft (approved: false).
