# B1 `_c` run-HEAD review — 12 November 2026

**Reviewer:** `b1-runc-head-reviewer`, a fresh independent reviewer. Read-only; I did not write this unit.
**Unit:** `ops-b1-restart-c-20261112` at `4b312844962e1106db04d5a60bf996fad0e3e514` (run-ID prefix `4b31`), parent `f1a776095216c77d6793a80dba998586b9c41254`, tree `760cf663470026691bb8b7036a7195a271c1a864`.
**Method:** fresh bare repo `/tmp/b1c_review/repo.git`; `git ls-remote` + fetch of the run branch from `https://github.com/dowlingwong/Agent_paper_B.git`; the delivery bundle `Claude outputs/b1_trunc_20261112.bundle` (sha256 `cc0d66c3406b2206871ee48c092af82249f719b7d52c8c3e2a009ffa3b735205`) fetched into the same object database (`git bundle verify` → `fbe7d3f037c942adb02b15f1e5e67a03767299b8 refs/heads/mac-b1-trunc-20261111`, prerequisite `fffa45a1`). Nothing was written under `agent_paper_B`; no TASL host was used. The base's round-4 reviewer was a different agent.

Result: all six requirements PASS. One residual item (force-free push) is not observable after the fact; no finding.

## Requirement 1 — one new commit on the reviewed base, branch and push

- `git rev-list --count f1a776095216c77d6793a80dba998586b9c41254..4b312844962e1106db04d5a60bf996fad0e3e514` = **1**; `git rev-list --parents -n1` = `4b31284 f1a77609` (single parent, no merge); `git rev-list --merges` over the range is empty.
- Remote: `git ls-remote origin refs/heads/ops-b1-restart-c-20261112` = `4b312844962e1106db04d5a60bf996fad0e3e514`, exactly HEAD. Branch name date `20261112` matches the commit date `2026-11-12T20:56:04+01:00` (`19:56:04Z`, same UTC date); run-ID prefix `4b31` = first four hex.
- PASS. The "pushed without force" property is not provable from a single fetch; see residual notes.

## Requirement 2 — prose-only change; JSON block byte-identical

- `git diff-tree -r --raw 4b31284` has exactly one line:
  `:100644 100644 5c9bd52ad3d6a0613d2a1e637174799f6f47b955 0c5dd06ae9fe998d8fed4f0a576418fa7d9b588b M docs/r1/authorizations/trackx_b1_20261105.md`
- The only changed hunk is `docs/r1/authorizations/trackx_b1_20261105.md:3` (prose). No mode change, no deletion (`git diff --diff-filter=D --name-only f1a77609 4b31284` empty).
- JSON block `trackx_b1_20261105.md:5-21`: **fence-to-EOF SHA-256 = `7a0486d5478aafe1499273a55f725b2f534ca2ad8449c76c9608c0e0738d14be`** at both HEAD and parent — matches the value in the request.
- `json.loads` of the block succeeds; 13 top-level keys; `approved` is `True` (`trackx_b1_20261105.md:9`).
- Full-file SHA-256: HEAD `0ef175aaad4544298a9944565ca15437abafb0346ed8e2d03a79fc8d920ed32e`, parent `e1bff5e42747efa40d99ee87cd622c1cfcd6c6eda53d736a3c839e1a4a32bec7` (prose only).
- PASS.

## Requirement 3 — prose content

`docs/r1/authorizations/trackx_b1_20261105.md:3` names every required fact:

- "the `_c` restart of B1" — yes; "run `fffa_20261111_b` stopped on a truncated proposer reply" — yes; "the fix is commit `1334c616`" — yes; "under PLAN §10 `R1-EXAM-B1-TRUNCATION-INVALID`" — yes; "the reviewed base is `f1a776095216c77d6793a80dba998586b9c41254`" — yes; "the restart hand-off is `proposals/B1_RESTART_HANDOFF_C_20261111.md`" — yes (file present at `docs/r1/proposals/B1_RESTART_HANDOFF_C_20261111.md`, sha256 `47b79bf55c673d8b4cbf81bc52082166f8ed3efa7447f8b9cd2c2e1c65d370cd`).
- No satisfaction claim: line 3 retains "It does not by itself establish those conditions or authorize launch" and ends "The real gate, current host preflight and handover remain required." No stale `_b` restart text, `ac32231c`, or `B1_RESTART_HANDOFF_20261109.md` reference remains in the note.
- PASS.

## Requirement 4 — metadata, scope, protected paths

- Author = committer = `Dowling Wong <wangdowling@gmail.com>`, both dates `2026-11-12T20:56:04+01:00`.
- Message is accurate: subject "Update B1 candidate note for the _c restart (truncation fix)"; body facts checked against the diff (base `f1a77609`, fix `1334c616`, hand-off, "JSON bindings byte-identical"). The sentence "This is the run HEAD for the exact-HEAD review, the real author gate and the host preflight" is forward-looking and does not claim those steps are done.
- One file changed, nothing deleted, no mode change.
- Protected-path diff `git diff --name-only 1334c616 f1a77609 -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` = **empty**; the same command for `f1a77609 4b31284` is also empty.
- PASS. (The commit carries no SSH signature; the `_b` run HEAD `fffa45a1` is also unsigned, and hand-off §1 states no signing requirement.)

## Requirement 5 — delivery readiness (§0 preconditions)

1. Diagnosis `docs/r1/reports/B1_TRUNCATION_DIAGNOSIS_20261111.md` (210 lines, sha256 `b751d9021f520fafceed867b9f7666e4e77b11133f0c07eba1d0aa715b900144`): `grep -i pending` gives 0 hits, so no PENDING section. `:76` records the scratch-venv re-run "17 passed, 0 skipped". `:100` "**cap check PASS**: 2,178 < 16,384"; `:107` "completed roots 64 (LLM 40) … 2178 → cap check **PASS** (margin 14206)".
2. I parsed the §3 table myself (lines 109-210): 66 data rows = 64 `completed=yes` + 1 failed root (`qwen36_27b/b1/on/openml_credit_approval__s9001`, completed=no) + 1 separator. Over the 64 completed roots the maximum `max completion` is **2,178**, none ≥ 16,384, and no completed root has a truncated or failed call. This satisfies hand-off §0.2 ("64 completed roots", PASS).
3. PLAN §10 rows are present: `R1-EXAM-B1-ANCHOR-R4` (`docs/r1/PLAN.md:1134`), `R1-EXAM-B1-ANCHOR-R4-H2` (`:1135`), `R1-EXAM-B1-TRUNCATION-INVALID` (`:1141`).
4. Review: delivery tip `fbe7d3f0` has parent `f1a77609` and differs from it only by `docs/r1/reviews/B1_TRUNCATION_REVIEW_20261111.md` (one `M`). At the tip, `:1` = "Reviewed base: f1a776095216c77d6793a80dba998586b9c41254"; `:5` records "Round 4 … **accepted** at `f1a77609`, which is the reviewed base"; the last round's `Verdict: accepted` and `Accepted commit: f1a776095216c77d6793a80dba998586b9c41254` are `:580-581`. The review's `Reviewed base:`, the round-4 `Accepted commit:` and READY agree — no disagreement, no STOP.
5. `Claude outputs/READY.txt:27-39` (item 4): branch `mac-b1-trunc-20261111` (`:31`), tip `fbe7d3f037c942adb02b15f1e5e67a03767299b8` (`:32`), Reviewed base `f1a776095216c77d6793a80dba998586b9c41254` (`:33`), review file (`:34`), restart hand-off `docs/r1/proposals/B1_RESTART_HANDOFF_C_20261111.md` (`:35`) — all match the bundle/tree facts.
- PASS — no STOP condition.

## Requirement 6 — tree and JSON bindings

- The run-HEAD tree differs from the parent in exactly the one note blob (`diff-tree` above); `r1/scripts/configs/exam_b1_v2.json` is unchanged by this commit.
- Note JSON (lines 9-19) vs config: `rule_sha256` = `53018aa7…` (`exam_b1_v2.json:17`), `stage_a_table_sha256` = `00ab143d…` (`:73`), `stage_a_amendment_table_sha256` = `7152512…` (`:82`), `stage_a_amendment_acceptance_sha256` = `0cda82fa…` (`:84`), `anchor_duplicate_reference.sha256` = `84200770…` (`:49-52`), `llm_call_cap` 80 (`:42`), `host` TASL-7 (`:3`), `gpu_uuid` `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` (`:6`), `workers` 20 (`:72`), `nodes` (`:43-47`); the config binds the note at `authorizations.b1` (`:56`). All **MATCH**.
- Recomputed file hashes: `r1/exam/rules/x5_rule_v2.yaml` = `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`; `docs/r1/reports/B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json` = `84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd`; `docs/r1/reports/OPS_O1_20261104.md` = `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e`. The two Stage A table digests (`00ab143d…`, `7152512…`) bind host-side files not in the repo; they are unchanged from the parent and bound identically in the config, `PLAN.md:914` and the accepted O1 record — consistent, not locally recomputable (expected).
- `paper_commit` (`exam_b1_v2.json:19`) = `1334c61619f76e71a7c6ba83c837714f9d3f0720`; `1334c616` is an ancestor of `f1a77609`; the anchor interval lower/upper values are unchanged.
- PASS.

## Residual notes (non-blocking)

- **Force-free push** cannot be verified after the fact from a single fetch (git exposes no push type). The evidence is consistent: one commit on the base, linear history, remote tip exactly the reviewed SHA. No indication of a rewrite.
- **Delivery branch not on origin:** `git ls-remote` at review time lists `ops-b1-restart-c-20261112` but not `mac-b1-trunc-20261111`. The reviewed base `f1a77609` is nevertheless on origin (reachable from the pushed run branch), and the review-record tip `fbe7d3f0` is in the bundle. This matches READY's bundle-delivery process; if the process expects the delivery branch pushed before staging, the Mac should push it.
- **Run-HEAD tree's review file is the pre-round-4 version** (rounds 1-3, last accepted `1c543173`), because the round-4 record commit `fbe7d3f0` is a delivery-only review-record commit after the base. This is exactly what hand-off §1 allows; the round-4 record at the delivery tip names `f1a77609`.
- The review record's intro at the delivery tip still says "Three rounds by one … reviewer agent" although round 4 is appended (`:5`); cosmetic, delivery-file only, and the same file clearly states round 4 and the accepted base.
- **Not exercised:** staging, the author gate, host preflight, and any TASL-7 operation are outside this read-only review; this acceptance covers the checkout metadata/content only.

## Verdict

VERDICT: accepted
