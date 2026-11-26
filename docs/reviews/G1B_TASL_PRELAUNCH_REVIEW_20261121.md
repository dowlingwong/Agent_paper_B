# G.1b TASL pre-launch package — independent review (21 November 2026)

**Reviewer.** Fresh independent reviewer (`g1b-tasl-prelaunch-reviewer`), delegated by the lead; no involvement in
writing the pre-launch report, the host-check bindings, the T1 prechecks, the specs, the plan or the wrapper.
**Read-only: the only file written is this review.** No run, no edit of the package, no commit/push/delete, no
HTCondor/deepthought action. Hosts were read-only inspected (`ssh -o BatchMode=yes`, commands in §8); no file was
created, changed or deleted on a host, and no GPU workload, server start/stop or lease was taken.

**Object under review.** Worktree `.claude-worktrees/main_t1_host_reports_20261121`, branch
`main-t1-host-reports-20261121` at HEAD `aaf2254a` on baseline `main` `d47d1008` (plus the uncommitted work below).
Files and the sha256 values used in this review:

| object | path | sha256 | state |
|---|---|---|---|
| pre-launch report | `docs/r1/reports/trackg_g0_20261117/G1B_TASL_PRELAUNCH_20261121.md` | `f5b3299b…b685107` (f5b3299baa2beb3356f1dc19b103353222122f7b406434699b8baf31be685107) | untracked |
| TASL-2 binding | `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md` | `681011b2…42d7b6b6d` (681011b2114f6ff7db679d3265535d1cc2e8a9bdbc231371230f4de42d7b6b6d) | untracked |
| TASL-7 binding | `docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md` | `09945c15…be4576a4` (09945c15df67b2627a97e6cc59239744738aecb14e522f7c52d1f390be4576a4) | untracked |
| TASL-2 original | `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_20261121.md` | `83636c03…d7a5bb6` | at `aaf2254a` |
| TASL-7 original | `docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_20261121.md` | `2b703226…40f2abf` | at `aaf2254a` |
| TASL-2 precheck + captures | `docs/r1/reports/trackg_g0_20261117/TASL2_T1_PRECHECK_20261121.md`, `…_captures/` | captures `SHA256SUMS` `e604aff7…985eaf`, 91/91 OK | untracked |
| TASL-7 precheck + captures | `docs/r1/reports/trackg_g0_20261117/TASL7_T1_PRECHECK_20261121.md`, `…_captures/` | captures `SHA256SUMS` `19c4f657…11d3e8a`, 170/170 OK | untracked |
| G.1b spec | `sweep2/t1_tasl/g1b_tasl_spec.json` | `2f0bdd70…aeadb` (2f0bdd70399c7ec24a9f91de1e00e96fba4d8682e666ff51352d09ea5e3aeadb) | modified (`M`) |
| G.4 spec | `sweep2/t1_tasl/g4_tasl_spec.json` | `fd5a14b5…1b6b` (fd5a14b51463d5658dc1833b1e6805f5b4241078ec3fa813a9a14df833ba1b6b) | modified (`M`) |
| dry-run wrapper | `sweep2/t1_tasl/dry_run_node.py` | `a12d349b…44d8e` (a12d349b80d309a399f55562f4b91684be8cf2fc9d662b8a005a219172144d8e) | untracked |
| plan | `sweep2/t1_tasl/T1_TASL_PLAN.md` | `fc5606ae…f2867c` (cited consistently by both prechecks) | committed |

Review basis: `main` baseline `d47d1008`; the package is **ENGINEERING_ONLY and pre-launch** — no EVIDENCE run, no
signed note. The review answers one question: is this package acceptable as (a) the basis for the described
ENGINEERING dry-runs, and (b) the record from which a G.1b/G.4 EVIDENCE launch could be signed.

---

## Verdict

**NOT ACCEPTED** as the launch-enabling pre-launch package. One **BLOCKING** finding: the package does not implement,
plan or even mention a check that the author's own authority row **R1-T1-TASL-ENV** requires before the three
TASL-7 G.1b noise floors can be used (finding **B1**). The description of the ENGINEERING dry-run is otherwise
consistent and does not need B1; after the small dry-run text/procedure fixes (**m5**, **m6**) the dry-run may
proceed. EVIDENCE launch is not acceptable until **B1** and **M1** are closed and the conditions in §7 are met and
this record is re-reviewed.

The package's *factual claims about what was measured* largely check out against the delivered captures and, where
they could be tested live, against the hosts read-only (§5, §8). The failure is scope/authority completeness, not
fabricated evidence.

---

## Findings

### B1 — BLOCKING (before any TASL-7 G.1b EVIDENCE run). The R1-T1-TASL-ENV cross-host default check is absent from the package.

The adopted authority row `R1-T1-TASL-ENV` on published `main` (`d47d1008`, `docs/r1/PLAN.md:1352`) says, verbatim:

> "The G.1b nodes measured on TASL-7 also run their default parts on TASL-2, and the metrics must be identical, else
> STOP and that node's G.1b is re-measured on TASL-2."

The row's basis (`docs/r1/proposals/T1_TASL_ROWS_DRAFT_20261121.md` §3a, option A — the adopted option) is explicit
that this is **not built yet**:

> "Each TASL-7 node's `default` and `default_repeat` parts (2 × 5 runs, fixed seeds) also run on TASL-2; the metrics
> must equal the TASL-7 values bit for bit, otherwise STOP … **Not built yet: a small reviewed addition to
> `g1b_tasl.py` (a `crosscheck` job reading the sealed TASL-7 default rows), which also needs the jax312 environment
> on TASL-2 in the G.1b spec** (the G.4 spec already requires it there)."

The rationale is the one the draft gives: the three TASL-7 nodes (`mlab_cifar10`, `mlgym_cifar10`,
`mlgym_breakout_minatar`) would have their noise floor on driver 580 while G.4/G.5 labels run on TASL-2 driver 535;
R1-S2C3-ACCEPT shows a driver/GPU-stack difference changes numbers, and the draft records that Breakout's metrics may
legitimately differ (its jax312 has no `ptxas`).

The package under review is silent on all of this:

- `grep -rn "crosscheck\|cross_host\|cross-host" sweep2/t1_tasl/ sweep2/g1b/` → **no hit**; `g1b_tasl.py` has no
  `crosscheck` subcommand and `assemble()` does not compare TASL-7 default rows against a TASL-2 re-run;
- `sweep2/t1_tasl/g1b_tasl_spec.json` `hosts.TASL-2.env_python` = `{torch312}` only — the jax312 environment the row
  draft requires on TASL-2 for the G.1b crosscheck is not declared (it is declared only in the G.4 spec's
  `worker.env_python`, and the host-level jax312 env does exist on TASL-2 per the TASL-2 precheck);
- the pre-launch report, both TASL prechecks and the plan mention the driver difference only as a fact
  (`G1B_TASL_PRELAUNCH_20261121.md:13` records the two driver versions) and never state the cross-host check, its
  STOP rule or the re-measure-on-TASL-2 fallback;
- the dry-run plan does not include it (see m6).

Consequence: a G.1b launch from this package would measure the three TASL-7 noise floors on driver 580 without the
identity check the author required, and would not satisfy its own cited authority row; if the metrics in fact differ
on Breakout (as the draft anticipates), the node must be re-measured on TASL-2, not accepted. This is a scientific
comparability requirement for the noise floors, not an optional extra.

**Fix before EVIDENCE (and before the three TASL-7 nodes launch):** implement and independently review the
`crosscheck` job — read the sealed TASL-7 `default`/`default_repeat` rows (10 fixed-seed rows per node), re-run
exactly those on TASL-2 with the identical spec/environment (torch312 for the two CIFAR nodes; jax312 for Breakout,
with the TASL-7 `XLA_FLAGS` irrelevant on TASL-2 and the environment built from the same freeze), compare the metrics
bit for bit, STOP on any difference; add `jax312` to `hosts.TASL-2.env_python` in the G.1b spec; add the step to
`T1_TASL_PLAN.md` and to the pre-launch report's launch sequence, and to the G.1b/JDL-free host run order; re-take
the spec shas and the launch record. Alternatively the author must record a new PLAN amendment choosing draft §3a
option B (all noise floors on TASL-2) or C (disclosed only). B1 does not block the described ENGINEERING dry-runs
(they are explicitly not noise floors and produce no EVIDENCE), but it must be closed before the dry-runs are used to
justify the EVIDENCE launch.

### M1 — MAJOR (before the TASL-7 `mlgym_breakout_minatar` EVIDENCE node). The jax312 + `XLA_FLAGS` path has no end-to-end sandboxed evidence on TASL-7, and the §6 table overstates it.

- TASL-7 J1a (`c6b_jax_gpu.json`) **FAILS as configured**: `XlaRuntimeError … Couldn't find a suitable version of
  ptxas` (the census jax312 freeze has no `nvidia-cuda-nvcc-cu12`; TASL-7's toolkit is `/usr/local/cuda-12.2` with no
  `/usr/local/cuda` symlink). J1b (`c6b_jax_gpu_xla_cuda_dir.json`) **PASSES only with**
  `XLA_FLAGS=--xla_gpu_cuda_data_dir=/usr/local/cuda-12.2 --xla_gpu_deterministic_ops=true`, in a delegated
  `systemd-run --user --scope`, **outside** the `WorkingCopyRunner` worker sandbox.
- The sandboxed jax smoke (`TASL2_T1_PRECHECK_20261121_captures/c6b_jax_gpu_smoke.json`, `effective:true`) is on
  **TASL-2** (which does not need the flag), not on TASL-7. TASL-7's only sandboxed smoke is the non-GPU `g0` smoke.
- The mechanism is otherwise sound and was checked in the captured harness units: `_sandbox_config` binds `/usr`
  read-only (so `/usr/local/cuda-12.2` is visible inside the sandbox) and the sandboxed-worker environment keep-list
  `_ENV_KEEP_PREFIXES` includes `XLA_` (`TASL7_T1_PRECHECK_20261121_captures/scripts/unit_ar_isolated.py:107-110`);
  `g1b_tasl.run_node_job` applies `hosts.*.extra_env` to the environment before the engine (so the spec's `XLA_FLAGS`
  is set), and TASL-2 proves the same worker code runs jax under the sandbox. The risk is therefore low but the exact
  460-run path has never been executed.
- The pre-launch report's §6 table row is imprecise: line 56 reads `GPU-in-sandbox smoke | PASS | PASS (jax GPU smoke
  too)` while J1a failed and J1b passed only with the host adaptation and outside the sandbox. P1 (lines 40-43)
  discloses the flag, but the table cell is what a reader will quote.

**Fix/condition:** add `mlgym_breakout_minatar` to the TASL-7 dry-run set (it exercises `extra_env` → sandbox →
jax312 → XLA at the pin; the default part is 10 runs), or record a sandboxed jax312 GPU smoke at `c025f89a` on
TASL-7 with `XLA_FLAGS` set through the spec's `extra_env`; and correct the §6 cell (e.g. "GPU-in-sandbox smoke PASS;
jax312 GPU smoke J1a FAIL as configured / J1b PASS with the host `XLA_FLAGS`, outside the sandbox").

### m1 — MINOR (text, before the TASL-2 binding is published/cited). "All seven passed" vs item-7 CUDA IPC untested.

`TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md:16-20` says "…and **all seven passed**, with no waiver", while its own
C6 row (line 54) says "GPU smoke with the sandbox on (GPU-in-sandbox prerequisite; **not §3 item 7 CUDA IPC**)" and the
two founding reviews require the report not to be cited as a §3 item 7 pass (TASL-2 review condition C1:
"§3 item 7 CUDA IPC is **UNTESTED** and §5 item 5/§5.5 remain open; no node using `cuda_share`/`cuda_open` may start on
the strength of this report"). The TASL-7 binding handles this correctly with an explicit item-7 paragraph
(`TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md:26-33`), and the pre-launch report itself discloses the limit
(`G1B_TASL_PRELAUNCH_20261121.md:22-23`: "CUDA IPC remains untested (§5.5 open) and is not used"). **Fix:** give the
TASL-2 binding the same up-front paragraph (six §3 conditions PASS + GPU-in-sandbox prerequisite; item 7 CUDA IPC
UNTESTED; "1-7 PASS" is the launch-schema value; AR option A only; no `cuda_share`/`cuda_open` node on this record).
If the text changes, re-take the binding sha and update `hosts.TASL-2.isolation_host_check.sha256` in both specs
(`g1b` and `g4.worker`), and re-take the pre-launch report's quoted sha.

### m2 — MINOR (text). TASL-7 precheck misstates the build-dir manifest breakdown.

`TASL7_T1_PRECHECK_20261121.md:153` says "24 lines (23 entries: **6 symlink lines + 17 regular files** …)". The
captured `proposer/bin_manifest.txt` has **14 `link` lines + 9 regular-file lines = 23 entries (+1 digest line = 24
lines)**; `bin_dir_listing.txt` agrees (14 symlinks, 9 files). The digest `a29c667f…` (sha256 of the 23 entry lines +
trailing newline), the file sha `52561323…` and the pre-launch report's "23 entries" are all correct; only the
breakdown sentence is wrong. Fix in the precheck report (not bound by a spec).

### m3 — MINOR (text; before EVIDENCE). The launch-commit sentence is wrong as written.

`G1B_TASL_PRELAUNCH_20261121.md:16-18`: "Paper commit in both specs: `d47d1008…` (main baseline). A launch commit
must be the branch commit once these specs/reports are committed; **this pre-launch engineering run uses the specs as
committed here**." The specs/reports are uncommitted (`git status`: two `M`, the rest `??`), and `d47d1008` cannot be
the launch commit: `g1b_lib.verify_launch` (`sweep2/g1b/g1b_lib.py:264-286`) requires the checkout HEAD to equal
`spec.paper.commit` **and** be tracked-clean, while `check_note` (`sweep2/t1_tasl/g1b_tasl.py:882-901`) requires the
note's `paper_commit` = `spec.paper.commit`, `spec_sha256` = the staged spec's sha, and the note byte-identical on
`origin/main`; `check_host_record` reads the binding from `origin/main`. So the pre-EVIDENCE sequence must be: commit
the specs/reports/note (and `dry_run_node.py` if used); stage a spec whose `paper.commit` is the launch commit;
sign the note with that commit and the staged spec's sha; push to `main`; launch from a clean checkout at the launch
commit with the staged spec. Replace "as committed here" with "as written here" and spell the staging step out.
(Dry-runs are unaffected: `run_node_job` never calls `verify_launch`, the note check or `check_host_record`.)

### m4 — MINOR (authority wording; before EVIDENCE). The signed note does not name the harness commit.

`R1-T1-TASL-ENV` says "Harness at the commit the signed note names, clean." Neither TASL note template
(`g1b_tasl_authorization.template.md`, the G.4 block) nor either `check_note` has a `harness_commit` field
(`g1b_tasl.py:899-901`, `g4_tasl.py:705-707`), unlike the H200 template. The harness *is* effectively bound (the spec
sha, which the note carries, pins `harness.commit`, and the host-check lines must name it), so this is a wording /
defence-in-depth gap rather than an unbound pin. **Fix:** add `harness_commit: <pin>` to both templates and to the
`want` dicts (require equality with `spec.harness.commit`), or record the interpretation in the plan/row.

### m5 — MINOR (dry-run procedure). The wrapper is not named, does not create the scope, and its row count is wrong.

`G1B_TASL_PRELAUNCH_20261121.md:74-81` describes the dry-runs as "via a documented partial-part wrapper around the
pinned `run_node_job`". The wrapper is `sweep2/t1_tasl/dry_run_node.py` (new, untracked), and:

- the pre-launch report does not name it (a reader cannot find the procedure);
- `dry_run_node.py` alone does **not** create the delegated `systemd-run --user --scope` (`AR_TEST_CGROUP_PARENT`,
  8G/swap0) nor set `taskset` cpus or `G1B_TASL_NODE_LOG`; `run_node_job`'s preflight will STOP without the scope env.
  The exact invocation (the `t1_tasl_node.sh` equivalent for the wrapper) must be documented;
- `dry_run_node.py` does not run `seal`; the report claims the dry-runs exercise "seal". Document the follow-up
  `python3 sweep2/t1_tasl/g1b_tasl.py seal <attempt-dir> <spec> --node <node>` (the wrapper's record carries
  `dry_run_partial: true`; `seal` does not check the row count, so this works);
- line 34 comment says "one default part only (**184 rows**)". One default part is **10 runs** (2 conditions × 5
  configs; 460 = 10 + 150 + 150 + 150). `partial_merge` itself merges correctly and skips the 460-row check; only the
  comment is wrong.

Fix the comment and add the exact scope + seal commands to the report (and to the wrapper's docstring), name the
wrapper, and track the file if it is part of the package.

### m6 — MINOR (dry-run coverage). The one-node-per-host set skips the two special environments; add the cheap ones.

The planned set is TASL-2 `mlab_ogbn_arxiv` and TASL-7 `mlab_cifar10` — both torch312/GPU/`cpus 0-7`. It does not
exercise the CPU node's `cpus 8-15` path (`mlgym_houseprice`, `device: cpu`, `cpus` disjoint from the GPU jobs) nor
the jax312 + `XLA_FLAGS` path (Breakout; M1). A default part is 10 runs, so adding both costs a few minutes each and
turns the dry-run into a real pre-EVIDENCE check of the two host adaptations. Recommended: dry-run
`mlgym_houseprice` on TASL-2 and `mlgym_breakout_minatar` on TASL-7 as well.

### m7 — MINOR (evidence). The G.4 Tailscale DNS-name claim was not captured; the name-bind path is untested.

`G1B_TASL_PRELAUNCH_20261121.md:66-72` claims `tasl-7.tail119748.ts.net` "resolves `.51` on TASL-7 for bind and `.50`
on TASL-2 for the client" and that the delivered bind test verified it. The delivered bind test/smoke bound the
**literal** `100.106.74.51` (`bind_test/bind_test_result.json`, `server.host: 100.106.74.51`; smoke argv `--host
100.106.74.51`), and no `getent`/resolution capture exists in either TASL precheck bundle. I verified the resolution
read-only at review time (§8): TASL-7 → `100.106.74.51`, TASL-2 → `100.106.74.50`, so the claim is true today; add
those two outputs (and the port to 8095) to the record. The spec's `serve` binds `--host
tasl-7.tail119748.ts.net` (the name), which no delivered test has exercised — confirm at G.4 start that the server
starts and listens on `.51` with the name (the worker `/health`/`/props` check stops on failure, so this is
fail-closed, but the name-bind test should be recorded).

### m8 — MINOR (clarity). The census sha in the spec is the report at the pinned commit, not at HEAD.

`sweep2/t1_tasl/g1b_tasl_spec.json` `census.commit` = `76f1d7ba` and `census.report_sha256` = `146b1114…`; that is
correct — the report at `76f1d7ba:docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md` has sha256
`146b1114…` (109 lines), verified. The same path at the branch tip and `aaf2254a` is `d7f8f8aa…` (143 lines; the AR
row added 21 Nov) and at `origin/main` `d47d1008` the file does not exist yet. `validate --launch` does not compare
the sha to a file, so nothing fails, but a future reader will see a mismatch. Add one line to the spec comment or the
report ("census report sha is of commit 76f1d7ba"). No change to the pinned values.

### m9 — MINOR (stale text). The TASL-2 precheck still says the spec sha is `PENDING`.

`TASL2_T1_PRECHECK_20261121.md:156-158` records `hosts.TASL-2.isolation_host_check.sha256 = "PENDING"` and gives the
sha "for the lead to fill". That was true when the precheck was written; the spec now carries `681011b2…` (and the
G.4 worker does too). Harmless historical text; correct it if the precheck report is published next to the filled
spec, or annotate it as "at time of check".

### Notes (not findings)

- **TASL-7 proposer-smoke captures are not in this worktree** (`TASL7_PROPOSER_SMOKE_20261121_captures/` is absent;
  the reported 62-file bundle lives in the ops worktree per the smoke report/review). The pre-launch package relies on
  that report only for the `.50`/`.51` shared-node fact, which its independent review confirmed and I re-confirmed
  live (§8); no action needed for G.1b.
- **§6 coverage.** Plan §6 is fully covered or explicitly deferred: items 1 (delegated scope), 2 (GPU UUID/no resident
  compute), 4 (houseprice CPU 8-15 beside GPU, synthetic 20 s/20 s and 12 s/12 s ratios 1.0, `c6c`), 5 (jax312 on
  TASL-2, sandboxed, `effective:true`) on TASL-2; items 1-3, 6 (llama-server 32k/24 GB props `b1-620d222`, n_ctx
  32768, 1 slot), 7 (Tailscale reachability/latency, `.51`-only bind) on TASL-7; item 3 (4090/Ada ratio of the first
  part) is **explicitly DEFERRED to the job** as the plan designs (`G1B_TASL_PRELAUNCH_20261121.md:58`), and item 8
  (per-call LLM time) is measured by the reviewed smoke (3 calls, p50 3.76 s wall, ≈39 tok/s generation). The
  pre-launch report's §6 table does not point to items 6-8 (they are in the sibling reports); a one-line coverage
  pointer would help.
- **G.4 bind-vs-code consistency** is correct: `g4_tasl.validate_spec` requires `server_url`'s host equal
  `proposer.tailscale_address` (`g4_tasl.py:174-177`), `serve` binds `--host prop["tailscale_address"]`
  (`g4_tasl.py:279`), and the spec sets both to `tasl-7.tail119748.ts.net`; `validate --launch` passes and the live
  resolution matches. No G.4 run exists anywhere (`find` for run/sealed G.4 artifacts: none; the only captures are
  the precheck and the bind test).

---

## 5. Verification performed (positive checks)

All checks below were performed read-only on the worktree; host checks in §8 were read-only `ssh`.

| # | check | result |
|---|---|---|
| 1 | authority rows on `d47d1008`: `R1-T1-HOST-TASL`, `R1-TRACKG-G3-EARLY`, `R1-G1B-CAP`, `R1-G1B-EDITS`, `R1-G1B-TIMEOUT`, `R1-T1-TASL-ENV` present exactly once | **PASS** (`docs/r1/PLAN.md:1343,1350-1352`) |
| 2 | 460 runs/node = (4+1) × 92; four declared edits; `edit_count` authority names R1-G1B-EDITS | **PASS** (`runs_per_node(4)=460`, spec and `validate --launch`) |
| 3 | timeout basis `census_slowest_x3` (3 × slowest of B1/B2/E1–E4) and per-node values | **PASS** — all seven spec values equal `T1_TASL_ROWS_DRAFT_20261121.md` §2 (13.347/65.156/21.8/35.948/40.795/61.781/6.794); `slowest ≥ baseline` enforced by `validate_spec` |
| 4 | hosts/UUIDs/drivers | **PASS** — TASL-2 `GPU-4d623e76-…94` / 535.309.01, TASL-7 `GPU-ab72fb4a-…b1` / 580.178.04; matches specs, bindings, report and live `nvidia-smi -L` (§8) |
| 5 | houseprice CPU `cpus 8-15` disjoint from TASL-2 GPU `0-7`; CPU/GPU coexistence | **PASS** — spec `nodes[mlgym_houseprice].cpus = "8-15"`; `validate_spec` refuses an overlap; `c6c` ratios 1.0 (12 s/12 s CPU, 20 s/20 s GPU, 8-core pin, `cuda_available=false`) |
| 6 | paper commit `d47d1008` in both specs; `origin/main` = `d47d1008` | **PASS** |
| 7 | harness pin `c025f89a` in both specs and in the bindings' `host_check_harness_commit` | **PASS** — live TASL-7 `git rev-parse HEAD` = `c025f89a…`, `status --porcelain` empty; TASL-2 precheck capture also clean |
| 8 | binding lines exactly once each; spec record paths exist and their sha256 equal the files | **PASS** — `host_check_host`, `host_check_harness_commit`, `host_check_items`, `host_check_verdict` exactly 1× in each binding; `681011b2…`/`09945c15…` match |
| 9 | `check_host_record` would accept both bindings (record on main, sha, lines, hostname, pin) | **PASS** — simulated with a local `read_main`: both hosts PASS; note the real gate reads `origin/main`, which does not yet contain the untracked bindings (see m3) |
| 10 | original reports + reviews | **PASS** — originals `83636c03…`/`2b703226…`; reviews `TASL2_ISOLATION_HOST_CHECK_REVIEW_20261121.md` (`bfe9b231…`, ACCEPTED C1–C4) and `TASL7_ISOLATION_HOST_CHECK_REVIEW_20261121.md` (`18e261cd…`, cited by the TASL-7 binding, ACCEPTED C1–C4) |
| 11 | capture bundles | **PASS** — TASL-2 91/91 `shasum -c`, `SHA256SUMS` `e604aff7…`; TASL-7 170/170, `SHA256SUMS` `19c4f657…`; both match the reports |
| 12 | both hosts PASS at the pin (sandboxed smoke `effective:true`, `waivers {}`, `exceptions []`; 27 passed / 1 root-only skip) | **PASS** — `c5`/`c6` records on both hosts; `pytest_isolation.json` 27/1 on both; TASL-7 binding item-7 CUDA-IPC limit disclosed (m1 is the TASL-2 wording) |
| 13 | uv 0.13.6, Python 3.12.16, census freezes `d2e70fe4…`/`80a455c6…` | **PASS** — freeze files' shas match the specs; captures: torch312 byte-equal, jax312 sorted-equal (68 lines, uv freeze `956d0b4f…`, census collation reproduces `80a455c6…`); `g1b_lib.compare_freeze` sorts before comparing (the engine's launch check); live uv/`python -VV` on both hosts |
| 14 | jax GPU (TASL-2 sandboxed `effective:true`; TASL-7 J1b with flag), XLA_FLAGS necessity and spec `extra_env` | **PASS** — J1a/J1b captures; `g1b_tasl_spec.hosts.TASL-7.extra_env.XLA_FLAGS = --xla_gpu_cuda_data_dir=/usr/local/cuda-12.2`; `run_node_job` applies `extra_env`; sandbox keep-prefix includes `XLA_`; `/usr` bound into the sandbox. Residual: M1 (no in-sandbox jax on TASL-7) |
| 15 | no `LD_LIBRARY_PATH`/`LD_PRELOAD` | **PASS** — absent from both specs; env captures record them null; `g4_tasl.py:338,357` strips/records them on the server path; proposer prereq capture `LD_LIBRARY_PATH=<unset>` |
| 16 | G.4 TODO fields: DNS hairpin, `server_url`/bind consistency, bin manifest, binary/model shas, no G.4 run | **PASS** — live `getent` `.51` (TASL-7) / `.50` (TASL-2); `host == tailscale_address` enforced by `g4_tasl.py:174-177`; `a29c667f…` recomputed from the 23-entry manifest; binary `b70f4882…` + build `0.7.0-dev (build 1, commit 620d222)`, GGUF `2959c1b0…` (19 598 489 952 B); no G.4 run/attempt/seal exists (m7 is the name-bind/evidence gap) |
| 17 | HousePrice CSV | **PASS** — live TASL-2 read-only: `/home/dowling/r1_inputs/house-prices/train.csv` sha256 `1e18addf…929d41`, 460 676 B; spec `hosts.TASL-2.extra_env.AR_HOUSEPRICE_TRAIN_CSV` points there |
| 18 | `validate --launch` both specs | **PASS** — `g1b_tasl.py validate … --launch` → `ok: true`, projection 28.262 GPU-h (sensitivity 41.644) within the 100 GPU-h cap, per-host 14.06/14.202; `g4_tasl.py validate … --launch` → `ok: true`, 11.077 GPU-h within the 20 cap |
| 19 | pre-launch report accuracy on the measured facts | **PASS except m3/m7** — all environment, host, binding, `§6`, CSV, manifest, binary/model and validation claims reproduce; the §6 jax cell (M1) and the launch-commit sentence (m3) are the exceptions |
| 20 | dry-run is clearly ENGINEERING / partial default part / no EVIDENCE / no signed note / lease-scope-timeout | **PASS in substance** — report lines 74-81 state it and `dry_run_node.py` labels partial rows; the procedure/coverage text is incomplete (m5, m6) |

---

## 6. Conditions

**Before the described ENGINEERING dry-runs:**

1. **m5** — document the exact dry-run command (delegated `systemd-run --user --scope -p Delegate=yes -p
   MemoryMax=8G -p MemorySwapMax=0` with `AR_TEST_CGROUP_PARENT`, `taskset -c <cpus>`, `G1B_TASL_NODE_LOG`; wrapper
   named in the report) and the `seal` follow-up; fix the "(184 rows)" comment to 10. This is text only.
2. **m6** — add `mlgym_houseprice` (TASL-2) and `mlgym_breakout_minatar` (TASL-7) to the dry-run set, or state why
   not (this also closes M1's end-to-end evidence if Breakout is included).
3. **m3 (partial)** — nothing to change for the dry-run; do not describe the specs as "committed" when they are not.

**Before the TASL-2 binding is published/cited and the specs are committed:** **m1** (re-take the binding sha, update
both specs' `isolation_host_check.sha256`, re-take the pre-launch report's quoted sha), **m9** (stale PENDING note),
**m2** (precheck report text).

**Before any G.1b EVIDENCE launch:**

4. **B1** — implement + independently review the R1-T1-TASL-ENV cross-host default check, add jax312 to the G.1b
   spec's TASL-2 host, put the check in the plan/report/launch sequence, re-take spec shas; **or** a new author PLAN
   amendment (option B or C) recorded on `main`. No G.1b launch while a cited authority clause is unbuilt.
5. **M1** — TASL-7 in-sandbox jax312 + `XLA_FLAGS` proof (or Breakout in the TASL-7 dry-run set), and the §6 table
   corrected (line 56).
6. **m3** — correct the launch-commit wording and spell out the commit → staged-spec (`paper.commit` = launch
   commit) → note (`spec_sha256`) → push -> clean-checkout-at-launch-commit sequence; the bindings and original
   reports must be on `origin/main` (the launch gate reads `origin/main`), and `verify_launch` needs
   `HEAD == spec.paper.commit` with a tracked-clean tree.
7. **m4** — the note names the harness commit (template + `check_note`), or the interpretation is recorded.
8. **m7** — record the `.51`/`.50` resolution evidence and the name-bind test in the G.4 record.
9. **m8** — annotate the census sha (no value change).

**Before G.4:** m7 (name-bind) plus the existing G.4 preconditions in `TASL7_T1_PRECHECK_20261121.md` §7; no G.4 run
exists or is claimed.

The pre-launch report's own limits are sound: no EVIDENCE launch, no signed note, dry-runs not a noise floor; the
report does not overclaim a measured G.1b result. The blocking issue is what the package does not include (B1), not
what it claims to have measured.

---

## 7. Review record (commands; Europe/Berlin, 21 November 2026)

- **Worktree (read-only):** `git status --short`, `git log`, `git show d47d1008:docs/r1/PLAN.md` (authority rows),
  `git show 76f1d7ba:…/TRACKG_U4_CENSUS_20261120.md | shasum`, `shasum -a 256` on the report, both bindings, both
  originals, both reviews, both specs, the wrapper, the plan, `HARNESS_ISOLATION_20261117.md`, the freeze files;
  `shasum -a 256 -c SHA256SUMS` in both capture bundles (91/91 and 170/170); Python reads of the capture JSONs
  (`c0_envs`, `c5`/`c6` smoke records, `c6b_jax*`, `c6c`, `env_check`, `host.json`, `pytest_isolation`,
  `proposer_prereq_result`, `bind_test_result`); `grep` for the binding lines (exactly once each), for
  `crosscheck`/`cross_host` (none), for `XLA_`/`LD_LIBRARY_PATH`, and for TODO/PENDING placeholders (none in the
  checked fields); a `check_host_record` simulation with a local `read_main` (both PASS); `python3
  sweep2/t1_tasl/g1b_tasl.py validate sweep2/t1_tasl/g1b_tasl_spec.json --launch` and
  `python3 sweep2/t1_tasl/g4_tasl.py validate sweep2/t1_tasl/g4_tasl_spec.json --launch` (both `ok:true`, exit 0).
  The validate calls import the modules and may refresh the gitignored `sweep2/t1_tasl/__pycache__` only.
- **TASL-2 (`ssh -o BatchMode=yes portal_zhixu`, read-only):** `hostname`; `getent hosts tasl-7.tail119748.ts.net`;
  `sha256sum` + `stat -c %s` of `/home/dowling/r1_inputs/house-prices/train.csv`; `nvidia-smi -L`;
  `envs/{torch312,jax312}/bin/python -VV`. No write, no GPU work, no lease.
- **TASL-7 (`ssh -o BatchMode=yes tasl7`, read-only):** `hostname`; `getent hosts tasl-7.tail119748.ts.net`;
  `nvidia-smi -L`; `uv --version`; `git -C /home/dowling/r1_tracks/t1_tasl/harness rev-parse HEAD` and
  `status --porcelain`; `envs/jax312/bin/python -VV`. No write, no server start/stop, no lease.
- **Not done:** no run, no dry-run, no server start/stop, no file edit outside this review, no commit/push/delete, no
  HTCondor/deepthought, no attempt-1 archive or lease-log touch.

**Result of the live read-only checks (21 Nov 2026):**

```
TASL-2: getent hosts tasl-7.tail119748.ts.net -> 100.106.74.50
TASL-2: train.csv sha256 1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41  460676 B
TASL-2: GPU-4d623e76-7587-ee15-a633-46f60d220d94; Python 3.12.16 (both envs)
TASL-7: getent hosts tasl-7.tail119748.ts.net -> 100.106.74.51
TASL-7: GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1; uv 0.13.6; harness HEAD c025f89aeafc…, status clean;
        Python 3.12.16 (jax312)
```

---

**AI-assisted: DeepSeek Harness agent (`g1b-tasl-prelaunch-reviewer`), 21 Nov 2026. ENGINEERING_ONLY; the only file
written is this review.**
