# compute/20261128-12 item 1 — G.5 P11 matrix complete: four scenarios PASS

**Result: the P11 engineering matrix now has every scenario.** On the free TASL-7 card at 08:35–10:08Z the
four previously blocked scenarios ran and PASS: `-determinism` (C2/C4/C5 repeat), `-restart` (C7/C10
controlled restart), `-tar` (C15 real tar failure) and `-closeserver` (C15 abnormal close). The primary
matrix, C9/C15 pre-run seals and the `-infra` STOP 7 were already recorded. No G.5 label, note or evidence
run; ENGINEERING_ONLY throughout.

- Task: `compute/20261128-12` item 1 (closing `compute/20261128-10`), PLAN R1-G5-P11.
- Base code `origin/main` `f7dc4945f63e09d1a7b66207bbbc43f76997aa29`; the deliverable branch descends from
  the partial record branch `compute-g5-p11-matrix-rerun-20261128` @ `f963b1bb`.
- Deliverable branch `compute-g5-p11-matrix-complete-20261128` @
  **`0ce1e664b9ef836f83c7f147bd24334184d896c5`**; record
  `docs/r1/reports/g5_p11_engineering_20261128_rerun/G5_P11_ENGINEERING_RERUN_20261128.md`.
- Review branch `compute-g5-p11-matrix-complete-20261128-review` @ `b186d017e179988416aa3af75b0c2fd5106eb0eb`:
  **ACCEPTED**. Round 1 found 18 ignored logs and an unexplained 08:37 refusal pair; both are closed in the
  re-check (420/420 captures; the 08:37 logs are the first refused campaigns).
- No code changed; no unit test applies to a host record. `SHA256SUMS` at the record root verifies.

## The four scenarios

| Scenario | Result | Key evidence |
|---|---|---|
| `-determinism` | **PASS** | Server 08:35:26–09:57:20Z, span 4,914 s, `/props` 32,768/1 slot. Both nodes: 80 proposals, 40 ran, 40 kept, 0 invalid, 0 infrastructure. Three audit chunks each, all `stop: null`; `same_fixed_seed_outcomes` 200/200/10 and `diffs_recounted 0` in six repeat records; `wave-checks` stops empty. Meter: worker 0.791 GPU-h, proposer 4,914 s. |
| `-restart` | **PASS** | Server-1 09:58:06–09:58:39Z (33 s), `restart-ready` 09:59:11Z, `restart-continue` 10:01:29Z, **STOP 12** at 10:02:40Z class infrastructure, server-2 10:02:19–10:02:46Z (27 s), both probes PASS. Attempt sealed. Meter: worker 0.059 GPU-h, proposer 60 s, 2 registered, no gaps. |
| `-tar` | **PASS** | Real `tar -cf out.tar out` failure; `out/` kept and sealed as `out_clear.tar` with **1,130** files, sha256 `07c6a35dffae71c5c27780c36115b6e4ae43affb17289e59531fca002ce187d9`; server 106 s; meter worker 0.021 GPU-h. |
| `-closeserver` | **PASS** | Server-2 killed (wrapper then child) before an end record; `close-server` wrote `closed: true`, `end_basis: closed_at`, reason `P11 engineering server interruption`, 20 s span; `seal-server` PASS. Server-1 normal seal 21 s. Meter: 41 s, 2 registered, 0 open. |

Coverage: C2, C7 and C15 move to PASS; C10 remains **PARTIAL (multi-day STOP 12)** as R1-G5-P11 allows;
C15's assembly and release parts remain for their first use. C4, C5, C6, C9, C11, C14 and C16 keep their
earlier PASS.

## Hashes

| Object | SHA-256 |
|---|---|
| `-determinism` server record / end / log | `cd71834e…` / `16f51e8d…` / `c21576c6…` |
| `-restart` server-1 / server-2 record | `8b768b1d…` / `e8ed4127…` |
| `-restart` campaign job record / diagnostics / out.tar | `d38acd55…` / `49321120…` / `d694b9d5…` |
| `-tar` `out_clear.tar` | `07c6a35dffae71c5c27780c36115b6e4ae43affb17289e59531fca002ce187d9` |
| `-closeserver` server-1 / server-2 record | `4154b044…` / `967801cc…` |
| `-closeserver` server-2 end / seal | `bed5f477…` / closed true, 20 s |

The record root `SHA256SUMS` binds the whole capture set; the attempt `out.tar` archives stay on the hosts
and are cited by their seal-receipt hashes.

## What happens next

One fresh review of the complete P11 item table. G.5 publication still waits on that review, the local
render and the remaining note checks; the coordinator publishes. No label, test or evaluation value was
read; no tolerance, note, seed, spec or request was changed. All P11 servers are stopped and both TASL cards
are free.

Decided alone: host placement (TASL-2 worker, TASL-7 proposer), the shared stamp and fresh scenario IDs,
stopping the server for the C11 chunk, the `restart-ready`/`restart-continue` timing, the `SIGKILL` order for
the close-server fixture, and stopping each scenario's server after its last job.
