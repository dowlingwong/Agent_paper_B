# G.1b — T1 GPU-node noise floors on NEMO2 H200 (HTCondor): job design

**Status: PREPARED — NOT SUBMITTED, NOT AUTHORIZED.** ENGINEERING_ONLY. No job was submitted, no GPU was used and
no labels were read. Submission needs four things: the author-signed note
`docs/r1/authorizations/g1b_t1_h200_<YYYYMMDD>.md` on published `main`, the two switch keys, the cluster's
host-check PASS (P1), and the author's decisions R1-G1B-EDITS (§2), G1B-TIMEOUT (§2a) and G1B-IMAGE (§2b). Written by the Mac-desk agent (Claude),
AI-assisted.

**Authority (published `main` `94db94bb`).**

| Row | What it fixes here |
|---|---|
| R1-T1-HOST-H200 (20 Nov) | G.1b runs on NEMO2 H200 (HTCondor). One GPU model per table, and the noise floor and the labels of a table use the same model. The cluster agent first checks the harness isolation inside the HTCondor container on H200; if that fails, the whole T1 table moves to Ada. |
| R1-TRACKG-G3-EARLY (20 Nov) | The T1 nodes are the six isolated-U2 census nodes: `mlab_cifar10`, `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`. `autoresearch_fixedtokens` and `mlgym_houseprice` join after their U2 passes. G.1b starts now. |
| R1-G1B-CAP (16 Nov) | 100 GPU-h cap for G.1b alone; a projection above it is an author STOP. The D21 protocol is unchanged ("552 runs per node"). |
| D21 rule, D21 uniform application (22 Oct) | 30 seeds per condition (train, split, joint; `"vary"` split). The node qualifies with ≥ 2 material edits (resolved, \|Δ̂_J\| > 2 se, \|Δ̂_J\| ≥ 0.002), mean plug-in P(wrong) ≥ 0.10 and σ_joint > 0. The rule applies to every node, with no exception after the results. Library versions go in every manifest. |
| R1-BX-D5 | Fixed step budget (the nodes' own `run_budget`), one GPU model per table. |
| R1-HARNESS-ISOLATION, READY 60 | Editable code in a sandboxed worker. The run record says `effective` only with no waiver and no exception. |
| R1-TRACKG-PORT-DECISIONS (4) | Node timeout = 3 × the census run time; a timeout is the run's failure (a divergent row), not an infrastructure rerun. |
| R1-QTORCH-AMEND, R1-SWEEP2-IMAGE | Image v2 (gpu `sha256:b1144ece…`) is approved **for Track P**; R1-SWEEP2-IMAGE says "image v2 只用于 Track P" (v2 is for Track P only). The 20 Nov task names v2 for G.1b, but no PLAN row authorizes it for the T1 table yet: author decision G1B-IMAGE (§2b), note field P6. |

**Revision 2 (after review round 1, `G1B_H200_REVIEW` B1–B3, M1–M8, N1–N6).** The data pin no longer depends on
the host path; data bytes are bound to the census data manifest; determinism compares outcomes; the first-node gate
tests the infrastructure, not qualification; the switch carries the S2-C5 launch binding and the note binds the paper
commit and the spec sha256; sealed jobs are assembled and verified before the summary; the D21 double check is
independent of `e1_report`; the requested slot-hours are capped too.

**Code.**
- Paper branch `mac-g1b-h200-20261120`, under `sweep2/g1b/`:
  - `g1b_lib.py`
  - `g1b_job.sh`
  - `g1b_render_jdl.py`
  - `g1b_switch.py`
  - `g1b_spec.json`
  - `g1b_authorization.template.md`
  - `env/torch312.freeze.txt` and `env/jax312.freeze.txt`
  - tests in `r1/tests/htcondor/test_g1b_h200.py`
- Harness branch `mac-trackg-t1-20261120`. It merges the three isolated kits at the experiment agent's pushed tips:
  - mlab `fb6e7d7`, mlgym `f07875d` and ar `448f682`, all on the accepted isolation fix `5403392`;
  - the HTCondor `gpu_identity` commits of `r1-local-trackg-htc-20261114`;
  - a new engine, `src/autoresearch/trackg/noise_floor.py`, with tests in `tests/trackg/test_trackg_noise_floor.py`;
  - the G.4 pilot runner (`pilot_g4.py`) and the campaign `record_gate`.

  `g1b_spec.json` → `harness.commit` names the harness commit with all of these. The harness branch is delivered as
  a bundle; the job clones `harness.repo` at that commit, so **the commit must be pushed to GitHub before launch**
  (the experiment or cluster agent pushes it; cluster test 7 in §6).

  One harness commit then holds all eight T1 candidate nodes, so the noise floor and the later label table can share
  one pin. The L40S preparation of 16 Nov (`g1b-noise-20261116` @ `231b6693`) is kept unchanged in
  `sweep2/g1b/superseded_l40s_20261116/`.

## 1. Protocol (D21, unchanged)

Per node, configurations `c0` (the baseline) and `c1 … cN` (the node's declared representative edits, from
`representative_edits/manifest.json`, applied as diffs on a fresh copy of the node by `WorkingCopyRunner`) run under
these conditions:

| Condition | Seeds | Seed environment |
|---|---|---|
| `default`, `default_repeat` | the node's own defaults (no seed variable set) | fixed-seed determinism pair |
| `train` | 1001–1030 | `AR_TRAIN_SEED` = s; split at the node default |
| `split` | 2001–2030 | `AR_SPLIT_SEED` = s; training seed at the node default |
| `joint` | 3001–3030 | both = s (paired d_s = m(c_k, s) − m(c0, s)) |

This is the E1 convention (rows match `r1.noise.e1_report`, `(None, None)` for the defaults). The seeds are disjoint
from the B.2 audit seeds 7001–7010 and the exam seeds 9001+; the engine refuses both ranges. Runs per node are
(N + 1) × 92.

**One job per node, four parts.** The `default` part runs first, then `train`, `split` and `joint`. Determinism
compares **outcomes** per configuration: two successful runs must give the bit-identical metric, and two failed runs
must fail the same way (for example both `divergent:timeout`). A configuration that diverges at its default is
reported (`divergent_configs_at_default`) and, as in `e1_report`, gives no paired comparison; it is not
non-determinism. If any pair has different outcomes, the job STOPs before any seeded run with `stop_class: node`:
the node does not qualify ("determinism"), and the infrastructure is shown to work. Every other STOP is
`stop_class: infrastructure`. One GPU training run at a time (`workers = 1`).

## 2. Author decision G1B-EDITS: the declared edit count (recommendation: A)

Every ported node declares **four** representative edits (E1–E4). The kits allow 3–5, and the U3 reviews accepted
four. R1-G1B-CAP's "552 runs per node" assumes **five** edits (6 configurations × 92), as in the CPU E1 measurement.
With four edits a node has 5 × 92 = **460** runs. The two cannot both hold, so the author must choose:

- **A (recommended): measure the four declared edits; 460 runs per node.**
  - No kit or pin changes: the census pins and the U2 smokes stay valid.
  - The rule is applied uniformly within T1, since every T1 node has four edits.
  - Run time: 26.8 GPU-h (28.8 with job startup).
  - Disclosure: D21's selection threshold of "≥ 2 material edits" is applied out of four edits on T1 nodes, against
    five on T0 nodes. That makes qualifying slightly harder on T1, and the screening funnel (R1-BX-D12) says so.
- **B: add a fifth declared edit per node before any measurement; 552 runs per node.**
  - This is a kit change in six nodes: one new diff, re-declared manifests, and composability tests.
  - `representative_edits/` is a frozen path, so every node's frozen pin changes. The census's committed and
    deployed pins would no longer match, and the U2 smokes would have to be repeated (or the census amended).
  - Run time: 32.1 GPU-h (34.1 with startup). It takes about a day of desk work plus re-smokes on Ada.

The job handles either choice: `g1b_spec.json` → `edit_count.n_edits_per_node` (uniform across nodes) and
`runs_per_node` = (n + 1) × 92. Both the job and the switch refuse to launch until `edit_count.authority` starts
with the PLAN row id `R1-G1B-EDITS`, and the switch checks that the row is on published `main`.

## 2a. Author decision G1B-TIMEOUT: the per-run timeout basis (recommendation: B)

R1-TRACKG-PORT-DECISIONS (4) sets the node timeout to 3 × the census run time, and the census used the B1 baseline
time (`c0`). An edit can make a run slower. The review found one known case: `mlab_ogbn_arxiv` E4 took 21.8 s in the
census smoke, while the timeout is 3 × 5.651 = 16.95 s. Every E4 run on that node would then time out: 92 divergent
rows, no paired joint deltas, so E4 cannot be material. The D21 verdict for that node would reflect the timeout
basis, not the noise.

- **A: keep 3 × the B1 baseline time.** No change. The ogbn E4 runs are divergent rows, and the screening funnel
  says why. ogbn then has three measurable edits, so it qualifies only with two of three material.
- **B (recommended): use 3 × the slowest executed census record of the node (baseline or declared edit), the same
  rule for all six nodes.** Read the basis from the census records (the cluster agent has them; the desk does not).
  It keeps the timeout as a guard against hangs, not a filter on edits. The walltime grows with it.
  Implementation: one spec field per node (`timeout_basis_seconds`, from the census records), passed to the engine
  as `measured_run_seconds` for the timeout only, and to the walltime. This is not built until the author decides.
- **C: drop E4 on ogbn.** That breaks the uniform edit count (R1-G1B-EDITS) and is not recommended.

The spec carries `timeout_decision` (basis `census_baseline_x3`, i.e. A, the only basis implemented). The job and the
switch refuse to launch until `timeout_decision.authority` names the PLAN row R1-G1B-TIMEOUT; the switch checks the
row on main and the note's P7. Option B needs a reviewed change (the spec field and the engine) and a row amending
R1-TRACKG-PORT-DECISIONS (4) ("baseline × 3") before it can be chosen. Under A, an ok-versus-timeout pair at the
default seeds is classified as non-determinism; the screening funnel names the timeout as the cause.

## 2b. Author decision G1B-IMAGE: the container image for the T1 table (recommendation: A)

One digest per table. G.1b, G.4 and G.5 must use the same image.

- **A (recommended): image v2 (gpu `sha256:b1144ece…`), recorded by a new author row for the T1 table.** The job
  uses the image only for `uv`, Python 3.12.16 from `/opt/r1/pythons`, `git`, `nvidia-smi` and (G.4/G.5)
  `llama-server`; the node environments are rebuilt from the census freezes, so the image's own Python
  environments do not enter the runs. This is what the 20 Nov task names.
- **B: the sweep-2 image v1 (`sha256:69b06b35…`).** Keeps the R1-SWEEP2-IMAGE split (v2 for Track P only), and its
  `llama-server` is the one sweep 2 pinned. It needs a check that v1 has `uv` and Python 3.12.16 (not verified from
  the desk), and a re-render of all three jobs with the v1 digest.

The note's P6 records the row; the switch refuses a note without it.

## 3. What one job does (`g1b_lib.py job`)

The job runs inside the v2 gpu container. It runs as the job's uid, which must not be root.

1. **Image and host.**
   - The sha256 of `/opt/r1/VERSIONS.txt` must equal the spec's `image.versions_sha256` (filled by the cluster agent
     from a v2 job record).
   - `nvidia-smi` must list exactly one GPU, named `NVIDIA H200`.
   - The job records the host, uid, CPU affinity and kernel.
2. **Pinned code.**
   - Clone the paper repository at the launch commit; the staged `g1b_lib.py` must equal that commit's copy.
   - Clone the harness at `harness.commit`, clean.
3. **Environment.**
   - Build the census environment with the image's `uv` (`UV_PYTHON_DOWNLOADS=never`, Python 3.12.16 from
     `/opt/r1/pythons`): `uv venv`, then `uv pip install --no-deps -r env/<torch312|jax312>.freeze.txt`.
   - The resulting `uv pip freeze`, sorted, must equal the committed freeze. That freeze is the Ada census freeze:
     torch312 `d2e70fe4…` with 77 lines, used for the five torch nodes; jax312 `80a455c6…` with 68 lines, used for
     Breakout.
   - So the H200 runs use the same libraries as the census, and D21's "library versions in every manifest" holds.
   - The image's own envs are not used for the nodes: env3 has numpy 2.4.4 and transformers 5.19, and no JAX.
4. **Data.**
   - Run the node's own `setup_command` with `AR_TRACKG_DATA_ROOT` in the job scratch. Its log is kept on failure
     and on its 7,200 s timeout.
   - The engine requires the node's **committed** frozen-file pin to equal the census value (for example `1f047ad7…`
     for `mlab_cifar10`). The census's deployed pin records the `data` symlink as `link:<target>`, which is a host
     path, so it cannot match on H200 and is not used.
   - The data bytes are bound separately. The node's `setup_command` writes `data/data_manifest.json` (per-file
     sha256 and size of the prepared data plus a source block of library versions and dataset revisions; no
     timestamp or host path). The engine requires the sha256 of that file to equal the census
     `data_manifest_sha256` (for example `43fdf860…` for `mlab_cifar10`; `null` for Breakout, which has no data and
     must have no `data` entry). Every run then checks each listed file against the manifest and refuses unlisted
     files (`ar_data.verify`, the nodes' own code). A download that differs from the census bytes, or a moved
     dataset revision, is a STOP.
5. **cgroup.** The job's own cgroup v2 directory, from `/proc/self/cgroup`, must be writable by the job's uid and
   have `cgroup.kill`. The runs' cgroups are created below it. Without delegation the job STOPs: there is no
   `no_cgroup` waiver.
6. **Runs.** For each part, the job writes the chunk file and runs
   `python -m autoresearch.trackg.noise_floor` from the built environment and the pinned harness. The engine:
   - re-validates the chunk: the canonical run expansion, the seed blocks, no waiver, timeout factor 3;
   - checks the node spec sha256, the committed pin, the data manifest and the declared-edit manifest;
   - resolves the HTCondor GPU assignment to a full UUID (`gpu_identity`);
   - runs every run through `WorkingCopyRunner` with `measured_run_seconds` = the census time, the timeout
     (3 × that) and an empty waiver set.
7. **The unisolated-run gate.**
   - Every executed record must have `isolation.effective: true`, `waivers {}`, `exceptions []`, `log_intact: true`,
     and a parent that was neither traced nor dumpable at the accept.
   - Otherwise the chunk STOPs at that run. The record stays on disk and no row is written.
   - The job re-checks the same six fields on every row before the merge, and `assemble` and the summary check them
     again.
   - Further STOPs: an infrastructure failure (a host problem, so the job stops rather than leave a gap), an
     unapplied declared edit, an integrity error, and not enough time before the deadline (walltime − 300 s). The
     engine subprocess's timeout is the time left to that deadline, so the job always writes its record before the
     walltime; on that timeout the engine log is kept.
   - Every STOP, including one during spec validation, still writes `job_record.json` (with `stop` and
     `stop_class`), `out.tar` when `out/` exists, and `SHA256SUMS`.
   - A divergent run, for example a timeout or a non-finite loss under an edit, is an E1 row with `success: false`.
8. **Outputs.**
   - Merged `out/runs.jsonl` (the validation metric only; sealed test values stay in the run records and are not
     copied), `out/edits.json`, the run records and logs, the setup and engine logs.
   - `job_record.json` (`g1b_h200_job_record/1`): image, host, GPU, code pins, environment, data root, cgroup, parts,
     determinism, run counts, STOP.
   - `out.tar` and `SHA256SUMS`.
   - HTCondor transfers `out.tar,job_record.json,SHA256SUMS,g1b_run.log`. Sealing to `/ceph/srv/dwong/paperb/g1b_h200/<run_id>/<node>/`
     is the operator's `g1b_lib.py seal` step. It verifies the sums, never overwrites, and writes
     `SEAL_RECEIPT.json` with the job record's sha256, the stop class and the sha256 of `g1b_run.log` (the wrapper
     log is written after `SHA256SUMS`, so the receipt binds it).

**Assembly** (`g1b_lib.py assemble g1b_spec.json <dest> <sealed node dirs…>`). Each sealed directory must have its
receipt (binding the job record), verify against `SHA256SUMS`, and hold a job record of this run id, this spec file
(sha256), the spec's harness commit, the v2 image and the H200, with `stop_class` null or `node`. The rows are
unpacked from `out.tar` (a node-class STOP contributes its default rows only), re-checked against the gate, and
written with `ASSEMBLY.json` (jobs, record hashes, GPU UUIDs, hosts, the rows' sha256).

**Offline summary** (`g1b_lib.py summarise <assembled dir> g1b_spec.json --paper-root .`) performs these checks:
- the run directory is the assembly (`ASSEMBLY.json` binds `runs.jsonl`) and holds every spec node;
- exact coverage per node, so a missing, duplicate or extra row STOPs (a node-class STOP: the default part only);
- the gate on every row (six fields);
- determinism per node by outcome (a non-deterministic node does not qualify);
- the pinned `r1.noise.e1_report.summarise`, with a check that its D21 constants are unchanged;
- an **independent** recomputation of every edit's quantities from the rows (`paired_joint_stats`: paired joint
  deltas, resolved, material, P(wrong); fewer than three paired seeds is "insufficient", as in `e1_report`). Any
  difference from `e1_report` in `material` or P(wrong) (> 1e-9), or in the node verdict, is rule drift and a STOP.

It writes `summary.json` with the screening funnel, the paired n per edit, the divergent rows per configuration and
`e1_report`'s proposed split policy (recorded, not applied: the split policy is the declared `"vary"`).

## 4. Times, walltime, projection (census values, Ada RTX 6000 Ada, 19 Nov)

`run_seconds` is the census B1 elapsed time per run (`TRACKG_U2_ISO_RESULTS_20261119.md` on `ops-tasl-20261116`
@ `6bbf4b3e`, sha256 `8e228778…`). The requested walltime is startup reserve 3,600 s + ⌈runs × run_seconds × 1.5⌉.
GPU-h is runs × run_seconds plus a declared startup estimate of 1,200 s per job (one GPU per job, `workers = 1`).

| Node | Budget | run s (census) | Runs (A) | Run GPU-h (A) | Walltime request (A) | Run GPU-h (B, 552) |
|---|---|---|---|---|---|---|
| mlab_cifar10 | 1,950 steps | 12.297 | 460 | 1.57 | 12,085 s | 1.89 |
| mlab_imdb | 1,000 steps | 64.142 | 460 | 8.20 | 47,858 s | 9.84 |
| mlab_ogbn_arxiv | 356 steps | 5.651 | 460 | 0.72 | 7,500 s | 0.87 |
| mlgym_cifar10 | 7,820 steps | 31.731 | 460 | 4.05 | 25,495 s | 4.87 |
| mlgym_fmnist | 9,380 steps | 34.376 | 460 | 4.39 | 27,320 s | 5.27 |
| mlgym_breakout_minatar | 2,000,000 env steps | 61.248 | 460 | 7.83 | 45,862 s | 9.39 |
| **Total** | | 209.445 | 2,760 | **26.76** (28.76 with startup) | 46.1 slot-h requested | **32.12** (34.1) |

- **Cap.** Both options are far under R1-G1B-CAP (100 GPU-h). The validator recomputes the projection and STOPs above
  the cap. It also STOPs when the requested walltimes (46.1 slot-h here) exceed the cap, so the cap bounds the
  table even if every job runs to its walltime. A spec may lower the cap but never raise it.
- **Walltime limit.** The longest job (imdb, 13.3 h) is under the 86,400 s job limit.
- **Timeouts.** The H200 run times are not yet measured; the census times are from Ada. The timeout (3 × the census
  time) and the walltime (× 1.5) leave room. A node that is more than 3 × slower on H200 times out run after run, and
  its job STOPs at the deadline.

## 5. JDL and submission

- **JDL.** `g1b_render_jdl.py <spec> <stage>` writes one JDL per node:
  - container universe with the v2 digest;
  - `request_cpus 8` (the census ran each run on 8 CPUs: 0–7 for the mlab nodes, 8–15 for the mlgym nodes),
    `request_memory 24576` MB, `request_disk 62914560` kB. The census capped each run at 8 GiB inside the run's
    scope; here the job-level request is 24 GiB and the engine sets no per-run memory cap (cluster test 9);
  - `request_GPUs 1` and `+RequestWalltime` per node;
  - `periodic_hold (NumJobStarts > 1)`, so a job is never resumed;
  - requirements `GPUs >= 1`, `GPUs_DeviceName =?= "NVIDIA H200"`, X86_64, Linux, `Cpus >= 8`, with no site pin
    (R1-SWEEP2-MEASURED-GPU pattern);
  - `when_to_transfer_output = ON_EXIT_OR_EVICT`.

  `--preview` renders from a spec with placeholders: the executable is `PREVIEW_NOT_SUBMITTABLE_…` and the manifest
  says `preview: true`.
- **Switch.** `g1b_switch.py` (the S2-C5 two-key pattern) submits only when:
  - the note is byte-identical to its blob on the local `origin/main` and parses, with `approved: true` and P1–P5
    recorded as PASS, citing R1-T1-HOST-H200, R1-TRACKG-G3-EARLY and R1-G1B-EDITS;
  - the run id, image digest, **paper commit, staged spec sha256**, VERSIONS sha256, harness commit, node list, edit
    count, runs per node and GPU-hours match the staged spec;
  - the staged files and JDLs equal a fresh canonical render;
  - both `--enable` and `G1B_ENABLE_REAL=1` are given;
  - the S2-C5 launch binding passes (`g1b_lib.verify_launch`, ported from `s2_c5_switch._verify_launch`):
    `git ls-remote origin refs/heads/main` equals the local `origin/main` (so main was fetched), the checkout is
    tracked-clean at exactly the spec's paper commit, that commit descends from main, `docs/r1/PLAN.md` and
    `docs/r1/authorizations/` equal main's, and the PLAN rows R1-T1-HOST-H200, R1-TRACKG-G3-EARLY, R1-G1B-CAP and
    R1-G1B-EDITS are on main.

  It submits `mlab_ogbn_arxiv` (the shortest node, about 2 h) alone first. The other five nodes need `--first-record`
  = `/ceph/srv/dwong/paperb/g1b_h200/<run_id>/mlab_ogbn_arxiv/job_record.json`. The switch checks that the sealed
  directory verifies against `SHA256SUMS`, that the receipt binds the record, and that the record has this run id,
  spec sha256, harness commit, image and H200, the census freeze sha256, a data step, a cgroup, a complete default part,
  and either no STOP with all rows written or a `node`-class STOP (determinism). An infrastructure STOP blocks the
  other nodes. The gate tests the H200 path (environment, data, cgroup, isolation gate, engine), not whether ogbn
  qualifies.

## 6. Needs a cluster test (flagged; the cluster agent is checking container isolation separately)

1. **Isolation inside the container on H200 (P1, R1-T1-HOST-H200):**
   - unprivileged user, mount, PID and network namespaces and `pivot_root` inside the HTCondor container;
   - Yama `ptrace_scope` ≥ 1 on the execute node;
   - a delegated cgroup v2 directory for the job's uid, with `cgroup.kill` (kernel ≥ 5.14);
   - a non-root job uid;
   - a sandboxed smoke whose record shows `effective: true`.

   Any failure here moves the T1 table to Ada.
2. **The v2 image's `/opt/r1/VERSIONS.txt` sha256** and the presence of `/opt/uv/uv`, Python 3.12.16 in
   `/opt/r1/pythons`, `git` and `nvidia-smi`.
3. **Egress from the job to PyPI and the PyTorch wheels** (torch 2.6.0 with its CUDA 12.4 libraries, about 3 GB;
   jax-cuda12 with CUDA 12.9 libraries), and **to the dataset hosts** (CIFAR-10 from cs.toronto.edu via torchvision;
   IMDb and DistilBERT, Fashion-MNIST and CIFAR via Hugging Face; ogbn-arxiv from snap.stanford.edu).
   - If a host is unreachable, stage that node's data from the submit host as a transfer input. That is a reviewed
     follow-up, and the data-manifest check stays.
4. **Data bytes on H200 equal the census bytes** (the data-manifest check). If a dataset download differs, the job
   STOPs and the author decides.
5. **JAX on H200.** The jax312 freeze carries CUDA 12.9 libraries; the H200 driver must support them.
6. **Run time on H200** against the census times (timeout margin), in particular `mlab_ogbn_arxiv` E4 (§2a).
7. **GitHub egress and pushed commits.** The job clones the paper repository at the launch commit and the harness at
   `harness.commit` from GitHub; both must be pushed and reachable from the execute node.
8. **The exact device name.** The requirement is `GPUs_DeviceName =?= "NVIDIA H200"` and the job requires
   `nvidia-smi` to say `NVIDIA H200`. If NEMO2 reports `NVIDIA H200 NVL` (or another variant), both the JDL and the
   job's `GPU_MODEL` need a reviewed change; nothing would match until then.
9. **Scratch and memory.** The wheels (about 3 GB for torch312) and the data go to `_CONDOR_SCRATCH_DIR`; the job sets
   `UV_NO_CACHE=1`, so `TMPDIR` must point there and the download must fit in `request_disk`. Check that the job-level 24 GiB request (no per-run
   8 GiB cap, unlike the census) is enforced by the job cgroup.
10. **GPU assignment variables.** `gpu_identity` resolves `NVIDIA_VISIBLE_DEVICES` and `_CONDOR_AssignedGPUs` to a full
    UUID and cross-checks `CUDA_VISIBLE_DEVICES`; index and `CUDA<n>` forms are refused. Check which forms NEMO2 sets
    inside the container.
11. **CPU affinity.** The census ran on 8 pinned CPUs; record the job's affinity (the job record has it) and check
    that `request_cpus 8` gives 8 usable CPUs inside the container.
12. **`+RequestWalltime` enforcement.** Check that NEMO2 holds or removes a job at its requested walltime, and that
    `ON_EXIT_OR_EVICT` still transfers the outputs.

## 7. STOPs (no retry, no deletion)

The pre-declared STOPs are:
- **Spec, plan and authority:** a placeholder at launch; a node missing, extra or listed twice; a non-uniform edit
  count; a projection over the cap; a walltime over 86,400 s; a wrong image or GPU model; a changed measurement
  constant.
- **Image and host:** a VERSIONS mismatch; a root uid; a GPU count other than 1 or a model other than H200.
- **Code and environment:** a clone or pin mismatch; a staged library that differs from the commit; a built freeze
  that differs from the census freeze; a Python version other than 3.12.16.
- **Data and cgroup:** the setup command fails or times out; the committed pin or the data manifest differs; no
  delegated cgroup.
- **Runs:** an unisolated record; an infrastructure failure; an unapplied edit; an integrity error; the deadline;
  non-determinism at the default seeds; a row count that differs from (N + 1) × 92.
- **Launch:** main not fetched, a dirty or different checkout, a commit not descending from main, authority files
  differing from main, a PLAN row missing on main; a first-node record that does not show a working H200 path.
- **Offline:** a sealed job without receipt, with failing sums, or not matching the table (run id, spec, harness,
  image, GPU, infrastructure STOP); coverage, a gate failure or D21 rule drift; a seal SHA mismatch or an existing
  seal target.

Outputs are always transferred and kept. A failed node is resubmitted only as a fresh submission into a new stage
directory, after diagnosis.

## 8. Residual risks

- The engine's real isolated path is exercised only on the cluster: the Mac test container runs as root without
  Yama, so the gate cannot pass here. The tests use a fake runner.
- `mlab_ogbn_arxiv` uses the official split, so its split seed probably moves nothing (σ_split ≈ 0); σ_joint carries
  the training noise. That is a measured property, not a defect.
- Breakout's evaluation keys are public constants (port report §6.2). The noise floor is unaffected, but this matters
  for the label table.
- The census was on Ada (RTX 6000 Ada). The H200 noise floor and the H200 labels share one GPU model, as
  R1-T1-HOST-H200 requires; the census times only size the jobs.
