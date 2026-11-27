"""Exercise the CPU-set shell driver's counting without contacting a host."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


DRIVER = Path(__file__).resolve().parents[2] / "sweep2/t1_tasl/run_cpuset_check.sh"


def write_executable(path, source):
    path.write_text(source)
    path.chmod(0o755)


@pytest.mark.parametrize("infrastructure_retries", [0, 1, 4])
def test_driver_counts_sealed_attempts_and_keeps_retry_limit(tmp_path, infrastructure_retries):
    tracks = tmp_path / "tracks"
    locks = tmp_path / "locks"
    capture = tmp_path / "capture"
    bin_dir = tmp_path / "bin"
    locks.mkdir()
    bin_dir.mkdir()
    driver = tmp_path / DRIVER.name
    # Relocate the two hard-coded host directories to isolate the fake host.
    driver.write_text(DRIVER.read_text().replace(
        "/home/dowling/r1_tracks/t1_tasl", str(tracks),
    ).replace("/home/dowling/r1_locks", str(locks)))

    write_executable(bin_dir / "git", '#!/bin/bash\nif [ "$1" = rev-parse ]; then echo fixture; fi\nexit 0\n')
    write_executable(bin_dir / "flock", "#!/bin/bash\nexit 0\n")
    write_executable(bin_dir / "systemd-run", f"""#!{sys.executable}
import json
import os
from pathlib import Path

root, = (Path(os.environ["CPUSET_FIXTURE"]) / "runs").iterdir()
node = root / "mlgym_houseprice"
number = len(list(node.glob("attempt-*"))) + 1
attempt = node / f"attempt-{{number}}"
attempt.mkdir(parents=True)
retry = number <= int(os.environ["CPUSET_RETRIES"])
(attempt / "job_record.json").write_text(json.dumps({{"stop_class": "infrastructure" if retry else None}}))
raise SystemExit(int(retry))
""")
    write_executable(bin_dir / "python3", f"""#!{sys.executable}
import json
from pathlib import Path
import sys

args = sys.argv[1:]
if args[0] == "-c":
    sys.argv = args[1:]
    exec(sys.argv[0])
elif args[1] == "cpuset-spec":
    Path(args[args.index("--out") + 1]).write_text("{{}}")
elif args[1] == "seal":
    pass
elif args[1] == "cpuset-verdict":
    attempts = [Path(args[i + 1]).name for i, arg in enumerate(args) if arg == "--attempt"]
    passed = len(attempts) == 3
    print(json.dumps({{"attempts": attempts, "verdict": "PASS" if passed else "STOP"}}))
else:
    raise SystemExit(f"unexpected fixture command: {{args}}")
""")
    result = subprocess.run(
        ["/bin/bash", str(driver), str(capture)], cwd=tmp_path,
        env={**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
             "CPUSET_FIXTURE": str(tracks), "CPUSET_RETRIES": str(infrastructure_retries)},
        capture_output=True, text=True, check=False, timeout=15,
    )
    tries = min(infrastructure_retries + 3, 6)
    verdict_file, = capture.glob("G5_TASL2_CPUSET_CHECK_*.json")
    verdict = json.loads(verdict_file.read_text())
    status = (capture / "cpuset_driver.status").read_text()

    assert verdict["attempts"] == [f"attempt-{i}" for i in range(infrastructure_retries + 1, tries + 1)]
    assert result.returncode == (0 if tries - infrastructure_retries == 3 else 1), status
    assert f"try_{tries}_rc=0" in status
    assert f"try_{tries + 1}_rc=" not in status
