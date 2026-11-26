# Expansion-G1b TASL-2 host-check and CPU-set determinism review (R1-T1-NODE-EXPANSION / R1-T1-X-ENV / R1-TASL2-CPU) — 26 November 2026

**Reviewer.** Fresh independent reviewer (`exp-hostcheck-reviewer`), delegated by the lead; no involvement in
writing the spec, the prep report, the run scripts, the six records, their captures or the session. Read-only: the
only file written by this review is this review (transient helper output went to `/tmp` only). No edit, commit,
push or delete of any repository or host artefact; no experiment/test/torch execution; no GPU workload or lease;
no HTCondor, deepthought or TASL-7 action. TASL-2 was inspected read-only over
`ssh -o BatchMode=yes portal_zhixu` with `ls`, `find`, `cat`, `sha256sum`, `sha256sum -c`, `git rev-parse/status/
worktree/log/ls-remote`, `stat`, `lslocks`, `ps`, `systemctl --user list-units` and `nvidia-smi` queries only;
scripts were read, never executed; no lock file was opened with `flock`.

**Objects under review.** Six engineering records and their capture sets, written uncommitted on the ops worktree
`ops-g1b-expansion-hostcheck-20261126` (HEAD = `a1597f70f5f273f636c7f7b4b6e0e10a16c3d49a` = `origin/main`; records
untracked, no push), plus the spec they serve.

| record (under `docs/r1/reports/tasl_chain_20261122/`) | bytes / lines | sha256 |
|---|---|---|
| `TASL2_ISOLATION_HOST_CHECK_X_mlgym_titanic_20261126.md` | 10,932 / 88 | `7a2e256a222760092f08bf0978b9305ca470e12c5ccd426864022b0e9fc66c8a` |
| `TASL2_ISOLATION_HOST_CHECK_X_mlgym_metamaze_20261126.md` | 10,891 / 88 | `3bb7dd5e28846ef44998c89dc0eb702fb0a084a31c72b66b5fcccea7ee730a67` |
| `TASL2_ISOLATION_HOST_CHECK_X_gc7rc_etth1_20261126.md` | 10,870 / 88 | `17cf8c73566bb9fa5fec57d0ba1040d0330211c5b1927ad561553bbbe3096f41` |
| `TASL2_ISOLATION_HOST_CHECK_X_gc7rc_forestcover_20261126.md` | 10,937 / 88 | `67f831aabdb365e57dac4bbfebe995a84e157fb6495b2424e05c8b9959e8888c` |
| `TASL2_CPUSET_DETERMINISM_X_TITANIC_12-15.md` | 9,749 / 123 | `737f9d6b766ebaf945184b9797f64eabf33057ae31bfe47771f7a73304fb0b5e` |
| `TASL2_CPUSET_DETERMINISM_X_FORESTCOVER_4-7.md` | 9,735 / 123 | `c01029fd82502c0e7c03efd9dce2df2dbe7e4cf184379cce214f99168e199bde` |

| capture set | files | `SHA256SUMS` sha256 |
|---|---|---|
| `TASL2_ISOLATION_HOST_CHECK_X_mlgym_titanic_20261126_captures/` | 47 + `SHA256SUMS` | `13088e9c54b1d6d15f787feda9191e4d1531e79681a2881606b1cdabda4f2201` |
| `…_mlgym_metamaze_20261126_captures/` | 47 + `SHA256SUMS` | `4f1cda113bb37e65e4583a8195423491452574ef64f2a86fab3d115ef0f0017c` |
| `…_gc7rc_etth1_20261126_captures/` | 47 + `SHA256SUMS` | `7700c97795ff10788c464d8343ebac2aef4c8012caa1606bc2319ebe734da2c0` |
| `…_gc7rc_forestcover_20261126_captures/` | 47 + `SHA256SUMS` | `69855a6e01933cac6cc7ab9b9a7f6019884505802038c921c3f46c3746386953` |
| `TASL2_CPUSET_DETERMINISM_X_TITANIC_12-15_captures/` | 22 + `SHA256SUMS` | `15958255f7da8c9dc5f8134018080fb2dd7b063ccaf8b20f97d7486ac5248996` |
| `TASL2_CPUSET_DETERMINISM_X_FORESTCOVER_4-7_captures/` | 22 + `SHA256SUMS` | `f2165904dbdf8ed9441ab58c720dbc8a5c0fb77bdda5d32e08c925d2d3bf2320` |

Spec under review: `sweep2/t1_tasl/g1b_tasl_x_spec.json`, sha256
`d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238` (the amended spec's value; the P4 review
record cites it). Prep report: `G1B_EXPANSION_PREP_20261126.md` §9 (steps 1–8) and §10.

**Verdict: ACCEPTED** for the six record shas above as delivered. No BLOCKING and no MAJOR finding. The host
evidence, the two determinism checks and every measured value the review could reach were independently
reproduced: the six capture sets are byte-identical to the TASL-2 assembled sets (232/232 non-`SHA256SUMS` files),
their `SHA256SUMS` verify rc 0 locally **and** on TASL-2, the committed pins recompute exactly, both result
channels equal the census B2 channels, and the end state is idle/unleased now. Five MINOR residual text/accuracy
defects (m1–m5, §4) are non-blocking: none is in a gate field (`host_check_*`, `determinism_check_*`) and none
changes a measured claim or a PASS; m5 is the one that qualifies a procedural-compliance sentence and should be
corrected or qualified in a follow-up edit if the lead wants the record text literally exact (that edit changes a
record sha and would supersede this review for that record). The four `host_check` gates and the two
`cpu_determinism` gates are **ready** to fill once the records are committed byte-identically (§3, §5).

## 1. What was checked and how

The review re-derived the §9 requirements from `G1B_EXPANSION_PREP_20261126.md` and checked each against the
records, then against the captures, then against the primary TASL-2 sources where they are preserved. The three
evidence layers were compared to each other, not just read:

1. **Records** — the six objects above (byte sizes and shas recomputed).
2. **Captures** — each file hashed and compared with the corresponding file in the TASL-2 assembled capture sets
   under `/home/dowling/r1_engineering/t1_tasl_x_hostcheck_20261126/captures/`; all 232 non-`SHA256SUMS` files
   matched exactly (47×4 = 188 host-check, 22×2 = 44 determinism), and all six `SHA256SUMS` verify `sha256sum -c` rc 0 on
   TASL-2 and `shasum -a 256 -c` rc 0 locally.
3. **Primary session evidence on TASL-2** — the preserved run root, the four worktrees, the separate clone, the
   determinism evidence root (`/home/dowling/r1_engineering/g1bx_cpuset_determinism_20261126/`), the run
   records/logs/result channels, and the current host end state.

## 2. Findings of fact (all verified)

### 2.1 Checkouts, pins, environments, data (§9 steps 1–4)

| item | result |
|---|---|
| Separate clone `…/t1_tasl_x/harness_repo` (origin `https://github.com/dowlingwong/autoresearch_harness.git`, `main` `3c80b53c4fb2`) — not Track P | **PASS** — verified now; single `git worktree list` shows the clone + four node worktrees |
| Four detached worktrees at the spec pins | **PASS** — Titanic `3a67042ba7e4211feb9681524f3879643c8cf635`, MetaMaze `aa354485bff6b5746c48ddadcb50d92e9c6f3645`, ETTh1 `3a06d86721b0c1826b165b68a9781a561e4993f4`, Forest Cover `85851664679d10889c5af406843c4a3fc38f7a49`; `symbolic-ref` rc 1 (detached), `HEAD` = pin, `status --porcelain --untracked-files=all` = only the setup `data` link; `merge-base --is-ancestor c025f89a` rc 0 (`step1_checkouts.txt`, `step1_checks.txt`, `checkout_end.txt`) |
| Track P repository untouched | **PASS** — `/home/dowling/r1_trackp/autoresearch_harness` @ `897d83c8efa364ec2fdd37288241cc42e01d7274`, `git status --porcelain --untracked-files=no` empty, directory mtime `2026-10-25 18:26:52 -0700` (predates the session); only `rev-parse`/`status`/`stat` captured (`c7_final.json`) |
| Seven-node checkout unchanged | **PASS** — `/home/dowling/r1_tracks/t1_tasl/harness` @ `c025f89aeafc2199bf3487b4bcaa16678273c702`, tracked-clean; only the six pre-existing untracked `data` links |
| Node-spec, committed-pin, edits-manifest values | **PASS** — captures equal the spec (`059fd0d5…`/`0368a73d…`/`fd464c6e…`; `d97bb182…`/`759d6bf0…`/`6de5741f…`; `8f874c50…`/`818b8f6e…`/`ba31fed3…`; `ff2a585b…`/`78b48db9…`/`0219deb8…`). The node-spec files' raw shas match the captures' `spec_file_sha256` (`08876175…`, `d46dee59…`, `9391f718…`, `edd1a076…`). **Independently recomputed the committed pins from the live TASL-2 trees** (frozen files + link handling as `frozen_file_hashes`/`committed_view` define them): all four equal the spec exactly — `0368a73d…`, `759d6bf0…`, `818b8f6e…`, `78b48db9…` |
| torch312 freeze | **PASS** — raw sha256 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`, 77 lines, Python 3.12.16, uv 0.13.6; matches `sweep2/g1b/env/torch312.freeze.txt` |
| venv_jax freeze and interpreter target | **PASS** — raw sha256 `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9`, 56 lines, Python 3.12.16; `bin/python`, `python3`, `python3.12` all resolve to `/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12`, sha256 `23bc148d2b48964b621c5561ff2b81c1d9c7b717967a7491efbf12f4304882b5`, 31,028,464 B; freeze unchanged |
| Data staged under `/home/dowling/r1_tracks/t1_tasl_x/data` | **PASS** — manifests equal the spec: `c8ccedd0…` (3 files), `e2338195…` (9), `eacc7e69…` (1), `2b5cfb15…` (2); each file re-hashed and matching; data roots read-only (`0o40500`); setup used the node's environment first on `PATH` and `taskset -c 16-31` (a set that avoids 8–11) |

### 2.2 C1–C7 at each pin (§9 step 5)

All four records carry the exact four gate lines, once each at column 0, and no duplicate/extra `host_check_*`
key: host `TASL-2`; harness commit = the node's pin; items `1-7 PASS`; verdict `PASS`. The gate regex
(`check_host_record`) admits them structurally.

| condition | result |
|---|---|
| C1 (unprivileged user/mount/PID/net/cgroup namespaces) | **PASS** for all four pins, node interpreter and `/usr/bin/python3`: `unshare` rc 0 with flags `0x72020000`, uid 1008→0 in the new user ns, PID 1 in the new PID ns, tmpfs mount+write rc 0, all namespace inodes changed |
| C2 (Yama ptrace_scope >= 1) | **PASS**, session-wide run once and copied identically into all four sets (identical `c2_ptrace.json` sha `55277815…`): `ptrace_scope=1`, `yama` in LSM, parent→child attach ok, unrelated same-uid sibling `EPERM`; command pinned `taskset -c 16-31` (TASL-2 run-root `logs/session_c2_ptrace.log`) |
| C3 (delegated cgroup v2 subtree, `cgroup.kill`, 8G/swap 0) | **PASS** at each pin: `memory.max=8589934592`, `memory.swap.max=0`, `cgroup.kill` exists, `nsdelegate=True`, `delegate`d scope, the unit's own `RunCgroup` create→join→kill→empty→removed |
| C4 (non-root + interpreter `sys.path` hard check) | **PASS**: euid 1008; `broad_entries=[]`, `sandbox_config_ok=True`, `isolation.worker_sandbox_available` true, for the node interpreter (torch312 for Titanic/ETTh1/Forest, **venv_jax for MetaMaze**) and `/usr/bin/python3` |
| C5 (real sandboxed CPU smoke, `effective: true`, empty waivers/exceptions) | **PASS** from each checkout (`repo` = that worktree): outcome ok, `effective=true`, `waivers={}`, `exceptions=[]`, `worker_sandbox` present, `log_intact=true`, `parent_dumpable_at_accept=false`, euid 1008, `ptrace_scope=1`, `nsdelegate=true`, run cgroup removed; pinned with `taskset` to the node's G.1b set — Titanic **12-15**, MetaMaze **0-3**, ETTh1 **16-31**, Forest Cover **4-7** |
| C6 (GPU smoke with the sandbox on, under the lease, full UUID) | **PASS** at all four pins **with torch312** (including MetaMaze, whose cenv is venv_jax): GPU `GPU-4d623e76-7587-ee15-a633-46f60d220d94` by full UUID, sandboxed worker (PID 1) allocated/synchronised a CUDA tensor (`cuda_available=true`, `device_count=1`, `tensor_sum=4096.0`, `matmul_value=16.0`, no CUDA error, metric written), `effective=true`, `waivers={}`, `exceptions=[]`, cgroup removed, no compute app before/after; `flock` exclusive on `~/r1_locks/gpu0.lock` acquired/released, lease log not written |
| C7 (end state) | **PASS** at each pin: GPU identical before/after (358 MiB reservation, 0 compute apps), `gpu0.lock` free, all six leftover buckets empty, `/` 342.7 GiB free, node checkout still at the pin with only the setup `data` link untracked, seven-node checkout at `c025f89a`, Track P only stat-read and tracked-clean |
| Supplementary `tests/trackg/test_trackg_isolation.py` | **PASS** at all four pins: **27 passed, 1 skipped** (root-only `test_unprivileged_end_to_end`), rc 0, in a delegated 8G/swap-0 scope with the pin's interpreter |

### 2.3 The two determinism checks (§9 step 7, R1-TASL2-CPU)

| item | Titanic (`mlgym_titanic`, 12-15) | Forest Cover (`gc7rc_forestcover`, 4-7) |
|---|---|---|
| adapted driver / sha256 | `run_baseline_determinism_mlgym_titanic_12-15.py` `538b5a41…f3bb57c2` | `run_baseline_determinism_gc7rc_forestcover_4-7.py` `485c7db6…886a0174` |
| source driver / sha256 | stability driver `848fcb9f…4014258b` — matches | same |
| diff / sha256 / lines | `96e0835c…01f6fd05`, 154 lines | `36de7b65…08777390`, 153 lines |
| diff applies to the stability driver | **PASS** — patching the stability driver with the capture reproduces the adapted driver byte-for-byte (`538b5a41…`) | **PASS** — reproduces `485c7db6…` |
| run 1 / run 2 | 10:15:47Z–10:18:13Z / 10:18:20Z–10:20:40Z, sequential | 10:15:47Z–10:17:22Z / 10:17:29Z–10:19:03Z, sequential; the two nodes ran concurrently on disjoint sets |
| per-run wrapper | 5 s `/proc/stat` busy preflight (set max 0.010 / 0.008 ≤ 0.2), `flock -n cpus-12-15.lock`, `systemd-run … Delegate=yes MemoryMax=8G MemorySwapMax=0`, `CUDA_VISIBLE_DEVICES=` hidden, torch312 first on `PATH`, `taskset -c 12-15`, driver `--group 12-15 --repeat n` | same with 4-7 (set max 0.012 / 0.002) |
| runs / outcome | rc 0, outcome ok, executed, full **150,000**-step census budget (primary `run.log`: `AR_STEPS completed=150000`), seeds 8001/8001, empty proposal list (only `s000_baseline`) | rc 0, outcome ok, executed, full **8,000**-step budget (`AR_STEPS completed=8000`), seeds 8001/8001 |
| `result_channel_sha256` | `77a834ecf04cfff506bc0c46368dbf8e87f31dedb184035b422e74c4abfce9d4` both runs — **equal to the census baseline's** (`TITANIC_U2_RESULT_20261125_RETRY_captures/result_channels/{s000_baseline,B2}.txt` sha256 computed locally: same) | `bcfc9b5d296a07335f46ec467c68ca7e282355882fccd44f9ea7f68cd628140a` both runs — **equal to the census baseline's** (`FORESTCOVER_U2_RESULT_20261125_captures/result_channels/B2.txt`, same) |
| `elapsed_seconds_info_only` and bound | 144.411 / 139.656 s ≤ 207.2745 s (1.5 × B1 138.183) | 93.510 / 93.547 s ≤ 140.109 s (1.5 × B1 93.406) |
| isolation / waivers / exceptions / frozen | `effective=true`, `waivers={}`, `exceptions=[]`, `frozen_files_changed=[]` (16 checked) both runs | same (16 checked) |
| affinity / scope / GPU | exactly `[12,13,14,15]`; `memory.max=8589934592`, `memory.swap.max=0`; no GPU (`CUDA_VISIBLE_DEVICES=""`) | exactly `[4,5,6,7]`; 8G / swap 0; no GPU |
| log reproducibility | both `run.log` sha256 `70d93e9f98684e53…` (byte-identical across runs) | both `run.log` sha256 `07c6557e5a66…` |
| checkout at run time | `3a67042b…` clean apart from `?? third_party/mlgym/nodes/mlgym_titanic/data` | `85851664…` clean apart from `?? nodes/gc7rc_forestcover/data` |
| record lines | the eight `determinism_check_*` lines exactly once at column 0 with the required values; seconds within bound; gate emulation (`check_determinism_record` semantics, including the `^\W*key\s*:` duplicate/markup refusal) **passes** | same |
| metric discipline | no metric value in the record or capture set; the census baseline's value exists only in the preserved evidence root's result channels (not copied into the records, the captures or this review), as §9 step 7 requires | same |

The determinism records' claim that the result channels reproduce the census baseline bit-for-bit is supported by
the primary channels (63 B each, both runs) and by the identical `run.log` hashes.

### 2.4 End state, no deletion, no earlier job (§9 step 8)

- **Now**, after both determinism checks: GPU `358 MiB, 0 %`, no compute apps; no `g1bx-*` user scope; no `ar_*`
  run cgroup; no determinism process; no CPU-set or GPU lock held (`lslocks` empty for `gpu0`/`cpus-*`);
  `/home/dowling/r1_tracks/t1_tasl_x/runs` and `sealed_g1b` do not exist (no G.1b job was started), so the checks
  ran before the nodes' first job as required.
- `session_end_state.txt` (10:21:37Z) records the GPU free, `cpus-0-3`/`cpus-4-7`/`cpus-12-15` leases free, all
  four node checkouts at their pins with only their `data` links, the seven-node checkout clean at `c025f89a`,
  Track P read-only (head `897d83c8`, mtime 2026-10-25) and `/` 343 GiB free.
- Nothing was deleted: the evidence root and its `validation` attempts are preserved, and no session script or
  host-check script deletes a repository/evidence path or runs `git commit/push/reset/clean`; the only removals are
  the probes' cleanup of their own temporary probe directories (`probe_userns.py` `os.rmdir`,
  `probe_interp.py` `shutil.rmtree`). `origin/main` is still `a1597f70` (the records are untracked).

## 3. Gate readiness

| node | gate requirements (spec `gate_requires`) | state |
|---|---|---|
| `mlgym_titanic` | `host_check`, `cpu_determinism` | **ready** — host-check record sha `7a2e256a…` at pin `3a67042b…`; determinism record sha `737f9d6b…` at cpus 12-15 |
| `mlgym_metamaze` | `host_check`, `env_row` | **ready** — host-check record sha `3bb7dd5e…` at pin `aa354485…`; `R1-T1-X-ENV` row is already on `main` (`docs/r1/PLAN.md` line 1547) and contains the required verbatim sentence |
| `gc7rc_etth1` | `host_check`, `review` | **ready** — host-check record sha `17cf8c73…` at pin `3a06d867…`; `docs/r1/reviews/G1B_EXPANSION_REVIEW_20261126.md` is on `main` (sha `7b6423f4…`) with one `spec_sha256: d0dce058…` line, one `verdict: ACCEPTED` line and the two `cpu_census_disposition` lines |
| `gc7rc_forestcover` | `host_check`, `review`, `cpu_determinism` | **ready** — host-check record sha `67f831aa…` at pin `85851664…`; determinism record sha `c01029fd…` at cpus 4-7; same review record |

- The four `host_check` gate lines can be filled as `host check <record> sha256 <its sha256>` with the shas above
  once the records are committed **byte-identically** to published `main`; the two `determinism check` lines
  likewise for Titanic and Forest Cover. The gate functions read only the four/eight column-0 lines and the
  record sha, and both were emulated over the delivered bytes: they pass (including the `runs: 2`, cpus, pin,
  channel-sha equality and seconds-within-1.5×B1 checks).
- The `hosts[].isolation_host_check` key is correctly absent from this node-expansion spec (the host check is per
  node and cited in each `gate_<node>` line).
- **P2 is not complete and cannot be completed by this session**: the four kit records and kit reviews that the spec
  cites are present on `main` with matching sha256s and each review's verdict is **ACCEPTED**
  (`TITANIC_KIT_REVIEW_20261125.md`, `MOUNTAINCAR_KIT_REVIEW_20261125.md`, `ETTH1_KIT_REVIEW_20261125.md`,
  `FORESTCOVER_KIT_REVIEW_20261125.md`), but prep report §7.5 / §10 say kit-review **c1** is still to be recorded
  by the coordinating chat; P2 stays PENDING until it is. That is a coordinator/plan step, not a defect in this
  session's evidence.
- No re-run of any host check or determinism check is required or suggested.

## 4. Findings

### BLOCKING

None.

### MAJOR

None. All gate-critical facts were independently reproduced (pins, environments, data, C1–C7, the two determinism
runs, the current end state), the capture sets are byte-identical to TASL-2, and every measured value cited in the
records matches its capture/primary source.

### MINOR (non-blocking; none is in a gate field, none changes a measured PASS)

- **m1 — wrong determinism cross-reference in two host-check records.** The MetaMaze and ETTh1 records' line 26–27
  say "The node's fixed-seed CPU-set determinism check (R1-TASL2-CPU) is a separate record
  (`…TASL2_CPUSET_DETERMINISM_X_FORESTCOVER_4-7.md`)". Neither node has a determinism check: both are on their
  census sets (0-3, 16-31) and their spec entries carry no `cpu_replacement`; the Forest Cover record is not
  "the node's" check. Correct text: no R1-TASL2-CPU determinism check applies to this node (or drop the
  sentence). Titanic correctly cites its own record; Forest Cover correctly cites its own.
- **m2 — frozen-entry count is off by one in all four host-check records.** §"Steps 1-4", step 2 says "16 frozen
  entries before the data link" (19 for MetaMaze). The cited `pins_*.json`/`.txt` — captured at step 2, when the
  data link was absent — records `frozen_entries=15` (18 for MetaMaze). 16/19 is the count of the full pin *after*
  the data link is present (committed view is 15/18; I recomputed the current full pins as 16/19/16/16 and the
  committed views as 15/18/15/15 from the live trees, reproducing the spec pins exactly). The sentence should read
  15/18 "before the data link" (or 16/19 "including the data link"). No pin value or gate value is affected; the
  same 16 appears correctly in the determinism records' "frozen checked" column.
- **m3 — typo in the Forest Cover determinism record.** §"Per-run wrapper" line 59 reads "The two nodes' checks
  (Titanic on 4-7 and Forest Cover on 4-7)"; Titanic's set is **12-15** (the Titanic record has the correct text).
- **m4 — the driver-validation sentence is imprecise.** Both determinism records say "one reduced-budget
  (**511** steps) run per node exercised the driver code path … (`validation/`)". The retained validation result
  shows `dryrun_steps=512` and `run_budget {steps, 512}`; the session's own logs show four validation attempts per
  node (rc 2, 1, 1, then 0), of which the fourth is the run preserved in `validation/`. Recommend "512 steps" and
  a word that the preserved validation run is the last of four attempts. This is auxiliary evidence only; neither
  determinism run is affected.
- **m5 — the "every CPU-bound step was pinned / CPUs 8-11 were never used" claim is over-broad.** The records'
  "What this binds"/"Scope" text asserts that every CPU-bound step ran under `taskset` and that CPUs 8–11 were not
  used by any step. The evidence supports this for the checks that matter: C1 (env+syspy), C3, C4, C5 and C7 carry
  `taskset -c <node set>` in the captured command lines; C2 and the data setup carry `taskset -c 16-31`; and the
  determinism runs carry `taskset -c <set>` with affinity asserted `[12,13,14,15]`/`[4,5,6,7]`. But the
  **supplementary pytest** step (4 × ≈15 s; `phase3_checks.sh` runs `exec timeout 900 "<python>" -m pytest …`
  inside the scope, with no `taskset`) and the **C6 GPU-smoke wrapper** (`run_gpu_smoke.sh` contains no `taskset`)
  ran with the default affinity, which includes CPUs 8–11; the step-1/2/3 helper invocations have no captured
  command line either way. Nothing suggests 8–11 were actually used (unpinned ≠ used), and no pinned C1–C7 or
  determinism evidence is tainted, but the absolute sentence is not established for those steps. Correct the
  wording (e.g., list the pinned steps exactly and say the supplementary pytest and the C6 wrapper ran unpinned)
  or qualify it; this is the only MINOR that touches a procedural-compliance statement, and any correction changes
  that record's sha.

### Observations (no action required)

- **O1 (cosmetic).** The host records' C7 wording "GPU identical before/after (… 0 %)" — for Titanic and Forest
  Cover the post-C6 `nvidia-smi` sample shows 5 % utilisation (memory 358 MiB and zero compute apps on both
  sides; a transient sample). The idle/unleased conclusion is unaffected.
- **O2 (inherited constant).** The determinism run records carry `steps_full_budget: false`, because the adapted
  driver inherits the stability driver's `max(steps) >= 2000000` test; the full budget is established instead by
  the primary `AR_STEPS completed=150000` / `8000` log lines and by the channel match. No gate reads the field.
- **O3 (row wording, not host evidence).** The published `R1-T1-X-ENV` row says "the host check refuses a
  different target or sha256". `env_check.py` records the target path/sha256/size and fails on a non-3.12.16 target
  or differing symlink targets, but it does not compare the target sha256 against a pinned expected value, so no
  "refusal of a different sha256" is evidenced. The row's substantive requirement — the host-check session records
  the target path and sha256 (before the first MetaMaze job) — is met. Worth reconciling the row's wording in the
  row/note review.
- **O4 (scope of captures).** The host-check capture sets reproduce outputs only; the probe scripts live in the
  preserved TASL-2 run root (`…/scripts/`). The records say exactly that, and the run root was read for this
  review; no action.
- **O5 (process note).** The TASL-2 run root's `logs/det_validation*.log` lines record four validation attempts per
  node (rc 2, 1, 1, 0); only the fourth attempt's result directory is retained in `validation/`. See m4.

## 5. Conditions for the lead (commit/gate, not host evidence)

1. **Commit the six records byte-identically to published `main`** (base `a1597f70`; merge, do not squash or
   rebase), then fill the four `gate_<node>` `host check …` lines and Titanic's and Forest Cover's
   `determinism check …` lines with the shas in §"Objects under review". Do not re-run anything.
2. If any MINOR is corrected before committing, the affected record's sha changes: re-hash and re-review that
   record; the shas in this review apply to the bytes as delivered.
3. Keep P2 PENDING until the coordinating chat records kit-review c1 (prep §7.5/§10); the kit reviews themselves
   are ACCEPTED with spec-matching shas. The `env_row` and `review` gate inputs are already on `main`.
4. Do not treat this review as a launch authorization: the per-node gates, the note and the P4 review record
   remain the launch inputs.

## Verdict

**ACCEPTED** — the six records are accurate host/determinism evidence for the four `host_check` gates and the two
R1-TASL2-CPU `cpu_determinism` gates; no BLOCKING or MAJOR finding; the five MINOR residuals (m1–m5) are prose or
auxiliary-evidence accuracy items outside the gate fields and do not change any measured PASS; gates are ready
once the records are committed byte-identically. m1–m4 are worth a follow-up correction if the lead wants clean
text (each such edit changes a record sha); m5 should be corrected or qualified if the record is to claim literal
CPU-pinning compliance.

*AI-assisted: DeepSeek Harness agent `exp-hostcheck-reviewer`, 26 Nov 2026. ENGINEERING_ONLY; uncommitted.*
