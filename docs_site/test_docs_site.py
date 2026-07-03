"""The corpus-faq help site (docs_site/, ZettelkastenWiki pilot) must satisfy
the package's full invariant harness. Skipped when the package isn't
installed (it is a docs-site dependency, not a web-app one)."""

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

zk = pytest.importorskip("zettelkastenwiki")

from build_site import CONFIG  # noqa: E402

from zettelkastenwiki import publish, testing  # noqa: E402


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("corpus_faq_site")
    publish(CONFIG, out)
    return out


def test_invariant_harness(site):
    testing.run_all(site, CONFIG)


def test_expected_pages_exist(site):
    for rel in (
        "index.html",
        "guide/what-is-the-corpus/index.html",
        "guide/how-to-search/index.html",
        "guide/how-to-cite/index.html",
        "faq/what-is-inside/index.html",
        "faq/rights-and-access/index.html",
        "faq/mobile-access/index.html",
    ):
        assert (site / rel).exists(), f"missing {rel}"


def test_russian_chrome(site):
    home = (site / "index.html").read_text(encoding="utf-8")
    assert 'lang="ru"' in home
    assert "Поиск по справке…" in home
    assert "https://samskrtam.ru/parallel-corpus/" in home
