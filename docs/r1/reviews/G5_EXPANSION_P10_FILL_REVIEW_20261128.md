# Independent tier-E review of the four G.5 expansion P10 fills

Task `local/20261128-05`. Base `914e1cf90fcc1a87dd2a59cc4984842281438eeb`.
Independent Codex reviewer `review_addenda` reviewed the branch without writing the implementation.

**Initial verdict: NOT ACCEPTED** at `02f4d364c6bb962a375840aa9b4f8f0d713d8e53`.
A contradictory clause inside an HTML comment could override the visible author decision.
The reviewer reproduced acceptance of an incorrect ETTh1 Student-t declaration with four degrees of freedom.

**Re-check verdict: ACCEPTED** at `8087c4c929b57664f0166a6a3cd73562d74f385e` for the P10
fills and their checker. There are no open review findings. The corrected checker reads one published PLAN
snapshot, uses the visible author decision, and refuses multiple visible declarations. The original hidden
clause now leaves the signed MetaMaze declaration in force and the incorrect ETTh1 declaration is refused.

- Independently verified R1-G5-TAILS-EXPANSION at `3013ddf0`, the reviewed paired-kurtosis basis
  at `9e3426ef` (report SHA-256 `b89b452e59caa88f1dcf2105fcf20c672f4a83f2c698e43dc6db2615c36a4533`),
  all four Markdown fills and their corresponding spec fragments against published `origin/main`.
  MetaMaze is `student_t` with `tails_nu: 5` and the signed scale adjustment. ETTh1, Forest Cover and
  Titanic are `gaussian`. The four drafts retain `approved: false`, the existing routes and the pending launch fields.
- Exercised the published authority gate with incorrect laws and degrees of freedom, missing authority,
  a missing row, a row outside an author section, and an invalid Gaussian degree-of-freedom field.
  The checker rejects each case. Git ancestry, scope and `git diff --check` passed.
- Re-check focused suite: 36 passed with Python 3.11.5, pinned clean harness `9bb41680`, fresh
  `TMPDIR`, `COPYFILE_DISABLE=1`, and `python -B -m pytest -q -p no:cacheprovider -rfE r1/tests/test_t1_g5_addendum.py`.
  The initial expanded six-file suite had 369 passes versus 358 on base. Both runs had the same two
  pre-existing failures in `test_t1_g5_tasl.py`: `test_g5_tasl_gpuh_b_needs_the_server_stopped_during_audits`
  (rounding) and `test_two_cards_xc3_fail_b_removes_a_failed_node_from_g5` (Linux path under `/home/dowling`).
  The required full-suite comparison is recorded separately in the task handoff.
- The actual launch-facing `check-note --draft` needs the published main G.5 note and full per-node spec,
  host and review bindings. Each node's actual P10 fragment passed its authority check. The full draft
  binding path was exercised with synthetic launch prerequisites. The review opened no sealed partition.
