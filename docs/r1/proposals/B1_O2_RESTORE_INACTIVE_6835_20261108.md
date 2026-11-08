# B1 O2: inactive Track S/P restoration and cooperative start protocol

**Proposal for independent review; no host action.** Scoped to frozen candidate `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb` and run `6835_20261108_a`. It implements the author's normal-completion instruction and accepted O2 marker helper, without adding a cgroup, process supervisor or new author decision. It applies only if the actual pre-handover and post-completion conditions below are established; a past snapshot does not establish current inactivity, proof of STOP creation, or no concurrent starts. Do not execute this proposal until independently reviewed and applicable site checks are completed.

## Facts and no-new-start amendment

The read-only O2 snapshot reviewed at `0b6be87261dce78b3d535f464ff800cf876530e6` found no process matching the checked current-user collector and P.3a patterns, a watcher pane, and no listed GPU compute app; its visibility and timing limits are explicit. It identified `/home/dowling/r1_tracks/out/smoke/manifest.json` as the one watcher-reachable manifest and `smoke/STOP` absent. None of those facts proves global absence, current inactivity, or running watcher bytes. At handover, repeat the actual accepted O2 census and inspect all reachable manifest/STOP targets, the watcher, locks, GPU, P.3a and relevant jobs. If prior S/P state is inactive, restore that inactivity: do not launch S collectors, S server or P.3a solely to perform restoration. If active state is found, this inactive-state procedure is inapplicable; use its separately reviewed safe-pause/restoration path.

The author said “你继续执行，不用管他。只要能跑就去跑” and directed the ordinary S watcher handover; the approved feature STATUS decision identifies `~/r1_locks/trackx_evidence.active` as the Track P authoritative signal. Where the observed site protocols actually respect that marker and no collector/P.3a is active, use the existing marker/priority protocol and the B1 cooperative GPU lease as the coordination mechanism; no separate operator conversation is required merely because another agent is present. The historical watcher's STOP touches act on reachable manifest directories after marker observation and are not proof that every possible new start checks the marker. Record what start paths and running watcher behavior were actually established; a pattern-miss alone is not proof of all-process absence or future compliance. Recheck immediately before marker, after watcher handover, and immediately before launch; preserve other work, never preempt or force-stop an active collector, and use the actual lease/GPU checks. If a material active job, start path, watcher behavior or safe pause cannot be determined well enough to avoid interference, STOP and identify the concrete missing site fact. This amendment removes no existing non-preemption or evidence-preservation condition and makes no claim that the marker is a kernel lock or prevents non-cooperators.

## Evidence before and after marker

Before creating B1's marker, create a private, unique B1-owned record of timestamp, exact run/head, watcher identity and observed behavior, all reachable manifest paths and each STOP's lstat status, and S/P state; `STOP` must be absent, including dangling symlinks, at every target this procedure may later retire. Record no secret argv. If the target already exists, its absence cannot be established, or there is an unexpected target, do not use this restoration procedure for it. Once the accepted marker creation receipt is captured, immediately publish and verify feature-branch STATUS, then observe watcher log and actual STOP effects. For the smoke target, establish an attributable ordinary watcher creation with a contemporaneous watcher observation, pre-marker absence, post-marker owned regular-file identity `(dev, ino)`, size and SHA-256. Record the full exact path, time and identity in a new B1-owned receipt; keep the watcher log and all evidence. A timestamp, empty bytes, a later file name, or absence alone does not prove the watcher created that file. If ownership, identity, provenance, expected targets or concurrent activity is uncertain, retain it and STOP; do not infer ownership.

## Normal completion only

After independently verified normal B1 completion and shutdown of its owned worker/server and lease release, use the **existing accepted** `b1_o2_marker.py retire` with the original B1 marker receipt. It validates owned regular file, device/inode/hash and moves it with Linux `renameat2(RENAME_NOREPLACE)` to the adjacent owned `_to_delete/`; verify its success and retain the new retirement receipt. Observe the watcher's marker-gone transition. The filesystem and no-replace capability must be qualified as in existing O2. Do not perform these actions on B1 STOP, uncertainty or abnormal exit; preserve marker, outputs, ledger, logs and report shutdown writes.

Only after marker-gone, and only if the exact smoke STOP was proved watcher-created for this handover and remains the same owned regular file, retire its bytes without overwrite using the unchanged reviewed marker helper's `retire` function with `NAME='STOP'`. This reuses its identity/hash, non-symlink, single-link, same-filesystem `_to_delete` and no-replace checks. The input receipt is the independently reviewed B1-owned JSON containing `dev`, `ino`, `sha256` and retained creation-provenance evidence; the helper enforces identity/hash, **not** the provenance judgment. A fresh independent reviewer must first accept the receipt and this precise reuse; apply only to `/home/dowling/r1_tracks/out/smoke`, no other target. The helper's directory checks assume cooperative same-UID access, not malicious concurrent substitution; stop on any discrepancy or missing capability. Its unique destination is reported in the receipt and bytes remain intact. Use only when no collector is running or newly starting and no other process depends on that STOP; never remove a pre-existing STOP. A failure after marker retirement is STOP and preserves all remaining state; no automatic retry.

Conditional exact command, with independently approved receipt already exclusively created at the named B1-owned path (its contents must match the observed identity; do not fabricate it):

```bash
set -eu
umask 077
PAPER=/home/dowling/r1_b1_engineering/b1_paper_final_68357d3d8cd0c9f301005e483a49ecfd05f6e5bb/paper
RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_6835_20261108_a
cd "$PAPER"
set -C
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B - "$RUN_DIR/smoke-stop-receipt.json" > "$RUN_DIR/smoke-stop-retirement.json" <<'PY'
import json, sys
from pathlib import Path
from r1.scripts import b1_o2_marker
receipt = json.loads(Path(sys.argv[1]).read_text())
b1_o2_marker.NAME = 'STOP'
result = b1_o2_marker.retire('/home/dowling/r1_tracks/out/smoke', receipt)
print(json.dumps(result, sort_keys=True), flush=True)
PY
```

The resulting retained `_to_delete` entry must be checked against the receipt; never recreate STOP. Restore observed prior inactivity by leaving Track S and P inactive; no restart commands or edits to their worktrees/files are needed. Record the marker-gone observation, retained STOP/marker destinations and current S/P state; verify normal-completion state and then follow the required complete-batch verifier and STATUS publication. For any other starting state, unknown provenance, unsafe archive location or unverified no-new-start protocol, the site operator and independent reviewer must establish the missing facts or approved alternative; effort is site-dependent. This proposal is not permission to launch B2, X.7 or sweep 2.
