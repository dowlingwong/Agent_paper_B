# Compute round status — 28 November 2026, 18:20 UTC

Round base `origin/main` `f532176f`; queue `coord/coordinator` `8aec575a`. The latest compute task card is
`compute/20261128-20`; no card after it. `compute/20261128-20` is complete (all four addenda host checks delivered
and reviewed). One read-only task ran this round: the sixth D.3 HTCondor pool read. No Paper B evidence job was
started.

## Delivered

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-03` — D.3 HTCondor preflight, sixth read | **not submitted**: `c03-001-175` (A100) and the ETP L40S both read `Start = false`; exact expressions recorded | `compute-d3-preflight-recheck6-20261128` @ `ce9dfdf906d5d7b9192ac1fbee72a86276c508c4` | read-only engineering record; no review required (same as rechecks 3–5) |
| `compute/20261128-20` — G.5 expansion host checks | **complete**: C1–7 PASS for Titanic, MetaMaze, ETTh1, Forest Cover at each node's exact harness SHA | four earlier branches, unchanged | all four **ACCEPTED WITH MINORS** (documentation only) |

Hashes (recheck 6): record sha256 `60a3748fd243001c3b7600dbfb23c16fbafdca5f63d73961ed63aa354a5c067c`,
`SHA256SUMS` sha256 `c3d11a47e96b66ccf1a4139f85e558bac99e72af91b0996b48658206d4181d70`, raw read
`5fd756fe7b757e3d0d8befe7aa65ba4139d9a5dc3863b80bec485c1902ad294e`. Tests: docs-only, no `r1/tests` unit
changed; `git diff --check` clean and `shasum -a 256 -c SHA256SUMS` OK. Full details in the record:
`docs/r1/reports/d3_preflight_20261128_recheck6/D3_HTCONDOR_PREFLIGHT_RECHECK6_20261128.md`.

## D.3 pool read (18:16:04Z, sixth)

| Route | GPUs / slot GPUs | CPUs | State / Activity | `Start` |
|---|---:|---:|---|---|
| `c03-001-175` (TOpAS A100) | 8 / 8 | 176 | Unclaimed / Idle | **false** |
| `c03-001-175` dynamic slot | 8 / 0 | 16 | Claimed / Busy | false |
| `g4401.nemo.privat` (NEMO2) | 4 / 4 | 48 | Unclaimed / Idle | **false** |
| `g4401.nemo.privat` (NEMO2) | 4 / 4 | 16 | Claimed / Retiring | **false** |
| `deepthought2` (ETP L40S) | 2 / 1 | 32 | Unclaimed / Idle | **false** |
| `deepthought` (TITAN X) | 4 / 2 | 10 | Unclaimed / Idle | false |

TOpAS now advertises `c03-001-175` as one 8-GPU / 176-CPU partitionable slot, but its machine policy still reads
`Requirements = false` and `WithinResourceLimits = error`. No request was edited; no job ID was created. The ETP
queue holds only the three Paper A probes `5045947.0`, `5045949.0`, `5045952.0` (`JobStatus 5`); TOpAS holds no
`dwong` job.

## Running / idle now

- **No Paper B job is running.** TASL-2: RTX 4090 at 353 MiB, 0 %, no compute apps, load 0.08 at 18:16Z; no
  `gpu0.lock` or CPU-set lock held. TASL-7: RTX 4090 at 44 MiB, 0 %, no compute apps (only the idle `ollama serve`
  daemon), load 0.08. Both cards were idle before and after the pool read.
- **Ada** (read-only): 8 × RTX 6000 Ada 48 GB; cards 5, 6, 7 empty (~5 MiB), card 2 at 18.7 GiB used / 0 %, cards
  0, 1, 3, 4 busy with other users' processes; `/data1` 1.9 TB free; load 16. No Paper B job on Ada.
- **deepthought**: load 0.41, 457 GiB available RAM; `/work` 904 GB free, `/ceph` 332 TB free.
  **deepthought2**: load 14.69 (other users), 909 GiB available RAM; same shared file systems.

## Blocked / pending

| Card | Waits for | Owner | Job id |
|---|---|---|---|
| `compute/20261128-18` G.5 launch | author's **"G.5 启动 A"**; then the coordinator merges `compute-g5-launch-base-20261128` @ `2178bc6e` and compute launches from its tip after `validate --launch` and the strict note check | author → coordinator → compute | none |
| `compute/20261126-06` G.5 campaigns | the G.5 launch decision and the addenda gates | author/coordinator/local | none |
| `compute/20261128-19` P.4 phase 1 | P3 STOP: no project SSH signing identity on any host; the author signs `befb58c8`'s exact bytes. P5 timing PASS and reviewed | author → local → compute | none |
| D.3 batch proposer preflight (`compute/20261128-03`) | a `Start = true` ETP L40S or TOpAS A100 on the exact request | compute, re-read each round | none |
| D.3a production launch | production launch binding (manifest, environment/image vs §§2/7.2, endpoint-to-card proof), then author P9 | compute/local → author | none |
| `compute/20261127-28` E-INT census | published census authorization and a signed spec; no `docs/r1/authorizations/paperc_eint_census_20261127.md` | author/design → compute | none |
| Paper C 3B fixed-memory census | one approved development task, cap, pin and a fitting host lease | design/author → compute | none |
| G.5 expansion addenda | coordinator publication of the four host records and local's addendum bindings | coordinator/local | none |

## Next-round checks, in order

1. Read `origin/coord/coordinator` and `AUTHOR.md` for the G.5 launch reply or the merge of
   `compute-g5-launch-base-20261128`; launch only from `2178bc6e`, after `validate --launch` and the strict note
   check.
2. Read `AUTHOR.md` for the P.4 P3 signature; take the phase-1 unit if it lands.
3. Re-read `condor_status` for `c03-001-175`, the ETP L40S and NEMO2; submit only on `Start = true`.
4. Read the queue for any card after `20261128-20`; continue with the first ready one.
5. Keep the recurring TASL/Ada host sample; no date decides anything.

**Rows (g) acknowledged:** placement was free within the rows; the pool read is read-only and created no request;
no request was edited to get a slot; no wall-clock limit decided anything; no sealed/test/label value was read; no
other user's process was touched.

Decided alone: to run the recurring pool read and the host sample only, since the two evidence cards remain blocked
at author decisions, and to report the TOpAS slot as not startable rather than editing a request. No signed value,
spec, seed or request was changed.
