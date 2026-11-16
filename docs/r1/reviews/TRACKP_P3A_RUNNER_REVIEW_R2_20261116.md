# Independent review — Track P P.3a probes-only runner (round 2, fixed code units), 16 November 2026

**Status: NOT ACCEPTED — 1 BLOCKING + 1 MAJOR + 5 MINOR.** Fresh independent reviewer (round 2; no part in
drafting the plan, the readiness corrections, the round-1 runner or its fixes). **Read-only review.** No push,
no commit, no merge, no deletion, no GPU command, no model execution and no TASL-7 contact. The only workspace
change is this uncommitted review file; transient `/tmp` probe scripts were used for the adversarial checks below and deleted
afterwards. The worktree was clean before the review and afterwards holds only this untracked file (all git
inspection was read-only; the CPU tests were run from a temporary venv, not from the repository).

## 0. Canonical bytes and method

Worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackp-p3a-code-20261116`, branch
`trackp-p3a-code-20261116` (local, no remote contains it), clean.

| Object | sha / line count |
|---|---|
| HEAD (delivery-pin/docs child) | `9071f5b228a8e8311ccf7fc96c0e7587832dcdf2` (parent `7c9e8b08`, subject `docs(r1): P.3a runner review fixes record + delivery pin`) |
| Reviewed code commit | `7c9e8b0829450a70c462f2513873a56abcb8efdf` (`fix(r1): … review fixes (round 1)`) |
| Round-1 runner under review before | `7ae4d2ea5f55772a5f64507a4af5f042d5b0b061` |
| Round-1 docs child (fixed constant) | `8a3d3eaf048c7dd0a109719175dace72333bbd04` |
| A3-short delta (unchanged) | `3833d93e8f84f19bc20908b111136d9d4a5c0556` |
| Paper base pin (ancestor) | `b9ad6f8fe2e771732100f704accd7f2ce7cf20f0` (`merge-base --is-ancestor` = true) |
| `r1/scripts/trackp_p3a_guarded.py` | `ca90270a0bc471de7fc9f645a62c6372f71f2387ef79cd3aa578663dacb45f7d`, 1310 lines |
| `r1/tests/test_trackp_p3a_probes_only.py` | `d51fb7acd582121d084573f5e4b606909924be5f20eaf1fa401aab387f808cf3`, 1086 lines |
| `docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md` | `03854181bb100a3734d61e19a2965e7c0d067b0186fe06fc1ccbe0a2f11f5aed`, 337 lines |
| Child `r1/scripts/trackp.py` (unchanged) | `d2a30ec2c1b4c2b33387898a4ccafecff3cd7c584a8df68d586c011a07b09e63` |
| `r1/scripts/trackp_p3a_watchdog.py` / `r1/scripts/trackp_p3a_gate.py` | `98a4d0b6…f57858a8` / `234f470e…009f12cf7` |

Author and committer of both under-review commits: `Dowling Wong <wangdowling@gmail.com>` (§1).
Authority read-only: plan rev2 `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md` (`8fcb37cc…`, 131 lines,
accepted for Unit A only), accepted Unit A review `docs/r1/reviews/TRACKP_P3A_ATTEMPT2_REVIEW_R2_20261116.md`
(`94d4c1de…`, 444 lines), M13 order record `docs/r1/reviews/TRACKP_P3A_M13_ORDER_RECORD_20261116.md`
(`351611c5…`, 573 lines; equals `M13_ORDER_RECORD_SHA256`), amendment `trackp_p3a_amend_20261104.md`
(`cd867e95…`; equals `AUTHORIZATION_AMEND_SHA256`), attempt-1 inventory `SHA256SUMS` `5c35ef2b…` (243 files). The
latter four documents are on the ops branch, not in this code checkout (see MINOR-2).

Local CPU evidence (temporary venv `/tmp/p3a_test_venv`, Python 3.13.4 / pytest 9.2.0, macOS, no GPU no model):

```
py_compile exam_run.py trackp.py trackp_p3a_guarded.py test_trackp_p3a_a3_short.py test_trackp_p3a_probes_only.py  OK
pytest r1/tests/test_trackp_p3a_probes_only.py -q   ->  41 passed, 2 skipped   (skips are the two token-id golden
                                                        vectors, explicit reasons: no huggingface_hub / no kev)
pytest r1/tests/test_trackp_p3a_a3_short.py -q      ->  8 passed
pytest r1/tests/test_trackp_p3a_guarded.py -q       ->  5 passed, 4 failed    (pre-existing/macOS: preexec_fn
                                                        prctl(PR_SET_PDEATHSIG) unavailable; that test file is
                                                        unchanged by this work — no diff after 7ae4d2ea)
pytest r1/tests/test_trackp_cli.py -q               ->  9 skipped            (no transformers/tokenizers locally)
```

All §3 claims of the code-units record reproduce exactly. No new test needs a GPU, model, tokenizer or host.

## 1. Diff and commit scope (question 1) — PASS

- `git diff 7ae4d2ea..9071f5b2 --stat` touches only
  `r1/scripts/trackp_p3a_guarded.py` (+216/−18), `r1/tests/test_trackp_p3a_probes_only.py` (+586/−28) and the
  docs record (added in `8a3d3eaf`, rewritten in the pin child `9071f5b2`). `--name-status` = `A` record,
  `M` runner, `M` tests; nothing else (two commits `8a3d3eaf` docs-only + `7c9e8b08` fixes + `9071f5b2` pin/docs;
  no merge commits).
- `git diff 7ae4d2ea..HEAD -- r1/c3/train/exam_run.py r1/scripts/trackp.py` is **empty**; the A3-short delta
  `3833d93e` and its test file are untouched. `git diff b9ad6f8f..3833d93e --stat` is flag/tests-only (29/17/139
  lines in `exam_run.py`, `trackp.py`, new test) as recorded.
- `git diff 7c9e8b08..9071f5b2 -- r1/` is **exactly one line**: `EXPECTED_PAPER_HEAD`
  `7ae4d2ea… → 7c9e8b08…`; the only other change in the pin child is the docs record. `9071f5b2^` = `7c9e8b08`.
- Both commits: author = committer = `Dowling Wong <wangdowling@gmail.com>`; `9071f5b2` is not contained in any
  remote-tracking branch (local/unpushed). Branch points at HEAD.
- `b9ad6f8f` is an ancestor of HEAD; paper/watches/gate/child scripts are tracked (`git ls-files` check is folded
  into `verify_probes_only_pins`, runner lines 945–950).

## 2. Round-1 MAJOR-1 (attempt-1 boot id) — FIXED

- `EXPECTED_ATTEMPT1_BOOT_ID = "2c9bb104-cc3c-4c60-be67-c1c8f0287fe4"` (runner line 77) equals the attempt-1
  journal's `campaign_start.boot_id` in the exported inventory bytes (independently read).
- `build_attempt1_provenance` reads the attempt-1 journal `campaign_start.boot_id` (line 892) and refuses when it
  is missing/empty (lines 893–894); the provenance records both `attempt1_boot_id` and
  `expected_attempt1_boot_id` (line 900). `assert_attempt1_pins` pins `attempt1_boot_id` to the reviewed
  value (lines 908–919).
- Live preflight compares the *current* boot id from `R.tasl7_driver_snapshot()` with the pinned attempt-1 id
  (`verify_attempt1_boot_id`, runner lines 312–319, called line 978) and therefore STOPs before any root/marker/GPU
  work. A second, journal-bound comparison runs in `run_probes_only_campaign` (line 1190) **before**
  `args.root.mkdir()` (1213), marker begin (1228) and both units.
- `campaign_start` records `boot_id`, `expected_attempt1_boot_id`, `attempt1_boot_id` and
  `attempt1_boot_id_match` (lines 1162–1164).
- Tests are real, not bypass stubs: `test_verify_attempt1_boot_id_gate`, the provenance boot-id tests,
  `test_preflight_refuses_host_driver_disk_and_boot_id` (mismatch branch),
  `test_campaign_stops_before_root_if_the_boot_id_is_not_the_attempt1_boot` (asserts the root does not exist).

**No remaining MAJOR on MAJOR-1.**

## 3. Round-1 MAJOR-2 (exact code identity) — PIN CYCLE SOUND IN SHAPE, BUT ONE NEW BYPASS (MAJOR)

### 3.1 What was verified (the intended mechanism)

`EXPECTED_PAPER_HEAD = 7c9e8b08…` in the delivery-pin child `9071f5b2` names the reviewed *code* commit, whose
`r1/` tree differs from the pin child only by that assignment (§1). The acceptance rule in `verify_paper_head`
(lines 283–309) is: branch `trackp-p3a-code-20261116` or detached (`HEAD`); commit is one of (i) exactly
`EXPECTED_PAPER_HEAD` (`exact_reviewed_runner_commit`), (ii) the fixed docs child with byte-identical `r1/` tree,
(iii) a mechanically-shaped delivery-pin child (direct child of `EXPECTED_PAPER_HEAD`, only runner+record changed,
one added/one removed runner line that contains the assignment and the expected sha) — otherwise STOP; plus
`b9ad6f8f` ancestor and a clean tracked tree. Checked read-only against the real repository:

| HEAD | running script constants | result |
|---|---|---|
| `9071f5b2` (delivered pin child) | `EXPECTED_PAPER_HEAD = 7c9e8b08` | ACCEPTED `delivery_pin_child` (`_delivery_pin_child` = true) |
| `7c9e8b08` (its own script, constant `7ae4d2ea`) | `7ae4d2ea` | refused (self-pin cycle; see MINOR-2) |
| `8a3d3eaf` (round-1 docs child) | delivered constants | refused (MINOR-1: it is an *ancestor* of `7c9e8b08`, not a child) |
| `7ae4d2ea`, arbitrary descendants | delivered constants | refused |

`campaign_start` records the actual paper HEAD (`paper_head`), the accepted kind (`paper_identity`), the
executing-runner path+sha256 and the child `trackp.py` path+sha256 (lines 1166–1168, 1008–1010). The old-path
`git ls-files --error-unmatch` check is folded into the probes-only preflight (lines 945–950). `b9ad6f8f`
ancestor + clean checkout kept.

### 3.2 MAJOR (new) — a crafted one-line child of `7c9e8b08` is accepted as the "mechanical" pin child

`_delivery_pin_child` (lines 262–280) accepts any direct child of `EXPECTED_PAPER_HEAD` whose runner diff is
`len(added)==1 and len(removed)==1`, both lines *contain* `"EXPECTED_PAPER_HEAD = "`, and the added line *contains*
`EXPECTED_PAPER_HEAD`. It never checks that the added line is **only** the assignment. A one-line change such as

```
-EXPECTED_PAPER_HEAD = "7c9e8b08…"
+EXPECTED_PAPER_HEAD = "7c9e8b08…"; __import__("os").system("…")
```

has exactly one added and one removed line, both contain the assignment, the added line contains the expected sha
— and is accepted. **Reproduced** in a throwaway repo that mirrors the real layout (reviewed commit → genuine pin
child and crafted direct child of the same reviewed commit):

```
reviewed fix commit:                          ACCEPTED kind=exact_reviewed_runner_commit
genuine mechanical pin child (parent=fix):    ACCEPTED kind=delivery_pin_child
CRAFTED one-line child with arbitrary code:   ACCEPTED kind=delivery_pin_child   <-- bypass
```

The crafted commit's parent is the reviewed commit, branch check passes, tree is clean, and `campaign_start`
would record a `delivery_pin_child` — so unreviewed code on that line would run. Tag/alias/symlink misuse is not an additional route (the check uses the resolved commit sha and the
repository the imported `r1` package lives in); the crafted-commit shape and the untracked/assume-unchanged dirty
state (MINOR-3) are the gaps. This contradicts the record's
claim that the preflight accepts "precisely … this single mechanical delivery-pin child — and refuses every other
commit" (record lines 43–49, 103–106).

**Fix (exact).** Make the pin-child test byte-exact instead of substring-shaped, at runner lines 276–280: fetch
`git show EXPECTED_PAPER_HEAD:r1/scripts/trackp_p3a_guarded.py`, substitute the reviewed `EXPECTED_PAPER_HEAD`
assignment line with the canonical delivered line (assignment + expected sha + the same trailing comment), and
require the commit's runner blob to be byte-identical; equivalently require both diff lines to match
`^EXPECTED_PAPER_HEAD = "[0-9a-f]{40}"(\s*#.*)?$` with the added line's sha equal to `EXPECTED_PAPER_HEAD`. Add a
CPU test that builds a crafted child as above and asserts refusal (the current `_paper_git_repo` test only builds
the genuine pin child).

### 3.3 MINOR-1 — the "docs-only child" acceptance branch is dead and the record states otherwise

`EXPECTED_PAPER_HEAD_DOCS_CHILD = 8a3d3eaf…` (line 47) is the round-1 docs child of `7ae4d2ea`; after the fix
commit it is an **ancestor** of `EXPECTED_PAPER_HEAD`, and `git diff --quiet 7c9e8b08 8a3d3eaf -- r1/` is non-empty
(fix changed `r1/`), so `_r1_tree_equal` is false and the branch at line 297 can never accept anything. The record
(§2.2 lines 103–108 and §0 lines 43–49) says "its docs-only child when the `r1/` tree is byte-identical" is
accepted; no such commit is accepted. Practical consequence: committing this review / the acceptance record as a
docs-only child of `9071f5b2` makes the *branch HEAD* unacceptable — the run must check out `9071f5b2` detached or
reset the branch. **Fix:** either accept `{commit : r1/ tree of commit == r1/ tree of the delivered pin child and
EXPECTED_PAPER_HEAD is an ancestor}` (derive the delivered tree via the executing-runner blob, see MINOR-3) or drop
the docs-child sentence from the record and state that no docs-only child of the pin is accepted.

## 4. BLOCKING (new) — M4's unit-start re-verification compares the *global* GPU lease log that attempt 2 itself appends to, so the EVIDENCE unit can never start

`build_attempt1_provenance` hashes the attempt-1 lease log as `root.parent / "gpu_lease_log.jsonl"` (line 875).
On TASL-7 the only viable `--attempt1-root` is the live preserved root
`/home/dowling/r1_trackp/runs/p3a_operator_20261027`; its parent is the runs directory, i.e. exactly
`R.LEASE_LOG = ~/r1_trackp/runs/gpu_lease_log.jsonl` (`r1/c3/train/run.py:41`), the 111-line file whose sha
`695050…` is pinned in `EXPECTED_ATTEMPT1_LEASE_LOG_SHA256`. The child `trackp.py probes` keeps writing that same
global file (`r1/scripts/trackp.py:96-98` uses `cfg["runs_dir"] / "gpu_lease_log.jsonl"`, and
`r1/scripts/configs/trackp_portal.json:6` = `/home/dowling/r1_trackp/runs`); the code-units record states this
explicitly ("the global … the runner requires it there … The child keeps writing the global log", record lines
327–329).

`make_unit_start_verifier` re-runs `build_attempt1_provenance` before each unit and compares
`lease_log_sha256`, journal, paper commit and boot id (lines 1092–1097). So:

1. `campaign_start`: global log still equals the pinned 111 lines → accepted.
2. DRYRUN unit start: global log still unchanged → accepted; the DRYRUN child takes the GPU lease and appends
   `start`/`end` to the global log (and its mirror to the new root).
3. **EVIDENCE unit start:** the global log has two new lines → `lease_log_sha256` differs from the campaign value
   → `TrackPStop("attempt-1 provenance drift at EVIDENCE/qwen3.5-4b-base unit start: lease_log_sha256")`, before
   the EVIDENCE child starts. The authorized two-unit run therefore cannot complete; it STOPs after spending
   DRYRUN GPU time.

**Reproduced** with the real module on a synthetic tree laid out exactly as the host (attempt-1 root directly under
the runs directory, lease log = `<runs>/gpu_lease_log.jsonl`):

```
DRYRUN unit-start check: trackp_prompt/v1/kev_pointer_v1/history_first/kev@2074cc44…
global lease log grew to 4 lines
EVIDENCE unit-start STOP: attempt-1 provenance drift at EVIDENCE/qwen3.5-4b-base unit start: lease_log_sha256
```

The only alternative interpretation is to pass a read-only *exported copy* of the attempt-1 root: that works
(probe with a static lease log passes both unit-start checks) but is not what the record specifies, would make
`attempt1_provenance.root` a copy path rather than M13's "literal attempt-1 root `/home/dowling/…`"
(M13 record line 373), and is not even usable as-is: the exported inventory contains only
`EVIDENCE/<base>/final/saved/manifest.json` (the model files are not in the 2.9 MB export), and `attempt1_input`
re-hashes every recorded `final/saved` file, so it would STOP with "does not match its recorded sha256". So the
intended and only available attempt-1 root is the live one, and the M4 check as written breaks the run.

**Fix (exact).** Stop re-hashing the mutable global file. Two acceptable routes: (a) snapshot the attempt-1 lease
log at campaign start into the new root (copy bytes, verify sha256 == `EXPECTED_ATTEMPT1_LEASE_LOG_SHA256`,
record its path in `campaign_start`) and have the unit-start verifier compare that immutable snapshot (and the
journal) — the child keeps appending the global log for `trackp.py`'s accounting; or (b) pin the attempt-1 lease
*prefix* (111 lines / the reviewed bytes) and at unit start verify that the first N lines of the global log are
byte-identical while allowing appended attempt-2 lines. Also add the missing CPU test: attempt-1 root under the
runs directory, unit-1 start check, append a lease pair to the global log, unit-2 start check must pass (the
current tests keep the attempt-1 root outside the runs dir — `make_attempt1_root` puts it under `tmp_path` while
the global/mirror log is separate — which is why this defect is not caught).

## 5. Round-1 MINORs M1–M8 (question 4) — all addressed as claimed, one of them incorrectly (M4 → §4)

| M | Status | Evidence |
|---|---|---|
| **M1** golden token-stream test | **Fixed as claimed** | `test_golden_field_order_from_the_pinned_renderers` always runs (source-level Qwen `prefix`/`segments` + Kev `records` layout, compared to `FRAMES`); the two token-id vectors skip with explicit reasons (`-rs` output captured); limitation recorded in record §2.8/§6. |
| **M2** per-family `derived_template_id` | **Fixed** | campaign provenance has no scalar id, only `derived_template_ids_by_family` (lines 902–903, test asserts absence); per-unit sidecar sets `derived_template_id`/`derived_template_family` and requires equality with `attempt2_template.template_id` and the M13 §3.5 id (lines 1063–1070); sidecar test asserts the two families are distinct. |
| **M3** preflight internals untested | **Fixed** | `_PreflightStubs` + one test per branch: paper dirty/wrong HEAD/base-pin not ancestor, harness pin/dirt, e0/rule/config/freeze/registry, hostname/driver(kernel+empty)/disk, GPU census, lease, `*.active`, experiment process, marker-helper sha, untracked scripts, amendment present/matching, boot mismatch. Tests exercise the real functions, not the branch they are meant to catch. |
| **M4** unit-start re-verification | **Implemented, but introduces BLOCKING §4** | `make_unit_start_verifier` re-reads journal/lease/boot/paper, re-hashes the loaded files and recomputes the template before the child; `unit_start` records it (lines 578–596). Journal/input/template drift are tested; lease-log drift of the mutable global file is not. |
| **M5** SIGTERM/`kill -9` marker-left doc | **Fixed** | record §6 documents `finally` end, that SIGKILL/power-loss can leave `p3a.active` and no STOP, the next preflight's `*.active` STOP, and the manual `trackp-evidence end p3a` recovery. |
| **M6** atomic sidecar write | **Fixed** | `write_json_atomic` (same-dir temp + fsync + `os.replace`, lines 176–189) used for `runner_manifest.json` (line 726), re-read compared (727–728); test asserts `os.replace` and no temp file remains. |
| **M7** root/attempt-1 root arg contract | **Fixed** | `l-exists` (dangling symlink refused, line 1132), absolute attempt-1 root (1128–1129), absolute/absent/UTC/new-prefix/directly-under-runs-dir root (1130–1147), reuse/nesting refused (1148–1152); tests cover each. |
| **M8** record wording / symlink statement | **Fixed** | record says "commits under review / to be recorded after review", no pre-acceptance claim, names the forbidden checkouts; symlink statement matches the code (extra regular files refused; symlinks recorded, never followed; a symlinked recorded model file fails the hash comparison). |

New bugs introduced by the +216/−18 lines: §4 (BLOCKING) is a direct consequence of M4; §3.2 (MAJOR) is in the
new `_delivery_pin_child`. The rest is fail-closed and consistent.

### MINOR-2 — delivery wording does not name the commit the host must check out

Record §5.5 (lines 292–299) says the code commit is `7c9e8b08`, `EXPECTED_PAPER_HEAD` names it, and "the run
checks out the reviewed runner commit/pin child, clean/detached or on branch …", with the pin child's sha to be
"recorded after review". Checked: checking out `7c9e8b08` and running **its own** script is refused (its constant
is still `7ae4d2ea`; self-pin cycle), so the only runnable clean checkout is the pin child `9071f5b2`. The record
should state that explicitly (exact sha; detached or branch; `7c9e8b08` alone is refused) and that the branch is
local/unpushed and must be pushed/fetched or otherwise transferred to TASL-7; the host's paper checkout moves off
`trackp-20261026`/`b9ad6f8f` to this commit (no merge of `main`), with `b9ad6f8f` still the ancestor pin.

### MINOR-3 — the pin is on the checkout, not on the executing bytes

The preflight records the executing script's path and sha256 (`EXECUTING_RUNNER = Path(__file__).resolve()`, lines
49, 1008–1010) but never compares it with the committed blob at `HEAD:r1/scripts/trackp_p3a_guarded.py`, and
`R.git_commit` (r1/c3/train/run.py:249-256) runs `git status --porcelain --untracked-files=no`, so untracked files
and `assume-unchanged`/`skip-worktree` modifications are not "dirty". A modified copy run from `/tmp`, or a local
`assume-unchanged` edit, passes the preflight; only the journal's recorded path/sha reveals it afterwards. Harden:
compare `sha256_file(EXECUTING_RUNNER)` to the `git show HEAD:<path>` bytes and refuse otherwise (this also gives
the byte-exact pin-child check in §3.2 a clean source of truth).

### MINOR-4 — DRYRUN `--n-probe 8` deviates from the accepted-plan review's pinned 32, without recorded rationale

`probes_only_units` sets DRYRUN `--n-probe 8` (line 1039, record §2.6 lines 181–183); round-2 P-M7 pinned the
attempt-1-style DRYRUN argv with `--n-probe 32` (0.01 GPU-h) or a stated reading. Either use 32 or record the
deviation and the reading in the record before Unit B; the changed-path assertion itself is unaffected.

### MINOR-5 — `attempt1_boot_id_match` is a literal

`campaign_start` writes `"attempt1_boot_id_match": True` (line 1164) rather than the computed comparison of the
two recorded ids. It is logically guaranteed by the two preceding gates, but write it as
`pins["boot_id"] == provenance["attempt1_boot_id"]` so the journal field is self-consistent if reused.

## 6. Regression checks (question 5) — PASS except §4

- **Two-command sequence**: `probes_only_units` returns exactly DRYRUN `kev-0.8b` then EVIDENCE
  `qwen3.5-4b-base`, both `probes --head-form linear12 --budget --a3-short --n-probe {8,100} --load
  <attempt1>/EVIDENCE/<base>/final/saved`; the campaign re-checks the sequence (lines 1224–1227) and tests pin it.
  `trackp.py` refuses `--a3-short` without `--budget`/with `--tiny` (trackp.py:223-233, 300, 316).
- **Marker**: `evidence_marker` begins `begin p3a` before the first unit and ends in `finally` on success or STOP;
  journal `marker_begin`/`marker_end` record command/rc/stdout/stderr/UTC; failed begin STOPs before GPU work,
  failed end STOPs after; test asserts begin/end on an exception. No `trackp-evidence run` (no nested flock).
- **Budget**: `Attempt2Budget.used = 130745.3789889291 s + run mirror` (lines 447–485); 45 h = 162000 s,
  60 h cap recorded (includes attempt 1); `require_available(projection)` is called before every child
  (line 570) with projections 600/1800 s, and the in-flight lease is bounded against the limit; tests cover the
  exact arithmetic, the crossing projection, incomplete lease pairs and the 60-h cap.
- **Provenance hashing / template block**: journal+lease sha, STOP seconds, paper commit, boot id pinned;
  `attempt1_input` cross-checks `saved/manifest.json["files"]` against `final/manifest.json["model_files_sha256"]`,
  re-hashes every file and refuses extra regular files; the template block imports `PROMPT_VERSION`, checks the
  live transformers version through the child manifest and the installed Kev commit/model sha, and both units'
  ids must equal the M13 ids (lines 766–769, 1207–1212, 1060–1070); sidecar schema
  `trackp_p3a_unit_manifest/v1` with per-unit provenance and atomic write.
- **No bypass path**: every child runs through `run_unit` (budget → boot re-check → live pins → unit-start
  verify → watchdog/gate → lease accounting → manifest/label/boot verification → sidecar). The only spawns are the preflight's
  git/`uv pip freeze`/`ps`/`nvidia-smi` queries, the marker helper, and — per unit — the gate/watchdog pair; the old multi-base path (`verify_pins`, `run_base`, main without
  `--probes-only`) is byte-for-byte untouched and refuses probes-only flags. No direct `trackp.py probes`
  invocation exists outside `run_unit`, and `--probes-only` is the only route to the attempt-2 path.
- **CPU-only**: the whole new test suite runs on macOS with stubs; no host/GPU/model is contacted (the four
  failures in the pre-existing supervisor suite are the known macOS `preexec_fn`/prctl ones, in an untouched test
  file).

## 7. Can `9071f5b2` be recorded as the reviewed Unit B runner / delivered as the clean checkout? (question 6)

**Not as reviewed** — BLOCKING §4 and MAJOR §3.2 must be fixed and re-reviewed first (the fixes will produce a new
code commit plus a new delivery-pin child; record that new pin child's sha). For the record:

- `9071f5b2` **is** the mechanically correct delivery-pin child of the reviewed code commit `7c9e8b08`: its
  `r1/` tree differs from `7c9e8b08` by exactly the one `EXPECTED_PAPER_HEAD` assignment, it passes the intended
  preflight (`delivery_pin_child`), and it carries the updated code-units record. If §3.2/§4 were waived, the host
  would check out **exactly `9071f5b2`** (detached `HEAD` or on branch `trackp-p3a-code-20261116`), clean — and
  **not** `7c9e8b08` (its own preflight refuses it: its constant is `7ae4d2ea`), not `3833d93e` (predates the
  probes-only runner) and not `8a3d3eaf` (predates the fixes). The branch is local/unpushed, so delivery also
  requires transferring it (push/fetch/bundle) to TASL-7; the host paper checkout then moves off
  `trackp-20261026`/`b9ad6f8f` to this exact commit (no merge of `main`), with `b9ad6f8f` still the ancestor pin.
- **Unit B remains blocked independently of this code review**: it still needs the Unit A execution record (the
  inventory export `TRACKP_P3A_ATTEMPT1_INVENTORY_RESULT_20261116.md` and the accepted M13 record exist; the plan
  §1a/§1b/§1d/§1e items must be complete), the **A6 disposition** (not decided — A6 is unimplemented; option 3
  expects it, so either a separately reviewed A6 unit or a recorded deferral with the long-context-row omission
  disclosed in the P.3a report), and the delivery/run authorization per the accepted plan (§2, §5 conditions 1–6).
  The runner's preflight authorizes none of these; a green preflight is not a run authorization.

## 8. Limits

- CPU-only static/dynamic review; the live TASL-7 paths (nvidia-smi, driver snapshot, marker helper, GPU lease,
  real children) were not executed — they are TASL-7-only. Their internals are covered by the stubbed CPU tests.
- No TASL-7 access this round; host facts (boot id, lease-log bytes, driver) are taken from the reviewed inventory
  bytes and the accepted round-2 review, and the runner re-checks them live at run time.
- The two adversarial reproductions use throwaway copies of the logic in `/tmp` (real module imported read-only);
  they were removed after use. No tracked file was modified.
- E0 slopes/RPS/bootstrap bounds were not recomputed (not part of this code-unit review).
- The plan/M13/amendment/Unit-A-review documents are on the ops branch, not this checkout; their bytes were
  verified by sha256 against the pins recorded in the runner.

**Verdict: not accepted** — 1 BLOCKING (§4: M4 unit-start lease-log re-verification of the mutable global lease
log STOPs the EVIDENCE unit, so the run cannot complete), 1 MAJOR (§3.2: crafted one-line child of `7c9e8b08`
accepted as the mechanical pin child), 5 MINOR (§3.3, MINOR-2…MINOR-5). Round-1 MAJOR-1 is fixed; round-1 MAJOR-2
is fixed for the intended cases; all eight round-1 MINORs are addressed (M4 in a way that breaks the run).
