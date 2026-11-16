# Independent review — R1-MAIN-PROPOSER, RUNBOOK B.1b and the `x5_rule_v2` draft (3–4 Nov 2026)

**Reviewers.** Two fresh agents (Claude), neither of which had seen the drafting. This record was written by the chat session from their reports.
- Base: coordinator `21873e3b`.
- Draft: `668c2b4c`.
- Revision: `1ce4567a`.
- Final: `347a8595`.

## Round 1 (draft): not accepted

1 BLOCKING, 6 MAJOR, several MINOR. All were fixed in `1ce4567a`.

| # | Finding | Fix |
|---|---|---|
| B1 | The X.6/X.7 change contradicted the frozen exam rule `x5_rule_v1`, which `runtime.author_gate` binds | New rule `x5_rule_v2`, with its code changes, a review and the PLAN row R1-EXAM-RULE-X5V2 carrying its sha, all before B1 |
| M2 | Thinking-off is a server flag (`thinking_args`; `--jinja`, q8_0 KV), not a harness change | Implemented as a paper-side change to the sweep; only `cache_prompt` needs the harness pin |
| M3 | The order skipped R1-HARNESS-NEXT-PIN | Sweep-1 B.2 now comes first, unless the author grants an exception |
| M4 | "Design unchanged except the manager" was false | The stack differences are listed, and R1-SWEEP-HOST is amended explicitly |
| M5 | Twin instances share seeds, so the labels are identical across sources | One shared split; the cross-proposer table runs train → test only; duplicates are grouped across sources; instance-cluster bootstrap |
| M6 | Selection effect: the exam nodes are among the sweep nodes | Disclosed; results lead with paired contrasts |
| M7 | No cost estimate for the thinking-off B2 runs | Added |

## Round 2 (`1ce4567a`): not accepted

2 MAJOR, 6 MINOR. All were fixed in `347a8595`.

- **MAJOR: unquoted YAML `off` loads as boolean `False`.** All mode fields are now quoted, and a test that they load as strings is required.
- **MAJOR: the code-change list was incomplete.** It now includes `load_rule` (version check and default path), the `b1_sensitivity.node` rename, and the B1/B2 mode logic in `exam_runner.py`.
- **MINOR:**
  - v1 was misdescribed;
  - the harness and paper commits were missing from the stack differences;
  - the eligibility predicate was not written in the registry's terms;
  - the X.6 text was stale;
  - the context was worded inconsistently;
  - the D22 PLAN-line guard (`exam_runner.py:97`) was not addressed.

## Round 3 (`347a8595`): **accepted**

All 8 round-2 findings are resolved, with no new issues.
- The reviewer checked that the YAML mode fields load as strings.
- The registry counts are 14 switchable models with an off switch, 5 non-thinking and 3 always-on.

Nothing in the change authorizes a run.
