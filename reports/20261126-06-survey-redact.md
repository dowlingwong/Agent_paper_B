# Report — resource survey redaction (`compute/20261126-11`)

**Result: PASS.** One new commit on the survey branch replaces every other user's name and the other project's
name; counts, memory, card numbers and PIDs are kept, and our own account `dwong` is kept.

- **Branch:** `compute-resource-survey-20261126`
- **New tip:** `f60a22258f63d158d25c1654c4c262c9e79fc06e` (one commit on top of `19396b62`)
- **Redacted report:** `docs/r1/reports/COMPUTE_RESOURCE_SURVEY_20261126.md` sha256
  `b75bda429a0ad031453359a7baa3639d99d92ace98f386980510f89ab1456d99`
- **Redacted captures:** `docs/r1/reports/COMPUTE_RESOURCE_SURVEY_20261126_captures/`

| Capture | New sha256 |
|---|---|
| `deepthought.txt` | `d9a79362c32a3adadb79e2b42851e0152bee56f69cd3adff2c459173a83dcbeb` |
| `deepthought2.txt` | `e2ef1bb47303c13fddd02b53ba5c08b1f06a43f86701e0b1c362928d9e206ad9` |
| `TASL-2.txt` | `2e52f719a8aa980375d33f1a9007d8381d29f7e90be2324f356a704ea2675b9a` |
| `TASL-7.txt` | `9bf2d62f6c814b266e2f1cfa634a3bc9b3494c7215d96bb2f931cd1284d8a9f1` (unchanged) |
| `Ada.txt` | `8018af70c035817a5625e8aeedf16ccf801394e055c8298ac5ee89b532dd16c9` |
| `ada_gemma4_31b_bench.txt` | `9ea8f8953ccfe5bd0203b46309afb84ad2fd8d853dc622fc0e368f87d5264921` |

**What changed:** each other user is `other user A`–`other user I`, consistently in the report and every capture;
the other project name is replaced by `our non-Paper-B project`; the `who` addresses are omitted. The mapping is not recorded in this
public branch. No count, memory value, card index, driver, PIDs or timestamp changed; no evidence value changed.
`dwong` (our account) and our own paths are unchanged.

**Check:** `grep` over the report and all captures finds none of the original names, the project string or the
connection addresses. The 26 Nov (g) acknowledgment in the earlier compute report remains valid; this unit only
redacts.

**What happens next:** the coordinator merges the branch (tier D); the findings (Ada LLM serving ready; P.4 training
not ready; TASL-7 card free) are already used in the placement proposal. No code or test run is involved.
