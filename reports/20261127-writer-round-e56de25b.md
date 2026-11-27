# Paper B writer round close — 27 November 2026

The writer queue is idle at research base `e56de25bb2237e2a98327e744da0abb0e97ba96e`
and coordinator queue `f6e087af46ea03992d02c0fbc20dfd38b1611bdc`. All five
assigned cards are published. The result-table handoff in runbook §3 item 4 awaits
authorised evidence and has no task ID. The earlier delivery states in the Writer
section of STATE.md are superseded by the published merge ancestry below.

| Task ID | Published delivery branch and exact tip | Recorded review verdict | Published merge |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. Title and trim follow-up had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

## Question, measurement and claim

Which decisions improve an autoresearch campaign under the same caps of 20
worker runs and 80 manager calls? The published Sweep 1 replay counted 3,274
duplicates in 4,999 proposals. That count motivates testing whether skipping
duplicates and detectable no-ops improves the final result. D.3 pairs
campaigns on fresh instances and measures the final configuration's gain over
its start on ten fresh audit seeds, in units of the node's reference standard
deviation. A0R − A0 measures what the rule layer adds under default keep.
A2 − A0R measures what noise-aware decisions add with that layer in place.
A3 − A2 and A5 − A2 measure what the learned forecasting arms add. The paired
estimates, intervals and declared within-family decisions will determine
which gains the paper can claim. The offline gate separately tests one-step
utility on logged proposals. D.3b proceeds after arms freeze and authorisation
regardless of the offline verdict.

The published Sweep 1 count record,
`docs/r1/reports/b2_audit_20261119/counts.json`, has SHA-256
`568c44dd101d57b7efa3b6577a426e4a9dd7a270a6e69a5f7c6eada1e9cb5e85`.
The published claim-to-table sheet SHA-256 is
`23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.
Campaign effects and intervals, gate estimates and verdict, C1 audit
extracts, realised T1 populations and evidence bindings remain placeholders.

## Draft checks

The [standalone manuscript repository](https://github.com/dowlingwong/paper_B_manuscript)
main and research submodule pin agree at `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`.
Both builds followed that revision's README.

| Variant | Fresh build | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---|---|---|---|
| Gate not passed | `latexmk -pdf`, rc 0 | p. 8 | 44 | `c0bf4b12c94439578bd759b38aafd6f1ef497d6284153a682e71613cecb9e71a` |
| Gate passed | `latexmk -pdf` with `DraftGatePassed`, rc 0 | p. 8 | 43 | `d56a6bcb48cd2d87f9b4472661bae39e23f7ef6e6aa5e19993281744f05b415d` |

Both rebuilds match the extracted text of their published pre-migration PDFs.
I rendered and checked page 8 in both variants, where limitations end and
references begin. Both logs have nine existing overfull boxes and zero
undefined citations, undefined references or multiply defined labels.
`FinalPaper` stopped at the unset gate outcome as expected (rc 12).
`git diff --check` passed. This round added no manuscript unit, so no new
delivery branch, review verdict or code test suite applies.

Decided alone to preserve the 15 locally modified paths after verifying
that each matches its published blob. The Build and Git operations used
temporary directories because the assigned worktree's shared Git metadata
is write-restricted. No server job was submitted and no sealed partition
was read.

## Next checks

Job states below come from the Compute receipt
`bf57e012ca81792f773f5e602bba90c594afb5d0` (13:20 UTC) and the Local handoff
`c289779ef214c4eef512895291fb00d03c83c9ea`.

| Lane | State and next dependency |
|---|---|
| Expansion G.1b running elsewhere | `compute/20261126-10`, TASL-2 run `g1b-x-tasl-20261126-a`. ETTh1 and MetaMaze are sealed. Forest Cover PID `106573` (CPUs 4–7, 88/150 joint runs) and Titanic PID `106578` (CPUs 12–15, 26/150 joint runs) were active. Check exits, both seals, assembly and the published determinism decisions. |
| Houseprice, P11 and G.5 blocked | Houseprice waiter `208315` exited before launch. `compute/20261127-15` needs the 0–7 leases after Forest Cover. P11 C2/C4/C5/C6/C9/C14/pre-run C15 need the signed note or a routed valid synthetic smoke spec. C10 long-span and C11 audit-chunk checks need an eligible TASL-7 GPU. G.5 needs the final binding, accepted review and note publication. |
| Screening STOP | `compute/20261127-25`, attempt `SMEAS_EVIDENCE_20261127T1155Z`, stopped after 30 of 10,164 runs because the OpenML cache tree changed. Published STOP record SHA-256 `c85bdc65d4d02c43093153b01966318244bcd11c837f16892a28e86ebf6b3ad6`. `local/20261127-23` delivered the accepted fix at `e9d7f230016ee32a1a338e83af4c01dfd467aeb2`, exact code `c12136d664ae588a2539b76b2602e36742979ce8`, 83 focused tests passed with zero new full-suite failure IDs. The coordinator is checking the merge. Compute then rebuilds the cache and repeats the smoke before a second author-signed re-issue. |
| D.3 and HTCondor blocked | Full rev 4 step-(5) re-check ACCEPTED, SHA-256 `459c5bc4dbc332c18bf6b2e3eb860b4db63ff85cbb216eabaac074a975048a30`. Frozen rev 4 SHA-256 `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745`. The coordinator recorded the early freeze and holds step (8) for screening disposition. Per-arm smoke also needs an eligible matched layout and dispatch with the arm list and authorisation. Preflight `compute/20261127-12` has no GPU match. Prior jobs `760148`, `760149`, `760152` were removed. No campaign is active. |
| Ada phase 1 blocked before signature | Synthetic 4B re-probe `trackp-p4-probe-20261127-b` completed and the older H200 request `760065` was removed. Phase-1 draft `mac-p4-phase1-ada-note-20261127` @ `68ed7514609d4d88f4b52b5ddb59a515a2d8dac5` was ACCEPTED for the blocked desk handoff and published unsigned at this base. Draft SHA-256 `9a907ce195904d430fab6042d878873398363b13184617b34d4c4ee4cd128bf1`. `local/20261127-25` handles P2 Kev eligibility and P3 reviewed runner pins. P4 author tick and P5 Ada smoke/E0 and timing disposition follow. |
| Writer result tables blocked | Wait for the signed releases and reviewed extracts for D.3, the offline gate and C1. The offline gate still needs eligible G.5 labels, T1 train/dev release, bound consumers and preregistration, trained and calibrated frozen arms, and the signed test releases. D.3b also needs the frozen arms. Fill only the authorised estimates and intervals and use their declared readings. |
