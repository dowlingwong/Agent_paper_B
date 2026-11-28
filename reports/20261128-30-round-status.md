# Compute round status — 28 November 2026, 13:00 UTC

Round base `origin/main` `d6696f29`; queue read at `coord/coordinator` `52e60856` and re-read after each unit.
Two units this round: the G.5 launch blocker with a clean launch base, and the fourth D.3 HTCondor preflight
read. No evidence job was submitted; no job id is open for compute.

## Delivered

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-18` — G.5 launch | **STOP at the note's launch binding**: `paper_commit a70c8872` vs `main d5d83198` (9 D.3/test files). Clean docs-only base prepared: note bytes unchanged, spec `7dcc…`, code equals `a70c` outside `docs/`/spec | `compute-g5-launch-base-20261128` @ `2178bc6e` | documentation only; coordinator merge |
| `compute/20261128-03` — D.3 HTCondor preflight | **not submitted**: `c03-001-175` A100 `Start=false`; `deepthought2` L40S advertised again but `Start=false`; no `dwong` job | `compute-d3-preflight-recheck4-20261128` @ `b2fb0539` | documentation only |

The G.5 record is `docs/r1/reports/g5_launch_base_20261128/` (record `0ea2edc5…`), the D.3 record
`docs/r1/reports/d3_preflight_20261128_recheck4/` (record `6b7578c6…`); both carry `SHA256SUMS`.

## Blocked / pending

| Card | Waits for | Owner | Job id |
|---|---|---|---|
| `compute/20261128-18` G.5 launch | coordinator merges `compute-g5-launch-base-20261128`; then launch from its tip `2178bc6e` (not the merge commit) | coordinator → compute | none |
| `compute/20261126-06` G.5 campaigns | the same launch | compute | none |
| `compute/20261128-03` D.3 preflight | a `Start=true` ETP L40S / TOpAS A100 on the exact request | compute, re-read each round | none |
| `compute/20261127-28` E-INT census | published `docs/r1/authorizations/paperc_eint_census_20261127.md` (absent) and a signed spec; Ada card 2 was empty at 12:59:56Z but Paper B has priority | author/design → compute | none |
| P.4 phase-1 note | reviewed timing carry-forward / publication; no compute job | design/local/coordinator | none |
| houseprice CPU-set part of G.5 | the G.5 launch (the CPU-set check itself is PASS and merged) | compute | none |

## Hosts at 12:55–13:00Z

| Host | State |
|---|---|
| TASL-2 | idle; load 0.19; RTX 4090 353 MiB display; no Paper B process; no tmux |
| TASL-7 | idle; load 0.00; RTX 4090 44 MiB; no Paper B process; no tmux |
| Ada | card 2 empty (5 MiB, 49,140 MiB) at 12:59:56Z; cards 0,1,3–7 held by other users; no Paper B process |
| deepthought / deepthought2 | other users' JEPA/Paper A work; no Paper B job; `condor_q` has no `dwong` job |

No active job ID is recorded for this round. The G.5 STOP happened before the runner; nothing was submitted.

## End of round

No runnable compute card is left. The next round checks, in order: (1) the coordinator's merge of
`compute-g5-launch-base-20261128`; (2) `condor_status` for a `Start=true` A100/L40S and the exact request;
(3) publication of the E-INT authorization note and a free Ada card; (4) whether the P.4 phase-1 note needs a
compute unit. The recurring host/pool sample continues.

**Rows (g) acknowledged:** free placement and the card/CPU-set leases were used only for reads; no request was
edited to get a slot; no wall-clock limit decided anything; no sealed/test/label value was read.

Decided alone: the clean launch base and stopping before any job; the D.3 read time and no submission; the
host sample times. No signed value, code, spec or note content changed.
