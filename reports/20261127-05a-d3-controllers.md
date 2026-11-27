# local/20261126-05 item 1 — D.3 controller units (DONE, accepted)

- **Task:** `local/20261126-05`, item 1.
- **Delivery:** one stack on `mac-d3-predecl-r4-20261127` @ `6412b843` (revision 4, now on `main` in `bd406db9`). Merge the top branch **`mac-d3-g9-sidecar-20261127` @ `27564dbb`**: it carries every unit, the review corrections (`c56e94f4`, `4ecbbb3d`) and the review record. The lower branches are kept for reading only.

  | Unit | Branch | Commit |
  |---|---|---|
  | A0R | `mac-d3-a0r-20261127` | `f81739c8` |
  | G8 | `mac-d3-g8-accounting-20261127` | `e775b38c` |
  | FIXR3 | `mac-d3-fixr3-20261127` | `2d4e9cf2` |
  | EGATE | `mac-d3-egate-20261127` | `871d4712` |
  | LADDER | `mac-d3-ladder-20261127` | `222de37a` |
  | G7 | `mac-d3-g7-outcome-table-20261127` | `e33abaef` |
  | G9 | `mac-d3-g9-sidecar-20261127` | `98bf9a72`, then corrections |

- **Implementation:** a Claude subagent for the local worker. Reviews and corrections were coordinated here.
- **Review record:** `docs/r1/reviews/D3_CONTROLLERS_REVIEW_20261127.md`.
  - A0R, G8, LADDER and G7: **accepted**.
  - FIXR3 and EGATE: **accepted as decision engines only**.
  - G9: **accepted with minors**. Round 1 was NOT ACCEPTED (B1, a livelock at a fixed timeout); it was fixed and re-checked.

## What exists now

- **`r1/c3/d3_controllers.py`:**
  - `RuleLayerController` with an explicit rule-layer switch, pinned to `d3_analysis.RULE_LAYER_ARMS`;
  - A0R;
  - LADDER, taking c on the grid, with t* = η exactly.
- **`r1/c3/accounting.py` (G8):** charged replicate runs; the single W counter (`OverBudget` is a STOP); re-issued LLM calls free against the cap; `table_ended_on` equal to the pinned analysis; the literal card condition for infrastructure.
- **`r1/c3/d3_replicate.py`:** the FIXR3 engine (Welch, r = 3) and the EGATE engine (`PaceStyleGate` 0.1/0.05/8, pair and seed logic).
- **`r1/c3/d3_outcome_table.py` (G7):** `r1_d3_outcome/v2` rows, validated end to end by `d3_analysis`.
- **`r1/c3/d3_sidecar.py` (G9):** a loopback, digest-pinned A5/A6 sidecar client. It waits for an answer with no read limit and writes progress records. A lost sidecar is infrastructure, a digest mismatch is a STOP, and only an error answer falls back. It refuses an image until §13 item 16 is set.

## Tests and suite

- **Module tests at the top:** 289 passed (A0R 14, G8 38, FIXR3 17, EGATE 20, LADDER 133, G7 40, G9 27). Neighbouring files pass unchanged.
- **Full suite** with torch (`~/anaconda3/envs/hupdate/bin/python`), against base `6412b843`:

  | Tree | Failed | Errors | Passed |
  |---|---|---|---|
  | base `6412b843` | 182 | 3 | 4276 |
  | LADDER code `4be7e706` | 182 | 3 | 4492 |
  | top code `449b6aea` | 182 | 3 | 4539 |

  The failing-id lists are identical: zero new failures. The corrections touch only `r1/c3/d3_*.py`, `accounting.py` and their tests.

## Decided alone (level 0, confirmed by the reviewers)

- G8 was built second, because FIXR3 and EGATE charge through it.
- `ended_on` follows the pinned analysis, not the G1/G6 design's precedence. **The design text must be corrected.**
- FIXR3 reads "rejects" as p ≤ α.
- EGATE runs the candidate first within a pair.
- LADDER's carrier prior.
- A thin controller for A0R.

## Open: coordinator or author

1. **Harness route for FIXR3 and EGATE replicate runs.** This is pre-declaration level. §5 declares a harness action that charges like verify, which needs a new harness pin. Running replicates in the runner around the harness trial departs from §5 and needs a revision before signature. G3 and G4 are not complete until this unit exists.
2. **G9's failure rule needs the author:** draft row **R1-D3B-SIDECAR-FAILURES** ("a call without an answer is waited for (or issued again with a growing timeout) and never answered by the fallback; a lost sidecar is infrastructure; a digest mismatch is a STOP; only an error answer falls back"), plus one sentence each in §6 and §10. §13 item 16 (the image) needs compute's checks of v1 against the Track P image.
3. **Before signing:** one sentence in §7.5 (d) ("keeps includes the first valid trial"). §13 items 21 and 31 stay open; both are explicit switches.
4. **Contracts for G1/G6:**
   - adopt `r1_d3_campaign_summary/v1` and `r1_d3_audit_row/v1`;
   - emit `llm_call_reissued`;
   - use a fresh `ChargedRunCounter` per attempt;
   - persist the sidecar progress records;
   - G2 writes c;
   - every arm runs a flag-logging controller (including A0 under `RuleLayerController(rule_layer=False)`, subject to G1's review);
   - G6 audits every kept incumbent.
