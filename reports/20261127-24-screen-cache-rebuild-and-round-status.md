# Report — screening cache rebuild PASS, and round status (`compute/20261127-26`)

`origin/main` `4a9a1f4a`; `origin/coord/coordinator` `d6943f1a`; `coord/compute` before this report `bf57e012`.
No evidence campaign, evidence run, label, evaluation or test partition was started or read this round. No GPU job
of ours is running. One engineering deliverable finished and was independently reviewed; the expansion G.1b is still
running on TASL-2.

## 1. Finished: `compute/20261127-26` — cache rebuild and engineering smoke: PASS

- **Deliverable branch:** `compute-screen-cache-rebuild-20261127`, tip
  `e6aced0f2039d2b0f380fb2a480d82768d1b7e59`; base `origin/main` `4a9a1f4a`.
- **Code:** `c12136d664ae588a2539b76b2602e36742979ce8`, the independently reviewed cache-layout fix
  (`mac-screen-cache-layout-20261127` @ `e9d7f230`), an ancestor of published `main`.
- **Host / environment:** deepthought, evidence venv Python 3.13.15 (scikit-learn 1.8.0, NumPy 2.4.4,
  SciPy 1.17.1, pandas 3.0.3), harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7` clean, 16 workers,
  CPU only.

| Result | Value |
|---|---|
| New cache `tree_sha256` | `3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07` |
| Cache manifest | `1987cc004aba9ead9705788d98cf05720855c5c0977be5c8eb3404f375382c21` |
| Smoke runs | **168 / 168**, `failed_runs=0`, `stop=null`, seed 999, 46.9 s |
| Smoke manifest | `3c6dd543314aa58b0e5dad266c18769f92c881befe8af9dc17e64f955f44d580` |
| `lineage_runs.jsonl` | `0d8221a3ebcc83d5953bc53cb4052a38b1235a91da46127c6d5496caee81e95c` |
| `worker_runtime.jsonl` | `4633b06b663d0f8cd30d7ffea2238e8e75dec1169d613a27f086ff7a32180141` |

The fixed-point layout that the stopped evidence run needed is present:
`openml_breast_w/data_cache/openml/openml.org/data/v1/download/52350/breast-w.arff.gz`, not the old short
`52350.gz`. `data-cache` filled each of the six OpenML nodes once and then made a fresh offline load that left the
tree unchanged. All six per-node trees and the top-level tree were independently recomputed read-only and match the
manifest; all 24 cache files with stored and decompressed hashes are captured in
`captures/cache_file_list.txt`.

The 168 worker-runtime receipts all name the evidence interpreter
`/ceph/dwong/r1_prepare_20261025/venv/bin/python3`, its prefix and package-list sha256
`a089bbf1fc7522a596631f4dd9535a18866336ff18edbbae14932106d94f16d3`; the smoke's 8 design nodes are
`digits_mlp`, `tabular_mlp` and the six OpenML nodes. Cotenancy at start: 40 CPUs, 31.9 free, load1 8.1, `ok: true`.

One *pre-check* STOP is preserved as context, not as a run or a scene: after the coordinator's docs-only
`4a9a1f4a` merge landed, the checkout's `refs/remotes/origin/main` was one commit behind, and the strict
environment gate refused before creating any output directory. After `git fetch`, the same cache and a new output
directory produced the PASS. `captures/precheck_context.txt` records the invocation, log time, both main SHAs and
the observed absence of the output directory; no attempt or run was retried. The old cache and both earlier STOP
scenes are preserved (`captures/preserved_scenes.txt`).

**Tests:** none new (docs-only deliverable, no code change). The reviewed code's tests and full-suite comparison are
the local worker's: 83 screening tests passed; full `r1/tests` base 5,043 / branch 5,044 passes, identical 156
failure/error IDs (local report `20261127-23-screen-cache-layout.md`).

**Independent review:** branch `compute-screen-cache-rebuild-review-20261127`, tip
`ec6c15c57dda9a9bd3b7fd436908f2145c008be7`, review record
`docs/r1/reviews/SCREEN_CACHE_REBUILD_REVIEW_20261127.md` sha256
`01353a65d3e61f1e5f36aac03b2249aeb06ba9f0b1dfe68ebaa779aa49ea4398`; **verdict: ACCEPTED**. No blocking
findings. Residual minors (non-blocking): start-time clone cleanliness rests on a post-run `git status`, and the
preserved-scene statement is a listing/mtime record rather than a content-hash proof.

**What happens next:** the coordinator merges the deliverable and its review. The local worker then prepares the
second re-issue of the screening note with `code_commit=c12136d6`, `data_cache_sha256=3843b53c…` and manifest
`1987cc00…` for the author's signature. No screening run starts before that note is signed, published and its strict
preflight passes. D.3 step (8) stays held under R1-D3-STEP8-HOLD.

## 2. Running: expansion G.1b (`compute/20261126-10`), 2 of 4 nodes sealed

Run `g1b-x-tasl-20261126-a` on TASL-2; all four nodes CPU-only (0 GPU-h of the 40 GPU-h cap). ETTh1 (16-31) and
MetaMaze (0-3) are sealed. At 14:05 UTC:

| Node | CPU set | State | Joint progress |
|---|---|---|---|
| `gc7rc_forestcover` | 4-7 | running, tmux pid `106573` | 111 / 150 joint runs |
| `mlgym_titanic` | 12-15 | running, tmux pid `106578` | 45 / 150 joint runs |

No STOP; both processes were alive and the joint `runs.jsonl` files were advancing. The next round must
`ps -p 106573,106578`; on each exit seal the attempt with
`g1b_tasl.py seal <attempt-1> <spec> --node <node>`, then when all four are sealed `assemble` and `summarise` and
report the four verdicts and summary sha256. Nothing is assembled from a partial set.

## 3. Blocked / waiting (no runnable action this round)

| Item | Why it cannot run now | Unblocked by |
|---|---|---|
| `compute/20261127-15` houseprice CPU-set check | Forest Cover holds CPUs 4-7. CPUs 0-3 are free after MetaMaze. | `gc7rc_forestcover` seals; then run `run_cpuset_check.sh` into a new capture directory. |
| `compute/20261127-05` G.5 P11 host tests | C2, C4, C5, C6, C9, C14, C15 need the signed G.5 note or a purpose-built synthetic smoke spec; the committed spec still refuses at `validate_spec(launch=True)` (`run_id` must be `c3_t1_labels_<YYYYMMDD>`) and carries PENDING fields. C10's hours span and C11's audit-chunk side need a task naming the route. | The G.5 note, or a task naming an engineering smoke spec/route. |
| `compute/20261127-12` D.3 HTCondor preflight | The pool advertises no GPU: 701 slots (677 claimed, 15 unclaimed, 9 Owner), **0 slots with `CUDADeviceName`**; job `760065` is in history with JobStatus 3 and wall time 0.0 (never matched). Request unchanged. | A runnable ETP L40S or TOpAS A100. |
| `compute/20261126-09` D.3 per-arm smoke | No task names the arms and authorization for the smoke. | A task file naming the arm list and authorization. |
| `compute/20261126-06` G.5 campaigns | The G.5 note is not published. | The G.5 note. |
| Ada P.4 4B arms | The 4B OOM disposition is with the author; no task names a rerun. | An author decision / task file. |

**Recurring checks this round:** TASL-7's card is now **free** — 44 MiB used, 0 % utilization, driver 580.178.04, no
compute apps, `gpu0.lock` free (second sample). TASL-2's card is free (353 MiB, 0 %). The ETP pool still has no batch
GPU. Ada was not sampled this round. The G.1b jobs, not a GPU lease, hold the TASL-2 CPU sets.

**Kit c1:** merged long ago (`166db0eb`); it is not next and nothing was re-run for it.

## 4. Decided alone

To use the exact reviewed code commit `c12136d6` (an ancestor of the newer docs-only `main`) rather than the moving
tip; to re-invoke only the preflight after `git fetch`, because it had created no attempt directory and no run had
started; to preserve the pre-check log and the old cache/scenes; and to keep C10/C11 blocked rather than start an
hours-long host test without a task naming its route, even though TASL-7's card became free. Read-only capacity and
pool samples only; no request, spec, note, seed or reviewed file was edited.

## 5. Next-round checks

1. `ssh tasl2 'ps -p 106573,106578'`; seal each attempt on exit; when all four nodes are sealed, `assemble` and
   `summarise`, then report the four per-node verdicts and summary sha256.
2. After `gc7rc_forestcover` seals (CPUs 4-7 free), run the houseprice check into a new capture directory.
3. Re-check `condor_status` for an L40S/A100; do not edit the request.
4. Watch `coord/coordinator` for a card after `-26`, the G.5 note, and any task naming the C10/C11 P11 route.
5. TASL-7 is free if a P11 or G.5 task wants the 4090.

**Task ids covered:** `compute/20261127-26` (delivered, reviewed), `compute/20261126-10` (monitor), with the state of
`compute/20261127-05`, `-15`, `-12`, `compute/20261126-06`, `-09`, `experiment/20261126-02` and
`cluster/20261126-03`.
