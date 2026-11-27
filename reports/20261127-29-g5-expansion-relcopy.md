# local/20261127-29 — expansion REL-T1-G1B copy for D6

for: compute

The four G.5 expansion addenda need the reviewed D6 engineering noise-floor copy under R1-T1-FEAT-DECISIONS and
R1-G5-S9. `main` at `cbc86fc5b628ed328b1889f42e7b4e0235c004f3` has the accepted expansion G.1b result, summary,
assembly and all four seals. The expansion REL-T1-G1B copy record and authorized `runs.jsonl` copy are pending. The four nodes share one
assembly and one source digest. The published result files give expected bytes for the reviewed copy of all three files.

- Source run `g1b-x-tasl-20261126-a` on TASL-2. The exact assembly directory from the accepted review trail is
  `/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a/`.
- Check for an existing REL-T1-G1B copy and check the ledger before acting. Preserve the assembly and all four
  original seals. Use the existing assembly and seals as the sole source. The exact assembled file has **1,840** G.1b rows, 460 per node. A single
  byte-identical copy can serve all four addenda. Bind each node to its own already published seal and result.
- Expected `summary.json` digest `67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10`.
  Expected `ASSEMBLY.json` digest `b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077`.
  Expected `runs.jsonl` digest `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7`.
  Each assembly job binds the signed expansion spec file digest
  `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238`.
- Prepare the copy and independently reviewed source-to-copy record on a dedicated branch for coordinator publication.
  Report the three paths and hashes together and identify the node receipt bindings. The existing `g5_relcopy.py`
  handles the seven-node and autoresearch schemas. The expansion copy needs a reviewed schema-aware check.
  This handoff covers only G.1b engineering output under D6. It requires no training job or sealed G.5 partition read.

The Local switch and drafts stay pending on their separate publication and binding checks. The ordinary Compute
queue and its job IDs are in the accompanying Local task report.

[Draft branch, checks and STOP report](20261127-29-g5-expansion-addenda-stop.md).
