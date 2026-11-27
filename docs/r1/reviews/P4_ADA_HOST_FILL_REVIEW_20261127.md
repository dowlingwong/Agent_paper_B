# Independent review — Ada P.4 host-config fill (27 November 2026)

Verdict: ACCEPTED

**Reviewer.** I am an independent tier-E reviewer. I did not write the fill, the fill input, the config values or the
test changes, and did not author the unit record. I reviewed commit `77e364e7` in my own worktree, made no change to
the author's branch, ran no job and no probe, opened no sealed or label file, and wrote nothing on Ada except the
read-only shell commands listed below. The only file I changed is this review.

**Summary.** The committed `r1/scripts/configs/trackp_ada_v1.json` is byte-for-byte the output of the reviewed fill
hook applied to the base template with the committed `host_fill.json`: exactly the 26 `TODO_VERIFY_ON_HOST` values
were replaced and nothing else. The file sha256 equals the value pinned by the note, all 26 values match the fill
input, and every host fact in `host_check.txt` that I could re-read over SSH matches. The test changes keep the
26-placeholder and 26-value enforcement and only build a template copy for the fill-hook fixtures. No probe, SFT or
evidence run is present in the commit or on the host. No BLOCKING finding; two stale-prose MINORs are noted below.

## Inputs reviewed

| Input | Ref / path | sha256 |
|---|---|---|
| Reviewed tip | `compute-p4-ada-hostconfig-20261127` @ `77e364e7` | — |
| Base | `origin/main` `66cc33f2` | — |
| Ada host config (filled) | `r1/scripts/configs/trackp_ada_v1.json` | `bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908` |
| Fill input | `…/ADA_HOST_FILL_20261127/host_fill.json` | `ec42f76d0e01bb15ab450e74a820e7587894090df34399c86dd25332345a1ca9` |
| Host check | `…/ADA_HOST_FILL_20261127/host_check.txt` | `516fea06549bedecb65dd83c47792bccb6822dc0f1d49b783614d39b8ec00a56` |
| Check-config output | `…/ADA_HOST_FILL_20261127/check_config.json` | `34748cebb7438f87724a5c23cf2becbea68f1388faf729e94bd9b0a36889e1d8` |
| Unit record | `…/ADA_HOST_FILL_20261127/ADA_HOST_FILL_20261127.md` | `3678b2533d56a42c9664200a037c2f88c54b0c3f5ae87ffb9653cfa5d76eab1d` |

`shasum -a 256 -c SHA256SUMS` in the fill directory passes all four listed files.

## What I checked

### 1. The config diff is exactly the 26 placeholders, byte for byte

- Base → tip diff touches only `r1/scripts/configs/trackp_ada_v1.json` (values) and the two test files, plus the new
  fill directory. The config diff changes exactly 26 value lines; no whitespace, key order, encoding or trailing
  newline changed.
- I reconstructed the fill independently: `git show 66cc33f2:r1/scripts/configs/trackp_ada_v1.json`, then the reviewed
  hook `p4_fill_host_config.py docs/…/host_fill.json --host-class ada_rtx6000` on that copy. Its reported
  `previous_sha256` is `b04e9fa3…`, its output sha256 is `bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908`,
  i.e. **identical to the committed file**, `placeholders_left: []`, `filled: 26`. This proves the committed bytes
  differ from the base only by those 26 substitutions.
- `host_fill.json` names exactly the 26 paths of `FH.expected("ada_rtx6000")` (`26 == 26`), and each of the 26 input
  values equals the committed config value at that path (checked through `FH._paths`, which handles the dotted arm
  names such as `bases.kev-0.8b.local_path`).
- No `TODO_VERIFY_ON_HOST` value remains anywhere in the file (the only string containing `TODO_VERIFY_ON_HOST` is the
  explanatory top-level `comment`).
- `python -B r1/scripts/trackp.py --config r1/scripts/configs/trackp_ada_v1.json --check-config` prints
  `placeholders: []` and digest `098123e3b8e52c80006d22ce478610d0583410ac46b04da6d0b3c66f966b1932`, exactly the
  committed `check_config.json`. The note correctly says this digest is not the file sha256 and that the spec/note use
  the file sha `bb0c7251…`.

### 2. The 26 filled values

| Area | Committed value |
|---|---|
| `work_dir`, `models_dir`, `runs_dir`, `hf_home` | `.`, `models`, `out`, `hf` (job-relative) |
| `gpu.name`, `gpu.compute_capability` | `NVIDIA RTX 6000 Ada Generation`, `8.9` |
| `gpu.lock_path` | `gpu0.lock` |
| `bases.kev-0.8b.*` | `models/qwen3.5-0.8b-base`, `models/kev-0.8b` |
| `bases.kev-4b.*` | `models/qwen3.5-4b-base`, `models/kev-4b` |
| `bases.qwen3.5-*.local_path`, `laya`, `startlux-*` | `models/<registry key>` |
| `venv.path` | `/opt/r1/envs/trackp` (the forced env3 path; the native route uses `direct.venv`) |
| `venv.causal_conv1d` | `1.7.0 … wheel sha256 8f676dbd…, R1-TRACKP-IMAGE-V22-B; imports on the Ada venv` |
| `direct.ssh_alias`, `hostname` | `ada_server`, `ucrtasl` |
| `direct.container_runtime`, `work_root`, `lock_dir` | `venv`, `/data1/zli538/paperb_p4_20261127/jobs`, `/data1/zli538/r1_locks` |
| `direct.shm_size`, `min_free_mib` | `16g`, `46000` |

The forced values agree with `ADA_FIXED` / `RELATIVE` / `FREE_TEXT` / `ADA_CHOICE` / `ADA_ABSOLUTE` / `ADA_PATTERN` in
`r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py:96-119`. The `ada_server` alias is the pre-existing, tested
Ada allowance (`p4_fill_host_config.py:182`; introduced in `3b32aae2`, i.e. in the base `66cc33f2`), not a new
exception.

### 3. Host facts re-read read-only on Ada (`ssh ada_server`; no write, no job, no other user's file or process)

| Fact | Record / config | Re-read 27 Nov 2026 |
|---|---|---|
| Account / uid | `zli538` / 1008 | `zli538` / 1008 |
| Hostname | `ucrtasl` | `ucrtasl` |
| Interpreter | `/data1/zli538/paperb_p4_20261127/venv/bin/python`, 3.12.10 | 3.12.10 |
| `uv` | `/home/zli538/.local/bin/uv` 0.7.8 | `uv 0.7.8` |
| Torch / CUDA / available | `2.6.0+cu124` / 12.4 / true | same |
| `causal_conv1d` | 1.7.0, wheel `8f676dbd…` | 1.7.0; wheel sha256 `8f676dbd2d42588d4fa85aabcb2da8f1bd9bf46dbdeea7b51c7dddf01e4e3e6f` |
| Driver | 545.23.08 | 545.23.08 |
| GPUs | 8 × 49140 MiB; 0/2/6/7 at 5 MiB, 1/3/4/5 shared (~33.7 GB) | same at the re-read; the four empty cards are still 5 MiB, the shared four still one foreign PID |
| `jobs` / `r1_locks` | 0700, empty | 0700, empty |
| `/data1` | 2.1 TB free, 69 % used | 2.1 TB free, 69 % used |

`direct.min_free_mib = 46000` is below the ~49.1 GB free on an empty card; `direct.work_root` and `direct.lock_dir`
exist under the reviewed account. The top-level `direct.venv` block (`python` = the reviewed interpreter,
`version` = 3.12.10) is validated by `p4_lib.ada_venv_config` (`r1/scripts/htcondor/trackp_p4/p4_lib.py:547-554`).

### 4. Test changes do not relax a fill assertion

- `_ada_template()` (`r1/tests/test_trackp_p4_direct.py:45-58`) reads the committed config and restores
  `TODO_VERIFY_ON_HOST` at `FH.expected(ADA)` — exactly the 26 paths, via the hook's own path map, and the test asserts
  `set(R.placeholders(_ada_template())) == set(FH.expected(ADA))` (line 806), so a 27th placeholder or a missing one
  would fail.
- The shipped-config assertion is split, not dropped: the template copy must still be refused as “not filled”
  (`test_the_direct_descriptor_is_canonical_and_needs_a_filled_host_config`, lines 248-252), and the committed filled
  file must have `placeholders == []` (line 807).
- The fill-hook tests still require the 26-value form and every refusal: template set equality and `len == 26`
  (lines 795-803), the nine refusal cases including the wrong alias, wrong GPU class, `podman`, a relative
  `work_root`, `..`, a bad hostname, a bad `min_free_mib` and a `FILL:` placeholder (lines 823-842), the “already
  filled: no second fill” refusal (lines 854-855), and the schema/class mismatch refusals (lines 852 and 859).
- The `ada_server` + `venv` path remains covered (`test_ada_venv_uses_the_same_entry_under_the_lease_and_seals_as_venv`,
  lines 497-513), which is exactly the committed runtime/alias pair.
- The runner fixture imports and writes the same template copy (`r1/tests/test_trackp_p4_runner.py:3489-3497`); its
  filled sha is recomputed from the fill, so no placeholder-vs-filled assumption is hidden.

No test assertion was relaxed. The only behavioural change is that the fixtures no longer copy a placeholder file that
the branch has now filled.

### 5. Test runs (Python 3.12.8 at
`/private/var/folders/…/opencode/d3venv/bin/python`; `AR_HARNESS_ROOT` pointed at the pinned harness checkout)

| Test file | Result |
|---|---|
| `r1/tests/test_trackp_p4_direct.py` | **45 passed** |
| `r1/tests/test_trackp_p4_runner.py` | **159 passed** |
| `r1/tests/test_trackp_sft.py` + `r1/tests/test_trackp_cli.py` | **35 passed, 9 skipped** |

These match the unit record. All three run on the reviewed tip; the counts are the same as claimed.

### 6. No probe, job, SFT, evidence, sudo or sealed read

- The commit changes 8 files: the fill directory (5 files), the config, and the two test files. There is no probe
  result, SFT output, evidence record or label read in the diff, and the working tree is clean.
- On Ada the `jobs` and `r1_locks` directories are empty and still dated from the earlier venv build
  (26 Nov 21:21 local); the only files under `/data1/zli538/paperb_p4_20261127` newer than the venv build are those
  two directories. No job, probe or training process is running; the shared-card processes belong to another user and
  were only sampled (`nvidia-smi` queries), never signalled or touched.
- `origin/main` is still `66cc33f2`; the branch is one commit (`77e364e7`) on that base, and I neither merged nor
  pushed to `main`.

## Findings

No BLOCKING finding. Two MINORs, both prose/legacy fields that this commit is not allowed to change (the fill hook
refuses any byte outside the 26 placeholders, and the task requires exactly the 26 substitutions):

- **MINOR m1 — stale alias in prose.** `r1/scripts/configs/trackp_ada_v1.json:2` still opens with
  “SSH alias experiment_zhixu”, and `r1/scripts/htcondor/trackp_p4/p4_direct.py:3` repeats it, while the executed
  value `direct.ssh_alias` is `ada_server` (`trackp_ada_v1.json:179`). The unit record documents why (`ADA_HOST_FILL…:85-86`).
  This is a documentation mismatch only; no code reads the comment or the docstring. A follow-up commit may correct
  both.
- **MINOR m2 — two `venv` records with different Pythons.** `trackp_ada_v1.json:108-109` still carries the image env3
  path `/opt/r1/envs/trackp` and Python `3.12.15` (a pre-existing base field), while the native Ada venv is 3.12.10 in
  `direct.venv`. The runtime cannot confuse them: `p4_render_jdl.direct_host_values` uses `direct.venv` when
  `container_runtime == "venv"` (`p4_render_jdl.py:145-146`) and `ada_venv_config` enforces 3.12.10
  (`p4_lib.py:552`). The record explains the split (`ADA_HOST_FILL…:55`). Non-blocking.

The distinction between the `--check-config` digest (`098123e3…`) and the file sha256 (`bb0c7251…`) is stated
correctly in the record and is not a finding.

## Verdict

Verdict: ACCEPTED

The fill is the reviewed hook's exact output over the base template, the 26 values and the file sha match the record,
the host facts are confirmed, the tests keep their enforcement and pass at the claimed counts, and no probe or evidence
run has occurred. The probe may proceed after the coordinator merges `compute-p4-ada-hostconfig-20261127`.
