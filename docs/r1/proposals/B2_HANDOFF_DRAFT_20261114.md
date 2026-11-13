# Track X Stage B2 hand-off — DRAFT, NOT ARMED (14 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local agent), MAC_OVERNIGHT_RUNBOOK_20261113 Unit 5. **This draft is not armed.**
It authorizes nothing, starts nothing and is not an author decision. It becomes usable only when the author has read
the B1 report of the running `_d` run and approves B2 in writing (§0). Every ⟨…⟩ field is a placeholder to be filled
from B1's accepted result or by the author; none may be guessed.

**Sources** (read from `ops-b1-restart-d-20261113` @ `7912b7ff`, the `_d` run HEAD, unless stated otherwise):
- RUNBOOK X.6 and X.7 (`docs/r1/RUNBOOK.md`, Track X table);
- `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md` Phase 6 and STOP 6;
- `docs/r1/proposals/B1_RESTART_HANDOFF_D_20261113.md` (pattern of preconditions, reviewed base, run-HEAD note,
  author gate, occupancy check, preflight, handover, marker transition);
- `r1/exam/rules/x5_rule_v2.yaml` (sha256 `53018aa7…16ad`), `r1/scripts/configs/exam_b2_v2.json`,
  `r1/scripts/exam_runner.py`, `r1/exam/runtime.py`, `r1/exam/campaign.py`, `r1/exam/analyze.py`;
- PLAN §10 rows R1-EXAM-PROTOCOL, R1-EXAM-HOST-B1B2-TASL7 (4 Nov 18:10), R1-MAIN-PROPOSER, R1-BX-D6-EXAM-RUNNER-UP,
  R1-SCHEMA, R1-EXAM-CACHE-REV, R1-EXAM-B1-HARNESS-PIN, R1-EXAM-A1-M1-REQUIREMENTS, R1-PORTAL-SCHEDULE,
  R1-TRACKX-MARKER, R1-EXAM-B1-TRUNCATION-INVALID, R1-EXAM-B1-MODEL-OUTPUT-INVALID;
- `docs/r1/reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md` §3 (M1–M21) and §5;
- `docs/r1/proposals/B2_GRID_VERIFIER_DESIGN_20261104.md` (on `mac-b1-20261107`);
- the `_c` post-run marker unit `docs/r1/proposals/B1_C_POSTRUN_RETIREMENT_20261112.md` (rev 5, `78c6fd7d`, on
  `trackS-ops-20261030`; not on `7912b7ff`), and the review candidates on `trackS-ops-20261030` @ `d7992019` that
  govern B1's normal end: the `_d` post-run unit `docs/r1/proposals/B1_D_POSTRUN_RETIREMENT_20261113.md` (rev 2,
  `491e1241`) and the Track S S0.5 resume unit `docs/r1/proposals/TRACKS_S05_T7_RESUME_20261114.md` (rev 2);
- `r1/scripts/b1_o2_marker.py` (marker tool).

## 0. Not armed — what arms it

B2 may start only when **all** of these hold. Until then, do nothing and report.

1. B1 run `7912_20261113_d` (or its successor) ended **normally**, its report and review loop (PORTAL_EXAM_RUNBOOK
   STOP 5: the reviewer recomputes the finalists from the manifests and checks the rule hash) are done, and the
   author has read the report.
2. The author approves B2 in a PLAN §10 row and commits a B2 authorization note
   `docs/r1/authorizations/trackx_b2_⟨YYYYMMDD⟩.md` whose JSON block binds `"author": "Dowling Wong"`,
   `"phase": "b2"`, `"approved": true` and `"rule_sha256": "53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad"`
   (the fields `runtime.author_gate` reads for every phase), plus the B2 bindings `author_gate` reads for b2 at
   `7912b7ff` (l. 429–440): `nodes`, `stage_a_table_sha256`, the Stage A amendment table and acceptance shas,
   `b1_analysis_sha256` (§1), `llm_call_cap` and `instances_per_node` (§2); and the host, GPU UUID, `workers` and
   anchor-reference bindings that B1's gate checks (l. 441–458) and that the B2 code unit (§0.3) is to add for b2.
   No agent sets `approved: true`.
3. **The B2 code path exists and is accepted.** At `7912b7ff` B2 cannot run; at least these places STOP on purpose:
   - `exam_runner.main` (l. 515–516): `STOP: B2 reviewed observer integration is not implemented` (any
     non-`--check-config` b2);
   - `exam_runner.evidence` (l. 328–330): `STOP: only x5_rule/v2 B1 evidence is implemented`;
   - `ExamRunner.start` (`runtime.py` l. 594–595): the same STOP as `main`;
   - `campaign.collect` (l. 171–173): `STOP: B2 observer integration is not implemented`, and behind it
     `campaign._collect_b1_review` (l. 208): `STOP: B1 candidate refuses other phases`;
   - `runtime.author_gate` (l. 425–426): `STOP: X5 v2 B2 authority and ranking are not implemented`;
   - and `analyze` B2 ranking (l. 325): `STOP: B2 node/instance grid has not been verified against the
     author-bound power plan` (the B2 grid verifier of `B2_GRID_VERIFIER_DESIGN_20261104.md` is proposed, not built).

   A separate engineering unit, independently reviewed, must give B2 the same protections B1 has — at `7912b7ff`
   most of them are gated on `phase == 'b1'` (`runtime.py` l. 596–651, 900–934): committed-config and registry
   checks, the authority HEAD binding of each root, worker environment, fresh-batch-only creation (l. 611–619), the
   cooperative GPU lease `~/r1_locks/gpu0.lock` (l. 648–650), the runner lock (l. 651), harness-source hashes,
   "an existing production root is preserved, never resumed automatically", and the author gate's host, GPU, workers
   and anchor bindings (l. 441–458); and, in `campaign._collect_b1_review` (l. 292–295), the model-output pre-check,
   the proposal journal, the observer journal and `cache_prompt` evidence. The marker tool `b1_o2_marker.py create`
   writes the STATUS heading `Track X B1 running` (l. 48), so B2 needs the phase parameterised or a reviewed B2
   equivalent. That unit is **not** part of this draft.
4. **The author adopts the invalid-trial rules for B2.** `R1-EXAM-B1-TRUNCATION-INVALID` (PLAN l. 1141) and
   `R1-EXAM-B1-MODEL-OUTPUT-INVALID` (l. 1147) are in PLAN at `7912b7ff` but scoped to B1. Extending them to B2 is the
   author's decision, in a PLAN row; §6 lists them as **proposed for B2**.
5. The STOPs of §6 are carried over by that code, with tests showing each one fires in phase `b2`.

## 1. Inputs from B1's accepted result (placeholders)

| Input | Value | Source |
|---|---|---|
| B1 run ID, run HEAD | ⟨7912_20261113_d⟩, ⟨7912b7ff…⟩ | B1 report |
| B1 analysis file and its sha256 (`b1_analysis`, `b1_analysis_sha256`) | ⟨path⟩, ⟨sha256⟩ | `analyze.py b1` under `x5_rule_v2` |
| Ranking by pooled thinking-off audited μ̂ (rule `ranking_mode: "off"`) | ⟨ordered list⟩ | B1 analysis |
| Finalists: top 4 + best of an absent family, ≤ 5; ties in registry order | ⟨ids⟩ | B1 analysis (`finalists`) |
| Each finalist's B2 mode | `"off"` (the runner STOPs on any other `b2_thinking_mode`) | rule `b2_mode` |
| Top 3 for the thinking-on rerun (descriptive only) | ⟨ids⟩ | B1 ranking |
| B1 variance used for the power plan | ⟨table⟩ | to be computed by a reviewed script or the author: `analyze b1` at `7912b7ff` gives only a per-candidate pooled `increment_sd` (l. 190), no per-node or final-Y variance |
| D28 node actually used (`digits_mlp` or `tabular_mlp`) | ⟨digits_mlp⟩ | B1 config at the run HEAD names `digits_mlp` |
| Template repairs carried into B2 (R1-EXAM-A1-M1-REQUIREMENTS (1)) | as in `exam_b2_v2.json` `template_repairs`, for any finalist among `olmo31_32b`, `devstral_small2_24b`, `ministral3_14b` | config |
| Anchor duplicate reference | ⟨B1's `B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json`, sha `84200770…85dd`, or a new author value⟩ | author |

## 2. B2 values the author sets (placeholders)

| Key in `exam_b2_v2.json` | At `7912b7ff` | Needed |
|---|---|---|
| `b2_instances_per_node` | `TODO_AUTHOR_B2_POWER_PLAN` | ⟨n⟩, fixed from the B1 variance before B2 (RUNBOOK X.6); the rule says only `b2_instances: author_decision_from_b1_variance` and no power-plan rule is declared yet, so the rule itself goes into the author's PLAN row; the code allows 1 ≤ n ≤ 89 (namespace 9011–9099, `runtime.py` l. 438) |
| instance seeds | (code) `range(9011, 9011 + n)` (`exam_runner.py` l. 405); the config's `instance_seeds` 9001–9004 are B1's and are not read for b2 | fresh, disjoint from 9001–9004 |
| audit seeds | (code) `range(9201, 9211)`, K = 10 (`runtime.py` l. 924; `analyze` refuses anything else for final Y, l. 267, 281); the config's `audit_seeds` 9101–9104 are B1's and are not read for b2. At `7912b7ff` the b2 job passes 9201–9210 to **every** per-proposal paired audit too, not only to the final-Y audit (post-campaign, so no leakage into selection), i.e. 2 × 10 instead of B1's 2 × 4 seed runs per audited proposal, which counts in GPU-h (the tie-break) | the code unit or the author confirms this is intended |
| `nodes` | `TODO_VERIFY_D28_DIGITS_OR_TABULAR`, credit_approval, ionosphere | the three B1 nodes |
| `llm_call_cap` | `TODO_AUTHOR_LLM_CALL_CAP` | ⟨80 as in B1, or author value⟩ |
| `workers` | 4 | ⟨20 as in B1 for TASL-7's 24 logical CPUs, or author value⟩ |
| `paper_commit` | `TODO_REVIEWED_M2_COMMIT` | the reviewed B2 code commit (re-pin rule) |
| `anchor_duplicate_reference` | `TODO_VERIFY_ON_HOST` | §1 |
| `authorizations.b2` | `TODO_AUTHOR_B2_V2_AUTHORIZATION_NOTE` | §0.2 |
| `d22_pick` | `TODO_AUTHOR_D22_PICK` | only for the schema-vs-free sensitivity, which can run only after the pick exists (§3.4) |
| Track G node | none | only if G.1 and G.3 are done, it runs on the same host beside the manager within the fit rule, and the author adds it (X.6) |

Unchanged from B1 and bound by sha: host TASL-7 and GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`
(R1-EXAM-HOST-B1B2-TASL7: the whole exam on one host), harness `a3fedbb` (R1-EXAM-B1-HARNESS-PIN),
`cache_prompt: false` on every request (R1-EXAM-CACHE-REV), context 32,768, q8_0 KV, temperature 0.2, schema
`manager_proposal/v1`, W = 20, memory `append_only_summary`, `vary` split, the Stage A tables and acceptance record,
llama.cpp `620d222` binary sha `b70f4882…7d8b`; and, if the author adopts them for B2 (§0.4), the 16,384 completion
cap of R1-EXAM-B1-TRUNCATION-INVALID and the model-output rules of R1-EXAM-B1-MODEL-OUTPUT-INVALID. At `7912b7ff` the
host and GPU bindings are enforced for b1 only (§0.3).

## 3. What B2 computes

1. **Primary:** every finalist, thinking off, on the three nodes × n fresh instances (9011…), W = 20; at the end of
   each root the incumbent's editable files are audited on seeds 9201–9210 and `final_y` is the mean of the ten
   metrics (`campaign.py` l. 306–311 at `7912b7ff`). An incomplete final-Y audit STOPs.
2. **Ranking (X.7 (a)):** best thinking-off B2 final audited Y, ties to lower GPU-h (rule `selection`), computed by
   `analyze` only after the grid verifier confirms each finalist covers exactly the author-bound grid.
3. **Top-3 rerun:** thinking on, descriptive only (`thinking_on_rerun: descriptive`); it never changes the pick.
   This departs from the text of RUNBOOK X.6 ("rerun once with thinking off", "zhixu portal") and Phase 6 ("other
   thinking mode"), which R1-MAIN-PROPOSER, R1-EXAM-RULE-X5V2 (B2 thinking off for every finalist) and
   R1-EXAM-HOST-B1B2-TASL7 (the whole exam on TASL-7) supersede.
4. **Second proposer (R1-BX-D6-EXAM-RUNNER-UP, proposed consequence):** ranked by the same B2 Y, different family
   from the pick; read from the B2 table, no extra run.
5. Report `docs/r1/reports/PROPOSER_EXAM_⟨date⟩.md`; review loop in which the reviewer recomputes every table
   from the manifests (STOP 6); then the author decides X.7.
6. **Schema sensitivity (R1-SCHEMA), after X.7 (a):** one node (`openml_credit_approval`), free generation vs schema,
   for the 7B anchor and the D22 pick (`--free-sensitivity`, which needs a PLAN line naming D22 and the pick,
   `exam_runner.py` l. 362–363). It runs only after the author records the pick, and goes into an addendum to the
   B2 report.

## 4. Procedure (pattern of hand-off `_d`)

1. **Reviewed base.** The B2 code unit (§0.3) has a review file whose last accepted round names the
   `Accepted commit:`. The `Reviewed base:` line of that file and `Claude outputs/READY.txt` name the same SHA; if
   the three disagree, STOP. Later commits may only add review records. The protected-path diff
   (`r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py
   r1/headroom/e1b_collect.py`) between the pinned `paper_commit` and the base is empty.
2. **Run HEAD.** One new commit on the reviewed base, on a new branch `ops-b2-⟨YYYYMMDD⟩`, changing only the prose of
   the B2 authorization note's context (name the B1 run, the reviewed base, this hand-off); JSON bindings
   byte-identical. Exact-HEAD independent review, then the **real author gate** on it. Push without force.
3. **Stage** the checkout clean on TASL-7 as for B1 (`b1_paper_final_<FULL_HEAD>/paper` pattern, B2 name), harness at
   `b1_harness_offline_stage_20261107_a/harness` (`a3fedbb`); frozen venv as in hand-off `_d` §0.3, else STOP.
4. **Fresh checks, each re-reviewed for the new HEAD and run ID:** TASL-7 read-only occupancy check; host preflight
   (`proposals/B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md` pattern) with a new absent `--out` and a new capture
   directory; the handover (`B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` with the command-boundary report). Do not
   preempt other users' work (R1-TASL7-AGENT-OCCUPANCY-07NOV).
5. **Run ID** `⟨first four hex of run HEAD⟩_⟨UTC date⟩_b2`, output tree `/home/dowling/exam-x/work/b2_<run ID>`.
   Nothing of B1's runs (`_a`, `_b`, `_c`, `_d`) is moved, overwritten or deleted.
6. **STATUS** on `mac-b1-20261107` (or the branch the author names): `## <date> — Track X B2 running`, then
   `B2 done` or `B2 stopped` (R1-PORTAL-SCHEDULE).
7. **Send back:** run ID and checkout SHA, the HEAD review, the author-gate receipt, preflight and handover receipts
   with the marker receipts, the first monitor capture.

## 5. Marker transition (Track X evidence marker `~/r1_locks/trackx_evidence.active`)

This section describes the sequence B2 depends on; **it does not authorize retiring any marker.** Each step is done
only under its own reviewed and accepted unit.

- **After B1's normal end:** the `_d` marker is retired by the `_d` post-run unit
  (`B1_D_POSTRUN_RETIREMENT_20261113.md`, rev 2, `491e1241`, a review candidate on `trackS-ops-20261030`, adapted from
  the accepted `_c` unit `78c6fd7d`), and only once that unit is accepted. It renames the marker into
  `~/r1_locks/_to_delete/` with its creation receipt (nothing deleted) and writes `*_after_run.*` receipts in the `_d`
  handover directory. If B1 ended in a STOP, that unit does not apply: preserve and report.
- **Between B1 and B2** the card is used by others: the Track S S0.5 resume unit (`TRACKS_S05_T7_RESUME_20261114.md`,
  rev 2, review candidate) resumes Track S `digits_mlp` S0.5 on TASL-7 right after the `_d` marker is retired, and
  P.3a may run between B1 and B2 (R1-EXAM-HOST-B1B2-TASL7).
- **At B2 start, before the new marker is created**, all of these must hold, otherwise STOP and report:
  Track S has reached a safe pause (its collector stopped at a unit boundary, its `trks_llm` servers stopped, the
  `trks_watch` watcher paused or reading the new marker) under a reviewed Track S pause procedure; P.3a is at its safe
  pause; no Track S, Track P or other GPU job is running (`nvidia-smi` lists no compute app); `flock -n
  ~/r1_locks/gpu0.lock true` succeeds. Track X never preempts another user's or track's running job
  (R1-TASL7-AGENT-OCCUPANCY-07NOV); the timing is agreed with the author.
- **Creating the B2 marker:** with the reviewed B2 marker tool (§0.3: `b1_o2_marker.py create` writes a B1 heading),
  receipt kept in the B2 handover directory. Track P and Track S stay paused for all of B2.
- **After the last B2 job** (or when B2 is stopped for good): retire the B2 marker the same way, by rename with its
  receipt, under its own reviewed post-run unit.
- If a marker does not match its receipt, STOP.

*Relation to R1-PORTAL-SCHEDULE.* That row describes one marker, created before the first B1 job and removed after
the last B2 job. Since the B1 restarts the author has treated the marker as a cooperative lock, renamed with its
receipt at each transition (PLAN `R1-EXAM-B1-TRUNCATION-INVALID` rationale), and R1-EXAM-HOST-B1B2-TASL7 lets P.3a
run between B1 and B2; a gap between the `_d` marker and the B2 marker follows from that, and the marker exists
whenever a B1 or B2 job runs.

## 6. STOPs carried over from B1

**Proposed for B2** (they become B2 rules only if the author adopts them, §0.4): as B1 after
R1-EXAM-B1-MODEL-OUTPUT-INVALID (diagnosis §3), model-output faults become **invalid trials, not STOPs**: M5–M9
(directive missing; directive symbol not editable or different; old or new value different; backslash in a value;
`.py` value too long, not a literal, or not a finite number), a prompt beyond the context **after** trial 1 (M19), a
reply whose summary cannot be encoded for the next request (M20); and, as R1-EXAM-B1-TRUNCATION-INVALID, a truncated
reply (M2) under the 16,384-token cap; every proposal journalled before execution; per-check rejection counts in the
B2 report.

These **still STOP** and are preserved and reported, never retried: M19 **at trial 1**; any proposal that reaches the
worker guard and fails it (an internal inconsistency once the pre-check exists); M10 (edit path ≠ editable file);
M15 (observer timeout — 60 s at `7912b7ff`; a 180 s standby patch is reviewed on `mac-b1-obs180-20261113` but applies
only if the author adopts it); M16 (post-campaign replay failure); M17 (an executed configuration fails or is
non-finite on an audit seed — for B2 this includes any of the ten final-Y seeds 9201–9210); M18 (LLM transport
failure); M21 (12 h root deadline); an incomplete final-Y audit; missing `cache_prompt` evidence; any pin, sha,
authority or host mismatch; and any existing production root found on restart. M14 (out-of-declared-range
`digits_mlp` value) executes as in B1. The open author questions of diagnosis §5 (observer timeout, audit-seed
failure, declared ranges) carry into B2 unchanged.

B2, X.7 and sweep 2 remain separately gated.
