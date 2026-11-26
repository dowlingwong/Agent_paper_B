# Independent review — Track S operator runbook rev 3.3 and the Track P evidence-marker helper (30 Oct 2026)

Reviewer: a fresh agent (Claude) that had not seen the work in progress, spawned by the chat session. It tested the §11.4 watcher with a stub collector and the drill marker, and the helper with a stub `nvidia-smi`. Record written by the chat session from the reviewer's two reports.

## Round 1 — not accepted

**BLOCKING:** none.

**MAJOR**
1. The drill counts were read from the manifest. The manifest is written only at session start and end, and its counts are per session. → Fixed: count distinct ids in `roots.jsonl`, read `sessions[-1].done.status`, and check for duplicates.
2. "done + exhausted = planned" had no data source, and forks were counted as units. → Fixed: §0.6 "Where the counts are"; the rate is exhausted / (committed + exhausted); a phase is finished when a dry run shows nothing left to do.
3. 3.0b let multi-day TASL-7 phases proceed with no Track P marker. → Fixed: a gate in 0.3(c) for Phase 6 and later.

**MINOR**
4. Status `done` instead of `complete`. → Fixed.
5. "3.0 below". → Fixed.
6. Server pre-checks ignored the drill marker. → Fixed.
7. 3.0b omitted resume and checks. → Fixed.
8. Helper GPU check failed open. → Fixed: `-i 0`; a failing `nvidia-smi` counts as busy.
9. Exit codes collided and no job rc was logged. → Fixed: log lines.
10. Race between concurrent `begin`s. → Fixed: `set -C`.
11. `end` matched the phase as a regex. → Fixed: `grep -F`.
12. Children inherited the lock. → Fixed: `flock -o`.

## Round 2 — accepted

All findings are fixed. The reviewer named three wording items: one remaining `"done"`, two "exhausted / planned" wordings, and a note on the 3.0b log line. It also suggested one doc line on `-o` background children. All four are fixed in the committed version; no re-review is needed.
