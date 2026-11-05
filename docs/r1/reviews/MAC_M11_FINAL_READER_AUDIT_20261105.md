# M11 final reader audit — 5 November 2026

AI-assisted (Codex). Fresh independent review of `0d6d569` in an isolated clone. **R1 verdict: NOT ACCEPTED as complete reader enforcement.** This audit covers the concrete issues below and a bounded static search; it does not prove every path has been found or change any author decision. No real label data, server, network, model, GPU or experiment was used.

## 1. `r1_sealed` spelling on the actual Mac filesystem

`r1/c3/analysis_guard.py:22–29` compares path components case-sensitively. In a synthetic temporary directory on this Mac, `r1_sealed/fake.jsonl` existed, an alternate spelling `R1_SEALED/fake.jsonl` also returned `Path.exists() == True`, and `Path.resolve()` retained `R1_SEALED`. `refuse_sealed` returned normally for that alternate spelling. Any existing guarded reader using the helper can consequently open a file in the sealed directory by such a spelling on this case-insensitive filesystem. Only a synthetic file was read/created in the probe.

**Unblock:** casefold lexical and resolved components conservatively before comparison, and test both uppercase spelling and symlink targets without accessing real sealed data. **Owner:** Mac implementer and this reviewer. **Effort:** bounded code/test change and independent recheck, approximately an hour. No concurrent-path-race or hardlink guarantee is implied.

## 2. D8 decision table parser accepts non-decision tables

`analysis_guard.py:60–79` counts header cells but does not examine their meaning. A synthetic `## 10. Author decisions`, `### 5 November 2026 (author)` followed by a Markdown table headed `| Artifact | SHA256 |` or `| Key | Proposed value |`, and the row `| R1-BX-D8-CONFIRM | <64 a characters> |`, makes `_confirm_row` return `True`. Such a table need not be an author decision table. The heading matcher also accepts the invalid calendar date `### 40 November 2026 (author)` and a negated `### 5 November 2026 (not author)` heading. These are unit-level counterexamples, not an assertion that the present checkout is authorized: `require_d8_confirmation` additionally requires the relevant gate file, the actual SHA and a committed PLAN.

**Unblock:** restrict accepted subsection/date and header to actual dated author decision tables, while preserving real PLAN headings; add synthetic negative tests for non-decision headers, invalid dates, negated headings, prose, fences and comments and a positive genuine decision-row fixture. **Owner:** Mac implementer and this reviewer. **Effort:** bounded parser/tests and recheck, approximately 1–2 hours.

## 3. Independently callable audit seed reader

`r1/c3/audit.py:217–224` reads `out/audit_seeds.json` without checking whether the path resolves under `r1_sealed/`. A synthetic direct call `resolve_seeds(Path(tmp)/'r1_sealed')` returned `(1, 2)` from a fixture there. The standard `audit.py` command checks `args.out` first at `:904–912`; this is a direct Python helper gap, not a demonstrated sweep-2 label-table CLI bypass and the file inspected was a synthetic seed list rather than labels.

**Unblock:** guard the derived `audit_seeds.json` and output path before inspection/read, including a sealed symlink test; retain explicit-seed behavior as appropriate. **Owner:** Mac implementer and this reviewer. **Effort:** small code/test change and recheck, under an hour.

## Bounded inventory and limits

The existing `dataset.load_table`, `offline_eval.assemble` and `ni_masking` call the shared guard; audit `evidence_plan`, accounting JSONL, sidecar pins and synthetic-exam readers have previously scoped reviews. `env.label_rows` invokes the guarded assembly before its second read under stable paths. Metadata-based sweep-1/pilot exemptions rely on the disclosed provenance process, not cryptographic identity, and the audit did not test adversarial concurrent path substitution or hardlinked aliases. Generic paths under the five author-held files and other protected training files are out of scope; the parent must not claim universal coverage on this review alone. D8 confirmation, seal handling after that decision, and phase authorization remain separate author actions.

## R2 — recheck of `088027c0d9866eb15ce21830751072743d4d99b1`

**NOT ACCEPTED** pending actual-PLAN compatibility. The three R1 issues are addressed in the candidate: lexical and resolved components are casefolded, unrelated headers and invalid/negated author headings are refused, and `resolve_seeds` checks its derived seed path before opening. Independent safe synthetic run of `r1/tests/test_c3_analysis_guard.py`: **34 passed**. No real data, host, network, GPU, model or experiment was used.

However, the new `_author_heading` requires an author marker in the heading itself. Four existing dated PLAN §10 author-decision subsections at `docs/r1/PLAN.md:973,988,1010,1022` have headings without that marker, followed by the explicit `| ID | Author's decision |` table. Independent calls to `_author_heading` return `False` for all four. If the author's genuine later D8 row is recorded in one of these established subsections, the guard will refuse it. This is a fail-closed compatibility defect; it does not permit an unauthorized read.

**Unblock:** accept the actual dated subsection plus explicit author-decision-table shape while continuing to reject invalid dates, unrelated decision tables and explicitly negated author headings; test using actual heading/header forms. **Owner:** implementer and same independent reviewer. **Effort:** bounded local code/tests and recheck, approximately an hour.

## R3 — recheck of `7c1953c602690f69a1d233f26d91f5617893887f`

**ACCEPTED for the three bounded R1 reader/parser corrections and the R2 compatibility correction.** A valid dated heading with an explicit `Author's decision` table is now accepted even when the heading itself has no author marker, matching the four actual PLAN heading styles identified above. A plain `Decision` header still requires an affirmative author marker; invalid dates, explicitly negated headings and unrelated table headers remain rejected. The sealed guard casefolds lexical and resolved components, and `resolve_seeds` checks before its seed file read.

Independent focused command, using the Mac harness venv with bytecode/cache disabled: `r1/tests/test_c3_analysis_guard.py` **39 passed**. Additional independent temporary-path probes confirmed STOP for the Mac case-insensitive `R1_SEALED` alias, a symlink to that alias and direct sealed seed reads; synthetic D8 rows under actual heading shapes were accepted, while invalid-date and explicitly negated headings were refused. No actual labels, real server, network, model, GPU or experiment were used.

**Scope and remaining STOP:** this accepts only the exact tested candidate and does not establish universal protection of other generic protected training readers, immunity to concurrent replacement or hardlink aliases, or cryptographic provenance. M11's full gate remains unimplemented/subject to review and the author's D8 row; `r1_sealed/` is not authorized for reading. The integrated diff requires identity verification and an independent integration review. **Owner:** Mac integrator/reviewer, then author and any separately authorized operator. **Effort:** bounded integration review plus author response; other reader coverage depends on the protected-file decision.
