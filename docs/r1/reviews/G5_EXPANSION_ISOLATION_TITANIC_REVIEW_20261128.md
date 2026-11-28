Verdict: ACCEPTED WITH MINORS

# Independent review of the TASL-2 host-check record for `mlgym_titanic` at the G.5 harness pin `d2ce4701` — 28 November 2026

**Reviewer.** Fresh independent reviewer (`compute`, R1 route). Not involved in writing the record, the check scripts,
the captures or the host session. Read-only against a clean clone of `dowlingwong/Agent_paper_B`; no host workload,
no lease, no experiment, no label/test/evaluation inspection, no edit of `main` or of the deliverable branch. The
harness repository was read anonymously over HTTPS (`git ls-remote` / `git show`) only.

**Scope.** The Titanic portion of `compute/20261128-20`, deliverable branch
`compute-g5-expansion-isolation-titanic-20261128` at tip `af191d0119976aeb2f47762f31ab11003d477e33` (reviewed
earlier at `af6843fa8c6392406cd8744cb135972cca22dcb7`; the branch also carries the MetaMaze record `c17dda52`,
which is outside this review). Paper base `origin/main` `66aa4e10b107d81d6abc305fb1fa16879ff737d7`
(the merge after `57e6d1ed`). Card `origin/coord/coordinator:tasks/compute/20261128-20-addenda-isolation.md`,
handoff `origin/coord/local:reports/20261128-14-g5-titanic-isolation-handoff.md` (commit `6ec596de`), accepted
harness review `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md` on `main`.

| Object | sha256 |
|---|---|
| record `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_mlgym_titanic_20261128.md` | `3d76372dc02ccfe01dfccb15f4c9180fbf59c2d33fa035d5a66faee9d3ece1f2` (unchanged from `af6843fa`) |
| capture set `…_20261128_captures/SHA256SUMS` | `5716a587963aca2287b57933c5c4143faa6cba1c9eb5c3181899039afc5b8387` |
| capture set | 32 captures + `SHA256SUMS` (33 files) — 32/32 verify |
| `torch312.freeze.txt` (77 lines) | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` |

## Gate lines

Present at column 0 (checked with `awk '{print length($0)": ["$0"]"}'` on lines 7-10), exactly:

```
host_check_host: TASL-2
host_check_harness_commit: d2ce4701faf03f00efaf9c475879acf213411d3b
host_check_items: 1-7 PASS
host_check_verdict: PASS
```

The harness commit exists and is the reviewed one: `git cat-file -t d2ce4701…` → `commit`; its parent is
`3a67042b…`, and `git merge-base --is-ancestor 3a67042ba7e4211feb9681524f3879643c8cf635 d2ce4701…` → rc 0. Commit
`d2ce4701` changes exactly `src/autoresearch/trackg/audit_g5.py`
(sha256 `5f384204c34e297191281bb3981db57607d58333222adab6def97e8d099e2690`) and
`src/autoresearch/trackg/campaign_v2_diff.py`
(`9d4f8e6838c31ebec835fd13434532b8afb8539e3cdd913188e52300d0c0a708`), matching the accepted harness review.

## Checks run (clean clone at the tip)

```
$ git clone https://github.com/dowlingwong/Agent_paper_B.git g5rev && git -C g5rev checkout af191d01
$ git rev-parse HEAD
af191d0119976aeb2f47762f31ab11003d477e33
$ git diff --stat af6843fa af191d01
 4 files changed, 38 insertions(+)      # the two Titanic and two MetaMaze run.log files only
$ shasum -a 256 docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_mlgym_titanic_20261128.md
3d76372dc02ccfe01dfccb15f4c9180fbf59c2d33fa035d5a66faee9d3ece1f2
$ cd …/TASL2_ISOLATION_HOST_CHECK_X_mlgym_titanic_20261128_captures
$ shasum -a 256 -c SHA256SUMS
… all 32 lines: OK
rc=0
```

- **Archive integrity.** 32/32 files verify, including both `records/titanic_*_smoke/run.log` and the
  `gpu_report.json`/`run_record.json` pairs. At the earlier tip `af6843fa` the two `run.log` entries were absent
  because `.gitignore` drops `*.log`; `af191d01` force-adds them and changes no other Titanic file (only additions).
- `wc -c stop_items.txt` → `0` (empty).
- `pytest_isolation.json` → `"counts": {"passed": 27, "skipped": 1}`, `rc: 0`, tail
  `27 passed, 1 skipped in 14.81s` (skip is the root-only test), run in a delegated 8G/swap-0 scope with torch312.

## C1-C7 (recomputed from the captures)

| # | Evidence read | Result |
|---|---|---|
| C1 | `c1_userns_env.json`, `c1_userns_syspy.json`: `condition_1_pass: true` both; torch312 and `/usr/bin/python3`; user/mount/PID/net (+cgroup) `unshare` rc 0, uid/gid 1008 mapped to 0, real tmpfs mounted and written | PASS |
| C2 | `c2_ptrace.json`: `ptrace_scope: 1`, yama in LSM, parent→child attach/detach ok, unrelated same-uid sibling `EPERM` (errno 1), `condition_2_pass: true` | PASS |
| C3 | `c3_cgroup.json/.txt`: `memory.max=8589934592`, `memory.swap.max=0`, `nsdelegate`, `cgroup.kill` present, `memory pids` controllers, create→populate→`cgroup.kill`→empty→removed, `condition_3_pass: true` | PASS |
| C4 | `c4_interp.json/.txt`: euid 1008 non-root; both interpreters pass the `sys.path` probe at the pin `d2ce4701…` (`broad_entries=[]`), `condition_4_pass: true` | PASS |
| C5 | `c5_smoke.json`: outcome `ok`/`1.0`, `isolation.effective=true`, `waivers={}`, `exceptions=[]`, `log_intact=true`, cgroup removed, `condition_5_pass: true`; result channel `4ffec570…` matches the run log and record | PASS |
| C6 | `c6_gpu_smoke.json`: full UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94` = expected; torch312; all 15 `checks` true (worker PID 1, sandbox present, tensor sum 4096, no CUDA error, metric written); `waivers={}`, `refused=false`; lease `~/r1_locks/gpu0.lock` flock-exclusive 14:07:37-14:07:39Z, no lease log; `nvidia-smi --query-compute-apps` empty pre/post; `condition_6_pass: true` | PASS |
| C7 | `c7_final.json/.txt`, `checkout_end.txt`: harness HEAD `d2ce4701…` (matches pin), seven-node checkout `c025f89a…`, only `third_party/mlgym/nodes/mlgym_titanic/data` untracked, GPU 353 MiB / no compute apps / 0 % after, lease `lease_free`, all six leftover buckets empty, 333.9 GiB free, Track P harness `897d83c8…` tracked-clean, `condition_7_pass: true` | PASS |

## Pins and environment

Recomputed against the committed inputs on `main` and the harness pin:

| Value | Record / capture | Independent check |
|---|---|---|
| `node_spec_sha256` | `059fd0d50059b4627382979fc9064a9f223f79e06b616eba195eefbb3f3380c1` | identical in `G5_EXPANSION_ADDENDUM_MLGYM_TITANIC_DRAFT_20261127.md` and `g1b_x_t1_tasl_20261126.md` on `main` |
| `committed_pin_sha256` | `0368a73d86f9cf8d695fe39cc6e4f3aa54f4c882c95ab66ddc146b519af80086` | identical in the same two `main` files |
| `edits_manifest_sha256` | `fd464c6e1bfc1ab13aded048e1feba97b2844f8fe537f3b0b8eaf1ae3e4a9bce` | harness `d2ce4701:third_party/mlgym/nodes/mlgym_titanic/representative_edits/manifest.json` hashes to this |
| `data_manifest_sha256` | `c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4` | matches `pins_mlgym_titanic.json`, `c7_final.json` and the addendum draft on `main`; all 3 node data files re-hashed `match: true` |
| torch312 freeze | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`, 77 lines, Python 3.12.16 | `git show origin/main:sweep2/g1b/env/torch312.freeze.txt` → same sha256, `wc -l` 77; `diff` against the capture is empty |

The node spec's raw file sha256 is `08876175e02d498b10680d3c35b5969b731404c513ec3fffc858374fa484ddac`, recorded as
`spec_file_sha256` in `pins_mlgym_titanic.json`; it is not the gate value and does not contradict
`node_spec_sha256`.

The record does **not** claim the other three nodes were run: it says their isolation checks are not run here
(lines 78-79). `host_facts` lists those checkouts at their census kit pins but contains no 20261128 isolation
records for them.

## Non-overclaim

- No G.1b/G.5/G.4 chunk: the only run records are the C5/C6 smoke records; `result_channel.txt` carries the kit's
  synthetic fixture (`val_accuracy: 1.0000`, `test_accuracy: 0.4242`), already identified as a fixture value in
  `G5_P11_ENGINEERING_REVIEW_20261128`. No census/chunk/campaign artefact is present.
- The data step only re-hashes `train.csv`, `test.csv`, `ground_truth.csv` for manifest match; no label content or
  evaluation value was inspected by the reviewer or recorded in the captures.
- No host push/commit: `checkout_end.txt` shows the detached G.5 worktree at the exact pin with only the `data`
  link untracked; there is no new commit or remote-tracking state in the captures. No deletion is claimed.
- CPU set: see m2.

## Findings

- **F1 (resolved at the reviewed tip).** At `af6843fa` `shasum -a 256 -c SHA256SUMS` failed with 2/32 unreadable:
  the `records/titanic_*_smoke/run.log` files were listed but absent, because `.gitignore` ignores `*.log` (the same
  pattern affects the four 20261126 isolation capture sets). Tip `af191d01` force-adds the four run logs and
  changes nothing else; 32/32 now verify from a clean checkout. No capture content changed, so the record's
  sha256 `3d76372d…` is unchanged and the addendum gate binding stays valid.
- **m1 (prose count now stale).** Record line 70 says the capture set is "31 files + `SHA256SUMS`"; at the reviewed
  tip it is 32 captures + `SHA256SUMS` (33 files). The gate does not read the count, but if the sentence is
  corrected the record's sha256 changes and Local must re-fill `host check <record> sha256 <…>` with the new digest.
  Leave as is (recommended) or fix in a coordinated follow-up.
- **m2 (inherited, procedural wording).** Line 64/65: "No CPUs 8-11 were used: every CPU-bound step was pinned
  with `taskset -c 12-15`." No committed capture contains a `taskset` command line: the C5/C6 `argv`, the
  `pytest_isolation.json` command and `commands.txt` all lack it, and no affinity capture exists. This repeats
  finding m5 of `EXPANSION_HOSTCHECK_REVIEW_20261126`. Nothing suggests CPUs 8-11 were used (the host was idle,
  `host_facts` `running_jobs=` empty), and no C1-C7 gate or environment binding is affected, but the absolute
  sentence is not evidenced by this capture set. Qualify it, or add an affinity capture in a future run.
- **O1 (transient sample).** C6's post-smoke `nvidia-smi` sample (`utc 14:07:39Z`) shows 8 % utilisation (memory
  353 MiB and compute-apps output identical to before); the immediately following C7 end-state sample (same
  second) shows 0 %, and the record's "GPU identical before/after" is stated for C7, where it holds.
  Idle/unleased conclusion unaffected.
- **O2 (cosmetic).** `pins_mlgym_titanic.txt` prints `data_files_present_and_match: got=None expected=None
  match=True`; the JSON carries the three per-file hashes, all `match: true`.
- **O3 (cosmetic).** C7's `data.link.is_symlink` is `false` because it inspects the node directory, not `data`;
  the expected untracked `data` entry is evidenced by the `git status --untracked-files=all` fields.
- **O4 (reader clarity).** `host_facts` "checkout mlgym_titanic: head=3a67042b…" is the G.1b checkout; the G.5
  worktree at `d2ce4701…` is captured in C4/C7. No contradiction.

## What remains

1. Coordinator publishes the record (or the branch tip) and Local fills the `mlgym_titanic` addendum gate with
   `host check <record> sha256 3d76372d…`, then runs the draft checks.
2. The MetaMaze record on this branch (`c17dda52`) needs its own independent review; ETTh1 and Forest Cover still
   need their per-node host checks at `6fc553df…` and `3f7b09fe…`.
3. Optional: correct m2 wording (and, if done, re-bind the record sha) at the next natural record revision.

**AI-assisted: DeepSeek compute agent, 28 Nov 2026. ENGINEERING_ONLY.**
