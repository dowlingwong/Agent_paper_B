# Compute round status — 28 November 2026, 18:55 UTC

Round base `origin/main` `c3a48405`; queue `coord/coordinator` `73fc54e2`; compute tip before this
report `d48047c7`. The latest compute card is `compute/20261128-21`; there is no card after it.

## Task and result

**Task `compute/20261128-21` (HTCondor read cadence) and the recurring host sample.** No Paper B
evidence or engineering card is runnable this round. No job was submitted, no job ID was created and
no deliverable branch was opened. `kit c1` and the expansion G.1b are complete (all four nodes
460/460, determinism PASS); the published G.5 note and launch card `compute/20261128-18` exist, but
the launch is blocked at the author's launch-base decision.

The pool read is **not due**: re-check 6 read the pool at `18:16:04Z`, and the new cadence in
`compute/20261128-21` permits the next read at `21:16:04Z`. No record branch was made because the
state is unchanged and the interval has not elapsed.

## Host sample (read-only, 18:49–18:52Z)

| Host | GPU / card | State | Load / memory | Paper B job |
|---|---|---|---|---|
| TASL-2 | RTX 4090, 353 MiB used / 24,564 MiB, 0 % | no compute apps; `gpu0`, `cpus-0-3`, `cpus-4-7` leases all free | load 0.2–0.4; 58 GiB available; `/home` 335 G free | none |
| TASL-7 | RTX 4090, 44 MiB used / 24,564 MiB, 0 % | no compute apps; `gpu0` lease free | load 0.05 | none |
| Ada | 8 × RTX 6000 Ada 48 GB | cards 2, 5, 6, 7 empty (~5 MiB); cards 0, 1, 3, 4 busy with other users' `vla-reasoning` processes | load 13.97; `/data1` 1.9 T free | none |
| deepthought | — | 5 users | load 0.51; 457 GiB available; `/work` 904 G free, `/ceph` 332 T free | none |
| deepthought2 | — | 15 users (other users' load) | load 13.90; 905 GiB available | none |
| HTCondor | — | `condor_q -submitter dwong` holds only Paper A `5045947.0`, `5045949.0`, `5045952.0` (JobStatus 5) | — | none; no Paper B ID |

No other user's process was touched. Both TASL cards were idle before and after the sample.

## Blocked / pending

| Card or line | Waits for | Owner | Job id |
|---|---|---|---|
| `compute/20261128-18` G.5 launch | author's **"G.5 启动 A"**; then the coordinator merges `compute-g5-launch-base-20261128` @ `2178bc6e`, and compute launches from its tip after `validate --launch` and the strict note check | author → coordinator → compute | none |
| `compute/20261126-06` G.5 campaigns | the G.5 launch decision, plus local's addendum launch bases (`local/20261128-17`) | author/coordinator/local | none |
| `compute/20261128-19` P.4 phase 1 | P3 STOP: no project SSH signing identity on any host; the author signs `befb58c8`'s exact bytes. P5 timing PASS and reviewed | author → local → compute | none |
| `compute/20261128-03` D.3 batch preflight | a `Start = true` ETP L40S or TOpAS A100 on the exact request; next read `21:16:04Z` | compute, per cadence | none |
| D.3a production launch binding | the launch manifest, environment/image binding vs §§2/7.2, endpoint-to-card proof, a fresh run ID and P10/P11 at that commit; no compute card yet | coordinator/local → compute | none |
| `compute/20261127-28` E-INT census | the published census authorization and a signed spec; no `docs/r1/authorizations/paperc_eint_census_20261127.md` | author/design → compute | none |
| Paper C 3B fixed-memory census | an approved development task, cap, pin and a fitting host lease | design/author → compute | none |

## Next-round checks, in order

1. Read `AUTHOR.md` for the G.5 launch reply. On **"G.5 启动 A"**, wait for the coordinator's merge
   of `2178bc6e`, then launch `c3_t1_labels_20261128` from its tip after `validate --launch` and the
   strict `check-note`; record launch time and per-node/wave job IDs.
2. Read `AUTHOR.md` for the P.4 P3 signature; take the phase-1 unit if it lands.
3. At or after `21:16:04Z`, read `c03-001-175`, the ETP L40S and NEMO2; submit only on
   `Start = true`; make a record branch only if the state changes.
4. Read the queue for any card after `20261128-21`; check `coord/local` for the addendum launch
   bases. No G.5 campaign starts without the launch decision.
5. Keep the recurring TASL/Ada host sample. No date decides anything.

**Rows (g) acknowledged:** placement is free within the rows; no request was edited to get a slot;
no wall-clock limit decided anything; no sealed, test or label value was read; no other user's
process was touched.

Decided alone: to sample the hosts and not to read the pool before the three-hour cadence elapsed;
to submit nothing and to open no branch, since no ready card exists after `20261128-21`. No signed
value, spec, seed or request was changed.
