# Paper B writer round close — 27 November 2026

The writer queue is idle at research base `4a9a1f4aaaadca90edf1ae481cec3163a67e42b0`
and coordinator queue `d6943f1a5ed78bc3496000e1160fe086577dc663`. No new
writer task ID was issued. All five assigned cards are already published.
The next writer work is runbook §3 item 4, pending authorised evidence
and a task card.

| Task ID | Delivery branch and tip | Recorded review verdict | Published merge |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. Title and trim had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

## Question, measurement and claim

Which control decisions improve an autoresearch campaign when each arm
has the same caps of 20 worker runs and 80 manager calls? The published
Sweep 1 replay counted 3,274 duplicates in 4,999 proposals. This motivates
testing a rule that skips duplicate proposals and detectable no-ops.
D.3 pairs arms on fresh campaign instances. It measures how much the final
configuration improves over the start on ten fresh audit seeds, in units
of the node's reference standard deviation. A0R − A0 measures what the
rule layer adds under default keep, A2 − A0R measures what the noise-aware
decision rule adds with that layer in place, and A3 − A2 and A5 − A2
measure what learned forecasts add. The paired estimates, intervals and
declared Holm decisions will determine which gains the paper can claim.

The offline gate separately tests one-step utility on logged proposals.
It is unread. D.3b requires frozen arms and its own authorisation and
proceeds under either gate verdict. Campaign effects and intervals, the
gate outcomes, the C1 audit extracts, realised T1 populations, evidence
bindings, and the outstanding proof and citation checks remain open.

| Published file | SHA-256 |
|---|---|
| Sweep 1 counts, `docs/r1/reports/b2_audit_20261119/counts.json` | `568c44dd101d57b7efa3b6577a426e4a9dd7a270a6e69a5f7c6eada1e9cb5e85` |
| Claim-to-table sheet, `docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md` | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4, `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md` | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Screening cache STOP, `docs/r1/reports/screen_measure_stop_20261127b/SCREEN_MEASURE_STOP_20261127B.md` | `c85bdc65d4d02c43093153b01966318244bcd11c837f16892a28e86ebf6b3ad6` |
| Unsigned Ada phase-1 draft, `docs/r1/proposals/TRACKP_P4_PHASE1_ADA_NOTE_DRAFT_20261127.md` | `9a907ce195904d430fab6042d878873398363b13184617b34d4c4ee4cd128bf1` |

## Draft checks

The research submodule pin and [manuscript repository](https://github.com/dowlingwong/paper_B_manuscript)
`main` agree at `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. Both
`latexmk -pdf` builds followed that revision's README.

| Draft preview | Build exit | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---|---|---|---|
| Gate not passed | 0 | p. 8 | 44 | `805549836cc47c11aba58cf619b83a10b416df52f90d6d5a0b4e62c599ad3452` |
| Gate passed | 0 | p. 8 | 43 | `28412625fb316480374b2a97b7e5a9416cc6ed4b026f6d323f3a36eba8e1388a` |

The extracted text of every page matched the corresponding published
pre-migration PDF. I rendered and checked the introduction, results,
contrast and gate tables, and references transition. Both logs have
nine existing overfull boxes and zero undefined citations, undefined
references or duplicate labels. The existing SGM citation still displays
its author verification placeholder. `FinalPaper` stopped at the unset
gate outcome as expected (exit 12). `git diff --check` passed. This round
adds a status report only. No manuscript delivery branch, new manuscript
review verdict or code test suite applies.

I used temporary Git metadata and a scratch manuscript checkout because
the assigned worktree's shared Git directory is write-restricted. I
checked all 15 modified paths in the assigned worktree against published
main and left them in place. No sealed partition was read. Compute
owns live host checks and job submissions.

## Next checks

Job state is from the latest compute receipt `bf57e012ca81792f773f5e602bba90c594afb5d0`
(13:20 UTC). The screening handoff is from the later coordinator queue.
The Ada P2 handoff is from `coord/local` @ `8ec7972956ee3f34951b3992546cf05af2fc22f3`.

| Lane | State and next dependency |
|---|---|
| Expansion G.1b running elsewhere | `compute/20261126-10`, TASL-2 run `g1b-x-tasl-20261126-a`. ETTh1 and MetaMaze are sealed. Forest Cover PID `106573` and Titanic PID `106578` were active at the last check. Check exits, both seals, assembly and the published determinism decisions. |
| Houseprice, P11 and G.5 blocked | Houseprice waiter `208315` exited before launch. `compute/20261127-15` needs both TASL-2 0–3 and 4–7 leases after Forest Cover. Note-dependent P11 checks need the G.5 note or a routed synthetic smoke spec. The C10 long span and C11 audit-chunk check need an eligible TASL-7 GPU. G.5 needs the final binding, accepted review and note publication. |
| Screening STOP and engineering handoff | `compute/20261127-25` attempt `SMEAS_EVIDENCE_20261127T1155Z` stopped after 30 of 10,164 runs because the OpenML cache tree changed. The independently accepted fix (`e9d7f230`, 83 focused tests and zero new full-suite failure IDs) is published at `83425c70`. `compute/20261127-26` is queued to rebuild the cache and repeat the 168-run engineering smoke. Check the new tree and manifest SHA-256, runtime records and smoke result before the author's second re-issue. No launch ID is recorded on this card yet. |
| D.3 blocked on screening | Author row R1-D3-STEP8-HOLD is published at `4a9a1f4a`. Step (8), which binds the frozen hash in the D.3a note and outcome tables, and every D.3 campaign wait for the screening result. If no decision node returns SHARED, step (8) proceeds on rev 4. If any returns SHARED, the author decides on the seventh D.3a arm. Adding it requires reviewed, signed and frozen rev 5. Per-arm smoke still needs a matched layout, arm list and authorisation. |
| HTCondor preflight idle | `compute/20261127-12` has no eligible ETP L40S or TOpAS A100 match. Earlier jobs `760148`, `760149`, `760152` were removed. Check for a match and the next receipt. |
| Ada phase 1 blocked before signature | Synthetic re-probe `trackp-p4-probe-20261127-b` completed. H200 request `760065` was removed. Local P2 eligibility record is independently ACCEPTED at task tip `0798e8697384d7f3343df91a17bbdfc137bd51ae` and awaits publication. P3 runner pins are in progress under `local/20261127-25`. P4 author tick and P5 Ada smoke/E0 and timing disposition follow. |
| Writer result tables blocked | Wait for the signed releases and reviewed extracts for D.3, the offline gate and C1. The gate needs eligible G.5 labels, T1 train/dev release, bound consumers and preregistration, frozen trained and calibrated arms, and test release. Fill estimates, intervals and declared readings as those releases arrive. The coordinator publishes reviewed manuscript updates to main. |
