# -*- coding: utf-8 -*-
"""Fill translator names into RIGHTS_TABLE + emit A41_TRANSLATORS inventory (H2440 residual)."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
META_DIR = ROOT / "web" / "corpus_builder"
RIGHTS = ROOT / "nkrya-parallel" / "export" / "RIGHTS_TABLE.md"
GITA = ROOT / "papers" / "data" / "A41_gita_editions.tsv"
OUT_INV = ROOT / "papers" / "data" / "A41_TRANSLATORS.tsv"
OUT_MD = ROOT / "papers" / "data" / "A41_TRANSLATORS.md"

SHIP_ALL_NOTE = (
    "ship-all RU (MG 08-08-2026 H2440) — document translator; "
    "no per-translator ship gate"
)


def load_meta_credits():
    by_slug = {}
    for p in META_DIR.glob("*.meta.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        slug = d.get("slug") or p.name.replace(".meta.json", "")
        by_slug[slug] = {
            "credit": (d.get("credit") or "").strip(),
            "role": (d.get("credit_role") or "").strip(),
            "rights": (d.get("rights") or "").strip(),
            "year": d.get("year") or "",
            "title": d.get("title_display") or d.get("title_ru") or "",
        }
    return by_slug


def load_gita():
    if not GITA.is_file():
        return []
    with GITA.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def rewrite_rights_table(meta):
    text = RIGHTS.read_text(encoding="utf-8")
    lines = text.splitlines()
    out = []
    filled = already = empty = 0
    for line in lines:
        if not line.startswith("|") or line.startswith("| #") or line.startswith("|---"):
            if line.startswith("_Created:"):
                line = re.sub(
                    r"Last updated: \d{4}-\d{2}-\d{2}",
                    "Last updated: 2026-08-08",
                    line,
                )
            out.append(line)
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            out.append(line)
            continue
        num, slug, title, tr, rights, needs = cells[:6]
        if re.fullmatch(r":?-+:?", num) or num == "#":
            out.append(line)
            continue
        # Markdown wraps slugs in backticks; strip with chr(96) (PowerShell-safe).
        slug_clean = slug.replace(chr(96), "").strip()
        m = meta.get(slug_clean)
        tr_empty = tr in ("—", "-", "", "\u2014")
        if m and m["credit"]:
            if tr_empty:
                tr = m["credit"]
                filled += 1
            else:
                already += 1
            if m["title"] and (title == slug_clean or title.startswith(slug_clean[:8])):
                title = m["title"]
        elif tr_empty:
            empty += 1
        # Rewrite rights: always append ship-all if not present; prefer cleared grant text.
        if SHIP_ALL_NOTE not in rights:
            if m and m["rights"] and "cleared" in m["rights"].lower():
                base = m["rights"]
            else:
                base = rights if not tr_empty or rights not in ("—", "-", "", "\u2014") else "in-copyright / grey residual"
                if rights not in ("—", "-", "", "\u2014"):
                    base = rights
                base = re.sub(
                    r"\s*—\s*corpus rights stay grey per project ruling; no redistribution(?:, export bulk gitignored)?",
                    "",
                    base,
                )
                base = re.sub(r"\s*—\s*no redistribution.*$", "", base)
                base = re.sub(r"\s*·\s*ship-all RU.*$", "", base)
            rights = f"{base} · {SHIP_ALL_NOTE}"
        bt = chr(96)
        out.append(
            f"| {num} | {bt}{slug_clean}{bt} | {title} | {tr} | {rights} | {needs} |"
        )
    body = "\n".join(out)
    if "ship-all RU (MG 08-08-2026 H2440)" not in body[:1200]:
        body = body.replace(
            "One row per exported seg=ru source",
            "**Policy (MG 08-08-2026, H2440):** **ship all** Russian text; "
            "**never reask** a per-translator ship gate. "
            "This table **documents translators** (and residual attribution gaps). "
            "Bulk gitignore of export artifacts is engineering, not a rights park.\n\n"
            "One row per exported seg=ru source",
            1,
        )
    RIGHTS.write_text(body + "\n", encoding="utf-8", newline="\n")
    return filled, already, empty


def write_inventory(meta, gita):
    inv = []
    for slug, m in sorted(meta.items()):
        inv.append({
            "slug": slug,
            "translator": m["credit"] or "—",
            "role": m["role"] or "—",
            "year": str(m["year"] or "—"),
            "title": m["title"] or "—",
            "source": "meta.json",
            "scope": "A41 corpus / Samudra",
        })
    seen = {r["slug"] for r in inv}
    for row in gita:
        slug = row.get("slug", "")
        if slug in seen:
            continue
        credit = (row.get("credit") or "").strip()
        inv.append({
            "slug": slug,
            "translator": credit or "—",
            "role": "translation",
            "year": str(row.get("orig_year") or row.get("year") or "—"),
            "title": f"Bhagavadgītā · {credit}" if credit else "Bhagavadgītā",
            "source": "A41_gita_editions.tsv",
            "scope": "A41 §5 Gītā register",
        })
    fields = ["slug", "translator", "role", "year", "title", "source", "scope"]
    with OUT_INV.open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        for row in inv:
            w.writerow(row)
    by_tr = {}
    for row in inv:
        by_tr.setdefault(row["translator"], []).append(row["slug"])
    lines = [
        "# A41 / Samudra — translator inventory (ship-all residual)",
        "",
        "_Created: 08-08-2026 · Last updated: 08-08-2026_",
        "",
        "**Policy:** MG 08-08-2026 (H2440) — **ship all** RU text for A41/A42 paths. "
        "This file **documents the different translators**; it is not a ship/no-ship gate.",
        "",
        f"**Machine twin:** [`A41_TRANSLATORS.tsv`](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_TRANSLATORS.tsv) "
        f"({len(inv)} source rows · {len(by_tr)} distinct translator/credit strings).",
        "",
        "Sources: committed `web/corpus_builder/*.meta.json` `credit` fields + "
        "[`A41_gita_editions.tsv`](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_gita_editions.tsv). "
        "Rows still `—` on the 131-source НКРЯ RIGHTS_TABLE lack a committed meta credit "
        "(H821 metadata-loss residual) — fill when meta is restored, not by guessing.",
        "",
        "## Distinct translators / credits",
        "",
        "| Translator / credit | # sources | Example slugs |",
        "|---|--:|---|",
    ]
    for t, slugs in sorted(by_tr.items(), key=lambda x: (-len(x[1]), x[0])):
        ex = ", ".join(f"`{s}`" for s in slugs[:4])
        if len(slugs) > 4:
            ex += f", … (+{len(slugs) - 4})"
        lines.append(f"| {t} | {len(slugs)} | {ex} |")
    lines += [
        "",
        "## Per-source table",
        "",
        "| Slug | Translator | Role | Year | Title | Source |",
        "|---|---|---|---|---|---|",
    ]
    for row in inv:
        lines.append(
            f"| `{row['slug']}` | {row['translator']} | {row['role']} | {row['year']} | "
            f"{row['title']} | {row['source']} |"
        )
    lines += ["", "_Dr. Mārcis Gasūns_", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return len(inv), len(by_tr)


def main():
    meta = load_meta_credits()
    gita = load_gita()
    filled, already, empty = rewrite_rights_table(meta)
    n, nt = write_inventory(meta, gita)
    print(
        f"RIGHTS_TABLE: filled {filled} empty translator cells from meta; "
        f"{already} already set; {empty} still empty"
    )
    print(f"A41_TRANSLATORS: {n} rows, {nt} distinct credits")


if __name__ == "__main__":
    main()
