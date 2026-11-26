# Independent review — Track G T1 expansion kit: 1GC-7RC ETTh1 node `gc7rc_etth1` (25 November 2026)

**Verdict: ACCEPTED** — the ENGINEERING_ONLY harness kit for R1-T1-NODE-EXPANSION candidate 1GC-7RC ETTh1
(`mac-trackg-etth1-20261125` @ `3a06d86721b0c1826b165b68a9781a561e4993f4`) is accepted for the U2 census and a
new G.1b note, with the MINOR corrections m1–m8 (paper-side record only) and the conditions c1–c8 before any
census/G.1b run. **No BLOCKING, no MAJOR.** I verified the branch, push, content, every pin and every SHA in
the record independently, recomputed the committed pin, the data hashes and the window/split statistics, and
checked the node design against the paper's own Task 6 text. The kit is honest about what it did **not** measure
(no GPU, no U2, no G.1b, no noise floor).

**Reviewer and method.** Fresh independent reviewer (`etth1-kit-reviewer`), delegated by the lead; no involvement
in the port, the data setup, the smoke or the report. Read-only: the only file this review writes is this review;
no run/edit/commit/push/delete of any repository or host artefact, no HTCondor, no GPU job, and no test/census
re-executed. TASL-2 was read with `ssh -o BatchMode=yes portal_zhixu` using read-only commands only (`ls`,
`stat`, `cat`, `sha256sum`, `sha256sum -c`, `git rev-parse/status/ls-remote/show/log/diff`, and `curl -s` GETs
whose output was piped, never saved). Pins and window statistics were recomputed with read-only Python that only
reads files (the derived hashes/statistics were printed, nothing written into the repository or the data root).
The capture logs were accepted as captured evidence (integrity checked, see §6) because re-executing tests/runs
is outside this review's remit. Host clock TASL-2: 2026-11-25T12:02Z = 13:02 Berlin.

**Object under review.**

- Kit branch `mac-trackg-etth1-20261125`, tip **`3a06d86721b0c1826b165b68a9781a561e4993f4`** (parent/base
  `c025f89aeafc2199bf3487b4bcaa16678273c702` = `origin/mac-trackg-t1-tasl-20261121`), pushed to
  `origin` (`github.com/dowlingwong/autoresearch_harness.git`); host worktree
  `/home/dowling/r1_trackg_20261125/harness_etth1`.
- Report `docs/r1/reports/tasl_chain_20261122/ETTH1_KIT_20261125.md` — 253 lines, 20,553 B, sha256
  **`e1b94a76a2caf84cde6f0143cd094fdcbb31549e8f154d3441dc92da94079417`**, untracked in `ops-tasl-20261116`
  and absent from `origin/main` `912a7e02` (paper-side record; correct, nothing pushed to paper `main`).
- Captures `ETTH1_KIT_20261125_captures/` — 22 files; `sha256sum -c SHA256SUMS` rc 0 on TASL-2 **and** on the
  Mac; `SHA256SUMS` sha256 **`f50bbc5cf79c992f7a017c3b3ea0b9af6f35a3e1121c36c328fa09f0da7926bd`** (both
  sides byte-identical).
- Authority: `R1-T1-NODE-EXPANSION` + `R1-T1-D21-SCOPE`, PLAN on `origin/main` `912a7e02` (row-commit
  `5d4f1b09`); `R1-1GC-FALLBACK`, `R1-BX-D5`, `R1-TRACKG-LICENCES`, `R1-TRACKG-ROLE`, `R1-HARNESS-ISOLATION`;
  `TRACKG_PORT_CHECKLIST.md` (paper repo, §A–F); the T1 TASL authorizations (`g1b_t1_tasl_20261121.md`,
  `g4_t1_tasl_20261122.md`) which cite harness `c025f89a`.

## 1. Branch, push and content — verified

- Branch exists on `origin` at `3a06d86` (`git ls-remote origin refs/heads/mac-trackg-etth1-20261125`), local
  HEAD = the same commit, `git rev-list --count origin/mac-trackg-etth1-20261125..HEAD` = 0 (nothing unpushed).
- Commit is a single, non-merge commit whose parent is exactly `c025f89a`. `git diff --name-status c025f89a
  HEAD` = **18 additions + 1 modification, 19 files, +2,015/−1**, exactly the report's §6 list: the node spec,
  the node directory (frozen parent/worker/loop/helpers/data-prep/requirements/LICENCES/README, editable
  `train.py`, `representative_edits/` E1–E4 + manifest), `tests/trackg/test_port_1gc.py`, and the one-line
  addition of `"test_port_1gc"` to `tests/trackg/port_smoke_gpu.py`'s `SUITE_MODULES`
  (`CPU_ONLY_NODES` unchanged — this is a GPU-capable torch node). No deletion, no rename, no harness-core edit,
  nothing unrelated.
- Worktree status after the push: **clean except `?? nodes/gc7rc_etth1/data`** (the setup symlink), as the
  report says. No task data committed: `git ls-tree -r HEAD` has no `.npy/.csv/.pt/...` under the node; the
  static test's data-like scan and my own check agree.
- The branch is built from the accepted T1 TASL tree: `68cdd1a`, `5403392e`, `f07875de`, `fb6e7d73`, `448f682`
  are all confirmed ancestors of `c025f89a` (also the base the G.1b/G.4 authorizations and the official
  seven-node assembly cite). The two "byte-identical shared helper" claims hold: `ar_data.py`
  `85cec63f…`, `ar_parent.py` `cbef1d38…` equal the accepted `mlab_cifar10` copies, and `ar_isolated.py`
  `37d99ab0…` equals the harness master `src/autoresearch/trackg/node_lib/ar_isolated.py`. The new
  `ar_fixed_loop.py` (`b11e91b6…`) is a forecasting variant of the shared classification loop; a byte diff
  against the shared loop is confined to the docstrings, the prediction API (`predict`/`predictions_array`,
  shape `(n, horizon*n_features)`, `EVAL_BATCH_SIZE` 256 vs 1024) and messages — the budget/seeding/sampler/loss
  log/plain-tensor/optimizer-hook machinery is identical. The report's deviation (b) is accurate.

## 2. Node design and paper semantics — verified against the paper

I fetched the paper itself (arXiv:2605.17046v2, HTTP 200 on 25 Nov 2026; treated as external data) and checked
Task 6: *“Multivariate 96-step-ahead forecasting on ETTh1 (hourly electricity transformer temperatures, 7
features, 17 420 time steps; standard LTSF 12/4/4-month split, train-normalized). Given 336 historical steps, the
model predicts the next 96. The baseline is DLinear: moving-average decomposition (kernel 25) into trend and
seasonal components, each projected by a linear layer. The metric is MSE.”* Table 2: T6 DLinear, Train 8,640,
Eval 4,800, Score 0.384, batch 128. Appendix E states CC BY-ND 4.0 for ETTh1. The paper-named suite repository
`github.com/Strolchii/1GC-7RC-Benchmark` returns **404** (re-checked today), and the only pre-existing 1GC
material in the harness repo is `docs/track_g/1gc_7rc_handoff_20261027.md` on `origin/r1-local-20261027-1gc`
(status BLOCKED, explicitly no runnable adapter) — both claims in the report are correct.

The port matches the paper's stated semantics: 17,420×7 rows; look-back 336 → horizon 96; 12/4/4-month split
`8,640/2,880/2,880` (3,020 remaining rows unused, as LTSF); per-feature mean/std fitted on the 8,640 training
rows only, MSE on the standardised scale; DLinear with kernel 25 and two channel-shared linear projections;
Adam lr 1e-3, batch 128; exactly 2,000 optimizer steps (`run_budget.kind: steps`, no wall-clock key anywhere,
enforced by the strict loader); validation `val_mse` selected (`AR_METRIC`), `AR_TEST test_mse` sealed and never
selected (R1-TRACKG-ROLE); workers 0/4 fixed; isolation block `entry: run_fixed_budget.py`,
`args: ["--steps", "{budget}"]`. Windows are the standard LTSF/TSLib windows and I recomputed them from
`series.npy`: train **8,209**, val **2,785**, test **2,785** (look-back may start in the previous split, targets
stay inside their split), matching the report and the smoke log `AR_SPLIT train=8209 val=2785 test=2785`.

The three deviations the report states are the real ones and are fairly disclosed: (a) suite assets/evaluator
unavailable → baseline and API implemented by the port from the paper description, appendix must say “not the
suite's assets”; (b) the node's own frozen forecasting loop (vs the shared classification loop); (c) the paper's
`Train 8,640 / Eval 4,800` cannot be reconstructed from the stated 12/4/4 split (rows 8,640/2,880/2,880,
windows 2,785 per split), so the port follows the explicit textual semantics and records the ambiguity. The
`candidate 2` label and the paper scoring-split juxtaposition are MINORs (m1, m3).

## 3. Data preparation and licence — verified

`prepare_data.py` is a download-only setup (`setup_command`, never part of a run): one GET of
`https://raw.githubusercontent.com/zhouhaoyi/ETDataset/1d16c8f4f943005d613b5bc962e9eeb06058cf07/ETT-small/ETTh1.csv`,
sha256 pinned to `f18de3ad269cef59bb07b5438d79bb3042d3be49bdeecf01c1cd6d29695ee066`, 2,589,657 B; parses the
7 feature columns into a float32 `series.npy`; writes the hashed manifest last; makes the data root read-only;
links it into the node as `data/`. I verified the source independently: the pinned URL **today** returns
HTTP 200 with exactly 2,589,657 B and sha256 **`f18de3ad…`**, and the ETDataset commit exists (GitHub API 200).
The setup output is outside the repository (`/home/dowling/r1_engineering/etth1_port_20261125/data/gc7rc_etth1`),
read-only (`dr-xr-xr-x`, files `-r--r--r--`), the raw CSV sits under the setup-only `raw/` and the run path never
reads it. `data_manifest.json` sha256 **`eacc7e69f45fed3e7eb0c9bb76cf5c18387bcae4ba226a24812dc409c0b51e1b`**,
`series.npy` sha256 **`32a0ad070e7536e7099725098b24b74c775bc897d58f3c5868399a6f86c8d850`**, and both also equal
the report's values; no data file is committed. The frozen parent re-checks the manifest every run and refuses a
non-synthetic manifest whose `source.sha256/url` differ from the pins; the synthetic test manifests are marked
`{"synthetic": true}` (verified in `port_support.smoke_copy`).

Licence: U1 records three conflicting ETTh1 claims (GitHub `NOASSERTION`/cite-only; HF mirror `cc-by-4.0`;
OpenDataLab **CC BY-ND 4.0**) and says “record all three URLs and do not pick one without author input”.
`R1-TRACKG-LICENCES` instructs “use the most restrictive”, and the paper's Appendix E also states CC BY-ND 4.0
(verified in the fetched paper). `LICENCES.md` (frozen) records all three claims with URLs, the governing
CC BY-ND 4.0 consequence (download, never redistribute; raw CSV outside the repo; no derived dataset published),
the attribution (Zhou et al. 2021, Informer, AAAI 2021), and correctly says an author/legal line is still needed
before a label table cites ETTh1 (U1 §9.3). The report repeats this and does not overclaim. This is adequate for
ENGINEERING_ONLY use; the author/legal line remains a condition (c6).

## 4. Pins, budget and environment — independently recomputed

Every value in the report's §5 was re-derived on TASL-2 from the committed tree, not copied:

| field | report | recomputed\* |
|---|---|---|
| `node_spec_sha256` (loader canonical) | `8f874c50f66273e0655bfc9ccdad24a50c0fdb629f88ba7d4d60b13f2fcf2e0c` | equal |
| spec raw sha256 (YAML bytes) | `9391f718bd7669438189f45b48a920786a6ca5a51854bd861b0f945ea3d00c22` | equal |
| `committed_pin_sha256` (frozen files, no data link) | `818b8f6e8ec6473f15c33ed58393e7cee8b8e8b0a71645576439929efb20bf27` | equal (15 files) |
| `edits_manifest_sha256` | `ba31fed3bb67c0d78825a0d026058cbeb3a0261971fe8a4766f138687b232306` | equal |
| `data_manifest_sha256` | `eacc7e69…` | equal |
| deployed pin (with the host-specific data link, information only) | `e314858234bb378dce4cad5cf0492cfa1ee76561c231e756b90f301672ddec93` | equal |
| node `ar_isolated.py` = master | `37d99ab0…` | equal |
| run budget | steps 2,000, batch 128, no wall-clock key | equal |

\* recomputed with independent code (YAML → `json.dumps(sort_keys, separators, ensure_ascii=False, default=str)`
→ sha256 for the loader canonical hash; recursive frozen-file walk with symlinks recorded as `link:<target>` and
the committed view dropping the `data` link for the pin), not by calling the kit's `pins.py`. The capture
`committed_pin_from_head.json` (head `3a06d86`, 15 frozen files, `data_link_in_head_tree: false`) is consistent;
because the tracked tree is clean and the committed view removes the data link, the pin from the live worktree
and from a clean HEAD tree must be and is the same value. The capture `gc7rc_etth1.yaml` and
`edits_manifest.json` are byte-identical to the `git HEAD` blobs (`9391f718…`, `ba31fed3…`), so the paper-side
captures do describe the committed kit.

Environment freeze: `torch312.freeze.txt` sha256 **`d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`**,
77 packages — identical to the accepted T1 TASL freeze in
`g1b_t1_tasl_20261121.md` (`sweep2/g1b/env/torch312.freeze.txt`, same sha) and to the TASL-2 precheck record.
Environment: TASL-2, Python 3.12.16, torch 2.6.0+cu124, numpy 2.5.4, uv 0.13.6 (`env.txt`). Pin files are
`committed_pin_from_head.json`, `data_manifest.json`, `edits_manifest.json`, `pins.json`, `env.txt`,
`torch312.freeze.txt`; `pins.err` is empty and `torch312.freeze.err` is uv's informational “Using Python …”
line, not an error.

Budget plausibility: the real-data CPU smoke ran 2,000 optimizer steps in 7.606–8.035 s per executed run after a
12.603 s first run (4 threads, cgroup), so the GPU run is expected to be well inside R1-BX-D5's 1–2 min
short-run window. This is a CPU observation used as an expectation; the census must record the GPU number
(condition c2), and the report says exactly that.

## 5. Tests and CPU smoke — records verified

- `tests/trackg/test_port_1gc.py`: **8 passed in 18.96 s** (`pytest_port_1gc.log`, header shows
  `rootdir: /home/dowling/r1_trackg_20261125/harness_etth1`, env `torch312`). Covers the static checks,
  manifest completeness/re-declaration, frozen-path refusal, E1/E2×E3/E4 composition in both orders, task
  semantics, synthetic smoke, tensor-subclass refusal and parent metric helpers.
- Isolation core `tests/trackg/test_trackg_isolation.py` under a systemd delegated scope with
  `AR_TEST_CGROUP_PARENT`: **27 passed, 1 skipped in 36.24 s** (`pytest_isolation.log`, a
  `run-…scope` line is present; 27 passing requires the cgroup parent, and the skip is the documented root-only
  test). Count identical to the accepted TASL-2 isolation host check (27/1 in 15.83 s).
- Whole `tests/trackg -k "not smoke"` on the kit branch: **359 passed, 3 failed, 1 skipped, 11 deselected in
  150.21 s**. The three failures are
  `test_trackg_campaign_v2_diff.py::{test_measured_timeout_is_a_proposal_failure_and_is_never_rerun,
  test_repeated_provisional_timeout_becomes_divergent_after_two_and_is_never_rerun}` and
  `test_trackg_t0_identity.py::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit`.
  The **same three test ids and the same exceptions** fail on the pristine base `c025f89a`
  (`/home/dowling/r1_tracks/t1_tasl/harness`, HEAD = `c025f89a`, clean except pre-existing data links),
  **3 failed in 2.24 s** → pre-existing environment failures, not kit regressions. The report's attribution of
  the t0 failure to the missing langchain-openai stack is consistent with the env (no `openai`,
  `langchain-openai`, `langchain_core` or `langgraph` installed; the probe imports the manager → LLM-client
  chain), but the probe's stderr is not captured, so that exact attribution is plausible, not proven (m4).
- Real-data CPU port smoke at the full 2,000-step budget through `WorkingCopyRunner` in a delegated 8 GiB cgroup
  (`ps.run_smoke`, CPU 0–3, no GPU UUID): 9 captures, 8 executed. My re-read of the host run records and the
  capture `cpu_real_smoke/records.json` matches the report's table and every record sha:

| run | outcome | val MSE | sealed test MSE | elapsed (s) | effective / waivers / exceptions / not_forced |
|---|---|---|---|---|---|
| `s000_baseline` | ok | 0.654580 | 0.375348 | 12.603 | true / {} / [] / [dataloader_workers] |
| `s001` frozen-path diff | refused `scope_violation` | — | — | — | not executed |
| `s002` NaN diff | divergent `non_finite_loss` | — | nan | 8.035 | true / {} / [] / [dataloader_workers] |
| `s003` = E1 | ok | 0.644269 | 0.373813 | 7.606 | true / {} / [] / [dataloader_workers] |
| `E1` | ok | 0.644269 | 0.373813 | 7.636 | true / {} / [] / [dataloader_workers] |
| `E2` | ok | 0.693659 | 0.392145 | 7.730 | true / {} / [] / [dataloader_workers] |
| `E3` | ok | 0.658426 | 0.369918 | 8.008 | true / {} / [] / [dataloader_workers] |
| `E4` | ok | 1.715713 | 1.243953 | 7.825 | true / {} / [] / [dataloader_workers] |
| `B2` baseline repeat | ok | 0.654580 | 0.375348 | 7.641 | true / {} / [] / [dataloader_workers] |

  The host `run_record.json` files confirm: `schema trackg_run/v1`, `node_spec_sha256 8f874c50…`,
  `run_budget {kind: steps, value: 2000}`, command `python3 -s run_fixed_budget.py --steps 2000`,
  `AR_STEPS completed=2000`, `AR_DEVICE cpu`, `CUDA_VISIBLE_DEVICES: ""`, `gpu_uuids: []`, CPU list `[0,1,2,3]`,
  `external_limit` the 8 GiB systemd scope, timeout 900 s provisional, `process.killed_with: null`,
  `leftover_processes_killed: false`, `timed_out: false`, determinism settings forced with
  `not_forced: ["dataloader_workers"]` only, cgroup empty after the run, 16 frozen entries checked and none
  changed, and code states equal to the manifest (`E1 249c95c3…`, `E4 5873d6ce…`, baseline `c6fda54c…`,
  s002 `8c39d73d…`). B2 reproduces B1's validation **and** sealed test metric to the digit (logs and result
  channels identical), and s003 reproduces E1 exactly — the CPU fixed-seed repeat is genuine. E1–E4 are the
  four declared edits, s001 is refused by the scope validator, s002 is a non-finite-loss divergence. Nothing in
  the records is a GPU run, a census or a noise floor; the report claims none.

The synthetic smoke (in the 8 tests) uses random data of the real shape only; the real-data smoke uses the
downloaded data. Neither is a measurement; the report calls them “no U2 and not the GPU census”.

## 6. Report and captures accuracy

- `SHA256SUMS` sha256 `f50bbc5c…` matches; 22 files; all hashes verify (rc 0) on TASL-2 and on the Mac; every
  capture is byte-identical host↔Mac. The named capture contents match the report's claims, including
  `pins.json` (`node_spec` canonical vs spec raw distinguished exactly as described), `env.txt`,
  `torch312.freeze.txt`, `data_manifest.json`, `edits_manifest.json`, `git_*` and the four pytest logs.
- Every number I checked in the report matches a capture or the host: commit/branch/base, 19 files/+2,015/−1,
  dirty-state line, pins, freeze, 8/27+1/359+3+1+11, the 9 smoke rows (val/test MSE and elapsed), the 2,000-step
  budget, the data root, the source hash/bytes, the settlement “clean except the data link”, the push remote ref
  and the report's own claim that the paper side is uncommitted.
- The data/capture provenance is consistent: setup output read-only and outside the repo; the committed pin is
  recomputable from a clean tree; the deployed pin adds only the host-specific data link; the commit was made at
  `03:40:12 -0800` (author) / `03:40:49 -0800` (committer) and every smoke capture is later, so the E1–E4
  manifest was committed before any measurement (also `measured: false`).
- **Val-vs-test MSE caveat (checked explicitly).** The report discloses that validation MSE (≈0.655) is much
  higher than sealed test MSE (≈0.375) and that selection is on validation, so the funnel/σ̂ must be read on
  validation. I independently checked that this is a property of the split, not a windowing bug: from
  `series.npy` with train-row standardisation, the target-only (“predict the mean”) MSE is **1.496 for
  validation** vs **1.110 for test** (target std 1.218 vs 1.053), and the node's R² is **0.559 on validation**
  (logged) vs **≈0.661 on test** (from 1 − 0.375348/1.1084). So the validation period is genuinely harder, the
  caveat is correct and sufficient, and the model's test MSE matching the paper's 0.384 reference within 2.3 %
  is a fair sanity check (properly a test-vs-test comparison). No test-based selection is done; the test metric
  is sealed.
- No overclaim found: the report explicitly says no GPU run, no U2, no G.1b, no noise floor, no D21/D28, no
  label/evidence use, no Track G readiness, and that a budget change after the census needs a new review.

## 7. Findings (no BLOCKING, no MAJOR)

- **m1 (MINOR, wording, paper side).** The report, `README.md` and `test_port_1gc.py` call 1GC-7RC ETTh1
  “candidate 2”. `R1-T1-NODE-EXPANSION` lists four candidates (MLGym MountainCarContinuous or MetaMaze, MLGym
  Titanic, 1GC-7RC ETTh1, 1GC-7RC Forest Cover) **without numbered labels**, and ETTh1 is the third there. Either
  cite the numbering source or say “the 1GC-7RC ETTh1 candidate”. (Frozen files: defer, see c8.)
- **m2 (MINOR, accuracy, paper side).** “the paper's winning T6 edit was an L1 swap” overstates it: the paper's
  analysis lists the winning T6 work as *“Plain DLinear + L1/MAE loss + WD 10⁻³ + train+val combined”*. L1 is
  one component, not the whole edit. Say “an L1/MAE loss change (one component of the paper's winning T6
  edits)” or drop the claim; E3 is justified as a code-level edit without it.
- **m3 (MINOR, disclosure, paper side).** The paper scores T6 on **held-out test** (Table 2 note; the 1GC
  handoff document says the same), while this node selects on `val_mse` and seals the test metric
  (R1-TRACKG-ROLE). The report states the policy but does not list this as a paper-vs-Paper-B deviation under
  “Deviations, stated”, and the appendix paragraph it prescribes (“implemented by the port … not the suite's
  assets”) is about assets only. Add: the paper's 0.384 reference is a *test-split* score; the node's selection
  metric is `val_mse` (≈0.655) and the two are not interchangeable. This is a protocol disclosure, not a
  measurement problem (c6).
- **m4 (MINOR, evidence gaps).** Three cited claims have no capture: (i) the prototype result “validation MSE
  plateaus ≈0.65; test ≈0.375 at 500→8,000 steps” (the prototype scripts exist and use the same windowing, but no
  output was saved); (ii) “the setup ran … exit 0” (the read-only data root and manifest are strong indirect
  evidence, but no setup log); (iii) the exact cause of the pre-existing t0-identity failure. Capture them, or
  mark them as unrecorded local observations. (i)–(ii) are harmless; (iii) should be worded “the missing
  langchain stack (exact module not captured)”.
- **m5 (MINOR, completeness).** The report says 22 capture files, but its parenthetical enumeration names 19
  files; with `SHA256SUMS` (discussed in the same sentence) it accounts for 20 of the 22 — it does not name
  `pins.err` and `torch312.freeze.err`. Both are benign (empty / uv's informational stderr), but the inventory
  should either name all 22 or say “all 22 files, `SHA256SUMS` self-checked”.
  Similarly the isolation-run environment/flags (`systemd-run -p Delegate=yes -p MemoryMax=8G …`,
  `AR_TEST_CGROUP_PARENT`) are asserted, not captured; the scope line and the 27 cgroup-requiring passes make it
  consistent, but a one-line command capture would close it.
- **m6 (MINOR, wording, paper side).** “the declared edits move validation MSE by large, ordered amounts” is too
  strong: E1 −0.0103, E2 +0.0391, E3 +0.0038 (0.6 %), E4 +1.0611 vs the 0.6546 baseline; the values are
  distinct, not monotone, and E1/E3 are small. Say “distinct amounts” and leave the discrimination verdict to
  the G.1b noise floor (which is exactly what the caveat says).
- **m7 (MINOR, cosmetic, frozen files — do not churn pins now).** `run_fixed_budget.py`’s header comment cites
  “the U1 audit, 26 Nov 2026” (U1 is 17 Nov 2026; `prepare_data.py` and `LICENCES.md` say 17 Nov), and
  `prepare_data.py` says “date + 7 features” for the `(17,420, 7)` array. These are comments only. Fixing them
  changes a frozen file → new committed pin → new review; leave them until after G.1b or fix before the census
  only with a full re-derivation/re-review (c8).
- **m8 (MINOR, disclosure, paper side).** The report does not repeat the threat-model item that the worker can
  read the validation/test targets (`data/series.npy` and the parent-sent full series) and that the budget fixes
  steps, not FLOPs. Both are in the frozen `README.md` and are standard for the non-Breakout torch nodes, but the
  paper-side funnel/appendix record should carry them for the S1 audit and the label-table disclosure (c6).
  Relatedly, “checklist E on the real data” should read “checklist E partly (CPU/synthetic); the GPU stub-manager
  smoke is pending U2”, and the checklist-E timeout item is unexercised (no timeout in the kit’s runs; the
  full-suite timeout tests are the pre-existing failures).

## 8. Conditions before the U2 census and the G.1b spec

- **c1.** This acceptance is recorded before any census; no U2/G.1b run before m1–m8 (paper-side) are either
  applied or explicitly waived, and never before c2–c4.
- **c2.** U2 on TASL-2 must run the standard GPU stub-manager smoke
  (`tests/trackg/port_smoke_gpu.py --node gc7rc_etth1`) at the full 2,000-step budget, GPU **by UUID**, with a
  CPU list, a memory cap and the pinned env `torch312`; record GPU model/UUID/driver, VRAM, wall time, every
  run's `run_record.json`, `isolation.effective: true` with `waivers {}`/`exceptions []`, and the fixed-seed
  repeat. Set `measured_run_seconds` and the timeout = 3 × slowest measured (R1-G1B-TIMEOUT) with its basis;
  no budget/spec change after the census without a new review (checklist A).
- **c3.** Recompute and record on the census host: `node_spec_sha256 8f874c50…`, spec raw `9391f718…`,
  **committed pin `818b8f6e…`** (clean tree, no data link), deployed pin `e3148582…` (with the link; not the
  census pin), `edits_manifest_sha256 ba31fed3…`, `data_manifest_sha256 eacc7e69…`, `ar_isolated 37d99ab0…`,
  freeze `d2e70fe4…`; use these fields for the G.1b chunk.
- **c4.** Confirm on the GPU, and record, that the baseline runs under the runner's forced deterministic
  settings (cudnn benchmark false, deterministic algorithms true, `CUBLAS_WORKSPACE_CONFIG=:4096:8`) and that a
  fixed-seed repeat is identical or the difference is recorded; if the node cannot run deterministically, the
  port must say so and a re-review is required before any G.1b chunk (checklist A).
- **c5.** The new G.1b spec/note (D21 protocol, 460 runs, seeds, 40 GPU-h expansion cap) is published by the
  coordinating chat only after c1–c4 and is itself independently reviewed and launch-checked; new run id; it
  cites the pins above and the measured timeout.
- **c6.** The appendix/funnel must carry: (i) 1GC-7RC is **not a suite** (repo 404); the baseline and evaluator
  are port-implemented from the paper's description, not suite assets (R1-1GC-FALLBACK); (ii) the paper scores
  T6 on held-out test while the node selects on validation `val_mse` and seals test (R1-TRACKG-ROLE) — the
  0.384 reference is a test score; (iii) ETTh1 licence: three conflicting claims, most restrictive CC BY-ND 4.0
  governing under R1-TRACKG-LICENCES, data downloaded and never redistributed, attribution recorded, and an
  **author/legal licence line is still required before any label table cites ETTh1** (U1 §9.3); (iv) the
  threat model: the worker can read the validation/test targets, the budget fixes optimizer steps not FLOPs
  (E4 is heavier per step), the worker and frozen loop share a process (the parent owns the metric arithmetic
  and the result channel), and the S1 audit must read diffs for label access; (v) no noise floor, D21/D28, GPU
  determinism verdict or label use yet.
- **c7.** Keep ETTh1 out of the repository and bundles; leave the data root read-only; the census must fetch the
  pinned source (hash-checked) and refuse a different revision; do not copy the raw CSV or `series.npy` into any
  branch, report bundle or capture.
- **c8.** The pins in §4 are the accepted ones. Any change to a committed/frozen kit file after this review
  (including m1/m7 wording in `README.md` or the node's frozen comments) changes the committed pin and requires
  a full pin re-derivation and a new review before U2; m1–m6 and m8 are to be applied to the **paper-side
  report/captures**, which are uncommitted and pin-neutral (`tests/trackg/test_port_1gc.py` is not part of the
  node's frozen pin, but changing it would change the surveyed branch and should be re-reviewed too).

## 9. What this review does not establish

No measurement, no GPU time or VRAM, no census record, no noise floor/D21/D28, no GPU fixed-seed determinism
verdict, no label/evidence use and no Track G readiness. I did not re-execute the tests or the smoke (read-only
review); their logs, run records and host state were verified for integrity and cross-checked against the
report, and the pinned source and paper were re-fetched. The val-vs-test MSE gap was checked as a split property
(§6), not measured as a noise floor. The 1GC-7RC paper is treated as external, untrusted data; its text is used
only to check the port's stated semantics.

**AI-assisted: DeepSeek Harness reviewer (`etth1-kit-reviewer`), delegated by the lead, 25 Nov 2026.
ENGINEERING_ONLY. Read-only review; the only file written is this review.**
