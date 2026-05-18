"""Tests for `app.services.slug` — pure helpers for URL slug derivation.

Two layers:
1. Transliteration table sanity (every Russian letter mapped, ё/щ produce
   multi-char output).
2. End-to-end derive_slug behaviour on the actual filename shapes seen in
   the live corpus.
"""
from app.services.slug import (
    derive_slug,
    make_unique_slug,
    transliterate_cyrillic,
)


# ── transliterate_cyrillic ──────────────────────────────────────────────────

def test_transliterate_passes_ascii_through():
    assert transliterate_cyrillic("bhagavadgita-1788") == "bhagavadgita-1788"
    assert transliterate_cyrillic("06_mahabharata-bhishmaparva") == "06_mahabharata-bhishmaparva"


def test_transliterate_handles_lowercase_cyrillic():
    assert transliterate_cyrillic("словарь") == "slovar"
    assert transliterate_cyrillic("кнауэр") == "knauer"


def test_transliterate_handles_uppercase_cyrillic():
    # Mapping is lowercase-keyed; we lower() before lookup so uppercase works.
    assert transliterate_cyrillic("Кришна") == "krishna"
    assert transliterate_cyrillic("ШИВА") == "shiva"


def test_transliterate_multichar_letters():
    # ё → yo, щ → shch, ц → ts, ч → ch, ш → sh
    assert transliterate_cyrillic("ёлка") == "yolka"
    assert transliterate_cyrillic("щит") == "shchit"
    assert transliterate_cyrillic("цапля") == "tsaplya"
    assert transliterate_cyrillic("часть") == "chast"
    assert transliterate_cyrillic("шапка") == "shapka"


def test_transliterate_drops_hard_and_soft_signs():
    assert transliterate_cyrillic("объект") == "obekt"
    assert transliterate_cyrillic("Кочергина") == "kochergina"


def test_transliterate_preserves_non_cyrillic_unicode():
    # Devanagari and IAST diacritics pass through unchanged; slug
    # normalisation will hyphen them out later.
    assert transliterate_cyrillic("Bhartṛhari") == "Bhartṛhari"
    assert transliterate_cyrillic("धर्म") == "धर्म"


# ── derive_slug — live-corpus shapes ────────────────────────────────────────

def test_derive_slug_ascii_filename_stays_clean():
    assert derive_slug("bhagavadgita-smirnov.html") == "bhagavadgita-smirnov"
    assert derive_slug("06_mahabharata-bhishmaparva.html") == "06_mahabharata-bhishmaparva"
    assert derive_slug("01_rigveda.html") == "01_rigveda"


def test_derive_slug_strips_known_extensions():
    assert derive_slug("foo.html") == "foo"
    assert derive_slug("foo.htm") == "foo"
    assert derive_slug("foo.txt") == "foo"
    assert derive_slug("foo.xml") == "foo"


def test_derive_slug_extension_match_is_case_insensitive():
    assert derive_slug("FOO.HTML") == "foo"
    assert derive_slug("MIXED.Html") == "mixed"


def test_derive_slug_cyrillic_filenames():
    # Live-corpus Cyrillic filenames from the dictionary section.
    assert derive_slug("Словарь Смирнова.txt") == "slovar-smirnova"
    assert derive_slug("Кнауэр.txt") == "knauer"
    assert derive_slug("Коссович.txt") == "kossovich"
    assert derive_slug("Фриш.txt") == "frish"
    assert derive_slug("Кочергина.txt") == "kochergina"


def test_derive_slug_cyrillic_with_punctuation():
    # Dots and dashes in the middle of the name get normalised to hyphens.
    assert derive_slug("Рамаяна 3. Словарь.txt") == "ramayana-3-slovar"
    assert derive_slug("Эрман-Темкин.txt") == "erman-temkin"
    assert derive_slug("Словарь Гринцера из Рамаяны 1-2.txt") == "slovar-grintsera-iz-ramayany-1-2"


def test_derive_slug_handles_mixed_script():
    # Sources with both Cyrillic and Latin (rare but possible).
    assert derive_slug("Шри Шарма BhG.txt") == "shri-sharma-bhg"


def test_derive_slug_empty_input_returns_empty():
    assert derive_slug("") == ""
    assert derive_slug(None) == ""  # type: ignore[arg-type]


def test_derive_slug_extension_only_returns_empty():
    # ".html" with no base → slug is empty.
    assert derive_slug(".html") == ""


def test_derive_slug_collapses_runs_of_separators():
    assert derive_slug("foo---bar.html") == "foo-bar"
    assert derive_slug("foo  bar  baz.html") == "foo-bar-baz"


def test_derive_slug_preserves_underscore():
    # Corpus uses `01_rigveda` style — underscore is URL-safe and meaningful.
    assert derive_slug("yoga-sutry_sharma.html") == "yoga-sutry_sharma"


# ── make_unique_slug — collision resolution ─────────────────────────────────

def test_make_unique_returns_base_when_no_collision():
    assert make_unique_slug("foo.html", existing=set()) == "foo"


def test_make_unique_appends_2_on_first_collision():
    assert make_unique_slug("foo.html", existing={"foo"}) == "foo-2"


def test_make_unique_finds_next_available_suffix():
    assert make_unique_slug(
        "foo.html", existing={"foo", "foo-2", "foo-3"},
    ) == "foo-4"


def test_make_unique_handles_empty_derived_base():
    # Pathological filename like ".html" derives to "" — falls back to "source".
    assert make_unique_slug(".html", existing=set()) == "source"
    assert make_unique_slug(".html", existing={"source"}) == "source-2"


def test_make_unique_does_not_mutate_existing_set():
    # The function should be pure on its input set; caller is responsible
    # for adding the returned slug back if more insertions follow.
    existing = {"foo"}
    before = set(existing)
    make_unique_slug("foo.html", existing=existing)
    assert existing == before
