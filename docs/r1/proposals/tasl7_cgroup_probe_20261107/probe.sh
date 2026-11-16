#!/usr/bin/env bash
# DRAFT ENGINEERING_ONLY: execute only after exact-byte independent review.
set -euo pipefail
printf 'UTC: '; date -u +%FT%TZ
printf 'host: '; hostname -s
printf 'identity: '; id
[[ $(hostname -s) == TASL-7 && $(id -u) == 1011 && $HOME == /home/dowling ]] || { printf 'STOP: wrong host/account\n' >&2; exit 1; }
printf '%s\n' 'LOCK DIRECTORY'
ls -la "$HOME/r1_locks"
for repo in "$HOME/exam-x/work/agent_paper_B" "$HOME/r1_trackp/Agent_paper_B" "$HOME/r1_tracks/work/Agent_paper_B"; do
  p="$repo/docs/r1/STATUS.md"
  [[ ! -L $p && -f $p && -r $p ]] || { printf 'STOP: invalid STATUS %s\n' "$p" >&2; exit 1; }
  before=$(sha256sum "$p" | cut -d ' ' -f1)
  printf 'STATUS BEGIN %s sha256=%s\n' "$p" "$before"
  cat "$p"
  after=$(sha256sum "$p" | cut -d ' ' -f1)
  [[ $before == "$after" ]] || { printf 'STOP: STATUS changed during read\n' >&2; exit 1; }
  printf 'STATUS END %s sha256=%s\n' "$p" "$after"
done
printf '%s\n' 'GPU OBSERVATION'
gpu=$(nvidia-smi --query-gpu=uuid,utilization.gpu --format=csv,noheader,nounits)
printf '%s\n' "$gpu"
printf '%s\n' "$gpu" | awk -F, '
  { gsub(/^[[:space:]]+|[[:space:]]+$/, "", $1); gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2) }
  NR == 1 && NF == 2 && $1 == "GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1" &&
    $2 ~ /^[0-9]+([.][0-9]+)?$/ && ($2 + 0) <= 5 { ok = 1 }
  END { if (NR != 1 || !ok) exit 1 }
' || { printf 'STOP: GPU UUID or utilization differs\n' >&2; exit 1; }
apps=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits)
printf 'compute-app-pids: %s\n' "$apps"
[[ -z ${apps//[[:space:]]/} ]] || { printf 'STOP: GPU compute app present or census ambiguous\n' >&2; exit 1; }
command -v python3
python3 -I -S -B - <<'PY'
import ctypes
import os
import platform
import select
import stat
import subprocess
import sys
import time

NAME = 'paper-b-cgroup-probe-20261107-a94ce1891ef94f93'
D = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
F = os.O_NOFOLLOW | os.O_CLOEXEC
CHILD = r'''import os, select, sys
procs, ready, control = map(int, sys.argv[1:])
if os.write(procs, b'0\n') != 2: raise RuntimeError('enrollment short write')
os.close(procs)
if os.write(ready, b'R') != 1: raise RuntimeError('ready short write')
os.close(ready)
r, _, _ = select.select([control], [], [], 30)
if r:
    v = os.read(control, 1)
    if v not in (b'X', b''): raise RuntimeError('invalid control byte')
os.close(control)
'''

def marker_check():
    for marker in ('trackx_evidence.active', 'trackp_evidence.active'):
        p = '/home/dowling/r1_locks/' + marker
        try: os.lstat(p)
        except FileNotFoundError: continue
        raise RuntimeError('STOP: evidence marker present or ambiguous: ' + marker)
    print('evidence_markers: absent at observation', flush=True)

def fdinfo_pid(fd):
    with open('/proc/self/fdinfo/%d' % fd, encoding='ascii') as f:
        values = [line.split(':',1)[1].strip() for line in f if line.startswith('Pid:')]
    if len(values) != 1: raise RuntimeError('STOP: pidfd identity unavailable')
    return int(values[0])

def tick(pid):
    with open('/proc/%d/stat' % pid, encoding='ascii') as f: s = f.read()
    end = s.rfind(')')
    if end < 0: raise RuntimeError('STOP: malformed process stat')
    return int(s[end + 2:].split()[19])

def events(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    rows = os.read(fd, 4096).decode('ascii').splitlines()
    out = {}
    for row in rows:
        k, v = row.split()
        if k in out: raise RuntimeError('STOP: duplicate cgroup event')
        out[k] = int(v)
    return out

def until(fd, field, expected, seconds=10):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        values = events(fd)
        if values.get(field) == expected: return values
        time.sleep(0.02)
    raise RuntimeError('STOP: cgroup event not observed: %s=%s' % (field, expected))

if platform.system() != 'Linux' or platform.machine() != 'x86_64':
    raise RuntimeError('STOP: expected Linux x86_64')
print('system_python:', sys.executable, sys.version, flush=True)
marker_check()
rows = open('/proc/self/cgroup', encoding='ascii').read().splitlines()
paths = [row[3:] for row in rows if row.startswith('0::')]
if len(paths) != 1 or not paths[0].startswith('/'):
    raise RuntimeError('STOP: unified cgroup unavailable')
parts = [p for p in paths[0].split('/') if p]
if any(p in ('.', '..') for p in parts): raise RuntimeError('STOP: invalid membership path')
fds = []
child = None
try:
    fd = os.open('/sys/fs/cgroup', D); fds.append(fd)
    libc = ctypes.CDLL(None, use_errno=True)
    buf = ctypes.create_string_buffer(512)
    if libc.fstatfs(fd, ctypes.byref(buf)) != 0 or ctypes.c_long.from_buffer(buf).value != 0x63677270:
        raise RuntimeError('STOP: cgroup v2 not established')
    for part in parts:
        fd = os.open(part, D, dir_fd=fd); fds.append(fd)
    parent = fd
    info = os.fstat(parent)
    print('parent_membership:', paths[0], 'uid:', info.st_uid, 'inode:', info.st_ino, flush=True)
    if info.st_uid != os.getuid(): raise RuntimeError('STOP: current cgroup not owned by this UID')
    marker_check()
    os.mkdir(NAME, 0o700, dir_fd=parent)  # EEXIST is STOP; retain, never reuse.
    root = os.open(NAME, D, dir_fd=parent); fds.append(root)
    ri = os.fstat(root)
    if not stat.S_ISDIR(ri.st_mode) or ri.st_uid != os.getuid():
        raise RuntimeError('STOP: probe cgroup owner/type mismatch')
    print('retained_cgroup:', paths[0].rstrip('/') + '/' + NAME, 'inode:', ri.st_ino, flush=True)
    os.mkdir('worker', 0o700, dir_fd=root)
    leaf = os.open('worker', D, dir_fd=root); fds.append(leaf)
    if os.fstat(leaf).st_uid != os.getuid(): raise RuntimeError('STOP: worker cgroup owner mismatch')
    freeze = os.open('cgroup.freeze', os.O_WRONLY | F, dir_fd=root); fds.append(freeze)
    ev = os.open('cgroup.events', os.O_RDONLY | F, dir_fd=root); fds.append(ev)
    procs = os.open('cgroup.procs', os.O_WRONLY | F, dir_fd=leaf); fds.append(procs)
    leaf_ev = os.open('cgroup.events', os.O_RDONLY | F, dir_fd=leaf); fds.append(leaf_ev)
    print('initial_events:', events(ev), events(leaf_ev), flush=True)
    if events(ev).get('populated') != 0: raise RuntimeError('STOP: new cgroup populated')
    ready_r, ready_w = os.pipe2(os.O_CLOEXEC); fds.extend((ready_r, ready_w))
    ctrl_r, ctrl_w = os.pipe2(os.O_CLOEXEC); fds.extend((ctrl_r, ctrl_w))
    child = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', CHILD,
                              str(procs), str(ready_w), str(ctrl_r)],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             close_fds=True, pass_fds=(procs, ready_w, ctrl_r))
    for x in (ready_w, ctrl_r, procs): os.close(x); fds.remove(x)
    readable, _, _ = select.select([ready_r], [], [], 10)
    if not readable or os.read(ready_r, 1) != b'R': raise RuntimeError('STOP: child enrollment not confirmed')
    child_pidfd = os.pidfd_open(child.pid, 0); fds.append(child_pidfd)
    start = tick(child.pid)
    if fdinfo_pid(child_pidfd) != child.pid or select.select([child_pidfd], [], [], 0)[0]:
        raise RuntimeError('STOP: child pidfd not live')
    expected = paths[0].rstrip('/') + '/' + NAME + '/worker'
    with open('/proc/%d/cgroup' % child.pid, encoding='ascii') as f: membership = f.read().splitlines()
    if '0::' + expected not in membership or tick(child.pid) != start:
        raise RuntimeError('STOP: child membership/identity mismatch')
    until(ev, 'populated', 1)
    print('child_enrolled: PASS pid=%d start=%d' % (child.pid, start), flush=True)
    if os.write(freeze, b'1\n') != 2: raise RuntimeError('STOP: freeze short write')
    print('frozen_events:', until(ev, 'frozen', 1), flush=True)
    if fdinfo_pid(child_pidfd) != child.pid or select.select([child_pidfd], [], [], 0)[0] or tick(child.pid) != start:
        raise RuntimeError('STOP: child identity/liveness changed while frozen')
    print('freeze_observed: PASS', flush=True)
    os.lseek(freeze, 0, os.SEEK_SET)
    if os.write(freeze, b'0\n') != 2: raise RuntimeError('STOP: thaw short write')
    print('thawed_events:', until(ev, 'frozen', 0), flush=True)
    if os.write(ctrl_w, b'X') != 1: raise RuntimeError('STOP: child release short write')
    os.close(ctrl_w); fds.remove(ctrl_w)
    if child.wait(timeout=10) != 0: raise RuntimeError('STOP: child exit nonzero')
    print('owned_child_wait: 0', flush=True)
    print('final_events:', until(ev, 'populated', 0), flush=True)
    print('probe_complete: retained cgroup and worker cgroup; no cleanup', flush=True)
finally:
    # Never signal, remove cgroups or attempt automatic recovery on failure.
    # Closing the pipe makes an unfrozen child observe EOF; a frozen child may
    # remain frozen and must be reported for operator inspection without retry.
    for fd in reversed(fds):
        try: os.close(fd)
        except OSError: pass
PY
