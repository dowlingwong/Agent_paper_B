# M13 template-order inventory — 5 November 2026

AI-assisted (Codex). Read-only source and previously retained artifact inspection at paper checkout `c2e04788d35bcac6b79c3a6820cb64cea01315f3`; no server, model, GPU or experiment. This inventory is not acceptance of M13 or evidence that the preserved P.3a attempt used a particular template.

## Current local implementation

`r1/c3/train/types.py:26` defines `PROMPT_VERSION = "trackp_prompt/v1"`. In `serialize.py:125–133`, the neutral text rendering places `state` (which includes the oldest-first history) before the proposal, question and options. `serialize.py:198–205` sets this version in the metadata of prompts made by `serialize_view`; it does not prove that each saved P.3a result includes that metadata.

The actual family wrappers are not all the same order:

| Local wrapper | Source evidence | Observed local composition |
|---|---|---|
| Kev `PointerWrapper` | `r1/c3/train/model.py:294–315` | A record contains `p.state` and a question instruction containing `p.proposal` followed by `p.question`; it passes that record to the external Kev encoder. Its final encoded token stream has not been independently inspected in this inventory. |
| Qwen `BinTokenWrapper` | `r1/c3/train/model.py:642–662` | Prefix: state (including history), proposed edit, question, optional bins; then `Belief:` and `Action:`. The code does not place the proposal literally immediately before a `<decide>` token. |
| Laya `LayaWrapper` | `r1/c3/train/model.py:394–400` | `state_text` explicitly places the proposed edit before the loop state; the comment gives end-truncation as the reason. This wrapper was removed from the current four-base P.3a pool, but shows that the shared version string does not by itself imply a universal wrapper-level order. |
| StartLux `StartLuxWrapper` | `r1/c3/train/model.py:549–556` | The submitted input string puts state before the proposed edit; the family's own framing is built subsequently. StartLux was removed from the current four-base P.3a pool. |

R1-BX-REVISIONS (d) in `docs/r1/PLAN.md` and `docs/r1/TRACK_P_POST_TRAINING.md:88–90` specify history before proposal and an E6 A6 comparison. Order and family framing must be checked separately; calling all `trackp_prompt/v1` renderings proposal-first or history-first would be inaccurate.

## Preserved E0 data and attempt 1

The local E0 file `r1/c3/train/data/e0_v1.jsonl.gz` hashes to `4f4db29b6a4c0ca0181825e5c2c0fb031521e034a006990b93686cd5fffc8290`, matching the prefix in `docs/r1/RUNBOOK.md:87`. All 4,000 local rows identify their **dataset** version as `trackp_e0/v1`, and store `state` and `proposal` separately; their prompt dictionaries have `group`, `options`, `proposal`, `question` and `state` and no `prompt_version`. `r1/c3/train/exam_synthetic.py:181–199,214` shows the separation and dataset-version field. The dataset label is not a recorded serializer or wrapper version, and does not determine actual model token order.

**NOT CHECKABLE locally: the paper commit and serialization used by P.3a attempt 1 as launched.** `docs/r1/RUNBOOK.md:87` says that commit is recorded in the per-run TASL-7 manifests but is `TODO_VERIFY` in committed material. The independently recorded OOM diagnosis `docs/r1/reviews/TRACKP_P3A_OOM_DIAGNOSIS_20261031.md:7–8` cites incident-time TASL-7 checkout `b9ad6f8fe2e771732100f704accd7f2ce7cf20f0` for the examined probe paths. That is useful context, but it is not a per-run launch-manifest verification of the entire preserved attempt. That Git object is not available in this local checkout. The committed `docs/r1/reports/trackp_p3a_dryrun_20261026/kev-0.8b_soft/manifest.json` records an earlier **DRYRUN**, not attempt 1, so it cannot resolve the evidence-run pin.

**Unblock:** an authorized TASL-7 operator supplies the exact preserved attempt-1 per-run manifest bytes and their hash, including the clean paper commit and model family; a local reviewer inspects that commit's serializer, wrapper and exact Kev encoder version/framing, and compares any prompt-version fields actually recorded. **Owner:** site operator for read-only receiving, Mac implementer and independent reviewer. **Effort:** a bounded manifest and source inspection after access; elapsed time depends on operator availability and retained records. P.3a remains STOP; no run, restart or relabel is authorized by this inventory.
