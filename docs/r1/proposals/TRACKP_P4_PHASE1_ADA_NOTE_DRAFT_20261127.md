# Track P P.4 phase 1 on Ada — authorization draft

**Status — unsigned, prerequisites pending (27 November 2026).** This revision applies PLAN §10 to the
[phase-1 authorization design](TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md). Phase 1 is ENGINEERING_ONLY
and uses the receipted sweep-1 train/dev partition. The test evaluator reads synthetic labels. The four
fitted models, reports and readiness intervals from this phase establish engineering readiness only.

## Choices for the author

| Choice | Recommendation and consequence |
|---|---|
| Host and runtime | Admit only `ada_rtx6000` through the reviewed `zli538` venv route. The Ada probes measured fit for all four bases. One arm's job stays on a single leased RTX 6000 Ada. Apply the same thresholds and seed policy to each arm. |
| P4 per-suite logging | Tick P4 as satisfied for phase 1 because T0 has one suite. Keep the per-suite logging prerequisite for the evidence phase. |
| Prompt-replay harness | Bind the actual harness used by `sft-data`. The probe records a clean `897d83c8efa364ec2fdd37288241cc42e01d7274`. Confirm that pin for the real-label and synthetic builders and require the reviewed runner, stage and switch to enforce it before signing. |
| Ada P5 | Require the staged Track P smoke with bound kernels and the E0 equivalence check on the admitted Ada runtime, with accepted reviews. Reconcile the result with the existing timing probes before citing them, and repeat the timing probe if the checked kernel path differs. |

The authorization still needs a published P.3a E0/E4 disposition for each Kev base (P2), a reviewed
harness-bound runner and exact launch pins (P3), the author's P4 tick, and the reviewed Ada P5 records.
The phase-1 switch expects a Markdown probe source with full SHA-256 values. The companion
[Ada probe binding record](../reports/trackp_p4_probe_ada_20261127b/P4_ADA_PROBE_BINDING_20261127.md)
supplies them from the accepted combined probe JSON. The actual stage is checked after publication
with `p4_switch.py check --stage STAGE --note NOTE`. Submit `kev-0.8b` solo first, then bind its sealed
STOP-free record before submitting the other arms.

## Draft key lines

approved: false
label: ENGINEERING_ONLY
phase: 1
run_id: trackp-p4-p1-20261122-a
spec: r1/scripts/htcondor/trackp_p4/p4_spec.json (schema trackp_p4_job/v1)
spec_sha256: PENDING — hash of the reviewed Ada-only spec with the launch pins filled
code_commit: PENDING — published runner commit with the reviewed harness binding
labels: /work/dwong/s2_release_20261123/release_sweep1_traindev/sweep1/traindev/label_block.traindev.jsonl sha256 6a6327a3731dc2d874822e009f3b2d84fbf1a6cbabfef505c657f90b14fd7b2a (R1-S2-LABELS-TRAINDEV-RELEASE)
label_receipt: /work/dwong/s2_release_20261123/release_sweep1_traindev/sweep1/traindev/RECEIPT.json sha256 f06e37a95266aa3267f978dd1d471722f418c1b6b34f6212df6dfd2b7eb665c1 (published receipt copy at docs/r1/reports/release_20261122/RECEIPT_sweep1_traindev.json)
source_label_block: docs/r1/reports/b2_audit_20261119/label_block.jsonl sha256 cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca (source identity bound by the release receipt)
label_freeze: docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md sha256 d0c8d10aa2f6728dd135481b9dde1a4345410272ee67bada0ce93a5be01f7914
label_table_binding: P4-F2 A (R1-P4-TESTPLAN-DECISIONS). The receipt binds the sealed v2 proposal table b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4. A3's FEAT-ONE identity at docs/r1/reports/arms_a3_20261123/feat_one_identity.json sha256 039b8360e293f44632e6a55bff79d32f2b4769045c112cfa4d54a596564853df binds it to sweep1_v3 proposals d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5. Apply A3's checked join by proposal ID.
table_pin: sweep1_v3 (c3_features/v3, trackp_prompt/v2), proposals.jsonl d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5 and configs.json b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df (r1/scripts/configs/trackp_sft.json), staged with build.json
duplicate_policy: heldout_excludes_seen (R1-TRACKP-SFT-DUP)
split: P3 (9 test / 3 dev / 6 train per node), the signed split file (P4-P1SPLIT A)
split_file: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569
arms: kev-0.8b, kev-4b, qwen3.5-0.8b-base, qwen3.5-4b-base (the two Kev arms are conditional on P2 under P4-ARMS A, both controls are required)
lr_grid: 1e-5,3e-5,1e-4 (seeds per lr: 3, learning curve: 250, 500 and full training, sampled by seed 20261122 + n)
readiness: instance-cluster bootstrap 95% interval for seed-mean RPS skill on primary validation, raw and temperature-scaled, 2,000 resamples, seed 20261108
host: R1-HOST-FREE. GPU model recorded per job. Keep each arm job on one card. Proposed class ada_rtx6000, NVIDIA RTX 6000 Ada Generation (sm_89), ucrtasl under zli538 through the p4_direct.py reviewed venv route, Python 3.12.10. Take an empty eligible card first, then a shared eligible card that satisfies the reviewed free-memory check (R1-CARD-SHARE).
host_config: r1/scripts/configs/trackp_ada_v1.json sha256 bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908
micro_batch: 8 (effective batch 16, P4-MB A)
gradient_checkpointing: on for kev-4b and qwen3.5-4b-base, off for both 0.8B arms (R1-P4-4B-CHECKPOINT)
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949 (v2.2 reference pin, R1-TRACKP-IMAGE-V22-B). Ada runs the pinned venv and records image_executed=false.
versions_sha256: aaa1a304c2230466f603e63c96d7259d631f0668fa2d8b6486772fef22f0117a
env3_freeze: docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt sha256 50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08 (R1-ENV-PIN, R1-TRACKP-V21-FREEZE, R1-TRACKP-P4-RUNNER-DECISIONS). Check the venv freeze at job start. The only permitted variance is causal-conv1d==1.7.0 with a valid local build label, recorded in the job receipt.
h200_smoke_e0: none (H200 is outside the proposed Ada-only spec)
h200_sft_probe: none (H200 is outside the proposed Ada-only spec)
ada_smoke_e0: PENDING — reviewed Track P staged smoke and E0 equivalence on the admitted Ada venv
ada_sft_probe: docs/r1/reports/trackp_p4_probe_ada_20261127b/P4_ADA_PROBE_BINDING_20261127.md (hours by arm in the order above 2.52, 6.79, 2.51, 6.75)
job_layout: one job per base under its GPU lease. Full clone with published main, pinned weight and tokenizer staging, receipted data build, grid, selection, learning curve, bootstrap, per-arm pin and synthetic test. Seal each attempt with job record, direct-launch receipt, out.tar and SHA256SUMS. Record hardware, lease, venv and other compute process count and memory at the start and end. An attempt lost alongside another process is an infrastructure failure and is repeated in a new directory (R1-CARD-SHARE). No per-attempt wall-clock limit (R1-NO-TIMEOUT).
real_label_test_read: none (P4-PHASE1-TEST A)
evaluation_seeds_read: none
harness_commit: PENDING — proposed 897d83c8efa364ec2fdd37288241cc42e01d7274, with reviewed staging and enforcement required
gpu_hours_cap: 40 (P4-CAP A and R1-NO-TIMEOUT (3), reporting threshold). R1-HOST-FREE (5) counts GPU-hours on any card. P4-PROBECAP A and P4-T1CHARGE A count every probe attempt and T1 once. probe_gpu_hours: 3.10. Projected training 20.57 GPU-h, combined 23.67 GPU-h, 29.855 slot-hours. slot_hours_cap: 64 (reporting threshold).
probe_charge_files: trackp-p4-probe-20261125-a _wallclock.json sha256 9a1949a156a23a735a6aae45888c99abc1935b17c069526d7dd6d227b4bf595c, trackp-p4-probe-20261127-b _wallclock.json sha256 fa49096f90319db735d775e0bdb1be3baf6cbd882fa31583c3ae1049c18f0877
P1: PASS — signed docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_20261124.md with final verification PASS, bound to the receipt and partition above
P2: PENDING — publish per-Kev E0 verdict and E4 hard-limit disposition, citing the P.3a attempt-1 records and ops-tasl-20261116 commit 2287e4926fe0895b0a55b3a6a61c9afadc701307. The Unit B summary docs/r1/reports/TRACKP_UNITB_TASL7_D2_RESULT_20261119.md sha256 cb2cdf3f107b8f5e6192f04faa511178e9a51c390df56014f15a83a493fea45d is on that branch.
P3: PENDING — reviewed prompt-replay harness binding and exact launch spec. Existing runner review docs/r1/reviews/TRACKP_P4_RUNNER_REVIEW_20261122.md and Ada probe review docs/r1/reviews/P4_ADA_PROBE_REVIEW_20261127.md.
P4: PENDING — author's single-suite logging tick for phase 1
P5: PENDING — R1-QTORCH-AMEND per-class Ada smoke and E0. R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22 and R1-TRACKP-IMAGE-V22-B describe the container reference. Ada's venv torch smoke and the per-base fit and timing probes are recorded separately.
P6: PASS — R1-TRACKP-P4-DECISIONS (all eight phase-1 choices) and R1-P4-4B-CHECKPOINT
P7: PASS — --check-config for the filled Ada host config, docs/r1/reports/trackp_p4_20261127/ADA_HOST_FILL_20261127/check_config.json sha256 34748cebb7438f87724a5c23cf2becbea68f1388faf729e94bd9b0a36889e1d8, accepted in docs/r1/reviews/P4_ADA_HOST_FILL_REVIEW_20261127.md. Check the native freeze again in each stage.
P8: PASS — R1-HOST-FREE governs placement and R1-T1-HOST-TASL records the earlier H200 route. R1-P4-D3-GPU-PREFLIGHT covered the Ada probe. The phase-1 class is for the author to approve.

## Verification before signature

The `VERSIONS.txt` hash is the reviewed v2.2 reference from `docs/r1/reports/trackp_p4_cluster_20261125/T1_versions/`.
The [Ada venv setup](../reports/trackp_p4_20261127/ADA_P4_VENV_20261127.md) reports the package freeze
and CUDA matmul. The [first probe review](../reviews/P4_ADA_PROBE_REVIEW_20261127.md) records the
prompt-replay harness import and the manual staging used for that probe. The
[4B re-check](../reviews/P4_4B_REPROBE_REVIEW_RECHECK_20261127.md) accepts the checkpointed fit
and charge record. The referenced Ada checks still need the functional Track P smoke and E0.

The frozen job design keeps the identity, receipt, split and synthetic test guards. The launch check
requires every P item to pass, the exact signed note on published main and a non-preview stage.
No phase-1 submission is authorized by this draft.
