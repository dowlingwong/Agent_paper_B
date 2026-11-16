# MOVE_PLAN (revision 2) — /ceph/dwong -> /work/dwong, small-file entries

**Revision 2** after the pre-execution review `docs/r1/reviews/HTCONDOR_MOVE_PLAN_REVIEW_20261114.md` (VERDICT: NOT ACCEPTED; no BLOCKING, 5 MAJOR). Fixes applied: F1 hf_cache removed (large blob cache); F2 the four previously-unclassified rows added and classified (`hcp_meg`, `models`, `trigger_efficiency.tar.zst`, `round5-titan-c7517f1.bundle`); F3 in-use check expanded (all reachable login hosts, cwd + /proc/<pid>/fd + tmux/screen, transcript recorded); F4 execution order and the 03:30 CET stop added; F5 the seven regular-file entries dropped from moves; F6 ceph_lwindett skipped as unreadable root:root 0700; F7 `.conda` skipped as a conda environment; F8 six evidence-boundary-unevidenced trees skipped conservatively; F9 MOVE_LOG schema added; F10 SHA/git verification path-normalised; F11 `_to_delete` creation and collision guards added; F12 citation corrected; NITs fixed (totals, .ollama, provenance).

**Result: 9 entries to move = 19.7 GB; 61 entries skipped.** All 70 top-level entries of `/ceph/dwong` are classified. `/work` at plan time: 1.4 T size, 385 G used, 1.1 T free (27 % used); the A5 floor is max(15 % of 1.4 T = 210 G, entry bytes + 5 GiB) and is checked before each move.

## Move list (largest first; one entry at a time)

| # | entry | size GB | files | reason |
|---:|---|---:|---:|---|
| 1 | `work` | 7.38 | 140 | working-directory tree; small files (median 544 B, p90 341 kB); cache-like name; not pinned, not evidence |
| 2 | `hcp_xopt_20261107` | 4.32 | 9389 | git source/optimisation tree; 9389 files, median 4.3 kB, 8411 under 64 kB; not pinned, not a results-named directory |
| 3 | `hcp_xopt_20261106` | 3.85 | 6308 | git source/optimisation tree; 6308 files, median 4.4 kB, 5764 under 64 kB; not pinned |
| 4 | `arXiv-v1-polished-extended-preprint` | 2.61 | 7775 | git source/preprint tree; 7775 files, median 3.1 kB; not pinned, not evidence |
| 5 | `y19_host` | 0.33 | 4000 | host checkout tree; 4000 files, median 3.4 kB |
| 6 | `zc_host` | 0.32 | 8014 | host checkout tree; 8014 files, median 2.9 kB |
| 7 | `megz_timing_host` | 0.31 | 2150 | host checkout tree; 2150 files, median 3.6 kB |
| 8 | `megz_host` | 0.30 | 2164 | host checkout tree; 2164 files, median 3.3 kB |
| 9 | `megz_r1_host_20261014` | 0.26 | 1017 | host checkout tree; 1017 files, median 2.6 kB |

## Skip list

| entry | size GB | reason |
|---|---:|---|
| `paper1_dataset` | 185.85 | large-file/data directory (185.85 GB, 105 files, median 1.43 GB) |
| `meg_z` | 84.82 | mostly large model/blob files (84.82 GB; p90 864 MB, max 909 MB) |
| `hcp_meg` | 66.03 | mixed large-blob tree (66.03 GB, 190 files, p90/max 700 MB) |
| `lucid_training_data` | 42.83 | large-file/data directory (42.83 GB, median 45 kB but max 1.79 GB archives) |
| `enl_runs` | 36.41 | results/data tree (36.41 GB) — evidence-adjacent, conservative skip |
| `b1` | 35.45 | B1 engineering/evidence tree (35.45 GB) |
| `jepa` | 29.58 | contains venv — venv rule |
| `tr09_runs` | 28.80 | results/data tree (28.80 GB) |
| `hf_cache` | 19.13 | model/blob cache: 19.13 GB in 27 files (p90 99.6 MB, max 3.99 GB); only ~6 MB is metadata; runbook §1 keeps large files on /ceph |
| `transformer` | 18.16 | contains venv — venv rule |
| `tr09_preparation` | 14.05 | data-preparation tree (14.05 GB) |
| `gain_units_20261028` | 8.92 | contains venv — venv rule |
| `delight_conf` | 5.24 | large-file directory (5.24 GB, 13 files, median 10.8 MB) |
| `models` | 4.68 | named by a pinned path (/ceph/dwong/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf); single 4.68 GB model file |
| `t20s_regen_20261021` | 3.07 | contains venv — venv rule |
| `b2` | 3.05 | B2 tree (3.05 GB) — evidence-adjacent, conservative skip |
| `trigger_efficiency.tar.zst` | 3.03 | single regular file (3.03 GB archive) — not a directory tree; directory-form rsync not applicable |
| `hcp_seal_20261027` | 2.72 | contains venv — venv rule |
| `deepthought_tasks_20261025` | 2.63 | contains venv — venv rule |
| `hcp_runs` | 2.28 | evidence boundary not evidenced — conservative skip (review F8) |
| `r1_batch1_ENGINEERING_ONLY_20261012_E4cC3e` | 2.25 | named by a pinned path (pinned_paths.txt: docs/r1/STATUS.md, BATCH_A handoff) |
| `ORACLE` | 2.03 | evidence boundary not evidenced — conservative skip (review F8) |
| `r1_prepare_20261025` | 1.24 | holds the sweep-1 evidence (C3_sweep_append_only_summary/none, 288 ledgers) and the W2 read; evidence + 66k files |
| `agent-checkpoint-intervention` | 1.00 | contains venv (45361 files, 44k <64 kB) — venv rule |
| `megz_r1_returns` | 0.98 | large-file directory (0.98 GB, 5 files, median 189 MB) |
| `opt` | 0.94 | named by a pinned path (/ceph/dwong/opt/llama.cpp/... in BATCH_B handoff); contains the pinned llama.cpp build |
| `mlst-successor-runs-20260913` | 0.83 | evidence boundary not evidenced — conservative skip (review F8) |
| `DELight_mtr` | 0.77 | evidence boundary not evidenced — conservative skip (review F8) |
| `noise-weighted-subspace-reconstruction` | 0.76 | contains venv — venv rule |
| `meg_env` | 0.39 | venv tree — venv rule |
| `.conda` | 0.37 | conda environment root — skipped conservatively as a conda install (the entry_stats flag `venv_or_conda=no, cache_like=yes` records only the name-based cache guess; R4: the skip is the safe side, not a measured environment test) |
| `paper1_env` | 0.32 | venv tree — venv rule |
| `y19_venv` | 0.26 | venv tree — venv rule |
| `zc_venv` | 0.26 | venv tree — venv rule |
| `tr07_runs` | 0.16 | evidence boundary not evidenced — conservative skip (review F8) |
| `agent_paper_B` | 0.13 | named by pinned paths (BATCH_A handoff) and is the active paper clone (another session) |
| `cresst_u2_audit_20260930` | 0.04 | audit output (evidence-adjacent) |
| `ots_env` | 0.03 | venv tree — venv rule |
| `round5-titan-c7517f1.bundle` | 0.02 | single regular file (22.67 MB git bundle) — file-form move not worth a new branch |
| `r1_bringup_20261025` | 0.00 | engineering bring-up record |
| `nimh_runs` | 0.00 | evidence boundary not evidenced — conservative skip (review F8) |
| `y19_zenodo_git` | 0.00 | tiny git metadata (864 kB) |
| `b3` | 0.00 | small miscellaneous tree (36 files, 600 kB); no evidence/pin/venv signal — move is optional, left out tonight (not worth a move) |
| `y19_zenodo` | 0.00 | tiny zenodo metadata (208 kB) |
| `r1_batch1_ENGINEERING_ONLY_resume_20261012T191238Z` | 0.00 | named by a pinned path (runner_claim path in STATUS) |
| `e12_runtime_20260823_201812` | 0.00 | tiny runtime directory (88 kB) |
| `ollama.log` | 0.00 | single regular file (40 kB) |
| `zc_logs` | 0.00 | tiny log directory (16 kB) |
| `trigger_efficiency.sha256` | 0.00 | single regular file (9.6 kB) |
| `lucid_c5_train.log` | 0.00 | single regular file |
| `y19_logs` | 0.00 | tiny log directory (6 kB) |
| `b3_logs` | 0.00 | tiny log directory (3 kB) |
| `b2_receive` | 0.00 | tiny receive directory (2 kB) |
| `lucid_training_data.gen.log` | 0.00 | single regular file |
| `lucid_c5_l40s.log` | 0.00 | single regular file |
| `lucid_c5_fast.log` | 0.00 | single regular file |
| `ceph_lwindett` | 0.00 | root:root 0700 and unreadable to the account (permission denied already recorded 25 Oct) — cannot copy, skip |
| `.ollama` | 0.00 | empty/near-empty dot directory (0 files, 1 B) — nothing to move |
| `enl_preparation` | 4.88 | data-preparation tree (4.88 GB) — evidence boundary not evidenced, conservative skip |
| `ollama` | 0.00 | empty dot directory (0 files, 9 B) — nothing to move |
| `tr09_receiving` | 0.01 | tiny receiving directory (14 MB, 4 files) — not worth a move |

## Execution protocol (runbook §1.4 + errata A5)

**Order/limits:** largest-first as listed; **one entry at a time**; stop starting new moves at **03:30 CET**; any entry not started by then is recorded as "not done tonight (cut-off)" in `MOVE_LOG.tsv`; the programme never trades a probe or the 05:30 stop for a move.

**Per-entry steps:**
1. **Re-check in-use** (F3): on deepthought run `pgrep -u dwong -a`, and for every pid of dwong read `/proc/<pid>/cwd` and `ls -l /proc/<pid>/fd` (own user only) for paths under `/ceph/dwong/<X>`; check `tmux ls`, `screen -ls`, and `ps -u dwong -o cmd | grep -E "nohup|screen|tmux"`. The same check on the other login hosts where `/ceph/dwong` is mounted — `portal1.etp.kit.edu`, `bms1.etp.kit.edu`, `bms3.etp.kit.edu` — via `ssh` from the Mac; `bms2` is recorded as "not checked: bms2 (unverified host)" if unreachable. The exact commands and outputs go to `raw/inuse_<UTC>.txt`. Also `condor_q dwong -af Iwd Cmd` (pool-wide).
2. **Pre-copy disk gate (A5):** `du -sb` the source, `df -h /work`, `quota -s` (no quota output → /work filesystem capacity 1.4 T is the conservative quota); require `free_after ≥ max(0.15 × 1.4 T, bytes + 5 GiB)`; record `pre_free_GiB`, `floor_GiB` in `MOVE_LOG.tsv`. If it fails: **stop the move programme**, record, report.
3. **Prepare retirement targets:** `mkdir -p /ceph/dwong/_to_delete /work/dwong/_to_delete`; ensure `/work/dwong/<X>` and the retirement names do not exist (unique suffix `_<n>` on collision; abort the entry on unresolved collision).
4. **Copy:** `nice -n 19 ionice -c3 rsync -aHAX --numeric-ids /ceph/dwong/<X>/ /work/dwong/<X>/`; record the rc.
5. **Verify:** file count, **file-content bytes** (`find -type f -printf '%s'` sum — not `du -sb`, which counts CephFS directory `st_size` recursively), **directory count**, **symlink-list SHA-256** (path → target), **permission-list SHA-256** (mode + path) equal; **path-normalised SHA-256 manifest** equal on both sides: `(cd /ceph/dwong/<X> && find . -type f -print0 | sort -z | xargs -0 sha256sum) | sha256sum` and the same under `/work/dwong/<X>`, and also `diff` of the two sorted manifests; for git repos/working trees `git -C <path> rev-parse HEAD` and `git -C <path> status --porcelain | wc -l` equal on both sides (R2: no absolute-path embedding — do not compare `git worktree list` text across `/ceph` vs `/work`). Record the manifest SHA.
5b. **Repeat the in-use check (R1, runbook §1.4 step 3) immediately before the rename**, with the same commands and hosts as step 1, into a second transcript; if a new user appears, do not rename: record `skipped_in_use` and go to the next entry.
6. **Retire and symlink (no deletion):** `mv /ceph/dwong/<X> /ceph/dwong/_to_delete/<X>.moved_20261114` then `ln -s /work/dwong/<X> /ceph/dwong/<X>`; verify no collision first (unique suffix on collision; abort the entry otherwise).
7. **Verify through the old path:** `ls -l /ceph/dwong/<X>` (symlink target), and for git trees `git -C /ceph/dwong/<X> status --porcelain | head`; record.
8. **Append to `MOVE_LOG.tsv`** schema v2 (columns: `entry, bytes, files, dirs, pre_free_GiB, floor_GiB, copy_rc, count_equal, bytes_equal, dirs_equal, symlink_sha_equal, perm_sha_equal, manifest_sha256, git_checks, inuse_hosts, moved_to, symlink_ok, old_path_ok, verdict, note`). Rows produced before the schema change are kept in `MOVE_LOG.tsv.v1.<UTC>` and are covered by the backfill (`MOVE_BACKFILL.tsv`).

**Failure rule (no deletion):** on any verification failure, do not rename; leave the source untouched; move the partial `/work` copy to `/work/dwong/_to_delete/<X>.failed_<UTC>` (a move, never `rm`; unique suffix on collision); record `verdict=failed` and continue with the next entry.

## Provenance / notes
- Inputs: `raw/inventory.tsv`, `raw/entry_stats.tsv` (**note: the raw stats file still contains the four malformed rows; the plan uses the re-measured numbers below, R3**): `hcp_meg` 190 files/66.03 GB/p90 700 MB; `models` 1 file/4.68 GB; `trigger_efficiency.tar.zst` 1 file/3.03 GB; `round5-titan-c7517f1.bundle` 1 file/22.67 MB), `pinned_paths.txt` (213 lines, 5 branches).
- `r1_prepare_20261025` is skipped because it holds the sweep-1 evidence and the W2 read, not because of a pin hit; `pinned_paths.txt` contains no `/ceph/dwong/r1_prepare_20261025` path (F12).
- The account's one idle job at plan time, cluster 759618, belongs to another session (`/work/dwong/r2_batch/tiny`); it is not ours and no `condor_rm`/`condor_hold` touches it.
- Nothing here deletes anything; the author's instruction for the night ("一律复制核对后原件进 _to_delete/、原路径留软链接，不删任何东西") is the protocol above.
