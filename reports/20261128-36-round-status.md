# Compute round status — 28 November 2026, 15:00 UTC

Round base `origin/main` `9b044b59`; queue `coord/coordinator` `d47cab43`. At reporting, `origin/main` is
`8c062a05` (addenda 1 and 2 published) and the queue is `ac7fb1a5`. One unit ran this round: the remaining
TASL-2 host check for the ETTh1 expansion addendum. The D.3 pool re-read found no startable slot.

## Delivered

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-20` — `gc7rc_etth1` G.5 host check | **PASS** C1-7 at `6fc553df`, CPUs 16-31, torch312; record + captures | `compute-g5-expansion-isolation-etth1-20261128` @ `ea6ab2bc743af7fe15b5678e0fd3983d3e47b90e` | `compute-…-review` @ `21ccbf64`, **ACCEPTED WITH MINORS** |

Record sha256 `6c2231d50c274a26512c5cc20cfcf97212b764e755e0dc6b948d33fbab3369b7`; capture `SHA256SUMS`
`218005c5f4ab2b52f69868df58e6a44ebf7fba667f57ed1c81646aee761a137a`, 35/35 verify; review file sha256
`68f7d4ba1dc51f585a322583398d90b65724a142c675d646648c3571f16d3a6d`. Details in report `20261128-35`.

## Running / idle now

- **No Paper B job is running.** TASL-2 was idle before and after the check (RTX 4090 at 353 MiB, 0 %, no compute
  apps); the GPU and CPU-set leases were free before and after. TASL-7 and Ada were not touched this round.
- HTCondor (`condor_q -submitter dwong` from `deepthought2`): three **held** old Paper A probe jobs
  `5045947.0`, `5045949.0`, `5045952.0` (`/work/dwong/paper_a_phasep/...`, JobStatus 5). They are not Paper B
  pieces and were not touched. No Paper B job is queued or running.

## D.3 HTCondor preflight re-read (14:54-14:55Z)

Read from `deepthought2` (the `deepthought` SSH session hung; no job was submitted from either host):

| Slot | Free GPUs | State / Activity | `Start` | `Requirements` | `WithinResourceLimits` |
|---|---:|---|---|---|---|
| `c03-001-175.gridka.de` (A100) | 8 | Unclaimed / Idle | `false` | `false` | `error` |
| `deepthought2.etp.kit.edu` (ETP L40S) | 1 | Unclaimed / Idle | `false` | `false` | `error` |

No submit: the card says submit only on a startable slot; no request was edited. The last full record remains
`compute/20261128-03` re-check 4 (`reports/20261128-31`).

## Blocked / pending

| Card | Waits for | Owner | Job id |
|---|---|---|---|
| `compute/20261128-18` G.5 launch | author's **"G.5 启动 A"**; then the coordinator merges `compute-g5-launch-base-20261128` @ `2178bc6e` and compute launches from its tip | author → coordinator → compute | none |
| `compute/20261128-20` `gc7rc_forestcover` | Local's per-node handoff (full suite at `3f7b09fe…`, tier E); worktree/run root prepared | local → compute | none |
| `compute/20261128-19` P.4 phase-1 | P3 STOP: no project SSH signing identity on any host; author signs `befb58c8`'s bytes. P5 timing is PASS and reviewed | author → local | none |
| `compute/20261127-28` E-INT census | published census authorization and a signed spec; no `docs/r1/authorizations/paperc_eint_census_20261127.md` | author/design → compute | none |
| D.3 batch proposer preflight (`compute/20261128-03`) | a `Start=true` ETP L40S or TOpAS A100 on the exact request | compute, re-read each round | none |
| `compute/20261126-06` G.5 campaigns | the G.5 launch decision and the addenda gates (ETTh1 record now delivered; Forest Cover pending) | author/coordinator/local | none |

## Next-round checks, in order

1. Read `origin/coord/coordinator` for the G.5 launch reply or the merge of `compute-g5-launch-base-20261128`;
   launch only from `2178bc6e`, after `validate --launch` and the strict note check.
2. Check Local's `coord/local` for the `gc7rc_forestcover` handoff; if present, run the same C1-7 matrix at
   `3f7b09fe` on CPUs 4-7, torch312, then review.
3. Re-read `condor_status` for `c03-001-175` and the ETP L40S; submit only on `Start = true`.
4. Take any new P.4 unit after the author signs P3; keep the census pending its authorization.
5. The recurring TASL/Ada host sample continues; no date decides anything.

**Rows (g) acknowledged:** placement was free within the rows; the ETTh1 check used only its named CPU set and
the GPU lease for the C6 smoke; no request was edited to get a slot; no wall-clock limit decided anything; no
sealed/test/label value was read; no other user's process was touched.

Decided alone: the ETTh1 run order (start as soon as Local's handoff landed), the prepared run root and reviewed
scripts, the additional step 1-4 captures, and reporting the pool as not startable rather than editing a request.
No signed value, spec, seed or request was changed.
