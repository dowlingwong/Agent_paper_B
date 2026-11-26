Reviewed base: `c2804f58` (READY 103 on READY 100 on main 3024db3f); accepted at `342b53b36`, confirmed at `dcaad5a73be36f718d6c922e7f23829669a7d19b`

# Independent review record — texts made stale by READY 97: G.5 authorization draft revision 10 (§3, §5, the spec sha256 and the re-rendered `t1_table_readings` line), the T1 release rows draft, dated notes

**Unit.** Text only, on `mac-t1-stale-texts-20261124` (on `c2804f58`): `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` revision 10 (§3's σ̂_node/δ_n text by D6-σ B, D6 A and the PRE-DELTA reading; the copy step with its five files and the 7001–7010 seed guard; STOP 5 as built plus `noise_precheck`/`check_usable`; D9 B; the launch's `plan_row` check of R1-T1-FEAT-DECISIONS; D7 per R1-T1-A5-DECISIONS with D7-DIFF B (READY 103) and its merge deadline; the history-drop report as a post-release step; R1-G5-DIFF-RECOUNT, the requirement of the recount harness commits for the G.5 launch, the exact `measurement_path_check` exemptions, and D7-DIFF B's O1 (open, (a) recommended); the `campaign_attribution` note line of READY 96, verbatim, as its own signed-text block in §5 and in §11 item 19; P5 citing the follow-ups review; main-state updates for 3024db3f) with the §5 key-lines block replaced by the `key-lines` render (K = 10; K = 6 differs only in `audit_K` and the two seed lines) — relative to revision 9 only `t1_table_readings` (D6-σ B) and `spec_sha256` (`b25fd7f1b06e3491a97f60c44af1dfede4e7147a941aa9dc87e3823542bd9d0f`) change; the harness-commit line stays PENDING with `<RENDER AFTER R1-G5-DIFF-RECOUNT: harness commits>` in the PENDING table; its change report `docs/r1/reports/g5_code_20261123/G5_DRAFT_REV10_20261124.md`; `docs/r1/proposals/T1_RELEASE_ROWS_DRAFT_20261123.md` (still `approved: false`; lines 63–64 STOP 5 and `check_usable` as built; table schema `/2` or `/1` under fallback A; the history-drop step; row texts byte-unchanged); dated notes in `reports/g5_code_20261123/T1_RELEASE_ROWS_DRAFT_20261123.md` and `reports/arms_t1feat_20261123/T1_FEATURES_20261123.md`. No code, spec, test, PLAN row, authorization or review changed. Authority: the user's message of 24 Nov 2026 (00:20), item 3.

**Full `r1/tests` suite** at `dcaad5a73` (run by the coordinating session; LightGBM off the path, fresh TMPDIR): 58 failed / 3 errors / 3860 passed / 197 skipped; the failure list `docs/r1/reports/g5_code_20261123/FULLSUITE_STALE_TIP_dcaad5a7.txt` is byte-identical to `FULLSUITE_BASE_3024db3f.txt` (61 entries): zero new failures.

**Process.** One independent reviewer, read-only, own detached worktrees; the render reproduced on clean checkouts; no data files opened. Round 1 accepted with five minors and a nit; the fixes were confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `342b53b36` | ACCEPTED (minors m1–m5, nit) |
| 2 | `dcaad5a73` | ACCEPTED (confirmation) |

**Open items.** One more `key-lines` render follows the R1-G5-DIFF-RECOUNT harness unit, when the spec's `harness_families.*.g5_commit` are filled with its tips (the `harness_commit` line and `spec_sha256` change then). Not worked in (change report §7.5): R1-G5-DIFF-RECOUNT's effect on P3, P7, §2.8–§2.11 and §8 (pending the G.4b re-pilot), the post-freeze reads amendment against §6 and C14. Listed but not edited (past reports): `G5_CODE_3B2_20261123.md` l.135, 181, 386; `G5_CODE_3A` l.283; `G5_CODE_3B1` l.32; the revision-9 report and reviews; code docstrings. The release-rows change report's table cell is left as reviewed with a dated note. READY 100 and READY 103 must be on main before the commit that publishes the signed G.5 note and spec.

## Round 1 (`342b53b36`)

> Reviewed base: 342b53b36 (mac-t1-stale-texts-20261124; base c2804f58)
>
> ## Summary
> No blocking problems; five minor ones. Own detached worktrees at `342b53b36` and `23c41a09`, removed; no `*block.jsonl` or `b1_manifests.json` opened.
>
> ## What I checked
> **1. The render.** `key-lines` for K = 10 and K = 6 on clean checkouts of both commits: rc 0, 53 lines, byte-identical across commits; K = 6 differs only in `audit_K` and the two seed lines. With the first line set to false the draft's block (`T1_G5_AUTHORIZATION_DRAFT_20261120.md:707–759`) is byte-equal to the render; `spec_sha256` `b25fd7f1…` equals `sha256sum` of the spec. The only line starting `approved:` in any changed file is the block's `approved: false`.
>
> **2. The stale-text list.** Fixed: G.5 draft §3 (σ̂_node paragraph, copy list, five files), §5 (both lines rendered; old sha `3627cc16…` only as history; the PENDING table), the proposal's lines 63–64 (STOP 5 `qualifies_D21` only; `check_usable` a separate STOP), a dated note in the release-rows change report. A branch-wide grep for `sigma_joint`, "σ_joint", "joint σ", "joint sigma" finds only the D21 criterion, E1/Track S/noise reports, listed past reports and reviews, and correct "only reported" statements.
>
> **3. Accuracy against the code.** STOP 5 a `NodeStop` at `g5_tasl.py:1561`; `noise_precheck` after STOP 5, before the freeze-wait check, `node_noise` then `check_usable`, a plain `Stop`, values in `context["noise_precheck"]`; the copy step (five files for the seven nodes, four for AR, `refuse_sealed` first, the seed guard, the count check, nine `noise_floor.seven` fields); D9 B's `D9_STOP` in three places; `T1_FEAT_TERMS` and `plan_row` with both boundaries; D7-DIFF B's table fields and schema; the history-drop command and exit codes; row quotes match PLAN.
>
> **4. No decided content changed.** Nothing under PLAN, `authorizations/` or `reviews/`; the release rows' two text blocks hash the same; the proposal `approved: false`; past reports only dated notes.
>
> **5. `campaign_attribution`.** Placement right (`note_lines` does not render it; `check_note` neither requires nor refuses it; inside the block it would break byte-equality); sha256 `5deead65…` equals `G5_FOLLOWUPS_20261123.md:114`.
>
> **6. `measurement_path_check`** (own run of `import_closure`/`measurement_paths` against `/tmp/pb/wt/t1h`). The claim holds: `diff_support.py` is in the path, also in `noise_floor`'s import closure at `c025f89a` and `2d09f9a9`. Exemptions: changes only to the four engine files directly under `trackg/` (`manager_v2_diff.py`, `campaign_v2_diff.py`, `proposal_v2_diff.py`, `pilot_g4.py`) while outside `noise_floor`'s closure; new files only `audit_g5.py`/`diagnostics_g5.py` in `trackg/`, anywhere outside `trackg/`, `nodes/`, `third_party/`, `configs/trackg/`, `node_lib/` while `noise_floor`'s closure is unchanged, and freely under `docs/`/`tests/`. It passes on `c025f89a`→`52e3c0b0` and `2d09f9a9`→`00829da1`.
>
> **7. Main state (git only).** Note 2 added by `3024db3f` with `approved: true`; the three `-xc2` step-1 verdicts `"verdict": "PASS"` (added `8c326a06`, merged `2ed97eda`); amendment, re-issued cross-check and third notes signed; no G.1b TASL summary result on main; none on `44c3d80e`; the merges and `4572e958` on main; neither A5 nor D7-DIFF B on main.
>
> ## Findings
> - **m1** Draft :1165–1170 (change report §7.3): the P5 constraint is narrower than the code (omits new modules outside `trackg/` and the four directories) and omits that `diff_support.py` is in `noise_floor`'s closure. Fix: state the exemption exactly.
> - **m2** Draft :465 (§2.12) still says "no G.5 harness commit exists yet" while citing the reviewed engines at `52e3c0b0`/`00829da1`.
> - **m3** Draft :117 (§1, R1-G4-DECISIONS cell) still says "The pilot has not run"; R1-G5-DIFF-RECOUNT (quoted at :144) says it ran.
> - **m4** Draft :1158–1164, :79–81, :1316–1317: O1 is presented as binding with option (a) chosen; the D7-DIFF B report records O1 as open with (a) recommended. Fix: "(O1 open; (a) recommended)".
> - **m5** Release rows draft, Order step 2: the history-drop report also reads the signed P3 split file and the pool tokenizers. Fix: "reads, of the G.5 outputs, only the table and that receipt".
>
> Nit: status line (:13–14) and §6 (:931) "merged onto `main` `3024db3f` as READY 100" — "with `main` `3024db3f` merged in" is clearer.
>
> VERDICT: ACCEPTED

## Round 2 (`dcaad5a73`)

> Reviewed base: dcaad5a73 (parent 342b53b36)
>
> ## Summary
> All five minors, the nit and the three extra edits are correctly fixed; nothing new is wrong. Own worktree, removed; no data files opened.
>
> **Scope.** `git diff --stat 342b53b36 dcaad5a73`: the G.5 draft (+34/−26), `T1_RELEASE_ROWS_DRAFT_20261123.md` (+2/−1), `G5_DRAFT_REV10_20261124.md` (+29/−10); nothing under `sweep2/`, `r1/`, `PLAN.md`, `authorizations/`, `reviews/`; no added line starts with `approved`.
>
> **Rendered block.** Now at draft lines 708–760, still the only `^approved:` line; byte-equal to my round-1 render and to a fresh `key-lines` render on `dcaad5a73`; spec sha256 still `b25fd7f1…9d0f`.
>
> **Release rows' text blocks** hash identically (`bb1b2da3…`) at `c2804f58`, `342b53b36`, `dcaad5a73`.
>
> **Each finding.** m1 fixed (the exemption matches the code; `diff_support.py` in the closure; relaxing the check changes noise-floor measurement code). m2 fixed (engines at `52e3c0b0`/`00829da1`; recount successors are what the check runs on). m3 fixed (pilot has run; report on an ops branch; path matches the row; G.4b noted). m4 fixed ("O1 open, (a) recommended" in the log, §9, §11, change report §7.3; §9 names (b), "Neither is chosen here."). m5 fixed (matches `serialize_t1.history_drop_report`). Nit fixed (matches merge `947ac286`).
>
> **Extra edits.** The §1 R1-T1-A5-DECISIONS cell, change report §7.1 and the log pointer (§8 → §7.5) are correct; the new change report §8 maps every finding accurately.
>
> No new findings.
>
> VERDICT: ACCEPTED

---

Code-Commit: dcaad5a73be36f718d6c922e7f23829669a7d19b
Verdict: ACCEPTED

Accepted at `342b53b36`, confirmed at `dcaad5a73`.
