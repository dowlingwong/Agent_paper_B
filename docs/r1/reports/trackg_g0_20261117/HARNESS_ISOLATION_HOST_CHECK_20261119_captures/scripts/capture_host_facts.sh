#!/bin/bash
# G0 host-condition capture (read-only). Run on Ada as uid 1030; writes nothing but stdout.
set -u
echo "=== utc"; date -u +%Y-%m-%dT%H:%M:%SZ
echo "=== host"; hostname; uname -a
echo "=== uid"; id
echo "=== python interpreters"; which -a python3; /usr/bin/python3 -V
echo
echo "=== sysctl: unprivileged userns / apparmor / yama"
for key in kernel.unprivileged_userns_clone kernel.apparmor_restrict_unprivileged_userns \
           kernel.apparmor_restrict_unprivileged_unconfined kernel.unprivileged_userns_apparmor_policy \
           user.max_user_namespaces kernel.yaml/ptrace_scope; do
  printf '%s = ' "$key"; sysctl -n "$key" 2>&1 | head -1
done
cat /proc/sys/user/max_user_namespaces 2>&1 | sed 's/^/proc max_user_namespaces = /'
cat /proc/sys/kernel/yama/ptrace_scope 2>&1 | sed 's/^/proc ptrace_scope = /'
echo "apparmor enabled = $(cat /sys/module/apparmor/parameters/enabled 2>&1)"
ls /sys/kernel/security/apparmor 2>&1
echo "LSM list = $(cat /sys/kernel/security/lsm 2>&1)"
echo
echo "=== cgroup v2"
stat -fc %T /sys/fs/cgroup
grep cgroup /proc/mounts
echo "self cgroup: $(cat /proc/self/cgroup)"
echo "cgroup.controllers (root): $(cat /sys/fs/cgroup/cgroup.controllers 2>&1)"
echo "cgroup.kill at root: $([ -e /sys/fs/cgroup/cgroup.kill ] && echo present || echo absent)"
echo
echo "=== systemd user manager"
loginctl show-user "$(id -un)" -p Linger 2>&1
systemctl --user is-system-running 2>&1
systemctl --user show -p ControlGroup -p Delegate 2>&1
echo "XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-}"
P=/sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service
echo "user manager cgroup: $P"
ls -ld "$P" 2>&1
echo "subtree_control: $(cat "$P/cgroup.subtree_control" 2>&1)"
echo "cgroup.procs writable: $([ -w "$P/cgroup.procs" ] && echo yes || echo no)"
echo "cgroup.kill present: $([ -e "$P/cgroup.kill" ] && echo yes || echo no)"
echo
echo "=== /sys mount flags (the sandbox's remount target)"
grep -E '^sysfs /sys ' /proc/mounts
echo "=== submount count under /sys: $(grep -c ' /sys/' /proc/mounts)"
echo
echo "=== nvidia"
nvidia-smi --query-gpu=index,uuid,name,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1
echo "compute apps:"; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>&1
