"""Registry for `/q/{slug}` popular-query landing pages.

Each entry is a curated high-intent Russian-language Sanskrit-studies query
that gets its own SEO landing page: short definition, 20 example verses
from the corpus, related-term cross-links.

The slug is the URL key (ASCII, lowercased). Russian users search for the
Cyrillic form; we just use the IAST transliteration as the slug because
percent-encoded Cyrillic URLs are ugly and harder to copy/paste.

`search_query` overrides the default search term. For Russian terms this
is usually the morphological root with no inflection ending — e.g. "дхарм"
matches "дхарма", "дхармы", "дхарме", "дхарму" via FTS5 prefix search.

`related` lists other slugs in this registry; the template renders them as
clickable cross-links at the bottom of the page. Entries should be
bidirectional in spirit but the code doesn't enforce it (validated in a
test instead).

Definitions are intentionally minimal — one neutral sentence each, no
theological commentary. Some entries omit them entirely; the template
handles that gracefully.
"""

# Concept terms (tier 1): high search volume, evergreen interest.
# Proper nouns (tier 2) follow.
POPULAR_TERMS: dict[str, dict] = {
    "dharma": {
        "term": "дхарма",
        "iast": "dharma",
        "devanagari": "धर्म",
        "definition": "Фундаментальное понятие индийской философии: закон, нравственный долг, истинный путь.",
        "search_query": "дхарм",
        "related": ["karma", "moksha", "varna", "ashrama"],
    },
    "karma": {
        "term": "карма",
        "iast": "karma",
        "devanagari": "कर्म",
        "definition": "Действие и его последствие; универсальный закон причинности, связывающий деяния и судьбу.",
        "search_query": "карм",
        "related": ["dharma", "moksha", "samsara"],
    },
    "atman": {
        "term": "атман",
        "iast": "ātman",
        "devanagari": "आत्मन्",
        "definition": "Индивидуальное «я», истинная самость, душа — одно из центральных понятий упанишад.",
        "search_query": "атман",
        "related": ["brahman", "moksha", "purusha"],
    },
    "brahman": {
        "term": "брахман",
        "iast": "brahman",
        "devanagari": "ब्रह्मन्",
        "definition": "Абсолют, высшая реальность, безличная основа всего сущего.",
        "search_query": "брахман",
        "related": ["atman", "moksha", "vedas"],
    },
    "moksha": {
        "term": "мокша",
        "iast": "mokṣa",
        "devanagari": "मोक्ष",
        "definition": "Освобождение от сансары — высшая цель духовной жизни в индуизме.",
        "search_query": "мокш",
        "related": ["samsara", "nirvana", "karma", "atman"],
    },
    "samsara": {
        "term": "сансара",
        "iast": "saṃsāra",
        "devanagari": "संसार",
        "definition": "Круговорот рождений и смертей, цикл перевоплощений.",
        "search_query": "сансар",
        "related": ["karma", "moksha", "nirvana"],
    },
    "yoga": {
        "term": "йога",
        "iast": "yoga",
        "devanagari": "योग",
        "definition": "Психофизическая дисциплина соединения индивидуального духа с абсолютом; одна из шести даршан.",
        "search_query": "йог",
        "related": ["dhyana", "bhakti", "moksha"],
    },
    "bhakti": {
        "term": "бхакти",
        "iast": "bhakti",
        "devanagari": "भक्ति",
        "definition": "Любовная преданность личному божеству как путь освобождения.",
        "search_query": "бхакти",
        "related": ["krishna", "yoga", "moksha"],
    },
    "nirvana": {
        "term": "нирвана",
        "iast": "nirvāṇa",
        "devanagari": "निर्वाण",
        "definition": "«Угасание» — освобождение от страданий и круга перерождений, особенно в буддийской традиции.",
        "search_query": "нирван",
        "related": ["moksha", "samsara"],
    },
    "avatara": {
        "term": "аватара",
        "iast": "avatāra",
        "devanagari": "अवतार",
        "definition": "Нисхождение божества в мир в телесном облике.",
        "search_query": "аватар",
        "related": ["krishna", "vishnu", "rama"],
    },
    "guna": {
        "term": "гуна",
        "iast": "guṇa",
        "devanagari": "गुण",
        "definition": "Качество, свойство; в санкхье — три первоначала природы: саттва, раджас, тамас.",
        "search_query": "гун",
        "related": ["dharma", "varna"],
    },
    "om": {
        "term": "ом",
        "iast": "oṃ",
        "devanagari": "ॐ",
        "definition": "Священный слог-мантра, символ абсолюта.",
        "search_query": "ом",
        "related": ["mantra", "brahman", "vedas"],
    },
    "mantra": {
        "term": "мантра",
        "iast": "mantra",
        "devanagari": "मन्त्र",
        "definition": "Священная формула или гимн, повторение которого имеет ритуальное и духовное значение.",
        "search_query": "мантр",
        "related": ["om", "vedas"],
    },
    "dhyana": {
        "term": "дхьяна",
        "iast": "dhyāna",
        "devanagari": "ध्यान",
        "definition": "Медитация, сосредоточенное созерцание; седьмая ступень классической йоги.",
        "search_query": "дхьян",
        "related": ["yoga", "moksha"],
    },
    "varna": {
        "term": "варна",
        "iast": "varṇa",
        "devanagari": "वर्ण",
        "definition": "Сословие в традиционном индийском обществе: брахманы, кшатрии, вайшьи, шудры.",
        "search_query": "варн",
        "related": ["dharma", "ashrama"],
    },
    "ashrama": {
        "term": "ашрама",
        "iast": "āśrama",
        "devanagari": "आश्रम",
        "definition": "Этап жизни в традиционной индийской системе: ученик, домохозяин, отшельник, странник.",
        "search_query": "ашрам",
        "related": ["dharma", "varna"],
    },
    "vedas": {
        "term": "веды",
        "iast": "veda",
        "devanagari": "वेद",
        "definition": "Древнейший пласт индийской священной литературы: Ригведа, Самаведа, Яджурведа, Атхарваведа.",
        "search_query": "вед",
        "related": ["upanishads", "brahman"],
    },
    "upanishads": {
        "term": "упанишады",
        "iast": "upaniṣad",
        "devanagari": "उपनिषद्",
        "definition": "Корпус философских текстов, завершающих ведийский канон.",
        "search_query": "упанишад",
        "related": ["vedas", "atman", "brahman"],
    },
    "purusha": {
        "term": "пуруша",
        "iast": "puruṣa",
        "devanagari": "पुरुष",
        "definition": "Дух, чистое сознание; в санкхье — пассивный мужской принцип, противоположный пракрити.",
        "search_query": "пуруш",
        "related": ["atman", "guna"],
    },

    # Proper nouns
    "krishna": {
        "term": "Кришна",
        "iast": "kṛṣṇa",
        "devanagari": "कृष्ण",
        "definition": "Божество индуизма, аватара Вишну, центральный персонаж «Бхагавадгиты».",
        "search_query": "Кришн",
        "related": ["arjuna", "vishnu", "avatara", "bhakti"],
    },
    "arjuna": {
        "term": "Арджуна",
        "iast": "arjuna",
        "devanagari": "अर्जुन",
        "definition": "Герой «Махабхараты», третий из братьев Пандавов, собеседник Кришны в «Бхагавадгите».",
        "search_query": "Арджун",
        "related": ["krishna", "dharma"],
    },
    "shiva": {
        "term": "Шива",
        "iast": "śiva",
        "devanagari": "शिव",
        "definition": "Одно из трёх главных божеств индуизма (вместе с Брахмой и Вишну).",
        "search_query": "Шив",
        "related": ["vishnu", "brahma"],
    },
    "vishnu": {
        "term": "Вишну",
        "iast": "viṣṇu",
        "devanagari": "विष्णु",
        "definition": "Одно из трёх главных божеств индуизма; хранитель мира.",
        "search_query": "Вишн",
        "related": ["shiva", "brahma", "krishna", "rama", "avatara"],
    },
    "brahma": {
        "term": "Брахма",
        "iast": "brahmā",
        "devanagari": "ब्रह्मा",
        "definition": "Бог-творец в индуистской триаде Тримурти.",
        "search_query": "Брахм",
        "related": ["vishnu", "shiva", "brahman"],
    },
    "rama": {
        "term": "Рама",
        "iast": "rāma",
        "devanagari": "राम",
        "definition": "Аватара Вишну, царевич Айодхьи, главный герой «Рамаяны».",
        "search_query": "Рам",
        "related": ["vishnu", "avatara"],
    },
    "indra": {
        "term": "Индра",
        "iast": "indra",
        "devanagari": "इन्द्र",
        "definition": "Верховное божество ведийского пантеона, царь богов, владыка грозы.",
        "search_query": "Индр",
        "related": ["vedas"],
    },
    "sarasvati": {
        "term": "Сарасвати",
        "iast": "sarasvatī",
        "devanagari": "सरस्वती",
        "definition": "Богиня знания, искусств и речи; супруга Брахмы.",
        "search_query": "Сарасват",
        "related": ["brahma", "vedas"],
    },
    "lakshmi": {
        "term": "Лакшми",
        "iast": "lakṣmī",
        "devanagari": "लक्ष्मी",
        "definition": "Богиня процветания и счастья; супруга Вишну.",
        "search_query": "Лакшм",
        "related": ["vishnu"],
    },
    "hanuman": {
        "term": "Хануман",
        "iast": "hanumat",
        "devanagari": "हनुमत्",
        "definition": "Обезьяноподобный воитель из «Рамаяны», верный спутник Рамы.",
        "search_query": "Хануман",
        "related": ["rama"],
    },
    "ganesha": {
        "term": "Ганеша",
        "iast": "gaṇeśa",
        "devanagari": "गणेश",
        "definition": "Слоноголовое божество, устранитель препятствий, сын Шивы и Парвати.",
        "search_query": "Ганеш",
        "related": ["shiva"],
    },
}


def get_term(slug: str) -> dict | None:
    """Case-insensitive lookup. Returns the entry or None."""
    return POPULAR_TERMS.get(slug.lower())


# Reference works (dictionaries, lexicons, glossaries, textbooks) that occupy
# top sort_order slots and otherwise dominate landing-page result sets. Excluded
# from `/q/{slug}` searches so example verses come from primary texts —
# Bhagavadgītā, Mahābhārata, Upaniṣads etc. — instead of dictionary glosses.
# Dictionary look-up remains useful but isn't what an SEO landing page should
# foreground.
REFERENCE_WORK_FILENAMES: frozenset[str] = frozenset({
    # Sanskrit/Russian dictionaries and lexicons
    "Словарь Смирнова.txt",
    "Кнауэр.txt",
    "Коссович.txt",
    "Фриш.txt",
    "Кочергина.txt",
    "Dic_MW.txt",
    "Dic_Apte.txt",
    "KEWA.txt",
    "dsg.txt",
    "fasmer-dr-ind.htm",
    # Per-work indexes/glossaries
    "Словарь Потаповой.txt",
    "Словарь Гринцера из Рамаяны 1-2.txt",
    "Рамаяна 3. Словарь.txt",
    "Словарь Гринцера из Бада Кадамбари.txt",
    "Эрман-Темкин.txt",
    # Encyclopedias and mythology compendia
    "Индуизм. Джайнизм. Сикхизм.txt",
    "Степанянц.txt",
    "Топоров.txt",
    "Mify_759_ind.html",
    "mify-drind.html",
})
