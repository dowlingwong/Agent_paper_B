# TASL-2 AR-pin host-check binding review R4 (final delta) — R3-M1 fix, 22 November 2026

**Reviewer.** Fresh independent delta reviewer (`ar-pin-binding-reviewer-r4`), delegated by the lead; no
involvement in writing the procedure, the run scripts, the binding record, its corrections, its captures or the
prior reviews. Read-only: the only file written by this review is this review (plus one transient rc-capture
redirect, `/tmp/r4_caps_check.txt`, outside the repository). No edit/commit/push/delete of any repo or host
artefact; no probe/pytest/torch execution; no GPU workload or lease; no HTCondor/deepthought/TASL-7 action. TASL-2
was inspected with read-only `ssh -o BatchMode=yes portal_zhixu` commands (`du`, `sha256sum`, `find`, `stat`);
nothing under any run root, checkout, venv, T1 `data`/`runs`/`sealed_g1b`, `~/r1_locks` or any repo was written,
and the lock file was not opened. Published-`main` state was checked read-only with `git ls-remote` and
`git show`/`cat-file` on already-fetched objects; nothing was fetched into the repository.

**Object under review.**

- Binding record `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md` —
  **185 lines, 19,538 B, sha256 `cce9b8fbf5586fe824b5016f572975a24f2b818019f627c2480f18c4650e175e`**
  (mtime `2026-11-22T16:33:28+01:00` = `15:33:28Z`); untracked (`??`) in `ops-tasl-20261116` (HEAD `b93d8c88`,
  `3c3f822a` a merge parent), and not on published `main`.
- Prior review `docs/r1/reviews/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_REVIEW_R3_20261122.md` — **247 lines,
  22,815 B, sha256 `6fd9b79c061b45a4feb484636091c0e9b9f17bc611b0b8767a0bf5022ac698e8`** (mtime `16:33:02+01:00`).
  R3 reviewed the record at **185 lines, 19,557 B, sha256 `992b2146…`**.
- Captures `TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122_captures/` — **byte-unchanged**: `SHA256SUMS`
  sha256 `1e8c6e67c014415ba28276734a6b1f6bdfd909abf702216a45a63708279441d1`, 101 files (100 hashed +
  `SHA256SUMS`).
- AR spec `sweep2/t1_tasl/g1b_tasl_ar_spec.json` — sha256
  `784d661a00633658323e77884dbce76fbc5943489612338639946430529bbd3a` (unchanged); its
  `hosts.TASL-2.isolation_host_check.record` is the record path above; `sha256` still `TODO`;
  `env_decision.authority` still `TODO`; `paper.commit` still `TODO`.
- Published `main` = **`52f4e3e564d85b61b38068112d3c8ca09d2cb424`** (`git ls-remote origin main`):
  `docs(r1): R1-G1B-AR-PY (option A)`, parent `3c3f822a`, `docs/r1/PLAN.md` +6 (the `R1-G1B-AR-PY` row); its
  commit message records the author's chat signature (22 Nov 2026, 15:40 CET).

**Verdict: ACCEPTED for the final record sha
`cce9b8fbf5586fe824b5016f572975a24f2b818019f627c2480f18c4650e175e` as a commit/citation candidate.** R3-M1 is
fixed and the delta is **byte-exact**: reversing only the C4 parenthetical edit from the current file reproduces
the R3-reviewed bytes (`19,557 B`, sha256 `992b2146…`) exactly, so no other byte changed. The corrected sentence
cites published `52f4e3e5` and names the AR-PY row, no new contradiction or **BLOCKING/MAJOR** issue is
introduced, the four `host_check_*` lines are exact, unique, column-0 and unchanged, the capture set is
byte-unchanged, and every measured claim is unchanged. The two MINOR residuals carried from R3 (R3-m1
helper-affinity wording; R3-m2 line-163 AR-ENV wording) are **unchanged by this delta and non-blocking**; the
record is usable as-is, and if the lead prefers a fully clean text those are a further edit that changes the sha.
**No re-run of the §3 host checks is required or suggested.**

## 1. The delta — byte-exact, confined to the C4 authority parenthetical

The prior bytes are not retained in the worktree (the file is edited in place), so the delta was established
mechanically: replace the two current C4 line segments with the R3-M1-era segments quoted by R3 and re-hash.

| Item | R3-reviewed bytes | Current bytes |
|---|---|---|
| record size | 19,557 B | 19,538 B |
| record lines | 185 | 185 |
| record sha256 | `992b21461fa9d4737f857f0c959e74223330a622d6c67d29d3e0385b0780d4fa` | `cce9b8fbf5586fe824b5016f572975a24f2b818019f627c2480f18c4650e175e` |

Reconstructing the R3-era file by reversing **only** the C4 edit (adding the string `(main 52f4e3e5)` after
"option A" and swapping the parenthetical back to the "not yet on published main" wording) yields **exactly
19,557 B and sha256 `992b2146…`** — the R3-reviewed object's recorded size and digest. The byte-exact
`difflib` diff (`n=0`) is therefore exactly:

```
--- R3-era (992b2146...)
+++ current (cce9b8fb...)
@@ -180,2 +180,2 @@
-- **C4 (authority wording):** this record is made under the author-signed **R1-G1B-AR-PY option A**, which amends
-  R1-G1B-AR-ENV (the AR-PY row is not yet on published main; it is to be published with this record); the earlier
+- **C4 (authority wording):** this record is made under the author-signed **R1-G1B-AR-PY option A** (main `52f4e3e5`), which amends
+  R1-G1B-AR-ENV (the AR-PY row is published on main `52f4e3e5`); the earlier
```

(Indentation in the two lines is preserved; only the parenthetical/commit-citation text changed.) Net **−19 B, 0
line-count delta**, consistent with an in-place two-line correction. **Nothing else changed**: no `host_check_*`
line, no measured value, no capture reference, no §1–§4/C1–C7 text. This is the strongest possible delta
attestation for a file whose prior bytes are not retained.

## 2. R3-M1 — item-by-item verification

| R3-M1 requirement | Delta verification | Status |
|---|---|---|
| The false parenthetical ("the AR-PY row is **not yet on published main**; it is to be published with this record") is gone | `grep` over the record finds no "not yet on published main", no "to be published with this record", no "not on main" (the only branch disclaimer is the true STOP-branch sentence on line 182). The C4 text now reads "the AR-PY row **is published on main `52f4e3e5`**". | **PASS** |
| Cite the actual publication commit `52f4e3e5` | Line 180 now carries "(main `52f4e3e5`)" and line 181 "(the AR-PY row is published on main `52f4e3e5`)". Read-only remote check: `git ls-remote origin main` = `52f4e3e564d85b61b38068112d3c8ca09d2cb424`; `git show 52f4e3e5` is `docs(r1): R1-G1B-AR-PY (option A)`, parent `3c3f822a`, adding the `R1-G1B-AR-PY` row to `docs/r1/PLAN.md`; the message records the author's chat signature. `R1-G1B-AR-ENV` (`587e4e07`) is an ancestor of `52f4e3e5`. | **PASS** |
| C4 names AR-PY | Line 180: "this record is made under the author-signed **R1-G1B-AR-PY option A** (main `52f4e3e5`), which amends R1-G1B-AR-ENV". | **PASS** |
| No new contradiction | The corrected sentence agrees with the published row (it amends `R1-G1B-AR-ENV`; option A re-points the three `bin/python*` symlinks; the host check reruns from §3) and with the record's own "Why this is a rerun" section (lines 45–59: authorised option-A fix, re-point at `2026-11-22T14:41:49Z`, repoint evidence `58d28727…`). No text now denies the AR-PY publication; the STOP-branch sentence remains true (branch `ops-t1-ar-pin-20261122` @ `9090650b`, verified present remotely; the STOP record + review and the record are **not** on `main`). The one remaining reference to the superseded row is the pre-existing line-163 "(AR-ENV)" sentence (R3-m2), unchanged by this delta and not a host-evidence or gate issue. | **PASS** |
| Four `host_check_*` lines once / values | `host_check_host: TASL-2` (9), `host_check_harness_commit: 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe` (10), `host_check_items: 1-7 PASS` (11), `host_check_verdict: PASS` (12) — each exactly once at column 0, no duplicates, no extra key. Gate `check_host_record` regex emulation over the record + spec returns exactly these four fields and no `bad`/duplicate values (spec `hostname` = `TASL-2`, `harness.commit` = `2d09f9a9…`, items/verdict `1-7 PASS`/`PASS`). Values identical to R1/R2/R3. | **PASS** |
| Captures / measured claims unchanged | Byte-unchanged capture set: `SHA256SUMS` sha256 `1e8c6e67…`; 101 files (100 hashed + `SHA256SUMS`); local `shasum -a 256 -c SHA256SUMS` **rc 0, 100/100 OK**; TASL-2 read-only `sha256sum SHA256SUMS` = `1e8c6e67…`, `du -sb captures` = **387,422 B**, file count **101**, non-`SHA256SUMS` content **349,614 B** (+ `SHA256SUMS` 9,136 B = record's **358,750 B**). Spot checks against the byte-identical captures reproduce the record's measured values: C1 `flags=0x72020000`, child `pid 1`/`ppid 0`; C2 `ptrace_scope=1`, unrelated-sibling attach errno 1; C3 `memory.max=8589934592`, `memory.swap.max=0`, `cgroup.kill exists`, child rc −9; C4 `euid 1008`, `broad_entries=[]`; C6 `tensor_sum 4096.0`, matmul `16.0`, `33,556,992 B`, torch `2.6.0+cu124`/CUDA `12.4`, lease `14:56:26Z`→`14:56:28Z` rc 0, no lease-log write; `gpu0.lock` 0 B, mtime `2026-11-22 06:58:52.391 -0800` = `14:58:52Z`; lease log mtime `2026-11-17 15:42:35` unchanged; pytest `27 passed, 1 skipped in 14.64s` rc 0, command carries **no `taskset`**; node pins `5bdce00a…`/`5c1bdf3d…`/`147f0d35…`/`55f2666a…`; data revision `915333b4…`. | **PASS** |
| Final sha suitable for the spec | `cce9b8fb…` **is** the sha256 of the current 185-line/19,538-B record bytes. Gate emulation (`check_host_record` semantics: path under `docs/r1/reports/`, digest match, four unique column-0 fields, expected values) **passes structurally**. As delivered the gate still cannot pass because the record is not yet on published `main` and the spec `sha256` is `TODO` — that is the record's stated workflow (lead commits, then fills the sha; lines 3–7, 161–162), not a content defect. Once the file is committed **byte-identically**, `cce9b8fb…` is the value for `hosts.TASL-2.isolation_host_check.sha256`. | **PASS** |

## 3. Findings

### BLOCKING

None.

### MAJOR

None. **R3-M1 is fixed**, with the byte-exact delta above; no new factual error, no new contradiction with
published `main`, and no change to the host evidence, the four gate lines or the capture basis.

### MINOR (residuals carried from R3 — unchanged by this delta, non-blocking)

- **R4-m1 = R3-m1 (helper-affinity room)** — lines 153–154 still say the helper inline Python "likewise ran with
  the delegated scope's default affinity". As R3 established, the six inline helpers run in the **top-level
  orchestration shell** (`run_all.sh:55–65` `json_flag`; `:97` `-VV`; `:333` C5 record copy; `:361` pytest-log
  parse; `:433` `venv_unchanged`; `:459` verdict read), not inside the `systemd-run --scope`; only the
  supplementary pytest is scoped. The substantive disclosure (helpers unpinned / default affinity; a
  procedure-literal deviation with no C1–C7 impact) is correct, so this is a wording room-attribution defect.
  Unchanged from R3; does not affect host evidence or the gate.
- **R4-m2 = R3-m2 (line-163 AR-ENV wording)** — line 163 "(the PLAN environment row (AR-ENV) … still required)"
  still names the AR-ENV row, while both `R1-G1B-AR-ENV` (`587e4e07`) and the amending `R1-G1B-AR-PY`
  (`52f4e3e5`) are published. This is stale/ambiguous precondition wording (the still-unfilled spec keys are the
  real "required" part); the launch gate `check_env_row` accepts either published row (neither is in
  `AR_PLAN_ROWS`, both name `ar-cond7a`), so it does not misstate a launch fact. Unchanged from R3; not a
  host-evidence defect.

Both residuals were present in the R3-reviewed bytes (proven by the byte-exact reconstruction) and are therefore
**not introduced by this delta**. Fixing either changes the sha; if the lead wants a fully clean text, do one
edit and re-hash (this review's `cce9b8fb…` would then be superseded). Neither blocks committing the record
as-is.

### Observations (no action required)

- **O1 (cosmetic)** — the corrected sentence cites the same commit twice ("(main `52f4e3e5`)" and "published on
  main `52f4e3e5`"). Redundant but accurate; no reason to re-hash for it.
- **O2 (cosmetic, R3-O3)** — the inserted text is not re-wrapped: lines 180/182/183 remain long (one line > 120
  chars). Cosmetic only.
- **O3 (operational, R3-O4)** — the local `origin/main` ref is now **`52f4e3e5`** (fetched), but the worktree HEAD
  `b93d8c88` merges `3c3f822a`, not `52f4e3e5`. The record's header "baseline `3c3f822a` merged in ops" is a true
  statement about the worktree, not a claim about published `main`. The lead should base the commit on current
  `main` (`52f4e3e5`) — fetch/merge first — so the gate's `read_main` (`git show origin/main:<path>`) sees the
  committed record. Not a record-content defect.
- **O4 (audit trail, unchanged)** — the STOP record/review and the STOP capture set remain branch-only
  (`ops-t1-ar-pin-20261122` @ `9090650bad92dbc2da254d7a793845d00fbad7ea8`, verified); the record correctly says
  `not main`. Publish them with the binding record only if the lead wants the cited trail on `main`.

## 4. Conditions (commit / gate, not host evidence)

- **RC1 (commit + spec sha).** Commit the record **byte-identically** to published `main` (base on `52f4e3e5`)
  and fill `cce9b8fbf5586fe824b5016f572975a24f2b818019f627c2480f18c4650e175e` into
  `hosts.TASL-2.isolation_host_check.sha256`; then re-run the launch precondition / `check_host_record`. Do not
  fill `992b2146…` (the superseded R3 object). **No re-run of C1–C7 is needed.**
- **RC2 (launch authority, unchanged).** `env_decision.authority` must name a published PLAN row that admits
  `ar-cond7a` and is not an `AR_PLAN_ROWS` row; both `R1-G1B-AR-ENV` (`587e4e07`) and `R1-G1B-AR-PY`
  (`52f4e3e5`) qualify. The third-note signature and `paper.commit` are still required; this record remains host
  evidence, **not** a launch authorization.
- **RC3 (scope).** §3 item 7 (CUDA IPC) remains **untested** on TASL-2 and AR option A uses none; the C1–C7 PASS
  evidence stands as reviewed. The two MINOR residuals (R4-m1/R4-m2) are non-blocking; accepting this sha does
  not assert they are fixed.

## Verdict

**ACCEPTED** for the final record sha
`cce9b8fbf5586fe824b5016f572975a24f2b818019f627c2480f18c4650e175e` as a commit/citation candidate: **R3-M1 is
fixed** (the false "not yet on published main / to be published with this record" parenthetical is replaced by
the actual citation to published `52f4e3e5`, and C4 names the AR-PY row), the delta is **byte-exact** (reversing
only that edit reproduces the R3 object `19,557 B` / `992b2146…`; net −19 B, 0 lines), there is **no
BLOCKING/MAJOR** issue and no new contradiction, the four `host_check_*` lines are exact/unique/column-0/
unchanged, the capture set is byte-unchanged (`SHA256SUMS` `1e8c6e67…`, 100/100 OK on Mac and TASL-2), the
measured claims are unchanged, and `cce9b8fb…` is the true sha256 of the current record — the value to fill into
`hosts.TASL-2.isolation_host_check.sha256` after a byte-identical commit. Two MINOR residuals carried from R3
(R3-m1 helper-affinity room; R3-m2 line-163 AR-ENV wording) remain, unchanged and non-blocking. Commit + fill +
re-run the gate; **no host-check re-run**.

---

### Reviewer's command record (22 Nov 2026, Europe/Berlin / TASL-2 PST)

- Mac (read-only): `wc -l/-c`, `shasum -a 256` and `stat` of the record, the R3 review and the spec; `shasum -a
  256 -c SHA256SUMS` in `captures/` (rc 0, 100/100 OK), recursive file count and content sum; `git status`,
  `git rev-parse HEAD/origin/main`, `git log -1 --format=%H %P`, `git merge-base --is-ancestor` (record vs
  `52f4e3e5`/`3c3f822a`, `R1-G1B-AR-ENV` vs `52f4e3e5`, STOP branch vs `main`), `git ls-remote origin main` and
  `refs/heads/ops-t1-ar-pin-20261122`, `git show 52f4e3e5 -- docs/r1/PLAN.md`, `git show 52f4e3e5:docs/r1/PLAN.md`
  grep of `R1-G1B-AR-(PY|ENV)`, `git ls-tree -r 9090650b` for the STOP record/review, `git cat-file` presence of
  the record/STOP on `52f4e3e5` (both absent); gate `check_host_record` regex emulation (Python) over the record
  + spec; the **byte-exact delta proof** (Python: reverse only the C4 edit → 19,557 B / `992b2146…`); reads of the
  record, the R3 review, `run_all.sh` (taskset/pytest/helper sections), `pytest_isolation.json`, `c6_gpu_smoke.json`,
  `c5_smoke.json`, `c4_interp.json`, `c3_cgroup.json`, `c1_userns_*`, `c2_ptrace.json`, `node_pins.json`,
  `step4_data_check.json`, `c6_gpu_lease_status.txt`, and `g1b_tasl.py` (`check_host_record`, `check_env_row`,
  `AR_PLAN_ROWS`).
- TASL-2 (`ssh -o BatchMode=yes portal_zhixu`, read-only): `du -sb captures`, `sha256sum captures/SHA256SUMS`,
  `find captures -type f | wc -l`, content-size sum, `stat` of `~/r1_locks/gpu0.lock` and the attempt-1 lease log.
  No probe, pytest, smoke, CUDA call or kit/U2 job was run on any host; the GPU lease was not taken and the lock
  file was not opened.
