"""Real-loop multi-step RL skeleton (design: ``paperC/docs/proposals/REALLOOP_RL_DESIGN_20261121.md``).

ENGINEERING_ONLY; CPU only; AI-assisted (Claude). Nothing here runs a worker or a node. The modules state the rules
any RL that learns from real-loop campaigns must obey, each behind an author decision of the design note, and say
what they do not close:

* ``reward``: run outcomes attributed with the worker-producible infrastructure class **not neutral** (RL-INFRA),
  host evidence restricted to faults the job cannot cause, every attempt charged, truncation counted;
* ``layout``: worker-root plans (``served``: no data on the worker's disk) and a scan that checks a built root; the
  guarantee is building the mount namespace from the plan, the scan is a check with stated limits;
* ``budget``: training rows served by the parent and counted there (bounds the data, not the compute: the measured
  timeout and a cgroup time limit do that), and the campaign budget owned by the controller;
* ``env`` and ``train``: a multi-step environment over an injected runner and a tiny CPU policy-gradient trainer
  that only accepts training-split instances — a mechanism check, not a proposed method (RL-ALGO).
"""
