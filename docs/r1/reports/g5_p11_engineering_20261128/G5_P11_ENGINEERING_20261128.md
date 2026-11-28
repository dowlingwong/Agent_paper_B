# G.5 P11 engineering smoke — STOP: the reviewed synthetic kit fails its baseline; two seal CLIs refuse themselves

Task `compute/20261128-09` (G.5 P11 matrix, supersedes `compute/20261128-05` item 1), PLAN **R1-G5-P11**.
Base `origin/main` `cb20c9fd`; tested code `b9e195acf3b0494410cbc752568ea920ef1623d6` (the accepted task tip).
ENGINEERING_ONLY; no label, test or evaluation value was read.

**Result: STOP. The matrix cannot reach its host checks.** Both nodes' first synthetic campaign stops at
`STOP 6: baseline_failed` before any proposal runs. The cause is a mechanical mismatch between the reviewed kit and
the pinned G.5-7 harness, not a host failure: the kit writes its `step` line only to the isolated result channel,
while the pinned outcome parser reads `steps_regex` from the run log, so `last_step` is null and every baseline is
`budget_not_reached`. A second defect blocks C9 and the `close-server` branch of C15: `close-attempt` and
`close-server` list their own Python process in `processes_mentioning` (the attempt/server path is in their argv)
and therefore always refuse. Nothing was patched or widened.

## Environment

| Host | Role | GPU | Driver | State at start |
|---|---|---|---|---|
| TASL-2 | worker / campaigns / audits / seals | RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94` | 535.309.01 | empty card, CPUs 0-7 free |
| TASL-7 | proposer server | RTX 4090 `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` | 580.178.04 | empty card, GPU lease free |

Clean checkout of `b9e195ac` on both hosts (`~/r1_engineering/g5-p11/repo`); harness `cbf7a003…` on each host.
`G5_TASL_ENABLE_REAL` unset. Specs are `g5-p11-20261128T014000Z-<suffix>.json` under `~/r1_engineering/g5-p11`;
the primary spec sha256 is `a10e5ef8cbb985474473a3e3fec00fd7a71fb9ba787968a13ed8f2eb5a5fc560` on both hosts.

## What passed

- **Setup and validation.** `p11-init` produced byte-identical specs on TASL-2 and TASL-7; `validate --launch
  --engineering` passed. `P11` spec files for the primary, `-determinism`, `-restart`, `-infra`, `-tar` and
  `-closeserver` scenarios were created; no scenario was resumed or overwritten.
- **Proposer server start.** TASL-7 started `llama-server` at `2026-11-28T02:04:34Z`; record
  `server_record.json` sha256 `847698cedfea0b93e680901c51e8a615c58299846ce5a2465884c91b48929867`.
  Binary sha256 `b70f4882…`, model sha256 `2959c1b0…`, build `0.7.0-dev (build 1, commit 620d222)`, GPU
  `GPU-ab72fb4a…`. The record was copied byte-for-byte to TASL-2 (`incoming/.../server-1.json`, same sha256).
- **Proposer link probe.** TASL-2 `p11-probe` PASS: `/health` ok, `/props` context 32,768, one slot, build
  `b1-620d222`, model `google_gemma-4-31B-it-Q4_K_M.gguf`; one completion 0.196 s; health median 30.68 ms
  (`g5-p11-20261128T014000Z-lease.probe1.json`).
- **Server seal and span.** `seal-server` on the stopped `server-1` PASS (procedural seal, span 112 s); the receipt
  was copied to TASL-2 and `server-span` accepted it. Server ended cleanly (`server_rc 0`, `stop_signal 15`).

## The blocking baseline STOP

Both `campaigns-wave1` attempts stopped after the baseline:

| Node | Diagnostic | Job record | GPU-s |
|---|---|---|---|
| `mlab_imdb` | `STOP 6: baseline_failed` (node) | `attempt-1` | 3.2 |
| `mlgym_breakout_minatar` | `STOP 6: baseline_failed` (node) | `attempt-1` | 3.3 |

The baseline run itself exits 0. The isolated worker returns the checksum and the trusted parent writes

```
step 5 loss: 0.998046875
val_accuracy: 0.001953125
test_accuracy: 0.001953125
```

to the **result channel** (`result_channel.txt`, 78 bytes). The run log contains only the runner line
`AR_RUNNER result_channel_sha256=… bytes=78`. The pinned harness (`cbf7a003`) classifies the run in
`src/autoresearch/trackg/outcome.py`: the selection metric is read from `result_text` when isolation is active, but
the step count is still read from `log_text`; with no step line there, `last_step` is null and the outcome is
`divergent/budget_not_reached`, which the campaign records as `baseline_failed`. That is a kit–harness interface
defect: the reviewed `parent.py` must also put the step line in the run log, or the pinned parser must read steps
from the result channel. It is not a TASL-2 or GPU failure.

Because each node now has a node-class STOP, `t1_tasl_node.sh` refuses every later job on that node:

```
STOP: mlab_imdb has a STOP on record (…/campaigns-wave1/attempt-1: STOP 6: baseline_failed);
the author decides before anything else runs
```

Therefore **C2, C4, C5, C14 and the wave-1/wave-2 campaign and audit commands are not covered** in this round.
The primary server was stopped after the probe; its GPU lease is free.

## The two seal-CLI refusals (C9 and C15 `close-server`)

`close-attempt` on the closed fixture stopped at:

```
STOP: processes [1022275] still name …/runs/g5-p11-20261128T014000Z-closed/mlab_imdb/campaigns-wave1/attempt-1
on their command line
```

`close-server` on the separate `-closeserver` scenario stopped at:

```
STOP: processes [2554947] still name …/proposer/g5-p11-20261128T014000Z-closeserver/server-1
on their command line
```

In both cases the listed PID is the calling process itself (or its parent shell), because the attempt/server path is
part of its command line. A read-only diagnostic reproduces this: with the path passed as `argv[1]`,
`processes_mentioning` returns `[parent, self]` (`close_attempt_selfscan.txt`, `close_server_selfscan.txt`). The
check therefore refuses every correct invocation. This is a defect in the reviewed engineering path; it is not a
live process and no foreign process was present. The separate `server-1` was killed without a normal end record; as
designed, `seal-server` then refused until `close-server` writes one.

## Not covered / next

- C2, C4, C5, C6, C9, C10, C11, C14, C16: blocked by the two defects above; no PASS is claimed.
- C15: `seal-server` and `server-span` exercised; `close-server` blocked by the self-scan refusal. Real assembly and
  release remain behind the signed sequence.
- Gate: none of this enters a release or a G.5 label; no sealed partition was read.
- Next: local fixes the kit step-line interface and the `processes_mentioning` self-exclusion for `close-attempt` /
  `close-server`; the coordinator re-issues the matrix card. Then rerun from a fresh commit and fresh IDs.

## Files

`tasl2/` and `tasl7/` hold the specs, probe output, server record/end/seal/span, both campaign diagnostics, job
records, ledgers, run logs, result channels, the refused node log and the two self-scan diagnostics.
`SHA256SUMS` binds the set.

Decided alone: host placement (TASL-2 worker, TASL-7 proposer), the scenario timestamp, and stopping the server after
the primary probe once both nodes recorded the node STOP; no code, tolerance, note, seed or request was changed.
