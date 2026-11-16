# TASL-7 rename probe: checked capture amendment — 7 November 2026

AI-assisted (Codex). **Draft for independent review; not executed and not authorization.** This append-only amendment supersedes the capture command in `TASL7_RENAME_CROSSDIR_AMENDMENT_20261107.md`; all of that document's script SHA, preflight, nonpreemption, no-deletion, single-attempt and STOP conditions remain in force. The prior files are retained unchanged. The previous capture command did not explicitly check whether writing the SSH status or hashing the evidence succeeded. A failure in either operation makes the evidence incomplete and must STOP, even if SSH itself reported zero.

After fresh independent review of this exact command and the cross-directory script, and after the specified separate full operator census, the operator may use the following Bash template. It checks exclusive local capture creation, records and checks the actual SSH client exit status, checks closing the capture descriptor, and treats status-write, close or digest failure as STOP. The evidence file is never removed or reused. `shasum` reads the already closed capture; it prints the digest to the operator's transcript and is not a proof that SSH delivered every remote byte. If no successful digest is produced or the complete script output/footer is absent or ambiguous, retain the partial capture and remote scene without retry. A transport failure may leave the remote execution outcome unknown even when an SSH status was recorded.

```bash
set -C
capture=/private/tmp/tasl7-rename-capability-20261107-7d322b6c3a1e4c2f.txt
if exec 3>"$capture"; then
  :
else
  printf '%s\n' 'STOP: local capture could not be exclusively created; SSH not invoked' >&2
  exit 1
fi
if ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' \
  < docs/r1/proposals/tasl7_rename_probe_20261107/probe_crossdir.sh >&3 2>&1; then
  ssh_status=0
else
  ssh_status=$?
fi
if printf '\nSSH_EXIT_STATUS=%s\n' "$ssh_status" >&3; then
  :
else
  printf '%s\n' 'STOP: cannot record SSH status; retain partial capture and remote scene' >&2
  exit 1
fi
if exec 3>&-; then
  :
else
  printf '%s\n' 'STOP: capture descriptor close failed; retain scene' >&2
  exit 1
fi
if shasum -a 256 "$capture"; then
  :
else
  printf '%s\n' 'STOP: capture digest failed; retain scene' >&2
  exit 1
fi
exit "$ssh_status"
```

The command checks output operations it invokes; it does not guarantee durable local storage or detect every failure in a remote process, SSH transport, or a concurrent host actor. The operator must confirm the complete output and success lines, inspect actual SSH status and any errors, record invocation time, UUID and digest, and obtain fresh independent evidence review. Any mismatch, incomplete evidence, output/capture failure, remote STOP, unconfirmed release or ambiguous transport remains STOP; no deletion, further site action, automatic retry or B1 launch is implied.
