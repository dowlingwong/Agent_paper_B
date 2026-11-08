# B1 6835 one-shot capacity capture — review only

No host action was performed. This fills the read-only refresh in `B1_CAPACITY_REFRESH_6835_20261108.md` at `52ccb201dd85cd01bd019e13944dd07ac257252e`; no server restart or PID check. Before a single use, independently review both exact scripts, freshness and authorization. Capture reports filesystem space/inodes, quota availability, aggregate memory/swap/load, CPU/affinity and checking process cgroup and PSI; any unavailable quota, actual B1 cgroup/assignment, server RSS or other data remain NOT CHECKABLE. Actual observed values and each command's rc require independent review; `CAPACITY_CAPTURE_COMPLETE` is merely evidence that the block reached its end, not that every constituent command succeeded, nor a launch approval. No retry after failure or uncertain state; preserve all capture files.

Run the local file, not a shell script passed on stdin. Its SHA is `334f3134c96867eae049b7beb76f49195f4467e44f2e61c788632ee527666afc`; remote script SHA is `843cfae62b5b0aafd0e2bde028ebb72972d16460a5778014c44c470ba69292d1`. SSH receives only the remote script; the local wrapper uses a private unique directory and writes the actual SSH exit to both log and separate rc. Environment is explicit and clean. Both files passed `bash -n`.

## Remote block

```bash
set -u
printf 'UTC '; date -u '+%Y-%m-%dT%H:%M:%SZ'; hostname
for p in /home/dowling/exam-x/work /home/dowling/exam-x/models; do
  printf '\nFILESYSTEM %s\n' "$p"
  df -Pk "$p"; printf 'df_bytes_rc=%s\n' "$?"
  df -Pi "$p"; printf 'df_inode_rc=%s\n' "$?"
done
if command -v quota >/dev/null 2>&1; then quota -s; printf 'quota_rc=%s\n' "$?"; else printf 'quota_NOT_CHECKABLE\n'; fi
printf '\nMEMORY\n'
awk '/^(MemTotal|MemAvailable|SwapTotal|SwapFree):/ {print}' /proc/meminfo; printf 'meminfo_rc=%s\n' "$?"
printf '\nLOAD\n'; cat /proc/loadavg; printf 'load_rc=%s\n' "$?"
printf '\nCPU\n'; getconf _NPROCESSORS_ONLN; printf 'cpu_rc=%s\n' "$?"
awk '/^Cpus_allowed_list:/ {print}' /proc/self/status; printf 'affinity_rc=%s\n' "$?"
printf '\nCGROUP_CHECKER_ONLY\n'; cat /proc/self/cgroup; printf 'cgroup_rc=%s\n' "$?"
for p in /proc/pressure/memory /proc/pressure/cpu; do
 if [ -r "$p" ]; then printf '%s\n' "$p"; cat "$p"; printf 'pressure_rc=%s\n' "$?"; else printf '%s NOT_CHECKABLE\n' "$p"; fi
done
printf "CAPACITY_CAPTURE_COMPLETE\n"
```

## Local wrapper

```bash
#!/bin/bash
set -u
set -o pipefail
umask 077
SCRIPT=/private/tmp/b1-capacity-refresh-6835-20261108.remote.sh
EXPECTED=843cfae62b5b0aafd0e2bde028ebb72972d16460a5778014c44c470ba69292d1
[ "$(shasum -a 256 "$SCRIPT" | awk '{print $1}')" = "$EXPECTED" ] || exit 1
OUT=$(mktemp -d /private/tmp/paper-b-6835-capacity-refresh-20261108.XXXXXXXX) || exit 1
set -C
exec 3> "$OUT/ssh.log"
printf 'PRIVATE_CAPTURE=%s\n' "$OUT"
if ssh -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=20 -o ServerAliveCountMax=3 tasl7 'exec env -i HOME=/home/dowling PATH=/usr/bin:/bin /bin/bash -s' < "$SCRIPT" >&3 2>&1; then rc=0; else rc=$?; fi
printf '\nSSH_EXIT=%s\n' "$rc" >&3 || exit 1
printf '%s\n' "$rc" > "$OUT/ssh.rc" || exit 1
shasum -a 256 "$SCRIPT" "$OUT/ssh.log" "$OUT/ssh.rc"
[ "$rc" -eq 0 ] || exit "$rc"
grep -qx CAPACITY_CAPTURE_COMPLETE "$OUT/ssh.log" || exit 1
printf 'PRELIMINARY_RECEIPT_FOR_INDEPENDENT_REVIEW=%s\n' "$OUT"
```
