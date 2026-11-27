# local/20261127-09 — G.5 sd-matched assembly accepted; authorization rendered as a draft

for: coordinator

- Assembly branch `mac-g5-sd-assembly-20261127` @ `82a22977cf98e01783ba00e2b93ec2e74779f6e8`. Started from the previous unit at `b9bc00fc`; comparison base and assembly merge base `6aee0eb34a9c8bae4c9c24d93b261d24a76a8403`. Independent tier-E **ACCEPTED** at code commit `70a69347`; the review is `docs/r1/reviews/G5_SD_ASSEMBLY_REVIEW_20261127.md`.
- Draft render branch `mac-g5-sd-render-20261127` @ `bc968b3e945f2cd9c0db3056145facceaae0dc58`, based on the exact assembly tip. A separate reviewer **ACCEPTED for conditional draft handoff**. See `docs/r1/reviews/G5_SD_DRAFT_RENDER_REVIEW_20261127.md`. Final publication requires the checks below.

## Assembly verification

Student-t uses scale `s * sqrt((nu - 2) / nu)` and retains sd `s`. Synthetic tests compare the integrated bin masses with the Student-t reference, check sd matching and unchanged Gaussian output, reconstruct Student-t targets from assembled parameters, and exercise complete round-tripping degrees-of-freedom tokens. The focused run was 284 passed and one inherited TASL-only path failure on Mac; the final parser re-check passed both focused tests.

Full `r1/tests` under `hupdate`, with clean harness pin `a3fedbbd`, `COPYFILE_DISABLE=1`, fresh short `TMPDIR` and no LightGBM. Command `python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.

| Checkout | Failed | Passed | Skipped | Errors |
|---|---:|---:|---:|---:|
| Base `6aee0eb3` | 76 | 4,840 | 162 | 3 |
| Assembly `82a22977` | 76 | 4,859 | 162 | 3 |

The 79 unique failed/error test IDs are identical. The complete sorted ID list, retaining spaces in two parameter IDs, has SHA-256 `1f8ae808ccf8ae3cd17503991f7d23a16055c77f55af01e33f74558ac7599256`.

## Render and next action

- Spec `sweep2/t1_tasl/g5_tasl_spec.json` SHA-256 `85c2f6208cf4e6f7b5395658f47fba1a2c212331d168585178807fdae36fc2c7`.
- Draft `docs/r1/authorizations/c3_t1_labels_20261127.md` SHA-256 `2b972f50138820fb131e7260f14a4520fb8742e2af3e6c642792899208189702`.
- The corrected published REL-T1-G1B copy review SHA-256 is `b067c35c929d841f9f98f20c98aa22322e1235f9d1c65d529d22c8ce089fec0a`. P10 is PASS from that copy and R1-G5-TAILS. `mlab_ogbn_arxiv` and `mlgym_breakout_minatar` use Student-t, ν = 5. `mlab_cifar10`, `mlab_imdb`, `mlgym_cifar10`, `mlgym_fmnist` and `mlgym_houseprice` use Gaussian. Autoresearch uses its completion record.

`python sweep2/t1_tasl/g5_tasl.py check-note sweep2/t1_tasl/g5_tasl_spec.json --note docs/r1/authorizations/c3_t1_labels_20261127.md --draft` returns the expected STOP solely for `['P11', 'paper_commit']`. This handoff retains `approved: false`.

Merge the accepted assembly unit independently. Finalize the draft after the combined P11 evidence under R1-G5-P11, including TASL-2 C2/C4/C5/C6/C9/C14/C15 pre-run, C11 chunk side, C7 audit context, C15 seal/close/span and job-start noise, and short-span restart handling. Fill the exact final launch-code `paper.commit`, rerender and bind the updated spec, pass the draft check, and get the final independent review. The coordinator publishes the bound note and spec and runs the strict check. Houseprice retains the separate S14 node guard. The downstream consumers and preregistration amendment are a separate unit under R1-G5-TAILS-CONSUMERS (3).

Decided alone: validated the render as a conditional draft on a separate branch so its unfinished binding does not enter the assembly merge. No real labels, evaluation files or new jobs were opened or launched for either unit.
