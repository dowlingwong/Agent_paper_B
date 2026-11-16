# S2-C5 — real-submission switch (reviewed unit; DISABLED, not enabled)

**Purpose (P6):** submit a reviewed sweep-2 EVIDENCE JDL only for the author-authorized run id + frozen image digest.
This unit is implemented and reviewed but **not enabled**: nothing is submitted by it in this state.

## Gate

`submit` requires ALL of:

1. the author-committed note `docs/r1/authorizations/c3_sweep2_<date>.md` (format:
   `sweep2/s2_c5_authorization.template.md`) with `approved: true`, `label: EVIDENCE`, `run_id`, the frozen v1 gpu
   digest `69b06b35…`, the accepted 32k layout (walltime 12,203 s, disk 42,460,977 kB, memory 32,000 MB, 16 chunks,
   41.72 GPU-h), P1–P7 all filled, `b2_audits: none`, `d8_lock: true`;
2. the spec pins that exact note (basename + sha256) and its run_id / image digest / layout match the note;
3. `--enable` **and** `S2C5_ENABLE_REAL=1` (two independent keys; the repository default has neither and this unit
   creates neither).

Without them the switch STOPs `S2-C5 real submission is disabled` (or the more specific validation STOP). A
submission writes `S2C5_SUBMISSION.json` next to the reviewed JDL for the record.

## Non-goals

- It does not create or modify the authorization note, the enable keys, or the label; the author does.
- It does not read labels, run jobs, or select/chunk the sweep; it only submits the already-reviewed JDL.
- It does not authorize EVIDENCE by itself: P1–P7 remain the author's gate (see the launch checklist).

## Tests

`r1/tests/htcondor/test_s2_c5_switch.py` (synthetic, no submission): matching note/spec accepted in `check`; run_id /
layout / approval mismatches STOP; `submit` is disabled without both keys; a missing reviewed JDL STOPs after the
keys are present. The template is intentionally `approved: false` and not a valid note.
