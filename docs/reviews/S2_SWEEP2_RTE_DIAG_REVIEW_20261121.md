# Independent review — R1-SWEEP2-RTE-DIAG classification (sweep-2 worker `runtime_error`s)

**Reviewed.** Target branch `ops-sweep2-rte-diag-20261121` @ `342b06eb436bfa566b85250161d2470c353dd291`
(worktree `.claude-worktrees/ops-sweep2-rte-diag-20261121`), one commit over published main
`d47d1008509f9730cd8728b68a2cc560ce81e0e0` (confirmed ancestor). The commit adds only the diagnosis report
`docs/r1/reports/sweep2_20261116/S2_SWEEP2_RTE_DIAG_20261121.md` (SHA-256
`46b0206f200b75ebd3206a2b49ed34c0603d3eb780df07cb9b158faed00af663`) and 123 evidence files under
`docs/r1/reports/sweep2_20261116/sweep2_rte_diag_20261121/`; `git diff --name-only d47d1008..HEAD` contains
nothing outside that report directory. Authority: the `R1-SWEEP2-RTE-DIAG` row of `docs/r1/PLAN.md:1349` on
base main, which fixes the rule before the diagnosis: replay each of the six trials twice (exact config and
seed, same image and harness, CPU); **(i)** if all six crash deterministically with an exception raised by the
proposed configuration values, they are proposal-induced, treated like `invalid_config`, and the four chunks
are accepted; **(ii)** if any one fails to reproduce or traces to infrastructure (OOM, I/O, signal,
environment), the four chunks are rerun whole at a new launch commit. Scope: the classification only — this
review does not authorise the collection change itself.

**Method / read-only.** No git writes, no jobs, no execution of the campaign or of the node. The only write is
this one uncommitted review file. Sealed originals were read on deepthought
(`/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a/`) over SSH; replay copies were read on deepthought under
`/tmp/rte_diag/` and `/tmp/rte_evidence/`; all comparison arithmetic was done locally on bytes fetched
read-only. Working tree was clean before this file (`git status --porcelain` empty).

## 1. Six trials and their identities — verified

An exhaustive scan of every sealed `work/roots/<campaign>/root_trials.jsonl` in all 16 chunks of
`s2ev-20261119-a` finds **exactly six** failed trials with `failure_category = "runtime_error"`, and they are
exactly the six in the report:

| trial id | proposal summary | sealed structured edit (`extra.manager.structured_edit`) | sealed patch (`art/trial-NNN/patch.diff`) |
|---|---|---|---|
| `openml_breast_w__s145-trial-016` | `change-class-weight-custom` | `class_weight: "{0: 1, 1: 1.2}"` (old `balanced`) | `class_weight: balanced` → `class_weight: {0` |
| `openml_breast_w__s155-trial-019` | `increase-max_depth-null` | `max_depth: "null"` (old `5`) | `max_depth: 5` → `max_depth: null` |
| `openml_climate__s264-trial-019` | `set-class-weight-custom-minority` | `class_weight: "{1: 1, 2: 2}"` (old `null`) | `class_weight: null` → `class_weight: {1` |
| `openml_climate__s264-trial-020` | `set-class-weight-custom-ratio` | `class_weight: "{1: 1, 2: 5}"` (old `null`) | `class_weight: null` → `class_weight: {1` |
| `openml_credit_approval__s200-trial-011` | `change-class-weight-custom` | `class_weight: "{0: 1, 1: 1.5}"` (old `balanced`) | `class_weight: balanced` → `class_weight: {0` |
| `openml_wdbc__s150-trial-020` | `change-class_weight-ratio` | `class_weight: "{0: 1, 1: 1.2}"` (old `balanced`) | `class_weight: balanced` → `class_weight: {0` |

All six sealed records have `execution_status = "failed"`, `failure_category = "runtime_error"`,
`validity_status = "invalid"`, `decision = "failed_invalid"`, `worker_failure_message = "exit code 1"`, and
`wall_clock_seconds` 1.0–2.0 on the original H200 run. The sealed chunk gates agree with the launch STOP
record (`ops-sweep2-launch-20261121`): breast_w `STOP: 2 worker runtime_error(s)`, climate `2`, credit `1`,
wdbc `1` — 2+2+1+1 = 6; all other 12 chunks have 0 (the `none` chunks included).

**Patch/config reconstruction (no wrong campaign or trial).** For each of the six I applied the sealed
`art/trial-NNN/patch.diff` to the sealed `work/roots/<campaign>/node/config.yaml` of the *same* campaign and
compared the result byte-for-byte with the committed replay `runs/<trial>/config.yaml`: **6/6 match** (each
patch is a single-line change and the remainder of the 9-line config is identical). The trial ids, campaign
ids, seeds (`out/roots/<campaign>.json` records `seed` = 145, 155, 264, 200, 150), and patch references are
the failing artifacts of the sealed run, not a neighbouring campaign's.

**Chunk-record hashes.** The sealed `job_record.json` SHA-256 values, the `SHA256SUMS` lines, the full
hashes in `summary.json`, and the abbreviated hashes in the report table all agree:

| chunk | sealed `job_record.json` SHA-256 | report / summary |
|---|---|---|
| `openml_breast_w-append_only_summary` | `67510277dfd04f121d4bab73ef94ab6822068e714cfdb6f1614405f2c95f4415` | `67510277…f4415` |
| `openml_climate-append_only_summary` | `3b49670e37c363bb9f09952a6f004006296ba383bb3206e70810dd9d62580c9c` | `3b49670e…80c9c` |
| `openml_credit_approval-append_only_summary` | `65fb201fbaed79a7381f9e72b682664423d11337c2d5010782d2bc653e029ab4` | `65fb201f…29ab4` |
| `openml_wdbc-append_only_summary` | `9fcf8936e0da11e10b5fe5f420df12c00f5d6456c9b5871eb0a10c0d4ab4c871` | `9fcf8936…bc871` |

All four sealed `job_record.json` files declare `harness_commit = a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`,
`image_digest = ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296`
(the reviewed v1 image), `paper_commit = 4aac52092813b2b01ddb96cd7d135c390aeff645`, H200 GPU, same
`level_layout` (8735 s / 32 000 MB). The report's provenance line matches the sealed record.

## 2. Replay provenance — verified

- **Input = exact sealed worker input.** Replay working dirs on deepthought
  `/tmp/rte_diag/<chunk>/runs/<campaign>-tNN/` contain the node copy. Every input file (benchmark.py,
  train.py, README.md, dataset.json and every populated `data_cache` file) is byte-identical to the sealed
  `work/roots/<campaign>/node/` copies: **6/6 trials**, no differences. All six replay `benchmark.py` files
  hash `92c78bc5a47eb023e82915349b8e7626cf53635f6c36b641b046f494bfdcb54a` and all six `train.py` files hash
  `27d740067156ccfa2c70fd5c70ff850f6bba8e15d4733c043d37c94420b782c7`, equal to the sealed node files.
- **Committed evidence = replay artifacts.** All 66 replay output/marker files (config, run1/run2 out/err/rc,
  traceback, metrics, benchmark, train) hash identically to the deepthought `/tmp/rte_diag` files, and
  `summary.json` (`0099e0cbc007823f04bb5ae9cb135643309451cb0f0d3f42c7d879d5bb0075b9`) is byte-identical to
  `/tmp/rte_summary.json` and `/tmp/rte_evidence/summary.json`.
- **Two runs per trial, both failure-signalling.** 12/12 runs have `rc = 1`; 12/12 stdout carry
  `FAILURE_CATEGORY=runtime_error`; for every trial `run1.out == run2.out` byte-for-byte.
- **The strongest reproducibility check.** For all six trials the sealed original `art/trial-NNN/run.log`
  (the H200 worker's combined stdout/stderr log) matches both replay stdout files content-for-content,
  including the full multi-line `FAILURE_MESSAGE` with line/column; the only byte difference is the single
  trailing newline that `local_worker._run_command` appends as its stdout/stderr separator
  (`run.log = stdout + "\n" + stderr`, with an empty stderr here). Checked 12/12:
  `sealed run.log == replay stdout + one "\n"`. This is an exact reproduction of the sealed failure text, not
  merely the same exception class.
- **Tracebacks.** The committed `traceback.txt` files show `yaml.safe_load` at `benchmark.py:153` and
  `value = float(config[key])` at `benchmark.py:164` of the copy under `/tmp/rte_diag/`; the imported
  `yaml`/`sklearn` paths are the declared venv `/ceph/dwong/r1_prepare_20261025/venv` (Python 3.13.15,
  `pyvenv.cfg` confirms 3.13.15). The replay therefore hit the same node code as the sealed run.
- **Seeds.** `metrics.json` written by the replay records `seed` = 145, 155, 264, 264, 200, 150 for the six
  trials, i.e. the campaign seeds recorded in the sealed `out/roots/<campaign>.json`. This evidences
  `AR_TRAIN_SEED` per campaign. `AR_SPLIT_SEED` is not separately retained and could not be independently
  read back, but it is immaterial here: all six exceptions are raised inside `_load_config`, i.e. before any
  split or model randomness is used (and the sealed original's failure text is identical).
- One disclosed difference, immaterial to these failures: the sealed original ran in the v1 image, whose
  sealed manifest reports Python 3.13.18, while the replay used the venv at 3.13.15. The failure text is
  identical, so PyYAML/`float()` behaviour is demonstrably equivalent for these inputs.

## 3. Exceptions and offending values — verified, and the causal mechanism is deterministic

- Five trials: the applied line is exactly `class_weight: {0` / `class_weight: {1` (configs and sealed
  patches above), and `yaml.safe_load` raises
  `yaml.parser.ParserError: while parsing a flow mapping … expected ',' or '}', but got ':'` (same message
  from the sealed run and both replays). This is raised at config load, before any dataset fetch or training.
- One trial: `max_depth: null` is loaded as `None`; the `ALLOWED_RANGES` loop starts with `C` (fine) then
  `max_depth`, and `float(None)` raises
  `TypeError: float() argument must be a string or a real number, not 'NoneType'` at `benchmark.py:164`.
- The sealed `root_trials` structured edits correspond exactly: the applied `{0`/`{1` is the leading token of
  the proposed mapping (`{0: 1, 1: 1.2}`, `{1: 1, 2: 2}`, `{1: 1, 2: 5}`, `{0: 1, 1: 1.5}`), and
  `max_depth: null` is the proposed `null` (old `5`). No random or environment input enters either failure:
  YAML parsing and `float(None)` are pure functions of the written config text, and the sealed original plus
  both replays give the identical exception text.
- **Mechanism (worth recording in the sweep-2 report).** The truncation is not a mangled manager token: the
  manager's `_extract_structured_edit` takes the explicit JSON `param`/`old_value`/`new_value` fields
  (Strategy 1) and retained the full mapping. The worker's `_parse_change_directive` re-parses the prose
  `objective` with `_CHANGE_RE = r"change … from (\S+) to (\S+)"` and then `rstrip(".,;:")`; the `(\S+)` for
  `{0: 1, 1: 1.2}` captures `{0:` and the rstrip removes the colon, leaving `{0`. (These functions were read
  in the preserved harness checkout at `/ceph/dwong/r1_prepare_20261025/autoresearch_harness`; the sealed
  `art/trial-NNN/patch.diff` is the direct evidence that the sealed worker behaved this way, and the same
  truncation reappears identically in both replays.) This is a deterministic worker edit-rendering
  limitation. In substance the proposals are also invalid per the node schema (`class_weight` allowed values
  are `{null, "balanced"}`; `max_depth` must be numeric), so had they been rendered in full they would have
  been `ConfigError` → `invalid_config` (exit 2), not a metric. Treating the six as
  `invalid_config`-equivalent is therefore substantively right; see finding F4 for the follow-up.

## 4. Infrastructure ruled out — verified

From the 12 raw `run*.err` (GNU `time -v`) files:

| quantity | observed |
|---|---|
| exit status | 1 in 12/12 (no SIGKILL/137, no 128+signal) |
| Signals delivered | 0 in 12/12 |
| Swaps | 0 in 12/12 |
| File system inputs | 0 in 12/12 |
| Maximum resident set size | 133,344–139,748 kB (~130–136 MiB) vs `RequestMemory=32000` MB |
| wall clock | 11/12 in 1.68–2.05 s; one 2:57.87 s (see below) |

The single 2:57.87 s run is `openml_breast_w__s145-t16` **run 1**, the batch's first Python invocation:
6 % CPU, 419 major page faults, 10.85 s user + 0.52 s system — i.e. ~2:47 blocked, consistent with a cold
first import from `/ceph` / host contention, not CPU work and not a timeout. The evidence that it is not a
timeout or OOM is direct: it still printed the complete failure + `FAILURE_CATEGORY`, exited 1, used
135,628 kB; the same trial's run 2 took 2.04 s with 0 major faults and the identical output; and the sealed
original took 1 s on H200. No replay shows OOM, signal, I/O or environment error. The report's statement
that the 2:57 run "includes the first OpenML cache/Sklearn import" is imprecise about the OpenML cache
(never touched, since `_load_config` fails before `_load_frame`); the outlier is cold first-import/page-cache
and host wait. This does not affect the conclusion.

## 5. Sealed directories untouched — verified

- Full `sha256sum -c SHA256SUMS` over all four sealed chunks: breast_w 977 OK, climate 1013 OK, credit 977
  OK, wdbc 977 OK; **0 FAILED**, exit 0 per chunk. Content hashes therefore verify against the sealed lists.
- `find /ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a -newermt "2026-11-21 09:00"` returns **0 entries**;
  the directory and `job_record.json` mtimes are 02:46 / 01:44 (sealing window), well before the replay
  window (10:50–11:05). All replay/derived copies live under `/tmp/rte_diag/`, `/tmp/rte_evidence/`,
  `/tmp/rte_summary.json` and the branch; nothing under `/ceph` was written.
- The seal receipts (`SEAL_RECEIPT.json`, `sealed_utc 2026-11-21T01:37:40Z` for breast_w) and the four
  `job_record.json` hashes above are unchanged.

## 6. Classification (i) vs (ii)

**(i) is justified for all six.** Each of the six reproduces exactly (sealed original output equals both replay
outputs modulo the worker's one byproduct newline, noted in §2), exits 1, and is raised while loading the
exact configuration derived from the proposed edit; none of the failure classes involves OOM, signal, I/O,
environment or nondeterminism.

**No (ii) evidence was found.** There is no non-reproducible trial, no OOM (maxRSS two orders of magnitude
below the 32 GB request), no signal (`Signals delivered: 0`), no I/O error (`File system inputs: 0`), and no
environment failure (the declared venv exists, Python 3.13.15, imports resolve, and the same interpreter
produces the same text as the sealed H200 run). The only irregular observation — the 2:57 first `time` run —
is an import/page-cache/cold-start outlier that still produced the identical failure and exit code, and its
steady-state repeat is 2.04 s.

Because the rule in `PLAN.md:1349` was fixed before the diagnosis and its (i) condition is "crash
deterministically with an exception raised by the proposed configuration values", the six records qualify as
proposal-induced invalid trials treated like `invalid_config`, and the four chunks do not need the (ii)
whole-chunk rerun. One nuance the sweep-2 report should carry forward is that for five of the six the
proximate *exception* is a deterministic worker prose-parser truncation (F4) even though the proposals are
also schema-invalid; the classification remains (i) because the failure is deterministic, proposal-triggered
and not infrastructure.

## Findings

- **F1 (minor, evidence metadata).** `summary.json` `config_lines` for `openml_breast_w__s155-t19` shows
  `class_weight: balanced` and omits the actual offending `max_depth: null` (the five `class_weight` rows do
  include the offending line). The report table, `config.yaml` and `traceback.txt` are correct; regenerate the
  summary's excerpt from the changed line or drop the field. No classification impact.
- **F2 (minor, report wording).** The report's evidence path says the replay dirs contain
  `(config, patch, run1/2 out/err/rc, traceback)`, but no `patch.diff` exists in either the deepthought replay
  dirs or the committed evidence: the patches live only in the sealed `art/trial-NNN/` (and in the
  `/tmp/rte_diag/<chunk>/roots/` copy). The diagnosis is still reconstructible from the committed config plus
  the sealed patch, but the parenthetical is inaccurate; consider committing the sealed patch/`run.log` or
  citing their sealed locations explicitly.
- **F3 (minor, wording).** "the 2:57 first breast run includes the first OpenML cache/Sklearn import": the
  OpenML cache is never exercised because config parsing fails before the dataset fetch; the outlier is the
  cold first import/page-cache plus host wait (6 % CPU, 419 major faults; run 2 = 2.04 s; sealed original =
  1 s). The report's load-bearing conclusion (not a timeout/OOM) is correct; reword the explanation.
- **F4 (follow-up, non-blocking for this row).** Record the deterministic worker edit-renderer defect in the
  sweep-2 report and fix it before the next sweep: the worker should apply the structured `new_value` (or
  quote/escape/parse mapping values and YAML values containing spaces/colons) instead of re-parsing the
  prose objective with `(\S+)` + `rstrip(".,;:")`. Otherwise a mapping-valued proposal silently becomes a
  `runtime_error` instead of the honest `invalid_config`. Add a unit test with `class_weight: {0: 1, 1: 1.2}`.
- **F5 (trivial).** The report's "maxRSS ~133–136 MB" covers the run-1 values; one run-2 observation is
  139,748 kB (≈136.5 MiB). Still two orders of magnitude below the 32 GB request; no impact.
- **F6 (note).** `AR_SPLIT_SEED` is not independently evidenced by the retained artifacts (only
  `AR_TRAIN_SEED`-derived `seed` in `metrics.json` is); all six failures occur before the split is used, so
  this does not matter for the classification, but a future replay harness should capture the full env.

No finding blocks the classification. The evidence is internally consistent, reproduces the sealed failures
exactly, and rules out the (ii) conditions.

VERDICT: ACCEPTED
