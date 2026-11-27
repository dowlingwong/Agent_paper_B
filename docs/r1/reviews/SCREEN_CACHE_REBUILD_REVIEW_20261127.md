# Review — screening cache rebuild and engineering smoke (`compute/20261127-26`)

Independent review (read-only with respect to the deliverable). ENGINEERING_ONLY record.

- **Task:** `compute/20261127-26` (screening cache rebuild and 168-run engineering smoke after the cache-layout fix).
- **Deliverable branch:** `compute-screen-cache-rebuild-20261127`, tip
  `11ca8fe85f44262fd3f62764eebac9ed251f7106` as first reviewed; re-checked at
  `e6aced0f2039d2b0f380fb2a480d82768d1b7e59` (see the re-check section). Base `origin/main`
  `4a9a1f4aaaadca90edf1ae481cec3163a67e42b0` (merge-base equals that commit).
- **Code commit reviewed by the run:** `c12136d664ae588a2539b76b2602e36742979ce8`.
- **Task text:** `tasks/compute/20261127-26-screen-cache-rebuild-smoke.md` on `coord/coordinator`; design report
  `reports/20261127-23-screen-cache-layout.md` on `coord/local`.
- **Deliverable files:** `docs/r1/reports/screen_cache_rebuild_20261127/` (14 files: report, `commands.sh`,
  `SHA256SUMS`, 11 captures).

## What was verified, and how

1. **Lineage.** After `git fetch`, `origin/main` is `4a9a1f4a`; the deliverable's merge-base with `origin/main` is
   `4a9a1f4a`, so the branch is based on the published main tip. `git merge-base --is-ancestor c12136d6 origin/main`
   passes. `git diff --name-status origin/main...<branch>` adds exactly the 14 report-directory files and nothing
   else (no code, authorization, note, spec or result change). `git diff c12136d6 origin/main -- r1/` is empty, so the
   detached checkout of the code commit used for the run is code-identical to main; the report says so and declares
   the choice.
2. **Hashes.** In a clean extraction of the branch, `shasum -a 256 -c SHA256SUMS` reports OK for all 13 listed
   entries (the manifest covers every file except itself). The report's §3 table values equal the actual file hashes
   (`cache_MANIFEST.json` `1987cc00…`, smoke `manifest.json` `3c6dd543…`, `design.json` `29396f5b…`,
   `lineage_runs.jsonl` `0d8221a3…`, `worker_runtime.jsonl` `4633b06b…`, `cotenancy.log` `7504a111…`,
   `smoke.log` `ef7865fe…`, `data_cache_build.log` `8159b5fd…`, `precheck_stop.log` `eb462ad2…`).
3. **Cache tree, recomputed independently.** Using `tree_sha256` exactly as the reviewed module defines it
   (`git show c12136d6:r1/noise/screen_measure.py`: sha256 of `json.dumps(obj, sort_keys=True,
   separators=(",", ":"))`), I hashed each node's `files` map from `captures/cache_MANIFEST.json` and then the
   six-node map. All six per-node values match the manifest and the report's table
   (`058343f9…`, `3dc7f6bb…`, `1dc25c43…`, `97951b0b…`, `36d193ed…`, `afd165f3…`), and the recomputed top-level
   tree is `3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07`, matching the manifest, the
   data-cache build log, the smoke manifest's `data_cache.tree_sha256`, and the report.
4. **Per-file list.** `captures/cache_file_list.txt` has exactly 24 rows; every `<node>/data_cache/<path>` entry in
   the manifest is present with the same stored and decompressed sha256, with no extras. The four pilot ARFF
   decompressed hashes equal `PILOT_ARFF_SHA256` at `c12136d6` for `openml_breast_w`, `openml_credit_approval`,
   `openml_ionosphere` and `openml_wdbc`.
5. **Fixed-point layout.** `openml_breast_w` holds
   `openml/openml.org/data/v1/download/52350/breast-w.arff.gz` (arff `true`, content `cb44e7f6…`), and no short
   `52350.gz` entry exists anywhere in the manifest or file list — the report's central claim is correct.
6. **Smoke numbers.** `captures/manifest.json`: label `ENGINEERING_ONLY`, `planned_runs=168`,
   `written_runs=168`, `failed_runs=0`, `stop=null`, `seeds=[999]`, `workers=16`, `elapsed_seconds=46.9`,
   37 `identity_flags`. `lineage_runs.jsonl` has 168 rows, all `success=true` with a non-null metric, 168 distinct
   `(node, config, seed, condition)` jobs (84 node/config pairs × {`seed`, `repeat`}) over all eight design nodes;
   the manifest's `runs_sha256` equals the file hash. 152 edit rows have changed `values_before`/`values_after`, 16
   baseline rows are unchanged, and no row reports `edit_applied=false`. `design_sha256` in the manifest is the
   canonical hash of the parsed design (it equals `sha256` of the canonical JSON, not of the indented
   `design.json` file), as the module defines; the report's file hash for `design.json` is the file's own, correct
   hash. `smoke.log` ends with the same 168/168/0/null summary and contains no STOP or traceback.
7. **Worker runtime.** `worker_runtime.jsonl` has 168 rows, one per distinct job. The probe's field names are
   `prefix` and `versions`; mapped onto `worker_runtime_expected`, all 168 rows carry
   `worker_python=/ceph/dwong/r1_prepare_20261025/venv/bin/python3`, `prefix=/ceph/dwong/r1_prepare_20261025/venv`
   and `package_list_sha256=a089bbf1fc7522a596631f4dd9535a18866336ff18edbbae14932106d94f16d3`, with
   `versions={'numpy':'2.4.4','pandas':'3.0.3','scikit-learn':'1.8.0','scipy':'1.17.1'}` — the manifest's
   expected values exactly. The manifest's `code_sha256` map equals the six files at `c12136d6` (including
   `r1/noise/screen_measure.py` `ba05e1a4…`).
8. **Pre-check STOP.** `captures/precheck_stop.log` is
   `STOP: engineering smoke requires the evidence runtime: origin/main is stale or missing; fetch before evidence use`.
   That is the exact `_published_bytes_ref` message in `r1/c3/audit.py` at `c12136d6`, reached through
   `evidence_environment`; the module orders `out.exists()` → cache validation → `check_edit_sets` (temporary copies
   only) → `evidence_environment` → `out.mkdir(parents=True)`, so no output directory, job or scene can exist when
   this refusal fires. Because the earlier "output directory exists" guard did not fire, the capture itself also
   shows the target directory did not exist at refusal. The narrative is chronologically consistent: cache manifest
   `13:49:35Z`, `4a9a1f4a` committed `13:50:58Z`, smoke started `13:53:41Z`. The report does not overstate the STOP
   (not a run, not a scene, no attempt started); the PASS is a new directory, and the code creates the output
   directory only with `mkdir(parents=True)` and no `exist_ok`.
9. **Scope.** The branch is docs/captures only. The smoke command is `run --engineering-smoke` with a public
   data cache (six public OpenML datasets plus `digits_mlp`/`tabular_mlp`); no `--evidence`, no note, no sealed
   path, and the label is `ENGINEERING_ONLY`. Worker metrics are `val_score`. No code, spec, pin, authorization,
   note or result file changed. No GPU/CUDA reference appears in any capture; the run profile (46.9 s, 16 workers,
   40-CPU host) is consistent with CPU.

## Findings

**BLOCKING:** none.

**MINOR:**

- **M1 — The STOP capture is a bare message.** `precheck_stop.log` carries no timestamp, host, command, exit code
  or output path, so the exact time and the "one commit behind" attribution are inferred from code ordering and
  commit times rather than captured. `commands.sh` also refers to "The STOP below" without reproducing the stopped
  invocation. This does not overstate the STOP (see item 8), but the record would be stronger with a timestamped
  shell transcript of both invocations.
- **M2 — Two narrative details are not captured.** "The checkout was a fresh full clone, detached at this commit,
  with a clean working tree" is not evidenced: `RUN_ENV.txt` records the code commit, Python, harness commit and
  `harness_dirty=0`, but no `git status`/clone record. Likewise "CPU only" has no device record; the captures only
  show no GPU reference and a CPU-consistent profile.
- **M3 — Retention instruction not confirmed.** The task asks to keep both earlier STOP scenes and the old cache;
  the report neither states nor captures that this was done.
- **M4 — Wording nit.** "Nothing was patched, relaxed or retried" sits beside a documented pre-check STOP and a
  re-invocation of the smoke after `git fetch`. What is true is that no *attempt* was retried (no run had started);
  the sentence reads as if the command was never run again.

These are record-keeping/wording gaps; none affects a hash, a count, the cache layout or the scope boundary.

## Re-check — delta at `e6aced0f`

- **Tip and scope.** Fetched; the branch tip is `e6aced0f2039d2b0f380fb2a480d82768d1b7e59`
  (one commit over `11ca8fe8`, "record pre-check context and preserved scenes; address review
  minors"). `git diff --name-status origin/main...<branch>` still adds only
  `docs/r1/reports/screen_cache_rebuild_20261127/**` (17 files, all in the report directory). The
  delta touches the report, `SHA256SUMS` and three new captures; no original capture changed.
- **Hashes.** `shasum -a 256 -c SHA256SUMS` reports OK for all 16 entries, which cover every file
  except `SHA256SUMS` itself. The three new files' actual hashes equal both `SHA256SUMS` and the
  report's §3 citations: `precheck_context.txt` `26c77a0c…`, `preserved_scenes.txt` `7b660c7c…`,
  `post_run_status.txt` `edb2c142…`. The report's own new hash (`800bf884…`) verifies.
- **Pre-check context (M1).** `captures/precheck_context.txt` gives the host, log path and mtime
  (`2026-11-27T13:53:19Z`, 22 s before the PASS at `13:53:41Z`), the first invocation and its
  output path, the two main SHAs (`83425c70` before the fetch, `4a9a1f4a` at the fetch), and the
  observed absence of the output directory. It asserts no exit code or process status — nothing is
  invented. Its "stopped in `evidence_environment()` before `out.mkdir()`" matches the module order
  verified in item 8.
- **Post-run status (M2).** `captures/post_run_status.txt` is labelled exactly as what it is: a
  host observation after the run, "not a run-time capture". The report now draws only its post-run
  clean `git status`, HEAD and host card state from it, and says the run "used only CPU nodes and
  requested no GPU" instead of treating the card state as run-time evidence. The capture shows a
  host card at 100 % (another process, not ours); the report does not claim otherwise, so the
  wording does not overstate.
- **Preserved scenes (M3).** `captures/preserved_scenes.txt` is a read-only listing that shows both
  earlier evidence STOP scenes (`SMEAS_EVIDENCE_20261127T1032Z`, `…T1155Z`), the earlier cache STOP
  directory, the old cache and the old smoke directory, with pre-run mtimes. "Remain untouched" is
  supported by the listing and unchanged mtimes rather than content hashes — adequate for the
  purpose, with no writer to those paths in this deliverable.
- **Wording (M4).** The report now says "Nothing was patched or relaxed; no attempt or run was
  retried — only the preflight was re-invoked after `git fetch`, and it had created no attempt.",
  which matches the record.
- **Residual minors.** (a) M2 is partly addressed: the post-run clean tree is captured, but "fresh
  full clone" and "clean at start" still rest on the post-run status and are not separately
  captured. (b) M3's preservation is evidenced by a directory listing, not content hashes. Neither
  affects a hash, a count, the cache layout or the scope boundary.
- **No BLOCKING finding.** The numbers and hashes of the original captures are unchanged and were
  not re-derived beyond the `SHA256SUMS` check; the earlier full verification stands.

## Verdict

verdict: ACCEPTED
