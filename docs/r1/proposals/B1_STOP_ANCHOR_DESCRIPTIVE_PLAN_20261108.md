# B1 STOP: B1-only anchor descriptive inspection — review only

**Author permitted a read-only explanation, not a rerun, gate recomputation, reading sweep evaluation audit values from seeds 7006–7010, scene modification, or restoration. This exact plan requires independent review before any host action.** Source inspection and a separate independent source check (`/root/audit_guard_review` message; record its eventual review) find that frozen `68357d3d` config explicitly uses B1 instance seeds 9001–9004 and B1 audit seeds 9101–9104. `runtime.py:437, 920–927` validates/binds them to the B1 worker job; `campaign.py:271–279` generates each B1 audited proposal with that job's audit seed list and corresponding metrics; its root manifest records job binding/hash and identities. These B1-only paths are distinct from sweep evaluation seeds 7006–7010. The 01:19:49 UTC accepted STOP observation recorded exactly 36 completed B1 root keys and no current root. This is a process provenance argument, not cryptographic proof against a hostile writer, earlier corruption or a post-check concurrent change.

The STOP branch in `exam_runner.py:213–219` computes the paired bootstrap in memory and raises before `:369` assigns its returned comparison to `anchor_gate`. This plan does not search other free-form logs or claim the comparison was never persisted elsewhere. It does **not** call `paired_instance_bootstrap`, compare the two anchors, calculate a confidence interval or produce a gate verdict. It reports only the number of audited proposals, their within-root descriptive mean `delta_audit`, and producer-recorded `trials/evaluated/invalid/duplicates/noops/parse_failed` for random-valid and scripted, separately for each of three nodes and each B1 instance seed 9001–9004. `invalid` is a recorded edit diagnostic, not the number of failed audit seeds; failed-audit counts remain NOT CHECKABLE. No qwen manifest, `root_trials`, event ledger, audit cache or raw metric vector is opened or output. No value is selected to change the STOP.

## Trust boundary and read scope

The code reads the **full JSON bytes** of `batch_state.json`, then for exactly 24 fixed random-valid/scripted roots reads `job.json` followed by `campaign_manifest.json`. Before opening each manifest it requires the job to bind the exact reviewed HEAD, B1 mode, node, instance seed and audit seeds 9101–9104, matching the authority config's exact B1 seeds and rule hash. It requires the 36 expected completed root keys and recorded STOP reason, binds every selected manifest path and SHA to `batch_state`, then checks the manifest's SHA-bound job, binding, phase, anchor, node, instance, completion, audit seed list and each proposal's identity before **any output**. It reports no raw per-seed vectors. A wrong job seed, including 7006–7010, stops before the corresponding manifest is opened; wrong manifest identity/hash/seed stops without reporting descriptive values. Duplicate JSON keys, symlinks, unowned/nonregular files, missing `O_NOATIME`, and changed file identity/mtime/size during each read cause STOP. Output uses `O_NOATIME` and no file is opened for writing.

Full-byte reads cannot first prove the absence of forbidden values in a corrupted or maliciously substituted file: an altered file would be read for its digest before mismatch is detected. The boundary relies on the reviewed B1 producer, fixed unique paths, the preserved stopped state and recorded hashes under the project's cooperative process assumptions, not adversarial same-UID protection. **Do not run if that provenance is doubtful or the operator cannot accept this disclosed limitation under the author's prohibition.** The script neither opens nor infers values from the known 7006–7010 sweep-evaluation files. A concurrent change after an individual file's check is not excluded. Preserve the stopped scene and all raw files.

## Candidate and local tests

Source `B1_STOP_ANCHOR_DESCRIPTIVE_20261108.py` SHA-256 `4605887538f62614ce153365306f01920a65e3e74a28529a4bfa378254b224e9`; local SSH wrapper `/private/tmp/b1-stop-anchor-descriptive-20261108.local.sh` SHA-256 `c52136dbf63dde108ead0e9f97643f8585d2b21d0460b5aae2ec7e60546d201b`. The wrapper verifies the source SHA, streams no stdin, uses clean environment and `/usr/bin/python3 -I -B`, creates a unique private local capture, and records actual SSH exit in log and separate rc. The read-only script uses `O_NOATIME` and refuses if unavailable; there is no fallback that might update file access times. A failure or uncertain SSH result leaves the scene intact and is STOP without automatic retry. Code returns all descriptive output only after validation of all 24 roots; the completion marker/rc alone is not independent acceptance.

Four local synthetic tests passed in a fresh pytest base: complete 24-root fixture, wrong job audit seeds stop before the corresponding manifest opens, tampered manifest hash and wrong manifest seeds refuse. On Mac, where `O_NOATIME` is unavailable, tests substitute a zero flag **only in the synthetic fixture**; they do not qualify Linux filesystem behavior. No host, real data, model, gate or GPU was accessed. The metadata-only alternative remains available if the above process boundary is not accepted, but it cannot explain numeric direction. An independent reviewer must inspect this exact script, test paths, full-byte-read limitation, and actual retained result before any conclusion.

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
SCRIPT=/private/tmp/paper-b-b1-stop-readonly-plan-20261108/docs/r1/proposals/B1_STOP_ANCHOR_DESCRIPTIVE_20261108.py
EXPECTED=4605887538f62614ce153365306f01920a65e3e74a28529a4bfa378254b224e9
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED" ] || exit 1
CODE=$(python3 -c 'import base64,sys;print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$SCRIPT") || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-stop-anchor-descriptive-20261108.XXXXXXXX) || exit 1
set -C
exec 3> "$OUT/ssh.log"
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
if ssh -n -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=3 tasl7 "exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /usr/bin/python3 -I -B -c 'import base64;exec(base64.b64decode(\"$CODE\"))'" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nSSH_EXIT=%s\n' "$rc" >&3 || exit 1
printf '%s\n' "$rc" > "$OUT/ssh.rc" || exit 1
shasum -a 256 "$SCRIPT" "$OUT/ssh.log" "$OUT/ssh.rc" || exit 1
[ "$rc" -eq 0 ] || exit "$rc"
grep -qx DESCRIPTIVE_CAPTURE_COMPLETE "$OUT/ssh.log" || exit 1
printf 'PRELIMINARY_RECEIPT_FOR_INDEPENDENT_REVIEW=%s\n' "$OUT"
```

Only after source/plan review and fresh assessment of the stated provenance and authorization may the operator run this file once. No earlier STOP or restriction is waived. If any mismatch or uncertainty arises, report it and preserve the scene; no automatic retry.
