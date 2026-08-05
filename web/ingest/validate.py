"""Corpus validation: checks the inputs before ingestion begins.

Two validators live here, and the difference between them is the point of
Lane A:

* `validate_bundle` opens and hashes **the canonical JSONL that publication
  will actually read**, as named by a manifest. This is the real gate.
* `validate_corpus` checks the legacy desktop HTML tree. That tree is a
  compatibility view — the app has published JSONL since the canonical
  converter landed — so validating it alone means validating something other
  than what ships. It is kept for the desktop product and for bundles that have
  no manifest yet, never as a substitute for the bundle check.
"""
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_WEB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WEB_DIR not in sys.path:
    sys.path.insert(0, _WEB_DIR)


@dataclass
class ValidationReport:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    # Values are usually counts, but bundle validation also records identity
    # strings (content hash, bundle version) that belong in the same summary.
    stats: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def print_summary(self) -> None:
        print("── Validation report ──────────────────────────────────────")
        for k, v in self.stats.items():
            print(f"  {k}: {v}")
        for w in self.warnings:
            print(f"  WARNING: {w}")
        for e in self.errors:
            print(f"  ERROR:   {e}")
        print("  Result:", "OK" if self.ok else "FAILED")
        print("───────────────────────────────────────────────────────────")


def _read_title_comment(file_path: str) -> str:
    """Return the first line of the file stripped of the <!-- --> wrapper, or ''."""
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            first = fh.readline().strip()
        if first.startswith("<!--") and first.endswith("-->"):
            return first[4:-3].strip()
        return ""
    except OSError:
        return ""


def validate_corpus(corpus_path: str) -> ValidationReport:
    """Validate the corpus directory tree.

    Checks performed
    ----------------
    1. Manifest (Programdata/data.txt) exists and is non-empty.
    2. No duplicate filenames in the manifest.
    3. Every listed file exists under Data/.
    4. Every listed file has a non-empty title comment on its first line.
    """
    report = ValidationReport()

    manifest_path = os.path.join(corpus_path, "Programdata", "data.txt")
    if not os.path.exists(manifest_path):
        report.errors.append(f"Manifest not found: {manifest_path}")
        return report

    with open(manifest_path, "r", encoding="utf-8") as fh:
        raw_lines = [ln.strip() for ln in fh if ln.strip()]

    if not raw_lines:
        report.errors.append("Manifest is empty (Programdata/data.txt has no entries).")
        return report

    report.stats["manifest_entries"] = len(raw_lines)

    # Duplicate check
    seen: set[str] = set()
    for fname in raw_lines:
        if fname in seen:
            report.errors.append(f"Duplicate manifest entry: {fname}")
        seen.add(fname)

    # File presence + title comment
    missing = 0
    no_title = 0
    for fname in raw_lines:
        file_path = os.path.join(corpus_path, "Data", fname)
        if not os.path.exists(file_path):
            report.errors.append(f"Missing file: Data/{fname}")
            missing += 1
            continue
        title = _read_title_comment(file_path)
        if not title:
            report.warnings.append(f"No title comment in: Data/{fname}")
            no_title += 1

    report.stats["missing_files"] = missing
    report.stats["no_title_comment"] = no_title

    return report


def validate_bundle(manifest_path: str, repo_root: str | None = None) -> ValidationReport:
    """Validate a corpus bundle against its manifest.

    Every canonical JSONL the manifest names is opened and hashed, so a single
    mutated byte in a file that is about to be published fails here — before
    ingest, not after a swap. Returns the same `ValidationReport` shape as
    `validate_corpus` so `publish` can treat both uniformly.
    """
    from corpus_builder.corpus_manifest import (
        ManifestError,
        load_manifest,
        validate_manifest,
    )

    report = ValidationReport()
    root = Path(repo_root) if repo_root else Path(_WEB_DIR).parent

    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        report.errors.append(str(exc))
        return report

    try:
        manifest_report = validate_manifest(manifest, repo_root=root, check_files=True)
    except ManifestError as exc:
        report.errors.append(str(exc))
        return report

    report.errors.extend(manifest_report.errors)
    report.warnings.extend(manifest_report.warnings)
    report.stats.update(manifest_report.stats)
    return report


def bundle_summary(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Small, log-friendly identity block for a manifest."""
    bundle = manifest["bundle"]
    return {
        "content_hash": manifest["content_hash"],
        "bundle_version": bundle["bundle_version"],
        "sources": bundle["totals"]["source_count"],
        "records": bundle["totals"]["record_count"],
    }
