# Mac-local retained atomic rename capability probe — draft, 7 November 2026

AI-assisted (Codex). **DRAFT; not independently reviewed or executed.** This engineering-only check is intended to qualify the Darwin `renameatx_np` operations used by the DRYRUN snapshot code in `r1/exam/b1_state_preserve.py`. Script `docs/r1/proposals/mac_rename_probe_20261107/probe.py` SHA-256 `b9af599e48af99cbc428999f71d74fd1334adc4b57f8d6502272e6d9b8c9712d`. No host, GPU, model, experiment, or real filesystem capability operation has been performed for this draft. The static Python AST parsed successfully.

The one-shot script opens `/private/tmp` without following its final component, exclusively creates `/private/tmp/paper_b_mac_rename_probe_20261107_f4e6b9c2187a4d52` and a private `_to_delete`, then exclusively creates two owned files. It checks Darwin `RENAME_EXCL` (`0x4`) refuses an existing target, moves A across directories into `_to_delete`, and checks `RENAME_SWAP` (`0x2`) exchanges B and A across directories. It checks inode identities and bytes after each operation and calls fsync on both directories following moves. After success, A remains at `b`, B at `_to_delete/c`; no cleanup is performed. If directory fsync or any other operation fails, the script stops with all existing names and bytes preserved to the extent the underlying operations permit; an error after rename may leave a changed but retained arrangement. No retry or cleanup is authorized.

Prior to any execution, a fresh independent reviewer must inspect the exact script and capture command, including Darwin API flags, path/owner checks and all failure paths. Confirm the exact committed script SHA, clean checkout, no existing target probe directory or capture path, and sufficient local free space. Use a site-qualified Python interpreter and `/bin/bash`, and do not run an experiment. Any collision, incomplete output, signal, write/close/hash failure, nonzero status or ambiguity is STOP: retain all output and files and do not rerun. The process does not test actual B1 runner, concurrency, permissions on other filesystems, durability after a crash, or Mac/Python behavior outside the examined calls.

**Exact proposed one-shot capture**, to be used only after independent acceptance:

```bash
set -C
capture=/private/tmp/paper_b_mac_rename_capture_20261107_f4e6b9c2187a4d52.txt
if exec 3>"$capture"; then :; else
  printf '%s\n' 'STOP: capture exists or cannot be created' >&2
  exit 1
fi
if python3 -I -S -B docs/r1/proposals/mac_rename_probe_20261107/probe.py >&3 2>&1; then
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
  printf '%s\n' 'STOP: capture hash failed; retain scene' >&2
  exit 1
fi
exit "$task_probe_status"
```

A new independent result reviewer must inspect complete capture and footer, hashes, identities and all error lines before the result is used. This check cannot authorize full pytest, Stage A→B1 recovery, a harness pin change or B1 launch; those separate gates remain open.
