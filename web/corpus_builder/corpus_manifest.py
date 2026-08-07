#!/usr/bin/env python3
"""Canonical corpus manifest: build, validate, and diff.

The manifest is the enumeration of record for one immutable corpus bundle. It
names every canonical JSONL that will actually be ingested and published, with
a SHA-256 and record count per file, so that publication can verify the bytes it
is about to publish rather than trusting a directory listing.

Design notes worth keeping
--------------------------
* **No wall clock.** `bundle` is a pure function of its inputs, so two builds
  from identical inputs are byte-identical (criterion A2). Event time belongs in
  build reports, which record *when* an artifact was produced; a manifest
  records *what* it is. A `generated_at` field here would make every rebuild a
  different file and make `content_hash` useless as an identity.
* **`content_hash` covers `bundle` only.** Rebuilding the same content at a new
  git revision keeps the same content hash — which is what lets a web DB, an
  offline pack, and a desktop view built weeks apart all name one input hash
  (criterion A6).
* **Paths are relative and POSIX.** A manifest built on Windows must validate on
  a Linux CI runner byte-for-byte.
* **No new parsers.** Slugs come from `app.services.slug`, source titles from
  `ingest.parse_html`, bibliographic fields from the existing `.meta.json`
  sidecars. This module adds a contract, not a second catalogue.

Usage
-----
    python corpus_builder/corpus_manifest.py build \\
        --corpus-path /path/to/corpus --bundle-version 2026.08 \\
        --out corpus_builder/manifest/corpus-manifest.json

    python corpus_builder/corpus_manifest.py validate \\
        corpus_builder/manifest/corpus-manifest.json

    python corpus_builder/corpus_manifest.py diff old.json new.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_THIS_DIR = Path(__file__).resolve().parent
_WEB_DIR = _THIS_DIR.parent
if str(_WEB_DIR) not in sys.path:
    sys.path.insert(0, str(_WEB_DIR))

from app.services.slug import make_unique_slug  # noqa: E402
from ingest.parse_html import get_source_title  # noqa: E402

SCHEMA_VERSION = 1
GENERATOR = "corpus_manifest/1"
SCHEMA_PATH = _THIS_DIR / "manifest" / "schema-v1.json"
DEFAULT_JSONL_DIR = _THIS_DIR / "jsonl"

# The views this platform is expected to generate from one bundle. Reports
# register their real output hashes against the manifest; the inventory here is
# the expectation, so a silently-missing generator is visible as a gap.
DEFAULT_GENERATED_ARTIFACTS: list[dict[str, Any]] = [
    {"name": "corpus.db", "kind": "web-db", "required": True},
    {"name": "base.db", "kind": "offline-pack", "required": True},
    {"name": "dict.db", "kind": "offline-pack", "required": True},
    {"name": "desktop-html", "kind": "desktop-view", "required": False},
]

_READ_CHUNK = 1 << 20


class ManifestError(Exception):
    """Raised when a manifest cannot be built, parsed, or verified."""


# ── hashing and canonical serialization ──────────────────────────────────────

def sha256_file(path: str | os.PathLike[str]) -> str:
    """SHA-256 of a file's raw bytes, streamed — never loads a whole JSONL."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_READ_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(payload: Any) -> str:
    """The one serialization used for hashing and for writing manifests.

    Sorted keys, two-space indent, no ASCII escaping, LF newline. Anything that
    hashes a manifest must go through this function or the hash is meaningless.
    """
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def content_hash(bundle: dict[str, Any]) -> str:
    body = canonical_json(bundle).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _rel_posix(path: Path, root: Path) -> str:
    return PurePosixPath(os.path.relpath(path, root).replace(os.sep, "/")).as_posix()


def _rel_under_root(path: Path, root: Path) -> str | None:
    """Relative POSIX path only when `path` stays under `root`.

    Schema paths forbid `..` traversal. Legacy desktop trees (e.g. Index/...)
    often sit outside the default `web/` corpus root; those optional blocks are
    omitted rather than written as schema-illegal `../…` paths.
    """
    rel = _rel_posix(path, root)
    if any(part == ".." for part in PurePosixPath(rel).parts):
        return None
    if rel.startswith("/"):
        return None
    return rel


def _git_revision(cwd: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd),
            capture_output=True,
            encoding="utf-8",
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    rev = (out.stdout or "").strip()
    return rev if out.returncode == 0 and rev else "unknown"


# ── JSONL inspection ─────────────────────────────────────────────────────────

@dataclass
class JsonlStats:
    record_count: int
    first_canonical_id: str | None
    last_canonical_id: str | None


def inspect_jsonl(path: Path) -> JsonlStats:
    """Count live records and capture the identity endpoints of a canonical file.

    Deleted (tombstoned) records are skipped, matching what `ingest` inserts, so
    the manifest count is the count that must land in the database.
    """
    count = 0
    first: str | None = None
    last: str | None = None
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ManifestError(f"{path}: line {lineno} is not valid JSON: {exc}") from exc
            if rec.get("deleted"):
                continue
            canonical_id = rec.get("id")
            if not canonical_id:
                raise ManifestError(f"{path}: line {lineno} has no canonical id")
            if first is None:
                first = str(canonical_id)
            last = str(canonical_id)
            count += 1
    if count == 0:
        raise ManifestError(f"{path}: contains no live records")
    return JsonlStats(record_count=count, first_canonical_id=first, last_canonical_id=last)


# ── build ────────────────────────────────────────────────────────────────────

@dataclass
class SourceInput:
    slug: str
    filename: str
    sort_order: int
    title: str
    jsonl_path: Path
    source_file: Path | None = None
    metadata_path: Path | None = None
    provenance: str = ""
    rights: str = ""


def enumerate_from_corpus(corpus_path: Path, jsonl_dir: Path) -> list[SourceInput]:
    """Enumerate sources from the legacy desktop tree.

    `Programdata/data.txt` still supplies publication order and the legacy
    filename each source is published under — that is the one thing it is good
    for. Everything else (identity, content, counts) comes from the canonical
    JSONL, which is the point of the manifest.
    """
    data_txt = corpus_path / "Programdata" / "data.txt"
    if not data_txt.exists():
        raise ManifestError(f"Source enumeration not found: {data_txt}")

    filenames = [ln.strip() for ln in data_txt.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not filenames:
        raise ManifestError(f"{data_txt} lists no sources")

    seen_slugs: set[str] = set()
    out: list[SourceInput] = []
    missing: list[str] = []

    for idx, filename in enumerate(filenames):
        html_path = corpus_path / "Data" / filename
        slug = make_unique_slug(filename, seen_slugs)
        seen_slugs.add(slug)
        jsonl_path = jsonl_dir / f"{slug}.jsonl"
        if not jsonl_path.exists():
            missing.append(f"{filename} (slug {slug!r}) → {jsonl_path}")
            continue

        title = get_source_title(str(html_path)) if html_path.exists() else ""
        meta_path = Path(str(html_path) + ".meta.json")
        provenance = ""
        rights = ""
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ManifestError(f"{meta_path}: invalid JSON: {exc}") from exc
            provenance = str(meta.get("provenance") or "")
            rights = str(meta.get("rights") or "")
            title = title or str(meta.get("title_ru") or meta.get("title_display") or "")
        else:
            meta_path = None  # type: ignore[assignment]

        out.append(
            SourceInput(
                slug=slug,
                filename=filename,
                sort_order=idx,
                title=title or slug,
                jsonl_path=jsonl_path,
                source_file=html_path if html_path.exists() else None,
                metadata_path=meta_path,
                provenance=provenance or f"derived from {filename}",
                rights=rights,
            )
        )

    if missing:
        raise ManifestError(
            "Missing canonical JSONL for enumerated sources:\n  " + "\n  ".join(missing)
        )
    return out


def enumerate_from_jsonl_dir(jsonl_dir: Path, *, quiet: bool = False) -> list[SourceInput]:
    """Fallback enumeration straight from a canonical JSONL directory.

    Used by fixtures and by any bundle that has no legacy desktop tree behind
    it. Order is the sorted slug order, which is deterministic by construction.

    The directory also holds pipeline intermediates — `<slug>.raw.jsonl`,
    `<slug>.aligned.jsonl` — which are inputs to the converter, not publishable
    sources. They are recognised by their multi-part suffix and excluded, and
    every exclusion is printed: a bundle that silently drops (or silently
    absorbs) a file is exactly the failure this manifest exists to prevent.
    """
    candidates = sorted(p for p in jsonl_dir.glob("*.jsonl") if p.is_file())
    paths = [p for p in candidates if "." not in p.stem]
    skipped = [p for p in candidates if "." in p.stem]
    if skipped and not quiet:
        print(f"  excluded {len(skipped)} pipeline intermediate(s) from the bundle:")
        for path in skipped:
            print(f"    {path.name}")
    if not paths:
        raise ManifestError(f"No canonical .jsonl files found under {jsonl_dir}")
    out: list[SourceInput] = []
    for idx, path in enumerate(paths):
        slug = path.stem
        meta_path = path.with_suffix(".meta.json")
        provenance = ""
        rights = ""
        title = ""
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            provenance = str(meta.get("provenance") or "")
            rights = str(meta.get("rights") or "")
            title = str(meta.get("title_ru") or meta.get("title_display") or "")
        else:
            meta_path = None  # type: ignore[assignment]
        out.append(
            SourceInput(
                slug=slug,
                filename=f"{slug}.html",
                sort_order=idx,
                title=title or slug,
                jsonl_path=path,
                metadata_path=meta_path,
                provenance=provenance or f"canonical JSONL {path.name}",
                rights=rights,
            )
        )
    return out


def build_manifest(
    sources: Sequence[SourceInput],
    *,
    bundle_version: str,
    corpus_root: Path,
    repo_root: Path,
    revision: str | None = None,
    generated_artifacts: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble a manifest document from already-enumerated sources."""
    if not sources:
        raise ManifestError("Cannot build a manifest with no sources")

    entries: list[dict[str, Any]] = []
    total_records = 0
    total_bytes = 0

    for src in sorted(sources, key=lambda s: (s.sort_order, s.slug)):
        stats = inspect_jsonl(src.jsonl_path)
        size = src.jsonl_path.stat().st_size
        total_records += stats.record_count
        total_bytes += size

        canonical: dict[str, Any] = {
            "path": _rel_posix(src.jsonl_path, corpus_root),
            "sha256": sha256_file(src.jsonl_path),
            "bytes": size,
            "record_count": stats.record_count,
        }
        if stats.first_canonical_id:
            canonical["first_canonical_id"] = stats.first_canonical_id
        if stats.last_canonical_id:
            canonical["last_canonical_id"] = stats.last_canonical_id

        entry: dict[str, Any] = {
            "slug": src.slug,
            "filename": src.filename,
            "sort_order": src.sort_order,
            "title": src.title,
            "provenance": src.provenance,
            "canonical": canonical,
        }
        if src.rights:
            entry["rights"] = src.rights
        if src.source_file is not None and src.source_file.exists():
            source_rel = _rel_under_root(src.source_file, corpus_root)
            if source_rel is not None:
                entry["source_file"] = {
                    "path": source_rel,
                    "sha256": sha256_file(src.source_file),
                    "bytes": src.source_file.stat().st_size,
                }
        if src.metadata_path is not None and src.metadata_path.exists():
            meta_rel = _rel_under_root(src.metadata_path, corpus_root)
            if meta_rel is not None:
                entry["metadata"] = {
                    "path": meta_rel,
                    "sha256": sha256_file(src.metadata_path),
                    "bytes": src.metadata_path.stat().st_size,
                }
        entries.append(entry)

    bundle = {
        "bundle_version": bundle_version,
        "corpus_root": _rel_posix(corpus_root, repo_root),
        "sources": entries,
        "generated_artifacts": [
            dict(a) for a in (generated_artifacts if generated_artifacts is not None
                              else DEFAULT_GENERATED_ARTIFACTS)
        ],
        "totals": {
            "source_count": len(entries),
            "record_count": total_records,
            "canonical_bytes": total_bytes,
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "bundle": bundle,
        "build": {
            "generator": GENERATOR,
            "revision": revision or _git_revision(repo_root),
        },
        "content_hash": content_hash(bundle),
    }


def write_manifest(manifest: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Explicit newline='' keeps LF on Windows, so a manifest built here is
    # byte-identical to one built on a Linux runner.
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(canonical_json(manifest))


def load_manifest(path: str | os.PathLike[str]) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"Manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"{path}: invalid JSON: {exc}") from exc


# ── validation ───────────────────────────────────────────────────────────────

@dataclass
class ManifestReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def print_summary(self) -> None:
        print("── Manifest report ────────────────────────────────────────")
        for key, value in self.stats.items():
            print(f"  {key}: {value}")
        for warning in self.warnings:
            print(f"  WARNING: {warning}")
        for error in self.errors:
            print(f"  ERROR:   {error}")
        print("  Result:", "OK" if self.ok else "FAILED")
        print("───────────────────────────────────────────────────────────")


def _schema_errors(manifest: dict[str, Any]) -> list[str]:
    """Validate against schema-v1.json.

    `jsonschema` is a hard dependency precisely so the schema file is
    load-bearing. A hand-written twin validator would drift from the published
    schema, and the drift would be invisible until a consumer trusted the wrong
    one.
    """
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    out = []
    for err in sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path)):
        location = "/".join(str(p) for p in err.absolute_path) or "<root>"
        out.append(f"schema: {location}: {err.message}")
    return out


def validate_manifest(
    manifest: dict[str, Any],
    *,
    repo_root: Path | None = None,
    check_files: bool = True,
) -> ManifestReport:
    """Structural, semantic, and (optionally) on-disk validation.

    With `check_files`, every canonical JSONL named by the manifest is opened
    and hashed. That is the check that makes a one-byte mutation fail *before*
    ingest rather than after publication.
    """
    report = ManifestReport()

    schema_errors = _schema_errors(manifest)
    report.errors.extend(schema_errors)
    if schema_errors:
        # Semantic checks below index into a shape the schema just rejected.
        return report

    bundle = manifest["bundle"]
    sources = bundle["sources"]

    expected_hash = content_hash(bundle)
    if manifest["content_hash"] != expected_hash:
        report.errors.append(
            f"content_hash mismatch: recorded {manifest['content_hash']}, recomputed {expected_hash}"
        )

    slugs = [s["slug"] for s in sources]
    duplicate_slugs = sorted({s for s in slugs if slugs.count(s) > 1})
    for slug in duplicate_slugs:
        report.errors.append(f"duplicate slug in bundle: {slug!r}")

    paths = [s["canonical"]["path"] for s in sources]
    duplicate_paths = sorted({p for p in paths if paths.count(p) > 1})
    for path in duplicate_paths:
        report.errors.append(f"two sources claim the same canonical path: {path!r}")

    ordered = sorted(sources, key=lambda s: (s["sort_order"], s["slug"]))
    if [s["slug"] for s in ordered] != slugs:
        report.errors.append(
            "sources are not in deterministic (sort_order, slug) order — the manifest is not reproducible"
        )

    totals = bundle["totals"]
    if totals["source_count"] != len(sources):
        report.errors.append(
            f"totals.source_count is {totals['source_count']}, bundle lists {len(sources)} sources"
        )
    record_sum = sum(s["canonical"]["record_count"] for s in sources)
    if totals["record_count"] != record_sum:
        report.errors.append(
            f"totals.record_count is {totals['record_count']}, source counts sum to {record_sum}"
        )
    byte_sum = sum(s["canonical"]["bytes"] for s in sources)
    if totals["canonical_bytes"] != byte_sum:
        report.errors.append(
            f"totals.canonical_bytes is {totals['canonical_bytes']}, source sizes sum to {byte_sum}"
        )

    report.stats["bundle_version"] = bundle["bundle_version"]
    report.stats["content_hash"] = manifest["content_hash"]
    report.stats["sources"] = len(sources)
    report.stats["records"] = record_sum

    if not check_files:
        report.stats["files_verified"] = 0
        return report

    root = (repo_root or Path.cwd()) / bundle["corpus_root"]
    verified = 0
    for src in sources:
        canonical = src["canonical"]
        path = root / canonical["path"]
        if not path.exists():
            report.errors.append(f"{src['slug']}: canonical file missing: {path}")
            continue
        actual_size = path.stat().st_size
        if actual_size != canonical["bytes"]:
            report.errors.append(
                f"{src['slug']}: size mismatch for {canonical['path']}: "
                f"manifest {canonical['bytes']}, on disk {actual_size}"
            )
        actual_hash = sha256_file(path)
        if actual_hash != canonical["sha256"]:
            report.errors.append(
                f"{src['slug']}: sha256 mismatch for {canonical['path']}: "
                f"manifest {canonical['sha256']}, on disk {actual_hash}"
            )
            continue
        verified += 1

    report.stats["files_verified"] = verified
    return report


def resolve_source_path(manifest: dict[str, Any], src: dict[str, Any], repo_root: Path) -> Path:
    """Absolute path of one source's canonical JSONL, per the manifest."""
    return repo_root / manifest["bundle"]["corpus_root"] / src["canonical"]["path"]


# ── diff ─────────────────────────────────────────────────────────────────────

def diff_manifests(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Structured difference between two manifests, keyed by slug."""
    old_by_slug = {s["slug"]: s for s in old["bundle"]["sources"]}
    new_by_slug = {s["slug"]: s for s in new["bundle"]["sources"]}

    added = sorted(set(new_by_slug) - set(old_by_slug))
    removed = sorted(set(old_by_slug) - set(new_by_slug))
    changed = []
    for slug in sorted(set(old_by_slug) & set(new_by_slug)):
        before, after = old_by_slug[slug], new_by_slug[slug]
        fields = []
        if before["canonical"]["sha256"] != after["canonical"]["sha256"]:
            fields.append("content")
        if before["canonical"]["record_count"] != after["canonical"]["record_count"]:
            fields.append("record_count")
        if before["sort_order"] != after["sort_order"]:
            fields.append("sort_order")
        if before.get("title") != after.get("title"):
            fields.append("title")
        if before.get("provenance") != after.get("provenance"):
            fields.append("provenance")
        if before.get("rights") != after.get("rights"):
            fields.append("rights")
        if fields:
            changed.append({
                "slug": slug,
                "fields": fields,
                "record_count_before": before["canonical"]["record_count"],
                "record_count_after": after["canonical"]["record_count"],
            })

    return {
        "content_hash_before": old["content_hash"],
        "content_hash_after": new["content_hash"],
        "identical": old["content_hash"] == new["content_hash"],
        "bundle_version_before": old["bundle"]["bundle_version"],
        "bundle_version_after": new["bundle"]["bundle_version"],
        "added": added,
        "removed": removed,
        "changed": changed,
        "record_count_before": old["bundle"]["totals"]["record_count"],
        "record_count_after": new["bundle"]["totals"]["record_count"],
    }


def format_diff(diff: dict[str, Any]) -> str:
    if diff["identical"]:
        return f"Manifests are identical ({diff['content_hash_after']})."
    lines = [
        f"  before: {diff['content_hash_before']} ({diff['bundle_version_before']})",
        f"  after:  {diff['content_hash_after']} ({diff['bundle_version_after']})",
        f"  records: {diff['record_count_before']} → {diff['record_count_after']}",
    ]
    for slug in diff["added"]:
        lines.append(f"  + {slug}")
    for slug in diff["removed"]:
        lines.append(f"  - {slug}")
    for entry in diff["changed"]:
        lines.append(
            f"  ~ {entry['slug']}: {', '.join(entry['fields'])}"
            f" ({entry['record_count_before']} → {entry['record_count_after']} records)"
        )
    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────────

def _cmd_build(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    corpus_root = Path(args.corpus_root).resolve()
    jsonl_dir = Path(args.jsonl_dir).resolve()

    if args.corpus_path:
        sources = enumerate_from_corpus(Path(args.corpus_path).resolve(), jsonl_dir)
    else:
        sources = enumerate_from_jsonl_dir(jsonl_dir)

    manifest = build_manifest(
        sources,
        bundle_version=args.bundle_version,
        corpus_root=corpus_root,
        repo_root=repo_root,
        revision=args.build_revision,
    )
    write_manifest(manifest, Path(args.out))
    print(f"Wrote {args.out}")
    print(f"  bundle_version: {manifest['bundle']['bundle_version']}")
    print(f"  content_hash:   {manifest['content_hash']}")
    print(f"  sources:        {manifest['bundle']['totals']['source_count']}")
    print(f"  records:        {manifest['bundle']['totals']['record_count']}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    report = validate_manifest(
        manifest,
        repo_root=Path(args.repo_root).resolve(),
        check_files=not args.no_files,
    )
    report.print_summary()
    return 0 if report.ok else 1


def _cmd_diff(args: argparse.Namespace) -> int:
    diff = diff_manifests(load_manifest(args.old), load_manifest(args.new))
    if args.json:
        print(json.dumps(diff, ensure_ascii=False, indent=2))
    else:
        print(format_diff(diff))
    return 0 if diff["identical"] or not args.fail_on_change else 2


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build, validate, and diff corpus manifests")
    parser.add_argument("--repo-root", default=str(_WEB_DIR.parent),
                        help="Repository root every corpus_root is relative to")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build a manifest from canonical JSONL")
    build.add_argument("--corpus-path", help="Legacy corpus tree (Data/ + Programdata/) for order and filenames")
    build.add_argument("--jsonl-dir", default=str(DEFAULT_JSONL_DIR))
    build.add_argument("--corpus-root", default=str(_WEB_DIR),
                       help="Directory manifest paths are relative to (default: web/)")
    build.add_argument("--bundle-version", required=True)
    build.add_argument("--build-revision", default=None,
                       help="Override the recorded revision (default: git rev-parse HEAD)")
    build.add_argument("--out", required=True)
    build.set_defaults(func=_cmd_build)

    validate = sub.add_parser("validate", help="Validate a manifest and the files it names")
    validate.add_argument("manifest")
    validate.add_argument("--no-files", action="store_true",
                          help="Structural checks only; do not open or hash canonical files")
    validate.set_defaults(func=_cmd_validate)

    diff = sub.add_parser("diff", help="Diff two manifests")
    diff.add_argument("old")
    diff.add_argument("new")
    diff.add_argument("--json", action="store_true")
    diff.add_argument("--fail-on-change", action="store_true",
                      help="Exit 2 when the manifests differ")
    diff.set_defaults(func=_cmd_diff)

    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return args.func(args)
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
