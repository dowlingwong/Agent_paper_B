# M10 preview docstring correction — independent review

AI-assisted (Codex), 5 November 2026. **ACCEPTED for this documentation-only correction.** Reviewed the uncommitted diff in `/private/tmp/paper-b-mac-20261104` against its HEAD `50b28aaefc665ba392d52eed1d2c68572e53747c`; diff SHA-256 `81d48b771387fe9aabf49c93c2d79c99c8dc0c2620339c6979fd0c112a54adfd`, resulting file SHA-256 `5649d21f7d48044ca9aeff2c83fbc184c14c3cf2a346c335ec09cc7056b2076d`.

The former statement that real submission is unconditionally disabled is stale. `r1/scripts/hk2/hk2_config.json` has `real_submission_enabled.value` set to `false`, and `hk2_submit.py:24–28` requires that setting to be true before submission. `hk2_submit.py:42–50` separately refuses the EVIDENCE kind and evidence phases. The corrected docstring states only those facts; it retains the explicit statements that the preview does not connect to submission, confer authority, or establish a reviewed execution boundary. The default-off switch does not itself authorize any job.

The diff changes only the leading module docstring; a comparison of Python ASTs after removing that docstring found the remainder identical. No tests, server, scheduler, model, GPU, or experiment were run. This review does not accept EVIDENCE submission, HK6/HK7 readiness, or the preview's proposed catalogue.
