# local/20261127-23 — screening: make the declared data cache stable under fetch_openml (second STOP)

Owner: local. Base: `main` `ab32029e`. STOP record: `docs/r1/reports/` from `compute-screen-measure-reissue-stop-20261127` (on `main`).
The `data-cache` step stores the OpenML download as `data/v1/download/52350.gz`; at load, scikit-learn 1.8.0's `fetch_openml(data_id=15,
as_frame=True, parser="auto")` writes `data/v1/download/52350/breast-w.arff.gz` (same bytes). The node copy's tree then gains a file, and the
integrity check (M1) STOPs. Fix it as a reviewed unit (tier E): build each node's cache in the exact layout `fetch_openml` reads and writes
at load (for example by loading once through the pinned code path after the download, and verifying that a second load writes nothing), so that
the declared tree is a fixed point. Keep the M1 check as strict as it is. **Explain why the 27 Nov engineering smoke (same code and cache,
168/168) did not stop on `openml_breast_w c3`.** If the smoke path differs from the evidence path, close the gap, because the smoke must
exercise what the evidence run does. Then: the new `code_commit`, a rebuilt cache with its new tree hash (compute), and a repeated engineering
smoke. The note needs a second re-issue for the new `code_commit` and `data_cache_sha256`; that goes to the author.
