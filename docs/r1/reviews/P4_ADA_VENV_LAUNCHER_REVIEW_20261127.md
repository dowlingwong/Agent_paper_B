# Independent review of the Ada P.4 venv launcher

AI-assisted (Codex, independent tier-E reviewer, 27 Nov 2026). Task `local/20261127-11`.
Base `98c571d22251a9d57a6d157950bd5ac8c340e17b`. Candidate
`8f6c9ec25883df45a1014c1e48e8cfff26648553`.

## Review and re-checks

- The Ada host fill selects the named venv and retains the reviewed interpreter path. The config discloses
  Python 3.12.10 on Ada and 3.12.15 in image v2.2. The probe and job wrappers invoke their existing entry points
  with the staged interpreter and unchanged arguments. The container routes retain their default interpreter.
- The job checks the pinned Ada config and the active interpreter, then runs live `uv pip freeze --python`
  before data or training steps. The package lines must match the published lock exactly, including
  `causal-conv1d==1.7.0`. The raw stdout hash is recorded. I recomputed the canonical normalized lock SHA-256
  `e607c1d87221999015c1cd988c38dbc2e8deb51938403e2ca2c0c2832755419b` from the published lock.
- The launcher holds the existing per-card flock. Native CUDA visibility is set to that card's UUID. The
  in-job driver and GPU identity query is scoped by UUID. A separate check requires that the pinned
  interpreter's CUDA runtime sees exactly that device before staging the job's inputs. Host, GPU model,
  driver, Python path and version, and the live freeze are captured in the runtime records.
- On the initial candidate, killing the Bash wrapper could leave the native training child alive. I reproduced
  that behavior with Bash, Python and a synthetic child. In the reviewed revision the launcher signals the
  native process group, and `p4_lib._sh` passes the GPU lease descriptor on to the training process.
  I verified with real subprocesses that a regular child stops and that a TERM-resistant child retains the
  flock until its exit. The final re-check confirmed that an unfinished launcher yields an infrastructure
  receipt and conservative incomplete-attempt charge, including when a late job record has a null STOP field.
- The initial first-arm switch required a container image in the record. The reviewed switch accepts a
  native record through its matching, hashed launcher receipt and verified venv freeze. The sealed launcher
  record gives `image_executed: false`. The probe receives the runner and its table inputs and generates
  synthetic labels in the job. The phase-1 switch still requires its signed note and launch checks.

## Checks and handoff

The exact candidate passed `git diff --check`, Bash syntax checks, and
`r1/tests/test_trackp_p4_direct.py` with **45 passed** using Python from the local torch environment.
I also passed both actual shell wrappers a fixture library and verified that the selected interpreter,
probe/job arguments and visible-device setting reached it. The full-suite base/tip comparison is a separate
delivery gate.

After publication, Compute fills and independently reviews the Ada host config for the authorized account,
then completes the environment, lease and synthetic probe checks in `compute/20261127-13`. The future
phase-1 note should name the runtime actually used and carry the applicable Ada smoke and E0 records.
This review exercised only local synthetic fixtures. It made no live host call, submitted no job and read no
credentials or sealed partitions.

Verdict: ACCEPTED
