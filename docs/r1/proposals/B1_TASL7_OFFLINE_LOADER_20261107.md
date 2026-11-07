# B1 staged cache offline loader — candidate for independent review

This one-time engineering check applies only after the reviewed offline stage succeeds and its receipt is independently examined. It reads the staged a3fedbb harness, copies only the eight SHA-bound cache files into a new B1-owned location, and invokes the same `fetch_openml(data_id=..., as_frame=True, parser='auto', data_home=...)` call used by the pinned node benchmarks. It reports shapes and hashes, never dataset rows, targets or B1 audit results. It uses the actual TASL-7 `/home/dowling/exam-x/work/venv/bin/python`, limits BLAS/OpenMP threads to one, runs no model, fitting, GPU or B1 campaign and does not modify the staged harness.

The script blocks Python `socket.connect`, `connect_ex`, `create_connection` and `getaddrinfo` before importing sklearn: this is an application-level network guard for this loader, not a kernel firewall or proof against native or adversarial bypass. After importing sklearn, the script replaces its OpenML clean-cache and network retry decorators with pass-through decorators, and denies `os.unlink` and `os.remove` for the process, so an invalid cache stops rather than being deleted and retried. Each copy is exclusive and hash-checked before and after loader use, including on loader exceptions; on early copy/import failure retain partial copies and logs. The result is a bounded cache/loader compatibility observation, not scientific provenance, resource sufficiency or launch authority. Output remains private. Never rerun automatically after any failure, disconnect or unclear outcome.

Script `tools/r1/b1_offline_loader_check_20261107.py` SHA-256 `cdcf535253570b14e3c82a0ed820e1ed7d05fd1b563a59b134fadf33d96c6850`. Local engineering demonstration used the received checkout at `/private/tmp/paper-b-b1-offline-receive-20261107-a/harness`, sklearn 1.8.0, one thread and a fresh directory `/private/tmp/paper-b-b1-loader-local-20261107-c`; both shapes and all hashes passed, exit 0. In this Mac test only, `sys.prefix` was replaced in-process to exercise the site-only prefix condition; it is not site evidence. A separate local synthetic corrupt-JSON cache exercised sklearn 1.8’s real `_get_json_content_from_openml_api`: exactly one open occurred, a parse error propagated, bytes were unchanged, and explicit `os.unlink` was denied; the synthetic file remains in `/private/tmp/paper-b-b1-loader-fault-20261107-a`. The success test log is `/private/tmp/paper-b-b1-loader-local-20261107-c.log`.

After independent review and fresh relevant handover and host checks, run once, with capture retained:

```bash
set -u
umask 077
SCRIPT=/private/tmp/paper-b-b1-pin-cache-plan-20261107/tools/r1/b1_offline_loader_check_20261107.py
EXPECTED=cdcf535253570b14e3c82a0ed820e1ed7d05fd1b563a59b134fadf33d96c6850
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-b1-loader-capture-20261107.XXXXXXXX) || exit 1
CODE=$(python3 -c 'import base64,sys; print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$SCRIPT") || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "set -eu; test \"\$HOME\" = /home/dowling; test ! -L /home; test ! -L /home/dowling; test ! -L /home/dowling/r1_b1_engineering; test -d /home/dowling/r1_b1_engineering; test ! -L /home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a; test ! -L /home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness; R=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness; test \"\$(git --no-optional-locks -c core.fsmonitor=false -C \"\$R\" rev-parse HEAD)\" = a3fedbbd44309b3fdf99d853ad841b9ec2c299e2; STATUS=\$(git --no-optional-locks -c core.fsmonitor=false -C \"\$R\" status --porcelain --untracked-files=all); test -z \"\$STATUS\"; exec env -i HOME=/home/dowling PATH=/home/dowling/exam-x/work/venv/bin:/usr/bin:/bin OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /home/dowling/exam-x/work/venv/bin/python -I -B -c 'import base64;exec(base64.b64decode(\"$CODE\"))' \"\$R\" /home/dowling/r1_b1_engineering/b1_offline_loader_20261107_a" > "$OUT/loader.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$OUT/exit.txt"
shasum -a 256 "$OUT/loader.log" "$OUT/exit.txt"
printf 'Private capture: %s; SSH exit=%s\n' "$OUT" "$rc"
```

PASS requires SSH exit 0, expected prefix, both expected shapes and target lengths, 16 BEFORE and AFTER hashes equal to their eight expected values, and `OFFLINE_LOADER_PASS`. A missing/changed file, unexpected path/symlink, existing destination, failed Python import, unexpected interpreter/prefix, network attempt, mismatch, interruption, or ambiguous SSH result is STOP: preserve the destination and capture and request independent evaluation. No conclusions about audit values or a final B1 gate follow from this check.
