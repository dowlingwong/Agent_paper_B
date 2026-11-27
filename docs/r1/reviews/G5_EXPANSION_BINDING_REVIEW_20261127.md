# Independent tier-E review of the G.5 expansion launch and release binding

Task `local/20261127-30`, unit 2. Base `f43823dad358a25608fe27013221eba9aaa7d385`.
Final reviewed code and template `0f365fac2209811ab846659d106f0655a9e0c172`.

Verdict: ACCEPTED

The initial review at `b629da3e407bbc652a70d6984e9c642cdf7124ae` withheld acceptance. It found a
checkout-specific split path, confusion between the raw and canonical G.1b spec digests, the
single-node spec passed to the eight-node P3 check, an undefined server-seal binding, and missing
expansion routing in the gate-noise record. It also identified attempt and plan reuse before the
addendum binding checks.

The re-check verified the portable split citation and exact published note, distinct raw and
canonical G.1b digests against the four published engineering receipts, and the full base spec
at P3. Each TASL-2 job takes the main worker slot, both S13 CPU-set leases and its census lease
when distinct. CPU-only admission is scoped to the process and the declared node. Jobs, plans
and seals bind the addendum's spec, note and run. Audit planning and E5 verify the bound archive
digest before reusing an archive. The proposer seal and span also bind the addendum.

Assembly inherits the signed main note's readings, K and audit seeds. The release locks apply
before archive reads. MLGym additions reach the primary assembly and D6 gate-noise record via
the exact signed v2 row. Each 1GC node has its own descriptive output and stays outside the
primary assembly and gate-noise record.

The independent reviewer ran `r1/tests/test_t1_g5_addendum.py` and `r1/tests/test_t1_g5_seal.py`
with `COPYFILE_DISABLE=1`, a fresh `TMPDIR`, `PYTHONDONTWRITEBYTECODE=1` and `-q -p no:cacheprovider -rf`.
All 67 tests passed. `git diff --check` passed. No remaining findings for the reviewed code and
template. The review used public engineering metadata and synthetic fixtures. Per-node fill,
authorization, launch and release still follow their own signed and reviewed checks.
