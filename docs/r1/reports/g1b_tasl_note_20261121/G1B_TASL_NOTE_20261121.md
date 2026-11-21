# G.1b on the TASL pair: the authorization note draft, a satisfiable launch binding, and the dry launch check

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, on `mac-g1b-auth-20261121` over published `main`
`16e0b52c`, for the queue of 21 Nov 2026 (20:57). Desk work only: no host, no run, no label, evaluation or sealed file.
Revised after review round 1.

## What is delivered

- **The note draft** `docs/r1/proposals/G1B_T1_TASL_NOTE_DRAFT_20261121.md` (approved: false). It uses the key-block
  format that `check_note` parses, from `sweep2/t1_tasl/g1b_tasl_authorization.template.md` (updated), with extra keys,
  which the parser allows. Its contents:
  - a fresh run id and the harness commit as a bare sha (both now checked against the spec);
  - the hosts with full GPU UUIDs and drivers, and the node-to-host split;
  - per node: the kit pins (node spec, committed pin and edit-manifest sha256s), the data manifest, the census record
    (at the census commit), the slowest census time and the timeout;
  - the env freezes and the census commit and report sha256s;
  - edits and runs, the projection against the cap, seal and receipts, the launch binding, the keys and the STOPs;
  - P1–P11, citing the rows and reports on `main`.

  The author makes four edits on signature: `approved: true`, `paper_commit`, `spec_sha256`, and P10 set to PASS with
  its review path. It sits under `docs/r1/proposals/` because the guarded launch-gate test expects no
  `g1b_t1_tasl_*.md` on `main` until the author signs.
- **A launch binding that can be met** (`sweep2/t1_tasl/g1b_tasl.py` `verify_launch_tasl`), a P7 gate for TASL-7
  nodes, and `check_note` checks of `run_id` and `harness_commit`. Tests are in `r1/tests/test_t1_tasl_g1b.py`
  (44 pass). `g1b_lib` (the S2-C5 binding of the sweep-2 kit) is unchanged.
- **The dry launch check** `sweep2/t1_tasl/g1b_note_dry_check.py`, with its output in
  `docs/r1/reports/g1b_tasl_note_20261121/dry_check.json`.
- **The P.4 phase-1 decision list** `docs/r1/proposals/TRACKP_P4_PHASE1_DECISIONS_20261121.md`: one page, eight
  decisions, each with a recommendation.
- **The T1 TASL code unit's review record** (`7060f90d`, unpublished until now), merged here so that the note's P4
  cites a review on `main`. It is docs only and based on `021dbc26`, which is on `main`.

## Blocking finding: the shipped launch gate could never pass

`g1b_tasl.launch` called `g1b_lib.verify_launch`, which requires all of the following:
- `HEAD` = the spec's `paper.commit`;
- that commit descends from the freshly fetched `origin/main`;
- `docs/r1/authorizations` there equals main's.

`check_note` requires the note to be on that `origin/main`, to name `paper.commit` and to bind the spec's sha256. So
the launch commit's own tree would hold a note naming that commit, and a spec that contains its own commit. No commit
can satisfy this. The sequence in the pre-launch report and its review (G1B_TASL_PRELAUNCH m3) has the same defect.

The same binding is in two other places, neither changed here because nothing in this queue launches them:
`sweep2/t1_tasl/g4_tasl.py` `launch` (G.4 needs the same fix before its note) and the sweep-2 kit's
`sweep2/g1b/g1b_switch.py`.

**The fix, `verify_launch_tasl`, requires:**
- `origin`'s URL names the spec's paper repository (https, ssh or scp form), and `ls-remote` equals the local
  `origin/main`;
- the checkout is tracked-clean, with no untracked code file (`.py`, `.sh`, `.pth`, `.so`) outside `docs/`;
- `HEAD` is published, i.e. an ancestor of or equal to `origin/main`;
- the spec file given is `HEAD`'s committed file;
- the note's `paper_commit` (= `spec.paper.commit`) is an ancestor of `HEAD` whose tree equals `HEAD`'s outside
  `docs/` and that one spec file. Code, kits, envs, tests and the other specs (G.4 included) are therefore the reviewed
  ones;
- the PLAN rows are on `origin/main`. `check_note` and `check_host_record` read the note and the host-check records
  from `origin/main`.

`main` may move on after the signature, so there is no code freeze. While the note stays byte-identical on `main`, the
hosts keep launching from the signed launch commit. Removing or changing the note on `main` stops further launches.

**The launch sequence:**
1. This unit merges; the merge is `M1`.
2. One commit sets the spec's `run_id` and `paper.commit = M1` and adds the signed note at
   `docs/r1/authorizations/g1b_t1_tasl_<date>.md`. It is published as `M2`.
3. Each host fetches and checks out `M2`, then runs nodes through `t1_tasl_node.sh g1b` with `--enable` and
   `G1B_TASL_ENABLE_REAL=1`. The hosts stay on `M2` for every node of the run, even after `main` moves on.

## The dry launch check (`dry_check.json`)

The check ran on this branch's code commit, standing in for `M1`, in a scratch origin and clone that borrow the
repository's objects read-only. The clone's `origin` is the spec's GitHub URL, rewritten to the scratch origin; the
script refuses to run unless git resolves both fetch and push to the scratch path. Nothing is written to the
repository, and the scratch directory is temporary. Every expected outcome holds (`ok: true`):

| Step | Outcome |
|---|---|
| The draft parses: 43 fields, no duplicates | PASS |
| The draft as drafted | STOP on `approved` (unsigned), as intended |
| As signed, in the scratch launch commit `M2` (only `run_id` and `paper` differ from the shipped spec), TASL-2 node `mlab_imdb` | the whole gate passes up to the node job, which is stubbed: `validate_spec --launch`, `check_note` on main with run_id and harness, both keys, both host-check records on main, `verify_launch_tasl` |
| TASL-7 node `mlab_cifar10` with P7 PENDING | STOP on P7 |
| `g1b_lib.verify_launch` on the same checkout | STOP ("tracked-clean at exactly the spec's paper commit") |
| `main` moves on: unrelated code, plus a second note for the same run with a hypothetical P7 PASS. Checkout at the new main | STOP (code differs from the paper commit) |
| The same, checkout kept at `M2` with the second note copied from `origin/main`: TASL-2 node with the first note, TASL-7 node with the second | both pass up to the stubbed node job |

## Author decisions

**LB: the launch binding.**
- **A (recommended):** `verify_launch_tasl` as implemented: launch from the published, signed launch commit, with the
  named paper commit as a code-equal ancestor.
- **B:** keep `g1b_lib.verify_launch`. That works only if the self-reference is removed from both sides:
  `paper.commit` taken out of the spec, *and* `paper_commit` dropped from the note or the spec-sha binding dropped.
  This is a larger change, and nothing would then tie the note to the code that runs. Not recommended.

**XC: the R1-T1-TASL-ENV cross-host check for the TASL-7 nodes** (mlab_cifar10, mlgym_cifar10,
mlgym_breakout_minatar). The row requires their default parts to be rerun on TASL-2 with identical metrics, else that
node is re-measured on TASL-2. The comparison needs the sealed TASL-7 rows, so it can only happen after those nodes run.
P7 is therefore a precondition, not a result. It attests that the crosscheck job (its own code, spec and note) is
reviewed and published, and the rule that no TASL-7 node is accepted or assembled without identical TASL-2
default-part metrics.
- **A (recommended):** sign this note now with P7 PENDING; launch the four TASL-2 nodes (≈ 14 GPU wall-hours).
  - The G.1b spec is final now and is not changed again. The crosscheck has its own spec file (with the TASL-2
    `jax312` env, which exists there per the pre-launch report) and its own script, built and reviewed as the next desk
    unit (≈ 1 GPU-h).
  - Once it is on `main`, a second G.1b note releases the TASL-7 nodes. It carries the same `run_id`, `paper_commit` and
    `spec_sha256`, with P7 PASS citing the crosscheck review.
  - The TASL-7 nodes launch from the same checkout `M2`, with the second note copied from `origin/main`. Every job
    record then carries the same spec sha256, so `assemble` can join all seven nodes. The dry check shows this route.
- **B:** build the crosscheck first, then sign one note with P7 PASS. One note and simpler records; G.1b starts later.
- **C:** move all seven nodes to TASL-2. No crosscheck is needed, but this takes ≈ 28 GPU wall-hours in series on one
  host and changes the reviewed node-to-host split, so it needs a spec change and a review.

**AR: autoresearch_fixedtokens.** R1-TRACKG-G3-EARLY lets it join "as soon as its U2 passes". Its U2 result is
accepted conditional on C1–C5 (U2_ISO_AUTORESEARCH_RESULT_REVIEW), and those conditions are only partly applied. There
is also no reviewed G.1b spec entry for it. Its census row review (TRACKG_U4_CENSUS_AR_ROW_REVIEW_R6) is NOT ACCEPTED,
on record-only traceability MAJORs with no BLOCKING finding; the row does not wait for that.
- **A (recommended):** not in this run. A separate G.1b run for it follows once C1–C5 are applied and a spec entry is
  reviewed: ≈ +28 GPU-h at 218.951 s per run, giving ≈ 56 GPU-h in total, ≈ 84 at sensitivity, under the 100 cap.
- **B:** wait and run all eight together. This delays G.1b, and with it G.4.

**RUNID: the run id.** Recommended `g1b-tasl-20261121-b`. The ENGINEERING dry runs used `g1b-tasl-20261121-a`, whose
sealed complete attempts exist on both hosts. Reusing it would make `next_attempt` refuse those nodes, and the dry
attempts could be assembled (dry-run review M2).

## Conditions of the earlier reviews (pre-launch review, dry-run review)

Both reviews held EVIDENCE blocked. The note's P4 cites this table.

| Condition | Disposition |
|---|---|
| Pre-launch B1: cross-host default check absent | Open, as P7 / decision XC. The code refuses TASL-7 nodes until P7 PASS; this note launches TASL-2 nodes only. |
| Pre-launch M1: TASL-7 `jax312` + `XLA_FLAGS` end-to-end proof | Closed by the TASL-7 dry run (dry-run review, M1 closed in substance). |
| Dry-run M2: dry attempts in the real run id | Closed by RUNID (`g1b-tasl-20261121-b`). |
| Pre-launch m1: TASL-2 binding says "all seven passed" while §3 item 7 (CUDA IPC) is untested | Interpretation recorded in P2: "1-7 PASS" is the launch-schema value; item 7 is untested; none of the seven nodes calls `cuda_share` or `cuda_open` (at harness `c025f89a` they appear only in each node's copied `ar_isolated.py` library). The binding text is not edited, so its sha256 and both specs stay as reviewed. |
| Pre-launch m3: launch-commit sequence | Closed by `verify_launch_tasl` and the sequence above. |
| Pre-launch m4: note does not name the harness commit | Closed: `harness_commit` in the note and template, checked by `check_note`. |
| Pre-launch m7: G.4 Tailscale name resolution | A G.4 condition; not needed for G.1b (no proposer). |
| Pre-launch m8: census sha annotation | Closed in the note's `census` line. |
| Pre-launch m9: TASL-2 precheck still says spec sha PENDING | Left as recorded (a report of that time). P11 annotates it, and the spec binds the host-check sha `681011b2`. |
| Pre-launch m2, m5, m6; dry-run m1–m4 (report and procedure text) | ENGINEERING-prep text only; no launch condition. Real jobs start through `t1_tasl_node.sh g1b`, which the T1 TASL code review accepted. |
| Dry-run m5: the `mlgym_houseprice` CPU path (cpus 8-15) not exercised by a dry run | Residual, disclosed. Its first real attempt is the first exercise. A refusal before any run uses up nothing, and an infrastructure STOP allows a new attempt. |
| Dry-run m6: seal receipts with a null `node_log_sha256` | Specific to the dry-run wrapper. `t1_tasl_node.sh` writes the log under `<runs_root>/<run_id>/_logs/`, which `seal` binds (noted in the note's `seal` line). |

## Notes

- The label is ENGINEERING_ONLY because the parser requires it: G.1b measures noise floors and reads no label. The
  note authorizes the real D21 runs (3,220), which the pre-launch report called the "EVIDENCE" step.
- The census report sha256 in the spec (`146b1114…`) is the census commit's copy. Main's copy (`d7f8f8aa…`) adds the
  autoresearch row and rewrites prose and acceptance text; the seven node rows are unchanged. The per-node census
  records are at the census commit `76f1d7ba`, not on `main`.
- Projection, from `validate --launch` on the shipped spec: 28.262 GPU-h (TASL-2 14.06, TASL-7 14.202), sensitivity
  41.644, plus 7.168 CPU core-hours for `mlgym_houseprice`; within the 100 GPU-h cap. The crosscheck adds about 1 GPU-h.
- Not changed, but considered: `-uno` remains for untracked non-code files (logs and captures under the checkout);
  untracked code files are refused.
