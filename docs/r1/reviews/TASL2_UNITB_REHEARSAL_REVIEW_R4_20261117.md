# Review R4 — TASL-2 ENGINEERING rehearsal of Unit B's exact DRYRUN invocation (revision 4)

**Status: NOT ACCEPTED — 2 BLOCKING (both are lease-semantics definitions that contradict the delivered D
bytes), 1 MAJOR (one expected report key does not exist), 5 MINOR.** The re-scoped command itself is
**correct and within authority**, and revision 4 **does avoid** the round-3 fatal finding (the tiny-kev
`--tiny`/A3-v1 `ContextOverflow`), which I re-verified from the D code path and with a CPU-only
token-count precheck of the exact `n=8` A3-v2 sample. The two BLOCKINGs are *definition-level*: the
mandated `clean` after-check/record would be false as written, and the run's own `gpu_lease` performs an
unaccounted out-of-scratch write/network action. They are small, mechanical text/allowance fixes — no
code, PLAN or authority change is needed for the rehearsal itself.

Reviewed bytes: `docs/r1/proposals/TASL2_UNITB_REHEARSAL_20261117.md`, 71 lines, sha256
`79ec3228cc5f507cf8113dd06e2eb997605210ac8164f5a2b5de08dc25564b7f` (matches the canonical value; file is
uncommitted-modified in `ops-tasl-20261116`). Prior reviews re-read and sha-checked: R1 `601a3b29…`,
R2 `8cae98de…`, R3 `2d8e79dd…` (all on the abandoned tiny-kev version). Authority re-read:
`R1-TASL2-UNITB-REHEARSAL` (`author-d8-confirm-20261117` @ `26177d82`, remote branch
`origin/author-d8-confirm-20261117`; PLAN row at that commit), `R1-TRACKP-UNITB` (main `16185b0b`),
`R1-TASL7-TRACKP`, and the Unit B definition in `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md`
(§1c.2, §2.2).

**Method (review only).** Local read of the delivered D bytes in the linked worktree
`.claude-worktrees/trackp-p3a-code-20261116` = `8662e35991659f7a661fb7ed6be4980791d302f3`
(byte-identical to the TASL-2 D checkout, see §5). Read-only SSH `ssh portal_zhixu` (user `dowling`) with
`GIT_OPTIONAL_LOCKS=0 git --no-optional-locks`, `sha256sum`, `find`, `nvidia-smi`, `flock` on a read-only
fd, and one CPU-only, no-model, no-GPU token-count precheck (§1.3; `PYTHONDONTWRITEBYTECODE=1`, stdout
only). **No unit execution, no GPU, no host writes, no commit/push.** Post-review state re-checked
identical: lease log 188 lines sha `f813ce66…`, D status clean, 0 `.pyc` newer than 00:00Z (total 72 =
the pre-existing set), no `ENGINEERING_rehearsal_*`/`p3a_attempt2_*` root, GPU 353 MiB/0 %.

---

## 1. Revision 4 fixes the round-3 central finding — CONFIRMED

R3's BLOCKING-1 was: `--tiny` forces `counters=None` (`trackp.py:240`), so `probes --tiny` takes A3 **v1**
`(0, 2000, 8000)`; the tiny kev `PointerWrapper` has `max_state=1024` and the 2k/8k rows raise an
**uncaught** `ContextOverflow` before any `report.json`/`manifest.json` (R3 §5). Revision 4 removes
`--tiny` and runs a **real** `kev-0.8b` base, so:

1. `_refuse_a3_short_without_budget` (`trackp.py:223-230`) passes (`--budget` set, `--tiny` false);
2. `cmd_probes` sets `counters = _counters(cfg) if args.budget and not args.tiny else None`
   (`trackp.py:240`) → **v2 budget path**;
3. `exam_run.probes` (`exam_run.py:282-308`) runs the four budget fractions and, with `a3_short=True`,
   sets `A3_descriptive = {"skipped": "R1-P3A-OOM-OPTION3", "levels": list(E.A3_DESCRIPTIVE),
   "pass": None}` (`exam_run.py:300-302`); `E.A3_DESCRIPTIVE = (2000, 8000)`
   (`exam_synthetic.py:93`) and `E.a3_probe` is **never called** with `a3_short` (test
   `test_a3_short_with_counters_skips_every_descriptive_call` asserts `a3_probe_calls == []`). A3 v1 is
   unreachable here (`a3_short and counters is None` is refused, `exam_run.py:270-271`), so the
   `08aeaff9` 2k/8k strict-limit path that killed R3 cannot run.

**1.3 CPU-only token-count precheck (no model, no GPU, no write) on TASL-2 of the exact `n=8` A3-v2 sample**
(`E.SEED = 20261026` is fixed and `probes()` takes no `args.seed`, so the A3 prompts/tokens are
weight-independent and identical on TASL-2 and TASL-7; `_probe_rng("A3", seed)`,
`exam_synthetic.py:332-333`):

```
POOL_LIMIT 1024 families ['kev','laya','qwen_control','startlux']
limit 1024 budget [298, 407, 346, 437, 362, 388, 331, 270]
frac 0.0  max by family {'kev': 695,'laya': 638,'qwen_control': 710,'startlux': 754}
frac 0.25 {'kev': 758,'laya': 684,'qwen_control': 773,'startlux': 817}
frac 0.5  {'kev': 830,'laya': 741,'qwen_control': 845,'startlux': 889}
frac 1.0  {'kev': 965,'laya': 854,'qwen_control': 980,'startlux': 1024}   global_max 1024
```

Kev's strict limit is `len(state)+1 > max_state` (raise), so the 1.0 row must stay **< 1024**; here kev is
965 and the 1024 cap is taken by **startlux**, not kev. This is the same structural result as the last
committed real-kev v2 report (`docs/r1/reports/trackp_e0v2_dryrun_20261026/runs/kev-0.8b/probes/report.json`:
`A3.protocol = "v2_budget"`, `A3.pass = True`, `max_tokens_by_level["1.0"].kev = 965`, startlux 1024,
`A3_errors` only `descriptive_2000/8000`). **So the mandated `A3.protocol == "v2_budget"` and the skipped
`A3_descriptive` dict are attainable on the real kev-0.8b, and R3's defect is avoided.** `_counters(cfg)`
also demonstrably works on TASL-2 (it loaded all four family tokenizers; see §5).

## 2. Command correctness — OK, and the one difference is correctly recorded

A2's DRYRUN child argv in the delivered D is produced by
`probes_only_units(...)` (`trackp_p3a_guarded.py:1202-1212`) and `run_unit` (`:698-699`, which appends
`--evidence <label> --run-dir <dir>`):

```
probes --base kev-0.8b --head-form linear12 --budget --a3-short --n-probe 8
       --load <attempt1>/EVIDENCE/kev-0.8b/final/saved --evidence DRYRUN --run-dir <root>/DRYRUN/kev-0.8b/probes
```

with `DRYRUN_BASE = "kev-0.8b"`, `DRYRUN_N_PROBE = 8` (`:76,83`). Revision 4 §1 runs exactly that command
**minus only `--load`**, with `<scratch>/ENGINEERING_rehearsal_<UTC>/DRYRUN/kev-0.8b/probes` for
`--run-dir`. The recorded reason is correct:

- the `--load` argument is `attempt1_root/"EVIDENCE"/base/"final"/"saved"` (`:1207`), i.e. a **TASL-7**
  attempt-1 EVIDENCE input; I verified the attempt-1 root and that saved dir are **absent on TASL-2**
  (`/home/dowling/r1_trackp/runs/p3a_operator_20261027/...`: no such file or directory), so the rehearsal
  cannot pass it and must not invent it;
- the base+adapter are instead loaded from the committed config's local paths
  (`_build`, `trackp.py:79-82`: `M.build_model("kev", spec["local_path"], ..., init_from=spec.get("adapter_local_path"), ...)`),
  both present (`…/Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41`, `…/jaredpalmer__kev-0.8b@788ddbdd6571`);
- `--load` is only `if args.load: model.load(Path(args.load))` in `cmd_probes` (`trackp.py:238-239`), so its
  absence changes no other code path; it only leaves `model.load()` and the attempt-1-trained head
  unexercised, which §1 correctly lists under "Not rehearsed" and says TASL-7's Unit B remains mandatory.
- `--evidence DRYRUN` is required/valid on a real base (`_evidence`, `trackp.py:48-51`;
  `EVIDENCE_LABELS` contains `DRYRUN`) and avoids needing the P.3a authorization note
  (`_require_authorization`). `--budget --a3-short` on a real base is exactly the A3-short v2 path
  (`trackp.py:240-242`).
- `python -m r1.scripts.trackp` vs the wrapper's `python <path>/r1/scripts/trackp.py` resolves identically
  (`REPO` from `__file__.parents[2]`, `PYTHONPATH=.`; `run_unit` records the same `sys.argv[1:]`), so this
  is not a behavioural difference.

**Authority check.** `R1-TASL2-UNITB-REHEARSAL` authorises an ENGINEERING rehearsal of *the kev-0.8b
DRYRUN path* in an explicitly ENGINEERING temp dir, not an attempt-2 root, never counted, review first;
`R1-TRACKP-UNITB`/attempt-2 plan §2.2 defines Unit B's DRYRUN as the short kev-0.8b changed-A3 probes run.
Rehearsing the child invocation (A2's DRYRUN minus one flag, with the wrapper and `--load` explicitly
un-rehearsed) stays inside that authority: **no PLAN or deviation change is needed**, and §1/§5 correctly
say TASL-2 is not evidence and TASL-7's Unit B remains mandatory. The one difference is clearly recorded.

## 3. Expected result values — one wrong key, one wrong parenthetical

Verified against `8662e359` code and the A3-short tests (`r1/tests/test_trackp_p3a_a3_short.py`).

| Unit expectation (§3 step 4) | Delivered D code | Verdict |
|---|---|---|
| `A3.protocol == "v2_budget"` | `exam_run.py:291` | **OK**, attainable (§1.3) |
| `A3_descriptive == {"skipped":"R1-P3A-OOM-OPTION3","levels":[2000,8000],"pass":null}` | `exam_run.py:300-302`, `exam_synthetic.py:93` | **OK** (exact) |
| `A4/A4_v1` present | code writes **`A4`** (v2) and **`A4_v1_raw`** (`exam_run.py:314-316`); there is no `A4_v1` key | **WRONG KEY — MAJOR-1** |
| A1 == A2 non-packing n/a | `exam_run.py:348-349` sets both to `{"pass": null, "reason": "model does not pack …"}` | **OK** |
| A5 n/a for kev | `exam_run.py:336-337` (family not in `qwen_control`/`qwen_reason`) | **OK** |
| `manifest.evidence_label == "DRYRUN"` | `run_manifest(evidence=_evidence(args))`, `run.py:344-353` | **OK** |
| `manifest.gpu_lease` non-empty | `lease_log` gets `start` + `end` events (`run.py:214-216, 228, 231`) → 2 entries | **OK for non-empty**, but the parenthetical "(start/end, **GPU uuid, duration**)" is wrong — see MINOR-1 |
| rc 0, `report.json` + `manifest.json` written | `trackp.py:339-340` writes both after `COMMANDS[...]` returns 0 | **OK** |
| no `ContextOverflow`/`A3_errors` | descriptive levels never attempted; v2 frac rows are within kev's limit for `n=8` (§1.3) | **OK** |

Note the A3 `pass` value and A4/A4_v1_raw `pass`/`criterion_met` are **not** required by the unit — correct,
because without `--load` the model is a fresh (seed-0) head and those numeric outcomes are not A2's.

## 4. GPU lease / marker semantics — NOT right; this is where the BLOCKINGs are

The ordinary lease is used (TASL-2, plain `trackp.py` ⇒ no Track P marker helper; `~/r1_locks/bin/trackp-evidence`
absent, no `*.active`), and no Track P marker is written. **But two lease facts are wrong:**

### BLOCKING-1 — the lease's STATUS gate performs an unaccounted out-of-scratch write + network action

`cmd_probes` takes the lease via `trackp.py:92-100` → `R.gpu_lease(...)` (`run.py:179-241`), whose first
portal guard is `portal_guard = hostname != "tasl-7"` → **True on TASL-2**, so it calls
`track_x_running(None)` (`run.py:130-141`), which runs

```
subprocess.run(["git","-C",REPO,"fetch","-q","origin","main"], check=False, timeout=60)
```

with `REPO` = the D worktree root. On TASL-2, `origin` = `https://github.com/dowlingwong/Agent_paper_B.git`
and **the fetch will write outside the scratch root and use the network**:

- `git ls-remote origin refs/heads/main` from TASL-2 returns remote main **`26177d82…`**, while the
  checkout's `origin/main` is the newer-packed ref **`b5a7aec…`** (packed-refs) — so the fetch is **not** a
  no-op: it creates a loose `.git/refs/remotes/origin/main` (`git rev-parse --git-path` ⇒
  `/home/dowling/Agent_paper_B/.git/refs/remotes/origin/main`) and downloads the intervening objects;
- `git rev-parse --git-path FETCH_HEAD` ⇒
  `/home/dowling/Agent_paper_B/.git/worktrees/Agent_paper_B_D_20261117/FETCH_HEAD` (currently **absent**),
  so the fetch creates a new file in the **worktree gitdir**, outside `<scratch>`.

Therefore §1's "**writes only in the scratch root + the shared lease log**" (§1 lines 19-20) is false for
this command, and §4's STOP "**any other host action**" would fire on the run's *own* lease code — under a
literal reading the unit can never be "clean". The before/after baselines in §3.2 (tracked-file SHA list,
`.pyc` inventory, `git status`, worktree list, scratch parent) **do not capture** `FETCH_HEAD`, the loose
remote ref or fetched objects, so the change would be invisible or (if "linked-worktree gitdir sha" is a
directory hash) would show as an unexplained change. Secondary hazard: if the fetch stalls, the uncaught
`subprocess.TimeoutExpired` (60 s, `check=False` only covers a non-zero rc, not the timeout) propagates
before the lock is taken → rc 1, no report, and the unit's STOP text would call this a "**real Unit B
defect**" although it is a TASL-2 network/lease artifact (see MINOR-4).

**Fix (definition only):** either (a) record the fetch as an expected lease side-effect with before/after
captures — `FETCH_HEAD` path/absence, `git rev-parse origin/main` before `b5a7aec…` and after (remote
`26177d82…`), `git ls-remote` sha, objects delta, and "network fetch by `gpu_lease` on a non-TASL-7 host" —
and widen §1/§4's allowance accordingly; or (b) **prime** the identical fetch during the §3.2 *before*
baseline (recorded), then re-baseline, so the run's fetch is content-idempotent, and still record the
`FETCH_HEAD`/`origin/main` values. Also add a preflight `git ls-remote origin main` (network present) and
note the uncaught-timeout path. §1 must stop saying "writes only in the scratch root + the shared lease
log".

### BLOCKING-2 — the lease log appends **three** lines, not two

D `gpu_lease` logs `{"event":"acquired"}` (`run.py:200-201`) **and** `{"event":"start"}` (`:211-214`) **and**
`{"event":"end"}` (`:226-228`) per successful acquisition; only `start`+`end` are appended to `run_log` (`:216`, `:231`)
(hence `manifest.gpu_lease` has 2 entries). So from the baseline **188 lines / sha `f813ce66…`** the run will
produce **191 lines (+3: acquired, start, end)**, not +2. (The old 26 Oct tail in the same log shows
start/end only because it predates `08aeaff9`; that is likely where the "two" came from.)

**Fix:** in §3.4 and §5 replace "the lease log's two appended lines" with "the lease log gains three lines
(acquired, start, end: 188→191); `manifest.gpu_lease` has two entries (start, end)"; keep the STOP exception
for "lease-log append" (any of those three lines).

**Marker semantics otherwise correct:** no marker helper is invoked by the bare CLI and no marker is
created; the lease additionally *checks* the Track X marker `~/r1_locks/trackx_evidence.active` (absent) and
records `trackx_marker: "absent: …"` in the `start` event — capture that string in the record as the
"no marker" evidence.

## 5. Host facts re-checked read-only (2026-11-17, 01:33–01:55Z; unit's facts were 00:12–00:25Z)

| Unit §2 fact | Re-check |
|---|---|
| venv `…/venvs/trackp-gpu`, Python 3.12.15, torch 2.6.0+cu124 | OK (`uv 0.13.6`; Python 3.12.15; torch 2.6.0+cu124, `cuda.is_available()=True`) |
| `uv pip freeze` 121 lines sha `50238e5a…`, byte-identical to committed freeze | **OK**: 121 lines, sorted sha `50238e5a07ca…`, identical to `…/pip_freeze_trackp-gpu.txt` (host file sha `50238e5a…`) |
| D worktree detached `8662e359…`, clean | **OK**: HEAD `8662e359916…`, `git status --porcelain -uall` = 0 lines; linked worktree of `/home/dowling/Agent_paper_B` (`git rev-parse --git-common-dir` = `/home/dowling/Agent_paper_B/.git`) |
| runner `c045475b…`; child `trackp.py` `d2a30ec2…` | **OK**: `c045475b458b…`, `d2a30ec2c1b4…` |
| config `049bafed…`, `--check-config` placeholders `[]`, digest `64073cea…` | **OK**: `049bafede821…`; `placeholders: []`; digest `64073ceaa266…` |
| config `bases.kev-0.8b` local base+adapter present | **OK**: both dirs present (`…Qwen__Qwen3.5-0.8B-Base@dc7cdfe2ee41`, `…jaredpalmer__kev-0.8b@788ddbdd6571`) |
| GPU RTX 4090, driver 535.309.01, 24,564 MiB, 353 MiB/0 %, no compute app | **OK**: identical (353 MiB, 0 %, no compute apps) |
| lease `~/r1_locks/gpu0.lock` free; no `*.active`; log 188 lines sha `f813ce66…` | **OK**: read-only `flock -n` FREE; no `*.active`; 188 lines, sha `f813ce6633ff…` |
| disk 374 G free | **OK**: 374 G available (`/dev/nvme0n1p2`) |
| no `ENGINEERING_rehearsal_*`/`p3a_attempt2_*` roots; no Track P marker helper | **OK**: none; `/home/dowling/r1_locks/bin/trackp-evidence` absent |
| (not in §2) `_counters` inputs / code pins | **OK but unrecorded**: all seven model dirs present, incl. laya `rl_agent_config.json`+`tokenizer`; `kev`/`laya`/`startlux-decide` `direct_url.json` commits = config pins (`2074cc44…`, `a478221b…`, `a99977d9…`), all import |
| (not in §2) `origin/main`/network state | **NEW**: `origin/main` `b5a7aec…` vs remote `26177d82…`, network reachable, worktree `FETCH_HEAD` absent (BLOCKING-1) |

Also recorded but not in the unit: D `r1/c3/train/run.py` sha `797f00d5ace5f439…` (the file that implements
`gpu_lease`/`run_manifest`) — recommend adding it to the D pin list so the lease/record behaviour is pinned
(MINOR-2). The attempt-2 plan's `--load` target `…/p3a_operator_20261027/EVIDENCE/kev-0.8b/final/saved` is
absent on TASL-2, as §1 states.

## 6. STOP / defect path — broadly right, needs an attribution clause

§1/§4 are correct that: any failure **STOPs, preserves, reports, no retry**; there is no host blast radius
(§5: no deletion, no other host/user, no attempt-2 root, no evidence label/table, no push, TASL-2 not
evidence, TASL-7's Unit B remains the evidence run); and `ContextOverflow`/missing `A3.protocol=v2_budget`/
missing skipped marker/no report/OOM/CPU-fallback are the right triggers. Two gaps:

- **MINOR-4:** the text makes *every* `rc != 0` / no-report a "**real Unit B defect**" that invokes
  C2 + a new D2 + the `R1-TRACKP-UNITB` amendment. But several failure causes are TASL-2-only, not Unit B
  defects: `check_environment` pin/venv mismatch, missing model/tokenizer dir, the lease's `git fetch`/
  `TimeoutExpired` or Track X STATUS guard, `nvidia-smi`/lock failure, `_counters` tokenizer load. Add a
  triage: a failure attributable to the **child code path** (ContextOverflow in an A3-v2 frac row, missing
  `protocol`/marker, child traceback in `probes`) → Unit B defect → C2/D2/amendment path; a **host/
  environment/lease** failure → rehearsal STOP (preserve/report) **without** declaring a Unit B defect.
- **MINOR-4 (same fix):** the STOP record fields are not enumerated (unlike §3.5 for clean): require argv/env,
  rc, stdout/stderr, run-dir tree, any report/manifest written, lease lines actually added (0/3), before/after
  baselines, fetch/ref state, and the explicit "TASL-2, not evidence; no retry" statement.

## 7. Objective clean criteria — right in substance, three gaps

Correct as written: rc 0; report+manifest exist with recorded sha256; `evidence_label == "DRYRUN"`;
`A3.protocol == "v2_budget"`; the exact `A3_descriptive` dict; A4/A4_v1_raw; A1==A2 n/a; A5 n/a; no
`ContextOverflow`/`A3_errors`; wall time ≤600 s (the delivered wrapper itself projects 600 s for this
DRYRUN, `trackp_p3a_guarded.py:85`; the historical attempt-1 kev probes lease window was ~33 s, so the bound
is ample); no new `.pyc` (`PYTHONDONTWRITEBYTECODE=1`); no tracked-file change; no other worktree; lease
released; disk tolerance; "ENGINEERING on TASL-2, not evidence; nothing counts toward the P.3a budget/tables"
and "no-GPU-evidence claim" avoided (§1, §5). Gaps:

- **BLOCKING-1 / BLOCKING-2** above: "no-outside-scratch except lease log" and the lease-log count/expected
  fields are wrong.
- **MINOR-3:** `<scratch>` is `<…>/ENGINEERING_rehearsal_<UTC>` with an unspecified parent. Name it exactly
  (e.g. `/home/dowling/r1_trackp/runs/ENGINEERING_rehearsal_<UTC>` or
  `/home/dowling/r1_engineering/ENGINEERING_rehearsal_<UTC>`) so the "must not exist", scratch-parent listing
  and before/after comparisons are unambiguous; the authority only requires an explicitly ENGINEERING temp
  dir that is not an attempt-2 root.
- **MINOR-5:** §3.5's clean record is "all shas/captures/SHA256SUMS and the §1 non-goal" — enumerate the
  required fields, e.g.: scratch root; argv/env; rc; wall_s; `<run-dir>/report.json` + `manifest.json`
  sha256; `A3.protocol`; the exact `A3_descriptive` dict; presence of `A4` and `A4_v1_raw`; `A1`/`A2`/`A5`
  reasons; `manifest.evidence_label`; `manifest.gpu_lease` entries (start/end, utc, monotonic_s — not uuid);
  `manifest.host` GPU uuid/driver; lease-log before/after (188→191) with sha; `trackx_marker: "absent: …"`;
  before/after baselines unchanged; the §1 difference (`--load` and wrapper not rehearsed; TASL-7 remains
  mandatory).

## 8. Findings and exact fixes

**BLOCKING-1 (lease STATUS gate writes outside the scratch root).** `gpu_lease` → `track_x_running` runs
`git -C D fetch -q origin main` on TASL-2; on these hosts it downloads objects and writes the worktree
`FETCH_HEAD` plus a loose `refs/remotes/origin/main` (b5a7aec→26177d82) under
`/home/dowling/Agent_paper_B/.git/…`, and uses the network. §1's "writes only in the scratch root + the
shared lease log" is false and §4's "any other host action" would flag the run's own lease. A stalled fetch
(non-zero rc is swallowed; a 60-s timeout is not) would crash before the lock and be misread as a Unit B
defect. *Fix:* record the fetch + its before/after ref/FETCH_HEAD/objects values as an expected lease
side-effect and widen §1/§4; or prime the identical fetch in the before-baseline and re-baseline (still
record it); add a preflight `git ls-remote` and the timeout caveat.

**BLOCKING-2 (lease log +3, not +2).** `acquired`+`start`+`end` are all appended by `run.py:200-229`, so
188→191 lines; `manifest.gpu_lease` has 2 entries. *Fix:* correct §3.4/§4/§5 wording to three lines and
state the manifest has two entries.

**MAJOR-1 (`A4_v1` does not exist).** The report key is **`A4_v1_raw`** (v1 criterion, renamed
`pass`→`criterion_met`, `exam_run.py:314-315`) plus **`A4`** (v2, `:316`). *Fix:* §3.4 "A4/A4_v1 present" →
"A4 (v2) and A4_v1_raw present"; do not add a STOP for a missing `A4_v1`.

**MINOR-1 (`manifest.gpu_lease` parenthetical).** Entries are `{event, job, pid, utc, monotonic_s,
trackx_marker, tasl7_driver}` — **no GPU uuid and no duration field**; the GPU uuid is in `manifest.host`
(`host_record`, `run.py:319+`), and duration = `end.utc − start.utc` (or monotonic_s). *Fix:* correct the
§3.4 parenthetical and require those fields.

**MINOR-2 (preflight pins incomplete).** `_counters(cfg)` loads tokenizers for **kev, laya, startlux and
qwen_control** (and laya's `rl_agent_config.json`), and `check_environment` imports `kev`/`laya`/
`startlux_decide`; §2 only asserts the kev-0.8b paths. *Fix:* add all four family model dirs, the three
code-pin imports/commits (present: `2074cc44…`, `a478221b…`, `a99977d9…`) and the D `run.py` sha
(`797f00d5…`) to the preflight/baseline record.

**MINOR-3 (scratch parent unnamed).** Name the exact scratch parent path.

**MINOR-4 (STOP attribution + STOP record fields).** Add the child-path vs host/environment/lease triage
before invoking the C2/D2/amendment path, and enumerate the STOP record fields (as in §6).

**MINOR-5 (clean record not enumerated).** Enumerate the mandated captures/expected values (as in §7).

## 9. Verdict

**Not accepted — 2 BLOCKING, 1 MAJOR, 5 MINOR.** The unit **must not be executed as written**: the mandated
`clean` after-check/record is false in two code-verified respects (lease log gains three lines, not two; the
run's own `gpu_lease` fetches and writes git refs/`FETCH_HEAD` outside the scratch root while §1 says it
writes only in the scratch root + the lease log), and one expected key (`A4_v1`) does not exist. All fixes
are definition/text/allowance-level — no code, PLAN or authority change is required for the rehearsal.

The re-scope itself is sound and stays inside `R1-TASL2-UNITB-REHEARSAL`: the command is A2's DRYRUN minus
`--load` (clearly recorded, `--load` target correctly absent on TASL-2), it reaches the changed A3-v2 path
with the descriptive 2k/8k rows skipped, the real kev-0.8b v2 rows fit the 1,024-token limit for the exact
`n=8` deterministic sample (kev 965; cap taken by startlux), `_counters`/code pins/model dirs are all
available, and revision 4 therefore **avoids R3's fatal tiny-kev `ContextOverflow`**. After the two
BLOCKINGs and MAJOR-1 are corrected (MINORs as convenient), the unit may be executed as corrected; the
result record must contain the captures/shas/expected values enumerated in §7 MINOR-5 (in particular
`A3.protocol="v2_budget"`, the exact `A3_descriptive` skipped marker, `A4`+`A4_v1_raw`, `A1`/`A2`/`A5` n/a,
`evidence_label="DRYRUN"`, the two `manifest.gpu_lease` entries, the 188→191 lease-log lines with sha, and
"TASL-2/ENGINEERING, not evidence"). A short R5 confirmation of the corrected definitions (or
coordinator-recorded errata with the re-check) is needed before execution; this review did not execute the
unit, touch the GPU, or write to the host.
