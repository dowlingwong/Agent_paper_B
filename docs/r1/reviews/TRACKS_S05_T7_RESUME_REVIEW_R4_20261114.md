# Independent review, round 4 (final confirmation) — Track S `digits_mlp` S0.5 resume unit (rev 4), 14 November 2026

**Reviewer.** Fresh and independent; I did not write the unit, the reviewed launchers, the pause record or the reports.
I read a `/tmp` clone only. The TASL hosts are unreachable in the author's VPN window and I was told not to attempt
access, so **no host access was made and nothing was executed**. Nothing under `/Users/wongdowling/Documents/agent_paper_B`
was modified; only `/tmp` and this file were written.

## Unit reviewed

- Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`; remote head and clone HEAD both
  at tip **`86295707a428f2556ac39d7a5ca62baee97dd1a3`** ("Track S S0.5 resume unit rev 4 (R3 path wording fix)"), tree
  `e8fa67f42725e85c3c2e838bf93c951570db11b4`; one commit on top of the R3-accepted `5e0cdded`.
- `docs/r1/proposals/TRACKS_S05_T7_RESUME_20261114.md`: blob `ce08f23a2fc74d8473dafbf54897ed31304978a2`, **75 lines,
  7111 B, sha256 `9737783c82f5637aa212ffb645fe9addef9d8cd9292ef3188c2ec417f01842f5`** — matches the pinned hash.
- Commit scope: **one file, +6/−4, three hunks** (title, §0.2, §2). No code, pin, STATUS or runbook byte change; no
  secret; non-executing ("candidate for independent review; not an execution", line 3).
- Re-hashed in the clone: launcher `tasl7_digits_s05_20261113.sh` `3e9574643a6736a14ce28f00dd0717a57de3987cc84242b7dc255139f7615151`;
  `tasl7_digits_s05b_20261113.sh` `3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a`;
  `r1/tracks/ops/trks-run` `b53bc811dc177000c27d33dc43f5f964954c15d7981c5705ad7fcadb851064c4`;
  `r1/tracks/collect.py` `d09cf1f4e1ce6fc6964b4e70a78a968279fa777be839c00c30f1a0f1398364d5`.

## Verification of the three requested items

1. **Precondition 2 — PASS.** §0.2 now reads `$WORK=scratch/digits_mlp/s05_t7_20261113`
   (`roots/<id>/root_trials.jsonl` and `roots/<id>/snapshots`; the leaves/S0.5b inputs live under `$WORK`, not `$RUN`),
   with `done.status` asserted `paused` and the new `len(manifest['sessions']) == 1`. Parentheses on lines 13–20 balance
   (5 open / 5 close) — the duplicated parenthetical from rev 3 is gone and there is no false `snapshots` path under
   `$WORK` itself. Matches code: `collect.py:832` `root_dir = run.work / "roots" / root_id`; `collect.py:926`
   `work/"roots"/.../root_trials.jsonl`; `collect.py:839` `root_dir / "snapshots"`.
2. **Copy-back — PASS.** §2 names `$RUN/s05_calibration.jsonl` and `$RUN/s05b_truncated.jsonl` ("both must exist"),
   the other run `*.jsonl` ledgers (`roots`/`forks`/`leaves`/`failed_units`/`audit_runs` as present), the manifest,
   the run's logs — collector `.log`/`.cmd`/`.exit`, S0.5b `s05b_t7_20261113_launch.log` and
   `trks_s05b_t7.{log,cmd,exit}` as present, and the launcher stdout/rc under `$R/logs/` — and `SHA256SUMS`. The S0.5b
   names match the code (`s05b` launcher `:10` `LOG=$R/logs/s05b_t7_20261113_launch.log`, `:9` `SESSION=trks_s05b_t7`,
   `trks-run`). No `sp05*` glob is used as a copy selector; `collect.py:1017` writes `run.out/"s05_calibration.jsonl"`
   and `:944` `out/"s05b_truncated.jsonl"` (out = `--out` = `$RUN`), so the named outputs are the real ones.
3. **Scope / semantics / runtime — PASS.** Title is rev 4. The diff vs `5e0cdded` is exactly the two requested fixes
   (the §0.2 path wording, already-requested single-session assertion, and the §2 S0.5b log naming); nothing else
   changed semantically. Non-executing; no code/pin/STATUS change; no remaining defect in an executing step after B1.

## Residual notes (not blocking; carried from R3, no new findings)

1. The literal string `sp05*` survives only inside the explanatory parenthetical "(the old `sp05*` glob matched
   nothing)" — it is a historical note, not an operative glob, and the copy list is explicit filenames + existence
   assertion. A purely literal string check would see the token; this is cosmetic, not a path error.
2. The launcher tees its stdout to `$R/logs/s05_t7_20261113_launch.log` but writes no launcher rc file
   (`tasl7_digits_s05_20261113.sh:14–15`); "launcher stdout/rc under `$R/logs/`" is satisfied for stdout, while the rc
   is the invocation's exit status to be recorded by the operator. The "assert each named file exists" clause binds the
   two explicitly named JSONLs, so this does not fail an executing step.
3. Host-side facts (pause scene, STOP inode/sha, manifest counts) remain execution preconditions; they were checked
   against the reviewed code and prior accepted evidence, not against a live host.

## Conclusion

The single R3 defect (F1, the `$WORK` snapshot path) is fixed, the R3 notes 1–3 are carried (title rev 4, S0.5b logs
named, `len(sessions)==1` added), the diff is confined to the reviewed document, and nothing remaining would fail at
runtime after B1 ends. The exact bytes at tip `86295707…` are the confirmed unit; execute only after the §0
preconditions.

VERDICT: accepted
