# G.5 P11 engineering matrix — independent review, 28 November 2026

- Date: 2026-11-28 (Europe/Berlin). Independent reviewer, read-only on both hosts: no job, submission, signal,
  edit, delete or host write was made. The only write is this review, on the review branch.
- Deliverable: `origin/compute-g5-p11-matrix-20261128` at
  `ba02dc21d1f7ae29264f290b20e762c32835a100` (parent `f4704bf2`), which applies the two
  non-blocking findings of the first review pass. The earlier tips `f4704bf2` (captures) and
  `0a748818` (original record) are superseded.
- Re-check: `git diff f4704bf2..ba02dc21` touches exactly three paths — the record (two edits: the
  close-server quote and the `server-span` registration sentence), the regenerated `SHA256SUMS`,
  and the new `tasl2/server-span-registration.json`. No other content changed; the diff is 32
  insertions and 3 deletions. `shasum -a 256 -c SHA256SUMS` now returns **50/50 OK, exit 0**.
- Tree: this is one record commit on `origin/main` `914e1cf9`, the capture commit, and the
  minor-fix commit. The record's stated base `cb20c9fd` is the merge that accepted the tested P11
  code; `914e1cf9` is the later main tip the record was cut from. Tested code
  `b9e195acf3b0494410cbc752568ea920ef1623d6`; pinned harness
  `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98`.
- Task `compute/20261128-09`, PLAN **R1-G5-P11**.
- Review branch: `compute-g5-p11-matrix-20261128-review`, created from `f4704bf2`; the first
  commit (`2fa851e6`) reviewed `f4704bf2`, and a second commit updates this file to re-check
  `ba02dc21`. The deliverable branch is untouched.

**Verdict: ACCEPTED — the STOP is correctly established; the `f4704bf2..ba02dc21` diff is clean and fixes both minors.**

The three STOP facts hold on the files, the pinned code and the host captures. Both synthetic
campaigns stop at `STOP 6: baseline_failed` because the pinned harness reads the step count from
the run log while the kit writes it only to the isolated result channel; that is a kit–harness
interface defect, not a TASL-2/host failure. Both seal CLIs refuse because `processes_mentioning`
lists the caller's own process; the self-scan diagnostics and the code confirm it. The passing
items (spec, server record, probe, seal and span) are real, and no sealed or paper test value was
read. Two non-blocking documentation issues were raised in the first pass; both are fixed in
`ba02dc21` (see Findings). The STOP remains correctly established.

## Checks and results

### 1. Branch, capture set and hashes — PASS

- `git rev-parse origin/compute-g5-p11-matrix-20261128` → `ba02dc21d1f7ae29264f290b20e762c32835a100`.
- `git diff --name-status f4704bf2 ba02dc21` → `M` record, `M` `SHA256SUMS`, `A`
  `tasl2/server-span-registration.json`; no other path. `git diff --stat` is 32 insertions and
  3 deletions.
- `shasum -a 256 -c SHA256SUMS` in the record directory at `ba02dc21`: **50/50 OK, exit 0**.
  The new entry `./tasl2/server-span-registration.json` hashes to `2a76ea7a…`; the record entry is
  the regenerated `b8358662f42b3869cb53b10c007b5a30eb9205923114622dba45f8855deb4451`.
  At `f4704bf2` the same check was 49/49; at `0a748818` it failed on 16 absent `.log`/`.jsonl`
  paths, fixed by the capture commit.

### 1a. Re-check of `ba02dc21` — PASS

- **MINOR-1 is fixed.** The `close-server` code block now ends at
  `…/proposer/g5-p11-20261128T014000Z-closeserver/server-1`, with no suffix, and the note
  immediately after it says the `close-attempt` message adds `on their command line` while
  `close-server` does not. This matches `tasl7/g5-p11-20261128T014000Z-closeserver.close-server.log`
  and `g5_seal.py:694`.
- **MINOR-2 is fixed.** `tasl2/server-span-registration.json` is committed and hashes to
  `2a76ea7a8287fe9f0bf034e940e12e7019b3e8a46446204ff8f11f86aadcc1c3`, byte-identical to the
  TASL-2 `runs/g5-p11-20261128T014000Z-lease/_server_spans/server-1.json` re-read from the host.
  The record's seal/span paragraph now names it, and `SHA256SUMS` binds it.
- **No other content changed.** The diff is limited to the two quote/registration edits and the
  sums; the A/B/C/D evidence, `run.log`, result channels, ledgers, node logs, self-scans and
  server records are unchanged from `f4704bf2`.

### 2. A — both synthetic campaigns stop at `STOP 6: baseline_failed` — PASS

On TASL-2, in `tasl2/mlab_imdb` and `tasl2/mlgym_breakout_minatar`:

| Item | `mlab_imdb` | `mlgym_breakout_minatar` |
|---|---|---|
| node log | `STOP 6: baseline_failed`, `NODE_EXIT=2` | same |
| `diagnostics.json` | `"stop": "STOP 6: baseline_failed"`, `stop_class: node`, `gpu_seconds: 3.2` | same, `3.3` |
| `campaign_record.json` | `"stop_kind": "baseline_failed"` | same |
| `attempt.json` | attempt 1, pid `1037220` | attempt 1, pid `1038323` |

The ledger (`campaign_ledger.jsonl`) records the exact cause, not merely the label:

```
"decision": "baseline_failed",
"final_outcome": {"kind": "divergent", "reason": "budget_not_reached",
                  "detail": {"budget": 5, "last_step": null}, "value": null}
```

The baseline process itself exited 0 (`process.returncode: 0`, no timeout, no launch error); the
engine exit code 3 is the campaign's STOP, not the run's. The result channel is 78 bytes and holds
exactly:

```
step 5 loss: 0.998046875
val_accuracy: 0.001953125
test_accuracy: 0.001953125
```

The committed `run.log` (107 bytes, sha256 `73c84ac11a9984464c9f931de781afc241bff52fe9ddf37acde9f2aa54f8406c`)
contains only a blank line and:

```
AR_RUNNER result_channel_sha256=63ba9190d5750bff93f7fed914aed1ffa28c31c29ef072c2c9610b080efcc196 bytes=78
```

The pinned harness explains the outcome. At `cbf7a003`, `src/autoresearch/trackg/outcome.py`
lines 168–175 set `metric_source = result_text` when the run is isolated, but lines 201–206 still
search `steps_regex` only in `log_text`:

```python
steps = [parse_float_token(m.group(1)) for m in re.finditer(steps_regex, log_text, re.MULTILINE)]
...
if last is None or last < budget_steps:
    return RunOutcome.divergent("budget_not_reached", last_step=last, budget=budget_steps)
```

`node.json` declares `run_budget: {kind: steps, value: 5}` and `steps_regex: ^step\s+(\d+)\b`.
The run log has no step line, so `last_step` is `None`; the outcome is
`divergent/budget_not_reached`. `campaign_v2_diff.py:453–455` then writes
`decision="baseline_failed"` for any non-OK baseline. This is exactly what the ledger and node logs
show.

**Host vs interface.** The run returned 0, the worker produced the checksum, the trusted parent
wrote the metric/step/test lines to the result channel, the isolation cgroup was effective and the
run log was intact. There is no GPU, transport, isolation or deadline failure. The cause is the
split source: the reviewed `parent.py` writes the step line only to the result channel, while the
pinned parser reads steps from the log. Either the kit must also put the step line in the run log,
or the parser must read steps from `result_text`; the record states both options. The STOP is a
correct engineering STOP, not a host failure.

The later `mlab_imdb-20261128T020814Z-1039923.node.log` also confirms the node-level consequence:

```
STOP: mlab_imdb has a STOP on record (.../campaigns-wave1/attempt-1: STOP 6: baseline_failed);
the author decides before anything else runs
```

### 3. B — `close-attempt` and `close-server` refuse themselves — PASS

The committed captures contain the exact refusals.

`tasl2/closed.log` (two invocations of the same closed-attempt fixture):

```
STOP: processes [1021816] still name /home/dowling/r1_engineering/g5-p11/runs/g5-p11-20261128T014000Z-closed/mlab_imdb/campaigns-wave1/attempt-1 on their command line
STOP: processes [1022275] still name /home/dowling/r1_engineering/g5-p11/runs/g5-p11-20261128T014000Z-closed/mlab_imdb/campaigns-wave1/attempt-1 on their command line
```

`tasl7/g5-p11-20261128T014000Z-closeserver.close-server.log`:

```
STOP: processes [2554947] still name /home/dowling/r1_engineering/g5-p11/proposer/g5-p11-20261128T014000Z-closeserver/server-1
```

The self-scan diagnostics show the parent and the caller:

```
tasl2/close_attempt_selfscan.txt:  self 1041020 / scan [1041019, 1041020]
tasl7/close_server_selfscan.txt:   self 2555418 / scan [2555417, 2555418]
```

The mechanism is in the reviewed code at `b9e195ac`:

- `sweep2/t1_tasl/g1b_tasl.py:1004–1017` `processes_mentioning` builds needles from the path and
  returns every `/proc/<pid>/cmdline` containing one of them. There is no exclusion for the caller.
- `sweep2/t1_tasl/g5_job.py:2051–2074` `close_attempt` calls `scan(attempt_dir)` and raises
  `STOP: processes {running} still name {attempt_dir} on their command line` when the scan is
  non-empty. The CLI passes `Path(a.attempt_dir)` from `argv`, so the caller's own cmdline contains
  the path.
- `sweep2/t1_tasl/g5_seal.py:674–694` `close_server` does the same with `scan(src)`, where `src` is
  the server directory supplied on the command line; its message is
  `STOP: processes {running} still name {src}`.
- Dispatch: `sweep2/t1_tasl/g5_tasl.py:3075` (`close-server`) and `:3255` (`close-attempt`).

The attempt owner is pid `1021754` and the `-closeserver` server is pid `2554860`; the refusal PIDs
are later, and no `llama-server`, `g5-p11` or attempt process is alive now. The job records' three
`foreign_checks` are empty, and the self-scan reproduces the self-match from a fresh process. The
refusal is therefore a defect in the reviewed engineering path, not a foreign/live process. The
record's conclusion holds.

### 4. C — the passing items are real — PASS

| Item | Evidence |
|---|---|
| primary spec sha256 | `a10e5ef8cbb985474473a3e3fec00fd7a71fb9ba787968a13ed8f2eb5a5fc560` on TASL-2 and TASL-7; `sha256sum` of both host files and both committed recipe files agrees |
| init spec | `2357bd0ce47ed2329b60106263c63bb567159d676bb99678115e02cc56acb1ab` on both hosts |
| server record | `847698cedfea0b93e680901c51e8a615c58299846ce5a2465884c91b48929867`; `server_end.json` `server_record_sha256` equals it |
| server end | `50d81220d20200f4233d4f8196316ae91d0546f30351acc896aa83a84660c95b`; `server_rc: 0`, `stop_signal: 15` |
| seal / span | seal receipt `g5-p11-20261128T014000Z-lease.seal-server-1.log` sha256 `2a76ea7a8287fe9f0bf034e940e12e7019b3e8a46446204ff8f11f86aadcc1c3`; `span_seconds: 112.0`; `seal_mode: procedural`; `files.server.tar` `cd00af99670694be45854e64c1f190c51f6238d57d5f8f04515976ea0f88dc17` |
| probe | `lease.probe1.json`: identity `n_ctx 32768`, `total_slots 1`, build `b1-620d222`, model `google_gemma-4-31B-it-Q4_K_M.gguf`; completion `0.1956379 s`; health median `30.68 ms`, p95 `31.41 ms`, n=20 |

On TASL-2 the `server-span` registration is also present at
`runs/g5-p11-20261128T014000Z-lease/_server_spans/server-1.json`, sha256
`2a76ea7a8287fe9f0bf034e940e12e7019b3e8a46446204ff8f11f86aadcc1c3` — byte-identical to the
committed seal receipt. It binds `server-1`, the same `server_record_sha256` and the 112.0 s span.
The `server-span` command therefore exercised and accepted the receipt. The sealed tree on TASL-7
contains `SEAL_RECEIPT.json` and `server.tar`; the tar hash matches the receipt. The probe's
`p11-probe` returned normally; a failed link would have raised STOP 12.

### 5. D — no sealed/label/test value, no changes, server stopped, leases free — PASS

- **No paper data.** The kit is synthetic: `parent.py` calls the isolated `worker.py`, whose
  `train.checksum()` performs a four-integer CUDA arithmetic and returns an integer checksum; the
  parent divides it by 4096. The two node names only select the published timing/host records. The
  `result_channel.txt` `test_accuracy` line is that synthetic fixture value, not a dataset or
  sealed-partition value. `sealed/` on TASL-2 is empty; `sealed-proposer/` holds only the sealed
  server; no label or evaluation file was read. The record is `ENGINEERING_ONLY` throughout.
- **No code/tolerance/note/seed/request change.** Both host checkouts are at `b9e195ac` with empty
  `git status --porcelain`; both harness checkouts are at `cbf7a003` with empty status. The spec
  hash is identical on both hosts and in the record; the ledger shows `seeds: {train: 5101,
  split: 5101}`, the declared measured run time and timeout factor, and zero proposals, zero
  manager calls and zero valid/kept rows. No proposal request was made. The record's "no code,
  tolerance, note, seed or request was changed" is consistent with the captures.
- **Server stopped.** The primary `server-1` ended with `server_rc: 0`, `stop_signal: 15`;
  `server_end.json` and the seal receipt bind it. No `llama-server` process remains; the recorded
  wrapper pid `2553875` is gone. The separate `-closeserver` server (pid `2554860`) was killed
  without a normal end record by design, so `seal-server` refused; it is also gone.
- **Leases free.** Current `nvidia-smi` on both hosts shows 0 % utilisation (353 MiB / 44 MiB
  residual display memory); `fuser` reports no holder of `~/r1_locks/gpu0.lock`; `lease_after.txt`
  on both hosts says `gpu0-free`. The TASL-2 CPU locks are also unheld.

## Findings — both resolved at `ba02dc21`

### MINOR-1 (was non-blocking) — the `close-server` quote is not verbatim — RESOLVED

In the first pass the record's second code block ended the refusal with `…/server-1` followed by
`on their command line`. The captured line
(`tasl7/g5-p11-20261128T014000Z-closeserver.close-server.log`) ends at `…/server-1`; the suffix
belongs to `close_attempt` (`g5_job.py:2074`), not `close_server` (`g5_seal.py:694`).

**Resolution at `ba02dc21`:** the code block now ends at `…/server-1`, and a parenthetical states
that the `close-attempt` message adds `on their command line` while `close-server` does not. The
quote and the capture now agree verbatim; the listed PID and the self-refusal conclusion are
unchanged.

### MINOR-2 (was non-blocking) — the `server-span` registration was not in the committed set — RESOLVED

In the first pass the record said the receipt was copied to TASL-2 and `server-span` accepted it,
and its file list said the set holds "server record/end/seal/span". The committed set held the
seal receipt/log (the same bytes that were registered) but not
`runs/g5-p11-20261128T014000Z-lease/_server_spans/server-1.json` or the `server-span` command
output. I verified the registration directly on TASL-2 (sha256 `2a76ea7a…`, same bytes as the seal
log; span 112.0 s), so the claim was true but not self-contained.

**Resolution at `ba02dc21`:** `tasl2/server-span-registration.json` is committed, hashes to
`2a76ea7a8287fe9f0bf034e940e12e7019b3e8a46446204ff8f11f86aadcc1c3`, and is byte-identical to
the host registration re-read from TASL-2. The record's seal/span paragraph names the file, and
the regenerated `SHA256SUMS` binds it (50/50 OK).

No new findings. The re-check touches exactly the two requested items — the close-server quote and
the server-span registration — plus the mechanically regenerated `SHA256SUMS`.

### Notes, not defects

- `closed.log` contains two refusals, `[1021816]` and `[1022275]`; the record quotes only the
  second. Both are the same self-match; the first does not change the finding.
- The probe JSON has no literal `PASS` field; its `identity`, `completion_seconds` and `health`
  are the successful probe result, and a failed probe would have raised STOP 12.
- The synthetic `test_accuracy` line is parsed by the harness (the node declares
  `test_scored: true`), but it is fixture arithmetic, not a paper label or sealed partition.

## Scope

The STOP correctly blocks the later matrix items: with a node-class STOP on each node,
`t1_tasl_node.sh` refuses further jobs, so C2, C4, C5, C14 and the wave-1/wave-2 campaign and
audit commands are not covered and no PASS is claimed for them. C9 and the `close-server` branch
of C15 are blocked by the self-scan defect; `seal-server` and `server-span` were exercised. This
record is a valid engineering STOP, not a host failure or an overclaim. The next step is the
local kit/harness fix named in the record (step line into the run log or parser reading
`result_text` for steps; self-exclusion in `processes_mentioning` for the two close commands),
then a fresh commit and fresh IDs.
