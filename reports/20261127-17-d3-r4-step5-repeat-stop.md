# local/20261127-17 — D.3 revision 4 step (5) STOP

for: coordinator

- Published base `2d88fe1b7bcaa1cb0b157ec48cf3be13255bf536`. Review and replay branch
  `mac-d3-r4-step5-repeat-20261127` @ `9841e2c0bf3f04460915016327c90c859376ac95`. This report updates the
  [previous step-(5) STOP](20261127-16-d3-r4-step5-stop.md) after the G1 fix.
- Independent tier-E full step (5) **NOT ACCEPTED**. Binding-only diff from
  `bd406db9d03f3bbdf3471431d1af96748e1f9556` **ACCEPTED**. The
  [review](https://github.com/dowlingwong/Agent_paper_B/blob/9841e2c0bf3f04460915016327c90c859376ac95/docs/r1/reviews/D3_PREDECL_R4_STEP5_REPEAT_REVIEW_20261127.md)
  SHA-256 is `47785eac7fe5bbf1bfbf3117974fab5660e23c8d4c39194eef30e2f099a9257b`.
- The G1 terminal snapshot repair passed. Seven synthetic harness, FIXR3 and EGATE cases used
  the actual chunk and audit paths with scripted inputs. The terminal configuration matched
  the post-decision incumbent. When the campaign reached 20 runs, the final and reported
  run-20 audits agreed and the pre-decision trace was preserved. The early call-cap case had
  seven charged runs and no run-20 outcome.
- G7 rejected the production G1 summaries because their keys differ from its required schema.
  After supplying a valid summary and normalizing the curve and terminal audit rows, G7
  refused again because production G6 emitted no per-keep audits. With fixture summaries and
  all keep audits supplied explicitly, all seven cases passed G7 and the pinned analysis on
  complete synthetic tables. The fixture path isolates the repaired terminal behavior.
- **Next.** Route the D.3a/b runner-to-audit-to-table integration to the G1/G6 owner with G7.
  Emit an exact G7 summary from the real ledger and accounting, capture and audit each kept
  incumbent with its charged-run index and the declared seeds, then assemble directly from
  those records. Preserve the signed §7.1, §7.5(a)/(d), §8 and item 25. Independently review
  the code unit and compare its full suite against base, then repeat step (5). Keep revision
  4 unfrozen and hold the per-arm smoke. The screening measurement and its disposition still
  precede freezing under R1-D3-ORDER.

## Tests and hashes

- Namespace check **PASS** at harness `9bb416805175149eb87b71f28d77530572aa4bce`
  for the 160 exact seeds in 20010–20801. `d3_analysis design` reproduced 126 paired
  instances and the normal first-step detectable differences 0.318575 and 0.304451 sd(D)
  for D.3a and D.3b without A6.
- Focused synthesis and guard checks **155 passed, 18 subtests passed** in Python 3.12 with
  the pinned NumPy 2.4.4. `git diff --check` passed. The branch contains the independent
  review and standalone synthetic replay evidence under `docs/r1/`. Production code and
  test suite bytes are identical to base, so verification uses focused checks and the replay.
- Declaration SHA-256 `142ea688ff62736216dc6c77328f186efb7801e8427ac97687f999a37045f663`.
  Analysis `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce`.
  Analysis tests `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4`.
  Namespace checker `62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2`.
  G2 constants `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93`.
  Gate utility producer `59d15d465edca1fb274cfe715653473949f8abeeb9d79adf9d8540ea471a77ab`.
  The declared gate path and key, and SMAC3 2.4.0, are bound.
- Replay script SHA-256 `52f639707f47faaa856b0ddd46160ba22151a5ba93e91ad3a346137521be5dfd`. Seven-record stdout SHA-256 `45bd71b40d63d7e265402373c6ad4a2baf67821bb026033f69073fd7e1a3f551`.
  The local rerun reproduced the independent stdout byte for byte.

I chose a fresh independent reviewer because the earlier reviewer was unavailable in this session,
and used isolated writable Git metadata for the fetch and branch commits because the assigned
checkout's shared Git metadata is read-only. All replays used synthetic inputs. No job was
submitted and no sealed input was opened.
