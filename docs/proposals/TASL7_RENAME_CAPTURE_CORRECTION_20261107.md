# Rename capability probe capture correction — 7 November 2026

AI-assisted (Codex). This new file supersedes the capture command in `TASL7_RENAME_CAPABILITY_PROBE_20261107.md`; the rest of that proposal and all review/operator prerequisites continue to apply. The earlier command places SSH outside an `if`, so a caller shell that already has `errexit` set could exit on SSH failure before recording the status. No invocation occurred, and the earlier proposal is retained unchanged.

After exact-byte independent review and fresh full operator preflight only, use this Bash command. Noclobber opens the unique local capture before SSH. The `if` records an SSH failure even with `errexit` set; a capture/write error, SSH status 255 or lost transport still requires treating the remote outcome as ambiguous, retaining the scene, and stopping without retry. Local file collision prevents SSH invocation. This command does not itself establish authorization or any prerequisite.

```bash
set -C
capture=/private/tmp/tasl7-rename-capability-20261107-7d322b6c3a1e4c2f.txt
exec 3>"$capture" || exit 1
if ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' \
  < docs/r1/proposals/tasl7_rename_probe_20261107/probe.sh >&3 2>&1; then
  ssh_status=0
else
  ssh_status=$?
fi
printf '\nSSH_EXIT_STATUS=%s\n' "$ssh_status" >&3
exec 3>&-
shasum -a 256 "$capture"
exit "$ssh_status"
```

The script and this correction require a fresh independent source review before any host action. They do not authorize B1 launch or clean-up.
