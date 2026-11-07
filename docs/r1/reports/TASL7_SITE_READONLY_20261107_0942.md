# TASL-7 read-only site and input observations — 7 November 2026, 09:42 CET

AI-assisted (Codex). This ENGINEERING_ONLY observation follows the author's 09:36 instruction recorded in PLAN §10 `R1-TASL7-AGENT-OCCUPANCY-07NOV`. At 08:42:34 UTC (09:42:34 CET), one SSH session read `~/r1_locks`, the three existing checkout STATUS files, mount/cgroup information, two Stage A tables and the pinned server binary, and queried GPU state. It did not intentionally start a model/GPU workload, acquire a lease, signal a process or write a remote file. Tool side effects and concurrent host changes were not independently monitored. The complete local capture is `/private/tmp/tasl7-site-readonly-20261107-0943.txt`, SHA-256 `1d6ff1ffa3652eba65ecadd5cdb152076e852ee04cd41ac1e46935170e9632ad`; the full STATUS text is kept locally, not reproduced here.

```bash
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > /private/tmp/tasl7-site-readonly-20261107-0943.txt 2>&1 <<'REMOTE'
set -u
date -u
hostname
ls -la "$HOME/r1_locks"
for repo in "$HOME/exam-x/work/agent_paper_B" "$HOME/r1_trackp/Agent_paper_B" "$HOME/r1_tracks/work/Agent_paper_B"; do
  printf '\nCHECKOUT %s\n' "$repo"
  if test -f "$repo/docs/r1/STATUS.md" && test -r "$repo/docs/r1/STATUS.md"; then sha256sum "$repo/docs/r1/STATUS.md"; cat "$repo/docs/r1/STATUS.md"; else printf 'STATUS_MISSING_OR_UNREADABLE\n'; fi
done
printf '\nWORK MOUNT\n'
findmnt -T "$HOME/exam-x/work" -o TARGET,SOURCE,FSTYPE,OPTIONS
printf '\nCGROUP OBSERVATION\n'
uname -srmo
cat /proc/self/cgroup
cat /sys/fs/cgroup/cgroup.controllers
ls -ld /sys/fs/cgroup "$HOME/exam-x/work" "$HOME/exam-x/models"
printf '\nPINNED INPUTS\n'
for path in "$HOME/exam-x/work/r1_stagea_20261103_t7h8/stage_a_table.json" "$HOME/exam-x/work/r1_stagea_20261104_t7j10/stage_a_table.json" "$HOME/exam-x/work/llama.cpp/build-exam/bin/llama-server"; do
  if test -f "$path" && test -r "$path"; then sha256sum "$path"; else printf 'MISSING_OR_UNREADABLE %s\n' "$path"; fi
done
printf '\nGPU CENSUS\n'
nvidia-smi --query-gpu=index,uuid,memory.used,memory.total,utilization.gpu --format=csv
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv
REMOTE
result=$?
shasum -a 256 /private/tmp/tasl7-site-readonly-20261107-0943.txt
exit "$result"
```

All three STATUS files were readable. This command prints a missing-file marker but does not fail the entire session on a missing STATUS or other individual command failure; the reported observations below are tied to the captured outputs, not inferred from its overall exit status.

`findmnt -T /home/dowling/exam-x/work` reported `/` on `/dev/nvme0n1p2`, filesystem `ext4`, options `rw,relatime,errors=remount-ro`. This is a point-in-time mount observation, not proof that a subsequently created batch has the same mount ID, that rename error behavior is safe, or that a particular cgroup delegation is usable. `uname` reported Linux `6.8.0-138-generic x86_64`; `/proc/self/cgroup` reported a unified `0::/user.slice/user-1011.slice/session-61138.scope` and `/sys/fs/cgroup/cgroup.controllers` listed `cpuset cpu io memory hugetlb pids rdma misc`. Cgroup creation, freezer, pidfd, kcmp, delegation and process ownership were not tested.

The following observed SHA-256 values match the then-current B1 config `r1/scripts/configs/exam_b1_v2.json`: Stage A primary table `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c`; Stage A amendment table `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103`; and `llama-server` binary `b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b`. These are point-in-time file reads, not proof of later inode stability, loaded executable identity, templates or model hashes.

The GPU query reported `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, 236/24564 MiB used, 0% utilization and no listed compute apps. It did not obtain a flock or establish future exclusivity. The separate approved note, final checkout, clean-state verification, worker Python binding, real worker determinism, reviewed handover and B1 phase gates remain incomplete. **No B1 launch is authorized by this observation.** Once local code, review and author-note prerequisites are ready, the operator must repeat the applicable fresh held-lock, server descriptor, worker/Python, GPU, disk, cgroup/filesystem and handover checks. Independent review of this observation is required.
