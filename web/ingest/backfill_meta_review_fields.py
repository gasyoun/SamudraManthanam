"""Backfill Phase-0 review fields in per-source .meta.json sidecars.

The original extractor intentionally left `title_en`, `provenance`, and `rights`
empty because those fields needed a later review pass. This script fills them
with conservative, non-fabricated defaults:

* `title_en` is an English display title derived from the stable source slug
  (not a scholarly translation of the Russian bibliographic title).
* `provenance` says exactly where the sidecar facts came from.
* `rights` records the project-level grey-rights policy: usable in the site, not
  an open reusable corpus dump.

Run:  python web/ingest/backfill_meta_review_fields.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "Index" / "lib" / "x86_64-win64" / "Data"

PROVENANCE = (
    "Mechanically extracted from the legacy Samudra Manthanam HTML corpus "
    "header; reviewed as a Phase 0 sidecar default."
)
RIGHTS = (
    "In-copyright / rights not cleared for open redistribution. Use within the "
    "Samudra Manthanam search and reader interface; do not publish as an open "
    "corpus dump without separate rights review."
)

TOKEN_OVERRIDES = {
    "adi": "Adi",
    "adiparva": "Adi Parva",
    "anushasanaparva": "Anushasana Parva",
    "aranyakanda": "Aranya Kanda",
    "aranyakaparva": "Aranyaka Parva",
    "atharvaveda": "Atharvaveda",
    "ayodhyakanda": "Ayodhya Kanda",
    "balakanda": "Bala Kanda",
    "bhagavadgita": "Bhagavad Gita",
    "bhagavatgita": "Bhagavad Gita",
    "bhishmaparva": "Bhishma Parva",
    "dronaparva": "Drona Parva",
    "gitarthasamgraha": "Gitartha Samgraha",
    "harivamsha": "Harivamsha",
    "karnaparva": "Karna Parva",
    "mahabharata": "Mahabharata",
    "mahabharataadd": "Mahabharata Addenda",
    "mahabharataslovar": "Mahabharata Dictionary",
    "mahabharata_slovar": "Mahabharata Dictionary",
    "mausalaparva": "Mausala Parva",
    "naradasmriti": "Narada Smriti",
    "ramayana": "Ramayana",
    "ramayana-3-slovar": "Ramayana III Dictionary",
    "rigveda": "Rigveda",
    "sabha": "Sabha",
    "sabhaparva": "Sabha Parva",
    "shalyaparva": "Shalya Parva",
    "shantiparva": "Shanti Parva",
    "sundarakanda": "Sundara Kanda",
    "udyogaparva": "Udyoga Parva",
    "valmikiramayana": "Valmiki Ramayana",
    "vanaparva": "Vana Parva",
    "vishnu": "Vishnu",
    "vishnu-smriti": "Vishnu Smriti",
    "yajnavalkyasmriti": "Yajnavalkya Smriti",
}


def title_from_slug(slug: str) -> str:
    parts = [part for part in re.split(r"[-_]+", slug) if part]
    out: list[str] = []
    for part in parts:
        if part.isdigit():
            out.append(part)
        else:
            out.append(TOKEN_OVERRIDES.get(part, part.capitalize()))
    title = " ".join(out)
    title = re.sub(r"\b(\d{2})\b", lambda m: str(int(m.group(1))), title)
    return title or slug


def main() -> int:
    files = sorted(DATA_DIR.glob("*.meta.json"))
    if not files:
        print(f"No .meta.json files under {DATA_DIR}", file=sys.stderr)
        return 1

    changed = 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        before = dict(data)

        if not str(data.get("title_en", "")).strip():
            data["title_en"] = title_from_slug(str(data.get("slug") or path.stem))
        if not str(data.get("provenance", "")).strip():
            data["provenance"] = PROVENANCE
        if not str(data.get("rights", "")).strip():
            data["rights"] = RIGHTS

        if data != before:
            with path.open("w", encoding="utf-8", newline="") as fh:
                fh.write(json.dumps(data, ensure_ascii=False, indent=2))
                fh.write("\n")
            changed += 1

    print(f"meta files scanned: {len(files)}")
    print(f"meta files updated: {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
