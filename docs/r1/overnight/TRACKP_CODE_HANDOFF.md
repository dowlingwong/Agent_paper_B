# Track P Phase 1 handoff — code (26 Oct 2026)

**Status: pending independent review (STOP 1).** Track P agent (Claude Code) on zhixu portal, branch `trackp-20261026` (paper repo; harness unchanged). AI-assisted; ENGINEERING_ONLY / DRYRUN. CPU only (`CUDA_VISIBLE_DEVICES=""`), tiny random-weight models; no real weights, no GPU, no API call, no secrets. Authority: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` Phase 1; spec `docs/r1/TRACK_P_POST_TRAINING.md`.

Commits `4919f59` … `09138a9` (plus this handoff) on top of `ef3e2f3` (Phase 0). Items 1.1–1.5 and 1.7–1.10 were written in parallel by five worker agents in separate git worktrees (`trackp-20261026-{labels,models,serialize,clients,exam}`) and merged here with `--no-ff`; 1.6 and 1.11, the RPS unification and the Laya loader fix were done by the coordinating agent.

## Environment

- Scratch venv `~/r1_trackp/venvs/trackp-cpu` (outside the repos): uv 0.13.5 (user install, `~/.local/bin`), Python 3.12.15 (Kev requires ≥ 3.12), harness deps from the harness `uv.lock` (`uv sync --frozen --extra dev`), plus torch 2.14.1+cpu, transformers 5.19.0, peft 0.21.2, safetensors 0.8.0, scipy, lightgbm, datasets 5.1.0 (Kev's checkpoint loader imports it), all with `--exclude-newer 2026-10-11`; code repos pinned and installed `--no-deps`: `kev` @ `2074cc4`, `laya` @ `a478221`, `startlux-decide` @ `a99977d` (their own pins — Kev: torch < 2.9; StartLux: transformers 5.8 — conflict with the rest; see deviations). Full list: `trackp_code_20261026/pip_freeze_trackp-cpu.txt`.
- Tokenizer files only (never weights) of Qwen3.5-0.8B/4B-Base, Laya typed-decisions and StartLux Instant 0.8B/2B/4B at the Phase 0 revisions in `HF_HOME=~/r1_trackp/hf_cache`. Tests that need them skip when the cache is absent.
- Commands: paper `AR_HARNESS_ROOT=~/r1_trackp/autoresearch_harness HF_HOME=~/r1_trackp/hf_cache HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES= python -m pytest -q -p no:cacheprovider --continue-on-collection-errors r1/tests`; harness `PYTHONPATH=src python -m pytest -q -p no:cacheprovider --continue-on-collection-errors tests` (delete the untracked `paper/tables/artifact_completeness_report.txt` afterwards).

## Tests

| | baseline (before any change, same venv) | after |
|---|---|---|
| paper `r1/tests` | 407 passed, 1 skipped, 11 failed, 4 collection errors | 536 passed, 1 skipped, 11 failed, 4 collection errors (+129 new tests) |
| harness `tests` | 434 passed, 9 failed, 1 error | 434 passed, 9 failed, 1 error (harness unchanged) |

The baseline failing set (lists in `trackp_code_20261026/`) is environmental: **the harness commit pinned on `main` (`6afdb0e`, Track H) is not on GitHub** (Phase 0 finding H1), so this clone's harness `r1` (`264011e`) lacks `SKIP_DISPLAY_ONE_LINE` / `is_control_plane_skip`: 4 Track H modules fail to import and 10 tests fail on the missing hooks; plus the known `test_real_runner_desktop_dryrun`. Harness failures: missing ledgers / KDD paper artefacts in a fresh clone. The after-run failing set is identical to the baseline; every new test passes.

New test files (all CPU): `test_trackp_trainer.py`, `test_trackp_cli.py` (incl. SIGKILL-and-resume through the CLI), `test_trackp_sidecar_loader.py`, `test_trackp_model.py`, `test_trackp_losses_metrics.py`, `test_trackp_soft_label_v2.py`, `test_trackp_serialize.py`, `test_trackp_exam_synthetic.py`, `test_trackp_exam_analyze.py`, `test_trackp_clients.py`.

## Items against "Done when"

| # | Done | Evidence / notes |
|---|---|---|
| 1.1 `r1/c3/train/model.py` | Yes (tiny models) | `PointerWrapper` (Kev via `kev.model` @ 2074cc4: encoding, special tokens, pointer head, row form on hybrids; warm start through `kev.checkpoint`), `HeadWrapper` → `LayaWrapper`, `StartLuxWrapper`; `BinTokenWrapper`; `ReasonThenBinWrapper` (Qwen; generate + teacher-forced scoring). Softmax-12 and cumulative-11 heads. Shapes, save→load bit-identical belief and action logits, sha256 manifest, tampered file refused — for every wrapper and both head forms. Kev variant of reason-then-bin not built (raises): `kev.model` drops the LM head. |
| 1.2 `serialize.py` | Yes | One template from what `featurize_view` reads (`ROW_FIELDS`); spy, future-row, own-outcome and extra-field leak tests; ≤ 1,024 tokens under all 6 pool tokenizers (896 for the neutral text + 128 framing reserve); truncation = drop oldest history lines (recorded in `meta`); worst case and all > 1,000 pilot proposals fit. |
| 1.3 `losses.py`, `metrics.py` | Yes | Hand-computed tests. One RPS definition for all of Track P (`metrics.rps` = `losses.rps`, see Q1). |
| 1.4 soft label v2, action target | Yes | `soft_label(..., sigma_mode="pooled_node")`, s = σ̂_node/√K from the C1 30-seed table `results/r1/pilot/E1_20261022T214606Z/summary.json` (sha256 checked); versions `soft_label/v1_se_audit` / `v2_pooled_node`; existing callers explicit `se_audit`; pilot `c3_audit_pilot_20261019T001338Z` rebuilt under v1 byte-identical (sha256 of `assemble` ×2 and `evaluate()` JSON equal to the pre-change code). `labels.action_target` (spec §3.5). |
| 1.5 `packing.py` | Yes | Spec mask + tree-depth positions; packed = unpacked ≤ 1e-5 fp32 on a tiny full-attention model; refused on a Qwen3.5 hybrid. |
| 1.6 `r1/scripts/trackp.py`, `configs/trackp_portal.json`, `trainer.py`, `run.py` | Yes | Subcommands `spike`, `toy`, `e0`, `probes`, `exam` run; `sft` (P.4), `a6` (P.5), `rb` (P.6) exist and refuse until their phase (the shared loop and losses they will use exist). Resumable (checkpoint per ¼ epoch with `COMPLETE` marker; data order a function of (seed, epoch)); SIGKILL mid-run then rerun gives bit-identical adapter and heads and no repeated completed step. Manifest per run (base revision, adapter/heads sha256, data hash, seed, git commits, GPU-lease log, evidence label). Refuses evaluation-seed columns before the P.4 final evaluation; refuses `TODO_VERIFY_ON_HOST` (only `--tiny` dry runs may pass `--allow-placeholders`); evidence runs need their authorization note; GPU lease = Track X STATUS check + no foreign compute process + `fcntl.flock` on `~/r1_locks/gpu0.lock`; real bases on CPU are a STOP. Tiny dry runs of spike for kev / laya / startlux / qwen_control, both head forms: all reload-identical. |
| 1.7 `exam_synthetic.py` | Yes | E0 set (10×7 grid, 10 held-out cells, 3,000/1,000, seed 20261026) committed `r1/c3/train/data/e0_v1.jsonl.gz` + sha256, regenerates byte-identically; E0 metrics/pass; E6 A1–A5 constructors and pass criteria. |
| 1.8 `exam_analyze.py`, `r1/c3/rules/p3_rule_v1.yaml` | Yes | Rule committed with its sha256 (`8df1abad…f840c`) before any analysis code; refusal on mismatch; every step and tie-break tested on synthetic results. |
| 1.9 `r1/c3/jev_client.py` | Yes | `POST /v1/systemone` per the public TypeSafe docs; versioned model refused otherwise; one request per state per repeat; monotone CDF; 3 repeats; full JSON log with returned version; key from env only (redacted); version mismatch = STOP. Fake server. |
| 1.10 `r1/c3/rb_demos.py` | Yes | DeepSeek `chat/completions`, `deepseek-flash`; prompt only from `DecisionPrompt.state` + `.proposal`; leak tests; peak-hour refusal; logs. Fake server. |
| 1.11 `r1/c3/serve.py` `TorchLoraLoader` | Yes (tiny model) | Builds the pinned wrapper from the pin's `model` spec and loads the saved adapter + heads (`write_model_pin` writes P.7 pins with sha256); answers rows that carry the serialised view (`row["prompt"]`); `SidecarPrior` forwards `prompt` when present; timeout and no-prompt rows fall back to A1 (unchanged path). |

## Deviations and interpretations (for the reviewer)

1. **10 finite bin edges, not 11.** `labels.EDGES` (−∞, −3, −2, −1, −0.5, −0.15, 0.15, 0.5, 1, 2, 3, +∞) has 10 interior edges between the 11 non-inert bins; spec §2.3/§5.1 and the runbook say "11". Cumulative-11 = no-op Bernoulli + 10 threshold sigmoids (11 outputs); the Jev rung = 10 edge Nouls + 1 inert Noul (11 questions; `include_inert=False` gives 10). (Q2)
2. **RPS normalisation.** Spec §6.1 writes Σ_k (P_k − Y_k)² + bin-0 Brier; §6.4 says RPS ≤ 1. Implemented once: 0.5 · (Brier₀ + (1 − y₀) · mean_k (Q_k − R_k)²) on the renormalised non-inert parts — proper, in [0, 1]. Two workers had written different versions; unified on this one (`61608dc`). (Q1)
3. **StartLux on transformers 5.19 is a port.** The released `bidirectional.py` refuses transformers ≠ 5.8.x. `StartLuxBidirectional` gives full-attention layers a non-causal key mask and DeltaNet layers the stock mask through 5.19's per-layer mask mapping and runs the same three self-checks (pass on tiny models). Not compared with the 5.8 reference on real weights: Phase 3 needs a separate transformers 5.8 venv for that comparison (and Kev's own pin says torch < 2.9, which Phase 2 must weigh against the driver-535 wheel question, Phase 0 risk R1).
4. **Kev record mapping.** Kev state = loop state; each proposal = one Kev question (instruction = proposal + question; options = 12 bins). Laya/StartLux: proposal placed before the state so end-of-state truncation never cuts the edit.
5. **E6 A5** runs on the bin-token family only (spec), listing order via `bin_order` with canonical options; `DecisionPrompt.options` permuted in a prompt would mislabel bin tokens in `BinTokenWrapper.prefix` — the runner never does that.
6. **Exam rule step 4.** Finalist 1 = first of the tied set after the tie-breaks, not necessarily the raw E3 top (rule comments). (Q3)
7. **Sidecar rows.** The online controller (`RuleController` via `proposal_row`) does not yet attach `row["prompt"]`; until it does (Track H follow-up, `serialize.serialize_view` on the E1 view), a real sidecar answers every row with the A1 fallback. Not changed here (outside 1.11).
8. **`r1/c3/rules/`** directory sits next to `r1/c3/rules.py`; no `__init__.py`, so `import r1.c3.rules` still loads the module (checked).

## Questions for the author

1. RPS definition (deviation 2).
2. Edges: 10 interior edges — cumulative-11 and the Jev inert Noul as implemented (deviation 1)?
3. Exam rule step-4 reading (deviation 6).
4. StartLux: is a separate transformers 5.8 venv for the Phase 3 reference comparison acceptable?
5. Harness pin `6afdb0e` must reach GitHub `r1` before Track H tests can run here (Phase 0 H1).
