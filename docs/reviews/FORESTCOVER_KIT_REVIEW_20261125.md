# Independent review — Track G T1 expansion kit: 1GC-7RC Forest Cover node `gc7rc_forestcover` (25 November 2026)

**Verdict: ACCEPTED** — the ENGINEERING_ONLY harness kit for R1-T1-NODE-EXPANSION candidate 4, 1GC-7RC Forest
Cover (`mac-trackg-forestcover-20261125` @ `85851664679d10889c5af406843c4a3fc38f7a49`), is accepted for the U2
census and a new G.1b note, with the MINOR corrections **m1–m7** (paper-side record; **m5** is a frozen-file
wording fix and is deferred to avoid churning the committed pin) and the conditions **c1–c8** before any
census/G.1b run. **No BLOCKING, no MAJOR.** I verified the branch, push, content, every pin and every SHA in the
record independently, re-downloaded and re-parsed the source data, reproduced the split and the scaler, recomputed
the committed and deployed pins, and checked the node design against the paper's own Task 5. The kit is honest
about what it did **not** measure (no GPU, no U2, no G.1b, no noise floor).

**Reviewer and method.** Fresh independent reviewer (`forestcover-kit-reviewer`), delegated by the lead; no
involvement in the port, the data setup, the smoke or the report. Read-only: the only file this review writes is
this review; no run/edit/commit/push/delete of any repository or host artefact, no HTCondor, no GPU job, and no
test/census re-executed. TASL-2 was read with `ssh -o BatchMode=yes portal_zhixu` using read-only commands only
(`ls`, `stat`, `cat`, `sha256sum`, `sha256sum -c`, `find`, `git rev-parse/status/ls-remote/log/diff`, and Python
that only read files — the X/y hashes were re-derived in memory, nothing written on the host). Local checks used
`git show`/`ls-tree` on objects already present and a throw-away bare clone under `/tmp` fetched from `origin`
(no write to any repository); the UCI zip/member, the arXiv paper, the UCI dataset page and the paper-named
suite repository were re-fetched and treated as external, untrusted data. Pins were recomputed with independent
code, not by calling the kit's `pins.py`. The capture logs were accepted as captured evidence (integrity
checked, §5/§6) because re-executing tests/runs is outside this review's remit. Host clock TASL-2:
2026-11-25T13:34Z = 14:34 Berlin.

**Object under review.**

- Kit branch `mac-trackg-forestcover-20261125`, tip **`85851664679d10889c5af406843c4a3fc38f7a49`** (parent/base
  `c025f89aeafc2199bf3487b4bcaa16678273c702` = `mac-trackg-t1-tasl-20261121`), pushed to `origin`
  (`github.com/dowlingwong/autoresearch_harness.git`; no PR, no merge); host worktree
  `/home/dowling/r1_trackg_20261125/harness_forestcover`, TASL-2.
- Report `docs/r1/reports/tasl_chain_20261122/FORESTCOVER_KIT_20261125.md` — 298 lines, 25,410 B, sha256
  **`ecc3e236cddd8660af73024a9bdf2b255b2cea064dcb81eaac0d0e4d363f12d1`**, untracked (`??`) in
  `ops-tasl-20261116` (HEAD `9253192f`) and absent from `origin/main` `912a7e02` (paper-side record; correct,
  nothing pushed to paper `main`).
- Captures `FORESTCOVER_KIT_20261125_captures/` — **52 hashed files + `SHA256SUMS`** (53 files on disk, 504 KiB);
  `sha256sum -c SHA256SUMS` rc 0 on TASL-2 **and** on the Mac; `SHA256SUMS` sha256
  **`2c75842d718f3441423ef6af67928a03247c6d06ed3e06bcd14673349086aed0`**; every file byte-identical host↔Mac
  (identical `SHA256SUMS` content plus rc-0 verification on both sides; spot files re-hashed by hand).
- Authority: `R1-T1-NODE-EXPANSION` + `R1-T1-D21-SCOPE`, PLAN row 1516 on `origin/main` `912a7e02` (25 Nov
  2026); `R1-1GC-FALLBACK` (4 Nov), `R1-BX-D5`, `R1-TRACKG-LICENCES`, `R1-TRACKG-ROLE`, `R1-HARNESS-ISOLATION`;
  `TRACKG_PORT_CHECKLIST.md` (paper repo, §A–F); the T1 TASL authorizations
  (`g1b_t1_tasl_20261121.md`, `g1b_t1_tasl_20261122.md`, `g1b_xc_t1_tasl_20261122.md`, `g4_t1_tasl_20261122.md`)
  which cite `harness_commit: c025f89a…`, and the official seven-node assembly review of 25 Nov 2026, which also
  cites `c025f89a…`.

## 1. Branch, push and content — verified

- Branch exists on `origin` at `8585166` (`git ls-remote origin refs/heads/mac-trackg-forestcover-20261125`);
  the TASL-2 worktree HEAD is the same commit, worktree status **clean except `?? nodes/gc7rc_forestcover/data`**
  (the setup symlink), exactly as the report says. No second commit and nothing unpushed: `git rev-list --count
  c025f89a..HEAD` = 1 and the tip's only parent is `c025f89a`.
- The commit is a single non-merge commit (author = committer = `2026-11-25T12:44:47Z`), and every measurement
  capture starts later (data setup `12:41Z`, smoke `12:56:45Z..13:17:54Z`, capture `SHA256SUMS` `13:18Z`), so
  E1–E4 + manifest were committed before any measurement — also `measured: false` in the manifest.
- `git diff --name-status c025f89a HEAD` = **19 files, +2,030/−1**: 17 additions under the node/spec/tests, one
  addition `tests/trackg/test_port_1gc.py`, and one modified line in `tests/trackg/port_smoke_gpu.py`
  (`SUITE_MODULES` gains `"test_port_1gc"`; `CPU_ONLY_NODES` unchanged — `gc7rc_forestcover` is a GPU-capable
  torch node, not CPU-only). No deletion, no rename, no harness-core edit, nothing unrelated.
- No task data committed: the 17 node/spec files are all text; `git ls-tree -r` under the node has no
  `.npy/.csv/.npz/.gz/...`; the whole branch's data-like files are pre-existing base-repo artefacts only. The
  new test's data-like scan agrees.
- The branch is built from the accepted T1 TASL tree: `68cdd1a`, `5403392e`, `f07875de`, `fb6e7d73`, `448f682`
  are all confirmed ancestors of `c025f89a` (the isolation core, its accepted fix, and the three accepted iso
  port branches). `c025f89a` is the harness the G.1b/G.4 authorizations and the official seven-node assembly
  cite, so the kit starts from the same tree the census/noise-floor code runs on.
- The byte-identical shared-helper claims hold: `ar_data.py` `85cec63f…`, `ar_parent.py` `cbef1d38…`,
  `ar_fixed_loop.py` `28562cfa…` and `ar_isolated.py` `37d99ab0…` equal the accepted `mlab_cifar10` copies at
  `c025f89a`; `ar_isolated.py` also equals the harness master
  (`src/autoresearch/trackg/node_lib/ar_isolated.py`). The node's `run_fixed_budget.py`/`ar_worker.py` are
  node-specific (data, split, scaler, seven-class metric), as the report says.
- Paper side: the report and captures are untracked in `ops-tasl-20261116` and absent from `origin/main`
  `912a7e02`; GitHub's PR API returns `[]` for the branch (no PR/merge).
- **Integration note (non-blocking).** The sibling 1GC-7RC ETTh1 kit branch adds the *same* file name
  `tests/trackg/test_port_1gc.py` and the *same* `SUITE_MODULES` line. Each kit branch is self-contained and
  fine for its own U2; if the coordinating chat ever assembles more than one kit into a single checkout, the
  identically named test module and that line must be reconciled (rename/union) before the GPU smoke runs there.

## 2. Node design and paper Task 5 semantics — verified against the paper

I fetched the paper itself (arXiv:2605.17046v2, HTTP 200 on 25 Nov 2026; treated as external data) and read
Table 2, Table 4/6, the Task 5 paragraph and Appendix E. The paper says: *"Task 5 (Tabular Prediction):
seven-class classification on Forest Cover Type (581 K rows, 54 features: 10 continuous + 44 binary one-hot;
stratified 80/10/10 split, StandardScaler-normalized). The baseline is a 3-layer MLP (128→256→128, BatchNorm,
ReLU, dropout = 0.3)."* Table 2, row T5: 40 min, Tabular Prediction, Accuracy ↑, Forest Cover, MLP (3L),
Train 465 K / Eval 58 K, score **0.806**, batch **4096**; the Table 2 note fixes the scoring split: **held-out
test for Tasks 4–6**. Table 4/6 mark **0.806 as the paper's own baseline ‡ run** ("Single run of the baseline
train.py (T3 15ep; **T5 40ep**; rest 5ep)") — 0.969 is the TabNet reference †, not the baseline. Appendix E:
Forest Cover Type, UCI, **CC BY 4.0**. The paper-named suite repository
`github.com/Strolchii/1GC-7RC-Benchmark` returns **404** again today (verified), and the only pre-existing 1GC
material in the harness repo is `docs/track_g/1gc_7rc_handoff_20261027.md` on `origin/r1-local-20261027-1gc`
(status BLOCKED, explicitly no runnable adapter — verified); the base tree has no 1GC node. All of the report's
paper claims are correct.

The node matches the paper's stated semantics: 581,012 × 54 with 7 classes (10 continuous + 4 wilderness
one-hot + 40 soil-type one-hot); **stratified 80/10/10** with a fixed split seed 42 — I reproduced
**464,810 / 58,101 / 58,101** rows exactly (per-class rounding); per-feature **means/population std fitted on the
464,810 training rows only**, StandardScaler semantics, all 54 columns scaled — reproduced to the run log's
`AR_INFO mean=[2959.2576,155.6673,14.0996] std=[280.0385,111.9292,7.4852]`; the paper's **3-layer MLP
128→256→128 with BatchNorm/ReLU/dropout 0.3** and a 7-logit head; batch 4096; Adam lr 1e-3; cross-entropy;
**exactly 8,000 optimizer steps**, enforced by the frozen loop's optimizer post-step hook (`AR_STEPS
completed=8000`, run records `run_budget {kind: steps, value: 8000}`), **no wall-clock key anywhere** (the spec
has prose only, referring to the paper's 40-minute agent budget as the motivation); workers 0, threads 4;
selection on `AR_METRIC val_accuracy=` (maximise) with `AR_TEST test_accuracy=` written **only to the result
channel** — the run.log has no metric/test line; test never selected (R1-TRACKG-ROLE). The spec loads through
the strict loader (the kit tests load it) and declares `suite: 1gc7rc`, `domain: tabular`, `allow_new_files:
false`, the isolation block and `setup_command`, as the report states.

The deviations the report states are the real ones and are fairly disclosed: (a) suite assets/evaluator
unavailable → the baseline and API are the port's implementation from the paper's description; (b) the paper
scores Task 5 on **held-out test** while this node selects on **validation** and seals test — the report states
this and that 0.806 is a test-split score not interchangeable with the node's selection metric (correct); (d)
the paper's 465 K/58 K rounding vs the port's exact 464,810/58,101/58,101 (correct); (e) the 0.806 baseline is
correctly attributed to the paper's own baseline run, and the port's baseline exceeds it. Two points need
correction or tightening:

- **m1 (MINOR, accuracy).** Deviation (c) says "the paper states the split and the model but **no epoch
  count**". The paper's results-table footnote ‡ does state the baseline's epoch count (T5 = 40 ep) and Table 2
  gives the 40-min budget. Say instead: "the paper gives the 40-min task budget and records the baseline run at
  40 epochs but no learning-rate schedule, weight decay or optimiser name; the port fixes Adam lr 1e-3, no
  schedule/weight decay and 8,000 steps (≈71 epochs) under R1-BX-D5 — deliberately longer than the paper's
  40-epoch baseline, which is why the port's baseline is expected to exceed 0.806." (The report's deviation
  (e) claim "trains longer" is right but should cite the 40 epochs.)
- **m7 (MINOR, statistical wording).** In §7 the deltas are compared against a binomial SE of ≈0.0013 near 0.90,
  which is a fair scale: E1 ≈ 10.6 SE, E2 ≈ 2.2 SE, E3 ≈ 3.6 SE, E4 ≈ 24 SE. "E1/E3/E4 are many SE" overstates
  E3; write "E1 and E4 are >10 SE, E3 is ≈3.6 SE (significant), E2 is ≈2.2 SE" and leave the discrimination
  verdict to the G.1b noise floor. Also, "the baseline converges well before the budget: validation accuracy
  **keeps improving to** ≈0.896 by 8,000 steps" (§4) is not supported by any capture — the run log records only
  the final accuracy and the training-loss lines, no validation trajectory — and it is internally inconsistent
  ("converges" vs "keeps improving"). Say "the final baseline accuracy at 8,000 steps was 0.8964 validation /
  0.8947 test; convergence was not measured" (m3, below).

## 3. Data preparation and licence — verified

`prepare_data.py` is a download-only one-off setup (`setup_command`, never part of a run): it GETs
`https://archive.ics.uci.edu/static/public/31/covertype.zip`, checks the pinned zip **`89a975c2…` /
11,251,206 B**, extracts the member `covtype.data.gz`, checks its pinned **`614360d0…` / 11,240,707 B**, parses
the 581,012 × 55 CSV into `X.npy` (float32, 581,012 × 54) and `y.npy` (int8, classes 0–6), writes the hashed
data manifest last, makes the data root read-only, and links it into the node as `data/`. The frozen parent
re-checks the manifest on every run and re-checks the **pinned source zip sha256 and URL** against the manifest
for the real (non-synthetic) data; the worker verifies the data before training and the parent verifies it again
after the worker answers (I read these code paths and saw the `AR_DATA manifest_sha256=…` lines twice in the run
logs).

I verified the data independently, not by copying the kit's values: the canonical URL **today** returns exactly
11,251,206 B with sha256 `89a975c2…`; the member is 11,240,707 B with sha256 `614360d0…`; re-parsing the raw zip
in memory with the pinned pandas/numpy environment reproduced **exactly** the committed `X.npy` sha256
`3c9503390b527ce0cc5d1713772db126e754d12f312f3581b3f15fe6f834bfa7` (125,498,720 B) and `y.npy`
`35e11486262e974a249c66474dc624fe29d88f690d9819612239fb4dd34768a7` (581,140 B), with class counts
211,840 / 283,301 / 35,754 / 2,747 / 9,493 / 17,367 / 20,510. From `y.npy` I reproduced the fixed split (above)
and the train-only scaler (above) exactly, so the manifest, split and scaler are consistent with the real data,
not just with each other. The data root is outside the repo, read-only (`dr-xr-xr-x`, files `-r--r--r--`), the
raw zip lives only under the setup-only `raw/` (which no run reads) and the branch holds no task data.

Licence: the UCI dataset-31 page (re-fetched today) states **CC BY 4.0** (attribution required), DOI
10.24432/C50K5N, and the paper's Appendix E also lists CC BY 4.0, so unlike ETTh1 there is no conflicting
licence claim. Download-only, never redistributed, with attribution, is consistent with R1-TRACKG-LICENCES.
Two MINORs:

- **m4 (MINOR, accuracy).** The report says the attribution is "recorded in `LICENCES.md`, **the spec and the
  manifest**". The full attribution string ("Covertype dataset, UCI Machine Learning Repository (Blackard, J. &
  Dean, D., 1998), DOI 10.24432/C50K5N, CC BY 4.0") is only in `LICENCES.md`; the spec's `external_benchmark.
  license` and the data manifest's `source.license` say only "CC BY 4.0 (UCI page); data downloaded, never
  redistributed". Correct the report sentence. **Do not edit the data manifest** to add the attribution unless
  the setup is re-run and the data pin re-derived (the manifest's bytes are the pinned `data_manifest_sha256`
  `2b5cfb15…`); the report-side wording fix is pin-neutral.
- **m5 (MINOR, frozen-file wording — do not churn pins now).** `LICENCES.md` says the statements are recorded as
  the U1 audit cites them "(`U1_LICENCE_AVAILABILITY_20261117.md` **§3 and §7**…)". Covertype is recorded in U1
  **§5** (1GC-7RC public datasets) and **§7** (audit result table); §3 is MLGym. This is a comment/reference
  only. Fixing a frozen file changes the committed pin → leave it until after G.1b, or fix before the census
  only with a full pin re-derivation and a new review (c8).

## 4. Pins, representative edits and environment — independently recomputed

Every value in the report's §5 was re-derived on TASL-2 from the committed tree, not copied:

| field | report | recomputed |
|---|---|---|
| `node_spec_sha256` (loader canonical: YAML payload → `json.dumps(sort_keys, separators=(",",":"), ensure_ascii=False, default=str)` → sha256) | `ff2a585b69b51b51d0649e7f57b4713c650c46a27c981982dbeb2d09badf0beb` | **equal** |
| spec raw sha256 (YAML file bytes; also equals the committed blob and `gc7rc_forestcover.yaml` capture) | `edd1a076aab8b2cc1f45192860b3555a844400c211581888b9edbcc4e5104e02` | **equal** |
| `committed_pin_sha256` (recursive frozen-file walk, symlinks as `link:<target>`, `data` link dropped → 15 entries → `json.dumps(sort_keys)` → sha256) | `78b48db9d36c5c67e55a4cc65495821e39f70b9d5bf01bb35410037e1b017a33` | **equal** (from the clean live tree = HEAD tree; capture `committed_pin_from_head.json` says `data_link_in_head_tree: false`, 15 files) |
| deployed pin (with the host-specific data link; 16 entries; information only) | `ec5c779161be56665bf7ae6d45adee140fde6e47cb46cb08bd583f8a0d4d5a5f` | **equal** |
| `edits_manifest_sha256` (manifest file bytes; also `representative_edits/manifest.json` capture) | `0219deb80aab3f839d52a186a6bdedca8d754c111cd964566439af457a83b6ed` | **equal** |
| `data_manifest_sha256` (host data root file and capture) | `2b5cfb15f3c91e865df0e42c37099a335360df457005d455f6127b217c62c66d` | **equal** |
| `X.npy` / `y.npy` | `3c950339…` / 125,498,720 B, `35e11486…` / 581,140 B | **equal** (re-derived from the raw zip) |
| source zip / member | `89a975c2…` / 11,251,206 B, `614360d0…` / 11,240,707 B | **equal** (re-downloaded) |
| `ar_isolated.py` = master | `37d99ab0…` | **equal** |
| env freeze | `d2e70fe4…`, 77 packages | **equal**, and **byte-identical** to the accepted T1 TASL freeze `sweep2/g1b/env/torch312.freeze.txt` (same sha in `g1b_t1_tasl_20261121.md`) |
| run budget | steps 8,000, batch 4,096, no wall-clock key | **equal** |

Environment: TASL-2, Python 3.12.16, torch 2.6.0+cu124, numpy 2.5.4, pandas 3.1.1, uv 0.13.6 (`env.txt`); GPU
present but unused (CUDA hidden, `torch.cuda.device_count=0`).

Representative edits: `manifest.json` is `measured: false`, carries the committed `node_spec_sha256` and
`node/run_budget`, one baseline code state and four edits; its `sha256` values are exactly the report's E1
`d59cd11e…` (lr 1e-3→4e-4), E2 `c960568c…` (1e-3→5e-3), E3 `19009049…` (cross-entropy→label smoothing 0.1 +
grad clip 1.0) and E4 `29f4535b…` (128/256/128→256/512/256), and the smoke run records' `code_state_sha256`
for E1–E4 equal the manifest's states (`798ca1a1…`, `267e34f5…`, `34d6a4bd…`, `73348ffb…`); the baseline run
state is `c92eb9cb…`. E1/E2 are same-line alternatives; the four are pairwise distinct and the declared
interacting pairs compose in both orders (`test_interacting_edits_compose`, passed).

## 5. Tests and CPU smoke — records verified

- `tests/trackg/test_port_1gc.py`: **8 passed in 64.40 s** (`pytest_port_1gc.log`). Covers the static checks,
  manifest completeness, frozen-path refusal, E1/E2×E3/E4 composition in both orders, the pinned Task 5
  semantics, synthetic smoke (random data of the real shape), tensor-subclass refusal and the parent metric
  helpers. The 8 test functions are exactly those 8 checks.
- Isolation core `tests/trackg/test_trackg_isolation.py` under a delegated scope with
  `AR_TEST_CGROUP_PARENT`: **27 passed, 1 skipped in 36.86 s** (`pytest_isolation.log`) — identical to the
  accepted TASL-2 host-check count (27 passed, 1 root-only skip, 15.83 s in
  `TASL2_ISOLATION_HOST_CHECK_20261121.md`).
- Whole `tests/trackg -k "not smoke"` on the kit branch: **359 passed, 3 failed, 1 skipped, 11 deselected in
  162.26 s** (`pytest_full_suite_kit.log`). The three failures are
  `test_trackg_campaign_v2_diff.py::{test_measured_timeout_is_a_proposal_failure_and_is_never_rerun,
  test_repeated_provisional_timeout_becomes_divergent_after_two_and_is_never_rerun}` and
  `test_trackg_t0_identity.py::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit`. The
  **same three test ids and the same exceptions** fail on the base `c025f89a` (`/home/dowling/r1_tracks/
  t1_tasl/harness`, HEAD `c025f89a`, clean except pre-existing data links) at **3 failed in 2.46 s**
  (`pytest_base_known_failures.log`) → pre-existing environment failures, not kit regressions. The t0 failure's
  attribution to the missing langchain-openai stack is consistent with the environment and with the earlier
  U2 record ("langchain-openai missing for the t0 identity test"), but this kit's capture does not show the
  missing module (m6).
- Real-data CPU checklist-E smoke at the full 8,000-step budget through `WorkingCopyRunner` in a delegated 8 GiB
  systemd scope with the worker sandbox (`ps.run_smoke`, CPU, `--cpus 16-31`, `CUDA_VISIBLE_DEVICES=""`; the
  reviewed `port_smoke_gpu.py` CLI's `--gpu-uuid` guard is overridden in memory only, no repo file changed):
  9 planned, 8 executed, with the full-fidelity run records. My re-read of the host `run_record.json` files and
  the capture `cpu_real_smoke/{summary.txt,summary.json}` matches the report's table and every value:

| run | executed | outcome | val accuracy | sealed test accuracy | elapsed (info only) |
|---|---|---|---|---|---|
| `s000_baseline` | yes | ok | 0.896439 | 0.894683 | 139.502 s |
| `s001` frozen-path diff | no | refused `scope_violation` (diff on `run_fixed_budget.py`) | — | — | — |
| `s002` broken NaN diff | yes | divergent `non_finite_loss` | 0.000000 | 0.000000 | 130.017 s |
| `s003` first declared edit (E1) | yes | ok | 0.883083 | 0.881689 | 133.528 s |
| `E1` (lr 4e-4) | yes | ok | 0.883083 | 0.881689 | 127.649 s |
| `E2` (lr 5e-3) | yes | ok | 0.899262 | 0.898849 | 128.366 s |
| `E3` (label smoothing + clip) | yes | ok | 0.891895 | 0.890329 | 135.036 s |
| `E4` (wider 256/512/256) | yes | ok | 0.927213 | 0.927919 | 344.405 s |
| `B2` baseline repeat | yes | ok | 0.896439 | 0.894683 | 129.126 s |

  Every executed run: `isolation.effective: true`, `waivers {}`, `exceptions []`,
  `determinism.not_forced == ["dataloader_workers"]`, `frozen_files_checked 16 / changed []`, worker sandbox
  present, cgroup killed and `empty_after: true`, `process.killed_with: null`, `timed_out: false`; limits
  `cpu_list [16..31]`, `gpu_uuids []`, external 8 GiB scope; run command `--steps 8000`; `AR_DEVICE cpu`;
  `AR_SPLIT train=464810 val=58101 test=58101 features=54 classes=7 split_seed=42 (fixed; AR_SPLIT_SEED=8001
  unused) standardised_on=train`; seeds train=split=8001. `B2` reproduces `B1`'s validation **and** sealed test
  accuracy to the digit (identical `run.log` sha256 `07c6557e…` and result-channel sha256 `bcfc9b5d…`);
  `s003` reproduces `E1` exactly (`run.log` `c1e7d434…`, channel `5a119acc…`), so the CPU fixed-seed repeat is
  genuine. Smoke wall **1,268.791 s**; scope memory peak **1,428,860,928 B** (1.43 GB of 8 GiB); no run timed out
  or was killed. The test accuracy is written only to the result channel (the run.log has no `AR_TEST` line) —
  the sealed/selection policy holds.
- **m2 (MINOR, accuracy of the launch accounting).** The report says attempt A "(12:56Z)" and attempt B
  "(12:59Z)" and "(no `runs/` was created by either)". The preserved captures say otherwise: attempt A's
  `raw/env.txt`/`gpu_state_pre.txt` are written at **12:55:10Z** and attempt B's at **12:55:27Z**, before the
  accepted smoke started at 12:56:45Z (attempt B at 12:59Z is impossible: attempt C was already running); and
  both preserved directories contain **empty `runs/` and `captures/` directories**, created by the driver
  preflight before the failure. Reword to: "attempts A and B (raw preflight captures at 12:55:10Z and
  12:55:27Z) failed before any run; no run was executed and no run record was produced (`runs/` scaffolds are
  empty)". Also, the failure causes as stated ("driver's `git rev-parse` cwd", "driver's `tests` import path")
  are session recollection, not evidence: no `smoke_error.txt`/`summary` was captured for either attempt and
  the driver was edited at 12:56:41Z (just before attempt C; it was created at 12:44:20Z), so the revision that
  failed A/B is not preserved — mark the causes as recollected, or re-capture them. This does not affect any
  measurement (no run happened).
- **m3 (MINOR, unsupported claim).** See §2: "the baseline converges well before the budget" / "keeps
  improving to ≈0.896 by 8,000 steps" is not captured (only the final accuracy and loss lines exist). The
  defensible statement is the final measured 0.8964 validation / 0.8947 sealed test.
- **m6 (MINOR, evidence gaps).** Three asserted points are not captured here: (i) the isolation-test run's
  delegated scope and `AR_TEST_CGROUP_PARENT` — `pytest_isolation.log` holds only the 27/1 summary (the 27
  cgroup-requiring passes make it consistent, but a one-line scope capture would close it); (ii) the first
  setup run's exit code — `setup.txt` is explicitly a *reconstructed transcript* of the session output (it says
  so), while `setup_verify.txt` shows the idempotent re-check `rc=0`, and the read-only data root + manifest
  are strong indirect evidence; (iii) the t0 missing-module attribution (above). Capture or word as inferred.
- **Budget plausibility.** 8,000 steps at batch 4,096 = 113 steps/epoch ≈ 71 epochs of 464,810 rows; the CPU
  smoke measured 127.6–139.5 s for the baseline and E1–E3, 344.4 s for the 3.8×-wider E4 and 129.1 s for the
  B2 repeat (4 threads, shared host; info only). R1-BX-D5's 1–2 min window is a property of the GPU label run,
  not of this contended CPU smoke host; the report says exactly that, requires U2 to record GPU wall time/VRAM,
  and says a GPU run above 120 s would need a budget reduction under checklist A (new review). The node is
  ≈1.7 GFLOP/step at batch 4,096, so the GPU run is expected to be seconds; this is an expectation, not a
  measurement, and the report labels it as such.

## 6. Report and captures accuracy

- `SHA256SUMS` sha256 `2c75842d…` matches; 52 hashed files + the sums file (53 files on disk, 504 KiB); all
  hashes verify (rc 0) on TASL-2 and on the Mac; every capture byte-identical host↔Mac (identical sums file and
  rc-0 verification on both sides; spot files re-hashed by hand). The named capture contents match the report's
  claims: `pins.json` (canonical vs raw spec hash distinguished exactly as described), `committed_pin_from_head.
  json` (HEAD `8585166`, 15 frozen files, no data link in the HEAD tree), `env.txt`, `torch312.freeze.txt`,
  `data_manifest.json` (identical to the host data root's file), `edits_manifest.json`, `gc7rc_forestcover.
  yaml` (byte-identical to the committed spec), `ancestry.txt`, `git_*`, `setup*`, `push_verify.txt` (shows the
  new branch and the `ls-remote` TIP), the four pytest logs
  and `cpu_real_smoke/{summary*,records.json,run_records/*,run_logs/*,result_channels/*}`.
- Every number I checked in the report matches a capture or the host: branch/tip/base, 19 files/+2,030/−1,
  dirty-state line, the pins, freeze, 8/27+1/359+3+1+11, base 3-failed, the 9 smoke rows (validation and sealed
  test accuracy, elapsed), 8,000-step budget, data root, source/member hashes and bytes, class counts, split and
  scaler, the 1,268.791 s wall and 1,428,860,928 B peak, the attempt-C start/finish (`12:56:45Z..13:17:54Z`),
  and the report's own claim that the paper side is uncommitted. The report's §4 table shows test accuracies that
  exist only in the result channels, and they match.
- **No overclaim found.** The report explicitly says no GPU run, no U2, no G.1b, no noise floor, no D21/D28, no
  label/evidence use and no Track G readiness; the budget/wall-time statements about the GPU are labelled
  expectations; the CPU smoke is called an upper bound, not the census number. The MINORs m1–m7 are the
  inaccuracies found; none changes a pin, a measurement record or the kit's usability.

## 7. Suitability, D21 caveats and blockers

- **Data obtainable reproducibly: YES** — I re-downloaded the pinned zip and member today and re-parsed the
  arrays; the manifest, X/y hashes and class counts match byte-for-byte; the frozen parent refuses a non-pinned
  source and the data root is read-only. CC BY 4.0 with attribution is the single clear licence; download-only
  is compatible with the kit.
- **Suitable for a noise floor: provisionally YES, with the report's four caveats**, which I checked: (i) the
  baseline is deterministic on a same-seed CPU repeat (B2 = B1 exactly); (ii) the declared edits move validation
  accuracy by −0.0134 / +0.0028 / −0.0045 / +0.0308, i.e. E1 ≈10.6 SE, E2 ≈2.2 SE, E3 ≈3.6 SE and E4 ≈24 SE
  against a binomial scale of ≈0.0013 near 0.90 — the report's "E2 is ~2 SE" is the right caveat (and m7 asks it
  to soften "many SE" for E3); (iii) accuracy is bounded on 58,101 validation rows, the trivial majority floor is
  48.8 % (class 2) and there is no degenerate "one class" optimum, with plenty of headroom; (iv) the random
  stratified split carries the known Covertype spatial-autocorrelation leakage of the paper's own protocol, so
  absolute accuracy is dataset-optimistic but comparisons stay within the node on the same split. No test-based
  selection is done; the test accuracy is sealed.
- **D21 notes (R1-T1-D21-SCOPE).** D21 is the G.1b noise-screening statistic (mean P(wrong) over the D21
  protocol) and is **not measured here**; the report claims no D21 verdict and says D21 does not select T1 nodes
  for G.5 (every node passing U2, G.1b fixed-seed determinism and, where run, the cross-host check enters G.5).
  That matches the authority row (PLAN row 1515) exactly. The report correctly leaves the low-noise judgement to
  the G.1b run.
- **Blockers/unknowns** as stated are the real ones: suite repo 404 (paper-semantics port, not suite assets);
  no GPU/U2/G.1b — VRAM, GPU wall time, GPU fixed-seed determinism, the 10-seed noise floor, the 3× timeout basis
  and D21/D28 are all unmeasured; the budget/time estimates are CPU measurements that U2 must confirm on the GPU.
  **No STOP**: the dataset is obtainable reproducibly and the task is usable for a noise-floor port; what remains
  is this acceptance and the U2/G.1b runs.

## 8. Findings

- **No BLOCKING, no MAJOR.**
- **m1 (MINOR, accuracy).** The paper states the baseline's epoch count in its results-table footnote (T5 =
  40 ep) and a 40-min budget; "no epoch count" in deviation (c) is too strong, and deviation (e) should cite the
  40 epochs it beats (§2).
- **m2 (MINOR, accuracy/evidence).** Attempt A/B timestamps and "no `runs/` was created" do not match the
  preserved captures (env UTC 12:55:10Z / 12:55:27Z; empty `runs/`/`captures/` dirs exist); the two failure
  causes are not captured and the failing driver revision was overwritten. Reword and mark the causes as
  recollected (§5). No run happened, so no measurement is affected.
- **m3 (MINOR, unsupported claim).** "The baseline converges well before the budget / validation accuracy keeps
  improving" has no capture (only final accuracy and loss lines) and is internally inconsistent; state the final
  measured accuracies instead (§2, §5).
- **m4 (MINOR, accuracy).** The full attribution string is only in `LICENCES.md`; the report's "`LICENCES.md`,
  the spec and the manifest" is wrong. Do not edit the data manifest without re-setup/re-pinning (§3).
- **m5 (MINOR, frozen-file wording — defer).** `LICENCES.md` cites U1 "§3 and §7"; Covertype is in U1 §5 and
  §7 (§3 is MLGym). A frozen-file edit changes the committed pin → fix only with full re-derivation/re-review
  after G.1b, or leave (§3, c8).
- **m6 (MINOR, evidence gaps).** Isolation-test scope/`AR_TEST_CGROUP_PARENT`, the first setup run's exit code
  (setup.txt is a reconstructed transcript; verify shows rc=0) and the t0 missing-module attribution are not
  captured in this kit's record; capture or word as inferred (§5).
- **m7 (MINOR, statistical wording).** "E1/E3/E4 are many SE" overstates E3 (≈3.6 SE); say the numbers and let
  G.1b decide. The report's E2 ≈2 SE caveat is correct (§2, §7).

## 9. Conditions before the U2 census and the G.1b spec

- **c1.** This acceptance is recorded before any census; no U2/G.1b run before m1–m4, m6–m7 are either applied
  (paper-side record; pin-neutral) or explicitly waived, and never before c2–c4. m5 is deferred; the pins in §4
  are the accepted ones.
- **c2.** U2 on TASL-2 must run the standard GPU stub-manager smoke (`tests/trackg/port_smoke_gpu.py --node
  gc7rc_forestcover`) at the full 8,000-step budget, GPU **by UUID**, with a CPU list, a memory cap and the
  pinned env `torch312`; record GPU model/UUID/driver, VRAM, wall time, every `run_record.json`,
  `isolation.effective: true` with `waivers {}`/`exceptions []`, and the fixed-seed repeat. Set
  `measured_run_seconds` and the timeout = 3 × slowest measured (R1-G1B-TIMEOUT) with its basis. If the GPU
  baseline wall at 8,000 steps is above 120 s, reduce the budget under checklist A with a new review
  (R1-BX-D5). This CPU smoke is not the checklist-E GPU smoke; the GPU one is part of U2.
- **c3.** Recompute and record on the census host: `node_spec_sha256 ff2a585b…`, spec raw `edd1a076…`,
  **committed pin `78b48db9…`** (clean tree, no data link), deployed pin `ec5c7791…` (with the link; information
  only, not the census pin), `edits_manifest_sha256 0219deb8…`, `data_manifest_sha256 2b5cfb15…`, `ar_isolated
  37d99ab0…`, freeze `d2e70fe4…`; use these fields for the G.1b chunk.
- **c4.** Confirm on the GPU, and record, that the baseline runs under the runner's forced deterministic
  settings (cudnn benchmark false, deterministic algorithms true, `CUBLAS_WORKSPACE_CONFIG=:4096:8`) and that a
  fixed-seed repeat is identical or the difference is recorded; if the node cannot run deterministically, a
  re-review is required before any G.1b chunk.
- **c5.** The new G.1b spec/note (D21 protocol, 460 runs, seeds, 40 GPU-h expansion cap) is published by the
  coordinating chat only after c1–c4 and is itself independently reviewed and launch-checked; new run id; it
  cites the pins above and the measured timeout.
- **c6.** The appendix/funnel must carry: (i) 1GC-7RC is **not a suite** (repo 404); the baseline and evaluator
  are port-implemented from the paper's description, not suite assets (R1-1GC-FALLBACK); (ii) the paper scores
  Task 5 on held-out test while the node selects on validation and seals test (R1-TRACKG-ROLE) — 0.806 is the
  paper's baseline test-split score, not interchangeable with the node's selection metric; (iii) UCI Covertype is
  CC BY 4.0, data downloaded and never redistributed, attribution recorded (with m4's correction), and the raw
  zip/derived arrays stay outside the repo; (iv) the threat model: the worker can read the validation/test
  labels, the budget fixes optimizer steps not FLOPs (E4 is ~3.8× heavier per step), the worker and frozen loop
  share a process while the parent owns the metric arithmetic and the result channel, and the S1 audit must read
  diffs for label access; (v) no noise floor, D21/D28, GPU determinism verdict or label use yet; (vi) the
  checklist-E run recorded here is the CPU variant on the real data — the GPU stub-manager smoke is pending U2.
- **c7.** Keep Forest Cover out of the repository and bundles; leave the data root read-only; the census must
  fetch the pinned source (hash-checked) and refuse a different revision; do not copy the raw zip, `X.npy` or
  `y.npy` into any branch, report bundle or capture. `data_manifest_sha256 2b5cfb15…` is the census data pin.
- **c8.** The pins in §4 are the accepted ones. Any change to a committed/frozen kit file after this review
  (including m5's `LICENCES.md` reference) changes the committed pin and requires a full pin re-derivation and a
  new review before U2. m1–m4, m6–m7 are to be applied to the **paper-side report**, which is uncommitted and
  pin-neutral; m4's manifest note and the data manifest must not be edited without re-running setup and re-pinning
  the data.

## 10. What this review does not establish

No measurement, no GPU time or VRAM, no census record, no noise floor/D21/D28, no GPU fixed-seed determinism
verdict, no label/evidence use and no Track G readiness. I did not re-execute the tests or the smoke (read-only
review); their logs, run records and host state were verified for integrity and cross-checked against the
report, and the pinned source, the paper, the suite-repo 404 and the UCI licence page were re-fetched. The
data hashes, split and scaler were recomputed from the raw download, not copied. The 1GC-7RC paper is treated
as external, untrusted data; its text is used only to check the port's stated semantics.

**AI-assisted: DeepSeek Harness reviewer (`forestcover-kit-reviewer`), delegated by the lead, 25 Nov 2026.
ENGINEERING_ONLY. Read-only review; the only file written is this review.**
