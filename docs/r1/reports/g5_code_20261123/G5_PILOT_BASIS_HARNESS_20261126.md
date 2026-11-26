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

**Full suite at `2888e44d`** (clean tree; code `f0e5f2c3`), same command and environment, fresh `TMPDIR` (deleted),
started 02:47:49Z after `pgrep` found no other suite: 59 failed, **4174 passed** (+51 against the base `f1f1b651`:
the 50 new ids of `test_t1_g5_tasl.py` and 1 of `test_t1_g5_job.py`), 197 skipped, 3 errors, 53 subtests passed
(370.4 s). Its sorted FAILED/ERROR list (`FULLSUITE_PB2_TIP_R1_2888e44d_FAILED.txt`, 62 ids) is **identical** to the
base list `FULLSUITE_PB2_BASE_f1f1b651_FAILED.txt` (main has not moved, so the base was not re-run).

---

## 12. Revision 13 (26 Nov 2026): TASL-2 CPU sets under R1-TASL2-CPU, and the xc3 PASS read from `main`

On the same branch (READY 111 accepted, not merged), with new commits. ENGINEERING_ONLY desk work as above: no host,
no push, no label, evaluation value, sealed file, `*block.jsonl` or `*b1_manifests.json` opened; `gate.py`,
`gate_input_builder.py`, `release.py` and the preregistration unchanged; the draft stays `approved: false`.

| commit | what |
|---|---|
| `6ca4dfa8` | `git merge --no-ff origin/main` (`cdb8be91`, fetched): the four xc3 short verdicts and their memo (merge `64a3076d`), the TASL-2 CPU stability record (review ACCEPTED), R1-TASL2-CPU. No conflict |
| `e88ea3d3` | code, spec and tests (`g5_tasl.py`, `g5_job.py`, `g5_tasl_spec.json`, `test_t1_g5_tasl.py`, `test_t1_g5_job.py`) |
| `f0f230e2` | G.5 draft revision 13 |
| this commit and the next | this section, the two full-suite lists |

**Authority.** R1-TASL2-CPU (`main` `cdb8be91`): "From now on no R1 job on TASL-2 uses CPUs 8-11. A spec or job that
pins a CPU set containing any of them gets a replacement set of the same size that avoids 8-11 (the Mac proposes it in
the next spec or note; the coordinating chat publishes it with that unit), and that set passes a fixed-seed
determinism check before its first use. Sealed results that used CPUs 8-15 stand …". The stability record
`reports/tasl_chain_20261122/TASL2_CPU_STABILITY_20261125.md` (sha256 `9dca2cf3…`): 0-3, 4-7, 12-15 PASS 3/3 bitwise,
8-11 FAIL 3/3 (MetaMaze baseline, JAX, CPU). The xc3 memo `XC3_SHORT_RESULT_20261125.md`: four PASS.

**Spec sha256 after this unit: `16b39b475e5ccccd9143de06b0a69996e5274d73033521d5cac8c1db0470627f`** (was
`b66ebb94…`).

### 12.1 Every TASL-2 CPU set in the G.5 spec and code

| where | set | host | under the row? | change |
|---|---|---|---|---|
| `worker.cpus` (every GPU node's TASL-2 jobs; `host_worker`, the `cpus` query's fallback) | 0-7 | TASL-2 | yes, no 8-11 | none; the validator now refuses it if it contains 8-11 |
| `nodes[mlgym_houseprice].cpus` (its own set: before this unit the `cpus` query and `g5_job`'s affinity check used it on **both** hosts) | 8-15 | TASL-2 and TASL-7 | yes on TASL-2 | **replaced on TASL-2 by 0-7** (`tasl2_cpus.replacements`); the entry keeps 8-15 (the validator keeps every node field equal to the signed G.1b spec), which now applies on TASL-7 only |
| `tasl7_audits.cpus` | 0-7 | TASL-7 (AMD Ryzen 9 7900X, 24 CPUs) | no | none |
| other nodes' `cpus` | none (they take the host's set) | — | — | none |
| `t1_tasl_node.sh` (`CPUS=$(… cpus …)`, `taskset -c "$T1_CPUS"`) | no literal set; it asks the `cpus` query | — | — | none; the query now returns 0-7 for houseprice on TASL-2 and 8-15 on TASL-7 (test) |
| `logdir` query | no CPU set | — | — | none |
| the signed G.1b spec (`g1b_tasl_spec.json`: TASL-2 0-7, houseprice 8-15), G.4/G.4b specs (0-7) | — | — | sealed results stand | unchanged (not G.5's; the check's derived spec drops houseprice's 8-15, §12.3) |

The only set containing 8-11 was houseprice's 8 CPUs, as expected. Wrapper check: `g5_tasl.py cpus <spec> --node
mlgym_houseprice` prints `0-7` (default host TASL-2) and `8-15` with `--host TASL-7`; `mlab_imdb` prints `0-7` on both.

### 12.2 The replacement: `mlgym_houseprice` on TASL-2 cpus 0-7 (proposed)

- **Stability.** 0-7 are physical P-cores 0-3; both halves passed the stability record 3/3 bitwise (0-3, 4-7). Same
  core type as 8-15 (P-cores 4-7). 12-15 also passed; 16-31 (E-cores) were not checked and are slower.
- **Overlap with the G.5 worker's 0-7: none in effect.** Every G.5 job on TASL-2, the CPU-only houseprice's
  included, holds the TASL-2 lease `~/r1_locks/gpu0.lock` for its whole run (`g5_job.run_job` takes
  `G.gpu_lease(w["lease"])` unconditionally; read in the code, not a new rule), so houseprice never runs beside a GPU
  node's job in G.5. In G.1b it did (G.1b takes no lease for a CPU node), which is why it had a set of its own. With
  0-7, G.5 uses only 0-7 on TASL-2 and leaves 12-31 free.
- **Overlap with the expansion G.1b until 2 Dec.** Its amendment (branch `mac-g1b-expansion-20261126c`, not read: in
  progress) is expected to use MetaMaze 0-3, Titanic and Forest Cover on 4-7 and 12-15 (one each) and ETTh1 16-31,
  i.e. every TASL-2 CPU but 8-11. **No 8-CPU set avoids both 8-11 and the expansion's sets.** The options:
  (A) 0-7: overlaps MetaMaze and the node on 4-7, exactly the overlap the worker's 0-7 already has, so it adds none;
  (B) 4-7 + 12-15: P-cores, PASS, but overlaps both expansion nodes on 4-7 and 12-15; (C) 12-15 + 16-19: overlaps the
  node on 12-15 and ETTh1, and half of it is unchecked, slower E-cores; (D) 16-23: E-cores only, unchecked, overlaps
  ETTh1. **Proposed: (A).** The overlap until 2 Dec is then a schedule matter for the author or the coordinating chat:
  (i) G.5's TASL-2 jobs start after the expansion jobs on 0-3 and 4-7 end (2 Dec 00:00 CET at the latest;
  recommended), (ii) the G.5 operator holds the expansion's CPU-set leases (`~/r1_locks/cpus-0-3.lock`,
  `~/r1_locks/cpus-4-7.lock`, as named on `mac-g1b-expansion-20261126b`) for each G.5 TASL-2 job (enforcing it would
  be a G.5 code change), or (iii) accept the overlap (the expansion's preflight refuses its own parts while its set is
  busy; G.5 has no preflight, and a shared CPU can turn a run into a timing STOP). B, C, D or a schedule other than (i)
  is an author or chat decision (draft §2.14, §11.1 S13).
- **Timing basis.** houseprice's census (`TRACKG_U4_CENSUS_20261120.md`, Ada host, 8 CPUs): run 5.059 s, slowest
  6.794 s; so the engine's run timeout is 20.382 s (3 × slowest, R1-G1B-TIMEOUT), an audit chunk's budget 9.486 s a
  run (5.059 × 1.25 × 1.5, `g5_job.chunk_plan` and the chunk deadline), a campaign call (5.059 + 60) × 1.5 s. Measured:
  the sealed G.1b TASL-2 attempt on 8-15 (its `job_record.json` timing, as captured by xc3) c0 median 4.80–4.87 s per
  part, at most 5.895 s; the xc3 TASL-7 attempt on 8-15 median 4.524 s, at most 5.686 s. 8-11 boost to 6.1 GHz, 0-7
  and 12-15 to 5.8 GHz, so at most about 5 % slower is expected on 0-7 (about 6.2 s worst case), well inside 9.486 s
  and 20.382 s. The timeouts hold; the determinism check measures it (its PASS needs every run ≤ 9.486 s). E-core
  options would put this margin at risk (unmeasured).

### 12.3 The fixed-seed determinism check before first use

**Which check.** The stability record is set-level and used the MetaMaze baseline (JAX); houseprice is a torch CPU
workload. Under the row the conservative reading is node-specific, so the check is houseprice's own G.1b fixed-seed
determinism on the new set, compared bit for bit with its sealed G.1b TASL-2 attempt on 8-15 (the one the xc3 spec
declares: attempt 1, `job_record.json` `15b7beea61f7829d396a9aa0415462e80c3aabd6c62c9c3327b2528af2a690aa`,
`SHA256SUMS` `0109ecc2…`; its xc3 PASS against TASL-7 is on `main`). The stability record is bound in the spec as the
evidence for choosing 0-7, not as the check.

**Built (small, reusing reviewed pieces).**
- `g5_tasl.py cpuset-spec <spec> --node <n> --run-id tasl2-cpuset-<n>-<YYYYMMDD> --out <file>` (`cpuset_spec`): the
  signed G.1b spec (sha256 checked against `harness_families.G5-7.g1b_spec`) with the run id and the node on its
  replacement set (where that is TASL-2's GPU set 0-7 its own `cpus` is dropped, because G.1b refuses a CPU-only set
  overlapping the GPU jobs'), plus an inert `cpuset_check` block; `g1b_tasl.validate_spec(launch=True)` passes; the
  node's affinity under it is 0-7. Only `run_id`, the node's `cpus` and `cpuset_check` differ from the signed spec
  (test). Written once.
- `g5_tasl.py cpuset-verdict <spec> --node <n> --check-spec <file> --reference <dir> --attempt <dir> …`
  (`cpuset_verdict`): requires the check spec byte-identical to `cpuset_spec`'s; reads the reference and the attempts
  with `g1b_crosscheck._sealed_rows` (receipt, sums, record bound; row gate); the reference must be the declared
  attempt; each attempt the check run, its spec sha256, the pin `c025f89a`, host TASL-2, no STOP. Per attempt it
  records affinity, completeness (c0..c4 × default, default_repeat), `g1b_lib.determinism_check`, identity of every
  `g1b_lib._outcome` with the reference, and the slowest run against the budget; no metric value. PASS needs ≥ 3
  distinct attempts, all true.
- The gate `check_cpuset_record` (switch, every TASL-2 job start of a node with a replacement): exactly one
  `docs/r1/reports/<dir>/G5_TASL2_CPUSET_CHECK_<node>_<YYYYMMDD>.json` on `main` (captures ignored; another depth, a
  near-miss or two files refused) that is a PASS for this node, TASL-2, this set and the G.1b set it replaces, the
  G5-7 pin, run and spec, the declared reference, the budget, ≥ 3 distinct attempts each with affinity equal to the
  set and every flag true; otherwise that job is refused (a refusal, not a node STOP). Other nodes, and houseprice's
  TASL-7 chunks, do not need it. The launch also needs R1-TASL2-CPU on `main` with the terms "no R1 job on TASL-2
  uses CPUs 8-11" and "passes a fixed-seed determinism check before its first use" (`plan_row`, added to the rows the
  launch binding checks).

**The key line** (rendered from the spec; signed verbatim; `check_note` enforces it):

```
tasl2_cpuset_check: mlgym_houseprice on cpus 0-7: before its first TASL-2 job the switch requires the one record docs/r1/reports/DIR/G5_TASL2_CPUSET_CHECK_mlgym_houseprice_YYYYMMDD.json on main (g5_tasl2_cpuset_check/1, written by g5_tasl.py cpuset-verdict); procedure: on TASL-2, 3 sealed attempts of the node's G.1b default part (c0..cN, default and default_repeat, the G.1b seeds) under the derived spec of g5_tasl.py cpuset-spec (run tasl2-cpuset-mlgym_houseprice-YYYYMMDD), each by sweep2/t1_tasl/dry_run_node.py in the delegated 8G scope pinned to cpus 0-7, the TASL-2 lease held; PASS: every attempt complete and deterministic with affinity 0-7, every outcome bit-identical to the sealed G.1b TASL-2 attempt 1 (job_record sha256 15b7beea61f7829d396a9aa0415462e80c3aabd6c62c9c3327b2528af2a690aa), and every run within 9.486 s (census run time x 1.25 x 1.5); otherwise the node's TASL-2 jobs are refused and the author decides
```

and beside it `tasl2_cpus: R1-TASL2-CPU: no G.5 job on TASL-2 uses CPUs 8-11 (stability record … sha256 9dca2cf3…);
GPU jobs on cpus 0-7; mlgym_houseprice on cpus 0-7 in place of its G.1b set 8-15 (same size; its TASL-7 audit chunks
keep 8-15); every G.5 job on TASL-2 holds the TASL-2 lease, so jobs sharing CPUs never overlap`.

**The procedure for the experiment agent** (TASL-2, after this unit is on `main`; a published checkout with fresh
`origin/main`; no GPU; about 3 × 10 runs of ~5 s plus setup). ENGINEERING_ONLY: no G.1b row, no label.

```
cd <published Agent_paper_B checkout on TASL-2> && git fetch origin
D=$(date -u +%Y%m%d); RUN=tasl2-cpuset-mlgym_houseprice-$D
ROOT=/home/dowling/r1_tracks/t1_tasl/runs/$RUN; SPEC=$ROOT/_specs/mlgym_houseprice.json
mkdir -p "$ROOT/_specs" "$ROOT/_logs"
python3 sweep2/t1_tasl/g5_tasl.py cpuset-spec sweep2/t1_tasl/g5_tasl_spec.json --node mlgym_houseprice \
  --run-id "$RUN" --out "$SPEC"
# no G.5 job and no expansion job on 0-7 meanwhile: hold the TASL-2 lease and the expansion's CPU-set leases of
# 0-3 and 4-7 (non-blocking; if any is busy, wait and retry; do not break a lease)
exec 7>>~/r1_locks/gpu0.lock 8>>~/r1_locks/cpus-0-3.lock 9>>~/r1_locks/cpus-4-7.lock
flock -n 7 && flock -n 8 && flock -n 9 || { echo "a lease is busy: wait"; exit 1; }
for i in 1 2 3; do
  LOG=$ROOT/_logs/mlgym_houseprice-$(date -u +%Y%m%dT%H%M%SZ)-$$.node.log
  systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- env T1_LOG="$LOG" bash -c '
    CG=$(sed -n "s/^0:://p" /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
    export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" G1B_TASL_NODE_LOG="$T1_LOG"
    unset NVIDIA_VISIBLE_DEVICES _CONDOR_AssignedGPUs
    taskset -c 0-7 python3 sweep2/t1_tasl/dry_run_node.py "$0" mlgym_houseprice' "$SPEC" >> "$LOG" 2>&1
  python3 sweep2/t1_tasl/g1b_tasl.py seal "$ROOT/mlgym_houseprice/attempt-$i" "$SPEC" --node mlgym_houseprice
done
SEALED=/home/dowling/r1_tracks/t1_tasl/sealed_g1b
python3 sweep2/t1_tasl/g5_tasl.py cpuset-verdict sweep2/t1_tasl/g5_tasl_spec.json --node mlgym_houseprice \
  --check-spec "$SPEC" --reference "$SEALED/g1b-tasl-20261121-b/mlgym_houseprice/attempt-1" \
  --attempt "$SEALED/$RUN/mlgym_houseprice/attempt-1" --attempt "$SEALED/$RUN/mlgym_houseprice/attempt-2" \
  --attempt "$SEALED/$RUN/mlgym_houseprice/attempt-3" > "G5_TASL2_CPUSET_CHECK_mlgym_houseprice_$D.json"
```

Notes for the agent: the loop's attempt numbers assume no attempt failed (a preflight refusal goes to `_refusals/`
and uses up no attempt; seal the attempts that exist and pass their directories); `dry_run_node.py` runs the pinned
`run_node_job` (preflight, host checks, harness `c025f89a` clean, `torch312` freeze, data manifest, row gate,
timing check) on the default part only; G.1b takes no lease for a CPU node, hence the explicit `flock`. **PASS
criterion:** the verdict JSON reads `"verdict": "PASS"`, `"reason": null` (a STOP names `too_few_attempts`,
`affinity`, `incomplete`, `nondeterministic`, `reference_mismatch` or `too_slow`; on STOP the set is not used and the
author decides). Commit the record as `docs/r1/reports/tasl_chain_20261122/G5_TASL2_CPUSET_CHECK_mlgym_houseprice_<D>.json`
with captures (the derived spec, the three sealed attempts' `job_record.json`, `SHA256SUMS`, `SEAL_RECEIPT.json` and
node logs, `lscpu`, the lease state) under a `…_captures/` directory, for independent review; the coordinating chat
publishes it. The switch does not read a review file for it (as for the xc3 verdicts); the review is the
publication step.

### 12.4 The validation rule (tests)

`_check_tasl2_cpus` (called by `validate_spec`): the `tasl2_cpus` block must be exactly `{authority: R1-TASL2-CPU,
excluded: 8-11, stability_record {path, sha256 = the checkout file's}, replacements}`; `worker.cpus` without 8-11;
`replacements` names exactly the nodes whose own set contains any of 8-11, each `{g1b_cpus: <the node's set>, cpus}`
of the same size, without 8-11 and within 0-31; and each replaced node has a declared reference attempt. Refused in
`test_tasl2_cpu_set_containing_8_11_is_refused` (16 cases): worker 0-11 and 4-9; replacement 8-15, 4-11 and
0-3,10,12-14; wrong size (12-15); beyond 31; not a list; wrong `g1b_cpus`; missing or extra replacement; wrong
authority or excluded; a stability record with another sha256; the block or its record missing.

### 12.5 The xc3 PASS on `main` (`cdb8be91`), read by the switch

Run against the real published `main` (`git show origin/main:…`, `ls-tree`), before and after the spec change:

| node | `check_crosshost_pass` | `g5_job.tasl7_eligible` |
|---|---|---|
| `mlab_cifar10`, `mlgym_cifar10`, `mlgym_breakout_minatar` | PASS (source `spec`: xc2 step-1 `xc` and step-2 `preassembly`) | eligible |
| `mlab_imdb` | PASS (`G1B_XC3_SHORT_VERDICT_mlab_imdb_20261125.json`, `9cce9064…`, short, run `g1b-tasl-20261121-b-xc3-a`) | eligible |
| `mlab_ogbn_arxiv` | PASS (`…_mlab_ogbn_arxiv_20261125.json`, `b42e485c…`) | eligible |
| `mlgym_fmnist` | PASS (`…_mlgym_fmnist_20261125.json`, `cb2ac690…`) | eligible |
| `mlgym_houseprice` | PASS (`…_mlgym_houseprice_20261125.json`, `6c7da440…`) | eligible |
| `autoresearch_fixedtokens` | refused: "audits stay on TASL-2 (… ar-cond7a exists only there …)" | not eligible |

XC3-FAIL read on `main`: A, from the signed note `authorizations/g1b_xc_short_t1_tasl_20261126.md` and the row (they
agree), `skip_nodes` none, xc3 run `g1b-tasl-20261121-b-xc3-a` (the note binds the xc3 spec on `main`). Before the
change the four were found by file pattern (source `main`); after it, by the listed record (source `spec`) with the
same reading. New test `test_xc3_pass_on_published_main_makes_all_seven_eligible` repeats this on the real
`origin/main` (skips where it is not readable).

**Placeholder removed: the spec now lists the four verdicts** (each `{record, sha256, mode: short,
crosscheck_run_id: g1b-tasl-20261121-b-xc3-a}`), so `PENDING short cross-check` no longer appears in the spec or the
note (the draft's revision-12 PENDING table had foreseen this). Reasons: the PASS exists, so the marker would be
signed into `tasl7_audits` as "PENDING" though it is not; the spec's sha256 (bound by the note) then binds the verdict
bytes; all seven nodes are bound the same way. Nothing the main-reading path checked is dropped: for a listed short
record the switch still reads XC3-FAIL (note and row, agreement), `skip_nodes`, requires the xc3 run id on `main` to
equal the listed one, and requires the listed file to be the node's only short verdict on `main`; `short_nodes` counts
listed short nodes too, so XC3-FAIL B's `xc3_b_check` and the xc3 note's `skip_nodes` rule cover the same four nodes.
The validator requires the listed record's exact shape (one record, mode short, the node's verdict name, the checkout
xc3 spec's run id, the checkout file's sha256; seven refusal cases). The marker stays accepted (tests run the marker
path on a spec with the marker restored).

### 12.6 The dates tool and the recompute (reported, not applied)

`default_tasl7_nodes` now goes over all seven G5-7 nodes with `list_main` (the `dates` CLI passes it) and keeps those
whose PASS `check_crosshost_pass` finds on `main`; on `main` `cdb8be91` that is all seven (source text "default: the
G5-7 nodes with a cross-host PASS on origin/main"). Desk recompute (R1-BX-D14-G4B; the captured G.4b summaries through
the same functions, as in §5.1), each node reported "cross-host PASS on main":

| `--today` | nodes on TASL-7 | claimable TASL-7 GPU-h | label span (h) | labels done | B.7 | D.3 | manuscript | slack |
|---|---|---|---|---|---|---|---|---|
| 2026-11-25 | default: all seven (eligible on `main`) | 0.0 | 216.9 | 2026-12-11 | 2026-12-14 | 2027-01-09 | 2027-01-16 | −6 |
| 2026-11-26 | default: all seven | 0.0 | 216.9 | 2026-12-12 | 2026-12-15 | 2027-01-10 | 2027-01-17 | −7 |

Same as the revision-12 scenario: no G5-7 wave has three or more chunks (wave chunk runs unchanged from §5.1), so no
chunk can move; campaign hours with startup 31.54; the binding work is autoresearch's 138.69 GPU-h. GPU-hours 216.9
of 425. Not applied (no spec date changed).

### 12.7 Draft revision 13

`docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` (`approved: false`): status line and a revision-13 entry;
recorded decisions add R1-TASL2-CPU; §1 names `main` `cdb8be91` and adds the row R1-TASL2-CPU; §2.10 says the four
xc3 verdicts are on `main` and listed (the "no short verdict is on `main` yet" and "named explicitly, as a scenario"
texts are corrected) and gives the seven-node recompute; new §2.14 (the CPU sets, the proposal and its justification,
the expansion overlap and its options, the timing basis, the check's procedure); §5 re-rendered (`tasl7_audits`,
`spec_sha256` changed; `tasl2_cpus`, `tasl2_cpuset_check` new; 56 lines after `approved`) with a revision-13 render
note; the PENDING table's `tasl7_audits` and `spec_sha256` rows; §11 item 23 and the post-signature record; §11.1 rows
S13 (the set and the schedule) and S14 (the check).

### 12.8 Tests

Targeted, one file at a time, at `f0f230e2`: `test_t1_g5_tasl` **221 passed** (+31 ids: 9 for the xc3 records, i.e. the
real-`main` eligibility test, the TASL-7 launch on a listed record and the 7-case listed-record shape; 22 for the CPU
sets, i.e. the 16-case validation rule, the shipped sets and key lines, the per-host `cpus` query and affinity, the
record gate with 20 tampered fields, the row requirement, `cpuset-spec`, and `cpuset-verdict` with six STOP reasons; changed: the two-cards block test, four marker tests on a marker spec, the dates default test);
`test_t1_g5_job` 52 passed (the fake main holds the real `mlab_imdb` verdict; the marker path checked on a marker
spec); `test_t1_g5_seal` 40; `test_t1_features` 30 + 1 skipped; `test_t1_tasl_g4` 47; `test_t1_tasl_g4b` 5;
`test_t1_tasl_crosscheck` 79; `test_t1_d7_diff_b` 19. Also `test_t1_tasl_xc3` 4 + 1 failed (pre-existing on `main`,
not touched) and `test_t1_tasl_g5_ar_projection` 6.

### 12.9 Full suite

`/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider -rfE r1/tests`, default options, lightgbm off (not
installed), `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, a fresh `TMPDIR` per run (deleted after), each started only when
`pgrep -f "[p]ytest.*r1/tests"` found nothing (the tip waited twice for the expansion amendment's suites).

| run | checkout | result | list beside this report |
|---|---|---|---|
| base | clean detached `cdb8be91` (a worktree under `/tmp/g5pb2dev/base`, removed afterwards), started 07:29:53Z | 59 failed, 4123 passed, 197 skipped, 3 errors, 53 subtests passed (353.1 s) | `FULLSUITE_PB2_BASE_cdb8be91_FAILED.txt` (62 ids) |
| tip | this branch at `ef41890a` (clean tree; code `e88ea3d3`, draft `f0f230e2`), started 07:48:22Z | 59 failed, **4205 passed** (+82: READY 111's 51 ids not yet on `main` and this unit's 31 of `test_t1_g5_tasl.py`), 197 skipped, 3 errors, 53 subtests passed (354.6 s) | `FULLSUITE_PB2_TIP_R13_ef41890a_FAILED.txt` (62 ids) |

The two sorted FAILED/ERROR node-id lists (each line's ` - message` cut) are **identical** (`diff` empty), and equal
to the `f1f1b651` base list of §9. The only T1 id in them is the pre-existing
`test_t1_tasl_xc3.py::test_note_draft_renders_the_spec_and_passes_the_checks`. The commit that fills this section
changes no code or test.

### 12.10 Open points for the reviewer

1. **The schedule against the expansion G.1b until 2 Dec** (§12.2): not decided here; (i) recommended. The lease file
   names of the expansion's CPU-set leases are those of `mac-g1b-expansion-20261126b`; the `c` amendment may rename
   them.
2. **houseprice's set on TASL-7 stays 8-15** (TASL-7 is not under the row; xc3 ran it there on 8-15 and matched
   TASL-2 bit for bit). Changing it would need a TASL-7 field; not proposed.
3. **The record gate trusts the committed record's flags**, as the xc3 verdict gate does; `cpuset-verdict` (reviewed
   code) computes them from the sealed attempts, and the record's review is the publication step, not a code check.
4. **The check's reference** is the attempt the xc3 spec declares (`cpuset_reference`); a replaced node outside the xc3
   spec is refused by the validator until a reference is declared.
5. `_bound_file` gained a `where` argument (message prefix only; P3's messages unchanged).
