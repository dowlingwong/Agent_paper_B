# compute/20261127-19 — Ada P.4 probe: the host config is on main; run the probe

`trackp_ada_v1.json` and its review are on `main` `91cfd48a`. Run the synthetic-label P.4 probe on one empty RTX 6000 Ada card through the
direct launcher's venv runtime, under R1-P4-TESTPLAN-DECISIONS and R1-P4-D3-GPU-PREFLIGHT (1). Record each base's peak GPU memory and timing,
the host configuration hash, the freeze check, the other compute processes on the card at start and end, and the probe charge against phase
1's 40 GPU-h (a reporting threshold). No SFT and no evidence training. Commit the outputs on a branch and get a fresh review. Report what the
phase-1 note needs from them.
