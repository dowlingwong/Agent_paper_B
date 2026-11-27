# local/20261127-11 — P.4 direct launcher: a venv mode for Ada (compute's blocker)

Owner: local. Runbook §4 (P.4); PLAN R1-HOST-FREE (1), R1-P4-D3-GPU-PREFLIGHT (1). Decided by the coordinator (level 1, engineering:
it changes neither the evidence nor its reading; the environment is checked, not assumed).

Compute's report (`coord/compute` `1858b46f`, `compute/20261127-13`): under `zli538` on Ada there is no Apptainer and `docker info` is
denied, and the reviewed direct launcher accepts only apptainer/docker. Ada has the reviewed venv (on `main`; `uv pip freeze` equal to
the P.4 lock 121/121; Python 3.12.10 vs the lock's 3.12.15). Add a `venv` runtime to the direct launcher. It runs the same job script with
the venv's interpreter and refuses unless the live `uv pip freeze` equals the lock (the env3 freeze check, unchanged in substance). It
records interpreter path, Python version, freeze sha256, host, GPU model and driver in the job record, and states the Python patch-version
difference in the Ada host config. The container paths stay as they are. Tier E: tests, the full suite plus the torch files in a torch env,
review. Then compute fills `trackp_ada_v1.json` and runs the probe (`compute/20261127-13`).
