# B1 `_c` STOP — fixed-prompt replay of trials 018–020 for the experiment agent (13 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local agent). This is item (1) of the author's route for the STOP of run `4b31_20261112_c` (`reports/B1_STOP_4B31_20261112.md`, `mac-b1-20261107` @ `3b7d5704`; PLAN §10 `R1-EXAM-B1-MODEL-OUTPUT-INVALID`). The replay is optional for the fix and is **not** a restart precondition. It names the exact reply that stopped trial 020 (diagnosis `reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md` §1.4). It runs on TASL-7. **The `_c` scene is only read**: everything the replay writes goes to a new directory under `/tmp`.

Below:
- `B=/home/dowling/exam-x/work/b1_4b31_20261112_c`
- `D=$B/olmo31_32b/b1/off/openml_credit_approval__s9002`
- `R=/tmp/b1_replay_4b31_<UTC timestamp>` (new; must not exist).

## 0. Boundaries and occupancy

- Do not modify, move or delete anything under `$B`, the `_c` handover directory, the staged checkouts, the `_b` or 6835 scenes, or `~/r1_locks`. In particular, leave the `_c` Track X marker as it is.
- The replay starts one llama-server for `olmo31_32b` for a few minutes. Follow the TASL-7 occupancy rules (R1-TASL7-AGENT-OCCUPANCY-07NOV):
  - Run a read-only census first (`nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv`).
  - If any compute application is present, do not start; report.
  - Never preempt anyone.
  - Stop the server when done, and run the census again.
- Use the frozen venv `/home/dowling/exam-x/work/venv` with `PYTHONDONTWRITEBYTECODE=1`. Use a clean checkout of `mac-b1-modelout-20261113` at the reviewed base, placed under `$R/paper` (not one of the staged checkouts). Use the staged harness `/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness` (`a3fedbb`) as `AR_HARNESS_ROOT`.

## 1. Copy the root

`mkdir -p $R && cp -a $D $R/root`, then `sha256sum $R/root/root_trials.jsonl $R/root/root_events.jsonl`. Both must equal the STOP report §5 values (`8c9fbfb0…`, `dad927e2…`). If they differ, STOP.

## 2. Start the server with the run's recorded argv

- **Record.** Take the newest `olmo31_32b` server record in `$B/servers/olmo31_32b/` (a `*.json` with `'argv'`, `'port'`; the off-mode interval). Use its `argv` unchanged except for the value after `--port`, which becomes a free port `P`.
- **Checks before start:**
  - the binary's SHA-256 equals `server.binary_sha256` in `exam_b1_v2.json`;
  - the model file's SHA-256 equals the registry's `quant_source.sha256` for `olmo31_32b`.
- **Environment:** the current one minus `LLAMA_ARG_*` and `LLAMA_API_KEY`, with `CUDA_VISIBLE_DEVICES` set to the config's `gpu_uuid`.
- **Start.** Log to `$R/server.log` and wait for `GET http://127.0.0.1:P/health` to answer ok.
- **Verify.** `GET /v1/models` must list the alias `olmo31_32b`.

## 3. Replay

```
cd $R/paper && AR_HARNESS_ROOT=<staged harness> PYTHONDONTWRITEBYTECODE=1 \
  /home/dowling/exam-x/work/venv/bin/python -m r1.scripts.b1_proposal_replay \
  --root-copy $R/root --candidate olmo31_32b --node openml_credit_approval --seed 9002 \
  --trials 18,19,20 --base-url http://127.0.0.1:P/v1 --out $R/replay > $R/replay_stdout.json
```

The script makes one proposer call per trial, 3 in all. It executes nothing and writes only under `$R/replay`.

## 4. Stop and deliver

1. Stop the server (SIGTERM to its process group) and run the census again.
2. `sha256sum $R/root/root_trials.jsonl $R/root/root_events.jsonl`. They must be unchanged.
3. Copy to the Mac, in `~/Documents/agent_paper_B/Claude outputs/b1_4b31_replay_20261113/`:
   - `replay.json`;
   - `replay_stdout.json`;
   - the server record you used;
   - the last 200 lines of `server.log`;
   - `census_before.txt`, `census_after.txt`;
   - a `SHA256SUMS`.
4. Tell the Mac-local agent, who adds the result to the diagnosis §1.4 and has it reviewed.

**Reading the result:**
- *Reproduced*: for 018/019, `context_sha256`, `raw_proposal_sha256` and the incumbent metric match; for all three trials, each `llm_call_event` pair matches. In that case, trial 020's `reply_fields`, `directive` and `new_precheck.check` name the mismatch.
- *Not reproduced*: report it as such. The diagnosis then keeps the exact reply as not established.

Either way, do not interpret further, and do not retry beyond one run.
