"""H2738 follow-up: numeric chapter must not 500 /api/search."""
from app.models import SearchResultItem


def test_search_result_item_coerces_int_chapter():
    item = SearchResultItem(
        source_id=1,
        source_title="Mahabharata articles",
        chapter=5,
        line_num=1,
        link_id="1.5.1",
        line_html="<p>x</p>",
        line_text="x",
        source_slug="mahabharata-stati",
        canonical_id="mahabharata-stati:1.5.1#ru",
    )
    assert item.chapter == "5"


def test_search_result_item_none_chapter_is_empty():
    item = SearchResultItem(
        source_id=1,
        source_title="t",
        chapter=None,
        line_num=1,
        line_html="",
        line_text="",
    )
    assert item.chapter == ""
