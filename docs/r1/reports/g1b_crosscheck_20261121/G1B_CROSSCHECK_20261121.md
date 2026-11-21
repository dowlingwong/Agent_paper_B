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
    delegated scope and row gate. The attempt is sealed with `g1b_tasl.py seal`.
  - `compare` reads two sealed attempts and writes a PASS/STOP verdict. PASS needs every default and
    default_repeat outcome identical (metric bit-identical, or the same failure) and both sides deterministic.
  - Launch needs the signed cross-check note `g1b_xc_t1_tasl_<date>.md` on `main`, both keys, both host-check
    records on `main`, and `verify_launch_tasl` with the cross-check spec.
- **`sweep2/t1_tasl/g1b_crosscheck_spec.json`**: run id `g1b-tasl-20261121-b-xc`, binding the signed G.1b spec.
  `paper.commit` names `10fd3343` until the launch commit sets it to the main commit carrying the code, so a launch
  before that refuses.
- **`docs/r1/proposals/G1B_XC_NOTE_DRAFT_20261121.md`**: the cross-check note (approved: false), parsed by
  `check_xc_note`.
- **`docs/r1/proposals/G1B_T1_TASL_NOTE2_DRAFT_20261121.md`**: the second G.1b note (approved: false).
  - It carries the first note's `run_id`, `paper_commit` `10fd3343`, `spec_sha256` `060aac91…` and `harness_commit`
    `c025f89a`, so the TASL-7 nodes' job records carry the same spec sha256 as the TASL-2 nodes'.
  - P7 is PASS, citing the cross-check review and the three verdicts (to fill).
  - P12 holds autoresearch_fixedtokens as PENDING (below).
  - Signed, it passes `check_note` against the signed spec, and its P7 opens the TASL-7 gate (tested).
- **Tests**: `r1/tests/test_t1_tasl_crosscheck.py` (22 tests).
  - The shipped spec and its derived specs (nothing but the node's host, the run id, the paper commit and the TASL-2
    env changes).
  - Nine spec refusals.
  - Breakout's env requirement on TASL-2.
  - The default-part job on both hosts with the fake host tools, followed by seal, compare and the CLI.
  - Six verdict cases: identical; a last-bit difference; the same failure on both hosts; a one-sided failure; a
    missing row; non-determinism.
  - Refusals of unsealed, tampered, infrastructure-stopped and ungated attempts.
  - The launch gate.
  - Both note drafts parsing.

  `test_t1_tasl_g1b` still passes (45).

## Order of operations (R1-G1B-TASL-DECISIONS XC A)

1. This unit is reviewed and reaches `main` (`M`).
2. The launch commit sets the cross-check spec's `paper.commit = M` and adds the signed cross-check note.
3. The six default-part jobs run: three nodes × two hosts, about 1 GPU-h in all. Each attempt is sealed.
4. `compare` runs per node on the two sealed attempts. The three verdicts are committed and reviewed.
5. The second G.1b note is signed with P7 citing the verdicts. The TASL-7 nodes launch from a published checkout whose
   code equals `10fd3343` (for example the first launch commit `985dd45d`), with the second note copied from
   `origin/main`.
6. **Before assembly**, each node's G.1b TASL-7 attempt is compared with its cross-check TASL-2 attempt (`compare`;
   the row's literal comparison).
   - A STOP re-measures that node on TASL-2 (R1-T1-TASL-ENV).
   - `assemble` at `10fd3343` does not run this comparison, so it is a recorded step before `assemble` and
     `summarise`, and its verdicts are committed with the assembly.

## autoresearch_fixedtokens: why it cannot join under the second note's binding, and what it needs

R1-G1B-TASL-DECISIONS: autoresearch "joins under that second note, together with the TASL-7 nodes, once its spec
entry and its U2 conditions C1–C5 are reviewed". The second note's binding is the signed spec (`060aac91…`) and the
code `10fd3343`. Autoresearch cannot run under either, for five reasons:

| Blocker | Fact | What resolves it |
|---|---|---|
| **Harness pin** | Its option-A kit (R1-TRACKG-AR-COND7; `mac-trackg-iso-ar-cond7a-20261120` @ `7330338`, code commit `0e0b820`) is **not** in `c025f89a`. | A harness commit `c025f89a` + `0e0b820`. The agent prepared it as `mac-trackg-t1-ar-20261121` @ `eb14ed61` (cherry-pick, clean). It differs from `c025f89a` only in the autoresearch node files, `src/autoresearch/trackg/node_lib/ar_isolated.py`, the port test and a report. Its autoresearch code equals `7330338`'s (`git diff` empty). The other seven nodes' files are unchanged. To check in its review: whether the harness tests that compare each node's `ar_isolated.py` copy with `node_lib` still pass. |
| **Host check at that pin** | `check_host_record` requires each host's record to name the spec's harness commit, and the TASL-2 record names `c025f89a`. | A TASL-2 host check (items 1–7) at the new pin, reviewed and on `main` (a cluster step); or an author ruling that the record carries over, given that the isolation code is unchanged. |
| **Spec** | An autoresearch entry cannot go into the signed spec without changing its sha256, which would break assembly of the seven nodes. An autoresearch-only spec fails `validate_spec`: it requires all seven census nodes and envs `torch312`/`jax312` at Python 3.12.16, while autoresearch's env is `ar-cond7a`, Python 3.12.15, freeze `11def6ad…` (122 lines). | A separate autoresearch G.1b spec with its own run id, a code change letting `validate_spec` accept it (a T1_NODES_LATER-only spec and a third env), and its freeze committed under `sweep2/g1b/env/`. |
| **Host layout** | The U2 run used `/home/dowling/r1_trackp/venvs/ar-cond7a` and data root `/home/dowling/r1_trackp/data` (manifest `ab7186d2…`). The G.1b layout requires `<base>/data` under `/home/dowling/r1_tracks/t1_tasl`. | The cluster agent builds the env and data under the T1 TASL base and checks the freeze and manifest. |
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
| Projection | 460 × 218.951 s + setup ≈ **28.2 GPU-h** (sensitivity 1.5: ≈ 42.2). With the seven nodes, 56.4 GPU-h (sensitivity 83.9), under the 100 GPU-h cap. About 28 wall-hours on TASL-2 after its four nodes. |

**U2 conditions C1–C5.** `U2_ISO_AUTORESEARCH_RESULT_REVIEW_20261121.md` accepted the result conditional on C1–C5,
which are text and record changes with no re-run.
- `U2_ISO_AUTORESEARCH_RESULT_20261121.md` on `ops-tasl-20261116` (sha256 `8f872f2d…`, changed from the reviewed
  `ca3bcadd…`) now carries:
  - the executed-unit record (`3bb015a1…` / `b83d9159…`);
  - R1-TRACKG-AR-U2-TASL2;
  - the 20,000 MiB floor;
  - the parent peak 6,560.3 MB;
  - the cross-host label;
  - the no-evidence statement.
- That branch is not merged into `main`.
- This unit's review checks the applied text against C1–C5, read-only. The U2 records reach `main` with the
  autoresearch unit.

**Decision NOTE2-AR (for the author).** R1-G1B-TASL-DECISIONS puts autoresearch under the second note.
- **A (recommended): sign the second note for the three TASL-7 nodes once the cross-check passes, and authorize
  autoresearch under a third note.** The third note is signed once a follow-up unit has landed the harness pin, the
  host check at that pin, the spec support and its spec. This changes the author's wording ("that second note"),
  hence an author decision. Its benefit: the TASL-7 nodes, about 14 GPU-h, do not wait on autoresearch's cluster and
  code steps.
- **B: as decided.** The second note waits until autoresearch's binding exists and carries both sets of fields. The
  TASL-7 nodes wait for it too.

## Limits

- The cross-check's derived spec carries every G.1b node (`validate_spec` requires all seven). Only the named node runs.
- On TASL-2, Breakout runs with `jax312` and without TASL-7's `XLA_FLAGS`. The pre-launch report found TASL-2's `jax312`
  CUDA working, and a refusal there is an infrastructure STOP.
- The before-assembly comparison is a recorded step, not a check inside `assemble` at `10fd3343`.
