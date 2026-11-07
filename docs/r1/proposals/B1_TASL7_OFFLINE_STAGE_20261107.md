# B1 offline harness staging candidate — independent review required

The 22:45:48 UTC private site locate, `/private/tmp/paper-b-b1-harness-locate-20261107.atA6ND9w/locate.log`, SHA-256 `d7a5be629dab27a16242486c3a004194a8f3746c5826d80fdd7b0699c1113d84`, reports the existing Stage A checkout at 897d83c with the a3fedbb object, and the existing Track S checkout clean at a3fedbb with neither node nor fallback cache. The source-only engineering archive has neither Git nor the caches. No existing checkout is to be modified. Correction to the earlier locate plan: the available pinned **Git** source is `/private/tmp/paper-b-b1-tests-harness-20261107`, not the local 897d83c checkout, which does not contain this object.

A new local Git clone was produced from that pinned source and its origin removed. Eight files, with SHA-256 listed in the previous locate plan, were copied from the local 897d83c checkout into the two L8 fallback directories. The actual current package is `/private/tmp/paper-b-b1-offline-payload-20261107-a/payload.tar`, SHA-256 `b8a8eb2fa09684fa1fa2b8f239c5ec00bdbb2f9bf029b67ceee9d150741880e0`, 25 MiB. The staged `.git/config` has only core entries and no origin. Local pack and fresh receive both report the exact a3fedbb HEAD, empty Git status, and all eight cache SHA-256 values. Local unpack remains at `/private/tmp/paper-b-b1-offline-receive-20261107-a`; both directories are retained. This does not establish scientific eligibility, site loader behaviour, or B1 launch readiness.

The receiver [`tools/r1/b1_offline_harness_stage_20261107.py`](../../../tools/r1/b1_offline_harness_stage_20261107.py) SHA-256 `3c68e80d5b0b51b3467d9d92fd6f5b784d343147a61a2093a5ee867f2af64927` creates the destination and received archive exclusively, checks the archive SHA before extracting, rejects links/special members, duplicate paths and traversal, and creates each file exclusively. It checks actual Git HEAD and clean status with optional locks disabled and rehashes all eight caches. It never deletes remote files and preserves partial state on failure. The archive includes a real Git checkout, not a fabricated Git identity. The tested package is bound by its exact hash; do not regenerate or substitute it for this execution.

After independent review, refreshed applicable handover/occupancy and no-preemption checks, the operator may execute the following **once**. It creates one new owned directory under the already existing engineering parent. The local evidence capture is private; retain it and do not repeat on error, uncertain SSH status, or interruption. The remote path and all existing parents must be real directories, not symlinks. No remote fetch, download, model, GPU, evaluation or repository modification is involved. Python and Git must already be installed. A successful result is only staging; host Python offline loader test on separate disposable cache copies, provenance review, final checkout and all B1 gates remain.

```bash
set -u
umask 077
SCRIPT=/private/tmp/paper-b-b1-pin-cache-plan-20261107/tools/r1/b1_offline_harness_stage_20261107.py
PAYLOAD=/private/tmp/paper-b-b1-offline-payload-20261107-a/payload.tar
EXPECTED_SCRIPT=3c68e80d5b0b51b3467d9d92fd6f5b784d343147a61a2093a5ee867f2af64927
EXPECTED_PAYLOAD=b8a8eb2fa09684fa1fa2b8f239c5ec00bdbb2f9bf029b67ceee9d150741880e0
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED_SCRIPT" ] || exit 1
[ "$(shasum -a 256 "$PAYLOAD" | awk '{print $1}')" = "$EXPECTED_PAYLOAD" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-b1-offline-stage-capture-20261107.XXXXXXXX) || exit 1
CODE=$(python3 -c 'import base64,sys; print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$SCRIPT") || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "set -eu; test \"\$HOME\" = /home/dowling; test ! -L /home; test ! -L /home/dowling; test ! -L /home/dowling/r1_b1_engineering; test -d /home/dowling/r1_b1_engineering; exec python3 -I -B -c 'import base64;exec(base64.b64decode(\"$CODE\"))' receive /home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a $EXPECTED_PAYLOAD" < "$PAYLOAD" > "$OUT/receive.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$OUT/exit.txt"
shasum -a 256 "$OUT/receive.log" "$OUT/exit.txt"
printf 'Private capture: %s; SSH exit=%s\n' "$OUT" "$rc"
```

Before using the destination, inspect the capture and independently confirm SHA, HEAD, all eight caches and clean Git status on site. Symlinks or unexpected existing destination, failed checks, any interruption or unverified outcome mean STOP with scene retained. The staging process consumes roughly two copies of the 25 MiB payload plus checkout overhead; verify space before executing. It does not erase the transfer tar. If this candidate is rejected, preserve the local and remote scenes and prepare a new separately named reviewed attempt, never an automatic retry.
