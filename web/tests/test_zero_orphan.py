"""Zero-orphan gate, end to end (H1925, B3/B5).

Drives the two real scripts — ``backfill_canonical_refs.py`` and
``zero_orphan_report.py`` — over a corpus that is genuinely rebuilt underneath
the stored references, because the failure this lane exists to prevent only
appears when the ordinals move.

Criteria under test:

- **B3** — backfill is pinned to one corpus version, idempotent, backed up.
- **B5** — every pre-migration retained reference resolves to the same
  canonical record after the rebuild; ambiguity and orphaning fail visibly;
  rollback rehearsal proves the previous corpus still resolves everything.
"""
import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest

from canonical_fixtures import make_corpus, make_state

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


backfill_mod = _load("backfill_canonical_refs")
zero_orphan = _load("zero_orphan_report")

SOURCES_V1 = [(1, "bhagavadgita-1909", "Бхагавадгита")]
LINES_V1 = [
    (1, 1, "bhagavadgita-1909:1.1", "dharmaksetre kuruksetre"),
    (1, 2, "bhagavadgita-1909:1.2", "samjaya uvaca"),
    (1, 3, "bhagavadgita-1909:1.3", "pasyaitam pandu-putranam"),
]
# The rebuild: a line is inserted at the top and the source is re-enumerated,
# so EVERY stored (source_id, line_num) now points at a different verse.
SOURCES_V2 = [(4, "bhagavadgita-1909", "Бхагавадгита")]
LINES_V2 = [
    (4, 1, "bhagavadgita-1909:1.0", "editor's invocation"),
    (4, 2, "bhagavadgita-1909:1.1", "dharmaksetre kuruksetre"),
    (4, 3, "bhagavadgita-1909:1.2", "samjaya uvaca"),
    (4, 4, "bhagavadgita-1909:1.3", "pasyaitam pandu-putranam"),
]


@pytest.fixture
def scenario(tmp_path):
    before = make_corpus(
        tmp_path / "before.db",
        corpus_version="v2026.01",
        sources=SOURCES_V1,
        lines=LINES_V1,
    )
    candidate = make_corpus(
        tmp_path / "candidate.db",
        corpus_version="v2026.02",
        sources=SOURCES_V2,
        lines=LINES_V2,
    )
    state = make_state(
        tmp_path / "state.db",
        # `old` is the fragment the proposer saw — the backfill checks it
        # against the pinned corpus before binding an unversioned ordinal.
        corrections=[
            {"id": 1, "source_id": 1, "line_num": 1, "old": "kuruksetre"},
            {"id": 2, "source_id": 1, "line_num": 3, "old": "pandu-putranam"},
        ],
    )
    return before, candidate, state


def _corrections(state):
    conn = sqlite3.connect(state)
    conn.row_factory = sqlite3.Row
    try:
        return {r["id"]: dict(r) for r in conn.execute("SELECT * FROM corrections")}
    finally:
        conn.close()


def test_backfill_pins_references_to_the_corpus_they_were_recorded_against(scenario):
    before, _candidate, state = scenario
    report = backfill_mod.backfill(before, state, apply=True)

    assert report["corpus_version"] == "v2026.01"
    assert report["legacy_map_rows"] == 3
    assert report["corrections_resolved"] == 2
    assert report["corrections_unresolved"] == 0
    assert Path(report["backup"]).exists()

    rows = _corrections(state)
    assert rows[1]["canonical_id"] == "bhagavadgita-1909:1.1"
    assert rows[2]["canonical_id"] == "bhagavadgita-1909:1.3"
    assert rows[1]["corpus_version"] == "v2026.01"
    assert rows[1]["ref_status"] == "legacy_direct"


def test_backfill_is_idempotent(scenario):
    before, _candidate, state = scenario
    first = backfill_mod.backfill(before, state, apply=True)
    snapshot = _corrections(state)
    second = backfill_mod.backfill(before, state, apply=True)

    assert first["legacy_map_rows"] == second["legacy_map_rows"]
    assert first["corrections_resolved"] == 2
    # Second pass has nothing to do: an already-backfilled row is recognised,
    # not re-derived — so a later run under a different pin cannot quietly
    # rewrite provenance recorded by an earlier one.
    assert second["corrections_resolved"] == 0
    assert second["corrections_already_canonical"] == 2
    assert _corrections(state) == snapshot


def test_backfill_refuses_a_mis_pinned_corpus(tmp_path):
    """The pin is checked, not trusted: wrong corpus ⇒ unresolved, not a bind."""
    corpus = make_corpus(
        tmp_path / "other.db",
        corpus_version="v2026.99",
        sources=SOURCES_V1,
        lines=[(1, 1, "bhagavadgita-1909:9.9", "a completely different verse")],
    )
    state = make_state(
        tmp_path / "state.db",
        corrections=[{"id": 1, "source_id": 1, "line_num": 1, "old": "kuruksetre"}],
    )
    report = backfill_mod.backfill(corpus, state, apply=True)

    assert report["corrections_resolved"] == 0
    assert report["corrections_unresolved"] == 1
    assert report["unresolved"][0]["status"] == "text_mismatch"
    rows = _corrections(state)
    assert rows[1]["canonical_id"] is None
    assert rows[1]["ref_status"] == "unresolved"


def test_backfill_dry_run_writes_nothing(scenario):
    before, _candidate, state = scenario
    report = backfill_mod.backfill(before, state, apply=False)
    assert report["applied"] is False
    assert report["backup"] is None
    conn = sqlite3.connect(state)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(corrections)")}
    finally:
        conn.close()
    assert "canonical_id" not in cols  # migrations not applied either


def test_zero_orphan_passes_after_backfill_despite_shifted_ordinals(scenario):
    before, candidate, state = scenario
    backfill_mod.backfill(before, state, apply=True)

    report = zero_orphan.compare(before, candidate, state)

    assert report["references_checked"] == 2
    assert report["counts"] == {"stable": 2}
    assert report["zero_orphan"] is True
    # Proof the ordinals really did move — otherwise this test would pass
    # trivially against an unchanged corpus.
    assert report["before_lines"] == 3 and report["candidate_lines"] == 4


def test_without_backfill_the_same_references_are_reported_not_mis_bound(scenario):
    """The pre-migration state: unversioned ordinals, no canonical columns.

    They must come out as *unresolved*, never silently re-bound to the verse
    that now occupies their ordinal.
    """
    before, candidate, state = scenario
    report = zero_orphan.compare(before, candidate, state)

    assert report["counts"].get("unresolved_before") == 2
    assert report["counts"].get("identity_changed", 0) == 0


def test_deleted_passage_is_reported_as_orphaned(scenario, tmp_path):
    before, _candidate, state = scenario
    backfill_mod.backfill(before, state, apply=True)
    # A rebuild that drops 1.3 entirely.
    candidate = make_corpus(
        tmp_path / "cand_del.db",
        corpus_version="v2026.03",
        sources=SOURCES_V2,
        lines=[line for line in LINES_V2 if line[2] != "bhagavadgita-1909:1.3"],
    )
    report = zero_orphan.compare(before, candidate, state)

    assert report["counts"].get("orphaned") == 1
    assert report["zero_orphan"] is False


def test_duplicate_canonical_id_in_the_rebuild_is_reported_as_ambiguous(scenario, tmp_path):
    before, _candidate, state = scenario
    backfill_mod.backfill(before, state, apply=True)
    candidate = make_corpus(
        tmp_path / "cand_dup.db",
        corpus_version="v2026.04",
        sources=SOURCES_V2,
        lines=LINES_V2 + [(4, 5, "bhagavadgita-1909:1.1", "duplicated anchor")],
    )
    report = zero_orphan.compare(before, candidate, state)

    assert report["counts"].get("ambiguous") == 1
    assert report["zero_orphan"] is False


def test_edited_text_is_content_changed_not_a_failure(scenario, tmp_path):
    before, _candidate, state = scenario
    backfill_mod.backfill(before, state, apply=True)
    edited = [
        (4, 2, "bhagavadgita-1909:1.1", "dharmaksetre kuruksetre CORRECTED")
        if line[2] == "bhagavadgita-1909:1.1"
        else line
        for line in LINES_V2
    ]
    candidate = make_corpus(
        tmp_path / "cand_edit.db",
        corpus_version="v2026.05",
        sources=SOURCES_V2,
        lines=edited,
    )
    report = zero_orphan.compare(before, candidate, state)

    assert report["counts"].get("content_changed") == 1
    assert report["counts"].get("stable") == 1
    # A text correction must not fail the gate — correcting text is the point.
    assert report["zero_orphan"] is True


def test_markup_only_change_is_stable(scenario, tmp_path):
    before, _candidate, state = scenario
    backfill_mod.backfill(before, state, apply=True)
    remarked = [
        (sid, num, cid, f"  {text}  ") for (sid, num, cid, text) in LINES_V2
    ]
    candidate = make_corpus(
        tmp_path / "cand_markup.db",
        corpus_version="v2026.06",
        sources=SOURCES_V2,
        lines=remarked,
    )
    report = zero_orphan.compare(before, candidate, state)
    assert report["counts"] == {"stable": 2}


def test_rollback_rehearsal_resolves_everything_in_the_previous_corpus(scenario):
    before, _candidate, state = scenario
    backfill_mod.backfill(before, state, apply=True)
    rehearsal = zero_orphan.compare(before, before, state)
    assert rehearsal["fatal"] == 0
    assert rehearsal["counts"] == {"stable": 2}


def test_restore_recovers_state_after_a_bad_backfill(scenario):
    before, _candidate, state = scenario
    report = backfill_mod.backfill(before, state, apply=True)

    conn = sqlite3.connect(state)
    conn.execute("UPDATE corrections SET canonical_id = 'wrong:9.9'")
    conn.commit()
    conn.close()

    backfill_mod.restore_state_db(report["backup"], state)
    rows = _corrections(state)
    # The backup is taken BEFORE the canonical writes, so recovery lands on the
    # pre-backfill state — recoverable, which is what B3 requires.
    assert rows[1]["canonical_id"] in (None, "")
