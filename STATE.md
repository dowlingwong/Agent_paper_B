# State — 28 Nov 2026, 01:45 CET, `main` at `adbd7020`

Coordinator: Claude Code session ca57c183, tmux `paperb-coordinator`, Remote Control "Paper B Coordinator". The recurring
round runs at :07 and :37. Work order: §2 of the next-phase runbook (the author's local version, read 26 Nov 23:10). Execution
authority: the signed PLAN on `main` and the signed notes. `HANDOVER.md` is the interim coordinator's view of 20:30Z.

**On `main` since the handover:** `95249de3` rows (f)(g) (one compute agent, free placement, shared cards, TIMEOUT A, no
dates); `b7e8a6aa` build source of the v2.2 image; `ef06a65c` **R1-G5-SIGNATURE** (G.5 signed, S1–S14 as recommended, S6 =
2027-12-31, S4 = acceptance line; the coordinator publishes the note once its records, render and review exist);
`54082a05` the ancestor–descendant screening test with its re-check review; `98c571d2` G.5 sd assembly + consumers + S9 split v2 (amendments as drafts), rev 4 pin update, screening smoke PASS, preflight/Ada blocker record, G1 replicate code, G2 constants (`4f5f686b…`); `42af62c6` **R1-STAGE-APPROVAL, R1-G5-TAILS-CONSUMERS, R1-P4-D3-GPU-PREFLIGHT** with canon and runbook sync; `03a352d9` screening ARFF fix, G2 fitter, manuscript (sources, 27 Nov), P11 TASL-7 run, design 6b/6c; `29099c4b` D.3 controller units (A0R, G8, FIXR3/EGATE engines, LADDER, G7, G9); `8b01ef6a` **R1-D3-VERIFY-SEED, R1-D3-PREDECL-R4** (author, 27 Nov; the pre-declaration freezes after its steps 3 and 5); `5c901d19` P.4 merge: sft-select missing-runs STOP and the H200 host-config fill (torch files 194/194; `cluster/20261126-01` done by this merge); `bd406db9` screening fix, P.4 direct launch and Ada host config, D.3 pre-declaration revision 4 (draft, unsigned), hygiene inventory; `6684e840` test-only unit, D.3c memo; `4490a0a9` copy review verdict line, P11 evidence table, redacted survey, manuscript restructure (title option 1, eight pages) and claim sheet; `e9c29a16` **R1-G5-TAILS, R1-G5-P11, R1-G5-S9** (author, 27 Nov); `9d87bebf` positive control and T5 shared-noise; `47df6f55` houseprice CPU-set fix (local/20261126-01); `166db0eb` **kit c1 record, seven-node REL-T1-G1B
copy, and the published expansion note `g1b_x_t1_tasl_20261126.md`** (strict check PASS, four gates PASS).

**Compute restarted by the author (28 Nov ~01:08); reports pushed (`coord/compute` `ebb7354b`).** **Running (seen on the hosts 01:19–01:27 CET):** screening evidence `SMEAS_EVIDENCE_20261128T001405Z` on deepthought2 (preflight passed, 64 workers, rows from 01:26 CET); TASL-7 E0 same-code reference `p5_e0_ref_20261128/e0e` (pid 2289540, from ~01:11 CET); houseprice CPU-set rerun `paperB_cpuset_20261128T001400Z` on TASL-2; P11 refusals being recorded. **Reporting gap (resolved) (28 Nov 00:05):** compute's reports since 18:08 sit on a local branch `coord-compute`, not on the remote `coord/compute` (`compute/20261128-02`). **Workers (23:22 CET, seen in their tmux panes):** Local (`paperb-local`) is working, on the houseprice CPU-set evidence (item 1).
Writer (`paperb-writer`) is working. **Compute is up** since 23:31 and delivered three reports by 23:41 (`coord/compute` @ `01df4594`). Local's report: `coord/local` @
`779ca615`. The writer pushed `writer-20261126-01-manuscript-restructure` and `writer-20261126-03-claim-table-sheet` (no report yet).

## Compute (DeepSeek; holds the former cluster and experiment cards, R1-AGENT-COMPUTE)

| # | Card | Runbook | State |
|---|---|---|---|
| done | `compute/20261126-10`: expansion G.1b | §2 2B | **all four nodes 460/460, determinism PASS**; result merged `cbc86fc5`; addenda `local/20261127-29` |
| 1b | `compute/20261127-05` with `-08`: G.5 P11 host tests | §2 2B | TASL-7 part done (C7, C10 short, C11 server side; ACCEPTED), merging; C2, C4, C5, C6, C9, C14, C15 pre-run, C11 chunk side still to run (TASL-2 needs the 0-7 leases) |
| 1a | `compute/20261127-20`: G1 final-snapshot fix **ACCEPTED** (`ff244366`, review `d5acf3ab`; G6/G7/analysis unchanged) | §2 2A | merged `2d88fe1b` |
| done | `compute/20261127-23`: D.3 integration merged `e92f3c73`; launchers merged `cd9af2af` | §2 2A | integration review next |
| 1b0 | `compute/20261127-22`: screening evidence run | §2 2A | **STOP** at the first worker-runtime probe (`python` vs `python3`, same interpreter; 0 runs); re-issued note published `b2f94c29`; run `compute/20261127-25` **STOPPED** (30 runs; cache tree changes under fetch_openml); fix merged `83425c70`; cache rebuilt (tree `3843b53c…`) and smoke 168/168 PASS, merged `523ccfbc`; second re-issue **signed and published** `280c0015` (R1-SCREEN-MEASURE-REISSUE-2); run `compute/20261127-30` **STOPPED** at the co-tenancy guard (186 runs, 0 failed; 9.87 of the required 10 free cores); rerun as infrastructure (R1-SCREEN-COTENANCY-INFRA, `c80f83bc`): `compute/20261127-35`: 8 co-tenancy stops so far (0 failed rows); back-off `compute/20261127-37`; **moved to deepthought2** (R1-SCREEN-DEEPTHOUGHT2): third re-issue published `a98d2eff` (`local/20261127-31` done); **launch `compute/20261128-06`** (waits for compute's restart); deepthought retries stopped `compute/20261127-38`; then a second re-issue for the author. Earlier: re-issue signed (R1-SCREEN-MEASURE-REISSUE, `96eb63da`); note prepared by `local/20261127-21`, then publication and a new launch |
| done | `compute/20261127-24`: 4B re-probe **PASS** (14.1 / 17.0 GB peak; total probe 3.10 GPU-h; projection 23.67), merged `85b2421f`; phase-1 draft merged `e56de25b`; P2 done (both Kev bases eligible; merged `523ccfbc`); P3 launch unit merged `a3c8284d`; choices signed (R1-P4-PHASE1-SIGNATURE, `280c0015`); Ada P5 records `compute/20261127-29`, then the coordinator publishes the note | §4 | — |
| 1c | `compute/20261127-19`: Ada P.4 probe: **0.8B bases PASS; 4B bases OOM at micro-batch 8 (STOP, author)**; record reviewed and merged `ebc28ec0`; 4B choice with the author | §4 | **ready** (host config on `main` `91cfd48a`) |
| 1c3 | Ada P5: smoke **PASS**; E0 not met against the 26 Oct reference; P5 record merged `15fe05b0`; **same-code TASL-7 reference** (R1-P4-E0-SAME-CODE-REFERENCE) `compute/20261128-01` | §4 | ready (first after screening) | **blocked**: Track P `gpu_lease` checks all GPUs; per-card lease merged `1f1b5d41`; P5 rerun `compute/20261127-33` |
| 1c2a0 | `local/20261128-02`: G.5 P11 engineering smoke path for the note-gated host tests (my "checked at publication" disposition withdrawn: R1-G5-P11 needs pre-publication coverage) | correction | ready |
| 1c2a | `compute/20261128-05`: dispositions: P11 without `validate --launch`, houseprice at 01:00 CET (28 Nov UTC run id), D6 copy waits for `local/20261128-01` (expansion copy variant) | coordinator | ready |
| 1c2b | `compute/20261128-04`: remove stale HTCondor requests 759624/759625 (Idle check, records kept) and 760065 (withdrawn); P.4 stays on Ada | author 28 Nov | ready |
| 1c2 | `compute/20261128-03` (= `-12`): D.3 HTCondor preflight, resubmit now as a new job (author reports free A100/L40S, 28 Nov) | §2 2A | ready |
| done | G1 adapter (`ac01717e`) and G6 audit (`0716ed8d`), merged `91cfd48a` | §2 2A | HPO-REF resumes (`local/20261127-15`); per-arm smoke once rev 4 freezes |
| 1d | `compute/20261127-16`: G1 core merged with the verify-seed checker; next the 6c replicate driver, then the G1 adapter at harness `9bb41680` (`verify_seed_base=20000`), then G6 | §2 2A | ready after `-12`/`-13` |
| 2 | houseprice CPU-set check | §2 2B | **STOP** `too_few_attempts`; driver fix merged `1f1b5d41`; rerun `compute/20261127-33` |
| 2b | `compute/20261126-11`: survey redaction | §4 | delivered `f60a2225`, **incomplete** (truncated `ps` user column in `Ada.txt` l.49–62); fix in `compute/20261127-02` item 2, then merge |
| 2c | `compute/20261127-03`: copy review's verdict case (G.5 B3); P11 evidence table | §2 2B | ready, after the launch |
| done | `cluster/20261126-01`: torch tests of the fill | §4 P.4 | fill merged with the STOP fix by the coordinator (torch env, 194/194) |
| 4 | `cluster/20261126-02` with `compute/20261126-02`: D.3 G1 runner and G6 audit, launcher outside HTCondor (design revision first) | §2 2A | ready |
| 5 | `experiment/20261126-02` and `cluster/20261126-03`: TASL-7 second sample; pool watch with a second Ada sample | §4 | recurring |
| 6 | `compute/20261126-03`: acknowledge rows (g) | — | with the next report |
| done | kit c1 record (`experiment/20261126-01`, `compute/20261126-04`); REL-T1-G1B copy (`compute/20261126-05`); survey (`compute/20261126-01`; Ada: LLM serving ready, P.4 training not ready: no torch env, no container runtime) | | merged `166db0eb` (survey: after item 2) |
| — | `compute/20261126-06`: G.5 campaigns on the TASL pair | §2 2B | blocked: G.5 note published (coordinator), after `local/20261126-08` render and review (local) |
| — | `compute/20261126-07`: P.4 probe on Ada | §2 2B, §4 | blocked: the Ada venv (`compute/20261127-06`) (the missing-runs STOP fix and the H200 fill are merged); the direct launcher and Ada host config are on `main` `bd406db9`. Earlier: a torch environment on Ada (the survey: a venv from the P.4 lock without sudo, or a container runtime from the host owner); the route goes to the author if a venv is not acceptable |
| done | `compute/20261127-14`: screening smoke **PASS** (168/168, no STOP) | §2 2A | merged `98c571d2`; note completion `local/20261127-12`, then the author signs |
| done | `compute/20261127-17`: G2 constants artifact (sha256 `4f5f686b…`, re-fit byte-identical, review ACCEPTED) | §2 2A | merged `98c571d2`; revision 4 fill `local/20261127-13` |
| 1d2 | `compute/20261127-28`: E-INT census on a second Ada card (R1-PAPERC-EINT-CENSUS, `d669b0bf`); smoke first; yields to Paper B | §2 3B | ready after `-27` has its card |
| done | `compute/20261127-27`: D.3 engineering smoke (TASL-2; G1/G6 chain PASS; G7 refused the smoke seed) merged `35c42b81`. **Coordinator errors:** the card asked for a G6 audit the frozen pre-declaration excludes for the smoke, and the merge included a G6 code change that was merged as documentation without the full suite; the suite was run afterwards: zero new failures, 6 more passing. G6 smoke path removed, merged `f43823da` | §2 2A | — |
| 1b | `compute/20261127-32`: G.5 P11 TASL-2 items (CPU sets free) | §2 2B | ready, after the screening launch |

## Local (Claude on the Mac)

| # | Card | Runbook | State |
|---|---|---|---|
| done | `local/20261126-01`: houseprice CPU-set procedure fix | §2 2B | merged `47df6f55`; the run is `compute/20261127-01` |
| 2 | `local/20261126-10` → `local/20261126-08` "prepare now" | §2 2B | **done** (report `779ca615`: fills listed; dry run clean; launch blocked only by `run_id`, P10 `tails`, the copy). P10 owner: `local/20261126-14` |
| done | `local/20261126-06` unit 1: P.4 direct launch and Ada host config (`5d1e2833`, re-check ACCEPTED WITH MINORS) | §2 2B, §4 | merged `bd406db9` (torch files: 194 passed) |
| done | `local/20261126-02` + `-04`: screening fix, both re-checks committed (`d1f239ee`) | §2 2A | merged `bd406db9`; smoke is `compute/20261127-07` |
| done | `local/20261126-03` + `-16`: D.3 pre-declaration revision 4 (`6412b843`, re-check ACCEPTED; draft, approved: false) | §2 2A | merged `bd406db9` (unsigned); the author signs §13 items 21–31 |
| done | `local/20261126-09`: positive control N1–N4 | — | `70af1457`; coordinator merge running (full suite) |
| done | `local/20261126-11`: T5 correction round | — | `440a3dd9`; coordinator merge running (full suite) |
| 8 | `local/20261126-07`: rows (g) inventory and the G.5 card monitor | §2 2B | ready |
| done | `local/20261126-04`: S9 sheet | §2 2B | `016742b1`; to the author with P10/P11 |
| 10 | `local/20261126-05`: item 1 controllers merged `29099c4b` (FIXR3/EGATE as decision engines only); item 2 test-only and item 4 D.3c memo merged; item 3 HPO reference **STOP** (re-check NOT ACCEPTED: needs G1/G6 interfaces, SMAC pin and per-attempt output dirs; resumes after G1/G6); item 5 Paper C last | §2 2A, 2C, 3A | in progress |
| 11 | `local/20261127-07` harness verify-seed unit **done** (harness `9bb41680`, checker `e44d966f`, ACCEPTED; checker merged); `local/20261127-08` revision 4 to frozen (after G2 and the harness unit); `local/20261126-06` unit 2 audit hosts **STOP** (re-check NOT ACCEPTED: launcher refuses shared cards against R1-CARD-SHARE; addendum binding to be designed; Ada as a G.5 audit host is a new host for a table, an author item later) — parked | §2 2A, 2B | ready in that order |
| done | `local/20261126-13`: hygiene inventory (`2005d0b0`: 72 worktrees proposed to retire, 14 keep, 6 active; 29 untracked dirs) | §2 0 | merged `bd406db9`; retirements are the author's |
| done | `local/20261127-09`: G.5 sd assembly and consumers merged `98c571d2`; render draft `mac-g5-sd-render-20261127` @ `bc968b3e` (P10 PASS) held for publication | §2 2B | G.5 waits for P11's TASL-2 items, the final `paper.commit`, the final review |
| 2a | `local/20261127-12` **done** (note ready to sign, review ACCEPTED, `b2360a7a`); `local/20261127-13` **done** (rev 4 binds G2; merged); `local/20261127-11` **done**: launcher venv mode ACCEPTED (`4a77a45b`), merged `66cc33f2` | §2 2A, 4 | `compute/20261127-18` (Ada host config, probe) |
| (old) | `local/20261127-01`: G.5 Student-t path | §2 2B | superseded by `-09`; was STOP: re-check NOT ACCEPTED pending the author's scope (gate oracle and A2 fit) and scale (sd matching) decision (`AUTHOR.md`). Branch `mac-g5-student-t-20261127` @ `b9bc00fc` kept |
| 2b | `local/20261126-08` final render | §2 2B | **STOP for decisions** (`mac-g5-render-20261126` @ `2959b369`; review NOT ACCEPTED on B1–B4): P10 and P11 go to the author (`sheets/G5_P10_P11_S9_SHEET_20261127.md`); B3 (copy review's verdict case) → `compute/20261127-03`; `paper.commit` filled at publication |
| 11e | `local/20261127-29`: four addendum drafts merged `f43823da`; switch STOPped on bindings → PRE-SPLIT v2 amendment **published** `a5a14901` (`split_v2_amendment` passes on `main`, sha256 `970d3e45…`); `local/20261127-30` unit 2: expansion launch and release binding merged `1afa7d62`; earlier: ( switch with its own launch binding; the main G.5 note does not wait); D6 copy `compute/20261127-36` | §2 2B | in progress |

## Writer

**Since `9de7eb57` (R1-MANUSCRIPT-REPO):** the writer works in `dowlingwong/paper_B_manuscript` on task branches (Codex GPT-6.2 Sol); the coordinator publishes reviewed manuscript revisions there and updates the `papers/manuscript` submodule pin. `papers/r1` is the pre-migration snapshot. Codex-recorded signatures are published after the coordinator's content check (R1-CODEX-RECORDED-SIGNATURES).

| # | Card | Runbook | State |
|---|---|---|---|
| 1 | `writer/20261126-01` with `-02`: restructure | §2 1, §3 | **delivered** `6138b54f` (re-check ACCEPT WITH MINOR, minors applied; main text about 8.85 pages). The author told the writer in its pane: title option 1, trim to eight pages. **Merge after that trim**, with `writer/20261126-03` |
| done | `writer/20261127-01`: sources and 27 Nov rows | §3 | merged `03a352d9` (figures dropped where PDFs were unreachable) |
| done | `writer/20261127-02`: Codex's manuscript edits adopted where they fit (`e3af70a4`, review accepted) | §3 | merged |
| done | `writer/20261126-03`: revised outline and claim-to-table sheet | §2 1, §3 | **delivered** (`a9a9f6bb`, review ACCEPT WITH MINOR, corrected). Merges with or after item 1; §6 passed to local (`local/20261126-16`); §5 items go to the author as one sheet |
| — | result tables | §3 item 4 | blocked: released results; none exist |

## Coordinator

- **Expansion note published** (`166db0eb`), from the prepared branch `coord-xnote-prep-20261126` @ `bfbd7af0`. P4 and the four gates are filled PASS; the draft
  `check-note-x` passes and `check_gate_x` passes for all four nodes against `main` `54082a05`. Only P2 waits for the c1 record.
- Waits for a delivery: expansion note publication (after the c1 review); G.5 note (after the copy, render and review); controls-pos
  merge (after `local/20261126-09`); T5 merge (after `local/20261126-11`); P.4 host-config fill merge (after
  `cluster/20261126-01`).
- Not dispatched: §2 order 0 at repository level and order 4 (design and author); 3B (fixed-memory census: no PLAN row for the
  census or for the design role, see `AUTHOR.md`).

**Process incident (27 Nov 01:49):** compute amended and force-pushed its G1 task branch (`121ba63d` → `51cf07f7`) before review. Against rule 1. Disclosed by compute; no `main` push. Correction card `compute/20261127-10`.

**Process incident (27 Nov 13:05, coordinator):** D.3 revision 4 was frozen (`9cd5863c`) before the screening result that R1-SCREEN-MEASURE and R1-SCREEN-MEASURE-SIGNATURE place before the D.3 binding freeze. No campaign has started; step (8) is held; the author is informed.

**Process incident (27 Nov 16:55, coordinator):** the D.3 smoke card asked for a G6 audit of the smoke, which the frozen pre-declaration excludes; and the coordinator merged the smoke branch, which carried a G6 code change, as documentation without the full suite. No pinned hash is affected (revision 4 pins `d3_analysis.py` only), no Y value is used, the new block 6391–6410 overlaps no declared block; the full suite run afterwards shows zero new failures; the G6 path is being removed.

**Departure from the runbook (recorded, not changed):** §2 says the local worker implements runner changes. The existing card
`cluster/20261126-02` gives the D.3 G1/G6 code to the agent that designed it, and R1-AGENT-COMPUTE passes that card to compute.
The card stands. Implementation and review stay with different agents.

**Unmerged branches:** `p4-hostconfig-fill-20261126` (waits for the torch tests); `mac-controls-pos-20261123` (re-check
accepted, waits for N3); `mac-t5-shared-20261122` (accept with minor, waits for its correction round);
`p4-staging-20261125` (parked: dates R1-STEP-ORDER withdrew);
`codex/layout-flatten-preview` (R1-LAYOUT-FLATTEN conditions unmet). Review records: `coord-reviews-20261126` @ `5b3379ec`.

**Open STOPs:** houseprice TASL-2 CPU-set (procedure; houseprice only); screening smoke `determinism_unverifiable
openml_breast_w c5 seed 999`; P.4 T4 (`env3` missing in the CPU image); P.4 T6/T1 (no H200; the route is Ada).

**Mac checkout (resolved 28 Nov):** the four approved documents are published (R1-MAC-WORKFLOW-APPROVAL, `15fe05b0`); earlier: uncommitted edits to `README.md`, `canon/README.md`, `canon/agents/coordinator/SOUL.md` and the runbook (§7
"Dispatch and run the queues"). The coordinator follows that §7 at the author's request. It is not on `main`.
