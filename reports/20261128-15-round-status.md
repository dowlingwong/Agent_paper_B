# Compute round status — 28 November 2026, 03:00 UTC

Round base `origin/main` `474c998d`; queue read at `coord/coordinator` `2076c0a7`. **No Paper B job is
running anywhere, and no card was runnable this round.** All host reads below are read-only.

## Checked, not runnable

| Card | Finding | Waits for |
|---|---|---|
| `compute/20261128-09` G.5 P11 matrix | The repair is reviewed and accepted (`local-20261128-p11-host-repair` @ `2f110e26`, review `fd3099ed…`) but is **not on `main`**. The coordinator's share of the repo already holds merge branch `coord-merge-p11r` @ `7254fa7e` (repair merge `b37453d2`), unpublished. Running the matrix from an unpublished merge would not be the run its card names. | publication to `main` and the reissued matrix card |
| `compute/20261128-03` / `-12` D.3 HTCondor preflight | `c03-001-175` advertises **8 free A100-PCIE-40GB** (Unclaimed/Idle) but the partitionable slot still says `Start = false`, `Requirements = false`, `WithinResourceLimits = error`; the ETP L40S on `deepthought2` advertises 1 free GPU with `Start = false`. This is the same pool expression as the 01:32Z record (`reports/20261128-11`), now re-read at 02:55Z. Nothing submitted; no request edited. | a slot whose `Start = true` |
| `compute/20261127-05` / `-08` / `-32` G.5 P11 host tests | Everything left is a campaign-path item and needs the same repaired kit step-line and close CLIs as the matrix. | the P11 repair on `main` |
| `compute/20261126-07` P.4 phase 1 / A5 SFT | E0 criterion still with the author (`sheets/P4_E0_CRITERION_SHEET_20261128.md`); the phase-1 note follows it. | author decision |
| `compute/20261127-28` E-INT census | No signed census spec/authorization; no ClimbMix data or tokenizer staged on Ada (`/data1` has no `data_manifest.json` or `shard_06542.parquet`). Staging needs the design's path/budget and the note. | author/design |
| `compute/20261126-06` G.5 campaigns | G.5 note not published; P11 coverage and final render first. | coordinator/local |
| D.3 pre-declared smoke (`openml_climate`, 6301–6302) | Named as next in `STATE.md`, but no card gives the launch commit, the arm set or which GPU model(s) will serve D.3; the frozen pre-declaration requires the smoke on each such model. Not started under R1-HOST-FREE without that routing. | a coordinator card |

## Hosts at 02:55–02:56Z

| Host | State |
|---|---|
| TASL-2 | RTX 4090 353 MiB / 0 % (display only); all CPU-set and GPU locks free; no Paper B process |
| TASL-7 | RTX 4090 44 MiB / 0 %; `gpu0.lock` free; `tianyu` has sessions but no GPU compute; no Paper B process |
| Ada | cards 0 and 2 empty (5 MiB); cards 1, 3, 4, 5, 6, 7 held by other users (pids 3952132, 1467xxx, 3303xxx); all our leases free |
| deepthought | 447 GiB available, load 6.88 on 40 CPUs, no Paper B job |
| deepthought2 | 939 GiB available, load 7.04 on 128 CPUs, no Paper B job (screening finished) |

## Active jobs and leases

- `760158.0` (`dwong`, R2 sparse-sk project, `slot1_4@c03-001-179`, 4 CPUs / 32 GB) is running. It is **not a
  Paper B job** and was not touched. The submitter `dwong` has no queued job; pool-wide, all users have 137
  running and 12,275 idle jobs (slots are a separate count).
- No GPU model beyond A100/V100S/L40S/TITAN X is advertised. **No H200 or H100 is back.** The ETP collector's GPU
  ads are the two TITAN X on `deepthought` and the one L40S on `deepthought2`; TOpAS shows V100S (`c03-001-159`),
  A100 (`c03-001-167` 0 free, `c03-001-175` 8 free but not startable, `c03-001-179` 0 free).
- The stale probes `759624`/`759625` stay removed and `760065` withdrawn (`reports/20261128-01`).

## Next-round checks, in order

1. Read `origin/main` for the P11 repair merge. If it is published **and** `compute/20261128-09` is reissued, run
   the matrix on TASL-2 and TASL-7 from that published commit, with a fresh shared UTC stamp and fresh IDs, after
   the lease check; then a fresh review of the item-by-item record.
2. Re-read `c03-001-175` and the `deepthought2` L40S `Start` expressions; submit only on `Start = true`.
3. Take the author's E0 criterion (then the phase-1 note) and the census spec; keep the D.3 smoke pending its card.
4. Keep the G.5 note track waiting on P11 coverage and the render; no label job starts before publication.

## What this round decided alone

No job was launched and nothing was changed: the P11 matrix was held at its publication boundary, the D.3 preflight
was not submitted because its slots are not startable, and the census was not prepared past the missing signature.
Host/card placement was not needed.

Rows (g) acknowledged (`compute/20261126-03`): work is placed by fit under R1-HOST-FREE, a card may be shared under
R1-CARD-SHARE, no request was edited to get a slot, and no wall-clock limit decided anything. No sealed or test
partition was read.
