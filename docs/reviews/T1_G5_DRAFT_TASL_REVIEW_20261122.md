Reviewed base: `3c3f822a` (published `main`; revision 7 was first reviewed over `9c2979a2`); revision 8 accepted at `fc018bf8e48d5483deb13cf14020f32da5f120f6`

# Independent review record — G.5 T1 label-run authorization draft on the TASL pair, revisions 7–8 (approved: false), with g5_ar_projection_tasl.py and g5_pin_check.py

**Unit.** `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` revisions 7 and 8 on `mac-g5-tasl-20261122` (revision 7,
`67d057b1`, rebased onto `3c3f822a` as `ebe7a4b7`) and `mac-g5-tasl-rev8-20261122`, with `sweep2/t1_tasl/g5_ar_projection_tasl.py`, the
new `sweep2/t1_tasl/g5_pin_check.py` (the G5-PIN B check) and their tests. Revisions 1–5 are in `T1_G5_DRAFT_REVIEW_20261121.md`;
revision 6 was reviewed with the T1 TASL code unit. Authority: R1-G5-DECISIONS (G5-AR A, G5-PIN B), R1-T1-DATA-MANIFEST,
R1-G1B-AR-ENV, R1-SWEEP2-RELEASE-DECISIONS, R1-BX-D8-CONFIRM-V31 and the frozen analysis preregistration on `main` `3c3f822a`; the
queue of 22 Nov 2026 (11:33), item 2. The draft authorizes nothing; it stays `approved: false`.

**Process.** One independent reviewer for all four rounds (a separate agent that did not write the draft), read-only, scratch
under `/tmp/g5r7rev/` and `/tmp/g5r8rev/` moved to `_to_delete/`; no secrets, labels, evaluation values or seed 7001–7010 results
read. Round 1 (revision 7) found three text-level majors (PRE-T1 A misquoted; the gate v3.1 and release authority not cited; no rule
for a late autoresearch) and twelve minors. Round 2 (revision 8) found one major (autoresearch's prerequisites had no PENDING
mechanism) and eight minors, among them `g5_pin_check.py` comparing blob ids only. Round 3 found that a docs-only amendment could
not complete items the spec carries. Round 4 accepted. Every figure of the draft was reproduced from the projection script in each
round; `g5_pin_check.py` passes on the real pins `c025f89a`/`2d09f9a9`.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `67d057b1 (rev 7)` | NOT ACCEPTED (M1–M3; m1–m12) |
| 2 | `32d84d18 (rev 8)` | NOT ACCEPTED (M1: no PENDING mechanism for autoresearch's prerequisites; m1–m8) |
| 3 | `5a95dbf0 (rev 8)` | NOT ACCEPTED (M1: docs-only amendment vs the spec; two nits) |
| 4 | `fc018bf8 (rev 8)` | ACCEPTED (one optional nit) |

**Open items.** For the author: §11 of the draft — decisions G5-W, G5-TEMP, G5-MEM (with the row amending E4 under A), G5-AUDIT, G5-DIV, G5-TASL-GPUH, G5-SLOT and G5-ARPEND; the values the signature fixes (cap 425, liveness floor, invalid-share, infrastructure and audited-band STOPs, the freeze wait and its date, the instance seed block, the seal, autoresearch's G.5 environment, CUDA IPC by C12 or the acceptance line, the K amendment). Before the signature: R1-G1B-JOIN and the seven-node REL-T1-G1B copy. For the G.5 code unit (§9), from round 4: the switch requires exactly one completion record matching `G5_AR_PREREQUISITES_<date>.md` on `main` (or a named supersession) and STOPs otherwise (STOP 15); and `autoresearch_fixedtokens` leaves `pilot_nodes` in `g4_tasl_dates_params.json` (round-1 m11).

## Round 1 (`67d057b1 (rev 7)`)

> Reviewed base: 67d057b1051c763ffcd199b8d64a7091628bc51a
>
> # Independent review: G.5 authorization draft, revision 7 (TASL pair), plus g5_ar_projection_tasl.py and its test
>
> **Scope.** I reviewed commit 67d057b1 in /tmp/pb/wt/g5 against published main 9c2979a2 (PLAN, the frozen preregistration, the split file, the signed G.4 note, the U4 census, the cross-check report). I checked the branch mac-g1b-ar-20261122 in /tmp/pb/repo and harness c025f89a..2d09f9a9 in /tmp/pb/wt/t1ar, all read-only. Nothing was modified: the worktree is clean and HEAD is unchanged. Scratch files are in /tmp/g5r7rev/_to_delete/. I read no secrets, no seed 7001–7010 results, no labels and no evaluation values. From the split file I read only the instance-to-partition assignment.
>
> ## Summary
>
> **The numbers are right.** Every number in §2.4, §2.6, §2.8, §2.9, §2.10, §2.11 and §8 reproduces exactly from `g5_ar_projection_tasl.py --today 2026-11-22`, `g4_tasl.py dates … --today 2026-11-22` and `g4_lib.g5_node`.
>
> **Citations largely check out.** The key values in §5 match R1-T1-TASL-ENV and the signed G.4 note. G5-SPLIT is correctly described as fixed by PRE-SPLIT A: the split file's sha256 matches, and I recomputed all eight nodes' T1 assignment from the rule (salt c3_t1_split/v1, seeds 5101–5112). The harness claims about 2d09f9a9 are accurate. The branch figures are accurate too: 28.227 GPU-h, 767.748 s from E2's 255.916 s, ar-cond7a 11def6ad…/Python 3.12.15, AR-ENV, and run_id g1b-ar-tasl-20261122-a.
>
> **Internal consistency holds.** There are ten open decisions. P1–P11, STOPs 1–13 and C1–C13 are all consistent and cross-referenced correctly. The draft stays `approved: false`.
>
> **Script and test.** Both are correct. The script reads only the params JSON. The K = 6 placeholder never appears in the output.
>
> **Targeted tests:** `test_t1_tasl_g5_ar_projection.py` and `test_t1_tasl_g4.py`, 33 passed.
>
> **Why not accepted.** There are three text-level major problems:
> - the frozen PRE-T1 A is misquoted, and the misquote changes how G5-AR B is described;
> - the gate and release authority published since revision 6 is stale or not cited (gate v3.1, release decisions, PRE-STAGE/PRE-DELTA);
> - G5-AR A has no rule for a late autoresearch, although PRE-T1 A freezes the primary T1 node set irrevocably.
>
> ## Findings
>
> **M1. PRE-T1 A is misquoted, so G5-AR B's consequence is wrong.**
> - **Where:** draft l.41 (§1 R1-SWEEP2-PREREG row), l.311 and l.316–318 (§2.11).
> - **Problem:**
>   - The frozen preregistration (`C3_SWEEP2_ANALYSIS_PREREG_20261121.md` l.166–170) says under PRE-T1 A: "A later read with more T1 nodes is **not allowed**." A preregistered secondary read exists only under option B, which was not chosen.
>   - The draft says such a read "is not primary" and that under G5-AR B, if the arms-frozen record does not wait, "autoresearch enters only a non-primary later read." Under the frozen A, autoresearch would then enter **no** gate read at all without amending the preregistration. Option B is presented as more benign than it is.
>   - l.311 says "Leave-one-suite-out is then in the primary read." Under PRE-SECONDARY A, leave-one-suite-out is a descriptive analysis (no verdict) using fold arms. What it gains from autoresearch is avoiding that descriptive STOP and adding a third suite to the T1 stratum. The aggregate verdict does not depend on it.
> - **Note:** R1-G5-DECISIONS on the newer main 3c3f822a gives reasoning consistent with the correct reading, so the decision itself is not affected. The record is still wrong.
> - **Fix:**
>   - Quote PRE-T1 A verbatim, including the requirement of at least 1 train and at least 1 dev instance per node.
>   - In G5-AR B, say that without waiting autoresearch enters no gate read unless the preregistration is amended.
>   - Call leave-one-suite-out a descriptive PRE-SECONDARY analysis.
>
> **M2. Gate and release authority on 9c2979a2 is stale or not cited, despite the revision note's claim.**
> - **Where:** l.16–17 and l.26 (the revision note), l.51 (§1 R1-BX-D8-CONFIRM row), l.380–381 (§3 checkouts), §5, and §6 l.496–505.
> - **Problem:**
>   - **Gate:** R1-BX-D8-CONFIRM-V31 (PLAN l.1358) replaced the gate bound by R1-BX-D8-CONFIRM: gate v3.1 @ `31dab9ef`, sha256 `a3f7d002…`. PRE-WDBC B uses v3.1, and the preregistration's §6 STOP binds "the v3.1 row". The draft still binds `6aa9985c`/`ffb70d7a…` and, in §6 item 1, "gate v3".
>   - **Release decisions:** R1-SWEEP2-RELEASE-DECISIONS is not cited.
>     - Its REL-T1-G1B amends PRE-DELTA: T1 σ_node comes from each node's G.1b summary "on the T1 host of R1-T1-HOST-TASL", copied out of the sealed tree by a reviewed step with its sha256, before the T1 train/dev row.
>     - §3 instead has the G.5 job read the summaries directly from the sealed run directories.
>     - REL-SCOPE A is not cited either.
>   - **Release staging:** PRE-STAGE A (code lock for both sources; no evaluation value of any instance before the test release) is not cited. Neither is preregistration §4 steps 4–5 (the test release cites the arms-frozen record and releases the test label blocks and every evaluation block).
>   - **§6 release rows:** they omit the preregistration's sha256 (`aa1a961b…`), the G.1b summary sha256s that PRE-DELTA requires in the T1 train/dev row, and the arms-frozen record. §1 (l.51) still says the T1 seal "needs its own release rows" as if no release machinery existed.
> - **Fix:**
>   - Add R1-BX-D8-CONFIRM-V31, R1-SWEEP2-RELEASE-DECISIONS and PRE-STAGE/PRE-DELTA to §1.
>   - In §6: gate v3.1 and its sha256, the preregistration sha256, and the G.1b summary sha256s via the REL-T1-G1B step in R1-T1-LABELS-UNSEAL. The test row cites the arms-frozen record and releases test labels plus evaluation blocks.
>   - Align §3's G.1b summary read with REL-T1-G1B.
>   - Add the preregistration and gate sha256s to §5.
>   - Drop "§2–§6 otherwise unchanged" from the revision note.
>
> **M3. G5-AR A has no declared rule for a late autoresearch.**
> - **Where:** §2.11 option A (l.305–312), §4, §7.
> - **Problem:**
>   - Under PRE-T1 A, the T1 node set is frozen in the arms-frozen record once and for all.
>   - Option A lets the seven nodes start before autoresearch's own prerequisites: the AR-ENV row, the TASL-2 host check at 2d09f9a9, the third-note G.1b with D21 and P10, and the G5-PIN code.
>   - It never says how long the arms freeze waits for autoresearch, or who decides to freeze without it. STOP 5 covers a D21 failure and "After a node STOP" covers STOPs, but a lag is not a STOP.
>   - The primary read's T1 node set, which is declared scientific content, could therefore be settled at run time without an author rule.
> - **Fix:** add to G5-AR A, with a matching STOP:
>   - the arms-frozen record waits for autoresearch's train/dev release;
>   - if that release is not done by a stated date or condition, the coordinating agent STOPs for the author, and only an author row may freeze the arms without autoresearch.
>
> **m1.** l.109: "PRE-MEM C takes T1 with one mode under A ('the same rule as T0 under B')". In the preregistration (l.88), the parenthesis refers to G5-MEM **B**. Fix the attribution.
>
> **m2.** l.39 and l.375 attribute "G.1b launches from exactly `985dd45d`" to R1-G1B-TASL-DECISIONS. That row names paper_commit `10fd3343`. The 985dd45d rule comes from the signed G.4 note (l.28), which also allows the docs-only child `dbdbd2b6`. Cite the G.4 note and mention dbdbd2b6.
>
> **m3. The A/B date comparison mixes G.1b assumptions.**
> - **Where:** l.290–292 and l.313–314.
> - **Problem:** A uses 2 days of remaining G.1b (15 Dec). B's "B.7 stays 8 Dec" uses 1 day. Autoresearch's G.1b (third note, 28.2 GPU-h on TASL-2) is ordered by R1-G1B-NOTE2-DECISIONS whichever way G5-AR goes. B keeps 8 Dec only if that G.1b is deferred until after the seven nodes' labels. Like for like, the difference is 6 days (14 vs 8 Dec, or 15 vs 9 Dec).
> - **Fix:** state B's assumption, or give B at 2 days.
>
> **m4.** l.273: "3.4 × the slowest of the other nodes (mlab_imdb, 64.1 s on the Ada)" compares a 4090 time with Ada times. The census (l.97) gives autoresearch's Ada B1 as 67.901 s, a 3.225× slowdown across hosts on the option-A path. Say so: most of autoresearch's cost is that slowdown, not intrinsic node weight.
>
> **m5. Two cap statements are incomplete.**
> - §2.9, l.237–238: with autoresearch, "campaign waves only" gives ≈ 448 GPU-h at share 0.8, which is above the 425 cap. Say so, as is done for the seven nodes.
> - §2.4, l.126–127: "both still within cap B" holds only at share 0.6. At 0.8, `reuse_parent_runs: false` gives 235.6 GPU-h (> 230) and 445.5 GPU-h (> 425).
>
> **m6. The script bypasses the TASL wrapper.** `g5_ar_projection_tasl.py` l.75 calls `g4_lib.recompute_dates` directly, not `g4_tasl.recompute_dates`. It therefore skips the wrapper's one-slot and gpu_model guards, and its tables keep `requested_slot_hours`, an HTCondor quantity the draft says does not exist on the TASL pair. The numbers are identical. Use the wrapper for the date grid and drop `requested_slot_hours`.
>
> **m7. The K = 6 placeholder name is row-shaped.** `R1-HYPOTHETICAL-K-CHECK` matches g4_lib's `^R1-[A-Z0-9-]+$` row pattern. Only the docstring and the PLAN-absence test keep it from being mistaken for a row. It is not emitted in the output (the date rows do not carry params), which is good. Consider adding `"hypothetical_k_check": true` to the K = 6 date rows.
>
> **m8. Test coverage is partial.** The test asserts only a few figures. Not asserted:
> - §2.4: 188.3 / 349.5;
> - §2.9: 39 / 43 / 55 / 62;
> - autoresearch's breakdown: 15.7 / 118.6, 10 jobs, 8 chunks; 179.8 and 89.8;
> - the eight-node MEM B and W B rows;
> - the LLM 120 s row: 337.3, 14 Dec, 17 Dec;
> - the K = 6 share 0.8 row;
> - "one day earlier with 1 day".
>
> I reproduced all of them by hand and they are correct. Asserting them would protect later revisions.
>
> **m9.** §8 l.577 says `sweep2/g4/g5_projection.py` prints §2.8. For the TASL pair it is `sweep2/t1_tasl/g5_projection_tasl.py`; the g4 version uses the H200 params.
>
> **m10.** STOP 10 names only 7004–7005 for T1 K = 6. Preregistration §3 and §6 make 7009–7010 a STOP too. Name both.
>
> **m11 (outside this unit).** `g4_tasl_dates_params.json` `pilot_nodes` still lists `autoresearch_fixedtokens`, which is stale against G4-NODE3 A. `recompute_dates` would accept an autoresearch "pilot" summary as measured. This is harmless before the pilot. Fix it with the §9 exemption list.
>
> **m12. Made stale by R1-G5-DECISIONS on main 3c3f822a** (G5-AR A, G5-PIN B):
> - "Ten author decisions are open" and P6: G5-AR and G5-PIN are now recorded.
> - The headings of §2.11 and §2.12 should cite the row.
> - The §5 `<… under G5-AR A>` placeholders can become firm values: nodes, `g1b_harness_commit`, environments, `noise_floor`, and the eight-node cap ("425 in revision 7, to be fixed in the G.5 note").
> - P9's AR-ENV is now R1-G1B-AR-ENV on main.
> - §1's "mac-g1b-ar-20261122 … not yet on main" is out of date: it was merged as c35c922d (READY 81, which confirms the draft's READY label).
> - The new R1-T1-DATA-MANIFEST row may bear on the node data pins.
> - The row records B.7 as "about 15 Dec", which is the 2-day-G.1b case (see m3).
>
> ## Verified correct (selection)
>
> - **§2.8 / §2.11 tables:** all 16 seven-node and 6 eight-node cells.
> - **§2.6 ranges:** 119–144, 167–206, 209–260, 305–386. Caps: 206.2 × 1.1 = 226.8 ≤ 230; 386.0 × 1.1 = 424.6 ≤ 425.
> - **Spans:** 7.0–8.6 and 12.7–16.1 days.
> - **Dates:** seven nodes 5/8 Dec with 0 slack; −2, −1, −3 cases. Eight nodes: 12/15 Dec −7; 16/19 Dec −11; 14/17 Dec −9; 8/11 Dec −3; 10/13 Dec −5. One day earlier at 1 day of G.1b. D.3 10 Jan, manuscript 17 Jan.
> - **Autoresearch:** 138.44 GPU-h (45 %), 179.83, 89.75; about 6 days on one slot.
> - **Revisions:** the review file holds rounds 1–5; the revision-6 text's "1–4" is now corrected.
> - **Harness:** 2d09f9a9 descends from c025f89a and changes only autoresearch's node and config files, `node_lib/ar_isolated.py` (docstring plus `torch.cuda.init()` in `cuda_open`), a report and tests.
> - **Host values:** UUIDs, drivers, URL, llama-server sha256 and build, build manifest, GGUF, freezes and the host-check sha256 `681011b2…` all match the signed G.4 note.
>
> ## Verdict
>
> **NOT ACCEPTED.** There are no blocking findings. M1–M3 are text-only fixes, and the minor findings can be fixed in the same pass.

## Round 2 (`32d84d18 (rev 8)`)

> Reviewed base: 32d84d182cb8ed7698c979662cf627d0c0dfd269
>
> # Independent review: G.5 authorization draft, revision 8 (TASL pair), plus g5_ar_projection_tasl.py, g5_pin_check.py and their tests
>
> **Scope.** I reviewed `git diff ebe7a4b7 32d84d18` in /tmp/pb/wt/g5 against published main 3c3f822a. Sources checked: the PLAN rows R1-G5-DECISIONS, R1-T1-DATA-MANIFEST, R1-G1B-AR-ENV, R1-SWEEP2-RELEASE-DECISIONS and R1-BX-D8-CONFIRM-V31, the frozen preregistration, and the signed G.4 note. I also checked the launch-chain branch mac-tasl-chain-20261122 @ 570ae410 in /tmp/pb/repo and the harness in /tmp/pb/wt/t1h (c025f89a, 2d09f9a9).
>
> Everything was read-only. All three worktrees are clean and their HEADs did not move. My scratch files are in /tmp/g5r8rev/_to_delete/. I read no secrets, labels, evaluation values or seed 7001–7010 results.
>
> ## Summary
>
> **What checks out:**
> - **Numbers.** Every date and GPU-hour figure in §2.4, §2.6, §2.8–§2.11 and §8 reproduces exactly from `g5_ar_projection_tasl.py --today 2026-11-22`. That covers all 24 date rows, the B-versus-A like-for-like comparison (9 vs 15 Dec, 8 vs 14 Dec) and "one day earlier with 1 day of G.1b".
> - **Targeted tests.** `test_t1_tasl_g5_ar_projection.py`, `test_t1_tasl_g5_pin_check.py` and `test_t1_tasl_g4.py`: 39 passed. The real-pins test ran (it was not skipped).
> - **Quotes and hashes, all exact:**
>   - PRE-T1 A is quoted verbatim.
>   - PRE-SECONDARY, PRE-STAGE, PRE-DELTA and REL-T1-G1B are correctly rendered.
>   - Gate v3.1: `31dab9ef`, and `git show 31dab9ef:r1/c3/gate.py | sha256sum` gives `a3f7d002…`.
>   - The preregistration file's sha256 is `aa1a961b…`, unchanged since main.
>   - Split file `b5967dd7…`; ar-cond7a freeze `11def6ad…`; torch312 and jax312 freezes.
>   - The corrected manifests `24cb3448…` and `54d3a74d…` match the chain's launch table. Autoresearch `ab7186d2…` matches its spec.
>   - The R1-G5-DECISIONS quotes ("425 GPU-h in revision 7, to be fixed in the G.5 note"; "The G.5 note itself still needs the author's signature") are verbatim.
> - **R1-G5-DECISIONS is applied** without over- or under-statement:
>   - eight nodes;
>   - K = 10 until a K-check row (P4, §5);
>   - cap 425, with 386.0 × 1.1 = 424.6;
>   - G5-PIN B;
>   - B.7 about 15 Dec. D.3 10 Jan and manuscript 17 Jan follow from R1-BX-D14's spans.
> - **Round-1 findings.** M1, M2 and M3 are addressed. m1–m10 and m12 are fixed. m11 is deferred to §9, as round 1 suggested.
> - **g5_pin_check.py is logically sound.** If the set of paths differing between G5-7 and G5-AR equals the pin delta, and on each delta path each side holds its own pin's blob, then every file outside the delta is identical in both commits, and G.5 touches no delta file. On the real pins it passes, with a 10-path delta matching the draft's description and `g5_changes: []`.
> - **Other checks.**
>   - `approved: false` is kept in the header, in §5 and by a test.
>   - The STOP, P and C cross-references resolve: STOP 13/14, §4 item 13, C12/C13, P11.
>   - The CUDA-IPC acceptance line's factual claims hold. At c025f89a, no seven-node parent calls `cuda_share`. At 2d09f9a9, nothing calls it, and the docstring says no node uses it.
>
> **Why not accepted.** One major problem remains:
> - The draft lets the seven nodes start before autoresearch's prerequisites.
> - It also says the note is signed only with every P recorded as PASS, with the autoresearch G.1b summary copy named in §5.
> - No mechanism reconciles the two, and §11 does not list one for signature.
>
> ## Findings
>
> **No blocking findings.**
>
> **M1. Autoresearch's prerequisites are said to gate only its own jobs, but the signature requires every P PASS. There is no PENDING mechanism, and §11 omits it.**
> - **Where:**
>   - header l.4–5 ("with every prerequisite in §7 recorded as PASS");
>   - §2.11 l.337 ("Its own prerequisites gate only its own jobs; the seven nodes may start before them");
>   - P1 l.597–598, P2 l.609–610 ("required only for autoresearch's jobs"), P9;
>   - §3 l.415–417 and §5 `noise_floor` (the note and spec name both REL-T1-G1B copies and their sha256s);
>   - §11 l.756–763 ("Rows that must exist before the note can be signed with every P PASS: … the resolution of the AR host-check STOP and the third note"; "The signature itself: … the REL-T1-G1B copies, and P1–P11 recorded as PASS").
> - **Problem:**
>   - Read literally, the note cannot be signed until autoresearch's host check at 2d09f9a9 passes, its G.1b under the third note is complete (P2: D21 verdicts), its summary has been copied by REL-T1-G1B, and P10 is declared for it.
>   - That contradicts §2.11 A, and nothing says how an autoresearch-only prerequisite is recorded at signature.
>   - The G.1b precedent (XC A: "signed now with P7 PENDING", with a later publication rule) is not used.
> - **Failure scenario:** the AR host check is STOPped right now (Python 3.12.16 vs 3.12.15). Either:
>   - the seven nodes' labels wait for an unrelated autoresearch fix, and B.7 slips past the accepted ~15 Dec; or
>   - the coordinating chat signs or publishes with autoresearch items unresolved, which no text authorizes.
> - **Fix:** choose one, and put it in §11 for the author.
>   - (a) Option (a) has four parts:
>     - P1 (the 2d09f9a9 host check), P2 (autoresearch), P9 (autoresearch), P10 (autoresearch) and autoresearch's REL-T1-G1B copy may be recorded PENDING at signature;
>     - the switch refuses autoresearch's jobs until each PASS record is committed (path and sha256);
>     - say who commits it and under what check (e.g. the coordinating chat, without a further author decision, as for note 2);
>     - the §5 `noise_floor` line gets autoresearch's copy by that amendment.
>   - (b) The signature waits for all of them. Then delete "the seven nodes may start before them" and say so in the dates.
>
> **Minor findings**
>
> **m1. Three different statements of G5-TASL-GPUH B against the 425 cap.**
> - **Where:** §2.6 l.210, §2.9 l.260–261, §11 item 6.
> - **Problem:**
>   - §2.6 says both cards counted "all exceed 425".
>   - §2.9 says campaign-waves-only at share 0.6 gives about 360, within 425.
>   - §11 says "cap 425 exceeded at share 0.8".
>   - Under the recommended G5-SLOT A with one server start (whole-span holding), B gives about 611 at 0.6, also above 425.
> - **Failure scenario:** the author picks B believing 425 holds at 0.6.
> - **Fix:** use one statement in all three places: within 425 only at share 0.6 and only if the server is stopped during audits; otherwise above 425.
>
> **m2. §11 lists the T1 release rows as rows that "must exist before the note can be signed".**
> - **Where:** §11 l.757–759.
> - **Problem:** R1-T1-LABELS-UNSEAL and R1-T1-LABELS-TEST-RELEASE come after the labels exist, so after G.5 runs. They cannot precede the signature. The draft itself says "not before the labels exist".
> - **Fix:** move them to a separate "after the table" list.
>
> **m3. The CUDA-IPC requirement is attributed to R1-G5-DECISIONS, which does not contain it.**
> - **Where:** revision note l.33–34 (listed under "R1-G5-DECISIONS … is applied"); §5 l.526–527 ("R1-G5-DECISIONS asks for the host test on TASL-2 or this line").
> - **Problem:** the PLAN row says nothing about CUDA IPC. The source is the coordinator's queue, on the basis of review condition C1 and the G.4 note's P1, which limits its acceptance to the pilot.
> - **Failure scenario:** a note check or reader cites a row for a requirement the row does not contain.
> - **Fix:** attribute it to C1, the G.4 note's P1 (which is pilot-only) and EVIDENCE status, not to R1-G5-DECISIONS.
>
> **m4. The late-autoresearch deadline is a B.7 date used as a release deadline, and its relation to V31 is unstated.**
> - **Where:** §2.11 l.343–348, STOP 14, §5 `ar_wait`.
> - **Problem:**
>   - 19 Dec is the projected B.7 (K = 10, share 0.8). The model puts B.7 three days after labels are done.
>   - A train/dev release on 19 Dec therefore implies B.7 around 22 Dec, which the text does not say.
>   - The wait also specializes R1-BX-D8-CONFIRM-V31's "If only some T1 nodes have labels by B.7, read … on the available labelled T1 nodes" for autoresearch, without saying so.
>   - The wait rule covers only autoresearch. A late, un-STOPped seven-node job is covered only implicitly, because nodes run in sequence, but the draft declares no node order.
> - **Note:** the rule is otherwise coherent with PRE-T1 A, its "later read … not allowed" and "nodes that STOP at G.5 follow the G.5 rule".
> - **Fix:**
>   - use the labels-done date (16 Dec) as the deadline, or state that B.7 then follows by about 3 days;
>   - say that the signed rule refines V31's partial-T1 read for autoresearch;
>   - either declare autoresearch last in the node order, or make the wait cover every un-STOPped node of the table.
>
> **m5. The census erratum is cited without the sha256 of its reviewed bytes, and its publication status is not stated.**
> - **Where:** §1 R1-T1-DATA-MANIFEST row (l.58), §5 `data_manifests`.
> - **Problem:**
>   - The erratum record is on `ops-t1-data-manifest-20261122` @ `ac298f25`, neither on main nor on the chain branch.
>   - The chain notes cite it with sha256 `9b40944be4df5f214066d689f7f0537590ed95895f9754b55630d8e774077799`. Citing reviewed bytes was the chain review's round-6 M1.
>   - §1 and §3 also call the chain "READY 83, published by merge", but 570ae410 is not on main yet, and "READY 83" appears nowhere in the repo.
> - **Fix:** add the erratum's sha256. State that the chain was delivered and accepted (review round 7 at cd50e36f, confirmed at e740dae7) but is not yet on main.
>
> **m6. g5_pin_check.py compares blob ids only, so mode and type changes on pin-delta paths pass undetected.**
> - **Where:** `_blob()` in `sweep2/t1_tasl/g5_pin_check.py`.
> - **Problem:** I built two synthetic repositories in scratch.
>   - A `chmod +x` of a pin-delta file in G5-7 passed the check.
>   - Replacing a pin-delta file with a symlink of the same content also passed.
>   - Paths outside the delta are covered, because `git diff --name-only` lists mode changes there.
>   - The harness has submodules (`harness/claw-code`, …), and a user-level `diff.ignoreSubmodules` setting would hide gitlink changes from `_changed`.
> - **Risk:** low, but the check's claim "byte-identical … G.5 changes no pin-delta file" is not exact.
> - **Fix:**
>   - compare `git ls-tree <commit> -- <path>` output (mode, type and object);
>   - pass `--ignore-submodules=none` (or `-c diff.ignoreSubmodules=none`) to the diff;
>   - add tests for a mode change, a type change, a one-sided deletion outside the delta, and the CLI usage error (rc 2 on a wrong argument count).
>
> **m7. P4 and §5 `audit_K` do not say who amends the signed note to K = 6.**
> - **Where:** P4 l.620–622, §5 l.505.
> - **Problem:** after a K-check PASS row, the signed note's `audit_K` and seed lines are "amended … before the first audit chunk", but the draft does not say whether the coordinating chat may amend the signed note on the strength of that row alone or whether the author re-signs.
> - **Fix:** state who amends and under what check, and list it in §11.
>
> **m8. Stale or loose wording.**
> - l.54: "How it enters G.5 is decision G5-AR". It is decided (A).
> - l.44–45: "the others in §2 are open". G5-SPLIT (§2.7) is fixed by the preregistration.
> - The §2.6 heading and the §5 `cap_gpu_hours` line attribute "425" to R1-G5-DECISIONS. The row only raised the cap and left the figure to the G.5 note. The body text (l.206–209) gets this right.
> - l.26–27 cites `reviews/T1_G5_DRAFT_TASL_REVIEW_20261122.md`, which does not exist in the commit. Publish it with the merge, or mark it as to be published.
>
> ## Verdict
>
> **NOT ACCEPTED.** M1 is a text-level fix: a PENDING mechanism for autoresearch's prerequisites, put to the author in §11. It can be made together with the minors. The numbers, the two scripts and the pin check's logic are correct and need no rework beyond m6.

## Round 3 (`5a95dbf0 (rev 8)`)

> Reviewed base: 5a95dbf0e11ea787f21b6c15d7c0c7ba16563438 (round 3; the diff 32d84d18..5a95dbf0, on top of my round-2 review of 32d84d182cb8ed7698c979662cf627d0c0dfd269)
>
> # Independent review, round 3: G.5 draft revision 8 at 5a95dbf0 (fixes for the round-2 findings)
>
> **Scope.** I reviewed `git diff 32d84d18 5a95dbf0`: the draft, `g5_pin_check.py` and its test. Everything was read-only. /tmp/pb/wt/g5 (HEAD 5a95dbf0) and /tmp/pb/wt/t1h (HEAD c025f89a) are clean and their HEADs did not move. I read no secrets, labels, evaluation values or seed 7001–7010 results.
>
> On scratch: my round-2 `_to_delete` directory had already been removed by someone else when I started this round. This round's scratch is in /tmp/g5r8rev/_to_delete/r3.
>
> ## Summary
>
> **Checks:**
> - **Targeted tests:** `test_t1_tasl_g5_ar_projection.py`, `test_t1_tasl_g5_pin_check.py` and `test_t1_tasl_g4.py`, 41 passed. The real-pins test ran.
> - **Pin check on the real pins:** `g5_pin_check.py /tmp/pb/wt/t1h c025f89a 2d09f9a9` gives rc 0 and `g5_changes: []`.
> - **Projection script:** runs unchanged. The new text changes no figures.
> - **Draft status:** still `approved: false`.
>
> **Round-2 findings:**
> - **m6 is fixed.** I re-ran my own synthetic repositories against the new code. A chmod on a pin-delta file now STOPs. A file turned into a directory STOPs. Edits and chmods on a delta path with spaces and brackets in its name STOP. The new tests cover the cases listed. `_entry` filters ls-tree output by exact path, so wildcard-like characters are harmless.
> - **m1 is fixed.** §2.6, §2.9, §5 and §11 item 6 now say the same thing.
> - **m2 is fixed.** The release rows are under "After the table".
> - **m3 is fixed.** CUDA IPC is attributed to the queue on the basis of C1 and the G.4 note's pilot-only P1.
> - **m5 is fixed.** I verified it:
>   - the erratum at `ac298f25` has sha256 `9b40944b…`, and `ac298f25` is on `origin/ops-t1-data-manifest-20261122`;
>   - `cd50e36f` and `e740dae7` exist, and `e740dae7` is in the chain at 570ae410;
>   - "READY 83" is gone from the draft.
> - **m8 is fixed.**
> - **m4 is fixed.** The freeze wait covers every un-STOPped node, the deadline is a release date (16 Dec), and the draft states that it refines V31. It is coherent with PRE-T1 A.
> - **m7 is fixed in the text.** See M1 for its mechanics.
> - **Round-2 M1 is answered in substance** by G5-ARPEND (§2.13) and STOP 15. The header, §2.11, P1, P2, P9, P10, §5 and §11 all follow it. §11 now separates what is needed before the signature, while the table runs, and after the table, and nothing already decided is listed as open.
>
> **Why not accepted.** One major remains. The "docs-only amendment" that G5-ARPEND A and the K amendment rely on contradicts what the draft says the G.5 spec carries.
>
> ## Findings
>
> **No blocking findings.**
>
> **M1. "Docs-only amendment" conflicts with the spec naming autoresearch's copy and environment (and possibly K).**
> - **Where:**
>   - §2.13 A ("fills autoresearch's part of `noise_floor` by a docs-only amendment of the note");
>   - §5 `noise_floor` and `audit_K`, P4, §11 items 8 and 16;
>   - against §3 l.450 ("the G.5 note **and spec** name those copies and their sha256s") and §9 l.742 ("Autoresearch's **spec entry** (environment `ar-cond7a`, its G.1b summary copy, its harness family)").
> - **Problem:**
>   - Under G5-ARPEND A, autoresearch's REL-T1-G1B copy does not exist at signature. Its environment may also change through the row that resolves the host-check STOP.
>   - If the spec carries the copy and the environment, as §3 and §9 say, then completing them changes the spec, not only `docs/`. The same applies to `audit_K` and the seed lines, if the spec carries K, as the G.4 spec carries W and the temperature.
>   - A spec change changes the spec sha256 the note and switch bind. Under the TASL launch binding, that has meant a re-issued spec on a launch commit (the R1-T1-DATA-MANIFEST chain), not a docs-only edit.
>   - Yet the author is asked to pre-authorize these steps as docs-only, "without a further author decision".
> - **Failure scenario:**
>   - The §9 code unit builds the spec as §3 and §9 describe.
>   - When the completion record or a K-check row arrives, the docs-only amendment does not match the spec, and the switch STOPs autoresearch's jobs or the K change.
>   - Or the coordinating chat re-issues the spec on a new launch commit, which the signed text does not cover.
> - **Fix (text-level), choose one:**
>   - **(a)** Say that the spec carries no autoresearch summary copy and no fixed autoresearch environment, but a PENDING marker. The switch then takes autoresearch's copy, environment and P10 declaration from the completion record on `main`, checked by sha256 (STOP 15). Likewise the spec carries both seed blocks, and the switch reads `audit_K` from the note as amended, checking the K-check row is on `main`. Then correct l.450 and l.742 to match.
>   - **(b)** Say that these completions re-issue the spec on a reviewed launch commit. State who does it and that it needs no further author decision, and drop "docs-only".
>   - Either way, list the chosen mechanism in §11 items 8 and 16.
>
> **Minor**
>
> **m1 (nit). The freeze-wait deadline leaves no margin in the projected worst case.**
> - **Where:** §2.11, STOP 14, §5 `freeze_wait`.
> - **Problem:** the proposed release deadline (16 Dec) equals the projected labels-done date at share 0.8. The train/dev release is an author row that comes after labels are done and after the REL-T1-G1B copies. So in that projection STOP 14 fires by construction. That is harmless, because it only calls the author, but it is worth saying, or the date could carry a small margin, when P7 recomputes it.
>
> **m2 (nit). STOP 14's author row can be needed during the table, not only after it.**
> - **Where:** §11 "After the table: … the freeze wait's author row only if STOP 14 fires".
> - **Problem:** STOP 14 also fires on a node STOP at G.5, which happens while the table runs.
> - **Fix:** move that clause, or word it "during or after the table".
>
> ## Verdict
>
> **NOT ACCEPTED.** M1 is a small text fix to §3, §9, §2.13, P4 and §11. Everything else from round 2 is resolved, and the code (`g5_pin_check.py` and its tests) is correct.

## Round 4 (`fc018bf8 (rev 8)`)

> Reviewed base: fc018bf8e48d5483deb13cf14020f32da5f120f6 (round 4; the diff 5a95dbf0..fc018bf8. Earlier rounds were reviewed at 32d84d182cb8ed7698c979662cf627d0c0dfd269 and 5a95dbf0)
>
> # Independent review, round 4: G.5 draft revision 8 at fc018bf8
>
> **Scope.** I reviewed `git diff 5a95dbf0 fc018bf8`. It changes only the draft: `sweep2/` and `r1/` are byte-identical to 5a95dbf0. Everything was read-only, and /tmp/pb/wt/g5 is clean at fc018bf8. Scratch is in /tmp/g5r8rev/_to_delete/r4 (round 3's is in /tmp/g5r8rev/_to_delete/r3).
>
> The targeted tests (`test_t1_tasl_g5_ar_projection.py`, `test_t1_tasl_g5_pin_check.py`, `test_t1_tasl_g4.py`) give 41 passed, with the real-pins test running. The draft stays `approved: false`.
>
> ## Summary
>
> **M1 (round 3) is fixed with option (a), and every place that described the old mechanism now agrees.**
> - **§2.13 A:**
>   - the spec carries PENDING markers for autoresearch's summary copy, environment and P10;
>   - the note's `noise_floor` and `ar_prerequisites` lines name the completion record's path pattern;
>   - the switch reads those items from the record on `main` and checks every cited sha256 (STOP 15).
>   - So neither the spec, nor its bound sha256, nor the signed note changes, and no launch commit is re-issued.
> - **§3:** the note and spec name only the seven-node copy, plus autoresearch's copy under G5-ARPEND B. The old "note and spec name those copies" wording is gone.
> - **K amendment (§5 `audit_K`, P4, §9, §11 item 16):** the spec carries both seed blocks and does not change. The amendment is a docs-only change to the note. The switch reads `audit_K` from the amended note and checks that the K-check row is on `main`.
> - **§9:** the spec entry describes the PENDING markers and both seed blocks.
> - **Stale wording:** none is left. There is no "fills autoresearch's part … by a docs-only amendment" and no old deadline.
>
> **m1 (round 3) is fixed.** The deadline is 18 Dec: labels done 16 Dec, plus 2 days for the copies and the release row. B.7 is about 21 Dec, and the text gives the reason for the margin. It is applied consistently in §2.11, STOP 14, §5 and §11 item 11. The "19 Dec" in the §2.11 table is the projected B.7, which is correct.
>
> **m2 (round 3) is fixed.** The STOP-14 row for a node STOP is under "while the table runs", and the deadline case is under "after the table".
>
> **§11** now lists exactly what the author signs:
> - eight decisions, G5-ARPEND included;
> - the values the signature fixes, items 9–16;
> - what is needed before the signature, while the table runs, and after the table.
>
> Nothing already decided is listed as open, and nothing is missing.
>
> ## Findings
>
> **No blocking or major findings.**
>
> **m1 (nit, optional). The completion record is named by a path pattern, but the draft does not say what happens if more than one file matches it.**
> - **Where:** §2.13 A, and the §5 `noise_floor` and `ar_prerequisites` lines.
> - **Problem:** the pattern is `docs/r1/reports/<…>/G5_AR_PREREQUISITES_<YYYYMMDD>.md`. A corrected record committed later would give two matches, and the text does not say which one the switch uses.
> - **Fix:** either say the switch requires exactly one matching record on `main` and STOPs otherwise (STOP 15), or say a later reviewed record supersedes an earlier one by naming it. This can go into the G.5 code unit (§9) without another round of the draft.
>
> ## Verdict
>
> **ACCEPTED.**

---

Code-Commit: fc018bf8e48d5483deb13cf14020f32da5f120f6
Verdict: ACCEPTED

Accepted: G.5 draft revision 8 at `fc018bf8` (`approved: false`), with `g5_ar_projection_tasl.py` and `g5_pin_check.py`.
