"""Tests for the /works size-and-chronology index.

Two layers:
1. Pure builder helpers (``build_works_index``) — slug parity with the app's
   own slug rule, the log10 size scale boundaries, and part labelling.
2. Route + data integrity — ``/api/works`` serves the committed
   ``works_index.json`` and ``/works`` renders; every size is null or 1–10 and
   the declared counts match the payload.
"""
import importlib.util
import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.slug import derive_slug as app_derive_slug

# Load the builder module straight from its file — it lives under
# corpus_builder/ (not an importable package) like the chronology builder.
_BUILD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "corpus_builder", "works_index", "build_works_index.py",
)
_spec = importlib.util.spec_from_file_location("build_works_index", _BUILD_PATH)
biw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(biw)


# ── slug parity ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("filename", [
    "01_rigveda", "06_mahabharata-bhishmaparva", "bhagavadgita-erman",
    "Кочергина", "Словарь Смирнова", "Dic_MW.txt",
])
def test_builder_slug_matches_app_slug(filename):
    # live_url correctness depends on the builder's slug being byte-identical
    # to the app's /sources/{slug} routing slug.
    assert biw.derive_slug(filename) == app_derive_slug(filename)


# ── log_scale ────────────────────────────────────────────────────────────────

def test_log_scale_zero_volume_is_unsized():
    assert biw.log_scale(0, 10, 1000) is None


def test_log_scale_min_is_one_max_is_ten():
    assert biw.log_scale(10, 10, 1_000_000) == 1
    assert biw.log_scale(1_000_000, 10, 1_000_000) == 10


def test_log_scale_clamps_reference_work_above_max_to_ten():
    # A dictionary larger than the literary ceiling clamps at 10, not 11+.
    assert biw.log_scale(50_000_000, 10, 1_000_000) == 10


def test_log_scale_is_logarithmic_not_linear():
    # Geometric midpoint of [10, 1e6] is 10**3.5 ≈ 3162 → mid of the 1..10 band.
    mid = biw.log_scale(round(10 ** 3.5), 10, 1_000_000)
    assert 5 <= mid <= 6


def test_log_scale_degenerate_domain():
    assert biw.log_scale(42, 100, 100) == 1


# ── part_label ───────────────────────────────────────────────────────────────

def test_part_label_multipart_keeps_distinguishing_suffix():
    out = biw.part_label("06_mahabharata-bhishmaparva", "mahabharata", "Mahābhārata")
    assert out == "Mahābhārata — Bhishmaparva"


def test_part_label_numbered_member_uses_number_when_no_suffix():
    # Ṛgveda maṇḍalas share the group name; the leading (zero-padded) number
    # disambiguates and keeps the parts aligned in the list.
    assert biw.part_label("07_rigveda", "rigveda", "Ṛgveda") == "Ṛgveda — 07"


def test_part_label_translator_suffix():
    out = biw.part_label("bhagavadgita-erman", "bhagavadgita", "Bhagavadgītā")
    assert out == "Bhagavadgītā — Erman"


def test_part_label_single_member_is_work_title():
    assert biw.part_label("isha-upanishad", "isha-upanishad", "Īśa Upaniṣad") == "Īśa Upaniṣad"


# ── route + data integrity ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_works_serves_index():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/works")
    assert r.status_code == 200
    data = r.json()
    assert data["n_works"] == len(data["works"])
    assert data["n_parts"] == sum(w["n_parts"] for w in data["works"])
    assert data["scale"]["transform"] == "log10"


@pytest.mark.asyncio
async def test_api_works_sizes_are_null_or_1_to_10():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        data = (await ac.get("/api/works")).json()
    for w in data["works"]:
        assert w["size"] is None or 1 <= w["size"] <= 10
        for p in w["parts"]:
            assert p["size"] is None or 1 <= p["size"] <= 10
        # live_url targets the slug route; timeline_url focuses this work.
        assert w["timeline_url"] == f"/chronology?focus={w['slug']}"


@pytest.mark.asyncio
async def test_works_page_renders_both_columns():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/works")
    assert r.status_code == 200
    assert "wx-works" in r.text and "wx-parts" in r.text
