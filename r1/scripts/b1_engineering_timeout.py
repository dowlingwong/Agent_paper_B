"""Bound one owned engineering test process group on Linux, including early root exit."""
import argparse
import os
import signal
import subprocess
import sys
import time


def observed_exit(child):
    # WNOWAIT preserves the child's PID/group identity until signalling finishes.
    info = os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    if info is None:
        return None
    return info.si_status if info.si_code == os.CLD_EXITED else -info.si_status


def stop_owned_group(child):
    # Refuse to signal an already reaped/non-child PID.
    observed_exit(child)
    try:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try: os.killpg(child.pid, sig)
            except ProcessLookupError: pass
            if sig == signal.SIGTERM: time.sleep(0.2)
    except BaseException:
        try:
            child.wait(timeout=30)
        except BaseException as wait_error:
            try: print('STOP: additional owned-root wait failure:', wait_error, file=sys.stderr)
            except Exception: pass
        raise
    else:
        child.wait(timeout=30)


def run(command, seconds):
    if not sys.platform.startswith('linux') or not hasattr(os, 'waitid'):
        raise RuntimeError('Linux waitid required')
    interrupted = []
    previous = {}
    def note_signal(signum, frame):
        interrupted.append(signum)
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        previous[sig] = signal.signal(sig, note_signal)
    child = None
    shutdown_attempted = False
    try:
        child = subprocess.Popen(command, start_new_session=True)
        deadline = time.monotonic() + seconds
        while True:
            status = observed_exit(child)
            if status is not None or interrupted or time.monotonic() >= deadline:
                break
            time.sleep(0.05)
        shutdown_attempted = True
        stop_owned_group(child)
        child = None
        if interrupted:
            print('STOP: engineering test interrupted by signal', interrupted[0], file=sys.stderr)
            return 128 + interrupted[0]
        if status is None:
            print('STOP: engineering test deadline', file=sys.stderr)
            return 124
        return status if status >= 0 else 128 - status
    finally:
        if child is not None and not shutdown_attempted:
            try: stop_owned_group(child)
            except (OSError, subprocess.SubprocessError) as exc:
                print('STOP: owned test group shutdown failed:', exc, file=sys.stderr)
        for sig, handler in previous.items(): signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.seconds <= 0 or not args.command: parser.error('positive seconds and command required')
    return run(args.command, args.seconds)


if __name__ == '__main__': sys.exit(main())
