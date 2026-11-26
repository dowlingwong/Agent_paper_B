#!/bin/bash
# ENGINEERING-ONLY TASL-2 G.5 job-path smoke (20261123).
# No G.5 authorization, label, evidence row, seal, commit or push. Synthetic
# spec + fake harness engine; the real sweep2/t1_tasl/g5_job.run_job and the
# real delegated-scope wrapper argv.
set -u
S=/home/dowling/r1_engineering/tasl2_g5_smoke_20261123
PAPER=/home/dowling/r1_tracks/t1_tasl/paper_g5smoke
LOGS=$S/logs
CAP=$S/captures
STATUS=$LOGS/status.txt
export SMOKE_ROOT=$S SMOKE_PAPER=$PAPER
UIDN=$(id -u)
mkdir -p "$LOGS" "$CAP/jobs" "$S/work/meta" "$S/work/base" "$S/_moved_aside"
# the previous trial trees are moved aside (never deleted)
[ -d "$S/runs" ] && [ -n "$(ls -A "$S/runs" 2>/dev/null)" ] && \
    mv "$S/runs" "$S/_moved_aside/runs-$(date -u +%Y%m%dT%H%M%SZ)"
[ -d "$CAP/jobs" ] && [ -n "$(ls -A "$CAP/jobs" 2>/dev/null)" ] && \
    mv "$CAP/jobs" "$S/_moved_aside/captures-jobs-$(date -u +%Y%m%dT%H%M%SZ)"
[ -f "$S/work/sibling_ready.json" ] && mv "$S/work/sibling_ready.json" "$S/_moved_aside/"
mkdir -p "$S/runs" "$CAP/jobs"
: > "$STATUS"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$STATUS"; }

make_fake_harness() {          # $1 = target dir
  if [ -e "$1" ]; then mv "$1" "$S/_moved_aside/$(basename "$1")-$(date -u +%Y%m%dT%H%M%SZ)"; fi
  cp -a "$S/fake_harness_src" "$1"
  git -C "$1" init -q
  git -C "$1" -c user.name=smoke -c user.email=smoke@local add -A
  git -C "$1" -c user.name=smoke -c user.email=smoke@local commit -qm \
      "synthetic G.5 engine (g5_tasl_engine_contract/1) for the ENGINEERING smoke; not the reviewed engine"
}

run_job() {                    # $1 kind, $2 node, $3 scenario, optional $4 = job-kill
  local kind=$1 node=$2 scen=$3 mode=${4:-job}
  local name="${node}_${kind}_${scen}"
  taskset -c 16-31 "$S/bin/smoke_wrapper.sh" "$mode" "$kind" "$node" "$scen" > "$LOGS/$name.log" 2>&1
  local rc=$?
  echo "wrapper_rc=$rc" >> "$LOGS/$name.log"
  log "job $name mode=$mode rc=$rc"
  return 0
}

# --------------------------------------------------------------------------- 0. fake harness checkouts
log "BUILD fake harness repos"
make_fake_harness "$S/fake_harness_g7" || { log "STOP: fake_harness_g7"; exit 1; }
make_fake_harness "$S/fake_harness_ar" || { log "STOP: fake_harness_ar"; exit 1; }
for d in fake_harness_g7 fake_harness_ar; do
  { echo "== $d =="; git -C "$S/$d" rev-parse HEAD; git -C "$S/$d" status --porcelain;
    sha256sum "$S/$d/src/autoresearch/trackg/audit_g5.py"; } >> "$LOGS/fake_harness.txt" 2>&1
done
log "SPEC build"
taskset -c 16-31 python3 "$S/bin/build_spec.py" > "$LOGS/build_spec.log" 2>&1 || { log "STOP: build_spec"; exit 1; }
sha256sum "$S/spec/smoke_spec.json" "$S/spec/server_record.json" > "$CAP/spec_files.sha256"

# --------------------------------------------------------------------------- 1. host/scope probe (a,b,c)
log "PROBE scope"
taskset -c 16-31 systemd-run --user --scope --unit="smoke-sibling-probe-$$" sleep 90 \
    > "$S/work/probe_sibling.log" 2>&1 &
SIBPROBE=$!
sleep 1
taskset -c 16-31 "$S/bin/smoke_wrapper.sh" probe > "$LOGS/probe.log" 2>&1
echo "probe_wrapper_rc=$?" >> "$LOGS/probe.log"
kill "$SIBPROBE" 2>/dev/null
wait "$SIBPROBE" 2>/dev/null
systemctl --user stop "smoke-sibling-probe-$$.scope" 2>/dev/null
log "PROBE done"

# --------------------------------------------------------------------------- 2. the literal g5 wrapper branch
log "LITERAL wrapper g5 branch (fail-closed switch, no note)"
timeout 120 taskset -c 16-31 bash "$PAPER/sweep2/t1_tasl/t1_tasl_node.sh" g5 "$S/spec/smoke_spec.json" \
    smoke_ok "$S/spec/NO-SIGNED-NOTE-ENGINEERING.md" campaigns-wave1 - --enable \
    > "$LOGS/literal_g5_wrapper.log" 2>&1
echo "literal_wrapper_rc=$?" >> "$LOGS/literal_g5_wrapper.log"
log "LITERAL wrapper done"

# --------------------------------------------------------------------------- 3. campaign+audit pairs
log "SCENARIO smoke_ok"
run_job campaigns smoke_ok normal
run_job audits   smoke_ok normal
log "SCENARIO smoke_oom"
run_job campaigns smoke_oom normal
run_job audits   smoke_oom oom
log "SCENARIO smoke_crash"
run_job campaigns smoke_crash normal
run_job audits   smoke_crash crash
log "SCENARIO smoke_infra"
run_job campaigns smoke_infra normal
run_job audits   smoke_infra infra
log "SCENARIO smoke_gate"
run_job campaigns smoke_gate normal
run_job audits   smoke_gate gate-row
log "SCENARIO smoke_deadline (65 s)"
run_job campaigns smoke_deadline normal
run_job audits   smoke_deadline deadline-child
log "SCENARIO smoke_kill (deliberate engine kill)"
run_job campaigns smoke_kill normal
run_job audits   smoke_kill deliberate-kill job-kill
log "SCENARIO smoke_cpu"
run_job campaigns smoke_cpu normal
run_job audits   smoke_cpu normal
log "SCENARIO smoke_stopdl (campaign engine deadline STOP)"
run_job campaigns smoke_stopdl engine-deadline
run_job campaigns smoke_stopdl normal            # refused: node has a node STOP on record
log "SCENARIO smoke_stopdl_a (audit engine deadline STOP)"
run_job campaigns smoke_stopdl_a normal
run_job audits   smoke_stopdl_a engine-deadline
log "SCENARIO smoke_timing (median run over the basis)"
run_job campaigns smoke_timing slow-run

# --------------------------------------------------------------------------- 4. orphan rule ((b),(d), item 11)
log "SCENARIO smoke_orphan: populated ar_* in a sibling scope, refusal, inspect/clear, rerun"
taskset -c 16-31 "$S/bin/smoke_wrapper.sh" orphan > "$LOGS/smoke_orphan_rule.log" 2>&1
echo "orphan_wrapper_rc=$?" >> "$LOGS/smoke_orphan_rule.log"
log "SCENARIO smoke_orphan done"

# --------------------------------------------------------------------------- 5. final hygiene
log "FINAL hygiene"
{
  echo "== lease =="; ls -la "$HOME/r1_locks/" 2>&1
  echo "== gpu apps =="; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
  echo "== app.slice scopes and ar_* =="
  for sc in /sys/fs/cgroup/user.slice/user-$UIDN.slice/user@$UIDN.service/app.slice/*; do
    [ -d "$sc" ] || continue
    echo "scope $(basename "$sc")"
    for ar in "$sc"/ar_*; do [ -d "$ar" ] && { echo "  ar=$ar"; cat "$ar/cgroup.events" 2>/dev/null; }; done
  done
  echo "== scopes at end =="; systemctl --user list-units 'run-*.scope' --no-legend 2>&1 | head -10
} > "$LOGS/final_hygiene.txt" 2>&1
log "ANALYZE"
taskset -c 16-31 python3 "$S/bin/analyze.py" > "$LOGS/analyze.log" 2>&1
echo "analyze_rc=$?" >> "$LOGS/analyze.log"

# --------------------------------------------------------------------------- 6. capture checksums
(cd "$CAP" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
(cd "$S/runs" 2>/dev/null && find . -name job_record.json -o -name diagnostics.json -o -name out.tar | sort | \
  xargs -r sha256sum > "$CAP/runs_job_artifacts.sha256")
sha256sum "$S/bin/"*.py "$S/bin/"*.sh > "$CAP/smoke_code.sha256"
log "DONE"
