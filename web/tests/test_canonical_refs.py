"""Resolver decision table — the B2/B4 adversarial fixtures (H1925).

The criterion under test is B4: *ambiguous or missing mappings fail visibly;
none silently binds to another line.* Each test below is one way a reference
can go wrong across a rebuild.
"""
import sqlite3

import pytest

from app.canonical_refs import (
    DurableRef,
    ResolutionStatus,
    build_identity_index,
    content_fingerprint,
    resolve_against_index,
    summarise,
)
from canonical_fixtures import make_corpus

SOURCES = [(1, "bhagavadgita-1909", "Бхагавадгита"), (2, "gitagovinda", "Гитаговинда")]
LINES_V1 = [
    (1, 1, "bhagavadgita-1909:1.1", "dharmakṣetre kurukṣetre"),
    (1, 2, "bhagavadgita-1909:1.2", "saṃjaya uvāca"),
    (2, 1, "gitagovinda:1.3-6", "meghair meduram ambaram"),
]


def _index(tmp_path, name, version, lines, sources=SOURCES):
    path = make_corpus(tmp_path / name, corpus_version=version, sources=sources, lines=lines)
    conn = sqlite3.connect(path)
    try:
        return build_identity_index(conn)
    finally:
        conn.close()


def test_canonical_reference_survives_reordered_ingest(tmp_path):
    """The headline case: ordinals all move, the canonical tuple does not."""
    v1 = _index(tmp_path, "v1.db", "v2026.01", LINES_V1)
    # A rebuild that inserts a line and renumbers the sources.
    lines_v2 = [
        (7, 1, "bhagavadgita-1909:1.0", "invocation added by the editor"),
        (7, 2, "bhagavadgita-1909:1.1", "dharmakṣetre kurukṣetre"),
        (7, 3, "bhagavadgita-1909:1.2", "saṃjaya uvāca"),
        (9, 1, "gitagovinda:1.3-6", "meghair meduram ambaram"),
    ]
    sources_v2 = [(7, "bhagavadgita-1909", "Бхагавадгита"), (9, "gitagovinda", "Гитаговинда")]
    v2 = _index(tmp_path, "v2.db", "v2026.02", lines_v2, sources_v2)

    ref = DurableRef(
        source_slug="bhagavadgita-1909",
        canonical_id="bhagavadgita-1909:1.1",
        corpus_version="v2026.01",
        source_id=1,
        line_num=1,
        origin="corrections#1",
    )
    before = resolve_against_index(ref, v1)
    after = resolve_against_index(ref, v2)

    assert before.status is ResolutionStatus.CANONICAL
    assert after.status is ResolutionStatus.CANONICAL
    # Identity and content held; only the throwaway ordinals moved.
    assert (before.source_slug, before.canonical_id) == (after.source_slug, after.canonical_id)
    assert before.fingerprint == after.fingerprint
    assert (before.source_id, before.line_num) == (1, 1)
    assert (after.source_id, after.line_num) == (7, 2)


def test_legacy_ordinal_across_versions_is_never_bound(tmp_path):
    """The mis-bind this whole lane exists to prevent.

    In v2 the ordinal (1, 1) is a *different verse*. With no mapping, the
    resolver must refuse rather than hand back a plausible wrong line.
    """
    lines_v2 = [
        (1, 1, "bhagavadgita-1909:1.0", "invocation added by the editor"),
        (1, 2, "bhagavadgita-1909:1.1", "dharmakṣetre kurukṣetre"),
    ]
    v2 = _index(tmp_path, "v2.db", "v2026.02", lines_v2)

    ref = DurableRef(corpus_version="v2026.01", source_id=1, line_num=1, origin="corrections#9")
    res = resolve_against_index(ref, v2)

    assert res.status is ResolutionStatus.ORPHAN
    assert "refusing to guess" in res.reason
    assert res.canonical_id is None


def test_legacy_ordinal_resolves_inside_its_own_version(tmp_path):
    v1 = _index(tmp_path, "v1.db", "v2026.01", LINES_V1)
    ref = DurableRef(corpus_version="v2026.01", source_id=1, line_num=2)
    res = resolve_against_index(ref, v1)
    assert res.status is ResolutionStatus.LEGACY_DIRECT
    assert res.canonical_id == "bhagavadgita-1909:1.2"


def test_legacy_ordinal_maps_across_versions_when_pinned(tmp_path):
    lines_v2 = [
        (1, 1, "bhagavadgita-1909:1.0", "invocation added by the editor"),
        (1, 2, "bhagavadgita-1909:1.1", "dharmakṣetre kurukṣetre"),
    ]
    v2 = _index(tmp_path, "v2.db", "v2026.02", lines_v2)
    legacy_map = {
        ("v2026.01", 1, 1): {
            "source_slug": "bhagavadgita-1909",
            "canonical_id": "bhagavadgita-1909:1.1",
            "fingerprint": "",
        }
    }
    ref = DurableRef(corpus_version="v2026.01", source_id=1, line_num=1)
    res = resolve_against_index(ref, v2, legacy_map)

    assert res.status is ResolutionStatus.LEGACY_MAPPED
    assert res.canonical_id == "bhagavadgita-1909:1.1"
    assert res.line_num == 2  # the ordinal moved; the mapping followed it


def test_duplicate_canonical_id_is_ambiguous_not_first_match(tmp_path):
    lines = [
        (1, 1, "bhagavadgita-1909:1.1", "first printing"),
        (1, 2, "bhagavadgita-1909:1.1", "duplicate anchor in the print edition"),
    ]
    idx = _index(tmp_path, "dup.db", "v2026.03", lines)
    ref = DurableRef(source_slug="bhagavadgita-1909", canonical_id="bhagavadgita-1909:1.1")
    res = resolve_against_index(ref, idx)

    assert res.status is ResolutionStatus.AMBIGUOUS
    assert len(res.candidates) == 2
    assert res.line_num is None  # nothing was bound


def test_deleted_passage_orphans_rather_than_shifting(tmp_path):
    lines_v2 = [(1, 1, "bhagavadgita-1909:1.2", "saṃjaya uvāca")]
    v2 = _index(tmp_path, "v2.db", "v2026.02", lines_v2)
    ref = DurableRef(
        source_slug="bhagavadgita-1909",
        canonical_id="bhagavadgita-1909:1.1",
        corpus_version="v2026.01",
    )
    res = resolve_against_index(ref, v2)
    assert res.status is ResolutionStatus.ORPHAN
    assert "does not exist" in res.reason


def test_unversioned_ordinal_binds_only_when_caller_vouches_for_it(tmp_path):
    """A live client's ordinals are current; a stored row's provenance is not."""
    v1 = _index(tmp_path, "v1.db", "v2026.01", LINES_V1)
    ref = DurableRef(source_id=1, line_num=1)

    stored = resolve_against_index(ref, v1)
    live = resolve_against_index(ref, v1, assume_current_version=True)

    assert stored.status is ResolutionStatus.ORPHAN
    assert live.status is ResolutionStatus.LEGACY_DIRECT


def test_reference_without_any_address_is_refused(tmp_path):
    v1 = _index(tmp_path, "v1.db", "v2026.01", LINES_V1)
    res = resolve_against_index(DurableRef(), v1)
    assert res.status is ResolutionStatus.ORPHAN
    assert "neither" in res.reason


def test_fingerprint_ignores_markup_and_whitespace_but_not_text():
    a = content_fingerprint("<p>dharmakṣetre   kurukṣetre</p>")
    b = content_fingerprint("dharmakṣetre kurukṣetre")
    c = content_fingerprint("dharmaksetre kuruksetre")
    assert a == b
    assert a != c
    assert content_fingerprint(None) == ""


def test_summarise_counts_every_status(tmp_path):
    v1 = _index(tmp_path, "v1.db", "v2026.01", LINES_V1)
    refs = [
        DurableRef(source_slug="bhagavadgita-1909", canonical_id="bhagavadgita-1909:1.1"),
        DurableRef(),
    ]
    counts = summarise(resolve_against_index(r, v1) for r in refs)
    assert counts["canonical"] == 1
    assert counts["orphan"] == 1


@pytest.mark.parametrize("missing", ["slug", "canonical"])
def test_half_a_canonical_tuple_is_not_a_canonical_reference(tmp_path, missing):
    v1 = _index(tmp_path, "v1.db", "v2026.01", LINES_V1)
    ref = DurableRef(
        source_slug=None if missing == "slug" else "bhagavadgita-1909",
        canonical_id=None if missing == "canonical" else "bhagavadgita-1909:1.1",
    )
    assert not ref.has_canonical
    assert resolve_against_index(ref, v1).status is ResolutionStatus.ORPHAN
