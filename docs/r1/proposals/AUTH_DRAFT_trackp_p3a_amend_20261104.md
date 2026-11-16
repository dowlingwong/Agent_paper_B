# Authorization amendment: Track P P.3a, option 3 — 4 November 2026 (DRAFT)

**Draft written 4 Nov 2026 by the chat session (Claude) at the operator's request (O7), for the author; AI-assisted.** It becomes an authorization only when the author commits it as `docs/r1/authorizations/trackp_p3a_amend_20261104.md`, either himself or by telling the Mac agent to commit it.

**Author:** Dowling Wong. *[When it is committed: the author's instruction, quoted verbatim, with date and time.]*

## What this amends

This note amends `docs/r1/authorizations/trackp_p3a_20261027.md` (27 Oct 2026). It records the author's ruling R1-P3A-OOM-OPTION3 (4 Nov 2026, 11:29): "(G1) P.3a OOM: option 3. The descriptive 2k/8k history-length probes are omitted (descriptive only under the spec), and attempt 1 is preserved."

## What is authorized

The **remaining P.3a evidence runs**, on the terms of the 27 Oct note, except for the following.

- **E6 A3 (history-length robustness)** runs **only** its specified rows: irrelevant acceptance history prepended at 0 / 25 % / 50 % / 100 % of the remaining token budget, under the smallest context limit in the pool (1,024 tokens) for every model (R1-A3-BUDGET; `TRACK_P_POST_TRAINING.md` §5.6, A3 row).
- **The descriptive 2k and 8k history-length rows of A3 are excluded.** They are not run, not attempted on any host, and not reported as missing results. The P.3a report states that they were omitted under R1-P3A-OOM-OPTION3.
- E0 and the E6 probes A1, A2, A4 and A5 are unchanged from the 27 Oct note. A5 stays descriptive only.
- **Attempt 1 is preserved** as it stands. It is not deleted, overwritten or reused as the new attempt. The new attempt writes to new output directories.
- **Template version.** Every P.3a result records the serialisation template version it used (R1-P3A-OOM-OPTION3 (G2)). The Mac agent (M13) identifies the order that attempt 1 used.

## Conditions

Unchanged from the 27 Oct note:
- the host (TASL-7 only), the GPU lease and the driver checks;
- the pins, the candidates and the pass rule (`p3_rule_v2.yaml`, sha256 `8c0ef908…`);
- the order: a DRYRUN first, if the code has changed since attempt 1;
- the STOP conditions and the review loop.

Additions:
- The Track P evidence marker helper is installed first (`proposals/trackp-evidence.sh` → `~/r1_locks/bin/trackp-evidence`, R1-TRACKS-S01-RERUN). The marker is set for the run.
- **Budget:** at most 60 GPU-hours in total for P.3a, **attempt 1 included**. Reaching 45 GPU-hours with candidates outstanding is a STOP with a report, as before.
- The operator runs this under the operator runbook's O7. This note gives no recovery authorization for Track P. A STOP is preserved as it stands and reported to the author.

## Not authorized by this note

Everything the 27 Oct note excludes, and in addition:
- the 2k and 8k A3 rows, on any host;
- any change to the A3 specification;
- any re-run of attempt 1's units into its own directories.
