# TASL-2 host check at harness pin `2d09f9a9` for the autoresearch G.1b spec — procedure for the experiment agent

Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026, for item 2 of the queue of 22 Nov 2026 (01:22).
ENGINEERING_ONLY. This is a procedure, not a launch authorization:
- it starts no G.1b run, writes no lease log, and reads no label;
- the third G.1b note, the author's environment row and both keys are still required before
  `autoresearch_fixedtokens` runs.

**Why.** R1-G1B-NOTE2-DECISIONS (NOTE2-AR A) signs the third note only once "a TASL-2 host check at that pin passes".
The spec `sweep2/t1_tasl/g1b_tasl_ar_spec.json` names the binding record at `hosts.TASL-2.isolation_host_check`.
`g1b_tasl.check_host_record` refuses it unless it is on published `main` with its declared sha256 and shows these lines:
- `host_check_host: TASL-2`
- `host_check_harness_commit: 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe`
- `host_check_items: 1-7 PASS`
- `host_check_verdict: PASS`

The record of 21 Nov (`TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md`) binds pin `c025f89a` and the torch312/jax312
interpreters, so it does not serve here.

**The method is that record's.** Use the same seven conditions of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3
and the same orchestration as `/home/dowling/r1_engineering/tasl2_t1_precheck_20261121/scripts/run_checks.sh`. Two
things change:
- the harness is the **second checkout at `2d09f9a9`**;
- the interpreter under test is **`ar-cond7a`** (Python 3.12.15).

## 0. Rules

- Work on **TASL-2 only** (`ssh -o BatchMode=yes portal_zhixu`). Do not contact TASL-7, HTCondor or deepthought.
- **Do not touch** these:
  - the seven-node checkout `/home/dowling/r1_tracks/t1_tasl/harness` (it must stay at `c025f89a`, clean);
  - its `runs/` and `sealed_g1b/` trees;
  - the Track P attempt-1 archive `/home/dowling/r1_trackp/runs/p3a_operator_20261027` and its lease log; `stat`
    them only.
- **No deletion.** Move anything that is in the way aside, into a `_to_delete/` folder beside it, and report it.
  Do not push. The lead commits the binding record.
- **The GPU.** GPU work holds `flock ~/r1_locks/gpu0.lock` for its duration and does not write the lease log. The
  card is never shared.
  - If the lease is held by a T1 job (a G.1b job of `g1b-tasl-20261121-b`, a cross-check job of
    `g1b-tasl-20261121-b-xc-*`, or a G.4 job of `g4-tasl-*`), wait for it to end. Never stop it.
  - Any other holder, or any compute process of another owner on `GPU-4d623e76-7587-ee15-a633-46f60d220d94` before
    or after, is a STOP.
- **CPUs.** T1 jobs use cpus 0-7 (GPU nodes) and 8-15 (`mlgym_houseprice`). Run every non-GPU step of this
  procedure under `taskset -c 16-31`: the data staging, which trains a tokenizer on about 3 cores; the checks; and
  the supplementary pytest.
- **Bytecode.** Set `PYTHONDONTWRITEBYTECODE=1` for every Python call, as the 21 Nov precheck did, so that no probe
  writes `__pycache__` into the venv in the Track P tree.
- **Root.** Run root `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/`, with `scripts/`, `captures/`,
  `logs/` and `records/`. Report times in UTC (TASL-2's clock is PST).

## 1. The second harness checkout at the pin

Commit `2d09f9a9` is on the harness branch `mac-trackg-t1-ar-20261121`, delivered in READY 78 as a bundle.
1. Make a separate clone from GitHub, as on 21 Nov. A separate clone leaves the seven-node checkout's metadata
   alone. Then fetch the branch:
   ```
   git clone --no-checkout https://github.com/dowlingwong/autoresearch_harness.git /home/dowling/r1_tracks/t1_tasl/harness_ar
   git -C /home/dowling/r1_tracks/t1_tasl/harness_ar fetch origin mac-trackg-t1-ar-20261121   # if pushed; otherwise:
   git -C /home/dowling/r1_tracks/t1_tasl/harness_ar fetch <READY 78 harness bundle> mac-trackg-t1-ar-20261121
   git -C /home/dowling/r1_tracks/t1_tasl/harness_ar checkout --detach 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe
   ```
   - The READY 78 bundle is incremental: its prerequisite is `c025f89a`, which the GitHub clone holds. So fetch from
     the bundle into the clone; do not clone from the bundle.
   - Before fetching, verify the bundle (`git bundle verify`) and check its sha256 against READY 78.
2. Record the following. Any difference is a STOP:
   - `git rev-parse HEAD` equals `2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe`;
   - `git status --porcelain --untracked-files=all` is empty;
   - `git merge-base --is-ancestor c025f89aeafc2199bf3487b4bcaa16678273c702 HEAD` gives rc 0;
   - the seven-node checkout is still at `c025f89a` and clean.

## 2. Node pins at the pin

The spec pins these values (sha256), and all must match. Compute them with the `ar-cond7a` interpreter and
`PYTHONPATH=/home/dowling/r1_tracks/t1_tasl/harness_ar/src`, as `noise_floor.check_node_pins` does:
```
from pathlib import Path
from autoresearch.trackg import isolation
from autoresearch.trackg.node_template import load_trackg_node_spec
from autoresearch.trackg.noise_floor import committed_view, frozen_pin_sha256, sha256_file
root = Path("/home/dowling/r1_tracks/t1_tasl/harness_ar")
spec = load_trackg_node_spec(root / "configs/trackg/nodes/autoresearch_fixedtokens.yaml")
node = root / "nodes/autoresearch_fixedtokens"
pin = isolation.frozen_file_hashes(node, spec.frozen_paths)
print(spec.raw_sha256, frozen_pin_sha256(committed_view(pin)), sha256_file(node / "representative_edits/manifest.json"))
```

| What | Expected |
|---|---|
| `configs/trackg/nodes/autoresearch_fixedtokens.yaml` file | `5bdce00ac51718de8547ce2d065c0e5ae83f26406ff9404f01ac42b0e2b866e7` |
| spec `raw_sha256` | `5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192` |
| committed file pin (no data link yet) | `147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc` |
| `representative_edits/manifest.json` | `55f2666a3d09aaedb8b8552aef00f8a9c27b84f1bd7df24d886904dad581e5c7` |

The Mac desk computed the last three at `2d09f9a9` and they match.

## 3. The environment `ar-cond7a`

The spec's interpreter (decision AR-ENV, option A) is `/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python`.
1. Record `uv --version` for the spec's `uv` (`/home/dowling/.local/bin/uv`). The U2 freeze was taken with uv 0.13.6.
2. Run `uv pip freeze --python /home/dowling/r1_trackp/venvs/ar-cond7a/bin/python`. Sorted, it must equal
   `sweep2/g1b/env/ar-cond7a.freeze.txt`: 122 lines, sha256
   `11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1`.
   - Capture the output.
   - On a difference, STOP and report the diff. The jobs would STOP on it too, so it is a matter for decision AR-ENV.
3. Run `python -c "import sys; print(sys.version)"`. It must give 3.12.15. Also run
   `python -c "import torch; print(torch.__version__, torch.version.cuda)"`; it should give `2.6.0+cu124 12.4`.
4. Do not install, upgrade or copy anything into this venv. If the author chooses option B (a byte copy under
   `/home/dowling/r1_tracks/t1_tasl/envs/ar-cond7a`), the copy is a separate step, and steps 2–3 are repeated on the
   copy.

## 4. Data under the T1 layout

The spec's data root is `/home/dowling/r1_tracks/t1_tasl/data`, so the node's data goes in
`/home/dowling/r1_tracks/t1_tasl/data/autoresearch_fixedtokens`. Stage it once, as `g1b_lib.run_setup` will re-check
it at every job start. This needs network access to Hugging Face and about 1 GB of disk. Run it from the node
directory of the AR checkout:
```
cd /home/dowling/r1_tracks/t1_tasl/harness_ar/nodes/autoresearch_fixedtokens
PATH=/home/dowling/r1_trackp/venvs/ar-cond7a/bin:$PATH \
AR_TRACKG_DATA_ROOT=/home/dowling/r1_tracks/t1_tasl/data HF_HOME=/home/dowling/r1_tracks/t1_tasl/hf \
  python3 prepare_data.py --out /home/dowling/r1_tracks/t1_tasl/data/autoresearch_fixedtokens
```
This is the node's own `setup_command`.

**Checks:**
- `sha256sum /home/dowling/r1_tracks/t1_tasl/data/autoresearch_fixedtokens/data_manifest.json` must give
  `ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`: 13 files, HF revision prefix `915333b`;
- the checkout's only untracked entry is now `nodes/autoresearch_fixedtokens/data` (the link to the data root);
- `git status` shows nothing else.

**STOP rules:**
- a download failure, or a revision or manifest mismatch, is a STOP;
- prepare_data refuses an `--out` that holds parquet files from elsewhere. Never reuse
  `/home/dowling/r1_trackp/data`.

## 5. The seven host conditions at the pin

Run the same seven checks as the 21 Nov binding record (its table, C1–C7), with
`HARNESS=/home/dowling/r1_tracks/t1_tasl/harness_ar` and the interpreter `ar-cond7a`. Each check is a PASS or a FAIL
with its capture:

| # | Condition (`HARNESS_ISOLATION_20261117.md` §3) | At this pin |
|---|---|---|
| C1 | Unprivileged user, mount, PID, network and cgroup namespaces are usable by the run uid. | `unshare(...)` rc 0 for the `ar-cond7a` interpreter and `/usr/bin/python3`; the uid map; a tmpfs mount; PID 1 in the new namespace. |
| C2 | Yama `ptrace_scope` ≥ 1. | Value 1; parent→child attach ok; an attach to an unrelated sibling fails with EPERM. |
| C3 | A delegated cgroup v2 subtree with `cgroup.kill` (census scope 8G / swap 0). | `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`; the pin's `isolation.RunCgroup` create → join → kill → empty → removed. |
| C4 | Not root; the interpreter's `sys.path` holds no home dir, runs tree or ancestor. | `WorkingCopyRunner._sandbox_config` passes for `ar-cond7a` (Python 3.12.15) and `/usr/bin/python3`; `broad_entries=[]`; `worker_sandbox_available=True`. |
| C5 | A real sandboxed smoke whose record shows `effective: true`. | At the pin: `effective: true`, `waivers {}`, `exceptions []`, `log_intact true`, `parent_dumpable_at_accept false`, cgroup removed. |
| C6 | A GPU smoke with the sandbox on (not §3 item 7, CUDA IPC). | Under the lease, GPU by full UUID: a CUDA tensor allocated and synchronised in the sandbox by the `ar-cond7a` interpreter; `effective: true`, empty waivers and exceptions. |
| C7 | End state. | The GPU is the same before and after with no compute process; no leftovers in the six buckets; disk recorded. The seven-node checkout is clean at `c025f89a`. The AR checkout is clean at `2d09f9a9`, except for the `nodes/autoresearch_fixedtokens/data` link from §4. The attempt-1 archive and lease log are untouched. |

Supplementary, not a §3 condition: run the pin's own `tests/trackg/test_trackg_isolation.py` in a delegated scope,
with the `ar-cond7a` interpreter, and record the pass, skip and fail counts.

The `1-7 PASS` value carries the same caveat as on 21 Nov:
- §3 item 7 (CUDA IPC) is untested on TASL-2;
- option A of `autoresearch_fixedtokens` uses no CUDA IPC. U2 confirmed this with an AST scan reporting no hits in
  `run_fixed_budget.py` and `ar_worker.py`; repeat that scan at the pin and record it.

## 6. The binding record

Write `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md`, laid out like the
21 Nov record:
- status line;
- the four key lines exactly, each at column 0 of its own line, outside any list or code block
  (`check_host_record` matches `^host_check_…`). They are written only if C1–C7 all pass; otherwise the record says
  `host_check_verdict: FAIL` with the failing items:

host_check_host: TASL-2
host_check_harness_commit: 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe
host_check_items: 1-7 PASS
host_check_verdict: PASS

- what it binds: steps 1–4 (checkout, pins, environment freeze and Python, data manifest);
- the C1–C7 table, and the supplementary test result;
- captures: a `_captures/` directory with `SHA256SUMS` (its own sha256 recorded outside the set), and
  `sha256sum -c` rc 0 on TASL-2 and after fetch;
- scope and non-authorities, as on 21 Nov.

Hand the record and its captures to the lead uncommitted. The lead then:
1. commits it to published `main`;
2. fills its sha256 into `hosts.TASL-2.isolation_host_check.sha256` of the AR spec;
3. cites it in the third note's P2 with harness `2d09f9a9`.

## 7. STOPs (report and wait; nothing is retried silently)

- The checkout cannot be made at `2d09f9a9`, or it is not clean.
- The seven-node checkout is changed.
- A node pin differs from §2.
- The freeze or Python of `ar-cond7a` differs from §3.
- The data download, revision or manifest fails (§4).
- Any of C1–C7 fails.
- The lease is busy, or a compute process of another owner is on the card.
- Disk on `/` falls below 20 GiB free.
