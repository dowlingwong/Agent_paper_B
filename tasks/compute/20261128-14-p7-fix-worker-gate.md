# compute/20261128-14 — D.3a P7: fix the worker-failure count (review B1), then re-review

The P7 review (`compute-d3a-p7-20261128-review` @ `9f1c0246`) is CHANGES REQUIRED on B1: `worker_gate.py` treats every `failed_invalid` record as an
uncharged precheck rejection, so the record says 0 worker failures; the captures show 33 charged failures (32 `invalid_config`, 1 `runtime_error`)
of 271 charged runs (12.18 %), and only 4 of 37 `failed_invalid` were uncharged prechecks (`worker_mode = local_worker_precheck`). Fix the
classification (charged = the worker ran: `worker_failure_message` / `run_command … success=False`), regenerate `worker_gate.json` and `p7_summary.json`,
correct the record's text and table, state the gate verdict against the declared threshold (no threshold changed), address the review's minors, and
get the re-check. Same captures, no rerun unless the reviewer asks. Priority: first, before any other work this round.
