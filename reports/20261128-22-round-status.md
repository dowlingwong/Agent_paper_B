# Compute round status — 28 November 2026, 07:30 UTC

Round base `origin/main` `b70cfa01` for the P7 work, queue read at `coord/coordinator` `70f8298b`
(which also added `compute/20261128-13` and `-14`). No Paper B job is running anywhere.

## Delivered this round

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-11` item 1 / `-13` — D.3a P7 layout | **ACCEPTED**: single measured model RTX 4090 on TASL-2; Ada not ready (no readable GGUF, no `llama-server`, harness `897d83c8` ≠ `9bb41680`); TASL-7 excluded (P11 target, foreign process) | `compute-d3a-p7-20261128` @ `77e54010`, merged `main` `980c6666` | coordinator accepted in `compute/20261128-13` |
| `compute/20261128-11` item 2 / `-14` — D.3a P7 smoke | **PASS**: 14/14 campaigns; 271 charged trials, 238 successful, **33 failures = 12.18 %** (limit 12.99 %); 4 prechecks, 77 skips; 1 admitted ParserError; whole job pinned to CPUs 16–31; 0.59 GPU-h; projection 38.3/42.5 GPU-h | `compute-d3a-p7-20261128` @ `3c12db25` (substantive tip `b730ee9b`) | `compute-d3a-p7-20261128-review` @ `b86e8966`: **ACCEPTED** (R2 `191f96b8…`; R3 diff re-check clean `351de7f6…`) |

The P7 record and its full capture tree are on the deliverable branch; `captures/SHA256SUMS` binds
916 entries (`af84ce0d…`) and all 28 inner manifests verify. The first attempt (server-only pin) is
disclosed as not the receipt; it reproduced the same 33/271 and the trial-071 ParserError.

## Hosts and jobs at 07:19–07:26Z

| Host | State |
|---|---|
| TASL-2 | idle after the P7 smoke; RTX 4090 353 MiB display, 23,830 MiB free; no Paper B process; all leases free |
| TASL-7 | **busy again**: at 07:19Z the card was empty (44 MiB), at 07:26Z another user's compute process held 8,402 MiB (15,563 MiB free); no Paper B process; `gpu0.lock` free |
| Ada | card 2 empty; cards 0,1,3–7 held by other users; no Paper B job |
| deepthought / deepthought2 | idle; no `dwong` Paper B job |
| HTCondor | no startable L40S/A100; TOpAS `c03-001-175` not advertised at the 05:50Z read; no `dwong` job |

## Blocked / pending

| Card | Waits for | Owner |
|---|---|---|
| `compute/20261128-12` item 1 — P11 four TASL-7 scenarios (`-determinism`, `-restart`, `-tar`, `-closeserver`) | an empty TASL-7 card; the 07:19Z window closed before setup, 07:26Z foreign 8.4 GiB | compute, re-read each round |
| `compute/20261128-03` D.3 batch preflight | a `Start=true` ETP L40S/TOpAS A100; re-read each round | compute |
| `compute/20261126-06` G.5 campaigns | published G.5 note (P11 coverage + final render) | coordinator / local |
| `compute/20261126-07` P.4 phase 1 / A5 SFT | author's E0 criterion; phase-1 note | author / coordinator |
| `compute/20261127-28` E-INT census | signed census spec, staged data, a free Ada card; yields to Paper B | author / design |
| `compute/20261126-11` survey redaction | fix already on `compute-resource-survey-20261126` @ `58e6bbeb`; coordinator merge | coordinator |
| `compute/20261127-03` P11 evidence table / copy verdict | P11 complete | compute |

## Next round, in order

1. Check the review branch for the diff re-check of `3c12db25`; if clean, the coordinator can
   publish the P7 record and cite it for D.3a P7.
2. Re-read TASL-7 each round. If the card is empty, run the four P11 scenarios from the clean
   `f7dc4945` checkout with a fresh shared stamp and IDs, append to the P11 record, regenerate
   `SHA256SUMS`, then request one fresh review of the complete item table.
3. Re-read the HTCondor pool (TOpAS `c03-001-175`, ETP L40S); submit only on `Start=true`.
4. No G.5 campaign starts before the published note; no D.3 campaign before the D.3a note.

**Rows (g) acknowledged:** free placement and the card/CPU-set leases were used, no request was
edited to get a slot, no wall-clock limit decided anything, and no sealed/test/label value was read.

Decided alone: the P7 single-model placement, the audit-matching package set as a disclosed
engineering shim, the whole-job 16–31 CPU set, the P7 rerun after attempt A, and stopping no work
when TASL-7 was reclaimed. No host state or other user's process was touched.
