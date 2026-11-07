# B1 final Paper checkout: offline stage candidate

**For independent review; not a host execution or a final-HEAD acceptance.** The final Paper checkout must contain the appropriately committed author-note candidate and be independently reviewed at its exact HEAD before the committed author gate/preflight and B1 launch. This plan packages a real detached Git checkout only after the final source HEAD exists; it neither creates the author note nor supplies approval. The local source must be clean with the exact selected HEAD; existing site Paper, Track S/P/X and harness worktrees are not touched. There is no remote Git fetch or network dependency other than the reviewed local-to-TASL7 transfer.

The local script `tools/r1/b1_paper_offline_stage_20261108.py`, SHA-256 `3011753cc60dfee8e985e51e19f628cdc363cfb818814b845ac5dd2358aedb94`, clones locally into a new directory, checks out the exact full SHA, removes its local origin and checks HEAD, clean Git status and no remotes. It packages the clone as a single tar; ignored local output and caches are not copied. The site receiver exclusively creates a new destination and archive, verifies the full tar digest before extraction, rejects traversal, special entries, duplicate names, symlink targets escaping the tree and members nested under symlinks, writes regular files exclusively, and creates links only after all files. Git uses `--no-optional-locks` for status. No remote file is removed; any partial artifact stays in place. The repository has one tracked relative symlink under `archive/old_b_2026-10-09/code/experiment_scaffold/pi_extensions/node_modules`; an all-symlink rejection would incorrectly reject the genuine checkout, so the receiver handles it explicitly through its general safe-link validation. It does not dereference it during extraction.

Local demonstration only: source HEAD `f2eccd7709a89cbdb9468623a02ea9fdabe16bff` produced `/private/tmp/paper-b-paper-offline-payload-test-20261108-a/paper.tar`, SHA-256 `fcff6858a4b4350fb6948b835bd614e18a4d8e927a2cc34c42f2e557e432cc58`, about 129 MiB; a clean receive using the final script at `/private/tmp/paper-b-paper-offline-receive-test-20261108-b` returned the same HEAD and clean status, with the tracked symlink intact. This is a test payload on an earlier HEAD, not the final B1 artifact. The final archive's size and SHA must be measured; allow at least the payload plus unpacked checkout space, with any final preflight space requirement separate.

## Once final HEAD is ready

After author-note prerequisites and independent review are complete as required by the authorized ordering, set the **actual clean final committed source path and full 40-hex HEAD** in a private local operator session. The script and command must themselves be accepted by a fresh reviewer before use. A new uniquely named local work directory and capture preserve the precise archive and logs. The illustrative directory names below are one-shot; if occupied, STOP and preserve the scene, not delete or overwrite it. This local pack never pushes any branch.

```bash
set -u
umask 077
SCRIPT=/private/tmp/paper-b-paper-offline-stage-20261108/tools/r1/b1_paper_offline_stage_20261108.py
EXPECTED_SCRIPT=3011753cc60dfee8e985e51e19f628cdc363cfb818814b845ac5dd2358aedb94
SOURCE=/absolute/path/to/final/clean/committed/paper
HEAD=REPLACE_WITH_EXACT_REVIEWED_40_HEX_HEAD
PACK=/private/tmp/paper-b-final-paper-payload-20261108-unique
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED_SCRIPT" ] || exit 1
set -C
python3 -B "$SCRIPT" pack "$SOURCE" "$PACK" "$HEAD" > "${PACK}.log" 2>&1 || exit 1
PAYLOAD="$PACK/paper.tar"
PAYLOAD_SHA=$(shasum -a 256 "$PAYLOAD" | awk '{print $1}') || exit 1
printf 'HEAD=%s\nPAYLOAD=%s\nSHA256=%s\n' "$HEAD" "$PAYLOAD" "$PAYLOAD_SHA"
```

Before transfer the independent reviewer checks the exact final source HEAD, clean status, full pack log, payload SHA and contents, no active Git hooks/alternates/credential-bearing metadata, tracked symlink, and final author-note/config bindings. Review the **filled-in** commands and artifact; this plan is not acceptance of a future payload. Source may subsequently advance: preserve and use the reviewed exact artifact, never silently substitute a new HEAD.

After that review, applicable handover/occupancy checks, and space check, execute the following once in the **same local session**. `HEAD`, `PAYLOAD`, `PAYLOAD_SHA`, `SCRIPT` and `EXPECTED_SCRIPT` are the bound values above; recheck them. This command creates an exclusive destination named by the full HEAD under the existing owned engineering directory. Preserve the private local capture and the full remote directory on any failure, interruption or unclear outcome; never automatically retry. Reusing a destination, even after failure, STOPs. There is no remote deletion, checkout in an existing tree, network fetch, model or GPU use.

```bash
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED_SCRIPT" ] || exit 1
[ "$(shasum -a 256 "$PAYLOAD" | awk '{print $1}')" = "$PAYLOAD_SHA" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-paper-final-capture-20261108.XXXXXXXX) || exit 1
CODE=$(python3 -c 'import base64,sys; print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$SCRIPT") || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "set -eu; test \"\$HOME\" = /home/dowling; test ! -L /home; test ! -L /home/dowling; test ! -L /home/dowling/r1_b1_engineering; test -d /home/dowling/r1_b1_engineering; exec python3 -I -B -c 'import base64;exec(base64.b64decode(\"$CODE\"))' receive /home/dowling/r1_b1_engineering/b1_paper_final_${HEAD} $HEAD $PAYLOAD_SHA" < "$PAYLOAD" > "$OUT/receive.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$OUT/exit.txt"
shasum -a 256 "$OUT/receive.log" "$OUT/exit.txt"
printf 'Private capture: %s; SSH exit=%s\n' "$OUT" "$rc"
```

PASS requires zero SSH exit, exact reported HEAD, clean status and no clone remotes. Independently inspect the retained logs and actual received checkout before relying on it; author gate, site preflight, data/lease/capacity and handover remain separate. If any check fails or is uncertain, preserve the scene and STOP. No automated replacement, repair, rerun or final phase is authorized by this template.
