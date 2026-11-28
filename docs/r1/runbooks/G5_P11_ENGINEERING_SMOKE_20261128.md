# G.5 P11 engineering smoke on TASL-2 and TASL-7

This procedure covers the engineering handoff in local/20261128-02 under R1-G5-P11.
Run from the independently accepted task commit on both hosts. The recipe admits only the two
synthetic node kits. Their names select the published IMDb and Breakout timing and host records.
The isolated worker computes a deterministic integer checksum on CUDA. The real campaign
engine receives scripted edits, and the real audit engine re-materializes and runs them.
The fixed engine input schema uses its existing EVIDENCE wire value. The paper-side run ID,
job records, plans, seals and release negative control identify engineering outputs.
The G.1b pre-check reads the reviewed copies from published main. The worker uses the
published 4090 runtime checks, GPU and CPU-set leases, and the pinned harness and torch environment.
The Breakout-labelled workload uses the synthetic torch kit and the declared Breakout deadline constants.

## Set up the run

Check the Compute ledger for active TASL work and confirm access to the shared leases,
delegated cgroups and the pinned G.5 checkout. Use a different run ID for every scenario
below. The same ID and spec bytes are used on both hosts. Start with the primary scenario
and retain any refusal, exit code, attempt or claim. Record actual paths and IDs.

Set these variables in the task checkout on both hosts. Supply one common UTC stamp and
use a fresh one for each scenario. Capture the spec SHA-256 and clean exact task commit from `p11-init` on both hosts.

```sh
unset G5_TASL_ENABLE_REAL
git fetch origin main
T1=sweep2/t1_tasl
g5() { python3 "$T1/g5_tasl.py" "$@"; }
BASE="$HOME/r1_engineering/g5-p11"
ID=g5-p11-20261128T120000Z-lease
SPEC="$BASE/$ID.json"
RUN="$BASE/runs/$ID"
IN="$BASE/incoming/$ID"
SERVER="$BASE/proposer/$ID"
g5 p11-init "$ID"
g5 validate "$SPEC" --launch --engineering
mkdir -p "$IN"
```

The `-lease` suffix enables the TASL-7 audit rendezvous. Use `-determinism` for the
repeat audit, `-restart` for the supervised restart, `-infra` for the injected audit
runner failure and `-tar` for a deliberately failed tar. Capture both the command status
and the underlying wrapper log for expected refusals. The same spec refuses validation
through the evidence mode.

Run the engineering server on TASL-7 in a supervised foreground terminal. Record its
wrapper PID and server PID from the new server record. On TASL-2 install an exact copy
of `server-1/server_record.json` under `$IN/server-1.json`, without overwrite.

```sh
# TASL-7
g5 serve "$SPEC" --engineering
# TASL-2, after server readiness and the copy
g5 p11-probe "$SPEC"
bash "$T1/t1_tasl_node.sh" g5 "$SPEC" mlab_imdb - campaigns-wave1 "$IN/server-1.json" --engineering
bash "$T1/t1_tasl_node.sh" g5 "$SPEC" mlgym_breakout_minatar - campaigns-wave1 "$IN/server-1.json" --engineering
```

## C2, C4, C5 and C14

On TASL-2 run the first audit chunk for both nodes. Use the `-determinism` scenario
with the same setup for a repeat of the same `(unit, seed)` pairs through the actual
engine. A matching receipt inside the synthetic archive gives the repeated pair
count. The audit archive contains the checked unit hashes, rematerialization count
and per-run isolation receipts. Keep the wrapper log showing the delegated scope.
Campaign and audit archives contain a synthetic binary. Inspect only named JSON and
JSONL members for the checks and capture the binary member's name from the tar listing.

```sh
for node in mlab_imdb mlgym_breakout_minatar; do
  bash "$T1/t1_tasl_node.sh" g5 "$SPEC" "$node" - audits-wave1 - --engineering
  cat "$RUN/$node/campaigns-wave1/attempt-1/diagnostics.json"
  cat "$RUN/$node/audits-wave1/chunk-0/attempt-1/diagnostics.json"
  tar -tf "$RUN/$node/audits-wave1/chunk-0/attempt-1/out.tar"
done
```

For C5 compare the reported deadlines with `started + 1800 + ceil(n * run_seconds * 1.5 * 1.25)`,
using the two original census times and each chunk's actual run count. K is 10.
The engineering planner limits transfer chunks to 200 rows. The production chunking
rule and the per-chunk deadline formula are unchanged. After registering any
TASL-7 work, finish the remaining TASL-2 chunks for each node. The final chunk has
the E5 diagnostics over the label-seed block. Run `g5 wave-checks "$SPEC" --node "$node"
--wave 1 --engineering` and record its result. Repeat the campaign and audit commands
with `wave2` to finish either node that has no recorded node STOP.
For C14 rerun the IMDb campaign and its first audit under `-infra`. The built-in test
runner injects a pre-start RunnerError for one unit at seed 7001, through all retries.
Verify the real audit engine's infrastructure row and the job's STOP 7. Retain it
as a separate engineering attempt.

## C7, C10, C11 and C16

Measure the short proposer span from TASL-2 with `g5 p11-probe "$SPEC"` during
the span and after restart. For a controlled restart use `-restart`. Start one
IMDb campaign. When `$RUN/mlab_imdb/campaigns-wave1/attempt-1/out/campaign/restart-ready`
appears, stop the engineering server by signaling its recorded wrapper. With the
server down, create `restart-continue` in that campaign directory. Keep it down
until the wrapper records the infrastructure STOP 12. Restart the server, verify
its identity with `p11-probe`, and copy the new record as `$IN/server-2.json`.
For the short-span record preserve UTC probes, both server identities and the
job record that classified the interruption.

For C11 and C16 use `-lease` and IMDb. The first local audit makes the multi-chunk
plan. Claim its non-final chunk 1 on TASL-2. Transfer the following three files from
TASL-2 to TASL-7, preserving their paths relative to `$RUN` and their hashes.

```sh
# TASL-2
git fetch origin main
g5 claim-chunk "$SPEC" --node mlab_imdb --wave 1 --chunk 1 --engineering
sha256sum "$RUN/_remote/claims/mlab_imdb/audits-wave1/chunk-1.json" \
          "$RUN/mlab_imdb/audits-wave1/plan_index.json" "$RUN/mlab_imdb/audits-wave1/plan.tar"
# TASL-7
git fetch origin main
bash "$T1/t1_tasl_node.sh" g5t7 "$SPEC" mlab_imdb - audits-wave1 1 --engineering
```

First call the last command while the engineering proposer server is up. Verify
the GPU lease refusal and preserve it. Stop and seal that server. Start the command
again with the server down. When
`$RUN/mlab_imdb/audits-wave1/chunk-1/attempt-1/out/lease-ready` appears, run
`g5 serve "$SPEC" --engineering` in a separate TASL-7 terminal and verify the
same lease refusal. Create `lease-continue` beside `lease-ready` to finish the
audit. Check the live GPU model, driver, paper commit and both environment freezes in the resulting job record.
If a pre-engine attempt allocated a directory, use its actual attempt number.

Copy the TASL-7 completed attempt, wrapper log and `$RUN/_access_log.jsonl` into
`$IN` on TASL-2. Use the exact wrapper log basename from the attempt record.
Register and seal the attempt on TASL-2.

```sh
NODE_LOG=$(python3 -c 'import json,sys; from pathlib import Path; print(Path(json.load(open(sys.argv[1]))["node_log"]).name)' "$IN/attempt-1/job_record.json")
g5 register-chunk "$SPEC" "$IN/attempt-1" --node mlab_imdb --wave 1 --chunk 1 \
  --access-log "$IN/_access_log.jsonl" --node-log "$IN/$NODE_LOG" --engineering
g5 finalize-remote "$SPEC" --access-log "$IN/_access_log.jsonl" --engineering
g5 seal-attempt "$SPEC" "$RUN/mlab_imdb/audits-wave1/chunk-1/attempt-1" --engineering
```

## C6, C9 and the pre-run checks of C15

Capture the meter before and after a synthetic closed attempt. Close it in a
fresh run with `p11-closed-fixture`. Record the increase in metered worker time,
the job's `gpu_seconds`, W, MEM, K and the signed reporting threshold.
Verify the per-job noise pre-check and its copy SHA-256 in the actual job record.
Verify free disk, each attempt receipt and the access log in the run seal.
Use `-tar` to exercise a real tar command failure. Its known fixture leaves the
attempt's `out/` tree for the seal. Verify that the seal records and hashes
`out_clear.tar`.

```sh
# TASL-2, separate closed-attempt scenario
g5 p11-meter "$SPEC"
g5 p11-closed-fixture "$SPEC"
sleep 5 # Make the synthetic interval visible at the meter’s 0.001 GPU-hour resolution.
ATTEMPT="$RUN/mlab_imdb/campaigns-wave1/attempt-1"
g5 close-attempt "$SPEC" "$ATTEMPT" --node mlab_imdb --job campaigns-wave1 \
  --reason "P11 synthetic interrupted attempt" --engineering
df -P "$BASE"
g5 seal-attempt "$SPEC" "$ATTEMPT" --engineering
g5 p11-meter "$SPEC"
# TASL-2, main scenario after all attempts are sealed and each node has ended
g5 seal-node "$SPEC" --node mlab_imdb --engineering
g5 seal-node "$SPEC" --node mlgym_breakout_minatar --engineering
g5 seal-run "$SPEC" --engineering
g5 p11-table-marker "$SPEC"
```

For C15 seal a normally stopped server using the first command below. To exercise
`close-server`, start an engineering server in its own terminal and record its
PID plus the wrapper PID. End the engineering child and wrapper without letting
the wrapper write the normal end record. Confirm both are gone and the lease is
free before closing. Preserve the process and lease checks. Copy the resulting
receipts to the engineering incoming tree on TASL-2, then register and meter
the spans.

```sh
# TASL-7
g5 seal-server "$SPEC" "$SERVER/server-1" --engineering
g5 close-server "$SPEC" "$SERVER/server-2" --reason "P11 engineering server interruption" --engineering
g5 seal-server "$SPEC" "$SERVER/server-2" --engineering
# TASL-2 after transfer
g5 server-span "$SPEC" "$IN/server-1-receipt.json" --engineering
g5 server-span "$SPEC" "$IN/server-2-receipt.json" --engineering
g5 p11-meter "$SPEC"
```

Use this negative control for release refusal. The command must exit nonzero
with the P11 engineering refusal before it attempts to open evidence. Retain
the earlier reviewed real REL-T1-G1B copy and bind its digest in the coverage
record. Real C15 assembly and release remain gated by the signed sequence.

```sh
python3 -m r1.c3.release --stage traindev --source g5 --table "$BASE/table/$ID" \
  --audit "$BASE/table/$ID" --out "$BASE/table/$ID/release"
```

The host record reports each C item, the actual code and spec SHA-256, review,
run and job IDs, prior record references and any remaining coverage gaps.
The coordinator determines whether the reviewed coverage satisfies P11.
