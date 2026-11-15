# Independent review: build runbook P2 (seed registry generated from code)

**AI-assisted (Claude, independent reviewer), 15–16 Nov 2026. ENGINEERING_ONLY.** Branch `paperc-build-20261115`, head `e783588`. Pins: canonical `d4ea56c1` (`author-qtorch-20261115`), Track S `fab88fce` (`trackS-ops-20261030`). I did not write this code. The only file I changed is this review.

## What I checked

- **Read:**
  - `paperC/src/paperc/seeds.py`, `paperC/tests/test_seeds.py`, `paperC/seeds/registry_v1.json`;
  - `paperC/docs/reports/SEED_REGISTRY_CHECK_20261115.md`, `paperC/docs/BUILD_STATUS.md`;
  - runbook P2;
  - plan §11.1 (line 392) and §4.1;
  - the seed check in P1's `paperC/src/paperc/schema.py`.
- **Commands:**
  - `PYTHONPATH=paperC/src paperC/.venv/bin/python -m pytest -q -p no:cacheprovider paperC/tests` gave **73 passed** (8 in `test_seeds.py`).
  - `python -m paperc.seeds`, then `git diff --stat`: empty, and the working tree stays clean. The registry is reproducible.
- **Registry contents:** 29 Paper B blocks (23 literal, 4 base_count, 1 formula, 1 prose_only), 3 Paper C blocks, no internal Paper B overlap. `scan_constants` finds 36 constants across the two pins.
- **Code read at the pins:**
  - Track S: `collect.py` (blocks, `audit_rule`, `instance_seed`, `--seed-base` guard, `seed_key_for`, D26 use), `oracle.py`, `probes/s1_factorial.py`, `simulate_controls.py`, `synthetic.py`, `worlds.py`;
  - `e1b_collect.py` (`_instance_seed`, CLI);
  - `e1_noise_floor.py` (`plan_runs`);
  - `exam/runtime.py`, `exam/b2_batch.py` and `exam/namespace.py` (B2 bounded to 1..89);
  - all configs under `r1/scripts/configs`.
- **Greps at both pins:**
  - literals passed as `seed=`, `train_seed=` and `split_seed=`;
  - `--seed*` CLI defaults;
  - `default_rng(...)` keys;
  - module-level `SEED`/`RNG`/`KEY` names;
  - `tools/`.
- **Other branches:**
  - Track G (`mac-trackg-20261104/09`): 8001–8010 appears only in prose (RUNBOOK G.1b, TRACK_G_RUNBOOK, HOREKA_RUNBOOK), never in code.
  - `codex/coordinator-20261031`, `main`, `htcondor-chain-20261114` and `ops-b1-restart-d-20261113`: no further seed code, and no `r1/tracks`.
  - `mac-tracks-s05-summary-both-20261115`: Track S files identical to the pin.
- **Empirical scan of the results files:**
  - Coverage: 1935 / 2314 JSON and 528 / 1215 JSONL files at `d4ea56c` / `fab88fc`, about 15k / 39k seed-keyed integers in the JSONL files.
  - No recorded value lies in a Paper C block.
  - Every recorded worker, instance and audit seed lies in a registered block. The values outside the blocks are counts, D26 LLM-call seeds, the T3/T5 RNG keys, and the Track S s01 probe seeds.
- **Paper C block gaps:**
  - Instances: 10,000 to Track S fixture (40000).
  - RNG keys: 20,000 to the same block.
  - Audits: 7,000,000 above the oracle blocks and 9,261,012 below the smallest date key (20261012).
  - Nothing in code or results collides with the proposed blocks.

## Findings

1. **MAJOR: the report and BUILD_STATUS propose a colliding audit block, and the report is stale.**
   - `SEED_REGISTRY_CHECK_20261115.md:41` and `BUILD_STATUS.md:9` give `paperc_audits` = 1,000,000–2,000,000. That is the `bbb40d1` value, and it overlaps `tracks_oracle_select` [1e6, 2e6). Line 44's claim "at least 1000 away from every Paper B block" is false for that value.
   - The code (`seeds.py:75`) and the registry use 10,000,000–11,000,000.
   - The report's Paper B table (lines 11–22) and its differences list (lines 24–33) also lack the blocks added in `2f0f804`. None of these is in plan §11.1, so each is a difference that runbook step 4 requires the report to list:
     - `tracks_oracle_select` / `_eval` 1e6–3e6;
     - `tracks_s11_factorial` 37001–37031;
     - `tracks_s11_boot_key` 20261029;
     - `rng_key_20261019`.
   - *Fix:*
     - regenerate both report tables from `registry_v1.json`;
     - correct the P2 row of BUILD_STATUS;
     - add a test that every registry block name appears in the report and that the report's Paper C ranges equal `PAPER_C_BLOCKS`.

2. **MAJOR: the completeness scan never matches a bare `SEED` / `SEEDS`.**
   - `SCAN_NAME` (`seeds.py:247`) requires at least one character before `SEED`; I checked that `SCAN_NAME.match("SEED")` is `None`.
   - Not scanned and not registered:
     - `r1/headroom/e1b_compare.py:46` `SEED = 20261012`;
     - `r1/scripts/b1_q2_reference.py:18` `SEED = 20261107` (canonical);
     - `r1/c3/train/exam_synthetic.py:67` `SEED = 20261026` (Track S pin).
   - `r1/c3/offline_eval.py:113` and `r1/diagnostics/di_test.py:31` (both 20261019) are covered only because the value happens to equal `PLAN_SEED`.
   - So `test_every_seed_constant_in_code_is_accounted_for` passes without checking them, and the docstring's guarantee (lines 25–28) is false.
   - Impact on Paper C: none, since all of these values are about 2.03e7.
   - *Fix:*
     - match names with `name.isupper()` and (`"SEED" in name` or `"_BASE" in name`);
     - add `IGNORED` entries for the string constants this newly matches (`c3/audit.py` `SEEDS_FILE`; `tracks/probes/determinism.py:44` `SEED_KEY`);
     - register the three keys as `rng_key_*` blocks;
     - add a test asserting that `SCAN_NAME` matches `SEED`.

3. **MAJOR: Paper B worker seeds that are not constants are missing, and nothing downstream catches them.**
   - **Node default seed 42.** The node default (`AR_TRAIN_SEED` / `AR_SPLIT_SEED` and openml `SPLIT_SEED`, all default 42; `docs/r1/STATUS.md:876` at `d4ea56c`) is a Paper B worker seed:
     - in every noise-floor `default` and `default_repeat` run;
     - as the fixed partner seed of every `train` and `split` run. `e1_noise_floor.py:200–202` passes `None`, which means the node default, and `NOISE_REMEASURE_20261022.md:14` records "split at 42" and "training at 42".
     - It lies in no block; the lowest block starts at 100.
   - **Other unregistered seeds:**
     - worker seed 999 in `r1/e2e.py:79`, in the gap 997–1000;
     - Track S's superseded audit layout 33001–34999 (`r1/tracks/IMPLEMENTATION_NOTES.md:94,139` and `oracle.py:256` at `fab88fc`). The shallow clone cannot show whether data were collected under it.
   - **Why nothing catches them.** P1's `check_campaign` (`schema.py:890–907`) only asks whether a value lies in a Paper B block, and it skips `None` (line 905). So a Paper C row with `worker_seed=None` (that is, the node default 42), or with 42, 999 or 33001, passes. `Registry.paper_c_block` (`seeds.py:372`) exists but nothing calls it.
   - No collision with the proposed Paper C blocks today: the nearest unregistered value is 15,000 below `paperc_instances`.
   - *Fix:*
     - add three blocks and list them in the report:
       - `harness_node_default` [42, 43), kind "external", read from the harness pin's node code (cite STATUS F4 until it is read);
       - `e2e_smoke` [999, 1000);
       - `tracks_superseded_audits` [33001, 35000), kind "prose_only";
     - make the check positive when a registry is passed: instance, worker, audit and ε seeds must lie in a Paper C block, and `worker_seed=None` is allowed only on synthetic rows.

4. **MINOR: K_DOMAIN and COUNT_DOMAIN are declared, not bounded by code.**
   - Nothing in the code bounds these arguments:
     - `e1b_collect.py:410` `--instances`;
     - `e1b_collect.py:415` `--audit-seeds`;
     - `e1_noise_floor.py:214` `--seeds`.
   - `K_DOMAIN = 90` (`seeds.py:48`) is chosen to fit below the next block, which is circular.
   - It is conservative against observed use: the configs use 18 and 2, and no recorded seed lies outside its block. So it is acceptable, but the runbook's STOP rule is never exercised.
   - *Fix:*
     - say in the report and the docstring that these are declared domains;
     - add a pinned-results check that recorded e1b, noise-floor and leaf-audit seeds lie inside them.

5. **MINOR: `unaccounted` checks only endpoints.**
   - `_ints` (`seeds.py:264–265`) reduces a range to `[start, stop-1]`, and line 320 tests only those two values. I checked that a constant `range(100, 5500)` is reported as accounted, although 997–1000 and 4001–5000 lie in no block.
   - Base constants (`B2_SEED_BASE`, `AUDIT_SEED_BASE`) are checked at the base only.
   - *Fix:* test that each range or (lo, hi) pair is covered by the union of blocks (an interval cover), not just its endpoints.

6. **MINOR: `function()` is acceptable under the "do not import" rule, but fragile.**
   - It imports nothing and runs only one function body with restricted builtins. I accept it.
   - However, `exec` also evaluates decorators and default arguments at def time. I checked that a default `sum(map(ord, ...))` is evaluated.
   - Restricted builtins are not a sandbox.
   - On Python 3.13 it works only because `compile()` inherits seeds.py's own `from __future__ import annotations`. With `dont_inherit=True`, the pinned `_instance_seed` fails with `NameError: name 'str' is not defined`.
   - *Fix:* either option works:
     - before compiling, assert the FunctionDef has no decorators, no defaults, and a single `Return` built only from BinOp, Constant, Name and Call(sum|map|ord); then strip the annotations;
     - or evaluate the `Return` expression with `_eval`, extended with `Mod` and those three calls, with no `exec` at all.

7. **MINOR: the claim for the `pc-` prefix is overstated, and the prefix is not enforced.**
   - D26 is the first four bytes of SHA-256(campaign|budget|rep|rev) (`r1/exam/stage_a.py:60`). A distinct prefix makes the inputs distinct. It does not make the 32-bit outputs disjoint: with about 1e5 calls on each side, a few birthday collisions are expected.
   - These collisions are harmless (the prompts differ), but report line 28 and `seeds.py:79` say "disjoint".
   - Neither `schema.py` nor the registry checks the prefix.
   - Track S's `seed_key_for` (`collect.py:744–746`) builds `tracks_{node}__s{seed}`, so the SPT port must change it.
   - *Fix:*
     - reword to "distinct D26 inputs";
     - check `campaign_id.startswith(PAPER_C_CAMPAIGN_PREFIX)` when a registry is passed.

8. **MINOR: the scope of the global namespace is not written down, and Paper C has no block for training seeds.**
   - One global namespace for worker and audit seeds is the right, conservative choice. Paper B passes the same integers as train/split seeds on every node, so a global check is a superset of plan §11.1's (node, seed) key.
   - The docstring (`seeds.py:6–8`) should say what lies outside that namespace:
     - D26 LLM seeds;
     - structured RNG keys `default_rng([seed, inst, …])` in the Track S simulators (`simulate_controls.py` defaults 0, 1, 11, 77, 78, 777, 9000, 9100; `synthetic.py`; `worlds.py`);
     - ML training seeds (Track P uses 0–2, `trackp_portal.json:106–144`).
   - Paper C reserves nothing for its own SPT-5 training seeds (plan line 229).
   - *Fix:* document the scope, and either reserve a Paper C training-seed block or declare training seeds a separate namespace.

9. **MINOR: no declared source table.**
   - Runbook P2 step 1 asks for a table in the module: branch, pin, path, symbol, bound. The sources are written inline in `paper_b_blocks()` (`seeds.py:150–225`), and branch names appear only in comments.
   - *Fix:* add a module-level `SOURCES` table that drives `paper_b_blocks()`, and write it into the registry JSON.

## Summary

The code reads the pins with `git show` and `ast`, the registry regenerates byte for byte, the tests pass, and the proposed Paper C blocks collide with nothing in code or recorded results. Three problems remain:
- the author-facing report and BUILD_STATUS propose a block that does collide (finding 1);
- the completeness guarantee is false (finding 2);
- the most-used Paper B worker seed, 42, is not registered, while the P1 check is negative-only (finding 3).

Verdict: NOT ACCEPTED

---

## Round 2 (16 Nov 2026)

Reviewed HEAD `6cf968e` against the response table `BUILD_P2_RESPONSE_R1_20261116.md`. Census and P3 files were not reviewed.

### What I checked

- **Commands:**
  - pytest gave **84 passed** (10 in `test_seeds.py`).
  - `python -m paperc.seeds`, then `git diff --stat`: empty, so the registry is still reproducible.
- **Registry:**
  - 44 Paper B blocks (21 literal, 15 rng_key, 4 base_count, 2 prose_only, 1 external, 1 formula);
  - 4 Paper C blocks;
  - `check_disjoint` is empty;
  - the worker-seed overlap list is empty. The two listed overlaps are RNG roots: 777 inside the e1b range, and 999.
- **Re-read:** `seeds.py` in full, the `check_campaign` diff in `schema.py`, the test diff, the rewritten report, and `BUILD_STATUS.md:9`.
- **Probe of the new checks:**
  - These are flagged: a worker seed of 42, a worker seed in `paperc_train_seeds`, an ε seed in `paperc_instances`, an audit block that straddles 11,000,000, and the campaign id `PC-c1`.
  - `check_campaign` with a registry has no other caller in `paperC/src`, so the stricter check breaks nothing.
- **Round-1 probes re-run:**
  - `range(100, 5500)` is now flagged (gaps 997–998 and 4001–5000).
  - A def-time default is no longer evaluated.
  - The pinned `_instance_seed` compiles with `dont_inherit=True`.
- **A broader AST probe at both pins.** It covers every integer literal in:
  - function defaults and call keywords whose name contains `seed`;
  - argparse `--*seed*` defaults;
  - local assignments to `*seed*` names;
  - positional arguments of `default_rng`, `RandomState`, `seed`, `manual_seed` and `Random`.

  Every value ≥ 10 lies in a block. The values outside every block are below 10 (0, 1, 7; out of scope by design) or are counts (`--seeds 10`, `--audit-seeds 6`, `AUDIT_SEEDS = 6`).
- **Results scans re-run:** 1935 / 2314 JSON and 528 / 1215 JSONL files at the two pins. No recorded value lies in any Paper C block, `paperc_train_seeds` included.

### Round-1 findings

| # | Status |
|---|---|
| 1 | Resolved. The report shows 10,000,000–11,000,000 and lists every added block as a difference; `BUILD_STATUS.md:9` is updated. |
| 2 | Resolved. `SCAN_NAME` matches `SEED` (tested). The three date keys are registered through `RNG_KEYS`. |
| 3 | Resolved, with one remaining gap (R2-1): blocks 42, 999 and 33001–34999 are added, and `check_campaign` now requires Paper C membership and the `pc-` prefix (tested). |
| 4 | Resolved. The bounds are stated as declarations in the docstring, `domains.note` and the report. Observed use lies inside them (round-1 scan). |
| 5 | Resolved. Coverage is now checked over whole intervals (tested). |
| 6 | Resolved, with a note (R2-4). Decorators, annotations and defaults are stripped, and the code is compiled with `dont_inherit` and an explicit flag. |
| 7 | Resolved. The wording is now "distinct inputs", and the prefix is enforced. |
| 8 | Resolved. The exclusions are named in the docstring and report; `paperc_train_seeds` 61000–62000 is added. |
| 9 | Resolved. `SOURCES`, `RNG_KEYS` and `EXTRA_BLOCKS` are declared, and `paper_b_blocks` reads exactly those. |

### Round-2 findings

1. **MINOR: `worker_seed=None` still passes on non-synthetic rows.**
   - `schema.py` (the new membership block) skips a role whose value is `None`.
   - I checked that an E-T0 `digits_mlp` row with `worker_seed=None`, which means the node default 42, gives no violation.
   - *Fix:* when a registry is passed and `identity.tier != "E-SYN"`, require an explicit worker seed (or record the default explicitly so that the check sees 42).

2. **MINOR: completeness scan (c) reads only parameters and keywords named exactly `seed` / `seed0`.**
   - It does not read argparse defaults (`default=`), other `*seed*` names (`order_seed`), or positional RNG-constructor literals.
   - At the pins, every such literal ≥ 10 lies in a block, but two only by coincidence:
     - `torch.Generator().manual_seed(1234)` (`r1/c3/train/model.py:495` at `fab88fc`) lies inside `noise_floor_train`, and it is missing from the report's RNG-root table;
     - `probes/determinism.py`'s `--order-seed` default 20261029 is registered only through other sources.
   - *Fix:*
     - widen (c) to any name containing `seed`, plus argparse `--*seed*` defaults and positional RNG-constructor arguments;
     - add `r1/c3/train/model.py` 1234 to `RNG_KEYS`.

3. **MINOR: a count in the report is wrong.** Report line 21 says "the four items on `IGNORED`"; there are five (`seeds.py:152–158`). *Fix:* say five, or name them.

4. **MINOR (note; no action required for acceptance): `function()` still `exec`s the function body without validating it.**
   - Only `sum`, `map` and `ord` are available, but I checked that a body using `().__class__` runs.
   - With def-time evaluation removed and the pins fixed, this is acceptable under the "do not import" rule.
   - An AST whitelist of the body (a single `Return` built from BinOp, Constant, Name and Call(sum|map|ord)) stays optional.

No BLOCKING or MAJOR findings remain. The registry is generated from code at the pins, it regenerates reproducibly, it is disjoint from every Paper B block by at least 1000, and nothing in code or recorded results lies in a Paper C block.

Verdict: ACCEPT
