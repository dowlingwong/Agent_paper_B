**AI-assisted (Claude, chat session, 22 Nov 2026; subagent). Revision 4 alignment: AI-assisted (Claude, local worker, 27 Nov 2026). DRAFT; not signed.**

# Authorization: D.3a closed loop on T0, rule arms (EVIDENCE) — DRAFT, NOT SIGNED

Drafted by a subagent of the coordinating chat. Tier E (R1-PROCESS-TIERS). This file authorizes nothing: `approved` stays `false` until the author
signs. Prepared under R1-D3-MIN ("Each stage also needs its authorization note") and R1-MINSUB-CHOICES (4), on branch
`mac-d3-predecl-20261122` over `author-minsub-20261122` @ `d9acb501`. It binds the D.3 pre-declaration by its sha256,
which does not exist yet: the pre-declaration (`D3_PREDECLARATION_DRAFT_20261122.md`) is itself a draft, and its signed
file's sha256 replaces the placeholder below. Every value here is copied from the pre-declaration or from the file it
names; nothing here changes the pre-declaration. Revision 2 follows `docs/r1/reviews/D3_PREDECLARATION_REVIEW_20261122.md` (findings 1, 8, 10 and NOTE 10:
EGATE pin, smoke seeds, P10/P11, chunk count by repetition, the house layout fields). Revision 3 follows the round-2
review `docs/r1/reviews/D3_PREDECLARATION_REVIEW_R2_20261122.md` (smoke node and replicate seeds, P10 outside the
pinned script, the analysis run once). Revision 4 (27 Nov 2026) aligns it with revision 4 of the pre-declaration
(A0R; one GPU model per instance, R1-HOST-FREE (2)(c); infrastructure failures, R1-CARD-SHARE (3) and R1-NO-TIMEOUT;
the 140 GPU-h figure a reporting threshold; D.3b unconditional, R1-D3B-UNCONDITIONAL).

**On signature** the author (or the coordinating chat under an explicit author row) copies this file to
`docs/r1/authorizations/d3a_<YYYYMMDD>.md` with: `approved: true`; `predeclaration_sha256` and every `<pending>` filled;
P1–P11 each PASS with its citation; then publishes it byte-identically on `main`. No D.3a campaign starts before that.

## Key block

```
approved: false
label: EVIDENCE
phase: d3a_closed_loop
run_id: <pending: d3a-<YYYYMMDD>-a>
predeclaration: docs/r1/authorizations/<signed D.3 pre-declaration>.md
predeclaration_sha256: <pending: sha256 of the signed, frozen pre-declaration>
analysis_script: r1/c3/d3_analysis.py
analysis_sha256: <pending: equal to the pre-declaration's §14 value at signing; draft value of revision 4: see the pre-declaration §9>
constants_file_sha256: <pending: the A1/A2/LADDER constants file, pre-declaration §5.0>
arms: A0, A0R, A1, A2, FIXR3, EGATE, LADDER
fixr3: r = 3, one-sided Welch, alpha 0.05
egate: r1/baselines/responses.py PaceStyleGate, alpha 0.1, clip 0.05, max_pairs 8 (as on main)
nodes: digits_mlp, openml_breast_w, openml_climate, openml_credit_approval, openml_ionosphere, openml_sonar, tabular_mlp
instances: 6201-6218 per node (126)
smoke_seeds: 6301-6302 on openml_climate, smoke replicate seeds 6311-6319 and 6321-6329 (ENGINEERING_ONLY, P7)
replicate_seeds: 6500 + 10 i + j, j = 1..9 (6501-6679)
memory_mode: append_only_summary
W: 20
llm_call_cap: 80 (R1-D3-CHOICES (2)); a call issued again after an infrastructure failure is not counted
repetitions: 1 (R1-D3-CHOICES (2))
audit: K = 10, seeds 6700 + 10 i + k (6701-6880), host deepthought CPUs
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296 (proposed; pre-declaration §2)
model_gguf_sha256: 2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75
server: -c 32768 -ngl 999 -np 1 --jinja --chat-template-kwargs {"enable_thinking":false} q8_0 K/V; cache_prompt false on every call
harness_commit: <pending: a3fedbbd44309b3fdf99d853ad841b9ec2c299e2 unless FIXR3/EGATE need a harness change>
paper_commit: <pending: the launch commit>
gpu_model: <pending: per node, a measured model (P7); one GPU model per instance across its arms and stages, R1-HOST-FREE (2)(c)>
layout_chunks: 49 (one chunk per node and arm at one repetition)
layout_request_walltime_s: <pending: 1.5 x the measured chunk time, per arm and GPU model, P7; a scheduler request only, reaching it is an infrastructure failure (R1-NO-TIMEOUT)>
layout_request_disk_kb: <pending: measured peak x 1.4, P7 (the sweep-2 rule)>
layout_request_memory_mb: <pending: measured peak x 1.4 as a floor, P7 (R1-SWEEP2-MEMORY form)>
layout_gpu_hours_projection: <pending: from P7; draft model 96.8 expected / 181.2 worst case at one repetition (layout basis, seven arms)>
layout_wall_hours: <pending: from P7>
projection_reporting_threshold_gpu_hours: 140 (R1-NO-TIMEOUT (3): reported against, reaching it reported to the author; not a STOP)
P1: PENDING — the sweep-2 B.2 audit (s2ev-20261119-a, addendum c3_sweep2_b2_addendum_20261122.md) completed, its run independently reviewed (ACCEPTED) and registered with the author's label-table freeze (R1-SWEEP2-RELEASE-DECISIONS)
P2: PENDING — the sweep-2 train/dev label blocks released under R1-S2-LABELS-TRAINDEV-RELEASE with release.py, receipt sha256 cited (and any further author row the author requires for sweep 2, pre-declaration §13 item 9)
P3: PENDING — the A1, A2 and LADDER constants fitted by the reviewed fitter from the receipted sweep-2 train/dev label partition and the pinned sweep-2 table, filtered to P3 dev instances (PRE-A2 C), the constants file's sha256 entered in the pre-declaration (§5.0, §14) before it is signed
P4: PENDING — the D.3 pre-declaration independently reviewed (ACCEPTED), signed by the author and frozen; its sha256 above
P5: PENDING — the D.3a code units reviewed and merged (pre-declaration §12: G1 runner, A0 change, G11 A0R controller, G2 fitter, G3 FIXR3, G4 EGATE wrapper around PaceStyleGate, G5 LADDER controller, G6 Y audit, G7 outcome-table builder, G8 replicate-run accounting), each with its review path and Code-Commit
P6: PENDING — the harness pin named (a3fedbbd, or a reviewed new pin if G3/G4 change the harness) and the harness-defaults check against the sweep-2 pin recorded
P7: PENDING — a 2-instance ENGINEERING smoke per arm on openml_climate (instance seeds 6301-6302, smoke replicate seeds 6311-6319 and 6321-6329 only) on each GPU model to be used, with working worker runs (gates.worker PASS); measured chunk time per arm; walltime request 1.5 x; projection reported against projection_reporting_threshold_gpu_hours; its outputs set only walltimes and the projection
P8: PENDING — the audit host checks of the pre-declaration §7.2 prepared on deepthought (environment basis = the e1 replay; harness-code equality of the audit harness and the campaign harness; co-tenancy protocol)
P9: PENDING — the author's signature of this note
P10: PENDING — the separate reviewed verify-seed disjointness check of the pre-declaration §4.1 (outside `r1/c3/d3_analysis.py`; its result entered in the pre-declaration before its review) re-run at the launch commit with the same verdict
P11: PENDING — `r1/c3/d3_analysis.py` at the launch commit has the sha256 of the pre-declaration's §14, and `r1/tests/test_d3_analysis.py` passes there (recorded output)
```

## Scope and pins

- **What runs.** Seven arms × seven nodes × 18 instances × the signed number of repetitions, memory
  `append_only_summary`, W = 20, the signed LLM-call cap, trial budget equal to the cap; seeds, arms, outcome and
  analysis exactly as the pre-declaration fixes them (§2–§9). The harness `campaign_id` of every campaign is its
  instance id, so all arms of an instance share the D26 seed stream; each (arm, repetition) has its own ledger root
  (pre-declaration §4.1).
- **Proposer host.** Any host and GPU model that fits and passes its environment check (R1-HOST-FREE (1)); every
  chunk of a node runs on that node's measured GPU model, so all arms of an instance (and its D.3b arms later) share
  one model (R1-HOST-FREE (2)(c)); cards may be shared (R1-CARD-SHARE); every campaign records host, GPU model and
  UUID, driver, CPU model, environment freeze and the other compute processes on its card at start and end.
- **Infrastructure failures** (pre-declaration §3.1): never an outcome, never a STOP, attempts unlimited; a lost chunk
  is rerun whole in a new directory on the same GPU model, nothing of the lost attempt charged.
- **Audit host.** deepthought CPUs (R1-MINSUB-CHOICES (4)), under the four conditions of R1-SWEEP2-B2-GO as the
  pre-declaration §7.2 applies them; 16 workers, at least 10 of 40 cores free, `cotenancy.log`.
- **Data read.** The constants file (from the sweep-2 dev label block) and the pinned noise source; no test label, no
  evaluation value, no T1 label; no D.3a output trains, tunes or selects any arm (R1-D3-MIN).
- **Outputs.** Sealed per chunk with `SHA256SUMS` as sweep 2; the outcome table (`r1_d3_outcome/v2`) built only from a
  complete design; the analysis run **once** by `r1/c3/d3_analysis.py` with `--d3b-not-run not_started`. A later D.3b analysis recomputes the D.3a family only as a reproduction check that must equal this
  run exactly (pre-declaration §9); the D.3a result is this run's.
- **Compute (pre-declaration §11).** Proposer ≈ 96.8 GPU-h expected, ≈ 181.2 GPU-h worst case on the layout basis, and
  ≈ 19.1 / 35.8 GPU-h on the realised sweep-2 chunk time (both replaced by P7); primary audit ≤ 10,080 seed runs,
  ≈ 13.1 worker-hours, ≈ 49 min at 16 workers, plus the Y(w) and kept-incumbent audits of the secondary outcomes.
- **Not authorized.** D.3b (runs whether or not the gate passes, R1-D3B-UNCONDITIONAL, but needs the arms-frozen record and its own note); the HPO-REF rows (their own note); D.3c; `openml_wdbc`; any T1 node; any other memory
  mode; any resume of a stopped or lost chunk (a lost chunk is rerun whole); any change to the arms after launch.

## Boundaries and STOPs

All STOPs of the pre-declaration §10 apply. In addition: no EVIDENCE launch before `approved: true`, P1–P11 all PASS and
this note published byte-identically on `main`; a launch commit whose authority files (PLAN, `authorizations/`) differ
from published `main`; a pin of the key block differing from the job record. On a STOP the stage is reported as
stopped, with no contrast computed from a partial design (pre-declaration §10).
