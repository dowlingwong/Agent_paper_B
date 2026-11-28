#!/bin/bash
exec 9>/home/dowling/r1_locks/gpu0.lock || exit 9
flock -n 9 || exit 9
exec 8>/home/dowling/r1_locks/cpus-16-31.lock || exit 8
flock -n 8 || exit 8
echo "checked_utc=$(date -u +%FT%TZ)"
echo "holder_pid=$$"
echo "--- /proc/locks matching the canonical inodes ---"
grep -E '(120088542|120091889)' /proc/locks
echo "--- lslocks ---"
lslocks 2>/dev/null | grep -E 'gpu0\.lock|cpus-16-31\.lock' || true
exec 9>&-
exec 8>&-
