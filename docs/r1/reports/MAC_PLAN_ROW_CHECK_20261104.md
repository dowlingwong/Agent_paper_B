# plan_row_check output (M1, mac-int-20261104)

Command (run on the commit before this file was added; this file adds no PLAN or STATUS line):

    python r1/scripts/plan_row_check.py --result HEAD --source origin/codex/coordinator-20261031 --source origin/docs/main-proposer-03nov --source origin/docs/runbooks-04nov --source origin/codex/b2-repair-20261031 --source 13badb0 --source origin/trackS-ops-20261030

Result: `2cc32728`. Source heads: coordinator `10742f85`, main-proposer `14dc0fea`, runbooks `c15b1102`, b2-repair `f98e315e`, trackS-decisions `13badb0d`, trackS-ops `f5d5c6b0`.

Expected RESULT-ONLY: the M1 STATUS entry this branch adds (nothing else).

```
## PLAN §10
origin/codex/coordinator-20261031: 235 items, 235 present byte-identical
origin/docs/main-proposer-03nov: 230 items, 230 present byte-identical
origin/docs/runbooks-04nov: 264 items, 264 present byte-identical
origin/codex/b2-repair-20261031: 193 items, 193 present byte-identical
13badb0: 207 items, 207 present byte-identical
origin/trackS-ops-20261030: 200 items, 200 present byte-identical
RESULT-ONLY: 0
## PLAN §10 other lines
origin/codex/coordinator-20261031: 36 items, 35 present byte-identical
  EDITED-BY:origin/docs/runbooks-04nov x1: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
    kept in result: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
origin/docs/main-proposer-03nov: 38 items, 37 present byte-identical
  SUPERSEDED-IN:origin/docs/runbooks-04nov x1: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
    kept in result: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
origin/docs/runbooks-04nov: 90 items, 90 present byte-identical
origin/codex/b2-repair-20261031: 32 items, 31 present byte-identical
  EDITED-BY:origin/docs/runbooks-04nov x1: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
    kept in result: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
13badb0: 33 items, 32 present byte-identical
  EDITED-BY:origin/docs/runbooks-04nov x1: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
    kept in result: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
origin/trackS-ops-20261030: 32 items, 31 present byte-identical
  EDITED-BY:origin/docs/runbooks-04nov x1: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
    kept in result: > **Historical index.** Dated author rows below take precedence over this index. In particular the D4 amendment, D18, D23, the `vary` split policy, R1-INFER-LLA
RESULT-ONLY: 0
## STATUS
origin/codex/coordinator-20261031: 853 items, 853 present byte-identical
origin/docs/main-proposer-03nov: 847 items, 847 present byte-identical
origin/docs/runbooks-04nov: 856 items, 856 present byte-identical
origin/codex/b2-repair-20261031: 798 items, 798 present byte-identical
13badb0: 817 items, 817 present byte-identical
origin/trackS-ops-20261030: 887 items, 887 present byte-identical
RESULT-ONLY: 1
  RESULT-ONLY x1: - M1 integration (4 Nov, Mac-local agent; AI-assisted, documents and merge only; MAC_LOCAL_RUNBOOK_20261104 rev 3.2): branch `mac-int-20261104` on coordinator `
MISSING total: 0
exit status: 0
```
