# compute/20261127-37 — screening reruns: back off between attempts

Eight co-tenancy stops so far (0 failed rows; latest `SMEAS_EVIDENCE_20261127T2125Z`), each within a minute or two: deepthought's other users keep the load
high. Under R1-SCREEN-COTENANCY-INFRA keep rerunning, but **at most one attempt every 30 minutes**, and only when a preflight sample shows at least 12
cores free for others (two cores of headroom above the guard's 10). Overnight load is usually lower. Record each attempt in one line. If the run has not
completed by 08:00 CET, stop retrying and report; a change of the worker count is the author's (a note re-issue).
