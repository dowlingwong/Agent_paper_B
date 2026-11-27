**AI-assisted (Claude, independent reviewer subagent, 23 Nov 2026).** Tier E, diff check only. I did not write the change.

**Verdict: accepted.** There are three NITs and no MAJOR or MINOR finding. The NITs are optional and change no value or pin.

# D.3 drafts: round-4 diff check of `e0fc6758` (reserved seeds 3301–3420)

Scope: `git diff a4053eac e0fc6758`, which is the one commit after the accepted state (review
`docs/r1/reviews/D3_PREDECLARATION_REVIEW_R3B_20261122.md`, committed at `a4053eac`). The change is checked against PLAN row
R1-SCREEN-MEASURE-CHOICES (6) (`/home/claude/wt/bplan/docs/r1/PLAN.md` line 1422, branch `author-minsub-20261122` @
`d3f03e2c`). The screening branch `mac-screen-measure-20261123` (@ `03a9e157`) was read with `git show`, and its seed
test was run read-only in its worktree `/home/claude/wt/smeasure`. Everything ran locally. No sealed, label, evaluation
or test-block file was opened. No code or draft was edited.

## Checks

1. **The change does only what it says.** It touches 3 files, with 7 insertions and 4 deletions. `git diff --check` is
   clean.
   - `r1/c3/d3_analysis.py` lines 148–149: adds one comment line and one `RESERVED_SEED_NAMESPACES` entry,
     `(3301, 3420)`. No other line changed. The label's text before " (" is unique
     ("supplementary screening measurement"), so the `label.split(" (")[0]` lookup in the tests is unaffected.
   - `D3_PREDECLARATION_DRAFT_20261122.md`:
     - adds one row (line 148) to the §4.2 reserved-namespace table;
     - in §9 (lines 423–424), replaces the sha256 and adds a parenthetical that names the addition;
     - in the §14 key block (line 605), replaces the sha256.
   - `D3A_AUTHORIZATION_DRAFT_20261122.md` line 29: in the pending text of `analysis_sha256`, replaces the draft value
     and changes "revision-3 draft value" to "draft value after the 23 Nov 2026 reserved-seed addition". The meaning is
     the same.
   - No other line changed in meaning.
   - PLAN row (6) asks for exactly this: "Seeds 3301–3420 are added to the D.3 pre-declaration's reserved list". The
     Paper C half of (6) concerns another branch.
   - Source citation: the block is `SEED_BLOCK = tuple(range(3301, 3421))` in `r1/noise/screen_design.py` line 55 on
     `mac-screen-measure-20261123`. The new row cites that file, which is correct (`screen_seeds.BLOCK` holds the same
     range).
2. **The tests and the namespace check pass.**
   - `python3 -m pytest -q r1/tests/test_d3_analysis.py -p no:cacheprovider`: **31 passed**.
   - `d3_analysis.check_namespaces()` returns without error, and so does `python -m r1.c3.d3_analysis namespaces` (exit
     0). The report has 15 reserved entries. The new entry is reported as `[3301, 3420, 120]`.
   - The D.3 blocks are 6201–6218, 6301–6302, 6311–6329, 6501–6679 and 6701–6880. None meets 3301–3420.
   - The nearest reserved neighbour is 3001–3030 (D21 joint seeds), which is disjoint from 3301–3420.
3. **The sha256 pins are correct.**
   - `r1/c3/d3_analysis.py` at `e0fc6758` (blob `74ca065c`) has sha256 `48126ffd411531bafbd507fa02076d00456f301de24e0a250dc0833a7b848e63`.
     It appears three times, and all three copies equal this value: pre-declaration §9 (line 423), §14 (line 605) and
     the D.3a note (line 29).
   - The D.3a note requires its value to equal "the pre-declaration's §14 value", and it does.
   - The tests file is unchanged (blob `90e0818b` in both commits). Its sha256 is `7d5d8d04323770de953d31eebd970346fa49ec068e2899b02191adffc7c3881d`,
     which equals §9 line 425.
   - The old value `cb5687e9…ebb3` (the file at `a4053eac`, blob `b20cf020`, re-computed) remains only in the historical
     reviews `D3_PREDECLARATION_REVIEW_R3_20261122.md` line 12 and `..._R3B_20261122.md` line 6. They record the state
     they reviewed, so the value is correct there.
   - A `git grep` over all local branches finds no other copy.
4. **The screening unit's own check is not affected. Its pin of blob `b20cf020` is correct and must stay.**
   - What the test checks: `r1/noise/screen_seeds.py` line 38 has `D3_SOURCE = (…, "b20cf020050edd79fd48f233f310850ac20cd297")`.
     `test_reserved_copy_equals_d3_blob` in `r1/tests/test_screen_measure.py` parses that blob and requires its
     `RESERVED_SEED_NAMESPACES` to equal the copy in `screen_seeds.py`.
   - The test still passes. The blob is still in the object store, reachable from `a4053eac`, an ancestor of the D.3
     head. In `/home/claude/wt/smeasure`, `pytest -k SeedTest` gives 4 passed, none skipped.
   - The pin is correct as a pin of the older blob. I compared the two dicts with `ast`:
     - blob `74ca065c` = blob `b20cf020` plus exactly one entry, the screening block itself;
     - the 14 common entries are identical and in the same order;
     - the copy in `screen_seeds.py` equals the older dict.
   - Re-pinning would break the check. Pointed at `74ca065c`, the equality test fails. If the copy were also updated,
     `check_block()` would refuse the block against its own reservation. I checked this:
     `SeedClash: block meets reserved namespace 'supplementary screening measurement …'`.
   - The pin also cannot change without cost. The screening authorization note pins
     `sha256_screen_seeds: dff8252b…2c4e` (line 70), which I re-computed and which still equals the file. Any edit to
     `screen_seeds.py` would require refilling that pin and a re-check.
   - **Nothing on the screening branch must change.**
     - The runner calls only the static `check_block` (`screen_measure.py` line 338), which is unaffected.
     - `seed_scan.json` is a dated record of 205 refs, with the ref-list sha256 recorded. A re-run now would also list
       the reservation itself (the new `3301`/`3420` tokens in `d3_analysis.py` and the D.3 pre-declaration) and would
       give a different ref-list hash. That is expected and is not a clash.
     - See NIT N3 for an optional status line.
5. **Statements of the reserved list or its count.**
   - Neither document states a count of reserved namespaces.
   - The test file asserts no count and does not cross-check the new interval. This is consistent with the row's
     "not cross-checked by import" and with the code comment "each interval that has a module constant".
   - The D.3a note does not restate the list. Its P10 refers to the separate verify-seed check, which imports
     `RESERVED_SEED_NAMESPACES` and therefore picks up the new entry automatically.
   - One prose sentence in §4.2 is now incomplete (N1).
   - Screening §12 item 6 also offered the G.4 allow-list 4001–4099 "if its author agrees". PLAN row (6) names only
     3301–3420, so leaving 4001–4099 out is consistent with the row. No D.3 block meets 4001–4099.

## Findings

**N1 (NIT).** `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md` lines 132–133: "The G.4 seeds and the Track S
blocks are checked only as declared intervals."
- Problem: the new screening block is also checked only as a declared interval, and its table row (line 148) says so.
  The sentence enumerates these cases and now omits it.
- Fix: "The G.4 seeds, the Track S blocks and the supplementary screening block are checked only as declared intervals."
  This is a text-only change with no sha effect.

**N2 (NIT).** Same file, line 148 (table row): the source "R1-SCREEN-MEASURE-CHOICES (6)" is not in the PLAN version the
document pins.
- That version is header line 14, `author-minsub-20261122` @ `d9acb501`, PLAN.md sha256 `75b5ae36…`, which is also the
  PLAN.md on this branch. The row was added in `d3f03e2c`.
- Effect: a reader checking against the pinned PLAN will not find the row.
- Fix: add "`author-minsub-20261122` @ `d3f03e2c`" to the row's source cell. Alternatively, move the header's PLAN pin
  when the later §13 settlements (R1-D3-CHOICES, also after `d9acb501`) are brought in before signing.
- Change the document only. Editing the code comment at `r1/c3/d3_analysis.py` line 148 would change the script's sha256.

**N3 (NIT, other branch, optional).** On `mac-screen-measure-20261123`, the following state the D.3 addition as still to
be done, or describe `b20cf020` as the current D.3 head blob:
- `SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md` lines 262–263 and §12 item 6 (lines 586–587, "Not changed here");
- `reviews/SCREEN_MEASURE_PREDECL_REVIEW_20261123.md` line 178 ("still current at that branch's head `a4053eac`").

The review line is a dated record and stays. If the screening drafts are touched again:
- add one sentence that item 6 was done at `e0fc6758` (blob `74ca065c`, which differs from `b20cf020` only by the
  3301–3420 entry);
- keep `D3_SOURCE` at `b20cf020` (check 4).

**Verdict: accepted.** This covers the D.3 pre-declaration draft, the D.3a authorization note draft,
`r1/c3/d3_analysis.py` (sha256 `48126ffd…8e63`) and its tests (sha256 `7d5d8d04…881d`), as of `e0fc6758`.
