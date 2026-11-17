# Independent review — Track G G.0 U1 licence/asset availability audit

**Reviewer.** Fresh independent reviewer agent (no prior involvement in this unit).
**Date/time of review.** 17 November 2026, ~01:20–01:55 CET (Europe/Berlin). URL re-checks done live on
this date; all observed values below are from that window.
**Object under review.** `docs/r1/reports/trackg_g0_20261117/U1_LICENCE_AVAILABILITY_20261117.md`,
canonical bytes **sha256 `02d13324de4d559df094fd0328c0c37bf631decaf19a57f821ae705e93fb7c3a`**, **335 lines**
(recomputed in the worktree, matches the bytes I was asked to review).
**Worktree / state.** `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`,
branch `ops-tasl-20261116`, HEAD `45fcf0fa`; the file is **untracked** (`??`), as the audit states it is
uncommitted. No commit/push made by this review; review file is uncommitted.
**Authority used for the review.** `R1-TRACKG-G0-GO` and `R1-TRACKG-PORT-OWNER` read verbatim in
`docs/r1/PLAN.md` lines **1258–1259** on branch `author-d8-confirm-20261117` @ `26177d82` (branch tip
`26177d82…` confirmed); `R1-ADA-CENSUS` (PLAN.md:773), `R1-TRACKG-G1B-HOST` (PLAN.md:1209),
`R1-1GC-FALLBACK` (PLAN.md:804), `R1-APPTAINER-HOST` (PLAN.md), `TRACK_G_RUNBOOK.md` §1–§4,
`prompts/TRACKG_PORT_CHECKLIST.md`, `TRACKG_G0_ADA_CENSUS_20261116.md` §5.
**Review scope.** Documents only: no host access, no GPU, no clone, no run, no commit/push. Licence
readings are checks of cited public pages, not legal advice.

## Verdict

**ACCEPTED** — no BLOCKING, no MAJOR. Nine MINOR fixes (all editorial/citation-completeness; none changes
a decision). The audit may be **recorded as the completed U1 docs-only census unit** once M1–M5 and M9 are
applied as text edits (M6–M8 are a wording/process tightening that can ride along; no re-review needed).
The audit's substantive position is right: **no verified licence-level STOP** for ENGINEERING_ONLY census
work, **but two author decisions gate the port/commit/sharing step** (MLGym CC-BY-NC 4.0 and the
unstated/unknown asset licences), exactly as §8–§9 of the audit frame it.

## 1. Scope (VERIFY 1) — PASS, one wording fix (M1)

- Docs-only is declared in the status block (no host/GPU/clone/run/commit) and the evidence is a fetch
  log (§11), not execution. Every measurement-like number is marked as metadata or "not measured"
  (§7 legend line 236; §9 item 6). No capability or measurement claim is made that the audit did not
  verify. **PASS.**
- Declared candidates match the T1 list the authority names: autoresearch (1 task), MLGym (CIFAR-10,
  Fashion-MNIST, House Price, MinAtar/MountainCar RL), MLAgentBench (cifar10, imdb, ogbn-arxiv),
  1GC-7RC public datasets **as extras, explicitly "not a suite"** — correct per `R1-1GC-FALLBACK`
  (PLAN.md:804: "1GC's public datasets may be used as extra tasks but do not count as a suite"). **PASS.**
- One inaccuracy: §5 line 206 says "**the five public datasets named in the T1 row**", but the T1 row in
  `TRACK_G_RUNBOOK.md` §1 names **seven** (TinyShakespeare, Forest Cover, ETTh1, AG News, ogbg-molhiv,
  TinyImageNet, VOC). The audit then correctly notes the two excluded ones, so the conclusion is right but
  the sentence contradicts its own parenthetical. `R1-BX-D2` assigns TinyImageNet/VOC to **T2**, so
  excluding them from a T1-candidate audit is defensible — see **M1** for the exact rewrite.
- The authority framing is accurate: G.0 on Ada = U0 → U1 → U2 → U4, ENGINEERING_ONLY, no noise floor / no
  D21 / no D28 (those are G.1b on L40S per `R1-TRACKG-G1B-HOST`); and the two 17 Nov rows are indeed **not
  in worktree HEAD** (verified: `git grep` for both ids in `HEAD:docs/r1/PLAN.md` returns nothing) — the
  audit's branch+commit citation is the correct way to cite them. The census §5 U1 framing ("per candidate
  task/suite record repository, dataset and task-asset licence/availability; flag the 1GC-7RC non-suite
  status; no GPU; resumable per suite") is reproduced faithfully.

## 2. Accuracy of licence/availability claims (VERIFY 2) — PASS (all decision-relevant claims correct)

I re-fetched the decision-relevant sources on 2026-11-17. Observed results:

| # | Audit claim (location) | Re-check result (URL) | Match |
|---|---|---|---|
| 1 | MLGym code licence **CC-BY-NC 4.0**; README: "majority … CC-BY-NC 4.0", SWE-Agent/Modded-NanoGPT MIT, Gymnax/Gymnax-blines Apache 2.0 (lines 93–99) | `raw.githubusercontent.com/facebookresearch/MLGym/main/LICENSE` = full CC BY-NC 4.0 text; README `/LICENSE` §License quote matches **verbatim** | ✓ |
| 2 | CC-BY-NC consequences: NonCommercial, attribution + licence notice + "Modified" indication, **no patent grant** (lines 100–112) | CC 4.0 text §2(b)(2) "Patent and trademark rights are not licensed"; §3(a)(1)(a–c) attribution/notice/modified; §1(i) NonCommercial definition — all as paraphrased | ✓ |
| 3 | MLAgentBench code **MIT**, copyright line is the unfilled placeholder (lines 155–158) | `…/snap-stanford/MLAgentBench/main/LICENSE` = MIT with `Copyright (c) [year] [fullname]` | ✓ |
| 4 | autoresearch **MIT declared in README only**, no `LICENSE` file, API `license: null` (lines 55–61) | README ends `## License` → `MIT`; `api.github.com/repos/karpathy/autoresearch` `"license": null`; `/contents/` lists 10 files, **no LICENSE** | ✓ |
| 5 | climbmix dataset card `license: mit`, card body otherwise empty, 600 GB full corpus, ~91.0–92.3 MB/shard, default 11-shard ≈1.0 GB download (lines 65–75) | HF API `license:mit`; raw card = `license: mit` only; dataset page "License: mit", "Total file size: 600 GB"; tree shard sizes 91,090,081–92,302,344 B; `prepare.py` `MAX_SHARD=6542`, `VAL_SHARD=MAX_SHARD`, `--num-shards` default 10 | ✓ |
| 6 | CIFAR-10 `license: unknown`, download 143,646,105 B (lines 120–122) | `huggingface.co/api/datasets/uoft-cs/cifar10`: `license: unknown`, `download_size: 143646105` | ✓ |
| 7 | IMDb `license: other`, Licensing Information "More Information Needed", 83,446,840 B (lines 169–172) | HF API/card: `license: other`, `download_size: 83446840`; card `### Licensing Information` → `[More Information Needed]` | ✓ |
| 8 | AG News `license: unknown`, "provided by the academic comunity [sic] for research purposes", 19,820,267 B, 120,000/7,600 (line 215) | HF API/card matches exactly, including the `comunity` typo and split counts | ✓ |
| 9 | ETTh1 conflicting: GitHub `other`/NOASSERTION, HF mirror `cc-by-4.0`, OpenDataLab `CC BY-ND 4.0` (line 214) | `api.github.com/repos/zhouhaoyi/ETDataset` → `license: {key:"other", spdx_id:"NOASSERTION"}`; `thuml/Time-Series-Library` → `license: cc-by-4.0` with `ETTh1` config; OpenDataLab ETT listing (openxlab `OpenDataLab/ETT`) lists CC BY-ND 4.0 — **but the audit gives no URL for this third claim, see M2** | ✓ / M2 |
| 10 | ogbn-arxiv **ODC-BY**, ogbg-molhiv **MIT**, ogbg-molhiv 41,127 graphs, HF mirror 401 (lines 173–178, 216) | `ogb.stanford.edu/docs/nodeprop/` → "License: ODC-BY" for ogbn-arxiv; `/docs/graphprop/` → "License: MIT" for ogbg-molhiv, 41,127 graphs; `huggingface.co/api/datasets/OGB/ogbn-arxiv` → HTTP **401** | ✓ |
| 11 | UCI Covertype **CC BY 4.0**, DOI 10.24432/C50K5N, 10.7 MB, 581,012 × 54 (line 213) | `archive.ics.uci.edu/dataset/31/covertype` → CC BY 4.0, DOI, file size, instance/feature counts | ✓ |
| 12 | 1GC-7RC repo **404 both HTML and API**; arXiv 2605.17046 v2 (19 May 2026) claims public GitHub (lines 198–205) | `github.com/Strolchii/1GC-7RC-Benchmark` → 404 page; `api.github.com/repos/Strolchii/1GC-7RC-Benchmark` → `{"message":"Not Found","status":"404"}`; arXiv abs page: v2 19 May 2026, abstract "publicly available on GitHub at this https URL" | ✓ |
| 13 | MLGym image `aigym/mlgym-agent:latest` amd64 7,248,568,196 B, digest `sha256:86d438d6…`, pushed 2024-11-04, arm64 1.18 GB; MLAgentBench image `qhwang123/researchassistant:latest` amd64 21,779,902,631 B, digest `sha256:6b3690a1…`, pushed 2023-06-24 (lines 139–142, 180–183) | Docker Hub v2 tags API: exact sizes, exact digests, exact push dates; arm64 1,181,562,597 B | ✓ |
| 14 | repo HEADs: autoresearch `228791fb…`, MLGym `9d40c1b5…`, MLAgentBench `5d71205c…`, ETDataset `1d16c8f4…` (lines 53, 90, 153, 214) | commits API: all four shas and dates match (2026-03-26 / 2025-08-10 / 2024-04-28 / 2021-06-04) | ✓ |
| 15 | MLGym: 19 task YAMLs; four T1 candidates present; `data/regressionKaggleHousePrice/data` 404; `_helpers/train.csv` 460,676 B; RL requirements jax[cuda12]/gymnax/flax/optax; dataset configs point at `uoft-cs/cifar10` / `zalando-datasets/fashion_mnist` (lines 112–142) | repo contents API: 19 YAMLs (exact list), 404 on the `data` path, `train.csv` size exactly 460,676, requirements exactly as cited, both configs' `data_path` as cited | ✓ |
| 16 | MLAgentBench: 15 task folders (named list), cifar10 via torchvision CIFAR10, imdb via `load_dataset("imdb")`, ogbn-arxiv via `PygNodePropPredDataset` (lines 159–178) | repo contents API: 15 dirs, names match exactly; prepare.py/train.py sources show exactly those calls | ✓ |
| 17 | TinyShakespeare: no licence metadata, char-rnn citation, 1,115,394 B (line 212) | HF API: no license tag, citation to char-rnn, `download_size: 1115394`; char-rnn API `license: null` | ✓ |
| 18 | README facts quoted for the three suites (13 tasks, experimental warning, 5-min wall clock, H100, `sudo dnf install -y nvidia-container-toolkit`, root-in-container guidance, Python 3.10/`install.sh`) | all quotes verified against the three READMEs; no misquote found | ✓ |
| 19 | OpenDataLab ETT CC BY-ND 4.0 (line 214) | claim is substantiated outside the audit's own citations (search: openxlab `OpenDataLab/ETT`, CC BY-ND 4.0), **but the audit cites no URL** → M2 | M2 |
| 20 | "third-party listing (rlresearch.ai, 2026-11-08 snapshot) links the same dead URL" (lines 203–204) | no URL given; not independently re-checked → M3 | M3 |

Nothing I checked was wrong. The two claims without a citation in an audit whose reading rule 1 says "every
licence claim below carries the URL it was read from" are M2/M3. The audit's own reading rules
(declared vs verified, public reachability ≠ reachability from Ada/HoreKa, sizes are metadata) are applied
consistently. MLGym's CC-BY-NC finding (the "most consequential" one) is exactly right, including the
no-patent-grant and modification/notice consequences.

## 3. Decision relevance (VERIFY 3) — PASS; disposition is right

- **No licence-level STOP for ENGINEERING_ONLY census use.** Agreed for G.0/U2: G.0 runs the suites' own
  baseline scripts in a private internal harness for raw-cost measurement; that is use, not distribution,
  and MLGym's NC term permits non-commercial research use. The audit states this "as far as U1 can verify"
  and disclaims legal advice — appropriate, and it does not over-claim clearance ("not licensed" is
  reserved for unstated asset licences). The STOP condition is correctly *not* created where none exists;
  inventing a STOP from an NC licence that permits research use would have been the error.
- **MLGym CC-BY-NC 4.0 needs an author line before ported bundles are committed/shared.** Correct: U3
  port kits will copy task assets into the harness, which triggers §3(a) attribution/notice/modification
  duties, and NC has to be acceptable for the project and any downstream release. The audit's per-node
  `LICENCES.md` recommendation (§10) is the right mechanism for the attribution/modification/notice
  duties and for the per-file MIT/Apache sub-components (SWE-Agent, Modded-NanoGPT, Gymnax,
  Gymnax-blines) that upstream does not itemise.
- **Asset licences that state nothing (CIFAR-10, IMDb, AG News) and ETTh1's three conflicting claims.**
  Correctly treated as author decisions, not as STOPs and not as licensed. "Unknown/other" is not
  prohibition; the census can still run, but no label-table citation may assert a licence. AG News'
  "research purposes" wording is correctly classified as a research-use statement, not an open licence.
- **Kaggle House Price.** Correctly ambiguous: bundled Kaggle-derived `train.csv` under Kaggle
  competition terms, and MLGym's CC-BY-NC does not relicense it. Needs the author decision the audit asks
  for (§9 item 2 covers the unknown licences but the Kaggle-terms question should be listed explicitly as
  an author item too — it is row-visible in §7 but not in the §9 author list; fold into M4).
- **1GC-7RC 404.** Correct: no suite, no harness licence citable, 4 Nov `R1-1GC-FALLBACK` stands; datasets
  are extras only. The audit correctly does not resurrect 1GC as a suite.
- **Open author/coordinator questions.** Clearly listed in §9 (9 numbered items with owner labels:
  author × 3, cluster agent × 2, unmeasured sizes, licence hygiene, 1GC, no manifest) and mirrored in the
  §7 "Not verified / needs input" column. Good. One process gap: §10 makes the `LICENCES.md` a de-facto
  requirement but `prompts/TRACKG_PORT_CHECKLIST.md` has **no licence/provenance step** (checked: no
  "licen" string in that file). As written the recommendation has no owner for amending the checklist —
  **M7**.

## 4. Consistency with `R1-TRACKG-PORT-OWNER` (VERIFY 4) — PASS, one wording fix (M6)

The authority row (PLAN.md:1259) is: **Mac agent writes each T1 candidate's port kit per
`prompts/TRACKG_PORT_CHECKLIST.md` (node config, 3–5 representative diffs, fixed-step wrapper, synthetic
tests), one independently reviewed bundle per suite; the experiment agent deploys and smokes on Ada.**
The audit assigns: Mac agent = port kit (§7 Owner column; §10 is addressed to the Mac agent); U1 = record;
cluster agent = host/container/egress; author = licence decisions. It never claims Mac work was done and
never claims porting/tests/smokes. The autoresearch fixed-step wrapper is correctly assigned to the Mac
port-kit list (the row's "固定步数 wrapper"). **PASS.**

Two precision fixes: (i) §2 line 81 calls "the fixed-step wrapper **and its raw-cost measurement**"
Mac-agent port-kit work — the wrapper is port-kit work, but the raw-cost measurement is U2 (and per
`TRACK_G_RUNBOOK.md` G.0.2 `.2` it happens after G.1 at the wrapper), not Mac work; (ii) the audit uses
"cluster agent" where the 17 Nov row names the "experiment agent" as the Ada deployer — if these are the
same actor, say so once; if not, the §9 items 4–5 (container/runtime path, egress) need the correct owner
name. See **M6**.

## 5. Completeness / gaps (VERIFY 5) — PASS, with pinning and citation gaps (M2–M5, M9)

- Candidate/suite table (§7): all 13 rows have Code licence, Asset licence, Availability,
  Blockers/unknowns, Owner, Not verified/needs input filled. Unmeasured sizes are marked ("size
  unmeasured", "not measured here", "exact bytes not fetched", "≈"). GitHub HEAD shas and Docker image
  digests give usable pins; URLs are ordinary public URLs and I could re-fetch all of them.
- Known gaps, all disclosed rather than papered over: ogbn-arxiv size, container image contents, egress,
  root-runtime, unsupported 1GC harness, TinyImageNet/VOC out of scope with a G.3 audit pre-condition.
  The "not verified / needs author or cluster-agent input" list is clear and actionable.
- Pinning gap: licence claims were read from **mutable HF dataset cards**, and the audit pins only GitHub
  shas. Revising cards would silently change the evidence. Add the HF revision shas observed on
  2026-11-17 (I recovered them: cifar10 `0b27149…`, imdb `e628166…`, ag_news `eb185aa…`, fashion_mnist
  `531be5e…`, climbmix `915333b…`, Time-Series-Library `2b66e59…`, tiny_shakespeare `c7a7ff3…`,
  OGB/ogbg-molhiv `2725c3f…`) or state "record the card revision when the port kit pins it" — **M9**.
- Citation gaps: OpenDataLab ETTh1 URL and rlresearch.ai listing URL (**M2/M3**); the Kaggle House Price
  competition URL that §3 line 133 tells the reader to "record" is not actually recorded (**M4**); IMDb's
  "task text says fine-tune DistilBERT" has no citable source (the repo's imdb benchmark has only
  `env/train.py` — a TODO stub — and no prepare script; see **M5**).
- Optional improvements (not gating, worth one line each): CIFAR-10's HF card tags it as derived from the
  withdrawn 80M Tiny Images dataset (relevant provenance for a licence audit); the MLAgentBench 13-vs-15
  count difference may be explained by paper versions (the OpenReview version states 15 tasks) rather than
  being "not resolved"; and if 1GC datasets are ever added as G.3 extras they must be re-ported to fixed
  step budgets (R1-BX-D5) since the 1GC benchmark's own design is 40–120 min wall-clock.

## 6. MINOR findings and exact fixes (no BLOCKING, no MAJOR)

- **M1 (§5 line 206).** "the five public datasets named in the T1 row" is wrong: the T1 row names seven.
  Fix: "the five datasets the T1 row keeps as possible **T1** extra tasks (the row also names TinyImageNet
  and VOC, which `R1-BX-D2` assigns to **T2** and which this U1 list excludes; if G.3 wants them they need
  a licence audit first)".
- **M2 (§5 ETTh1 row line 214, §7 row line 250).** OpenDataLab's "CC BY-ND 4.0" is the third conflicting
  claim and the audit says "record all three URLs", but only two are cited. Fix: add the exact URL
  (e.g. `https://openxlab.org.cn/datasets/OpenDataLab/ETT`) + snapshot date, or drop the claim to two
  sources (the conflict finding survives either way).
- **M3 (§5 lines 203–204).** "A third-party listing (`rlresearch.ai`, 2026-11-08 snapshot) links the same
  dead URL" has no URL. Fix: add it, or delete the sentence (the arXiv-quote-vs-404 discrepancy stands on
  its own).
- **M4 (§3 lines 126–133, §7 row 243).** It says "record the exact URLs" for the Kaggle source but no
  Kaggle URL appears. Fix: add the competition URL
  (`kaggle.com/competitions/house-prices-advanced-regression-techniques`) and, if feasible, one identity
  check of `_helpers/train.csv` (row/column count vs the Kaggle train file); otherwise mark the
  competition identity as inferred. Also add "Kaggle competition terms" to the §9 author list.
- **M5 (§7 IMDb row line 246).** "task text says fine-tune DistilBERT — weight source not in the task's
  prepare script" is not verifiable from the cited repo: the imdb benchmark has no prepare script and
  `env/train.py` is a TODO stub. Fix: cite where the task text says this (paper/task description) or drop
  the parenthetical; keep the real open point — the pretrained-weight source and its licence are not in
  the repo, so the port kit must record it.
- **M6 (§2 line 81; §7–§9 owner labels).** (i) Re-attribute "raw-cost measurement" from Mac port-kit work
  to U2/experiment-agent; only the fixed-step wrapper is Mac work. (ii) Align "cluster agent" with
  `R1-TRACKG-PORT-OWNER`'s "experiment agent" (state equality or rename), so the §9 container/egress
  items have an unambiguous owner.
- **M7 (§9 item 9 line 292; §10 lines 294–303; §1 line 48).** §10 is called a "recommendation" but §1/§9
  say the port kit "must" carry `LICENCES.md`, and `TRACKG_PORT_CHECKLIST.md` currently has no
  licence/provenance step (checked). Fix: phrase it as a recommendation to the **author/coordinator to
  amend `TRACKG_PORT_CHECKLIST.md`** with a licence/provenance checkbox (plus the Mac agent applying it),
  and make the "must" conditional ("once adopted"). Otherwise the requirement is unenforceable and
  ownerless.
- **M8 (status line 7).** "Written in the worktree `ops-tasl-20261116` (HEAD `c921983e`)" is stale at the
  file's final mtime: `c921983e` was HEAD when writing began (00:50) but `45fcf0fa` landed at 01:16
  (a child commit; still does not contain the 17 Nov rows). Fix on commit: cite the commit that carries
  this file (or "HEAD `c921983e` at 01:15, `45fcf0fa` at completion"). Cosmetic, but this audit is
  otherwise rigorous about pins.
- **M9 (§1 reading rule 2; §10).** Pins GitHub shas but not the HF dataset-card revisions all licence
  claims were read from. Fix: add the observed HF revision shas (listed in §5 above) to §5/§7 or §10, or
  state that the port kit must record the card revision.

## 7. What U1 may record, and the decisions it must hand up

**U1 may be recorded as done as a docs-only census unit** once M1–M5/M9 are applied (all text/citation
edits; no new fetches needed except M2/M3 URLs). It moves no gate and authorizes nothing, as §8 states.
Decisions U1 correctly hands up:

1. **Author — MLGym CC-BY-NC 4.0 acceptance** for T1 + paper artefact/port release (with attribution,
   notice, "Modified" indication; no patent grant).
2. **Author — unstated asset licences**: CIFAR-10 (both suites), IMDb, AG News — accept with citation or
   substitute a cleanly licensed task.
3. **Author — ETTh1** which of the three conflicting licence claims governs (or do not cite it).
4. **Author — Kaggle House Price terms** for the bundled Kaggle-derived split.
5. **Author — 1GC-7RC repo 404**: leave the 4 Nov fallback in place (recommended; no action) or raise the
   404 if 1GC is ever wanted back.
6. **Coordinator — amend `TRACKG_PORT_CHECKLIST.md`** to carry the licence/provenance step (M7).
7. **Cluster/experiment agent — container path (Docker/Podman root runtime vs Apptainer `.sif`), egress
   allowlists (`huggingface.co` + LFS/Xet, `cs.toronto.edu`, OGB host, `registry-1.docker.io`, PyPI), and
   the 7.25/21.8 GB image pulls** on the census host; U1 cannot close these.

## 8. Attestation

No host access, no GPU, no clone/run of any suite, no commit/push. The only write was this review file
(uncommitted). All URL re-checks were live public web fetches on 2026-11-17. Spot-checks were limited to
the decision-relevant claims listed in §2; I did not re-verify claims that are irrelevant to the
licence/ownership decision. If anything in this review conflicts with a dated PLAN row, the PLAN row wins.
