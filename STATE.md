# State — 26 Nov 2026, about 23:30 CET, `main` at `ef06a65c`

Coordinator: Claude Code session ca57c183, tmux `paperb-coordinator` (took over at `9bdf4a18`). `HANDOVER.md` is the
interim coordinator's view of 20:30Z. Where it differs from this file, this file is newer.

**Published 26 Nov, later:** `b7e8a6aa`, the merge of `htc-image-v2.2-20261124` (the build source of the pinned v2.2
image; full suite with zero new failures after re-running two load flakes); `ef06a65c`, **R1-G5-SIGNATURE** (the author signed
G.5 with S1–S14 as recommended, S6 = 2027-12-31, S4 = the acceptance line). The G.5 note is published once the REL-T1-G1B copy,
the final render and its review exist (the row pre-authorises that publication).

**Published earlier this round:** the rows of 26 Nov (f) and (g) (R1-AGENT-COMPUTE, R1-HOST-FREE, R1-CARD-SHARE, R1-NO-TIMEOUT
with TIMEOUT A, R1-STEP-ORDER), merged as `95249de3` (merge of `52a3ce7a`). The author's answer was "D1: A". Published under
R1-AUTONOMY (3): PLAN additions only, D8 guard PASS, the PLAN-reading test subset identical on base and merge (6 failed,
539 passed, 3 errors, same ids). **No calendar date decides anything any more.** The tasks that rested on these rows are in
force: `tasks/compute/*`, `local/20261126-06`, `local/20261126-07` and `writer/20261126-02`.

| Role | Queue (first item first) | Blocked on |
|---|---|---|
| compute (DeepSeek; replaces cluster and experiment) | 1. kit c1 record (`experiment/20261126-01` with `compute/20261126-04`); 2. REL-T1-G1B seven-node copy (`compute/20261126-05`); 3. resource survey and Ada readiness (`compute/20261126-01`); 4. D.3 G1/G6 code with the non-HTCondor launcher; 5. torch tests of the host-config fill; then the rest of `compute/20261126-00` | **Not started.** No `coord/compute` branch exists. The author starts the agent |
| local (Claude on the Mac) | 1. houseprice CPU-set fix; 2. screening smoke STOP; 3. D.3 pre-declaration revision 4; 4. S9 sheet; 5. host-free units (P.4 off HTCondor first); 6. rows (g) inventory; 7. G.5 final render (prepare now, render after the signature and the copy); then `local/20261126-05` | **Not started.** No `coord/local` branch exists |
| writer | manuscript restructure (`writer/20261126-01`), with `writer/20261126-02` | Not started |
| design | runbook draft (Codex) | No PLAN row for the role |
| coordinator | Done: takeover; rows (f)(g); G.5 signing sheet (`sheets/G5_SIGNING_SHEET_S1_S14_20261126.md`); kit c1 launch path verified; unmerged branches classified. Done later: v2.2 merge; G.5 signature row; reviews of controls-pos (accepted) and T5 (accept with minor). In progress: re-check of the screening test | — |

**Critical path to the gate:** kit c1 record → expansion note published → four expansion nodes on TASL-2 (aim: before
30 Nov 20:33 CET, so the reviewed note's `cutoff` line has no case) ‖ REL-T1-G1B copy → author signs G.5 → final render →
G.5 on the eight nodes (expansion nodes join by addendum, S9) → T1 train/dev release → arms (A5 needs a GPU: Ada) → arms-frozen
record → the gate read. D.3 runs in parallel: screening STOP diagnosis, pre-declaration revision 4, G1/G6 code.

**Unmerged branches (classified 26 Nov):**
- `p4-hostconfig-fill-20261126` (`021c4eec`): tier E, two acceptances, merges cleanly. Waits for the torch tests (task
  `cluster/20261126-01`, now compute's).
- `htc-image-v2.2-20261124`: merged (`b7e8a6aa`).
- `mac-controls-pos-20261123` (`25d5a510`): re-check **ACCEPTED** (record on `coord-reviews-20261126` @ `28ddabf4`). Not
  merged yet: its new test `test_critical_values` fails at 10 decimal places with scipy 1.11.1, which would be a new failure.
  Fix task `local/20261126-09`.
- `mac-screening-test-20261122` (`e7392a61`): fresh re-check running (coordinator-arranged).
- `mac-t5-shared-20261122` (`d0ef5282`): fresh review **ACCEPT WITH MINOR** (record on `coord-reviews-20261126` @ `a2464ec4`).
  One correction round, task `local/20261126-11`; then merge.
- `p4-staging-20261125` (`3bbf2f52`): adds target dates that R1-STEP-ORDER withdrew. Parked, not merged.
- `codex/layout-flatten-preview`: not merged (R1-LAYOUT-FLATTEN conditions unmet).

**Open STOPs:** (1) houseprice TASL-2 CPU-set check, a procedure defect, blocks houseprice only; (2) screening smoke
`determinism_unverifiable openml_breast_w c5 seed 999`; (3) P.4 T4, `env3` missing in the CPU image; (4) P.4 T6/T1, no H200
in the pool. Under R1-HOST-FREE the route is Ada, after the survey and a non-HTCondor launcher (`local/20261126-06` unit 1).

**Local checkout on the Mac:** uncommitted edits to `canon/*`, both SOUL files, the runbook (§7 daily pass) and the READMEs
are not published and do not count. `main` now changes `canon/` too, so a pull will conflict there. The author decides what
happens to those edits.
