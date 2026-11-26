# G.5 — T1 label runs on the TASL pair (RTX 4090): authorization draft (approved: false)

**Status: DRAFT for the author's signature. `approved: false`. Not runnable.**
- This document authorizes nothing until the author signs a final version and the coordinating chat publishes it
  to `main` as `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md`, with every prerequisite in §7 recorded as PASS
  (under G5-ARPEND A, §2.13, autoresearch's own prerequisites may be PENDING at signature and gate only its jobs).
- The G.5 job code is built and independently reviewed, and is on published `main`: part 3a (spec, validator,
  switch), part 3b-1 (job, audit planning, diagnostics, STOP counters) and part 3b-2 (seal, locked assembly, release
  locks, REL-T1-G1B copy step), merged as `619cb0d4` (READY 91, from `mac-g5-code-main-20261123`, code base
  `2582c898`; review `docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`). The ARMS-T1FEAT unit (READY 92, merge
  `2798e1aa`), the G.5 follow-ups (READY 96, merge `1c961117`) and the R1-T1-FEAT-DECISIONS unit (READY 97, merge
  `44c3d80e`) are on `main` too (§9). *(Revision 12:)* so are the A5 T1 prompt (READY 100, merge `467224d4`),
  D7-DIFF B (READY 103: the table carries each step's own proposal diff, schema `g5_t1_table/2`; merge `b6d774b4`),
  READY 104 (merge `139a2870`), revision 11's D21-scope and two-cards code (READY 108, merge `03c0d842`) and the xc3
  short cross-check unit (READY 107, merge `90964673`). The recount harness unit of R1-G5-DIFF-RECOUNT exists and is
  reviewed; its tips G5-7 `cbf7a003` and G5-AR `ccdb3774` (on the reviewed engines `52e3c0b0` and `00829da1`) are the
  spec's G.5 harness commits since revision 12 (§2.12, §5, §9). This revision's own code (the G.4b pilot basis, the
  harness-commit fill, the imported xc3 rules, the CUDA-IPC extension and the TASL-7 dates) is on branch
  `mac-g5-pilot-basis-g4b-20261126`, **not on `main`**, under independent review.
- Written by the Mac-desk agent (Claude), AI-assisted.
  - Revisions 1–5 (H200) passed rounds 1–5 of the independent review (`reviews/T1_G5_DRAFT_REVIEW_20261121.md`).
  - Revision 6 re-targeted the draft from NEMO2 H200 to the TASL pair under R1-T1-HOST-TASL (worker on TASL-2,
    proposer `llama-server` on TASL-7 over Tailscale, one GPU model: RTX 4090) and added G5-TASL-GPUH and G5-SLOT. It
    was reviewed with the T1 TASL code unit (`reviews/T1_TASL_REVIEW_20261121.md`).
  - Revision 7 (22 Nov) moved the authority to published `main` `9c2979a2`, after the signed G.4 note. It cited the
    rows published since revision 6, fixed G5-SPLIT through the frozen preregistration, added G5-AR and G5-PIN,
    recomputed the projection and dates as of 22 Nov, filled the known key values, and named the TASL launch binding.
    Reviewed in round 1 of `reviews/T1_G5_DRAFT_TASL_REVIEW_20261122.md` (not accepted, M1–M3 and m1–m12).
  - Revision 8 (22 Nov) moved the authority to published `main` `3c3f822a` and applied R1-G5-DECISIONS (G5-AR A,
    G5-PIN B: eight nodes, K = 10 until a K-check row, the cap 425 GPU-h, `g5_pin_check.py`) and the revision-7 review
    (PRE-T1 A quoted, gate v3.1 and the release rows cited, the freeze wait with STOP 14). Rounds 2 and 3 added
    G5-ARPEND (§2.13) with the completion record, and the K amendment and autoresearch's items without a spec change.
    Round 4 of the same review accepted it at `fc018bf8`.
  - **Revision 9 (23 Nov), text only**, against published `main` `89899f76` and the G.5 code on
    `mac-g5-code-main-20261123` @ `2582c898` (merged into this branch). No projection or date is recomputed; no code
    changes in this unit. (`main` moved from `000ac3b1` during this revision by the T0 arms-readiness merge `630398c6`
    and the author rows `89899f76`; the code branch merged it at `ecfd86a5` and then fixed the switch's G5-MEM A row
    check at `baf6be5d`, refactored into `g5_tasl.decision_row_checks` at `2582c898` with the same terms; `key-lines`
    prints the same block at `30e2d51a`, `baf6be5d` and `2582c898`.)
    - Autoresearch's TASL-2 host check at harness `2d09f9a9` is PASS (binding record
      `reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md`, sha256 `cce9b8fb…`, after
      R1-G1B-AR-PY), and the third G.1b note is signed (`authorizations/g1b_ar_t1_tasl_20261122.md`) (§1, §2.11,
      §2.13, P1, P2, P9).
    - R1-G1B-JOIN is on `main` (§1, §3, P2, §11).
    - The TASL launch chain is published: (a)–(c) by merge `38ae4a05`, (d) by merge `5d5ca7b4`, with the launch table
      and the publication record (§1, §3).
    - The G.4 note cited is the re-issued `authorizations/g4_t1_tasl_20261123.md` (paper commit `b5824240`), which
      supersedes `g4_t1_tasl_20261122.md` (§1, P3).
    - The §5 block is the block `sweep2/t1_tasl/g5_tasl.py key-lines` prints for the spec on the code branch: it adds
      the lines of part 3a (`invalid_share_stop`, `infrastructure_stop`, `seal`, `decisions`, `e4_amendment_row`,
      `cuda_ipc_acceptance`), the freeze-wait clause "no G.5 job starts on or after this date", and the lines
      `t1_table_readings` and `server_log` of part 3b-2. The five readings proposed in part 3b-1's report §7 are
      listed beside it; the code does not render or check them (§5).
    - §6 follows the built seal, assembly and release locks; §9 says what is built and what remains; §4, §7, §8, §10
      and §11 follow.
    - The author rows R1-G5-DECISIONS-2, R1-G5-MEM-E4 and R1-ARMS-DECISIONS (`main` `89899f76`) are applied (§1, §2,
      §5, §6, P6, §11): the eight §11 decisions are signed, all as recommended (option A); items 9–19 are fixed at the
      note's signature. The switch's row check (`g5_tasl.decision_row_checks`; fixed at `baf6be5d`, accepted by the G.5-on-main review (`docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`, READY 91 @ `deb888cc`))
      checks the decisions row for the eight options and, under G5-MEM A, the E4 row's id, and the
      E4 row for "E4" and "memory modes"; both rows pass against `main` `89899f76`'s PLAN (§2.3, §5, §11).
  - **Revision 10 (24 Nov), text only**, against published `main` `44c3d80e`, which carries the author rows
    R1-T1-FEAT-DECISIONS (23 Nov (e), with its reading of PRE-DELTA for T1) and R1-T1-A5-DECISIONS (23 Nov (f)) and
    the code of READY 97; in its phase 2, rebased onto the D7-DIFF B tip `c2804f58` (which contains `main`
    `3024db3f`). No projection or date is recomputed; no code or spec changes in this unit. Change report:
    `reports/g5_code_20261123/G5_DRAFT_REV10_20261124.md`.
    - T1's σ̂_node is T0's definition (the median `sd_joint` over material edits) and δ_n is D18, both computed from
      the G.1b `runs.jsonl` copy bound by sha256 to each summary copy (D6-σ B, D6 A; the PRE-DELTA reading); the
      summary's `sigma_joint` is no longer used for σ̂_node and is only reported (§3, §5, §6).
    - The REL-T1-G1B copy step also copies each G.1b run's `ASSEMBLY.json` and `runs.jsonl` beside the summary copy;
      the spec's `noise_floor.seven` gains four fields for them and `noise_floor.t1_sigma_node` (§3, §5).
    - The switch requires R1-T1-FEAT-DECISIONS on `main` and runs a noise pre-check after STOP 5 (§4, §11); the
      assembly STOPs on a non-zero `raw_state_missing` or `flag_mismatch` count (D9 B, §6).
    - D7 is decided by R1-T1-A5-DECISIONS (D7-DIFF B with fallback A). Its code (READY 100 and D7-DIFF B, READY 103)
      is accepted on `mac-d7-diff-b-20261124` @ `c2804f58` and is not on `main` (§6, §9, §11). The history-drop
      report (D7-DIFF B report §9) is a post-release cluster step (§6, §11).
    - **The §5 block is re-rendered** with `key-lines` on this branch rebased onto `c2804f58` (phase 2 of this
      revision). D7-DIFF B changes neither the spec nor `g5_tasl.py`, so the block is byte-identical to the render on
      `44c3d80e`: against revision 9 only `t1_table_readings` (D6-σ B) and `spec_sha256` (READY 97's spec fields)
      changed (§5).
    - **The G.5 launch requires the recount harness commits** (R1-G5-DIFF-RECOUNT). D7-DIFF B's O1 bears on that
      unit (O1 open; (a) recommended): the table's claim holds only if the recount unit keeps `proposal.diff` as the
      manager's text, and the audit's re-materialisation must use the same recount rule (§9). The spec binds the G.5 harness commits only in `harness_families.<family>.g5_commit`, still PENDING; the
      `harness_commit` line and `spec_sha256` are rendered once more after that fill (§5).
    - The `campaign_attribution` line of the harness engines report §7 item 6 (READY 96, quoted in the follow-ups
      report §4) is added for the author's signature beside the block (§5, §11 item 19); P5 cites the follow-ups
      review and the D7-DIFF B review.
    - `main` moved from `44c3d80e` to `3024db3f` meanwhile. Revision 10 takes from it only what bears on the points
      above, R1-G5-DIFF-RECOUNT (§1, §9), and corrects P2's state (note 2 signed, the `-xc2` step-1 verdicts PASS);
      the other consequences of R1-G5-DIFF-RECOUNT (the G.4b re-pilot behind P3 and the dates) are noted, not worked
      in (change report §7.5).
  - **Revision 11 (25 Nov), code and text**, on branch `mac-g5-scope-twocards-20261125` (from READY 104), with
    published `main` merged in twice: `5d4f1b09` (the two author rows below) and then `912a7e02`, which carries READY
    100, 103 and 104 (merges `467224d4`, `b6d774b4`, `139a2870`) and the signed G.4b note. It works in the two author
    rows; change report `reports/g5_code_20261123/G5_SCOPE_TWOCARDS_20261125.md`. Texts of revision 10 that say
    READY 100, 103 or 104 are not on `main` (the opening paragraph, §6 step 2, §9, §11) are now stale; they are left
    for the next revision, with the recount fill.
    - **R1-T1-D21-SCOPE.** D21 does not select T1 nodes for C3: every T1 node that passed U2, G.1b fixed-seed
      determinism and, where run, the cross-host check enters G.5 whatever its D21 value. STOP 5 is now fixed-seed
      determinism; a node that does not qualify under D21 is recorded (its D21 value in the launch context, in
      `build.json` and in the T1 noise record) for the screening funnel (R1-BX-D12), not STOPped. The G.1b cross-host
      gate and the σ̂_node/δ_n usability STOP stay (§3, §4 item 5, §6, P2, P10, §11).
    - **R1-G5-AUDIT-TWO-CARDS** (amends G5-SLOT A). Campaign waves keep one worker slot on TASL-2 with the server on
      TASL-7; audit chunks may also run on TASL-7's RTX 4090 while no campaign wave holds the server, claimed and
      registered on TASL-2, under TASL-7's GPU lease (the server's), for the G5-7 family only, after the node's
      cross-host PASS: the `-xc2` step-1 and step-2 verdicts for the three TASL-7 nodes; for the other four, a short
      cross-check (a separate unit, PENDING here) (§2.10, §4, §5, P1, §10, §11).
    - The spec changed (`tasl7_audits`, `slots.worker_host`, `slots.audit_hosts`) and `note_lines` changed, so **the §5
      block is re-rendered**: `hosts`, `gpu_model`, `job_layout` and `spec_sha256` changed, `tasl7_audits` and
      `t1_node_scope` are new; the harness commits stay PENDING (§5).
    - Not worked in: the recount harness unit is now reviewed (G5-7 `cbf7a003`, G5-AR `ccdb3774`, READY 105, as the
      coordinator cites them), but `harness_families.<family>.g5_commit` stays PENDING for the later fill, and the
      texts of §9 and §11 that say the unit does not exist yet are left for that fill's revision. Revision 11's code
      is on this branch only, not on `main`; the opening paragraph's "on published `main` (revision 10)" is about the
      code before this revision.
    - Review rounds 1 and 2 changed code and text within revision 11 (change report §9); round 2 added the switch's
      B STOP record `_switch_stop.json` (§2.10, §4 "After a node STOP"), the registration's comparison with the
      claim (§4 step 4), the TASL-7 refusal of an abandoned claim (§4 step 5), and the xc3 key-line rules copied from
      the xc3 branch (§2.10). The §5 block did not change in round 2.
  - **Revision 12 (26 Nov), code and text**, on branch `mac-g5-pilot-basis-g4b-20261126` from published `main`
    `f1f1b651`, which carries READY 107, 108 and 109, the G.4b result with its corrigenda, and the author rows of
    26 Nov (R1-BX-D14-G4B, R1-XC3-FAIL-READING, R1-XC3-NOTE, R1-P4-PROBE-CHARGE, R1-G5-EXPANSION-JOIN) with the signed
    xc3 note. Change report: `reports/g5_code_20261123/G5_PILOT_BASIS_HARNESS_20261126.md`. It ports what was still
    right of the unreviewed preparation `mac-g5-pilot-basis-g4b-20261125` @ `a9c23230` (not merged).
    - **P3 reads the G.4b re-pilot** (R1-G5-DIFF-RECOUNT): the spec's `pilot_basis` binds the G.4b spec, the signed
      G.4b note, the result report and its corrigenda by path and sha256, each node's sealed attempt, the measured
      liveness, the dates row R1-BX-D14-G4B and the eight-node recompute of G4B-DATES A (216.9 GPU-h; labels done
      11 Dec, B.7 14 Dec 2026, D.3 9 Jan, manuscript 16 Jan 2027), all filled from the committed result; P7 = 216.9
      (P3, P7, §1, §2.1–§2.4, §2.8, §2.10, §2.11, §8, C8, §11).
    - **The recount harness commits are filled** (G5-7 `cbf7a003`, G5-AR `ccdb3774`); `g5_pin_check`,
      `measurement_path_check` and the engine contract pass on them at the desk (§2.12, §9, P5).
    - **XC3-FAIL A is signed** (R1-XC3-NOTE, R1-XC3-FAIL-READING): the "open" wording is removed; the switch's
      reading on `main` is A with `skip_nodes` none, and its rules are now imported from READY 107's
      `g1b_crosscheck.py` rather than copied (§2.10, §11).
    - **CUDA IPC on TASL-7:** the acceptance line names TASL-7's audit chunks, and under C12 a TASL-7 audit chunk needs
      TASL-7's own C12 record (P1, §5, §10 C12).
    - **The dates tool counts TASL-7 audit chunks** (`dates --tasl7-audits`): the recompute R1-BX-D14-G4B asks for; it
      changes no date for the eight nodes (§2.10, §8).
    - **The expansion nodes** join through an addendum note (R1-G5-EXPANSION-JOIN; §2.11, §11).
    - The §5 block is rendered again: `harness_commit`, `gpu_hours`, `cuda_ipc`, `cuda_ipc_acceptance` and
      `spec_sha256` changed. Stale revision-10 and revision-11 text about what is not on `main` is corrected.
    - A new list of what the author still signs in the G.5 note is §11.1.
- Values marked *(proposed)* are recommendations, not decisions. Recorded decisions: G5-AR A and G5-PIN B
  (R1-G5-DECISIONS); G5-W, G5-TEMP, G5-MEM, G5-AUDIT, G5-DIV, G5-TASL-GPUH, G5-SLOT and G5-ARPEND, each A
  (R1-G5-DECISIONS-2), with E4 amended for T1 (R1-G5-MEM-E4); G5-SPLIT is fixed by the preregistration; the
  ARMS-T1FEAT decisions D1–D4, D6, D6-σ, D8 and D9 (R1-T1-FEAT-DECISIONS) and D7 (R1-T1-A5-DECISIONS); the T1 node
  scope (R1-T1-D21-SCOPE) and the TASL-7 audit chunks amending G5-SLOT A (R1-G5-AUDIT-TWO-CARDS). The values of
  §11 items 9–19 are fixed at the note's signature. §2.8 and §2.11 show the options together.

## 1. Authority (published `main` `44c3d80e`)

*(Revision 12:)* published `main` is now `f1f1b651`. Its author rows of 26 Nov that bear on this note are listed at
the end of the table (R1-BX-D14-G4B, R1-XC3-FAIL-READING, R1-XC3-NOTE, R1-G5-EXPANSION-JOIN); R1-P4-PROBE-CHARGE
concerns Track P only.

*(Revision 11:)* published `main` was then `912a7e02`; `5d4f1b09` added, among others, R1-T1-D21-SCOPE and
R1-G5-AUDIT-TWO-CARDS, which revision 11 works in (listed before R1-G5-DIFF-RECOUNT below), and R1-T1-NODE-EXPANSION
and R1-A5-FOLDS-PARALLEL, which do not change the code of this unit (a candidate that enters G.5 under
R1-T1-NODE-EXPANSION needs its own spec entry and a code change; change report §7).

Every row below up to R1-T1-A5-DECISIONS is on published `main` `44c3d80e`. All of them but those two were already on
`main` `89899f76`, the authority of revision 9; revision 10 adds R1-T1-FEAT-DECISIONS and R1-T1-A5-DECISIONS and
changes no other row's cell except where it says so. `main` `3024db3f` still carries every row below and adds, among
others, R1-G5-DIFF-RECOUNT (24 Nov), listed last; its other rows since `44c3d80e` (R1-POSTFREEZE-READS-CHOICES,
R1-TRACKP-P4-RUNNER-DECISIONS) do not bear on the points revision 10 changes. The two rows of revision 11 (on
`5d4f1b09`) are listed just before R1-G5-DIFF-RECOUNT.

| Row | What it fixes here |
|---|---|
| R1-T1-HOST-TASL (21 Nov; amends the Ada fallback of R1-T1-HOST-H200) | The isolation fails in the HTCondor container on H200 (job 759828) and Ada is occupied, so the T1 table (G.1b, G.4, G.5) runs on the two RTX 4090 hosts: worker (training) on TASL-2 under the harness isolation; the proposer `llama-server` (gemma4_31b, exam settings: context 32,768, `-ngl 999 -np 1 --jinja`, q8_0 KV, `cache_prompt` false, `{"enable_thinking":false}`) on TASL-7 over Tailscale. G.1b may use both hosts' GPUs. One GPU model (RTX 4090) for the whole table. Precondition: the host checks pass on TASL-2 (and on TASL-7 if it runs workers); otherwise STOP. |
| R1-TRACKG-AR-U2-TASL2 (21 Nov) | `autoresearch_fixedtokens`' cond7a smoke and U2 move to TASL-2; the harness-isolation host checks pass on TASL-2 first. |
| R1-TRACKG-G3-EARLY | T1 nodes: `mlab_cifar10`, `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`. `autoresearch_fixedtokens` and `mlgym_houseprice` "join as soon as their U2 passes". `mlgym_houseprice`'s U2 passed in the U4 census (20 Nov; CPU-only), so seven nodes are certain. `autoresearch_fixedtokens`' U2 passed on TASL-2 (the U4 census, `reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, B1 218.951 s on TASL-2's RTX 4090); it joins G.1b under the third note (R1-G1B-NOTE2-DECISIONS), now signed (`authorizations/g1b_ar_t1_tasl_20261122.md`, run `g1b-ar-tasl-20261122-a`). It enters G.5 under G5-AR A (R1-G5-DECISIONS, §2.11). |
| R1-T1-TASL-ENV | Replaces the image row; it is on `main` and was a draft in revision 6. It fixes the following, and each STOPs the job if not met:<br>– **Hosts:** TASL-2 (driver 535.309.01) and TASL-7 (driver 580.178.04), each identified by host name and the full UUID of its RTX 4090; a driver change during the table STOPs.<br>– **Environments:** torch312 and jax312 built with uv from the census freezes (Python 3.12.16), equal to the freeze at every job start.<br>– **Harness:** at the commit the signed note names, clean; the harness-isolation host checks passed on every host that runs workers.<br>– **Jobs:** non-root, Yama `ptrace_scope` ≥ 1, the delegated scope (MemoryMax 8G, MemorySwapMax 0), the host's GPU lease, no other compute process on the card.<br>– **Proposer:** the Track X exam `llama-server` on TASL-7, used in place (executable `b70f4882…7d8b`, build `620d222`, its build directory bound by a manifest), with the pinned GGUF and the exam settings, on TASL-7's Tailscale address.<br>– **Node data:** manifests equal to the census (for `mlgym_fmnist` and `mlgym_cifar10`, the census erratum of R1-T1-DATA-MANIFEST).<br>Its environments do not include autoresearch's `ar-cond7a` (Python 3.12.15); R1-G1B-AR-ENV, amended by R1-G1B-AR-PY, admits it for autoresearch's G.1b (P9). |
| R1-G1B-EDITS, R1-G1B-TIMEOUT | G.1b measures the four declared edits E1–E4 per T1 node (460 runs per node). The T1 timeout (G.1b, G.4, G.5) is 3 × the slowest of the node's B1, B2 and E1–E4 census records (`census_slowest_x3`; the node's own census host where that is a TASL host, as for autoresearch). In G.5, an edited proposal's timeout is its failure, and a baseline timeout STOPs the campaign. |
| R1-G1B-TASL-DECISIONS, R1-G1B-NOTE2-DECISIONS | **G.1b on the TASL pair.**<br>– The launch binding is LB A (`verify_launch_tasl`): hosts launch from the signed, published commit whose code equals the note's `paper_commit` outside `docs/` and the spec (paper_commit `10fd3343` in the first note).<br>– The signed first note (`authorizations/g1b_t1_tasl_20261121.md`, run_id `g1b-tasl-20261121-b`) ran the TASL-2 nodes from `985dd45d` (or its docs-only child `dbdbd2b6`), the checkout the signed G.4 note names; three are sealed.<br>– The three TASL-7 nodes run under a second note, with the same run_id, once the cross-host check has passed. The cross-host check is re-issued under R1-T1-DATA-MANIFEST (`authorizations/g1b_xc_t1_tasl_20261123.md`, run `g1b-tasl-20261121-b-xc2`, a full rerun); note 2 is published after its three step-1 verdicts are PASS and committed, and is not on `main` yet.<br>– `autoresearch_fixedtokens` joins G.1b under the third note with its own spec (run_id `g1b-ar-tasl-20261122-a`, R1-G1B-CAP's 100 GPU-h shared). Harness `2d09f9a9` is reviewed and the spec support is on `main` (`mac-g1b-ar-20261122`, READY 81, merged as `c35c922d`). The first TASL-2 host check at that pin STOPped on 22 Nov (Python 3.12.16 against the frozen 3.12.15); R1-G1B-AR-PY resolved it, and the rerun is PASS (binding record below). The third note is signed: `authorizations/g1b_ar_t1_tasl_20261122.md` (sha256 `ac5ee6c5…`; `paper_commit` `570ae410`, `spec_sha256` `65da95db…`, harness `2d09f9a9`, launched from chain commit (d) `d52c9d9d`). No result of autoresearch's G.1b is on `main` yet. |
| R1-T1-DATA-MANIFEST (22 Nov) | The census data manifests of `mlgym_fmnist` and `mlgym_cifar10` become the manifests the frozen environment produces (census erratum `reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md`, published on `main` byte-identical to the reviewed bytes, sha256 `9b40944be4df5f214066d689f7f0537590ed95895f9754b55630d8e774077799`, commit `4b7452b6`); the G.1b, cross-check and G.4 specs are re-issued with the corrected values. **The TASL launch chain is published** (`reports/tasl_chain_20261122/PUBLICATION_20261122.md`, `LAUNCH_TABLE.md`, `launch_table.json`, `TASL_CHAIN_20261122.md`; review `reviews/TASL_LAUNCH_CHAIN_REVIEW_20261122.md`): (a)–(c) by merge `38ae4a05` without squash, launch commits (a) `34a5b1d6` (G.1b amendment for `mlgym_fmnist` and note 2; spec `7ff3c95b…`, paper commit `3c3f822a`), (b) `b5824240` (cross-check `-xc2`; spec `a9e6b463…`), (c) `6ad899e0` (G.4; spec `fd9c6e9d…`); (d) `d52c9d9d` (autoresearch's G.1b; spec `65da95db…`, paper commit `570ae410`) by merge `5d5ca7b4`. Signed and published: the amendment note `authorizations/g1b_t1_tasl_20261122.md`, the cross-check re-issue `g1b_xc_t1_tasl_20261123.md`, the G.4 re-issue `g4_t1_tasl_20261123.md`; the first cross-check and G.4 notes are superseded. Note 2 is not yet published. G.5's node data pins are these values (§5). |
| R1-G1B-AR-ENV (22 Nov), R1-G1B-AR-PY (22 Nov) | Autoresearch's G.1b runs in `ar-cond7a` in place (`/home/dowling/r1_trackp/venvs/ar-cond7a`, Python 3.12.15, torch 2.6.0+cu124), read-only, for this node only, every job comparing `uv pip freeze` and the Python version with the committed freeze `sweep2/g1b/env/ar-cond7a.freeze.txt` (`11def6ad…`). R1-G1B-AR-PY amends it after the AR-pin host-check STOP: the venv's interpreter symlinks are re-pointed to uv's versioned CPython 3.12.15, the only change to the venv; the freeze, spec, note and procedure stay unchanged, and the host check reruns. The rows name G.1b; G.5's use of the same environment for autoresearch is part of the G.5 note (P9, §11). |
| TASL-2 host check at harness `2d09f9a9` (record, not a row) | `reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md`, sha256 `cce9b8fbf5586fe824b5016f572975a24f2b818019f627c2480f18c4650e175e` (merge `e9c12a4a`; review `reviews/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_REVIEW_R4_20261122.md`): `host_check_items: 1-7 PASS`, `host_check_verdict: PASS` at `2d09f9a9`, the rerun after R1-G1B-AR-PY. As on 21 Nov, item 7 (CUDA IPC) is untested on TASL-2. The third note cites it as its P2. |
| R1-G1B-JOIN (22 Nov) | Option A of decision G1B-JOIN (`reports/tasl_chain_20261122/TASL_CHAIN_20261122.md` §4): the G.1b seven-node row of run `g1b-tasl-20261121-b` is assembled across the first note's three sealed TASL-2 attempts (spec `060aac91…`, paper commit `10fd3343`) and the attempts under the spec re-issued by R1-T1-DATA-MANIFEST (paper commit `3c3f822a`), by `sweep2/t1_tasl/g1b_tasl_join.py`, each group by `g1b_tasl.assemble` unchanged, behind the unchanged cross-check gate. Nothing is rerun; autoresearch joins by node from its own run (§3). |
| R1-G5-DECISIONS (22 Nov) | On revision 7: **G5-AR A** — G.5 covers eight nodes (the seven plus autoresearch); accepted cost as projected, about 305 GPU-h at K = 10 (autoresearch about 138), the cap raised accordingly ("425 GPU-h in revision 7, to be fixed in the G.5 note"), B.7 from about 8 Dec to about 15 Dec 2026; **K = 6** (about 208.5 GPU-h, B.7 about 11 Dec) only after a published K-check author row, until then **K = 10**. **G5-PIN B** — two G.5 harness commits carrying byte-identical G.5 code, one on `c025f89a` (the seven nodes' noise floor), one on `2d09f9a9` (autoresearch's); each node's G.5 runs on the harness commit of its own G.1b noise floor. "The G.5 note itself still needs the author's signature." |
| R1-G4-DECISIONS, signed G.4 note | G4-LB A (the TASL launch binding for G.4); G4-ORDER B (lease order only: the pilot runs whenever both cards are free); G4-NODE3 A (pilot nodes `mlab_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`; **no autoresearch-suite node**). The pilot: 3 instances per node (seeds 4001–4003), W = 20 manager calls, temperature 0.2, memory mode `history`, `max_tokens` 4096; run_id `g4-tasl-20261121-a`. **The note in force is the re-issued `authorizations/g4_t1_tasl_20261123.md`** (sha256 `89e50a9c…`; signed by the coordinating chat under R1-T1-DATA-MANIFEST): `paper_commit` `b5824240`, `spec_sha256` `fd9c6e9d…`, launched from chain commit (c) `6ad899e0` or a docs-only descendant; only the `mlgym_fmnist` manifest and the binding fields changed. It supersedes `g4_t1_tasl_20261122.md` (`paper_commit` `02abb367`), under which no pilot job or server ran. *(Revision 12:)* the pilot has run; its result report (`reports/tasl_chain_20261122/G4_TASL_PILOT_RESULT_20261122.md`, as R1-G5-DIFF-RECOUNT cites it) is on an ops branch. R1-G5-DIFF-RECOUNT added the G.4b re-pilot (run `g4b-tasl-20261124-a`, signed note `authorizations/g4_t1_tasl_20261125.md`, below): P3 and P7 read G.4b's sealed attempts, not G.4's. G4-LB A, G4-ORDER B and G4-NODE3 A stand for G.4b. |
| R1-SWEEP2-PREREG (frozen 21 Nov) | `authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, `frozen: true`. Relevant decisions:<br>– **PRE-SPLIT A:** P3 is the only evidence split. The T1 rule is G5-SPLIT verbatim, and its assignment is in `r1/c3/splits/c3_p3_split_v1.json` (sha256 `b5967dd7…`, eight T1 nodes, autoresearch included).<br>– **PRE-MEM C:** T1 enters with its mode(s) under G5-MEM.<br>– **PRE-DUP A:** the cross-instance repeat rule for the primary test and dev populations is the one G5-AUDIT proposed.<br>– **PRE-DIV A:** divergence on the evaluation seeds.<br>– **PRE-T1 A**, verbatim: "one primary gate read. The T1 node set and its instances are frozen in the arms-frozen record: exactly the T1 nodes whose train/dev labels were released and used to freeze the arms; a node needs ≥ 1 train and ≥ 1 dev instance to be supplied (otherwise reported, not supplied); nodes that STOP at G.5 follow the G.5 rule. No test partition of any tier is released before the arms-frozen record. A later read with more T1 nodes is not allowed."<br>– **PRE-SECONDARY A:** leave-one-suite-out is a descriptive analysis (no verdict), with fold arms retrained without the held-out suite; it STOPs if a suite has no labelled T1 node.<br>– **PRE-STAGE A:** a code lock for both sources: until the test release row exists, readers get the label block of train and dev instances only and no evaluation value of any instance (receipted partitions written by the release step).<br>– **PRE-DELTA A:** T1 σ_node from each node's sealed G.1b summary, its path and sha256 recorded in the T1 train/dev release row before any training (as amended by REL-T1-G1B, below). R1-T1-FEAT-DECISIONS reads it for T1: "T1's σ_node and δ_n both come from the `runs.jsonl` copies bound by sha256 to each G.1b summary; the preregistration itself is unchanged" (below).<br>– Procedure §4 steps 4–5: the **arms-frozen record** (arms, T0 and T1 node sets, split-file, noise-source and G.1b summary sha256s, gate and gate-input builder sha256s), then the test label blocks and every evaluation block.<br>The preregistration's sha256 is `aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5`. |
| R1-SWEEP2-RELEASE-DECISIONS | REL-SCOPE A (PRE-STAGE A as signed: until a test row exists, readers get train/dev labels only); REL-CODE A (integrity checks in `r1/c3/release_checks.py`); **REL-T1-G1B:** PRE-DELTA's "each node's sealed G.1b summary on H200" reads "on the T1 host of R1-T1-HOST-TASL", each summary copied out of the sealed tree by a reviewed step with its sha256 before the T1 train/dev row (§3, §6). Its copy list is amended by R1-T1-FEAT-DECISIONS D6 A (below): each G.1b run's `ASSEMBLY.json` and `runs.jsonl` are copied beside the summary copy. |
| R1-BX-D14 | Target dates: B.7 ≈ 8 Dec 2026, D.3 ≈ 3 Jan 2027, manuscript 10 Jan 2027. They are recomputed from measured throughput after the T1 pilot, and changes are reported to the author before they are applied. R1-G5-DECISIONS accepted B.7 moving to about 15 Dec with autoresearch (pre-pilot; with R1-BX-D14's spans, D.3 about 10 Jan 2027 and the manuscript about 17 Jan 2027). *(Revision 12:)* R1-BX-D14-G4B (below) sets the targets from the G.4b recompute: B.7 ≈ 14 Dec 2026, D.3 ≈ 9 Jan 2027, manuscript 16 Jan 2027. |
| R1-BX-D1, R1-BX-D5 | T1 nodes are label nodes; the nodes' fixed step budgets; one GPU model per table. |
| D1 | The campaign budget is compute (worker runs) plus an LLM-call cap (see G5-W). |
| D15, D26 | Manager temperature 0.2; every manager call carries a seed derived deterministically from (instance, trial index, repetition), recorded in its call event (see G5-TEMP). |
| R1-BX-D3, R1-BX-PROPOSED-CONFIRM (D3; Track G E4) | Audit seeds K = 6 (labels 7001–7003, evaluation 7006–7008) for T1 **only after** the sweep-1 subsampling check passes and a PLAN row records it; until then **K = 10** (repeated by R1-G5-DECISIONS for G.5). If the check fails, K stays 10 and the coordinating agent STOPs for the author. E4 also says "both memory modes; about 12 campaigns per T1 node" (see G5-MEM). |
| R1-BX-PROPOSED-CONFIRM (E5) | Divergence = a non-finite loss, or no metric at the fixed budget. A divergent proposal enters no belief bin, is counted separately, and has action target u = −g. If only some seeds diverge, μ comes from the rest and the label is marked partial; more than half diverging makes the proposal divergent. A heavy-tailed node uses a Student-t, declared before labels are built. |
| R1-MAIN-PROPOSER (e) | Duplicates are grouped by (instance, incumbent hash, edit hash) for folds and deduplication; one instance → train/dev/test assignment; pooled intervals use an instance-cluster bootstrap. |
| R1-BX-D8-V3-A (3) | Split per tier P3 = 1/3 : 1/6 : 1/2 (train : validation : test), written into the analysis preregistration. |
| R1-BX-D8-V3-B (author's addition) | **T1 = 12 instances per node**; per-tier test floor T1 ≥ 3 test instances per node; a node below the floor is excluded from the IQM, kept in the PoI and reported. |
| R1-BX-D8-CONFIRM-V31 (replaces the gate of R1-BX-D8-CONFIRM) | Gate v3.1: `r1/c3/gate.py` @ `31dab9efb94b7f187ec44cab1bc4a4ad63c1085d`, sha256 `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23` (it differs from v3 only in accepting a declared T0 node set); T0 and T1 pooled with tier as a stratum; partial T1 at B.7 read on T0 plus the labelled T1 nodes, disclosed; leave-one-suite-out needs at least one labelled T1 node per suite, otherwise it STOPs; the aggregate gate does not STOP on it. The T1 seal is lifted by the T1 release rows under PRE-STAGE A (§6). |
| R1-MAIN-PROPOSER, R1-EXAM-X7, R1-SWEEP2-SETTINGS (1) | Proposer `gemma4_31b`, thinking off, the exam server flags, context 32,768, `cache_prompt` false. |
| R1-EXAM-B1-TRUNCATION-INVALID | Every proposer call carries a completion cap; a truncated reply is an invalid proposal. |
| R1-BX-PROPOSED-CONFIRM (D4) | `manager_proposal/v2-diff`. A pick that fails diff liveness on a T1 node is a STOP; the author decides between a single-parameter fallback and moving the node to T2. |
| R1-TRACKG-G5-DIVERGENCE (4 Nov) | Asked "whether a T1 node should STOP when its audited label proposals' divergence fraction exceeds 20 %, or instead be judged case by case", the author replied "设 20% STOP" (set a 20 % STOP). The recorder's *(proposed)* consequence: a move to T2 needs a separate author row. The 20 % "originated as an agent proposal, not a measured threshold". |
| R1-TRACKG-PORT-DECISIONS (3), (4) | (3) The port-written imdb baseline is frozen and independently reviewed before any label run, and the census funnel and appendix say "baseline written by us". (4) Timeout = 3 × the census baseline run time; a timeout is the proposal's failure, not an infrastructure rerun. |
| R1-HARNESS-ISOLATION | Every T1 label run is effectively isolated: `effective: true`, `waivers {}`, `exceptions []`. Anything else is refused. |
| R1-B2-DECOUPLE, 28 Oct clarification | Labels use the label seeds; the evaluation seeds are never used for C3 or Track P training, tuning or selection. |
| R1-S2-LABELS-TRAINDEV-RELEASE, R1-SWEEP1-RELEASE-COMPAT(-SCOPE) | The T0 train/dev release under PRE-STAGE A with `r1/c3/release.py`: performed for sweep 2 (merge `dc9ad88a`) and, after the compatibility replay, for sweep 1 (merge `a454d6db`), with receipts under `reports/release_2026112*/`. The T1 rows follow the same release step (§6). |
| R1-ARMS-FEATURIZER (23 Nov) | Arms trained on both T0 sources use the v3 featurizer. Extended to every arm by R1-ARMS-DECISIONS (FEAT-ONE A). |
| R1-G5-DECISIONS-2 (23 Nov (b)) | "Section 11 decisions of the G.5 draft revision 8 (READY 84; code READY 88–90), as recommended": G5-W A (20 manager calls); G5-TEMP A (0.2 with the engine's seed rule); G5-MEM A (`history` only, 12 instances per node; with R1-G5-MEM-E4); G5-AUDIT A (audit-once for cross-instance groups; parent runs reused subject to cluster test C2; E5 on the label seeds only); G5-DIV A (20 % on audited proposals from 40; the literal "2 × census" kept); G5-TASL-GPUH A (the worker card counts against the 425 GPU-h cap); G5-SLOT A (one slot on TASL-2); G5-ARPEND A (autoresearch's prerequisites PENDING at signature, completed by a reviewed record that the coordinating chat commits). "Section 11 items 9–16 and the new note lines are fixed at the note's signature." |
| R1-G5-MEM-E4 (23 Nov (b)) | Amends R1-BX-PROPOSED-CONFIRM E4's "both memory modes" for T1: G.5 runs the engine's `history` memory mode only, 12 instances per node (12 campaigns, as E4 counts them); the memory-mode contrast stays on T0; disclosed as different from both T0 modes. (Context, not row text: R1-G5-DECISIONS-2 ties it to G5-MEM A; the switch's check at `baf6be5d` is in §2.3.) |
| R1-ARMS-DECISIONS (23 Nov (b)) | T0 arms (READY 87, `mac-t0-arms-readiness-20261123` @ `4e4d6d1a`, `reports/arms_readiness_20261123/T0_ARMS_READINESS_20261123.md` §3), as recommended. *(Context, not row text: the arms-frozen record's code is `r1/c3/arms_freeze.py`, merged as `630398c6`.)* For G.5: ARMS-T1FEAT A (a reviewed CPU unit gives G.5 rows the features); ARMS-WDBC A (A3 trains and selects on all eight T0 nodes plus T1); ARMS-TWIN B (per-mode twin groups); FEAT-ONE A (v3 for every arm); ARMS-SECONDARY A, which amends PRE-SECONDARY A as to the secondary arms in this read (its text does not mention leave-one-suite-out). *(Context, not row text: the record format is `r1_c3_arms_frozen/v1` (`arms_freeze.render_record`, `check_record`); R1-T1-LABELS-TEST-RELEASE, not yet a row, will cite the record by path and sha256 as `release.row_pattern` requires (§6).)* |
| R1-T1-FEAT-DECISIONS (23 Nov (e)) | The ARMS-T1FEAT report's §5 decisions (`reports/arms_t1feat_20261123/T1_FEATURES_20261123.md`): D1 A, D2 A, D3 A, D4 A, D8 A; **D6 A**, amending REL-T1-G1B: "a reviewed copy of each G.1b run's `ASSEMBLY.json` and `runs.jsonl` (noise-floor data, ENGINEERING_ONLY, G.1b seeds only) is committed beside its summary copy and `g5_noise.derive` runs on the copies"; D18's 0.002 floor as preregistered; **D6-σ B**: "σ_node for T1 uses T0's definition (median `sd_joint` over material edits, over all edits if none is material) from the bound `runs.jsonl`, with reviewed code and spec field on main before the G.5 launch"; D7 by a separate unit (R1-T1-A5-DECISIONS, below); **D9 B**: "the assembly STOPs on any non-zero `raw_state_missing` or `flag_mismatch` count; reviewed code on main before the G.5 launch". Its reading of PRE-DELTA is quoted under R1-SWEEP2-PREREG above. *(Context, not row text: the code is READY 97, merge `44c3d80e`, report `reports/arms_t1feat_20261123/T1_FEAT_DECISIONS_20261123.md`, review `reviews/T1_FEAT_DECISIONS_REVIEW_20261123.md`, `Verdict: ACCEPTED`; the switch's check of this row is in §11.)* |
| R1-T1-A5-DECISIONS (23 Nov (f)) | A5's T1 input (READY 98, `mac-a5-t1-prompt-20261123`, its report §6–§7): D7-FORM A (`trackp_prompt_t1/1` is A5's T1 input, disclosed); **D7-DIFF B with fallback A**: a bounded diff excerpt, "with the reviewed `g5_assemble` change on main before the G.5 launch; if it is not on main by then, the input is A (no diff text) with FL1 disclosed"; D7-HIST A; D7-WORDING as built; F1 A; FL4–FL6 (as the row states). *(Context, not row text: READY 98 with `main` `3024db3f` merged in (READY 100), not on `main`, and the D7-DIFF B `g5_assemble` change (READY 103, report `reports/arms_t1feat_20261123/D7_DIFF_B_20261124.md`, review `reviews/D7_DIFF_B_REVIEW_20261124.md`) are accepted on `mac-d7-diff-b-20261124` @ `c2804f58`; neither is on `main` `3024db3f`; §6 step 2, §9.)* |
| R1-T1-D21-SCOPE (25 Nov; on `main` `5d4f1b09`; revision 11) | "D21 does not select T1 nodes for C3. Every T1 node that passed U2, G.1b fixed-seed determinism and, where run, the cross-host check enters G.5 and, if its G.5 completes, PRE-T1's T1 node set, regardless of its D21 value; no other threshold is introduced." The 22 Oct D21 rows keep governing T0's noise-node pool; PRE-T1 does not use D21. Each node's D21 value is reported in the screening funnel (R1-BX-D12). G5-AR A stands. Under D21 only `mlgym_breakout_minatar` and `mlgym_houseprice` qualify (the row's figures). |
| R1-G5-AUDIT-TWO-CARDS (25 Nov; on `main` `5d4f1b09`; revision 11) | Amends G5-SLOT A: campaign waves keep one worker slot on TASL-2 with the proposer server on TASL-7; G.5 audit chunks (no proposer) may also run on TASL-7's RTX 4090 while no campaign wave holds the server, with the GPU leases keeping a card from being shared. One table, one GPU model (both RTX 4090). A node's audits run on TASL-7 only after a cross-host check PASS for that node: the xc2 verdicts for the three TASL-7 nodes; for the others, a short cross-check under the reviewed `g1b_crosscheck.py` before their first TASL-7 audit chunk. The TASL-7 harness isolation host check record is cited in the G.5 note. Implemented as a reviewed code unit; the G.5 note fixes the schedule. |
| R1-G5-DIFF-RECOUNT (24 Nov; on `main` `3024db3f`) | The G.4 pilot (its result report on an ops branch, not on `main`) refused 155 of 180 proposals (122 `malformed_hunk`, 33 `malformed_diff`). Option A: the G.5 harness commits (G5-7 and G5-AR, byte-identical G.5 code, `g5_pin_check`) apply a manager diff after recomputing each hunk header's line counts from the hunk body (`git apply --recount` semantics); the context must still match; structurally malformed diffs stay refused; a reviewed harness unit. A short G.4b re-pilot on the same three nodes (W = 20, new run id) measures diff liveness and recomputes the R1-BX-D14 dates; the coordinating chat publishes its spec and re-issued note after independent review and passing launch checks, without a further author decision. The G.4 pilot's strict-application liveness is disclosed. *(Revision 12 works it in fully: the recount tips are the G.5 harness commits (§2.12, §9); the G.4b re-pilot, run under the recount harness G5-7 `cbf7a003`, is P3's basis (the spec's `pilot_basis`), and its result (`reports/tasl_chain_20261122/G4B_TASL_PILOT_RESULT_20261125.md` with its corrigenda; PASS on 3 nodes, liveness `ran_of_valid` 0.6667 / 0.8167 / 0.6167, review ACCEPTED) gives the dates and P7. The G.4 pilot's strict-application liveness (0.0167 / 0.1833 / 0.1667) is disclosed.)* |
| R1-BX-D14-G4B (26 Nov; on `main` `f1f1b651`; revision 12) | G4B-DATES A: the binding eight-node G.5 recompute after the G.4b re-pilot gives the targets B.7 ≈ 14 Dec 2026, D.3 ≈ 9 Jan 2027, manuscript 16 Jan 2027 (216.9 of 425 GPU-h projected; 6 days after the 4 Nov targets); the seven-node comparison is not used. "These dates are targets, not gates." When the expansion nodes that enter G.5 are known (cutoff 2 Dec) and when READY 108's TASL-7 audits are in the dates tool, the coordinating chat recomputes and reports a later date before applying it. The NEMO2 H200 outage can make P.4/A5 the critical path for B.7. |
| R1-XC3-FAIL-READING (26 Nov; revision 12) | XC3-FAIL A: R1-T1-D21-SCOPE's "where run, the cross-host check" is the R1-T1-TASL-ENV check that gates a node's G.1b (xc2 for the three TASL-7 nodes). The short cross-check (xc3) decides only where a node's G.5 audits may run: a non-PASS keeps them on TASL-2 and does not remove the node from G.5 or PRE-T1. "The xc3 note carries xc3_fail: A." |
| R1-XC3-NOTE (26 Nov; revision 12) | The author signs the xc3 note (READY 107; launch commit `6f4e2ba1`, spec `sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json` sha256 `fc064ded…`), published as `authorizations/g1b_xc_short_t1_tasl_20261126.md` with `xc3_fail: A`, `xc3_cap: R1-G1B-CAP` (2.0 GPU-h inside R1-G1B-CAP) and `skip_nodes: none` (`mlgym_houseprice` runs). |
| R1-G5-EXPANSION-JOIN (26 Nov; revision 12) | G5-EXPAND A: G.5 launches on its eight nodes as soon as its note is signed. An R1-T1-NODE-EXPANSION candidate whose G.1b completes with determinism PASS by 2 Dec 2026 joins G.5 through a G.5 addendum note with the same code, K and rules; until 2 Dec the expansion G.1b jobs take precedence on the TASL cards. |

**The v2-diff engine as it is** (harness `c025f89a`, the TASL G.1b and G.4 pin; it adds only `--gpu-uuid`, CPU-only
chunks and `stop_on_timeout` to `b5747066`, none of which touches the v2-diff engine; autoresearch's pin `2d09f9a9`
descends from `c025f89a` and changes only autoresearch's node files and config, `node_lib/ar_isolated.py`, a code-unit
report and the port-check tests, not the engine): one manager call per proposal; a
temperature parameter (its original default 0.0; the G.4 pilot and the G.4b re-pilot pass 0.2); a per-call seed
`sha256("<manager seed>:<step>")[:8]`, deterministic in (instance, trial index), repetition 0; a memory parameter
with two modes: `history` (the prompt shows the campaign's own last 12 steps: summary → decision (metric)) and
`none` (no history). Neither mode is T0's `append_only_summary`, which keeps a summary file. Within a campaign, inert
proposals and duplicates of an earlier step are not run.

## 2. Author decisions (each with options and a recommendation)

Every decision of this section is now recorded on `main`: G5-AR A and G5-PIN B by R1-G5-DECISIONS; the eight others,
each as recommended (A), by R1-G5-DECISIONS-2; G5-SPLIT by the preregistration. The options are kept as the record of
what was decided. "Recommended" below means the option the row chose.

### 2.1 G5-W: what W = 20 counts (decided: A, R1-G5-DECISIONS-2)

The 20 Nov task says "W = 20, ~150 audited proposals/node". The G.4 and G.4b pilots and the v2-diff engine count W in manager
calls. D1, sweeps 1 and 2 (`--runs 20`) and R1-W2-3-STOP count W in worker runs.

- **A (recommended): 20 manager calls per campaign.** 240 × ran share audited proposals per node (144 at share 0.6,
  192 at 0.8, §2.8), close to the task's "~150". The engine supports it today, and the G.4b re-pilot, P3's basis,
  ran it (W = 20 manager calls, as the G.4 pilot did), so P3 needs no re-run.
  - The label definition does not depend on W, but the population of labelled proposals does: about 12–16 runs per
    T1 campaign against 20 on T0, so T1 proposals come from earlier, weaker incumbents and lower trial indices.
    With tier as a stratum in the gate this is a disclosed difference between tiers.
  - R1-W2-3-STOP (every Track P source ledger uses exactly 20 worker runs) concerns the sweep data rebuild; a T1
    ledger would fail that check. Any Track P use of T1 ledgers needs its own author row.
- **B: 20 worker runs plus an LLM-call cap of 80 per campaign.** Matches D1 and the sweeps; 240 audited proposals
  per node; 1.6 × the GPU-hours of A at ran share 0.6 and 1.23 × at 0.8 (§2.8). Needs a worker-run budget in the
  v2-diff engine (harness work, §9) and then a re-issued G.4b re-pilot with it (P3), which moves the dates.

The audited band of STOP 9 depends on this choice: *(proposed)* 100–200 under A, 150–240 under B (B gives 240 ran
proposals per node, fewer audited after cross-instance duplicates).

### 2.2 G5-TEMP: the proposer temperature (decided: A, R1-G5-DECISIONS-2)

- **A (recommended): temperature 0.2 (D15) with the engine's per-call seed rule.** The engine has the parameter since
  `24935be3`, and the G.4b re-pilot (P3's basis) ran at 0.2, as the G.4 pilot did, so the pilot's shares are measured
  under the setting G.5 uses. The seed
  rule meets D26's determinism (instance, trial index, repetition 0) but is not T0's derivation function; disclosed.
- **B: temperature 0 (the engine's original default).** Fully deterministic on a deterministic server. At step 1
  every instance of a node sees the same prompt (baseline code, no history), so all 12 instances make the same first
  proposal; instances diverge only through the metrics that later enter the history. More cross-instance
  duplicates, less diversity; a disclosed deviation from D15. The G.4b re-pilot would have to be re-issued at 0 (P3),
  which `g4_tasl.validate_spec` also refuses today (it requires 0.2).

### 2.3 G5-MEM: memory mode (decided: A, R1-G5-DECISIONS-2, with R1-G5-MEM-E4)

E4 says "both memory modes; about 12 campaigns per T1 node"; V3-B says 12 instances per node.

- **A (recommended): the engine's `history` mode only, 12 instances.** 12 campaigns per node, as E4 counts them; 6
  test instances under P3, above the floor of 3. Disclosed as different from both T0 modes. **It amends E4's "both
  memory modes" and needs an author row saying so**: **R1-G5-MEM-E4** (on `main`). The spec's `e4_amendment_row`
  names the row at signature. The switch (`g5_tasl.decision_row_checks`, fixed at `baf6be5d`, accepted by the G.5-on-main review (`docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`, READY 91 @ `deb888cc`)) requires under G5-MEM A that the decisions row cite the E4 row by its id and that the E4 row's
  text, without the id cell, name "E4" and "memory modes" (`g5_tasl.plan_row`). R1-G5-DECISIONS-2 ("G5-MEM A (…; with
  R1-G5-MEM-E4)") and R1-G5-MEM-E4 both pass against `main` `89899f76`'s PLAN. The memory contrast stays on T0, where both modes run. The
  G.4b re-pilot ran `history` (P3). PRE-MEM C takes T1 "with its mode(s) under G5-MEM (one mode under G5-MEM A, the
  same rule as T0 under B)": the parenthesis refers to G5-MEM B, under which T1 has both modes as T0 does.
- **B: both engine modes (`history` and `none`), 12 instances each** (twin campaigns sharing instance seeds; labels
  shared by the (instance, incumbent, edit) key, R1-MAIN-PROPOSER (e)). About 2 × the cost (§2.8, an upper bound).
  `none` exists in the engine since `24935be3`. Neither mode is T0's `append_only_summary`; a T0-matching rendering
  would be new engine work.
- **C: both modes, 6 instances each.** 12 campaigns per node, but only 3 test instances: exactly at the floor, and it
  contradicts V3-B's 12 instances.

### 2.4 G5-AUDIT: which proposals are audited, and duplicates (decided: A, R1-G5-DECISIONS-2)

- **A (recommended): as C3_DESIGN §4 and the sweep-1 authorization:** every non-inert, non-duplicate evaluated
  proposal, **including** proposals that diverged or timed out in the campaign, and its parent incumbent, at the K
  audit seeds with joint seeds. No-ops are labelled by rule.
  - **Parent runs reused** (decided with G5-AUDIT A, "subject to cluster test C2", R1-G5-DECISIONS-2). A kept proposal's audit runs at the audit seeds serve again when it is the
    parent incumbent of later proposals (same code state, same seeds). This relies on fixed-seed determinism of
    **edited** code states on the RTX 4090; G.1b checks it only for each node's baseline and declared edits at the default
    seeds, so cluster test C2 checks it for audit pairs. If C2 fails, or the author prefers, every parent is re-run
    (`reuse_parent_runs: false`, K = 10, recommended row: at ran share 0.6, 188.3 GPU-h for seven nodes and 349.5
    for eight, within the caps; at 0.8, 235.6 (above 230) and 445.5 (above 425), so re-running every parent at share
    0.8 needs a higher cap).
  - **E5 per seed block.** A proposal's label status (divergent, partial or not) is decided by E5 over the **label
    seeds** only (7001–7005, or 7001–7003 at K = 6). Divergence on the evaluation seeds is part of the evaluation
    value `y_eval` and is handled by PRE-DIV A of the frozen preregistration; it never changes a training label,
    the divergence STOP or a pre-release count (R1-B2-DECOUPLE). Applying E5 over all K seeds would let evaluation-seed outcomes
    decide labels and remove nodes, and would need an author row amending R1-B2-DECOUPLE; not recommended.
  - **Duplicate key** (R1-MAIN-PROPOSER (e)): (instance, incumbent hash, candidate hash). Within an instance, the
    engine does not run a duplicate, so it gets no label.
  - **Across instances**, the same (node, incumbent hash, candidate hash) can recur (most at step 1, where every
    instance starts from the baseline). Because the audits use common seeds, its label would be the same in every
    instance. Such a group is audited once (decided with G5-AUDIT A) and every member carries the label, so coverage does not
    depend on job order. For the gate, the test-side members of a group that also occurs on a train or validation
    instance are left out of the primary test population and kept in a secondary full population, and the
    validation-side members of a group that also occurs on a train instance are left out of the primary
    validation population (where arms are selected) and kept in a secondary one, disclosed (the same rule as
    R1-TRACKP-SFT-DUP for Track P). **The gate side of this rule is now fixed by PRE-DUP A** of the frozen
    preregistration; the audit-once part is decided by R1-G5-DECISIONS-2 (G5-AUDIT A).
  - The G.4b re-pilot reports the cross-instance duplicate rate (P3); the recompute uses it (dup factor 0.9184, §8).
- **B: every proposal with an `ok` campaign outcome.** Cheaper by the in-campaign divergent share, but in-campaign
  divergent proposals never get E5's seed-level test. It also weakens G5-DIV A, whose denominator is the audited
  proposals (§2.5). Not recommended.

### 2.5 G5-DIV: the divergence STOP (decided: A, R1-G5-DECISIONS-2)

The 20 Nov task adds "divergence > 2 × census".

- **Literal census reading.** Each census node has one deliberately divergent record (the broken diff, `s002`) among
  8 executed records: 12.5 %, so 2 × census = 25 %. It is looser than 20 % and never binds.
- **A (recommended): the author's 20 % rule, on the denominator the author was asked about.** The task's
  "2 × census" STOP is kept in its literal reading (25 %, on the same denominator); it never binds below 20 %, and
  the note says so.
  - Denominator: the node's **audited** label proposals. It therefore depends on G5-AUDIT: under AUDIT B the
    in-campaign divergent proposals are not in it, and the rule is weaker.
  - Numerator: proposals that are divergent under E5 on the **label seeds** (more than half of them divergent;
    G5-AUDIT, E5 per seed block). The evaluation seeds never enter the STOP.
  - Evaluated at the end of each wave's audits (§3), once the node has at least 40 audited proposals. If wave 1 gives
    fewer than 40, the first evaluation is at the end of wave 2, and wave 1's rate is an early warning only.
  - The noise at a small count: at n = 40, a node whose true E5 rate is 15 % STOPs with probability 0.135, and one at
    18 % with 0.286 (binomial, X ≥ 9); at n = 130 the 15 % figure is 0.047. The alternative of a single evaluation
    at the end of wave 2 lowers the false STOP but lets most of the spend happen first.
  - Early warning (not a STOP): the in-campaign single-seed divergent share per proposal after each wave, reported
    to the author when above 20 %.
- **B: min(20 %, max(2 × the upper 95 % Clopper–Pearson bound of the pilot's rate, 10 %)) on the same
  denominator**, for the three pilot nodes; the others use 20 %. The pilot runs no audits, so it measures only the
  single-seed divergent share per proposal (`divergent_of_proposals`), a different quantity, on 60 proposals.
- **C: 2 × the G.1b divergent-row rate of the node, capped at 20 %.** Exists for all seven nodes on the 4090, but G.1b
  measures declared edits, not LLM proposals.

### 2.6 G5-CAP: the GPU-hour cap (425 GPU-h for eight nodes, as projected; the figure fixed by this note)

Under W A, MEM A, AUDIT A (§2.8; worker-card hours, G5-TASL-GPUH A): with the seven nodes, 119–144 GPU-h at K = 6
and 167–206 GPU-h at K = 10 (ran share 0.6–0.8); with autoresearch as the eighth node, 209–260 GPU-h at K = 6 and
305–386 GPU-h at K = 10. Direct host runs have no scheduler, so there are no requested slot-hours; the binding
quantity is the worker card's wall time (G5-SLOT).

R1-G5-DECISIONS raised the cap "accordingly (425 GPU-h in revision 7, to be fixed in the G.5 note)". This draft fixes
it at **425 GPU-h of the worker card** (option B of revision 7 with autoresearch): it covers K = 10 at ran share ≤ 0.8
with a 10 % margin (386.0 × 1.1 = 424.6) under W A, MEM A, AUDIT A with reused parents, and G5-TASL-GPUH A. Any other
combination of §2.8/§2.11 needs the cap of its row instead, which the signature then fixes (§11): MEM B, W B,
`reuse_parent_runs: false` at share 0.8 (445.5) exceed 425; both cards counted (G5-TASL-GPUH B) stay within 425
only at share 0.6 and only if the server is stopped during the audits (≈ 360), and exceed it otherwise (§2.9). Options A
(150 GPU-h, K = 6 only) and C (a pre-declared audit subset) of revision 7 do not fit eight nodes and are withdrawn.

Under every option: the projection and the consumed worker GPU-hours (a running meter from the job records) within
the cap. The proposer card's hours are reported beside them (G5-TASL-GPUH).

### 2.7 G5-SPLIT: the instance split (fixed by R1-SWEEP2-PREREG; no longer a decision)

Per node, the 12 instances are ordered by `sha256("c3_t1_split/v1:" + <node> + ":" + <instance seed>)`. The first 6
are test, the next 2 validation, the remaining 4 train (P3 = 1/2 : 1/6 : 1/3 of 12). The frozen preregistration
(PRE-SPLIT A) quotes this rule and binds the split file `r1/c3/splits/c3_p3_split_v1.json` (sha256
`b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`, schema `c3_p3_split/v1`). Its `t1` block names
the salt `c3_t1_split/v1`, the seeds 5101–5112 and eight nodes, `autoresearch_fixedtokens` included. The signed note
cites that file; the G.5 code reads the assignment from it and recomputes it from the rule as a check. The
per-instance diagnostics are read only after the split exists (it does).

### 2.8 The decisions together (pre-pilot, `sweep2/t1_tasl/g5_projection_tasl.py`)

Worker GPU-hours and audited proposals per node, seven nodes (census run times on the RTX 6000 Ada × 1.0, LLM 60 s per
call; the 4090 values measured by the G.4b re-pilot replace both in the recompute, P3 and P7). AUDIT A; cross-instance
duplicate factor 1.0 (conservative; the G.4b re-pilot measured 0.9184); parents = the 12 baselines (a kept proposal's audit runs serve again when it is a later
parent: same code state, same seeds, on a fixed-seed-deterministic host); MEM "both" is an upper bound (twin campaigns
share labels by key). The eight-node figures with autoresearch are in §2.11.

| W | MEM | Ran share | K = 6 GPU-h | K = 10 GPU-h | Audited per node |
|---|---|---|---|---|---|
| A: 20 calls | A: one mode | 0.6 | 118.7 | 166.9 | 144 |
| A: 20 calls | A: one mode | 0.8 | 143.8 | 206.2 | 192 |
| A: 20 calls | B: both | 0.6 | 237.5 | 333.8 | 288 |
| A: 20 calls | B: both | 0.8 | 287.5 | 412.4 | 384 |
| B: 20 runs, cap 80 calls | A: one mode | 0.6 | 189.6 | 265.5 | 240 |
| B: 20 runs, cap 80 calls | A: one mode | 0.8 | 177.6 | 253.6 | 240 |
| B: 20 runs, cap 80 calls | B: both | 0.6 | 379.2 | 531.0 | 480 |
| B: 20 runs, cap 80 calls | B: both | 0.8 | 355.3 | 507.1 | 480 |

With one worker slot (G5-SLOT) these hours are also the label span in hours: the recommended row at K = 10 is 7.0–8.6
days of the worker card alone (12.7–16.1 days with autoresearch, §2.11).

### 2.9 G5-TASL-GPUH: which card's hours count against the cap (decided: A, R1-G5-DECISIONS-2)

On H200 one card carried the server and the worker. On the TASL pair the proposer holds TASL-7's card for the whole
campaign span while the worker uses TASL-2's.

- **A (recommended): the cap counts the worker card (TASL-2).** The proposer card's held hours (campaign spans) are
  metered and reported beside it, not capped. The 230 GPU-h of G5-CAP B were sized on worker plus server work on one
  card, so A is the closer like-for-like.
- **B: both cards count.** What the proposer card adds depends on how long the server is held:
  - held for the campaign waves only (stopped during the audits): + the campaign hours, 167 + 39 ≈ 206 GPU-h at ran
    share 0.6 and 206 + 43 ≈ 249 at 0.8 (K = 10, W A, MEM A) — within cap B at 0.6, above it at 0.8;
  - held for the whole label span (G5-SLOT A, one server start): × 2, ≈ 334 and 412 GPU-h; cap B would need raising.
  - With autoresearch (G5-AR A), K = 10, W A, MEM A: campaign waves only, 305 + 55 ≈ 360 GPU-h at 0.6 (within 425)
    and 386 + 62 ≈ 448 at 0.8 (above 425); the whole span (G5-SLOT A with one server start), ≈ 611 and 772 (above
    425). So under B the 425 cap holds only at share 0.6 with the server stopped during audits.

### 2.10 G5-SLOT: one worker slot, and TASL-7 (decided: A, R1-G5-DECISIONS-2; amended by R1-G5-AUDIT-TWO-CARDS)

TASL-7's card serves the proposer for the table's span (it holds TASL-7's GPU lease), so G.5 has **one** worker slot
(TASL-2). TASL-7's G.1b nodes (under the second G.1b note, after the cross-host check) must be sealed before the G.5
server starts, since both use TASL-7's lease. The G.4 pilot and the G.4b re-pilot (both run) were not ordered
against G.1b (G4-ORDER B), but needed TASL-7's lease. Autoresearch's G.1b (third note, ≈ 28.2 GPU-h) runs on TASL-2 and so shares the worker card
with G.5.

- **A (recommended): one slot, nodes in sequence on TASL-2.** The dates below are pre-pilot, from `g4_tasl.py dates`
  with `--today 2026-11-22` (G.4 is signed but has not run; nothing from the cross-check or the pilot, and three of
  the seven G.1b nodes, are sealed). Revision 9 does not recompute them; `main` `89899f76` holds no newer G.1b,
  cross-check or pilot result. They assume the remaining G.1b work takes 1 day before the labels start. These
  are the seven-node dates, kept for comparison; G.5 covers eight nodes (§2.11, R1-G5-DECISIONS). *(Revision 12:)*
  the binding dates are the G.4b recompute of G4B-DATES A (R1-BX-D14-G4B; P3): on 25 Nov, eight nodes, K = 10, one
  slot, 216.9 GPU-h: labels done 11 Dec, B.7 14 Dec 2026, D.3 9 Jan 2027, manuscript 16 Jan 2027 (−6 days against the
  4 Nov targets). The G.4 pilot's own recompute (seven nodes, ran share 0.1667 under strict diff application) gave B.7
  3 Dec; R1-G5-DIFF-RECOUNT replaces it.
  - Seven nodes, K = 10, ran share 0.6 and LLM 60 s per call: labels done 5 Dec, B.7 8 Dec, **0 days of slack**
    against R1-BX-D14. The slack was 1 day on 21 Nov; the day lost is the calendar day, not a new measurement.
  - At ran share 0.8, or at 120 s per call: B.7 10 Dec (−2 days).
  - With 2 days of remaining G.1b: B.7 9 Dec (−1), or 11 Dec (−3) at share 0.8 or 120 s per call.
  - With autoresearch: §2.11.

  The G.4 pilot measured the 4090's LLM speed (median 12–15 s per call, against the 60 s assumed above); the G.4b
  re-pilot measured it again (median 11.83 s over its three nodes), and its figures are in the recompute (P3, P7).
- **B: audits on TASL-7 while campaigns pause.** The audit chunks need no proposer, so TASL-7's card could run audits
  between the waves when the server is stopped. This needs TASL-7's host checks (R1-T1-HOST-TASL's precondition) and
  a server restart per wave (identity re-checked each time); about 30–40 % shorter label span. Not built (still
  refused by the validator).

**The amendment (R1-G5-AUDIT-TWO-CARDS, revision 11; on `main` since merge `03c0d842`, READY 108).** Campaign
waves keep **one worker slot on TASL-2** with the proposer server on TASL-7. G.5 **audit chunks** (no proposer) may
also run on **TASL-7's RTX 4090 while no campaign wave holds the server**. As built (`g5_tasl.py`, `g5_job.py`; change
report §2):
- **The leases.** A TASL-7 audit chunk takes TASL-7's GPU lease `~/r1_locks/gpu0.lock`, which is the lease the
  proposer server holds for its whole life (`proposer.lease`; the validator requires `tasl7_audits.lease` to be it).
  So a running server keeps every TASL-7 chunk out, and a chunk keeps the server from starting. "No campaign wave holds
  the server" is checked as: the lease is free and the server's `/health` does not answer at the chunk's start
  (`g5_job.server_down`); a campaign wave needs that server, so none can run meanwhile. TASL-2's lease is unchanged.
- **One table, one GPU model.** Both cards are RTX 4090; every job record checks its card's model (`gpu_check` and the
  record's `gpu.name` against the spec's `gpu_model`).
- **Who may run there.** The G5-7 family only, in the TASL-7 checkout of the G5-7 commit
  (`/home/dowling/r1_tracks/t1_tasl/harness_g5` on TASL-7, a new checkout apart from G.1b's TASL-7 checkout, which stays
  at its pin), with the `torch312` and `jax312` environments and the extra environment (`XLA_FLAGS`) that the signed
  G.1b spec gives TASL-7. Autoresearch's audits stay on TASL-2: its `ar-cond7a` exists only there. A node whose TASL-7
  environment is not filled is refused there (`tasl7_audits.node_extra_env`); `mlgym_houseprice`'s input path there
  is filled with the xc3 spec's value (§5 PENDING table).
- **The per-node cross-host PASS** (checked by the switch at each TASL-7 job start, `check_crosshost_pass`):
  - `mlab_cifar10`, `mlgym_cifar10`, `mlgym_breakout_minatar`: both `-xc2` verdicts on `main`, bound by sha256 in the
    spec: step 1 (`xc`, the two hosts' cross-check runs, `G1B_XC2_STEP1_VERDICT_<node>_20261122.json`) and step 2
    (`preassembly`, the node's G.1b TASL-7 attempt against the TASL-2 cross-check attempt, the row's literal comparison
    and the one the G.1b assembly gate binds, `G1B_XC2_STEP2_PREASSEMBLY_VERDICT_<node>_20261124.json`). Both are
    required: step 1 shows the two hosts agree on the same code and environment, step 2 that the node's own TASL-7
    measurement equals TASL-2's.
  - `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_fmnist`, `mlgym_houseprice`: the spec carries `PENDING short cross-check:
    <node>`. Their short cross-check under the reviewed `g1b_crosscheck.py` is the xc3 unit (READY 107, on `main`;
    its note signed, R1-XC3-NOTE). The switch accepts its PASS **without a spec change**, as that unit names its
    verdicts (the signed note's `verdicts` line):
    exactly one file `docs/r1/reports/<dir>/G1B_XC3_SHORT_VERDICT_<node>_<YYYYMMDD>.json` on `main` (expected
    `docs/r1/reports/tasl_chain_20261122/G1B_XC3_SHORT_VERDICT_<node>_20261125.json`): schema
    `g1b_tasl_crosscheck_verdict/1`, this node, mode `short`, rule R1-G5-AUDIT-TWO-CARDS, verdict PASS with no reason,
    the seven nodes' G.1b pin, signed spec and run, and both hosts in `sides` (each with `run_id`, `spec_sha256`,
    `job_record_sha256`, `attempt`; the TASL-2 side's `run_id` is the G.1b run, the TASL-7 side's `<xc3 run>-TASL-7`),
    `label` ENGINEERING_ONLY and `complete: true`, and the xc3 run id: the xc3 spec's where it is on `main`, else the
    signed note's, else one carrying `g1b-tasl-20261121-b-xc3-` (on `main` `f1f1b651`: the xc3 spec's run
    `g1b-tasl-20261121-b-xc3-a`). Only a `.json` named exactly so directly under `docs/r1/reports/<dir>/` counts;
    copies in a `*_captures/` subtree are ignored; any other `.json` naming the node's token, or two files, is refused.
    The xc3 spec is bound through the signed note (its `run_id` and `xc_spec_sha256` `fc064ded…`, checked against
    the spec on `main`); no short verdict is on `main` yet. The verdict's path and sha256 go into the
    launch context, the claim and the TASL-7 job record, and are checked again at the registration. Until such a file
    exists the node may not run on TASL-7 (fail closed), but runs on TASL-2; the placeholders do not block the launch.
  - **The coupling with the xc3 note** (review round 1, M3). The switch reads XC3-FAIL and `skip_nodes` from
    published `main`: the signed xc3 note `docs/r1/authorizations/g1b_xc_short_t1_tasl_<YYYYMMDD>.md` (exactly one
    such file; it must read `approved: true`, exactly one `xc3_fail: A|B` line, exactly one `xc3_cap` line reading
    `R1-G1B-CAP` or `G5-CAP`, `skip_nodes` `none` or some of the four nodes with no empty entry, and, where the xc3 spec
    is on `main`, that spec's `run_id` and `xc_spec_sha256`) and the PLAN row R1-XC3-FAIL-READING its report proposes
    (at most once; the row must carry the sentence `The xc3 note carries xc3_fail: A.` or `... B.` exactly once). Where
    both exist they must agree, or every short-check node's jobs STOP. With neither on `main` the reading is "A
    pending": no short verdict can exist without a run under the signed note, and those nodes stay on TASL-2. A node in
    `skip_nodes` has no short check and stays on TASL-2 under either option. *(Revision 12:)* the xc3 unit is on
    `main` (READY 107), so the switch no longer carries a copy of its rules: it imports `g1b_crosscheck.short_decisions`
    (the note's `xc3_fail`, `xc3_cap` and `skip_nodes`) and `g1b_crosscheck.xc3_fail_row_option` (the row's sentence),
    and the 20 recorded cases of review round 2, N4 run through them and through the switch's reader with the same
    outcomes. `check_xc_note` is not used: it checks a note file on disk against the xc3 spec file and the paper
    commit for the xc3 launch, while the switch reads the note from `main`. **On `main` `f1f1b651` the switch reads
    XC3-FAIL A** from the signed note `authorizations/g1b_xc_short_t1_tasl_20261126.md` and from R1-XC3-FAIL-READING,
    which agree, with `skip_nodes` none; the note binds the xc3 spec on `main` (`fc064ded…`) and its run id.
  - Every refusal refuses only that node's TASL-7 chunk.
  - **XC3-FAIL — signed A** (R1-XC3-FAIL-READING and the xc3 note's `xc3_fail: A`, 26 Nov). **Both options are built
    behind the value on `main`**, and G.5 follows the signed one, A. **A**: a failed (STOP) or missing short check only
    keeps that node's audits off TASL-7; it still runs on TASL-2 and stays in G.5 and PRE-T1. **B** (not chosen):
    R1-T1-D21-SCOPE read literally ("passed … where run, the cross-host check"): a node whose short check was run and
    did not PASS (a committed short verdict reading `verdict: STOP`) leaves G.5: STOP 5 at every job start of that
    node, TASL-2 included (`g5_tasl.xc3_b_check`); a node without a verdict yet, or with a PASS, goes on; a skipped node
    is not affected; a verdict file that cannot be read as a short verdict refuses that node's jobs. The B STOP is
    recorded by the switch in the table's runs tree as `<run_id>/<node>/_switch_stop.json` (`stop_class: node`, the
    verdict path and sha256, the rule, the time; written once, on TASL-2 only), which the order check and the seal
    read, so the node and the run can still be sealed (review round 2, N1; §4 "After a node STOP"). Under the signed A
    the B path does not fire.
  - **During G.5 the xc3 unit must not commit a second signed note (or any second file under the note's name
    pattern) or a changed xc3 spec on `main`** without a G.5 code change: the switch reads them at every job start of
    the four short-check nodes, and any of these makes it refuse every job of those nodes (STOP, TASL-2 included),
    whatever the option, until that code change (review round 2).
- **The TASL-7 host check record** `reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md`
  (sha256 `09945c15…`; `host_check_items: 1-7 PASS` at `c025f89a`, item 7 untested as on TASL-2) is the record the
  signed G.1b spec gives TASL-7. The switch checks it on `main` at every TASL-7 job start, and the note cites it in P1
  and in the `tasl7_audits` line (`check_note` requires P1 to name it).
- **The order and the state** (the runs tree on TASL-2 stays the table's tree):
  1. TASL-2 runs a wave's first audit chunk, which makes the wave's plan (as before).
  2. On TASL-2, `g5_tasl.py claim-chunk <spec> --node <n> --wave <w> --chunk <i>` claims one chunk for TASL-7, only
     for a node that can run there now (review round 1, M1): the G5-7 family, G5-TASL-GPUH A, no placeholder in its
     TASL-7 environment, the TASL-7 host check record on `main`, and its cross-host PASS on `main` (the same check as
     the switch's, with XC3-FAIL and `skip_nodes`). Never the wave's last chunk (it computes E5 over the wave), never a
     chunk TASL-2 started, only while no other claim is open (one TASL-7 chunk at a time), and not after the final
     TASL-7 log registration (step 6). It holds the flock `_remote/claims.lock`, which TASL-2's audit jobs also hold
     from choosing their chunk to creating its attempt. It records the plan's sha256s, K, the TASL-2 meter reading, the
     registered TASL-7 attempts that reading includes, and the PASS records it checked. Before claiming, and before a
     TASL-7 job, the operator fetches `origin` in the checkout used (the checks read published `main`).
  3. The operator copies the claim and the wave's `plan_index.json` and `plan.tar` byte-identically into TASL-7's runs
     tree (same layout), and runs `t1_tasl_node.sh g5t7 <spec> <node> <note> audits-wave<w> <i> --enable` on TASL-7.
     The job reads the plan with an access-log line on TASL-7, runs exactly the claimed chunk, and writes no plan, no
     K lock and no wave checks.
  4. **Every TASL-7 attempt must be registered.** Each attempt directory, TASL-7's `_access_log.jsonl` and the node
     wrapper log its record names are copied back, and `g5_tasl.py register-chunk <spec> <attempt dir> --node --wave
     --chunk --access-log <copy> [--node-log <copy>]` files them into TASL-2's runs tree, in order (attempt N only
     after N − 1), and only into an open claim. Checked: sums, record, claim and plan, the record's `crosshost_pass`
     non-null and equal to the claim's (checked on `main` at the claim, and by the switch at the run; the check on
     `main` at registration time is recorded for information only and never blocks the accounting; review round 2,
     N2), the access log passes STOP 11 and extends the one registered before. Only then does the attempt count for
     the meter, the STOP records, E5, the wave checks and the seal. A
     crashed TASL-7 attempt is closed on TASL-7 (`close-attempt`) and registered like any other. TASL-7's `_refusals/`
     (refusal texts before any attempt) stay on TASL-7 and are not sealed (disclosed).
  5. TASL-2 never runs a claimed chunk; the wave's last chunk waits until every claimed chunk is closed (a registered
     attempt complete or ended in an author STOP). A claim TASL-7 cannot finish is handed back by `g5_tasl.py
     abandon-claim <spec> --node --wave --chunk --reason <text> --access-log <copy>` (review round 1, M1): only while
     the claim is open, with a reason, after registering TASL-7's access log in the same call, and with the operator's
     confirmation that every TASL-7 attempt of the chunk is registered (the code cannot see TASL-7's tree). Effect: the
     chunk is TASL-2's again (a later attempt number in the same chunk directory); nothing more is registered into the
     claim; the record lies under `_remote/abandoned/` and is sealed with the run. **The operator copies the abandon
     record to TASL-7 (same path) before any further TASL-7 job**; a TASL-7 job refuses a chunk whose abandon record
     is present (review round 2, N3).
  6. After TASL-7's last G.5 job, `g5_tasl.py finalize-remote <spec> --access-log <copy>` registers TASL-7's access
     log a last time (no claim may be open; afterwards no claim, registration or abandonment is accepted).
     `seal_node` refuses while the node has an open claim, and `seal_run` while any claim is open or, if TASL-7 had
     claims, without that final registration after every other TASL-7 record (review round 1, M2).
- **The meter** (STOP 9, worker card under G5-TASL-GPUH A): a TASL-7 audit chunk is worker-card time and counts
  against the cap once registered. At a TASL-7 job start the check adds to the claim's TASL-2 reading only the TASL-7
  job records the claim does not already list as registered. TASL-7 chunks are refused under G5-TASL-GPUH B.
- **Mixed-host labels** (disclosed; review round 1, m6). With two cards, the units of one audit group (candidate and
  parent code states at the K seeds) and the rows E5 reads for one wave may come from different hosts' chunks, so one
  label can combine runs from TASL-2 and TASL-7. This rests on the cross-host PASS (bit-identical default-part outcomes
  on both cards for that node) and on one GPU model; the per-proposal outcomes themselves are not compared across
  hosts. The T1 report and the screening funnel (R1-BX-D12) disclose which nodes had chunks on TASL-7 (the registration
  records under `_remote/registrations/` name them).
- **The dates with TASL-7 audit chunks** *(revision 12; R1-BX-D14-G4B asks for this recompute)*. `g5_tasl.py dates
  <spec> <sealed G.4b attempts> --pilot-spec sweep2/t1_tasl/g4b_tasl_spec.json --today <date> --tasl7-audits
  [--tasl7-nodes <node> …]` adds a `tasl7_audits` block to the one-slot recompute. It moves to TASL-7 only what the
  rules above allow: audit chunks of the eligible nodes (default: the xc2 nodes with a PASS on `main`; the xc3 nodes
  are named explicitly, as a scenario until their PASS is on `main`), never a wave's first chunk (the TASL-2 job that
  makes the wave's plan takes it, so a claim is refused, `claim_chunk`) or its last chunk (E5), and never while a
  campaign wave holds the server; the wave's chunks are cut by `g5_job.chunk_plan`. **For the eight nodes this changes
  nothing:** at the G.4b figures no G5-7 node has a wave of three or more chunks (the most is two: `mlab_imdb` and
  `mlgym_breakout_minatar` in wave 2), so no chunk can move, and the dates stay labels done 11 Dec, B.7 14 Dec
  (`--today 2026-11-25`; with `--today 2026-11-26` each date is one day later). Autoresearch, whose audits are 8 of
  its 10 jobs, may not run on TASL-7. The GPU-hours are the same either way; the recommended reading counts TASL-7
  audit-chunk hours inside the 425 cap (§11.1).
- **What the note fixes (the schedule):** the phases in which the server is stopped for TASL-7 audit chunks (between
  campaign waves; the server's stop and restart follow G5-TASL-GPUH A's records and STOP 12, a restart re-checked as
  before), which nodes' chunks are claimed for TASL-7 and in which order, and that a claimed chunk runs only on
  TASL-7. The code enforces the rules above, not a timetable (change report §5).

### 2.11 G5-AR: how `autoresearch_fixedtokens` enters G.5 (decided: A, R1-G5-DECISIONS)

Autoresearch is the only autoresearch-suite T1 node. The author kept it in G.1b because it is "needed for
leave-one-suite-out" (R1-G1B-TASL-DECISIONS, R1-G1B-NOTE2-DECISIONS). The published rules decide what it is worth:
- Under R1-BX-D8-CONFIRM-V31, leave-one-suite-out STOPs unless each suite has a labelled T1 node; the aggregate gate
  does not STOP. Under PRE-SECONDARY A, leave-one-suite-out is a descriptive analysis (no verdict) with fold arms
  retrained without the held-out suite. What autoresearch adds is a third suite in the T1 stratum and a
  leave-one-suite-out analysis that does not STOP; the aggregate verdict does not depend on it.
- Under PRE-T1 A, there is one primary gate read; the T1 node set is "exactly the T1 nodes whose train/dev labels
  were released and used to freeze the arms" (each with ≥ 1 train and ≥ 1 dev instance), and "a later read with more
  T1 nodes is not allowed". So autoresearch enters any gate read only if its train/dev labels are released before the
  arms-frozen record.

What it costs (pre-pilot, `sweep2/t1_tasl/g5_ar_projection_tasl.py --today 2026-11-22`; W A, MEM A, AUDIT A):
- Its census B1 run takes 218.951 s on TASL-2's 4090 under the option-A isolation path. On the Ada, un-isolated, it took
  67.901 s (U2, 17 Nov): the census records a 3.225× cross-host option-A slowdown (bpb and VRAM not normalised). Most
  of autoresearch's cost here is that slowdown, not the node's intrinsic weight; the other nodes' times are Ada
  times (the slowest, `mlab_imdb`, 64.1 s). Its timeout basis is 767.748 s (3 × E2's 255.916 s, R1-G1B-TIMEOUT).
- Alone it needs 138.4 GPU-h at K = 10 and ran share 0.6 (campaigns 15.7, audits 118.6; 10 jobs, 8 of them audit
  chunks). That is 45 % of the eight-node total. It needs 179.8 GPU-h at share 0.8 and 89.8 at K = 6.
- Neither the G.4 pilot nor the G.4b re-pilot measures it (G4-NODE3 A, unchanged for G.4b). In the recompute (P3) it
  takes the pilot nodes' median LLM time and shares and its own TASL-2 census run time without the ratio (§8), until
  G.5's own first wave: 138.69 GPU-h of the 216.9 (8 audit chunks), the longest node.
- Its census time is already a 4090 time, so the post-pilot 4090/census ratio must not be applied to it (§8, §9).

| W | MEM | Ran share | K = 6 GPU-h (8 nodes) | K = 10 GPU-h (8 nodes) | Audited per node |
|---|---|---|---|---|---|
| A: 20 calls | A: one mode | 0.6 | 208.5 | 305.3 | 144 |
| A: 20 calls | A: one mode | 0.8 | 259.9 | 386.0 | 192 |
| A: 20 calls | B: both | 0.6 | 417.0 | 610.7 | 288 |
| A: 20 calls | B: both | 0.8 | 519.8 | 772.1 | 384 |
| B: 20 runs, cap 80 calls | A: one mode | 0.6 | 334.9 | 489.5 | 240 |
| B: 20 runs, cap 80 calls | A: one mode | 0.8 | 320.9 | 475.5 | 240 |

Dates with autoresearch, one worker slot (G5-SLOT A). The table assumes 2 days of remaining G.1b before the labels,
because autoresearch's G.1b (≈ 28.2 GPU-h) and the TASL-2 G.1b work share TASL-2. With 1 day, each B.7 is one day
earlier. R1-G5-DECISIONS accepted the first row's B.7 (about 15 Dec). The AR host check at `2d09f9a9` first STOPped on
22 Nov; after R1-G1B-AR-PY its rerun is PASS and the third note is signed, but no result of autoresearch's G.1b is on
`main`, so it may start later than this assumes; the recompute on the G.4b re-pilot (P3, P7) takes the actual state.

| K | Case | GPU-h | Labels done | B.7 | Slack against 8 Dec |
|---|---|---|---|---|---|
| 10 | share 0.6, LLM 60 s | 305.3 | 12 Dec | 15 Dec | −7 |
| 10 | share 0.8 | 386.0 | 16 Dec | 19 Dec | −11 |
| 10 | LLM 120 s | 337.3 | 14 Dec | 17 Dec | −9 |
| 6 (K-check PASS row only) | share 0.6, LLM 60 s | 208.5 | 8 Dec | 11 Dec | −3 |
| 6 (K-check PASS row only) | share 0.8 | 259.9 | 10 Dec | 13 Dec | −5 |

D.3 and the manuscript move with B.7 (the recompute shifts them by R1-BX-D14's spans). At K = 10 and share 0.6 that
gives D.3 10 Jan and the manuscript 17 Jan.

*(Revision 12.)* The G.4b recompute (P3; `g5_tasl.py dates <spec> <sealed G.4b attempts> --pilot-spec
sweep2/t1_tasl/g4b_tasl_spec.json --today 2026-11-25`, the G.4b result's `dates_g5.json`): 216.9 GPU-h at K = 10,
labels done 11 Dec, B.7 14 Dec 2026, D.3 9 Jan 2027, manuscript 16 Jan 2027. R1-BX-D14-G4B adopted it as the target
(G4B-DATES A); the table above stays as the pre-pilot record.

- **A (decided): eight nodes in one G.5 table, the same design for every node.** Autoresearch runs 12 instances
  under the same W, memory mode, temperature, K, audit, divergence and STOP rules.
  - Its own prerequisites gate only its own jobs; the seven nodes may start before them (under G5-ARPEND A, §2.13;
    under G5-ARPEND B the signature waits for them). They are: its G.1b noise floor under the third note (signed;
    P2, P10); its environment for G.5 (P9); the TASL-2 host check at its pin (PASS, `cce9b8fb…`; P1); and its
    REL-T1-G1B summary copy. The G5-PIN B commits (P5) are needed before any G.5 job.
  - Cap: 425 GPU-h (§2.6).
  - The date change goes to the author under R1-BX-D14 with the post-pilot numbers (P7), before it is applied.
  - **The freeze wait** *(proposed rule; review M3, round 2 m4)*. Under PRE-T1 A the arms-frozen record fixes the T1
    node set once. The arms-frozen record therefore **waits for the train/dev release of every T1 node of this table
    that has not STOPped** (autoresearch included; the T1 train/dev release row naming them, §6). The deadline is a
    release date: **18 Dec 2026** *(proposed)*: the projected labels-done date at K = 10 and share 0.8 (16 Dec) plus 2
    days for the REL-T1-G1B copies and the release row (B.7 then about 21 Dec), recomputed with P7 and fixed in the
    signed note. Without that margin STOP 14 would fire by construction in the worst projected case. If a node's release has
    not happened by then (a late node, autoresearch's prerequisites still PENDING, or the wave not finished), or a
    node STOPs at G.5, the coordinating agent STOPs for the author (STOP 14). Only an author row may then freeze the
    arms without that node; under PRE-T1 A it then enters no gate read (for autoresearch, leave-one-suite-out also
    STOPs in the descriptive analysis). No agent freezes the arms without a node on its own. For this table, this
    rule refines R1-BX-D8-CONFIRM-V31's "if only some T1 nodes have labels by B.7, read … on the available labelled T1
    nodes": the available nodes are fixed by the author, not by timing.
  - G5-SLOT B (audits also on TASL-7) would shorten the span by about a third; it is not built. *(Revision 11:)*
    R1-G5-AUDIT-TWO-CARDS amends A instead (audit chunks on TASL-7 while no campaign wave holds the server, §2.10).
    *(Revision 12:)* the dates tool now counts TASL-7 audit chunks; for these eight nodes it moves no chunk (§2.10).
  - **The expansion nodes** *(revision 12, R1-G5-EXPANSION-JOIN)*. G.5 launches on these eight nodes. An
    R1-T1-NODE-EXPANSION candidate whose G.1b completes with determinism PASS by 2 Dec 2026 joins through a **G.5
    addendum note** with the same code, K and rules. *(proposed)* path:
    `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>_addendum_<N>.md`, citing the signed note by path and sha256, the
    candidate's G.1b note and result, and the R1-BX-D14-G4B recompute with that node. **Not built:** the switch reads
    only the note named by the spec's `run_id` and only the eight nodes of the split file and the spec; a joining node
    needs a spec entry, a split-file assignment and a reviewed code unit that reads the addendum (§9, §11.1). Until
    2 Dec the expansion G.1b jobs take precedence on the TASL cards.
- **B (not chosen): seven nodes in G.5; autoresearch by a later amendment.** The cap would have stayed 230 GPU-h.
  Like for like (2 days of remaining G.1b in both, autoresearch's G.1b ordered by R1-G1B-NOTE2-DECISIONS either way),
  B.7 would have been 9 Dec against A's 15 Dec, 6 days earlier; with 1 day, 8 against 14 Dec. Autoresearch's labels
  would have come about 6 days after the seven on the one slot. Under PRE-T1 A they would have entered a gate read
  only if the arms-frozen record waited for them (the same days as A plus a second note, a review and an amendment);
  without that wait, autoresearch would have entered **no** gate read unless the preregistration were amended, and
  leave-one-suite-out would have STOPped.
- **C (not chosen): autoresearch with fewer instances or audits** (for example 6 instances, 3 of them test, exactly
  at the floor). About half its cost, but it contradicts V3-B's 12 instances per node and the split file's 12.

### 2.12 G5-PIN: two G.1b harness pins (decided: B, R1-G5-DECISIONS)

The seven nodes' noise floors come from harness `c025f89a`; autoresearch's will come from `2d09f9a9` (third note).
P5 requires the G.5 harness commit to descend from the G.1b pin, with the measurement path byte-identical, so that the
noise floor and the labels share it.

Commit `2d09f9a9` descends from `c025f89a` and changes files inside that path:
- autoresearch's node directory and its config;
- `src/autoresearch/trackg/node_lib/ar_isolated.py`, the master that `isolation.py` loads for its sandbox probe. Its
  diff is a docstring and `torch.cuda.init()` inside the compatibility helper `cuda_open`, which no node uses.

No single G.5 commit is therefore byte-identical over the whole path to both pins.

- **B (decided): two G.5 harness commits with byte-identical G.5 code.**
  - `G5-7` descends from `c025f89a` and carries the seven nodes; `G5-AR` descends from `2d09f9a9` and carries
    autoresearch. Each node's G.5 jobs run on the commit of its own G.1b noise floor.
  - **The check that enforces it** (built in revision 8: `sweep2/t1_tasl/g5_pin_check.py`, tests
    `r1/tests/test_t1_tasl_g5_pin_check.py`). For the whole tree, not a list of G.5 files:
    1. `G5-7` descends from `c025f89a`, `G5-AR` from `2d09f9a9`, and `2d09f9a9` from `c025f89a`;
    2. the paths that differ between `G5-7` and `G5-AR` are exactly the paths that differ between the two pins (the
       pin delta: autoresearch's node and config files, `node_lib/ar_isolated.py`, a report, tests);
    3. on each pin-delta path, `G5-7` holds `c025f89a`'s blob and `G5-AR` holds `2d09f9a9`'s.
    So every file outside the pin delta, everything G.5 adds or changes included, is byte-identical between the two
    commits, and G.5 changes no pin-delta file. On the real harness the two pins themselves pass. *(Revision 10:)* the
    reviewed engines are at G5-7 `52e3c0b0` and G5-AR `00829da1` (as the follow-ups report cites them). *(Revision
    12:)* the recount unit of R1-G5-DIFF-RECOUNT gave both successors, G5-7 `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98`
    and G5-AR `ccdb3774f60dbca21adc918777a0ddd2e6e634f8` (pushed; review record in the harness repository), and they
    are the spec's `harness_families.<family>.g5_commit`. At the desk on the harness repository: `g5_pin_check.py`
    passes on the pair (pin delta of 10 paths; the G.5 changes, `audit_g5.py`, `campaign_v2_diff.py`, the reclassify
    script, reports and tests, identical in both), and `measurement_path_check` passes per family (308 files, the
    15-file `noise_floor` closure, no engine file in it, no addition in the measurement directories other than
    `audit_g5.py`).
    The G.5 switch runs it at every job start, with the two commits from the note (§5), and STOPs on any failure
    (STOP 13).
  - The literal P5 holds within each family (each G.5 commit against its own G.1b pin), checked separately (§7 P5).
  - There are two harness checkouts on TASL-2, as G.1b already has for autoresearch (the third note's second
    checkout). A node launched from the other family's checkout STOPs (§4 item 13).
- **A (not chosen): one G.5 commit descending from `2d09f9a9`, with P5 per node** (the seven nodes checked against
  `c025f89a` except the pin-delta files, bound by sha256); it would have weakened P5's literal byte-identity.

### 2.13 G5-ARPEND: autoresearch's own prerequisites at signature (decided: A, R1-G5-DECISIONS-2)

Autoresearch's prerequisites are independent of the seven nodes': the TASL-2 host check at `2d09f9a9` (P1), its G.1b
under the third note with its D21 verdict (P2), its environment for G.5 (P9), its Student-t or Gaussian declaration
(P10), and its REL-T1-G1B summary copy (§3, §5 `noise_floor`). State on `main` `89899f76`: the host check is PASS
(`TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md`, sha256 `cce9b8fb…`, after R1-G1B-AR-PY) and the third note is
signed (`g1b_ar_t1_tasl_20261122.md`); no result of its G.1b is on `main`, so the D21 verdict, the summary copy and P10
are still open. The environment is `ar-cond7a` as amended by R1-G1B-AR-PY (freeze `11def6ad…`, Python 3.12.15).

- **A (recommended): PENDING at signature, completed by a record.** The signed note may record these five items for
  autoresearch as PENDING. The G.5 switch refuses autoresearch's jobs until a **completion record** is on `main`:
  `docs/r1/reports/<dir>/G5_AR_PREREQUISITES_<YYYYMMDD>.md`, citing, each with path and sha256, the host-check binding
  record at `2d09f9a9` (now PASS, `cce9b8fb…`), the third note (now signed) and its sealed G.1b summary with the D21
  verdict, the REL-T1-G1B copy of that summary, the P10 declaration, and the environment (`ar-cond7a` freeze
  `11def6ad…` under R1-G1B-AR-ENV as amended by R1-G1B-AR-PY). The coordinating chat commits it after an independent
  review, **without a further author decision**, as for note 2 under R1-G1B-NOTE2-DECISIONS. **Neither the spec nor
  the signed note changes:** the spec carries PENDING markers in place of autoresearch's host check, summary copy,
  environment and P10 declaration (`ar_prerequisites.pending`: `host_check`, `noise_floor_copy`, `environment`,
  `tails`), and the note's `noise_floor`, `environments`, `tails` and `ar_prerequisites` lines name the completion
  record's path pattern; the switch reads these items from the record on `main` and checks every cited sha256 (STOP
  15), so the spec sha256 the note binds stays the same and no launch commit is re-issued.
  - **The record format is the one part 3a built** (`g5_tasl.check_ar_record`; `g5_tasl.py check-ar-record`): exactly
    one file on `main` matching the pattern (none, two or more, or a near-miss name outside `docs/r1/reviews/` is STOP
    15); `key: value` lines `schema: g5_ar_prerequisites/1`, `node: autoresearch_fixedtokens`, `verdict: PASS`,
    `g5_spec_sha256` (the signed spec's sha256), `review` (an independent review on `main` naming the record's path
    and sha256, `Verdict: ACCEPTED`), `host_check`, `g1b_note`, `noise_floor_copy`, `noise_floor_copy_review` (under
    D6 A of R1-T1-FEAT-DECISIONS the copy's `ASSEMBLY.json` and `runs.jsonl` lie beside it on `main` and this review
    must name both with their sha256s; the format itself is unchanged, §3),
    `g1b_sealed_summary`, `d21_verdict`, `tails` (`gaussian` or `student_t`), `tails_declaration` and `environment`
    (`<name> freeze <path> sha256 <hex> python <x.y.z> interpreter <abs path>`), plus `environment_row` for an
    environment other than the proposed `ar-cond7a`, a row that must name that environment and "G.5".
  - The seven nodes start without waiting; the freeze wait (§2.11) bounds how late autoresearch may come.
- **B: the signature waits for all of them.** Then the seven nodes do not start before autoresearch's G.1b has
  a result and its copy and P10 exist, and the dates of §2.11 move by however long that takes. (Under B the switch
  does not check the third G.1b note itself; under A the completion record binds it. Part 3a report §8.)

## 3. What the label table is, and the order of work

For each T1 node:
- 12 root campaign instances of `run_v2_diff_campaign`, memory mode per G5-MEM, W per G5-W, temperature per
  G5-TEMP, with the record gate (`noise_floor.check_effective`) and the timeout basis of the table's noise floor
  (§4 item 8).
- **Order:** (1) wave-1 campaigns (instances 1–4); (2) wave-1 audits; (3) the G5-DIV, band, liveness and invalid-share
  checks on the sealed diagnostics; (4) wave-2 campaigns (instances 5–12); (5) wave-2 audits; (6) the checks again.
  A STOP at (3) halts the node before wave 2. In the built job these are the four jobs `campaigns-wave1`,
  `audits-wave1`, `campaigns-wave2`, `audits-wave2` (`g5_tasl.py run`), with the checks as `g5_tasl.py wave-checks`
  (written once per wave, `wave_checks_wave<N>.json`).
- Audits per G5-AUDIT: paired fresh-seed re-runs of the proposal's code state and its parent incumbent at the K audit
  seeds with joint seeds (training seed = split seed = s, `"vary"` split), so each seed gives a paired d_s, as in
  C3_DESIGN §4 and the sweep-1 B.2 audit. Audits run in chunks, each under the walltime limit. A cross-instance group
  audited in wave 1 is carried into wave 2, not audited again (part 3b-1 report §5 item 4; a reading proposed for the
  note, §5).
- Labels and keep decisions use the validation metric. The sealed task test metric is never read for labels or
  selection.

The soft-label width comes from the G.1b noise floor on the same RTX 4090 environment (TASL-2 or TASL-7, the same
census freeze and harness pin; R1-T1-HOST-TASL), and the width is s = σ̂_node/√K_label (R1-BX-D3). **σ̂_node is
T0's definition** (R1-T1-FEAT-DECISIONS D6-σ B; `dataset.noise_table`'s rule), computed from the node's G.1b
`runs.jsonl`:
- per declared edit k, the sd (numpy, ddof 1) over the joint-seed condition (seeds 3001–3030, `"vary"` split) of
  m(c_k, s) − m(c0, s), from successful runs with a metric, with at least three paired seeds;
- an edit is material if it is resolved (|Δ̂_J| > 2 se, or Δ̂_J ≠ 0 when se = 0) and |Δ̂_J| ≥ 0.002 (as in
  `e1_report`);
- σ̂_node is the median of these sds over the material edits, or over all edits with an sd if none is material.

**Which nodes (R1-T1-D21-SCOPE, revision 11).** D21 does not select T1 nodes: every T1 node that passed U2, G.1b
fixed-seed determinism and, where run, the cross-host check is in the table, whatever its D21 value; no other
threshold is introduced. Under D21 only `mlgym_breakout_minatar` and `mlgym_houseprice` qualify (the row's figures), so
most nodes enter as non-qualifying nodes. For them the definition above is unchanged and still has to give a usable
value:
- A non-qualifying node may have fewer than two material edits. With one, σ̂_node is that edit's sd; with none, the
  fallback, the median over all edits with an sd. D21's own `σ_joint > 0` check does not apply to σ̂_node.
- The fallback is still required to be finite and > 0, and δ_n finite and > 0 (`g5_noise.check_usable`, the switch's
  noise pre-check and the assembly): σ̂_node scales the soft-label width s = σ̂_node/√K_label and the gain z-scores, so a
  zero or non-finite value cannot make labels. A node whose paired differences do not vary across seeds (sd 0 on every
  edit used), or with no edit of three paired seeds, therefore still STOPs; that is the existing STOP, not a new
  threshold.
- Each node's D21 value (the verdict, the material-edit count, the mean P(wrong) over the material edits and the rule's
  checks; `g5_tasl.g1b_verdict_scope`) is recorded: in the switch's launch context, as `d21` in `build.json`'s node
  entry and in the T1 noise record (`g5_noise.derive`), and, as before, in the REL-T1-G1B copy record's `d21_verdict`.
  The screening funnel (R1-BX-D12) reads it from the noise record or `build.json`.
- *(R1-G5-AUDIT-TWO-CARDS.)* A node's labels may combine audit runs from both cards (§2.10, "Mixed-host labels"); the
  funnel discloses, per node, its D21 value and whether any of its audit chunks ran on TASL-7.

From the same run, δ_n is D18 unscaled (PRE-DELTA A): max(0.002, 0.25 × the median of the sds over all edits with
an sd); the 0.002 floor applies as preregistered (R1-T1-FEAT-DECISIONS). σ_node scales the soft-label width and g,
and enters the table bytes (the rows' `sigma_node` and `sigma_cmp`, the features' `recorded_gain_z`, `build.json`).
- **The source** follows the row's reading of PRE-DELTA for T1: "T1's σ_node and δ_n both come from the `runs.jsonl`
  copies bound by sha256 to each G.1b summary; the preregistration itself is unchanged". The summary carries no
  median paired sd, so neither value can be read from its fields. The binding: the summary copy's `assembly_sha256`
  is the sha256 of the `ASSEMBLY.json` copy beside it, whose `runs_sha256` is the sha256 of the `runs.jsonl` copy,
  and the edit and paired-seed counts must equal the summary's `n_edits` and `paired_joint_n`.
- **One value, by construction.** `g5_assemble.noise_by_node` (the table) calls `g5_noise.node_delta` on the
  committed copies, selected by the spec field `noise_floor.t1_sigma_node: "t0_definition"`; the validator and
  `noise_by_node` refuse any other value or a missing one. `g5_noise.derive` (the T1 noise record of the gate run,
  schema `g5_t1_noise/2`) takes its values from `noise_by_node`, so the record and the table carry the same σ_node
  and δ_n.
- **The summary's `sigma_joint`** (the sd of the baseline's own runs over the joint seeds, which revision 9 named as
  σ̂_node) is no longer used for σ̂_node: that path is removed from the code. It is still reported, in `build.json`
  (`nodes.<node>.sigma_joint`) and in the noise record.

Before any label is assembled, each node is declared Gaussian or Student-t from the G.1b summary (E5; prerequisite
P10). The seven nodes'
summary is that of run `g1b-tasl-20261121-b`, assembled from both hosts' sealed node directories: the first note's
three sealed TASL-2 attempts and the attempts under the spec re-issued by R1-T1-DATA-MANIFEST, joined under R1-G1B-JOIN
(`g1b_tasl_join.py assemble`, behind the cross-check gate, which writes `crosscheck_gate.json`). Autoresearch's is that of
`g1b-ar-tasl-20261122-a`, in the `ar-cond7a` environment at harness `2d09f9a9`. Each summary reaches G.5 through the
**REL-T1-G1B step** (R1-SWEEP2-RELEASE-DECISIONS): copied out of the sealed tree by a reviewed step, with its sha256,
before the T1 train/dev release row, which records the path and sha256 (PRE-DELTA A). **Its copy list is amended by
R1-T1-FEAT-DECISIONS D6 A:** each G.1b run's `ASSEMBLY.json` and `runs.jsonl` are copied beside the summary copy, and
σ̂_node and δ_n are computed on those copies (above). The train/dev row still cites only the summary copies; they pin
the run copies through the hash chain. The step was built in part 3b-2 and extended by READY 97:
`g5_tasl.py rel-copy <spec> --kind seven|ar --summary <sealed summary.json> --dest docs/r1/reports/<…>`
(`g5_relcopy.py`).
- It requires the summary under the G.1b spec's sealed root (`sealed_g1b`, no symlink on the path), so the joined,
  gated seven-node run directory is written there first. It applies the `refuse_sealed` check to every source before
  opening it, and `ASSEMBLY.json` and `runs.jsonl` must be regular files.
- It STOPs, writing nothing, on a `runs.jsonl` record with any seed field in 7001–7010 (the G.5 label and evaluation
  seeds), and on a node with a qualifying (or counted) verdict whose edit and paired-seed counts in `runs.jsonl` differ
  from the summary's `n_edits` and `paired_joint_n`.
- It copies `summary.json`, `ASSEMBLY.json`, `runs.jsonl` and, for the seven nodes, `crosscheck_gate.json`
  byte-identically into a new directory with `COPY_RECORD.json`, and prints the spec fields and what the copy's review
  must name (now also the `ASSEMBLY.json` and `runs.jsonl` copies with their sha256s).

The spec names the seven-node copy, its cross-check gate copy, its `ASSEMBLY.json` and `runs.jsonl` copies
(`noise_floor.seven`'s `assembly_copy`, `assembly_sha256`, `runs_copy`, `runs_sha256`, PENDING now) and their sha256s.
At launch the two run-copy paths must be `ASSEMBLY.json` and `runs.jsonl` beside the summary copy. The note's
`noise_floor` line names only the summary and gate copies (§5); it binds the spec by its sha256, and the summary's
sha256 pins the run copies. Autoresearch's copy is named the same way under G5-ARPEND B; under G5-ARPEND A the spec
carries PENDING markers for autoresearch's host check, copy (the four run-copy fields included), environment and P10
declaration. The switch takes them from the completion record on `main`, checked by sha256 (§2.13, STOP 15). The
record's format is unchanged: its `noise_floor_copy` names the summary copy, the run copies are the files beside it,
and the copy's review (`noise_floor_copy_review`) must name both with their sha256s. At every job start the switch
checks the run copies on `main` against the chain (`check_g1b_copy`, `run_copies`). For autoresearch's jobs it then
joins the two floors by node (`g1b_tasl_join.noise_floor_by_node`; the split file's eight T1 nodes).

**Checkouts.** The paper-repo checkouts are kept apart, as for G.1b and G.4:
- G.1b's first note ran from `985dd45d` (or its docs-only child `dbdbd2b6`), as the first G.4 note stated. The TASL
  launch chain of R1-T1-DATA-MANIFEST is published (launch table `reports/tasl_chain_20261122/LAUNCH_TABLE.md`): the
  amendment note and note 2 launch from chain commit (a) `34a5b1d6`, the cross-check (`-xc2`) from (b) `b5824240`,
  the G.4 pilot from (c) `6ad899e0`, and autoresearch's G.1b from (d) `d52c9d9d`, each or a docs-only descendant.
- G.5 launches from its own published checkout, at or after the commit that publishes the G.5 note and spec, whose
  code equals the note's `paper_commit` outside `docs/` and the spec (the TASL launch binding, §9).
- The G.5 job reads the G.1b summaries and runs only as the REL-T1-G1B copies (the summary, `ASSEMBLY.json` and
  `runs.jsonl` copies), by path and sha256 (above), never from the sealed run directories or through another
  launch's checkout.

The harness checkouts are per G5-PIN.

## 4. STOPs

Every G.1b STOP (plan §7) and every G.4 STOP (plan §7) applies to the G.5 jobs: spec and authority, host identity,
the GPU lease and foreign compute processes, root uid, GPU UUID and model, Yama `ptrace_scope`, the delegated scope,
the harness checkout at the pin and clean, environment freeze, data manifest, GGUF and `llama-server` sha256 and
build on TASL-7, the server's `/props` before and after each wave, the 4090 timing STOP, the deadline, and the launch
binding. In addition:

1. **Divergence** (G5-DIV). The rule the author chooses, evaluated as stated there. The STOP halts the node; a move
   to T2 needs a separate author row.
2. **Isolation.** Any run record that is not `effective: true` with empty waivers and exceptions STOPs that job
   (`stop_unisolated`), with the evidence kept. No waiver for label runs.
3. **Diff liveness** (D4). *(proposed)* A node whose ran-of-valid share is below 0.25 (absolute; the same for every
   node) after wave 1 STOPs. The author decides between a single-parameter fallback and T2.
4. **Proposer output.** A truncated reply is invalid (completion cap 4,096 tokens). A node whose invalid share
   (parse failures, truncations, refusals) exceeds 0.2 of its manager calls in a wave STOPs (as sweep 2's
   `max_parse_failure_rate`). A prompt longer than 32,768 − 4,096 tokens STOPs the campaign. The built counters read
   "refusals" as model refusals (recorded as parse failures); diff refusals (`not_run_refused`) count toward D4
   liveness (STOP 3), not here (part 3b-1 report §5 item 3; the proposed reading `invalid_share_counting`, §5).
5. **Noise floor.** *(Revision 11, R1-T1-D21-SCOPE.)* A node that failed G.1b fixed-seed determinism is not run in
   G.5: a STOP for that node; the author decides on T2 (R1-BX-D12 discloses it). No node is dropped silently. As
   built, STOP 5 tests the node's verdict in the REL-T1-G1B copy for a determinism PASS (`determinism.deterministic:
   true`, not the summary's "fixed-seed determinism failed" verdict; a verdict without a determinism result is not a
   PASS). **D21 does not select:** a node that does not qualify under D21 is recorded (its D21 value in the launch
   context, `build.json` and the noise record, §3), not STOPped. The G.1b cross-host gate still STOPs where it ran: the
   seven-node copy must carry the cross-check gate record naming the three TASL-7 nodes and binding its assembly
   (`check_g1b_copy`), or every job STOPs. The switch requires R1-T1-D21-SCOPE on `main`. **The noise pre-check**
   (READY 97, review m6) follows it at every job start, before the freeze-wait check and before any job runs:
   `g5_tasl.noise_precheck` reads the node's summary copy and its `ASSEMBLY.json` and `runs.jsonl` copies from
   published `main` and computes σ̂_node and δ_n with the table's code (`g5_noise.node_noise`, then `check_usable`).
   The job STOPs unless σ̂_node (T0's definition) is finite and > 0 and δ_n is finite and > 0; a non-finite per-edit
   sd or median is a STOP too. This STOP has no number of its own; the switch raises it as a plain STOP, not as STOP
   5's node STOP. The values go into the launch context (`noise_precheck`). The assembly repeats both tests on the
   copies (§6).
6. **Integrity, transport, baseline.** A `stop_integrity`, `stop_transport` or `baseline_failed` ledger line STOPs
   that job. A failed job is resubmitted only as a new attempt after diagnosis, never resumed.
7. **Infrastructure.** Final infrastructure failures (after 2 reruns) above 5 % of a node's proposals STOP the node
   *(proposed)*.
8. **Timeout.** The basis is R1-G1B-TIMEOUT's `census_slowest_x3` (decided), so the noise floor and the labels share
   it (on the 4090, a G.1b run reaching it is already a STOP). A timeout is the proposal's divergent failure (E5 over
   the label seeds). A **baseline** timeout STOPs the campaign. In an audit, a baseline timeout at a label seed is
   this timing STOP, and any other divergence of the baseline there is a node STOP, as `baseline_failed` (part 3b-1
   report §5 item 5; the proposed reading `audit_baseline`, §5).
9. **Budget.** The projection or the consumed GPU-hours above the cap (G5-CAP; worker card per G5-TASL-GPUH); a job
   past its declared deadline; *(proposed)* an audited count per node after wave 1, extrapolated to 12 instances, outside the band of G5-W (100–200 under A, 150–240 under B; doubled under MEM B). The cross-instance
   duplicate share seen in 4 instances understates the share for 12, so the extrapolation overstates the audited count.
   The author then decides: accept, change W, or cap the audits. The built counters count audited groups (unique
   audited proposals) for this band and for STOP 1's denominator, members beside them (proposed reading
   `audit_once_across_waves`, §5). As built, a missed audit-chunk deadline is a node STOP (the author decides; part 3b-1 review m5 and its fix in the 3b-1 report §6: "Both deadline STOPs are node class").
10. **Seeds.** Any use of the evaluation seeds outside the audit's evaluation block, or, when K = 6, of seeds 7004–7005
    (label) or 7009–7010 (evaluation), is a STOP (as the preregistration's §3 and §6). The G.5 validator refuses
    every other reserved block (below).
11. **Reading.** Any read of sealed content before its release step (§6) is a STOP and is reported. In the built
    code every opening of sealed content goes through the access-logged reader (`g5_seal.SealedTree`, or
    `open_server_log` on TASL-7) with a declared purpose and its release lock; any other entry in the access log is
    STOP 11 (§6).
12. **Proposer.** The TASL-7 server unreachable over Tailscale, restarted, or with `/props` (context, slots, build,
    GGUF) different from the server record STOPs the job (infrastructure); the wave is re-run as a new attempt after
    the identity is re-checked, never resumed.
13. **Harness family** (G5-PIN B). A node's job at a harness checkout other than its family's G.5 commit, or any failure
    of `g5_pin_check.py` on the note's two G.5 commits (G.5 code not byte-identical, a pin-delta file changed, an
    ancestry broken), STOPs the job.
14. **The freeze wait** (§2.11). The train/dev release of any un-STOPped T1 node of this table (autoresearch included)
    not done by the date the note fixes (*(proposed)* 18 Dec 2026), or a node STOPped at G.5: the coordinating agent
    STOPs for the author before the arms-frozen record. Only an author row may freeze the arms without that node. The
    switch also refuses any G.5 job that would start on or after that date, since it cannot lead to a release by it
    (part 3a report §5 item 9; the note's `freeze_wait` line says so). The date is read from the note and moves only by
    a docs-only amendment naming an author row on `main` that names the new date (`g5_tasl.py freeze-wait`).
15. **Autoresearch's prerequisites** (G5-ARPEND A). An autoresearch job without the completion record of §2.13 on
    `main`, with two or more records (or a near-miss name), or with a record whose cited files or sha256s do not
    match, STOPs.
16. **TASL-7 audit chunks** *(revision 11, R1-G5-AUDIT-TWO-CARDS; §2.10)*. A TASL-7 job is refused (a refusal before
    any run, not a node STOP) for a campaign job, for autoresearch, without the node's cross-host PASS on `main`, without
    the TASL-7 host check record on `main`, without a claim (copied from TASL-2) naming exactly that node, wave, chunk,
    spec, K and the wave's plan index, while the server's lease is held or its `/health` answers, on a GPU model other
    than the RTX 4090, for a node whose TASL-7 environment is not filled, and under G5-TASL-GPUH B. Once it runs, every
    STOP of this section applies to it as on TASL-2, and counts on TASL-2 once the attempt is registered. On TASL-2, a
    claim is refused for a node that could not run on TASL-7 now (the refusals above that do not need the claim), the
    wave's last chunk, a started or claimed chunk, while another claim is open, after the final TASL-7 log
    registration, or on the checks of TASL-2's order check; a registration is refused for an attempt that is not the
    claimed chunk's next TASL-7 attempt, into a closed or abandoned claim, with a missing or changed `crosshost_pass`,
    without the node wrapper log its record names, that fails its sums, holds other files, would overwrite, or comes
    with an access log that fails STOP 11 or does not extend the one registered before. Under XC3-FAIL B (§2.10) a
    committed STOP short verdict is STOP 5 for every job of that node.

**After a node STOP**, the node's partial outputs stay sealed and kept. Whether its labelled instances enter the
table is decided by an author row; they count toward B.7 only if that row says so and the node has at least 3 labelled
test instances. *(Revision 11.)* A node STOP the switch raises after the node has run is recorded in the runs tree so
that the node can be sealed: under XC3-FAIL B, `<run_id>/<node>/_switch_stop.json` (§2.10). `node_finished` then
reports the node as ended, `seal_node` seals its attempts, plans and that record, and `seal_run` can follow. The
record is written under B also when the STOP comes at the node's first job start; that node then has a node directory
holding only the record and is sealed with `seal-node`, not declared `--not-run`. A node STOPped at the switch on
determinism (STOP 5, R1-T1-D21-SCOPE) never runs, has no node directory and is declared with `seal-run --not-run`.

## 5. Key values (the final note carries these lines; the G.5 switch matches every one)

The block below is what `python sweep2/t1_tasl/g5_tasl.py key-lines sweep2/t1_tasl/g5_tasl_spec.json` prints (K = 10,
the default) for the spec on this revision's branch (revision 12: branch `mac-g5-pilot-basis-g4b-20261126` on `main`
`f1f1b651`; spec sha256 `1e29b595…`), with one change: the first line, which the command prints as the signed note's
`approved: true`, reads `approved: false` here. A test (`test_draft_section5_block_is_the_key_lines_render`) checks
that every other line of the render is in this draft.
- **Revision 12's render.** Against revision 11's block exactly five lines changed: `harness_commit` (the recount tips
  G5-7 `cbf7a003…`, G5-AR `ccdb3774…`, filled), `gpu_hours` (216.9, the G.4b recompute, P7), `cuda_ipc` and
  `cuda_ipc_acceptance` (both name TASL-7's audit chunks), and `spec_sha256` (`a80b16e2…` → `1e29b595…`: the
  `pilot_basis`, P7, harness-commit and `cuda_ipc` fields). The other 50 lines are unchanged.
- **Revision 11's render** (superseded by revision 12's; R1-T1-D21-SCOPE, R1-G5-AUDIT-TWO-CARDS). The spec gained `tasl7_audits`,
  `slots.worker_host` and `slots.audit_hosts`, and `note_lines` changed. Against revision 10's block: `hosts`,
  `gpu_model` and `job_layout` changed (the TASL-7 audit chunks and the schedule rule, §2.10), `spec_sha256` changed
  (`b25fd7f1…` → `a80b16e2…`; `eef8f5eb…` before review round 1 filled `mlgym_houseprice`'s TASL-7 input path),
  and two lines are new: `tasl7_audits` (the TASL-7 host check record, the G5-7 checkout,
  the lease, each node's cross-host PASS records or PENDING marker, the xc3 file pattern and the XC3-FAIL rule) and
  `t1_node_scope` (R1-T1-D21-SCOPE). The
  other 49 lines are unchanged; the harness commits stay PENDING. P1 must also cite the TASL-7 host check record
  (`check_note`).
- **Revision 10's render** (superseded by revision 11's, above). It was rendered on a clean checkout of this branch rebased onto `c2804f58` (change report
  §3), and it is byte-identical to the render on `44c3d80e`: D7-DIFF B changes neither the spec nor `g5_tasl.py`.
  Against revision 9's block (spec `3627cc16…` on `2582c898`) exactly two lines changed, both with READY 97: the spec
  sha256 (READY 97 added `noise_floor.t1_sigma_node` and the four run-copy fields of `noise_floor.seven` and
  `noise_floor.ar`) and `t1_table_readings` (`TABLE_READINGS["sigma_cmp"]`, D6-σ B). The other 51 lines are
  unchanged. With `--k 6 --k-row <row>` only `audit_K` and the two seed lines differ (below). If any code under
  sweep2/t1_tasl` or the spec changes before the signature, the block is rendered again and compared. *(Revision 12:)*
  the render after the recount fill is done (above); no harness value is PENDING any more.
- The values governed by §11 items 9–19 (for example the cap 425, the liveness floor 0.25, the invalid-share and
  infrastructure STOPs, the audited band, the freeze-wait date 2026-12-18, the seal, the CUDA-IPC branch, the
  `t1_table_readings` choice and the `server_log` option) are the spec's proposals; the block prints them without
  revision 8's *(proposed)* marks, and they are fixed only at the note's signature.
- `check_note` (run by the switch at every job start) requires every line verbatim, as `note_lines` renders it from
  the spec, with `audit_K`, the two seed lines and the `freeze_wait` date read from the note. It also requires
  `paper_commit` and `spec_sha256` to bind the spec, and P1–P11 PASS with their citations (§7).
- Every value that reads `PENDING` comes from a spec field still marked PENDING. At signature the spec is filled
  (run id, `paper.commit`, the seven-node copy and gate copy with the `ASSEMBLY.json` and `runs.jsonl` copies beside
  them (nine `noise_floor.seven` fields from `COPY_RECORD.json`), the P10 tails, `cuda_ipc.mode`, `decisions_row`, `e4_amendment_row`, the decisions' `signed` flags) and the note's lines are
  printed again from the filled spec. Autoresearch's items stay as the completion-record pattern under G5-ARPEND A.
- The lines follow the options in the spec. The spec carries the recommended row (all options A), unsigned; another
  option changes the lines it governs (`g5_tasl.py options <spec> --set G5-MEM=B …` shows the spec it gives).

```
approved: false
label: EVIDENCE
run_id: PENDING: c3_t1_labels_YYYYMMDD (the signed note's date)
hosts: worker TASL-2 (RTX 4090 GPU-4d623e76-7587-ee15-a633-46f60d220d94, driver 535.309.01), proposer TASL-7 (RTX 4090 GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1, driver 580.178.04) over Tailscale http://tasl-7.tail119748.ts.net:8095; TASL-7's card also runs G.5 audit chunks while no campaign wave holds the server (R1-G5-AUDIT-TWO-CARDS)
host_authority: R1-T1-HOST-TASL; environment row R1-T1-TASL-ENV; for autoresearch, R1-G1B-AR-ENV's ar-cond7a (amended by R1-G1B-AR-PY) extended to its G.5 jobs by this note (P9)
environments: torch312 d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42, jax312 80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1 (census freezes, Python 3.12.16); autoresearch: from the completion record docs/r1/reports/*/G5_AR_PREREQUISITES_YYYYMMDD.md (G5-ARPEND A; proposed ar-cond7a sweep2/g1b/env/ar-cond7a.freeze.txt 11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1, Python 3.12.15)
llama_server_sha256: b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b; build 0.7.0-dev (build 1, commit 620d222); build-directory manifest a29c667f770b9f62f99e86359867b88d08a2e4781d3a55bd3c2dd58552f1e170 (as in the signed G.4 note)
gguf_sha256: 2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75
harness_commit: G5-7 cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98 (seven nodes); G5-AR ccdb3774f60dbca21adc918777a0ddd2e6e634f8 (autoresearch); g5_pin_check.py PASS on the pair (G5-PIN B, R1-G5-DECISIONS); per family, the measurement path byte-identical to its G.1b pin (P5)
g1b_harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702 (seven nodes); 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe (autoresearch)
gpu_model: NVIDIA GeForce RTX 4090 (one table, one GPU model: campaigns on TASL-2 with the server on TASL-7; audit chunks on TASL-2, and on TASL-7 under R1-G5-AUDIT-TWO-CARDS; each job record checks the card's model)
nodes: mlab_cifar10,mlab_imdb,mlab_ogbn_arxiv,mlgym_cifar10,mlgym_fmnist,mlgym_breakout_minatar,mlgym_houseprice (CPU-only),autoresearch_fixedtokens (G5-AR A, R1-G5-DECISIONS)
data_manifests: mlab_cifar10 43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3, mlab_imdb a87254e16dfd13ad606e69ab357d02715773c0a442f5e59de42788c7cbcb935c, mlab_ogbn_arxiv 9131216213b0950e46d0eae81e691503991c0218627fde56ba88e6ac33cd4c6c, mlgym_cifar10 54d3a74d342d285fe724538a46872d028639533b4280557b00062e3d3c706100, mlgym_fmnist 24cb34483c5a23b4e7a198ac2840044171f2668d4f8cb3fe8b5e53ac69cadc32, mlgym_breakout_minatar none, mlgym_houseprice 73ee55972381fd36ee5b3244467d7f05333adfc292ed48089786b366d5c686ff, autoresearch_fixedtokens ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51; each equal to the node's G.1b spec (R1-T1-TASL-ENV; R1-T1-DATA-MANIFEST for mlgym_fmnist and mlgym_cifar10)
instances_per_node: 12 (memory mode history)
instance_seeds: 5101-5112 (instance k: training = split = manager seed 5100 + k)
instance_split: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569 (R1-SWEEP2-PREREG, PRE-SPLIT A; rule of §2.7)
memory_mode: history (G5-MEM A)
campaign_W: 20 manager calls (G5-W A)
proposer: gemma4_31b (thinking off; exam flags; context 32768; cache_prompt false)
temperature: 0.2 (G5-TEMP A); per-call seed sha256(f"{manager_seed}:{step}")[:8]
completion_cap_tokens: 4096
proposal_schema: manager_proposal/v2-diff
timeout_basis: census_slowest_x3 (R1-G1B-TIMEOUT)
audit_K: 10 (R1-G5-DECISIONS; K = 6 only after a published K-check author row, by a docs-only amendment of this line and the two seed lines citing that row)
audit_seeds_label: 7001-7005
audit_seeds_evaluation: 7006-7010
audit_scope: G5-AUDIT A: non_inert_non_duplicate_evaluated_incl_divergent_and_timed_out; reuse_parent_runs true; E5 on the label seeds only; duplicate key (instance, incumbent hash, candidate hash); cross-instance groups audited once; gate repeats per PRE-DUP A
divergence_stop: G5-DIV A: 0.2 of the audited label proposals, E5 on the label seeds, from 40 audited, at the end of each wave's audits; the literal 2 x census (0.25) kept, it never binds below 0.2
liveness_floor: 0.25
invalid_share_stop: 0.2
infrastructure_stop: 0.05
audited_band: 100-200 per node (G5-W A, G5-MEM A)
noise_floor: seven nodes: PENDING: the reviewed REL-T1-G1B copy of the g1b-tasl-20261121-b summary (joined under G1B-JOIN) sha256 PENDING with its cross-check gate record PENDING: the copy of crosscheck_gate.json, beside the summary copy sha256 PENDING (REL-T1-G1B copy of g1b-tasl-20261121-b, joined under G1B-JOIN behind the cross-check gate); autoresearch: from the completion record docs/r1/reports/*/G5_AR_PREREQUISITES_YYYYMMDD.md (G5-ARPEND A); joined by node (g1b_tasl_join.py floor-by-node; the split file's eight T1 nodes)
tails: mlab_cifar10 PENDING: P10 (Gaussian or Student-t from the seven-node G.1b summary), mlab_imdb PENDING: P10 (Gaussian or Student-t from the seven-node G.1b summary), mlab_ogbn_arxiv PENDING: P10 (Gaussian or Student-t from the seven-node G.1b summary), mlgym_cifar10 PENDING: P10 (Gaussian or Student-t from the seven-node G.1b summary), mlgym_fmnist PENDING: P10 (Gaussian or Student-t from the seven-node G.1b summary), mlgym_breakout_minatar PENDING: P10 (Gaussian or Student-t from the seven-node G.1b summary), mlgym_houseprice PENDING: P10 (Gaussian or Student-t from the seven-node G.1b summary), autoresearch_fixedtokens from the completion record (G5-ARPEND A)
job_layout: per node in sequence (G5-SLOT A as amended by R1-G5-AUDIT-TWO-CARDS), wave 1 (instances 1-4) campaigns then audits, wave 2 (instances 5-12) campaigns then audits; audits in chunks with declared deadlines; campaign waves on TASL-2's one worker slot with the server on TASL-7; a wave's plan and its last chunk (E5) on TASL-2; other chunks on TASL-2, or on TASL-7 once claimed on TASL-2 (one open claim at a time), and registered on TASL-2 before they count; the schedule is fixed by this note
tasl7_audits: TASL-7 host check docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md sha256 09945c15df67b2627a97e6cc59239744738aecb14e522f7c52d1f390be4576a4; G5-7 checkout /home/dowling/r1_tracks/t1_tasl/harness_g5 (autoresearch's audits stay on TASL-2); lease ~/r1_locks/gpu0.lock (the server's); per node the cross-host PASS before its first TASL-7 audit chunk (a PENDING node's PASS is read from main as docs/r1/reports/DIR/G1B_XC3_SHORT_VERDICT_NODE_YYYYMMDD.json, mode short, with XC3-FAIL from the signed xc3 note or R1-XC3-FAIL-READING on main: A, without a PASS the node runs on TASL-2 only; B, a STOP verdict is STOP 5 for the node; skip_nodes stay on TASL-2): mlab_cifar10 docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_mlab_cifar10_20261122.json sha256 e5264c0b4f03d29b1e01f7348ca9a7e0aa4bbf5af4638f070963c08743b55987 (xc) and docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP2_PREASSEMBLY_VERDICT_mlab_cifar10_20261124.json sha256 9403653fbea6cdca9bfe3367dec58d53062cb194827c10334523387b85ade8ff (preassembly); mlab_imdb PENDING short cross-check: mlab_imdb; mlab_ogbn_arxiv PENDING short cross-check: mlab_ogbn_arxiv; mlgym_cifar10 docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_mlgym_cifar10_20261122.json sha256 cbd4b05f664e237654558f91c0d89583a15d3dadbefdcdde7202afb4171efb29 (xc) and docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP2_PREASSEMBLY_VERDICT_mlgym_cifar10_20261124.json sha256 fea9ca97f4ce7bb3820050613dc38c4d3f59eee49abd4c07392fe3c420a38709 (preassembly); mlgym_fmnist PENDING short cross-check: mlgym_fmnist; mlgym_breakout_minatar docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_mlgym_breakout_minatar_20261122.json sha256 29fe460eab12544a5e24964651a095ffa28e9d4c1314d3d4b9eaaddefcb6ca0a (xc) and docs/r1/reports/tasl_chain_20261122/G1B_XC2_STEP2_PREASSEMBLY_VERDICT_mlgym_breakout_minatar_20261124.json sha256 503fc73130cbc4122320bfce3aa70d3c773e3ba396d6d6189a0942ddcab9c4f9 (preassembly); mlgym_houseprice PENDING short cross-check: mlgym_houseprice
t1_node_scope: every T1 node that passed U2, G.1b fixed-seed determinism and, where run, the cross-host check, whatever its D21 value (R1-T1-D21-SCOPE); each node's D21 value is recorded for the screening funnel (R1-BX-D12), not a STOP
launch: the TASL launch binding (LB A of R1-G1B-TASL-DECISIONS, as G4-LB A): a published checkout at or after the commit that publishes this note and the spec, code equal to paper_commit outside docs/ and the spec
gpu_hours: 216.9 (P7, post-pilot recompute)
cap_gpu_hours: 425, counted per the worker card (G5-TASL-GPUH A)
proposer_card_hours: metered and reported
cuda_ipc: the acceptance line cuda_ipc_acceptance, signed (TASL-2 and TASL-7's audit chunks)
freeze_wait: the arms-frozen record waits for the train/dev release of every un-STOPped T1 node of this table until 2026-12-18; no G.5 job starts on or after this date (STOP 14)
ar_prerequisites: PENDING until the completion record docs/r1/reports/*/G5_AR_PREREQUISITES_YYYYMMDD.md (G5-ARPEND A; STOP 15)
gate: r1/c3/gate.py @ 31dab9efb94b7f187ec44cab1bc4a4ad63c1085d sha256 a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23 (v3.1, R1-BX-D8-CONFIRM-V31)
preregistration: docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md sha256 aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5 (frozen)
release_rows: R1-T1-LABELS-UNSEAL (train and validation), R1-T1-LABELS-TEST-RELEASE (test labels and every evaluation block) (§6; PRE-STAGE A, REL-SCOPE A, REL-T1-G1B)
seal: procedural (receipts and access log)
t1_table_readings: sigma_cmp = sigma_node (dataset.noise_table's definition, the median joint paired sd over material edits, on the node's G.1b runs.jsonl copied beside its summary; R1-T1-FEAT-DECISIONS D6-sigma B); invalid, refused and final-infrastructure proposals left out of the table, counted; delta_hat = sign x (campaign value - best before the step), sign +1 maximize / -1 minimize, 0 for no-ops and duplicates; a label uses the label seeds where candidate and parent are both ok (partial below K_label); more than half candidate-divergent is a divergent label; fewer than half left otherwise is a STOP; an evaluation seed where only the parent diverged is a STOP; the table (campaign values of every instance) opens with R1-T1-LABELS-UNSEAL; test labels and every evaluation value stay locked until R1-T1-LABELS-TEST-RELEASE; campaign-divergent delta_hat: refuse
server_log: (a) sealed per server at its stop (seal-server; close-server after a crash), in clear on TASL-7 while it runs (STOP 11); option (b), prompt logging off, not built
decisions: G5-W A, G5-TEMP A, G5-MEM A, G5-AUDIT A, G5-DIV A, G5-TASL-GPUH A, G5-SLOT A, G5-ARPEND A (row PENDING: the author's PLAN row signing the section 11 decisions)
e4_amendment_row: PENDING: G5-MEM A needs the author's PLAN row amending E4's 'both memory modes'
cuda_ipc_acceptance: The author accepts, for the G.5 label runs (EVIDENCE) on TASL-2 and for the G.5 audit chunks on TASL-7 (R1-G5-AUDIT-TWO-CARDS), the residual risk that harness-isolation host-check item 7 (CUDA IPC across the isolation boundary, reports/HARNESS_ISOLATION_20261117.md §3) is untested on TASL-2 and on TASL-7: no frozen parent exports a CUDA tensor, harness 2d09f9a9 documents that no node uses cuda_share or cuda_open, and every run record that is not effective with empty waivers and exceptions still STOPs its job (STOP 2), on either host. Disclosed in the T1 report.
paper_commit: PENDING: the commit that publishes the signed G.5 note and this spec
spec_sha256: 1e29b59529443f1705770fa792fb937045a3bb5f9f5db06593d7f1289b4848e9
```

**Lines that differ in other cases** (also rendered by `note_lines`):
- K = 6 after a published K-check PASS row (P4; docs-only amendment of the note):
  `audit_K: 6 (K-check row <row>; R1-G5-DECISIONS; docs-only amendment of the signed note)`,
  `audit_seeds_label: 7001-7003`, `audit_seeds_evaluation: 7006-7008`.
- C12 passed (P1): `cuda_ipc: C12 PASS: <record> sha256 <hex> (TASL-2); C12 PASS: <TASL-7 record> sha256 <hex>
  (TASL-7 audit chunks)`, or, without a TASL-7 record, `…(TASL-2); no C12 record for TASL-7: no G.5 audit chunk runs
  on TASL-7 (R1-G5-AUDIT-TWO-CARDS)`; no `cuda_ipc_acceptance` line. The spec's `cuda_ipc.mode` is PENDING (`c12 |
  acceptance`); `key-lines` renders the acceptance branch for any mode other than `c12`, so the two `cuda_ipc` lines
  above are one of the two cases, not a choice already made.
- A freeze-wait date moved by an author row: `… until <date> (moved by author row <row>); no G.5 job starts on or
  after this date (STOP 14)`.
- G5-ARPEND B: `ar_prerequisites: PASS, cited in noise_floor, environments, tails and P1 (G5-ARPEND B)`, with
  autoresearch's copy, environment and tails written out in those lines.

**What the PENDING values wait for.**

| Line | PENDING until |
|---|---|
| `run_id`, `paper_commit`, `spec_sha256` | the signature: run id `c3_t1_labels_<YYYYMMDD>`, equal to the note's file name; the commit that publishes the note and spec; the filled spec's sha256 (`1e29b595…` is the unfilled spec's in revision 12; `a80b16e2…` in revision 11 after review round 1; `b25fd7f1…` was the unfilled spec's from READY 97 to revision 10; `3627cc16…` in revision 9) |
| `tasl7_audits` (four nodes) | not a fill at signature: `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_fmnist` and `mlgym_houseprice` read `PENDING short cross-check: <node>`, and the switch takes each node's PASS from `main` by its file pattern (§2.10) without a spec or note change; the line keeps the marker. If the short cross-check's verdicts are on `main` before the signature, the spec may instead list them (record, sha256, mode `short`, run id) and the block is rendered again. `mlgym_houseprice`'s TASL-7 input path (`tasl7_audits.node_extra_env`) is filled since review round 1: `/home/dowling/r1_inputs/house-prices/train.csv`, the value of the xc3 spec's `extra_env_additions.TASL-7.AR_HOUSEPRICE_TRAIN_CSV` (branch `mac-xc3-short-crosscheck-20261125b`; the G.1b spec's TASL-2 value; the xc3 note's prerequisite (a) copies the file there byte-identically, sha256 `1e18addf…`) |
| `noise_floor` (seven nodes) | the seven-node G.1b row assembled under R1-G1B-JOIN, then its REL-T1-G1B copy, gate copy and `ASSEMBLY.json` and `runs.jsonl` copies (D6 A) with a review naming all four with their sha256s (P2, §3). The line names the summary and gate copies only; the spec's four run-copy fields are filled at the same time |
| `tails` (seven nodes) | the P10 declaration from the seven-node summary |
| `gpu_hours` | *(revision 12: filled, no longer PENDING)* 216.9, the G.4b recompute's `g5_total_gpu_hours` (P3, P7); the validator requires `projection.gpu_hours_p7` to equal `pilot_basis.dates.g5_total_gpu_hours`, and the switch recomputes it from the sealed G.4b summaries at every TASL-2 job start |
| `t1_table_readings` (its σ_node text) | not PENDING in the spec. D6-σ B is decided (R1-T1-FEAT-DECISIONS) and built (READY 97): the line's first reading changed from revision 9's "sigma_cmp = sigma_node (the node's G.1b joint sigma)" to the T0-definition text of `g5_tasl.TABLE_READINGS["sigma_cmp"]` on `main`, as the block now prints it. D7-DIFF B does not change `TABLE_READINGS`; its report (§11 O2, option (a) recommended) leaves the line as it is, since the diff text the table now carries is not a campaign value |
| `decisions` | the spec's `decisions_row` set to R1-G5-DECISIONS-2 and each `decisions.<id>.signed` set true (fills at signature). The switch requires the row on `main` exactly once, its text naming every decision with its option (`G5-W A`, …, `G5-ARPEND A`) and, under G5-MEM A, the E4 row's id (`decision_row_checks`, accepted by the G.5-on-main review (`docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`, READY 91 @ `deb888cc`)): R1-G5-DECISIONS-2 passes (run with `g5_tasl.plan_row` on `main` `89899f76`'s PLAN). The line then ends "(row R1-G5-DECISIONS-2)" |
| `e4_amendment_row` | the spec's `e4_amendment_row` set to R1-G5-MEM-E4 (a fill at signature). The switch requires the row on `main` exactly once, its text naming "E4" and "memory modes" (`decision_row_checks`, accepted by the G.5-on-main review (`docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`, READY 91 @ `deb888cc`)): R1-G5-MEM-E4 passes (§2.3) |
| `environments`, `noise_floor`, `tails`, `ar_prerequisites` (autoresearch) | the completion record under G5-ARPEND A (§2.13, STOP 15) |

**Readings proposed in the part 3b-1 report (§7), not rendered or checked by the code.** The 3b-1 review ruled that
the first three decide what a declared STOP counts and so belong in the signed note; the other two are offered. The
code applies each reading, but `note_lines` has no line for them, so `check_note` neither requires nor refuses them:
written into the note they would be signed text, not checked lines. Making them checked lines needs a code change to
`note_lines` (not made in this text-only revision). `gpuh_b_meter` is updated to what part 3b-2 built (TASL-7's server
spans in place of 3b-1's campaign-wall-time lower bound, 3b-2 report §1.4).

```
invalid_share_counting: STOP 4's invalid share counts invalid proposals (parse failures, model refusals) and replies at the completion cap; diff refusals (not_run_refused: scope or malformed hunks) count toward D4 liveness (STOP 3), not STOP 4
audit_once_across_waves: a cross-instance group (incumbent hash, candidate hash) audited in wave 1 is not audited again in wave 2; its wave-2 members carry the wave-1 label; STOP 1's denominator and STOP 9's band count audited groups
audit_baseline: a timeout of the baseline code state at an audit label seed is STOP 8 (timing); any other divergence of the baseline there is a node STOP (as baseline_failed)
reuse_parent_runs_false: when parent runs are not reused, each distinct parent state is re-run once at the audit seeds, shared by its children (the §2.4 projection's reading)
gpuh_b_meter: under G5-TASL-GPUH B the running meter adds the registered TASL-7 server spans (server record start to server end); a server a campaign record names whose span is not registered counts as open until now; a gap in the server numbers counts as open from the previous registered server's stop (or the earliest known start) until now
```

**The `campaign_attribution` line** (revision 10; READY 96). The harness engines report §7 item 6 proposes it (review
decision 4), and the follow-ups report `reports/g5_code_20261123/G5_FOLLOWUPS_20261123.md` §4 quotes it verbatim
"for the author to sign or amend"; the follow-ups review (`reviews/G5_FOLLOWUPS_REVIEW_20261123.md`) found it to match
the harness report byte for byte. It is copied here verbatim from that quotation. Like the five readings above,
`note_lines` does not render it and `check_note` neither requires nor refuses it: written into the note it is signed
text, not a checked line (§11 item 19). It is placed here and not in the rendered block above, which must equal
`key-lines`.

```
campaign_attribution: in G.5 campaigns, a frozen parent killed at the job scope's memory limit (oom and oom_kill both rose), a fault signal of the frozen parent that recurs on the rerun of the same code state and seed, and a default infrastructure log pattern that appears only after AR_DEVICE and recurs on that rerun are discarded_divergent (audited, tabled, counted in divergent_in_campaign), not infrastructure_failure_final
```

**The two lines of part 3b-2** (rendered and checked). `t1_table_readings` signs the readings the locked assembly
applies (§6) and ends with the author's choice for the logged Δ̂ of a proposal that diverged or timed out in its
campaign: `refuse` (the spec's value, and the only reading the assembly applies without a signed note), `neg_inf` or
`leave_out` (§11 item 17). Its first reading is the σ_node definition: on `main` `44c3d80e` it reads "sigma_cmp =
sigma_node (dataset.noise_table's definition, the median joint paired sd over material edits, on the node's G.1b
runs.jsonl copied beside its summary; R1-T1-FEAT-DECISIONS D6-sigma B)" (D6-σ B, §3; revision 9's text "the node's
G.1b joint sigma" was D6-σ A and is withdrawn), as the block prints it. `server_log` states option (a): TASL-7's `llama-server.log` stays in clear on TASL-7 while
the server runs and is sealed at its stop; option (b), prompt logging off, is not built (§11 item 18).

**The CUDA-IPC acceptance line** (used only if C12 has not passed before the first G.5 job; the coordinator's queue
asks for the host test on TASL-2 or this line, after review condition C1 and the G.4 note's P1, which accepts the risk
for the pilot only). It is the `cuda_ipc_acceptance` line of the block above (`g5_tasl.CUDA_IPC_ACCEPTANCE`), signed
verbatim in the note. *(Revision 12:)* it now covers TASL-7's audit chunks as well as TASL-2 (R1-G5-AUDIT-TWO-CARDS:
item 7 is untested on both hosts' records):

> The author accepts, for the G.5 label runs (EVIDENCE) on TASL-2 and for the G.5 audit chunks on TASL-7 (R1-G5-AUDIT-TWO-CARDS), the residual risk that harness-isolation host-check item 7 (CUDA IPC across the isolation boundary, reports/HARNESS_ISOLATION_20261117.md §3) is untested on TASL-2 and on TASL-7: no frozen parent exports a CUDA tensor, harness 2d09f9a9 documents that no node uses cuda_share or cuda_open, and every run record that is not effective with empty waivers and exceptions still STOPs its job (STOP 2), on either host. Disclosed in the T1 report.

Under C12 instead, each host needs its own record: TASL-2's (`cuda_ipc.c12_record`) for every job, and TASL-7's
(`cuda_ipc.c12_tasl7_record`, with `c12_host` TASL-7) for a TASL-7 audit chunk; without the TASL-7 record no chunk
runs on TASL-7 (the switch at the TASL-7 job start and `claim_chunk` refuse; TASL-2 jobs go on).

*(proposed)* The instance seed block 5101–5112 is disjoint from G.1b (1001–3030), G.4 and G.4b (4001–4099), the census seeds
(8001–8010), the audit seeds (7001–7010) and the exam seeds (9001+, including 9101+ and 9201+). It avoids
5001–5006, the E1b audit seeds on the CPU nodes.

## 6. Sealing and staged release

**The seal is procedural.** The operator, the cluster agent and the author work under one account (`dowling`) on the TASL
hosts, so file modes restrict nobody. *(proposed alternative, needs a cluster test: encrypt `out.tar` inside
the job to a release public key held by the author; not built, and the spec accepts only `seal_mode: procedural`.)*
What makes the procedural seal checkable (built in part 3b-2, `sweep2/t1_tasl/g5_seal.py`):
- **Writing.** The campaign ledgers, the audit records, every per-proposal value **and the job's logs** go only into
  the job's `out.tar`. In clear, the job transfers only `out.tar`, `diagnostics.json`, `job_record.json` and
  `SHA256SUMS`. TASL-7's `llama-server.log` also carries prompts, and prompts carry per-step metric values. Under
  option (a), the one built (`server_log` line, §5), it stays in clear on TASL-7 while the server runs, governed by
  STOP 11 alone, and is sealed with the server's records at the server's stop (`g5_tasl.py seal-server`, or
  `close-server` first after a crash); the clear log is then removed. Option (b), prompt logging off, changes the
  server's arguments and is not built (§11 item 18).
- `diagnostics.json` has a fixed schema: counts and shares only (proposals, valid, invalid, truncated, ran, inert,
  duplicate, divergent in campaign, timed out, kept; audited, E5-divergent on the label seeds (no evaluation-seed
  count before release); cross-instance duplicate groups; prompt
  and completion token percentiles; GPU-seconds; STOP state). `job_record.json` has a fixed schema too. Neither holds
  a metric value, delta, label or keep outcome per proposal. (The built audit diagnostics also carry label-seed and
  planned counts, none an evaluation-seed outcome; part 3b-1 report §5 item 10.)
- The seal steps (`seal-attempt`, `seal-node`, `seal-run` on TASL-2; `seal-server` on TASL-7) verify the sums, never
  overwrite, and record the sha256 of every file in `SEAL_RECEIPT.json`. Every opening of sealed content goes through
  the access-logged reader (`g5_seal.SealedTree`; `open_server_log` on TASL-7), which checks the purpose's release lock
  and writes one line (who, when, purpose, rows, member names) to `ACCESS_LOG.jsonl` before anything is read; STOP 11
  applies to any other opening.
- What this can and cannot show: the receipt hashes **detect changes** to sealed content; they cannot detect a
  **read**. Reads are governed only by STOP 11 and the access log, which rest on the operators' and agents'
  compliance. The encryption alternative would make an early read impossible rather than forbidden.

**Before release**, operators, agents, reviewers and the author open only `diagnostics.json`, the job records and
the seal receipts. These are enough for every STOP in §4. (The job code's own reads during the table, audit
planning and the wave E5 on the label seeds, are a declared pre-release purpose with its own access log, reviewed in
part 3b-1.)

**Release** is staged under PRE-STAGE A (a code lock for both sources) and REL-SCOPE A, with one author row per stage
(the preregistration's §8 ids, which `r1/c3/release.py` names for tier T1). As built:
- **The assembly** (`g5_tasl.py assemble --stage traindev|test --table <dir> --evidence <dir> --note <signed note>`,
  `g5_assemble.py`) writes the input of the release step in the layout `release.py` and the frozen gate-input
  builder read for source `g5`: the table (`proposals.jsonl`, `build.json`) and the evidence directory
  (`label_block.jsonl`, `evidence_completion.json`; after the test row `evaluation_block.jsonl`). It reads the sealed
  tree through the access-logged reader behind each stage's row, so it does not open receipted partitions; the
  release step then partitions (part 3b-2 report §7 item 1). One label block serves both stages: it is written at the
  train/dev stage for every instance of the assembled nodes, test included, from the label seeds only, and stays in
  the evidence directory, which only the release step may open before the test row. The table (campaign values of
  every instance) is open after R1-T1-LABELS-UNSEAL, as the note's `t1_table_readings` line says.
  - **σ̂_node and δ_n** come from `noise_by_node` on the committed REL-T1-G1B copies beside each cited summary copy
    (§3). A cited node without a G.1b fixed-seed determinism PASS is STOP 5 (revision 11, R1-T1-D21-SCOPE: a node that
    does not qualify under D21 is assembled, and its D21 value is written as `d21` into its `build.json` entry and the
    noise record for the funnel); a node without a finite positive σ̂_node (T0's
    definition) or δ_n is a STOP (`g5_noise.check_usable`); so are a run copy other than the one the spec (or, under
    G5-ARPEND A, the completion record's copy check) names, and a broken hash chain.
  - **D9 B** (R1-T1-FEAT-DECISIONS): `g5_assemble.derive` STOPs after a node's rows if its `raw_state_missing` or
    `flag_mismatch` count is not 0, with the fixed reason "STOP (R1-T1-FEAT-DECISIONS D9 B): {node}: {counts} is not
    0: …" (the node and the names of the non-zero counts only, no count or value). Nothing is written. It applies in
    the train/dev stage, in the test stage (before the evaluation block is written) and in the release step's
    re-derivation (`verify_evidence`). `build.json` still carries both counts per node, always 0 in a table that
    exists.
- **The release step** (`python -m r1.c3.release --stage traindev|test --source g5 --table <dir> --audit <dir> --out
  <dir>`) checks the row's exact text on the committed PLAN, the frozen preregistration (whose final block binds the
  gate and gate-input builder sha256s), the split file, the release-code commit, the cited files' bytes, and runs the
  registered integrity check `release_checks.g5_integrity`. That check requires the G.5 code under `sweep2/`
  (`t1_tasl`, `g1b`, `g4`, `s2_c2_lib.py`) and the spec equal to `origin/main` and unmodified, then re-derives the
  blocks from the sealed tree inside the integrity context and compares bytes. It runs on TASL-2 from a clean,
  published checkout. So the G.5 files under `sweep2/` and the spec must not change on `main` from launch to the T1
  test release (part 3b-2 report §5 item 6; a PLAN row or a coordinator rule should state this freeze).
- **Readers** of T1 labels after release open only receipted partitions (`release.traindev_labels`,
  `release.builder_source`). A raw reader that does not know the tier needs the test rows of both tiers (fail closed).
  Before the test row, readers get the train/dev label block only and no evaluation value of any instance.

1. **R1-T1-LABELS-UNSEAL** (the T1 train/dev row). Its text must match `release.row_pattern("T1", "traindev")`
   exactly (`release.row_text` renders it): it cites the preregistration's sha256 (`aa1a961b…`); per PRE-DELTA A as
   amended by REL-T1-G1B, each T1 node's G.1b summary copy by node, committed path and sha256 (the REL-T1-G1B step,
   §3); the instance-split file's sha256 (`b5967dd7…`); and the release-code commit. The gate v3.1 sha256
   (`a3f7d002…`, R1-BX-D8-CONFIRM-V31) is bound through the frozen preregistration's block, which the release step
   checks, not through the row text. The nodes the row names are the nodes assembled; for the seven nodes the cited
   copy must be the spec's `noise_floor.seven` copy, for autoresearch under G5-ARPEND A the completion record's
   `noise_floor_copy`. The row cites only the summary copies (`release.py` allows one item per node); the
   `ASSEMBLY.json` and `runs.jsonl` copies from which σ̂_node and δ_n are computed are pinned by each summary's sha256
   through the hash chain (§3), as R1-T1-FEAT-DECISIONS' reading of PRE-DELTA states. Under PRE-T1 A and the freeze
   wait the row names every un-STOPped node at once. It comes before any training and releases the **train and dev label blocks** of those nodes to the C3 training pipeline: arms are
   trained on train and selected on dev. Track P reads them only if the author says so in a row.
2. The **arms-frozen record** (preregistration §4 step 4) is committed: arms, the T0 and T1 node sets (PRE-T1 A;
   autoresearch per §2.11 and STOP 14), and the split-file, noise-source, G.1b summary, gate and gate-input builder
   sha256s. Its format is `r1_c3_arms_frozen/v1` (`r1/c3/arms_freeze.py` on `main`, under R1-ARMS-DECISIONS): a
   Markdown file under `docs/r1/` with one fenced JSON block, checked by `python -m r1.c3.arms_freeze check --record
   <file>`. Its `t1` block names the frozen T1 nodes with their suites in the gate's `SUITES`, the memory mode(s) and
   the frozen instances (each frozen node with a train and a dev instance, PRE-T1 A); its `g1b_summaries` cover exactly
   that node set with committed files; its `label_tables.g5` binds the T1 train/dev receipt and partition.
   R1-ARMS-DECISIONS (ARMS-T1FEAT A) gives the features to a reviewed CPU unit; that unit also builds the T1 δ_n input
   and the suite mapping (part 3b-2 report §5 items 3–5). It is the ARMS-T1FEAT unit (READY 92, on `main` by merge
   `2798e1aa`; accepted at `a5715142`, confirmed at `b033050e`; review `docs/r1/reviews/T1_FEATURES_REVIEW_20261123.md`;
   report `reports/arms_t1feat_20261123/T1_FEATURES_20261123.md`). It computes the features inside the assembly, so
   they are table bytes, and its code sits under `sweep2/t1_tasl`, frozen from the launch. Its author decisions (its
   report §5), as recorded on `main` `44c3d80e`:
   - **R1-T1-FEAT-DECISIONS** decides D1–D4 A, D8 A, **D6 A** (the REL-T1-G1B copy list amended, §3), **D6-σ B**
     (T1's σ_node by T0's definition, §3) and **D9 B** (the assembly STOPs on a non-zero count, above). The code for
     D6 A, D6-σ B and D9 B is on `main` (READY 97, merge `44c3d80e`; report
     `reports/arms_t1feat_20261123/T1_FEAT_DECISIONS_20261123.md`). D1–D4 and D8 needed no change.
   - **D7** (a T1 input for A5) is decided by **R1-T1-A5-DECISIONS**: D7-FORM A (`trackp_prompt_t1/1`) and **D7-DIFF
     B with fallback A**. Without a T1 A5 input `gate_input_builder.TEST_SERIES` cannot supply T1, and PRE-T1 A would
     freeze an empty T1 set.
     - **Built and accepted, on `main` since revision 12's base.** The A5 T1 prompt (READY 98 with `main` `3024db3f`
       merged in (READY 100), merge `467224d4`; review `reviews/A5_T1_PROMPT_REVIEW_20261123.md`) and D7-DIFF B (READY
       103: code `d7b410b8` with the review fixes `c2b53b7e`; report `reports/arms_t1feat_20261123/D7_DIFF_B_20261124.md`;
       review `reviews/D7_DIFF_B_REVIEW_20261124.md`, accepted at `8f4f7f3a`, confirmed at `c2b53b7e`; merge
       `b6d774b4`), from branch `mac-d7-diff-b-20261124` @ `c2804f58`. So the D7-DIFF B `g5_assemble` change is on
       `main` before any commit that publishes the signed note (R1-T1-A5-DECISIONS: B, not the fallback).
     - **What D7-DIFF B changes in the table.** `g5_assemble.node_rows` writes into every tabled row
       `proposal_diff` (the ledger line's `proposal.diff`, the manager's parsed reply, written before the step runs)
       and `proposal_diff_sha256` (the harness's `diff_sha256` rule); `build.json` gains a `proposal_diff` record and
       the table schema becomes `g5_t1_table/2`. A tabled line without a text `proposal.diff` STOPs the assembly.
       Every other row byte, the label block and the evaluation block are unchanged (D7-DIFF B report §6). The spec
       and `g5_tasl.py` are unchanged, so the §5 block is too.
     - **The deadline.** The `g5_assemble` change must be merged to `main` **before the commit that publishes the
       signed note and spec** (the note's `paper_commit`), since the G.5 code under `sweep2/t1_tasl` is frozen from
       there and `release_checks.g5_integrity` re-derives with the code on `main`. Otherwise the input is A (no diff
       text, a `g5_t1_table/1` table) with FL1 disclosed, and the `g5_assemble.py` part must then not be merged
       afterwards (D7-DIFF B report §8). Under B, FL2 is disclosed (its text: D7-DIFF B report §10).
     - **After R1-T1-LABELS-UNSEAL and before the arms-frozen record**, the cluster agent runs the history-drop report
       (`python -m r1.c3.train.serialize_t1 history-drop-report --table <G.5 table dir> --receipt <release
       root>/g5/traindev/RECEIPT.json --budget-w 20 --out
       docs/r1/reports/arms_t1feat_20261123/T1_HISTORY_DROP_<YYYYMMDD>.json`, D7-DIFF B report §9): counts only, train
       and dev prompts only. Exit 1 (a prompt too long) is a STOP. It is descriptive: D7-LEN is signed as built.
   - D5 (the tier carried by the node code) is decided by R1-ARMS-DECISIONS.
   - **The T1 noise record** (`g5_noise.derive`, schema `g5_t1_noise/2`) is built after R1-T1-LABELS-UNSEAL is on
     PLAN, since it needs the train/dev row that cites the summary copies. Under D6 A it reads only committed files,
     so it is a CPU step on any clean checkout of `main` with no host access; it has no CLI (the READY 97 report §3
     gives a one-line call). The record is committed and reviewed, and its sha256 is cited before the gate run; the
     gate input's `noise` is `merge_noise(dataset.noise_table(<pinned T0 source>), builder_noise(…))`. Where it is
     cited stays open: the READY 97 report §3 says "in the arms-frozen record", but that record's format has no T1
     noise slot (`arms_freeze.check_record` pins `noise_source` to the T0 file; T1 release rows draft §5 item 3a).
3. **R1-T1-LABELS-TEST-RELEASE**. Its text must match `release.row_pattern("T1", "test")` exactly: it cites the
   preregistration's sha256 and, after it, the arms-frozen record by committed path (`docs/r1/…md`) and sha256
   (`release.row_text(..., arms_path=, arms=)`), then the split file and the release-code commit. It releases the
   **test label blocks and every evaluation block** of the G.5 T1 tables to the gate run (§4 step 5); the
   assembly's test stage, which writes the evaluation block, and the TASL-7 server logs need it too.
4. The sealed task test metric is never released.

Partial T1 at B.7 follows R1-BX-D8-CONFIRM-V31: the gate is read on T0 plus the labelled T1 nodes of the arms-frozen
record, with the count disclosed.

**Leave-one-suite-out.** The seven nodes are in two suites (MLAgentBench, MLGym). Under R1-BX-D8-CONFIRM-V31 and
PRE-SECONDARY A, the descriptive leave-one-suite-out analysis STOPs unless `autoresearch_fixedtokens` (the only
third-suite T1 node) has labelled T1 instances; the aggregate gate does not STOP on it. Under PRE-T1 A this is decided
in the arms-frozen record, the only read; G5-AR A (§2.11) and STOP 14 keep autoresearch in it unless an author row
says otherwise.

**Breakout.** `mlgym_breakout_minatar`'s evaluation keys are public constants (port report §6.2). The labels use the
validation return only, inside the isolated worker, and the sealed test return is never read; disclosed in the
appendix.

## 7. Prerequisites (each PASS in the final note)

- **P1** — R1-T1-HOST-TASL: the harness-isolation host checks pass on TASL-2 (and on TASL-7 if G.1b ran workers
  there), recorded with their sha256.
  - Done for TASL-2 at `c025f89a`: `reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md`, sha256
    `681011b2…`, as cited by the signed G.4 notes (the re-issued `g4_t1_tasl_20261123.md` included). Under G5-AR A
    the check is also needed at `2d09f9a9` (the third note's TASL-2 host check).
  - Done for TASL-2 at `2d09f9a9`: `reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md`,
    sha256 `cce9b8fb…`, PASS (items 1–7 as recorded, item 7 untested as below), the rerun after R1-G1B-AR-PY; the
    third note cites it as its P2. The first attempt at that pin STOPped on 22 Nov (Python 3.12.16 against the frozen
    3.12.15). Under G5-ARPEND A the G.5 spec keeps autoresearch's host check as a PENDING marker and the completion
    record cites this record (§2.13); under G5-ARPEND B the spec names it at signature.
  - Host-check item 7 (CUDA IPC; `reports/HARNESS_ISOLATION_20261117.md` §3) is untested on TASL-2 (review condition
    C1). The G.4 note's P1 accepts the residual risk for the pilot only. The risk is that an edit uses CUDA IPC within
    its own worker; no frozen parent exports a CUDA tensor, and `2d09f9a9` documents that no node uses
    `cuda_share`/`cuda_open`. G.5's labels are EVIDENCE, so P1 needs either **C12** (item 7 tested on TASL-2, its
    record and sha256 in the `cuda_ipc` line) or the **acceptance line** of §5, signed in the note.
    *(Recommendation: C12, if it can run on TASL-2 before the G.5 table starts; the acceptance line otherwise.)*
  - *(Revision 11, R1-G5-AUDIT-TWO-CARDS.)* TASL-7 now runs G.5 workers (audit chunks), so its host check is part of
    P1 too: `reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md`, sha256 `09945c15…`
    (`host_check_items: 1-7 PASS`, `host_check_verdict: PASS` at `c025f89a`, the record the signed G.1b spec gives
    TASL-7; item 7, CUDA IPC, untested there as on TASL-2). `check_note` requires P1 to cite it, the `tasl7_audits`
    line names it with its sha256, and the switch checks it on `main` at every TASL-7 job start. *(Revision 12:)* the
    CUDA-IPC acceptance line now names TASL-7's audit chunks as well as TASL-2 (§5); under C12, TASL-7 needs its own
    record (`cuda_ipc.c12_tasl7_record`) before any TASL-7 audit chunk (the switch and `claim_chunk` check it).
- **P2** — G.1b complete on the TASL pair: per node a fixed-seed determinism result and a D21 verdict (recorded, not
  selecting, under R1-T1-D21-SCOPE: a node enters G.5 with a determinism PASS and, for the three TASL-7 nodes, the
  cross-host check PASS, whatever its D21 value), the summary assembled from the sealed node directories of both hosts. For the seven nodes: the three sealed TASL-2 nodes of the first note, `mlgym_fmnist`
  under the amendment note, and the three TASL-7 nodes under note 2 after the re-issued cross-host check
  (`g1b-tasl-20261121-b-xc2`) passed, all in run `g1b-tasl-20261121-b`, assembled under R1-G1B-JOIN (on `main`;
  `g1b_tasl_join.py assemble`). For autoresearch, its G.1b under the signed third note (`g1b-ar-tasl-20261122-a`),
  required only for autoresearch's jobs (PENDING at signature under G5-ARPEND A). Each summary copied out by the
  REL-T1-G1B step with its sha256, together with its run's `ASSEMBLY.json` and `runs.jsonl` (D6 A of
  R1-T1-FEAT-DECISIONS, §3).
  - State on `main` `3024db3f` (revision 10): the amendment note (`g1b_t1_tasl_20261122.md`), the re-issued
    cross-check note (`g1b_xc_t1_tasl_20261123.md`) and the third note are signed; the `-xc2` cross-check's three
    step-1 verdicts are PASS (`reports/tasl_chain_20261122/G1B_XC2_STEP1_VERDICT_*_20261122.json`, merge
    `2ed97eda`); note 2 is signed and published (`authorizations/g1b_t1_tasl_20261123.md`, commit `3024db3f`). No
    G.1b noise-floor result under the amendment note, note 2 or the third note is recorded on `main`. (Until
    `44c3d80e` note 2 was not published and no `-xc2` verdict was on `main`.)
  - *(Revision 11, state on `main` `5d4f1b09`, as file names, not re-read here:)* the three step-2 (`preassembly`)
    verdicts are on `main` (`G1B_XC2_STEP2_PREASSEMBLY_VERDICT_<node>_20261124.json`), and so are result records of
    the TASL-7 note-2 nodes, the `mlgym_fmnist` amendment and autoresearch's G.1b
    (`reports/tasl_chain_20261122/G1B_TASL7_NOTE2_RESULT_20261124.md`, `G1B_TASL2_FMNIST_AMENDMENT_20261122.md`,
    `AR_G1B_TASL2_RESULT_20261122.md`). No joined seven-node summary and no REL-T1-G1B copy is on `main`.
    R1-T1-D21-SCOPE quotes the D21 outcome of the official seven-node assembly; this revision does not re-check it.
- **P3** — the G.4b re-pilot (R1-G5-DIFF-RECOUNT) run and read **with the W, memory mode and temperature the author
  decides here** (otherwise it is re-run or amended first): liveness, invalid, refusal and per-proposal divergence
  shares per node; the cross-instance duplicate rate; the R1-BX-D14 dates recomputed (`g4_lib.recompute_dates`, which
  models this table) and reported (`g5_tasl.py dates <spec> <sealed G.4b attempts> --pilot-spec
  sweep2/t1_tasl/g4b_tasl_spec.json --today <date>`, one slot, the eight nodes with autoresearch exempt from the
  ratio, §8). *(Revision 12: done.)*
  - **The pilot P3 reads is the G.4b re-pilot**, run `g4b-tasl-20261124-a`: the G.4 pilot's three nodes, seeds
    4001–4003, W = 20 manager calls, `history` and 0.2, under the recount harness G5-7 `cbf7a003`. These are the
    recommended options of G5-W, G5-MEM and G5-TEMP, so under them it needs no re-run. Its signed note is
    `authorizations/g4_t1_tasl_20261125.md` (sha256 `df600e3f…`); its result report is
    `reports/tasl_chain_20261122/G4B_TASL_PILOT_RESULT_20261125.md` (sha256 `af74c536…`, PASS, review ACCEPTED), with
    the corrigenda `G4B_TASL_PILOT_RESULT_CORRIGENDA_20261125.md` (sha256 `3eca0732…`; m1–m7, no measured value
    changed).
  - The G.5 switch reads what the re-pilot ran from `g4b_tasl_spec.json`'s `pilot` block. The spec's `pilot_basis`
    binds that file by its sha256 (`56f8c293…`, the G.4b launch table's and every sealed job record's) and names, all
    from the committed result:
    - the run and its nodes; the signed G.4b note, the result report and the corrigenda, each by path and sha256;
    - each node's sealed attempt on TASL-2 (`sealed_g4/g4b-tasl-20261124-a/<node>/attempt-1`), with the sha256 of its
      `SEAL_RECEIPT.json` and `job_record.json` (report §7) and of `out/pilot/pilot_summary.json` (the captured copy,
      equal to the sealed job record's summary);
    - the liveness per node (`proposals` 60; `ran_of_proposals`, `ran_of_valid`, `ok_of_proposals`):
      `mlab_cifar10` 0.6667 / 0.6667 / 0.6, `mlgym_fmnist` 0.8167 / 0.8167 / 0.8167, `mlgym_breakout_minatar`
      0.6167 / 0.6167 / 0.6167;
    - the dates row R1-BX-D14-G4B and the eight-node recompute of G4B-DATES A (`today` 2026-11-25, labels done
      2026-12-11, B.7 2026-12-14, D.3 2027-01-09, manuscript 2027-01-16, 216.9 GPU-h), the G.4b result's
      `dates_g5.json`. The seven-node comparison (`dates_g4.json`, 78.2 GPU-h, B.7 8 Dec) is not used.
  - At every TASL-2 job start the switch re-reads the three sealed G.4b attempts (`g4_tasl.read_sealed_summary`
    against the G.4b spec: SHA256SUMS, receipt, run id, spec sha256, harness commit, RTX 4090, TASL-2, no STOP, a
    complete pilot summary). It requires each declared sha256 and liveness figure, recomputes the dates on the
    declared day and requires them. It also requires on `main`: the result report and the corrigenda at their sha256
    (the report naming the run id, the G.4b spec sha256 and each node's receipt and job-record sha256), the signed
    G.4b note at its sha256 (approved, with the run id and the G.4b spec sha256), and R1-BX-D14-G4B naming
    "G4B-DATES A" and "eight-node". A TASL-7 audit job does not re-read the seals (they are on TASL-2); the validator's
    `pilot_basis` checks still apply there. `check_note` requires P3 to cite the run id and the result report's path.
    `g5_tasl.py pilot-basis <spec>` runs the same check on TASL-2 before the signature. At the desk, the recompute on
    the captured summaries with this spec reproduces `dates_g5.json` exactly.
  - **STOP 3 and the liveness floor.** STOP 3 (ran-of-valid below 0.25 after wave 1) applies to G.5's own waves, not
    to the pilot. The G.4b `ran_of_valid` figures (0.6667 / 0.8167 / 0.6167) are all above the 0.25 floor, so no
    pilot node points to a likely STOP 3 (G.4's strict-application figures, 0.0167 / 0.1833 / 0.1667, were all below
    it). D4's node STOP (zero liveness) is not triggered on any node.
  - It measures no autoresearch-suite node (G4-NODE3 A). Under G5-AR A, autoresearch enters the recompute from its
    TASL-2 census time, without the 4090/census ratio (§8).
  - The G.4 pilot (`g4-tasl-20261121-a`, note `authorizations/g4_t1_tasl_20261123.md`, result report on an ops branch)
    refused 155 of 180 proposals under strict diff application (122 `malformed_hunk`, 33 `malformed_diff`). That
    liveness is disclosed (R1-G5-DIFF-RECOUNT), and its recompute is replaced by G.4b's. It is no longer P3's basis.
    `g5_tasl.py dates` without `--pilot-spec` still reads its sealed attempts.
- **P4** — K = 10 (R1-G5-DECISIONS), unless a published K-check PASS author row exists before the first audit chunk,
  in which case the coordinating chat amends the note's `audit_K` and seed lines to K = 6 first (a docs-only
  amendment of the note citing that row; the spec carries both seed blocks and does not change; the switch reads
  `audit_K` from the note; no further author decision, since R1-G5-DECISIONS admits K = 6 on that row); if the
  check fails, K stays 10 and the
  coordinating agent STOPs for the author (R1-BX-D3). K is uniform within the T1 table.
- **P5** — G.5 job code (spec, campaigns in waves, audit runner, diagnostics, release locks, switch) independently
  reviewed at the launch commit. Built and reviewed on `mac-g5-code-main-20261123`, on `main` since merge `619cb0d4`
  (READY 91; review `reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`): part 3a
  (`reviews/G5_CODE_3A_REVIEW_20261123.md`), part 3b-1 (`reviews/G5_CODE_3B1_REVIEW_20261123.md`) and part 3b-2
  (`reviews/G5_CODE_3B2_REVIEW_20261123.md`), each `Verdict: ACCEPTED`; and the paper-side follow-ups to the
  harness engines (READY 96, `g5_job.py`, `g5_tasl.py`, `t1_tasl_node.sh`, on `main` since merge `1c961117`; review
  `reviews/G5_FOLLOWUPS_REVIEW_20261123.md`, `Verdict: ACCEPTED`). The harness side: `trackg/audit_g5.py` hosts **both**
  engine subcommands (the campaign and the audit engine, with the `ENGINE_CONTRACT` marker) at both G.5 harness
  commits; the follow-ups report cites the engines at G5-7 `52e3c0b0` and G5-AR `00829da1` and their review in the
  harness repository. *(Revision 12:)* the recount unit of R1-G5-DIFF-RECOUNT is reviewed, and its tips G5-7
  `cbf7a003` and G5-AR `ccdb3774` are the spec's G.5 harness commits; both carry the engine contract and the recount
  rule `trackg_diff_recount/v1` (checked at the desk, §9); without an engine that passes its check the job STOPs
  (part 3b-1 report §5 item 1, §9 n4). The launch commit also carries the ARMS-T1FEAT
  unit's code in `sweep2/t1_tasl` (`g5_features.py`, `g5_noise.py`, its changes to `g5_assemble.py` and to
  `IMPORT_SOURCES`), so P5 cites that unit's independent review beside the three above (accepted at `a5715142`, confirmed at `b033050e`, review record on `030b80a0`;
  `reviews/T1_FEATURES_REVIEW_20261123.md`, on `main` with the unit since merge `2798e1aa`). It also carries the
  R1-T1-FEAT-DECISIONS code (READY 97: `g5_relcopy.py`, `g5_noise.py`, `g5_assemble.py`, `g5_tasl.py` and the spec),
  so P5 also cites `reviews/T1_FEAT_DECISIONS_REVIEW_20261123.md` (accepted at `5cb82fa7`, on `main` since merge
  `44c3d80e`), and, if the D7-DIFF B `g5_assemble` change is on `main` before the publishing commit
  (R1-T1-A5-DECISIONS), its review `reviews/D7_DIFF_B_REVIEW_20261124.md` (accepted at `8f4f7f3a`, confirmed at
  `c2b53b7e`; on `main` with the change since merge `b6d774b4`). *(Revision 12:)* P5 also cites the review of READY
  108 (`reviews/G5_SCOPE_TWOCARDS_REVIEW_20261125.md`, accepted at `8b363374`, code `7146197e`), whose code the
  switch runs, and the review of this revision's unit once it is accepted. `check_note` requires P5 and P8 to cite review files that are on `main`
  with `Verdict: ACCEPTED`. Its harness commit descends from the G.1b pin, and the measurement path is
  byte-identical between the two commits, so the noise floor and the labels share it. There are two G.1b pins,
  `c025f89a` for the seven nodes and `2d09f9a9` for autoresearch; the check runs per family (G5-7 against `c025f89a`,
  G5-AR against `2d09f9a9`), and `g5_pin_check.py` passes on the pair (G5-PIN B). The path is all of
  `src/autoresearch/trackg/` except the v2-diff engine files the labels may change (`manager_v2_diff.py`,
  `campaign_v2_diff.py`, `proposal_v2_diff.py`, `pilot_g4.py`), plus `nodes/`, `third_party/`, `configs/trackg/`,
  `node_lib/`, and every module outside `trackg/` in the import closure of `noise_floor` (the validator computes the
  closure and runs `git diff --quiet <g1b pin> <g5 pin> -- <paths>` over the files present at the G.1b pin). New
  files that G.5 adds — the audit runner and the diagnostics writer, *(proposed)* `trackg/audit_g5.py` and
  `trackg/diagnostics_g5.py` — are allowed if they are outside the import closure of `noise_floor` (the validator
  checks that none of the measurement-path modules imports them). A change such as the R1-TRACKG-AR-COND7
  `ar_isolated.cuda_open` fix therefore fails the check. That fix is in `2d09f9a9`, autoresearch's G.1b pin, and it
  fails the check against `c025f89a`; this is why G5-PIN arose (decided B).
- **P6** — author decisions recorded: the open ones of §11. Already recorded on `main`: G5-AR A and G5-PIN B, with
  the cap raised and K = 10 (R1-G5-DECISIONS); R1-G1B-EDITS and R1-G1B-TIMEOUT; G5-SPLIT through R1-SWEEP2-PREREG
  (PRE-SPLIT A and the split file); R1-G1B-JOIN; the eight §11 decisions, each A (R1-G5-DECISIONS-2); E4 under
  G5-MEM A (R1-G5-MEM-E4; both rows pass the switch's row check, accepted by the G.5-on-main review (`docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`, READY 91 @ `deb888cc`), §2.3). `check_note`
  requires P6 to cite the spec's `decisions_row`.
- **P7** — the §8 projection, recomputed from the G.4b re-pilot's sealed summaries (P3), is within the cap.
  *(Revision 12:)* 216.9 GPU-h of 425; the spec's `projection.gpu_hours_p7` equals `pilot_basis.dates.g5_total_gpu_hours`
  and the validator requires the two to be equal. With TASL-7 audit chunks the GPU-hours are the same (§2.10).
- **P8** — the imdb baseline frozen and independently reviewed (R1-TRACKG-PORT-DECISIONS (3)); the review cited.
- **P9** — the host/environment row R1-T1-TASL-ENV (in place of the image row; G.1b, G.4 and G.5 use it), on `main`.
  For autoresearch, R1-G1B-AR-ENV admits `ar-cond7a` for its G.1b; this note extends the same environment, with the
  same freeze check at every job, to autoresearch's G.5 jobs, so that its noise floor and labels share it (§11). The
  22 Nov AR host-check STOP was resolved by R1-G1B-AR-PY, which changed only the venv's interpreter symlinks (to uv's
  versioned CPython 3.12.15); the freeze, Python version and procedure are unchanged, so the proposed G.5 environment
  is `ar-cond7a` under R1-G1B-AR-ENV as amended by R1-G1B-AR-PY (the spec's `proposed_environment`). Autoresearch's
  part may be PENDING at signature under G5-ARPEND A.
- **P10** — per node, the Gaussian or Student-t declaration from the G.1b summary, recorded before any label is
  assembled (E5); autoresearch's in the completion record under G5-ARPEND A. *(Revision 11:)* under R1-T1-D21-SCOPE
  this covers every node in the table, the non-qualifying ones included (all but `mlgym_breakout_minatar` and
  `mlgym_houseprice`); the declaration rule itself is unchanged, and D21 is not part of it.
- **P11** — host tests C1–C15 below PASS, in particular C3 (run time on the TASL-2 4090 against the timeout basis)
  and C10 (the proposer link over Tailscale). C12 can be replaced by the author's acceptance (P1); C13 applies only
  under G5-PIN B. *(Revision 11:)* C16 (TASL-7 audit chunks) is needed only before the first TASL-7 audit chunk; the
  TASL-2-only table does not wait for it.

## 8. Projection (pre-pilot; recomputed from the G.4b re-pilot before signature)

One formula serves this note and the G.4 recompute: `g4_lib.g5_node` (`sweep2/t1_tasl/g5_projection_tasl.py` prints
§2.8 with the TASL params; the `sweep2/g4` version uses the H200 params).
Per node, with r the census baseline run time and s the ran share (ran proposals per manager call):
- campaigns: manager calls × (60 s LLM + s × r × 1.25 + the instance baseline amortized), with 240 calls under W A;
- audits: (audited + 12 baselines) × K × r × 1.25, with audited = ran × the cross-instance duplicate factor (1.0
  before the pilot; inert proposals and in-campaign duplicates are not run at all); a kept proposal's audit runs
  serve again when it is a later parent (`reuse_parent_runs`; re-running every parent adds 0.2 × ran per node);
- startup: 1,500 s per job (2 campaign waves + the audit chunks; kept from the H200 model as a conservative
  allowance, since the server stays up on TASL-7 between jobs).

The factor 1.25 covers slower edited runs and timeouts; the 4090's speed is unmeasured (C3). After the G.4b re-pilot,
`g5_tasl.py dates <spec> <sealed G.4b attempts> --pilot-spec sweep2/t1_tasl/g4b_tasl_spec.json`
(`g4_tasl.recompute_dates`, i.e. `g4_lib.recompute_dates` with one slot, on the G.5 spec's parameters) uses each pilot node's measured 4090 seconds per call, run median and shares, the census time × the
measured 4090/census ratio elsewhere (except the nodes censused on the 4090, below), the measured cross-instance
duplicate rate, the memory-mode factor of G5-MEM, and the cap of G5-CAP; its label span is the larger of total / slots
and the longest node's serial work. That result is the binding P7 number. The spec carries it in
`pilot_basis.dates` and `projection.gpu_hours_p7`, and the switch recomputes it from the sealed G.4b summaries at
every TASL-2 job start (P3). *(Revision 12:)* on 25 Nov: 216.9 GPU-h (ratio 0.497, LLM 11.83 s, ran share 0.6667,
keep share 0.3469, dup factor 0.9184), labels done 11 Dec. With `--tasl7-audits` the tool adds a `tasl7_audits`
block: the label span is at least TASL-2's load, at least the campaign hours plus TASL-7's audit hours (TASL-7 serves
the proposer during campaigns), and at least each node's own serial work less its claimable TASL-7 hours; only a
wave's chunks 1 … n−2 of an eligible node are claimable (§2.10). For the eight nodes it moves nothing.

**Autoresearch** (G5-AR). The eight-node figures in §2.11 come from `sweep2/t1_tasl/g5_ar_projection_tasl.py`. It
uses the same `g4_lib.g5_node` and the TASL date wrapper `g4_tasl.recompute_dates` (one worker slot; no requested
slot-hours), with autoresearch's census B1 time on TASL-2's 4090 (218.951 s); its K = 6 rows are marked
`hypothetical_k_check`. Before the pilot the ratio is 1.0, so the figures are consistent. After the pilot, `recompute_dates`
would multiply every non-pilot node's census time by the measured 4090/census ratio, autoresearch's included, which
is wrong for a node censused on the 4090. Part 3a built the exemption: `g4_tasl_dates_params.json` lists
`ratio_exempt_nodes` (`autoresearch_fixedtokens`; `g4_tasl.recompute_dates` requires the list to equal the nodes of the
G.1b specs censused on the 4090), `autoresearch_fixedtokens` has left `pilot_nodes`, and `g5_tasl.py dates <spec>
<sealed G.4b attempts> --pilot-spec sweep2/t1_tasl/g4b_tasl_spec.json --today <date>` computes the eight-node P7 number from the G.5 spec (its nodes, census times,
options and cap 425). The G.4 checkout keeps the old ratio code, so P7 comes from `g5_tasl.py dates`, not from
`g4_tasl.py dates` (part 3a report §7). With the pre-pilot fallbacks the figures of §2.8 and §2.11 are unchanged. Under G5-AR B (not chosen), autoresearch would need its own 4090
noise floor, its own projection and an amendment of this note (not chosen, §2.11).

## 9. What is built, and what remains

**Built** (the G.5 code unit, independently reviewed and accepted in three parts, on `mac-g5-code-main-20261123`, code
base `2582c898`, merged with `main` `89899f76`; on `main` since merge `619cb0d4`, READY 91):
- **Part 3a** (`reports/g5_code_20261123/G5_CODE_3A_20261123.md`): the spec `sweep2/t1_tasl/g5_tasl_spec.json`
  (schema `g5_tasl_labels/v1`; every §11 decision as an explicit option, A by default, `signed: false`), its validator
  and `options`, `note_lines`/`key-lines` and `check_note` (§5), the switch with the TASL launch binding (LB A), the
  per-family measurement-path identity (P5) and `g5_pin_check.py` at every job start (STOP 13), autoresearch's spec
  entry with the PENDING markers and the completion-record check (STOP 15), both seed blocks with `audit_K` read from
  the note (P4), the freeze wait (STOP 14), the check of the REL-T1-G1B copies, and the date recompute exempting nodes
  censused on the 4090 (§8).
- **Part 3b-1** (`G5_CODE_3B1_20261123.md`): the job (`g5_job.py`: the four jobs per node, audit planning with
  cross-instance groups and parent reuse, chunks with deadlines), `diagnostics.json` and `job_record.json` with fixed
  nested schemas and no evaluation-seed outcome in clear, the STOP counters and `wave-checks`, the K lock,
  `close-attempt`, the GPU-hour meter, and the harness-engine contract (`g5_job.engine_contract()`).
- **Part 3b-2** (`G5_CODE_3B2_20261123.md`): the procedural seal with receipts and access logs (`g5_seal.py`, including
  the TASL-7 server seal and `close-server`), the locked two-stage assembly (`g5_assemble.py`), the release locks in
  every reader of sealed G.5 content, the registered integrity check `release_checks.g5_integrity` (REL-CODE A), the
  REL-T1-G1B copy step (`g5_relcopy.py`), the G5-TASL-GPUH B meter from TASL-7's server spans, and the note lines
  `t1_table_readings` and `server_log`.
- **R1-T1-FEAT-DECISIONS** (READY 97, merge `44c3d80e`; `reports/arms_t1feat_20261123/T1_FEAT_DECISIONS_20261123.md`):
  D6 A in the copy step (the `ASSEMBLY.json` and `runs.jsonl` copies, the seed guard, the count check) and in the
  switch's copy check (`run_copies`, `check_g1b_copy`); D6-σ B in `noise_by_node` and `g5_noise` (the `sigma_joint`
  path removed; spec field `noise_floor.t1_sigma_node`; the four run-copy fields; the `sigma_cmp` reading); D9 B in
  `g5_assemble.derive`; the noise pre-check after STOP 5 (§4); and the launch check of the row (`T1_FEAT_ROW`,
  `T1_FEAT_TERMS`, §11).
- **R1-T1-D21-SCOPE and R1-G5-AUDIT-TWO-CARDS** (revision 11; READY 108, on `main` since merge `03c0d842`; change
  report `reports/g5_code_20261123/G5_SCOPE_TWOCARDS_20261125.md`, reviewed and accepted): STOP 5 as fixed-seed
  determinism with each node's D21 value recorded (`g5_tasl.g1b_verdict_scope`, `require_deterministic`; the switch,
  `check_g1b_copy`, `check_ar_record`, `g5_assemble.noise_by_node`, `g5_noise.derive`); the spec block
  `tasl7_audits` and its validator; the switch's `host`/`chunk` with `check_crosshost_pass` and `tasl7_host_check`;
  `g5_job.claim_chunk`, `register_attempt` and the TASL-7 path of `run_job`; `seal_run` sealing `_remote`; the CLI
  commands `claim-chunk` and `register-chunk`; the node wrapper kind `g5t7`; the note lines `tasl7_audits` and
  `t1_node_scope`; the switch's checks of both rows on `main`.
- **Revision 12's unit** (branch `mac-g5-pilot-basis-g4b-20261126`, **not on `main`**, under independent review;
  change report `reports/g5_code_20261123/G5_PILOT_BASIS_HARNESS_20261126.md`): P3 on the G.4b result
  (`check_pilot_basis`, `pilot_basis_check`, the `pilot-basis` CLI, the P7 tie, P3's citation of the result report,
  the G.4b checkout among the checkouts a family may not use, the dates row in the switch's row checks); the recount
  harness commits in the spec; the xc3 rules imported from `g1b_crosscheck`; the CUDA-IPC acceptance line for TASL-7
  and the per-host C12 records (`check_c12`, `g5_job.tasl7_eligible`); `dates --tasl7-audits` (`tasl7_dates`,
  `default_tasl7_nodes`).

**Remains, before any G.5 job:**
- **The harness engines**: `trackg/audit_g5.py` with the campaign and audit engine subcommands and the
  `ENGINE_CONTRACT` marker, at both G.5 harness commits (`G5-7` on `c025f89a`, `G5-AR` on `2d09f9a9`), independently
  reviewed, with a smoke test on TASL-2. Its contract (part 3b-1 §2 and §9, part 3b-2 §5 item 1): every edit-caused
  failure is classed divergent, never infrastructure; engine stop text carries no value or per-seed outcome; every
  `ok` audit row, evaluation seeds included, carries a finite numeric `outcome.value`. Under G5-W B it would also need
  a worker-run budget in the v2-diff engine (not planned; G5-W B is refused at launch). *(Revision 10, as cited, not
  re-checked here: the follow-ups report (READY 96) names the reviewed engines at G5-7 `52e3c0b0` and G5-AR
  `00829da1`, with their report and review in the harness repository; the paper-side follow-ups are on `main`; the
  TASL-2 ENGINEERING smoke with a fake engine is on `main`
  (`reports/tasl_chain_20261122/G5_TASL2_ENGINE_SMOKE_20261123.md`, review ACCEPTED: 13 items PASS, 2 not exercised,
  the real engines not run).)*
- **The recount harness unit (R1-G5-DIFF-RECOUNT): done (revision 12).** The G.5 harness commits apply a manager
  diff after recomputing each hunk header's line counts (`git apply --recount` semantics), at both commits, as a
  reviewed harness unit: G5-7 `cbf7a003` and G5-AR `ccdb3774`, successors of `52e3c0b0` and `00829da1`, filled in the
  spec's `harness_families.<family>.g5_commit` (§5). It ran in the G.4b re-pilot (G5-7, `harness_g4b`). The TASL-2
  checkouts `harness_g5` and `harness_g5_ar` must be moved to these commits before the first G.5 job (STOP 13
  otherwise; on 25 Nov `harness_g5` was at `52e3c0b0`). The two points that bore on it, kept as the record:
  - **O1 of D7-DIFF B (report §11; O1 open, (a) recommended).** The table carries `proposal.diff` as the manager's
    text, so that claim holds only if the unit keeps writing the manager's parsed reply into the ledger's
    `proposal.diff` and records any recounted text only in the run's diff provenance. The audit re-materialises every
    code state from the chain of `proposal.diff` texts, so it must apply them with the same recount rule, or it STOPs
    on integrity. Option (a) would have the unit's review confirm both; option (b) would add an assembly check once
    the provenance shape is known. Neither is chosen here. *(Revision 12: the G.4b result's ledger check shows the
    shape: `diff_recount.raw_diff_sha256` equals the sha256 of `proposal.diff`, and the applied (recounted) text is
    in the run's diff record, so (a)'s first half holds on the G.4b ledgers; the audit side is not re-checked here.)*
  - **P5's measurement path** (`g5_tasl.measurement_path_check`, per family, against the G.1b pin):
    - **changes** are allowed only to the four engine files directly under `trackg/` (`manager_v2_diff.py`,
      `campaign_v2_diff.py`, `proposal_v2_diff.py`, `pilot_g4.py`), and only while they stay out of `noise_floor`'s
      import closure;
    - **new files** are allowed only as `audit_g5.py` or `diagnostics_g5.py` in `trackg/`; or anywhere outside
      `trackg/`, `nodes/`, `third_party/`, `configs/trackg/` and `node_lib/`, as long as `noise_floor`'s import
      closure is unchanged; or freely under `docs/` and `tests/`. *(Revision 12: the recount tips pass this check; the
    recount sits in `campaign_v2_diff.py`, an engine file.)*
    - `diff_support.py` (where `apply_diff` and `parse_unified_diff` live) is in `noise_floor`'s import closure. A
      recount change there would STOP every G.5 job at the P5 check. Relaxing the check to admit it would change the
      noise-floor measurement code itself, not only G.5 code, so the noise floor and the labels would no longer share
      one measurement path. The recount must therefore sit in the engine files or the allowed additions.
- (Done since revision 9.) The G.5 code is on `main` (merge `619cb0d4`), with P5's reviews, including the G5-MEM A
  row check as fixed at `baf6be5d` and refactored into `g5_tasl.decision_row_checks` at `2582c898` (the decisions row
  for the eight options and the E4 row's id; the E4 row for "E4" and "memory modes"; both rows on `main` pass, §2.3),
  accepted by the G.5-on-main review (`docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`, READY 91 @
  `deb888cc`).
- (Done since revision 12's base.) **The D7-DIFF B `g5_assemble` change** (R1-T1-A5-DECISIONS; READY 103) is on
  `main` (merge `b6d774b4`), before any commit that publishes the signed note and spec, so A5's T1 input is D7-DIFF B
  (§6 step 2). It writes table bytes (`proposal_diff`, `proposal_diff_sha256`, schema `g5_t1_table/2`) but changes
  neither the spec nor `g5_tasl.py`.
- **Revision 12's unit** reviewed and merged before the commit that publishes the signed note and spec (it changes the
  spec and `g5_tasl.py`, so the §5 block and `spec_sha256` are those of the merged spec).
- **The expansion addendum** (R1-G5-EXPANSION-JOIN), only if a candidate joins: a spec entry for the node, its
  split-file assignment (the frozen preregistration binds the split file `b5967dd7…` with eight T1 nodes, so a ninth
  node needs an author decision on how it enters PRE-SPLIT and PRE-T1), and a reviewed code unit that reads the
  addendum note. Not built.

**Remains, optional or for later** (none blocks the recommended options):
- The five readings of part 3b-1 §7 as checked note lines (§5): a change to `note_lines` and its tests.
- A small report of the proposer-card hours under G5-TASL-GPUH A from the registered server spans (§2.6 and §5 ask
  for them beside the cap; under A no code reports them yet; part 3b-2 §5 item 7; needed before the T1 report, not a
  STOP input).
- Under G5-ARPEND B, a check of the third G.1b note by the switch (part 3a report §8; under A the completion record
  binds it).
- The C12 record format, provisional in part 3a (`c12_host`/`c12_verdict` lines, or a `c12_review` on `main`), fixed
  when the C12 procedure is written.
- Option (b) of `server_log` (prompt logging off) and the encryption seal: not built; each needs a code unit and a
  cluster test if the author chooses it.
- Refinements recorded as open in the reviews: the close-attempt end time (latest modification time), a seal cleanup
  after a crash between rename and cleanup, and the `close-server` pid check after a TASL-7 reboot (part 3b-2 §10).

**The ARMS-T1FEAT unit** (accepted on `mac-t1-features-20261123`, READY 92 @ `030b80a0`: accepted at `a5715142`, confirmed at `b033050e`; review `docs/r1/reviews/T1_FEATURES_REVIEW_20261123.md`; not part of
the three G.5 parts; on `main` since merge `2798e1aa`): the T1 features for A3/A5 (table bytes, written by the
assembly), the T1 noise input (`g5_noise.py`) and the suite mapping. Its decisions D1–D4, D6, D6-σ, D8 and D9 are
recorded by R1-T1-FEAT-DECISIONS, with the code they need on `main` (READY 97); D7 is recorded by R1-T1-A5-DECISIONS,
and its code (READY 100 and the D7-DIFF B `g5_assemble` change, READY 103) is on `main` (merges `467224d4`,
`b6d774b4`; §6 step 2).

**Post-release cluster steps** (after R1-T1-LABELS-UNSEAL, before the arms-frozen record): the T1 noise record
(`g5_noise.derive`, §6 step 2) and the history-drop report (D7-DIFF B report §9; §6 step 2).

## 10. Needs a cluster test

- **C1.** Everything in the TASL plan (`sweep2/t1_tasl/T1_TASL_PLAN.md` §6).
- **C2.** The audit runner on the TASL-2 4090: re-materialisation, isolated joint-seed runs, fixed-seed determinism of audit
  pairs (which the reuse of parent runs relies on), and E5 per seed block (label seeds only for labels and the STOP).
- **C3.** Run time on the TASL-2 4090 against the timeout basis (false divergence).
- **C4.** Diagnostics out per wave and per audit chunk, so the STOPs act early.
- **C5.** The audit-chunk deadlines for the K = 10 imdb and Breakout audits.
- **C6.** The seal: under the shared operator account file modes restrict nobody, so either the procedural seal
  (receipt hashes, access log; built, C15) is exercised end to end, or the encryption alternative (not built) works
  end to end.
- **C7.** The resident GGUF on TASL-7 (no per-job transfer) and the one worker slot (G5-SLOT); under
  R1-G5-AUDIT-TWO-CARDS, the server stopped and restarted around the TASL-7 audit phases with its identity re-checked.
- **C8.** The cross-instance identical-proposal rate at the chosen temperature, from the G.4b re-pilot's instances
  (P3; the recompute's dup factor 0.9184).
- **C9.** The worker GPU-hour meter against the cap under the chosen W, MEM and K, closed attempts included, with the
  proposer card's hours beside it (under G5-TASL-GPUH B, the registered server spans against TASL-7's card time).
- **C10.** The proposer link over Tailscale for a multi-day span: reachability, per-call latency, a server restart
  handled as an infrastructure STOP with the identity re-checked.
- **C11.** TASL-7's lease: the server holds it while it runs; G.1b on TASL-7 (second note) finished before. Under
  R1-G5-AUDIT-TWO-CARDS a TASL-7 audit chunk takes the same lease, refused while the server holds it, and a server
  start refused while a chunk holds it.
- **C12.** Host-check item 7 (CUDA IPC) on TASL-2, and on TASL-7 for its audit chunks, in place of the acceptance
  line in P1 (§5).
- **C13.** G5-PIN B: the two harness checkouts on TASL-2, each node launched from its own family's checkout and each
  checkout holding both G.5 commits (`g5_pin_check.py` runs in the node's family checkout), `g5_pin_check.py` passing
  on the two G.5 commits, and a node at the other family's checkout refused (§4 item 13).
- **C14.** The harness unit's smoke test on TASL-2 (§9): the engines' out trees with binaries read only by the named
  members; infrastructure rows without an isolation block become STOP 7; the re-materialised `code_state_sha256`
  matches the ledgers' hashes; every `ok` audit row carries a finite `outcome.value`; the `g5` kind of the node wrapper
  in a real delegated scope.
- **C15.** The seal, assembly and release on real outputs (part 3b-2 report §4): `seal-attempt` (with free disk
  checked first, a tar failure and a closed attempt), `seal-node`, `seal-run`; on TASL-7 `seal-server`, `close-server`
  after a dead server, the receipt registered on TASL-2 with `server-span`; the joined, gated G.1b run directory under
  `sealed_g1b` and `rel-copy` on TASL-2 (the five files of D6 A, with the seed guard and the count check on the real
  `runs.jsonl`); the noise pre-check at a job start on the copies on `main`; both assembly stages with the signed note
  (D9 B's counts 0 on real ledgers); the release step for `--source g5` on a clean, published checkout on TASL-2.
- **C16** *(revision 11, R1-G5-AUDIT-TWO-CARDS)*. Before each claim and each TASL-7 job, `git fetch origin` in the
  paper checkout used (the PASS, XC3-FAIL and host-check reads are of published `main`). On TASL-7: the G5-7 checkout at its G.5 commit at
  `/home/dowling/r1_tracks/t1_tasl/harness_g5`, clean, holding both G.5 commits for `g5_pin_check.py`; the G.5 paper
  checkout for the launch binding; `torch312` and `jax312` equal to their freezes; one audit chunk end to end
  (claim on TASL-2, copy, `t1_tasl_node.sh g5t7` on TASL-7, copy back, `register-chunk`), with the server stopped,
  the lease taken, the GPU model recorded, and the registered attempt sealed on TASL-2.

## 11. What the author still signs

Recorded already (no further decision): G5-AR A and G5-PIN B, the cap raised to the projection, K = 10 until a
K-check row, B.7 about 15 Dec (R1-G5-DECISIONS); G5-SPLIT (PRE-SPLIT A); the timeout basis (R1-G1B-TIMEOUT); the
seven-node G.1b assembly across the notes (R1-G1B-JOIN); autoresearch's G.1b environment (R1-G1B-AR-ENV as amended by
R1-G1B-AR-PY); **items 1–8 below, each as recommended (A), by R1-G5-DECISIONS-2** (`main` `89899f76`), with E4 amended
for T1 by R1-G5-MEM-E4. R1-G5-DECISIONS-2 says: "Section 11 items 9–16 and the new note lines are fixed at the note's
signature." Also recorded (`main` `44c3d80e`): the ARMS-T1FEAT decisions D1–D4, D6, D6-σ, D8 and D9
(R1-T1-FEAT-DECISIONS) and D7 (R1-T1-A5-DECISIONS) (§6 step 2).

**What the code requires of these rows.** At signature the spec's `decisions_row` is set to R1-G5-DECISIONS-2, its
`e4_amendment_row` to R1-G5-MEM-E4, and each `decisions.<id>.signed` to true (`validate_spec --launch` refuses unsigned
decisions). At every job start the switch (`g5_tasl.decision_row_checks`, fixed at `baf6be5d`, accepted by the G.5-on-main review (`docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`, READY 91 @ `deb888cc`))
requires each row on `main` exactly once (`g5_tasl.plan_row`): the decisions row naming `G5-W A`, …,
`G5-ARPEND A` and, under G5-MEM A, the E4 row's id `R1-G5-MEM-E4`; the E4 row naming "E4" and "memory modes" in its
text. Checked with the code against `main` `89899f76`'s PLAN: both rows pass.

**R1-T1-FEAT-DECISIONS at launch** (READY 97). After those checks the switch calls
`plan_row("R1-T1-FEAT-DECISIONS", read_main, terms=("D6 A", "D6-σ B", "D8 A", "D9 B"))` and adds the row to the rows
the launch binding checks on `origin/main`. The id and the terms are constants of the code (`T1_FEAT_ROW`,
`T1_FEAT_TERMS`), not spec fields, so the signature fills nothing for them. The row must occur exactly once; each term
must occur literally in its text without the id cell, not preceded or followed by a letter or digit (`D6-σ B` with
the ASCII hyphen-minus and the Greek small sigma U+03C3). A missing or misspelt term STOPs every job. `plan_row`
cannot see negation: it proves only that the strings occur. On `main` `44c3d80e` and on `3024db3f` the row occurs once and its text
contains each of the four terms once with those boundaries (checked in this revision by a text search, not by running
the code; the READY 97 test `test_t1_feat_decisions_row_on_this_checkouts_plan` checks it on the real PLAN).

**Decisions** (signed: items 1–8, option A each, R1-G5-DECISIONS-2):
1. **G5-W** — **A: 20 manager calls (signed)** | B: 20 worker runs with an 80-call cap (refused at launch: no
   worker-run budget in the engine, and the pilot ran manager calls).
2. **G5-TEMP** — **A: 0.2 with the engine's seed rule (signed)** | B: 0 (needs a re-issued G.4b re-pilot at 0).
3. **G5-MEM** — **A: `history` only, 12 instances (signed), with R1-G5-MEM-E4 amending E4's "both memory modes"**
   (both rows pass the switch's row check at `baf6be5d`, above) | B (needs a pilot with both modes) | C (refused as not
   built).
4. **G5-AUDIT** — **A (signed)**: the audit-once rule for cross-instance groups, `reuse_parent_runs: true` (subject
   to C2), E5 on the label seeds only | B.
5. **G5-DIV** — **A: 20 % on audited proposals from 40, the literal "2 × census" kept (signed)** | B | C.
6. **G5-TASL-GPUH** — **A: the worker card counts (signed; the 425 cap assumes it)** | B: both cards (within 425
   only at share 0.6 with the server stopped during audits; above it otherwise).
7. **G5-SLOT** — **A: one slot on TASL-2 (signed)**, amended by **R1-G5-AUDIT-TWO-CARDS** (campaign waves keep the
   one slot on TASL-2; audit chunks may also run on TASL-7 while no campaign wave holds the server, §2.10) | B: audits
   on TASL-7 while campaigns pause, a server restart per wave (not built; refused).
8. **G5-ARPEND** — **A**: autoresearch's own prerequisites PENDING at signature, completed by a reviewed record the
   coordinating chat commits without a further author decision; the spec carries PENDING markers and the switch reads
   the record (no spec or note change) (**signed**) | B: the signature waits for them (§2.13).

**What remains for the signature: the values it fixes** (*(proposed)* in the draft; each is a line of §5; "items
9–16 and the new note lines", R1-G5-DECISIONS-2):
9. The cap, 425 GPU-h of the worker card (§2.6), or the cap of another row of §2.8/§2.11 if a decision above departs
   from the recommended row.
10. The liveness floor 0.25 (STOP 3), the invalid-share STOP 0.2 (STOP 4), the infrastructure STOP 5 % (STOP 7), and
   the audited band 100–200 per node under W A (150–240 under B; doubled under MEM B) (STOP 9).
11. The freeze wait over every un-STOPped node and its release date, *(proposed)* 18 Dec 2026, recomputed with P7,
    with "no G.5 job starts on or after this date" (§2.11, STOP 14).
12. The instance seed block 5101–5112 (§5).
13. The seal: procedural (receipts and access log; built) or the encryption alternative (not built) (§6, C6).
14. Autoresearch's G.5 environment: `ar-cond7a` under R1-G1B-AR-ENV as amended by R1-G1B-AR-PY, extended to G.5 by this
    note (P9).
15. CUDA IPC: C12 passed (the `cuda_ipc` line cites it; for TASL-7's audit chunks its own record) **or** the
    acceptance line of §5, signed verbatim (revision 12: it names TASL-2 and TASL-7's audit chunks).
16. The K amendment: after a published K-check PASS row, the coordinating chat amends the note's `audit_K` and seed
    lines to K = 6 without a further author decision; the spec carries both seed blocks and is not re-issued, and the
    switch reads `audit_K` from the note (P4).
17. The T1 table readings of the `t1_table_readings` line (§5, §6; its σ_node text follows D6-σ B of
    R1-T1-FEAT-DECISIONS, as rendered on the final code tip), and in it the Δ̂ of a proposal that diverged or
    timed out in its campaign: `refuse` (the spec's value; the assembly STOPs on such a proposal) | `neg_inf` (−∞,
    "never kept"; not standard JSON) | `leave_out` (not tabled, still audited and counted) (part 3b-2 report §6
    item 3).
18. TASL-7's `llama-server.log`: option (a), sealed per server at its stop and in clear on TASL-7 while it runs (built;
    the `server_log` line) | option (b), prompt logging off (not built; it changes the server's arguments, needs a
    validator change, a re-issued spec and a cluster test).
19. The five readings of part 3b-1 (§5), as signed text in the note (the code applies them but does not check the
    lines), or as checked lines after a code change (§9); and the `campaign_attribution` line of the harness engines
    report §7 item 6 (READY 96; quoted verbatim in §5 from the follow-ups report §4), signed as written or amended, as
    signed text in the same way.
20. *(Revision 11, R1-G5-AUDIT-TWO-CARDS.)* The schedule of the TASL-7 audit chunks, which the row says the note
    fixes (§2.10): when the server is stopped for TASL-7 audit phases, which nodes' chunks are claimed for TASL-7 and
    in which order, and that a claimed chunk runs only on TASL-7. The code enforces the rules (one open claim, never
    a wave's last chunk, the lease, the server down, the cross-host PASS), not a timetable. The `tasl7_audits`,
    `hosts`, `gpu_model` and `job_layout` lines are rendered from the spec (§5).
21. *(Revision 11; revision 12: signed.)* **XC3-FAIL A**, signed in the xc3 note (`xc3_fail: A`) and in
    R1-XC3-FAIL-READING (26 Nov): a failed or missing short check keeps only that node's audits off TASL-7; nothing to
    sign in the G.5 note. G.5's switch reads A from `main` (both options stay built; the two sources agree).
22. *(Revision 11, R1-T1-D21-SCOPE.)* Nothing to sign: the row decides it. The note's `t1_node_scope` line states it,
    and each node's D21 value goes to the screening funnel (R1-BX-D12) from the T1 noise record or `build.json` (§3).

**Rows and records needed before the signature:** items 1–8 are signed (R1-G5-DECISIONS-2) and E4 is amended
(R1-G5-MEM-E4), and both pass the switch's row check (`decision_row_checks`, accepted by the G.5-on-main review (`docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md`, READY 91 @ `deb888cc`)); the
seven-node REL-T1-G1B copy with its cross-check gate copy and its `ASSEMBLY.json` and `runs.jsonl` copies (D6 A) and
a review naming all four with their sha256s, which needs the amendment, `-xc2` and note-2 runs and the joined assembly
under R1-G1B-JOIN (P2); the reviewed harness engines and **the reviewed recount unit (R1-G5-DIFF-RECOUNT) at both G.5
harness commits**, which keeps `proposal.diff` as the manager's text with the audit applying the same recount rule
(D7-DIFF B's O1, open, (a) recommended) and passes P5's measurement path (§9), whose commits fill
`harness_families.<family>.g5_commit` (P5; done in revision 12: `cbf7a003`, `ccdb3774`); done since revision 9: the ARMS-T1FEAT unit
and the R1-T1-FEAT-DECISIONS code reviewed and on `main` (P5), and the author rows R1-T1-FEAT-DECISIONS (D1–D4, D6 A,
D6-σ B, D8, D9 B) and R1-T1-A5-DECISIONS (D7); the D7-DIFF B `g5_assemble` change (READY 103) merged to `main`
**before the commit that publishes the signed note and spec**, or else D7 A with FL1 disclosed (R1-T1-A5-DECISIONS;
§6 step 2; done: merge `b6d774b4`); the §5 block rendered again after the harness-commit fill (done in revision 12);
the G.4b result on `main` and `pilot_basis` filled from it (P3), with the post-pilot recompute (P7; done in revision
12, 216.9 GPU-h); revision 12's unit reviewed and merged; under G5-ARPEND B also autoresearch's G.1b, its copy and P10 (its host check is PASS and its note signed:
P1, P2, P9, P10). Optional: a K-check row (P4; K = 6 by amendment, item 16).

**After the signature, while the table runs:** under G5-ARPEND A, the completion record for autoresearch (§2.13), which
the coordinating chat commits after its review (the switch reads it; no amendment); the K amendment if a K-check row
appears; the freeze wait's author row if STOP 14 fires on a node STOP.

**After the table:** the T1 release rows R1-T1-LABELS-UNSEAL (train/dev) and, after the arms-frozen record,
R1-T1-LABELS-TEST-RELEASE (test labels and every evaluation block), each in the exact text of `release.row_pattern`
(§6); the T1 noise record (`g5_noise.derive` on the committed copies, D6 A) built after R1-T1-LABELS-UNSEAL, reviewed
and cited before the gate run; the history-drop report on the train/dev prompts (D7-DIFF B report §9; §6 step 2),
committed with its review, exit 1 a STOP; the T1 input for A5 (D7, R1-T1-A5-DECISIONS) on `main` before the
arms-frozen record, without which T1 is not in the read; the arms-frozen record in the
format of `r1/c3/arms_freeze.py` (R1-ARMS-DECISIONS), its T1 rows carrying the features the table already holds; the
freeze wait's author
row if STOP 14 fires on the release deadline.

**The signature itself:** `approved: true` on the final note at `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md`,
with every PENDING value of §5 filled by filling the spec and printing the lines again (`g5_tasl.py key-lines`), from
the reviewed G.5 code unit (P5) and the seven-node REL-T1-G1B copy (the G.4b recompute (P3, P7) and the two G.5
harness commits are filled since revision 12), and P1–P11 recorded as PASS (autoresearch's items PENDING under G5-ARPEND A). `g5_tasl.py check-note
<spec> --note <note> --draft` on the completed unsigned note, and without `--draft` once it is on `main`.

### 11.1 What the author still signs in the G.5 note (revision 12)

Every key line of §5 is signed as rendered; most are fixed by rows already on `main` or by the spec. The list below
names each line or choice that still carries an author choice at signature, with the options and a recommendation.
**Nothing here is decided by this draft.** Lines not listed (hosts, environments, the binaries, nodes, data
manifests, seeds, schema, timeout basis, gate, preregistration, release rows, `t1_node_scope`, `tasl7_audits`,
`launch`) follow rows on `main` and are signed as rendered.

| # | Note line(s) | What is chosen | Options | Recommendation |
|---|---|---|---|---|
| S1 | `cap_gpu_hours` | the cap and **how TASL-7 audit-chunk hours count** | (A) 425 GPU-h of the worker card, **TASL-7 audit-chunk hours inside the 425** (as built: the meter counts a registered TASL-7 attempt against the cap, STOP 9; the line reads "425, counted per the worker card (G5-TASL-GPUH A)"); (B) TASL-7 audit hours outside the cap, metered beside it like the proposer card (needs a meter change in `g5_job`, a review and a new render); (C) a higher cap | **A**: a TASL-7 audit chunk is worker work on the same GPU model; the projection (216.9 GPU-h) is the same on either card, so A keeps 208 GPU-h of headroom; for the eight nodes no chunk can move to TASL-7 anyway (§2.10) |
| S2 | `gpu_hours` | P7 | 216.9 GPU-h, the G.4b recompute bound in `pilot_basis` (P3) | sign as rendered; an expansion node (S9) needs a recompute in its addendum |
| S3 | P3, P7 (prerequisite lines) | their PASS text | P3 must cite `g4b-tasl-20261124-a` and `reports/tasl_chain_20261122/G4B_TASL_PILOT_RESULT_20261125.md` (`check_note`); P7 "216.9 GPU-h within 425" | sign with those citations; `g5_tasl.py pilot-basis <spec>` on TASL-2 PASS before signing |
| S4 | `cuda_ipc`, `cuda_ipc_acceptance` | P1 for CUDA IPC on both hosts | (a) the acceptance line as extended in revision 12 (TASL-2 and TASL-7's audit chunks); (b) C12 on TASL-2 and on TASL-7 (two records); (c) C12 on TASL-2 only, so no audit chunk runs on TASL-7 | (b) if both host tests can run before the first G.5 job; otherwise (a). (c) costs nothing for the eight nodes today (no chunk can move) but would block TASL-7 for an expansion node. The extended wording is itself an author wording choice: sign it verbatim, or amend it (a code change of `CUDA_IPC_ACCEPTANCE` and a new render) |
| S5 | `job_layout` (§11 item 20) | the TASL-7 schedule the row says the note fixes | (A) as built: chunks claimed for TASL-7 by the operator under the code's rules (never a wave's first or last chunk, one open claim, the lease, the server down, the cross-host PASS), no timetable; (B) no TASL-7 audit chunks for the eight nodes (TASL-2 only) | **A**: it changes nothing for the eight nodes (no wave has three chunks) and keeps the path for an expansion node or a later K/chunk change; B is equivalent in effect now and simpler to audit |
| S6 | `freeze_wait` (§11 item 11) | the release date | (a) 18 Dec 2026 as proposed (labels done 11 Dec by the G.4b recompute, + 2 days = 13 Dec, so 5 days of margin); (b) 13 Dec (no margin); (c) a later date | **(a)** at signature; if expansion nodes join (S9) the coordinating chat recomputes and an author row may move the date by the docs-only amendment the line allows |
| S7 | `liveness_floor`, `invalid_share_stop`, `infrastructure_stop`, `audited_band` (§11 item 10) | the STOP thresholds | as proposed (0.25, 0.2, 5 %, 100–200) or other values | as proposed: the G.4b `ran_of_valid` (0.6667 / 0.8167 / 0.6167) is well above 0.25; the projected audited counts (146.9, 180.0, 135.9 for the pilot nodes) are inside 100–200 |
| S8 | `t1_table_readings`, `server_log`, `seal` and the part 3b-1 readings with `campaign_attribution` (§11 items 13, 17–19) | unchanged since revision 11 | as listed in §11 | as listed in §11 (`refuse`; option (a); procedural; signed text) |
| S9 | — (a later addendum note) | **how an expansion node joins** (R1-G5-EXPANSION-JOIN) | *(proposed)* `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>_addendum_<N>.md`, citing the signed note, the candidate's G.1b note and result, its spec entry, and a dates recompute; the same code, K and rules | to be fixed with the code unit that reads it (not built). Open, for the author: the frozen split file (`b5967dd7…`, PRE-SPLIT A) lists eight T1 nodes, so a ninth node's instance split and its entry into PRE-T1's node set need a decision before its addendum |
| S10 | `decisions`, `e4_amendment_row` | the rows | fills at signature: R1-G5-DECISIONS-2, R1-G5-MEM-E4 (both pass the switch's row check) | fill as stated |
| S11 | `audit_K` and the seed lines (§11 item 16) | K | K = 10 now; K = 6 only after a K-check PASS row, by a docs-only amendment | as rendered |
| S12 | `environments` (autoresearch, §11 item 14) | autoresearch's G.5 environment | `ar-cond7a` under R1-G1B-AR-ENV as amended by R1-G1B-AR-PY, extended to G.5 by this note | as rendered (from the completion record under G5-ARPEND A) |

Not to sign in the G.5 note (decided elsewhere): XC3-FAIL A, `xc3_cap` and `skip_nodes` (the signed xc3 note,
R1-XC3-FAIL-READING); the dates (targets, not gates: R1-BX-D14-G4B); the eight-node basis (G4B-DATES A); the T1 node
scope (R1-T1-D21-SCOPE).
