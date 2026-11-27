# Verdict: ACCEPTED
Task: `compute/20261127-29` (with `compute/20261127-33` item 2)
Reviewed tip: `compute-p5-ada-smoke-e0-20261127` @ `28e451ea12d948c3ca542de2e6747952ed43dd3d` (initial review at `eab09bc9…`, re-checks at `dd6a529b…` and `28e451ea…`; base `origin/main` `1afa7d62…`)

Independent review of `docs/r1/reports/trackp_p5_ada_20261127/` at the tip above. I did not write the record.
All work was read-only: worktrees at `eab09bc9` (initial review), `dd6a529b` and `28e451ea` (re-checks), local
hashing/re-computation, and read-only `ssh ada_server` hashing/cat of the receipts named by the record. No GPU
job was launched, no file was written on Ada, and no label was read.

The central finding is correct: the staged Track P smoke **passes** on the RTX 6000 Ada, and the E0 equivalence
check **does not meet** its pre-declared criteria and is correctly reported as a **STOP**, not a PASS. The
minors are packaging/disclosure defects, not a defect in the result.

## Addendum — re-check at `dd6a529b` (27 Nov 2026)

I re-checked only the two required fixes and the corrected wording against the initial review at `eab09bc9`.
Read-only; no GPU job, no write on Ada, no label read.

**Closed.**

- `smoke_report.json` is committed; sha256 `6a3c49055c72a5e2c3026bd5702c9cc016ec515024cd2bb298ae3c150b6a5547`
  equals the record and the host receipt.
- `e0b_report.json` (`46f8dbb2a63973920129bbedd7957694310b79df73394aefe9f55f96cd6c5597`) and
  `e0c_report.json` (`0f71111589e32a7e2b9515b3606454fc458e12c6e59950e413ceeba7e9c27073`) are committed and
  match the host reports.
- `e0e_report.json` and `e0e_manifest.json` are the renamed originals, unchanged:
  `7df24070ee8a3a0838b3e2b3e71bf264fcbc6d8fa5a531fac2d28c16d8b9e817` and
  `b4f918948f31b2ffb40c7428a25a16dc893f75154ebd4024e5a725d7df0197bb`.
- `e0d` is disclosed as a third, non-comparison scene ended at step 0 with no report. The step-0 state is what
  the host shows; the stated reason ("the wrapper was corrected to `--stage final`") is not recorded in
  `e0d.log` or `e0d/`, so it is plausible but not independently evidenced. That does not affect the comparison.
- The drift paragraph now names R1-E0-HEADFIT, the AdamW-to-L-BFGS head-fit change and `471f93f7`/`52b527b9`,
  and correctly says the reference starts LoRA from the fitted head while `c80f83bc` restores the fresh head.
  This is the specific, checkable cause; the drift claim is no longer under-specified.
- The memory wording is corrected: "0 MiB foreign-process memory; card total 5–8 MiB" matches the lease
  (`other_processes.memory_mib = 0`) and the captures (5 MiB start, 8 MiB end).

**Still open at this tip (required), closed at `28e451ea` below.** `smoke_lease.jsonl` was **not in the branch**
at `dd6a529b`. The tree there has 11 files
under the record directory and none is the lease:

```
git ls-tree -r --name-only dd6a529b docs/r1/reports/trackp_p5_ada_20261127/
git cat-file -e dd6a529b:docs/r1/reports/trackp_p5_ada_20261127/smoke_lease.jsonl
fatal: path '.../smoke_lease.jsonl' does not exist in 'dd6a529b'
```

The record at that tip nevertheless cited `smoke_lease.jsonl` at lines 20 and 31 and listed it under "Captured
files (this directory)" at line 81. The lease hash
`69d0d2d03b83f63de043d1132baaeddb391c24ad00818b29cac511dc5c5f52e2` already matched the 515-byte host file
`/data1/zli538/paperb_p4_20261127/p5_20261127_b/smoke/lease.jsonl`, so the evidence was genuine and the
recorded hash right; the branch simply did not carry the file, which made the reference dangling. At that tip
the required fix was to commit the lease (hash `69d0d2d0…`) or remove/repoint the three citations, so M1 was
only half closed.

At `dd6a529b` one required artifact was still missing, so the verdict at that tip remained **ACCEPTED WITH
MINORS**, with M1 open. The final re-check below closes it.

### Final re-check at `28e451ea` (27 Nov 2026)

`smoke_lease.jsonl` is now in the branch. The `*.jsonl` ignore rule had kept it out; it was force-added in this
tip. Verified read-only:

```
git ls-remote origin refs/heads/compute-p5-ada-smoke-e0-20261127
28e451ea12d948c3ca542de2e6747952ed43dd3d
git cat-file -e 28e451ea:docs/r1/reports/trackp_p5_ada_20261127/smoke_lease.jsonl    # present
git show 28e451ea:docs/r1/reports/trackp_p5_ada_20261127/smoke_lease.jsonl | shasum -a 256
69d0d2d03b83f63de043d1132baaeddb391c24ad00818b29cac511dc5c5f52e2
git diff --name-status dd6a529b 28e451ea
A  docs/r1/reports/trackp_p5_ada_20261127/smoke_lease.jsonl
```

The hash matches the record and the 515-byte host file. The lease content is the same start/end pair already
embedded in `smoke_report.json`: card 0, UUID `GPU-9be33fd1-8eeb-497d-772a-87362d6720be`,
`other_processes {count: 0, memory_mib: 0}` at both samples.

No citation is dangling now. I extracted every backticked `.json`/`.jsonl`/`.txt`/`.md`/`.py` filename from the
record and checked each against the tree at `28e451ea`; all 12 resolve:

```
comparison_e0e.json  e0_config_ref.json  e0b_report.json  e0c_report.json
e0e_manifest.json    e0e_report.json     gpu_after.txt    gpu_before.txt
p5_compare_ada.py    p5_reference.json   smoke_lease.jsonl smoke_report.json
```

The tree has 13 files (the record plus the 12 cited files). **M1 is closed.** The scientific result is
unchanged and reconfirmed: the smoke PASS is real and the E0 equivalence is a STOP. The optional "only" caveat
about the changed config comment was not taken; it is cosmetic and I do not ask for it again.

## 1. Hashes and the E0 data manifest

Every sha256 the record claims for a file that is in the branch matches. Command (in the detached worktree at
`eab09bc9`):

```
cd docs/r1/reports/trackp_p5_ada_20261127 && shasum -a 256 *
```

| File | Computed sha256 | Record claim | Match |
|---|---|---|---|
| `e0e_report.json` (was `report.json`) | `7df24070ee8a3a0838b3e2b3e71bf264fcbc6d8fa5a531fac2d28c16d8b9e817` | `7df24070…` | yes |
| `comparison_e0e.json` | `7d3b9f8721e586615ba9992d0cbc3c56a20f52b11cb534aebb021e390aa5a5d4` | `7d3b9f87…` | yes |
| `e0_config_ref.json` | `9773547dc286f638792b53b06cc7133d61209c2d9e92cdfd4982a062c1a2c054` | `9773547d…` | yes |
| `p5_reference.json` | `bc1c9182a7f49f19bd0d276176de2bd31612e3b07ae8cd670bc5c78822d33afc` | `bc1c9182…` | yes |
| `e0e_manifest.json` (was `manifest.json`) | `b4f918948f31b2ffb40c7428a25a16dc893f75154ebd4024e5a725d7df0197bb` | `b4f91894…` at `dd6a529b` | yes |
| `p5_compare_ada.py` | `da5354ed4ce1fdd3c92e9fa846b274901f633d886845c08fca6abfde0a5e9216` | not claimed | — |
| `gpu_before.txt` | `3ba812533d0a6abf39cb08d9a3e20cb363fedc2e8332790c731b53ea9174076e` | not claimed | — |
| `gpu_after.txt` | `d8d436d3796b8e1d16d15c10cbec939d8dc0dc7c63f27fcb3aa8a0e59874841f` | not claimed | — |

The record's config claim for the smoke also matches the repository file:

```
shasum -a 256 r1/scripts/configs/trackp_ada_v1.json
bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908
```

At `eab09bc9` the two hashes that could not be checked from the branch (the smoke report and the smoke lease)
matched the host files; at `dd6a529b` the smoke report was committed, and at `28e451ea` the lease is too:

```
ssh ada_server 'sha256sum /data1/zli538/paperb_p4_20261127/p5_20261127_b/smoke/*'
6a3c49055c72a5e2c3026bd5702c9cc016ec515024cd2bb298ae3c150b6a5547  .../smoke/report.json
69d0d2d03b83f63de043d1132baaeddb391c24ad00818b29cac511dc5c5f52e2  .../smoke/lease.jsonl
```

**Data manifest.** `manifest.json` has
`"data_manifest_sha256": "b963be2dd378241e0b0689907d4051bfa62922a8e4968aa40061ed7ef275bfef"`. The same digest is
in `docs/r1/reports/trackp_h200_20261118/stages/e0_h200/reference_manifest.json` and in the TASL-7 run manifest
(`docs/r1/reports/tasl7_equivalence_20261026/run/manifest.json`). `p5_reference.json` **does not itself carry a
manifest hash**; it is a report, not a manifest. The equality therefore holds against the reference manifest
(`reference_manifest.json`, which accompanies the byte-identical reference report), not literally inside
`p5_reference.json`.

`p5_reference.json` is byte-identical to the H200 reference (`cmp` returned identical;
`bc1c9182…` both). That reference report's manifest records paper `8e13e77`, harness `897d83c8`, and the same
`b963be2d…` data digest, so the comparator's stated provenance is sound.

Clarification, not a defect: the E0e manifest's `"config_sha256": "754f6854…"` is not the file-byte hash of
`e0_config_ref.json` (`9773547d…`). It is `config_digest(cfg) = sha256(json.dumps(cfg, sort_keys=True))`; I
recomputed `754f6854…` from the committed config, so both values are internally consistent. The record quotes
the file-byte hash, which is the more informative one.

## 2. Smoke evidence

Read-only command:

```
ssh ada_server 'cat .../p5_20261127_b/smoke/report.json; cat .../p5_20261127_b/smoke/lease.jsonl'
```

- `pass: true`; `device: "NVIDIA RTX 6000 Ada Generation"`; `capability: [8, 9]`.
- Four bound kernels: `causal_conv1d_fn`, `causal_conv1d_update`,
  `torch_chunk_gated_delta_rule`, `torch_recurrent_gated_delta_rule` — the two `causal_conv1d` and the two
  `fla.gated_delta_rule` bindings the record names.
- `causal_conv1d 1.7.0`, `fla 0.5.2`, torch `2.6.0+cu124`, transformers `5.19.0`, CUDA runtime `12.4`.
- `bf16_matmul.rel_err_vs_fp32 = 0.0028721054550260305` (record: 0.00287); both DeltaNet forward checks
  (`float32`, `bfloat16`) `pass: true`.
- Lease has one start and one end event, both `gpu_index: 0`, UUID
  `GPU-9be33fd1-8eeb-497d-772a-87362d6720be`, `other_processes: {count: 0, memory_mib: 0}`. The lease is
  therefore on card 0 with no foreign process. The E0e manifest's own `gpu_lease` has the same card/UUID and
  `0/0` foreign-process samples at 20:33:06Z and 21:11:15Z.
- The record's model digests are correct for the staged local tree:
  `.../paper_c80f83bc/models/qwen3.5-0.8b-base/config.json` = `b90b86f3…` and
  `model.safetensors-00001-of-00001.safetensors` = `c2b1e5a1…`. `git -C .../harness rev-parse HEAD` =
  `897d83c8efa364ec2fdd37288241cc42e01d7274`; the paper checkout is `c80f83bc` with only untracked `models/`.

One wording point: the record says the card was "empty at start and end (0 foreign processes, 0 MiB)". The
committed captures show **5 MiB** at start and **8 MiB** at end on card 0; the `0 MiB` is the lease's
*foreign-process* memory, which is the meaningful figure. "Empty" is acceptable for scheduling; "0 MiB" should
be read as foreign-process memory, not total device use.

## 3. The comparator re-run

Command (from the worktree root):

```
python3 docs/r1/reports/trackp_p5_ada_20261127/p5_compare_ada.py \
  docs/r1/reports/trackp_p5_ada_20261127/p5_reference.json \
  docs/r1/reports/trackp_p5_ada_20261127/e0e_report.json
```

At `eab09bc9` the same E0e report was named `report.json`; the bytes and hash are identical. Exit status
**1**; output `equivalent: false`. The three pre-declared criteria:

| Metric | Reference | Ada | Delta | Tolerance | Pass |
|---|---:|---:|---:|---:|---|
| `width_slope_vs_label` | 0.9134840344314319 | 0.9029562469607993 | −0.010527787470632544 | 0.05 abs | yes |
| `mean_slope` | 1.019259573471914 | 1.0141623146693686 | −0.0050972588025455234 | 0.05 abs | yes |
| `rps` | 1.9400102792893227e-4 | 1.4383536969300546e-4 | rel. 0.2585844970589734 | 0.10 rel | **no** |

This is exactly the record's table: the two slopes pass, RPS is 25.86 % below the reference (record rounds to
25.9 %), and the run is not equivalent.

The comparator is not a relaxed rewrite. `diff -u` against
`docs/r1/reports/trackp_h200_20261118/stages/e0_h200/compare.py` shows label changes only (`portal`/`tasl7` →
`reference`/`ada`, plus two descriptive output keys); `ABS`, `REL`, the metric list and the pass logic are the
same. The tolerances are the ones fixed in the TASL-7 `PREDECLARATION.md` (0.05/0.05 abs, 10 % relative), so "pre-declared"
is accurate.

`e0e_report.json` has `pass: true` because `e0_pass_v2` checks the E0 engineering thresholds (width slope ≥ 0.6 and
its bootstrap lower bound > 0, mean slope ≥ 0.8). The record does not confuse that with equivalence: the title,
the summary and the STOP paragraph all say the equivalence is **not** met and that the phase-1 note may not cite
it. I confirm the STOP reading.

## 4. The code-drift claim

Command:

```
git diff --stat 8e13e77 c80f83bc -- r1/c3/train/ r1/scripts/trackp.py
```

18 files, +3,696/−165. The drift is not incidental: the E0 recipe itself changed between the reference and the
Ada run.

- `r1/c3/train/exam_run.py`: `fit_head_on_states` (AdamW, cosine schedule, ≤ `max_steps`, early stopping,
  best state restored) is replaced by `fit_head_lbfgs` (full-batch L-BFGS, CPU float64).
- The current `e0_v2` deep-copies the fresh belief head, runs the descriptive L-BFGS fit, records its test
  metrics, then does `model.heads["belief"].load_state_dict(fresh_head)` — **LoRA starts from the fresh head**.
  The `8e13e77` code leaves the fitted head in place, so its LoRA stage starts from the fitted head.
- The commits are in the reference's future: `471f93f7` "E0 thresholds and two-stage budget, L-BFGS head fit,
  control readout, exam rule v2" and `52b527b9` "head fit stays descriptive (LoRA starts from the fresh head)",
  both 26 Oct, after `8e13e77` (26 Oct 03:08 −0700). The repository documents this as R1-E0-HEADFIT.
- `r1/scripts/trackp.py`: `cmd_e0` gains the stage/budget split and passes `head_fit=args.stage == "final" and
  not args.hard`; at `8e13e77` it used `e0c["max_steps"]`/`e0c["patience"]` directly and always ran the old head
  fit. `exam_synthetic.e0_metrics_v2` gains the bootstrap interval fields (the compared `rps`, slopes and label
  ceiling are unchanged), and `e0_pass_v2` gains the lower-bound condition.

The base and adapter revisions and the data-manifest digest are identical between the two runs, so the changed
head-fit protocol is a sufficient identified explanation for a different head-fit block and a different LoRA
trajectory. **The record's claim is supported — in fact the diff establishes more than "consistent with code
drift": it shows a deliberate recipe change, so the E0 comparison at `c80f83bc` against an `8e13e77` reference
is not a controlled same-recipe comparison.** The record's sentence "the metric comparison cannot separate code
drift from a runtime difference" is defensible about the metric alone but understates what `git diff` settles.
This is not an overstatement and does not change the STOP. At `dd6a529b` the record names the change
(R1-E0-HEADFIT, `471f93f7`/`52b527b9`), so this point is closed.

I checked that `c80f83bc` is still the current code for these paths on the review base: `git diff c80f83bc
1afa7d62 -- r1/c3/train/ r1/scripts/trackp.py r1/scripts/configs/trackp_ada_v1.json` is empty. "Current code" is
accurate.

## 5. Non-comparison attempts and the config copy

Verified against the host reports:

| Scene | Report sha256 | Stage / budget | LoRA test RPS | Record |
|---|---|---|---:|---|
| `e0b` | `46f8dbb2a63973920129bbedd7957694310b79df73394aefe9f55f96cd6c5597` | `final`, 6000 steps | 9.599665888245219e-5 | `9.60e-5`, `46f8dbb2…` |
| `e0c` | `0f71111589e32a7e2b9515b3606454fc458e12c6e59950e413ceeba7e9c27073` | `screen`, 2000 steps, no head fit | 1.002877004917583e-4 | `1.00e-4`, `0f711115…` |
| `e0d` | none (no report) | `screen`, aborted at step 0 | — | not disclosed at `eab09bc9`; **disclosed at `dd6a529b`** |

`e0d` is a real third non-comparison scene: `e0d_run.sh` launches the `screen` stage into `.../e0d`,
`e0d.log` ends after the model-load lines, and `e0d/` holds only a step-0 checkpoint/metrics stub. It is
harmless to the comparison (no report, no metric). At `eab09bc9` the record said "Two earlier engineering
attempts" and did not mention it; at `dd6a529b` the third scene is disclosed as required (addendum).

Config copy: I flattened both files and compared every leaf. `e0_config_ref.json` differs from
`r1/scripts/configs/trackp_ada_v1.json` at exactly:

```
/e0/final/max_steps 6000 -> 2000
/e0/final/patience  10   -> 5
/comment            ...  -> "P5 E0-equivalence copy: final budget set to the TASL-7 reference ..."
```

So the claim "only `max_steps` and `patience`" is correct for functional values; the comment string also changes
(trivial, non-functional). The E0e report confirms `stage: final`, `max_steps: 2000`, `patience: 5`, lr/token
lr/head lr 1e-4/1e-4/1e-3, batch 8, seed 0, and `lora.best_step 1900`, `stopped_at 2000`, `completed: true`.

## 6. Timing carry-forward

`compute/20261127-24`'s 4B re-probe was committed `a801dc60` at 2026-11-27 13:38 +0100 and its re-check
`46b6820b` at 13:40 +0100; the smoke lease starts 18:34:21Z and the E0e lease 20:33:06Z. The probe therefore
predates the smoke, as the record says. The probe ran on paper `e92f3c73`, while the smoke/E0 ran on
`c80f83bc`, so the code is not the same either.

The record's conclusion is right: **no reviewed carry-forward exists**, and the phase-1 note (R1-P4-PHASE1-
SIGNATURE / Ada P5 line) requires either a reviewed carry-forward establishing that the existing timings used
the verified kernel/runtime, or a repeat of the timing probe after parity. The 4B probe's own record does not
claim that carry-forward, and I found none in the repository.

The stated reasons are slightly off, though. "Predates the smoke" is not by itself a disqualifier — a
carry-forward is precisely a reviewed argument about an earlier measurement — and an E0 metric miss does not
bear on whether a timing probe used the right kernels. The operative reason is the absence of the review (and
the different paper commit). The conclusion stands; a short reword would make it precise.

## Minors

Status after `28e451ea`: M1–M4 closed; M5 not taken (cosmetic).

1. **Required — the smoke evidence is not in the branch.** The record cites `lease.jsonl` and the smoke report
   hash, but the branch contains neither a smoke `report.json` nor `lease.jsonl` (the single `report.json` is
   E0e). The hashes match the host files, so the claim is true, but a reader of the record cannot check it and
   the `lease.jsonl` reference is dangling in the record directory. Commit the smoke report and lease (e.g.
   under `smoke/`), or state explicitly that they are host-only and correct the path. **Closed at `28e451ea`:
   the reports and `smoke_lease.jsonl` are committed; see the addendum.**
2. **Required — disclose `e0d`.** Say that a third scene, the `screen` launch into `e0d`, was aborted at step 0
   and produced no report; it is not the comparison and not one of the two scenes with reports. **Closed.**
3. **Recommended — name the drift.** State that the reference is pre-R1-E0-HEADFIT (`8e13e77` runs the AdamW
   head fit and lets LoRA start from the fitted head; `c80f83bc` records an L-BFGS fit and restores the fresh
   head), with `471f93f7`/`52b527b9`. This converts "consistent with drift" into the actual, checkable cause.
   **Closed.**
4. **Recommended — precise memory wording.** "Empty at start and end (0 foreign processes, 0 MiB)" should note
   that the captures show 5/8 MiB total on card 0 and that the zero is foreign-process memory. **Closed.**
5. **Optional — "only" in the config sentence.** Add "functional values"; the comment string also differs. Not
   taken; no further request.

## Unverified / limits

- The smoke report does not record the invocation or the model path, so the model digests were verified by
  hashing the staged tree under `paper_c80f83bc/models/`, not from a run log. The harness commit was verified on
  the checkout, not from a smoke manifest (there is none).
- The cause of the `e0d` abort is not documented beyond the truncated log; no label or evidence data was read
  to infer it.
- I did not re-run the smoke or E0, did not read labels, and did not write on Ada.
- `e0d`'s step-0 checkpoint remains only on the host. At `28e451ea` the record, smoke report, smoke lease,
  `e0b`/`e0c`/E0e reports, E0e manifest, comparison, config copy and reference are all committed.

## Disposition

The smoke PASS and the E0 STOP are independently confirmed. The record must not be cited as an Ada E0
equivalence, and the phase-1 note's `ada_smoke_e0` line remains blocked. The `e0d` disclosure, the drift and
memory wording, and the smoke-lease packaging are all fixed. **Final verdict: ACCEPTED.** No tolerance,
reference or result should be changed to turn the miss into a pass.
