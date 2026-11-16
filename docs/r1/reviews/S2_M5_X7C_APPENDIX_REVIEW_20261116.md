Reviewed base: 5a2e4440a4b5b5ae4f5b188e0aa6c25ccf8f9b39

# S2-M5 X.7(c) appendix — independent review record (16 November 2026)

Branch `mac-s2-m5-x7c-20261116` from `author-sweephost-20261116` @ `fd275c53`. Unit:
- declaration `proposals/X7C_APPENDIX_DECLARATION_20261116.md` (`4af42d8a`, before any computation);
- `r1/scripts/x7c_appendix.py` (`655a8a4b`, sha256 `19106320…`);
- `reports/X7C_APPENDIX_20261116.md` and `reports/x7c_appendix_20261116/x7c_output.{json,md}`.

R1-EXAM-X7 (c). One freshly spawned independent reviewer agent (AI-assisted, Claude), three rounds. The reviewer's rerun reproduced the committed outputs byte for byte, and its independent reimplementation matched every value.
- Round 1 (`a8073156`): REVISE. 1 MAJOR: Q1 is an upper bound on the A2-skippable share, not the share itself, because it also includes first trials and invalid trials. 4 MINOR.
- Round 2 (`85cc1fcb`): ACCEPT, with 4 MINOR wording points.
- Round 3 (`5a2e4440`, those points fixed): ACCEPT. One optional nit is left as is: "comparable measure" could read "closer measure".

The declared rule's outcome is unchanged: **differences, not null**. The declaration is unchanged, and the report carries an erratum on Q1's wording.

Accepted commit (round 3, last): 5a2e4440a4b5b5ae4f5b188e0aa6c25ccf8f9b39

The round texts are reproduced unchanged below.

---

# Review R1 — S2-M5, X.7(c) appendix "C3 premises vs proposer strength"

Independent reviewer (Claude). Reviewed base: `mac-s2-m5-x7c-20261116` @ `a8073156585cb2e751f33593261dd0a16578020a`
(declaration `4af42d8a`, script `655a8a4b`, outputs and report `a8073156`; parent `fd275c53`).
Read-only on the worktree and repo; scratch only in `/tmp/pb/rev_s2m5/`.

VERDICT: REVISE

The computation is correct and reproduces bit for bit. The declared rule was applied exactly, and the decision
("differences", not null) holds. One MAJOR problem remains: the report reads Q1 as a share it does not measure, and
it builds its main interpretive claims on that reading. The fix is wording plus one disclosed post-hoc table. No
rerun of the declared analysis is needed.

## Findings

### 1. MAJOR — Q1 is not "the share the A2 rules skip". It also counts first trials and invalid trials, and the invalid-trial accounting differs between random_valid and the LLM rows

**Where.** Declaration §3, Q1, third bullet ("These are the proposals the A2 rule layer skips …"). Report §2, item 1,
bullets 1, 3 and 4 ("17.5 % of thinking-off trials repeat an evaluated configuration or the incumbent"; the
C3_DESIGN §2.3 comparison; "the duplicate / no-op rules will skip far fewer runs than in sweep 1"). Report §4,
"Q1 depends on budget use".

**Evidence.**
- `audited` is a subset of `props` from `r1/c3/features.py::replay_campaign`. `props` already leaves out two kinds of
  trial:
  - every row with `decision == "skipped"` or no parsed metric (`checks["skipped_invalid"]`);
  - the first trial of each root, because `featurize_view` returns `None` when there is no incumbent metric yet.
- So, per root, trials − audited = 1 first trial + invalid/skipped trials + replayed no-ops/duplicates. Only the last
  term is what C3_DESIGN §5 A2 skips ("π = 1 on hash duplicates and inactive keys").
- The first-trial term shows directly in B2: root `digits_mlp__s9012` has 20 trials, 0 invalid, 0 duplicates and
  19 audited.

Decomposition from the committed manifests (`diagnostics`; the off-only rows are exact):

| row | trials (off) | Q1 | first-trial part | invalid part | replayed noop/dup part | noop/dup share of valid proposals |
|---|---|---|---|---|---|---|
| random_valid | 356 | 0.579 | 0.034 | 0.326 (116) | 0.219 (78) | 0.342 |
| qwen25_coder_7b | 242 | 0.545 | 0.050 | 0.145 (35) | 0.351 (85) | 0.436 |
| scripted | 242 | 0.149 | 0.050 | 0 | 0.099 (24) | 0.104 |
| gemma4_31b B1 | 240 | 0.175 | 0.050 | 0–0.125 (0–30)* | 0–0.125 | 0–0.132* |
| gemma4_31b B2 (per root) | 240 | 0.188 | 0.050 | 0.083 (20) | 0.054 (13) | 0.063 |

*gemma4_31b's B1 `diagnostics` (45 invalid) pool its on and off roots, and there are no per-root B1 diagnostics in
the evidence directory, so only bounds are possible.

- **Composition of the invalid trials.** In the harness, `failed_invalid` covers several kinds:
  - `no_op_patch` and `effective_config_unchanged` (`control_plane/campaign.py` ~L2335): these are A2-skippable in
    spirit (an incumbent repeat, or an inactive key under D25);
  - worker, metric or scope failures: these are not.

  The committed data do not show which kind each invalid trial is. `invalid == noops` holds in every row; that fits
  the no-op kind but does not prove it. B2 `invalid_trials.json` shows no model-output-check rejections.
- **Accounting asymmetry.** random_valid's invalid trials do not use a worker run (356 − 116 = 240 = 12 × 20), so
  its roots run on and its Q1 numerator and denominator both grow. LLM roots stop at 20 trials, and there the invalid
  trials do use worker runs (each B2 root: `worker_runs` = `trials` = 20 with 2–4 invalid). The anchor and the
  finalist therefore reach their Q1 by different mechanisms.
- **Consequences for the report's reading.**
  - "17.5 % … repeat an evaluated configuration or the incumbent" is false as stated. About 5 pp are first trials,
    which cannot be repeats. Between 0 and 12.5 pp are invalid trials of unknown kind. The replayed repeat share is
    at most about 12.5 % (B2: 5.4 %).
  - The C3_DESIGN §2.3 comparison does not compare like with like. §2 item 3 quotes a *repeat* share, "39–77 % of LLM
    trials repeat an evaluated configuration". qwen2.5-coder's B1 Q1 (0.545) falls inside that range, but its
    replayed repeat share is 0.351, which is below it. That is itself a C3-premise finding worth stating. (Also,
    "§2.3" is §2 item 3, and that text does not name the model; §4 does.)
- **Is the decision robust? Yes.**
  - With the first trial removed from both numerator and denominator (my paired bootstrap, same seed and B), the
    finalist minus each anchor is:
    - random_valid: −0.432 [−0.492, −0.366];
    - scripted: +0.027 [−0.026, 0.084];
    - qwen25: −0.390 [−0.452, −0.338].

    The verdicts are the same.
  - On valid proposals only, the point values are random_valid 0.342 and qwen25 0.436, against at most 0.132 for the
    finalist (0.063 in B2). The direction holds, and the gaps are at least 0.21.

**Fix.**
- Keep the declared Q1 and the decision; both are pre-registered and correctly computed. Do not edit the
  declaration. Add an erratum paragraph to the report instead.
- Restate Q1 as "1 − audited share of trials". It is an upper bound on the A2-skippable share, because it includes
  each root's first trial and every invalid trial.
- Add the decomposition table above, labelled post hoc and descriptive, with bounds for gemma4_31b B1 and per-root
  values for B2.
- Rewrite report §2.1 bullets 1, 3 and 4 to match. The supported claim is that the finalist proposes far fewer
  replayed repeats and fewer invalid trials than qwen2.5-coder and random_valid. The size of A2's saving in sweep 2
  depends on how many invalid trials are no-op patches, and these data do not show that.
- In §4, explain the worker-run asymmetry: invalid trials are free for random_valid and cost a run for the LLM rows.

### 2. MINOR — The opening sentence understates the result

Report lines 5–6 say "the finalist and two anchors differ on two C3 premises". In fact the finalist differs from all
three anchors beyond the 95 % CI:
- from random_valid and qwen25 on Q1 and Q2;
- from scripted on Q2: +0.0055 [0.0013, 0.0089].

Fix: say so.

### 3. MINOR — The Q2 node caveat covers qwen2.5-coder only

Per-node sds, from the output:

| row | digits_mlp | credit | ionosphere |
|---|---|---|---|
| pick | 0.0050 | 0.0052 | 0.0209 |
| scripted | 0.0068 | 0.0048 | 0.0094 |
| random_valid | 0.0444 | 0.0175 | 0.0243 |

- Against scripted, the "beyond CI" difference comes from ionosphere, and on digits the pick is the *less* dispersed.
- Against random_valid, the pick is lower on all three nodes, so that difference is consistent across nodes.

Fix: add both sentences to report §2.2.

### 4. MINOR — Q3 for ministral3_14b rests on 38 % forecast coverage

ministral3_14b's Q3 uses 47 of 125 audited proposals (`forecast_query_failed` = 173 over its roots). It enters the
Q3 Spearman ρ, and the report text does not mention it; only the table's coverage column (0.38) shows it.

Fix: one sentence in §2.3 or §4. Optionally, also give ρ without that row.

### 5. MINOR — Pre-registration covers the interval rule, not blindness to point values; say so plainly

- Git proves the order of the commits: declaration 02:11:59, script 02:13:10, outputs 02:14:21. The claim that the
  declaration was committed "before the script existed" cannot be checked, and the 71 s gaps are tight.
- The pre-seen B1 analysis values equal the Q2 and Q3 point values exactly: `increment_sd` = Q2 and `a4_brier` = Q3
  for all 18 rows, which I checked. The pre-seen `diagnostics` counts give Q1 approximately.
- The declaration discloses all of this honestly.

Fix: add one sentence to the report saying that the point values were known in advance and that the declaration
fixed the comparisons, the interval method and the null rule.

## What I verified

- **Reproducibility.** I reran the given command into `/tmp/pb/rev_s2m5/out.json` and `out.md` (12 s). Both are
  byte-identical to the committed `x7c_output.json` (`f35a5a87…`) and `x7c_output.md` (`4dc35e13…`). The script's
  sha256 is `19106320…`, matching the report. `git status` in the worktree was clean.
- **Inputs.**
  - `b1_manifests.json` (`dc5cd04d…`), `completion_usage.txt` (`b5107bcb…`) and `complete_batch_verifier.json`
    (`07cb62de…`) equal the blobs on `gh/mac-b1-20261107` and its `SHA256SUMS`.
  - `b2_manifests.json` (`1c8d0e57…`) and all 12 B2 root manifests equal the blobs on `gh/ops-b2-exec-20261115`
    handback.
- **Independent reimplementation.** I wrote a vectorised per-cluster-sums version with the same RNG draw sequence. It
  reproduces:
  - every row's Q1, Q2, Q3, log score and μ̂ (differences ≤ 1e-17);
  - all seven 95 % intervals, to 6 dp;
  - Spearman ρ, identical to `scipy.stats.spearmanr` (Q1 −0.428, Q2 −0.443, Q3 0.091). There are no exact ties, so
    the script's tie handling does not matter.
- **Bootstrap.**
  - One draw of 12 instance ids per resample is shared by every row, so the pairing is correct.
  - Q1 is a ratio of sums recomputed per resample; Q2 and Q3 are recomputed from the pooled resampled proposals.
  - `default_rng(20261116)`, B = 10,000, linear percentiles; the Bonferroni level is 1 − 0.05/7.
  - The NaN count is 0 for every comparison. Q3 of random_valid and scripted is NaN everywhere and is correctly left
    out.
- **Declared rule.** There are exactly 7 comparisons (Q1 × 3, Q2 × 3, Q3 × qwen25), with the rule "the 95 % CI
  excludes 0". The decision is "differences", with 5 of 7 beyond the CI and 3 of 7 under Bonferroni, as reported. The
  null wording was correctly not used. The STOP checks match the declaration: 12 off roots per row, shared ids, usage
  totals equal to manifest trials, μ̂ equal to the analysis within 1e-12.
- **Thinking-off filter.** Proposals are filtered with `mode == "off"`, and Q1 denominators use only the off roots
  from the usage table. Per-root usage trials are the right denominators: their totals equal `diagnostics.trials`,
  and in B2 each root manifest's `diagnostics.trials` equals 20.
- **Forecasts.** Only non-null `p_delta_positive` is used, with a [0, 1] check, and coverage is reported.
- **Report against output.** Every number in the report's §1 table, the B2 replication values and the per-node sd
  statements for qwen25 and random_valid match the output. The μ̂ disclosure (pick below scripted, intervals
  overlapping) is correct. Nothing in the report claims proposer strength.

---

# Review R2 — S2-M5, X.7(c) appendix (round 2)

Independent reviewer (Claude). Reviewed base: `85cc1fcb18a3ef9170d972cf3c04c611bc3c9ff5`, one commit on `a8073156`.
`git diff --stat a8073156 HEAD` shows only `docs/r1/reports/X7C_APPENDIX_20261116.md` changed (+53/−15). The
declaration, script and outputs are byte-unchanged, so the round-1 reproduction stands: the committed outputs are
byte-identical to my rerun in `/tmp/pb/rev_s2m5/out.{json,md}`. The worktree is clean. Read-only throughout.

VERDICT: ACCEPT

The round-1 MAJOR finding is resolved, and so are the four round-1 MINOR findings. Four new MINOR wording points
remain (below). None affects the decision or the report's supported claim.

## Round-1 findings

- **F1 (MAJOR): resolved.**
  - §2.1 now calls Q1 an upper bound on the A2-skippable share. It names its three parts: first trials,
    `skipped_invalid`, and replayed repeats.
  - It adds the decomposition table, labelled post hoc and attributed. Its numbers match my decomposition.
  - It gives the first-trial-removed verdicts, which match my run: −0.432 [−0.492, −0.366], +0.027 [−0.026, 0.084],
    −0.390 [−0.452, −0.338].
  - It explains the worker-run asymmetry for random_valid (356 − 116 = 240 = 12 × 20).
  - It sets qwen's 0.351 against the C3_DESIGN range.
  - It adds an erratum to the header and leaves the declaration untouched.
- **F2: resolved.** The opening line names all three anchors and Q2 against scripted, which is correct.
- **F3: resolved.** The scripted per-node values (0.0068 / 0.0048 / 0.0094) and the ionosphere 0.021 vs 0.0094 match
  the output. The pick is lower than random_valid on all three nodes, which is correct.
- **F4: resolved.** It now says ministral3_14b's Q3 uses 47 of 125 proposals (coverage 0.38) and that the row is in
  the Q3 Spearman. Both match the output.
- **F5: resolved.** The new "What the pre-registration protects" bullet is accurate.

## New findings (all MINOR)

### R2-1. MINOR — "The invalid trials are probably no-ops" says more than the evidence shows

**Where.** §2.1, third bullet (report lines 57–59).

**Evidence.** The harness `edit_novelty` flag (`active_config_equals_incumbent`) is computed from
`_effective_config_at(worker, node_spec)` after `decision_made`. I read this in the harness copy at `561f71f`
(`control_plane/campaign.py` ~L1799–1830). That copy may not be the B1 pin `a3fedbb`. If a failed trial's edit has
already been reverted at that point, every invalid trial is automatically counted as a no-op. Then
invalid == no-op count is a tautology, not evidence about what kind of edit it was.

The report's conclusion does not need this argument:
- the pick's Q1 upper bound is 0.175;
- qwen2.5-coder's *lower* bound on the A2-skippable share (replayed repeats only) is 0.351, and random_valid's is
  0.219.

So "A2 has much less to skip in sweep 2" holds whatever kind the invalid trials are.

**Fix.** Change "probably" to "may be". Add that the equality may be automatic if failed edits are reverted before
the novelty flag is recorded. Rest the sweep-2 sentence (lines 80–82) on the bound comparison above.

### R2-2. MINOR — "For the LLM rows each trial costs a run" generalises from B2

**Where.** §2.1, fourth bullet; §4, Q1 bullet.

**Evidence.** The supporting fact is from the 12 B2 gemma4_31b roots only. In B1, several LLM roots ran more than 20
off trials, so some of their trials did not cost a run:

| row | longest roots (off trials) |
|---|---|
| qwen3_coder_30b_a3b | 34, 44 |
| olmo31_32b | 37 |
| ornith10_9b | 28, 22 |
| glm47_flash | up to 22 |

**Fix.** Say "for the LLM rows almost every trial costs a run: 20 trials per root, with a few longer roots". Cite B2
as the per-root check.

### R2-3. MINOR — Two sentences in §2.1 say more than the data, or reason loosely

- Lines 80–81: "… than under `qwen2.5-coder:7b` … or `random_valid`, in both B1 and B2." B2 has no anchor rows. The
  comparison is B1 only, and B2 only replicates the pick's own value. Fix: "in B1; the pick's B2 value replicates".
- Lines 83–85: "qwen2.5-coder's replayed-repeat share here (0.351) is below that range, so the two are not directly
  comparable." The two are not comparable because they are different measures. That qwen's share is below the range
  is the like-for-like finding. Fix: "The §2.3 figure is a repeat share on pilot data. The like-for-like B1 value for
  qwen2.5-coder, 0.351, is below that range." (Also, "§2.3" is §2 item 3 of C3_DESIGN.)

### R2-4. MINOR — The decision table still labels Q1 "rule-skippable share"

**Where.** §1 table, line 36. Fix: "Q1 skip share (upper bound)", to match the erratum.

## What I verified this round

- The diff is confined to the report, so the declaration, script and outputs are unchanged since round 1, where they
  reproduced bit for bit.
- Every new number in the report matches `x7c_output.json` or my round-1 computations:
  - the breakdown table;
  - the first-trial-removed intervals;
  - the per-node sds;
  - ministral's 47/125;
  - 356 − 116 = 240.
- The decision text, the Bonferroni statement and the opening sentence agree with the output.
- The report claims nothing about proposer strength.

---

# Review R3 — S2-M5, X.7(c) appendix (round 3)

Independent reviewer (Claude). Reviewed base: `5a2e4440a4b5b5ae4f5b188e0aa6c25ccf8f9b39`, one commit on `85cc1fcb`.
`git diff 85cc1fcb 5a2e4440` changes only `docs/r1/reports/X7C_APPENDIX_20261116.md` (+14/−11). The declaration,
script and outputs are unchanged since round 1, so the bit-for-bit reproduction still holds. The worktree is clean.
Read-only throughout.

VERDICT: ACCEPT

## Round-2 findings

- **R2-1: resolved.**
  - The text now reads "may be no-ops".
  - It gives the reason the equality may be automatic: the no-op flag is taken from the effective configuration
    after the decision, by which time a failed edit is reverted.
  - The sweep-2 sentence now rests on the bound comparison: the pick's upper bound 0.175 against the
    replayed-repeat lower bounds 0.351 (qwen2.5-coder) and 0.219 (random_valid). These match the breakdown table.
- **R2-2: resolved.**
  - The text now reads "almost every trial", with B2 as the per-root check.
  - The B1 roots above 20 off trials match the usage table: qwen3_coder_30b_a3b 34 and 44, olmo31_32b 37,
    ornith10_9b 28, glm47_flash up to 22.
- **R2-3: resolved.**
  - The comparison is now "In B1 …", and B2 is described as repeating the pick's value (0.188, matching the output).
  - The comparability logic is fixed: §2.3 is called a different measure from Q1, and qwen's 0.351 is given as the
    like-for-like value, below the range.
- **R2-4: resolved.** The §1 table now reads "Q1 rule-skippable share (upper bound)".

## New findings

None that need a change.

One optional nit: in "On the comparable measure", "closer measure" would be more exact. The pilot's repeat
definition in C3_DESIGN §2 item 3 is not shown to be identical to the replayed-repeat share.

## Verified

- The diff is confined to the report.
- Every changed number agrees with `x7c_output.json` and with my round-1 decomposition and usage-table counts.
- No BLOCKING or MAJOR findings remain.
