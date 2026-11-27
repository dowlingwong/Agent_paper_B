# local/20261127-20 — E-INT development census desk preparation

for: coordinator

- Base `840ad01df1c517f023c3dc14c32ec7ae2429a109`. Delivery
  `mac-paperc-eint-census-prep-20261127` @ `a9057712d9096971d1ef67f771a4f1f98b7de895`.
- Independent **ACCEPTED for desk preparation** at `36bfbbc3`. Review SHA-256
  `1d766c90be5a21e748bbcc28d4349dfaddd4968ae3a4bc0139f4341d75d28310`. The reviewer
  verified packed/unpacked equality and accounting in synthetic CPU cases, including a real
  tiny decoder update and the common evaluator. Mixed-phase, mismatched and non-finite
  receipts refuse.
- Runbook SHA-256 `cc01c3703ba15f4219b68c71d05360cd4a8fd1b9793e63c1c8853fb448c042f7`, batching/data module `621fe4c3d11acb30beae3c4827b3c1b96126bdb8dc03b73e9d100861fbaa82e1`, cell driver `ea55dae94685982396f6e1bf6e686e29f5b3fa2901100e727eceda946735f722`.
  The data manifest is `ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`.
- Tests: 4 focused tests passed in the local Python 3.12 torch environment. The paper-side R1 test and implementation paths are byte-identical to base.
- Next: a separate signed launch card binds the empty GPU lease, the allocator cap and
  smoke budget. The smoke checks baseline repeatability, the allocator and process-memory
  sensor, identical validation targets and receipt completeness. The census stays pending.

Decided alone: reuse the pinned raw ClimbMix documents and tokenizer with a new
boundary-safe loader and one common 512-token development evaluator. The comparison uses
a measurable allocator cap and reports sampled device-process memory separately. No GPU
or evidence job was submitted.
