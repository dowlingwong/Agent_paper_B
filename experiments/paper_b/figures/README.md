# Paper B figure-generation namespace

Each script here is a **slot** named by the manuscript's experimental plan
(`papers/paper_b/sections/07_experiments.tex`, Table "Required figures and
tables").  A slot refuses to run without a qualified dataset
(`--dataset <dir>`) and does not implement generation until the dataset exists
with its frozen split manifest.  No fabricated curves are permitted in this
tree.
