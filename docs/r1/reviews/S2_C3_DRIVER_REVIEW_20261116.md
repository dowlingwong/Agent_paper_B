# Independent review — S2-C3 TASL-independent declared-input replay driver (R1-S2C3-DRIVER)

Review date: 16 Nov 2026. Reviewer: independent read-only review (no execution of the 3 jobs).
Target: branch `s2c3-driver-20261116` @ `c545852c7083559a0eccdf7da86ad34ecdc8070a` (worktree
`.claude-worktrees/s2c3-driver-20261116`, clean, equals `origin/s2c3-driver-20261116`).
Authority: `origin/author-decisions-20261116b` @ `025bfc16477a3911ea461d7a6cfc85f3ea523d66`, rows
**R1-S2C3-DRIVER**, **R1-SWEEP-HOST-HTC**, **R1-SWEEP2-SETTINGS**, **R1-SWEEP2-LAYOUT**.
Scope of this review: code/doc/test inspection plus the local, no-run reproductions below. **No HTCondor job was
submitted, no llama-server was started, no label was read.** The only writes were this review file.

## 0. Summary

**VERDICT: NOT ACCEPTED** — one deterministic blocker in the real campaign path (findings §8 B1). The declared-input
and shim-sha engineering is otherwise strong: 161 tests pass, the local audit is clean (25/25, 0 failures), the JDL and
all 37 staged transfer inputs reproduce byte-identically from committed code, the six comparison criteria implement the
author-accepted corrected numbers (20/33/20 ±10 %, 0/240, final_y table), and the shim is genuinely additions-only with
byte-pinned patched sources. However, the shim relocates the Stage A tables **only** for the `author_gate` digest check;
the same tables are read from the same TASL-absolute config paths by `r1/scripts/exam_runner.py:stage_a_pass_set`,
which the B2 root campaign calls on every root through `authorized_b1_observer → _authorized_candidate` because the
committed registry's `gemma4_31b.runtime.footprint_mib` is `TODO_VERIFY_ON_HOST`. The driver's preflight probes only
four gates and does not exercise that call, so preflight would **PASS**, the model would be fetched and the server
started, and then root 1 of every one of the 3 jobs would raise `FileNotFoundError` and STOP. Also: the committed
JDL/specs/README still carry the pre-32k (stale 16k) resource numbers, not the author-accepted 32k layout, and the
"nothing is fetched at run time / self-contained" claim is incorrect (three pinned network fetches per job).

## 1. What was run / reproduced (read-only, no job)

| check | command | result |
|---|---|---|
| test suite | `.venv-test/bin/python -m pytest r1/tests/htcondor/ -q` | **161 passed** (132 pre-existing + 29 driver tests collected) |
| declared-input audit | `python sweep2/s2_c3_replay.py audit sweep2/spec.replay.example.json` | 25 items, **0 failures**, 22 verified locally + 5 deferred (3 harness trees, 2 installed-cache digests), binding recomputed `c502a9aa…` |
| JDL/staging reproduction | `python sweep2/render_jdl.py sweep2/spec.replay.example.json --out … --stage-dir …` | committed JDL **byte-identical**; **37** staged files, all byte-identical to `sweep2/dryrun/replay/` |
| compare expected sources | `s2_c3_compare.verify_expected_sources()` | criteria sha `63bd0a9b…`; derived totals trials 240 / invalid 20 / duplicates 33 / noops 20 / parse_failed 0 / queries 240 / query_failed 0; all 12 embedded final_y match the pinned manifests |
| declared file shas | `sha256sum` of the 4 TASL-only copies + 8 file items | all equal the manifest (Stage A t7h8 `00ab143d…`, t7j10 `7152512…`, prompts `70872a77…`, cache archive `f51c3c32…`) |
| paper blobs | `git show 8709dce7:<path>` vs declared | all 9 match (PLAN `1f6c4132…` is the pinned B2 PLAN, not the decisions branch) |
| OpenML cache | extract archive; recompute per-file/tree digests | credit-approval tree `702a0b3c…`, ionosphere `65dfc44c…`; all 8 files match; the same per-file shas were independently found in the local Mac harness copy |
| shim shape | `git apply --numstat` | `r1/exam/campaign.py` +2/0, `r1/exam/runtime.py` +56/0 → **58 additions, 0 removals, 3 hunks** (as claimed) |
| patched sources | apply label then shim to `git show 8709dce7` copies | campaign `014b1a8a…` → (label) `33feb320…` → (both) **`d9d8b5a0…`**; runtime `ce50194e…` → **`2c5883f2…`**; both equal `PATCHED_SOURCE_SHA256` |
| pinned roots | `shasum -c` of `c3_replay_inputs/SHA256SUMS` | 24/24 OK; 12 EVIDENCE/COMPLETE b2/off manifests, final audit seeds start 9201, no 7001–7010 anywhere |

## 2. Authority correspondence (R1-S2C3-DRIVER etc.)

* Authority text (16 Nov, 11:41 CET) authorises exactly: an independently reviewed, **fully declared-input**,
  **TASL-independent** ENGINEERING replay driver for the S2-C3 L40S deployment check; inputs declared item-by-item with
  sha; ENGINEERING_ONLY; **no B.2 audit**; **no 7001–7010**; criterion 3 corrected pre-data to 20/33/20 (±10 %) over
  the 12 thinking-off roots and parse failure 0/240.
* Implemented accordingly: 25 declared items; ENGINEERING_ONLY + `replay_marker = s2_c3_replay/v1`; no B.2 path is
  invoked; audit seeds pinned to `[9201..9210]` and 7001–7010 refused in spec, manifest validation, `_scan_forbidden_seeds`
  and the comparison; criterion 3 applied as corrected (`s2_c3_compare.py`), original 58/82/58 retained only for
  transparency; the correction is pre-data (manifest totals computed from pinned inputs match exactly).
* R1-SWEEP2-SETTINGS (1): server is pinned to ctx 32768, `-ngl 999 -np 1`, `--jinja`, thinking off, q8_0 K/V,
  `cache_prompt` false (`LLAMACPP_CACHE_PROMPT`/`LLAMACACHE_PROMPT` popped); non-numeric `--no-webui`/`-lv 4` recorded.
* R1-SWEEP-HOST-HTC: 3 HTCondor jobs, L40S/NEMO2/CPU-class requirements, one table one host class, no `/ceph` write
  from the job (operator seal).
* **R1-SWEEP2-LAYOUT not honoured** — see M1: the branch is based on `2b454c33`, which predates the accepted 32k
  layout (`sweep2-main-20261116` @ `9a79cfe0`: `walltime_s 12203`, `request_disk_kb 42460977`,
  `request_memory_mb 32000`). The committed C3 JDL/specs/README/tests still carry `7200 / 50000000 / 128000`.
* Over/under-claim: over — "nothing is fetched at run time"/"self-contained"/"no network data" (M2); "the exact set
  the un-shimmed probe reports" is a gate-name allow-list screen, not set equality (m4). Under — the missed Stage A
  reader (B1) is not disclosed; the run-time network prerequisites are not disclosed; the physical GPU UUID is
  intentionally rebound from the authorization's TASL GPU to the L40S class but the doc only says "physical host"
  (m1/O3).
* The authority row is not an ancestor of the branch (`025bfc16` diverges from main `9ae6d877`); the in-tree PLAN is
  the B2-bound `8709dce7` PLAN. Citing the external decisions commit is acceptable for the run (it is not a run input),
  but the branch alone cannot show its mandate (m6).

## 3. Skill/security review of the reviewed shim

Verified positives:

1. **Additions only, exact targets/anchors.** `sweep2/s2_c3_driver_shim.diff`: 58 added lines, 0 removed, 3 hunks;
   only `r1/exam/runtime.py` (+56) and `r1/exam/campaign.py` (+2). `check_shim_scope` enforces files, no-rename,
   no-removal, the three anchor headers (`read_registry`, `_committed_b1_authority`, `require_worker_host`) and screens
   every added code line against trial/manager/scoring/audit terms. The driver re-checks the diff sha (`571456b6…`)
   and both resulting source shas (`2c5883f2…`, `d9d8b5a0…`; independently reproduced from the pinned commit).
2. **Inert without the switch.** `_s2c3_declared()` returns `None` unless `R1_S2C3_DECLARED_INPUTS` is set; then the
   original dryrun/production `host_check`, the original `require_worker_host`, and the original Stage A paths are used
   unchanged (tested). The patch exists only in the detached sandbox worktree and is shadow-executed; the pinned
   authorization checkout stays clean (`git status --porcelain --untracked-files=all` empty before/after).
3. **Only three hooks.** (a) `host_check` early replay branch; (b) one relocation call in the
   `_committed_b1_authority` digest loop; (c) `require_worker_host` early replay branch. No trial, manager, scoring,
   audit, ledger or manifest line is added/replaced. The reproduced patched-source bytes are the reviewed bytes.
4. **Fail-closed switch.** Missing/bad manifest, absent root/sandbox env, TASL host, out escaping the sandbox, or a
   declared copy whose sha differs from `cfg[..._sha256]` all raise STOP; they cannot silently fall back to the TASL
   path or to a non-TASL host. A copy cannot differ in content because the same B2-bound sha256 is re-checked.
5. **Authorization gates still run.** With the switch set, `_verify_b1_worker_input`/`author_gate` still check committed
   config bytes, committed note bytes, PLAN rows, rule and B1-analysis digests, registry, seeds/workers/cap/node/host/GPU
   bindings and `authorization_checkout_head`; the B2 configuration binding `c502a9aa…` still recomputes and both
   `out`/`base_url` are non-binding.

**BLOCKER B1 — the shim relocates the Stage A tables for only one of the two code sites that read them.** The pinned B2
root campaign path is:

`r1/exam/campaign.py:262` `with authorized_b1_observer(job), preservation:` →
`r1/exam/observer.py:76-77` `read_registry(cfg['registry']); _authorized_candidate(job,cfg,registry)` →
`r1/exam/observer.py:29-30` `if placeholders(runtime.get('footprint_mib')): eligible=stage_a_pass_set(cfg,…,v2=True)`
(the committed registry has `gemma4_31b.runtime.footprint_mib = "TODO_VERIFY_ON_HOST"`, `r1/exam/registry.yaml:187`, so
this branch is always taken for this candidate) →
`r1/scripts/exam_runner.py:270-271` `digest_file(cfg['stage_a_table'])` then `json.loads(Path(cfg['stage_a_table']))`,
and `:276-277` `_repo_path(cfg['stage_a_amendment_table'])` + digest. `cfg['stage_a_table']` is the TASL-absolute
`/home/dowling/exam-x/work/r1_stagea_20261103_t7h8/stage_a_table.json` and the amendment path is the TASL-absolute
t7j10 path (`exam_b2_v2.json`). Those paths do not exist off TASL, and `stage_a_pass_set` is in
`r1/scripts/exam_runner.py`, which the shim does **not** touch (`sweep2/s2_c3_driver_shim.diff` contains no
`stage_a_pass_set`/`exam_runner` reference; the only relocation call is
`sweep2/s2_c3_driver_shim.diff:85` inside `_committed_b1_authority`). Therefore every root campaign raises
`FileNotFoundError` (or the `PreparationStop` on the amendment path) at `authorized_b1_observer.__enter__`, before any
trial runs. The driver's gate probe exercises only four gates
(`sweep2/s2_c3_replay.py:1072-1081`: `verify_b1_worker_input`, `host_check`, `require_worker_host`,
`harness_binding`), not `_authorized_candidate`/`stage_a_pass_set`; so the two-phase preflight would report PASS, fetch
the 19.6 GB model, start the server, and then STOP at root 1 in **all three jobs**. (The same is true of the operator
`preflight` CLI.) This is a deterministic blocker, not an unverified risk, and it also makes the unit's claim that the
preflight covers "the exact B2 authorization gates the campaign calls" an over-claim.

Additional (non-blocking) semantic observations about the same shim:

* Replay-mode `host_check` also skips the production `R1_DRYRUN`/`R1_FAKE_OLLAMA_ROOT`/`R1_EXAM_DRYRUN` refusal and the
  author disk-floor `space_check(models_dir/work_dir)` (100 GB) that the original branch runs. Neither affects numerics,
  the job env does not set those variables, and the failure modes are STOPs, but the bypass table does not disclose
  them (m1).
* `require_worker_host` in replay returns the actual node and no longer compares it to `job['host']`; the recorded host
  binding is still enforced (`job['host'] == cfg['host']` and the authorization note's host/GPU), while the physical
  host/GPU are deliberately rebound to the L40S class. This is within the authority row but should be stated explicitly
  (m1/O3).
* No plausible way to set the env wrongly produces a silent run: a wrong/missing manifest path raises (JSON error / STOP),
  and a manifest from another run can only relocate to bytes that still must equal the B2-bound sha. The switch is
  scoped to the shadow-executed patched modules only, so other phases cannot see it.

## 4. Declared inputs (25 items)

* 25 items: 9 `paper_blob`, 8 `file`, 3 `harness_tree`, 2 `staged_tree`, 3 `value`. All have a path/identity, sha256 or
  tree digest, provenance and consumer; no undeclared input is needed.
* TASL-only material (Stage A t7h8/t7j10, Stage A prompts, OpenML archive) is copied read-only once and shipped with
  `sweep2/s2_c3_inputs/PROVENANCE.json`; the copy shas equal the values `exam_b2_v2.json` (and the B2 authorization note)
  already bind for tables/prompts, so relocation cannot change what the authorization approves. The OpenML archive
  extracts deterministically to the declared per-file/tree identities; per-file shas match both the B2 run-root copies
  (as recorded in provenance) and the independent local harness copy. The archive install target
  `experiments/r1/pilot/L8_20261009T152916Z/nodes/<node>/data_cache` is exactly the path `_collect_b1_review` copies
  from, and the driver requires it to be gitignored and the harness clone to stay clean (cheap fail-safe).
* The 5 deferred-to-job-start items are genuinely verifiable inside the job: the 3 harness trees via
  `git ls-tree -r a3fedbb` in the cloned pinned harness, and the 2 cache trees after extraction/install. The audit
  correctly lists them as deferred rather than claiming local verification.
* **Run-time network:** the job does fetch (i) the paper repo at `8709dce7`, (ii) the harness repo at `a3fedbb`, and
  (iii) the 19.6 GB GGUF from HuggingFace (after preflight), and it verifies commits/sha of each. Nothing is fetched
  from TASL, and no TASL path is read on the campaign path after B1 is fixed (the only remaining absolute TASL values
  in `authority_config` — prompts, server binary, models/work dirs — are not read by the `campaign.main` path; I
  re-checked the call graph). But the driver doc's "nothing is fetched at run time"/"self-contained"/"no network data"
  wording is factually wrong (M2), and the 3×19.6 GB egress + GitHub/HF availability are run-time preconditions.
* No labels, no B.2 audit data, no secret material is copied; the only copied TASL material is authorization-bound
  Stage A/OpenML input data.

## 5. Run path, labels, transfer/seal

* 3 jobs × 4 roots/node; one owned server per job; `out`/`base_url` rewrite only (canonical-form check, exactly two
  differing lines with those keys; originals re-verified); binding recomputed by the B2 method and unchanged by the
  rewrite; label patch applied separately before the shim in a detached worktree; ENGINEERING_ONLY + replay marker
  required on every manifest; audit seeds exactly 9201–9210; 7001–7010 refused everywhere; STOP-and-persist on every
  refusal with tars/sums written; transfer outputs/seal are the C2 pattern and the seal additionally binds the shim sha,
  declared-inputs manifest sha and `items_verified == items_declared`.
* Preflight is implemented twice (unshimmed refusals screened against a gate allow-list; shimmed four gates must all
  pass) and the model is fetched only after preflight — but because of B1 the preflight does not cover the gate that
  deterministically fails, so this ordering does not protect the run.
* Criterion comparison: criterion 1 |Δ|≤0.02 / mean≤0.01; criterion 2 parse_failed/forecast_queries ≤0.02 against
  240 queries (B2 0/240); criterion 3 ±10 % of 20/33/20; criterion 4 61/61 full offload; criterion 5 total root wall
  ≤ 2× B2 GPU time (0.504917 h); criterion 6 all roots rc 0 with complete manifests. Matches the criteria document and
  the authority row. (Note: the row's "parse failure 0/240" is implemented as the pre-declared ≤2 % rate against the
  corrected 240 denominator; the B2 reference value is 0/240 — consistent with the criteria document.)

## 6. Tests / reproducibility

161/161 pass; the 29 driver tests cover declared-input audit/STOP persistence, cache determinism/traversal/gitignore,
shim additions-only + anchor/forbidden screening, patch application and patched-source pins, shim inertness, TASL
refusal, sandbox escape, relocation sha failure, spec mutation, seal bindings. The gaps are the real call graph:
`stage_a_pass_set`/`authorized_b1_observer` are not exercised, and no test would have caught B1. JDL and the 37 staged
inputs reproduce exactly; `condor_submit` is not installed here, so the ad remains operator work (as documented).

## 7. Run-safety in the real image (independent of B1)

* Proven by the S2-C4 real run with the same image digest/model: clone-at-commit, GGUF fetch (81.8 s), L40S detection,
  `-np 1`/61/61 offload, CPU class and 16-CPU container all work; `/opt/r1/envs/harness/bin/python` has the needed deps.
* Persistent risks to watch: GitHub/HF availability and 3×19.6 GB model egress; 50 GB disk request vs ~30 GB measured
  S2-C4 peak (fits); 128 GB memory request (over-provisioned); 7200 s walltime vs the accepted 12,203 s (the C3 job is
  ~4 roots, far below a full 18-instance chunk, so likely ample, but the driver's per-root timeout derives from it:
  `walltime-600` = 6600 s); a root >6600 s would STOP. The criteria are stochastic replays, so even a correct stack can
  legimitately land NOT PASS (especially criterion 3 duplicates 33 ± 3.3) — that is pre-declared, not a driver defect.
* The remaining author gate (sweep-2/EVIDENCE) precedes submission; this review does not authorise it.

## 8. Findings

**B1 (blocker).** The reviewed shim does not relocate the two Stage A tables for `r1/scripts/exam_runner.py:stage_a_pass_set`
(called on every B2 root via `authorized_b1_observer → _authorized_candidate`, because the committed registry's
`gemma4_31b.runtime.footprint_mib` is `TODO_VERIFY_ON_HOST`). The call reads the TASL-absolute
`cfg['stage_a_table']`/`cfg['stage_a_amendment_table']` directly, which do not exist off TASL, so every root campaign
raises before any trial. The preflight's four-gate probe does not exercise this path, so the driver (and the operator
`preflight` CLI) would PASS preflight, fetch the model, start the server, and then STOP at root 1 in all 3 jobs; P4
cannot be produced. Fix requires a re-reviewed shim extension (additions-only hunk in `r1/scripts/exam_runner.py`, or an
equivalent reviewed accessor) covering both Stage A reads, a new patched-source sha pin/targets in the driver and spec,
and a fifth preflight gate that exercises `_authorized_candidate`/`stage_a_pass_set` so a missing relocation fails
closed; then re-render and re-run the local checks. (This also fixes the unit's "pre-flights the exact B2 authorization
gates the campaign calls" over-claim.)

**M1 (major).** Stale pre-32k transfer layout in committed run artifacts. `sweep2/render_jdl.py:60-61` hard-codes
`request_memory = 128000` and `request_disk = 50000000`; `sweep2/render_jdl.py` emits `+RequestWalltime` from
`spec['walltime_s']`, which is `7200` in all three replay specs (`sweep2/spec.replay*.json:134`) and in the staged
`s2_c3_spec.json`; the committed JDL (`sweep2/dryrun/replay/s2_c3_replay_job.jdl:10-13`) and README (`:24`) advertise
those values, and `r1/tests/htcondor/test_s2_c3_replay.py:790` pins them. The author-accepted 32k layout
(R1-SWEEP2-LAYOUT, same authority commit; measured in `sweep2-main-20261116` @ `f172d299`/`9a79cfe0`) is
`walltime 12,203 s`, `request_disk 42,460,977 kB`, `request_memory 32,000 MB`. Merge/port that layout
(`9a79cfe0`: spec-driven `request_disk_kb`/`request_memory_mb`, spec `walltime_s 12203`) or explicitly justify a
C3-specific set before the operator dry-run; the under-requested walltime is the risky direction.

**M2 (major, documentation).** `S2_C3_DRIVER.md:35` ("nothing is assumed or fetched at run time"), `:71`
("self-contained"), `:216` (reviewer checklist "no network data") are false: each job clones the paper repo
(`prepare_authorization_checkout` → `lib.clone_at`), clones the harness (`lib.clone_at`), and fetches the 19.6 GB GGUF
(`lib.fetch_model`) at run time. Identity is commit/sha-pinned and no TASL mount is needed, so the declared-input intent
is met — but reword to "three pinned network artifacts are fetched and identity-verified; no *unpinned* data and no
TASL access", and disclose the network/egress precondition.

**m1 (minor).** The replay `host_check` branch additionally bypasses the production dryrun-env refusal
(`R1_DRYRUN`/`R1_FAKE_OLLAMA_ROOT`/`R1_EXAM_DRYRUN`) and the author disk-floor `space_check` on `models_dir`/`work_dir`;
the physical host/GPU are rebound from the authorization's TASL-7/GUID to the L40S class while the recorded job host is
still TASL-7. None affects numerics; disclose in the bypass table.

**m2 (minor).** `job_record["server"]` drops the started server's `argv` and there is no `manager_settings` block, so
ctx 32768 / `-np 1` / q8_0 are evidenced only by the pinned spec and the transferred `llama-server.log`; record the
argv or the exam settings like S2-C2 does.

**m3 (minor).** The comparison verifies the label-patch sha but not `record["driver_shim"]["patch_sha256"]`,
`record["declared_inputs"]["manifest_sha256"]`, or `manifest.job_sha256 == out/job.json`; the seal enforces shim/declared
so the gated path is covered, but the comparison should mirror those pins (defense in depth). `seal_replay` also does
not require `status == COMPLETE` (it can seal a STOP output; harmless for retention, worth an explicit note).

**m4 (minor).** The unshimmed preflight is a gate-**name** allow-list with "at least one blocker", not "the exact set":
a subset passes, and the doc's "exact set" is stronger than the code. In practice the unshimmed probe will report
`verify_b1_worker_input`, `host_check`, `require_worker_host`, `out_under_work_dir` and the two
`authorization_input:*_table` blockers; `openml_data_cache` will not appear because the cache is installed in `prep`
before preflight, and `rule`/`stage_a_amendment_acceptance` resolve in the pinned checkout. Fail-safe, but say so.

**m5 (minor, evidence hygiene).** Evidence timestamps are in the future relative to the commits and wall clock:
`created_utc 2026-11-16T12:00:00Z` (declared manifest, PROVENANCE), `generated_utc 12:20Z`/`12:30Z` (shim scope,
declared-inputs audit, prep evidence) vs HEAD timestamp 11:02:54Z and the review clock ~11:11Z. Also
`s2_c3_prep_evidence…json` reports `items_verified_checkouts: 25` while `phases.openml_cache` is `false` and does not
persist the installed-cache `cache_report`; the installed tree identities are only in the separate `openml_cache`
block. Record real times and the full cache re-verification report.

**m6 (minor).** The author row is not an ancestor of the branch (branch base `2b454c33`; row lives at
`025bfc16` on the decisions branch, merge-base `9ae6d877`). Citing the external commit is acceptable because the row is
not a run input and the in-tree PLAN is correctly the B2-bound `8709dce7` PLAN, but a branch-only reader cannot see the
mandate; add a pointer/record.

**O1 (observation).** Pre-declared criteria 1/3 are tolerances on a *stochastic* re-run (temperature 0.2; final_y
tolerance 0.02/0.01, diagnostics ±10 % of 20/33/20 ⇒ duplicates 29.7–36.3 over 240). A correct stack can legitimately
produce NOT PASS; expect that and state it before submission (no relaxation allowed after data).

**O2 (observation).** Remaining prerequisites/risks: the author's sweep-2/EVIDENCE gate; GitHub + HF availability; 3×
19.6 GB GGUF egress; 128 GB memory / 50 GB disk requests; 7200 s walltime (see M1); 3 L40S slots and 4-roots/node
walltime; sealed `/ceph` receipt by the operator after transfer.

**O3 (observation).** The 5 deferred declared items and the four shimmed gates are verified at job start; the local
`prep` evidence cannot cover them. That is correctly disclosed; after B1 is fixed, the first real preflight is the
place to confirm the full shimmed gate walk (now including the Stage A pass-set read).

## 9. Required before re-review

1. Fix B1: extend the reviewed shim/pins to relocate both Stage A tables on the `stage_a_pass_set` read path; add it to
   the gate probe/`preflight`; add a regression test that would fail if `stage_a_pass_set` reads the TASL path; update
   `SHIM_TARGETS`/`PATCHED_SOURCE_SHA256`/specs/tests/docs and re-run the local reproductions.
2. Fix M1: port the accepted 32k layout (12,203 s / 42,460,977 kB / 32,000 MB) and re-render the JDL/specs/dry-run,
   or obtain an explicit author decision for a C3-specific layout and disclose it.
3. Fix M2 wording; add m1–m6 as appropriate.
4. Then operator `condor_submit -dry-run` for the three rendered JDLs, and only then the 3 ENGINEERING jobs (subject to
   the author's sweep-2/EVIDENCE gate).

## 10. Verdict

**VERDICT: NOT ACCEPTED** — blocker B1 (the shim does not cover the `stage_a_pass_set` Stage A read on the real
campaign path; the preflight does not exercise it, so the run would fetch the model and then STOP at root 1 in all three
jobs). Re-review after the shim/pin/preflight fix and the M1 layout correction; the rest of the declared-input, shim,
label and comparison engineering reviewed here is sound.
