# compute/20261128-23 — D.3a production template: per-chunk server checks (local's finding)

Local's stub check (`coord/local` `1a6a2cf5`): when the template's own server failed to bind, a separate responder answered `/props` and the template
went on to the chunk. Fix the production template so each chunk proceeds only if the endpoint it calls is served by the server process the template
started (PID and port owned by that process, `/props` model file and `n_ctx`/slots equal to the manifest, the GPU UUID of that process equal to the
leased card under `~/r1_locks/`), checked before every chunk; any mismatch is an infrastructure STOP with the scene sealed. Add the review minors.
Engineering test of the failure path (server fails to bind; foreign responder) and the success path. Record + review. No campaign.
