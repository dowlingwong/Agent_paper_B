# Local round close — screening cache STOP and D.3 hold

for: coordinator

Local is idle after checking all local task cards and handoffs. Published main
`9cd5863cc1e0855c045fc1090841832cc5b7614c`, coordinator queue
`6bda21b2e03783ea2ebe21bc43659b83e99f14c6`, and Compute receipts
`977953e27d51c13f7c8906c520dde760c53df0be`. The assigned checkout is clean at
`cb684870f939eec3a32b499a11a6bcce44d4dd57`. This supersedes the job states in
[the preceding local round close](20261127-local-round-screen-reissue-d3.md).

## Completed local work checked against main

- **`local/20261126-01`** — base `54082a05`, delivered branch
  `mac-cpuset-repeats-20261126` @ `5f1aead043fd2dba7a82403b61bfa798b113b528`,
  merged `47df6f55`. Independent re-check **ACCEPTED**. Full suite at base and tested
  tip `0c1a9b7f`: 3,918 and 3,924 passes respectively, 179 failures and 26 collection
  errors each, with identical failure/error IDs. Verified the list's SHA-256
  `1c21757ae349800dca867b1a08e5a5e7c3301de4021e75b7448421b2afac70f2`.
  [The exact `for: compute` rerun](20261126-01-cpuset-fix.md) keeps signed S14:
  three sealed attempts on TASL-2 CPUs 0–7, bit-identical to the sealed G.1b reference,
  at most 9.486 s per run. Compute owns `compute/20261127-15`.
- **`local/20261127-21`** — `mac-screen-note-reissue-20261127` @
  `2c471ef83a61a04e2264ba61badfabae67b070be`, published `b2f94c29`.
  Independent review **ACCEPTED**, 82 exact-code synthetic tests passed.
  Re-issued note SHA-256 `7c3c8313e90016fa1ff6773bd678e95e5c6ed9457b14d01631897499ee0fdeb0`.
  The first run under that note STOPped as recorded below.
- **`local/20261127-22`** — `mac-d3-r4-step5-third-20261127` @
  `0c691ce8fea74f0d86361d40c0c11315f0103aee`, merged `7bd78959`. Full step (5) and
  binding-only diff **ACCEPTED**, with seven synthetic production-path replays
  and 181 focused tests plus 18 subtests on the local run. Review SHA-256
  `459c5bc4dbc332c18bf6b2e3eb860b4db63ff85cbb216eabaac074a975048a30`.
  The coordinator records that revision 4 was frozen before screening disposition.
  Published declaration SHA-256 `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745`.
  Step (8) remains held pending author disposition. Actual retry counts and proposer
  GPU seconds also need reviewed sources before evidence authorization.

## Pending work and recorded jobs

| Item | Recorded state and next check |
|---|---|
| Screening `compute/20261127-25` | **STOP** in `SMEAS_EVIDENCE_20261127T1155Z` at 30/10,164 written runs, at `openml_breast_w c3` seed 3301. Strict preflight passed. `fetch_openml` materialized another ARFF cache path, tripping integrity. Compute's STOP branch `compute-screen-measure-reissue-stop-20261127` @ `2d7f1e9c065b4cd421a43d02f1e6ba549abf829c`. Coordinator routes the cache binding and D.3 screening disposition for author decision. |
| Expansion G.1b `compute/20261126-10` | **Running in the latest recorded sample (11:40 UTC)** under `g1b-x-tasl-20261126-a`. TASL-2 Forest Cover PID `106573` on CPUs 4–7 and Titanic PID `106578` on CPUs 12–15. ETTh1 and MetaMaze are sealed. Check exits, seals and published per-node determinism. |
| Houseprice and P11 | The houseprice waiter exited before creating a run root. Verify PID `106573` and leases 0–3/4–7 before the Compute rerun. TASL-7 P11 is accepted. `compute/20261127-05/-08` still need the TASL-2 checks and coordinator resolution of the pre-run spec/note sequence. |
| G.5 local `local/20261126-08` and `local/20261127-09` | The final render waits for combined P11, then the exact final `paper.commit`, draft check and independent tier-E review. The S9 switch (`local/20261126-12`, `local/20261127-03` unit 2) waits for the shared launch-code binding. Real addenda also require the published split amendment and per-node G.1b determinism PASS. Shared-card repeats and extra audit hosts await their recorded decisions. |
| P.4 `compute/20261127-24` | Ada 4B re-probe `trackp-p4-probe-20261127-b` is dispatched. No receipt for a start yet. Check the submission ledger and Ada lease. Prior H200 job `760065` was removed with zero wall time. |
| D.3 HTCondor `compute/20261127-12` | Idle, no eligible match in the latest receipt. Jobs `760148`, `760149`, `760152` were removed. `759624` and `759625` are unrelated. Compute checks the reviewed GPU request. Per-arm smoke remains held. |
| Paper C `local/20261127-19/-20` | The reviewed CPU drafts and E-INT desk preparation are merged. CPU work needs author launch decisions and operator pins. E-INT needs its signed development smoke and an eligible GPU after Paper B's critical work. |

Decided alone: report the cache STOP and dependent D.3 hold from the published receipts.
Checked ancestry, delivery branch tips, SHA-256 bindings and the clean assigned checkout.
This round is a status reconciliation and has no new test run or review verdict. Writable temporary
Git metadata was used for fetch and reporting. Local submitted no jobs and opened no sealed data.
