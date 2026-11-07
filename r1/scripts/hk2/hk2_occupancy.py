"""Pure classification of already observed processes on one GPU; no site access.

The caller must independently establish device identity, complete visibility,
process type, memory and descendant identity. This helper cannot do so and
is not wired into a runner or an authorization gate.
"""


class OccupancyError(ValueError):
    pass


def classify_processes(processes, *, startup, ignore_below_mib):
    """Return every supplied row for one GPU with classification and blocking status.

    A later check may ignore positively identified owned descendants. At
    startup no such exclusion is applied. The caller explicitly supplies the
    memory threshold; the runbook's 256 MiB is proposed, not selected here.
    """
    if type(startup) is not bool:
        raise OccupancyError('startup must be boolean')
    if type(ignore_below_mib) is not int or ignore_below_mib < 0:
        raise OccupancyError('invalid memory threshold')
    if not isinstance(processes, (list, tuple)):
        raise OccupancyError('processes must be a complete supplied list')
    output = []
    seen = set()
    for row in processes:
        if not isinstance(row, dict):
            raise OccupancyError('invalid process row')
        pid, kind, memory = row.get('pid'), row.get('type'), row.get('memory_mib')
        descendant = row.get('owned_descendant')
        if type(pid) is not int or pid <= 0 or pid in seen:
            raise OccupancyError('invalid or duplicate PID')
        if kind not in ('C', 'G', 'C+G'):
            raise OccupancyError('unknown process type')
        if type(memory) is not int or memory < 0:
            raise OccupancyError('unknown process memory')
        if type(descendant) is not bool:
            raise OccupancyError('unknown descendant status')
        seen.add(pid)
        if kind == 'G': reason = 'graphics'
        elif memory < ignore_below_mib: reason = 'below_threshold'
        elif not startup and descendant: reason = 'owned_descendant'
        else: reason = 'blocking'
        output.append(dict(row, classification=reason, blocking=reason == 'blocking'))
    return output
