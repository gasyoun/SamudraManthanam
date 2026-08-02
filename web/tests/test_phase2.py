import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.settings import settings
import aiosqlite
from app.db import create_schema

client = TestClient(app)

@pytest.mark.asyncio
async def test_regex_safety_timeout(test_db):
    response = client.post("/api/search", json={
        "query": ".*arjuna.*",
        "mode": "regex"
    })
    assert response.status_code == 200
    data = response.json()
    assert "search_metadata" in data
    assert "scanned_rows" in data["search_metadata"]
    assert "timeout" in data["search_metadata"]
    assert "truncated" in data["search_metadata"]


@pytest.mark.asyncio
async def test_regex_catastrophic_backtracking_bounded(test_db):
    """H1830: a single pathological pattern must not hang past a wall-clock bound.

    stdlib re has no per-call timeout; search_regex previously only checked
    MAX_TIME between rows, so one re.search on a ~30-char non-matching line
    with (a+)+$ could block for tens of seconds. The fix uses the `regex`
    package's per-match timeout (or equivalent). Assert completion <2s.
    """
    import time
    t0 = time.time()
    response = client.post("/api/search", json={
        "query": "(a+)+$",
        "mode": "regex",
        "case_sensitive": True,
    })
    elapsed = time.time() - t0
    assert response.status_code == 200, response.text
    assert elapsed < 2.0, f"ReDoS path took {elapsed:.2f}s (expected <2s)"
    data = response.json()
    assert "results" in data

@pytest.mark.asyncio
async def test_reader_view(test_db):
    response = client.get("/sources/1")
    assert response.status_code == 200
    assert "Source 1" in response.text
    assert "svasti arjuna" in response.text

@pytest.mark.asyncio
async def test_reader_highlight(test_db):
    response = client.get("/sources/1?highlight=10")
    assert response.status_code == 200
    assert "highlighted" in response.text

@pytest.mark.asyncio
async def test_export_metadata(test_db):
    response = client.get("/api/search/export?query=arjuna")
    assert response.status_code == 200
    assert "Запрос:" in response.text
    assert "arjuna" in response.text

@pytest.mark.asyncio
async def test_context_endpoint_returns_surrounding_lines(test_db):
    # source 1 has line_num=10 and line_num=11 in the fixture
    response = client.get("/api/search/context?source_id=1&line_num=10&window=5")
    assert response.status_code == 200
    data = response.json()
    assert "before" in data and "current" in data and "after" in data
    assert data["current"]["line_num"] == 10
    assert data["current"]["link_id"] == "1.10"
    # line 11 should appear in after
    assert any(l["line_num"] == 11 for l in data["after"])
    # no lines before line 10 in this source
    assert data["before"] == []

@pytest.mark.asyncio
async def test_context_endpoint_window_clamped(test_db):
    response = client.get("/api/search/context?source_id=1&line_num=10&window=25")
    assert response.status_code == 422  # exceeds max=20

@pytest.mark.asyncio
async def test_context_endpoint_missing_line_returns_null_current(test_db):
    response = client.get("/api/search/context?source_id=1&line_num=999&window=5")
    assert response.status_code == 200
    data = response.json()
    assert data["current"] is None
    assert data["before"] == []
    assert data["after"] == []

@pytest.mark.asyncio
async def test_anchor_redirect(test_db):
    # /sources/1/anchor/1.10 should redirect to /sources/1?highlight=1.10
    response = client.get("/sources/1/anchor/1.10", follow_redirects=False)
    assert response.status_code == 302
    assert "highlight=1.10" in response.headers["location"]

@pytest.mark.asyncio
async def test_search_result_contains_context_button(test_db):
    response = client.post("/api/search", json={"query": "arjuna", "mode": "plain"})
    assert response.status_code == 200
    html = response.json()["html_fragment"]
    assert "btn-context" in html
    assert "btn-copy-citation" in html
