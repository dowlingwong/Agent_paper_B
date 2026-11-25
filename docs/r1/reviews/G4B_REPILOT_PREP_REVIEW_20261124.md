Reviewed base: origin/main `3024db3f8`; accepted at `364cfda0` (launch commit `cfa299e1`), confirmed at `c611edbf08334e1af60e09004ed7b017f549380b` (launch commit `0fc96f28ef99e4819f1dce9e15332afe82ee3520`)

# Independent review record — the G.4b re-pilot (R1-G5-DIFF-RECOUNT): the G.4b pin rule in `g4_tasl.py`, the G.4b spec, the re-issued G.4 note draft (approved: false) and the launch commit

**Unit.** On `mac-g4b-repilot-20261124` (on main `3024db3f`): `sweep2/t1_tasl/g4_tasl.py` (a spec whose `harness` block carries `g1b_pin` or `pin_rule` is G.4b; otherwise the G.4 behaviour is unchanged and the shipped `g4_tasl_spec.json` still validates. G.4b desk checks: `pin_rule` R1-G5-DIFF-RECOUNT, `g1b_pin` `c025f89a`, a successor commit, the G.1b environments, run id `g4b-tasl-<date>-<letter>`, a checkout that is none of G.1b's, G.4's or the two G.5 families'. Launch: `harness_rule_check` reuses `g5_tasl.measurement_path_check` against the G.1b pin, requires `pilot_g4.py`, `manager_v2_diff.py` and `proposal_v2_diff.py` equal to the pin and the recount needle in `campaign_v2_diff.py`; the TASL-2 host record is checked against `g1b_pin`, as G.5 does; R1-G5-DIFF-RECOUNT is a bound PLAN row; new `check-note [--draft]` and `harness-check`); `g5_tasl.py dates --pilot-spec`; `sweep2/t1_tasl/g4b_tasl_spec.json` (the three G.4 nodes, W = 20, seeds 4001–4003, run id `g4b-tasl-20261124-a`, checkout `harness_g4b`, harness `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98` (the reviewed G5-7 recount tip, READY 105), projection 11.077 GPU-h, cap 20; every other field as G.4's); `docs/r1/proposals/G4B_T1_TASL_NOTE_DRAFT_20261124.md` (approved: false; the disclosure of the G.4 pilot's strict-application liveness — 155/180 refused, 122 `malformed_hunk`, 33 `malformed_diff`, per node — citing `docs/r1/reports/tasl_chain_20261122/G4_TASL_PILOT_RESULT_20261122.md` at its main path with sha256 `07c03920e266375919fd95ebbd2805a8c15d3157a1ed9e9c80b565fa8747dbe8`; what G.4b measures; the binding eight-node `g5_tasl.py dates … --pilot-spec` and a seven-node comparison); the launch commit `0fc96f28` built by `sweep2/t1_tasl/build_g4b_launch.py` as in the TASL launch chain (only the spec and the note change; `paper.commit` = its parent `90d4dcee`; pinned dates; SSH-signed); the generated launch table; report `docs/r1/reports/tasl_chain_20261122/G4B_REPILOT_PREP_20261124.md` with the publication checks (§4) and the TASL-2 re-classification command (§7); tests `r1/tests/test_t1_tasl_g4.py`, `test_t1_tasl_g4b.py` (new), `test_t1_g5_tasl.py`. gate.py, gate_input_builder.py, release.py and the preregistration are unchanged. Authority: R1-G5-DIFF-RECOUNT; the user's messages of 24 Nov 2026 (18:10, 23:15).

**Full `r1/tests` suite** (LightGBM off the path, fresh TMPDIR): base 3024db3f 58 failed / 3 errors / 3823 passed / 197 skipped; tip `741c5d84` (later commit docs only) 58 / 3 / 3846 / 197; `FULLSUITE_G4B_BASE_3024db3f.txt` = `FULLSUITE_G4B_TIP.txt` (61 entries): zero new failures.

**Process.** One independent reviewer, read-only, own detached worktrees; `validate --launch`, `harness-check`, `check-note --draft` run on the launch commit; a simulated signed note passed strict `note_check` and `publication-check` against `origin/main` with the P4 reviews stubbed; the launch commit rebuilt in a scratch clone (identical tree). Round 1 accepted with six minors; the coordinating session applied them (the author's session was lost in a server restart), rebuilt the launch commit on the new base and re-ran the full suite; confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `364cfda0` | ACCEPTED (minors m1–m6) |
| 2 | `c611edbf` | ACCEPTED (confirmation; cosmetic n1, n2) |

**Open items.** Publication (report §4): do not re-run the builder after this review unless the rebuilt launch commit equals `0fc96f28` (the sha depends on SSH signing); check 5a — the G.4 result report is on `origin/main` with sha256 `07c03920…` before signing (it reaches main through the experiment agent's result branch); check 5b — the paper copy of `docs/r1/reviews/G5_DIFF_RECOUNT_REVIEW_20261124.md` equals the harness record at `cbf7a003` (sha256 `6dd4ffda…`); merge without squash or rebase so the launch commit keeps its sha; P4 names this record and the recount review; strict `check-note` and `publication-check` after a fresh fetch. The rule does not by itself limit what `campaign_v2_diff.py` can change; G.4b measures the recount and nothing else for the pinned reviewed commit `cbf7a003` (m1). The harness branches must be pushed before TASL-2 can fetch them. G.5's `pilot_basis` and P3 still read the G.4 spec; a G.5 unit points them to G.4b after its result. Cosmetic: n1 the refusal message for the G.5 checkouts names only G.1b and G.4; n2 report §8 names base `76043a05` where it is `90d4dcee`.

## Round 1 (`364cfda0`)

> Reviewed base: 364cfda06 (mac-g4b-repilot-20261124; launch commit cfa299e1; base 76043a05 on main 3024db3f)
>
> ## Summary
> No blocking problem. The pin rule, spec, note draft and launch commit hold up. Six minor findings, about wording or the publication checklist.
>
> ## What I checked and ran
> - **On the launch commit:** `validate --launch` rc 0 (11.077 GPU-h, 180 proposals); `harness-check --repo /tmp/pb/harness` rc 0 (308 measurement-path files unchanged, 15-file `noise_floor` closure without an engine file, `audit_g5.py` added); `check-note --draft` rc 0; strict `check-note` on the unsigned draft refused on its path, as it should be.
> - **Simulated signed note** (copied to `docs/r1/authorizations/g4_t1_tasl_20261125.md` with `approved: true`, against real `origin/main`): strict `note_check` stops only because P4's two review files are missing from main; with them stubbed it passes, including the TASL-2 record checked against `c025f89a` and cited by P1. `g1b_tasl_join.py publication-check` rc 0.
> - **G.4 path:** `g4_tasl_spec.json` byte-identical to `3024db3f` (`fd9c6e9d…`) and still passes `validate --launch`.
> - **Spec vs G.4 spec:** only `comment`, `third_node_reason`, `paper.commit` (= `76043a05`), `run_id` (`g4b-tasl-20261124-a`), `harness.{commit,branch,g1b_pin,pin_rule}`, `worker.harness_dir` differ; nodes, pilot block (W = 20, seeds 4001–4003), cap 20 and host-check block identical; nodes match the G.4 result table.
> - **Disclosure figures** all match the G.4 result report (155/180; 122/33; 59 (53/6), 48 (45/3), 48 (24/24); 22 ran, 3 duplicates, 0 invalid, 0 inert; ran_of_valid 0.0167/0.1833/0.1667; ran share 0.1667, B7 2026-12-03).
> - **Citation:** `git show origin/ops-tasl-20261116:<path> | sha256sum` = `07c03920…dbe8`, the same at `9eafa66d` (the adding commit); the branch is now at `9253192f` with the file unchanged; not on origin/main yet.
> - **Recount review file:** `docs/r1/reviews/G5_DIFF_RECOUNT_REVIEW_20261124.md` exists on the harness at `cbf7a003` (sha `6dd4ffda…`); not on paper main; `G4B_REPILOT_PREP_REVIEW_20261124.md` on neither.
> - **Launch commit** matches the chain pattern (34a5b1d6, b5824240, 6ad899e0, d52c9d9d): one file outside `docs/` plus the note, parent = `paper.commit`, pinned dates, same trailer style, SSH-signed. Rebuilt in a scratch clone with signing off: tree `5f086e8b` identical; without the gpgsig header the author's commit hashes to my unsigned rebuild (`c623f531`); tail tree identical.
> - **Rule soundness:** the closure rooted at `noise_floor` suffices for `cbf7a003` (engine files import only trackg modules; nothing under `src/` outside trackg changed); the only other `campaign_v2_diff.py` change is `45cb3de` (`runner_factory`, default `WorkingCopyRunner`), inert on G.4's call path; `f31050f..cbf7a003` is a docstring plus docs.
> - **Host record against `g1b_pin`:** justified (`g5_tasl.launch` does `check_host_record(..., PC.PIN_SEVEN)`; `isolation.py`, `runner.py` byte-identical). HEAD = `harness.commit` and clean still checked under the lease.
> - **Report §7** `SHA=cbf7a003` consistent with harness §8 and the script's HEAD check.
> - **Invariants:** gate files, `release.py`, prereg unchanged; no `approved: true` field line; full-suite lists identical (61; 58 F / 3 E; 3846 − 3823 = 23 new test ids).
> - **Tests:** test_t1_tasl_g4 47; test_t1_tasl_g4b 5; test_t1_g5_tasl 116; test_t1_tasl_g1b 45; test_t1_tasl_chain 16.
> - **Dates commands** run (`g5_tasl.py dates … --pilot-spec` rc 0, fallback basis; the seven-node `g4_tasl.py dates` takes the G.4b spec).
>
> Seed reuse right and disclosed; P1 CUDA IPC "unchanged" acceptable.
>
> ## Minor findings
> - **m1** `g4_tasl.py:178-215` with `g5_tasl.py:1444-1470`: the rule does not by itself limit what `campaign_v2_diff.py` can change (excluded from the measurement path; only the needle checked; a new non-trackg module it imports is neither restricted by `NO_ADDITIONS` nor seen by the closure). Safe here only because `harness.commit` is pinned exactly and `cbf7a003` was reviewed. Say so in §2.
> - **m2** report §4 / note `g4_strict_liveness`: no publication check verifies the result report is on main (strict `check-note` and `publication-check` do not read that citation). Add `git show origin/main:<path> | sha256sum` = `07c03920…` before signing.
> - **m3** note P4: the paper-side recount review is not tied to the harness record; state the paper copy is byte-identical to `cbf7a003:docs/r1/reviews/G5_DIFF_RECOUNT_REVIEW_20261124.md` (sha256 `6dd4ffda613459f014c0c172d57040f1b36008faf66a7b0c434986f80450c096`) and check it.
> - **m4** report §4 check 1 / builder docstring: rebuilding reproduces the launch sha only under the same signing setup (SSH Ed25519, global `commit.gpgsign=true`); an unsigned rebuild gave `c623f531` with an identical tree. Require the rebuilt `launch_commit` to equal `cfa299e1`, or do not re-run after review.
> - **m5** `g4_tasl.py:120,149-159`: `pinned_checkouts` reads only the G.1b, AR-G.1b and G.4 specs; `harness_g5`/`harness_g5_ar` are not refused (a G.4b spec with `worker.harness_dir=…/harness_g5` passes `validate --launch`).
> - **m6** `g4_tasl.py:86,955-960`, note `measures`: the G.4 path is behaviourally identical but not "byte for byte" (it now imports `g5_pin_check`; `check_import_sources` checks more modules); the note's "among the engine files only the recount differs" omits the inert `runner_factory`.
>
> ## Housekeeping
> No commits or pushes in `/tmp/pb/repo`; worktrees removed and pruned; scratch in `/tmp/g4brev/_to_delete/`.
>
> VERDICT: ACCEPTED

## Round 2 (`c611edbf`)

> Reviewed base: c611edbf0 (launch commit 0fc96f28; base 90d4dcee)
>
> ## Summary
> All six fixes are in place and nothing else changed. The base diff is only those fixes; the launch commit, its three checks and both test files pass. Two cosmetic leftovers remain.
>
> **The base `90d4dcee`** (parent `76043a05`): only m5 in `g4_tasl.py` (`pinned_checkouts()` adds `g5_tasl_spec.json`'s `harness_families.*.harness_dir`; docstring updated), one m5 assert in `test_t1_tasl_g4.py`, and m6 in the note template's `measures` line. gate files, `release.py`, `r1/liveness/gate.py`, `docs/r1/authorizations/` unchanged from `3024db3f`.
>
> **The tail `94a880ae`:** m1 "Scope of the rule" in §2; m6 "behaviour unchanged … not byte for byte"; m4 check 1 (no re-run unless the rebuilt launch sha equals the reviewed one, because the sha depends on signing); m2 check 5a (the G.4 result report on `origin/main`, `07c03920…`); m3 check 5b (paper copy of the recount review byte-identical to `cbf7a003:…`, `6dd4ffda…`); config `base` `90d4dcee`, listed in §1.
>
> **The launch commit `0fc96f28`:** changes exactly the spec and the note; SSH-signed; parent `90d4dcee` = spec `paper.commit`. Against `cfa299e1`: the spec differs only in `paper.commit` (sha256 `56f8c293…`); the note only in `paper_commit`, `spec_sha256` and the m6 line; `harness_commit` still `cbf7a003`. Launch table `741c5d84` matches; `c611edbf` adds only docs.
>
> **Commands on the launch commit:** `validate --launch` rc 0 (11.077 GPU-h); `harness-check --repo /tmp/pb/harness` rc 0 (`cbf7a003`, pin `c025f89a`, 308 files, 15-file closure, no engine file, host check against `c025f89a`); `check-note --draft` rc 0 (one `approved: false` line, no `approved: true`). A simulated signed copy with the P4 reviews stubbed passes strict `note_check` against `origin/main`. Pinned checkouts: `harness_g5`, `harness_g5_ar`, `harness`, `harness_ar` refused; `harness_g4b` accepted; `g4_tasl_spec.json` still validates.
>
> **Tests:** test_t1_tasl_g4 47; test_t1_tasl_g4b 5 (none skipped). Full-suite lists identical (61); not rerun.
>
> **Cosmetic:** n1 the refusal message (`g4_tasl.py:290`) still says "must not be a G.1b or G.4 checkout" for the G.5 checkouts; n2 report §8 (≈ lines 409–410) says the launch commit was rebuilt on base `76043a05`; it is `90d4dcee`.
>
> VERDICT: ACCEPTED

---

Code-Commit: c611edbf08334e1af60e09004ed7b017f549380b
Verdict: ACCEPTED

Accepted at `364cfda0`, confirmed at `c611edbf`.
