#!/usr/bin/env python3
"""Build reports: what a generator produced, from which input manifest.

Every generated view — the web `corpus.db`, the offline packs, the desktop HTML
and catalogue outputs — is a *derivative* of one corpus bundle. A build report
is the record that ties one such derivative back to the exact bundle it came
from, so that "which corpus is this pack built from?" has an answer that is not
a guess about timestamps.

The report carries the event time the manifest deliberately does not: a manifest
is identity, a report is history.

Shape
-----
    {
      "report_version": 1,
      "artifact": {"name": "base.db", "kind": "offline-pack"},
      "input_manifest": {
        "content_hash": "sha256:…",
        "bundle_version": "2026.08",
        "source_count": 96,
        "record_count": 574939
      },
      "outputs": [{"name": "base.db", "sha256": "…", "bytes": 1234, "record_count": 1000}],
      "counts": {"sources": 96, "rows": 574939},
      "generator": "build_offline_pack/1",
      "generated_at": "2026-08-04T18:30:00+00:00"
    }

`input_manifest.content_hash` is the join key across every report. Criterion A6
is exactly the assertion that the web DB, the offline packs, and the desktop
outputs all carry the same value there.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPORT_VERSION = 1
_READ_CHUNK = 1 << 20

VALID_KINDS = {"web-db", "offline-pack", "desktop-view", "export"}


class BuildReportError(Exception):
    """Raised when a build report cannot be written or read back consistently."""


def _sha256_file(path: str | os.PathLike[str]) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_READ_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_reference(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the joinable identity of an input manifest."""
    try:
        bundle = manifest["bundle"]
        return {
            "content_hash": manifest["content_hash"],
            "bundle_version": bundle["bundle_version"],
            "source_count": bundle["totals"]["source_count"],
            "record_count": bundle["totals"]["record_count"],
        }
    except KeyError as exc:
        raise BuildReportError(f"Manifest is missing {exc} — cannot reference it in a report") from exc


def manifest_reference_from_meta(meta: Mapping[str, Any]) -> dict[str, Any]:
    """Build a manifest reference from a published DB's `corpus_meta` rows.

    A downstream generator (offline pack, desktop view) reads its input from
    `corpus.db`, not from the manifest file. It still has to name the same input
    manifest, so it inherits the identity the ingest recorded rather than
    re-deriving one — which is what keeps A6 true across generators that never
    see the manifest.
    """
    content = str(meta.get("input_manifest_hash") or "")
    if not content:
        raise BuildReportError(
            "Source database carries no input_manifest_hash — it was built without a "
            "manifest, so no derivative of it can be registered against one."
        )
    reference: dict[str, Any] = {
        "content_hash": content,
        "bundle_version": str(meta.get("bundle_version") or meta.get("corpus_version") or ""),
    }
    if meta.get("source_count") is not None:
        reference["source_count"] = int(meta["source_count"])
    if meta.get("record_count") is not None:
        reference["record_count"] = int(meta["record_count"])
    return reference


def output_entry(
    path: str | os.PathLike[str],
    *,
    name: str | None = None,
    record_count: int | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe one produced file by its real, on-disk bytes."""
    p = Path(path)
    if not p.exists():
        raise BuildReportError(f"Declared output does not exist: {p}")
    entry: dict[str, Any] = {
        "name": name or p.name,
        "sha256": _sha256_file(p),
        "bytes": p.stat().st_size,
    }
    if record_count is not None:
        entry["record_count"] = record_count
    if extra:
        entry.update(dict(extra))
    return entry


def build_report(
    *,
    artifact_name: str,
    artifact_kind: str,
    manifest: Mapping[str, Any] | None = None,
    manifest_ref: Mapping[str, Any] | None = None,
    outputs: Iterable[Mapping[str, Any]],
    counts: Mapping[str, Any] | None = None,
    generator: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if artifact_kind not in VALID_KINDS:
        raise BuildReportError(
            f"Unknown artifact kind {artifact_kind!r} (expected one of {sorted(VALID_KINDS)})"
        )
    if (manifest is None) == (manifest_ref is None):
        raise BuildReportError("Pass exactly one of manifest= or manifest_ref=")
    reference = dict(manifest_ref) if manifest_ref is not None else manifest_reference(manifest)
    stamp = generated_at or datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "report_version": REPORT_VERSION,
        "artifact": {"name": artifact_name, "kind": artifact_kind},
        "input_manifest": reference,
        "outputs": [dict(o) for o in outputs],
        "counts": dict(counts or {}),
        "generator": generator,
        "generated_at": stamp,
    }


def write_report(report: Mapping[str, Any], out_path: str | os.PathLike[str]) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    return path


def load_report(path: str | os.PathLike[str]) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildReportError(f"Build report not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildReportError(f"{path}: invalid JSON: {exc}") from exc


def validate_report(report: Mapping[str, Any]) -> list[str]:
    """Return a list of problems; empty means the report is well-formed."""
    errors: list[str] = []
    if report.get("report_version") != REPORT_VERSION:
        errors.append(f"report_version is {report.get('report_version')!r}, expected {REPORT_VERSION}")
    artifact = report.get("artifact") or {}
    if not artifact.get("name"):
        errors.append("artifact.name is missing")
    if artifact.get("kind") not in VALID_KINDS:
        errors.append(f"artifact.kind is {artifact.get('kind')!r}, expected one of {sorted(VALID_KINDS)}")
    manifest_ref = report.get("input_manifest") or {}
    content = str(manifest_ref.get("content_hash") or "")
    if not content.startswith("sha256:") or len(content) != len("sha256:") + 64:
        errors.append(f"input_manifest.content_hash is not a sha256 reference: {content!r}")
    if not manifest_ref.get("bundle_version"):
        errors.append("input_manifest.bundle_version is missing")
    outputs = report.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        errors.append("outputs is empty — a report must name what it produced")
    else:
        for idx, entry in enumerate(outputs):
            digest = str(entry.get("sha256") or "")
            if len(digest) != 64:
                errors.append(f"outputs[{idx}].sha256 is not a bare sha256 hex digest")
            if not entry.get("name"):
                errors.append(f"outputs[{idx}].name is missing")
    if not report.get("generator"):
        errors.append("generator is missing")
    if not report.get("generated_at"):
        errors.append("generated_at is missing")
    return errors


def agree_on_input(reports: Iterable[Mapping[str, Any]]) -> tuple[bool, set[str]]:
    """Do these reports all name the same input manifest? (Criterion A6.)

    Returns `(agree, hashes)`; `hashes` is every distinct content hash seen, so
    a caller can name the offenders rather than just failing.
    """
    hashes = {str((r.get("input_manifest") or {}).get("content_hash")) for r in reports}
    return len(hashes) == 1, hashes


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect corpus build reports")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("validate", help="Validate one or more build reports")
    check.add_argument("reports", nargs="+")

    agree = sub.add_parser("agree", help="Assert several reports name one input manifest")
    agree.add_argument("reports", nargs="+")

    args = parser.parse_args()
    loaded = [load_report(p) for p in args.reports]

    if args.command == "validate":
        failed = False
        for path, report in zip(args.reports, loaded):
            errors = validate_report(report)
            if errors:
                failed = True
                print(f"{path}: FAILED")
                for err in errors:
                    print(f"  ERROR: {err}")
            else:
                print(f"{path}: OK ({report['input_manifest']['content_hash']})")
        return 1 if failed else 0

    ok, hashes = agree_on_input(loaded)
    if ok:
        print(f"All {len(loaded)} reports name {hashes.pop()}")
        return 0
    print("Reports disagree on their input manifest:", file=sys.stderr)
    for path, report in zip(args.reports, loaded):
        print(f"  {path}: {(report.get('input_manifest') or {}).get('content_hash')}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
