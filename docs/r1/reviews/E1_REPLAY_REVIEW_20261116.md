# Independent review — C3 B.1 e1 environment replay report (16 November 2026)

Reviewer: `reviewer-e1`, independent and read-only (did not write the reviewed unit). This is the
only write; no execution, no git write, no commit. Review date 2026-11-16 (Europe/Berlin).

Reviewed branch: `ops-e1-replay-20261116` @ `fd833c9e4837787dd64f078a32c2ebe72fc944bf`, parent
`origin/main` @ `9ae6d87783f53f9da27200869085c9ed0e7697e2`; directory
`docs/r1/reports/e1_replay_20261116/` (13 added files, 0 modified, 0 deleted; branch not merged).

## Authorities read

- Authorization `docs/r1/authorizations/c3_env_replay_20261116.md` @ `4da73306b8e10455fb124cf13d367e49b37247fe`
  (`origin/author-decisions-20261116`, committed 2026-11-16 10:31:47 CET, before the run), and PLAN row
  **R1-E1-AUTH**; basis R1-B2-REPLAY-GO (C1).
- Predeclared protocol `docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md`
  ("Predeclared replay protocol"), the case selection in
  `docs/r1/reports/MAC_M3_DRYRUNS_20261104.md` §1, and the runbook O4 e1/OpenML-STOP and co-tenancy
  text (`docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md`), plus R1-B2-DECOUPLE and R1-HANDOVER-04NOV.
- M3 reviews: `docs/r1/reviews/MAC_M3_REVIEW_20261104.md`, `MAC_M3_REVIEW_20261109.md`, and
  `M3_DRYRUN_PATH_REVIEW_20261114.md` (IT-1 (a) accepted at `5ef9db16`).

## Bottom line on the question asked

The STOP is the driver's predeclared OpenML hard STOP and is correct. The report is faithful: it
does not claim a replay or a pass, it does not overstate the environment evidence, and the artifacts
it ships are internally consistent and genuinely derived from the pinned corpus and driver. The
authorization's Open execution STOP was not bypassed and could not have been.

## Checks performed and results (all verified)

### Branch topology

- `fd833c9e` is a single commit whose only parent is `origin/main` @ `9ae6d877`; `origin/main` is
  still `9ae6d877`; `fd833c9e` is not merged to main; the branch contains exactly the 13 report files
  (all additions, no deletions).
- `5ef9db16` and `ec6e30a9` are ancestors of `origin/main` @ `9ae6d877`; `129317d1`
  (`mac-m3-dryrun-path-20261114` tip, one review-record commit past `5ef9db16`) is also in main.
- The authorization commit `4da73306` (with the authorization file and R1-E1-AUTH) is on
  `origin/author-decisions-20261116`, timestamped 10:31:47 CET; the run started ≈09:44 UTC
  (10:44 CET), so authorization predates execution. The report cites it by hash, which is correct
  because that branch is not merged to main.

### Sequence, dry run and pins

- Dry run first, into a distinct new directory
  `results/r1/engineering/C3_env_replay_20261116T094408Z_dryrun`: `logs/dryrun.stdout.log` is exactly
  the driver's dry-run return (`{"label": "DRYRUN", "cases": 16, "out": …, "nodes": [...]}`), exit 0,
  and `replay_plan.json` (SHA256 `a5f04ef271ba5eab57543f238c2c2b82481a303fb19e5a454ad2accb5f055ba6`)
  is a genuine driver `write_json` artifact: sorted keys, indent 2, trailing newline, byte-for-byte
  reproducible from its parsed content, `label: DRYRUN`, `schema: r1.c3_env_replay/1`,
  `tolerance: 0`, `environment: DEFERRED_TO_HOST`, `harness_commit: 6adf3859…`, thread env 1,
  `llm_requests: none`, `written_utc: 2026-11-16T09:45:29Z`.
- The plan's 16 cases match `MAC_M3_DRYRUNS_20261104.md` §1 exactly (case ids, nodes, seeds
  104/102/105/103/100/100/105/104, metrics, recorded tokens, kept/discarded decisions, patch
  prefixes), and each t002 `incumbent_files_hash` equals the corresponding t001
  `configuration_hash`. 12/16 cases are OpenML.
- Plan provenance is genuine, not merely self-consistent: the corpus index (`812468e2…`) and sidecar
  (`bb6d891c…`) hashes match the repo blobs at the pin; the two frozen trees resolve to
  `6b1c0c61…`/`468e57ce…`; the collector blob at `ccb4712` hashes to `0001260442f9…` with both seed
  bindings present; **all 64 per-case corpus hashes** (ledger, events, root record, archive file for
  each of the 16 cases) match git blobs at `5ef9db16`; all 16 tar members (patch and log) match their
  recorded hashes; every archived log's last emitted metric token equals the plan's recorded token;
  every `patch_hash` equals the archived patch member hash.
- Real replay second, into a different new directory `…_real` (no `--dry-run`): `logs/real.stdout.log`
  is exactly one `{"verdict": "STOP", "reason": "STOP: OpenML offline dataset availability and worker
  network denial are not verified; no replay scheduled"}` line, exit 2; stderr empty.
- Deployed paper code `5ef9db16`: the driver blob hashes to
  `a9cad4d544bdf061c42ecb4b4c2d3d10d8bc94342574d9a37489bd4b179aa7d8`, and is byte-identical at
  `5ef9db16`, `9ae6d877` and the report branch.
- Pins in `pins.json`/`logs/env_observations.log` match the authorization: batch wrapper →
  `/ceph/dwong/r1_prepare_20261025/venv/bin/python`, Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4,
  pandas 3.0.3, SciPy 1.17.1, 59 packages with list SHA256 `c09242ac…`, newest dist-info mtime
  `2026-10-26T22:09:12Z` (< launch 2026-10-27T15:48Z), `uv.lock` `dd42d018…`, freeze `c760b28f…`,
  narwhals 2.27.1 the documented addition, harness HEAD `6adf3859…`. Co-tenancy was checked at
  09:44:44Z and 09:45:44Z: 113.4/113.5% total CPU ≈ 1.13 of 40 cores used, ≈38.87 free (≥10
  required). Disk/file-count headroom matches the report.

### STOP and driver code

- The reason string is byte-for-byte the driver's whole-set gate message at
  `git show 5ef9db16:r1/scripts/c3_env_replay.py` lines 578–579. It is *not* the per-case message
  (lines 482–483, which lacks `"; no replay scheduled"`), so the run-level gate fired before
  scheduling. It also proves the host check at lines 576–577 passed (the OpenML gate is only reached
  after it), i.e. the run was on `deepthought`.
- Driver order verified: output-new (line 551), output-not-in-corpus/batch (553–555), no LLM modules
  (556), `verify_corpus` (557), `verify_collector_binding` (558), `select_cases` (559), count 16
  (560), host (576–577), **OpenML STOP (578–579)**, then `check_environment`/`check_harness`/
  `check_resources` (588–590), `out.mkdir()` (591), `scratch.mkdir()` (592), and only then the case
  loop (599). So no case could run, no real out dir or scratch could be created, and no
  `cases.jsonl`/`summary.json`/driver `STOP.json` could be emitted. The report's operator-authored
  `STOP.json` says so explicitly (`artifact_author`, custom schema, no driver summary schema).
- `cases.jsonl` is zero bytes (SHA256 `e3b0c442…`), consistent with zero cases run. The report's
  distinction between the operator STOP.json and a driver-emitted one is honest.

### Evidence integrity

- `SHA256SUMS.txt` verifies for all 12 listed evidence files (I recomputed each from the pushed
  blobs; `cases.jsonl` and both stderr logs hash to the empty-string digest, as stated).
- Both stdout logs have the exact `json.dumps` key order of the driver's dry-run return
  (`label, cases, out, nodes`) and its `Stop` handler (`verdict, reason`), i.e. they are consistent
  with real driver output rather than free text.
- Pins/commands/cotenancy/env-observation logs are mutually consistent with the report and with the
  plan (paths, stamps, hashes, host, timestamps); no contradictory artifact was found.

### Authorization compliance

- e1 only: no e2, no B.2 work, no audit outputs; the branch contains only the report. The report says
  so in §7 and does not carry the replay-passed disclosure.
- ENGINEERING_ONLY is the label of `STOP.json`/`pins.json` and the report; the dry-run plan is
  correctly `DRYRUN`. Host CPUs only, workers 1, no manager model; no GPU or worker ran.
- Output directories are under `<paper checkout>/results/r1/engineering/` — outside the preserved
  batch and outside `results/r1/evidence/`. Dry-run and real paths are distinct and both new; the
  real one was never created. The preserved batch was only read; nothing was deleted or moved.
- One operator on the host is asserted, and the host capture shows only the operator's own session
  processes and no other Paper B workload. Nothing indicates a bypass or a second run.

### "Precise missing mechanism" statement

Accurate and sufficient for the author. It names both required properties — (a) proof that the exact
OpenML datasets for the six nodes are available offline, bound to the exact task/data identity rather
than any cache file, and (b) enforced no-network download in worker subprocesses while preserving the
frozen worker's numerical semantics — then requires independent review and wiring into
`c3_env_replay.run`. It correctly identifies the M3 evidence hole (presence-only `has_cache_files`,
`fetch_openml(..., data_home=...)` without `download_if_missing=False`, gate A1 OPEN/partial, A4
offline OPEN, 9 Nov review note that wiring is left out). It overclaims nothing: it explicitly says a
passing environment recheck cannot clear the STOP and that only that mechanism can.

## Findings

**Blockers: none.**
**Majors: none.**

**Minors**

1. **Scratch-newness is attributed to a driver check that was never reached.** `REPORT.md` §4 lists
   "output/scratch-new" among the checks that ran before the STOP, and `STOP.json`
   (`checks_reached_and_passed_before_the_stop`) states `"output-and-scratch-must-be-new": "passed
   (real out dir and scratch did not exist)"`. The driver's pre-STOP code only checks that `--out`
   does not already exist (line 551) and is not inside the corpus/batch (553–555); "output and
   scratch must be new" lives in `check_resources` (lines 450–451, called at 590), which the report
   itself correctly says was never reached. The fact that the scratch path did not exist is true and
   is supported by code order (`scratch.mkdir()` is after the STOP), but it is an operator
   observation, not a driver check that passed. Fix: relabel as "output new (driver, line 551);
   scratch new (operator observation; `check_resources` not reached)".
2. **The authorization quotation in `STOP.json` is a paraphrase inside quotation marks.**
   `stop_rule[0]` quotes the authorization's "Open execution STOP" but changes "the present driver"
   to "the driver", drops "that", and appends "; do not bypass", which is PLAN row R1-E1-AUTH's
   wording, not the authorization note's. Meaning is unchanged; for precision quote the note exactly
   and cite R1-E1-AUTH separately for the no-bypass clause.
3. **Post/during-run state is asserted without a capture.** `cotenancy.log` concludes "no co-tenant
   appeared during the run", and `REPORT.md` §5 says "no lingering replay/worker processes", but
   both co-tenancy snapshots are *before* the two starts and `env_observations.log` is pre-run; there
   is no during-run or post-run capture. The claims are logically supported (the driver STOPs before
   the case loop, so no worker/case process could exist, and the driver process exited), so this is
   immaterial, but phrasing such as "no other-user load and no Paper B workload at either check; no
   worker could start before the STOP" would match the evidence exactly.

## Observations (not findings)

- The 4 November M3 review's own verdict is **NOT ACCEPTED** (only its same-reviewer safety-remediation
  re-check was accepted); the M3 acceptance is the 9 November review, recorded at `ec6e30a9`. The
  report/authorization list both reviews under "M3 accepted"; the report uses the 4 November Major 1
  accurately, so this is a citation nuance only.
- The pre-STOP enumeration omits the host check (`platform.node()`, lines 576–577), which did pass —
  the exact OpenML message can only be reached after it. Mentioning it would strengthen the host
  claim.
- "Freeze vs current list: only addition narwhals==2.27.1" is not printed directly in
  `env_observations.log`; it follows from the current package-list SHA `c09242ac…` matching the 28
  October observation, whose only freeze difference was narwhals. A direct diff capture would be
  cleaner but the claim is sound.
- The authorization asks for inspection between the dry run and the real run. The report records the
  inspection (§3) but not its time; `pins.json` puts the dry-run plan at 09:45:29Z and the real start
  at ≈09:45:45Z. This is immaterial: the real invocation refuses at the whole-set gate before
  scheduling, so the STOP/report conclusions do not depend on it.
- `commands.txt` is a curated exact-command record with annotations, not a shell transcript
  ("verbatim" in `REPORT.md` §1 is slightly strong, though the commands themselves match the driver
  CLI and the logs).
- Host-side facts (batch/interpreter/harness/deployment/retained state) are operator observations and
  cannot be independently re-derived from this repository; the report consistently labels them as
  observations and explicitly says they cannot supply a PASS, which is the correct treatment.
- The report's conclusion is well supported by strong positive evidence: all pre-execution source,
  corpus, collector and case-selection checks necessarily passed before the exact line-579 message
  could be printed, and the plan artifacts bind to the pinned corpus and driver at `5ef9db16`.

VERDICT: ACCEPTED
