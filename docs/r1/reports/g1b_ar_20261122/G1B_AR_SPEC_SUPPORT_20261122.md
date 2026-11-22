# autoresearch_fixedtokens joins G.1b under its own spec: spec support, spec, third-note draft, host-check procedure

Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026, on `mac-g1b-ar-20261122` over published `main`
`9c2979a2`, for item 2 of the queue of 22 Nov 2026 (01:22). This is desk work: no host, no run, no label.

## Authority

R1-G1B-NOTE2-DECISIONS, NOTE2-AR A:

> "`autoresearch_fixedtokens` joins G.1b under a third note with its own spec, signed once its harness pin (harness
> `2d09f9a9`, `mac-trackg-t1-ar-20261121`) is independently reviewed, a TASL-2 host check at that pin passes, and its
> spec support and spec exist."

The readiness list is in `docs/r1/reports/g1b_crosscheck_20261121/G1B_CROSSCHECK_20261121.md` ("why it cannot join
under the second note's binding"). This unit covers its *Spec*, *Assembly* and *Note binding* rows, and prepares the
*Host layout* row for the experiment agent. The *Harness pin* row is reviewed separately.

## What changed

**`sweep2/t1_tasl/g1b_tasl.py`.** A second spec kind is selected by its schema, `g1b_tasl_ar_job/v1`. The seven-node
spec (schema `g1b_tasl_job/v1`) is validated and run exactly as before. There is one deliberate exception: it now
refuses `autoresearch_fixedtokens`, which may join G.1b only under its own spec, by the decision. The signed spec does
not contain that node, so its validation is unchanged; `test_seven_node_spec_is_the_signed_one_and_still_validates`
checks it at sha256 `060aac91…`.

For the AR kind, `validate_spec` checks the following.
- **Environment:** exactly `ar-cond7a`, at Python 3.12.15, with its freeze committed under `sweep2/g1b/env/`.
- **Host:** exactly TASL-2, with the node on TASL-2.
- **Node:** exactly `T1_NODES_LATER` (`autoresearch_fixedtokens`), with the shared rules: the uniform `n_edits`, the
  census times and pins, the GPU device, `<base>/data`, the lease, the GPU UUID format, and R1-G1B-CAP for this
  spec alone.
- `validate_ar` adds:
  - **Its own run:** the run_id is neither the signed seven-node spec's (bound by path and sha256) nor
    `<that run_id>-…` (the cross-check's form). The paper and harness repositories are the same.
  - **A second checkout:** `hosts.TASL-2.harness_dir` is neither equal to, nor inside, nor above the seven-node
    checkout. The hostname and GPU UUID equal the seven-node spec's (one card, one lease).
  - **The census host:** `estimate.census_gpu_model` is the RTX 4090 with ratio 1.0, because the AR census ran on
    TASL-2.
  - **The decisions:** `note_rule` cites R1-G1B-NOTE2-DECISIONS. At launch, `env_decision.authority` names a PLAN
    row, because R1-T1-TASL-ENV names only torch312/jax312 (decision AR-ENV in the note draft).
  - **One cap for G.1b:** this projection, plus the seven-node spec's (recomputed from the bound file), plus the
    cross-check's declared hours (`caps.crosscheck_gpu_hours`, about 2.1), must stay within R1-G1B-CAP. The result is
    reported in `projection.g1b_shared_cap`.
- **Node job:** the job is unchanged. For the AR kind its record adds `spec_schema`, `note_rule`, `env_decision` and
  its own `output_use`.
- **Assembly and summary:** `assemble` writes `g1b_tasl_ar_assembly/1` and `summarise` writes `g1b_tasl_ar_summary/1`.
  `summarise` refuses an assembly of the other kind. The AR noise floor joins the seven nodes' table by node, as its
  own run record.
- **`check_note_ar`, and the CLI `check-note-ar [--draft]`,** check the third note:
  - name: `docs/r1/authorizations/g1b_ar_t1_tasl_<date>.md`;
  - bindings: the paper commit, the spec sha256, the run_id, the full harness commit, `env_row` (the spec's
    `env_decision` row), `note_rule` and `host_row`;
  - P1–P8 PASS, each citing what it needs: P2 the TASL-2 host-check record and the pin; P3 a review and the pin;
    P4 a review; P7 the environment row;
  - no `<…>` and no PENDING anywhere;
  - draft mode as for the second note.
  - `check_note` refuses an AR spec, and `check_note_ar` refuses a seven-node spec.
- **`launch`:** for an AR spec it runs `check_note_ar`, checks the TASL-2 host record at the AR pin, and requires
  these PLAN rows: `PLAN_ROWS`, R1-T1-TASL-ENV, R1-TRACKG-AR-U2-TASL2, R1-G1B-NOTE2-DECISIONS and the environment row.
- **Wrapper:** `t1_tasl_node.sh g1b` needs no change; the script dispatches on the spec's schema.

**`sweep2/t1_tasl/g1b_tasl_ar_spec.json`** (new): run `g1b-ar-tasl-20261122-a` and harness
`2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe` in `/home/dowling/r1_tracks/t1_tasl/harness_ar`. Its values come from the
record (the census at `ops-tasl-20261116` `3c6ce37a`, the U2 result `8f872f2d…`, the smoke report `8814eecc…` and its
captures):

| Item | Value |
|---|---|
| Node spec raw sha256 / file | `5c1bdf3d…` / `5bdce00a…` |
| Committed pin | `147f0d35…` |
| Edit manifest | `55f2666a…` (four edits) |
| Data manifest | `ab7186d2…` |
| Census baseline (B1) | 218.951 s |
| Slowest census record (E2) | 255.916 s, so the timeout is 767.748 s |
| Environment | `ar-cond7a`, Python 3.12.15, freeze `11def6ad…`, at `/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python` (AR-ENV A) |
| Projection | 28.227 GPU-h (sensitivity 42.216); G.1b together 58.589 (85.96), under 100 |

The Mac desk recomputed the three node pins at `2d09f9a9` (`noise_floor.check_node_pins` construction) and they match.

Three fields stay TODO until signature, so launch validation refuses the spec until they are filled:
- `paper.commit`;
- the host-check record's sha256;
- `env_decision.authority`.

**`sweep2/g1b/env/ar-cond7a.freeze.txt`** (new): the U2 in-scope freeze (`env_freeze_live.txt`), 122 lines, sha256
`11def6ad…`, as on `ops-tasl-20261116`.

**`docs/r1/proposals/G1B_AR_T1_TASL_NOTE3_DRAFT_20261122.md`** (new): the third note, `approved: false`. It contains:
- the binding, host, node, census, environment, data, measurement and projection lines;
- P1, P5, P6 and P8 PASS;
- P2, P3, P4 and P7 PENDING (the host check, the harness review, this unit's review, and the environment row);
- the STOPs;
- the author decision **AR-ENV**, with options A (the AR census venv in place; recommended), B (a byte copy under
  the T1 layout) and C (a uv rebuild from the freeze; not recommended).

**`docs/r1/reports/g1b_ar_20261122/TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md`** (new): the experiment agent's
procedure on TASL-2. It covers:
- the second checkout at the pin;
- the node pins;
- the `ar-cond7a` freeze and Python;
- the data staged under the T1 layout;
- the seven §3 conditions at the pin, with the CUDA-IPC scan;
- the binding record with its four key lines;
- the STOPs.

## Tests

**`r1/tests/test_t1_tasl_g1b_ar.py`** (new), 52 tests:
- **Specs:**
  - the signed seven-node spec is unchanged and validates, and refuses autoresearch;
  - the shipped AR spec validates, its projection and shared cap are as above, and launch validation refuses each
    TODO;
  - the pins are the census values, and the committed freeze has the pinned sha256 and 122 lines;
  - 23 refusals: schema, envs, Python, freeze, a second host, extra nodes, the node's host, `n_edits`, the run_id
    (equal, derived), harness_dir (equal, inside, above), GPU UUID, hostname, the bound seven-node spec (sha, path),
    the census GPU, the ratio, `note_rule`, the cross-check hours (0, 11), the harness repo;
  - the shared cap exceeded.
- **The node job end to end:**
  - the record's AR fields;
  - the timeout basis of 255.916 s;
  - the engine runs from the AR checkout with the AR interpreter and the GPU UUID;
  - the chunk ids carry the AR run id.
- **Seal, assembly and summary:**
  - seal, `assemble` and `summarise` use the AR schemas;
  - an assembly of the other kind is refused;
  - the seven-node spec cannot assemble the AR attempt.
- **The third note:**
  - strict and draft modes;
  - 17 field refusals;
  - the name;
  - two `approved` lines.
- **Launch:**
  - the keys;
  - the PLAN rows, including the environment row;
  - a host record at the old pin is refused;
  - a node outside the spec is refused;
  - a seven-node note is refused.
- **CLI:** `check-note-ar`.
- **The shipped draft:** it binds the spec's run_id and pin, and its open fields are the four PENDING items.

Existing tests pass: `test_t1_tasl_g1b`, `test_t1_tasl_crosscheck`, `test_t1_tasl_g4`, `test_p3_split`,
`htcondor/test_g1b_h200` and `htcondor/test_g4_h200`. Together with the new file, `test_t1_tasl_*` gives 155
passed, and the other three files give 180 passed.

## Before the third note can be signed

1. The independent review of harness `2d09f9a9` gives P3.
2. The independent review of this unit gives P4.
3. The experiment agent runs the host-check procedure on TASL-2, and the lead commits the binding record. Its sha256
   goes into the spec and P2.
4. The author decides AR-ENV and writes the row. It goes into `env_decision.authority`, `env_row` and P7.
5. The merge carrying this unit becomes `paper.commit`. The spec's sha256 after these fills becomes the note's
   `spec_sha256`.
6. Run `check-note-ar --draft`, then sign, publish, and run `check-note-ar`.
