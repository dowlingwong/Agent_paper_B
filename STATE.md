# State — 27 Nov 2026, 00:20 CET, `main` at `47df6f55`

Coordinator: Claude Code session ca57c183, tmux `paperb-coordinator`, Remote Control "Paper B Coordinator". The recurring
round runs at :07 and :37. Work order: §2 of the next-phase runbook (the author's local version, read 26 Nov 23:10). Execution
authority: the signed PLAN on `main` and the signed notes. `HANDOVER.md` is the interim coordinator's view of 20:30Z.

**On `main` since the handover:** `95249de3` rows (f)(g) (one compute agent, free placement, shared cards, TIMEOUT A, no
dates); `b7e8a6aa` build source of the v2.2 image; `ef06a65c` **R1-G5-SIGNATURE** (G.5 signed, S1–S14 as recommended, S6 =
2027-12-31, S4 = acceptance line; the coordinator publishes the note once its records, render and review exist);
`54082a05` the ancestor–descendant screening test with its re-check review; `47df6f55` houseprice CPU-set fix (local/20261126-01); `166db0eb` **kit c1 record, seven-node REL-T1-G1B
copy, and the published expansion note `g1b_x_t1_tasl_20261126.md`** (strict check PASS, four gates PASS).

**Workers (23:22 CET, seen in their tmux panes):** Local (`paperb-local`) is working, on the houseprice CPU-set evidence (item 1).
Writer (`paperb-writer`) is working. **Compute is up** since 23:31 and delivered three reports by 23:41 (`coord/compute` @ `01df4594`). Local's report: `coord/local` @
`779ca615`. The writer pushed `writer-20261126-01-manuscript-restructure` and `writer-20261126-03-claim-table-sheet` (no report yet).

## Compute (DeepSeek; holds the former cluster and experiment cards, R1-AGENT-COMPUTE)

| # | Card | Runbook | State |
|---|---|---|---|
| 1 | `compute/20261126-10`: launch the four expansion nodes from `7d0279d8` with the published note | §2 2B | ready (note on `main` `166db0eb`). **At 23:52 the pane showed compute on `cluster/20261126-01` (torch tests); no launch report yet.** Check next round |
| 2 | `compute/20261127-01` (= `experiment/20261126-03`): houseprice CPU-set check on TASL-2 | §2 2B | next: ready (fix on `main` `47df6f55`); waits on the 0-3/4-7 leases while the expansion runs |
| 2b | `compute/20261126-11`: redact other users' names in the survey | §4 | ready, small |
| 3 | `cluster/20261126-01`: torch tests of the P.4 host-config fill | §4 P.4 | ready |
| 4 | `cluster/20261126-02` with `compute/20261126-02`: D.3 G1 runner and G6 audit, launcher outside HTCondor (design revision first) | §2 2A | ready |
| 5 | `experiment/20261126-02` and `cluster/20261126-03`: TASL-7 second sample; pool watch with a second Ada sample | §4 | recurring |
| 6 | `compute/20261126-03`: acknowledge rows (g) | — | with the next report |
| done | kit c1 record (`experiment/20261126-01`, `compute/20261126-04`); REL-T1-G1B copy (`compute/20261126-05`); survey (`compute/20261126-01`; Ada: LLM serving ready, P.4 training not ready: no torch env, no container runtime) | | merged `166db0eb` (survey: after item 2) |
| — | `compute/20261126-06`: G.5 campaigns on the TASL pair | §2 2B | blocked: G.5 note published (coordinator), after `local/20261126-08` render and review (local) |
| — | `compute/20261126-07`: P.4 probe on Ada | §2 2B, §4 | blocked: `local/20261126-06` unit 1 on `main` (local) **and** a torch environment on Ada (the survey: a venv from the P.4 lock without sudo, or a container runtime from the host owner); the route goes to the author if a venv is not acceptable |
| — | `compute/20261126-08`: screening smoke repeat | §2 2A | blocked: `local/20261126-02` on `main` (local) |
| — | `compute/20261126-09`: D.3 per-arm smoke | §2 2A | blocked: item 4 (compute), `local/20261126-05` item 1 and `local/20261126-03` (local) |

## Local (Claude on the Mac)

| # | Card | Runbook | State |
|---|---|---|---|
| done | `local/20261126-01`: houseprice CPU-set procedure fix | §2 2B | merged `47df6f55`; the run is `compute/20261127-01` |
| 2 | `local/20261126-10` → `local/20261126-08` "prepare now" | §2 2B | **done** (report `779ca615`: fills listed; dry run clean; launch blocked only by `run_id`, P10 `tails`, the copy). P10 owner: `local/20261126-14` |
| 3 | `local/20261126-06` unit 1: P.4 direct launch and the Ada host configuration | §2 2B, §4 | ready. The fill hook takes compute's survey when it lands |
| 4 | `local/20261126-02`: screening smoke STOP diagnosis and fix | §2 2A | ready |
| 5 | `local/20261126-03` with `local/20261126-16` (the claim sheet's §6 inputs): D.3 pre-declaration revision 4 | §2 2A | ready |
| 6 | `local/20261126-09`: positive control N1–N4 (N3 blocks its merge) | — | ready, small |
| 7 | `local/20261126-11`: T5 shared-noise correction round | — | ready, small |
| 8 | `local/20261126-07`: rows (g) inventory and the G.5 card monitor | §2 2B | ready |
| 9 | `local/20261126-04`: S9 sheet | §2 2B | ready |
| 10 | `local/20261126-05`: controllers A0R, FIXR3, EGATE, LADDER, G7, G8, G9; test-only unit; HPO reference; D.3c memo; Paper C consolidation | §2 2A, 2C, 3A | ready, in its own order |
| 11 | `local/20261126-06` units 2–3: further G.5 audit hosts; revision 4 under R1-HOST-FREE | §2 2B | ready after unit 1 |
| 12 | `local/20261126-13`: checkout hygiene inventory | §2 0 | ready, last |
| 2b | `local/20261126-15` → `local/20261126-08` final render (P10 inside, `local/20261126-14`) | §2 2B | **ready** (copy on `main` `166db0eb`); next after item 1 |
| — | `local/20261126-12`: G.5 addendum code | §2 2B | blocked: the author's S9 row, after item 9 |

## Writer

| # | Card | Runbook | State |
|---|---|---|---|
| 1 | `writer/20261126-01` with `writer/20261126-02`: restructure after R1-ALIGN-OUTCOME, rows (g) in deviations and methods | §2 1, §3 | **current**: in progress (pane, 23:22) |
| 2 | `writer/20261126-03`: revised outline and claim-to-table sheet | §2 1, §3 | **delivered** (`a9a9f6bb`, review ACCEPT WITH MINOR, corrected). Merges with or after item 1; §6 passed to local (`local/20261126-16`); §5 items go to the author as one sheet |
| — | result tables | §3 item 4 | blocked: released results; none exist |

## Coordinator

- **Expansion note published** (`166db0eb`), from the prepared branch `coord-xnote-prep-20261126` @ `bfbd7af0`. P4 and the four gates are filled PASS; the draft
  `check-note-x` passes and `check_gate_x` passes for all four nodes against `main` `54082a05`. Only P2 waits for the c1 record.
- Waits for a delivery: expansion note publication (after the c1 review); G.5 note (after the copy, render and review); controls-pos
  merge (after `local/20261126-09`); T5 merge (after `local/20261126-11`); P.4 host-config fill merge (after
  `cluster/20261126-01`).
- Not dispatched: §2 order 0 at repository level and order 4 (design and author); 3B (fixed-memory census: no PLAN row for the
  census or for the design role, see `AUTHOR.md`).

**Departure from the runbook (recorded, not changed):** §2 says the local worker implements runner changes. The existing card
`cluster/20261126-02` gives the D.3 G1/G6 code to the agent that designed it, and R1-AGENT-COMPUTE passes that card to compute.
The card stands. Implementation and review stay with different agents.

**Unmerged branches:** `p4-hostconfig-fill-20261126` (waits for the torch tests); `mac-controls-pos-20261123` (re-check
accepted, waits for N3); `mac-t5-shared-20261122` (accept with minor, waits for its correction round);
`p4-staging-20261125` (parked: dates R1-STEP-ORDER withdrew);
`codex/layout-flatten-preview` (R1-LAYOUT-FLATTEN conditions unmet). Review records: `coord-reviews-20261126` @ `5b3379ec`.

**Open STOPs:** houseprice TASL-2 CPU-set (procedure; houseprice only); screening smoke `determinism_unverifiable
openml_breast_w c5 seed 999`; P.4 T4 (`env3` missing in the CPU image); P.4 T6/T1 (no H200; the route is Ada).

**Mac checkout:** uncommitted edits to `README.md`, `canon/README.md`, `canon/agents/coordinator/SOUL.md` and the runbook (§7
"Dispatch and run the queues"). The coordinator follows that §7 at the author's request. It is not on `main`.
