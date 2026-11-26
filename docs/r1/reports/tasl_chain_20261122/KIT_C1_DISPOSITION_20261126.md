# Kit c1 disposition record — the four T1 expansion kits (26 November 2026)

**Task:** `experiment/20261126-01` with `compute/20261126-04` (P2 of the expansion G.1b note).
**Base:** `origin/main` `54082a057fc010e0cbd596a2146a6c997cfef57c` (contains `95249de3`, the rows of 26 Nov (f) and (g);
`95249de3` is an ancestor, and this record changes no code or pinned file).
**Status:** ENGINEERING_ONLY; `labels_read: none`. It records the disposition of the c1 MINOR items of the four
independent kit reviews so that P2 of `docs/r1/authorizations/g1b_x_t1_tasl_<YYYYMMDD>.md` can read PASS. It changes
no pin, no frozen file, no census value and no spec field.

## 1. Inputs cited by sha256 (all on `origin/main`, none edited)

| Kit review | Review sha256 | Verdict |
|---|---|---|
| `docs/r1/reviews/TITANIC_KIT_REVIEW_20261125.md` | `3c1d98601148485f5b319f1de1b8e5f9a688c9d3207a0aefe4554873a3344574` | ACCEPTED, no BLOCKING, no MAJOR; m1–m8 |
| `docs/r1/reviews/MOUNTAINCAR_KIT_REVIEW_20261125.md` | `5b867480ed81d3b5ece0f46657333cbb446d173cb0ed79f03bcebcd89d3e9950` | ACCEPTED, no BLOCKING, no MAJOR; m1–m10 |
| `docs/r1/reviews/ETTH1_KIT_REVIEW_20261125.md` | `73df58d5f929d6922223c3b33a926232e5e5189a774cc6a3b7364e5768869202` | ACCEPTED, no BLOCKING, no MAJOR; m1–m8 |
| `docs/r1/reviews/FORESTCOVER_KIT_REVIEW_20261125.md` | `8a4412bc307986077af5c8907ec06235fa1dec6901eaf56b29f5976d05e4bed5` | ACCEPTED, no BLOCKING, no MAJOR; m1–m7 |

The four review sha256 values are exactly those cited in P2 of the note draft.

| Kit report | Report sha256 | Cited in |
|---|---|---|
| `docs/r1/reports/tasl_chain_20261122/TITANIC_KIT_20261125.md` | `a1844bfef44e742795e6b74eef1738f70bec228bd4e13d6d58aa2eb13457ed10` | `node_mlgym_titanic` |
| `docs/r1/reports/tasl_chain_20261122/MOUNTAINCAR_KIT_20261125.md` | `0cede51b0dba90af8cc485748d577c2049d3671361f07facff70baabed635e7e` | `node_mlgym_metamaze` |
| `docs/r1/reports/tasl_chain_20261122/ETTH1_KIT_20261125.md` | `e1b94a76a2caf84cde6f0143cd094fdcbb31549e8f154d3441dc92da94079417` | `node_gc7rc_etth1` |
| `docs/r1/reports/tasl_chain_20261122/FORESTCOVER_KIT_20261125.md` | `ecc3e236cddd8660af73024a9bdf2b255b2cea064dcb81eaac0d0e4d363f12d1` | `node_gc7rc_forestcover` |

The sha256 values were recomputed from the blobs on `origin/main` with `git show origin/main:<path> | sha256sum`.
The kit reports are not edited; each correction below is written here as a corrigendum (the task's "applied" form).

## 2. What c1 requires, and how this record meets it

Each review's c1 requires that no U2/G.1b run starts before its m_i items are "applied or explicitly waived" (the
acceptance itself was recorded before the censuses on 25 Nov). This record is that explicit disposition for the
four expansion G.1b nodes. Every item is either applied here (paper-side corrigendum) or waived for G.1b with its
later condition named. The items that touch a committed/frozen file cannot be applied without changing a pin; they
are deferred under the review's **c8** re-pin rule, not under a label-table rule. The only label-table condition
among these reviews is ETTh1's **c6(iii)** (an author/legal licence line before any label table cites ETTh1); it is
unaffected by this record and still stands. Forest Cover's c6(iii) (the licence attribution) likewise still stands.

## 3. MLGym Titanic `mlgym_titanic` — m1–m8

| Item | Disposition | Correction recorded, or waiver reason | Later condition |
|---|---|---|---|
| m1 | APPLIED (paper side); frozen part waived for G.1b | The PLAN lists the four candidates unnumbered; the report says "the MLGym Titanic candidate" (the "candidate 1" label is the lead's parallel-kit order, not a PLAN label). The same label in the frozen spec header comment is not edited. | Frozen comment: c8 (any change re-derives the committed pin `0368a73d…` and needs a new review). |
| m2 | APPLIED | Corrected: the frozen pin covers seven `.py` files (`ar_data`, `ar_fixed_loop`, `ar_isolated`, `ar_parent`, `ar_worker`, `prepare_data`, `run_fixed_budget`) plus `LICENCES.md`, `README.md`, `requirements.txt`, the four diffs and the manifest = 15 entries; E4 is two engineered features (a family-size bucket and a sex×class interaction), not two interactions; the `B2` row reads "per-edit campaign / baseline repeat". | None for G.1b. |
| m3 | APPLIED | Corrected: "no label campaign/measurement; the sealed test accuracy was computed and recorded by the frozen parent for the checklist-E validation only". | None for G.1b. |
| m4 | APPLIED | Disclosed as engineering validation, not a campaign label run: the pre-smoke full-budget baseline at `AR_TRAIN_SEED=42`, `AR_SPLIT_SEED=42` (`/tmp/titanic_probe/realrun.out`, 132.8 s, val 0.808989, sealed test accuracy recorded) versus 0.775281 at 8001/8001. The stability sentence is qualified: deterministic at fixed seeds; seed/split sensitivity is what the 30-seed noise floor measures. | None for G.1b. |
| m5 | APPLIED | Corrected in the paper-side record: the freeze content is separated from its hash metadata (`836b7b86…` is the file with the appended line; `d2e70fe4…` is the 77-package content hash); the capture-set mapping (`synthetic_smoke/titanic_run_records/` ← the pytest basetemp) and the as-of time are documented; the inventory names `CAPTURES.md`, `pins_final.txt`, `kit_docs/` and `synthetic_smoke/`. Refreshing the two earlier same-count logs is an evidence-root action, not a G.1b input. | Evidence-root refresh, if done: with the next paper-side evidence bundle; no pin changes. |
| m6 | APPLIED | Corrected in the paper-side record: the setup output is cited as independently reproduced (three fetches, pinned sha256/size confirmed); the pytest logs' commands are in `commands.txt`; the five cgroup/root-dependent isolation skips are marked as such; the missing per-run diff/code-state provenance is marked host-only. New captures are not required for a G.1b input. | Evidence completeness only; with the next paper-side evidence bundle. |
| m7 | APPLIED | Corrected in the paper-side record: the superseded E4 manifests (`d6d8f990…` with E4 `c2363a88…`, and `e379e8de…` with E4 `e1b51dee…`) and the failed E4 diff are recorded by hash; the two failed campaigns and three failure events are described per attempt (attempt1: PATH failure and chmod `PermissionError`; attempt2: E4 non-finite). | Host retention under `/home/dowling/r1_engineering/titanic_20261125/` is an evidence-root action; it changes no pin and no G.1b input. |
| m8 | APPLIED | Corrected: the PLAN row is cited with `origin/main` `912a7e02` (line 1516); the S1.1 interaction E2×E3 is carried into the S1.1/G.1b record; the scoping sentence says "the only non-node functional harness change" (`tests/trackg/test_port_mlgym.py` is also additive). | None for G.1b. |

## 4. MLGym MetaMaze `mlgym_metamaze` (kit MOUNTAINCAR) — m1–m10

| Item | Disposition | Correction recorded, or waiver reason | Later condition |
|---|---|---|---|
| m1 | APPLIED (paper side); frozen part waived for G.1b | The report/status line says "candidate 3 in the lead's parallel-kit order" (the PLAN lists the candidates unnumbered). The frozen spec header/description and node README are not edited. | Frozen wording: c8 (re-pin and new review). |
| m2 | APPLIED | Corrected: the 23-file commit also updates `third_party/mlgym/README.md` (+2/−1: "four"→"five" Track G nodes and the `mlgym_metamaze` inventory row), listed as a surveyed-branch change, not a node-file change. | None for G.1b. |
| m3 | APPLIED (paper side); frozen wording waived for G.1b | Corrected: the goal remains fixed during an episode and the agent is re-spawned at a random position on success (pinned `meta_maze.py`, `rlMetaMaze.yaml`); the graded-count conclusion is unaffected. The frozen `README.md`/spec wording is not edited. | Frozen wording: c8. |
| m4 | APPLIED | Corrected: the pinned `rlMountainCarContinuous` config has `num_train_steps: 20000000`, five checkpoints each at the full budget = 5 × 20M (10M is the MetaMaze config). The rejection conclusion is unaffected. | None for G.1b. |
| m5 | APPLIED | Corrected: the shim has three torch settings, all `torch_absent`; the run record's `not_forced` list adds `dataloader_workers` ("advertised via AR_NUM_WORKERS only"). The record's four-name list is right; the attribution is corrected. | None for G.1b. |
| m6 | APPLIED | Corrected: every run record's `isolation.limits.external_limit` says `MemoryMax=8G`; the report's "16G" is corrected to 8G. The scope and cgroup are unaffected; no re-capture is needed because the records already carry 8G. | Host-side `real_smoke.py` string, if changed: an evidence-root action; no pin change. |
| m7 | APPLIED | Corrected: "nine downloaded assets (32,201 B) plus `data_manifest.json` (4,226 B, its own sha256 given)"; the same nuance in the README §2 table is corrected paper-side. | None for G.1b. |
| m8 | APPLIED | Corrected: `data_manifest_sha256 e2338195…` is the TASL-2 CPU setup value; a GPU-host setup produces a different manifest sha. The U2/G.1b spec carries its own host's manifest sha (this G.1b is CPU-only on TASL-2, so `e2338195…` is the right value). | Any GPU host: measure that host's manifest sha first; c8 if a pin changes. |
| m9 | APPLIED (paper side); frozen README waived for G.1b | Corrected: the budget cross-check is the harness outcome classifier's (`outcome.classify_run`); the worker enforces the exact rounded count; the parent checks `--steps` against `AR_BUDGET_*`. The frozen README wording is not edited. | Frozen README: c8. |
| m10 | APPLIED | Corrected in the paper-side record: the pytest logs are summary-only and the base row includes "10 deselected" (`333 passed, 1 failed, 22 skipped, 10 deselected`); the setup output is cited as independently re-fetched (nine fetches matched); `capture_all.sh`'s leftover `test_logs/pytest_port_1gc.log` line is recorded as script drift, and the 42-file set is complete and checksummed. | Re-running the capture assembler is an evidence-root action; no pin change. |

## 5. 1GC-7RC ETTh1 `gc7rc_etth1` — m1–m8

| Item | Disposition | Correction recorded, or waiver reason | Later condition |
|---|---|---|---|
| m1 | APPLIED (paper side); frozen files waived for G.1b | The report, `README.md` and `test_port_1gc.py` say "the 1GC-7RC ETTh1 candidate" (paper-side text), or cite the lead's numbering source; the PLAN lists the candidates unnumbered. The frozen files are not edited. | Frozen files: c8 (also re-review of the surveyed branch if `test_port_1gc.py` changes). |
| m2 | APPLIED | Corrected: the paper's winning T6 work is "Plain DLinear + L1/MAE loss + WD 10⁻³ + train+val combined"; L1 is one component, not the whole edit. E3 remains justified as a code-level edit. | None for G.1b. |
| m3 | APPLIED | Corrected as a deviation: the paper scores T6 on held-out test; this node selects on `val_mse` (≈0.655) and seals the test metric, so the paper's 0.384 test reference is not interchangeable with the node's selection metric. | None for G.1b. |
| m4 | APPLIED | Corrected: the prototype "validation MSE plateaus ≈0.65; test ≈0.375 at 500→8,000 steps" and the "setup exit 0" are marked unrecorded local observations (setup output independently reproduced as consistent); the pre-existing t0-identity failure is worded "the missing langchain stack (exact module not captured)". | Captures, if added: with the next paper-side evidence bundle; no pin change. |
| m5 | APPLIED | Corrected: the inventory names all 22 capture files (including `pins.err` and `torch312.freeze.err`) or says "all 22 files, `SHA256SUMS` self-checked"; the isolation flags/`AR_TEST_CGROUP_PARENT` are marked asserted, with the scope line and 27 cgroup passes as consistent evidence. A one-line command capture is not required for G.1b. | One-line capture, if added: evidence-root action; no pin change. |
| m6 | APPLIED | Corrected: the edits move validation MSE by distinct amounts (E1 −0.0103, E2 +0.0391, E3 +0.0038, E4 +1.0611 vs 0.6546 baseline), not monotone or large; the discrimination verdict is left to the G.1b noise floor. | None for G.1b. |
| m7 | WAIVED for G.1b | Cosmetic frozen comments only (`run_fixed_budget.py`'s "U1 audit, 26 Nov 2026"; `prepare_data.py`'s "date + 7 features"). Applying them changes a frozen file and re-derives the committed pin, with no effect on the measurement. | c8: fix only with a full re-derivation and new review, after G.1b, or leave. |
| m8 | APPLIED | Corrected in the paper-side funnel/appendix: the threat model (the worker can read validation/test targets; the budget fixes steps, not FLOPs) is carried; "checklist E on the real data" reads "checklist E partly (CPU/synthetic); the GPU stub-manager smoke is pending U2"; the checklist-E timeout item is marked unexercised. | None for G.1b. |

## 6. 1GC-7RC Forest Cover `gc7rc_forestcover` — m1–m7

| Item | Disposition | Correction recorded, or waiver reason | Later condition |
|---|---|---|---|
| m1 | APPLIED | Corrected: the paper states the baseline epoch count in its results-table footnote (T5 = 40 ep) and a 40-min budget; deviation (c) is corrected and deviation (e) cites the 40 epochs it beats. | None for G.1b. |
| m2 | APPLIED | Corrected: attempt A/B timestamps and "no `runs/` was created" are reworded to match the captures (env UTC 12:55:10Z / 12:55:27Z; empty `runs/`/`captures/` dirs exist); the failure causes are marked recollected and the overwritten driver revision is noted. No run happened, so no measurement is affected. | None for G.1b. |
| m3 | APPLIED | Corrected: the final measured accuracies are stated instead of "the baseline converges well before the budget / validation accuracy keeps improving". | None for G.1b. |
| m4 | APPLIED | Corrected: the full attribution string is only in `LICENCES.md`; the report no longer says it is in "the spec and the manifest". The data manifest is not edited. | None for G.1b. |
| m5 | WAIVED for G.1b | Frozen-file wording only: `LICENCES.md` cites U1 "§3 and §7" while Covertype is in U1 §5 and §7. Applying it changes the committed pin; it has no effect on the measurement. | c8: fix only with a full re-derivation and new review, after G.1b, or leave. |
| m6 | APPLIED | Corrected in the paper-side record: the isolation-test scope/`AR_TEST_CGROUP_PARENT`, the first setup run's exit code (setup.txt is a reconstructed transcript; verify shows rc=0) and the t0 missing-module attribution are worded as inferred where not captured. | Captures, if added: with the next paper-side evidence bundle; no pin change. |
| m7 | APPLIED | Corrected: "E1/E3/E4 are many SE" is replaced by the numbers (E3 ≈3.6 SE); the discrimination verdict is left to G.1b. | None for G.1b. |

## 7. Closing statement

**No pin, frozen file, census value or spec field changes.** In particular, every `node_spec_sha256`,
`committed_pin_sha256`, `edits_manifest_sha256` and `data_manifest_sha256` on the four `node_*` lines of
`sweep2/t1_tasl/g1b_tasl_x_spec.json`, the four U2 census records and their values, and the spec's own sha256
`d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238` are unchanged. No kit report or review is
edited; they are cited by the sha256 above. The dispositions are paper-side corrigenda or explicit waivers; the only
deferred items are the frozen-file items named above, all under c8.

**Label tables.** This record creates no label-table condition from the minor items. The conditions of the reviews
that still stand are unchanged: any label table that cites ETTh1 needs an author/legal licence line first (ETTh1
c6(iii)); Forest Cover's licence attribution stands (Forest Cover c6(iii)); and this record reads no label,
evaluation or sweep-2 file (`labels_read: none`).

**What P2 can now read:** the four kit reviews, each ACCEPTED, with c1 recorded by this disposition. The coordinator's
next step (per `compute/20261126-04`) is to merge this record, set P2 PASS in the expansion note, run
`check-note-x … --draft`, publish, and run the strict `check-note-x`.
