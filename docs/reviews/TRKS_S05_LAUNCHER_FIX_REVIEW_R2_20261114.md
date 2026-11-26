# Track S S0.5 resume unit rev 5 — final narrow confirmation of the launcher-sha fix (round 2)

Reviewer: fresh independent agent (did not write the change). Date 2026-11-14, ~10:40Z.
Unit: repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`, tip
`9b217c53ab007c25ac39a9a87a128480620c0db4` ("Track S S0.5 resume unit rev 5 (cite the fixed launcher sha; no-op STOP;
K clarification)", parent `e253a423069d44248cd8496eddbeec587c49e489`), fetched in a clean `/tmp` clone. Nothing under
`/Users/wongdowling/Documents/agent_paper_B` was touched; TASL-7 was read only (`ssh tasl7`, read-only commands).
Writes were confined to `/tmp` and this `_xfer` directory.

Subject bytes (re-hashed in the clone):

```
f9373cb532afe17d76683ea4e80f1296d60e5136b1287f14ba310a4bbd5a7431  docs/r1/proposals/TRACKS_S05_T7_RESUME_20261114.md  (81 lines)
f823b86a85272ef6246ceb3ce9f5142057eb1b5f297a1d5ddd20394ebaba3dd3  r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh  (79 lines)
3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a  r1/tracks/ops/launch/tasl7_digits_s05b_20261113.sh
```

Previous launcher revision (still what is installed on TASL-7): `3e9574643a6736a14ce28f00dd0717a57de3987cc84242b7dc255139f7615151`.

## 1. Fixed sha cited; `3e957464…` only as the aborted revision; title rev 5; "sha above" gone — PASS

- Title (line 1) reads `… (14 November 2026, rev 5)`; `grep -c "sha above"` = 0.
- `§0.4` (line 25) now cites the full fixed sha
  `f823b86a85272ef6246ceb3ce9f5142057eb1b5f297a1d5ddd20394ebaba3dd3`, matching the file bytes at this tip exactly.
- `3e957464` appears exactly once in the unit (line 29), inside the first-resume note, correctly labelled "the previous
  script revision" that "aborted rc=1 before starting anything". Line 31 now says "The fixed revision is `f823b86a…`
  (see §0.5; the new unit script sha)" — the old self-contradiction/pointer to the broken sha is resolved.
- `grep -rn f823b86a` now finds the unit (lines 25, 31); the R1 finding that it appeared in no file is fixed.
- §0 commit diff is 3 hunks / 8 insertions / 5 deletions, all inside this one file.

## 2. Already-retired STOP no-op branch present; host matches — PASS

`§1 step 2` (lines 41-43) adds: "if `$RUN/STOP` is already absent and a single `$RUN/_to_delete/STOP.retired.*` exists
with 0 B, inode 57048847 and sha `e3b0c442…`, skip the rename and record that verification; do not create a second
one". Any other combination still falls through to the fail-closed `STOP` checks. Read-only host state confirms exactly
that case:

- `out/digits_mlp/s05_t7_20261113/STOP` absent;
- `_to_delete/` mode 700, containing **one** `STOP.retired.20261114T103527Z`: 0 bytes, inode **57048847**, sha256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, original pause mtime 2026-11-13 05:47:35 -0800;
- nothing else under `$RUN` changed since the pause except `_to_delete` (mtime 2026-11-14 02:35:27 -0800 = rename time).

## 3. K clarification — PASS, no contradiction elsewhere

`§0.4` (lines 23-24) now states the launcher's `K` is the **server count 2**, distinct from the manifest's audit
`K`=5, which is `--k-audit` seeds and is not changed by the resume. Verified against the code: `collect.py` sets
`DEFAULT_K = 5` and records `"K": int(args.k_audit)` in the manifest (the resume command in `.cmd` passes no
`--k-audit`, so the manifest's `K: 5` reproduces and the `MANIFEST_KEYS` resume check passes); the launcher has
`K=${K:-2}`, `trks-servers $K`, readiness over 18101..18102. Host manifest: `"K": 5`, `phase "S0.5"`, one session.
Other `K`/`k=2` occurrences in the unit (`§0.5`, `§1 step 3`) agree; no contradiction.

## 4. Scope, launcher, secrets — PASS

`git diff --name-status e253a423 9b217c53` lists exactly `docs/r1/proposals/TRACKS_S05_T7_RESUME_20261114.md`;
no launcher, no other path, no mode change (100644 both revisions, blob `9457021c…` → `9d3c1bdb…`). The fixed launcher
is unchanged and still `f823b86a…`, 79 lines, LF, ends in a newline; `bash -n` rc=0. Secret/credential pattern scan over
the changed file and the commit diff is empty. Historical mentions of `3e957464…` in older reports/reviews are
historical facts, not contradictions of this unit.

## 5. Host state and next actions — consistent

- Deployed launcher is still `3e957464…` (4816 B, mode 700) — the deploy of `f823b86a…` is genuinely pending, as
  the next action requires; installed S0.5b sha `3685dfe6…` matches the unit.
- Captured paused command: `$R/logs/trks_s05_t7.cmd`, 786 B, sha256
  `fe9fae36311875470f6682539479ec2496e8be9bfe7bd56c5a32837dbd84054b`; the pre-resume capture in
  `/private/tmp/trks-s05-resume-20261114T103508Z/old.cmd` is byte-identical (`cmp` clean).
- No `trks_llm`, no `llama-server`, no collector session; only `trks_watch`; lease FREE, no GPU compute app; markers
  absent; paper `8237fd02…` clean, prior sha `5c849d15…` — the preconditions the unit names are satisfiable.
- The recorded first-resume abort is corroborated: `$R/logs/s05_t7_resume_launch.rc` = `rc=1`, stdout empty, collector
  log/exit untouched since 2026-11-13 13:03:00Z, and the retired STOP above. So the aborted attempt started nothing,
  and the no-op STOP branch covers its only side effect.
- Next action as stated is correct: deploy `f823b86a…` to `$R/launch/tasl7_digits_s05_20261113.sh` on TASL-7, verify
  sha256 + `bash -n`, run `K=2 bash $R/launch/tasl7_digits_s05_20261113.sh` in tmux `trks_s05t7resume`, expect
  `trks_llm` with 2 servers (18101/18102) and collector `trks_s05_t7`, then require `trks_s05_t7.cmd` byte-identical
  to the capture above.

## Residual notes (non-blocking, none prevents the resume)

1. Pre-existing minor not taken in rev 5: `§0.2` still says "`done` holds the counts … and `done.status`", while the
   counts live at `manifest["sessions"][0]["done"]` (there is no top-level `done` key). The values are as stated —
   `{roots 22, forks 6, leaves 0, failed 0, exhausted 0, deadline_hit false, status "paused"}` — once read at the
   nested path; R1 flagged the wording and rev 5 left it unchanged.
2. "see §0.5" resolves to `§0` precondition item 5 (the document has no numbered 0.5 subsection). The full sha is
   already written in `§0.4`, so no ambiguity remains; wording only, and that item 5 restates itself.
3. `§0.4`'s "Deployed reviewed scripts: … `f823b86a…`" holds only after the pending deploy; the host still has
   `3e957464…`. Read it as the deploy-verification precondition, which is what the next action implements.
4. `§0.2`'s "no new/removed paths" check must be read against the pause-state capture (the 10:35:13Z stage-A log
   predates the rename); at resume time `_to_delete/` exists and `$RUN/STOP` is absent, which `§1 step 2`'s no-op
   branch explicitly anticipates.

VERDICT: accepted
