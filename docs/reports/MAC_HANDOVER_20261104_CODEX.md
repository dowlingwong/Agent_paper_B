# Mac-local continuation handover — 4 November 2026

AI-assisted (Codex). This continuation began from `mac-int-20261104` at `8bbdafd4` and used an independent clone at `/private/tmp/paper-b-mac-20261104`; the Mac main worktree was not edited. No remote host, model, GPU or evidence run was used. CPU tests used local mock servers, including sandbox-external localhost tests; their own orphaned mock servers were terminated. Do not treat draft code, design acceptance, or an unchanged failure set as permission to run an experiment.

## Published branches and gates

| Branch | Last published head at this handoff | State |
|---|---|---|
| `mac-int-20261104` | parent of this handoff/status commit | Reviews, decision rows and status; no B1 launch authorization. |
| `mac-x5v2-20261104` | `bf8b2da` | M2 handoff/tests reviewed; M2 itself **NOT ACCEPTED**. Code `5fcea74` combines the M5 fix with M2 and contains a v2 B2 ranking STOP. Grid design is a conditional proposal, not an implemented gate. |
| `mac-m5-fix-20261104` | `d5f7b75` | The M5 fix was reviewed and integrated byte-identically into the M2 branch. Historical Stage A measurements were not rerun or reaccepted. |
| `mac-b2-20261104` | `14686a2` | M3 partial fail-closed fixes and conditional offline-boundary design reviewed. M3 **NOT ACCEPTED**; OpenML replay and B.2 remain STOP. |
| `mac-trackg-20261104` | `5fbf99b` | M10 disabled draft and non-authorizing bundle preview; `--submit` always refuses. Guard design reviewed as a conditional proposal only. M10 and HK1 incomplete. |
| `mac-gate-20261104` | `9bdbcc2` | Synthetic-only M11 prototype, reviewed in disabled form. Existing readers unguarded; M11 and B.7 not ready. |

M2 full-suite record and review are on `mac-x5v2-20261104`: `74a07907` 821 passed / 39 failed / 11 skipped; `75134796` 890 / 39 / 11; combined code `5fcea74` 894 / 39 / 11. All 39 failing IDs match. Two required pinned-harness controls separately passed. `docs/r1/reports/MAC_M2_HANDOFF_20261104.md` and `reports/mac_m2_tests_20261104/` contain the logs and SHA256SUMS. This is not a clean suite. The primary reviewer for the new round was a fresh Codex reviewer; the stopped prior Claude reviewer was not recoverable.

The M2 rule SHA is still `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20` for the unchanged **draft** file; do not issue the final pin or write R1-EXAM-RULE-X5V2 until the author resolves the sensitivity and D28 questions and the necessary code is accepted. B1 entry guards remain. The operator v3 message is not ready. B1's `workers=20` controls a process pool of paired audits after collection; roots and seeds are sequential. Headroom is unmeasured. Configs still need author-selected values and pins bound and reviewed before a final authorization; the `stage_a_amendment_acceptance_sha256` format remains open.

The M5 supplementary check (`reports/MAC_M5_RECORDED_BOS_CHECK_20261104.md`) found 330/330 recorded token checks with matching first server token and recorded BOS ID, plus 110 byte checks. Its inference is conditional on the copied journal identity and O1's tokenizer recomputation; the pinned tokenizer was not independently reloaded, and it does not establish that a D3 STOP was never swallowed.

The queue report's committed source includes only two of the several cited raw files; precise times and teardown cannot be independently checked from that merge. HK0 still needs the author's 5 November job start times and the subsequent T_max/GPU decision. Do not perform the queue probe again. P.3a remains STOP; the author's amendment note does not authorize a restart.

## Author replies recorded in PLAN §10

- Second proposer: author "是我的决定" in response to "用 exam 第二名" and the local/different-family/B2 thinking-off audited-Y/closed-loop-only proposal; consequences labelled proposed.
- B1: "按照建议决定" for the digits variant, call cap 80 and 20 workers; hash format was not decided.
- J3: "确认涵盖 J3" pending NHR@KIT's answer; a restrictive reply requires STOP. It does not waive phase, budget, review or evidence authorization.
- Host consolidation: "保留现有逐项决定"; DTQ disclosure: "先等 DTQ 结果".
- Five (h) items: "采用五项建议"; partial-T1 H1: "采用此部分 T1 方案"; expand (j): "现在逐项展开"; divergence STOP: "设 20% STOP" (asked as strictly above 20%). The numerical denominator, numerator and time need specification. The Track S repeat-with-pick clause was omitted from the question and remains open.
- The follow-up questions on the remaining (j) items, Track S repeat, M2 thinking-on sensitivity and D28 interpretation, and M10 unified submission/ledger approach were asked asynchronously; no reply was observed as of this handoff. Do not interpret elapsed time as a decision.

## Next actions and STOPs

1. Obtain the author's answers to the two M2 sensitivity/D28 questions; do not freeze the rule merely from its unchanged SHA. Keep the full B2 ranking STOP until an independently reviewed verifier binds the author-approved B2 power plan, finalist set, complete node/instance grid and independent receipt evidence. Proposed design and its review are at `mac-x5v2-20261104` @ `bf8b2da`. No count or trust root has been decided. The described tolerance and interrupted-GPU-hour handling are proposals, not existing policy. Restore the actual ranking and tie tests before enabling it.
2. M10's reviewed design is on `mac-trackg-20261104` @ `5fbf99b`. Its preview does not prove classification, immutable execution or authorization. Account/user-wide serialization, Slurm delayed accounting, immutable execution and real site capabilities remain unresolved. No real submit or HK1.
3. M3's reviewed proposal at `mac-b2-20261104` @ `14686a2` requires Linux process-tree offline enforcement, tests with the actual pinned OpenML loader and verification of host capabilities; these are distinct outstanding conditions, with no implied ordering for read-only capability checks. Keep all current e1/B.2 STOPs and author decisions on the five out-of-scope files.
4. M11 needs independently trusted PLAN and label provenance, guards in all existing readers, validated statistics and oracle construction, online baseline integration and actual TabPFN support. `welch_replicates` in the prototype is synthetic-only and must not receive evidence. Old per-node verdict cannot be used for B.7. No sweep-2 table is read before R1-BX-D8-CONFIRM.
5. Answer the author's remaining decision questions only with context and record verbatim dated PLAN rows after responses. Do not attribute recorder proposals to the author. Prioritize independent work, but do not access servers, retry stopped experiments or bypass gates. Preserve local and published artifacts; use `_to_delete/` for retirement.
