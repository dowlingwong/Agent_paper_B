# Independent review of Paper C measurement (b)

Code-Commit: d6ac990dc449dad9262a27260a760b5a30a0b4cf
Verdict: ACCEPTED

Acceptance covers pre-signature handoff for local/20261127-19(b). Base
`840ad01df1c517f023c3dc14c32ec7ae2429a109`. I reviewed the signed
R1-PAPERC-MEASURE-FIRST, R1-PAPERC-ROWS-CONFIRMED and R1-PAPERC-HARNESS-PIN-SET
rows, along with the actual pinned harness source at
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`.

I exercised the exact reviewed entry helper, verifier and accounting with
the exact pinned `run_real_campaign`, using in-memory stub workers and a
stub proposer in a temporary directory. The proposer saw the measured
start of 0.8 before its first proposal. The campaign discarded a worse
candidate, rejected a no-op precheck, and kept a strict improvement.
The real ledger and events counted two candidate worker runs and three
proposer calls. The start counts as one additional CPU run. Separate
synthetic checks exercised tie refusal, mixed spec/seed receipt refusal,
and both alternatives of the stakes floor. `git diff --check` passed.

The first review refused `77c05e12` because the exam observer crashed and
would have charged an extra call per observation even with a valid implementation.
The revision removed the observer and reads proposal telemetry and terminal
record counts. It also attests the campaign worker runtime before proposing,
refuses file changes in start and audit runs, rejects missing kept edits, and
binds the receipt roster, code, spec and exact audit seeds.

The proposed worker block 62,000–62,011 and audit block
10,901,000–10,901,119 checked against the committed registry, D.3
reservations and the separate measurement (a) audit block. The worker
extension is still unpublished. The runner requires the published
registry and its exact digest before any evidence run.

The author still needs to decide the proposer, cap and registry extension.
The coordinator and operator must bind the actual proposer digest and
thinking-off server configuration, audited runtime and resource pins, and
the exact authorized roots. The final one-line correction to the caller's
manager mode was verified with the injected backend. The ledger, campaign
start and proposal events all report `langgraph_manager`, and the
synthetic decisions and accounting are unchanged. The review does not
authorize execution. No live model
or worker job ran, and I did not open a protected label or evaluation file.
