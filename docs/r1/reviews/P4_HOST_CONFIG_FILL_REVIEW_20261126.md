# Independent read-only review — P.4 T3 host-config fill commit, 26 November 2026

**Verdict: ACCEPTED.** No blocking finding. Every T3 criterion of the accepted P.4 cluster test plan passes: the
host config is the `p4_fill_host_config.py` output from the committed `host_fill.json` on top of the published pre-fill
file, exactly the 19 values changed, `--check-config` clean, the printed file sha256 is T3's, and all four arms pass
`check_local_paths`. The commit is publishable so `paper.commit` can include it. One non-blocking finding (n1) asks
the coordinating chat to disposition an evidence phrase before the host-config sha256 is frozen into the probe
spec/note; three cosmetic notes (n2-n4).

**Unit.** Branch `p4-hostconfig-fill-20261126` @ `82a7bf1c1328ca875786ecf85777b588d9533e19` (pushed;
`origin/p4-hostconfig-fill-20261126` = `82a7bf1c…`), one commit on published main `f1f1b6511983b03a5632429ef62c0db0856f649c`
(`origin/main` = `f1f1b651…`; the branch is 1 commit ahead of and 0 behind `origin/main`). It implements step 4 of
`docs/r1/reports/trackp_p4_runner_20261122/P4_CLUSTER_TEST_PLAN_20261124.md` (§5.2 lines 763-789, T3 lines 370-385,
§6 step 4 lines 866-872) using the reviewed fill hook
`r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py` (on `main`; unchanged by this commit).

**Reviewed bytes** (sha256 of the files at `82a7bf1c`, read from its worktree; the local copies are the commit's blobs):

| File | sha256 | Notes |
|---|---|---|
| `r1/scripts/configs/trackp_htcondor_v2.json` (new) | `4b4a1233301cbc354e2112f33a89db08e6ff97c94452ffddbed8744948254af0` | 7,689 B; T3 file sha256 |
| `r1/scripts/configs/trackp_htcondor_v2.json` (at `f1f1b651`) | `18f18cfc74d9a6b7aaf31124623883da513967dd8258e4339ef264d7e47e4140` | 7,689 B; matches the plan's "today" value |
| `docs/r1/reports/trackp_p4_cluster_20261126/host_fill.json` | `481e94d780f01820b5e0f7722b81fce100de9d6c9e8f92b63f2238fbd08a4177` | 1,294 B; the fill input |
| `…/HOST_CONFIG_FILL_20261126.md` | `9e09844eb9d6edb02c83dc235360afb158c9693e7e327fc3cfcac6eeb0865c4f` | 1,854 B |
| `…/T3_check_config.json` | `1174df9760caf9a0ee06f758f8d5a08c871982b3ba62eaf192e8e8ad3bb3de81` | `--check-config` output |
| `…/T3_local_paths.json` | `f9cda3ddd5ecd8d5ed3ad0f7be6c4b236ccc9e1f2484a0dbb652ae72eab527b4` | `check_local_paths` output |
| `…/T3_host_config_sha256.txt` | `3931669cf5cdc25cbb3a4404c0223085bcaae10dff7584ce0579530a52d1d635` | `sha256sum` output |

The plan copy in the reviewed tree, `P4_CLUSTER_TEST_PLAN_20261124.md`, has sha256
`ce1fccc58a8d19600030019a1b3b06ab0a4a29942d1d229148122ef1cdf4bc8d`; it carries the 25 Nov status note (F5 done, etc.)
and the T3 procedure used below.

## What I verified

### 1. The config is the script's output, not a hand fill

I extracted the committed tree to scratch (`git archive 82a7bf1c`), put the *pre-fill* config (`git show
f1f1b651:…`, sha256 `18f18cfc…`) back, and ran the committed script and the committed input:

```
p4_fill_host_config.py docs/r1/reports/trackp_p4_cluster_20261126/host_fill.json \
    --config r1/scripts/configs/trackp_htcondor_v2.json --dry-run
```

It returned `"filled": 19`, `"previous_sha256": "18f18cfc…"`, `"sha256": "4b4a1233…"`,
`"placeholders_left": []`, `"values_sha256": "481e94d7…"` and the same four `local_paths` as
`T3_local_paths.json`. A real (non-`--dry-run`) run on the scratch copy produced a config **byte-identical**
(`cmp`) to the committed config with sha256 `4b4a1233…`. A hand edit that changed any other byte, or that produced
another sha256, would not match this reproduction.

The script's `--template` output vs the committed `host_fill.json`: every forced value is character-identical to the
template (so FIXED was not overridden), the template `comment` is retained, and the only differences are the six
`FILL: …` hints replaced by the chat's values plus the `venv.causal_conv1d` text with the real build-log sha256.

### 2. Exactly the 19 placeholders, none partial, none extra

- Pre-fill config: `run.placeholders()` = exactly the script's 19 `EXPECTED` paths (12 `FIXED` + 6 `RELATIVE` + 1
  `FREE_TEXT`), i.e. the plan's 19 values; the only other `TODO_VERIFY` string is inside the top-level `comment`
  key, which the plan and `run.placeholders` ignore (`r1/c3/train/run.py:61-74`).
- Post-fill config: `placeholders == []`; `run.load_config()` with the strict (no-placeholder) rule passes; no
  `FILL`/`TBD`/`PENDING` value remains.
- `host_fill.json`: `schema` `trackp_p4_host_fill/1`; `values` keys == the 19 `EXPECTED` paths exactly (no missing,
  no unknown, no duplicate dotted spelling); every value a non-empty trimmed string that is not a placeholder and
  passes `p4_fill_host_config.check_value`; each value equals the config leaf it names.
- Forced values match the script's rules computed from `p4_lib` on this tree: `gpu.name` "NVIDIA H200" (=
  `p4_lib.GPU_MODEL`), `gpu.compute_capability` "9.0", `venv.path` "/opt/r1/envs/trackp" (=
  `Path(p4_lib.ENV3_PYTHON).parents[1]`), `hf_home` "hf", `models_dir` "models", `runs_dir` "out", and the six
  arm paths `models/<base registry key>` / `models/<adapter registry key>` (the names checked by
  `p4_lib.check_local_paths`; all exist in `r1/c3/train/registry.yaml`).
- Chat-chosen values are valid under the script's own rules: `work_dir="."` and `gpu.lock_path="gpu0.lock"` and
  `bases.laya/startlux-*.local_path="models/<key>"` all pass `_relative_ok` (job-relative, no absolute path, `~`,
  `..`, backslash or empty segment); `venv.causal_conv1d` names both `1.7.0` and `R1-TRACKP-IMAGE-V22-B`, and its
  build-log sha256 `fe872a3e…3312` and `TORCH_CUDA_ARCH_LIST 8.0;8.9;9.0` match
  `docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md` lines 27 and 34 (`venv.causal_conv1d` is inert to
  the code; see n1).

### 3. The commit changes only those 19 values (plus its own record)

- `git diff --name-status f1f1b651 82a7bf1c`: one modified file (`r1/scripts/configs/trackp_htcondor_v2.json`,
  numstat 19/19) and five added files under `docs/r1/reports/trackp_p4_cluster_20261126/` (report,
  `host_fill.json`, the three T3 captures). No `r1/scripts`, `r1/tests` or other config change; no file-mode change;
  no `.fill-tmp` residue in the tree.
- At the line level the two configs have the same number of lines, exactly 19 lines differ (the 19 placeholders'
  lines), and no line is added or deleted. Putting the 19 pre-fill values back with the script's own path mapping
  and re-serialising in the repository layout (indent 1, ASCII, final newline) reproduces the pre-fill file **byte
  for byte** (sha256 `18f18cfc…`). This is the same no-other-change rule the shipped F5 test enforces.

### 4. T3 checks reproduce exactly

Run on the scratch copy of the fill commit with the plan's T3 commands (lines 374-378):

- `trackp.py --config r1/scripts/configs/trackp_htcondor_v2.json --check-config` → **rc 0**, `placeholders: []`,
  `sha256: e507642a2087b70e4ebf10e000579b9b46ae3b455b14a4d7461fadbbcc164866` — this is the `config_digest`
  (`sha256(json.dumps(cfg, sort_keys=True))`, `r1/c3/train/run.py:85-86`), independently recomputed from the
  committed config. The output is **byte-identical** to `T3_check_config.json`. The same command on the pre-fill
  config gives rc 1 and exactly the 19 placeholders, as the plan expects.
- `sha256sum` of the config = `4b4a1233…`; output byte-identical to `T3_host_config_sha256.txt`. This is the value
  the plan requires for `host_config.sha256` (line 753: "Not the `"sha256"` printed by `--check-config`"), and the
  report correctly distinguishes `e507642a…` from the file sha.
- `p4_lib.check_local_paths(a, Path('.'), Path('/nonexistent/condor/execute/dir_0'))` for all four arms returns
  `…/dir_0/models/qwen3.5-0.8b-base` (+ `models/kev-0.8b`), `…/models/qwen3.5-4b-base` (+ `models/kev-4b`),
  `…/models/qwen3.5-0.8b-base`, `…/models/qwen3.5-4b-base`, with no `STOP:`. The output is **byte-identical** to
  `T3_local_paths.json`.

Environment limit: this review host has no image env3 and no `torch`. `trackp.py` imports
`r1.c3.train.trainer` (hence `numpy`/`torch`) at module load, so I ran the CLI with the bundled Python 3.12 and a
no-op `torch` module on `PYTHONPATH` in scratch, only to satisfy that import. The `--check-config` code path
(`r1/scripts/trackp.py:493-499`) never calls torch, and its printed JSON and rc are identical to the committed
captures; `trackp.py`'s rc rule is `0 if (not left or allow) else 1`.

### 5. The values file carries the fill input only

`host_fill.json` (1,294 B) has only `schema`, `comment`, `values`; `values` is 19 short strings, no nested
objects/lists, no label, evaluation, model, weight or output data, no `/Users` or `/home` path, no token/secret.
Its sha256 `481e94d7…` is the one the report records and the one the script returns as `values_sha256`.

### 6. Publishability / `paper.commit`

- The commit's only parent is `f1f1b651` = published `origin/main`; a fast-forward merge keeps the host config at
  `4b4a1233…`, which is T3's file sha256, the value the plan puts into `host_config.sha256` (lines 382, 551, 753,
  789) and the note's `host_config:` line. No later commit on the branch changes it.
- F5 is already resolved on `main`, so this commit correctly carries no test change: at `f1f1b651`
  `r1/tests/test_trackp_p4_runner.py:1553-1567` (`_host_config_state`) accepts either the 19 placeholders or a filled
  config verified by `check_value` and restores the placeholders to sha256 `18f18cfc…`; its filled branch
  (lines 1588-1595) also runs `check_local_paths` and accepts a placeholder or the exact file sha;
  `test_trackp_sft.py:597-600` accepts the placeholder or a `venv.causal_conv1d` naming `1.7.0` and
  `R1-TRACKP-IMAGE-V22-B`. I emulated those filled-state assertions on the committed config: they pass (19/19
  `check_value`, restore sha `18f18cfc…`, 4/4 `check_local_paths`; the shipped spec's `host_config.sha256` is still
  a placeholder, which the test allows). The commit touches no test or code file.
- Branch worktree is clean, the tip equals the pushed branch, and the branch is exactly one commit ahead of
  `origin/main`. This matches the plan's definition of the host-config fill commit (lines 46-49) as its own reviewed
  commit before `paper.commit`, and the probe clones it (line 519).

### 7. The report's claims match the artifacts

The report's previous/new/host_fill sha256 values, "19/19, none left", the forced/chosen-value summary, the
`--check-config` rc and digest, the four arm paths, and "Tests were not edited (F5 is already on main)" all match
what I reproduced. Its "Diff" sentence (n3) is the only wording nit.

## Findings

**n1 (non-blocking; for the chat to disposition before the host-config sha is frozen).**
`venv.causal_conv1d` ends "…, confirmed by T1 and T2". T2 did PASS (25 Nov report lines 36-40: `status: identical`,
raw `causal-conv1d==1.7.0`), and the build arch/sha are from `V22_BUILD_20261124.md`. T1, however, had **not** run:
the cluster's own report on this branch's tree says T1 is "BLOCKED/queued", "no `versions.out` yet" (lines 26-34,
69) and "Job 760065 remains queued unchanged; T1 output cannot be produced until capacity returns" (lines 76-81);
its later commit on `trackp-p4-cluster-20261125` (`8a9d48a1f`, authored `2026-11-26T02:28:44+01:00` = 01:28:44Z,
26 s after this fill commit; its "Update 26 Nov 01:30Z" section) repeats "job 760065 remains idle … 0 H200 machine
ads at 01:28:35Z". So the phrase records a confirmation that does not yet
exist; the plan's own suggested value (line 787) does not contain it (the phrase comes from the reviewed fill hook's
hint, `p4_fill_host_config.py:65-66`), and the script's validity rule only needs `1.7.0` and
`R1-TRACKP-IMAGE-V22-B`. It is inert to the code and cannot be false when used: T1's value gates the probe (plan
line 874, STOP S4) and is needed for `image.versions_sha256` in the spec-fill, so the statement will be true before
the probe runs and before `host_config.sha256` is frozen. Recommendation: when T1 runs, cite its committed
`versions.out`/`T1_versions` record, or reword now — but note that rewording changes the host-config sha256 and
therefore T3's file sha, the report and the commit message; the chat should decide whether to do that before merge or
let the phrase stand as a forward reference that T1 satisfies before the config is used. This is not a finding
against the fill mechanics.

**n2 (cosmetic).** `host_fill.json` keeps the template `comment` ("every value confirmed on the host …; the FILL
values must be replaced") although the values are now filled and the forced paths are script-determined, not
host-confirmed. The script ignores `comment`; only the file bytes/sha256 matter.

**n3 (cosmetic).** The report's Diff sentence names the config "plus this record and `host_fill.json`" but the commit
also adds the three T3 capture files. Scope is nevertheless exactly the six files above.

**n4 (cosmetic).** `host_fill.json` has no trailing newline (last byte `}`), unlike the repository's other committed
JSON; the script reads bytes, so its sha256 `481e94d7…` and the fill are unaffected.

## Limits of this review

- This host has no image env3 and no `pytest`, so I did not re-run `r1/tests/test_trackp_p4_runner.py` or
  `test_trackp_sft.py`, nor the full suite. The F5 evidence I relied on is the test source at `f1f1b651` (unchanged
  by this commit) plus a direct emulation of its filled-state assertions on the committed config; the F7 unit report
  on `main` records 119 passed for the pre-fill state. The empty worktree, clean `--check-config` and the commit's
  scope make a test-only regression implausible, but this review does not claim to have executed the suite.
- I did not run T3 inside the v2.2 image; I re-ran the exact T3 commands on this host (with the torch stub described
  above) and got byte-identical artifacts. The "in the image, no GPU" provenance of the captures is the report's
  claim, not independently observed by me.
- I did not run or re-check T1/T2 (they are outside this commit); their status is read from the committed cluster
  reports on this tree and the pushed cluster branch.

## Independence

Read-only on the reviewed branch and its worktree: no file, commit, ref, job or config was changed, and nothing was
pushed. Scratch work was under `/private/tmp` (`git archive` extraction; the pre-fill config from `git show`; the
fill run and the CLI checks). The only file written under the workspace is this review. Two pre-existing local
branches/refs were only read (`git rev-parse`, `git ls-remote`, `git log`, `git show`).
