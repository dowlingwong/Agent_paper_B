# Independent review (round 2) — S2-C3 TASL-independent declared-input replay driver (R1-S2C3-DRIVER)

Review date: 16 Nov 2026. Independent read-only review (fresh reviewer; no HTCondor, no llama-server, no GPU, no
job). This review verifies the **round-2 fixes** requested by
`docs/r1/reviews/S2_C3_DRIVER_REVIEW_20261116.md` (round-1 verdict NOT ACCEPTED: blocker B1; majors M1, M2; minors
m1–m6).

Target: branch `s2c3-driver-fix-20261116` @ **`3e2ebbf0a7d8b569204faf7f8a92afc5ab05319a`** (worktree
`.claude-worktrees/s2c3-driver-fix-20261116`, clean, equals HEAD; based on `s2c3-driver-20261116` @ `c545852c`).
Authority: `origin/author-decisions-20261116b` @ `025bfc16477a3911ea461d7a6cfc85f3ea523d66`, rows
**R1-S2C3-DRIVER**, **R1-SWEEP-HOST-HTC**, **R1-SWEEP2-SETTINGS**, **R1-SWEEP2-LAYOUT** (read from the decisions
branch; the review itself is not a run input). The only write of this review was this uncommitted file.

## 0. Summary

**VERDICT: ACCEPTED for the 3-job ENGINEERING run.** The round-1 blocker is fixed and independently reproduced:
the reviewed additions-only 4th shim hunk relocates **both** TASL-absolute Stage A tables inside
`r1/scripts/exam_runner.py:stage_a_pass_set`, the fifth preflight gate exercises the real
`authorized_b1_observer → _authorized_candidate → stage_a_pass_set` chain, and I reproduced, with the real pinned
clones and the committed probe, (i) the unshimmed exact TASL refusal set (including `authorized_candidate` failing on
`/home/dowling/exam-x/work/r1_stagea_20261103_t7h8/stage_a_table.json`) and (ii) all five shimmed gates passing. M1 (accepted 32k layout) and M2
(network disclosure) are fixed and reproduce; the minors are addressed. Only small non-blocking residuals remain
(evidence-timestamp inconsistency, seal wording for early STOP records, evidence generated with an intermediate
driver revision, and the inherited stale C2 dry-run snapshot); none touches the run path.

| check | command / method | result |
|---|---|---|
| test suite | `.venv-test/bin/python -m pytest r1/tests/htcondor -q` (in the worktree) | **176 passed** |
| declared-input audit | `python sweep2/s2_c3_replay.py audit sweep2/spec.replay.example.json` | 25 items, **0 failures**, 22 verified locally + 5 deferred; binding recomputed `c502a9aa…290b` |
| JDL / staging reproduction | `python sweep2/render_jdl.py sweep2/spec.replay.example.json --out … --stage-dir …` | **37** staged files, all byte-identical to `sweep2/dryrun/replay/`; committed JDL **byte-identical** |
| shim shape | `git apply --numstat`, hunk parsing | 3 files (`runtime.py` +65/0, `campaign.py` +2/0, `exam_runner.py` +5/0) = **72 added, 0 removed, 4 hunks**; sha256 `defac236…aa92` |
| patched-source pins | apply label then shim to `git show 8709dce7` copies | runtime `0cc6705e…5d3`, campaign `d9d8b5a0…c0c`, exam_runner `9acc121c…d85` — all equal `PATCHED_SOURCE_SHA256`; label-only intermediate campaign `33feb320…14c` (round-1 value) |
| gate probe, unshimmed | committed `GATE_PROBE`, real pinned clones (paper `8709dce7`, harness `a3fedbb`), no replay env | 5 gates exercised; `verify_b1_worker_input`, `host_check`, `require_worker_host`, `authorized_candidate` refuse with the reviewed TASL reasons (notably `authorized_candidate → FileNotFoundError /home/dowling/exam-x/work/r1_stagea_20261103_t7h8/stage_a_table.json`); `harness_binding` OK |
| gate probe, shimmed | same, with `R1_S2C3_{DECLARED_INPUTS,DECLARED_ROOT,SANDBOX_ROOT}` | **all five gates OK** (incl. `authorized_candidate`); probe reports exactly `PROBE_GATES` |
| fail-closed checks | negative probe runs | corrupt declared copy → `STOP: … stage_a_table sha256 mismatch`; manifest w/o `stage_a_inputs` → TASL FileNotFoundError; bad manifest schema → `STOP: … manifest is invalid` |
| inertness | patched sources loaded **without** the env switch | same TASL refusals as the unshimmed walk (switch is the only difference) |
| compare expectations | `s2_c3_compare.verify_expected_sources()` | criteria sha `63bd0a9b…`; 240 trials / invalid 20 / duplicates 33 / noops 20 / parse_failed 0; 12 final_y derived |
| worktree | `git status --porcelain -uall` | clean (before this review file) |

I did not re-run the full `prep`/`preflight` CLI (it re-clones GitHub). For the gate check I used the *committed*
`GATE_PROBE` (verified byte-identical to the probe copy in `sweep2/evidence`'s surviving sandbox
`/tmp/s2c3fix_e2e/work/gate_probe.py`) against the pinned, clean clones in that sandbox
(paper `8709dce7`, harness `a3fedbb`, patched sources matching the pins), and separately reconstructed the patched
bytes from `git show 8709dce7` + the committed label/shim. No server, model fetch or root ran.

## 1. B1 — blocker from round 1: FIXED (independently reproduced)

*The 4th hunk really covers the direct reads.* `sweep2/s2_c3_driver_shim.diff` adds, inside
`r1/scripts/exam_runner.py:stage_a_pass_set`, a 5-line block that (i) returns inert unless
`_s2c3_declared()` (i.e. `R1_S2C3_DECLARED_INPUTS`) is set, and (ii) in replay mode rebinds a **local copy** of
`cfg` so `cfg['stage_a_table']` and `cfg['stage_a_amendment_table']` are resolved through the same
`_s2c3_relocate()` used by `_committed_b1_authority` — the amendment *acceptance* is the committed repo-relative
`docs/r1/reports/OPS_O1_20261104.md` and needs no relocation. The function body's subsequent reads
(`digest_file(cfg['stage_a_table'])`, `Path(cfg['stage_a_table']).read_text()`, `_repo_path(cfg['stage_a_amendment_table'])`)
therefore all see the declared copies. I checked every `stage_a_table`/`stage_a_amendment_table` reference in the
pinned paper tree (outside tests): the only two readers on the `campaign.main → collect →
_collect_b1_review → authorized_b1_observer/_verify_b1_worker_input` path are `_committed_b1_authority` (patched in
round 1) and `stage_a_pass_set` (patched now), and both are exercised by the probe. The remaining readers are **not**
on the replay run path: `exam_runner._evidence_unreviewed` (the separate `evidence` CLI phase, not called by
`campaign.main`), `exam_dryrun.py`, `b1_batch.py`/`b2_batch.py` (batch launchers), and `stage_a.py` (prompts — the
campaign path does not read them), and the harness repo has no Stage A reference. No remaining unpatched TASL
Stage-A-table read exists on the run path.

*Inert, same sha256 check, no numeric code.* The block is additions-only and guarded by `_s2c3_declared() is not
None`; `_s2c3_relocate` re-checks `digest_file(relocated) == cfg[key+'_sha256']` (same pin the B2 config binds) and
raises STOP on mismatch. The added lines do not touch trial/manager/scoring/audit code: `git apply --numstat` gives
72/0 across the three named files, `check_shim_scope` restricts hunks to the four allow-listed anchors and screens
every added code line against `run_config|paired(|run_real_campaign|root_trials|root_events|audit_seeds|instance_seeds|final_audits|diagnostics|write_json|score|metric|manager|proposal`;
manual reading agrees. The patched bytes reproduce exactly the updated pins (runtime `0cc6705e…`, campaign
`d9d8b5a0…`, exam_runner `9acc121c…`), and `SHIM_TARGETS`/`SHIM_SHA256`/`PATCHED_SOURCE_SHA256` were updated in the
driver, all three replay specs, the declared-inputs manifest (pin `7c40fdf5…`), the rendered staged copies and the
tests.

*The fifth gate is real.* `GATE_PROBE` now imports and shadow-executes the patched `r1.scripts.exam_runner`, then
calls the real `r1.exam.observer._authorized_candidate(job, cfg, read_registry(cfg['registry']))` — the exact chain
the B2 root campaign enters (the committed registry still has `gemma4_31b.runtime.footprint_mib =
TODO_VERIFY_ON_HOST` in `r1/exam/registry.yaml`, so the call is always taken). `preflight()` requires
`frozenset(probe.checks) == PROBE_GATES` for **both** walks and passes only when the unshimmed refusal set is exactly
`expected_tasl_blockers(node)` (missing **or** unexpected ⇒ STOP) and no shimmed gate fails. My run of the committed
probe reproduces this end-to-end: unshimmed `authorized_candidate` fails on the TASL tooling path (the round-1
blocker), shimmed `authorized_candidate` passes. The evidence
(`sweep2/evidence/s2_c3_prep_evidence_20261116.json`, `s2_c3_preflight_local_20261116.txt`) says the same
(7-gate exact unshimmed set, five shimmed gates OK, probe rc 0). The regression test
`test_b1_regression_stage_a_pass_set_is_reached_off_tasl_and_relocated` builds a synthetic tree from the real
`runtime.py`/`exam_runner.py`/`observer.py` + the committed shim, and asserts unshimmed `_authorized_candidate` raises
`FileNotFoundError/OSError`, shimmed resolves the registry footprint, and a tampered declared copy is a STOP — it
reproduces the blocker and the fix.

## 2. M1 — accepted 32k layout: FIXED

All three replay specs, the staged `s2_c3_spec.json` and the C2 example spec carry
`walltime_s = 12203`, `request_disk_kb = 42460977`, `request_memory_mb = 32000`; `validate_spec` pins these three
values exactly (no range fallback: a different value is a STOP), `render_jdl.py` renders `request_memory`/
`request_disk`/`+RequestWalltime` from the spec (`_layout` stops on missing/non-positive; no `128000`/`50000000`
remains in C3 artifacts), the per-root timeout is `max(600, 12203-600) = 11603 s`, and the values equal
R1-SWEEP2-LAYOUT (`request_walltime 12,203 s`, `request_disk 42,460,977 kB`, `request_memory 32,000 MB`) at
`025bfc16`. Reproduced: the rendered JDL is byte-identical to `sweep2/dryrun/replay/s2_c3_replay_job.jdl`
(`request_memory = 32000`, `request_disk = 42460977`, `+RequestWalltime = 12203`, CPU class 6/207, 16 CPUs) and all
37 staged transfer inputs are byte-identical to the committed dry-run set; tests pin the layout and the derived
timeout. The C2 example spec (`sweep2/spec.example.json`) was updated to the accepted layout; the C2 *frozen
dry-run capture* (`sweep2/dryrun/s2_c2*`) is intentionally *not* refreshed here — the maintained capture lives on
`origin/sweep2-main-20261116` (verified there: `RequestDisk=42460977`, `RequestMemory=32000`,
`RequestWalltime=12203`, CPU-class requirements). It is not a C3 transfer input and does not affect the C3 run.

## 3. M2 — false "self-contained/no network" claim: FIXED

`S2_C3_DRIVER.md` §2.1 now discloses the three run-time network fetches (paper repo clone at `8709dce7`, harness
clone at `a3fedbb`, 19.6 GB GGUF from HuggingFace `619aca75`), each identity-checked, with the aggregate
3 × 19.6 GB egress and the "GitHub/HF availability is a run-time precondition; failure is a STOP" statement; the
reviewer checklist and the driver module docstring were reworded accordingly. No "self-contained"/"nothing is
fetched"/"no network data" claim remains in the unit (only fix-mapping references remain). This matches the code
(`prepare_authorization_checkout`/`lib.clone_at`, `lib.fetch_model`) and the declared inputs' note.

## 4. Minors from round 1

* **m1 — replay `host_check`/`require_worker_host` keep the DRYRUN-env refusal and the 100 GB floor.** The shim's
  replay branch raises on `R1_DRYRUN`/`R1_FAKE_OLLAMA_ROOT`/`R1_EXAM_DRYRUN`, refuses approved exam hosts, requires
  the output to stay inside the declared sandbox, and calls `space_check(Path(root))` (`MIN_FREE_BYTES =
  100_000_000_000`); only the TASL host/GPU and `/home/dowling` work-dir pins are dropped. The host/GPU rebinding is
  disclosed in `_bypass_dispositions` and recorded in `job_record.host_rebind`. Test
  `test_replay_host_check_keeps_the_dryrun_refusal_and_the_disk_floor` covers all of it. **Addressed.**
* **m2 — server argv + manager settings in `job_record`.** `server_record()` records `argv` and a `manager_settings`
  block (ctx 32768, `-ngl 999`, `-np 1`, jinja, thinking false, cache_prompt false, q8_0 K/V, alias); the comparison
  re-checks the same set and the transferred server log. **Addressed.**
* **m3 — compare mirrors the pins; seal records status.** The comparison now re-checks
  `driver_shim.patch_sha256`, `patched_source_sha256`, `targets`, `declared_inputs.manifest_sha256`,
  every-item-verified, `independent_of_tasl`, and each manifest `job_sha256 == out/<root>/job.json`; the seal binds
  the shim sha, patched-source pins and declared-manifest sha and records `record_status`/`complete_run_result` in
  receipt and marker. **Addressed** (one wording nit below, m2 in §6).
* **m4 — exact unshimmed refusal set.** `_preflight_status` now requires set equality (missing or unexpected ⇒ STOP),
  per node (`openml_*` add `openml_data_cache`), and the probe must report exactly the five gate names; tests cover
  both directions. **Addressed.**
* **m5 — real UTC timestamps / complete cache report.** Declared manifest `created_utc 11:25:00Z`, shim-scope
  `11:29:23Z`, prep evidence `11:29:13Z` are all before the round-2 commit (`11:31:48Z`); the prep evidence now
  carries the full `cache_report` (`phases.openml_cache = true`, installed-tree digests re-derived) and drops the
  misleading `items_verified_checkouts`; the audit evidence dropped its fabricated `generated_utc` and now records a
  relative manifest path. **Mostly addressed** — see m1 in §6 for the `PROVENANCE.json` residual.
* **m6 — authority ancestry documented.** `S2_C3_DRIVER.md` §1 records the external decisions commit, the merge-base
  `9ae6d877` and `branch_ancestor: false`; every job record's `authority` block (and the STOP record) carries the
  same pointer, tested by `test_record_base_notes_the_external_authority_row`. **Addressed.**

## 5. Run path, declared inputs, invariants (unchanged/regression-checked)

* 3 jobs × 4 roots/node, one owned 32k server per job, `out`/`base_url` rewrite only (canonical-form check), all
  three patched modules shadow-executed in the campaign subprocess (verified: `SHADOW_RUNNER` imports and
  `exec`s runtime, campaign and `r1.scripts.exam_runner` into their own module dicts before `campaign.main`, with
  `__file__`-derived `REPO` and `git show HEAD:` checks still pointing at the pinned clean checkout).
  `require_committed_b1_config` still enforces `cwd == REPO`, the committed config/note/PLAN/rule/B1-analysis bytes,
  the 24 root inputs, binding `c502a9aa…`, and the clean `8709dce7` HEAD.
* Preflight strictly precedes `lib.fetch_model` and `lib.start_server`; a preflight STOP writes `job_record.json`
  (`STOP_B2_AUTHORIZATION_GATE`) and packages everything.
* Declared input verification is item-by-item (local files/values, paper blobs by `git show 8709dce7`, harness trees
  by `git ls-tree -r a3fedbb`, OpenML cache installed and re-digested at the campaign's read path, gitignore
  enforced); the audit reconstructs the same binding; TASL-only copies equal the sha256 the B2 config/authorization
  binds, so relocation cannot change what is authorized.
* Labels/audit invariants: ENGINEERING_ONLY + `s2_c3_replay/v1` required on every manifest, audit seeds exactly
  9201–9210, reserved 7001–7010 refused in spec validation, manifest scan and comparison, no B.2 audit accepted.
* Comparison criteria are unchanged in substance (criteria sha `63bd0a9b…`): 240 trials, 20/33/20 ±10 %, 0/240 parse
  failures, 12 final_y pins reproduced from the pinned manifests.

## 6. Findings

No blockers. No majors.

**m1 (minor, evidence hygiene).** `sweep2/s2_c3_inputs/PROVENANCE.json` now claims `created_utc =
2026-11-16T11:48:00Z` and "copies were made 11:47–11:48Z". The file content is first committed at `11:02:54Z`
(`c545852c`), so a UTC copy time of 11:47–11:48Z is impossible; the value is most likely local time (11:47–11:48
CET ≈ 10:47–10:48Z) mislabelled with `Z`. This is the same class as round-1 m5 and the fix-table claim that all
evidence "carries real UTC times (no future timestamps)" is therefore not fully true. No run path reads
PROVENANCE.json, so this is documentation/evidence hygiene only; correct the value/note (or state it is local time).

**m2 (minor, seal wording vs behaviour).** `seal_replay`'s new docstring and `S2_C3_DRIVER.md` §4.4 say "a STOP
output may be sealed for retention". That holds for STOP records created after `record["host"]`/`label_patch`/
`driver_shim`/`declared_inputs` are populated, but an **early** `STOP_PREP` record from `_stop_record()` has none of
those blocks: seal refuses it ("job record has no host identity"). Retention for an early STOP is still via the
transferred `out.tar`/`work.tar`/`SHA256SUMS` on the submit host, and no COMPLETE-capable path is affected; narrow
the wording (or copy the pin blocks into `_stop_record`, which would be consistent with the documented intent).

**m3 (minor, evidence provenance).** The committed local `prep`/`preflight` evidence was produced with an
intermediate driver revision (`/tmp/s2c3fix_e2e/s2_c3_replay.py` sha256 `1996e304…`), not the committed
`sweep2/s2_c3_replay.py` (`26dea212…`). I diffed the two: the differences are spec-validation/`_server_thinking`,
`server_record`, docstrings and the audit note — the `GATE_PROBE` is byte-identical and `prep`/`preflight` code is
unchanged, and re-running the committed probe against the same pinned clones reproduces the same result, so the
evidence is substantively valid; note it in the evidence (or regenerate with the committed revision) so a branch-only
reader can reproduce it byte-for-byte.

**Observations (no action required for the run).**
* The inherited C2 dry-run snapshot in this branch (`sweep2/dryrun/s2_c2_eng_example.jdl`, `s2_c2_spec.json`,
  `s2_c2.dryrun.txt`) still shows the pre-32k values; the maintained C2 capture is on `origin/sweep2-main-20261116`.
  Keep that branch's C2 artifacts on merge; not used by the C3 run.
* `exam_runner._evidence_unreviewed` and the batch/dry-run scripts still read the TASL Stage-A paths, but they are
  outside the ENGINEERING replay path (no B.2 audit; `campaign.main` is the only entry used).
* The driver enforces a per-root timeout (`11603 s`) but not a total-job deadline; a hung root can consume the
  12,203 s HTCondor walltime (the job entry pre-creates the five outputs so an early kill still transfers
  placeholders). Normal expectation from the B2 chunk measurement (9,387 s for an 18-instance chunk) leaves ample
  margin for 4 roots.

## 7. Run-safety for the 3 ENGINEERING jobs (unit review, not a cluster review)

No remaining unit-level blocker to the 3 jobs: preflight (two walks, exact sets) precedes the model fetch, the
server starts only after the five gates pass, and any refusal is a persisted STOP with no retry. What to watch at
run time:

1. **Cluster resources.** The task's cluster note is accepted: NEMO2 currently advertises no g36xx L40S ads (only
   H200/n3xx and the deepthought portal L40S), so `condor_submit` may simply idle. The unit itself requires
   `CloudSite=BwForCluster-Nemo2 ∧ GPUs_DeviceName="NVIDIA L40S" ∧ CpuFamily 6 ∧ CpuModelNumber 207 ∧ Cpus≥16`; if the
   L40S nodes that come back carry a different CPU class, the ad will never match (and `lib.cpu_identity` would STOP
   the job). That would need an author decision, not a driver change. This review is about the unit.
2. **Network/egress.** GitHub + HuggingFace availability and 3 × 19.6 GB GGUF downloads (fail = STOP before roots).
3. **100 GB sandbox floor.** The reviewed shim keeps the author's `space_check` 100 GB floor on the declared sandbox,
   so if the container scratch filesystem reports <100 GB free the job STOPs at preflight (before the model fetch).
   Watch this in the first job's `host_check`; it is the intended author-STOP-0 semantics, not a bypass.
4. **Resources/time.** 32,000 MB memory, 42,460,977 kB disk, 16 CPUs, 12,203 s walltime, 11,603 s per-root timeout;
   the B2 chunk basis (9,387 s for 18 instances) leaves margin for 4 roots, but watch root wall times.
5. **Server/build/offload.** The owned 32k server must report the pinned build (`0.7.0-dev (build 11669, commit
   620d2225c)`) and full offload (61/61); the log/argv are recorded and re-checked by the comparison.
6. **Stochastic criteria.** Criteria 1–6 are tolerances on a temperature-0.2 replay; a correct stack can legitimately
   land NOT PASS (duplicates 33 ±3.3 etc.). That is pre-declared, not a defect; no post-data relaxation.
7. **Operator gates.** `condor_submit -dry-run` on the submit host is still pending, and submission remains gated on
   the author's sweep-2/EVIDENCE authorisation. Sealing `/ceph` is operator work (NEMO2 slots do not provide
   ProvidesEtpCeph). No execution happened here and P4 is not claimed.

## 8. Verdict

All round-1 required items are implemented: B1 (shim relocation of both Stage A reads in `stage_a_pass_set`, the
fifth `authorized_candidate` preflight gate, updated pins, and a regression test) is fixed and independently
reproduced against the real pinned clones; M1 (accepted 32k layout throughout, spec-driven renderer, re-rendered
JDL/37 staged inputs, 11,603 s per-root timeout) and M2 (network/egress disclosure) are fixed; minors m1–m6 are
addressed. Remaining items are minor evidence/wording residuals (PROVENANCE UTC value, seal wording for early STOP
records, evidence generated with an intermediate driver revision) plus observations that do not affect the run.
Tests 176/176 pass, the declared-input audit is clean (25 items, 0 failures), and the JDL/37 staged inputs reproduce
byte-identically.

VERDICT: ACCEPTED for the 3-job ENGINEERING run
