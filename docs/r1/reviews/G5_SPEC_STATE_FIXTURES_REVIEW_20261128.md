# Independent tier-E review of the G.5 spec-state test fixtures

Task `local/20261128-11`. Independent reviewer `Codex /root/g5_fixture_review`. Reviewed code
`7939e98a44a65bb8b56f280af930000788f270ae` on accepted render
`6466e0440e7ee8ff292e148c1212b5742685629d`. Publication comparison base
`a70c8872ead621696b8f8f14134319009f0fa3e6`.

Verdict: ACCEPTED

This verdict covers the test-fixture change. The focused three-way comparison and full base-to-tip
comparison are separate publication checks recorded in the worker handoff on `coord/local`.

## Fixture coverage

- The draft builder restores the unsigned run, decision and copy placeholders, freeze date, IPC mode and per-node tails. I independently compared its complete output to the `a70c8872` JSON while sourcing it from both the draft and filled blobs. Mutating one restored dict did not change the next call or the source bytes.
- The original option, refusal, signature, copy, tails and CPU-set assertions remain in their respective paths. CLI checks that rely on draft state now use a separate spec file per test. Synthetic signed-spec fixtures fill fresh copies of the restored state. The added positive CLI assertion exercises a filled spec with Gaussian nodes and both Student-t declarations at five degrees of freedom.
- I independently ran `validate --launch` through the CLI handler on the restored draft, a synthetic filled spec and the rendered filled spec. The draft refused. Both filled specs passed with empty unsigned and blocker lists.

## Binding preservation

`git diff --check` passed. The fixture commit changes only three test files. The rendered spec still hashes to
`7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e` and its unsigned note to
`1a2ecfc2a05136edea226ea5aacc136419f5b8e02abe8e4c8d7943f63834079c`, matching the accepted render.
The review used published metadata and synthetic inputs without opening a sealed partition or submitting any job.
