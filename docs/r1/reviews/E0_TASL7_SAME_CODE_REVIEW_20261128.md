# Verdict: CHANGES REQUIRED

Task: `compute/20261128-01`, PLAN row `R1-P4-E0-SAME-CODE-REFERENCE`.
Reviewed branch/tip: `compute-p5-tasl7-e0-20261128` @ `e611835b5a1e237f0a1aa924fb8d63ec14235f81`
(one commit on base `a98d2eff1d2847e34f00effe66b53bc00467e936`). `origin/main` has since advanced to
`73524055d4a05f4375d48a98ae0b58ca0569278f`; the deliverable is not rebased, so the diff was taken against the
declared base. Reviewer: fresh-context delegated subagent, independent and read-only. Work was done in a detached
worktree at `/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/e0tasl7review/tip`; no host
login, no run, no GPU job, no write on any host, and no label was read. The only write is this review file.

## Bottom line

The scientific result is genuine and is correctly reported as a **STOP**: the TASL-7 E0 re-run reproduces the
pinned Ada run on both slope criteria and misses the RPS criterion by 19.09 % against a 10 % relative tolerance.
The provenance, data manifest, E0 recipe and comparator all reproduce exactly. **However, the committed deliverable
is incomplete: `SHA256SUMS` lists `gpu_lease.jsonl`, but that file is not in the branch, so `shasum -c SHA256SUMS`
fails for a listed file.** The record also overstates one derived-file description. Those are packaging/factual
defects, not a defect in the result; they are enough to require changes before acceptance.

## What is confirmed

### 1. Diff scope and cleanliness

```
git diff --name-status a98d2eff..e611835b
A  docs/r1/reports/trackp_p5_tasl7_20261128/E0_TASL7_SAME_CODE_20261128.md
A  docs/r1/reports/trackp_p5_tasl7_20261128/SHA256SUMS
A  docs/r1/reports/trackp_p5_tasl7_20261128/ada_reference_e0e_report.json
A  docs/r1/reports/trackp_p5_tasl7_20261128/comparison_e0e.json
A  docs/r1/reports/trackp_p5_tasl7_20261128/comparison_existing_comparator.json
A  docs/r1/reports/trackp_p5_tasl7_20261128/e0_config_ref_tasl7.json
A  docs/r1/reports/trackp_p5_tasl7_20261128/e0e_manifest.json
A  docs/r1/reports/trackp_p5_tasl7_20261128/e0e_report.json
A  docs/r1/reports/trackp_p5_tasl7_20261128/gpu_after.txt
A  docs/r1/reports/trackp_p5_tasl7_20261128/gpu_before.txt
A  docs/r1/reports/trackp_p5_tasl7_20261128/p5_compare_ada.py
```

Only the record directory is added; no existing file, code path, config, plan row or `.gitignore` is touched.
`git diff --check a98d2eff..e611835b` exits 0 (no whitespace errors). The added `p5_compare_ada.py` is a capture,
not a repository code change: it is byte-identical to the existing comparator
(`da5354ed4ce1fdd3c92e9fa846b274901f633d886845c08fca6abfde0a5e9216`, see §4).

### 2. Run provenance

`e0e_manifest.json` (sha256 `5da9a353637c7081a18dc9812e11a7561686e7f0ac63e09c28a4d9ad40a68f5b`) and the pinned
Ada manifest at `docs/r1/reports/trackp_p5_ada_20261127/e0e_manifest.json` agree on every required field:

| Field | TASL-7 run | Ada reference |
|---|---|---|
| paper commit | `c80f83bc5bc93356dfacadbcb5b186dfb59d028f` | same |
| harness commit | `897d83c8efa364ec2fdd37288241cc42e01d7274` | same |
| paper/harness dirty | `false` / `false` | `false` / `false` |
| seed | `0` | `0` |
| lr / token_lr | `1e-4` / `1e-4` | `1e-4` / `1e-4` |
| stage / variant / target | `final` / `fresh` / `y_soft` | same |
| evidence | `DRYRUN` | `DRYRUN` |
| max_steps / patience | `2000` / `5` | `2000` / `5` |
| data manifest | `b963be2dd378241e0b0689907d4051bfa62922a8e4968aa40061ed7ef275bfef` | same |
| torch / transformers / peft | `2.6.0+cu124` / `5.19.0` / `0.21.2` | same |
| kev / laya / startlux pip commits | `2074cc44` / `a478221b` / `a99977d9` | same |

The data digest also equals `docs/r1/reports/trackp_h200_20261118/stages/e0_h200/reference_manifest.json`
(`b963be2d…`), so the equality is against the reference manifest of record. Host: TASL-7, RTX 4090, sm_89,
driver `580.178.04`, UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, matching `gpu_before.txt`/`gpu_after.txt` and
the manifest. The committed Ada reference report
(`ada_reference_e0e_report.json`, `7df24070ee8a3a0838b3e2b3e71bf264fcbc6d8fa5a531fac2d28c16d8b9e817`) is
byte-identical to `docs/r1/reports/trackp_p5_ada_20261127/e0e_report.json` at the base (`diff` empty, same sha),
so the comparator's reference is the pinned Ada run and not a substitute.

The run manifest's canonical `config_sha256` is `31dd5776887df8e03c7f6e360f460c47f43c5d3bafc04a22c17f595c3b99b3d4`;
I recomputed `sha256(json.dumps(cfg, sort_keys=True))` from the committed config and got the same value. The
file-byte hash is `4f47048d…` as the record says.

### 3. The E0 recipe is the Ada recipe

Against `docs/r1/reports/trackp_p5_ada_20261127/e0_config_ref.json` (file sha256
`9773547dc286f638792b53b06cc7133d61209c2d9e92cdfd4982a062c1a2c054`, the hash named in the plan row), the
following blocks are exactly equal:

- `e0` (including `final.max_steps 2000`, `final.patience 5`, `final.eval_every 100`, `screen` block, `seed 0`);
- `head_lr = 0.001`;
- `lora = {"r": 16, "alpha": 32, "dropout": 0.05}`;
- `lr_grid = [1e-05, 3e-05, 0.0001]`;
- `token_lr = 0.0001`;
- Kev base: adapter `jaredpalmer/kev-0.8b@788ddbdd65715bb03a56788c822f6c632c9a551d`, base
  `Qwen/Qwen3.5-0.8B-Base@dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68`.

The TASL-7 file is `r1/scripts/configs/trackp_portal.json` changed at only three leaves: the `comment`, plus
`e0.final.max_steps 6000 -> 2000` and `e0.final.patience 10 -> 5`. The report agrees: `pass: true`,
`max_steps 2000`, `patience 5`, `lr 1e-4`, `token_lr 1e-4`, `head_lr 1e-3`, `variant fresh`, `stage final`,
`target y_soft`; `lora.best_step 1800`, `stopped_at 2000`, `early_stopped false`, `completed true`.

### 4. Comparator re-run

The committed comparator is byte-identical to the existing one on the base:

```
sha256  docs/r1/reports/trackp_p5_ada_20261127/p5_compare_ada.py
      = docs/r1/reports/trackp_p5_tasl7_20261128/p5_compare_ada.py
      = da5354ed4ce1fdd3c92e9fa846b274901f633d886845c08fca6abfde0a5e9216
```

I re-ran it in the record directory exactly as instructed:

```
python3 p5_compare_ada.py ada_reference_e0e_report.json e0e_report.json
```

Exit status **1**; `equivalent: false`. The output is byte-identical to `comparison_existing_comparator.json`
(sha256 `e85aa0032e075edf7931806622e39bd588b65052a963576f5e8278519387b58c`). The criteria and tolerances are
unchanged and hard-coded in the script (`ABS = 0.05` for the two slopes, `REL = 0.10` for RPS):

| Criterion | Ada (reference) | TASL-7 (candidate) | Delta | Tolerance | Pass |
|---|---:|---:|---:|---:|---|
| `width_slope_vs_label` | 0.9029562469607993 | 0.9051355634400368 | +0.0021793164792374142 | 0.05 abs | yes |
| `mean_slope` | 1.0141623146693686 | 1.0126712329837813 | −0.0014910816855873144 | 0.05 abs | yes |
| `rps` | 1.4383536969300546e-4 | 1.1637524682441221e-4 | rel. 0.1909135626876941 | 0.10 rel | **no** |

Recomputed independently: `|1.1637524682441221e-4 − 1.4383536969300546e-4| / 1.4383536969300546e-4 =
0.1909135626876941` = **19.091 %**; the absolute gap is `2.7460122868593255e-5`, while 10 % of the Ada RPS is
`1.4383536969300548e-5`. `comparison_e0e.json` (sha256
`46805e6c7fd4d37e9ed562adf0d55e740d82fc9fddb2a68def33bb488cbcf92e`) carries the same numbers and only relabels
the criteria (`reference_ada`, `candidate_tasl7`); its `descriptive` block is numerically identical to the
comparator output.

### 5. Lease, timing and the carry-forward disclaimer

`e0e_manifest.json` records one lease `start` at `2026-11-28T00:11:43Z` and one `end` at
`2026-11-28T00:40:07Z`, both on card 0 / UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, both with
`other_processes {count: 0, memory_mib: 0}` and `pid 2289540`. Span: 28 min 24 s = 1,704 s = **0.47333 GPU-h**,
matching the record's `0.4733`. `gpu_before.txt`/`gpu_after.txt` show 44 MiB total idle device use and no compute
process; the `0 MiB` in the record is correctly qualified as **foreign-process** memory. The record explicitly
says this is **not** a parity timing carry-forward and that a repeat or an explicitly reviewed carry-forward is
still required — that is the correct disposition.

### 6. Label discipline and STOP

The run is `ENGINEERING_ONLY` with `evidence_label: DRYRUN`; the report's `n_test = 1000` is the E0 synthetic
test split, not the paper's sealed test labels. I found no reference to a sealed/test label or an evaluation
value in the record or the capture directory. The record does not claim equivalence, does not widen a tolerance,
does not change the reference, and does not present a second run with a better value: the directory has a single
E0 scene (`e0e`) and the comparator's miss is kept as the result. It names the miss a **STOP** and forbids
widening, re-running for a better value, or changing the reference without the author's decision.

## Findings

1. **Required — `gpu_lease.jsonl` is listed in `SHA256SUMS` but is not in the branch, so the checksum file does
   not verify.** In the record directory at `e611835b`, `shasum -a 256 -c SHA256SUMS` verifies ten files and
   fails on the eleventh:

   ```
   shasum: gpu_lease.jsonl: No such file or directory
   gpu_lease.jsonl: FAILED open or read
   ```

   `git ls-tree -r --name-only e611835b docs/r1/reports/trackp_p5_tasl7_20261128/` has 11 entries and none is
   `gpu_lease.jsonl`; the record nevertheless lists it under "Files" at line 67 ("`gpu_lease.jsonl` (the two
   lease events)") and line 69 ("`SHA256SUMS` binds them"). The cause is the inherited ignore rule:
   `git check-ignore -v` reports `.gitignore:49:*.jsonl`. The file does exist in the author's worktree
   (`/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/pb-p5e0/docs/r1/reports/trackp_p5_tasl7_20261128/gpu_lease.jsonl`)
   with sha256 `f71fa1e50cd8141e074a5a92e563f8737f19a5ef0ff4edc1b2032d69fdfe4114`, exactly the hash in
   `SHA256SUMS`, and its two events match the manifest's `gpu_lease` array. The evidence is real; the branch
   simply does not carry it. Fix: force-add the file (`git add -f gpu_lease.jsonl`) and re-commit (do not amend
   or force-push), or remove the file from `SHA256SUMS` and from the record's "Files" list. Force-adding is the
   precedent used for `smoke_lease.jsonl` in the Ada P5 record. **This is the blocking defect.**

2. **Required (small) — `comparison_e0e.json` does not fully "correct" the reference/candidate labels, contrary
   to the record's description.** The record says the file is "same numbers, reference/candidate labels
   corrected" (lines 68–69). The top-level `candidate`/`reference` strings and the `criteria` keys are corrected, but
   the `descriptive` block still uses the comparator's original keys, and those keys are inverted: in
   `comparison_e0e.json`, `descriptive["lora.best_step"] = {"ada": 1800, "reference": 1900}`, where 1800 is
   TASL-7 and 1900 is Ada; likewise `descriptive["head_fit.test"]["ada"]["rps"] = 0.017788…` is the TASL-7 value
   and `…["reference"]["rps"] = 0.016919…` is Ada. Read against the file's own top-level `reference: Ada …` and
   `candidate: TASL-7 …`, the keys say the opposite of their contents. Fix: rename the descriptive keys (and the
   `head_fit.test` sub-keys) to `reference_ada`/`candidate_tasl7`, or reword the record to say only the criteria
   were relabelled. No number changes; the STOP is unaffected.

3. **Minor — "only `max_steps` and `patience`" omits the changed `comment`.** `e0_config_ref_tasl7.json` differs
   from `r1/scripts/configs/trackp_portal.json` at exactly three leaves: `comment`, `e0.final.max_steps
   6000->2000`, `e0.final.patience 10->5`. The functional claim is correct; the string change is cosmetic. The
   same caveat was accepted as optional in the Ada P5 review. Suggest "only the functional E0 final budget
   (`max_steps`, `patience`); the provenance comment also changes".

4. **Minor — "only host fields differ (GPU model, lock path, direct block)" understates the config delta.** The
   full top-level key set that differs from the Ada config is `bases, comment, direct, gpu, hf_home, host, image,
   lease, lease_comment, models_dir, runs_dir, sft, venv, work_dir`. Most are host/launcher fields, but `sft`
   (a different SFT schema) is not, and the list of examples is incomplete. The claim that matters — the
   E0-relevant blocks are identical — is true and verified in §3. Suggest "only host/launcher fields and the
   unused SFT block differ".

5. **Minor — the pinned config's descriptive `host` field still reads "TASL-2 (zhixu portal)" while the manifest
   records hostname TASL-7.** The functional host fields were updated (RTX 4090, `/home/dowling/r1_locks/gpu0.lock`,
   absolute model paths), and the manifest/`gpu_before.txt` are authoritative for TASL-7, so this is a stale
   descriptor inherited from `trackp_portal.json`, not evidence of a wrong host. Because the file hash is pinned,
   note it in the record rather than silently editing the file; a reader will otherwise ask why a "tasl7" config
   names TASL-2.

6. **Minor — "about 2.7e-5 absolute" is the observed gap, not the tolerance.** The 10 % relative tolerance on the
   Ada RPS is `1.438e-5` absolute; the observed gap is `2.746e-5`. The sentence at line 55 can be misread as
   saying the tolerance is 2.7e-5. Suggest "the observed gap is about 2.7e-5 absolute, while the 10 % tolerance
   is only about 1.4e-5".

7. **Observation — the Python patch version is not disclosed.** The Ada record states the run used Python
   `3.12.10` (`/data1/zli538/paperb_p4_20261127/venv`); the TASL-7 config's `venv.python` is `3.12.15`. The
   record's environment line lists torch/transformers/peft, which do match, but omits Python. This is a residual
   host difference, not a code/config difference, and it does not change the STOP. Suggest adding the Python
   version to the environment line so the "same code and configuration" claim is not read as a bit-identical
   environment.

## STOP disposition

**The RPS criterion is a real STOP: 1.163752e-4 vs Ada 1.438354e-4 is 19.09 % below, against a 10 % relative
tolerance, so `equivalent: false` and the Ada phase-1 note's `ada_smoke_e0` line and A5 SFT remain gated; no
tolerance, reference or result may be changed to turn the miss into a pass.**

## Limits

- I did not log in to TASL-7 or Ada and did not re-hash the original host artifacts. The manifest, report,
  config, comparator and comparison were verified from the committed copies; the missing lease was verified from
  the author's local worktree copy, whose hash equals the `SHA256SUMS` entry.
- I re-ran only the comparator, not the E0 training. The training result is accepted as recorded, not
  independently reproduced.
- `origin/main` is now `73524055`, ahead of the declared base `a98d2eff`; I evaluated the deliverable against the
  declared base. The branch adds only the record directory, so it is merge-safe.
