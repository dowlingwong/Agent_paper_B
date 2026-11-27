"""G.5 T1 label runs on the TASL pair: the spec validator and the G.5 switch (G.5 code unit, part 3a).

EVIDENCE table. This module validates ``g5_tasl_spec.json``, checks the signed note line by line, and gates every G.5
job start; its runner is ``g5_job.run_job`` (part 3b-1: the campaign waves, audit chunks, diagnostics and STOP
counters), reached only after every check below. The seal step (``g5_seal``), the locked assembly
(``g5_assemble``) and the REL-T1-G1B copy step (``g5_relcopy``) are part 3b-2, on this CLI behind the same gates
(the spec validated for launch and the import-source check; the copy step, which comes before the signature, validates
the spec without launch). AI-assisted (Claude). Authority: the G.5 authorization draft revision 8
(``docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md``, accepted in round 4 of
``docs/r1/reviews/T1_G5_DRAFT_TASL_REVIEW_20261122.md``), §2, §4, §5, §7, §9, §11.

* **Decisions (§11).** Every open decision is an explicit field ``decisions.<id>.option`` with the recommended option A
  as default and ``signed: false``. ``apply_options`` switches an option and sets the fields it governs; the validator
  checks each field against the option. What each non-default option changes, or why it is refused:
  - G5-W B: ``campaign.W_semantics`` ``worker_runs`` with ``llm_call_cap`` 80, audited band 150-240. Launch refused:
    the v2-diff engine has no worker-run budget (harness work) and the G.4b re-pilot ran W = 20 manager calls (P3).
  - G5-TEMP B: temperature 0.0. Launch refused unless the pilot spec P3 reads (``g4b_tasl_spec.json``'s ``pilot``
    block, R1-G5-DIFF-RECOUNT) ran at 0, i.e. a re-issued G.4b spec bound by its sha256 in ``pilot_basis.spec``.
  - G5-MEM B: modes ``history`` and ``none``, 12 instances each, audited band doubled. Launch refused unless
    the G.4b pilot spec ran both modes (P3). G5-MEM A needs ``e4_amendment_row`` (it amends E4's "both
    memory modes"). G5-MEM C is refused (not built): the draft gives no assignment of the split file's 12 instances
    to two modes of 6, and C contradicts R1-BX-D8-V3-B's 12 instances per node.
  - G5-AUDIT B: audit scope ``ok`` outcomes only (G5-DIV's denominator is then weaker; reported). ``reuse_parent_runs``
    may be false under either option (§2.4); E5 on any seed block other than the label seeds is refused (it would need
    a row amending R1-B2-DECOUPLE).
  - G5-DIV B and C: per-node thresholds from inputs the spec carries (the pilot's divergent counts; the G.1b
    divergent-row rates), required at launch; ``divergence_threshold`` computes them.
  - G5-TASL-GPUH B: both cards count; needs ``proposer.server_stopped_during_audits`` true and the projection plus the
    campaign hours within the cap.
  - G5-SLOT B: refused (not built, §2.10). R1-G5-AUDIT-TWO-CARDS amends G5-SLOT A instead: campaign waves keep one
    worker slot on TASL-2 (``slots.worker_slots`` 1), and audit chunks may also run on TASL-7 (``slots.audit_hosts``,
    the spec's ``tasl7_audits`` block; see "TASL-7 audit chunks" below).
  - G5-ARPEND A: autoresearch's noise-floor copy, environment, P10 declaration and host check are PENDING markers in
    the spec; the switch reads them from the one completion record on published main (STOP 15). B: the spec carries
    them, filled at signature.
  Any option other than the recommended row needs the cap of its row: the validator refuses a cap below the
  pre-pilot projection at ran share 0.6 (K = 10) under the chosen options. That is a floor only; the cap the draft
  sizes (share 0.8 plus 10 %) is carried by the P7 recompute and the signature.
* **Key values (§5).** ``note_lines`` renders every key line of the note from the spec, with K (P4) and the
  freeze-wait date (STOP 14) read from the note: both can move by a docs-only amendment citing an author row on main.
  ``check_note`` requires each line verbatim, the binding fields (``paper_commit``, ``spec_sha256``), P1-P11 PASS, and
  the reviews P5 and P8 cite on main with ``Verdict: ACCEPTED``.
* **The switch** (``launch``): off by default, both keys (``--enable`` and ``G5_TASL_ENABLE_REAL=1``); then the note,
  the decisions row (and the E4 row under G5-MEM A), R1-T1-FEAT-DECISIONS (``T1_FEAT_TERMS``), the TASL-2 host
  check, the C12 record on main under ``cuda_ipc: c12`` (P1), the seven-node REL-T1-G1B copy with its cross-check
  gate record and the copies of its run's ``ASSEMBLY.json`` and ``runs.jsonl`` (D6 A of R1-T1-FEAT-DECISIONS;
  reviewed, by sha256), and for autoresearch its completion record (STOP 15) or, under G5-ARPEND B, the spec's
  items, then ``g1b_tasl_join.noise_floor_by_node`` on the two copies; under R1-T1-D21-SCOPE a node without a G.1b
  fixed-seed determinism PASS is STOP 5, and a node that does not qualify under D21 is recorded (``context["d21"]``),
  not STOPped; the rows R1-T1-D21-SCOPE and R1-G5-AUDIT-TWO-CARDS on main; then the freeze wait (STOP 14), ``g5_pin_check`` on the two G.5 commits (STOP 13), the node's family checkout at its G.5
  commit and clean, the per-family measurement-path identity against the G.1b pin (P5; no file may be added under
  ``nodes/``, ``third_party/``, ``configs/trackg/`` or ``node_lib/``, and in trackg only the declared G.5 files), and
  the TASL launch binding (``g1b_tasl.verify_launch_tasl`` after the import-source check; LB A).
* **TASL-7 audit chunks** (R1-G5-AUDIT-TWO-CARDS). ``launch(..., host="TASL-7", chunk=i)``: audit jobs only, the
  G5-7 family only (autoresearch's audits stay on TASL-2, where ar-cond7a exists), the TASL-7 host check record on
  main (also cited in the note's P1 and ``tasl7_audits`` line), and the node's cross-host PASS
  (``check_crosshost_pass``): the xc2 step-1 and step-2 verdicts for the three TASL-7 G.1b nodes, bound by sha256 in
  the spec; for the other four, their xc3 short verdicts (all PASS on main since cdb8be91), bound by sha256 in the
  spec since revision 13 and read on main at each TASL-7 job start together with XC3-FAIL, ``skip_nodes`` and the
  rule that the listed file is the node's one short verdict on main. The marker ``PENDING short cross-check: <node>``
  stays accepted: the switch then finds the PASS on main by its file pattern (none: that node's TASL-7 chunk is
  refused; its TASL-2 jobs and the launch are not affected). The job side (claim on TASL-2, lease, server down, GPU model, registration)
  is ``g5_job``'s. XC3-FAIL and ``skip_nodes`` are read by the xc3 unit's own rules, imported from
  ``g1b_crosscheck`` (``short_decisions``, ``xc3_fail_row_option``). Under ``cuda_ipc: c12`` a TASL-7 audit chunk
  also needs a C12 PASS record for TASL-7 (``c12_tasl7_record``); the acceptance line names both hosts.
* **TASL-2 CPU sets** (R1-TASL2-CPU). No TASL-2 set of the spec contains CPUs 8-11 (``_check_tasl2_cpus``): the
  worker's set may not, and a node whose G.1b set contains any of them (``mlgym_houseprice``, 8-15) runs its TASL-2
  jobs on the replacement in ``tasl2_cpus.replacements`` (same size; ``tasl2_node_cpus``, which the ``cpus`` query and
  ``g5_job``'s affinity check read). Before such a node's first TASL-2 job the switch requires the fixed-seed
  determinism record of that set on main (``check_cpuset_record``), written by ``cpuset-verdict`` from three sealed
  attempts of the node's G.1b default part on that set under ``cpuset-spec``'s derived spec, compared with the sealed
  G.1b TASL-2 attempt; the launch also needs the row R1-TASL2-CPU on main.
* **P3** (R1-G5-DIFF-RECOUNT) reads the G.4b re-pilot, not the G.4 pilot: what it ran from ``g4b_tasl_spec.json``'s
  ``pilot`` block (the file bound by path and sha256 in ``pilot_basis.spec``), so only a re-issued G.4b spec can clear
  a P3 blocker. ``pilot_basis`` also binds, from the committed G.4b result: the signed G.4b note, the result report and
  its corrigenda (each by path and sha256), each node's sealed attempt (receipt, job-record and pilot-summary sha256),
  the measured liveness, the dates row (R1-BX-D14-G4B, G4B-DATES A: the eight-node recompute) and that recompute
  (``dates --pilot-spec``). At every TASL-2 job start ``pilot_basis_check`` re-reads the sealed G.4b attempts and the
  files on main and recomputes the dates; P7 (``projection.gpu_hours_p7``) equals the recompute's
  ``g5_total_gpu_hours``. The G.4 pilot stays readable: ``dates`` without ``--pilot-spec`` reads its sealed attempts,
  and the proposer, environments and sealed root are still compared with the signed G.4 note's spec (G.4b's are the
  same).
* **Dates with TASL-7 audit chunks** (``dates --tasl7-audits``, R1-BX-D14-G4B's recompute): besides the one-slot
  recompute, a ``tasl7_audits`` block moves to TASL-7 only what R1-G5-AUDIT-TWO-CARDS and ``g5_job`` allow: audit
  chunks of the eligible nodes (``--tasl7-nodes``, default the G5-7 nodes whose PASS is on main), never a wave's first
  chunk (the TASL-2 job that makes the wave's plan takes it) or its last (E5), and never while a campaign wave holds
  the server (TASL-7's lease); the GPU-hours stay inside the cap.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "g4"))
import g1b_tasl as G  # noqa: E402
import g4_tasl as T4  # noqa: E402
import g4_lib  # noqa: E402
import g5_pin_check as PC  # noqa: E402
import g1b_crosscheck as X  # noqa: E402
import g1b_tasl_join as J  # noqa: E402

L = G.L
Stop, NodeStop = G.Stop, G.NodeStop
SCHEMA = "g5_tasl_labels/v1"
EVIDENCE = "EVIDENCE"
GPU_MODEL = G.GPU_MODEL
ADA_MODEL = "NVIDIA RTX 6000 Ada Generation"
WORKER_HOST, PROPOSER_HOST = "TASL-2", "TASL-7"
DRIVERS = {"worker": "535.309.01", "proposer": "580.178.04"}          # R1-T1-TASL-ENV
# R1-G5-AUDIT-TWO-CARDS (amends G5-SLOT A): G.5 audit chunks may also run on TASL-7's RTX 4090 while no campaign wave
# holds the server; a node's audits run there only after its cross-host check PASS. Campaign waves stay on TASL-2.
AUDIT_HOST = PROPOSER_HOST
JOB_HOSTS = (WORKER_HOST, AUDIT_HOST)
TWO_CARDS_ROW = "R1-G5-AUDIT-TWO-CARDS"
XC_PENDING = "PENDING short cross-check: {node}"      # the spec's marker until the node's short cross-check PASS exists
# R1-TASL2-CPU (26 Nov 2026 (b)): no R1 job on TASL-2 uses CPUs 8-11 (the two 6.1 GHz P-cores that failed the MetaMaze
# determinism stress 3/3). A CPU set of the spec that contains any of them gets a replacement of the same size that
# avoids them, and that set passes a fixed-seed determinism check before its first use (``check_cpuset_record``).
TASL2_CPU_ROW = "R1-TASL2-CPU"
TASL2_CPU_TERMS = ("no R1 job on TASL-2 uses CPUs 8-11", "passes a fixed-seed determinism check before its first use")
TASL2_EXCLUDED = (8, 9, 10, 11)
TASL2_NCPUS = 32                                                   # i9-14900KF: CPUs 0-31 (lscpu, stability record)
TASL2_STABILITY = "docs/r1/reports/tasl_chain_20261122/TASL2_CPU_STABILITY_20261125.md"
CPUSET_SCHEMA = "g5_tasl2_cpuset_check/1"
CPUSET_TOKEN = "G5_TASL2_CPUSET_CHECK_"
CPUSET_NAME = re.compile(r"^docs/r1/reports/[A-Za-z0-9_.\-]+/G5_TASL2_CPUSET_CHECK_(?P<node>[a-z0-9_]+)_\d{8}\.json$")
CPUSET_RUN = re.compile(r"^tasl2-cpuset-(?P<node>[a-z0-9_]+)-\d{8}$")
CPUSET_REPEATS = 3                                                 # sealed attempts, as the stability record's 3/3
# The expansion G.1b's TASL-2 CPU sets (R1-T1-NODE-EXPANSION; mac-g1b-expansion-20261126c: MetaMaze 0-3, Forest Cover
# 4-7, Titanic 12-15, ETTh1 16-31), each guarded there by a CPU-set lease ``~/r1_locks/cpus-<set>.lock``; its CPU jobs
# take no TASL-2 GPU lease. Used in the note's wording only (the operator's flock); G.5 code takes none of them.
EXPANSION_CPU_SETS = ("0-3", "4-7", "12-15", "16-31")
XC2_DIR = "docs/r1/reports/tasl_chain_20261122"
XC2_VERDICTS = {"xc": XC2_DIR + "/G1B_XC2_STEP1_VERDICT_{node}_20261122.json",
                "preassembly": XC2_DIR + "/G1B_XC2_STEP2_PREASSEMBLY_VERDICT_{node}_20261124.json"}
# R1-T1-D21-SCOPE: D21 does not select T1 nodes for C3. These verdict texts are g1b_lib.summarise's.
D21_SCOPE_ROW = "R1-T1-D21-SCOPE"
DETERMINISM_FAILED = "fixed-seed determinism failed"
# The switch requires both rows on published main (plan_row; literal terms of their text on 5d4f1b09's PLAN).
D21_SCOPE_TERMS = ("D21 does not select T1 nodes for C3", "no other threshold is introduced")
TWO_CARDS_TERMS = ("Amends G5-SLOT A", "while no campaign wave holds the server", "cross-host check PASS")
AR = "autoresearch_fixedtokens"
SEVEN = ("mlab_cifar10", "mlab_imdb", "mlab_ogbn_arxiv", "mlgym_cifar10", "mlgym_fmnist", "mlgym_breakout_minatar",
         "mlgym_houseprice")
T1_NODES = SEVEN + (AR,)
FAMILIES = {"G5-7": PC.PIN_SEVEN, "G5-AR": PC.PIN_AR}                  # G5-PIN B (R1-G5-DECISIONS)
FAMILY_SPECS = {"G5-7": "sweep2/t1_tasl/g1b_tasl_spec.json", "G5-AR": "sweep2/t1_tasl/g1b_tasl_ar_spec.json"}
DECISIONS = ("G5-W", "G5-TEMP", "G5-MEM", "G5-AUDIT", "G5-DIV", "G5-TASL-GPUH", "G5-SLOT", "G5-ARPEND")
OPTIONS = {"G5-W": ["A", "B"], "G5-TEMP": ["A", "B"], "G5-MEM": ["A", "B", "C"], "G5-AUDIT": ["A", "B"],
           "G5-DIV": ["A", "B", "C"], "G5-TASL-GPUH": ["A", "B"], "G5-SLOT": ["A", "B"], "G5-ARPEND": ["A", "B"]}
AR_PENDING = "PENDING: G5-ARPEND A (from the completion record docs/r1/reports/*/G5_AR_PREREQUISITES_YYYYMMDD.md)"
AR_FILL_B = "TODO: G5-ARPEND B (filled at signature)"
TAILS = ("gaussian", "student_t")       # P10 (E5); = r1.c3.labels.TAIL_LAWS (a test checks they are equal)
TAILS_NU = "tails_nu"                    # R1-G5-TAILS: the Student-t degrees of freedom, beside a node's tails
RUN_COPY_KEYS = ("assembly_copy", "assembly_sha256", "runs_copy", "runs_sha256")   # D6 A (R1-T1-FEAT-DECISIONS)
T1_SIGMA_NODE = "t0_definition"          # = g5_noise.T1_SIGMA_NODE (D6-σ B; a test checks they are equal)
AR_PENDING_ITEMS = ["host_check", "noise_floor_copy", "environment", "tails"]   # §2.13: the spec's PENDING markers,
#                                                                       named as the completion record's keys
SCOPE = {"A": "non_inert_non_duplicate_evaluated_incl_divergent_and_timed_out", "B": "ok_outcome_only"}
SPLIT_SHA256 = "b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569"
SPLIT_SALT = "c3_t1_split/v1"
PREREG_SHA256 = "aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5"
GATE = {"path": "r1/c3/gate.py", "commit": "31dab9efb94b7f187ec44cab1bc4a4ad63c1085d",
        "sha256": "a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23"}   # v3.1, R1-BX-D8-CONFIRM-V31
INSTANCE_SEEDS = (5101, 5112)
SEED_BLOCKS = {"10": {"label": [7001, 7005], "evaluation": [7006, 7010]},
               "6": {"label": [7001, 7003], "evaluation": [7006, 7008]}}
RESERVED = ((1001, 3030, "G.1b"), (4001, 4099, "G.4 and G.4b"), (5001, 5006, "the E1b audit seeds"),
            (7001, 7010, "audit"), (8001, 8010, "census"), (9001, 10 ** 9, "exam"))
WAVES = [[1, 4], [5, 12]]
JOBS = ("campaigns-wave1", "audits-wave1", "campaigns-wave2", "audits-wave2")
SEED_RULE = 'sha256(f"{manager_seed}:{step}")[:8]'
ENABLE_ENV = "G5_TASL_ENABLE_REAL"
NOTE_DIR = "docs/r1/authorizations"
NOTE_NAME = re.compile(r"^c3_t1_labels_(\d{8})\.md$")
RUN_ID = re.compile(r"^c3_t1_labels_\d{8}$")
RECORD_NAME = re.compile(r"^docs/r1/reports/[A-Za-z0-9_.\-]+/G5_AR_PREREQUISITES_\d{8}\.md$")
RECORD_TOKEN = "G5_AR_PREREQUISITES"
XC_SPEC = "sweep2/t1_tasl/g1b_crosscheck_spec.json"
# P3's pilot (R1-G5-DIFF-RECOUNT): the G.4b re-pilot, bound from its committed result (pilot_basis). The dates are the
# eight-node recompute (R1-BX-D14-G4B, G4B-DATES A), not the seven-node comparison.
PILOT_SPEC_REL = "sweep2/t1_tasl/g4b_tasl_spec.json"
G4_NOTES = ("docs/r1/authorizations/g4_t1_tasl_20261122.md", "docs/r1/authorizations/g4_t1_tasl_20261123.md")
PILOT_BASIS_KEYS = ("run_id", "spec", "note", "nodes", "settings", "result_report", "corrigenda", "review", "dates_row",
                    "sealed", "liveness", "dates")
PILOT_SEALED_KEYS = ("sealed_path", "seal_receipt_sha256", "job_record_sha256", "out_tar_sha256",
                     "pilot_summary_sha256")
PILOT_LIVENESS = {"proposals": ("proposals",), "ran_of_proposals": ("rates", "ran_of_proposals"),
                  "ran_of_valid": ("diff_liveness", "ran_of_valid"),
                  "ok_of_proposals": ("diff_liveness", "ok_of_proposals")}       # spec key: path in pilot_summary.json
PILOT_DATES_KEYS = ("today", "labels_done", "B7", "D3", "manuscript", "g5_total_gpu_hours")
PILOT_SUMMARY_MEMBER = "out/pilot/pilot_summary.json"                              # as g4_tasl.read_sealed_summary
PILOT_DATES_ROW = "R1-BX-D14-G4B"
PILOT_DATES_TERMS = ("G4B-DATES A", "eight-node")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
G5_TRACKG_ADDITIONS = ("src/autoresearch/trackg/audit_g5.py", "src/autoresearch/trackg/diagnostics_g5.py")  # P5
NO_ADDITIONS = ("nodes/", "third_party/", "configs/trackg/", "src/autoresearch/trackg/node_lib/")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
AR_NOTE = re.compile(r"^docs/r1/authorizations/g1b_ar_t1_tasl_\d{8}\.md$")
# R1-T1-FEAT-DECISIONS (the ARMS-T1FEAT report's §5): the switch requires it on main, naming the decisions the G.5
# code on main implements (table bytes: D6-σ, D8, D9; the copies D6 A). plan_row matches each term literally (the
# hyphen-minus and Greek small sigma U+03C3 of "D6-σ B"), not running on into a letter or digit.
T1_FEAT_ROW = "R1-T1-FEAT-DECISIONS"
T1_FEAT_TERMS = ("D6 A", "D6-σ B", "D8 A", "D9 B")
PLAN_ROWS = ("R1-T1-HOST-TASL", "R1-T1-TASL-ENV", "R1-G1B-TIMEOUT", "R1-G5-DECISIONS", "R1-SWEEP2-PREREG",
             "R1-SWEEP2-RELEASE-DECISIONS", "R1-BX-D8-CONFIRM-V31", "R1-G1B-JOIN", "R1-HARNESS-ISOLATION")
ROW_ID = re.compile(r"^R1-[A-Z0-9][A-Z0-9-]*[A-Z0-9]$")
CITED = re.compile(r"^(\S+) sha256 ([0-9a-f]{64})$")
VERDICT_ACCEPTED = re.compile(r"^Verdict: ACCEPTED\s*$", re.M)
PLACEHOLDER = re.compile(r"<[^>]*>")
NU_TEXT = re.compile(r"[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?")
NU_SAID = re.compile(r"(?<![\w-])(?:nu|\u03bd)\s*=\s*((?:[^\s,;)\]}`|]|,(?=[0-9]))*)")
# The T1 table readings of part 3b-2 (g5_assemble), signed in the note's t1_table_readings line (review M2); the
# assembly refuses a note whose line differs, and without a signed note it allows only "refuse".
TABLE_READINGS = {
    "sigma_cmp": "sigma_cmp = sigma_node (dataset.noise_table's definition, the median joint paired sd over material "
                 "edits, on the node's G.1b runs.jsonl copied beside its summary; R1-T1-FEAT-DECISIONS D6-sigma B)",
    "excluded": "invalid, refused and final-infrastructure proposals left out of the table, counted",
    "delta_hat": "delta_hat = sign x (campaign value - best before the step), sign +1 maximize / -1 minimize, 0 for "
                 "no-ops and duplicates",
    "label_divergence": "a label uses the label seeds where candidate and parent are both ok (partial below K_label); "
                        "more than half candidate-divergent is a divergent label; fewer than half left otherwise is a "
                        "STOP",
    "evaluation_parent_only": "an evaluation seed where only the parent diverged is a STOP",
    "table_open": "the table (campaign values of every instance) opens with R1-T1-LABELS-UNSEAL; test labels and every "
                  "evaluation value stay locked until R1-T1-LABELS-TEST-RELEASE",
}
DELTA_HAT_OPTIONS = ("refuse", "neg_inf", "leave_out")
SERVER_LOG = {"a": "(a) sealed per server at its stop (seal-server; close-server after a crash), in clear on TASL-7 "
                   "while it runs (STOP 11); option (b), prompt logging off, not built"}
# P1 without C12: the acceptance line covers both hosts that run G.5 workers, TASL-2 (every job) and TASL-7 (audit
# chunks, R1-G5-AUDIT-TWO-CARDS); item 7 is untested on both (their host-check records). Under ``cuda_ipc: c12`` each
# host needs its own C12 PASS record (``check_c12``): TASL-2's for every job, TASL-7's for a TASL-7 audit chunk.
CUDA_IPC_ACCEPTANCE = (
    "The author accepts, for the G.5 label runs (EVIDENCE) on TASL-2 and for the G.5 audit chunks on TASL-7 "
    "(R1-G5-AUDIT-TWO-CARDS), the residual risk that harness-isolation host-check item 7 (CUDA IPC across the "
    "isolation boundary, reports/HARNESS_ISOLATION_20261117.md §3) is untested on TASL-2 and on TASL-7: no frozen "
    "parent exports a CUDA tensor, harness 2d09f9a9 documents that no node uses cuda_share or cuda_open, and every run "
    "record that is not effective with empty waivers and exceptions still STOPs its job (STOP 2), on either host. "
    "Disclosed in the T1 report.")
CUDA_C12_HOSTS = {"TASL-2": ("c12_record", "c12_sha256", "c12_review"),
                  "TASL-7": ("c12_tasl7_record", "c12_tasl7_sha256", "c12_tasl7_review")}


# =============================================================================================== small helpers
def load_spec(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def _get(spec: dict, path: tuple):
    cur = spec
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return KeyError
        cur = cur[k]
    return cur


def _set(spec: dict, path: tuple, value) -> None:
    cur = spec
    for k in path[:-1]:
        cur = cur.setdefault(k, {})
    cur[path[-1]] = value


def _ph(value) -> bool:
    """A placeholder: a string starting with TODO / PENDING / ... (``g1b_lib``), or None."""
    return value is None or L._placeholder(value)


def _nu_ok(nu) -> bool:
    return not isinstance(nu, bool) and isinstance(nu, (int, float)) and math.isfinite(nu) and nu > 2


def _parse_nu(token: str) -> float | None:
    if NU_TEXT.fullmatch(token) is None:
        return None
    value = float(token)
    return value if _nu_ok(value) else None


def check_tails_nu(n: dict, *, allow: bool = False) -> None:
    """R1-G5-TAILS: ``tails_nu`` (the Student-t degrees of freedom) is required where ``tails`` is ``student_t``, a
    finite real number > 2 (the label's sd is then finite, ``r1.c3.labels.STUDENT_T_SCALE``; a draft may leave it a
    placeholder), and refused where ``tails`` is ``gaussian`` or not yet declared (PENDING)."""
    tails, where = n.get("tails"), f"{n.get('node')}.{TAILS_NU}"
    if tails == "student_t":
        if TAILS_NU not in n:
            raise Stop(f"STOP: {where} is required where tails is student_t (R1-G5-TAILS)")
        nu = n[TAILS_NU]
        if not _nu_ok(nu) and not (allow and isinstance(nu, str) and _ph(nu)):
            raise Stop(f"STOP: {where} must be a finite number > 2 (R1-G5-TAILS)")
    elif TAILS_NU in n:
        raise Stop(f"STOP: {where} is refused where tails is not student_t (R1-G5-TAILS)")


def tails_text(n: dict) -> str:
    """A node's declared tail law as the note's ``tails`` line renders it: ``gaussian`` (unchanged), or
    ``student_t (nu = 5)``."""
    if n.get("tails") != "student_t":
        return str(n["tails"])
    nu = n.get(TAILS_NU)
    display = str(nu).removesuffix(".0") if _nu_ok(nu) else str(nu)
    return f"student_t (nu = {display})"


def _rel_ok(rel) -> bool:
    return isinstance(rel, str) and bool(rel) and not rel.startswith("/") and ".." not in Path(rel).parts \
        and not _ph(rel)


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _repo_file_sha(rel: str) -> str | None:
    p = REPO_ROOT / rel
    return L._sha_file(p) if p.is_file() else None


def options(spec: dict) -> dict:
    return {k: (spec.get("decisions") or {}).get(k, {}).get("option") for k in DECISIONS}


def _finite_or_none(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) else None


def g1b_verdict_scope(node: str, verdict: dict) -> dict:
    """R1-T1-D21-SCOPE on one node's G.1b verdict (``g1b_lib.summarise``'s shape). D21 does not select: the node's D21
    value is recorded (``d21``: the verdict, the material-edit count, the mean P(wrong) over the material edits and the
    rule's checks; JSON-safe, a non-finite number becomes null) for the screening funnel (R1-BX-D12). What still
    decides is fixed-seed determinism: ``deterministic`` is True only for a verdict that carries ``determinism`` with
    ``deterministic: true`` and is not the summary's determinism-failure verdict (a verdict without a determinism
    result is not taken as deterministic). No other threshold is applied here."""
    v = verdict or {}
    det = v.get("determinism") if isinstance(v.get("determinism"), dict) else {}
    deterministic = det.get("deterministic") is True and v.get("reason") != DETERMINISM_FAILED
    checks = v.get("checks") if isinstance(v.get("checks"), dict) else None
    n_material = v.get("n_material")
    d21 = {"qualifies_D21": v.get("qualifies_D21") is True,
           "n_material": n_material if isinstance(n_material, int) and not isinstance(n_material, bool) else None,
           "mean_p_wrong_material": _finite_or_none(v.get("mean_p_wrong_material")),
           "checks": {str(k): bool(x) for k, x in sorted(checks.items())} if checks is not None else None,
           "reason": v.get("reason") if isinstance(v.get("reason"), str) else None,
           "selects": False, "rule": D21_SCOPE_ROW}
    return {"node": node, "deterministic": deterministic, "d21": d21}


def require_deterministic(node: str, verdict: dict) -> dict:
    """STOP 5 under R1-T1-D21-SCOPE: a node that failed G.1b fixed-seed determinism is not run in G.5 (node STOP; the
    author decides on T2, R1-BX-D12). A node that does not qualify under D21 is recorded, not STOPped."""
    scope = g1b_verdict_scope(node, verdict)
    if not scope["deterministic"]:
        raise NodeStop(f"STOP 5: {node} has no G.1b fixed-seed determinism PASS (R1-T1-D21-SCOPE): not run in G.5; "
                       f"the author decides on T2 (R1-BX-D12)")
    return scope


def node_entry(spec: dict, name: str) -> dict:
    for node in spec["nodes"]:
        if node["node"] == name:
            return node
    raise Stop(f"STOP: {name} is not a G.5 node")


# =============================================================================================== options
def audited_band(opts: dict) -> list[int]:
    """STOP 9's band (§2.1, §4 item 9): 100-200 under G5-W A, 150-240 under B; doubled under G5-MEM B."""
    lo, hi = (100, 200) if opts["G5-W"] == "A" else (150, 240)
    k = 2 if opts["G5-MEM"] == "B" else 1
    return [lo * k, hi * k]


def divergence_block(option: str, pilot_nodes: list[str]) -> dict:
    """The ``divergence`` block of each G5-DIV option (§2.5); inputs that come from measurements are PENDING."""
    common = {"min_audited": 40, "denominator": "audited label proposals",
              "numerator": "E5-divergent on the label seeds"}
    if option == "A":
        return {"rule": "fixed", "threshold": 0.2, "literal_2x_census": 0.25, **common}
    if option == "B":
        return {"rule": "pilot_cp", "cap": 0.2, "floor": 0.1, "other_nodes": 0.2, "cp_level": 0.95, **common,
                "pilot_counts": {n: {"divergent": "PENDING", "proposals": "PENDING"} for n in pilot_nodes}}
    return {"rule": "g1b_2x", "cap": 0.2, **common,
            "g1b_divergent_rows": {n: {"divergent": "PENDING", "rows": "PENDING"} for n in T1_NODES}}


def required_settings(spec: dict) -> dict:
    """{field path: value} that the chosen options fix (the validator compares each)."""
    o = options(spec)
    w_a, mem = o["G5-W"] == "A", o["G5-MEM"]
    req = {("campaign", "W"): 20,
           ("campaign", "W_semantics"): "manager_calls" if w_a else "worker_runs",
           ("campaign", "llm_call_cap"): None if w_a else g4_lib.G5_LLM_CALL_CAP,
           ("campaign", "temperature"): 0.2 if o["G5-TEMP"] == "A" else 0.0,
           ("memory", "modes"): ["history"] if mem == "A" else ["history", "none"],
           ("memory", "instances_per_mode"): 6 if mem == "C" else 12,
           ("key_values", "audited_band"): audited_band(o),
           ("audit", "scope"): SCOPE.get(o["G5-AUDIT"]),
           ("audit", "cross_instance_duplicates"): "audit_once",
           ("audit", "e5_seed_block"): "label",
           ("divergence", "rule"): {"A": "fixed", "B": "pilot_cp", "C": "g1b_2x"}.get(o["G5-DIV"]),
           ("cap", "counts"): "worker_card" if o["G5-TASL-GPUH"] == "A" else "both_cards",
           ("slots", "worker_slots"): 1,
           ("slots", "worker_host"): WORKER_HOST,
           ("slots", "audit_hosts"): list(JOB_HOSTS),            # G5-SLOT A as amended by R1-G5-AUDIT-TWO-CARDS
           ("ar_prerequisites", "mode"): o["G5-ARPEND"]}
    if o["G5-TASL-GPUH"] == "B":
        req[("proposer", "server_stopped_during_audits")] = True
    return req


def apply_options(spec: dict, choices: dict) -> dict:
    """A copy of the spec with the given options and every field they govern; the options are left unsigned."""
    out = copy.deepcopy(spec)
    for key, opt in choices.items():
        if key not in DECISIONS or opt not in OPTIONS[key]:
            raise Stop(f"STOP: unknown decision or option {key}={opt}")
        out["decisions"][key]["option"] = opt
        out["decisions"][key]["signed"] = False
    for path, value in required_settings(out).items():
        _set(out, path, copy.deepcopy(value))
    o = options(out)
    if "G5-DIV" in choices:
        out["divergence"] = divergence_block(o["G5-DIV"], out["pilot_basis"]["nodes"])
    if "G5-TASL-GPUH" in choices and o["G5-TASL-GPUH"] == "A":
        out["proposer"]["server_stopped_during_audits"] = False
    if "G5-MEM" in choices:
        out["e4_amendment_row"] = ("PENDING: G5-MEM A needs the author's PLAN row amending E4's 'both memory modes'"
                                   if o["G5-MEM"] == "A" else None)
    if "G5-ARPEND" in choices:
        marker = AR_PENDING if o["G5-ARPEND"] == "A" else AR_FILL_B
        ar = node_entry(out, AR)
        ar["env"], ar["tails"] = marker, marker
        out["noise_floor"]["ar"].update(copy=marker, sha256=marker, review=marker, sealed_path=marker,
                                        **{k: marker for k in RUN_COPY_KEYS})
        out["harness_families"]["G5-AR"]["isolation_host_check"] = marker if o["G5-ARPEND"] == "A" else \
            {"record": marker, "sha256": marker}
        out["ar_prerequisites"]["pending"] = list(AR_PENDING_ITEMS) if o["G5-ARPEND"] == "A" else []
        if o["G5-ARPEND"] == "B":
            prop = out["ar_prerequisites"]["proposed_environment"]
            out["envs"][prop["name"]] = {"freeze": prop["freeze"], "sha256": prop["sha256"], "python": prop["python"]}
        else:
            out["envs"].pop(out["ar_prerequisites"]["proposed_environment"]["name"], None)
    return out


def clopper_pearson_upper(x: int, n: int, level: float = 0.95) -> float:
    """The upper limit of the two-sided Clopper-Pearson interval at ``level`` (tail (1 - level) / 2), by bisection on
    the binomial CDF."""
    if not (isinstance(x, int) and isinstance(n, int) and 0 <= x <= n and n > 0):
        raise Stop("STOP: Clopper-Pearson needs integer counts 0 <= x <= n, n > 0")
    if x == n:
        return 1.0
    tail = (1.0 - level) / 2.0

    def cdf(p: float) -> float:
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x + 1))
    lo, hi = x / n, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if cdf(mid) > tail:
            lo = mid
        else:
            hi = mid
    return hi


def divergence_threshold(spec: dict, node: str) -> dict:
    """STOP 1's threshold for one node under the chosen G5-DIV option (§2.5)."""
    d = spec["divergence"]
    if d["rule"] == "fixed":
        return {"node": node, "threshold": d["threshold"], "literal_2x_census": d["literal_2x_census"],
                "min_audited": d["min_audited"], "rule": "G5-DIV A"}
    if d["rule"] == "pilot_cp":
        counts = (d.get("pilot_counts") or {}).get(node)
        if counts is None:
            return {"node": node, "threshold": d["other_nodes"], "min_audited": d["min_audited"],
                    "rule": "G5-DIV B (not a pilot node)"}
        if not all(isinstance(counts.get(k), int) for k in ("divergent", "proposals")):
            raise Stop(f"STOP: G5-DIV B needs the pilot's divergent and proposal counts for {node}")
        ub = clopper_pearson_upper(counts["divergent"], counts["proposals"], d["cp_level"])
        return {"node": node, "threshold": round(min(d["cap"], max(2 * ub, d["floor"])), 6), "cp_upper": ub,
                "min_audited": d["min_audited"], "rule": "G5-DIV B"}
    rows = (d.get("g1b_divergent_rows") or {}).get(node) or {}
    if not all(isinstance(rows.get(k), int) for k in ("divergent", "rows")) or rows["rows"] <= 0:
        raise Stop(f"STOP: G5-DIV C needs the G.1b divergent-row counts for {node}")
    return {"node": node, "threshold": round(min(d["cap"], 2 * rows["divergent"] / rows["rows"]), 6),
            "min_audited": d["min_audited"], "rule": "G5-DIV C"}


def audit_seeds(spec: dict, k: int) -> dict:
    """The label and evaluation seeds at K (STOP 10: under K = 6, 7004-7005 and 7009-7010 are never used)."""
    if k not in (10, 6):
        raise Stop("STOP: K is 10 or 6")
    b = spec["audit"]["seed_blocks"][str(k)]
    return {"label": list(range(b["label"][0], b["label"][1] + 1)),
            "evaluation": list(range(b["evaluation"][0], b["evaluation"][1] + 1))}


def instance_seeds(spec: dict) -> list[int]:
    lo, hi = spec["instances"]["seeds"]
    return list(range(lo, hi + 1))


def split_from_rule(node: str, seeds: list[int]) -> dict:
    """§2.7: the 12 instances ordered by sha256("c3_t1_split/v1:" + node + ":" + seed); 6 test, 2 dev, 4 train."""
    order = sorted(seeds, key=lambda s: hashlib.sha256(f"{SPLIT_SALT}:{node}:{s}".encode()).hexdigest())
    ids = [f"{node}__s{s}" for s in order]
    return {"test": sorted(ids[:6]), "dev": sorted(ids[6:8]), "train": sorted(ids[8:])}


# =============================================================================================== projection
def dates_params(spec: dict) -> dict:
    """The R1-BX-D14 recompute inputs for the eight-node G.5 table: ``g4_tasl_dates_params.json`` with the spec's nodes
    and census times, the nodes censused on the 4090 exempt from the ratio, and the options' W, memory modes, parent
    reuse and cap."""
    p = json.loads((HERE / "g4_tasl_dates_params.json").read_text())
    o = options(spec)
    p["t1_nodes"] = [n["node"] for n in spec["nodes"]]
    p["run_seconds"] = {n["node"]: n["run_seconds"] for n in spec["nodes"]}
    p["ratio_exempt_nodes"] = sorted(n["node"] for n in spec["nodes"] if n.get("census_gpu_model") == GPU_MODEL)
    p["w_semantics"] = spec["campaign"]["W_semantics"]
    p["mem_modes"] = len(spec["memory"]["modes"]) if o["G5-MEM"] == "B" else 1
    p["reuse_parent_runs"] = bool(spec["audit"]["reuse_parent_runs"])
    p["g5_cap_gpu_hours"] = spec["key_values"]["cap_gpu_hours"]
    p["llm_seconds_fallback"] = spec["projection"]["llm_seconds_fallback"]
    p["startup_s"] = spec["projection"]["startup_s"]
    return p


def projection(spec: dict) -> dict:
    """Pre-pilot GPU-hours under the chosen options at ran share 0.6 and 0.8 (K = 10 and 6), the cap's basis per
    G5-TASL-GPUH (A: worker card; B: worker card + the proposer card over the campaign waves, server stopped during
    the audits)."""
    out = {}
    both = options(spec)["G5-TASL-GPUH"] == "B"
    for share in (0.6, 0.8):
        p = dates_params(spec) | {"ran_share_fallback": share}
        r = T4.recompute_dates({}, p, today=date(2026, 11, 23))
        for k in ("10", "6"):
            per = r["g5_by_K"][k]["per_node"]
            worker = round(sum(v["gpu_hours"] for v in per.values()), 1)
            campaign = round(sum(v["campaign_gpu_hours"] for v in per.values()), 1)
            out[f"share={share} K={k}"] = {"worker_gpu_hours": worker, "campaign_gpu_hours": campaign,
                                           "capped_gpu_hours": round(worker + campaign, 1) if both else worker}
    return out


# =============================================================================================== the spec
def _check_split(spec: dict) -> dict:
    sf = spec["instances"]["split_file"]
    if sf.get("path") != "r1/c3/splits/c3_p3_split_v1.json" or sf.get("sha256") != SPLIT_SHA256 \
            or sf.get("salt") != SPLIT_SALT:
        raise Stop("STOP: instances.split_file must be r1/c3/splits/c3_p3_split_v1.json, sha256 b5967dd7…, salt "
                   "c3_t1_split/v1 (R1-SWEEP2-PREREG, PRE-SPLIT A)")
    raw = (REPO_ROOT / sf["path"]).read_bytes()
    if _sha_bytes(raw) != SPLIT_SHA256:
        raise Stop("STOP: the split file in the checkout differs from its frozen sha256")
    t1 = (json.loads(raw).get("t1") or {}).get("nodes") or {}
    if sorted(t1) != sorted(T1_NODES):
        raise Stop(f"STOP: the split file's T1 nodes {sorted(t1)} are not the eight G.5 nodes")
    for node, parts in t1.items():
        want = split_from_rule(node, instance_seeds(spec))
        if {k: sorted(v) for k, v in parts.items()} != want:
            raise Stop(f"STOP: the split file's assignment for {node} differs from the §2.7 rule")
    return {"path": sf["path"], "sha256": SPLIT_SHA256, "nodes": len(t1)}


def _check_seeds(spec: dict) -> None:
    inst = spec.get("instances") or {}
    if inst.get("per_node") != 12 or inst.get("seeds") != list(INSTANCE_SEEDS) or inst.get("waves") != WAVES:
        raise Stop("STOP: instances must be 12 per node, seeds 5101-5112, waves 1-4 and 5-12 (R1-BX-D8-V3-B, §3)")
    seeds = instance_seeds(spec)
    for lo, hi, what in RESERVED:
        clash = [s for s in seeds if lo <= s <= hi]
        if clash:
            raise Stop(f"STOP: instance seeds {clash} fall in the reserved {what} block")
    if (spec.get("audit") or {}).get("seed_blocks") != SEED_BLOCKS:
        raise Stop("STOP: audit.seed_blocks must be K = 10: 7001-7005 / 7006-7010 and K = 6: 7001-7003 / 7006-7008")


def g4_spec() -> dict:
    """The G.4 pilot spec on this checkout: the signed G.4 note's proposer, environments, sealed root and checkout,
    which G.5 still compares with (G.4b's are the same), and the default of ``dates``. P3 reads ``pilot_spec``."""
    return json.loads((HERE / "g4_tasl_spec.json").read_text())


def pilot_spec() -> tuple[dict, str]:
    """The pilot spec P3 reads (R1-G5-DIFF-RECOUNT): the G.4b re-pilot spec on this checkout, validated as a G.4b spec
    (``g4_tasl.validate_spec``, no launch), and its file sha256, the ``spec_sha256`` each sealed G.4b job record
    carries."""
    p = REPO_ROOT / PILOT_SPEC_REL
    pilot = T4.load_spec(p)
    T4.validate_spec(pilot)
    if not T4.is_g4b(pilot):
        raise Stop(f"STOP: {PILOT_SPEC_REL} is not a G.4b spec (R1-G5-DIFF-RECOUNT; P3)")
    return pilot, L._sha_file(p)


def _share(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1


def _bound_file(entry, what: str, *, prefix: str, name: re.Pattern | None = None, where: str = "pilot_basis") -> dict:
    """A ``{path, sha256}`` binding of a committed file: a repository path under ``prefix`` (and matching ``name``,
    where given), and its sha256 equal to the file in this checkout (the switch checks it on published main too)."""
    tag = " (P3)" if where == "pilot_basis" else ""
    if not isinstance(entry, dict) or set(entry) != {"path", "sha256"} or not _rel_ok(entry.get("path")) or \
            not str(entry["path"]).startswith(prefix) or (name is not None and not name.fullmatch(str(entry["path"]))) \
            or not SHA64.fullmatch(str(entry.get("sha256"))):
        raise Stop(f"STOP: {where}.{what} must be {{path, sha256}} of a committed file under {prefix}{tag}")
    if _repo_file_sha(entry["path"]) != entry["sha256"]:
        raise Stop(f"STOP: {where}.{what}: {entry['path']} in the checkout differs from its declared sha256{tag}")
    return entry


def check_pilot_basis(spec: dict) -> tuple[dict, str]:
    """P3's ``pilot_basis`` (R1-G5-DIFF-RECOUNT), every value filled from the committed G.4b result: exactly the G.4b
    re-pilot run, the G.4b spec at its sha256 in the checkout, its nodes; the signed G.4b note, the result report and
    its corrigenda, each by path and sha256 (equal to the checkout's files); the dates row R1-BX-D14-G4B; per node the
    sealed attempt (``<G.4b sealed_root>/<run>/<node>/attempt-<N>``, three sha256) and the liveness (60 proposals,
    shares in [0, 1]); and the recompute (``today`` and three ISO dates, ``g5_total_gpu_hours`` positive). No
    placeholder of any kind. What the pilot ran is read from the G.4b spec, never declared here. Returns the G.4b spec
    and its sha256."""
    pb = spec.get("pilot_basis") or {}
    if set(pb) != set(PILOT_BASIS_KEYS):
        raise Stop(f"STOP: pilot_basis must carry exactly {list(PILOT_BASIS_KEYS)}; what the pilot ran is read from "
                   f"{PILOT_SPEC_REL}'s pilot block, not declared here (P3)")
    ps = pb.get("spec") or {}
    if not isinstance(ps, dict) or set(ps) != {"path", "sha256"} or ps.get("path") != PILOT_SPEC_REL:
        raise Stop(f"STOP: pilot_basis.spec must be {{path: {PILOT_SPEC_REL}, sha256}} (the G.4b re-pilot spec, "
                   f"R1-G5-DIFF-RECOUNT; P3)")
    pilot, pilot_sha = pilot_spec()
    if ps.get("sha256") != pilot_sha:
        raise Stop(f"STOP: pilot_basis.spec.sha256 differs from {PILOT_SPEC_REL} in the checkout (the spec the sealed "
                   f"G.4b attempts ran; P3)")
    run_id = pilot["run_id"]
    if pb.get("run_id") != run_id or not T4.G4B_RUN_ID.fullmatch(str(pb.get("run_id"))) or \
            pb.get("nodes") != [n["node"] for n in pilot["nodes"]]:
        raise Stop(f"STOP: pilot_basis must name exactly the G.4b re-pilot run of {PILOT_SPEC_REL} and its nodes, not "
                   f"the G.4 pilot (R1-G5-DIFF-RECOUNT; P3)")
    L._commit(pilot["harness"].get("commit"), f"{PILOT_SPEC_REL} harness.commit", allow_placeholder=False)
    note = pb.get("note")
    if isinstance(note, dict) and note.get("path") in G4_NOTES:
        raise Stop("STOP: pilot_basis.note must be the signed G.4b note, not one of the G.4 notes (P3)")
    _bound_file(note, "note", prefix=f"{NOTE_DIR}/", name=re.compile(r"docs/r1/authorizations/g4_t1_tasl_\d{8}\.md"))
    for key in ("result_report", "corrigenda"):
        _bound_file(pb.get(key), key, prefix="docs/r1/reports/", name=re.compile(r"[^\s]+\.md"))
    _bound_file(pb.get("review"), "review", prefix="docs/r1/reviews/", name=re.compile(r"[^\s]+\.md"))
    if pb.get("dates_row") != PILOT_DATES_ROW:
        raise Stop(f"STOP: pilot_basis.dates_row must be {PILOT_DATES_ROW} (G4B-DATES A: the eight-node recompute; P3)")
    sealed, live, dates = pb.get("sealed"), pb.get("liveness"), pb.get("dates")
    nodes = pb["nodes"]
    if not isinstance(sealed, dict) or sorted(sealed) != sorted(nodes) or \
            not isinstance(live, dict) or sorted(live) != sorted(nodes):
        raise Stop("STOP: pilot_basis.sealed and pilot_basis.liveness must have exactly the G.4b nodes (P3)")
    root = re.escape(pilot["worker"]["sealed_root"].rstrip("/") + f"/{run_id}/")
    for node in nodes:
        e = sealed[node]
        if not isinstance(e, dict) or set(e) != set(PILOT_SEALED_KEYS):
            raise Stop(f"STOP: pilot_basis.sealed.{node} must carry exactly {list(PILOT_SEALED_KEYS)} (P3)")
        if not re.fullmatch(root + re.escape(node) + r"/attempt-[1-9][0-9]*", str(e["sealed_path"])):
            raise Stop(f"STOP: pilot_basis.sealed.{node}.sealed_path must be <G.4b sealed_root>/{run_id}/{node}/"
                       f"attempt-<N> (P3)")
        bad = [k for k in PILOT_SEALED_KEYS[1:] if not SHA64.fullmatch(str(e[k]))]
        if bad:
            raise Stop(f"STOP: pilot_basis.sealed.{node}: {bad} must be sha256 values (P3)")
        lv = live[node]
        if not isinstance(lv, dict) or set(lv) != set(PILOT_LIVENESS):
            raise Stop(f"STOP: pilot_basis.liveness.{node} must carry exactly {list(PILOT_LIVENESS)} (P3)")
        if not (type(lv["proposals"]) is int and lv["proposals"] == g4_lib.PILOT_PROPOSALS) or \
                not all(_share(lv[k]) for k in PILOT_LIVENESS if k != "proposals"):
            raise Stop(f"STOP: pilot_basis.liveness.{node}: proposals {g4_lib.PILOT_PROPOSALS} and shares in [0, 1] "
                       f"(P3)")
    if not isinstance(dates, dict) or set(dates) != set(PILOT_DATES_KEYS):
        raise Stop(f"STOP: pilot_basis.dates must carry exactly {list(PILOT_DATES_KEYS)} (P3)")
    for key in PILOT_DATES_KEYS[:-1]:
        if not DATE.fullmatch(str(dates[key])):
            raise Stop(f"STOP: pilot_basis.dates.{key} must be an ISO date (P3)")
        try:
            date.fromisoformat(dates[key])
        except ValueError:
            raise Stop(f"STOP: pilot_basis.dates.{key} must be an ISO date (P3)") from None
    total = dates["g5_total_gpu_hours"]
    if not (isinstance(total, (int, float)) and not isinstance(total, bool) and total > 0):
        raise Stop("STOP: pilot_basis.dates.g5_total_gpu_hours must be positive (P3)")
    return pilot, pilot_sha


def dates_pilot_spec(path: str | Path | None) -> tuple[dict, str]:
    """The pilot spec whose sealed attempts ``dates`` reads, and its file sha256: ``g4_tasl_spec.json`` by default (the
    G.4 pilot, kept for history), or (``--pilot-spec``) the G.4b re-pilot spec of R1-G5-DIFF-RECOUNT, which must
    validate as a G.4b spec and have the G.4 pilot's settings (W, memory mode, temperature) and nodes. P3's
    ``pilot_basis.dates`` is this command's output with ``--pilot-spec sweep2/t1_tasl/g4b_tasl_spec.json``."""
    default = HERE / "g4_tasl_spec.json"
    p = Path(path) if path else default
    pilot = T4.load_spec(p)
    if p.resolve() != default.resolve():
        T4.validate_spec(pilot)
        g4 = g4_spec()
        if not T4.is_g4b(pilot):
            raise Stop("STOP: --pilot-spec is for the G.4b re-pilot spec (R1-G5-DIFF-RECOUNT)")
        if pilot_settings(pilot) != pilot_settings(g4) or \
                [n["node"] for n in pilot["nodes"]] != [n["node"] for n in g4["nodes"]]:
            raise Stop("STOP: the G.4b spec must run the G.4 pilot's settings (W, memory mode, temperature) on its nodes")
    return pilot, L._sha_file(p)


def pilot_settings(g4: dict) -> dict:
    """What a G.4 or G.4b pilot spec ran, from its ``pilot`` block: W counts manager calls in the v2-diff pilot
    (``budget``), one memory mode, the temperature. P3 reads it from the G.4b spec (``pilot_spec``); only a re-issued
    G.4b spec changes these."""
    pilot = g4["pilot"]
    return {"W_semantics": pilot.get("W_semantics", "manager_calls"), "W": pilot["budget"],
            "memory_modes": [pilot["memory_mode"]], "temperature": pilot["temperature"]}


def other_checkouts() -> set[str]:
    """The harness checkouts of G.1b (both specs, every host), G.4 and G.4b: a G.5 family checkout is none of them."""
    out = set()
    for rel in FAMILY_SPECS.values():
        out |= {h.get("harness_dir") for h in json.loads((REPO_ROOT / rel).read_text())["hosts"].values()}
    out.add(g4_spec()["worker"].get("harness_dir"))
    out.add((json.loads((REPO_ROOT / PILOT_SPEC_REL).read_text()).get("worker") or {}).get("harness_dir"))
    return out - {None}


def _check_family(spec: dict, fam: str, launch: bool, o: dict) -> dict:
    f = (spec.get("harness_families") or {}).get(fam) or {}
    if f.get("g1b_pin") != FAMILIES[fam]:
        raise Stop(f"STOP: harness_families.{fam}.g1b_pin must be {FAMILIES[fam]} (G5-PIN B)")
    L._commit(f.get("g5_commit"), f"harness_families.{fam}.g5_commit", allow_placeholder=not launch)
    G._abs(f.get("harness_dir"), f"harness_families.{fam}.harness_dir")
    gs = f.get("g1b_spec") or {}
    if gs.get("path") != FAMILY_SPECS[fam]:
        raise Stop(f"STOP: harness_families.{fam}.g1b_spec.path must be {FAMILY_SPECS[fam]}")
    if gs.get("sha256") != _repo_file_sha(gs["path"]):
        raise Stop(f"STOP: harness_families.{fam}.g1b_spec.sha256 differs from {gs['path']} in the checkout")
    g1b = json.loads((REPO_ROOT / gs["path"]).read_text())
    if gs.get("run_id") != g1b["run_id"] or g1b["harness"]["commit"] != FAMILIES[fam]:
        raise Stop(f"STOP: harness_families.{fam}.g1b_spec must name that spec's run_id and pin")
    if f["harness_dir"] in other_checkouts():
        raise Stop(f"STOP: harness_families.{fam}.harness_dir must not be a G.1b or G.4 checkout, nor G.4b's (they "
                   f"stay at their commits)")
    check = f.get("isolation_host_check")
    if fam == "G5-AR" and o["G5-ARPEND"] == "A":
        if check != AR_PENDING:
            raise Stop("STOP: under G5-ARPEND A, G5-AR's isolation_host_check is the PENDING marker (§2.13)")
    else:
        if not isinstance(check, dict) or not str(check.get("record", "")).startswith(("docs/r1/reports/", "TODO",
                                                                                         "PENDING")):
            raise Stop(f"STOP: harness_families.{fam}.isolation_host_check must name a report under docs/r1/reports/")
        if launch and _ph(check.get("record")):
            raise Stop(f"STOP: harness_families.{fam}.isolation_host_check.record must be filled")
        L._sha(check.get("sha256"), f"harness_families.{fam}.isolation_host_check.sha256",
               allow_placeholder=not launch)
    return g1b


def xc_pending(node: str) -> str:
    return XC_PENDING.format(node=node)


def _check_xc_entries(node: str, entries) -> list[dict] | None:
    """One node's ``tasl7_audits.crosshost_pass`` value: the exact marker ``PENDING short cross-check: <node>`` (the
    node may not run on TASL-7 yet; it still runs on TASL-2), or a list of cross-host PASS records, each
    ``{record, sha256, mode, crosscheck_run_id}`` under docs/r1/reports/, with at least one ``xc`` or ``short`` record. For the three
    TASL-7 G.1b nodes the list is exactly their two xc2 verdicts (step 1 ``xc``, step 2 ``preassembly``) of the
    cross-check spec's run. For the four xc3 short-check nodes a list is exactly one record (revision 13, now that
    their PASS verdicts are on main): mode ``short``, the file ``docs/r1/reports/<dir>/G1B_XC3_SHORT_VERDICT_<node>_
    <YYYYMMDD>.json``, the run id of the xc3 spec in the checkout, and the sha256 of that file in the checkout. The
    record bytes are checked on published main at each TASL-7 job start (``check_crosshost_pass``)."""
    if entries == xc_pending(node):
        if node in X_NODES:
            raise Stop(f"STOP: tasl7_audits.crosshost_pass.{node} must name its xc2 verdicts (on main), not a PENDING "
                       f"marker")
        return None
    if not isinstance(entries, list) or not entries:
        raise Stop(f"STOP: tasl7_audits.crosshost_pass.{node} must be a list of PASS records or "
                   f"{xc_pending(node)!r}")
    for e in entries:
        if not isinstance(e, dict) or set(e) != {"record", "sha256", "mode", "crosscheck_run_id"} or \
                not _rel_ok(e.get("record")) or not str(e["record"]).startswith("docs/r1/reports/") or \
                e.get("mode") not in X.MODES + (SHORT_MODE,) or not isinstance(e.get("crosscheck_run_id"), str) or \
                _ph(e["crosscheck_run_id"]):
            raise Stop(f"STOP: tasl7_audits.crosshost_pass.{node}: each record is {{record, sha256, mode, "
                       f"crosscheck_run_id}} with a report path and a mode in {X.MODES + (SHORT_MODE,)}")
        L._sha(e.get("sha256"), f"tasl7_audits.crosshost_pass.{node}.sha256", allow_placeholder=False)
    if not {"xc", SHORT_MODE} & {e["mode"] for e in entries} or len({e["record"] for e in entries}) != len(entries):
        raise Stop(f"STOP: tasl7_audits.crosshost_pass.{node} needs an xc or short (both hosts) PASS record, each named "
                   f"once")
    if node in X_NODES:
        xc_run = json.loads((REPO_ROOT / XC_SPEC).read_text())["run_id"]
        want = sorted((XC2_VERDICTS[mode].format(node=node), mode, xc_run) for mode in XC2_VERDICTS)
        if sorted((e["record"], e["mode"], e["crosscheck_run_id"]) for e in entries) != want:
            raise Stop(f"STOP: tasl7_audits.crosshost_pass.{node} must be exactly its xc2 step-1 and step-2 verdicts "
                       f"({[w[0] for w in want]}) of run {xc_run}")
    else:                                                    # an xc3 short-check node with its verdict pinned
        xc3_run = json.loads((REPO_ROOT / XC3_SPEC_REL).read_text())["run_id"]
        e = entries[0]
        m = SHORT_XC_NAME.fullmatch(str(e["record"]))
        if len(entries) != 1 or e["mode"] != SHORT_MODE or not m or m.group("node") != node or \
                e["crosscheck_run_id"] != xc3_run:
            raise Stop(f"STOP: tasl7_audits.crosshost_pass.{node} must be exactly its xc3 short verdict "
                       f"docs/r1/reports/<dir>/{SHORT_XC_TOKEN}{node}_<YYYYMMDD>.json (mode {SHORT_MODE}) of run "
                       f"{xc3_run}, or {xc_pending(node)!r}")
        if _repo_file_sha(e["record"]) != e["sha256"]:
            raise Stop(f"STOP: tasl7_audits.crosshost_pass.{node}: {e['record']} in the checkout differs from its "
                       f"declared sha256")
    return entries


X_NODES = ("mlab_cifar10", "mlgym_breakout_minatar", "mlgym_cifar10")          # the cross-check spec's TASL-7 nodes


def _check_tasl7(spec: dict, launch: bool, g1b_seven: dict) -> dict:
    """``tasl7_audits`` (R1-G5-AUDIT-TWO-CARDS): TASL-7 as an audit host for the G5-7 family only. Its identity, lease,
    environments, extra environment and host-check record are the ones the signed G.1b spec gives TASL-7 (where G.1b
    ran the three TASL-7 nodes), its lease is the proposer server's (so a held server excludes every TASL-7 audit and a
    TASL-7 audit excludes a server start), its harness checkout is the G5-7 family's path (a new checkout on TASL-7,
    apart from G.1b's), and its runs tree has the TASL-2 layout (the same runs_root), so claims, plans and attempts copy
    by relative path. ``crosshost_pass`` names each of the seven nodes' cross-host PASS records or the PENDING marker;
    autoresearch has none (its audits stay on TASL-2: ar-cond7a exists only there)."""
    t = spec.get("tasl7_audits")
    if not isinstance(t, dict):
        raise Stop("STOP: tasl7_audits is required (R1-G5-AUDIT-TWO-CARDS amends G5-SLOT A)")
    ref = g1b_seven["hosts"][AUDIT_HOST]
    p = spec["proposer"]
    want = {"authority": f"{TWO_CARDS_ROW} (amends G5-SLOT A)", "host": AUDIT_HOST, "hostname": ref["hostname"],
            "gpu_uuid": ref["gpu_uuid"], "driver": DRIVERS["proposer"], "lease": p["lease"], "families": ["G5-7"],
            "harness_dir": spec["harness_families"]["G5-7"]["harness_dir"], "base": ref["base"],
            "runs_root": spec["worker"]["runs_root"], "uv": ref["uv"], "env_python": ref["env_python"],
            "extra_env": ref.get("extra_env") or {}, "isolation_host_check": ref["isolation_host_check"]}
    bad = sorted(k for k, v in want.items() if t.get(k) != v)
    if bad:
        raise Stop(f"STOP: tasl7_audits fields {bad} differ from the TASL-7 of the signed G.1b spec, the proposer's lease, "
                   f"the G5-7 checkout path or the worker's runs tree (R1-G5-AUDIT-TWO-CARDS)")
    if t["gpu_uuid"] != p["gpu_uuid"] or t["hostname"] != p["hostname"]:
        raise Stop("STOP: tasl7_audits must be the proposer's host and card")
    G.cpu_list(t.get("cpus", ""))
    extra = set(t) - set(want) - {"cpus", "node_extra_env", "crosshost_pass"}
    if extra:
        raise Stop(f"STOP: tasl7_audits has unknown fields {sorted(extra)}")
    nx = t.get("node_extra_env") or {}
    if not isinstance(nx, dict) or not set(nx) <= set(SEVEN) or \
            not all(isinstance(v, dict) and all(isinstance(x, str) for x in v.values()) for v in nx.values()):
        raise Stop("STOP: tasl7_audits.node_extra_env maps seven-node names to {name: value}")
    xp = t.get("crosshost_pass")
    if not isinstance(xp, dict) or sorted(xp) != sorted(SEVEN):
        raise Stop(f"STOP: tasl7_audits.crosshost_pass must name exactly the seven nodes (autoresearch's audits stay on "
                   f"{WORKER_HOST})")
    pending = sorted(n for n in SEVEN if _check_xc_entries(n, xp[n]) is None)
    return {"pending_crosshost": pending}


def _cpus(text, what: str) -> list[int]:
    try:
        return G.cpu_list(text)
    except (ValueError, TypeError):
        raise Stop(f"STOP: {what} is not a CPU list") from None


def _tasl2_ok(cpus: list[int], what: str) -> None:
    """R1-TASL2-CPU: a TASL-2 CPU set may not contain any of CPUs 8-11, and names only TASL-2's CPUs 0-31."""
    bad = sorted(set(cpus) & set(TASL2_EXCLUDED))
    if bad:
        raise Stop(f"STOP: {what} contains CPUs {bad}: no R1 job on TASL-2 uses CPUs 8-11 ({TASL2_CPU_ROW})")
    if max(cpus) >= TASL2_NCPUS:
        raise Stop(f"STOP: {what} names CPUs beyond TASL-2's 0-{TASL2_NCPUS - 1}")


def _check_tasl2_cpus(spec: dict) -> dict:
    """R1-TASL2-CPU on every TASL-2 CPU set of the spec. ``worker.cpus`` (the GPU jobs) may not contain CPUs 8-11. A
    node's own ``cpus`` is its G.1b set (the validator keeps it equal to the signed G.1b spec, and it is the set its
    TASL-7 audit chunks use): where it contains any of 8-11, ``tasl2_cpus.replacements`` must give that node a TASL-2
    set of the same size without them (``g1b_cpus`` naming the set it replaces), and no other node has a replacement.
    Each replacement needs its fixed-seed determinism record on main before the node's first TASL-2 job
    (``check_cpuset_record``). A replacement may share the worker's CPUs: every G.5 job on TASL-2, the CPU-only node's
    included, holds the TASL-2 lease (``g5_job.run_job``), so they never run at the same time. The stability record is
    bound by path and sha256. Returns ``{node: cpus}`` of the replacements."""
    t = spec.get("tasl2_cpus")
    keys = {"authority", "excluded", "stability_record", "replacements"}
    if not isinstance(t, dict) or set(t) != keys:
        raise Stop(f"STOP: tasl2_cpus must carry exactly {sorted(keys)} ({TASL2_CPU_ROW})")
    if t["authority"] != TASL2_CPU_ROW or t["excluded"] != "8-11":
        raise Stop(f"STOP: tasl2_cpus.authority must be {TASL2_CPU_ROW} and excluded 8-11")
    _bound_file(t["stability_record"], "stability_record", prefix="docs/r1/reports/",
                name=re.compile(re.escape(TASL2_STABILITY)), where="tasl2_cpus")
    _tasl2_ok(_cpus(spec["worker"].get("cpus", ""), "worker.cpus"), "worker.cpus")
    reps = t["replacements"]
    if not isinstance(reps, dict):
        raise Stop("STOP: tasl2_cpus.replacements maps node names to {g1b_cpus, cpus}")
    need = []
    for n in spec["nodes"]:
        own = n.get("cpus")
        if own is not None and set(_cpus(own, f"{n['node']}.cpus")) & set(TASL2_EXCLUDED):
            need.append(n["node"])
    if sorted(reps) != sorted(need):
        raise Stop(f"STOP: tasl2_cpus.replacements must name exactly the nodes whose G.1b CPU set contains any of CPUs "
                   f"8-11 ({sorted(need)}; {TASL2_CPU_ROW})")
    out = {}
    for name in need:
        r, own = reps[name], node_entry(spec, name)["cpus"]
        if not isinstance(r, dict) or set(r) != {"g1b_cpus", "cpus"} or r["g1b_cpus"] != own:
            raise Stop(f"STOP: tasl2_cpus.replacements.{name} must be {{g1b_cpus: {own!r}, cpus}}")
        new = _cpus(r["cpus"], f"tasl2_cpus.replacements.{name}.cpus")
        _tasl2_ok(new, f"tasl2_cpus.replacements.{name}.cpus")
        if len(new) != len(_cpus(own, f"{name}.cpus")):
            raise Stop(f"STOP: tasl2_cpus.replacements.{name}.cpus must have the size of the set it replaces "
                       f"({own}; {TASL2_CPU_ROW})")
        cpuset_reference(name)                     # its determinism check compares with a declared G.1b attempt
        out[name] = r["cpus"]
    return out


def cpuset_reference(node: str) -> dict:
    """The sealed G.1b TASL-2 attempt a replacement set's determinism check compares with: the one the xc3 spec in the
    checkout declares for the node (``g1b_tasl2_attempts``; reviewed with the xc3 unit, and its PASS against TASL-7 is
    on main)."""
    ref = (json.loads((REPO_ROOT / XC3_SPEC_REL).read_text()).get("g1b_tasl2_attempts") or {}).get(node)
    if not isinstance(ref, dict):
        raise Stop(f"STOP: {node} has no declared sealed G.1b TASL-2 attempt in {XC3_SPEC_REL}; its replacement CPU set "
                   f"has no reference for the fixed-seed determinism check ({TASL2_CPU_ROW})")
    return ref


def expansion_leases(cpus: str) -> list[str]:
    """The expansion G.1b's CPU-set lease files whose sets overlap ``cpus`` (``EXPANSION_CPU_SETS``)."""
    own = set(G.cpu_list(cpus))
    return [f"~/r1_locks/cpus-{x}.lock" for x in EXPANSION_CPU_SETS if own & set(G.cpu_list(x))]


def cpuset_budget_s(node: dict) -> float:
    """The determinism check's timing bound for a replacement set: the slowest run of every attempt within the audit
    chunk's per-run budget (census run time x 1.25 x 1.5, ``g5_job.chunk_plan``), the tightest of the node's G.5
    deadlines (the engine's run timeout is 3 x the slowest census run)."""
    return round(float(node["run_seconds"]) * 1.25 * 1.5, 3)


def tasl2_node_cpus(spec: dict, node: str) -> str:
    """The node's CPU set on TASL-2: its R1-TASL2-CPU replacement, else its own set, else the worker's."""
    rep = (spec["tasl2_cpus"]["replacements"]).get(node)
    return rep["cpus"] if rep else (node_entry(spec, node).get("cpus") or spec["worker"]["cpus"])


def validate_spec(spec: dict, *, launch: bool = False) -> dict:
    """The spec schema and its consistency with the decisions. Returns the options, the projection, the unsigned
    decisions and the launch blockers; ``launch=True`` raises on any blocker or unfilled field."""
    allow = not launch
    if spec.get("schema") != SCHEMA or spec.get("label") != EVIDENCE:
        raise Stop(f"STOP: spec must be {SCHEMA}, label {EVIDENCE}")
    run_id = spec.get("run_id")
    if not (_ph(run_id) and allow) and not (isinstance(run_id, str) and RUN_ID.fullmatch(run_id)):
        raise Stop("STOP: run_id must be c3_t1_labels_<YYYYMMDD>")
    for key, repo in (("paper", L.PAPER_REPO), ("harness", L.HARNESS_REPO)):
        if (spec.get(key) or {}).get("repo") != repo:
            raise Stop(f"STOP: {key}.repo must be {repo}")
    L._commit(spec["paper"].get("commit"), "paper.commit", allow_placeholder=allow)
    # --- decisions
    dec = spec.get("decisions") or {}
    if sorted(dec) != sorted(DECISIONS):
        raise Stop(f"STOP: decisions must be exactly {list(DECISIONS)} (§11 items 1-8)")
    for key in DECISIONS:
        d = dec[key]
        if d.get("options") != OPTIONS[key] or d.get("recommended") != "A" or d.get("option") not in OPTIONS[key] \
                or not isinstance(d.get("signed"), bool):
            raise Stop(f"STOP: decisions.{key} must carry option in {OPTIONS[key]}, recommended A, signed true/false")
    o = options(spec)
    unsigned = [k for k in DECISIONS if not dec[k]["signed"]]
    if o["G5-SLOT"] == "B":
        raise Stop("STOP: G5-SLOT B (audits on TASL-7 while campaigns pause, a server restart per wave) is not built "
                   "(G.5 draft §2.10); R1-G5-AUDIT-TWO-CARDS amends G5-SLOT A instead (tasl7_audits)")
    if o["G5-MEM"] == "C":
        raise Stop("STOP: G5-MEM C is not built: the draft gives no assignment of the split file's 12 instances to two "
                   "memory modes of 6 each, and C contradicts R1-BX-D8-V3-B (12 instances per node); an author row "
                   "would have to fix both first (G.5 draft §2.3)")
    bad = {"/".join(p): (_get(spec, p), v) for p, v in required_settings(spec).items() if _get(spec, p) != v}
    if bad:
        raise Stop(f"STOP: fields inconsistent with the chosen options (use apply_options): {bad}")
    blockers = []
    pb = spec.get("pilot_basis") or {}
    g4 = g4_spec()                       # the signed G.4 note's proposer, environments and sealed root (below)
    pilot, _ = check_pilot_basis(spec)                                              # P3: the G.4b re-pilot
    ran = pilot_settings(pilot)
    for field, want in (("W_semantics", spec["campaign"]["W_semantics"]), ("W", spec["campaign"]["W"]),
                        ("memory_modes", spec["memory"]["modes"]), ("temperature", spec["campaign"]["temperature"])):
        if ran[field] != want:
            blockers.append(f"P3: the G.4b re-pilot {pilot['run_id']} ({PILOT_SPEC_REL}) ran {field} = "
                            f"{ran[field]!r}, the options need {want!r}: the re-pilot is re-run or amended first (a "
                            f"re-issued G.4b spec)")
    if o["G5-W"] == "B":
        blockers.append("G5-W B: the v2-diff engine has no worker-run budget with an LLM-call cap (harness code "
                        "unit, G.5 draft §9); not built")
    # --- harness families, identity, environments
    g1b = {fam: _check_family(spec, fam, launch, o) for fam in FAMILIES}
    dirs = [spec["harness_families"][f]["harness_dir"] for f in FAMILIES]
    if len(set(dirs)) != 2:
        raise Stop("STOP: the two G.5 harness families need two checkouts (G5-PIN B)")
    if spec.get("gpu_model") != GPU_MODEL or spec.get("model") != T4.MODEL:
        raise Stop("STOP: gpu_model must be the RTX 4090 and model the pinned gemma4_31b GGUF")
    if (spec.get("timeout_decision") or {}).get("basis") != g1b["G5-7"]["timeout_decision"]["basis"] or \
            not str(spec["timeout_decision"].get("authority", "")).startswith("R1-G1B-TIMEOUT"):
        raise Stop("STOP: timeout_decision must be census_slowest_x3 under R1-G1B-TIMEOUT (one basis for the table)")
    if not str((spec.get("host_decision") or {}).get("authority", "")).startswith("R1-T1-TASL-ENV"):
        raise Stop("STOP: host_decision.authority must be R1-T1-TASL-ENV")
    w = spec.get("worker") or {}
    ref = g1b["G5-7"]["hosts"][WORKER_HOST]
    if w.get("host") != WORKER_HOST or w.get("hostname") != ref["hostname"] or w.get("gpu_uuid") != ref["gpu_uuid"] \
            or w.get("driver") != DRIVERS["worker"] or w.get("lease") != "~/r1_locks/gpu0.lock":
        raise Stop("STOP: the worker is TASL-2 with the RTX 4090, driver and lease of the G.1b spec")
    for key in ("base", "runs_root", "sealed_root", "uv"):
        G._abs(w.get(key), f"worker.{key}")
    if w["sealed_root"] in (ref["sealed_root"], g4["worker"]["sealed_root"]):
        raise Stop("STOP: worker.sealed_root must be G.5's own (not G.1b's or G.4's)")
    G.cpu_list(w.get("cpus", ""))
    p = spec.get("proposer") or {}
    for key in ("host", "hostname", "gpu_uuid", "tailscale_address", "server_url", "binary", "binary_sha256",
                "expected_build", "model_path", "lease", "args", "bin_dir_manifest_sha256"):
        if p.get(key) != g4["proposer"][key]:
            raise Stop(f"STOP: proposer.{key} must equal the G.4 spec's (the server of the signed G.4 note)")
    T4.server_url_parts(p["server_url"])
    G._abs(p.get("run_dir"), "proposer.run_dir")
    if p["run_dir"] == g4["proposer"]["run_dir"] or p.get("driver") != DRIVERS["proposer"] or \
            not isinstance(p.get("server_stopped_during_audits"), bool):
        raise Stop("STOP: proposer.run_dir must be G.5's own, driver 580.178.04, server_stopped_during_audits a bool")
    G._abs(p.get("sealed_root"), "proposer.sealed_root")          # part 3b-2: the TASL-7 server seal
    run_dir, prop_sealed = Path(p["run_dir"]), Path(p["sealed_root"])
    if prop_sealed == run_dir or run_dir in prop_sealed.parents or prop_sealed in run_dir.parents:
        raise Stop("STOP: proposer.sealed_root must be apart from proposer.run_dir (the server seal, part 3b-2)")
    if sorted(json.loads((REPO_ROOT / XC_SPEC).read_text())["nodes"]) != sorted(X_NODES):
        raise Stop("STOP: the cross-check spec's TASL-7 nodes are not the three xc2 nodes")
    tasl7 = _check_tasl7(spec, launch, g1b["G5-7"])                 # R1-G5-AUDIT-TWO-CARDS
    envs = dict(spec.get("envs") or {})
    prop_env = spec["ar_prerequisites"]["proposed_environment"]
    ar_env_ref = json.loads((REPO_ROOT / FAMILY_SPECS["G5-AR"]).read_text())["envs"]
    if {k: v for k, v in envs.items() if k != prop_env["name"]} != g4["envs"]:
        raise Stop("STOP: envs must be the census freezes torch312 and jax312 of R1-T1-TASL-ENV")
    if o["G5-ARPEND"] == "A" and prop_env["name"] in envs:
        raise Stop("STOP: under G5-ARPEND A autoresearch's environment comes from the completion record, not envs")
    if o["G5-ARPEND"] == "B" and envs.get(prop_env["name"]) != {k: prop_env[k] for k in ("freeze", "sha256",
                                                                                         "python")}:
        raise Stop("STOP: under G5-ARPEND B envs must carry autoresearch's environment (the proposed one)")
    ref_env = ar_env_ref.get(prop_env.get("name")) or {}
    if prop_env.get("name") != G.AR_ENV or any(prop_env.get(k) != ref_env.get(k) for k in ("freeze", "sha256",
                                                                                          "python")):
        raise Stop("STOP: ar_prerequisites.proposed_environment must be ar-cond7a as in the AR G.1b spec (P9)")
    # --- campaign, memory, audit, divergence
    c = spec.get("campaign") or {}
    if c.get("proposal_schema") != "manager_proposal/v2-diff" or c.get("cache_prompt") is not False \
            or c.get("max_tokens") != g4_lib.MAX_TOKENS or c.get("ctx") != T4.CTX or c.get("per_call_seed_rule") != SEED_RULE:
        raise Stop("STOP: campaign must be manager_proposal/v2-diff, cache_prompt false, cap 4096, ctx 32768, and the "
                   "engine's per-call seed rule")
    a = spec.get("audit") or {}
    if not isinstance(a.get("reuse_parent_runs"), bool) or \
            a.get("duplicate_key") != "instance, incumbent hash, candidate hash":
        raise Stop("STOP: audit.reuse_parent_runs must be a bool and the duplicate key R1-MAIN-PROPOSER (e)'s")
    _check_seeds(spec)
    split = _check_split(spec)
    d = spec.get("divergence") or {}
    if d != {**divergence_block(o["G5-DIV"], pb["nodes"]), **{k: d.get(k) for k in ("pilot_counts",
                                                                                   "g1b_divergent_rows") if k in d}}:
        raise Stop("STOP: the divergence block is not the one of the chosen G5-DIV option (§2.5)")
    if o["G5-DIV"] == "B" and sorted(d.get("pilot_counts") or {}) != sorted(pb["nodes"]):
        raise Stop("STOP: G5-DIV B needs pilot_counts for exactly the pilot nodes")
    if o["G5-DIV"] == "C" and sorted(d.get("g1b_divergent_rows") or {}) != sorted(T1_NODES):
        raise Stop("STOP: G5-DIV C needs g1b_divergent_rows for exactly the eight nodes")
    if o["G5-DIV"] in ("B", "C"):
        for n in (pb["nodes"] if o["G5-DIV"] == "B" else T1_NODES):
            try:
                divergence_threshold(spec, n)
            except Stop as exc:
                blockers.append(str(exc))
    # --- nodes
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or [n.get("node") for n in nodes] != list(T1_NODES):
        raise Stop(f"STOP: nodes must be the eight T1 nodes {list(T1_NODES)} (G5-AR A, R1-G5-DECISIONS)")
    on_4090 = T4.census_on_4090_nodes()
    for n in nodes:
        fam = "G5-AR" if n["node"] == AR else "G5-7"
        if n.get("family") != fam:
            raise Stop(f"STOP: {n['node']} runs on harness family {fam} (G5-PIN B)")
        r = {x["node"]: x for x in g1b[fam]["nodes"]}.get(n["node"])
        for key in ("spec_path", "node_dir", "node_spec_sha256", "committed_pin_sha256", "data_manifest_sha256",
                    "run_seconds", "slowest_census_seconds", "census_record", "device", "cpus"):
            if n.get(key) != r.get(key):
                raise Stop(f"STOP: {n['node']}.{key} differs from its G.1b spec")
        if n.get("census_gpu_model") != (GPU_MODEL if n["node"] in on_4090 else ADA_MODEL):
            raise Stop(f"STOP: {n['node']}.census_gpu_model does not match the G.1b specs")
        if n["node"] == AR and o["G5-ARPEND"] == "A":
            if n.get("env") != AR_PENDING or n.get("tails") != AR_PENDING:
                raise Stop("STOP: under G5-ARPEND A autoresearch's env and tails are the PENDING marker (§2.13)")
            if TAILS_NU in n:
                raise Stop(f"STOP: under G5-ARPEND A autoresearch's {TAILS_NU} comes from the completion record, not "
                           f"the spec (§2.13)")
            continue
        if n.get("env") != r["env"]:
            raise Stop(f"STOP: {n['node']}.env must be its G.1b environment {r['env']}")
        if n["env"] not in envs or n["env"] not in (w.get("env_python") or {}):
            raise Stop(f"STOP: {n['node']} needs {n['env']} in envs and worker.env_python")
        if n.get("tails") not in TAILS and not (allow and _ph(n.get("tails"))):
            raise Stop(f"STOP: {n['node']}.tails must be gaussian or student_t (P10)")
        check_tails_nu(n, allow=allow)
    for name, py in (w.get("env_python") or {}).items():
        G._abs(py, f"worker.env_python.{name}")
    tasl2_cpus = _check_tasl2_cpus(spec)                                  # R1-TASL2-CPU
    # --- noise floor, autoresearch's prerequisites
    nf = spec.get("noise_floor") or {}
    if nf.get("t1_sigma_node") != T1_SIGMA_NODE:
        raise Stop(f"STOP: noise_floor.t1_sigma_node must be {T1_SIGMA_NODE!r} (R1-T1-FEAT-DECISIONS D6-σ B: T1's "
                   f"σ_node by dataset.noise_table's definition on the copied G.1b runs)")
    for key, fam, schema in (("seven", "G5-7", G.SUMMARY_SCHEMA), ("ar", "G5-AR", G.AR_SUMMARY_SCHEMA)):
        e = nf.get(key) or {}
        if e.get("run_id") != spec["harness_families"][fam]["g1b_spec"]["run_id"] or e.get("schema") != schema:
            raise Stop(f"STOP: noise_floor.{key} must be the {schema} summary of run "
                       f"{spec['harness_families'][fam]['g1b_spec']['run_id']}")
        if key == "ar" and o["G5-ARPEND"] == "A":
            if any(e.get(k) != AR_PENDING for k in ("copy", "sha256", "review", "sealed_path", *RUN_COPY_KEYS)):
                raise Stop("STOP: under G5-ARPEND A noise_floor.ar is the PENDING marker (§2.13)")
            continue
        for k in ("assembly_sha256", "runs_sha256"):                # D6 A: the run's copies beside the summary copy
            L._sha(e.get(k), f"noise_floor.{key}.{k}", allow_placeholder=allow)
        if launch and any(e.get(k) != (Path(str(e.get("copy"))).parent / name).as_posix()
                          for k, name in (("assembly_copy", "ASSEMBLY.json"), ("runs_copy", "runs.jsonl"))):
            raise Stop(f"STOP: noise_floor.{key}.assembly_copy and runs_copy must be ASSEMBLY.json and runs.jsonl "
                       f"beside the summary copy (D6 A, R1-T1-FEAT-DECISIONS)")
        if launch and (not _rel_ok(e.get("copy")) or not _rel_ok(e.get("review"))):
            raise Stop(f"STOP: noise_floor.{key} must name its reviewed REL-T1-G1B copy and review")
        if launch and not str(e.get("sealed_path", "")).startswith("/"):
            raise Stop(f"STOP: noise_floor.{key}.sealed_path must be the sealed summary's absolute path")
        L._sha(e.get("sha256"), f"noise_floor.{key}.sha256", allow_placeholder=allow)
        if key == "seven":           # M3: the cross-check gate record travels with the seven-node copy
            xs = e.get("crosscheck_spec") or {}
            if xs.get("path") != XC_SPEC or xs.get("sha256") != _repo_file_sha(XC_SPEC):
                raise Stop(f"STOP: noise_floor.seven.crosscheck_spec must be {XC_SPEC} at its sha256 in the checkout")
            L._sha(e.get("gate_sha256"), "noise_floor.seven.gate_sha256", allow_placeholder=allow)
            if launch and (not _rel_ok(e.get("gate_copy")) or
                           Path(e["gate_copy"]) != Path(e["copy"]).parent / "crosscheck_gate.json"):
                raise Stop("STOP: noise_floor.seven.gate_copy must be crosscheck_gate.json beside the summary copy")
    ap = spec.get("ar_prerequisites") or {}
    if ap.get("node") != AR or ap.get("record_dir") != "docs/r1/reports" or \
            ap.get("record_name") != "G5_AR_PREREQUISITES_YYYYMMDD.md" or \
            ap.get("pending") != (AR_PENDING_ITEMS if o["G5-ARPEND"] == "A" else []):
        raise Stop("STOP: ar_prerequisites must name autoresearch, the record pattern and the PENDING items of "
                   "the chosen G5-ARPEND option")
    # --- key values, cap, gate, preregistration, rows
    kv = spec.get("key_values") or {}
    for key in ("liveness_floor", "invalid_share_stop", "infrastructure_stop_share"):
        if not isinstance(kv.get(key), (int, float)) or isinstance(kv[key], bool) or not 0 < kv[key] < 1:
            raise Stop(f"STOP: key_values.{key} must be a share in (0, 1)")
    try:
        deadline = date.fromisoformat(str(kv.get("freeze_wait_release_date")))
    except ValueError:
        raise Stop("STOP: key_values.freeze_wait_release_date must be an ISO date") from None
    tr = kv.get("t1_table_readings") or {}
    if set(tr) != {"campaign_divergent_delta_hat", "options"} or tr.get("options") != list(DELTA_HAT_OPTIONS) or \
            tr["campaign_divergent_delta_hat"] not in DELTA_HAT_OPTIONS:
        raise Stop(f"STOP: key_values.t1_table_readings.campaign_divergent_delta_hat must be one of {DELTA_HAT_OPTIONS} "
                   f"(part 3b-2; the author signs it in the note's t1_table_readings line)")
    if kv.get("server_log") not in SERVER_LOG:
        raise Stop("STOP: key_values.server_log must be 'a' (the server seal); option (b), prompt logging off, changes "
                   "server_argv and is not built")
    if kv.get("seal_mode") != "procedural":
        raise Stop("STOP: key_values.seal_mode: only the procedural seal is built (the encryption alternative needs "
                   "cluster test C6 and its own code; G.5 draft §6)")
    cuda = kv.get("cuda_ipc") or {}
    if set(cuda) != {"mode", *CUDA_C12_HOSTS["TASL-2"], *CUDA_C12_HOSTS["TASL-7"]}:
        raise Stop(f"STOP: key_values.cuda_ipc must carry mode and, per host, its C12 record, sha256 and review "
                   f"({sorted(k for v in CUDA_C12_HOSTS.values() for k in v)}; P1)")
    if cuda.get("mode") == "c12":
        for host, (rk, sk, vk) in CUDA_C12_HOSTS.items():
            if host == AUDIT_HOST and cuda.get(rk) is None:
                if cuda.get(sk) is not None or cuda.get(vk) is not None:
                    raise Stop(f"STOP: cuda_ipc.{sk} and {vk} need {rk} (P1)")
                continue                     # no C12 on TASL-7: its audit chunks are refused under c12 (check_c12)
            if not _rel_ok(cuda.get(rk)) or not str(cuda[rk]).startswith("docs/r1/reports/"):
                raise Stop(f"STOP: cuda_ipc c12 needs its record under docs/r1/reports/ ({rk})")
            L._sha(cuda.get(sk), f"key_values.cuda_ipc.{sk}", allow_placeholder=False)
            if cuda.get(vk) is not None and (not _rel_ok(cuda[vk]) or not cuda[vk].startswith("docs/r1/reviews/")):
                raise Stop(f"STOP: cuda_ipc.{vk} must be a review under docs/r1/reviews/ (or null)")
    elif cuda.get("mode") != "acceptance" and not (allow and _ph(cuda.get("mode"))):
        raise Stop("STOP: key_values.cuda_ipc.mode must be c12 or acceptance (P1)")
    elif any(cuda.get(k) is not None for v in CUDA_C12_HOSTS.values() for k in v):
        raise Stop("STOP: the C12 fields are for cuda_ipc.mode c12 only (null otherwise; P1)")
    cap = kv.get("cap_gpu_hours")
    if not isinstance(cap, (int, float)) or isinstance(cap, bool) or cap <= 0:
        raise Stop("STOP: key_values.cap_gpu_hours must be positive")
    proj = projection(spec)
    low, high = proj["share=0.6 K=10"]["capped_gpu_hours"], proj["share=0.8 K=10"]["capped_gpu_hours"]
    if low > cap:
        raise Stop(f"STOP: the chosen options project {low} GPU-h at ran share 0.6 (K = 10) above the cap {cap}: "
                   f"they need the cap of their row, which the signature fixes (§2.6, §11 item 9)")
    p7 = (spec.get("projection") or {}).get("gpu_hours_p7")
    if not (allow and _ph(p7)) and not (isinstance(p7, (int, float)) and not isinstance(p7, bool) and 0 < p7 <= cap):
        raise Stop("STOP: projection.gpu_hours_p7 must be the P7 recompute, within the cap")
    p3_total = pb["dates"]["g5_total_gpu_hours"]
    if not _ph(p7) and p7 != p3_total:
        raise Stop(f"STOP: projection.gpu_hours_p7 ({p7}) must be the R1-BX-D14 recompute's g5_total_gpu_hours on the "
                   f"sealed G.4b summaries, pilot_basis.dates ({p3_total}) (P7, §8)")
    if spec.get("gate") != GATE or _repo_file_sha(GATE["path"]) != GATE["sha256"]:
        raise Stop("STOP: gate must be r1/c3/gate.py v3.1 (sha256 a3f7d002…), as in the checkout")
    pr = spec.get("preregistration") or {}
    if pr.get("path") != "docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md" or \
            pr.get("sha256") != PREREG_SHA256 or _repo_file_sha(pr["path"]) != PREREG_SHA256:
        raise Stop("STOP: preregistration must be the frozen C3_SWEEP2_ANALYSIS_PREREG_20261121.md (sha256 aa1a961b…)")
    rows = {"decisions_row": spec.get("decisions_row"), "e4_amendment_row": spec.get("e4_amendment_row")}
    if o["G5-MEM"] != "A" and rows["e4_amendment_row"] is not None:
        raise Stop("STOP: e4_amendment_row is only for G5-MEM A (null otherwise)")
    for key, value in rows.items():
        if key == "e4_amendment_row" and o["G5-MEM"] != "A":
            continue
        if not (allow and _ph(value)) and not (isinstance(value, str) and ROW_ID.fullmatch(value)):
            raise Stop(f"STOP: {key} must be a PLAN row id")
    if launch:
        if unsigned:
            raise Stop(f"STOP: decisions not signed: {unsigned} (§11; the author's row signs them)")
        if blockers:
            raise Stop("STOP: the chosen options cannot launch: " + "; ".join(blockers))
        if cuda.get("mode") not in ("c12", "acceptance"):
            raise Stop("STOP: key_values.cuda_ipc.mode must be c12 or acceptance before launch (P1)")
    return {"spec": spec, "run_id": run_id, "options": o, "unsigned": unsigned, "launch_blockers": blockers,
            "projection": proj, "cap_gpu_hours": cap, "share_0_8_with_margin": round(high * 1.1, 1),
            "audited_band": kv["audited_band"], "freeze_wait_release_date": deadline.isoformat(), "split": split,
            "e4_amendment_needed": o["G5-MEM"] == "A",
            "divergence_denominator_weaker": o["G5-AUDIT"] == "B",
            "tasl7_pending_crosshost": tasl7["pending_crosshost"], "tasl2_cpu_replacements": tasl2_cpus,
            "pilot_basis_run_id": pilot["run_id"]}


# =============================================================================================== the note (§5)
def _range(block: list[int]) -> str:
    return f"{block[0]}-{block[1]}"


def note_lines(spec: dict, *, k: int = 10, k_row: str | None = None, freeze: str | None = None,
               freeze_row: str | None = None) -> dict:
    """Every key line of the signed note (§5, plus the §11 values), rendered from the spec. ``check_note`` requires
    each verbatim; ``audit_K`` and the two seed lines follow the note's K (P4), and ``freeze_wait`` the note's date
    (the spec's, or a later one moved by a docs-only amendment citing an author row)."""
    o = options(spec)
    w, p = spec["worker"], spec["proposer"]
    fam = spec["harness_families"]
    nodes = spec["nodes"]
    a_mode = o["G5-ARPEND"] == "A"
    record = "docs/r1/reports/*/G5_AR_PREREQUISITES_YYYYMMDD.md"
    pe = spec["ar_prerequisites"]["proposed_environment"]
    ar_env = (f"autoresearch: from the completion record {record} (G5-ARPEND A; proposed {pe['name']} "
              f"sweep2/g1b/{pe['freeze']} {pe['sha256']}, Python {pe['python']})" if a_mode else
              f"{pe['name']} sweep2/g1b/{pe['freeze']} {pe['sha256']} (Python {pe['python']}; autoresearch only)")
    names = []
    for n in nodes:
        suffix = " (CPU-only)" if n["device"] == "cpu" else " (G5-AR A, R1-G5-DECISIONS)" if n["node"] == AR else ""
        names.append(n["node"] + suffix)
    seeds = spec["audit"]["seed_blocks"][str(k)]
    if k == 10:
        k_line = ("10 (R1-G5-DECISIONS; K = 6 only after a published K-check author row, by a docs-only amendment of "
                  "this line and the two seed lines citing that row)")
    else:
        k_line = f"6 (K-check row {k_row}; R1-G5-DECISIONS; docs-only amendment of the signed note)"
    modes = spec["memory"]["modes"]
    nf = spec["noise_floor"]
    seven = (f"seven nodes: {nf['seven']['copy']} sha256 {nf['seven']['sha256']} with its cross-check gate record "
             f"{nf['seven'].get('gate_copy')} sha256 {nf['seven'].get('gate_sha256')} (REL-T1-G1B copy of "
             f"{nf['seven']['run_id']}, joined under G1B-JOIN behind the cross-check gate)")
    ar_nf = (f"autoresearch: from the completion record {record} (G5-ARPEND A)" if a_mode else
             f"autoresearch: {nf['ar']['copy']} sha256 {nf['ar']['sha256']} (REL-T1-G1B copy of {nf['ar']['run_id']})")
    kv = spec["key_values"]
    band = kv["audited_band"]
    div = spec["divergence"]
    div_line = {"fixed": f"G5-DIV A: {div.get('threshold')} of the audited label proposals, E5 on the label seeds, "
                         f"from {div['min_audited']} audited, at the end of each wave's audits; the literal "
                         f"2 x census ({div.get('literal_2x_census')}) kept, it never binds below "
                         f"{div.get('threshold')}",
                "pilot_cp": f"G5-DIV B: min({div.get('cap')}, max(2 x the upper limit of the two-sided "
                            f"{round(100 * div.get('cp_level', 0))} % Clopper-Pearson interval (upper tail "
                            f"{round(50 * (1 - div.get('cp_level', 0)), 2)} %) of the pilot's divergent share, "
                            f"{div.get('floor')})) for the pilot nodes, "
                            f"{div.get('other_nodes')} for the others, on the audited label proposals from "
                            f"{div['min_audited']}",
                "g1b_2x": f"G5-DIV C: min({div.get('cap')}, 2 x the node's G.1b divergent-row rate), on the audited "
                          f"label proposals from {div['min_audited']}"}[div["rule"]]
    cuda = kv["cuda_ipc"]
    t7 = spec["tasl7_audits"]
    xc_parts = []
    for n in SEVEN:
        e = t7["crosshost_pass"][n]
        xc_parts.append(f"{n} {e}" if isinstance(e, str) else
                        f"{n} " + " and ".join(f"{x['record']} sha256 {x['sha256']} ({x['mode']})" for x in e))
    t2 = spec["tasl2_cpus"]
    reps = t2["replacements"]
    tasl2_line = (f"{TASL2_CPU_ROW}: no G.5 job on TASL-2 uses CPUs 8-11 (stability record "
                  f"{t2['stability_record']['path']} sha256 {t2['stability_record']['sha256']}); GPU jobs on cpus "
                  f"{w['cpus']}; " + "; ".join(f"{n} on cpus {r['cpus']} in place of its G.1b set {r['g1b_cpus']} "
                                               f"(same size; its TASL-7 audit chunks keep {r['g1b_cpus']})"
                                               for n, r in reps.items())
                  + "; every G.5 job on TASL-2 holds the TASL-2 lease ~/r1_locks/gpu0.lock, so G.5 jobs sharing CPUs "
                    "never overlap one another; the expansion G.1b's CPU jobs take only their CPU-set leases "
                    "~/r1_locks/cpus-<set>.lock, not that lease, and overlap with them is governed by the schedule the "
                    "note fixes (draft section 11.1 S13)")
    checks = []
    for n, r in reps.items():
        ref = cpuset_reference(n)
        checks.append(
            f"{n} on cpus {r['cpus']}: before its first TASL-2 job the switch requires the one record "
            f"docs/r1/reports/DIR/{CPUSET_TOKEN}{n}_YYYYMMDD.json on main ({CPUSET_SCHEMA}, written by g5_tasl.py "
            f"cpuset-verdict); procedure: on TASL-2, {CPUSET_REPEATS} sealed attempts of the node's G.1b default part "
            f"(c0..cN, default and default_repeat, the G.1b seeds) under the derived spec of g5_tasl.py cpuset-spec "
            f"(run tasl2-cpuset-{n}-YYYYMMDD), each by sweep2/t1_tasl/dry_run_node.py in the delegated 8G scope "
            f"pinned to cpus {r['cpus']}, the operator holding by flock the TASL-2 lease ~/r1_locks/gpu0.lock (a "
            f"CPU node's G.1b job takes no lease) and, while expansion G.1b jobs run, the CPU-set leases "
            f"{' and '.join(expansion_leases(r['cpus'])) or 'none'}; PASS: every attempt complete and deterministic "
            f"with affinity {r['cpus']}, every outcome bit-identical to the sealed G.1b TASL-2 attempt "
            f"{ref['attempt']} (job_record sha256 {ref['job_record_sha256']}), and every run within "
            f"{cpuset_budget_s(node_entry(spec, n))} s (census run time x 1.25 x 1.5); otherwise the node's TASL-2 "
            f"jobs are refused and the author decides")
    cpuset_line = "; ".join(checks) if checks else "none (no TASL-2 CPU set of this spec contains CPUs 8-11)"
    lines = {
        "label": EVIDENCE,
        "run_id": spec["run_id"],
        "hosts": f"worker TASL-2 (RTX 4090 {w['gpu_uuid']}, driver {w['driver']}), proposer TASL-7 (RTX 4090 "
                 f"{p['gpu_uuid']}, driver {p['driver']}) over Tailscale {p['server_url']}; TASL-7's card also runs "
                 f"G.5 audit chunks while no campaign wave holds the server ({TWO_CARDS_ROW})",
        "host_authority": "R1-T1-HOST-TASL; environment row R1-T1-TASL-ENV; for autoresearch, R1-G1B-AR-ENV's "
                          "ar-cond7a (amended by R1-G1B-AR-PY) extended to its G.5 jobs by this note (P9)",
        "environments": f"torch312 {spec['envs']['torch312']['sha256']}, jax312 {spec['envs']['jax312']['sha256']} "
                        f"(census freezes, Python 3.12.16); {ar_env}",
        "llama_server_sha256": f"{p['binary_sha256']}; build {p['expected_build']}; build-directory manifest "
                               f"{p['bin_dir_manifest_sha256']} (as in the signed G.4 note)",
        "gguf_sha256": spec["model"]["sha256"],
        "harness_commit": f"G5-7 {fam['G5-7']['g5_commit']} (seven nodes); G5-AR {fam['G5-AR']['g5_commit']} "
                          f"(autoresearch); g5_pin_check.py PASS on the pair (G5-PIN B, R1-G5-DECISIONS); per family, "
                          f"the measurement path byte-identical to its G.1b pin (P5)",
        "g1b_harness_commit": f"{fam['G5-7']['g1b_pin']} (seven nodes); {fam['G5-AR']['g1b_pin']} (autoresearch)",
        "gpu_model": f"{GPU_MODEL} (one table, one GPU model: campaigns on TASL-2 with the server on TASL-7; audit "
                     f"chunks on TASL-2, and on TASL-7 under {TWO_CARDS_ROW}; each job record checks the card's model)",
        "nodes": ",".join(names),
        "data_manifests": ", ".join(f"{n['node']} {n['data_manifest_sha256'] or 'none'}" for n in nodes)
                          + "; each equal to the node's G.1b spec (R1-T1-TASL-ENV; R1-T1-DATA-MANIFEST for "
                            "mlgym_fmnist and mlgym_cifar10)",
        "instances_per_node": (f"{spec['memory']['instances_per_mode']} per memory mode ({', '.join(modes)})"
                               if len(modes) > 1 else f"{spec['memory']['instances_per_mode']} (memory mode {modes[0]})"),
        "instance_seeds": f"{_range(spec['instances']['seeds'])} ({spec['instances']['rule']})",
        "instance_split": f"{spec['instances']['split_file']['path']} sha256 {spec['instances']['split_file']['sha256']} "
                          f"(R1-SWEEP2-PREREG, PRE-SPLIT A; rule of §2.7)",
        "memory_mode": f"{' and '.join(modes)} (G5-MEM {o['G5-MEM']})",
        "campaign_W": ("20 manager calls (G5-W A)" if o["G5-W"] == "A" else
                       f"20 worker runs with an LLM-call cap of {spec['campaign']['llm_call_cap']} (G5-W B)"),
        "proposer": "gemma4_31b (thinking off; exam flags; context 32768; cache_prompt false)",
        "temperature": f"{spec['campaign']['temperature']} (G5-TEMP {o['G5-TEMP']}); per-call seed {SEED_RULE}",
        "completion_cap_tokens": str(spec["campaign"]["max_tokens"]),
        "proposal_schema": spec["campaign"]["proposal_schema"],
        "timeout_basis": "census_slowest_x3 (R1-G1B-TIMEOUT)",
        "audit_K": k_line,
        "audit_seeds_label": _range(seeds["label"]),
        "audit_seeds_evaluation": _range(seeds["evaluation"]),
        "audit_scope": (f"G5-AUDIT {o['G5-AUDIT']}: {spec['audit']['scope']}; reuse_parent_runs "
                        f"{str(spec['audit']['reuse_parent_runs']).lower()}; E5 on the label seeds only; duplicate key "
                        f"({spec['audit']['duplicate_key']}); cross-instance groups audited once; gate repeats per "
                        f"PRE-DUP A"),
        "divergence_stop": div_line,
        "liveness_floor": str(kv["liveness_floor"]),
        "invalid_share_stop": str(kv["invalid_share_stop"]),
        "infrastructure_stop": str(kv["infrastructure_stop_share"]),
        "audited_band": f"{band[0]}-{band[1]} per node (G5-W {o['G5-W']}, G5-MEM {o['G5-MEM']})",
        "noise_floor": f"{seven}; {ar_nf}; joined by node (g1b_tasl_join.py floor-by-node; the split file's eight "
                       f"T1 nodes)",
        "tails": ", ".join(f"{n['node']} " + ("from the completion record (G5-ARPEND A)"
                                              if n["node"] == AR and a_mode else tails_text(n)) for n in nodes),
        "job_layout": f"per node in sequence (G5-SLOT A as amended by {TWO_CARDS_ROW}), wave 1 (instances 1-4) "
                      f"campaigns then audits, wave 2 (instances 5-12) campaigns then audits; audits in chunks with "
                      f"declared deadlines; campaign waves on TASL-2's one worker slot with the server on TASL-7; a "
                      f"wave's plan and its last chunk (E5) on TASL-2; other chunks on TASL-2, or on TASL-7 once claimed "
                      f"on TASL-2 (one open claim at a time), and registered on TASL-2 before they count; the schedule "
                      f"is fixed by this note",
        "tasl7_audits": f"TASL-7 host check {t7['isolation_host_check']['record']} sha256 "
                        f"{t7['isolation_host_check']['sha256']}; G5-7 checkout {t7['harness_dir']} (autoresearch's "
                        f"audits stay on TASL-2); lease {t7['lease']} (the server's); per node the cross-host PASS "
                        f"before its first TASL-7 audit chunk (an xc3 short-check node's PASS is the one file "
                        f"docs/r1/reports/DIR/{SHORT_XC_TOKEN}NODE_YYYYMMDD.json on main, mode short, bound below by "
                        f"sha256 or, for a node marked PENDING, found by that name; with XC3-FAIL from the signed xc3 "
                        f"note or {XC3_ROW} on main: A, without a PASS the node runs on TASL-2 only; B, a STOP verdict "
                        f"is STOP 5 for the node; skip_nodes stay on TASL-2): " + "; ".join(xc_parts),
        "tasl2_cpus": tasl2_line,
        "tasl2_cpuset_check": cpuset_line,
        "t1_node_scope": f"every T1 node that passed U2, G.1b fixed-seed determinism and, where run, the cross-host "
                         f"check, whatever its D21 value ({D21_SCOPE_ROW}); each node's D21 value is recorded for the "
                         f"screening funnel (R1-BX-D12), not a STOP",
        "launch": "the TASL launch binding (LB A of R1-G1B-TASL-DECISIONS, as G4-LB A): a published checkout at or "
                  "after the commit that publishes this note and the spec, code equal to paper_commit outside docs/ "
                  "and the spec",
        "gpu_hours": f"{spec['projection']['gpu_hours_p7']} (P7, post-pilot recompute)",
        "cap_gpu_hours": f"{kv['cap_gpu_hours']}, counted per " + (
            f"the worker card (G5-TASL-GPUH A), the hours of G.5 audit chunks on TASL-7 included ({TWO_CARDS_ROW})"
            if o["G5-TASL-GPUH"] == "A" else
            "both cards (G5-TASL-GPUH B, server stopped during audits)"),
        "proposer_card_hours": "metered and reported",
        "cuda_ipc": (f"C12 PASS: {cuda.get('c12_record')} sha256 {cuda.get('c12_sha256')} (TASL-2); "
                     + (f"C12 PASS: {cuda.get('c12_tasl7_record')} sha256 {cuda.get('c12_tasl7_sha256')} (TASL-7 audit "
                        f"chunks)" if cuda.get("c12_tasl7_record") else
                        f"no C12 record for TASL-7: no G.5 audit chunk runs on TASL-7 ({TWO_CARDS_ROW})")
                     if cuda.get("mode") == "c12"
                     else "the acceptance line cuda_ipc_acceptance, signed (TASL-2 and TASL-7's audit chunks)"),
        "freeze_wait": f"the arms-frozen record waits for the train/dev release of every un-STOPped T1 node of this "
                       f"table until {freeze or kv['freeze_wait_release_date']}"
                       + (f" (moved by author row {freeze_row})" if freeze_row else "")
                       + "; no G.5 job starts on or after this date (STOP 14)",
        "ar_prerequisites": (f"PENDING until the completion record {record} (G5-ARPEND A; STOP 15)" if a_mode else
                             "PASS, cited in noise_floor, environments, tails and P1 (G5-ARPEND B)"),
        "gate": f"{GATE['path']} @ {GATE['commit']} sha256 {GATE['sha256']} (v3.1, R1-BX-D8-CONFIRM-V31)",
        "preregistration": f"{spec['preregistration']['path']} sha256 {spec['preregistration']['sha256']} (frozen)",
        "release_rows": "R1-T1-LABELS-UNSEAL (train and validation), R1-T1-LABELS-TEST-RELEASE (test labels and every "
                        "evaluation block) (§6; PRE-STAGE A, REL-SCOPE A, REL-T1-G1B)",
        "seal": "procedural (receipts and access log)",
        "t1_table_readings": table_readings_line(spec),
        "server_log": SERVER_LOG[kv["server_log"]],
        "decisions": ", ".join(f"{d} {o[d]}" for d in DECISIONS) + f" (row {spec['decisions_row']})",
    }
    if o["G5-MEM"] == "A":
        lines["e4_amendment_row"] = str(spec["e4_amendment_row"])
    if cuda.get("mode") != "c12":
        lines["cuda_ipc_acceptance"] = CUDA_IPC_ACCEPTANCE
    return lines


def table_readings_line(spec: dict) -> str:
    """The note's t1_table_readings line (part 3b-2, review M2): the readings, and the author's choice for the logged
    delta_hat of a proposal that diverged or timed out in its campaign (refuse | neg_inf | leave_out)."""
    choice = spec["key_values"]["t1_table_readings"]["campaign_divergent_delta_hat"]
    return "; ".join(TABLE_READINGS.values()) + f"; campaign-divergent delta_hat: {choice}"


P_CITES = {"P1": ("R1-T1-HOST-TASL",), "P3": (), "P4": ("R1-G5-DECISIONS",), "P5": ("docs/r1/reviews/",),
           "P6": (), "P7": (), "P8": ("docs/r1/reviews/",), "P9": ("R1-T1-TASL-ENV",), "P2": (), "P10": (),
           "P11": ()}


def note_k(fields: dict) -> tuple[int, str | None]:
    """``audit_K`` read from the note (P4): 10, or 6 with the K-check row it names."""
    m = re.fullmatch(r"(10|6) \((.*)\)", fields.get("audit_K", ""))
    if not m:
        raise Stop("STOP: the note's audit_K line must read '10 (...)' or '6 (K-check row R1-...; ...)'")
    if m.group(1) == "10":
        return 10, None
    row = re.match(r"K-check row (R1-[A-Z0-9][A-Z0-9-]*[A-Z0-9])(?![A-Za-z0-9-])", m.group(2))
    if not row:
        raise Stop("STOP: audit_K 6 must name the K-check PASS row (P4)")
    return 6, row.group(1)


FREEZE_LINE = re.compile(r"^the arms-frozen record waits for the train/dev release of every un-STOPped T1 node of "
                         r"this table until (?P<date>\d{4}-\d{2}-\d{2})(?: \(moved by author row "
                         r"(?P<row>R1-[A-Z0-9][A-Z0-9-]*[A-Z0-9])\))?; no G\.5 job starts on or after this date "
                         r"\(STOP 14\)$")


def note_freeze(fields: dict, spec: dict) -> tuple[str, str | None]:
    """The freeze-wait release date read from the note (m3): the spec's date, or another date moved by a docs-only
    amendment of the note that names the author row (which ``check_note`` requires on main, naming the date)."""
    m = FREEZE_LINE.fullmatch(fields.get("freeze_wait", ""))
    if not m:
        raise Stop("STOP: the note's freeze_wait line is not in the required form (STOP 14)")
    d, row = m.group("date"), m.group("row")
    try:
        date.fromisoformat(d)
    except ValueError:
        raise Stop("STOP: the note's freeze_wait date is not a date") from None
    if (d != spec["key_values"]["freeze_wait_release_date"]) != bool(row):
        raise Stop("STOP: a freeze_wait date other than the spec's needs the author row that moves it (and only "
                   "then names one)")
    return d, row


def decision_row_checks(spec: dict, o: dict) -> list[tuple[str, tuple[str, ...]]]:
    """The author rows the switch checks for the decisions, with the terms each must name: the decisions row names every
    decision's option and, under G5-MEM A, cites the E4 amendment row by its id; the E4 row amends E4's "both memory
    modes" (R1-BX-PROPOSED-CONFIRM E4), so it names E4 and "memory modes". (The first form required the E4 row itself
    to name "G5-MEM", which main's R1-G5-MEM-E4 does not: it is tied to G5-MEM A by R1-G5-DECISIONS-2's "G5-MEM A
    (...; with R1-G5-MEM-E4)".) The term checks alone would not refuse a single row serving as both: ``plan_row``
    strips only the id cell, so a row whose text names its own id, "E4" and "memory modes" would pass. So the two rows
    must be distinct: ``decisions_row == e4_amendment_row`` under G5-MEM A is refused here (G.5 follow-ups, 23 Nov
    2026)."""
    e4 = spec["e4_amendment_row"] if o["G5-MEM"] == "A" else None
    if e4 is not None and e4 == spec["decisions_row"]:
        raise Stop(f"STOP: under G5-MEM A the decisions row and the E4 amendment row must be two rows; both are {e4}")
    checks = [(spec["decisions_row"], tuple(f"{d} {o[d]}" for d in DECISIONS) + ((e4,) if e4 else ()))]
    if e4:
        checks.append((e4, ("E4", "memory modes")))
    return checks


def plan_row(row: str, read_main, *, terms: tuple[str, ...] = ()) -> str:
    """The row's line on published main's PLAN (exactly once), naming every term. A term may not run on into a letter
    or digit on either side: "G5-W A" matches neither "G5-W AB" nor "XG5-W A" (the preceding boundary: review m5 of
    R1-T1-FEAT-DECISIONS). The match is literal: it cannot see negation ("not D9 B" names "D9 B")."""
    if not isinstance(row, str) or not ROW_ID.fullmatch(row):
        raise Stop(f"STOP: {row!r} is not a PLAN row id")
    plan = (read_main("docs/r1/PLAN.md") or b"").decode("utf-8", "replace")
    lines = [ln for ln in plan.splitlines() if re.match(rf"^\| {re.escape(row)} \|", ln)]
    if len(lines) != 1:
        raise Stop(f"STOP: the PLAN row {row} must exist exactly once on published main")
    text = lines[0].split("|", 2)[2]                 # the row's text, without its id cell
    missing = [t for t in terms if not re.search(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])", text)]
    if missing:
        raise Stop(f"STOP: the PLAN row {row} does not name {missing}")
    return lines[0]


def check_note(note_path: Path, spec_path: Path, *, spec: dict, on_main=G._note_on_main, read_main=G._read_main,
               draft: bool = False) -> dict:
    """The signed G.5 note ``docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md`` (named by the spec's run_id): on
    published main byte-identically, ``approved: true`` (``draft=True``: exactly one ``approved: false`` line, need
    not be on main), no ``<…>`` placeholder, ``paper_commit`` and ``spec_sha256`` binding the spec, P1-P11 PASS with
    their citations, and every key line of ``note_lines`` verbatim, with K read from the note (P4). Returns the
    fields with ``_K`` and ``_K_row``."""
    note_path = Path(note_path)
    m = NOTE_NAME.fullmatch(note_path.name)
    if note_path.parent.as_posix().split("/")[-3:] != NOTE_DIR.split("/") or not m:
        raise Stop(f"STOP: the note must be {NOTE_DIR}/c3_t1_labels_<YYYYMMDD>.md")
    if note_path.name != f"{spec['run_id']}.md":
        raise Stop(f"STOP: the note's name must be the spec's run_id ({spec['run_id']}.md)")
    raw = note_path.read_bytes()
    approved = [ln for ln in raw.decode().splitlines() if re.match(r"^approved\s*:", ln)]
    if draft:
        if approved != ["approved: false"]:
            raise Stop("STOP: draft mode is for the unsigned note (exactly one line 'approved: false')")
    elif approved != ["approved: true"] or not on_main(f"{NOTE_DIR}/{note_path.name}", raw):
        raise Stop("STOP: the note must read approved: true and be committed byte-identically on origin/main")
    fields = G._note_fields(raw)
    k, k_row = note_k(fields)
    freeze, freeze_row = note_freeze(fields, spec)
    want = note_lines(spec, k=k, k_row=k_row, freeze=freeze, freeze_row=freeze_row)
    unfilled = sorted(key for key, v in fields.items()
                      if (PLACEHOLDER.search(v) or L._placeholder(v)) and v != want.get(key))
    if unfilled:
        raise Stop(f"STOP: note fields not filled (placeholder): {unfilled}")
    for key, value in (("paper_commit", spec["paper"]["commit"]), ("spec_sha256", L._sha_file(spec_path))):
        if fields.get(key) != value:
            raise Stop(f"STOP: note field {key} must be {value!r}")
    cites = dict(P_CITES)
    cites["P1"] = cites["P1"] + (spec["harness_families"]["G5-7"]["isolation_host_check"]["record"],
                                 spec["tasl7_audits"]["isolation_host_check"]["record"])      # R1-G5-AUDIT-TWO-CARDS
    cites["P2"] = (spec["noise_floor"]["seven"]["copy"],)
    cites["P3"] = (spec["pilot_basis"]["run_id"], spec["pilot_basis"]["result_report"]["path"])   # the G.4b re-pilot
    cites["P6"] = (str(spec["decisions_row"]),)
    for key, needles in cites.items():
        value = fields.get(key, "")
        if not value.upper().startswith(("PASS — ", "PASS - ")):
            raise Stop(f"STOP: {key} must be PASS")
        missing = [n for n in needles if n not in value]
        if missing:
            raise Stop(f"STOP: {key} must cite {missing}")
    if k == 6:
        plan_row(k_row, read_main, terms=("K-check", "PASS"))
    if freeze_row:
        plan_row(freeze_row, read_main, terms=(freeze,))
    for key in ("P5", "P8"):          # the reviews these prerequisites cite are on main and accepted
        reviews = T4.REVIEW_PATH.findall(fields[key])
        if not reviews:
            raise Stop(f"STOP: {key} must cite a review file docs/r1/reviews/<name>.md")
        for review in reviews:
            text = (read_main(review) or b"").decode("utf-8", "replace")
            if not VERDICT_ACCEPTED.search(text):
                raise Stop(f"STOP: {key} cites {review}, which is not on published main with 'Verdict: ACCEPTED'")
    bad = sorted(key for key, value in want.items() if fields.get(key) != value)
    if bad:
        raise Stop(f"STOP: note key lines differ from the spec (§5): {bad}")
    return {**fields, "_K": k, "_K_row": k_row, "_freeze": freeze, "_freeze_row": freeze_row}


# =============================================================================================== REL-T1-G1B copies
def _review_names(review: str, needles: list[str], read_main, what: str) -> None:
    rv = read_main(review) if _rel_ok(review) and str(review).startswith("docs/r1/reviews/") else None
    text = rv.decode("utf-8", "replace") if rv is not None else ""
    missing = [n for n in needles if n not in text]
    if rv is None or missing or not VERDICT_ACCEPTED.search(text):
        raise Stop(f"STOP: the review {review} of {what} must be on published main, name {missing or needles} and "
                   f"read 'Verdict: ACCEPTED'")


def check_g1b_copy(entry: dict, *, schema: str, run_id: str, nodes: list[str], read_main,
                   gate_for: dict | None = None) -> dict:
    """A REL-T1-G1B copy of a sealed G.1b summary (R1-SWEEP2-RELEASE-DECISIONS): a committed file on published main
    with the declared sha256, of the summary schema and run, covering exactly the given nodes, and an independent
    review on main that names the copy's path and sha256 and the sealed summary's path (``sealed_path``; the copy is
    byte-identical to it) with ``Verdict: ACCEPTED``.

    ``gate_for`` (the seven-node copy, M3): the cross-check gate record ``crosscheck_gate.json`` is copied beside the
    summary copy (``gate_copy``, ``gate_sha256``), named with its sha256 in the same review, and binds the summary's
    assembly: schema ``g1b_tasl_crosscheck_gate/1``, the cross-check spec's TASL-7 nodes, G.1b spec sha256 and run id,
    and ``assembly_json_sha256`` equal to the summary's ``assembly_sha256`` (as ``g1b_tasl_join.noise_floor_by_node``
    requires). Returns each node's D21 verdict and, under R1-T1-D21-SCOPE, its scope (``g1b_verdict_scope``: the D21
    value recorded for the funnel, and fixed-seed determinism); the caller STOPs a node without a determinism PASS
    (STOP 5), never one that only does not qualify under D21.

    **D6 A (R1-T1-FEAT-DECISIONS, amending REL-T1-G1B's copy list):** the copies of the run's ``ASSEMBLY.json`` and
    ``runs.jsonl`` lie beside the summary copy on published main, bound to it (the summary's ``assembly_sha256`` is
    the sha256 of that ``ASSEMBLY.json``, whose ``runs_sha256`` is the sha256 of that ``runs.jsonl``), and the same
    review names both paths and sha256s (``run_copies``). Where ``entry`` names them (the spec's ``noise_floor.seven``,
    or ``noise_floor.ar`` under G5-ARPEND B), its ``assembly_copy``, ``assembly_sha256``, ``runs_copy`` and
    ``runs_sha256`` must be those; the returned dict carries the four fields for ``g5_assemble.noise_by_node``."""
    rel, sha, review, sealed = entry.get("copy"), entry.get("sha256"), entry.get("review"), entry.get("sealed_path")
    if not _rel_ok(rel) or not _rel_ok(review) or not str(review).startswith("docs/r1/reviews/"):
        raise Stop("STOP: a REL-T1-G1B copy needs a repository path and a review under docs/r1/reviews/")
    if not isinstance(sealed, str) or not sealed.startswith("/"):
        raise Stop("STOP: a REL-T1-G1B copy names the absolute path of the sealed summary it was taken from")
    raw = read_main(rel)
    if raw is None or _sha_bytes(raw) != sha:
        raise Stop(f"STOP: the REL-T1-G1B copy {rel} is not on published main with sha256 {sha}")
    s = json.loads(raw)
    if s.get("schema") != schema or s.get("label") != G.ENGINEERING_ONLY or s.get("run_id") != run_id:
        raise Stop(f"STOP: {rel} is not the {schema} summary of run {run_id}")
    verdicts = s.get("verdicts") or {}
    if sorted(verdicts) != sorted(nodes):
        raise Stop(f"STOP: {rel} covers {sorted(verdicts)}, not {sorted(nodes)}")
    runs = run_copies(rel, raw, read_main)
    named = {k: entry[k] for k in RUN_COPY_KEYS if k in entry}
    if named and named != {k: runs[k] for k in RUN_COPY_KEYS}:
        raise Stop(f"STOP: the REL-T1-G1B copy of {rel} names other ASSEMBLY.json / runs.jsonl copies than the ones "
                   f"beside it on published main (D6 A)")
    needles = [rel, sha, sealed, runs["assembly_copy"], runs["assembly_sha256"], runs["runs_copy"], runs["runs_sha256"]]
    out = {"copy": rel, "sha256": sha, "review": review, "sealed_path": sealed, "raw": raw, **runs,
           "qualifies_D21": {n: (v or {}).get("qualifies_D21") is True for n, v in verdicts.items()},
           "scope": {n: g1b_verdict_scope(n, v) for n, v in verdicts.items()}}          # R1-T1-D21-SCOPE
    if gate_for is not None:
        gate_rel, gate_sha = entry.get("gate_copy"), entry.get("gate_sha256")
        if not _rel_ok(gate_rel) or Path(gate_rel) != Path(rel).parent / "crosscheck_gate.json":
            raise Stop("STOP: the seven-node copy needs crosscheck_gate.json copied beside it (gate_copy)")
        gate_raw = read_main(gate_rel)
        if gate_raw is None or _sha_bytes(gate_raw) != gate_sha:
            raise Stop(f"STOP: the cross-check gate copy {gate_rel} is not on published main with sha256 {gate_sha}")
        gate = json.loads(gate_raw)
        xc = gate_for
        problems = [k for k, ok in (
            ("schema", gate.get("schema") == X.GATE_SCHEMA),
            ("nodes", sorted(gate.get("nodes") or {}) == sorted(xc["nodes"])),
            ("g1b_spec_sha256", gate.get("g1b_spec_sha256") == xc["g1b_spec"]["sha256"]),
            ("crosscheck_run_id", gate.get("crosscheck_run_id") == xc["run_id"]),
            ("assembly_json_sha256", isinstance(s.get("assembly_sha256"), str)
             and gate.get("assembly_json_sha256") == s["assembly_sha256"])) if not ok]
        if problems:
            raise Stop(f"STOP: the cross-check gate record {gate_rel} does not bind this summary's assembly and the "
                       f"TASL-7 nodes (R1-T1-TASL-ENV): {problems}")
        needles += [gate_rel, gate_sha]
        out.update(gate_copy=gate_rel, gate_sha256=gate_sha, gate_raw=gate_raw)
    _review_names(review, needles, read_main, f"the REL-T1-G1B copy {rel}")
    return out


def run_copies(rel: str, summary_raw: bytes, read_main) -> dict:
    """D6 A: the copies of the G.1b run's ``ASSEMBLY.json`` and ``runs.jsonl`` beside the summary copy ``rel`` on
    published main, bound to the summary's bytes by sha256 (summary ``assembly_sha256`` → ``ASSEMBLY.json``;
    its ``runs_sha256`` → ``runs.jsonl``)."""
    d = Path(rel).parent
    a_rel, r_rel = (d / "ASSEMBLY.json").as_posix(), (d / "runs.jsonl").as_posix()
    a_raw, r_raw = read_main(a_rel), read_main(r_rel)
    if a_raw is None or r_raw is None:
        raise Stop(f"STOP: the copies of the G.1b run's ASSEMBLY.json and runs.jsonl must be on published main beside "
                   f"{rel} (D6 A of R1-T1-FEAT-DECISIONS amends REL-T1-G1B's copy list)")
    try:
        bound = json.loads(summary_raw).get("assembly_sha256") == _sha_bytes(a_raw) and \
            json.loads(a_raw).get("runs_sha256") == _sha_bytes(r_raw)
    except (ValueError, AttributeError):
        bound = False
    if not bound:
        raise Stop(f"STOP: the copies {a_rel} and {r_rel} are not the run of {rel} (assembly_sha256 / runs_sha256)")
    return {"assembly_copy": a_rel, "assembly_sha256": _sha_bytes(a_raw), "runs_copy": r_rel,
            "runs_sha256": _sha_bytes(r_raw)}


def noise_precheck(copy: dict, node: str, read_main) -> dict:
    """The switch's cheap pre-check (review m6 of R1-T1-FEAT-DECISIONS): from the REL-T1-G1B summary copy and the
    run copies beside it on published main (``copy``: ``check_g1b_copy``'s result), the node's σ_node by T0's
    definition must be computable, finite and > 0 and its δ_n finite and > 0 (``g5_noise.node_noise`` and
    ``check_usable``, the code the table and the noise record use), or the job STOPs before it starts. Returns the
    two values with the runs sha256."""
    import g5_noise as N                                     # noqa: PLC0415 - g5_noise imports this module
    raws = [read_main(copy[k]) for k in ("copy", "assembly_copy", "runs_copy")]
    if any(r is None for r in raws):
        raise Stop(f"STOP: the REL-T1-G1B copies of {node}'s G.1b run are not on published main")
    st = N.node_noise(node, *raws, copy["runs_copy"])
    N.check_usable(node, st)
    return {"node": node, "sigma_node": st["sigma_node_t0_definition"], "delta_n": st["delta_n"],
            "runs_sha256": st["runs_sha256"]}


def check_seven_copy(spec: dict, read_main) -> dict:
    """The seven-node REL-T1-G1B copy with its cross-check gate record (M3)."""
    xs = spec["noise_floor"]["seven"]["crosscheck_spec"]
    xc = json.loads((REPO_ROOT / xs["path"]).read_text())
    if L._sha_file(REPO_ROOT / xs["path"]) != xs["sha256"] or \
            xc["g1b_spec"]["sha256"] != spec["harness_families"]["G5-7"]["g1b_spec"]["sha256"]:
        raise Stop("STOP: the cross-check spec must be the bound one and bind the seven-node G.1b spec")
    return check_g1b_copy(spec["noise_floor"]["seven"], schema=G.SUMMARY_SCHEMA,
                          run_id=spec["noise_floor"]["seven"]["run_id"], nodes=list(SEVEN), read_main=read_main,
                          gate_for=xc)


def floor_by_node(seven: dict, ar: dict) -> dict:
    """``g1b_tasl_join.noise_floor_by_node`` on the two copies (draft §5 ``noise_floor``: "g1b_tasl_join.py
    floor-by-node"), run on byte-identical temporary files: the seven-node summary beside its gate record, and
    autoresearch's summary; the union must be the split file's eight T1 nodes."""
    with tempfile.TemporaryDirectory(prefix="g5_floor_") as tmp:
        d7, dar = Path(tmp) / "seven", Path(tmp) / "ar"
        d7.mkdir()
        dar.mkdir()
        (d7 / "summary.json").write_bytes(seven["raw"])
        (d7 / "crosscheck_gate.json").write_bytes(seven["gate_raw"])
        (dar / "summary.json").write_bytes(ar["raw"])
        out = J.noise_floor_by_node(d7 / "summary.json", dar / "summary.json",
                                    REPO_ROOT / "r1/c3/splits/c3_p3_split_v1.json")
    for node, v in out["nodes"].items():
        v["summary"] = seven["copy"] if v["schema"] == G.SUMMARY_SCHEMA else ar["copy"]
    return out


def check_c12(spec: dict, read_main, host: str = WORKER_HOST) -> dict:
    """P1 under ``cuda_ipc: c12`` (M1): the host's C12 record on published main at its sha256 (TASL-2: ``c12_record``,
    for every job; TASL-7: ``c12_tasl7_record``, for a TASL-7 audit chunk, R1-G5-AUDIT-TWO-CARDS; without it no audit
    chunk runs on TASL-7 under c12). While the C12 record format is not fixed: either the record carries ``c12_host:
    <the host's name>`` and ``c12_verdict: PASS`` (both must then be right), or a review on main (``c12_review``,
    ``c12_tasl7_review``) names the record and its sha256 and reads ``Verdict: ACCEPTED``."""
    if host not in CUDA_C12_HOSTS:
        raise Stop(f"STOP: host must be one of {list(CUDA_C12_HOSTS)}")
    c = spec["key_values"]["cuda_ipc"]
    rk, sk, vk = CUDA_C12_HOSTS[host]
    hostname = spec["worker"]["hostname"] if host == WORKER_HOST else spec["tasl7_audits"]["hostname"]
    rel, sha = c.get(rk), c.get(sk)
    if rel is None:
        raise Stop(f"STOP: under cuda_ipc c12 a {host} job needs a C12 PASS record for {host} ({rk} is null; P1); "
                   f"without it no G.5 audit chunk runs on {host}")
    raw = read_main(rel) if _rel_ok(rel) else None
    if raw is None:
        raise Stop(f"STOP: the C12 record {rel} is not on published main (P1)")
    if _sha_bytes(raw) != sha:
        raise Stop(f"STOP: the C12 record {rel} differs from its declared sha256 (P1)")
    fields = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        m = re.match(r"^(c12_[a-z_]+):\s*(.*?)\s*$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: duplicate {m.group(1)} in the C12 record")
            fields[m.group(1)] = m.group(2)
    out = {"record": rel, "sha256": sha, "host": host}
    if "c12_host" in fields or "c12_verdict" in fields:
        if fields.get("c12_host") != hostname or fields.get("c12_verdict") != "PASS":
            raise Stop(f"STOP: the C12 record does not read a PASS on {hostname}: "
                       f"{ {k: fields.get(k) for k in ('c12_host', 'c12_verdict')} } (P1)")
        out["fields"] = fields
    elif c.get(vk) is None:
        raise Stop(f"STOP: the C12 record has no c12_host / c12_verdict lines and no {vk} names it (P1)")
    if c.get(vk) is not None:
        _review_names(c[vk], [rel, sha], read_main, f"the C12 record {rel}")
        out["review"] = c[vk]
    return out


# =============================================================================================== TASL-7 audits
# The short cross-check (xc3) unit's PASS verdicts for the four pending nodes, as that unit writes them (READY 107, on
# main; the signed note's verdicts line): docs/r1/reports/tasl_chain_20261122/G1B_XC3_SHORT_VERDICT_<node>_20261125.json,
# schema g1b_tasl_crosscheck_verdict/1, mode "short", rule R1-G5-AUDIT-TWO-CARDS. The directory and date are matched by
# pattern; the xc3 spec is bound through the signed note on main (``xc3_reading``: run_id and xc_spec_sha256).
SHORT_XC_NAME = re.compile(r"^docs/r1/reports/[A-Za-z0-9_.\-]+/G1B_XC3_SHORT_VERDICT_(?P<node>[a-z0-9_]+)_\d{8}\.json$")
SHORT_XC_TOKEN = "G1B_XC3_SHORT_VERDICT_"
SHORT_MODE = "short"
SIDE_FIELDS = ("run_id", "spec_sha256", "job_record_sha256", "attempt")
# XC3-FAIL (an author decision) is recorded in the signed xc3 note's ``xc3_fail`` line
# (docs/r1/authorizations/g1b_xc_short_t1_tasl_<YYYYMMDD>.md) and in the PLAN row R1-XC3-FAIL-READING; the switch reads
# both from published main (``xc3_reading``). A: a failed or missing short check keeps only that node's audits off
# TASL-7. B: a node whose short check was run and did not PASS leaves G.5 (STOP 5 at every job start of that node). The
# note's ``skip_nodes`` names nodes with no short check: they stay on TASL-2 and B does not touch them. The rules for the
# note's choices and for the row are the xc3 unit's own (READY 107, on main): ``g1b_crosscheck.short_decisions`` and
# ``g1b_crosscheck.xc3_fail_row_option``, imported (``X``), with its ``SHORT_DECISIONS`` and ``XC3_FAIL_ROW_SENTENCE``.
XC3_NOTE_NAME = re.compile(r"^docs/r1/authorizations/g1b_xc_short_t1_tasl_\d{8}\.md$")
XC3_ROW = X.XC3_FAIL_ROW
XC3_SPEC_REL = "sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json"
XC3_RUN_PREFIX = "g1b-tasl-20261121-b-xc3-"


def short_nodes(spec: dict) -> list[str]:
    """The nodes whose cross-host PASS is the xc3 short check: those the spec marks ``PENDING short cross-check``, and
    (revision 13) those whose listed record is a ``short`` verdict."""
    def short(e, n):
        return e == xc_pending(n) or (isinstance(e, list) and any(isinstance(x, dict) and x.get("mode") == SHORT_MODE
                                                                  for x in e))
    return [n for n in SEVEN if short(spec["tasl7_audits"]["crosshost_pass"][n], n)]


def xc3_reading(spec: dict, read_main, list_main) -> dict:
    """XC3-FAIL and ``skip_nodes`` from published main.
    - The signed xc3 note: the files ``docs/r1/authorizations/g1b_xc_short_t1_tasl_<YYYYMMDD>.md`` on main (the date is
      chosen at signature); two or more is a STOP; one must read ``approved: true``, its choices by the xc3 unit's
      ``g1b_crosscheck.short_decisions`` (imported: ``xc3_fail``, ``xc3_cap``, ``skip_nodes`` among the nodes this
      spec marks for the short check; the parser of ``g1b_tasl._note_fields``, which refuses duplicate keys, as the xc3
      reader's), and, where the xc3 spec is on main, its ``run_id`` and ``xc_spec_sha256`` equal to that spec's. (The
      xc3 unit's ``check_xc_note`` reads a note file on disk against the spec file and the paper commit, for the xc3
      launch; this reader takes the note from main, so it applies the rules the G.5 entry needs and not that check.)
    - The PLAN row R1-XC3-FAIL-READING (``g1b_crosscheck.xc3_fail_row_option``, imported: once, with exactly one
      sentence "The xc3 note carries xc3_fail: A." or "... B."). Where both exist they must agree.
    ``xc3_fail`` is None while neither is on main ("A pending": no short verdict exists without a run under the signed
    note, and a node without a PASS stays on TASL-2 either way). Also the xc3 run id: the xc3 spec's on main, else the
    note's, else None (then a verdict's run id must carry the prefix ``g1b-tasl-20261121-b-xc3-``)."""
    notes = sorted(p for p in list_main("docs/r1/authorizations/") if XC3_NOTE_NAME.fullmatch(p))
    if len(notes) > 1:
        raise Stop(f"STOP: {len(notes)} xc3 notes on published main ({notes}); XC3-FAIL is ambiguous")
    raw_spec = read_main(XC3_SPEC_REL)
    try:
        xc3_spec = json.loads(raw_spec) if raw_spec is not None else None
    except ValueError:
        raise Stop(f"STOP: {XC3_SPEC_REL} on published main is not JSON") from None
    note_value, skip, note_rel, note_run = None, [], None, None
    pending = short_nodes(spec)
    if notes:
        note_rel = notes[0]
        f = G._note_fields(read_main(note_rel) or b"")
        note_run = f.get("run_id")
        if f.get("approved") != "true":
            raise Stop(f"STOP: the xc3 note {note_rel} on published main does not read approved: true")
        try:
            decided = X.short_decisions(f, {"nodes": pending})        # the xc3 unit's rules (READY 107, on main)
        except Stop as exc:
            raise Stop(f"STOP: the signed xc3 note {note_rel} on published main: {exc}") from None
        note_value, skip = decided["xc3_fail"], decided["skip_nodes"]
        if xc3_spec is not None and (note_run != xc3_spec.get("run_id")
                                     or f.get("xc_spec_sha256") != _sha_bytes(raw_spec)):
            raise Stop(f"STOP: the signed xc3 note {note_rel} does not bind the xc3 spec on main (run_id, "
                       f"xc_spec_sha256)")
    row_value = X.xc3_fail_row_option(read_main)                      # the xc3 unit's rule (READY 107, on main)
    if note_value and row_value and note_value != row_value:
        raise Stop(f"STOP: XC3-FAIL differs between the signed xc3 note ({note_value}) and {XC3_ROW} ({row_value})")
    spec_run = xc3_spec.get("run_id") if isinstance(xc3_spec, dict) else None
    return {"xc3_fail": note_value or row_value, "note": note_rel, "row": row_value is not None, "skip_nodes": skip,
            "run_id": spec_run or note_run}




def _short_files(node: str, list_main) -> list[str]:
    """The node's short verdict file on main: a ``.json`` named exactly ``G1B_XC3_SHORT_VERDICT_<node>_<YYYYMMDD>.json``
    directly under ``docs/r1/reports/<dir>/``. Copies inside a ``*_captures/`` subtree are ignored; any other ``.json``
    path naming ``G1B_XC3_SHORT_VERDICT_<node>_`` (another depth or a near-miss name) is refused; files that are not
    ``.json`` are ignored. Two or more matches are refused."""
    cands = []
    for p in list_main("docs/r1/reports/"):
        parts = p.split("/")
        if not p.endswith(".json") or SHORT_XC_TOKEN + node + "_" not in parts[-1] or \
                any(x.endswith("_captures") for x in parts[:-1]):
            continue
        cands.append(p)
    odd = [p for p in cands if not (SHORT_XC_NAME.fullmatch(p) and SHORT_XC_NAME.fullmatch(p).group("node") == node)]
    if odd:
        raise Stop(f"STOP: .json paths on published main name {SHORT_XC_TOKEN}{node} but are not "
                   f"docs/r1/reports/<dir>/{SHORT_XC_TOKEN}{node}_<YYYYMMDD>.json: {sorted(odd)[:5]}")
    if len(cands) > 1:
        raise Stop(f"STOP: {len(cands)} short cross-check verdicts of {node} on published main: {sorted(cands)[:5]}")
    return sorted(cands)


def _check_xc_verdict(spec: dict, node: str, rel: str, raw: bytes, mode: str, run_id: str | None) -> dict:
    """One cross-host PASS record (``g1b_crosscheck``'s verdict schema ``g1b_tasl_crosscheck_verdict/1``): this node,
    the given mode, label ENGINEERING_ONLY, complete, PASS with no reason, the seven nodes' G.1b pin, signed G.1b spec
    and run, the cross-check run id, and both hosts in ``sides``.
    - ``xc`` / ``preassembly`` (the xc2 verdicts): rule R1-T1-TASL-ENV, the spec's run id, each side deterministic.
    - ``short`` (the xc3 short check): rule R1-G5-AUDIT-TWO-CARDS; the run id ``run_id`` (the xc3 spec's or the signed
      note's on main) or, with neither on main, one carrying ``g1b-tasl-20261121-b-xc3-``; each side naming
      ``run_id``, ``spec_sha256``, ``job_record_sha256`` and ``attempt``, the TASL-2 side's ``run_id`` the G.1b run
      (the sealed G.1b attempt) and the TASL-7 side's ``<xc3 run>-TASL-7``; a side's ``deterministic`` true where
      present.
    Anything else refuses the node's TASL-7 audit chunk."""
    try:
        v = json.loads(raw)
    except ValueError:
        v = None
    v = v if isinstance(v, dict) else {}
    fam = spec["harness_families"]["G5-7"]
    sides = v.get("sides")
    short = mode == SHORT_MODE
    xrun = v.get("crosscheck_run_id")
    run_ok = isinstance(xrun, str) and (xrun == run_id if run_id is not None else
                                        (short and xrun.startswith(XC3_RUN_PREFIX)))
    sides_ok = isinstance(sides, dict) and sorted(sides) == sorted(JOB_HOSTS) and \
        all(isinstance(x, dict) for x in sides.values())
    if sides_ok and short:
        sides_ok = all(all(k in x for k in SIDE_FIELDS) and x.get("deterministic", True) is True
                       for x in sides.values()) and \
            sides[WORKER_HOST]["run_id"] == fam["g1b_spec"]["run_id"] and sides[AUDIT_HOST]["run_id"] == f"{xrun}-TASL-7"
    elif sides_ok:
        sides_ok = all(x.get("deterministic") is True for x in sides.values())
    problems = [k for k, ok in (
        ("schema", v.get("schema") == X.VERDICT_SCHEMA),
        ("label", v.get("label") == G.ENGINEERING_ONLY),
        ("node", v.get("node") == node),
        ("verdict", v.get("verdict") == "PASS" and v.get("reason") is None),
        ("complete", v.get("complete") is True),
        ("mode", v.get("mode") == mode),
        ("rule", v.get("rule") == (TWO_CARDS_ROW if short else "R1-T1-TASL-ENV")),
        ("harness_commit", v.get("harness_commit") == fam["g1b_pin"]),
        ("g1b_spec_sha256", v.get("g1b_spec_sha256") == fam["g1b_spec"]["sha256"]),
        ("g1b_run_id", v.get("g1b_run_id") == fam["g1b_spec"]["run_id"]),
        ("crosscheck_run_id", run_ok),
        ("sides", sides_ok)) if not ok]
    if problems:
        raise Stop(f"STOP: {rel} is not a cross-host PASS of {node}: {problems}; {node}'s audits do not run on "
                   f"{AUDIT_HOST} (it may still run on {WORKER_HOST})")
    return {"record": rel, "sha256": _sha_bytes(raw), "mode": mode, "crosscheck_run_id": xrun}


def check_crosshost_pass(spec: dict, node: str, read_main, list_main=None) -> dict:
    """R1-G5-AUDIT-TWO-CARDS at a TASL-7 audit job start and at a claim: the node's cross-host PASS.

    - Autoresearch never runs on TASL-7 (its ar-cond7a environment exists only on TASL-2).
    - A node whose ``tasl7_audits.crosshost_pass`` lists records (the three TASL-7 G.1b nodes: their xc2 step-1 and
      step-2 verdicts): every record on published main at its sha256 and a PASS (``_check_xc_verdict``).
    - A node with the marker ``PENDING short cross-check: <node>`` (the other four; the xc3 short check): XC3-FAIL must
      be on main (``xc3_reading``: the signed xc3 note or R1-XC3-FAIL-READING), the node not in the note's
      ``skip_nodes`` (no short check: TASL-2 only), and exactly one verdict file
      ``docs/r1/reports/<dir>/G1B_XC3_SHORT_VERDICT_<node>_<YYYYMMDD>.json`` on main that is a short PASS. No file:
      refused (fail closed).
    - A short-check node whose short verdict the spec lists (revision 13): the record on published main at its sha256
      and a short PASS of the listed run id, and the same reading as for the marker: XC3-FAIL on main, the node not
      skipped, the xc3 run id on main (where known) the listed one, and the listed record the one short verdict file
      of the node on main.
    Any failure refuses only that node's TASL-7 audit chunks; its TASL-2 jobs and the launch are untouched (except
    under XC3-FAIL B, ``xc3_b_check``)."""
    list_main = list_main or (lambda prefix="": [])
    if node == AR or node not in SEVEN:
        raise Stop(f"STOP: {node}'s audits stay on {WORKER_HOST} ({AR}'s environment ar-cond7a exists only there; "
                   f"tasl7_audits covers the G5-7 family only)")
    entries = spec["tasl7_audits"]["crosshost_pass"][node]
    if isinstance(entries, list):
        out = []
        for e in entries:
            raw = read_main(e["record"]) if _rel_ok(e["record"]) else None
            if raw is None or _sha_bytes(raw) != e["sha256"]:
                raise Stop(f"STOP: the cross-host PASS record {e['record']} of {node} is not on published main with "
                           f"sha256 {e['sha256']}; {node}'s audits do not run on {AUDIT_HOST}")
            out.append(_check_xc_verdict(spec, node, e["record"], raw, e["mode"], e["crosscheck_run_id"]))
        res = {"node": node, "source": "spec", "records": out}
        short = [e for e in entries if e["mode"] == SHORT_MODE]
        if short:
            reading = xc3_reading(spec, read_main, list_main)
            if reading["xc3_fail"] is None:
                raise Stop(f"STOP: {node}: neither a signed xc3 note nor {XC3_ROW} is on published main (XC3-FAIL not "
                           f"recorded); {node} may not run on {AUDIT_HOST} (it may still run on {WORKER_HOST})")
            if node in reading["skip_nodes"]:
                raise Stop(f"STOP: the signed xc3 note skips {node} (skip_nodes): its audits stay on {WORKER_HOST}")
            if reading["run_id"] is not None and reading["run_id"] != short[0]["crosscheck_run_id"]:
                raise Stop(f"STOP: the xc3 run on published main ({reading['run_id']}) is not the listed short "
                           f"verdict's ({short[0]['crosscheck_run_id']}); {node}'s audits do not run on {AUDIT_HOST}")
            found = _short_files(node, list_main)
            if found != [short[0]["record"]]:
                raise Stop(f"STOP: the short verdict files of {node} on published main ({found}) are not exactly the "
                           f"listed {short[0]['record']}; {node}'s audits do not run on {AUDIT_HOST}")
            res["xc3_fail"] = reading["xc3_fail"]
        return res
    if entries != xc_pending(node):
        raise Stop(f"STOP: tasl7_audits.crosshost_pass.{node} is neither a record list nor its PENDING marker")
    reading = xc3_reading(spec, read_main, list_main)
    if reading["xc3_fail"] is None:
        raise Stop(f"STOP: {xc_pending(node)}: neither a signed xc3 note nor {XC3_ROW} is on published main (XC3-FAIL "
                   f"not recorded); {node} may not run on {AUDIT_HOST} (it may still run on {WORKER_HOST})")
    if node in reading["skip_nodes"]:
        raise Stop(f"STOP: the signed xc3 note skips {node} (skip_nodes): it has no short check and its audits stay on "
                   f"{WORKER_HOST}")
    found = _short_files(node, list_main)
    if not found:
        raise Stop(f"STOP: {xc_pending(node)}: no cross-host PASS record of {node} is on published main; it may not run "
                   f"on {AUDIT_HOST} (it may still run on {WORKER_HOST})")
    rel = found[0]
    rec = _check_xc_verdict(spec, node, rel, read_main(rel) or b"", SHORT_MODE, reading["run_id"])
    return {"node": node, "source": "main", "records": [rec], "xc3_fail": reading["xc3_fail"]}


def xc3_b_check(spec: dict, node: str, read_main, list_main) -> dict | None:
    """XC3-FAIL B at every job start of a short-check node (TASL-2 included): with B on main (``xc3_reading``) and the
    node not skipped, a committed short verdict of the node reading ``verdict: STOP`` (schema, node, mode and rule as
    the writer's) means its short check was run and did not PASS: the node leaves G.5 (STOP 5, R1-T1-D21-SCOPE read as
    B). A PASS, or no verdict yet, lets it go on; a file that cannot be read as a short verdict is a refusal. Under A,
    or without a recorded XC3-FAIL, nothing here."""
    if node not in short_nodes(spec):
        return None
    reading = xc3_reading(spec, read_main, list_main)
    if reading["xc3_fail"] != "B" or node in reading["skip_nodes"]:
        return {"node": node, "xc3_fail": reading["xc3_fail"], "applies": False}
    found = _short_files(node, list_main)
    if not found:
        return {"node": node, "xc3_fail": "B", "applies": True, "verdict": None}
    try:
        v = json.loads(read_main(found[0]) or b"")
    except ValueError:
        v = None
    if not (isinstance(v, dict) and v.get("schema") == X.VERDICT_SCHEMA and v.get("node") == node
            and v.get("mode") == SHORT_MODE and v.get("rule") == TWO_CARDS_ROW and v.get("verdict") in ("PASS", "STOP")):
        raise Stop(f"STOP: {found[0]} cannot be read as {node}'s short verdict; under XC3-FAIL B its G.5 jobs wait")
    if v["verdict"] == "STOP":
        exc = NodeStop(f"STOP 5: {node}'s short cross-check was run and did not PASS ({found[0]}); under XC3-FAIL B "
                       f"(R1-T1-D21-SCOPE's cross-host check read to include it) the node is not run in G.5; the "
                       f"author decides (R1-BX-D12)")
        exc.record = {"verdict": found[0], "verdict_sha256": _sha_bytes(read_main(found[0]) or b""),
                      "xc3_note": reading["note"], "xc3_row": reading["row"]}
        raise exc
    return {"node": node, "xc3_fail": "B", "applies": True, "verdict": found[0]}


# =============================================================================================== R1-TASL2-CPU check
def _derived_bytes(d: dict) -> bytes:
    return (json.dumps(d, indent=1, sort_keys=True) + "\n").encode()


def cpuset_spec(spec: dict, node: str, run_id: str) -> dict:
    """The derived G.1b spec of a replacement set's fixed-seed determinism check (R1-TASL2-CPU): the signed G.1b spec
    of the G5-7 family (``harness_families.G5-7.g1b_spec``, by sha256), with its own run id
    ``tasl2-cpuset-<node>-<YYYYMMDD>`` and the node pinned to its replacement set on TASL-2 (where the set is the
    TASL-2 GPU jobs' set, the node's own ``cpus`` is dropped so that it takes the host's set: G.1b refuses a CPU-only
    set overlapping the GPU jobs', which ran beside it there). Everything else is the signed spec: harness pin, checkout,
    environments, data manifest, seeds, timeouts, host checks. ``g1b_tasl.validate_spec(launch=True)`` must pass, and
    the node's affinity under it must be the replacement set. ENGINEERING_ONLY: it runs the default part only
    (``dry_run_node.py``), no G.1b row."""
    reps = spec["tasl2_cpus"]["replacements"]
    if node not in reps:
        raise Stop(f"STOP: {node} has no TASL-2 replacement CPU set ({TASL2_CPU_ROW})")
    m = CPUSET_RUN.fullmatch(str(run_id))
    if not m or m.group("node") != node:
        raise Stop(f"STOP: the check's run id must be tasl2-cpuset-{node}-<YYYYMMDD>")
    fam = spec["harness_families"]["G5-7"]
    raw = (REPO_ROOT / FAMILY_SPECS["G5-7"]).read_bytes()
    if _sha_bytes(raw) != fam["g1b_spec"]["sha256"]:
        raise Stop(f"STOP: {FAMILY_SPECS['G5-7']} in the checkout is not the signed G.1b spec "
                   f"({fam['g1b_spec']['sha256'][:8]}…)")
    d = copy.deepcopy(json.loads(raw))
    d["run_id"] = run_id
    entry = G.node_entry(d, node)
    if entry.get("host") != WORKER_HOST or entry.get("cpus") != reps[node]["g1b_cpus"]:
        raise Stop(f"STOP: {node} is not a {WORKER_HOST} node with cpus {reps[node]['g1b_cpus']} in the signed G.1b spec")
    new = reps[node]["cpus"]
    if G.cpu_list(new) == G.cpu_list(d["hosts"][WORKER_HOST]["cpus"]):
        entry.pop("cpus")
    else:
        entry["cpus"] = new
    d["cpuset_check"] = {"rule": TASL2_CPU_ROW, "node": node, "cpus": new, "g1b_cpus": reps[node]["g1b_cpus"],
                         "g1b_run_id": fam["g1b_spec"]["run_id"], "g1b_spec_sha256": fam["g1b_spec"]["sha256"],
                         "output_use": "ENGINEERING_ONLY fixed-seed determinism check of a TASL-2 CPU set; the default "
                                       "part only (dry_run_node.py); no G.1b row, no label"}
    G.validate_spec(d, launch=True)
    if G.cpu_list(G.node_cpus(d, G.node_entry(d, node))) != G.cpu_list(new):
        raise Stop(f"STOP: {node}'s affinity under the derived spec is not {new}")
    return d


def _attempt_timing(rec: dict) -> tuple[float, float]:
    t = rec.get("timing")
    if not isinstance(t, list) or not t or not all(isinstance(x, dict) and isinstance(x.get("max_wall_s"), (int, float))
                                                   and isinstance(x.get("c0_median_wall_s"), (int, float)) for x in t):
        raise Stop("STOP: the attempt's job record has no timing (c0_median_wall_s, max_wall_s per part)")
    return max(float(x["max_wall_s"]) for x in t), max(float(x["c0_median_wall_s"]) for x in t)


def cpuset_verdict(spec: dict, node: str, derived_path: Path, reference: Path, attempts: list[Path]) -> dict:
    """The fixed-seed determinism record of a replacement set (``g5_tasl2_cpuset_check/1``; R1-TASL2-CPU), from the
    derived spec file (it must be ``cpuset_spec``'s, byte for byte), the node's sealed G.1b TASL-2 attempt (the one the
    xc3 spec declares: attempt, ``job_record.json`` and ``SHA256SUMS`` sha256) and the check's sealed attempts
    (``g1b_crosscheck._sealed_rows``: receipt, sums and record bound; the default part's rows, row gate re-checked).
    Each attempt must carry the derived run id and spec sha256, the harness pin, host TASL-2 and no STOP. PASS when
    there are at least ``CPUSET_REPEATS`` attempts, each with affinity equal to the set, complete (c0..cN default and
    default_repeat), deterministic (``g1b_lib.determinism_check``), with every outcome (``g1b_lib._outcome``) identical
    to the reference's, and every run within ``cpuset_budget_s``. The record carries no metric value: per attempt only
    the booleans, the timing and the sha256 values. Inputs that are not what is named are refused."""
    reps = spec["tasl2_cpus"]["replacements"]
    if node not in reps:
        raise Stop(f"STOP: {node} has no TASL-2 replacement CPU set ({TASL2_CPU_ROW})")
    r = reps[node]
    raw = Path(derived_path).read_bytes()
    try:
        d = json.loads(raw)
    except ValueError:
        raise Stop(f"STOP: {derived_path} is not JSON") from None
    want = cpuset_spec(spec, node, str((d if isinstance(d, dict) else {}).get("run_id")))
    if raw != _derived_bytes(want):
        raise Stop(f"STOP: {derived_path} is not the derived spec of cpuset-spec for {node}")
    dsha, fam = _sha_bytes(raw), spec["harness_families"]["G5-7"]
    pin, want_cpus = fam["g1b_pin"], G.cpu_list(r["cpus"])
    decl = cpuset_reference(node)
    ref = Path(reference)
    rec, rows = X._sealed_rows(ref, node)
    ref_bad = [k for k, ok in (("run_id", rec.get("run_id") == fam["g1b_spec"]["run_id"]),
                               ("host", (rec.get("host") or {}).get("host") == WORKER_HOST),
                               ("attempt", rec.get("attempt") == decl["attempt"]),
                               ("job_record_sha256", L._sha_file(ref / "job_record.json") == decl["job_record_sha256"]),
                               ("sha256sums_sha256", L._sha_file(ref / "SHA256SUMS") == decl["sha256sums_sha256"]),
                               ("harness_commit", rec.get("harness_commit") == pin)) if not ok]
    if ref_bad:
        raise Stop(f"STOP: {ref} is not {node}'s declared sealed G.1b TASL-2 attempt ({ref_bad})")
    configs = ["c0"] + [f"c{k}" for k in range(1, G.node_entry(want, node)["n_edits"] + 1)]
    expected = {(c, cond) for c in configs for cond in X.DEFAULT_CONDITIONS}

    def outcomes(path, rws):
        out = {}
        for row in rws:
            key = (row["config"], row["condition"])
            if key in out:
                raise Stop(f"STOP: {path} has two rows for {key}")
            out[key] = L._outcome(row)
        return out
    ref_out = outcomes(ref, rows)
    if set(ref_out) != expected:
        raise Stop(f"STOP: the reference {ref} does not hold c0..c{len(configs) - 1} default and default_repeat")
    budget = cpuset_budget_s(node_entry(spec, node))
    seen, out_atts = set(), []
    for a in attempts:
        a = Path(a)
        arec, arows = X._sealed_rows(a, node)
        bad = [k for k, ok in (("run_id", arec.get("run_id") == want["run_id"]),
                               ("spec_sha256", arec.get("spec_sha256") == dsha),
                               ("harness_commit", arec.get("harness_commit") == pin),
                               ("host", (arec.get("host") or {}).get("host") == WORKER_HOST),
                               ("stop", arec.get("stop") is None and arec.get("stop_class") is None)) if not ok]
        if bad:
            raise Stop(f"STOP: {a} is not a complete attempt of the check run {want['run_id']} ({bad})")
        if arec.get("attempt") in seen:
            raise Stop(f"STOP: attempt {arec.get('attempt')} is given twice")
        seen.add(arec.get("attempt"))
        got = outcomes(a, arows)
        max_wall, c0_med = _attempt_timing(arec)
        complete = set(got) == expected
        out_atts.append({"sealed": str(a), "attempt": arec.get("attempt"),
                         "job_record_sha256": L._sha_file(a / "job_record.json"),
                         "affinity": arec.get("affinity"), "affinity_ok": arec.get("affinity") == want_cpus,
                         "complete": complete, "deterministic": bool(L.determinism_check(arows)["deterministic"]),
                         "identical_to_reference": complete and all(got[k] == ref_out[k] for k in expected),
                         "max_wall_s": max_wall, "c0_median_wall_s": c0_med, "within_budget": max_wall <= budget})
    if len(out_atts) < CPUSET_REPEATS:
        reason = "too_few_attempts"
    elif not all(x["affinity_ok"] for x in out_atts):
        reason = "affinity"
    elif not all(x["complete"] for x in out_atts):
        reason = "incomplete"
    elif not all(x["deterministic"] for x in out_atts):
        reason = "nondeterministic"
    elif not all(x["identical_to_reference"] for x in out_atts):
        reason = "reference_mismatch"
    elif not all(x["within_budget"] for x in out_atts):
        reason = "too_slow"
    else:
        reason = None
    return {"schema": CPUSET_SCHEMA, "label": G.ENGINEERING_ONLY, "rule": TASL2_CPU_ROW, "node": node,
            "host": WORKER_HOST, "cpus": r["cpus"], "g1b_cpus": r["g1b_cpus"], "harness_commit": pin,
            "g1b_run_id": fam["g1b_spec"]["run_id"], "g1b_spec_sha256": fam["g1b_spec"]["sha256"],
            "check_run_id": want["run_id"], "check_spec_sha256": dsha, "configs": configs,
            "reference": {"sealed": str(ref), "attempt": decl["attempt"], "job_record_sha256": decl["job_record_sha256"]},
            "repeats": CPUSET_REPEATS, "budget_s": budget, "attempts": out_atts,
            "complete": len(out_atts) >= CPUSET_REPEATS and all(x["complete"] for x in out_atts),
            "verdict": "PASS" if reason is None else "STOP", "reason": reason}


def _cpuset_files(node: str, list_main) -> list[str]:
    """The node's determinism record on main: a ``.json`` named exactly ``G5_TASL2_CPUSET_CHECK_<node>_<YYYYMMDD>.json``
    directly under ``docs/r1/reports/<dir>/`` (copies inside a ``*_captures/`` subtree ignored); another ``.json`` path
    naming it is refused, and so are two or more."""
    cands = []
    for p in list_main("docs/r1/reports/"):
        parts = p.split("/")
        if not p.endswith(".json") or CPUSET_TOKEN + node + "_" not in parts[-1] or \
                any(x.endswith("_captures") for x in parts[:-1]):
            continue
        cands.append(p)
    odd = [p for p in cands if not (CPUSET_NAME.fullmatch(p) and CPUSET_NAME.fullmatch(p).group("node") == node)]
    if odd:
        raise Stop(f"STOP: .json paths on published main name {CPUSET_TOKEN}{node} but are not "
                   f"docs/r1/reports/<dir>/{CPUSET_TOKEN}{node}_<YYYYMMDD>.json: {sorted(odd)[:5]}")
    if len(cands) > 1:
        raise Stop(f"STOP: {len(cands)} TASL-2 CPU-set records of {node} on published main: {sorted(cands)[:5]}")
    return sorted(cands)


def check_cpuset_record(spec: dict, node: str, read_main, list_main) -> dict | None:
    """R1-TASL2-CPU at every TASL-2 job start of a node with a replacement set: "that set passes a fixed-seed
    determinism check before its first use". Exactly one record ``docs/r1/reports/<dir>/G5_TASL2_CPUSET_CHECK_<node>_
    <YYYYMMDD>.json`` on published main (``cpuset_verdict``'s schema), for this node, TASL-2 and this set (and the G.1b
    set it replaces), the G5-7 G.1b pin, run and spec, the check spec's sha256 (recomputed as ``cpuset_spec``'s for
    the record's run id), the declared reference attempt, at least ``CPUSET_REPEATS``
    distinct attempts, each with affinity equal to the set, complete, deterministic, identical to the reference and
    within the budget; ``verdict: PASS``, no reason. Otherwise the node's TASL-2 job is refused (not a node STOP: the
    author decides on the set). A node without a replacement: None."""
    r = spec["tasl2_cpus"]["replacements"].get(node)
    if r is None:
        return None
    found = _cpuset_files(node, list_main)
    if not found:
        raise Stop(f"STOP: {node} runs on TASL-2 cpus {r['cpus']} ({TASL2_CPU_ROW}), and no fixed-seed determinism "
                   f"record docs/r1/reports/<dir>/{CPUSET_TOKEN}{node}_<YYYYMMDD>.json of that set is on published "
                   f"main; its TASL-2 jobs wait")
    rel = found[0]
    raw = read_main(rel) or b""
    try:
        v = json.loads(raw)
    except ValueError:
        v = None
    v = v if isinstance(v, dict) else {}
    fam, decl = spec["harness_families"]["G5-7"], cpuset_reference(node)
    want_cpus, budget = G.cpu_list(r["cpus"]), cpuset_budget_s(node_entry(spec, node))
    atts, reps = v.get("attempts"), v.get("repeats")
    atts_ok = isinstance(atts, list) and type(reps) is int and reps >= CPUSET_REPEATS and len(atts) >= reps and \
        all(isinstance(a, dict) for a in atts) and len({a.get("attempt") for a in atts}) == len(atts) and \
        all(a.get("affinity") == want_cpus and a.get("affinity_ok") is True and a.get("complete") is True and
            a.get("deterministic") is True and a.get("identical_to_reference") is True and
            a.get("within_budget") is True and isinstance(a.get("max_wall_s"), (int, float)) and
            not isinstance(a.get("max_wall_s"), bool) and a["max_wall_s"] <= budget for a in atts)
    run = CPUSET_RUN.fullmatch(str(v.get("check_run_id")))
    spec_ok = False
    if run and run.group("node") == node:                # the check spec's sha256, recomputed (review nit 1)
        spec_ok = v.get("check_spec_sha256") == _sha_bytes(_derived_bytes(cpuset_spec(spec, node, v["check_run_id"])))
    ref = v.get("reference")
    problems = [k for k, ok in (
        ("schema", v.get("schema") == CPUSET_SCHEMA), ("label", v.get("label") == G.ENGINEERING_ONLY),
        ("rule", v.get("rule") == TASL2_CPU_ROW), ("node", v.get("node") == node), ("host", v.get("host") == WORKER_HOST),
        ("cpus", v.get("cpus") == r["cpus"]), ("g1b_cpus", v.get("g1b_cpus") == r["g1b_cpus"]),
        ("harness_commit", v.get("harness_commit") == fam["g1b_pin"]),
        ("g1b_run_id", v.get("g1b_run_id") == fam["g1b_spec"]["run_id"]),
        ("g1b_spec_sha256", v.get("g1b_spec_sha256") == fam["g1b_spec"]["sha256"]),
        ("check_run_id", bool(run) and run.group("node") == node), ("check_spec_sha256", spec_ok),
        ("reference", isinstance(ref, dict) and ref.get("attempt") == decl["attempt"]
         and ref.get("job_record_sha256") == decl["job_record_sha256"]),
        ("budget_s", v.get("budget_s") == budget), ("attempts", atts_ok), ("complete", v.get("complete") is True),
        ("verdict", v.get("verdict") == "PASS" and "reason" in v and v.get("reason") is None)) if not ok]
    if problems:
        raise Stop(f"STOP: {rel} is not a fixed-seed determinism PASS of {node} on TASL-2 cpus {r['cpus']} "
                   f"({TASL2_CPU_ROW}): {problems}; its TASL-2 jobs wait")
    return {"node": node, "cpus": r["cpus"], "record": rel, "sha256": _sha_bytes(raw)}


SWITCH_STOP = "_switch_stop.json"
SWITCH_STOP_SCHEMA = "g5_tasl_switch_stop/1"


def switch_stop_path(spec: dict, node: str) -> Path:
    return Path(spec["worker"]["runs_root"]) / spec["run_id"] / node / SWITCH_STOP


def write_switch_stop(spec: dict, node: str, message: str, record: dict) -> Path:
    """Review round 2, N1: the switch's node STOP under XC3-FAIL B, recorded in the table's runs tree (TASL-2) as
    ``<run_id>/<node>/_switch_stop.json`` (``stop_class: node``, the verdict path and sha256, the rule, the time), so
    that ``g5_job.node_stopped`` and ``g5_seal.node_finished`` see it: no further job of the node starts, and the node,
    then the run, can be sealed (``seal_node`` copies the record into ``_node``). Written only here, once: an existing
    record is kept as it is (idempotent; the first STOP is the one on record)."""
    path = switch_stop_path(spec, node)
    if path.exists():
        return path
    rec = {"schema": SWITCH_STOP_SCHEMA, "run_id": spec["run_id"], "node": node, "stop": message, "stop_class": "node",
           "rule": "XC3-FAIL B (R1-T1-D21-SCOPE read to include the short cross-check)", "written_by": "g5_tasl.launch",
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **record}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x") as fh:
            fh.write(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    except FileExistsError:
        pass
    return path


def tasl7_host_check(spec: dict, read_main) -> dict:
    """The TASL-7 harness-isolation host check record (cited in the note's P1 and ``tasl7_audits`` line): on main at
    its sha256, PASS for TASL-7 at the seven nodes' G.1b pin, as the G.1b TASL-7 jobs required."""
    t = spec["tasl7_audits"]
    return G.check_host_record({"hostname": t["hostname"], "isolation_host_check": t["isolation_host_check"]},
                               PC.PIN_SEVEN, read_main)


# =============================================================================================== STOP 15
def list_main(prefix: str = "") -> list[str]:
    res = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-tree", "-r", "--name-only", "origin/main",
                          *(["--", prefix] if prefix else [])], capture_output=True, text=True)
    if res.returncode:
        raise Stop("STOP: cannot list published main")
    return res.stdout.splitlines()


def _cited(fields: dict, key: str, read_main, *, on_main: bool = True) -> tuple[str, str]:
    m = CITED.fullmatch(fields.get(key, ""))
    if not m:
        raise Stop(f"STOP 15: the completion record's {key} must read '<path> sha256 <64 hex>'")
    path, sha = m.groups()
    if on_main:
        raw = read_main(path) if _rel_ok(path) else None
        if raw is None or _sha_bytes(raw) != sha:
            raise Stop(f"STOP 15: {key} {path} is not on published main with sha256 {sha}")
    return path, sha


ENV_LINE = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+) freeze (?P<freeze>\S+) sha256 (?P<sha>[0-9a-f]{64}) python "
                      r"(?P<python>\d+\.\d+\.\d+) interpreter (?P<interp>/\S+)$")


def check_ar_record(spec: dict, spec_path: Path, *, read_main, list_main=list_main) -> dict:
    """G5-ARPEND A's completion record (§2.13, STOP 15; round-4 nit): exactly one file on published main matching
    ``docs/r1/reports/<dir>/G5_AR_PREREQUISITES_<YYYYMMDD>.md`` (none, or two or more, is a STOP), naming this spec's
    sha256 (every other path on main naming ``G5_AR_PREREQUISITES``, outside ``docs/r1/reviews/`` where its reviews
    live, is a STOP too: a near-miss name or a deeper directory is never silently ignored), with every cited file on
    main at its sha256, an independent review on main that names the record's path
    and sha256 with ``Verdict: ACCEPTED``, and an item for each of the spec's PENDING markers. Returns autoresearch's
    noise-floor copy, environment, tails and host check, which the switch then uses."""
    found = sorted(p for p in list_main() if RECORD_TOKEN in p and not p.startswith("docs/r1/reviews/"))
    odd = [p for p in found if not RECORD_NAME.fullmatch(p)]
    if odd:
        raise Stop(f"STOP 15: paths on published main that name {RECORD_TOKEN} but are not "
                   f"docs/r1/reports/<dir>/G5_AR_PREREQUISITES_<YYYYMMDD>.md: {odd[:5]}")
    if len(found) != 1:
        raise Stop(f"STOP 15: exactly one completion record G5_AR_PREREQUISITES_<YYYYMMDD>.md must be on published "
                   f"main; found {len(found)}: {found[:5]}")
    rel = found[0]
    raw = read_main(rel)
    if raw is None:
        raise Stop(f"STOP 15: cannot read {rel} from published main")
    rec_sha = _sha_bytes(raw)
    f = G._note_fields(raw)
    open_fields = sorted(k for k, v in f.items() if PLACEHOLDER.search(v) or L._placeholder(v))
    if open_fields:
        raise Stop(f"STOP 15: the completion record has unfilled fields: {open_fields}")
    for key, want in (("schema", "g5_ar_prerequisites/1"), ("node", AR), ("verdict", "PASS"),
                      ("g5_spec_sha256", L._sha_file(spec_path))):
        if f.get(key) != want:
            raise Stop(f"STOP 15: the completion record's {key} must be {want!r}")
    missing = [m for m in spec["ar_prerequisites"]["pending"] if m not in f]
    if missing:
        raise Stop(f"STOP 15: the completion record does not complete the spec's PENDING items {missing}")
    # the review of the record itself
    review = f.get("review", "")
    rv = read_main(review) if _rel_ok(review) and review.startswith("docs/r1/reviews/") else None
    text = rv.decode("utf-8", "replace") if rv is not None else ""
    if rv is None or rel not in text or rec_sha not in text or not VERDICT_ACCEPTED.search(text):
        raise Stop(f"STOP 15: the record's review must be on main, name {rel} and its sha256 {rec_sha}, and read "
                   f"'Verdict: ACCEPTED'")
    # P1: the TASL-2 host check at autoresearch's pin
    hc_path, hc_sha = _cited(f, "host_check", read_main)
    host = G.check_host_record({"hostname": spec["worker"]["hostname"],
                                "isolation_host_check": {"record": hc_path, "sha256": hc_sha}}, PC.PIN_AR, read_main)
    # P2: the third G.1b note
    note_path, _ = _cited(f, "g1b_note", read_main)
    if not AR_NOTE.fullmatch(note_path):
        raise Stop("STOP 15: g1b_note must be docs/r1/authorizations/g1b_ar_t1_tasl_<YYYYMMDD>.md")
    nf = G._note_fields(read_main(note_path))
    if nf.get("approved") != "true" or nf.get("run_id") != spec["noise_floor"]["ar"]["run_id"] or \
            nf.get("harness_commit") != PC.PIN_AR or \
            nf.get("spec_sha256") != spec["harness_families"]["G5-AR"]["g1b_spec"]["sha256"]:
        raise Stop("STOP 15: the third G.1b note must be signed, for run g1b-ar-tasl-20261122-a at harness 2d09f9a9, "
                   "binding the autoresearch G.1b spec this G.5 spec binds (harness_families.G5-AR.g1b_spec)")
    # the REL-T1-G1B copy of its sealed summary, with the D21 verdict
    copy_path, copy_sha = _cited(f, "noise_floor_copy", read_main)
    sealed_path, sealed_sha = _cited(f, "g1b_sealed_summary", read_main, on_main=False)
    if sealed_sha != copy_sha:
        raise Stop("STOP 15: the REL-T1-G1B copy is not byte-identical to the sealed summary it cites")
    floor = check_g1b_copy({"copy": copy_path, "sha256": copy_sha, "review": f.get("noise_floor_copy_review"),
                            "sealed_path": sealed_path},
                           schema=G.AR_SUMMARY_SCHEMA, run_id=spec["noise_floor"]["ar"]["run_id"], nodes=[AR],
                           read_main=read_main)
    d21 = "qualifies" if floor["qualifies_D21"][AR] else "does_not_qualify"     # recorded (R1-T1-D21-SCOPE)
    if f.get("d21_verdict") != d21:
        raise Stop(f"STOP 15: d21_verdict must be the copy's verdict ({d21})")
    # P10
    if f.get("tails") not in TAILS:
        raise Stop("STOP 15: tails must be gaussian or student_t (P10)")
    nu = None                                      # R1-G5-TAILS: tails_nu beside a student_t declaration only
    if f["tails"] == "student_t":
        nu = _parse_nu(f.get(TAILS_NU, ""))
        if nu is None:
            raise Stop(f"STOP 15: {TAILS_NU} must be a finite number > 2 where tails is student_t (R1-G5-TAILS)")
    elif TAILS_NU in f:
        raise Stop(f"STOP 15: {TAILS_NU} is refused where tails is gaussian (R1-G5-TAILS)")
    decl_path, _ = _cited(f, "tails_declaration", read_main)
    other = {"gaussian": "student_t", "student_t": "gaussian"}[f["tails"]]
    lines = [ln for ln in read_main(decl_path).decode("utf-8", "replace").splitlines() if AR in ln]
    word = lambda w, ln: re.search(rf"(?<![A-Za-z0-9_-]){w}(?![A-Za-z0-9_-])", ln)  # noqa: E731
    if not lines or not all(word(f["tails"], ln) and not word(other, ln) for ln in lines):
        raise Stop(f"STOP 15: the tails declaration {decl_path} must name {AR} with {f['tails']} (P10)")
    if nu is not None:                             # the declaration states the same nu on every line naming AR
        said = [[_parse_nu(m.group(1)) for m in NU_SAID.finditer(ln)] for ln in lines]
        if not all(v and all(x == nu for x in v) for v in said):
            display = str(nu).removesuffix(".0")
            raise Stop(f"STOP 15: the tails declaration {decl_path} must state nu = {display} for {AR} on each line "
                       f"naming it (R1-G5-TAILS)")
    # P9: the environment
    m = ENV_LINE.fullmatch(f.get("environment", ""))
    if not m:
        raise Stop("STOP 15: environment must read '<name> freeze <path> sha256 <hex> python <x.y.z> interpreter "
                   "<abs path>'")
    env = m.groupdict()
    freeze_raw = read_main(env["freeze"]) if _rel_ok(env["freeze"]) else None
    if freeze_raw is None or _sha_bytes(freeze_raw) != env["sha"]:
        raise Stop(f"STOP 15: the environment freeze {env['freeze']} is not on main with sha256 {env['sha']}")
    pe = spec["ar_prerequisites"]["proposed_environment"]
    proposed = (env["name"], env["freeze"], env["sha"], env["python"]) == \
        (pe["name"], f"sweep2/g1b/{pe['freeze']}", pe["sha256"], pe["python"])
    if proposed:
        if env["interp"] != spec["worker"]["env_python"].get(pe["name"]):
            raise Stop("STOP 15: the proposed environment must use the spec's interpreter for it")
        env_row = None
    else:                          # §2.13: a different environment needs the row that names its use for G.5 too
        env_row = f.get("environment_row", "")
        if not ROW_ID.fullmatch(env_row):
            raise Stop("STOP 15: an environment other than the proposed ar-cond7a needs environment_row")
        plan_row(env_row, read_main, terms=(env["name"], "G.5"))
    return {"record": rel, "sha256": rec_sha, "review": review, "host_check": host, "noise_floor": floor,
            "qualifies_D21": floor["qualifies_D21"][AR], "scope": floor["scope"][AR], "tails": f["tails"],
            **({TAILS_NU: nu} if nu is not None else {}),
            "environment": {"name": env["name"], "freeze": env["freeze"], "sha256": env["sha"],
                            "python": env["python"], "interpreter": env["interp"], "row": env_row}}


# =============================================================================================== STOP 14
def freeze_wait_check(spec: dict, *, today: date, released: list[str] = (), stopped: list[str] = (),
                      before_arms_frozen: bool = False, deadline: str | None = None) -> dict:
    """STOP 14 (§2.11). At a job start: a G.5 job on or after the release deadline cannot lead to that node's release
    by the deadline, so it STOPs for the author. Before the arms-frozen record (``before_arms_frozen``): every
    un-STOPped node released by the deadline and no node STOPped at G.5; otherwise STOP. Only an author row may freeze
    the arms without a node."""
    deadline = date.fromisoformat(deadline or spec["key_values"]["freeze_wait_release_date"])
    if before_arms_frozen:
        unknown = sorted((set(released) | set(stopped)) - set(T1_NODES))
        if unknown:
            raise Stop(f"STOP 14: unknown nodes {unknown}")
        if stopped:
            raise Stop(f"STOP 14: nodes STOPped at G.5 {sorted(stopped)}: the author decides before the arms-frozen "
                       f"record (only an author row may freeze the arms without them)")
        late = sorted(set(T1_NODES) - set(released) - set(stopped))
        if late and today < deadline:      # not yet: wait (a refusal, but not a STOP for the author)
            raise Stop(f"WAIT (not yet): the train/dev release of {late} is not done; the arms-frozen record waits "
                       f"until {deadline} ({(deadline - today).days} days left)")
        if late:
            raise Stop(f"STOP 14: the release deadline {deadline} has passed ({today}) and the train/dev release of "
                       f"{late} is not done: the coordinating agent STOPs for the author")
        return {"deadline": deadline.isoformat(), "released": sorted(released)}
    if today >= deadline:
        raise Stop(f"STOP 14: the freeze-wait release deadline {deadline} is reached ({today}): no further G.5 job; "
                   f"the coordinating agent STOPs for the author")
    return {"deadline": deadline.isoformat(), "days_left": (deadline - today).days}


# =============================================================================================== P5, STOP 13
ENGINE_FILES = ("manager_v2_diff.py", "campaign_v2_diff.py", "proposal_v2_diff.py", "pilot_g4.py")
TRACKG = "src/autoresearch/trackg/"
PATH_DIRS = (TRACKG, "nodes/", "third_party/", "configs/trackg/")
NOISE_FLOOR = TRACKG + "noise_floor.py"


def _ls(repo: Path, commit: str) -> set[str]:
    out = PC._git(repo, "ls-tree", "-r", "-z", "--name-only", commit).stdout
    return {p for p in out.split("\0") if p}


def _module_file(mod: str, files: set[str]) -> str | None:
    base = "src/" + mod.replace(".", "/")
    for cand in (base + ".py", base + "/__init__.py"):
        if cand in files:
            return cand
    return None


def import_closure(repo: Path, commit: str, root: str = NOISE_FLOOR) -> set[str]:
    """The files of ``autoresearch.*`` modules that ``root`` imports, transitively (absolute and relative imports,
    at any depth in the module, with the packages' ``__init__.py``). Dynamic loads (importlib, a file loaded by path)
    are not followed; the directories of the measurement path cover them."""
    files = _ls(repo, commit)
    if root not in files:
        raise Stop(f"STOP: {root} is not at {commit[:8]}")
    seen, todo = set(), [root]
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        seen.add(path)
        parts = path[len("src/"):-len(".py")].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        pkg_parts = parts if path.endswith("__init__.py") else parts[:-1]
        for i in range(1, len(pkg_parts) + 1):            # the packages a module import executes
            init = "src/" + "/".join(pkg_parts[:i]) + "/__init__.py"
            if init in files:
                todo.append(init)
        tree = ast.parse(PC._git(repo, "show", f"{commit}:{path}").stdout, filename=path)
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = pkg_parts[:len(pkg_parts) - (node.level - 1)]
                    mod = ".".join(base + ([node.module] if node.module else []))
                else:
                    mod = node.module or ""
                mods = [mod] + [f"{mod}.{a.name}" for a in node.names]
            for mod in mods:
                if mod.split(".")[0] != "autoresearch":
                    continue
                hit = _module_file(mod, files)
                if hit:
                    todo.append(hit)
    return seen


def measurement_paths(repo: Path, commit: str) -> tuple[list[str], set[str]]:
    """P5's measurement path at the G.1b pin: all of ``src/autoresearch/trackg/`` except the v2-diff engine files,
    plus ``nodes/``, ``third_party/``, ``configs/trackg/`` (``node_lib/`` is inside trackg), and every module of
    ``noise_floor``'s import closure outside trackg; only files present at the pin."""
    files = _ls(repo, commit)
    closure = import_closure(repo, commit)
    engine = {TRACKG + f for f in ENGINE_FILES}
    paths = {p for p in files if p.startswith(PATH_DIRS) and p not in engine} | closure
    return sorted(paths), closure


def measurement_path_check(repo: Path, g1b_pin: str, g5_commit: str) -> dict:
    """P5 per family (G5-7 against c025f89a, G5-AR against 2d09f9a9): the G.5 commit descends from its G.1b pin, no
    measurement-path file present at the pin differs (content, mode or type, or deleted), and ``noise_floor``'s import
    closure is the same at both commits (so no measurement-path module imports a file G.5 added)."""
    repo = Path(repo)
    pin, g5 = PC._commit(repo, g1b_pin), PC._commit(repo, g5_commit)
    if not PC._descends(repo, pin, g5):
        raise Stop(f"STOP: the G.5 commit {g5[:8]} does not descend from its G.1b pin {pin[:8]} (P5)")
    paths, closure = measurement_paths(repo, pin)
    all_changed = set(PC._changed(repo, pin, g5))
    changed = sorted(all_changed & set(paths))
    if changed:
        raise Stop(f"STOP: the measurement path differs between the G.1b pin {pin[:8]} and G.5 {g5[:8]}: {changed[:10]}")
    added = sorted(all_changed - _ls(repo, pin))
    bad_added = [a for a in added if a.startswith(NO_ADDITIONS) or (a.startswith(TRACKG) and a not in G5_TRACKG_ADDITIONS)]
    if bad_added:                                            # m4: a new file could shadow a module or config there
        raise Stop(f"STOP: G.5 adds files inside the measurement directories (only {list(G5_TRACKG_ADDITIONS)} may be "
                   f"added in trackg/): {bad_added[:10]}")
    closure_g5 = import_closure(repo, g5)
    if closure_g5 != closure:
        raise Stop(f"STOP: noise_floor's import closure changed at G.5 (a G.5 file entered the measurement path): "
                   f"{sorted(closure_g5 ^ closure)[:10]}")
    engine_in_closure = sorted(p for p in closure if p.rsplit("/", 1)[-1] in ENGINE_FILES and p.startswith(TRACKG))
    return {"g1b_pin": pin, "g5_commit": g5, "paths": len(paths), "closure": sorted(closure),
            "closure_outside_trackg": sorted(p for p in closure if not p.startswith(TRACKG)),
            "engine_files_in_closure": engine_in_closure,
            "g5_added": added}


def family_checkout(spec: dict, fam: str, git=G._sh) -> dict:
    """The node's family checkout at its G.5 commit and clean (only nodes/<node>/data links), as G.1b's
    ``harness_checkout``: a node at the other family's checkout STOPs (STOP 13)."""
    f = spec["harness_families"][fam]
    shim = {"hosts": {WORKER_HOST: {"harness_dir": f["harness_dir"]}}, "harness": {"commit": f["g5_commit"]}}
    try:
        return G.harness_checkout(shim, WORKER_HOST, git)
    except Stop as exc:
        raise Stop(f"STOP 13: {fam}: {exc}") from None


# =============================================================================================== P3 (G.4b)
def _tar_member(tar_path: Path, name: str) -> bytes:
    with tarfile.open(tar_path) as tar:
        try:
            member = tar.extractfile(name)
        except KeyError:
            member = None
        if member is None:
            raise Stop(f"STOP: {tar_path} has no {name}")
        return member.read()


def _dig(d: dict, path: tuple):
    for k in path:
        d = d.get(k) if isinstance(d, dict) else None
    return d


def _main_file(entry: dict, what: str, read_main) -> bytes:
    raw = read_main(entry["path"])
    if raw is None or _sha_bytes(raw) != entry["sha256"]:
        raise Stop(f"STOP: P3: the {what} {entry['path']} must be on published main with sha256 {entry['sha256']}")
    return raw


def pilot_basis_main_check(spec: dict, read_main) -> tuple[dict, str]:
    """P3's half on published main, at every job start on either host (review m5): ``check_pilot_basis``, then the G.4b
    result report, its corrigenda and its review at their sha256 (the report naming the run id, the G.4b spec sha256
    and each node's SEAL_RECEIPT.json, job_record.json and out.tar sha256; the review reading ``Verdict: ACCEPTED``
    and naming the report's sha256), the signed G.4b note at its sha256 (``approved: true``, the run id, the G.4b spec
    sha256), and the dates row R1-BX-D14-G4B naming G4B-DATES A and the eight-node recompute. Returns the G.4b spec and
    its sha256."""
    pilot, pilot_sha = check_pilot_basis(spec)
    pb = spec["pilot_basis"]
    raw = _main_file(pb["result_report"], "G.4b result report", read_main)
    _main_file(pb["corrigenda"], "G.4b result corrigenda", read_main)
    text = raw.decode("utf-8", "replace")
    needles = [pb["run_id"], pilot_sha] + [pb["sealed"][n][k] for n in pb["nodes"]
                                           for k in ("seal_receipt_sha256", "job_record_sha256", "out_tar_sha256")]
    missing = [x for x in needles if x not in text]
    if missing:
        raise Stop(f"STOP: P3: the G.4b result report {pb['result_report']['path']} does not name {missing}")
    review = _main_file(pb["review"], "review of the G.4b result", read_main).decode("utf-8", "replace")
    if "Verdict: ACCEPTED" not in review or pb["result_report"]["sha256"] not in review:
        raise Stop(f"STOP: P3: the review {pb['review']['path']} must read 'Verdict: ACCEPTED' and name the result "
                   f"report's sha256 {pb['result_report']['sha256']}")
    note_raw = _main_file(pb["note"], "signed G.4b note", read_main)
    fields = G._note_fields(note_raw)
    if fields.get("approved") != "true" or fields.get("run_id") != pb["run_id"] or \
            fields.get("spec_sha256") != pilot_sha:
        raise Stop(f"STOP: P3: the signed G.4b note {pb['note']['path']} must read approved: true, run_id "
                   f"{pb['run_id']} and spec_sha256 {pilot_sha}")
    plan_row(pb["dates_row"], read_main, terms=PILOT_DATES_TERMS)
    return pilot, pilot_sha


def pilot_basis_check(spec: dict, read_main) -> dict:
    """P3 in full, at every TASL-2 job start, where the G.4b seals are (R1-G5-DIFF-RECOUNT): ``pilot_basis_main_check``
    (the files on published main), then:
    - per node, the sealed attempt read by ``g4_tasl.read_sealed_summary`` against the G.4b spec (SHA256SUMS, receipt,
      run id, spec sha256, harness commit, RTX 4090, TASL-2, no STOP, a complete pilot summary), its receipt,
      job-record, out.tar and pilot-summary sha256 as declared, and the declared liveness equal to the pilot summary's;
    - ``dates`` equal to ``g4_tasl.recompute_dates`` on those summaries with this spec's parameters (``dates_params``,
      the eight nodes) on the declared day, i.e. what ``g5_tasl.py dates <spec> <sealed> --pilot-spec
      sweep2/t1_tasl/g4b_tasl_spec.json --today <day>`` prints (the G.4b result's ``dates_g5.json``).
    The G.4b sealed attempts must therefore stay in place on TASL-2 until G.5 is sealed."""
    pilot, pilot_sha = pilot_basis_main_check(spec, read_main)
    pb = spec["pilot_basis"]
    summaries, seals = {}, {}
    for node in pb["nodes"]:
        e = pb["sealed"][node]
        d = Path(e["sealed_path"])
        summary = T4.read_sealed_summary(d, pilot, pilot_sha)
        if summary.get("node") != node:
            raise Stop(f"STOP: P3: {d} is not a sealed attempt of {node}")
        got = {"seal_receipt_sha256": L._sha_file(d / "SEAL_RECEIPT.json"),
               "job_record_sha256": L._sha_file(d / "job_record.json"),
               "out_tar_sha256": L._sha_file(d / "out.tar"),
               "pilot_summary_sha256": _sha_bytes(_tar_member(d / "out.tar", PILOT_SUMMARY_MEMBER))}
        bad = sorted(k for k, v in got.items() if v != e[k])
        if bad:
            raise Stop(f"STOP: P3: the sealed G.4b attempt {d} differs from pilot_basis.sealed.{node}: {bad}")
        live = {k: _dig(summary, path) for k, path in PILOT_LIVENESS.items()}
        bad = sorted(k for k, v in live.items() if v != pb["liveness"][node][k])
        if bad:
            raise Stop(f"STOP: P3: pilot_basis.liveness.{node} differs from the sealed G.4b pilot summary: {bad}")
        summaries[node], seals[node] = summary, got
    rec = T4.recompute_dates(summaries, dates_params(spec), today=date.fromisoformat(pb["dates"]["today"]))
    got_dates = {k: rec[k] for k in PILOT_DATES_KEYS}
    bad = sorted(k for k in PILOT_DATES_KEYS if got_dates[k] != pb["dates"][k])
    if bad:
        raise Stop(f"STOP: P3: pilot_basis.dates differ from the R1-BX-D14 recompute on the sealed G.4b summaries "
                   f"(g5_tasl.py dates --pilot-spec): {bad}")
    return {"run_id": pb["run_id"], "spec_sha256": pilot_sha, "result_report": pb["result_report"]["path"],
            "note": pb["note"]["path"], "dates_row": pb["dates_row"], "seals": seals, "liveness": pb["liveness"],
            "dates": got_dates}


# =============================================================================================== dates: TASL-7 audits
WAVE_SHARES = {1: 4, 2: 8}            # instances per wave (WAVES: 1-4 and 5-12), of 12


def default_tasl7_nodes(spec: dict, read_main, list_main=None) -> list[str]:
    """The ``--tasl7-nodes`` default (revision 13): every one of the seven G5-7 nodes whose cross-host PASS is on
    published main as ``check_crosshost_pass`` reads it, the xc2 verdicts of the three TASL-7 G.1b nodes and the xc3
    short verdicts of the other four (with XC3-FAIL and ``skip_nodes`` read from main); a node without one is left out.
    Autoresearch never (its audits stay on TASL-2)."""
    out = []
    for node in SEVEN:
        try:
            check_crosshost_pass(spec, node, read_main, list_main)
        except Stop:
            continue
        out.append(node)
    return out


def tasl7_dates(rec: dict, spec: dict, nodes: list[str], *, read_main=None, list_main=None,
                source: str = "explicit") -> dict:
    """R1-BX-D14 dates with G.5 audit chunks also on TASL-7 (R1-G5-AUDIT-TWO-CARDS), from the one-slot recompute ``rec``
    (``g4_tasl.recompute_dates`` on this spec), as far as ``g5_job``'s schedule allows:

    - only audit chunks of the given G5-7 nodes (``nodes``, each eligible for TASL-7, i.e. with a cross-host PASS;
      autoresearch never), never a campaign wave. With ``read_main``, each node's PASS is looked up on main and
      reported (``crosshost``); a node without one is computed as a scenario;
    - per node and wave, the wave's chunks as ``g5_job.chunk_plan`` cuts them (census run time x 1.25 x 1.5 per run,
      up to ``CHUNK_LIMIT_S``) for the projected runs: ceil((audited + parents) x the wave's share of the 12
      instances) units x the K audit seeds. Chunk 0 is taken by the TASL-2 job that makes the wave's plan
      (``next_chunk``; a claim before the plan is refused) and the last chunk computes E5 on TASL-2 (``claim_chunk``),
      so only chunks 1 .. n-2 can run on TASL-7: each with its runs x the 4090 run time x the audit inflation, plus
      one startup;
    - TASL-7's card serves the proposer while any campaign wave runs (its lease), so a TASL-7 audit chunk never
      overlaps a campaign: the label span is at least TASL-2's load and at least the campaign hours plus TASL-7's audit
      hours, TASL-7 taking x = min(its claimable hours, half the non-campaign hours); and at least each node's own
      serial work less its claimable TASL-7 hours (autoresearch: all of it);
    - the dates follow from that span as ``g4_lib.recompute_dates`` does (prerequisite, G.1b and queue days, then the
      R1-BX-D14 spans). The GPU-hours stay the one-slot total: a TASL-7 audit chunk does the same work on the same GPU
      model, counted inside the cap (the recommended reading; the note's ``cap_gpu_hours`` line fixes it).

    A planning estimate for the coordinating chat; it gates nothing and is not P3's ``pilot_basis.dates``."""
    import g5_job                                           # noqa: PLC0415 - g5_job imports this module
    if options(spec)["G5-TASL-GPUH"] == "B":
        raise Stop("STOP: TASL-7 audit chunks are not built under G5-TASL-GPUH B (g5_job.tasl7_eligible)")
    if len(set(nodes)) != len(nodes):
        raise Stop("STOP: --tasl7-nodes names a node twice")
    bad = [n for n in nodes if n not in SEVEN or node_entry(spec, n)["family"] not in spec["tasl7_audits"]["families"]]
    if bad:
        raise Stop(f"STOP: {bad} cannot run audit chunks on {AUDIT_HOST} (the G5-7 family's seven nodes only; "
                   f"{AR}'s audits stay on {WORKER_HOST})")
    k = rec["binding_K"]
    per = rec["g5_by_K"][str(k)]["per_node"]
    params = rec["params"]
    seeds = audit_seeds(spec, k)
    seed_list = seeds["label"] + seeds["evaluation"]
    infl, startup_h = float(params["audit_inflation"]), float(params["startup_s"]) / 3600
    total = rec["g5_total_gpu_hours"]
    campaign_h = sum(v["campaign_gpu_hours"] for v in per.values()) + 2 * len(per) * startup_h
    rows, claimable_h = {}, {}
    for node in nodes:
        n_entry, row = node_entry(spec, node), per[node]
        status = "not looked up"
        if read_main is not None:
            try:
                check_crosshost_pass(spec, node, read_main, list_main)
                status = "cross-host PASS on main"
            except Stop:
                status = "no cross-host PASS on main (a scenario)"
        waves, node_h = {}, 0.0
        for wave, share in WAVE_SHARES.items():
            units = math.ceil((row["audited"] + row["parents"]) * share / 12)
            plan = {"units": [{"unit": f"u{i}"} for i in range(units)], "seeds": seed_list}
            sizes = [len(c) for c in g5_job.chunk_plan(plan, n_entry)]
            mid = list(range(1, len(sizes) - 1))
            h = float(sum(sizes[i] * row["inputs"]["run_s"] * infl / 3600 + startup_h for i in mid))
            waves[str(wave)] = {"units": units, "runs": sum(sizes), "chunks": len(sizes), "chunk_runs": sizes,
                                "tasl7_claimable_chunks": mid, "tasl7_claimable_gpu_hours": round(h, 2)}
            node_h += h
        claimable_h[node] = node_h
        rows[node] = {"crosshost": status, "census_run_seconds": n_entry["run_seconds"],
                      "run_s_4090": row["inputs"]["run_s"], "waves": waves,
                      "tasl7_claimable_gpu_hours": round(node_h, 2)}
    h7 = sum(claimable_h.values())
    x = min(h7, max(0.0, (total - campaign_h) / 2))
    longest = max(v["gpu_hours"] - claimable_h.get(n, 0.0) for n, v in per.items())
    label_h = max(total - x, campaign_h + x, longest)
    wall_days = math.ceil(float(params["prerequisite_days"]) + float(params.get("g1b_days", 0))
                          + float(params["queue_days"]) + label_h / 24.0)
    labels_done = date.fromisoformat(rec["today"]) + timedelta(days=wall_days)
    b7 = labels_done + timedelta(days=int(params["analysis_days_to_b7"]))
    d3 = b7 + timedelta(days=int(params["b7_to_d3_days"]))
    manuscript = d3 + timedelta(days=int(params["d3_to_manuscript_days"]))
    targets = {key: date.fromisoformat(v) for key, v in rec["targets_R1_BX_D14"].items()}
    got = {"B7": b7, "D3": d3, "manuscript": manuscript}
    return {"rule": f"{TWO_CARDS_ROW}: audit chunks of eligible nodes on {AUDIT_HOST} while no campaign wave holds the "
                    f"server; never a wave's first chunk (it makes the plan on {WORKER_HOST}) or its last (E5)",
            "nodes": list(nodes), "nodes_source": source, "per_node": rows, "binding_K": k,
            "campaign_gpu_hours_with_startup": round(campaign_h, 2), "tasl7_claimable_gpu_hours": round(h7, 2),
            "tasl7_gpu_hours_used": round(x, 2), "tasl2_gpu_hours": round(total - x, 2),
            "label_span_hours": round(label_h, 2),
            "label_span_hours_one_slot": round(max(total, rec["longest_node_gpu_hours"]), 2),
            "longest_node_gpu_hours_with_tasl7": round(longest, 2),
            "gpu_hours_counted": total, "cap_gpu_hours": rec["g5_cap_gpu_hours"],
            "gpu_hours_reading": "TASL-7 audit chunk hours counted inside the cap (recommended reading; the G.5 note's "
                                 "cap_gpu_hours line fixes it)",
            "labels_done": labels_done.isoformat(), "B7": b7.isoformat(), "D3": d3.isoformat(),
            "manuscript": manuscript.isoformat(),
            "slack_days": {key: (targets[key] - got[key]).days for key in targets},
            "note": "a planning estimate (targets, not gates: R1-BX-D14-G4B); not pilot_basis.dates (P3)"}


# =============================================================================================== the switch
IMPORT_SOURCES = {**T4.IMPORT_SOURCES, "g4_tasl": "sweep2/t1_tasl/g4_tasl.py",
                  "g5_pin_check": "sweep2/t1_tasl/g5_pin_check.py", "g5_tasl": "sweep2/t1_tasl/g5_tasl.py",
                  "g1b_crosscheck": "sweep2/t1_tasl/g1b_crosscheck.py", "g1b_tasl_join": "sweep2/t1_tasl/g1b_tasl_join.py",
                  "g5_job": "sweep2/t1_tasl/g5_job.py", "g5_seal": "sweep2/t1_tasl/g5_seal.py",
                  "g5_assemble": "sweep2/t1_tasl/g5_assemble.py", "g5_relcopy": "sweep2/t1_tasl/g5_relcopy.py",
                  "g5_features": "sweep2/t1_tasl/g5_features.py", "g5_noise": "sweep2/t1_tasl/g5_noise.py"}


def check_import_sources(repo: Path = None) -> dict:
    """As ``g4_tasl.check_import_sources``, over the modules this script imports."""
    repo = Path(repo or REPO_ROOT).resolve()
    out = {}
    for name, rel in IMPORT_SOURCES.items():
        mod = sys.modules.get(name)
        if mod is None:
            continue
        got = Path(getattr(mod, "__file__", "") or "").resolve()
        if got != repo / rel:
            raise Stop(f"STOP: module {name} was imported from {got}, not the reviewed {rel}")
        out[name] = rel
    return out


def job_runner(spec_path, node_name, job, context) -> dict:
    """The real job entry (part 3b-1): ``g5_job.run_job``, reached only through ``launch`` after every check."""
    import g5_job                                            # noqa: PLC0415 - g5_job imports this module
    check_import_sources()                                   # again, now that g5_job is imported (3b-1 review m4)
    return g5_job.run_job(spec_path, node_name, job, context)


def launch(spec_path: Path, note_path: Path, node_name: str, *, job: str, enable: bool, today: date,
           on_main=G._note_on_main, read_main=G._read_main, list_main=list_main, pin_check=None, mpath_check=None,
           checkout=None, launch_binding=None, runner=None, server_record: Path | None = None,
           host: str = WORKER_HOST, chunk: int | None = None, pilot_check=None, pilot_main_check=None) -> dict:
    """The G.5 switch at every job start (§9). Off unless both keys are given; every check below must pass before the
    runner is called (the default runner is ``g5_job.run_job``, part 3b-1). ``server_record``: the proposer's
    ``server_record.json`` copied from TASL-7, for campaign jobs. ``host``: TASL-2, or TASL-7 for an audit chunk under
    R1-G5-AUDIT-TWO-CARDS (``chunk``: the claimed chunk; the G5-7 family only; the node's cross-host PASS and the TASL-7
    host check on main; under ``cuda_ipc: c12`` TASL-7's C12 record; the TASL-7 checkout of the G5-7 commit).
    ``pilot_check``: P3 in full at a TASL-2 job start (default ``pilot_basis_check``: the files on main and the sealed
    G.4b attempts, which are on TASL-2); ``pilot_main_check``: P3's half on main at a TASL-7 job start (default
    ``pilot_basis_main_check``; review m5)."""
    if job not in JOBS:
        raise Stop(f"STOP: job must be one of {JOBS}")
    if host not in JOB_HOSTS:
        raise Stop(f"STOP: host must be one of {JOB_HOSTS}")
    if host == AUDIT_HOST and not job.startswith("audits"):
        raise Stop(f"STOP: only audit chunks run on {AUDIT_HOST}; campaign waves keep one worker slot on {WORKER_HOST} "
                   f"({TWO_CARDS_ROW})")
    if (host == AUDIT_HOST) != (chunk is not None):
        raise Stop(f"STOP: a {AUDIT_HOST} audit job names its claimed chunk; a {WORKER_HOST} job takes none")
    spec = load_spec(spec_path)
    validate_spec(spec, launch=True)
    node = node_entry(spec, node_name)
    if host == AUDIT_HOST and node["family"] not in spec["tasl7_audits"]["families"]:
        raise Stop(f"STOP: {node_name}'s audits stay on {WORKER_HOST} (family {node['family']}; ar-cond7a exists only "
                   f"there)")
    fields = check_note(note_path, spec_path, spec=spec, on_main=on_main, read_main=read_main)
    if not enable or os.environ.get(ENABLE_ENV) != "1":
        raise Stop(f"STOP: real G.5 runs are disabled (needs --enable AND {ENABLE_ENV}=1)")
    o = options(spec)
    context: dict = {"job": job, "K": fields["_K"], "K_row": fields["_K_row"], "options": o, "host": host}
    if chunk is not None:
        context["chunk"] = chunk
    if job.startswith("audits"):
        context["audit_seeds"] = audit_seeds(spec, fields["_K"])
    rows = list(PLAN_ROWS)
    for row, terms in decision_row_checks(spec, o):
        plan_row(row, read_main, terms=terms)
        rows.append(row)
    plan_row(T1_FEAT_ROW, read_main, terms=T1_FEAT_TERMS)        # R1-T1-FEAT-DECISIONS: STOP until it is on main
    rows.append(T1_FEAT_ROW)
    for row, terms in ((D21_SCOPE_ROW, D21_SCOPE_TERMS), (TWO_CARDS_ROW, TWO_CARDS_TERMS),
                       (PILOT_DATES_ROW, PILOT_DATES_TERMS),          # R1-T1-D21-SCOPE, two cards; P3's dates row
                       (TASL2_CPU_ROW, TASL2_CPU_TERMS)):             # TASL-2 CPUs 8-11 (revision 13)
        plan_row(row, read_main, terms=terms)
        rows.append(row)
    if fields["_K_row"]:
        rows.append(fields["_K_row"])
    fam = node["family"]
    seven_check = spec["harness_families"]["G5-7"]["isolation_host_check"]
    context["host_check"] = {"G5-7": G.check_host_record({"hostname": spec["worker"]["hostname"],
                                                          "isolation_host_check": seven_check}, PC.PIN_SEVEN,
                                                         read_main)}
    if spec["key_values"]["cuda_ipc"]["mode"] == "c12":                                              # P1 (M1)
        context["cuda_ipc"] = check_c12(spec, read_main)
        if host == AUDIT_HOST:                                      # R1-G5-AUDIT-TWO-CARDS: TASL-7's own C12 record
            context["cuda_ipc_tasl7"] = check_c12(spec, read_main, host=AUDIT_HOST)
    if host == WORKER_HOST:                                         # P3 in full: the sealed G.4b attempts are on TASL-2
        context["pilot_basis"] = (pilot_check or pilot_basis_check)(spec, read_main)
    else:                                                           # P3's half on main (review m5)
        pm = (pilot_main_check or pilot_basis_main_check)(spec, read_main)
        context["pilot_basis"] = {"main_only": True, "spec_sha256": pm[1] if isinstance(pm, tuple) else pm}
    seven = check_seven_copy(spec, read_main)                                                       # M3
    context["noise_floor"] = {"seven": seven}
    ar_copy = None
    if fam == "G5-AR":
        if o["G5-ARPEND"] == "A":
            rec = check_ar_record(spec, spec_path, read_main=read_main, list_main=list_main)        # STOP 15
            context.update(ar_record=rec, ar_environment=rec["environment"], ar_tails=rec["tails"])
            context["host_check"]["G5-AR"] = rec["host_check"]
            verdict_scope = rec["scope"]
            ar_copy = rec["noise_floor"]
            if rec["environment"]["row"]:
                rows.append(rec["environment"]["row"])
        else:
            context["host_check"]["G5-AR"] = G.check_host_record(
                {"hostname": spec["worker"]["hostname"],
                 "isolation_host_check": spec["harness_families"]["G5-AR"]["isolation_host_check"]}, PC.PIN_AR,
                read_main)
            ar = check_g1b_copy(spec["noise_floor"]["ar"], schema=G.AR_SUMMARY_SCHEMA,
                                run_id=spec["noise_floor"]["ar"]["run_id"], nodes=[AR], read_main=read_main)
            context["noise_floor"]["ar"] = ar
            verdict_scope = ar["scope"][AR]
            ar_copy = ar
        context["floor_by_node"] = floor_by_node(seven, ar_copy)          # the eight nodes joined by node
    else:
        verdict_scope = seven["scope"][node_name]
        if node_name in X_NODES:            # the G.1b cross-host gate (where run): the gate record names the node
            context["g1b_crosshost_gate"] = json.loads(seven["gate_raw"])["nodes"][node_name]
    # R1-T1-D21-SCOPE: STOP 5 is fixed-seed determinism; the D21 value is recorded for the funnel, not a STOP
    if not verdict_scope["deterministic"]:
        raise NodeStop(f"STOP 5: {node_name} has no G.1b fixed-seed determinism PASS (R1-T1-D21-SCOPE): not run in "
                       f"G.5; the author decides on T2 (R1-BX-D12)")
    context["d21"] = verdict_scope["d21"]
    try:
        context["xc3_b"] = xc3_b_check(spec, node_name, read_main, list_main)     # XC3-FAIL B, read from main
    except NodeStop as exc:                   # review round 2, N1: the B STOP is recorded in the table's runs tree
        if host == WORKER_HOST:
            write_switch_stop(spec, node_name, str(exc), getattr(exc, "record", None) or {})
        raise
    context["noise_precheck"] = noise_precheck(ar_copy if fam == "G5-AR" else seven, node_name, read_main)   # m6
    if host == AUDIT_HOST:                                           # R1-G5-AUDIT-TWO-CARDS
        context["crosshost_pass"] = check_crosshost_pass(spec, node_name, read_main, list_main)
        context["host_check"][AUDIT_HOST] = tasl7_host_check(spec, read_main)
    else:                    # R1-TASL2-CPU: a replacement set's fixed-seed determinism record before its first use
        context["tasl2_cpuset"] = check_cpuset_record(spec, node_name, read_main, list_main)
    context["freeze_wait"] = freeze_wait_check(spec, today=today, deadline=fields["_freeze"])        # STOP 14
    fams = spec["harness_families"]
    repo = Path(fams[fam]["harness_dir"])
    try:
        context["pin_check"] = (pin_check or PC.check)(repo, fams["G5-7"]["g5_commit"], fams["G5-AR"]["g5_commit"])
    except PC.Stop as exc:                                                                          # STOP 13
        raise Stop(f"STOP 13: {exc}") from None
    context["checkout"] = (checkout or family_checkout)(spec, fam)
    context["measurement_path"] = (mpath_check or measurement_path_check)(repo, fams[fam]["g1b_pin"],
                                                                         fams[fam]["g5_commit"])     # P5
    if context["measurement_path"].get("g5_commit") != fams[fam]["g5_commit"]:
        raise Stop("STOP: the measurement-path check ran on another commit")

    def bind(repo_root, s, r):
        imports = check_import_sources(repo_root)        # first: no shadowed module's code runs as the binding
        return {**G.verify_launch_tasl(repo_root, s, r, spec_path=spec_path), "imports": imports}
    context["launch"] = (launch_binding or bind)(REPO_ROOT, spec, tuple(rows))
    if server_record is not None:
        context["server_record"] = str(server_record)
    return (runner or job_runner)(spec_path, node_name, job, context) | {"context": context}


# =============================================================================================== CLI
def part_3b2(a) -> dict:
    """The part 3b-2 commands behind the same gates as ``close-attempt``: the spec validated for launch (the copy step,
    which precedes the signature, without launch) and the import-source check after the lazy imports."""
    import g5_assemble                                       # noqa: PLC0415 - g5_seal and g5_job come with it
    import g5_relcopy                                        # noqa: PLC0415
    check_import_sources()
    spec_path = Path(a.spec)
    spec = load_spec(spec_path)
    validate_spec(spec, launch=a.cmd != "rel-copy")
    SE = g5_assemble.SE
    if a.cmd == "seal-attempt":
        return SE.seal_attempt(spec, Path(a.attempt_dir))
    if a.cmd == "seal-node":
        return SE.seal_node(spec, a.node)
    if a.cmd == "seal-run":
        return SE.seal_run(spec, not_run=tuple(a.not_run))
    if a.cmd == "seal-server":
        return SE.seal_server(spec, Path(a.server_dir))
    if a.cmd == "close-server":
        return SE.close_server(spec, Path(a.server_dir), a.reason)
    if a.cmd == "server-span":
        return SE.register_server_span(spec, Path(a.receipt))
    if a.cmd == "rel-copy":
        return g5_relcopy.copy_summary(spec, a.kind, Path(a.summary), a.dest)
    if spec_path.resolve() != (REPO_ROOT / g5_assemble.SPEC_REL).resolve():
        raise Stop(f"STOP: the assembly uses the committed spec {g5_assemble.SPEC_REL} (the release check re-derives "
                   f"from it)")
    return g5_assemble.assemble(spec_path, a.stage, Path(a.table), Path(a.evidence),
                                note_path=Path(a.note) if a.note else None)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec"); v.add_argument("--launch", action="store_true")
    op = sub.add_parser("options"); op.add_argument("spec"); op.add_argument("--set", action="append", default=[],
                                                                               help="DECISION=OPTION")
    kl = sub.add_parser("key-lines"); kl.add_argument("spec"); kl.add_argument("--k", type=int, default=10)
    kl.add_argument("--k-row")
    cn = sub.add_parser("check-note"); cn.add_argument("spec"); cn.add_argument("--note", required=True)
    cn.add_argument("--draft", action="store_true")
    ar = sub.add_parser("check-ar-record"); ar.add_argument("spec")
    mp = sub.add_parser("measurement-path"); mp.add_argument("repo"); mp.add_argument("g1b_pin")
    mp.add_argument("g5_commit")
    fw = sub.add_parser("freeze-wait"); fw.add_argument("spec"); fw.add_argument("--today", required=True)
    fw.add_argument("--released", nargs="*", default=[]); fw.add_argument("--stopped", nargs="*", default=[])
    fw.add_argument("--before-arms-frozen", action="store_true")
    dt = sub.add_parser("dates"); dt.add_argument("spec"); dt.add_argument("sealed", nargs="*")
    dt.add_argument("--today", required=True)
    dt.add_argument("--pilot-spec", help="the G.4b re-pilot spec whose sealed attempts are given (R1-G5-DIFF-RECOUNT; "
                                         "P3's basis); default g4_tasl_spec.json (the G.4 pilot, kept for history)")
    dt.add_argument("--tasl7-audits", action="store_true",
                    help="also count G.5 audit chunks on TASL-7 (R1-G5-AUDIT-TWO-CARDS): a tasl7_audits block with its "
                         "own dates (R1-BX-D14-G4B's recompute); the one-slot values are unchanged")
    dt.add_argument("--tasl7-nodes", nargs="*",
                    help="with --tasl7-audits: the nodes eligible for TASL-7 audit chunks (default: the G5-7 nodes whose "
                         "cross-host PASS is on origin/main: the xc2 and the xc3 short verdicts)")
    pbc = sub.add_parser("pilot-basis"); pbc.add_argument("spec")
    r = sub.add_parser("run"); r.add_argument("spec"); r.add_argument("--note", required=True)
    r.add_argument("--node", required=True); r.add_argument("--job", required=True, choices=JOBS)
    r.add_argument("--enable", action="store_true"); r.add_argument("--server-record")
    r.add_argument("--host", default=WORKER_HOST, choices=JOB_HOSTS)
    r.add_argument("--chunk", type=int, help="TASL-7 only: the claimed chunk (R1-G5-AUDIT-TWO-CARDS)")
    cc = sub.add_parser("claim-chunk"); cc.add_argument("spec"); cc.add_argument("--node", required=True)
    cc.add_argument("--wave", type=int, required=True, choices=(1, 2)); cc.add_argument("--chunk", type=int, required=True)
    rg = sub.add_parser("register-chunk"); rg.add_argument("spec"); rg.add_argument("attempt_dir")
    rg.add_argument("--node", required=True); rg.add_argument("--wave", type=int, required=True, choices=(1, 2))
    rg.add_argument("--chunk", type=int, required=True)
    rg.add_argument("--access-log", required=True, help="a copy of TASL-7's <run_id>/_access_log.jsonl")
    rg.add_argument("--node-log", help="a copy of the TASL-7 node wrapper log the attempt's record names")
    ab = sub.add_parser("abandon-claim"); ab.add_argument("spec"); ab.add_argument("--node", required=True)
    ab.add_argument("--wave", type=int, required=True, choices=(1, 2)); ab.add_argument("--chunk", type=int, required=True)
    ab.add_argument("--reason", required=True); ab.add_argument("--access-log", required=True)
    fr = sub.add_parser("finalize-remote"); fr.add_argument("spec"); fr.add_argument("--access-log", required=True)
    sv = sub.add_parser("serve"); sv.add_argument("spec"); sv.add_argument("--note", required=True)
    sv.add_argument("--enable", action="store_true")
    for name in ("cpus", "logdir"):
        q = sub.add_parser(name); q.add_argument("spec"); q.add_argument("--node", required=True)
        q.add_argument("--host", default=WORKER_HOST, choices=JOB_HOSTS)
    cs2 = sub.add_parser("cpuset-spec", help="R1-TASL2-CPU: the derived G.1b spec of a replacement set's check")
    cs2.add_argument("spec"); cs2.add_argument("--node", required=True); cs2.add_argument("--run-id", required=True)
    cs2.add_argument("--out", required=True, help="written once (no overwrite)")
    cv = sub.add_parser("cpuset-verdict", help="R1-TASL2-CPU: the fixed-seed determinism record of a replacement set")
    cv.add_argument("spec"); cv.add_argument("--node", required=True); cv.add_argument("--check-spec", required=True)
    cv.add_argument("--reference", required=True, help="the node's sealed G.1b TASL-2 attempt (declared in the xc3 spec)")
    cv.add_argument("--attempt", action="append", required=True, help="a sealed attempt of the check (repeat)")
    ca = sub.add_parser("close-attempt"); ca.add_argument("spec"); ca.add_argument("attempt_dir")
    ca.add_argument("--node", required=True); ca.add_argument("--job", required=True, choices=JOBS)
    ca.add_argument("--chunk", type=int); ca.add_argument("--reason", required=True)
    wc = sub.add_parser("wave-checks"); wc.add_argument("spec"); wc.add_argument("--node", required=True)
    wc.add_argument("--wave", type=int, required=True, choices=(1, 2))
    # part 3b-2: the seal (TASL-2; seal-server on TASL-7), the spans, the REL-T1-G1B copy, the locked assembly
    sa = sub.add_parser("seal-attempt"); sa.add_argument("spec"); sa.add_argument("attempt_dir")
    sn = sub.add_parser("seal-node"); sn.add_argument("spec"); sn.add_argument("--node", required=True)
    sr = sub.add_parser("seal-run"); sr.add_argument("spec"); sr.add_argument("--not-run", nargs="*", default=[])
    ss = sub.add_parser("seal-server"); ss.add_argument("spec"); ss.add_argument("server_dir")
    cs = sub.add_parser("close-server"); cs.add_argument("spec"); cs.add_argument("server_dir")
    cs.add_argument("--reason", required=True)
    sp = sub.add_parser("server-span"); sp.add_argument("spec"); sp.add_argument("receipt")
    rc = sub.add_parser("rel-copy"); rc.add_argument("spec"); rc.add_argument("--kind", required=True,
                                                                            choices=("seven", "ar"))
    rc.add_argument("--summary", required=True); rc.add_argument("--dest", required=True)
    asm = sub.add_parser("assemble"); asm.add_argument("spec"); asm.add_argument("--stage", required=True,
                                                                               choices=("traindev", "test"))
    asm.add_argument("--table", required=True); asm.add_argument("--evidence", required=True)
    asm.add_argument("--note", help="the signed note docs/r1/authorizations/<run_id>.md (its t1_table_readings line); "
                                    "without it only the refuse reading applies")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate":
            out = validate_spec(load_spec(Path(a.spec)), launch=a.launch)
            out.pop("spec")
            print(json.dumps({"ok": True, **out}, indent=1))
        elif a.cmd == "options":
            choices = dict(s.split("=", 1) for s in a.set)
            print(json.dumps(apply_options(load_spec(Path(a.spec)), choices), indent=1, ensure_ascii=False))
        elif a.cmd == "key-lines":
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            lines = {"approved": "true", **note_lines(spec, k=a.k, k_row=a.k_row),
                     "paper_commit": spec["paper"]["commit"], "spec_sha256": L._sha_file(Path(a.spec))}
            print("\n".join(f"{key}: {value}" for key, value in lines.items()))
        elif a.cmd == "check-note":
            spec = load_spec(Path(a.spec))
            validate_spec(spec, launch=not a.draft)
            fields = check_note(Path(a.note), Path(a.spec), spec=spec, draft=a.draft)
            print(json.dumps({"ok": True, "K": fields["_K"], "mode": "draft" if a.draft else "strict"}, indent=1))
        elif a.cmd == "check-ar-record":
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            out = check_ar_record(spec, Path(a.spec), read_main=G._read_main)
            out["noise_floor"].pop("raw", None)
            print(json.dumps(out, indent=1))
        elif a.cmd == "measurement-path":
            print(json.dumps(measurement_path_check(Path(a.repo), a.g1b_pin, a.g5_commit), indent=1))
        elif a.cmd == "freeze-wait":
            print(json.dumps(freeze_wait_check(load_spec(Path(a.spec)), today=date.fromisoformat(a.today),
                                               released=a.released, stopped=a.stopped,
                                               before_arms_frozen=a.before_arms_frozen), indent=1))
        elif a.cmd == "serve":
            import g5_job                                    # noqa: PLC0415
            check_import_sources()
            print(json.dumps(g5_job.serve_launch(Path(a.spec), Path(a.note), enable=a.enable), indent=1,
                             default=str))
        elif a.cmd in ("cpus", "logdir"):
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            node = node_entry(spec, a.node)
            w = spec["worker"] if a.host == WORKER_HOST else spec["tasl7_audits"]        # g5t7: TASL-7's own values
            cpus = tasl2_node_cpus(spec, a.node) if a.host == WORKER_HOST else (node.get("cpus") or w["cpus"])
            print(cpus if a.cmd == "cpus" else str(Path(w["runs_root"]) / spec["run_id"] / "_logs"))
        elif a.cmd == "cpuset-spec":
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            data = _derived_bytes(cpuset_spec(spec, a.node, a.run_id))
            try:
                with Path(a.out).open("xb") as fh:
                    fh.write(data)
            except FileExistsError:
                raise Stop(f"STOP: {a.out} exists (no overwrite)") from None
            print(json.dumps({"ok": True, "path": a.out, "sha256": _sha_bytes(data)}, indent=1))
        elif a.cmd == "cpuset-verdict":
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            print(json.dumps(cpuset_verdict(spec, a.node, Path(a.check_spec), Path(a.reference),
                                            [Path(x) for x in a.attempt]), indent=1, sort_keys=True))
        elif a.cmd == "close-attempt":
            import g5_job                                    # noqa: PLC0415
            check_import_sources()
            spec = load_spec(Path(a.spec))
            validate_spec(spec, launch=True)
            print(json.dumps(g5_job.close_attempt(spec, Path(a.spec), a.node, a.job, Path(a.attempt_dir), a.reason,
                                                  chunk=a.chunk), indent=1))
        elif a.cmd in ("claim-chunk", "register-chunk", "abandon-claim", "finalize-remote"):   # TWO-CARDS, TASL-2
            import g5_job                                    # noqa: PLC0415
            check_import_sources()
            spec = load_spec(Path(a.spec))
            validate_spec(spec, launch=True)
            sp = Path(a.spec)
            if a.cmd == "claim-chunk":
                out = g5_job.claim_chunk(spec, sp, a.node, a.wave, a.chunk)
            elif a.cmd == "register-chunk":
                out = g5_job.register_attempt(spec, sp, Path(a.attempt_dir), a.node, a.wave, a.chunk,
                                              Path(a.access_log), node_log=Path(a.node_log) if a.node_log else None)
            elif a.cmd == "abandon-claim":
                out = g5_job.abandon_claim(spec, sp, a.node, a.wave, a.chunk, a.reason, Path(a.access_log))
            else:
                out = g5_job.finalize_remote(spec, sp, Path(a.access_log))
            print(json.dumps(out, indent=1))
        elif a.cmd == "wave-checks":
            import g5_job                                    # noqa: PLC0415
            spec = load_spec(Path(a.spec))
            validate_spec(spec, launch=True)
            print(json.dumps(g5_job.wave_checks(spec, a.node, a.wave), indent=1))
        elif a.cmd in ("seal-attempt", "seal-node", "seal-run", "seal-server", "close-server", "server-span",
                       "rel-copy", "assemble"):
            print(json.dumps(part_3b2(a), indent=1, default=str))
        elif a.cmd == "dates":
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            g4spec, g4sha = dates_pilot_spec(a.pilot_spec)
            summaries = {}
            for sealed in a.sealed:
                s = T4.read_sealed_summary(Path(sealed), g4spec, g4sha)
                if s["node"] in summaries:
                    raise Stop(f"STOP: two sealed attempts given for {s['node']}")
                summaries[s["node"]] = s
            rec = T4.recompute_dates(summaries, dates_params(spec), today=date.fromisoformat(a.today))
            if a.tasl7_nodes is not None and not a.tasl7_audits:
                raise Stop("STOP: --tasl7-nodes needs --tasl7-audits")
            if a.tasl7_audits:
                explicit = a.tasl7_nodes is not None
                nodes = list(a.tasl7_nodes) if explicit else default_tasl7_nodes(spec, G._read_main, list_main)
                rec["tasl7_audits"] = tasl7_dates(rec, spec, nodes, read_main=G._read_main, list_main=list_main,
                                                  source="explicit (--tasl7-nodes)" if explicit else
                                                  "default: the G5-7 nodes with a cross-host PASS on origin/main")
            print(json.dumps(rec, indent=1, default=str))
        elif a.cmd == "pilot-basis":
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            print(json.dumps(pilot_basis_check(spec, G._read_main), indent=1))
        else:
            out = launch(Path(a.spec), Path(a.note), a.node, job=a.job, enable=a.enable, today=date.today(),
                         server_record=Path(a.server_record) if a.server_record else None, host=a.host,
                         chunk=a.chunk)
            print(json.dumps({"ok": True, "node": a.node, "job": a.job}, indent=1, default=str))
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
