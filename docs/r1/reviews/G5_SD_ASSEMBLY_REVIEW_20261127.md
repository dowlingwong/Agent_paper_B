# G.5 sd-matched assembly review — 27 Nov 2026

Task `local/20261127-09`, assembly unit, under R1-G5-TAILS-CONSUMERS (2).
Independent tier-E reviewer (Codex). Published comparison base `6aee0eb34a9c8bae4c9c24d93b261d24a76a8403`;
resumed Student-t tip `b9bc00fc75d77d9609d2dd4473a5ca7dd0b98185`.

**Verdict: ACCEPTED** at `70a69347ddb9610d5cc4a4c89b0d4a854751affb`.
The prior candidate `b53ddbd2` refused malformed suffixes and mismatched exponents, but its declaration parser
still treated the comma in `ν = 5,5` as punctuation and silently accepted the prefix. The correction consumes the
comma followed by a digit within the candidate token, which the numeric full match refuses. Tests cover this,
comma-space prose, exponent notation and exact round-trip rendering.

The assembly's label wire format is parametric. It binds the signed tail law and degrees of freedom in
`soft_parameters`, with `sd_matched` provenance in the build entry. The target uses standard deviation
`s = sigma_node / sqrt(k_label)` and Student-t scale `s * sqrt((nu - 2) / nu)`. The synthetic assembly test
reconstructs its output against SciPy, checks variance matching and distinguishes the Gaussian and Student-t
targets. The Gaussian assembly bytes match the previous path. Declarations are validated before sealed reads.

The scope is assembly. SFT, arms-frozen fits and the gate remain the separate consumer unit in
R1-G5-TAILS-CONSUMERS (3). P11 and publication-time binding are required independently for note publication.
The review examined committed code and synthetic fixtures. No evidence data was opened.
