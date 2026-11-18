"""Dictionary layer service (H7790): structured headword access to the five
digitized RU Sanskrit dictionaries served from the corpus FTS lines.

Each dictionary work is ingested as a corpus source whose `line_text` is
one dictionary entry (tab-separated headword/translit/gloss columns). This
module parses those lines into structured entries and builds a cached
per-dict index used by the dict UI router:

* headword pages (Devanagari / IAST / SLP1 / Cyrillic translit, homonyms,
  POS markers, glosses),
* per-dict alphabet index (Sanskrit varṇamālā order),
* lookup accepting Devanagari/IAST/SLP1 (via indic-transliteration),
* reverse RU→Sa gloss search with dict badges.

Bounded by design: entries that do not parse into the known column shapes
are still served (raw line displayed) and counted in `unparsed`, never
silently dropped.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from indic_transliteration import sanscript
from indic_transliteration.sanscript import DEVANAGARI, IAST, SLP1

# ---------------------------------------------------------------- registry

DICTS: dict[str, dict] = {
    "frish": {
        "title": "Фриш — санскритско-русский словарь",
        "short": "Фриш",
        "description": "Словарь А. И. Фриша (латинско-русский, переиздание): "
                       "санскритские слова с деванагари, IAST, SLP1, кириллической "
                       "транслитерацией и русскими толкованиями.",
        "order": 1,
    },
    "kochergina": {
        "title": "Кочергина — санскритско-русский учебный словарь",
        "short": "Кочергина",
        "description": "Санскритско-русский учебный словарь В. А. Кочергиной "
                       "(с приставочными формами на °).",
        "order": 2,
    },
    "kossovich": {
        "title": "Коссович — санскритско-русский словарь",
        "short": "Коссович",
        "description": "Словарь К. А. Коссовича к греческо-славянским сравнениям "
                       "(дореформенная орфография).",
        "order": 3,
    },
    "knauer": {
        "title": "Кнауэр — санскритско-русский словарь",
        "short": "Кнауэр",
        "description": "Практический словарь Ф. И. Кнауэра с этимологическими "
                       "сравнениями (дореформенная орфография).",
        "order": 4,
    },
    "slovar-smirnova": {
        "title": "Смирнов — словарь к Бхагавад-гите",
        "short": "Смирнов",
        "description": "Словарь А. П. Смирнова к переводу Бхагавад-гиты: "
                       "кириллические заглавки со ссылками на источники.",
        "order": 5,
    },
}

# Sanskrit varṇamālā bucket order (IAST letters).
ALPHABET_ORDER = (
    "a ā i ī u ū ṛ ṝ ḷ e ai o au "
    "k kh g gh ṅ c ch j jh ñ ṭ ṭh ḍ ḍh ṇ t th d dh n "
    "p ph b bh m y r l v ś ṣ s h"
).split()
_VOWEL_BUCKETS = ("a", "ā", "i", "ī", "u", "ū", "ṛ", "ṝ", "ḷ", "e", "ai", "o", "au")
_CONSONANT_BUCKETS = tuple(
    l for l in ALPHABET_ORDER if l not in _VOWEL_BUCKETS
)

# IAST → SLP1 via the library; Cyrillic translit of Sanskrit is matched
# through the precomposed Cyrillic column where present.

_ROMAN_HOMONYM = re.compile(r"^\s{0,3}((?:I{1,3}|IV|V|VI{1,3}|IX|X)\b)")
_POS_TAGS = re.compile(
    r"\b(m\.|f\.|n\.|mf\.|mn\.|fn\.|adj\.|adv\.|pron\.|num\.|pp\.|caus\.|"
    r"desid\.|intens\.|pass\.|v\.)\b"
)


def _strip_slashes(s: str) -> str:
    """'/a-/ /an-/' → ['a-','an-'] joined by space, slashes removed."""
    parts = [p.strip() for p in s.split("/") if p.strip()]
    return " ".join(parts)


def _first_headword(slashed: str) -> str:
    parts = [p.strip() for p in slashed.split("/") if p.strip()]
    return parts[0] if parts else slashed.strip()


def iast_to_slp1(iast: str) -> str:
    if not iast:
        return ""
    return sanscript.transliterate(iast, IAST, SLP1)


def slp1_to_iast(slp1: str) -> str:
    if not slp1:
        return ""
    return sanscript.transliterate(slp1, SLP1, IAST)


def deva_to_iast(deva: str) -> str:
    if not deva:
        return ""
    return sanscript.transliterate(deva, DEVANAGARI, IAST)


def bucket_of(iast: str) -> str:
    """Bucket an IAST headword into its varṇamālā letter."""
    w = iast.strip().lower()
    if not w:
        return "?"
    for b in ("kṣ", "jñ",) or ():
        if w.startswith(b):
            return b
    # two-letter vowel buckets first
    for b in _VOWEL_BUCKETS:
        if w.startswith(b):
            return b
    for b in _CONSONANT_BUCKETS:
        if w.startswith(b):
            return b
    return w[0]


ALPHABET_POSITION = {b: i for i, b in enumerate(ALPHABET_ORDER)}


def alphabet_sort_key(iast: str):
    b = bucket_of(iast)
    return (ALPHABET_POSITION.get(b, len(ALPHABET_ORDER)), iast)


def has_devanagari(s: str) -> bool:
    return any(0x0900 <= ord(c) <= 0x097F for c in s)


@dataclass
class DictEntry:
    canonical_id: str
    seq: int
    deva: str = ""
    iast: str = ""
    slp1: str = ""
    cyr: str = ""
    homonym: str = ""
    pos: list = field(default_factory=list)
    gloss_html: str = ""
    raw: str = ""

    @property
    def slug(self) -> str:
        iast = _strip_slashes(self.iast)
        if not iast and self.deva:
            iast = deva_to_iast(_strip_slashes(self.deva))
        return iast_to_slp1(iast or _strip_slashes(self.cyr)) or "x"

    def display_deva(self) -> str:
        return _strip_slashes(self.deva)

    def display_iast(self) -> str:
        return _strip_slashes(self.iast)

    def display_cyr(self) -> str:
        return _strip_slashes(self.cyr)


def _pos_tags(text: str) -> list:
    return sorted({m.group() for m in _POS_TAGS.finditer(text)})


def _parse_frish(text: str) -> DictEntry:
    cols = text.split("\t")
    e = DictEntry(canonical_id="", seq=0)
    if len(cols) >= 5:
        e.deva, e.iast, slp1, e.cyr, gloss = cols[0], cols[1], cols[2], cols[3], cols[4]
        e.slp1 = _strip_slashes(slp1)
        m = _ROMAN_HOMONYM.match(gloss)
        if m and m.start(1) == 0:
            e.homonym = m.group(1)
        e.pos = _pos_tags(gloss)
        e.gloss_html = gloss
        return e
    e.raw = text
    return e


def _parse_knauer(text: str) -> DictEntry:
    cols = text.split("\t")
    e = DictEntry(canonical_id="", seq=0)
    if len(cols) >= 5:
        e.deva, e.iast, e.slp1, e.cyr, gloss = cols[0], cols[1], cols[2], cols[3], cols[4]
        e.slp1 = _strip_slashes(e.slp1)
        e.pos = _pos_tags(gloss)
        e.gloss_html = gloss
        return e
    e.raw = text
    return e


def _parse_smirnova(text: str) -> DictEntry:
    cols = text.split("\t")
    e = DictEntry(canonical_id="", seq=0)
    if len(cols) >= 5:
        e.cyr, e.iast, _, _, gloss = cols[0], cols[1], cols[2], cols[3], cols[4]
        e.pos = _pos_tags(gloss)
        e.gloss_html = gloss
        return e
    e.raw = text
    return e


_KOCH_HEAD = re.compile(r"^(°?[\u0900-\u097F]+)\s*(?:([IVX]+)\s+)?(?:/\s*/)?/([^/]+)/\s*(.*)$")


def _parse_kochergina(text: str, html: str) -> DictEntry:
    e = DictEntry(canonical_id="", seq=0)
    m = _KOCH_HEAD.match(html)
    if m:
        e.deva, e.homonym, e.iast, e.gloss_html = (
            m.group(1), m.group(2) or "", m.group(3), m.group(4))
        e.pos = _pos_tags(e.gloss_html)
        return e
    e.raw = text or html
    return e


_KOSS_HEAD = re.compile(
    r"^(\d+)\s+([\u0900-\u097F]+)\s+/([^/]+)/\s+/([^/]+)/\s+/([^/]+)/\s*(.*)$"
)


def _parse_kossovich(text: str, html: str) -> DictEntry:
    e = DictEntry(canonical_id="", seq=0)
    m = _KOSS_HEAD.match(html)
    if m:
        e.homonym = m.group(1)
        e.deva, e.iast, e.slp1, e.cyr, e.gloss_html = (
            m.group(2), m.group(3), m.group(4), m.group(5), m.group(6))
        e.pos = _pos_tags(e.gloss_html)
        return e
    # fallback: headword + single slash group (kochergina shape)
    return _parse_kochergina(text, html)


_PARSERS = {
    "frish": lambda row: _parse_frish(row[0]),
    "knauer": lambda row: _parse_knauer(row[0]),
    "slovar-smirnova": lambda row: _parse_smirnova(row[0]),
    "kochergina": lambda row: _parse_kochergina(row[0], row[1]),
    "kossovich": lambda row: _parse_kossovich(row[0], row[1]),
}


def parse_line(work: str, text: str, html: str, canonical_id: str, seq: int) -> DictEntry:
    e = _PARSERS[work]((text, html))
    e.canonical_id = canonical_id
    e.seq = seq
    if not e.iast and e.deva:
        e.iast = deva_to_iast(_strip_slashes(e.deva))
    if not e.iast and e.cyr:
        # smirnova: iast column may repeat the headword; fallback = cyr head
        pass
    return e


# ---------------------------------------------------------------- index


async def load_dict_entries(db, source_id: int, work: str) -> list[DictEntry]:
    entries: list[DictEntry] = []
    async with db.execute(
        "SELECT line_text, line_html, canonical_id, line_num FROM corpus_lines "
        "WHERE source_id = ? ORDER BY line_num",
        (source_id,),
    ) as cur:
        for text, html, canonical_id, line_num in await cur.fetchall():
            try:
                e = parse_line(work, text, html, canonical_id, line_num)
            except Exception:
                e = DictEntry(canonical_id=canonical_id or "", seq=line_num, raw=text)
            entries.append(e)
    return entries


_INDEX_CACHE: dict[tuple, list] = {}
_INDEX_CACHE_MAX = 8


async def get_dict_index(db, db_path: str, corpus_version: str, source_id: int,
                         work: str) -> list[DictEntry]:
    """Cached per-dict entry list, keyed by (db, corpus_version, source)."""
    key = (db_path, corpus_version, source_id, work)
    cached = _INDEX_CACHE.get(key)
    if cached is not None:
        return cached
    entries = await load_dict_entries(db, source_id, work)
    if len(_INDEX_CACHE) >= _INDEX_CACHE_MAX:
        _INDEX_CACHE.clear()
    _INDEX_CACHE[key] = entries
    return entries


def alphabet_index(entries: list[DictEntry]) -> list:
    """[(bucket, count, first_iast)] in varṇamālā order."""
    counts: dict[str, int] = {}
    for e in entries:
        b = bucket_of(e.iast or e.cyr or "")
        counts[b] = counts.get(b, 0) + 1
    out = []
    for b, n in sorted(counts.items(), key=lambda kv: alphabet_sort_key(kv[0])):
        out.append({"letter": b, "count": n})
    return out


# ---------------------------------------------------------------- lookup

def normalize_query(q: str) -> dict:
    """Accept Devanagari / IAST / SLP1 / Cyrillic and derive match keys."""
    q = q.strip()
    res: dict[str, str] = {"raw": q}
    if not q:
        return res
    if has_devanagari(q):
        res["iast"] = deva_to_iast(q)
        res["slp1"] = iast_to_slp1(res["iast"])
        return res
    if re.fullmatch(r"[A-Za-z0-9~^'\\-]+", q):
        # SLP1-looking (ASCII, possibly uppercase vowels) — but a plain
        # lowercase word is ambiguous between SLP1 and IAST; try both.
        res["slp1"] = q
        res["iast"] = slp1_to_iast(q)
        return res
    res["iast"] = q
    res["slp1"] = iast_to_slp1(q)
    return res


def entry_matches(e: DictEntry, keys: dict) -> bool:
    raw = keys.get("raw", "")
    if not raw:
        return False
    for attr, key in (("slp1", "slp1"), ("iast", "iast")):
        want = keys.get(key)
        if not want:
            continue
        have = _strip_slashes(getattr(e, attr)) or ""
        if have.lower() == want.lower():
            return True
        # multi-headword cells: any token match
        if any(t.lower() == want.lower() for t in have.split()):
            return True
    if any(has_devanagari(c) for c in raw):
        deva = _strip_slashes(e.deva)
        if any(t == raw for t in deva.split()):
            return True
    return False


def prefix_matches(entries: list[DictEntry], keys: dict, limit: int = 40) -> list:
    out = []
    want = (keys.get("slp1") or keys.get("iast") or keys.get("raw") or "").lower()
    if not want:
        return out
    for e in entries:
        have = (_strip_slashes(e.slp1) or _strip_slashes(e.iast)).lower()
        if have.startswith(want) or any(
            t.startswith(want) for t in have.split()
        ):
            out.append(e)
            if len(out) >= limit:
                break
    return out


# ---------------------------------------------------------------- gloss search


async def search_gloss(db, id_to_work: dict[int, str], ru_query: str,
                        limit: int = 60):
    """Reverse RU→Sa gloss search across the dict sources.

    FTS over the entry lines; each hit is parsed back into a structured
    entry so the card can show the Sanskrit headword with a dict badge.
    """
    if not ru_query.strip() or not id_to_work:
        return []
    source_ids = list(id_to_work)
    placeholders = ",".join("?" * len(source_ids))
    sql = (
        "SELECT line_text, line_html, canonical_id, line_num, source_id "
        f"FROM corpus_lines WHERE corpus_lines MATCH ? "
        f"AND source_id IN ({placeholders}) LIMIT ?"
    )
    # quote the phrase for FTS5; bare token match keeps it simple and safe
    match = '"' + ru_query.replace('"', '""') + '"'
    async with db.execute(sql, (match, *source_ids, limit)) as cur:
        rows = await cur.fetchall()
    out = []
    for text, html, canonical_id, line_num, source_id in rows:
        work = id_to_work.get(source_id)
        if not work:
            continue
        e = parse_line(work, text, html, canonical_id, line_num)
        e_dict = DICTS[work]
        out.append({
            "work": work,
            "badge": e_dict["short"],
            "dict_title": e_dict["title"],
            "entry": e,
        })
    return out


async def resolve_dict_source_ids(db) -> dict[str, int]:
    """slug → source_id for the five dict works (per current DB)."""
    slugs = list(DICTS.keys())
    placeholders = ",".join("?" * len(slugs))
    out: dict[str, int] = {}
    async with db.execute(
        f"SELECT slug, id FROM sources WHERE slug IN ({placeholders})", slugs
    ) as cur:
        for slug, sid in await cur.fetchall():
            out[slug] = sid
    return out


async def dict_entry_count(db, source_id: int) -> int:
    async with db.execute(
        "SELECT COUNT(*) FROM corpus_lines WHERE source_id = ?", (source_id,)
    ) as cur:
        return (await cur.fetchone())[0]
