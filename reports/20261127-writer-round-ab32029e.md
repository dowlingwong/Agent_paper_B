# Paper B writer round close — 27 November 2026

Writer is idle. All five dispatched writer cards are published. The next writer
handoff is the result tables (next-phase runbook §3, item 4). It has no task ID and
is pending the authorised evidence releases. Published research base
`ab32029ec6af333d48e49262130ff928b105737f`, coordinator queue
`136083a995cf065f9e1223f2a1b4cf5357998d7f`, and Compute receipts
`977953e27d51c13f7c8906c520dde760c53df0be`.

| Task | Delivery branch and exact tip | Review on record | Published merge |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The author-directed title and trim had no separate review. | `6bc4f0df` |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. | `4490a0a9` |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. | `03a352d9` |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. | `e153df24` |

The four delivery tips are ancestors of the published research base. The current
[standalone manuscript](https://github.com/dowlingwong/paper_B_manuscript) is at
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`, matching the published submodule pin.
This round verifies that commit. Future manuscript changes use task branches in
the standalone repository and the coordinator handles publication and pin updates.

## Question, measurement and claim

Which control decisions improve a campaign at the same caps of 20 worker runs and
80 manager calls? Sweep 1 replay classified 3,274 of 4,999 proposals as duplicates.
That count motivates testing the rule that skips duplicates and detectable no-ops.
D.3 pairs controllers on fresh campaign instances and measures the final configuration's
gain over the starting configuration on ten fresh audit seeds, scaled by each node's
reference standard deviation. A0R − A0 measures the gain from the skips under the
default keep rule. A2 − A0R measures what the noise-aware rule adds with the skips
in place. A3 − A2 and A5 − A2 measure what each learned forecast adds. The paired
effect estimates and intervals, read under the signed within-family rules, determine
which gains the paper can claim. The offline gate tests one-step decisions on logged
proposals. D.3b runs under either gate outcome once the arms are frozen and the
campaign is authorised.

Sweep 1 count source: `docs/r1/reports/b2_audit_20261119/counts.json` at `f77e5ba9`,
SHA-256 `568c44dd101d57b7efa3b6577a426e4a9dd7a270a6e69a5f7c6eada1e9cb5e85`.
The campaign effects and intervals, gate estimates and verdict, applicable C1 audit
extracts, and realised T1 populations and evidence bindings remain placeholders.
The claim-to-table sheet SHA-256 is
`23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.

## Draft checks

Both variants were rebuilt from the pinned standalone source using its README commands.

| Variant | Build | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---|---|---|---|
| Gate not passed | `latexmk -pdf`, rc 0 | p. 8 | 44 | `0c756b65a0c4023268ef980564d436868b69ba14c270dfc4ff3b44e826d474ab` |
| Gate passed | `latexmk -pdf` with `DraftGatePassed`, rc 0 | p. 8 | 43 | `5412af60d9ef46d89077d64607ba755ab34f973db3661e57321d2595f1de6139` |

Extracted text matches the corresponding published pre-migration PDF throughout.
Page 8 of each variant was rendered and inspected for the transition from limitations
to references. Both final logs have zero unresolved citations, references or duplicate
labels, and nine existing overfull boxes. The `FinalPaper` build stopped at the unset
gate-outcome switch, rc 12. `git diff --check` passed. This is a verification and
queue reconciliation round, so the review verdicts are those on record in the table.
There was no new manuscript change or code test suite run.

Decided alone to preserve the 15 modified research files after verifying that each
matches the published tree. The linked Git metadata is read-only in this session.
Fetch and reporting used writable temporary Git metadata and the builds used an archive of
the pinned manuscript. This round submitted no jobs and accessed no sealed result data.

## Pending work and recorded jobs

| Lane | Latest receipt and next check |
|---|---|
| Screening **STOP** | `compute/20261127-25`, attempt `SMEAS_EVIDENCE_20261127T1155Z`, stopped at 30/10,164 recorded runs when `fetch_openml` materialised another ARFF path and the cache-integrity check tripped. See published STOP at `ab32029e`, record SHA-256 `c85bdc65d4d02c43093153b01966318244bcd11c837f16892a28e86ebf6b3ad6`. The re-issued note and companion hashes are `7c3c8313e90016fa1ff6773bd678e95e5c6ed9457b14d01631897499ee0fdeb0` and `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`. Check `local/20261127-23` for the reviewed cache fix and smoke-path reconciliation, then Compute's rebuilt cache hash and engineering smoke, and a second author-signed re-issue before a fresh evidence launch. |
| D.3 held | The coordinator froze revision 4 before screening disposition. Step (8) is held and the author has been informed. Frozen declaration SHA-256 `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745`. Check the screening result and author/coordinator disposition before the binding, approved placement, per-arm smoke and campaign authorisations. The real infrastructure-attempt counts and proposer GPU time need reviewed sources. D.3b also needs frozen arms and an approved sidecar. |
| Expansion G.1b **running elsewhere** | Last recorded sample 11:40 UTC in Compute `51dcef4a`. TASL-2 run `g1b-x-tasl-20261126-a`: ETTh1 and MetaMaze sealed, Forest Cover PID `106573` on CPUs 4–7, Titanic PID `106578` on CPUs 12–15. Check exits, seals, assembly and per-node determinism. |
| Houseprice, P11 and G.5 **blocked** | Houseprice waiter PID `208315` exited before launch. Check 0–3 and 4–7 leases before `compute/20261127-15`. TASL-7 P11 is accepted. The TASL-2 checks in `compute/20261127-05/-08` still need the corrected pre-run binding and leases. G.5 campaigns require the published note and strict check. The gate and applicable C1 extracts depend on eligible labels, releases, reviewed consumer and preregistration bindings, frozen arms, and signed test releases. |
| Ada re-probe **dispatched** | `compute/20261127-24`, expected attempt `trackp-p4-probe-20261127-b`. No start receipt in the fetched reports. Check the Ada lease and submission ledger, then the two checkpointed 4B outcomes and review for the phase-1 note. |
| D.3 batch preflight **idle** | `compute/20261127-12` is waiting for an eligible ETP L40S or TOpAS A100 match. Jobs `760148`, `760149` and `760152` were removed, as was the separate P.4 H200 request `760065`. Idle IDs `759624` and `759625` belong to other work. |

Next writer action is to populate the result tables from released estimates and
intervals, using the signed interpretation for each outcome. The report supersedes
the job states in [the preceding writer round](20261127-writer-round-9cd5863c.md).
