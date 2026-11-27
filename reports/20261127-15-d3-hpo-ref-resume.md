# local/20261127-15 — HPO-REF CPU runner and G6 terminal audit

for: coordinator

- Published base `91cfd48a67f8d62d4e20826976cbdbdbcfcaf505`. Delivery `mac-d3-hpo-ref-resume-20261127` @ `b57131b5fca9b428989dc2a804a8a7a9f5d20f15`. Reviewed code `ff7961b4eafad116aa83865a4569362c107703a2`. Resumes and supersedes the implementation STOP from `local/20261126-05` item 3, candidate `666320c9`.
- The CPU runner hashes exact rendered editable files with G1's function, insists the start match G1, and seals the G6 snapshots, keep records and charged runs. G6 uses the shared seed cache and the same approved OpenML cache hash. G7 builds the outcome row from the final, curve and keep audits.
- SMAC3 is `smac==2.4.0` with `ConfigSpace==1.2.2`, `scikit-learn==1.6.1` and the exact transitive distribution pins in `r1/c3/d3_hpo_ref.py::SMAC_PINS`. The check reads installed distribution metadata. Each retry receives fresh worker and optimizer directories. A missing incumbent stops before a summary. The version pin fills revision 4 §5.8.
- **Independent tier E ACCEPTED** at `ff7961b4`. The initial review reproduced an ignored OpenML cache and mischarged host-loss and runtime-error cases. The re-check verified cache staging over tracked placeholders for climate and sonar, STOP on unknown runtime errors and infrastructure retry on exit 137 through real LocalWorker synthetic subprocesses. Review `docs/r1/reviews/D3_HPO_REF_RESUME_REVIEW_20261127.md`.
- Focused tests passed 135/135 locally and 95/95 independently with real pinned SMAC3 on synthetic inputs and harness `9bb416805175149eb87b71f28d77530572aa4bce`. The independent initial-design check used all seven nodes × 18 seeds and round-tripped 630 rendered configurations including exact start hashes. No live host, evidence run, worker training job, sealed input or test partition was used.

## Full suite and hashes

Serial full `r1/tests` runs used Python 3.12.8, NumPy 2.4.4, pytest 9.2.0, torch 2.15.0, harness `9bb41680`, fresh `TMPDIR` values and no LightGBM. Command `python -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.

| Checkout | Passed | Failed | Errors | Skipped | Subtests passed |
|---|---:|---:|---:|---:|---:|
| Base `91cfd48a` | 4,937 | 115 | 3 | 160 | 71 |
| Deliverable `b57131b5` | 4,968 | 115 | 3 | 161 | 71 |

**Zero new failures or errors.** The 118 sorted `FAILED` and `ERROR` IDs match exactly. SHA-256 `1326e6adc3ada56e23add49153325c24f6c95d22a5b6f8536d663214d51f9fd2`. The full-suite comparator environment uses scikit-learn 1.9.1 and skips the optimizer test. The separate pinned real-backend run includes and passes that test.

| Artifact | SHA-256 |
|---|---|
| SMAC3 and RS core `r1/c3/d3_hpo_ref.py` | `70016dd198b0328108897cda84b3ea2cc244a9b13c4d59a9332181901307d194` |
| CPU worker and audit adapter `r1/c3/d3/hpo_runner.py` | `bf317eec0125d236a463108219ee34cee82e3554658b6aa521df34ee2aeb1bbe` |
| G6 audit `r1/c3/d3/audit.py` | `452724ec92b9820ddfb187f2ea4999f3c0bbc6c1241b55f4594b8a4b0cd5a4a3` |
| Worker audit adapter `r1/c3/audit.py` | `0830e85e0da324b5e2bf5b41f2c19e744f30de1406ea59e2f7ec82573e8dab8c` |
| Independent review | `aecad064536bee96d4e090225804c5c2dadb82a6f3ed05c1db2a0eaf05a8ae1f` |
| Revision 4 draft with this field | `0567e2107ccda1b3aae833b73c5cbc47889d24af0d918bc3cc2724c1023ebce0` |

## Handoff

- Coordinator publication closes the SMAC3 version field in revision 4. The document still follows its complete step-(5) review, screening disposition and freeze sequence.
- The future signed HPO-REF stage launcher calls `r1.c3.d3.hpo_runner.run_cpu_campaign` with the matched G1 start SHA-256, approved worker interpreter and the approved OpenML cache root and tree digest for OpenML nodes. The launcher admits the worker environment and CPU host, and enforces the pooled worker-failure STOP at stage assembly. The optimizer environment is independently pinned and has no implicit choice of the benchmark worker interpreter.
- For the terminal and kept-incumbent audits the launcher calls `audit_cpu_campaign` on the sealed campaign, with the declared deepthought §7.2 worker metadata, the same verified data-cache binding, and the shared G6 per-seed cache. It applies the stage's placement and co-tenancy rules before this call. Use the full `g7_audit.json` and `outcome_row.json` only after the complete stage has passed its checks.
- The synthetic backend logged two non-fatal NumPy warnings from SMAC3's debug timing mean on an empty vector and ConfigSpace deprecation warnings. The diagnostic timing mean is outside the optimizer result. The live Linux environment and approved data caches remain preflight responsibilities of the future stage launcher.

Decided alone: select the tested SMAC3 2.4.0 distribution closure with scikit-learn 1.6.1. SMAC3 2.4.0's import failed against the desk's scikit-learn 1.9.1. Preserve fresh attempt trees and pass an independent benchmark interpreter, then reuse G6 and G8 for audit and worker-failure rules.

## Round state

Queue `fb16b178`, published main `91cfd48a`, latest Compute receipt `db2f5195`. The local queue has no further runnable card. The assigned linked worktree is clean. The sandbox makes its shared Git metadata read-only, so the task branches and exact test snapshots use temporary Git metadata.

- The coordinator is testing the merge of accepted gate-output branch `796c43a4` from `local/20261127-14`. HPO-REF awaits coordinator publication. D.3 revision 4 still needs the screening signature and disposition, remaining freeze fields and complete independent review. G5 labels, train/dev release, arms freeze and the single offline gate read follow the signed order.
- Expansion G.1b `g1b-x-tasl-20261126-a` on TASL-2 was last sampled at 05:36 UTC. ETTh1 is sealed. MetaMaze PID `106579` on CPUs 0–3, Forest Cover `106573` on 4–7 and Titanic `106578` on 12–15 were still running. Check per-node completion, seals, assembly and determinism.
- Houseprice fix `local/20261126-01` is merged at `47df6f55`. Once MetaMaze and Forest Cover have both sealed, `compute/20261127-15` checks the leases and reruns from a fresh capture using the exact reviewed `for: compute` handoff in `reports/20261126-01-cpuset-fix.md`. The previous waiter timed out without creating a run root. The remaining TASL-2 P11 engineering checks wait on the same leases and precede G.5 publication. Final render also needs `paper.commit` and tier-E review.
- Ada's host configuration is published and the synthetic probe is ready under `compute/20261127-19`. The Compute branch has no probe job ID yet. The separate H200 request `760065` was last recorded Idle. D.3 preflight jobs `760148`, `760149` and `760152` were removed. Check for an eligible ETP L40S or TOpAS A100 match. TASL-7's GPU lease was free at the last Compute sample.
- Expansion addenda await the final G.5 binding, published node receipts and the split amendment. Paper C consolidation awaits the author's historical PLAN-row confirmation. The extra G.5 audit hosts and shared-card repeat mechanism await their recorded binding and authority decisions.

No compute job was submitted in this round.
