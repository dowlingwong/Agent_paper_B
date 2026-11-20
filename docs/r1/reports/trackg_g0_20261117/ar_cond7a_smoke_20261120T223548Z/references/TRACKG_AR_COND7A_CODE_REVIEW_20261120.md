# Independent review — R1-TRACKG-AR-COND7 option A code unit (kit branch, 20 November 2026)

**Reviewer.** Fresh independent reviewer (`cond7-reviewer`), delegated by the coordinator; no involvement in
writing the unit, the kit, the isolation core or the earlier isolation review. Read-only: the only file written is
this review record (uncommitted). No code edit, no commit/push/delete, no GPU/Ada/TASL/U2/census/HTCondor action.
Temp material used to verify scope/hashes: `git archive 448f6820` into `/tmp/cond7_review_before` and a node copy
with a fake `data` link in `/tmp/cond7_deployed` (both outside every repository, deleted/ignored material only).

**Object under review.** Branch `mac-trackg-iso-ar-cond7a-20261120` in worktree
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/harness_ar_cond7_20261120`, base
`448f6820f885d70ee6872b692284fe861afd3a33`, HEAD **`13786d1fe740e9bb77d10f88685feb88f28a5980`** (3 commits, no
merges): `0e0b82093c6b12703f16b82239e981aee33ad56b` (code), `6f235c432b99e6e4f103c071a34b1441f55798fb`,
`13786d1f` (captures). Report `docs/r1/reports/trackg_g0_20261117/TRACKG_AR_COND7A_CODE_UNIT_20261120.md`,
sha256 **`4f1f4fe0b432d7967fc282611fb6648c8395dd0f8679320520e5570025249bfb`**, 238 lines; captures
`..._captures/SHA256SUMS` sha256 `e47141b2e3342f689ccdc435630e93d94237411e444475675711c60ad86aeef0`, 15 files.
Status in the report: local only, not pushed, not run on a GPU — independently confirmed (§2.3).

**Verdict summary: ACCEPTED (code change) — 0 BLOCKING, 1 MAJOR, 6 MINOR.** The 7-file code/test/spec/manifest
change is in the intended scope and is correct: the autoresearch result path now uses the parent-owned CPU
`memfd` buffer (`iso.SharedBuffer` + `bind_cpu` + `SCM_RIGHTS`) on every host; no `cuda_share` / `bind_cuda` /
`cuda_open` call site remains in `run_fixed_budget.py` or `ar_worker.py`; the metric is still computed only by the
frozen parent from the worker's float32 logits with unchanged shape/dtype/copy semantics, causality probe, repeat
check, budget/weight fingerprint and metric value semantics; `cuda_open` has the C3 `torch.cuda.init()` fix; the
node spec is `shared_dev_shm: false` so an isolated run records `exceptions: []` (expected `effective: true` on
Ada); the new `frozen_pin_sha256` `147f0d35…` and spec `raw_sha256` `5c1bdf3d…` recompute independently, and the
old `b5f0ec2f…` / `5f48b86f…` reproduce from the base kit; the manifest changed only `node_spec_sha256`; the
before/after CPU test selections reproduce exactly (9 failed / 186 passed / 19 skipped / 19 deselected; 8/1/19;
11/18) with an identical failure set. **The MAJOR (M1) is the report's slowdown disclosure: §8:174–177 says there
are "8 logits requests per run (4 validation batches + 3 causality-probe batches + 1 repeat)" and "≈1.2–2 s per
run". The real/U2 configuration has 10,240 validation sequences in batches of 16, i.e. 640 evaluation requests
(+3 probe +1 repeat = 644) of the same 1 GiB buffer, ≈640 GiB one-way per run — about 80× the disclosed volume;
at the report's own 0.15–0.25 s/request that is ≈97–161 s per run, not 1.2–2 s, i.e. likely 2.4–3.4× the only
measured GPU run of this node (B1 67.901 s, 17 Nov).** This is report-only (no code change needed) but it is the
PLAN row's explicit "slowdown … measured and disclosed" item and must be corrected before the report is used to
plan the Ada smoke/U2 (C1). Conditions C1–C6; the code may proceed to the one isolated Ada smoke only after C1 and
under C2.

## 1. Authority and inputs (read-only, verified in this session)

- PLAN row **R1-TRACKG-AR-COND7** (option A): "CUDA IPC is removed from the result path (the worker hands logits
  or answers to the frozen parent through the existing socket/CPU buffer; only the parent computes the metric) and
  `torch.cuda.init()` is added to `ar_isolated.cuda_open`; isolation stays `effective:true` with no waivers. Kit
  pins and `frozen_pin_sha256` are updated, one isolated smoke runs, then the U2 unit; the slowdown of the logits
  transfer is measured and disclosed." Present at `origin/main:docs/r1/PLAN.md:1317` (`df58bcd5…`, the worktree's
  current published main); it was added by `bf1bcad6` ("author decisions 19 Nov (noon) … R1-TRACKG-AR-COND7 …").
  Note: the row does **not** exist at `de3de54f` (that commit's PLAN has 1,317 lines but no COND7 row; it is a
  docs ancestor of `bf1bcad6`), so report:14–16's "published paper main `de3de54f` (row at line 1317)" cites the
  wrong commit for the row (m2) — the authority itself is valid.
- Harness-isolation fix review `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md`, sha256
  `c8e468c76af682e48d6a56607835e4a974e359f78be86333e6d9f37c9fc1ca36` (ACCEPTED; `5403392e…`), condition **C3**:
  "No autoresearch GPU run … may be started until the logits transfer design decision is recorded (socket/CPU
  buffer, …) and `cuda_open`'s missing `torch.cuda.init()` is fixed in that same reviewed change; without init a
  fresh consumer segfaults, and with a user namespace the IPC open fails on this host/driver." Condition C4
  (paper-side text correction) is an owned follow-up.
- Ada host-check report `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_HOST_CHECK_20261119.md`, sha256
  **`6a7005098659e56c103d2f74e76f65979cbf39a1b46e24c3e3e168e38cda97d7`** (matches report:19–21's citation; its
  §6 has the plain-consumer matrix: `cuda_open` works after `torch.cuda.init()`, segfaults without it;
  user-namespace-only → `invalid resource handle`; sandbox shape → same).
- Kit branch `mac-trackg-iso-ar-20261117` @ `448f6820…` ("ar kit after the accepted isolation core fix `5403392`,
  merge `2e65922`", verified `git log --oneline -2 448f6820`: `448f682`, `2e65922`) and kit-update report
  `TRACKG_ISO_KIT_UPDATE_20261119.md` §3 (ar committed-file pin `b8482875…` → **`b5f0ec2f…`**; autoresearch GPU
  smoke BLOCKED by condition 7, `effective:false`, `exceptions:["shared_dev_shm"]`).
- Node spec/loader and isolation core: `src/autoresearch/trackg/node_template.py`, `runner.py`, `isolation.py`,
  `tests/trackg/test_trackg_isolation.py`, `tests/trackg/isolated_fixture.py` are **unchanged** vs base 448f682
  (`git diff --stat 448f6820 13786d1f -- <those>` empty), i.e. the accepted core sandbox is untouched; only the
  mirrored master `src/autoresearch/trackg/node_lib/ar_isolated.py` changed.

## 2. Scope and integrity — PASS

### 2.1 Files changed vs 448f6820

`git diff --name-status 448f6820 13786d1f` = the 7 intended code/spec/manifest/test files plus the 17 report/capture
files (report §2:32 says "Diff is 7 files, +85/−63"; `git diff --numstat 448f6820 0e0b820` over only those 7
files is exactly +85/−63, so the sentence is right for the code change, but the evidence file `code_change.diff`
is the whole `448f682..0e0b820` diff — 8 files, 526 lines, because the report was committed together with the code
commit; see m1). No other code/test/spec file changed.

| file | old sha256 (448f682) | new sha256 (HEAD) |
|---|---|---|
| `nodes/autoresearch_fixedtokens/run_fixed_budget.py` | `93778238d9e468e617e4c8bd8e126bc32a3a8740aa1132c2e28f921fa0479e9a` | `58d80b5224ac5e3981f60ac7b7e251a8c97eaf31d0a88a4e8811e920699a33ed` |
| `nodes/autoresearch_fixedtokens/ar_worker.py` | `fd838dac623d23e5d82cdf7927b2e7470de1fa5f3a675ae5f424905b7f689573` | `65a4927c54a566baa5efd7c26104e66eeb96ccfd6eddf92b59766b70d75613eb` |
| `nodes/autoresearch_fixedtokens/ar_isolated.py` | `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` | `3ba34c67673585e5858c5d5c2b4f0bc1b6b6be11c9898a62f71d12a5b60ddc36` |
| `src/autoresearch/trackg/node_lib/ar_isolated.py` (master) | `37d99ab0…` | `3ba34c67…` — **byte-identical to the node copy** (`cmp` OK, same sha) |
| `configs/trackg/nodes/autoresearch_fixedtokens.yaml` | `953a081d…` | `5bdce00a…` |
| `nodes/autoresearch_fixedtokens/representative_edits/manifest.json` | `02e05d06…` | `55f2666a…` |
| `tests/trackg/test_port_autoresearch.py` | `0c2e6114…` | `2b9f3692…` |

Every listed old/new sha256 was recomputed from the base archive and from the working tree and matches the report's
table (§2:34–42) and the captures (`before/after/sha256_files.txt`), which also verify against `SHA256SUMS`
(15/15 OK).

### 2.2 Frozen files outside the intent — untouched

`cmp` of base vs HEAD for `ar_parent.py`, `ar_data.py`, `prepare.py`, `ar_budget.py`, `prepare_data.py`,
`requirements.txt`, `LICENCES.md` and the E1–E4 diffs: identical. `ar_isolated.py`'s diff is **docstrings only +
one `torch.cuda.init()` line** (no sandbox/protocol logic); the node and master copies are byte-identical, which
`port_support.check_isolated` also asserts (`port_support.py:199–200`).

### 2.3 Manifest, commits, push

- Structural JSON diff of the base vs HEAD manifest: **one difference only**, `node_spec_sha256`
  `5f48b86f…` → `5c1bdf3d…` (which equals the new spec `raw_sha256`); `measured:false`, `run_budget`, the four
  edits' `sha256`/`normalised_diff_sha256`/`files_touched` and the baseline raw hash unchanged.
- 3 commits, linear, no merge commits, `448f682` is an ancestor; branch not pushed (remote
  `refs/heads/mac-trackg-iso-ar-20261117` still at `448f6820…`; no `*cond7*`/new remote head). Working tree clean.
- The report's own claim "the report was added in docs commit `6f235c4`" is inaccurate (m1).

## 3. Option A correctness — PASS (static; dynamic deferral disclosed)

**Result path, by construction.** `run_fixed_budget.py:63–92` (`LogitSource`) now unconditionally allocates
`iso.SharedBuffer((B,T,vocab), "float32")` and sends the sealed `memfd` descriptor with a `bind_cpu` request
(`:76–85`); `__call__` returns `torch.from_numpy(self.shared.snapshot()).to(self.device)` (`:92`). The whole old
`device.type == "cuda"` branch (`_set_allocator_settings`, `iso.cuda_share`, `bind_cuda`, `torch.cuda.synchronize`,
`buffer.clone`) is deleted. `ar_worker.py:142–146` maps the parent's buffer and wraps it as a CPU tensor;
`:149–162` copies `model(x)` into it with `out.copy_(result.float())` (a blocking device→host copy on a GPU host;
the CUDA-only synchronize is gone) and keeps the old shape/dtype checks; `bind_cuda` is removed and the serve table
is `{train, bind_cpu, logits, finish}` (`:171`).

**No CUDA IPC call site remains in the result path.** An AST scan (not just a string grep) of
`run_fixed_budget.py` and `ar_worker.py` finds no use of `cuda_share`, `cuda_open`, `_share_cuda_` or
`_new_shared_cuda`; the only occurrences anywhere in the tree are the (unused) definitions/docstrings in
`ar_isolated.py:617–645` and the static test. There is no fallback branch and no device-type condition left.
`iso.SharedBuffer` is the sealed `memfd` + `SCM_RIGHTS` mechanism already exercised by every other isolated node;
`bind_cpu` was previously the CPU-only branch and is now the only branch.

**Metric semantics unchanged.** The parent still pre-builds every validation batch with `prepare.make_dataloader`
and the frozen tokenizer before `P.start_worker()` (`:144–151`), holds the targets, computes
`cross_entropy(logits.reshape(-1, vocab), y.reshape(-1), reduction="none")` and the byte-count sum itself
(`:158–183`), runs the causality probe (3 cuts, `CAUSAL_ATOL`, exit 9) and the repeat check (exit 10), and writes
`AR_METRIC val_bpb=` to the result channel. `ar_budget.py` (budget closure) and the worker's weight fingerprint
(`ar_worker.py:165–168`) are untouched. The transport carries the same float32 values: the worker's `.float()`
copy is exact, the parent's memfd `snapshot()` is an exact defensive host copy, and `.to(device)` is an exact copy
to the parent's device — only the transport changed, so the metric values are identical by construction (the
CPU path is byte-for-byte the previously-tested code).

**Edge cases checked.**
- *Buffer size:* `(16, 2048, 8192)` float32 = 1,073,741,824 B = 1 GiB (real config); the CPU synthetic smoke's
  copy uses `(16, 256, 8192)` = 128 MiB (`test_port_autoresearch.py:132–135`). The memfd is `ftruncate`d and
  sealed `F_SEAL_SHRINK|F_SEAL_GROW|F_SEAL_SEAL` (`ar_isolated.py:591–599`), so the parent's mapping cannot
  SIGBUS; the worker maps the passed fd read-write and `torch.from_numpy` gets a writable array.
- *`out.copy_` semantics:* `out` is a CPU tensor over the mmap; `out.copy_(cuda_tensor)` is explicitly allowed
  across devices and is synchronous for a pageable CPU destination (`non_blocking=False`), so the parent's next
  request sees the complete write; the old explicit `torch.cuda.synchronize` is redundant now (its removal does
  not change ordering for a default-stream forward; note the pre-existing caveat that an edited `train.py` that
  runs its forward on a private CUDA stream could race — this is unchanged from the old design, not a regression).
- *`.to(device)` copy:* parent-side float32 H2D, blocking; the returned tensor is a private copy, so the worker
  cannot alter what the parent scores afterwards (same guarantee as the old `clone()`), and `snapshot()` protects
  the probe/repeat values.
- *Leaks:* one `SharedBuffer` per run, created after training, never explicitly `close()`d; this is the
  pre-existing CPU-path behaviour and is process-scoped — each isolated run is a fresh parent process, so nothing
  accumulates across a smoke/campaign. Failure paths (`P.fail`, worker death) end the parent process. No leak
  across runs.
- *Memory:* bytes moved are only the logits; the CPU page-cache accounting question is discussed under M1/§8 and
  in m5. Buffer + snapshot are within the disclosed ≈2 GiB host and ≈1 GiB VRAM transient envelope.
- *No CUDA IPC fallback:* confirmed (see above).

**Not dynamically exercised here:** the Mac has no torch and no GPU (Environment: Python 3.11.11, pytest 9.2.0,
numpy 2.4.6, `import torch` → ModuleNotFoundError, `CUDA_VISIBLE_DEVICES=`). The 18 skipped port tests (17 wrapper-metric/budget probes + the synthetic smoke)
are exactly the ones that would drive `bind_cpu`+`logits` on a torch-enabled host; the report says this (§6:151–153,
§9 risk 1). The Ada smoke/CPU run are mandatory conditions (C2/C3).

## 4. `cuda_open` `torch.cuda.init()` — PASS (evidence-backed, code unused)

`ar_isolated.py:628–645`: `torch.cuda.init()` is the first statement after `import torch`, before
`torch.UntypedStorage._new_shared_cuda`. The rationale is not invented: the accepted C3 review (sha `c8e468c7…`,
§6) and the host-check report (`6a700509…`) record that a plain consumer **without** init segfaults in
`_new_shared_cuda` and the same consumer **works** after `torch.cuda.init()`, while a user namespace yields
`invalid resource handle` (a platform limitation, not fixable here). `torch.cuda.init()` is idempotent and only
initialises a context; `cuda_open` has no call site in any node of this kit (the worker's `bind_cuda` handler was
deleted), so there is no compatibility regression — an unused helper that now fails cleanly on a CPU-only host
instead of crashing is strictly better. The fix is not re-exercised on this Mac (no torch/GPU); the report
discloses this (§9 risk 3), and it does not sit on the autoresearch result path.

## 5. Isolation — PASS (expected `effective:true`, `exceptions:[]`; confirmation deferred to Ada)

- Spec `configs/trackg/nodes/autoresearch_fixedtokens.yaml:50–51`: `shared_dev_shm: false` (was `true`); that and
  its comment are the only semantic spec change. Loader accepts it (`node_template.py:290–293`); `IsolationSpec`
  keeps the field optional/default false (`:256`).
- Runner consequence (`runner.py:518–524`): `exceptions = ["shared_dev_shm"] if iso_spec.shared_dev_shm else []`;
  `effective = not waivers and not exceptions and euid != 0 and cgroup is not None and sandbox is not None`.
  With this spec, `exceptions` is `[]`; on Ada (uid 1030, delegated cgroup v2, sandbox available — established by
  the accepted fix/host-check and the five passing isolated node smokes) the one isolated run must therefore
  record `effective:true, waivers {}, exceptions:[]`. That is expected, not yet measured for this node.
- Sandbox unchanged: `ar_isolated.py:318–323` still mounts a private `tmpfs` at `/dev/shm`
  (`mode=1777,size=8g`) when the flag is false; the flag is still passed through the runner's `_sandbox_config`.
  Nothing in the core sandbox/probe/namespace code changed (isolation.py/runner.py byte-identical vs base).
- Tests/other nodes: the only test that asserts an authoring node's `shared_dev_shm` value is the replaced one.
  The generic behaviour (`test_dev_shm_is_private_unless_the_node_opts_out`, `test_trackg_isolation.py:581–598`)
  uses the **fixture** spec and still covers both branches, including `exceptions == ["shared_dev_shm"]` and
  `effective is False` for the opted-in case; it is Linux-only and is in the 19 Linux deselected tests here (it
  must run on Ada, C3). This kit has no other Track G node, so no other node depends on the flag. Removing the
  opt-out does not break a core test or another node in this tree.
- Text residue (disclosed): the accepted core's `isolation.limits_text()` still says "with shared_dev_shm (CUDA
  IPC), /dev/shm is shared with the worker…" and "/dev is the host's (a private /dev/shm unless shared_dev_shm);
  CUDA IPC across the PID namespace is exercised only by the kits' GPU smoke" (`isolation.py:617,621`). That text
  is copied into every isolated run record (`runner.py:544`), so the AR run record will carry a now-stale CUDA-IPC
  sentence. The report discloses it as risk 6 and deliberately keeps the change out of the accepted core (m6 note;
  part of C5).

## 6. Pins — PASS (independently recomputed with the kit's own loader/definition)

Recomputed with `load_trackg_node_spec(...)` + `isolation.frozen_file_hashes(node_dir, spec.frozen_paths)` +
`sha256(json.dumps(pin, sort_keys=True))` (the runner's own definition, `runner.py:189–190,260`):

| value | base 448f682 (recomputed from `git archive`) | HEAD (recomputed from the worktree) | report |
|---|---|---|---|
| `frozen_pin_sha256` (20 entries, committed files, no `data` link) | `b5f0ec2f351d59369fb14996848fce540309393646cc20c36b6651387b1e4453` | `147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc` | matches §5:113 |
| spec `raw_sha256` | `5f48b86f03e0224cc12104ef1d335460310c271e723704055dbf9948bc135ff9` | `5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192` | matches §5:114 |

The old pin also matches the accepted kit-update report's table (`TRACKG_ISO_KIT_UPDATE_20261119.md:84`:
`b8482875…` → `b5f0ec2f…`) and the old spec hash matches the committed base manifest. Node and master
`ar_isolated.py` are byte-identical, the manifest's `node_spec_sha256` is the new spec hash, and no other manifest
field changed. **Deployed-pin caveat (m3):** after `setup_command` links `data/`, `frozen_file_hashes` hashes the
link target (`isolation.py:215–216`; `runner.py:189–190` hashes the *node root*), so the run record's
`frozen_pin_sha256` is a **deployed** pin with 21 entries, not `147f0d35` (20 entries). I reproduced this on a
node copy with a `data` symlink: deployed pin changed (and the `data` entry is `link:<absolute target>`). The
accepted kit-update report explicitly warns about this convention; report §5:132 "The census/run records will
carry the new pin" is therefore over-broad and must say which pin is which (C4/m3).

## 7. Tests — PASS (reproduced before/after; same failure set; no GPU)

Environment as claimed: Python 3.11.11 (`_harness_venv`), pytest 9.2.0, numpy 2.4.6, pyyaml present, **no torch**,
`CUDA_VISIBLE_DEVICES=`; macOS/Darwin. Tests are CPU/static only (no test requires a GPU; `grep` for
`torch.cuda.is_available()` in `tests/trackg` finds none in the changed file).

Commands and results (from the worktree, `-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`; 19 Linux-only
isolation tests deselected — the e2e subprocess/prctl/mount tests plus the memfd-sealed test; exact deselect list
reconstructed from the capture counts and confirmed by matching them):

```
pytest tests/trackg [19 deselected]        -> 9 failed, 186 passed, 19 skipped, 19 deselected (14.73 s)
pytest tests/trackg/test_trackg_isolation.py -k "<8 unit tests + 1 Linux-skip>" 
                                            -> 8 passed, 1 skipped, 19 deselected (0.15 s)
pytest tests/trackg/test_port_autoresearch.py -> 11 passed, 18 skipped (0.61 s)
```

These match the report/captures after-run (`9 failed, 186 passed, 19 skipped, 19 deselected`; `8 passed, 1
skipped, 19 deselected`; `11 passed, 18 skipped`) and the recorded 9 failure ids (3× `review_round1`
shadow/`sched_getaffinity`, 5× `review_round2` `/proc` shadow + session-kill, 1× `runner`
`sched_getaffinity`), all Darwin platform failures. Before-side check: I exported base `448f6820` with
`git archive` and ran the same selections — the isolation (8/1/19) and port (11/18) results are identical, and the
9 platform failures are identical (the export is not a git repository, so the two `test_trackg_t0_identity` tests
additionally fail there for lack of `git`; those pass in the real worktree and are unrelated). `failures.txt` is
byte-identical between `before/` and `after/`; the capture `before/` file hashes and git id match base 448f682.

The new test is meaningful and not a weakening of the removed one:
`test_result_path_uses_the_cpu_buffer_not_cuda_ipc` (`test_port_autoresearch.py:38–55`) replaces
`test_shared_dev_shm_for_cuda_ipc` and asserts (a) spec `shared_dev_shm is False`, (b) neither frozen script
contains `cuda_share`/`bind_cuda`/`cuda_open`, (c) parent uses `iso.SharedBuffer(`/`"bind_cpu"`/`snapshot()`,
(d) worker maps `iso.SharedBuffer(` and does `out.copy_(result.float())`, (e) `torch.cuda.init()` inside
`cuda_open` in the master. Together with `check_isolated`'s node==master assertion this covers both copies. It is
a source-text guard (as is the kit's style); the *dynamic* transport is exercised only by the torch tests, which
are skipped here — that is exactly what C3's Ada CPU run must cover. The other `shared_dev_shm` test uses fixture
specs, so nothing else needed changing; `py_compile` of all changed Python files passes.

Captures integrity: `shasum -a 256 -c SHA256SUMS` → 15/15 OK; `SHA256SUMS` sha256 `e47141b2…` matches report
§10:227; `code_change.diff` is byte-identical to `git diff 448f6820 0e0b820` (526 lines), which does include the
report (m1). Evidence gap (minor): the capture logs do not record the commands/deselect list, so the 19-test
selection had to be reconstructed (it reproduces exactly).

## 8. Report accuracy — one MAJOR, several MINOR

Verified correct: authority text, C3 paraphrase, host-check hash `6a700509…`, kit branch/base/merge, all 7 old/new
hash pairs, both pins and the spec hash, "20 entries", the `effective` formula, the manifest-only-spec-hash change,
the diffstat `+85/−63`, test counts and failure identity, the "18 skipped = torch/pyarrow smoke + wrapper probes"
statement, "not pushed / not run on a GPU", and the residual risks 4–6.

**MAJOR M1 — §8:171–179 slowdown disclosure is wrong by ~80× in volume and ~50–130× in time.** The real node
config (`prepare.py:42,44,60`: `MAX_SEQ_LEN=2048`, `EVAL_TOKENS=40*524288=20,971,520`, `VOCAB_SIZE=8192`;
`run_fixed_budget.py:138–143`: `rows=eval_tokens//max_seq_len=10,240`, `batch_size=min(16,rows)=16`,
`steps=rows//batch_size=640`) has **640** validation batches, not 4; with the 3 causality-probe batches
(`PROBE_CUTS`, `run_fixed_budget.py:57`) and the 1 repeat (`:171`) that is **644** logits requests per run, each
1 GiB, ≈640 GiB one-way (≈1.9 TiB with the D2H + host snapshot + H2D copies) — not 8 requests / 8 GiB. At the
report's own "0.15–0.25 s per request" that is **≈97–161 s per run**, ~48–130× the stated "≈1.2–2 s", and vs the
only measured GPU run of this node (17 Nov U2 B1 `elapsed_seconds_info_only = 67.901 s` with the old CUDA-IPC
path, `origin/main:docs/r1/reports/trackg_g0_20261117/TRACKG_U2_AR_RESULT_20261117.md:44`) it is plausibly
**2.4–3.4× the whole run**, not "small next to the 500-step training budget"; the 9-run GPU smoke alone would take
≈15–24 min longer (17 Nov whole smoke: 564 s). The "4 validation batches" is the *synthetic CPU smoke's* reduced
config (`tests/trackg/test_port_autoresearch.py:132–135`: `MAX_SEQ_LEN 256`, `EVAL_TOKENS = 4*16*256` → 4 batches,
128 MiB buffer), mixed with the real config's 1 GiB buffer. The PLAN row requires the slowdown to be measured and
disclosed; as submitted the disclosure materially understates the cost the U2/census (and the Ada session plan)
will see. No code change is needed; fix §8 (C1) and replace it with the Ada measurement (C2).

MINOR:
- **m1 (§7:159–163, §10:236):** the report says "this report is added in the docs commit that follows [0e0b820]"
  — in fact `0e0b820` contains the 221-line report (`git show --stat 0e0b820`: 8 files including the report) and
  `6f235c4` only edits §7 (+3/−2). Consequently `code_change.diff` = `git diff 448f682..0e0b820` is the 8-file
  diff (code + report), not "the 7-file code/test/spec/manifest change".
- **m2 (§1:14–16):** the R1-TRACKG-AR-COND7 row is not at `de3de54f` (added later by `bf1bcad6`; present at
  `origin/main` `df58bcd5` line 1317). Cite the published main that actually carries the row.
- **m3 (§5:132):** "The census/run records will carry the new pin" must distinguish the committed-file pin
  `147f0d35…` (20 entries) from the **deployed** pin (21 entries, `data: link:<abs target>`) that a run record
  will actually carry after `setup_command`; otherwise a U2/census check comparing the record to `147f0d35` will
  STOP or be misread. (Reproduced; the accepted kit-update report already warned about this convention.)
- **m4 (§2.3:58–59, §9 risk 4:195–198, R5:221–222):** "no node uses [cuda_share/cuda_open] (verified: the mlab
  and mlgym kits' … never call them either)" cannot be verified in this worktree (only the ar kit is present; the
  other kits live on their own branches). It is consistent with the accepted port-isolation report (only
  autoresearch used CUDA IPC), but the word "verified" needs a provenance or the claim should be softened. Also,
  after this change the `cuda_open` init fix/docstring exists only in the ar kit master; the mlab/mlgym masters
  stay at `37d99ab0…` (unused, so no runtime risk) — the propagation decision (R5) needs an owner/record.
- **m5 (§8:179–180, R4:218–220):** "the CPU-buffer page cache also counts against the run's memory cap" holds for
  cgroup-based caps (the GPU smoke uses `--memory-limit` external / `systemd-run MemoryMax`, `port_smoke_gpu.py`
  + `port_support.limits`), but **not** for the runner's default `memory_method="rlimit_data"` (RLIMIT_DATA does
  not count file-backed shared mappings; only the parent's anonymous `snapshot()` does). State the mechanism for
  the smoke; also add to R4 the metric-finiteness/repeat check that §9 risk 1 already requires ("finite and
  repeatable") so the formal condition and the risk agree.
- **m6 (informational, matches risk 6):** `isolation.limits_text()` still carries the CUDA-IPC sentence in every
  isolated run record (`isolation.py:617,621`; `runner.py:544`); after this change no node uses CUDA IPC, so the
  AR record will contain a stale sentence. Text-only; disclosed and deliberately left in the accepted core (C5).

No hidden CUDA IPC, no `cuda_share`/`bind_cuda`/`cuda_open` call site, no metric-semantics change, no pin
mismatch, no manifest field beyond the spec hash, no isolation waiver/exception, and no un-disclosed GPU-memory or
performance risk found — apart from the understated slowdown above, which is disclosed in kind but not in size.

## 9. Findings

| # | severity | where | finding |
|---|---|---|---|
| M1 | **MAJOR** | report `TRACKG_AR_COND7A_CODE_UNIT_20261120.md:171–179` (esp. `:174–177`) | Slowdown disclosure uses 8 requests / ≈1.2–2 s per run; the real config is 644 requests of 1 GiB (≈640 GiB one-way; ≈97–161 s/run at its own bandwidth), ≈2.4–3.4× the 67.9 s measured B1. Report-only; fix §8 and replace with the Ada measurement. |
| m1 | MINOR | report `:159–163`, `:236` | Wrong commit attribution (report is in `0e0b820`, not the following docs commit) and `code_change.diff` described as 7 files though it is the 8-file `448f682..0e0b820` diff. |
| m2 | MINOR | report `:14–16` | Authority row is cited at `de3de54f` where it does not exist; it is on `origin/main` `df58bcd5` (added by `bf1bcad6`), line 1317. |
| m3 | MINOR | report `:132` (and §5) | Committed-file vs deployed (`data`-link) pin not distinguished; run records will carry the deployed 21-entry pin, not `147f0d35`. |
| m4 | MINOR | report `:58–59`, `:195–198`, `:221–222` | "verified" claim about the mlab/mlgym kits is not checkable in this worktree; `cuda_open` init fix not propagated to those masters (unused, no runtime risk) — needs owner/record. |
| m5 | MINOR | report `:179–180`, `:218–220` | Memory-cap mechanism wording (RLIMIT_DATA vs cgroup) and R4 should include the metric-finite/repeat confirmation (§9 risk 1 already does). |
| m6 | MINOR | `src/autoresearch/trackg/isolation.py:617,621` + `runner.py:544` | Stale CUDA-IPC text lands in every isolated run record's `isolation.limits`; text-only, disclosed as risk 6. |

**BLOCKING: none.**

## 10. Verdict and mandatory conditions

**Verdict: ACCEPTED for the code change (7 files; scope, transport, metric semantics, pins, manifest and tests
all verified; 0 BLOCKING, 1 MAJOR, 6 MINOR).** The MAJOR is in the report only and requires no code change, but the
report may not feed the Ada smoke/U2/census planning until it is fixed.

- **C1 (M1, required before the Ada smoke).** Correct §8 to the real configuration: 640 validation requests + 3
  probe + 1 repeat = 644 requests per run of the 1 GiB buffer (≈640 GiB one-way; ≈1.9 TiB moved with D2H + host
  snapshot + H2D), and re-estimate (≈97–161 s/run at the report's own bandwidths, i.e. likely 2.4–3.4× the
  measured B1 67.901 s) or state explicitly that the measurement will replace the estimate; delete the "small next
  to the training budget" conclusion until measured.
- **C2 (Ada isolated smoke — the one smoke R1-TRACKG-AR-COND7 requires).** After C1, run the one isolated GPU
  smoke on Ada and confirm in the record/captures: `isolation.effective: true`, `waivers {}`, `exceptions: []`,
  the private `/dev/shm` (no `shared_dev_shm`), **no CUDA IPC error**, the full run completes; `bind_cpu` +
  `logits` + parent snapshot are exercised; the metric is finite and the B2 repeat is equal within `CAUSAL_ATOL`
  (metric repeat); and record the measured wall time overhead (per run and per request against the 17 Nov B1
  67.901 s), peak host cgroup memory (note the 1 GiB memfd shmem + 1 GiB snapshot) and peak VRAM. Replace §8 with
  these measured values. If the measured overhead is large, disclose it in the U2/census cost and decide a
  mitigation (e.g. registering/pinning the host buffer or copying H2D directly from the mapping) before the U2.
- **C3 (Ada Linux/CPU tests, R3).** Run the selections that cannot run on Darwin: `tests/trackg` with the 19
  Linux-only isolation tests **included**, in particular `test_dev_shm_is_private_unless_the_node_opts_out` and
  `test_shared_buffer_is_sealed_against_resizing`, and the full `test_port_autoresearch.py` (the 18 skipped
  wrapper/smoke tests) — confirm no new failures vs base `448f682` and that the dynamic `bind_cpu`/`logits` path
  and the metric/probe/exit behaviour are unchanged.
- **C4 (report MINORs m1–m3).** Fix the commit attribution and `code_change.diff` description, the authority
  citation (`df58bcd5`/`bf1bcad6`, line 1317), and state the committed-file vs deployed pin convention (include
  both `147f0d35…` and the rule for the `data`-link pin) before the report is committed for the U2/census record.
- **C5 (m4–m6).** Record the ownership/decision for (a) propagating the `cuda_open` init fix/docstring to the
  mlab/mlgym kit masters, (b) the paper-side text correction (isolation-report §3 item 7/§5.5, port report; C4 of
  the isolation-fix review), and (c) the stale `limits_text()` CUDA-IPC sentence that lands in AR run records.
- **C6 (sequence).** The autoresearch U2 unit may start only after C1–C3 and the passing isolated Ada smoke; the U2
  result must carry the deployed-pin convention and the measured slowdown; no T1 label run and no census launch
  before that. Push of this branch (and the other kits' branches) is the coordinator's step after acceptance; the
  reviewer performed no push.

## 11. Reproduction commands (read-only)

```
# scope / hashes
git -C <unit> diff --name-status 448f6820 13786d1f ; git diff --numstat 448f6820 13786d1f
git -C <unit> diff 448f6820 13786d1f -- configs nodes src tests
shasum -a 256 <7 files> ; cmp nodes/.../ar_isolated.py src/.../node_lib/ar_isolated.py
# base tree for before-side checks
mkdir -p /tmp/cond7_review_before && git -C <unit> archive 448f6820 | tar -x -C /tmp/cond7_review_before
# pins (kit loader)
PYTHONPATH=src _harness_venv/bin/python - <<'EOF'
from pathlib import Path; import json, hashlib
from autoresearch.trackg.node_template import load_trackg_node_spec
from autoresearch.trackg.isolation import frozen_file_hashes
spec = load_trackg_node_spec("configs/trackg/nodes/autoresearch_fixedtokens.yaml")
pin = frozen_file_hashes(Path("nodes/autoresearch_fixedtokens"), spec.frozen_paths)
print(spec.raw_sha256, hashlib.sha256(json.dumps(pin, sort_keys=True).encode()).hexdigest())
EOF
# no CUDA IPC in the result path (AST, not grep)
_harness_venv/bin/python - <<'EOF'
import ast
for f in ("nodes/autoresearch_fixedtokens/run_fixed_budget.py","nodes/autoresearch_fixedtokens/ar_worker.py"):
    t=ast.parse(open(f).read())
    hits=[n.attr for n in ast.walk(t) if isinstance(n,ast.Attribute) and n.attr in {"cuda_share","cuda_open","_share_cuda_","_new_shared_cuda"}]
    print(f, hits or "NO CUDA IPC API USE")
EOF
# captures
(cd .../captures && shasum -a 256 -c SHA256SUMS) ; shasum -a 256 SHA256SUMS
git -C <unit> diff 448f6820 0e0b820 > /tmp/gen.diff && diff /tmp/gen.diff .../captures/code_change.diff
# tests (Mac CPU, no torch; 19 Linux-only isolation tests deselected)
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= _harness_venv/bin/python -m pytest tests/trackg -q -p no:cacheprovider \
  --deselect .../test_trackg_isolation.py::test_ok_isolated_run_takes_the_metric_from_the_channel ... (19 ids)
... pytest tests/trackg/test_port_autoresearch.py -q
... pytest tests/trackg/test_trackg_isolation.py -q -k "isolation_block_is_validated or ... tampered_kit"
# arithmetic behind M1
rows = 40*524288 // 2048 ; batch = min(16, rows) ; steps = rows // batch  # -> 10240, 16, 640
```

*Reviewer's environment: Darwin 25.6.0 arm64, Python 3.11.11 (`_harness_venv`), pytest 9.2.0, numpy 2.4.6, no
torch, `CUDA_VISIBLE_DEVICES=`; no GPU, no Ada login, no HTCondor. ENGINEERING_ONLY; AI-assisted.*
