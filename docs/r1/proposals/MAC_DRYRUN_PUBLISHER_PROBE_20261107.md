# Mac-local DRYRUN batch-state publisher probe — draft, 7 November 2026

AI-assisted (Codex). **Draft; no execution or independent acceptance.** This one-shot, Mac-local ENGINEERING_ONLY check exercises the actual `publish_dryrun_state` and `existing_identity` functions from committed `r1/exam/b1_state_preserve.py`, source SHA-256 `c1deccb0795d5b30643a7b50b62fceed7eecb2ca440cb22005c7491d9d03942c`. The exact script `mac_publisher_probe_20261107/probe.py` SHA-256 `0ca7439945cdc2bf86b0d3627ebaa83e30d3e1a7d1f3059faff7916f42310bdc` loads and executes those source bytes after verifying that hash; it does not reimplement the publisher. Source path is derived from this committed checkout. `python3 -I -S -B` prevents ordinary Python bytecode writes and user-site imports; it is not a kernel write sandbox.

The script opens the root-owned sticky `/private/tmp` and verifies its opened/named identity. It exclusively creates a fresh `paper_b_mac_publisher_probe_20261107_4dfe33725b0140b8` directory and checks ownership, mode and device. It calls the real publisher first with `expected_identity=None` and then with the returned first identity, on `batch_state.json`. It checks that the canonical state has the second JSON bytes/inode and the sole file in its `_to_delete` directory retains the first JSON bytes/inode. It prints identities, hashes and retained name. The publisher creates exclusive candidate files, uses Darwin's `renameatx_np` EXCL and SWAP through the reviewed DRYRUN path, fsyncs, and retains old data. It does not intentionally delete, truncate or replace old bytes; all directories/files remain on success or failure. A failure after a successful rename can leave an intermediate retained arrangement. `finally` closes descriptors, and the process exits; it does not perform cleanup or retry.

**Preconditions.** Before invocation a fresh independent reviewer must accept the exact script, actual publisher dependency, capture and every error path. The operator must inspect a clean committed checkout, verify both SHA values, inspect `/private` and `/private/tmp` ownership/type/sticky permissions and local disk, confirm both fixed root and capture paths are absent including symlinks, and verify the selected Mac-local `python3`. Use a single cooperative private test root; same-UID concurrent modification is outside this check. Any collision, nonzero status, missing output/footer, signal, capture error, failed hash or ambiguity is STOP: retain every file and output, never clean up or retry. No local user-data or existing project result is modified; incidental Python/OS effects are not comprehensively traced.

After independent review, from the exact clean checkout, use `/bin/bash` for this single invocation:

```bash
set -C
capture=/private/tmp/paper_b_mac_publisher_capture_20261107_4dfe33725b0140b8.txt
if exec 3>"$capture"; then :; else
  printf '%s\n' 'STOP: capture exists or cannot be created' >&2
  exit 1
fi
if python3 -I -S -B docs/r1/proposals/mac_publisher_probe_20261107/probe.py >&3 2>&1; then
  task_probe_status=0
else
  task_probe_status=$?
fi
if printf '\nPROBE_EXIT_STATUS=%s\n' "$task_probe_status" >&3; then :; else
  printf '%s\n' 'STOP: cannot record probe status; retain scene' >&2
  exit 1
fi
if exec 3>&-; then :; else
  printf '%s\n' 'STOP: capture close failed; retain scene' >&2
  exit 1
fi
if shasum -a 256 "$capture"; then :; else
  printf '%s\n' 'STOP: capture digest failed; retain scene' >&2
  exit 1
fi
exit "$task_probe_status"
```

Record the UTC time, exact checkout HEAD, interpreter, both source/script hashes, capture SHA and complete output. A fresh independent result reviewer must inspect source bindings, retained capture and two identities/bytes before this is used. The check is limited to two successful sequential calls on this Mac filesystem, not crash durability, asynchronous STOP, full pytest no-deletion, Stage A→B1 recovery, production B1 Linux behavior or launch approval. The user explicitly forbids deletion and old data must remain in `_to_delete`; this test cannot waive any author decision or B1 gate.

Static validation only: Python AST parse and `git diff --check`; the script and actual publisher were not executed, and no real file rename or host, model, GPU or experiment action occurred.
