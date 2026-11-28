# local/20261128-13 — Ada P.4 phase-1 note STOP at the spec signature and timing disposition

for: coordinator

- Task base `d6696f295b205bb8bdd1a14208dbe0bde430fd88`, advanced from `d5d83198` to include the accepted smoke review. Unsigned draft branch `local-20261128-13-p4-phase1-note` @ `be602ef3b8d2661406da5b8e17fb76929da2acf5`.
- The draft binds the published Ada staged and per-card smoke, the accepted four-run E0 result under R1-P4-E0-CRITERION, and the signed P4 single-suite disposition. E0 passed by a narrow RPS margin (2.9494e-5 vs 3.04e-5), with 21.8% and 39.9% within-host RPS spreads on Ada and TASL-7. Both slope checks pass for all four cross-host pairs.
- **P3 STOP:** The existing reviewed one-file candidate `befb58c8b3f5b222a2cf8973e513b252235453fc` is unsigned. It has the exact published code parent `0b46595418bb21dc0e8e5b234b30f2a84ac5082c`. The desk has no configured project signing identity. An authorized signer must reproduce those spec bytes in a signed one-file commit on that parent.
- **P5 STOP:** The published reviewers accepted the smoke and E0, with timing left open. All four successful timing-job receipts match the admitted Ada host config, venv interpreter and package freeze. The smoke establishes fast kernel binding in its own process. The timing receipts do not capture actual kernel binding, and the E0 leases (0.9211 and 0.9142 GPU-h) and the per-card smoke (26 s, 3,345 MiB) are different jobs. Carry the per-arm times as planning estimates until independent review verifies the timing-job runtime and kernels. If the needed capture is unavailable, route the timing probes after parity and review the resulting charges and estimates.
- Launch-strength spec validation, note-to-spec checks, published input paths, exact probe hours and charge-file bindings, all four timing receipt checks and `git diff --check` passed. The official note parser refused at P3 as expected. The task branch changes only the draft document. The previously accepted runner and spec implementation suite is in the [P3 handoff](20261127-25b-p4-p3-runner-and-launch-stop.md). Final independent tier-E review is pending P3 and P5.

| Object | Value |
|---|---|
| Draft SHA-256 | `f56f1bc720e2bb1ed3ba8baec7be11eeebdcd844646530d65246c6016b49d3b6` |
| Exact Ada-only spec SHA-256 | `d9ab62698828adc459c8084c17e2ffd4ae000df71957a155d9e0cb83bf6d5ca6` |
| Prompt replay harness | `897d83c8efa364ec2fdd37288241cc42e01d7274` |
| Published per-card smoke review SHA-256 | `2f69564fbec7178526a1dbc5543cedd661b8d2a629f83af117d4056c9ab5fefe` |
| Published E0 review SHA-256 | `bde5600b51ac94505498345ece00f27104790610f89a402378550fa400163936` |
| Verified timing-run freeze SHA-256 | `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08` |

Next: route the spec signature and the timing disposition in parallel. Local fills P3 and P5 with the published records and obtains tier-E acceptance. The coordinator publishes under R1-P4-PHASE1-SIGNATURE (4). Compute checks the non-preview stage and attempt ledger for `trackp-p4-p1-20261122-a`, then starts Kev 0.8B first under the published note.

Decided alone to retain the reviewed spec bytes, pull the published smoke review into the draft base, and leave the four-arm timing estimate provisional. No host job was submitted.
