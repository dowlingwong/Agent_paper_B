"""Real-loop multi-step RL skeleton (design: ``paperC/docs/proposals/REALLOOP_RL_DESIGN_20261121.md``).

ENGINEERING_ONLY; CPU only; AI-assisted (Claude). Nothing here runs a worker or a node. The modules fix the three
rules any RL that learns from real-loop campaigns must obey, each behind an author decision of the design note:

* ``reward``: the run outcome classes of the isolated harness mapped to rewards, with the worker-produced
  infrastructure class **not neutral** (RL-INFRA) and truncation accounted per arm;
* ``layout``: the worker root holds the training split only (plus unlabelled evaluation inputs under RL-LAYOUT A);
  a scan refuses any parent-only file, renamed or not;
* ``budget``: training examples served by the parent and counted there, so an edited worker cannot train on more
  data than the fixed budget (RL-BUDGET), and the campaign budget owned by the controller;
* ``env`` and ``train``: a multi-step environment over an injected runner and a tiny CPU policy-gradient trainer
  that only accepts training-split instances — a mechanism check, not a proposed method (RL-ALGO).
"""
