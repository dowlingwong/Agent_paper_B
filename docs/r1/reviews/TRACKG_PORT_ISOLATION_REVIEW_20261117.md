Reviewed base: harness MLGym `061d638edc91254477d699b3be89e40625cc99ec`, MLAgentBench `0aae2f68376a5665ce1869e835906615b7e08ecc`, autoresearch `5d3dccccf1790203212d2e0aa96c969f7c703fdc`; report `660f27a2` (accepted in round 4)

# Independent review record — Track G port kits on the isolated runner, with the port decisions

**Unit.** Three `autoresearch_harness` branches, each over its accepted U3 tip (READY 56–58) and merging the isolation
core `68cdd1a` (READY 60):
- `mac-trackg-iso-mlgym-20261117` over `334c89c`;
- `mac-trackg-iso-mlab-20261117` over `8596a0e`;
- `mac-trackg-iso-ar-20261117` over `08d0650`.

Also the report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` on `mac-trackg-port-isolation-20261117` over `main`
`50176481`. Authority: PLAN rows R1-TRACKG-PORT-DECISIONS (1)–(3) and R1-HARNESS-ISOLATION (on `main` `50176481`);
queue of 17 Nov 2026, item (2).

**Process.** One independent reviewer, a separate agent that wrote none of this code and is not the core's reviewer,
ran all four rounds. It edited nothing in the worktrees; its copies, probes and scratch files are under
`/tmp/kitrev/`, and it created no cgroups or `/dev/shm` files. The round texts are reproduced below as delivered, as
block quotes, so that only this record's own closing lines are read as the acceptance.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | MLGym `bf6bb3e` (from `334c89c`), MLAB `7115df6` (from `8596a0e`), autoresearch `7c6253f` (from `08d0650`) | MLGym ACCEPTED with notes (M1, M2); MLAB ACCEPTED with notes; autoresearch NOT ACCEPTED (B1; M3–M5) |
| 2 | autoresearch `4b831e5`, MLGym `a4b4537`, plus the core merge of `68cdd1a` in all three | autoresearch ACCEPTED with notes (the census GPU smoke must pass first); MLGym ACCEPTED; MLAB ACCEPTED with notes |
| 3 | MLGym `061d638` (N-c), autoresearch `5d3dccc` (N-b); report `bc284ac5` | code verdicts unchanged; report: corrections R1–R7 |
| 4 | report `660f27a2` (from `bc284ac5`) | report ACCEPTED (three wording nits, applied in `b82f9e01`) |

**Coordinator's test runs** (Python 3.12, CPU):
- `test_port_mlgym.py`: 30 passed.
- `test_port_mlagentbench.py`: 22 passed.
- `test_port_autoresearch.py`: 29 passed.
- `tests/trackg` without the port files: the known t0 environment failure only (`test_manager_proposal_v1…`). Before
  the scope-line exemption, the MLGym branch also failed the t0 base-file test; that test now allows only added lines
  naming `third_party/mlgym/` in the root `README.md` and `LICENSE`.

---
## Round 1

> # Review: Track G port kits after the isolation merge (MLGym, MLAgentBench, autoresearch)
>
> Reviewer: independent (did not write this code). Date: 2026-11-17.
> Branches reviewed (worktrees untouched; all work done in copies under /tmp/kitrev/):
>
> | Kit | Branch @ HEAD | Base | Suite result here |
> |---|---|---|---|
> | MLGym | `mac-trackg-iso-mlgym-20261117` @ bf6bb3e | 334c89c | test_port_mlgym: **29 passed** (8 min 38 s) |
> | MLAgentBench | `mac-trackg-iso-mlab-20261117` @ 7115df6 | 8596a0e | test_port_mlagentbench: **22 passed** (2 min 30 s) |
> | autoresearch | `mac-trackg-iso-ar-20261117` @ 7c6253f | 08d0650 | test_port_autoresearch: **27 passed** (5 min 55 s) |
>
> No skips in any suite. `test_trackg_t0_identity.py` in MLGym: the scope-line test passes, and `test_manager_proposal_v1...` fails as the known environment failure. `src/` is unchanged from the accepted core eac6846 in all three branches. `ar_isolated.py`, `ar_parent.py`, `ar_data.py`, `ar_fixed_loop.py`, `port_support.py` and `isolated_fixture.py` are byte-identical across all kits, and `ar_isolated.py` matches the master copy.
>
> ## Verdict
>
> * **MLGym: ACCEPTED with notes.** Fix M1 before any census run that uses mlgym_houseprice. M2 is a documentation fix.
> * **MLAgentBench: ACCEPTED with notes.**
> * **autoresearch: NOT ACCEPTED.** B1 means the GPU path, which is the only one the census uses, very likely cannot work as configured. M3 to M5 should be fixed in the same round.
>
> Taken together, the unit is **NOT ACCEPTED** until B1 is fixed and the GPU smoke has run.
>
> ---
>
> ## Blocking
>
> ### B1 (autoresearch): CUDA IPC of the parent's buffer cannot work with `expandable_segments:True` under this sandbox
> `configs/trackg/nodes/autoresearch_fixedtokens.yaml:47` puts `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` in the isolation env, so the parent gets it too, as its docstring says at `run_fixed_budget.py:3-5`. The parent then allocates the shared logits buffer through the caching allocator (`run_fixed_budget.py:60`) and exports it with `iso.cuda_share` (`:61`). That buffer lives in an expandable segment.
>
> In torch 2.6 (the version in the test venv), IPC of an expandable-segment tensor works differently from cudaMalloc memory. The receiver fetches the segment's file descriptors from the sender with `pidfd_open(pid)` plus `pidfd_getfd`. The binary `libc10_cuda.so` contains the strings "pidfd_getfd syscall needed to use IPC for CUDA tensors when expandable_segments:True is set" and "Tensors allocated with expandable_segments:True cannot be shared between processes".
>
> Under R1-HARNESS-ISOLATION that path cannot succeed:
> * The worker is in a new PID namespace, so the parent's pid either does not exist there or names another process.
> * The parent is non-dumpable, so `pidfd_getfd` (which needs ptrace-attach rights) is refused even if the pid resolved.
>
> Failure scenario: on the GPU host every run, the baseline included, fails at `bind_cuda`. Either the worker gets an error reply and the parent exits 12, or `_share_cuda_` raises in the parent. The census would see 100 % failures, or count them against proposals.
>
> This could not be tested here because the host has no GPU. The evidence is the torch binary plus the kernel's pidfd rules.
>
> Fix: allocate the IPC buffer outside expandable segments. Options are `torch.cuda.memory._set_allocator_settings("expandable_segments:False")` around the allocation, which is torch's own suggested remedy, or keeping the variable out of the parent's environment and setting it only for the worker. Then run `tests/trackg/port_smoke_gpu.py` before accepting the kit. Legacy cudaIpc across the PID namespace is still the core's accepted, GPU-smoke-only risk.
>
> A secondary point applies only if the expandable path ever worked: torch exports the segment's pages around the block (20 MiB granularity in the large pool), not only the block. The worker could then reach neighbouring parent tensors such as the "private" clones and `first_logits`. A dedicated cudaMalloc-backed allocation avoids that as well.
>
> ---
>
> ## Minor
>
> ### M1 (MLGym houseprice): decision 2 can be silently bypassed by an existing data directory from the old setup
> `third_party/mlgym/nodes/mlgym_houseprice/prepare_data.py:56-75`: when `--out` already holds a manifest, setup only re-verifies and re-links it. It ignores `--from-file`, checks neither the table's shape nor the file's hash against the given file, and does not check the manifest's `source`.
>
> The setup at base 334c89c wrote exactly such a directory: same node, same `FILES`, same `--out` path, with MLGym's forwarded `train.csv` and `source = {repository: MLGym, path: …/_helpers/train.csv}`. The parent (`run_fixed_budget.py:40-44`) only prints `same_as_mlgym_copy=…` and refuses nothing.
>
> Reproduced in /tmp/kitrev/hpx: a manifest with an MLGym source and a 2-row CSV, then a re-run with `--from-file` pointing at an invalid file. Result: exit 0, data linked, and the run would use MLGym's copy.
>
> Fix: in prepare_data and in the parent, require `source.provided_by == "user download, passed with --from-file"` (or a `kaggle` key), and refuse otherwise. On a re-run with `--from-file`, check that the file's sha256 equals the recorded one. Optionally make the parent check the 1460×81 shape.
>
> Test gap: no test asserts that a run prints `AR_DATA houseprice_sha256=` or that the manifest records `md5`. Today the hash is "checked" only against the manifest written at setup, which is self-consistency only, as designed, and the census pins it.
>
> ### M2 (MLGym): licence and scope text not accurate in places
> * `third_party/mlgym/README.md:3` says "everything under this directory is licensed under … CC BY-NC 4.0, not under the repository's MIT licence". The nodes' own LICENCES.md says some MLGym material is from gymnax and gymnax-blines under Apache-2.0 (`policy.py`, `helpers.py`, `networks.py`). Apache-2.0 §4 terms, including shipping the licence text, still apply, and no Apache text is in the subtree. The directory also holds harness files written by the port; `ar_isolated.py` is byte-identical to the MIT master in `src/`.
>   * Suggested wording: "MLGym-derived material: CC BY-NC 4.0 (parts from gymnax/gymnax-blines also Apache-2.0); files written by the port are also offered under CC BY-NC 4.0 here." The root README/LICENSE line can stay as is.
> * The `LICENCES.md:19` "Scope within the harness repository" paragraph in all four MLGym nodes still says recording the scope "is the author's decision (port report, open point 1)". That decision is now made and implemented, so the text is stale.
> * `configs/trackg/nodes/mlgym_houseprice.yaml:91`: `external_benchmark.data` still reads "as shipped in MLGym (… _helpers/train.csv, sha256 pinned in prepare_data.py)", which contradicts decision 2.
> * `mlgym_houseprice/LICENCES.md:34` says the sha256 and md5 are "printed by every run". Only the sha256 is printed. The md5 is in the manifest, whose sha256 is printed.
>
> ### M3 (autoresearch): without the worker sandbox, the worker can choose the validation text the parent scores
> The parent reads the validation shard lazily, after the worker has trained and while it is answering: `val_loader` is created at `run_fixed_budget.py:135`, and parquet row groups are read on `next()`. The only data checks are at `:115`, before the worker starts, and at `:161`, after the evaluation.
>
> Under the documented `no_worker_sandbox` waiver (and in the tests' `run_parent` path), the worker can do the following, all passing every check:
> 1. Restore the write bits.
> 2. Replace `shard_06542.parquet` after its own post-training check, at `bind_cpu`.
> 3. Restore the original bytes on its first `logits` request, after the parent has read the shard.
>
> Demonstrated in a copy (`tests/trackg/test_kitrev_probes.py::test_val_shard_swap_without_sandbox`): same model, exit 0 both times, final data check passed. `val_bpb` was 2.310986 honest and 7.034641 swapped. The direction depends on the forged text; the point is that the scored text is under the attacker's control.
>
> With the sandbox the data is a locked read-only bind, so this is closed. That is reasoned from the core design; I did not run it through the runner. The MLGym and MLAB parents load all labels before starting the worker, so this is autoresearch only.
>
> Fix (cheap): read the validation shard into memory, or build all `EVAL_TOKENS` batches, which is about 160 MB of int64, before `P.start_worker()`.
>
> ### M4 (autoresearch): the editable code chooses which validation rows are scored
> `run_fixed_budget.py:130-136` takes `batch_size` from the worker's reply, which is train.py's `DEVICE_BATCH_SIZE` clipped to 1..512. It evaluates `EVAL_TOKENS // (B*T)` batches, so the number of rows scored is `floor(10240/B)*B`. The packing is row-sequential, so the rows form a prefix whose length the edit chooses. A non-divisor B drops up to B-1 tail rows, as much as about 5 %.
>
> Demonstrated: the same deterministic model gives `val_bpb` 2.310986 at B=16 and 2.310696 at B=60 (`test_batch_size_changes_metric`). The effect is small, but it is a free channel that is not training, and it can flip close keep/discard decisions. B also scales the parent's GPU memory (B×64 MiB per logits copy; four or more copies are live).
>
> Upstream autoresearch has the same property, but here the metric is declared frozen. Fix: use a fixed evaluation batch size in the parent (16, or any divisor of 10240), or refuse a B for which `steps*B*T != EVAL_TOKENS`.
>
> ### M5 (autoresearch): the parent's repeat check (exit 10) is not exercised by any test
> Mutation on a copy with the parent's check at `run_fixed_budget.py:156-158` disabled: all 11 `test_wrapper_metric_is_frozen` cases still pass. The worker's weight fingerprint produces the expected exit 10.
>
> The reverse mutation, with the worker fingerprint disabled, makes `updates_weights_in_forward` and `hides_tensors_from_the_fingerprint` exit 0 (`test_port_autoresearch.py:197,214`). Their 8×1e-3 weight drift stays below `CAUSAL_ATOL` = 0.05, so the parent check never fires for them.
>
> My probe with Python-side state (no weight change, +1.0 on the logits after 6 calls) does get exit 10 from the parent, so the check works. Add that probe, or one like it, to the suite. The test messages currently match "changed", which hides which check fired; assert the specific message.
>
> ---
>
> ## Notes
>
> * **N1 (all kits): test labels reach the worker.** They do so through the read-only data mount, which is the core's documented and accepted limitation, so the sealed-test requirement holds only at the protocol level. No parent sends test labels, test metrics or validation metrics to a worker; I checked every parent.
>   * Some frozen workers load labels into memory needlessly: `mlab_imdb/ar_worker.py:97-103` (`part("test")` puts `test_y` on the device), `mlab_ogbn_arxiv/ar_worker.py:98` (full `y`, captured by the batch closure), and the cifar/fmnist workers (`np.load` of `test_y`). This adds nothing an editable process cannot read itself, but it is easy to drop.
>   * Closing the requirement needs parent-only label files that are not mounted into the worker. That would be a core change.
> * **N2 (MLGym breakout): the worker can recognise the evaluation episodes.** `AR_SPLIT_SEED` reaches the worker (the `AR_` prefix is on the allow-list), validation keys derive from it (`run_fixed_budget.py:34-40`), test keys are the public constants 0-4, and `evaluate_policy.py` is readable. A stateful `act_logits`, which counts calls and batch positions, could replay the parent's rollout and its action RNG, then choose logits by planning rather than by policy. This falls in the documented "answers differently from a fixed model" class, but unlike autoresearch the MLGym/MLAB nodes have no probes. Cheap probes: ask for the logits of a permuted observation batch and check they permute the same way, or repeat one validation key and compare returns.
> * **N3 (MLAB imdb, decision 3):**
>   * The freeze is real. Mutating train.py on a copy fails both `test_imdb_baseline_is_frozen_and_disclosed` (hash recorded in LICENCES.md) and `test_manifest_complete[mlab_imdb]` (the manifest's baseline code state). A coordinated change of train.py, LICENCES.md and a re-declared manifest would pass, which is acceptable: LICENCES.md is frozen and pinned via `frozen_pin_sha256`. Recording the hash in the census plan as well would add an external anchor.
>   * The disclosure wording is recorded. I could not verify the census funnel and appendix, which are not in this repo.
>   * Independent review of the baseline: correct. The weight-decay groups match DistilBERT's names (biases, `embeddings.LayerNorm.weight`, `*_layer_norm.weight`), the linear decay reaches 0 at the last step, and bf16 autocast is used on CUDA only. Cosmetic: `[:, :256]` truncation drops `[SEP]` for long reviews, and `info["max_tokens"]` is unused. Neither blocks.
> * **N4 (paths and manifests, focus c):** consistent. Every file in every node dir is covered by the frozen or editable lists, and no listed path is missing (script check). The MLGym nodes and specs exist only under `third_party/mlgym`; `port_support._home` and the decision-1 test check this. The manifests are current (the suites pass). Static checks mutated on a copy (parent `import train`, parent `print("AR_METRIC …")`) are caught. Leftover: an empty untracked `configs/trackg/nodes/` directory in the MLGym worktree. Core file `configs/trackg/node_template.yaml` names the entries `run_isolated.py`/`worker.py`, while the kits use `run_fixed_budget.py`/`ar_worker.py`; that is cosmetic.
> * **N5 (parent loops, focus e):** no bugs found. Splits (seeded permutations, houseprice MLGym procedure, official ogbn split), seeds, budget flags, `check_array` shape and dtype checks, and the non-finite handling (accuracy counts non-finite rows as wrong, RMSE becomes nan, breakout refuses non-finite logits, a NaN in autoresearch logits always poisons the sum) are all correct. Budget accounting stays in the worker, as documented.
> * **N6 (t0 identity scope test):** `_scope_line_only` accepts any added line that mentions `third_party/mlgym/`. That is fine for its purpose but permissive.
> * **N7 (houseprice):** the run prints `synthetic (port tests only…)` when the manifest says so. That is informational only; the census should refuse it.
> * **N8 (could not test):** all CUDA paths (B1, CUDA IPC across the PID namespace, the GPU smoke, the compiled autoresearch path) and runs with a real cgroup parent, since the smokes used the `no_cgroup` and `root` waivers on this host.
>
> ## Scratch artefacts
> /tmp/kitrev/{mlgym,mlab,ar}_tests.log; copies and mutations in /tmp/kitrev/copies/ (iso-ar with `tests/trackg/test_kitrev_probes.py`, iso-ar-norepeat, iso-ar-nofp, iso-mlab-mut, iso-mlgym-mut); probe outputs in /tmp/kitrev/probes/; houseprice setup probe in /tmp/kitrev/hpx/. No cgroups or /dev/shm files created; worktrees clean at their HEADs.

---

## Round 2

> # Kit review, round 2: Track G port kits (MLGym, MLAgentBench, autoresearch)
>
> Reviewer: independent. Date: 2026-11-17. Worktrees were read only; work was done in /tmp/kitrev/.
>
> | Kit | HEAD | Kit diff reviewed | Suite here |
> |---|---|---|---|
> | autoresearch | ecd2c71 (merge of 68cdd1a over 4b831e5) | 7c6253f..4b831e5 | test_port_autoresearch: **29 passed** (5 min 53 s) |
> | MLGym | e85f50b (merge of 68cdd1a over a4b4537) | bf6bb3e..a4b4537 | test_port_mlgym: **30 passed** (10 min 48 s). t0 identity: 2 passed; known env failure `test_manager_proposal_v1…` |
> | MLAgentBench | 0aae2f6 (merge of 68cdd1a over 7115df6) | none: no change under nodes/, configs/ or tests/ | test_port_mlagentbench: **22 passed** (2 min 40 s) |
>
> Merge check: each merge commit changes only `src/autoresearch/trackg/isolation.py`, by 9 lines added and 5 removed. That matches the core change 4b831e5/a4b4537/7115df6 → 68cdd1a. All 11 copies of `ar_isolated.py` still equal the master copy. The worktrees are clean.
>
> ## Verdicts
>
> * **autoresearch: ACCEPTED with notes.** This is conditional on the census GPU smoke (`port_smoke_gpu.py`) passing before the node is used, as the coordinator proposes. The B1 fix cannot be exercised on this host.
> * **MLGym: ACCEPTED.**
> * **MLAgentBench: ACCEPTED with notes.** The notes are N1 and N3 from round 1, which are unchanged.
>
> ## Round-1 findings: status
>
> | Finding | Status | Evidence |
> |---|---|---|
> | B1: CUDA IPC with expandable segments | **Fixed in code; untested (no GPU).** | `run_fixed_budget.py:71` calls `_set_allocator_settings("expandable_segments:False")` right before the buffer allocation. That is torch 2.6's own suggested remedy, from the same `libc10_cuda.so` message. No large-pool allocation precedes the buffer: the validation `y` tensors are 256 KiB each and go to the small pool. So the 1 GiB buffer cannot be served from an existing expandable segment. The setting stays off, so the later clones are also ordinary segments. The GPU smoke is required to confirm that the setting takes effect at run time and that legacy cudaIpc works across the PID namespace (core risk). See N-a. |
> | M1: houseprice stale data dir | **Fixed.** | I re-ran my round-1 probe (/tmp/kitrev/hpx2): an MLGym-sourced manifest plus a bogus `--from-file` is now refused ("not set up from the user's Kaggle download") and nothing is linked. The parent refuses non-user-download sources with exit 2 and prints `sha256=… md5=…`. The new tests cover the MLGym-source case, a different file on re-run, and the parent refusal. |
> | M2: licence text | **Fixed.** | The root LICENSE/README, `third_party/mlgym/README.md`, the four LICENCES.md scope paragraphs, the houseprice yaml `data:` line and the md5 claim are now accurate and consistent. The new scope lines still name `third_party/mlgym/`, so the t0 scope check passes. See N-c. |
> | M3: validation shard swap without the sandbox | **Fixed.** | All 640 validation batches (64 in the smoke) are built before `start_worker()` (`:152` before `:156`). I re-ran my swap probe on a copy of 4b831e5: swapped and honest runs give the identical `val_bpb=2.310986`, both exit 0. In round 1 they gave 7.034641 and 2.310986. |
> | M4: train.py chooses the scored rows | **Fixed.** | `EVAL_BATCH_SIZE = 16`, a remainder is refused, and `AR_INFO eval_rows=… eval_batch_size=…` is printed. I re-ran my probe: `DEVICE_BATCH_SIZE` 16 and 60 now give the identical `val_bpb=2.310986`. In round 1 they gave 2.310986 and 2.310696. |
> | M5: parent repeat check untested | **Fixed.** | The new probe `changes_its_answers_after_the_probe` expects exit 10 with the parent's own message. I mutated a copy to remove the parent check: exactly that probe fails (1 failed, 11 passed). |
>
> ## Notes (none blocking)
>
> * **N-a (autoresearch, B1 follow-up).**
>   * Consider a cheap self-check after allocating the buffer, so that a torch version where the runtime setting is ignored fails loudly instead of with a pidfd error inside the worker. Look up the segment holding `self.buffer.data_ptr()` in `torch.cuda.memory_snapshot()`, require `is_expandable` to be false, and otherwise `P.fail` with a clear message.
>   * Also, if `_share_cuda_` or `bind_cuda` fails, the run is classified as a runtime failure of the proposal, not as infrastructure. The GPU smoke precondition covers this before any census use.
> * **N-b (autoresearch, cosmetic).** The rows-remainder refusal at `run_fixed_budget.py:143` exits with `EXIT_WORKER` (12), but it is a frozen-configuration error that happens before any worker exists. `EXIT_BAD_INVOCATION` would be clearer. It is unreachable with the frozen `prepare.py` (10,240 rows; 64 in the smoke).
> * **N-c (MLGym licence).** The texts are accurate now. Strictly, Apache-2.0 §4(a) asks for a copy of the Apache licence alongside redistributed Apache-licensed code (`policy.py`, `helpers.py`, `networks.py`). Consider adding the Apache-2.0 text, or a pointer, in `third_party/mlgym/`. This is a documentation nicety.
> * **N-d (MLGym houseprice).** The parent's source check is skipped when the manifest says `"synthetic": true` (`run_fixed_budget.py:45`), and the run then prints the `synthetic` marker. Only the port tests write such manifests. The census should refuse any run whose log carries that marker; this is round-1 N7, unchanged.
> * **N1 and N2 (open threat-model items).** I agree they can go into the port report as open items rather than code changes in this unit; I do not consider either blocking.
>   * N1, labels readable through the data mount, is the core's documented and accepted limitation. Dropping the needless in-memory `test_y` loads in the imdb, ogbn and cifar workers would be a tidy follow-up.
>   * N2, Breakout's evaluation keys being recognisable, is in the documented "answers differently from a fixed model" class. Please state in the report that the MLGym and MLAgentBench nodes have no causality or repeat probes, unlike autoresearch.
>
> ## Could not test
> Any CUDA path: the B1 fix, CUDA IPC across the PID namespace, and the compiled autoresearch run. Runs with a real cgroup parent. The smokes ran with the `no_cgroup` and `root` waivers.
>
> ## Scratch
> Logs: /tmp/kitrev/r2_{mlgym,ar}_tests.log and r2_t0.log. Copies: /tmp/kitrev/copies/iso-ar-r2 (with `tests/trackg/test_kitrev_probes.py`) and iso-ar-r2-norepeat. Probe outputs: /tmp/kitrev/probes/. Houseprice probe: /tmp/kitrev/hpx2/. I created no cgroups and no /dev/shm files.

---

## Round 3

> # Kit review, round 3: code confirmation and unit report check
>
> Reviewer: independent. Date: 2026-11-17. Worktrees were read only and are still clean (iso-mlgym, iso-ar, iso-mlab, kitrep). Scratch is in /tmp/kitrev/.
>
> ## (a) Code
>
> | Kit | Diff | Check | Tests run here |
> |---|---|---|---|
> | MLGym `061d638` | e85f50b..061d638 | `third_party/mlgym/LICENSE-APACHE-2.0` is byte-identical (`cmp`) to jax 0.4.35's dist-info LICENSE, which is also identical to chex's and optax's: the standard Apache-2.0 text with appendix. README and Breakout LICENCES.md name it. The file sits outside every node directory; the Breakout LICENCES.md change is the only frozen-file change. | `test_port_mlgym -k "not synthetic_smoke"`: 26 passed, 4 deselected. t0 identity: 2 passed plus the known env failure. |
> | autoresearch `5d3dccc` | ecd2c71..5d3dccc | One line: the row-count remainder now exits with `P.EXIT_BAD_INVOCATION` (2). The path cannot be reached with the frozen `prepare.py`. | Full `test_port_autoresearch`: **29 passed**. |
> | MLAgentBench `0aae2f6` | none | Unchanged since round 2 (22 passed then). | none |
>
> On N-a: not adding the self-check is acceptable, given that §4 of the report records it and the GPU smoke is a precondition.
>
> **Code verdicts: MLGym ACCEPTED. autoresearch ACCEPTED with notes (GPU smoke precondition). MLAgentBench ACCEPTED with notes.** These are unchanged from round 2.
>
> ## (b) Report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` @ bc284ac5
>
> Most of the report is accurate and matches the code and my rounds 1–2. I checked:
> - the branch tips;
> - the shared-file description;
> - every decision in §3, including that the t0 scope rule only allows added lines naming `third_party/mlgym/`;
> - the B1, M3 and M4 descriptions;
> - the claim that `shared_dev_shm` makes runs `effective: false` (runner.py:514-517);
> - the §5 counts. I reproduced 30/22/29, and the round-3 subsets above.
>
> I also checked the §5 statement that the smokes run with the sandbox and the `root`/`ptrace_scope`/`no_cgroup` waivers. The smoke records under /tmp/kitrev/t show `worker_sandbox` set, exactly those three waivers, and `effective: false`.
>
> Corrections, in order of importance:
>
> ### R1 (§2, overstated): "The parent sends no label it scores to the worker" is not true for autoresearch
> The autoresearch parent sends the validation input tokens `x`. Its scored targets are `y = x` shifted by one position (prepare's loader: `inputs = row[:, :-1]`, `targets = row[:, 1:]`). So every target except the last of each row is in the worker's input. This is inherent to LM evaluation, and it is the reason the causality probe exists.
>
> Suggested wording: "…for the other nodes. For autoresearch the scored targets are, by construction, the next input tokens; the causality probe and the repeat check are what stop a model from reading them (§6.4)."
>
> ### R2 (§6, missing): budget enforcement runs next to the editable code
> §6.6 says only that per-step compute is editable. Per the core docstring and `ar_fixed_loop.py`, the step and token counting itself runs in the worker, next to the editable code. Editable code can add updates by other means (a second optimizer, manual parameter updates, an EMA copy) and can read the data files directly, so the step/token budget is not enforced against an adversarial edit. Add this to §6.6, or as its own item. It relies on the declared-edit review and the S1 audit, as for §6.1.
>
> ### R3 (§6.1, incomplete for autoresearch)
> Readable validation data means more than "return logits built from the labels". An edited `train.py` can read `shard_06542.parquet` directly and train on it. The budgeted loader refuses the validation split (exit 8), but a direct parquet read bypasses the loader. Add this sentence.
>
> ### R4 (§7 step 3, missing): the smoke passes even when isolation is not effective
> `port_support.limits()` silently waives `root`, `ptrace_scope` (when the scope is < 1) and `no_cgroup` (when `AR_TEST_CGROUP_PARENT` is unset). `check_smoke` does not require `effective`. So on Ada a smoke can print `CHECKLIST_E_PASSED` while isolation was not effective.
>
> Add to step 3: check every run record's `isolation.waivers` is empty and `effective` is `true`. The exception is autoresearch, where `effective` is `false` by design and `exceptions == ["shared_dev_shm"]` must be the only entry.
>
> Also say:
> - run the smoke with each node's own Python environment. Breakout uses a separate JAX environment (spec `notes.python_env`);
> - `--cpus`, `--memory-limit` and `--runs-root` (outside the repository) are required;
> - House Prices runs without `--gpu-uuid`.
>
> ### R5 (§2 table, slightly overstated): ogbn masking
> "the worker masks validation and test labels to −1 before train.py sees them" overstates it. train.py gets a masked copy (`info["y_train_only"]`), but the full `y` stays in the worker, captured by the batch closure, and `y.npy` is readable. Suggest: "train.py is given a copy with validation and test labels masked to −1 (the full labels stay readable, §6.1)".
>
> ### R6 (§4, §5): what checks M3 and M4 behaviourally
> In the suite, M3 is covered only by a source-order test, and M4 by the source check plus the printed `eval_rows`/`eval_batch_size`. The behavioural evidence is the reviewer's scratch probes. On 4b831e5, a shard swap and `DEVICE_BATCH_SIZE` 60 each give the same `val_bpb` as the honest run; in round 1 they changed it.
>
> Say this in §5. Optionally add the probes to the suite; they are in `/tmp/kitrev/copies/iso-ar-r2/tests/trackg/test_kitrev_probes.py`. The swap must happen in the worker's `bind_cpu` (the probe patches `ar_isolated.SharedBuffer`); a thread swapping after the data check does not distinguish old from new.
>
> ### R7 (references)
> At bc284ac5, neither `docs/r1/reviews/TRACKG_PORT_ISOLATION_REVIEW_20261117.md` (header) nor `docs/r1/reports/HARNESS_ISOLATION_20261117.md` (§1 authority, §7 step 1 "core report §3") exists in the paper repo. Either add them in this unit, or name the branch or commit where they live.
>
> ### Smaller points
> - **§3(1):** "`LICENSE` is MLGym's own CC BY-NC 4.0 text at commit 9d40c1b5". I could not check this against upstream (no downloads). The file is the standard CC BY-NC 4.0 legal code. Mark it as "per U1", or as verified by whoever compared it.
> - **§3(2):** the shape check (1,460 × 81) runs only at first setup, not on re-run and not in the parent. The re-run and the parent check the manifest's source and hash. The report's wording is in the setup context and is fine, but "every run checks the table's shape" must not be inferred.
> - **§3(3):** add the round-1 caveat that a coordinated change of `train.py`, `LICENCES.md` and a re-declared manifest would pass the tests. It is caught only by the census's committed `frozen_pin_sha256`. Recording the baseline sha256 in the census plan as well would give an external anchor.
> - **§2:** "sealed memfd" means sealed against shrinking and growing, not against writes; the worker writes into it. Consider "a size-sealed memfd". The shared-files list could also name the node-specific frozen helpers: `ar_budget.py` (autoresearch) and `policy.py`/`helpers.py`/`evaluate_policy.py` (Breakout).
> - **§6 "Closed for every node (given `effective: true`)":** autoresearch is never `effective: true`. Add "autoresearch: the same, except the `/dev/shm` channel (§6.5)", so readers do not count it among the fully closed nodes.
> - **§6.2 / §6.3:** these are accurate and match my N2 and the probe gap. §6.2 could add that the image, imdb and ogbn workers are told explicitly which split they are answering (`meta["split"]`). That is harmless because §6.3 already covers it, but it makes the point concrete.
> - **§3(2) / N-d:** this is captured correctly. Consider also listing "refuse any run whose log has the `synthetic` marker" as a census step in §7.
>
> ## Verdicts
>
> - **Code: MLGym ACCEPTED. autoresearch ACCEPTED with notes** (GPU smoke `port_smoke_gpu.py` must pass, with the record checks of R4, before use). **MLAgentBench ACCEPTED with notes.**
> - **Report: ACCEPTED after corrections.** R1–R4 should be fixed before the report is used as the T1 reference. R5–R7 and the smaller points are editorial.
>
> Scratch: /tmp/kitrev/r3_{mlgym_fast,t0,ar}.log. I created no cgroups and no /dev/shm files.

---

## Round 4

> # Kit review, round 4: unit report confirmation (docs only)
>
> Reviewer: independent. Date: 2026-11-17. I reviewed `git diff bc284ac5..660f27a2` in /tmp/pb/wt/kitrep, read only; the worktree is clean. The code is unchanged since round 3, so the code verdicts stand: **MLGym ACCEPTED; autoresearch ACCEPTED with notes** (the census GPU smoke must pass, with the record checks in §7 step 3, before use); **MLAgentBench ACCEPTED with notes.**
>
> ## Round-3 corrections: status
>
> | Item | Status |
> |---|---|
> | R1 (autoresearch targets are next input tokens) | **Done** (§2): stated, with the reason for the causality probe and the repeat check. |
> | R2 (budget enforced next to editable code) | **Done** (§6.6). |
> | R3 (train.py can train on the validation parquet) | **Done** (§6.1). |
> | R4 (smoke does not check isolation; record checks; env, CLI) | **Done** (§7 step 3). The wording matches `port_support.limits()` and `check_smoke`, and the autoresearch exception `["shared_dev_shm"]` is stated. |
> | R5 (ogbn masking) | **Done** (§2 table). |
> | R6 (M3/M4 evidence) | **Done** (§4): attributed to the reviewer's scratch probes. Not adding them to the suite is acceptable. |
> | R7 (references) | **Done.** I verified that branch `mac-harness-isolation-report-20261117` (tip 6655214e) holds `docs/r1/reports/HARNESS_ISOLATION_20261117.md`, whose §3 is "Host conditions and waivers", as §7 step 1 cites. The review record is noted as added after the review. |
> | Smaller points (LICENSE not compared upstream; shape check at first setup only; coordinated-change caveat; memfd wording; node-specific helpers; autoresearch caveat on "closed"; refuse `synthetic` marker) | **All done.** |
>
> ## Remaining wording nits (non-blocking; fix if convenient)
>
> 1. **§6.1, line 156:** "No parent sends a scored label to the worker" is still unqualified. It now conflicts with §2's autoresearch statement. Suggest "No classification or regression parent sends a scored label to the worker (autoresearch: see §2)…".
> 2. **§6.5, line 174:** "the CPU path already uses a sealed memfd". For consistency with §2, write "a memfd sealed against resizing".
> 3. **§4, line 121:** "the smoke probes check the printed batch size". These are the parent probes (`test_wrapper_metric_is_frozen`, run via `ps.run_parent`), not the runner smoke. Suggest "the parent probes".
>
> ## Verdict
>
> **Report: ACCEPTED.** It now matches the code and my rounds 1–3. The three nits above are editorial and do not change any claim the census relies on. None of the open threat-model items (§6.1–6.7) is blocking for this unit, provided §6.1 and §6.5 go to the author for decision as written.

---

## Open points for the author

These are from the report's §6 and §7.
- **Labels the worker can read.** The data directories hold the validation and test labels, and autoresearch's
  validation parquet. Decide whether a training-split-only worker layout is required before T1, or whether the
  declared-edit review and the S1 audit are relied on.
- **`autoresearch_fixedtokens`.** Its runs are always `effective: false` because of `shared_dev_shm`. Accept the
  exception with disclosure, or require a memfd-only path.
- **The imdb disclosure sentence.** It must go into the census funnel and the appendix when they are written.
- **Further open items:**
  - Breakout's evaluation episodes are recognisable;
  - the MLGym and MLAgentBench nodes have no causality or repeat probes;
  - the budget is not enforced against an adversarial edit.
- **Experiment agent.** Run the GPU smoke per node with the run-record checks of §7 step 3. For autoresearch this smoke
  is a precondition for any use.

---

Code-Commit: 5d3dccccf1790203212d2e0aa96c969f7c703fdc
Verdict: ACCEPTED

Accepted commits: harness MLGym `061d638edc91254477d699b3be89e40625cc99ec`, MLAgentBench `0aae2f68376a5665ce1869e835906615b7e08ecc`, autoresearch `5d3dccccf1790203212d2e0aa96c969f7c703fdc` (code, rounds 2–3; autoresearch with the
GPU-smoke condition); report `660f27a2` (round 4), with its requested wording nits in `b82f9e01`.
