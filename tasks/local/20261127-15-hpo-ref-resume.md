# local/20261127-15 — HPO reference: G1 and G6 are on main; resume item 3

The G1 adapter and the G6 audit are on `main` `91cfd48a` (both ACCEPTED). Resume `local/20261126-05` item 3 from
`mac-d3-hpo-ref-20261127` @ `666320c9`: wire the production runner to G1's rendered-file start/config hash contract and G6's terminal
audit; pin SMAC3 by installed distribution metadata; use a fresh output directory per attempt. Re-check on the real backend with synthetic
inputs (tier E). Its SMAC3 version then fills revision 4's TODO. Run tests that touch the D.3 harness with `AR_HARNESS_ROOT` at
`9bb41680` (the adapter needs `verify_seed_base`).
