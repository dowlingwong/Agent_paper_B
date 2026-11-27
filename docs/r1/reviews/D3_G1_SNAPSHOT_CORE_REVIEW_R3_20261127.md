# D.3 G1 charged-run snapshot core — third independent tier-E review

**Reviewer:** fresh, independent tier-E reviewer; I did not write this unit. Reviewed branch
`compute-d3-g1-snapshot-20261127` @ `44075323d56efc76573590aea4ec7b28567b3490` (new commit on
`f1b1ad20`; no force push), merge base `6684e840`. This record is on the same review branch
`compute-d3-g1-core-review-20261127`, as a new commit on top of the first and second reviews; the reviewed
branch is not merged. No campaign, audit, label, evaluation, GPU or evidence run was made. I read no
test/evaluation partition and no sealed label.

**Reviewed hashes:**

| File | sha256 |
|---|---|
| `docs/r1/reports/d3_g1_20261127/D3_G1_UNIT_20261127.md` | `e6d69524206d347fe929f671fdac7aebf27f650cb672813982114b6c722e3d46` |
| `r1/c3/d3/snapshots.py` | `8fffeca715a96bb2daf414d5f209322ead30761a2dc3f08ff9827e41381d54fd` |
| `r1/c3/d3/campaign_chunk.py` | `653804b8d3d03119829488874a9c932cb214639fa54f58afbf0656d35307e11f` |

Verdict: ACCEPTED

N1 is resolved and none of the remaining items is BLOCKING or MAJOR. The snapshot core and the chunk shell now
satisfy the four coordinator conditions and the revision-6b record/refusal contract at the level this unit
claims. The remaining notes are documentation/schema details and a future full-runner STOP behaviour; they do
not change what this unit records or how a snapshot is read.

## 1. Per-finding resolution

| Finding | Status | Evidence at `44075323` |
|---|---|---|
| **N1 (MAJOR)** manifest model-source check optional | **FIXED** | `campaign_chunk.py:186-189`: `campaign_model_source_sha256` is required; a missing key raises `ChunkStop` before `out.mkdir`; the comparison is unconditional. New test `test_manifest_source_key_is_required` passes; independent probe refuses before creating output. |
| **N2** missing/renamed chunk fields | **FIXED** | `campaign_chunk.py:253-272` writes `campaign_model`, `host_class`, `lease_path`, `chunk_start_utc`, `chunk_end_utc`, `driver_version`, `memory_total_mib`, `memory_free_mib_at_start` (the old names are kept too); probe confirms all eight keys. |
| **N3** status always complete | **FIXED** | `campaign_chunk.py:272`: `status` is `"stopped"` if any campaign `ended_on` is `stop` or `error`, else `"complete"`. Probe with a stop factory writes `status=stopped`. |
| **N4** campaign id not checked | **FIXED** | `campaign_chunk.py:201-202`: `run_chunk` refuses when `kwargs["campaign_id"] != spec.instance_id(seed)`. Probe raises `ChunkStop`. |
| **N5** `instance_model` optional | **FIXED** | `campaign_chunk.py:139-141`: defaults to `campaign_model` and then requires equality; a mismatch raises. |
| **B1** parity at E0/E1/E2 | **FIXED** (carried) | `snapshots.py:327-335` checks every observed `worker_runs`; `:362-370` raises `SnapshotParityStop`; probe at `hook E1` passes. End check `campaign_chunk.py:209-210`. |
| **B2** E1 state and no-extra-call assertion | **FIXED** (carried) | `snapshots.py:299-325` keeps E1 and refuses to replace it at E2; `:345-361` expects +1 main / +2 verify; probe `w5` verify keeps E1 `n=4`, `pending_action=verify`. |
| **B3** deterministic projection | **FIXED** (carried) | `snapshots.py:78-102` raises `SnapshotStop` for unsupported objects; no `repr` fallback. |
| **B4** hardware refusals fail-closed | **FIXED** | `run_chunk` requires `observed`, calls `check_hardware` before creating output, and the N1 source key is now mandatory. All missing/mismatch probes refuse. |
| **B5** chunk layout | **FIXED** | Per-campaign `ledger.jsonl`, `runs.jsonl`, `summary.json`, `campaign_id`, `record_name`; chunk fields as N2. |
| **M1** `final.json` alias | **FIXED** (carried) | `snapshots.py:437-450` copies `w20.json` and adds final fields; probe confirms equal controller state/incumbent. |
| **M2** four-seeded-run test | **note** | No direct unit test still; independent probe with verify at trial 1, `W=5`, produces `w5` `run_kind=verify`, `worker_runs=5`. |
| **M3** ignored `llm_calls` | **FIXED** (carried) | `note_decision(epoch, action)` only. |
| **M4** harness pin | **PASS** | Unit record names `a3fedbbd`; the review command uses a clean worktree at that pin. |

## 2. Four coordinator conditions

| # | Result | Check |
|---|---|---|
| 1 | **PASS** | Parity checked at E0/E1/E2 (`snapshots.py:327-335`) and at the end (`campaign_chunk.py:209-210`); mismatch fails closed. |
| 2 | **PASS** | One count per worker call (`CountingWorker`, `snapshots.py:460-491`); skips charge no run; seeded verify runs counted singly; no block-charge path. |
| 3 | **PASS** | E1 state is authoritative (`snapshots.py:299-325`); `note_run` asserts +1 main / +2 verify (`:345-361`); verify snapshots carry E1 state and `pending_action=verify`. |
| 4 | **PASS** | Projection is documented and deterministic (`snapshots.py:120-147`); unsupported objects raise `SnapshotStop` (`:78-102`); a controller without `snapshot_state()` is projected from known fields or refused. |

## 3. Remaining notes (MINOR; none blocks)

1. **Unit record test count is stale.** The unit record still says 19 tests (`13 + 6`); this commit adds a seventh
   chunk test, for **20**. The unit-record hash is unchanged (`e6d69524…`). Update the count in the next
   documentation touch; it does not affect the code or the review's evidence.
2. **The `campaign_id` assertion is after `out.mkdir`.** `run_chunk` refuses a wrong `campaign_id`, but by then
   the empty chunk directory exists. A refused chunk leaves a scaffold directory; the caller should remove it or
   the assertion should run before `out.mkdir` (the design says a pre-launch refusal has no output directory).
3. **`host_class`, `lease_path` and `chunk_start_utc` may be `null`.** They are copied from `observed`
   (`campaign_chunk.py:255-256`); `check_hardware` does not require them. Revision 6b names them in every chunk;
   a launcher that omits them writes nulls rather than refusing. Record-only, not a scientific STOP.
4. **A stopped chunk still runs the remaining instances.** `status` correctly becomes `"stopped"`, but
   `run_chunk` continues the loop after a `stop`/`error` campaign. D5b §2.3 says a STOP stops new submissions;
   this is future full-runner behaviour, outside this unit's accepted scope.

## 4. Tests and environment

Command at the tip `44075323`, with `AR_HARNESS_ROOT` at a clean worktree of the pin
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`:

```
V=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/ar_pin \
  "$V/bin/python" -m pytest -q -p no:cacheprovider \
  r1/tests/test_d3_g1_snapshots.py r1/tests/test_d3_g1_chunk.py
```

- **20 passed** (13 snapshot tests, 7 chunk tests), 1.10 s.
- Full `r1/tests`, same venv and pin, one run at a time, fresh `TMPDIR`:

| Tree | Commit | Result |
|---|---|---|
| base | `6684e840` | **100 failed, 4328 passed, 161 skipped, 3 errors** |
| tip | `44075323` | **100 failed, 4348 passed, 161 skipped, 3 errors**, 765.29 s |

The sorted FAILED/ERROR id lists are identical: 103 ids each, sha256
`e6f2073eb1adeafb5438af19d88bb9e8ad97666a009d029961b6c5ccbad70880`. The only difference is **+20 passed**, the
new unit tests. **Zero new failing ids; none removed.** The earlier environment-sensitive `d3g1_tipfix.log`
(46 failed / 4401 passed) is not used for the id comparison; the same-environment base/tip run above is the
authoritative evidence.

Environment: Python 3.12.8, pytest 9.2.0, NumPy 2.5.5, torch 2.15.0; harness `a3fedbbd` clean; no GPU, campaign,
audit or label read.

Independent probes (not committed; outside the repository tree):
1. Missing source key: `ChunkStop` before output creation.
2. `check_hardware`: missing model/proposer/memory/lease, `observed=None`, and `instance_model` mismatch all
   refuse.
3. `chunk.json`: all eight N2 keys present; `status=stopped` for a stop factory.
4. Wrong `campaign_id`: `ChunkStop`.
5. `final.json`: controller state, incumbent and `alias_sha256` equal `w20`.
6. Verify at trial 1: `W=5` produces `w5` with `run_kind=verify`, `worker_runs=5`.

## 5. Scope

**In scope:** the revised diff; N1–N5 and the carried B1–B5/M1–M4; the four coordinator conditions; the 20 unit
tests; the full-suite comparison; the chunk record and refusal wiring.

**Out of scope (not accepted or rejected here):** the full G1 adapter (real node specs, `gemma4_31b`, per-arm
factories, A0/A0R/A1/A2/A3/A5/A6, real record names and ledger-root separation); G6 and the Y/Y(w) audit; FIXR3
and EGATE/design revision 6c; the verify-seed rule and P10/P14; the A1/A2/LADDER constants and signed
pre-declaration; the two launchers; `d3_analysis.py` and the `r1_d3_outcome/v2` builder; the screening
measurement; any evidence, test-label or evaluation read.

## 6. Review-file hash

The final line below is excluded from its own hash. To reproduce:

```
sed '/^Review record sha256:/d' docs/r1/reviews/D3_G1_SNAPSHOT_CORE_REVIEW_R3_20261127.md | sha256sum
```

Review record sha256: 63e39469a241a5aa46379ea1014ab3d3054ecfe5fd41faa17cde08ce1dfabbc0
