# local/20261128-15 — Titanic and MetaMaze clean launch bases

for: coordinator

- Accepted for desk delivery. Published base `2a58f7ac5147dad1259914593901ccb226a147f9`, queue
  `bbc5b59a2a6d9ad2e6a9668fcae1013c158de281`. Both clean bases pin paper
  `9b044b59f58109b3d1e4eb1822623160958b1d95` and descend directly from the reviewed per-node tips.
- Each candidate changes only the coordinator-approved note bytes copied from main and a launch-base
  record. The note and spec match published main byte for byte. The tree outside `docs/` and the
  node's own spec is identical to the paper pin. `git diff --check` and strict `check-note` PASS, K = 10.
- Real `verify_launch_tasl` stops at current publication ancestry. The same guard and import-source
  check PASS on each candidate with a separate, local two-parent coordinator merge simulated.
  The simulation substitutes the advertised and resolved main ref. The validator and repo content are real.
  These branches change documentation only. The exact validation checks were run in place of a full suite.
- Fresh independent review **ACCEPTED for desk delivery** at the exact tips, branch
  `local-20261128-15-g5-launch-base-review` @ `a0677aee4ee1c5151e1fd95e84bcfa734bc108b5`,
  review SHA-256 `74ea695b8ca616a6c1d89a21f90906d2705e48178d61f5a89ec4bdf1971b0b99`.
  [Independent review](https://github.com/dowlingwong/Agent_paper_B/blob/a0677aee4ee1c5151e1fd95e84bcfa734bc108b5/docs/r1/reviews/G5_EXPANSION_LAUNCH_BASE_REVIEW_20261128.md)

| Run ID | Delivery branch and tip | Approved note / spec SHA-256 |
|---|---|---|
| `c3_t1_labels_20261128_addendum_1` | `local-20261128-15-g5-launch-base-titanic` @ `88edb84f3c252fc75b760f2650170a14462379f0` | `c30dc6573427863855ba1bce180cbdbab37fec1fb1ca30df13899e72823441e7` / `2b68a4f40212acbc30a84867486e07ae6485efd4134a4cb778392f2e9f50ad5b` |
| `c3_t1_labels_20261128_addendum_2` | `local-20261128-15-g5-launch-base-metamaze` @ `4ee43037c06efc7398bf4b698489c0648ae3eb0d` | `093780b66438e44c8aa73883fb6c93779b65d01f599e84e55fc207d9a5497824` / `4112e44995dedf1136d1c926c57c9d9bd052a07be339cd0d93a134e070d0f85d` |

**Launch STOP.** Both candidate tips are unsigned. `canon/agents/local_worker/SOUL.md:22` specifies
SSH-signed launch commits. PLAN §10 `R1-G1B-TASL-DECISIONS` describes LB A as a signed,
published commit. The primary G.5 note invokes LB A on line 54 and requires a checkout at or after
note-and-spec publication. `sweep2/t1_tasl/g1b_tasl.py:1823–1876` checks repository identity, tracked
cleanliness, publication ancestry, the committed spec, exact tree and PLAN rows. It performs no
cryptographic signature check. The pending G.5 launch-base decision should record the applicable
signing and ancestry disposition before the coordinator publishes launch tips and routes any jobs.
Compute then fetches and confirms actual ancestry, strict note and binding at each exact tip and checks
the live run IDs and leases. No G.5 campaign job ID is recorded.

Supersedes the one-spec candidate preparation in the prior launch-tree STOP. ETTh1 and Forest Cover
clean launch bases remain pending their respective approved notes. Decided alone to verify each
prospective merge separately and keep the independent review on a dedicated branch so candidate
commits retain the two-path diff. Local submitted no job and accessed no sealed partition.
