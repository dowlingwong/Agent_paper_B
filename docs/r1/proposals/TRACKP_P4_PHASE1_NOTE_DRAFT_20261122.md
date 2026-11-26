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
  review or anywhere on `main` and is read on the host (`TODO_VERIFY_ON_HOST`); an independent review of the v2.2
  run records (the v2.2 review reviews the Dockerfile and workflow diff); and the SFT probe. The v2.2 report and
  review are on `main` since `ac981011` (merge of `trackp-v22-image-20261124` @ `a20bd02e`). The per-arm training hours from the probe go into the spec's `estimate`, with
  `estimate.source: h200_sft_probe: <record>`; the note's `h200_sft_probe:` must name the same record (the switch
  checks it).
- R1-TRACKP-P4-RUNNER-DECISIONS (on `main` since `ffe1edff`) is written in: (1) the env3 freeze reading
  (`env3_freeze:`), (2) tokenizers staged through the hub into `HF_HOME` (`job_layout:`), (3) `kev-0.8b` the first,
  solo arm (the submission order below; the spec's `first_arm`, which the runner requires). The P4 tick and the
  signature follow later.
- The host config sha256 after the cluster agent fills its `TODO_VERIFY_ON_HOST` values (P7); its image fields are at
  v2.2 already.
- The signed sweep-1 label freeze and the sweep-1 train/dev release receipt and partition (P1).
- The per-base P.3a records (P2). They may remove a Kev base under P4-ARMS A; then `arms:` and the spec's `arms`
  change together. If they remove `kev-0.8b`, the first arm of R1-TRACKP-P4-RUNNER-DECISIONS (3) is gone and the
  runner STOPs: that returns to the author.
- The runner's review (P3), the launch commit (`code_commit`, the spec's `paper.commit`) and the spec's sha256.
- **25 Nov 2026 (R1-P4-TESTPLAN-DECISIONS).** P4-F2 A is written in as `label_table_binding:` (filled: the receipt
  binds the sealed v2 table, and each job runs A3's FEAT-ONE A identity check and A3's join by proposal id; the switch
  checks the line). P4-PROBE A: the probe runs only through the reviewed probe mode (`p4_lib.py probe`, staged by
  `p4_render_jdl.py --probe`). P4-PROBECAP A: the probe's GPU-hours count against the 40 GPU-h; `gpu_hours_cap:` now
  carries `probe_gpu_hours: <FILL>`, which must equal the spec's `caps.probe_gpu_hours` and the probe record's one
  `p4_probe_gpu_hours:` line (the switch checks both), and the spec's projection is recomputed from the probe.
- **26 Nov 2026 (R1-P4-PROBE-CHARGE).** P4-T1CHARGE A: T1's GPU time is part of `probe_gpu_hours`. `probe-record`
  requires every T1 job's ClusterId and `condor_history` RemoteWallClockTime (`--t1-history` from the committed
  `condor_history.txt`, or `--t1-wallclock`), bound to T1's pinned committed record
  (`docs/r1/reports/trackp_p4_cluster_20261125/T1_versions/`, job 760065), and charges T1 once, in the base charge
  file `_wallclock.json`; `gpu_hours_cap:` must cite
  P4-T1CHARGE A (the switch checks it). P4-EXTRAPROBE A and the killed-attempt charge are unchanged.
- **27 Nov 2026: revised to R1-HOST-FREE** (PLAN row R1-HOST-FREE (3): the P.4 phase-1 note is revised to the row
  before signature; card local/20261126-06 unit 1). The GPU model is recorded, not fixed: the spec admits host classes
  (`hosts`: `nemo2_h200`, NVIDIA H200 by HTCondor; `ada_rtx6000`, NVIDIA RTX 6000 Ada Generation started directly
  over SSH under a GPU lease by `p4_direct.py`), each with its own host config and its own SFT probe estimate; each
  job is told its class and refuses a GPU other than exactly one of that class's; every job record names host, GPU
  model, UUID, driver and the env3 freeze; one arm's training run stays on one card (one job, one leased card; the
  assembly records each arm's class and card). `host:`, `host_config:`, the per-class probe lines (`h200_sft_probe:`,
  `ada_sft_probe:`; a class the spec does not admit reads `none`), `gpu_hours_cap:` and P8 changed; the switch checks
  them. At signature, the admitted classes are the spec's `hosts` and a class the spec does not admit is struck from
  `host:` and `host_config:`.
- **27 Nov 2026: rows (g)** (R1-NO-TIMEOUT, R1-STEP-ORDER, R1-CARD-SHARE). No time limit decides a probe or a job
  attempt: HTCondor's `+RequestWalltime` stays a scheduler request only, a direct launch has none, and a walltime kill
  is sealed as an infrastructure failure and repeated. The 40 GPU-h and 64 slot-hour figures are reporting thresholds
  (R1-NO-TIMEOUT (3)): usage is reported against them at launch validation, before every submission and at the
  assembly, and reaching one is reported to the author at once; nothing is refused for it. The direct launcher checks
  the card's free memory, not an empty card, and shares when it must (R1-CARD-SHARE (1)); every job record (and every
  direct launcher record) names the card's other compute processes at the start and at the end, count and memory only
  (R1-CARD-SHARE (4)); an attempt lost beside another process (an OOM, a kill) is an infrastructure failure, sealed and
  repeated in a new attempt directory, never an outcome (R1-CARD-SHARE (3)).

**Two recorded checks:**
1. before signature, on the completed but unsigned note: `p4_switch.parse_note` and `check_binding` against the stage
   (the test `test_the_note_draft_parses_and_its_completion_binds_a_filled_spec` does this on a filled copy; the note
   is not yet on `main`, so `p4_switch.py check` itself, which requires the note on `origin/main`, cannot run here, and
   `approved: false` is the only field the parser reports);
2. `python r1/scripts/htcondor/trackp_p4/p4_switch.py check --stage <stage> --note <note>` on the published note,
   from a stage rendered with `p4_render_jdl.py` (no `--preview`), before the first submission.

**Submission order** (R1-TRACKP-P4-RUNNER-DECISIONS (3)). First `submit --arm kev-0.8b` alone (it stages an adapter
and a base). Then the other three arms,
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
label_table_binding: P4-F2 A (R1-P4-TESTPLAN-DECISIONS): the receipt's inputs.proposals_sha256 is the sealed v2 table b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4 (arms_freeze.SWEEP1_SEALED_PROPOSALS_SHA256; any other value is a STOP); each job runs A3's FEAT-ONE A identity check (arms_freeze.require_feat_one on docs/r1/reports/arms_a3_20261123/feat_one_identity.json sha256 039b8360e293f44632e6a55bff79d32f2b4769045c112cfa4d54a596564853df, the result A3 consumed), which binds it to the sweep1_v3 table d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5, and then joins the released labels to that table by proposal id as A3 does (arms_freeze.load_traindev and arms_freeze.training_rows: a released label for a proposal outside the table, a label on a within-campaign duplicate or a test row, a duplicate label row, and a non-inert, non-duplicate train/dev table row without its label row are each a STOP; duplicates and test rows carry no label); no new release
table_pin: sweep1_v3 (c3_features/v3, trackp_prompt/v2); proposals.jsonl d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5 and configs.json b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df (pinned in r1/scripts/configs/trackp_sft.json), transferred with build.json into each job
duplicate_policy: heldout_excludes_seen (R1-TRACKP-SFT-DUP)
split: P3 (9 test / 3 dev / 6 train per node), the signed split file (P4-P1SPLIT A)
split_file: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569
arms: kev-0.8b, kev-4b, qwen3.5-0.8b-base, qwen3.5-4b-base (P4-ARMS A; minus a Kev base with an E0 failure or E4 hard limit per P2; both controls always carried)
lr_grid: 1e-5,3e-5,1e-4; seeds per lr: 3; learning curve: 250, 500 and the full training set, drawn by seed 20261122 + n (P4-LC A)
readiness: instance-cluster bootstrap 95 % interval of the seed-mean RPS skill on primary val, raw and temperature-scaled, 2,000 resamples, seed 20261108; no gate decision in phase 1
host: R1-HOST-FREE (and R1-T1-HOST-TASL for NEMO2 H200): the GPU model recorded per job, not fixed; one GPU per job and one card per arm (an arm's training run stays on one card); admitted host classes (the spec's hosts; a class the spec does not admit is struck at signature): nemo2_h200 (NVIDIA H200, compute capability 9.0, HTCondor) and ada_rtx6000 (NVIDIA RTX 6000 Ada Generation, compute capability 8.9, direct launch over SSH under a GPU lease, p4_direct.py, on a card with the free memory the job needs, R1-CARD-SHARE); sft_gradient_checkpointing: off
host_config: r1/scripts/configs/trackp_htcondor_v2.json <FILL: sha256 at the launch commit, after the TODO_VERIFY_ON_HOST fill (its image fields are at v2.2)>; r1/scripts/configs/trackp_ada_v1.json <FILL: sha256 at the launch commit, after its TODO_VERIFY_ON_HOST fill from the Ada survey (p4_fill_host_config.py --host-class ada_rtx6000)>
micro_batch: 8 (host config sft.micro_batch; effective batch 16; P4-MB A)
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949 (image v2.2, tag 20261124-v2.2-667bb9c2; R1-TRACKP-IMAGE-V22-B; docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md)
versions_sha256: <FILL: sha256 of /opt/r1/VERSIONS.txt in image v2.2, read on the host (TODO_VERIFY_ON_HOST: not in the cluster records)>
env3_freeze: docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt sha256 50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08 (R1-ENV-PIN; R1-HTC-QTORCH); each job compares the image's env3 pip freeze to it under R1-TRACKP-V21-FREEZE, read per R1-TRACKP-P4-RUNNER-DECISIONS (1) ("the same version number" is version 1.7.0, any local build label admitted and recorded; with image v2.2 building causal_conv1d from source, R1-TRACKP-IMAGE-V22-B, the env3 line is checked against 1.7.0). Admitted causal_conv1d line, exactly one of: causal-conv1d==1.7.0, or causal-conv1d==1.7.0+LABEL where LABEL is a PEP 440 local label (letters and digits in dot-separated segments); the line and its label are recorded in the job record's env3_freeze and a label is disclosed in the P.4 report. Every other line must match the pin exactly. STOP forms include a direct reference (causal-conv1d @ file://… or causal-conv1d @ https://…, even to a file of version 1.7.0) and the causal_conv1d spelling (causal_conv1d==1.7.0), as well as any other version or operator, a malformed label, a removed or added causal_conv1d line, and any other difference. Image v2.2 records its sorted freeze identical to the pin (causal-conv1d==1.7.0, built from source and installed by name), so its job is expected to record status identical with no local label
h200_smoke_e0: docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md, on main since ac981011 (image v2.2 on NEMO2 H200: I2 759993 PASS, I3 759994 PASS, staged smoke 759997 PASS with kernels_bound causal_conv1d_fn/causal_conv1d_update, E0 760000 equivalent=true) <FILL: the independent review of these run records>
h200_sft_probe: <FILL: the nemo2_h200 class's SFT fit and timing probe record per base at micro-batch 8 (peak device memory, seconds per step; P4-PROBE A, run through the reviewed probe mode p4_lib.py probe), on main, with one line "p4_probe_host_class: nemo2_h200", one line "p4_estimate_hours: ARM HOURS" per arm equal to the spec's hosts.nemo2_h200.estimate.hours and one line "p4_probe_gpu_hours: HOURS" equal to the spec's caps.probe_gpu_hours (p4_switch check); or "none: the spec does not admit nemo2_h200">
ada_sft_probe: <FILL: the ada_rtx6000 class's SFT fit and timing probe record per base at micro-batch 8 (the probe mode through p4_direct.py, compute/20261126-07), on main, with one line "p4_probe_host_class: ada_rtx6000", one line "p4_estimate_hours: ARM HOURS" per arm equal to the spec's hosts.ada_rtx6000.estimate.hours and one line "p4_probe_gpu_hours: HOURS" equal to the spec's caps.probe_gpu_hours (p4_switch check); or "none: the spec does not admit ada_rtx6000">
job_layout: one job per base (P4-JOB A): identity, env3 freeze, full clone with origin/main, configs, inputs, staging (the one network step: registry weights by size and sha256; tokenizers through the hub into the job's HF_HOME, R1-TRACKP-P4-RUNNER-DECISIONS (2)), data, grid, select, learning curve, bootstrap, per-arm pin file, synthetic test path; out.tar, job_record.json (trackp_p4_job_record/1), SHA256SUMS; sealed under /ceph/srv/dwong/paperb/trackp_p4/trackp-p4-p1-20261122-a/, one attempt-N directory per arm and job, with a receipt (a direct attempt also binds its launcher record direct_launch.json, trackp_p4_direct_launch/1: host, hostname, runtime and image digest, lease, card UUID, the card's other compute processes at start and end, start and end UTC, wall clock, exit code); no wall-clock limit on any attempt (R1-NO-TIMEOUT): HTCondor's +RequestWalltime is a scheduler request only, and a walltime kill or an attempt lost beside another compute process is an infrastructure failure, repeated in a new attempt directory (R1-CARD-SHARE (3))
real_label_test_read: none (P4-PHASE1-TEST A; the evaluator runs once per job on a synthetic-label build, with its one-read ledger)
evaluation_seeds_read: none
harness_commit: none (the SFT path does not import the harness)
gpu_hours_cap: 40 (P4-CAP A, a reporting threshold under R1-NO-TIMEOUT (3): usage is reported against it and reaching it is reported to the author at once, not refused; GPU-hours on any card, R1-HOST-FREE (5): an HTCondor attempt by its RemoteWallClockTime or receipt, a direct attempt by its launcher's wall clock on its one card; P4-PROBECAP A: the SFT probes' GPU-hours, every host class, count against this figure; P4-T1CHARGE A (R1-P4-PROBE-CHARGE): T1's GPU time is included in them, every T1 job's condor_history RemoteWallClockTime bound to T1's committed record and charged once, in the probe record run's base charge file: probe_gpu_hours: <FILL: the spec's caps.probe_gpu_hours, two decimals, the charge of every sealed probe attempt plus T1's, rounded up to 0.01, equal to the probe record's p4_probe_gpu_hours line> GPU-h; the spec's projection for the four jobs, recomputed from the probe, <FILL: projection.total_gpu_hours> GPU-h (16.94 in the draft's 8x case; each arm at its largest estimate over the admitted classes); the two together reported against 40 (launch validation, the switch's check before every submission and the assembly add the probe's hours); every sealed attempt, repeats included, is charged); slot_hours_cap: 64 (a reporting threshold, R1-NO-TIMEOUT (3))
probe_charge_files: <FILL: each probe run and the sha256 of each of its charge files (_wallclock.json, then any _wallclock.<n>.json), as the probe record's p4_probe_charge_file: lines and the spec's caps.probe_charge_files give them (P4-PROBECAP A; the switch checks all three; assemble and the switch's cap check refuse a changed, missing or unlisted charge file)>
P1: PENDING — the sweep-1 label freeze signed (docs/r1/authorizations/C3_SWEEP1_LABEL_FREEZE_<date>.md) with its final verification PASS, and the sweep-1 train/dev release receipt (inputs.label_block_sha256 cdae9c3f…9aca; partition sha256 above)
P2: PENDING — per Kev base, the P.3a record: E0 verdict and any E4 hard limit (attempt-1 final reports; Unit B, ops-tasl-20261116 @ 2287e492)
P3: PENDING — the P.4 runner unit, independently reviewed at the launch commit: docs/r1/reviews/<FILL>
P4: PENDING — the author's tick: the Track P per-suite logging unit is not applicable to phase 1 (T0 is one suite); a precondition of the evidence phase, not of this phase (proposed PASS on the author's signature)
P5: PENDING — R1-TRACKP-IMAGE-V21, R1-TRACKP-IMAGE-V22 and R1-TRACKP-IMAGE-V22-B on NEMO2 H200, each with a committed result record and an independent review. Image v2.2 records (docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md; Dockerfile/workflow review docs/r1/reviews/TRACKP_V22_IMAGE_REVIEW_20261124.md, round 2 ACCEPTED at 3c54a0e8; both on main since ac981011, the merge of trackp-v22-image-20261124 @ a20bd02e): GitHub Actions run 45290856704, tag 20261124-v2.2-667bb9c2, gpu ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949, cpu ghcr.io/dowlingwong/r1-htc-cpu@sha256:a3b3a07424743b84c99101ae61b610f9bd4b6ffe1f2f48c0f6d099fbb84d46b8, causal_conv1d build log sha256 fe872a3edc8f9745148c7e2fe5e02f3f02aebd3c47f5d7a686c610ec816d3312; I2 759993 PASS (the cpu digest changed), I3 759994 PASS, the staged smoke 759997 PASS (kernels_bound with causal_conv1d_fn and causal_conv1d_update), E0 760000 equivalent=true. Still open: an independent review of the run records, then the SFT probe per base at micro-batch 8, from which the P4-CAP projection is recomputed
P6: PASS — R1-TRACKP-P4-DECISIONS on main: P4-PHASE1-TEST A, P4-P1SPLIT A, P4-LABELS A, P4-ARMS A, P4-MB A, P4-JOB A, P4-LC A, P4-CAP A
P7: PENDING — trackp.py --check-config clean on r1/scripts/configs/trackp_htcondor_v2.json as the job uses it (every TODO_VERIFY_ON_HOST filled, with local_path/adapter_local_path naming the job's staged models/<registry key>; image.gpu, image.cpu, image.tag and host at image v2.2, set in the runner's v2.2 update); the env3 freeze checked in the job under R1-TRACKP-V21-FREEZE
P8: PASS — R1-T1-HOST-TASL on main (P.4 on NEMO2 H200) and R1-HOST-FREE on main (any admitted host class that fits and passes its environment check; the GPU model recorded, not fixed)

STOPs (each returns to the author; outputs are kept; a repeated job is a new attempt, never a resume): those of the
draft's §4, as the job enforces them —
- a GPU not of the job's admitted host class (other than exactly one GPU of that class's model and compute
  capability), for a direct job a card other than the leased one, a VERSIONS.txt sha256 other than the pin, a root uid;
- an env3 freeze difference other than causal-conv1d==1.7.0 with at most a local build label (R1-TRACKP-V21-FREEZE; R1-TRACKP-P4-RUNNER-DECISIONS (1)); a direct reference or the causal_conv1d spelling is a STOP;
- a shallow clone, a paper commit not on main, a dirty clone;
- a host or SFT config sha256 other than the pin, a TODO_VERIFY_ON_HOST left;
- a table file other than the pin, a partition or receipt other than labels:/label_receipt:, a receipt source block other
  than cdae9c3f…9aca, a label freeze other than label_freeze: (and every refusal of LabelBlockSource);
- P4-F2 A: a receipt table other than the sealed v2 table b713c423…57c4, a FEAT-ONE identity result other than the
  committed one or one that does not bind that table to sweep1_v3, and in A3's join a released label for a proposal
  outside the table, a label on a duplicate or a test row, a duplicate label row, or a non-inert, non-duplicate
  train/dev table row without its label row;
- a staged weight of another size or sha256, a config local path other than the staged directory;
- a refusal of the SFT pipeline (split, policy, sealed path, evaluation column), a CUDA OOM at micro-batch 8 on a card
  the job had to itself (beside another compute process it is an infrastructure failure, repeated, R1-CARD-SHARE (3))
  (`stop_class: arm`), a control arm that cannot be trained;
- a real-label test read;
- an HTCondor job whose requested walltime would exceed 86,400 s (a scheduler request; no limit on a direct job).
  Not a STOP (R1-NO-TIMEOUT (3)): a projection or the consumed GPU-hours over 40, or slot-hours over 64, the probes'
  GPU-hours included; reaching them is reported to the author at once.
