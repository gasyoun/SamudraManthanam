#!/usr/bin/env python3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ignatiev_book_to_canonical as ig  # noqa: E402

arch = Path(
    r"C:/Users/user/Documents/GitHub/SamudraManthanam/"
    r"archive_ignatiev_2026/Переводы с санскрита"
)
works = [
    ("Майя-тантра", "Майя-тантра.pdf", "maya"),
    ("Нирвана-тантра", "nirvana-tantra.pdf", "nirvana"),
    ("Йони-тантра", "yoni-tantra.pdf", "yoni"),
    ("Нируттара-тантра", "Нируттара-тантра.pdf", "niruttara"),
    ("Гуптасадхана-тантра", "Гуптасадхана-тантра.pdf", "gupta"),
]
for folder, fname, slug in works:
    t = ig.extract_text(arch / folder / fname)
    _, rep = ig.parse_book(t, slug, footnote_mode="bracket")
    gaps = rep.get("verse_gaps") or []
    cols = rep.get("id_collisions") or []
    osc = sum(1 for g in gaps if "->1" in g or "->2" in g)
    print(
        f"{slug}: verses={rep['verse_count']} gaps={len(gaps)} "
        f"osc={osc} coll={len(cols)} ch={rep['chapters']}"
    )
