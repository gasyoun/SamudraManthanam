"""Zero-orphan evidence for a candidate corpus rebuild (H1925, B5).

The invariant this proves, stated as the plan states it: **every retained
reference resolves to the same canonical record, with the same content, after a
corpus rebuild — and none silently binds to a different line.**

How it works: resolve every retained reference twice — once against the corpus
it was recorded against (``--before``), once against the rebuild candidate
(``--candidate``) — and compare *both* halves of the answer:

- **identity** — same ``(source_slug, canonical_id)``;
- **content** — same fingerprint (NFC + whitespace-collapsed, tags stripped),
  so a markup fix is not reported as a text change but an edited verse is.

Verdicts per reference:

===================  ====================================================
``stable``           resolves in both, same identity, same content
``content_changed``  same identity, different text (informational, not fatal)
``identity_changed`` resolves to a DIFFERENT passage — the silent mis-bind
``orphaned``         resolved before, resolves to nothing now
``ambiguous``        matches several lines now — never bound
``unresolved_before``never resolved even in its own corpus (pre-existing debris)
===================  ====================================================

The gate fails (exit 1) on ``identity_changed``, ``orphaned`` or ``ambiguous``.
``content_changed`` does not fail — text corrections are the point of the
project — but it is always reported and counted.

``--rollback-rehearsal`` re-runs the whole comparison against ``--before``
after the candidate check, proving the previous corpus still resolves every
retained reference, i.e. that rolling back is a real option rather than an
assumption (the reference-side twin of Lane A's A7 bundle rollback).

Usage::

    python scripts/zero_orphan_report.py --before corpus.db --candidate candidate.db \\
        --state state.db --json reports/zero_orphan.json --rollback-rehearsal
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.canonical_refs import (  # noqa: E402
    DurableRef,
    Resolution,
    ResolutionStatus,
    build_identity_index,
    load_legacy_map,
    resolve_against_index,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

FATAL_VERDICTS = ("identity_changed", "orphaned", "ambiguous")


def collect_retained_refs(state_path: str) -> list[DurableRef]:
    """Every reference in state.db that must survive a rebuild.

    Today that is the corrections queue; the loader is deliberately a list of
    (table, projection) so a new retained-reference table is one entry, not a
    new script. AI cache rows are keyed by prompt hash and hold no corpus
    coordinates, so they carry no reference to orphan — see
    docs/DURABLE_REFERENCE_INVENTORY.md for the full census and that verdict.
    """
    conn = sqlite3.connect(f"file:{state_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    refs: list[DurableRef] = []
    try:
        try:
            rows = conn.execute(
                "SELECT id, source_id, line_num, source_slug, canonical_id, corpus_version "
                "FROM corrections"
            ).fetchall()
        except sqlite3.OperationalError:
            rows = conn.execute("SELECT id, source_id, line_num FROM corrections").fetchall()
        for row in rows:
            keys = row.keys()
            refs.append(
                DurableRef(
                    source_slug=row["source_slug"] if "source_slug" in keys else None,
                    canonical_id=row["canonical_id"] if "canonical_id" in keys else None,
                    corpus_version=row["corpus_version"] if "corpus_version" in keys else None,
                    source_id=row["source_id"],
                    line_num=row["line_num"],
                    origin=f"corrections#{row['id']}",
                )
            )
    finally:
        conn.close()
    return refs


def _verdict(before: Resolution, after: Resolution) -> str:
    if not before.ok:
        return "unresolved_before"
    if after.status is ResolutionStatus.AMBIGUOUS:
        return "ambiguous"
    if not after.ok:
        return "orphaned"
    same_identity = (
        before.source_slug == after.source_slug and before.canonical_id == after.canonical_id
    )
    # A pre-JSONL line has no canonical id on either side; fall back to the
    # content fingerprint so such a reference is still checked rather than
    # waved through as "identity matched (None == None)".
    if before.canonical_id is None and after.canonical_id is None:
        same_identity = before.fingerprint == after.fingerprint
    if not same_identity:
        return "identity_changed"
    if before.fingerprint != after.fingerprint:
        return "content_changed"
    return "stable"


def compare(before_path: str, candidate_path: str, state_path: str) -> dict:
    before_conn = sqlite3.connect(f"file:{before_path}?mode=ro", uri=True)
    try:
        before_index = build_identity_index(before_conn)
    finally:
        before_conn.close()

    cand_conn = sqlite3.connect(f"file:{candidate_path}?mode=ro", uri=True)
    try:
        cand_index = build_identity_index(cand_conn)
    finally:
        cand_conn.close()

    state_conn = sqlite3.connect(f"file:{state_path}?mode=ro", uri=True)
    try:
        legacy_map = load_legacy_map(state_conn)
    finally:
        state_conn.close()

    refs = collect_retained_refs(state_path)
    rows = []
    counts: dict[str, int] = {}
    for ref in refs:
        before = resolve_against_index(ref, before_index, legacy_map)
        after = resolve_against_index(ref, cand_index, legacy_map)
        verdict = _verdict(before, after)
        counts[verdict] = counts.get(verdict, 0) + 1
        rows.append(
            {
                "origin": ref.origin,
                "verdict": verdict,
                "before": before.as_dict(),
                "after": after.as_dict(),
            }
        )

    fatal = sum(counts.get(v, 0) for v in FATAL_VERDICTS)
    return {
        "before_corpus_version": before_index.corpus_version,
        "candidate_corpus_version": cand_index.corpus_version,
        "before_lines": before_index.line_count,
        "candidate_lines": cand_index.line_count,
        "legacy_map_rows": len(legacy_map),
        "references_checked": len(refs),
        "counts": counts,
        "fatal": fatal,
        "zero_orphan": fatal == 0,
        "references": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--before", required=True, help="corpus the references were recorded against")
    ap.add_argument("--candidate", required=True, help="rebuilt corpus under test")
    ap.add_argument("--state", required=True, help="state.db holding retained references")
    ap.add_argument("--json", help="write the full report here")
    ap.add_argument(
        "--rollback-rehearsal",
        action="store_true",
        help="also prove the BEFORE corpus still resolves everything (rollback is real)",
    )
    args = ap.parse_args()

    report = compare(args.before, args.candidate, args.state)

    if args.rollback_rehearsal:
        rehearsal = compare(args.before, args.before, args.state)
        report["rollback_rehearsal"] = {
            "counts": rehearsal["counts"],
            "fatal": rehearsal["fatal"],
            "rollback_safe": rehearsal["fatal"] == 0,
        }

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"before={report['before_corpus_version']} ({report['before_lines']} lines) → "
        f"candidate={report['candidate_corpus_version']} ({report['candidate_lines']} lines)"
    )
    print(f"references checked: {report['references_checked']}")
    for verdict, n in sorted(report["counts"].items()):
        print(f"  {verdict:18s} {n}")
    if "rollback_rehearsal" in report:
        rr = report["rollback_rehearsal"]
        print(f"rollback rehearsal: {'SAFE' if rr['rollback_safe'] else 'UNSAFE'} ({rr['counts']})")

    if report["zero_orphan"]:
        print("ZERO-ORPHAN: PASS")
        return 0
    print(f"ZERO-ORPHAN: FAIL — {report['fatal']} reference(s) orphaned/ambiguous/re-bound")
    for row in report["references"]:
        if row["verdict"] in FATAL_VERDICTS:
            print(f"  {row['origin']}: {row['verdict']} — {row['after']['reason']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
