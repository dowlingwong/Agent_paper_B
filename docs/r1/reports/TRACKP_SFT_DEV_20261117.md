# Track P SFT pipeline (Stage S) — engineering unit, 17 Nov 2026

**Authority.** PLAN `R1-TRACKP-SFT-DEV` (branch `author-decisions-20261117b` @ `45fb94cc`): build and try the SFT
pipeline now on sweep 1's `c3_features/v3` + `trackp_prompt/v2` table (ENGINEERING); plug in sweep-1 B.2's label
block when it exists; the outputs are not used for any evidence, selection or tuning; the 7006–7010 evaluation block
is never read; train directly once sweep 2's labels exist. Spec: `docs/r1/TRACK_P_POST_TRAINING.md` §3.4, §3.6, §4,
§6.1, §7.1. AI-assisted (Claude); **ENGINEERING_ONLY**.

**Branch.** `mac-trackp-sft-dev-20261117`, from `main` = `26177d82` with `mac-w2-v3-rebuild-20261115` @ `d8aa9561`
merged (`--no-ff`): that branch carries `c3_features/v3` (`r1/c3/features.py`) and `trackp_prompt/v2`
(`r1/c3/train/types.py`), the versions the deepthought table was built with, and is not on `main` yet. The bundle
therefore carries those commits too.

## 1. What was built

| piece | file | what it does |
|---|---|---|
| data builder | `r1/c3/train/sft_data.py` | label sources, prompt replay, soft labels, instance splits, the data directory |
| Stage S runner | `r1/c3/train/sft.py` | L = RPS + CE in the shared `Trainer`; val eval hook; early stopping; temperature scaling; lr selection helper |
| CLI | `r1/scripts/trackp.py` | `sft-data`, `sft-dev`, `sft-select`; `sft` (P.4) now runs the same trainer behind its authorization note |
| protocol config | `r1/scripts/configs/trackp_sft.json` | table pins, label settings, splits, training protocol (host-independent) |
| host config, HTCondor | `r1/scripts/configs/trackp_htcondor_v2.json` | image v2 digests; paths and GPU record `TODO_VERIFY_ON_HOST` for the cluster agent |
| shared replay inputs | `r1/c3/dataset.py` | `sweep_replay_inputs` factored out of `build_from_sweep` (no behaviour change) so the prompt builder replays exactly what the table builder replayed |
| offline model | `r1/c3/train/tiny.py` | `HashBagModel` (`--tiny --family hashbag`): CPU, no tokenizer or download, for the dry run |
| tests | `r1/tests/test_trackp_sft.py` | 26 tests, tiny CPU/synthetic dry run end to end (below) |

### 1.1 Labels — the label source plugs in; 7006–7010 are never read

`LabelBlockSource(label_block.jsonl, sweep="sweep1"|"sweep2")` reads the file that `r1.c3.audit evidence-run`
writes for the label seeds (row format of `audit.evidence_blocks`), plus `evidence_completion.json` for two things
only: the label block's sha256 and the label seeds. It never opens `evaluation_block.jsonl`, `runs.jsonl` (both seed
blocks) or a mixed `audits.jsonl`; a test spies on every `open` during a full build and checks this. It refuses: a
path naming an evaluation or mixed file; a label block beside `STOP.json`; a completion without label seeds
7001–7005 or with another label-block sha256; a row with a field outside the label-block schema, an audit row whose
seeds are not 7001–7005 (k = 5), or any field name matching `run.EVAL_COLUMNS`; a label for a proposal that is not in
the table, or whose node, `sigma_node` or inert status disagrees with the table row.

Sweep 2's B.2 (R1-SWEEP2-B2-DRAFT) is to write the same file through the same audit code; it plugs in with
`--label-sweep sweep2` and the sweep-2 table and index. The full consumption check `audit.verify_evidence_completion`
re-derives both blocks from `runs.jsonl` and therefore reads the evaluation seeds, so it is **not** run inside the
SFT process; the data manifest says so, and the agent that consumes an audit runs it separately before use.

Soft labels: `labels.soft_label`, mode `pooled_node` (R1-SOFT-SIGMA, s = sigma_node/√5), rule no-ops one-hot on bin 0.
`SyntheticLabelSource` gives deterministic synthetic labels for dry runs (never audit data).

### 1.2 Prompts and table binding

`sweep_prompts` resolves the sweep with `dataset.sweep_replay_inputs` (index, classification sidecar, pinned noise,
manifests, ledger counts — the code path of `build-sweep`), replays every root ledger with `replay_campaign`'s row
filter and serialises each proposal with `serialize.serialize_view` (`trackp_prompt/v2`, ≤ 1,024 tokens for every
pool tokenizer). Every replayed proposal's features must equal its table row's (`features_hash`), so each prompt is
bound to its table row; a replayed proposal outside the table, or a labelled proposal without a prompt, is refused.
Table pins (`trackp_sft.json`): `proposals.jsonl` `d0048567…` and `configs.json` `b585b727…` of the deepthought
rebuild (`W2_3_REBUILD_RUN_20261115.md`). `build.json` holds paths and the build commit, so it is recorded, not pinned.

### 1.3 Splits (spec §3.6; R1-MAIN-PROPOSER (e))

By instance, never by trial: per node, instances ordered by `sha256("trackp_sft/v1:" + instance)`; 3 test, 3 val, 12
train of 18 (proposed values). The assignment depends on the instance name only, so sweep 2 (same instance seeds)
gets the same assignment. `holdout_nodes` gives LONO folds. Test instances contribute no row to the data directory.
Cross-split duplicates — the same (node, incumbent, candidate) on two instances — have two policies, see §3 (1).

### 1.4 Stage S runner (spec §6.1, §4)

`run_stage_s`: L_S = RPS + CE (`loss: "rps"` for the CE-off ablation); AdamW, cosine, warm-up 5 %, effective batch 16
(host micro-batch × accumulation), ≤ 5 epochs, evaluation every ¼ epoch and at step 0, early stopping on val RPS with
patience 2, the best checkpoint loaded back; adapter lr must be on the grid {1e-5, 3e-5, 1e-4}, new heads 1e-3, new
token rows 1e-4. Eval hook, on the val instances' training labels: RPS, RPS skill vs the training base rate, NLL,
all-bins and top-1 ECE, PIT histogram, mean predictive sd, mean label sd, width ratio. Then temperature scaling on val
(R1-TEMPERATURE), saved as `best/temperature.json`, with val metrics before and after. `select_lr` picks the lr with
the lowest mean best val RPS over seeds (equal seed counts required). `Trainer` runs `run.guard_rows` on the rows.

## 2. Verification

- `r1/tests/test_trackp_sft.py`: **26 passed** (CPU, torch 2.6.0, Python 3.12). Synthetic sweep (9 instances of
  `digits_mlp`, ledgers → table rows by the table's own replay → prompts), label sources and every refusal, splits,
  both duplicate policies, a Stage S run on the hash-bag model (best checkpoint = selected, step-0 evaluation,
  temperature), refusal of an `y_eval` column by the trainer, `select_lr`, and the CLI end to end (`sft-data` →
  `sft-dev --tiny --family hashbag` → `sft-select`; `sft-dev --evidence EVIDENCE` and P.4 `sft` without its note
  STOP).
- Affected existing tests (the five files that exercise `build_from_sweep`, plus the Track P CLI, trainer, serialize,
  model and W2 budget tests): no new failure; the 11 `test_trackp_model.py` failures are the same on base `26177d82`
  in this environment (transformers 4.49 without the Qwen3.5 classes; no Hugging Face access).
- Full `r1/tests` suite: see the review record.
- **Real-ledger smoke (ENGINEERING; synthetic labels, whitespace token counter because Hugging Face is not reachable
  from this machine).** A local `build-sweep` at `main` `26177d82` through the refactored `sweep_replay_inputs`
  reproduced the deepthought table's `proposals.jsonl` (`d0048567…`) and `configs.json` (`b585b727…`) byte for byte.
  `sft-data` on that table with the pinned sweep index and classification: 4,999 prompts replayed (15 s), every one
  bound to its table row; synthetic labels on the 1,725 eligible proposals (B.2's expected population); a hash-bag
  Stage S run of 370 steps on CPU completed. Counts (24 test / 24 val / 96 train instances):

  | | `drop_from_train` | `exclude_from_heldout` |
  |---|---|---|
  | labelled (eligible) | 1,725 | 1,725 |
  | test-instance rows withheld | 262 | 262 |
  | dropped: pair also on a test instance | 756 | 0 |
  | dropped: train pair also on a val instance | 189 | 0 |
  | dropped: val pair also on a train instance | 0 | 240 |
  | **train rows** | **378** | **1,176** |
  | **val rows** | **140** | **47** |
  | test proposals whose pair is on a train/val instance | 674 (kept in test) | 674 (excluded by the P.4 evaluator) |

  None of these numbers is evidence; they show the size of the duplicate question below.

## 3. Open points for the author

1. **Cross-split duplicates (decision needed before any real use).** Every campaign of a node starts from the same
   configuration and B.2 audits each distinct configuration once (1,725 proposals, 466 configurations), so the same
   (node, incumbent, candidate) pair recurs across instances with the same label. Keeping such a pair on both sides of
   a split leaks the label. `drop_from_train` (default here) keeps the test population whole but leaves 378 training
   rows of 1,725; `exclude_from_heldout` keeps 1,176 training rows but makes val small (47) and restricts the test
   population to unseen pairs, which changes what the test number estimates. Other options: more val instances per
   node, or merging instances that share pairs into one split group (likely close to one group per node). Spec §3.6
   says "group duplicates … by edit hash across splits"; R1-MAIN-PROPOSER (e)(3) groups by (instance, incumbent hash,
   edit hash) across sources. Both policies here keep every pair inside one split of the data actually used.
2. **Split sizes** (3 test / 3 val / 12 train instances per node, salt `trackp_sft/v1`) are the Track P agent's
   proposal; R1-TRACKP-SFT-DEV does not fix them.
3. **Verification of a label block** (`audit.verify_evidence_completion`) reads the evaluation seeds by design and
   stays a separate step outside the SFT process; the manifest records that it was not run.
4. **Which table the label block was audited on.** The manifest records `table_matches_audit_table` (the completion's
   `proposals_sha256` against this table). If B.2 audits another build of the same ledgers, every label must still
   match its table row (node, `sigma_node`, inert status).
5. **Micro-batch per host.** `trackp_portal.json` has no `sft.micro_batch`, so TASL-2 / TASL-7 use 8 (× 2 accumulation);
   a 4B base may need a smaller one, set in the host config. `trackp_htcondor_v2.json` proposes 16 on H200.
6. **Released heads.** Kev's pointer head and Laya's decision head train at the adapter lr (as in E0 v2); new heads at
   1e-3.

## 4. How to run (unchanged on each host)

All commands from a clean paper checkout of the delivered branch, with the host's Track P environment.

**Data (any host with the paper repository; CPU; once per label source).** On deepthought the table is
`/work/dwong/htcondor_prep_20261114/w2_3_rebuild_20261115/tables/c3_features_v3_20261115T232007Z`; elsewhere copy it
(the pins check the bytes). Pool tokenizers need Hugging Face access or a cache with the pinned revisions.

```
python r1/scripts/trackp.py sft-data --table <table dir> \
  --sweep <paper>/results/r1/pilot/C3_sweep_index_20261028T033315Z.json --paper-root <paper> \
  --classification <paper>/results/r1/evidence/C3_sweep_classification_20261028.json \
  --labels synthetic --run-dir ~/r1_trackp/runs/sft_data/sweep1_v3_synthetic      # until B.2's labels exist
# once sweep-1 B.2 has completed (label block only; its completion file sits beside it):
  --labels <audit dir>/label_block.jsonl --label-sweep sweep1 [--label-freeze <freeze record>]
# sweep 2: the sweep-2 table/index (add its pin to trackp_sft.json) and --label-sweep sweep2
```

**Experiment agent, TASL-2 / TASL-7 (RTX 4090; `--config r1/scripts/configs/trackp_portal.json`, the default; GPU
lease taken by the command):**

```
python r1/scripts/trackp.py sft-dev --data ~/r1_trackp/runs/sft_data/<name>/data --base kev-0.8b \
  --lr 3e-5 --seed 0 --run-dir ~/r1_trackp/runs/sft_dev/kev-0.8b_lr3e-5_s0
python r1/scripts/trackp.py sft-select --runs <run dirs of one grid> --run-dir <out>
```

**Cluster agent, HTCondor H200, image v2 (`--config r1/scripts/configs/trackp_htcondor_v2.json`).** First, per
R1-QTORCH-AMEND, I2/I3 on v2 and one Track P smoke plus one E0 equivalence check on the GPU model; then fill the
`TODO_VERIFY_ON_HOST` values (`--check-config` lists them; real runs refuse a config that still holds one). Same
`sft-dev` command with `--config r1/scripts/configs/trackp_htcondor_v2.json`.

**Offline dry run (any CPU):** `sft-dev --tiny --family hashbag --allow-placeholders --lr 1e-4 --steps 20 ...`.

`sft-dev` writes only ENGINEERING_ONLY (DRYRUN with `--tiny`) and refuses other labels; P.4 Stage S evidence runs
use `sft` with `docs/r1/authorizations/trackp_p4_<date>.md`. Every run writes `manifest.json` (config, data
manifest sha256, base, model files, git state, environment, host and GPU) and `report.json`.
