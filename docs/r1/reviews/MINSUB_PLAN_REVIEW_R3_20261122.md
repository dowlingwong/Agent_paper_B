# Round 3: review of commit `aea4e510` (row R1-MINSUB-CHOICES and what follows it)

**AI-assisted independent review (Claude, the session of rounds 1 and 2, 22 Nov 2026) of commit `aea4e510` on
`author-minsub-20261122`, on top of `ecc717fd`. No human review. Scope: this commit only; consistency, traceability,
executability. The ICML facts of item (2) were not verified, as agreed. No sealed label or evaluation file was opened.**

**Verdict: ACCEPT WITH MINOR.** 0 MAJOR, 5 MINOR, 4 NOTE. Nothing in the commit contradicts the frozen preregistration,
R1-G5-DECISIONS, R1-SWEEP2-B2-GO, R1-SWEEP2-RELEASE-DECISIONS, R1-BX-D3, RUNBOOK §1 or BRANCHES.md; each fix is one
sentence. Short paths as in round 1; FULLTEXT = `docs/r1/inputs/NOVELTY_FULLTEXT_20261019.md`.

## MINOR

1. **Item (1): "keeps it on its own card" cannot be done on the TASL pair as main records it.** PLAN:1414. G.5 has one
   worker slot: TASL-2 trains, TASL-7 holds the proposer server (PLAN:1343;
   `proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md:207-212, :315`, "one slot, nodes in sequence on TASL-2"). A second
   worker card means workers beside the server on TASL-7 or another GPU model, both against R1-T1-HOST-TASL. Nor does
   the row say what runs while `autoresearch_fixedtokens` has no sealed noise floor: its G.1b note is not yet signed
   (PLAN:1384). **Fix:** "runs first in the single worker slot once its G.1b is sealed; until then the cheapest
   node of each other suite runs"; drop "own card" or name the row that amends R1-T1-HOST-TASL.
2. **Item (4): the added arm is not reconciled with R1-D3-MIN, and its screen is undefined.** PLAN:1409 still says "the
   five D.3a arms" and lists a "separate noise-aware keep threshold" and the "Ladder margin rule" as not run in closed
   loop; that rule is "keep iff Δ̂ > η, with η tuned on dev" (FULLTEXT:304), the new arm's keep half. The row does not
   say what the screen threshold is compared with: A1's constant prior gives one screen decision for every non-rule
   proposal (`C3_DESIGN.md:86`). **Fix:** "amends R1-D3-MIN: six D.3a arms; this arm stands for the Ladder margin rule
   in closed loop"; name the screened quantity and the search objective (dev label block only, no evaluation value).
3. **Item (4): the offline condition cannot be met.** PLAN:1414 "unless it is in the arms-frozen record and inside the
   preregistration's secondary scope": PRE-SECONDARY A's secondary arms are a fixed list (PREREG:186) without this
   arm. **Fix:** "an offline test read of this arm needs a signed preregistration amendment".
4. **Item (4): two defaults have no referent, and the host permission lacks its conditions.** PLAN:1414. "Memory mode
   ... as in sweep 2": sweep 2 ran two modes (`authorizations/c3_sweep2_20261119.md:50`). "LLM-call cap as in sweep
   2": that note declares none. Deepthought for the D.3 audit needs no change to R1-SWEEP-HOST-HTC (PLAN:1201 covers
   label sweeps and their audits) and meets R1-D3-MIN's "needs a row", but the sweep-2 permission came with
   conditions (PLAN:1382 D2, D3; PLAN:1391). **Fix:** give the two values; add "all D.3 audits on this one host, with
   the environment basis, harness-code equality check and disclosed host difference of R1-SWEEP2-B2-GO".
5. **Item (3): "the selection-bias statement" is not a name in the theory files.** PLAN:1414, CUR:39, :77. It can be T4
   Proposition 9 (`theory/T4_FEEDBACK_PROPOSER.md:83`), T2 Proposition 4 or T5's "selection bias of the value proxy"
   (`theory/T5_SIMULATION.md:131`). T4 Proposition 6, the keep rule R1-C3 cites (PLAN:407), is in neither the checked
   set nor the order. **Fix:** write "T4 Proposition 9"; place Proposition 6 or say 8' covers it. The other names
   match R1-T4-PROOF-CHECK and `proposals/T4_PROP10_REVISION_20261028.md:26-31`.

## NOTE

6. PLAN:1407 checks Proposition 7 first "if the gate does not pass"; PLAN:1414 (3) checks it before the gate read.
7. `inputs/NOVELTY_SWEEP_PART3_20261122.md:7` still lists the ICML quota page as an access failure.
8. CUR:77 "Packets are being prepared" and CUR:81 "is being drafted" are state with no record (PLAN:1412).
9. No conflict found for the static rule with PRE-A2 C, PRE-SELECT, the arms-frozen record or R1-D3-MIN's "not used
   to train, tune or select" sentence (it is tuned on the dev label block, not on D.3a outputs, and reads no test);
   nor for a run order in a PLAN row against the unsigned, tier-E G.5 note. CUR §2, §4, §5, §7 agree with the row.
