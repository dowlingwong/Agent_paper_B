# Independent review — Track P Unit B result on TASL-7 with D2 (19 November 2026)

**Status: ACCEPTED — 0 BLOCKING, 0 MAJOR, 1 MINOR (documentation only, non-blocking).** Fresh independent
reviewer; no part in authoring D2/C2'', the unit, the run, the result record or the captures. **Review only: no GPU
job, no host modification, no deletion, no commit/push, no HTCondor/deepthought.** Read-only SSH to TASL-7
(`ssh -o BatchMode=yes tasl7 '…'`) was used for the live-fact checks; the only workspace change I made is this
uncommitted, untracked review file (the ops worktree is being written concurrently by other agents — e.g. untracked
`docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_FIX_20261119.md` — unrelated to this review and not touched by
it). One transient exception to "no host write": the live-venv freeze was captured into two short-lived
`/tmp` files on TASL-7 and removed immediately (`/tmp` re-checked: no `rv_freeze*` leftovers, no `dowling`-owned
`/tmp` file newer than 01:19Z); no repository, venv, lease log, model, run root or marker was touched.

## 0. Objects, authority, method

| Object | Value at review |
|---|---|
| Published main | **`de3de54fd22dcdd86215be0924307e36a64ed08b`** (`origin/main`; `de3de54f`) |
| `R1-TRACKP-D2` | `de3de54f:docs/r1/PLAN.md:1300` — authorize D2 from D `8662e359`, accept TASL-7 (driver `580.178.04`) / TASL-2 (`535.309.01`) each with its own driver pin; replace attempt-1 boot-id equality with verification of attempt-1 artifacts against recorded hashes; record/disclose current boot id; nothing else changes; **"R1-TRACKP-UNITB then names D2 in place of D"**; Unit B on TASL-7 first, TASL-2 if TASL-7 unreachable; one host per table, named in the report |
| `R1-TRACKP-UNITB` | `de3de54f:docs/r1/PLAN.md:1246` — probes-only, qwen3.5-4b, new root, DRYRUN first, 45-h GPU budget, host verifies HEAD/clean/runner sha; STOPs; A6 deferred |
| `R1-TRACKP-TASL2-HOST` | `de3de54f:docs/r1/PLAN.md:1275` — TASL-2 fallback only; one host per table, host named in report |
| **D2** (delivery pin) | `8309b69e81837fb9719fa01b28f0dde94975e4f9`; `git rev-list --parents -n 1` = `8309b69e 9dc4afba` (single parent); on TASL-7 detached, `status --porcelain` empty |
| **C2''** (code) | `9dc4afbaa29546dafb1d1274e37d3910c5d9ed0e`; parent `8662e359` (D) |
| Runners | D2 runner blob `d3419e2d2582367b5bb0b53994c9baaf5a04a3815b4b5a47ce38786c25a64750`; C2'' runner `ae2a7955…`; child `r1/scripts/trackp.py` `5679ce1b26721ca129fedf7e9e9bef705d8ce056eb2fac7e745d7879b65aee6` |
| D2 delivery-pin property | `git diff 9dc4afba 8309b69e -- r1/scripts/trackp_p3a_guarded.py` = **one line only** (`EXPECTED_PAPER_HEAD` `5b7ad0cb…` → `9dc4afba…`); D2 tree runner = `4823f7c9…` = content sha256 `d3419e2d…` — **delivery_pin_child reproduced** |
| R3 code review | `docs/r1/reviews/TRACKP_P3A_D2_CODE_REVIEW_R3_20261119.md`, sha256 `ae5299d5…` — **ACCEPTED, 0 BLOCKING / 0 MAJOR / 3 MINOR (documentation only)**; R1/R2 files sha256 `1287b4a8…` / `837d3490…` (match R3's citations) |
| Result record reviewed | `docs/r1/reports/TRACKP_UNITB_TASL7_D2_RESULT_20261119.md`, **sha256 `b53dbaeae3c1c94d3a6631475c7b644e7e24ba18e43b2cbef09889b4211e8819`, 42 lines** (untracked at review time; ops worktree HEAD `e294e29e`) |
| Captures reviewed | `docs/r1/reports/trackp_unitb_tasl7_d2_20261119T011430Z/`, `SHA256SUMS` sha256 **`02e7c8b4a6e79e9c4772f4dbf17417e75e87ba8b0648b2c594747aedab76792d`**, 12 logged files (+ the static `SHA256SUMS`), `shasum -a 256 -c` → **12/12 OK** |

Method: the record was read line by line and every number/claim mapped to the journal, the child/runner manifests,
the reports and the captures (§4); all captures were re-hashed against the live TASL-7 root with read-only
`sha256sum` (§3, §5); provenance was re-derived independently (attempt-1 journal/manifests/saved files/archive/lease
snapshot re-hashed on the host and compared with the D2 pins): no recorded value was taken on trust from the record
or from the journal's own claims. Commands are reproduced in the appendix.

## 1. Host / identity — VERIFIED

| # | Claim | Independently verified on TASL-7 |
|---|---|---|
| 1 | Detached D2 `8309b69e` on TASL-7 | `/home/dowling/r1_trackp/d2_20261119`: `rev-parse HEAD` = `8309b69e…`, `symbolic-ref` fails → **detached**, `status --porcelain` count **0** |
| 2 | Host profile TASL-7 / driver `580.178.04`; attempt-1 host | `hostname` = TASL-7, `uname -r` 6.8.0-149-generic; `nvidia-smi` driver **580.178.04**; `/proc/driver/nvidia/version` = 580.178.04; dpkg `nvidia-utils-580`/`libnvidia-compute-580` = 580.178.04-0ubuntu0.22.04.1; attempt-1 manifests record `tasl7_driver.nvidia_smi_driver = ["580.178.04"]` for all four bases |
| 3 | Current boot id `713ca10b…` recorded, not required to equal attempt-1 `2c9bb104…` | `/proc/sys/kernel/random/boot_id` = **`713ca10b-ec21-413c-b61f-30da4a7b1e96`**; journal `boot_id` = same; `boot_id_required: false`; attempt-1 journal `campaign_start.boot_id` = **`2c9bb104-cc3c-4c60-be67-c1c8f0287fe4`**; journal `boot_id_matches_attempt1: false` |
| 4 | Paper identity `delivery_pin_child` C2'' | journal `paper_identity` = `{kind: delivery_pin_child, commit: 8309b69e…, expected_commit: 9dc4afba…, branch: HEAD}`; `paper.dirty: false`; runner `EXPECTED_PAPER_HEAD` = `9dc4afba…` |
| 5 | Harness `897d83c8…` clean | `autoresearch_harness`: HEAD = `897d83c8efa364ec2fdd37288241cc42e01d7274`, branch `trackp-20261026`, `status --porcelain` = 0 lines |
| 6 | Frozen venv `trackp-gpu` freeze `50238e5a…` (121 lines) | `…/venvs/trackp-gpu/bin/python` = Python 3.12.15; `uv pip freeze --python` = **121 lines, sha256 `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`**, `cmp` against committed `tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt` (same sha256) = **identical** |
| 7 | Config pin `049bafed…` | `r1/scripts/configs/trackp_portal.json` sha256 = **`049bafede821e9a15b38cdfc96b9198f1d1cbdd63153dced25250e045e71c2f7`**; recomputed `config_digest` (per `r1/c3/train/run.py:86`, `json.dumps(sort_keys=True)`) = **`64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c`** = child-manifests' `config_sha256`; placeholders `[]` |
| 8 | One host per table; TASL-2 fallback not used; no evidence outside Unit B | Run root contains only `DRYRUN/kev-0.8b` and `EVIDENCE/qwen3.5-4b-base` plus provenance/lease/journal; no TASL-2 artifact, no D21/D28/noise-floor root; `runs/` has only the attempt-1 root (untouched), the attempt-2 root and its `.parent`; new items under `r1_trackp` since 18 Nov are only the D2 deployment (`d2_20261119`, `.git` objects) and the run |

## 2. Attempt-1 provenance / artifact verification — VERIFIED (real host, fail-closed code)

D2's preflight (`verify_attempt1_artifacts` → `verify_attempt1_manifest`/`_archive`/`_lease_log`) re-hashes every
listed file and STOPs on any mismatch (read at `trackp_p3a_guarded.py:1095-1280`); the journal record
`attempt1_artifacts.verified_utc = 2026-11-19T01:14:52Z` and its values were independently reproduced from the live
bytes:

| Artifact | D2 pin / journal | Live TASL-7 re-hash |
|---|---|---|
| Attempt-1 journal | `1e73e80f…`, 81 events | `1e73e80f…`, **81 lines**; last event `STOP` 2026-10-29T01:25:17Z; `gpu_seconds_total` **130745.3789889291**; paper `b9ad6f8f…`; boot `2c9bb104…` |
| 4× `EVIDENCE/<base>/final/manifest.json` | `5ee8842a…` (kev-0.8b), `9d7b333d…` (kev-4b), `0381f73a…` (qwen3.5-0.8b-base), `9e1d5f08…` (qwen3.5-4b-base) | **all four match**; each manifest's `git.paper.commit` = `b9ad6f8f…`, `git.harness.commit` = `897d83c8…`, boot = `2c9bb104…`, driver = 580.178.04 |
| 4× `final/saved/manifest.json` | `26d80be0…`, `e898d51a…`, `8524b503…`, `f4c36658…` | **all four match** |
| 16 saved/model files (`adapter/README.md`, `adapter/adapter_config.json`, `adapter/adapter_model.safetensors`, `heads.safetensors` × 4 bases) | as in journal `verified_files` (bytes+sha256) | **all 16 match byte-for-byte** |
| Backup archive | `fa2437ee52d8873075c0bed6e88fba16d04deb2428e931a365dc602cdf902c87`, 328,136,435 B | `p3a_attempt1_final_saved_20261117T0015Z.tar.gz` = **`fa2437ee…`, 328136435 B** |
| Attempt-1 lease log (TASL-7 global path) | `6950509182f4230dd2c7e2bad4253748415fa969e84ef9bdac21e19242b55077`, 111 lines | source `/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl`; **`head -111` sha = `69505091…` = snapshot sha; `cmp` identical**; snapshot 55,726 B, 111 lines, mode `0444` |
| Driver snapshot | 580.178.04 kernel+packages in `pins.driver` | kernel module + dpkg + `nvidia-smi` all 580.178.04 (§1) |
| Boot ids | current recorded/disclosed; attempt-1 recorded; not compared | see §1 |
| **No live-log conflation** | — | `unit_start_verification.lease_log_snapshot_sha256` = `69505091…` (immutable snapshot), and the snapshot is exactly the first 111 lines of the live global log; the live log is now **117 lines = the same 111 lines + six attempt-2 entries (lines 112–117)** — the unit-start checks bind the snapshot and never re-hash the growing live log |

Every value the record attributes to the preflight is present in the journal and was re-derived from the real host
files; nothing was satisfied by trusting the attempt-1 inventory alone.

## 3. Execution / journal / budget — VERIFIED

| # | Claim | Verified |
|---|---|---|
| 1 | Exactly two probes units: `DRYRUN kev-0.8b n=8`, `EVIDENCE qwen3.5-4b-base n=100`, `--a3-short` | journal argv: `probes … --base kev-0.8b … --a3-short --n-probe 8 --evidence DRYRUN` and `--base qwen3.5-4b-base … --a3-short --n-probe 100 --evidence EVIDENCE`; child-manifest argv identical; `probes_only {a3_short: true, dryrun_n_probe: 8, evidence_n_probe: 100, dryrun_base: kev-0.8b, base: qwen3.5-4b-base}` |
| 2 | Journal 8 events in order: campaign_start → marker_begin rc0 → unit_start/complete ×2 → marker_end rc0 → complete | **8 events**, exact order: `campaign_start` 01:14:53Z, `marker_begin` rc0 01:14:53Z, `unit_start`(DRYRUN) 01:14:53Z, `unit_complete` 01:15:14Z, `unit_start`(EVIDENCE) 01:15:14Z, `unit_complete` 01:18:00Z, `marker_end` rc0 01:18:00Z, `complete` 01:18:01Z; no STOP/retry/exception event |
| 3 | A3 `pass: true` / `v2_budget`, A3_descriptive skipped `R1-P3A-OOM-OPTION3`, A4 pass | both `report.json`: `A3.pass=true`, `A3.protocol="v2_budget"`, `A3_descriptive.skipped="R1-P3A-OOM-OPTION3"`, `A3_descriptive.pass=null`, `A4.pass=true` (DRYRUN slope 0.9843, EVIDENCE slope 0.9940); `A4_v1_raw.criterion_met=true` |
| 4 | GPU seconds 17.7276 + 162.2841; total 130925.3907 | `unit_complete.gpu_seconds_unit` = **17.727633464994142** and **162.2840853670059**; `gpu_seconds_total` = **130925.3907077611** = attempt-1 130745.3789889291 + `new_lease_seconds` 180.01171883200004 |
| 5 | 36.368 h; remaining 8.632 h to 45 h STOP / 60 h cap | `130925.3907077611/3600` = 36.36816 → **36.368 h**; `remaining_seconds` 31074.609292238907 (45 h limit 162000 − used) = **8.6318 h → 8.632 h**; `cap_seconds` 216000 (60 h); budget in `complete` event |
| 6 | No STOP/retry; marker rc0 | no STOP/retry file or event; `marker_begin.rc=0`, `marker_end.rc=0`; helper log: `01:14:53 begin p3a`, `01:18:00 end p3a`; marker now `absent`, lease `free` |
| 7 | Lease log 111 → 117 lines | global `/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl`: **117 lines**, sha `e97e03d2…`; attempt-1 ended at line 111; lines 112–117 are exactly the two units' `acquired`+`start`+`end` entries (pids 28655, 28892) |
| 8 | GPU 43 MiB / 0 % after; no leftover process | `nvidia-smi` at 01:21Z: **43 MiB / 24564 MiB, 0 %**, no compute apps (only Xorg/gnome-shell graphics clients); `ps` grep for `trackp*` → none |
| 9 | Only operator log dir extra (`${ROOT}.parent` mistake), kept not deleted | `/home/dowling/r1_trackp/runs/p3a_attempt2_20261119T011430Z.parent/` present with `unitb_d2_20261119T011430Z.log` (1299 B, sha `b20a9dab…` = captured `unitb_d2.log`); launcher in `/tmp/run_unitb_d2.sh` explains it (`LOG="$ROOT.parent/…"`); nothing deleted |
| 10 | rc 0 / complete | `.parent` operator log `Exit status: 0`, `unitb_d2_rc=0`; journal `complete` event; captures `unitb_d2.log` sha `b20a9dab…` identical to host log |

## 4. Record accuracy — every claim mapped

| Record line | Claim | Evidence | Result |
|---|---|---|---|
| 3-5 | Status/authority, `R1-TRACKP-UNITB` names D2 | §0 PLAN rows | **match** |
| 5-8 | D2 `8309b69e`, C2'' `9dc4afba`, R3 accepted 0B/0M/3m, runner `d3419e2d`, child `5679ce1b` | §0 | **match** |
| 8-10 | TASL-7 profile 580.178.04, attempt-1 host, current boot `713ca10b…`, attempt-1 `2c9bb104…`, `boot_id_required:false` | §1, §2 | **match** |
| 14 | Root, TASL-7, 188 K, 528 G free | `du -sh` root = **188K**; `df -h` = **528G** avail (`df -B1` 566,183,645,184 B at re-check; journal `campaign_start.disk.free_bytes` 566,184,722,432 B) | **match** |
| 14-16 | Journal 8 events order | §3 item 2 | **match** |
| 17-20 | Command, harness `897d83c8…` clean, freeze `50238e5a…` (121), config `049bafed…`, no STOP | §1 items 5-7, §3 item 6; command string in operator log = journal argv = `/tmp/run_unitb_d2.sh` | **match** |
| 21-26 | Preflight: journal `1e73e80f…` 81 events, 4 manifests + files, archive `fa2437ee…` 328,136,435 B, lease `69505091…` 111 lines, boot disclosure, driver in `pins.driver` | §2 | **match** |
| 27-31 | A3/A3_descriptive/A4, GPU seconds, total, 36.368 h, 8.632 h | §3 items 3-5 | **match** |
| 32-34 | Marker rc0, lease 111→117, GPU 43 MiB/0 %, no leftover, `.parent` kept | §3 items 6-9 | **match**, with the path-precision MINOR-1 below |
| 35-36 | Capture inventory | §5 | **match** (12 logged files + static `SHA256SUMS`) |
| 38-42 | Scope: one host per table, fallback not used, no evidence outside Unit B, no noise/D21/D28, no deletion, no force push, no HTCondor/deepthought | §1 item 8; attempt-1 root **724 files, none newer than 2026-11-17**, so the run did not modify it; `.parent` preserved; no other run root; no HTCondor/deepthought artefact. The scope wording claims only "no force push" (not "no push"): `origin/trackp-p3a-d2-20261119` exists at `8309b69e` and is not merged into `origin/main` `de3de54f` — nothing in the inspected state contradicts it | **match** |

No number, hash, rc, unit name, host or budget value in the record disagrees with the journal/reports/captures or
the live host.

## 5. Captures and completeness — VERIFIED

- `SHA256SUMS`: `shasum -a 256 -c` → **12/12 OK** on the Mac. Live-vs-capture hashes (host `sha256sum` vs capture
  file) are **identical for all 12**: journal `9bfda7fc…`, run-root lease `b8d8c835…`, attempt-1 snapshot
  `69505091…`, operator log `b20a9dab…`, DRYRUN `probes.stdout.log` `872a1d28…` / `manifest` `accb89b0…` /
  `report` `aa51bb0c…` / `runner_manifest` `342cbb95…`, EVIDENCE `8842d828…` / `5a6e1981…` / `cedd4c18…` /
  `dbc249db…`. So the captures are a faithful copy of the live run root.
- Cross-file consistency: runner-manifest `inputs.child_manifest_sha256`/`child_report_sha256` match the child
  manifest/report hashes (`accb89b0…`/`aa51bb0c…`, `5a6e1981…`/`cedd4c18…`); journal `unit_complete.runner_manifest_sha256`
  matches `342cbb95…`/`dbc249db…`; child `cost.gpu_seconds` matches the journal unit totals; `attempt1_input.loaded_hash.composite_sha256`
  matches `unit_start_verification.attempt1_input_composite_sha256` (`685cfe88…` / `e817addd…`).
- Child manifests are consistent with D2: `paper.commit 8309b69e`, harness `897d83c8`, `config_sha256 64073cea…`,
  `evidence_label` DRYRUN/EVIDENCE, `seed 0`, `head_form linear12`; journal `executing_files` hashes equal the 12
  live D2 files (`d3419e2d…` runner, `5679ce1b…` child, `d1c12ce6…` run.py, …), so the executed bytes are D2.
- Required Unit B outputs exist: 8 events + complete budget, both unit child manifests/reports/stdout logs, both
  runner manifests, attempt-1 provenance snapshot, run-root lease log, operator log, `SHA256SUMS`; nothing expected
  is missing and the record's capture list matches the directory.

## 6. Findings

### MINOR

**MINOR-1 — lease-log line counts lack their paths (`docs/r1/reports/TRACKP_UNITB_TASL7_D2_RESULT_20261119.md:32`).**
The sentence "lease log 111 → 117 lines" is true only for the TASL-7 **global** lease log
`/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl` (117 lines now, sha `e97e03d2…`, lines 112–117 = the six
attempt-2 entries; attempt-1 ended at line 111). The file **captured** in
`trackp_unitb_tasl7_d2_20261119T011430Z/gpu_lease_log.jsonl` is the **run-root** lease log and has **4 lines**
(sha `b8d8c835…`), while the immutable attempt-1 snapshot has **111 lines** (`attempt1_provenance/gpu_lease_log.jsonl`,
sha `69505091…`). As written, a reader comparing the record with the capture directory sees 4 lines, not 111→117.
Non-blocking documentation precision only: the numbers are individually correct and no-evidence claim is affected.
Suggested wording: "global lease log 111 → 117 lines; the run-root lease log (captured) has 4 lines; the preflight
bound the immutable 111-line attempt-1 snapshot (the growing live log is never re-hashed at unit starts)."

No BLOCKING or MAJOR findings. Two non-findings worth recording: (i) the Status line's "one GPU session" is
acceptable shorthand for **one marker-bracketed campaign on one host** (01:14:53–01:18:00), though there were two
sequential unit subprocesses and therefore two lease acquisitions (global-log lines 112 and 115); (ii) the host
still has the operator launcher `/tmp/run_unitb_d2.sh` and `/tmp/d2_wt.log` (created 01:14Z), which are outside the
run root, undisclosed in the record, non-load-bearing, and in fact corroborate the recorded command and the
detached-D2 preparation (`HEAD is now at 8309b69`).

## 7. Verdict

**ACCEPTED — 0 BLOCKING, 0 MAJOR, 1 MINOR (documentation only, non-blocking).** The result record accurately
reports the run: the D2 identity is correct and was checked out detached; the attempt-1 provenance was genuinely
re-hashed on the real host and every pinned hash, byte count and the archive/lease snapshot match; the execution is
exactly the two probes units with the expected A3/A4 results and the journal's eight events; GPU accounting
(17.7276 + 162.2841 = 130925.3907 s = 36.368 h; 8.632 h remaining) and the 111→117 global-lease growth are exact;
the captures reproduce the live run root hash-for-hash; the one operational anomaly (`${ROOT}.parent` log dir) is
disclosed and preserved; the scope statement (one host, TASL-2 fallback unused, nothing outside Unit B, no deletion)
is consistent with the host state. The MINOR is a wording precision issue only.

**Conditions (non-blocking):**
1. Acceptance is tied to the reviewed bytes: result record sha256
   `b53dbaeae3c1c94d3a6631475c7b644e7e24ba18e43b2cbef09889b4211e8819` and capture `SHA256SUMS` sha256
   `02e7c8b4a6e79e9c4772f4dbf17417e75e87ba8b0648b2c594747aedab76792d`. Commit them unchanged (as untracked →
   tracked) and do not edit the record; any byte change voids this acceptance.
2. Either fix MINOR-1 in a separately recorded erratum (cheap, one sentence) or accept it as-is; no re-review of the
   run evidence is required either way.
3. Keep `runs/p3a_attempt2_20261119T011430Z.parent/` and the host `/tmp` launcher as they are — they explain and
   corroborate the run; no cleanup/deletion is needed (or authorised here).

## Appendix — key read-only commands and results

```
# workspace / authority
git -C /Users/wongdowling/Documents/agent_paper_B rev-parse origin/main            # de3de54f…
git show de3de54f:docs/r1/PLAN.md | grep -n 'R1-TRACKP-D2\|R1-TRACKP-UNITB\|R1-TRACKP-TASL2-HOST'   # 1300 / 1246 / 1275
git rev-list --parents -n 1 8309b69e                                               # 8309b69e 9dc4afba
git show 8309b69e:r1/scripts/trackp_p3a_guarded.py | shasum -a 256                 # d3419e2d…
git diff 9dc4afba 8309b69e -- r1/scripts/trackp_p3a_guarded.py                     # one line: EXPECTED_PAPER_HEAD
cd docs/r1/reports/trackp_unitb_tasl7_d2_20261119T011430Z && shasum -a 256 -c SHA256SUMS   # 12/12 OK

# TASL-7 (read-only)
ssh -o BatchMode=yes tasl7 'git -C /home/dowling/r1_trackp/d2_20261119 rev-parse HEAD'        # 8309b69e…, DETACHED, clean
ssh -o BatchMode=yes tasl7 'sha256sum /home/dowling/r1_trackp/runs/p3a_operator_20261027/journal.jsonl'
#   1e73e80f…, 81 lines
ssh -o BatchMode=yes tasl7 'sha256sum /home/dowling/r1_trackp/backups/p3a_attempt1_final_saved_20261117T0015Z.tar.gz'
#   fa2437ee…, 328136435 B
ssh -o BatchMode=yes tasl7 'for b in kev-0.8b kev-4b qwen3.5-0.8b-base qwen3.5-4b-base; do sha256sum …/final/manifest.json …/final/saved/manifest.json …/final/saved/{adapter/*,heads.safetensors}; done'
#   all four manifests + 4 saved manifests + 16 files match the D2 pins / journal
ssh -o BatchMode=yes tasl7 'head -111 runs/gpu_lease_log.jsonl | sha256sum'   # 69505091… == snapshot; cmp identical
ssh -o BatchMode=yes tasl7 'wc -l runs/gpu_lease_log.jsonl'                   # 117
ssh -o BatchMode=yes tasl7 'cat /proc/sys/kernel/random/boot_id'              # 713ca10b-…
ssh -o BatchMode=yes tasl7 'uv pip freeze --python venvs/trackp-gpu/bin/python'   # 121 lines, sha 50238e5a…, cmp vs pin identical
ssh -o BatchMode=yes tasl7 'nvidia-smi'                                       # 43 MiB, 0 %, no compute apps
ssh -o BatchMode=yes tasl7 'ps -eo args | grep trackp'                        # none
ssh -o BatchMode=yes tasl7 'trackp-evidence status'                           # marker: absent / lease: free
ssh -o BatchMode=yes tasl7 'find runs -maxdepth 2 …'                          # run root + .parent only; attempt-1 724 files, none newer than 2026-11-17
```
