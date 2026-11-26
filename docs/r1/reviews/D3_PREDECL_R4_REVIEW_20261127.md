# Review: D.3 pre-declaration revision 4 and `d3_analysis.py` (branch `mac-d3-predecl-r4-20261127`)

**Reviewer:** an independent tier-E reviewer, AI-assisted (Claude, 27 Nov 2026), who did not write this unit. It ran round 1 and a diff-only re-check, read-only, in fresh detached worktrees that were removed afterwards. It opened no label, test-partition or evaluation file. The local worker transcribed this record from the reviewer's full text, which replaces the implementer's earlier summary.

## Part 1. Round 1 (tip `0b373a79`, code commit `f85b3c88`): not accepted

**Scope:** `git diff 5d29aa46 0b373a79`:
- the pre-declaration (revision 4);
- the D.3a authorization draft;
- `r1/c3/d3_analysis.py`;
- `r1/tests/test_d3_analysis.py`;
- the unit report.

**Checked against:**
- tasks `local/20261126-03` and `-16`, and card `local/20261126-07` item 3;
- the PLAN rows: R1-D3B-UNCONDITIONAL, R1-D3-DECOMP, R1-D3-OUTCOMES2, R1-D3-HPO-REF, R1-D3-ORDER, R1-D3-CHOICES, R1-HOST-FREE, R1-CARD-SHARE, R1-NO-TIMEOUT, R1-STEP-ORDER, R1-SUBMISSION-MIN;
- the claim sheet at `a9a9f6bb` (sha256 `58d33590…1020`);
- `GOAL_METRIC_ALIGNMENT_PROPOSAL_20261126.md` §6;
- the G1/G6 design.

### Commands run

- **Tests:** 53 passed.
- **`python -m r1.c3.d3_analysis design`:** D.3a k = 8: 0.3186 (t: 0.3233). D.3b k = 5: 0.3045; k = 6: 0.3100. Last step 0.2496. n = 126, df = 119.
- **Pins:** equal to the files (`aa13ebad…fe7d`, `9e3a91e1…5dfe`).
- **Refusals, checked on a synthetic CLI:**
  - `gate_not_passed` refused, by argparse and by `analyse()`;
  - a v1 table refused;
  - a second `gpu_model` on one instance refused.
- **Holm families and directions:** as declared.
- **Power figure:** recomputed by hand, (z₁₋α/(2k) + z₀.₈)/√126. It matches, including the item 22 alternatives (0.3325, 0.3346, 0.3382, 0.3250).
- **HPO-REF configuration space:** matches the harness `configs/nodes/*.yaml` at `a3fedbbd` for all seven nodes.

### Blocking finding

**B1 (§3.1 item 4, lines 148–152).** The draft extended R1-NO-TIMEOUT (2)'s infrastructure case from "another compute process on its card" to "shared the job's host CPUs or card":
- with no recording rule (R1-CARD-SHARE (4) records only the card's processes);
- with no §13 item.

This moves Y and the failure STOP at the operator's choice after the fact.

**Failure scenario:**
1. A slow `digits_mlp` proposal on a shared HTCondor host passes 600 s.
2. The chunk is rerun on the same seeds and the same GPU model, so the same proposal passes 600 s again.
3. Attempts are unlimited and this is never a STOP, so the chunk never ends.

**Fix:**
- (a) keep the literal card condition; or
- (b) an author item with a recording rule and a repeat on an unshared host.

Either way, apply it to §12 "G1 additions".

### Minor findings

1. Row 5 with a favourable learned gain gave no note (`d3_analysis.py:762`; §7.4 item 4).
2. `rule_layer_alone` replaced the whole headline of rows 3–4 and dropped their gate-dependent half (`:771`; lines 539–540).
3. Stale "proposed" markers remained on values that R1-D3-CHOICES (2) settled:
   - lines 66 and 90;
   - §7.1 item 10;
   - §10 items 14 and 19, and the fallback-prior rate;
   - §5.4 and §5.5 item 19;
   - `d3_analysis.py:83-84`.

   Also, §13 item 11 still said "STOP".
4. SMAC3 "at most 80 asks" did not fit `proposal_cap` being refused for SMAC3 (`:232`).
5. The mixed learned case (one favourable, one unfavourable, giving `learned_gain = gain`) was not stated.

### Checked and correct in round 1

- The 26 Nov (d) rows are applied as written.
- The six points of task `-16` are met: families in the sheet's order; FWER 0.05 per family and "up to 0.10" overall stated; readings including the harm and rule-layer-alone cases; rule layer off for FIXR3, EGATE and LADDER; repeat charging; the power figure labelled as a design figure.
- The code matches the text.
- Secondary outcomes are descriptive only, with no route to a test read.
- Rows (g) are applied.
- The departures, the author items 21–30 and the open TODO fields are listed accurately.
- No earlier test was weakened.

Round-1 verdict: not accepted.

## Part 2. Re-check (tip `9d5c1272`, diff from `0b373a79`): accepted

- **Pins:** `d3_analysis.py` `c0be0399…84ce` and tests `c6c56c33…01a4`, equal to the files. Tests: 53 passed. `design` output unchanged.
- **B1 resolved.** §3.1 item 4 now uses the literal card condition, recorded per R1-CARD-SHARE (4): a T0 hit where only the host CPUs were shared is the proposal's failure. The new §13 item 31 (R1-D3-R4-CPUSHARE) offers the alternative, with a recording rule and a repeat on an unshared host or slot. §12 "G1 additions (ii)" matches.
- **Minors 1–5:** resolved, with tests where the code changed.
- **Nothing else changed.**

### Notes (none blocking)

- **The literal condition can still loop** when the card is shared again. That is R1-NO-TIMEOUT (2) and R1-CARD-SHARE (3) as written. G1 could place such a repeat on an unshared card.
- **A doubled "(§13 item 15)"** in the FIXR3 memory-display line. The local worker fixed it in the commit that adds this record; the change is docs only, and no pin moves.

**About the implementer's earlier summary:** it was faithful, with two small points:
- it gave option (a) plus item 31 as "the" fix;
- the no-full-suite instruction was the coordinator's, not the reviewer's.

Verdict: ACCEPTED
