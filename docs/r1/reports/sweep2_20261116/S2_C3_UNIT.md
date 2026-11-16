# S2-C3 — L40S deployment check: replay unit (ENGINEERING; implementation for review; **nothing executed**)

**Authority:** pre-declared protocol `docs/r1/reports/sweep2_20261116/S2_C3_CRITERIA.md` @ `95321abc`
(sha256 `20870b16d8259982351571e832a7d3f2990d34d042c3aec2d841467f895ae85e`), written under
`author-decisions-20261116` @ `4da73306` (R1-SWEEP-HOST-HTC; R1-SWEEP2-SETTINGS) and the work plan
`docs/runbooks-16nov` §3 S2-C3. ENGINEERING_ONLY: no EVIDENCE label, no label table, no B.2 audit, no seed 7001–7010,
nothing here is a run result. **No HTCondor job was submitted, no llama-server was started, no deepthought/TASL host
was touched.** The only execution in this unit is `pytest` on synthetic data.

## Status

| item | state |
|---|---|
| replay driver / job entry / JDL renderer / comparison | implemented, 100 synthetic tests pass |
| rendered dry-run JDL (no `condor_submit`) | committed under `sweep2/dryrun/replay/`; real dry-run by the operator later |
| **execution of the 3 replay jobs** | **BLOCKED — preflight STOP, see §6; needs an author decision before any submission** |
| P4 (L40S deployment check passed) | **not claimed, not passed** |

## 1. What the unit does

One job == one B2 node: it validates the replay spec (`s2_c3_replay/v1`, every pin fixed in code and refused otherwise),
verifies the 25 pinned replay-input files against their SHA256SUMS, prepares the 4 root `job.json` copies rewriting
**only** `out` and `base_url`, recomputes the B2 configuration `binding` exactly as the B2 code does, prepares a clean
paper checkout at the B2 HEAD `8709dce7` plus a detached worktree carrying the reviewed label patch, **pre-flights the
exact B2 authorization gates** the campaign driver will call, and only when every gate passes starts ONE owned
llama-server (the 32k exam setting) and runs the 4 root campaigns sequentially, requiring rc 0 and a complete
`campaign_manifest.json` per root. It then writes `job_record.json`, `out.tar`/`work.tar` + `SHA256SUMS`, and the
operator seals the transferred output with the S2-C2 seal guards.

| file | role |
|---|---|
| `sweep2/s2_c3_replay.py` | spec validation, pinned-input verification, byte-scoped job.json rewrite, B2 binding recomputation, paper/harness checkouts, label patch apply + scope check, exact B2 authorization-gate preflight, owned server + 4 sequential root campaigns, job record/package, `seal` |
| `sweep2/s2_c3_replay_job.sh` | container entry point (pre-creates the transferred outputs, runs the driver) |
| `sweep2/render_jdl.py` | extended to dispatch `s2_c2_job/v1` (unchanged) and `s2_c3_replay/v1` (stages the 31 transfer inputs + renders the fixed JDL) |
| `sweep2/s2_c3_compare.py` | applies the pre-declared criteria 1–6 to the three job outputs, verifies the expected-value source pins, writes `S2_C3_RESULTS.md`, hard STOPs on missing/duplicate instances, label leak, pin mismatch, audit-seed mismatch |
| `sweep2/s2_c3_label_patch.diff` | reviewed label patch (sha256 `fd0234c9579b293cdb7db259303e1ef86dffdd6a7e8ed3360f04227badddf741`) |
| `sweep2/spec.replay.example.json`, `sweep2/spec.replay.openml_credit_approval.json`, `sweep2/spec.replay.openml_ionosphere.json` | the three per-node replay specs |
| `sweep2/dryrun/replay/` | rendered JDL + staged transfer inputs (real `condor_submit -dry-run` pending on the submit host) |
| `sweep2/evidence/s2_c3_preflight_local_20261116.txt` | raw local preflight capture (dev host, NOT a job run) |
| `r1/tests/htcondor/test_s2_c3_replay.py` | 100 synthetic tests (no GPU/network/HTCondor) |

## 2. Pinned inputs (verified before and after the rewrite)

All 24 pinned files (12 roots × `job.json` + `campaign_manifest.json`) are staged flat as `S2C3_IN_*` and verified
against the pinned `SHA256SUMS` (sha256 `6224b75a4d4aec9ac2f289cf913e19cbb814263a9e7d0e7b381122695d0cadf6`):

- root set is exactly `{digits_mlp, openml_credit_approval, openml_ionosphere} × seeds 9011–9014`;
- each `job.json`: `phase=b2`, `mode=off`, `dryrun=false`, `W=20`, `workers=20`, `llm_call_cap=80`,
  `harness_commit=a3fedbb…`, `authorization_checkout_head=8709dce7…`, `audit_seeds=[9201…9210]`,
  `binding=c502a9aa…`, candidate `gemma4_31b` thinking-off with GGUF `2959c1b0…`, and an `authority_config` that is
  **byte-identical (JSON-equal) to the committed `r1/scripts/configs/exam_b2_v2.json` at `8709dce7`**;
- any reserved B.2 audit seed 7001–7010 anywhere is refused; no B.2 audit runs.

## 3. `job.json` rewrite — only `out` and `base_url`

The pinned files are in the B2 `write_json(indent=2)` canonical form. The driver re-serialises the parsed object,
proves the round-trip is byte-identical, then re-serialises with exactly two values changed and **line-diffs the two
texts**: exactly two lines may differ, and their keys must be `out` and `base_url`. Anything else (an extra change, a
non-canonical input) is a STOP. The rewritten file is written to `<sandbox>/out/<root>/job.json` because the B2
campaign binds `campaign_manifest.job_sha256 = sha256(out/job.json)`; the staged originals are re-verified afterwards.

## 4. `binding` and `authorization_checkout_head` — the exact B2 method

B2 computes the configuration binding in `ExamRunner.__init__` (`r1/exam/runtime.py` @ `8709dce7`):

```
binding = sha256(json.dumps({'config': cfg,
                             'registry_sha256': sha256(registry snapshot),
                             'rule_sha256': cfg['rule_sha256'],
                             'value_grids_sha256': sha256(value_grids)}, sort_keys=True))
```

The batch registry snapshot is a byte copy of the committed `cfg['registry']` at the run HEAD, so the committed blobs
reproduce it. The driver reads `r1/scripts/configs/exam_b2_v2.json`, `r1/exam/rules/x5_rule_v2.yaml` and
`r1/exam/value_grids.yaml` from `8709dce7` via `git show`, checks the rule digest equals the recorded
`rule_sha256`, and recomputes to **`c502a9aa…` — equal to all 12 recorded bindings and to the spec pin**
(`sweep2/evidence/s2_c3_preflight_local_20261116.txt`). `out` and `base_url` are **not** binding inputs, so the
sandbox rewrite provably cannot change it; the driver re-verifies every recorded `job.json` binding against the
recomputed value. A different config/registry/rule/grids value is a STOP.

`authorization_checkout_head` is the paper HEAD the B2 authorization binds (`8709dce7`). The driver clones the paper
repo at that exact commit and verifies **HEAD == `8709dce7` and `git status --porcelain --untracked-files=all` is
empty**, and that the committed B2 authorization note is present, before and after the label patch. The campaign's
`require_committed_b1_config` gate therefore sees exactly the pinned authorization checkout.

## 5. Label patch — method, scope, sha record

`execution_label` is hard-coded inside `_collect_b1_review`; the reviewed patch replaces that one line with
`'ENGINEERING_ONLY'`, adds `'replay_marker':'s2_c3_replay/v1'`, and refuses a DRYRUN job. It changes no trial or
audit logic. `check_patch_scope` enforces this mechanically: the diff may touch only `r1/exam/campaign.py`; every
removed line must be an `execution_label` line; every added line must be the ENGINEERING_ONLY/marker line or the
DRYRUN guard; any `def `/`run_config`/`audit`/ledger/`final_audits` change is a STOP.

**Why the patch is applied to a detached worktree, not to the authorization checkout:** committing (or leaving dirty)
the patch in the pinned checkout would change HEAD or the worktree state, and the very next campaign gate
(`require_committed_b1_config`: clean checkout, HEAD == the job's `authorization_checkout_head`) would then STOP the
replay. The driver therefore applies the patch in a `git worktree` of the same pinned commit, records the original and
patched `campaign.py` sha256 (`014b1a8a…` → `33feb320…`) and the patch sha256, and runs `r1.exam.campaign` with the
patched source **shadow-executed in the module namespace** (same `python -m r1.exam.campaign` code path, same
`__file__`/REPO, same trial/audit code). This is not an authorization bypass: the authorization basis is still the
clean pinned commit and the patch is declared, pinned and reflected in every manifest.

The driver then requires every campaign manifest to carry `execution_label=ENGINEERING_ONLY` **and** the replay
marker; anything else (EVIDENCE, DRYRUN, a missing marker) is a label-leak STOP, and the comparison re-checks it.

## 6. STOP — the pre-declared protocol cannot execute the unmodified B2 driver off TASL (author decision needed)

The driver implements the full run path, but its preflight evaluates the *same* B2 functions the campaign calls
(`_verify_b1_worker_input`, `host_check`, `require_worker_host`, harness binding) plus deterministic environment checks,
and **refuses before fetching the model or starting the server** if any of them would refuse. A local capture
(`sweep2/evidence/s2_c3_preflight_local_20261116.txt`; dev host, not a job) shows the blockers that would stop the
campaign on NEMO2:

1. **Stage A authorization inputs are TASL-side files** — `exam_b2_v2.json` points `stage_a_table` /
   `stage_a_amendment_table` at absolute `/home/dowling/exam-x/work/r1_stagea_*/…`; they are not in the repository and
   not shipped, so `author_gate → _committed_b2_authority` raises `FileNotFoundError` and would STOP the campaign.
2. **The B2 exam-host gate is hard-coded** — `host_check` accepts only `TASL-2`/`TASL-7`, requires
   `cfg['host'] == platform.node()`, `models_dir`/`work_dir` at `/home/dowling/exam-x/...`, and
   `out` under `cfg['work_dir']`; `require_worker_host` repeats the host pin. A NEMO2 L40S slot cannot satisfy this.
3. **The pre-declared `out` rewrite is itself incompatible** — rewriting `out` into the job sandbox violates the B2
   `out under /home/dowling/exam-x/work` check. This is structural: it would fail even on TASL-7.
4. **OpenML nodes need TASL-side data** — the campaign requires the verified
   `experiments/r1/pilot/L8_20261009T152916Z/nodes/<node>/data_cache` (untracked harness data); it is not in the
   harness commit and a fresh clone stops with “missing verified OpenML cache”.

**The pre-declared protocol allows only a label patch (“it changes no trial/audit logic”), so none of these gates was
bypassed.** P4 is therefore blocked pending an author decision: either (a) a separately reviewed **replay authorization
/ replay patch** that declares the NEMO2 host/path substitution *and* where the Stage A tables and OpenML caches come
from (sha-pinned, transferred as job inputs), or (b) run the check elsewhere. The driver is ready to execute once such
a decision is pinned; the preflight re-evaluates it with no code change beyond the reviewed patch sha.

**Shadow-exec scope limitation (for the author-decision path):** the driver shadow-executes only
`r1/exam/campaign.py` (the file the pinned label patch touches); `r1/exam/runtime.py` — where `host_check` and the
committed-config gate live — is imported from the pinned checkout and is *not* shadowed. A future replay-mode decision
that has to change `runtime.py` would therefore need a reviewed extension of this mechanism (and its own pin), not just
a bigger `campaign.py` patch. This is recorded rather than implemented, to keep the pre-declared “label-only patch”
boundary intact.

## 7. Pre-declared criteria defect (must be fixed before any replay data exists)

Criterion 3 is declared as “invalid/duplicates/noops each within ±10 % of B2's **58/82/58 over the 12 roots (480
trials**, 480 evaluated …)”. The 480-trial / 58-82-58 figure is the **24-root candidate batch** (thinking-off + the
descriptive thinking-on rerun); the replay is the **12 thinking-off roots = 240 trials**, whose pinned B2 totals are
**invalid 20, duplicates 33, noops 20** (verified from the SHA256SUMS-pinned manifests; also `b2_manifests.json`
`gpu_hours=0.504917` confirms the 12-root off basis for criterion 5). Applied **exactly as written**, criterion 3 would
be NOT PASS for a correct replay. This comparison **applies the declared numbers unchanged** (no post-hoc relaxation)
and reports the defect automatically in `S2_C3_RESULTS.md`; only the author may amend the pre-declaration, and only
before a run. **Recommendation: amend criterion 3 to the 12-root off-root totals (20/33/20) before P4.**

## 8. What cannot be verified without the real run

Every criterion 1–6 value, the server's real offload line (expected 61/61 at the B2 setting), the actual wall time,
parse failures, the label as emitted by a real campaign, and the sealed `/ceph` receipt. The unit's synthetic tests
prove the machinery and the arithmetic only; they are not a deployment result. In particular the run path after a
passing preflight (owned 32k server + 4 sequential `r1.exam.campaign` roots with the label patch) is implemented and
reviewable but has never been executed, and criterion 3's pre-declared denominator is internally inconsistent (§7).

## 9. Exact execution steps (3 jobs) — **not done here; do not submit before the §6 decision**

After the author decision and the review of this unit:

1. On the submit host (deepthought), from the repo at the branch carrying this unit:
   `python3 sweep2/render_jdl.py sweep2/spec.replay.example.json --out sweep2/dryrun/replay/s2_c3_replay_job.jdl --stage-dir <stage-digits>` (fresh dir) and likewise the two `spec.replay.openml_*.json` specs;
   then `condor_submit -dry-run` each and compare with `sweep2/dryrun/replay/README.md`.
2. Submit the three jobs (one per node; no more). Expected first outcome after the current §6 STOP is a fast STOP in
   the preflight with the blocker list, **before** the model/server; keep every sandbox.
3. On completion, copy the three job-output directories and seal each:
   `python3 -m sweep2.s2_c3_replay seal <job-output> --run-id s2c3-<stamp> --chunk-id <node>` → sealed under
   `/ceph/srv/dwong/paperb/sweep2/s2c3-<stamp>/<node>/` with `ENGINEERING_ONLY.txt`, `SEAL_RECEIPT.json`, `SHA256SUMS`.
4. Compare: `python3 sweep2/s2_c3_compare.py <job1> <job2> <job3> --out S2_C3_RESULTS.md` → `PASS`/`NOT PASS` per
   criterion, per-instance table, the criterion-3 defect disclosure; independent review before any EVIDENCE claim.
5. Only three jobs, one per node; no retries (a nonzero root / missing manifest / label leak / pin mismatch is a STOP
   for the whole check; retain everything).

## 10. STOP list (in addition to the runbook §4 STOPs)

- Any spec pin differs from the pre-declared constants; any attempt to select EVIDENCE/DRYRUN or another label.
- Staged inputs do not match the pinned SHA256SUMS, the rewrite changes anything but `out`/`base_url`, or the staged
  originals change during preparation.
- Recomputed binding ≠ recorded/spec binding, committed config ≠ recorded `authority_config`, or the authorization
  checkout is not clean at `8709dce7`.
- The label patch does not apply cleanly, touches anything outside the execution label/marker, or its sha differs.
- Any B2 authorization gate refuses (the preflight STOP in §6) — **never bypassed**.
- Nonzero root rc, missing/incomplete `campaign_manifest.json`, missing replay marker, any `execution_label` other than
  ENGINEERING_ONLY, reserved seed 7001–7010, audit seeds other than 9201–9210, or a mismatched pin.
- Any `out.tar`/`work.tar`/`SHA256SUMS`/seal guard failure; an existing sealed target is never overwritten.

## 11. Tests and no-execution disclosure

`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/sweep2-cluster-20261116/.venv-test/bin/python -m pytest
r1/tests/htcondor/ -q` → **132 passed** (100 new S2-C3 tests + the 26 S2-C2 and 6 S2-C4 tests unchanged). No GPU, no
network, no HTCondor, no `/ceph`; the seal tests monkeypatch the sealed root. No labels were read and no B.2 audit ran
in this unit.

## 12. Dry-run JDL

`sweep2/dryrun/replay/s2_c3_replay_job.jdl` (+ the 31 staged transfer-input files) was rendered and the spec validated;
`condor_submit` is **not installed on this machine**, so the real `condor_submit -dry-run` must be performed by the
deepthought operator (exact command and expected ad in `sweep2/dryrun/replay/README.md`). Nothing was submitted.
