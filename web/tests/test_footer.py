"""Footer rendering — corpus version visibility and graceful degradation."""
from fastapi.testclient import TestClient

from app.main import app
from app import corpus_info

client = TestClient(app)


def test_footer_present_on_home():
    r = client.get("/")
    assert r.status_code == 200
    assert 'class="site-footer"' in r.text


def test_footer_shows_corpus_version_when_loaded():
    corpus_info.corpus_version = "2026.06"
    corpus_info.generated_at = "2026-06-12T00:00:00"
    try:
        r = client.get("/")
        assert "Корпус: версия 2026.06" in r.text
        assert "от 2026-06-12" in r.text
    finally:
        corpus_info.corpus_version = None
        corpus_info.generated_at = None


def test_footer_hides_version_when_unloaded():
    # Pre-corpus_meta databases must not break the footer.
    assert corpus_info.corpus_version is None
    r = client.get("/")
    assert "Корпус: версия" not in r.text
    assert 'class="site-footer"' in r.text
