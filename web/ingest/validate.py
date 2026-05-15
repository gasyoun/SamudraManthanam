"""Corpus validation: checks the source tree before ingestion begins."""
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


@dataclass
class ValidationReport:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, int] = field(default_factory=dict)

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
