# G.4b re-pilot under R1-G5-DIFF-RECOUNT: pin rule, spec, re-issued note and launch commit (24 Nov 2026)

Prepared by the Mac-desk agent (Claude), AI-assisted, on `mac-g4b-repilot-20261124` over published `main` `3024db3f`.
ENGINEERING_ONLY. Desk work only: no host was used, nothing was pushed, and no label, evaluation value, sealed file,
`*block.jsonl` or `b1_manifests.json` was opened. The harness git dir `/tmp/pb/harness` was read with `git show`,
`ls-tree` and `diff` only.

**Authority.** PLAN row R1-G5-DIFF-RECOUNT (24 Nov 2026): "A short G.4b re-pilot on the same three nodes (W = 20, new
run id) measures diff liveness and recomputes the R1-BX-D14 dates; the coordinating chat publishes its spec and
re-issued note once they are independently reviewed and their launch checks pass, without a further author decision.
The G.4 pilot's strict-application liveness is disclosed." R1-G4-DECISIONS (G4-LB A, G4-ORDER B, G4-NODE3 A) stands
unchanged for G.4b.

**Where the harness commit lives.** The harness commit is one field: `harness_commit` in
`docs/r1/reports/tasl_chain_20261122/g4b_build_config.json`. The builder copies it into two places in the launch
commit, the spec's `harness.commit` and the note's `harness_commit`. It also writes it into the generated launch table
(`G4B_LAUNCH_TABLE.md`, `g4b_launch_table.json`).

This report does not repeat the sha. Every value that depends on it is read from the launch table: the harness
commit, the spec sha256 and the launch commit. The field holds the recount unit's final reviewed G5-7 tip (READY 105);
the config's `harness_commit_status` says so.

## 1. Commits on the branch

| commit | what | built by |
|---|---|---|
| `1e8c70dd` | the G.4b pin rule in `g4_tasl.py`; `g5_tasl.py dates --pilot-spec`; tests; the **template** spec `sweep2/t1_tasl/g4b_tasl_spec.json` and the **template** note draft (binding values PENDING) | by hand |
| `76043a05` | the template note draft cites the G.4 pilot report at its `main` path (sha256 unchanged) | by hand |
| `90d4dcee` (base, the spec's `paper.commit`) | review m5 (`pinned_checkouts` also covers the two G.5 families' checkouts) and m6 (the note's `measures` line names the inert `runner_factory`) | by hand |
| launch commit (sha: launch table) | the spec with `harness.commit` (from the config) and `paper.commit` (= base) filled; the note draft with `paper_commit`, `spec_sha256` and `harness_commit` filled; nothing else | `build_g4b_launch.py` |
| tail | this report, the builder and its config, `r1/tests/test_t1_tasl_g4b.py` | `build_g4b_launch.py` (from `wip-g4b-tail`) |
| table | `G4B_LAUNCH_TABLE.md`, `g4b_launch_table.json` | `build_g4b_launch.py` |
| full-suite lists | `FULLSUITE_G4B_BASE_3024db3f.txt`, `FULLSUITE_G4B_TIP.txt` beside this report | by hand, after the build |

## 2. The pin rule (`sweep2/t1_tasl/g4_tasl.py`)

**The blocker.** Before this unit, two checks stood in the way:
- `validate_spec` STOPped unless `harness.commit` equalled the G.1b pin `c025f89a`;
- `launch` compared TASL-2's host-check record (`host_check_harness_commit: c025f89a…`) with `harness.commit`.

G.4b must run on the recount commit, which is a successor of the pin, so both had to change.

**Scope of the rule (review m1).** `campaign_v2_diff.py` is excluded from the measurement path and checked only for
the recount needle, and a new module it imported outside `trackg/` would be neither restricted by `NO_ADDITIONS` nor
seen by `noise_floor`'s closure. So the rule does not by itself limit what that file can change. "G.4b measures the
recount and nothing else" holds for the pinned, reviewed commit `cbf7a003` (READY 105: only the recount pre-pass and
the inert `runner_factory` of the G.5 engines differ on G.4's call path), not as a property of the rule; `harness.commit`
is pinned exactly and checked at launch.

**Which spec is G.4b.** A spec is G.4b if its `harness` block carries `g1b_pin` or `pin_rule`. Any other spec is a G.4
spec, and its behaviour is unchanged (the module now imports `g5_pin_check` at load and `check_import_sources` checks more
modules, so the code path is not byte for byte; review m6):
- the same condition and message in `validate_spec`;
- the host record compared with `harness.commit`;
- `PLAN_ROWS`;
- no new record key.

The shipped `g4_tasl_spec.json` is unchanged and validates as before (tested). The original G.4 behaviour stays
available. G.4's sealed attempts still read through `seal`, `read_sealed_summary` and `dates` against
`g4_tasl_spec.json`.

**At the desk (`validate_spec`, no git).** For a G.4b spec, `validate_spec` requires:
- `harness.pin_rule` = `R1-G5-DIFF-RECOUNT`;
- `harness.g1b_pin` = the G.1b spec's harness commit (`c025f89a`);
- `harness.commit` a full commit (a placeholder is allowed only before launch), and not the pin;
- `envs` equal to the G.1b spec's;
- `run_id` matching `g4b-tasl-<YYYYMMDD>-<letter>`, so it can never be G.4's `g4-tasl-20261121-a`;
- `worker.harness_dir` not one of the G.1b, autoresearch-G.1b or G.4 checkouts, which stay at their pins.

Every other G.4 check runs unchanged: nodes equal to the G.1b spec's, W = 20, seeds, model, server, cap.

**At launch (`harness_rule_check`, on the worker's harness repository, before the TASL binding).** The rule follows
how G.5 checks each family against its G.1b pin, and it reuses the reviewed code instead of copying it. It has three
parts.

1. **`g5_tasl.measurement_path_check(repo, g1b_pin, commit)`** (P5 of G.5). It requires all of the following:
   - the commit descends from the pin;
   - no measurement-path file present at the pin differs. The measurement path is all of trackg except the four
     engine files, plus `nodes/`, `third_party/`, `configs/trackg/` and `noise_floor`'s import closure;
   - the only files added in trackg are `audit_g5.py` and `diagnostics_g5.py`;
   - the import closure is the same at both commits.

   Why: the runner, the isolation code and `diff_support` measured the G.1b noise floor and ran G.4's workers, and
   G.4b's result is compared with G.4's.
2. **`pilot_g4.py`, `manager_v2_diff.py` and `proposal_v2_diff.py` keep the pin's tree entries** (mode, type and
   object). This check is new and specific to G.4b. It means the pilot driver, the prompt and the proposal parser are
   G.4's, so `campaign_v2_diff.py` is the only engine file that may differ.

   On G.4's call path (`pilot_g4` calling `run_v2_diff_campaign` with the default `runner_factory`), that file
   differs only by the recount pre-pass. The `runner_factory` parameter that the G.5 engines added defaults to G.4's
   `WorkingCopyRunner`. So G.4b measures the recount and nothing else.
3. **`campaign_v2_diff.py` carries `DIFF_RECOUNT_RULE = "trackg_diff_recount/v1"`** at the commit, which shows the
   recount engine is present.

`g5_pin_check` (G5-7 against G5-AR) is not run: it compares the two G.5 families, and G.4b runs on one.

What happens around the rule:
- A failing rule is a STOP, before the binding and before the runner.
- `run_node_job` refuses a G.4b spec unless it has a rule result for its own commit and pin. The result is written
  into the job record as `harness_rule`.
- `launch` and `serve_launch` bind `R1-G5-DIFF-RECOUNT` as an extra PLAN row.
- `g5_tasl` is imported lazily, because it imports `g4_tasl`. The import-source check runs straight after that import.
  It now also covers `g5_pin_check`, `g5_tasl`, `g4_tasl`, `g1b_crosscheck` and `g1b_tasl_join`.

**The TASL-2 host check.** `host_check_commit(spec)` returns `harness.commit` for G.4 and `g1b_pin` for G.4b. G.5
already does this for G5-7: `g5_tasl.launch` calls `check_host_record(..., PIN_SEVEN)` on the same record,
`TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md` (sha256 `681011b2…`).

This is sound because of the measurement-path check:
- The record's items C1–C7 cover two kinds of evidence. Some are host conditions: namespaces, ptrace_scope, the
  delegated cgroup, the non-root uid, and the interpreters' `sys.path`. The rest are smokes run with the pin's own
  `isolation.RunCgroup`, `WorkingCopyRunner._sandbox_config`, and sandboxed CPU and GPU runs.
- Those files are in the measurement path (trackg and the closure), and check 1 keeps them byte-identical at the
  successor.

The record cannot cover a change in host state since 21 Nov. G.5 accepts the same limit. A record naming the
successor commit would be refused, but no such record exists. P1 of the note states the comparison.

**CLI.**
- `g4_tasl.py check-note <spec> --note <note> [--draft]`:
  - draft mode checks the unsigned draft, wherever it is, with exactly one `approved: false` line, and reads nothing
    from main;
  - strict mode requires the note on `origin/main`, P4's reviews on main, and TASL-2's record on main at
    `host_check_commit`, cited by P1.
- `g4_tasl.py harness-check <spec> [--repo R]` runs the rule for a G.4b spec and refuses a G.4 spec.

`check_note` gains a `draft=False` parameter, which `launch` and `serve_launch` never pass. For G.4b it also requires:
- `g1b_pin` equal to the spec's;
- P6 PASS, citing R1-G5-DIFF-RECOUNT;
- non-empty `g4_strict_liveness`, `measures` and `dates`.

**`g5_tasl.py dates --pilot-spec`.** `g5_tasl.py dates` read sealed pilot attempts only against `g4_tasl_spec.json`,
so it refused G.4b's attempts, which have another run id, spec and harness commit. The new option names the G.4b spec.
That spec must validate as a G.4b spec and must have G.4's nodes and G.4's pilot settings: W, memory mode and
temperature, which are what G.5's P3 reads. Without the option, the behaviour is unchanged.

**Desk checks on the configured commit.**
- `harness-check` passes on `/tmp/pb/harness`. 308 measurement-path files are unchanged. The `noise_floor` closure has
  15 files, none of them an engine file.
- The added files are `audit_g5.py` in trackg, plus `scripts/trackg_g4_reclassify.py`, three test files and three
  docs, all outside the measurement directories.
- The G5-AR tip is refused against `c025f89a`, because the measurement path differs in autoresearch's node files.
  G.4b therefore needs the G5-7 family. That matches G.4, which ran on `c025f89a`, the G5-7 pin.

## 3. The spec (`sweep2/t1_tasl/g4b_tasl_spec.json`)

- **Nodes.** `mlab_cifar10`, `mlgym_fmnist` and `mlgym_breakout_minatar`. Confirmed from two sources: the G.4 result
  `G4_TASL_PILOT_RESULT_20261122.md` (first committed on `ops-tasl-20261116`; read with `git show`: its per-node table and seals), and
  `g4_tasl_spec.json`. Node pins, environments and census records are identical to G.4's, and they are checked against
  the G.1b spec.
- **Pilot settings.** W = 20 in `pilot.budget`, as in G.4 (`validate_spec` requires it). 3 instances with seeds
  4001–4003, as in G.4. Temperature 0.2, `history`, `max_tokens` 4096, `cache_prompt: false`.
- **Run id** `g4b-tasl-20261124-a`. It follows the `<kind>-tasl-<date>-<letter>` convention of
  `g1b-tasl-20261121-b`, `g4-tasl-20261121-a` and `g1b-ar-tasl-20261122-a`.
- **Harness.** `commit` comes from the config (G5-7, branch `mac-trackg-g5-7-20261124`). `g1b_pin` is `c025f89a`, and
  `pin_rule` is `R1-G5-DIFF-RECOUNT`.
- **Checkout.** `worker.harness_dir` is `/home/dowling/r1_tracks/t1_tasl/harness_g4b`, a new checkout. G.4's
  `harness` is G.1b's checkout and stays at the pin. G.5's `harness_g5` stays free for G.5. No checkout moves under
  another table.
- **Unchanged from G.4.** Everything else, including:
  - `sealed_root` `sealed_g4` (G.4b writes under a new run-id directory);
  - the proposer block (its `run_dir` gets the new run id);
  - the cap of 20 GPU-h and the layout.

  The projection is therefore G.4's 11.077 GPU-h. G.4 measured 1.5717 GPU-h; the projection assumes every call runs.
- **Changed fields** (tested): exactly `comment`, `third_node_reason`, `paper.commit`, `run_id`,
  `harness.{commit,branch,g1b_pin,pin_rule}` and `worker.harness_dir`. G.4's `third_node_reason` ("autoresearch has
  no passed isolated U2") is stale. The new text says the three nodes are G.4's and that autoresearch belongs to the
  G5-AR family.
- **Checks.** The built spec passes `validate --launch`, which the builder runs. The template at the base passes
  `validate` without `--launch`, and with `--launch` it refuses on `paper.commit`.

## 4. The re-issued note (`docs/r1/proposals/G4B_T1_TASL_NOTE_DRAFT_20261124.md`, approved: false)

**Format.** The note uses the key-block format of `g4_tasl.check_note`. G.4 does not render its key lines from the
spec (G.5's `note_lines` has no G.4 counterpart), so the lines are written out by hand. A test checks each binding line
against the built spec, and `check-note --draft` checks the rest.

Compared with the signed G.4 note `g4_t1_tasl_20261123.md`, these lines change:
- the spec, `paper_commit`, `spec_sha256` and `run_id`;
- `harness_commit`, plus the new `g1b_pin`, `harness` and `harness_rule`;
- P1, which states the comparison with the pin;
- P2, which cites R1-G5-DIFF-RECOUNT;
- P3, which adds G.5 and AR G.1b jobs to the lease order;
- P4, the reviews;
- P6, new: the harness rule;
- `reissue`;
- `g4_strict_liveness`, `measures` and `dates`.

`census_erratum` is kept, for the `mlgym_fmnist` manifest.

**Disclosure** (`g4_strict_liveness`). The figures come from the G.4 result report
`docs/r1/reports/tasl_chain_20261122/G4_TASL_PILOT_RESULT_20261122.md` (sha256 `07c03920…`). The note cites it at that
`main` path: it reaches `main` through the experiment agent's result branch; it was first committed on
`ops-tasl-20261116` at `9eafa66d`. Its sha256 is unchanged.
- 155 of 180 proposals were refused before any run: 122 `malformed_hunk` and 33 `malformed_diff`.
- Per node: `mlab_cifar10` 59 refused (53 / 6), `mlgym_fmnist` 48 (45 / 3), `mlgym_breakout_minatar` 48 (24 / 24).
- 22 proposals ran, 3 were duplicates and 0 were invalid. `ran_of_valid` was 0.0167 / 0.1833 / 0.1667.
- G.4's dates recompute rests on that liveness: seven nodes, ran share 0.1667, B.7 2026-12-03. G.4b's recompute
  replaces it for the dates.

**What G.4b measures** (`measures`). G.4b measures diff liveness under `trackg_diff_recount/v1`, per node and in total:
- `ran_of_valid` and `ok_of_proposals`;
- refusals by reason;
- the kept, discarded, duplicate, inert and invalid counts;
- latency.

It uses the same nodes, seeds, W, prompt, model and server as G.4. Each ledger line carries `diff_recount`. The
figures are compared with G.4's and with the offline re-classification (§7). Liveness 0 on a node is a node STOP.

**The dates** (`dates`). After the three seals, on TASL-2 from the G.4b launch checkout:

```
# binding: the eight-node G.5 table of R1-G5-DECISIONS (one slot, autoresearch exempt from the ratio, G.5 cap)
python3 sweep2/t1_tasl/g5_tasl.py dates sweep2/t1_tasl/g5_tasl_spec.json \
  sealed_g4/g4b-tasl-20261124-a/mlab_cifar10/attempt-N sealed_g4/g4b-tasl-20261124-a/mlgym_fmnist/attempt-N \
  sealed_g4/g4b-tasl-20261124-a/mlgym_breakout_minatar/attempt-N \
  --pilot-spec sweep2/t1_tasl/g4b_tasl_spec.json --today <date>
# comparison with G.4's recompute (seven nodes, g4_tasl_dates_params.json)
python3 sweep2/t1_tasl/g4_tasl.py dates sweep2/t1_tasl/g4b_tasl_spec.json sweep2/t1_tasl/g4_tasl_dates_params.json \
  <the same three sealed attempts> --today <date>
```

The sealed paths are relative to `/home/dowling/r1_tracks/t1_tasl`. As R1-BX-D14 (iii) requires, changed dates go to
the author before they are applied.

**Filled at publication.** Only three things: `approved: true`, the title line, and the file name
`g4_t1_tasl_<YYYYMMDD>.md`. The date must be one no G.4 note uses, so not 20261122 or 20261123.

P4 pre-names two review files, which must be on `main` before the strict check:
- `docs/r1/reviews/G5_DIFF_RECOUNT_REVIEW_20261124.md`, a paper-side record of the recount unit's review;
- `docs/r1/reviews/G4B_REPILOT_PREP_REVIEW_20261124.md`, this unit's review.

If the reviews are filed under other names, P4's paths are edited to match before signing. That changes a citation,
not a value.

**Checks before the coordinating chat publishes.** R1-G5-DIFF-RECOUNT says the spec and note are published "once
they are independently reviewed and their launch checks pass". The checks are:

| # | check | where | must give |
|---|---|---|---|
| 1 | `build_g4b_launch.py build g4b_build_config.json --worktree W` with the final tip. It runs `validate --launch`, `harness-check` on the harness repository and `check-note --draft`, all with the base's code. It refuses a launch commit that changes anything outside `docs/` other than the spec. **Do not re-run it after the review** unless the rebuilt `launch_commit` equals the reviewed one (the launch table's): the sha reproduces only under the same signing setup (SSH, `commit.gpgsign=true`); an unsigned rebuild gives a different sha with an identical tree (review m4) | desk | rc 0 |
| 2 | `python3 sweep2/t1_tasl/g4_tasl.py validate sweep2/t1_tasl/g4b_tasl_spec.json --launch` | desk, the launch commit | rc 0, projection 11.077 |
| 3 | `python3 sweep2/t1_tasl/g4_tasl.py harness-check sweep2/t1_tasl/g4b_tasl_spec.json --repo <harness git dir holding the final tip>` | desk | rc 0 |
| 4 | `python3 sweep2/t1_tasl/g4_tasl.py check-note sweep2/t1_tasl/g4b_tasl_spec.json --note docs/r1/proposals/G4B_T1_TASL_NOTE_DRAFT_20261124.md --draft` | desk | rc 0 |
| 5 | `pytest r1/tests/test_t1_tasl_g4b.py` with `AR_HARNESS_ROOT` set to a harness repository holding the tip (5 passed, none skipped), and `test_t1_tasl_g4.py` | desk, branch tip | all pass |
| 5a | `git show origin/main:docs/r1/reports/tasl_chain_20261122/G4_TASL_PILOT_RESULT_20261122.md \| sha256sum` equals `07c03920e266375919fd95ebbd2805a8c15d3157a1ed9e9c80b565fa8747dbe8`: the G.4 result report the note cites is on `main` (it arrives through the experiment agent's result branch; no other check reads that citation; review m2) | before signing | equal |
| 5b | the paper copy of the recount review `docs/r1/reviews/G5_DIFF_RECOUNT_REVIEW_20261124.md` (P4) is byte-identical to the harness record `cbf7a003:docs/r1/reviews/G5_DIFF_RECOUNT_REVIEW_20261124.md`, sha256 `6dd4ffda613459f014c0c172d57040f1b36008faf66a7b0c434986f80450c096` (strict `check-note` only checks that a file exists at that path; review m3) | before signing, and again at 7 | equal |
| 6 | merge the branch into `main` **without squash or rebase**, so the launch commit stays an ancestor of `main` with its sha; put the two review files of P4 on `main`; then publish the signed note | coordinating chat | — |
| 7 | `python3 sweep2/t1_tasl/g4_tasl.py check-note sweep2/t1_tasl/g4b_tasl_spec.json --note docs/r1/authorizations/g4_t1_tasl_<date>.md` in strict mode: the note byte-identical on `origin/main`, P4's reviews on main, and TASL-2's record on main at `g1b_pin`, cited by P1 | after a fresh fetch | rc 0 |
| 8 | `python3 sweep2/t1_tasl/g1b_tasl_join.py publication-check docs/r1/authorizations/g4_t1_tasl_<date>.md` without `--p4`: no `<FILL` field, and the `census_erratum` citation equal to the file on main | after a fresh fetch | rc 0 |

Checks 7 and 8 need the note on `main`. If either fails, the note is withdrawn before any launch, and nothing has run.
On the hosts, the code repeats every gate at launch (§6).

## 5. The launch commit, as in the TASL chain

**What a launch commit is in the chain.** Sources: READY 83/85, merges `38ae4a05` and `5d5ca7b4`, launch commits
`34a5b1d6`, `b5824240`, `6ad899e0` and `d52c9d9d`, and the files `TASL_CHAIN_20261122.md`, `LAUNCH_TABLE.md` and
`PUBLICATION_20261122.md`. From these:
- there is one commit per run, and it changes exactly one file outside `docs/`, that run's spec, plus the note draft
  in `docs/`;
- the spec's `paper.commit` is the commit's parent;
- the commit is built **at the desk** by a builder with pinned author and committer dates (`build_launch_chain.py`,
  `build_launch_chain_ar.py`). A tail and a generated launch table follow it;
- the coordinating chat publishes it by merge, never by squash or rebase, and then publishes the signed note on
  `main`;
- the hosts launch from the launch commit or from a docs-only descendant, with the note copied from `origin/main`.
  `verify_launch_tasl` requires the code to equal `paper.commit` outside `docs/` and the spec.

**So option (a) applies: the launch commit is on this branch.** It is made by `sweep2/t1_tasl/build_g4b_launch.py`,
which reuses the chain builder's helpers from `build_launch_chain.py` (`git`, `commit`, `fields_replace`, `sub1`,
pinned dates). It changes only the spec and the note draft. Its sha, the spec sha256, the paper commit and the harness
commit are in `G4B_LAUNCH_TABLE.md`.

The tests check:
- the parent and the changed files;
- that the tip carries the launch commit's spec and note byte for byte;
- that the base holds the template, which differs in exactly `harness.commit` and `paper.commit`;
- that `verify_launch_tasl` passes from the launch commit and from a docs-only child, against a local origin whose
  `main` contains them;
- that `verify_launch_tasl` refuses the branch tip ("differs from the paper commit outside docs/");
- that at the base, whose code is the paper commit, the signed note refuses the template spec on `spec_sha256`.

**The placeholder.** In the committed templates at the base, five values read `PENDING: …`: the harness commit,
`paper.commit`, and the note's three binding fields. The launch commit fills them from the one config field. No
hand-written file holds another copy of the harness sha.

## 6. TASL-2 and TASL-7 steps (for the cluster agent, after publication)

1. **Prerequisite (done by the recount unit, not this one).** `mac-trackg-g5-7-20261124` is pushed to the harness
   `origin`.
2. **TASL-2: a new harness checkout.** `harness` and `harness_g5` are not touched. `TIP` is read from the published
   spec (`harness.commit`):
   ```
   cd /home/dowling/r1_tracks/t1_tasl
   TIP=$(python3 -c "import json;print(json.load(open('paper_g4b/sweep2/t1_tasl/g4b_tasl_spec.json'))['harness']['commit'])")
   test -e harness_g4b && exit 2
   git clone --no-checkout https://github.com/dowlingwong/autoresearch_harness.git harness_g4b
   git -C harness_g4b fetch origin mac-trackg-g5-7-20261124
   git -C harness_g4b checkout --detach "$TIP"
   test "$(git -C harness_g4b rev-parse HEAD)" = "$TIP" && test -z "$(git -C harness_g4b status --porcelain)"
   ```
   The clone must contain `c025f89a`, which is an ancestor of the tip.
3. **Both hosts: a new paper checkout `paper_g4b`.** G.4's `paper_g4` at `6ad899e0` stays as it is. The new checkout is
   a fresh clone of the paper repository, fetched, and detached at the launch commit or a docs-only descendant. The
   signed note is copied from `origin/main` into its `docs/r1/authorizations/`.
4. **TASL-2: smoke checks.**
   - Items 1–3 of the harness report §10: the checkout is clean at the tip; `measurement_path_check` passes; and the
     following runs in torch312 and jax312 from `harness_g4b`:
     `PYTHONPATH=src python -B -m pytest -p no:cacheprovider -q tests/trackg/test_trackg_diff_recount.py
     tests/trackg/test_trackg_g4_reclassify.py`.
   - Then, from `paper_g4b`: `python3 sweep2/t1_tasl/g4_tasl.py harness-check sweep2/t1_tasl/g4b_tasl_spec.json`
     (the default repository is `worker.harness_dir`) and the strict `check-note`. Both must give rc 0.
5. **The offline G.4 re-classification** (§7), before or alongside the re-pilot. Its JSON is kept with the G.4b
   records.
6. **TASL-7: start the server.**
   ```
   G4_TASL_ENABLE_REAL=1 python3 sweep2/t1_tasl/g4_tasl.py serve sweep2/t1_tasl/g4b_tasl_spec.json \
     --note docs/r1/authorizations/g4_t1_tasl_<date>.md --enable
   ```
   Then copy `proposer/g4b-tasl-20261124-a/server-N/server_record.json` to `records/g4b-tasl-20261124-a/` on
   TASL-2.
7. **TASL-2: run each node**, in the order `mlab_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`:
   ```
   G4_TASL_ENABLE_REAL=1 bash sweep2/t1_tasl/t1_tasl_node.sh g4 sweep2/t1_tasl/g4b_tasl_spec.json <node> \
     docs/r1/authorizations/g4_t1_tasl_<date>.md \
     /home/dowling/r1_tracks/t1_tasl/records/g4b-tasl-20261124-a/server_record.json --enable
   ```
   `launch` runs the harness rule on `harness_g4b` before the binding, and each job record carries `harness_rule`.

   After the first node, apply item 5 of the harness report §10: each ledger proposal line has `diff_recount`, and
   where `changed` is true, `runs[0].diff.diff_sha256` equals `diff_recount.applied_diff_sha256`. That item reads
   only those diff fields.
8. **Stop and seal.** Stop the server with SIGTERM. Copy `server_end.json` and `llama-server.log` to TASL-2. Then seal
   each node:
   `python3 sweep2/t1_tasl/g4_tasl.py seal runs/g4b-tasl-20261124-a/<node>/attempt-N sweep2/t1_tasl/g4b_tasl_spec.json
   --node <node> --server-end … --server-log …`.
9. **Dates and result report.** Run the two commands of §4. Then write a result report like G.4's, with captures but
   no `out.tar`. It gives G.4b against G.4 per node, both refusal counts, and the re-classification JSON.

## 7. The offline re-classification of G.4's refusals (harness report §8)

This runs on TASL-2, before or alongside G.4b. What it does:
- It reads only two kinds of member from G.4's sealed `out.tar`: `out/pilot.json` and the `campaign_ledger.jsonl`
  files.
- It verifies them against the captures committed on `ops-tasl-20261116`.
- It re-runs only the parse/apply step, once with the strict rule and once with the recount.
- It writes one new JSON file.

The command below is the harness report's §8 command in its revised form. `SHA` is the code commit that the final
harness report names in its §8. The final G5-7 tip adds only the report on top of that commit, so the tip may be used
instead. The command uses its own checkout, `harness_g4rc`, as the harness report says. `harness_g4b` at the tip would
also work, but separate checkouts leave the re-pilot's checkout untouched.

```
cd /home/dowling/r1_tracks/t1_tasl
SHA=cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98   # the final G5-7 tip (READY 105); code commit f31050f5 is behaviour-identical
H=/home/dowling/r1_tracks/t1_tasl/harness_g4rc
test -e "$H" && exit 2
git clone --no-checkout https://github.com/dowlingwong/autoresearch_harness.git "$H"
git -C "$H" fetch origin mac-trackg-g5-7-20261124
git -C "$H" checkout --detach "$SHA"
test "$(git -C "$H" rev-parse HEAD)" = "$SHA" || exit 2
test -z "$(git -C "$H" status --porcelain)" || exit 2
git -C paper_g4 fetch origin ops-tasl-20261116
test -e /tmp/g4caps && exit 2
mkdir /tmp/g4caps && git -C paper_g4 archive origin/ops-tasl-20261116 \
  docs/r1/reports/tasl_chain_20261122/G4_TASL_PILOT_RESULT_20261122_captures | tar -x -C /tmp/g4caps
C=/tmp/g4caps/docs/r1/reports/tasl_chain_20261122/G4_TASL_PILOT_RESULT_20261122_captures
S=sealed_g4/g4-tasl-20261121-a
envs/torch312/bin/python -B "$H/scripts/trackg_g4_reclassify.py" --harness-root "$H" \
  --pair "$S/mlab_cifar10/attempt-1"           "$C/mlab_cifar10" \
  --pair "$S/mlgym_fmnist/attempt-1"           "$C/mlgym_fmnist" \
  --pair "$S/mlgym_breakout_minatar/attempt-1" "$C/mlgym_breakout_minatar" \
  --out records/g4-tasl-20261121-a/g4_reclassify_20261124.json
echo rc=$?
```

The harness report gives these expected smoke values:
- `refused_before`: 122 `malformed_hunk` and 33 `malformed_diff`;
- `g4_rule_replay`: 155 matching the ledger;
- 0 unverified incumbents;
- 25 accepted texts unchanged.

`new_rule` and `by_reason` are the measurement. They project the recount onto G.4's incumbents and do not replace
G.4b: once a recounted diff runs, G.4b's own campaigns diverge from G.4's.

## 8. What changes when the harness review settles the tip

**The one value.** `harness_commit` in `g4b_build_config.json`, together with its `harness_commit_status` text. To
apply a new tip:
1. Commit the edited config on `wip-g4b-tail`, the tail ref.
2. With a clean worktree, run
   `python sweep2/t1_tasl/build_g4b_launch.py build docs/r1/reports/tasl_chain_20261122/g4b_build_config.json --worktree <worktree>`.
   Run it from a copy of the builder outside the worktree, because it resets the branch to the base.

The builder rebuilds the launch commit, the tail and the table. It fails closed if the new tip breaks the harness
rule.

**What changes with it:**
- the spec's `harness.commit` and its sha256;
- the note's `harness_commit` and `spec_sha256`;
- the launch commit and the branch tip;
- the full-suite tip list, which is regenerated on the new tip.

**What does not change:** the base, `paper.commit`, the code, the tests, the projection, and every other note line.

The recount unit's review settled the tip at `cbf7a003` (READY 105); the launch commit was rebuilt on it, on base
`76043a05`. G5-AR's tip is irrelevant to G.4b, which uses G5-7 only.

**Outside this unit:**
- G.5's spec names its two family commits when its own unit does (harness report §9.1).
- G.5's `pilot_basis` and P3 read `g4_tasl_spec.json` (run `g4-tasl-20261121-a`). If G.5's P3 is to rest on G.4b, a
  reviewed G.5-side change must point them at the G.4b spec. G.4b runs the same settings, so P3's blockers do not
  change. For the R1-BX-D14 recompute, `dates --pilot-spec` already reads G.4b's attempts.

## 9. Tests and full suite

**Targeted tests.** Each file was run alone, with `TMPDIR=/tmp/g4bdev/t` and `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`.

| file | result |
|---|---|
| `test_t1_tasl_g4.py` | 47 passed: 30 existing and 17 new. The new tests cover the G.4b rule and its refusals; the G.4 rule kept; the harness rule on synthetic repositories (8 refusal cases, plus ancestry and an unknown commit); launch and serve for G.4b; the job record; draft and strict note checks; the CLI |
| `test_t1_tasl_g4b.py` (new) | 5 passed, none skipped, including the real harness rule on the configured commit |
| `test_t1_g5_tasl.py` | 116 passed, 1 of them new (`dates --pilot-spec`) |
| `test_t1_tasl_g1b.py` | 45 passed |
| `test_t1_tasl_chain.py`, `test_t1_g5_job.py`, `test_t1_g5_seal.py`, `test_t1_tasl_crosscheck.py`, `test_t1_tasl_g1b_ar.py`, `test_t1_tasl_g5_ar_projection.py` | 16, 37, 36, 30, 69 and 6 passed |

**Full suite.**
- Command: `/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider -rfE r1/tests`, with no lightgbm importable,
  `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, and no other `r1/tests` pytest running.
- Base: a clean detached clone of `3024db3f`, with `TMPDIR=/tmp/g4bdev/tb`.
- Tip: the branch tip, with a fresh `TMPDIR=/tmp/g4bdev/t`.
- The sorted `FAILED|ERROR` lines are beside this report, in `FULLSUITE_G4B_BASE_3024db3f.txt` and
  `FULLSUITE_G4B_TIP.txt`. They are identical: 61 lines (58 failed, 3 errors).
- Base: 58 failed, 3823 passed, 197 skipped, 3 errors. Tip: 58 failed, 3846 passed, 197 skipped, 3 errors. The 23
  extra passes are exactly the 23 new test ids (17 in `test_t1_tasl_g4.py`, 5 in `test_t1_tasl_g4b.py`, 1 in
  `test_t1_g5_tasl.py`); no test id was removed.
- The tip run was on the build whose launch commit is in the launch table, before this paragraph and the two list
  files were added (docs only).
- A first base run in a clone without `refs/remotes/origin/main` gave 60 failed. The two extra failures
  (`test_c3_arms_freeze.py::test_record_checker_accepts_a_complete_record_and_round_trips` and
  `test_c3_release.py::test_author_rows_find_what_the_analysis_guard_finds_on_the_real_plan`) read published-ancestor
  state. With the clone's `origin` set to the paper repository URL and `origin/main` set to `3024db3f`, as in the tip
  worktree, the base gave the list above.
- The list the task named, `docs/r1/reports/arms_t1feat_20261123/FULLSUITE_BASE_3024db3f.txt`, is not on `main`
  `3024db3f`, so the base was run here.

## 10. Open points for the reviewer

- **P1 and the CUDA IPC risk.** The author accepted the residual CUDA IPC risk for G.4 "with this line". The G.4b note
  says the same risk applies, because the nodes, frozen parents and isolation code are the same. It does not claim a
  new author acceptance; the coordinating chat publishes under R1-G5-DIFF-RECOUNT. Please confirm this reading.
- **The host check at the pin.** It relies on the host state being unchanged since 21 Nov, as G.5's check does. No
  re-check was made at the successor.
- **P4's pre-named review paths** (§4).
- **Refusal text.** When `measurement_path_check` refuses during a G.4b check, its message still says
  "G.5 <commit>". This is cosmetic.
- **Seeds.** G.4b reuses G.4's seeds 4001–4003. The inputs match, but the replies need not, because the server is not
  guaranteed to be deterministic. The comparison with G.4 is therefore not paired per proposal.
- **Projection layout.** G.4's layout, which assumes 60 s per call, is kept, although the measured median was
  12–15 s. The cap is unaffected.
