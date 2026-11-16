Reviewed base: 46bee4c78f118bb136ebaa98f4b5f68f172c1fd5

# HTCondor adapter: author answers HTC-Q1 (a) and HTC-Q2 (b) — independent review record (14 November 2026)

Branch `mac-htcondor-20261114`, on top of the accepted adapter (`ee6567a0`, record `68057612`). HTC-Q1 (a): walltime holds stay outside the repeated-timeout cap, recorded as `infrastructure_failure/htcondor_walltime_hold`. HTC-Q2 (b): a disk hold, code 34 subcode 104, is `infrastructure_failure/htcondor_disk_hold`. Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`02f11188`): changes requested (a disk text rule went beyond 34/104 and mapped filesystem quota or I/O errors to infrastructure failures).
- Round 2 (`46bee4c7`): **accepted**: disk holds by code 34/104 only; disk-mentioning texts stay `unclassified` (tested).

Accepted commit (round 2, last): 46bee4c78f118bb136ebaa98f4b5f68f172c1fd5

Notes, not blocking: a genuine disk-limit hold without code 34/104 is now `unclassified` (a human decides, by the standing rule); the pre-existing memory text rule can give a disk-policy hold that mentions memory the memory reason (still an infrastructure failure); the module's top docstring does not repeat that disk holds are recognised by code only. The earlier review record `HTCONDOR_ADAPTER_REVIEW_20261114.md` stays unchanged as history.

The round texts are reproduced unchanged below.

---

# Review: HTCondor adapter, author answers HTC-Q1 (a) and HTC-Q2 (b), round 1

Reviewed commit: 02f11188a4c1ea59cf2db0486b343ecded172734
Branch: `mac-htcondor-20261114` (worktree /tmp/pb/wt/htc). Base: 6805761214a8baf5d6ebdf3d9d6d0b451294b05e (review record on top of accepted ee6567a0315356551b514180933cb4a4f2f1475d).
Reviewer: independent (did not write the change). Read-only; scratch in /tmp/rev_htc2, removed at the end.

Author answers (14 Nov):
- HTC-Q1 (a): HTCondor walltime holds do not count toward the repeated-timeout cap; they are recorded separately as `infrastructure_failure`.
- HTC-Q2 (b): an HTCondor disk hold (code 34 subcode 104) is `infrastructure_failure/htcondor_disk_hold`.

## Summary of checks

| # | Check | Result |
|---|---|---|
| 1 | Change implements exactly the answers | HTC-Q1: yes. HTC-Q2: the code-34/104 table entry is exact. The commit also adds a text rule for codes 3, 26, 34-other and code-less holds; that goes further than the answer and is too loose (B1) |
| 2 | Disk text rule cannot misclassify | Order is correct: walltime, then memory, then disk. But unrelated holds that mention disk next to the words "limit", "quota" or "exceed" become `infrastructure_failure` (B1) |
| 3 | No other consumer needs `htcondor_disk_hold` | Confirmed: no allow-list anywhere |
| 4 | Tests pass and are not vacuous | 74 passed. Positive paths are guarded by mutation. No negative test for the new rule (part of B1) |
| 5 | Diff contains nothing else | Confirmed: 3 files, all in scope; `git diff --check` clean |

## 1. Does the change implement the answers?

**HTC-Q1 (a).** No code change was needed. The adapter never emits the runner's `timeout` reason; walltime holds stay `htcondor_walltime_hold` (codes 46/47, or walltime text). The handoff (§3, l. 59) and the `htc_events.py` module docstring now state the answer and drop the "open question" wording. On the harness side, `campaign_v2_diff.run_with_retries` (tgv2 717ad83, l. 118) counts toward the cap only when `outcome.reason == TIMEOUT_REASON`. Every other `infrastructure_failure` goes through `max_infra_reruns` to `infrastructure_failure_final`, so it is "recorded separately", as answered. The new test asserts `reason != "timeout"`. That check is weak on its own, but mutation M6 below shows it catches walltime being mapped to `timeout`.

**HTC-Q2 (b).** `HOLD_CODES[(34, 104)] = "htcondor_disk_hold"` is exact. The handoff table row for 34/104 moves from `unclassified` to `infrastructure_failure`, and the catch-all row is updated. The commit also adds a text rule (`classify_hold`, l. 131–134). The question and the answer both name only "code 34 subcode 104". The text rule follows the memory rule by analogy and is defensible in principle. As written, though, it breaks the standing rule (B1).

## 2. Probe of the disk text rule

The rule, after the walltime and memory checks and only for code 3, 26, 34-other or no code:

```python
if re.search(r"\bdisk\b", t) and ("exceed" in t or re.search(r"over (its |the )?(allocated )?disk", t)
                                  or ("disk" in t and ("limit" in t or "quota" in t))):
    return "htcondor_disk_hold"
```

The words "exceed", "limit" and "quota" may appear anywhere in the text; only "over … disk" is anchored to the word disk. The memory rule anchors "limit" (`over (cgroup )?memory limit`), so the disk rule is looser than the memory rule it copies.

Probe results (`classify_hold`, 47 texts):

Correct, as intended:
- 34/102 and 34/0 "gone over (cgroup) memory limit" → memory. 34/104 with any text, including "No space left on device", → disk (by code, as answered).
- "Job has gone over disk limit" (34/0, 34/103, no code), "SYSTEM_PERIODIC_HOLD: disk usage exceeded request" (26), "Job exceeded the disk request" (26) → disk.
- Walltime first: "exceeded its walltime; memory 3 GB; disk 2 GB" (26) → walltime. Codes 46/47 → walltime.
- Memory before disk: "memory usage exceeded request; disk 2 GB limit" (26) and "gone over memory limit; disk ok" (34/0) → memory.
- With a code other than 3/26/34, nothing changes: "Error writing to disk" (22/28), "(errno 122) Disk quota exceeded" (12/122), "No space left on device" (13/28), user holds (code 1, even with reason text "disk limit test"), IWD on `/data/disk1` (14/2) → unclassified. HTCondor writes the `Code N Subcode M` line in its hold events, so in real logs these are protected by their codes.
- Plain mentions stay unclassified with any code: "Error writing to disk" (no code, 34/0, 26), "disk I/O error" (no code, 3), "(errno 28) No space left on device" (no code), "No space left on device" (34/0), "scratch disk on execute node is full".

Wrong: an unrecognised hold becomes `infrastructure_failure`:

| Hold text | Code | Got | Should be |
|---|---|---|---|
| `STARTER failed to send file(s): error writing to /home/u/out: (errno 122) Disk quota exceeded` | none | `htcondor_disk_hold` | unclassified (this is strerror(EDQUOT), a user filesystem quota during output transfer, not a disk-request hold) |
| `Disk quota exceeded` | none | `htcondor_disk_hold` | unclassified |
| `via condor_hold (by user dow): disk limit test` | none | `htcondor_disk_hold` | unclassified (user hold) |
| `Error writing to disk: file size limit exceeded` | none | `htcondor_disk_hold` | unclassified (RLIMIT_FSIZE) |
| `disk I/O error; retry limit reached` | 26/0 | `htcondor_disk_hold` | unclassified |
| `local disk limit` | none | `htcondor_disk_hold` | unclassified |
| `Failed to pull docker image x: disk quota exceeded` | none | `htcondor_disk_hold` | arguable (image pull or unclassified) |

Wrong reason, still `infrastructure_failure`:

| Hold text | Code | Got |
|---|---|---|
| `Job used 3 GB memory above request; disk limit 10 GB` | 26/0 | `htcondor_disk_hold` (it is a memory hold; "limit" belongs to disk only by co-occurrence) |
| `SYSTEM_PERIODIC_HOLD: disk usage exceeded request; memory 2 GB` | 26/0 | `htcondor_memory_hold` (the memory rule's own looseness, which existed before this commit; it now meets the disk rule) |

Safe misses (unclassified, a human decides; acceptable): `PeriodicHold expression '(DiskUsage > RequestDisk)'` (3), `Job exceeded RequestDisk` (26), `Diskusage exceeded`, because `\bdisk\b` does not match inside `diskusage` or `requestdisk`. The memory rule behaves the same way.

## 3. Consumers of the reasons

- Paper `r1/scripts/htcondor/`: only `htc_events.py` names reasons (`HOLD_CODES`, `classify_hold`). `htc_submit.py`, `htc_units.py` and `htc_config.json` mention walltime only in the margin guard and have no reason list.
- Harness `r1-local-trackg-htc-20261114` (/tmp/pb/wt/htc_h, e5830af) and `r1-local-trackg-v2-20261114` (/tmp/pb/wt/tgv2, 717ad83): no `htcondor_*` reason appears anywhere. `outcome.py` has `OUTCOME_KINDS` (kinds, not reasons) and `infrastructure_log_patterns: []` (a pattern list, empty). `campaign_v2_diff.py` branches only on `reason == "timeout"`; it has no allow-list of other reasons.
- Docs: `HTCONDOR_ADAPTER_REVIEW_20261114.md` l. 93/98/229 still say "34/104 unclassified". That file is a historical review record and should stay as it is.

Nothing else needs `htcondor_disk_hold` added.

## 4. Tests

`cd /tmp/pb/wt/htc && PYTHONDONTWRITEBYTECODE=1 /tmp/trackg_venv/bin/python -m pytest -q -p no:cacheprovider r1/tests/htcondor/` → **74 passed** (67 + 6 parametrized + 1 new test).

Mutations, run on a `git archive` copy in scratch:

| Mutation | Result |
|---|---|
| M1 `htc_events.py` from 68057612 | 5 failed |
| M2 34/104 back to `unclassified` | 3 failed |
| M3 disk text rule disabled | 2 failed |
| M4 disk checked before memory | 1 failed |
| M5 disk checked before walltime | 2 failed |
| M6 code 46 → `timeout` | 2 failed |
| **M7 disk rule loosened to "any text containing the word disk"** | **74 passed** |

The positive paths and the order are guarded. Nothing asserts that a hold which only mentions disk stays unclassified, so M7, a direct breach of the standing rule, passes.

## 5. Diff scope

`git diff 68057612 02f11188` touches only the handoff (§3 table and cap sentence), `htc_events.py` (module docstring, `HOLD_CODES` 34/104, `classify_hold` docstring and disk rule) and `test_htc_adapter.py` (one expectation flipped, 5 cases and 1 test added). There are no other changes, `git diff --check` is clean, and the worktree is clean.

## Findings

### B1 — BLOCKING: the disk text rule maps unrecognised holds to `infrastructure_failure`

Once the word "disk" appears, the words "exceed", "limit" and "quota" are accepted anywhere in the hold text. The result is that `(errno 122) Disk quota exceeded` (no code), a code-less user hold "…disk limit test", "Error writing to disk: file size limit exceeded" and "disk I/O error; retry limit reached" (26) all become `infrastructure_failure/htcondor_disk_hold`. The standing rule says they must stay unclassified for a human. The rule also gives a memory hold that mentions a disk limit the disk reason. The code-less path is a supported path: the commit's own test `"Job went over disk quota"` has no code. The rule also extends HTC-Q2 beyond the code 34/104 that the author ruled on. No test catches a loosened rule (M7).

Suggested fix, either option:
- (a) Smallest change, exactly the answer: drop the text rule and keep only `HOLD_CODES[(34, 104)]`, so disk text without that code stays unclassified until the pool report (handoff §6 item 5) shows real texts. Revert the parametrized cases for code 3 and code-less disk text to `unclassified`.
- (b) Keep a text rule, but anchor every keyword to disk, e.g.
  `re.search(r"over (its |the )?(allocated |requested )?disk( limit| quota| request)?\b|exceed\w* (its |the )?(allocated |requested )?disk\b|\bdisk (usage|space) (exceed|over|above)|\bdisk (limit|quota|request) exceed", t)`
  and add `and "errno" not in t`, so that strerror texts such as "Disk quota exceeded" stay unclassified. Optionally require `code is not None` for the text path. Then update the handoff row text ("text naming disk with 'exceed', 'over … disk', 'limit' or 'quota'") to match.

For either option, add negative tests that must stay `unclassified`: `"Error writing to disk"`, `"disk I/O error; retry limit reached. Code 26 Subcode 0"`, `"(errno 122) Disk quota exceeded"`, `"via condor_hold (by user x): disk limit test"`, `"Error writing to disk: file size limit exceeded"`. With option (b), also add `"Job used 3 GB memory above request; disk limit 10 GB. Code 26 Subcode 0"`, which must not be `htcondor_disk_hold`. Check that mutation M7 then fails.

### N1 — NON-BLOCKING: stale test count in the handoff

Handoff §7 still says "paper `r1/tests/htcondor` 67 passed"; it is now 74 (more after the B1 fix). Fix: update the count in the same change as B1.

### N2 — NON-BLOCKING: the memory rule's looseness can take a disk hold

`"disk usage exceeded request; memory 2 GB"` (26) gives `htcondor_memory_hold`, because the memory rule accepts "memory" plus "exceed" anywhere. Both are `infrastructure_failure`, so only the reason is wrong. The looseness existed before this commit and was accepted. Suggested fix (optional): anchor memory the same way, e.g. `memory (usage )?exceed|exceed\w* (its |the )?(allocated |requested )?memory`, and add one test.

### N3 — NON-BLOCKING: default PeriodicHold texts stay unclassified

`(DiskUsage > RequestDisk)` and "exceeded RequestDisk" are not recognised, and neither are the memory equivalents. This is safe under the standing rule. Suggested fix: none needed now; revisit once the pool report lists the real texts (handoff §6 item 5).

## Verdict

HTC-Q1 (a) is implemented correctly and completely. HTC-Q2 (b) is correct for code 34/104. The added text rule breaks the "unrecognised holds stay unclassified" rule in probed cases and has no negative tests.

Verdict: changes requested

---

# Review: HTCondor adapter, author answers HTC-Q1 (a) and HTC-Q2 (b), round 2

Reviewed commit: 46bee4c78f118bb136ebaa98f4b5f68f172c1fd5
Branch: `mac-htcondor-20261114` (worktree /tmp/pb/wt/htc). Parent: 02f11188a4c1ea59cf2db0486b343ecded172734 (round 1, changes requested; see REVIEW_HTC_Q1Q2_round1.md).
Reviewer: independent (did not write the change). Read-only; scratch in /tmp/rev_htc2, removed at the end.

## Round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| B1 (BLOCKING): disk text rule turns unrecognised holds into `infrastructure_failure` | **resolved** | Text rule removed. A disk hold is now recognised only by `HOLD_CODES[(34, 104)]`, which is option (a) of the round-1 fix and exactly the author's HTC-Q2 (b). Negative tests added; the loosening mutation now fails (below) |
| N1 (NON-BLOCKING): stale test count in handoff §7 | **resolved** | §7 now reads "67 passed at the accepted adapter, 79 after the 14 Nov HTC-Q1/Q2 change". Both counts check out: 74 − 7 round-1 additions = 67, and 79 is the measured count now |
| N2 (NON-BLOCKING): memory rule looseness | open (optional, pre-existing) | See N2 below |
| N3 (NON-BLOCKING): default PeriodicHold texts unclassified | open (no action needed) | Now also has an explicit test: `DiskUsage > RequestDisk. Code 3` → `unclassified` |

## Diff `git diff 02f11188 46bee4c7`

There are 3 files, all in scope, and `git diff --check` is clean:
- `htc_events.py`: the 4-line disk text rule is deleted, and the `classify_hold` docstring now says that a disk hold is recognised only by 34/104 and that disk-mentioning text stays `unclassified`. `HOLD_CODES` and the module docstring are unchanged and still accurate ("a hold for memory, disk or walltime … `htcondor_disk_hold`").
- Handoff: the §3 table row is now "hold code 34 subcode 104 (disk) only … a text that merely mentions disk stays `unclassified`", and the §7 count is updated.
- Tests: the two round-1 positive text cases (code 3 "disk usage exceeded", code-less "went over disk quota") are replaced by 7 cases that expect `unclassified`. These are errno 122 quota, a user hold "disk limit test", "file size limit exceeded", "disk I/O error; retry limit reached" with code 26, "went over disk quota", `DiskUsage > RequestDisk` with code 3, and "memory above request; disk limit 10 GB" with code 26. The positive cases for 34/104 (two texts) and for walltime before memory, and the HTC-Q1/Q2 end-to-end test from round 1, are kept.

The worktree is clean at 46bee4c7. The harness branches are unchanged (htc_h e5830af, tgv2 717ad83), so the round-1 consumer check still holds: no allow-list of `htcondor_*` reasons exists, and the cap counts only `reason == "timeout"`.

## Tests

`cd /tmp/pb/wt/htc && PYTHONDONTWRITEBYTECODE=1 /tmp/trackg_venv/bin/python -m pytest -q -p no:cacheprovider r1/tests/htcondor/` → **79 passed**.

Mutations, run on a `git archive` copy of 46bee4c7 in scratch:

| Mutation | Result |
|---|---|
| M1 `htc_events.py` from 02f11188 (the round-1 rule back) | 6 failed |
| M1b `htc_events.py` from 68057612 (34/104 unclassified) | 3 failed |
| **M7 any text containing the word disk → `htcondor_disk_hold` (the round-1 loosening mutation)** | **6 failed** (round 1: 74 passed) |
| M7b substring "disk" → disk hold | 7 failed |
| M7c "disk" + "quota" | 2 failed |
| M7d "disk" + "exceed" | 2 failed |
| M7e "disk" + "limit" | 4 failed |
| M2 34/104 → `unclassified` | 3 failed |
| M6 code 46 → `timeout` (HTC-Q1) | 2 failed |
| M8 memory rule loosened to "memory" anywhere | 1 failed |

Every way of reintroducing a disk text match is caught, including each single-keyword variant. The tests are not vacuous.

## Probe (round-1 list, re-run against 46bee4c7)

- Now `unclassified`, as required: the errno 122 "Disk quota exceeded" texts (with and without the STARTER prefix), the code-less user hold "disk limit test", "Error writing to disk: file size limit exceeded", "disk I/O error; retry limit reached" (26), "local disk limit", "memory above request; disk limit 10 GB" (26), "Error writing to disk" (22/28), "disk I/O error".
- Also `unclassified` now: genuine disk texts without 34/104, such as "disk usage exceeded request" (26) and "Job has gone over disk limit" (34/0). This follows from the author's answer, which named only 34/104, and is safe under the standing rule; a human decides.
- Still correct: 34/104 with any text → `htcondor_disk_hold`. 34/102 and the code-less "gone over memory limit" → memory. Walltime text with memory and disk mentions (26) → walltime. Code 46 → walltime.
- "Failed to pull docker image x: disk quota exceeded" (no code) → `htcondor_image_pull`. This comes from the pre-existing pull-wording rule and is unrelated to this change; real image failures carry code 35.

## Findings

No BLOCKING findings.

### N2 — NON-BLOCKING (carried over, pre-existing): the memory rule can take a disk policy hold

`"SYSTEM_PERIODIC_HOLD: disk usage exceeded request; memory 2 GB. Code 26 Subcode 0"` → `htcondor_memory_hold`, because the memory rule accepts "memory" plus "exceed" anywhere in the text. Both reasons are `infrastructure_failure`, so only the reason is wrong. Now that the disk text rule is gone, the same hold without the word "memory" is `unclassified`. The behaviour predates this change and was accepted in the adapter review. Suggested fix (optional, later): anchor the memory text, e.g. `memory (usage )?exceed|exceed\w* (its |the )?(allocated |requested )?memory`, together with the pool report's real texts (handoff §6 item 5), and add this text as a test.

### N4 — NON-BLOCKING: the module docstring is silent on code-only disk recognition

The top-of-module docstring of `htc_events.py` lists `htcondor_disk_hold` but does not say that it is recognised only by code. The `classify_hold` docstring and the handoff do say so, so this is cosmetic. Suggested fix: optionally add "(code 34/104 only)" next to `htcondor_disk_hold` the next time the file is touched.

## Verdict

HTC-Q1 (a) and HTC-Q2 (b) are implemented exactly: walltime holds stay outside the timeout cap, and a disk hold is `infrastructure_failure/htcondor_disk_hold` only for code 34 subcode 104. Disk-mentioning texts stay `unclassified`, the tests guard both directions, and the diff has nothing else.

Verdict: accepted
Accepted commit: 46bee4c78f118bb136ebaa98f4b5f68f172c1fd5
