# Sweep 1 readiness after D28 node repair — 27 October 2026

AI-assisted (OpenAI Codex). **ENGINEERING_ONLY / PILOT; readiness STOP, not sweep authorization.** The author must authorize sweep 1 separately. Results are pending independent review.

## D21 and D28

After rule `b2f8b74` and harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, breast_w, sonar and wdbc pass D21. Blood_transfusion fails D21 (mean P(wrong) 0.07715375 < 0.10) and is not re-run or used. The separate climate check at the same harness pin passes D21. See [repair D21](DT_D28_D21_REPAIR_20261027.md) and [climate D21](DT_D28_CLIMATE_D21_20261027.md). The untouched digits_mlp, tabular_mlp, credit_approval and ionosphere retain their 22 October D21 and prior Phase 6 D28 results; the harness diff from `897d83c` modifies only the four repair-node configs, leaving the four untouched nodes and climate unchanged.

| D28 node | Trials | Novelty | Invalid rate | Keeps after trial 1 | Verdict |
|---|---:|---:|---:|---:|---|
| openml_breast_w | 20 | 0.70 | 0.00 | 2 | pass |
| openml_climate | 20 | 0.55 | 0.05 | 2 | pass |
| openml_sonar | 20 | 0.85 | 0.00 | 5 | pass |
| openml_wdbc | 20 | 0.75 | 0.00 | 1 | pass |

The D28 campaign used two instances × W=10, memory on, structure-only `manager_proposal/v1`, pinned llama.cpp and one TITAN; 80 trials. Server offload was full before and after (5,253 MiB); runner return code 0. Exact raw records are under `results/r1/engineering/liveness_llamacpp_20261027T122913Z/`. The legacy reused driver writes `AI-assisted (Claude)` in its run record; it was actually invoked by the OpenAI Codex operator. This copied field is preserved rather than rewritten.

The D28 manifest records the harness pin but does **not** record a paper commit or config SHA. The operator launch checked a clean paper branch against its then-current remote head; the original config SHA observed after the run and before its edit was `85431afc775803de885a362dbfb1797323ae907a626a35f4bc871f2bae374d70`. These observations do not make the manifest proof of runtime paper/config bytes. Trial references point into `/tmp/r1_d28_liveness_20261027_attempt02/`; an unmodified relative-path archive of the temporary work, server logs, driver and config check is `temporary_provenance.tar.gz`, SHA256 `3ca5a6ece49bd08865bc21d837a956d8c83ca7b419cd709b62945fd497a8e30c`. References in original ledgers remain unchanged.

## Proposed sweep-1 pinned set — author gate remains

- Nodes: `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`, `openml_credit_approval`, `openml_sonar`, `openml_climate`. Climate replaces blood_transfusion under R1-D28-REPAIR after its own D21 and D28 pass.
- Paper pin: `main` HEAD at launch, to be recorded then; no push to `main` during the agreed launch window. A successor R1-DT-PIN row must record the final pin at launch.
- Harness: `6adf3859de66c4814fcf376eed59880fbd8eeaf7`; the accepted resume-stamp fix is excluded. Config `r1/scripts/configs/c3_sweep_deepthought.json` SHA256 `52a6ea870fb38077af665a8e86dfd9efc851c44e1d110eb3c4484a90f24b69cc`; `--check-config` passed. Config and `HARNESS_PIN_C3` are prepared on this branch, not yet merged to main.
- llama.cpp `version: 0.7.0-dev (build 1, commit 620d222)`; Qwen2.5-Coder-7B-Instruct Q4_K_M GGUF SHA256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`; schema `manager_proposal/v1`.
- 18 instances × two memory modes (`append_only_summary`, `none`) × W=20 per node; audits K=10, seeds 7001–7005 label and 7006–7010 evaluation, never mixed. One batch on one TITAN, `footprint_mib=5253`, workers=16; local-disk scratch, durable results on Ceph. Prior estimate 14–20 h sweep and 2–3 h audit is provisional.

STOP: do not start sweep 1 without the author-committed `docs/r1/authorizations/c3_sweep1_<date>.md`, independent acceptance and a matching final pin set. No evidence sweep or B.2 audit has started.
