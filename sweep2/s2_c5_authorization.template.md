# Authorization: sweep 2 (EVIDENCE) — unapproved template

The cluster operator fills the note after independent review under R1-SWEEP2-AUTH. The coordinating chat publishes it to main. Keep approval false until every prerequisite and both projections are established.

approved: false
label: EVIDENCE
run_id: <reviewed run ID>
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296
layout_request_walltime_s: 17469
layout_request_disk_kb: 42460970
layout_request_memory_mb: 32000
layout_chunks: 16
layout_gpu_hours: <reviewed projection up to 60>
layout_wall_hours: <reviewed projection up to 48>
P1: PASS — R1-SWEEP-HOST-HTC signed (author-sweephost-20261116)
P2: PASS — the reviewed launch code is main HEAD or a descendant with identical authority files
P3: PASS — this note
P4: PASS — R1-S2C3-ACCEPT, original S2-C3 NOT PASS retained and disclosed
P5: PASS — R1-SWEEP2-LAYOUT-H200 and R1-SWEEP2-RESOURCES with reviewed projections
P6: PASS — exact integration's S2-C5 switch reviewed, with launch-commit C3b required
P7: PASS — v1 image digest frozen above
b2_audits: none (this authorization carries no B.2 audits)
d8_lock: true
The note must be published before the launch commit is fixed. Repeat C3b at that exact commit and require 8/8 before submission.
