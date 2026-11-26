Reviewed base: the P.4 runner at `bb1a9eb006c5` (READY 101; code identical to `4315ab295`); accepted at `8d2f61c7d` (rebased as `124e2613e`), confirmed at `924205cc45b128c865160a9688932b41399acc1b`

# Independent review record — the P.4 cluster test plan (runner cluster tests, the SFT probe per base at micro-batch 8 under the SFT authorization draft's §10, the fields the cluster fills)

**Unit.** On `mac-trackp-p4-testplan-20261124` (on READY 101's `bb1a9eb0`): `docs/r1/reports/trackp_p4_runner_20261122/P4_CLUSTER_TEST_PLAN_20261124.md`, docs only. It identifies "the draft's §10" as `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md` (rev 4.2) "## 10. Needs a cluster test (NEMO2 H200, image v2.1)", with the probe defined in that draft's §2 (one `sft-dev` per base, synthetic labels, micro-batch 8, at most 50 steps, peak memory and seconds per step), applied to image v2.2; gives exact commands, outputs, pass criteria and commit paths for the runner's cluster tests T0–T8 (with T1 a read-only NEMO2 H200 job reading `/opt/r1/VERSIONS.txt` and running the two unscoped `nvidia-smi` queries the job uses); specifies the probe, its probe-strength validation and the record format (`p4_estimate_hours: <arm> <hours>` per spec arm, as `p4_switch.check_probe_hours` requires), and the derivation of hours from seconds per step and P4-CAP; tabulates every TODO, TODO_VERIFY_ON_HOST, `<FILL…>` and PENDING field of the spec, the host config and the note draft with owner, source command and timing; gives the order of operations up to the phase-1 note's signature and STOPs S1–S18. Blockers found and stated: F1 no probe mode in the runner (and `sft-dev` records no peak memory; `seal` has no sealed-root option); F2 the published sweep-1 train/dev receipt `f06e37a9…` binds `inputs.proposals_sha256` `b713c423…` (the sealed v2 table) while `p4_lib.inputs` requires the `sweep1_v3` pin `d0048567…`, so every P.4 job STOPs at step 5 until the author decides the binding and a reviewed runner change lands (missed by the runner review, whose rounds predate the receipt); F3 unscoped `nvidia-smi` in the job; F5 tests pin today's placeholders; F6 the signed freeze record must be in `paper.commit`; F7 nineteen host-config placeholders; F8 the v2.2 run-record review is pending. Authority: the user's message of 24 Nov 2026 (15:58), item 3.

**Process.** One independent reviewer, read-only, own detached worktrees, desk commands only (`validate`, `validate --launch`, `--check-config`, `test_trackp_p4_runner.py` once), no data files opened. Round 1 accepted with eight minors; the author's fixes (rebased onto READY 101) were confirmed with one minor (n1, step order), which the coordinating session fixed; that confirmation found one inconsistency (n2, who decides F2), fixed and confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `8d2f61c7d` | ACCEPTED (minors m1–m8) |
| 2 | `2ae1491bd` | ACCEPTED (confirmation; minor n1) |
| 3 | `820821c8a` | NOT ACCEPTED (n2) |
| 4 | `924205cc4` | ACCEPTED (confirmation) |

**Open items.** Author decisions: the receipt/table binding for P.4 (F2; for example FEAT-ONE A applied to A5's phase-1 data), before the code commit and before any signature (S9); whether the at most 50-step synthetic probe counts as "no training run", before the probe; whether the probe's GPU-hours count against the 40 GPU-h cap. Engineering units needed: a reviewed probe mode (F1, §4.2) with probe-strength validation and a peak-memory record; the F2 runner change; scoping of the job's `nvidia-smi` queries if T1 shows more than one GPU (F3). Before the probe: the independent review of the v2.2 run records (I2 759993, I3 759994, smoke 759997, E0 760000), the host-config fill commit (19 placeholders, F5 test changes), T1's VERSIONS value. Cosmetic: two "Author decision" paragraphs at lines 830-833 run together in Markdown; step 4a renders as an indented paragraph.

## Round 1 (`8d2f61c7d`)

> Reviewed base: 8d2f61c7d (mac-trackp-p4-testplan-20261124; one docs-only commit on 4315ab295)
>
> ## Summary
> The plan is accurate: no invented command, flag or function, and no false claim about the code. The six blockers check out, the field table is complete, and the probe-hours derivation is explicit and matches the spec's `estimate` block, `projection` and P4-CAP. No major finding; eight minors.
>
> ## What I ran
> `p4_lib.py validate p4_spec.json`: ok (16.94 GPU-h, 24.41 slot-hours; walltime 6282 s for the 0.8B arms, 37656 s for the 4B arms; within the cap). `validate --launch`: `STOP: paper.commit must be filled`, rc 2. `trackp.py --check-config`: rc 1, exactly the plan's 19 placeholders. Host config `18f18cfc…`, spec `04cfd060…`. `test_trackp_p4_runner.py`: 89 passed.
>
> ## Verified
> - **Commands and flags.** Every quoted argparse line is exact (`p4_lib.py:969-972`, `p4_render_jdl.py:137-141`, `p4_switch.py:323-326`, `trackp_p4_test_path.py:28-31`, `trackp.py:446-490`). The §4.3 inner commands are exactly what `data_argv(synthetic=True)` and `sft_dev_argv(..., extra=("--steps","50"))` build, with `trackp()`'s `offline_env` and PYTHONPATH. T2–T4 library calls match; nvidia-smi, condor and apptainer options are real. The missing modes are missing (`p4_lib` has only `validate`/`job`/`seal`/`assemble`; `run_job` calls `validate_spec(launch=True)` at `:625`, which requires an `h200_sft_probe:` source at `:270`; `max_memory_allocated` only in `spike.py` and `trackp_gpu_smoke.py`; no sealed-root option on `seal`).
> - **§10.** Draft rev 4.2, `## 10` at line 404; the §10 and §2 quotes (≈ lines 135-143) faithful; the "no training run" tension stated (§0 item 2, §8 item 1); the probe reads no label, receipt, freeze record or test path; synthetic data holds no test rows. A probe cannot count as an arm (`check_run_protocol` `p4_lib.py:591` and `select_lr` `sft.py:179` refuse `protocol_deviation`; a synthetic `data_sha256` is refused; its run id keeps it out of `charged_hours`, `assemble`, `check_first_record`; `out.tar` holds no weights). The synthetic training count (≈ 593) is plausible (4,999 = 1,725 eligible + 3,274 duplicates + 0 no-ops; `SyntheticLabelSource` skips duplicates); S13 guards it.
> - **Field table.** Complete against every spec TODO, all 19 host-config values and every note `<FILL…>`/PENDING line; owners and commands right; the `config_digest` vs file-sha256 point is correct and important.
> - **Blocker 1 is real.** `RECEIPT_sweep1_traindev.json` (sha256 `f06e37a9…65c1`) has `inputs.proposals_sha256` `b713c423…57c4` (= `arms_freeze.SWEEP1_SEALED_PROPOSALS_SHA256`, the sealed B.2 v2 table); `p4_lib.inputs` (`p4_lib.py:449-453`) requires the `sweep1_v3` pin `d0048567…d1d5` from `trackp_sft.json`. Every P.4 job on the published release STOPs at step 5: the accepted runner (READY 82 / `4315ab295`) cannot run on the released data. The runner review missed it: round 1 minor 4 asked for this check (review lines 102, 182), but rounds 1–5 (22 Nov) predate the receipt (`e3536d839`, 23 Nov), and the 24 Nov update and review did not compare against it.
> - **Blocker 2 is real.** `gpu_identity` (`p4_lib.py:342-353`) and `run.foreign_compute_processes` (`run.py:150-156`) call `nvidia-smi` unscoped; the smoke and E0 stages scoped both (`--id="$GPU_UUID"` and the `nvidia-smi-scoped` shim); HANDOFF.md requires scoped NVML process checks.
> - **Other blockers and STOPs.** F5 tests exist (`test_trackp_p4_runner.py:266, 1246`); `verify_launch_p4` allows differences only under docs/ and in the spec. F6: no freeze file on 3024db3f. F7: 19 placeholders. F8: only the Dockerfile/workflow v2.2 review on main. S1–S18 match the code.
> - **Order of operations** sound up to signature.
> - **Probe-hours derivation.** `steps(m) = 5·ceil(ceil(m/8)/2)` matches `Trainer` (`trainer.py:136-139`); learning-curve points match `lc_points`; `H_a` through `projection` (startup 1800 s, wall factor 1.5); 15.67 h from 86,400 s; hours in (0, 20]; `check_probe_hours` tolerance 1e-9; the manual "probe GPU-h + projection ≤ 40" check fills a code gap.
>
> ## Minor findings
> - **m1** Lines 81, 348-349, 816-817: the plan does not say the accepted READY 82 runner cannot run on the released receipt or that the runner review missed it; nor that the non-preview T8 render (`check_inputs`, `p4_render_jdl.py:76-102`) and `p4_switch.check` do not check the receipt's table; S9's "validate --launch with these receipt values" suggests a gate that does not exist. Scenario: T8 PASS plus switch PASS taken as clearing the binding; the solo job STOPs at `inputs`, charged to the cap; re-signing needed.
> - **m2** Lines 64, 757, 850: who settles "no training run" is inconsistent (chat in §0/§6 step 1, author in §8 item 1); it is the author's.
> - **m3** Lines 461-463: the probe spec's validation is unspecified (launch strength cannot pass before the probe; default strength accepts a placeholder `versions_sha256` that `image_identity` rejects).
> - **m4** Lines 81 vs 764-770: the probe is tied to the F2 fix for no reason.
> - **m5** Lines 321-322 (T4): `… | tee …; echo "rc=$?"` without pipefail records tee's status.
> - **m6** Lines 601 vs 605-607: 2430 × 1.26 / 3600 = 0.8505 rounds up to 0.86, not "≈ 0.85".
> - **m7** Lines 216-220: F3 could be settled by T1 (the read-only H200 job could run the two unscoped queries); I3's `NVIDIA_VISIBLE_DEVICES=GPU-…` line in `i3_identity.txt` is relevant evidence.
> - **m8** Line 654 vs 648: "launch commit" used in two senses.
>
> ## Cleanup
> Worktree removed; scratch in /tmp/p4tprev/_to_delete/. Nothing committed or pushed; of the receipt only its sha256, `inputs`, `outputs` and `counts` read.
>
> VERDICT: ACCEPTED

## Round 2 (`2ae1491bd`)

> Reviewed base: 2ae1491bd (on 124e2613e, the rebased copy of 8d2f61c7d; parent bb1a9eb0)
>
> ## Summary
> The rebase changed no content, and all eight fixes are correct and consistent with the code. One sentence added by the m1 fix gets the job's step order wrong (n1); minor, not blocking. No data files opened; from the receipt only its `utc` key read.
>
> ## Rebase
> `124e2613e^` is `bb1a9eb006c523aa0ac604e34d672576f0a16142`; `git diff 4315ab295 bb1a9eb00 -- r1` empty; `git diff 8d2f61c7d 124e2613e -- docs` lists only `FULLSUITE_P4_TIP_4315ab29.txt` and `TRACKP_P4_RUNNER_V22_REVIEW_20261124.md` (bb1a9eb0's own docs commit); the plan byte-identical between `8d2f61c7d` and `124e2613e`; `2ae1491bd` changes only the plan (+164/−66).
>
> ## The fixes
> - **m1** correct apart from n1: `check_inputs` at `p4_render_jdl.py:79-104` never reads `inputs.proposals_sha256`; the table check at `p4_lib.py:449-453`; receipt `utc` 2026-11-23T09:23:16Z; S9 a manual gate before signature; step 4a gates the signature, not the probe; T5's note covers T5 and T8.
> - **m2** correct (author decides in §0 item 2, §6 step 1, §8 item 1; S4 gates the probe).
> - **m3** correct and matches `validate_spec` (default strength requires both controls and `first_arm == kev-0.8b`, `p4_lib.py:239-247`; `estimate.hours` keys equal the arms; placeholders accepted for `paper.commit`, `versions_sha256`, `host_config.sha256`; `sft_config.sha256` and the fixed label source, stage and block always required; probe-strength pins use `_pin(allow=False)` patterns; launch strength cannot pass before the probe; four arms, one per job, right; in the probe spec `paper.commit` names the host-config fill commit, stated).
> - **m4** correct. **m5** correct (`set -o pipefail`; `RC=${PIPESTATUS[0]}` in T4 and the T8 loop). **m6** correct (0.86). **m7** correct; the T1 commands are real and mirror `gpu_identity` and `run.foreign_compute_processes`; `gpu_visibility.txt` with `2>&1`; `transfer_output_files` valid; `i3_identity.txt` line 55 is `NVIDIA_VISIBLE_DEVICES=GPU-a853e181-…`. **m8** correct.
>
> ## New minor
> **n1** — plan lines 101 (F2) and 899 (S9) say the job STOPs at `inputs` "after staging"; in `run_job` `inputs` (step 5) runs before `stage` (step 6), `p4_lib.py:648-651`. Fix: "before staging".
>
> VERDICT: ACCEPTED

## Round 3 (`820821c8a`)

> Reviewed base: 820821c8a (parent 2ae1491bd)
>
> ## Summary
> The n1 wording is now correct, but moving the binding decision to the author contradicts §6 step 1 of the same plan.
>
> **Diff.** `git diff --stat 2ae1491bd 820821c8a` touches only the plan (2+/2−, lines 101 and 899); three word changes: "after staging," → "), before staging (`p4_lib.py:648-651`),"; "coordinating chat's" → "author's"; "it, after" → "it at step 5, before".
>
> **Wording.** Correct: `p4_lib.py:648-651` is `inputs(...)`, then the step append, then `stage(...)`.
>
> **n2 — "the author's binding decision" is inconsistent with §6 step 1.** Line 101 gives the binding to the author; step 4a (line 842) and S9 (line 896) and §8 item 9 are neutral; but §6 step 1 under "Chat decisions." (lines 824-825) still lists "The receipt/table binding for P.4 (F2; FEAT-ONE A applied to A5's phase-1 data), and the runner change it needs." Fix: move the F2 item out of "Chat decisions" to an "Author decision" paragraph ("the chat prepares the options and the runner change"); optionally name the author in step 4a and S9.
>
> VERDICT: NOT ACCEPTED

## Round 4 (`924205cc4`)

> Reviewed base: 924205cc4 (parent 820821c8a)
>
> ## Summary
> n2 is fixed; the plan gives the F2 decision to the author everywhere, and the commit changes nothing else.
>
> 1. **Only the plan changed.** `git diff --stat 820821c8a 924205cc4`: one file, 5 insertions, 3 deletions.
> 2. **F2 belongs to the author everywhere.** Line 101 "the author's binding decision"; line 825 (§6 step 1 "Chat decisions") "The options and the runner change for the receipt/table binding (F2); the decision itself is the author's (below)."; lines 832-833 new "**Author decision**, before the code commit: … The chat prepares the options and the runner change; it does not decide it."; line 844 "The author's F2 binding decision …"; line 898 "not decided by the author". Neutral lines (precondition table line 126, §8 item 9 lines 949-951, §9 m1 row line 959, field-table notes "Subject to F2"/"F2 first") name no decider. The "chat" owner entries for `paper.commit`, `labels.*` and the `labels:` line concern filling values.
> 3. **Nothing else changed.** Four hunks (825, 832-833, 844, 898), each as described.
>
> Cosmetic: lines 830-833 hold two "**Author decision**" paragraphs with no blank line between them.
>
> VERDICT: ACCEPTED

---

Code-Commit: 924205cc45b128c865160a9688932b41399acc1b
Verdict: ACCEPTED

Accepted at `8d2f61c7d`, confirmed at `924205cc4`.
