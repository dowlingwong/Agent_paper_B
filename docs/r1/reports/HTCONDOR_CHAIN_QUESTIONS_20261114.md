# Questions — HTCondor submission chain, 14 Nov 2026 (Apptainer route)

Each item: context, options, recommendation, paste-ready answer. Nothing here blocks the steps that do not depend on it; the author said to record and carry on.

## Q-A1 (BLOCKING for S2/S4/S5) — the reviewed adapter has no container universe

**Context.** The author's instruction says to generate the S2/S4/S5 job files with the Mac agent's reviewed adapter (`mac-htcondor-20261114`). That adapter renders `universe = docker` / `docker_image = <image>` unconditionally (`r1/scripts/htcondor/htc_submit.py` L254) and validates a docker image reference; it has no `universe = container`, no `container_image`, and no SIF-transfer path. The S2/S4/S5 designs need exactly those (Apptainer via Singularity; NEMO2 has no Docker).
**Options.** (a) The Mac agent extends the adapter with an explicit container mode — recommended shape: a new manifest key `runtime: "container"` (or `image_kind`), rendering `universe = container` and `container_image = <image>` instead of docker; for a SIF path (`/work/.../*.sif`) on a remote job, the SIF is listed as a transferred input and counted against `max_transfer_input_mb` (or a documented exception), with a `container_image` that HTCondor can transfer; guards otherwise unchanged. New review round on the adapter. (b) The cluster agent hand-writes the S2/S4/S5 JDLs and they go through the same independent-review gate before each real submission (same discipline, different author). (c) Keep docker universe and drop NEMO2 (contradicts S2/S5).
**Recommendation.** (a) if the Mac agent can do it quickly (it is a small renderer + guard change); otherwise (b) — the review gate is what matters, not who typed the JDL.
**Paste-ready answer:** `Q-A1：<a 由 Mac agent 加 container 模式 | b 由 cluster agent 手写 JDL 并走同一评审>。`

## Q-D1 (recorded, no action needed) — the deepthought Docker daemon is not running

**Context.** Read-only check 14 Nov 10:51 CET: `/var/run/docker.sock` absent, `DOCKER_HOST` unset, context `default` at the unix socket, `systemctl is-active docker` = **inactive**, `docker info` cannot connect. The account is in group `docker` (last night's failure was the daemon, not permissions). Per the author's supplement the daemon was not started by me; S3 proceeds on the `apptainer build` def route.
**Option.** The author asks the admin (Kylian) to start/enable the daemon if the Docker→`docker-daemon://` SIF route is ever wanted; not needed for today's S1–S6.
**Recommendation:** record only.
**Paste-ready answer:** `Q-D1 已知，S3 走 apptainer def；docker daemon 由作者找 Kylian。`

## Q-S4 (compatibility risk for S4) — mixed Singularity versions on the ETP local fleet

**Context.** S1 measured `SingularityVersion` on the ETP-local slots as mixed: 88× apptainer 1.2.5, 42× 1.3.4, and 1.5.x elsewhere (NEMO2 all 1.5.4, TOpAS 1.5.5). A SIF built by apptainer 1.5.5-1.el8 (the login node) should run on 1.5.x, but 1.2.5/1.3.4 compatibility is not guaranteed; S4 will find out when the local-CPU job runs.
**Options.** (a) accept the fleet as-is and record which node ran; (b) pin S4 to a node class with 1.5.x; (c) build the SIF with a lower `--apptainer-version` if needed.
**Recommendation:** (a) first, with the node's SingularityVersion recorded in the I1 output; escalate only if the SIF fails on 1.2.5/1.3.4.
**Paste-ready answer:** `Q-S4：<a 先接受并记录 | b 限定 1.5.x 节点 | c 降版本重建>。`
