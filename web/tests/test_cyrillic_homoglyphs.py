"""Regression guard for issue #16: Cyrillic homoglyphs (с/а etc.) leaking into
Sanskrit-IAST ('sa') corpus segments. Hermetic — scans the checked-in jsonl
source directly, no corpus.db required.
"""
import glob
import json
import os
import sys

import pytest

CORPUS_BUILDER = os.path.join(os.path.dirname(__file__), "..", "corpus_builder")
sys.path.insert(0, CORPUS_BUILDER)

from scan_cyrillic_homoglyphs import scan_record  # noqa: E402

JSONL_DIR = os.path.join(CORPUS_BUILDER, "jsonl")

EXPECTED_ISSUE_16_WORDS = {
    "05_ramayana-sundarakanda:1.35#sa": "saṃcukoca",
    "05_ramayana-sundarakanda:22.25#sa": "calāgramukuṭaprāṃśuś",
    "05_ramayana-sundarakanda:31.4#sa": "cekṣvākuvaṃśasya",
    "05_ramayana-sundarakanda:37.12#sa": "chīlavān",
    "yoga-sutry:4.8#sa": "tad-vipāka-anuguṇānām",
    "yoga-sutry_sharma:4.8#sa": "tad-vipāka-anuguṇānām",
    "yoga-sutry_zagumennov:4.8#sa": "tad-vipāka-anuguṇānām",
}


def _iter_sa_records():
    # Cheap substring pre-filter avoids json.loads on the ~50% of lines that
    # are 'ru' segments — those are never in scope for this homoglyph check.
    for path in sorted(glob.glob(os.path.join(JSONL_DIR, "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                if '"seg": "sa"' not in line:
                    continue
                s = line.strip()
                if not s:
                    continue
                rec = json.loads(s)
                if rec.get("seg") == "sa":
                    yield path, lineno, rec


@pytest.fixture(scope="module")
def sa_records():
    return list(_iter_sa_records())


def test_no_cyrillic_homoglyphs_in_sa_segments(sa_records):
    offenders = []
    for path, lineno, rec in sa_records:
        homoglyphs, _russian_runs = scan_record(rec)
        if homoglyphs:
            offenders.append((os.path.relpath(path), lineno, rec.get("id"), homoglyphs))
    assert not offenders, (
        f"Cyrillic homoglyph(s) found in #sa corpus segments: {offenders}"
    )


def test_known_issue_16_words_are_clean(sa_records):
    # The words named in issue #16 must round-trip to their Latin form.
    seen = set()
    for _path, _lineno, rec in sa_records:
        rid = rec.get("id")
        if rid in EXPECTED_ISSUE_16_WORDS:
            seen.add(rid)
            expected = EXPECTED_ISSUE_16_WORDS[rid]
            assert expected in rec.get("text", ""), (
                f"{rid}: expected Latin form {expected!r} not found in {rec.get('text')!r}"
            )
    missing = set(EXPECTED_ISSUE_16_WORDS) - seen
    assert not missing, f"missing expected #sa records: {missing}"
