# Fresh independent review — P.4 T3 host-config fill commit (26 November 2026)

**Verdict: ACCEPTED.** No blocking finding. Independently re-running the reviewed fill hook reproduces the
committed config byte for byte from the committed input, exactly the 19 `TODO_VERIFY_ON_HOST` values change,
`--check-config` is clean with the captured digest, the T3 file sha256 is `4b4a1233…`, and all four arms pass
`check_local_paths`. The commit is fast-forward publishable so `paper.commit` can include it. One non-blocking
finding (n1) asks the coordinating chat to tighten the `venv.causal_conv1d` phrase "confirmed by T1 and T2"
before the host-config sha256 is frozen; two cosmetic notes (n2, n3).

This review was made from scratch and does not rely on the earlier review that the branch tip carries
(`389bc514`, `docs/r1/reviews/P4_HOST_CONFIG_FILL_REVIEW_20261126.md`); that file was read only after the checks
below were completed. Nothing was pushed and no job was submitted.

## Unit and reviewed bytes

Branch `p4-hostconfig-fill-20261126`; reviewed commit **`82a7bf1c1328ca875786ecf85777b588d9533e19`** (tree
`c940a42ee080540e97fb5566b452d4ed12319a52`), parent **`f1f1b6511983b03a5632429ef62c0db0856f649c`** = published
`origin/main` = `f1f1b651…` at review time. Branch tip `389bc514…` = this fill commit + the earlier review doc;
branch is **2 ahead / 0 behind** `origin/main`.

| Path at `82a7bf1c` | sha256 | Notes |
|---|---|---|
| `r1/scripts/configs/trackp_htcondor_v2.json` | `4b4a1233301cbc354e2112f33a89db08e6ff97c94452ffddbed8744948254af0` | 7,689 B; T3 file sha256 |
| same file at `f1f1b651` | `18f18cfc74d9a6b7aaf31124623883da513967dd8258e4339ef264d7e47e4140` | 7,689 B; the plan's "today" value |
| `docs/r1/reports/trackp_p4_cluster_20261126/host_fill.json` | `481e94d780f01820b5e0f7722b81fce100de9d6c9e8f92b63f2238fbd08a4177` | 1,294 B; fill input |
| `…/HOST_CONFIG_FILL_20261126.md` | `9e09844eb9d6edb02c83dc235360afb158c9693e7e327fc3cfcac6eeb0865c4f` | report |
| `…/T3_check_config.json` | `1174df9760caf9a0ee06f758f8d5a08c871982b3ba62eaf192e8e8ad3bb3de81` | `--check-config` capture |
| `…/T3_local_paths.json` | `f9cda3ddd5ecd8d5ed3ad0f7be6c4b236ccc9e1f2484a0dbb652ae72eab527b4` | `check_local_paths` capture |
| `…/T3_host_config_sha256.txt` | `3931669cf5cdc25cbb3a4404c0223085bcaae10dff7584ce0579530a52d1d635` | `sha256sum` capture |

Unchanged supporting files used: fill hook `r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py`
`523256060271038441aaa573387ed019d7b994cb1e96c77c46f40f65f1744d0e`; `p4_lib.py`
`cabe1d7249e78458cdbcaa0d55d996b97a4250aff0a915a88c7923aed682427e`; `r1/tests/test_trackp_p4_runner.py`
`36e2a058d061c62b52952bd317e56ebc3acc86d1db8f8e982dac43efeb52e752`; cluster test plan
`ce1fccc58a8d19600030019a1b3b06ab0a4a29942d1d229148122ef1cdf4bc8d`.

Method: both commits extracted with `git archive` into `/tmp` scratch; the fill hook was dry-run and then really
run there against the pre-fill config restored with `git show f1f1b651:…`; the T3 commands were re-run on the fill
tree; hashes/bytes compared with `cmp`/`sha256sum`. The review host has no image env3, no `torch` and no `pytest`;
for the `trackp.py --check-config` CLI only, a no-op `torch` module on `PYTHONPATH` was used to satisfy the module
import (the `--check-config` path never calls torch).

## 1. The fill-hook output reproduces exactly

On the pre-fill config (`18f18cfc…`) with the committed `host_fill.json`:

```
p4_fill_host_config.py docs/r1/reports/trackp_p4_cluster_20261126/host_fill.json \
    --config r1/scripts/configs/trackp_htcondor_v2.json --dry-run
```

gives `"filled": 19`, `"previous_sha256": "18f18cfc74d9…e4140"`, `"sha256": "4b4a1233301c…4af0"`,
`"placeholders_left": []`, `"values_sha256": "481e94d7…4177"`, `"written": false`, and the same four
`local_paths` as `T3_local_paths.json`. A real (non-dry) run on the scratch copy writes a file **byte-identical**
to the committed config (`cmp` equal, sha256 `4b4a1233…`), so the commit is exactly the hook's output from the
committed input, not a hand fill.

## 2. Exactly 19 values, no partial fill, no other change

- Pre-fill config: `r1.c3.train.run.placeholders()` = exactly the 19 known paths = the hook's `EXPECTED`
  (12 forced + 6 relative + 1 free text). The only other `TODO_VERIFY` string in the file is inside the top-level
  `comment` value, which the code rule and the plan ignore.
- Post-fill config: `placeholders == []`; `R.load_config()` in strict mode passes; no `FILL`/`TBD`/`PENDING`
  value remains.
- `host_fill.json` has `schema: trackp_p4_host_fill/1` and `values` whose keys equal the 19 `EXPECTED` paths
  exactly (no missing, no unknown). Every value equals the config leaf it names and passes
  `p4_fill_host_config.check_value`.
- Reverse mapping (put the 19 pre-fill values back with the hook's own path resolution and re-serialise in the
  repository layout, indent 1, ASCII, final newline) reproduces the pre-fill file **byte for byte**
  (`18f18cfc…`). Combined with `git diff --numstat` = `19 19` for the config and 19 changed leaves with no leaf
  added/removed, this is the "nothing else changed" rule.
- Negative checks on the hook: an already-filled config is refused (rc 2, "must hold exactly the 19 known
  TODO_VERIFY_ON_HOST values"); an 18-value input is refused (rc 2, `no partial fill`); a wrong forced value is
  refused (rc 2). The pre-fill config through the real CLI gives rc 1 and exactly the 19 placeholders — the T3
  captures are therefore from the filled state, not a placeholder state.

## 3. The 19 values against the plan and host verification

Every value matches §5.2 of `P4_CLUSTER_TEST_PLAN_20261124.md` and the code constraints:

| Values | Independent basis |
|---|---|
| `bases.kev-0.8b/kev-4b` base+adapter paths; `bases.qwen3.5-0.8b-base/-4b-base` base paths | `models/<registry key>` is what `p4_lib.check_local_paths` requires and `p4_lib.stage` creates (`job_dir/models/<key>`); all four keys exist in `r1/c3/train/registry.yaml`; 4/4 arms pass `check_local_paths` |
| `gpu.name = NVIDIA H200` | `p4_lib.GPU_MODEL`; plan §5.2 line 779; the v2.2 staged smoke asserts `get_device_name(0) == "NVIDIA H200"` and passed unchanged (759997); `/opt/r1/VERSIONS.txt` capture in the v2.2 I3 record |
| `gpu.compute_capability = 9.0` | plan §5.2 line 780; the same smoke asserts `torch.cuda.get_device_capability(0) == (9, 0)` and passed on v2.2 (759997), no assertion relaxed (accepted P5 review); H200 is sm_90 |
| `venv.path = /opt/r1/envs/trackp` | `Path(p4_lib.ENV3_PYTHON).parents[1]`; the v2.2 env3 freeze capture (`T2_env3_freeze.json`) was taken from that path inside the image and reads `status: identical`; image build creates that venv |
| `hf_home = hf`, `models_dir = models`, `runs_dir = out` | `p4_lib.offline_env` sets `HF_HOME=job_dir/hf`; `p4_lib.stage` stages into `job_dir/models`; `trackp.py` writes the lease log to `<runs_dir>/gpu_lease_log.jsonl` with cwd = job dir (`p4_lib.trackp`), the lease creates its parent, and the P.4 job tars `out` into `out.tar` |
| `work_dir = .`; `gpu.lock_path = gpu0.lock`; `bases.laya/startlux-*.local_path = models/<key>` | plan §5.2 lines 778-785 (suggested exactly these); all pass the hook's relative-path rule; the trackp job runs with cwd = job directory so they resolve inside the job scratch; the four unused bases have no P.4 code path (only the fill hook names them; `p4_lib.ARMS` and `validate_spec` admit only the four arms) |
| `venv.causal_conv1d` text | names `1.7.0` and `R1-TRACKP-IMAGE-V22-B` (plan line 787); the build facts match `V22_BUILD_20261124.md`: source build in image v2.2, `TORCH_CUDA_ARCH_LIST="8.0;8.9;9.0"`, build-log sha256 `fe872a3e…3312`, installed by name; the v2.2 env3 freeze capture is `causal-conv1d==1.7.0` (T2, PASS). The trailing "confirmed by T1 and T2" is n1 below |

## 4. The T3 captures reproduce exactly

On the fill tree, the plan's T3 commands:

- `trackp.py --config r1/scripts/configs/trackp_htcondor_v2.json --check-config` → **rc 0**, stdout
  **byte-identical** to `T3_check_config.json`: `placeholders: []`, `sha256:
  e507642a2087b70e4ebf10e000579b9b46ae3b455b14a4d7461fadbbcc164866`. That value is `run.config_digest`
  (`sha256(json.dumps(cfg, sort_keys=True))`), independently recomputed from the committed config and distinct
  from the file sha256, as the report says.
- `sha256sum r1/scripts/configs/trackp_htcondor_v2.json` = `4b4a1233…`, byte-identical to
  `T3_host_config_sha256.txt`; this is the plan's `host_config.sha256` value.
- `p4_lib.check_local_paths(a, Path('.'), Path('/nonexistent/condor/execute/dir_0'))` for all four arms →
  `/nonexistent/condor/execute/dir_0/models/<registry key>` (plus the adapter for the two Kev arms), no `STOP:`;
  stdout **byte-identical** to `T3_local_paths.json`.

The pre-fill config gives rc 1 with the 19 placeholders through the same CLI, so the captures are consistent with
the filled state and with the plan's expectation.

## 5. Commit scope and tests

`git diff --name-status f1f1b651 82a7bf1c` = one modified file (`r1/scripts/configs/trackp_htcondor_v2.json`,
numstat 19/19) plus five added files under `docs/r1/reports/trackp_p4_cluster_20261126/` (report, `host_fill.json`,
the three T3 captures). No `r1/tests`, no other `r1/scripts` or config change; all added modes 100644; no
`.fill-tmp`/`.orig`/`.rej` residue.

Not touching tests is correct: F5 is already resolved on `main`. At `f1f1b651` the runner test's
`_host_config_state` accepts a filled config — it runs the hook's `check_value` on all 19 values and asserts the
19 placeholders restored give sha256 `18f18cfc…` — and its filled branch also runs `check_local_paths` for all
arms and accepts either a placeholder or the exact config file sha256 in the spec; `test_trackp_sft` accepts the
placeholder or a `venv.causal_conv1d` naming `1.7.0` and `R1-TRACKP-IMAGE-V22-B`. Emulating those filled-state
assertions on the committed config passes (19/19 `check_value`, restored sha `18f18cfc…`, 4/4 local paths). The
spec `p4_spec.json` is untouched and still holds the placeholder `host_config.sha256`, which is the plan's
later spec-fill commit; nothing here needs it changed.

## 6. Publishability

`origin/main` (`f1f1b651…`) is an ancestor of the branch tip; the fill commit's only parent is `origin/main`. A
fast-forward merge keeps the config at `4b4a1233…`, the T3 file sha256 that the plan feeds into
`host_config.sha256` and the note's `host_config:` line. The branch's second commit (`389bc514`) adds only the
earlier review doc; it does not change the config or the captures.

## Findings

**n1 (non-blocking; for the chat to dispose before `host_config.sha256` is frozen into the probe spec/note).**
`venv.causal_conv1d` ends "…, confirmed by T1 and T2". T2 is a PASS (25 Nov report: v2.2 env3 freeze `status:
identical`, `causal-conv1d==1.7.0`), and the build facts are in `V22_BUILD_20261124.md`. The T1 **job** (760065),
however, was still queued at commit time: the cluster report in this commit's tree (published main, 25 Nov) says T1
is "BLOCKED/queued", "no `versions.out` yet", "T1 remains queued, not complete", and "T1 output cannot be produced
until capacity returns"; the parallel cluster branch's 26 Nov 01:28Z update (not an ancestor of this commit)
repeats 0 H200 machine ads and 760065 idle. The underlying v2.2 `/opt/r1/VERSIONS.txt` text and sha (`aaa1a304…`) are nonetheless recorded
through the plan's Route B by the accepted P5 review (§m4), so the facts are evidenced — only the attribution to
"T1" is premature/ambiguous, and the plan's own suggested value (line 787) does not contain the phrase. The value
is inert to the code (the hook's only rule for it is naming `1.7.0` and `R1-TRACKP-IMAGE-V22-B`; the filled-state
test checks only that), and T1/Route B is needed before the probe's `image.versions_sha256` is filled, so it can
still become true before the config is used. Recommendation: when T1 runs, cite its committed `versions.out` (or
the P5 Route B value) — or reword now, accepting the consequent change of the host-config sha256, the T3 captures
and the report/commit-message text. This is not a finding against the fill mechanics.

**n2 (cosmetic).** The report's Diff sentence says the commit is the config "plus this record and
`host_fill.json`", but the commit also adds the three T3 capture files. The actual scope is exactly the six files
above and is correct.

**n3 (cosmetic).** `host_fill.json` keeps the fill hook's template `comment` ("the FILL values must be replaced")
although the values are filled, and it has no trailing newline (last byte `}`). The hook reads bytes and the
committed sha `481e94d7…` is the one recorded; no functional effect.

## Limits of this review

- This host has no image env3, no `torch` and no `pytest`, so the full runner test suite was not executed; the F5
  evidence is the test source on `main` (unchanged by this commit) plus a direct emulation of its filled-state
  assertions on the committed config. The `--check-config` CLI was run with a no-op `torch` stub only to satisfy
  the module import; that code path never calls torch and its rc/output match the committed capture.
- I did not run T3 inside the v2.2 image; I re-ran the exact T3 commands here and the captures are
  byte-identical, but the "in the image, no GPU" provenance of the captures is the report's claim, not
  independently observed by me.
- I did not run T1/T2; their status is read from the committed cluster report, the T2 capture and the accepted P5
  review on this tree.

## Independence / read-only

No file, commit, ref, job or config was changed; nothing was pushed or submitted. Scratch work was only under
`/tmp` (`git archive` of both commits, the fill runs, the CLI checks). The only file written under the workspace is
this review. The earlier review and the branch tip were only read, after this review's checks were done.
