# G.1b of the T1 node-expansion candidates — spec, note draft and launch commit (26 November 2026; R1-TASL2-CPU amendment)

**Status.** Prepared for independent review of the R1-TASL2-CPU amendment; ENGINEERING_ONLY; AI-assisted (Claude,
Mac-desk agent). Nothing ran, no host was reached, no label or evaluation value was read. Branch
`mac-g1b-expansion-20261126c`, rebuilt on published `main` `cdb8be91` (fetched 26 Nov 2026). The accepted branch
`mac-g1b-expansion-20261126b` (accepted at `52b2cb49`, review record `cb258591`, launch commit `db5c6944`, base on
`f1f1b651`) and the round-1 branch `mac-g1b-expansion-20261126` are left untouched; this branch supersedes them. Not
pushed.

| item | value |
|---|---|
| authority | R1-T1-NODE-EXPANSION, R1-G5-EXPANSION-JOIN, R1-T1-D21-SCOPE, R1-BX-D14-G4B, **R1-TASL2-CPU**; the G.1b rows R1-T1-HOST-TASL, R1-T1-TASL-ENV, R1-G1B-EDITS, R1-G1B-TIMEOUT, R1-G1B-CAP, R1-G1B-TASL-DECISIONS, R1-G1B-NOTE2-DECISIONS, R1-T1-DATA-MANIFEST, R1-G1B-AR-ENV, R1-G1B-AR-PY, R1-G1B-JOIN, R1-XC3-FAIL-READING |
| base (code and templates) | `e81e0a34ce97dade1e79027a0ea8c86b277e6f7e` (parent `cdb8be91`) |
| launch commit | `7d0279d8a677582f4f6e5892461bf7138e78fd66` (its parent is the base; `paper.commit` = the base) |
| spec | `sweep2/t1_tasl/g1b_tasl_x_spec.json`, sha256 `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238` at the launch commit |
| run id | `g1b-x-tasl-20261126-a` (unchanged: no job of it has started) |
| note draft | `docs/r1/proposals/G1B_X_T1_TASL_NOTE_DRAFT_20261126.md` (`approved: false`; publishes as `docs/r1/authorizations/g1b_x_t1_tasl_<YYYYMMDD>.md`) |
| this unit's review record (to come) | `docs/r1/reviews/G1B_EXPANSION_REVIEW_20261126.md` (named by the spec's `review_record`; regenerated after review with the new spec sha256; P4 and the ETTh1/Forest Cover gates read it, §4) |
| launch table | `G1BX_LAUNCH_TABLE.md`, `g1bx_launch_table.json` beside this report (generated) |
| builder | `sweep2/t1_tasl/build_g1bx_launch.py` with `g1bx_build_config.json` (pinned dates; SSH-signed commits; holder `wip-g1bx-tail-c`) |
| full-suite lists | `FULLSUITE_G1BX_BASE_cdb8be91.txt`, `FULLSUITE_G1BX_TIP.txt` beside this report (§11) |

**Summary.** All four candidates passed their U2 census on TASL-2, each CPU-only on one CPU set. The spec runs all
four CPU-only on TASL-2, using no GPU card: 0 GPU-h against the 40 GPU-h cap. Under R1-TASL2-CPU no node uses CPUs
8-11: MetaMaze stays on 0-3 and ETTh1 on 16-31 (their census sets); Titanic moves to 12-15 and Forest Cover to 4-7,
replacement sets of the same size that the TASL-2 CPU stability record passed. Each replacement set needs its own
fixed-seed determinism check before its first use, and that check is a launch gate. The four sets are disjoint, so
all four nodes can run at once; at the sensitivity ratio 1.5 the longest (Titanic) takes 27.4 h, and the latest
common start is 30 Nov 2026 20:33 CET (§5). No node can launch from what is on `main` today: each needs the TASL-2
host check at its kit pin (one session, §9), MetaMaze also the EXP-ENV row (§10), ETTh1 and Forest Cover this unit's
review record, Titanic and Forest Cover their determinism check records. Every gate fails closed and is checked at
launch, node by node.

## R1-TASL2-CPU amendment (26 November 2026)

**What `main` added since the accepted unit's base `f1f1b651`.** The xc3 short cross-check verdicts; the TASL-2 CPU
stability record `TASL2_CPU_STABILITY_20261125.md` (sha256 `9dca2cf3…164b`, review
`docs/r1/reviews/TASL2_CPU_STABILITY_REVIEW_20261125.md` ACCEPTED, captures `captures/tasl2_cpu_stability_20261125/`,
`SHA256SUMS` sha256 `1a2c80c8…832df`); and the PLAN row **R1-TASL2-CPU** (author, 26 Nov 2026 (b)). The record ran
MetaMaze's census baseline three times on each P-core group: CPUs 8-11 (physical cores 4 and 5, the only cores with
`cpuinfo_max_freq` 6.1 GHz) failed 3 of 3 with the sandboxed worker killed by a native signal; CPUs 0-3, 4-7 and
12-15 passed 3 of 3 each, bitwise identical. The row: no R1 job on TASL-2 uses CPUs 8-11; a spec that pins a set
containing any of them gets a replacement set of the same size that avoids 8-11 (the Mac proposes it in the next spec
or note; the coordinating chat publishes it with that unit), and that set passes a fixed-seed determinism check
before its first use; sealed results that used CPUs 8-15 stand.

**What changed in this unit.**

| item | before (accepted at `52b2cb49`) | now |
|---|---|---|
| base | `d26a2147` on `f1f1b651` | `e81e0a34` on `cdb8be91` (the accepted base cherry-picked, then amended) |
| Titanic CPU set | 8-11 (census set), `max_attempts: 2` | **12-15** (`cpu_replacement`: census set 8-11, R1-TASL2-CPU), no attempt cap |
| Forest Cover CPU set | 8-11 (census set), `max_attempts: 2`, after Titanic under the shared lease | **4-7** (`cpu_replacement`), no attempt cap, its own lease |
| MetaMaze, ETTh1 | 0-3, 16-31 | unchanged |
| validation | `max_attempts: 2` required on 8-11 | any node or host CPU set containing 8-11 refused; `max_attempts` refused; a replacement set must have the census set's size and be one the stability record passed (0-3, 4-7, 12-15); the stability record checked by sha256 in this checkout |
| gates | host check; env row (MetaMaze); review (ETTh1, Forest Cover) | plus **`cpu_determinism`** for Titanic and Forest Cover (`check_determinism_record`, §4, §9) |
| note | `retry_8_11`, `census_cpus` lines | `cpu_sets`, `determinism_check_mlgym_titanic`, `determinism_check_gc7rc_forestcover` (rendered from the spec; `check-note-x` requires them); `retry_8_11` removed |
| attempts | at most two on 8-11 (`next_attempt(…, max_attempts)`) | the existing rule only (`next_attempt` back to its `main` signature) |
| launch rows | … R1-G5-EXPANSION-JOIN | plus R1-TASL2-CPU (`X_PLAN_ROWS`; checked on `origin/main` by `verify_launch_tasl`) |
| job record | `census_cpus` = the node's set | `cpus`, `census_cpus` (the census set) and `cpu_replacement` (the row) |
| schedule | the 8-11 chain (34.8 h, 51.9 h at 1.5×) carries the critical path | four disjoint sets, all in parallel; Titanic 18.4 h (27.4 h) is the longest |
| MetaMaze/Titanic crash disclosure | "the stability record is pending" | cites the stability record, its review and R1-TASL2-CPU |
| Forest Cover's review condition | "on its census CPU set" | "on its CPU set" (4-7, the R1-TASL2-CPU replacement of 8-11); for the reviewer to confirm (§6) |
| host-check procedure (§9) | worktrees in Track P's harness repository | a separate clone (review m9); every step pinned off 8-11; step 7, the two determinism checks |

Unchanged: the pins, manifests, census times, timeouts (3 × the slowest census record), the `measurement` block, the
environments, the engine admission, the CPU-set preflight, the publication rule and the three existing gate kinds.
The seven-node and autoresearch kinds and their specs are unchanged (tests).

**For the reviewer.** (a) The Forest Cover condition of the round-1 CPU-census disposition now reads "its CPU set"
rather than "its census CPU set" (§6); the regenerated review record needs the disposition line again if the
reviewer confirms it on 4-7. (b) The determinism-check design (§5.2) and its gate (§4). (c) The assignment (Titanic
on 12-15, Forest Cover on 4-7, §5.1), the reverse of the first suggestion. (d) The timing argument (§5.3).

## 1. The inputs on main, and what they settle

The node-expansion merge `47d2a39d5` published four kit records, their four independent reviews (each ACCEPTED, no
BLOCKING or MAJOR) and five U2 records. Nothing on `main` since changes them; `cdb8be91` adds the stability record
and R1-TASL2-CPU, which change where two nodes run, not what they run.

| node | kit record (review) | harness branch @ pin | U2 record | U2 verdict, census CPU set | G.1b CPU set |
|---|---|---|---|---|---|
| `mlgym_titanic` | `TITANIC_KIT_20261125.md` (`reviews/TITANIC_KIT_REVIEW_20261125.md`) | `mac-trackg-titanic-20261125` @ `3a67042b` | `TITANIC_U2_RESULT_20261125_RETRY.md` (the first record is the STOP) | PASS on the retry, cpus 8-11 | 12-15 |
| `mlgym_metamaze` | `MOUNTAINCAR_KIT_20261125.md` (`reviews/MOUNTAINCAR_KIT_REVIEW_20261125.md`) | `mac-trackg-mountaincar-20261125` @ `aa354485` | `METAMAZE_U2_RESULT_20261125.md` | PASS on attempt C, cpus 0-3 | 0-3 |
| `gc7rc_etth1` | `ETTH1_KIT_20261125.md` (`reviews/ETTH1_KIT_REVIEW_20261125.md`) | `mac-trackg-etth1-20261125` @ `3a06d867` | `ETTH1_U2_RESULT_20261125.md` | PASS on attempt B, cpus 16-31 | 16-31 |
| `gc7rc_forestcover` | `FORESTCOVER_KIT_20261125.md` (`reviews/FORESTCOVER_KIT_REVIEW_20261125.md`) | `mac-trackg-forestcover-20261125` @ `85851664` | `FORESTCOVER_U2_RESULT_20261125.md` | PASS, one launch, cpus 8-11 | 4-7 |

- **MetaMaze over MountainCarContinuous.** The candidate-3 kit is filed as `MOUNTAINCAR_KIT_20261125.md` but ports
  `mlgym_metamaze`; MountainCarContinuous was rejected for noise-floor suitability (kit §3). No separate MetaMaze kit
  record exists.
- **Kit pins exist on TASL-2 only.** None of the four kit commits is in the local harness repository (it has
  `c025f89a` only, and fetch is not possible here). Harness facts come from the kit records and their captures on
  `main`.
- **All censuses ran CPU-only**, at the full budget, in a delegated 8 GiB / swap-0 scope, with B2 equal to B1 to the
  digit (for Titanic and Forest Cover the baseline and B2 result channels are byte-identical; their sha256 is the
  one each determinism check must reproduce, §5.2). Titanic is in the harness's `CPU_ONLY_NODES` at `3a67042b`; the
  other three are not, at their pins.

## 2. The design

A new spec kind, `g1b_tasl_x_job/v1`, in `sweep2/t1_tasl/g1b_tasl.py`, beside the seven-node and autoresearch kinds.
Both of those are unchanged: their specs are byte-identical, and the existing tests pass unchanged. The new kind adds,
for itself only:

1. **A harness pin and checkout per node** (`nodes[].harness`), checked at its pin and clean by every job. The job
   record and the assembly carry the node's pin.
2. **CPU nodes on their CPU sets**, each under a CPU-set lease (`~/r1_locks/cpus-<set>.lock`, non-blocking). Sets
   must be equal or disjoint; equal sets run one after another. The four sets of this spec are disjoint.
3. **R1-TASL2-CPU.** No node or host CPU set of this kind may contain CPUs 8-11 (`X_EXCLUDED_CPUS`). A node whose
   census set contains them carries `cpu_replacement`: the row, the census set, the stability record (path and
   sha256, checked against the file in the checkout) and the fixed-seed determinism check (the record path the gate
   reads, two runs, and the census baseline's result-channel sha256). The replacement set must have the census set's
   size and be one of the groups the stability record passed (`X_STABLE_SETS`: 0-3, 4-7, 12-15); the node's gate
   must require `cpu_determinism`. A node on its census set carries neither.
4. **The CPU-set preflight** (`cpu_preflight`, `cpu_busy_check`). It reads the per-CPU busy fraction from `/proc/stat`
   over 5 s (idle and iowait count as idle) and refuses above 0.2 on any CPU of the set. It runs before the attempt
   (a refusal record; nothing is used up) and before each of the four parts (an infrastructure STOP). The readings
   are recorded as `cpu_preflight` in the job record.
5. **How the engine admits a CPU chunk** (`cpu_only`). `harness_list` (Titanic) starts the engine as before.
   `census_override` (the other three) starts `python -c X_ENGINE_OVERRIDE <node> --chunk …`, which checks that the
   chunk names that node, adds the node to `autoresearch.trackg.noise_floor.CPU_ONLY_NODES` in the engine's own
   process, and calls the engine's `main`. At `c025f89a` that list is used only by the chunk guard. The U2 census
   drivers had added the node to the smoke's own copy, `tests.trackg.port_smoke_gpu.CPU_ONLY_NODES`. No harness file
   changes.
6. **The census environment of each node.** torch312 is compared with `uv pip freeze`. `venv_jax` is compared with
   `python -m pip --disable-pip-version-check freeze`, the tool its census used; its freeze is committed as
   `sweep2/g1b/env/venv_jax.freeze.txt` (sha256 `630ed6e1…`, 56 packages).
7. **Census times per record** (B1, B2, E1-E4). They bind `run_seconds` (= B1) and the timeout basis (= the slowest).
8. **Per-node launch gates and the review record** (§4), **row-based publication** (§4), and its own cap (40 GPU-h),
   run namespace, assembly and summary.

The earlier rule "at most two attempts on CPUs 8-11" (`max_attempts`, `retry_8_11`) is removed: no node runs there,
and validation now refuses a `max_attempts` key.

## 3. Per node: pins, CPU set, census basis, host

Every value is from the kit record and the U2 record on `main`; the tests compare the spec with each capture's
`pins.json`, run records (CPU list = the census set) and file sha256s. All four nodes: host TASL-2, device cpu, 4
edits, 460 runs, timeout basis `census_slowest_x3`.

| node | harness pin | env | node_spec / committed pin / edits / data manifest (first 8) | census set | G.1b set | census B1, B2, E1, E2, E3, E4 (s) | timeout |
|---|---|---|---|---|---|---|---|
| `mlgym_titanic` | `3a67042ba7e4211feb9681524f3879643c8cf635` | torch312 | `059fd0d5` / `0368a73d` / `fd464c6e` / `c8ccedd0` | 8-11 | 12-15 | 138.183, 137.714, 128.04, 147.81, 155.965, 139.607 | 467.895 s |
| `mlgym_metamaze` | `aa354485bff6b5746c48ddadcb50d92e9c6f3645` | venv_jax | `d97bb182` / `759d6bf0` / `6de5741f` / `e2338195` | 0-3 | 0-3 | 53.721, 53.596, 53.69, 53.63, 53.662, 54.626 | 163.878 s |
| `gc7rc_etth1` | `3a06d86721b0c1826b165b68a9781a561e4993f4` | torch312 | `8f874c50` / `818b8f6e` / `ba31fed3` / `eacc7e69` | 16-31 | 16-31 | 10.908, 11.028, 11.026, 10.87, 11.392, 11.506 | 34.518 s |
| `gc7rc_forestcover` | `85851664679d10889c5af406843c4a3fc38f7a49` | torch312 | `ff2a585b` / `78b48db9` / `0219deb8` / `2b5cfb15` | 8-11 | 4-7 | 93.406, 93.734, 93.52, 93.131, 96.023, 255.723 | 767.169 s |

- **Titanic.** The census basis is the retry. Its record gives 156 s / 468 s from the ceiling of the slowest record;
  the spec uses the raw slowest record and 3× it, as every G.1b spec does. The retry's captures are at
  `TITANIC_U2_RESULT_20261125_RETRY_captures/` (its text says `captures/titanic_u2_retry_20261125/`; the files and
  the `SHA256SUMS` sha256 `feb95183…` match). Census baseline result channel sha256 `77a834ec…ce9d4` (= B2's).
- **MetaMaze.** The data manifest is host-specific (kit review c3, c6(vi)); `e2338195…` is TASL-2's.
- **ETTh1.** CPU set 16-31, the sixteen E-cores, as its census ran.
- **Forest Cover.** The slowest record is E4 (255.723 s), inside the 300 s ceiling. Census baseline result channel
  sha256 `bcfc9b5d…8140a` (= B2's).
- **Host.** TASL-2 for all four: it is their census host, and their environments and data are there. TASL-7 is not
  used.
- **Paths.** New paths on TASL-2 under `/home/dowling/r1_tracks/t1_tasl_x/` (one checkout per node, plus `data`,
  `runs` and `sealed_g1b`). The job runs the node's own `setup_command` with the census environment first on `PATH`;
  the engine compares the data manifest with the census value.

## 4. The note, its gates, the review record and publication

**Format.** The note uses `key: value` lines (read by `_note_fields`) and is checked by `check_note_x` (CLI
`g1b_tasl.py check-note-x <spec> --note <note> [--draft]`). It checks:
- the file name;
- `approved`, `label`, `labels_read: none`, `run_id`, `paper_commit` and `spec_sha256`, equal to the spec's;
- `publication_row` and `note_rule` citing R1-T1-NODE-EXPANSION, and `host_row` citing R1-T1-TASL-ENV;
- one `node_<node>` line and one `gate_<node>` line per node;
- for each node on a replacement set, one `determinism_check_<node>` line naming R1-TASL2-CPU, `cpus <set>`, the
  record path and the census baseline's result-channel sha256 (and no such line for another node);
- the `funnel` line, naming every candidate;
- the `cutoff` line, with the instant `2 Dec 2026 00:00 CET` and `finished_utc`;
- P1-P7 PASS, with their citations;
- no `<…>` placeholder anywhere.

In the draft only, P2 and P4 may read PENDING. The rendered lines (run id, host, environments, the four node lines,
projection, cap, CPU preflight, the two determinism-check lines) come from `build_g1bx_launch.py render`.

**P4 and the review record.** In strict mode, P4 must cite `docs/r1/reviews/G1B_EXPANSION_REVIEW_20261126.md`, and that
file on published `main` must have exactly one line `spec_sha256: <this spec's sha256>` and exactly one line
`verdict: ACCEPTED`. The record the coordinator generates after acceptance therefore needs these lines at column 0
(the spec sha256 changed with this amendment):

```
spec_sha256: d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238
verdict: ACCEPTED
cpu_census_disposition: gc7rc_etth1 ACCEPTED
cpu_census_disposition: gc7rc_forestcover ACCEPTED
```

**Per-node gates** (`check_gate_x`, run at every launch of that node; each fails closed):

| node | gate requires | checked |
|---|---|---|
| all four | `host check <report> sha256 <hex>` | the report on `main`, its sha256, `host_check_host: TASL-2`, `host_check_harness_commit: <the node's pin>`, `host_check_items: 1-7 PASS`, `host_check_verdict: PASS` |
| `mlgym_metamaze` | `env row <R1 row>` | the PLAN row on `main`, present once, containing verbatim `venv_jax is admitted as the census environment of mlgym_metamaze for its G.1b on TASL-2` |
| `gc7rc_etth1`, `gc7rc_forestcover` | `review docs/r1/reviews/G1B_EXPANSION_REVIEW_20261126.md` | the record on `main` with the `spec_sha256` line (from the note, equal to the spec file's), `verdict: ACCEPTED`, and `cpu_census_disposition: <node> ACCEPTED` |
| `mlgym_titanic`, `gc7rc_forestcover` | `determinism check <record> sha256 <hex>` (R1-TASL2-CPU) | the record is the one the spec names (`TASL2_CPUSET_DETERMINISM_X_TITANIC_12-15.md`, `TASL2_CPUSET_DETERMINISM_X_FORESTCOVER_4-7.md` under `docs/r1/reports/tasl_chain_20261122/`), on `main`, with the cited sha256; each of its lines `determinism_check_host: TASL-2`, `_node: <node>`, `_cpus: <set>`, `_harness_commit: <pin>`, `_runs: 2`, `_result_channel_sha256: <the census baseline's>`, `_baseline_seconds: <s1> <s2>` (each in (0, 1.5 × census B1]) and `_verdict: PASS` exactly once at column 0; a line of those keys in another casing or with markup is refused (`check_determinism_record`) |

A PENDING gate keeps that node from launching; it does not keep the note from being published. A gate completed later
goes into a later note with the same spec and run (a new file name, the other lines unchanged), and that later note is
independently reviewed before it is published.

**Publication without an author decision.** `check_note_x` requires a `publication_row` citing R1-T1-NODE-EXPANSION,
and `launch` checks that the row on `main` says the "coordinating chat publishes the new G.1b spec and note"
(`check_publication_row`; the row is unchanged on `cdb8be91`). R1-TASL2-CPU says the coordinating chat publishes the
replacement sets with this unit, so no further decision is needed for them.

## 5. CPU sets, determinism check, timing, schedule

### 5.1 The replacement sets and the assignment

Under R1-TASL2-CPU each 4-CPU census set on 8-11 needs a 4-CPU replacement that avoids 8-11. MetaMaze keeps 0-3 and
ETTh1 keeps 16-31, so the sets left on the P-cores are 4-7 (physical cores 2 and 3) and 12-15 (cores 6 and 7). Both
are two complete SMT pairs, both report `cpuinfo_max_freq` 5,800,000 kHz, and both passed the stability check 3 of 3
with outputs bitwise identical to 0-3's (53.4-54.3 s per run on each). Nothing in the record separates them as
hardware. The E-cores are not used for a replacement: Titanic's census attempt on 16-31 was aborted, the E-cores are
much slower (max 4.4 GHz), and ETTh1 holds them.

**Assignment: Titanic on 12-15, Forest Cover on 4-7** (the reverse of the first suggestion). With 4-7 and 12-15
equivalent as hardware, the choice is set by G.5, the only other user of TASL-2's CPUs:
- The G.5 spec (on `main` and on the G.5 branch tip `6ca4dfa8`) runs its TASL-2 GPU worker on cpus 0-7, which
  overlaps 4-7 but not 12-15. Its houseprice audits on 8-15 are being moved off 8-15 in a parallel G.5 amendment.
- So 4-7 is the set that a G.5 job is most likely to touch. The node there should be the one that tolerates
  contention best and frees the set soonest. Forest Cover's timeout (767.169 s, set by its slow E4 record) is 8.2× its
  B1 and about 8× its typical records, against Titanic's 3.4× B1 and 3.0× its slowest. A slowdown in the middle of a
  part, which the preflight cannot see until the next part, is far less likely to become a timing STOP for Forest
  Cover. Forest Cover is also the shorter node (16.4 h against 18.4 h), so 0-7 is free for G.5's worker sooner.
- Titanic, the longest node with the tightest timeout margin, gets 12-15, which no G.5 set on `main` touches once
  the houseprice audits leave 8-15.
- With all four sets disjoint, both orders allow all four nodes to run at once; the reverse would only move the
  G.5 overlap onto the more fragile node.

### 5.2 The fixed-seed determinism check (R1-TASL2-CPU)

The row asks that a replacement set "passes a fixed-seed determinism check before its first use". Two readings were
considered:
- **(i) The stability record itself.** It is a fixed-seed determinism check of 4-7 and 12-15 (three bitwise
  identical runs each), but of MetaMaze (JAX) only, not of the node that will use the set (Titanic and Forest Cover
  run torch312). Its own review says the 3/3 result "is not a long-run stability proof for 4–7/12–15".
- **(ii) A node-specific check before the node's first job** on the set, recorded and committed, and enforced as a
  launch gate.

**Decision: (ii) for Titanic and Forest Cover, as a launch gate, with (i) cited as supporting evidence.** It is the
conservative reading: "its first use" is the node's first job on the set, and only the node's own workload on that
set shows that this workload is deterministic there. The cost is small: two census baselines per node, about
2 × 140 s for Titanic and 2 × 95 s for Forest Cover, run while the host-check session's checkouts and data are in
place. MetaMaze (0-3) and ETTh1 (16-31) run on their census sets, which are not replacement sets, so the row asks no
check of them; 0-3 is also covered by the stability record and MetaMaze's accepted census.

**The check, per node** (procedure in §9 step 7; the note's `determinism_check_<node>` lines state it):
- **What runs:** the census baseline step only (`s000_baseline`: the reviewed census smoke's first run, seeds
  8001/8001, the census budget — Titanic 150,000 steps, Forest Cover 8,000), twice, one after another, from the node's
  G.1b checkout at its pin, in its environment (torch312), each in its own delegated scope (MemoryMax 8G,
  MemorySwapMax 0), `taskset -c <set>`, `CUDA_VISIBLE_DEVICES` empty, with the set idle before each run.
- **Pass criterion:** both runs exit 0 with isolation `effective: true`, waivers `{}`, exceptions `[]`; both result
  channels have the census baseline's sha256 (Titanic `77a834ecf04cfff506bc0c46368dbf8e87f31dedb184035b422e74c4abfce9d4`,
  Forest Cover `bcfc9b5d296a07335f46ec467c68ca7e282355882fccd44f9ea7f68cd628140a`), so they are bitwise identical to
  each other and to the census, where B2 already equalled B1; and each baseline wall time (`elapsed_seconds_info_only`)
  is at most 1.5 × the census B1 (Titanic 207.2745 s, Forest Cover 140.109 s), which checks the timing basis on the
  new cores (§5.3).
- **Why reproduce the census channel, not only repeat it:** the census set (8-11) is the suspect one. Matching the
  census bytes on a healthy set shows that the census, and the timing and determinism it measured, carry over.
  MetaMaze did the same in the stability record (all passing groups equal to the accepted 0-3 hashes). A mismatch is
  not a PASS: the node's gate stays PENDING and the author decides.
- **Record and gate:** the record at the path the spec names, with the eight `determinism_check_*` lines (§4); the
  coordinating chat commits it to `main`, and a later, reviewed note fills the gate as
  `determinism check <record> sha256 <its sha256>`.

### 5.3 Why the census timeouts still hold on 4-7 and 12-15

The timeouts are 3 × the slowest census record (R1-G1B-TIMEOUT) measured on TASL-2. For Titanic and Forest Cover
those records were measured on 8-11, so the basis is node-specific and the cores change. The question is whether a
run on a 5.8 GHz core can come near 3 × a record measured on a 6.1 GHz core.
- **Clock bound.** From the stability record's host facts: 8-11 (cores 4-5) have `cpuinfo_max_freq` 6,100,000 kHz;
  every other P-core, including 4-7 and 12-15, has 5,800,000 kHz; governor `powersave` under `intel_pstate`, turbo on,
  so each core boosts to its own limit. A run that scales fully with the clock is at most 6.1/5.8 = 1.052× slower on
  the new sets.
- **Measured bound.** MetaMaze's baseline on 8-11 had trained its full budget when it crashed at 51.934 s and 50.674 s
  (attempt A and the retry; the stability review's evidence index). On the 5.8 GHz sets it took 53.721 s (census B1,
  0-3) and 53.4-54.3 s (the nine stability runs on 0-3, 4-7, 12-15). Those crashes came before evaluation ended, so
  the full 8-11 run was longer than 51.9 s, and the slowdown off 8-11 is below 54.347/50.674 = 1.072. That agrees
  with the clock bound.
- **Margins** (at the measured 1.072, the larger of the two):

| node | timeout | slowest record × 1.072 | timeout / that | B1 × 1.072 | timeout / that |
|---|---|---|---|---|---|
| `mlgym_titanic` (12-15) | 467.895 s | 167.19 s | 2.80 | 148.13 s | 3.16 |
| `gc7rc_forestcover` (4-7) | 767.169 s | 274.14 s (E4; typical E3 102.94 s) | 2.80 (7.45 on E3) | 100.13 s | 7.66 |

- A timing STOP needs a run about 2.8 times slower than its slowest census record, even after the core change. The
  300 s ceiling applies to the census records, which do not change; even Forest Cover's E4 × 1.072 (274 s) is under it.
- **Concurrency.** The censuses ran essentially alone (preflight load 0.1-0.8). In the G.1b all four nodes run at
  once on disjoint sets, so they share only the L3 cache, memory bandwidth and the package power limit, not CPU time;
  the 2.8× margin and the 1.5 sensitivity ratio of the schedule cover that, and each job records its measured ratio
  to the census B1 per part.
- **Checked before first use.** Each determinism check refuses a baseline slower than 1.5 × the census B1 on the new
  set, so the transfer of the timing basis is measured, not assumed, before either node starts.

**Conclusion:** the 3× census-slowest timeouts hold on 12-15 and 4-7; no change to the timeouts is needed.

### 5.4 Projection and schedule

From the census records on TASL-2, at ratio 1.0, with a sensitivity ratio of 1.5. Each configuration gets 92 runs;
c0 is timed at the mean of B1 and B2; each node adds 900 s of setup.

| node | CPU set | estimate (h) | at 1.5× (h) | latest start at 1.5× (CET) | job deadline (h) |
|---|---|---|---|---|---|
| `mlgym_titanic` | 12-15 | 18.378 | 27.443 | **30 Nov 20:33** | 53.97 |
| `gc7rc_forestcover` | 4-7 | 16.400 | 24.475 | 30 Nov 23:31 | 36.81 |
| `mlgym_metamaze` | 0-3 | 7.131 | 10.572 | 1 Dec 13:25 | 21.59 |
| `gc7rc_etth1` | 16-31 | 1.675 | 2.388 | 1 Dec 21:36 | 5.18 |
| all four at once (disjoint sets) | | 18.378 (longest) | 27.443 | **30 Nov 20:33** | |
| all four one after another (reference) | | 43.584 | 64.878 | 29 Nov 07:07 | |

A latest start is 2 Dec 2026 00:00 CET (`2026-12-01T23:00:00Z`) minus the 1.5× hours, with no retry, rounded down to
the minute (exact: 20:33:25, 23:31:30, 13:25:40, 21:36:43, 07:07:19). GPU: 0 GPU-h, margin 40 GPU-h. CPU: 175.128 CPU
core-hours by the spec's B1 accounting. The 8-11 chain of the accepted unit (34.8 h, 51.9 h at 1.5×, latest start
29 Nov 20:04) no longer exists.

**Schedule.** Each node starts as soon as its own gate is PASS; nothing waits for another node. Titanic and Forest
Cover first need their determinism checks (minutes) and those records on `main` in a reviewed note. Starting by
29-30 Nov leaves room for one infrastructure retry of Forest Cover; a Titanic retry adds up to 27.4 h, so Titanic
should start as early as its gates allow.

**If a determinism check fails.** The node does not launch on that set (its gate stays PENDING) and the author
decides. The only other stable P-core group is 0-3, which MetaMaze holds for about 7-11 h; a re-issued spec could put
the node on 0-3 after MetaMaze (an equal set, run in turn under the lease) with its own determinism check, if the
1.5× hours still fit before the cutoff. Otherwise the node goes to T2.

### 5.5 CPU sets and G.5

R1-G5-EXPANSION-JOIN gives the expansion G.1b jobs precedence on the TASL cards, not on CPU sets, and the G.5 jobs take
no CPU lease. Each expansion job therefore refuses to start, and refuses each later part, while its set is busy (the
preflight). The preflight samples only the five seconds before each part, so a G.5 job that starts in the middle of a
part is not caught until the next part.

**G.5 CPU sets assumed here.** On TASL-2: the G.5 GPU worker on cpus 0-7 (G.5 spec on `main` and on the G.5 branch
tip `6ca4dfa8`), and the houseprice CPU audits moved off 8-15 by the parallel G.5 amendment onto a set that amendment
names (not known to this unit; under R1-TASL2-CPU an 8-CPU set avoiding 8-11). This unit does not change any G.5 file.

**Recommendation to the coordinating chat (for the G.5 schedule):** keep G.5's TASL-2 CPUs disjoint from the four
expansion sets 0-3, 4-7, 12-15 and 16-31 while the node on each set runs (until its sealed attempt finishes, at the
latest 2 Dec 2026 00:00 CET). With 8-11 withdrawn, those four sets are all of TASL-2's usable CPUs, so in practice:
- G.5's TASL-2 worker (0-7) starts once MetaMaze (0-3) and Forest Cover (4-7) have finished: about 16.4 h after a
  common start, 24.5 h at 1.5×;
- G.5's houseprice audits take no CPU of 12-15 until Titanic ends and none of 16-31 until ETTh1 ends (ETTh1 is short,
  1.7-2.4 h); an audit set inside 16-31 is free once ETTh1 has ended;
- the G.5 amendment does not choose 4-7 or 12-15 for the audits while those nodes run.

A per-CPU lock taken by G.5 as well would make this mechanical; that is a G.5 code unit, not part of this one.

## 6. ETTh1 and Forest Cover: the reviewer's disposition

Their kit reviews (c2/c4) asked for a GPU census and GPU determinism. Their U2 censuses ran CPU-only and leave that
open (`ETTH1_U2_RESULT_20261125.md` §8, `FORESTCOVER_U2_RESULT_20261125.md` §7-§8). The round-1 reviewer accepted the
CPU census as the census of a CPU G.1b, with c2 and c4 disposed of for device cpu, on conditions in the spec
(`nodes[].cpu_census_conditions`) and the note (`cpu_census_conditions`, funnel):
- each node stays on the CPU, on its census set, for its G.1b and for any G.5 addendum;
- a GPU run needs c2/c4 met (a GPU census on TASL-2) and a re-issued spec;
- the funnel discloses that their noise floors are CPU-measured;
- kit review c1 is still to be recorded (P2).

**Amended for R1-TASL2-CPU (Forest Cover only).** The first condition cannot hold for Forest Cover as written, because
its census set 8-11 is withdrawn. Its condition now reads "on its CPU set … its census set 8-11 is replaced by 4-7
under R1-TASL2-CPU (same size, determinism-checked before first use)", and it says that the reviewer's disposition is
to confirm the condition on the replacement set. The device question that c2/c4 concern is unchanged (CPU, the same
P-core microarchitecture, 4 threads), and the determinism check on 4-7 must reproduce the census baseline bytes. ETTh1's
condition is unchanged (16-31). The regenerated review record carries the disposition lines again only if the
reviewer confirms this. Any G.5 addendum for Forest Cover would run it on 4-7 under the same conditions.

## 7. Disclosures

1. **MetaMaze and Titanic on CPUs 8-11.** Two MetaMaze census attempts there STOPped with native signals after the
   full-budget baseline (SIGSEGV, rc −11; SIGILL, rc −4); attempt C on 0-3 passed and is the census. Titanic's
   first smoke on 8-11 also STOPped (SIGSEGV, SIGILL, a worker death) while a sibling smoke shared the set; its retry
   passed alone. **The TASL-2 CPU stability record** (`TASL2_CPU_STABILITY_20261125.md`, sha256 `9dca2cf3…164b`,
   review ACCEPTED) then reproduced the failure on 8-11 (3 of 3) and passed 0-3, 4-7 and 12-15 (3 of 3 each,
   bitwise identical) under the newest microcode `0x133`; the mechanism is not established read-only (consistent
   with degradation of the two 6.1 GHz cores). On it the author decided R1-TASL2-CPU. The note's
   `disclosure_metamaze_cpus` line cites the record, its review, its captures' `SHA256SUMS` and the row. It replaces
   the earlier "pending stability record" text.
2. **Titanic and Forest Cover off their census sets.** Their timing basis and census determinism were measured on
   8-11; §5.3 argues the timing carries over and each determinism check measures it on the new set. Their census
   records that used 8-11 stand (the row: sealed results on 8-15 stand); they are census inputs, not G.1b results.
3. **The census override** (§2 item 5). If the reviewer refuses it, the alternative is a reviewed harness unit adding
   the three nodes to `CPU_ONLY_NODES` (new pins, new host checks, a re-issued spec).
4. **ETTh1 and Forest Cover on the CPU** (§6), with Forest Cover's condition amended.
5. **Kit review c1** is not recorded on `main` for any of the four. P2 stays PENDING until the coordinating chat
   records it.
6. **Data and licences** (note line `disclosure_data`). Titanic's tables come from MLGym's pinned commit, not a user
   Kaggle download (R1-TRACKG-PORT-DECISIONS (2) names House Prices only). ETTh1 needs an author or legal licence line
   before any label table cites it. 1GC-7RC is not a suite.
7. **Records read.** The U2 records and the stability record show census selection and sealed-test values in their
   tables. They were read for pins, CPU sets, wall times and hashes only, and no value is copied. The census result
   channels were hashed, not printed. No `block.jsonl` or `b1_manifests.json` file was opened.

## 8. What is outside this unit

G.5's code admits exactly its eight nodes and two harness pins (a review note). An expansion node joining G.5 needs a
G.5 code unit and the G.5 addendum note, with the CPU-census conditions of §6 for ETTh1 and Forest Cover and, for
Titanic and Forest Cover, their R1-TASL2-CPU replacement sets. The G.5 CPU sets themselves belong to the parallel G.5
amendment (§5.5).

## 9. Host checks and determinism checks: one TASL-2 session, ready for the experiment agent

One session on TASL-2 (`ssh portal_zhixu`) covers the four pins, following
`TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md` as it was done for the AR pin, then the two determinism checks. Nothing
in it reads a label or runs a G.1b chunk. Do it **before G.5 takes TASL-2's card**, because C6 needs the GPU lease
briefly. No process may use CPUs 8-11 (R1-TASL2-CPU): pin every CPU-bound step with `taskset` to the node's G.1b set
(or a set the host-check procedure names that avoids 8-11), never 8-11.

1. **Checkouts (separate clone, review m9).** Clone the harness repository into a new directory of its own,
   `git clone <harness origin> /home/dowling/r1_tracks/t1_tasl_x/harness_repo`, not into Track P's
   `/home/dowling/r1_trackp/autoresearch_harness`. In that clone, `git fetch origin <branch>` for the four kit branches,
   then `git worktree add --detach /home/dowling/r1_tracks/t1_tasl_x/harness_<titanic|metamaze|etth1|forestcover> <pin>`
   at the spec's paths. Record `git rev-parse HEAD` (it must equal the pin) and `git status --porcelain` (it must be
   empty) for each.
2. **Pins at each checkout.** Recompute `node_spec_sha256` and the committed pin (`committed_view` of
   `frozen_file_hashes`, without the data link) with the node's environment; both must equal the spec's.
3. **Environments.**
   - torch312: `uv pip freeze --python …/torch312/bin/python` must equal `sweep2/g1b/env/torch312.freeze.txt`.
   - venv_jax: `…/venv_jax/bin/python -m pip --disable-pip-version-check freeze` must equal
     `sweep2/g1b/env/venv_jax.freeze.txt`. Also record `readlink -f` of `venv_jax/bin/python`, `python3` and
     `python3.12`, the target's `python --version` (3.12.16) and the target's sha256; the EXP-ENV row needs them
     (§10). Modify nothing in `venv_jax`.
4. **Data.** Run each node's `setup_command` into `/home/dowling/r1_tracks/t1_tasl_x/data`, with the node's
   environment first on `PATH`. Each manifest sha256 must equal the spec's.
5. **C1-C7 at each pin**, the conditions of the AR procedure, with these interpreters:
   - C1, C3, C5 and C7 at each of the four pins. C5 is a real sandboxed CPU smoke from that checkout, with
     `effective: true` and empty waivers and exceptions, pinned to the node's G.1b set (Titanic 12-15, MetaMaze 0-3,
     ETTh1 16-31, Forest Cover 4-7).
   - C4 (`_sandbox_config`): torch312 for Titanic, ETTh1 and Forest Cover; **venv_jax for MetaMaze**; and
     `/usr/bin/python3`.
   - C2 once per session (it is host-wide), recorded in each record.
   - C6 (the GPU smoke with the sandbox on, under `~/r1_locks/gpu0.lock`, GPU named by its full UUID): **with
     torch312** at each torch pin (Titanic, ETTh1, Forest Cover), and at MetaMaze's pin also with torch312, because
     venv_jax has no CUDA packages and C6 tests the host, not the node. Do it before G.5 takes the card.
   - The supplementary `tests/trackg/test_trackg_isolation.py` at each pin, with the counts recorded.
6. **Four host-check records**, one per pin, under `docs/r1/reports/tasl_chain_20261122/`, named
   `TASL2_ISOLATION_HOST_CHECK_X_<NODE>_20261126.md`. Each has the four lines at column 0
   (`host_check_host: TASL-2`, `host_check_harness_commit: <pin>`, `host_check_items: 1-7 PASS`,
   `host_check_verdict: PASS`), written only if C1-C7 all pass, and captures with `SHA256SUMS`. The coordinating chat
   commits them to `main` and fills each gate as `host check <record> sha256 <its sha256>`.
7. **The two determinism checks (R1-TASL2-CPU)**, after steps 1-4 for that node and before its first G.1b job. Titanic
   on 12-15 and Forest Cover on 4-7 may run at the same time (disjoint sets); the two runs of one node run one after
   another.
   - **Evidence root** (new, outside every repository; nothing deleted):
     `/home/dowling/r1_engineering/g1bx_cpuset_determinism_<YYYYMMDD>/<node>_<set>/`.
   - **Driver.** The stability record's driver `captures/tasl2_cpu_stability_20261125/scripts/run_baseline_stability.py`
     (sha256 `848fcb9f…258b`) adapted to the node, changing only its constants: the harness checkout
     (`/home/dowling/r1_tracks/t1_tasl_x/harness_titanic` or `…/harness_forestcover`), the pin and branch, the
     environment (torch312, freeze sha256 `d2e70fe4…`), the data root (`/home/dowling/r1_tracks/t1_tasl_x/data`), the
     node's pin values from the spec (`node_spec_sha256`, `committed_pin_sha256`, `edits_manifest_sha256`,
     `data_manifest_sha256`), the provisional timeout of the node's census (Titanic 1800 s, Forest Cover 900 s), and
     the evidence root. It still calls the kit's own `run_smoke_campaign()` with an **empty proposal list**, so only
     `s000_baseline` runs (seeds 8001/8001, the census budget: Titanic 150,000 steps, Forest Cover 8,000 steps), and
     applies the reviewed baseline check. For Forest Cover, not on `CPU_ONLY_NODES` at its pin, the driver adds it
     to `tests.trackg.port_smoke_gpu.CPU_ONLY_NODES` in its own process, exactly as its census driver
     (`run_u2_smoke.py`) did; Titanic is on the list at its pin. Record the adapted driver's sha256 and its diff
     against the stability driver.
   - **Each run** (repeat n = 1, 2): first sample `/proc/stat` for 5 s and go on only if no CPU of the set was busier
     than 0.2; hold `flock -n ~/r1_locks/cpus-<set>.lock` for the run, so no G.1b job of that set can start; then

     ```
     systemd-run --user --scope --unit=g1bx-det-<node>-r<n>-<utc> --collect -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
       env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PATH=/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin:$PATH \
           VIRTUAL_ENV=/home/dowling/r1_tracks/t1_tasl/envs/torch312 AR_TRACKG_DATA_ROOT=/home/dowling/r1_tracks/t1_tasl_x/data \
       taskset -c <set> /home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python <driver> --repeat <n> \
         --runs-root <evidence>/runs/r<n> --out <evidence>/results/r<n>.json
     ```

     with `AR_TEST_CGROUP_PARENT` set to the scope inside it, as the census and stability runs did. Record per run:
     exit code, outcome, `isolation.effective`, waivers, exceptions, frozen files changed, `result_channel_sha256`
     (from the run record), `elapsed_seconds_info_only`, affinity, `memory.max`, `memory.swap.max`, the busy sample,
     load, harness `HEAD` and `git status`. Record hashes and wall times only: no metric value goes into the record.
   - **Pass criterion** (all of): both runs exit 0 with outcome ok, `effective: true`, waivers `{}`, exceptions `[]`,
     frozen files changed `[]`; both `result_channel_sha256` equal the spec's census baseline sha256 (Titanic
     `77a834ecf04cfff506bc0c46368dbf8e87f31dedb184035b422e74c4abfce9d4`, Forest Cover
     `bcfc9b5d296a07335f46ec467c68ca7e282355882fccd44f9ea7f68cd628140a`); each `elapsed_seconds_info_only` at most
     Titanic 207.2745 s / Forest Cover 140.109 s (1.5 × census B1); affinity equal to the set; the scope 8G / swap 0;
     the checkout at its pin, clean apart from the data link.
   - **Record**, at the path the spec names: `docs/r1/reports/tasl_chain_20261122/TASL2_CPUSET_DETERMINISM_X_TITANIC_12-15.md`
     or `…/TASL2_CPUSET_DETERMINISM_X_FORESTCOVER_4-7.md`, with captures in `<record stem>_captures/` and their
     `SHA256SUMS`. On PASS it carries these eight lines at column 0, each exactly once in the whole file (do not
     repeat them in a quoted or fenced example; a line of these keys in another casing or with markup is refused):
     `determinism_check_host: TASL-2`, `determinism_check_node: <node>`, `determinism_check_cpus: <set>`,
     `determinism_check_harness_commit: <pin>`, `determinism_check_runs: 2`,
     `determinism_check_result_channel_sha256: <the census baseline sha256 above>`,
     `determinism_check_baseline_seconds: <run 1> <run 2>` (seconds, three decimals) and
     `determinism_check_verdict: PASS`. If any criterion fails, the record says FAIL with the reason and the node's
     gate stays PENDING (the author decides, §5.4).
   - The coordinating chat commits the record to `main` and, in a later reviewed note, fills the gate with
     `determinism check <record> sha256 <its sha256>`.
8. **End state.** The GPU is idle and unleased; no process or scope is left over; no CPU lease is held; nothing is
   deleted.

## 10. Decisions

**Author decision (one): EXP-ENV, MetaMaze's environment.** Unchanged by this amendment. R1-T1-TASL-ENV names torch312
and jax312. MetaMaze's census environment is `venv_jax` (Python 3.12.16, `pip freeze` sha256 `630ed6e1…`, 56
packages), which is not jax312.

- **Option A (recommended).** Proposed row text (the gate requires the first sentence verbatim):

  > | R1-T1-X-ENV | EXP-ENV A: venv_jax is admitted as the census environment of mlgym_metamaze for its G.1b on TASL-2
  > (R1-T1-NODE-EXPANSION, spec `sweep2/t1_tasl/g1b_tasl_x_spec.json`), beside R1-T1-TASL-ENV's torch312/jax312:
  > `/home/dowling/r1_trackg_20261125/venv_jax`, Python 3.12.16, used in place and read-only, for this node only. Its
  > interpreter symlinks (`bin/python`, `python3`, `python3.12`) resolve to the uv-managed CPython 3.12.16
  > (`cpython-3.12.16-linux-x86_64-gnu/bin/python3.12`, as the census captures show), whose target path and sha256 the
  > host-check session records (prep report §9 step 3) before the first MetaMaze job; the host check refuses a
  > different target or sha256 (the jobs themselves compare the Python version and the freeze). Every job compares
  > `python -m pip freeze` and the Python version with the committed freeze `sweep2/g1b/env/venv_jax.freeze.txt`
  > (sha256 `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9`) and STOPs on any difference. Nothing
  > modifies venv_jax while the expansion G.1b runs. |

  The row id is the author's choice; the gate cites it as `env row <id>`.
- **Option B.** Build a uv environment from the freeze and re-run MetaMaze's U2 census in it (about 7 min of CPU),
  then re-issue the spec.

Without a decision, MetaMaze's gate stays PENDING; the other three nodes are not affected.

**No other decision is needed for R1-TASL2-CPU.** The row lets the Mac propose the replacement sets in this spec and
note and the coordinating chat publish them with this unit.

**For the reviewer:** the replacement sets and their validation (§2 item 3, §5.1), the determinism gate (§4, §5.2),
the timing argument (§5.3), the schedule (§5.4) and Forest Cover's amended condition (§6).

**For the coordinating chat and the experiment agent (launch steps, no decision):**
1. Run the host-check session and the two determinism checks (§9).
2. Record c1 (P2).
3. Generate the review record with the four lines (§4; the new spec sha256) and cite it in P4.
4. Publish the note with the gates that are PASS; complete the others in later reviewed notes.
5. Keep G.5's TASL-2 CPUs off the four expansion sets while those nodes run (§5.5).
6. Launch each gated node with `t1_tasl_node.sh g1b sweep2/t1_tasl/g1b_tasl_x_spec.json <node> <note> --enable` and
   `G1B_TASL_ENABLE_REAL=1`, from a published checkout of the launch commit (publish by merge, not squash or rebase).

**If not all four make the cutoff:** the cutoff applies node by node, and a late node goes to T2. With the four sets
disjoint, no node waits for another; Titanic is the one to start first.

## 11. Tests and full suite

**Targeted tests**, each file run alone with a fresh `TMPDIR` and `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, at the tip:

| file | result |
|---|---|
| `test_t1_tasl_g1b_x.py` | 146 passed (R1-TASL2-CPU: no set containing 8-11 for any node or the host, the replacement sets and every `cpu_replacement` field, the census baseline result-channel sha256 against the captures, the stability record's passing groups and the row on this checkout, the `cpu_determinism` gate and each refusal of its record, the note's `determinism_check_<node>` lines, no attempt cap, the job record's `cpus`/`census_cpus`/`cpu_replacement`) |
| `test_t1_tasl_g1bx_launch.py` | 3 passed (the built spec and table, incl. the CPU sets, census sets and determinism records; the launch commit against the template; launches from the launch commit and a docs-only child, not from the tip) |
| `test_t1_tasl_g1b.py` | 45 passed (unchanged) |
| `test_t1_tasl_g1b_ar.py` | 69 passed (unchanged) |
| `test_t1_tasl_chain.py` | 16 passed (unchanged) |
| `test_t1_tasl_crosscheck.py` | 79 passed (unchanged) |

**Full suite.** Command `/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider -rfE r1/tests` (default options),
with no lightgbm importable, `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, and a fresh `TMPDIR` per run (deleted right after it);
each run started only when no other `r1/tests` pytest was running.

Results: in the docs commit after the generated launch table (the full suite runs on the built tip).
