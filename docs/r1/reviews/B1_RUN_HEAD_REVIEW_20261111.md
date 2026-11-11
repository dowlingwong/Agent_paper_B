# Independent review — B1 run HEAD `fffa45a` (11 Nov 2026)

**Reviewer.** Freshly spawned independent reviewer; did not write this unit. Tree was obtained only from the remote in a fresh throwaway clone under `/tmp/b1_review_20261111/repo` (`git init` + `git fetch` of the exact branch/tips; `git cat-file`/`rev-parse`/`show` only). Nothing under `/Users/wongdowling/Documents/agent_paper_B` was touched, and no TASL host was contacted.

**Unit under review.**

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `ops-b1-restart-20261111`, HEAD `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa`, parent `ac32231c5ee787401e7f67b9acb4650e68ad30d9`.
- Parent = the reviewed base named on the `Accepted commit:` line of the last accepted round (round 8) of `docs/r1/reviews/B1_R4_REVIEW_20261109.md` on `mac-b1-r4-20261109` (delivery tip `3c0fa0b7e6e099ca7125a0eebc19758341b0ad7d`).

## Checks

### 1. Remote branch is exactly `fffa45a1…` — PASS

`git ls-remote https://github.com/dowlingwong/Agent_paper_B.git refs/heads/ops-b1-restart-20261111` returned
`fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa	refs/heads/ops-b1-restart-20261111`.
The local `run` ref (fetched from the remote, not from any working copy) resolves to the same SHA. `git ls-remote` for `mac-b1-r4-20261109` returned `3c0fa0b7e6e099ca7125a0eebc19758341b0ad7d`.

### 2. One commit on top of the reviewed base, on the required branch — PASS

- `git rev-list --parents -n 1 refs/heads/run` → `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa ac32231c5ee787401e7f67b9acb4650e68ad30d9` (single parent, not a merge).
- `git rev-list --count ac32231..fffa45a` = **1**; `git merge-base --is-ancestor ac32231 fffa45a` holds.
- Branch name `ops-b1-restart-20261111` matches `ops-b1-restart-<YYYYMMDD>`; the commit timestamp is `2026-11-11 11:07:14 +0100`.
- The remote object graph shows a single fast-forward child of the base, which is consistent with a non-force push. A `--force` push cannot be distinguished from the object graph alone — see residual note R-1.

### 3. Only the prose of the note changed — PASS

`git diff --name-status ac32231 fffa45a` → exactly one entry:
`M docs/r1/authorizations/trackx_b1_20261105.md`.
`git diff --raw` shows `100644 100644 095ed20 5c9bd52` — same mode, no add/delete/rename, no mode change; `--numstat` is `1 1`. `git diff --name-status --diff-filter=D` is empty (no file deletions). `git diff --name-only ac32231 fffa45a | wc -l` = 1, so the HEAD tree is the base tree except this one blob.

### 4. JSON block byte-identical; still valid and `approved: true` — PASS

The note file has 21 lines / 1697 bytes at HEAD and 21 lines / 1409 bytes at the base; the ```json fence is line 5 in both. Hashing from the ```json fence (line 5) to EOF gives, for **both** base and HEAD:

- length = **770 bytes**, SHA-256 = `7a0486d5478aafe1499273a55f725b2f534ca2ad8449c76c9608c0e0738d14be`.

So the entire JSON block is byte-identical. Parsing it yields 13 keys (`author`, `phase`, `approved`, `rule_sha256`, `nodes`, `stage_a_table_sha256`, `stage_a_amendment_table_sha256`, `stage_a_amendment_acceptance_sha256`, `anchor_duplicate_reference_sha256`, `llm_call_cap`, `host`, `gpu_uuid`, `workers`); `approved` is `true`.

### 5. New prose names the required things and claims nothing beyond them — PASS

At HEAD the prose paragraph (`docs/r1/authorizations/trackx_b1_20261105.md:3`) contains, verbatim:

- the R4 restart: "This candidate is the R4 restart of B1 after run `6835_20261108_a` stopped on the anchor gate";
- the stopped run: `6835_20261108_a`;
- the reviewed base: `ac32231c5ee787401e7f67b9acb4650e68ad30d9`;
- this hand-off: `proposals/B1_RESTART_HANDOFF_20261109.md`.

It retains the negative caveats: "It does not by itself establish those conditions or authorize launch." and "The real gate, current host preflight and handover remain required." It does **not** claim the gate, preflight or handover are satisfied; the words "satisfied"/"passed"/"completed" do not occur. The order authority is cited (`PLAN §10 R1-EXAM-B1-NOTE-ORDER-07NOV`), and the R4-H2 plan row is cited (`PLAN §10 R1-EXAM-B1-ANCHOR-R4-H2`).

### 6. Commit identity and message — PASS

`git cat-file -p fffa45a`: `author Dowling Wong <wangdowling@gmail.com> 1794391634 +0100` and `committer Dowling Wong <wangdowling@gmail.com> 1794391634 +0100`. The message ("Update B1 candidate note for the R4 restart", body: R4 restart after run `6835_20261108_a` stopped on the anchor gate; diagnosis accepted class D via H2 alone / H1 not supported / D7 PASS; author adopted R4 via `R1-EXAM-B1-ANCHOR-R4-H2`; names the stopped run, reviewed base and hand-off; JSON bindings byte-identical; this is the run HEAD for the exact-HEAD review, real author gate and host preflight) is accurate against the facts verified in §7–§8.

### 7. Side facts asserted by the note are consistent with the reviewed base tree — PASS

- **PLAN row `R1-EXAM-B1-ANCHOR-R4-H2` exists and is dated 11 Nov.** `docs/r1/PLAN.md:1135` on the parent (`git show ac32231:docs/r1/PLAN.md`): "R1-EXAM-B1-ANCHOR-R4-H2 (11 Nov; amends R1-EXAM-B1-ANCHOR-R4)" — class D resting on H2 alone, H2 on `random_valid`/digits_mlp only, H1 not supported, H3 supported, H4 not supported, **D7 PASS** (120/242 = 0.4959). It also records that B1 restarts via `proposals/B1_RESTART_HANDOFF_20261109.md` after independent review.
- **Note-order authority exists.** `docs/r1/PLAN.md:1065`: row `R1-EXAM-B1-NOTE-ORDER-07NOV` = "允许此顺序" (author allowed committing the `approved: true` candidate, then exact-HEAD review, the real gate and preflight, launching only when every condition and the handover hold).
- **Hand-off §0 on the parent admits class D with H1 or H2 and D7 PASS.** `docs/r1/proposals/B1_RESTART_HANDOFF_20261109.md:9-10`: "class D with H1 or H2 supported … gives class D with H2 supported (on random_valid/digits_mlp only), H1 not supported …", and "Its D7 line is PASS … 120/242 = 0.49586776859504134" inside the pinned interval `[0.42386590667728663, 0.5800007633587785]`.
- **Parent and accepted round 8.** Parent is `ac32231c…`; in `docs/r1/reviews/B1_R4_REVIEW_20261109.md` at the delivery tip `3c0fa0b` the round-8 header (`:430-434`) names `ac32231c5ee787401e7f67b9acb4650e68ad30d9` as its `Unit:`, the file's last accepted round ends with `Accepted commit: ac32231c5ee787401e7f67b9acb4650e68ad30d9` (`:473`) and `VERDICT: accepted` (`:475`). The `Reviewed base:` line at the top (`:3`) names the same SHA. `git diff --name-status ac32231 3c0fa0b` lists only `M docs/r1/reviews/B1_R4_REVIEW_20261109.md` (review-record-only commit, as §1 permits).
- **Diagnosis report.** `docs/r1/reports/B1_STOP_DIAGNOSIS_20261111.md` exists on branch `mac-b1-diag-report-20261111` @ `3e4d7cc9` (the branch/tip named by hand-off §1:24 and PLAN row `:1135`); its lines 9–15 state: Class **D — resting on H2 alone**; H1 **NOT SUPPORTED**; H2 SUPPORTED (`random_valid`, 0.756 σ_joint); D7 **PASS** 120/242 inside the same pinned interval. It was accepted in round 3 of `docs/r1/reviews/B1_STOP_DIAGNOSIS_REPORT_REVIEW_20261111.md` (final line `VERDICT: accepted`). The report is intentionally on that separate branch and is **not** in the run-HEAD tree — the note cites it by the same repo-relative path convention used by the PLAN row and the hand-off (paths relative to `docs/r1/`); see residual note R-2.

### 8. JSON bindings match the HEAD config; rule/config unchanged — PASS

`r1/scripts/configs/exam_b1_v2.json` at HEAD carries values identical to the note's JSON bindings: `rule_sha256 = 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`, `anchor_duplicate_reference.sha256 = 84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd`, `stage_a_table_sha256 = 00ab143d…`, `stage_a_amendment_table_sha256 = 71525124…`, `stage_a_amendment_acceptance_sha256 = 0cda82fa…`, `llm_call_cap = 80`, `host = TASL-7`, `gpu_uuid = GPU-ab72fb4a-…`, `workers = 20`. The rule blob `r1/exam/rules/x5_rule_v2.yaml` hashes to `53018aa7…`; `docs/r1/reports/B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json` hashes to `84200770…`; `docs/r1/reports/OPS_O1_20261104.md` hashes to `0cda82fa…`. `git diff --stat ac32231 fffa45a -- r1/scripts/configs/exam_b1_v2.json r1/exam/rules/x5_rule_v2.yaml` is empty (config and rule are unchanged base→HEAD).

### 9. No protected exam path, rule, config or bound artifact changed — PASS

`git diff --name-only ac32231 fffa45a -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py r1/scripts/configs` is empty, and the commit tree delta is a single path (§3). The `paper_commit = fb57c6a45eceba1fc468bccb4efcefd5440398b3` re-pin is untouched, as required for the R4 fix.

## Residual notes (non-blocking)

- **R-1 — force-push is not provable from the object graph.** The remote shows a single fast-forward child of the base with no rewritten ancestry, which is consistent with a non-force push; only the operator's push log can confirm no `--force`. Requiring that confirmation is reasonable, but it is not detectable from `ls-remote`/the objects.
- **R-2 — cited diagnosis path is repo-relative to `docs/r1/`.** The note (and PLAN row `:1135`, hand-off §0/§1) writes `reports/B1_STOP_DIAGNOSIS_20261111.md`, i.e. `docs/r1/reports/B1_STOP_DIAGNOSIS_20261111.md`; the file is on `mac-b1-diag-report-20261111` @ `3e4d7cc9`, not in the run-HEAD tree. That matches the documented branch/tip, so the note is not asserting a file in the checkout.
- **R-3 — the prose drops the earlier model-inventory sentence.** `git diff` (base line vs HEAD line 3) removes "The first model-inventory attempt remains incomplete and preserved; the author's single authorized new attempt passed its scoped independent review." No governing requirement (hand-off §1:23, PLAN `R1-EXAM-B1-NOTE-ORDER-07NOV`) mandates that sentence, and the required names and negative caveats are all present, so this is within the allowed "prose only" change.

## Verdict

All governing conditions check out: the remote branch is exactly `fffa45a1…`; the HEAD is one commit on the reviewed base `ac32231c…` on `ops-b1-restart-20261111`; the commit changes only line 3 of `docs/r1/authorizations/trackx_b1_20261105.md`; the JSON block from the fence to EOF is byte-identical (`7a0486d5…`) and still valid with `approved: true`; the prose names the R4 restart, run `6835_20261108_a`, the reviewed base and the hand-off and does not claim the gate/preflight/handover are satisfied; author and committer are `Dowling Wong <wangdowling@gmail.com>`; the asserted diagnosis/PLAN/hand-off/review facts match the reviewed-base tree and the delivery tip. This exact HEAD is fit to be checked out clean on TASL-7, to receive the real author gate and host preflight, and to be the run HEAD (its first four hex `fffa` give the run-ID prefix).

VERDICT: accepted
