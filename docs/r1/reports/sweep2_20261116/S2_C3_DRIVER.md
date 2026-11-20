# S2-C3 TASL-independent ENGINEERING replay driver (R1-S2C3-DRIVER)

Status: **implemented, 176 synthetic tests pass, declared-input audit clean, local real-clone prep + two-phase
pre-flight executed** (no HTCondor job, no llama-server, no B.2 audit, no seed 7001–7010, no label read). This
document is the reviewable description of the driver authorised by author row **R1-S2C3-DRIVER**
(`origin/author-decisions-20261116b` @ `025bfc16477a3911ea461d7a6cfc85f3ea523d66`), building on the frozen unit
`s2c3-deploy-20261116` @ `2b454c33`, on branch `s2c3-driver-fix-20261116` (round-2 fix per
`docs/r1/reviews/S2_C3_DRIVER_REVIEW_20261116.md`). The same authority commit carries **R1-SWEEP2-LAYOUT**, whose
accepted 32k layout is applied here unchanged (see §4).

| item | state |
|---|---|
| declared-inputs manifest + TASL-only copies | committed (`sweep2/s2_c3_declared_inputs.json`, sha256 `7c40fdf5…1893`; `sweep2/s2_c3_inputs/`), audit clean |
| reviewed TASL-only preflight shim | committed (`sweep2/s2_c3_driver_shim.diff`, sha256 `defac236…aa92`), additions only (72 added / 0 removed / 4 hunks / 3 files), applied and byte-pinned |
| driver `sweep2/s2_c3_replay.py` | extended: declared-input verification, shim pre-flight with an exact unshimmed refusal set and five shimmed gates, runtime shadow-exec of all three patched sources, accepted 32k layout |
| comparison `sweep2/s2_c3_compare.py` | unchanged in substance (criteria 1–6, 20/33/20 ±10 %, 0/240, final_y/offload/throughput); now also re-checks the shim/declared-input/job-sha pins and the recorded server argv/settings |
| tests | `r1/tests/htcondor/` → **176 passed** (161 pre-existing + 15 new/updated driver tests, incl. the B1 regression) |
| local declared-inputs audit | `sweep2/evidence/s2_c3_declared_inputs_audit_20261116.json` — 25/25 items declared, 0 failures |
| local `prep` + two-phase pre-flight against the real pinned clones | `sweep2/evidence/s2_c3_prep_evidence_20261116.json` and `sweep2/evidence/s2_c3_preflight_local_20261116.txt` — paper `8709dce7` + harness `a3fedbb` cloned from GitHub, 25/25 declared items verified, OpenML cache installed with the declared tree digests, both patches applied with the pinned patched-source shas, binding `c502a9aa…`, exact unshimmed TASL refusal set, **all five shimmed gates PASS**; **no server, no roots, no HTCondor** |
| execution of the 3 replay jobs | **NOT DONE** (this unit is local code/tests/docs evidence only; P4 is still not claimed) |

## 1. What the author row authorises

R1-S2C3-DRIVER authorises "an independently reviewed, fully declared-input, TASL-independent ENGINEERING replay
driver for the S2-C3 L40S deployment check", with every input declared item-by-item with sha256 verification,
ENGINEERING_ONLY, no B.2 audit, no 7001–7010. It also accepted the corrected criterion 3 (invalid 20 / duplicates 33
/ noops 20 over 240 trials, ±10 %; parse failure 0/240). R1-SWEEP2-LAYOUT (same commit) fixes the sweep-2 layout at
walltime 12,203 s / disk 42,460,977 kB / memory 32,000 MB.

This branch implements exactly that: it **reuses the B2 campaign/trial/manager/scoring/audit code** (nothing numeric is
reimplemented), constructs the campaign job from the 12 pinned B2 root `job.json` files with only `out` and
`base_url` rewritten, and skips/relocates **only** the TASL-specific preflight through one small reviewed shim.

**Authority ancestry (m6):** the decisions row is *external* to this branch — the branch base is `2b454c33`, the row
lives at `025bfc16` on `origin/author-decisions-20261116b`, and the merge-base is `9ae6d877`. The row is not a run
input; the in-tree PLAN is the B2-bound `8709dce7` blob (pinned as a declared input). Every job record carries an
`authority` block recording this (`branch_ancestor: false`).

## 2. Declared inputs — every input, path + sha256, verified at start

`sweep2/s2_c3_declared_inputs.json` (sha256
`7c40fdf5ddaf435b48dffb063e85f878f1ea36d43f49a5fe094768d8ad201893`) lists 25 items. The driver refuses to start
(`DECLARED_INPUTS_STOP.json` + `job_record.json` status `STOP_PREP`) if any item is missing or its sha256/tree digest
differs. Nothing **unpinned** is fetched at run time; three identity-pinned network artifacts are (see §2.1).

| # | item id | kind | path / identity | sha256 | provenance |
|---|---|---|---|---|---|
| 1 | `b2_config` | paper blob | `r1/scripts/configs/exam_b2_v2.json` | `869a4327…1d6` | committed paper `8709dce7` |
| 2 | `registry_snapshot` | paper blob | `r1/exam/registry.yaml` | `2c6ef6b3…723` | committed paper `8709dce7` |
| 3 | `rule_x5_rule_v2` | paper blob | `r1/exam/rules/x5_rule_v2.yaml` | `53018aa7…6ad` | committed paper `8709dce7` |
| 4 | `value_grids` | paper blob | `r1/exam/value_grids.yaml` | `7ab60c16…a14` | committed paper `8709dce7` |
| 5 | `b1_analysis` | paper blob | `docs/r1/reports/b1_d_20261113_evidence/complete_batch_verifier.json` | `07cb62de…ffc` | committed paper `8709dce7` (B2 authorization bound) |
| 6 | `b2_authorization_note` | paper blob | `docs/r1/authorizations/trackx_b2_20261115.md` | `ef92521c…a0f3` | committed paper `8709dce7` |
| 7 | `plan_author_rows` | paper blob | `docs/r1/PLAN.md` | `1f6c4132…d996` | committed paper `8709dce7` (X5/B2 author rows) |
| 8 | `anchor_duplicate_reference` | paper blob | `docs/r1/reports/B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json` | `84200770…85dd` | committed paper `8709dce7` |
| 9 | `stage_a_amendment_acceptance` | paper blob | `docs/r1/reports/OPS_O1_20261104.md` | `0cda82fa…053e` | committed paper `8709dce7` |
| 10 | `stage_a_table_t7h8` | file (TASL-only) | `sweep2/s2_c3_inputs/stage_a_table_t7h8.json` → `S2C3_IN_stage_a_table_t7h8.json` | `00ab143d…975c` | TASL-7 `/home/dowling/exam-x/work/r1_stagea_20261103_t7h8/stage_a_table.json`, read-only scp 16 Nov |
| 11 | `stage_a_amendment_table_t7j10` | file (TASL-only) | `sweep2/s2_c3_inputs/stage_a_amendment_table_t7j10.json` | `7152512…2103` | TASL-7 `…/r1_stagea_20261104_t7j10/stage_a_table.json` |
| 12 | `stage_a_prompts` | file (TASL-only) | `sweep2/s2_c3_inputs/prompts.jsonl` (50 lines) | `70872a77…510a` | TASL-7 `…/frozen_inputs/trackx_stagea_promptset_20261031/prompts.jsonl` |
| 13 | `openml_cache_archive` | file (TASL-only) | `sweep2/s2_c3_inputs/openml_cache_t7_20261009.tar.gz` (67 KB, deterministic) | `f51c3c32…7f3e` | TASL-7 `b1_harness_offline_stage_20261107_a` harness pilot cache (OpenML ids 29 / 59) |
| 14 | `openml_credit_approval_cache` | staged tree | `openml_credit_approval/data_cache` | tree `702a0b3c…57a8`; 4 files listed | same archive; per-file sha256 equal to the B2 run-root copies |
| 15 | `openml_ionosphere_cache` | staged tree | `openml_ionosphere/data_cache` | tree `65dfc44c…4bf7`; 4 files listed | same archive; per-file sha256 equal to the B2 run-root copies |
| 16 | `node_digits_mlp` | harness tree | `nodes/digits_mlp` | `bf66ecca…6d55` (2 blobs) | committed harness `a3fedbb` |
| 17 | `node_openml_credit_approval` | harness tree | `nodes/openml_credit_approval` | `c67b9ab9…7e23` (5 blobs) | committed harness `a3fedbb` |
| 18 | `node_openml_ionosphere` | harness tree | `nodes/openml_ionosphere` | `9209cbda…6ca` (5 blobs) | committed harness `a3fedbb` |
| 19 | `replay_root_inputs` | file | `docs/r1/reports/sweep2_20261116/c3_replay_inputs/SHA256SUMS` (24 files) | `6224b75a…adf6` | pinned from the B2 batch output (committed `2b454c33`) |
| 20 | `label_patch` | file | `sweep2/s2_c3_label_patch.diff` | `fd0234c9…d741` | this branch (reviewed label-only patch) |
| 21 | `driver_shim` | file | `sweep2/s2_c3_driver_shim.diff` | `defac236…aa92` | this branch (re-reviewed TASL-only shim) |
| 22 | `criteria` | file | `docs/r1/reports/sweep2_20261116/S2_C3_CRITERIA.md` | `63bd0a9b…bcdc` | this branch (pre-declared criteria 1–6) |
| 23 | `b2_configuration_binding` | value | `c502a9aa…290b` (recomputed, not trusted) | — | B2 evidence batch |
| 24 | `model_gguf` | value | sha256 `2959c1b0…1b75`, size 19 598 489 952 | — | B2 candidate record; fetched and sha-verified before serving |
| 25 | `image_llama_server` | value | `ghcr.io/…@sha256:69b06b35…5296`, llama-server `f8d35fd3…cc0` | — | frozen v1 GPU image |

The three TASL-only inputs (Stage A tables, Stage A prompt set) and the OpenML caches are **copied read-only from
TASL-7 once** (recorded in `sweep2/s2_c3_inputs/PROVENANCE.json`, including the deterministic archive recipe and real
UTC copy timestamps) and shipped in this branch. Every copy sha256 equals the value the B2 configuration/authorization
already binds (`00ab143d`, `7152512`, `70872a77`) — the relocation therefore cannot change what the authorization
approves. The OpenML per-file sha256 values were cross-checked against the B2 run-root copies on TASL-7
(`b2_8709_20261115_b2/gemma4_31b/b2/off/<node>__s9011/node/data_cache`); they are identical. **No input needed at run
time is TASL-only, and no unpinned data is used.**

Verification phases (all before the model/server):
1. staged declared `file` items and `value` items (before any clone);
2. `paper_blob` items against `git show 8709dce7:<path>` in the freshly cloned pinned paper checkout, and
   `harness_tree` items against `git ls-tree -r a3fedbb` in the freshly cloned pinned harness;
3. `staged_tree` items after `stage_openml_cache` installs and re-digests the extracted cache;
4. after preparation, the staged `file` items and the 24 pinned root inputs are re-verified byte-identically; after
   the 4 roots they are verified again (`job_record.declared_inputs.post_run`).

### 2.1 Run-time network (M2 disclosure — identity pinned, no TASL access)

Each job **does** fetch three network artifacts at run time, and verifies the identity of each before use:

| # | fetch | identity check | egress |
|---|---|---|---|
| 1 | clone the paper repo `https://github.com/dowlingwong/Agent_paper_B.git` | `git fetch --depth 1` of `8709dce7`; HEAD must equal it; checkout must be clean | small |
| 2 | clone the harness repo `https://github.com/dowlingwong/autoresearch_harness.git` | exact commit `a3fedbb` | small |
| 3 | fetch the GGUF from HuggingFace (bartowski `gemma-4-31B-it` Q4_K_M, revision `619aca75`) | size `19598489952` + sha256 `2959c1b0…1b75` | **19.6 GB per job, 3 × 19.6 GB total** |

Consequences: the 3 jobs need outbound GitHub and HuggingFace access (availability is a run-time precondition; a
failure is a STOP, never a fallback), and the model egress is ~58.8 GB in aggregate. Nothing is fetched from TASL and
no TASL mount is needed.

The operator can audit the local half at any time without a run:

```
python3 sweep2/s2_c3_replay.py audit sweep2/spec.replay.example.json
# → 25 items, 0 failures; 22 verified locally + 5 explicitly deferred to job start (3 harness trees, 2 installed-
#   cache digests; the 2 staged-tree file lists are themselves verified locally); TASL-only items listed as shipped;
#   recomputed binding = c502a9aa…290b
```

## 3. The reviewed shim — exactly what is bypassed and why it cannot change numerics

`sweep2/s2_c3_driver_shim.diff` (sha256 `defac236…aa92`, **72 added lines, 0 removed lines, 4 hunks, 3 files**) is
applied to the detached shadow worktree after the label patch. It is **inert** unless `R1_S2C3_DECLARED_INPUTS` is
set, so every other exam phase and the un-shimmed pre-flight walk see the unmodified B2 code.

| hunk (anchor) | change | what it does |
|---|---|---|
| `def read_registry(path):` | + helpers + 2 lines at the top of `host_check` | `_s2c3_declared()`, `_s2c3_relocate()`, `_s2c3_host_check()`, `_s2c3_require_worker_host()`; replay mode replaces the TASL host/work-dir gate while keeping the production DRYRUN-env refusal and the 100 GB disk floor |
| `def _committed_b1_authority(cfg, note, raw, rule_sha):` | + 1 line | `path=_s2c3_relocate(cfg,path_key,path)` — the Stage A table paths resolve to the declared copies after the same sha256 check the original loop already performs |
| `def stage_a_pass_set(cfg, registry_candidates, *, v2):` | + 5 lines | round-2 **B1 fix**: the same relocation is applied to the local `cfg` before the two Stage A reads, so `exam_runner.stage_a_pass_set` (reached on every B2 root through `authorized_b1_observer → _authorized_candidate`) no longer reads the TASL-absolute `/home/dowling` paths |
| `def require_worker_host(job, node=None):` | + 2 lines | replay mode returns the real node after the off-TASL/sandbox check instead of pinning `cfg.host == platform.node()` |

**What is bypassed** (the driver refuses to continue unless the un-shimmed probe reports *exactly* the reviewed set
below — a missing expected refusal is a STOP just like an unexpected one — `preflight.missing_tasl_blockers` /
`preflight.unexpected_tasl_blockers`):

| pre-declared TASL refusal | disposition |
|---|---|
| `authorization_input:stage_a_table` | read from the declared sha256-pinned copy (same sha256 the config binds) |
| `authorization_input:stage_a_amendment_table` | same, declared copy |
| `authorized_candidate` | the `stage_a_pass_set` read is relocated to the declared copies (same sha256 check); `_authorized_candidate` then resolves the registry footprint exactly as on TASL |
| `host_check` | TASL-2/7 + `/home/dowling` + out-under-work_dir replaced with: **must not be an approved exam host**, out inside the declared job sandbox; the production DRYRUN-env refusal and the author 100 GB disk floor are **kept** (floor applied to the declared job sandbox) |
| `require_worker_host` | actual-node == TASL-7 pin replaced with the same off-TASL/sandbox + DRYRUN-env + disk-floor check; the job host/GPU fields are still compared to the committed config/authorization, and the physical host/GPU rebound is recorded in `job_record.host_rebind` |
| `out_under_work_dir` | admitted by the replay-mode sandbox check (the B2 `/home/dowling` rule is not applicable off TASL) |
| `openml_data_cache` (openml_* nodes only) | shipped archive installed into the pinned harness at the exact path the campaign copies from |

**Why the numerics and the B2 authorization semantics are provably unchanged:**
- the shim adds lines only, and every added code line is screened against
  `run_config|paired(|run_real_campaign|root_trials|root_events|audit_seeds|instance_seeds|final_audits|diagnostics|write_json|score|metric|manager|proposal`
  (`check_shim_scope`, enforced by the driver and covered by tests); no trial, manager, scoring or audit function is
  touched or re-implemented;
- the patched source bytes are pinned after applying **label then shim**: `r1/exam/runtime.py` → `0cc6705e…5d3`,
  `r1/exam/campaign.py` → `d9d8b5a0…c0c`, `r1/scripts/exam_runner.py` → `9acc121c…9d85`; a different patched source is
  a STOP;
- the pinned authorization checkout stays **byte-identical** (`git status --porcelain --untracked-files=all` empty;
  the patches live only in a detached sandbox worktree and are shadow-executed in the module namespace);
- the authorization gates still run unchanged: committed `exam_b2_v2.json` bytes, the committed B2 note bytes, the
  PLAN §10 author rows, the rule/b1-analysis/manifest digests, the seed/worker/cap/node/host/GPU bindings, and the
  `authorization_checkout_head == 8709dce7` check. Only *where the already-sha-bound Stage A files are read from* and
  *which physical host runs the ENGINEERING check* change (plus, in replay mode only, the DRYRUN-env/disk-floor path
  the check applies to);
- the configuration `binding` is recomputed with the B2 method and equals `c502a9aa…290b`; `out`/`base_url` are not
  binding inputs, so the sandbox rewrite cannot move it;
- the label patch remains separate and label-only (ENGINEERING_ONLY + replay marker; a DRYRUN job is refused).

The driver pre-flights the B2 gates **twice** with the same patched sources: once with the replay env unset (it must
report exactly the reviewed TASL refusal set) and once with the replay env set (all five gates must pass:
`verify_b1_worker_input`, `host_check`, `require_worker_host`, `harness_binding`, **`authorized_candidate`**). The
probe must report exactly those five gates or the preflight is a STOP, so "the pre-flight covers the gates the
campaign calls" is a checked property. Only after PASS is the model fetched and the single owned 32k server started.

## 4. Driver mechanics (changed vs the frozen unit)

1. `prep`: pinned-root SHA256SUMS verification → declared-inputs local verification → pin/clone paper `8709dce7`
   (clean, note present) → pin/clone harness `a3fedbb` (clean) → binding recomputation → declared `paper_blob`/
   `harness_tree` verification → OpenML cache archive extraction/verification/installation (target must be
   `git check-ignore`d; harness must stay clean) → `apply_reviewed_patches` (label then shim; all scopes, all shas,
   all three patched-source pins, authorization checkout untouched) → criteria pin → re-verify pinned roots, declared
   files.
2. `preflight`: un-shimmed TASL walk (blocker enumeration, exact-set screen) then shimmed walk (all five gates must
   pass; the probe must exercise exactly the five).
3. `run`: one owned 32k server (`-c 32768 -ngl 999 -np 1 --jinja`, thinking off, q8_0 KV, cache_prompt false), then the
   4 roots of the node sequentially through `python -m r1.exam.campaign` semantics with **all three** patched modules
   (campaign, runtime, `r1.scripts.exam_runner`) shadow-executed (same `__file__`/`REPO`, same trial/audit code).
   `job_record.server` records the started `argv` and the pinned `manager_settings` (ctx 32768, `-np 1`, q8_0 KV,
   thinking off, cache_prompt false, alias), not just the log; `job_record.host_rebind` records the physical
   host/GPU rebinding.
4. every root must produce a COMPLETE `campaign_manifest.json` with `execution_label=ENGINEERING_ONLY` +
   `replay_marker=s2_c3_replay/v1`, audit seeds exactly `[9201..9210]`, no 7001–7010, job binding and job sha
   reproduced; any leak/pin mismatch/nonzero root is a STOP with everything retained; then `out.tar`/`work.tar`/
   `job_record.json` + `SHA256SUMS`, and the operator seals with the S2-C2 guards (seal binds the shim sha, the
   patched-source pins and the declared-inputs manifest sha; a STOP output may be sealed for retention and the seal
   receipt records the record status so it cannot be mistaken for a COMPLETE run result).

**Layout (R1-SWEEP2-LAYOUT, applied unchanged — no C3-specific guess):** the 3 replay specs and the rendered JDL
carry `walltime_s = 12203`, `request_disk_kb = 42460977`, `request_memory_mb = 32000`; `render_jdl.py` takes these
from the spec (no hard-coded `128000`/`50000000` remains), the replay validator pins the exact values, and the
per-root campaign timeout is derived from the accepted walltime (`root_timeout_s = max(600, 12203 - 600) = 11603 s`).

## 5. STOP list (in addition to the frozen unit's)

- any declared input missing/unreadable/different sha256 (the audit report is persisted in `DECLARED_INPUTS_STOP.json`);
- the 3 TASL-only inputs cannot be shipped/verified (not the case here — they are committed with provenance);
- driver-shim sha differs, the shim removes/modifies any pinned line, touches a file outside
  `{r1/exam/runtime.py, r1/exam/campaign.py, r1/scripts/exam_runner.py}`, or matches trial/audit/scoring code;
- the patched-source byte pins differ; the authorization checkout is not clean before/after patching;
- the un-shimmed walk reports anything other than **exactly** the reviewed TASL refusal set (a missing expected
  refusal or an unexpected one), the probe does not exercise exactly the five gates, or any shimmed gate still
  refuses;
- the replay runs on an approved exam host (TASL-2/TASL-7), or the DRYRUN environment enters it, or the declared
  sandbox is below the 100 GB author floor — the shim refuses, so a misdirected job STOPs instead of quietly becoming
  a TASL run;
- the OpenML cache target is not gitignored by the pinned harness (it would dirty the bound checkout);
- any label leak, any 7001–7010 seed, any audit-seed set other than 9201–9210, any nonzero root, any missing manifest;
- a rendered JDL with any layout value other than the accepted 32k set.

## 6. Verification plan

Local (done here; no execution of the 3 jobs):

```
PY=/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/sweep2-cluster-20261116/.venv-test/bin/python
$PY -m pytest r1/tests/htcondor/ -q -p no:cacheprovider          # 176 passed
$PY sweep2/s2_c3_replay.py audit sweep2/spec.replay.example.json  # 0 failures
$PY sweep2/render_jdl.py sweep2/spec.replay.example.json \
      --out /tmp/s2c3.jdl --stage-dir /tmp/s2c3-stage             # 37 staged files, JDL renders
# local prep + two-phase pre-flight against the real pinned clones (network clone; no server, no roots):
cd /tmp/s2c3-stage && $PY s2_c3_replay.py preflight s2_c3_spec.json  # exact TASL set + five gates PASS
```

The local `prep` + `preflight` were run here (evidence committed): paper `8709dce7` and harness `a3fedbb` were cloned
from the declared GitHub URLs, the declared-inputs audit verified 25/25 items (paper blobs, harness node trees, all
declared files, the installed OpenML cache trees), the binding recomputed to `c502a9aa…290b`, the criteria pin
matched, all three patched sources matched their pins while the authorization checkout stayed clean, the unshimmed
walk reported **exactly** the reviewed TASL refusal set, and the shimmed walk passed **all five** gates — including
the Stage A pass-set/`_authorized_candidate` path that was the round-1 blocker. No server, model or root ran.

The driver also has a no-server gate-walk command for the operator: `python3 sweep2/s2_c3_replay.py preflight
s2_c3_spec.json` (inside the job sandbox / worker image) — it runs the same `prep` + two-phase pre-flight as `run` and
exits non-zero unless the exact unshimmed set is reported and every shimmed gate passes.

Operator (NOT done here): on the deepthought submit host, from this branch: render the three per-node specs, run
`condor_submit -dry-run` and compare with `sweep2/dryrun/replay/README.md`; then, only after independent review and the
author's sweep-2/EVIDENCE gate, submit the 3 ENGINEERING jobs (one per node), seal each output, and run
`sweep2/s2_c3_compare.py` → `S2_C3_RESULTS.md`.

## 7. What is still unverified without a run

- every criterion 1–6 value (final_y, parse failures, diagnostics 20/33/20, offload 61/61, wall time);
- the shimmed gate walk *inside the worker image* against the real pinned clones (it is now verified on the local
  machine with the same pinned clones and patched sources, but the job image's Python/deps are only exercised at
  job start);
- the real OpenML cache install into a real `a3fedbb` clone inside the image (tested locally against the real clone
  and synthetically against a git-ignored harness);
- the actual ENGINEERING_ONLY manifest and server log emitted by a real campaign;
- the sealed `/ceph` receipt; the real `condor_submit -dry-run`;
- GitHub/HuggingFace availability and the 3 × 19.6 GB egress at run time.

P4 (L40S deployment check passed) remains **not claimed**.

## 8. Independent reviewer checklist

1. **Authority**: R1-S2C3-DRIVER + R1-SWEEP2-LAYOUT rows at `origin/author-decisions-20261116b` @ `025bfc16` (external
   to this branch's ancestry; see §1); criteria correction applied pre-data (20/33/20 over 240, 0/240) and unchanged
   here; layout values equal the accepted numbers.
2. **Declared inputs**: every item in `sweep2/s2_c3_declared_inputs.json` has a path, a sha256/tree digest and a
   provenance; the three TASL-only items equal the sha256 the B2 config/authorization binds; no declared input is
   missing or unverifiable (audit evidence committed). Confirm the **only** run-time fetches are the three
   identity-pinned artifacts (paper/harness clone + GGUF, §2.1) and that no TASL mount or unpinned data is used.
3. **Shim**: read `sweep2/s2_c3_driver_shim.diff`; confirm additions only, only the three named files, only the four
   anchors, no trial/manager/scoring/audit line. Confirm the off-TASL assertion (it refuses TASL-2/TASL-7, keeps the
   DRYRUN-env refusal and the 100 GB floor) and the sandbox confinement. Confirm the shim is inert without
   `R1_S2C3_DECLARED_INPUTS`, and that **both** Stage A read paths (`_committed_b1_authority` and
   `stage_a_pass_set`) are relocated.
4. **No numeric reimplementation**: check the driver imports/calls the B2 code path (`r1.exam.campaign` shadow-exec,
   `run_config`/`paired` untouched, binding recomputed with `ExamRunner`'s method) rather than reproducing it.
5. **Authorization semantics**: confirm the pinned checkout is clean at `8709dce7`, the committed config/note/PLAN/rule/
   B1-analysis digests still gate the run, and the shim only relocates already-sha-bound Stage A files and the
   physical host.
6. **Label/audit invariants**: 4 roots/node sequentially, exactly 9201–9210, no 7001–7010, ENGINEERING_ONLY + replay
   marker in every manifest, no B.2 audit, no label read.
7. **STOP behaviour**: every refusal path persists evidence and never retries; a label leak/pin mismatch is a STOP; the
   unshimmed refusal set is exact, not a subset.
8. **No-execution disclosure**: this branch contains no run output and no claim about P4; the dry-run JDL is staged but
   `condor_submit` was not available here.
9. **Reproduce**: `pytest r1/tests/htcondor/ -q` → 176 passed; `python3 sweep2/s2_c3_replay.py audit
   sweep2/spec.replay.example.json` → 0 failures; `render_jdl` → 37 staged transfer inputs with the accepted layout.

## 9. Review round 2 fixes (mapping to `docs/r1/reviews/S2_C3_DRIVER_REVIEW_20261116.md`)

| finding | fix |
|---|---|
| **B1** (blocker): `stage_a_pass_set` read the TASL-absolute Stage A tables unrelocated; preflight never exercised it | re-reviewed **additions-only** 4th shim hunk in `r1/scripts/exam_runner.py:stage_a_pass_set` (relocates both tables via the same `_s2c3_relocate` sha256 check, inert without the switch); `SHIM_TARGETS`/`SHIM_SHA256`/`PATCHED_SOURCE_SHA256`/specs/manifest updated; the gate probe now imports + shadow-execs the patched `exam_runner` and **exercises `_authorized_candidate` → `stage_a_pass_set` as a fifth gate**, with the same patched `exam_runner` shadow-executed in the real root campaign; regression test reproduces the off-TASL FileNotFoundError and the relocated success |
| **M1** (major): stale 16k layout | spec-declared accepted 32k layout: `walltime_s 12203`, `request_disk_kb 42460977`, `request_memory_mb 32000` in all 3 replay specs; `render_jdl.py` uses the spec fields (no hard-coded 128000/50000000); exact validator pins; JDL/README/37 staged inputs re-rendered; per-root timeout `max(600, walltime-600) = 11603 s`; tests updated; **no C3-specific layout invented** |
| **M2** (major doc): false "nothing fetched"/"self-contained" claim | §2.1 explicitly discloses the three identity-pinned run-time fetches (paper clone `8709dce7`, harness clone `a3fedbb`, 19.6 GB GGUF) and the 3 × 19.6 GB egress; reviewer checklist reworded accordingly |
| **m1** (minor): replay `host_check` bypassed the DRYRUN-env refusal + 100 GB disk floor; host/GPU rebound undisclosed | the replay branch now **keeps** the `R1_DRYRUN`/`R1_FAKE_OLLAMA_ROOT`/`R1_EXAM_DRYRUN` refusal and the 100 GB floor (applied to the declared sandbox); host/GPU rebinding is disclosed in the bypass table and in `job_record.host_rebind` |
| **m2** (minor): no server argv/manager settings in `job_record` | `job_record.server` now carries `argv` and a pinned `manager_settings` block (ctx 32768, `-ngl 999`, `-np 1`, q8_0 K/V, thinking off, cache_prompt false, alias); the comparison re-checks them |
| **m3** (minor): compare did not mirror the shim/declared pins / job sha | the comparison now re-checks `driver_shim.patch_sha256`, `patched_source_sha256`, `targets`, `declared_inputs.manifest_sha256`, every-item-verified, `independent_of_tasl`, and `manifest.job_sha256 == out/<root>/job.json`; `seal_replay` requires the patched-source pins and records the record status (`complete_run_result`) so a sealed STOP is explicit |
| **m4** (minor): unshimmed screen was a name allow-list, not the exact set | the unshimmed walk must report **exactly** `expected_tasl_blockers(node)` (a missing expected refusal or an unexpected one is a STOP); the probe must exercise exactly the five gates; docs updated from "allow-list" to "exact set" |
| **m5** (minor): evidence timestamps in the future; cache report incomplete | the declared-inputs manifest, `PROVENANCE.json`, shim-scope, audit and prep evidence carry real UTC times (no future timestamps); the prep evidence records the full cache re-verification report (`cache_report`, `phases.openml_cache = true`) |
| **m6** (minor): authority row is external to the branch | documented in §1 and recorded in every `job_record.authority` block (`branch_ancestor: false`, merge-base + external commit) |
| O1/O2/O3 | restated in §7: the criteria are tolerances on a stochastic replay (a correct stack can legitimately land NOT PASS); remaining prerequisites are the author's sweep-2/EVIDENCE gate, GitHub/HF availability, 3 × 19.6 GB egress, and 3 L40S slots; the deferred declared items and the five shimmed gates are verified at job start |

## 10. No-execution disclosure

Nothing was executed: no HTCondor job was submitted, no llama-server was started, no B.2 audit ran, no label was read,
no seed 7001–7010 was touched, and no `/ceph` write occurred. The only runs are `pytest` on synthetic data, the
declared-inputs `audit`, the JDL renderers, and the no-server local `prep`/`preflight` against the real pinned clones.
P4 is not claimed.
