# Independent review — G.4b re-pilot result memo on the TASL pair under R1-G5-DIFF-RECOUNT (`g4b-tasl-20261124-a`), 25 November 2026

- Date: 2026-11-25 (Europe/Berlin). Reviewer: fresh independent reviewer, delegated read-only. No run, retry, edit,
  push, delete, signal or HTCondor action was taken on either host; nothing was started, stopped or copied on the
  hosts. TASL-2 and TASL-7 were inspected read-only over SSH (`ls`, `stat`, `cat`, `sha256sum`, `sha256sum -c`,
  `git rev-parse`/`git status --no-optional-locks`/`git show`/`git grep`/`git ls-tree`, `nvidia-smi`, `ss`, `ps`);
  local work was limited to hashing and to reading already-captured bytes (fetched to a local temp dir and analysed
  there). Only this review file was written. TASL-2/TASL-7 records were read only; `harness_g4b`, `harness_g4rc` and
  every run/seal/record directory were left as found.
- Unit reviewed: result memo
  [`G4B_TASL_PILOT_RESULT_20261125.md`](../reports/tasl_chain_20261122/G4B_TASL_PILOT_RESULT_20261125.md)
  (sha256 `af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`, untracked on `ops-tasl-20261116` at
  `9253192f`) and its captures directory
  `G4B_TASL_PILOT_RESULT_20261125_captures/` (`MANIFEST.sha256` sha256
  `316d68f09c93f540017a8a37cb0c0a609df94428be94b53e063c858eff1eccef`; 52 entries, `sha256sum -c` all OK, covering
  every capture file except the manifest itself; 552 KiB, no `out.tar`).
- Bindings checked against: launch commit `0fc96f28ef99e4819f1dce9e15332afe82ee3520` (parent `90d4dcee`; ancestor of
  published `main` `912a7e0277d7b816bc111cf90ea10f267f94d3d9`), harness `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98`
  (branch `mac-trackg-g5-7-20261124`, `g1b_pin` `c025f89aeafc2199bf3487b4bcaa16678273c702`), spec
  `sweep2/t1_tasl/g4b_tasl_spec.json` sha256
  `56f8c293ddd3fa3bbf64b55c36f1139231c0a44631d2b5179b3e5471dcb86a1b`, signed note
  `docs/r1/authorizations/g4_t1_tasl_20261125.md` sha256
  `df600e3f7e66ea6ea413c549812ccea11a909bb06cb82527a08f5b679d541db2` (both taken from `origin/main` `912a7e02`).

**Verdict: ACCEPTED.** No BLOCKING and no MAJOR finding. All substantive claims of the memo and every expected smoke
value reproduce from the captured bytes and from the host state; the dates change is captured and correctly handled
as *reported, not applied* per R1-BX-D14 (iii). Seven MINOR findings are listed in §8 (prose and capture-summary
precision); none changes a number, a STOP conclusion, or the verdict. Conditions before the author applies the dates
are in §9.

## 1. Bindings, checkouts, smoke and gate checks — PASS

Every value the memo binds was re-checked from the hosts, not from the memo:

| item | verified value (host) |
|---|---|
| `paper_g4b` HEAD, both hosts | `0fc96f28` detached; only the copied note untracked (`df600e3f…`); tracked clean |
| `paper_g4b` origin/main, both hosts | `912a7e02` |
| spec on the host | `56f8c293…` (identical to `912a7e02:sweep2/t1_tasl/g4b_tasl_spec.json`) |
| `harness_g4b` (TASL-2) | HEAD `cbf7a003`; `c025f89a` an ancestor; only the two run-time data symlinks untracked (`nodes/mlab_cifar10/data`, `third_party/mlgym/nodes/mlgym_fmnist/data`, both pointing at the data root, the same links G.4's worker creates) |
| `harness_g4rc` (TASL-2) | HEAD `cbf7a003`, `status --porcelain` empty |
| old checkouts | TASL-2 `harness` `c025f89a`, `harness_g5` `52e3c0b0` (clean), `harness_g5_7` `52e3c0b0`, `paper_g4` `6ad899e0` (only its pre-existing untracked G.4 note); TASL-7 `harness` `c025f89a`, `paper_g4` `6ad899e0`. `paper_g4`'s `FETCH_HEAD` mtime is 2026-11-22 on both hosts (the reclass fetch went into `paper_g4b`, as the memo says); `paper_g4b`'s is 2026-11-25 |
| launch commit content | changes exactly `docs/r1/proposals/G4B_T1_TASL_NOTE_DRAFT_20261124.md` and the spec; parent `90d4dcee`; on `main` `912a7e02`; carries an SSH `gpgsig` header (not cryptographically verified here — no allowed-signers file — and not material to this result review) |
| G.4b TASL-2 host record | `681011b2114f6ff7db679d3265535d1cc2e8a9bdbc231371230f4de42d7b6b6d` at `origin/main`, as cited by P1 and compared with `g1b_pin` |

Harness rule (independent re-derivation of the three parts from `harness_g4b`): `git diff c025f89a cbf7a003` is 10
files (4 docs, `scripts/trackg_g4_reclassify.py`, `src/autoresearch/trackg/audit_g5.py`, 3 test files, and
`src/autoresearch/trackg/campaign_v2_diff.py`); `pilot_g4.py`, `manager_v2_diff.py` and `proposal_v2_diff.py` have the
pin's tree entries (identical blob ids); `campaign_v2_diff.py` differs and carries
`DIFF_RECOUNT_RULE = "trackg_diff_recount/v1"`. This is exactly the note's P6 and the memo's §2.

Smoke/gate evidence (captured logs, matching the host copies byte for byte): `step2_smoke.log` shows item-1
`HEAD=cbf7a003 dirty_lines=0`, `measurement_path_check` rc 0 with `paths 308`, the 15-file `noise_floor` closure and
`engine_files_in_closure: []`; torch312 and jax312 pytest `75 passed in 1.52s` each with rc 0; `g4_tasl.py
harness-check` rc 0; strict `check-note` rc 0 with `{ok: true, mode: strict, run_id: g4b-tasl-20261124-a,
harness_commit: cbf7a003…, host_check_commit: c025f89a…, g4b: true, paper_commit: 90d4dcee…, spec_sha256:
56f8c293…}`; `verify_launch_tasl` rc 0 with the binding and all six import-source paths. The memo's §1–§2 statements
are accurate (the P4 review files `G5_DIFF_RECOUNT_REVIEW_20261124.md` sha256 `6dd4ffda…` and
`G4B_REPILOT_PREP_REVIEW_20261124.md` are on `origin/main` `912a7e02`, and the G.4 report cited by the note hashes to
`07c03920…dbe8` there, so the strict note check is meaningful).

## 2. Offline re-classification of G.4's refusals — PASS

`reclass/g4_reclassify_20261124.json` sha256
`d5a6c4bb23d2f5062f3f050a2e23f1b242b943dba45b0ac0f22ac5d17ff3e660` (the same sha on the host at
`records/g4-tasl-20261121-a/g4_reclassify_20261124.json`), schema `trackg_g4_reclassify/v1`,
`script_commit = harness_root_commit = cbf7a003`, `harness_root_dirty = false`, `script_checkout_dirty = false`.
Values: `refused_before` 122 `malformed_hunk` + 33 `malformed_diff`; `g4_rule_replay.matches_ledger` 155 with an empty
mismatch list; `incumbent_unverified` 0; `accepted_by_g4_rule` 25 with `accepted_text_unchanged` 25; `with_recounted_headers`
155; `left_to_strict_parser` `{}`. Projection: `new_rule` applied 138 / duplicate 12 / refused `context_mismatch` 5;
`by_reason` 110+12 and 28+5; per node 56+3, 37+11, 45+1+2 (sums 59/48/48, applied 138, duplicates 12, context 5). All
match memo §3, and the static-projection caveat (`basis`) is stated in the memo.

Provenance re-checked: the `/tmp/g4caps` capture archive used by the reclass equals the G.4 captures committed on
`ops-tasl-20261116` (`MANIFEST.sha256` sha256 `b83d115b…dda08` = the copy at `origin/main` `912a7e02` and in the
review worktree); the reclass run exited 0 with empty stderr (`step3_reclass.log`), and `paper_g4`'s `FETCH_HEAD`
mtime is unchanged from 22 November (the memo's disclosed deviation — fetch into `paper_g4b` instead of `paper_g4` —
is real and did not touch `paper_g4`).

## 3. Three worker nodes, liveness, ledger and GPU-hours — PASS

From the job records / `pilot_summary.json` / `ledger_check.json` (host copies and captures are byte-identical):
three nodes, `ok: true`, `stop: null`, `stop_class: null`, `stops: []`, no `_refusals/` anywhere under the run root,
one `attempt-1` per node (no retry), `NODE_EXIT=0` and `systemd_run_rc=0` in all three node logs. Totals:

- proposals 180; ran 126; kept 47; discarded 75 (excluding divergent); divergent 4 (all `mlab_cifar10`); duplicate 37;
  refused 17, all `context_mismatch` (15/0/2); invalid/inert/timeout 0.
- per node ran 40/49/37 of 60; `ran_of_valid` 0.6667/0.8167/0.6167 and total 0.7000; `ok_of_proposals`
  0.6000/0.8167/0.6167 and total 0.6778.
- per node job spans 1140/1292/2002 s (total 4434 s); campaign wall 1137.6/1290.4/1999.6 s; in-run GPU time
  283.9/638.4/1208.2 s (0.5918 GPU-h); `2 × 4434 / 3600 = 2.4633` GPU-h, equal to 0.6333 + 0.7178 + 1.1122 — inside
  the 11.077 GPU-h projection and far inside the 20 GPU-h cap. The TASL-7 server span 14:49:56–16:15:58Z is 1.4339 h,
  as stated.
- G.4 comparison reproduced from the G.4 report and its captures: ran 1/11/10 and 22; refusals 59 (53/6), 48 (45/3),
  48 (24/24) and 155 (122/33); `ran_of_valid` 0.0167/0.1833/0.1667 and 0.1222; GPU-h 0.4972/0.4594/0.6150 and
  1.5717. The memo's G.4/ G.4b table is accurate on every cell.
- timing: run medians 7.032 < 13.347, 13.014 < 40.795, 30.441 < 61.781 s (the declared bases), `timeouts` 0; `fit`
  shows `all_fit_ctx: true`, `calls_at_completion_cap: 0`, `cache_prompt_false_on_every_call: true`, 60 calls per
  node; `/props` identical before and after every node (`b1-620d222`, 32,768 context, one slot, the pinned GGUF).
- `diff_recount` ledger check re-derived independently from the 9 host ledger files (63 lines each; 60 proposal lines
  per node, 180 total): every proposal line carries `rule: trackg_diff_recount/v1`; `raw_diff_sha256` equals
  sha256(`proposal.diff`) for all 180; where `changed` is true (122 = 41/48/33) `runs[0].diff.diff_sha256` equals
  `applied_diff_sha256` with no mismatch; where `changed` is false (58) `proposal.diff` equals `runs[0].diff.diff_text`
  byte for byte (including the 17 refused lines, whose run record is present with `executed: false`). The repo-side
  `ledger_check.json` totals (122/58, `ok: true`, `problems: []`) encode the same facts; the memo's §5 is exact.

## 4. Seals, out.tar and proposer server — PASS

Sealed attempts at `sealed_g4/g4b-tasl-20261124-a/<node>/attempt-1/` exist for all three nodes; `sha256sum -c
SHA256SUMS` is OK in each (re-run on the host), and the sealed file digests match the memo §7 and the capture
`sealed_SHA256SUMS`:

| node | SEAL_RECEIPT | job_record | out.tar | node.log |
|---|---|---|---|---|
| `mlab_cifar10` | `b795b17d…` | `9fc8e868…` | `5f9c2f2a…` | `27052119…` |
| `mlgym_fmnist` | `da3a24ac…` | `13d2f658…` | `5d0b48dd…` | `ea037f1c…` |
| `mlgym_breakout_minatar` | `ad45f5aa…` | `d475e9e5…` | `8661e5b8…` | `7c1ed5f6…` |

All three receipts have `stop: null`, `stop_class: null`, the same `server_record_json_sha256 cf864800…`,
`server_end_json_sha256 3fe5f18c…` and `llama_server_log_sha256 ac9dff50…`, and `sealed_utc 2026-11-25T16:17:14Z`,
after the 16:15:58Z stop. G.4's sealed receipts are byte-unchanged (`19050924…`, `bf22fb1b…`, `1ad040e0…`, mtimes
22 November).

Server: `server_record.json` sha256 `cf864800…` (server dir on TASL-7 and the copy in `records/` on TASL-2),
`server_end.json` `3fe5f18c…` (`server_rc 0`, `stop_signal 15`, stopped `2026-11-25T16:15:58Z`),
`llama-server.log` `ac9dff50…` with exactly 180 `slot launch_slot_` entries (verified by count;
`llama log tasks after stop: 180` in the stop log); serve pid 1486189, llama-server pid 1486296; binary
`b70f4882…`, build `version: 0.7.0-dev (build 1, commit 620d222)`, GGUF `2959c1b0…`, `bin_manifest` `a29c667f…`,
`ldd_outside_bin_dir: []`. After the run both hosts are quiescent: TASL-2 353 MiB / 0 %, no compute apps, no
`llama-server`/`g4_tasl.py`/`pilot_g4` process, port 8095 not listening; TASL-7 44 MiB / 0 %, same process/port
state. The GPUs and the `gpu0.lock` leases were free at the final capture on both hosts (`final_TASL-2.json`,
`final_TASL-7.json`), and the same holds at review time.

## 5. R1-BX-D14 dates — captured, changed, not applied — PASS with one prose defect (m1)

`dates_g5.json` sha256 `e3f6f485…` (eight-node G.5-table binding) and `dates_g4.json` sha256 `75f531ca…` (seven-node
comparison) are byte-identical between the host `records/g4b-tasl-20261124-a/` and the captures; both `.err` files are
empty; `step6_dates.log` records `dates_g5_rc=0` and `dates_g4_rc=0`; both JSONs carry `today: 2026-11-25`. Values:

| value | G.4 published (verified in G.4's `dates_recompute.json` sha `90dc8bf8…`) | G.4b eight-node | G.4b seven-node |
|---|---|---|---|
| `labels_done` | 2026-11-30 | 2026-12-11 | 2026-12-05 |
| `B7` | 2026-12-03 | 2026-12-14 | 2026-12-08 |
| `D3` | 2026-12-29 | 2027-01-09 | 2027-01-03 |
| `manuscript` | 2027-01-05 | 2027-01-16 | 2027-01-10 |
| total / cap / within | 31.7 / 230 / true | 216.9 / 425 / true | 78.2 / 230 / true |
| longest node | 7.5 | 138.69 | 21.93 |
| `binding_K` / `ran_share` / `keep_share` / `dup_factor` | 10 / 0.1667 / 0.7273 / 0.9 | 10 / 0.6667 / 0.3469 / 0.9184 | same as binding |
| `llm_seconds_median` / ratio | 12.332 / 0.4546 | 11.83 / 0.497 | 11.83 / 0.497 |
| slack to targets (B7 2026-12-08, D3 2027-01-03, manuscript 2027-01-10) | +5 d | −6 d | 0 d |

The memo's §8 table and its handling are correct: the change is reported to the author, **nothing is applied** — on
`origin/main` `912a7e02` no date row was changed (the new dates `2026-12-14`/`2027-01-09`/`2027-01-16` appear nowhere
under `docs/` except an unrelated precheck capture), the host `paper_g4b` HEADs stay at the launch commit, and no commit
or push carries them. This is the R1-BX-D14 (iii) requirement ("changed dates go to the author before they are
applied") and the note's `dates` line. Only the prose delta statement is wrong: it says B.7/D.3/manuscript each moved
+5 days, which is true only for the seven-node comparison; the eight-node binding moves all four values by +11 (m1).

## 6. Preservation and host state — PASS

Old runs/seals/checkouts are preserved: `runs/g1b-*`, `runs/g4-tasl-20261121-a`, `sealed_g1b/*`,
`sealed_g4/g4-tasl-20261121-a` (receipt mtimes 22 November), the preserved `paper_g4.old_9c2979a2_*` checkouts on
both hosts, and the G.4 server directories and pre-existing G.4 record files (mtimes 22 November; the G.4 records
directory itself gained only the disclosed reclass JSON, see m7). No `_refusals/` directory exists under the
G.4b run root; only `attempt-1` for each node. `paper_g4b` is tracked-clean on both hosts with only the copied signed
note untracked. The memo's §9 statement is accurate.

## 7. Report/captures accuracy

Every host-derived capture was compared to the live host file and matches byte for byte: the three nodes'
`job_record`/`pilot_summary`/`node.log`/`attempt.json`/`SEAL_RECEIPT`/`SHA256SUMS`/`ledger_check`, the server files
(`server_record`, `server_end`, `llama-server.log`, `bin_manifest`, `serve.out`, `serve.pid`), the reclass JSON, the
dates files, all 12 evidence logs in the captures (10 written on TASL-2, `step4_serve_start.log` and
`step5_stop_server.log` on TASL-7), and `server/serve.out`/`server/serve.pid`. The capture `MANIFEST.sha256` verifies all 52 entries and covers
every file except itself. The memo's numbers nowhere exceed the captured bytes; the only defects are documentation and
capture-summary precision items in §8.

## 8. Findings

**No BLOCKING, no MAJOR.**

- **m1 (MINOR, memo §8 prose, lines ~175–179).** "B.7, D.3 and manuscript each +5 days" is true only for the
  seven-node comparison; in the eight-node binding column the same three values move by +11 days
  (`12-03→12-14`, `12-29→01-09`, `01-05→01-16`). The table is right; reword to "+5 d seven-node / +11 d eight-node"
  for all four rows so the prose does not contradict the table the author will use.
- **m2 (MINOR, memo §10, TASL-7 bullet).** The TASL-7 `logs/g4b_20261125/` list includes `step6_dates.log`; that
  file exists only on TASL-2 (where the dates commands ran). TASL-7's directory holds exactly `serve.out`, `serve.pid`,
  `step1_paper_g4b.log`, `step4_serve_start.log`, `step5_stop_server.log`. Fix the path list.
- **m3 (MINOR, capture `evidence/step6_dates.log`).** The "key values" block prints the R1-BX-D14 *target* dates under
  labels "G5-table dates" / "G4-compare dates" (`B7 2026-12-08`, `D3 2027-01-03`, `manuscript 2027-01-10`), while
  `dates_g5.json` records `B7 2026-12-14` (and only `dates_g4.json` has `B7 2026-12-08`). The primary JSONs are
  correct and the memo uses them, but the log summary reads as if the dates had not changed; correct the extractor or
  annotate the log so the capture cannot be read against the memo.
- **m4 (MINOR, captures `evidence/step2_smoke.log` and `step3_reclass.log`).** `step2_smoke.log`'s harness-check JSON
  is truncated at its start (it begins mid-`closure`; no schema/repo/commit/`g1b_pin`/`paths` fields) although rc=0 is
  recorded and the adjacent `measurement_path_check` output carries the same binding. `step3_reclass.log`'s post-run
  summary prints `checkouts_clean: None None`, `totals_keys: []`, `refused_before: None`, … because it looks for keys
  at the JSON's top level while they are nested under `total`/`nodes` (the JSON itself is correct and is what the memo
  cites). Complete/fix the summary blocks if these captures are the durable record.
- **m5 (MINOR, memo §9 clock note).** "TASL-2's clock read ~33 s ahead of TASL-7's" has no supporting simultaneous
  cross-host observation in the captures. The cross-host order still holds with a wide margin (server stopped
  16:15:58Z on TASL-7; the last node finished 16:06:01Z on TASL-2, ~10 min earlier), so the conclusion is safe; cite
  the observation or soften the number.
- **m6 (MINOR, memo §1).** "`harness` (`c025f89a`), `harness_g5` (`52e3c0b0`) and `paper_g4` (`6ad899e0`) were left
  untouched on both hosts" — TASL-7 has no `harness_g5` (and no `harness_g4b`); only `harness` and `paper_g4` exist
  there. Phrase as "on the hosts where they exist"; the untouched claim itself checks out for every existing checkout.
- **m7 (MINOR, memo §9 wording).** "The only same-name inputs touched were the launches' own new checkouts …" is
  slightly too strong: the reclass JSON is a new file inside the old G.4 records directory
  `records/g4-tasl-20261121-a/` (disclosed in §3/§10 and intended by the recipe, but it is a same-name directory
  change). Add it to the sentence; the sealed/runs/seal entries are indeed unchanged.

## 9. Conditions before the author applies the dates

The memo satisfies R1-BX-D14 (iii): the change is captured and reported, and nothing is applied. Before applying
anything, the author should note:

1. **Which basis to apply.** The *binding* eight-node sheet moves B.7/D.3/manuscript to 2026-12-14/2027-01-09/
   2027-01-16 (and `labels_done` to 2026-12-11), 6 days after the R1-BX-D14 targets; the seven-node comparison
   2026-12-08/2027-01-03/2027-01-10 lands exactly on them. The eight-node total (216.9 GPU-h) is not like-for-like
   with G.4's published seven-node 31.7 — 138.69 of the 216.9 is `autoresearch_fixedtokens` — so the +6-day slip is
   attributable to the recount driving the full eight-node table, not to the seven-node table (which is 0 d).
2. **Recompute anchor.** The dates were computed with `--today 2026-11-25`. Any application on a later date needs a
   fresh recompute, and the change itself must be a `main` edit that records the new target rows; the memo (and its
   corrected prose, m1) stays a report, and its sha256 should be preserved if it is committed as the durable record.
3. **G.5-side open item.** G.5's `pilot_basis`/P3 still name the G.4 spec/run (prep report §8). The dates used
   `--pilot-spec` and are unaffected, but if P3's baseline is to rest on G.4b, that needs a separate reviewed
   G.5-side change; it does not block the date decision.
4. **Capture fixes before publication.** m1–m4 should be corrected (or annotated) if the memo plus these captures are
   to be the committed record; m5–m7 are wording.

## 10. Verdict

**ACCEPTED.** The G.4b re-pilot result is reproducible from the captured bytes and the host state: bindings, smoke,
harness rule, strict note check, offline reclass, three nodes with seals/receipts/`out.tar`, `stop: null`, the
`diff_recount` ledger invariant on 180/180 proposals, 2.4633 GPU-h, 17 refusals vs 155, liveness 0.7000 vs 0.1222,
no STOP and no liveness 0, full preservation, and the R1-BX-D14 dates captured and correctly reported as *changed, not
applied*. The seven MINOR findings are documentation/capture-summary precision and should be applied before the memo is
committed as the durable record; none affects a number or the PASS conclusion.
