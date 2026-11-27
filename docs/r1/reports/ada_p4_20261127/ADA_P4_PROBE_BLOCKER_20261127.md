# Ada P.4 probe preparation — host-runtime blocker (task `compute/20261127-13`)

**Result: BLOCKED before the host-config fill.** The reviewed direct launcher accepts only `apptainer` or `docker`
and runs the job in the digest-pinned image. On Ada under the approved account `zli538` (uid 1008), Apptainer is
absent and Docker's daemon socket is not accessible to this account. Filling `direct.container_runtime` with
either value would therefore be false; the host config, the probe and the phase-1 note cannot proceed until a
runtime or a reviewed venv launch path exists. No fill commit, no probe, no GPU job, no training was run.

- **Base:** `origin/main` `e153df24ee3435bbe0b2fa994297b15250550c30`
- **Branch:** `compute-preflight-blockers-20261127`
- **Venv record:** `compute-ada-p4-venv-20261127` @ `a1d0cf74`, review R2 `ACCEPTED` (`a2efbb40`); freeze 121/121
  equal to the lock; Python 3.12.10 (image lock 3.12.15); torch 2.6.0+cu124; CUDA smoke 0.53 s on an empty card.
- **Host at the check:** `ucrtasl`, `zli538`, 27 Nov 2026 03:06 UTC; driver 545.23.08; 8 × RTX 6000 Ada 48 GB;
  cards 0 and 2 empty (48,427 MiB free each); `/data1` 2.1 TB free.

## Evidence

```
$ ssh ada_server 'hostname; id'
ucrtasl
uid=1008(zli538) gid=1101(zli538) groups=1101(zli538),27(sudo),1202(explore),1205(wam4agent)

$ command -v apptainer singularity podman docker
(no apptainer, singularity or podman)
/usr/bin/docker

$ docker info
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock:
Get "http://%2Fvar%2Frun%2Fdocker.sock/v1.51/version": dial unix /var/run/docker.sock: connect: permission denied
```

The filling tool (`r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py --host-class ada_rtx6000`) forces
`direct.container_runtime` to one of `apptainer` or `docker`; `p4_direct.py` refuses any other value. The venv is a
valid Python environment but the reviewed launcher does not have a venv runtime mode: it always starts the
digest-pinned image through one of those two runtimes. The task's "Python 3.12.10 vs 3.12.15" difference is
recorded in the venv unit and would be stated in the probe record; it is not the blocker.

## What is needed (Level 2 host/engineering decision)

1. The host owner grants `zli538` access to the Docker socket (docker group), or installs Apptainer usable without
   `sudo`; then the fill can name the real runtime and the probe can start. **Recommended** if the owner agrees,
   because it uses the reviewed launcher unchanged.
2. Alternatively, the author approves a reviewed **venv launch path** (no container) for the Ada probe; that is a
   code/design change with its own review and is not made here.

No `sudo`, no group change, no Docker login and no other user's file was touched. The empty cards 0 and 2 are
available; no lease was taken.

**Decided alone:** to stop before writing a host config whose runtime value would be false; to keep the accepted
venv as evidence and not to work around the launcher; to leave the Ada cards untouched.

**Needs:** the coordinator/author decides between (1) and (2). Until then `compute/20261127-13` and the P.4 probe
(`compute/20261126-07`) remain blocked; the venv unit itself is accepted.
