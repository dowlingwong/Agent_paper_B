# Track S — GPU-node extension and fallback date (proposal skeleton, 4 Nov 2026)

**Status.** AI-assisted skeleton (Claude, chat session) for PLAN §10 R1-BX-D10, which the author adopted on 4 Nov 2026. It records what is decided and lists what the Track S design revision must settle. It changes no Track S pin, rule or threshold, and authorizes nothing. The Track S design (rev 7.4) and operator runbook (rev 3.3 of record, `13badb0`) are on `docs/trackS-decisions-30oct`; the revision is written against them after the Mac agent's integration (MAC_LOCAL M1).

## Decided (R1-BX-D10)

- **Add 1–2 GPU nodes to Track S:** autoresearch (short fixed-step variant) and one RL-type task with high noise and interacting edits.
- **Fallback date ≈ 15 Dec 2026.** If Track S has no campaign-level result by then, the DAC-reduction argument rests on the theorem plus synthetic controls, and the paper says so explicitly.

## Why (review document P3, P4)

On the two CPU nodes with single-parameter edits, edits barely interact, so the NF condition holds almost by construction, and a Track S null would be read as circular. GPU nodes with code-level diffs give the contrast.

## What the design revision must settle (open)

1. **Nodes:** which RL-type task, chosen from the Track G census (G.0), by noise level and measured edit–edit interaction.
2. **Manager.** R1-MAIN-PROPOSER (j) keeps `qwen2.5-coder:7b` for Track S on the CPU nodes. GPU nodes take code-level diffs (R1-BX-D4), which the 7B may handle poorly. Options: the 7B (consistent with the CPU nodes), or the main proposer (consistent with C3). Either needs D28 diff liveness.
3. **Seed-replayable sampling** on the GPU nodes: `cache_prompt: false`, the S0.1 identity test re-run on the chosen manager and host, and the task runs' own determinism from the census.
4. **Budget:** Track S needs about 80k calls per CPU node at the current design. Its GPU-node arm must be re-sized against task-run cost (fixed step budget; one GPU model).
5. **Host:** the 4090s are contested (Track X, Track P, sweep 2). The proposer may sit on deepthought across two TITANs (R1-BX-REVISIONS (f)) while task runs use the T1 GPU model.
6. **Schedule:** what counts as a "campaign-level result" for the 15 Dec fallback, declared before the GPU-node runs start.

## Next

The Mac agent drafts the design revision (MAC_LOCAL M6), an independent reviewer accepts it, and the author commits a PLAN row before any GPU-node Track S run.
