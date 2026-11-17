# U1 — Track G G.0 licence and asset availability audit (17 November 2026)

**Status.** Unit **U1** of Track G **G.0**, **documents only**. Written 17 Nov 2026 by a Mac-local
worker agent (Claude), AI-assisted, from public web sources only: **no host access, no GPU, no clone, no
run, no experiment, no commit/push**. It records licences, availability and asset provenance as observed
on **2026-11-17 (01:15–01:20 CET)**; every licence claim below carries the URL it was read from. Written in
the worktree `ops-tasl-20261116` (HEAD `c921983e` when writing began; the file is carried by commit
`45fcf0fa` and later; the two 17 Nov rows are not in `ops-tasl-20261116`'s ancestry yet), uncommitted at
review time.

**Authority.** `R1-TRACKG-G0-GO` (17 Nov 2026): G.0 on Ada = U0 (deploy + Paper A status) → **U1
(licence and asset availability, documents only)** → U2 (per-node raw cost) → U4 (census report);
ENGINEERING_ONLY, no noise floor, no D21 and no D28 in G.0 (those are G.1b on L40S,
`R1-TRACKG-G1B-HOST`); no review authority is claimed here. `R1-TRACKG-PORT-OWNER` (17 Nov): the **Mac
agent** writes the port kit for each T1 candidate per `prompts/TRACKG_PORT_CHECKLIST.md`. The two rows are
`docs/r1/PLAN.md` §10 lines 1258–1259 on branch **`author-d8-confirm-20261117` @ `26177d82`**; they are
**not yet in this worktree's HEAD `c921983e`**, which is why this file cites them by branch and commit.
The U1 scope and resumable-unit framing follow `TRACKG_G0_ADA_CENSUS_20261116.md` §5 ("U1 — licence and
asset availability audit (docs only)").

**This file authorizes nothing.** It is an engineering record and **not a legal opinion**. A dataset or
code base is "licensed for our use" only where an upstream licence text says so and is cited below;
otherwise the cell says **unknown / not stated**, which means *not found on the cited page*, not that no
licence exists.

**Reading rules.**
1. *declared* = stated in a README or dataset card; *verified* = read in a fetched page (all fetches are
   listed in §11). Nothing here is verified beyond what §11 shows.
2. Repository HEAD shas were resolved on 2026-11-17 (cited per row) so a port kit can pin them.
3. "Publicly reachable" is an observed HTTP status from a normal web client, not a statement about
   reachability from Ada/HoreKa compute nodes; egress is a experiment-agent question (§9).
4. The four candidate suites are exactly those the T1 list names; **1GC-7RC is not a suite**
   (`R1-1GC-FALLBACK`, adopted 4 Nov 12:45; `RUNBOOK` Track G T1 row). Its public datasets are recorded
   only because `RUNBOOK` T1 keeps them as *possible extra tasks* whose tier and fold are open until G.3.

## 1. Scope

Per candidate task/suite (T1 list from `R1-BX-D1/D2` and `TRACK_G_RUNBOOK.md` §1):

| Suite | Candidates recorded |
|---|---|
| autoresearch | the single short fixed-step variant (1 task) |
| MLGym (lighter tasks) | CIFAR-10, Fashion-MNIST, House Price, a MinAtar/MountainCar-type RL task |
| MLAgentBench (light tasks, third suite) | cifar10, imdb, ogbn-arxiv |
| 1GC-7RC public datasets (not a suite) | TinyShakespeare, Forest Cover, ETTh1, AG News, ogbg-molhiv |

For each: upstream repository URL, code licence (name + SPDX where known), task-asset/dataset licence or
terms, public reachability, GPU-model-specific notes, size/estimated download, and any access restriction
that could block ENGINEERING_ONLY research use (§2–§8). §9 lists what U1 cannot close and who must close
it; §10 states what the port kit must carry.

## 2. Suite 1 — autoresearch (1 task)

- **Repository.** [`github.com/karpathy/autoresearch`](https://github.com/karpathy/autoresearch) — created
  6 Mar 2026; default branch `master`; HEAD **`228791fb499afffb54b46200aca536f79142f117`** (2026-03-26);
  public (GitHub API HTTP 200). Repo is three files plus `pyproject.toml`/`uv.lock`; ~530 KB.
- **Code licence: MIT — *declared*, not shipped as a file.** The README ends with a `## License` section
  reading "MIT" ([README](https://github.com/karpathy/autoresearch/blob/master/README.md)). The
  repository has **no `LICENSE` file** (root file listing on 2026-11-17 contains only `.gitignore`,
  `.python-version`, README, analysis notebook, `prepare.py`, `program.md`, `progress.png`,
  `pyproject.toml`, `train.py`, `uv.lock`) and the GitHub API reports `"license": null`. SPDX as declared:
  `MIT`. A licence text should be copied into the port kit and the README statement recorded; the owner
  (karpathy) has not shipped the text.
- **Task assets.** `prepare.py` (frozen, data prep + tokenizer + dataloader + the fixed `evaluate_bpb`
  metric), `train.py` (the single editable file), `program.md` (human instructions). The suite's own agent
  loop is not used (integration principle: only task assets become nodes).
- **Dataset.** `prepare.py` downloads from
  `https://huggingface.co/datasets/karpathy/climbmix-400b-shuffle/resolve/main`; `MAX_SHARD = 6542`,
  `VAL_SHARD = 6542` pinned; default `--num-shards 10` → **10 training shards + shard 06542 = 11 parquet
  shards**. HF tree on 2026-11-17 lists ~91.0–92.3 MB per shard → **≈1.0 GB default download**; the full
  corpus is **600 GB** per the dataset page.
- **Dataset licence: MIT — *declared on the dataset card*.** The HF dataset card front-matter is
  `license: mit` and the dataset page shows "License: mit"
  ([dataset card](https://huggingface.co/datasets/karpathy/climbmix-400b-shuffle)). The card body is
  otherwise empty: **the underlying corpus provenance (what ClimbMix is, which sources were mixed) is not
  documented on the card**, so MIT is the uploader's assertion for the packaged shards, not a
  source-by-source clearance. Public, no gate observed.
- **GPU-model-specific note: YES.** README requires "a single NVIDIA GPU (**tested on H100**)", Python
  3.10+, `uv`; every run is a **fixed 5-minute wall-clock budget** and the metric is `val_bpb` (lower is
  better). The README also gives explicit tuning advice for smaller GPUs (lower `DEPTH`, lower
  `MAX_SEQ_LEN`, `WINDOW_PATTERN=L`, …) and links small-platform forks. Consequence for G.0/G.1: the
  suite has **no fixed-step argument** (R1-BX-D5 forbids wall-clock budgets), so the fixed-step wrapper is Mac-agent port-kit work (`TRACK_G_RUNBOOK.md` G.0.2, G.1), while the raw-cost
  measurement itself is U2 / experiment-agent work.
- **Access restrictions / terms.** None stated beyond MIT. Network needs: `huggingface.co` +
  LFS/Xet CDN (data), PyPI (via `uv sync`, including `rustbpe`, `tiktoken`, `torch`).
- **U1 blocker/unknown.** No `LICENSE` file; corpus provenance undocumented; egress and `rustbpe` wheel
  availability on the run host unverified (§9).

## 3. Suite 2 — MLGym (lighter tasks; 4 candidates)

- **Repository.** [`github.com/facebookresearch/MLGym`](https://github.com/facebookresearch/MLGym) (Meta
  GenAI + UCSB NLP); default branch `main`; HEAD **`9d40c1b5035202018cd7091fb4e83a9c68b377c0`**
  (2025-08-10); public (GitHub API HTTP 200). README carries a "**experimental framework … under heavy
  development**" warning.
- **Code licence: CC-BY-NC 4.0 — this is the most consequential finding in this audit.** The repo
  `LICENSE` is the full *Attribution-NonCommercial 4.0 International* text, and the README states: "The
  majority of this code is licensed under CC-BY-NC 4.0 … However portions of the project are available
  under separate license terms: SWE-Agent and Modded-NanoGPT are released under MIT license; Gymnax and
  Gymnax-blines are released under Apache 2.0 License"
  ([LICENSE](https://github.com/facebookresearch/MLGym/blob/main/LICENSE),
  [README](https://github.com/facebookresearch/MLGym/blob/main/README.md)). SPDX `CC-BY-NC-4.0`.
  Consequences that matter for us, read off that licence text:
  - NonCommercial only: use "not primarily intended for or directed towards commercial advantage" is
    permitted; academic research use fits the ordinary reading, but a commercial downstream (or a
    commercial partner/artefact) would not. This is the licence, not a legal opinion.
  - Attribution + licence notice + modification indication are required when the material (including
    **Adapted Material**) is shared. Porting task assets into the harness and putting them on a branch
    is sharing Adapted Material → each node bundle must carry the notice and attribution (§10).
  - **No patent grant**: the CC 4.0 text states "Patent and trademark rights are not licensed under this
    Public License".
  - CC licences are not designed for software; there is no source-form/notice machinery like MIT/Apache.
  - Some portions are MIT (SWE-Agent, Modded-NanoGPT) and Apache 2.0 (Gymnax/Gymnax-blines); which files
    those cover is not itemised upstream — a port kit must state per-file provenance.
- **Suite and task assets.** The README states "MLGym-Bench consists of 13 diverse … tasks". The repo's
  `configs/tasks/` holds 19 YAML files (the 13 tasks plus near-duplicate/`L1` variants); the four T1
  candidates are present as **default suite tasks** (`configs/tasks/`):
  `imageClassificationCifar10.yaml`, `imageClassificationFMnist.yaml`,
  `regressionKaggleHousePrice.yaml`, and for the RL candidate both `rlBreakoutMinAtar.yaml`
  (MinAtar Breakout) and `rlMountainCarContinuous.yaml` / `…Reinforce.yaml` (MountainCar-type). Assets =
  `data/<task>/` starter code + `evaluate.py` + `memory.json`, dataset configs under `configs/datasets/`.
- **Datasets / task-asset licences (per candidate).**
  - **CIFAR-10**: config `datasets/cifar10HF.yaml` → HF dataset `uoft-cs/cifar10`; the HF dataset card
    declares **`license: unknown`** (API tags and card metadata), download 143,646,105 B (≈144 MB). The
    CIFAR-10 page itself states no licence. **No licence to cite.**
  - **Fashion-MNIST**: config `datasets/fashionMnistHF.yaml` → HF dataset
    `zalando-datasets/fashion_mnist`; card declares **`license: mit`**, download 36,106,894 B (≈36 MB)
    ([card](https://huggingface.co/datasets/zalando-datasets/fashion_mnist)).
  - **House Price**: config `datasets/kaggleHousePrice.yaml` points at `data/regressionKaggleHousePrice/data`
    (`is_local: true`), but that path does **not** exist in the repo (API HTTP 404 on 2026-11-17); the
    shipped data is `data/regressionKaggleHousePrice/_helpers/train.csv` (460,676 B) plus
    `_generate_split.py`, i.e. the split is generated locally from a bundled Kaggle-derived train file.
    Source is the Kaggle competition **"House Prices — Advanced Regression Techniques"** ([kaggle.com/competitions/house-prices-advanced-regression-techniques](https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques); Ames housing, De Cock 2011); the bundled `_helpers/train.csv` identity is inferred from the file name and columns (no row/column check against the Kaggle train file was performed). Kaggle competition data is subject to Kaggle's competition rules/terms, and MLGym's
    CC-BY-NC does not itself relicense Kaggle data → **ambiguous; record the exact URLs, do not claim a
    licence**.
  - **MinAtar/MountainCar RL**: no external dataset download; the environment comes from the code stack
    (`data/rlBreakoutMinAtar/requirements.txt`: `jax[cuda12]`, `gymnax`, `flax`, `optax`, …), and the
    README attributes Gymnax/Gymnax-blines to **Apache 2.0**. Agent-generated env/episode data only.
- **Runtime and size.** Tasks run inside a container: Docker or Podman, GPU via `nvidia-container-runtime`
  (README step 5: `sudo dnf install -y nvidia-container-toolkit`); image
  [`aigym/mlgym-agent:latest`](https://hub.docker.com/r/aigym/mlgym-agent): **amd64 7,248,568,196 B
  (≈7.25 GB)**, digest `sha256:86d438d6a6c08df7f574af26864dfc416a70624bb6d4e8e5f4d825a41b3d4ba4`,
  **last pushed 2024-11-04** (arm64 1.18 GB); image contents (whether task data are baked in) not
  verified. Apptainer `.sif` is the RUNBOOK §3 fallback when Docker is unavailable.
- **GPU-model-specific note: none in the repo.** The framework is GPU-agnostic; no tested-model statement
  in the README. Any table comparability rule comes from R1-BX-D5, not upstream.
- **Access restrictions that matter.** (i) CC-BY-NC non-commercial + attribution + no patent grant;
  (ii) container requirement with a root-installed NVIDIA runtime on the host; (iii) egress to
  `huggingface.co` (CIFAR-10/F-MNIST) and `registry-1.docker.io` (image); (iv) Kaggle-data terms for
  House Price.

## 4. Suite 3 — MLAgentBench (light tasks; 3 candidates)

- **Repository.** [`github.com/snap-stanford/MLAgentBench`](https://github.com/snap-stanford/MLAgentBench)
  (Stanford SNAP); default branch `main`; HEAD **`5d71205cc20a8e95d43aa7cb7120e89ca3323e31`**
  (2024-04-28); public (GitHub API HTTP 200). Paper arXiv:2310.03302.
- **Code licence: MIT — *verified*, with a defect.** The repo `LICENSE` is the MIT text, but its
  copyright line is the **unfilled template** `Copyright (c) [year] [fullname]`
  ([LICENSE](https://github.com/snap-stanford/MLAgentBench/blob/main/LICENSE)). SPDX `MIT`; no copyright
  holder is named anywhere in the licence file. Record the defect; the MIT grant text is present.
- **Suite and task assets.** README and paper say 13 tasks; the repo's `MLAgentBench/benchmarks/`
  currently holds **15 task folders** (CLRS, amp-parkinsons-disease-progression-prediction, babylm,
  bibtex-generation, cifar10, fathomnet, feedback, house-price, identify-contrails, imdb,
  literature-review-tool, llama-inference, ogbn-arxiv, spaceship-titanic, vectorization) — the
  count difference is not resolved in this audit. The three T1 candidates (`cifar10`, `imdb`,
  `ogbn-arxiv`) are **default suite tasks**; their data are **not vendored** and are fetched on first run.
- **Task data sources and licences.**
  - **cifar10**: `benchmarks/cifar10/scripts/prepare.py` calls `torchvision.datasets.CIFAR10(...,
    download=True)` → canonical CIFAR-10 archive from `cs.toronto.edu` (~10^2 MB; not measured here).
    **CIFAR-10 licence: unknown** (same finding as the HF mirror in §3).
  - **imdb**: no `prepare.py`; `benchmarks/imdb/env/train.py` calls `datasets.load_dataset("imdb")` →
    HF dataset `stanfordnlp/imdb`. Card metadata is **`license: other`** and the "Licensing Information"
    section says "More Information Needed" (`download_size` 83,446,840 B ≈83 MB) — **terms are
    unspecified upstream; do not claim a licence**; the canonical citation is Maas et al. 2011.
  - **ogbn-arxiv**: `benchmarks/ogbn-arxiv/scripts/prepare.py` calls
    `PygNodePropPredDataset(name="ogbn-arxiv")` → OGB download. OGB's dataset page lists
    **License: ODC-BY** for ogbn-arxiv
    ([OGB node-property docs](https://ogb.stanford.edu/docs/nodeprop/)); attribution required. Download
    size not measured here (order 10^2 MB; the HF mirror `OGB/ogbn-arxiv` returned **HTTP 401** without
    auth, so plan on the OGB host, not the HF mirror).
- **Runtime and size.** Two routes: `pip install -e .` + `bash install.sh` (Python 3.10), or the Docker
  image [`qhwang123/researchassistant:latest`](https://hub.docker.com/r/qhwang123/researchassistant):
  **amd64 21,779,902,631 B (≈21.8 GB)**, digest
  `sha256:6b3690a13ba44fd089086e9860a298ed49a179d9a04a5406c0df074569a3aabe`, pushed **2023-06-24**;
  README recommends running it as root inside the container. Apptainer `.sif` fallback per RUNBOOK §3.
- **GPU-model-specific note: none in the repo.** Tasks are PyTorch; the README does not state a tested
  GPU model. Whether the 2023 image ships a CUDA-compatible torch build is **not verified**.
- **Access restrictions that matter.** Code is permissive; the *data* are the constraint (CIFAR-10 and
  IMDb licences unstated). Image is 21.8 GB (egress/storage/time), and pulling it needs
  `registry-1.docker.io`. Some other MLAgentBench tasks use Kaggle data (README requires Kaggle API
  credentials), but **none of the three U1 candidates do** — the Kaggle note applies to the suite, not to
  cifar10/imdb/ogbn-arxiv.

## 5. 1GC-7RC public datasets — **1GC-7RC is not a suite**

- **Suite status.** Replaced 4 Nov 2026 by MLAgentBench as the third suite (`R1-1GC-FALLBACK`; `STATUS.md`
  records the author's ruling "1GC-7RC没公开repo" / "1GC-7RC 换成 MLAgentBench我同意"). This audit keeps
  that decision: **the datasets below are studied only because the T1 row keeps them as possible extra
  tasks; their tier, whether they count toward 12–16, and their fold role are open until G.3.**
- **Repository availability — discrepancy recorded.** arXiv 2605.17046 v2 (19 May 2026) abstract says
  "The benchmark, harness, and all evaluation artifacts are publicly available on GitHub at this https
  URL" → [`github.com/Strolchii/1GC-7RC-Benchmark`](https://github.com/Strolchii/1GC-7RC-Benchmark). On
  2026-11-17 that URL returns **HTTP 404** in both the HTML page and the GitHub API
  (`/repos/Strolchii/1GC-7RC-Benchmark` → `"Not Found"`), i.e. private, deleted or never published. **Therefore no code
  or harness licence can be cited for the suite**, and the 4 Nov fallback remains the correct state. If
  the author ever wants 1GC-7RC back, this 404 is the item to resolve; otherwise no action.
- **Per-dataset records** (the five datasets the T1 row keeps as possible **T1 extra tasks**; the runbook's
  T1 row *also* names TinyImageNet and VOC, which `R1-BX-D2` assigns to **T2** and which this U1 list
  excludes — if G.3 wants them they need a licence audit first, TinyImageNet being ImageNet-derived; the
  row itself names seven):

| Dataset (domain) | Public source | Licence / terms | Availability & size |
|---|---|---|---|
| TinyShakespeare (language modelling) | HF [`karpathy/tiny_shakespeare`](https://huggingface.co/datasets/karpathy/tiny_shakespeare); text from [`karpathy/char-rnn`](https://github.com/karpathy/char-rnn) (API `license: null`, no licence field) | **No licence metadata** on the dataset card (card has citation only, to char-rnn); the *text* is Shakespeare, i.e. public domain, but the packaging states no terms | Public (HTTP 200); `download_size` 1,115,394 B (~1.1 MB) |
| Forest Cover (tabular/vision) | UCI ML Repository **Covertype**, id 31 ([dataset page](https://archive.ics.uci.edu/dataset/31/covertype)), DOI 10.24432/C50K5N | **CC BY 4.0** (stated on the UCI page; attribution required) | Public (HTTP 200); `covtype.data.gz` 10.7 MB; 581,012 instances × 54 features |
| ETTh1 (time series) | [`zhouhaoyi/ETDataset`](https://github.com/zhouhaoyi/ETDataset) (HEAD `1d16c8f4f943005d613b5bc962e9eeb06058cf07`); HF mirror [`thuml/Time-Series-Library`](https://huggingface.co/datasets/thuml/Time-Series-Library) config `ETTh1` | **Conflicting / ambiguous:** GitHub API reports `license: other / NOASSERTION` and the README only asks to cite Informer (AAAI 2021); the HF mirror card declares **`license: cc-by-4.0`**; OpenDataLab's ETT page ([openxlab.org.cn/datasets/OpenDataLab/ETT](https://openxlab.org.cn/datasets/OpenDataLab/ETT), snapshot 2026-11-17) claims **CC BY-ND 4.0**. Three sources, three answers — record all three URLs and do not pick one without author input | Public (HTTP 200 in all three); ETTh1.csv small (hourly, 2 years; exact bytes not fetched) |
| AG News (text classification) | HF [`fancyzhx/ag_news`](https://huggingface.co/datasets/fancyzhx/ag_news); original AG corpus from ComeToMyHead (Zhang et al. 2015) | **`license: unknown`**; the card states the corpus is "provided by the academic comunity [sic] for research purposes" — a research-use statement, **not an open licence** | Public (HTTP 200); `download_size` 19,820,267 B (~20 MB); 120,000 train / 7,600 test |
| ogbg-molhiv (graph) | OGB [`ogbg-molhiv`](https://ogb.stanford.edu/docs/graphprop/) (MoleculeNet-derived, RDKit-processed) | **MIT** (stated on the OGB page); HF mirror card also states MIT | Public via OGB tools (HTTP 200 docs); 41,127 graphs; download size not measured here |

- **U1 finding.** Four of the five have a citable licence or clear terms (Forest Cover CC BY 4.0,
  ogbg-molhiv MIT, TinyShakespeare public-domain text with no packaging terms, AG News research-use with
  no licence); **ETTh1 has three conflicting licence claims**. None blocks ENGINEERING_ONLY research *in
  principle*, but AG News and ETTh1 would need an author decision before any label table that cites them.

## 6. GPU-model-specific and runtime notes (summary)

| Suite / candidate | GPU-model-specific note upstream | Runtime need |
|---|---|---|
| autoresearch | **Yes**: single NVIDIA GPU, "tested on H100"; 5-minute wall clock; README gives smaller-GPU tuning guidance | `uv sync` (PyPI), `huggingface.co` data, 1 GPU; **needs the Mac-agent fixed-step wrapper** (no step argument upstream) |
| MLGym (all four candidates) | **No** repo-level note | Docker/Podman + `nvidia-container-runtime` (root install) or Apptainer `.sif`; 7.25 GB image; `huggingface.co`; JAX/CUDA for the RL task |
| MLAgentBench (all three candidates) | **No** repo-level note | Docker image 21.8 GB (or `install.sh`); `cs.toronto.edu` (CIFAR-10), `huggingface.co` (IMDb), OGB host (ogbn-arxiv); PyTorch |
| 1GC-7RC datasets | Not applicable at dataset level (1GC is a single-GPU, 40–120 min wall-clock *benchmark* per its abstract; no repo to check) | Dataset-specific; Forest Cover CSV, ogbg-molhiv via OGB, ETTh1 CSV, AG News text, TinyShakespeare text |

## 7. Audit result table

Legend: **Owner** = who must deliver/produce the thing (Mac agent port kit per `R1-TRACKG-PORT-OWNER`;
"U1" = this record only; "none" = not a suite / not ported). **Unknowns** column = explicit
"not verified / needs author or experiment-agent input". Sizes are observed metadata, not measured downloads.

| Candidate / suite | Code licence (SPDX) | Asset licence (SPDX) | Availability | Blockers / unknowns | Owner | Not verified / needs input |
|---|---|---|---|---|---|---|
| **autoresearch** (1 task) | **MIT** (declared in README `## License`; **no LICENSE file**; GitHub API `license: null`) | climbmix-400b-shuffle: **MIT** (HF card); corpus provenance undocumented | Public, HTTP 200; default data ≈1.0 GB; repo ~530 KB | no LICENSE text shipped; no fixed-step argument upstream (wall-clock 5 min) → wrapper needed; PyPI `rustbpe` | Mac agent port kit; U1 record | experiment-agent: HF + PyPI egress; author: accept README-only MIT? |
| **MLGym — CIFAR-10** | **CC-BY-NC-4.0** (repo LICENSE); portions MIT/Apache 2.0 | `uoft-cs/cifar10` HF card: **license unknown**; ≈144 MB | Public, HTTP 200; container 7.25 GB (amd64) | NC licence + attribution + no patent grant; container/runtime; data licence unstated | Mac agent port kit; U1 record | **author**: is CC-BY-NC acceptable for T1 + paper artefact? **experiment-agent**: Apptainer/container + HF egress |
| **MLGym — Fashion-MNIST** | same MLGym CC-BY-NC-4.0 | `zalando-datasets/fashion_mnist`: **MIT**; ≈36 MB | Public, HTTP 200 | as above (suite licence dominates the bundle) | Mac agent port kit; U1 record | **author**: CC-BY-NC acceptance; experiment-agent: container/egress |
| **MLGym — House Price** | same MLGym CC-BY-NC-4.0 | Kaggle "House Prices" competition data ([competition](https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques)), bundled as `_helpers/train.csv` (460,676 B) + local split generator; Kaggle competition terms, no explicit licence in repo; bundle identity inferred | Public repo; **no external download**; config's `data/…/data` path 404s in repo | Kaggle competition terms vs MLGym redistribution; data licence ambiguous | Mac agent port kit; U1 record | **author**: accept Kaggle-terms data?; confirm split identity |
| **MLGym — RL (MinAtar Breakout / MountainCar)** | same MLGym CC-BY-NC-4.0 | Gymnax/Gymnax-blines **Apache-2.0** (per MLGym README); env generated, no external data | Public; jax[cuda12] deps | NC suite licence; GPU/JAX stack; container | Mac agent port kit; U1 record | experiment-agent: CUDA/JAX + container; **author**: CC-BY-NC acceptance |
| **MLAgentBench — cifar10** | **MIT** (LICENSE; copyright line unfilled placeholder) | CIFAR-10 via torchvision: **licence unknown** | Public, HTTP 200; torchvision download ~10^2 MB; image 21.8 GB | image size/egress; data licence unstated | Mac agent port kit; U1 record | **author**: accept unstated CIFAR-10 terms?; experiment-agent: image pull + `cs.toronto.edu` egress |
| **MLAgentBench — imdb** | **MIT** | `stanfordnlp/imdb`: **`license: other`, "More Information Needed"** (≈83 MB) | Public, HTTP 200 | IMDb terms unspecified; PyTorch/DistilBERT fine-tune needs HF model weights? (the task text/paper describes a DistilBERT fine-tune, but the repo has no prepare script and the pretrained-weight source/licence is not recorded in it) | Mac agent port kit; U1 record | **author**: accept unstated IMDb terms?; experiment-agent: HF egress |
| **MLAgentBench — ogbn-arxiv** | **MIT** | OGB ogbn-arxiv: **ODC-BY** (attribution); size unmeasured | Public docs, HTTP 200; HF mirror returns 401 | OGB host egress; size; image 21.8 GB | Mac agent port kit; U1 record | experiment-agent: OGB download host + image pull |
| **1GC-7RC extra: TinyShakespeare** | n/a — **1GC-7RC is not a suite**; repo 404 | HF card: **no licence metadata**; Shakespeare text public domain | Public, HTTP 200; ~1.1 MB | packaging terms unstated; tier/fold open (G.3) | none (not ported); U1 record | **author/G.3**: include as extra task? |
| **1GC-7RC extra: Forest Cover** | n/a | UCI Covertype: **CC BY 4.0** | Public, HTTP 200; 10.7 MB | none beyond attribution; tier/fold open | none (not ported); U1 record | **author/G.3**: include as extra task? |
| **1GC-7RC extra: ETTh1** | n/a | **Conflicting**: GitHub NOASSERTION / HF mirror CC-BY-4.0 / OpenDataLab CC BY-ND 4.0 ([openxlab.org.cn/datasets/OpenDataLab/ETT](https://openxlab.org.cn/datasets/OpenDataLab/ETT), 2026-11-17) | Public, HTTP 200 | three conflicting licence claims; no clean citation | none (not ported); U1 record | **author**: which licence governs?; **G.3**: include? |
| **1GC-7RC extra: AG News** | n/a | HF card **license unknown**; "research purposes" statement | Public, HTTP 200; ~20 MB | no open licence; research-use only | none (not ported); U1 record | **author**: accept research-use terms?; **G.3**: include? |
| **1GC-7RC extra: ogbg-molhiv** | n/a | OGB: **MIT** | Public via OGB; 41,127 graphs | size; OGB egress; tier/fold open | none (not ported); U1 record | experiment-agent: OGB host; **G.3**: include? |

## 8. What this changes for G.0 (and what it does not)

- **No item is a hard STOP for ENGINEERING_ONLY census work** at the licence level *as far as U1 can
  verify*, because the census uses the suites' task assets in a private harness on an internal cluster and
  not commercially. The two items that need a decision **before any ported asset is committed or shared**
  are (i) **MLGym's CC-BY-NC 4.0** (attribution + NonCommercial + no patent grant; adaptation and
  redistribution into a harness branch is "sharing Adapted Material" under that licence) and (ii) the
  **unstated data licences** (CIFAR-10, IMDb, AG News) and **ETTh1's three conflicting claims**, which
  cannot be called licensed without an author/legal call.
- **No new authorisation is created here.** This U1 record does not move any gate; it supplies the U4
  census's licence/availability columns and the port-kit provenance requirements below.

## 9. Blockers and unknowns (U1 cannot close these)

1. **MLGym CC-BY-NC 4.0 acceptance (author).** The suite code and its bundled task assets are
   NonCommercial; our use is academic and ENGINEERING_ONLY, but the port bundle is a redistribution that
   must carry attribution, the licence notice and a modification statement, and CC 4.0 grants **no patent
   licence**. Needs an explicit author line before the Mac-agent bundles are merged/shared.
2. **Unstated asset licences (author).** CIFAR-10 (both suites), IMDb, AG News: "unknown"/"other". They are
   ubiquitous in ML benchmarking, but U1 will not assert a licence. Needs an author decision (accept with
   citation, or substitute a cleanly licensed task).
3. **ETTh1 conflict (author).** Three sources, three licences; no single citation is defensible as-is.
4. **Container/runtime path on the census host (cluster agent).** MLGym 7.25 GB and MLAgentBench 21.8 GB
   images need Docker/Podman + `nvidia-container-runtime` (root) or Apptainer `.sif` conversion. The
   RUNBOOK §3 route (Apptainer) is only confirmed on deepthought2 (`R1-APPTAINER-HOST`); the Ada/HoreKa
   host check is a experiment-agent item and is **outside U1's no-host scope**.
5. **Egress allowlists (cluster agent).** Needed hosts: `huggingface.co` (+ LFS/Xet CDN),
   `cs.toronto.edu` (CIFAR-10), OGB download host (`ogb.stanford.edu`/`snap.stanford.edu`),
   `registry-1.docker.io`, PyPI. Not verified from any compute node.
6. **Unmeasured sizes.** ogbn-arxiv download and the MLGym image contents (data baked in or fetched at
   run time) were not verified; the U2 raw-cost unit measures runtime/VRAM, not download sizes.
7. **autoresearch licence hygiene.** MIT is declared in the README only; no `LICENSE` file exists. The port
   kit should copy the README statement and record the pinned commit; the dataset card's MIT is the
   uploader's assertion and the corpus provenance is undocumented.
8. **1GC-7RC repo 404.** The arXiv v2 "publicly available" claim does not hold on 2026-11-17. The 4 Nov
   `R1-1GC-FALLBACK` stands; no licence for the 1GC harness exists to cite. If the author wants 1GC-7RC
   back, this is the item to raise; if not, the datasets are recorded only for a future G.3 decision.
9. **No suite ships a licence manifest.** None of the three repos ships a per-task/per-dataset licence
   file; the port kit must build one (below).

## 10. Port-kit licence requirements (recommendation to the author/coordinator and the Mac agent)

**Recommendation to the author/coordinator:** amend `prompts/TRACKG_PORT_CHECKLIST.md` with a
licence/provenance checkbox, and once adopted the Mac agent applies it. Then each node bundle should carry,
next to the `NodeSpec` and the 3–5 declared diffs, a short `LICENCES.md`
with: upstream URL + **pinned commit** (table §7 gives the HEAD shas resolved on 2026-11-17 — pin those,
do not track `main`), the code licence and its file path in the upstream repo (or the README statement
where no file exists, as with autoresearch), each dataset's source URL and licence exactly as cited here,
the HF dataset-card revision sha it read, the attribution string, and — for MLGym assets — the CC-BY-NC
4.0 notice, the "Modified" indication, and
the MIT/Apache sub-components that apply. HF dataset-card revisions observed on 2026-11-17: cifar10 `0b27149`, imdb `e628166`, ag_news
`eb185aa`, fashion_mnist `531be5e`, climbmix `915333b`, Time-Series-Library `2b66e59`,
tiny_shakespeare `c7a7ff3`, ogbg-molhiv `2725c3f`; pin these with the citations above.
Also record container digests if a container is used
(`sha256:86d438d6…` MLGym amd64, `sha256:6b3690a1…` MLAgentBench amd64) so a later check can re-pull the
same image.

## 11. Availability evidence — fetch log (2026-11-17, Europe/Berlin)

| URL | Result |
|---|---|
| `https://api.github.com/repos/karpathy/autoresearch` + `/contents/` + `/commits/master` | 200; `license: null`; no LICENSE file; HEAD `228791fb…` |
| `https://raw.githubusercontent.com/karpathy/autoresearch/master/README.md` / `prepare.py` | 200; README "## License MIT"; data URL + shard logic |
| `https://huggingface.co/datasets/karpathy/climbmix-400b-shuffle` (+ `README.md` raw, `/api/.../tree/main`) | 200; card `license: mit`; 600 GB; ~92 MB/shard |
| `https://github.com/facebookresearch/MLGym` + `/LICENSE` + `/README.md` + `/commits/main` | 200; CC-BY-NC 4.0 + MIT/Apache portions; HEAD `9d40c1b5…` |
| `https://api.github.com/repos/facebookresearch/MLGym/contents/{tasks,configs/tasks,configs/datasets,data,…}` | 200; 19 task YAMLs, dataset configs, `data/rlBreakoutMinAtar/requirements.txt`, house-price `_helpers/train.csv`; `data/regressionKaggleHousePrice/data` → **404** |
| `https://huggingface.co/api/datasets/{uoft-cs/cifar10,zalando-datasets/fashion_mnist,stanfordnlp/imdb,fancyzhx/ag_news,karpathy/tiny_shakespeare}` | 200; licences `unknown` / `mit` / `other` / `unknown` / none |
| `https://github.com/snap-stanford/MLAgentBench` + `/LICENSE` + `/README.md` + `/commits/main` + benchmark trees | 200; MIT text with placeholder copyright; HEAD `5d71205c…`; 15 task folders; prepare scripts for cifar10/ogbn-arxiv, `load_dataset("imdb")` for imdb |
| `https://hub.docker.com/v2/repositories/{aigym/mlgym-agent,qhwang123/researchassistant}/tags` | 200; sizes/digests as cited in §3–§4 |
| `https://ogb.stanford.edu/docs/{nodeprop,graphprop}/` | 200; ogbn-arxiv **ODC-BY**, ogbg-molhiv **MIT** |
| `https://archive.ics.uci.edu/dataset/31/covertype` | 200; **CC BY 4.0**, 10.7 MB |
| `https://api.github.com/repos/{zhouhaoyi/ETDataset,karpathy/char-rnn}` + ETDataset README | 200; ETDataset `license: other / NOASSERTION`, HEAD `1d16c8f4…`; char-rnn `license: null` |
| `https://huggingface.co/api/datasets/thuml/Time-Series-Library` | 200; card `license: cc-by-4.0` (HF mirror claim, conflicts with the origin) |
| `https://arxiv.org/abs/2605.17046` | 200; v2 abstract claims a public GitHub repo link |
| `https://github.com/Strolchii/1GC-7RC-Benchmark` + `https://api.github.com/repos/Strolchii/1GC-7RC-Benchmark` | **404** both (HTML page and API) |
| `https://huggingface.co/api/datasets/OGB/ogbn-arxiv` | **401** without auth (HF mirror gated; use the OGB host) |

## 12. References

- Authority: [`docs/r1/PLAN.md`](../../PLAN.md) §10 `R1-TRACKG-G0-GO`, `R1-TRACKG-PORT-OWNER`
  (branch `author-d8-confirm-20261117` @ `26177d82`, lines 1258–1259); `R1-BX-D1/D2/D5/D12/D14`;
  `R1-1GC-FALLBACK`; `R1-TRACKG-G1B-HOST`.
- Runbook and scope: [`docs/r1/RUNBOOK.md`](../../RUNBOOK.md) Track G; [`TRACK_G_RUNBOOK.md`](../../prompts/TRACK_G_RUNBOOK.md)
  §1, §2, §4 (G.0, G.1); [`TRACKG_PORT_CHECKLIST.md`](../../prompts/TRACKG_PORT_CHECKLIST.md);
  [`TRACKG_G0_ADA_CENSUS_20261116.md`](../TRACKG_G0_ADA_CENSUS_20261116.md) §3–§5;
  [`TRACKG_U0_DEPLOY_20261117.md`](../../proposals/TRACKG_U0_DEPLOY_20261117.md).
- U1 is documents only; the next G.0 unit is U2 (per-node raw cost, one resumable unit per node), then U4
  (census report `TRACKG_CENSUS_<date>.md`).


## 12. Author decision (17 November 2026, `R1-TRACKG-LICENCES`)

The author signed `R1-TRACKG-LICENCES` (`author-decisions-20261117b` @ `45fb94cc`): Track G is used for
academic research; **no dataset is redistributed** (repo/public artefacts carry only download scripts and
hashes, the appendix lists every licence/source); MLGym (CC-BY-NC) is used non-commercially with notice;
CIFAR-10 / IMDb / AG News have no declared licence and are cited as generic research datasets with
disclosure; ETTh1's conflicting claims are handled by the strictest one; Kaggle House Price data is
downloaded by the user under the competition terms; 1GC-7RC 404 keeps the 4 Nov fallback; and
`prompts/TRACKG_PORT_CHECKLIST.md` gets a "licence & provenance" step (Mac agent applies it with the port
kit). This resolves the author decisions listed in §7/§9; the coordinator/port-checklist item remains with
the Mac agent per `R1-TRACKG-PORT-OWNER`.
