# compute/20261128-03 — D.3 HTCondor single-GPU preflight: submit now (A100 / L40S reported free)

The author reports (28 Nov): GridKa TOpAS has 7 free A100 on `c03-001-175`, and the ETP L40S is free. Re-run `compute/20261127-12` now, under
R1-P4-D3-GPU-PREFLIGHT (2), which names "one matched ETP L40S or TOpAS A100". **Submit a new job; do not edit any existing request** (the stale probes
`759624`/`759625` from 13 Nov and the P.4 H200 test `760065` are not to be changed). First check the slots' `Start` expression with `condor_status`
(earlier it was `false`); if a slot is startable, submit the D.3 preflight with a request that matches it, the candidate pinned container, the inputs
staged by file transfer for TOpAS (no `/work`, `/ceph`), and their hashes checked inside the job. ENGINEERING_ONLY; not the per-arm smoke and not
evidence. If `Start` is still false, report the exact expressions and do not work around them. Report job id, matched machine and GPU, container digest,
input hashes, and anything unverified. Priority: right after the TASL-7 E0 reference has started (both can run at once).
