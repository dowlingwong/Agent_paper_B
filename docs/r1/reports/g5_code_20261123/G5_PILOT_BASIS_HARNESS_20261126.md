# G.5 unit: pilot basis on the G.4b result, recount harness commits, xc3 rules by import, CUDA-IPC on TASL-7, TASL-7 audit chunks in the dates (26 Nov 2026)

Prepared by the Mac-desk agent (Claude), AI-assisted, on branch `mac-g5-pilot-basis-g4b-20261126` from published
`main` `f1f1b651` (main did not move during the unit). Paper B, route R1, T1 G.5. ENGINEERING_ONLY desk work: no host
was used, nothing was pushed, no label, evaluation value, sealed file, `*block.jsonl` or `*b1_manifests.json` was
opened, and `gate.py`, `gate_input_builder.py`, `release.py` and the preregistration are unchanged. The harness was
read with `git -C /tmp/pb/harness show` and checked with the G.5 code's own desk checks. **For independent review.**
The G.5 draft stays `approved: false`.

**Authority (on `main` `f1f1b651`).** R1-G5-DIFF-RECOUNT; R1-BX-D14-G4B (G4B-DATES A: the binding eight-node
recompute; the dates are targets, not gates; the coordinating chat recomputes when the expansion nodes are known and
when READY 108's TASL-7 audits are in the dates tool); R1-XC3-FAIL-READING (A); R1-XC3-NOTE (the signed note
`authorizations/g1b_xc_short_t1_tasl_20261126.md`: `xc3_fail: A`, `xc3_cap: R1-G1B-CAP`, `skip_nodes: none`);
R1-G5-EXPANSION-JOIN; R1-G5-AUDIT-TWO-CARDS; R1-T1-D21-SCOPE; the G5 rows (R1-G5-DECISIONS, -DECISIONS-2, -MEM-E4).
The committed G.4b result `reports/tasl_chain_20261122/G4B_TASL_PILOT_RESULT_20261125.md` (sha256 `af74c536…`, the
reviewed memo) with `G4B_TASL_PILOT_RESULT_CORRIGENDA_20261125.md` (sha256 `3eca0732…`) and the captures beside it.

**Commits.**

| commit | what |
|---|---|
| `f3b18e9c` | code, spec and tests (`g5_tasl.py`, `g5_tasl_spec.json`, `g5_job.py`, `test_t1_g5_tasl.py`, `test_t1_g5_job.py`) |
| `4bbbd8d2` | G.5 draft revision 12, the release-rows draft note, the draft-render test |
| `28ed1405`, `ec6348a4`, and the last commit | this report (results filled in the last commit), the draft header line, the two full-suite lists |

The unreviewed preparation `mac-g5-pilot-basis-g4b-20261125` @ `a9c23230` (base `f55b8a1e`) was read with `git show`
and ported by hand; it was not merged, and its worktree `/tmp/pb/wt/g5pb` was not touched.

---

## 1. pilot_basis and P3 (the G.4b re-pilot)

### 1.1 What the spec now binds

`g5_tasl_spec.json` `pilot_basis` names run `g4b-tasl-20261124-a` and binds, by path and sha256 (as the prep bound
the spec), every file P3 rests on, with every value taken from the committed result. No placeholder remains.

| field | value | source |
|---|---|---|
| `spec` | `sweep2/t1_tasl/g4b_tasl_spec.json`, `56f8c293ddd3fa3bbf64b55c36f1139231c0a44631d2b5179b3e5471dcb86a1b` | result §1; the file on `main`; every sealed job record's `spec_sha256` (captures) |
| `note` | `docs/r1/authorizations/g4_t1_tasl_20261125.md`, `df600e3f7e66ea6ea413c549812ccea11a909bb06cb82527a08f5b679d541db2` | result §1 (copied byte-identically from `main`); `approved: true`, `run_id` and `spec_sha256` checked |
| `result_report` | `…/G4B_TASL_PILOT_RESULT_20261125.md`, `af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb` | the file on `main`; the corrigenda name `af74c536…` as the reviewed, unchanged memo |
| `corrigenda` | `…/G4B_TASL_PILOT_RESULT_CORRIGENDA_20261125.md`, `3eca07329cc177cd317169270eb2d0bbd66ed29bf074ae0a1a7a559d448291ae` | the file on `main` (new binding; R1-BX-D14-G4B cites §8 "with its corrigenda") |
| `dates_row` | `R1-BX-D14-G4B` | PLAN; the switch requires it on `main` naming "G4B-DATES A" and "eight-node" |
| `sealed.<node>.sealed_path` | `/home/dowling/r1_tracks/t1_tasl/sealed_g4/g4b-tasl-20261124-a/<node>/attempt-1` | result §7, §10; each capture `SEAL_RECEIPT.json` `sealed_path` |
| `sealed.mlab_cifar10` | receipt `b795b17d…101c`, job record `9fc8e868…1fa7`, pilot summary `048c818f…e143` | result §7 table; captures `MANIFEST.sha256` |
| `sealed.mlgym_fmnist` | receipt `da3a24ac…4ac9`, job record `13d2f658…8319`, pilot summary `a80b4422…5da0` | same |
| `sealed.mlgym_breakout_minatar` | receipt `ad45f5aa…2cfe`, job record `d475e9e5…414d`, pilot summary `40bf933d…5688` | same |
| `liveness` (`proposals`, `ran_of_proposals`, `ran_of_valid`, `ok_of_proposals`) | `mlab_cifar10` 60, 0.6667, 0.6667, 0.6; `mlgym_fmnist` 60, 0.8167, 0.8167, 0.8167; `mlgym_breakout_minatar` 60, 0.6167, 0.6167, 0.6167 | result §4 table; each capture `pilot_summary.json`, equal to the sealed job record's `summary` |
| `dates` | `today` 2026-11-25, `labels_done` 2026-12-11, `B7` 2026-12-14, `D3` 2027-01-09, `manuscript` 2027-01-16, `g5_total_gpu_hours` 216.9 | result §8 binding column; capture `dates_g5.json` (sha256 `e3f6f485…`) |
| `projection.gpu_hours_p7` | 216.9 | = `pilot_basis.dates.g5_total_gpu_hours` (R1-BX-D14-G4B: "216.9 of 425 GPU-h") |

Full sha256 values are in the spec. The spec sha256 changes from `a80b16e2…` (base) to
**`1e29b59529443f1705770fa792fb937045a3bb5f9f5db06593d7f1289b4848e9`**.

**Conflict stated (pilot-summary sha256).** The result report does not print the sha256 of
`out/pilot/pilot_summary.json` inside each sealed `out.tar`. The value used is the sha256 of the committed capture
`<node>/pilot_summary.json` (listed in the captures' `MANIFEST.sha256`). At the desk the capture's JSON equals the
sealed job record's `summary` (which the job-record sha256 binds, and which `run_node_job` reads from that very file
before the tar), but byte identity with the tar member cannot be shown without the sealed `out.tar`, which is only on
TASL-2. `pilot_basis_check` compares the member's sha256 at every TASL-2 job start and at `g5_tasl.py pilot-basis`,
so a mismatch refuses (fails closed) and would need a one-field fill from TASL-2 and a new render.

**Desk reproduction of the binding dates.** `g4_tasl.recompute_dates` on the three captured summaries with this
spec's `dates_params` and `today` 2026-11-25 gives exactly the captured `dates_g5.json` (the whole JSON is equal), so
the eight-node binding is the G.5 spec's own recompute (G4B-DATES A); the seven-node `dates_g4.json` (78.2 GPU-h) is
not used.

### 1.2 Code (`sweep2/t1_tasl/g5_tasl.py`)

Ported from the prep (`c872492d`): `pilot_spec()`, the P3 settings check reading the G.4b spec's `pilot` block,
`pilot_basis_check(spec, read_main)` at every **TASL-2** job start (`launch(..., pilot_check=)`), the CLI
`pilot-basis <spec>`, the P7 tie (`projection.gpu_hours_p7` must equal `pilot_basis.dates.g5_total_gpu_hours`),
`check_note`'s P3 citation of the result report, the G.4b checkout `harness_g4b` among the checkouts a G.5 family may
not use, the RESERVED label "G.4 and G.4b", and the docstrings.

Changed against the prep:
- **No placeholder machinery.** The prep allowed `PENDING G.4b RESULT: …` before launch (34 placeholders). All values
  are now filled, so `check_pilot_basis` accepts no placeholder at all (`pilot_pending` and its tests are dropped).
- **More is bound:** the note is `{path, sha256}`, the corrigenda are bound, and `dates_row` names R1-BX-D14-G4B. At
  desk validation each bound file's sha256 must equal the checkout's file; at job start, the file on `main`.
- **TASL-7 jobs do not re-read the seals** (they are on TASL-2); they still pass the validator's `pilot_basis` checks.
  The prep predates the TASL-7 host.
- The switch adds R1-BX-D14-G4B (terms "G4B-DATES A", "eight-node") to the rows it checks on `main` and binds.

### 1.3 STOPs and thresholds that read pilot values

| rule | reads | G.4b values | outcome |
|---|---|---|---|
| STOP 3 (ran-of-valid below `liveness_floor` 0.25 after wave 1) | G.5's own wave-1 ledgers, not the pilot | `ran_of_valid` 0.6667 / 0.8167 / 0.6167 | all above 0.25: no pilot node points to a likely STOP 3 (G.4's strict values 0.0167 / 0.1833 / 0.1667 were all below). The prep's open point is closed. No code makes a pilot value a P3 blocker |
| D4 node STOP (zero diff liveness) | the pilot summary (`g4_tasl`) | none zero | not triggered |
| P7 (within the cap) | the recompute | 216.9 of 425 | within; P7 tie enforced |
| P7 tie (prep open point) | `pilot_basis.dates` | 216.9 = 216.9 | kept as in the prep: draft §8 calls the recompute "the binding P7 number" |
| G5-DIV B (not chosen) | `divergence.pilot_counts` | (G.4b: 4 divergent on `mlab_cifar10`, 0, 0) | not used under the signed G5-DIV A; nothing filled |
| audited band (STOP 9) | G.5's own counts | projected audited 146.9 / 180.0 / 135.9 for the pilot nodes | inside 100–200 |

## 2. Harness commits (R1-G5-DIFF-RECOUNT)

`harness_families.G5-7.g5_commit` = `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98`, `harness_families.G5-AR.g5_commit` =
`ccdb3774f60dbca21adc918777a0ddd2e6e634f8`. Both are on the remote harness (`refs/heads/mac-trackg-g5-7-20261124`,
`mac-trackg-g5-ar-20261124`, checked with `git ls-remote`). `cbf7a003` is also the commit G.4b ran on (`harness_g4b`).

Desk checks the switch makes, run on `/tmp/pb/harness` (also in `test_recount_tips_pass_the_desk_harness_checks`
against `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, which holds both tips):
- `g5_pin_check.py <repo> cbf7a003 ccdb3774`: rc 0. Pin delta 10 paths (autoresearch's node and config files,
  `node_lib/ar_isolated.py`, a report, three tests); G.5 changes identical in both families: `audit_g5.py`,
  `campaign_v2_diff.py`, `scripts/trackg_g4_reclassify.py`, two reports, two reviews, three tests.
- `measurement_path_check` (P5 freeze) G5-7 against `c025f89a` and G5-AR against `2d09f9a9`: rc 0 each; 308
  measurement-path files, the 15-file `noise_floor` closure (5 outside trackg), no engine file in it, the only trackg
  addition `audit_g5.py`.
- `g5_job.check_engines` (the engine contract `g5_tasl_engine_contract/1`) passes at both; `campaign_v2_diff.py`
  carries `trackg_diff_recount/v1` at both; `pilot_g4.py`, `manager_v2_diff.py`, `proposal_v2_diff.py` keep the pin's
  entries.

Operational note (not code): on 25 Nov TASL-2's `harness_g5` was at `52e3c0b0` (G.4b result §1). Before the first
G.5 job both family checkouts (and TASL-7's `harness_g5` for audit chunks) must be at the new commits, or STOP 13.
**The G.4b sealed attempts (`sealed_g4/g4b-tasl-20261124-a/<node>/attempt-1` on TASL-2) must stay in place, unchanged,
until G.5 is sealed:** every TASL-2 job start re-reads them (P3), and a moved or changed file refuses the job
(review round 1, m6).

**§5 key-lines block re-rendered** (draft revision 12): against revision 11 exactly five lines changed —
`harness_commit` (the two tips; the PENDING harness line is gone, as is its row in the PENDING table), `gpu_hours`
("216.9 (P7, post-pilot recompute)"), `cuda_ipc`, `cuda_ipc_acceptance` (§4) and `spec_sha256`. A new test checks
that every rendered line except `approved:` is in the draft.

## 3. xc3 rules by import

Removed from `g5_tasl.py`: `xc3_note_decisions`, `xc3_row_option`, `XC3_DECISIONS`, `XC3_ROW_SENTENCE`,
`XC3_OPTIONS`. `xc3_reading` now calls `g1b_crosscheck.short_decisions(fields, {"nodes": short_nodes(spec)})` and
`g1b_crosscheck.xc3_fail_row_option(read_main)` (READY 107, on `main`); `XC3_ROW = X.XC3_FAIL_ROW`. A refusal from
`short_decisions` is re-raised with the note's path in front; accept/refuse outcomes are unchanged. `check_xc_note`
is not used: it checks a note file on disk against the spec file and paper commit for the xc3 launch, while the
switch reads the note from `main`.

- **Equivalence:** the 20 recorded cases (13 note cases, 7 row cases, recorded from the xc3 branch on 25 Nov) run
  through the imported functions and through `xc3_reading` with the same outcomes
  (`test_round2_n4_xc3_rules_are_the_xc3_units_imported`).
- **Frozen closure:** `g1b_crosscheck` was already imported by `g5_tasl` (as `X`), so nothing new enters the import
  closure; `g1b_crosscheck.py` is unchanged, so the xc3 launch commit's code is untouched. Nothing in the G.1b, xc3
  or G.4 launch paths imports `g5_tasl` (only `g4_tasl.harness_rule_check`, lazily, for G.4b). `sweep2/t1_tasl`
  freezes at the G.5 launch.
- **Real `main`:** with `read_main = origin/main` (`f1f1b651`) the switch reads `{xc3_fail: A, note:
  docs/r1/authorizations/g1b_xc_short_t1_tasl_20261126.md, row: true, skip_nodes: [], run_id:
  g1b-tasl-20261121-b-xc3-a}`; the note binds the xc3 spec on `main` (`fc064ded2a79fa97…`, `xc_spec_sha256`) and its
  run id; R1-XC3-FAIL-READING says "The xc3 note carries xc3_fail: A." and agrees. The three xc2 nodes pass
  `check_crosshost_pass` on `main`; the four short-check nodes are refused on TASL-7 (no short verdict on `main` yet),
  as designed. A test pins this on the checkout's files (`test_xc3_reading_on_published_main_is_xc3_fail_a`).

## 4. CUDA-IPC acceptance on TASL-7

Found: `CUDA_IPC_ACCEPTANCE` named TASL-2 only; the code check was the note line (acceptance) or `check_c12`
(TASL-2's record, `c12_host` = TASL-2) at every job start; revision 11 left the TASL-7 wording to the author.

Now:
- The acceptance line reads: "The author accepts, for the G.5 label runs (EVIDENCE) on TASL-2 and for the G.5 audit
  chunks on TASL-7 (R1-G5-AUDIT-TWO-CARDS), the residual risk that harness-isolation host-check item 7 (…) is untested
  on TASL-2 and on TASL-7: … every run record that is not effective with empty waivers and exceptions still STOPs its
  job (STOP 2), on either host. Disclosed in the T1 report." The `cuda_ipc` line under acceptance adds "(TASL-2 and
  TASL-7's audit chunks)". Both host records state item 7 untested.
- Under `c12`, each host needs its own record: new spec fields `c12_tasl7_record`, `c12_tasl7_sha256`,
  `c12_tasl7_review` (null by default; validated like TASL-2's). `check_c12(spec, read_main, host=)` checks the host's
  record (`c12_host` must be that host's name). The switch checks TASL-7's record at a TASL-7 audit job start, and
  `g5_job.tasl7_eligible` (so `claim_chunk`) refuses a claim without it; TASL-2 jobs are unaffected. Without a TASL-7
  record the `cuda_ipc` line says no audit chunk runs on TASL-7.
- The draft §5 and P1 carry the new wording; §10 C12 names both hosts.

The wording is still the author's to sign or amend (§7, S4).

## 5. The dates tool counts TASL-7 audit chunks

`g5_tasl.py dates <spec> <sealed…> [--pilot-spec …] --today <d> --tasl7-audits [--tasl7-nodes <node> …]` keeps the
one-slot output unchanged (so `pilot_basis.dates` and P3 are unaffected) and adds a `tasl7_audits` block
(`tasl7_dates`), modelled on READY 108's rules as built:
- **Eligible nodes:** `--tasl7-nodes` (explicit; any G5-7 node; each is looked up on `main` and reported as "cross-host
  PASS on main" or "a scenario"); default `default_tasl7_nodes`: the xc2 nodes whose PASS records are on `origin/main`
  (today `mlab_cifar10`, `mlgym_breakout_minatar`, `mlgym_cifar10`). Autoresearch and non-G5-7 nodes are refused;
  G5-TASL-GPUH B is refused (TASL-7 chunks not built there).
- **Which chunks:** per node and wave, the chunks `g5_job.chunk_plan` cuts (census run time × 1.25 × 1.5 per run, up
  to 82,800 s) for ceil((audited + parents) × the wave's share of 12 instances) units × the K audit seeds. **Chunk 0
  cannot move** (the TASL-2 audit job that makes the wave's plan takes it under the claims lock; a claim before the
  plan is refused, and `claim_chunk` refuses a chunk with TASL-2 attempts), and **the last chunk (E5) cannot move**; so
  only chunks 1 … n−2 are claimable, each at its runs × the 4090 run time × 1.25 plus one startup.
- **The lease:** TASL-7 serves the proposer during every campaign wave, so a TASL-7 chunk never overlaps a campaign:
  label span = max(TASL-2 load, campaign hours + TASL-7 audit hours, each node's own work less its claimable TASL-7
  hours), TASL-7 taking x = min(claimable hours, half the non-campaign hours). Dates from the span as
  `g4_lib.recompute_dates` does. GPU-hours unchanged (counted inside the cap, the recommended reading).

### 5.1 The recompute for the coordinating chat (R1-BX-D14-G4B) — reported, not applied

Binding command (TASL-2, published checkout with this unit merged):

```
python3 sweep2/t1_tasl/g5_tasl.py dates sweep2/t1_tasl/g5_tasl_spec.json \
  /home/dowling/r1_tracks/t1_tasl/sealed_g4/g4b-tasl-20261124-a/mlab_cifar10/attempt-1 \
  /home/dowling/r1_tracks/t1_tasl/sealed_g4/g4b-tasl-20261124-a/mlgym_fmnist/attempt-1 \
  /home/dowling/r1_tracks/t1_tasl/sealed_g4/g4b-tasl-20261124-a/mlgym_breakout_minatar/attempt-1 \
  --pilot-spec sweep2/t1_tasl/g4b_tasl_spec.json --today <date> --tasl7-audits [--tasl7-nodes <nodes>]
```

The sealed attempts are not on `main`, so the desk output below uses the committed captured summaries (equal to the
sealed job records' summaries; the one-slot part reproduces `dates_g5.json` exactly) through the same functions:

| `--today` | nodes on TASL-7 | claimable TASL-7 GPU-h | label span (h) | labels done | B.7 | D.3 | manuscript | slack vs 8 Dec / 3 Jan / 10 Jan |
|---|---|---|---|---|---|---|---|---|
| 2026-11-25 | none (one slot, the binding) | — | 216.9 | 2026-12-11 | 2026-12-14 | 2027-01-09 | 2027-01-16 | −6 |
| 2026-11-25 | default: the three xc2 nodes | 0.0 | 216.9 | 2026-12-11 | 2026-12-14 | 2027-01-09 | 2027-01-16 | −6 |
| 2026-11-25 | scenario: all seven G5-7 nodes | 0.0 | 216.9 | 2026-12-11 | 2026-12-14 | 2027-01-09 | 2027-01-16 | −6 |
| 2026-11-26 | default / all seven | 0.0 | 216.9 | 2026-12-12 | 2026-12-15 | 2027-01-10 | 2027-01-17 | −7 |

**Finding: for the eight nodes the TASL-7 audit chunks change no date.** No G5-7 node has a wave of three or more
chunks at these figures (wave chunk runs: `mlab_cifar10` 530 / 1060, `mlgym_breakout_minatar` 500 / 721+269,
`mlgym_cifar10` 530 / 1060, `mlab_imdb` 530 / 688+372, `mlab_ogbn_arxiv` 530 / 1060, `mlgym_fmnist` 640 / 1280,
`mlgym_houseprice` 530 / 1060), so nothing is claimable. Campaign hours with startup are 31.5 of 216.9; the binding
work is autoresearch's 138.7 GPU-h (120.8 of audits in 8 chunks), which may not run on TASL-7 (`ar-cond7a` is only on
TASL-2). For information only (not allowed by the code): if chunk 0 could also be claimed, `mlgym_breakout_minatar`
and `mlab_imdb` would each give about 8.0 GPU-h, and labels done would be 10 Dec, B.7 13 Dec (one day earlier). Any
such change (a plan-only TASL-2 step, smaller chunks for TASL-7, autoresearch on TASL-7) would be a new code unit and
an author decision; none is proposed here. The expansion nodes (cutoff 2 Dec) need the same recompute with their
spec entries.

## 6. Draft revision 12 and the release rows

`docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` (`approved: false`): status bullets (what is on `main`:
READY 100, 103, 104, 107, 108; the recount unit exists and is filled; this unit is not on `main`); a revision-12 entry;
§1 (main `f1f1b651`; rows R1-BX-D14-G4B, R1-XC3-FAIL-READING, R1-XC3-NOTE, R1-G5-EXPANSION-JOIN added; the
R1-G4-DECISIONS, R1-G5-DIFF-RECOUNT and R1-BX-D14 cells updated); §2.1–§2.5, §2.8 (G.4b as P3's basis); §2.10 (the
binding dates, XC3-FAIL **signed A** with the "open"/"neither chosen" wording removed, the imported rules, the real-main
reading, the TASL-7 dates finding, READY 107/108 on `main`); §2.11 (the G.4b recompute; the expansion addendum,
*(proposed)* path `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>_addendum_<N>.md`, not built); §2.12 (the recount
tips and the desk checks); §5 (the new render, its intro, the PENDING table without the harness row, `gpu_hours`
filled, the C12 case and the extended acceptance line); §6 (D7-DIFF B on `main`); §7 P1, P3 (rewritten from the prep's
Part B with the filled values), P5, P7; §8; §9 (built and remaining); §10 C8, C12; §11 items 2, 15, 21 and the lists;
**§11.1, what the author still signs** (§7 below). The prep's Part B text was used where still right; its 34
placeholders are filled from the committed result only.

`T1_RELEASE_ROWS_DRAFT_20261123.md`: a dated note (READY 100/103 on `main`, so the table is `g5_t1_table/2`;
XC3-FAIL A signed, so the XC3-FAIL B STOP does not arise; revision 12 changes `g5_tasl.py`, `g5_job.py` and the spec,
not the files the rows read). Row texts unchanged.

## 7. What the author still signs in the G.5 note

Also in the draft as §11.1. Options and recommendations; nothing is decided here.

| # | Note line(s) | Options | Recommendation |
|---|---|---|---|
| S1 | `cap_gpu_hours` and **how TASL-7 audit-chunk hours count** | (A) 425 GPU-h of the worker card with TASL-7 audit-chunk hours **inside** the cap (as built: the meter counts a registered TASL-7 attempt, STOP 9; after round 1 the rendered line says so); (B) outside, metered beside it (a `g5_job` meter change, review, new render); (C) a higher cap | **A** (same work, same GPU model; 216.9 projected leaves 208 GPU-h; no chunk can move for the eight nodes anyway) |
| S2 | `gpu_hours` | 216.9 (P7, bound in `pilot_basis`) | sign as rendered; an expansion node needs its own recompute |
| S3 | P3, P7 | P3 citing `g4b-tasl-20261124-a` and the result report (required by `check_note`); P7 "216.9 GPU-h within 425" | sign with those citations after `g5_tasl.py pilot-basis` on TASL-2 has PASSed and that PASS is recorded before the signature; the G.4b seals stay in place until G.5 is sealed |
| S4 | `cuda_ipc`, `cuda_ipc_acceptance` | (a) the extended acceptance line; (b) C12 on both hosts; (c) C12 on TASL-2 only (no TASL-7 chunks) | (b) if both host tests can run before the first job, else (a); (c) costs nothing now but blocks TASL-7 for an expansion node; the wording itself is the author's (sign verbatim or amend by a code change) |
| S5 | `job_layout` (the TASL-7 schedule, §11 item 20) | (A) as built, operator claims under the code's rules, no timetable; (B) no TASL-7 chunks for the eight nodes | **A** (equivalent in effect now; keeps the path open) |
| S6 | `freeze_wait` | (a) 18 Dec 2026 as proposed (labels done 11 Dec + 2 = 13 Dec; 5 days margin); (b) 13 Dec; (c) later | **(a)**; move by an author row if expansion nodes join |
| S7 | `liveness_floor`, `invalid_share_stop`, `infrastructure_stop`, `audited_band` | as proposed (0.25, 0.2, 5 %, 100–200) or others | as proposed (G.4b liveness ≥ 0.6167; projected audited counts inside the band) |
| S8 | `t1_table_readings`, `server_log`, `seal`, part 3b-1 readings and `campaign_attribution` | unchanged since revision 11 (§11 items 13, 17–19) | as in §11 |
| S9 | (a later addendum note) | *(proposed)* `c3_t1_labels_<YYYYMMDD>_addendum_<N>.md` with the same code, K and rules | fix with the code unit that reads it (not built); **open:** the frozen split file lists eight T1 nodes, so a ninth node's split and PRE-T1 entry need a decision first |
| S10 | `decisions`, `e4_amendment_row` | fills: R1-G5-DECISIONS-2, R1-G5-MEM-E4 | fill |
| S11 | `audit_K`, seed lines | K = 10; K = 6 only by a docs-only amendment after a K-check row | as rendered |
| S12 | `environments` (autoresearch) | `ar-cond7a` under R1-G1B-AR-ENV / R1-G1B-AR-PY, extended to G.5 | as rendered (completion record under G5-ARPEND A) |

Not signed in the G.5 note: XC3-FAIL, `xc3_cap`, `skip_nodes` (signed in the xc3 note and R1-XC3-FAIL-READING); the
dates (targets, R1-BX-D14-G4B); the eight-node basis (G4B-DATES A); the node scope (R1-T1-D21-SCOPE).

## 8. Tests

Environment: `/tmp/tgport312/bin/python`, `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, `TMPDIR=/tmp/g5pb2dev/t`,
`PYTHONDONTWRITEBYTECODE=1`; `python -m pytest -q -p no:cacheprovider r1/tests/<file>`, one file at a time.

| file | base `f1f1b651` | tip |
|---|---|---|
| `test_t1_g5_tasl.py` | 140 passed | **186 passed** (46 new ids: 24 `pilot_basis` refusals, 5 CUDA spec refusals, 2 P3 citation cases, 15 tests) |
| `test_t1_g5_job.py` | 51 passed | **52 passed** (the TASL-7 C12 claim check) |
| `test_t1_g5_seal.py` | 40 passed | 40 passed |
| `test_t1_features.py` | 30 passed, 1 skipped | 30 passed, 1 skipped |
| `test_t1_tasl_g4.py` | 47 passed | 47 passed |
| `test_t1_tasl_g4b.py` | 5 passed | 5 passed |
| `test_t1_tasl_crosscheck.py` | 79 passed | 79 passed |
| `test_t1_d7_diff_b.py` | 19 passed | 19 passed |
| `test_t1_tasl_xc3.py` (extra) | 4 passed, 1 failed | 4 passed, 1 failed (the same test, pre-existing: its note draft uses `xc3_fail: B`, and `main`'s R1-XC3-FAIL-READING now says A) |
| `test_t1_tasl_g5_ar_projection.py` (extra; reads the draft) | 6 passed | 6 passed |

Changed tests: `test_g5_temp_b_needs_a_pilot_at_zero` (a re-issued G.4 spec no longer clears P3; a re-issued G.4b spec
only when bound by sha256); the launch-ready world (`ready`, `note_text`, `go` with a fake P3 check, the dates row in
`UNIT_ROWS`); the C12 line; the xc3 equivalence test (now on the imported functions); the m6 checkout test
(`harness_g4b`). New: the shipped `pilot_basis` equals the committed result and captures; the desk recompute equals
`dates_g5.json`; refusals; the P7 tie; `pilot_basis_check` on synthetic sealed G.4b attempts (passes; 17 refusal
cases; not run on TASL-7); the `pilot-basis` CLI; the harness commits and the real-harness checks; the draft render;
the CUDA wording, spec refusals and the TASL-7 C12 path in the switch and the claim; the TASL-7 dates rules,
refusals, defaults and the eight-node finding; the xc3 reading on real `main`.

## 9. Full suite

`/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider -rfE r1/tests`, default options, lightgbm off, a fresh
`TMPDIR` per run (deleted after), started only when `pgrep -f "[p]ytest.*r1/tests"` found nothing. Base on a clean
detached checkout of `f1f1b651` (removed afterwards), then the tip.

| run | checkout | result | list beside this report |
|---|---|---|---|
| base | clean detached `f1f1b651` (a worktree under `/tmp/g5pb2dev/base`, removed afterwards), started 02:03:53Z | 59 failed, 4123 passed, 197 skipped, 3 errors, 53 subtests passed (330.9 s) | `FULLSUITE_PB2_BASE_f1f1b651_FAILED.txt` (62 ids) |
| tip | this branch at `ec6348a4` (clean tree; code `f3b18e9c`, draft `4bbbd8d2`/`ec6348a4`), started 02:09:38Z | 59 failed, **4170 passed** (+47: the 46 new ids of `test_t1_g5_tasl.py` and 1 of `test_t1_g5_job.py`), 197 skipped, 3 errors, 53 subtests passed (329.4 s) | `FULLSUITE_PB2_TIP_ec6348a4_FAILED.txt` (62 ids) |

The two sorted FAILED/ERROR node-id lists (each line's ` - message` cut) are **identical** (`diff` empty). The only
T1 id in them is the pre-existing `test_t1_tasl_xc3.py::test_note_draft_renders_the_spec_and_passes_the_checks` (§8).
The later report-only commit changes no code or test.

## 10. Conflicts and open points for the reviewer

1. **Pilot-summary sha256** from the captures, not printed in the result report (§1.1); checked on TASL-2 only.
2. **`--today` anchor.** `pilot_basis.dates` keeps the published binding's 2026-11-25 (what R1-BX-D14-G4B adopted).
   The corrigenda ask to re-anchor `--today` before application; on 26 Nov each date is one day later. Not applied.
3. **The corrigenda's last line** ("G.5's `pilot_basis`/P3 still read the G.4 spec") is resolved by this unit.
4. **TASL-7 audits give no date gain for the eight nodes** (§5.1); R1-BX-D14-G4B expected the recompute might move a
   date. The chunk-0 rule is READY 108's code, not a row; changing it would be a new unit.
5. **Expansion addendum not built**, and a ninth T1 node conflicts with the frozen split file's eight nodes (PRE-SPLIT
   A) unless the author decides how it enters; flagged, not decided (S9).
6. `cap_gpu_hours` now names the TASL-7 audit-chunk hours as counted (round 1, m4); S1 still offers the options.
7. `dates_pilot_spec` still requires the G.4b spec to have G.4's settings (unchanged from the prep; conservative).
8. The G.5 switch does not itself check the recount marker in `campaign_v2_diff.py`; the commit identity (filled
   `g5_commit`, STOP 13 checkout check) binds the reviewed recount code. A marker check could be added if wanted.
9. `test_t1_tasl_xc3.py::test_note_draft_renders_the_spec_and_passes_the_checks` fails on base and tip alike (§8).
10. This unit and the expansion unit share no files; whichever lands second re-runs the tests, and re-renders the §5
    block only if the spec or `note_lines` changed (the draft-render test enforces it).

## 11. Review round 1 (ACCEPTED at `a3523491`, eight minors, four nits): the fixes

On the same branch, new commits `f0e5f2c3` (code, spec, tests) and `e0ca7cff` (draft), then this report. Main is still
`f1f1b651`.

| finding | fix |
|---|---|
| m1 | `pilot_basis.sealed.<node>.out_tar_sha256` from result §7 (`5f9c2f2a9ceb52d3448f9e69023af47e3c5af300194de646350f8b09694df48a`, `5d0b48dd23ff66bdff0472d8d7c433b942d2e2bd142a40ee0b0e1b01b3fd1ed5`, `8661e5b8184b40ae1c1e7a18e9c39e6cb79657a9d7331f66b1d9f6e3a099a6ef`; each also in its node's captured `sealed_SHA256SUMS`); checked against the sealed `out.tar` at TASL-2 job starts and required in the result report's text; the member hash is kept. S3 (draft §11.1, §7 above): the TASL-2 `pilot-basis` PASS is recorded before the signature |
| m2 | `test_draft_section5_block_is_the_key_lines_render` extracts the fenced §5 block and asserts it equals the render (the `approved:` line excepted) |
| m3 | the draft (status entry of revision 10, §9 O1 item, §11 rows list) marks D7-DIFF B's O1 satisfied under (a) by the recount review (harness `docs/r1/reviews/G5_DIFF_RECOUNT_REVIEW_20261124.md` line 32 at `cbf7a003`; `audit_g5.py` lines 539–571) |
| m4 | `note_lines` `cap_gpu_hours`: "425, counted per the worker card (G5-TASL-GPUH A), the hours of G.5 audit chunks on TASL-7 included (R1-G5-AUDIT-TWO-CARDS)"; re-rendered; S1 keeps the options (B now also needs a `note_lines` change) |
| m5 | `pilot_basis_main_check` (result, corrigenda, review, note, dates row on `main`) runs at every job start on either host (`launch(..., pilot_main_check=)` at TASL-7); `pilot_basis_check` calls it and adds the seal re-read at TASL-2; new test `test_p3_main_half_runs_at_tasl7_job_starts` |
| m6 | the operational note (§2) and S3 say that the G.4b seals stay in place until G.5 is sealed; also the draft's P3 |
| m7 | `test_pilot_basis_cli_reads_main` uses a `Main` fake built from the checkout's files (and checks the refusal without the report) |
| m8 | merge-order wording (§10 item 10) |
| nits | draft §1 heading names `f1f1b651`; §11.1 intro lists the mechanical fills (`run_id`, `paper_commit`, `spec_sha256`, `noise_floor`/`tails`, `ar_prerequisites`); "from the committed result, its review and its committed captures"; `pilot_basis.review` binds `reviews/G4B_TASL_PILOT_RESULT_REVIEW_20261125.md` (`a04b490e445cce5b313e624a5c45656055ee9d39b15c5b5a3af4b42d3831f3ad`; on `main`, "Verdict: ACCEPTED", naming the report's sha256) |

Not fixed here, as instructed: `test_t1_tasl_xc3` (pre-existing on `main`).

**Spec sha256 after round 1: `b66ebb9427d260da7d41eacf6e327ff2095351fd5d16fe4ca980d98f5c9d7acf`.** The §5 block was
re-rendered: against the round-0 render only `cap_gpu_hours` and `spec_sha256` changed.

**Targeted tests at `e0ca7cff`:** `test_t1_g5_tasl` 190 passed (+4: three refusal cases, one test); `test_t1_g5_job`
52; `test_t1_g5_seal` 40; `test_t1_features` 30 + 1 skipped; `test_t1_tasl_g4` 47; `test_t1_tasl_g4b` 5;
`test_t1_tasl_crosscheck` 79; `test_t1_d7_diff_b` 19; `test_t1_tasl_xc3` 4 + 1 failed (pre-existing);
`test_t1_tasl_g5_ar_projection` 6.

ROUND1_SUITE_PLACEHOLDER
