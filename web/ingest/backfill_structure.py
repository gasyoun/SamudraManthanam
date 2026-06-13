"""Backfill the `structure` field (verse | dictionary | prose) into every
per-source .meta.json, per the authoritative rule in docs/CONVERTER_SPEC.md §9.3.

Rule (in order):
  1. citation_block count > 0          -> "verse"
  2. slug matches a dictionary marker  -> "dictionary"
  3. otherwise                         -> "prose"

This replaces the low-confidence census heuristic (which mis-read the 53
range-dependent Vedic/Epic files as prose) with the simple, correct test:
any file carrying citation_block markup is a verse text.

Reads citation_block counts from docs/TAG_CENSUS.json (already produced by
tag_census.py) so it needs no second corpus scan. Writes UTF-8 without BOM,
preserving key order and all existing fields.

Run:  cd web ; python ingest/backfill_structure.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
ROOT = os.path.dirname(WEB)
DATA_DIR = os.path.join(ROOT, "Index", "lib", "x86_64-win64", "Data")
CENSUS = os.path.join(ROOT, "docs", "TAG_CENSUS.json")

# Dictionary slug markers (same set as the converter spec / census heuristic).
DICT_MARKERS = (
    "slovar", "dic_", "kewa", "kochergina", "kossovich", "knauer",
    "warnemyr", "fasmer", "dsg", "toporov", "ramayana-3-slovar",
)


def classify(slug: str, citation_block: int) -> str:
    if citation_block > 0:
        return "verse"
    if any(k in slug for k in DICT_MARKERS):
        return "dictionary"
    return "prose"


def main() -> None:
    census = json.load(open(CENSUS, encoding="utf-8"))

    changed = updated = missing = unchanged = 0
    dist = {"verse": 0, "dictionary": 0, "prose": 0}

    for rec in census["sources"]:
        filename = rec["filename"]
        slug = rec["slug"]
        structure = classify(slug, rec["tags"]["citation_block"])
        dist[structure] += 1

        meta_path = os.path.join(DATA_DIR, filename + ".meta.json")
        if not os.path.exists(meta_path):
            print(f"  MISSING meta.json: {filename}")
            missing += 1
            continue

        with open(meta_path, "r", encoding="utf-8") as fh:
            meta = json.load(fh)

        if meta.get("structure") == structure:
            unchanged += 1
            continue

        # Insert `structure` right after `scripts` if present, else append,
        # so the field lands in a sensible spot without reordering the rest.
        new_meta = {}
        inserted = False
        for k, v in meta.items():
            new_meta[k] = v
            if k == "scripts" and not inserted:
                new_meta["structure"] = structure
                inserted = True
        if not inserted:
            new_meta["structure"] = structure

        was_present = "structure" in meta
        # Match the existing skeleton formatting: 2-space indent, UTF-8 no BOM,
        # trailing newline, LF line endings (newline="" + manual \n keeps Git
        # from seeing a whole-file reformat).
        with open(meta_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(new_meta, ensure_ascii=False, indent=2))
            fh.write("\n")
        updated += 1 if was_present else 0
        changed += 1

    print(f"distribution: {dist} (total {sum(dist.values())})")
    print(f"written: {changed}  (of which value-changed: {updated})  "
          f"unchanged: {unchanged}  missing: {missing}")


if __name__ == "__main__":
    main()
