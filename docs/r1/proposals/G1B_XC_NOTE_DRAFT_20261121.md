# G.1b cross-host check — authorization note (R1-T1-TASL-ENV; ENGINEERING_ONLY) — DRAFT for the author's signature

This draft is in the key-block format `sweep2/t1_tasl/g1b_crosscheck.py check_xc_note` parses. On signature the author
copies it to `docs/r1/authorizations/g1b_xc_t1_tasl_<YYYYMMDD>.md` with `approved: true` and `paper_commit` and
`xc_spec_sha256` filled, in the same commit as the cross-check spec's `paper.commit` (the launch commit, as for the
G.1b note): `paper_commit` is the main commit that carries `g1b_crosscheck.py`; the hosts launch from that published
commit. Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026; independently reviewed (P4).

approved: false
label: ENGINEERING_ONLY
labels_read: none
run_id: g1b-tasl-20261121-b-xc
paper_commit: <FILL at the launch: the main commit carrying g1b_crosscheck.py; equal to the cross-check spec's paper.commit>
xc_spec_sha256: <FILL at the launch: sha256 of sweep2/t1_tasl/g1b_crosscheck_spec.json as committed on the launch main>
g1b_spec_sha256: 060aac91ba452a69e4e898b66b92ebd5bfc0887c2933cfd2e438d93d17ecb465
harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702
host_row: R1-T1-TASL-ENV
jobs: six default-part jobs (mlab_cifar10, mlgym_cifar10, mlgym_breakout_minatar, each on TASL-7 and on TASL-2): 10 runs each, 60 runs in all, under the G.1b preflight, lease, delegated scope and row gate; run ids g1b-tasl-20261121-b-xc-TASL-7 and g1b-tasl-20261121-b-xc-TASL-2; sealed with g1b_tasl.py seal against the derived specs
envs: TASL-2 gains jax312 (/home/dowling/r1_tracks/t1_tasl/envs/jax312/bin/python, the census freeze, as the pre-launch report built it) for mlgym_breakout_minatar; nothing else changes
projection: about 1 GPU-h (the three nodes' default parts on both hosts: 10 x (12.3 + 31.7 + 61.2) s per host plus setup), within R1-G1B-CAP beside the G.1b projection
verdict: g1b_crosscheck.py compare per node (TASL-7 attempt against TASL-2 attempt): PASS when every default and default_repeat outcome is identical and both sides are deterministic; a STOP means that node's G.1b is re-measured on TASL-2 (the author decides)
P1: PASS — R1-T1-TASL-ENV: the G.1b TASL-7 nodes' default parts on TASL-2, metrics identical (R1-G1B-TASL-DECISIONS XC A)
P2: PASS — TASL-2 harness-isolation host check docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md sha256 681011b2114f6ff7db679d3265535d1cc2e8a9bdbc231371230f4de42d7b6b6d
P3: PASS — TASL-7 harness-isolation host check docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md sha256 09945c15df67b2627a97e6cc59239744738aecb14e522f7c52d1f390be4576a4
P4: PENDING — independent review of the cross-check unit: docs/r1/reviews/G1B_CROSSCHECK_REVIEW_20261121.md (the author sets PASS on signature)

STOPs (as G.1b; each returns to the author, outputs kept): any preflight refusal (host, GPU UUID, driver, uid, ptrace, scope,
affinity, harness, env freeze, data manifest, foreign process, lease); a row that is not effectively isolated; a default-part
timeout on the 4090; a non-deterministic default part; a verdict that is not PASS.
