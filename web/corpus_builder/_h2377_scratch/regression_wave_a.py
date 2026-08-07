#!/usr/bin/env python3
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ignatiev_book_to_canonical as ig  # noqa: E402

arch = Path(
    r"C:/Users/user/Documents/GitHub/SamudraManthanam/"
    r"archive_ignatiev_2026/Переводы с санскрита"
)
jsonl = Path(__file__).resolve().parents[1] / "jsonl"
works = [
    ("Йони-тантра", "yoni-tantra", "yoni-tantra.pdf"),
    ("Нируттара-тантра", "niruttara-tantra", "Нируттара-тантра.pdf"),
    ("Гуптасадхана-тантра", "guptasadhana-tantra", "Гуптасадхана-тантра.pdf"),
    ("Нирвана-тантра", "nirvana-tantra", "nirvana-tantra.pdf"),
]
for folder, slug, fname in works:
    src = arch / folder / fname
    committed = jsonl / f"{slug}.raw.jsonl"
    text = ig.extract_text(src)
    mode = ig.detect_footnote_mode(text)
    recs, rep = ig.parse_book(text, slug, footnote_mode="auto")
    old_n = sum(
        1
        for ln in committed.read_text(encoding="utf-8").splitlines()
        if ln.strip() and json.loads(ln).get("seg") == "ru"
    )
    new_n = rep["verse_count"]
    # Passage-set delta vs committed (stronger than count).
    old_ps = {
        json.loads(ln)["passage"]
        for ln in committed.read_text(encoding="utf-8").splitlines()
        if ln.strip() and json.loads(ln).get("seg") == "ru"
    }
    new_ps = {r["passage"] for r in recs if r.get("seg") == "ru"}
    print(
        f"{slug}: mode={mode} committed_ru={old_n} new_ru={new_n} "
        f"delta={new_n - old_n} ch={rep['chapters']} "
        f"gaps={len(rep.get('verse_gaps') or [])} "
        f"pass_only_old={len(old_ps - new_ps)} "
        f"pass_only_new={len(new_ps - old_ps)}"
    )
