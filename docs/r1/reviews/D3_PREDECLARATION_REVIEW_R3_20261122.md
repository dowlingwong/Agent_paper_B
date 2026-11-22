**AI-assisted independent review (Claude, fresh session, subagent), 22 Nov 2026, round 3 (diff-focused).** Tier E.
Under review: commit `1a8aead8` (revision 3), checked against round 2 (`070af821`). PD = `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`,
AN = `D3A_AUTHORIZATION_DRAFT_20261122.md`, S = `r1/c3/d3_analysis.py`, T = `r1/tests/test_d3_analysis.py`. No sealed, label,
test-partition, evaluation or sweep-table file was opened. The only report file opened was `chunks_summary.json`, which holds timings.

# D.3 drafts, revision 3: round-3 review

## Verdict: ACCEPT WITH MINOR (1 MINOR, 3 NOTE)
**Not yet "accepted".** It is accepted once the one sentence of R3-1 is added and a diff-only check confirms it. No other change is required.
**Checked:**
- `pytest T` gives 31 passed.
- The sha256 of S is `cb5687e9…ebb3` and of T `7d5d8d04…881d`, equal to PD:422-424, PD:604 and AN:29.
- `namespaces` passes with five blocks, including smoke_replicate [6311, 6329, 18]. The smoke replicate law gives 6311–6319 and 6321–6329 (T:59-62).

## Round-2 findings
- MINOR A — **resolved**: the formula is (1 + d/(2c))^(n−1), with 0.0390 by pair 8 and 0.0468 by pair 7 (PD:266-271). This matches `decide`.
- MINOR B — **resolved**: smoke on `openml_climate` with replicate seeds 6311–6329 (PD:120, S:87-111, AN:36/62). The smoke seeds are refused in tables (T:156).
- MINOR C — **resolved**: the verify-seed check is a separate reviewed check that imports S without changing it, and it runs before step (5) (PD:122, PD:547-550, AN P10).
- MINOR D — **resolved**: [sha] items are settled at step (4), before the review at (5), and a later change gets a diff-only re-check (PD:22-34).
- NOTE 1 — **resolved** (PD:261-263). NOTE 3 — **resolved** (PD:272-275). The arithmetic holds: 14 runs after a 7-pair commit leave 6 single-run pairs, and 16 runs after an 8-pair reject leave 4.
- NOTE 2 — **resolved; one gap (R3-1).** Replicate failures count in the 12.99 % rate (PD:449, item 14). The incumbent rule is at PD:280-286, item 19 and G4.
  No incumbent STOP is left in §10.
- NOTE 4 — **resolved**: the note gets a size cap, encoding errors become REFUSED, and exactly one `approved: true` line is required (S:331-353, T:319-331).
  The start-configuration check is in `validate_table` (S:304-307, T:190). The note's sha is pinned in the launch record (PD:428-429).
- NOTE 5 — **resolved**: the D.3a analysis runs once, and the recomputation is a reproduction check where a difference is a STOP (PD:432-436, AN:84-86).
- NOTE 6 — **resolved**: the table sha is checked against both the addendum pin and the receipt's `inputs.proposals_sha256` (PD:170-178). NOTE 7 — **resolved** (PD:128-134, T:88).

## Judgement 1: EGATE incumbent-replicate failure (PD:280-286)
The reasoning is sound. Excluding a campaign on an event only EGATE can have makes EGATE's missingness depend on its own history, which biases
EGATE − A0. §8 also needs a complete paired design. Discarding the candidate is a rule of the arm, so Y measures the policy as run.
§5.5, §10, item 14, item 19 and G4 agree.
**R3-1 MINOR — what happens next is unspecified.** Worker runs are deterministic for a fixed configuration and seed, so a failed incumbent run at seed j
fails again. The PD does not say whether a later test that needs (incumbent, seed j) re-runs it, which would charge and count the same failure again, or reuses the
recorded failure. G4 would have to invent this. *Fix (one sentence in §5.5 and item 19):* "a failed (incumbent, seed) run is recorded
and never re-run; a later test that reaches that pair ends there with discard."

## Judgement 2: compute correction (PD:466-482)
The numbers trace to `chunks_summary.json`. Of the eight `append_only_summary` chunks, `wall_s` has a mean of 1,080.05 s and a maximum of
1,150.5 s (`openml_climate`). All 16 chunks total 4.32 GPU-h. The realised basis is 1,150.5 × 7/3,600 = 2.237 GPU-h per arm. Recomputed results:
- D.3a expected 5 × 2.237 + 1.7734 × 2.237 = 15.15; D.3a worst (8 + 4) × 2.237 = 26.85.
- D.3b expected 7.93 (11.90 with A6); D.3b worst 17.90 (26.85 with A6).
All match the PD. Three of these chunks (`breast_w`, `climate`, `credit_approval`) carry a post-run STOP flag but have full-length `wall_s`.
The basis holds, and the maximum is conservative.
**NOTE R3-a.** The 140 GPU-h STOP still makes sense as a ceiling on the P7 projection. P7 is a 2-instance smoke extrapolated by the
R1-SWEEP2-MEASURED-GPU rule, the same method that gave the 5,823 s layout basis, which overstated the realised time about 5×. Against the realised basis,
140 is about 5× the worst case, so it would not catch a moderate overrun. PD:486 should say the STOP applies to the P7 projection made by that rule.
AN:87 quotes only the layout basis (76.7/135.9); add the realised values or "see PD §11".

## Other new points
- **NOTE R3-b — the seed search claim in PD:150 is not accurate.** Paper C's synthetic E-SYN benchmark (`paperC/src/paperc/learner_validation.py:148`,
  refs `paperc-build-20261115`, `paperc-esyn-scaling-20261122` and others) uses simulator root seeds `range(6200, 6328)`. These cover the D.3
  instance seeds 6201–6218, the smoke seeds 6301–6302 and the smoke replicates 6311–6327. Its other blocks (4000–4511, 4500–5267, 6000–6127) overlap R1's reserved list too.
  They are a separate synthetic RNG domain with no T0 node, so there is no real collision. Round 2 missed this too. *Fix:* say so in PD:150.
- **NOTE R3-c.** The eight-step order is coherent: (1)–(3) inputs, (4) [sha] choices, (5) review, (6) sign with a diff-only re-check, (7) freeze, (8) pins.
  Step (3) now puts G1's verify-seed rule and its separate check on the critical path to signing.

## Could not check
The harness `vary` verify-seed rule, which is pending by design. The claim that 18 campaigns ran concurrently on 16 workers per chunk (PD:471), which `chunks_summary.json` does not record.
