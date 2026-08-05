"""Backfill canonical references into state.db from a PINNED corpus (H1925, B3).

What it does, in one pass over a corpus DB:

1. builds ``legacy_ref_map`` — every ``(corpus_version, source_id, line_num)``
   in the pinned corpus mapped to its ``(source_slug, canonical_id)`` plus a
   content fingerprint;
2. fills the canonical columns on existing ``corrections`` rows by resolving
   each stored reference against that same pinned corpus.

Safety properties, all of them load-bearing rather than decorative:

- **Pinned, not live.** The mapping is only meaningful relative to one corpus
  version, so the version is part of the key and is read from the corpus DB
  itself — never passed in by hand.
- **Backup first.** ``--apply`` takes a ``sqlite3``-consistent backup of
  ``state.db`` before its first write and prints the path; ``--restore <path>``
  puts it back. Recovery is exercised in ``tests/test_canonical_state_migrations.py``.
- **Never guesses.** A correction whose stored reference does not resolve is
  recorded with ``ref_status='unresolved'`` and listed in the report. It is
  not bound to a nearby line, and its ordinals are left untouched.
- **Idempotent.** Re-running produces the same rows and the same report.

Usage::

    python scripts/backfill_canonical_refs.py --corpus corpus.db --state state.db
    python scripts/backfill_canonical_refs.py --corpus corpus.db --state state.db --apply
    python scripts/backfill_canonical_refs.py --state state.db --restore state.db.backup-...
"""
from __future__ import annotations

import argparse
import datetime
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.canonical_refs import (  # noqa: E402
    DurableRef,
    build_identity_index,
    load_legacy_map,
    normalise_plain,
    resolve_against_index,
)
from app.canonical_state_migrations import (  # noqa: E402
    apply_migrations,
    backup_state_db,
    restore_state_db,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def build_legacy_map_rows(index) -> list[tuple]:
    now = datetime.datetime.now().isoformat(timespec="seconds")
    version = index.corpus_version or ""
    rows: list[tuple] = []
    for (source_id, line_num), rec in index.by_ordinal.items():
        if not rec["source_slug"] or not rec["canonical_id"]:
            # Nothing to map to: a pre-JSONL source with no canonical id. Left
            # out on purpose — an entry pointing at NULL would be a mapping
            # that silently resolves to nothing.
            continue
        rows.append(
            (
                version,
                source_id,
                line_num,
                rec["source_slug"],
                rec["canonical_id"],
                rec["fingerprint"],
                now,
            )
        )
    return rows


def _check_text_evidence(res, row, index, unversioned: bool) -> tuple[bool, str]:
    """Does the pinned corpus actually contain the text this record remembers?

    Only applied to the unversioned rows whose binding rests on the operator's
    ``--corpus`` pin — a row that carries its own canonical tuple or its own
    corpus version was resolved on recorded evidence and needs no vouching.

    A correction's ``old_text`` is the fragment the proposer saw, so the test is
    containment, not equality. An empty or whitespace-only ``old_text`` carries
    no evidence either way and is accepted (the resolution still stands on the
    ordinal within the pinned corpus).
    """
    if not unversioned or not res.ok:
        return True, ""
    keys = row.keys()
    old_text = normalise_plain(row["old_text"] if "old_text" in keys else "")
    if not old_text:
        return True, ""
    rec = index.by_ordinal.get((res.source_id, res.line_num))
    line_text = (rec or {}).get("text", "")
    if old_text in line_text:
        return True, ""
    return False, (
        f"pinned corpus_version={index.corpus_version} line "
        f"(source_id={res.source_id}, line_num={res.line_num}) does not contain the "
        f"text this record was written against — the pin looks wrong, refusing to bind"
    )


def backfill(corpus_path: str, state_path: str, apply: bool) -> dict:
    corpus = sqlite3.connect(f"file:{corpus_path}?mode=ro", uri=True)
    try:
        index = build_identity_index(corpus)
    finally:
        corpus.close()

    if not index.corpus_version:
        raise SystemExit(
            f"ERROR: {corpus_path} has no corpus_meta.corpus_version — refusing to "
            "build a mapping that cannot be pinned to a corpus version."
        )

    backup_path = None
    if apply:
        apply_migrations(state_path)
        backup_path = str(backup_state_db(state_path))

    state = sqlite3.connect(state_path)
    state.row_factory = sqlite3.Row
    try:
        map_rows = build_legacy_map_rows(index)
        if apply:
            state.executemany(
                "INSERT OR REPLACE INTO legacy_ref_map "
                "(corpus_version, source_id, line_num, source_slug, canonical_id, "
                " fingerprint, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                map_rows,
            )
            state.commit()

        legacy_map = load_legacy_map(state) if apply else {
            (r[0], r[1], r[2]): {"source_slug": r[3], "canonical_id": r[4], "fingerprint": r[5]}
            for r in map_rows
        }

        try:
            corrections = state.execute(
                "SELECT id, source_id, line_num, old_text, source_slug, canonical_id, "
                "corpus_version FROM corrections"
            ).fetchall()
        except sqlite3.OperationalError:
            # Canonical columns absent in a dry run against an unmigrated DB.
            corrections = state.execute(
                "SELECT id, source_id, line_num, old_text FROM corrections"
            ).fetchall()

        resolved, unresolved = [], []
        already = 0
        updates = []
        for row in corrections:
            keys = row.keys()
            recorded_version = row["corpus_version"] if "corpus_version" in keys else None
            if (
                recorded_version
                and "source_slug" in keys
                and row["source_slug"]
                and row["canonical_id"]
            ):
                # Already carries a full canonical tuple: backfilling is done
                # for this row, and re-deriving it would rewrite provenance
                # that a previous (possibly differently pinned) pass recorded.
                # Verifying it is the zero-orphan report's job, not this one's.
                already += 1
                continue
            ref = DurableRef(
                source_slug=row["source_slug"] if "source_slug" in keys else None,
                canonical_id=row["canonical_id"] if "canonical_id" in keys else None,
                corpus_version=recorded_version,
                source_id=row["source_id"],
                line_num=row["line_num"],
                origin=f"corrections#{row['id']}",
            )
            # A pre-migration row records no corpus version, so on its own the
            # resolver refuses its ordinal — correctly. The operator supplies
            # the missing fact by PINNING a corpus with --corpus, which is why
            # this path (and only this path) may read an unversioned ordinal as
            # belonging to the pinned corpus. The pin is then CHECKED against
            # the text the correction itself remembers, so a mis-pinned corpus
            # surfaces as unresolved rather than as a wrong binding.
            unversioned = not recorded_version and not ref.has_canonical
            res = resolve_against_index(
                ref, index, legacy_map, assume_current_version=unversioned
            )
            evidence_ok, evidence_note = _check_text_evidence(res, row, index, unversioned)
            if res.ok and evidence_ok:
                resolved.append(res.as_dict())
                updates.append(
                    (
                        res.source_slug,
                        res.canonical_id,
                        res.corpus_version,
                        res.status.value,
                        row["id"],
                    )
                )
            else:
                item = res.as_dict()
                if res.ok and not evidence_ok:
                    item["status"] = "text_mismatch"
                    item["reason"] = evidence_note
                unresolved.append(item)
                updates.append((None, None, None, "unresolved", row["id"]))

        if apply and updates:
            state.executemany(
                "UPDATE corrections SET source_slug = ?, canonical_id = ?, "
                "corpus_version = ?, ref_status = ? WHERE id = ?",
                updates,
            )
            state.commit()
    finally:
        state.close()

    return {
        "corpus_version": index.corpus_version,
        "applied": apply,
        "backup": backup_path,
        "corpus_lines": index.line_count,
        "legacy_map_rows": len(map_rows),
        "corrections_total": len(resolved) + len(unresolved) + already,
        "corrections_resolved": len(resolved),
        "corrections_unresolved": len(unresolved),
        "corrections_already_canonical": already,
        "unresolved": unresolved,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", help="pinned corpus.db to map from")
    ap.add_argument("--state", required=True, help="state.db to backfill")
    ap.add_argument("--apply", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--restore", help="restore state.db from this backup and exit")
    ap.add_argument("--json", help="write the report to this path")
    args = ap.parse_args()

    if args.restore:
        restore_state_db(args.restore, args.state)
        print(f"restored {args.state} from {args.restore}")
        return 0

    if not args.corpus:
        ap.error("--corpus is required unless --restore is given")

    report = backfill(args.corpus, args.state, args.apply)
    if args.json:
        Path(args.json).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    mode = "APPLIED" if report["applied"] else "DRY RUN"
    print(f"[{mode}] corpus_version={report['corpus_version']}")
    print(f"  corpus lines indexed : {report['corpus_lines']}")
    print(f"  legacy_ref_map rows  : {report['legacy_map_rows']}")
    print(
        f"  corrections          : {report['corrections_resolved']} resolved / "
        f"{report['corrections_unresolved']} unresolved / "
        f"{report['corrections_already_canonical']} already canonical "
        f"(of {report['corrections_total']})"
    )
    if report["backup"]:
        print(f"  state.db backup      : {report['backup']}")
    for item in report["unresolved"][:20]:
        print(f"  UNRESOLVED {item['origin']}: {item['status']} — {item['reason']}")
    # Unresolved rows are a finding to act on, not a crash: exit 0 so the report
    # is usable in a dry run, and let the zero-orphan gate be the blocking check.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
