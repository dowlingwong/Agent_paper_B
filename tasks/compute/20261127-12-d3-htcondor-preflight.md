# compute/20261127-12 — D.3 single-GPU HTCondor preflight (R1-P4-D3-GPU-PREFLIGHT (2)), ENGINEERING_ONLY

Owner: compute. PLAN **R1-P4-D3-GPU-PREFLIGHT** (`main` `42af62c6`). In parallel with the Ada probe preparation and the G1 code.

On one matched ETP L40S (deepthought2 advertises one) or a TOpAS A100: check that the scheduler matches the intended request; start the
candidate pinned container (v2.2 digest on `main`); inside the job, validate the GPU and read the inputs. TOpAS workers lack ETP's
`/work` and `/ceph`, so stage the inputs from the submit side by HTCondor file transfer (or an approved staging path) and check
their hashes inside the container. Use only approved, non-sealed inputs. This is not D.3 per-arm smoke and not evidence. Do not edit a
request to get a slot; an unmatched request is a finding. Report: job ids, matched machine and GPU, container digest, input hashes,
and anything still unverified.
