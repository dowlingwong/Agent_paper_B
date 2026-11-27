# Amendment to the sweep-2 C3 analysis preregistration: PRE-SPLIT cites split v2

approved: false

This amendment implements PLAN §10 **R1-G5-S9 (1)** (author, 27 Nov 2026). It records the
PRE-SPLIT citation in a companion to `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`
(SHA-256 `aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5`). The signed,
frozen preregistration retains its original bytes.

## A§1. PRE-SPLIT citation

PRE-SPLIT option A cites `r1/c3/splits/c3_p3_split_v2.json` (SHA-256
`4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a`). The file uses the v1 assignment
rules and salts (`c3_p3_split/v1` and `c3_t1_split/v1`). Its T0 block and the entries for the eight
original T1 nodes are byte-identical to v1. The added T1 entries are `mlgym_titanic`,
`mlgym_metamaze`, `gc7rc_etth1` and `gc7rc_forestcover`.

## A§4. Publication

The coordinator publishes this text at
`docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md`. At publication the
coordinator sets the status line and final block's `approved` to `true`, sets `frozen` to `true`,
and fills `signed_by` and `signed_utc` from the authorization record. The release check verifies
the committed amendment and its author row against published `main`.

## A§5. Final block

```
amends: docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md sha256 aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5
plan_row: R1-G5-S9
pre_split: A
split_file: r1/c3/splits/c3_p3_split_v2.json sha256 4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a
supersedes_split_file: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569
approved: false
frozen: false
signed_by: <pending: at publication>
signed_utc: <pending: YYYY-MM-DDTHH:MM:SSZ at publication>
```
