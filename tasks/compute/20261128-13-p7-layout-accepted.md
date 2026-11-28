# compute/20261128-13 — P7 layout accepted: RTX 4090; run the smoke on TASL-2

Your proposal (`main` `980c6666`) is accepted under R1-HOST-FREE (2)(c): D.3a's measured proposer model is the **RTX 4090**. Run the seven-arm smoke on
TASL-2 now (`openml_climate` 6301/6302, replicate seeds as declared, harness `9bb41680`, exclude CPUs 8–11, no G6 Y audit), record per arm/seed time,
resource peaks and `gates.worker`, fresh review. Note for the campaign layout later: TASL-7's card is the same model, so D.3a chunks may also run there
once that card is empty and its own environment/lease check passes; that is placement, not a new model. G.5 also needs the TASL pair, so report the
D.3a projection in 4090 hours so the coordinator can order the two.
