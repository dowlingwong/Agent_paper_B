# Independent re-review — Track P P.3a D2 host-adaptation unit (round 2), 19 November 2026

**Status: NOT ACCEPTED — 0 BLOCKING, 1 MAJOR (NEW: the TASL-2 fallback still cannot run — the probes-only preflight and
`run_unit` call the TASL-7-only `R.tasl7_driver_snapshot()`, whose `nvidia-utils-580` package assertion cannot pass on
TASL-2's driver `535.309.01`, and the unchanged child records `tasl7_driver` only on `tasl-7`, so a real TASL-2 run
STOPs in the preflight before the round-1 fix is ever reached), 2 MINOR.** The round-1 MAJOR-1 (attempt-1 lease-log
discovery hard-wired to TASL-7's live log) is **fixed and independently reproduced with the real functions**. Fresh
independent reviewer; no part in authoring C2/D2/C2'/D2'. **Read-only review:** no code, host, GPU, model, evidence
root, push, merge or deletion. The only workspace change is this uncommitted review file; both worktrees
(`trackp-p3a-d2-20261119`, `trackp-p3a-code-20261116`) were tracked-clean before and after (`git status --porcelain
--untracked-files=no` empty; HEADs unchanged). CPU tests ran in `/Users/wongdowling/Documents/agent_paper_B/
.claude-worktrees/_harness_venv` (Python 3.11.11, pytest 9.2.0, no `torch`, macOS). Synthetic trees were built under
`/tmp` (platform temp) and removed; no attempt-1/TASL artifact was touched.

## 0. Authority and canonical bytes

- Published `main` = **`de3de54fd22dcdd86215be0924307e36a64ed08b`**; `R1-TRACKP-D2` at `docs/r1/PLAN.md:1300`
  (`git show origin/main:docs/r1/PLAN.md`): host-adaptation unit producing D2 from D `8662e359`, changing only the
  host contract — accept TASL-7 (driver `580.178.04`) **or** TASL-2 (driver `535.309.01`, host-equivalence passed
  17 Nov), each with its own driver pin; replace the attempt-1 boot-id equality check with verification of the
  attempt-1 artifacts against recorded hashes (journal `1e73e80f…`, the four `final/manifest.json` and the files they
  list, archive `fa2437ee…`, lease log `69505091…`); record/disclose the current boot id; nothing else. Unit B runs
  on TASL-7 first and on TASL-2 if TASL-7 is unreachable (`R1-TRACKP-TASL2-HOST`); one host per table.
- Round-1 review read: `reviews/TRACKP_P3A_D2_CODE_REVIEW_20261119.md`, sha256
  `1287b4a81ae1c6a7c1f10792b6c806f4cd94f996fc6a4229869334550e1aa211` — matches the unit record's citation.
- The 17 Nov basis documents used by the unit (`TRACKP_TASL7_BACKUP_20261117.md`,
  `TRACKP_TASL2_EQUIVALENCE_RESULT_20261117.md`, `TRACKP_TASL2_DELIVERY_20261117.md`, the attempt-1 inventory
  `trackp_p3a_attempt1_inventory_20261116/`, `TASL2_UNITB_REHEARSAL_*`) live on branch **`ops-tasl-20261116`**
  (HEAD `7ceb43a3`) and are **absent from the delivery tree** (checked with `git cat-file -e D2':<path>`); the unit
  record §5/§7 states this — accurate.
- Worktree: `.claude-worktrees/trackp-p3a-d2-20261119`, branch `trackp-p3a-d2-20261119`, HEAD = D2' = `c93b423c`.

| Object | sha / detail |
|---|---|
| base **D** | `8662e35991659f7a661fb7ed6be4980791d302f3`; single parent `5b7ad0cb`; runner sha256 `c045475b458b0112315a04b858c2b2f407b668b64b8651f921441a1a24864e56` (1,505 lines) |
| **C2'** (code commit) | `dfd81ed1720a8429bc370344ff53696a4d51a5d9`; `git rev-list --parents -n 1` = `dfd81ed1 8662e359` (single parent = D); author/committer `Dowling Wong <wangdowling@gmail.com>`; runner sha256 `08408356d7315419eb0b22a11cfb3ba60ea875744f23069ad4ce74bdb1b975ed` (1,819 lines); tests sha256 `c4e11c076e26a51212154fbe9f4af4ba66cca6bf9d8034aad2be6a9c616ec4c1` (1,662 lines); unit report sha256 `2d319a37df5427b97b51c43c1b6bb52c5b9d460ad63052fe505b5bf31dc4b740`; code-units addendum sha256 `97a15e6620ca0f0ff3467a89a945eb21c27e7920b223d5d8e912b198347fd909` |
| **D2'** (delivery-pin child) | `c93b423c4716364a00f6821738ef67e04bbbe67d`; `git rev-list --parents -n 1` = `c93b423c dfd81ed1` (single parent = C2'); runner sha256 `c535ad5d63fb2401fb5800d2947d16cc9ac1caece48721e1f134dda6b78cc5a4` (blob `54c14b48`); adds `docs/r1/reports/TRACKP_P3A_D2_DELIVERY_20261119.md` (sha256 `59fdd01a…`) |
| `EXPECTED_PAPER_HEAD` in D2' | `dfd81ed1720a8429bc370344ff53696a4d51a5d9` == C2' (`r1/scripts/trackp_p3a_guarded.py:56`) |

`git diff --name-status 8662e359 dfd81ed1` = `M docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md`,
`A docs/r1/reports/TRACKP_P3A_D2_CODE_UNIT_20261119.md`, `M r1/scripts/trackp_p3a_guarded.py`,
`M r1/tests/test_trackp_p3a_probes_only.py` (+1,116/−125). `git diff --numstat dfd81ed1 c93b423c` =
`67 0 docs/r1/reports/TRACKP_P3A_D2_DELIVERY_20261119.md`, `1 1 r1/scripts/trackp_p3a_guarded.py`.

## 1. Round-1 MAJOR-1 — FIXED (independently verified with the real functions)

Code reading (D2' worktree):

- `attempt1_lease_log_candidates` / `attempt1_lease_log_path` (`r1/scripts/trackp_p3a_guarded.py:1198-1222`) are the
  single host-aware discovery: TASL-7 → `<attempt1-root>/../gpu_lease_log.jsonl` only; TASL-2 →
  `<attempt1-root>/../_attempt1_gpu_lease_log.jsonl` first, with the global name as a **fail-closed** fallback
  (the selected file is hash-checked; a mismatch/missing file STOPs; a symlinked candidate STOPs; the runs parent
  must not be a symlink). `verify_attempt1_lease_log` (`:1225-1236`) uses it.
- `build_attempt1_provenance(root, *, artifacts=None, profile=None)` (`:1286-1324`): the campaign path passes the
  preflight's verified `pins["attempt1_artifacts"]` record and **re-checks the recorded path + sha256**
  (`:1297-1309`); direct callers use the host-aware discovery (`:1310-1317`). No hard-wired `gpu_lease_log.jsonl`
  remains in the provenance path.
- `run_probes_only_campaign` passes `artifacts=pins["attempt1_artifacts"]` after requiring the record
  (`:1688-1693`); `assert_attempt1_pins` (`:1363-1374`) still pins `lease_log_sha256` to `69505091…`; the BLOCKING-1
  `snapshot_attempt1_lease_log` (`:1327-1360`) snapshots `provenance["lease_log"]`, i.e. the selected attempt-1 file.
- TASL-7 behaviour is unchanged by construction (same single candidate/path; same pinned sha; same snapshot bytes).

Independent reproduction (reviewer-written tree; **only the expected recorded hashes were monkeypatched**, the real
verifier/provenance/assert/snapshot functions ran; no host contact):

```
TASL-2-shaped <base>/runs/p3a_operator_20261027 + backups/<archive>;
runs/_attempt1_gpu_lease_log.jsonl = staged attempt-1 copy (pinned sha);
runs/gpu_lease_log.jsonl          = different "live TASL-2" log (193-line shape)
PASS verify_attempt1_artifacts(TASL-2): lease path = .../runs/_attempt1_gpu_lease_log.jsonl
PASS build_attempt1_provenance(artifacts=preflight record): lease path = .../_attempt1_gpu_lease_log.jsonl
PASS build_attempt1_provenance(profile=TASL-2):            lease path = .../_attempt1_gpu_lease_log.jsonl
PASS assert_attempt1_pins: lease sha == the pinned attempt-1 sha  (round-1 hard-wired path would have been the
     different live log: assert would STOP)
PASS snapshot_attempt1_lease_log: source = staged copy; dest attempt1_provenance/gpu_lease_log.jsonl; bytes equal
PASS TASL-7-shaped tree: global gpu_lease_log.jsonl selected → provenance → assert → snapshot unchanged
PASS fail-closed: TASL-2 staged missing + live different → TrackPStop (sha mismatch)
PASS fail-closed: TASL-2 staged symlink → TrackPStop
PASS fail-closed: artifact-record lease path swapped to the live log → TrackPStop (digest != recorded)
PASS fail-closed: snapshot provenance sha mismatch → TrackPStop
```

The new end-to-end test `test_tasl2_campaign_end_to_end_uses_the_staged_attempt1_lease_log`
(`r1/tests/test_trackp_p3a_probes_only.py:1603-1662`) does **not** stub `verify_probes_only_pins` or
`assert_attempt1_pins`: it drives the real preflight (`_PreflightStubs` patches only its dependencies), the real
`build_attempt1_provenance`, the real `assert_attempt1_pins`, the real unit-start verifier and the real
`snapshot_attempt1_lease_log`, with the live TASL-2 log different, and reaches `complete`. **MAJOR-1 is closed.**

## 2. NEW MAJOR — the TASL-2 fallback is still not executable (TASL-7-only driver snapshot)

### 2.1 The preflight/`run_unit` call a TASL-7-only helper that cannot return on TASL-2

`R.tasl7_driver_snapshot()` (`r1/c3/train/run.py:151-169`) is not host-generic:

- it queries **`nvidia-utils-580` / `libnvidia-compute-580`** (`:159`, `check=True`) and requires the package set to
  be exactly those two names with **package versions prefixed by the kernel-module version** (`:166`);
- TASL-2 is **driver `535.309.01`** (ops `TRACKP_TASL2_EQUIVALENCE_RESULT_20261117.md`, rehearsal STOP report:10,
  host-facts); its utils packages are the 535 branch. If the 580 packages are absent the `dpkg-query` fails
  (`CalledProcessError` → `TrackPStop`); if a 580 package were installed its version is 580.x ≠ `535.309.01`
  (`TrackPStop` "installed package/kernel driver mismatch"). There is no path in which this function returns on
  TASL-2.

It is called unconditionally by the probes-only path:
- `verify_probes_only_pins` (`r1/scripts/trackp_p3a_guarded.py:1433`, right after the freeze/registry checks and
  **before** `verify_attempt1_artifacts` at `:1441-1443`) — so a TASL-2 run STOPs in the preflight, before the
  MAJOR-1-fixed artifact/provenance path is ever reached;
- `run_unit` (`:739`, before every child) — same STOP once per unit;
- (`main()` `:1800` is the unchanged non-probes TASL-7-only path.)

Demonstration with the **real** `R.tasl7_driver_snapshot()`, faking only the OS primitives (`/proc` contents,
`nvidia-smi`, `dpkg-query`) to a TASL-2 shape (`Kernel Module 535.309.01`, boot `86c613a9…`):

```
[580 packages absent]     R.TrackPStop: TASL-7 driver snapshot failed: Command '['dpkg-query', ...,
                          'nvidia-utils-580', 'libnvidia-compute-580']' returned non-zero exit status 1.
[580 packages installed]  R.TrackPStop: TASL-7 NVIDIA installed package/kernel driver mismatch
```

The unit's TASL-2 tests hide this because `_PreflightStubs` monkeypatches `R.tasl7_driver_snapshot`
(`r1/tests/test_trackp_p3a_probes_only.py:945`) — the exact function that blocks TASL-2 is stubbed. The round-1
review's "wrong driver/empty driver/unknown host STOP (code)" was likewise checked against the stub, not the real
function.

### 2.2 Even past the preflight, the unchanged child and `run_unit` cannot pass on TASL-2

The child `r1/scripts/trackp.py` (unchanged by C2'; sha256 `d2a30ec2…`, blob `326b4422`, same in D and D2')
records `tasl7_driver` **only on `tasl-7`** (`r1/scripts/trackp.py:333-334`). On TASL-2 the attempt-2 child manifest
would therefore have no top-level `tasl7_driver`, and its `gpu_lease` events carry `tasl7_driver: null` (portal guard
in `R.gpu_lease`, `run.py:184,210`). The committed TASL-2 rehearsal manifest produced by this exact child on TASL-2
(`ops-tasl-20261116:docs/r1/reports/tasl2_rehearsal_20261117/DRYRUN/kev-0.8b/probes/manifest.json`) confirms both:
`"tasl7_driver" in manifest == False`, both `gpu_lease[*].tasl7_driver == None`. `run_unit` requires them
(`r1/scripts/trackp_p3a_guarded.py:866-875`): `manifest.get("tasl7_driver") or {}` → `.get("boot_id") != boot_id` →
STOP "unit manifest label or boot ID mismatch", and each lease event's missing driver boot id → STOP "unit lease
driver state missing or boot ID mismatch". So even if the preflight were fixed, the first unit would STOP — after its
GPU work — and the unit never reaches `unit_complete`.

### 2.3 Consequence, severity and doc accuracy

A real TASL-2 run is fail-closed (no attempt-2 root, marker, lease or GPU work before the STOP), so there is no
integrity or evidence risk; TASL-7 behaviour is unaffected. But the unit's declared purpose under `R1-TRACKP-D2` /
`R1-TRACKP-TASL2-HOST` — **TASL-2 acceptance** — is not delivered, exactly the class of defect the round-1 MAJOR-1
was. The record overstates the delivered capability and does not disclose this:
- unit report §1.1 ("Two profiles are accepted", table at `:46-56`), §1.1 `:69-71` ("only the probes-only
  attempt-2 path accepts TASL-2"), §7 `:244` ("the code accepts both reviewed hosts");
- delivery record `:31` ("Host profiles: TASL-7 … and TASL-2 …") and, most directly, `:40-41` "**so a TASL-2 run
  passes preflight → provenance → `assert_attempt1_pins` → snapshot**" — a TASL-2 run STOPs earlier, in
  `verify_probes_only_pins` at `R.tasl7_driver_snapshot()`.

**Required fix (host contract, within `R1-TRACKP-D2`):** a host-parameterized driver snapshot (per-host expected
package names/version rule, or a runner-local snapshot read from `/proc`/`nvidia-smi`) used by
`verify_probes_only_pins` and `run_unit`; and a host-aware boot-stability/child-driver handling — either record a
driver/boot snapshot on TASL-2 too (`r1/scripts/trackp.py:333-334`) or adapt the `run_unit` manifest/lease checks
(`:866-875`) to a TASL-2-provided boot id. `run.py`/`trackp.py` are `EXECUTING_FILES` and may be changed by C2 as
part of the host contract. Update the unit report/delivery record and add a test that exercises the real snapshot
path with a TASL-2-shaped OS (the current `_PreflightStubs` stub must not be the only coverage). Alternative (author
decision, not this reviewer's): explicitly scope the unit to TASL-7 and remove the TASL-2 claims — a deviation from
`R1-TRACKP-D2` that must be recorded. **Until fixed, D2' must not be represented as TASL-2-capable.**

## 3. Scope of C2'/D2' (review item 2) — PASS

`C2'` touches only `r1/scripts/trackp_p3a_guarded.py`, its probes-only tests, the new D2 unit report and the
code-units §7 addendum; `D2'` adds only the delivery record plus the one canonical `EXPECTED_PAPER_HEAD` line.
To test "nothing else changes" independently of the prose, both runner blobs were parsed with `ast` and every
top-level function/class/assignment compared by exact source segment (126 of 138 D items byte-identical;
TASL-7 `if __name__` line-number artifact only):

- changed: module docstring, `FREEZE_PIN` (comment only), `attempt1_journal_facts` (symlink refusals),
  `build_attempt1_provenance`, `snapshot_attempt1_lease_log` (docstring), `verify_probes_only_pins`,
  `campaign_start_record`, `run_probes_only_campaign`, `main` — all host-contract / artifact-verification / boot-id
  disclosure;
- added: host constants and `normalized_hostname`, `host_profile`, `attempt1_lease_log_candidates`,
  `attempt1_lease_log_path`, manifest-sha pins, `verify_attempt1_manifest`/`_archive`/`_lease_log`/
  `_artifacts`, `attempt1_archive_path`, `_require_plain_file`/`_require_plain_dir`;
- removed: `EXPECTED_DRIVER`, `verify_attempt1_boot_id`.

Unchanged, byte-identical: `probes_only_units`, `run_base`, `run_unit` (content), `Attempt2Budget`/`GPUBudget`,
`verify_paper_head`/`_delivery_pin_child`/`verify_executing_files`, `EXECUTING_FILES`, `PAPER_BASE_PIN`/
`EXPECTED_PAPER_HEAD` acceptance logic, `EXPECTED_PAPER_BRANCH`, template ids/order, marker protocol, seeds, E0/rule/
config/registry pins, the attempt-1 multi-base path. The manifest-sha pins and identity-required checks are the
round-1 MINOR-1 fix, inside "verification of the attempt-1 artifacts". **Scope is within `R1-TRACKP-D2`.**

## 4. Delivery identity (review item 5) — PASS

- Single parents: `git rev-list --parents -n 1 dfd81ed1` = `dfd81ed1 8662e359`; for `c93b423c` = `c93b423c dfd81ed1`;
  no merge commits.
- Byte-exact mechanical pin: `G.expected_pin_runner_blob()` (C2' runner blob with the single canonical
  `EXPECTED_PAPER_HEAD` line replaced by the line naming C2') equals D2's runner blob byte-for-byte; sha256
  `c535ad5d63fb2401fb5800d2947d16cc9ac1caece48721e1f134dda6b78cc5a4`. `git diff C2' D2' -- r1/` is exactly the one
  substitution line (`- 5b7ad0cb…`, `+ dfd81ed1…`); the only other D2' change is the docs record.
- Executed in the real worktree (no monkeypatch):
  `_delivery_pin_child(C2') = False`, `_delivery_pin_child(D2') = True`, `_docs_child_of_reviewed(D2') = False`,
  `verify_paper_head(D2', branch="HEAD") → kind "delivery_pin_child"`,
  `verify_paper_head(D2', branch="trackp-p3a-d2-20261119") → TrackPStop (branch not accepted)`,
  `verify_paper_head(C2', branch="HEAD") → "exact_reviewed_runner_commit"`,
  `verify_executing_files()` PASSES (12 files, executing runner sha `c535ad5d…`, `is_ancestor(C2', HEAD)` true).
- Delivery-record values independently re-computed: C2' runner `08408356…`, D2' runner `c535ad5d…`, C2' tests
  `c4e11c07…`, C2' unit report `2d319a37…`, C2' code-units addendum `97a15e66…`, C2' sha `dfd81ed1…` — all match.
- Operator condition (correctly stated in §7/delivery record): **D2' only as a detached HEAD**; the delivery branch
  name is refused by the unchanged paper-head rule. `R1-TRACKP-UNITB` must name D2'.
- **Condition (not a defect):** D2' cannot contain its own sha (hash cycle). The delivery record carries C2' and the
  D2' runner blob and says the D2' commit sha is supplied with the handoff; the **ops delivery record / handoff must
  carry `C2' = dfd81ed1…`, `D2' = c93b423c…`, runner blob `c535ad5d…`** or the pin child is unreferenced.

## 5. Artifact verification / fail-closed correctness (review item 4) — PASS (TASL-7/TASL-2 artifact data)

- **Pinned hashes match the committed inventory**: `sha256(ops-tasl-20261116/.../trackp_p3a_attempt1_inventory_
  20261116/SHA256SUMS)` entries for the four `EVIDENCE/<base>/final/manifest.json` and the four
  `final/saved/manifest.json` equal `EXPECTED_ATTEMPT1_MANIFEST_SHA256` / `EXPECTED_ATTEMPT1_SAVED_MANIFEST_SHA256`
  exactly (`kev-0.8b 5ee8842a…/26d80be0…`, `kev-4b 9d7b333d…/e898d51a…`,
  `qwen3.5-0.8b-base 0381f73a…/8524b503…`, `qwen3.5-4b-base 9e1d5f08…/f4c36658…`).
- Verifier (`verify_attempt1_manifest` `:1094-1175`, `verify_attempt1_archive` `:1184-1195`,
  `verify_attempt1_lease_log` `:1225-1236`, orchestrator `:1239-1283`): final manifest sha + schema
  `trackp_run_manifest/v1` + `evidence_label EVIDENCE` + family match; saved manifest sha and `files ==
  model_files_sha256`; every listed model file re-hashed; absolute/`..` paths, non-string entries, missing leaf,
  symlinked leaf, unrecorded extra saved file, symlinked `EVIDENCE`/`<base>`/`final`/`saved` directory and
  root/journal/backups/runs parents all STOP; archive sha `fa2437ee…`; lease sha `69505091…`; missing/mismatched
  artifacts STOP before the attempt-2 root. Identity metadata is now **required** (paper `b9ad6f8f`, harness
  `897d83c8`, attempt-1 boot `2c9bb104…`, driver `580.178.04`); the ops M13/inventory evidence states attempt-1
  manifests record exactly those (M13 review `:79-83`, inventory result `:40-41`), so the real tree passes.
- Host profiles (`host_profile`/`normalized_hostname` `:284-306`): TASL-7 driver `580.178.04`, TASL-2 driver
  `535.309.01`, distinct freeze pins; both committed freeze files are byte-identical (121 lines,
  sha `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`), matching the TASL-2 host-equivalence
  record; unknown host/wrong driver/empty driver STOP. **But** on TASL-2 the real driver snapshot STOPs first — the
  new MAJOR above.
- Current boot id is required non-empty and recorded (`preflight.boot_id`, `attempt1_artifacts.current_boot_id`,
  `campaign_start.boot_id`); `boot_id_required: false` and `boot_id_matches_attempt1` are disclosure only;
  `verify_attempt1_boot_id` is absent and there is no current-vs-attempt-1 equality gate (remaining boot-id
  comparisons are attempt-1 identity and within-campaign stability only).
- Attempt-1 lease-log facts corroborated: staged TASL-2 copy `69505091…` (111 lines); TASL-2 live global log 193
  lines `edc8247b…`; archive `fa2437ee…` at `<attempt1-root>/../../backups/` on both hosts (ops 17 Nov backup
  report).

## 6. Tests (review item 6) — PASS on the claimed numbers, no regression

Claimed command, re-run in both worktrees (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```
cd .claude-worktrees/trackp-p3a-d2-20261119
../_harness_venv/bin/python -m pytest -q -p no:cacheprovider \
  r1/tests/test_trackp_p3a_guarded.py r1/tests/test_trackp_p3a_probes_only.py
C2'/D2': 5 failed, 63 passed, 2 skipped
D (8662e359, .claude-worktrees/trackp-p3a-code-20261116): 5 failed, 49 passed, 2 skipped
```

The five failures are the same ids on both revisions and all `ModuleNotFoundError: No module named 'torch'`
(`test_real_subprocess_accepts_only_complete_unit`, `test_partial_report_without_manifest_is_not_complete`,
`test_deadline_stops_real_fake_process`, `test_timeout_terminates_fake_descendant`,
`test_golden_field_order_from_the_pinned_renderers`) — pre-existing environment limitation, no regression; +14 net
passes are the new host/artifact tests (matches the report's +7 from revision 1 and +7 from round-1 fixes).
Adjacent claims re-checked: `test_trackp_gpu_budget_safety.py` 6 failed/3 passed identically on D and D2';
`test_trackp_p3a_a3_short.py` collection error on both (imports `torch`, untouched). The 26 host/artifact/provenance/
e2e tests all pass. New tests are meaningful (TASL-2 staged-copy discovery, host-aware provenance, real TASL-2
end-to-end, manifest pin mismatch, schema/label/family, saved-manifest disagreement, unsafe path, extra file,
symlinked directory/leaf, boot-id requirement, no-equality campaign). **Coverage gap:** the TASL-2 preflight tests
stub `R.tasl7_driver_snapshot` (see §2.1), so the suite cannot detect the new MAJOR — MINOR-2.

## 7. Docs (review item 7) — mostly accurate; one capability overclaim

Read in full: revised `docs/r1/reports/TRACKP_P3A_D2_CODE_UNIT_20261119.md` (§0.2/§7) and
`docs/r1/reports/TRACKP_P3A_D2_DELIVERY_20261119.md`. Verified accurate: authority and canonical commits; "only the
host contract" for the artifact/lease work; freeze-pin claim; eight manifest pins vs inventory; TASL-2
staged-lease path and live-log distinction; 63/49 test numbers and the torch failures; basis documents' ops branch;
detached-HEAD-only wording; C2'/D2' runner-blob disclosure; "no host execution" residual; TASL-2 staging-path
assumption disclosed as the only added operational assumption; "D2 cannot contain its own sha; ops record must carry
it". **Inaccurate:** the claimed TASL-2 capability ("a TASL-2 run passes preflight → provenance → assert →
snapshot", del. record `:40-41`; "the code accepts both reviewed hosts", unit record `:244`) is contradicted by
§2 above: a real TASL-2 run STOPs in the preflight at `R.tasl7_driver_snapshot()`. The unit report also says
`test_trackp_p3a_guarded.py` needed no change because its boot-stability check compares the current campaign's own
boot id — true, but that check is one of the TASL-7-only call sites (§2.1).

## 8. What was not checked / limits

No TASL-7/TASL-2 contact, no GPU, no model, no evidence root; the real 313 M archive and ~350 M attempt-1 model
files were not hashed here. Artifact behaviour was exercised on synthetic trees with monkeypatched expected hashes
(as the unit's own tests do); the real recorded hashes/paths were validated against the committed 17 Nov
reports/inventory only. The TASL-2 driver-snapshot failure is established from the pinned code + the documented
TASL-2 driver/package facts and demonstrated with the real function against TASL-2-shaped OS primitives; it is not a
claim that TASL-2 hardware was run.

## 9. Verdict and conditions

**NOT ACCEPTED — 0 BLOCKING, 1 MAJOR (new), 2 MINOR.**

| # | Severity | Finding | Location |
|---|---|---|---|
| MAJOR-1 (round 1) | — | **FIXED.** Attempt-1 lease-log discovery is host-aware and used by verifier → provenance → `assert_attempt1_pins` → snapshot; TASL-7 identical; reproduced with the real functions | `r1/scripts/trackp_p3a_guarded.py:1198-1360`, `:1688-1693` |
| **MAJOR-2 (new)** | **MAJOR** | **TASL-2 fallback still not executable.** `verify_probes_only_pins` (`:1433`) and `run_unit` (`:739`) call the TASL-7-only `R.tasl7_driver_snapshot()` (`r1/c3/train/run.py:151-169`; hard-coded `nvidia-utils-580`/`libnvidia-compute-580`, package version == kernel-module version), which cannot return on TASL-2 (driver `535.309.01`) → preflight STOP before the artifact/provenance path; past that, the unchanged child records `tasl7_driver` only on `tasl-7` (`r1/scripts/trackp.py:333-334`) while `run_unit` requires it (`:866-875`), so the first unit would STOP after GPU work. Fail-closed, no integrity risk, but the `R1-TRACKP-D2`/`R1-TRACKP-TASL2-HOST` purpose is not delivered and the record claims otherwise | see §2 |
| MINOR-1 | MINOR | The new e2e test's/record's claim that "only the child units/marker/live-host checks are stubbed" is inaccurate: `_PreflightStubs` also stubs the checkout/environment identity checks (`verify_paper_head`, `verify_executing_files`, `R.git_commit`, `subprocess.run`, `registry.reverify`, `is_ancestor`, `r1/tests/...:937-941`). It cannot mask the lease-log defect (the target path is real) and those checks have separate tests, but the claim should be worded correctly | `r1/tests/test_trackp_p3a_probes_only.py:891-983`, `:1603-1610`; unit report §0.2/§3 |
| MINOR-2 | MINOR | The TASL-2 preflight/host-profile tests stub `R.tasl7_driver_snapshot` (`:945`), so "TASL-2 preflight acceptance" is not tested against the real host-specific function and the new MAJOR escaped. Exercise the real/adapted snapshot with TASL-2-shaped OS primitives (or a host-aware snapshot function) | `r1/tests/test_trackp_p3a_probes_only.py:945`, `:1000-1013` |

**Conditions for acceptance (fix and re-review):**

1. **MAJOR-2:** make the driver/boot-id path host-parameterized for the two reviewed hosts (per-host expected
   driver/package rule, or a runner-local `/proc` + `nvidia-smi` snapshot) and use it in `verify_probes_only_pins`
   and `run_unit`; make the attempt-2 child's driver/boot recording (or the `run_unit` manifest/lease checks)
   host-aware; update the unit report/delivery record; add a test that does not stub the blocking function for the
   TASL-2 case. Re-review required. (Alternative author decision: scope the unit to TASL-7 only, delete the TASL-2
   claim, and record the `R1-TRACKP-D2` deviation — this reviewer cannot accept a TASL-2 claim that cannot run.)
2. Until then, D2' may be used on **TASL-7 only** (detached HEAD) and must not be represented as TASL-2-capable.
3. Non-blocking: MINOR-1 (test/record wording) and MINOR-2 (real TASL-2 snapshot coverage).
4. Operator/delivery: run D2' **detached only**; one host per table named in the run report; `R1-TRACKP-UNITB`
   amended to name D2'; the ops delivery record/handoff must carry `C2' = dfd81ed1…`, `D2' = c93b423c…` and the D2'
   runner blob `c535ad5d…`.

Round-1 findings otherwise dispositioned: MINOR-1 (manifest/saved pins + required identity) fixed and verified;
MINOR-2 (symlinked directories) fixed for `EVIDENCE`/`<base>`/`final`/`saved`/root/journal/`backups`/runs and tested;
MINOR-3 (TASL-2 e2e + negative cases) added and passing; MINOR-4 (ops-branch basis docs, detached-only wording,
delivery references) addressed with the D2' commit-sha condition above.
