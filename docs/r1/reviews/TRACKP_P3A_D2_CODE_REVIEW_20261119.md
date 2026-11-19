# Independent review — Track P P.3a D2 host-adaptation code unit (C2 / D2), 19 November 2026

**Status: NOT ACCEPTED — 0 BLOCKING, 1 MAJOR (TASL-2 attempt-1 provenance still hard-wires the TASL-7 live lease
log, so a TASL-2 run STOPs after the preflight), 4 MINOR.** Fresh independent reviewer; no part in authoring,
committing or delivering C2/D2. **Read-only review.** No push, commit, merge or deletion; the D2 worktree was not
modified (verified clean before and after); no TASL host, no GPU, no model, no evidence root was touched. The only
workspace change made by this review is this uncommitted review file plus transient `/tmp` scratch files and a
transient `/tmp` synthetic tree used for the adversarial checks. CPU tests were run in the existing CPU-only venv
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/_harness_venv` (Python 3.11.11, pytest 9.2.0, no
`torch`, macOS).

## 0. Authority and canonical bytes

Authority read from **published `main` `de3de54fd22dcdd86215be0924307e36a64ed08b`**
(`git -C .claude-worktrees/ops-tasl-20261116 show origin/main:docs/r1/PLAN.md`):

- `R1-TRACKP-D2` (PLAN line 1300): authorize a host-adaptation unit producing D2 from D `8662e359`, changing only
  the host contract: accept TASL-7 (driver `580.178.04`) or TASL-2 (driver `535.309.01`; host-equivalence passed
  17 Nov), each with its own driver pin; replace the attempt-1 boot-id equality check with verification of the
  attempt-1 artifacts against their recorded hashes (journal `1e73e80f…`, the four `final/manifest.json` and the
  files they list, archive `fa2437ee…`, lease log `69505091…`), recording and disclosing the current boot id;
  nothing else (probes, seeds, data, budgets, STOPs).
- `R1-TRACKP-UNITB` (line 1246): Unit B runs on D (to be amended to D2), 45 GPU-h; `R1-TRACKP-TASL2-HOST`
  (line 1275): evidence tables may be produced on TASL-2 or TASL-7, one host per table, named in the report.

Supporting 17 Nov basis documents cited by the unit (`reports/TRACKP_TASL7_BACKUP_20261117.md`,
`reports/TRACKP_TASL2_EQUIVALENCE_RESULT_20261117.md`, `reports/TRACKP_TASL2_DELIVERY_20261117.md`,
`reports/trackp_p3a_attempt1_inventory_20261116/`) exist on branch `ops-tasl-20261116` (the branch the PLAN row
itself names), **not** on published `main` and **not** in the D2 branch; they were read from the ops worktree.

Worktree under review: `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackp-p3a-d2-20261119`
(local branch `trackp-p3a-d2-20261119`; HEAD = D2; clean before and after the review).

| Object | sha / detail |
|---|---|
| base **D** | `8662e35991659f7a661fb7ed6be4980791d302f3`; parent `5b7ad0cb7fedd083bad457968dc3dd3e920ac154`; subject `docs(r1): P.3a runner review-fixes (round 2) record + delivery pin` |
| **C2** (code commit) | `f95eb8e41477aa63beda25c63d76d3161e68a149`; single parent = D; subject `fix(r1): Track P D2 host adaptation (TASL-7/TASL-2) + attempt-1 artifact hash verification`; author/committer `Dowling Wong <wangdowling@gmail.com>` |
| **D2** (mechanical pin child) | `246ed88b07967dc858e086eeee0d9316b8a6092f`; single parent = C2; subject `docs(r1): Track P P.3a D2 delivery pin (host adaptation C2)` |
| `r1/scripts/trackp_p3a_guarded.py` | D `c045475b458b0112315a04b858c2b2f407b668b64b8651f921441a1a24864e56` (1,505 lines); C2 `6f7c3befee53c7128cceacd81b4d2d008dc9e559320dd7eba459933b37754dd7`; D2 `0f9b76d4191093a66159cc4e468ee7cc926ba869abd7ec4d12f180d1f284620f` (both 1,742 lines) |
| `r1/tests/test_trackp_p3a_probes_only.py` | D `880172d8a5f29e1bb7f6b7c44b826db2424752aec807d54d44ca3c9ff5eac6c7` (1,267 lines); C2 = D2 `5bfe3b8ddcc44856166d80aa6fcc442f4ec752cb6795346a5724895b3da4e367` (1,465 lines) |
| `docs/r1/reports/TRACKP_P3A_D2_CODE_UNIT_20261119.md` | C2 = D2 `b57f4b686a4cfb1685b88eef81fd90517f8cf82a7b9d581b2967f654e5c62600` (200 lines) |
| `docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md` | D `032e1e7aef6d7d282ef55ea774fbe4fe71b8f96ce531f9131ca7ab4936f28558` (385 lines); C2 = D2 `7f4ca285fe0ff6c447eac7d1769517bd3f8a0cdbcc6bda45042459620eeb25e6` (414 lines) |

The delivered D on TASL-2 (per `TRACKP_TASL2_DELIVERY_20261117.md`) has runner `c045475b…`, which matches D here
(§4) — the delivery reference is consistent.

## 1. Scope of C2 and D2 (review item 1) — PASS

```
$ git diff --name-status 8662e359  f95eb8e4
M  docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md
A  docs/r1/reports/TRACKP_P3A_D2_CODE_UNIT_20261119.md
M  r1/scripts/trackp_p3a_guarded.py
M  r1/tests/test_trackp_p3a_probes_only.py
$ git diff --stat 8662e359 f95eb8e4
 4 files changed, 758 insertions(+), 94 deletions(-)
$ git diff --name-status f95eb8e4 246ed88b
M  r1/scripts/trackp_p3a_guarded.py          # one line only
```

No other path changed; no deletion; no file outside `r1/` beyond the two authorised docs records.

To check "nothing else changes" independently of the diff's prose, both runner blobs were parsed with `ast` and every
top-level function/class/assignment compared by exact source segment. Exactly this changed:

- changed definitions: `campaign_start_record`, `main`, `run_probes_only_campaign`, `verify_probes_only_pins`;
- added: `_require_plain_file`, `attempt1_archive_path`, `host_profile`, `normalized_hostname`,
  `verify_attempt1_archive`, `verify_attempt1_artifacts`, `verify_attempt1_lease_log`, `verify_attempt1_manifest`,
  and constants `ATTEMPT1_ARCHIVE_NAME`, `ATTEMPT1_BASE_FAMILIES`, `ATTEMPT1_EVIDENCE_BASES`,
  `ATTEMPT1_MANIFEST_SCHEMA`, `EXPECTED_ATTEMPT1_ARCHIVE_SHA256`, `EXPECTED_DRIVER_TASL2`, `EXPECTED_DRIVER_TASL7`,
  `FREEZE_PIN_TASL2`, `HOST_TASL2`, `HOST_TASL7`;
- removed: `verify_attempt1_boot_id`, `EXPECTED_DRIVER`.

All other 110 top-level items are byte-identical, including `probes_only_units`, `run_base`, `run_unit`,
`Attempt2Budget`/`GPUBudget`, unit order, seeds, E0/rule/config/registry pins, template ids/order, marker protocol,
`PAPER_BASE_PIN`, `EXPECTED_PAPER_HEAD` (unchanged in C2), `EXECUTING_FILES`, and the attempt-1 multi-base
(`verify_pins`/`main` non-probes) path. C2's change set is the host contract + boot-id disclosure + the new artifact
verification + tests/docs only. **Scope is within `R1-TRACKP-D2`.**

## 2. Host contract and fail-closed behaviour (review item 2)

### 2.1 Host profiles — PASS

`host_profile`/`normalized_hostname` (`r1/scripts/trackp_p3a_guarded.py:269-291`) accept only `tasl-7`
(driver `580.178.04`, freeze `tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt`) and `tasl-2`
(driver `535.309.01`, freeze `trackp_phase2_20261026/pip_freeze_trackp-gpu.txt`); anything else raises
`TrackPStop` before root/marker/GPU work. The multi-base attempt-1 path stays TASL-7-only (`:1704-1707`), as before.

Freeze-pin claim checked: both committed freeze files exist, are **byte-identical** (121 lines,
`sha256 50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`), matching the TASL-2
host-equivalence/rehearsal record's freeze (121 lines, same sha) and PLAN's TASL-2 host-equivalence basis. Wrong
driver for the matched host, empty driver list, and unknown host all STOP (code) — confirmed by the unit's new
tests and re-run below.

### 2.2 Artifact verification vs. real attempt-1 artifacts — PASS (structure/content), with MINOR-1

The verifier's assumptions were checked against the committed attempt-1 inventory capture (the same bytes from
TASL-7) — not just against the report's prose:

| Check | Real attempt-1 value | Verdict |
|---|---|---|
| four `EVIDENCE/<base>/final/manifest.json` shas | `5ee8842a…`, `9d7b333d…`, `0381f73a…`, `9e1d5f08…` = report §5 / inventory `SHA256SUMS` | match |
| schema / label / family | `trackp_run_manifest/v1` / `EVIDENCE` / `kev`,`kev`,`qwen_control`,`qwen_control` (4 bases) | match |
| `model_files_sha256` | 4 entries: `adapter/README.md`, `adapter/adapter_config.json`, `adapter/adapter_model.safetensors`, `heads.safetensors` | match |
| `final/saved/manifest.json["files"]` == `model_files_sha256` | true for all four bases | match |
| identity metadata cross-checked by code | paper `b9ad6f8f…`, harness `897d83c8…`, boot `2c9bb104-…`, driver `580.178.04` | match |
| archive path | `<attempt1-root>/../../backups/p3a_attempt1_final_saved_20261117T0015Z.tar.gz`; TASL-7 `/home/dowling/r1_trackp/backups/…`, same on TASL-2, sha `fa2437ee52d8…` | match (backup report) |
| TASL-2 lease copy | `<attempt1-root>/../_attempt1_gpu_lease_log.jsonl` = `/home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl`, sha `69505091…`; live TASL-2 log is a different log (193 lines, `edc8247b…`) | match (backup report) |

The verifier (`verify_attempt1_manifest` at `:1067`, `verify_attempt1_archive` at `:1149`,
`verify_attempt1_lease_log` at `:1160`, orchestrator `verify_attempt1_artifacts` at `:1185`) rejects:
missing/symlinked leaf files, wrong schema/label/family, non-string or
empty `model_files_sha256`, unsafe (absolute/`..`) recorded paths, saved-manifest disagreement, extra/unrecorded
files in `final/saved`, and present-and-different identity metadata; it re-hashes every listed file and records
manifest/file hashes. The current boot id is required non-empty (`:1193-1194`) and recorded in `pins.boot_id`,
`pins.attempt1_artifacts`, and `campaign_start` (`:1390-1401`, `:1581-1587`). The old equality function is removed;
the only remaining attempt-1 boot-id comparisons are provenance/disclosure (`:1214`, `:1585`) and
attempt-1-journal↔attempt-1-manifest consistency (`:1126`) — no current-vs-attempt-1 gate.

### 2.3 MAJOR-1 — TASL-2 acceptance is not actually delivered: the attempt-1 **provenance** path still hard-wires TASL-7's live lease log

`run_probes_only_campaign` (`:1605-1612`) calls, after the preflight:

```
provenance = build_attempt1_provenance(args.attempt1_root)
assert_attempt1_pins(provenance)
```

but `build_attempt1_provenance` (`:1232-1250`) still hard-codes the TASL-7 path:

```
1241:    lease_log = root.parent / "gpu_lease_log.jsonl"
1244:    facts.update({"lease_log": str(lease_log), "lease_log_sha256": sha256_file(lease_log), ...
```

and `assert_attempt1_pins` (`:1288-1296`) requires `lease_log_sha256 == 69505091…`. On TASL-2,
`<attempt1-root>/../gpu_lease_log.jsonl` is **TASL-2's live global log** (different log, sha `edc8247b…`,
per `TRACKP_TASL7_BACKUP_20261117.md`), while the attempt-1 log was staged as
`_attempt1_gpu_lease_log.jsonl` (sha `69505091…`). `snapshot_attempt1_lease_log` (`:1253-1267`, `source =
Path(provenance["lease_log"])`, called at `:1642`) would likewise snapshot the wrong log if the assert were relaxed.

Runtime demonstration (synthetic TASL-2-shaped tree: attempt-1 copy `_attempt1_gpu_lease_log.jsonl` with the pinned
bytes, live `gpu_lease_log.jsonl` different; expected hashes monkeypatched as the unit's own tests do; no host
contact):

```
PASS verify_attempt1_artifacts: lease path = .../runs/_attempt1_gpu_lease_log.jsonl
build_attempt1_provenance lease path = .../runs/gpu_lease_log.jsonl
build_attempt1_provenance lease sha  = 86f65226…        # the live TASL-2 log, not the attempt-1 copy
STOP in assert_attempt1_pins: attempt-1 lease_log_sha256 '86f65226…' != reviewed 'cfd0a49e…'
```

So on a real TASL-2 the new preflight would pass, then the campaign would STOP at `assert_attempt1_pins` **before
creating the attempt-2 root**, i.e. the authorised TASL-2 fallback (`R1-TRACKP-D2` / `R1-TRACKP-TASL2-HOST`) does
not work and the unit is effectively TASL-7-only. It fails closed (no GPU/root/marker risk), but it is a functional
defect against the unit's purpose, and the record is inaccurate/incomplete about it: §1.1 presents per-host lease
discovery, §2 lists "the read-only lease-log snapshot" as merely "unchanged", and §7 does not disclose that the
provenance/snapshot path remains TASL-7-specific. TASL-7 execution is unaffected.

**Required fix:** make `build_attempt1_provenance`/`snapshot_attempt1_lease_log` use the host-aware lease-log
discovery (TASL-7 `gpu_lease_log.jsonl`; TASL-2 `_attempt1_gpu_lease_log.jsonl`, sha-pinned), e.g. by passing
`profile`/the verified `pins["attempt1_artifacts"]["lease_log"]` through `run_probes_only_campaign`, then update the
unit record (§1.1/§2/§7) and add the missing test (§3.3). A TASL-2 run must end-to-end either pass the preflight
and provenance/assert/snapshot, or fail loudly for the right reason.

### 2.4 MINOR-2 — symlink refusal is leaf-only

`_require_plain_file` (`:1057-1064`) rejects a symlink at the leaf, and `final/saved` itself is checked
(`:1091-1092`), but intermediate directory symlinks are not checked: a symlinked `EVIDENCE/<base>/final`,
`EVIDENCE/<base>`, `journal.jsonl` target (`attempt1_journal_facts`, `:1031-1032` only does `is_file()`), or the
`backups/`/`runs/` parents are followed. A symlinked `final` pointing at a self-consistent copy therefore passes
`verify_attempt1_artifacts`, contradicting report §1.2(d) "refuses symlinks". Defence-in-depth only (tampering
requires write access to the attempt-1 tree); recommend `realpath`/ancestor checks, or narrow the report claim.

### 2.5 MINOR-1 — the four `final/manifest.json` files are not compared to their recorded sha256

`verify_attempt1_artifacts` records each `manifest_sha256` (`:1136-1140`) but never compares it to a pin; the
`model_files_sha256`/`saved.files` chain authenticates each other, and the `git`/`tasl7_driver` identity
cross-checks are skipped when a field is absent (`:1119-1135`, "Fields that are absent are tolerated"). A
self-consistent swap of a final+saved manifest and its listed saved files (or a manifest stripped of identity
fields) passes verification, so a partial/tampered copy cannot be detected. The four manifest shas and the four
saved-manifest shas are recorded in the committed inventory and in report §5; pinning them (and requiring, not
tolerating, the identity fields) would close this. Report §5 discloses the choice and offers it "if the reviewer
requires it" — the PLAN text ("the four `final/manifest.json` and the files they list") does not spell out manifest
hashes, so I do not treat this as MAJOR, but it should be pinned or explicitly dispositioned by the author.

## 3. Tests (review item 4) — PASS on the claimed numbers; MINOR-3 coverage gap

Re-ran the claimed command in the D2 worktree (CPU venv, no GPU/model/host; `PYTHONDONTWRITEBYTECODE=1`,
`-p no:cacheprovider`):

```
cd .claude-worktrees/trackp-p3a-d2-20261119
../_harness_venv/bin/python -m pytest -q -p no:cacheprovider \
  r1/tests/test_trackp_p3a_guarded.py r1/tests/test_trackp_p3a_probes_only.py
=> 5 failed, 56 passed, 2 skipped   (C2/D2)

cd .claude-worktrees/trackp-p3a-code-20261116   # base D worktree, HEAD = 8662e359, clean
=> 5 failed, 49 passed, 2 skipped   (D)
```

The five failures are **exactly the same test ids on both revisions**:
`test_trackp_p3a_guarded.py::{test_real_subprocess_accepts_only_complete_unit,
test_partial_report_without_manifest_is_not_complete, test_deadline_stops_real_fake_process,
test_timeout_terminates_fake_descendant}` and
`test_trackp_p3a_probes_only.py::test_golden_field_order_from_the_pinned_renderers` — all
`ModuleNotFoundError: No module named 'torch'` (pre-existing environment limitation; identical on D). The +7 net
passes vs D are the new host/artifact tests; no unit regression. Report §3's claim (56/5/2 vs 49/5/2) is accurate.

Adjacent claims re-checked on both revisions:

```
r1/tests/test_trackp_gpu_budget_safety.py      D2: 6 failed, 3 passed; D: 6 failed, 3 passed (same ids)
r1/tests/test_trackp_p3a_a3_short.py           both: collection error (imports torch); file untouched by C2
```

New coverage reviewed: both accepted hosts and their distinct driver/freeze pins; unknown host; wrong driver per
host; TASL-2 preflight acceptance; current boot id recorded and a **different** boot accepted; artifact
good/bad journal, listed saved file, missing manifest, archive, lease log; TASL-2 `_attempt1_gpu_lease_log.jsonl`
discovery; leaf-symlink refusal; artifact record reaching `campaign_start`; campaign with a non-attempt-1 boot.

### MINOR-3 — the tests could not catch MAJOR-1

The end-to-end campaign tests stub the preflight and the provenance pin
(`r1/tests/test_trackp_p3a_probes_only.py:1218-1220`), and the only TASL-2-shaped test calls
`verify_attempt1_artifacts` in isolation (`test_attempt1_artifacts_accept_the_tasl2_lease_log_copy_path`). There is
no test in which a TASL-2 attempt-1 root (attempt-1 copy + a *different* live `gpu_lease_log.jsonl`) walks the
`verify_probes_only_pins → build_attempt1_provenance → assert_attempt1_pins → snapshot` path. Also untested:
wrong manifest schema/family/evidence_label, saved-manifest disagreement, unsafe recorded path, unrecorded extra
saved file. Add these with the MAJOR-1 fix.

## 4. Delivery identity (review item 3) — PASS (operator must check out detached)

- `git rev-list --parents -n 1 f95eb8e4` = `f95eb8e4 8662e359` (single parent = D);
  `git rev-list --parents -n 1 246ed88b` = `246ed88b f95eb8e4` (single parent = C2). No merge commits.
- `git diff f95eb8e4 246ed88b` is exactly one removed and one added line, and the added line is the canonical
  template `PIN_LINE_TEMPLATE.format(C2)`; taking C2's runner text and substituting that line reproduces D2's
  runner blob **byte-for-byte** (`0f9b76d4191093a66159cc4e468ee7cc926ba869abd7ec4d12f180d1f284620f`). D2 differs
  from C2 in no other file (docs/tests identical shas, §0).
- Unchanged acceptance logic confirmed by AST (paper-head/executing rules untouched). Executed in the D2 worktree
  against the real repo:
  `verify_paper_head({"commit": D2, "branch": "HEAD"}) -> kind "delivery_pin_child"`;
  `verify_paper_head({"commit": D2, "branch": "trackp-p3a-d2-20261119"}) -> TrackPStop` (branch not accepted).
  So D2 is accepted as the mechanical delivery-pin child of C2 **only as a detached HEAD**; `EXPECTED_PAPER_BRANCH`
  and `EXECUTING_FILES` are unchanged. Operator condition: deliver/check out **D2 detached** (as the 17 Nov TASL-2
  D delivery did); do not run on `trackp-p3a-d2-20261119` (see MINOR-4).

## 5. Docs (review item 5) — mostly accurate; MINOR-4

Read in full: `docs/r1/reports/TRACKP_P3A_D2_CODE_UNIT_20261119.md` and the §7 addendum of
`docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md`.

Verified accurate against independent data: authority citation (`R1-TRACKP-D2` on published `main` `de3de54f`);
canonical commits; "only the host contract" scope; host/driver/freeze-pin table (freeze byte-identical, sha
`50238e5a…`); artifact schema/paths/recorded hashes (§5 table matches the inventory `SHA256SUMS`, including the
qwen3.5-4b-base model-file hashes `d1502e5c…/3b31604a…/0b39d3fa…/aeea9ec1…`); TASL-2 lease-copy path and live-log
distinction; boot-id removal and disclosure fields; test numbers (56/5/2 vs 49/5/2, same torch failures);
"uncommitted, no host/GPU/push" claims; §7 limits (no host execution, first preflight I/O cost, TASL-2 freeze
substitute, detached HEAD, one host per table).

### MINOR-4 — doc traceability / operator wording

- The cited 17 Nov basis reports and the attempt-1 inventory are **not** on published `main` and **not** in the D2
  branch; they live on `ops-tasl-20261116` (the PLAN row names that branch, so the citation is legitimate, but the
  unit record should state it, and "the committed attempt-1 inventory" reads as if it were in the delivery tree).
- §7 says the operator may check out D2 "detached … **or on the accepted branch name**": D2 exists only on branch
  `trackp-p3a-d2-20261119`, which `verify_paper_head` rejects (verified above). The record should say plainly that
  **detached HEAD is the only accepted form for D2**.
- The C2/D2 shas do not appear in the unit record (they cannot); the delivery record (`R1-TRACKP-UNITB` amendment /
  ops delivery report) must carry `C2 = f95eb8e4…`, `D2 = 246ed88b…` and the D2 runner sha, or the pin children are
  unreferenced.

## 6. What was not checked / limits

- No TASL-7/TASL-2 contact, no GPU, no model, no evidence root; therefore the real 313 M archive and ~350 M
  attempt-1 model files were not hashed here. Artifact-verifier behaviour on synthetic trees was exercised with
  monkeypatched expected hashes (as the unit's own tests do); the real recorded hashes and paths were validated
  against the committed 17 Nov reports/inventory only.
- Review was read-only; the D2 worktree stayed clean at `246ed88b…` before and after.

## 7. Verdict

**NOT ACCEPTED — 0 BLOCKING, 1 MAJOR, 4 MINOR.**

| # | Severity | Finding | Location |
|---|---|---|---|
| MAJOR-1 | MAJOR | TASL-2 campaign STOPs at `assert_attempt1_pins`: `build_attempt1_provenance` (and hence the BLOCKING-1 snapshot source) still hard-wires the TASL-7 live `gpu_lease_log.jsonl` instead of the host-discovered attempt-1 log (`_attempt1_gpu_lease_log.jsonl`, sha `69505091…`); TASL-2 fallback is not delivered and the record does not disclose it | `r1/scripts/trackp_p3a_guarded.py:1241-1244`, `:1262`, `:1288-1296`, `:1611-1612`, `:1642` |
| MINOR-1 | MINOR | four `final/manifest.json` (and saved-manifest) bytes recorded but not pinned; self-consistent manifest/saved-file swap passes; absent identity fields tolerated (report §5 discloses; pin or disposition) | `:1067-1141`, `:1119-1135` |
| MINOR-2 | MINOR | symlink refusal is leaf-only; symlinked `final`/`EVIDENCE`/journal/archive parents followed (report claims "refuses symlinks") | `:1057-1064`, `:1031-1032`, `:1091-1092`, `:1114-1116` |
| MINOR-3 | MINOR | no TASL-2 end-to-end campaign test; e2e stubs provenance pin; several artifact negative cases untested (this let MAJOR-1 escape) | `r1/tests/test_trackp_p3a_probes_only.py:1218-1220` |
| MINOR-4 | MINOR | basis reports on ops branch not flagged; §7 branch-name wording wrong for D2 (detached is the only accepted form); delivery record must carry C2/D2 shas | report §7 |

**Conditions for acceptance (fix and re-review):**

1. **MAJOR-1:** make attempt-1 provenance and the BLOCKING-1 snapshot use the host-aware lease-log discovery (or
   the verified `pins["attempt1_artifacts"]["lease_log"]` path/sha), so a TASL-2 run passes preflight → provenance →
   assert → snapshot; update the unit record (§1.1/§2/§7) to state this; add the TASL-2 end-to-end test (attempt-1
   copy present, live TASL-2 log different) plus the missing artifact negatives.
2. Re-run the claimed CPU suite and confirm no new failures vs D.
3. Non-blocking: address MINOR-1 (pin manifest hashes or record an explicit author disposition), MINOR-2, MINOR-3,
   MINOR-4.
4. Operator/delivery conditions: run D2 **detached** (never on `trackp-p3a-d2-20261119`); one host per table named
   in the run report; `R1-TRACKP-UNITB` amended to name D2; ops delivery record records `C2`/`D2` shas.

Until MAJOR-1 is fixed, D2 may be used on TASL-7 only; it must not be represented as TASL-2-capable.
