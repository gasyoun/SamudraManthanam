"""Export a filtered word-of-the-day pool from the Kochergina dictionary (H4955).

Kochergina (`koch`) is approved for extensive use in the `pwg_ru` edition —
ship-all ruling, per-card attribution preserved, no per-translator reask
(SanskritLexicography/RussianTranslation/RIGHTS_APPROVALS.md § "Dictionary /
reference sources").

Source: `pwg-ru-data/corpus/koch.jsonl` (private sibling repo, Git LFS,
29,177 entries — `{"source": "koch", "slp1": ..., "iast": ..., "gloss": ...}`).
That repo is not expected to be checked out on the production host, so this
script runs at dev/maintenance time and commits its filtered, self-contained
output into this repo. The nightly picker (`word_of_day_generate.py`) only
ever reads the committed pool, never the source repo.

Filtering:
- drop bound/compound-only stems (slp1 starting with "-")
- drop entries with an empty gloss
- Devanagari is re-derived from `slp1` via the vendored `sanskrit_util`
  (authoritative transcode), not scraped from the gloss text
- the gloss's own trailing Devanagari+IAST echo (Kochergina's print
  convention repeats headword forms at the end of the gloss) is stripped,
  since headword/IAST/Devanagari are already carried as separate fields
- part of speech is a best-effort regex extraction from the standard
  Kochergina abbreviation set embedded in the gloss; entries where no
  abbreviation matches ship with pos="" rather than a fabricated guess

Usage:
    python scripts/word_of_day_export_pool.py [--source PATH] [--out PATH]
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "web"))

from app.vendor import sanskrit_util as _su  # noqa: E402

DEFAULT_SOURCE = REPO_ROOT.parent / "pwg-ru-data" / "corpus" / "koch.jsonl"
DEFAULT_OUT = REPO_ROOT / "web" / "app" / "data" / "word_of_day_pool.jsonl"

DEVANAGARI_TAIL_RE = re.compile(r"[ऀ-ॿ].*$")

# Standard abbreviations used throughout Kochergina's printed dictionary.
# Ordered longest-first so e.g. "pl." doesn't shadow a longer match.
POS_ABBREV = [
    ("bah.", "bahuvrihi"),
    ("adj.", "adjective"),
    ("adv.", "adverb"),
    ("num.", "numeral"),
    ("prep.", "preposition"),
    ("conj.", "conjunction"),
    ("part.", "particle"),
    ("pron.", "pronoun"),
    ("pl.", "plural"),
    ("m.", "masculine"),
    ("f.", "feminine"),
    ("n.", "neuter"),
]
POS_RE = re.compile(
    r"(?<![A-Za-z])(" + "|".join(re.escape(a) for a, _ in POS_ABBREV) + r")"
)


def extract_pos(gloss: str) -> str:
    m = POS_RE.search(gloss)
    return m.group(1) if m else ""


def clean_gloss(gloss: str) -> str:
    stripped = DEVANAGARI_TAIL_RE.sub("", gloss).strip()
    return stripped or gloss.strip()


def build_pool(source: Path):
    entries = []
    with source.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            slp1 = row.get("slp1", "")
            iast = row.get("iast", "")
            gloss = row.get("gloss", "")
            if not slp1 or slp1.startswith("-") or slp1.endswith("-"):
                continue
            if not gloss.strip():
                continue
            entries.append({
                "entry_id": f"koch:{slp1}",
                "slp1": slp1,
                "iast": iast,
                "devanagari": _su.slp1_to_devanagari(slp1),
                "gloss": clean_gloss(gloss),
                "pos": extract_pos(gloss),
                "source": "Кочергина В. А., Санскритско-русский словарь",
            })
    return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if not args.source.exists():
        print(f"Source not found: {args.source}", file=sys.stderr)
        print("Run `git lfs pull --include=corpus/koch.jsonl` in pwg-ru-data first.", file=sys.stderr)
        sys.exit(1)

    entries = build_pool(args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"Wrote {len(entries)} entries to {args.out}")


if __name__ == "__main__":
    main()
