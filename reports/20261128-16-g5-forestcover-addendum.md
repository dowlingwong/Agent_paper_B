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
