# G.1b cross-host check, the second G.1b note, and autoresearch_fixedtokens readiness

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, on `mac-g1b-xc-20261121` over published `main`
`985dd45d`, for item 2 of the queue of 21 Nov 2026 (22:44). This is desk work only: no host, no run, and no label,
evaluation or sealed file was opened.

## Delivered

- **`sweep2/t1_tasl/g1b_crosscheck.py`**: the R1-T1-TASL-ENV cross-host check (module docstring).
  - Per TASL-7 node and host, a spec is derived from the signed G.1b spec, which is bound by sha256 (`060aac91…`).
    It has its own run id, the node is assigned to the host, and TASL-2 gains `jax312` for Breakout. Everything else
    is unchanged.
  - The pinned `g1b_tasl.run_node_job` then runs the **default part only**: 10 runs, under the G.1b preflight, lease,
    delegated scope and row gate. The job is started by `t1_tasl_node.sh xc <spec> <node> <note> <host>`; the wrapper
    asks this script for `cpus` and `logdir` with `--host`. The attempt is sealed with `g1b_tasl.py seal`.
  - `compare --mode xc|preassembly` reads two sealed attempts and refuses any input that is not the pair the mode
    names. It checks the run ids, the spec sha256s (recomputed for the derived specs), the harness pin, receipt, sums
    and record, the row node, and one regular `out/default/runs.jsonl`. It writes a PASS/STOP verdict with a reason.
    PASS needs every default and default_repeat outcome of c0..cN present and identical (metric bit-identical, or
    the same failure) and both sides deterministic.
  - `check-note2` checks the second G.1b note: no unfilled field, no `<…>` placeholder in P7, and P7 PASS citing the
    signed cross-check note on `main` and the three step-1 PASS verdicts committed on `main`, by path and sha256. It
    runs twice: `--draft` on the unsigned note before signature, then strict mode on the published note before any
    TASL-7 node launches.
  - `assemble` is the gated assembly for the TASL-7 nodes (XC A). For each node it recomputes the pre-assembly
    comparison from the attempts given and requires it to equal the committed step-2 PASS verdict. Only then does it
    run `g1b_tasl.assemble` with the signed spec, unchanged, and it writes `crosscheck_gate.json`, which binds
    `ASSEMBLY.json` and `runs.jsonl` by sha256. The gated `summarise` refuses a run without a matching gate record.
  - Launch needs the signed cross-check note `g1b_xc_t1_tasl_<date>.md` on `main` (no unfilled field), both keys,
    both host-check records on `main`, and `verify_launch_tasl` with the cross-check spec.
- **`sweep2/t1_tasl/g1b_crosscheck_spec.json`**: run id `g1b-tasl-20261121-b-xc`, binding the signed G.1b spec.
  `paper.commit` names `10fd3343` until the launch commit sets it to the main commit carrying the code, so a launch
  before that refuses.
- **`docs/r1/proposals/G1B_XC_NOTE_DRAFT_20261121.md`**: the cross-check note (approved: false), parsed by
  `check_xc_note`.
- **`docs/r1/proposals/G1B_T1_TASL_NOTE2_DRAFT_20261121.md`**: the second G.1b note (approved: false).
  - It carries the first note's `run_id`, `paper_commit` `10fd3343`, `spec_sha256` `060aac91…` and `harness_commit`
    `c025f89a`, so the TASL-7 nodes' job records carry the same spec sha256 as the TASL-2 nodes'.
  - P7 is **PENDING** with a PASS template. It is completed only after the three step-1 verdicts are on `main` and
    `check-note2` passes. While P7 is PENDING, `g1b_tasl.launch` refuses every TASL-7 node (tested).
  - P12 holds autoresearch_fixedtokens as PENDING (below). The draft is written for decision NOTE2-AR option A.
- **Tests**: `r1/tests/test_t1_tasl_crosscheck.py` (29 tests after the round-1 revisions; 22 in round 1).
  - The shipped spec and its derived specs (nothing but the node's host, the run id, the paper commit and the TASL-2
    env changes).
  - Nine spec refusals.
  - Breakout's env requirement on TASL-2.
  - The default-part job on both hosts with the fake host tools, followed by seal, compare and the CLI.
  - Seven verdict cases, each with its reason: identical; a last-bit difference; the same failure on both hosts; a
    one-sided failure; a missing row; a config missing on both sides; non-determinism.
  - Refusals of attempts the mode does not name:
    - wrong run id, spec sha256 or harness;
    - a row of another node;
    - a receipt with the wrong host or attempt;
    - sums not listing exactly the two files;
    - unsealed, infrastructure-stopped or tampered attempts;
    - duplicate or unreadable tar members;
    - ungated rows.
  - `run_xc`: the parts are restored after a Stop, and the function is not re-entrant.
  - The launch gate.
  - Both note drafts.
  - `check-note2`.
  - The gated `assemble`.
  - The wrapper's `xc` kind, and the real `cpus`/`logdir` answers.
  - The real `verify_launch_tasl` with the cross-check spec: passes at the launch commit, refuses a later change to
    the G.1b spec or the code.

  `test_t1_tasl_g1b` still passes (45).

## Order of operations (R1-G1B-TASL-DECISIONS XC A)

1. This unit is reviewed and reaches `main` (`M`).
2. The launch commit sets the cross-check spec's `paper.commit = M` and adds the signed cross-check note.
3. The six default-part jobs run (`t1_tasl_node.sh xc`): three nodes × two hosts, about 2.1 GPU-h in all (0.58 h of
   runs plus 6 × 900 s of setup). Each attempt is sealed. Each host keeps a checkout for this launch commit separate
   from its G.1b checkout (minor 9).
4. `compare --mode xc` runs per node on the two sealed attempts. The three verdicts are committed and reviewed.
5. P7 of the second G.1b note is completed from its template. `check-note2 --draft` passes on the unsigned note and
   is recorded. The note is then signed and published, and strict `check-note2` passes and is recorded before any
   TASL-7 node launches. The TASL-7 nodes launch from a published checkout whose code equals `10fd3343` (at or before
   `985dd45d`), with the second note copied from `origin/main`.
6. **Before assembly**, `compare --mode preassembly` compares each node's G.1b TASL-7 attempt with its cross-check
   TASL-2 attempt (the row's literal comparison). The three verdicts are committed.
7. `g1b_crosscheck.py assemble` (not `g1b_tasl.py assemble`) assembles the seven nodes. It refuses unless each TASL-7
   node's recomputed comparison equals its committed step-2 PASS. `assemble` is bound to no launch commit, only to
   the spec sha256, but the cross-check spec it reads must be the launch one. So it runs from a checkout at or after
   the cross-check launch commit L, where that spec's `paper.commit` is M; at M itself the recomputed derived-spec
   sha256 differs and the gate refuses, which fails closed. Then `g1b_crosscheck.py summarise`.

**Decision XC-REMEASURE (for the author, settled in advance).** R1-T1-TASL-ENV says a non-identical node "is
re-measured on TASL-2". That re-measure cannot run under the signed spec:
- it needs that node on TASL-2, so a spec with a different sha256;
- `g1b_tasl.assemble` requires one spec sha256 and `receipt.host == node.host`.

The re-measured node therefore cannot join the seven-node table as the code stands.
- **A (recommended): decide only if a `cross_host_mismatch` occurs.** The remedy is then a reviewed unit:
  - a note-bound re-measure spec for the named node (the signed spec with that node on TASL-2 and its own run id);
  - an extension of `g1b_crosscheck.py assemble` accepting that node's attempt under its own spec and receipt;
  - a note for it.

  Nothing is built for a case that may not happen.
- **B: build it now.** About a day of desk work and review, before any data shows it is needed.

A `nondeterministic` verdict is not a cross-host result. A re-measure would be a second draw, so the verdict
returns to the author without a prescribed remedy. An `incomplete` verdict returns to the author too.

**Decision XC-NONDET (for the author, if it occurs).** A TASL-7 node whose G.1b attempt ends in a determinism STOP
(`stop_class: node`) gets a step-2 verdict STOP with reason `nondeterministic`. `assemble_gated` then refuses the
whole seven-node table, although `g1b_tasl.assemble` itself accepts node-STOP attempts and reports them as such.
- **A (recommended): decide if it occurs.** Either the author accepts that node as a reported determinism failure,
  assembled through a reviewed extension of the gate, or it is dropped from the table by a row.
- **B: build the exception now.** Not recommended before any data.

## autoresearch_fixedtokens: why it cannot join under the second note's binding, and what it needs

R1-G1B-TASL-DECISIONS: autoresearch "joins under that second note, together with the TASL-7 nodes, once its spec
entry and its U2 conditions C1–C5 are reviewed". The second note's binding is the signed spec (`060aac91…`) and the
code `10fd3343`. Autoresearch cannot run under either, for five reasons:

| Blocker | Fact | What resolves it |
|---|---|---|
| **Harness pin** | Its option-A kit (R1-TRACKG-AR-COND7; `mac-trackg-iso-ar-cond7a-20261120` @ `7330338`, code commit `0e0b820`) is **not** in `c025f89a`. | A harness commit `c025f89a` + `0e0b820`. The agent prepared it as `mac-trackg-t1-ar-20261121`:<br>• `eb14ed61`: cherry-pick, clean. Its autoresearch code equals `7330338`'s; the other seven nodes' files are unchanged.<br>• `fb3ad64f`: the port check accepts a declared earlier master. Review M4: at `eb14ed61` the master `node_lib/ar_isolated.py` (`3ba34c67…`) no longer equals the seven nodes' copies (`37d99ab0…`, the `c025f89a` master), and the check failed 7 nodes. Syncing the copies would change their frozen pins and the signed spec. The check now accepts a copy that is the current master or a declared earlier master (`37d99ab0…`, frozen in the seven T1 nodes' pins); `autoresearch_fixedtokens` must carry the current one. Test `tests/trackg/test_port_node_lib.py`; the port `test_static` checks pass (9).<br>The harness commit itself needs its own review before an autoresearch spec pins it. |
| **Host check at that pin** | `check_host_record` requires each host's record to name the spec's harness commit, and the TASL-2 record names `c025f89a`. | A TASL-2 host check (items 1–7) at the new pin, reviewed and on `main` (a cluster step); or an author ruling that the record carries over, given that the isolation code is unchanged. |
| **Spec** | An autoresearch entry cannot go into the signed spec without changing its sha256, which would break assembly of the seven nodes. An autoresearch-only spec fails `validate_spec`: it requires all seven census nodes and envs `torch312`/`jax312` at Python 3.12.16, while autoresearch's env is `ar-cond7a`, Python 3.12.15, freeze `11def6ad…` (122 lines). | A separate autoresearch G.1b spec with its own run id, a code change letting `validate_spec` accept it (a T1_NODES_LATER-only spec and a third env), and its freeze committed under `sweep2/g1b/env/`. |
| **Host layout** | The U2 run used `/home/dowling/r1_trackp/venvs/ar-cond7a` and data root `/home/dowling/r1_trackp/data` (manifest `ab7186d2…`). The G.1b layout requires `<base>/data` under `/home/dowling/r1_tracks/t1_tasl`, and `harness_checkout` requires HEAD at the spec's pin in the shared `harness_dir`, which holds `c025f89a` for the four TASL-2 nodes. | The cluster agent builds the env and data under the T1 TASL base and checks the freeze and manifest. TASL-2 needs a second harness checkout at the new pin, with its own `harness_dir` in the autoresearch spec. |
| **Assembly** | `L.summarise` requires every node of the spec. An autoresearch-only spec is its own run. | A separate `assemble`/`summarise` for the autoresearch run. Its noise floor joins the seven nodes' table by node, as an eighth run record, not inside the seven-node assembly. |
| **Note binding** | The second note binds `10fd3343` and `060aac91…`. Autoresearch would run from newer code (the spec support) and another spec. | The second note carries autoresearch's own binding (for example `ar_paper_commit`, `ar_spec_sha256`, `ar_run_id`, `ar_harness_commit`), read by the new launch code. Alternatively, a third note. |

Values already on record (from `ops-tasl-20261116` `TASL2_AR_COND7A_RESULT_20261121_captures`, accepted with C1–C5):

| Item | Value |
|---|---|
| Census times on TASL-2 (R1-G1B-TIMEOUT: "the node's own census host where that is a TASL host") | B1 218.951 s, B2 218.443 s, E1 219.565 s, E2 255.916 s, E3 217.516 s, E4 222.584 s |
| Slowest census record | 255.916 s (E2), so the timeout is 767.748 s |
| Node spec at `eb14ed61` | sha256 `5bdce00a…` |
| Edit manifest | sha256 `55f2666a…`, four edits |
| Committed pin | `147f0d35…` (R1-TRACKG-AR-U2-TASL2) |
| Data manifest | `ab7186d2…` |
| Projection | 460 × 218.951 s + setup ≈ **28.2 GPU-h** (sensitivity 1.5: ≈ 42.2). With the seven nodes, 56.49 ≈ 56.5 GPU-h (sensitivity 83.9), under the 100 GPU-h cap. About 28 wall-hours on TASL-2 after its four nodes. |

**U2 conditions C1–C5.** `U2_ISO_AUTORESEARCH_RESULT_REVIEW_20261121.md` accepted the result conditional on C1–C5,
which are text and record changes with no re-run.

The result `U2_ISO_AUTORESEARCH_RESULT_20261121.md`, sha256 `8f872f2d…`, is on `ops-tasl-20261116`, not on `main`.
Its sha256 is bound on `main` by the U4 census, its acceptance sidecar and the delta spot check.

Applied:
- the 20,000 MiB floor;
- the parent peak 6,560.3 MB;
- the cross-host label;
- the no-evidence statement;
- the s001 and bundle byte counts;
- the C5 sha pair unchanged;
- no CUDA-IPC claim;
- the one-smoke rule.

**Not applied (review M5).**
- **C1:** the preserved "executed unit" `b83d9159…` is the Ada-targeted unit. The TASL-2 adaptations exist only in
  the result's prose.
- **C4:** the B1/B2 median is written as 218.7935 s; it is 218.697 s. The wall time "1,791.0 s (29:49)" is wrong:
  1,791.0 s is 29 min 51 s.
- **Stale text:** "reaches main after the sweep-2 launch" (the row is on `main`), and "T1 labels run on H200" (twice).
- **The cited smoke report `8814eecc…`:** it still carries the m6–m9 errors.

The bound result cannot be edited without breaking those three bindings. The agent therefore wrote an errata file
beside it: `U2_ISO_AUTORESEARCH_RESULT_20261121_ERRATA.md`, on `mac-ar-u2-text-20261121` @ `0e5972b6` over
`ops-tasl-20261116`. It binds `8f872f2d…` and corrects each item.

Still open:
- the errata need a short independent re-review (bundled for review with this unit);
- C3/C4: the executed and reviewed unit bytes were not preserved.

**Decision NOTE2-AR (for the author).** R1-G1B-TASL-DECISIONS puts autoresearch under the second note.
- **A (recommended): sign the second note for the three TASL-7 nodes once the cross-check passes, and authorize
  autoresearch under a third note.** The third note is signed once a follow-up unit has landed the harness pin, the
  host check at that pin, the spec support and its spec. This changes the author's wording ("that second note"),
  hence an author decision. Its benefit: the TASL-7 nodes, about 14 GPU-h, do not wait on autoresearch's cluster and
  code steps. Under either option, autoresearch's run has its own spec, so its own assembly and summary, and a second
  harness checkout on TASL-2.
- **B: as decided.** The second note waits until autoresearch's binding exists and carries both sets of fields. The
  TASL-7 nodes wait for it too.

## Limits

- The cross-check's derived spec carries every G.1b node (`validate_spec` requires all seven). Only the named node runs.
- On TASL-2, Breakout runs with `jax312` and without TASL-7's `extra_env` `XLA_FLAGS`. The cross-check note discloses
  this. The pre-launch report found TASL-2's `jax312` CUDA working, and a refusal there is an infrastructure STOP.
- The derived specs' own projection and `deadline_s`, as recorded in each job record, still count all 460 runs per
  node. That overstates them; it does not bind anything.
- The three TASL-7 nodes' assembly must go through `g1b_crosscheck.py assemble`. `g1b_tasl.py assemble` at
  `10fd3343` remains callable by hand, and the operator steps name the gated command.
