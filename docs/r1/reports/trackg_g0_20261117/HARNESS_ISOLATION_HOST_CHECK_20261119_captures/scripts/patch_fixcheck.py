"""G0 confirm: patch a SCRATCH copy (/tmp/ada_iso_fixcheck) of the harness so a bind remount preserves the
source mount's locked flags (nosuid/nodev/noexec). Not an accepted change: diagnostic only.
"""
import sys

p = "/tmp/ada_iso_fixcheck/src/autoresearch/trackg/node_lib/ar_isolated.py"
t = open(p).read()

bad = """                remount = (_MS_BIND | _MS_REMOUNT | _MS_NOSUID | _MS_NODEV | _MS_NOEXEC
                       | (_MS_RDONLY if read_only else 0))"""
good = """                locked = _source_mount_flags(src)
                remount = _MS_BIND | _MS_REMOUNT | (_MS_RDONLY if read_only else 0) | locked"""
if t.count(bad) != 1:
    # the earlier naive patch may not be present if this runs on a fresh scratch copy: patch the original line
    bad = "remount = _MS_BIND | _MS_REMOUNT | _MS_NOSUID | (_MS_RDONLY if read_only else 0)"
    if t.count(bad) != 1:
        raise SystemExit("neither the naive nor the original remount line found")
t = t.replace(bad, good)

anchor = "def _sandbox_preexec(config: dict):"
helper = '''_MS_FLAG_NAMES = {"nosuid": _MS_NOSUID, "nodev": _MS_NODEV, "noexec": _MS_NOEXEC}


def _source_mount_flags(path: str) -> int:
    """The locked access flags (nosuid/nodev/noexec) of the mount that holds *path*: a bind remount must keep
    every flag the source mount has set, or the kernel refuses the remount with EPERM in a user namespace."""
    real = os.path.realpath(path)
    best, flags = "", 0
    try:
        with open("/proc/self/mountinfo") as handle:
            lines = handle.read().splitlines()
    except OSError:
        return 0
    for line in lines:
        left, _, _right = line.partition(" - ")
        parts = left.split()
        if len(parts) < 6:
            continue
        point = parts[4]
        if (real == point or real.startswith(point.rstrip("/") + "/")) and len(point) > len(best):
            best, flags = point, 0
            for name in parts[5].split(","):
                flags |= _MS_FLAG_NAMES.get(name, 0)
    return flags


'''
assert t.count(anchor) == 1
t = t.replace(anchor, helper + anchor)
open(p, "w").write(t)
print("scratch patch applied: bind remount preserves source locked flags")
