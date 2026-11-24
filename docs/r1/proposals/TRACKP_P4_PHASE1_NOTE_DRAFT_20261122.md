# Track P P.4 (A5 SFT, belief only), phase 1 — authorization note — DRAFT for the author's signature (approved: false)

This is the final note of the P.4 phase-1 authorization draft (`docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md`,
revision 4.2 on `main`; R1-TRACKP-P4-DECISIONS), filled up to the fields that need the cluster's results. It is in the
key-block format `r1/scripts/htcondor/trackp_p4/p4_switch.py check` parses (every `key: value` line is a field; no key
twice; no `<…>` left at signature).

**Fields still open** (`<FILL …>` or `PENDING` below):
- Image v2.2 and the H200 records (P5). `image:` now holds the v2.2 gpu digest of the cluster report
  `docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md` (24 Nov 2026; R1-TRACKP-IMAGE-V22-B). Image v2.1
  (`sha256:31478d99…`) is not the P.4 image: its prebuilt causal_conv1d failed to import (smoke 759983,
  R1-TRACKP-IMAGE-V22). Still open: the `VERSIONS.txt` sha256 of image v2.2, which is not in the cluster report, its
  review or the v2.2 branch and is read on the host (`TODO_VERIFY_ON_HOST`); the main commit that carries the v2.2
  report (at the time of writing it is only on the branch `trackp-v22-image-20261124` @ `a20bd02e`); an independent
  review of the v2.2 run records (the v2.2 review on that branch reviews the Dockerfile and workflow diff); and the
  SFT probe. The per-arm training hours from the probe go into the spec's `estimate`, with
  `estimate.source: h200_sft_probe: <record>`; the note's `h200_sft_probe:` must name the same record (the switch
  checks it).
- The env3 freeze reading: PENDING R1-TRACKP-P4-RUNNER-DECISIONS (1), which is not on `main` at the time of writing.
  `env3_freeze:` keeps R1-TRACKP-V21-FREEZE as the row states it until then.
- The host config sha256 after the cluster agent fills its `TODO_VERIFY_ON_HOST` values (P7); its image fields are at
  v2.2 already.
- The signed sweep-1 label freeze and the sweep-1 train/dev release receipt and partition (P1).
- The per-base P.3a records (P2). They may remove a Kev base under P4-ARMS A; then `arms:` and the spec's `arms`
  change together.
- The runner's review (P3), the launch commit (`code_commit`, the spec's `paper.commit`) and the spec's sha256.

**Two recorded checks:**
1. before signature, on the completed but unsigned note: `p4_switch.parse_note` and `check_binding` against the stage
   (the test `test_the_note_draft_parses_and_its_completion_binds_a_filled_spec` does this on a filled copy; the note
   is not yet on `main`, so `p4_switch.py check` itself, which requires the note on `origin/main`, cannot run here, and
   `approved: false` is the only field the parser reports);
2. `python r1/scripts/htcondor/trackp_p4/p4_switch.py check --stage <stage> --note <note>` on the published note,
   from a stage rendered with `p4_render_jdl.py` (no `--preview`), before the first submission.

**Submission order.** First `submit --arm kev-0.8b` alone (it stages an adapter and a base). Then the other three arms,
with `--first-record` naming its sealed, STOP-free record.

Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026; to be independently reviewed with the P.4 runner unit (P3).

approved: false
label: ENGINEERING_ONLY
phase: 1
run_id: trackp-p4-p1-20261122-a
spec: r1/scripts/htcondor/trackp_p4/p4_spec.json (schema trackp_p4_job/v1)
spec_sha256: <FILL at signature: sha256 of p4_spec.json at the launch commit, with its TODO fields filled>
code_commit: <FILL at signature: the reviewed P.4 runner commit on main = the spec's paper.commit>
labels: <FILL: <release root>/sweep1/traindev/label_block.traindev.jsonl sha256 from its RECEIPT.json> (the receipted sweep-1 train/dev partition, R1-S2-LABELS-TRAINDEV-RELEASE; P4-LABELS A)
label_receipt: <FILL: <release root>/sweep1/traindev/RECEIPT.json sha256>
source_label_block: docs/r1/reports/b2_audit_20261119/label_block.jsonl sha256 cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca (read only by the release step; the job checks the receipt's inputs.label_block_sha256 against it)
label_freeze: <FILL: docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_<date>.md sha256>
table_pin: sweep1_v3 (c3_features/v3, trackp_prompt/v2); proposals.jsonl d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5 and configs.json b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df (pinned in r1/scripts/configs/trackp_sft.json), transferred with build.json into each job
duplicate_policy: heldout_excludes_seen (R1-TRACKP-SFT-DUP)
split: P3 (9 test / 3 dev / 6 train per node), the signed split file (P4-P1SPLIT A)
split_file: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569
arms: kev-0.8b, kev-4b, qwen3.5-0.8b-base, qwen3.5-4b-base (P4-ARMS A; minus a Kev base with an E0 failure or E4 hard limit per P2; both controls always carried)
lr_grid: 1e-5,3e-5,1e-4; seeds per lr: 3; learning curve: 250, 500 and the full training set, drawn by seed 20261122 + n (P4-LC A)
readiness: instance-cluster bootstrap 95 % interval of the seed-mean RPS skill on primary val, raw and temperature-scaled, 2,000 resamples, seed 20261108; no gate decision in phase 1
host: NEMO2 H200 (HTCondor), R1-T1-HOST-TASL; one GPU per job; sft_gradient_checkpointing: off
host_config: r1/scripts/configs/trackp_htcondor_v2.json <FILL: sha256 at the launch commit, after the TODO_VERIFY_ON_HOST fill (its image fields are at v2.2)>
micro_batch: 8 (host config sft.micro_batch; effective batch 16; P4-MB A)
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949 (image v2.2, tag 20261124-v2.2-667bb9c2; R1-TRACKP-IMAGE-V22-B; docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md)
versions_sha256: <FILL: sha256 of /opt/r1/VERSIONS.txt in image v2.2, read on the host (TODO_VERIFY_ON_HOST: not in the cluster records)>
env3_freeze: docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt sha256 50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08 (R1-ENV-PIN; R1-HTC-QTORCH); each job compares the image's env3 pip freeze to it under R1-TRACKP-V21-FREEZE: equal, or different only in the causal_conv1d line at version 1.7.0 (a local label such as +cu12torch2.6… or a wheel of that version admitted), recorded in the job record and disclosed in the P.4 report; any other difference is a STOP. Image v2.2 records its sorted freeze identical to the pin (causal-conv1d==1.7.0, built from source and installed by name), so its job is expected to record status identical <FILL: the reading of R1-TRACKP-P4-RUNNER-DECISIONS (1) once on main>
h200_smoke_e0: docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md (image v2.2 on NEMO2 H200: I2 759993 PASS, I3 759994 PASS, staged smoke 759997 PASS with kernels_bound causal_conv1d_fn/causal_conv1d_update, E0 760000 equivalent=true) <FILL: the main commit carrying it and the review of these run records>
h200_sft_probe: <FILL: the SFT fit and timing probe record per base at micro-batch 8 (peak memory, seconds per step)>
job_layout: one job per base (P4-JOB A): identity, env3 freeze, full clone with origin/main, configs, inputs, staging (the one network step), data, grid, select, learning curve, bootstrap, per-arm pin file, synthetic test path; out.tar, job_record.json (trackp_p4_job_record/1), SHA256SUMS; sealed under /ceph/srv/dwong/paperb/trackp_p4/trackp-p4-p1-20261122-a/, one attempt-N directory per arm and job, with a receipt
real_label_test_read: none (P4-PHASE1-TEST A; the evaluator runs once per job on a synthetic-label build, with its one-read ledger)
evaluation_seeds_read: none
harness_commit: none (the SFT path does not import the harness)
gpu_hours_cap: 40 (P4-CAP A; the spec's projection 16.94 GPU-h for the four jobs in the draft's 8x case, recomputed from the probe before signature; the draft's 14–19 GPU-h also counts the probe itself, which runs before this note; every sealed attempt, repeats included, is charged to the cap); slot_hours_cap: 64
P1: PENDING — the sweep-1 label freeze signed (docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_<date>.md) with its final verification PASS, and the sweep-1 train/dev release receipt (inputs.label_block_sha256 cdae9c3f…9aca; partition sha256 above)
P2: PENDING — per Kev base, the P.3a record: E0 verdict and any E4 hard limit (attempt-1 final reports; Unit B, ops-tasl-20261116 @ 2287e492)
P3: PENDING — the P.4 runner unit, independently reviewed at the launch commit: docs/r1/reviews/<FILL>
P4: PENDING — the author's tick: the Track P per-suite logging unit is not applicable to phase 1 (T0 is one suite); a precondition of the evidence phase, not of this phase (proposed PASS on the author's signature)
P5: PENDING — R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22 and R1-TRACKP-IMAGE-V22-B on NEMO2 H200, each with a committed result record and an independent review. Image v2.2 records (docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md; Dockerfile/workflow review docs/r1/reviews/TRACKP_V22_IMAGE_REVIEW_20261124.md, round 2 ACCEPTED at 3c54a0e8; on branch trackp-v22-image-20261124 @ a20bd02e, not yet on main): GitHub Actions run 45290856704, tag 20261124-v2.2-667bb9c2, gpu ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949, cpu ghcr.io/dowlingwong/r1-htc-cpu@sha256:a3b3a07424743b84c99101ae61b610f9bd4b6ffe1f2f48c0f6d099fbb84d46b8, causal_conv1d build log sha256 fe872a3edc8f9745148c7e2fe5e02f3f02aebd3c47f5d7a686c610ec816d3312; I2 759993 PASS (the cpu digest changed), I3 759994 PASS, the staged smoke 759997 PASS (kernels_bound with causal_conv1d_fn and causal_conv1d_update), E0 760000 equivalent=true. Still open: those records on main with a review of the run records, then the SFT probe per base at micro-batch 8, from which the P4-CAP projection is recomputed
P6: PASS — R1-TRACKP-P4-DECISIONS on main: P4-PHASE1-TEST A, P4-P1SPLIT A, P4-LABELS A, P4-ARMS A, P4-MB A, P4-JOB A, P4-LC A, P4-CAP A
P7: PENDING — trackp.py --check-config clean on r1/scripts/configs/trackp_htcondor_v2.json as the job uses it (every TODO_VERIFY_ON_HOST filled, with local_path/adapter_local_path naming the job's staged models/<registry key>; image.gpu, image.cpu, image.tag and host at image v2.2, set in the runner's v2.2 update); the env3 freeze checked in the job under R1-TRACKP-V21-FREEZE
P8: PASS — R1-T1-HOST-TASL on main (P.4 on NEMO2 H200)

STOPs (each returns to the author; outputs are kept; a repeated job is a new attempt, never a resume): those of the
draft's §4, as the job enforces them —
- a GPU other than one NVIDIA H200, a VERSIONS.txt sha256 other than the pin, a root uid;
- an env3 freeze difference other than the causal_conv1d line at 1.7.0 (R1-TRACKP-V21-FREEZE);
- a shallow clone, a paper commit not on main, a dirty clone;
- a host or SFT config sha256 other than the pin, a TODO_VERIFY_ON_HOST left;
- a table file other than the pin, a partition or receipt other than labels:/label_receipt:, a receipt source block other
  than cdae9c3f…9aca, a label freeze other than label_freeze: (and every refusal of LabelBlockSource);
- a staged weight of another size or sha256, a config local path other than the staged directory;
- a refusal of the SFT pipeline (split, policy, sealed path, evaluation column), a CUDA OOM at micro-batch 8
  (`stop_class: arm`), a control arm that cannot be trained;
- a real-label test read;
- the cap: a projection or the consumed GPU-hours over 40, a requested walltime over 64 slot-hours or 86,400 s per job.
