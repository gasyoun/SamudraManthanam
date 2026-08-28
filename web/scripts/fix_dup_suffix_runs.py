"""Repair duplicate-suffix debris runs in canonical JSONL (H3614).

Root cause. The legacy Ignatiev exporter anchored every interleaved
front-matter/essay chunk of a chapter to the *upcoming* verse anchor and
disambiguated collisions with a bare ``chr(ord(c) + 1)`` letter run that never
stopped at ``b`` — or even at ``z`` (shaktisangama-tantra ch.37 ran
``37.2b..37.2\\x86``; brihannila-tantra ch.22 ran ``22.2b..22.2y``). The last
member of each such run is the real verse; every earlier member is
scholarly-apparatus prose carrying a false verse identity, and the bare base
slot is held by a navigation chunk, not the verse.

What this script does (deterministic, idempotent, auditable — never a hand
edit, never an invariant weakening):

* scans every canonical JSONL the corpus gate reads
  (``dup_suffix_report.canonical_jsonl_files``);
* groups records sharing the same ``work`` + numeric passage root + segment
  tail, where a member may carry one trailing debris suffix (the old mint
  allowed any ``chr()`` character once ``z`` overflowed);
* a group of THREE or more members is a debris run (collisions are pairs —
  ``base`` + ``b`` stays untouched, matching the ``suffix_depth`` invariant);
* inside a run, the LAST member in file order is re-keyed to the bare root
  (restoring the real verse's identity) and every earlier member is re-keyed
  to a Class C prose paragraph id ``c{chapter}.p{n}`` (LINE_ID_SCHEME §C —
  note: no dot after ``c``; the ``c.`` prefix is reserved for nav headings
  and must never appear in JSONL), preserving the record's ``chapter`` field
  and file position;
* groups containing ``.comm`` members are reported and SKIPPED (re-keying a
  commentary id would orphan its ``annotates`` link — none exist today).

Only ``id`` / ``passage`` / ``group`` are rewritten; every untouched line is
preserved byte-for-byte. Re-running after a repair is a no-op.

Usage
-----
    python web/scripts/fix_dup_suffix_runs.py --dry-run   # report only
    python web/scripts/fix_dup_suffix_runs.py             # apply + report
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SCRIPTS_ROOT = Path(__file__).resolve().parent
WEB_ROOT = SCRIPTS_ROOT.parent
for p in (str(SCRIPTS_ROOT), str(WEB_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from dup_suffix_report import DUP_ID_RE, canonical_jsonl_files  # noqa: E402

# Bare numeric passage: `work:22.2#ru`, `work:22.2`, `work:22.2.comm1`.
BARE_ID_RE = re.compile(
    r"^(?P<work>[^:]+):(?P<root>[0-9.]+)(?P<tail>(?:#|\.comm).*)$"
)

MIN_RUN_MEMBERS = 3


class RepairError(Exception):
    """A file cannot be repaired safely — stop loudly instead of guessing."""


def _split_id(rid: str):
    """Return ``(work, root, suffix_or_None, tail)`` for a numeric-passage id.

    ``tail`` is the ``#seg`` or ``.comm…`` remainder (possibly empty-shaped —
    always present for sa/ru/comm records). Returns ``None`` for ids that are
    not verse/comment numeric-passage ids (prose, dictionaries, sequences).
    """
    m = DUP_ID_RE.match(rid)
    if m:
        work, root = m.group("base").rsplit(":", 1)
        return work, root, m.group("suffix"), m.group("tail")
    mb = BARE_ID_RE.match(rid)
    if mb:
        return mb.group("work"), mb.group("root"), None, mb.group("tail")
    return None


def find_run_groups(records: list[dict]) -> tuple[dict[tuple, list[int]], list[dict]]:
    """Return (safe debris-run groups, skipped unsafe groups).

    A group key is ``(work, root, tail)``; members are record indexes in file
    order. Groups with ``MIN_RUN_MEMBERS`` or more members qualify. A group is
    SKIPPED when any commentary record annotates the run's root (or carries a
    ``.comm`` id on it) — re-keying the verse id would orphan the commentary's
    ``annotates`` link, so a human reviews instead.
    """
    groups: dict[tuple, list[int]] = {}
    comm_roots: dict[str, set] = {}
    for idx, rec in enumerate(records):
        parts = _split_id(rec["id"])
        if parts is None:
            continue
        work, root, _suffix, tail = parts
        groups.setdefault((work, root, tail), []).append(idx)
        if ".comm" in rec["id"] or rec.get("annotates"):
            comm_roots.setdefault(rec.get("work", work), set()).add(
                rec.get("annotates") or root
            )

    runs: dict[tuple, list[int]] = {}
    skipped: list[dict] = []
    for key, idxs in groups.items():
        if len(idxs) < MIN_RUN_MEMBERS:
            continue
        work, root, _tail = key
        if root in comm_roots.get(work, set()):
            skipped.append(
                {
                    "group": key,
                    "members": [records[i]["id"] for i in idxs],
                    "reason": (
                        "a commentary annotates this passage root — manual "
                        "review owed (re-keying would orphan annotates)"
                    ),
                }
            )
            continue
        runs[key] = idxs
    return runs, skipped


def repair_records(
    records: list[dict], filename: str
) -> tuple[list[dict], list[dict], list[dict]]:
    """Return (new_records, changes, skipped) for one file's records."""
    runs, skipped = find_run_groups(records)
    if not runs:
        return records, [], skipped

    changes: list[dict] = []
    taken_ids = {rec["id"] for rec in records}
    prose_n = 0

    # Groups ordered by earliest member: prose paragraph ids then follow
    # document order deterministically.
    for key in sorted(runs, key=lambda k: min(runs[k])):
        idxs = runs[key]
        work, root, tail = key
        last = idxs[-1]
        for pos, idx in enumerate(idxs):
            rec = records[idx]
            old_id = rec["id"]
            if pos == len(idxs) - 1:
                final_id = f"{work}:{root}{tail}"
            else:
                chapter = str(rec.get("chapter") or "0")
                while True:
                    prose_n += 1
                    candidate = f"c{chapter}.p{prose_n}"
                    final_id = f"{work}:{candidate}{tail}"
                    if final_id not in taken_ids:
                        break
            if final_id == old_id:  # pragma: no cover - already bare
                continue
            if final_id in taken_ids:
                raise RepairError(
                    f"{filename}: re-key {old_id!r} → {final_id!r} collides "
                    f"with an existing id — refusing to guess"
                )
            rec["id"] = final_id
            rec["passage"] = final_id.split(":", 1)[1].split("#", 1)[0]
            rec["group"] = f"{work}:{rec['passage']}"
            rec["_h3614_rekeyed"] = True
            taken_ids.discard(old_id)
            taken_ids.add(final_id)
            changes.append({"old": old_id, "new": final_id})
    return records, changes, skipped


def repair_file(path: Path, dry_run: bool) -> dict:
    with open(path, encoding="utf-8", newline="") as fh:
        raw_lines = fh.readlines()

    records: list[dict] = []
    for line in raw_lines:
        stripped = line.strip()
        records.append(json.loads(stripped) if stripped else {})

    new_records, changes, skipped = repair_records(records, path.name)
    if not changes:
        return {"file": path.name, "changes": [], "skipped": skipped}

    out_lines = []
    for line, rec in zip(raw_lines, new_records):
        if not line.strip():
            out_lines.append(line)
            continue
        if rec.get("_h3614_rekeyed"):
            del rec["_h3614_rekeyed"]
            ending = "\n" if line.endswith("\n") else ""
            out_lines.append(json.dumps(rec, ensure_ascii=False) + ending)
        else:
            out_lines.append(line)

    if not dry_run:
        tmp = path.with_name(path.name + ".repair-tmp")
        with open(tmp, "w", encoding="utf-8", newline="") as fh:
            fh.writelines(out_lines)
        tmp.replace(path)
    return {"file": path.name, "changes": changes, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run", action="store_true", help="Report the repair without writing"
    )
    args = parser.parse_args()

    files = canonical_jsonl_files()
    if not files:
        print("SKIP  canonical JSONL not found — nothing to repair.", file=sys.stderr)
        return 0

    total_changes = 0
    for path in files:
        result = repair_file(path, args.dry_run)
        if result["changes"] or result["skipped"]:
            print(f"== {result['file']}")
            for change in result["changes"]:
                print(f"   {change['old']}  ->  {change['new']}")
            for skip in result["skipped"]:
                print(f"   SKIPPED {skip['group']}: {skip['reason']}")
        total_changes += len(result["changes"])

    mode = "DRY-RUN" if args.dry_run else "APPLIED"
    print(f"\n{mode}: {total_changes} id(s) re-keyed across canonical JSONL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
