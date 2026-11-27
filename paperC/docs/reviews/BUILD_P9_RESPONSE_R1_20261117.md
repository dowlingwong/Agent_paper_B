# P9 response to independent review round 1

17 November 2026. **ENGINEERING_ONLY.** Response to the [round 1 review](BUILD_P9_REVIEW_20261117.md) of `0e281ae9`.

1. **MAJOR — Exact constant paired differences.** Floating-point rounding in the sample mean of `[0.1, 0.1, 0.1]` produced a spurious positive standard error. The paired test now checks exact equality of the differences before estimating variance. It records the common value and zero standard error and marks the comparison as unresolved. The regression fixture exercises both declarations at a supplied zero-effect power of 0.80, and verifies that an explicitly supplied positive known SD still yields a test.

The full CPU benchmark reran all 12 repetitions. All substantive fields match the reviewed JSON, with only its source fingerprint refreshed, and the report matches byte for byte. The full Paper C suite passed 234/234 with zero skips.
