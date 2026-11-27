# Paper B writer round close — 27 November 2026

Research base `d669b0bf2c544d8740d3c5965153a8a05a078226`.
Coordinator queue `3f096503e87218bde149f003f2f1298f2c6de761`.
**Writer idle.** No new task ID or direct writer handoff. The five assigned cards are published.
The next writer action is runbook §3 item 4: enter authorised estimates and intervals, apply the declared readings,
and rebuild both drafts for independent review.

| Task | Delivery branch and tip | Recorded review | Published merge |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections recorded. Title and trim had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections recorded. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

## Question, measurement and claim

Which control decisions improve an autoresearch campaign with the same caps of 20 worker runs and 80 manager calls,
and by how much? The published Sweep 1 replay found that 3,274 out of 4,999 proposals repeated a configuration
already evaluated. This motivates testing a rule that skips duplicates and detectable no-ops.
D.3 pairs arms on fresh campaign instances and measures final improvement over the start on ten fresh audit seeds,
in units of the node's reference standard deviation. A0R − A0 isolates the rule layer under default keep.
A2 − A0R isolates the noise-aware rule with that layer in place. A3 − A2 and A5 − A2 compare learned forecasts
with the constant forecast. The paired estimates, intervals and declared Holm decisions determine what the paper
can claim. The offline gate tests one-step utility on logged proposals. It is unread. D.3b proceeds under
either gate verdict after the arms freeze and its own authorisation.

The D.3, gate and C1 effect estimates and intervals, realised T1 populations, evidence bindings and approval
placeholders are still in place. Each theory statement remains subject to the recorded proof conditions.
No result was inserted.

## Draft checks

[Manuscript repository](https://github.com/dowlingwong/paper_B_manuscript) `main` and the
research submodule pin both resolve to `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`.

| Draft | `latexmk -pdf` exit | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---|---:|---|
| Gate not passed | 0 | p. 8 | 44 | `c8a8fdedcd3529473b2fa419acae8dc340ce5b7dc76c711523995b449f6d54fc` |
| Gate passed | 0 | p. 8 | 43 | `f25c539023c0f3af7cfec7ce3db9bca41edea08364cfbbcadd94465c934b61de` |

Both builds followed the pinned README and matched the corresponding published pre-migration PDF text on every
page. The title, framing, results and references transition were checked on rendered pages. The logs show nine
existing overfull boxes per draft and zero undefined references, undefined citations or duplicate labels. The
SGM citation's author verification placeholder is still visible. The `FinalPaper` guard stopped at the unset
gate outcome (exit 12). `git diff --check` passed. This status report carries the existing review verdicts.
No manuscript change, new delivery branch or code test run was needed.

| Source verified on published research main | SHA-256 |
|---|---|
| `docs/r1/reports/b2_audit_20261119/counts.json` | `568c44dd101d57b7efa3b6577a426e4a9dd7a270a6e69a5f7c6eada1e9cb5e85` |
| `docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md` | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md` (frozen rev 4) | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |

Decided alone: build in scratch from the pinned standalone source and use temporary Git metadata for the fetch and
report because the assigned worktree's shared Git directory is write-restricted. All 15 modified paths in the
assigned worktree match the published research tree and were preserved. No sealed data was read and no job was submitted.

## Next round checks

Reported activity comes from Compute `6ec7bccbf3a27fe5905105c6c26113a9fcecd3c7` (host sample 14:05 UTC),
Local `45bd74aa1541b20a0202badbfa34fca16a22a807`, and the coordinator queue above.

| Lane | Status and next dependency |
|---|---|
| **Expansion G.1b running elsewhere** | `compute/20261126-10`, TASL-2 run `g1b-x-tasl-20261126-a`. ETTh1 and MetaMaze sealed. Forest Cover PID `106573` at 111/150 joint runs and Titanic PID `106578` at 45/150 in the last sample. Check both exits and seals, then assembly and published determinism. |
| **Houseprice, P11 and G.5 blocked** | Prior houseprice waiter `208315` exited before any run. `compute/20261127-15` needs TASL-2 leases 0–3 and 4–7 after Forest Cover. Remaining P11 checks need the note or a synthetic spec and the C10/C11 route. G.5 waits for the final binding, accepted review and publication. |
| **Screening STOP, re-issue ready for signature** | Evidence attempt `SMEAS_EVIDENCE_20261127T1155Z` stopped at 30/10,164 after the OpenML cache changed. The fixed cache and 168/168 engineering smoke are reviewed and published at `523ccfbc`. Exact second re-issue draft `mac-screen-note-reissue-2-20261127` @ `78dfbada` is independently ACCEPTED. Draft SHA-256 `9b86e40cec73cc9e39be004c4479059d0c8977184b78f244b376b9acd9005e2a`. Check for author signature, coordinator publication, strict preflight and a fresh attempt ID. |
| **D.3 hold and Ada engineering lane** | R1-D3-STEP8-HOLD keeps step (8) and every D.3 campaign pending the screening result. If no decision node is SHARED, bind rev 4. A SHARED result goes to the author for the extra-arm decision. `compute/20261127-27` is dispatched for per-arm engineering smoke on Ada with no job ID reported. Separate HTCondor preflight is idle without a match. Jobs `760148`, `760149`, and `760152` were removed. |
| **Ada P.4 phase 1 blocked** | Synthetic 4B re-probe `trackp-p4-probe-20261127-b` completed and passed. H200 job `760065` was removed without matching. P2 is published. P3 runner review accepted `8c8b9fec`. Check runner publication, the authorised SSH-signed spec, author tick, and staged Ada smoke/E0 with the timing disposition. No phase-1 job ID recorded. |
| **Paper C E-INT routed to Compute** | `compute/20261127-28` can start its development smoke on a second eligible Ada card after `-27` has a card. Paper B has priority. No E-INT job ID recorded. |
| **Writer result tables blocked** | Await released D.3, gate and C1 extracts. The gate follows G.5 labels, T1 train/dev release, reviewed target-consumer and preregistration bindings, the frozen trained and calibrated arms, and signed test releases. D.3b also needs the frozen arms. Recheck the writer queue when a release or handoff is published. |
