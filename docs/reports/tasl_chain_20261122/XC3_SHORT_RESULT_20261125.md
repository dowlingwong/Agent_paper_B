# XC3 short cross-check of the four G.1b TASL-2 nodes on TASL-7 — PASS on all four (26 November 2026)

**Result: PASS on all four nodes.** The four default-part jobs (`mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_fmnist`,
`mlgym_houseprice`) ran on TASL-7 under the signed short cross-check note, were sealed, copied byte-identically to
TASL-2, and compared with each node's sealed G.1b TASL-2 attempt by `g1b_crosscheck.py compare --mode short`:
**all four verdicts are PASS** — every default and default_repeat outcome of c0–c4 is present and bit-identical
across the hosts, both sides are deterministic. No author STOP occurred, no infrastructure STOP, no attempt-2.
GPU-h consumed: **0.180** of the 2.0 cap (projection 1.039, sensitivity 1.184). ENGINEERING_ONLY; no label,
evaluation or sweep-2 file was read. AI-assisted (DeepSeek Harness agent `xc3-runner`, delegated by the lead).

Orchestration: the lead tasked the xc3-runner agent; the four verdict files and this memo are committed on the new
branch `xc3-short-verdicts-20261126` off published `main` `f1f1b651` and pushed to `origin` (no push to `main`;
the branch awaits the independent review the note's `publication` line requires before merge). Nothing was deleted;
all checkouts and archives are kept.

## 1. Authority and inputs (all verified before any job)

- **Note:** `docs/r1/authorizations/g1b_xc_short_t1_tasl_20261126.md`, sha256
  `02f1d8db430aa97b091ce2ff7c4b793ea548b90bae02512fdf23440477aa95f7`, read byte-identically from published
  `origin/main` `f1f1b6511983b03a5632429ef62c0db0856f649c`; `approved: true`, `label: ENGINEERING_ONLY`,
  `labels_read: none`. It carries the author's three bound choices — **`xc3_fail: A`, `xc3_cap: R1-G1B-CAP`,
  `skip_nodes: none`** — and binds `run_id: g1b-tasl-20261121-b-xc3-a`,
  `paper_commit: 59fbd7d3ad08774aa300153c487cd9001f9d0e29`,
  `xc_spec_sha256: fc064ded2a79fa974194340cc2309ed4948dfc949335521c10ad77d55c56854c`,
  `g1b_spec_sha256: 7ff3c95b963a2f1690461ca58dc98bec7ad79e31ccbbe159c57004716a8cc5f7`,
  `harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702`.
- **PLAN row `R1-XC3-FAIL-READING` is on `main` and records option A** ("The xc3 note carries xc3_fail: A."), so
  strict `check_xc_note` accepts the note. The launch rows `R1-T1-HOST-TASL`, `R1-TRACKG-G3-EARLY`, `R1-G1B-CAP`,
  `R1-G1B-EDITS`, `R1-G1B-TIMEOUT`, `R1-T1-TASL-ENV`, `R1-G1B-TASL-DECISIONS`, `R1-G5-AUDIT-TWO-CARDS` are all on
  `main`.
- **Launch table:** `docs/r1/reports/tasl_chain_20261122/XC3_LAUNCH_TABLE.md` — launch commit
  `6f4e2ba1ed6cc85c61f1eecdae08ed40db8c6a42`, whose parent is the paper commit `59fbd7d3`; spec sha256
  `fc064ded…` (verified against the spec file at the launch commit). The launch commit is an ancestor of
  `origin/main` `f1f1b651` (verified before and during the run); `main` did not move during the run.
- **Spec:** `sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json` sha256 `fc064ded…` (schema
  `g1b_tasl_crosscheck_short_spec/1`); `validate` PASS on both hosts (`ok: true`, run id, four nodes,
  projection 1.039 GPU-h ≤ 2.0).
- **Host-check records on `main`:** TASL-2 `681011b2…` and TASL-7 `09945c15…`, as the G.1b spec declares; both
  parsed as PASS for the harness pin.
- **Launch binding `verify_launch_tasl` PASS on both hosts:** `BINDING_OK` — `paper_commit 59fbd7d3`,
  `head 6f4e2ba1`, `main f1f1b651`, spec path. The four derived TASL-7 specs validate.
- **Checkouts:** `paper_xc3` cloned from `origin`, detached at `6f4e2ba1`, `origin/main` freshly fetched, tracked
  tree clean, with the signed note copied byte-identically into `docs/r1/authorizations/` (sha `02f1d8db…`).
  Host roots are `/home/dowling/r1_tracks/t1_tasl`; harness on both hosts at `c025f89a…`.

## 2. Prerequisites (a)–(e)

| # | requirement | result |
|---|---|---|
| (a) | `train.csv` copied from TASL-2 to `/home/dowling/r1_inputs/house-prices/train.csv` on TASL-7, byte-identically | **PASS**: sha256 `1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41`, **460,676 bytes**, md5 `80ccab65fb115cbad143dbbd2bcd5577` — identical on TASL-2 and TASL-7 |
| (b) | TASL-7 harness at `c025f89a`, clean | **PASS**: `HEAD c025f89a…`, `git status --porcelain` shows only the allowed `nodes/<node>/data` links (pre-run: `mlab_cifar10`, `mlgym_cifar10`; post-run adds the four job nodes, still data links only) |
| (c) | Hugging Face hub and OGB reachable from TASL-7 | **PASS**: `https://huggingface.co` 200, `https://ogb.stanford.edu` 200; all three ML data setups (`mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_fmnist`) and the houseprice CSV setup succeeded inside their jobs (`out/setup.log`, part rc 0, 10/10 rows, no chunk stop — the engine's data-manifest check passed against the G.1b spec's value) |
| (d) | signed note + XC3-FAIL PLAN row on `main`, launch commit merged | **PASS**: note and row on `main` `f1f1b651`; launch commit ancestor; strict `check-xc-note` PASS on both hosts |
| (e) | `lscpu` + torch312 BLAS/threadpool config on both hosts | **PASS**: captured before the comparisons (hashes §8). TASL-7: AMD Ryzen 9 7900X 12-Core (24 threads), RTX 4090 driver 580.178.04, GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`; TASL-2: Intel Core i9-14900KF, 32 CPUs. The CPU-only node crossed AMD↔Intel and still matched bit-identically (§4) |

## 3. The four TASL-7 jobs

Command per node, inside its delegated scope, from the `paper_xc3` checkout, with `G1B_TASL_ENABLE_REAL=1` and
`T1_TASL_ORCHESTRATOR_PYTHON=<torch312 python>`, after a fresh `git fetch origin main`:

```
bash <checkout>/sweep2/t1_tasl/t1_tasl_node.sh xc <checkout>/sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json \
     <node> <checkout>/docs/r1/authorizations/g1b_xc_short_t1_tasl_20261126.md TASL-7 --enable
```

On rc 0 each attempt was sealed with `g1b_tasl.py seal <runs>/g1b-tasl-20261121-b-xc3-a-TASL-7/<node>/attempt-1
<runs>/…/_specs/<node>.json --node <node>`. Run ids: `g1b-tasl-20261121-b-xc3-a-TASL-7`.

| node | attempt | job start–end (UTC) | wall s | rows written/success/divergent | c0 median wall s | 4090/Ada ratio | max wall s | deadline s |
|---|---|---|---|---|---|---|---|---|
| `mlab_imdb` | 1 | 01:32:30–01:39:21 | 411 | 10/10/0 | 36.279 | 0.5656 | 36.414 | 92116 |
| `mlab_ogbn_arxiv` | 1 | 01:39:23–01:41:01 | 98 | 10/10/0 | 4.199 | 0.7431 | 20.404 | 11399 |
| `mlgym_fmnist` | 1 | 01:41:04–01:43:23 | 139 | 10/10/0 | 12.387 | 0.3603 | 13.743 | 51039 |
| `mlgym_houseprice` (CPU, cpus 8-15) | 1 | 01:43:26–01:44:14 | 48 | 10/10/0 | 4.524 | 0.8942 | 5.686 | 10582 |

All four: `stop: null`, `stop_class: null`, `label: ENGINEERING_ONLY`, harness `c025f89a…`, default part only
(10 rows = (4 edits + 1) × 2 conditions), determinism true on both conditions, no `_refusals/` directory. The three
GPU jobs held the exclusive lease `~/r1_locks/gpu0.lock` for their duration (`record.lease`), the CPU-only
houseprice held none and ran on cpus 8-15. GPU: `NVIDIA GeForce RTX 4090`, 24,564 MiB, driver 580.178.04, UUID
`GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`.

Derived-spec sha256 (equal to each record's `spec_sha256`) and sealed hashes:

| node | derived spec sha256 | job_record.json | out.tar | SHA256SUMS | SEAL_RECEIPT.json |
|---|---|---|---|---|---|
| `mlab_imdb` | `3a5dd2d81a0c61a1…` | `a7105c54b7d5b750…` | `1fa7be3cd41a3b22…` | `e60c9899a5856eee…` | `18b488df2c23cded…` |
| `mlab_ogbn_arxiv` | `7cb1e20295305b0a…` | `d1b4ccff9ed277c9…` | `8cf68530e824ba8f…` | `119d4fefd9216ff7…` | `eae5234af9153903…` |
| `mlgym_fmnist` | `acfa25dba71d0425…` | `31540a9e8ef6c765…` | `419b0f692aee2276…` | `b3ad32ccb1b65733…` | `02cf352593eb03a8…` |
| `mlgym_houseprice` | `b28cb5b692d91ff8…` | `d598d9b4891700f3…` | `29768909a11bc234…` | `4bbd54a306378d0c…` | `a89b346ac9c519a9…` |

Full hashes are in `<capture>/TASL-7/jobs/<node>.sha256.txt`; the sealed directories (`out.tar`, `job_record.json`,
`SHA256SUMS`, `SEAL_RECEIPT.json`, `node.log`) and the derived specs are in the capture set. `sha256sum -c` passes on
every sealed copy.

## 4. Transfer and comparison

**Transfer.** The four sealed TASL-7 attempts were packed as a tar (`sha256
eabdd7f5c249414e831fb087d80fee3f97d2b42b441637b5ca2e60ac956d14eb`) and copied byte-identically to TASL-2 at
`/home/dowling/r1_tracks/t1_tasl/captures/xc3_20261126/peer_TASL-7/<node>/attempt-1` (the §7 path). The tar hash
matches on both ends; on arrival each copy `sha256sum -c`s against its own `SHA256SUMS`, and the copied
`job_record.json`/`out.tar`/`SEAL_RECEIPT.json` hashes equal the TASL-7 originals (capture
`TASL-2/peer_transfer_check.txt`, `TASL-2/peer_TASL-7/peer_sha256.txt`).

**Comparison.** Four `compare --mode short` runs on TASL-2 (the host holding the sealed G.1b attempts), from the
`paper_xc3` checkout (`HEAD 6f4e2ba1`, `origin/main f1f1b651`), each TASL-7 attempt-1 against its declared sealed
G.1b TASL-2 attempt — attempt-1 for `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_houseprice`, **attempt-3** for
`mlgym_fmnist`:

```
python sweep2/t1_tasl/g1b_crosscheck.py compare <spec> --mode short --node <node> \
    --a <peer_TASL-7>/<node>/attempt-1 --b <sealed_g1b>/g1b-tasl-20261121-b/<node>/attempt-<1|3> \
    --out docs/r1/reports/tasl_chain_20261122/G1B_XC3_SHORT_VERDICT_<node>_20261125.json
```

| node | TASL-2 attempt | compare rc | verdict | reason | rows identical | both deterministic | verdict sha256 |
|---|---|---|---|---|---|---|---|
| `mlab_imdb` | 1 | 0 | **PASS** | null | 10/10 | yes | `9cce90640315f5de…` |
| `mlab_ogbn_arxiv` | 1 | 0 | **PASS** | null | 10/10 | yes | `b42e485ce259b5c9…` |
| `mlgym_fmnist` | 3 | 0 | **PASS** | null | 10/10 | yes | `cb2ac690825e0928…` |
| `mlgym_houseprice` | 1 | 0 | **PASS** | null | 10/10 | yes | `6c7da4409966ff5e…` |

Exit codes 0 = PASS (3 = STOP, 2 = refusal; neither occurred). Each verdict: `schema
g1b_tasl_crosscheck_verdict/1`, `mode short`, `rule R1-G5-AUDIT-TWO-CARDS`,
`crosscheck_run_id g1b-tasl-20261121-b-xc3-a`, `g1b_run_id g1b-tasl-20261121-b`, `g1b_spec_sha256 7ff3c95b…`,
`harness_commit c025f89a…`, `complete: true`, `verdict: PASS`, `reason: null`, `on_stop: null`; the TASL-2 side
binds job-record sha256 `4468021a…` / `45583b27…` / `5476148a…` / `15b7beea…` (the spec's pins) and the declared
attempt.

**PASS criterion (unchanged, the reviewed one).** Every default and default_repeat outcome of c0–c4 is present on
both sides and identical (`g1b_lib._outcome`: the metric bit-identical when ok, the same failure when failed), and
both sides are deterministic. TASL-7 reproduces each node's G.1b default part bit-identically. This is not a new
noise floor and changes nothing in any node's G.1b record.

| node | c0 | c1 | c2 | c3 | c4 |
|---|---|---|---|---|---|
| `mlab_imdb` | 0.9028 | 0.9072 | 0.902 | 0.902 | 0.8716 |
| `mlab_ogbn_arxiv` | 0.295077 | 0.400416 | 0.526729 | 0.076278 | 0.69556 |
| `mlgym_fmnist` | 0.858333 | 0.8745 | 0.923 | 0.9025 | 0.76 |
| `mlgym_houseprice` | 30638.050688 | 29579.254351 | 27539.225477 | 26160.532374 | 25822.622077 |

(`mlgym_houseprice` is CPU-only: its metrics are bit-identical across TASL-7's AMD Ryzen 9 7900X and TASL-2's
Intel Core i9-14900KF, the mismatch §8/§12 of the prep doc flagged as most plausible did not occur.)

## 5. Cap and GPU-h (decision XC3-CAP)

- Projection checked by `validate`: **1.039 GPU-h** (estimate ratio 1.0), **1.184 GPU-h** at sensitivity 1.5,
  2.112 CPU core-hours, 40 runs in all; cap `caps.max_gpu_hours = 2.0`; `within_cap: true`.
- `short_cap_gate` ran before each GPU job in `launch_xc`; no refusal.
- **Consumed by the run's three GPU attempts (job records): `mlab_imdb` 0.1142, `mlab_ogbn_arxiv` 0.0272,
  `mlgym_fmnist` 0.0386 — total 0.180 GPU-h**, well within the 2.0 GPU-h cap. `mlgym_houseprice` used no GPU
  (CPU-only, no lease).
- Budget counted against `xc3_cap: R1-G1B-CAP` as signed (G.1b's 100 GPU-h; recorded consumption before this run
  ≈ 43.2 GPU-h of 100 by the note's accounting).

## 6. What PASS means, and what was not done

- **PASS** means TASL-7 reproduces that node's G.1b default part bit-identically under the reviewed criterion, so
  under **R1-G5-AUDIT-TWO-CARDS** that node's G.5 audit chunks may run on TASL-7. It is not a new noise floor.
- No STOP verdict, no refusal, no `incomplete`/`nondeterministic`/`cross_host_mismatch`; nothing is re-measured on
  TASL-2; the nodes' G.1b records are unchanged.
- **Not run:** no TASL-2 job (by design — the TASL-2 side is the sealed G.1b attempt), no G.1b/G.5/G.4 job, no
  Track P work, no attempt-2 (no retry was needed or made), no `assemble`/`summarise`, no deletion. `paper_xc3`
  checkouts and all old attempts/archives are kept.

## 7. Host end state

- **TASL-7** (01:47:58Z): idle; no compute app on the RTX 4090; GPU lease `~/r1_locks/gpu0.lock` free (0 bytes, no
  holder); harness `c025f89a` with only the six allowed `nodes/<node>/data` links untracked; disk 468 GiB free.
- **TASL-2** (01:48:16Z): idle; no `noise_floor`/`g1b`/`t1_tasl` process of the user; disk 345 GiB free.
- New host paths only: `paper_xc3/` (both hosts), `runs/g1b-tasl-20261121-b-xc3-a-TASL-7/`,
  `sealed_g1b/g1b-tasl-20261121-b-xc3-a-TASL-7/`, `captures/xc3_20261126/` (both hosts). Nothing overwritten or
  deleted.

## 8. Verdict status and publication

- The four verdict files are committed byte-identically to the `compare` outputs at the spec's fixed paths, with
  `captured_verdict_<node>.json` copies in the capture set (no other file under `docs/r1/reports/` is named
  `G1B_XC3_SHORT_VERDICT_*`). A pre-merge `short_verdict_status` validation against the pushed branch reports
  **PASS** for all four (capture `inputs/verdict_status_branch.log`).
- The canonical `g1b_crosscheck.py verdict-status <spec>` reads `origin/main`. Until this branch is reviewed and
  **merged to `main`**, it correctly reports **PENDING** for the four nodes (`tasl7_audits: false`); after the merge
  it reports PASS. Nothing was pushed to `main` here; the verdicts are not canonical until the merge.
- Per the note's `publication` line and the prep doc §10 item 8, the branch (verdicts + memo + captures) awaits the
  independent review before merge. **`g1b_crosscheck.py verdict-status`** is the G.5 audit-host gate reader.

## 9. Captures

`docs/r1/reports/tasl_chain_20261122/XC3_SHORT_RESULT_20261125_captures/` with a `SHA256SUMS` over every payload
file:

- `inputs/` — signed note, spec, launch table (md + json), prep doc, `validate.log` and `check_xc_note.log` from
  both hosts, `verify_launch_binding.log` from both hosts, the driver/collect/compare scripts, the prereq-(a)
  `train.csv` hashes, `cap_and_decisions.json`, `verdict_status.txt` (canonical, PENDING pre-merge),
  `verdict_status_branch.log` (pre-merge validation of the committed bytes: PASS x4).
- `TASL-7/` — `lscpu.txt`, `threadpool.txt`, `gpu_pre.txt`, `trees_pre.txt`, `clone.log`, `jobs/` (status, per-node
  wrapper output and node seal output, fetch logs, `records/` job records, `specs/` derived specs, `sealed/`
  sealed attempt copies, per-node `sha256.txt`, `records_summary.json`, `cap_and_decisions.json`),
  `postrun_state.txt`, `postrun_state2.txt`.
- `TASL-2/` — `lscpu.txt`, `threadpool.txt`, `trees_pre.txt`, `clone.log`, `validate.log`, `check_xc_note.log`,
  `verify_launch_binding.log`, `tasl2_attempts_verify.txt` (the four sealed G.1b attempts verified against the
  spec's pins), `peer_transfer_check.txt`, `peer_receipts.sha256`, `attempts/`, `peer_TASL-7/` (the transferred
  copies + `peer_sha256.txt`), `postcompare_state.txt`.
- `verdicts/` — `captured_verdict_<node>.json` byte-identical copies of the four committed verdicts.

Host-side evidence remains on both hosts under `/home/dowling/r1_tracks/t1_tasl/`.

## 10. Reproduce

1. On both hosts: clone `origin`, fetch `origin/main`, `git checkout --detach 6f4e2ba1`; copy
   `docs/r1/authorizations/g1b_xc_short_t1_tasl_20261126.md` byte-identically from `origin/main`;
   `g1b_crosscheck.py validate <spec>` and strict `check-xc-note`.
2. TASL-7: the prereq-(a) CSV copy, the (b)-(e) checks, then the four `t1_tasl_node.sh xc` jobs sequentially, each
   after `git fetch origin main`, sealing each rc-0 attempt with `g1b_tasl.py seal`.
3. Transfer the four sealed attempts to TASL-2 at `captures/xc3_20261126/peer_TASL-7/` and verify `SHA256SUMS`.
4. TASL-2: four `compare --mode short` runs writing the verdict paths, then commit the verdicts + this memo +
   captures on a branch off `origin/main`, push, and merge to `main` only after independent review.
