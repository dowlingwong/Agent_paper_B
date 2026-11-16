# Appendix draft — B1 post-hoc engineering change: truncated proposer replies (11 November 2026)

**Status.** Draft for the paper appendix. AI-assisted (Claude, Mac-local agent). It discloses PLAN §10 `R1-EXAM-B1-TRUNCATION-INVALID`. Fields in ⟨…⟩ are filled from the diagnosis (`reports/B1_TRUNCATION_DIAGNOSIS_20261111.md`) and from the restarted run's B1 report.

---

**Truncated proposer outputs (post-hoc engineering change).** The pre-registered B1 procedure did not say what happens when a proposer's reply is cut short. A run of B1 stopped when one thinking-mode reply of `qwen36_27b` filled the 32,768-token context: 31,551 generated tokens, against a configured thinking budget of 2,048. The client library raised an error at that point, and the error ended the campaign. Sixty-four campaign roots had completed at the time. No candidate's result had been read or used; the anchors' descriptive fields (the scripted − random-valid difference and the 7B duplicate rate) had been recorded in the stop report. We then made one engineering change and reran B1 from the start in a fresh output tree.

1. A reply that ends because of the length limit (or a content filter) is an **invalid proposal**. Its text is discarded, even if part of it would parse. It counts against the candidate's LLM-call budget like any other proposal, and the campaign continues. This is the same treatment as any other reply that does not parse into the proposal schema.
2. Every proposer call carries a completion cap of **16,384 tokens**, half the context. We fixed this value before inspecting the stopped run's per-call usage. We then checked that it exceeds the largest completion of every completed root of that run (largest: 2,178 tokens, a thinking-on call of `qwen38_27b`; per-root table in the diagnosis, §3). So the cap would not have cut any reply of those 64 roots. The failed root's calls are reported separately: 12 calls of at most 2,173 tokens, then the 31,551-token reply, which the cap would have cut.

Nothing else changed: models, quantisations, server build and flags (including the 2,048-token thinking budget), prompts, schema, seeds, budgets, nodes, the ranking rule `x5_rule_v2` and its analysis.

**What a reader should know.** In this server build the thinking budget is enforced only when the chat template exposes a thinking start and end tag. For the two thinking-on models of the stopped run it took effect: every other thinking-on call ended within 2,178 tokens (diagnosis §2–§3). Why the one stopped call ran to 31,551 tokens could not be established from the retained evidence. Thinking-on rows of B1 are therefore read as "thinking with a 2,048-token budget", with replies that overrun anyway capped at 16,384 tokens and counted as invalid ⟨confirm for every thinking-on candidate of the restarted run from its usage table⟩. Truncated proposals per candidate and mode in the restarted run: ⟨table: candidate, mode, proposer calls, truncated, share⟩. A model that often thinks past the cap loses those calls as invalid proposals. This lowers its valid-proposal rate. It affects its audited μ̂ only through which proposals reach the audit.

---

Provenance: STOP report `reports/B1_STOP_FFFA_20261111.md` (branch `mac-b1-20261107` @ `8af27919`); code `r1/exam/b1_llm_truncation.py` (`1334c616`); configuration re-pin `62adc6a3`; review `reviews/B1_TRUNCATION_REVIEW_20261111.md`.
