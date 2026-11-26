**Record of a fresh independent tier-E review (round 1), as relayed by the coordinator on 27 Nov 2026; summarised
by the implementer (Claude, local worker). The reviewer's own text was not received; this summary carries its
findings.**

# Review of the D.3 pre-declaration revision 4 — round 1

Reviewed: branch `mac-d3-predecl-r4-20261127` @ `0b373a79` (`D3_PREDECLARATION_DRAFT_20261122.md` revision 4,
`r1/c3/d3_analysis.py`, `r1/tests/test_d3_analysis.py`, the D.3a authorization draft, the unit report).

**Verdict: NOT ACCEPTED (round 1).** One blocking finding, five minors.

## Blocking

**B1.** Draft §3.1 item 4 (lines 148–152) extends R1-NO-TIMEOUT (2)'s infrastructure case from "another compute
process on its card" to "shared the job's host CPUs or card". That has no recording rule (R1-CARD-SHARE (4) records
only the card's processes), and the rerun can loop forever: the same seeds reproduce the same slow proposal on a
shared HTCondor host, attempts are unlimited and it is never a STOP. Fix (option (a)): keep the row's literal
condition (another compute process on the job's card, recorded per R1-CARD-SHARE (4)); a T0 CPU-only budget hit
counts as the proposal's failure. Add as an open author question (§13 item 31, with draft row text) whether CPU
sharing should count and, if so, how it is recorded and that the repeat runs on a host or slot without other compute
processes so that the repeat decides. Apply the same to §12 "G1 additions".

## Minors

1. Readings: row 5 with a favourable learned gain (`d3_analysis.py:762`; §7.4 item 4) — add a note, like the harm
   notes, that a learned gain under row 5 is reported (or list it under §13 item 23).
2. `rule_layer_alone` (`d3_analysis.py:771`; draft 539–540): replace only the rule-control clause of rows 3/4 and
   keep the gate-dependent half.
3. Stale "proposed" markers for values R1-D3-CHOICES (2) settled (draft line 66, §3 heading line 90, §7.1 item 10,
   §10 items 14/19 and the fallback-prior rate, §5.4/§5.5 item 19, `d3_analysis.py:83-84` comments); §13 item 11 to
   "reporting threshold".
4. SMAC3 "at most 80 asks" against `proposal_cap` refused for SMAC3 (`d3_analysis.py:232`): state in §5.8 that every
   ask is evaluated and charged, or drop "80 asks".
5. The mixed learned case (one of A3 − A2 / A5 − A2 favourable, the other unfavourable → `learned_gain = gain`):
   list it in §7.4 item 2 and in the report's departures.

## Required after correction

Re-pin §9/§14 and the report; rerun `pytest r1/tests/test_d3_analysis.py` and `python -m r1.c3.d3_analysis design`.
No full suite unless code outside `d3_analysis` changes. Then a re-check of the diff by the reviewer.
