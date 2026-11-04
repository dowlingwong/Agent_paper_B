# DRAFT — Authorization: C3 B.1 environment replay (packet e1)

**Draft by the Mac-local worker (Claude), MAC_LOCAL_RUNBOOK_20261104 M3 step 5; AI-assisted, 4 November 2026. This is not an authorization.** The author commits it, edited or as is, under `docs/r1/authorizations/c3_env_replay_<date>.md`, as R1-B2-REPLAY-GO says, after M3 is independently accepted. Placeholders are in `<angle brackets>`. Each one says where its value comes from.

---

# Authorization: C3 B.1 environment replay (ENGINEERING_ONLY)

Committed on the author's instruction of `<date, time>`: "`<author's words>`". Basis: R1-B2-REPLAY-GO (4 Nov 11:29); M3 accepted in `docs/r1/reviews/MAC_M3_REVIEW_<date>.md` at commit `<M3 accepted commit>`.

## What is authorized

One CPU-only, `ENGINEERING_ONLY` run of the predeclared 16-case replay, exactly as `docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md` ("Predeclared replay protocol") sets it out, with the driver `r1/scripts/c3_env_replay.py`. It is carried out by **the operator** (R1-HANDOVER-04NOV moves the replay from the deepthought agent to the operator). It is not B.2 and authorizes no audit.

## Pins

| Item | Value | Source |
|---|---|---|
| Paper code | `<M3 accepted commit>` on branch `<branch the operator deploys>` | the M3 review; the operator deploys only a reviewed hash the author passed on (MAC runbook §0) |
| Driver | `r1/scripts/c3_env_replay.py` at that commit | M3 |
| Harness | the preserved batch checkout `/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness`, clean at `6adf3859de66c4814fcf376eed59880fbd8eeaf7` | R1-SWEEP1-CLASSIFY; the driver checks it |
| Interpreter | the batch wrappers `…/autoresearch_harness/.venv/bin/python{,3}` → `/ceph/dwong/r1_prepare_20261025/venv/bin/python`; Python 3.13.15; scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1; `uv.lock` SHA256 `dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090` | replay draft; environment investigation |
| Package baseline | `/ceph/dwong/r1_prepare_20261025/freeze_with_lightgbm.txt`, SHA256 `c760b28f2d03cfd31ae491b13b13ec6a348caee603b051349d9f85f9af282406`, plus only `narwhals==2.27.1` | replay draft |
| Sources | index `results/r1/pilot/C3_sweep_index_20261028T033315Z.json` (`812468e2…`); sidecar `results/r1/evidence/C3_sweep_classification_20261028.json` (`bb6d891c…`); frozen trees `6b1c0c61…` / `468e57ce…` | R1-SWEEP1-CLASSIFY; C3_B1_CORPUS_FREEZE_20261031 |
| Cases | 16, fixed: per node, the smallest `append_only_summary` instance seed, budget indices 1 and 2 (list in `reports/MAC_M3_DRYRUNS_20261104.md` §1) | replay draft |

## Host and workers

- **Host:** deepthought, CPUs only. No GPU and no manager model. The driver sets `CUDA_VISIBLE_DEVICES=""`.
- **Workers: 1.** The driver runs the 16 cases one after another, each with `OMP/OPENBLAS/MKL_NUM_THREADS=1`, as the sweep's collector did.
- **Estimated duration:** under 5 minutes of CPU, from the recorded trial times of about 2 s. R1-B2-REPLAY-GO allows 1–2 h, including setup.
- **Co-tenancy:** check other users' load before starting and leave at least 10 cores free (operator runbook O4; R1-COMPUTE).
- **Scratch:** a new local `/tmp/r1_c3_env_replay_<stamp>`.
- **Output:** a new directory outside the batch and outside `results/r1/evidence/`, for example `<paper checkout>/results/r1/engineering/C3_env_replay_<stamp>`. It is labelled ENGINEERING_ONLY.

Command, run inside the batch environment: `. <batch>/env.sh`, with `AR_HARNESS_ROOT` set to the batch harness and `PYTHONDONTWRITEBYTECODE=1`. The interpreter is the batch venv:
```
python -B -m r1.scripts.c3_env_replay --paper-root <reviewed paper checkout> \
  --harness <batch>/autoresearch_harness --batch <batch> \
  --scratch /tmp/r1_c3_env_replay_<stamp> --out <output dir> --min-free-bytes <operator estimate>
```
First run the same command with `--dry-run`, then run it without `--dry-run`.

## Pass rule (declared before execution; not changeable afterwards)

**PASS** requires all 16 cases to reproduce their recorded primary metric (`val_score` for digits_mlp and tabular_mlp, `val_auc` for the six OpenML nodes) **with zero tolerance**. The comparison is the emitted token against the recorded token, never re-rounded. It also requires every environment check to pass (summary `verdict: PASS`). Anything else is not a pass.

## STOPs (each one: retain everything, report, no automatic retry)

- Any environment check fails: the wrapper target, Python or library versions, `uv.lock`, a dist-info mtime at or after 27 Oct 15:48 UTC, a package difference from the 25 Oct freeze other than narwhals 2.27.1, the worker `python3` not being the batch wrapper, or the driver not running in the batch venv.
- Any source fails verification: index, sidecar, manifests, corpus trees, original blobs, archive members, a recovered patch differing from the recorded patch, or a missing or unsuccessful selected trial. No later trial is substituted.
- A seed cannot be established, or falls in 7001–7010.
- An OpenML node would download data.
- An LLM client module is loaded, or a GPU is touched.
- A case's metric is missing, non-finite or differs; the worker changed files; the data cache changed.
- Interruption, inaccessible records, or disk or file-count headroom below the floor (Ceph 50 GiB).

## Report and what follows

- The operator reports each case (`cases.jsonl`, raw logs, `replay_plan.json`, `summary.json` or `STOP.json`) on its `ops-*` branch. An independent review follows.
- Only if the review confirms all 16 cases and all environment checks may a decision record carry the disclosure the replay draft fixes, verbatim: "B.1 numerics environment reconstructed from uv.lock and the batch venv, confirmed by replay; no freeze snapshot was taken at launch." It must also say at once that the batch `.venv` executables were wrappers to the shared venv, not a separately built venv, and it must not overstate when dependencies were installed. A passed replay is a bounded reproducibility check of these 16 worker evaluations. It is not proof that every original dependency or all 288 roots were identical. It says nothing about LLM seed replay (R1-SWEEP1-CACHE-DISCLOSURE).
- **This note does not start B.2.** B.2 needs the separate ruling e2 (R1-B2-REPLAY-GO).
