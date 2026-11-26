# M11 three reader guards: integration review

**ACCEPTED only for the integrated generic-reader scope**, source HEAD `78d4697fbb747cbda45341fa56a0e27d6d90dfde`. This is not D8 gate acceptance, comprehensive reader coverage, permission to read sweep-2 labels or a B1 production change. No host, real sealed material, model, GPU or network was accessed.

The integrated `registry.py`, `model.py` and `spike.py` blobs are byte-identical respectively to the separately reviewed `703e7a5`, `2ac25aa` and `2b59eac` candidates. The integration carries their three scoped independent reviews; no five author-held M3 files were changed in the integration. The registry download guard checks target and existing entries before Hub use with disclosed symlink behavior, while the other two place sealed guards before the respective hash and metrics reads. Hardlink, concurrent path replacement and other reader limitations remain.

Independent combined synthetic test run in a fresh isolated checkout and unique pytest basetemp returned **20 passed**. Model-hash and spike tests execute exact function ASTs because torch is unavailable; full module import, wrapper and model/trainer paths are not covered. This preserves the prior acceptance boundaries rather than claiming a complete D8 or universal sealed-reader solution.
