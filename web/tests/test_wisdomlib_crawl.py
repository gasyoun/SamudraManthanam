import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

WISDOMLIB = Path(__file__).resolve().parents[1] / "corpus_builder" / "wisdomlib"
sys.path.insert(0, str(WISDOMLIB))

import crawl  # noqa: E402
import workflow_stagec  # noqa: E402


VALID_HTML = "<html>" + ("content " * 40) + "</html>"


class DummyClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _args(**kwargs):
    defaults = dict(
        section=None,
        ctype=None,
        lang=None,
        slug=None,
        english=False,
        pali=None,
        min_words=0,
        limit=0,
        shard=None,
        out="content",
        dry_run=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _book(tmp_path, chapter_count=1):
    rec = {
        "slug": "test-book",
        "url": "https://www.wisdomlib.org/sanskrit/book/test-book",
        "source_lang": "sanskrit",
        "chapter_count": chapter_count,
        "first_doc": "https://www.wisdomlib.org/sanskrit/book/test-book/d/doc1.html",
    }
    (tmp_path / "books_full.jsonl").write_text(json.dumps(rec) + "\n", encoding="utf-8")


def _last_run(tmp_path):
    return json.loads((tmp_path / "content" / crawl.LAST_RUN).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def wisdomlib_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(crawl, "HERE", tmp_path)
    monkeypatch.setattr(crawl.httpx, "AsyncClient", lambda **_kwargs: DummyClient())


def test_workflow_launcher_defaults_build_safe_argv():
    argv = workflow_stagec.build_argv({})
    assert argv == ["crawl.py", "stageC", "--lang", "sanskrit", "--workers", "1", "--delay", "5"]


def test_workflow_launcher_accepts_comma_filters_and_flags():
    argv = workflow_stagec.build_argv({
        "WL_LANG": "sanskrit,pali",
        "WL_SECTION": "purana,yoga",
        "WL_CTYPE": "book",
        "WL_SLUG": "skanda-purana,test-book",
        "WL_ENGLISH": "true",
        "WL_PALI_MODE": "exclude",
        "WL_MIN_WORDS": "1000",
        "WL_LIMIT": "2",
        "WL_WORKERS": "2",
        "WL_DELAY": "10",
    })
    assert argv == [
        "crawl.py", "stageC",
        "--lang", "sanskrit", "--lang", "pali",
        "--section", "purana", "--section", "yoga",
        "--ctype", "book",
        "--slug", "skanda-purana", "--slug", "test-book",
        "--english", "--no-pali",
        "--min-words", "1000", "--limit", "2",
        "--workers", "2", "--delay", "10",
    ]


def test_workflow_launcher_rejects_bad_slug():
    with pytest.raises(ValueError, match="invalid slug"):
        workflow_stagec.build_argv({"WL_SLUG": "test-book;rm -rf ."})


def test_workflow_launcher_rejects_invalid_workers_and_delay():
    with pytest.raises(ValueError, match="WL_WORKERS"):
        workflow_stagec.build_argv({"WL_WORKERS": "0"})
    with pytest.raises(ValueError, match="WL_DELAY"):
        workflow_stagec.build_argv({"WL_DELAY": "-1"})


def test_workflow_launcher_refuses_unfiltered_full_corpus():
    # Clearing every filter (notably an empty lang) must not silently select all books.
    with pytest.raises(ValueError, match="unfiltered full-corpus"):
        workflow_stagec.build_argv({"WL_LANG": ""})
    # An explicit non-lang filter is still allowed even with lang cleared.
    assert "--section" in workflow_stagec.build_argv({"WL_LANG": "", "WL_SECTION": "purana"})
    assert "--limit" in workflow_stagec.build_argv({"WL_LANG": "", "WL_LIMIT": "5"})


def test_workflow_launcher_accepts_shard():
    argv = workflow_stagec.build_argv({"WL_LANG": "sanskrit", "WL_SHARD": "2/3"})
    assert argv[argv.index("--shard") + 1] == "2/3"
    assert argv.index("--lang") < argv.index("--shard")   # shard follows the selectors


def test_workflow_launcher_rejects_bad_shard():
    with pytest.raises(ValueError, match="WL_SHARD"):
        workflow_stagec.build_argv({"WL_LANG": "sanskrit", "WL_SHARD": "3/2"})
    with pytest.raises(ValueError, match="WL_SHARD"):
        workflow_stagec.build_argv({"WL_LANG": "sanskrit", "WL_SHARD": "abc"})


def test_workflow_launcher_shard_alone_still_refuses_full_corpus():
    # A shard is a partition, not a selector: it must not satisfy the guard.
    with pytest.raises(ValueError, match="unfiltered full-corpus"):
        workflow_stagec.build_argv({"WL_LANG": "", "WL_SHARD": "1/3"})


def test_select_shards_are_disjoint_and_covering():
    recs = [{"slug": f"book-{i}", "source_lang": "sanskrit"} for i in range(200)]
    n = 4
    shards = [
        {r["slug"] for r in crawl.select(recs, _args(lang=["sanskrit"], shard=f"{k}/{n}"))}
        for k in range(1, n + 1)
    ]
    union = set().union(*shards)
    assert union == {r["slug"] for r in recs}          # every book covered once
    for i in range(n):
        for j in range(i + 1, n):
            assert not (shards[i] & shards[j])          # no book fetched twice
    assert all(shards)                                  # md5 spread leaves none empty


def test_select_rejects_bad_shard():
    with pytest.raises(ValueError, match="1<=k<=n"):
        crawl.select([], _args(shard="5/3"))


def test_validate_cached_docs_keeps_good_files_absent_from_short_expected(tmp_path):
    # A truncated/partial `expected` list must not delete valid cached chapters.
    bdir = tmp_path / "test-book"
    bdir.mkdir()
    (bdir / "doc1.html").write_text(VALID_HTML, encoding="utf-8")   # in expected
    (bdir / "doc2.html").write_text(VALID_HTML, encoding="utf-8")   # good, NOT in expected
    (bdir / "doc3.html").write_text("<html>Just a moment...</html>", encoding="utf-8")  # block
    valid, removed = crawl._validate_cached_docs(bdir, ["doc1.html"])
    assert valid == {"doc1.html"}
    assert removed == 1                                  # only the block page deleted
    assert (bdir / "doc2.html").exists()                 # good unexpected file preserved
    assert not (bdir / "doc3.html").exists()


@pytest.mark.asyncio
async def test_stage_c_valid_complete_cache_skips_fetch(monkeypatch, tmp_path):
    _book(tmp_path)
    bdir = tmp_path / "content" / "test-book"
    bdir.mkdir(parents=True)
    (bdir / "doc1.html").write_text(VALID_HTML, encoding="utf-8")
    (tmp_path / "content" / crawl.DOCS_MANIFEST).write_text(
        json.dumps({"test-book": ["doc1.html"]}), encoding="utf-8"
    )

    async def fail_fetch(_client, url):
        raise AssertionError(f"unexpected fetch: {url}")

    monkeypatch.setattr(crawl, "fetch", fail_fetch)
    await crawl.stage_c(1, _args(lang=["sanskrit"]))

    assert _last_run(tmp_path)["pages_written"] == 0
    assert _last_run(tmp_path)["pending_pages"] == 0


@pytest.mark.asyncio
async def test_stage_c_removes_block_cache_and_refetches(monkeypatch, tmp_path):
    _book(tmp_path)
    bdir = tmp_path / "content" / "test-book"
    bdir.mkdir(parents=True)
    (bdir / "doc1.html").write_text("Just a moment...", encoding="utf-8")
    (tmp_path / "content" / crawl.DOCS_MANIFEST).write_text(
        json.dumps({"test-book": ["doc1.html"]}), encoding="utf-8"
    )

    async def fake_fetch(_client, url):
        assert url.endswith("/doc1.html")
        return VALID_HTML

    monkeypatch.setattr(crawl, "fetch", fake_fetch)
    await crawl.stage_c(1, _args(lang=["sanskrit"]))

    summary = _last_run(tmp_path)
    assert summary["invalid_cached_files_removed"] == 1
    assert summary["pages_written"] == 1
    assert (bdir / "doc1.html").read_text(encoding="utf-8") == VALID_HTML


@pytest.mark.asyncio
async def test_stage_c_queues_missing_expected_file(monkeypatch, tmp_path):
    _book(tmp_path, chapter_count=2)
    bdir = tmp_path / "content" / "test-book"
    bdir.mkdir(parents=True)
    (bdir / "doc1.html").write_text(VALID_HTML, encoding="utf-8")
    (tmp_path / "content" / crawl.DOCS_MANIFEST).write_text(
        json.dumps({"test-book": ["doc1.html", "doc2.html"]}), encoding="utf-8"
    )

    async def fake_fetch(_client, url):
        assert url.endswith("/doc2.html")
        return VALID_HTML

    monkeypatch.setattr(crawl, "fetch", fake_fetch)
    await crawl.stage_c(1, _args(lang=["sanskrit"]))

    assert _last_run(tmp_path)["pages_written"] == 1
    assert (bdir / "doc2.html").exists()


@pytest.mark.asyncio
async def test_stage_c_unknown_manifest_fetches_landing(monkeypatch, tmp_path):
    _book(tmp_path)
    calls = []

    async def fake_fetch(_client, url):
        calls.append(url)
        if url.endswith("/test-book"):
            return VALID_HTML + '<a href="/sanskrit/book/test-book/d/doc1.html">doc</a>'
        return VALID_HTML

    monkeypatch.setattr(crawl, "fetch", fake_fetch)
    await crawl.stage_c(1, _args(lang=["sanskrit"]))

    manifest = json.loads((tmp_path / "content" / crawl.DOCS_MANIFEST).read_text(encoding="utf-8"))
    assert manifest == {"test-book": ["doc1.html"]}
    assert (tmp_path / "content" / "test-book" / "doc1.html").exists()
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_stage_c_blocked_landing_is_reported(monkeypatch, tmp_path):
    _book(tmp_path)

    async def fake_fetch(_client, _url):
        return "Just a moment..."

    monkeypatch.setattr(crawl, "fetch", fake_fetch)
    await crawl.stage_c(1, _args(lang=["sanskrit"]))

    summary = _last_run(tmp_path)
    assert summary["blocked_landings"] == 1
    assert summary["pages_written"] == 0
    assert summary["pending_pages"] == 0
