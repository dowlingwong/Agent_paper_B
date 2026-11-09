# B1 STOP diagnosis — partial (9 Nov 2026, Mac-local overnight agent)

**Status.** AI-assisted (Claude, overnight session under `MAC_LOCAL_RUNBOOK_OVERNIGHT_20261109`). Partial: the data steps of the plan could not run tonight. Not a classification, not a gate change, no restart. The STOP report `reports/B1_STOP_6835_20261108.md` stays authoritative. Plan: `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` (commit `1d517b79`, cherry-picked onto this branch).

## 1. Why this is partial

The overnight session ran in a sandbox on the Mac with the repository mounted, but **without SSH to TASL-7** (no `~/.ssh`, host name not resolvable) and **without access to the accepted descriptive capture** under `/private/tmp/paper-b-stop-anchor-descriptive-20261108.SuozFFd5/` (folder access to it was refused by the session's permission check). No anchor value of run `6835_20261108_a` was available. So D0, D1, D2, D3 (values), D4, D7 and D8 are **not computed**. Nothing on the host was contacted, read, signalled or changed.

What was done instead:

1. The static steps D5 and D6 and the σ constants for D3 (sections 2–4).
2. A read-only diagnosis reader for all of D0–D8, extending the accepted descriptive reader, with synthetic known-answer tests (section 5). It is ready for one run by a session that has SSH, after independent review.
3. A local mode of the same file that computes D1 and the D3 means from the already accepted descriptive capture on the Mac, with no host contact (section 5). This is the fastest way to D1.

## 2. D5 — metric orientation (static)

| Node | Metric | Direction (harness `configs/nodes/*.yaml`, `origin/r1` `897d83c`) |
|---|---|---|
| `digits_mlp` | `val_score` (validation accuracy) | maximize |
| `openml_credit_approval` | `val_auc` | maximize |
| `openml_ionosphere` | `val_auc` | maximize |

`delta_audit` is `mean(candidate − incumbent)` over the audit seeds (`r1/c3/audit.py::paired`, frozen `68357d3d`), so a positive value is an improvement on all three nodes. `anchor_gate` calls `paired_instance_bootstrap(scripted, random_valid)`, so `difference = scripted − random_valid` and the gate needs its lower bound above 0. No sign error is visible in the paper-side code.

**Limit.** The harness pin `a3fedbb` is not in the local harness clone (99 commits; `git cat-file` fails), so the direction was read from `origin/r1`, not from the pin. A session with the pin should confirm the three YAML files there.

## 3. D6 — anchor-path code between the accepted exam checkout and `68357d3d` (static)

Base: `exam-x-20261026` @ `8a819f75` (the exam code accepted in `EXAM_1_REVIEW_20261026.md`; it is also the merge base with `68357d3d`).

| Component | Change | Bearing on the anchors |
|---|---|---|
| `r1/headroom/scripted_manager.py` (`scripted`) | **unchanged** (blob `1f1af532`) | proposal law unchanged: one numeric symbol × log-uniform factor in [1/3, 3]; 30 % categorical switch on OpenML |
| `r1/exam/value_grids.yaml` (`random_valid` grid) | **unchanged** (blob `c29138a4`, SHA-256 `7ab60c16…b1ea14`) | value grid unchanged |
| `autoresearch.manager.random_valid` (`random_valid` law) | in the harness pin `a3fedbb`, **not inspectable here** | open |
| `r1/exam/guards.py` (bootstrap) | unchanged | gate statistic as accepted |
| `r1/exam/campaign.py` | +231 lines: `LocalWorker` → `B1IntegrityWorker` (`b1_proposal_guard.py`, new); `run_config(..., preserve_node_outputs=True, stop_on_invalid=True)` for audits; `preserve_pinned_editables` wrapper (`b1_editable_preserve.py`, new); OpenML cache guard (`b1_openml_cache_guard.py`, new); job/config binding checks | could change which edits run or are counted invalid (H4); needs D0/D2 counts to judge |
| `r1/exam/runtime.py`, `r1/scripts/exam_runner.py` | +682 / +443 lines, mostly B1 orchestration, leases, preservation, STOP handling | `anchor_gate` itself unchanged in logic |

So the two anchors' proposal laws (paper side) and the gate statistic are the ones accepted on 26 Oct; what is new is the worker wrapper, audit options and guards around them. That leaves H4 open until D0/D2 show the invalid, no-op, duplicate and audit counts.

## 4. D3 — σ_node used for standardisation

From the committed D21 noise floor `docs/r1/reports/NOISE_FLOOR_COMMON_20261022.md` (commit `511c3797`, file SHA-256 `9be292b773799d1591e55ea6845551a8fa121b00ec1a0dfe324b2c46de52c01d`), Table 1, 30 seeds per condition:

| Node | σ_joint [95 % CI] | median paired sd(Δ̂) |
|---|---|---|
| `digits_mlp` | 0.0102 [0.0081, 0.0137] | 0.0066 |
| `openml_credit_approval` | 0.0279 [0.0222, 0.0375] | 0.0030 |
| `openml_ionosphere` | 0.0410 [0.0327, 0.0551] | 0.0160 |

The reader reports D3 means divided by both. σ_joint is the primary choice because the B1 audits vary the seed; the paired sd is shown because `delta_audit` is itself a paired difference.

**Descriptive context only (not a test).** The accepted descriptive review gives per-root mean `delta_audit` within about [−0.0166, +0.0148] for `random_valid` and [−0.0028, +0.0013] for `scripted`. Every one of these is smaller than σ_joint of the noisiest node (0.041) and most are smaller than σ_joint of `digits_mlp` (0.0102). Both anchors' typical increments are near zero on the noise scale, which fits H1 (two random proposers) and H3 (low power on 12 pairs) better than a sign error. This is a reading of ranges, not of the paired values; it does not classify the STOP.

## 5. The diagnosis reader (ready, not run)

`docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py`, SHA-256 `13ad5a53efed9acd0ffc5bb12c8424c56d47a2f3b845814147761ecd78e2ee05`.

**Host mode** (no arguments). Same boundary as the accepted descriptive reader (fixed root, `O_NOFOLLOW` path walk, `O_NOATIME` with no fallback, owned regular files, identity unchanged during each read, duplicate JSON keys and non-finite numbers refused). Extensions:

- reads all **three** anchors (36 roots); for each root validates the job (HEAD `68357d3d`, B1, node, instance seed, audit seeds 9101–9104 in job and config, rule hash, W = 20) **before** opening the manifest; checks the manifest against the batch-state SHA and the job SHA; then reads `root_trials.jsonl` only after matching it to the manifest's `evidence_hashes`;
- D0: per proposal, `k = 4`, no missing seed value, and `delta_audit` equal to the mean of the stored candidate − incumbent vectors (mismatches are counted, not hidden); proposal IDs must be `EXAM:<node>__s<seed>:t<bbb>`;
- D1: the gate recomputed with a port of the frozen `paired_instance_bootstrap` (a test asserts equality with `r1/exam/guards.py` on random inputs), plus the 12 per-instance differences, raw and divided by σ_joint;
- D2: trials, evaluated, invalid, duplicates, no-ops, parse failures, audited count, keeps, worker runs, termination, mean in-run incumbent gain;
- D3: mean, median, share harmful, and both standardised means, for `random_valid` and `scripted`;
- D4: the same for budget index ≤ 10 vs > 10;
- D7: summed qwen duplicates / evaluated against [0.4239, 0.5800] (as `anchor_gate` sums them over roots);
- D8: the D3 numbers for `qwen25_coder_7b`, information only.

It outputs nothing until all 36 roots validate, prints `DIAGNOSIS_CAPTURE_COMPLETE` at the end, and never prints raw per-seed metric vectors (only per-proposal budget index and `delta_audit`). No 7006–7010 file is opened.

**Local mode** (`--descriptive-capture <ssh.log>`, on the Mac). Reads the one JSON line of the accepted descriptive capture, requires exactly the 24 expected rows and the completion marker, and computes D1 (each root is one instance, so the root mean is the cluster mean the gate uses) and the D3 node means raw and over σ_joint. It contacts no host. Command:

```bash
python3 -I -B docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py \
  --descriptive-capture /private/tmp/paper-b-stop-anchor-descriptive-20261108.SuozFFd5/ssh.log \
  > /private/tmp/b1-stop-d1-local-20261109.json; echo "rc=$?"
```

**Tests.** `r1/tests/test_b1_stop_diagnosis_synthetic.py` (SHA-256 `fff106d5…798b`): 8 tests, all passing with the 4 existing descriptive tests (12 passed) under Python 3.11 on Linux, where `O_NOATIME` is real: known-answer D1/D2/D4/D7 values; a negative difference reproduces the STOP; a duplicate rate outside the interval is flagged; bootstrap port equals the frozen guard; a 7006–7010 job seed stops before that manifest is opened; a `root_trials` hash mismatch refuses; an inconsistent `delta_audit` is counted; the local mode computes D1 and refuses a capture with 23 rows.

**Host wrapper (paste-ready, run once, only after independent review of this exact file).** Same pattern as the accepted descriptive wrapper, with exit code captured to the log and a separate `.rc`:

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
SCRIPT=<worktree>/docs/r1/proposals/B1_STOP_DIAGNOSIS_20261109.py
EXPECTED=13ad5a53efed9acd0ffc5bb12c8424c56d47a2f3b845814147761ecd78e2ee05
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED" ] || exit 1
CODE=$(python3 -c 'import base64,sys;print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$SCRIPT") || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-b1-stop-diagnosis-20261109.XXXXXXXX) || exit 1
set -C
exec 3> "$OUT/ssh.log"
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
if ssh -n -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=3 tasl7 "exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /usr/bin/python3 -I -B -c 'import base64;exec(base64.b64decode(\"$CODE\"))'" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nSSH_EXIT=%s\n' "$rc" >&3 || exit 1
printf '%s\n' "$rc" > "$OUT/ssh.rc" || exit 1
shasum -a 256 "$SCRIPT" "$OUT/ssh.log" "$OUT/ssh.rc" || exit 1
[ "$rc" -eq 0 ] || exit "$rc"
grep -qx DIAGNOSIS_CAPTURE_COMPLETE "$OUT/ssh.log" || exit 1
printf 'PRELIMINARY_RECEIPT_FOR_INDEPENDENT_REVIEW=%s\n' "$OUT"
```

Under `exec(...)` the script's `__name__` is `__main__` and `sys.argv` is `['-c']`, so host mode runs. Python on TASL-7 must provide `O_NOATIME` (it did for the descriptive run).

## 6. Hypotheses — status tonight

| # | Status | Why |
|---|---|---|
| H1 design | undetermined; descriptive ranges point this way | both proposal laws unchanged since 26 Oct and both random; no anchor values |
| H2 metric | undetermined | needs D2 keeps and D4 halves |
| H3 power | undetermined; descriptive ranges point this way | increments are small against σ_joint; no paired values |
| H4 engineering | undetermined | anchor proposal code and gate unchanged; new worker/audit wrappers need D0/D2 counts; `random_valid` manager at the harness pin not inspected |

**Classification (plan §4): not possible tonight.** D7 is also not evaluated. Under the runbook, Task 1 stops here; the question for the author is in `reports/MAC_OVERNIGHT_QUESTIONS_20261110.md`.
