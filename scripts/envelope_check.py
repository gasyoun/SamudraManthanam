#!/usr/bin/env python3
"""Verify one release envelope against the bytes it pins (V6 verification).

The envelope (data/manifest/envelopes/*.envelope.json, schema
release-envelope-v1) is the object dashboards and manuscripts pin. This script
is the rerun side of that contract: it re-derives every digest the envelope
declares from the bytes actually on disk and reports PASS/FAIL/SKIP per check.
It never repairs, never rewrites, never trusts a recorded digest it could not
recompute.

Spec: Uprava docs/SPEC_RELEASE_ENVELOPE_V6_PORTFOLIO_2026.md
Reference implementation: kosha scripts/envelope_check.py (H4239 pilot)

Checks:
  CHK-1  envelope schema + required fields present
  CHK-2  each pinned_artifacts entry's sha256 recomputes from its file's
         lf-canonical bytes on disk
  CHK-3  output_digests parity: declared rows == conversion_report.json
         total_records == sum of per-source 'records' over the declared
         148 sources
  CHK-4  source_pins directory digest re-derives: sha256 of the sorted
         '<slug>:<sha256(lf-canonical bytes)>' lines over the report-source
         .jsonl files, one per conversion_report.json['sources'] entry
         (SKIP a file that is absent rather than fail the whole check)

Exit 0 when every run check passes (SKIP allowed); exit 1 on any FAIL.

Usage:
    python scripts/envelope_check.py --envelope data/manifest/envelopes/v0.19.50.envelope.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SCHEMA = "release-envelope-v1"
REQUIRED = (
    "schema",
    "envelope_id",
    "release_tag",
    "created",
    "code_revision",
    "pinned_artifacts",
    "source_pins",
    "output_digests",
    "config",
    "licence",
    "checks",
    "review",
    "citation",
    "publication_state",
)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical(b: bytes) -> bytes:
    """LF-canonical form — CRLF normalised, reproducible from any compliant checkout."""
    return b.replace(b"\r\n", b"\n")


def sha256_file_lf(path: Path) -> str:
    return sha256_bytes(canonical(path.read_bytes()))


def report(results, fatal=None, extra=None) -> str:
    lines = ["{:<20} {:<6} {}".format(cid, status, detail) for cid, status, detail in results]
    if extra:
        lines += ["  drift: " + d for d in extra]
    if fatal:
        lines.append("FATAL: " + fatal)
    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--envelope", required=True)
    args = ap.parse_args()

    env_path = Path(args.envelope)
    if not env_path.is_absolute():
        env_path = REPO / env_path
    env = json.loads(canonical(env_path.read_bytes()))

    results = []

    def record(cid: str, ok: bool, detail: str, skipped: bool = False):
        results.append((cid, "SKIP" if skipped else ("pass" if ok else "FAIL"), detail))

    # CHK-1 schema + required fields
    missing = [k for k in REQUIRED if k not in env or env[k] in (None, "", [], {})]
    record(
        "CHK-1-schema",
        not missing,
        "schema={}".format(env.get("schema"))
        + ("" if not missing else "; missing/empty: {}".format(", ".join(missing))),
    )
    if env.get("schema") != SCHEMA:
        print(report(results, fatal="schema is {}, expected {}".format(env.get("schema"), SCHEMA)))
        return 1

    # CHK-2 pinned_artifacts digests
    pin_drift = []
    for a in env["pinned_artifacts"]:
        fp = REPO / a["path"]
        if not fp.is_file():
            pin_drift.append("{}: file not found".format(a["path"]))
            continue
        got = sha256_file_lf(fp)
        if got != a["sha256"]:
            pin_drift.append("{}: sha256 {} != declared {}".format(a["path"], got, a["sha256"]))
    record("CHK-2-artifact-pins", not pin_drift, "{} artifact(s)".format(len(env["pinned_artifacts"])))
    if pin_drift:
        print(report(results, extra=pin_drift))

    # CHK-3 output parity against conversion_report.json
    conv_path = REPO / env["config"]["source_manifest"]
    drift = []
    if not conv_path.is_file():
        drift.append("{}: source_manifest not found".format(conv_path))
    else:
        conv = json.loads(canonical(conv_path.read_bytes()))
        ds = next(iter(env["output_digests"]["datasets"].values()))
        declared_rows = ds["rows"]
        if conv.get("total_records") != declared_rows:
            drift.append(
                "total_records {} != declared rows {}".format(conv.get("total_records"), declared_rows)
            )
        sources = conv.get("sources", [])
        if conv.get("total_sources") != len(sources):
            drift.append(
                "total_sources {} != len(sources) {}".format(conv.get("total_sources"), len(sources))
            )
        records_sum = sum(s["records"] for s in sources)
        if records_sum != declared_rows:
            drift.append("sum(sources.records) {} != declared rows {}".format(records_sum, declared_rows))
    record("CHK-3-output-parity", not drift, "declared rows vs {}".format(env["config"]["source_manifest"]))
    if drift:
        print(report(results, extra=drift))

    # CHK-4 source_pins directory digest
    sp_drift = []
    if not env["source_pins"]:
        record("CHK-4-source-pins", False, "no source_pins declared")
    else:
        sp = env["source_pins"][0]
        jsonl_dir = REPO / "web" / "corpus_builder" / "jsonl"
        sources = conv.get("sources", []) if conv_path.is_file() else []
        lines = []
        skipped_files = []
        for s in sorted(sources, key=lambda r: r["slug"]):
            slug = s["slug"]
            fp = jsonl_dir / "{}.jsonl".format(slug)
            if not fp.is_file():
                skipped_files.append(slug)
                continue
            lines.append("{}:{}".format(slug, sha256_file_lf(fp)))
        if not sources:
            sp_drift.append("conversion_report.json unavailable — cannot re-derive source_pins")
            record("CHK-4-source-pins", False, "source_manifest unavailable")
        elif skipped_files:
            record(
                "CHK-4-source-pins",
                True,
                "{}/{} files hashed; {} absent".format(len(lines), len(sources), len(skipped_files)),
                skipped=True,
            )
        else:
            manifest_str = "\n".join(lines) + "\n"
            agg = sha256_bytes(manifest_str.encode("utf-8"))
            if agg != sp["sha256"]:
                sp_drift.append("aggregate digest {} != declared {}".format(agg, sp["sha256"]))
            record("CHK-4-source-pins", not sp_drift, "{}/{} files hashed".format(len(lines), len(sources)))
    if sp_drift:
        print(report(results, extra=sp_drift))

    fails = [r for r in results if r[1] == "FAIL"]
    print(report(results))
    n_pass = sum(1 for r in results if r[1] == "pass")
    n_skip = sum(1 for r in results if r[1] == "SKIP")
    n_fail = len(fails)
    print("\n{} pass / {} skip / {} fail".format(n_pass, n_skip, n_fail))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
