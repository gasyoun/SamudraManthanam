"""D7 acceptance — the categorised dup-suffix invariant (H1927), hermetic.

VERIFICATION D7: "Duplicate-suffix validation uses a categorised invariant, not
an unexplained stale count ceiling."

`test_converter.py::test_gate4_dup_suffix_invariants_hold` runs the invariant
against the real corpus and is `@pytest.mark.corpus`, so it does not run on an
ordinary PR. These tests run always, on synthetic records, and their job is to
prove the invariants are *capable* — specifically that they catch the H1829 bug
shape, which the count ceiling they replace did not.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from dup_suffix_report import (  # noqa: E402
    CONCENTRATION_MIN_POPULATION,
    POPULATION_BACKSTOP,
    build_report,
)


def rec(rid, work, seg="ru"):
    return {"id": rid, "work": work, "seg": seg, "passage": rid.split(":", 1)[-1]}


def healthy_pair(work, passage):
    """A genuine collision: base + 'b', both segments present."""
    return [
        rec(f"{work}:{passage}#sa", work, "sa"),
        rec(f"{work}:{passage}#ru", work, "ru"),
        rec(f"{work}:{passage}b#sa", work, "sa"),
        rec(f"{work}:{passage}b#ru", work, "ru"),
    ]


def test_genuine_collisions_pass():
    records = healthy_pair("gita", "1.1") + healthy_pair("gita", "2.4")
    report = build_report(records)
    assert report.dup_records == 4
    assert report.ok, [v.detail for v in report.violations]


def test_orphaned_suffix_is_caught():
    """The H1829 signature: a 'b' with no base — an invented boundary.

    The count ceiling could never see this; a handful of orphans is far under
    any threshold. This is the single most important invariant here.
    """
    records = [rec("nirvana-tantra:5.9b#ru", "nirvana-tantra")]
    report = build_report(records)
    violations = report.violations_for("base_present")
    assert len(violations) == 1
    assert "invented" in violations[0].detail


def test_suffix_run_is_caught():
    records = [
        rec("x:1.1#ru", "x"),
        rec("x:1.1b#ru", "x"),
        rec("x:1.1c#ru", "x"),
        rec("x:1.1d#ru", "x"),
    ]
    report = build_report(records)
    caught = {v.record_id for v in report.violations_for("suffix_depth")}
    assert caught == {"x:1.1c#ru", "x:1.1d#ru"}


def test_unexpected_segment_is_caught():
    records = [rec("x:1.1#nav", "x", "nav"), rec("x:1.1b#nav", "x", "nav")]
    report = build_report(records)
    assert report.violations_for("segment_pairing")


def test_commentary_suffix_is_allowed():
    """`.comm` records legitimately carry a suffix and are not sa/ru."""
    records = [rec("x:1.1.comm", "x", "comm"), rec("x:1.1b.comm", "x", "comm")]
    report = build_report(records)
    assert not report.violations_for("segment_pairing")


def test_h1829_concentration_shape_is_caught():
    """Reproduce the real bug's proportions: one work holding ~79%.

    Every pair here is individually well-formed — base present, suffix 'b',
    proper segments. Only the *distribution* is wrong, which is exactly what
    made the original bug survive a per-record check.
    """
    records = []
    for i in range(40):  # 160 dup records in one work
        records += healthy_pair("nirvana-tantra", f"5.{i}")
    for i in range(5):  # 20 elsewhere
        records += healthy_pair("gita", f"1.{i}")

    report = build_report(records)
    assert report.dup_records >= CONCENTRATION_MIN_POPULATION
    violations = report.violations_for("concentration")
    assert violations, "the 79%-in-one-work shape was not caught"
    assert "nirvana-tantra" in violations[0].work


def test_concentration_is_not_applied_to_a_tiny_population():
    """A single legitimate multi-verse work must not be flagged as runaway."""
    records = healthy_pair("gita", "1.1")
    report = build_report(records)
    assert report.dup_records < CONCENTRATION_MIN_POPULATION
    assert not report.violations_for("concentration")


def test_backstop_prompts_rederivation_rather_than_hiding_a_bug():
    """The count is retained, but only as a prompt — and it says so."""
    records = []
    works = [f"work-{i}" for i in range(40)]
    per_work = (POPULATION_BACKSTOP // len(works)) + 2
    for work in works:
        for i in range(per_work):
            records += healthy_pair(work, f"1.{i}")

    report = build_report(records)
    assert report.dup_records > POPULATION_BACKSTOP
    violations = report.violations_for("population_backstop")
    assert violations
    assert "re-derive" in violations[0].detail
    # And it is the ONLY complaint — the structural invariants are all satisfied.
    assert {v.invariant for v in report.violations} == {"population_backstop"}


def test_report_counts_are_reported_even_when_passing():
    records = healthy_pair("gita", "1.1")
    report = build_report(records)
    assert report.by_suffix == {"b": 2}
    assert report.by_segment == {"sa": 1, "ru": 1}
    assert report.by_work == {"gita": 2}
    assert report.to_dict()["ok"] is True


def test_lfs_pointer_is_refused_not_silently_skipped(tmp_path):
    """An unreadable source must fail loudly, never shrink the population.

    dic_mw.jsonl is LFS-tracked, so a checkout without LFS leaves a pointer
    stub. Skipping it would let the gate report a full-corpus pass over a
    corpus it never read — the false-passing shape this whole report replaces.
    """
    from dup_suffix_report import CorpusUnavailableError, load_records

    stub = tmp_path / "dic_mw.jsonl"
    stub.write_text(
        "version https://git-lfs.github.com/spec/v1\n"
        "oid sha256:0000000000000000000000000000000000000000000000000000000000000000\n"
        "size 12345\n",
        encoding="utf-8",
    )
    with pytest.raises(CorpusUnavailableError, match="Git LFS pointer"):
        load_records([stub])


def test_malformed_jsonl_line_is_refused(tmp_path):
    from dup_suffix_report import CorpusUnavailableError, load_records

    bad = tmp_path / "broken.jsonl"
    bad.write_text('{"id": "x:1.1#ru", "work": "x"}\nnot json at all\n', encoding="utf-8")
    with pytest.raises(CorpusUnavailableError, match="not valid JSON"):
        load_records([bad])


@pytest.mark.parametrize(
    "rid,is_dup",
    [
        ("x:1.1b#ru", True),
        ("x:1.1b.comm", True),
        ("x:1.1#ru", False),
        ("x:1.1a#ru", False),  # 'a' is not a disambiguation suffix
        ("x:1.1#ruby", False),  # a letter in the tail is not a suffix
    ],
)
def test_dup_id_pattern_boundaries(rid, is_dup):
    from dup_suffix_report import DUP_ID_RE

    assert bool(DUP_ID_RE.match(rid)) is is_dup
