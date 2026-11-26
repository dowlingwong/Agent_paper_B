# Independent review: sweep-1 classification prerequisites (28 October 2026)

AI-assisted independent review (OpenAI Codex). The reviewer inspected preserved batch state, native manifests and collection records, launch/preparation records, logs, Git history and local remote-tracking reflog. No stopped batch was resumed or modified by this review.

| Check | Result and evidence |
|---|---|
| Authorization and pins | PASS for the recorded launch: liveness and both sweep manifests record paper `ccb47128aad82e331f79df4a893dbc1ee7e42f51`, harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, config SHA256 `2fa891f43bf26e6ed2ac6c794696428a43568a69a850d6029e3bc8233616974b`, GGUF SHA256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c`, and build `version: 0.7.0-dev (build 1, commit 620d222)`; these match `docs/r1/authorizations/c3_sweep1_20261027.md`. |
| Harness cleanliness | PASS for recorded launch-time state: all three native manifests report `harness.dirty=false`. The later working tree has four untracked data caches; its current status is not substituted for the recorded launch status. |
| Completeness | PASS: 144 root files per mode, 18 per authorized node; each `collection_checks.json` records 144/144 roots, no root failure, no failed LLM call and no parse failure. |
| Restarts and watchdog | PASS on retained records: one runner, no interruption or watchdog events; the two collector `--resume` sessions with zero remaining jobs are completion checks, not failure restarts. |
| Gates and execution | PASS for recorded gates: `prepare.json` is clean (paper 579 passed, 38 skipped; harness unexpected failures empty), all eight D28 node verdicts passed, pin checks recorded pinned, GPU offload observations were 5253 MiB, and runner `stop_reason` is null. |
| Frozen protocol/config | PASS for preserved Git/config evidence: `git diff ccb4712..22cc893` excluding `results/` is empty; the two actual configuration hashes match the authorized hash. This does not prove the absence of an unrecorded temporary edit subsequently restored. |
| `d51b0a8` push | PASS for ordering: `d51b0a8` is not an ancestor of `22cc893`; it entered main through `30303d8`. The local `origin/main` reflog records successful push confirmation at 28 October 03:38:47 UTC, after B.1 started on 27 October 15:48 UTC. This is a local push-confirmation timestamp, not an independently obtained GitHub server event timestamp; `d51b0a8`'s earlier commit creation time is not its push time. |

The offload/census evidence is sampled, not continuous: six GPU census observations cannot prove every moment between samples remained fully offloaded or rule out unrecorded transient changes. No retained log reports OOM, CPU fallback or a STOP. This review accepts the recorded checks within these limits and does not assert continuous monitoring. It does not claim B.2 was run.

The original index SHA256 is `812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab`; original append-only manifest SHA256 is `f18f8a8b47ba17dc1da9e875d500831d6d0d03c69aa7d12b216444aeff1af98f`; original none manifest SHA256 is `5053067331676e1aaefb0c757cac47ec82200ad124ff81f3d2ae074cf197d440`. The classification sidecar records the original and relocated paths without editing these records.
