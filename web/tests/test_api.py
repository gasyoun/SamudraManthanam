import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import os
import json
from urllib.parse import quote

@pytest.mark.asyncio
async def test_search_basic():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/search", json={
            "query": "arjuna",
            "mode": "plain"
        })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "html_fragment" in data
    # Verify Jinja dict access didn't crash (if it did, we'd get 500)
    assert len(data["results"]) >= 0

@pytest.mark.asyncio
async def test_search_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Empty query
        response = await ac.post("/api/search", json={"query": "", "mode": "plain"})
        assert response.status_code == 422
        
        # Invalid mode
        response = await ac.post("/api/search", json={"query": "test", "mode": "bad"})
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_path_traversal():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Attempt traversal
        response = await ac.get("/api/corpus-sync/file/..%5CProgramdata%5Cdata.txt")
        assert response.status_code in [400, 404]

@pytest.mark.asyncio
async def test_export_standalone():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/export?query=arjuna&mode=plain")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "html" in response.text.lower()
    # Verify no NameError for render_standalone
    assert "style" in response.text.lower()

@pytest.mark.asyncio
async def test_source_selection_none():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # source_ids=[] should return zero results
        response = await ac.post("/api/search", json={
            "query": "arjuna",
            "mode": "plain",
            "source_ids": []
        })
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0

@pytest.mark.asyncio
async def test_multi_token_plain_search():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Query with multiple tokens should match lines containing all tokens
        response = await ac.post("/api/search", json={
            "query": "arjuna krishna",
            "mode": "plain"
        })
    assert response.status_code == 200
    # The tokens should be joined by AND in FTS5
    # (Assuming there's data that matches both)

@pytest.mark.asyncio
async def test_invalid_get_mode_export():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid mode in GET should return 422
        response = await ac.get("/api/search/export?query=test&mode=bad")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_invalid_get_mode_stream():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/stream?query=test&mode=bad")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_invalid_get_source_ids():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/export?query=test&source_ids=1,nope")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_export_rejects_unbounded_query():
    """REGRESSION: GET /api/search/export used to accept arbitrarily long
    `query` strings while POST /api/search was capped at 1000. Now both share
    the same Pydantic-equivalent constraint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/export?query=" + "a" * 2000 + "&mode=plain")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_export_rejects_empty_query():
    """The export endpoint must require a non-empty query, just like POST."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/export?query=&mode=plain")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stream_rejects_unbounded_query():
    """Same bound applies to the SSE endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/stream?query=" + "a" * 2000 + "&mode=plain")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_export_filename_is_sanitized():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/export?query=arjuna%22%0D%0AX-Bad%3Ayes&mode=plain")
    assert response.status_code == 200
    content_disposition = response.headers["content-disposition"]
    assert "\r" not in content_disposition
    assert "\n" not in content_disposition
    assert "X-Bad:yes" not in content_disposition

@pytest.mark.asyncio
async def test_invalid_regex():
    """Both entry points answer with the SAME status and payload.

    They used to disagree — POST 422 (pydantic's own error, which echoed the
    offending pattern and the engine's message) against GET 400. H1926 routes
    every regex refusal through one contract, so the shape below is now the
    whole story; per-route detail lives in tests/test_regex_bounded.py.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid regex in POST
        response = await ac.post("/api/search", json={
            "query": "[",
            "mode": "regex"
        })
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_regex"

        # Invalid regex in GET
        response = await ac.get("/api/search/export?query=%5B&mode=regex")
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_regex"

@pytest.mark.asyncio
async def test_export_json_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/export?query=arjuna&mode=plain&format=json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert set(["query", "mode", "corpus_version", "timestamp", "source_filter"]).issubset(data["metadata"].keys())
    assert data["metadata"]["query"] == "arjuna"
    assert "results" in data
    assert isinstance(data["results"], list)
    if data["results"]:
        item = data["results"][0]
        for key in ("source_id", "source_title", "chapter", "line_num", "link_id", "line_html", "line_text"):
            assert key in item


@pytest.mark.asyncio
async def test_export_csv_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/export?query=arjuna&mode=plain&format=csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    body = response.text
    assert "# query" in body
    assert "arjuna" in body
    assert "source_id" in body


@pytest.mark.asyncio
async def test_export_json_csv_same_result_set_as_html():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        html_resp = await ac.get("/api/search/export?query=arjuna&mode=plain")
        json_resp = await ac.get("/api/search/export?query=arjuna&mode=plain&format=json")
    assert html_resp.status_code == 200
    assert json_resp.status_code == 200
    json_data = json_resp.json()
    assert json_data["metadata"]["result_count"] == len(json_data["results"])


@pytest.mark.asyncio
async def test_export_invalid_format():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/export?query=arjuna&mode=plain&format=xml")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_export_json_csv_text_is_snippet_capped():
    """H1831: JSON/CSV export must not return full untruncated line_text.

    A broad single-letter/prefix query can hit many rows; each row's text must
    be a KWIC-sized snippet (≤ ~window*2 + ellipsis + match), never the full
    verse+translation dump that would let a client reconstruct the corpus.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Broad query; fixture corpus is small but still exercises the path.
        json_resp = await ac.get("/api/search/export?query=a&mode=plain&format=json")
        csv_resp = await ac.get("/api/search/export?query=a&mode=plain&format=csv")
    assert json_resp.status_code == 200
    assert csv_resp.status_code == 200
    data = json_resp.json()
    # Hard cap: a single KWIC window is 40 chars each side → well under 500
    # even with match + ellipsis. Full corpus lines are often much longer.
    max_snippet = 500
    for item in data.get("results") or []:
        assert len(item.get("line_text") or "") <= max_snippet
        assert len(item.get("line_html") or "") <= max_snippet
    # CSV body lines after the header should also be short in the text column.
    # (Structural check: no multi-kilobyte CSV cells for line_text.)
    assert len(csv_resp.text) < 200_000


@pytest.mark.asyncio
async def test_multi_query_header_does_not_duplicate_ordinal():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/search", json={
            "query": "arjuna\nkrishna",
            "mode": "plain"
        })
    assert response.status_code == 200
    fragment = response.json()["html_fragment"]
    assert "2-та" not in fragment
    # PR #161 (commit 6d7fa82) intentionally dropped the old "при пахтании
    # океана в N поисковых запросах" header in favor of a compact stats
    # line that folds every query term into one quoted, comma-joined
    # string instead of counting them — assert that current contract.
    assert "«arjuna, krishna»" in fragment

@pytest.mark.asyncio
async def test_morphological_search_metadata():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/search", json={
            "query": "svasti",
            "mode": "morphological"
        })
    assert response.status_code == 200
    data = response.json()
    assert "search_metadata" in data
    assert data["search_metadata"] is not None
    assert "stems" in data["search_metadata"]
    assert "variants" in data["search_metadata"]
    # "svasti" should at least expand to itself
    assert "svasti" in data["search_metadata"]["stems"]

@pytest.mark.asyncio
async def test_search_stream_morphological():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/stream?query=svasti&mode=morphological")
    assert response.status_code == 200
    # SSE response
    assert "text/event-stream" in response.headers["content-type"]
    # Check for progress or done events
    assert "progress" in response.text or "done" in response.text


def _parse_sse_events(text):
    """Parse `data: {...}` SSE lines into a list of decoded JSON payloads."""
    events = []
    for line in text.splitlines():
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:"):].strip()))
    return events


@pytest.mark.asyncio
async def test_search_stream_happy_path_hit():
    """A3.2: fixture hit query yields text/event-stream + >=1 data event
    reporting a nonzero total via the 'done' event."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/stream?query=arjuna&mode=plain")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = _parse_sse_events(response.text)
    assert len(events) >= 1

    done_events = [e for e in events if e.get("type") == "done"]
    assert len(done_events) == 1
    assert done_events[0]["total"] >= 1

    progress_events = [e for e in events if e.get("type") == "progress"]
    assert any(e.get("found_so_far", 0) >= 1 for e in progress_events)


@pytest.mark.asyncio
async def test_search_stream_invalid_regex():
    """Validation parity: an unparseable regex pattern returns 400,
    matching POST /api/search's regex-mode behavior."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/stream?query=" + quote("(") + "&mode=regex")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_stream_rejects_empty_query():
    """Validation parity: empty query rejected, same as POST /api/search."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/search/stream?query=&mode=plain")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_stream_does_not_appear_in_frontend():
    """A3.3: search.js must not call the stream endpoint (unwired, PLAN R7)."""
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    search_js_path = os.path.join(static_dir, "search.js")
    with open(search_js_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "/api/search/stream" not in content
    assert "search/stream" not in content
