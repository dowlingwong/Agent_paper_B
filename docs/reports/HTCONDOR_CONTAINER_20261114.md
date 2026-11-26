# HTCondor adapter: container universe (14 November 2026)

**Status.** ENGINEERING_ONLY; nothing submitted. AI-assisted (Claude, Mac-local agent). The author's unit of 14 Nov
10:53 (after the cluster agent reported that the adapter rendered only `universe = docker`,
`HTCONDOR_CHAIN_20261114.md`). Branch `mac-htcondor-container-20261114` from `mac-htcondor-20261114` @ `46bee4c7`
(the adapter with the HTC-Q1/Q2 answers, accepted).

## 1. Manifest (`htc_job/v1`, extended)

| Key | Rule |
|---|---|
| `runtime` (optional) | `"docker"` (default; unchanged behaviour: `universe = docker`, `docker_image`) or `"container"` (`universe = container`) |
| `image` | runtime docker only (required there, refused with runtime container) |
| `container_image` | runtime container only (required there): `docker://<image reference>` (pulled by the execute node, never transferred) or an absolute path to a `*.sif` file |
| `container_transfer` (optional bool) | runtime container with a SIF only |

A SIF image is handled apart from the ordinary transfer inputs:

- **On a shared file system, local job:** a SIF under `/work/` or `/ceph/` for a local-placement job (which sees
  `/work`, `/home`, `/ceph`) is read in place and not transferred; the JDL says `transfer_container = false`.
- **Transferred (remote job, e.g. NEMO2):** only with `container_transfer: true` written in the manifest. The SIF must
  then exist here as a regular file (no symlink in the last path component), not be listed again in
  `transfer_input_files`, fit in `request_disk` (`disk_kb` × 1024 ≥ its size), and be at most
  `max_container_transfer_mb`, a cap of its own in
  `htc_config.json` (value 8000, status `proposed:` until the cluster agent's S5 measurement). HTCondor transfers it
  (no `transfer_container` line).
- **Refused:** a remote job with a SIF and no `container_transfer: true` (remote nodes do not see `/work` or
  `/ceph`); `container_transfer: true` on a local job; a SIF path outside `/work` or `/ceph` without transfer;
  `container_transfer` with a `docker://` image or with runtime docker; a relative path, a `..` part or a non-`.sif`
  name.
- **The 100 MB cap** (`max_transfer_input_mb`) still applies to the ordinary inputs (executable, `transfer_input_files`,
  resume directory); the SIF never counts toward it.

## 2. Transfer time

`htc_events.job_summary` and the queue-time rows gain `input_transfer_s`: the seconds between each event 040
"Started transferring input files" and the next "Finished transferring input files", summed over attempts (an
eviction and restart transfers again), empty when no complete pair was logged. Output transfer is not counted. A
transferred SIF is expected to fall inside the input-transfer window, so for the S5 job this column should give the image
transfer time; S5 has to confirm that on HTCondor 25.0. The queue-time row now has 14 columns, one more than the
cluster runbook §4.2 lists.
`htc_submit --dry-run` also prints `container={...}` (kind, transfer, bytes) for runtime container.

## 3. Reference test against the cluster agent's JDLs

`r1/tests/htcondor/data/s2/` holds byte copies of the four S2 job files the cluster agent wrote by hand (S2L local
CPU, S2N1 NEMO2 L40S, S2N2 NEMO2 H200, S2T TOpAS V100S; hashes in `SHA256SUMS`). For each, the matching manifest
renders a JDL **equivalent** to the reference: the same submit commands with the same values after normalising key
case and aliases (`RequestCPUs` = `request_cpus`), argument syntax (`S2L` = `"S2L"`) and the order of the
`requirements` clauses; the adapter adds only its `# manifest_sha256` comment. 4 of 4 equivalent.

**S4/S5:** no S4 or S5 job file existed in the cluster agent's tree when this was written, and no review record for
the S2 files was there either. S4/S5 are covered by cases written from the author's text (a local SIF on `/work`, a
transferred SIF on NEMO2, the separate cap). When the reviewed S2/S4/S5 files are committed, they replace the copies
and are added to the equivalence test.

## 4. Tests

`r1/tests/htcondor`: 91 passed (79 before; 12 new tests in `test_htc_container.py`, with more cases after review round 1), `/tmp/trackg_venv`.

## 5. For the author / cluster agent

- Conservative choices to confirm: `/home` is not treated as shared for a SIF (only `/work` and `/ceph`); transfer is
  refused for local jobs; a remote job with a SIF on `/ceph/srv` is refused (see below).
- The reference test covers only `docker://` images (the four S2 files); the SIF and `transfer_container` lines have no
  outside reference until the reviewed S4/S5 files exist. Accepting this unit does not review the S2 files themselves.

- `max_container_transfer_mb`: set from S5 (image size and measured `input_transfer_s`).
- Is a SIF under `/ceph/srv` readable by remote jobs with `etp_ceph: true` (`ProvidesEtpCeph`)? If so, those jobs
  could read it in place too; the adapter refuses it for now (remote ⇒ transfer).
- ETP-local Singularity versions are mixed (1.2.5/1.3.4 on many slots, cluster report S1); a SIF built with 1.5.x may
  need a version requirement. Not added here.
