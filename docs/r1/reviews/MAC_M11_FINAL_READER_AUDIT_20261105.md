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
