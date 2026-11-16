# Track P P.3a attempt-2 code units — review records and delivery (16 November 2026)

**Status: code units reviewed and accepted; delivery to TASL-7 BLOCKED by a TASL-7 network outage at the
time of transfer; Unit B not started.** AI-assisted; no GPU run. Authority: `author-decisions-20261116`
@ `4da73306` + `R1-TRACKP-A6-DEFER` (`author-decisions-20261116c` @ `65d8d5bb`); accepted Unit A plan
`docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md` (rev 2) + review `94d4c1de…`; M13 record `351611c5…`;
authorizations `trackp_p3a_20261027.md` + `trackp_p3a_amend_20261104.md`.

## 1. Reviewed code units (branch `trackp-p3a-code-20261116`, pushed to origin at D)

| | Commit | Content |
|---|---|---|
| A3-short delta | `3833d93e` | `--a3-short` in `exam_run.probes`/`trackp.py` (+tests); skips the descriptive 2k/8k A3 rows under option 3, records the skipped marker; flag-off byte-identical; refused without `--budget` |
| Runner round 1 | `7ae4d2ea` | probes-only runner in `trackp_p3a_guarded.py` + tests |
| Runner round 2 fixes | `7c9e8b08`/`5b7ad0cb` | boot-id gate, exact-HEAD pin, per-family provenance, unit-start verification, atomic sidecar, root/attempt-1 validation, executing-file identity, lease-log snapshot |
| Docs + delivery pin | `8a3d3eaf`/`9071f5b2`/`8662e359` | code-units record; mechanical `EXPECTED_PAPER_HEAD` pin child |

**Final delivery shape:** reviewed code commit **C = `5b7ad0cb7fedd083bad457968dc3dd3e920ac154`**, and its
mechanical delivery-pin child **D = `8662e35991659f7a661fb7ed6be4980791d302f3`** (D^ = C; `git diff C..D -- r1/`
is exactly the single canonical `EXPECTED_PAPER_HEAD = "5b7ad0cb…"` line). The host must check out **exactly
D** (detached or branch `trackp-p3a-code-20261116`), clean; C's own script refuses C; `9071f5b2`,
`7c9e8b08`, `3833d93e`, `8a3d3eaf` are refused. Branch pushed to `origin/trackp-p3a-code-20261116`
= D.

## 2. Independent review records (committed with this report)

| Unit | Review | Verdict |
|---|---|---|
| A3-short `3833d93e` | `reviews/TRACKP_P3A_A3SHORT_REVIEW_20261116.md` (sha `01334776…`) | **ACCEPTED** (0 BLOCKING/MAJOR; 5 MINOR) |
| Runner `7ae4d2ea` round 1 | `reviews/TRACKP_P3A_RUNNER_REVIEW_20261116.md` (sha `ba9dd81c…`) | **NOT ACCEPTED** (2 MAJOR) |
| Runner `9071f5b2` round 2 | `reviews/TRACKP_P3A_RUNNER_REVIEW_R2_20261116.md` (sha `b1501460…`) | **NOT ACCEPTED** (1 BLOCKING + 1 MAJOR) |
| Runner D `8662e359` round 3 | `reviews/TRACKP_P3A_RUNNER_REVIEW_R3_20261116.md` (sha `77f6e944…`) | **ACCEPTED** (0 BLOCKING/MAJOR; 3 MINOR non-blocking) |

Round-3 confirms: BLOCKING-1 fixed (immutable lease-log snapshot; unit starts never re-hash the live log;
host-shaped test), MAJOR-1 fixed (byte-exact delivery-pin child; crafted executable child refused; 12
executing files byte-identical to `HEAD:` blobs; accepted set exactly {C, docs-only child of C with identical
`r1/`, D}), all retained fixes intact, CPU tests reproduced (probes-only 45 passed/2 skipped; A3-short 8
passed; guarded 5/4 pre-existing macOS prctl; CLI 9 skipped). Residual MINORs are non-blocking (crafted-test
payload after a comment; `EXECUTING_FILES` not the full import graph; one record line wording).

## 3. Delivery attempt — BLOCKED by TASL-7 network outage

At `2026-11-16T22:30:07Z` the delivery session to TASL-7 failed at the transport layer:
`ssh: connect to host 100.106.74.51 port 22: Operation timed out` (capture
`reports/trackp_p3a_code_delivery_20261116/`: `ssh.log`, `ssh.exit` = 255, empty `delivery.txt`). Tailscale
control status showed the node `tasl-7.tail119748.ts.net` **active, relay "lax", tx 1248 / rx 0** — the
same failure signature as the 15 Nov TASL-7 outage (node advertising but not passing traffic). TASL-2 and
Ada were reachable in the same check (`portal_zhixu`, `experiment_zhixu` answered); the Mac's Tailscale is
up. **No host was touched; the TASL-7 checkout is still at `b9ad6f8f`/`trackp-20261026`; no command ran.**

## 4. Delivery procedure (to run when TASL-7 is reachable)

1. `git -C /home/dowling/r1_trackp/Agent_paper_B fetch origin trackp-p3a-code-20261116` (branch already on
   origin at D).
2. Confirm the checkout is clean and record HEAD/branch/`git status` before.
3. `git -C … checkout --detach 8662e35991659f7a661fb7ed6be4980791d302f3` (exactly D; branch or detached).
4. Verify: HEAD = D; clean; `git merge-base --is-ancestor b9ad6f8f HEAD` true; C ancestor; runner sha256
   `c045475b…`; child `r1/scripts/trackp.py` sha256 recorded; `git log -1` subject.
5. Record before/after capture and SHA256SUMS in `reports/`; then, only after Unit B run authorization,
   run `trackp_p3a_guarded.py --probes-only …` (the reviewed entry point; no bare probes, no e4/e0 re-runs).
6. Retry only while preserving the scene; a failure at any step is a STOP recorded as it stands.

## 5. Unit B remains gated

Even with D delivered, Unit B (probes-only EVIDENCE, qwen3.5-4b, new root, DRYRUN-first, 45-h projection)
requires a green preflight **and** the run authorization per the accepted plan; A6 is deferred under
`R1-TRACKP-A6-DEFER` (disclose in the P.3a report; separate reviewed A6 unit before any P.3b order change).
No Unit B command has been run; no GPU lease taken; nothing deleted.
