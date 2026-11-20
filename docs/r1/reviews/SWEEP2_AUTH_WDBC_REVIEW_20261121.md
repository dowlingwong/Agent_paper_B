# Review (round 4): sweep-2 authorization note update for the R1-S2C3B-WDBC declared 7/8 C3b exception

- **Reviewer:** fresh, independent, read-only reviewer (AI-assisted, DeepSeek Harness subagent). Not the note's
  author, not the executing cluster agent, not the R1-S2C3B-WDBC code author. This review file is the **only**
  artifact written; it is left **uncommitted** in the worktree.
- **Target:** branch `sweep2-auth-20261120b` @ `22ecc9449adbe92b5911a63ffb8a01edc74f4ceb`, worktree
  `.claude-worktrees/sweep2-auth-20261120b`; base = published `main` `df58bcd5bdeeb7d1cb1cd1c3beddc29376b3575e`
  (`df58bcd5` is an ancestor; the branch adds only docs, no `sweep2/` or `r1/` code change).
- **Note reviewed:** `docs/r1/authorizations/c3_sweep2_20261119.md`. Published bytes at `df58bcd5`:
  sha256 `ef4325c5078bd9ba46f528edd605346f0677b183248471f09169dd04ee12a04c`, 9,861 B. Branch bytes at
  `22ecc944`: sha256 `349e502b40b75a02b372cf495e78980145ede7c883f7868cc6228e9daa27e86a`, 11,073 B (both match the
  brief). Diff vs published main: 15+/7- in the note only (7 hunks), nothing else.
- **Branch-tip caveat (recorded, not a defect):** while this review was starting, the branch tip advanced
  `22ecc944` → `19ea1a228e2c54aada12a14e907787eca413a8c7` (commit message: "dry-run report notes the later P6
  exception edit (all other key-block values unchanged)"), and `origin/sweep2-auth-20261120b` already points at
  `19ea1a22`. The delta is `docs/r1/reports/sweep2_20261116/SWEEP2_SCHEDULER_DRYRUN_20261120.md` only (+3/−3 prose
  lines); the note bytes are **byte-identical** at `22ecc944` and `19ea1a22` (sha `349e502b…`), so every check below
  applies unchanged to both. Worktree is clean.
- **Authority read:** PLAN row **R1-S2C3B-WDBC** on `origin/author-decisions-20261120b` @
  `2c1888df` (PLAN line 1336; not on `main`), including PLAN rows R1-SWEEP2-AUTH (l.1299), R1-S2C3B-LAUNCH
  (l.1243), R1-S2C3B-RERUN (l.1286), R1-SWEEP2-LAYOUT-AMEND (l.1233); exception code on
  `origin/s2c3b-wdbc-exception-20261120` @ `a234a6cb`
  (`sweep2/s2_c3b_lib.py` `apply_declared_exception`, `sweep2/s2_c5_switch.py` `parse_note` /
  `liveness_nodes_ok`); its review `docs/r1/reviews/S2C3B_WDBC_EXCEPTION_REVIEW_20261120.md` (ACCEPTED, round 2 at
  `1d4273fb`); real STOP evidence on `origin/ops-s2c3b-launch-stop-20261120` @ `0e635c9f`
  (`.../s2c3b_launch_20261120/job_record.json`, `SEAL_RECEIPT.json`, `SHA256SUMS`,
  `docs/r1/reports/sweep2_20261116/S2_C3B_LAUNCH_STOP_20261120.md`); the previous launch review
  `docs/r1/reviews/SWEEP2_AUTH_LAUNCH_REVIEW_20261120.md` (round 3 ACCEPTED at `df58bcd5`).
- **Method: read-only.** No jobs, no `condor_*`, no project test suite, no git writes (only the instructed
  `git fetch` of the three cited branches, which updates remote-tracking refs). The only execution was stdlib
  Python applying the exception-branch code to committed blobs and to the real STOP record, and read-only `git`
  (`show`, `diff`, `ls-tree`, `merge-base`, `rev-parse`).

---

## 0. Verdict summary

**All required checks pass.** The note's six absolute "8/8" places are updated; the new
"C3b exception and analysis scope (R1-S2C3B-WDBC)" bullet is accurate against the PLAN row, the exception code and
the **real** STOP record; the collection-gates bullet keeps all 16 node/memory pairs and `min_live_nodes` 8 without
contradicting the seven-node primary analysis; **only the P6 key-block line differs** from the published note
(programmatically proven, including a hash of the other 19 lines); the integrated `parse_note` accepts the note and
`resolve_label` returns EVIDENCE with the new sha staged; `check()` accepts once publication is simulated and
fails closed before; the exception is exactly openml_wdbc + invalid_rate + observed ≤ 0.30 and the note does not
broaden it; the C3b "reproduce exactly or 8/8, else STOP" rule and the no-commit window are stated; nothing else in
the note becomes false.

Findings are **non-blocking** (two wording/precision nits in the note, two optional precision observations, and two
items outside the note: stale operational "8/8 required" text in the cluster launch prompt / authorization
template, and the publication/launch preconditions in §6). No note edit is required before publication of these
bytes; §6 items are launch-step obligations for the coordinating chat / cluster agent.

**Final line: `VERDICT: ACCEPTED`.**

---

## 1. Check 1 — the six 8/8 places (required)

All six are present and updated in the requested direction; the published note had five lines containing "8/8"
(l.7, 33, 73, 90→98, 108→116) plus the STOP list's absolute "liveness < 8" (l.113→121). New note:

| # | Place (new line) | Text now present | Verdict |
|---|---|---|---|
| 1 | Header, l.7 | "…rerun at the launch commit (no commit to `main` between it and the launch): **8/8, or the 7/8 declared in R1-S2C3B-WDBC (only openml_wdbc failing, only invalid_rate, observed <= 0.30)**." | **PASS** |
| 2 | Key-block P6, l.33 | "…launch-commit C3b **8/8, or the 7/8 declared in R1-S2C3B-WDBC (only openml_wdbc failing, only invalid_rate, observed <= 0.30)**, required; switch enabled with both keys for this run id only" | **PASS** |
| 3 | Liveness bullet, l.73–74 | "S2-C3b D28 liveness at the launch commit: **8/8, or the 7/8 declared in R1-S2C3B-WDBC (only openml_wdbc failing, only invalid_rate, observed <= 0.30)**, with the launch image digest…" | **PASS** |
| 4 | Launch-commit bullet, l.98 | "…at which S2-C3b is rerun and **passes 8/8 or the declared R1-S2C3B-WDBC 7/8 shortfall**; recorded in every job record…" | **PASS** (short form; §7 F1) |
| 5 | "No EVIDENCE launch before" bullet, l.116 | "…launch-commit C3b **8/8, or the declared R1-S2C3B-WDBC 7/8 shortfall**, is required at that commit)." | **PASS** (short form; §7 F1) |
| 6 | STOP list, l.121 | "…parse failures > 0.2; **liveness below 8 unless it is exactly the R1-S2C3B-WDBC shortfall (openml_wdbc, invalid_rate, observed <= 0.30)**; chunk over walltime…" | **PASS** |

Stale-absolute check (script over the committed bytes): no `8/8 only`; no `liveness < 8`; no `C3b 8/8 required`;
no `passes 8/8;`. The only remaining absolute-looking phrases are the new qualified ones above. The note also keeps
the row reference in every place (six occurrences of `R1-S2C3B-WDBC`, lines 7, 33, 73, 77, 98, 116, 121).

## 2. Check 2 — new bullet vs the PLAN row and the real STOP record (required)

New bullet, note l.77–82:

> **C3b exception and analysis scope (R1-S2C3B-WDBC):** all 16 chunks (all eight nodes) run; the **primary
> sweep-2 analysis uses the seven nodes that passed C3b**; `openml_wdbc` is a pre-declared sensitivity row
> (with / without), disclosed in the sweep-2 report and the appendix. The STOP record is
> `ops-s2c3b-launch-stop-20261120`, job 759810 (`openml_wdbc` `invalid_rate` observed 0.30, required < 0.3;
> every other criterion and node passes). The launch accepts a sealed C3b record that is 8/8, or exactly this
> 7/8 shortfall with `declared_exception`; any other C3b result is a STOP.

| Claim in the bullet | Source checked | Verdict |
|---|---|---|
| all 16 chunks / all 8 nodes run | PLAN row R1-S2C3B-WDBC ("sweep 2 submits all 16 chunks (8 nodes)"); collection code expects 16 pairs | **PASS** |
| primary analysis = seven nodes that passed C3b | PLAN row verbatim (same phrase) | **PASS** |
| openml_wdbc = pre-declared sensitivity row (with/without), disclosed in sweep-2 report + appendix | PLAN row verbatim | **PASS** |
| STOP record branch `ops-s2c3b-launch-stop-20261120` | `origin/ops-s2c3b-launch-stop-20261120` @ `0e635c9f` exists; commit `0e635c9f` is the STOP data commit on `df58bcd5` | **PASS** |
| job 759810 | `S2_C3B_LAUNCH_STOP_20261120.md:7` — "Job **759810** on `g4401.nemo.privat` (NVIDIA H200)…" | **PASS** |
| openml_wdbc invalid_rate observed 0.30, required < 0.3 | real `job_record.json` `liveness_results`: `openml_wdbc.failed_criteria = ["invalid_rate"]`, `invalid_rate = {observed: 0.3, required: "< 0.3"}`, `n_trials: 20` | **PASS** |
| every other criterion and node passes | real record: wdbc `active_novelty_fraction.observed = 0.7` (≥ 0.5), `keep_after_trial_1.observed = 2` (≥ 1); the other seven nodes all `pass: true`; `live_nodes: 7`, `failed_nodes: ["openml_wdbc"]` | **PASS** |
| launch accepts 8/8 or exactly this 7/8 with `declared_exception`; anything else STOP | PLAN row + `liveness_nodes_ok` (see Check 6); note wording "exactly this 7/8 shortfall … any other C3b result is a STOP" | **PASS** |

The bullet does **not** broaden the exception: it names a single node, a single criterion, an observed bound and
`declared_exception`; the six places repeat "only openml_wdbc failing, only invalid_rate, observed <= 0.30".

## 3. Check 3 — collection-gates bullet vs collection code and the 7-node primary analysis (required)

Added sentence (l.88–89): "Collection still requires all 16 node/memory pairs and `min_live_nodes` 8
(`openml_wdbc` runs); this is unchanged."

- `s2_c2_lib.collect_evidence` requires exactly the 16 node/memory pairs (distinct-key check, "sealed collection
  has N/16 distinct node/memory pairs"); both `openml_wdbc` chunks are in the sweep-1 baseline, so the wdbc chunk
  must be sealed/collected — consistent with "all 16 chunks run" and with wdbc being only a **sensitivity** row.
- The liveness spec still carries `min_live_nodes` 8 (`validate_spec`: "liveness.min_live_nodes must be 8"); the
  R1-S2C3B-WDBC exception is applied **after** the 8/8 verdict (`apply_declared_exception` sets `pass` true but
  leaves `min_live_nodes` 8 in the record), so "min_live_nodes 8 … unchanged" is accurate and the declared 7/8
  stays explainable via `declared_exception`.
- The seven-node **primary analysis** and the all-16-chunk **collection** are different scopes; the note says so
  explicitly (l.77–78 vs l.83–89). No contradiction found.

Precision observation (§7 F4): `collect_evidence` itself does not re-check `min_live_nodes`; that value lives in the
chunk/liveness spec. The sentence groups the two gates; it is not false (both remain at their published values),
only a reword candidate.

## 4. Check 4 — key-block byte identity (required, programmatic)

Script: extract the fenced key block (` ``` ` … ` ``` `) from `git show df58bcd5:…` and
`git show 22ecc944:…`; compare line by line and by hash.

- Both key blocks have exactly **20** lines; the published and branch fences are at the same place; no stray
  key/`word:` lines outside the block (also confirmed by `parse_note`, §5).
- Exactly **1** differing line: **P6**.
- SHA-256 of the key block **with the P6 line removed**:
  `9abc2c25c618e66a95e7ddb991972a3db7a4751049d4c64fc4980b15729e621b` for **both** the published and branch bytes
  (19 lines). So every other key-block line — `approved`, `label`, `run_id`, `phase`, `image`, all six
  `layout_*`, `b2_audits`, `d8_lock`, `P1`–`P5`, `P7` — is byte-identical.
- As a cross-check, the P6 line is still a single line, still starts `P6: PASS — `, and `parse_note` accepts it.

## 5. Check 5 — parsers, key-block structure and prose consistency (required)

Against the exception-branch code at `a234a6cb` (`sweep2/s2_c5_switch.py`, `sweep2/s2_c2_lib.py`), with the
branch note bytes `349e502b…` staged under `docs/r1/authorizations/`:

- `parse_note`: **ACCEPTED**. Exactly 20 parsed `key: value` fields — `approved`, `label`, `run_id`, `phase`,
  `image`, `layout_request_walltime_s`, `layout_request_disk_kb`, `layout_request_memory_mb`, `layout_chunks`,
  `layout_gpu_hours`, `layout_wall_hours`, `b2_audits`, `d8_lock`, `P1`–`P7`. **No duplicates**, no missing
  required field, all seven P fields `PASS — `. Layout values equal `ACCEPTED_LAYOUT`
  (`8735 / 42460970 / 32000 / 16`); `image` equals `FROZEN_IMAGE`; `b2_audits` equals the exact required string;
  `approved: true`; `label: EVIDENCE`; `run_id: s2ev-20261119-a`.
- `resolve_label(spec)` with `label_source.authorization_sha256 = 349e502b…`: **EVIDENCE**. With a wrong sha it
  STOPs ("authorization note sha256 mismatch") — fail-closed.
- `check(spec, note)` (note + spec pinning the new sha, no JDL):
  - **before publication** → STOP "authorization note is not committed on `origin/main`" (expected; `origin/main`
    still carries `ef4325c5…`);
  - with publication simulated (`_authorized_note` matching the new bytes) → **ACCEPTED**, returns
    `note_sha256 = 349e502b40b75a02b372cf495e78980145ede7c883f7868cc6228e9daa27e86a`, correct run_id/layout;
  - a spec still pinning the published `ef4325c5…` → STOP "spec pins a different authorization note sha256".
- Prose consistency: no stale absolute claims remain (`8/8 only`, `liveness < 8`, `C3b 8/8 required` all absent);
  l.81 is exactly the required "8/8, or exactly this 7/8 shortfall with `declared_exception`; any other C3b
  result is a STOP."; no line outside the fenced block starts with `word:`, so nothing can shadow a key field.

## 6. Check 6 — code/row consistency and what else stays true (required)

**The exception is exactly the declared one.** `s2_c3b_lib.DECLARED_EXCEPTION = {row: R1-S2C3B-WDBC,
node: openml_wdbc, criterion: invalid_rate, required: "< 0.3", max_observed: 0.30}`. `apply_declared_exception`
returns the verdict unchanged unless the PLAN row is present, `live_nodes == 7`, `failed_nodes ==
["openml_wdbc"]`, wdbc `failed_criteria == ["invalid_rate"]`, `required == "< 0.3"`, `observed` a non-bool numeric
`0 ≤ observed ≤ 0.30`, and the other two criteria were evaluated. `liveness_nodes_ok` independently re-checks the
recorded wdbc entry and the seven `pass: true` siblings and requires
`^\| R1-S2C3B-WDBC \|` on published `main`'s PLAN.

Re-run against the **real** STOP record (read from `origin/ops-s2c3b-launch-stop-20261120`) with the two PLAN
versions:

| Input | Driver `apply_declared_exception` | Switch `liveness_nodes_ok` |
|---|---|---|
| real record, PLAN without the row (`df58bcd5`) | refused (`pass` stays False) | **False** |
| real record, PLAN with the row (`2c1888df`) | accepted, `declared_exception` = {row R1-S2C3B-WDBC, node openml_wdbc, criterion invalid_rate, required "< 0.3", max_observed 0.3, observed 0.3} | **True** (after JSON round trip) |
| observed changed to 0.31 | refused | — |
| two failed nodes / `live_nodes` 6 | refused | — |

The row at `2c1888df` (PLAN l.1336) matches both the driver and switch regexes (`^| R1-S2C3B-WDBC |`); it is
**not** on published `main`. Row text matches the note's bullet on every point (16 chunks/8 nodes, seven-node
primary analysis, wdbc pre-declared sensitivity with/without, disclosure in report+appendix, 8/8 or exact 7/8).

**C3b rerun / no-commit window.** The note requires the rerun at the launch commit (l.7, l.73, l.98) and accepts
only 8/8 or "exactly this 7/8 shortfall … any other C3b result is a STOP" (l.81), which is the row's "must
reproduce exactly this result (7/8 with the same openml_wdbc failure) or give 8/8; otherwise STOP". The no-commit
window is unchanged: "No commit to `main` between the C3b rerun and the launch" (l.99).

**Nothing else becomes false.** The only key-block change is P6; the prose changes are only the six places, the new
bullet, and the one collection sentence. The previously verified facts are untouched: B.2 PASS (l.7, l.64), the
H200-layout scheduler dry-run record (l.33, l.92–95), P4 by R1-S2C3-ACCEPT (l.31), the H200
`GPUs_DeviceName` pin with **no site pin** (l.46–47), the pinned image/run_id/layout (key block), and the sealing /
D8 line. `sweep2/` and `r1/` are byte-identical to published `main` on this branch (`git diff df58bcd5..22ecc944
-- sweep2 r1` empty). The branch-level claim "all 16 chunks (all eight nodes) run" is also consistent with the
unchanged "16 chunks (one per (node, memory mode))" layout at l.66.

## 7. Findings (all non-blocking)

- **F1 (minor, wording only).** Two of the six places (launch-commit l.98, "No EVIDENCE launch before" l.116) use
  the short form "the declared R1-S2C3B-WDBC 7/8 shortfall" without the inline "(only openml_wdbc failing, only
  invalid_rate, observed <= 0.30)" qualifier that the header/P6/Liveness/STOP lines carry. The exact shortfall is
  defined twice in the same note (l.73–74, l.77–82) and the row is named, so nothing is stale or broadened; an
  optional tightening for uniform precision.
- **F2 (minor, precision).** l.79 "The STOP record is `ops-s2c3b-launch-stop-20261120`, job 759810" — this is the
  20 Nov pre-launch record at `df58bcd5`; at the new launch commit a **new** C3b record will exist. Optional reword
  to "the STOP record that established this shortfall is …" to avoid pinning the launch-time record by implication.
- **F3 (observation, historical).** The header still says "merged onto published `main` `3a6dcf4d`" while this
  revision is prepared under R1-S2C3B-WDBC and will be published at a later `main`. The round-3 review treated
  the base reference as historical/harmless; no action required.
- **F4 (observation, precision).** l.88–89 groups "all 16 node/memory pairs" (a `collect_evidence` check) with
  `min_live_nodes` 8 (the C3b/spec field). Both values are unchanged and the sentence is not false; optional
  reword.
- **F5 (outside the note — operational text still says 8/8).** `docs/r1/prompts/CLUSTER_SWEEP2_LAUNCH_PROMPT_20261120.md:18`
  ("rerun the S2-C3b liveness at exactly that commit (**8/8 required**)") and
  `sweep2/s2_c5_authorization.template.md:24` ("require 8/8 before submission") remain absolute. They are not the
  note and the PLAN row explicitly amends R1-SWEEP2-AUTH (and the prompt itself says PLAN on `main` wins), but the
  cluster agent should be given the amended instruction / the prompt updated before the rerun; otherwise it may
  STOP on the now-declared 7/8. This is a coordinating-chat action, not a note defect.
- **F6 (publication / launch conditions, all verified as necessary).**
  1. **Publish PLAN row R1-S2C3B-WDBC on `main` with the note.** Verified: the real 7/8 record is refused by both
     driver and switch with `main`'s current PLAN (no row) and accepted once the row is present. Publishing the
     note without the row would leave the note's cited authority absent on `main` and the exception fail-closed.
  2. **Re-render the 16 launch chunk specs at the new launch commit, pinning note sha `349e502b…`.** Verified: a
     spec still pinning `ef4325c5…` STOPs ("spec pins a different authorization note sha256"). The dry-run-report
     edit at `19ea1a22` already states that launch specs are re-rendered at the launch commit.
  3. **Rerun S2-C3b at the new launch commit** (the 20 Nov job 759810 ran at `df58bcd5`); the note's launch-commit
     rule requires the rerun at that commit, reproducing exactly the 7/8 shortfall or 8/8.
  4. **Publish or resolve the cited STOP evidence.** The STOP record lives only on
     `ops-s2c3b-launch-stop-20261120` (not on `main`, not on `author-decisions-20261120b`); prior round-3 review
     recommended publishing branch-only cited evidence with the note, and the same applies here.
  5. **Publish the note bytes exactly** (`349e502b…`, 11,073 B) on `main`; any further edit changes the sha and
     re-opens F6.2.

## 8. What was not done (scope)

No jobs submitted, no `condor_*`, no project pytest run, no git write (only the instructed fetch of the cited
branches), no worktree changes other than this review file. No claim above is based on a test run; all code
conclusions are from reading the committed exception-branch code and re-running its pure functions on the
committed blobs and the real STOP record (stdlib Python only).

---

`VERDICT: ACCEPTED`
