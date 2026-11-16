# MOVE_LOG notes — schema history, verification change, confirmations

**MOVE_LOG schema v1** (rows for hcp_xopt_20261107, hcp_xopt_20261106, arXiv-v1, y19_host): 16 columns, kept untouched in `MOVE_LOG.tsv.v1.20261113T234151Z`. Their content checks passed at move time (file count, file bytes, path-normalised SHA-256 manifest; git state where a repo existed). They were backfilled with the v2 checks (`MOVE_BACKFILL.tsv`).

**MOVE_LOG schema v2** (current `MOVE_LOG.tsv`): 20 columns — `entry, bytes, files, dirs, pre_free_GiB, floor_GiB, copy_rc, count_equal, bytes_equal, dirs_equal, symlink_sha_equal, perm_sha_equal, manifest_sha256, git_checks, inuse_hosts, moved_to, symlink_ok, old_path_ok, verdict, note`. It adds the author's 14 Nov checks: directory count, symlink-list SHA-256 (path → target), permission-list SHA-256 (mode + path).

## Verification-metric change (author instruction 14 Nov ~00:47 CET; confirmed by the same reviewer)

- **Why:** the plan's "total bytes" used `du -sb`, which on CephFS counts the directory `st_size` (recursively sized), so `/ceph` and `/work` directory entries differ even for identical content. The first move (hcp_xopt_20261107) failed its byte check while its **file count and SHA-256 content manifest were equal** — a false negative, not a content difference.
- **Change:** total bytes are now the sum of file-content bytes (`find -type f -printf '%s'`), compared together with file count, path-normalised per-file SHA-256 manifest, directory count, symlink-list SHA-256 and permission-list SHA-256.
- **Reviewer confirmation (verbatim, 14 Nov, `HTCONDOR_MOVE_PLAN_REVIEW_20261114.md` "Author-requested confirmation"):**
  > "I confirm that changing the verification byte metric from `du -sb` to the sum of file-content bytes (`find -type f -printf '%s'`), together with file count and the path-normalised per-file SHA-256 manifest and the added directory count, symlink-list SHA-256 (path → target) and permission-list SHA-256 (mode + path), is correct and safe: content identity is still fully checked by the manifest and count (the `du -sb` mismatch was a CephFS directory-`st_size` artefact, not a content difference), the false negative could not have hidden a real content difference, and the no-deletion rule (retire by move, never `rm`) is unchanged."
- **v2.2 refinement (disclosed):** the volatile git index cache (`*/.git/index`) is excluded from the content SHA manifest, because `git status` (part of the verification itself) refreshes that file and would otherwise cause a false content mismatch. Repo identity is still checked by `HEAD` + `git status --porcelain` count on both sides. The first `zc_host` copy failed exactly on `.git/index` (8014/8014 files and 322,815,669/322,815,669 bytes equal, 3 differing .git/index lines); it was retired to `/work/dwong/_to_delete/zc_host.failed_*` (no deletion) and re-copied/verified under v2.2.

## Method note (backfill)

`match_pair`/`verify_pair.sh` compares the retired original `/ceph/dwong/_to_delete/<X>.moved_20261114` with `/work/dwong/<X>` on the same six checks. It is the same pair of trees the pre-rename check compared, and nothing writes to `_to_delete`; a pre-rename holder of an original inode would surface as a mismatch.


## Outcome after the night's first block (14 Nov 00:57 CET)

- **8 entries moved** (hcp_xopt_20261107, hcp_xopt_20261106, arXiv-v1-polished-extended-preprint, y19_host, zc_host, megz_timing_host, megz_host, megz_r1_host_20261014) with symlinks back; **backfill 8/8 ok** on file count, file-content bytes, directory count, symlink-list SHA, permission-list SHA and file SHA manifest (`MOVE_BACKFILL.tsv`).
- **`work` not moved**: `/work` does not support POSIX ACLs and `/ceph/dwong/work` carries them; `rsync -A` failed with `set_acl: ... Operation not supported`, rc 23. Per the no-deletion rule the partial `/work` copy was retired to `/work/dwong/_to_delete/work.failed_<UTC>` and the original remains untouched. Question Q12.
- **Two false-negative incidents, both recorded, neither hidden:** (1) the first move's `du -sb` byte mismatch (CephFS directory `st_size`); (2) `zc_host`'s first cut differed only in `*/.git/index`, a cache file that the verification's own `git status` rewrites — the copy was retired and re-made, and the content manifest now excludes that cache (repo identity still checked by HEAD + porcelain). The first backfill attempt was run before the exclusion was actually in the script; its file was preserved as `MOVE_BACKFILL.tsv.first_attempt_<UTC>` and the corrected backfill replaces it.
