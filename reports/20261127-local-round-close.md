# Local round close — 27 November 2026

Queue checked at `coord/coordinator` `cc3109a2`, published main `bad59593`, and last compute report
`coord/compute` `372d2099`. No runnable local card remains at this queue tip. No compute job was submitted in this
round. The final code publication belongs to the coordinator.

## Delivered and reviewed

| Task | Candidate or publication | Disposition |
|---|---|---|
| `local/20261126-01` houseprice CPU set | `5f1aead0`, merged `47df6f55` | Reviewed three-attempt procedure with signed criterion preserved. Exact `for: compute` command in `20261126-01-cpuset-fix.md`. |
| `local/20261127-05` ARFF by content | `cb684870`, merged `03a352d9` | Accepted; fresh-cache repeat to `compute/20261127-14`. |
| `local/20261127-06` G2 fitter | `6cf882b0`, merged `03a352d9` | Accepted; constants artifact run is `compute/20261127-17`. |
| `local/20261127-07` verify-seed | harness `9bb41680`, checker `e44d966f` merged `e153df24` | Accepted; 160 disjoint seeds checked. New harness for D.3 G1 adapter follows `compute/20261127-16`. |
| `local/20261126-05` item 5 Paper C | `2d0df77a` | Accepted candidate; author confirmation of the historical PLAN rows' basis remains pending. |
| `local/20261127-09` G.5 assembly and render | assembly `82a22977`, draft `bc968b3e` | Assembly accepted with unchanged full-suite failure IDs; draft accepted for conditional handoff. P10 PASS. |
| `local/20261127-09` consumers and `local/20261127-03` S9 unit 1 | consumer `681f15d7`, exact integrated `f5e3827b` | Accepted. Full integrated suite compared with `e153df24`: 4,867 to 4,931 passed and the same 79 failing/error IDs. Exact bindings in the two task reports. |
| `local/20261126-12` addendum template | `4fe8ac1f`, merged `bad59593` | Accepted as a draft template. The switch and filled per-node authorization remain pending. |
| `local/20261127-08` draft prep and `local/20261127-10` review record | `ba7d69df` | Pin-only acceptance recorded and pushed. Complete freeze still pending. |

## Other jobs and next dependencies

- **Expansion G.1b `g1b-x-tasl-20261126-a`**. Latest report has ETTh1 finished and sealed, MetaMaze PID `106579`
  on CPUs 0–3, Forest Cover PID `106573` on 4–7 and Titanic PID `106578` on 12–15 running. Next is their seals,
  assembly and per-node determinism summaries under `compute/20261126-10`.
- **Houseprice waiter**. The last attempt timed out waiting for both CPU-set leases without a run root. Rerun under
  `compute/20261127-15` with a fresh capture after MetaMaze and Forest Cover seal, using the accepted exact command.
- **P.4**. Last reported HTCondor job `760065` is Idle. Ada's reviewed venv is on main; `compute/20261127-13` owns
  the reviewed host-config fill and separate probe. The preflight `compute/20261127-12` and screening smoke
  `compute/20261127-14` await compute receipts.
- **G.5**. The main note needs combined P11 and the final `paper.commit`, draft/strict checks and independent final
  review. P11's remaining host checks and addendum's exact published node evidence are in their reports. The switch
  uses the final launch-code binding with separate 1GC outputs. T1 SFT, arms and gate remain gated by the exact
  preregistration amendments and signed release order.
- **D.3**. `local/20261127-08` must get the accepted G2 artifact/SHA from `compute/20261127-17`, the pinned
  SMAC3 environment after G1/G6, and the exact §7.5(e) gate-report path/key. HPO-REF also needs the G1/G6 interfaces
  and per-attempt output dirs. Per-arm smoke still waits on its implementation and release prerequisites.
- **Audit hosts and card-sharing monitor**. The extra audit-host unit stays parked pending shared-card/bind/host
  authority. The repeat-list and the G.5 monitor follow the author decision recorded in the rows-(g) report.

All status statements on live compute refer to the latest published receipts. The original local checkout is clean.
