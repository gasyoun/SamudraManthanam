"""Verify the H2403 A41 uplift pack: blob-URL targets exist, lint hygiene holds.

Checks, for the three touched/added papers/ files:
  1. every https://github.com/gasyoun/SamudraManthanam/blob/main/<path> URL points at a
     path that exists in this checkout (a blob URL to a missing file 404s);
  2. no raw HTML tags (org .md rule);
  3. no trailing whitespace, file ends with exactly one newline;
  4. dated header present with DD-MM-YYYY and a closing byline.

Run:  python papers/scripts/verify_a41_uplift_links.py   (from the repo root)
Exit 0 = all green, 1 = at least one defect (printed).
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    "papers/A41_parallel_corpus_descriptor.md",
    "papers/A41_ARR_RESPONSIBLE_NLP_CHECKLIST.md",
    "papers/data/A41_DATA_STATEMENT_SAMUDRA_SA_RU_CORPUS.meta.md",
]

# `?raw=true` (and any query string) is a legitimate suffix on an image blob URL —
# strip it before resolving the path on disk, or every inline figure reads as dead.
BLOB_RE = re.compile(
    r"https://github\.com/gasyoun/SamudraManthanam/blob/main/([^\s)#?]+)"
)
TREE_RE = re.compile(
    r"https://github\.com/gasyoun/SamudraManthanam/tree/main/([^\s)#?]+)"
)
HTML_RE = re.compile(r"<(?!!--)(/?)(?:div|span|br|table|tr|td|th|img|p|b|i|u|font)\b")
HEADER_RE = re.compile(r"_Created: \d{2}-\d{2}-\d{4} · Last updated: \d{2}-\d{2}-\d{4}_")

failures: list[str] = []

for rel in TARGETS:
    path = ROOT / rel
    if not path.exists():
        failures.append(f"{rel}: MISSING FILE")
        continue
    text = path.read_text(encoding="utf-8")

    for regex, kind in ((BLOB_RE, "blob"), (TREE_RE, "tree")):
        for target in sorted(set(regex.findall(text))):
            if not (ROOT / target).exists():
                failures.append(f"{rel}: dead {kind} target -> {target}")

    for m in HTML_RE.finditer(text):
        line = text[: m.start()].count("\n") + 1
        failures.append(f"{rel}:{line}: raw HTML tag {m.group(0)!r}")

    for i, line in enumerate(text.split("\n"), start=1):
        if line != line.rstrip():
            failures.append(f"{rel}:{i}: trailing whitespace")

    if not text.endswith("\n") or text.endswith("\n\n"):
        failures.append(f"{rel}: must end with exactly one newline")

    if not HEADER_RE.search(text):
        failures.append(f"{rel}: missing DD-MM-YYYY dated header")

    if "_Dr. Mārcis Gasūns_" not in text:
        failures.append(f"{rel}: missing closing byline")

if failures:
    print("FAIL — %d defect(s):" % len(failures))
    for f in failures:
        print("  -", f)
    raise SystemExit(1)

print("PASS — %d files: blob/tree targets resolve, no HTML, hygiene + header/byline OK"
      % len(TARGETS))
