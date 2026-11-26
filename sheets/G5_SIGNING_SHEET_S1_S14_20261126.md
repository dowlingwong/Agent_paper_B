# G.5 signing sheet: S1 to S14 (draft for the author)

**Coordinator:** Claude Code session ca57c183 (tmux `paperb-coordinator`), 26 Nov 2026, about 22:40 CET. AI-assisted.
**Basis:** published `main` `95249de3`. The rows of 26 Nov (f) and (g) are in force. The G.5 note draft is revision 13,
`docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md`, sha256 `3229de2b3a803740f3934957ffcd93b3e112428cd6632ab6bfdcd11f7c41aa34`,
last changed in `311f1b2b`. Revision 13's code (`mac-g5-pilot-basis-g4b-20261126`) is an ancestor of `main`.
**Status:** tier D. This sheet decides nothing. The options and texts come from the draft's §11.1. What this sheet adds is a
reading of each line under the rows now in force, plus a recommendation. The author decides.

## 0. How the rows of 26 Nov (g) meet the G.5 note

- **R1-HOST-FREE (3)** says: "the G.5 note is signed as drafted for the TASL pair so that it can start". The
  recommendations below therefore keep revision 13's code and spec. They need **no new code revision**.
- **R1-NO-TIMEOUT (1)** withdraws the wall-time bounds of checks, job deadlines and latest starts, but only for runs not yet
  launched. Once signed, a run "follows its note". Two lines of the draft carry a date or a wall-time bound: S6
  (`freeze_wait`, STOP 14) and S14 (9.486 s a run). Each is handled below.
- **R1-NO-TIMEOUT (3)** makes 425 GPU-h a reporting threshold. Where the code stops at it (STOP 9), the coordinator
  publishes an addendum that raises the figure. The row pre-authorises that addendum, so S1 changes nothing in the code.
- **R1-CARD-SHARE (5)**: G.5's reviewed lease check still refuses to start beside another user's compute process. On
  TASL-2 and TASL-7, a G.5 job therefore starts on a card to itself. Local task `local/20261126-07` item 2 (a card monitor
  plus a repeat addendum) covers a process that appears mid-run. The signature does not wait for that unit.
- **R1-STEP-ORDER (2)(a)–(b)**: each expansion node that passes G.1b joins G.5 by addendum whenever it completes. The
  arms-frozen record waits for every node in the set. S6 and S9 follow from this.

## 1. The fourteen lines

| # | Line | Recommendation | Basis and what it costs |
|---|---|---|---|
| S1 | `cap_gpu_hours` | **A**: 425 GPU-h of the worker card, TASL-7 audit-chunk hours inside it | As built: STOP 9 counts TASL-7 attempts. The projection is 216.9 GPU-h (S2), which leaves about 208 GPU-h of headroom. Under R1-NO-TIMEOUT (3) the 425 is a reporting threshold. B would need a meter change and a new review. |
| S2 | `gpu_hours` (P7) | **Sign as rendered**: 216.9 GPU-h | The G.4b recompute in `pilot_basis`. Each expansion node that joins brings its own recompute in its addendum. |
| S3 | P3, P7 text | **Sign with the citations** `g4b-tasl-20261124-a` and `G4B_TASL_PILOT_RESULT_20261125.md` | The `pilot-basis` PASS from a published `main` checkout on TASL-2 is on `main`: `docs/r1/reports/tasl_chain_20261122/G5_TASL_PREP_20261126.md` §3, stdout sha256 `2ea43c57…`. The captures' `SHA256SUMS` has sha256 `870988ad…287935`. The G.4b sealed attempts stay untouched until G.5 is sealed. |
| S4 | `cuda_ipc` | **(a)**: the acceptance line, signed verbatim (TASL-2 and TASL-7 audit chunks) | No C12 record is on `main` (searched 26 Nov). (b) needs two host tests before the first job, and nobody is tasked with them. (a) costs nothing: no frozen parent exports a CUDA tensor, and no node uses `cuda_share`/`cuda_open` (P1). If you want (b), I task the compute agent and G.5 waits for it. |
| S5 | `job_layout` (TASL-7 schedule) | **A**: as built, claimed chunks under the code's rules, no timetable | For the eight nodes no wave has three chunks, so A and B are the same today. A keeps the path open for expansion nodes. |
| S6 | `freeze_wait` (STOP 14) | **(c) a later date: `2027-12-31`**, with this sentence in the signing row: "under R1-STEP-ORDER the date is a technical bound, not a rule" | The draft proposes 18 Dec. STOP 14 refuses any G.5 job that starts on or after that date, and only "a docs-only amendment naming an author row on `main` that names the new date" can move it. With 18 Dec, an expansion node that joins late, or any slip, would cost you a fresh dated row. R1-STEP-ORDER withdrew the 17 Dec release and the 20 Dec freeze. STOP 14's other part, "the arms-frozen record waits for every un-STOPped node", is exactly R1-STEP-ORDER (2)(b) and stays. This is a value fill and a re-render, with no code change. **Checked:** the spec validator needs only an ISO date (`g5_tasl.py:1124` on `95249de3`), and the note line has a fixed form with any date (`FREEZE_LINE`, `:1422`). The date is a spec value filled at signature with the other fills, so it needs no code change. |
| S7 | STOP thresholds | **As proposed**: liveness 0.25, invalid share 0.2, infrastructure 5 %, audited band 100–200 | G.4b `ran_of_valid` is 0.6667, 0.8167 and 0.6167. The projected audited counts are 146.9, 180.0 and 135.9. |
| S8 | `t1_table_readings`, `server_log`, `seal`, 3b-1 readings, `campaign_attribution` | **As listed in §11**: `refuse`; option (a); procedural; signed text | Unchanged since revision 11. |
| S9 | Expansion addendum | **Not signed now.** It is a separate sheet (task `local/20261126-04`) | Under R1-STEP-ORDER (2)(a) the 2 Dec condition is gone: a node joins whenever its G.1b PASSes. What remains open is the frozen eight-node split file (`b5967dd7…`, PRE-SPLIT A) and the addendum code, which is not yet built. |
| S10 | `decisions`, `e4_amendment_row` | **Fill as stated**: R1-G5-DECISIONS-2, R1-G5-MEM-E4 | Each row occurs exactly once on `main` (checked 26 Nov on `95249de3`). |
| S11 | `audit_K`, seed lines | **As rendered**: K = 10, and K = 6 only after a K-check PASS row | No K-check row exists. |
| S12 | `environments` (autoresearch) | **As rendered**: `ar-cond7a` under R1-G1B-AR-ENV / R1-G1B-AR-PY | Comes from the completion record under G5-ARPEND A. |
| S13 | `tasl2_cpus` and the schedule against the expansion G.1b | Set **(A) 0-7**. Schedule **(i) with (ii)'s flock**: each G.5 TASL-2 job takes `cpus-0-3.lock` and `cpus-4-7.lock`; a busy lease means wait | No 8-CPU set avoids both 8-11 and the expansion's sets. In practice the expansion G.1b launches before G.5 can (see §2), so G.5 waits for MetaMaze and Forest Cover (about 16.4 h, or 24.5 h at 1.5×). With R1-STEP-ORDER no cutoff ends that precedence. It ends when the jobs end. |
| S14 | `tasl2_cpuset_check` | **A as built**: three sealed attempts on 0-7, bit-identical to the sealed G.1b TASL-2 attempt, each run within 9.486 s | The 9.486 s is a wall-time bound in a CPU-set check, the kind R1-NO-TIMEOUT (1) withdraws. R1-HOST-FREE (3) signs the note as drafted, though, and 9.486 s is also the audit run budget R1-NO-TIMEOUT (2) keeps. Attempt 1 measured a maximum of 3.877 s (`G5_TASL_PREP_20261126.md`, table row "houseprice TASL-2 cpuset check"), so the bound costs nothing. Option A′ (timing descriptive only) needs a change to `cpuset-verdict` and a re-render. |

## 2. What must exist before the note can be signed (not the author's work)

The author can give the choices now. The note itself still needs these records on `main`. Each is tasked or owed:

1. **The seven-node REL-T1-G1B copy (P2, D6 A)**: `g5_relcopy.py` run on the joined run `g1b-tasl-20261121-b` on TASL-2. It
   produces the summary, `crosscheck_gate.json`, `ASSEMBLY.json` and `runs.jsonl` copies with `COPY_RECORD.json`, plus a
   fresh review naming all four sha256s. **None is on `main`.** New task `compute/20261126-04`.
2. **P10**: the Gaussian or Student-t declaration per node, taken from that summary. It follows step 1.
3. **The final render**: fill the spec (`decisions.<id>.signed`, S6's date, S4's mode), run `g5_tasl.py key-lines`, then
   `check-note … --draft`. Owner: the local worker, who wrote the draft. Tier E, review of the render.
4. **Publication**: `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md` with `approved: true`, the strict `check-note`
   after publication, and a PLAN row that records the signature. Setting `approved: true` is outside R1-AUTONOMY (3), so it
   needs your "推 main".

After the signature, before houseprice's first TASL-2 job: the CPU-set record (`local/20261126-01`, then
`experiment/20261126-03`). That blocks houseprice only.

## 3. The reply that signs

> 签 G.5：S1–S14 按推荐（S6 = 2027-12-31，S4 = 验收行）+ 推 main

A different choice on any line: name the line and the option, for example "S6 = 18 Dec", "S4 = C12".

## 4. Not checked by this sheet

The render itself (nothing was run). The state of TASL-2 and TASL-7. Whether
`g1b-tasl-20261121-b`'s joined directory is intact on TASL-2.
