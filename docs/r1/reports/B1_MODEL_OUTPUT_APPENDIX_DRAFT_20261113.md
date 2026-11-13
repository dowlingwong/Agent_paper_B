# Appendix draft — B1 post-hoc engineering change: model-output faults are invalid trials (13 November 2026)

**Status.** A draft for the paper appendix that discloses PLAN §10 `R1-EXAM-B1-MODEL-OUTPUT-INVALID`. AI-assisted (Claude, Mac-local agent). Fields in ⟨…⟩ are filled in from the restarted run's B1 report.

---

**Inconsistent or unusable proposals (post-hoc engineering change).** A proposer states its edit twice: in a free-text objective, which the worker executes, and in structured fields, which the ledger, replay and audits use. The pre-registered procedure stopped a B1 run whenever the two disagreed, or the value could not be inserted safely. A run stopped this way after 89 of its campaign roots had completed. One model's objective and fields named different edits; it had been proposing an impossible ridge model for several trials. No candidate result had been used.

We made one engineering change and reran B1 from the start, in a fresh output tree. Such a proposal is not executed. It is recorded as an invalid trial and charged one LLM call, exactly like a reply that does not parse. This applies when the objective names no executable change, names a different or non-editable parameter, or gives different old or new values. It also applies when the value contains a backslash or, for Python-configured nodes, is not a bounded finite number. A prompt that has outgrown the model's context (it repeats earlier proposal summaries) is treated the same way after the first trial, as is a reply whose summary cannot be encoded for the next request. Every proposal is now written to disk before anything is executed.

Proposals that were never stopped before are recorded exactly as before (apart from one improbable encoding case on a root's last call). Executed configurations that later fail on an audit seed, observer timeouts and transport failures still stop the run.

Model-output rejections in the restarted run, per candidate and mode: ⟨table: candidate, mode, proposer calls, rejected, by check⟩. A candidate whose proposals often contradict themselves loses those calls as invalid proposals. They count toward the pre-registered liveness gate's invalid-trial rate (eligibility requires fewer than 30 % invalid trials, thinking off), so frequent rejections can make a candidate ineligible, exactly as frequent unparseable replies would. Otherwise they affect its audited μ̂ only through which proposals reach the audit.

---

Provenance:
- stop report: `reports/B1_STOP_4B31_20261112.md` (`mac-b1-20261107` @ `3b7d5704`);
- diagnosis: `reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md`;
- code: `3458b672`, `02a91494`; configuration re-pins: `2eda52e7`, `c5bf524b`;
- review: `reviews/B1_MODEL_OUTPUT_REVIEW_20261113.md`.
