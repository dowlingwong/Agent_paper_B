# Compute round status — 28 November 2026, 17:50 UTC

Round base `origin/main` `7cd65cfa`; queue `coord/coordinator` `52fb6892`. At reporting both are unchanged and the
latest compute task card is `compute/20261128-20`. Two units ran: the last expansion addendum host check
(`compute/20261128-20`) and a D.3 pool re-read (`compute/20261128-03`). No Paper B evidence job was started.

## Delivered

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-20` — `gc7rc_forestcover` G.5 host check | **PASS** C1-7 at `3f7b09fe`, CPUs 4-7, torch312; record + 36-file capture set | `compute-g5-expansion-isolation-forestcover-20261128` @ `3a334d528d4be799c049d3748b8fec4c8c01f58b` | `…-review` @ `eb34c563e36f8f55058d49a0cc1a97edeb7e377a`, **ACCEPTED WITH MINORS** |
| `compute/20261128-03` — D.3 HTCondor preflight re-read 5 | **not submitted**: no `Start = true` slot; exact expressions recorded | `compute-d3-preflight-recheck5-20261128` @ `64e3c73b8b62def02cf1dcb11f6b2696a0a09409` | read-only engineering record |

Hashes: Forest Cover record sha256 `00b84d68…`, `SHA256SUMS` sha256 `95fb1af5…`, review file sha256
`42702d3a…`. Recheck 5 record sha256 `37f389bd…`, `SHA256SUMS` sha256 `a5267158…`. Details in report
`20261128-37` (Forest Cover) and the recheck-5 record on its own branch (pool read).

## Running / idle now

- **No Paper B job is running.** TASL-2: RTX 4090 at 353 MiB, 0 %, no compute apps; `gpu0.lock` and the CPU-set
  locks are free; load 0.22 at 17:34Z. TASL-7: RTX 4090 at 44 MiB, 0 %, no compute apps; load 0.00. Both were idle before
  and after the Forest Cover check.
- **Ada** (read-only sample): 8 × RTX 6000 Ada; four cards empty (indices 2, 5, 6, 7 at ~5 MiB), four busy with
  other users' processes; `/data1` 1.9 TB free. No Paper B job on Ada.
- **HTCondor** (`condor_q -submitter dwong` from deepthought2): no queued or running Paper B job. Three held
  Paper A probes `5045947.0`, `5045949.0`, `5045952.0` (JobStatus 5) were not touched.

## D.3 pool re-read (17:42Z, recheck 5)

| Route | GPUs / free | State | `Start` |
|---|---:|---|---|
| `c03-001-175` (TOpAS A100) | 8 / 8 | Unclaimed / Idle | **false** |
| `g4401.nemo.privat` (NEMO2) | 4 / 4 | Claimed / Retiring | **false** |
| `g4401.nemo.privat` (NEMO2) | 4 / 0 | Unclaimed / Idle | false |
| `g4401.nemo.privat` (NEMO2) | 1 / 1 | Unclaimed / Idle and one Drained | false |
| `deepthought2` (ETP L40S) | 2 / 1 | Unclaimed / Idle | **false** |
| `deepthought` (TITAN X) | 4 / 2 | Unclaimed / Idle | false |

NEMO2 advertises GPUs again, but only in a retiring slot with no free GPU or in unstartable/Drained slots. No
request was edited. Record and raw `condor_status` output are in the recheck-5 branch.

## Blocked / pending

| Card | Waits for | Owner | Job id |
|---|---|---|---|
| `compute/20261128-18` G.5 launch | author's **"G.5 启动 A"**; then the coordinator merges `compute-g5-launch-base-20261128` @ `2178bc6e` and compute launches from its tip after `validate --launch` and the strict note check | author → coordinator → compute | none |
| `compute/20261126-06` G.5 campaigns | the G.5 launch decision and the addenda gates (Forest Cover record now delivered) | author/coordinator/local | none |
| `compute/20261128-19` P.4 phase 1 | P3 STOP: no project SSH signing identity on any host; author signs `befb58c8`'s exact bytes. P5 timing is PASS and reviewed | author → local → compute | none |
| D.3 batch proposer preflight (`compute/20261128-03`) | a `Start = true` ETP L40S or TOpAS A100 on the exact request | compute, re-read each round | none |
| D.3a production launch | production launch binding (manifest, environment/image vs §§2/7.2, endpoint-to-card proof), then author P9 | compute/local → author | none |
| `compute/20261127-28` E-INT census | published census authorization and a signed spec; no `docs/r1/authorizations/paperc_eint_census_20261127.md` | author/design → compute | none |
| Paper C 3B fixed-memory census | one approved development task, cap, pin and a fitting host lease | design/author → compute | none |
| Forest Cover addendum fill | record and review publication, then Local fills the gate | local | none |

## Next-round checks, in order

1. Read `origin/coord/coordinator` for the G.5 launch reply or the merge of `compute-g5-launch-base-20261128`;
   launch only from `2178bc6e`, after `validate --launch` and the strict note check.
2. Read `origin/coord/local` for the Forest Cover addendum fill and any new handoff.
3. Re-read `condor_status` for `c03-001-175`, the ETP L40S and NEMO2; submit only on `Start = true`.
4. Check `AUTHOR.md` for the P.3 signature; take the P.4 phase-1 unit if it lands.
5. Read the queue for any card after `20261128-20`; continue with the first ready one.
6. The recurring TASL/Ada host sample continues; no date decides anything.

**Rows (g) acknowledged:** placement was free within the rows; the Forest Cover check used only its named CPU set
and the GPU lease for the 2 s C6 smoke; no request was edited to get a slot; no wall-clock limit decided anything;
no sealed/test/label value was read; no other user's process was touched.

Decided alone: the order (Forest Cover first, then the pool re-read), the corrected-pinning rerun before
publication, keeping the first attempt as non-evidence, and reporting the pool as not startable rather than
editing a request. No signed value, spec, seed or request was changed.
