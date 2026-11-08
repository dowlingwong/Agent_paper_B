# B1 6835 post-marker observation — review only

No host action has been performed. This conditional read-only capture is for use **after** accepted marker creation, immediate feature STATUS publication and remote-SHA verification, and before accepting the watcher pause or launching B1. Review exact scripts and site conditions independently first. It reads marker and smoke STOP lstat/dev/inode/uid/mode/nlink/size/hash, the own marker and STATUS receipts, recent watcher log and on-disk watcher hash, watcher pane metadata, current-user collector/P.3a candidate PIDs and GPU observations. It sends no signals, changes no remote file and does not read process argv. It does not establish that running watcher bytes equal disk bytes, that pgrep patterns find all work or that future starts cannot race. Preserve private captures. Exit zero and the completion marker mean only that the block reached its end: independently review all component rc values, marker receipt identity, actual watcher log and effects, fresh prior target inventory, and no-preemption conditions. Unreadable/missing evidence or unexpected effects require STOP and no automatic retry.

`/private/tmp/b1-post-marker-6835-20261108.remote.sh` SHA-256 `32f77b6d6b24eb4b435ecb75c983adb5adf91db74c1d455c62befe51a19d2ee2`; `/private/tmp/b1-post-marker-6835-20261108.local.sh` SHA-256 `9efc7ab52335c97bf4aa97ad1e21bb20bd53d0f4821761823e531753901bc73a`. The local script supplies remote block through SSH stdin with clean environment and captures the actual SSH exit in an exclusive private log and separate rc. Run it as a file, never as Bash stdin. Both passed `bash -n`. A bounded watcher provenance inference needs pre-marker absence, observed marker log, reviewed watcher path, post-marker owned file identity and no known competing action; it is not kernel proof.

## Remote

```bash
set -u
set -o pipefail
printf 'UTC '; date -u '+%Y-%m-%dT%H:%M:%SZ'; hostname
RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_6835_20261108_a
printf '\nMARKER AND STOP IDENTITY\n'
/usr/bin/python3 -I -B - <<'PY'
import os, stat, hashlib
for path in ('/home/dowling/r1_locks/trackx_evidence.active','/home/dowling/r1_tracks/out/smoke/STOP'):
 try:
  st=os.lstat(path)
  print('PATH',path,'dev',st.st_dev,'ino',st.st_ino,'uid',st.st_uid,'mode',oct(st.st_mode),'nlink',st.st_nlink,'size',st.st_size,'mtime_ns',st.st_mtime_ns,flush=True)
  if stat.S_ISREG(st.st_mode):
   fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW); cur=os.fstat(fd)
   if (cur.st_dev,cur.st_ino)!=(st.st_dev,st.st_ino): raise RuntimeError('identity changed')
   h=hashlib.sha256()
   while True:
    b=os.read(fd,65536)
    if not b: break
    h.update(b)
   os.close(fd); print('SHA256',path,h.hexdigest(),flush=True)
  else: print('NOT_REGULAR',path,flush=True)
 except FileNotFoundError: print('ABSENT',path,flush=True)
 except Exception as e: print('NOT_CHECKABLE',path,type(e).__name__,str(e),flush=True)
PY
printf 'identity_rc=%s\n' "$?"
for f in "$RUN_DIR/marker-receipt.json" "$RUN_DIR/status-receipt.md"; do
 printf '\nRECEIPT %s\n' "$f"
 if [ -f "$f" ] && [ ! -L "$f" ]; then sha256sum "$f"; printf 'receipt_sha_rc=%s\n' "$?"; cat "$f"; printf 'receipt_read_rc=%s\n' "$?"; else printf 'RECEIPT_NOT_CHECKABLE\n'; fi
done
printf '\nWATCHER LOG RECENT\n'
if [ -f /home/dowling/r1_tracks/logs/watch.log ] && [ ! -L /home/dowling/r1_tracks/logs/watch.log ]; then tail -n 40 /home/dowling/r1_tracks/logs/watch.log; printf 'watch_log_rc=%s\n' "$?"; else printf 'watch_log_NOT_CHECKABLE\n'; fi
printf '\nWATCHER SCRIPT HASH\n'; sha256sum /home/dowling/r1_tracks/bin/trks-watch; printf 'watch_hash_rc=%s\n' "$?"
printf '\nWATCHER TMUX METADATA\n'; tmux list-panes -a -F 'session=#{session_name} pane=#{pane_id} pid=#{pane_pid} command=#{pane_current_command}' | awk '/session=trks_watch /'; printf 'tmux_pipeline_rc=%s\n' "$?"
printf '\nCOLLECTOR PIDS\n'; pgrep -u "$(id -u)" -f 'python -m r1\.tracks\.collect .*--stop-file'; printf 'collector_rc=%s\n' "$?"
printf '\nTRACK P CANDIDATE PIDS\n'; pgrep -u "$(id -u)" -f '[p]3a|[t]rack.?p'; printf 'trackp_rc=%s\n' "$?"
printf '\nGPU\n'; nvidia-smi --query-gpu=index,uuid,memory.used,memory.total,utilization.gpu --format=csv; printf 'gpu_rc=%s\n' "$?"
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv; printf 'compute_rc=%s\n' "$?"
printf 'POST_MARKER_CAPTURE_COMPLETE\n'
```

## Local

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
SCRIPT=/private/tmp/b1-post-marker-6835-20261108.remote.sh
EXPECTED=32f77b6d6b24eb4b435ecb75c983adb5adf91db74c1d455c62befe51a19d2ee2
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-post-marker-6835-20261108.XXXXXXXX) || exit 1
set -C
exec 3> "$OUT/ssh.log"
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
if ssh -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=3 tasl7 'exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /bin/bash -s' < "$SCRIPT" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nSSH_EXIT=%s\n' "$rc" >&3 || exit 1
printf '%s\n' "$rc" > "$OUT/ssh.rc" || exit 1
shasum -a 256 "$SCRIPT" "$OUT/ssh.log" "$OUT/ssh.rc"
[ "$rc" -eq 0 ] || exit "$rc"
grep -qx POST_MARKER_CAPTURE_COMPLETE "$OUT/ssh.log" || exit 1
printf 'PRELIMINARY_RECEIPT_FOR_INDEPENDENT_REVIEW=%s\n' "$OUT"
```
