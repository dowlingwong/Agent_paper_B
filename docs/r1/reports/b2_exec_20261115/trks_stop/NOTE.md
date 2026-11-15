# Track S STOP 4 consequences — operator record (15 November 2026)

**Author decisions (branch `author-stop4-20261115` @ `1f5f24e3`, PLAN §10):**
- `R1-TRACKS-STOP4-END`: Track S ends at STOP 4; no EVIDENCE; TASL-7 is no longer allocated to Track S; all Track S directories/processes/branches/data stay exactly as they are (no move/modify/delete); cleanup only by a later author decision.
- `R1-TRACKS-STOP4-CONSEQUENCES` item (7): `trks_watch` on TASL-7 keeps running until B2 ends; after B2 ends normally and the B2 marker is retired, the experiment agent stops it with an independently reviewed unit, **without deleting any file**.
- Item (4): TASL-2 is released from Track S, but after its network is restored the experiment agent performs a **read-only inventory** (Track S servers, GPU lease, processes); the inventory goes to review before any other use; nothing is resumed, no lock is released; the scene stays untouched pending the author's decision.

**Units prepared here (reviewed before execution):**
- `stop_trks_watch.sh` — stops only the pinned `trks_watch` tmux session (pane pid `1388760`, script SHA `cf6884…`) after gates: `b2.exit`=0, `POSTRUN_COLLECT_OK`, `marker-retirement.json`, marker absent; records before/after process tables; verifies the manifest/STOP inventory is byte-identical to the post-watch inventory (scene unchanged); no file is written to or removed from the Track S scene.
- `tasl2_readonly_inventory.sh` — read-only SSH inventory to a local directory (no start/stop/signal, no lock release, no writes on TASL-2). TASL-2 is not resolvable from this Mac at present (`ssh: Could not resolve hostname tasl2`), so it runs only after the network is restored.
