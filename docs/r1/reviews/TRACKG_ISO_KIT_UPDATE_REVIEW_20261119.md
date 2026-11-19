# R1-TRACKG-G0 isolated-kit update review — kit branches `448f682 / fb6e7d7 / f07875d` (19 November 2026)

**Reviewer:** independent reviewer (`iso-kit-reviewer`), delegated by the coordinator after the accepted
harness-isolation fix. Read-only: no code edit, no commit, no push, no GPU/U2/census run, no deletion, no
HTCondor/deepthought. SSH to Ada (`ucrtasl`) was used read-only; the only writes were this review file and
throwaway `/tmp` directories on Ada used for the pin/test reproduction (removed afterwards). No evidence file
was modified.

**Verdict: ACCEPTED.** The three kit branches are correct, clean and local-only: each carries exactly one
non-fast-forward merge of the accepted fix `5403392` and one copy/pin commit that changes only the node copies of
`ar_isolated.py`; all eight node copies and all eight recomputed `frozen_pin_sha256` values match the accepted
fix review's table and the submitted report. The five torch-node GPU smokes are genuinely isolated (`effective:
true`, `waivers {}`, `exceptions []`, cgroup killed/removed, real captured records) and pass; the autoresearch
smoke is honestly **BLOCKED** by condition 7 and is not claimed as a pass; HousePrice is a correct **STOP** and
Breakout/MinAtar correctly not run. The remaining findings are MINOR record/evidence-index inaccuracies only
(M-1…M-5), with no BLOCKING or MAJOR finding; no code or commit change is required. Record corrections
C-K1…C-K4 and one authority-wording condition C-K5 are listed below.

---

## Authority and scope

- **Delegation:** the Track G isolated-kit update is the accepted fix review's condition C2 ("Proceed with the
  verified plan — merge core `5403392` into `mac-trackg-iso-{ar,mlab,mlgym}-20261117`, copy the new master
  `37d99ab0…` over the 8 node copies, commit the recomputed `frozen_pin_sha256` values … and rerun each per-node
  smoke on Ada with the fixed core"; branch local/unpushed until that is done), in
  `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (sha256
  `c8e468c76af682e48d6a56607835e4a974e359f78be86333e6d9f37c9fc1ca36`; verdict **ACCEPTED**, condition 6 PASS,
  condition 7 BLOCKED/documented).
- **Published paper main** `de3de54fd22dcdd86215be0924307e36a64ed08b` (`git -C .claude-worktrees/ops-tasl-20261116
  rev-parse origin/main`). **Accepted isolation core** `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e`. **Accepted Ada
  fix** `5403392e94cb59d732f45d6702fc857531ad8fd5` (branch `mac-harness-isolation-fix-20261119`; worktree clean at
  `5403392`).
- **Unit reviewed:** report `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md`, sha256
  `3c3ae74a3788e86f0645e316b7c66392ac8bec45c01b8e0a5f4ed26a01f04bd7` (matches the task's `3c3ae74a…`), and its
  captures `TRACKG_ISO_KIT_UPDATE_20261119_captures/`: `SHA256SUMS` sha256
  `781602fa37fe06073ee444ac27479182a348454382759327554dfe4dcfdbd3d0`, 341 listed files + `SHA256SUMS` = 342 files;
  `sha256sum -c` rc 0 with 341/341 OK both on the Mac copy and on Ada's
  `/home/dowling/r1_engineering/iso_kit_update_20261119/captures/` (the report's "341 files, 3.4 MB" matches Ada
  `du -sh`; the Mac copy's actual file bytes are 2,290,364, the difference being `du` directory/block accounting).
  **Every capture file's sha256 is present in the live Ada evidence tree** (checked content-addressably over all
  9,411 live evidence files), so the captures are genuine snapshots, not reconstructions.
- **Ada kit worktrees** `/home/dowling/r1_trackg_20261117/harness_iso_{ar,mlab,mlgym}`: tips `448f6820f885d70ee6872b692284fe861afd3a33` /
  `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9` / `f07875de79a5a57739227b13e0fd52d31646edaf`; local branches
  `mac-trackg-iso-{ar,mlab,mlgym}-20261117`; expected untracked runtime `data` links only (see findings).
- Note: the corrected fix report copy in the ops worktree (sha256 `0ff9a7f2…`) already carries the accepted
  review's C1 corrections (per-file split `+47/−3`, stock-queue row marked "stdout not captured"); the kit
  update's pin table matches that corrected text and the acceptance-review table.

## Checks, commands and results

### 1. Branch and commit integrity (Ada, read-only)

| kit | pre tip (verified) | merge commit | merge parents | copy/pin commit = new tip | copy diff |
|---|---|---|---|---|---|
| ar | `5d3dccccf1790203212d2e0aa96c969f7c703fdc` | `2e65922d2add7edaf6228d2bad7dd8b8b0b0db16` | pre + `5403392` | `448f6820f885d70ee6872b692284fe861afd3a33` | 1 file `+47/−3` |
| mlab | `0aae2f68376a5665ce1869e835906615b7e08ecc` | `f7db8e24e1899a2c504d9fba8bd3553ff88562ad` | pre + `5403392` | `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9` | 3 files `+141/−9` |
| mlgym | `061d638edc91254477d699b3be89e40625cc99ec` | `0c1df3a73c838c5e2b4076d988b66776f5b2e50f` | pre + `5403392` | `f07875de79a5a57739227b13e0fd52d31646edaf` | 4 files `+188/−12` |

- `git cat-file -p` shows each merge is a true two-parent, non-fast-forward "Merge made by the 'ort' strategy"
  commit of the fix branch (`git reflog` entries at 18:02:55/56 -0800; `rev-list --count pre..tip` = 3, i.e. two
  new kit commits plus the fix commit reachable only through the merge).
- `git diff --numstat pre..merge` is exactly the accepted fix diff in all three kits: `ar_isolated.py` 47/3,
  `runner.py` 34/0, `tests/trackg/test_trackg_isolation.py` 73/0 (+154/−3); no other file changed by the merge.
  The kit tips' `runner.py` and `test_trackg_isolation.py` are the exact `5403392` blobs (git object ids
  `15a1778f…` / `906fae66…`) and `src/autoresearch/trackg/node_lib/ar_isolated.py` is the fixed master
  `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` (= `5403392`'s master; the pre-kit
  `src/`/isolation test were byte-identical to `68cdd1a`, so the merge is the clean application of the fix).
- `git show --name-status` of the copy commits: only the expected node copies —
  `nodes/autoresearch_fixedtokens/ar_isolated.py`; `nodes/mlab_{cifar10,imdb,ogbn_arxiv}/ar_isolated.py`;
  `third_party/mlgym/nodes/mlgym_{breakout_minatar,cifar10,fmnist,houseprice}/ar_isolated.py` — `M` only, no
  config/spec/YAML/licence edits and no deletion. The recomputed pin values are in the commit messages.
- **Master and all eight node copies**: content sha256 `37d99ab0…` for the kit master at tip (and at `5403392`)
  and for every one of the eight committed node copies in all three kits; likewise the working-tree master and
  node copies (only untracked `data` links in `git status`).
- **Independent pin recomputation** (not trusting the captures): for every kit I exported the *pre* and *tip*
  node trees from git (`git archive` to `/tmp`), loaded each kit's **own** node spec
  (`load_trackg_node_spec`) and used the kit's `isolation.frozen_file_hashes` exactly as `WorkingCopyRunner`
  takes it (`sha256(json.dumps(files, sort_keys=True))`). Result: **all eight old pins and all eight new pins
  match the report table and the acceptance-review table exactly**, `changed_frozen_files ==
  ["ar_isolated.py"]` for all eight, frozen-file counts 20 (ar) / 16 (mlab×3) / 18 (breakout) / 16 (other
  mlgym). New pins: `b5f0ec2f…`, `1f047ad7…`, `4b1019a6…`, `bd71fdf4…`, `cec562e6…`, `2d7e533b…`, `eb60107e…`,
  `88d359f2…` (full 64-hex values in the report §3).
- **No push / old branches untouched / no deletion**: `git ls-remote --heads origin` on the harness repo still
  shows `refs/heads/mac-trackg-iso-{ar,mlab,mlgym}-20261117` at the pre tips
  (`5d3dccc / 0aae2f6 / 061d638`); `origin/mac-harness-isolation-20261117` is still `68cdd1a`; the fix branch
  `mac-harness-isolation-fix-20261119` exists only locally at `5403392` (no origin ref). Local branch tips,
  origin-tracking refs, the accepted worktrees `harness_iso_core` (`68cdd1a`, clean) and
  `harness_iso_fix_20261119` (`5403392`, clean), the other port worktrees (tracked files clean), the tag
  `kdd-etaai-arxiv-v1`, and the stash list are unchanged; the kit branch reflogs show only creation
  (16:19), merge and copy commit; the worktree-HEAD "reset: moving to HEAD" entries are from 16:19:08
  (worktree creation), before this unit. No evidence of a reset/rewrite/deletion by this unit. Attempt-1
  outputs, old data trees and the old U3 `harness_mlgym/nodes/mlgym_houseprice` directory are still present.

### 2. Static tests (independently re-run, Ada)

Command shape per kit, from the kit root, CPU-masked, GPU-masked, delegated user cgroup, no repo writes:

```
systemd-run --user --scope -p Delegate=yes -- bash -c '
  CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
  cd <kit> && PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= \
  taskset -c 0-15 <envs/torch312/bin/python> -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"'
```

| kit | report (capture) | this review (re-run) |
|---|---|---|
| ar | 2 failed, 227 passed, 1 skipped, 3 deselected, 137.61 s | **2 failed, 227 passed, 1 skipped, 3 deselected, 137.79 s** |
| mlab | 2 failed, 218 passed, 1 skipped, 5 deselected, 45.32 s | **2 failed, 218 passed, 1 skipped, 5 deselected, 45.24 s** |
| mlgym | 2 failed, 225 passed, 1 skipped, 6 deselected, 47.17 s | **2 failed, 225 passed, 1 skipped, 6 deselected, 47.23 s** |

- The two failures are exactly the reported pre-existing/environmental ones in every kit:
  `tests/trackg/test_trackg_review_round2.py::test_child_that_leaves_the_group_but_not_the_session_is_killed`
  and `tests/trackg/test_trackg_t0_identity.py::test_manager_proposal_v1_campaign_is_byte_identical_to_the_base_commit`.
- **Child-kill**: reproduced the cause (`/usr/bin/python3` is 3.10.12 and 3.10's `subprocess.Popen` has no
  `process_group=` keyword — `inspect.signature` check false), and reproduced the fix: re-running just that test
  with `envs/torch312/bin` first on `PATH` under the delegated scope gives **1 passed in 1.65 s**
  (matches `pytest/post_childkill_pathfix.txt`, 1.61 s).
- **t0 identity**: reproduced the probe failure manually against base commit `a3fedbb` (exported with
  `git archive` to `/tmp`): the probe raises `ImportError: langchain-openai is required for OpenAI-compatible
  providers (vllm, lm_studio, llamacpp, openai, deepseek)` at
  `autoresearch/llm/langchain_client.py:168`, and `import langchain_openai` fails in `envs/torch312`. Both
  failures pre-date the update (identical in `pre_kit_*.log` and `post_full_*.log`, and in the source files
  unchanged by the merge), so they are not kit/isolation regressions; no test was skipped or weakened — the
  deselect counts are unchanged and the only skip is the pre-existing root-only uid-65534 test.
- **Core isolation file**: re-run alone under the delegated scope in `harness_iso_ar` gives **27 passed,
  1 skipped in 22.97 s**; `-rs` shows the skip is `test_trackg_isolation.py:506` "needs root to drop to uid
  65534 and delegate a cgroup". The full runs' +27 passed/+1 skipped delta vs the pre-update counts is exactly
  this file. No regression.
- No writes into the kits: `PYTHONDONTWRITEBYTECODE=1` / `-p no:cacheprovider`; after the re-runs
  `git status --porcelain` in the three worktrees shows only the same untracked `data` links, and no new
  `__pycache__`/`.pytest_cache` under the kit worktrees.

### 3. Per-node GPU smokes, blocked record and STOPs (captures + live Ada)

Captures were compared to the live evidence root: all 341 capture hashes are present in the live tree, every
report-cited baseline `run_record.json` sha256 and deployed `frozen_pin_sha256` matches the live file, and the
live `smoke/attempt2/<node>.log` files are byte-identical to the captures. The eight `ar_isolated.py` copies
inside the run work trees (`runs_smoke/s000_baseline/work` and `runs_edits/B2/work` of all six attempted
nodes) are all the fixed master `37d99ab0…`, so the records were produced by the updated kit, not the old unit.

**Five PASS nodes** — for every node: `CHECKLIST_E_PASSED` + `SMOKE_EXIT=0` in the log; 9 run directories and 9
complete `run_record.json`; `s000_baseline` ok, `s001` not executed / `scope_violation`, `s002` divergent
`non_finite_loss`, `s003` + `E1…E4` ok, `B2` ok; **every executed record** `isolation.effective: true`,
`waivers {}`, `exceptions []`, `frozen_files_changed []`, `log_intact true`, `cgroup.kill.empty_after true`,
`cgroup.removed true`, `parent_traced_by null`; cgroup parent, `limits.cpu_list`, `limits.gpu_uuids`,
`memory_method: external` with `MemoryMax=8G -p MemorySwapMax=0` text, `not_forced == ["dataloader_workers"]`,
`sealed` test value, no stray CR, exactly one `AR_METRIC` + one `AR_TEST` line in the result channel (63 bytes)
and no metric line in the log, and no synthetic marker in either the record gate or the run data manifest.

| node | kit tip | baseline / B2 | baseline `run_record.json` sha256 | deployed pin | GPU UUID / cpus |
|---|---|---|---|---|---|
| mlab_cifar10 | `fb6e7d7` | 0.5152 / 0.5152 | `e74912cc…` | `a459b3d8…` | `GPU-f439cca8-…` / 0-7 |
| mlab_imdb | `fb6e7d7` | 0.9048 / 0.9048 | `71e85958…` | `c169a6b8…` | `GPU-f439cca8-…` / 0-7 |
| mlab_ogbn_arxiv | `fb6e7d7` | 0.275982 / 0.275982 | `9d4f980c…` | `5ff5824a…` | `GPU-f439cca8-…` / 0-7 |
| mlgym_cifar10 | `f07875d` | 0.491 / 0.491 | `5f6ada86…` | `817c9034…` | `GPU-3b36edea-…` / 8-15 |
| mlgym_fmnist | `f07875d` | 0.861667 / 0.861667 | `aea01795…` | `ef804338…` | `GPU-3b36edea-…` / 8-15 |

The report's deployed-pin note is correct: recomputing each run work tree's pin with the `data` symlink present
(`data: link:/home/dowling/r1_trackg_20261117/data/<node>`) reproduces each record's `frozen_pin_sha256`
exactly (17 frozen entries for the torch nodes, 21 for autoresearch), while the §3 table is the committed-file
pin (no data link).

**autoresearch_fixedtokens — condition 7 BLOCKED (verified, not a pass):** 9 records; `s001` refused
`scope_violation` (not executed); all 8 executed records are `divergent` (`s002` `non_finite_loss`) with
`returncode 12`, `isolation.effective: false`, `waivers {}`, `exceptions ["shared_dev_shm"]`,
`shared_dev_shm: true`, cgroup kill empty/removed, no metric reported. The baseline really trained
32,768,000 tokens (500 steps of 65,536; log's `AR_TOKENS consumed=32768000`), `peak_vram_mb=1980.1`, elapsed
77.624 s, then failed with `AR_ERROR worker bind_cuda … cuda_open … torch.UntypedStorage._new_shared_cuda …`
`RuntimeError: CUDA error: invalid resource handle` — exactly the accepted condition-7 limitation. Baseline
record sha256 `2090936167f58df7a77fac98aa2966c4d4e8c7e78c1eac898a84ab3a29fd8c61` and deployed pin
`91e50af690fcc6e21894f8f3b392c01ab5d41d2793cb2f44565f062e754c96a5` match §8. The smoke exits 1 at its own
`check_baseline_log` assertion (no metric in the baseline result channel) — the correct refusal; no pass is
claimed anywhere. GPU 2 is idle again in the closing snapshot.

**STOPs / not run:** HousePrice — `/home/dowling/r1_inputs` does not exist, `data/mlgym_houseprice` absent, the
old U3 node directory has no data link and was untouched, the pin was updated (`88d359f2…`) and no smoke was
run; the spec still requires the user's Kaggle `train.csv` via `AR_HOUSEPRICE_TRAIN_CSV` (R1-TRACKG-PORT-DECISIONS
(2)). Breakout/MinAtar — no `data/mlgym_breakout_minatar`, and `envs/jax312/bin/python -c "import jax"` fails
with the reported `TypeError: argument should be a str or an os.PathLike object … not 'NoneType'`; the pin was
updated (`cec562e6…`) and no smoke was run.

**GPU gate / host / leftovers:** Paper A gate JSONs before the smokes say `verdict: clear_finished`,
`paper_a_live_waiting_for_card: false`, `paper_a_processes: []`; the pre-run snapshot shows GPU 2
`GPU-f439cca8-…` and GPU 6 `GPU-3b36edea-…` at 5 MiB used / 48,427 MiB free / 0 % with no compute app, and the
other six cards loaded; records only ever name those two UUIDs; the closing snapshot shows both idle; no smoke
process and only `init.scope` remain (no leftover scope/process). Host facts re-checked live: 96 CPUs, 8× RTX
6000 Ada, driver 545.23.08, Linux 5.15.0-151, uid 1030 in the records.

### 4. Report accuracy and captures

Every tip/hash/record/path/number in `TRACKG_ISO_KIT_UPDATE_20261119.md` was cross-checked against the live Ada
worktrees/evidence and the captures: commit shas/base/branch/parents/diffstats; master sha and all eight node
copies; all eight pins; the `pytest` counts/times and failure names; the six data-link/manifest entries and
`data_manifest.json` sha256 values (all six match; no `synthetic` key anywhere); the GPU gate/cards/UUIDs and
the two-chain CPU/cgroup/8 GiB settings; the five PASS runs' 9-record structure, baseline/B2 values, record
shas, deployed pins, result channels, sealed values and no-metric-in-log/no-CR checks; the autoresearch 9
records and its 32.77M-token training/CUDA-IPC failure; the HousePrice STOP and Breakout reason; the "not
pushed / old branches untouched / no deletion / six local commits / attempt-1 preserved" statements. The
captures' `SHA256SUMS` verifies 341/341 and every capture hash exists in the live evidence tree. The report's
blockers/STOPs are clearly recorded and there is no overclaim: condition 7 is **BLOCKED/NOT PASS**, the
autoresearch smoke is not called a pass, and the torch-node "PASS" claims are all supported by the records.

Five MINOR inaccuracies remain (M-1…M-5); none affects the kit commits, the smokes or the BLOCKED/STOP
conclusions. All other report-cited evidence paths exist.

### 5. Authority, conditions and port decisions

- **C2 followed**: merge of the exact accepted fix, byte-identical node copies, recomputed committed-file pins,
  per-node smokes re-run on Ada; the branches are local and unpushed. No kit YAML pin file needed editing — the
  node-spec comments name the isolation branch (`mac-harness-isolation-20261117`), not a sha.
- **C3**: no U2/census/experimental run, no T1 label and no evidence was produced. Condition 7 is kept
  **BLOCKED/NOT PASS**, and the report forbids an autoresearch U2 GPU run until the logits-transfer design
  decision and the `cuda_open` `torch.cuda.init()` fix are in one reviewed change. The autoresearch per-node
  smoke is the C2-mandated BLOCKED-state check; it failed closed, was run last on an idle card under the 8 GiB
  scope, and yielded no evidence. §8/§10.3 paraphrase C3 as "for U2", which is not in C3's literal text — see
  M-4/C-K4.
- **Port decisions preserved**: the merge changes only the three fix files and the copy commits only the eight
  `ar_isolated.py` copies, so the port decisions (HousePrice from the user's Kaggle file, MLGym licence/CC-BY-NC
  and Apache texts, node specs, data manifests) are untouched. No TASL-7/TASL-2/HTCondor/deepthought/root use is
  visible in the evidence; GPU use was confined to the two idle cards with before/after snapshots.

## Findings

### BLOCKING

None.

### MAJOR

None.

### MINOR

- **M-1 — wrong count of untracked data links (§11, `TRACKG_ISO_KIT_UPDATE_20261119.md:323`).** The report says
  "the three kit worktrees show only the **five** untracked runtime `data` symlinks". The live worktrees have
  **six**: `harness_iso_ar` 1 (`nodes/autoresearch_fixedtokens/data`), `harness_iso_mlab` 3
  (`nodes/mlab_{cifar10,imdb,ogbn_arxiv}/data`), `harness_iso_mlgym` 2
  (`third_party/mlgym/nodes/mlgym_{cifar10,fmnist}/data`) — all created by `setup_command` and listed in §5
  (which includes autoresearch). Correct to six; untracked links do not affect the commits.
- **M-2 — "02:08Z pre-run snapshot" is not in `gpu/` (§6, `:167`).** In the live evidence `gpu/` contains
  `before_20261119T015257Z.txt`, `before_latest.txt` (both written 01:52:57Z = 17:52:57 -0800) and
  `final_20261119T023618Z.txt`; there is no 02:08Z GPU snapshot. The 02:08:23Z artifact is
  `paper_a/gate_smoke_20261119T020823Z.json` (the Paper A gate, correctly cited in the same sentence). Reword:
  the pre-run GPU snapshot is the 01:52:57Z `gpu/before_*.txt`; the 02:12:07Z chain-start snapshots are inside
  the attempt-2 chain logs.
- **M-3 — evidence-index paths in §12 are not the live paths (`:341-347`).** (a) The attempt-2 chain logs are
  named `attempt2/chain_{A,B}_attempt2.log` but do not exist there: live evidence has
  `smoke/chain_{A,B}_attempt2.log` (the captures stage them under `smoke/attempt1/` because
  `stage_captures.sh` copies `$E/smoke/*.log` there first). (b) `attempt2/<node>/gpu_{before,after}.txt` and
  `attempt2/<node>/<run_id>/` are the *capture* layout; the live evidence layout is
  `smoke/attempt2/runs/<node>/{runs_smoke,runs_edits}/<run_id>/`. (c) `attempt2/summary_<node>.json` exists only
  for `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_fmnist`; the two cifar10 nodes have `attempt2/records_<node>.json`
  instead (plus the aggregates `summary_so_far.json`/`summary_all_torch.json`). Every node does have a gate
  output with `issues []`, so no substantive claim is unsupported — the index wording should distinguish
  capture paths from the Ada evidence root and say "summary_<node>.json or records_<node>.json".
- **M-4 — C3 is paraphrased with a "for U2" qualifier not present in C3 (§8 `:274-276`, §10.3).** The accepted
  review's C3 says "No autoresearch GPU run … may be started until …" without the "for U2" limitation. The unit
  did start the autoresearch per-node GPU smoke (the C2-mandated BLOCKED-state check, run after all five torch
  smokes on an idle card); it failed closed and produced no evidence, and the report correctly keeps condition 7
  BLOCKED and forbids the U2 autoresearch run. To remove ambiguity, add an explicit sentence that the per-node
  smoke is the C2-mandated check of the known block (not a U2/experimental GPU run) and that C3 remains in force
  for every autoresearch U2 run; the next authority review should confirm this reading of C3.
- **M-5 — two rounding/wording imprecisions in §6 (`:175-177`).** The observed torch-node peak in the captured
  snapshots is 2,853 MiB (`2.79 GiB` / `2.85 GB`), reported as "**~2.85 GiB**"; and "each card returned to
  5 MiB / 0 % between nodes" is literally only true for each node's own card — because the two chains ran
  concurrently, the other card's snapshot can show the sibling chain's job (e.g.
  `smoke/attempt2/mlab_cifar10/gpu_after.txt` shows GPU 6 at 867 MiB/14 %;
  `smoke/attempt2/mlgym_cifar10/gpu_after.txt` shows GPU 2 at 2,853 MiB/60 %; the autoresearch `gpu_after.txt`
  shows GPU 2 at 5 MiB/9 %). The closing snapshot does show both cards idle (5 MiB/0 %). Reword to "~2.85 GB
  (2,853 MiB)" and "each node's own card returned to 5 MiB/0 % (the other card carried the concurrent chain)".

## Conditions

- **C-K1 (record, before the report is committed/cited by the census).** Apply M-1 and M-2 (six data links; the
  correct pre-run GPU snapshot reference), then re-hash the report. No code or kit-commit change.
- **C-K2 (record/evidence index).** Apply M-3: correct the §12 attempt-2 chain-log paths, distinguish capture
  paths from the Ada evidence root, and describe the per-node gate output as `summary_<node>.json` or
  `records_<node>.json`.
- **C-K3 (authority wording).** Apply M-4: state explicitly that the autoresearch per-node smoke is the
  C2-mandated BLOCKED-state check, not a U2/experimental GPU run, and that C3's prohibition remains in force for
  every autoresearch U2 GPU run. No new run is needed.
- **C-K4 (optional nit).** Apply M-5's wording/rounding corrections.
- **C-K5 (process, not a correctness condition).** The three kit branches remain local and are correct as
  reviewed; the root may push them (`448f682 / fb6e7d7 / f07875d`) after/with the C-K1…C-K4 record fixes. The
  census must commit the pins with the stated convention (committed-file pin, §3 table) and never compare them
  to the deployed per-record pins by accident (§3, §10.2).
- **C3 remains a hard pre-condition (unchanged):** no autoresearch U2 GPU run until the logits-transfer design
  decision (socket/CPU buffer, or a documented non-PID-namespace GPU mode with a waiver) and the `cuda_open`
  `torch.cuda.init()` fix are recorded in one reviewed change.

## Residual risks confirmed

Condition 7 is a platform limitation (CUDA IPC does not cross a user namespace on Ada/driver 545.23.08) and is
correctly kept BLOCKED; the autoresearch GPU port and the `cuda_open` init bug remain open. The kit pins change,
so the census must commit them. HousePrice still needs the user's Kaggle file (or a recorded decision) and
Breakout needs its JAX environment and MinAtar data. The two static-test environment repairs (put
`envs/torch312/bin` first on `PATH`; install `langchain-openai`) are not kit regressions. The data links are
runtime-only and must be redone on the deploy host. No additional overclaim or deletion was found.

## Verdict

**ACCEPTED** for the Track G isolated-kit update: the three local kit branches `448f6820…`, `fb6e7d73…`,
`f07875de…` correctly merge the accepted fix `5403392`, update exactly the eight node copies of
`ar_isolated.py` to the fixed master `37d99ab0…`, carry the recomputed committed-file pins
(`b5f0ec2f…/1f047ad7…/4b1019a6…/bd71fdf4…/cec562e6…/2d7e533b…/eb60107e…/88d359f2…`), are unpushed, and the
five per-node torch GPU smokes genuinely pass with `effective: true`, `waivers {}`, `exceptions []` and a real
captured record; autoresearch is honestly BLOCKED by condition 7, HousePrice is a correct STOP, and
Breakout/MinAtar is correctly not run. MINOR findings M-1…M-5 are record/evidence-index corrections (conditions
C-K1…C-K5); there are no BLOCKING or MAJOR findings.

---

### Reviewer's command record (all on 19 Nov 2026, Europe/Berlin; read-only)

- Mac: `sha256sum` / `sha256sum -c SHA256SUMS` (341/341) on report and captures; report sha `3c3ae74a…`;
  `git -C .claude-worktrees/ops-tasl-20261116 rev-parse origin/main` = `de3de54f`; content-addressed comparison
  of all 341 capture hashes against the live Ada evidence manifest; reads of the accepted fix review, the unit
  report and every capture; parse of the records/gates/logs with Python.
- Ada (`ssh -o BatchMode=yes experiment_zhixu …`): `git -C harness_iso_{ar,mlab,mlgym} rev-parse/status/log/
  reflog/show/cat-file/for-each-ref/diff --numstat/show --name-status`; `git ls-remote --heads origin`; `git
  rev-list --count`; branch/worktree/ref cleanliness checks; all 8 kit node specs' pin recomputation from
  `git archive` trees with the kits' own `isolation.frozen_file_hashes` (pre and tip); live file hashes of the
  evidence root (9,411 files); live/deployed pin recomputation over the attempt-2 run work trees; `sha256sum`
  of the six data manifests; `nproc`, `nvidia-smi`, `uname`, `/usr/bin/python3 --version`,
  `subprocess.Popen` signature, `import langchain_openai`, the t0 probe against base `a3fedbb` (manual,
  `/tmp`), the live JAX import; a delegated-scope re-run of `tests/trackg -k "not smoke"` in all three kits,
  the isolation file alone (`27 passed, 1 skipped`), and the child-kill test with the environment `PATH` fixed
  (`1 passed`); `git status`/`__pycache__`/`.pytest_cache`/process/scope leftover checks. Temporary `/tmp`
  directories used for these reproductions were removed; no repository or evidence file was written.
