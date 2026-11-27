# Compute round status — 27 Nov 2026, 22:35 CET (`coord/compute` @ this commit)

Base `origin/main` `1afa7d62ffd98709a100de6e725d123cbc272a73`; queue read at `coord/coordinator` `ac90b07d`.
Worked the STATE order: screening first, then the 34/33/31/32 cards, then the new 36 card.

## Finished this round

| Card | Result | Branch / tip | Review | Published |
|---|---|---|---|---|
| `compute/20261126-10` expansion G.1b | all four nodes 460/460, deterministic; all four join G.5 by addendum; D21 funnel 0/4 (reported, not a selector) | `compute-expansion-g1b-20261127` @ `50fc9cbc` | `compute-expansion-g1b-review-20261127` @ `618ecaf4`, ACCEPTED (`346f079c…`) | merged `cbc86fc5` |
| `compute/20261127-31` G6 smoke audit revert | `audit_seeds` refuses 6301-6302 again; focused 17 passed; full suite base=tip 119/5,032 with identical IDs (`e23e215a…`; reviewer 117/5,034 identical IDs `29557901…`) | `compute-g6-smoke-audit-revert-20261127` @ `345f4c97` | `compute-g6-smoke-audit-revert-review-20261127` @ `6eadf655`, ACCEPTED (`a4d0c926…`) | merged `f43823da` |
| `compute/20261127-29` Ada P5 | **smoke PASS; E0 equivalence STOP** (RPS 25.86 % below TASL-7, tolerance 10 %; slopes pass; R1-E0-HEADFIT recipe change) | `compute-p5-ada-smoke-e0-20261127` @ `28e451ea` | `compute-p5-ada-smoke-e0-review-20261127` @ `be396f10`, ACCEPTED (`fee7a734…`) | **not publishable as a P5 PASS; STOP with the coordinator** |

Reports: `20261127-31-expansion-g1b-result.md`, `20261127-32-screen-cotenancy-blocked.md`,
`20261127-33-g6-smoke-audit-revert.md`, `20261127-34-ada-p5-stop.md`.

## Screening (`compute/20261127-35`) — blocked, no analysis

Eight co-tenancy scenes are kept, all 0 failed: `1550Z` 186, `1822Z` 108, `1837Z` 439, `1840Z` 442,
`1842Z` 223, `1845Z` 440, `2120Z` 365, `2125Z` 444 (latest; manifest `61f3822e…`). A `1816Z` and a `2118Z`
attempt were strict-preflight refusals only (`origin/main` stale; no output). Every started run passed the
launch preflight and then hit the 60 s guard with foreign load around 45 cores (load1 ~52–60 with our 15
workers). No `analysis.json`, no resumed scene.

**Next check:** `ssh deepthought 'uptime'`; retry only when `cpus - 1-min load` is ≥ ~25, with a new
`SMEAS_EVIDENCE_<stamp>`, after `git fetch` in `/work/dwong/screen_measure_20261127/paper_c12136d6` (it goes
stale whenever main moves). The note, code `c12136d6` and cache tree `3843b53c…` are unchanged.

## Blocked / waiting

| Card | What it waits for |
|---|---|
| `compute/20261127-32` G.5 P11 TASL-2 items | **G.5 note/spec**: `python3 sweep2/t1_tasl/g5_tasl.py validate sweep2/t1_tasl/g5_tasl_spec.json --launch` returns `STOP: run_id must be c3_t1_labels_<YYYYMMDD>` at `1afa7d62`. TASL-2/7 cards are idle and CPU sets 0-3/4-7/16-31 free; C2/C4/C5/C6/C9/C11/C14/C15 run as soon as the note and filled spec are published. |
| `compute/20261127-33` houseprice CPU-set | the reviewed run id is date-based and the 27 Nov live/sealed roots already exist; the next unused UTC date is 28 Nov. Next check after `00:00Z`. (No wall-clock rule decides the check; this is an identifier collision.) |
| `compute/20261127-36` D6 expansion copy | a reviewed **expansion variant** of `g5_relcopy.py`: the current step supports only `seven` and `ar` schemas, and the expansion assembly is outside `sealed_g1b`. The local handoff (`reports/20261127-29-g5-expansion-relcopy.md`, `coord/local` @ `a51597b5`) explicitly asks for that schema-aware check. Prepared next round: extend `KINDS` with `x` (`g1b_tasl_x_summary/1`, `g1b_tasl_x_assembly/1`, four nodes, assembly under `/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a`), keep the 7001–7010 STOP and no-overwrite rules, then copy `summary.json`/`ASSEMBLY.json`/`runs.jsonl` and review. |
| `compute/20261127-28` E-INT census | signed census spec/authorization, staged data/tokenizer and smoke; yields to Paper B. |
| `compute/20261127-12` D.3 HTCondor preflight | no batch GPU: `condor_status -af CUDADeviceName` returns 566 × `undefined`; request unchanged. |

## Running elsewhere / capacity

- **No screening or P5 job is live.** The last P5 process ended after writing `e0e`; the Ada card 0 lease was
  released.
- **TASL-2 / TASL-7:** both RTX 4090s idle (0–44 MiB); TASL-2 load 0.16.
- **Ada:** card 0 free at last check; card 2 shows another user's processes (3 GB class); cards 1/3/4/5
  foreign (33 GB class); 6/7 foreign (27 GB class).
- **deepthought:** load fluctuates 6–60; the batch venv and cache are intact; no job of ours is live.
- **Rows (g) acknowledged:** free placement and shared cards were used; no request edited; no wall-clock limit
  decided anything.

## Next-round checks, in order

1. `compute/20261127-35`: fetch the screening checkout, check `uptime`, launch a fresh stamp if there is room;
   on a clean run run `r1.noise.screen_analysis` exactly as the note says, then report per-node verdicts.
2. `compute/20261127-36`: implement + test + review the expansion `relcopy` schema; run the copy on TASL-2 from
   the sealed/assembly source; report path/hash for `summary.json`, `ASSEMBLY.json`, `runs.jsonl`.
3. `compute/20261127-32`: after the G.5 note/spec, run the P11 TASL-2 items; TASL-7 card is free.
4. `compute/20261127-33` houseprice: after 00:00 UTC, run the reviewed command with a new capture dir.
5. P5 STOP: coordinator/author decision on the E0 reference (re-baseline or historical `8e13e77`); then the
   timing carry-forward and the phase-1 note.
