# Authorization: G.1b T1 noise floors on NEMO2 H200 (ENGINEERING_ONLY) — unapproved template

The cluster agent fills the bracketed values from the reviewed, launch-ready stage (`g1b_render_jdl.py` without
`--preview`, then `g1b_switch.py check`). The coordinating chat publishes the note to `main` as
`docs/r1/authorizations/g1b_t1_h200_<YYYYMMDD>.md`. Keep `approved: false` until the author signs and every
prerequisite is recorded as PASS. The switch also needs `--enable` and `G1B_ENABLE_REAL=1`, and it submits the
first node (`mlab_ogbn_arxiv`, the shortest) alone: the other five only with `--first-record` pointing at that
node's sealed job record, which must show no STOP (environment, data pin, cgroup, isolation gate and determinism all
passed on H200).

approved: false
label: ENGINEERING_ONLY
run_id: g1b_t1_h200_20261120
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd
versions_sha256: <sha256 of /opt/r1/VERSIONS.txt in the v2 gpu image, from a v2 H200 job record>
harness_commit: <the pushed T1 harness commit in g1b_spec.json>
paper_commit: <the launch commit (spec paper.commit); descends from main>
spec_sha256: <sha256 of the staged g1b_spec.json>
nodes: mlab_cifar10,mlab_imdb,mlab_ogbn_arxiv,mlgym_cifar10,mlgym_fmnist,mlgym_breakout_minatar
n_edits_per_node: <4, or 5 if the author chooses option B of G1B-EDITS>
runs_per_node: <460 for four edits; 552 for five>
gpu_hours: <reviewed projection, at most 100 (R1-G1B-CAP)>
P1: PASS — R1-T1-HOST-H200 host check: harness isolation works inside the v2 container on H200 (record <path>)
P2: PASS — R1-TRACKG-G3-EARLY: the six isolated-U2 census nodes
P3: PASS — R1-G1B-EDITS: the author's decision on the declared edit count
P4: PASS — this G.1b unit independently reviewed; the job code is at the launch commit
P5: PASS — the v2 VERSIONS sha256 above is read from a v2 job record on H200 (record <path>)
d8_lock: true
labels_read: none
