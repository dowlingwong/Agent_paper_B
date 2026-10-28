# TabPFN version pin — proposal (28 October 2026)

AI-assisted (Claude, chat session) for the open item of PLAN §10 **R1-TABPFN**: "the TabPFN version; the coordinator proposes one after checking the installed package". **This is a proposal only; the author decides.** Nothing has been installed on any host and no weights have been downloaded.

Revised after independent review (`docs/r1/reviews/MAC_LOCAL_DELIVERABLES_REVIEW_20261028.md`, findings T1–T9; none was blocking).

## What was checked (28 Oct)

- PyPI metadata of `tabpfn`.
- The wheel `tabpfn-9.2.0-py3-none-any.whl` (sha256 `bf8edb860cf490ab021d0ba6e91a9798f1b549bdb220066599661c8fc6d6089f`, matching PyPI). It was downloaded without dependencies and its source read.
- The Hugging Face model cards of `Prior-Labs/tabpfn_3_5` and `Prior-Labs/TabPFN-v2-reg`.
- The repository README's licence section.

The v2 licence file itself could not be retrieved (both `priorlabs.ai/tabpfn-license/` and the HF `LICENSE` file failed to load; see "What the author has to do").

## Facts

| Item | Finding | Source |
|---|---|---|
| Latest package | `tabpfn` **9.2.0**, released 2026-10-12. Python ≥ 3.10, torch ≥ 2.5. Code licence Apache-2.0 | PyPI; wheel `licenses/` |
| Default model | `settings.tabpfn.model_version` defaults to **v3.5**: checkpoint `tabpfn-v3.5-20260909.safetensors` in `Prior-Labs/tabpfn_3_5`, a single multitask checkpoint for both classifier and regressor | `tabpfn/settings.py:37–38`; `tabpfn/model_loading.py:210–223` |
| Selectable versions | v2, v2.5, v2.6, v3, v3.5, v3.5-fast | `tabpfn/constants.py:31–39` |
| Gating | **Every version from v2.5 on** needs a one-time licence acceptance with Prior Labs (`ux.priorlabs.ai`, Licenses tab) and an API key in `TABPFN_TOKEN`. The licence check contacts the Prior Labs licence server at download, and `save_token` writes the key to `~/.cache/tabpfn/auth_token`. The licence lookup also queries the Hugging Face API with the user's HF token, and the gated-repo error asks for HF terms acceptance and `HF_TOKEN`. **v2 has no acceptance step** and a direct-download fallback | `tabpfn/model_loading.py:458–460, 557–570`; `tabpfn/browser_auth.py` (`_get_license_name`, `verify_token`, `save_token`); `tabpfn/errors.py:31–74` |
| v3.5 weights licence | `tabpfn-3-5-license-v1.0`: "permissive for research and limited internal evaluation". Testing, evaluation and internal benchmarking are allowed. The model, derivatives and outputs "cannot be used for any commercial or production purpose". The card does not say whether research results may be published, and cites no paper | HF card `Prior-Labs/tabpfn_3_5`; README (v2.5–v3.5 "released under non-commercial licenses") |
| v2 weights licence | `priorlabs-1-1`: "Apache 2.0 with an additional attribution requirement". The requirement is §10 of `LICENSE.txt` in `Prior-Labs/TabPFN-v2-reg`, as quoted by the independent re-review. It applies when the weights, a derivative, or a product containing them is distributed or made available. It then requires: a copy of the licence; a prominent "Built with PriorLabs-TabPFN" on each related page or document; and a name beginning with "TabPFN" for any distributed model trained or fine-tuned from the weights or outputs. Internal benchmarking without external communication is exempt. Peer-reviewed: Hollmann et al., *Nature* 2025, doi:10.1038/s41586-024-08328-6 | HF card and `LICENSE.txt` of `Prior-Labs/TabPFN-v2-reg`; README (`METADATA:164`) |
| What R1-TABPFN needs | Regression with the full predictive distribution: `predict(..., output_type="full")` returns logits plus a `FullSupportBarDistribution`, which is integrated onto the 12 canonical bins. Row embeddings for R-A1 (`TabPFNRegressor.get_embeddings`). Fine-tuning (`tabpfn.finetuning`, `FinetunedTabPFNRegressor`) | `tabpfn/regressor.py:151–173, 2344–2366`; `tabpfn/finetuning/finetuned_regressor.py:155` |
| Scale | No subsampling by default (`SUBSAMPLE_SAMPLES = None`). Pre-training limits: v2 10,000 rows / 500 features; v2.5 50,000 rows / 2,000 features; TabPFN-3 and later up to 1,000,000 rows; v3.5 card 20,000 features. Our ~2,000 labelled rows and tens of features are inside all of them | `tabpfn/inference_config.py:213` and `_get_v2_config`; `tabpfn/regressor.py:184, 439–443`; HF card |
| Settings override | `Settings` reads `TABPFN_*` variables from a `.env` file in the working directory, so a stray `TABPFN_MODEL_VERSION` or `TABPFN_MODEL_CACHE_DIR` would silently change a run | `tabpfn/settings.py:27–29` |

## Options

| Option | For | Against |
|---|---|---|
| **A. v3.5** (newest release and package default) | Newest model; the natural default a reviewer would expect | Gated: needs a Prior Labs account, licence acceptance and an API key, possibly HF access too, and reviewers need the same to reproduce. Silent on publication. Fine-tuned weights are derivatives under a non-commercial, "limited internal evaluation" licence, so releasing them or their predictions may not be allowed. No paper to cite (cite as software plus model card) |
| **B. v2** (*Nature* 2025) | Peer-reviewed and citable, ungated, and reproducible by anyone, subject to the §10 attribution and naming obligations; Apache-2.0-based licence | Older. A reviewer may ask why the newest version was not used. A paper or code release that uses it must carry "Built with PriorLabs-TabPFN" and a copy of the licence |
| **C. Both** (recommended) | v3.5 as the primary TabPFN rung (newest), with v2 beside it as the citable, ungated and releasable reference | One more rung to run. Both are expected to be cheap (in-context needs no training; fine-tuning ~2,000 rows on a 4090 is expected to take minutes, **not measured**) |

## Design point to settle with the pin

**Regression target and width.** TabPFN regresses a scalar. The natural target is z = Δ_label / σ_node from the five label seeds (7001–7005), and the 12-bin belief is obtained by integrating the predictive bar distribution over the canonical bin edges, with the no-op bin set by the rule layer. This predictive distribution includes label noise, whereas the other arms' soft labels fix the width (σ_node/√K, or `se_audit` for the gate arms). RPS is therefore not exactly like-for-like across arms. **Open for R1-TABPFN:** accept the difference and report it, or deconvolve the known label width.

## Proposed pin (if C is chosen)

- Package `tabpfn==9.2.0`, wheel sha256 as above. Install it in its own venv on TASL-7, the R1-TABPFN host, so that the pinned `trackp-gpu` venv is not changed (tabpfn pulls in lightgbm, skrub and pydantic-settings).
- **v3.5:** `Prior-Labs/tabpfn_3_5`, file `tabpfn-v3.5-20260909.safetensors`. Record the HF revision and file sha256 at first download, as for the models in `r1/c3/train/registry.yaml`.
- **v2:** `Prior-Labs/TabPFN-v2-reg`, file `tabpfn-v2-regressor.ckpt`, the package default for v2. Record the revision and sha256 at download.
- Pass `model_version` and the checkpoint path explicitly in code; never rely on the package default. Record `tabpfn.settings` (model_version, cache dir) in every manifest, and run without a `.env` file in the working directory.

## What the author has to do

1. Choose A, B or C.
2. For A or C:
   - read the v3.5 licence text (`tabpfn-3-5-license-v1.0`) and confirm that reporting results in a paper is acceptable; ask Prior Labs if unsure;
   - confirm whether fine-tuned v3.5 weights and their predictions may be released with the code; if not, release only v2 artifacts;
   - create the Prior Labs account, accept the licence and place `TABPFN_TOKEN` in `~/.config/r1/secrets.env` on TASL-7 (mode 600, like the other keys);
   - if the HF repo is gated, accept its terms on Hugging Face and make `HF_TOKEN` available there too;
   - allow network access from TASL-7 to `ux.priorlabs.ai` and its API for the first download;
   - after the download, delete `~/.cache/tabpfn/auth_token` or set it to mode 600.
3. For B or C: confirm §10 of the v2 `LICENSE.txt`. A paper or code release that reports or distributes v2 results needs a copy of the licence and a prominent "Built with PriorLabs-TabPFN". Any released fine-tuned model needs a name beginning with "TabPFN". Internal benchmarking without external communication is exempt.
4. Decide the regression-target and width point above.
5. Record the choice as a PLAN §10 row; that closes the R1-TABPFN open item.
