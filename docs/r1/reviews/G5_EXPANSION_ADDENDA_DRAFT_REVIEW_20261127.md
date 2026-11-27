# Independent review of the four G.5 expansion addendum drafts

Task `local/20261127-29`. Two independent read-only reviewer sessions. The re-check below is the final
verdict for the drafts. The coordination report was finalized against the reviewed commit and checked
against the draft bytes before the report was routed.

## Re-check

### Re-check of corrections for the G.5 expansion addendum drafts (`local/20261127-29`)

**Correction SHA** `e18106d881ec172daae8dde49ce5bf2eae8910ec` (single parent `16764386e3eb2579655713ec5d937a6b523d5c0a`, base `cbc86fc5`)

**Verdict ACCEPTED for draft handoff only.** This does not approve publication, filling, placement or launch.

## Diff scope
- The full diff from `16764386` to `e18106d8` touches only the four `docs/r1/proposals/G5_EXPANSION_ADDENDUM_*_DRAFT_20261127.md` files, with 28 lines added and 12 removed. Each file gets the same change.
- `git diff --check` is clean. Compared against `cbc86fc5`, the only changes are the four new files.
- The untracked copies in the worktree are byte-identical to the files at `e18106d8`.

## The three minor findings
1. **REL-T1-G1B / D6 copy is closed.** `g1b_noise_floor` now reads "PENDING independently reviewed REL-T1-G1B and D6 copies of summary, assembly and runs". The result-directory files are no longer presented as meeting the requirement. The body cites them only as published inputs and states "The separately reviewed D6 copy is pending with Compute."
2. **sd matching in `label_tail` is closed.** The field now binds nu and gives scale = sd × √((nu − 2)/nu). This matches R1-G5-TAILS-CONSUMERS (1) in `docs/r1/PLAN.md:1645` and the template's `label_tail` line.
3. **Refusal-check paragraph is closed.** A new closing paragraph requires the switch review to show refusal for each of the six template cases:
   - a missing or failing G.1b completion
   - an unpublished note
   - a changed pin
   - an incompatible CPU placement
   - the wrong split
   - a 1GC supply request

   It also requires citing those checks in the final review field.

## Per-node seal citations
- The extra `g1b_seal:` key is gone. This also settles note 4 of the first review. Each seal is now cited in its draft's body.
- I recomputed every receipt digest at `cbc86fc5` and each one matches its draft. The node inside each receipt is also correct.

| Draft | Receipt | SHA-256 | `node` |
|---|---|---|---|
| ETTh1 | `SEAL_RECEIPT_gc7rc_etth1.json` | `96dad194…02d7` | `gc7rc_etth1` |
| Forest Cover | `SEAL_RECEIPT_gc7rc_forestcover.json` | `2940254a…3506` | `gc7rc_forestcover` |
| MetaMaze | `SEAL_RECEIPT_mlgym_metamaze.json` | `897fadba…de10` | `mlgym_metamaze` |
| Titanic | `SEAL_RECEIPT_titanic.json` | `13773f15…0207` | `mlgym_titanic` |

- `summary.json` (`67355b66…aa10`) and `ASSEMBLY.json` (`b4c90ec6…f077`) both match. The runs digest `c23dec91…08a7` is unchanged.

## Boundaries that still hold
- All four drafts still have `approved: false`, and each keeps 11 PENDING markers.
- `launch_code`, `node_spec_entry`, the harness, isolation and environment bindings, the PRE-SPLIT amendment and `review` all remain PENDING.
- `execution_layout` still cites only the G.1b CPU sets (16-31, 4-7, 0-3 and 12-15) and leaves the G.5 placement and lease PENDING.
- R1-G5-S9 routing is unchanged. The two `gc7rc_*` drafts stay separate descriptive outputs, excluded from SFT, arms and the primary gate. The two `mlgym_*` drafts go to T1 suite MLGym, with arms and gate only after the signed releases.

## Routing of the D6 copy (`reports/20261127-29-g5-expansion-relcopy.md`)
- The report is addressed `for: compute`.
- **Recover the existing assembly.** It names the exact assembly directory for run `g1b-x-tasl-20261126-a`. It asks Compute to check for an existing copy and the ledger first, to keep the assembly and all four seals, and to use the exact 1,840-row file (460 rows per node).
- **Exact copy hashes.** It lists the expected digests for all three files and the spec digest `d0dce058…d238`. It asks for the three paths and hashes to be reported together with each node's receipt binding.
- **No new jobs.** It says the copy needs no training job and no sealed G.5 partition read. It does not explicitly rule out re-running G.1b or assembly. Telling Compute to use the exact assembled file implies that, so this is a wording note and not a blocker.
- It calls `runs.jsonl` "the missing file". The drafts mark the summary and assembly copies PENDING as well. The report still asks for all three paths and hashes, so the two are consistent in effect.

## Defect outside the drafts (fix before routing)
- In `reports/20261127-29-g5-expansion-addenda-stop.md`, the ETTh1 row has a 61-character digest `bdf33d37…fcfc7`. The real SHA-256 of that draft at `e18106d8` is `870057740e56b6bcd866b37690352f30ad527be73b9206b85dce170ab9d03176`. The other three rows match.
- The same report still contains the placeholders `BRANCH_TIP` and `REVIEW_STATUS`.

## Constraints kept
I made no edits, launched nothing, used no SSH and touched no credentials. I read only published Markdown and JSON receipts, summaries and PLAN text at `cbc86fc5` and `e18106d8`. I opened no sealed label, test or evaluation file.

## Initial review

### Tier-E review: four G.5 expansion addendum drafts (`local/20261127-29`)

**Verdict: ACCEPTED FOR DRAFT HANDOFF**, with the minor findings below. This accepts the drafts only as unfinished drafts. It does not mean they are ready to publish or approved for any launch.

Scope: draft commit `16764386e3eb2579655713ec5d937a6b523d5c0a` against its parent `cbc86fc5b628ed328b1889f42e7b4e0235c004f3`, which equals `origin/main` in the given git dir. The commit adds only the four `docs/r1/proposals/G5_EXPANSION_ADDENDUM_*_DRAFT_20261127.md` files (4 × 47 lines). The untracked copies in this worktree are byte-identical to the committed ones.

## Findings

1. **The REL-T1-G1B / D6 copy is not resolved (minor; fix before filling).** All four drafts fill `g1b_noise_floor` with the compute worker's `summary.json` and `ASSEMBLY.json` from `docs/r1/reports/g1b_x_20261127/`. Only the runs copy is marked PENDING. Under REL-T1-G1B as amended by D6, each summary and assembly must also come out of the sealed tree through a reviewed copy step. The seven-node precedent does this with `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/{summary,ASSEMBLY,runs}.json*` plus `COPY_RECORD.json` and `crosscheck_gate.json`. No such copy record exists yet for the expansion run. The task asks whether the addendum needs that copy, and for it to go to compute if so. The drafts never answer this. They should mark the whole D6/REL-T1-G1B copy for the run as PENDING, or say it has been tasked to compute, instead of implying the result-directory files already satisfy it.

2. **The `label_tail` field leaves out sd matching (minor).** The template asks for "declared law and provenance … with nu and sd matching for Student-t" (R1-G5-TAILS-CONSUMERS). The drafts only say "PENDING node-specific P10 declaration". The filled version should name the sd-matched scale rule.

3. **The template's refusal-check paragraph is missing (minor).** The template requires confirming that these cases are refused:
   - a missing or failing completion
   - an unpublished note
   - a changed pin
   - an incompatible CPU placement
   - a wrong split
   - a 1GC supply request

   The drafts' closing paragraph covers harness descent, CPU-only admission, environment, placement and routing, but not this list. It belongs in the switch review and in the filled `review:` line.

4. **Field added beyond the template (note only).** The drafts add `g1b_seal:` (the per-node receipt), which the template does not have. The values are correct, but the addendum switch's reader, once it exists, must accept or ignore this key.

5. **Placement will need a decision when the drafts are filled (note only).** The G.1b sets for metamaze (0-3) and forestcover (4-7) are the same CPUs whose locks R1-G5-SIGNATURE S13 makes every G.5 TASL-2 job take (`cpus-0-3.lock` and `cpus-4-7.lock`). The drafts handle this correctly: the G.1b lease and budget are cited only as references and `execution_layout` stays PENDING. The filler should still expect a real placement decision here.

6. **Kit file naming (note only).** Metamaze's kit is `MOUNTAINCAR_KIT_20261125.md`. This matches `kit_record` in the G.1b spec, and that kit's captures contain `spec/mlgym_metamaze.yaml`, so it is consistent, not an error.

7. **Out of scope.** Part (1) of the task, the addendum switch, is not in this commit. The drafts correctly leave `launch_code` and `node_spec_entry` as PENDING.

The drafts make clear they are not ready to publish:
- All four have `approved: false`.
- Every field the template leaves open stays PENDING: base note and spec, launch code, spec entry, harness/isolation/environment binding, placement, label tail, PRE-SPLIT amendment, GPU-hour projection and review.
- The header says the coordinator publishes only after the main G.5 note, its prerequisites and acceptance of the filled draft.
- "Establish eligibility" is accurate wording; it claims no authorization.

## What I independently checked

- **Commit:** confirmed the commit, its single parent, that the parent equals `origin/main`, and that only the four draft files changed.
- **Task:** read `origin/coord/coordinator:tasks/local/20261127-29-g5-addenda.md` (last changed at `8a545b58`).
- **Template and PLAN:** read the published template `G5_EXPANSION_ADDENDUM_TEMPLATE_20261127.md` and its review, and the `docs/r1/PLAN.md` rows R1-G5-S9, R1-G5-SIGNATURE, R1-STEP-ORDER and R1-G5-EXPANSION-JOIN. I also read the REL-T1-G1B and D6 text in PLAN.
- **Hashes:** recomputed SHA-256 at the parent for every cited file. All matched what the drafts state:
  - G.1b note and spec, and `G1B_X_RESULT_20261127.md`
  - all four `SEAL_RECEIPT_*.json`, plus `summary.json` and `ASSEMBLY.json`
  - `c3_p3_split_v2.json` and the round-2 result review
  - the four kit records and both CPU-set determinism records
- **Other hashes:** every other 64- or 40-hex value in the drafts appears in the G.1b spec or on main. The sealed runs SHA `c23dec91…` matches `ASSEMBLY.json` and the result report.
- **Seal receipts:** node, `run_id` `g1b-x-tasl-20261126-a`, attempt 1, `stop: null`. Titanic's receipt names `mlgym_titanic`.
- **Result report:** 460/460 runs and 0 divergent rows for each node, determinism PASS, CPU sets as cited.
- **Per-node values against the G.1b spec `nodes[]`:** spec path, `node_spec_sha256`, `committed_pin_sha256`, `data_manifest_sha256`, environment and freeze hash/tool, CPU set, `cpu_only` mode (`census_override`, or `harness_list` for Titanic), harness kit pin, kit record, replacement-set determinism records, and run budget = 3 × slowest census. I recomputed 34.518, 767.169, 163.878 and 467.895 s. Leases match the G.1b note's `host_TASL2` line.
- **Split and routing:** v2 contains all four nodes at 4 train / 2 dev / 6 test each. Membership routes `mlgym_*` to suite MLGym as `arms_and_gate_after_g5_addendum`, and `gc7rc_*` to `g5_addendum_extra_task` with suite none and supply `never`. That matches each draft's `supply:` line and R1-G5-S9 (2). I looked only at counts and membership, not instance lists or labels.

## Constraints

No files were changed, nothing was launched, and I used no SSH, credentials or third parties. I read only published G.1b summaries, receipts and split seed assignments; no sealed label, test or evaluation data was opened. One tooling issue, not a blocker: zsh reads `$P:s…` as a modifier, so I re-ran those reads with `${P}:path` quoting. An rvm `ps` warning printed on every command and did not affect results.
