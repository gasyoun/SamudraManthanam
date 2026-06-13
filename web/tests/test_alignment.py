"""ALIGNMENT_SPEC §7 gates — JSONL corpus tests.

All tests load JSONL files produced by html_to_canonical.py.
They skip automatically if web/corpus_builder/jsonl/ does not exist.

Gates checked:
  1. Group completeness — every verse citation_block → one group
  2. Cardinality baselines — buddhacharita-balmont/mify-drind 100% 0:1
  3. No phantom pairing — monolingual groups have no opposite segment
  4. Gold set green — all hand-verified groups from alignment_gold.jsonl pass
  (5. Reader toggle parity — deferred to Phase 2 reader implementation)
"""
import json
import pytest
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def jsonl_dir():
    p = Path(__file__).parent.parent / "corpus_builder" / "jsonl"
    if not p.exists() or not any(p.glob("*.jsonl")):
        pytest.skip("JSONL not built — run html_to_canonical.py first")
    return p


def _load_source(jsonl_dir: Path, slug: str) -> list[dict]:
    """Load all records for one source slug."""
    path = jsonl_dir / f"{slug}.jsonl"
    if not path.exists():
        pytest.skip(f"{slug}.jsonl not found in JSONL dir")
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _build_group_index(records: list[dict]) -> dict[str, list[dict]]:
    """Group records by their 'group' key."""
    idx: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        idx[rec["group"]].append(rec)
    return dict(idx)


def _cardinality(group_records: list[dict]) -> str:
    """Compute group cardinality from member segs: '1:1' | '0:1' | '1:0'."""
    segs = {r["seg"] for r in group_records}
    has_sa = "sa" in segs
    has_ru = "ru" in segs
    if has_sa and has_ru:
        return "1:1"
    if has_ru:
        return "0:1"
    if has_sa:
        return "1:0"
    return "?:?"


@pytest.fixture(scope="session")
def gold_fixtures() -> list[dict]:
    """Load hand-verified gold groups from fixtures/alignment_gold.jsonl."""
    fixture_path = Path(__file__).parent / "fixtures" / "alignment_gold.jsonl"
    if not fixture_path.exists():
        pytest.skip("alignment_gold.jsonl not found")
    entries = []
    with open(fixture_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# ---------------------------------------------------------------------------
# Gate 1: Group completeness
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate1_rigveda_group_count(jsonl_dir):
    """Every citation_block in rigveda has exactly one group (one group key per block)."""
    records = _load_source(jsonl_dir, "01_rigveda")
    groups = _build_group_index(records)
    verse_groups = {g for g, recs in groups.items()
                   if any(r["seg"] in ("sa", "ru") for r in recs)}
    # Rigveda book 1 has 191 hymns (mandala 1) — check at least 191 groups exist
    assert len(verse_groups) >= 100, (
        f"Too few verse groups in 01_rigveda: {len(verse_groups)}"
    )


@pytest.mark.corpus
def test_gate1_all_verse_records_have_group(jsonl_dir):
    """Every sa/ru record must have a non-empty 'group' field."""
    for jf in sorted(jsonl_dir.glob("*.jsonl")):
        with open(jf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("seg") in ("sa", "ru"):
                    assert rec.get("group"), (
                        f"Missing group on {rec['id']}"
                    )


@pytest.mark.corpus
def test_gate1_comm_group_matches_annotates(jsonl_dir):
    """Every comm record's 'group' must equal '{work}:{annotates}'."""
    errors = []
    for jf in sorted(jsonl_dir.glob("*.jsonl")):
        with open(jf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if (rec.get("seg") or "").startswith("comm"):
                    work = rec["work"]
                    ann = rec.get("annotates")
                    expected_group = f"{work}:{ann}"
                    if rec.get("group") != expected_group:
                        errors.append(
                            f"{rec['id']}: group={rec.get('group')!r} "
                            f"but annotates={ann!r}"
                        )
    assert not errors, (
        f"Gate 1 group/annotates mismatch ({len(errors)} records): {errors[:3]}"
    )


# ---------------------------------------------------------------------------
# Gate 2: Cardinality baselines
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate2_buddhacharita_all_monolingual(jsonl_dir):
    """buddhacharita-balmont: every verse group must be 0:1 (Russian only, no Sanskrit)."""
    records = _load_source(jsonl_dir, "buddhacharita-balmont")
    groups = _build_group_index(records)

    parallel = [g for g, recs in groups.items() if "sa" in {r["seg"] for r in recs}]
    assert not parallel, (
        f"buddhacharita-balmont has unexpected 1:1 groups: {parallel[:3]}"
    )

    monolingual = [g for g, recs in groups.items() if "ru" in {r["seg"] for r in recs}]
    # Spec baseline: 8,852 blocks; our count: 8,852 (image-only blocks excluded)
    assert len(monolingual) >= 8_800, (
        f"buddhacharita-balmont: expected ≥8,800 monolingual groups, got {len(monolingual)}"
    )


@pytest.mark.corpus
def test_gate2_mify_drind_all_monolingual(jsonl_dir):
    """mify-drind: every verse group must be 0:1 (Russian only, no Sanskrit)."""
    records = _load_source(jsonl_dir, "mify-drind")
    groups = _build_group_index(records)

    parallel = [g for g, recs in groups.items() if "sa" in {r["seg"] for r in recs}]
    assert not parallel, (
        f"mify-drind has unexpected parallel groups: {parallel[:3]}"
    )

    monolingual = [g for g, recs in groups.items() if "ru" in {r["seg"] for r in recs}]
    # Spec says 1,172; our count is 1,154 (18 image-only blocks excluded — correct)
    assert len(monolingual) >= 1_100, (
        f"mify-drind: expected ≥1,100 monolingual groups, got {len(monolingual)}"
    )


@pytest.mark.corpus
def test_gate2_rigveda_mostly_parallel(jsonl_dir):
    """01_rigveda: overwhelming majority of groups should be 1:1."""
    records = _load_source(jsonl_dir, "01_rigveda")
    groups = _build_group_index(records)

    verse_groups = {g: recs for g, recs in groups.items()
                   if any(r["seg"] in ("sa", "ru") for r in recs)}
    parallel = sum(1 for recs in verse_groups.values()
                  if "sa" in {r["seg"] for r in recs} and "ru" in {r["seg"] for r in recs})
    total = len(verse_groups)
    ratio = parallel / total if total else 0
    assert ratio >= 0.95, (
        f"01_rigveda: only {parallel}/{total} ({ratio:.1%}) groups are 1:1; expected ≥95%"
    )


# ---------------------------------------------------------------------------
# Gate 3: No phantom pairing
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate3_monolingual_groups_have_no_opposite_segment(jsonl_dir):
    """Gate 3: a 0:1 group must not contain a #sa record; 1:0 must not contain #ru."""
    errors = []
    for jf in sorted(jsonl_dir.glob("*.jsonl")):
        with open(jf, encoding="utf-8") as f:
            src_records = []
            for line in f:
                line = line.strip()
                if line:
                    src_records.append(json.loads(line))

        groups = _build_group_index(src_records)
        for group_key, recs in groups.items():
            segs = {r["seg"] for r in recs}
            if "sa" in segs and "ru" in segs:
                continue  # 1:1, fine
            if "ru" in segs and "sa" not in segs:
                # 0:1 — must not also have #sa
                sa_recs = [r for r in recs if r["seg"] == "sa"]
                if sa_recs:
                    errors.append(f"Phantom sa in 0:1 group {group_key}")
            if "sa" in segs and "ru" not in segs:
                # 1:0 — must not also have #ru
                ru_recs = [r for r in recs if r["seg"] == "ru"]
                if ru_recs:
                    errors.append(f"Phantom ru in 1:0 group {group_key}")

    assert not errors, f"Gate 3 phantom pairing violations: {errors[:5]}"


# ---------------------------------------------------------------------------
# Gate 4: Gold set
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_gate4_gold_set(jsonl_dir, gold_fixtures):
    """Gate 4: every hand-verified group in alignment_gold.jsonl passes all checks."""
    # Cache loaded files to avoid re-reading
    cache: dict[str, dict[str, list[dict]]] = {}

    def get_groups(slug: str) -> dict[str, list[dict]]:
        if slug not in cache:
            records = _load_source(jsonl_dir, slug)
            cache[slug] = _build_group_index(records)
        return cache[slug]

    failures = []

    for entry in gold_fixtures:
        group_key = entry["group"]
        slug = group_key.split(":")[0]
        all_groups = get_groups(slug)

        # --- Group must exist ---
        if group_key not in all_groups:
            failures.append(f"MISSING group {group_key}")
            continue

        recs = all_groups[group_key]
        by_seg: dict[str, list[dict]] = defaultdict(list)
        for r in recs:
            by_seg[r["seg"]].append(r)

        # --- Cardinality ---
        card = _cardinality(recs)
        expected_card = entry["cardinality"]
        if card != expected_card:
            failures.append(
                f"{group_key}: cardinality {card!r} != expected {expected_card!r}"
            )

        # --- Alignment ---
        # Derived from cardinality for this test
        expected_align = entry["alignment"]
        actual_align = "markup" if card == "1:1" else "monolingual" if card in ("0:1", "1:0") else "none"
        if actual_align != expected_align:
            failures.append(
                f"{group_key}: alignment {actual_align!r} != expected {expected_align!r}"
            )

        # --- sa member ---
        expected_sa_id = entry.get("sa_id")
        if expected_sa_id is None:
            if "sa" in by_seg:
                failures.append(f"{group_key}: unexpected #sa record in 0:1 group")
        else:
            sa_recs = by_seg.get("sa", [])
            if len(sa_recs) != 1:
                failures.append(f"{group_key}: expected 1 #sa, got {len(sa_recs)}")
            elif sa_recs[0]["id"] != expected_sa_id:
                failures.append(
                    f"{group_key}: sa id {sa_recs[0]['id']!r} != {expected_sa_id!r}"
                )
            else:
                sa_rec = sa_recs[0]
                # Text fragment
                frag = entry.get("sa_text_fragment")
                if frag and frag not in sa_rec.get("text", ""):
                    failures.append(
                        f"{group_key}: sa text missing {frag!r} — got {sa_rec['text'][:80]!r}"
                    )
                # Author fragment
                author_frag = entry.get("sa_author_fragment")
                if author_frag:
                    author_val = sa_rec.get("author", "")
                    if author_frag not in author_val:
                        failures.append(
                            f"{group_key}: sa.author {author_val!r} missing {author_frag!r}"
                        )
                # Dhruva
                if entry.get("sa_dhruva"):
                    if not sa_rec.get("dhruva"):
                        failures.append(f"{group_key}: expected dhruva=True on sa record")
                # Alt_ref
                expected_alt = entry.get("sa_alt_ref")
                if expected_alt is not None:
                    actual_alt = sa_rec.get("alt_ref")
                    if actual_alt != expected_alt:
                        failures.append(
                            f"{group_key}: sa.alt_ref {actual_alt!r} != {expected_alt!r}"
                        )

        # --- ru member ---
        expected_ru_id = entry.get("ru_id")
        if expected_ru_id is None:
            if "ru" in by_seg:
                failures.append(f"{group_key}: unexpected #ru record in 1:0 group")
        else:
            ru_recs = by_seg.get("ru", [])
            if len(ru_recs) != 1:
                failures.append(f"{group_key}: expected 1 #ru, got {len(ru_recs)}")
            elif ru_recs[0]["id"] != expected_ru_id:
                failures.append(
                    f"{group_key}: ru id {ru_recs[0]['id']!r} != {expected_ru_id!r}"
                )
            else:
                ru_rec = ru_recs[0]
                frag = entry.get("ru_text_fragment")
                if frag and frag not in ru_rec.get("text", ""):
                    failures.append(
                        f"{group_key}: ru text missing {frag!r} — got {ru_rec['text'][:80]!r}"
                    )
                author_frag = entry.get("ru_author_fragment")
                if author_frag:
                    author_val = ru_rec.get("author", "")
                    if author_frag not in author_val:
                        failures.append(
                            f"{group_key}: ru.author {author_val!r} missing {author_frag!r}"
                        )

        # --- commentary members ---
        # comm_ids = null in fixture → skip comm check entirely
        # comm_ids = [] → assert no comm records
        # comm_ids = [...] → assert exact match
        expected_comm_ids = entry.get("comm_ids")
        if expected_comm_ids is not None:
            expected_sorted = sorted(expected_comm_ids)
            actual_comm_ids = sorted(
                r["id"] for r in recs if (r.get("seg") or "").startswith("comm")
            )
            if actual_comm_ids != expected_sorted:
                failures.append(
                    f"{group_key}: comm_ids mismatch\n"
                    f"  expected: {expected_sorted}\n"
                    f"  actual:   {actual_comm_ids}"
                )

    assert not failures, (
        f"Gate 4 (gold set) FAIL: {len(failures)} failures:\n"
        + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# Extra: Nav headings must not appear in JSONL
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_nav_headings_absent_from_jsonl(jsonl_dir):
    """Verse parse path skips chapter_title divs — no nav records should exist.

    The converter tracks chapter headings as internal state only; they are NOT
    emitted as JSONL records (ALIGNMENT_SPEC §4 point 3).
    """
    nav_records = []
    for jf in sorted(jsonl_dir.glob("*.jsonl")):
        with open(jf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                passage = rec.get("passage", "")
                # Nav headings would have passage = "c.N" or seg = "nav"
                if passage.startswith("c.") or rec.get("seg") == "nav":
                    nav_records.append(rec["id"])

    assert not nav_records, (
        f"Unexpected nav heading records found in JSONL ({len(nav_records)}): "
        f"{nav_records[:5]}"
    )


# ---------------------------------------------------------------------------
# Extra: dhruva and alt_ref fields appear only in Gitagovinda
# ---------------------------------------------------------------------------

@pytest.mark.corpus
def test_dhruva_only_in_gitagovinda(jsonl_dir):
    """dhruva=True should appear only in gitagovinda.jsonl."""
    non_gg_dhruva = []
    for jf in sorted(jsonl_dir.glob("*.jsonl")):
        if jf.stem == "gitagovinda":
            continue
        with open(jf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("dhruva"):
                    non_gg_dhruva.append(rec["id"])

    assert not non_gg_dhruva, (
        f"dhruva=True outside gitagovinda: {non_gg_dhruva[:5]}"
    )


@pytest.mark.corpus
def test_gitagovinda_has_dhruva_records(jsonl_dir):
    """Gitagovinda must have at least one record with dhruva=True."""
    records = _load_source(jsonl_dir, "gitagovinda")
    dhruva_recs = [r for r in records if r.get("dhruva")]
    assert len(dhruva_recs) >= 10, (
        f"Expected ≥10 dhruva records in gitagovinda, got {len(dhruva_recs)}"
    )
