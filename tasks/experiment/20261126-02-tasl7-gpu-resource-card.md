# experiment/20261126-02 — who holds TASL-7's GPU; resource card

Read-only, no `sudo`, touch nothing of another user.
1. TASL-7: `nvidia-smi` compute processes with user, memory and start time, now and once more after six hours. A job
   of user `jiachenl` held the card on 26 Nov. Report what you see; the author decides.
2. Resource card of `canon/COMPUTE.md` §5 for TASL-2, TASL-7 and Ada: hostname, user, `nproc`, `lscpu | head -20`,
   `free -g`, `nvidia-smi` (model, memory, driver), `df -h` of the work paths.

Done when: one report with the values. No branch is needed unless you want to keep captures.
