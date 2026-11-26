"""Protect the pinned worker's per-trial patch and log from overwrite."""
from pathlib import Path


class B1WorkerArtifactStop(SystemExit):
    """Escape the harness's ordinary-exception handler without rewriting evidence."""


class GuardedTrialPath(type(Path())):
    """Exclusively create worker outputs; retain partial writes on failure."""

    def write_text(self, data, encoding=None, errors=None, newline=None):
        try:
            with self.open(mode='x', encoding=encoding, errors=errors, newline=newline) as stream:
                return stream.write(data)
        except Exception as exc:
            raise B1WorkerArtifactStop(
                f'STOP: B1 worker artifact write failed or already exists: {self}'
            ) from exc
