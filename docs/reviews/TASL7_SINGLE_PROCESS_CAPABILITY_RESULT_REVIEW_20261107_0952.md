# Independent review: TASL-7 single-process capability result, 7 November 2026

**Verdict: ACCEPTED for the bounded engineering result report only.** This is not acceptance of a host lease, B1 readiness, launch authority, or scientific results. Independent reviewer: Codex, AI-assisted.

## Material reviewed

- Result report `docs/r1/reports/TASL7_SINGLE_PROCESS_CAPABILITY_RESULT_20261107_0952.md`, SHA-256 `a584126655e83cefd1835339e2613e75de4612c964a645f5a8665a686a0358aa`, in the coordinator's checkout. This review binds those exact bytes.
- Retained raw capture `/private/tmp/tasl7-capability-20261107-0953.txt`, SHA-256 `c539d7cde1f6b38554e75de4711e72fe1bc41546d8fd5a4bdc95d2b2f894acb9`.
- Probe `docs/r1/proposals/tasl7_capability_probe_20261107/probe.sh`, SHA-256 `f8d90cd6c39729e69ef663207c2f609f4404bdb4bd1c4bbf0eecc3608281c266`, checked against the blob at commit `2ec1693220e2d48bb6a75bb9eeff2587937b431e` and the accepted R2 probe review.
- The coordinator's retained tool result for the invocation and SSH exit; PLAN §10's recorded author decisions and the accepted R2 probe review.

## Findings

The raw timestamp `2026-11-07T08:52:55Z` corresponds to 09:52:55 CET. The report's SSH invocation matches the coordinator's tool record, including its noclobber local capture, stdin script, and SSH options. Exit zero is coordinator-reported and tool-visible; it is not part of the raw capture and I did not independently repeat the SSH operation.

I extracted the complete three STATUS payloads from the capture in memory and independently hashed their bytes. Their hashes equal both the reported values and each captured before/after hash: exam `65661d28abfc301ac155d9ae7a87f570f196753e1a8b98a1622129915307b1b6`; Track P `dd1c19142ee869568b4a4ba4360ceb878a1d6253bb7ee139da15cac232189317`; Track S `97b7217a49d47d857083ee695d96eeb5fd5a9cf1a275b4f4de0d2dc9a7922faf`. Matching snapshots are not an atomicity or continuous-inactivity proof.

The capture supports the report's host and UID, Python version, directory and lock identities, GPU utilization and empty compute-app listing, transient flock acquisition and explicit unlock, self-kcmp result, self-pidfd observation, and descriptor-close completion. The script and report properly limit these to point-in-time, single-process observations: self-kcmp does not demonstrate inherited open-file-description identity; self-pidfd does not qualify a worker or server; neither demonstrates cgroup delegation or an ongoing lease. The GPU query is not evidence of memory availability or absence of all host activity.

The report accurately records that coordination with other operators beyond observed snapshots was not independently established. The accepted proposal identifies coordination and no preemption as conditions; this review makes no finding that a snapshot alone fulfills them. The script intentionally performs the bounded read and transient advisory lock operations described. I did not trace SSH, utilities, Python internals, logging, or concurrent host behavior, and make no claim that incidental effects were impossible.

The report preserves the distinction between the author's permission to continue and the separate no-deletion, non-preemption, checkout, independent review, gate, and launch requirements. Its remaining B1 items are not discharged by this result.

## Review method and limits

This review compared the retained local evidence with the committed script and prior review. It did not access TASL-7, rerun the probe or tests, execute a model or GPU workload, send a signal, or delete anything. The raw capture is local and may contain historical status text; its hash and the source report identify the reviewed evidence, but this review does not publish its contents. This acceptance applies solely to the exact report SHA above.
