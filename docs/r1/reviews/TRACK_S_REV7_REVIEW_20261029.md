# Track S rev 7 — independent confirmation review (29 Oct 2026)

AI-assisted (Claude); read-only.

**Verdict: ACCEPT WITH MINOR CHANGES.** 0 BLOCKING, 0 MAJOR, 12 MINOR. The core rule (§0, §3, §10) is exhaustive and exclusive; no outcome is automatic. Apply m5–m7 and m9 before S0.8.

## 1. One-way consistency
- **m1.** The §0 elements table, row (2), still lists "a budget positive control (P0)"., but P0 is unmeasured.
- **m2.** §4 Primary 2 still says "supports A only"; replace it with "MDE at 300 reported".
- **m3.** The analysis code still contains B, the flip gate and "inconclusive" (notes §1(e); §2 items 3 and 5). Remove them in S0.3 and test that only {A, A-small, no gain found} can be output, before the S0.8 hash.
- **m4.** If no decision node survives S0.5b, no outcome is defined. State "Track S not run".

## 2. "No gain found" wording
- **m5.** UB₉₅ bounds **π\*** only, not "the four-member family". Reword: "the selected member π\* did not beat m\*; its mean gain is below UB₉₅". Report S0.6's P(correct member) with it.
- **m6. Block the equivalence reading.** Under N0, P(UB₉₅ < δ_Y) = 0.97, while the flip rate reaches 10 % in only ≈ 10 % of runs. A small UB₉₅ mostly means that π\* and m\* agree on 90–95 % of decisions, not that there are no dynamics. Add the sentence "UB₉₅ < δ_Y is not an equivalence or negligibility result", and print the flip rate next to UB₉₅.
- **m7.** The power figures in §0 and §10 (≈ 0.75 at δ_Y; ≈ 0.6 at 2 δ_Y) are FIXTURE values for a digits-like node at n = 110. Use per-node placeholders from the final S0.6; tabular at n_max will be weaker. P2+ diffuse reached only 0.90 δ_Y with fixed members (notes §5.2). Declare that the achieved oracle gain is reported when ±5 % is unreachable.

## 3. Members, sizing, controls
- **m8.** The centres r̄₁, τ̄ and r̄₂ are means over m\*'s states. π\* visits different states. At g\* = 0, V̂\* ≥ 0 clips the threshold, so a member can only skip more: a net level shift. Soften "cannot win by a level shift" to "approximately; the matched static is the guard". **No leakage**: the centres are frozen from dev, and S3e uses fresh blocks.
- **m9.** The runbook uses "≥" but the notes and code use ">". With g = 0 and V̂\* = 0, ">" skips, which contradicts "g = 0 executes every non-rule proposal". Pin "≥" and add a test.
- **m10.** z₀.₉₅ + z₀.₉₀ gives 90 % power unadjusted. Under Holm with one gaining node and one null node, the test is at α/2, so power ≈ Φ(2.93 − 1.96) ≈ 0.83. Relabel accordingly. The n values (79, 215, 316) check.
- **m11.** S0.6 runs "before tuning", yet it is matched to the "dev between-configuration sd", which does not exist yet. Write "pilot" (rev 6.1 item 6), or re-run S0.6 after S0.7, since it gates only N0.
- **Checked, OK:** Holm, the order of the exact placebo, the |z| > 3.5 rule, and the N0 STOP (P(X ≥ 19 | p = 0.05, n = 200) ≈ 0.005). State whether S0.6 applies two-node Holm or a per-node test; per-node is conservative.

## 4. Info member
Keeping the member is right, but the §11 reason is wrong. Changing a member after a synthetic study and before any real data does not breach pre-registration. The real reason is circularity: P1 is a planted mechanism, and fitting the member to it would inflate the claimed sensitivity. Dilution is negligible (a −5 δ_Y member is almost never selected).

**Required:**
- Correct the §11 rationale.
- State that the information channel is effectively unprobed. The P1-diffuse power comes from the other members, so m7 must not call it "information sensitivity".
- A null result for the info member is uninformative about the channel.

## 5. Cost and schedule
Verified: S0.7 (18.4k), S3e (15.2k / 41.8k), totals (52k / 79k), all wall-time cells.
- **m12.** The S3e row says n = 78 but the total row says n = 79. The g = 0.8 extension (+60 campaigns, ≈ 2.4k calls) is missing from the table.

Schedule plausible; 15–23 Nov includes slack.
