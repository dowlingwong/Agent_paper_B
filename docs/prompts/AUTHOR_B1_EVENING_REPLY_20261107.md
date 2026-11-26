# Author B1 reply — 7 November 2026

Recorded verbatim from the author's answer to the question about TASL-7 cgroup delegation; line breaks and spelling below preserve the reply. This file is the durable pointer for the dated PLAN §10 rows. The author described the message as “7 Nov evening”; no more precise time is asserted.

> Author answers (7 Nov evening). Record them in PLAN §10 as dated author rows, verbatim pointer to this message.
>
> To your question: I don't know of an existing delegated-cgroup launch method or an administrator for it, and none is needed. Decisions:
>
> 1. No cgroup requirement for B1. cgroup containment was never a PLAN, runbook or author requirement (your own B1_STOP_ALTERNATIVES_20261107.md says so), and Stage A ran on TASL-7 without it. B1 uses the same process management as Stage A (t7h8/t7j10), plus today's accepted B1 units that do not depend on cgroups. Do not integrate the cgroup, supervisor, freezer or exit-receipt candidates into the B1 path; keep them on their branches.
>    STOP semantics for B1: stop starting new work; stop the B1-owned worker processes and the B1 llama-server through the existing stop paths; preserve every output file, ledger and log; publish STATUS; never re-run or change anything automatically. Log or record lines written during the shutdown itself are acceptable and must be noted in the STOP report.
>    Not required for B1: kernel freezing, fsync/receipt durability guarantees, protection against a malicious same-UID process, or proof that in-flight GPU work has finished.
>
> 2. Scope of the no-deletion rule (amends R1-EXAM-B1-NO-DELETION-07NOV). It applies to repository files, experiment outputs and evidence, other tracks' files and processes, and remote files. It does not apply to normal internal temp, lock and pending-guard files that the pinned harness a3fedbb, pytest's tmp directories or Python caches create and clean up themselves. The harness pin stays a3fedbb; no harness replacement, and no push of the harness candidate.
>
> 3. Tests: run the B1-related tests and the full suite with pytest normally, on the Mac and on TASL-7 as needed.
>
> Everything else in the 7 Nov prompt stands, including the Q2 rule and the other launch conditions. Goal unchanged: get B1 launched as soon as those conditions hold.

The same answer bundle also included a response to the older conditional harness-pin question: **“先完成验证再决定（建议）”**. The preceding explicit decision that the harness pin stays `a3fedbb` and there is no harness replacement is retained as written. The selected response to the older question does not adopt the replacement or authorize a push.
