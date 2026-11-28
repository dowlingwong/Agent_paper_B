Verdict: ACCEPTED WITH MINORS

# Independent review of the TASL-2 host-check record for `gc7rc_etth1` at the G.5 harness pin `6fc553df` — 28 November 2026

**Reviewer.** Fresh independent reviewer (tier E, engineering). Not involved in writing the record, the check
scripts, the captures or the host session. Read-only against a new git worktree of `dowlingwong/Agent_paper_B`;
no host workload, no lease, no experiment, no label/test/evaluation inspection, no edit of `main` or of the
deliverable branch. The harness repository was not cloned or run; its pin was checked against the committed
handoff and the accepted harness review on `main`.

**Deliverable.** Branch `compute-g5-expansion-isolation-etth1-20261128` at tip
`ea6ab2bc743af7fe15b5678e0fd3983d3e47b90e` (single commit, parent `9b044b59f58109b3d1e4eb1822623160958b1d95`).
Base `origin/main` `9b044b59…` is the merge base of the tip with `origin/main` (current `origin/main` has since
advanced to `bf96387c`, which contains `9b044b59`). Card `origin/coord/coordinator:tasks/compute/20261128-20-addenda-isolation.md`
(commit `d47cab43`, an ancestor of the current coordinator tip `ac7fb1a5`). Handoff
`origin/coord/local:reports/20261128-14-g5-etth1-isolation-handoff.md` at `150212b1dc719e4811962f7dc9b100cdbd49a68c`.
Paper test base `57e6d1ed5945ab48684e24e145b69d333b4f77d4`.

| Object | sha256 |
|---|---|
| record `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_gc7rc_etth1_20261128.md` | `6c2231d50c274a26512c5cc20cfcf97212b764e755e0dc6b948d33fbab3369b7` |
| capture set `…_20261128_captures/SHA256SUMS` | `218005c5f4ab2b52f69868df58e6a44ebf7fba667f57ed1c81646aee761a137a` |
| capture set | 35 captures + `SHA256SUMS` (36 files) — 35/35 verify |
| `torch312.freeze.txt` (77 lines) | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` |

## Gate lines

Present at column 0 on lines 7–10, exact (checked with `awk` lengths 23/67/26/24; no trailing whitespace):

```
host_check_host: TASL-2
host_check_harness_commit: 6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c
host_check_items: 1-7 PASS
host_check_verdict: PASS
```

The harness commit equals the pin in Local's handoff (`6fc553df…`, parent `3a06d867…`) and the accepted harness
review `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md` on `main` (review sha256
`4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`, matched by recomputation). The
`checkout_end.txt`, `c4_interp.txt` and `c7_final.json` all carry the same full 40-hex pin.

## Checks run (new worktree at the tip)

```
$ git worktree add …/etth1g5_review ea6ab2bc743af7fe15b5678e0fd3983d3e47b90e --detach
$ git rev-parse HEAD
ea6ab2bc743af7fe15b5678e0fd3983d3e47b90e
$ git merge-base --is-ancestor 9b044b59f58109b3d1e4eb1822623160958b1d95 ea6ab2bc ; echo $?
0
$ git diff --stat 9b044b59 ea6ab2bc | tail -1
 37 files changed, 3198 insertions(+)
$ git diff --name-status 9b044b59 ea6ab2bc | awk '{print $1}' | sort | uniq -c
  37 A
$ cd …/TASL2_ISOLATION_HOST_CHECK_X_gc7rc_etth1_20261128_captures
$ shasum -a 256 -c SHA256SUMS | grep -c ': OK'
35
$ shasum -a 256 -c SHA256SUMS >/dev/null ; echo $?
0
$ shasum -a 256 SHA256SUMS
218005c5f4ab2b52f69868df58e6a44ebf7fba667f57ed1c81646aee761a137a  SHA256SUMS
$ wc -c < stop_items.txt
0
```

- **Archive integrity.** 35/35 listed files verify from the clean worktree, including both `records/*/run.log`
  files (no `.gitignore`-drops-`*.log` problem here), the `gpu_report.json`/`run_record.json` pairs and the
  `SHA256SUMS` digest itself. All added files are additions only; no existing file was changed or deleted.
- **Condition flags.** Parsing `c1_*.json` … `c7_final.json` gives
  `condition_1_pass`…`condition_7_pass` all boolean `true` (`c1_userns_env.json` and `c1_userns_syspy.json` both
  carry C1). `stop_items.txt` is empty (0 bytes).
- **Supplementary pytest.** `pytest_isolation.json`: `rc: 0`, `{"passed": 27, "skipped": 1}`, tail
  `27 passed, 1 skipped in 14.91s` in a delegated 8G/swap-0 scope with torch312 (the skip is the root-only test).

## C1–C7 (recomputed from the captures)

| # | Evidence read | Result |
|---|---|---|
| C1 | `c1_userns_env.json`, `c1_userns_syspy.json`: both `condition_1_pass: true`; torch312 `3.12.16` and `/usr/bin/python3` `3.10.12`; user+mount+PID+net(+cgroup) `unshare` rc 0, uid/gid 1008 mapped to 0, child PID 1 of its PID namespace, real tmpfs mounted and written (`launcher_all_five_one_call`, `user_mount_pid_net`) | PASS |
| C2 | `c2_ptrace.json`: `ptrace_scope: 1`, `yama_in_lsm: true`, parent→child attach/detach ok, unrelated same-uid sibling attach `EPERM` (errno 1), `condition_2_pass: true` | PASS |
| C3 | `c3_cgroup.json`/`.txt`: `memory.max=8589934592`, `memory.swap.max=0`, `nsdelegate=True`, `cgroup.kill` present, owner uid 1008, create→populate→`cgroup.kill`→empty→removed, all nine checks true, `condition_3_pass: true` | PASS |
| C4 | `c4_interp.json`/`.txt`: euid/uid 1008 non-root; torch312 3.12.16 and `/usr/bin/python3` 3.10.12 both pass the `sys.path` probe at pin `6fc553df…` (`broad_entries=[]`, `sandbox_config_ok=True`), `condition_4_pass: true` | PASS |
| C5 | `c5_smoke.json`: outcome `ok`/`1.0`, `isolation.effective=true`, `waivers={}`, `exceptions=[]`, `log_intact=true`, ptrace_scope 1, cgroup removed, `condition_5_pass: true`; result channel `4ffec570…` matches the run log | PASS |
| C6 | `c6_gpu_smoke.json`: full UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94` = expected; torch312; all 15 `checks` true (worker PID 1, sandbox present, tensor sum 4096, `torch 2.6.0+cu124`, CUDA 12.4, metric written, no CUDA-error text, cgroup removed); `waivers={}`, `refused=false`; lease `~/r1_locks/gpu0.lock` flock-exclusive 14:48:20–14:48:22Z, no lease log; `nvidia-smi --query-compute-apps` empty pre/post; `condition_6_pass: true` | PASS |
| C7 | `c7_final.json`/`.txt`, `checkout_end.txt`: harness HEAD `6fc553df…` = pin; seven-node checkout `c025f89a…`; only `nodes/gc7rc_etth1/data` untracked; lease `lease_free`; all six leftover buckets empty; 333.9 GiB free; Track P harness `897d83c8…` tracked-clean; `condition_7_pass: true` | PASS |

## Pins, environment, data

| Value | Record / capture | Independent check |
|---|---|---|
| `node_spec_sha256` | `8f874c50f66273e0655bfc9ccdad24a50c0fdb629f88ba7d4d60b13f2fcf2e0c` | identical in `G5_EXPANSION_ADDENDUM_GC7RC_ETTH1_DRAFT_20261127.md`, `g1b_x_t1_tasl_20261126.md` and the 20261126 ETTh1 capture set on `main` |
| `committed_pin_sha256` | `818b8f6e8ec6473f15c33ed58393e7cee8b8e8b0a71645576439929efb20bf27` | identical in the same committed files |
| `edits_manifest_sha256` | `ba31fed3bb67c0d78825a0d026058cbeb3a0261971fe8a4766f138687b232306` | identical in `g1b_x_t1_tasl_20261126.md` and the 20261126 captures |
| `data_manifest_sha256` | `eacc7e69f45fed3e7eb0c9bb76cf5c18387bcae4ba226a24812dc409c0b51e1b` | matches `c7_final.json`, `pins_gc7rc_etth1.json`, `datapins_gc7rc_etth1.json`; 1 file (`series.npy`, sha256 `32a0ad07…`) re-hashed `match: true` |
| torch312 freeze | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`, 77 lines, Python 3.12.16 | `env_torch312.json`: freeze equal to `sweep2/g1b/env/torch312.freeze.txt`, raw and sorted equal; capture `torch312.freeze.txt` recomputes to the same digest and 77 lines |
| frozen entries | 16 (`pins_gc7rc_etth1.json`/`.txt`) | matches the pinned view with the `data` link present; no contradiction with the 15-entry pre-link value of the older record |
| interpreter | uv CPython 3.12.16, sha256 `23bc148d…`, 31,028,464 B | `c7_final.json:interpreter_evidence` and `host_facts` agree |

## Binding to the handoff

`git show origin/coord/local:reports/20261128-14-g5-etth1-isolation-handoff.md` gives harness
`6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c`, parent `3a06d86721b0c1826b165b68a9781a561e4993f4`, review sha256
`4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`, paper test base `57e6d1ed…` and CPUs 16–31
in `torch312` — all as stated in the record. Recomputation of the review file on `main` returns exactly
`4c721776…`. The record's "source `local/20261128-14-g5-etth1-isolation-handoff` (`coord/local` `150212b1`)"
also matches `origin/coord/local`.

## Non-overclaim

- No G.1b/G.5/G.4 chunk: the only run records are the two synthetic smoke records (`parent.py 5`, budget 5
  steps, nodes `fake_isolated` / `tasl2_gpu_smoke`). No census/chunk/campaign artefact is present.
- No label or evaluation value was read: the data step only re-hashes `series.npy`; `result_channel.txt` carries
  the kit's synthetic fixture (`val_accuracy: 1.0000`, `test_accuracy: 0.4242`), already identified as a fixture
  value in earlier engineering reviews.
- No host deletion, commit or push: `commands.txt` lists only `git rev-parse`/`status`/`merge-base`, the check
  scripts and `taskset`-wrapped helpers; `checkout_end.txt` shows the detached G.5 worktree at the exact pin with
  only the `data` link untracked and an empty stash; `host_facts` `running_jobs=` is empty.
- Scope: TASL-7, HTCondor, Ada and deepthought are not contacted by any captured command; the record is marked
  `ENGINEERING_ONLY` in the status line and the footer.
- No CPU 8–11 evidence is present, but see m1 for the over-broad wording of that claim.

## PASS / minor table

| # | Check | Result |
|---|---|---|
| 1 | record sha256, tip, base and single-commit additions | PASS |
| 2 | `SHA256SUMS` 35/35 verify, rc 0, digest `218005c5…` | PASS |
| 3 | `condition_1_pass`…`condition_7_pass` all true; `stop_items.txt` empty | PASS |
| 4 | pins, env freeze 77 lines/shape, data manifest, GPU UUID/driver/lease times, pytest counts, disk, leftovers, checkout end | PASS |
| 5 | four gate lines exact and correct harness SHA; pin equals handoff and accepted review | PASS |
| 6 | no CPU 8–11 use, no label/eval read, no host deletion/commit/push, ENGINEERING_ONLY | PASS (m1 wording) |
| 7 | captures complete and internally consistent | PASS (m2 wording) |

| Minor | Description | Blocking? |
|---|---|---|
| m1 (inherited, procedural wording) | "No CPUs 8-11 were used: every CPU-bound step was pinned with `taskset -c 16-31`" is broader than the evidence. Only the step 1–4 helper commands in `commands.txt` and the `host_facts` process listing show `taskset -c 16-31`; `phase3_checks.sh` is invoked with no visible `taskset` and the pytest command inside `systemd-run` has none, and no affinity capture exists. Nothing suggests CPUs 8–11 were used and no C1–C7 gate or environment binding is affected, but the absolute sentence is not evidenced by this capture set. This repeats finding m5 of `EXPANSION_HOSTCHECK_REVIEW_20261126`. Qualify the wording (list the pinned steps exactly) or add an affinity capture in a future run. | No |
| m2 (cosmetic) | C7 says "GPU identical before/after (353 MiB, no compute apps, 0 %)". The C7 sample after the smoke is `353 MiB, no compute apps, **5 %**` (`c7_final.json:gpu_after`); memory and the compute-app list are identical. Idle/unleased conclusion is unaffected, but "identical … 0 %" overstates the utilisation sample. | No |

### Observations (no action required)

- **O1 (inherited host constant).** The record's `i9-14900KF` is not printed by this capture set (`host_facts`
  records 32 CPUs, `cpuinfo_max_freq`, microcode `0x133` and uname but no CPU model). It is established by other
  committed records (`TASL2_CPU_STABILITY_20261125.md`, the 20261126 host checks) and is not a gate value.
- **O2 (inspection artefact).** `c7_final.json:data.link.is_symlink` is `false` because the probe inspects the
  node directory, not `data`; `datapins_gc7rc_etth1.json` records `link_present: true` with target
  `/home/dowling/r1_tracks/t1_tasl_x/data/gc7rc_etth1`, and the `git status --untracked-files=all` field shows
  the expected `?? nodes/gc7rc_etth1/data`. The "only the data symlink untracked" claim is supported.
- **O3 (queue state).** The record cites `coord/coordinator` `d47cab43`; that commit is an ancestor of the
  current coordinator tip `ac7fb1a5` (one commit behind), i.e. the queue state at handoff, not a contradiction.
- **O4 (capture order).** `step1_checkout.txt` is stamped 14:50:17Z, after phase3 (14:48:01Z); `commands.txt`
  states the step 1–4 captures were taken after phase3. The pin at run time is independently evidenced by the
  pin fields in `c4_interp.txt`/`c5_smoke.json`/`c6_gpu_smoke.json` and by the C7 end-state check. No
  contradiction, but the step 1–4 captures are end-of-session re-verifications, not pre-run captures.
- **O5 (record digest).** The record does not embed its own sha256; consistent with the sibling records, it says
  Local fills the addendum gate as `host check <record> sha256 <its sha256>`. The digest for that fill is
  `6c2231d50c274a26512c5cc20cfcf97212b764e755e0dc6b948d33fbab3369b7`.

## What remains

1. Coordinator publishes this record (or the reviewed tip) and Local fills the `gc7rc_etth1` addendum gate with
   `host check <record> sha256 6c2231d5…`, then runs the draft checks.
2. Optional only: correct m1/m2 wording at a natural record revision. If the record bytes change, re-hash it and
   have Local fill the new digest; no host re-run is needed.
3. `gc7rc_forestcover` remains blocked on Local's per-node handoff; Titanic and MetaMaze carry their own records
   and reviews.

**AI-assisted: DeepSeek compute agent, 28 Nov 2026. ENGINEERING_ONLY.**
