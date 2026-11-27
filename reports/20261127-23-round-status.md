# Round status — 27 Nov 2026, 13:20 UTC (compute)

`origin/main` `85b2421f`; `origin/coord/coordinator` `dcca5b56` (no card after `compute/20261127-25`); `origin/coord/compute`
before this report `baa00540`. No evidence campaign completed this round, no GPU job of ours is left running, and no label,
evaluation or test partition was read.

The first ready card in the queue is `compute/20261126-10` (expansion G.1b), which is running. Everything else in the
coordinator's Compute queue is done, waiting on a signature, or waiting on a host/lease. The round's work was therefore the
expansion monitor and the capacity/queue check below.

## 1. Running — expansion G.1b (`compute/20261126-10`), 2 of 4 nodes sealed

Note `docs/r1/authorizations/g1b_x_t1_tasl_20261126.md` sha256 `16d31f48…`, spec `sweep2/t1_tasl/g1b_tasl_x_spec.json`
sha256 `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238` (matches the card's `d0dce058…cfd238`).
Run `g1b-x-tasl-20261126-a` on TASL-2; all four are CPU nodes (0 GPU-h; the 40 GPU-h cap is untouched).

| Node | CPU set | State | Runs | Verdict / next |
|---|---|---|---|---|
| `gc7rc_etth1` | 16-31 | **sealed** `2026-11-27T00:37:08Z` | 460/460, 0 divergent | `determinism.deterministic: true`; 5/5 configs same outcome; no divergent config at default |
| `mlgym_metamaze` | 0-3 | **sealed** `2026-11-27T07:05:09Z` | 460/460, 0 divergent | `deterministic: true`; 5/5 configs same outcome; no divergent config at default |
| `gc7rc_forestcover` | 4-7 (pid `106573`) | running | default 10, train 150, split 150, joint **88/150** | no STOP; joint is the last part |
| `mlgym_titanic` | 12-15 (pid `106578`) | running | default 10, train 150, split 150, joint **26/150** | no STOP; joint is the last part |

Integrity of the two sealed attempts (read-only, on TASL-2): `sha256sum -c SHA256SUMS` 2/2 OK for each; both receipts have
`stop: null` and bind the job record and wrapper log —

- `gc7rc_etth1`: job_record `2c50d59acbf1d224ddbc35927318237be2f4ebdaf76ff7d5cb4632092394aca2`,
  node_log `7af07b7b74e13ea1cbcdab498dbe746bd1bc603cd77893070ee08dbdf4368c27`, harness `3a06d867…`,
  projection 1.644 h (1.675 h by record, 16 CPUs).
- `mlgym_metamaze`: job_record `e1bc322996c72d2c57d10c4d0d1dadc7cff17ece5f37ecd1aba01f31dc422073`,
  node_log `cfe2699018152f466823bfd20002b08b47265b181b106cf4bdbdda1386976be8`, harness `aa354485…`,
  projection 7.114 h (7.131 h by record, 4 CPUs).

Rate sample: `gc7rc_forestcover` went 87 → 88 joint runs in ~1.5 min and `mlgym_titanic` 25 → 26 over the same interval;
both were at 71/150 and 12/150 joint at the 12:41 UTC sample (~31 and ~26 joint runs per hour since then), so both are
advancing without a timing or node STOP. At the observed rate the two remaining nodes are hours, not days, from their seals.

**Next step (next round):** on each process exit, run `g1b_tasl.py seal <attempt-1> <spec> --node <node>` (the sealed target
must not exist), then, when all four nodes are sealed, `assemble` one sealed attempt per node and `summarise` with the note's
spec; report the four per-node verdicts and the summary sha256. Nothing will be assembled from a partial set.

## 2. Blocked / waiting (no runnable action this round)

| Item | Why it cannot run now | Unblocked by |
|---|---|---|
| `compute/20261127-05` G.5 P11 host tests | C2, C4, C5, C6, C9, C14, C15 need the signed G.5 note or a purpose-built synthetic smoke spec. The committed spec refuses at validation: `STOP: run_id must be c3_t1_labels_<YYYYMMDD>` (`validate_spec(launch=True)`, `main` `85b2421f`), and it carries PENDING fields. C11's audit-chunk side and C10's hours-long span need TASL-7's card, which another user's process holds now (7.3 GB, 46 %). | The G.5 note; or a task that names an engineering smoke spec; a free TASL-7 card |
| `compute/20261127-15` houseprice CPU-set check | CPUs 0-3 are free now (MetaMaze released them), but 4-7 are held by Forest Cover. The check needs both. | `gc7rc_forestcover` seals |
| `compute/20261127-12` D.3 HTCondor preflight | The pool advertises **0 GPUs** (`condor_status`: 693 slots, no `CUDADeviceName`, 22 machines earlier); no L40S/A100 match. Request unchanged. | A runnable ETP L40S or TOpAS A100 |
| `compute/20261126-09` D.3 per-arm smoke | Revision 4 is frozen and G1/G6 are merged, but no task names the arms and authorization for the smoke. | A task file naming the arm list and authorization |
| `compute/20261126-06` G.5 campaigns | The G.5 note is not published. | The G.5 note |

Correction to the queue wording: the remaining P11 items are not waiting only on the TASL-2 0-7 leases. The note-dependent
items (C2, C4, C5, C6, C9, C14, C15) stay refused at `validate_spec(launch=True)` whatever the lease state; the GPU items
(C10 hours, C11 chunk side) wait on TASL-7's card.

## 3. Capacity (read-only samples, 13:12–13:15 UTC)

- **Ada:** cards 0 and 2 empty (5 MiB); 1, 3, 4, 5 held by another user's process at 33.7 GB each and 6, 7 at 27.0/26.9 GB.
  No job of ours.
- **TASL-2:** expansion pids `106573`/`106578`; GPU free (353 MiB, 0 %); load 8.2; `cpus-0-3` and `cpus-16-31` free,
  `cpus-4-7` and `cpus-12-15` held by the two running nodes.
- **TASL-7:** card held by another user's python (7.3 GB, 46 %); no job of ours; `gpu0.lock` free.
- **deepthought:** load 7.7, 448 GiB available RAM; TITAN X cards 0, 2, 3 idle-ish, card 1 in foreign use (5.7 GB);
  `condor_q` shows no job of ours.
- **ETP pool:** 693 slots, 669 claimed, **0 GPU slots advertised**.

## 4. Decided alone

To keep the round to read-only monitoring and push nothing new: no job was submitted, no request, spec, seed or reviewed file
was edited, no lease was taken from a running node, and no evidence or sealed tree was written. The `validate_spec` refusal
was reproduced on a clean `origin/main` worktree.

## 5. Rows (g) — acknowledged

Free placement and shared-card rules were applied (`compute/20261126-03`): no request was edited to get a slot, no wall-clock
limit decided anything, no other user's process was touched, and this round took no card at all. The capacity sample above
records other users' cards by count and memory only.

## 6. Next round checks

1. `ssh tasl2 'ps -p 106573,106578'`; seal each attempt on exit; when all four nodes are sealed, assemble and summarise and
   report the verdicts and the summary sha256.
2. After `gc7rc_forestcover` seals (4-7 free), rerun the houseprice check (`compute/20261127-15`) into a new capture directory,
   then the TASL-2 P11 items if the G.5 note exists.
3. Re-check `condor_status` for an L40S/A100; do not edit the request.
4. Watch `coord/coordinator` for a card after `-25` (none at this fetch) and for the G.5 note or a screening re-issue.

**Task ids this report covers:** `compute/20261126-10` (monitor), with the state of `compute/20261127-05`, `-15`, `-12`,
`compute/20261126-06`, `-09`. **No deliverable branch this round; no tests ran; no review verdict applies.**
