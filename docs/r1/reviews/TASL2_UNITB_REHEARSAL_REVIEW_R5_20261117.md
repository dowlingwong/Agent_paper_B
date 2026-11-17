# Review R5 — TASL-2 ENGINEERING rehearsal of Unit B's exact DRYRUN invocation (revision 5)

**Status: ACCEPTED — 0 BLOCKING, 0 MAJOR, 8 MINOR (all non-blocking: none changes the command, the
authority, the clean criteria or the expected values), plus 2 observations.** This is the short
confirmation round requested after R4: the two R4 BLOCKINGs and the R4 MAJOR are closed in substance, the
command is still A2's DRYRUN minus only `--load`, the expected A3-v2 values are correct and attainable, the
GPU lease/marker semantics are now stated correctly, the scope is unchanged, and every §2 host fact still
matches. The MINORs are recording/wording gaps that R4 itself classed as "as convenient"; the unit may be
executed as written. **Review only: the unit was not executed, no host write, no commit/push, no GPU
command; read-only SSH to TASL-2 (`portal_zhixu`, user `dowling`) was used for the host facts.** The only
workspace change made by this review is this uncommitted review file.

## 0. Canonical bytes and method

| Object | sha256 / lines |
|---|---|
| **Revision-5 unit under review** | `1037043a577b0bcad848c99ba7b0ec2a0748ec26be11dc51a3eb0d0126297ea7`, **81 lines**; `docs/r1/proposals/TASL2_UNITB_REHEARSAL_20261117.md`, worktree `ops-tasl-20261116`, **uncommitted-modified** (`M`); matches the canonical value given |
| Round-4 review (re-read, sha-checked) | `9699efb6bd8eb8c9f1e4e11c2b3e0c040201f3468f0cae4898db34a6769c5c8c`, 315 lines — NOT ACCEPTED (2 BLOCKING, 1 MAJOR, 5 MINOR) |
| R4 reviewed revision-4 bytes (for the delta) | `79ec3228…`, 71 lines |
| Delivered code **D** | `8662e35991659f7a661fb7ed6be4980791d302f3`, clean on TASL-2 and on the local linked worktree `trackp-p3a-code-20261116` |
| D files compared host↔local (byte-identical) | runner `c045475b…`, child `trackp.py` `d2a30ec2…`, config `049bafed…`, `run.py` `797f00d5…`, freeze `50238e5a…` |

Host facts were re-read read-only on TASL-2 on **2026-11-17, 01:42–01:46Z** with `git --no-optional-locks`
reads (status/HEAD/rev-parse/worktree list), `sha256sum`, `find`/`ls`, `wc -l`, `nvidia-smi` queries, one
read-only `flock -n` lease probe and one read-only `git ls-remote`; no Python was run on the host, no
bytecode or index touched, no unit child started, no GPU command was issued. Code evidence was read from
the local D worktree at `8662e359` (byte-identical to TASL-2 D for every file compared). The post-review
state was re-checked at 01:46:10Z and is identical to the baseline (lease log 188 lines sha `f813ce66…`,
D status 0 lines, `FETCH_HEAD` absent, GPU 353 MiB / 0 %, 0 compute apps, no new roots).

## 1. Disposition of the R4 findings — every BLOCKING/MAJOR is closed in substance

| R4 item | Revision 5 | This review |
|---|---|---|
| **BLOCKING-1** `gpu_lease` status gate runs `git -C D fetch` → unaccounted out-of-scratch write + network; a stalled fetch would be misread as a Unit B defect | §1 (lines 19–27) now labels the lease log (+3 lines, 188→191), the two `manifest.gpu_lease` entries, and the fetch (writes the linked-worktree `FETCH_HEAD` and a loose `refs/remotes/origin/main`; **uses the network**) as **expected side effects, "recorded, not 'outside changes'"**; preflight records `git ls-remote` (remote main `26177d82…` vs local `b5a7aec…`) and the `FETCH_HEAD`/ref state before/after; a stalled fetch (`TimeoutExpired`) is an explicit **host/network STOP, not a Unit B defect**; §1 no longer says writes go only to the scratch root + lease log ("Everything **else** is written only under the scratch root"). §3.4 (line 63) excepts "the recorded lease/fetch side effects"; §3.5 (line 66) requires `FETCH_HEAD`/ref before/after in the record | **CLOSED in substance.** Code confirmed: `track_x_running` at `run.py:130–141` runs `git -C REPO fetch -q origin main` (timeout 60, `check=False`); on TASL-2 `portal_guard=True` (`run.py:183`). Host pre-state confirmed: remote main `26177d82…` (host `ls-remote`), local `origin/main` = packed `b5a7aec…`, loose `refs/remotes/origin/main` **absent**, `FETCH_HEAD` **absent** — so the fetch will write them and the record now requires capturing that. Residual wording only → MINOR R5-1/R5-2 |
| **BLOCKING-2** the lease log gains **three** lines (acquired/start/end: 188→191), not two; `manifest.gpu_lease` has **two** entries | §1 line 20–21, §3.4 line 62–63 ("gained exactly **three** lines"), §3.5 line 66 ("the three added lines") all state +3 / 188→191 and two manifest entries | **CLOSED.** Code confirmed: `run.py:200` logs `acquired`, `:211–214` `start`, `:226–228` `end` (three lines per acquisition); only `start`+`end` reach `run_log` (`:215–216`, `:230–231`) and `run_manifest` sets `gpu_lease = lease_log` (`:353`) → 2 entries. Host baseline 188 lines sha `f813ce66…` confirmed |
| **MAJOR-1** the report key is `A4_v1_raw`, not `A4_v1` | §3.4 line 60: "`A4` and `A4_v1_raw` present (there is no `A4_v1` key)" | **CLOSED.** Code confirmed: `exam_run.py:314` writes `A4_v1_raw` (renamed `pass`→`criterion_met` at `:315`), `:316` writes `A4` (v2). No `A4_v1` key exists |
| MINOR-1 `manifest.gpu_lease` parenthetical (no uuid/duration fields there) | §3.4 line 59 and line 61–62 now say GPU uuid is in `manifest.host`, duration derived | Closed in substance; clause is **duplicated** → R5-7 |
| MINOR-2 preflight pins incomplete (four family dirs, code-pin imports, D `run.py` sha) | §2/§3 still assert only the kev-0.8b base+adapter; no four-family dirs, no code-pin imports/commits, no `run.py` sha `797f00d5…` | **Still open** → R5-3 (all of these are present on the host; recording gap only) |
| MINOR-3 `<scratch>` parent unnamed | §3.1 line 53 still `…/ENGINEERING_rehearsal_<UTC>` | **Still open** → R5-5 |
| MINOR-4 STOP attribution + STOP record fields | §4 lines 73–75 add the child-path vs host/env/network triage ("child-path failure … real Unit B defect … host/env/network failure before the child … item STOP, not a Unit B defect; No retry") | Attribution **CLOSED**; STOP record fields still not enumerated → R5-4 |
| MINOR-5 clean record not enumerated | §3.5 line 66 now enumerates the record (argv/env, D shas, report/manifest sha256 + exact keys/values, lease log before/after + three lines, `FETCH_HEAD`/ref before/after, tracked/pyc/untracked/worktree/nvidia-smi, wall time, stdout/stderr + SHA256SUMS, §1 non-goal and the one difference) | Closed in substance; a few fields still missing → R5-6 |

## 2. Command, expected values, lease/marker semantics, scope — correct and unchanged

1. **Command = A2's DRYRUN minus only `--load`.** A2's child argv is built at
   `trackp_p3a_guarded.py:1202–1212` as `probes --base kev-0.8b --head-form linear12 --budget --a3-short
   --n-probe 8 --load <attempt1>/EVIDENCE/kev-0.8b/final/saved` (`DRYRUN_BASE="kev-0.8b"`,
   `DRYRUN_N_PROBE=8`, `:76,83`), and `run_unit` (`:698–699`) appends `--evidence DRYRUN --run-dir <dir>`.
   §1 line 16–17 is exactly that **minus only `--load`**, with
   `<scratch>/ENGINEERING_rehearsal_<UTC>/DRYRUN/kev-0.8b/probes` as run dir. `--load` is used only by
   `if args.load: model.load(Path(args.load))` (`trackp.py:238–239`), and the attempt-1 saved dir is
   **absent on TASL-2** (verified: `/home/dowling/r1_trackp/runs/p3a_operator_20261027` does not exist), so
   its omission is correct, recorded and cannot change another code path.
2. **Reaches the changed A3-v2 short path, not the fatal tiny path.** `_refuse_a3_short_without_budget`
   (`trackp.py:223–230`) passes (`--budget` set, `--tiny` false); `cmd_probes` sets
   `counters = _counters(cfg)` (`trackp.py:240`); `exam_run.probes` writes
   `A3.protocol = "v2_budget"` (`exam_run.py:291`) and, with `a3_short`, the exact
   `A3_descriptive = {"skipped": "R1-P3A-OOM-OPTION3", "levels": [2000, 8000], "pass": null}`
   (`exam_run.py:300–302`, `E.A3_DESCRIPTIVE = (2000,8000)` at `exam_synthetic.py:93`); the v1 0/2k/8k rows
   are unreachable in this argv. R4's CPU-only token precheck of the deterministic `n=8` A3-v2 sample
   (kev 965 < 1024; cap taken by startlux) is still valid because D is unchanged (`8662e359`) and
   `E.SEED=20261026` is fixed; it was not re-run here (short confirmation).
3. **Other expected values correct:** `manifest.evidence_label == "DRYRUN"` (`trackp.py:48–51`,
   `run_manifest`); `A1 == A2 == {"pass": null, "reason": "model does not pack …"}` for non-packing kev
   (`exam_run.py:348–349`); `A5` N/A for kev (`exam_run.py:336–337`); `report.json`/`manifest.json` written
   after a 0 rc (`trackp.py:339–340`); no `A3_errors`/`ContextOverflow` on the v2 fractions for this sample
   (R4 §1.3).
4. **GPU lease / marker semantics correct:** `_lease` (`trackp.py:92–100`) → `R.gpu_lease`
   (`run.py:179–241`) holds the ordinary `~/r1_locks/gpu0.lock` and appends to
   `…/runs/gpu_lease_log.jsonl`; on TASL-2 `portal_guard=True`, the Track X marker
   `~/r1_locks/trackx_evidence.active` is absent (verified), no marker helper exists on TASL-2, no marker is
   taken or written, and the `start` event records `trackx_marker: "absent: …"`.
5. **Scope unchanged and authority-consistent.** `R1-TASL2-UNITB-REHEARSAL` (remote main `26177d82…`,
   re-read: "在明确标为 ENGINEERING 的临时目录跑 kev-0.8b 的 DRYRUN 路径；不是 attempt-2 root，永不计入；单元先独立审查")
   still covers this. The new branch `author-decisions-20261117b` @ `33c82351…` (verified by read-only
   `ls-remote`; row absent from `origin/main` `26177d82…`) adds
   **`R1-TASL2-REHEARSAL-SCOPE`**: "TASL-2 排练照抄 Unit B 的 DRYRUN 命令（kev-0.8b、`--a3-short`、n = 8，与 A2 相同参数），
   在 ENGINEERING 临时目录运行，不用 `--tiny`；这在 R1-TASL2-UNITB-REHEARSAL（"kev-0.8b 的 DRYRUN 路径"）范围内" —
   this **confirms** the unit's scope, it does not change it. §1/§5 still say TASL-2 is ENGINEERING, not
   evidence, no attempt-2 root/table, and TASL-7's Unit B remains mandatory.

## 3. Host facts still match (read-only re-check, 2026-11-17 01:42–01:46Z)

| Unit §2 fact | Re-check |
|---|---|
| `trackp-gpu` venv, Python 3.12.15, torch 2.6.0+cu124 | **OK**: Python 3.12.15; torch 2.6.0+cu124, `cuda.is_available()=True` |
| `uv pip freeze` = 121 lines sha `50238e5a…`, byte-identical to committed freeze | **OK**: 121 lines, plain and sorted sha both `50238e5a07ca…`; host committed `pip_freeze_trackp-gpu.txt` sha `50238e5a…` → byte-identical |
| D worktree `8662e359…`, detached, clean | **OK**: HEAD `8662e359916…`; `status --porcelain -uall` = 0 lines; `git worktree list` = main `b5a7aec` + D only |
| runner `c045475b…`, child `d2a30ec2…`, config `049bafed…` | **OK**: `c045475b458b…`, `d2a30ec2c1b4…`, `049bafede821…`; `--check-config` placeholders `[]` and digest `64073cea…` recomputed from the byte-identical config (`PLACEHOLDER="TODO_VERIFY"`, `run.py:62–87`; no host execution) |
| config kev-0.8b base+adapter local paths present | **OK**: both dirs present (`…Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41`, `…jaredpalmer__kev-0.8b@788ddbdd6571`); all 8 model dirs present |
| GPU RTX 4090, driver 535.309.01, 24,564 MiB, 353 MiB / 0 %, no compute app | **OK**: identical; 0 compute apps |
| lease `gpu0.lock` free; no `*.active`; log 188 lines sha `f813ce66…` | **OK**: read-only `flock -n` FREE; Track X marker absent; log 188 lines sha `f813ce6633ff…` |
| disk 374 G free | **OK**: 374 G available (`/dev/nvme0n1p2`) |
| no `ENGINEERING_rehearsal_*` / `p3a_attempt2_*` roots; no Track P marker helper | **OK**: none under `~/r1_trackp/runs`, `~/r1_engineering` or up to depth 3; `/home/dowling/r1_locks/bin/trackp-evidence` absent |
| (needed by BLOCKING-1) `FETCH_HEAD` / ref state | **OK/new**: `FETCH_HEAD` path = `…/.git/worktrees/Agent_paper_B_D_20261117/FETCH_HEAD`, **absent**; `origin/main` exists only as packed `b5a7aec…` (loose ref **absent**); remote main via `ls-remote` = `26177d82…`; origin = `https://github.com/dowlingwong/Agent_paper_B.git` |
| (not in §2, see R5-3) code pins / `run.py` | **OK but unrecorded**: `kev`/`laya`/`startlux_decide` installed with `direct_url.json` commits `2074cc44…`, `a478221b…`, `a99977d9…` (= config `code_pins`); D `run.py` sha `797f00d5ace5f439…` |

## 4. Remaining MINOR findings (non-blocking — apply if convenient; none is a precondition)

- **R5-1 — §4's STOP list is not literally re-widened for the run's own lease fetch.** §4 (line 72) still
  reads "…(lease-log append excepted), **any other host action**". The `gpu_lease` fetch/ref write is part
  of the unit, and §1 (line 19–27) explicitly reclassifies it as an expected, recorded side effect and
  §3.4 (line 63) excepts "the recorded lease/fetch side effects", so the intent is unambiguous and the
  clean criteria are attainable; but for literal consistency add "**(the §1 recorded lease/fetch/ref side
  effects excepted)**" to §4. Conservative-direction wording only; not a false result.
- **R5-2 — §3 step 2 ("Before") does not list the preflight captures §1 promises.** §1 says "Preflight
  records `git ls-remote` …, the `FETCH_HEAD`/ref state before/after"; §3.5 requires `FETCH_HEAD`/ref
  before/after in the record, but the §3.2 baseline list (lines 54–56) mentions only "linked-worktree
  gitdir/index sha". Add to step 2: `git ls-remote origin main`, `git rev-parse origin/main`,
  `git -C D rev-parse --git-path FETCH_HEAD` (test -e), and the fetched-objects delta (`.git/objects`
  count/size before/after), so the before state is captured where the procedure says it is. Related: §1
  says the fetch "**may** write" the `FETCH_HEAD`/loose ref; with remote main `26177d82…` ahead of the
  local packed `b5a7aec…` and the loose ref absent, it **will** write both (and may download objects) —
  record the expected after-state (`origin/main` → `26177d82…`, `FETCH_HEAD` present) rather than "may".
- **R5-3 — R4 MINOR-2 is still open: preflight pins for the other families/imports/`run.py`.** §2 still
  asserts only the kev-0.8b base+adapter. `_counters(cfg)` loads tokenizers for **kev, laya, startlux,
  qwen_control** and `check_environment` imports `kev`/`laya`/`startlux_decide`; the four family dirs, the
  three code-pin commits (`2074cc44…`, `a478221b…`, `a99977d9…`, all verified present) and D `run.py` sha
  `797f00d5…` should be in the §2 fact block / §3.2 baseline / §3.5 record. Recording gap only; a mismatch
  here would be an item STOP (host/env), not a Unit B defect.
- **R5-4 — STOP record fields not enumerated.** §3.5 ends "or STOP with the enumerated fields", but the
  STOP-specific list from R4 MINOR-4 is not written out. Add: argv/env, rc, stdout/stderr, run-dir tree,
  any `report.json`/`manifest.json` written (with sha256), lease-log lines actually added (0/3, or 2 on an
  early failure end), before/after baselines including fetch/ref state, and the explicit "TASL-2
  ENGINEERING, not evidence; no retry" statement.
- **R5-5 — R4 MINOR-3 is still open: the scratch parent is unnamed.** §3.1 still says
  `…/ENGINEERING_rehearsal_<UTC>`. Name it exactly (e.g. under
  `/home/dowling/r1_engineering/unitb_rehearsal_20261117/` or `/home/dowling/r1_trackp/runs/`) so
  "must not exist", the scratch-parent listing and the before/after comparisons are unambiguous. Note the
  first candidate parent already contains four pre-existing outside-scratch files (`now.sorted`,
  `pin.sorted`, `venv_freeze_now.txt` = sha `50238e5a…`; `venv_freeze_err.txt` = sha `4f201bae…`) plus the
  D worktree; these must be part of the scratch-parent baseline.
- **R5-6 — clean-record field list still misses a few R4 MINOR-5 items.** §3.5 line 66 omits: `rc`
  explicitly; the `manifest.gpu_lease` entry fields (`event, job, pid, utc, monotonic_s, trackx_marker`;
  duration = `end.utc − start.utc`) and the `trackx_marker: "absent: /home/dowling/r1_locks/trackx_evidence.active"`
  string as the "no marker" evidence; `disk`; the `A1`/`A2`/`A5` n/a reasons; and the report/manifest
  paths. "the exact keys/values above" covers some of these ambiguously — enumerate them.
- **R5-7 — §3.4 duplicates the `manifest.gpu_lease` clause.** Line 59 ("non-empty (two entries; GPU uuid
  in `manifest.host`, duration derived)") and lines 61–62 ("has two entries with the GPU uuid in
  `manifest.host` (duration derived)") say the same thing twice inside one requirement; keep one (correct,
  no contradiction).
- **R5-8 — the unit is labelled revision 4.** Title line 1 says "Unit (revision 4)" and line 3 "Revision 4
  follows…", but these are the revision-5 bytes under round-5 review (R4 reviewed `79ec3228…`, 71 lines);
  bump the label to revision 5 (or state that this is revision-4 errata) so the review/execution records
  cite the right text.

## 5. Observations (not findings against the unit)

- **O-1 — the new authority row's last clause is broader than the unit's STOP triage.** `R1-TASL2-REHEARSAL-SCOPE`
  @ `33c82351…` says "若仍失败，即 Unit B 本身缺陷，STOP 并转 C2/D2 + 授权修订路线"; §4's triage correctly says a
  host/environment/network failure before the child is an **item STOP, not a Unit B defect**. Read "仍失败" as a
  **child-path** failure; the result record should say so explicitly (a host/env failure is not evidence
  about Unit B), and the coordinator may note the errata. The row is on the new branch, not yet on
  `origin/main` (`26177d82…`), which is consistent with the §1 "local `b5a7aec…` vs remote `26177d82…`"
  preflight fact.
- **O-2 — baseline bookkeeping.** The pre-existing `.pyc` inventory is 72 files (65 tracked
  `results/…` + 7 ignored in 4 `__pycache__` dirs) and the scratch-parent candidate holds the four files
  listed in R5-5; the §3.2 before/after captures should record these counts/shas so "no new `.pyc`" and
  "unchanged outside scratch" are objectively checkable.

## 6. Verdict

**ACCEPTED — 0 BLOCKING, 0 MAJOR, 8 MINOR (non-blocking).** The two R4 BLOCKINGs and the R4 MAJOR are
corrected in the delivered bytes: the `gpu_lease` status-gate fetch (out-of-scratch write + network) is now
recorded as an expected, captured side effect with a host/network STOP for a stalled fetch; the lease log
is stated as +3 lines (188→191, `acquired`/`start`/`end`) with two `manifest.gpu_lease` entries; the
expected key is `A4`/`A4_v1_raw` (no `A4_v1`). **The unit may be executed as written**, provided the
operator treats the §1 lease/fetch/ref side effects as the expected, recorded side effects (which §1
states) and captures them; the MINORs above are recording/editorial gaps, not preconditions. The command
is A2's DRYRUN minus only `--load` (recorded, attempt-1 `final/saved` absent on TASL-2), it reaches the
A3-v2 short path with the descriptive 2k/8k levels skipped, the GPU lease/marker semantics are correct, the
scope is unchanged and confirmed by the new authority row, and every §2 host fact still matches
(2026-11-17 01:42–01:46Z).

**The result record must contain:** unit + exact command argv and env (`PYTHONDONTWRITEBYTECODE=1
GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1`, `PYTHONPATH=.`, frozen `trackp-gpu` venv, from the D worktree);
rc 0 and wall time ≤600 s; D HEAD `8662e359…` / runner `c045475b…` / child `d2a30ec2…` / config
`049bafed…` (digest `64073cea…`, placeholders `[]`) / freeze 121 lines sha `50238e5a…` (and `run.py`
`797f00d5…` if R5-3 is applied); `<run-dir>/report.json` and `manifest.json` paths + sha256;
`manifest.evidence_label == "DRYRUN"`; `manifest.gpu_lease` two entries (`start`/`end`, each with `job`,
`pid`, `utc`, `monotonic_s`, `trackx_marker`; duration derived) and the GPU uuid/driver from
`manifest.host`; `report["A3"]["protocol"] == "v2_budget"`;
`report["A3_descriptive"] == {"skipped":"R1-P3A-OOM-OPTION3","levels":[2000,8000],"pass":null}`; `A4` and
`A4_v1_raw` present; `A1`/`A2` non-packing n/a and `A5` n/a reasons; no `ContextOverflow`/`A3_errors`;
lease log before/after 188→191 lines with hashes and the three added lines (and the
`trackx_marker: "absent: …"` string); `git ls-remote` remote main `26177d82…` vs local `b5a7aec…` and the
`FETCH_HEAD`/loose-`origin/main` state before/after the run; tracked-file/`.pyc`/untracked/worktree/
`nvidia-smi` before/after; disk; stdout/stderr and `SHA256SUMS`; the §1 non-goal (TASL-2 ENGINEERING, not
evidence, never counted, no attempt-2 root/table, TASL-7's Unit B remains mandatory) and the one recorded
difference (`--load` absent, guarded wrapper un-rehearsed); and "no retry". **If a STOP occurs, record**
argv/env, rc, stdout/stderr, run-dir tree, any report/manifest written, lease lines actually added (0/3,
or 2 on an early failure end), before/after baselines incl. fetch/ref state, and the attribution —
**child-path failure → Unit B defect → C2/D2 + `R1-TRACKP-UNITB` amendment path; host/env/network failure
before the child → item STOP (preserve/report), not a Unit B defect; no retry.**

This review did not execute the unit (or any part of it), did not write to the host, did not commit or
push, did not touch the GPU, and left the TASL-2 state unchanged.
