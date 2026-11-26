# Run I — T0 arms A3 (23 November 2026)


Code commit C: paper
Code commit C: 89899f765fc4134c05897bf079ced3ecb95314f2
Clean checkout at start: tracked changes = 0
Author row: R1-ARMS-DECISIONS (FEAT-ONE A, ARMS-CAL A, ARMS-LEFTOUT A, ARMS-HP A, ARMS-WDBC A, ARMS-TWIN B, ARMS-T1FEAT A).
A3 settings typed: --calibration temperature --twin-weight mode_group; --folds; --primary-t0 seven; T0-only (no T1 labels used; --t1 omitted).

## Environment
Separate venv: /work/dwong/arms_t0_20261123/venv
python / numpy / scipy / scikit-learn / lightgbm: 3.13.15 / 2.4.4 / 1.17.1 / 1.8.0 / 4.7.0
pip freeze sha256: e536366970176cddbc297b23bcf13601f39a55bac4695b1f9fabe23f66d685a5 (8 lines; copy ENVIRONMENT_pip_freeze.txt)
The shared B.2/audit venv /ceph/dwong/r1_prepare_20261025/venv was not modified.

## Commands and results
1. FEAT-ONE identity: python -B -m r1.c3.arms_freeze identity --sealed /ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table --arms-table /work/dwong/htcondor_prep_20261114/w2_3_rebuild_20261115/tables/c3_features_v3_20261115T232007Z --out /work/dwong/arms_t0_20261123/feat_one_identity.json; exit 0; pass=true, n_sealed=4999, n_budget_frac_left_differ=116, n_other_differences=0, keys_equal=true, configs_equal=true; sha256: 039b8360e293f44632e6a55bff79d32f2b4769045c112cfa4d54a596564853df
2. A3 train/select/calibrate: python -B -m r1.c3.arms_freeze train-a3 --release-root sweep1=/work/dwong/s2_release_20261123/release_sweep1_traindev --receipt sweep1=f06e37a95266aa3267f978dd1d471722f418c1b6b34f6212df6dfd2b7eb665c1 --table sweep1=/work/dwong/htcondor_prep_20261114/w2_3_rebuild_20261115/tables/c3_features_v3_20261115T232007Z --release-root sweep2=/work/dwong/s2_release_20261122/release_sweep2_traindev_v2 --receipt sweep2=de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c --table sweep2=/work/dwong/s2_audit_20261122/table --identity /work/dwong/arms_t0_20261123/feat_one_identity.json --calibration temperature --twin-weight mode_group --folds --primary-t0 seven --artefact-root /ceph/srv/dwong/paperb --out /ceph/srv/dwong/paperb/arms_t0_20261123/a3; exit 0.

## A3 entries (8: primary + 7 LONO; all PRE-SELECT chose sweep2_only)
- A3: role=primary, n_predictions=5012, choice=sweep2_only, dev_values={'pooled': 0.17915879053806394, 'sweep2_only': 0.21724638906097313}, calibration=temperature, twin_weight=mode_group
- A3@lono:digits_mlp: role=fold, n_predictions=684, choice=sweep2_only, dev_values={'pooled': 0.1777442969801388, 'sweep2_only': 0.22299573030571587}, calibration=temperature, twin_weight=mode_group
- A3@lono:openml_breast_w: role=fold, n_predictions=596, choice=sweep2_only, dev_values={'pooled': 0.18720380754917823, 'sweep2_only': 0.24788928505111782}, calibration=temperature, twin_weight=mode_group
- A3@lono:openml_climate: role=fold, n_predictions=600, choice=sweep2_only, dev_values={'pooled': 0.25113534589215, 'sweep2_only': 0.3086349931850239}, calibration=temperature, twin_weight=mode_group
- A3@lono:openml_credit_approval: role=fold, n_predictions=585, choice=sweep2_only, dev_values={'pooled': 0.12999524499530293, 'sweep2_only': 0.16151905449523557}, calibration=temperature, twin_weight=mode_group
- A3@lono:openml_ionosphere: role=fold, n_predictions=610, choice=sweep2_only, dev_values={'pooled': 0.17746985803309284, 'sweep2_only': 0.2354700184381216}, calibration=temperature, twin_weight=mode_group
- A3@lono:openml_sonar: role=fold, n_predictions=637, choice=sweep2_only, dev_values={'pooled': 0.20363322814585416, 'sweep2_only': 0.24303888107019236}, calibration=temperature, twin_weight=mode_group
- A3@lono:tabular_mlp: role=fold, n_predictions=684, choice=sweep2_only, dev_values={'pooled': 0.19697741340182828, 'sweep2_only': 0.21701514465828844}, calibration=temperature, twin_weight=mode_group
total predictions 9408

## Sealed artefact files
- a3/entries.json sha256: 9e0efcd7598d31e1f68c365af26e0eae6132615580732370da05091e9f69d058
- a3/A3/model.txt sha256: c38e64ea2e6c0ea53b749c94f39348bf8b0d05571234e5470d4683c00314eb5d
- a3/A3/predictions.json sha256: 9fa2889401f1d6180f4ed3ae33966dd25e88256b9ba66ff93766ec163dbcd95a
- a3/A3/selection.json sha256: e56d4c5fa0de518a226ce348b1e52a95349e53cdc3c3c0376ceaafa65f452710

A3 only was produced; no A5 entries, no arms-frozen record, no test label or evaluation value was read.
