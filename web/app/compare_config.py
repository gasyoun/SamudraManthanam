"""Configuration for /compare/{work}/{ch}.{v} multi-translation comparison pages.

Each work groups several corpus sources that share a `{chapter}.{verse}` link_id
scheme. The route fetches the same verse across all listed sources for
side-by-side display.

`bridges` handles cases where the same verse appears in a parent work under a
different chapter numbering — e.g. Bhagavadgītā chapter 1 = Mahābhārata
Bhīṣma-parvan adhyāya 23 in Erman's edition. `chapter_offset=22` means
"to find Gītā chapter X in this bridged source, look up link_id (X+22).Y"
with range-merge fallback applied as usual.

Verse-count discrepancies (some translations merge stanzas into blocks like
"1.3-6") are handled by the range-fallback in compare_service._fetch_verse.

Sources are listed in the order they should appear on the page — generally
chronological by first publication, with commentaries and bridges at the end.
"""

WORKS = {
    "bhagavadgita": {
        "title": "Бхагавадгита",
        "title_iast": "Bhagavadgītā",
        "description": (
            "Сравнение русских переводов и санскритских комментариев "
            "«Бхагавадгиты» — стих за стихом."
        ),
        "chapter_count": 18,
        "sources": [
            {"filename": "bhagavadgita-1788.html",       "label": "Петров 1788",                       "role": "translation"},
            {"filename": "bhagavadgita-1909.html",       "label": "Казначеева 1909",                   "role": "translation"},
            {"filename": "bhagavadgita-1914.html",       "label": "Каменская и де Манциарли 1914",     "role": "translation"},
            {"filename": "bhagavadgita-smirnov.html",    "label": "Смирнов 1977",                      "role": "translation"},
            {"filename": "bhagavadgita-prabhupada.html", "label": "Прабхупада 1984",                   "role": "translation"},
            {"filename": "bhagavadgita-sementsov.html",  "label": "Семенцов 1999",                     "role": "translation"},
            {"filename": "bhagavadgita-erman.html",      "label": "Эрман 2009",                        "role": "translation"},
            {"filename": "bhagavadgita-burba.html",      "label": "Бурба 2009",                        "role": "translation"},
            {"filename": "bhagavadgita-sharma.html",     "label": "Шри Шарма 2015",                    "role": "translation"},
            {"filename": "bhagavadgita-radha.html",      "label": "Блиндерман 2016",                   "role": "translation"},
            {"filename": "bhagavadgity.html",            "label": "Сборник переводов 1788–2016",       "role": "anthology"},
            {"filename": "ramanuja_gitabhashya.html",            "label": "Рамануджа. Гитабхашья",         "role": "commentary"},
            {"filename": "gitarthasamgraha-abhinavagupta.html",  "label": "Абхинавагупта. Гитартхасанграха", "role": "commentary"},
        ],
        "bridges": [
            {
                "filename": "06_mahabharata-bhishmaparva.html",
                "label": "Махабхарата VI (Эрман) — контекст",
                "role": "context",
                "chapter_offset": 22,
            },
        ],
    },
    "yogasutra": {
        "title": "Йога-сутры",
        "title_iast": "Yoga-Sūtra",
        "description": "Сравнение русских переводов «Йога-сутр» Патанджали — сутра за сутрой.",
        "chapter_count": 4,
        "sources": [
            {"filename": "yoga-sutry_zagumennov.html",   "label": "Загуменнов 1991",                  "role": "translation"},
            {"filename": "yoga-sutry_vyasa-bhashya.html","label": "Островская и Рудой 1992 (с Вьяса-бхашьей)", "role": "translation"},
            {"filename": "yoga-sutry_sharma.html",       "label": "Шри Шайлендра Шарма 2007",         "role": "translation"},
            {"filename": "yoga-sutry.html",              "label": "11 переводов (сборник)",            "role": "anthology"},
        ],
        "bridges": [],
    },
    "shatakatrayam": {
        "title": "Шатакатраям",
        "title_iast": "Śatakatraya",
        "description": "Сравнение русских переводов «Шатакатраи» Бхартрихари — стих за стихом.",
        "chapter_count": 3,
        "sources": [
            {"filename": "shatakatrayam-serebryakov.html", "label": "Серебряков 1979", "role": "translation"},
            {"filename": "shatakatrayam.html",             "label": "Леонов 2020",      "role": "translation"},
        ],
        "bridges": [],
    },
}
