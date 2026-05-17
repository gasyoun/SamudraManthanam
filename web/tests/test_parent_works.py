"""Tests for `parent_works.detect_parent_work` and the resulting `isPartOf`
shape on source-page JSON-LD.

Three things to lock down:
1. Every filename family from the live corpus resolves to the expected parent.
2. Unrecognised filenames return None (no false positives).
3. `Book.isPartOf` becomes a list when parent detected, stays a dict otherwise
   — preserves backward compat for downstream consumers.
"""
from app.parent_works import detect_parent_work
from app.services.source_metadata import build_source_jsonld


# ── detect_parent_work: volume relationships ────────────────────────────────

def test_mahabharata_parvans_map_to_mahabharata():
    for fname in (
        "01_mahabharata-adiparva.html",
        "06_mahabharata-bhishmaparva.html",
        "12_mahabharata-shantiparva.html",
        "18_mahabharata-svargarohanikaparva.html",
    ):
        parent = detect_parent_work(fname)
        assert parent is not None, f"{fname}: should match MBh"
        assert parent["name"] == "Махабхарата"
        assert parent["alternateName"] == "Mahābhārata"


def test_rigveda_mandalas_map_to_rigveda():
    for fname in ("01_rigveda.html", "09_rigveda.html", "10_rigveda.html"):
        parent = detect_parent_work(fname)
        assert parent is not None
        assert parent["name"] == "Ригведа"
        assert parent["alternateName"] == "Ṛgveda"


def test_atharvaveda_books_map_to_atharvaveda():
    for fname in ("01_atharvaveda.html", "19_atharvaveda.html"):
        parent = detect_parent_work(fname)
        assert parent is not None
        assert parent["name"] == "Атхарваведа"
        assert parent["alternateName"] == "Atharvaveda"


def test_ramayana_kandas_map_to_ramayana():
    for fname in (
        "01_ramayana-balakanda.html",
        "02_ramayana-ayodhyakanda.html",
        "05_ramayana-sundarakanda.html",
    ):
        parent = detect_parent_work(fname)
        assert parent is not None
        assert parent["name"] == "Рамаяна"
        assert parent["alternateName"] == "Rāmāyaṇa"


# ── detect_parent_work: edition / translation groupings ─────────────────────

def test_bhagavadgita_translations_anthology_and_commentaries_all_map_to_bhg():
    bhg_filenames = [
        "bhagavadgita-1788.html",
        "bhagavadgita-smirnov.html",
        "bhagavadgita-prabhupada.html",
        "bhagavadgita-radha.html",
        "bhagavadgity.html",                      # anthology
        "ramanuja_gitabhashya.html",              # commentary
        "gitarthasamgraha-abhinavagupta.html",    # commentary
        "gitartha-samgraha_yamunacharya.html",    # commentary (32-verse summary)
    ]
    for fname in bhg_filenames:
        parent = detect_parent_work(fname)
        assert parent is not None, f"{fname}: should map to BhG"
        assert parent["name"] == "Бхагавадгита"
        assert parent["alternateName"] == "Bhagavadgītā"


def test_yoga_sutra_editions_all_map_to_yoga_sutra():
    for fname in (
        "yoga-sutry.html",                # anthology
        "yoga-sutry_vyasa-bhashya.html",
        "yoga-sutry_sharma.html",
        "yoga-sutry_zagumennov.html",
    ):
        parent = detect_parent_work(fname)
        assert parent is not None
        assert parent["name"] == "Йога-сутры"
        assert parent["alternateName"] == "Yoga-Sūtra"


def test_shatakatraya_editions_map_to_shatakatraya():
    for fname in ("shatakatrayam.html", "shatakatrayam-serebryakov.html"):
        parent = detect_parent_work(fname)
        assert parent is not None
        assert parent["alternateName"] == "Śatakatraya"


def test_buddhacarita_translations_map_to_buddhacarita():
    for fname in ("buddhacharita.html", "buddhacharita-balmont.html"):
        parent = detect_parent_work(fname)
        assert parent is not None
        assert parent["alternateName"] == "Buddhacarita"


# ── False-positive guard ────────────────────────────────────────────────────

def test_unrelated_filenames_return_none():
    # Dictionaries, single-work files, ad-hoc texts should NOT match.
    for fname in (
        "Словарь Смирнова.txt",
        "Dic_MW.txt",
        "isha-up.html",                # Upaniṣad — no parent registry entry yet
        "kama-sutra.html",
        "manavadharmashastra.html",
        "hatha-yoga-pradipika.html",
        "",
    ):
        assert detect_parent_work(fname) is None, f"{fname!r} should not match"


def test_partial_filename_match_does_not_falsely_resolve():
    # Patterns are anchored — a file that merely contains "rigveda" in the
    # middle must not match.
    assert detect_parent_work("rigveda-overview.html") is None
    assert detect_parent_work("foo_mahabharata.html") is None


# ── Book.isPartOf shape: list when parent, dict when not ────────────────────

def test_jsonld_ispart_of_becomes_list_when_parent_detected():
    source = {
        "id": 1,
        "filename": "06_mahabharata-bhishmaparva.html",
        "title": "Махабхарата VI (2009); В.Г. Эрман",
    }
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Site",
    )
    assert isinstance(jsonld["isPartOf"], list)
    assert len(jsonld["isPartOf"]) == 2
    # WebSite first (existing), parent Book second.
    assert jsonld["isPartOf"][0]["@type"] == "WebSite"
    assert jsonld["isPartOf"][1]["@type"] == "Book"
    assert jsonld["isPartOf"][1]["name"] == "Махабхарата"
    assert jsonld["isPartOf"][1]["alternateName"] == "Mahābhārata"


def test_jsonld_ispart_of_stays_dict_when_no_parent():
    # Preserves backward-compatible shape for sources without a known parent.
    source = {
        "id": 1,
        "filename": "isha-up.html",
        "title": "Иша упанишада (1992); А.Я. Сыркин",
    }
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Site",
    )
    assert isinstance(jsonld["isPartOf"], dict)
    assert jsonld["isPartOf"]["@type"] == "WebSite"


def test_jsonld_ispart_of_for_bhagavadgita_translation():
    source = {
        "id": 1,
        "filename": "bhagavadgita-smirnov.html",
        "title": "Бхагавад-Гита (1977); Б. Л. Смирнов",
    }
    jsonld = build_source_jsonld(
        source=source, canonical_url="/sources/1", site_name="Site",
    )
    assert isinstance(jsonld["isPartOf"], list)
    parent = next(p for p in jsonld["isPartOf"] if p["@type"] == "Book")
    assert parent["name"] == "Бхагавадгита"
    assert parent["alternateName"] == "Bhagavadgītā"
