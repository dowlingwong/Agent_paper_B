"""Stand-in for the two harness symbols of the missing pin 6afdb0e (Track H); for comparing test runs only."""
from r1.harness import import_harness
import_harness()
import autoresearch.memory.summarizer as s
if not hasattr(s, "SKIP_DISPLAY_ONE_LINE"):
    s.SKIP_DISPLAY_ONE_LINE = "one_line/v1"
if not hasattr(s, "is_control_plane_skip"):
    def is_control_plane_skip(rec):
        extra = getattr(rec, "extra", None) or {}
        dec = getattr(getattr(rec, "decision", None), "value", None)
        c = extra.get("control") or {}
        return dec == "skipped" and bool(c) and c.get("reason") != "inactive_key"
    s.is_control_plane_skip = is_control_plane_skip
