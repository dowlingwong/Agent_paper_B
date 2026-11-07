# B1 TASL-7 harness pin and OpenML cache: read-only locate plan

**Candidate for fresh independent review; no host action in preparing it.** A single read-only capacity capture `/private/tmp/paper-b-b1-capacity-readonly-20261107.xn8UKGYy/inventory.txt` SHA-256 `ee166453e8edafd13c75b8e699ca2771ea87eaa360635bc51b0e5e97ca1b0206` reports at 2026-11-07 22:41:12 UTC that `/home/dowling/exam-x/work/autoresearch_harness` is at **897d83c8efa364ec2fdd37288241cc42e01d7274**, and its two expected L8 fallback cache paths returned missing. Its local exit capture is 0, but the per-path `du`/`df` checks returned 1; the snapshot does not prove caches are absent anywhere else. Do not switch, clean, delete or otherwise alter this existing Stage A harness checkout. B1 requires `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` and its `b1_harness_sources` checks the actual Git HEAD and clean tracked/untracked status; a source-only archive without `.git` cannot satisfy that check. The existing engineering archive at `/home/dowling/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/harness` was suitable for the bounded synthetic test only; it is not a Git checkout and does not contain the two fallback caches.

## Verified local candidate data, not a site receipt

In the separate local `/Users/wongdowling/Documents/autoresearch_harness` at 897d83c, the ignored L8 fallback directories contain four gzip files per node. The `a3fedbb` node `dataset.json` names dataset 29 (`credit-approval`) and 59 (`ionosphere`). The source caches were read only. The uncompressed ARFF MD5 values match each cache's own OpenML dataset metadata: credit `a948be968270a823fce432227c1aa36e`, ionosphere `23dd3c8b5693e2848901fd1a0248ef42`. For ionosphere, the ARFF gzip bytes also match the committed historical E1b node-state snapshot; its three metadata gzip files differ in compression bytes but decompress identically. This establishes the stated file relationships, not an independent proof of scientific eligibility or an identity for the credit cache against a separately accepted external artifact.

| Node | Cache-relative file under `openml/openml.org/` | Local SHA-256 |
|---|---|---|
| credit | `api/v1/json/data/qualities/29.gz` | `5e3213b47856a86b5087dc7a663624d9641a3bc6145d2dd79308f837890cc827` |
| credit | `api/v1/json/data/features/29.gz` | `ffc560253f365d1d301d2eeaf86cd9fe1040f52d9e923ab73534adbadd21019c` |
| credit | `api/v1/json/data/29.gz` | `5229a8b115c8bc536576a6d48086b3ef9bc57b673cb31fa26894cb6682c562dd` |
| credit | `data/v1/download/29/credit-approval.arff.gz` | `b21f01872e3db3d90f775be77e431ccd3bfd96555ad09bcea49fcd558bb4fc4a` |
| ionosphere | `api/v1/json/data/qualities/59.gz` | `2e40aafecce975d3d09ead5eabec40956163cd9f81a39e70b78977ac101c9aa7` |
| ionosphere | `api/v1/json/data/features/59.gz` | `04154009932e0fd7ac67716c604b3d46ef551be85cfe5e47387596b33267ced1` |
| ionosphere | `api/v1/json/data/59.gz` | `2d18f98c5d0fe9b0f014d8cb6684c49b22d61ee11d398dd48eebefbc035260da` |
| ionosphere | `data/v1/download/59/ionosphere.arff.gz` | `40b4580d51a1815c9d1bea32cc579d523ea98af8c80a06a345e192729359644e` |

On Mac with scikit-learn 1.8.0, separate fresh copies of these caches were used in a single process with `socket.socket.connect` replaced by a refusal; actual `fetch_openml(data_id=..., as_frame=True, parser='auto')` loaded credit shape `(690,15)` and ionosphere `(351,34)`, target lengths 690 and 351. All eight copied file hashes were unchanged after loading. Retained local engineering copies: `/var/folders/mf/cqjfz_8x7tgbhvl955fzybtr0000gn/T/b1-openml-cache-offline-ev38y26d`. This is not a host venv test, full network-system-call proof, data validation, model run, or evidence from 7006–7010 or B1 audit seeds. The source `data_cache` is Git-ignored (`experiments/**`), so a clean Git status cannot by itself attest its contents.

## Read-only site locate

After fresh applicable STATUS/lock/process and no-preemption checks, the authorized operator can run the following **once**, following independent command review. It inspects only four explicitly named own-tree candidate roots: the known historical harness, the existing source-only engineering extraction, and two possible Track S/P sibling harness locations. The latter are search candidates, not claims that those checkouts exist. It enumerates only the two selected node-local cache directories and their exact L8 fallback counterparts. It prints Git HEAD/status/object availability with optional locking disabled and hashes cache files; it performs no `git checkout`, fetch, model load, GPU work, host write or deletion. Cache paths may contain operational metadata; retain the full capture privately and publish only reviewed facts. Error or missing access is NOT CHECKABLE, not a global absence claim.

```bash
set -u
umask 077
OUT=$(mktemp -d /private/tmp/paper-b-b1-harness-locate-20261107.XXXXXXXX) || exit 1
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > "$OUT/locate.log" 2>&1 <<'REMOTE'
set -u
date -u; hostname
for root in "$HOME/exam-x/work/autoresearch_harness" \
 "$HOME/r1_b1_engineering/b1_worker_engineering_20261107_2208_a/harness" \
 "$HOME/r1_tracks/work/autoresearch_harness" "$HOME/r1_trackp/work/autoresearch_harness"; do
  printf '\nROOT %s\n' "$root"
  if test -L "$root" || ! test -d "$root"; then printf 'ROOT_MISSING_OR_SYMLINK\n'; continue; fi
  if test -d "$root/.git" && ! test -L "$root/.git"; then
    git --no-optional-locks -c core.fsmonitor=false -C "$root" rev-parse HEAD; printf 'git_head_rc=%s\n' "$?"
    git --no-optional-locks -c core.fsmonitor=false -C "$root" status --porcelain --untracked-files=all; printf 'git_status_rc=%s\n' "$?"
    git --no-optional-locks -c core.fsmonitor=false -C "$root" cat-file -e a3fedbbd44309b3fdf99d853ad841b9ec2c299e2^{commit}; printf 'pin_object_rc=%s\n' "$?"
  else printf 'NO_LOCAL_GIT_DIRECTORY\n'; fi
  python3 -I -B - "$root" <<'PY'
import hashlib, os, stat, sys
from pathlib import Path
root=Path(sys.argv[1])
for node,dataid,arff in [('openml_credit_approval',29,'credit-approval.arff.gz'),('openml_ionosphere',59,'ionosphere.arff.gz')]:
    relative=[f'openml/openml.org/api/v1/json/data/{dataid}.gz',
              f'openml/openml.org/api/v1/json/data/features/{dataid}.gz',
              f'openml/openml.org/api/v1/json/data/qualities/{dataid}.gz',
              f'openml/openml.org/data/v1/download/{dataid}/{arff}']
    for label,cache in [('node',root/'nodes'/node/'data_cache'),
                        ('fallback',root/'experiments/r1/pilot/L8_20261009T152916Z/nodes'/node/'data_cache')]:
        print('CACHE',node,label,str(cache),flush=True)
        cur=root
        try:
            for part in cache.relative_to(root).parts:
                cur=cur/part
                if cur.is_symlink(): raise RuntimeError('symlink in cache path')
            if not cache.is_dir(): print('MISSING_OR_NOT_DIRECTORY'); continue
            entries=[]
            for parent,dirs,files in os.walk(cache,followlinks=False):
                for name in dirs+files:
                    p=Path(parent)/name
                    if p.is_symlink(): raise RuntimeError('symlink in cache tree')
                    if not (p.is_dir() or p.is_file()): raise RuntimeError('special entry in cache tree')
                    entries.append(p.relative_to(cache).as_posix())
            print('ENTRY_COUNT',len(entries))
            for rel in relative:
                p=cache/rel
                if not p.is_file() or p.is_symlink(): print('MISSING_OR_UNSAFE',rel);continue
                h=hashlib.sha256()
                with p.open('rb') as f:
                    for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
                print('FILE',rel,'bytes',p.stat().st_size,'sha256',h.hexdigest())
        except (OSError,RuntimeError,ValueError) as exc:
            print('NOT_CHECKABLE',type(exc).__name__,str(exc))
PY
  printf 'cache_probe_rc=%s\n' "$?"
done
REMOTE
rc=$?
printf '%s\n' "$rc" > "$OUT/exit.txt"
shasum -a 256 "$OUT/locate.log" "$OUT/exit.txt"
printf 'Private capture: %s; SSH exit=%s\n' "$OUT" "$rc"
```

The local `GIT_OPTIONAL_LOCKS`/`--no-optional-locks` read is not a reservation or concurrency proof. On the actual B1 path, `r1/exam/campaign.py` copies `nodes/<node>/data_cache` if it exists **even if empty**; it uses the L8 fallback only when the copied node has no such directory. `r1/c3/audit.py` follows the same rule. Thus an empty local cache can defeat the fallback. The reviewer must check all four expected files, extra entries, directory/symlink safety, data IDs, and the exact code pin and execution venv; a matching HEAD alone is not cache provenance.

## Minimal offline staging path if no ready checkout is found

Use a new B1-owned directory, never the existing 897 Stage A worktree or an existing evidence path. The local pinned `a3fedbb` checkout is an available exact code source; prepare a self-contained offline Git payload from that specific commit and the two locally hashed cache trees, review its member list and credential-free Git metadata, and transfer it into exclusively new paths. Keep the expected eight hashes above and the payload hash in an immutable manifest; verify them after transfer and before use. The Git metadata must support the real `git -C <root> rev-parse HEAD` and `git status --porcelain --untracked-files=all` checks; the ignored caches need a separate SHA manifest because Git cleanliness does not bind them. Do not fake `.git`, use a moving branch, push a harness candidate, fetch model/data from the network, or modify/delete the source caches. Do not extract over any existing target.

An implementation owner must prepare the exact local payload/transfer commands and demonstrate, on new test-owned directories, that any Git-internal temp/lock behavior and extraction do not delete protected repository or remote files; an independent reviewer checks those commands and all source bytes before the operator executes them. This is a bounded packaging task, not a new author decision. Once a separate host checkout and cache copies exist, the operator verifies the exact pin, clean Git state, the eight hashes and symlink-free paths, and runs a separately reviewed **offline loader-only** test with the same host Python/scikit-learn as B1 on disposable copies, with network calls denied and no model fitting or registered audit seeds. Record shapes and success only; do not print dataset rows or evaluation values. Failure or incomplete cache is STOP, retain scene and do not retry automatically. Only after independently reviewed data provenance and loader evidence may the new checkout be used in the later final-head author gate/preflight and 20-worker/capacity assessment; none of this is B1 launch authority.
