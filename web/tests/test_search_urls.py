"""Pretty search IRI helpers."""
from app.search_urls import (
    expand_source_token,
    pretty_search_path,
    pretty_search_url,
    shorten_source,
)


def test_hastinapur_share_url_is_short_and_readable():
    url = pretty_search_url(
        base="https://samudra.samskrte.ru",
        query="Хастинапур",
        source_slugs=["mahabharata-ukazatel-geo"],
    )
    assert url == "https://samudra.samskrte.ru/search/geo/Хастинапур"
    assert "?" not in url
    assert "%D0" not in url


def test_alias_round_trip():
    assert expand_source_token("geo") == "mahabharata-ukazatel-geo"
    assert shorten_source("mahabharata-ukazatel-geo") == "geo"
    assert pretty_search_path("Абхиманью", ["mahabharata-ukazatel-imen"]) == (
        "/search/imen/Абхиманью"
    )
    assert pretty_search_path("Баранников", ["mahabharata-stati"]) == (
        "/search/stati/Баранников"
    )


def test_all_sources_omits_src_segment():
    assert pretty_search_path("Хастинапур") == "/search/Хастинапур"
