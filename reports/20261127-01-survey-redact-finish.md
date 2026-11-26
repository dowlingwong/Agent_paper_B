# Report — survey redaction finished (`compute/20261127-02` item 2)

**Task:** `compute/20261127-02` item 2, completing `compute/20261126-11` on `compute-resource-survey-20261126`.
**Result: PASS.** The truncated `top` USER column in `Ada.txt` is replaced by the same label the report uses; every
capture was re-scanned for the original names and their prefixes; the report's hash table is updated.

- **Branch:** `compute-resource-survey-20261126`
- **Previous tip:** `f60a22258f63d158d25c1654c4c262c9e79fc06e`
- **New tip:** `58e6bbebb0f91913c857825be1861cd6a282d17d`
- **Report:** `docs/r1/reports/COMPUTE_RESOURCE_SURVEY_20261126.md` sha256
  `5762e3e4dbb4b958f014b2388389cc4f266a742a064b5836c9364d1662d22416`
- **`Ada.txt`:** sha256 `aaa2a20ec497605ac7e415d6b5144a86b4c0607f72f35ab4ed87f7865478bf1f` (was
  `8018af70c035817a5625e8aeedf16ccf801394e055c8298ac5ee89b532dd16c9`)

## What changed

`docs/r1/reports/COMPUTE_RESOURCE_SURVEY_20261126_captures/Ada.txt` lines 49–62 held `vla-rea+` in the `top` USER
column, a prefix of the name already labelled `other user D` elsewhere in the file. It is now `other user D`.
Counts, PIDs, memory values, card indices, timestamps and the other five captures are unchanged. Re-scan for the
original names and their prefixes (`vla`, `reason`, `jiachen`, `amons`, `friem`, `lbogn`, `zihao`, `myan`, `zli5`,
`zhixu`) over the report and all captures found none outside the `other user A`–`I` labels.

The report's redaction paragraph now records this second pass, and its hash table carries the new `Ada.txt` hash.

## Other hashes (unchanged)

| Capture | sha256 |
|---|---|
| `deepthought.txt` | `d9a79362c32a3adadb79e2b42851e0152bee56f69cd3adff2c459173a83dcbeb` |
| `deepthought2.txt` | `e2ef1bb47303c13fddd02b53ba5c08b1f06a43f86701e0b1c362928d9e206ad9` |
| `TASL-2.txt` | `2e52f719a8aa980375d33f1a9007d8381d29f7e90be2324f356a704ea2675b9a` |
| `TASL-7.txt` | `9bf2d62f6c814b266e2f1cfa634a3bc9b3494c7215d96bb2f931cd1284d8a9f1` |
| `ada_gemma4_31b_bench.txt` | `9ea8f8953ccfe5bd0203b46309afb84ad2fd8d853dc622fc0e368f87d5264921` |

## Tests and scope

Docs-only: no code, spec, pin, data, label or evaluation file changed; no host command, job or GPU use. The scan
was a local `grep` over the committed files.

**Decided alone:** to keep the same `other user D` label rather than introduce a new letter, since the same
processes appear under that label elsewhere in `Ada.txt`; to add one sentence to the report so the second pass is
visible. No mapping or original name is recorded in the public branch.

**Needs:** the coordinator merges the branch (tier D). Nothing else.
