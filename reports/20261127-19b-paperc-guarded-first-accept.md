# local/20261127-19(b) — guarded first acceptance

for: coordinator

- Base `840ad01df1c517f023c3dc14c32ec7ae2429a109`. Delivery
  `mac-paperc-guarded-first-accept-20261127` @ `008895a4ba08471e20ebfb3b125d1d516e5f17c0`.
- Independent **ACCEPTED for pre-signature handoff** at `d6ac990dc449dad9262a27260a760b5a30a0b4cf`.
  Review SHA-256 `06ec30c48ecb800ac3b32d6e92657305438366e5d22467cfcbaccb65f49d68e3`.
  A synthetic replay through the actual `a3fedbbd` harness charged two candidate runs,
  one separate start evaluation and three proposer calls. It discarded the worse first
  candidate and preserved the start through a precheck before keeping the later improvement.
- Proposed pre-declaration and runbook SHA-256 `6e378e80962b6569f4399a9434864420db0ac3b0aa3955c68286e83e0020cfc2`. Launcher SHA-256 `28d40a769b8bcb7def9997d2789eb0918f18af9b3e8afcda78b877e64f6dd658`.
  Proposed twelve worker seeds are 62,000–62,011 and the paired fresh audit block
  is 10,901,000–10,901,119.
- Tests: 7 focused tests passed in the local Python 3.12 torch environment. The paper-side R1 test and implementation paths are byte-identical to base.
- Next: author decision on the Track X pick, thinking off, the 20-worker/80-call bounds plus
  the separate start measurement, and the registry extension. Then bind the actual
  proposer server and runtime, exact spec and sealed output location and sign the note.
  The two CPU measurements precede R1-PAPERC-CORE.

Decided alone: use the published harness's initial-incumbent parameter and account from
its normal proposal events. The proposed budgets and seed extension await the author.
No real proposer call or worker job was submitted.
