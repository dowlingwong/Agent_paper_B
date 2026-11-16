# Read-only archive/tree comparison before the 60ec worker test

**Candidate requiring a fresh independent review of this new checker before execution.** This is an engineering-test preflight, not a new provenance root or B1 launch gate. It reads the two retained archives and their extracted trees; it creates no remote file, does not delete anything and invokes no GPU, model or worker. Keep the original evidence and do not retry automatically after a failure. As usual, use it only after the existing author-scoped host and no-preemption checks.

The local checker is `docs/r1/proposals/B1_ENGINEERING_VERIFY_ARCHIVE_TREE_20261107.py`, SHA-256 `54a381e71b5a394e1b8615e2b8a5987d6bd43909fc857130acb280b22dae5920`. It verifies each archive's full SHA-256, rejects unsafe types, paths and duplicates, and compares the bytes of every extracted regular file against the corresponding archive member. It rejects unexpected files/directories and symlinks, except that ordinary regular `.pyc` files directly under `__pycache__` directories whose parents are archive directories are listed as `CACHE`; those cache bytes are not considered part of the verified source. This is a cooperative point-in-time check, not an atomic snapshot or proof against a malicious concurrent same-UID process. It does not verify file modes.

Use the SHA-bound checker in the review workspace below with the exact single existing remote engineering run; this checker is not part of the older `60ec` source checkout. No user-provided text is interpolated into the remote command:

```bash
set -u
umask 077
CHECKER=/private/tmp/paper-b-wrapper-site-result-review-20261107/docs/r1/proposals/B1_ENGINEERING_VERIFY_ARCHIVE_TREE_20261107.py
test "$(shasum -a 256 "$CHECKER" | awk '{print $1}')" = 54a381e71b5a394e1b8615e2b8a5987d6bd43909fc857130acb280b22dae5920 || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-worker-tree-check-20261107.XXXXXXXX) || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'python3 -I -B - /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/paper.tar /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/paper f9d2813fa5a1654c7a0785c08738dd7c23d506f7e2a0c2c0cf90401ae9ace842 /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/harness.tar /home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/harness 70270971de13dd5c02531bd9c23c90e3179db1862f8e5e8543b23d8c2fb8e2a6' < "$CHECKER" > "$OUT/tree-check.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$OUT/exit.txt"
shasum -a 256 "$OUT/tree-check.log" "$OUT/exit.txt"
printf 'Private capture: %s; exit=%s\n' "$OUT" "$rc"
```

**Acceptance:** exit 0, exactly two `PASS` lines with paper 263 files and harness 504 files, no STOP or unexpected error, and each `CACHE` path retained in the local capture for review. An absent or unreadable member, changed bytes, hash mismatch, link, special file, disallowed extra entry, SSH error or incomplete output is STOP; retain the log and do not run the worker or automatically retry. The checker prints all allowed cache paths, including any existing `r1/__pycache__` paths. `CACHE` entries are not evidence of source equivalence.

Python's `PYTHONDONTWRITEBYTECODE=1` prevents writes but does not prevent reading an existing `.pyc`. Therefore before the second remote real-worker block, check that each path component from `/home` through `$base/tmp` is a real directory and not a symlink, then require both `test ! -e "$base/tmp/worker-pycache"` and `test ! -L "$base/tmp/worker-pycache"`; add `PYTHONPYCACHEPREFIX="$base/tmp/worker-pycache"` to that block's existing `env -i` invocation, keeping `PYTHONDONTWRITEBYTECODE=1`. This directs cache lookups to a fresh absent location while disabling cache creation; do not remove existing caches. Check the host venv identity, sibling `python3`, prefix/dependency imports, current host resources and no-preemption immediately before the reviewed worker invocation. These checks do not prove stability after observation and do not replace any B1 launch condition.

Local verification: the checker compared the actual 60ec paper archive and a locally extracted pinned harness archive successfully (263 and 504 files); it recorded 22 existing local harness cache entries. Separate test-owned synthetic archive/trees passed when identical, recorded a root-level cache, and stopped on altered bytes and an unexpected symlink. Test material was retained; no host was contacted. The new checker and the cache-prefix adjustment require independent review before use.
