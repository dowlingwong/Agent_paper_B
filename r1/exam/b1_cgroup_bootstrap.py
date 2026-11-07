"""Join an already-owned B1 cgroup before executing any workload.

Invoked with an isolated Python interpreter (-I -S -B), never with site hooks.
Inherited descriptors are exclusively supplied by the reviewed parent.
"""
import os
import sys


def main(argv):
    if len(argv) < 7:
        return 2
    procs_fd, ready_fd, grant_fd, stdout_fd, stderr_fd, exec_fd = map(int, argv[:6])
    command = argv[6:]
    if not command or not os.path.isabs(command[0]):
        return 2
    try:
        if os.write(procs_fd, b'0\n') != 2:
            raise OSError('short self-enrollment')
        os.close(procs_fd)
        if os.write(ready_fd, b'M') != 1:
            raise OSError('short enrollment acknowledgement')
        os.close(ready_fd)
        if os.read(grant_fd, 1) != b'G':
            return 2
        os.close(grant_fd)
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        for fd in {stdout_fd, stderr_fd}:
            if fd not in (1, 2):
                os.close(fd)
        # Parent observes this descriptor close only at exec or process exit;
        # it must also verify the live executable and command line.
        os.set_inheritable(exec_fd, False)
        os.execve(command[0], command, os.environ)
    except BaseException:
        # No diagnostic to a batch log before successful enrollment/grant.
        # Parent handles a missing acknowledgement as a STOP.
        return 2


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
