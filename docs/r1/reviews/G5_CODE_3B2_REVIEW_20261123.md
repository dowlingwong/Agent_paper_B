Reviewed base: `926ad83b` (the accepted part 3b-1, READY 89), with the merge `b7b6e9cf` of READY 86; accepted at `0f9e8773`, confirmed at `166d692a2b35f25cf70c7f8d1d19421652a0d92f` (report wording point applied at `3652f4c1`)

# Independent review record — the G.5 code unit, part 3b-2: the seal step, the access-logged sealed reader, the locked two-stage assembly of the T1 label table, the release locks in every reader, the REL-T1-G1B copy step, the G5-TASL-GPUH B meter from TASL-7 server spans, close-server and the `g5_integrity` release check

**Unit.** On `mac-g5-code-3b2-20261123` over `926ad83b` (part 3b-1): `sweep2/t1_tasl/g5_seal.py` (seal steps for the whole 3b-1 seal list into `.partial` siblings renamed after a receipt naming every file's sha256, tars verified member by member before any source is removed, an `out/` left in clear sealed as `out_clear.tar`; `SealedTree`, which checks the purpose's release lock and writes an access-log line with the kind and members before opening, opens only ledgers, a plan or a chunk, and reduces a chunk's rows to the purpose's stage so that no evaluation-seed kind or value leaves it at train/dev; STOP 11 over TASL-2's and TASL-7's access logs; `seal_server` (option a for `llama-server.log`); `close-server`; registered server spans server-1..N, a gap counted open; encryption refused as not built), `sweep2/t1_tasl/g5_assemble.py` (train/dev stage under R1-T1-LABELS-UNSEAL reading label seeds only; test stage under both rows re-deriving the table and label block byte-identically before writing the evaluation block; row shapes of `audit.evidence_blocks` and the frozen builder; the table readings (`refuse` | `neg_inf` | `leave_out`) taken only from the signed note, `refuse` without a note; `read_evidence` needs the test row except inside the release integrity check; `verify_evidence`), `sweep2/t1_tasl/g5_relcopy.py` (the REL-T1-G1B copies with `crosscheck_gate.json`, matching 3a's checks), changes to `g5_job.py` (GPUH B meter from server spans; close-attempt metered to the closing time with the latest mtime recorded), `g5_tasl.py` (CLI seal-attempt/node/run, seal-server, close-server, server-span, assemble, rel-copy; note lines `t1_table_readings` and `server_log`), `g5_tasl_spec.json`, `r1/c3/release_checks.py` (registers `g5_integrity` under REL-CODE A, with a publication check over every `IMPORT_SOURCES` file and the spec), `r1/tests/test_t1_g5_seal.py` (30) and the report `docs/r1/reports/g5_code_20261123/G5_CODE_3B2_20261123.md`. The coordinator merged READY 86 (`fbbac887`) into the branch at `b7b6e9cf`, because both change `release_checks.py`; the reviewer confirmed the sweep-1 and sweep-2 checks are byte-for-byte as accepted in READY 86. Authority: the G.5 draft revision 8 §3, §4, §6, §9, §10; PRE-STAGE, PRE-T1; REL-T1-G1B, REL-SCOPE, R1-SWEEP2-RELEASE-DECISIONS; the coordinating chat's draft queue (unit 3).

**Process.** One independent reviewer, read-only, synthetic data and fakes only (no secrets, sealed data, labels or evaluation values; no server access). Round 1 found two blocking issues (a test that passed only because the branch differed from origin/main; `read_evidence` releasing test labels under the train/dev row) and four majors (evaluation-seed values handed to train/dev callers; table readings settable by a command-line flag; no recovery for a TASL-7 server that ends without its end record; close-attempt metered to the latest mtime) and ten minors. Round 2 accepted with three non-blocking points; n1 (the private opener returning raw rows) was fixed and confirmed, n2 and n3 are recorded as open; the confirmation round's one wording point was applied to report §10.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `b7b6e9cf` | NOT ACCEPTED (B1–B2; M1–M4; minors m1–m10) |
| 2 | `0f9e8773` | ACCEPTED (non-blocking n1–n3) |
| 3 | `166d692a` | ACCEPTED (confirmation; one wording point) |

**Open items.** (1) Author decisions: the T1 table readings (`refuse` proposed; `neg_inf`; `leave_out`, the T0 precedent), signed as the note line `t1_table_readings`; `llama-server.log` option (b), prompt logging off, not built (it changes `server_argv` and needs a validator and spec change; under (a) with one server start the log stays in clear on TASL-7 for the table span); the seal mode (procedural built, encryption not); confirming in the note that the table, readable after UNSEAL, carries campaign values for test instances (as sweep 2's tables after D8). (2) Needed outside this unit: the harness unit (`trackg/audit_g5.py`) writing `outcome.value`; the two T1 release rows and the arms-frozen record; a T1 δ_n derivation for the gate run's noise input; T1 features for A3/A5; the suite-name mapping (`mlagentbench` → `MLAgentBench`) in the arms-frozen `Tier1.suites`; proposer-card hours under GPUH A (a reported figure, before the T1 report); the G.5 files under `sweep2/` and the spec frozen on main from launch to the T1 test release. (3) n2: a crash between a seal's rename and its cleanup leaves clear content; the operator STOPs and reports. n3: `close_server` can be blocked by a reused pid after a reboot; the author decides until a start-time check exists. Optional and not built: the third G.1b note check under G5-ARPEND B. (4) Cluster: write the joined gated G.1b run under `sealed_g1b` (no symlinks) before `rel-copy`; check free disk before sealing; after any `seal-server` register the receipt on TASL-2 with `server-span` at once; after a TASL-7 crash run `close-server` then `seal-server` before any audit; under GPUH B never leave a started server unregistered; run `assemble` at both stages with the same `--note`; run the release integrity check from a clean published checkout without the sweep-1 options.

## Round 1 (`b7b6e9cf`)

> Reviewed base: b7b6e9cfb64d2e3e15eb3c0d91d9ce5c89014b84 (the merge tip; the 7 author commits run from 926ad83b511d23b46241bfe6befdb44f9b687d03 to 6bca44f15cc1d39c8d993259af8b8aae77d7ec85)
>
> ## Summary
> I can't accept this unit yet. Most of it is sound: the seal steps and receipts, the access-logged reader with STOP 11, the two assembly stages, the REL-T1-G1B copy step, the GPUH B meter and the `g5_integrity` registration. The merge commit is also correct. All targeted tests pass, each file run on its own: test_t1_g5_seal 19, test_t1_g5_job 23, test_t1_g5_tasl 107, test_c3_release 41, test_c3_sweep1_release_compat 12, test_c3_sweep2_audit 28.
>
> What stops it:
> - One test will fail as soon as the code is on main (B1).
> - One reader gives out test labels with only the train/dev lock (B2).
> - Four major gaps (M1–M4): evaluation values leave the locked reader at train/dev; the table readings can be changed by a command-line flag; a crashed proposer server has no way out; and the close-attempt meter now undercounts.
>
> All of these were checked by running code in scratch (not committed); the details are in each finding.
>
> The merge is clean. Against the READY 86 parent (fbbac887), release_checks.py differs only in the one docstring line and the added `g5_integrity` block. `sweep1_integrity`, `sweep2_integrity` and the compat replay are byte-for-byte as accepted. The merge brings in only READY 86's four files.
>
> ## Blocking
> **B1 — `test_registered_check_refuses_unpublished_g5_code` (r1/tests/test_t1_g5_seal.py) only passes because this branch differs from origin/main.**
> - Failure: once the G.5 code is published, `_g5_published` passes and `verify_evidence` raises FileNotFoundError on `/nonexistent/table/build.json`, which is not the ValueError the test expects. Main's suite goes red at merge.
> - Reproduced: a sparse clone at b7b6e9cf with `refs/remotes/origin/main` set to HEAD gives 1 failed, 18 passed.
> - Fix: create the "differs" and "dirty" conditions on purpose (stub the git calls in `release_checks`, or use a temporary clone). Add a positive test that a published checkout goes on to `verify_evidence` (stubbed).
>
> **B2 — `g5_assemble.read_evidence` returns the whole label block (train, dev and test labels) under R1-T1-LABELS-UNSEAL alone.**
> - This breaks PRE-STAGE A and §6 ("before the test row, readers get the train/dev label block only").
> - Report §3 lists this as the intended lock, and `test_assembly_traindev_then_test` pins it.
> - Scratch check: with a train/dev-only lock it returned rows of the dev, test and train splits.
> - Its only current caller holds both rows, but it is a reader built by this unit with the wrong lock.
> - Fix: `label_block.jsonl` should need the test row (or the integrity context), as `release.guard_raw_label_path` does; or drop the function and read the block inline after both locks. Correct the test and §3.
>
> ## Major
> **M1 — `SealedTree.open_members` gives raw `rows.jsonl`, evaluation-seed values included, to any `assembly traindev:` purpose. The values are dropped only by the caller (`_values`).**
> - Scratch check: `open_members(..., ("out/audit/rows.jsonl",), "assembly traindev: anything")` returned 210 evaluation-seed values. STOP 11 then passed, because the access log does not record which member was read.
> - Ruling on the author's question: reading those bytes into memory is acceptable under §6's procedural seal. It is unavoidable while the engine writes one `rows.jsonl`, and 3b-1 accepted the same pattern. Handing the values back to the caller is not acceptable.
> - Fix:
>   - give `g5_seal` a stage-aware rows reader that strips `outcome.value`, and also the result kind (ok or divergent) at evaluation seeds, before returning anything at train/dev;
>   - allow each purpose only its named members (the ledger pattern, `plan.json`, the chunk members);
>   - write member names into the access log;
>   - add a test.
>
> **M2 — The table readings are not tied to an author decision.**
> - `--divergent-delta-hat neg_inf` is an operator flag on the command line. `build.json` records whatever was chosen, and `verify_evidence` replays it, so the release check cannot catch a choice the author never made.
> - σ_cmp = σ_node and the exclusions are applied with no binding either.
> - Fix:
>   - add the `t1_table_readings` line (and `server_log`) to 3a's `note_lines`;
>   - have `assemble` take the Δ̂ choice from the signed note and refuse if the note's readings differ from `READINGS`;
>   - until then, allow only `refuse`.
> - The report should also list "leave campaign-divergent proposals out of the table" as an option. That is the T0 precedent: rows without a metric are not tabled. The draft requires these proposals to be audited, not tabled, so the report's "must be in the T1 table" does not follow.
>
> **M3 — A TASL-7 server that ends without `server_end.json` has no recovery path.**
> - When it happens: the serve wrapper is killed, an OOM kill, or a reboot. C10 expects restarts over a multi-day span.
> - `seal_server` then refuses forever.
> - Under GPUH B, `require_server_spans` refuses every later audit, and the open span grows until STOP 9.
> - Under either option, `llama-server.log` stays in clear on TASL-7 indefinitely.
> - Fix: add a `close-server` command, guarded like close-attempt (pid gone, same host, lease free). It writes a closed end record with the log's sha256 and the conservative end time (the closing time, with the log's latest mtime recorded beside it); `seal_server` then works. Add tests.
>
> **M4 — close-attempt now meters to the latest mtime (g5_job.close_attempt).**
> - Ruling: not acceptable as the metered value. STOP 9 guards the signed cap:
>   - an overcount is a recoverable STOP that goes to the author;
>   - an undercount is overspend that cannot be undone.
> - It also contradicts this unit's own choice of an upper bound (open spans counted until now) for the proposer card.
> - Fix: `gpu_seconds` = closing time − start. Keep `latest_mtime_utc` and add `gpu_seconds_to_latest_mtime` for C9. An author row may adopt the mtime end later. Update `test_m7`.
>
> ## Minor
> - **m1 — Missing failure-path tests.**
>   - A test-stage re-derivation mismatch. I checked in scratch that the STOP fires and no evaluation block is written, but no unit test covers it.
>   - A partial seal: a crash after `mkdir` leaves a target with no receipt, and a re-run refuses "exists".
>   - A tampered receipt; a partial `seal_node`; span re-registration and gaps.
> - **m2 — Partial seals.** Write into a `.partial` sibling and rename after the receipt, in all four seal steps; and say what the operator does after a partial seal.
> - **m3 — `out_clear.tar` is checked by member names only** before `rmtree(out)`. Compare member sha256s with the source files, as `seal_server` does for the log.
> - **m4 — `G5_PATHS` omits `sweep2/s2_c2_lib.py`.** It is imported through `g4_lib` and is in `IMPORT_SOURCES`, so a committed but unpublished change to it passes the origin/main check. Derive the paths from `IMPORT_SOURCES`.
> - **m5 — A server used only by a closed campaign attempt is never metered.** Close-attempt records carry no `server_record`, so under B such a server is neither metered nor required. `server_attempt` numbers servers contiguously, so require registered spans server-1..N with no gaps, and count any gap as open.
> - **m6 — TASL-7's `ACCESS_LOG.jsonl` is never checked by STOP 11.** `open_server_log` writes it and nothing reads it.
> - **m7 — Missing `outcome.value` on evaluation-seed rows is found late.** At train/dev, a missing value on `ok` evaluation-seed rows is not detected, so a harness defect shows up only after the arms are frozen. Check that the key is present and numeric without keeping the value, or name this in the harness smoke test.
> - **m8 — `derive` does not require `_run` to be sealed,** and it checks the runs-tree job access log rather than its sealed copy.
> - **m9 — Report wording.**
>   - §6.3's parent-divergence rule is not what the code does. The code STOPs when candidate plus parent divergence leaves fewer than half the label seeds, which the frozen builder needs anyway. Partial labels from parent-only divergence are an unstated reading.
>   - §3's `read_evidence` row is wrong (see B2).
>   - §1.1 should say that the runs-tree `out.tar` copies stay in clear after the seal.
> - **m10 — Autoresearch under G5-ARPEND A.** Bind the row's autoresearch summary to the completion record's `noise_floor_copy` (the author's §7.7).
>
> ## Rulings on the author's readings and uncertainties
> - **Evaluation bytes in memory at train/dev:** acceptable, provided the values are dropped inside the reader (M1).
> - **Test labels in the evidence directory after UNSEAL:** consistent.
>   - It follows §6 and PRE-STAGE.
>   - It matches sweep 2: the B.2 evidence directory holds the label block for all splits, and even the evaluation block, before any release.
>   - `release.py`'s test stage requires the same label block.
>   - G.5 is stricter, since the evaluation block exists only after the test row.
> - **Δ̂ for campaign-divergent proposals:**
>   - `refuse` is the right default.
>   - `neg_inf` reproduces the campaign's "never kept" decision and the frozen builder handles it, but it is non-standard JSON.
>   - Leaving these proposals out of the table is the third option (the T0 precedent).
>   - The author decides, and the decision must be bound in the note (M2).
> - **σ_cmp = σ_node:** consistent with T0's fallback for nodes without edit kinds (`dataset.noise_table`). Acceptable once the author signs the line.
> - **Leaving out invalid, refused and final-infrastructure proposals:** consistent with T0, where skipped rows and rows without a metric are not tabled, and they are counted. Acceptable.
> - **Parent divergence STOPs the assembly:** acceptable; it fails closed, and the builder would refuse those labels anyway. The wording needs fixing (m9).
> - **Table open after UNSEAL with test instances' campaign values:**
>   - It is consistent with T0: the sweep-2 tables are readable after the D8 row, and `guard_table` applies the same check to the g5 table.
>   - It is also consistent with PRE-STAGE, which locks labels and evaluation values only.
>   - But §6 keeps per-proposal values in `out.tar` "before release", and the UNSEAL row names only the train/dev label blocks, so the author must confirm this in the note.
> - **Two-stage byte identity:** correct, and it fires on a mismatch (scratch check). Needs a test (m1).
> - **The author's §7 inconsistencies:**
>   - Items 1–6 and 8 are accepted.
>   - Item 6 is satisfiable: `assemble_gated_join` lets the operator choose the destination.
>   - Item 7 is m10.
> - **`g5_integrity`:**
>   - It fits `release.py`'s `check(table_dir, audit_dir, **integrity_args)` and enters the integrity context itself, as the sweep checks do.
>   - Passing the sweep-1 options to it gives a TypeError STOP, which fails closed.
>   - Registering it under REL-CODE A is legitimate without a new author row. The decision already places checks in `release_checks.py`, and the rows draft asks only for a reviewed check and a reviewed extraction step, which this review is.
>   - The origin/main check is otherwise sound: it covers committed differences and tracked modifications, and the shadow check covers `IMPORT_SOURCES`. The gap is m4.
> - **Copy step:** matches 3a's `check_g1b_copy` / `check_seven_copy`.
>   - It adds `runs_jsonl_sha256`, and binds `assembly_sha256` to the gate record through `ASSEMBLY.json`.
>   - The gate copy sits beside the summary copy.
>   - Placement under `sealed_g1b` is checked, with no symlinks on the path.
> - **"Needed outside this unit" (§5):** the five items are complete and accurate (`outcome.value`, the T1 release rows and arms-frozen record, T1 δ_n, T1 features, suite names). Add:
>   - the 3a `note_lines` additions (M2);
>   - the close-server tool if M3 is not fixed here;
>   - freezing the G.5 files under `sweep2/` and the spec on main from launch until the T1 test release, because the re-derivation and the `spec_sha256` binding fail closed on any change;
>   - proposer-card hours, which no code reports under G5-TASL-GPUH A (§2.6, §5).
>
> ## Notes for the cluster agent
> - Write the joined, gated G.1b run directory under `sealed_g1b`, with no symlinks on the path, before `rel-copy`.
> - Sealed copies duplicate `out.tar`, so check free disk before `seal-attempt`. Until m2 is fixed, after a partial seal STOP and report; do not move or delete the half-written target.
> - The `out.tar` copies in the runs tree stay in clear after sealing; nobody opens them.
> - Close crashed attempts promptly.
> - If a TASL-7 serve process dies without `server_end.json`, STOP for the author (M3).
> - Under G5-TASL-GPUH A, `llama-server.log` is in clear on TASL-7 for the whole table span.
> - The `--server-record` copied to TASL-2 must be byte-identical to TASL-7's, because the spans are matched by sha256.
> - Run the release integrity check on TASL-2 from a clean, published checkout. `sweep2/{t1_tasl,g1b,g4}` and `s2_c2_lib.py` must equal origin/main, and the spec must be unchanged since launch.
> - Do not pass `--paper-root`, `--index` or `--classification` for `--source g5`.
>
> ## Process
> - Read-only on /tmp/pb/wt/g5b2; it is still clean, with no untracked files.
> - Scratch probes, temporary files and a sparse clone were made under /tmp/g5b2rev and moved to /tmp/g5b2rev/_to_delete/; nothing was deleted.
> - Tests were run one file at a time with TMPDIR=/tmp/g5b2rev/t, PYTHONDONTWRITEBYTECODE=1 and AR_HARNESS_ROOT=/tmp/pb/wt/t1h.
> - No secrets, sealed data, labels, evaluation values or 7001–7010 results were read; no server was contacted.
>
> VERDICT: NOT ACCEPTED (B1 branch-dependent integrity-check test fails once published; B2 read_evidence releases test labels under the train/dev row; M1–M4 to fix before re-review)

## Round 2 (`0f9e8773`)

> Reviewed base: 0f9e8773f735ca71123f0121e56cb76ef5b27ee7 (round 2: six commits on b7b6e9cfb64d2e3e15eb3c0d91d9ce5c89014b84; the unit as a whole on 926ad83b511d23b46241bfe6befdb44f9b687d03)
>
> ## Summary
> Round 2 is accepted. I checked each claim in the author's summary against the code; all of them hold, and both blocking and all four major findings from round 1 are fixed. Two of the fixes were also confirmed by running them: the reviewer probe from round 1 is now a test and passes, and the integrity-check tests now pass in a clone where origin/main equals HEAD (the state after merge).
>
> All targeted test files pass, each run on its own: test_t1_g5_seal 30, test_t1_g5_job 23, test_t1_g5_tasl 107, test_c3_release 41, test_c3_sweep1_release_compat 12, test_c3_sweep2_audit 28. Since the merge, release_checks.py has changed only in the G.5 block, so the sweep-1 and sweep-2 checks are still byte-for-byte as accepted in READY 86.
>
> ## Round-1 findings
> - **B1, fixed.**
>   - The git calls now go through `release_checks._g5_git`, and the tests create the "differs" and "dirty" cases on purpose.
>   - A positive test shows that a published checkout reaches `verify_evidence` (stubbed). It runs inside the integrity context with the stage from `test_released("T1")`, and only the `COMPLETION_KEEP` keys come out.
>   - In a sparse clone at 0f9e8773 with origin/main set to HEAD, all 30 seal tests pass.
> - **B2, fixed.** `read_evidence` now needs the test row for both blocks. The one exception is the release integrity check, where the label block needs only the train/dev row, as the §6 carve-out allows. The test and report §3 are corrected.
> - **M1, fixed.**
>   - `SealedTree` opens only three kinds: ledgers, a plan, or a chunk. Each kind takes only its own members, and an exact member set is required.
>   - Raw rows are not available through the public methods. `chunk_rows` passes rows through `reduce_rows`, so at train/dev no evaluation-seed kind or value leaves the reader. Those rows are still checked: each planned run must have a row, and an ok row must carry a finite value.
>   - The access log records the kind and the member names, and STOP 11 checks them. The member pattern is shown equal to `g5_job`'s.
> - **M2, fixed.**
>   - `TABLE_READINGS`, a three-way choice (`refuse`, `neg_inf`, `leave_out`) in the spec, and two new note lines, `t1_table_readings` and `server_log`, which the switch checks verbatim.
>   - `assemble --note` takes the Δ̂ choice only from the signed note. The note must be on main byte-identically, read `approved: true`, bind this spec's sha256, and carry the line verbatim.
>   - Without a note only `refuse` is allowed, and the command-line flag is gone.
>   - `verify_evidence` re-binds the readings to the note instead of replaying `build.json`. A forged `build.json` either fails the note check or fails the byte comparison.
>   - `leave_out` is built faithfully (not tabled, counted as an exclusion).
> - **M3, fixed.** `close-server` is guarded like close-attempt: same host, no process names the directory, the pid is gone, the lease is free, and a reason is required. It writes `server_end.json` with the log's sha256, the closing time as the end, and the log's latest mtime beside it. `seal-server` then works on it, and this is tested.
> - **M4, fixed.** close-attempt now meters to the closing time. `latest_mtime_utc` and `gpu_seconds_to_latest_mtime` are recorded beside it, and `test_m7` is updated.
> - **m1–m10, done.**
>   - Seals are written into a `.partial` directory and renamed after the receipt; a leftover `.partial` STOPs.
>   - Receipts now name their sealed path.
>   - Tar members are checked by sha256 before any source is removed.
>   - The publication check now covers `s2_c2_lib.py` and every file in `IMPORT_SOURCES`, plus the spec.
>   - A gap in the registered server numbers is counted as an open span and refuses audits under GPUH B.
>   - STOP 11 now covers TASL-7's access log.
>   - At train/dev, ok evaluation-seed rows must carry a finite value (checked, not kept).
>   - `derive` requires the sealed `_run`, that the live job access log equals its sealed copy, and that the sealed K lock equals K.
>   - The report wording is fixed.
>   - The autoresearch summary is bound to the completion record's `noise_floor_copy`.
>
> ## New minor points (non-blocking)
> - **n1 — `SealedTree._open` is private but still returns raw `rows.jsonl`.**
>   - Called directly as `_open(dir, "out.tar", "chunk", "assembly traindev: …")`, it bypasses `reduce_rows`, and the access log entry looks the same as a `chunk_rows` read.
>   - Suggested hardening: do the reduction inside `_open` for the chunk kind.
>   - Any such call is still a STOP 11 compliance matter.
> - **n2 — A crash between the rename and the cleanup leaves clear content with no automated path.**
>   - In `seal_attempt` (before `rmtree(out)`) and in `seal_server` (before the log is unlinked), the sealed copy exists, so a re-run STOPs with "exists" while `out/` or `llama-server.log` stays in clear.
>   - Fix later: a cleanup that runs when the target verifies against its receipt.
> - **n3 — `close_server` can be blocked by a reused pid after a TASL-7 reboot.**
>   - It uses `os.kill(pid, 0)`, so another process holding the old pid makes it STOP with "still alive", and there is no override.
>   - Fix later: also compare the process's start time or command line.
>
> ## Rulings on the author's flagged judgment calls
> - **The assembly checks only the note's publication, approval, spec sha256 and readings line, not the full `check_note`:** accepted. The switch runs `check_note` at every job start, and the byte-identical main copy plus the spec binding tie the readings to that note.
> - **A server numbered above the highest registered one, named by no campaign record, stays invisible under GPUH B:** accepted as a C9 limit. Operator procedure covers it (see the cluster notes).
> - **The assembly requires the whole run sealed:** accepted. `release.py` writes one train/dev release per source, once, and PRE-T1 A with the freeze wait makes that release cover the whole table. Staggered releases are not possible in any case.
> - **Proposer-card hours under GPUH A are not built:** accepted for this unit. They are a reported figure, not a STOP input, and §5 item 7 lists them as needed. They should exist before the T1 report.
>
> The report's "needed elsewhere" list is now complete: it adds the freeze on main from launch to the T1 test release, and the proposer-card hours. The open decisions in §6, including the three Δ̂ options and the T0 precedent for `leave_out`, are stated accurately.
>
> ## Notes for the cluster agent
> - After any `seal-server`, copy the receipt to TASL-2 and register it with `server-span` at once.
> - After a TASL-7 crash, run `close-server` and then `seal-server` before any audit.
> - Under GPUH B, never leave a started server unregistered.
> - If a seal STOPs on an existing `.partial`, report it and do not touch it.
> - If a re-seal STOPs with "exists" while `out/` or a server log is still in clear, STOP and report it (n2).
> - Run `assemble` at both stages with the same `--note`. Without a note only `refuse` applies.
> - Keep the G.5 files under `sweep2/` and the spec frozen on main from launch to the T1 test release.
>
> ## Process
> - Read-only on /tmp/pb/wt/g5b2, which is still clean.
> - Scratch this round (a sparse clone and pytest temporary files) was moved to /tmp/g5b2rev/_to_delete/round2/.
> - The round-1 scratch I had moved to /tmp/g5b2rev/_to_delete/ was gone when this round started. I did not delete it; something outside this review removed it.
> - Tests were run one file at a time with TMPDIR=/tmp/g5b2rev/t, PYTHONDONTWRITEBYTECODE=1 and AR_HARNESS_ROOT=/tmp/pb/wt/t1h.
> - No secrets, sealed data, labels, evaluation values or 7001–7010 results were read, and no server was contacted.
>
> VERDICT: ACCEPTED

## Round 3 (`166d692a`)

> Reviewed base: 166d692a2b35f25cf70c7f8d1d19421652a0d92f (one commit on 0f9e8773f735ca71123f0121e56cb76ef5b27ee7)
>
> ## Summary
> The n1 fix is correct and the report matches my round-2 review, so the acceptance stands. One wording point in §10 can be fixed at the author's convenience (below).
>
> - **n1, fixed.**
>   - `SealedTree._open` now returns `{chunk, rows, evaluation_rows_dropped}` for the chunk kind, after `reduce_rows`. Raw `rows.jsonl` cannot leave the reader any more, even through the private opener.
>   - The order is unchanged: lock check, path check, receipt check, access-log line, then the read. The stage comes from the purpose, which `require` has already validated.
>   - `chunk_rows` now just returns `_open`'s result.
>   - Ledgers and plans are unchanged.
>   - The M1 test now calls `_open(chunk, "out.tar", "chunk", "assembly traindev: private")` directly. It checks that no raw member comes back and that only label seeds do.
> - **Report §10:**
>   - It records n1 as fixed and n2 and n3 as open: for n2 the operator STOPs and reports; for n3 the author decides until a start-time check exists.
>   - It records my rulings on the four flagged judgments, and the round-2 cluster notes, accurately.
>   - One wording point: the cluster-notes list should also say "a re-seal that STOPs with 'exists' while `out/` or a server log is still in clear is a STOP to report". The n2 bullet says the operator STOPs and reports, but the list itself omits that case.
> - **Tests:** each file run on its own, all passing: test_t1_g5_seal 30, test_t1_g5_job 23, test_t1_g5_tasl 107, test_c3_release 41.
>
> ## Process
> - Read-only on /tmp/pb/wt/g5b2, which is still clean.
> - This round's scratch (pytest temporary files) was moved to /tmp/g5b2rev/_to_delete/round3/.
> - When I checked at the end, round 2's /tmp/g5b2rev/_to_delete/round2/ had also gone, as round 1's had before. I did not delete either; something outside this review removed them.
> - No secrets, sealed data, labels, evaluation values or 7001–7010 results were read, and no server was contacted.
>
> VERDICT: ACCEPTED

---

Code-Commit: 166d692a2b35f25cf70c7f8d1d19421652a0d92f
Verdict: ACCEPTED

Accepted at `0f9e8773`, confirmed at `166d692a`; every §11 decision stays `signed: false`.
