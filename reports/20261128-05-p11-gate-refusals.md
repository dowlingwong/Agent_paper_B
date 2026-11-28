# compute/20261127-32 — G.5 P11 host tests: gate-blocked remainder recorded, fresh review ACCEPTED

**Result: the note-gated remainder cannot be run before the signed G.5 note; each command was invoked by its own
host-test path and refused at the launch gate with the exact message `STOP: run_id must be c3_t1_labels_<YYYYMMDD>`
(rc 2). Recorded as "checked at publication" per disposition `compute/20261128-05` item 1. Review ACCEPTED (two
MINOR observations; MINOR-1 wording applied).**

- Task: `compute/20261127-32` with `compute/20261127-05`, `compute/20261128-05` item 1; R1-G5-P11.
- Deliverable branch: `compute-g5-p11-refusals-20261128` @ `dec84350a5f93957287f5a9f6fb9cc1f5066b3d0`
  (base `a98d2eff`; append-only section + seven captures; MINOR-1 wording commit on top).
- Review branch: `compute-g5-p11-refusals-20261128-review` @ `be56676c6a4803c9a70d3960132d09bae7d795b1`;
  `Verdict: ACCEPTED`, review file `docs/r1/reviews/G5_P11_REFUSALS_REVIEW_20261128.md`, sha256
  `d8e4e559cdde4bbc858196880759d151379b3b02245214692b65361490136d5f`.
- Checkout: TASL-2 `paperB_cpuset_20261128T001400Z` (detached at `a98d2eff`, clean).
- Captures: `docs/r1/reports/g5_code_20261123/P11_REFUSALS_20261128/`, seven files plus `SHA256SUMS` (all verify).

| Command | Refusal | rc |
|---|---|---:|
| `seal-attempt` | `STOP: run_id must be c3_t1_labels_<YYYYMMDD>` | 2 |
| `seal-node` | same | 2 |
| `seal-run` | same | 2 |
| `seal-server` | same | 2 |
| `close-server` | same | 2 |
| `server-span` | same | 2 |
| `validate --launch` (control only) | same | 2 |

The refusal happens before any item path is read or written (the committed spec is read first); no smoke attempt,
sealed file, label or evaluation value was created or read. C2, C4, C5, C9, C14, C16, the hours-long C10 span and
the audit-chunk side of C11 remain gate-blocked and are **not** reported as PASS; they need the signed note and
filled spec, or an authorized synthetic smoke spec, and are checked at publication/first real use.

The earlier TASL-7 server/restart/identity/lease evidence (`P11_HOST_TEST_RUN_20261127/`) is unchanged and still
stands for C7 and the server side of C11.

Decided alone: did not call `validate --launch` as an item test (per the disposition), did not fabricate a note or
a smoke spec, and applied only the review's MINOR-1 wording fix.

**Update 28 Nov 02:00 CET:** the coordinator has withdrawn the "checked at publication" disposition for the
P11 host tests (STATE `a06dfc3f`: `local/20261128-02` must supply a G.5 P11 engineering smoke path, because
R1-G5-P11 needs pre-publication coverage). The refusal captures above remain valid evidence, but the task is
**not complete**: compute runs the engineering smoke items when local publishes that path, then gets a fresh review.
