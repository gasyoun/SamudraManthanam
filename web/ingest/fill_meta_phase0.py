"""Phase 0 hygiene pass (H231): fill title_en / provenance / rights on the 148
active corpus meta.json files. Does not touch the 4 un-ingested dharmasastra
texts (naradasmriti, vishnu-smriti, yajnavalkyasmriti, yajnavalkyasmriti_add —
see .ai_state.md "DECISION NEEDED").

Re-runnable: edits are driven entirely by the tables below, keyed by slug.
Existing title_en/provenance/rights values are overwritten each run so the
tables are the single source of truth; needs_review is recomputed from
whether provenance is a real source or an honest TBD placeholder.

Usage:
    python web/ingest/fill_meta_phase0.py --corpus-path Index/lib/x86_64-win64/Data
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

OUT_OF_SCOPE = {
    "naradasmriti",
    "vishnu-smriti",
    "yajnavalkyasmriti",
    "yajnavalkyasmriti_add",
}

# English/IAST titles, hand-reviewed per slug. Sanskrit work names use the
# common English form for the ~10 well-known epics/vedas (Rigveda,
# Atharvaveda, Mahabharata, Ramayana, Bhagavad Gita, Upanishad) and IAST
# diacritics for specific parva/kanda/text names, per SHARED_CODE.md sanskrit-util
# convention.

RIGVEDA_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
RIGVEDA_YEAR = [1989, 1989, 1989, 1989, 1999, 1999, 1999, 1999, 1999, 1999]

TITLE_EN = {}

for i, (roman, year) in enumerate(zip(RIGVEDA_ROMAN, RIGVEDA_YEAR), start=1):
    TITLE_EN[f"{i:02d}_rigveda"] = f"Rigveda, Maṇḍala {roman} (Elizarenkova, {year})"

ATHARVAVEDA_YEAR = {
    1: 2005, 2: 2005, 3: 2005, 4: 2005, 5: 2005, 6: 2005, 7: 2005, 8: 2007,
    9: 2007, 10: 2007, 11: 2007, 12: 2007, 13: 2010, 14: 2010, 15: 2010,
    16: 2010, 17: 2010, 18: 2010, 19: 2010,
}
for book, year in ATHARVAVEDA_YEAR.items():
    TITLE_EN[f"{book:02d}_atharvaveda"] = f"Atharvaveda, Book {book} (Elizarenkova, {year})"

PARVA_EN = {
    "adiparva": "Ādiparva",
    "sabhaparva": "Sabhāparva",
    "aranyakaparva": "Āraṇyakaparva",
    "virataparva": "Virāṭaparva",
    "udyogaparva": "Udyogaparva",
    "bhishmaparva": "Bhīṣmaparva",
    "dronaparva": "Droṇaparva",
    "karnaparva": "Karṇaparva",
    "shalyaparva": "Śalyaparva",
    "sauptikaparva": "Sauptikaparva",
    "striparva": "Strīparva",
    "shantiparva": "Śāntiparva",
    "anushasanaparva": "Anuśāsanaparva",
    "ashvamedhikaparva": "Aśvamedhikaparva",
    "ashramavasikaparva": "Āśramavāsikaparva",
    "mausalaparva": "Mausalaparva",
    "mahaprasthanikaparva": "Mahāprasthānikaparva",
    "svargarohanikaparva": "Svargārohaṇikaparva",
}
MAHABHARATA_BOOKS = [
    (1, "adiparva", "Kalyanov", 1950),
    (2, "sabhaparva", "Kalyanov", 1962),
    (3, "aranyakaparva", "Vasilkov & Neveleva", 1987),
    (4, "virataparva", "Kalyanov", 1967),
    (5, "udyogaparva", "Kalyanov", 1976),
    (6, "bhishmaparva", "Erman", 2009),
    (7, "dronaparva", "Kalyanov", 1993),
    (8, "karnaparva", "Vasilkov & Neveleva", 1990),
    (9, "shalyaparva", "Kalyanov", 1996),
    (10, "sauptikaparva", "Vasilkov & Neveleva", 1998),
    (11, "striparva", "Vasilkov & Neveleva", 1998),
    (12, "shantiparva", "Neveleva", 2017),
    (13, "anushasanaparva", None, None),
    (14, "ashvamedhikaparva", "Vasilkov & Neveleva", 2003),
    (15, "ashramavasikaparva", "Vasilkov & Neveleva", 2005),
    (16, "mausalaparva", "Vasilkov & Neveleva", 2005),
    (17, "mahaprasthanikaparva", "Vasilkov & Neveleva", 2005),
    (18, "svargarohanikaparva", "Vasilkov & Neveleva", 2005),
]
ROMAN18 = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
           "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII"]
for book_num, parva_slug, translator, year in MAHABHARATA_BOOKS:
    roman = ROMAN18[book_num - 1]
    en_parva = PARVA_EN[parva_slug]
    slug = f"{book_num:02d}_mahabharata-{parva_slug}"
    if translator:
        TITLE_EN[slug] = f"Mahabharata, Book {roman} ({en_parva}) ({translator}, {year})"
    else:
        TITLE_EN[slug] = f"Mahabharata, Book {roman} ({en_parva}) — translator not stated"

TITLE_EN["kommentarii-k-makhabkharate"] = "Mahabharata, Book I — Commentary (Kalyanov, 1950)"
TITLE_EN["stati-makhabkharaty"] = "Mahabharata, Book I — Afterword (Barannikov, 1950)"
TITLE_EN["ukazateli-makhabkharaty"] = "Index to the Mahabharata (Kalyanov, Vasilkov, Neveleva & Erman, 1950–2009)"
TITLE_EN["slovar-smirnova"] = "Concordance Dictionary to the Mahabharata (Smirnov, 1955–1989)"

KANDA_EN = {
    "balakanda": "Bālakāṇḍa",
    "ayodhyakanda": "Ayodhyākāṇḍa",
    "aranyakanda": "Araṇyakāṇḍa",
    "sundarakanda": "Sundarakāṇḍa",
}
RAMAYANA_BOOKS = [
    (1, "balakanda", "Grintser", 2006, None),
    (2, "ayodhyakanda", "Grintser", 2006, None),
    (3, "aranyakanda", "Grintser", 2014, None),
    (5, "sundarakanda", "Leonov", 2022, "interlinear draft"),
]
RAMAYANA_ROMAN = {1: "I", 2: "II", 3: "III", 5: "V"}
for book_num, kanda_slug, translator, year, note in RAMAYANA_BOOKS:
    roman = RAMAYANA_ROMAN[book_num]
    en_kanda = KANDA_EN[kanda_slug]
    slug = f"{book_num:02d}_ramayana-{kanda_slug}"
    if note:
        TITLE_EN[slug] = f"Ramayana, Book {roman} ({en_kanda}), {note} (Leonov, {year})"
    else:
        TITLE_EN[slug] = f"Ramayana, Book {roman} ({en_kanda}) ({translator}, {year})"

TITLE_EN["ramayana-3-slovar"] = "Index of Names and Place-Names to the Ramayana, Book III (Grintser, 2006)"
TITLE_EN["slovar-grintsera-iz-bada-kadambari"] = "Index of Names, Terms and Titles from Bāṇa's Kādambarī (Grintser, 1995)"
TITLE_EN["slovar-grintsera-iz-ramayany-1-2"] = "Index to the Ramayana, Books I–II (Grintser, 2006)"
TITLE_EN["slovar-potapovoy"] = "Index to the Ramayana (Zakharyin & Potapova, 1986)"

UP_EN = {
    "ait-up": ("Aitareya", 1992, False),
    "atma-up": ("Ātma", 1992, False),
    "br-up": ("Bṛhadāraṇyaka", 1992, False),
    "brb-up": ("Brahmabindu", 1992, False),
    "ch-up": ("Chāndogya", 1992, False),
    "chag-up": ("Chāgaleya", 1992, True),
    "isha-up": ("Īśa", 1992, False),
    "jab-up": ("Jābāla", 1992, True),
    "kai-up": ("Kaivalya", 1992, False),
    "kan-up": ("Kaṇṭaśruti", 1992, True),
    "kat-up": ("Kaṭha", 1992, False),
    "kau-up": ("Kauṣītaki", 1992, False),
    "kena-up": ("Kena", 1992, False),
    "mai-up": ("Maitrī", 1992, False),
    "man-up": ("Māṇḍūkya", 1992, False),
    "mnar-up": ("Mahānārāyaṇa", 1992, True),
    "mun-up": ("Muṇḍaka", 1992, False),
    "nr-up": ("Nīlarudra", 1992, True),
    "pai-up": ("Paiṅgala", 1992, True),
    "pr-up": ("Praśna", 1992, False),
    "rampt-up": ("Rāmapūrvatāpanīya", 1992, True),
    "shv-up": ("Śvetāśvatara", 1992, False),
    "sub-up": ("Subāla", 1992, True),
    "tai-up": ("Taittirīya", 1992, False),
    "vajs-up": ("Vajrasūcika", 1992, False),
}
for slug, (en_name, year, excerpt) in UP_EN.items():
    if excerpt:
        TITLE_EN[slug] = f"{en_name} Upaniṣad (excerpt; transl. Syrkin, {year})"
    else:
        TITLE_EN[slug] = f"{en_name} Upaniṣad (transl. Syrkin, {year})"

TITLE_EN["yotat-up"] = "Yogatattva Upaniṣad (transl. Martynov, 1992)"
TITLE_EN["jabala-up"] = "Jābāla Upaniṣad (transl. Tolchelnikov, Ishimbaev, Kochergin & Shirobokov, 2025)"

TITLE_EN.update({
    "biruni": "Abū Rayhān al-Bīrūnī, India (transl. Khalidov, Zavadovsky & Erman, 1995)",
    "dic_mw": "A Sanskrit-English Dictionary (Monier-Williams, 1899)",
    "kewa": "KEWA: A Concise Etymological Sanskrit Dictionary (Mayrhofer, 1953–1980)",
    "mify_759_ind": "Myths of the Peoples of the World: Encyclopedia, 2 vols. (ed. Tokarev, 1987–1988)",
    "amaru-shataka": "Amaruśataka (Leonov, 2022)",
    "bhagavadgita-1788": "Bhagavad Gita [Baguat-Geta, first Russian translation] (Petrov, 1788; repr. 1914)",
    "bhagavadgita-1909": "Bhagavad Gita, verse translation (Kaznacheeva, 1909)",
    "bhagavadgita-1914": "Bhagavad Gita (Kamenskaya & de Manziarly, 1914)",
    "bhagavadgita-burba": "Bhagavad Gita (Burba, 2009)",
    "bhagavadgita-erman": "Bhagavad Gita (Erman, 2009)",
    "bhagavadgita-prabhupada": "Bhagavad Gita As It Is (A.C. Bhaktivedanta Swami Prabhupada, 1984)",
    "bhagavadgita-radha": "Bhagavad Gita (Blinderman, 2016)",
    "bhagavadgita-sementsov": "Bhagavad Gita (Sementsov, 1999)",
    "bhagavadgita-sharma": "Shrimad Bhagavad Gita (Shailendra Sharma, 2015)",
    "bhagavadgita-smirnov": "Bhagavad Gita (Smirnov, 1977)",
    "bhagavadgity": "Bhagavad Gita — Anthology of Translations (1788–2016)",
    "buddhacharita-balmont": "Aśvaghoṣa, Buddhacarita (transl. Balmont, 1913)",
    "buddhacharita": "Aśvaghoṣa, Buddhacarita (Leonov, 2023)",
    "chaurapanchashika": "Bilhaṇa, Caurapañcāśikā (Leonov, 2020)",
    "devi-gita": "Devī Gītā (Ignatiev, 2005)",
    "dic_apte": "The Practical Sanskrit-English Dictionary (Apte, Vaman Shivaram, 1890)",
    "dsg": "A Dictionary of Sanskrit Grammar (Abhyankar, Kashinath Vasudev, 1961)",
    "fasmer-dr-ind": "Etymological Dictionary of the Russian Language (Vasmer, 1964–1973)",
    "gitagovinda": "Jayadeva, Gītagovinda (Syrkin, 2020)",
    "gitartha-samgraha_yamunacharya": "Yāmunācārya, Gītārthasaṃgraha (Pskhu, 2021)",
    "gitarthasamgraha-abhinavagupta": "Abhinavagupta, Gītārthasaṅgraha (Erchenkov, 2008)",
    "hatha-yoga-pradipika": "Haṭhayogapradīpikā (Shailendra Sharma, 2013)",
    "kama-sutra": "Vātsyāyana Mallanāga, Kāmasūtra (Syrkin, 2000)",
    "kumarasambhava": "Kālidāsa, Kumārasambhava (transl. Mikushevich, 1977)",
    "manavadharmashastra": "Mānavadharmaśāstra [Laws of Manu] (transl. Elmanovich, ed. Ilyin, 2002)",
    "megha-duta": "Kālidāsa, Meghadūta [Cloud Messenger] (transl. Ritter, 1914)",
    "mify-drind": "Myths of Ancient India (Temkin & Erman, 1982)",
    "nyaya-bhashya": "Nyāyasūtra & Nyāyabhāṣya (transl. Shokhin, 2001)",
    "pandey": "R.B. Pandey, Ancient Indian Domestic Rites (transl. from English by Vigasin, 1990)",
    "paramarthasara-abhinavagupta": "Abhinavagupta, Paramārthasāra (transl. Isaeva, 2014)",
    "pratyabhijna-hridaya_kshemaraja": "Kṣemarāja, Pratyabhijñāhṛdaya (transl. Isaeva, 2014)",
    "raghuvamsha": "Kālidāsa, Raghuvaṃśa [The Dynasty of Raghu] (transl. Erman, 1996)",
    "ramanuja_gitabhashya": "Rāmānuja, Gītābhāṣya (transl. Sementsov, 2021)",
    "sankhya-karika": "Īśvarakṛṣṇa, Sāṃkhyakārikā (transl. Shokhin, 1995)",
    "shatakatrayam-serebryakov": "Bhartṛhari, Śatakatraya (transl. Serebryakov, 1979)",
    "shatakatrayam": "Bhartṛhari, Śatakatraya (transl. Leonov, 2020)",
    "shiva-sutry_sharma": "Śivasūtra (transl. Shailendra Sharma [Skt.] & M. Nikolaeva [Eng.], 2007)",
    "shukasaptati": "Śukasaptati (transl. Shiryaev, 1960)",
    "toporov": "Articles for Mythological Encyclopedias (Toporov, 2014)",
    "vedanga_jyotisha": "Vedāṅgajyotiṣa (transl. Shirobokov, 2025)",
    "vedartha-samgraha_ramanuja": "Rāmānuja, Vedārthasaṃgraha (transl. Pskhu, 2007)",
    "warnemyr": "The Roots, Verb-Forms and Primary Derivatives of the Sanskrit Language (Whitney, 1885)",
    "yoga-sutry": "Yogasūtra — 11 Translations (various translators)",
    "yoga-sutry_sharma": "Yogasūtra (transl. Shailendra Sharma, 2007)",
    "yoga-sutry_vyasa-bhashya": "Vyāsabhāṣya [on the Yogasūtra] (transl. Ostrovskaya & Rudoy, 1992)",
    "yoga-sutry_zagumennov": "Patañjali, Yogasūtra (transl. Zagumennov, 1991)",
    "vishnu-purana": "Viṣṇu Purāṇa, Book I (transl. Posova, 1995)",
    "iliada_gnedich": "Homer, Iliad (transl. Gnedich, 1829)",
    "induizm-dzhaynizm-sikkhizm": "Hinduism. Jainism. Sikhism: Dictionary (Albedil & Dubyansky, 1996)",
    "yoga-bessmertie-i-cvoboda-mircha-eliade-per-pakhomova": "Mircea Eliade, Yoga: Immortality and Freedom (transl. Pakhomov, 1999)",
    "knauer": "Textbook of the Sanskrit Language (Knauer, 1908)",
    "kossovich": "Sanskrit-Russian Dictionary (Kossovich, 1854)",
    "kochergina": "Sanskrit-Russian Dictionary (Kochergina, 1987)",
    "stepanyants": "Indian Philosophy: Encyclopedia (ed. Stepanyants, 2009)",
    "syrkin_tom_1_utf": "Selected Works, Vol. 1 (Syrkin)",
    "frish": "Frish, Sanskrit Chrestomathy, Vol. II: Dictionary (1956)",
    "erman-temkin": "Dictionary of Indian Names and Terms (Temkin & Erman, 1996)",
})


def compute_rights(year: int | None) -> str:
    """Honest classification, never a fabricated licence.

    Locked project ruling (.ai_state.md "Decisions locked"): corpus rights
    stay grey overall (no open dumps/DOI) — this only distinguishes a
    pre-1929 edition (translator/author long deceased, safely out of term)
    from a modern in-copyright academic edition.
    """
    if year is not None and year <= 1929:
        return "public domain (pre-1929 edition; translator/author long deceased)"
    return ("in-copyright academic edition (named translator/editor, 20th-21st c.) "
            "— corpus rights stay grey per project ruling; no redistribution")


def compute_provenance(imprint: str) -> str:
    """No digitization-source note exists anywhere in the source HTML
    (checked headers + footers) or repo docs, so an honest TBD is correct
    for every file rather than inventing an origin."""
    if imprint:
        return f"print edition: {imprint} — digital source TBD"
    return "print edition unknown — digital source TBD"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-path", required=True)
    args = parser.parse_args()

    corpus = Path(args.corpus_path)
    meta_files = sorted(corpus.glob("*.meta.json"))

    filled = missing_title = skipped_scope = 0
    for path in meta_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        slug = data["slug"]
        if slug in OUT_OF_SCOPE:
            skipped_scope += 1
            continue
        title_en = TITLE_EN.get(slug)
        if not title_en:
            print(f"MISSING title_en mapping for slug: {slug}", file=sys.stderr)
            missing_title += 1
            continue

        data["title_en"] = title_en
        data["provenance"] = compute_provenance(data.get("imprint", ""))
        data["rights"] = compute_rights(data.get("year"))
        # Provenance is an honest TBD for every file (no digitization source
        # is recorded anywhere), so needs_review stays true across the board.
        data["needs_review"] = True

        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        filled += 1

    print(f"filled: {filled}, out-of-scope skipped: {skipped_scope}, "
          f"missing title_en mapping: {missing_title}")
    return 1 if missing_title else 0


if __name__ == "__main__":
    sys.exit(main())
