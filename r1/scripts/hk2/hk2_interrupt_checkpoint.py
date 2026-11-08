"""Cooperative USR1 flag and owned-unit archive primitive, not a job runner.

The caller must quiesce its own unit writers, validate job/unit provenance and
invoke checkpoint promptly after a signal. This helper does not control any
child, submit work, re-run, authenticate history or provide crash durability.
"""
import os
import re
import signal
import stat
from pathlib import Path


class CheckpointError(RuntimeError):
    pass


def _existing_directory(raw):
    path = Path(raw)
    if not path.is_absolute() or '..' in path.parts:
        raise CheckpointError('absolute non-traversing directory required')
    try:
        if str(path) != os.path.realpath(path):
            raise CheckpointError('symlink or alias in directory path')
        info = path.lstat()
    except OSError as exc:
        raise CheckpointError('directory unavailable') from exc
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise CheckpointError('directory must be an owned directory')
    return path, info


class InterruptCheckpoint:
    """Install a cooperative USR1 flag in the dedicated caller's main thread."""
    def __init__(self):
        self.requested = False
        self._previous = None
        self._installed = False
        self._archived = False
        self._attempted = False

    def _on_usr1(self, _signum, _frame):
        self.requested = True

    def __enter__(self):
        if self._installed:
            raise CheckpointError('handler already installed')
        self._previous = signal.signal(signal.SIGUSR1, self._on_usr1)
        self._installed = True
        return self

    def __exit__(self, _type, _value, _traceback):
        if self._installed:
            signal.signal(signal.SIGUSR1, self._previous)
            self._installed = False

    def checkpoint(self, open_unit, archive_root, job_id):
        """Archive an owned quiescent directory once, or return None if no USR1.

        archive_root is the existing results/_interrupted directory. Creates a
        fresh job-id directory exclusively and moves the unit into it on the
        same filesystem. On any failure preserve all partials and report STOP.
        """
        if not self._installed or self._attempted:
            raise CheckpointError('checkpoint handler absent or archive already attempted')
        if not self.requested:
            return None
        self._attempted = True
        if not isinstance(job_id, str) or not re.fullmatch(r'[0-9]+', job_id):
            raise CheckpointError('numeric Slurm job ID required')
        unit, unit_info = _existing_directory(open_unit)
        root, root_info = _existing_directory(archive_root)
        if unit_info.st_dev != root_info.st_dev:
            raise CheckpointError('unit and archive must share a filesystem')
        if os.path.commonpath((str(unit), str(root))) in (str(unit), str(root)):
            raise CheckpointError('unit and archive paths overlap')
        jobdir = root / job_id
        try:
            os.mkdir(jobdir, 0o700)
            target = jobdir / unit.name
            if os.path.lexists(target):
                raise CheckpointError('archive destination exists')
            current = unit.lstat()
            if (current.st_dev, current.st_ino) != (unit_info.st_dev, unit_info.st_ino):
                raise CheckpointError('unit identity changed')
            os.rename(unit, target)
        except OSError as exc:
            raise CheckpointError('archive failed; preserve partial state') from exc
        self._archived = True
        return {'job_id': job_id, 'original': str(unit), 'archive': str(target),
                'unit_dev': unit_info.st_dev, 'unit_ino': unit_info.st_ino}
