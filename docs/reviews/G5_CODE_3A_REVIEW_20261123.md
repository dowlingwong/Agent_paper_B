Reviewed base: `eed8bf30` (published `main` `1402f466` merged into the accepted G.5 draft revision 8 `d802195d`); accepted at `6cada94f`, confirmed at `9b3914e8805a2250dc2a7699c1b455da99c92aa6`

# Independent review record — the G.5 code unit, part 3a: the G.5 spec, validator and option switching, the note check, the switch and its pre-runner checks, and the TASL dates fix

**Unit.** On `mac-g5-code-20261123` over `eed8bf30` (main `1402f466` merged into `mac-g5-tasl-rev8-20261122` @ `d802195d`): `sweep2/t1_tasl/g5_tasl_spec.json` (eight nodes on two harness families, G5-7 on `c025f89a` and G5-AR on `2d09f9a9`, pins checked against both G.1b specs; instance seeds 5101–5112; audit seed blocks for K = 10 and K = 6; all eight §11 decisions as fields, option A, `signed: false`; the §5 values as proposed values; autoresearch's PENDING markers under G5-ARPEND A; the projection 305.3/386.0 and 208.5/259.9 GPU-h, 424.6 ≤ 425), `sweep2/t1_tasl/g5_tasl.py` (validator with `apply_options`; the note check: key lines verbatim, P1–P11 PASS, `audit_K` and the freeze-wait date read from the note; the switch, off by default with both keys: decisions and E4 rows (G5-MEM A), TASL-2 host checks, the REL-T1-G1B copies with the cross-check gate record, STOP 15 with exactly one reviewed completion record, STOP 14, STOP 13 via `g5_pin_check.py`, P5 measurement path with no additions in the measurement directories, the C12 record, then the launch binding; the runner itself is part 3b and refuses), `r1/tests/test_t1_g5_tasl.py` (107), the dates fix (`autoresearch_fixedtokens` out of `pilot_nodes` in `g4_tasl_dates_params.json`; `ratio_exempt_nodes` equal to the 4090-censused nodes in `g4_tasl.py`/`g4_lib.py`, H200 path unchanged), and the report `docs/r1/reports/g5_code_20261123/G5_CODE_3A_20261123.md`. Authority: the G.5 draft revision 8 §2, §4, §5, §7, §9, §11 and its reviews; R1-G5-DECISIONS, R1-G1B-TASL-DECISIONS, G4-NODE3, REL-T1-G1B, R1-G1B-JOIN; the coordinating chat's draft queue (unit 3), with §9 split into parts 3a and 3b.

**Process.** One independent reviewer, read-only, synthetic data and the real pins only (no secrets, sealed data, labels or evaluation values; no server access), scratch under `/tmp/g5rev/`. Round 1 found three majors where a prerequisite was checked only on paper (the C12 record never read from main; P3 compared with the G.5 spec's own fields rather than the G.4 spec; the seven-node noise floor accepted without the cross-check gate) and six minors. Round 2 accepted with three minors; one (P5/P8 citations without a review file) was fixed and confirmed, two are recorded as open items.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `612849f2` | NOT ACCEPTED (M1–M3; minors m1–m6) |
| 2 | `6cada94f` | ACCEPTED (minors m1–m3) |
| 3 | `9b3914e8` | ACCEPTED (confirmation) |

**Open items.** (1) All of §11 is unsigned: G5-W, G5-TEMP, G5-MEM, G5-AUDIT, G5-DIV, G5-TASL-GPUH, G5-SLOT, G5-ARPEND (A recommended for each); G5-MEM A needs the author's explicit signature and a PLAN row amending E4's "both memory modes" (the switch refuses without it); the values §11 items 9–16 fix. (2) The note the author signs carries five key lines beyond draft §5 (`invalid_share_stop`, `infrastructure_stop`, `seal`, `decisions`, `e4_amendment_row`), the restored floor-by-node wording and the freeze-wait line "no G.5 job starts on or after this date". (3) Draft revision 8 is stale against main in §1, §2.11, §2.13, P1, P2, P9 (autoresearch's host check PASS and third note signed; R1-G1B-JOIN and the launch chain published; the G.4 note re-issued as `g4_t1_tasl_20261123.md`): a text-only revision before the signature. (4) The C12 record format is provisional (`c12_host`/`c12_verdict`, or a `c12_review` on main); fix it with the C12 procedure. (5) Under G5-ARPEND B the switch does not check the third G.1b note (optional hardening in part 3b). (6) Part 3b: the job (two waves with audits between them, the proposer check per wave), the audit runner, `diagnostics.json`/`job_record.json` and the STOP counters, K uniformity after the first audit chunk, the seal with its access log, assembly and release locks, the REL-T1-G1B copy step (which must copy `crosscheck_gate.json`). (7) Cluster: each family checkout on TASL-2 must contain both G.5 commits (C13); the G.5 harness commits may add only `trackg/audit_g5.py` and `trackg/diagnostics_g5.py`; G.4 launches from its own commit (this unit changes `g4_tasl.py`/`g4_lib.py`); P7's eight-node number comes from this unit's `dates`; a moved freeze-wait date needs an author row naming it in ISO form.

## Round 1 (`612849f2`)

> Reviewed base: eed8bf3003a5115365c99b80c76c6b4604fa3888 (the diff eed8bf30..612849f251669b871690f594d67ba3866e7bc7e2, four commits 50c6639c, 13bd8ff5, eb7bbe06, 612849f2)
>
> # Independent review: G.5 code unit, part 3a (spec, validator, note check, switch, dates fix)
>
> ## Summary
>
> The unit is close to shippable. It is well built, and the defaults are faithful to the draft. Three enforcement gaps keep it from acceptance. In each, a draft prerequisite is checked only on paper:
> - the C12 record is never read from main;
> - P3 is checked against a field the spec declares about itself, not against the G.4 spec;
> - the seven-node noise-floor copy is accepted without the cross-check gate that the draft's `noise_floor` line names.
>
> All three are small code fixes. No blocking findings.
>
> **What I checked and ran:**
> - **Tests.** `test_t1_g5_tasl.py`: 85 passed, including the real-pins case (AR_HARNESS_ROOT=/tmp/pb/wt/t1h). Also passed: `test_t1_tasl_g4.py` (30), `htcondor/test_g4_h200.py` (67), `test_t1_tasl_g5_ar_projection.py` (6) and `test_t1_tasl_g5_pin_check.py` (7).
> - **Projection.** `g5_tasl.py validate` on the shipped spec reproduces the draft: 305.3 / 386.0 GPU-h at K = 10, 208.5 / 259.9 at K = 6, and 424.6 ≤ 425. The non-default rows also match the draft: W B 489.5, MEM B 610.7, parents re-run 349.5 / 445.5, both cards counted 360.4 / 448.3. `g5_ar_projection_tasl.py` and `g5_projection_tasl.py` still run unchanged.
> - **P5 on the real pins.** `c025f89a` and `2d09f9a9` each pass against themselves (308 paths). `c025f89a` against `2d09f9a9` STOPs on autoresearch's node and config files and `node_lib/ar_isolated.py`. No engine file is in the closure. The closure leaves trackg only to reach `autoresearch/__init__`, `control_plane/permissions` and `nodes/spec`, and imports only `yaml` outside autoresearch.
> - **Real records on main.** `check_host_record` passes on both TASL-2 binding records: `681011b2…` at `c025f89a` and `cce9b8fb…` at `2d09f9a9`. The third G.1b note on main has `approved: true`, run `g1b-ar-tasl-20261122-a`, `harness_commit` `2d09f9a9`, and `spec_sha256` `65da95db…`, which equals what the G.5 spec binds. So STOP 15's note check would pass on the real note.
> - **Spec values.** Every §5 value in the spec matches the draft: UUIDs, drivers, server URL, llama-server and GGUF sha256s, manifests, environment freezes, gate, preregistration, split and seeds. The G.1b specs on the branch are byte-identical to main.
>
> **Points 1–7 of the brief:**
> - **Defaults and options (1).**
>   - All eight §11 decisions are A, `signed: false`, and switchable. `apply_options` sets exactly the fields each option governs, and the validator STOPs on any mismatch. No default changes declared content.
>   - G5-MEM A requires the E4 row: it is a PLAN row id at launch, the row must be on main naming "E4" and "G5-MEM", and the decisions row must name "G5-MEM A".
>   - The author's readings are sound:
>     - **MEM C refused:** the frozen split has no instance-to-mode rule, and C contradicts V3-B.
>     - **Band doubled only under MEM B:** this follows draft STOP 9 and §11 item 10, not the coordinator's "B/C" wording. It is moot anyway, since C is refused.
>     - **DIV B as the upper limit of a two-sided 95 % Clopper–Pearson interval, and 40 audits applied to B and C:** both are defensible, but the note line should say "two-sided" (m6).
>     - **Projection refusal at share 0.6:** acceptable as a floor, since P7 binds (m6).
> - **Spec (2).** Correct as listed above.
> - **Note check (3).**
>   - Key lines are matched verbatim, and P1–P11 must read PASS.
>   - `audit_K` is read from the note. K = 6 needs a single PLAN row on main naming "K-check" and "PASS", and the seed lines must agree with K.
>   - **The extra lines.** Only five are truly new: `invalid_share_stop`, `infrastructure_stop`, `seal`, `decisions` and `e4_amendment_row`. `cuda_ipc_acceptance` is already in the draft, as the verbatim line under §5. The five carry values that §11 makes the signature fix, so they strengthen the note and need no draft amendment. They should still appear in the version the author signs.
>   - **The seed line without angle brackets** is defensible but reads ambiguously (m6).
>   - **One real content loss:** the `noise_floor` line drops "g1b_tasl_join.py floor-by-node" (M3).
> - **Switch (4).**
>   - Off by default; both keys needed. Every check runs before any runner, and the default runner refuses.
>   - The launch binding is last, after the import-source check. The files that `validate_spec` reads from the working tree (split file, G.1b and G.4 specs) are covered by that binding.
>   - STOP 13, STOP 5 per node, REL-T1-G1B by sha256 and review, and STOP 15's exactly-one rule all work.
>   - STOP 14: see m3.
> - **Dates fix (5).**
>   - Correct: autoresearch is out of `pilot_nodes`, and an autoresearch "pilot" summary is now refused.
>   - `g4_tasl.recompute_dates` requires `ratio_exempt_nodes` to equal the nodes censused on the 4090, read from the G.1b specs (`{autoresearch_fixedtokens}`).
>   - The H200 path is unchanged by default (empty list). Its only change is one added, empty output key.
>   - The tests are meaningful: a ratio of 2.0 doubles the Ada nodes, autoresearch stays at 218.951 s, and a bad or missing list is refused.
>
> ## Findings
>
> **No blocking findings.**
>
> **M1. A C12 record is never checked on main (P1).**
> - **Where:** `g5_tasl.py` `validate_spec` (lines 596–602), `note_lines` `cuda_ipc`, and `launch`.
> - **Problem:** under `cuda_ipc.mode = "c12"`, the code only checks that the record path looks like a path under `docs/r1/reports/` and that the sha256 is 64 hex digits. Nothing reads the record from main, checks its sha256, or checks that it reads PASS. The TASL-2 host records, by contrast, go through `check_host_record`. The draft recommends C12 over the acceptance line.
> - **Failure scenario:** I confirmed this with a probe. A spec whose C12 record does not exist on main, with an arbitrary sha256, launches through the whole switch. The note's line "C12 PASS: … sha256 …" matches verbatim, because it is rendered from the same spec fields. Labels marked EVIDENCE would then run without the CUDA-IPC test or the signed acceptance.
> - **Fix:** in `launch` (or `check_note`), under c12:
>   - read the record with `read_main`, compare its sha256, and require host TASL-2, item 7 PASS and a PASS verdict (or a review on main with `Verdict: ACCEPTED`, if the C12 format is not fixed yet);
>   - add a test.
>
> **M2. The P3 pilot-basis blocker can pass vacuously.**
> - **Where:** `validate_spec` lines 450–460, the spec's `pilot_basis`, and the test `test_g5_temp_b_needs_a_pilot_at_zero`.
> - **Problem:** the blocker compares `pilot_basis.W_semantics / W / memory_modes / temperature` with the chosen options. Those four values are declared in the G.5 spec itself and are never compared with the G.4 spec they claim to describe. The validator loads `g4_tasl_spec.json`, but checks only its `run_id` and nodes. That spec's `pilot` block holds `budget` 20, `temperature` 0.2 and `memory_mode` history.
> - **Failure scenario:** probe confirmed. The author signs G5-TEMP B, and someone edits `pilot_basis.temperature` to 0.0. The blocker disappears, although the same G.4 run, `g4-tasl-20261121-a`, was specified at 0.2. The unit's own test clears the blocker exactly this way ("a re-run pilot at 0"). The same applies to MEM B (`memory_modes`) and W B (`W_semantics`).
> - **Fix:**
>   - derive the four values from `g4["pilot"]` (`budget`, `temperature`, `memory_mode`; W is manager calls for the v2-diff pilot), or require equality with it;
>   - change the test so that only a re-issued G.4 spec clears the blocker.
>
> **M3. The seven-node noise floor is accepted without the cross-check gate.**
> - **Where:** `check_g1b_copy`, `launch` line 1182, and the `noise_floor` line in `note_lines` (line 736). Compare draft §5 `noise_floor` ("joined by node (g1b_tasl_join.py floor-by-node; …)"), and R1-G1B-JOIN ("behind the unchanged cross-check gate").
> - **Problem:**
>   - `g1b_tasl_join.noise_floor_by_node` refuses a seven-node summary unless `crosscheck_gate.json` sits beside it, with that schema and `assembly_json_sha256 == summary.assembly_sha256`. This is R1-T1-TASL-ENV's gate for the TASL-7 nodes.
>   - The switch never runs that check. It accepts any reviewed JSON of schema `g1b_tasl_summary/1` for the run that covers the seven nodes.
>   - The rendered note line also drops the reference to floor-by-node, so the signed text no longer names this safeguard.
> - **Failure scenario:** probe confirmed. A summary assembled outside `assemble_join`, or from an assembly whose cross-check did not pass, is copied out and reviewed. G.5 labels then use σ̂ from TASL-7 nodes that never passed the cross-host gate. Only a reviewer's attention stands in the way.
> - **Fix:**
>   - require the REL-T1-G1B copy to include the gate record: copy `crosscheck_gate.json` beside the summary, name its path and sha256 in the spec and the review, and check its schema and `assembly_json_sha256` against the summary's `assembly_sha256`;
>   - or call `J.noise_floor_by_node` on the two copies;
>   - restore "g1b_tasl_join.py floor-by-node" in the line.
> - **Note:** the copy step itself is not built here, so this also fixes what that step must copy.
>
> **Minor**
>
> **m1. STOP 15 has three checks that pass on the record's word alone.**
> - **Where:** `check_ar_record`.
> - **Problem and failure:**
>   - **(a)** `g1b_sealed_summary`'s sha256 is only compared with `noise_floor_copy`'s sha256, both written in the same record. "Byte-identical to the sealed summary" is self-asserted (probe confirmed: a nonexistent path passes).
>   - **(b)** `tails_declaration` is only checked to be on main at its sha256. Its content is never compared with the record's `tails`, and nothing requires that it is about autoresearch.
>   - **(c)** The third note's `spec_sha256` is not compared with the G.5 spec's G5-AR `g1b_spec.sha256` (`65da95db…`). If the autoresearch G.1b spec were re-issued, the G.5 node fields copied from it (manifest, run times, timeout basis) could silently diverge from the spec that produced the noise floor.
> - **Fix:**
>   - require the copy's review to name the sealed path and sha256;
>   - require the declaration to name `autoresearch_fixedtokens` and the same tails value;
>   - check `nf["spec_sha256"]` against the G.5 spec's G5-AR `g1b_spec.sha256`.
> - **Also tidy:** the `provided` identity map (line 929) is dead complexity. `ar_prerequisites.pending` lists three items, while the spec carries four PENDING markers (the G5-AR host check too). The record checks all four in substance, so align the list with the markers.
>
> **m2. "Exactly one record" ignores near-miss names.**
> - **Where:** `RECORD_NAME`, `check_ar_record`.
> - **Failure:** probe confirmed. A corrected record committed as `…/G5_AR_PREREQUISITES_20261206_v2.md`, or two directories deep, is not counted, so the old record is still used without any STOP.
> - **Fix:** collect every path on main containing `G5_AR_PREREQUISITES`, and STOP if any of them does not fit the strict pattern, or if their number is not one.
>
> **m3. STOP 14 at job start is a new consequence, and the deadline cannot be moved without a new spec.**
> - **Where:** `freeze_wait_check` and the `freeze_wait` note line.
> - **Problem:** no job may start on or after 18 Dec (report item 9). That is a reasonable reading, but the draft's STOP 14 stops only "before the arms-frozen record", and the note line does not say that jobs stop. The deadline lives in the spec, whose sha256 the note binds.
> - **Failure:** the author answers STOP 14 by waiting for a late node. Its remaining jobs cannot start until the spec, the note and the launch commit are re-issued, which draft §2.13 sets out to avoid.
> - **Fix:** add "no G.5 job starts on or after this date" to the `freeze_wait` line, so that the author signs it. Optionally read the date from the note, as `audit_K` is, so that a docs-only amendment citing an author row can move it.
> - **Also:** in `before_arms_frozen` mode `today` is ignored, so "not yet" and "deadline passed" give the same message. This matters for the release step later.
>
> **m4. P5 allows G.5 to add files inside the measurement directories.**
> - **Where:** `measurement_path_check`.
> - **Problem:** only paths present at the pin are compared. The code follows the draft's literal "files present at the G.1b pin", but the report's claim that "the directory list covers" dynamic loads holds only for existing files.
> - **Failure:** probe confirmed. A G.5 commit adds `nodes/cifar/json.py`, which would shadow a module for the node's own scripts, or a file under `configs/trackg/` or `node_lib/`. The check passes, and so does `g5_pin_check`, as long as both families carry the file.
> - **Fix:** STOP on any path added under `nodes/`, `third_party/`, `configs/trackg/` or `trackg/node_lib/`. In `trackg/`, allow additions only from a declared list such as `audit_g5.py` and `diagnostics_g5.py`.
>
> **m5. Tests do not cover two paths.**
> - **Problem:**
>   - the switch's G5-ARPEND B branch (`launch` lines 1193–1201: the autoresearch host check and copy from the spec) has no launch test;
>   - `plan_row` with a duplicated row is not tested.
> - **Fix:** add a ready-world launch test under ARPEND B, and a duplicate-row case.
>
> **m6. Wording and nits.**
> - **(a) The seed rule.** `sha256("manager_seed:step")[:8]` reads as hashing a constant string. Prefer `sha256(f"{manager_seed}:{step}")[:8]`, both in the note line and in the spec's `per_call_seed_rule`.
> - **(b) Report item 4's reason is inaccurate.** G.5's `check_note` exempts a value equal to its rendered line from the placeholder rule, so angle brackets would have passed. The real reason is the draft's "every `<…>` field of §5 filled" rule at signature.
> - **(c) The DIV B line** should say "two-sided 95 % (upper tail 2.5 %)".
> - **(d) The cap floor.** The validator's floor is share 0.6. For non-default rows the draft sizes the cap at share 0.8 plus 10 %; the report should say that P7 and the signature carry this.
> - **(e) Two smaller gaps.** A G5-7 `harness_dir` is compared only with its own family's G.1b checkout, not with autoresearch's G.1b checkout or G.4's. The P5 and P8 citations are not checked to be reviews on main with `Verdict: ACCEPTED`.
>
> ## The report's "draft vs main" list (items 1–11)
>
> - **Items 1, 2, 3 and 11 are true on main:**
>   - the autoresearch-pin binding record `cce9b8fb…` reads PASS at `2d09f9a9`, and the third note is signed;
>   - R1-G1B-JOIN and the TASL launch chain (`tasl_chain_20261122/*`) are on main;
>   - the G.4 note was re-issued as `g4_t1_tasl_20261123.md`, with `paper_commit` `b5824240` and spec `fd9c6e9d…`;
>   - `PC.check` needs both G.5 commits in one repository.
> - **None blocks the code.** Items 1–3 make §1, §2.11, §2.13, P1, P2 and P9 of the draft factually stale. A text-only revision should fix them before the author signs, so that the signed note is accurate. G5-ARPEND A remains the right mechanism: autoresearch's G.1b run, its copy and P10 are still pending.
> - **Items 4–10** are defensible judgments, subject to m6(a)–(c) and m3. Item 5 needs no draft amendment, but the version the author signs should show the five new lines. Item 8 (host checks at the G.1b pins) is consistent with P1 and with P5's byte-identity of the isolation code.
>
> ## Notes for the cluster agent
>
> - **Both commits in each checkout.** Each family checkout on TASL-2 (`harness_g5`, `harness_g5_ar`) must contain both G.5 commits, or STOP 13 fires (report item 11). Include this in C13.
> - **G.4 launches from its own commit.** This unit changes `g4_tasl.py` and `g4_lib.py`. G.4 has not run yet (the 20261123 note says so), and it must launch from its own published commit or a docs-only descendant, as its note says. A checkout moved to a main that contains this unit fails the binding, which is fail-closed.
> - **P7 uses the new code.** The eight-node P7 number must come from `g5_tasl.py dates` in this unit's code, which exempts autoresearch from the ratio. G.4's own checkout still has the old ratio code.
> - **K uniformity is not enforced yet.** The switch reads `audit_K` at every job start. "No K change after the first audit chunk" needs job state and is part 3b; do not amend K once any audit chunk has run.
> - **Record format.** The completion record is parsed as `key: value` lines, so any prose line shaped like `Word: …` becomes a field. A duplicate key STOPs, and so does a prose line with `<…>`. Write records with that in mind.
>
> ## Process
>
> - Read-only throughout. /tmp/pb/wt/g5code stayed clean at 612849f2, and /tmp/pb/wt/t1h at c025f89a. /tmp/pb/repo was not touched.
> - **One side effect:** my test runs refreshed or added ignored `.pyc` files inside the existing `__pycache__/` directories of the worktree (`r1/tests/`, `sweep2/t1_tasl/`, and possibly others). The directories already existed from the author's runs, and `verify_launch_tasl` excludes `__pycache__`.
> - My scratch is in /tmp/g5rev/_to_delete/ (probes, scripts, tmp). Nothing was deleted. The other files in /tmp/g5rev are not mine and were left alone.
> - No secrets, sealed data, labels, evaluation values or seed 7001–7010 results were read. No server access.
> - **For memory:** nothing new about the user.
>
> VERDICT: NOT ACCEPTED (M1 C12 record not checked on main; M2 P3 pilot basis checked only against the spec's own fields; M3 seven-node copy accepted without the cross-check gate / floor-by-node)

## Round 2 (`6cada94f`)

> Reviewed base: 6cada94f16194ca37d4a7ce5b9ea8943beadfa5b (round 2: the diff 612849f2..6cada94f, i.e. aeb39bf3 and 6cada94f; round 1 reviewed eed8bf30..612849f251669b871690f594d67ba3866e7bc7e2)
>
> # Independent review, round 2: G.5 code unit part 3a
>
> ## Summary
>
> All three round-1 majors are fixed. So are m1–m6, and the fixes hold up. I checked them against the code, the real files on the branch and main, and my own probes. Two minor gaps and one asymmetry remain. None blocks shipping.
>
> **Tests (one file at a time, AR_HARNESS_ROOT=/tmp/pb/wt/t1h, no bytecode written this round):**
> - `test_t1_g5_tasl.py`: 106 passed, the real-pins case included.
> - `test_t1_tasl_g4.py`: 30 passed.
> - `test_t1_tasl_g5_pin_check.py`: 7 passed.
> - `test_t1_tasl_g5_ar_projection.py`: 6 passed.
> - `htcondor/test_g4_h200.py`: 67 passed.
> - I did not re-run the crosscheck and chain test files. This round does not change those modules, only imports them.
>
> **Round-1 findings, verified:**
> - **M1 (C12 record) is fixed.**
>   - Under `cuda_ipc: c12`, `check_c12` runs in the switch. It reads the record from main and compares its sha256.
>   - It accepts the record either through `c12_host` and `c12_verdict` lines, which must read TASL-2 and PASS, or through a `c12_review` on main that names the record and its sha256 and reads `Verdict: ACCEPTED`.
>   - Tests cover a missing record, a wrong sha256, FAIL, another host, a record with neither form, and a review that is not accepted.
> - **M2 (P3 pilot basis) is fixed.**
>   - `pilot_basis` may hold only the run id, the note, the nodes and an explanatory `settings` string. Any other key is refused.
>   - What the pilot ran is read from `g4_tasl_spec.json`'s `pilot` block by `pilot_settings`: budget 20, `history`, 0.2, manager calls by default. This matches the real G.4 spec.
>   - The TEMP B test now clears the blocker only with a re-issued G.4 spec, and declaring 0.0 in the G.5 spec is refused.
>   - A G.4 spec with a list of memory modes would keep the blocker, which is fail-closed.
> - **M3 (cross-check gate) is fixed.** `check_seven_copy` does the following:
>   - binds `g1b_crosscheck_spec.json` (sha256 `a9e6b463…`) and requires that its `g1b_spec.sha256` is `7ff3c95b…`. This is true on the branch: run `-xc2`, three TASL-7 nodes;
>   - requires `crosscheck_gate.json` on main, beside the copy, at its sha256;
>   - checks the gate's schema `g1b_tasl_crosscheck_gate/1`, its nodes against the cross-check spec, the G.1b spec sha256, the run id, and `assembly_json_sha256` against the summary's `assembly_sha256`. These are stricter than `noise_floor_by_node`'s own checks, and consistent with `g1b_crosscheck.py` line 506;
>   - requires the review to name the copy, the gate record, their sha256s and the sealed path.
>   Autoresearch jobs also run `J.noise_floor_by_node` on temporary byte-identical copies. The note line again names "g1b_tasl_join.py floor-by-node" and the gate record.
> - **m1 is fixed.**
>   - (a) The REL-T1-G1B reviews must name the sealed path.
>   - (b) Every line of the tails declaration that names autoresearch must carry the record's tails value and not the other.
>   - (c) The third note's `spec_sha256` must equal G5-AR's bound `g1b_spec.sha256`, which the real note does: `65da95db…`.
>   - The `provided` map is gone, and `pending` now lists all four markers, `host_check` included.
> - **m2 is fixed.** Any path on main containing `G5_AR_PREREQUISITES`, outside `docs/r1/reviews/`, must fit the strict pattern. Tests cover a `_v2` name, a deeper directory and a path outside `reports/`.
> - **m3 is fixed.**
>   - The freeze-wait date is read from the note. A different date needs "(moved by author row R1-…)", and that row must be on main naming the date. The note line says "no G.5 job starts on or after this date".
>   - `before_arms_frozen` now separates WAIT (deadline not yet reached) from STOP 14, and does not count stopped nodes as late.
>   - The spec stays unchanged when the date moves.
> - **m4 is fixed.** Additions under `nodes/`, `third_party/`, `configs/trackg/` and `trackg/node_lib/` STOP. In `trackg/` only `audit_g5.py` and `diagnostics_g5.py` may be added, and the closure check still applies to them.
> - **m5 is fixed.** There is now a launch test under ARPEND B (the decisions row must sign B, floor-by-node runs, and a replaced host record STOPs), plus duplicate and malformed `plan_row` tests.
> - **m6 is fixed.**
>   - (a) The seed rule reads `sha256(f"{manager_seed}:{step}")[:8]`.
>   - (b) The rationale for report item 4 is corrected.
>   - (c) The DIV B line says two-sided, upper tail 2.5 %.
>   - (d) The report states that the cap check is only a floor.
>   - (e) A family checkout may not be any G.1b checkout (either spec, any host) or G.4's. The reviews P5 and P8 cite must be on main and read `Verdict: ACCEPTED`, but see m1 below.
>
> **The author's judgment calls:**
> - **Provisional C12 format:** acceptable while no C12 procedure exists. It should be tightened when the procedure is written (m2 below).
> - **A moved-date row has to name the date in ISO form:** acceptable and fail-closed. An author row that writes "22 Dec" instead fails until it is restated in ISO form. The cluster agent should know this.
> - **floor-by-node only in autoresearch jobs:** correct. Under ARPEND A autoresearch's copy may not exist yet when seven-node jobs run. The seven-node jobs get the stricter gate check, and `check_g1b_copy` already enforces the exact seven nodes.
> - **m2 scan excluding `docs/r1/reviews/`:** right, since reviews naturally carry the name. A file elsewhere whose name contains the token (for example a template under `proposals/`) would STOP every autoresearch job. That is fail-closed and acceptable.
> - **ARPEND B pin mismatch covered only by `check_host_record`:** acceptable, with the asymmetry noted in m3 below.
>
> ## Findings
>
> **No blocking or major findings.**
>
> **m1. The check of the reviews P5 and P8 cite can pass without checking anything.**
> - **Where:** `check_note`, the loop over `T4.REVIEW_PATH.findall(fields[key])`.
> - **Problem:** `P_CITES` only requires the substring `docs/r1/reviews/`. If the cited text has no path matching `docs/r1/reviews/….md`, `findall` returns nothing and no review is checked.
> - **Failure:** my probe passes with `P5: PASS — docs/r1/reviews/ (G.5 code review, round 2)` and no review file on main.
> - **Fix:** require at least one `REVIEW_PATH` match in P5 and in P8.
>
> **m2. The provisional C12 record need not name item 7 or the harness pin.**
> - **Where:** `check_c12`.
> - **Problem:** the two lines `c12_host: TASL-2` and `c12_verdict: PASS`, with no review, are enough (probe confirmed). This is the same level of trust as `check_host_record`, but nothing ties the record to host-check item 7 or to a harness commit.
> - **Fix, when the C12 procedure is written:** fix its format, for example `c12_item: 7 PASS` plus `c12_harness_commit`, and check both. Until then, prefer the `c12_review` route.
>
> **m3. Under G5-ARPEND B the switch does not check the third G.1b note.**
> - **Where:** the ARPEND B branch of `launch`.
> - **Problem:** under A, the completion record ties autoresearch's floor to the signed third note: `approved: true`, run, pin `2d09f9a9`, spec `65da95db…`. Under B, only the copy's run id, its review and the host record at the pin are checked.
> - **Mitigation:** under B the signature waits for all of autoresearch's prerequisites, so the author sees them.
> - **Optional fix:** have the spec carry `g1b_note` under B and run the same note check.
>
> ## Notes for the cluster agent
>
> - Round 1's notes are now in report §7, and they are accurate.
> - **The no-additions rule constrains the G.5 harness commits.** G.5 may add only `trackg/audit_g5.py` and `trackg/diagnostics_g5.py` in `trackg/`, and nothing under `configs/trackg/`, `nodes/`, `third_party/` or `node_lib/`. Any other placement STOPs P5 until this unit's lists are changed and re-reviewed.
> - **The REL-T1-G1B step must copy `crosscheck_gate.json` beside the seven-node summary,** with its sha256 recorded, and its review must name both copies, their sha256s and the sealed path.
> - **A moved freeze-wait date** needs an author row that names the new date in ISO form.
>
> ## Process
>
> - Read-only throughout. /tmp/pb/wt/g5code is clean at 6cada94f, and /tmp/pb/wt/t1h at c025f89a. Tests ran with `PYTHONDONTWRITEBYTECODE=1`.
> - No secrets, sealed data, labels, evaluation values or seed 7001–7010 results were read. No server access.
> - This round's scratch is in /tmp/g5rev/_to_delete/r2. Round 1's `_to_delete` contents had already been removed by someone else when I started.
>
> VERDICT: ACCEPTED

## Round 3 (`9b3914e8`)

> Reviewed base: 9b3914e8805a2250dc2a7699c1b455da99c92aa6 (confirmation round: the diff 6cada94f..9b3914e8, one commit. Earlier rounds: eed8bf30..612849f2 in round 1 and 612849f2..6cada94f in round 2)
>
> # Confirmation review: G.5 code unit part 3a
>
> ## Summary
>
> The commit fixes round-2 m1 correctly. It changes nothing else in the code.
>
> **m1 (P5 and P8 citations) is fixed.**
> - **The fix:** `check_note` now collects the `REVIEW_PATH` matches for P5 and P8 first. If there are none, it STOPs with "must cite a review file docs/r1/reviews/<name>.md". It then checks each cited review for `Verdict: ACCEPTED`, as before.
> - **The test:** `test_cited_reviews_must_name_a_review_file` uses my probe text, "PASS — docs/r1/reviews/ (G.5 code review, round 2)". It checks P5 and P8 separately and expects the new STOP for each.
> - **Run:** `test_t1_g5_tasl.py` gives 107 passed (AR_HARNESS_ROOT=/tmp/pb/wt/t1h, no bytecode written).
>
> **m2 and m3 are now recorded as open items in the report.**
> - Report §8 lists the provisional C12 format and the missing third-note check under ARPEND B, with the same fixes I suggested.
> - Report §7 now holds my round-2 cluster notes:
>   - no additions in the measurement directories;
>   - the gate copy in the REL-T1-G1B step;
>   - the ISO date in a row that moves the freeze-wait date.
> - Both items are accurately stated, and leaving them open is acceptable, as I said in round 2.
>
> ## Findings
>
> No blocking, major or minor findings.
>
> ## Process
>
> - Read-only throughout. /tmp/pb/wt/g5code is clean at 9b3914e8, and /tmp/pb/wt/t1h is clean at c025f89a.
> - No secrets, sealed data, labels, evaluation values or seed 7001–7010 results were read. No server access.
> - Scratch was moved to /tmp/g5rev/_to_delete/r3.
>
> VERDICT: ACCEPTED

---

Code-Commit: 9b3914e8805a2250dc2a7699c1b455da99c92aa6
Verdict: ACCEPTED

Accepted at `6cada94f`, confirmed at `9b3914e8`; every §11 decision stays `signed: false`.
