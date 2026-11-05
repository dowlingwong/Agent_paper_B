# Independent Mac overnight report review — 5 November 2026

AI-assisted (Codex). Interim draft checked in `/private/tmp/paper-b-mac-20261104`, SHA-256 `aa61860bba43ef47edea60611dc09de009b5034faadedddecaac3bbf20833a58`. **Round 1: NOT ACCEPTED** pending the corrections below. This review is documentation-only; no server, model, GPU, experiment, author decision or launch authority is supplied.

1. The earlier draft's M10 section described the default-off switch and HK1 checks but omitted the separate EVIDENCE authorization STOP. `MAC_M10_INTEGRATION_REVIEW_20261105.md` states that EVIDENCE remains refused until the separate author-note gate exists. Include the unblock, owner and effort and do not imply enabling the switch closes it.
2. The statement that no real server was contacted was too broad: feature branches were pushed to GitHub. Narrow it to no experiment host or real model service and disclose GitHub publication.

Checks on the initial draft: the proposed B1 row has an empty decision cell and the English author approval line is explicitly conditional; the B1 rule digest, note fields, both Stage A digests and code pin agree with the unsigned note and prior reviews. The entire held operator quotation is byte-identical to `B1_OPERATOR_MESSAGE_V3_DRAFT_20261105.md`. B1 launch and M3 replay are correctly STOP; offline/synthetic and production limits are distinguished. Listed B1 and integration code commits are ancestors of their respective reviewed checkouts; M10's 33 fake-Slurm tests, M3's eight synthetic loader tests and M13's read-only inventory are supported by their named reviews. These are documentation checks, not independent re-execution of the full implementation.

During this review a fresh M10 audit identified additional purported authority-parser and DEADLINE-resubmission blockers; the report is being updated. I independently reproduced the fenced-example parser defect on `b77ec1b` by mocking `Path.read_text`: `hk2_common.plan_has_row` returned `True` for an authorization ID appearing solely inside a fenced markdown example under dated §10. No Slurm or filesystem mutation was used. Await the fresh audit's durable written record and a corrected final report before recheck; do not represent M10 as currently accepted for use.

## Same-reviewer interim recheck

**ACCEPTED for the interim DRAFT only**, SHA-256 `6986972919b1179c126ed3587fe8214808f48a55bf38ca8a44cae8763169dff1`. The report now limits its no-contact claim to experiment hosts and real model services and discloses GitHub publication. The separately refused EVIDENCE path, necessary HK6/HK7/J5 implementation, scope binding and author-note gate are explicit, with owner and estimated effort. It records M10 as not accepted after the fresh audit and conditions HK1 switch enablement on repaired and independently reviewed code. The interim M10 parser, DEADLINE and EVIDENCE observations agree with `MAC_M10_FINAL_READINESS_REVIEW_20261105.md` at audit commit `34c8df4`. The held operator quotation remains byte-identical to the source draft, and the author decision cell remains empty.

This is not acceptance of B1 launch, M10 use, M3 replay, any author decision or the eventual morning report. A changed report, including corrections reflecting subsequent M10 reviews and the actual morning handoff, needs a further independent recheck against its exact final bytes.

## Same-reviewer interim recheck after M10 integration

**ACCEPTED for the revised interim DRAFT only**, SHA-256 `da8e6ecfa43a5c98d6a1bf5d162127e3432f57a842007165b13c8792ffd3676b`. M10 commits `3e43e6c`, `59b08d3` and review commit `113eec8` are ancestors of the integration checkout. `MAC_M10_FINAL_INTEGRATION_REVIEW_20261105.md` supports the two engineering repairs, Python 3.9 fake-Slurm result of 38 passed, and retained full-M10/EVIDENCE STOP. The report now identifies Q19's proposed F/C/D, accounting, budget, timing, shape and marker choices as author decisions, and correctly discloses the caller-selected PLAN and exact-manifest-only DEADLINE process limits. These are not site or phase approvals. The held operator quotation still matches the source exactly; no author decision is filled in.

This is a review of the interim report's claims, not re-execution or approval of the M10 implementation. The final morning report requires a further independent recheck against its final bytes and subsequent branch state.

## Same-reviewer interim recheck after M10 and M11 updates

**ACCEPTED for the revised interim DRAFT only**, SHA-256 `5d875d7ac452a84e43b244863f5faaf7ac208fbf9c36caa2f9f3352db308d04a`. Commits `3ff6de7`, `0d6d569`, `8645778`, `d9447e1`, `3d0b915` and `4025d8b` are ancestors of the integration checkout. `MAC_M10_EVIDENCE_NOTE_INTEGRATION_REVIEW_20261105.md` supports the standalone proposed-format checker's seven synthetic Python 3.9 tests and confirms that the submitter does not use it; EVIDENCE and HK6/HK7 remain refused. `MAC_M11_FINAL_READER_INTEGRATION_REVIEW_20261105.md` supports the reader corrections and 39 synthetic tests, while leaving D8, author confirmation, protected training-reader coverage and hostile alias/race protections outside its scope. The report names the remaining work, owner and estimated effort, and its M10 EVIDENCE estimate reflects the independently reviewed one-to-several-day range. The exact held operator quotation remains byte-identical and the author decision cell remains empty.

This is a documentation recheck only. It does not authorize any experiment or accept full M10/M11, and it does not accept the final morning report. Recheck the latter against its final bytes and the then-current branch state.

## Same-reviewer interim recheck after B1 sealed-path correction

**ACCEPTED for the revised interim DRAFT only**, SHA-256 `366a1294dcd6383aa9368fbee562a692c3482e42dbd462c06fa449668ae23bce`. On B1 branch head `4019756`, the independent adversarial audit accepts only the case-insensitive sealed-path correction at code pin `bab4b8cb0569b94c23f2828f1a8cdb5ce3782dcf`; its synthetic batch suite reported 36 passed. The independent draft review accepts the unsigned repin and held wording only. That pin is an ancestor and matches config and both draft documents; actual hashes of the note, operator draft, rule and O1 report match the repin review. The held operator quotation in this report is byte-identical to the updated operator draft. The report correctly identifies the earlier full-handoff review as preceding the later fix and says a final checkout review remains necessary. M10 EVIDENCE and M11 protected training-reader limits remain explicit. No author decision cell is filled.

This review accepts the current interim documentation only; it neither re-executes B1 nor accepts a production batch or final author-bound checkout. A further independent recheck is needed after subsequent changes and at the morning handoff.

## Same-reviewer interim recheck after M3/M10 inventories

**ACCEPTED for the revised interim DRAFT only**, SHA-256 `4b47a322b257ec1601c8a9b274077756434ae894dc0bdfbece92eae871f07290`. The reviewed M3 dependency inventory and HoreKa work-identity inventory are integrated in ancestor commits `c4b4d97` and `bdf5c51`; their report bytes match the SHA-256 values in their independent reviews. Both reviews explicitly limit acceptance to file-only source inventory, with offline executability, actual-work identity, site capability and authorization unresolved. The interim report correctly distinguishes the overnight request's HoreKa §3 items 1–2 from the later runbook templates, Slurm mode and shard/merge items 3–7. Full M10 and EVIDENCE remain STOP pending their own author, implementation/review and site conditions. The B1 operator quotation remains byte-identical to the updated held draft and no author decision is filled.

This documentation recheck is not implementation, site, phase or final-report acceptance. Recheck the morning report against its exact final bytes and then-current branch state.

## Same-reviewer interim recheck: historical full-suite disclosure

**ACCEPTED for the revised interim DRAFT only**, SHA-256 `b34f001d9d16583ce447a8147add9500fe81e8418ff46835d6424a8e1c8ff298`. The added historical result agrees with `docs/r1/reports/mac_m2_tests_20261104/authority_0437cea.log` on the B1 branch: **39 failed, 896 passed, 11 skipped**, log SHA-256 `f379057178992d94633e016656598b64809060740b184bf19f85096e6877b218`, matching the failure-classification report. The text explicitly labels these as historical, says the full suite was not rerun after the changes under the no-model instruction, and does not claim a passing current full suite. This is a documentation and retained-log check; it does not independently establish an absence of every possible unrecorded run.

The final morning report remains subject to independent recheck against its exact final bytes and then-current branch state. No model, host, server or experiment was used in this recheck.
