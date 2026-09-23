#!/usr/bin/env python3
"""H5281 — ONE review sheet for the НКРЯ showcase bibliography (≤10 cards).

Three `sphere` cards (the agent's proposed НКРЯ sphere per group of showcase
texts) + a seeded 7-row random spot-check of the filled bibliographic rows
(translator · date_trans · publisher), drawn from the 16 distinct
bibliographic records behind the 24 showcase texts (Rigveda I–IV / V–VIII /
IX–X, MBh III, Rām I–II / III, ten Gītās) so one printed volume is never
counted twice. Every card carries the agent's verification (Evidence panel +
ssb-evidence stamp, H4114 gate); the human rules on what the agent could not.

Source of truth: web/corpus_builder/nkrya_showcase_bib.json.
Usage:  python scripts/build_nkrya_showcase_sheet.py
Output: review/samudramanthanam-nkrya-showcase-bib_spotcheck10_review.html
"""
import html
import json
import os
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")

from csl_pyutil import render_review_sheet  # noqa: E402
from csl_pyutil.evidence import EvidenceManifest  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BIB = os.path.join(REPO, "web", "corpus_builder", "nkrya_showcase_bib.json")
SHEET_ID = "samudramanthanam-nkrya-showcase-bib_spotcheck10"
SHEET = os.path.join(REPO, "review", f"{SHEET_ID}_review.html")
GENERATED = "23-09-2026"
VERIFIER = "Claude Code Opus 5.5 (claude-opus-5-5)"
SEED = 5281
SPOT_N = 7

# 16 distinct bibliographic records -> representative slug (one volume, one row)
RECORDS = {
    "rv_i_iv": "01_rigveda", "rv_v_viii": "05_rigveda", "rv_ix_x": "09_rigveda",
    "mbh_iii": "03_mahabharata-aranyakaparva", "ram_i_ii": "01_ramayana-balakanda",
    "ram_iii": "03_ramayana-aranyakanda",
    **{g: g for g in ("bhagavadgita-1788", "bhagavadgita-1909", "bhagavadgita-1914",
                      "bhagavadgita-smirnov", "bhagavadgita-sementsov", "bhagavadgita-erman",
                      "bhagavadgita-burba", "bhagavadgita-prabhupada", "bhagavadgita-radha",
                      "bhagavadgita-sharma")},
}

# Verification done by the agent 23-09-2026 — quoted from the fetched page.
SPOT_EVIDENCE = {
    "rv_i_iv": ("https://ru.wikipedia.org/wiki/%D0%A0%D0%B8%D0%B3%D0%B2%D0%B5%D0%B4%D0%B0",
                "«М.: Наука, 1989-99. Мандалы I—IV. 1989. 768 с. (2-е изд., испр. — 1999)»"),
    "rv_ix_x": ("https://ru.wikipedia.org/wiki/%D0%A0%D0%B8%D0%B3%D0%B2%D0%B5%D0%B4%D0%B0",
                "«Мандалы IX—X. 1999. 560 с. 2500 экз.»"),
    "mbh_iii": ("https://fantlab.ru/edition309935",
                "«М.: Главная редакция восточной литературы издательства «Наука», 1987 г.» · "
                "«перевод Я. Василькова, С. Невелевой»"),
    "ram_i_ii": ("https://ladomirbook.ru/books/ramayana-3-aranyakanda/",
                 "«Рамаяна. Книга I: Балаканда … Кн. II: Айодхьяканда … М.: Ладомир: Наука, 2006» · "
                 "«в переводе Павла Александровича Гринцера»"),
    "bhagavadgita-1788": ("http://bhagavadgita.ru/bg_1788.htm",
                          "«Багуат-Гета, или Бесѣды Кришны съ Аржуномъ» · «на Англійской, и съ сего на "
                          "Россійской языкъ» · «Въ Университетской Типографіи у Н. Новикова. 1788» · "
                          "«Переводчик: Александр Андреевич Петров»"),
    "bhagavadgita-burba": ("https://archive.org/details/bkhagavad-gita-burba",
                           "«[пер. с санскрита Д. Бурбы]. — М.: РИПОЛ классик, 2009. — 560 с.» · "
                           "ISBN 978-5-386-01452-0 (also bookvoed.ru/book?id=380586)"),
    "bhagavadgita-prabhupada": ("https://ru.wikipedia.org/wiki/%D0%91%D1%85%D0%B0%D0%B3%D0%B0%D0%B2%D0%B0%D0%B4-%D0%B3%D0%B8%D1%82%D0%B0_%D0%BA%D0%B0%D0%BA_%D0%BE%D0%BD%D0%B0_%D0%B5%D1%81%D1%82%D1%8C",
                                "first Russian edition 1984 (BBT), a double translation Sanskrit→English→"
                                "Russian (Серебряный 1999); translated by a team coordinated by "
                                "О. Х. Киселева (vasudeva.ru «Подвиг самиздата»)"),
    "bhagavadgita-1914": ("https://rusneb.ru/catalog/000199_000009_004464084/",
                          "«Бхагавад-Гита или Песнь Господня … с английского и санскритского А. Каменской "
                          "и И. Манциарли. : Издание журнала Вестник Теософии, 1914. — 188 с.»"),
    "bhagavadgita-erman": ("https://www.labirint.ru/books/185770/",
                           "«Махабхарата. Книга шестая. Бхишмапарва» · пер. В. Г. Эрмана · Ладомир, 2009 · "
                           "серия «Литературные памятники» (РАН; Ладомир–Наука)"),
    "bhagavadgita-radha": ("https://ivran.ru/anonsy?artid=4645",
                           "«Бхагавад-гита в традиции бенгальского вайшнавизма: в 3 т. Т. 1 / Пер., сост., "
                           "ред. Р.Т. Блиндерман. - М.: Золотой век, 2016» (chitai-gorod.ru/catalog/book/910164)"),
    "ram_iii": ("https://litpamyatniki.ru/library/552",
                "«Рамаяна. Книга третья: Араньяканда (Книга о лесе) / Изд. подготовил П.А. Гринцер»"),
}

SPHERE_CARDS = [
    {"id": "sphere-rigveda", "slugs": [f"{i:02d}_rigveda" for i in range(1, 11)],
     "title": "sphere — Ригведа I–X (Елизаренкова)",
     "proposal": "художественная",
     "why": ("Hymn poetry translated as literature in the «Литературные памятники» series with a "
             "philological apparatus; not a confessional edition. The alternative is "
             "«нехудожественная: церковно-богословская» because the hymns are liturgical texts."),
     "sources": ["https://ru.wikipedia.org/wiki/%D0%A0%D0%B8%D0%B3%D0%B2%D0%B5%D0%B4%D0%B0"]},
    {"id": "sphere-gita-literary", "slugs": ["bhagavadgita-smirnov", "bhagavadgita-sementsov",
                                             "bhagavadgita-erman", "bhagavadgita-burba"],
     "title": "sphere — Гита: Смирнов, Семенцов, Эрман, Бурба",
     "proposal": "художественная",
     "why": ("Academic or literary translations straight from Sanskrit, published outside any "
             "religious organisation (Ылым / Восточная литература / Ладомир–Наука / РИПОЛ классик). "
             "Бурба was re-checked on 23-09 as a literary translation with word-by-word grammar, so "
             "it moved here from the confessional group."),
     "sources": ["https://search.rsl.ru/ru/record/01001265302", "https://www.labirint.ru/books/185770/",
                 "https://archive.org/details/bkhagavad-gita-burba"]},
    {"id": "sphere-gita-confessional", "slugs": ["bhagavadgita-1788", "bhagavadgita-1909",
                                                 "bhagavadgita-1914", "bhagavadgita-prabhupada",
                                                 "bhagavadgita-radha", "bhagavadgita-sharma"],
     "title": "sphere — Гита: 1788, 1909, 1914, Прабхупада, Сарартха-варшини, Шарма",
     "proposal": "нехудожественная: церковно-богословская",
     "why": ("Religious-teaching editions: 1788 from Novikov's circle via Wilkins' English, "
             "1909 and 1914 theosophical, Prabhupāda ISKCON, the 2016 Gauḍīya commentary edition and "
             "Шарма's yogic commentary. The weakest member is 1788, which is also an Enlightenment "
             "literary monument; reject if you want it in художественная."),
     "sources": ["http://bhagavadgita.ru/",
                 "https://vasudeva.ru/raznoe/stati/podvig-samizdata-bhagavad-gita-kak-ona-est-1984"]},
]


def esc(s):
    return html.escape(str(s or "—"), quote=True)


def fields_table(rows):
    head = "<tr><th>slug</th><th>translator</th><th>date_trans</th><th>publisher</th><th>sphere</th></tr>"
    body = "".join(f"<tr><td>{esc(s)}</td><td>{esc(b['translator'])}</td><td>{esc(b['date_trans'])}</td>"
                   f"<td>{esc(b['publisher'])}</td><td>{esc(b['sphere'])}</td></tr>" for s, b in rows)
    return f"<table>{head}{body}</table>"


def links(urls):
    return " · ".join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(u[:60])}</a>' for u in urls)


def main():
    bib = json.load(open(BIB, encoding="utf-8"))["sources"]
    items, stamp = [], {}
    for c in SPHERE_CARDS:
        rows = [(s, bib[s]) for s in c["slugs"]]
        items.append({
            "id": c["id"], "filt": "sphere", "title": c["title"],
            "badges": ["sphere", f"{len(rows)} texts", f"предложение: {c['proposal']}"],
            "question": (f"<p>Какую сферу НКРЯ поставить этим текстам? Агент предлагает "
                         f"<b>{esc(c['proposal'])}</b>.</p><p>✅ = согласен · ❌ = другая сфера "
                         "(напишите какую) · ⏸ = спросить НКРЯ.</p>"),
            "panels": [("Evidence — agent position", f"<p>{esc(c['why'])}</p><p>{links(c['sources'])}</p>"),
                       ("Rows affected", fields_table(rows))],
            "note_placeholder": "Если сфера другая — впишите её (и для каких текстов).",
        })
        stamp[c["id"]] = {"verifier": VERIFIER, "method": "primary_source_quote",
                          "sources": c["sources"], "verified_date": GENERATED}

    picked = sorted(random.Random(SEED).sample(sorted(RECORDS), SPOT_N))
    for rec in picked:
        slug = RECORDS[rec]
        b = bib[slug]
        url, quote = SPOT_EVIDENCE[rec]
        cid = f"spot-{rec}"
        items.append({
            "id": cid, "filt": "spot", "title": f"spot-check — {b['headers_all']} ({b['translator']}, {b['date_trans']})",
            "badges": ["spot-check", f"seed {SEED}", "agent: верно"],
            "question": ("<p>Верны ли переводчик, год перевода и издательство в этой строке? "
                         "Агент сверил строку с источником ниже и считает её верной.</p>"
                         "<p>✅ = верно · ❌ = ошибка (впишите правильное) · ⏸ = не знаю.</p>"),
            "panels": [("Evidence — source quote (verified 23-09-2026)",
                        f"<p>{esc(quote)}</p><p>{links([url])}</p>"),
                       ("Row as filled", fields_table([(slug, b)]) +
                        f"<p>edition: {esc(b['edition'])}</p><p>doubt: {esc(b.get('doubt'))}</p>")],
            "note_placeholder": "Если строка неверна — впишите правильные данные.",
        })
        stamp[cid] = {"verifier": VERIFIER, "method": "primary_source_quote",
                      "sources": [url], "verified_date": GENERATED}

    cfg = {
        "sheet_id": SHEET_ID,
        "title": "НКРЯ showcase: sphere + bibliography spot-check (H5281)",
        "subtitle": (f"{len(items)} cards · ~5 min · 3 sphere proposals + {SPOT_N} random rows "
                     f"(seed {SEED}) of the 16 filled bibliographic records."),
        "footer": ("Approve = the agent's proposal / filled row is right. Reject = wrong — write the "
                   "correction in the note. Defer = ask НКРЯ / unknown. Verdicts fold into "
                   "web/corpus_builder/nkrya_showcase_bib.json and the showcase package."),
        "approve_label": "✅ верно", "reject_label": "❌ неверно",
        "filters": [("sphere", "sphere"), ("spot", "spot-check")],
        "generated": GENERATED, "show_ids": True, "note_min_height_px": 60,
        "save_as": r"SamudraManthanam\review\%s_decisions.json" % SHEET_ID,
        "preflight": {"allow_slp1_tokens": ["confessional"]},  # English word, not SLP1
    }
    screening = {"deterministic": 0, "lookup": SPOT_N, "agent": 0, "human": len(items),
                 "evidence_path": "web/corpus_builder/nkrya_showcase_bib.json", "rules": []}
    manifest = EvidenceManifest(SHEET_ID, [i["id"] for i in items], repo_root=REPO)
    manifest.declare_joined("web/corpus_builder/nkrya_showcase_bib.json",
                            ["translator", "date_trans", "publisher", "sphere", "edition", "doubt", "evidence"])
    manifest.declare_omitted("nkrya-parallel/export/showcase/MANIFEST.tsv",
                             "generated from the same bibliography by build_nkrya_showcase_package.py")
    for i in items:
        manifest.add_card(i["id"], ["translator", "date_trans", "publisher", "sphere"])
    out = render_review_sheet(items, cfg, screening=screening, manifest=manifest)
    out = out.replace("</body>", f"<!-- ssb-evidence: {json.dumps(stamp, ensure_ascii=False)} -->\n</body>", 1)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    with open(SHEET, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"{len(items)} cards ({', '.join(picked)}) -> {os.path.relpath(SHEET, REPO)}")


if __name__ == "__main__":
    main()
