# Local Paper B payload for candidate 9dfd — no transfer

**For independent review; host transfer and gate have not been performed.** The separate candidate checkout source `/private/tmp/paper-b-b1-next-20261107` was clean at HEAD `9dfd6cf31622fa8f21da02843d61d51bbc200e05` when packaged. This exact HEAD carries the author-authorized `approved:true` candidate note, subject to the approved subsequent exact-HEAD/gate/preflight/handover sequence. The current model-inventory SSH STOP remains in force; **do not execute the transfer below while it is unresolved**. This artifact does not waive or resolve that STOP, constitute an author gate pass, or authorize B1.

Using the accepted no-deletion copy/receive tool (`28c62bb140543cca3a87d8ff353d9168c4fc3a73`, review `9c8cf602cf6f0492c2dc75b04bb7ea425afade20`), local exclusive pack produced `/private/tmp/paper-b-paper-payload-9dfd-20261108-a/paper.tar`, SHA-256 `0bf3156e525b57bb00732a0ab6f87ab2a6561273880d1457f5bdbb9590470cfe`, approximately 146 MiB. Its retained pack log SHA-256 `ccebfe81e62f8c57c457bb03a3de82093c5dd8e0cf62ba5772ef098ab8e3726a` reports exact HEAD, clean Git status and no remote. Exclusive local receive `/private/tmp/paper-b-paper-receive-9dfd-20261108-a/paper` likewise reports that HEAD, clean status and no remote; receive log SHA-256 `5c108506f5bd864b86d3e2dd272dda25566a53305bc40be5ac527797bf144bd7`. `git fsck --connectivity-only --no-reflogs --no-dangling` passed locally; `f2eccd7709a89cbdb9468623a02ea9fdabe16bff` is an ancestor and protected exam paths have no changes after that code pin. This is not the real host gate.

The retained private member manifest `/private/tmp/paper-b-paper-payload-9dfd-20261108-a.manifest.json` SHA-256 `4d1e04ff1bc6b089dc00bccc2c04369ce1da73ff60cfd9e82b33d30d674afe15` enumerates **16,572** archive entries: 12,475 regular files with SHA-256 and sizes, 4,096 directories and one relative symlink with target. Every archive regular file was compared byte-for-byte by SHA-256 to the received file; directory/link types and target matched; an additional walk found zero extra or missing paths. These are local point-in-time comparisons, not an atomic proof against later mutation. The manifest records mtime 00:56:04 CET and the original received `.git/index` records mtime 00:56:29 CET; these filesystem timestamps do not independently establish the change time. The index current SHA is `b0456012e617a2382898ef55a9f44f1eaabb6d181bed4ba62109975daa39a05e`, whereas tar and manifest bind `bf9bf2e102d0c8b1344c4f63012c45fc202174af57b740bfa1aa50d9589925ff`. The change mechanism and whether it involved deletion or replacement of a protected Git repository file are both NOT CHECKABLE from the retained evidence; that original scene is preserved without replacement. Independent reviewer `b01094113955dc0619c036c1fd36c1240f61c97c` reproduced an exclusive separate local receive and compared every entry before any further Git operation, including index, with no mismatch. The received `.git` has only HEAD, minimal core config, index, copied objects and empty refs; no remote, hook directory, alternates or grafts, no metadata symlinks/special entries, no shallow repository or split index. It is a real detached Git checkout using the actual copied object store and index.

A local pattern scan over all **21,275** Git objects, including **10,080 blobs**, found zero matches for PEM private-key headers, GitHub token prefixes with token-shaped suffixes, and AWS access-key-shaped IDs. This bounded pattern scan does **not** prove the object database or working tree contains no confidential material or all possible credential formats. The private manifest and artifact contain complete tracked content and Git objects, including historical objects; inspect under the user's access policy and do not publish them. No source contents or credentials were printed in the scan. The received configured note SHA-256 is `66abe0af038687c0e798c80c6c8f10e90cfd9c0db25c041d37bd43d42d06a412`; the committed config SHA-256 is `64a7d771fb00fe1bc22bba2df355a84764dfbd1764b7c69a7abd9fd9f6255d01` and its `paper_commit` is f2. Comparing and hashing these bytes does not execute `author_gate`.

## Filled one-shot site transfer command — review only

After the independent reviewer examines the exact payload, manifest, Git metadata, note/config, command and the model-inventory STOP has been resolved under the author's instructions, the site operator must refresh relevant occupancy, handover and space facts. The command creates only a new own directory `/home/dowling/r1_b1_engineering/b1_paper_final_9dfd6cf31622fa8f21da02843d61d51bbc200e05`; existing Track S/P/X checkouts and inputs are not altered. No retry after failure, connection loss or uncertain state. The script is supplied from a local file rather than to Bash on stdin; SSH receives only the tar stream, preventing SSH from swallowing later shell statements. Output is private local capture; its actual SSH exit is written in both the log and a separate rc file. Any missing/failed capture is STOP and all partial files remain.

```bash
set -u
set -o pipefail
umask 077
SCRIPT=/private/tmp/paper-b-paper-offline-stage-20261108/tools/r1/b1_paper_offline_stage_20261108.py
PAYLOAD=/private/tmp/paper-b-paper-payload-9dfd-20261108-a/paper.tar
HEAD=9dfd6cf31622fa8f21da02843d61d51bbc200e05
PAYLOAD_SHA=0bf3156e525b57bb00732a0ab6f87ab2a6561273880d1457f5bdbb9590470cfe
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = 462b860e15b1cc8bac7e685ec3ddd7ecebf1850981df593b0063ef5e8cbe3b67 ] || exit 1
[ "$(shasum -a 256 "$PAYLOAD" | awk '{print $1}')" = "$PAYLOAD_SHA" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-paper-9dfd-site-capture-20261108.XXXXXXXX) || exit 1
CODE=$(python3 -c 'import base64,sys;print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$SCRIPT") || exit 1
set -C
exec 3> "$OUT/receive.log"
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
if ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "set -eu; test \"\$HOME\" = /home/dowling; test ! -L /home; test ! -L /home/dowling; test ! -L /home/dowling/r1_b1_engineering; test -d /home/dowling/r1_b1_engineering; exec python3 -I -B -c 'import base64;exec(base64.b64decode(\"$CODE\"))' receive /home/dowling/r1_b1_engineering/b1_paper_final_9dfd6cf31622fa8f21da02843d61d51bbc200e05 $HEAD $PAYLOAD_SHA" < "$PAYLOAD" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nSSH_EXIT=%s\n' "$rc" >&3 || exit 1
printf '%s\n' "$rc" > "$OUT/receive.rc" || exit 1
shasum -a 256 "$OUT/receive.log" "$OUT/receive.rc"
printf 'SSH_EXIT=%s PRIVATE_CAPTURE=%s\n' "$rc" "$OUT"
exit "$rc"
```

The actual site result, final host checkout, author gate, native preflight, model inventory disposition, resource assessment, O2 handover and launch remain separate checks. The code pin and any later HEAD changes must be independently rechecked rather than silently substituted.
