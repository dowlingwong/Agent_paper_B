# One authorized repeat of offline B1 cache check

**Candidate for independent review by the same reviewer who assessed the first attempt; not executed.** The first capture `/private/tmp/paper-b-b1-loader-capture-20261107.IDBCosWY/loader.log`, SHA-256 `5646fa9f8f2e4d3c1823387e92abdcd33f5b6a85996ef35f920ab9f9b93667f5`, is retained as **incomplete attempt: exit code not captured**; the destination `/home/dowling/r1_b1_engineering/b1_offline_loader_20261107_a` and all other evidence remain untouched. Its successful loader lines do not upgrade that attempt to PASS.

## Author instruction (8 November, verbatim)

> 不追认第一次为 PASS，按以下顺序处理：
> 1. 先做只读确认。 核对这 8 个文件当前的 SHA，和第一次日志里的前后值一致，不改动现场。
> 2. 修包装。 SSH 的退出码要可靠地保存下来，例如 ssh … ; rc=$?; echo "SSH_EXIT=$rc" | tee -a <log>；如果用了管道，加 set -o pipefail，避免 ssh | tee 只拿到 tee 的退出码。退出码写进日志，也写进单独的 rc 文件。
> 3. 只读重跑一次同样的离线缓存检查。判定通过需要三条同时满足：SSH_EXIT=0、日志里有 OFFLINE_LOADER_PASS、8 个文件前后 SHA 不变。
> 4. 第一次运行的日志和现场原样保留，报告中标为"incomplete attempt: exit code not captured"，不删除、不覆盖。
> 5. 由同一个独立审查验收重跑。验收前，B1 的其他门槛照旧，不因此放宽。
> 如果重跑结果和第一次不一致（加载失败或 SHA 变了），停下来报告，不要再重试。
> 还有一个顺带的好处：修好的包装可以复用到之后所有的 SSH 检查，后面不会再因为同样的原因卡住。

The first step below is source-read-only on the site. The second uses exactly the prior reviewed loader `cdcf535253570b14e3c82a0ed820e1ed7d05fd1b563a59b134fadf33d96c6850` in the same host venv, same one-thread environment, with network and retry/unlink guards; like the first check it creates new private cache copies for loading, does not fit a model, use GPU or touch staged input bytes. It writes exclusively to new `/home/dowling/r1_b1_engineering/b1_offline_loader_20261108_b`; this is the sole newly authorized attempt, never an automatic retry after a failed/mismatching result. Existing author-gate, B1, host and scientific conditions are unchanged.

`tools/r1/ssh_capture_once_20261108.sh` SHA `507a8aafd5a4dd8228d9b147fd32f9de2e427b839ee504df4bf841fea758d40a` is a reusable **single-call** wrapper, with pipefail, exclusive log and rc files, `ssh -n` and explicit `/dev/null` stdin. It writes the SSH status both as `SSH_EXIT=` in the log and as the sole separate rc value; it returns that SSH status, or its own nonzero failure if capture fails. It does not retry. A local mock SSH returning 17 while input was available reported rc 17 in both files and did not consume stdin; retained test files `/private/tmp/paper-b-ssh-capture-test-20261108-a`. `tools/r1/b1_loader_source_hashes_20261108.py` SHA `2393ede0db80a2d85ef8a1fe3479017435bdd8a058ce925afab9684a5c7d2c1a` checks the eight exact sources without writing the host; it uses the previously reviewed loader's hash list and no-follow checks. This verifies current bytes only, not an atomic reservation.

After same-reviewer acceptance and fresh host/no-preemption checks, the following single local Bash script performs the read-only check and, **only if it and its recorded SSH exit both pass**, performs the one new check. It checks the retained first log's exact SHA and verifies each BEFORE and AFTER against the loader's eight bindings before contacting the host. The capture directory is exclusively new, SSH never consumes script stdin, and neither session is repeated. A failed source check, changed hash, SSH failure, missing marker or inconsistent result is STOP: retain all files and report. Independently review the exact filled script and the new attempt before calling it accepted.

```bash
set -u
set -o pipefail
umask 077
BASE=/private/tmp/paper-b-b1-loader-one-more-20261108
WRAP="$BASE/tools/r1/ssh_capture_once_20261108.sh"
VERIFY="$BASE/tools/r1/b1_loader_source_hashes_20261108.py"
LOADER="$BASE/tools/r1/b1_offline_loader_check_20261107.py"
FIRST=/private/tmp/paper-b-b1-loader-capture-20261107.IDBCosWY/loader.log
[ "$(shasum -a 256 "$WRAP" | awk '{print $1}')" = 507a8aafd5a4dd8228d9b147fd32f9de2e427b839ee504df4bf841fea758d40a ] || exit 1
[ "$(shasum -a 256 "$VERIFY" | awk '{print $1}')" = 2393ede0db80a2d85ef8a1fe3479017435bdd8a058ce925afab9684a5c7d2c1a ] || exit 1
[ "$(shasum -a 256 "$LOADER" | awk '{print $1}')" = cdcf535253570b14e3c82a0ed820e1ed7d05fd1b563a59b134fadf33d96c6850 ] || exit 1
[ "$(shasum -a 256 "$FIRST" | awk '{print $1}')" = 5646fa9f8f2e4d3c1823387e92abdcd33f5b6a85996ef35f920ab9f9b93667f5 ] || exit 1
python3 -B - "$LOADER" "$FIRST" <<'PY' || exit 1
import runpy,sys
expected={(n,p):h for n,(_,_,fs) in runpy.run_path(sys.argv[1]).get('FILES').items() for p,h in fs.items()}
rows={'BEFORE':{},'AFTER':{}}
for line in open(sys.argv[2],encoding='utf-8'):
 parts=line.split()
 if parts and parts[0] in rows:
  if len(parts)!=4 or (parts[1],parts[2]) in rows[parts[0]]: raise SystemExit('STOP: malformed/duplicate first log')
  rows[parts[0]][(parts[1],parts[2])]=parts[3]
if len(expected)!=8 or any(rows[k]!=expected for k in rows): raise SystemExit('STOP: first log hashes differ')
print('FIRST_LOG_EIGHT_BEFORE_AFTER_MATCH')
PY
CAP=$(mktemp -d /private/tmp/paper-b-b1-loader-repeat-20261108.XXXXXXXX) || exit 1
LCODE=$(python3 -c 'import base64,sys;print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$LOADER") || exit 1
VCODE=$(python3 -c 'import base64,sys;print(base64.b64encode(open(sys.argv[1],"rb").read()).decode())' "$VERIFY") || exit 1
printf 'PRIVATE_CAPTURE=%s\n' "$CAP"
if bash "$WRAP" "$CAP/source.log" "$CAP/source.rc" tasl7 "exec python3 -I -B -c 'import base64;exec(base64.b64decode(\"$VCODE\"))' '$LCODE'"; then :; else exit 1; fi
[ "$(cat "$CAP/source.rc")" = 0 ] || exit 1
grep -qx 'EIGHT_SOURCE_HASHES_MATCH' "$CAP/source.log" || exit 1
[ "$(grep -c '^CURRENT ' "$CAP/source.log")" = 8 ] || exit 1
R=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
DEST=/home/dowling/r1_b1_engineering/b1_offline_loader_20261108_b
if bash "$WRAP" "$CAP/loader.log" "$CAP/loader.rc" tasl7 "set -eu; unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS; export GIT_OPTIONAL_LOCKS=0 GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null; test \"\$HOME\" = /home/dowling; test ! -L /home; test ! -L /home/dowling; test ! -L /home/dowling/r1_b1_engineering; test ! -L /home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a; test ! -L '$R'; test ! -e '$DEST'; test ! -L '$DEST'; test \"\$(git --no-optional-locks -c core.fsmonitor=false -C '$R' rev-parse HEAD)\" = a3fedbbd44309b3fdf99d853ad841b9ec2c299e2; STATUS=\$(git --no-optional-locks -c core.fsmonitor=false -C '$R' status --porcelain --untracked-files=all); test -z \"\$STATUS\"; exec env -i HOME=/home/dowling PATH=/home/dowling/exam-x/work/venv/bin:/usr/bin:/bin OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /home/dowling/exam-x/work/venv/bin/python -I -B -c 'import base64;exec(base64.b64decode(\"$LCODE\"))' '$R' '$DEST'"; then :; else exit 1; fi
[ "$(cat "$CAP/loader.rc")" = 0 ] || exit 1
grep -qx 'SSH_EXIT=0' "$CAP/loader.log" || exit 1
grep -qx 'OFFLINE_LOADER_PASS' "$CAP/loader.log" || exit 1
python3 -B - "$LOADER" "$CAP/loader.log" "$FIRST" <<'PY' || exit 1
import runpy,sys
expected={(n,p):h for n,(_,_,fs) in runpy.run_path(sys.argv[1]).get('FILES').items() for p,h in fs.items()}
rows={'BEFORE':{},'AFTER':{}}
for line in open(sys.argv[2],encoding='utf-8'):
 parts=line.split()
 if parts and parts[0] in rows:
  if len(parts)!=4 or (parts[1],parts[2]) in rows[parts[0]]: raise SystemExit('STOP: malformed/duplicate loader log')
  rows[parts[0]][(parts[1],parts[2])]=parts[3]
if len(expected)!=8 or any(rows[k]!=expected for k in rows): raise SystemExit('STOP: repeated loader hashes differ')
first=open(sys.argv[3],encoding='utf-8').read().splitlines()
repeated=open(sys.argv[2],encoding='utf-8').read().splitlines()
for prefix in ('PYTHON ', 'LOADED '):
 if [x for x in first if x.startswith(prefix)] != [x for x in repeated if x.startswith(prefix)]:
  raise SystemExit('STOP: interpreter, version or load result differs from first attempt')
print('REPEAT_EIGHT_BEFORE_AFTER_MATCH')
PY
shasum -a 256 "$CAP/source.log" "$CAP/source.rc" "$CAP/loader.log" "$CAP/loader.rc"
printf 'REPEAT_RESULT_FOR_INDEPENDENT_REVIEW=%s\n' "$CAP"
```
