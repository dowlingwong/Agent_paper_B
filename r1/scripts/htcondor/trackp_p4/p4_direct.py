#!/usr/bin/env python3
"""Track P P.4 phase 1, the direct launch path (R1-HOST-FREE): the host-side launcher of one staged job, run by the
compute agent over SSH on a host of a direct-launch class (``ada_rtx6000``: SSH alias ``experiment_zhixu``), beside
the HTCondor path and with the same job logic. ENGINEERING_ONLY; AI-assisted (Claude).

The stage is the canonical one (``p4_render_jdl.py ... --host-class <direct class>``, or ``--probe`` for a probe spec
whose ``host_class`` is a direct class): the same transferred inputs as an HTCondor job (``p4_lib.TRANSFER_INPUTS`` or
``PROBE_TRANSFER_INPUTS``), this file, ``STAGE_MANIFEST.json`` and one descriptor ``p4direct_<arm>.json`` per arm
(``trackp_p4_direct_job/1``: the run, arm, mode, host class and its GPU, the image digest, the entry script and the
host values of the class's filled host config: hostname, container runtime, work root, lock directory, shm size). The
stage is copied to the host unchanged. Then::

    python3 p4_direct.py launch --stage <stage dir on the host> --arm <arm> --gpu <index>

1. refuses to run as root; reads the descriptor (a preview descriptor is never launched) and verifies every staged
   file against ``STAGE_MANIFEST.json``; the host's ``hostname`` must be the descriptor's;
2. a P.4 job (mode ``job``) needs the switch's once-only marker ``P4_SUBMIT_STARTED_<arm>.json`` in the stage (written
   by ``p4_switch.py submit`` after the signed note's checks and the two keys; ``check`` never writes it), naming this
   arm and this stage manifest's sha256; a probe (mode ``probe``) was entered in the probe run's submission ledger when
   it was staged (``p4_render_jdl.stage_probe``);
3. takes our GPU lease: an exclusive, non-blocking ``flock`` on ``<lock_dir>/gpu<index>.lock`` (the same lock our
   other jobs on the host take); a held lock is a refusal (exit 75): two of our P.4 jobs never hold one lease, and the
   agent takes another card or waits. The container inherits the lease's descriptor (``pass_fds``), so a SIGKILLed
   launcher does not free the card while an apptainer container runs; a docker container (run by dockerd) carries the
   label ``r1.p4.gpu_uuid=<uuid>``, and a card with such a running container is refused (review M1);
4. the leased card (``nvidia-smi --id=<index>``) must be the class's GPU (name and compute capability) with at least
   ``min_free_mib`` MiB free (the host config's value; R1-CARD-SHARE (1): free memory decides, not an empty card, so
   the job shares a card with another user's process when it must; ``p4_direct.py cards`` lists free memory,
   processes and running P.4 containers so that the agent takes an empty card when one exists, and the class's SFT
   probe runs on an empty card). A refusal in steps 1-4 writes nothing: no job directory, and the stage stays
   launchable (review M2);
5. the stage launches once: ``P4_DIRECT_LAUNCHED_<arm>.json`` is created exclusively in the stage (a second launch
   from the same stage is refused; a repeat is a new stage); then a fresh job directory
   ``<work_root>/<run_id>/<arm>/<UTC stamp>-<pid>-<random>`` (never an existing one; every new level mode 0700) and
   the launcher record ``direct_launch.json`` (``trackp_p4_direct_launch/1``, status ``started``), so every launch
   from here leaves an attempt to seal. The card's other compute processes are recorded at the start and at the end
   (count and memory only, R1-CARD-SHARE (4)), and ``card_shared`` says whether there were any; speed on a shared
   card is descriptive only (R1-CARD-SHARE (2));
6. copies the staged inputs into the job directory (each checked against the manifest) and runs the entry script
   (``p4_job.sh`` or ``p4_probe.sh``, with the spec, the arm and the host class) in the digest-pinned image v2.2
   through ``apptainer`` or ``docker``, or on Ada through the reviewed host venv and the same entry script. Only the leased
   card visible (by UUID: ``--gpus device=<uuid>`` or ``--nv --nvccli`` with ``NVIDIA_VISIBLE_DEVICES``; the job's own
   identity step refuses anything but exactly one GPU of its class, and ``P4_LEASED_GPU_UUID`` binds it to this
   lease), as the calling non-root user, the job directory the working directory and ``HOME``;
7. no wall-clock limit (R1-NO-TIMEOUT): the container runs until it exits. A SIGTERM, SIGINT or SIGHUP to the
   launcher stops the container and is recorded (status ``interrupted``); the attempt is sealed as an infrastructure
   failure and repeated in a new stage and attempt directory, never resumed and never an outcome (R1-CARD-SHARE (3);
   likewise an OOM beside another process, ``p4_lib.seal``);
8. writes the final launcher record (host, hostname, user, runtime and its version, image digest, lease path, card
   index, UUID, name, driver, the other processes at start and end, start and end UTC, ``wall_clock_s`` = the lease
   span, exit code) and releases the lease. The GPU-hours of the attempt are ``wall_clock_s`` / 3600 (one card,
   R1-HOST-FREE (5)), or the job record's ``gpu_hours`` if larger (``p4_lib.seal``).

The outputs to copy back for ``p4_lib.py seal`` are ``out.tar``, ``job_record.json``, ``SHA256SUMS``, ``p4_run.log``
and ``direct_launch.json`` (printed at the end). Standard library only (Python 3.6+), so it runs with the host's own
``python3``; nothing here reads a credential or a label file.
"""
import argparse
import binascii
import errno
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time

DESCRIPTOR_SCHEMA = "trackp_p4_direct_job/1"
LAUNCH_SCHEMA = "trackp_p4_direct_launch/1"          # = p4_lib.DIRECT_LAUNCH_SCHEMA
LAUNCH_FILE = "direct_launch.json"                    # = p4_lib.DIRECT_LAUNCH_FILE
ENGINEERING_ONLY = "ENGINEERING_ONLY"
LEASED_GPU_ENV = "P4_LEASED_GPU_UUID"                 # = p4_lib.LEASED_GPU_ENV
RUNTIMES = ("apptainer", "docker", "venv")
MODES = {"job": "p4_job.sh", "probe": "p4_probe.sh"}
SPEC_FILES = {"job": "p4_spec.json", "probe": "p4_probe_spec.json"}
OUTPUTS = ("out.tar", "job_record.json", "SHA256SUMS", "p4_run.log", LAUNCH_FILE)
DIGEST = re.compile(r"^ghcr\.io/dowlingwong/r1-htc-gpu@sha256:[0-9a-f]{64}$")
SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")
LEASE_BUSY_EXIT = 75
REFUSED_EXIT = 2


class Refusal(Exception):
    """The launcher refuses (before or instead of running the container)."""


def _utc(t=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _run(argv):
    """A short host command (nvidia-smi, the runtime's --version); never a timeout that decides an outcome."""
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)


def _write_atomic(path, doc):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def load_descriptor(stage, arm):
    """The arm's descriptor, checked: schema, label, not a preview, a safe run id and arm, a known mode with its entry
    script and spec file, a digest-pinned image, an admitted runtime, absolute paths for the work root and lock dir."""
    if not SAFE.match(arm or ""):
        raise Refusal("STOP: unsafe arm name {!r}".format(arm))
    path = os.path.join(stage, "p4direct_{}.json".format(arm))
    try:
        with open(path) as fh:
            d = json.load(fh)
    except (OSError, ValueError) as exc:
        raise Refusal("STOP: cannot read the descriptor {}: {}".format(path, exc))
    if not isinstance(d, dict) or d.get("schema") != DESCRIPTOR_SCHEMA or d.get("label") != ENGINEERING_ONLY:
        raise Refusal("STOP: {} is not a {} ENGINEERING_ONLY descriptor".format(path, DESCRIPTOR_SCHEMA))
    if d.get("preview") is not False:
        raise Refusal("STOP: a preview stage is never launched")
    if d.get("arm") != arm or not SAFE.match(str(d.get("run_id"))) or d.get("run_id") in (".", ".."):
        raise Refusal("STOP: the descriptor's run id or arm is not this launch's")
    mode = d.get("mode")
    if mode not in MODES or d.get("entry") != MODES[mode] or d.get("spec_file") != SPEC_FILES[mode]:
        raise Refusal("STOP: the descriptor's mode/entry/spec file is not one of {}".format(MODES))
    if not DIGEST.match(str(d.get("image_digest"))):
        raise Refusal("STOP: the image must be pinned by digest (ghcr.io/dowlingwong/r1-htc-gpu@sha256:...)")
    host = d.get("host") or {}
    if host.get("container_runtime") not in RUNTIMES:
        raise Refusal("STOP: container runtime {!r} is not one of {}".format(host.get("container_runtime"), RUNTIMES))
    if host["container_runtime"] == "venv":
        venv = host.get("venv") or {}
        python = venv.get("python", "")
        if d.get("host_class") != "ada_rtx6000" or not isinstance(python, str) or not os.path.isabs(python) or \
                ".." in python.split("/") or not python.endswith("/bin/python") or venv.get("version") != "3.12.10":
            raise Refusal("STOP: the Ada venv needs its reviewed absolute Python 3.12.10 interpreter")
    for key in ("work_root", "lock_dir"):
        v = os.path.expanduser(str(host.get(key, "")))
        if not os.path.isabs(v) or ".." in v.split("/"):
            raise Refusal("STOP: host.{} must be an absolute path without '..', not {!r}".format(key, host.get(key)))
    if not re.match(r"^[1-9][0-9]*[mg]$", str(host.get("shm_size", ""))):
        raise Refusal("STOP: host.shm_size must be like 16g")
    if not re.match(r"^[1-9][0-9]*$", str(host.get("min_free_mib", ""))):
        raise Refusal("STOP: host.min_free_mib must be a positive integer (MiB the job needs free on its card)")
    if not isinstance(d.get("inputs"), list) or not d["inputs"] or d["entry"] not in d["inputs"] or \
            d["spec_file"] not in d["inputs"] or any(not SAFE.match(str(x)) for x in d["inputs"]):
        raise Refusal("STOP: the descriptor's inputs must list the entry script, the spec and the transferred files")
    return d


def verify_stage(stage, descriptor_name):
    """Every file the manifest lists has its sha256 (the descriptor and the inputs among them); returns the manifest's
    sha256 and its file map."""
    mpath = os.path.join(stage, "STAGE_MANIFEST.json")
    try:
        with open(mpath) as fh:
            manifest = json.load(fh)
    except (OSError, ValueError) as exc:
        raise Refusal("STOP: cannot read {}: {}".format(mpath, exc))
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict) or descriptor_name not in files or "p4_direct.py" not in files:
        raise Refusal("STOP: the stage manifest does not list the descriptor and p4_direct.py")
    if manifest.get("preview") is True:
        raise Refusal("STOP: a preview stage is never launched")
    for name, want in sorted(files.items()):
        p = os.path.join(stage, name)
        if not SAFE.match(name) or os.path.islink(p) or not os.path.isfile(p) or _sha(p) != want:
            raise Refusal("STOP: staged {} is missing or changed after staging".format(name))
    return _sha(mpath), files


def check_submit_marker(stage, arm, manifest_sha):
    """A P.4 job launches only from a stage the switch submitted: ``P4_SUBMIT_STARTED_<arm>.json`` names this arm and
    this stage manifest (``p4_switch.py submit``)."""
    path = os.path.join(stage, "P4_SUBMIT_STARTED_{}.json".format(arm))
    try:
        with open(path) as fh:
            marker = json.load(fh)
    except (OSError, ValueError):
        raise Refusal("STOP: no switch marker {}: a P.4 job is launched only after p4_switch.py submit (the signed "
                      "note's checks and both keys)".format(os.path.basename(path)))
    if not isinstance(marker, dict) or marker.get("arm") != arm or marker.get("launch_kind") != "direct" or \
            marker.get("stage_manifest_sha256") != manifest_sha:
        raise Refusal("STOP: the switch marker does not name this arm, a direct launch and this stage manifest")
    return _sha(path)


def take_lease(lock_path):
    """An exclusive non-blocking flock (``flock -n``); a held lock is a refusal. Returns the open file (the lease)."""
    d = os.path.dirname(lock_path)
    if d and not os.path.isdir(d):
        os.makedirs(d, mode=0o700)
    fh = open(lock_path, "a")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, OSError) as exc:
        fh.close()
        if isinstance(exc, BlockingIOError) or getattr(exc, "errno", None) in (errno.EAGAIN, errno.EACCES):
            raise Refusal("STOP: the GPU lease {} is held by another job: wait for a free card or lease another "
                          "(never shared)".format(lock_path))
        raise
    return fh


CARD_QUERY = "--query-gpu=index,uuid,name,compute_cap,driver_version,memory.total,memory.free"


def _card_row(parts):
    i, uuid, name, cap, driver, memory, free = parts
    try:
        free_mib = float(free.split()[0])
    except (ValueError, IndexError):
        free_mib = None
    return {"index": int(i), "uuid": uuid, "name": name, "compute_capability": cap, "driver": driver,
            "memory_total": memory, "memory_free_mib": free_mib}


def query_card(index, run=_run):
    res = run(["nvidia-smi", "--id={}".format(index), CARD_QUERY, "--format=csv,noheader"])
    if res.returncode != 0:
        raise Refusal("STOP: nvidia-smi --id={} failed: {}".format(index, (res.stderr or "").strip()[:200]))
    rows = [[x.strip() for x in ln.split(",")] for ln in res.stdout.splitlines() if ln.strip()]
    if len(rows) != 1 or len(rows[0]) != 7 or rows[0][0] != str(index) or not rows[0][1].startswith("GPU-"):
        raise Refusal("STOP: nvidia-smi --id={} did not list exactly that one card: {!r}".format(index, rows))
    return _card_row(rows[0])


def list_cards(run=_run):
    """Every card with its free memory and its other compute processes (count and memory): the compute agent takes
    an empty card when one exists and shares one with enough free memory when none does (R1-CARD-SHARE (1))."""
    res = run(["nvidia-smi", CARD_QUERY, "--format=csv,noheader"])
    if res.returncode != 0:
        raise Refusal("STOP: nvidia-smi failed: {}".format((res.stderr or "").strip()[:200]))
    cards = [_card_row([x.strip() for x in ln.split(",")]) for ln in res.stdout.splitlines()
             if ln.strip() and len(ln.split(",")) == 7]
    for c in cards:
        c["other_processes"] = card_processes(c["uuid"], run)
        try:
            c["running_p4_docker_containers"] = running_p4_containers(c["uuid"], run)
        except (Refusal, OSError) as exc:                 # no docker on the host, or not usable: said so
            c["running_p4_docker_containers"] = "unknown: {}".format(exc)
    return cards


DOCKER_LABEL = "r1.p4.gpu_uuid"                       # every P.4 docker container carries its leased card's UUID


def running_p4_containers(uuid=None, run=_run):
    """Review M1: the running docker containers of P.4 jobs (by their ``r1.p4.gpu_uuid`` label; only the card ``uuid``
    when given). A docker container outlives a SIGKILLed launcher (dockerd runs it), so ``launch`` refuses a card that
    still has one and ``cards`` lists them. A failing ``docker ps`` is a refusal for ``launch``."""
    flt = "label={}={}".format(DOCKER_LABEL, uuid) if uuid else "label={}".format(DOCKER_LABEL)
    res = run(["docker", "ps", "--filter", flt, "--format", "{{.Names}}"])
    if res.returncode != 0:
        raise Refusal("STOP: docker ps failed: {}".format((res.stderr or "").strip()[:200]))
    return [x.strip() for x in (res.stdout or "").splitlines() if x.strip()]


def card_processes(uuid, run=_run):
    """The compute processes on the card (count and memory only, R1-CARD-SHARE); a query failure is a refusal."""
    res = run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory", "--format=csv,noheader,nounits"])
    if res.returncode != 0:
        raise Refusal("STOP: nvidia-smi --query-compute-apps failed: {}".format((res.stderr or "").strip()[:200]))
    mem, count = 0.0, 0
    for ln in res.stdout.splitlines():
        parts = [x.strip() for x in ln.split(",")]
        if len(parts) >= 3 and parts[0] == uuid:
            count += 1
            try:
                mem += float(parts[2])
            except ValueError:
                pass
    return {"count": count, "memory_mib": mem}


def runtime_version(runtime, run=_run):
    try:
        res = run([runtime, "--version"])
    except OSError:
        raise Refusal("STOP: {} is not executable here".format(runtime)) from None
    version = (res.stdout or res.stderr or "").strip().splitlines()
    if res.returncode != 0 or not version:
        raise Refusal("STOP: {} --version failed: the configured runtime is not usable here".format(runtime))
    return version[0][:200]


def container_argv(desc, job_dir, uuid, uid, gid, name):
    """The container command: the entry script with the spec, arm and host class, in the digest-pinned image, only
    the leased card visible, as the calling user, cwd and HOME in the job directory."""
    host = desc["host"]
    image = desc["image_digest"]
    env = {"HOME": os.path.join(job_dir, "home"), "TMPDIR": os.path.join(job_dir, "tmp"),
           "CUDA_VISIBLE_DEVICES": uuid, "NVIDIA_VISIBLE_DEVICES": uuid, LEASED_GPU_ENV: uuid}
    args = ["/bin/bash", desc["entry"], desc["spec_file"], desc["arm"], desc["host_class"]]
    if host["container_runtime"] == "docker":
        argv = ["docker", "run", "--rm", "--name", name, "--label", "{}={}".format(DOCKER_LABEL, uuid),
                "--gpus", "device={}".format(uuid),
                "--user", "{}:{}".format(uid, gid), "--shm-size", host["shm_size"],
                "-v", "{0}:{0}".format(job_dir), "-w", job_dir, "--entrypoint", args[0]]
        for k in sorted(env):
            argv += ["-e", "{}={}".format(k, env[k])]
        return argv + [image] + args[1:], {}
    if host["container_runtime"] == "apptainer":
        argv = ["apptainer", "exec", "--nv", "--nvccli", "--containall", "--cleanenv", "--home", env["HOME"],
                "--bind", "{0}:{0}".format(job_dir), "--pwd", job_dir]
        for k in sorted(env):
            if k != "HOME":
                argv += ["--env", "{}={}".format(k, env[k])]
        return argv + ["docker://" + image] + args, {"NVIDIA_VISIBLE_DEVICES": uuid}
    if host["container_runtime"] == "venv":
        return args, {**env, "P4_VENV_PYTHON": host["venv"]["python"], "PYTHONNOUSERSITE": "1"}
    raise Refusal("STOP: container runtime {!r} is not one of {}".format(host["container_runtime"], RUNTIMES))


class Launch(object):
    """One launch (``launch``); the steps are methods so that the tests can drive them with fakes."""

    def __init__(self, stage, arm, gpu, run=_run, popen=subprocess.Popen, hostname=None, now=time.time,
                 environ=None):
        self.stage, self.arm, self.gpu_index = os.path.abspath(stage), arm, int(gpu)
        self.run, self.popen, self.now = run, popen, now
        self.hostname = hostname or socket.gethostname()
        self.environ = dict(os.environ if environ is None else environ)
        self.record, self.job_dir, self.proc, self.interrupted, self.lease = None, None, None, None, None
        self.container_name = None

    def _save(self):
        _write_atomic(os.path.join(self.job_dir, LAUNCH_FILE), self.record)

    def _finish(self, status, exit_code, refusal=None, t_end=None):
        t_end = self.now() if t_end is None else t_end
        r = self.record
        r["status"], r["exit_code"], r["refusal"] = status, exit_code, refusal
        r["ended_utc"] = _utc(t_end)
        start = r.get("_lease_t")
        r["wall_clock_s"] = round(t_end - start, 3) if start is not None else 0.0
        r["wall_clock_basis"] = "the GPU lease span (one card)" if start is not None else "no lease taken"
        r.pop("_lease_t", None)
        self._save()

    def _on_signal(self, signum, frame):
        self.interrupted = signum
        if self.proc is not None:
            if self.container_name and self.record["runtime"] == "docker":
                self.run(["docker", "kill", self.container_name])
            try:
                self.proc.terminate()
            except OSError:
                pass

    def prepare(self):
        """Checks that need no lease and leave nothing behind: user, descriptor, stage, host name, switch marker."""
        if os.geteuid() == 0:
            raise Refusal("STOP: the launcher runs as root")
        desc = load_descriptor(self.stage, self.arm)
        manifest_sha, files = verify_stage(self.stage, "p4direct_{}.json".format(self.arm))
        if self.hostname != desc["host"].get("hostname"):
            raise Refusal("STOP: this host is {!r}, the descriptor's class {} runs on {!r}".format(
                self.hostname, desc["host_class"], desc["host"].get("hostname")))
        marker_sha = check_submit_marker(self.stage, self.arm, manifest_sha) if desc["mode"] == "job" else None
        for name in desc["inputs"]:
            if name not in files:
                raise Refusal("STOP: the input {} is not in the stage manifest".format(name))
        if os.path.exists(self._launched_path()):
            raise Refusal("STOP: {} was already launched from this stage; a repeat is a new stage".format(self.arm))
        self.desc, self.files = desc, files
        self.manifest_sha, self.marker_sha = manifest_sha, marker_sha
        self.lock_path = os.path.join(os.path.expanduser(desc["host"]["lock_dir"]), "gpu{}.lock".format(self.gpu_index))

    def _launched_path(self):
        return os.path.join(self.stage, "P4_DIRECT_LAUNCHED_{}.json".format(self.arm))

    def acquire(self):
        """The lease and the card checks (review M2: before anything is written, so a refusal here leaves no job
        directory and does not use up the stage): our flock, the class's GPU, no P.4 container of ours still running on
        the card (review M1, docker), enough free memory, a usable runtime."""
        self.lease = take_lease(self.lock_path)
        self.lease_t = self.now()
        card = query_card(self.gpu_index, self.run)
        self.card = card
        if card["name"] != self.desc["gpu_name"] or card["compute_capability"] != self.desc["compute_capability"]:
            raise Refusal("STOP: card {} is {} ({}), not the class's {} ({})".format(
                self.gpu_index, card["name"], card["compute_capability"], self.desc["gpu_name"],
                self.desc["compute_capability"]))
        runtime = self.desc["host"]["container_runtime"]
        if runtime == "docker":
            running = running_p4_containers(card["uuid"], self.run)
            if running:
                raise Refusal("STOP: a P.4 container still runs on card {} ({}): its launcher was killed; wait for it "
                              "or stop it before leasing the card again".format(self.gpu_index, running))
        self.others_start = card_processes(card["uuid"], self.run)
        self.need = int(self.desc["host"]["min_free_mib"])
        if card["memory_free_mib"] is None or card["memory_free_mib"] < self.need:
            raise Refusal("STOP: card {} has {} MiB free, the job needs {} MiB (R1-CARD-SHARE (1): free memory, not "
                          "an empty card, decides); lease another card".format(self.gpu_index,
                                                                                 card["memory_free_mib"], self.need))
        if runtime == "venv":
            venv = self.desc["host"]["venv"]
            self.runtime_version = runtime_version(venv["python"], self.run)
            if self.runtime_version != "Python " + venv["version"]:
                raise Refusal("STOP: the Ada venv interpreter is not Python {}".format(venv["version"]))
        else:
            self.runtime_version = runtime_version(runtime, self.run)

    def _mkdir_private(self, path):
        """Create ``path`` and any missing parent below the work root, each with mode 0700 (review M9)."""
        root = os.path.expanduser(self.desc["host"]["work_root"])
        if not os.path.isdir(root):
            os.makedirs(root, mode=0o700)
            os.chmod(root, 0o700)
        rel = os.path.relpath(path, root).split(os.sep)
        cur = root
        for i, part in enumerate(rel):
            cur = os.path.join(cur, part)
            last = i == len(rel) - 1
            if last or not os.path.isdir(cur):
                os.mkdir(cur, 0o700)                    # the job directory itself is never an existing one
                os.chmod(cur, 0o700)                    # whatever the umask

    def claim(self):
        """Once the lease and the card are ours: the once-only launch marker in the stage, then a fresh job directory
        and the launcher record (status ``started``). From here on every outcome leaves an attempt to seal."""
        try:
            fd = os.open(self._launched_path(), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                raise Refusal("STOP: {} was already launched from this stage; a repeat is a new stage".format(self.arm))
            raise
        desc = self.desc
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(self.now()))
        name = "{}-{}-{}".format(stamp, os.getpid(), binascii.hexlify(os.urandom(3)).decode())
        self.job_dir = os.path.join(os.path.expanduser(desc["host"]["work_root"]), desc["run_id"], self.arm, name)
        self._mkdir_private(self.job_dir)
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps({"arm": self.arm, "job_dir": self.job_dir, "launched_utc": _utc(self.now())}) + "\n")
        self.record = {
            "schema": LAUNCH_SCHEMA, "label": ENGINEERING_ONLY, "run_id": desc["run_id"], "arm": self.arm,
            "mode": desc["mode"], "host_class": desc["host_class"], "expected_hostname": desc["host"]["hostname"],
            "ssh_alias": desc["host"].get("ssh_alias"), "hostname": self.hostname, "user": self.environ.get("USER"),
            "uid": os.getuid(), "runtime": desc["host"]["container_runtime"], "runtime_version": self.runtime_version,
            "image_digest": desc["image_digest"], "host_config": desc.get("host_config"),
            "lease": {"lock_path": self.lock_path, "gpu_index": self.gpu_index, "acquired_utc": _utc(self.lease_t)},
            "gpu": self.card, "other_processes_start": self.others_start, "other_processes_end": None,
            "card_shared": bool(self.others_start["count"]), "memory_needed_mib": self.need,
            "stage": {"dir": self.stage, "manifest_sha256": self.manifest_sha, "submit_marker_sha256": self.marker_sha},
            "job_dir": self.job_dir, "command": None, "started_utc": _utc(self.lease_t), "ended_utc": None,
            "wall_clock_s": None, "exit_code": None, "status": "started", "refusal": None,
            "timeout": "none (R1-NO-TIMEOUT)", "_lease_t": self.lease_t}
        if self.record["runtime"] == "venv":
            self.record["venv"] = desc["host"]["venv"]
            self.record["image_executed"] = False
        self._save()

    def copy_inputs(self):
        for name in self.desc["inputs"]:
            dst = os.path.join(self.job_dir, name)
            shutil.copy2(os.path.join(self.stage, name), dst)
            if _sha(dst) != self.files[name]:
                raise Refusal("STOP: the copied input {} is not the staged file".format(name))
        for sub in ("home", "tmp"):
            os.mkdir(os.path.join(self.job_dir, sub), 0o700)

    def execute(self):
        uuid = self.record["gpu"]["uuid"]
        self.container_name = re.sub(r"[^A-Za-z0-9_.-]", "-", "p4-{}-{}-{}".format(
            self.desc["run_id"], self.arm, os.path.basename(self.job_dir)))
        argv, extra_env = container_argv(self.desc, self.job_dir, uuid, os.getuid(), os.getgid(), self.container_name)
        self.record["command"] = argv
        self.record["status"] = "running"
        self._save()
        # The native job inherits only the host tool search path and the job's own settings.
        environ = ({"PATH": self.environ.get("PATH", os.defpath)} if self.record["runtime"] == "venv"
                   else self.environ)
        env = dict(environ, **extra_env)
        old = {s: signal.signal(s, self._on_signal) for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)}
        try:
            # review M1: the child inherits the lease's descriptor, so a SIGKILLed launcher does not free the card
            # while the container runs (apptainer runs in the child; a docker container is found by its label)
            self.proc = self.popen(argv, cwd=self.job_dir, env=env, pass_fds=(self.lease.fileno(),))
            rc = self.proc.wait()                       # no timeout: R1-NO-TIMEOUT
        finally:
            for s, h in old.items():
                signal.signal(s, h)
        return rc

    def main(self):
        try:
            self.prepare()
            self.acquire()
        except Refusal as exc:                          # nothing written: no job directory, the stage not used up
            busy = "is held by another job" in str(exc)
            if self.lease is not None:
                self.lease.close()
            return {"status": "refused", "refusal": str(exc), "job_dir": None,
                    "exit_code": LEASE_BUSY_EXIT if busy else REFUSED_EXIT, "wall_clock_s": 0.0, "outputs": []}
        try:
            try:
                self.claim()
                self.copy_inputs()
            except Refusal as exc:
                if self.record is None:
                    return {"status": "refused", "refusal": str(exc), "job_dir": None, "exit_code": REFUSED_EXIT,
                            "wall_clock_s": 0.0, "outputs": []}
                self._finish("refused", REFUSED_EXIT, str(exc))
                return self.summary()
            rc = self.execute()
            try:
                self.record["other_processes_end"] = card_processes(self.record["gpu"]["uuid"], self.run)
            except Refusal as exc:
                self.record["other_processes_end"] = {"error": str(exc)}
            if self.interrupted is not None:
                self._finish("interrupted", rc, "STOP: the launcher received signal {}; the container was stopped "
                                                "(a repeat is a new stage, never a resume)".format(self.interrupted))
            else:
                self._finish("finished", rc)
            return self.summary()
        except Exception as exc:  # noqa: BLE001 - the record says what happened; the lease is released below
            if self.record is None:
                raise
            self._finish("refused" if self.proc is None else "interrupted", REFUSED_EXIT,
                         "STOP: launcher failure {}: {}".format(type(exc).__name__, exc))
            return self.summary()
        finally:
            if self.lease is not None:
                self.lease.close()                      # releases the flock

    def summary(self):
        r = self.record
        return {"status": r["status"], "exit_code": r["exit_code"], "refusal": r["refusal"], "job_dir": self.job_dir,
                "wall_clock_s": r["wall_clock_s"],
                "outputs": [os.path.join(self.job_dir, n) for n in OUTPUTS
                            if os.path.exists(os.path.join(self.job_dir, n))]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")
    ln = sub.add_parser("launch", help="launch one staged job on this host under a GPU lease")
    ln.add_argument("--stage", required=True)
    ln.add_argument("--arm", required=True)
    ln.add_argument("--gpu", required=True, type=int, help="the card index to lease (nvidia-smi index)")
    sub.add_parser("cards", help="list the cards: free memory and other compute processes (read-only)")
    a = ap.parse_args(argv)
    if a.cmd == "cards":
        try:
            print(json.dumps(list_cards(), indent=1))
        except Refusal as exc:
            print(str(exc), file=sys.stderr)
            return REFUSED_EXIT
        return 0
    if a.cmd != "launch":
        ap.error("a subcommand is required: launch or cards")
    out = Launch(a.stage, a.arm, a.gpu).main()
    print(json.dumps(out, indent=1))
    rc = out.get("exit_code")
    return rc if isinstance(rc, int) and 0 <= rc < 256 else REFUSED_EXIT


if __name__ == "__main__":
    sys.exit(main())
