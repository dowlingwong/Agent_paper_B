# G.1b on the TASL pair: the authorization note draft, a satisfiable launch binding, and the dry launch check

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, on `mac-g1b-auth-20261121` over published `main`
`16e0b52c`, for the queue of 21 Nov 2026 (20:57). Desk work only: no host, no run, no label, evaluation or sealed file.

## What is delivered

- **The note draft** `docs/r1/proposals/G1B_T1_TASL_NOTE_DRAFT_20261121.md` (approved: false). It is in the key-block
  format `check_note` parses, from the template `sweep2/t1_tasl/g1b_tasl_authorization.template.md`, with extra keys
  (the parser allows them). It contains:
  - a fresh run id;
  - the hosts with full GPU UUIDs and drivers, and the node-to-host split;
  - the harness pin `c025f89a`;
  - per node: the kit pins (node spec, committed pin and edit-manifest sha256s), the data manifest, the census record,
    the slowest census time and the timeout;
  - the env freezes and the census commit and report sha256s;
  - edits and runs, the projection against the cap, seal and receipts, the keys and the STOPs;
  - P1–P11, each citing its row or report on `main`.
  
  Three fields can only be filled at the launch: `approved`, `paper_commit` and `spec_sha256`. It sits under
  `docs/r1/proposals/` because the guarded launch-gate test expects no `g1b_t1_tasl_*.md` on `main` until the author
  signs.
- **A launch binding that can be met** (`sweep2/t1_tasl/g1b_tasl.py` `verify_launch_tasl`) and a P7 gate for TASL-7
  nodes, with tests in `r1/tests/test_t1_tasl_g1b.py` (42 pass). `g1b_lib` (the S2-C5 binding used by the sweep-2 kit)
  is unchanged.
- **The dry launch check** `sweep2/t1_tasl/g1b_note_dry_check.py`, with its output in
  `docs/r1/reports/g1b_tasl_note_20261121/dry_check.json`.
- **The P.4 phase-1 decision list** `docs/r1/proposals/TRACKP_P4_PHASE1_DECISIONS_20261121.md`: one page, eight
  decisions, each with a recommendation.
- **The T1 TASL code unit's review record** (`7060f90d`, unpublished until now), merged here so that the note's P4
  cites a review on `main`.

## Blocking finding: the shipped launch gate could never pass

`g1b_tasl.launch` called `g1b_lib.verify_launch`, which requires all of the following:
- `HEAD` = the spec's `paper.commit`;
- that commit descends from the freshly fetched `origin/main`;
- `docs/r1/authorizations` at that commit equals main's.

`check_note` requires the note to be on that same `origin/main` and to name `paper.commit`. So `main` would have to name
a commit that descends from `main` itself, and no commit can satisfy that. The sequence in the pre-launch report and its
review (G1B_TASL_PRELAUNCH m3: "the branch commit becomes `paper.commit`, then the signed note binds the spec sha256")
hits the same wall: once the note is published, `main` has moved past `paper.commit`. The sweep-2 kit's
`g1b_switch.py` has the same shape. It is not changed here, since nothing in this queue launches it; it is noted for
its own unit.

**The fix, `verify_launch_tasl`, requires:**
- `ls-remote` = the local `origin/main`;
- a tracked-clean checkout at exactly `origin/main`, so the note, the spec and every authority file are main's;
- the spec file given is the committed one;
- the note's `paper_commit` (= `spec.paper.commit`) is an ancestor of `main`;
- that ancestor's tree equals main's outside `docs/` and `sweep2/t1_tasl/*_spec.json`, so code, kits, envs and tests
  are the reviewed ones;
- the PLAN rows are on `main`.

**The launch sequence then works:**
1. This unit merges, giving commit `M1`.
2. One commit sets the spec's `run_id` and `paper.commit = M1` and adds the signed note at
   `docs/r1/authorizations/g1b_t1_tasl_<date>.md`. It is published as `M2`.
3. Each host fetches and checks out `M2` exactly, then runs `run-node --note … --enable` with
   `G1B_TASL_ENABLE_REAL=1`.

## The dry launch check (`dry_check.json`)

Run on this branch's code commit standing in for `M1`, in a scratch origin and clone that borrow the repository's
objects read-only. Nothing is written to the repository; the scratch directory is temporary. Every expected outcome
holds (`ok: true`):

| Step | Outcome |
|---|---|
| The draft parses: 41 fields, no duplicates | PASS |
| The draft as drafted | STOP on `approved` (unsigned), as intended |
| As signed (in the scratch launch commit, only `run_id` and `paper` differ from the shipped spec), TASL-2 node `mlab_imdb` | the whole gate passes (`validate_spec --launch`, `check_note` on main, both keys, both host-check records on main, `verify_launch_tasl`) up to the node job, which is stubbed |
| TASL-7 node `mlab_cifar10` with P7 PENDING | STOP on P7 |
| TASL-7 node with a hypothetical P7 PASS line | passes up to the stubbed node job |
| `g1b_lib.verify_launch` on the same launch checkout | STOP: "the launch checkout must be tracked-clean at exactly the spec's paper commit" |

## Author decisions

**LB: the launch binding.**
- **A (recommended):** `verify_launch_tasl` as implemented. Launch at the published main that carries the note, with
  the named commit as a code-equal ancestor.
- **B:** keep `g1b_lib.verify_launch` and drop `paper_commit` from the note, binding only the spec sha256. This is
  weaker: nothing would tie the note to the code that runs.

**XC: the R1-T1-TASL-ENV cross-host check for the TASL-7 nodes** (mlab_cifar10, mlgym_cifar10,
mlgym_breakout_minatar). No crosscheck job exists, and the spec has no TASL-2 `jax312` entry, although the env exists
there (pre-launch report: TASL-2 `jax312` set-equal, jax GPU works).
- **A (recommended):** sign the note with P7 PENDING.
  - The four TASL-2 nodes (≈ 14 GPU wall-hours) launch at once; the code refuses the TASL-7 nodes.
  - The crosscheck job is built and reviewed as the next desk unit: default parts on TASL-2, metric identity against
    the TASL-7 rows, a TASL-2 `jax312` spec entry, and refusal to assemble a TASL-7 node without it. It costs about
    1 GPU-h.
  - A second note (same run id and spec, P7 PASS) then releases the TASL-7 nodes.
- **B:** build the crosscheck first and sign one note with P7 PASS. Simpler records; G.1b starts later.
- **C:** move all seven nodes to TASL-2. No crosscheck is needed, but it takes ≈ 28 GPU wall-hours in series on one
  host and changes the reviewed node-to-host split.

**AR: autoresearch_fixedtokens.**
- **A (recommended):** not in this run. Its census row is NOT ACCEPTED (TRACKG_U4_CENSUS_AR_ROW_REVIEW_R6), although
  its U2 result is accepted with conditions C1–C5. A separate G.1b run follows once the row is accepted and its spec
  entry is reviewed: ≈ +28 GPU-h at 218.951 s per run, giving ≈ 56 in total and ≈ 84 at sensitivity, under the 100 cap.
- **B:** wait and run all eight together. This delays G.1b, and with it G.4.

**RUNID: the run id.** Recommended `g1b-tasl-20261121-b`. The ENGINEERING dry runs used `g1b-tasl-20261121-a`, whose
attempt directories exist on both hosts, so reusing it would make the dry attempts count.

## Notes

- The label is ENGINEERING_ONLY because the parser requires it: G.1b measures noise floors and reads no label. The
  note authorizes the real D21 runs (3,220 runs), which the pre-launch report called the "EVIDENCE" step.
- The census report sha256 in the spec (`146b1114…`) is the census commit's copy; main's copy (`d7f8f8aa…`) adds the
  autoresearch row only. The note records both.
- Projection, from `validate --launch` on the shipped spec: 28.262 GPU-h (TASL-2 14.06, TASL-7 14.202), sensitivity
  41.644, plus 7.168 CPU core-hours for mlgym_houseprice; within the 100 GPU-h cap.
