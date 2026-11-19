# Track P P.3a D2 — host adaptation (TASL-7/TASL-2) + attempt-1 artifact hash verification, 19 November 2026

**Status: implementation record for re-review, revision 3 — responds to the independent round-2 review
(`reviews/TRACKP_P3A_D2_CODE_REVIEW_R2_20261119.md`, sha `837d3490…`: 0 BLOCKING, 1 new MAJOR (MAJOR-2), 2 MINOR,
NOT ACCEPTED; the round-1 MAJOR-1 is independently verified FIXED). ENGINEERING_ONLY; AI-assisted.** No GPU job, no model, no experiment,
no TASL host and no evidence root was touched; no push, no merge, no deletion. This unit changes **only the host
contract**: the probes-only supervisor `r1/scripts/trackp_p3a_guarded.py`, the host snapshot/record helpers it
depends on (`R.host_driver_snapshot` / `R.driver_record` in `r1/c3/train/run.py`; the child's host-aware driver
record in `r1/scripts/trackp.py`) and its tests/records, as authorized by `R1-TRACKP-D2` in `docs/r1/PLAN.md`
(published `main` `de3de54f`). Basis: `reports/TRACKP_TASL7_BACKUP_20261117.md`
(TASL-7 recovered; attempt-1 artifacts hashed; archive + TASL-2 copy verified), `reports/TRACKP_TASL2_DELIVERY_20261117.md`
and `reports/TRACKP_TASL2_EQUIVALENCE_RESULT_20261117.md` (TASL-2 host-equivalence **PASSED**, `equivalent: true`),
and the 17 Nov STOP that D hard-codes TASL-7/driver `580.178.04`/attempt-1 boot `2c9bb104…`.

Revision 3 closes round-2 MAJOR-2 (the driver/boot path was TASL-7-only, so a real TASL-2 run STOPed in the
preflight) and the two round-2 minors (see §0.3). Revision 2 fixed the round-1 MAJOR defect and the four minors (see
§0.2): the attempt-1 **provenance** and the BLOCKING-1
lease-log snapshot now use the same host-aware lease-log discovery as the artifact verifier (TASL-7 live global log;
TASL-2 staged `_attempt1_gpu_lease_log.jsonl`), so a TASL-2 run passes preflight → provenance →
`assert_attempt1_pins` → snapshot instead of STOPing after the preflight. A real TASL-2 end-to-end test (live TASL-2
global log different, attempt-1 pin asserts **not** stubbed) now covers that path.

**Commits under review / to be recorded after review.**

| | |
|---|---|
| **Base** | `8662e35991659f7a661fb7ed6be4980791d302f3` (D; published base `de3de54f`; `b9ad6f8f` attempt-1 pin) |
| **C2** (code commit) | the single commit that introduces this report: `fix(r1): Track P D2 host adaptation (TASL-7/TASL-2) + attempt-1 artifact hash verification`. Touches `r1/scripts/trackp_p3a_guarded.py`, `r1/scripts/trackp.py`, `r1/c3/train/run.py`,
`r1/tests/test_trackp_p3a_probes_only.py`, this report, the code-units record and the unchanged-suite test stubs. **C2 cannot contain its own sha** (a commit sha covers the file that states it); its exact sha is reported after the commit exists. |
| **D2** (mechanical delivery-pin child) | direct child of C2, single parent; its only runner change is the single canonical `EXPECTED_PAPER_HEAD = "<C2>"` assignment, byte-for-byte otherwise identical to C2's runner blob. The D2 commit also adds `docs/r1/reports/TRACKP_P3A_D2_DELIVERY_20261119.md`, which records the C2 sha and the D2 runner-blob sha (docs outside `r1/` are allowed by the unchanged pin-child rule). **D2 cannot contain its own sha** (hash cycle); the D2 commit sha is supplied to the coordinator with the handoff for the ops delivery record. |

Author and committer: `Dowling Wong <wangdowling@gmail.com>`. `R1-TRACKP-UNITB` must name **D2** in place of D; one
host per table, named in the run report (this unit runs on no host). C2 alone is refused by C2's own script for the
same self-pin-cycle reason as C/D: its `EXPECTED_PAPER_HEAD` still names `5b7ad0cb` (the reviewed code commit D pins),
and D2 is the byte-exact pin child of C2.

## 0.2 Response to review round 1 (19 November 2026)

| Finding | Status | Where |
|---|---|---|
| **MAJOR-1** TASL-2 campaign STOPs at `assert_attempt1_pins`: `build_attempt1_provenance` (and the snapshot source) still hard-wired `<attempt1-root>/../gpu_lease_log.jsonl` (TASL-7's live log) instead of the host-discovered attempt-1 log, so the TASL-2 fallback was not delivered | **Fixed.** One discovery helper, `attempt1_lease_log_path` (TASL-7 `gpu_lease_log.jsonl`; TASL-2 `_attempt1_gpu_lease_log.jsonl` with a fail-closed global-log fallback), is used by `verify_attempt1_lease_log`, `build_attempt1_provenance` and (through the provenance record) `snapshot_attempt1_lease_log`. The campaign passes the preflight's verified `attempt1_artifacts` lease record (path + sha256 re-checked); the discovery branch fails closed on a missing/mismatched log. TASL-7 behaviour is unchanged (same single candidate/path). Real TASL-2 end-to-end test added. | §1.1, §1.2, §2, §3 |
| **MINOR-1** the four `final/manifest.json` (and saved-manifest) bytes were recorded but not pinned; absent identity fields were tolerated | **Fixed.** `EXPECTED_ATTEMPT1_MANIFEST_SHA256` / `EXPECTED_ATTEMPT1_SAVED_MANIFEST_SHA256` pin the eight recorded inventory hashes; the paper/harness/boot/driver identity fields are now **required**. Tests: pin mismatch, wrong schema/label/family, saved-manifest disagreement. | §1.2, §5 |
| **MINOR-2** symlink refusal was leaf-only | **Fixed (defence in depth).** Attempt-1 `EVIDENCE`, `EVIDENCE/<base>`, `final`, `saved` must be plain (non-symlink) directories; the root, journal, `backups` directory and run-global lease-log parent are also checked. Test: symlinked `final` directory. | §1.2 |
| **MINOR-3** no TASL-2 end-to-end campaign test; several artifact negatives missing | **Fixed.** A real TASL-2 e2e test drives the **real** `verify_probes_only_pins` → `build_attempt1_provenance` → `assert_attempt1_pins` → `snapshot_attempt1_lease_log` path (the exact `_PreflightStubs` list is in §3) with a different live TASL-2 global log; manifest schema/label/family, saved-manifest disagreement, unsafe path, unrecorded file and symlinked-directory negatives added. | §3 |
| **MINOR-4** basis reports live on `ops-tasl-20261116`; D2 branch-name wording was wrong; C2/D2 shas were not in a delivery record | **Addressed.** §5/§7 state the basis documents' branch; §7 states plainly that **detached HEAD is the only accepted form for D2**; the full C2/D2 shas and D2 runner blob sha are supplied to the coordinator for the ops delivery record / `R1-TRACKP-UNITB` amendment (a commit cannot contain its own sha; the unit-side record cannot carry them). | §5, §7 |

## 0.3 Response to review round 2 (19 November 2026)

| Finding | Status | Where |
|---|---|---|
| **MAJOR-2 (new)** TASL-2 fallback still not executable: `verify_probes_only_pins` and `run_unit` called the TASL-7-only `R.tasl7_driver_snapshot()` (580-only package assertions), and the unchanged child recorded `tasl7_driver` only on `tasl-7` while `run_unit` required it, so a real TASL-2 run STOPed in the preflight and could not complete | **Fixed.** A host-parameterized `R.host_driver_snapshot(expected_driver=None)` now backs both call sites: on TASL-7 it returns the unchanged `tasl7_driver_snapshot()` (580 package checks intact); on another reviewed host it reads the same `/proc` + `nvidia-smi` primitives, requires kernel/user agreement and the host's expected driver pin, and records the driver-branch package inventory best-effort (e.g. `nvidia-utils-535`). The attempt-2 child (`r1/scripts/trackp.py`, via `R.driver_record`) records the generic `host_driver` on TASL-2 for `--a3-short` probes only, and its `gpu_lease` events carry `host_driver`; TASL-7 still records `tasl7_driver` only. `run_unit` accepts either record for the manifest/lease boot-id checks. Real-snapshot tests (OS primitives faked, the blocking function **not** stubbed) cover the TASL-2 preflight, the `gpu_lease` record and a full `run_unit`; TASL-7 behaviour is asserted identical. | §1.1, §1.2, §2, §3 |
| **MINOR-1** the e2e/stub wording was inaccurate (`_PreflightStubs` also fakes checkout/environment identity checks) | **Fixed.** The e2e test docstring and §3 list exactly what `_PreflightStubs` fakes, and the host driver snapshot is no longer among the stubs. | §3 |
| **MINOR-2** the TASL-2 preflight tests stubbed `R.tasl7_driver_snapshot`, masking MAJOR-2 | **Fixed.** `_PreflightStubs` now drives the **real** `R.host_driver_snapshot`/`R.tasl7_driver_snapshot` through faked OS primitives (`/proc`, `uptime`, `nvidia-smi`, `dpkg-query`) for both TASL-7 and TASL-2 shapes; tests assert the real TASL-7-only function cannot return on TASL-2-shaped primitives. | §3 |

## 1. What changed (only the host contract)

### 1.1 Host profiles (`host_profile`, `normalized_hostname`)

Normalized hostname = lower-case first label (`TASL-7`/`tasl-7` → `tasl-7`). Two profiles are accepted, each with its
own driver pin, freeze pin, and attempt-1 lease-log discovery order:

| | TASL-7 (attempt-1 host; Unit B primary) | TASL-2 (host-equivalence PASSED 17 Nov) |
|---|---|---|
| normalized hostname | `tasl-7` | `tasl-2` |
| NVIDIA driver pin | `580.178.04` | `535.309.01` |
| freeze pin (committed) | `docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt` | `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` |
| attempt-1 lease log | `<attempt1-root>/../gpu_lease_log.jsonl` (the live global log at attempt-1's end) | `<attempt1-root>/../_attempt1_gpu_lease_log.jsonl` (the attempt-1 copy; TASL-2's live global log is a different log), fallback `<attempt1-root>/../gpu_lease_log.jsonl` |
| attempt-1 backup archive | `<attempt1-root>/../../backups/p3a_attempt1_final_saved_20261117T0015Z.tar.gz` | same |
| attempt-1 root | `--attempt1-root /home/dowling/r1_trackp/runs/p3a_operator_20261027` | same path (already staged from the archive) |
| driver/boot snapshot | unchanged `R.tasl7_driver_snapshot()` (kernel/user agreement + the 580 package assertions) | `R.host_driver_snapshot("535.309.01")`: same `/proc` + `nvidia-smi` primitives, kernel/user agreement, the host's expected driver pin, and branch package inventory best-effort (`nvidia-utils-535`, `libnvidia-compute-535`); no 580-only probe |
| child driver record (attempt-2 probes) | unchanged `tasl7_driver` (top level and per `gpu_lease` event) | generic `host_driver` (top level and per `gpu_lease` event); verified by `run_unit` |

The driver/boot snapshot is host-parameterized (MAJOR-2 fix, revision 3): `verify_probes_only_pins` and `run_unit`
call `R.host_driver_snapshot(...)`; on TASL-7 it returns the unchanged `tasl7_driver_snapshot()` record, and on
TASL-2 it never touches the 580-only package probe. The attempt-2 child records the matching generic `host_driver`
on TASL-2 (only for `--a3-short` probes) and `run_unit` accepts either record. TASL-7 manifest/record bytes are
unchanged.

**TASL-2 freeze pin.** No separate TASL-2 freeze file is committed. The TASL-2 host-equivalence and Unit B
rehearsal units recorded the TASL-2 venv freeze as 121 lines, sha256
`50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`, **byte-identical** to the committed
`docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` (and to the TASL-7 pin, same sha). The TASL-2
profile therefore pins that committed portal freeze; the code records both pins and the unit hashes both files (equal).
A future dedicated TASL-2 freeze pin would replace that file without logic change.

The same discovery (`attempt1_lease_log_path`) is used by the preflight verifier, `build_attempt1_provenance` and
(in turn) `snapshot_attempt1_lease_log` (MAJOR-1 fix, revision 2): a TASL-2 run snapshots the staged attempt-1 copy,
never the different live TASL-2 global log; a missing/mismatched selected log is a STOP.

Any other normalized hostname is a STOP before any root/marker/GPU work. The **multi-base attempt-1 code path**
(`main()` without `--probes-only`) remains TASL-7-only, exactly as before; only the probes-only attempt-2 path accepts
TASL-2.

### 1.2 Attempt-1 artifact verification replaces the attempt-1 boot-id equality gate

`verify_attempt1_boot_id(current, attempt1)` (MAJOR-1/round-2) is **removed**. In its place,
`verify_attempt1_artifacts(attempt1_root, current_boot_id, profile)` verifies the preserved attempt 1 against its
recorded hashes and **records and discloses the current boot id without comparing it to attempt-1's boot id**
(`boot_id_required: false`, `boot_id_matches_attempt1` computed for disclosure only). It is called from the preflight
(`verify_probes_only_pins(..., attempt1_root=...)`), i.e. **before the attempt-2 root is created**, and its record is
written to the `campaign_start` journal line (top level and inside `pins`).

Verified, fail-closed:

1. **Journal** — sha256 must equal `1e73e80fac2fb5262cffb8d599c8bd861d99d9f4b23b3c20f56543bca501a344` (81 events),
   with the existing journal facts (single trailing STOP, paper commit `b9ad6f8f`, attempt-1 boot id `2c9bb104…`,
   `gpu_seconds_total = 130745.3789889291`).
2. **The four `EVIDENCE/<base>/final/manifest.json` files and every file they list** — bases `kev-0.8b`, `kev-4b`,
   `qwen3.5-0.8b-base`, `qwen3.5-4b-base`. The attempt-1 schema is `trackp_run_manifest/v1`: its
   `model_files_sha256` maps relative saved-file paths to sha256 (4 model files per base in attempt 1:
   `adapter/README.md`, `adapter/adapter_config.json`, `adapter/adapter_model.safetensors`, `heads.safetensors`).
   The verifier (a) requires the manifest file itself to be a plain file whose sha256 equals the recorded inventory
   hash (`5ee8842a…`, `9d7b333d…`, `0381f73a…`, `9e1d5f08…`) with the expected schema, `evidence_label` `EVIDENCE`,
   and family (`kev`/`qwen_control`); (b) re-hashes **every listed file** under `final/saved/` and compares it to the
   recorded sha256; (c) requires `final/saved/manifest.json["files"]` to equal the final manifest's
   `model_files_sha256` and its own bytes to equal the recorded saved-manifest sha256 (`26d80be0…`, `e898d51a…`,
   `8524b503…`, `f4c36658…`); (d) refuses symlinked leaves **and** symlinked `EVIDENCE`/`<base>`/`final`/`saved`
   directories, unsafe paths, missing/extra unrecorded saved files; and (e) **requires** the manifest's recorded
   identity metadata (paper `b9ad6f8f`, harness `897d83c8`, attempt-1 boot id, driver `580.178.04`) — absent or
   different is a STOP. Each manifest's own sha256 and each file's sha256 are recorded in the preflight record.
3. **Backup archive** — `<attempt1-root>/../../backups/p3a_attempt1_final_saved_20261117T0015Z.tar.gz`
   sha256 `fa2437ee52d8873075c0bed6e88fba16d04deb2428e931a365dc602cdf902c87` (313 M; verified identical on TASL-7 and
   in the TASL-2 copy).
4. **Attempt-1 lease log** — sha256 `6950509182f4230dd2c7e2bad4253748415fa969e84ef9bdac21e19242b55077` (111 lines),
   discovered per host as in §1.1. The campaign's provenance takes the **same** verified path, so the BLOCKING-1
   read-only snapshot into `<new-root>/attempt1_provenance/gpu_lease_log.jsonl` copies the attempt-1 log on both
   hosts (TASL-7 live global log; TASL-2 staged copy), and the unit-start re-hash of that immutable snapshot is
   unchanged.
5. **Current boot id** — required non-empty and recorded (`preflight.boot_id`; campaign-start `boot_id`; inside
   `attempt1_artifacts`). It is not compared with the attempt-1 boot id; the record explicitly says
   `boot_id_required: false` and discloses `attempt1_boot_id` / `boot_id_matches_attempt1`.

Any missing or mismatched artifact is a `TrackPStop` before the new root/marker/GPU step. The preflight result now
also carries `host`, `host_profile` (driver/freeze pin/lease-log names), `expected_driver`, `driver` (the
host-parameterized snapshot) and `attempt1_artifacts`. `run_unit` keeps its within-campaign boot-id stability check,
now against `R.host_driver_snapshot()`, and accepts the child's `tasl7_driver` (TASL-7, unchanged) or `host_driver`
(other reviewed hosts) record for both the manifest and each `gpu_lease` event.

### 1.3 Tests

`r1/tests/test_trackp_p3a_probes_only.py` is extended: both host profiles and their driver/freeze pins; unknown-host
and wrong-driver (per host) refusal; TASL-2 preflight acceptance; the current boot id recorded and a **different**
boot accepted (no equality gate); artifact verification good/bad journal / listed saved file / pinned manifest bytes
/ archive / lease log; manifest schema/label/family, saved-manifest disagreement, unsafe path, unrecorded saved file
and symlinked-directory negatives; TASL-2 lease-log copy discovery; host-aware `build_attempt1_provenance`; the
preflight artifact record reaching the `campaign_start` journal; a campaign run with a non-attempt-1 boot id; and a
**real TASL-2 end-to-end campaign test** with the live TASL-2 global log different from the staged attempt-1 copy;
real-snapshot tests for the host-parameterized driver/boot path (`R.host_driver_snapshot`, `R.driver_record`, a real
`run_unit` on TASL-2-shaped OS primitives, and the `gpu_lease` `host_driver` record); and a test asserting the
TASL-7 snapshot record is returned unchanged. The A3-short delta, template/order, provenance, budget, marker,
unit-sequence and positive/negative dry-run tests are retained. `test_trackp_p3a_guarded.py` and
`test_trackp_gpu_budget_safety.py` only changed their `run_unit` boot-source stub (`host_driver_snapshot`) — their
coverage is otherwise unchanged.

**MINOR-1 (round 2) — what the e2e test actually stubs.** `_PreflightStubs` fakes only: the checkout/environment
identity checks (`verify_paper_head`, `verify_executing_files`, `R.git_commit`, `is_ancestor`, `registry.reverify`,
the git/config/uv `subprocess` calls), the live-host state checks (disk usage, GPU census, lease, priority markers,
foreign processes, marker helper), the child units and the marker. The host driver/boot snapshot is **real** (only
the OS primitives beneath it are faked), as are the attempt-1 artifact verification, `build_attempt1_provenance`,
`assert_attempt1_pins` and `snapshot_attempt1_lease_log`.

## 2. What did not change

- Probes, unit command lines and order (`DRYRUN kev-0.8b` n=8 then `EVIDENCE qwen3.5-4b-base` n=100, `--a3-short`,
  `--load` from attempt-1 `final/saved`), seeds, data (`e0_v1` sha), rule, approved config, registry and model files.
- Budgets/STOPs: 45-h lease STOP seeded with attempt-1's 36.318161 h, 60-h cap, projections (600 s / 1800 s), no
  retry, one-shot DRYRUN→EVIDENCE sequence.
- Attempt-1 provenance binding (journal/lease hashes, paper commit, boot-id **provenance pin** of the journal,
  `assert_attempt1_pins`, the read-only lease-log snapshot, unit-start drift re-verification, M13 template ids/order,
  per-unit sidecar `runner_manifest.json`). Only the **source discovery** of the lease log/pin hashes inside
  `build_attempt1_provenance`/`snapshot_attempt1_lease_log` changed (MAJOR-1 fix); the pinned values and the
  assert/snapshot semantics are unchanged, and TASL-7 selects the same path as before.
- Paper-head identity rules (`EXPECTED_PAPER_HEAD` acceptance: exact C, docs-only child, byte-exact delivery-pin
  child), executing-bytes pinning of the 12 files, harness/E0/rule/config/freeze checks (freeze now selected per host
  from the same two committed pins).
- Marker protocol, environment, journal event schema (new fields are additive).
- The attempt-1 multi-base campaign path (`--probes-only` absent; still TASL-7-only) and all non-P.3a code.
- Shared-module behaviour on TASL-7 is byte/record identical: `R.host_driver_snapshot()` returns the unchanged
  `tasl7_driver_snapshot()` record, `R.gpu_lease(..., record_host_driver=True)` adds no key on TASL-7, the child
  keeps recording `tasl7_driver` only, and the new `R.driver_record`/`R.host_driver_snapshot` code paths are inert
  off the attempt-2 probes path. The changes in `r1/c3/train/run.py`/`r1/scripts/trackp.py` are additive host-contract
  helpers (an opt-in keyword and a manifest-record selector); no probe/unit/seed/data/budget/STOP logic changes.

## 3. Exact CPU test commands and results (local Mac; no GPU/model/host)

Python: the workspace's existing CPU venv (`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/_harness_venv/bin/python`,
3.11.11, pytest 9.2.0); `torch` is not installed in it, so model/tokenizer tests cannot be collected/run here
(pre-existing environment limitation, identical on the D baseline).

```
cd .claude-worktrees/trackp-p3a-d2-20261119
../_harness_venv/bin/python -m pytest -q -p no:cacheprovider \
  r1/tests/test_trackp_p3a_guarded.py r1/tests/test_trackp_p3a_probes_only.py
```

- **After C2 revision 3 (round-2 review fixes): 69 passed, 5 failed, 2 skipped.** (Revision 2: 63 passed;
  revision 1: 56 passed.) The 5 failures are exactly the pre-existing torch-dependent tests
  (`test_real_subprocess_accepts_only_complete_unit`, `test_partial_report_without_manifest_is_not_complete`,
  `test_deadline_stops_real_fake_process`, `test_timeout_terminates_fake_descendant`,
  `test_golden_field_order_from_the_pinned_renderers`).
- **D baseline (same commands in `.claude-worktrees/trackp-p3a-code-20261116`): 49 passed, 5 failed, 2 skipped** —
  the same 5 torch failures. No new failure is introduced; the 20 net added passes are the new host/artifact tests
  (7 from revision 1, 7 from the round-1 review fixes including the TASL-2 e2e, and 6 from the round-2 review fixes:
  real host snapshot, TASL-7 snapshot identity, `gpu_lease` host record, real `run_unit` on TASL-2, `R.driver_record`
  and the child wiring check).
- `r1/tests/test_trackp_gpu_budget_safety.py` is unchanged by this unit and fails 6/9 identically on D and on C2
  (pre-existing environment: no NVIDIA `/proc` device here).
- `r1/tests/test_trackp_p3a_a3_short.py` cannot be collected on this Mac (imports `torch`); it is untouched.

No GPU job, no TASL host command, no evidence root, no marker, no lease was used. Nothing was pushed.

## 4. Attempt-1 artifact path discovery (fail-closed, parameterized by host)

- attempt-1 root: the operator's `--attempt1-root` (absolute, required) — TASL-7 and the staged TASL-2 copy both
  `/home/dowling/r1_trackp/runs/p3a_operator_20261027`.
- archive: `<attempt1-root>/../../backups/p3a_attempt1_final_saved_20261117T0015Z.tar.gz` (both hosts).
- lease log: per-host candidate names relative to `<attempt1-root>/..` (§1.1); the first existing candidate is
  hash-checked, and a mismatch/missing file STOPs with the tried paths listed.
- manifests/model files: `<attempt1-root>/EVIDENCE/<base>/final/{manifest.json,saved/...}` for the four bases.
- If the TASL-2 staging ever places the attempt-1 lease-log copy elsewhere, the preflight STOPs (listing the tried
  paths); the fix is a reviewed profile/path change, not a silent fallback — this is intentional fail-closed
  behavior and the only operational assumption added here.

## 5. Recorded attempt-1 manifest facts used for review (from the committed 16 Nov inventory capture)

The attempt-1 inventory (`reports/trackp_p3a_attempt1_inventory_20261116/`, read-only export) records the same four
`final/manifest.json` bytes. It lives on branch **`ops-tasl-20261116`** (the branch the PLAN row names), not on
published `main` and not in the delivery tree; the 17 Nov backup/delivery/equivalence reports cited above are on the
same branch. Revision 2 **pins** these eight hashes in `EXPECTED_ATTEMPT1_MANIFEST_SHA256` /
`EXPECTED_ATTEMPT1_SAVED_MANIFEST_SHA256` (MINOR-1 fix):

| base | final/manifest.json sha256 | final/saved/manifest.json sha256 |
|---|---|---|
| kev-0.8b | `5ee8842a9c7fda453b95bd50e187307b71eb1ce102e4308bd733ca0efbcb7006` | `26d80be0d7a6990c6867559c3337374c53e5c3ced22d15bf62c307e6f3ff090c` |
| kev-4b | `9d7b333d859c24bc25e2c2e74821b87e6fba9cd675540081b01647eabcbec6bb` | `e898d51ac173dedf053851cc1b5b89c5407308966024671e3e78e39dfde02d57` |
| qwen3.5-0.8b-base | `0381f73aeecae332ce509f291cd2d078cab7298ef3d1053468a222d9482244d1` | `8524b5033fb6f7094cd2cc022603107981bf93855d42db5f451f703f5d29e935` |
| qwen3.5-4b-base | `9e1d5f08c5e3360870cbedd7eab3f7353fa9421cd8f055079c526ee10736c688` | `f4c366588a3727d51cda0dc1be1c6b04ff218ec6256b826a829303a569fce401` |

The code now verifies both these manifest file sha256 pins and the manifests' recorded model-file hashes (and
saved-manifest agreement), and requires the recorded identity fields. Attempt-1 recorded model-file hashes are
unchanged by this unit (e.g. `qwen3.5-4b-base`: adapter README `d1502e5c…`, config `3b31604a…`, adapter `0b39d3fa…`, heads
`aeea9ec1…`).

## 6. Reviewer checklist

- C2 changes only the host contract + tests + docs: the supervisor, the host-parameterized snapshot/record helpers
  (`r1/c3/train/run.py`, `r1/scripts/trackp.py`) and tests/records. `git diff 8662e359..C2 -- r1/scripts/trackp_p3a_guarded.py`
  shows no change to probes/units/budget/STOP/template/paper-head logic; on TASL-7 the shared-module records are
  unchanged (`R.host_driver_snapshot` returns `tasl7_driver_snapshot`, the child keeps `tasl7_driver`, the lease
  events keep only `tasl7_driver`).
- D2 is a single-parent child of C2 whose runner blob is C2's blob with only the canonical `EXPECTED_PAPER_HEAD`
  line changed to C2 (`git rev-parse D2^` == C2; `git show D2:r1/scripts/trackp_p3a_guarded.py` vs
  `git show C2:r1/scripts/trackp_p3a_guarded.py` differ in exactly that line).
- The attempt-1 boot-id equality function is gone (`verify_attempt1_boot_id` absent). The separate within-unit
  boot-stability check in `run_unit` remains: it compares the running child's boot id with the **current campaign's
  own** start boot id (recorded in this journal) and is not the attempt-1 equality gate.
- Both host profiles and wrong-driver/wrong-host refusals have CPU tests; the current boot id is recorded.
- MAJOR-1 regression: `test_tasl2_campaign_end_to_end_uses_the_staged_attempt1_lease_log` drives the real
  preflight → `build_attempt1_provenance` → `assert_attempt1_pins` → `snapshot_attempt1_lease_log` path on a
  TASL-2-shaped tree (attempt-1 copy present, live TASL-2 global log different) and reaches `complete` without
  stubbing those functions; `grep -n "gpu_lease_log.jsonl" build_attempt1_provenance` shows no hard-wired path.
- The four final and four saved manifest sha256 pins equal the recorded inventory values (unit test).
- MAJOR-2 regression (round 2): the real `R.tasl7_driver_snapshot()` cannot return on TASL-2-shaped OS primitives,
  while the real `R.host_driver_snapshot`/preflight/child-record/`run_unit` path completes on them; no test stubs the
  blocking snapshot function, and the `_PreflightStubs` list is disclosed (§3).
- Nothing outside the new worktree was modified; no push/merge/deletion.

## 7. Limits / residual uncertainty

- **No host execution.** This unit did not contact TASL-7/TASL-2 and did not hash the real 313 M archive or the real
  ~350 M attempt-1 model files; the verification logic is exercised on synthetic trees whose expected hashes are
  monkeypatched. The first real preflight will pay a one-time I/O cost (journal + 8 manifests + ~20 model files +
  the 313 M archive) before any root/marker/GPU work.
- **TASL-2 freeze**: no dedicated TASL-2 freeze file exists; the portal freeze byte-identical to the TASL-7 pin is
  used and disclosed. If the author wants a separate TASL-2 pin, that is a one-file change.
- **TASL-2 capability scope.** With revision 3 the TASL-2 code path is executable and CPU-tested end-to-end on
  TASL-2-shaped OS primitives (host snapshot → preflight → provenance/assert/snapshot → child record → `run_unit`
  acceptance). This record still does **not** claim a TASL-2 hardware run: no host was contacted. The generic portal
  snapshot gates on `/proc` ↔ `nvidia-smi` agreement plus the expected driver pin, and records the driver-branch
  package inventory best-effort (Ubuntu package names are branch-specific; a missing branch package set is recorded,
  not silently ignored). The first real TASL-2 preflight/unit remains an operator step.
- **Delivery branch / detached HEAD (MINOR-4 fix).** C2 and D2 live on branch `trackp-p3a-d2-20261119`, and the
  unchanged paper-head identity rule does **not** accept that branch name. **Detached HEAD is therefore the only
  accepted form for D2** (as the 17 Nov TASL-2 D delivery did); do not run on the branch. `EXPECTED_PAPER_BRANCH` is
  intentionally unchanged: paper-head identity rules are outside this unit's scope.
- **C2/D2 delivery references (MINOR-4).** A commit cannot contain its own or its child's final sha (hash cycle), so
  the exact `C2`, `D2` and D2 runner-blob sha256 values are supplied to the coordinator with the completion handoff
  for the ops delivery record / `R1-TRACKP-UNITB` amendment. The ops delivery record must carry them.
- **TASL-2 lease-log copy path** is taken from the backup/delivery reports
  (`runs/_attempt1_gpu_lease_log.jsonl`); a different staging path needs a reviewed profile change (fail-closed). The
  provenance and snapshot now use this same path (revision 2); the live TASL-2 `gpu_lease_log.jsonl` is used only by
  the lease/budget accounting (it is the log this campaign's own children append to), never as an attempt-1 artifact.
- The boot id is no longer an equality gate, so a host reboot between attempt 1 and attempt 2 no longer blocks; the
  attempt-1 identity now rests on the recorded artifact hashes. This is exactly `R1-TRACKP-D2`'s intent and is
  disclosed in every `campaign_start`.
- One host per table: the code accepts both reviewed hosts and the TASL-2 path is now implemented/tested at CPU
  level, but this record does **not** claim that either host was used; the operator run report must name the actual
  host per `R1-TRACKP-UNITB`.
