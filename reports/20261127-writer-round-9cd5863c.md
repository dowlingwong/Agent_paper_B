# Paper B writer round close — 27 November 2026

Writer is idle. Published research base `9cd5863cc1e0855c045fc1090841832cc5b7614c`;
queue `coord/coordinator` at `6bda21b2e03783ea2ebe21bc43659b83e99f14c6`.
All five writer cards are published. The result-table handoff (next-phase runbook §3,
item 4) has no task ID and remains pending the authorised evidence. No new
manuscript unit, independent review, compute submission or sealed-data access this round.

| Task | Delivered branch and tip | Review on record | Published merge |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The title and eight-page trim had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

The four delivery tips are ancestors of the published base. The manuscript now lives at
[dowlingwong/paper_B_manuscript](https://github.com/dowlingwong/paper_B_manuscript),
whose published commit `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5` matches the research
pin at `papers/manuscript`. Future LaTeX deliverables use a separate task branch there.

## Question and evidence

Which decisions improve an autoresearch campaign under the same caps of 20 worker runs
and 80 manager calls? In Sweep 1, replay found 3,274 duplicates in 4,999 proposals. That
measurement motivates testing whether a campaign improves when it skips duplicates and
detectable no-ops. D.3 pairs arms on fresh instances and measures how much the final
configuration improves on the start on ten fresh audit seeds, in units of each node's
reference standard deviation. A0R − A0 estimates the gain from the skips. A2 − A0R measures
what the noise-aware rule adds with the skips in place. A3 − A2 and A5 − A2 measure what
each learned forecast adds under that controller. The paired estimates, intervals and signed
within-family rules determine which gains the paper can claim. The offline gate separately
tests whether the forecasts improve one-step decisions on logged proposals. D.3b runs after
arms freeze and its own authorisation under either gate verdict.

The campaign effects and intervals, gate estimates and verdict, applicable C1 audit extracts,
and realised T1 populations and evidence bindings remain placeholders.

## Draft checks

Fresh builds from the pinned standalone manuscript using its README commands.

| Variant | Build | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---|---|---|---|
| Gate not passed | `latexmk -pdf`, rc 0 | p. 8 | 44 | `0995b041a96bb38021a63e94ac615fa6e51996aa629690cde5c8fa81ea1dbe09` |
| Gate passed | `latexmk -pdf` with `DraftGatePassed`, rc 0 | p. 8 | 43 | `b6a1bbe773aa83e40328679f3673bd91ff440bdc1b84c95f87e9f0d678265cd1` |

Every page matched the corresponding published pre-migration draft in extracted text.
Rendered page 8 of both and verified the transition from limitations to references. The
logs show zero unresolved citations, references or duplicate labels and nine existing
overfull boxes per build. The `FinalPaper` guard stopped at the unset gate outcome, rc 12.
`git diff --check` passed. No code changed. The claim-to-table sheet SHA-256 is
`23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.

Decided alone to preserve the assigned worktree after confirming that its 15 modified
paths already match published main byte for byte. The standalone clone was clean. The
linked research Git metadata is read-only in this environment, so origin fetches and
reporting used temporary metadata, and the builds used a temporary archive of the
pinned manuscript.

## Next round

- **Screening, Compute's first item.** The first attempt `SMEAS_EVIDENCE_20261127T1032Z`
  under run ID `smeas-20261123-a` stopped at the runtime probe with 0/10,164 runs
  and no process left. The signed re-issue is published at `b2f94c29`, review ACCEPTED.
  Re-issued note SHA-256 `7c3c8313e90016fa1ff6773bd678e95e5c6ed9457b14d01631897499ee0fdeb0`,
  companion SHA-256 `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`.
  Check `compute/20261127-25` for strict preflight and a fresh attempt stamp before any
  duplicate submission. No re-issue receipt is in the fetched Compute report. A decision-node
  SHARED finding goes to the author before D.3 binds.
- **D.3 blocked at step (8).** The full revision 4 step-(5) and binding-only re-checks are
  ACCEPTED (`local/20261127-22`, review tip `0c691ce8fea74f0d86361d40c0c11315f0103aee`,
  review SHA-256 `459c5bc4dbc332c18bf6b2e3eb860b4db63ff85cbb216eabaac074a975048a30`).
  The coordinator recorded that revision 4 was frozen before screening disposition
  (`9cd5863c`, frozen document SHA-256
  `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745`).
  Step (8) is held and the author has been informed. Check screening disposition, then the
  coordinator's binding decision, reviewed real counts for infrastructure attempts and
  proposer GPU time, approved placement, per-arm smoke, and stage authorisations. D.3b
  also needs frozen arms and the approved sidecar.
- **Running elsewhere, latest recorded sample 11:40 UTC.** Compute `51dcef4a` records TASL-2
  expansion `g1b-x-tasl-20261126-a` with ETTh1 and MetaMaze sealed. Forest Cover PID
  `106573` was in joint on CPUs 4–7 with 79 run files and Titanic PID `106578` was at
  109/150 split runs on CPUs 12–15. Check both seals and per-node determinism, then
  the houseprice retry `compute/20261127-15` once the 0–7 leases permit it. The previous
  waiter `208315` exited before launch.
- **G.5, offline gate and C1 pending.** Check remaining TASL-2 P11 tests, the valid
  pre-run spec/note sequence, final bindings and review, and coordinator publication of
  the G.5 note. Then check eligible labels, T1 train/dev release, reviewed consumer and
  preregistration bindings, trained and calibrated frozen arms, and the signed test releases.
  The writer fills tables from the authorised D.3, gate and applicable C1 extracts.
- **Ada and scheduler.** `compute/20261127-24` is ready for checkpointed 4B re-probe
  `trackp-p4-probe-20261127-b` on an empty Ada card. Check receipt and lease before launch.
  The first probe `trackp-p4-probe-20261125-a` is complete and the two 4B arms hit the
  signed OOM STOP. H200 `760065` and D.3 preflight `760148`, `760149`, `760152` were
  removed after no match. `compute/20261127-12` is idle pending an eligible L40S or A100
  match. The recorded idle `759624` and `759625` belong to other work.
