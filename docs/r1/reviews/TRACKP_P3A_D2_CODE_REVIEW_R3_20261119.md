# Independent re-review — Track P P.3a D2 host-adaptation unit (round 3), 19 November 2026

**Status: ACCEPTED — 0 BLOCKING, 0 MAJOR, 3 MINOR (documentation only, non-blocking).** Round-2
**MAJOR-2 is FIXED and independently reproduced with the real functions**: the driver/boot snapshot is now
host-parameterized, a TASL-2 run passes `verify_probes_only_pins → build_attempt1_provenance →
assert_attempt1_pins → snapshot_attempt1_lease_log`, a real `run_unit` completes on a TASL-2-shaped child
`host_driver` record, the old TASL-7-only `tasl7_driver_snapshot()` cannot return on TASL-2-shaped OS primitives
and no P.3a test stubs it, and TASL-7 records are provably identical to D. Round-1 **MAJOR-1 remains fixed**.
Round-2 **MINOR-2 is fixed**; round-2 **MINOR-1 is materially fixed but its "exactly/nothing else" wording is still
not literal** (MINOR-1 below). New: two documentation imprecisions (stale delivery-record verification-command
values; an internal contradiction about `test_trackp_gpu_budget_safety.py` being "unchanged"). Fresh independent
reviewer; no part in authoring C2''/D2''. **Read-only review:** no code edit, commit, push, merge or deletion; no
TASL host, GPU, model, evidence root or HTCondor/deepthought contact. The only workspace change is this uncommitted
review file (untracked, as the earlier review records are); both worktrees were tracked-clean before and after
(`git status --porcelain` empty; HEADs unchanged).

## 0. Authority, canonical bytes, environment

- Published `main` = **`de3de54fd22dcdd86215be0924307e36a64ed08b`**; `R1-TRACKP-D2` (`origin/main:docs/r1/PLAN.md`,
  row after `R1-S2C3-ACCEPT`): authorize a host-adaptation unit producing D2 from D `8662e359`, changing only the
  host contract — accept TASL-7 (driver `580.178.04`) or TASL-2 (driver `535.309.01`, host-equivalence passed 17 Nov,
  replicated by `R1-TRACKP-TASL2-HOST`), each with its own driver pin; replace the attempt-1 boot-id equality check
  with verification of the attempt-1 artifacts against recorded hashes; record/disclose the current boot id;
  **nothing else changes (probes, seeds, data, budgets, STOPs)**; Unit B runs on TASL-7 first, TASL-2 if TASL-7 is
  unreachable; one host per table. `r1/c3/train/run.py` and `r1/scripts/trackp.py` are `EXECUTING_FILES`; as the
  round-2 review recorded, they may change **as part of the host contract** — which is what this revision does.
- Round-1 review read: `reviews/TRACKP_P3A_D2_CODE_REVIEW_20261119.md`, sha256 `1287b4a8…`; round-2 review read:
  `reviews/TRACKP_P3A_D2_CODE_REVIEW_R2_20261119.md`, sha256 `837d3490…` — both match the unit record's citations.
  Both are **untracked** in the ops worktree (`ops-tasl-20261116`, HEAD `364e94d9`); my R3 file is likewise untracked.
- Unit worktree: `.claude-worktrees/trackp-p3a-d2-20261119`, branch `trackp-p3a-d2-20261119`, HEAD = D2'' = `8309b69e`;
  clean before and after. Tests ran in `.claude-worktrees/_harness_venv` (Python 3.11.11, pytest 9.2.0, no `torch`,
  macOS). Synthetic trees and reviewer scripts lived under the platform temp dir and were removed; the real 313 M
  archive and attempt-1 model files were not hashed.

| Object | sha / detail |
|---|---|
| base **D** | `8662e35991659f7a661fb7ed6be4980791d302f3`; single parent `5b7ad0cb`; runner sha256 `c045475b458b0112315a04b858c2b2f407b668b64b8651f921441a1a24864e56` (1,505 lines) |
| **C2''** (code commit) | `9dc4afbaa29546dafb1d1274e37d3910c5d9ed0e`; `git rev-list --parents -n 1` = `9dc4afba 8662e359` (single parent = D); author/committer `Dowling Wong <wangdowling@gmail.com>`; runner sha256 `ae2a7955225b82a95faacbf0dedd1eff06f20ad7a2eddb6cf0cfc434c9469d72` (1,820 lines); `r1/tests/test_trackp_p3a_probes_only.py` sha256 `5bdd61ddc0081270f1a9ac2e53b5e7ada40a36ec152115b5d555c1d128edba86` (1,858 lines); `r1/c3/train/run.py` `d1c12ce62a1809ecf3ad913e56c3d36ee4f43fa2f32f9f206227a16ed376df95`; `r1/scripts/trackp.py` `5679ce1bc26721ca129fedf7e9e9bef705d8ce056eb2fac7e745d7879b65aee6`; unit report `9d594b4a52d1ed71d5739cdb2c3cce5a8ca3765a0a680d16954ce300f457bd35`; code-units addendum `319d185263cc2e769df93ea2abdea8f1a32ce971462fbd1e39b016f544612664` |
| **D2''** (delivery-pin child) | `8309b69e81837fb9719fa01b28f0dde94975e4f9`; `git rev-list --parents -n 1` = `8309b69e 9dc4afba` (single parent = C2''); runner sha256 **`d3419e2d2582367b5bb0b53994c9baaf5a04a3815b4b5a47ce38786c25a64750`**; adds only `docs/r1/reports/TRACKP_P3A_D2_DELIVERY_20261119.md` (sha256 `9223e24a8a66f040e4f9e75d894896dfe18a4c903cd8f8f06cd7816365713af1`) plus the one canonical pin line |
| `EXPECTED_PAPER_HEAD` at C2'' / D2'' | `5b7ad0cb…` / **`9dc4afba…`** (`r1/scripts/trackp_p3a_guarded.py:56`) |

`git diff --name-status 8662e359 9dc4afba` = `M docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md`,
`A docs/r1/reports/TRACKP_P3A_D2_CODE_UNIT_20261119.md`, `M r1/c3/train/run.py`, `M r1/scripts/trackp.py`,
`M r1/scripts/trackp_p3a_guarded.py`, `M r1/tests/test_trackp_gpu_budget_safety.py`, `M r1/tests/test_trackp_p3a_guarded.py`,
`M r1/tests/test_trackp_p3a_probes_only.py` (+1,472/−172). Incremental **C2'→C2''** (superseded round-2 commit
`dfd81ed1` still present) is the round-3 fix only: `run.py` +82/−1, `trackp.py` +8/−3,
`trackp_p3a_guarded.py` +5/−4 (two functions), probes-only tests +226/−30 (6 new tests, none removed),
`test_trackp_p3a_guarded.py`/`test_trackp_gpu_budget_safety.py` 6/−6 each (boot-source stub only), docs.

## 1. Round-2 MAJOR-2 — FIXED (independently reproduced with the real functions)

### 1.1 What was implemented

- `r1/c3/train/run.py:172-186` `host_driver_snapshot(expected_driver=None)`: on `tasl-7` it calls the **unchanged**
  `tasl7_driver_snapshot()` (`:151-169`, 580 package assertions intact) and additionally checks the expected pin when
  given; every other host goes to `_generic_driver_snapshot` (`:190-225`), which reads the same `/proc/driver/nvidia/
  version` + boot id + `nvidia-smi --query-gpu=driver_version` primitives, **requires kernel↔user agreement and the
  caller's expected driver pin**, then records the driver-branch package inventory (`nvidia-utils-<branch>`,
  `libnvidia-compute-<branch>`) best-effort (dpkg absent/non-zero is recorded as `nvidia_packages_checked: false`, a
  present-but-mismatched set STOPs). No 580-only probe on another host.
- `run.py:228-242` `driver_record(tiny, a3_short)`: tiny → `{}`; `tasl-7` → unchanged `{"tasl7_driver": …}` (every
  non-tiny run, exactly D's condition); other host + `--a3-short` (the attempt-2 probes path) → `{"host_driver": …}`;
  otherwise `{}` — i.e. inert off the probes path.
- `run.py:251-309` `gpu_lease(..., record_host_driver=False)`: opt-in only; on a portal host with
  `record_host_driver=True` it snapshots `host_driver` for the `start` and `end` events (boot-id stability checked
  between them); on TASL-7 no key is added a fortiori (portal guard false).
- `r1/scripts/trackp.py:91-93` `_driver_record(args)` = `R.driver_record(...)`; `:97-105` `_lease` passes
  `record_host_driver=bool(getattr(args, "a3_short", False))`; `:336-338` `main` uses
  `extra.update(_driver_record(args))` instead of the TASL-7-only branch. The probes command always carries
  `--a3-short` (`probes_only_units`), so the attempt-2 child on TASL-2 records generic `host_driver` at manifest top
  level **and** in both `gpu_lease` events; on TASL-7 it records `tasl7_driver` only, key order/bytes unchanged.
- `r1/scripts/trackp_p3a_guarded.py:739` `run_unit` boot check now calls `R.host_driver_snapshot()`;
  `:868` manifest driver = `tasl7_driver or host_driver`; `:875` per-lease-event driver =
  `(tasl7_driver or host_driver)`; `verify_probes_only_pins` `:1434` uses
  `R.host_driver_snapshot(profile["expected_driver"])`. There is **no remaining TASL-7-only call in the probes-only
  path**: `tasl7_driver_snapshot` appears only at `:1801` (`main()` non-probes attempt-1 multi-base campaign, still
  TASL-7-only by the unchanged `:1784-1785` guard) and inside `host_driver_snapshot`'s TASL-7 branch. The
  `run.py::gpu_lease` portal path never calls it.

### 1.2 Independent reproduction (real functions, TASL-2/TASL-7-shaped OS primitives only)

Reviewer-written script (not the unit's tests): only `/proc` text, `uptime`, `nvidia-smi`, `dpkg-query`, hostname,
git/config/registry identity checks, live-host state and the child script were faked; **none of the functions under
test was stubbed**. Section A/B loaded the real `run.py`; C/D the real `trackp_p3a_guarded.py`:

```
A. R.host_driver_snapshot on TASL-2-shaped primitives (kernel 535.309.01)
PASS A1 snapshot returns: nvidia_smi_driver=['535.309.01'], driver_branch='535', packages_checked=True,
        expected=['nvidia-utils-535','libnvidia-compute-535'], boot recorded
PASS A2 TASL-2 asked for 580.178.04 -> STOP "NVIDIA driver 535.309.01 is not the reviewed 580.178.04 on tasl-2"
PASS A3 580 kernel/user vs expected 535.309.01 -> STOP
PASS A4 kernel 535 / nvidia-smi 535.113.01 -> STOP "kernel/user driver mismatch"
PASS A5 empty nvidia-smi driver list -> STOP
PASS A6 dpkg unavailable -> best-effort record (nvidia_packages_checked=False, no STOP)
PASS A7 535-branch package version 535.113.01 != kernel module -> STOP
PASS A8 incomplete 535 package set -> STOP
PASS A9 R.tasl7_driver_snapshot() on TASL-2-shaped primitives -> STOP "TASL-7 driver snapshot failed:
        ... nvidia-utils-580"  (the old snapshot cannot return on TASL-2)

B. TASL-7 identity with D, and the record helpers
PASS B1 R.host_driver_snapshot() == R.tasl7_driver_snapshot() on TASL-7 (dict-for-dict)
PASS B2 base D's tasl7_driver_snapshot() (loaded from the D worktree) == C2'' R.host_driver_snapshot() on TASL-7
PASS B3 R.driver_record on TASL-7: {"tasl7_driver": …} for every non-tiny run, {} for tiny — D semantics
PASS B4 R.driver_record on TASL-2: {"host_driver": …} only for a3-short probe runs, {} otherwise
PASS B5 R.gpu_lease(record_host_driver=True) on TASL-2: host_driver in start+end, tasl7_driver None
PASS B6 R.gpu_lease(record_host_driver=True) on TASL-7: unchanged record (tasl7_driver only, no host_driver key)

C. Preflight chain (real verify_probes_only_pins -> verify_attempt1_artifacts -> build_attempt1_provenance ->
   assert_attempt1_pins -> snapshot_attempt1_lease_log) on a TASL-2-shaped tree whose attempt-1 lease copy is
   runs/_attempt1_gpu_lease_log.jsonl and whose live TASL-2 global log is a different 193-line log
PASS C1 preflight completed: host=tasl-2, expected_driver=535.309.01, boot recorded, lease =
        _attempt1_gpu_lease_log.jsonl (host profile lease names as designed)
PASS C2 provenance+assert: lease source = the staged copy, sha pinned
PASS C3 snapshot copied the staged attempt-1 log read-only
PASS C4 TASL-2 preflight with 580 driver -> STOP
PASS C5 TASL-2 preflight kernel/user disagreement -> STOP
PASS C6 regression simulation (G.R.host_driver_snapshot replaced by the pre-fix TASL-7-only snapshot):
        TASL-2 preflight -> STOP "TASL-7 driver snapshot failed" (the new tests would catch a MAJOR-2 regression)
PASS C7 TASL-7-shaped tree: preflight/provenance select the global gpu_lease_log.jsonl (unchanged)

D. Real run_unit on a TASL-2-shaped child manifest/lease (fake child process only; run_unit, the budget accounting
   and the real host snapshot are the shipped code)
PASS D1 TASL-2 child record (host_driver top level + both gpu_lease events) accepted -> unit_start, unit_complete
PASS D2 manifest with no driver record -> STOP "unit manifest label or boot ID mismatch"
PASS D3 gpu_lease event with a different boot id -> STOP "unit lease driver state missing or boot ID mismatch"
PASS D4 TASL-7-shaped tasl7_driver record accepted -> unit_start, unit_complete (unchanged)
```

### 1.3 Old TASL-7-only snapshot / test stubbing

- `R.tasl7_driver_snapshot()` is still defined (TASL-7 and the non-probes attempt-1 path need it) but **cannot
  return on TASL-2**: 580-only `dpkg-query` with `check=True` raises, and a hypothetical 580 install fails the
  version check (A9/C6). No probes-only call site remains, so it is not reachable on a TASL-2 attempt-2 run.
- **No P.3a test stubs the blocking function.** `_PreflightStubs` (`r1/tests/test_trackp_p3a_probes_only.py:891-983`)
  patches only identity/live checks, the child units and marker; `G.R.Path` is replaced by a wrapper returning fake
  text only for the two `/proc` files (`:969-970`, disclosed as an OS primitive), so the real
  `R.host_driver_snapshot`/`R.tasl7_driver_snapshot` run. No `monkeypatch` of `tasl7_driver_snapshot` exists in the
  P.3a suites; `host_driver_snapshot` is stubbed only in the pre-existing `run_unit` wiring tests
  (`test_trackp_p3a_guarded.py:23,36,56,75,92,143`, `test_trackp_gpu_budget_safety.py:27,175,195,217`, and
  `test_trackp_p3a_probes_only.py:1502,1534,1545`) where the snapshot is not the subject; the new
  `test_host_driver_snapshot_is_real_and_host_parameterized` (`:1735`), `test_host_driver_snapshot_returns_the_unchanged_
  tasl7_record` (`:1758`), `test_gpu_lease_records_a_host_driver_on_tasl2_for_attempt2_probes` (`:1767`),
  `test_run_unit_accepts_a_tasl2_shaped_child_manifest_and_lease` (`:1795`), `test_driver_record_helper_is_host_aware`
  (`:1838`) all drive the real snapshots; the last remaining source-level check
  (`test_child_trackp_wires_the_host_driver_record`, `:1853`) is asserted on `trackp.py` source because the child
  module needs the pinned torch env to import (disclosed).

### 1.4 Residual observations (not findings)

- The branch package inventory is best-effort by design (Ubuntu package names are branch-specific; e.g. a
  `…-535-server` packaging would be recorded as `checked: false`, not fatal). The version rule is the same one the
  proven TASL-7 snapshot uses, so a present package set must match the kernel module. The first real TASL-2
  preflight remains an operator step; a false STOP there is fail-closed, not silent.
- `run_unit` re-checks the current boot id at each unit start but does not re-assert the driver pin there (the pin is
  enforced at campaign start and the child's `host_driver` records the actual driver). A driver swap without a reboot
  in the middle of a campaign is recorded but not refused; acceptable under `R1-TRACKP-D2` (the card's driver cannot
  be changed while the job holds the GPU lease in normal operation) and disclosed as recorded, not gated.

## 2. Round-1 MAJOR-1 — remains FIXED

No change to `attempt1_lease_log_candidates/path`, `verify_attempt1_lease_log`, `build_attempt1_provenance`,
`snapshot_attempt1_lease_log`, `assert_attempt1_pins`, `make_unit_start_verifier` or `run_probes_only_campaign`
between C2' and C2'' (AST diff, §4). Independently re-reproduced end-to-end on TASL-2 in §1.2 C1–C3 (real
verifier → provenance → `assert_attempt1_pins` → snapshot, staged `_attempt1_gpu_lease_log.jsonl` selected, the
different live TASL-2 log never read as the attempt-1 artifact), and TASL-7 selects the global log (C7).

## 3. Round-2 MINOR-1 / MINOR-2

- **MINOR-2 fixed:** the TASL-2 preflight tests no longer stub `R.tasl7_driver_snapshot`; `_PreflightStubs` runs the
  real snapshots on faked OS primitives for both host shapes, and the new tests assert the real TASL-7-only function
  cannot return on TASL-2-shaped primitives (`:1074-1078`, A9 here). A MAJOR-2 regression would fail
  `test_preflight_accepts_tasl2_with_its_own_driver_and_refuses_the_other_host_driver` (`:1060`) and
  `test_run_unit_accepts_a_tasl2_shaped_child_manifest_and_lease` (`:1795`) — shown by the C6 simulation.
- **MINOR-1 materially fixed, wording still not literal:** the record no longer claims only child/live-host checks
  are stubbed and the driver snapshot is indeed no longer stubbed, but "list exactly what `_PreflightStubs` fakes"
  (unit report `:52, :155-160`) and the e2e docstring's "fakes only these dependencies, and nothing else"
  (`:1671-1679`) still omit that the class **rebinds the E0/rule/config/freeze path + expected-hash constants**
  (`:935-943`) and the amendment path, and that the e2e test also stubs `installed_kev_encoder` and
  `attempt1_environment` (`:1710-1711`). None of these can mask the host-snapshot defect (the driver path is real),
  but the claim should be worded exactly — **MINOR-1**.

## 4. Scope (review item 4) — PASS

Incremental C2'→C2'' changes in `trackp_p3a_guarded.py` are exactly **`run_unit`** and **`verify_probes_only_pins`**:
the boot-source call, the manifest-driver selector and the per-lease-event selector (3 lines) and one
`host_driver_snapshot(profile["expected_driver"])` call. Everything else in the supervisor is byte/segment identical
to C2' (which the round-2 review verified against D). `run.py` gains only `host_driver_snapshot`,
`_generic_driver_snapshot`, `driver_record` and an additive opt-in `record_host_driver` keyword in `gpu_lease`;
`trackp.py` gains `_driver_record`, the `_lease` keyword pass-through and the `main` record selector. Verified by an
`ast` top-level segment comparison of D→C2'' and C2'→C2'': unchanged byte-for-byte include `probes_only_units`,
`run_base`, `Attempt2Budget`/`GPUBudget`, `verify_paper_head`/`_delivery_pin_child`/`verify_executing_files`,
`EXECUTING_FILES`, `EXPECTED_PAPER_BRANCH`, the `EXPECTED_PAPER_HEAD` acceptance logic, template ids/order, seeds,
E0/rule/config/registry pins, budget constants, marker protocol and the attempt-1 multi-base path. No probe, unit,
seed, data, budget, STOP, marker or paper-head change; `run.py`/`trackp.py` changes are the additive host-contract
helpers the round-2 review condition explicitly permitted. `git diff 8662e359 9dc4afba` touches only the three code
files, the tests and the two authorised docs records. **Scope is within `R1-TRACKP-D2`.**

## 5. Delivery identity (review item 5) — PASS

Executed in the real D2'' worktree, no monkeypatching of the identity functions:

```
git rev-list --parents -n 1 9dc4afba  -> 9dc4afba 8662e359           (C2'': single parent D)
git rev-list --parents -n 1 8309b69e  -> 8309b69e 9dc4afba           (D2'': single parent C2'')
G.EXPECTED_PAPER_HEAD               = 9dc4afbaa29546dafb1d1274e37d3910c5d9ed0e
G.expected_pin_runner_blob() sha256 = d3419e2d2582367b5bb0b53994c9baaf5a04a3815b4b5a47ce38786c25a64750
HEAD:r1/scripts/trackp_p3a_guarded.py sha256 = d3419e2d…            (byte-exact mechanical pin)
G._delivery_pin_child(C2'') = False ; G._delivery_pin_child(D2'') = True ; G._delivery_pin_child(D) = False
G._docs_child_of_reviewed(D2'') = False
G.verify_paper_head({commit:D2'', branch:"HEAD"}) -> kind "delivery_pin_child"
G.verify_paper_head({commit:D2'', branch:"trackp-p3a-d2-20261119"}) -> TrackPStop (branch refused)
G.verify_paper_head({commit:D2'', branch:"main"}) -> TrackPStop
G.verify_paper_head({commit:C2'', branch:"HEAD"}) -> "exact_reviewed_runner_commit"
G.verify_executing_files() -> PASS (12 files, executing runner sha d3419e2d…, is_ancestor(C2'') true)
git diff --name-status 9dc4afba 8309b69e -> A docs/…/TRACKP_P3A_D2_DELIVERY_20261119.md, M r1/scripts/trackp_p3a_guarded.py
git diff 9dc4afba 8309b69e -- r1/ -> exactly the one canonical EXPECTED_PAPER_HEAD line substitution 5b7ad0cb→9dc4afba
```

- No merge commits; author/committer unchanged. D2'' differs from C2'' in no other file; the only two files are the
  allowed docs record and the pin line.
- Delivery-record values independently recomputed and matching the record's "Delivered objects" table: C2''
  `9dc4afba`, D2'' runner blob `d3419e2d`, C2'' runner `ae2a7955`, C2'' probes tests `5bdd61dd`, C2'' guarded/budget
  test stubs `58c264c0`/`b596d1f9`, C2'' `run.py` `d1c12ce6`, C2'' `trackp.py` `5679ce1b`, unit report `9d594b4a`,
  code-units addendum `319d1852`.
- Operator condition (correctly stated): **D2'' only as a detached HEAD**; the branch name is refused by the
  unchanged paper-head rule. `R1-TRACKP-UNITB` must name D2'' = `8309b69e…`, and the ops delivery record/handoff
  must carry `C2'' = 9dc4afba…`, `D2'' = 8309b69e…`, runner blob `d3419e2d…` (D2'' cannot contain its own or its
  child's sha; the record correctly supplies everything else).

## 6. Tests (review item 6) — PASS; no regression

Claimed command re-run in both worktrees (`PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):

```
C2''/D2'' (9dc4afba/8309b69e): 5 failed, 69 passed, 2 skipped
D (8662e359):                  5 failed, 49 passed, 2 skipped
```

The 5 failures are the same ids on both revisions and all `ModuleNotFoundError: No module named 'torch'`
(`test_real_subprocess_accepts_only_complete_unit`, `test_partial_report_without_manifest_is_not_complete`,
`test_deadline_stops_real_fake_process`, `test_timeout_terminates_fake_descendant`,
`test_golden_field_order_from_the_pinned_renderers`) — pre-existing environment limitation, identical on D; no
regression. +20 net passes vs D = 7 (revision 1) + 7 (round-1 fixes) + 6 (round-2 fixes: real host snapshot, TASL-7
identity, `gpu_lease` host record, real `run_unit` on TASL-2, `R.driver_record`, child wiring) — matches the record.
`test_trackp_p3a_probes_only.py` function count 56→62 with **nothing removed** (verified by AST), so no prior coverage
was dropped. Adjacent: `test_trackp_gpu_budget_safety.py` 6 failed/3 passed identically on D and C2''; 
`test_trackp_p3a_a3_short.py` collection error (imports `torch`) on both; `test_trackp_trainer.py` skipped on both.
The 20 host/driver-related new+adjusted tests pass (targeted run, `-k "host_driver or driver_record or tasl2 or
preflight or gpu_lease"` → 20 passed). New tests are meaningful: the real snapshot is exercised for both host shapes
with kernel/user disagreement, wrong pin, empty `nvidia-smi`, package-set and old-TASL-7-only cases; a real `run_unit`
consumes a TASL-2 child record and refuses missing/mismatched records; TASL-7 record identity with D is asserted.

## 7. Docs (review item 7) — substantively accurate; MINOR-2 and MINOR-3

Read in full: revised `docs/r1/reports/TRACKP_P3A_D2_CODE_UNIT_20261119.md` (§0.3/§1/§3/§6/§7) and
`docs/r1/reports/TRACKP_P3A_D2_DELIVERY_20261119.md`. Verified accurate: authority and canonical commits; "only the
host contract" scope and the `run.py`/`trackp.py` inclusion; host/driver/freeze table (both freeze files committed,
121 lines, byte-identical sha `50238e5a…`); the TASL-2 staged-lease path and the different live log; attempt-1
manifest hashes vs the 17 Nov basis records; 69/49 test numbers and torch failures; the round-2 response table;
"no host execution, code-level TASL-2 capability only" (`§7 :276-281`); detached-HEAD-only wording; C2''/D2''
runner-blob disclosure; the `_PreflightStubs` disclosure list (modulo MINOR-1). Not accurate:
 
- **MINOR-2 — delivery record §"Verification commands" carries stale superseded values.** `:59` cites
  `rev-parse HEAD^  # == C2 e8816221…`, but HEAD^ is `9dc4afba`; `e8816221…` is an earlier, superseded C2 candidate
  (same runner, different `test_trackp_p3a_probes_only.py`), not the delivered code commit. `:62` cites the runner
  sha as `f284d233…`, which is not a git object and matches neither C2'' nor D2'' (`d3419e2d…`). The "Delivered
  objects" table above those commands is correct and the real identity checks pass, so this is a non-blocking
  erratum; but the verification block would mislead an operator and should not be used as written.
- **MINOR-3 — internal contradiction about the unchanged-suite test file.** Unit report `§3 :206` says
  `r1/tests/test_trackp_gpu_budget_safety.py` "is unchanged by this unit", while `§1.3 :151-153` correctly says it
  changed its `run_unit` boot-source stub, and the C2'' tree indeed modifies it (6/−6, stub only). "Coverage
  otherwise unchanged" is the accurate wording.

The unit record also states `§7 :283-288` that the exact C2''/D2'' shas are supplied with the handoff so the ops
delivery record can carry them — the correct treatment given the hash cycle.

## 8. What was not checked / limits

No TASL-7/TASL-2 contact, no GPU, no model, no evidence root; the real 313 M archive and attempt-1 model files were
not hashed here. Artifact/host behaviour was exercised on synthetic trees and TASL-shaped OS primitives with only the
expected hashes/identity checks faked (as the unit's tests do); the recorded hashes/paths/drivers were cross-checked
against the committed 17 Nov basis records and the attempt-1 inventory (`_attempt1_gpu_lease_log.jsonl` 69505091…,
live TASL-2 log 193 lines, archive fa2437ee…, driver 535.309.01, boot 86c613a9…, freeze 50238e5a…). The TASL-2 code
path is verified at code level only; the first real TASL-2 preflight remains an operator step. A `py_compile` check of
the three changed modules touched only git-ignored `__pycache__` `.pyc` files; tracked worktree state stayed clean
(`git status --porcelain` empty, HEAD `8309b69e` before and after).

## 9. Verdict and conditions

**ACCEPTED — 0 BLOCKING, 0 MAJOR, 3 MINOR (documentation only).**

| # | Severity | Finding | Location |
|---|---|---|---|
| MAJOR-2 (round 2) | — | **FIXED.** Host-parameterized `R.host_driver_snapshot` backs the preflight and `run_unit`; the child records generic `host_driver` on TASL-2 (manifest + both `gpu_lease` events) and `run_unit` accepts it; TASL-2 preflight → provenance → assert → snapshot and a real `run_unit` complete on TASL-2-shaped primitives; driver mismatch/kernel-user disagreement STOP; old TASL-7-only snapshot cannot return on TASL-2 and no P.3a test stubs it; TASL-7 records equal D's | `r1/c3/train/run.py:172-242,251-309`, `r1/scripts/trackp.py:91-105,336-338`, `r1/scripts/trackp_p3a_guarded.py:739,868,875,1434` |
| MAJOR-1 (round 1) | — | **remains FIXED** (unchanged; re-reproduced end-to-end on TASL-2) | `trackp_p3a_guarded.py:1198-1360,1681-1750` |
| MINOR-1 (round 2, residual) | MINOR | The "exactly/nothing else" stub-disclosure claim is still not literal: `_PreflightStubs` also rebinds the E0/rule/config/freeze path+hash constants and the amendment path, and the e2e test also stubs `installed_kev_encoder`/`attempt1_environment`; none can mask the host-snapshot defect | unit report `:52,:155-160`; tests `:935-943,:1671-1679,:1710-1711` |
| MINOR-2 | MINOR | Delivery record §"Verification commands" cites stale/superseded values: `HEAD^ # == C2 e8816221…` (actual `9dc4afba`; e8816221 is a superseded C2 candidate) and runner `# f284d233…` (not an object; actual `d3419e2d…`). The "Delivered objects" table is correct | delivery record `:58-65` (`:59`, `:62`) |
| MINOR-3 | MINOR | Unit report §3 says `test_trackp_gpu_budget_safety.py` is "unchanged by this unit"; §1.3 and the tree show it changed its boot-source stub (6/−6) | unit report `:151-153` vs `:206` |

Round-2 findings dispositioned: MAJOR-2 fixed (above); MINOR-2 fixed; MINOR-1 materially fixed with the residual
wording above. Round-1 findings remain dispositioned as in the round-2 review.

**Conditions:**

1. **Operator/delivery:** run D2'' `8309b69e…` **detached only** (branch `trackp-p3a-d2-20261119` is refused); one
   host per table named in the report; `R1-TRACKP-UNITB` amended to name D2''; the ops delivery record/handoff carries
   `C2''=9dc4afba…`, `D2''=8309b69e…`, D2'' runner blob `d3419e2d…` (and can correct MINOR-2 in the handoff if the
   commits are not re-created).
2. **Non-blocking, recommended before handoff (commits are still unpublished, so cheap):** correct MINOR-2 and
   MINOR-3 in the delivery record/unit report and the residual MINOR-1 wording, then re-create C2/D2 and re-verify
   only identity: `expected_pin_runner_blob()` sha == the new D2 runner blob, `_delivery_pin_child(new D2) == True`,
   `verify_paper_head(new D2, "HEAD") == "delivery_pin_child"`, `verify_executing_files()` passes, and the claimed CPU
   command still gives 69/5/2 vs 49/5/2. Alternatively, record the MINOR-2 erratum explicitly in the ops delivery
   record.
3. **TASL-2 execution:** code-level capability is now verified; the first real TASL-2 preflight/unit remains an
   operator step and any host contact must be reported (one host per table, driver `535.309.01`, freeze sha
   `50238e5a…`).
