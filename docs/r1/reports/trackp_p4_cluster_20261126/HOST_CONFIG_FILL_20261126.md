# T3 — host-config fill commit (26 November 2026)

Made with **only** `r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py` on the checkout of `f1f1b651`; every one of
the 19 `TODO_VERIFY_ON_HOST` values was supplied from `host_fill.json` (schema `trackp_p4_host_fill/1`), with no
manual edit of the config. The script reported `"filled": 19`, `"placeholders_left": []`, and all four arms' local
paths under `job_dir/models/<registry key>`.

| Item | Value |
|---|---|
| previous host-config sha256 | `18f18cfc74d9a6b7aaf31124623883da513967dd8258e4339ef264d7e47e4140` |
| **new host-config sha256** | **`4b4a1233301cbc354e2112f33a89db08e6ff97c94452ffddbed8744948254af0`** |
| host_fill.json sha256 | `481e94d780f01820b5e0f7722b81fce100de9d6c9e8f92b63f2238fbd08a4177` |
| filled placeholders | 19 / 19; none left |
| values chosen | `work_dir="."`, `gpu.lock_path="gpu0.lock"`, unused bases `models/<base>`, `venv.causal_conv1d` names 1.7.0 + R1-TRACKP-IMAGE-V22-B |
| forced values | H200, compute_capability 9.0, `/opt/r1/envs/trackp`, `hf`, `models`, `out`, P.4 arm paths (script-enforced) |

T3 checks (v2.2 image env3, no GPU):

- `trackp.py --config r1/scripts/configs/trackp_htcondor_v2.json --check-config` → rc 0, `"placeholders": []`
  (`T3_check_config.json`; the printed `config_digest` is `e507642a…`, distinct from the file sha256).
- `sha256sum` of the file = `4b4a1233…` (`T3_host_config_sha256.txt`).
- `p4_lib.check_local_paths` for all four arms → `/nonexistent/condor/execute/dir_0/models/<key>` with no STOP
  (`T3_local_paths.json`).

Diff: only `r1/scripts/configs/trackp_htcondor_v2.json`, 19 replacements / 19 deletions, plus this record and
`host_fill.json`. Tests were not edited (F5 is already on main). Independent review pending on this branch; the
coordinating chat publishes it so `paper.commit` can include it.
