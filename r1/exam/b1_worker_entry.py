"""Production B1 worker bootstrap: no log attachment before parent release."""
import argparse
import json
from pathlib import Path

from r1.exam.b1_worker_handoff import await_parent, attach_log


def main(argv=None):
    released=False
    try:
        p=argparse.ArgumentParser();p.add_argument('--job',required=True);a=p.parse_args(argv)
        job=json.loads(Path(a.job).read_text())
        if job.get('phase')!='b1' or job.get('dryrun'):
            raise RuntimeError('STOP: production B1 bootstrap requires B1 evidence job')
        await_parent(job)
        attach_log(job)
        released=True
        # Delayed until after release: campaign imports the harness and node
        # dependencies and must not run as part of an unreleased child.
        from r1.exam.campaign import collect
        collect(job)
    except BaseException:
        if not released:
            # stdout/stderr are DEVNULL until attach_log; do not print a
            # post-STOP traceback to the new root. Parent records its error.
            return 2
        raise
    return 0


if __name__=='__main__': raise SystemExit(main())
