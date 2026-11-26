# Run I environment record — T0 arms A3

- Separate venv: `/work/dwong/arms_t0_20261123/venv` (base CPython 3.13.15, `/ceph/dwong/r1_prepare_20261025/python/cpython-3.13.15-linux-x86_64-gnu/bin/python3.13`).
- Exact versions: Python **3.13.15**, NumPy **2.4.4**, SciPy **1.17.1**, scikit-learn **1.8.0**, LightGBM **4.7.0**.
- `pip freeze` (8 lines) sha256: **e536366970176cddbc297b23bcf13601f39a55bac4695b1f9fabe23f66d685a5**; copy: `ENVIRONMENT_pip_freeze.txt`.
- The shared B.2/audit venv `/ceph/dwong/r1_prepare_20261025/venv` was **not** modified; this venv is separate.
- Thread environment for every command: OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=1; PYTHONDONTWRITEBYTECODE=1.
- All A3 entries record `toolchain` python 3.13.15 / numpy 2.4.4 / lightgbm 4.7.0.
