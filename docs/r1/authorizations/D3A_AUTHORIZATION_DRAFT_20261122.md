**AI-assisted (Claude, chat session, 22 Nov 2026; subagent). DRAFT; not signed; not reviewed.**

# Authorization: D.3a closed loop on T0, rule arms (EVIDENCE) — DRAFT, NOT SIGNED

Drafted by a subagent of the coordinating chat. Tier E (R1-PROCESS-TIERS). This file authorizes nothing: `approved` stays `false` until the author
signs. Prepared under R1-D3-MIN ("Each stage also needs its authorization note") and R1-MINSUB-CHOICES (4), on branch
`mac-d3-predecl-20261122` over `author-minsub-20261122` @ `d9acb501`. It binds the D.3 pre-declaration by its sha256,
which does not exist yet: the pre-declaration (`D3_PREDECLARATION_DRAFT_20261122.md`) is itself a draft, and its signed
file's sha256 replaces the placeholder below. Every value here is copied from the pre-declaration or from the file it
names; nothing here changes the pre-declaration.

**On signature** the author (or the coordinating chat under an explicit author row) copies this file to
`docs/r1/authorizations/d3a_<YYYYMMDD>.md` with: `approved: true`; `predeclaration_sha256` and every `<pending>` filled;
P1–P9 each PASS with its citation; then publishes it byte-identically on `main`. No D.3a campaign starts before that.

## Key block

```
approved: false
label: EVIDENCE
phase: d3a_closed_loop
run_id: <pending: d3a-<YYYYMMDD>-a>
predeclaration: docs/r1/authorizations/<signed D.3 pre-declaration>.md
predeclaration_sha256: <pending: sha256 of the signed, frozen pre-declaration>
analysis_script: r1/c3/d3_analysis.py
analysis_sha256: <pending: equal to the pre-declaration's §14 value at signing; draft value e16e4f2e2a6e1e4464c6049cb640e877e8196379352fca215f7f0a8d5eb47f84>
constants_file_sha256: <pending: the A1/A2/LADDER constants file, pre-declaration §5.0>
arms: A0, A1, A2, FIXR3, EGATE, LADDER
nodes: digits_mlp, openml_breast_w, openml_climate, openml_credit_approval, openml_ionosphere, openml_sonar, tabular_mlp
instances: 6201-6218 per node (126)
memory_mode: append_only_summary
W: 20
llm_call_cap: <pending: the signed value; proposed 80>
repetitions: <pending: the signed value; proposed 1>
audit: K = 10, seeds 6700 + 10 i + k (6701-6880), host deepthought CPUs
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296 (proposed; pre-declaration §2)
model_gguf_sha256: 2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75
server: -c 32768 -ngl 999 -np 1 --jinja --chat-template-kwargs {"enable_thinking":false} q8_0 K/V; cache_prompt false on every call
harness_commit: <pending: a3fedbbd44309b3fdf99d853ad841b9ec2c299e2 unless FIXR3/EGATE need a harness change>
paper_commit: <pending: the launch commit>
gpu_model: <pending: the measured model, P7>
layout_chunks: 42 (one per node and arm)
layout_request_walltime_s: <pending: 1.5 x the measured chunk time, per arm, P7>
layout_gpu_hours_projection: <pending: from P7; draft model 76.7 expected / 135.9 worst case>
projection_stop_gpu_hours: <pending: proposed 140>
P1: PENDING — the sweep-2 B.2 audit (s2ev-20261119-a, addendum c3_sweep2_b2_addendum_20261122.md) completed, its run independently reviewed (ACCEPTED) and registered with the author's label-table freeze (R1-SWEEP2-RELEASE-DECISIONS)
P2: PENDING — the sweep-2 train/dev label blocks released under R1-S2-LABELS-TRAINDEV-RELEASE with release.py, receipt sha256 cited (and any further author row the author requires for sweep 2, pre-declaration §13 item 9)
P3: PENDING — the A1, A2 and LADDER constants fitted by the reviewed fitter on the sweep-2 dev label block only (PRE-A2 C), the constants file's sha256 entered in the pre-declaration (§5.0, §14)
P4: PENDING — the D.3 pre-declaration independently reviewed (ACCEPTED), signed by the author and frozen; its sha256 above
P5: PENDING — the D.3a code units reviewed and merged (pre-declaration §12: G1 runner, A0 change, G2 fitter, G3 FIXR3, G4 EGATE, G5 LADDER controller, G6 Y audit, G7 outcome-table builder), each with its review path and Code-Commit
P6: PENDING — the harness pin named (a3fedbbd, or a reviewed new pin if G3/G4 change the harness) and the harness-defaults check against the sweep-2 pin recorded
P7: PENDING — a 2-instance ENGINEERING smoke per arm on the GPU model to be used, with working worker runs (gates.worker PASS); measured chunk time per arm; walltime 1.5 x; projection at or below projection_stop_gpu_hours
P8: PENDING — the audit host checks of the pre-declaration §7.2 prepared on deepthought (environment basis = the e1 replay; harness-code equality of the audit harness and the campaign harness; co-tenancy protocol)
P9: PENDING — the author's signature of this note
```

## Scope and pins

- **What runs.** Six arms × seven nodes × 18 instances × the signed number of repetitions, memory
  `append_only_summary`, W = 20, the signed LLM-call cap, trial budget equal to the cap; seeds, arms, outcome and
  analysis exactly as the pre-declaration fixes them (§2–§9). The harness `campaign_id` of every campaign is its
  instance id, so all arms of an instance share the D26 seed stream.
- **Proposer host.** HTCondor GPU jobs, one GPU model for the stage (and for D.3b), not the TASL pair (R1-D3-MIN
  "Hosts"); the job requirements pin the measured GPU model; every campaign records site, node, GPU model and UUID,
  driver and CPU model (as the sweep-2 note requires).
- **Audit host.** deepthought CPUs (R1-MINSUB-CHOICES (4)), under the four conditions of R1-SWEEP2-B2-GO as the
  pre-declaration §7.2 applies them; 16 workers, at least 10 of 40 cores free, `cotenancy.log`.
- **Data read.** The constants file (from the sweep-2 dev label block) and the pinned noise source; no test label, no
  evaluation value, no T1 label; no D.3a output trains, tunes or selects any arm (R1-D3-MIN).
- **Outputs.** Sealed per chunk with `SHA256SUMS` as sweep 2; the outcome table (`r1_d3_outcome/v1`) built only from a
  complete design; the analysis run once by `r1/c3/d3_analysis.py` with `--d3b-not-run` until D.3b exists.
- **Compute (pre-declaration §11).** Proposer ≈ 76.7 GPU-h expected, ≈ 135.9 GPU-h worst case (model from the sweep-2
  H200 chunk, replaced by P7); audit ≤ 8,820 seed runs, ≈ 11.5 worker-hours, ≈ 43 min at 16 workers.
- **Not authorized.** D.3b (needs the gate's pass and its own note); `openml_wdbc`; any T1 node; any other memory
  mode; any resume of a stopped chunk; any change to the arms after launch.

## Boundaries and STOPs

All STOPs of the pre-declaration §10 apply. In addition: no EVIDENCE launch before `approved: true`, P1–P9 all PASS and
this note published byte-identically on `main`; a launch commit whose authority files (PLAN, `authorizations/`) differ
from published `main`; a pin of the key block differing from the job record. On a STOP the stage is reported as
stopped, with no contrast computed from a partial design (pre-declaration §10).
