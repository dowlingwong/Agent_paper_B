# B1 capacity: current assessment and read-only refresh

**Planning assessment, not a reservation, measured B1 peak, gate or launch authority.** The configured `workers=20` remains unchanged. No host, model, GPU or experiment was accessed for this report. Reviewed exact candidate is `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb`; its config identifies `/home/dowling/exam-x/work` and `/home/dowling/exam-x/models`.

The independently accepted practical output estimate (`B1_PRACTICAL_OUTPUT_CAPACITY_REVIEW_20261108.md`, reviewing `d1219e3a`) uses the planned 260 roots and measured file-size metadata. Its 40 audit copies per root and 100× largest historical two-ledger size are assumptions: together they give 8.24 GiB, rounded to a **10 GiB planning allowance**, not a full-run bound. Its historical source roots are not full B1 outputs and synthetic fixtures do not represent native server, audit, log or state-version growth. The inventory at 2026-11-07 23:07:18 UTC recorded **584.95 GiB** free and **118,633,645 inodes** on the observed filesystem; after the existing 100,000,000,000-byte floor, 491.81 GiB remained. This is a preliminary operational judgment, not a current reservation, quota check or proof for another filesystem. The later bounded O2 snapshot at 2026-11-08 00:34 UTC reported about **584.62 GiB** free; it did not measure a B1 workload or inode quota. Check both actual filesystems, current quota/inodes, competing consumption and expected growth before launch; keep the existing floor and monitoring at least every 30 minutes, more frequently if necessary. Do not introduce a new fixed threshold.

The independently accepted 20-worker assessment (`B1_CPU_MEMORY_FEASIBILITY_20261108.md`, review `fd7be0361113b03bc424054ffcadefc9a0d493bf`) reports that same earlier inventory had **63,420,669,952 bytes MemAvailable**, 24 online CPUs and **1,106,530,304 bytes** swap in use. Small dataset dimensions do not bound fitted-model or process memory. At most 20 configuration audits may be concurrent; four seeds are sequential within each, while each active pool task can have a benchmark subprocess, and the resident runner and server also need resources. Existing actual-worker evidence has no representative 20-worker peak and no per-worker RAM bound; old availability does not establish current headroom. Use refreshed host availability, CPU affinity/quota where observable and current workload, plus host memory of the owned native server during already reviewed preflight; avoid double counting and disclose unknowns. A sum of RSS double-counts shared pages. If a specific unknown prevents a defensible estimate, assess the smallest separately reviewed bounded CPU-only measurement; do not automatically reduce workers, run a benchmark, or declare a new blanket benchmark gate.

## Exact site facts to refresh — review only

On the already authorized site-check window, an operator can capture the following as a **read-only** remote shell block via the independently reviewed SSH capture method with explicit stdin, clean environment, private exclusive local log, separate actual SSH rc, and no retry after failure. Review the filled wrapper and fresh no-preemption conditions first; this document does not perform or independently authorize a host action. Retain command errors and distinguish unavailable quota/pressure/affinity from a zero value. The cgroup and affinity below describe this checking process only, and may differ from the final B1 process. `df` values include filesystem free space rather than necessarily user quota; `quota` without a facility or permission is NOT CHECKABLE. Observe current owned server memory in the reviewed preflight using its verified PID/start identity and `/proc/<pid>/status` or `smaps_rollup` where readable, recording identity and read failures; do not inspect or signal other processes. The result must be reviewed together with actual final launch environment and workload, not interpreted as an upper bound.

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
```

On an inability to establish safe continuation, preserve outputs and use existing STOP semantics. Exact HEAD, receive, real author gate, native preflight and O2 handover remain separately reviewed.
