# S2-C3 / S2-C3b operator follow-up (when the queued ENGINEERING jobs finish)

The 3 S2-C3 jobs are queued on deepthought: **759736** digits_mlp, **759737** openml_credit_approval,
**759738** openml_ionosphere; submit dirs `/work/dwong/htcondor_prep_20261114/s2c3_run_20261116_a/<node>/`.
They are idle only because no NEMO2 `g36xx` L40S slot is currently advertised (H200/CPU nodes and the
deepthought2 portal L40S do not match the pinned `CloudSite=Nemo2, GPUs_DeviceName=NVIDIA L40S, Arch/OpSys,
Cpus>=16, CpuFamily=6, CpuModelNumber=207` requirements). When the nodes return the jobs run themselves; the
operator then:

## S2-C3 (3 jobs; driver `s2c3-driver-fix-20261116` @ `52e023e6`)

1. Check each job ended rc 0 and its output dir has `out.tar`, `work.tar`, `job_record.json`, `SHA256SUMS`,
   `llama-server.log` (the pre-created placeholders are overwritten on success; a STOP keeps a `stop` record and
   the tars).
2. **Seal each chunk on deepthought** (the `/ceph` target is ETP-side). Copy the reviewed driver files to the submit
   host once, e.g. `sweep2/s2_c2_lib.py`, `sweep2/s2_c3_replay.py`, `sweep2/s2_c3_compare.py`, the three
   `sweep2/spec.replay.*.json`, `sweep2/s2_c3_driver_shim.diff`, `sweep2/s2_c3_label_patch.diff`,
   `sweep2/s2_c3_declared_inputs.json`, `sweep2/s2_c3_inputs/`, `sweep2/dryrun/replay/` into
   `<submit-run>/driver/` (keep the repo-relative layout so `HERE.parent` resolves). Then per node:
   `cd <submit-run>/<node> && python3 ../driver/sweep2/s2_c3_replay.py seal . --run-id s2c3-20261116-a --chunk-id <node>`
   (verifies the transferred SHA256SUMS and record pins; writes `SEAL_RECEIPT.json` under
   `/ceph/srv/dwong/paperb/sweep2/s2c3-20261116-a/<node>/`; no overwrite).
3. **Compare** (Mac checkout of the driver branch, or the same files on deepthought):
   `python3 sweep2/s2_c3_compare.py <digits_mlp> <openml_credit_approval> <openml_ionosphere> --out docs/r1/reports/sweep2_20261116/S2_C3_RESULTS.md`
   (the three paths are the transferred job output dirs; criteria 1–6 as pre-declared/corrected: final_y ±0.02/
   mean ±0.01, parse 0/240 ≤0.02, diagnostics 20/33/20 ±10 %, full 61/61 offload, ≤2× B2 GPU time, no STOP).
4. Commit the sealed receipts + `S2_C3_RESULTS.md` on a reviewed ops/report branch (no labels read; ENGINEERING) and
   get the independent review of the deployment check before claiming P4.

## S2-C3b (after S2-C3; assets already staged and dry-run verified)

Staged on deepthought: `/work/dwong/htcondor_prep_20261114/s2c3b_run_20261116_a/` (JDL + staged inputs; real
`condor_submit -dry-run` rc 0, `RequestDisk=42460977`, `RequestMemory=32000`, `RequestWalltime=12203`). Submit with
`condor_submit s2_c3b.jdl` from that dir **after** the S2-C3 run/operator follow-up (author order). On completion:
`cd <submit-run> && python3 sweep2/s2_c3b_lib.py seal . --run-id s2c3b-20261116-a --chunk-id liveness-prompt`
(with the c3b branch files on the submit host) and commit the liveness/prompt comparison report.

## Guardrails

No B.2 audits; no 7001–7010/8001–8010/9001–9303 seeds; no label read; ENGINEERING_ONLY; seal only after the job
transferred its outputs; no overwrite of sealed paths; nothing deleted (failed jobs kept, move aside if needed).
