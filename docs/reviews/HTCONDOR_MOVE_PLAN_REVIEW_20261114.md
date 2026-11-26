# Independent pre-execution review — `/ceph/dwong` → `/work/dwong` move plan (night of 13/14 Nov 2026)

**Reviewer role:** fresh, independent, read-only reviewer for unit task-11. Not the author, not the
executing agent. This review was performed **before anything moved**, as the runbook's opening rule and
§1.3 require ("A fresh independent reviewer checks the plan … until *accepted*").

**Date/time of review:** 13 November 2026, 23:46–23:53 CET (Europe/Berlin).

**Worktree:** `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/htcondor-prep-20261114`,
branch `htcondor-prep-20261114`, HEAD **`c78f8c4a3fbb250266cee7a0820354b905181f46`**.
`MOVE_PLAN.md` and its inputs are **untracked** in that worktree (`git status`: `?? docs/r1/reports/htcondor_prep_20261114/`),
so the reviewed text is bound by SHA-256 below, not by a commit (finding F17).

**Artifacts reviewed (SHA-256, working tree at the time of review):**

| Artifact | Lines | SHA-256 |
|---|---:|---|
| `docs/r1/reports/htcondor_prep_20261114/MOVE_PLAN.md` | 96 | `5b09b5cb814b46b8b4a914ef9d54eb9fe73ce2bd0ffd88d30e87589306aa589a` |
| `docs/r1/reports/htcondor_prep_20261114/POOL_FACTS.md` | 51 | `8bc3bacb00bdadd8cb9c65e0a77d3237a443cfe1f146c9cdf8fc7eb6f8a6e6ce` |
| `…/pinned_paths.txt` | 213 | `54033599a1386f22853605c87c567300fc2d1b1ee8a85ff313e02c00f113008f` |
| `…/raw/inventory.tsv` | 72 | `e697f85ddd15ac2a6950f101c97a2d9aa2d4603ef3df94086326329c4aadcdb6` |
| `…/raw/entry_stats.tsv` | 72 | `5957f2fff19f81f35253fde790e6e6c0b186e557c5269b684f9662abb588a52d` |
| `…/raw/pool_facts_raw.txt` | 84 | `fd4cbfd814eeed09b1c4bb756129b9a17461b85fbf61bdc91427983d9699f5d8` |
| `…/raw/host_facts_A.txt` | 161 | `278d0579deaa444d5f69392af0afee4d76da9e3cd60c75eb068985b8ec5b1430` |
| `…/raw/host_facts_B.txt` | 115 | `ba6529e0eb6e8aa18465db3bcf82e19f0430055370fa8e9b2833a48ef42420e2` |

**Reviewed against:** `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md` §0.2, §0.5, §1.1–§1.4
(240 lines, provenance `69b3576b`, unchanged) and `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_ERRATA_20261114.md`
§A4, §A5, §A7-F10/F11 (106 lines, operative where it differs from the runbook), plus the author's night
instruction "文件搬迁按 §1，一律复制核对后原件进 `_to_delete/`、原路径留软链接，不删任何东西".

**Hard limits of this review (deliberate).** No SSH, no cluster access, no deepthought/portal1/bms access,
no execution of any cluster command, no file moves, no `du`/`find` on `/ceph` or `/work`, no git
commit/push. Every statement about cluster state below is taken from the supplied `raw/` transcripts and
is marked as such; I did not measure anything on the pool. No file other than this review was written.

---

## 1. What was checked, and how

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Runbook §0.2, §0.5, §1.1–§1.4 | full read (240 lines) | Rules extracted; see §5, §6. |
| 2 | Errata A4, A5, A7-F10/F11 | full read (106 lines) | Operative requirements extracted; the plan deviates in F3/F4/F12. |
| 3 | Plan table transcription | parsed all 66 table rows and compared every size/file/median/p90/<64KB value with `raw/entry_stats.tsv` | **0 mismatches** — the numbers were copied faithfully; the problems are classification, coverage and protocol, not arithmetic. |
| 4 | Inventory completeness | `raw/inventory.tsv` has 70 entries; `host_facts_A` L14 shows `/ceph/dwong` with link count 63 (= 2 + 61 subdirectories); 70 entries = 61 directories + 9 regular files | Inventory itself is complete at top level. |
| 5 | Plan coverage vs inventory | set difference | **4 entries in the inventory are absent from the plan** (73.76 GB, incl. `hcp_meg` 66.03 GB); 36 move + 30 skip = 66, not 70 (F2). |
| 6 | Entry-stats integrity | field-count and sanity check of all 70 rows | **4 malformed rows, exactly the 4 missing entries** (`lt64k` > `files`, `max` empty) (F2). |
| 7 | Classification of every move row | §1.3 rows, `entry_stats` flags, `host_facts_A` listing, 25 Oct census | 1 wrong (F1), 1 unreadable/root-owned (F6), 7 single-file (F5), 6 need a kind note (F8), rest consistent. |
| 8 | Classification of every skip row | same | All 30 skip reasons are valid on the recorded data; `r1_prepare_20261025` has a wrong citation (F12); whole-tree venv skips are conservative (F13). |
| 9 | Pinned paths | `grep` of `pinned_paths.txt` vs plan | No move row is named by a pinned path. `agent_paper_B`, `opt`, `models`, `r1_batch1_*` are skipped; `r1_prepare_20261025` is **not** in `pinned_paths.txt` (F12); `autoresearch_harness`, `tmp`, `llamacpp_setup`, `third_party` are not current top-level entries (historical pins). |
| 10 | venv/conda rule | `entry_stats` flags + `host_facts_A` A10 | **No move row has `venv_or_conda=yes`**; all 14 flagged entries are skipped. `.conda` needs an explicit cache justification (F7). |
| 11 | Sweep-1 evidence | `host_facts_B` B5, `POOL_FACTS` L45 | Sweep outputs live under `r1_prepare_20261025/…` and are **skipped**; the pinned `root_trials` paths are under it as well. Requirement met. |
| 12 | Disk gate | raw `df`/`quota` vs plan arithmetic | Numbers correct; per-entry gate text present but the MOVE_LOG schema and the floor-breach action are not specified (F9). |
| 13 | No-deletion protocol | clause-by-clause against runbook §1.4 + errata A5 | Protocol preserved; gaps in F5/F10/F11. |
| 14 | Scope/order/time/in-use | §1.4 + A4 + A7-F10 + §1.1.3 | Deviations F3 and F4. |
| 15 | Author instruction | Chinese instruction vs protocol | Plan does not contradict it: original → `_to_delete/`, symlink back, never `rm` (§7). |
| 16 | Cluster state | — | **Not checked** (no SSH); see §8. |

---

## 2. Findings

Severity: **BLOCKING** = executing as written would certainly fail or be unsafe (data loss, evidence
loss, STOP condition entered blindly); **MAJOR** = a stated goal, standing rule or classification is
wrong/unexecutable as written and must be fixed before acceptance; **MINOR** = robustness/executability
detail that can cost the night or make verification unreliable; **NIT** = wording/evidence hygiene.

**There is no BLOCKING finding.** The no-deletion protocol is intact and nothing in the plan can delete
or overwrite data. The plan still cannot be accepted as written because of F1–F5.

| ID | Sev | Where | Finding and evidence | Exact required fix |
|---|---|---|---|---|
| F1 | **MAJOR** | MOVE_PLAN L9 | **`hf_cache` is misclassified as a move.** `entry_stats.tsv`: 19,133,118,938 B / 127 files / 100 files < 64 KB / median 0 B / p90 99,630,640 B / max 3,987,450,520 B / `cache_like=yes`, not git. The 100 small files can account for at most 6.4 MB, so **≥19.12 GB (99.9 %) sits in 27 files**, p90 99.6 MB. That is a model/blob cache, not the §1.3 "huggingface metadata" cache; runbook L80 says large files (models, archives, datasets kept as large files) **stay on `/ceph`**, and the §1.3 large-file row marks "mostly models and archives" skip. Moving it would put 19.13 GB — **38 % of the plan's 50.15 GB** — on `/work` for a benefit of 127 inodes. The plan's quoted evidence (median 0, 100/127 <64 KB) counts only the metadata files and does not support "small-file tree". | Remove `hf_cache` from the move list and classify it **skip**: "large-file/blob cache — 27 files ≥64 KB hold ≥19.12 GB (p90 99.6 MB, max 3.99 GB, `cache_like=yes`); §1 large files stay on `/ceph`". If the author wants the HF metadata under `/work`, do a `find -size +64k` census first and move only the small files (split entry, same protocol on the remainder). |
| F2 | **MAJOR** | MOVE_PLAN table L7–L74 vs `raw/inventory.tsv` | **4 of 70 inventory entries are not classified at all**, and their stats rows are the only corrupt rows in `entry_stats.tsv`: `hcp_meg` 66,025,737,182 B/190 files, `models` 4,683,073,537 B/1, `trigger_efficiency.tar.zst` 3,033,112,238 B/1, `round5-titan-c7517f1.bundle` 22,670,205 B/1 → **73.76 GB unclassified**. Corrupt rows, exact text: `hcp_meg\t…\t190\t191560\t700717256\t700717256\t\tno\tno\tno` (field 4 `lt64k` = 191,560 > 190 files; `max` empty), and the same for the three single-file entries (`lt64k` = 4,683,073,536 > 1 etc.). The plan's own count (36 + 30 = 66) exposes the gap; `models` appears only in the Excluded prose (L90) without size/files. §1.3 requires classifying **every** entry. | Add 4 rows (all **skip**): `hcp_meg` 66.03 GB/190 → large-file dir (median 191,560 B, p90 = max 700,717,256 B); `models` 4.68 GB/1 → pinned GGUF (`pinned_paths.txt` L24) + single large model file; `trigger_efficiency.tar.zst` 3.03 GB/1 → single archive, stays on `/ceph`; `round5-titan-c7517f1.bundle` 22.67 MB/1 → single-file git bundle, no small-file benefit. Regenerate the four `entry_stats` rows (or mark `lt64k`/`max` `n/a`) so later readers do not inherit the shift; update the summary counts. |
| F3 | **MAJOR** | MOVE_PLAN L82 (protocol step 5) | **The in-use check is narrower than the operative errata.** Step 5 re-checks in-use **on deepthought only** and says "record that other login hosts were not checked (A7-F10)" — but errata A7-F10 requires the process check on **every** login host where `/ceph/dwong` is mounted that is reachable from deepthought's SSH config (`deepthought`, `portal1`, `bms1`, `bms3`; `bms2` unverified) and allows "not checked: `<host>`" only for an **unreachable** host. The re-check also performs only half of §1.1.3: it takes cwd but not the **open-files** check (`ls -l /proc/<pid>/fd`, own user only) and not the `tmux`/`screen`/`nohup` check. Why it matters: after the `mv`, a process that holds a cwd/fd on the original keeps operating on the `_to_delete` inode while `/ceph/dwong/<X>` points at the `/work` copy — silent divergence, which is exactly the §0.5 STOP "a move would touch a directory that a running process/job uses". The claim in `POOL_FACTS` §3 that "no process was seen opening a moved entry's files" is not backed by any raw transcript: `host_facts_A` A13 is only `ps -u dwong -o pid,etime,cmd` (no `/proc/<pid>/cwd`/`fd` output), and the pids 1791926/1800582 quoted there appear in neither `host_facts_A` nor `host_facts_B`. | Replace step 5 with: on each of `deepthought`, `portal1`, `bms1`, `bms3`, run `pgrep -u dwong -a`, `ls -l /proc/<pid>/cwd` and `ls -l /proc/<pid>/fd | grep /ceph/dwong` (own pids only), a `tmux`/`screen`/`ps -u dwong` check, and pool-wide `condor_q dwong -af Iwd Cmd`; record host, command and result per entry in `MOVE_LOG.tsv`; if any hit is under the entry, **skip the entry** (STOP); hosts that cannot be reached are recorded as "not checked: `<host>`" and no other host may be declared unchecked. Capture the output into `raw/` so the claim is reproducible. |
| F4 | **MAJOR** | MOVE_PLAN (whole document) | **No execution window, order or scope rule.** The plan says "entry by entry" once (L5) but never "one entry at a time", never states the execution order, and contains **no 03:30 CET stop** — errata A4 L45 makes "stop starting new moves at 03:30" operative and the night's hard stop is 05:30 (A4; runbook L229). It also gives no rule for entries not yet done at the cut-off. The table happens to be sorted largest-first, but nothing binds execution to that order. | Add an "Execution order and stop" section: execute **in the table order (descending size), one entry at a time** (copy → verify → re-check → retire → symlink → verify); before starting each entry compare `date` (CET) with 03:30; **do not start a new entry at or after 03:30** (an already-running copy may finish); record the stop time and the unprocessed entries in `MOVE_LOG.tsv` and carry them to the report; the 05:30 hard stop still ends all VPN-dependent work. |
| F5 | **MAJOR** | MOVE_PLAN L80 (protocol step 3) applied to file entries | **The directory-form rsync cannot execute for the 7 regular-file entries.** `rsync -aHAX --numeric-ids /ceph/dwong/<X>/ /work/dwong/<X>/` requires the source to be a directory; for a regular file it fails ("change_dir … failed: Not a directory", rsync exit 23). The affected move rows are `ollama` (9 B/1 file), `ollama.log` (40,351 B), `trigger_efficiency.sha256` (9,626 B) and the four `lucid_*` logs (1,065/1,072/7,982/1,594 B; `host_facts_A` L47–49 shows the lucid logs as `-rw-r--r--`). Step 4 then has no `/work` copy to compare and the failure rule's "move the partial `/work` copy" has nothing to move. | Recommended: **drop the 7 single-file entries** from tonight's move list (57 KB total, 7 inodes of benefit; nothing is lost by leaving them on `/ceph`) and say so in the plan. Alternative: add a file branch — `rsync -aHAX --numeric-ids /ceph/dwong/<X> /work/dwong/<X>` (no trailing slash), `sha256sum` both, `mv` + `ln -s` the file, verify through the old path. Also decide explicitly for the 0-file directories (`ceph_lwindett` F6, `.ollama` F16). |
| F6 | MINOR | MOVE_PLAN L43 | **`ceph_lwindett` must not be moved.** `host_facts_A` L32: `drwx------ 4 root root 2 May 20 13:38 ceph_lwindett` — root:root 0700, so `dwong` cannot read it; the inventory recorded 2 B/0 files because it could not be traversed, and `docs/r1/reports/DT_HOST_CENSUS_20261025.md` already records "ceph_lwindett permission denied; skipped". rsync will fail, and §0.2 "never touch what you did not start" applies: a root-owned directory is not the author's to relocate. | Classify **skip**: "root:root 0700, unreadable (census 20261025: permission denied); not relocatable by `dwong`". Remove from the move list. |
| F7 | MINOR | MOVE_PLAN L19 | **`.conda` needs the conda-vs-cache justification.** §1.3 has an explicit "Python venv or conda environment → skip" row; `.conda` is moved under the generic small-file/cache reason. The recorded flags (`venv_or_conda=no`, `cache_like=yes`) support a package-cache move, but the plan never says why the one entry with "conda" in its name is not the conda-environment row (A10 lists six venv paths, none `.conda`). 0.37 GB/8,238 files is a genuine small-file win, so keep it only with a recorded reason. | One-line reason: "conda package cache (`venv_or_conda=no`, `cache_like=yes` in `entry_stats.tsv`; no `envs/`/`conda-meta` environment)" plus the read-only `ls .conda` check that establishes it; otherwise skip. |
| F8 | MINOR | MOVE_PLAN L15–L18, L45–L74 | **The evidence/results boundary is not evidenced for 6 moved entries.** The plan skips `enl_runs` and `tr09_runs` as "holds evidence/results" but moves `hcp_runs`, `tr07_runs`, `nimh_runs`, `mlst-successor-runs-20260913` with the identical generic reason; `ORACLE` and `DELight_mtr` are moved under the git row although `meg_z` (also `git=yes`) is skipped as evidence. Neither `inventory.tsv` nor `entry_stats.tsv` records the §1.1.2 "cache, data, models or results" class, so the move/skip line for these six cannot be reconstructed from the inputs. If any of them holds run outputs, ledgers or captures, the move violates the §1.3 evidence row. | Add a one-line `kind`/basis per entry with the read-only evidence (git HEAD + top-level names + presence of `results/`, `ledger`, `*.jsonl`, `captures/`), and skip the entries that hold evidence. This is a quick `ls`/`find -maxdepth 1` pass over six directories; record it in the plan before accepting. |
| F9 | MINOR | MOVE_PLAN L78, L84 | **MOVE_LOG.tsv is not defined and the floor-breach consequence is missing.** Errata A5 requires the `du -sb` / `df` / `quota` / floor numbers in `MOVE_LOG.tsv`, and runbook §1.4.6 requires entry, bytes, files, manifest SHA, verdict; the plan only says "record in `MOVE_LOG.tsv`" and "append the result", and the file does not exist yet. The plan also says "require post-copy free ≥ floor" without stating A5's/§0.5's consequence: **stop the move programme and report**. | Create `MOVE_LOG.tsv` before the first move with the header `entry, utc, du_bytes, files, df_avail_before, quota_output, expected_free_after, floor, gate_pass, manifest_sha256, git_head_ceph, git_head_work, in_use_check, retire_name, verify_pass, old_path_pass, verdict, notes`; add "gate would be breached → **stop the move programme**, record, report (A5, §0.5)". |
| F10 | MINOR | MOVE_PLAN L81 | **Manifest and git comparisons are not normalized.** The runbook's `find … -print0 \| sort -z \| xargs -0 sha256sum` embeds absolute paths, so `/ceph/dwong/<X>/…` and `/work/dwong/<X>/…` manifests are never equal; `git worktree list` likewise prints the worktree's absolute path. As written, every verification would falsely fail (safe direction, but it would burn the night and retire good copies as `.failed_*`). | In step 4: generate both manifests from each copy root with relative paths (`cd <root> && find . -type f -print0 \| sort -z \| xargs -0 sha256sum`) and compare; for git compare `rev-parse HEAD` and `status --porcelain` (identical) and normalize the path field of `git worktree list` (or compare `HEAD`/`status` only). |
| F11 | MINOR | MOVE_PLAN L79, L86 | **`/work/dwong/_to_delete` is never created and the failed-copy name has no collision guard.** The failure rule moves partial copies to `/work/dwong/_to_delete/<X>.failed_<UTC>`, but the plan only creates `/ceph/dwong/_to_delete` (step 2); errata A5's "check the destination does not exist and use a unique suffix" is applied to the destination and retirement name but not to the `.failed_*` name. The "no `/work` copy exists" case (F5) is also undefined. | `mkdir -p /work/dwong/_to_delete` before the first copy; `test -e` + unique suffix for `.failed_<UTC>`; if no `/work` copy exists, record "nothing to retire" and continue; never `rm`. |
| F12 | MINOR | MOVE_PLAN L61 (skip reason), L82, L90 | **Wrong citations.** (a) `r1_prepare_20261025`'s skip reason says "named by a pinned path (`pinned_paths.txt`)", but `pinned_paths.txt` contains **no** `r1_prepare` line (verified: 0 hits); the pin is real only through the sweep-1 manifests/authorization (A7-F11's authoritative list; `host_facts_B` B5 lists the sweep dirs under it), and the skip is already justified by evidence + venv. (b) L82 cites "A7-F10" for *not* checking other login hosts, while A7-F10 requires the opposite (F3). (c) L90 says `r1_prepare_20261025` contains `autoresearch_harness`, whereas `pinned_paths.txt` names `/ceph/dwong/autoresearch_harness` as a top-level path; that path is not a current top-level entry (§1 row 4), so it is a historical pin, and `tmp`, `llamacpp_setup`, `third_party` are likewise historical. | Cite the sweep manifests/authorization for `r1_prepare_20261025` (or drop the pinned claim and keep evidence + venv); correct the A7-F10 citation; state that `autoresearch_harness`/`tmp`/`llamacpp_setup`/`third_party` are historical pins not present in the inventory. |
| F13 | MINOR | MOVE_PLAN L50, L52, L54, L62 | **Whole project trees are skipped as "venv".** `transformer` (18.16 GB, 24,940 files, 23,714 <64 KB), `jepa` (29.58 GB, 15,778/11,320), `gain_units_20261028` (8.92 GB, 41,121/37,569) and `agent-checkpoint-intervention` (1.00 GB, 45,361/44,280) are skipped because a `venv` **subdirectory** is present (`host_facts_A` A10 lists `jepa/venv`, `gain_units_20261028/venv`, …), not because the entry itself is an environment. The skip is conservative and safe, but it leaves ~127 k files (~126 k <64 KB) on `/ceph` — the workload §1 exists to relocate. | Record the venv as a subpath and state that the rest of the tree is deliberately left (or mark it for a later pass that moves the tree and leaves/rebuilds `venv/`). Do **not** add these to tonight's list if it would cost the 03:30/05:30 window. |
| F14 | NIT | MOVE_PLAN L5 | Summary arithmetic label: "the whole plan (45 GB) leaves ~1.05 T free" — the 36 move rows sum to **50,152,126,849 B = 50.15 GB (46.71 GiB)** and 1.1 T − 50.15 GB ≈ 1.05 T. The "50.2 GB" in the same sentence is right; the "45 GB" label is wrong. | Say "50.2 GB (46.7 GiB)" in both places. |
| F15 | NIT | POOL_FACTS §1 / L15 vs `raw/pool_facts_raw.txt` L78 and `host_facts_B` B1 | The author's job 759618 is described as **IDLE** with `Cmd=/work/dwong/r2_batch/tiny/./exe.sh`, `Iwd=/work/dwong/r2_batch/tiny`; the raw transcript records only `759618 cms cms.dwong` (accounting group), and `host_facts_B` B1 at 23:39:53 says "0 own jobs … 1 held" for all users. The state/Iwd therefore rest on an unrecorded query. Not a move risk (`r2_batch` is under `/work`, not `/ceph/dwong`), but the claim should be reproducible. | Append the verbatim `condor_q` output used for 759618 (Iwd/Cmd/JobStatus) to `raw/` and quote it; reconcile "IDLE" with "1 held". |
| F16 | NIT | MOVE_PLAN L43–L44 | `.ollama` is 1 B/0 files and `ceph_lwindett` is unreadable (F6); copying 0-file entries costs a full copy/verify/retire/symlink cycle for no benefit. | Optional: omit `.ollama` from the list (and `ceph_lwindett` per F6); keep the other small directories. |
| F17 | NIT | provenance | `MOVE_PLAN.md` and its inputs are untracked in the worktree, so the plan the author executes is not bound by a commit; this review binds it by SHA-256 (header). | Commit the plan + inputs before execution (or copy their SHA-256 into the report). Do not push `main`/`r1`/`exam-x-*` (§0.2). |

---

## 3. Classification audit

### 3.1 The 36 move rows

`flags` = `entry_stats.tsv` git/venv/cache columns; `<64 KB` = `lt64k/files`. All values were checked
against `entry_stats.tsv` and match exactly. "OK" means the recorded evidence supports the §1.3 row the
plan asserts.

| entry | GB | files | <64 KB | flags | §1.3 basis asserted | audit |
|---|---:|---:|---:|---|---|---|
| `hf_cache` | 19.13 | 127 | 100/127 | cache | cache (metadata/data) | **REMOVE — F1** |
| `work` | 7.38 | 140 | 125/140 | git+cache | git repo / worktree | OK (git row; 7.37 GB sits in its 15 large git objects — permitted, low inode benefit) |
| `enl_preparation` | 4.88 | 1324 | 1232/1324 | — | small-file data | OK |
| `hcp_xopt_20261107` | 4.32 | 9389 | 8411/9389 | git | git repo / worktree | OK |
| `hcp_xopt_20261106` | 3.85 | 6308 | 5764/6308 | git | git repo / worktree | OK |
| `arXiv-v1-polished-extended-preprint` | 2.61 | 7775 | 7195/7775 | git | git repo / worktree | OK |
| `hcp_runs` | 2.28 | 4320 | 3113/4320 | — | small-file data | kind note — F8 |
| `ORACLE` | 2.03 | 1622 | 1473/1622 | git | git repo / worktree | kind note — F8 |
| `mlst-successor-runs-20260913` | 0.83 | 4546 | 3659/4546 | — | small-file data | kind note — F8 |
| `DELight_mtr` | 0.77 | 1453 | 1211/1453 | git | git repo / worktree | kind note — F8 |
| `.conda` | 0.37 | 8238 | 7560/8238 | cache | cache (metadata/data) | justify — F7 |
| `y19_host` | 0.33 | 4000 | 3812/4000 | git | git repo / worktree | OK |
| `zc_host` | 0.32 | 8014 | 7823/8014 | git | git repo / worktree | OK |
| `megz_timing_host` | 0.31 | 2150 | 1950/2150 | git | git repo / worktree | OK |
| `megz_host` | 0.30 | 2164 | 1973/2164 | git | git repo / worktree | OK |
| `megz_r1_host_20261014` | 0.26 | 1017 | 983/1017 | git | git repo / worktree | OK |
| `tr07_runs` | 0.16 | 2075 | 1888/2075 | — | small-file data | kind note — F8 |
| `tr09_receiving` | 0.01 | 4 | 2/4 | — | small-file data | OK |
| `nimh_runs` | 0.00 | 249 | 247/249 | — | small-file data | kind note — F8 |
| `y19_zenodo_git` | 0.00 | 22 | 21/22 | — | small-file data | OK |
| `b3` | 0.00 | 36 | 33/36 | — | small-file data | OK |
| `y19_zenodo` | 0.00 | 13 | 13/13 | — | small-file data | OK |
| `e12_runtime_20260823_201812` | 0.00 | 55 | 55/55 | — | small-file data | OK |
| `ollama.log` | 0.00 | 1 | 1/1 | — | small-file data | file-form or drop — F5 |
| `zc_logs` | 0.00 | 12 | 12/12 | — | small-file data | OK |
| `trigger_efficiency.sha256` | 0.00 | 1 | 1/1 | — | small-file data | file-form or drop — F5 |
| `lucid_c5_train.log` | 0.00 | 1 | 1/1 | — | small-file data | file-form or drop — F5 |
| `y19_logs` | 0.00 | 8 | 8/8 | — | small-file data | OK |
| `b3_logs` | 0.00 | 5 | 5/5 | — | small-file data | OK |
| `b2_receive` | 0.00 | 6 | 6/6 | — | small-file data | OK |
| `lucid_training_data.gen.log` | 0.00 | 1 | 1/1 | — | small-file data | file-form or drop — F5 |
| `lucid_c5_l40s.log` | 0.00 | 1 | 1/1 | — | small-file data | file-form or drop — F5 |
| `lucid_c5_fast.log` | 0.00 | 1 | 1/1 | — | small-file data | file-form or drop — F5 |
| `ollama` | 0.00 | 1 | 1/1 | — | small-file data | file-form or drop — F5 |
| `ceph_lwindett` | 0.00 | 0 | 0/0 | — | small-file data | **REMOVE — F6** |
| `.ollama` | 0.00 | 0 | 0/0 | cache | cache (metadata/data) | empty; NIT F16 |

No move row is a venv/conda entry, and no move row is named by a pinned path — those two §1.3 rules are
satisfied on the recorded flags. The two `git=yes` entries not in the git row (`hf_cache` = cache, F1)
and the 0-file entries are the only structural oddities.

### 3.2 The 30 skip rows

All 30 were checked one by one against `entry_stats.tsv`/`host_facts`; **the reasons are valid as far as
the recorded inputs go**. Summarised:

| reason class | entries (all skipped) | check |
|---|---|---|
| Pinned path | `agent_paper_B` (0.13 GB), `opt` (0.94 GB), `models` (in prose only — F2), `r1_batch1_ENGINEERING_ONLY_20261012_E4cC3e` (2.25 GB), `r1_batch1_ENGINEERING_ONLY_resume_20261012T191238Z` (0.00 GB) | Named by `pinned_paths.txt`; correct. `r1_prepare_20261025` is **not** named there (F12). |
| Evidence/results | `paper1_dataset` 185.85 GB (median 1.43 GB), `meg_z` 84.82 GB (max 908.9 MB), `lucid_training_data` 42.83 GB (p90 1.79 GB), `enl_runs` 36.41 GB (median 575 KB), `b1` 35.45 GB (max 4.84 GB), `tr09_runs` 28.80 GB (max 14.36 GB), `tr09_preparation` 14.05 GB (max 6.93 GB), `delight_conf` 5.24 GB (median 10.8 MB), `b2` 3.05 GB, `megz_r1_returns` 0.98 GB (median 189 MB), `cresst_u2_audit_20260930` 0.04 GB (audit), `r1_bringup_20261025` 0.00 GB | Correct on size/name evidence; `b2` is the one whose "results" character is not recorded (same F8 caveat, but skip is the safe side). |
| venv/conda | `jepa`, `transformer`, `gain_units_20261028`, `t20s_regen_20261021`, `hcp_seal_20261027`, `deepthought_tasks_20261025`, `r1_prepare_20261025`, `agent-checkpoint-intervention`, `noise-weighted-subspace-reconstruction`, `meg_env`, `paper1_env`, `y19_venv`, `zc_venv`, `ots_env` | `venv_or_conda=yes` in every case; correct per §1.3. Four are whole project trees (F13). |

### 3.3 Entries missing from the plan (F2)

| entry | bytes | files | required class |
|---|---:|---:|---|
| `hcp_meg` | 66,025,737,182 | 190 | skip — large-file directory (median 191,560 B; 66 GB in 190 files; max 700.7 MB) |
| `models` | 4,683,073,537 | 1 | skip — pinned GGUF (`pinned_paths.txt` L24) + single large model file |
| `trigger_efficiency.tar.zst` | 3,033,112,238 | 1 | skip — single 3.0 GB archive, stays on `/ceph` |
| `round5-titan-c7517f1.bundle` | 22,670,205 | 1 | skip (or move with a file-form command) — single-file git bundle |

`models` is pinned and is the only one mentioned in prose (L90); none of the four appears in the move/skip
table with size and file count, as §1.3 requires.

---

## 4. Disk-gate audit

**Source of the numbers:** `host_facts_A` A1 — `work:/work_storage/work 1.4T 385G 1.1T 27% /work`;
`/ceph 1.4P 986T 346T 75%`; `/home 100G 202M`. A1's `quota` section prints nothing; `host_facts_B` B7
confirms `/usr/bin/quota` exists and prints nothing; `POOL_FACTS` L37 records the same. The no-quota-output
finding and the use of the 1.4 T filesystem capacity as the quota proxy are **correct and conservative**:
15 % of the largest possible quota (= filesystem capacity, 1.4 T) is ≥ 15 % of any smaller real quota.

| Item | Plan value | Check |
|---|---|---|
| `/work` free at plan time | 1.1 T of 1.4 T (27 % used) | Matches raw `df` exactly. |
| Plan move total | 50.2 GB | Rows sum to 50.15 GB (50,152,126,849 B); ✓ (the separate "45 GB" label is wrong — F14). |
| Floor | max(15 % × 1.4 T = 210 G, entry bytes + 5 GiB) | Arithmetic ✓; the floor is A5's `max(15 % of the quota, bytes + 5 GiB)` with the capacity proxy; 210 G always binds (largest entry bytes + 5 GiB = 24.2 GB). |
| Expected free after the whole plan | ~1.05 T | 1.1 T − 50.15 GB ≈ 1.05 T ✓; far above the 210 G floor, so admissible entry by entry. |
| Per-entry pre-copy check | specified (L78): `du -sb`, `df -h /work`, `quota -s`, require post-copy free ≥ floor, record in `MOVE_LOG.tsv` | Present; **but** the record fields, the file itself and the floor-breach consequence are missing (F9). |

`/ceph` (15 % floor) is not at risk: 346 T free before the moves, and the moves do not write to `/ceph`
(the originals are renamed within the same filesystem). No quota/disk STOP is expected, and the per-entry
gate covers unexpected growth on the shared `/work`.

---

## 5. No-deletion protocol audit

Clause-by-clause against runbook §1.4 and errata A5 (the plan's step numbers are its L78–L86):

| Requirement (runbook/errata) | Plan | Status |
|---|---|---|
| Before each entry: `du -sb`, `df -h`, `quota -s`; post-copy free ≥ floor; numbers in `MOVE_LOG.tsv` | step 1 | Present; fields/consequence missing (F9) |
| `mkdir -p /ceph/dwong/_to_delete` before first move | step 2 | Present |
| Destination and retirement name collision guard, unique suffix, else abort | step 2 | Present for `/work/dwong/<X>` and `<X>.moved_20261114`; missing for `/work/dwong/_to_delete/<X>.failed_*` (F11) |
| `rsync -aHAX --numeric-ids` under `nice`/`ionice` | step 3 | Present; fails for 7 file entries (F5) |
| Verify file count + total bytes | step 4 | Present |
| SHA-256 manifest of every file equal on both sides | step 4 | Present but needs path normalization (F10) |
| Git repos: `rev-parse HEAD`, `status --porcelain`, `worktree list` equal | step 4 | Present but needs path normalization (F10) |
| Re-check in-use after the copy, before the rename | step 5 | Present; too narrow (F3) |
| `mv` original to `/ceph/dwong/_to_delete/<X>.moved_20261114` | step 6 | Present |
| `ln -s /work/dwong/<X> /ceph/dwong/<X>` | step 6 | Present |
| Verify through the old path (`ls -l`, `git status` if git) | step 7 | Present |
| Append result to `MOVE_LOG.tsv` | step 7 | Present; schema missing (F9) |
| Failed verification: source untouched, no rename, partial `/work` copy moved to `/work/dwong/_to_delete/<X>.failed_<UTC>`, never `rm`, record, next entry | failure rule L86 | Present and **matches A5**; prerequisites missing (F11) and the no-copy case undefined (F5) |

**No deletion anywhere in the plan; no `rm` in the protocol or the failure rule.** The original is always
retained complete in `/ceph/dwong/_to_delete/`, the old path keeps working through a symlink, and the
failure path only moves a partial copy. This part of the plan is correct and is the reason there is no
BLOCKING finding.

---

## 6. Scope, order, time and active sessions

- **One entry at a time / order / 03:30 stop:** not stated (F4). The table is sorted largest-first, but
  nothing binds execution to that order, and there is no cut-off for starting new moves.
- **In-use re-check:** deepthought only, cwd but not open files, no other login hosts (F3). At collection
  the recorded sessions are a `codex app-server` (pid 1100480, 17 days), a VS Code server plus a
  `fileWatcher` (pids 1790824–1791391) and terminal shells whose cwd is `/ceph/dwong`
  (`host_facts_A` A13, `host_facts_B` B9, `POOL_FACTS` §3). None is recorded as holding a cwd/fd under a
  specific moved entry, and `condor_q` is pool-wide; the author's job 759618 (`Iwd=/work/dwong/r2_batch/tiny`
  per `POOL_FACTS`; raw evidence incomplete — F15) does not touch a moved entry.
- **Pinned paths:** no move row is named by `pinned_paths.txt`; the sweep-1 evidence under
  `r1_prepare_20261025` (including the pinned `root_trials` paths listed in `host_facts_B` B5) is
  skipped. `agent_paper_B`, `opt`, `models`, `r1_batch1_*` are skipped. This requirement is met.
- **Paper B data:** the moves relocate already-present files without reading their contents; the plan
  adds no Paper B data to the cluster and performs no experiment/label/sweep work. Consistent with §0.2.
- **The author's instruction** ("一律复制核对后原件进 `_to_delete/`、原路径留软链接，不删任何东西"):
  the plan implements exactly that; no contradiction. The only non-compliance is classification/coverage
  quality (F1/F2) and protocol gaps (F3/F4/F5), not the no-deletion guarantee.

---

## 7. What I accept as correct

- The 66 transcribed rows are numerically faithful to `entry_stats.tsv` (0 mismatches on size, files,
  `<64 KB`, median, p90).
- The 30 skip reasons are valid on the recorded evidence (F12 citation aside), including all six venv
  entries listed by name in `host_facts_A` A10, all pinned entries, and the large/evidence directories.
- No move row is a venv/conda entry or a pinned path (per the recorded flags and `pinned_paths.txt`).
- The disk arithmetic, the no-quota diagnosis and the conservative capacity proxy are correct.
- The no-deletion protocol and the failed-copy retirement are preserved, and the plan never `rm`s.
- The inventory is complete at the top level; the gaps are in the plan, not the raw inventory.

---

## 8. What this review could not check

- No SSH/cluster access: I did not inspect `/ceph/dwong` or `/work/dwong` live, did not run
  `pgrep`/`/proc`/`condor_q`, did not confirm the in-use state at review time, and did not verify the
  paths' existence/ownership beyond the supplied `raw/` transcripts.
- I did not execute or test the rsync/verify commands on the cluster; F5 and F10 are static analyses of
  the command forms.
- I did not read the sweep-1 ledgers or any Paper B evidence (not needed for a move-plan review and
  forbidden by §0.2/§5).
- `POOL_FACTS`'s job-759618 state/Iwd are accepted only as prose because the raw transcript does not
  contain them (F15).

---

## 9. Verdict and what I need before acceptance

The plan's core design is sound and its no-deletion guarantee is intact, but it **cannot be accepted as
written**: it would move a 19.13 GB blob cache that §1/§1.3 says must stay on `/ceph` (F1), it leaves
73.76 GB of entries unclassified with corrupt stats rows (F2), it checks in-use on only one of the four
login hosts and only half of the §1.1.3 check (F3), it has no execution order or 03:30 stop (F4), and its
copy command cannot execute for 7 of its 36 entries (F5). Those five fixes are plan-text edits plus a
regeneration of four stats rows; no cluster action is required to make them.

**Minimal revision that would let me accept it on re-check:** fix F1–F5 and F6/F7/F9/F10/F11 in
`MOVE_PLAN.md`/`MOVE_LOG.tsv` (and the four `entry_stats.tsv` rows); fix or explicitly carry F8, F12 and
F13; F14–F17 are edits/notes. I do not need a new night window or cluster access to re-check — a diff of
`MOVE_PLAN.md` and the regenerated stats rows suffices.

**If revised as above, the execution order I expect:** the table order, descending size, **one entry at a
time**: `work`, `enl_preparation`, `hcp_xopt_20261107`, `hcp_xopt_20261106`,
`arXiv-v1-polished-extended-preprint`, `hcp_runs`, `ORACLE`, `mlst-successor-runs-20260913`,
`DELight_mtr`, `.conda`, `y19_host`, `zc_host`, `megz_timing_host`, `megz_host`, `megz_r1_host_20261014`,
`tr07_runs`, `tr09_receiving`, `nimh_runs`, `y19_zenodo_git`, `b3`, `y19_zenodo`, `e12_runtime_20260823_201812`,
`zc_logs`, `y19_logs`, `b3_logs`, `b2_receive` (26 entries, ≈31.0 GB; 27 if `.ollama` is kept), with the
single-file/empty entries dropped or handled by the file-form branch, and the run stopped before 03:30 CET.

**Residual risk I would carry after the revision:** (1) in-use blind spots on hosts that cannot be
reached (`bms2` unverified; unreachable hosts recorded, not checked); (2) the brief `mv`→`ln -s` window
during which the old path does not exist — a writer on a just-moved entry could still land on the
`_to_delete` inode, which the per-entry check reduces but cannot eliminate; (3) `/work` is a shared
filesystem (1.1 T now, other users' growth unknown) — the per-entry gate covers it; (4) F8's
results-vs-source judgement for `hcp_runs`/`tr07_runs`/`nimh_runs`/`mlst-successor-runs-20260913`/`ORACLE`/
`DELight_mtr` remains an author judgement (conservative option: skip them); (5) moved originals double
their space in `_to_delete` on `/ceph` until the author retires them (346 T free, no deletion tonight);
(6) the plan text is uncommitted (F17).

VERDICT: NOT ACCEPTED

---

## Re-check round — revision 2 (final go/no-go)

**Reviewed document:** `docs/r1/reports/htcondor_prep_20261114/MOVE_PLAN.md` **revision 2** (107 lines),
SHA-256 `f5e1f44277f1061419c76c36770be5931d44858329334597133feb7a8eb9a90b`, same worktree
`htcondor-prep-20261114` @ `c78f8c4a`; inputs unchanged (`raw/entry_stats.tsv` still
`5957f2fff19f81f35253fde790e6e6c0b186e557c5269b684f9662abb588a52d`; `raw/inventory.tsv`,
`pinned_paths.txt`, `POOL_FACTS.md` as in round 1). **Re-checked:** 13 November 2026, 23:56–23:59 CET.
Read-only, as before: no SSH, no cluster access, no moves, no git commit; only this review file was
written. Re-check scope = my round-1 findings F1–F17 plus this reviewer's checks of the changed plan; it
is not a full re-review (the unchanged sections are covered by round 1).

### R.1 What was re-checked, and how

| # | Check | Method | Result |
|---|---|---|---|
| 1 | All 70 inventory entries classified | parsed both revised tables and compared the name union with `raw/inventory.tsv` | **70 = 9 move + 61 skip**, no duplicates, union = inventory exactly; **0 size mismatches** against inventory bytes. |
| 2 | Totals | sum of the table rows | moves **19.68 GB** (plan says 19.7 ✓), skips **614.40 GB**, total **634.10 GB** = inventory total ✓. |
| 3 | Move classification | `entry_stats.tsv` flags vs the §1.3 rows | all 9 moves are `git=yes` → §1.3 "git repositories and worktrees" row; **none is venv/conda**, **none is pinned**, **none is the evidence set**. `work` is also `cache_like=yes`. |
| 4 | venv/pinned/evidence protection | flags + `pinned_paths.txt` | all 14 `venv_or_conda=yes` entries are skipped; `agent_paper_B`, `opt`, `models`, both `r1_batch1_*` are skipped; `r1_prepare_20261025` skipped for evidence and the pin claim removed (F12 ✓). |
| 5 | F1 fix | `hf_cache` row | now in the skip list with the blob-cache reasoning (19.13 GB, 27 files, p90 99.6 MB, max 3.99 GB, ~6 MB metadata; §1 keeps large files on `/ceph`). **Fixed.** |
| 6 | F2 fix | four rows + provenance | `hcp_meg`, `models`, `trigger_efficiency.tar.zst`, `round5-titan-c7517f1.bundle` are classified with size/reason; totals corrected; all 70 covered. **Fixed** (residual note R3 on the stats file). |
| 7 | F3 fix | protocol step 1 | in-use check expanded to deepthought + portal1/bms1/bms3 via SSH, with `pgrep`, cwd **and** `/proc/<pid>/fd`, `tmux`/`screen`/nohup, pool-wide `condor_q`, transcript `raw/inuse_<UTC>.txt`, and `bms2` recorded as not checked. **Coverage fixed**; the check is now placed **before** the copy only — see R1. |
| 8 | F4 fix | protocol "Order/limits" | largest-first as listed, one entry at a time, 03:30 CET stop, "not done tonight (cut-off)" recording, no trade against probes/05:30. **Fixed.** |
| 9 | F5 fix | move list | the 7 regular-file entries are all in the skip list with the directory-form-rsync reason. **Fixed.** |
| 10 | F6/F7 fixes | skip list | `ceph_lwindett` skipped (root:root 0700, unreadable, 25 Oct census); `.conda` skipped under the venv/conda row. **Fixed** (reason-consistency note R4). |
| 11 | F8 fix | skip list | the six evidence-boundary trees are skipped conservatively; `enl_preparation` also left out. **Fixed.** |
| 12 | F9/F10/F11 fixes | protocol steps 2–8 | `MOVE_LOG.tsv` schema and the "stop the move programme" floor action present; SHA manifest path-normalised (`cd <root> && find . … sha256sum`) with a `diff` of both sorted manifests; `_to_delete` created on both sides; destination/retirement/`failed_*` collision guards present. **F10 partially fixed** — see R2. |
| 13 | No-deletion rule | full text grep | no `rm`; original → `_to_delete/`, symlink back, failure retires the partial `/work` copy by move; header/provenance repeat the author's instruction. **No contradiction.** |
| 14 | 15 % disk STOP | protocol step 2 + summary | `/work` 1.4 T/385 G/1.1 T free (✓ raw `df`); floor `max(0.15 × 1.4 T, bytes + 5 GiB)`; largest entry 7.38 GB + 5 GiB = 12.4 GB < 210 G, so 210 G binds; post-plan free ≈1.08 T; gate recorded in `MOVE_LOG.tsv`; breach ⇒ stop programme. **No contradiction.** |

### R.2 Round-1 findings — status

| Finding | Status | Evidence |
|---|---|---|
| F1 hf_cache | **fixed** | skip row with blob-cache arithmetic. |
| F2 4 unclassified entries | **fixed** | 9 + 61 = 70, sizes match inventory 0 mismatches; totals 19.68/614.40/634.10 GB. |
| F3 in-use coverage | **fixed (coverage)** / R1 (timing) | 4 hosts + fd + tmux + transcript + bms2 note; post-copy re-check not repeated before `mv`. |
| F4 order/03:30 | **fixed** | "Order/limits" paragraph. |
| F5 single-file entries | **fixed** | all 7 now skip. |
| F6 ceph_lwindett | **fixed** | skip, unreadable root:root 0700. |
| F7 .conda | **fixed (skip)** / R4 (reason wording) | skip under the conda row. |
| F8 evidence boundary | **fixed** | six trees skipped; `enl_preparation` also skipped. |
| F9 MOVE_LOG/floor action | **fixed** | steps 2 and 8. |
| F10 manifest/git normalisation | **partially fixed** / R2 | manifest normalised; `git worktree list \| sort` still embeds the absolute path. |
| F11 _to_delete/guards | **fixed** | steps 3, 6, failure rule. |
| F12 pinned citation | **fixed** | `r1_prepare` now evidence-based; provenance note says no pin hit; A7-F10 no longer mis-cited. |
| F13 whole-tree venv skips | superseded (conservative) | trees now skipped deliberately; benefit deferred, no safety issue. |
| F14 totals | **fixed** | 19.7 GB, 61 skips. |
| F15 759618 provenance | noted | provenance note added; raw transcript still not attached (acceptable, no move impact). |
| F16 .ollama/ollama | **fixed** | skipped as empty. |
| F17 provenance | **partially fixed** | note lists inputs; file still untracked — commit or record sha256 before execution (cosmetic). |

### R.3 Remaining findings (execution-time; applied inline, no new review round needed)

| ID | Sev | Finding and evidence | Exact inline fix (apply during execution) |
|---|---|---|---|
| R1 | **MINOR** | **The in-use re-check is not repeated after the copy, immediately before `mv`.** Runbook §1.4 step 3: "Make sure nothing has started using X since §1.1 (repeat that check)" — *after* verify, before the rename. The revised plan runs the check only as step 1, before the rsync (L92); a process that starts using the entry during a multi-minute copy (e.g. 9,389-file `hcp_xopt_20261107`, 7.38 GB `work`) would then continue on the `_to_delete` inode after the rename — the §0.5 STOP case. | Insert a **step 5b** (same commands/hosts/transcript as step 1) between step 5 (Verify) and step 6 (Retire): if a new hit appears under `/ceph/dwong/<X>`, **do not rename** — leave both copies, record `verdict=skipped_in_use`, continue with the next entry. |
| R2 | **MINOR** | **`git worktree list \| sort` is still compared with absolute paths.** Step 5 (L96) keeps `git -C <path> worktree list \| sort` "equal on both sides"; the first token is `/ceph/dwong/<X>` vs `/work/dwong/<X>`, so the lines are never equal for a normal repo and the git verification would fail for all 9 moves (all are git trees). The SHA manifest is correctly path-normalised; only this check was not. | In step 5, compare `git -C <path> worktree list --porcelain` with the `worktree ` path line stripped (or compare only `rev-parse HEAD` + `status --porcelain \| wc -l` and keep `worktree list` as a recorded artefact). One-line edit; no re-review needed. |
| R3 | **NIT** | `raw/entry_stats.tsv` is unchanged (SHA `5957f2ff…`) and its four rows are still malformed (`lt64k` > `files`, `max` empty), while the plan's provenance lists "`raw/entry_stats.tsv` (4 rows corrected from direct measurement…)". The plan's numbers are correct; the input file is not. | Either correct the four rows in `entry_stats.tsv`, or reword the provenance to "the four `entry_stats.tsv` rows are malformed; this plan uses direct re-measurements (190/66.03 GB; 1/4.68 GB; 1/3.03 GB; 1/22.67 MB)". |
| R4 | **NIT** | The `.conda` skip reason says "conda environment root — relocating breaks absolute paths … not a plain cache", while `entry_stats.tsv` records `venv_or_conda=no, cache_like=yes`. Skipping is the safe side, but the stated reason contradicts the recorded flag. | State "conservative skip: name/role ambiguous between a conda package cache (`venv_or_conda=no`, `cache_like=yes`) and an environment root; not worth the risk tonight", or record the `ls .conda` check that decided it. |

### R.4 Order, conditions and residual risk

- **Order the plan prescribes and I accept:** largest-first as listed, **one entry at a time** — `work`
  (7.38 GB), `hcp_xopt_20261107` (4.32), `hcp_xopt_20261106` (3.85), `arXiv-v1-polished-extended-preprint`
  (2.61), `y19_host` (0.33), `zc_host` (0.32), `megz_timing_host` (0.31), `megz_host` (0.30),
  `megz_r1_host_20261014` (0.26); stop starting new moves at **03:30 CET**; not-started entries are
  recorded as not done.
- **Ordering caution:** `work` is **7.38 GB for 140 files**, and ~7.37 GB of that sits in its 15 large git
  objects — it is the largest time cost for the smallest inode benefit of the night. Least-risk alternative
  if the clock is tight: do `hcp_xopt_20261107`/`hcp_xopt_20261106` (9,389/6,308 files) and
  `arXiv-v1` (7,775 files) first (the actual small-file wins), then the four host-checkout trees, and leave
  `work` for last — dropping it first would cost the least value if 03:30 approaches. Do not let moves
  delay probes or the 05:30 VPN stop.
- **Conditions of acceptance (mandatory, inline):** apply **R1** (repeat the in-use check as step 5b,
  immediately before the first `mv`) and **R2** (normalise `worktree list` before the first git
  verification). These are protocol-text edits at execution time; they do not need another review round —
  same convention as the runbook review's accepted inline points. R3/R4 are wording/evidence fixes.
- **Residual risk I carry:** (1) `bms2` is not checked (recorded; unverified host, author question);
  (2) the brief `mv`→`ln -s` window still exists — a user that starts in that window lands on the original
  inode; the step-5b check and the preserved `_to_delete` original bound the damage; (3) `/work` is a
  shared 1.4 T filesystem — the per-entry 210 G gate covers other users' growth; (4) the four
  `entry_stats.tsv` malformed rows persist (R3) — use the plan's re-measured numbers, not the TSV columns;
  (5) coverage is now conservative (19.7 GB vs 50.2 GB; `enl_preparation`, the tiny directories and the
  six evidence-boundary trees stay on `/ceph`) — the small-file goal is only partly met tonight, which is
  the right trade for evidence safety; (6) moved originals double their space in `_to_delete` until the
  author retires them (346 T free on `/ceph`, nothing deleted); (7) `MOVE_PLAN.md`/inputs are untracked —
  commit or bind by SHA-256 (`f5e1f442…`) in the report.
- **Verification of the no-deletion rule and the author's instruction:** re-checked and unchanged — copy →
  verify (count/bytes/path-normalised SHA-256 manifest/git state) → re-check in-use → `mv` original to
  `/ceph/dwong/_to_delete/<X>.moved_20261114` → `ln -s /work/dwong/<X> /ceph/dwong/<X>` → verify through
  the old path; failure leaves the source untouched and retires the partial `/work` copy by move; **no
  `rm` anywhere**; the 15 % disk STOP is wired into the loop. The plan is materially correct and safe.

**Moves may begin** once R1 and R2 are applied inline (do them before the first entry), in the order above
with the caution stated. No further independent review round is required for these two one-line
execution-time edits.

## Author-requested confirmation (verification metric + extra checks)

**Reviewed (worktree, read-only; no SSH):** `moves/move_entry.sh` v2 (SHA-256
`dc6bf23223238454bae18e7bc3a4e5b229cd880e5be1b8ac1faf2f838acf2abb`), `moves/verify_pair.sh`
(SHA-256 `8f98db03dbbafe7ab605653492d06ab3a9c5feade98a3548373a50200fb9b96d`), `MOVE_PLAN.md`
revision 2 with R1/R2 applied (SHA-256 `76a8329698785a3277e6bdd228f1e0c9f9876c765a9437b8279ad0db55343aa4`),
and the disclosed deviation in `docs/r1/reports/HTCONDOR_PREP_20261114.md` §2. `MOVE_LOG.tsv` /
`MOVE_BACKFILL.tsv` live on the cluster under `/work/dwong/htcondor_prep_20261114/moves/`; I cannot
read them without SSH, so the v1 rows for the 4 completed moves are checked through the script and
the report's disclosure, not from the live TSV.

**Confirmation (one sentence):**
> I confirm that changing the verification byte metric from `du -sb` to the sum of file-content bytes
> (`find -type f -printf '%s'`), together with file count and the path-normalised per-file SHA-256
> manifest and the added directory count, symlink-list SHA-256 (path → target) and permission-list
> SHA-256 (mode + path), is correct and safe: content identity is still fully checked by the manifest
> and count (the `du -sb` mismatch was a CephFS directory-`st_size` artefact, not a content
> difference), the false negative could not have hidden a real content difference, and the
> no-deletion rule (retire by move, never `rm`) is unchanged.

**Backfill method:** comparing `/ceph/dwong/_to_delete/<X>.moved_20261114` with `/work/dwong/<X>` is
methodologically equivalent to the pre-rename comparison provided the retired original has not been
written to since the rename; nothing writes there (the old path is now a symlink to the `/work` copy,
and step 1/5b guard against a pre-existing user), and any process that had held the original inode
before the rename would appear as a backfill mismatch — it exposes that residual risk rather than
hiding it.

**Remaining MINOR (does not block):** M1 — on the "in-use appeared after verify" path
(`move_entry.sh` L82–86) the script exits without a `MOVE_LOG.tsv` row (the accepted R1 text says
record `skipped_in_use`) and leaves the `/work/dwong/<X>` copy in place; a later retry then hits the
destination-exists guard (L48) unless `RESUME=1` is used. Fix: append the `skipped_in_use` row and
either keep the copy deliberately for `RESUME=1` or retire it to
`/work/dwong/_to_delete/<X>.inuse_<UTC>` with the usual collision guard (a move, no deletion).

**NITs (next pass):** (a) `MOVE_PLAN.md` steps 5/8 still say "total bytes" and the old 16-column
MOVE_LOG list — update to "file-content bytes" and the v2 20-column schema so the accepted plan text
matches `move_entry.sh` v2; (b) the `.failed_<TS>` retirement move (L78) has no `test -e` collision
guard and `|| true` can hide a failed retirement; (c) when `inuse_hosts.txt` is absent the fallback
string is used as a filename in `tr < "$HOSTS"` (L36/L79/L91), so `inuse_hosts` records empty instead
of "(no host transcript)". None of these changes content identity or the no-deletion rule.

**Scope note:** content identity is complete (file count + per-file SHA-256 + content bytes); ACLs,
xattrs, hardlink identity and mtimes are copied by `rsync -aHAX` but not compared — metadata, not
content; add `getfacl`/`getfattr` hashes only if full metadata identity is wanted.

VERDICT: ACCEPTED
