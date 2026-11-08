# B1 STOP: one-shot anchor metadata inspection — review only

The author explicitly allowed a read-only inspection of saved B1 anchor evidence, without an experiment, gate recomputation, reading evaluation audit values from seeds 7006–7010, modifying the STOP scene or restoring B1. **This plan has not been run and requires independent review of exact scripts before site use.** It deliberately inspects only filesystem metadata, never any file content, because root/candidate manifests and ledgers combine fields and the actual files have not been independently established safe to read field-by-field. The accepted STOP capture already states the failure and the 36 completed root keys; this plan cannot establish actual failed-audit counts, per-instance deltas, comparison interval or its cause. They remain NOT CHECKABLE under this method; do not infer zero or recompute the gate. A further narrowly reviewed method would be needed before any safe value-level inspection.

Static source at frozen `68357d3d`: `exam_runner.py:213–225` computes `paired_instance_bootstrap` in the local `comparison` variable and raises on `difference_lower <= 0` before returning; `:369` assigns `runner.state['anchor_gate']` only after the call returns. This explains why the failure branch does not itself save that comparison to `anchor_gate`; it does not establish whether some other artifact contains a value. In `campaign.py`, candidate/root manifests combine `audited_proposals` with audit seeds and metrics. B1's authorized instance seeds are 9001–9004 and its own audit seeds are 9101–9104; neither is a reason to scan a mixed unknown file for forbidden evaluation-seed values. The seed numbers 7006–7010 are not authorized for reading or output. The actual persisted manifest contents are not known merely from filename or size.

## Exact one-shot invocation

`B1_STOP_ANCHOR_METADATA_20261108.py` SHA-256 `23da37c3f802da6bdadac36af3e493ea24917e0f9464ebf1fc07d8ff264188fc` enumerates only the fixed STOP root `/home/dowling/exam-x/work/b1_6835_20261108_a`, the three named anchors, three nodes and instance seeds 9001–9004. It opens only directory descriptors (`O_DIRECTORY|O_NOFOLLOW`) and uses `stat(..., follow_symlinks=False)` for the fixed candidate/root filenames. It outputs type, size, owner, dev/inode and mtime only; missing paths, symlinks or permission errors are `NOT_CHECKABLE`. It neither opens a regular file for reading nor performs hashes, JSON parsing, ledger counting, value filtering or computation of comparison statistics. Existing filesystem metadata is non-atomic and file sizes alone are not audit failure counts. Local synthetic tests assert directory descriptors only, no builtins file open, no content output and symlink refusal: **3 passed**. No host was contacted.

The local `/private/tmp/b1-stop-anchor-metadata-20261108.local.sh` SHA-256 `fcde9db74de74e1fba5b3fa552bb21454a60f0dbf2943d0ce6af76c012e98833` verifies that source SHA, uses clean environment and `/usr/bin/python3 -I -B`, and captures real SSH exit in a new private log and separate rc. It sends no stdin or signal and makes no remote file write. The output and capture hashes are private. On SSH failure, incomplete capture or any unknown site state, preserve all material and STOP; do not rerun automatically. The completion marker and rc 0 only establish the block reached its end, not completeness of all metadata, correctness of the anchor criterion, or current worker absence.

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
SCRIPT=/private/tmp/paper-b-b1-stop-readonly-plan-20261108/docs/r1/proposals/B1_STOP_ANCHOR_METADATA_20261108.py
EXPECTED=23da37c3f802da6bdadac36af3e493ea24917e0f9464ebf1fc07d8ff264188fc
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED" ] || exit 1
CODE=$(python3 -c 'import base64,sys;print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$SCRIPT") || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-stop-anchor-metadata-20261108.XXXXXXXX) || exit 1
set -C
exec 3> "$OUT/ssh.log"
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
if ssh -n -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=3 tasl7 "exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /usr/bin/python3 -I -B -c 'import base64;exec(base64.b64decode(\"$CODE\"))'" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nSSH_EXIT=%s\n' "$rc" >&3 || exit 1
printf '%s\n' "$rc" > "$OUT/ssh.rc" || exit 1
shasum -a 256 "$SCRIPT" "$OUT/ssh.log" "$OUT/ssh.rc" || exit 1
[ "$rc" -eq 0 ] || exit "$rc"
grep -qx METADATA_CAPTURE_COMPLETE "$OUT/ssh.log" || exit 1
printf 'PRELIMINARY_RECEIPT_FOR_INDEPENDENT_REVIEW=%s\n' "$OUT"
```

Only after independently reviewing this precise plan and confirming the author's authorization/STOP scope may the operator run the local file once. No marker retirement, process signal, manifest read, gate invocation, rerun, or B1 restoration is implied. The independent reviewer must compare the actual output and rc to this plan, record limitations, and avoid requesting or displaying protected values.
