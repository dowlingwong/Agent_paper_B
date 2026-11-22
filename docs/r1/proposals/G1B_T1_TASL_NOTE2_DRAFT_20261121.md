# G.1b on the TASL pair — second authorization note (the three TASL-7 nodes) — DRAFT for signature (revised 22 Nov 2026 for R1-T1-DATA-MANIFEST)

This draft is the second note of R1-G1B-TASL-DECISIONS (XC A) for the three TASL-7 nodes (`mlab_cifar10`,
`mlgym_cifar10`, `mlgym_breakout_minatar`) of run `g1b-tasl-20261121-b`. R1-T1-DATA-MANIFEST amends
R1-G1B-NOTE2-DECISIONS' "same run_id, paper_commit and spec_sha256" in two of its three parts: note 2 binds the
re-issued spec (the same as the amendment note for `mlgym_fmnist`), `spec_sha256` `7ff3c95b…`, and so the
`paper_commit` its launch binding needs, `3c3f822aaa839958a8754ffdcfa09a51e7699107` (the row's "each with the paper_commit its launch binding
needs"). The run id and harness are the first note's. The TASL-7 attempts therefore run the code of
`3c3f822a`, not `10fd3343`; between them the job path changes only by the autoresearch-only branches of
`g1b_tasl.py` and the cross-check kind of `t1_tasl_node.sh` (`g1b_lib.py` and `r1/noise` unchanged; decision
G1B-JOIN in the chain report).

**Changes against the 21 Nov draft:** `paper_commit`, `spec_sha256`, the `spec` line, the corrected manifest
values on the `mlgym_fmnist` and `mlgym_cifar10` node lines; P4 and P10 (the launch-chain review and the census
erratum record); P12 (autoresearch now under the third note: PASS, it is not in this run); the `nodes` and
`scope` lines (the amendment note and the joined assembly); the re-issued cross-check run id in P7's template.

- **Launch:** the TASL-7 nodes launch from the published commit that changes the G.1b spec to this
  `spec_sha256` (or a docs-only descendant), not from `985dd45d` (launch table:
  `docs/r1/reports/tasl_chain_20261122/TASL_CHAIN_20261122.md`).
- **P7** stays PENDING until the re-issued cross-check (run `g1b-tasl-20261121-b-xc2`) has run and its three
  step-1 verdicts are on `main`; then P7 is completed from the template below and checked twice with
  `python sweep2/t1_tasl/g1b_crosscheck.py check-note2 sweep2/t1_tasl/g1b_crosscheck_spec.json --note <note>
  --verdict <path> (x3)`, first with `--draft` (unsigned, copied to its final name), then strict on the
  published note before any TASL-7 node launches.
- **Assembly:** all seven nodes assemble into one row through the gated assembly of decision G1B-JOIN (the
  first note's three sealed attempts carry the old spec sha256).
- **The census erratum** is part of P4, which cites the independently reviewed erratum record `docs/r1/reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md`
  (sha256 `9b40944b…`, the bytes its review fixes; review `docs/r1/reviews/T1_DATA_MANIFEST_ERRATUM_REVIEW_20261122.md`), published on `main`
  byte-identical, with the review's editorial conditions in a separate addendum beside it. The cited sha256
  must be one a review fixes: if the record on `main` differs, STOP (no correction at signature).
  `python sweep2/t1_tasl/g1b_tasl_join.py publication-check <note> --p4` checks it against `origin/main`.
- **Signature:** copy to `docs/r1/authorizations/g1b_t1_tasl_<YYYYMMDD>.md` with a date no other G.1b note
  uses, `approved: true`, and publish byte-identically on `main`; the TASL-7 host copies it from `origin/main`
  into its launch checkout's `docs/r1/authorizations/` (an untracked docs file). Signed by the coordinating
  chat under R1-T1-DATA-MANIFEST.

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, revised 22 Nov 2026; independently reviewed
with the cross-check unit and with the launch chain.

approved: false
label: ENGINEERING_ONLY
labels_read: none
run_id: g1b-tasl-20261121-b
paper_commit: 3c3f822aaa839958a8754ffdcfa09a51e7699107
spec_sha256: 7ff3c95b963a2f1690461ca58dc98bec7ad79e31ccbbe159c57004716a8cc5f7
spec: sweep2/t1_tasl/g1b_tasl_spec.json, re-issued under R1-T1-DATA-MANIFEST (the first note's spec sha256 060aac91ba452a69e4e898b66b92ebd5bfc0887c2933cfd2e438d93d17ecb465 with two data_manifest_sha256 values, mlgym_fmnist and mlgym_cifar10, and paper.commit changed); run_id unchanged; the same spec as the amendment note
host_row: R1-T1-TASL-ENV (hosts and environments of the T1 table on the TASL pair), with R1-T1-HOST-TASL
harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702
harness: dowlingwong/autoresearch_harness at harness_commit (branch mac-trackg-t1-tasl-20261121), clean on both hosts (checked by every job; check_note requires harness_commit to equal the spec's)
launch: from a published checkout of the launch commit (an ancestor of the freshly fetched origin/main) holding the signed spec, whose code equals paper_commit outside docs/ and the spec file (verify_launch_tasl); main may move on after the signature, and the note must stay byte-identical on origin/main
gpu_model: NVIDIA GeForce RTX 4090 on both hosts (one GPU model for the whole table, R1-T1-HOST-TASL)
host_TASL2: hostname TASL-2; GPU GPU-4d623e76-7587-ee15-a633-46f60d220d94; driver 535.309.01; cpus 0-7 for GPU nodes, 8-15 for mlgym_houseprice; lease ~/r1_locks/gpu0.lock; envs torch312
host_TASL7: hostname TASL-7; GPU GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1; driver 580.178.04; cpus 0-7; lease ~/r1_locks/gpu0.lock; envs torch312, jax312 (XLA_FLAGS=--xla_gpu_cuda_data_dir=/usr/local/cuda-12.2)
node_split: TASL-2 runs mlab_imdb, mlab_ogbn_arxiv, mlgym_fmnist (GPU) and mlgym_houseprice (CPU); TASL-7 runs mlab_cifar10, mlgym_cifar10, mlgym_breakout_minatar (GPU); each host runs its GPU nodes one after another under its GPU lease; mlgym_houseprice runs on TASL-2's cpus 8-15 without a GPU lease, beside the GPU nodes
nodes: the seven nodes of R1-TRACKG-G3-EARLY in this run's spec; this note launches the three TASL-7 nodes; autoresearch_fixedtokens runs under the third note with its own spec (R1-G1B-NOTE2-DECISIONS)
node_mlab_cifar10: host TASL-7; gpu; env torch312; node_spec_sha256 90c8364f3c35b276ad97c73ea66b9e31d9f8e128aa9be7db5a013b5eb7b4093f; committed_pin_sha256 1f047ad7cc8cb9e7520a9362c578dcfa516cd4e59301c7ff12d915690ca494c2; edits_manifest_sha256 bef79111cf21be264713e04eab2ac13e0f926bb4a6457b93ff32bf540e56b44d; data_manifest_sha256 43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3; census_record (at census commit 76f1d7ba, not on main) docs/r1/reports/trackg_g0_20261117/u2_iso_mlab_cifar10_20261119T033747Z/; slowest census record 13.347 s; timeout 40.041 s (3 x slowest, R1-G1B-TIMEOUT); runs 460
node_mlab_imdb: host TASL-2; gpu; env torch312; node_spec_sha256 0123a8a771f5abc1028dd83fab7afdf67afb053f7bf064c693f081ec13601510; committed_pin_sha256 4b1019a60b1ac96028944d1dcc02be582f84e1fab0dbfd11d00011f460fb97fb; edits_manifest_sha256 09edee58dbe18cf009276bbced98c9d534fef9cf04680a707b118f2f097ad969; data_manifest_sha256 a87254e16dfd13ad606e69ab357d02715773c0a442f5e59de42788c7cbcb935c; census_record (at census commit 76f1d7ba, not on main) docs/r1/reports/trackg_g0_20261117/u2_iso_mlab_imdb_20261119T034107Z/; slowest census record 65.156 s; timeout 195.468 s (3 x slowest, R1-G1B-TIMEOUT); runs 460
node_mlab_ogbn_arxiv: host TASL-2; gpu; env torch312; node_spec_sha256 e952df6a2f3f9abfdca944805e57a86604770d289101135fe45763b510752c0c; committed_pin_sha256 bd71fdf4c6b3a66715cb602a41a7a1f5bdeeaa6e23439c558a96c2bda061c9d7; edits_manifest_sha256 b2cf5ae6f51fde68acae32e9324306e0b76fb965831cd1cd8037f64dceddfe1a; data_manifest_sha256 9131216213b0950e46d0eae81e691503991c0218627fde56ba88e6ac33cd4c6c; census_record (at census commit 76f1d7ba, not on main) docs/r1/reports/trackg_g0_20261117/u2_iso_mlab_ogbn_arxiv_20261119T035109Z/; slowest census record 21.8 s; timeout 65.4 s (3 x slowest, R1-G1B-TIMEOUT); runs 460
node_mlgym_cifar10: host TASL-7; gpu; env torch312; node_spec_sha256 f1360bcd01b0a68b8262360c68a6d5b4adad70cd46d127b539791b1ee3eadad1; committed_pin_sha256 2d7e533b2a1075000d15a21445f98b94d7df2cf527baff0264f3ae306f93022e; edits_manifest_sha256 d0ad0e64ebce12f9d6c5d57ada95c0e7c8c26deedb4ec5479245e2c7e3027d9a; data_manifest_sha256 54d3a74d342d285fe724538a46872d028639533b4280557b00062e3d3c706100 (census erratum, R1-T1-DATA-MANIFEST; was c0ef1168…); census_record (at census commit 76f1d7ba, not on main) docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_cifar10_20261119T035326Z/; slowest census record 35.948 s; timeout 107.844 s (3 x slowest, R1-G1B-TIMEOUT); runs 460
node_mlgym_fmnist: host TASL-2; gpu; env torch312; node_spec_sha256 65f229affedca7abcc0a78792053cf5fa3c8a1237bf683298faa03e674a152e9; committed_pin_sha256 eb60107ee2a329ac1f6b919f0d632e1fc84f1e6440b704010891398096c841b3; edits_manifest_sha256 de6782b31d529a759176ddc7c8e1b922c37d434a2c379c3ef3143dfe5fa8db37; data_manifest_sha256 24cb34483c5a23b4e7a198ac2840044171f2668d4f8cb3fe8b5e53ac69cadc32 (census erratum, R1-T1-DATA-MANIFEST; was 8d28287b…); census_record (at census commit 76f1d7ba, not on main) docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_fmnist_20261119T035842Z/; slowest census record 40.795 s; timeout 122.385 s (3 x slowest, R1-G1B-TIMEOUT); runs 460
node_mlgym_breakout_minatar: host TASL-7; gpu; env jax312; node_spec_sha256 db57b202301e323d4471cf23ef6ad3b822d5f5e0d471f1896ffda3041af2a10a; committed_pin_sha256 cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4; edits_manifest_sha256 a7fe205a28ee5b3fdc6c6b847ebe6745b3b8dbc4b3260fd72080bb87bf487812; data_manifest_sha256 none (the node has no data setup; null in the spec); census_record (at census commit 76f1d7ba, not on main) docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_breakout_minatar_20261119T045751Z/; slowest census record 61.781 s; timeout 185.343 s (3 x slowest, R1-G1B-TIMEOUT); runs 460
node_mlgym_houseprice: host TASL-2; cpu (cpus 8-15); env torch312; node_spec_sha256 2f150cded7c846a28fd97113519333a33d9775588a7d6c7bd0d9dcc05e85c049; committed_pin_sha256 88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654; edits_manifest_sha256 f26332ff9e75bbda708f40581a904ba474f849c7b7e0564a1513923b2393e34b; data_manifest_sha256 73ee55972381fd36ee5b3244467d7f05333adfc292ed48089786b366d5c686ff; census_record (at census commit 76f1d7ba, not on main) docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_houseprice_20261120T215244Z/; slowest census record 6.794 s; timeout 20.382 s (3 x slowest, R1-G1B-TIMEOUT); runs 460
envs: torch312 (freeze env/torch312.freeze.txt, sha256 d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42) and jax312 (freeze env/jax312.freeze.txt, sha256 80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1), Python 3.12.16, built with uv 0.13.6; each job compares uv pip freeze to the freeze at its start (STOP on a difference)
census: ops-tasl-20261116 commit 76f1d7bac8bf9b265c0e2c93174b8c16e2df49aa, report docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md sha256 146b111410122108c7efa25246b61db62060adcaa3ea14fb2111ec2e13d692d7 (the copy on main, sha256 d7f8f8aab2c4d1002c8f666caca0ae4393ca11514d3d040ac0949f1657c79890, adds the autoresearch row and rewrites prose and acceptance text; the seven node rows are unchanged); the per-node census records are at the census commit, not on main
edits: four declared edits per node (E1-E4) from each census U2 record's declared-edit manifest; (4 + 1) x 92 = 460 runs per node; 3,220 runs in all (R1-G1B-EDITS)
measurement: D21 protocol unchanged: 30 seeds per condition (train 1001-, split 2001-, joint 3001-), split policy vary, one worker, isolation gate effective:true with waivers {} and exceptions [], the pinned e1_report rule
timeouts: per node 3 x the slowest census record (values on the node lines); on the 4090 the first run that reaches its timeout is a STOP (stop_on_timeout, harness c025f89a), not a divergent row (R1-G1B-TIMEOUT)
projection: estimate (4090/Ada ratio 1.0) 28.262 GPU-h (TASL-2 14.06, TASL-7 14.202 GPU wall-hours) plus mlgym_houseprice 7.168 CPU core-hours; sensitivity (ratio 1.5) 41.644 GPU-h; the TASL-7 -> TASL-2 cross-host check adds about 1 GPU-h; all within the 100 GPU-h cap (R1-G1B-CAP)
cap: 100 GPU-h for G.1b (R1-G1B-CAP); a projection or consumption beyond it is an author STOP
seal: each attempt writes out/, job_record.json (g1b_tasl_job_record/1), out.tar and SHA256SUMS under <runs_root>/g1b-tasl-20261121-b/<node>/attempt-N/; jobs are started through sweep2/t1_tasl/t1_tasl_node.sh g1b, whose log goes to <runs_root>/g1b-tasl-20261121-b/_logs/ and is bound by the seal (the dry runs' null node_log_sha256 came from the dry-run wrapper); g1b_tasl.py seal copies it without overwrite to <sealed_root>/g1b-tasl-20261121-b/<node>/attempt-N/ with SEAL_RECEIPT.json binding the record and the wrapper log; assemble takes one sealed attempt per node from both hosts and lists the unused infrastructure attempts; summarise applies the D21 rule (double-checked)
keys: real runs need --enable and G1B_TASL_ENABLE_REAL=1 on each host, after this note is on main
P1: PASS — R1-T1-HOST-TASL: G.1b on TASL-2 and TASL-7, one GPU model (RTX 4090); the worker host checks pass on both hosts (P2, P3)
P2: PASS — TASL-2 harness-isolation host check docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md sha256 681011b2114f6ff7db679d3265535d1cc2e8a9bdbc231371230f4de42d7b6b6d (review docs/r1/reviews/TASL2_ISOLATION_HOST_CHECK_REVIEW_20261121.md); "1-7 PASS" is the launch-schema value: §3 item 7 (CUDA IPC) is untested on TASL-2 (review condition C1), and no node of this run uses cuda_share or cuda_open (at harness c025f89a they appear only in each node's copied ar_isolated.py library, called by none of the seven)
P3: PASS — TASL-7 harness-isolation host check docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md sha256 09945c15df67b2627a97e6cc59239744738aecb14e522f7c52d1f390be4576a4 (review docs/r1/reviews/TASL7_ISOLATION_HOST_CHECK_REVIEW_20261121.md)
P4: PASS — independent review of the code unit docs/r1/reviews/T1_TASL_REVIEW_20261121.md (accepted at 021dbc26 with harness c025f89a); the pre-launch and dry-run reviews (docs/r1/reviews/G1B_TASL_PRELAUNCH_REVIEW_20261121.md, docs/r1/reviews/G1B_TASL_DRYRUN_REVIEW_20261121.md) held EVIDENCE blocked; every condition they set is disposed of in the table "Conditions of the earlier reviews" of docs/r1/reports/g1b_tasl_note_20261121/G1B_TASL_NOTE_20261121.md; the launch chain of R1-T1-DATA-MANIFEST: docs/r1/reviews/TASL_LAUNCH_CHAIN_REVIEW_20261122.md; the census erratum record docs/r1/reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md sha256 9b40944be4df5f214066d689f7f0537590ed95895f9754b55630d8e774077799 (review docs/r1/reviews/T1_DATA_MANIFEST_ERRATUM_REVIEW_20261122.md)
P5: PASS — R1-G1B-EDITS: 4 declared edits, 460 runs per node
P6: PASS — R1-G1B-TIMEOUT: census_slowest_x3 (per-node values on the node lines)
P7: PENDING — R1-T1-TASL-ENV cross-host check, not yet run. Template for PASS, completed only after the three step-1 verdicts are on main and check-note2 passes: "PASS — R1-T1-TASL-ENV cross-host check: the reviewed job sweep2/t1_tasl/g1b_crosscheck.py (docs/r1/reviews/G1B_CROSSCHECK_REVIEW_20261121.md) ran under docs/r1/authorizations/g1b_xc_t1_tasl_<date>.md (the re-issued note, run g1b-tasl-20261121-b-xc2); step-1 verdicts PASS: <path> sha256 <sha256>; <path> sha256 <sha256>; <path> sha256 <sha256>; before assembly each node's G.1b TASL-7 attempt is compared with its cross-check TASL-2 attempt (compare --mode preassembly), and g1b_crosscheck.py assemble requires that PASS for the TASL-7 nodes; a cross_host_mismatch is decision XC-REMEASURE". While P7 reads PENDING, g1b_tasl.launch refuses every TASL-7 node
P8: PASS — R1-G1B-CAP: projection 28.262 GPU-h (sensitivity 41.644) under 100
P9: PASS — R1-TRACKG-G3-EARLY: the seven T1 nodes above; G.1b starts on them without waiting for the T2 list
P10: PASS — the launch binding verify_launch_tasl, the run_id and harness_commit checks of check_note, and the first note, independently reviewed: docs/r1/reviews/G1B_TASL_NOTE_REVIEW_20261121.md (decision LB); the cross-check job, its gated assembly and this second note: docs/r1/reviews/G1B_CROSSCHECK_REVIEW_20261121.md; the re-issued spec and this revision: docs/r1/reviews/TASL_LAUNCH_CHAIN_REVIEW_20261122.md
P11: PASS — reports on main: docs/r1/reports/trackg_g0_20261117/G1B_TASL_PRELAUNCH_20261121.md, G1B_TASL_DRYRUN_20261121.md (ENGINEERING dry runs under run_id g1b-tasl-20261121-a, hence the new run_id), TASL2_T1_PRECHECK_20261121.md (its "spec sha PENDING" line predates the spec; the spec binds the host check sha 681011b2), TASL7_T1_PRECHECK_20261121.md; the rows on main: docs/r1/PLAN.md R1-T1-HOST-TASL, R1-T1-TASL-ENV, R1-G1B-EDITS, R1-G1B-TIMEOUT, R1-TRACKG-G3-EARLY, R1-G1B-CAP

P12: PASS — autoresearch_fixedtokens is not in this run: it joins G.1b under the third note with its own spec (R1-G1B-NOTE2-DECISIONS NOTE2-AR A; R1-G1B-AR-ENV)
scope: this second note launches the three TASL-7 nodes of run g1b-tasl-20261121-b (spec as the amendment note, harness as the first note); the three sealed TASL-2 nodes stay under the first note and mlgym_fmnist runs under the amendment note; all seven nodes assemble into one row through the gated assembly of decision G1B-JOIN

STOPs (each returns to the author; outputs are kept, nothing is deleted or silently retried):
- a host name, GPU UUID, GPU model or driver other than above; a root uid; Yama ptrace_scope below 1; a scope without
  MemoryMax 8G and MemorySwapMax 0; a CPU affinity other than the node's cpus;
- a busy GPU lease, or a compute process of another owner on the leased GPU before or after any part;
- the harness not at c025f89a or not clean; an environment freeze, node data manifest or kit pin other than above;
- a run record that is not effective:true with empty waivers and exceptions;
- the first run that reaches its timeout on the 4090 (stop_class timing);
- a node or timing STOP ends the node; only an infrastructure STOP may be followed by a new attempt;
- the projection or the GPU-hours consumed passing 100 GPU-h;
- for a TASL-7 node, a cross-host default-part metric on TASL-2 that is not identical (R1-T1-TASL-ENV);
- any label, evaluation or sweep-2 file opened (none is needed).
