# Authorization: sweep 2 (EVIDENCE) — TEMPLATE, not valid until the author fills and commits it

# Committed by the author as docs/r1/authorizations/c3_sweep2_<date>.md. `approved: true` only after P1–P7.

approved: false
label: EVIDENCE
run_id: <author run id, e.g. s2sweep-20261117-a>
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296
layout_request_walltime_s: 17469
layout_request_disk_kb: 42460970
layout_request_memory_mb: 32000
layout_chunks: 16
layout_gpu_hours: <reviewed projection up to 60>
layout_wall_hours: <reviewed projection up to 48>
P1: PASS — R1-SWEEP-HOST-HTC signed (author-sweephost-20261116)
P2: PASS — main contains the reviewed S2-M2 integration
P3: PASS — this note
P4: PASS — L40S deployment check (S2-C3) reviewed
P5: PASS — timing pilot + R1-SWEEP2-LAYOUT accepted
P6: PASS — S2-C5 switch enabled for this run id only
P7: PASS — v1 image digest frozen above
b2_audits: none (this authorization carries no B.2 audits)
d8_lock: true
# Author: fill every field, set approved: true, commit as docs/r1/authorizations/c3_sweep2_<date>.md.
