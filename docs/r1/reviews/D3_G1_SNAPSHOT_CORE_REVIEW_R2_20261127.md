# D.3 G1 charged-run snapshot core — second independent tier-E review

**Reviewer:** fresh, independent tier-E reviewer; I did not write this unit. Reviewed branch
`compute-d3-g1-snapshot-20261127` @ `f1b1ad20c2fcd309aea529b9e0c945d843229d94` (new commit on
`51cf07f7`; no force push), merge base `6684e840`. This record is on the same review branch
`compute-d3-g1-core-review-20261127`, as a new commit on top of the first review; the reviewed branch is not
merged. No campaign, audit, label, evaluation, GPU or evidence run was made. I read no test/evaluation
partition and no sealed label.

**Reviewed hashes (match the author's message):**

| File | sha256 |
|---|---|
| `docs/r1/reports/d3_g1_20261127/D3_G1_UNIT_20261127.md` | `e6d69524206d347fe929f671fdac7aebf27f650cb672813982114b6c722e3d46` |
| `r1/c3/d3/snapshots.py` | `8fffeca715a96bb2daf414d5f209322ead30761a2dc3f08ff9827e41381d54fd` |
| `r1/c3/d3/campaign_chunk.py` | `474d385c36fcfb6f80ad68440bfc1cc0327a1e1a2381a5fededad9487839be10` |

Verdict: CHANGES REQUIRED

The four coordinator conditions now pass, and B1, B2, B3, M1 and M3 are fixed. One MAJOR residual remains in
B4: `run_chunk` still does not require the manifest's model-source sha, so a manifest without
`campaign_model_source_sha256` (or with the design's `campaign_model_source` object) runs with the source check
skipped. B5 is substantially fixed but still omits several fields revision 6b names. The core snapshot code is
accepted; the chunk shell needs the fail-closed source check before merge.

## 1. Per-finding resolution

| Finding (first review) | Status | Evidence at `f1b1ad20` |
|---|---|---|
| **B1** parity at E0/E1/E2 | **FIXED** | `snapshots.py:327-335`: `observe_budget` now calls `check_parity` whenever `worker_runs` is observed, including `hook E0/E1/E2`; `snapshots.py:362-370` still raises `SnapshotParityStop`. Probe: `observe_budget(fake(worker_runs=7), where="hook E1")` with count 0 raised `SnapshotParityStop`. `campaign_chunk.py:206-207` keeps the end-of-campaign check. |
| **B2** E1 state and no-extra-call assertion | **FIXED** | `snapshots.py:299-325`: only E0/E1 update the capture; E2 refuses to replace `_trial` and raises if no E1 state exists. `snapshots.py:345-361`: `note_run` expects `controller_calls_at_e1 + 1` for a main run and `+2` for a verify run and raises `SnapshotStop` otherwise. Probe: trial 2 E1 `n=4`; `w5` verify snapshot has `n=4`, `pending_action=verify`. New test `test_verify_snapshots_keep_the_e1_controller_state` passes. |
| **B3** deterministic controller projection | **FIXED** | `snapshots.py:78-102`: `_jsonable` no longer returns `repr`; an unsupported object raises `SnapshotStop`, and a failing `to_dict()` also raises. Probe: two equal controllers with `log=[Weird()]` raise `SnapshotStop` instead of hashing. |
| **B4** hardware refusals wired and fail-closed | **PARTIALLY FIXED** | `campaign_chunk.py:174-189`: `run_chunk` requires `observed` and calls `check_hardware` before `out.mkdir`. `check_hardware` (`:127-159`) refuses a missing campaign/proposer model, missing observed model/proposer, a non-`pass` memory check, a non-`True` lease, and an `instance_model` mismatch; all seven probes pass. **Residual N1:** the manifest's source check remains optional (`campaign_chunk.py:186-188`). A manifest without `campaign_model_source_sha256` is accepted and the factory runs; the design's `campaign_model_source` object is not checked either. |
| **B5** chunk layout | **PARTIALLY FIXED** | `campaign_chunk.py:214-240`: each campaign now writes `ledger.jsonl`, `runs.jsonl`, `summary.json`, `campaign_id` and `record_name`; `campaign.json` and the per-campaign summary carry them. `chunk.json` (`:245-270`) has hardware/proposer/request/scope/environment fields and the test checks them. **Residual N2:** `campaign_model`, `host_class`, `lease_path`, `chunk_start_utc` and `chunk_end_utc` are absent from `chunk.json`; `driver`, `memory_total`, `memory_free` use different names from revision 6b; `status` is always `"complete"` (N3). |
| **M1** `final.json` true alias at w=20 | **FIXED** | `snapshots.py:437-450` copies the written `w20.json` payload and adds `final/ended/ended_on/run_kind/alias_of/alias_sha256`. Probe: controller state, incumbent and `alias_sha256` equal `w20`; test asserts the state and incumbent. |
| **M2** four-seeded-run test | **STILL NOT DIRECTLY TESTED** | The unit adds no test for verify-at-trial-1; the existing test still places verify at trial 2 (w5 is the third seeded run). Independent probe with verify at trial 1 and `W=5` produced `w5.json` with `run_kind=verify`, `worker_runs=5`, so the behaviour works; this is a test-coverage note, not a code defect. |
| **M3** ignored `llm_calls` in `note_decision` | **FIXED** | `note_decision(epoch, action)` no longer takes `llm_calls`; `RecordingController.decide` passes only epoch/action (`snapshots.py:339-343`, `:503-506`). The module docstring now says `llm_calls` comes from the observed budget. |
| **M4** harness pin in the unit record | **PASS** | The unit record still names `a3fedbbd`; the review command uses a clean worktree at that commit. The shared default checkout is not the pin, so the command must keep `AR_HARNESS_ROOT` explicit (environment note, not a code finding). |

## 2. The four coordinator conditions

| # | Result | Check |
|---|---|---|
| 1 | **PASS** | Hook parity is checked at E0/E1/E2 (`snapshots.py:327-335`) and at the end (`campaign_chunk.py:206-207`); a mismatch raises `SnapshotParityStop` at the hook (probe). |
| 2 | **PASS** | One count per worker call (`CountingWorker`, `snapshots.py:460-491`); skips charge no run (test); seeded verify runs are counted singly; no retry/block-charge path. |
| 3 | **PASS** | E1 state is authoritative (`snapshots.py:305-325`); `note_run` asserts `+1` main / `+2` verify and fails on an extra call (`:345-361`); verify snapshots carry the E1 hash with `pending_action=verify` (probe and new test). |
| 4 | **PASS** | The projection is documented (`snapshots.py:120-147`), deterministic for known controller fields, and unsupported objects raise `SnapshotStop` (`:78-102`); no `repr`/object-id fallback remains. A controller without `snapshot_state()` is either projected from known fields or refused. |

## 3. New / remaining findings

### N1 (MAJOR) — the manifest's model-source check is still fail-open

`run_chunk` checks the source only when the key is present:

```python
if str(manifest.get("campaign_model_source_sha256", "")) and \
        str(manifest["campaign_model_source_sha256"]) != sha256_json(dict(spec.campaign_model_source)):
    raise ChunkStop(...)
```

(`r1/c3/d3/campaign_chunk.py:186-188`). A manifest without `campaign_model_source_sha256` passes this block. The
independent probe passed a manifest with only `campaign_model` and `proposer_model`; `run_chunk` created the
output directory and reached the factory. Revision 6b says the manifest carries the campaign model source sha
and the chunk compares the observed card with that manifest; the source binding is the only check that the
manifest's `campaign_model`/`proposer_model` are the reviewed ones. A design-conforming manifest that uses a
`campaign_model_source` object rather than the `_sha256` key is also not checked. Make the key required (refuse
when absent), or accept both documented forms and compare the sha explicitly. The test
`test_manifest_source_mismatch_is_refused` covers a wrong value, not a missing one.

### N2 (MINOR) — several revision-6b fields are absent or renamed in `chunk.json`

A probe of the written chunk record shows `campaign_model`, `host_class`, `lease_path`, `chunk_start_utc` and
`chunk_end_utc` absent; the code writes `driver`, `memory_total`, `memory_free` instead of revision 6b's
`driver_version`, `memory_total_mib`, `memory_free_mib_at_start`, and `required_memory_mib` is absent. The
hardware facts are partly present under `hardware`/`hardware_claim`, but the named keys in revision 6b are not.
This is schema completeness, not a snapshot-contract defect; it should be fixed or explicitly assigned to the
launcher unit.

### N3 (MINOR) — `chunk.json.status` is always `"complete"`

`campaign_chunk.py:263` writes `"status": "complete"` unconditionally, even when a factory returns
`ended_on="stop"` or `"error"`; `run_chunk` also continues to the next instance. Revision 6b/D5b §2.3 says a STOP
stops new submissions and writes the manifest with reason. This may be intended for the later full-runner unit,
but the current record would call a stopped chunk complete.

### N4 (MINOR) — `run_chunk` does not assert `campaign_id` equals the instance id

`_validate_kwargs` (`campaign_chunk.py:165-172`) requires `campaign_id` but does not compare it with
`spec.instance_id(seed)`. The design fixes the harness `campaign_id` to the instance id; a factory can pass a
different id and the ledger/summary would disagree with `campaign.json`. Add the assertion in the chunk shell.

### N5 (MINOR) — `instance_model` is checked only when present

`check_hardware` (`campaign_chunk.py:139-141`) skips the instance claim when the manifest has no
`instance_model`; revision 6b says the per-instance manifest carries it. Treating absence as
`campaign_model` is a safe default, but it is not the fail-closed reading.

## 4. Tests and environment

Command at the tip `f1b1ad20`, with `AR_HARNESS_ROOT` at a clean worktree of the pin
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`:

```
V=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv
AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/ar_pin \
  "$V/bin/python" -m pytest -q -p no:cacheprovider \
  r1/tests/test_d3_g1_snapshots.py r1/tests/test_d3_g1_chunk.py
```

- **19 passed** (13 snapshot tests, 6 chunk tests), 1.34 s. The author's claim is confirmed.
- Full `r1/tests`, same venv and pin, one run at a time, fresh `TMPDIR`:

| Tree | Commit | Result |
|---|---|---|
| base | `6684e840` | **100 failed, 4328 passed, 161 skipped, 3 errors** |
| tip | `f1b1ad20` | **100 failed, 4347 passed, 161 skipped, 3 errors** |

The sorted FAILED/ERROR id lists are identical: 103 ids each, sha256
`e6f2073eb1adeafb5438af19d88bb9e8ad97666a009d029961b6c5ccbad70880`. The only difference is **+19 passed**, the
new tests. **Zero new failing ids; none removed.**

The provided `d3g1_tipfix.log` was not used for the id comparison: it reports 46 failed / 4401 passed in a
different dependency environment, so its raw counts are not comparable with the base run. The two extra failing
ids it shows (`test_b1_real_worker_determinism.py::test_b1_real_worker_run_is_seed_deterministic` and
`test_c3_audit.py::test_real_worker_run_is_seed_deterministic`) were independently run at `6684e840` and at
`f1b1ad20` with this venv/pin and fail on both; they are not attributable to this unit. The same-environment
base/tip comparison above is the authoritative evidence.

Environment: Python 3.12.8, pytest 9.2.0, NumPy 2.5.5, torch 2.15.0; harness `a3fedbbd` clean; no GPU, campaign,
audit or label read.

Independent probes (not committed; outside the repository tree):
1. Hook parity: `SnapshotParityStop` at `hook E1` for `worker_runs=7` with count 0.
2. E1 state: stateful controller at trial 2; `w5` verify snapshot `n=4`, `pending_action=verify`.
3. Strict projection: `log=[Weird()]` raises `SnapshotStop`.
4. Hardware: all seven missing/mismatch cases refuse; `observed=None` refuses before creating output; the
   manifest-without-source case passes (N1).
5. `final.json`: controller state, incumbent and `alias_sha256` equal `w20`.
6. Verify at trial 1: `W=5` produces `w5` with `run_kind=verify` and `worker_runs=5`.

## 5. Scope

**In scope:** the five-file revised diff; the four coordinator conditions; the first review's B1–B5 and M1–M4;
the new tests; the full-suite comparison; the chunk record and refusal wiring.

**Out of scope (not accepted or rejected here):** the full G1 adapter (real node specs, `gemma4_31b`, per-arm
factories, A0/A0R/A1/A2/A3/A5/A6, real record names and ledger-root separation); G6 and the Y/Y(w) audit; FIXR3
and EGATE/design revision 6c; the verify-seed rule and P10/P14; the A1/A2/LADDER constants and signed
pre-declaration; the two launchers; `d3_analysis.py` and the `r1_d3_outcome/v2` builder; the screening
measurement; any evidence, test-label or evaluation read.

## 6. Review-file hash

The final line below is excluded from its own hash. To reproduce:

```
sed '/^Review record sha256:/d' docs/r1/reviews/D3_G1_SNAPSHOT_CORE_REVIEW_R2_20261127.md | sha256sum
```

Review record sha256: 96ee13afc5f1dbad02137615294222d4340ea141af9c83470885c7a9f8855610
