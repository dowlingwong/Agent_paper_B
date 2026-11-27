# local/20261127-31 — screening on deepthought2 (R1-SCREEN-DEEPTHOUGHT2): runner binding and note re-issue

PLAN **R1-SCREEN-DEEPTHOUGHT2** (`main` `0bb81e26`): CPU only, at most 64 CPUs. Prepare (1) whatever host-specific runner binding deepthought2 needs
(the evidence environment, harness `6adf3859`, the rebuilt cache tree `3843b53c…` or a rebuild there, the worker count within 64 and the reviewed launch
binding, the co-tenancy headroom rule) as a reviewed unit if code changes, and (2) a third re-issue of the note for deepthought2 (host line, worker count,
fresh stamp; same design, seeds, analysis and STOP rules; the old STOP records preserved, none of their rows carried into the analysis). Run its check and
get the screening reviewer's diff re-check. The row pre-authorises publication of the reviewed note. Report the tip and the exact launch command for compute.
