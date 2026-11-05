"""Shared helpers of the HoreKa 2 tools (``hk2_submit.py``, ``hk2_status.py``).

HoreKa runbook (``docs/r1/prompts/HOREKA_RUNBOOK_20261104.md`` rev 3, PLAN R1-HOREKA-RUNBOOK) §3 items 1-2.
Standard library only; runs under the HoreKa system Python 3.9 (no ``match``, no ``X | Y`` at runtime,
no ``zip(strict=)``, no ``datetime.fromisoformat`` of a ``Z`` suffix). AI-assisted (Claude, M10, 4 Nov 2026);
ENGINEERING_ONLY.

Open author items are never hard-coded silently: F, C, D (runbook §7 item 3), the budget numbers (§7 item 4),
T_max (§7 item 2) and the campaign start come from ``hk2_config.json``, where every value carries a ``status``
("ruled: <row>", "measured: <source>" or "proposed: <source>"). Each tool prints the keys still marked
proposed and records them with the config sha256.
"""
from __future__ import annotations

import csv
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEFAULT_CONFIG = HERE / "hk2_config.json"
DEFAULT_PLAN = REPO / "docs" / "r1" / "PLAN.md"
CANONICAL_RESULTS_ROOT = Path('/hfs2/data/project/hk-project-p0027888/ka_ir7683/r1/results')
CONFIG_SCHEMA = "hk2_config/v1"
STATUS_PREFIXES = ("ruled:", "measured:", "proposed:")

# Slurm job states (sacct/squeue long names).
OUTSTANDING_STATES = ("PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "SUSPENDED", "REQUEUED",
                      "RESIZING", "SIGNALING", "STAGE_OUT")
EXPECTED_END_STATES = ("COMPLETED", "DEADLINE")


class Hk2Error(RuntimeError):
    """A usage or configuration error (exit 2)."""


class AccountingPending(Hk2Error):
    """Accounting is not reconciled; pause and retry after the polling interval."""


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

def parse_iso(text: str) -> dt.datetime:
    """An ISO time with an explicit UTC offset (``Z`` accepted); naive times are refused."""
    raw = str(text).strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    value = dt.datetime.fromisoformat(raw)
    if value.tzinfo is None:
        raise Hk2Error(f"time {text!r} has no UTC offset; write e.g. 2026-11-20T20:00:00+01:00")
    return value


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slurm_local(value: dt.datetime) -> str:
    """``value`` as the host's local wall-clock time, the form ``--deadline`` expects (runbook §0.5)."""
    return value.astimezone().replace(tzinfo=None, microsecond=0).isoformat()


_TIME_RE = re.compile(r"^(?:(\d+)-)?(?:(\d+):)?(\d+)(?::(\d+))?$")


def parse_slurm_time(text: str) -> int:
    """Slurm time limit ("MM", "MM:SS", "HH:MM:SS", "D-HH", "D-HH:MM", "D-HH:MM:SS") in seconds.

    ``UNLIMITED``, ``INVALID`` and ``NOT_SET`` raise: the tools never plan with an unbounded limit.
    """
    raw = str(text).strip()
    if "-" in raw:
        days_s, rest = raw.split("-", 1)
        if not days_s.isdigit():
            raise Hk2Error(f"bad Slurm time {text!r}")
        parts = rest.split(":")
        if not all(p.isdigit() for p in parts) or not 1 <= len(parts) <= 3:
            raise Hk2Error(f"bad Slurm time {text!r}")
        h, m, s = (parts + ["0", "0"])[:3]
        return int(days_s) * 86400 + int(h) * 3600 + int(m) * 60 + int(s)
    parts = raw.split(":")
    if not all(p.isdigit() for p in parts) or not 1 <= len(parts) <= 3:
        raise Hk2Error(f"bad Slurm time {text!r}")
    if len(parts) == 1:
        return int(parts[0]) * 60
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def format_slurm_time(seconds: int) -> str:
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    return (f"{days}-" if days else "") + f"{h:02d}:{m:02d}:{s:02d}"


_MEM_RE = re.compile(r"^(\d+)([KMGT]?)B?$", re.IGNORECASE)
_MEM_UNIT_MB = {"K": 1.0 / 1024, "": 1.0, "M": 1.0, "G": 1024.0, "T": 1024.0 * 1024}


def parse_mem_mb(text: str) -> float:
    """Slurm ``--mem`` value in MB (Slurm's default unit is MB). ``0`` (all memory) is refused."""
    match = _MEM_RE.match(str(text).strip())
    if not match:
        raise Hk2Error(f"bad --mem value {text!r}")
    value = int(match.group(1)) * _MEM_UNIT_MB[match.group(2).upper()]
    if value <= 0:
        raise Hk2Error("--mem=0 (all memory of the node) is refused")
    return value


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REQUIRED_KEYS = ("real_submission_enabled", "account", "freeze_F", "cutoff_C", "copyback_D", "campaign_start", "budget_ceiling_gpu_h",
                 "budget_stop_gpu_h", "t_max_hours", "probed_shape", "max_outstanding", "dev_partitions",
                 "dev_max_time", "agent_partitions", "gpu_partition_prefix", "ruling_row_id", "results_root",
                 "stop_marker", "query_min_interval_s")


def load_config(path: Optional[Path] = None) -> Dict[str, object]:
    """Values, statuses and sha256 of the HoreKa tool config (every value must carry a status)."""
    target = Path(path) if path else DEFAULT_CONFIG
    data = target.read_bytes()
    payload = json.loads(data.decode("utf-8"))
    if payload.get("schema") != CONFIG_SCHEMA:
        raise Hk2Error(f"{target}: schema must be {CONFIG_SCHEMA}")
    values: Dict[str, object] = {}
    statuses: Dict[str, str] = {}
    for key in REQUIRED_KEYS:
        entry = payload.get(key)
        if not isinstance(entry, dict) or "value" not in entry or "status" not in entry:
            raise Hk2Error(f"{target}: key {key!r} must be {{'value': ..., 'status': ...}}")
        status = str(entry["status"])
        if not status.startswith(STATUS_PREFIXES):
            raise Hk2Error(f"{target}: status of {key!r} must start with one of {STATUS_PREFIXES}")
        values[key] = entry["value"]
        statuses[key] = status
    for key in ("freeze_F", "cutoff_C", "copyback_D", "campaign_start"):
        parse_iso(str(values[key]))
    if type(values["real_submission_enabled"]) is not bool:
        raise Hk2Error("real_submission_enabled must be a JSON boolean")
    for key in ("budget_ceiling_gpu_h", "budget_stop_gpu_h", "t_max_hours", "query_min_interval_s"):
        value = values[key]
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise Hk2Error(f"{key} must be a positive finite JSON number")
    if values["query_min_interval_s"] < 60:
        raise Hk2Error("query_min_interval_s must be at least 60 seconds")
    if type(values["max_outstanding"]) is not int or not 1 <= values["max_outstanding"] <= 90:
        raise Hk2Error("max_outstanding must be an integer between 1 and 90")
    shape = values["probed_shape"]
    if not isinstance(shape, dict) or any(type(shape.get(k)) is not int for k in ("gpus", "cpus_per_task", "mem_mb")):
        raise Hk2Error("probed_shape must contain integer resources")
    if not (1 <= shape["gpus"] <= 1 and 1 <= shape["cpus_per_task"] <= 32 and 1 <= shape["mem_mb"] <= 184320):
        raise Hk2Error("probed_shape exceeds the currently probed shape")
    if parse_slurm_time(str(values["dev_max_time"])) <= 0:
        raise Hk2Error("dev_max_time must be positive")
    if expand_path(str(values["results_root"])).resolve() != CANONICAL_RESULTS_ROOT.resolve():
        raise Hk2Error("results_root differs from the canonical shared project state root")
    if not parse_iso(str(values["freeze_F"])) <= parse_iso(str(values["cutoff_C"])) <= parse_iso(str(values["copyback_D"])):
        raise Hk2Error("freeze_F, cutoff_C and copyback_D must be in order")
    if float(values["budget_stop_gpu_h"]) > float(values["budget_ceiling_gpu_h"]):  # type: ignore[arg-type]
        raise Hk2Error("budget_stop_gpu_h must not exceed budget_ceiling_gpu_h")
    return {"values": values, "statuses": statuses, "path": str(target),
            "sha256": hashlib.sha256(data).hexdigest(),
            "proposed": sorted(k for k, s in statuses.items() if s.startswith("proposed:"))}


def expand_path(text: str) -> Path:
    """Expand ``$VAR`` and ``~``; an unexpanded variable is an error, never a literal ``$PROJECT`` folder."""
    expanded = os.path.expanduser(os.path.expandvars(str(text)))
    if "$" in expanded:
        raise Hk2Error(f"path {text!r} has an unset variable ({expanded!r})")
    return Path(expanded)


# ---------------------------------------------------------------------------
# PLAN §10 ruling check
# ---------------------------------------------------------------------------

def plan_has_row(plan_path: Path, row_id: str) -> Tuple[bool, str]:
    """Require one exact decision in a real author table under dated §10."""
    try:
        lines = Path(plan_path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return False, f"PLAN not readable at {plan_path}: {exc}"
    in_section = False
    seen_section = False
    dated = False
    found = []
    fence = None
    comment = False
    html = None
    header = None
    table = False
    for raw in lines:
        if html is not None:
            if re.search(r'</' + re.escape(html) + r'\s*>', raw, re.I):
                html = None
            header, table = None, False
            continue
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', raw)
        if fence is not None:
            if re.match(r'^ {0,3}' + re.escape(fence[0]) + r'{' + str(len(fence)) + r',}\s*$', raw):
                fence = None
            header, table = None, False
            continue
        if marker:
            fence = marker.group(1)
            header, table = None, False
            continue
        # HTML comments, including multi-line comments, cannot supply decisions.
        line, rest = '', raw
        while rest:
            if comment:
                pos = rest.find('-->')
                if pos < 0:
                    rest = ''
                    break
                rest, comment = rest[pos + 3:], False
            else:
                pos = rest.find('<!--')
                if pos < 0:
                    line += rest
                    break
                line += rest[:pos]
                rest, comment = rest[pos + 4:], True
        if not line.strip() or line.expandtabs(4).startswith('    '):
            header, table = None, False
            continue
        tag = re.match(r'^ {0,3}<([A-Za-z][\w-]*)\b[^>]*>', line)
        if tag:
            if not re.search(r'</' + re.escape(tag.group(1)) + r'\s*>', line, re.I):
                html = tag.group(1)
            header, table = None, False
            continue
        if line.startswith("## "):
            in_section = bool(re.match(r"^## 10\.(\s|$)", line))
            seen_section = seen_section or in_section
            dated = False
            header, table = None, False
            continue
        if in_section and line.startswith("### "):
            match = re.match(r'^###\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b', line)
            try:
                if match is None:
                    raise ValueError('not a date')
                dt.datetime.strptime(match.group(1), '%d %B %Y')
                dated = True
            except ValueError:
                dated = False
            header, table = None, False
            continue
        if line.startswith('#'):
            dated = False
            header, table = None, False
            continue
        if not in_section or not dated or not line.lstrip().startswith('|') or r'\|' in line:
            header, table = None, False
            continue
        parts = line.strip().split('|')
        cells = parts[1:-1] if parts[-1] == '' else parts[1:]
        sep = len(cells) >= 2 and all(re.fullmatch(r'\s*:?-{3,}:?\s*', cell) for cell in cells)
        if sep:
            table = bool(header and len(header) == len(cells) and re.search(r'\bauthor\b', header[1], re.I))
            header = None
            continue
        if not table:
            header = cells if len(cells) >= 2 else None
            continue
        if len(cells) >= 2 and cells[0].strip() == row_id:
            found.append(cells[1].strip())
    if not seen_section:
        return False, f"PLAN at {plan_path} has no '## 10.' section"
    if len(found) == 1 and found[0] and found[0] not in ('-', '—'):
        return True, f"PLAN §10 row {row_id!r} at {plan_path}"
    return False, f"PLAN §10 at {plan_path} has no unique nonempty dated row {row_id}"


# ---------------------------------------------------------------------------
# Slurm queries (only ``squeue -u $USER`` and ``sacct -u $USER``)
# ---------------------------------------------------------------------------

Runner = Callable[[Sequence[str]], "subprocess.CompletedProcess[str]"]


def default_runner(argv: Sequence[str]) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(list(argv), capture_output=True, text=True, timeout=120)


def current_user() -> str:
    user = os.environ.get("USER") or os.environ.get("LOGNAME")
    if not user:
        raise Hk2Error("USER is not set; the tools query only the user's own jobs")
    return user


def gpus_from_tres(text: str) -> int:
    """GPU count from a TRES/GRES string: ``gres/gpu=1``, ``gres/gpu:h100=2``, ``gres:gpu:1``, ``gpu:4``."""
    generic = []
    typed = []
    for item in str(text or "").split(","):
        item = item.strip()
        if "gpu" not in item.lower():
            continue
        head = item.split("(", 1)[0]
        match = re.search(r"[:=](\d+)$", head)
        if not match:
            raise Hk2Error(f"cannot determine GPU allocation from {item!r}")
        count = int(match.group(1))
        if re.match(r"^(?:gres/)?gpu(?:=|:)(?:\d+)$", head):
            generic.append(count)
        else:
            typed.append(count)
    if len(generic) > 1:
        raise Hk2Error(f"ambiguous GPU totals in {text!r}")
    if generic and typed and sum(typed) > generic[0]:
        raise Hk2Error(f"GPU totals disagree in {text!r}")
    return generic[0] if generic else sum(typed)


class QueryLock:
    """Cross-process lock covering query, guard and submission/ledger write."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.file = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+")
        fcntl.flock(self.file.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *args):
        fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
        self.file.close()


def query_snapshot(config, runner=default_runner):
    """Query once under QueryLock; require at least 60 s since the preceding query."""
    directory = records_dir(config)
    interval = max(60, float(config["values"]["query_min_interval_s"]))
    throttle = QueryThrottle(directory / "query_state.json", interval)
    delay = throttle.wait_needed()
    if delay > 0:
        raise Hk2Error(f"query throttled; retry after {delay:.1f} seconds")
    # Mark before either call, including failed calls, so errors cannot cause rapid polling.
    throttle.mark()
    user = current_user()
    live = squeue_jobs(runner, user)
    # Preserve observations even when the subsequent sacct call fails. A job
    # must not disappear during accounting delay without leaving a WAIT gate.
    record_observed_jobs(config, live)
    accounted = sacct_jobs(runner, user, parse_iso(str(config["values"]["campaign_start"])))
    return live, accounted


SQUEUE_FORMAT = "%i|%P|%T|%l|%b|%q|%j"


def squeue_jobs(runner: Runner, user: str) -> List[Dict[str, object]]:
    """The user's outstanding jobs (``squeue -u USER``). Any failure raises: guards fail closed."""
    proc = runner(["squeue", "-u", user, "-h", "-o", SQUEUE_FORMAT])
    if proc.returncode != 0:
        raise Hk2Error(f"squeue failed (rc {proc.returncode}): {proc.stderr.strip()[:300]}")
    jobs = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 7:
            raise Hk2Error(f"unexpected squeue line {line!r}")
        jid, part, state, limit, tres, qos, name = (p.strip() for p in parts)
        if "[" in jid or "," in part or not jid.isdigit():
            raise Hk2Error(f"cannot account for aggregate/ambiguous squeue entry {line!r}")
        gpu_count = gpus_from_tres(tres)
        if (part.startswith("gpu-") or part.startswith("dev-gpu")) and not gpu_count:
            raise Hk2Error(f"GPU request missing from squeue entry {line!r}")
        jobs.append({"job_id": jid, "partition": part, "state": state, "time_limit_s": parse_slurm_time(limit),
                     "gpus": gpu_count, "qos": qos, "name": name})
    return jobs


SACCT_FIELDS = "JobID,JobName,Partition,State,ElapsedRaw,AllocTRES,Start,End,TimelimitRaw"


def sacct_jobs(runner: Runner, user: str, since: dt.datetime) -> List[Dict[str, object]]:
    """The user's jobs since ``since`` (``sacct -X -u USER``), allocation lines only."""
    start = since.astimezone().replace(tzinfo=None, microsecond=0).isoformat()
    proc = runner(["sacct", "-X", "-u", user, "-S", start, "-n", "-P", "-o", SACCT_FIELDS])
    if proc.returncode != 0:
        raise Hk2Error(f"sacct failed (rc {proc.returncode}): {proc.stderr.strip()[:300]}")
    jobs = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 9:
            raise Hk2Error(f"unexpected sacct line {line!r}")
        jid, name, part, state, elapsed, tres, start_s, end_s, limit = (p.strip() for p in parts)
        if not re.fullmatch(r"\d+(?:_\d+)?", jid) or not elapsed.isdigit():
            raise Hk2Error(f"ambiguous accounting entry {line!r}")
        gpu_count = gpus_from_tres(tres)
        if int(elapsed) and (part.startswith("gpu-") or part.startswith("dev-gpu")) and not gpu_count:
            raise Hk2Error(f"GPU allocation missing from accounting entry {line!r}")
        jobs.append({"job_id": jid, "name": name, "partition": part, "state": state.split()[0] if state else "",
                     "elapsed_s": int(elapsed), "gpus": gpu_count,
                     "start": start_s, "end": end_s,
                     "time_limit_s": int(limit) * 60 if limit.isdigit() else None})
    return jobs


def gpu_hours(seconds: float, gpus: int) -> float:
    return float(seconds) * int(gpus) / 3600.0


class QueryThrottle:
    """At most one ``squeue``/``sacct`` round per ``min_interval`` seconds, shared by both tools.

    HoreKa kills jobs of users who poll ``squeue`` faster than every 30 s (runbook §0.1 sources). The state is a
    small JSON file next to the ledger.
    """

    def __init__(self, path: Path, min_interval: float, clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self.path = Path(path)
        self.min_interval = float(min_interval)
        self.clock = clock
        self.sleep = sleep

    def last(self) -> Optional[float]:
        try:
            raw = self.path.read_text()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise Hk2Error(f"query throttle state is unreadable: {exc}")
        try:
            timestamp = float(json.loads(raw)["last_query_epoch"])
        except (ValueError, KeyError, TypeError) as exc:
            raise Hk2Error(f"query throttle state is invalid: {exc}")
        if not (0 <= timestamp < float("inf")):
            raise Hk2Error("query throttle timestamp is invalid")
        return timestamp

    def wait_needed(self) -> float:
        last = self.last()
        if last is None:
            return 0.0
        return max(0.0, self.min_interval - (self.clock() - last))

    def mark(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"last_query_epoch": self.clock()}))
        os.replace(str(tmp), str(self.path))


# ---------------------------------------------------------------------------
# GPU-hour ledger (runbook §0.4)
# ---------------------------------------------------------------------------

LEDGER_FIELDS = ("job_id", "name", "phase", "partition", "gpus", "elapsed_s", "allocation_gpu_h", "end_state",
                 "expected_end", "resubmit")


def read_ledger(path: Path) -> Dict[str, Dict[str, str]]:
    if not Path(path).exists():
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        return {row["job_id"]: row for row in csv.DictReader(fh)}


def write_ledger(path: Path, rows: Dict[str, Dict[str, str]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")

    def key(jid: str):
        head = jid.split("_", 1)[0]
        return (int(head) if head.isdigit() else 0, jid)

    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(LEDGER_FIELDS))
        writer.writeheader()
        for jid in sorted(rows, key=key):
            writer.writerow({k: rows[jid].get(k, "") for k in LEDGER_FIELDS})
    os.replace(str(tmp), str(path))


def submission_phases(records_dir: Path) -> Dict[str, str]:
    """job id -> phase, from the submit tool's records (``submissions.jsonl``)."""
    out: Dict[str, str] = {}
    path = Path(records_dir) / "submissions.jsonl"
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError as exc:
            raise Hk2Error(f"corrupt submission record at {path}: {exc}")
        if not isinstance(rec, dict):
            raise Hk2Error(f"invalid submission record at {path}")
        if rec.get("job_id"):
            out[str(rec["job_id"])] = str(rec.get("phase", ""))
    return out


def record_deadline_jobs(config, accounted):
    """Remember observed DEADLINE ids, including old ledger entries, under query.lock."""
    directory = records_dir(config)
    path = directory / 'deadline_jobs.json'
    try:
        previous = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(previous, list) or any(not isinstance(j, str) or not j.isdigit() for j in previous):
            raise ValueError('invalid deadline job list')
        seen = set(previous)
    except FileNotFoundError:
        seen = set()
    except (OSError, ValueError, TypeError) as exc:
        raise Hk2Error('cannot read deadline history: ' + str(exc)) from exc
    ledger = expand_path(str(config['values']['results_root'])) / 'engineering' / 'gpu_ledger.csv'
    for jid, row in read_ledger(ledger).items():
        if row.get('end_state') == 'DEADLINE' or row.get('resubmit') == 'never':
            if not jid.isdigit():
                raise Hk2Error('ambiguous deadline job id in ledger')
            seen.add(jid)
    for row in accounted:
        if (str(row.get('state', '')).split() or [''])[0].rstrip('+') == 'DEADLINE':
            jid = str(row.get('job_id', ''))
            if not jid.isdigit():
                raise Hk2Error('ambiguous deadline job id in accounting')
            seen.add(jid)
    if seen:
        directory.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.tmp')
        with tmp.open('w', encoding='utf-8') as fh:
            json.dump(sorted(seen), fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp), str(path))
        fd = os.open(str(directory), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    return seen


def refuse_deadline_resubmission(config, manifest_sha, accounted):
    """Refuse the exact manifest bytes of any project submission observed DEADLINE.

    Changed bytes, semantic equivalence and jobs submitted outside this tool
    cannot be inferred; the project-wide submission process remains necessary.
    """
    if not isinstance(manifest_sha, str) or not re.fullmatch(r'[0-9a-f]{64}', manifest_sha):
        raise Hk2Error('manifest digest missing or invalid')
    deadlines = record_deadline_jobs(config, accounted)
    path = records_dir(config) / 'submissions.jsonl'
    if not path.exists():
        return
    mappings = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            raise Hk2Error('corrupt submission record: ' + str(exc)) from exc
        if not isinstance(row, dict):
            raise Hk2Error('invalid submission record')
        jid = row.get('job_id')
        if not jid:
            continue
        digest = row.get('manifest_sha256')
        if not str(jid).isdigit() or not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise Hk2Error('submission record lacks a valid job id or manifest digest')
        jid = str(jid)
        if jid in mappings and mappings[jid] != digest:
            raise Hk2Error('conflicting manifest digests for submission job id')
        mappings[jid] = digest
    if any(mappings.get(jid) == manifest_sha for jid in deadlines):
        raise Hk2Error('DEADLINE job must not be resubmitted with the same manifest')


def budget_state(outstanding: List[Dict[str, object]], accounted: List[Dict[str, object]]) -> Dict[str, float]:
    """Use the runbook's conservative used plus full outstanding reservation."""
    used = sum(gpu_hours(float(j["elapsed_s"]), int(j["gpus"])) for j in accounted)  # type: ignore[arg-type]
    reserved = sum(gpu_hours(float(j["time_limit_s"]), int(j["gpus"])) for j in outstanding)  # type: ignore[arg-type]
    return {"used_gpu_h": used, "reserved_gpu_h": reserved}


def record_observed_jobs(config, outstanding):
    """Persist every user job seen by either the status or submit tool."""

    directory = records_dir(config)
    path = directory / "observed_jobs.json"
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(stored, list) or any(not isinstance(x, str) or not x.isdigit() for x in stored):
            raise ValueError("invalid observed jobs")
        seen = set(stored)
    except FileNotFoundError:
        seen = set()
    except (OSError, ValueError, TypeError) as exc:
        raise Hk2Error("cannot read observed job ledger: " + str(exc)) from exc
    live = {str(j["job_id"]) for j in outstanding}
    seen.update(live)
    seen.update(submission_phases(directory))
    if any(not jid.isdigit() for jid in seen):
        raise Hk2Error("cannot record ambiguous observed job id")
    directory.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(sorted(seen), fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(str(tmp), str(path))
    dirfd = os.open(str(directory), os.O_RDONLY)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)
    return seen


def require_submission_accounted(config, outstanding, accounted):
    """Pause if an observed user job vanished without terminal accounting."""
    seen = record_observed_jobs(config, outstanding)
    live = {str(j["job_id"]) for j in outstanding}
    terminal = {"BOOT_FAIL", "CANCELLED", "COMPLETED", "DEADLINE", "FAILED", "NODE_FAIL",
                "OUT_OF_MEMORY", "PREEMPTED", "TIMEOUT", "REVOKED", "SPECIAL_EXIT"}
    finished = {str(j["job_id"]) for j in accounted
                if (str(j.get("state", "")).split() or [""])[0].rstrip("+") in terminal}
    missing = seen - live - finished
    if missing:
        raise AccountingPending("waiting for terminal accounting of observed jobs: " + ", ".join(sorted(missing)))


def records_dir(config: Dict[str, object]) -> Path:
    """Where submission records, generated scripts, the throttle state and the ledger live (engineering side)."""
    return expand_path(str(config["values"]["results_root"])) / "engineering" / "hk2_jobs"  # type: ignore[index]
