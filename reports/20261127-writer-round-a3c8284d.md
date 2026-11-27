# Paper B writer round close — 27 November 2026

Research base `a3c8284dfc9eec5d06eeb9cd92f4c1255078d928`.
Coordinator queue `0cd257567d424c3f0268b51a67fddf49a0cad3f3`.
**Writer idle.** There is no new task ID or writer handoff. All five writer cards are on research main.
The next writer task is runbook §3 item 4. Fill the result tables from authorised extracts, apply the
declared outcome readings, then rebuild both drafts for review.

| Task | Delivery branch and tip | Recorded review | Published merge |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The title and trim have no separate re-review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

## Question, measurement and claim

Which control decisions improve campaigns at the same caps of 20 worker runs and 80 manager calls,
and by how much? A published Sweep 1 replay classified 3,274 of 4,999 proposals as duplicates. That
motivates testing a rule that skips duplicates and detectable no-ops. D.3 pairs arms on the same fresh
campaign instances and measures the final gain over the starting configuration using ten fresh audit
seeds, in units of the node's reference standard deviation. A0R − A0 estimates the effect of adding
the rule layer to default keep. A2 − A0R estimates the incremental effect of the noise-aware policy.
A3 − A2 and A5 − A2 estimate gains from using the respective learned forecast in place of the constant
forecast. Paired effects, intervals and the declared Holm decisions determine which claims the campaign
supports. The separate, unread offline gate tests one-step decisions on logged proposals. D.3b runs
after the arms freeze and its stage authorisation under either gate verdict.

Campaign, gate and C1 effects and intervals, realised T1 populations, evidence bindings and approval
fields still have placeholders. The SGM citation also has an author verification placeholder.

## Draft builds and hashes

[Manuscript main](https://github.com/dowlingwong/paper_B_manuscript) and the research submodule pin both
resolve to `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`.

| Draft | Build | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---|---:|---:|---|
| Gate not passed | `latexmk` exit 0 | 8 | 44 | `7a12b5db1783a317a2369694c5f2709419409b0c41987e29227f9cc341f9a78d` |
| Gate passed | `latexmk` exit 0 | 8 | 43 | `37e0105c34ed31016fb4e4b82b845bb0f89901d41880a47c80a4985410bfea7b` |

Extracted text matches both published snapshot PDFs. Visually checked the title, results, and
references transition. Final logs have no undefined citations, undefined references, or duplicate labels.
The nine existing overfull boxes per draft remain. `FinalPaper` stopped on the unset gate-outcome
switch (exit 12). `git diff --check` passed. The existing review verdicts apply to the published cards.
This round required no manuscript edit, delivery branch, code test suite, or new manuscript review.

| Published source | SHA-256 |
|---|---|
| `docs/r1/reports/MAC_M3_DRYRUNS_20261104.md` (Sweep 1 duplicate count) | `f39f112c9687f63c6a8c05013b917af847ff1f03a470404942e4fdfea5ac27ea` |
| `docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md` | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md` (frozen rev 4) | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |

Decided alone to build the pinned source in scratch and to use temporary Git metadata for fetch and
reporting because the assigned worktree shares write-restricted Git metadata. The 15 modified paths in
the assigned worktree match published research main and were preserved. No sealed partition was opened
and no job was submitted.

## Next round checks

Job states come from the latest Compute receipt `6ec7bccbf3a27fe5905105c6c26113a9fcecd3c7` and the
coordinator queue. The expansion figures are from the 14:05 UTC host sample.

| Lane | State and next dependency |
|---|---|
| Expansion G.1b running elsewhere | TASL-2 run `g1b-x-tasl-20261126-a` (`compute/20261126-10`). ETTh1 and MetaMaze sealed. Forest Cover PID `106573` at 111/150 joint runs and Titanic PID `106578` at 45/150 at last check. Check exits, seals, assembly and per-node determinism before G.5 addenda. |
| Houseprice, P11 and G.5 blocked | Houseprice waiter `208315` exited before any run. Check the CPU 0–3 and 4–7 leases after Forest Cover seals. Remaining P11 checks need their accepted route and combined host record. G.5 then needs final binding, review and publication. |
| Screening evidence STOP | Preserve `SMEAS_EVIDENCE_20261127T1155Z` at 30/10,164. The fixed cache and 168/168 engineering smoke are published at `523ccfbc`. Second re-issue `78dfbada` is independently ACCEPTED, SHA-256 `9b86e40cec73cc9e39be004c4479059d0c8977184b78f244b376b9acd9005e2a`. Check the author signature, published note, strict preflight and fresh attempt ID. |
| D.3 evidence held | R1-D3-STEP8-HOLD keeps step (8) and all campaigns pending the screening result. With no SHARED decision node, proceed on rev 4. A SHARED result requires the author's extra-arm decision. The Ada engineering smoke card `compute/20261127-27` is ready. No job ID was reported. Pool jobs `760148`, `760149` and `760152` were removed. Check for an eligible L40S/A100 match. |
| P.4 P3 merged and Ada P5 ready after D.3 smoke | P3 runner `8c8b9fec` is on main at `a3c8284d` with ACCEPTED review. Check `compute/20261127-29` for the staged smoke, E0 equivalence and timing disposition, and check the SSH-signed spec and phase-1 approval. No P5 or phase-1 job ID was reported. The 4B re-probe `trackp-p4-probe-20261127-b` passed. H200 request `760065` was removed without a match. |
| Paper C E-INT waits for Ada allocation | `compute/20261127-28` takes a separate eligible Ada card after the D.3 engineering smoke secures its card. Paper B keeps priority. Check for a smoke or census job ID. |
| Writer result tables blocked | Await released D.3, gate and C1 extracts. The gate requires completed G.5 labels, T1 train/dev release, reviewed target-consumer and preregistration bindings, the frozen arms and the signed test releases. D.3a and D.3b require their own authorisations. D.3b also requires frozen arms. |
