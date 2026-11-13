# B1 post-hoc changes — appendix disclosure drafts (14 November 2026)

**Status.** Draft for the paper appendix. AI-assisted (Claude, Mac-local agent), MAC_OVERNIGHT_RUNBOOK_20261113
Unit 6. Not an author decision. It brings the three post-hoc changes to Track X Stage B1 into one place, with the
same five parts for each: the original criterion, the trigger, the change, its date and PLAN row, and what it cannot
affect. Fields in ⟨…⟩ are filled from the B1 report of run `7912_20261113_d` (or its successor) once that run has
ended; no count is guessed here.

**Sources.** PLAN §10 rows and the three earlier per-change drafts are read from `ops-b1-restart-d-20261113` @
`7912b7ff` (the `_d` run HEAD): `reports/B1_GATE_AMENDMENT_DRAFT_20261109.md`,
`reports/B1_TRUNCATION_APPENDIX_DRAFT_20261111.md`, `reports/B1_MODEL_OUTPUT_APPENDIX_DRAFT_20261113.md`,
`reports/B1_TRUNCATION_DIAGNOSIS_20261111.md`, `reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md`. The three STOP
reports are on `mac-b1-20261107` @ `1e5728f9`: `reports/B1_STOP_6835_20261108.md`,
`reports/B1_STOP_FFFA_20261111.md`, `reports/B1_STOP_4B31_20261112.md`. The earlier drafts stay the detailed record;
this file does not replace them.

**Common facts.** B1 ran on TASL-7 under the frozen rule `x5_rule_v2` (sha256 `53018aa7…16ad`), unchanged by all
three changes. Each change came after a STOP and before any candidate result had been used; each run was restarted
from the start in a fresh output tree, the stopped trees preserved. Runs: `6835_20261108_a` (stopped 8 Nov),
`fffa_20261111_b` (11 Nov), `4b31_20261112_c` (13 Nov), `7912_20261113_d` (running at the time of writing).

---

## 1. Anchor ordering made descriptive (R4, extended to H2)

**Original criterion.** RUNBOOK X.3: random-valid < scripted on the audited mean proposal increment (paired instance
bootstrap over 12 instance pairs, 3 nodes × seeds 9001–9004, 2000 resamples, seed 20261026, STOP if the lower 95 %
bound ≤ 0), and the `qwen2.5-coder:7b` duplicate rate inside its pinned interval [0.4239, 0.5800]. "If the exam
cannot order the anchors, STOP." Fixed before Stage A; never exercised on real data before 8 Nov (DRYRUN overrides it).

**Trigger.** Run `6835_20261108_a`, 8 Nov 2026 01:19:49 UTC, after the 36 anchor roots and before any candidate:
`STOP: random-valid < scripted cannot be shown` (`reports/B1_STOP_6835_20261108.md`). scripted − random_valid = +0.0046,
95 % [−0.0006, +0.0089]; 7B duplicate rate 120 / 242 = 0.4959 (inside). Diagnosis `reports/B1_STOP_DIAGNOSIS_20261111.md`
(branch `mac-b1-diag-report-20261111`): class D resting on H2 alone (the random-valid anchor's increment falls from
the first to the second half of its roots, driven by `digits_mlp`), H1 not supported, D7 PASS.

**Change.** The anchor-ordering STOP is removed. The difference is still computed and recorded as a descriptive
field (`scripted_minus_random`, role `descriptive_only`). The 7B duplicate-rate STOP and its interval are kept. Added:
a descriptive first- vs second-half increment table for every candidate and anchor (`r1/scripts/b1_candidate_halves.py`),
used by no ranking, finalist choice or STOP. No replacement ordering gate was chosen.

**Date and PLAN row.** 9 Nov 2026, `R1-EXAM-B1-ANCHOR-R4` (conditional on a class-D design verdict); 11 Nov 2026,
`R1-EXAM-B1-ANCHOR-R4-H2` (condition becomes class D with H1 or H2, and D7 PASS). Code `fb57c6a4`, re-pin `4542360e`.

**What it cannot affect.** No candidate had run when the change was made. It removes a STOP; it does not change any
quantity that enters the ranking, the finalist rule, the 7B check, seeds, budgets, nodes or pins. It does bear on how
the ranking quantity is read: `pooled_audited_mean_proposal_increment` is the same incumbent-relative increment in
which H2 was seen, which is why the halves table is reported for every candidate.

**_d values.** scripted − random_valid in `_d`: ⟨value, 95 % interval⟩; 7B duplicate rate: ⟨k / n⟩; candidates whose
second-half increment falls by more than ⟨…⟩ σ_joint: ⟨list or "none"⟩.

---

## 2. Truncated replies are invalid trials; 16,384-token completion cap

**Original criterion.** The pre-registered procedure did not say what happens to a reply cut short. In the code, the
OpenAI SDK's structured-output parser raised `LengthFinishReasonError`, the harness logged `llm_call_failed` and
re-raised, and the root worker exited, which stopped the batch. No completion cap was sent.

**Trigger.** Run `fffa_20261111_b`, 11 Nov 2026 13:51:09 UTC: a `qwen36_27b` thinking-on reply
(`openml_credit_approval` s9001, trial 13) filled the 32,768-token context with 31,551 completion tokens against a
2,048-token thinking budget; 64 roots had completed (`reports/B1_STOP_FFFA_20261111.md`; diagnosis
`reports/B1_TRUNCATION_DIAGNOSIS_20261111.md`).

**Change.** (1) A reply ending with finish reason `length` or `content_filter` is an invalid proposal: text discarded
even if part would parse, recorded as an invalid trial (`parse_failed`, no worker run), charged to the LLM-call budget,
campaign continues; every other LLM-call failure stays a STOP. (2) Every proposer call carries
`max_completion_tokens = 16384`, fixed before the stopped run's per-call usage was read and then checked to exceed the
largest completion of every completed root (largest 2,178 tokens).

**Date and PLAN row.** 11 Nov 2026, `R1-EXAM-B1-TRUNCATION-INVALID`. Code `1334c616`, re-pin `62adc6a3`.

**What it cannot affect.** No reply of the 64 completed roots of `fffa_20261111_b` would have been cut by the cap.
Models, quantisations, server build and flags (including the 2,048-token thinking budget), prompts, schema, seeds,
budgets, nodes, `x5_rule_v2` and its analysis are unchanged. A truncated reply lowers a candidate's valid-proposal rate;
it reaches the audited μ̂ only through which proposals are audited. A root whose calls all end at the cap can still
reach the unchanged 12 h root deadline, which stays a STOP.

**_d values.** Per candidate and mode: ⟨candidate, mode, proposer calls, truncated, share⟩; largest completion per
thinking-on candidate: ⟨…⟩; whether the 2,048 thinking budget took effect for every thinking-on candidate: ⟨…⟩.

---

## 3. Model-output STOPs become invalid trials; proposal journal

**Original criterion.** A proposal states its edit twice: a free-text objective (which the worker executes) and
structured fields (which ledger, replay and audits use). The worker guard stopped the batch when the two disagreed or
the value could not be inserted safely. Some other model outputs also ended the run: a prompt beyond the context, and
a reply whose summary would make later requests unencodable.

**Trigger.** Run `4b31_20261112_c`, 13 Nov 2026 03:01:55 UTC, after 89 completed roots: in
`olmo31_32b` / `openml_credit_approval__s9002` trial 020 the objective's directive and the structured edit differed
(`reports/B1_STOP_4B31_20261112.md`). Trials 018/019 had asked for the same impossible `model_type` change with
agreeing descriptions and were rejected by the node (`invalid_config`). Diagnosis and inventory of every model-output
STOP: `reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md` §3 (M1–M21).

**Change.** Of the 21 inventoried cases, three groups:
- **Turned from STOP into invalid trial** (not executed, charged its LLM call, reason kept): M5–M9 (directive missing;
  directive symbol not editable or different; old or new value different; backslash in the value; `.py` value too
  long, not a literal or not finite), M19 (prompt beyond the context, after trial 1; at trial 1 it stays a STOP),
  M20 (lone surrogate in the reply's summary).
- **Already invalid trials, unchanged:** M1 (parse failure), M2 (truncation, §2), M3, M4 (left to the harness's D25
  loop), M11–M13 (harness preconditions, node rejection, worker timeout).
- **Still STOP:** M10 (edit path mismatch, internal), M15 (observer unparseable answer is `query_failed`; observer
  timeout stays a STOP), M16 (replay failure, now unreachable from model output), M17 (executed configuration failing or
  non-finite on an audit seed), M18 (transport failure), M21 (12 h root deadline). M14 (`digits_mlp` value outside the
  node's declared ranges) executes, as before.

Plus: every proposer call is journalled to `b1_proposals.jsonl` before the proposal is returned (objective,
structured edit, parsed directive, raw reply, check outcome), and the journal is validated against ledger and events.

**Date and PLAN row.** 13 Nov 2026, `R1-EXAM-B1-MODEL-OUTPUT-INVALID`. Code `3458b672`, `02a91494`; re-pins
`2eda52e7`, `c5bf524b`.

**What it cannot affect.** Every trial that did not stop before is recorded exactly as before, with two narrow
exceptions (diagnosis §4.2a: a summary surrogate on a root's last proposer call, or on a proposal the D25 loop would
have replaced, is now an invalid trial). Prompts, schema, seeds, temperature, completion cap, thinking policy, context,
budgets, nodes, `x5_rule_v2` and its analysis are unchanged. A rejected proposal never reaches the audit, so it changes
μ̂ only through which proposals are audited; but rejections count toward D28's invalid-trial rate (eligibility
requires an invalid rate below 30 %, thinking off), so frequent rejections **can make a candidate ineligible**.

**_d values.** Rejections per candidate, mode and check, read from each root manifest's
`proposal_journal.rejected_by_check` (same counts in `b1_proposals.jsonl`): ⟨table: candidate, mode, proposer calls,
directive_missing, directive_symbol_not_editable, directive_symbol_differs, directive_old_differs,
directive_new_differs, replacement_escape, python_value_*, context overflow (M19), unencodable summary (M20)⟩. For
example `olmo31_32b`'s directive mismatches: ⟨n of N proposer calls⟩. Candidates whose D28 invalid rate crosses 30 %
because of rejections: ⟨list or "none"⟩.

---

## 4. Draft appendix paragraph (combined)

> **Post-hoc changes to the proposer screen (B1).** B1 was restarted three times. Each restart followed a stop of the
> pre-specified procedure, was made before any candidate result had been used, and reran B1 from the start in a fresh
> output tree; the ranking rule, fixed before any B1 data existed, was never changed. (i) The first run stopped on the
> anchor check, which required a random-valid proposer to be shown worse than a scripted random proposer
> (scripted − random-valid +0.0046 [−0.0006, +0.0089], 12 instance pairs). A diagnosis found no defect but found the
> random-valid anchor's incumbent-relative increment falling within its runs on one node; because the check compares two
> random proposers no pilot had shown to be ordered, we kept the comparison as a descriptive number, kept the
> duplicate-rate check, and report first- vs second-half increments for every model. (ii) The second run stopped when one
> thinking-mode reply filled the context; truncated replies are now invalid proposals, charged to the budget, under a
> 16,384-token completion cap that no reply of the completed roots had reached. (iii) The third run stopped when one
> model's free-text edit and structured edit disagreed; such proposals, and two other unusable outputs, are now invalid
> trials, every proposal is journalled before execution, and the rejections count toward the eligibility gate's
> invalid-trial rate. In the final run: ⟨anchor difference⟩; truncated proposals ⟨total, per candidate in Table ⟨n⟩⟩;
> model-output rejections ⟨total, per candidate and check in Table ⟨n⟩⟩.
