Reviewed base: 37ef68f3f19c57fc720588e6ac7e3b23e2cfa4f3

# HTCondor adapter: container universe — independent review record (14 November 2026)

Branch `mac-htcondor-container-20261114`, from `mac-htcondor-20261114` @ `46bee4c7` (HTC-Q1/Q2 accepted). The manifest gains `runtime: "docker" | "container"`, `container_image` (`docker://…` or an absolute SIF path) and `container_transfer`; a SIF on `/work` or `/ceph` is read in place by local jobs (`transfer_container = false`); a remote (NEMO2) job transfers it only with an explicit `container_transfer: true` under its own cap `max_container_transfer_mb` (8000, `proposed:` until the cluster agent's S5 measurement); ordinary inputs keep the 100 MB cap; `input_transfer_s` from the 040 events. Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`1b08681f`): **accepted**, no blocking findings, ten non-blocking notes.
- Round 2 (`37ef68f3`, follow-ups for N1, N3, N5–N9): **accepted**, no regression; four non-blocking notes (R1–R4).

Accepted commit (round 2, last): 37ef68f3f19c57fc720588e6ac7e3b23e2cfa4f3

Open, not blocking: the reference test covers only the four S2 `docker://` JDLs, which have no review record of their own; S4/S5 references do not exist yet, so the SIF and `transfer_container` lines have no outside reference (re-run the test when reviewed S2/S4/S5 files arrive). R1 (duplicate-SIF check compares path strings, not resolved paths), R2 (disk boundary not tested tightly), R3 (disk check covers the SIF alone, a lower bound), R4 (the S2 file time 08:53 UTC predates the cluster report's S1 time 10:51 CET; unexplained), N2 (argument-syntax leniency in the test normaliser), N4 (symlink check on the last path component only), N10 (S2 manifests not committed as JSON).

The round texts are reproduced unchanged below.

---

# Independent review: HTCondor adapter, container universe, round 1

Reviewed commit: 1b08681f920ba2ccb8bd065c42f6ae142a869189

Branch `mac-htcondor-container-20261114`, one commit on `46bee4c78f118bb136ebaa98f4b5f68f172c1fd5` (the accepted adapter with HTC-Q1/Q2; its review record is `f2a46da1` on `mac-htcondor-20261114`). Reviewer: an independent reviewer (Claude, AI-assisted), 14 Nov 2026. I did not write this code. I made no change to any repo or worktree; the worktree is still clean. Scratch work was under `/tmp/rev_htcc/`, and it has been removed.

## 1. What I ran

| Check | Result |
|---|---|
| `pytest -q r1/tests/htcondor/` (`/tmp/trackg_venv`) | **91 passed** (base `46bee4c7`: 79 passed; 12 new tests in `test_htc_container.py`; `test_htc_adapter.py` is unchanged) |
| `git diff --name-status 46bee4c7..1b08681f` | 3 scripts/config modified; report, test, and `data/s2/` (README, 4 JDL, SHA256SUMS) added. Nothing else touched |
| Commit metadata | author and committer `Dowling Wong <wangdowling@gmail.com>`, with the `Co-Authored-By` and `Claude-Session` trailers |
| S2 copies vs the cluster agent's tree | `cmp` identical for all four; `sha256sum -c SHA256SUMS` OK; the hashes match the source files |
| Docker runtime, differential | 256 docker manifests (placement × gpus × accounting_group × executable_in_image × resume_dir × cloud_site × etp_ceph × arguments with spaces and quotes), validated and rendered with the base and the new `htc_submit.py`: **256/256 identical** outcomes (same JDL bytes, same input totals, same refusals) |
| CLI | `htc_submit.py S2L.json --dry-run` (no condor_submit on PATH) renders the S2L JDL and prints `container={"bytes": null, "kind": "docker", "transfer": false}`; rc 0 |
| Mutation of the equivalence test | 16 mutations (§4); every semantic mutation is caught |
| Guard probes | 28 SIF/docker:// cases (§5) |

## 2. The implementation against the unit

| Unit clause | Implementation | Verdict |
|---|---|---|
| manifest `runtime: "docker" \| "container"` | optional, default `docker`; `RUNTIME_KEYS` makes `image` required for docker and refused for container, `container_image` the reverse; any other value refused | ✔ |
| `container_image`: `docker://…` or SIF path | `docker://` + the existing `IMAGE` regex, or an absolute `*.sif` path in `PATH_TEXT` with no `.`/`..` parts; anything else refused (`oras://`, relative, `.img`, null) | ✔ |
| image handled apart from ordinary inputs | `container_plan()` runs after the 100 MB total; the SIF is never added to `total_input_bytes` and never put into `transfer_input_files` | ✔ |
| SIF on shared FS not transferred | local job + SIF under `/work/` or `/ceph/` → `transfer_container = false` | ✔ |
| transfer (NEMO2) only with explicit `container_transfer: true` | remote + SIF without `true` refused (also with `false`); `true` requires a regular, non-symlink file here and ≤ `max_container_transfer_mb`; no `transfer_container` line, so HTCondor transfers it | ✔ |
| separate image cap, `proposed:`, pending S5 | `max_container_transfer_mb` = 8000, status `proposed: … S5 …`, required config key, checked as a nonnegative finite number, listed in `proposed_config` | ✔ |
| record transfer time | `job_summary`/`queue_rows` gain `input_transfer_s` (040 input pairs) | ✔ (see N6) |
| ordinary inputs still ≤ 100 MB | unchanged code path; test with a 101 MB input plus a transferred SIF still refuses | ✔ |
| reference test against reviewed S2/S4/S5 JDLs | only the four S2 JDLs exist, unreviewed, all `docker://`; S4/S5 absent. Disclosed in the report and README | partly met, by necessity (N1) |
| docker runtime unchanged | differential 256/256 identical; existing tests unchanged and passing. The only visible change for docker manifests is the refusal text (`manifest keys for runtime docker: …`); no consumer matches on it. An explicit `"runtime": "docker"` is now accepted (it was an unknown key before) | ✔ |

## 3. HTCondor semantics (from my knowledge of the manual; uncertainties stated)

- **`universe = container`.** Correct. The pool runs 25.0.12, and the cluster agent's read-only `condor_submit -dry-run` of a container-universe JDL returned rc 0 (`HTCONDOR_CHAIN_20261114.md` S1). Confident.
- **`container_image = docker://…`.** Correct, and nothing else is required in the submit file: the image is not transferred; the execute point pulls it (Apptainer converts it to a SIF, or Docker runs it where the slot has Docker), and condor_submit adds the runtime-matching requirements itself. Uncertain: (a) on ETP-local slots with both `HasDocker` and `HasSingularity` (237 of 245), which runtime HTCondor picks for a `docker://` image. I believe it can use either, so S2L may not exercise Apptainer. (b) NEMO2 workers need outbound registry access for the pull. (c) The conversion uses scratch disk or a cache. (d) Apptainer pull failures may not carry hold code 35 (`InvalidDockerImage`); they then classify as `unclassified`, which fails closed.
- **`container_image = /path/x.sif`.** HTCondor transfers a local image file by default (`transfer_container` defaults to true; `should_transfer_files = YES` is rendered). `transfer_container = false` makes the execute point use the path in place, which is the right setting for a SIF on `/work`/`/ceph` that local nodes mount. Confident on the semantics. The transferred image is read on the access point, so the path must exist on the host running condor_submit; the adapter checks "here", which is that host only when the adapter runs on deepthought.
- **040 texts.** `"Started transferring input files"` / `"Finished transferring input files"` match HTCondor's `FileTransferEvent` strings, and they appear on the header line, which is what `text[0]` holds. The queue step is `"Entered queue to transfer input files"`; it is correctly not counted, and the output pair is ignored. Confident on the strings. **Uncertain:** whether, in 25.0, the container image is moved inside that input-transfer window rather than by a separate mechanism or cache. The report states it as fact (N6).

## 4. The equivalence test

The normaliser drops comments and blank lines, lowercases keys, maps four `Request*` aliases, splits `arguments` on whitespace after stripping outer double quotes, and sorts `&&` clauses of `requirements` with outer parentheses stripped. Comparison is whole-dict equality, so an extra or missing command fails. Values are compared case-sensitively.

Mutations run in scratch (equivalence-test result shown; reference mutations also trip the SHA256 test):

| Mutation | Caught |
|---|---|
| reference: `=?=` → `==`; `RequestMemory` 4000 → 4096; drop `+RemoteJob = True`; CloudSite string; add `transfer_container = false`; extra argument; `ON_EXIT` → `ON_EXIT_OR_EVICT`; image `:latest`; `True` → `true` | all 9 caught |
| renderer: `universe = docker`; `transfer_container = false` always; never; on a transferred SIF; `=?=` → `==` in device clause; drop `+RemoteJob` | all 6 caught (SIF cases by the self-written string tests, docker:// cases by the S2 references) |
| renderer: drop single-quote wrapping of arguments with spaces | not caught by this file (S2 arguments have no spaces; `test_htc_adapter.py` covers argument syntax) |

The alias equivalence (`RequestCPUs` = `request_cpus` and so on) is right to my knowledge (condor_submit looks up the attribute name as an alternate key). The clause sort is sound for `&&`. Duplicate keys collapse to the last value, which matches condor_submit. One real leniency, demonstrated (N2): new-syntax `arguments = "'a b'"` (one argument `a b`) and old-syntax `arguments = 'a b'` (two arguments with literal quotes) normalise to the same list. The S2 references are not affected.

## 5. Guards (probes)

| Case | Result |
|---|---|
| local, `/work/…`, `/ceph/srv/…` (no flag or `false`) | accepted, `transfer_container = false` |
| local `/home/…`, `/tmp/…`, `/workx/…`, `//work/…` without transfer | refused |
| `/work/../etc/r.sif`, `/work/./r.sif`, relative, `.img`, directory named like the path | refused |
| local with `container_transfer: true`; flag `1` or `"yes"` | refused |
| remote without flag (also `/ceph/srv` with `etp_ceph: true`) | refused |
| remote + flag: regular file ≤ cap accepted, `bytes` reported, `total_input_bytes` 0; cap exact accepted; over cap refused; missing refused; **leaf** symlink refused | ✔ |
| remote + flag: SIF reached through a **symlinked parent directory** | accepted (N4) |
| remote + flag, SIF also listed in `transfer_input_files` | accepted; counted toward 100 MB and transferred twice (N5) |
| remote + flag, `disk_kb` 1 with a 3 MB SIF | accepted (N3) |
| `docker://` with `container_transfer` (`true` or `false`); with runtime docker | refused |
| 100 MB cap with a transferred SIF | still enforced; the SIF is never counted |

## 6. `input_transfer_s` and consumers

Pairing: a "Started" opens and a later "Finished" closes. A second "Started" before a "Finished" restarts the window, so an interrupted attempt is dropped. A "Finished" without a "Started" is ignored. Pairs are summed over attempts, and the value is empty when there is no complete pair. Probes: two attempts → 170 s (test); two starts and one finish → 30; finish only → `""`; queued-only window not counted; zero-length pair → `0`; output pair only → `""`; interrupted attempt then a full one → only the full one. Correct.

Consumers: the column is appended last in `COLUMNS`. `queue_rows` and `write_tsv` (DictWriter with header, file opened `"w"`) handle it. No in-repo code reads the TSV or matches the header by position. The only test on the header compares it with `list(ev.COLUMNS)`. Nothing in the repo breaks. Outside: the format now differs from runbook §4.2 (13 columns) and from the hand-off (N7).

## 7. The report

`docs/r1/reports/HTCONDOR_CONTAINER_20261114.md` is accurate on the manifest rules, the guards, the cap, the 91 (79 + 12) count, and the 4-of-4 S2 equivalence. **It discloses** that no S4/S5 files existed and that the S2 files had no review record (§3; also `data/s2/README.md`). Two statements need softening or adding (N1, N6), and the README timestamp is doubtful (N8).

## 8. Findings

No BLOCKING findings.

**N1 (NON-BLOCKING). The reference clause of the unit is only partly met.** The references are the four S2 JDLs, unreviewed, all `docker://`. So `transfer_container = false` and the transferred-SIF rendering have no external reference, only the author's own string assertions. This is disclosed and cannot be fixed by the Mac agent today. *Fix:* in report §3, add one sentence: "the SIF lines (`transfer_container`) have no external reference yet". When the cluster agent commits the reviewed S2/S4/S5 files, replace the copies, add S4/S5 manifests to `S2_CASES`, regenerate `SHA256SUMS`, and re-run. Acceptance of this commit does not stand in for the review gate on the S2 JDLs.

**N2 (NON-BLOCKING). The arguments normaliser is lenient for arguments with spaces or quotes.** `jdl_commands('arguments = "\'a b\'"')` equals `jdl_commands("arguments = 'a b'")` (1 vs 2 arguments in HTCondor). *Fix:* parse new syntax properly: outer `"…"`, single-quote grouping, doubled `''` and `""`. Old syntax (no outer double quotes) splits on whitespace with quotes literal. Or accept the old/new difference only when the value has no whitespace or quotes.

**N3 (NON-BLOCKING, before S5). `request_disk` is not checked against the transferred SIF.** A transferred image lands in the job's scratch directory (to my knowledge), so an 8 GB SIF with `disk_kb` 5,000,000 passes validation and invites a disk hold (34/104, now `infrastructure_failure`). *Fix:* when `transfer` is true, require `disk_kb * 1024 ≥ SIF bytes + total_input_bytes` (plus a margin), or at least print a warning in the dry-run line. Mention the `docker://` conversion disk in the report.

**N4 (NON-BLOCKING). The symlink check covers only the last path component.** `<dir>/ldir/r2.sif` with `ldir` a symlink is accepted for transfer. The size is still right because `stat` follows links, and the base adapter treats inputs the same way. The no-transfer SIF on `/work`/`/ceph` is not checked at all (existence, symlink); that is defensible off the submit host but not stated. *Fix:* for the transfer case use `os.path.realpath(img) == img`. In the report, state that a shared-FS SIF is not checked locally (or check it when `/work` is visible).

**N5 (NON-BLOCKING). The SIF may also appear in `transfer_input_files`.** It is then counted toward 100 MB and transferred twice. *Fix:* refuse a `transfer_input_files` entry equal to `container_image`.

**N6 (NON-BLOCKING). Stated facts about transfer time.** Report §2 says "S5's measured image transfer time is this column for the S5 job". That presumes the 25.0 image transfer lies inside the 040 input window (unverified). The column also includes the ordinary inputs, and interrupted attempts are dropped. *Fix:* reword as "expected to include the image; S5 confirms, e.g. by comparing with the same job on a `docker://` image". Optionally expose `input_transfer_pairs` and `input_transfer_incomplete` in `job_summary`.

**N7 (NON-BLOCKING). Format and hand-off drift.** The queue-time TSV now has 14 columns, against runbook §4.2's 13. `HTCONDOR_ADAPTER_HANDOFF_20261114.md` §2/§3 still says the adapter renders `universe = docker` and lists the old row. Last night's 13-column `queue_times.tsv` files will not concatenate positionally with new ones. *Fix:* add a line to the hand-off (or point it to the new report) noting the container runtime and the 14th column. Consumers should read by header.

**N8 (NON-BLOCKING). README timestamp.** `data/s2/README.md` says the S2 files are "dated 14 Nov 09:53 CET". The cluster report has S1 at 10:51 CET and S2 "not started" at that time, so 09:53 CET looks like another clock or zone (09:53 UTC = 10:53 CET?). *Fix:* state the source and zone, or drop the time.

**N9 (NON-BLOCKING). Choices beyond the unit's text, to be confirmed by the author.** (a) `/home` is not treated as shared, though the docstring says local nodes see it. (b) `container_transfer: true` is refused for local jobs, so a local job cannot use a SIF outside `/work`/`/ceph`. (c) Remote + `etp_ceph` with a SIF on `/ceph/srv` is refused (already asked in §5). All three are conservative and fail closed. *Fix:* list (a) and (b) beside (c) in report §5.

**N10 (NON-BLOCKING). S2 manifests exist only inside the test.** *Fix:* commit them as `data/s2/*.json`, so the cluster agent can render them with the CLI and compare with what it submits.

Verdict: accepted
Accepted commit: 1b08681f920ba2ccb8bd065c42f6ae142a869189


---

# Independent review: HTCondor adapter, container universe, round 2

Reviewed commit: 37ef68f3f19c57fc720588e6ac7e3b23e2cfa4f3

This is one follow-up commit on `1b08681f920ba2ccb8bd065c42f6ae142a869189`, which was accepted in round 1 (`REVIEW_HTC_CONTAINER_round1.md`). Reviewer: the same independent reviewer (Claude, AI-assisted), 14 Nov 2026. I made no change to any repo or worktree; the worktree is clean. Scratch work was under `/tmp/rev_htcc/`, and it has been removed.

## 1. What I ran

| Check | Result |
|---|---|
| `pytest -q r1/tests/htcondor/` | **91 passed** (same count; the new cases were added to an existing test function) |
| `git diff --name-status 1b08681f..37ef68f3` | `htc_submit.py`, `test_htc_container.py`, `data/s2/README.md`, the container report and the hand-off are modified. Config, `htc_events.py` and the reference JDLs are untouched (`SHA256SUMS` still OK) |
| Commit metadata | author and committer `Dowling Wong <wangdowling@gmail.com>`, with the `Co-Authored-By` and `Claude-Session` trailers |
| Docker runtime, differential vs base `46bee4c7` | 256 manifests: **256/256 identical** (validation outcome, input total, JDL bytes) |
| Container differential vs round-1 `1b08681f` | 11 cases. Only the two intended guards change an outcome (disk 1 KiB short; SIF listed in `transfer_input_files`). Everything else is identical |
| Mutations of the new guards | removing the N5 check → 1 failure; removing the N3 check → 1 failure; `×1024` → `×1000`, and `<` → `<=`, both go uncaught (see R2) |

## 2. Round-1 notes

| Note | Change | Verdict |
|---|---|---|
| N3 request_disk | a transferred SIF needs `disk_kb × 1024 ≥ size`. The unit is right (`request_disk` defaults to KiB). An exact fit is accepted (2930 KiB for 3,000,000 B), and 2929 is refused | ✔ resolved as stated. Ordinary inputs are not added to the SIF (R3) |
| N5 SIF also an input | refused when `container_image` appears verbatim in `transfer_input_files` | ✔ for the same spelling. Other spellings pass (R1) |
| N6 wording | report §2: "expected to fall inside the input-transfer window … S5 has to confirm that on HTCondor 25.0"; notes 14 columns vs runbook §4.2 | ✔ |
| N7 hand-off | rendering paragraph now names `runtime: "container"` and points to the container report | ✔ (the 14th column is documented in the container report, which the hand-off now points to) |
| N8 README time | now "file modification time 14 Nov 08:53 UTC on the Mac" | source and zone now stated, as asked. It is the same instant as before (09:53 CET), so the oddity against the cluster report's S1 at 10:51 CET remains (R4) |
| N1, N9 | report §5 lists the docker://-only reference coverage, the fact that this acceptance does not review the S2 files, and the three conservative choices | ✔ |
| N2, N4, N10 | left as notes. Report §1 now says "no symlink in the last path component", which matches the code | accepted as open notes |

No regression found. The docker path is byte-identical to the base, the S2 equivalence still holds, and the round-1 guard behaviour is unchanged apart from the two new refusals.

## 3. Findings

No BLOCKING findings.

**R1 (NON-BLOCKING). The duplicate-SIF check compares strings only.** Listing the same file as `r1.sif` (relative to the manifest directory) or as `<dir>//r1.sif` passes, and the file is then transferred twice and counted toward 100 MB. Real SIFs are far above 100 MB, so in practice the 100 MB cap still refuses them; the gap matters only for small images. *Fix:* compare `os.path.realpath(base / f)` (absolute `f` as is) with `os.path.realpath(img)` for every input entry.

**R2 (NON-BLOCKING). The disk test is far from the boundary.** It uses 2000 KiB against 3,000,000 B, so a KiB/kB slip (`×1000`) or `<=` would pass the suite. *Fix:* add 2930 KiB → accepted and 2929 KiB → refused for the 3,000,000-byte SIF.

**R3 (NON-BLOCKING). `request_disk` covers the SIF alone.** The ordinary inputs, up to 100 MB, and the job's own output are not included. *Fix (optional):* require `disk_kb × 1024 ≥ size + total_input_bytes`, or say in report §1 that the check is a lower bound.

**R4 (NON-BLOCKING). README time vs cluster report.** 08:53 UTC (09:53 CET) is before the cluster report's S1 (10:51 CET), when it says S2 had not started. Either the Mac clock or the report times differ. *Fix:* add a half-sentence noting the discrepancy, or drop the time. It does not affect the byte identity, which was checked directly.

Verdict: accepted
Accepted commit: 37ef68f3f19c57fc720588e6ac7e3b23e2cfa4f3
