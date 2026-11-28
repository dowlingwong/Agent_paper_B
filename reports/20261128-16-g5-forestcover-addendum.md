# local/20261128-16 — Forest Cover addendum 4

for: coordinator

- Paper base `f532176f3f0241909c9fb8df63a58e6fbefaefbd`. The host-check receipt and independent
  review are published via `942255a3`. This clears the receipt STOP in
  [local/20261128-14](20261128-14-g5-forestcover-publication-stop.md).
- Run `c3_t1_labels_20261128_addendum_4`. Forest Cover is a separate descriptive node under S9.
  The draft binds Gaussian P10, PRE-SPLIT v2, D6, the determinism PASS, and TASL-2 CPU-only
  deployment on CPUs 4–7 in `torch312` at harness `3f7b09febf401a83f3aa881f00eecdd032024416`.
  The signed budget rule gives 767.169 s per proposal. The signed main note supplies K = 10.
- Draft/spec delivery `local-20261128-16-g5-addendum-forestcover` @ `9825ee84a9eb28e20be076a4caffbd4f9d1dbb40`.
  The unsigned spec-only commit `b9268a2a9ad9406b33de03b41804d2c2626df93f` is a direct
  child of the paper pin. Its tree differs by the Forest Cover spec. The delivery adds
  the unsigned note under `docs/`.
- Fresh independent tier-E verdict **ACCEPTED**. Review branch
  `local-20261128-16-g5-forestcover-addendum-review` @ `8507f061d2e5d5cee011a23357ffa48802d1cbed`.
  [Review](https://github.com/dowlingwong/Agent_paper_B/blob/8507f061d2e5d5cee011a23357ffa48802d1cbed/docs/r1/reviews/G5_EXPANSION_ADDENDUM_FORESTCOVER_LAUNCH_REVIEW_20261128.md)
- Focused synthetic addendum tests **36 passed** on Python 3.12.8, pytest 9.2.0. The one-spec tree
  and `git diff --check` passed. The real binder and launch-strength spec validator passed at
  K = 10 with the exact review blob supplied as the sole fixture. The stock command below
  currently exits 2 at review publication. This unit changes a spec and note. The earlier exact
  Forest Cover harness base and tip full suites each recorded 5,071 passed, 156 failed, 3 errors,
  164 skipped and 71 subtests passed, with the same 159 failure/error IDs.
  [Full-suite comparison](20261128-14-g5-forestcover-isolation-handoff.md)

| Object | SHA-256 |
|---|---|
| Addendum spec | `2834327aac53e5172cef3dce4aafd4f646903c0c3f4af7dc86adfbc7551b1a78` |
| Unsigned note with review citation | `7cc89513d42f8d1e6a7cad753e4f6d92cd1c7fedf26dcfd726ca87f27baf1954` |
| Independent review | `b50fbfc491d98e9b304a3cfc5cee6747455a1693255b9fbef41855394a201f9f` |
| Published TASL-2 receipt | `00b84d688d1b167bab1817709919fa7b8c8237ccaff3d60a1245e10a5c27eb12` |
| Published G.1b seal receipt | `2940254a01b7136d76eb2ed310536a7bf92cf5b03b373cffa8408ca285433506` |
| PRE-SPLIT v2 amendment | `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7` |
| Exact harness suite failure/error IDs | `3dc18712e00890e9003c6f9bf934caf6b20238dbec83e36aa779fa53d2a5eeea` |

## Publication STOP and handoff

The coordinator first publishes the review-only branch. After fetching, run the stock draft check against
the exact delivery, then publish the approved note under R1-G5-S9 and R1-STEP-ORDER (2)(a) and run the
strict check.

```sh
python -B sweep2/t1_tasl/g5_tasl.py check-note \
  sweep2/t1_tasl/g5_tasl_addendum_gc7rc_forestcover_20261128.json \
  --note docs/r1/authorizations/c3_t1_labels_20261128_addendum_4.md --draft
```

Local takes the clean-launch-base follow-up once the approved note bytes are on main. The launch base
requires the author's G.5 launch decision and the coordinator's signing and publication disposition
under LB A. Compute checks the ledger, ancestry, strict authorization and leases before a submission.
The isolation capture is `20261128T173716Z`. No campaign job ID is recorded.

Decided alone to follow the published ETTh1 one-spec pattern and the existing pre-pilot planning
formula. The assigned linked Git directory denied writes to `FETCH_HEAD`, so the round used task
worktrees backed by the existing writable nested repository in the assigned workspace. All 16
existing project changes in the linked checkout match historical published `1afa7d62` byte
for byte and were preserved. Local submitted zero jobs and opened zero sealed partitions.

## Round close

After sending both delivery branches and the report, Local fetched main
`4ceb5099b65245f10b4c10eab22c7201325799c9`, queue `3a2bdef8dda5846a736d9179ba50b66954e79969`,
Compute `d48047c7d3041da92cbf170edf8af8ea803e52d3` and Writer
`268f45f0ae196df55215d740c4629871dc212632`. Main advanced by the D.3 pool record only.
Local has no runnable card. Compute's 18:16 UTC sample found zero Paper B jobs running or queued
across TASL-2, TASL-7, Ada and HTCondor. Held IDs `5045947.0`, `5045949.0` and `5045952.0`
belong to Paper A. Writer is idle pending released evidence and the results-table card.
[Compute ledger](https://github.com/dowlingwong/Agent_paper_B/blob/d48047c7/reports/20261128-39-round-status.md) ·
[Writer ledger](https://github.com/dowlingwong/Agent_paper_B/blob/268f45f0/reports/20261128-writer-round-f532176f.md)

| Lane | State and next check |
|---|---|
| Forest Cover `local/20261128-16` | Coordinator publishes the review and checks the unsigned note. After approved publication, Local prepares the clean launch base. |
| Primary G.5 and addenda 1–3 | Author's G.5 launch-base decision and coordinator signing and publication disposition for `2178bc6e`, `88edb84f`, `4ee43037`, and `e9441f03`. No campaign job IDs. [Clean bases](20261128-15-g5-clean-launch-bases.md) · [ETTh1](20261128-15-g5-etth1-clean-launch-base.md) |
| Houseprice `local/20261126-01` and `local/20261127-27` | Closed. Signed three-attempt CPU-set PASS on TASL-2 for `tasl2-cpuset-mlgym_houseprice-20261128`, checkout `paperB_cpuset_20261128T001400Z`. [Reviewed exact rerun handoff](20261127-27-houseprice-two-attempts.md#compute-handoff) · [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/d48047c7/reports/20261128-04-houseprice-cpuset-pass.md) |
| P.4 `local/20261128-13` | P5 timing PASS. P3 awaits the project signature on the exact spec bytes from `befb58c8` with parent `0b465954`. No phase-1 job ID. [P.4 STOP](20261128-13-p4-timing-carry-forward-stop.md) |
| D.3a and HTCondor | Exact P7 engineering runs `d3a-p7-exact-20261128-c` and `-d` are closed. Production waits for manifest, image or environment binding, endpoint-to-card proof, fresh run ID, P10/P11 review and P9. Previous batch job `760158.0` left the queue. Recheck 6 saw `Start=false` on ETP L40S and TOpAS A100, so no replacement ID. Compute follows the new pool cadence in `compute/20261128-21`. |
| Other blocked work | G.5 shared repeat awaits the author disposition. Additional audit hosts await placement and authorization. Paper C CPU work awaits operator pins and authorization, and E-INT needs a signed spec and fitting lease. The gate awaits G.5 labels, train/dev release, consumer and proof checks, arms freeze and explicit test release. |
