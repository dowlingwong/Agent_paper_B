# TASL-7 B1 handover: concrete read-only checks and command boundary

AI-assisted (Codex). **Candidate for independent review; not permission to access TASL-7 or create a marker.** This is a locally prepared supplement to the accepted conditional handover draft `B1_TASL7_HANDOVER_20261107.md`, not an executable launch or restoration procedure. Source: `MAC_OVERNIGHT_PROMPT_20261107.md` §§0.3–0.5; `PLAN.md` rows R1-EXAM-HOST-B1B2-TASL7 and R1-TRACKX-MARKER; O2 in the integration checkout's `docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md` SHA-256 `e27b36752a5f22a645a070c7720084ea8f157f176dca3b867aea8c54de34f867`; Track S operator runbook rev 3.3 SHA-256 `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`; retained TASL-7 census and watcher inspection and their independent reviews. No remote host, model, GPU, process, or experiment was accessed for this document. The retained watcher file SHA `cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112` is not proof of the running shell's code.

## Exact read-only inspection after host-access prerequisites

The prior census observed other-user agents and a Track S watcher; it does **not** establish whether another operator holds the host. First obtain a reliable ownership/cooperation handover through already-authorized records or the author/operator; if that cannot be established, do not access or change the host beyond the authorized initial census. The following proposed site commands are observation-oriented and contain no explicit remote file writes or process signals. **Do not run this block until ownership and site identity are established, the applicable authority is checked, and each tool's side effects are independently verified for the actual site.** In particular the `tmux` client uses a Unix socket and socket directory; its behavior cannot be certified side-effect-free from this static report. If that behavior or any other tool is unverified, STOP before the block and use existing reviewed evidence. Once independently reviewed for the site, an authorized operator may run it with Bash, capturing complete output with exclusive creation into a demonstrably new operator-owned local report path; do not use a clobbering shell redirection. Any failure, inaccessible path, ambiguous identity or changed state stops further action. These observations are not an exclusivity test. Do not copy output into an existing operator worktree or expose command-line secrets.

```bash
set -euo pipefail
printf 'UTC: '; date -u +%FT%TZ
printf 'host: '; hostname
printf 'uid/user: '; id
printf 'home: %s\n' "$HOME"
ls -la "$HOME/r1_locks"
stat -c 'lock device=%d inode=%i owner=%u type=%F path=%n' "$HOME/r1_locks/gpu0.lock"
sha256sum /home/dowling/r1_tracks/bin/trks-watch
printf '%s\n' 'tmux panes:'
tmux list-panes -a -F 'session=#{session_name} pane=#{pane_id} pid=#{pane_pid} command=#{pane_current_command}'
printf '%s\n' 'process metadata (all visible users; command name only):'
ps -eo user,pid,ppid,stat,etime,comm
printf '%s\n' 'GPU inventory:'
nvidia-smi --query-gpu=index,uuid,memory.used,memory.total --format=csv
printf '%s\n' 'GPU compute applications:'
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv
printf '%s\n' 'disk:'
df -h "$HOME"
printf '%s\n' 'complete checkout STATUS files (historical status is not live ownership):'
for repo in "$HOME/exam-x/work/agent_paper_B" "$HOME/r1_trackp/Agent_paper_B" "$HOME/r1_tracks/work/Agent_paper_B"; do
  status_path="$repo/docs/r1/STATUS.md"
  printf 'CHECKOUT %s\n' "$repo"
  if [ -L "$status_path" ] || [ ! -f "$status_path" ] || [ ! -r "$status_path" ]; then
    printf 'STOP: missing, inaccessible, non-regular or symlink STATUS: %s\n' "$status_path" >&2
    exit 1
  fi
  before=$(sha256sum "$status_path" | cut -d ' ' -f1)
  cat "$status_path"
  after=$(sha256sum "$status_path" | cut -d ' ' -f1)
  if [ "$before" != "$after" ]; then
    printf 'STOP: STATUS changed while read: %s\n' "$status_path" >&2
    exit 1
  fi
  printf 'STATUS SHA-256: %s\n' "$before"
done
```

Capture separately the names, ownership, type, device, inode, size and timestamps of every `manifest.json` under `/home/dowling/r1_tracks/out`, the corresponding sibling `STOP` path including explicit absence, the three watcher's marker paths, and the current watcher log position; treat symlinks, traversal errors, inaccessible directories and concurrent changes as STOP. This must use the watcher's actual `find ... -name manifest.json` semantics rather than assuming only regular files; the watcher can touch an existing STOP, changing timestamps. Even an empty observed set does not authorize mutation of a later-discovered or unowned path. The operator must compare all applicable STATUS sources, establish the latest relevant running/stopped entries and STOP on ambiguity; a prefix or historical checkout alone is insufficient. The before/after hashes do not prove an atomic snapshot or rule out a change-and-revert. The all-process listing may be restricted by site visibility; it does not establish ownership, absence of hidden processes, or no future process start. Do not print or collect arbitrary process arguments or secrets. The expected GPU UUID is `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`; the historical 585 GiB observation is not a current capacity guarantee. Real `flock`/descriptor checks and worker determinism are separately reviewed engineering actions, not part of these read-only commands and not permitted merely because this snapshot looks idle.

## Coordination and mutation boundary

Before considering the marker, the authorized operator and Track S/P owners must establish in durable handover evidence that no other operator holds TASL-7, identify the actually executing watcher and Track S server/session, stop or finish Track S collectors at their own safe point without preemption, and prevent new Track S/P starts for the whole handover. `trks-watch` matches a specific same-UID command-line pattern and after one hour can attempt `tmux kill-session -t trks_llm` even if matching collectors remain. A PID name, an empty `pgrep`, a historical script hash, or an empty GPU-app query alone cannot establish all collectors, server identity, watcher loaded bytes, or cooperation. Track P's owner must identify P.3a's actual checkpoint and demonstrate a safe pause and a way to restore its recorded prior state; do not send a signal or alter its work/data as a substitute. If an owner, identity, safe point or no-new-start coordination cannot be established, **do not create the marker**.

The author gate, real host preflight and approved-note ordering remain prerequisites. After every prerequisite is independently satisfied, the intended marker path is `~/r1_locks/trackx_evidence.active`: the operation must use exclusive non-following creation, fail if any path already exists, bind a unique run identity and the reviewed checkout, record inode/device/owner/content hash, flush durable evidence, and preserve any partially created entry on error. Publish the matching `## <date> — Track X B1 running` STATUS from the authorized own checkout; do not edit another operator's checkout. Only then observe the reviewed watcher pause and validate its precise actions against the pre-inventory. A `FORCED` log, unexpected STOP touch, unseen process, ownership change or other STOP preserves the scene and waits for the author. These are required properties, **not an approved implementation**: no safe exact marker-creation or STATUS-publication command has yet been reviewed against this site and its concurrency conditions.

On verified **normal completion**, release the lease, then retire only the marker created by this handover, and any STOP file proved absent before and created by this handover, by an atomic same-filesystem non-overwriting move to a uniquely named `_to_delete/` location; verify each entry's device, inode, owner and content before moving and preserve all bytes. A pathname pre-check followed by ordinary `mv` is not an atomic no-replace guarantee and must not be presented as one. An identity check followed by rename still needs an explicitly reviewed same-UID cooperative ownership/race assumption. Observe the watcher's marker-gone transition, restore the recorded Track S/P state only through commands owned and reviewed for those tracks, then run the complete-batch verifier and publish its result/manifest. Preserve every pre-existing STOP and unowned path. On any **abnormal STOP**, do not retire markers or STOP files, restore, retry, or change pins; preserve and report.

No source establishes an exact safe Track P pause/resume command, the running watcher's code identity, a complete no-new-start coordination mechanism, or race-safe no-replace retirement capability on TASL-7. Therefore there is currently **no complete reviewed executable mutation sequence**. To unblock: the Track S/P owners or author provide an attributable current handover and safe points (elapsed time unknown); the B1 implementer prepares and tests exact creation, publication and retirement operations without deleting anything, and an independent reviewer checks them (engineering/review effort unknown until ownership and site capability are known); an authorized site operator then verifies the relevant site capability and current state. Any author-note ordering clarification and all other B1 gates remain separate. This report does not establish B1 readiness.
