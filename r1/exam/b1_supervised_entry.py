"""Isolated, no-output runner bootstrap waiting for supervisor release."""
import os
import sys


def main(argv):
    if len(argv)<4:
        return 2
    grant_fd,log_fd,exec_fd=map(int,argv[:3])
    command=argv[3:]
    if not command or not os.path.isabs(command[0]):
        return 2
    try:
        if os.read(grant_fd,1)!=b'G': return 2
        os.close(grant_fd)
        os.dup2(log_fd,1);os.dup2(log_fd,2)
        if log_fd not in (1,2): os.close(log_fd)
        os.set_inheritable(exec_fd,False)
        os.execve(command[0],command,os.environ)
    except BaseException:
        return 2


if __name__=='__main__':
    raise SystemExit(main(sys.argv[1:]))
