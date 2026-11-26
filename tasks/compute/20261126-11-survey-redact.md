# compute/20261126-11 — resource survey: remove other users' names before it reaches main

Your survey (`compute-resource-survey-20261126` @ `19396b62`) is accepted as a survey. The repository is public, and the report
and its captures name other users of shared hosts (user names, and a project name of another user's processes). `canon/README.md`
rule 8 and compute/20261126-03 item 2 keep other users' identities out of our records.

One new commit on the branch: replace each other user's name and project name with `other user A`, `B`, … (consistent within
the report), in the report and in every capture. Keep counts, memory and card numbers. Keep our own account. Give the new report
sha256 and the capture hashes. The coordinator then merges the branch (tier D).

Your findings are used now: Ada is ready for LLM serving and not for P.4 training (no torch environment, no usable container
runtime). TASL-7's card is free. A second Ada sample and a second TASL-7 sample go into your next pool-watch round.
