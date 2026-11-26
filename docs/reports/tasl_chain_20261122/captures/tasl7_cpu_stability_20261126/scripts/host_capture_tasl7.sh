#!/bin/bash
# TASL-7 CPU stability check - read-only host facts capture (no sudo, no system change).
set -u
E=/home/dowling/r1_engineering/metamaze_20261125/tasl7_cpu_stability_20261126
H=$E/host
mkdir -p "$H"
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# ---------------------------------------------------------------- cpuinfo / os / kernel
{
  echo "=== utc $(ts)"
  echo "=== uname"; uname -a
  echo "=== os"; (grep -E 'PRETTY_NAME|^NAME|^VERSION' /etc/os-release)
  echo "=== cpuinfo keys"; grep -E '^(processor|cpu family|model|model name|stepping|microcode|cpu MHz|cpu cores|siblings|physical id|vendor_id|bogomips|cache size)' /proc/cpuinfo | sed 's/[[:space:]]*$//' | sort | uniq -c | sed 's/^ *//'
  echo "=== microcode unique"; grep -E '^microcode' /proc/cpuinfo | sort | uniq -c
  echo "=== model/microcode per-cpu"; grep -E '^(processor|model|model name|stepping|microcode)' /proc/cpuinfo | paste - - - - - 2>/dev/null | head -30
  echo "=== kernel cmdline"; cat /proc/cmdline
  echo "=== dmesg_restrict"; cat /proc/sys/kernel/dmesg_restrict
  echo "=== kptr_restrict"; cat /proc/sys/kernel/kptr_restrict
  echo "=== ptrace_scope"; cat /proc/sys/kernel/yama/ptrace_scope
  echo "=== uptime"; uptime
  echo "=== boot"; who -b 2>&1
  echo "=== last reboots"; last -x reboot 2>&1 | head -6
} > "$H/cpuinfo.txt"

lscpu > "$H/lscpu.txt" 2>&1
lscpu -J > "$H/lscpu.json" 2>&1

# ---------------------------------------------------------------- topology / freq / governor / power
{
  echo "=== lscpu -e"
  lscpu -e
  echo "=== topology per cpu"
  for c in /sys/devices/system/cpu/cpu[0-9]*; do
    n=${c##*/cpu}
    core=$(cat "$c/topology/core_id" 2>/dev/null)
    sib=$(cat "$c/topology/thread_siblings_list" 2>/dev/null)
    maxf=$(cat "$c/cpufreq/cpuinfo_max_freq" 2>/dev/null)
    minf=$(cat "$c/cpufreq/cpuinfo_min_freq" 2>/dev/null)
    cur=$(cat "$c/cpufreq/scaling_cur_freq" 2>/dev/null)
    gov=$(cat "$c/cpufreq/scaling_governor" 2>/dev/null)
    epp=$(cat "$c/cpufreq/energy_performance_preference" 2>/dev/null)
    echo "cpu$n  core_id=$core siblings=$sib maxfreq=$maxf minfreq=$minf curfreq=$cur governor=$gov epp=$epp"
  done
  echo "=== cpufreq driver"; cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver 2>&1
  echo "=== global governor (cpufreq policy)"; cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor 2>&1
  echo "=== amd_pstate status"; cat /sys/devices/system/cpu/amd_pstate/status 2>&1
  echo "=== boost"; cat /sys/devices/system/cpu/cpufreq/boost 2>&1; cat /sys/devices/system/cpu/cpufreq/policy0/boost 2>&1
  echo "=== epp avail"; cat /sys/devices/system/cpu/cpufreq/policy0/energy_performance_available_preferences 2>&1
  echo "=== cppc"; ls /sys/devices/system/cpu/cpu0/cpufreq/ | sort
  echo "=== dmi"; for f in sys_vendor product_name board_name bios_vendor bios_version bios_date; do echo -n "$f: "; cat /sys/class/dmi/id/$f 2>&1; done
  echo "=== thermal throttle (package/core counters, context only)"
  for f in /sys/devices/system/cpu/cpu*/thermal_throttle/*; do [ -f "$f" ] && echo "$f = $(cat "$f" 2>/dev/null)"; done | head -8
  echo "=== powercap/rapl"
  ls /sys/class/powercap 2>&1 | head
  echo "=== machinecheck"
  ls -d /sys/devices/system/machinecheck/machinecheck* 2>/dev/null | wc -l
  cat /sys/devices/system/machinecheck/machinecheck0/check_interval 2>&1
  echo "=== edac"
  ls /sys/devices/system/edac/mc 2>&1
  echo "=== cgroup/systemd user"
  cat /proc/self/cgroup
  loginctl show-user dowling 2>&1 | head -8
  echo "=== mem/swap"; free -b
  echo "=== nproc/online"; nproc; cat /sys/devices/system/cpu/online
} > "$H/admin_extra.txt"

# ---------------------------------------------------------------- AMD microcode provenance
{
  echo "=== /proc/cpuinfo microcode (unique) $(ts)"
  grep -E '^microcode' /proc/cpuinfo | sort | uniq -c
  echo "=== signature for this CPU (family 25 model 97 -> 0xa60f12?)"
  grep -m1 -E '^(cpu family|model|stepping)' /proc/cpuinfo
  echo "=== dpkg amd64-microcode"
  dpkg -l amd64-microcode 2>&1 | tail -3
  echo "=== ucode file(s) /lib/firmware/amd-ucode"
  ls -l /lib/firmware/amd-ucode 2>&1 | head
  sha256sum /lib/firmware/amd-ucode/* 2>/dev/null | head
  echo "=== early load initrd"
  ls -l /boot/initrd.img-$(uname -r) 2>&1
  echo "=== microcode sysfs"
  ls /sys/devices/system/cpu/microcode 2>&1
  cat /sys/devices/system/cpu/microcode/reload 2>&1
  echo "=== reload check (read-only; writing reload needs root)"
  echo "=== dmesg ucode messages attempt"
  dmesg 2>&1 | grep -i -E 'microcode|ucode' | head -5 || true
  echo "=== dmesg rc above"
} > "$H/admin_microcode_probe.txt"

# ---------------------------------------------------------------- read-only privilege / event log probes
{
  echo "=== UTC $(ts) - read-only kernel/hardware event log probes (no sudo)"
  echo "--- privilege facts"
  id; grep -E 'CapEff|CapPrm' /proc/self/status; echo "sudo groups: $(groups)"
  echo "--- dmesg"; dmesg 2>&1 | head -3; echo "dmesg_rc=$?"
  echo "--- journalctl -k --since 2026-11-20"; journalctl -k --since 2026-11-20 2>&1 | head -5
  echo "--- file log perms"; ls -l /var/log/syslog /var/log/kern.log /var/log/dmesg 2>&1
  echo "--- read attempts"; head -1 /var/log/kern.log 2>&1; head -1 /var/log/syslog 2>&1
  echo "--- kernel log alternatives"; ls -l /dev/kmsg /proc/kmsg 2>&1
  echo "--- /sys/fs/pstore"; ls -la /sys/fs/pstore 2>&1
  echo "--- coredumpctl/rasdaemon/mcelog"; which coredumpctl rasdaemon mcelog 2>&1; ls /var/crash 2>&1
} > "$H/admin_readonly_probe.txt"

{
  echo "=== UTC $(ts) - read-only kernel/hardware event log search (no sudo)"
  patterns=("mce" "Machine check" "Machine Check" "trap invalid opcode" "invalid opcode" "general protection" "segfault" "SIGSEGV" "SIGILL" "Hardware Error" "MCE" "microcode")
  for p in "${patterns[@]}"; do
    k=$(journalctl -k --since 2026-11-20 --no-pager 2>/dev/null | grep -c -F -- "$p" || true)
    a=$(journalctl --since 2026-11-20 --no-pager 2>/dev/null | grep -c -F -- "$p" || true)
    u=$(journalctl --user --since 2026-11-20 --no-pager 2>/dev/null | grep -c -F -- "$p" || true)
    printf 'pattern %-22s journal-k=%s journal-all=%s journal-user=%s\n' "$p" "$k" "$a" "$u"
  done
  echo "--- journal visibility hint"
  journalctl -k --since 2026-11-20 --no-pager 2>&1 | head -3
} > "$H/kernel_log_search_readonly.txt"

echo "HOST_CAPTURE_DONE $(ts)"
ls -l "$H"
