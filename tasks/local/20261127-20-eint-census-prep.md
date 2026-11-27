# local/20261127-20 — Paper C E-INT development census: prepare only

Owner: local (drafter). The author's instruction of 27 Nov and runbook §5. One GPU card, a fixed memory cap and a fixed number of effective
training tokens; matched seeds; four cells `baseline / A / B / A+B`, where A changes batching and B enlarges the context. The question is
whether A changes B's feasibility or gain. Write the independent run instructions (workload check of `autoresearch_fixedtokens`, token
accounting, masks and loss accounting for packing, the memory cap, the cells, the seeds, the outputs and the readout), with code and tests,
reviewed. **Do not launch.** The run waits for an available card and a launch task file; Paper B's critical work takes the cards first.
