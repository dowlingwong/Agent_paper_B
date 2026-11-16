# Track S tabular_mlp S0.4 — TASL-7 pause drill record (14 Nov 2026)

- pre-drill: distinct roots = 1 (22:19:30Z), tmux = trks_llm / trks_s04_t7 / trks_watch, lease HELD, compute app 800412, FORCED count 0.
- `touch $R/trks_drill.active` at **2026-11-14T22:19:30Z**.
- watcher `priority marker seen (…/trks_drill.active): pausing` at **22:19:37Z** (7 s; within ~1 min).
- collector `trks_s04_t7` exit **22:22:26Z rc=0**; manifest `sessions=1`, `done {roots 2, forks 0, leaves 0, failed 0, exhausted 0, deadline_hit false, status paused}`.
- watcher `servers stopped; lease released` at **22:22:37Z**; observed lease FREE / 0 llama-server / no trks_llm / no listener at **22:22:57Z** (graceful ~20 s shutdown); compute apps empty; **no FORCED** line.
- pause latency: marker → watcher "servers stopped" = **3 m 07 s**; marker → observed lease-free = **3 m 27 s**.
- watcher STOP files recorded **before deletion** in `$R/logs/STOP_FILES.s04t_20261114T222237Z.txt` (3 files, all 0 B sha e3b0c442…):
  `out/digits_mlp/s05_t7_20261113/STOP` (inode 57049062), `out/smoke/STOP` (inode 57048195), `out/tabular_mlp/s04_t7_20261114/STOP` (inode 57305747).
- marker removed **22:23:09Z**; new watcher `marker gone` line **22:23:37Z**; STOPs deleted (0 remaining); old tabular scenes untouched (the digits s05_t7 scene's drill STOP removed, restoring its post-retirement state).
- resume **22:23:47Z** via the committed launcher (fresh k=1 server pid 803220, readiness 22:23:49Z, collector `trks_s04_t7`); roots grew 2→3 (22:26:13Z), no duplicate root_id, no duplicate (instance,budget_index) in s04_rows (54 rows), exhausted 0.
