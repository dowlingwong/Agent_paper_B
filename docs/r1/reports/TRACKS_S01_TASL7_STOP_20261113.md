# Track S `digits_mlp` S0.1 on TASL-7 — STOP (13 November 2026)

**Run-internal STOP at the S0.1 gate; preserved and reported, not retried.** Under the author's 13 Nov revision
(STOP of B1 `_c` allows the host move), the `_c` Track X marker was retired by the accepted STOP-case unit (marker
renamed into `_to_delete/`, creation and retirement receipts kept, `_c` STOP scene byte-untouched, all seven scene
hashes equal to the accepted capture). Then the TASL-7 preparation was executed: paper checkout fetched and detached
at pin `8237fd02b09ef2d28016a1c9f6acac3c35bb768b` (clean, non-shallow), prior `a2u_prior_r2_20261111.json`
(sha256 `5c849d151d939a183ecf6c21113cc46aee6a457142e1c7ed9704b48d77eed607`) copied to
`$OUT/digits_mlp/`, and the k=2 servers started (`tmux trks_llm`, 18101/18102, lease held).

## 1. What happened

- 2026-11-13T10:50:12Z: `tasl7_digits_s01_20261113.sh` started in tmux; launch log: `S0.1 start (node digits_mlp,
  host TASL-7, k=2 probe period)` then `both endpoints ready`; the serial probe started in `trks_s01_serial`.
- Serial probe repeat 1 (`$R/logs/trks_s01_serial.log`):
  `{"http://127.0.0.1:18101/v1": {"latency": {"n": 600, "mean_s": 0.658…, "p95_s": 0.716…}, "errors": 0,
  "identity_rate": 0.87, "clients": 1, "identity_rate_per_client": [0.87], ...}}`
  Repeats 2 and 3: `"errors": 600, "identity_rate": 0.0` (n=0).
- **S0.1 identity < 100 %** in the serial setting (0.87 on the only completed repeat), which is the Track S operator
  runbook §10 "S0.1 identity < 100 % in both settings → STOP (author)". The probe's requests carry a fixed seed and
  `temperature 0.2` (probe code at the pin), so identical repeats are expected to be identical.
- The server log tail shows the 18101 server declining/queueing a task (`process_new_: processing task …; decoding,
  decline task`), consistent with the later 600-error repeats (requests not served rather than wrong content).
- We stopped our own S0.1 sessions and servers (10:51:25Z): tmux now only `trks_watch`; no `llama-server`/probe
  process; `gpu0.lock` free; GPU no compute app. No retry was attempted.

## 2. Preserved evidence (nothing deleted or overwritten)

- `$R/logs/s01_t7_20261113_launch.log`; `$R/logs/trks_s01_serial.{cmd,log,exit}` (the exit file still shows the old
  Oct entries because the probe was stopped before writing a new rc); `$R/out/digits_mlp/s01_t7_20261113/` (empty
  result dir); `$R/logs/llama_18101.log` and `llama_18102.log` (append-only, large; today's tail included the task
  decline/queue lines); capture under `/private/tmp/trks-s01-t7-stop-*` (read-only) and
  `/private/tmp/b1-c-stop-retirement-capture-*` for the retirement.
- The `_c` STOP scene (batch, unit logs, root_events/trials, node, `b1.log`, `b1.exit`, handover, staged checkout) is
  untouched (hash-equal to the accepted STOP capture); B1 is not retried; the Track S move is now STOPPED at S0.1.
- The TASL-7 paper checkout remains at pin `8237fd02` detached/clean; harness `a3fedbb`; prior file present with its
  sha; the k=2 server tmux session was stopped cleanly; no Track S session remains.

## 3. Interpretation

- The S0.1 gate is exactly the host-change risk check. It failed on TASL-7: serial identity 0.87 < 1.0 and the
  serving layer later declined requests. Candidate causes to diagnose (no conclusion yet): host/driver-specific
  nondeterminism (TASL-7 driver 580.178.04/CUDA 13.0 vs TASL-2 535/12.2; same llama.cpp commit 620d2225 built per
  host), and/or serving instability with two 7B servers on the single 4090 (both at `-ngl 999 -c 8192 --parallel 1`)
  under the probe's random-order load.
- This is an author gate (runbook §10): **STOP and ask**. S0.5 must not start; no retry, no parameter change and no
  pin change without the author's decision.

## 4. Next step for the author

Options for the author's decision (no action taken):
1. Authorise a **diagnostic rerun** of S0.1 on TASL-7 under explicitly reviewed conditions (e.g., single server only,
   or k=1 with a documented reason; cold server; a shorter probe), reported separately;
2. Wait for TASL-2 to return and run/continue there (TASL-2 is still unreachable; its scene is preserved and must only
   be censused);
3. Treat TASL-7 as unusable for `digits_mlp` and keep Track S paused.

Until then the Track S line is STOP: no S0.5, no copy-back, no further host changes. B1 `_c` remains STOPPED and
untouched; its marker is retired with receipts; a future B1 `_d` D-B1R still takes priority (READY.txt/origin polling
continues every 30 minutes).
