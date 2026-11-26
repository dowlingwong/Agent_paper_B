# Independent review — G.1b official seven-node TASL assembly (R1-G1B-JOIN A) and floor-by-node (25 November 2026)

**Verdict: ACCEPTED** — the ENGINEERING_ONLY seven-node assembly (`g1b_tasl_assembly/1`) of run
`g1b-tasl-20261121-b`, its `g1b_tasl_summary/1`, the `g1b_tasl_crosscheck_gate/1` record and the
`g1b_tasl_floor_by_node/1` (eight nodes incl. autoresearch) are accepted, with the MINOR corrections m1–m6 and the
conditions c1–c6 before G5 use. **No BLOCKING, no MAJOR.** I re-derived the assembled rows from the seven sealed
attempts, recomputed every D21 / mean P(wrong) / sigma / determinism value independently, recomputed the three
cross-check comparisons from the sealed `out.tar` files, and matched every record to the host byte-for-byte. The
difference from the provisional assembly is assembly provenance only, and the two paper-commit code versions differ
only outside the seven-node measurement path.

**Reviewer and method.** Fresh independent reviewer (`g1b-seven-assembly-reviewer`), delegated by the lead; no
involvement in the runs, cross-check, assembly, memo or floor. Read-only: the only file written by this review is this
review; no run/edit/commit/push/delete of any repository or host artefact, no HTCondor, no job/test/pipeline executed.
TASL-2 was read with `ssh -o BatchMode=yes portal_zhixu` and TASL-7 with `ssh -o BatchMode=yes tasl7`, using read-only
commands only (`ls`, `stat`, `cat`, `sha256sum`, `sha256sum -c`, `git rev-parse/status`, and host `python3` that only
read files — `out.tar` members were read into memory, nothing was written, no lock was taken). Local checks used
`git show <commit>:<path>` on objects already present; the D21 recomputation ran only on copies fetched to `/tmp`.
Host clock TASL-2: 2026-11-25T03:16 PST = 11:16Z.

**Object under review.**

- Memo `docs/r1/reports/tasl_chain_20261122/G1B_TASL_SEVEN_NODE_ASSEMBLY_20261125.md` — 2,844 B, 39 lines, sha256
  `d88eeea322a20c2b21dcd49dcb334123f30f3a0a1a9dad2dd8f561c4e0e62885`; untracked (`??`) in `ops-tasl-20261116`
  (HEAD `9253192f`), not on `origin/main` `5d4f1b09`.
- Records dir `docs/r1/reports/tasl_chain_20261122/G1B_TASL_SEVEN_NODE_ASSEMBLY_20261125/` — 5 files; local
  `shasum -a 256 -c SHA256SUMS` rc 0: `ASSEMBLY.json` 9,888 B `e4056710beff92b4e0628372831632c9a54d070be1c41497e990eb45924236dd`;
  `crosscheck_gate.json` 1,136 B `00ee68c28aa2f9fcebd0b858d85df21a1baa3175b492eb5bfef0b074b073c8e2`;
  `summary.json` 17,287 B `945abc0a7ced28a7ffa27905c3282b7ad4b25ed6f9c49de01ca7c595491e7a67`;
  `floor_by_node.json` 3,320 B `6fb8f9908b54ba9804eebcd7d6a5fb2b264155de1ecd8e9c520066ea1db6667d`;
  `SHA256SUMS` 331 B `c9f24811e54eeb6168c2ab90b972a63f91da0d7e5b69d8ce3d2538805c0600f8`.
- Host (TASL-2) `/home/dowling/r1_tracks/t1_tasl/joined_seven_official_20261125/` — the same four files with the same
  sha256 (byte-identical host↔Mac), plus `edits.json` (7,704 B, `9451ecea…`) and `runs.jsonl` (2,206,955 B,
  `1f56c068…`), and `_unpacked_060aac91ba45/` (3 nodes) + `_unpacked_7ff3c95b963a/` (4 nodes).
- Host captures `/home/dowling/r1_tracks/t1_tasl/logs/`: `official_join.out` 11,066 B (parses to `ASSEMBLY.json` plus
  `crosscheck_gate.json` exactly), `official_summary.out` 17,287 B (byte-identical to `summary.json`),
  `official_floor.out` 3,320 B (byte-identical to `floor_by_node.json`), `official_floor.err` 0 B.
- Host assembly checkout `/home/dowling/r1_tracks/t1_tasl/paper_join2` at HEAD = `origin/main` = `5d4f1b09…`, clean;
  `g1b_tasl_join.py` `e6754b30…`, `g1b_tasl.py` `aa6d1db0…`, `g1b_crosscheck.py` `67c45c9d…`, re-issued spec
  `7ff3c95b…`, cross-check spec `a9e6b463…` — all equal to `main` `5d4f1b09`.
- Authority: PLAN row R1-G1B-JOIN (present once on `origin/main` `5d4f1b09`), chain report `TASL_CHAIN_20261122` §4,
  R1-T1-DATA-MANIFEST, R1-T1-TASL-ENV, R1-T1-D21-SCOPE, R1-G5-AUDIT-TWO-CARDS.

## 1. The assemble rule and its inputs — verified

### 1.1 The two specs, the paper commits and the code difference

- **Predecessor.** `git show 985dd45d:sweep2/t1_tasl/g1b_tasl_spec.json` has raw sha256 `060aac91…` — equal to the
  signed first note's `spec_sha256` on `main` (note `approved: true`) and to `spec_sha256` in the three TASL-2 job
  records; its `paper.commit` `10fd3343…` equals the first note's `paper_commit`.
- **Re-issued spec.** `5d4f1b09:sweep2/t1_tasl/g1b_tasl_spec.json` has raw sha256 `7ff3c95b…` — equal to
  `ASSEMBLY.join.spec_sha256`, `crosscheck_gate.g1b_spec_sha256`, and the cross-check spec's `g1b_spec.sha256`; its
  `paper.commit` is `3c3f822a…`. Its canonical sha256 `sha256(json.dumps(spec, sort_keys=True))` is
  `b24c89ee…` = `ASSEMBLY.spec_json_sha256` (recomputed).
- **Difference.** Recomputing the JSON diff gives exactly `nodes.3.data_manifest_sha256`,
  `nodes.4.data_manifest_sha256`, `paper.commit`; corrected nodes `{mlgym_cifar10, mlgym_fmnist}`, unchanged
  `{mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv, mlgym_breakout_minatar, mlgym_houseprice}`; same run id and node order.
  This equals `ASSEMBLY.join.difference` exactly. Both specs' `harness.commit` is `c025f89a…`.
- **Code versions.** Over the join's `JOB_CODE_PATHS`, `git diff 10fd3343 3c3f822a` names exactly the three recorded
  files — `sweep2/g1b/env/ar-cond7a.freeze.txt`, `sweep2/t1_tasl/g1b_tasl.py`, `sweep2/t1_tasl/t1_tasl_node.sh` — and
  nothing under `sweep2/g1b/g1b_lib.py`, `r1/noise` or `r1/harness.py`. I read the `g1b_tasl.py` diff: the added code
  is the AR spec kind/validation/summary/launch branch and the related refactors; for a non-AR spec `spec_hosts` is
  `HOSTS`, the launch rows and order are unchanged, `run_node_job` only gains an `if is_ar(spec)` record update, and
  `assemble`/`summarise` keep the seven-node schema and path. The AR spec-support review (ACCEPTED at `6617d8cb`,
  confirmed `740c48f3`) verified the same, and
  `r1/tests/test_t1_tasl_chain.py::test_the_job_code_difference_of_the_two_paper_commits` codifies this allowlist.
  `g1b_tasl.py`, `g1b_lib.py`, `r1/noise` and `r1/harness.py` are identical between `3c3f822a` and `5d4f1b09`
  (empty diff), so the assembly/summarise code is the code the four newer attempts ran.

### 1.2 Seven sealed attempts, exactly

Enumerating both hosts' `sealed_g1b/g1b-tasl-20261121-b/` trees gives exactly seven attempts, one per node, no
`attempt-2`; each dir has `job_record.json`, `SEAL_RECEIPT.json`, `SHA256SUMS`, `node.log`, `out.tar`, and
`sha256sum -c SHA256SUMS` returned rc 0 for all seven. Receipts bind the job-record sha, run id, node, host and
attempt, with `stop: null`. The TASL-2 working copies of the three TASL-7 attempts are byte-identical to the TASL-7
originals (job record, `out.tar` and `SHA256SUMS` sha256 equal; TASL-7 `sha256sum -c` also rc 0), so the assembly used
authentic TASL-7 attempts.

| node | host / attempt | spec | job record sha256 | out.tar sha256 | rows | wall | hours (per-job wall; houseprice CPU) |
|---|---|---|---|---|---|---|---|
| mlab_ogbn_arxiv | TASL-2 / 1 | 060aac91 | `45583b27…` | `04f2d0c7…` | 460 | 3,335 s | 0.9264 |
| mlab_imdb | TASL-2 / 1 | 060aac91 | `4468021a…` | `0faf572d…` | 460 | 16,601 s | 4.6114 |
| mlgym_houseprice | TASL-2 / 1 | 060aac91 | `15b7beea…` | `2588cd30…` | 460 | 2,317 s | 0.6436 |
| mlgym_fmnist | TASL-2 / 3 | 7ff3c95b | `5476148a…` | `a180c6e5…` | 460 | 5,438 s | 1.5106 |
| mlab_cifar10 | TASL-7 / 1 | 7ff3c95b | `d07eb4f2…` | `eb30fb24…` | 460 | 2,815 s | 0.7819 |
| mlgym_cifar10 | TASL-7 / 1 | 7ff3c95b | `1663b2ba…` | `f886b59b…` | 460 | 5,411 s | 1.5031 |
| mlgym_breakout_minatar | TASL-7 / 1 | 7ff3c95b | `c8a8d858…` | `156ee4d6…` | 460 | 16,920 s | 4.7000 |

All seven job records are `ENGINEERING_ONLY`, `run_id g1b-tasl-20261121-b`, harness `c025f89a…`, `stop` and
`stop_class` `null`, host/GPU as in `ASSEMBLY.jobs`; the sealed paths, attempts, job-record shas, spec shas,
GPU UUIDs/devices and `timing[]` arrays match `ASSEMBLY.jobs` on every one of the 17 fields I compared (0 mismatch).
**No corrected node sits under the old spec** (fmnist attempt-3 and mlgym_cifar10 carry `7ff3c95b`; the three
`060aac91` attempts are the non-corrected TASL-2 nodes, which the code also enforces), and **no third spec** appears:
only `060aac91` and `7ff3c95b` occur among the seven job records, the join block and the gate.

The unsealed `mlgym_fmnist` attempt-1/2 in the runs tree are `stop_class: infrastructure` under `060aac91` (the data-
manifest mismatch), with job-record shas `8c2fe155…` and `571b5403…`; both are listed with their paths and stop
strings in `ASSEMBLY.join.unsealed_attempts_not_used` exactly as on the host.

### 1.3 The three step-2 preassembly verdicts and the cross-check gate

- The three verdict files are committed on `origin/main` `5d4f1b09` with sha256 `9403653f…` (mlab_cifar10),
  `503fc731…` (mlgym_breakout_minatar), `fea9ca97…` (mlgym_cifar10); the worktree copies are byte-identical to the
  main blobs. Each reads `g1b_tasl_crosscheck_verdict/1`, `mode: preassembly`, `verdict: PASS`, `complete: true`,
  `reason: null`, `on_stop: null`, `crosscheck_run_id g1b-tasl-20261121-b-xc2`, `g1b_spec_sha256 7ff3c95b…`.
- Each verdict's TASL-7 side cites the job-record sha of the seven-node TASL-7 attempt
  (`d07eb4f2…`, `c8a8d858…`, `1663b2ba…`) and its TASL-2 side cites the cross-check TASL-2 attempt job record
  (`c863ea61…`, `13409bef…`, `f30edd05…`); those TASL-2 attempts exist on TASL-2, carry harness `c025f89a…`, run id
  `g1b-tasl-20261121-b-xc2-TASL-2` and the derived cross-check spec shas `af30beb0…`, `6a50c785…`, `73254656…`,
  which I recomputed from the signed re-issued spec and the cross-check spec and they match.
- I recomputed the three preassembly comparisons from the actual sealed `out.tar` default parts: 10
  `(config, condition)` outcomes per side, deterministic on both sides, every outcome identical TASL-7↔TASL-2, and
  the committed verdict `rows` match the recomputed outcomes exactly (0 mismatch on all three nodes). The gate's
  comparison is therefore the comparison of the attempts given.
- `crosscheck_gate.json` has `schema g1b_tasl_crosscheck_gate/1`, `rule R1-T1-TASL-ENV`,
  `crosscheck_run_id g1b-tasl-20261121-b-xc2`, `g1b_spec_sha256 7ff3c95b…`, exactly the three nodes (verdict paths as
  above), `assembly_json_sha256 e4056710…` = sha256(`ASSEMBLY.json`) and `runs_jsonl_sha256 1f56c068…` =
  sha256(`runs.jsonl`). Schema and assembly sha match as required.

### 1.4 The assembly records are a faithful function of the sealed attempts

- **Reconstruction.** From the seven sealed `out.tar` files, in the assembly's job order, I rebuilt `runs.jsonl`
  exactly as `g1b_tasl_join.assemble_join` does (job order `060aac91` group then `7ff3c95b` group; per-row
  `json.dumps(sort_keys=True)`): 3,220 rows = 7 × 460, every row's node correct and every `isolation` gate field
  valid (0 violations). The reconstruction is **byte-identical** to the official `runs.jsonl` (sha256 `1f56c068…`,
  2,206,955 B), which is also `ASSEMBLY.runs_sha256` and `crosscheck_gate.runs_jsonl_sha256`. The rebuilt `edits.json`
  is the official one (`9451ecea…`, 7,704 B, 7 nodes).
- **ASSEMBLY.jobs.** Seven entries, `g1b_tasl_assembly/1`, run id `g1b-tasl-20261121-b`, `spec_json_sha256 b24c89ee…`,
  `runs_sha256 1f56c068…`; per-node node/host/attempt/sealed path/`stop_class: null`/GPU UUID/device/`timing`/spec
  sha/job-record sha equal the host records; `join` block as in §1.1 (both paper commits, the code-difference list,
  the node split, the two unsealed infrastructure attempts).
- **summary.json.** `assembly_sha256 e4056710…`, `ENGINEERING_ONLY`, 7 nodes, hosts/devices/`timing_4090` equal to
  the assembly. I recomputed every verdict from `runs.jsonl` with the pinned `r1.noise.e1_report` rule and
  `g1b_lib`'s independent per-edit statistics: **0 mismatches** on all seven nodes for `qualifies_D21`,
  `mean_p_wrong_material`, `sigma_joint`/`sigma_train`/`sigma_split`, `n_material`, `paired_joint_n`, `divergent`
  rows/by-config, the `determinism` structure and `median_wall_seconds`. Screening funnel `measured 7, qualified 2,
  failed_determinism 0`; the two qualifying nodes are `mlgym_breakout_minatar` and `mlgym_houseprice`.

| node | D21 | mean P(wrong) | sigma_joint | determinism | memo match |
|---|---|---|---|---|---|
| mlab_cifar10 | false | 0.010050537868361728 | 0.018578266872881336 | true | exact |
| mlgym_cifar10 | false | 7.2686301422209e-13 | 0.01037016941969144 | true | exact |
| mlgym_breakout_minatar | true | 0.17969980001800998 | 7.7516153743556515 | true | exact |
| mlab_imdb | false | 0.045823359403353664 | 0.0064248941133544036 | true | exact |
| mlab_ogbn_arxiv | false | 0.0044048932945487534 | 0.06196111851205978 | true | exact |
| mlgym_fmnist | false | 0.0 | 0.0040357128669948296 | true | exact |
| mlgym_houseprice | true | 0.31458651509587915 | 12042.88012945658 | true | exact |

Every value above is float-equal to the memo table and to the provisional summary's verdict object; the only
provisional↔official summary difference is `assembly_sha256` (§1.6).

### 1.5 Floor-by-node (eight nodes incl. autoresearch)

- `g1b_tasl_floor_by_node/1`; `split_file_sha256 b5967dd7…` = sha256 of `main`'s
  `r1/c3/splits/c3_p3_split_v1.json`; the eight node keys are exactly the split file's `t1.nodes`
  (`autoresearch_fixedtokens` + the seven), no overlap.
- I re-derived the record that `noise_floor_by_node` produces from the two summaries (the seven-node summary bytes
  and the AR summary bytes, both fetched from the host) and compared it field by field: it equals the official record
  for every node. The seven entries cite
  `/home/dowling/r1_tracks/t1_tasl/joined_seven_official_20261125/summary.json` sha `945abc0a…`, run
  `g1b-tasl-20261121-b`, schema `g1b_tasl_summary/1`, the summary's `qualifies_D21`, assembly `e4056710…`; the AR
  entry cites `/home/dowling/r1_tracks/t1_tasl/ar_assembly_20261124/summary.json` sha `186c51e1…`, run
  `g1b-ar-tasl-20261122-a`, schema `g1b_tasl_ar_summary/1`, `qualifies_D21: false`, assembly `a2d26e1e…`. The seven
  summary sits beside the gate whose `assembly_json_sha256` equals its `assembly_sha256` (the floor code's own check).
- AR summary (host, byte-identical to what the floor hashes): `ENGINEERING_ONLY`, D21 **false**, `mean_p_wrong_material
  0.05798512674928419` (memo's 0.057985), `sigma_joint 0.00679369389686993`, determinism true, 4 material edits,
  screening `1 measured / 0 qualified / 0 failed`; the AR job wall is 104,824 s = **29.1178 h**, `stop: null`,
  `sha256sum -c` rc 0. The floor is a provenance join: the mean/sigma/determinism values live in the two referenced
  summaries (both verified), while the floor itself records the source hash, run/schema and the D21 flag.

### 1.6 Official vs provisional — provenance only

The provisional host tree `joined_seven_provisional_20261125/` has `edits.json 9451ecea…` and `runs.jsonl 1f56c068…`
identical to the official, and `summary.json 67a53207…`. The exact diffs are: `ASSEMBLY.json` only in
`join.unsealed_attempts_not_used` (official lists the two fmnist infrastructure attempts; provisional lists none;
`b2104243…` vs `e4056710…`); `summary.json` only in `assembly_sha256`; the official adds `crosscheck_gate.json` and
`floor_by_node.json`, which the provisional has not. All seven per-node measured values are identical, so the
difference is assembly provenance only, as claimed — there is no measured-value change between the ungated and gated
runs.

### 1.7 Cap and STOP

- Seven-node spec `caps.max_total_gpu_hours = 100`. Measured seven-node GPU hours from the job records: six GPU nodes
  = 50,520 s = **14.0333 h** (the memo's 14.0334 is the sum of the four-place rounded rows — m2); ≤ 100.
- AR: 29.1178 h ≤ 100; AR spec `caps.max_total_gpu_hours = 100` (`crosscheck_gpu_hours 2.1`), harness pin `2d09f9a9…`.
- **No STOP.** Seven job records `stop`/`stop_class` null; three step-2 verdicts PASS with `reason: null`;
  `summary.json` has 0 determinism failures; the AR summary likewise; `ASSEMBLY`/`summary`/`gate`/`floor` contain no
  STOP other than the two disclosed unsealed infrastructure stops. The two D21-qualifying nodes are reported, not a
  STOP: under R1-T1-D21-SCOPE D21 does not select T1 nodes.

## 2. Findings

**No BLOCKING. No MAJOR.** The six points below are record/precision corrections; none changes a measured value, a
seal, a hash, a qualification flag or the cap accounting.

**m1 — The memo's CPU-hours label is wrong by the core count.** The `mlgym_houseprice` row reads "0.6436 CPU
core-h", but 0.6436 h is the job's CPU **wall** time (2,317 s; affinity 8–15, 8 CPUs). That is 5.1489 core-hours if
core-hours are meant (as the earlier TASL-2 result memo reported). The value is correct as per-job wall hours,
consistent with the GPU nodes' GPU-hours; the label should read "0.6436 CPU wall-h (5.1489 core-h, 8 CPUs)".

**m2 — The seven-node GPU total is the sum of the rounded rows.** The exact sum of the six GPU nodes' job walls is
50,520 s = 14.03333 h → 14.0333 GPU-h; the memo's 14.0334 is the sum of the table's four-place values. State which
convention is used (no cap impact, 100 GPU-h).

**m3 — "The official and provisional assemblies differ only in ASSEMBLY.json" is imprecise, and the provisional
artefacts are not named.** Verified: the difference is `ASSEMBLY.json` (unsealed list only) + `summary.json`
(`assembly_sha256` only) + the two added files (`crosscheck_gate.json`, `floor_by_node.json`); `edits.json` and
`runs.jsonl` are byte-identical. The provisional tree and its hashes (ASSEMBLY `b2104243…`, summary `67a53207…`) are
not recorded in the memo or records set, so the comparison cannot be reproduced from the published records. Name the
provisional tree/hashes (or drop the sentence).

**m4 — The join module's docstring understates the recorded code difference.** It says the reviewed difference is
"only the autoresearch-only branches of `g1b_tasl.py` and the cross-check kind of `t1_tasl_node.sh`"; the recorded
`job_code_files_differing` also contains `sweep2/g1b/env/ar-cond7a.freeze.txt` (the AR environment's freeze file,
unused by the seven-node jobs). The chain report §4 and the chain test include it; the docstring should match.

**m5 — The memo's "rc 0" for the three commands has no exit-code capture.** The host has the stdout captures
(`official_join.out`, `official_summary.out`, `official_floor.out`) and an empty `official_floor.err`, and I verified
they reproduce `ASSEMBLY.json`+gate, `summary.json` and `floor_by_node.json` exactly, so the runs succeeded; but the
records dir carries no rc artefact and the memo does not name the host logs. Add a captures/host-log sentence with
paths and shas (as other result memos do), or drop the literal rc claim.

**m6 — The memo does not state the job-code-difference check, although it is the central validity condition for
joining two code versions.** `ASSEMBLY.join.job_code_files_differing` is exactly the reviewed/tested allowlist and
`g1b_lib.py`/`r1/noise`/`r1/harness.py` are unchanged, which I verified; the PASS memo should say so explicitly
(one sentence), because a G5 consumer otherwise has to re-derive it. Note also that the official summary was produced
with `g1b_tasl.py summarise`, not the gate-checking `g1b_crosscheck.py summarise` that the join module's docstring
recommends; the gate had already been enforced by `assemble_gated_join` and the floor-by-node command re-checked the
gate against `summary.assembly_sha256`, so there is no data effect — record this in the memo for completeness.

## 3. Conditions before G5 use

1. **Publish the records and the review on `main`.** The memo (sha `d88eeea3…`), the records dir (4 records +
   `SHA256SUMS c9f24811…`) and this review are currently untracked in `ops-tasl-20261116` (HEAD `9253192f`) and not on
   `origin/main`; the host tree is the only holder of the assembled `runs.jsonl` (sha `1f56c068…`) and `edits.json`
   (sha `9451ecea…`). Publish with hashes and keep the host tree, or also publish the two assembled files.
2. **Apply m1–m3 (and record m4–m6) before or with publication**, or publish an erratum; none changes a result.
3. **Cite this review, the memo, the records shas and the floor record in the G5 note/authorization** as the
   independent review that admitted the seven-node floor. Report each node's D21 value from the two summaries in the
   screening funnel (R1-T1-D21-SCOPE / R1-BX-D12); do not select on D21.
4. **Use the official records only.** Mark `joined_seven_provisional_20261125/` superseded and do not cite it: it has
   no cross-check gate and is not the admitted assembly.
5. **Before any TASL-7 audit chunk:** the three TASL-7 nodes are covered by the xc2 PASS (step-1 verdicts + step-2
   preassembly verdicts); the five nodes measured only on TASL-2 need the short cross-check under the reviewed
   `g1b_crosscheck.py` before their first TASL-7 audit chunk, and the G5 note must cite the TASL-7 harness-isolation
   host-check record (R1-G5-AUDIT-TWO-CARDS).
6. **Keep AR separate and run the join tests before reuse.** The AR floor joins by node only and is never merged into
   the seven-node assembly (G5-PIN B; its own run/schema/harness/environment). If `g1b_tasl_join.py` is to be used for
   any further assembly (e.g. R1-T1-NODE-EXPANSION joins), run its test suite (`r1/tests/test_t1_tasl_chain.py`) and
   record an independent code review; this read-only review verified the module's logic as exercised but did not
   execute the tests.

## 4. What this review does not establish

- It is not a G5 authorization, does not schedule G5, does not select or rank nodes, and reads no label/evaluation
  data; the run is ENGINEERING_ONLY (job records `label: ENGINEERING_ONLY`, notes `labels_read: none`).
- It does not re-verify the harness-isolation host checks, the census erratum, the U2 results or the cross-check step-1
  records beyond citing their accepted reviews; it does not re-run the cross-check jobs, the join, the summariser or
  the tests.
- It does not accept the provisional assembly, and it does not cover any later assembly or any node outside the eight.
