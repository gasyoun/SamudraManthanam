"""Lane A acceptance tests — canonical manifest and immutable bundle.

Each test names the criterion from
[VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md)
it proves, so a failure points at the contract it broke rather than at a helper.

All tests are hermetic: they build a throwaway bundle under `tmp_path` and never
read the real 521 MB corpus.
"""
import copy
import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from corpus_builder.build_report import agree_on_input, load_report, validate_report
from corpus_builder.corpus_manifest import (
    ManifestError,
    build_manifest,
    canonical_json,
    content_hash,
    diff_manifests,
    enumerate_from_jsonl_dir,
    inspect_jsonl,
    load_manifest,
    validate_manifest,
    write_manifest,
)
from ingest.publish import corpus_identity, publish, restore_backup

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "corpus_bundle"


# ── bundle scaffolding ───────────────────────────────────────────────────────

@pytest.fixture
def bundle(tmp_path: Path):
    """A minimal, self-contained corpus bundle on disk.

    Layout mirrors the real one: `<repo>/web/` is the corpus root, canonical
    JSONL lives under it, and a legacy desktop tree sits alongside so tests can
    show that publication follows the manifest rather than that tree.
    """
    repo_root = tmp_path / "repo"
    corpus_root = repo_root / "web"
    jsonl_dir = corpus_root / "jsonl"
    jsonl_dir.mkdir(parents=True)

    for name in ("fixture-alpha.jsonl", "fixture-beta.jsonl", "fixture-beta.meta.json"):
        shutil.copy(FIXTURE_DIR / name, jsonl_dir / name)

    # Legacy desktop tree — deliberately stale relative to the JSONL, so any
    # test that accidentally reads it produces visibly different content.
    data_dir = repo_root / "corpus" / "Data"
    program_dir = repo_root / "corpus" / "Programdata"
    data_dir.mkdir(parents=True)
    program_dir.mkdir(parents=True)
    for slug in ("fixture-alpha", "fixture-beta"):
        (data_dir / f"{slug}.html").write_text(
            f"<!-- STALE HTML TITLE for {slug} -->\n<p>stale desktop body</p>\n",
            encoding="utf-8",
        )
    (program_dir / "data.txt").write_text(
        "fixture-alpha.html\nfixture-beta.html\n", encoding="utf-8"
    )

    return {
        "repo_root": repo_root,
        "corpus_root": corpus_root,
        "jsonl_dir": jsonl_dir,
        "corpus_path": repo_root / "corpus",
    }


def make_manifest(bundle, version="test-1", revision="testrev"):
    sources = enumerate_from_jsonl_dir(bundle["jsonl_dir"])
    return build_manifest(
        sources,
        bundle_version=version,
        corpus_root=bundle["corpus_root"],
        repo_root=bundle["repo_root"],
        revision=revision,
    )


def write_bundle_manifest(bundle, version="test-1", revision="testrev") -> Path:
    manifest = make_manifest(bundle, version=version, revision=revision)
    path = bundle["corpus_root"] / "corpus-manifest.json"
    write_manifest(manifest, path)
    return path


def mutate_one_byte(path: Path) -> None:
    """Flip a single character of text inside a JSONL record.

    A one-character edit inside a string value keeps the file valid JSON with an
    unchanged record count — so only the hash can catch it. That is the point.
    """
    text = path.read_text(encoding="utf-8")
    assert "svasti" in text, "fixture changed; pick another token to mutate"
    path.write_text(text.replace("svasti", "svastj", 1), encoding="utf-8")


# ── A1 — schema rejects incomplete manifests ─────────────────────────────────

def test_a1_valid_manifest_passes_schema(bundle):
    report = validate_manifest(make_manifest(bundle), repo_root=bundle["repo_root"])
    assert report.ok, report.errors
    assert report.stats["files_verified"] == 2


@pytest.mark.parametrize(
    "path,label",
    [
        (("bundle", "sources", 0, "slug"), "identity"),
        (("bundle", "sources", 0, "canonical", "sha256"), "hash"),
        (("bundle", "sources", 0, "canonical", "record_count"), "count"),
        (("bundle", "sources", 0, "provenance"), "provenance"),
        (("bundle", "bundle_version"), "version"),
        (("schema_version",), "schema version"),
        (("content_hash",), "content hash"),
    ],
)
def test_a1_schema_rejects_missing_required_field(bundle, path, label):
    manifest = make_manifest(bundle)
    node = manifest
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]

    report = validate_manifest(manifest, repo_root=bundle["repo_root"], check_files=False)
    assert not report.ok, f"manifest missing {label} was accepted"


def test_a1_schema_rejects_absolute_and_traversing_paths(bundle):
    for bad in ("/etc/passwd", "../outside/file.jsonl", "web/../../escape.jsonl"):
        manifest = make_manifest(bundle)
        manifest["bundle"]["sources"][0]["canonical"]["path"] = bad
        manifest["content_hash"] = content_hash(manifest["bundle"])
        report = validate_manifest(manifest, repo_root=bundle["repo_root"], check_files=False)
        assert not report.ok, f"path {bad!r} was accepted"


def test_a1_rejects_duplicate_slug_and_wrong_totals(bundle):
    manifest = make_manifest(bundle)
    manifest["bundle"]["sources"][1]["slug"] = manifest["bundle"]["sources"][0]["slug"]
    manifest["content_hash"] = content_hash(manifest["bundle"])
    report = validate_manifest(manifest, repo_root=bundle["repo_root"], check_files=False)
    assert not report.ok
    assert any("duplicate slug" in e for e in report.errors)

    manifest = make_manifest(bundle)
    manifest["bundle"]["totals"]["record_count"] += 1
    manifest["content_hash"] = content_hash(manifest["bundle"])
    report = validate_manifest(manifest, repo_root=bundle["repo_root"], check_files=False)
    assert not report.ok
    assert any("totals.record_count" in e for e in report.errors)


def test_a1_tampered_content_hash_is_caught(bundle):
    manifest = make_manifest(bundle)
    # Change content but leave the recorded hash untouched — the exact shape of
    # a hand-edited manifest.
    manifest["bundle"]["sources"][0]["title"] = "silently retitled"
    report = validate_manifest(manifest, repo_root=bundle["repo_root"], check_files=False)
    assert not report.ok
    assert any("content_hash mismatch" in e for e in report.errors)


def test_a1_deleted_records_are_not_counted(bundle):
    stats = inspect_jsonl(bundle["jsonl_dir"] / "fixture-alpha.jsonl")
    # The fixture has four records, one tombstoned; the manifest must count the
    # three that will actually be inserted.
    assert stats.record_count == 3
    assert stats.first_canonical_id == "alpha.1.1"


def test_a1_pipeline_intermediates_are_excluded_and_reported(bundle, capsys):
    """`<slug>.raw.jsonl` is converter input, not a publishable source.

    Found by running the builder against the real JSONL directory, where 22
    intermediates would otherwise have entered the bundle as sources with
    schema-invalid slugs.
    """
    (bundle["jsonl_dir"] / "fixture-alpha.raw.jsonl").write_text(
        '{"id": "raw.1", "seq": 1, "text": "unconverted", "html": "<p>x</p>"}\n',
        encoding="utf-8",
    )
    manifest = make_manifest(bundle)
    slugs = [s["slug"] for s in manifest["bundle"]["sources"]]
    assert slugs == ["fixture-alpha", "fixture-beta"]
    # The exclusion is announced, never silent.
    assert "fixture-alpha.raw.jsonl" in capsys.readouterr().out


def test_a1_empty_jsonl_is_refused(bundle):
    """A source with no live records cannot enter a bundle at all."""
    (bundle["jsonl_dir"] / "fixture-empty.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(ManifestError, match="no live records"):
        make_manifest(bundle)


# ── A2 — determinism ─────────────────────────────────────────────────────────

def test_a2_two_builds_from_identical_inputs_are_byte_identical(bundle, tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    write_manifest(make_manifest(bundle), first)
    write_manifest(make_manifest(bundle), second)

    assert first.read_bytes() == second.read_bytes()
    assert load_manifest(first)["content_hash"] == load_manifest(second)["content_hash"]


def test_a2_manifest_carries_no_wall_clock_field(bundle):
    """A timestamp anywhere in the document would defeat the test above."""
    text = canonical_json(make_manifest(bundle)).lower()
    for forbidden in ("generated_at", "timestamp", "built_at", "created_at"):
        assert forbidden not in text, f"{forbidden} makes rebuilds non-reproducible"


def test_a2_content_hash_ignores_build_revision(bundle):
    """Same content at a new revision keeps one identity — what A6 joins on."""
    a = make_manifest(bundle, revision="aaaaaaa")
    b = make_manifest(bundle, revision="bbbbbbb")
    assert a["build"]["revision"] != b["build"]["revision"]
    assert a["content_hash"] == b["content_hash"]


def test_a2_source_order_is_stable_and_checked(bundle):
    manifest = make_manifest(bundle)
    manifest["bundle"]["sources"].reverse()
    manifest["content_hash"] = content_hash(manifest["bundle"])
    report = validate_manifest(manifest, repo_root=bundle["repo_root"], check_files=False)
    assert not report.ok
    assert any("deterministic" in e for e in report.errors)


# ── A3 — a one-byte mutation fails before ingest ─────────────────────────────

def test_a3_one_byte_mutation_fails_hash_validation(bundle):
    manifest = make_manifest(bundle)
    mutate_one_byte(bundle["jsonl_dir"] / "fixture-alpha.jsonl")

    report = validate_manifest(manifest, repo_root=bundle["repo_root"], check_files=True)
    assert not report.ok
    assert any("sha256 mismatch" in e for e in report.errors)
    # The record count is unchanged, so a count-only check would have passed.
    assert not any("record" in e for e in report.errors)


def test_a3_mutation_aborts_ingest_before_any_row_is_written(bundle, tmp_path):
    from ingest.ingest import _enumerate_from_manifest

    manifest = make_manifest(bundle)
    mutate_one_byte(bundle["jsonl_dir"] / "fixture-alpha.jsonl")

    with pytest.raises(ValueError, match="sha256 mismatch"):
        _enumerate_from_manifest(manifest, bundle["repo_root"])


def test_a3_stale_record_count_is_caught_even_when_hash_matches(bundle):
    """A manifest can be internally consistent and still lie about a file."""
    manifest = make_manifest(bundle)
    manifest["bundle"]["sources"][0]["canonical"]["record_count"] = 99
    manifest["bundle"]["totals"]["record_count"] = sum(
        s["canonical"]["record_count"] for s in manifest["bundle"]["sources"]
    )
    manifest["content_hash"] = content_hash(manifest["bundle"])

    manifest_path = bundle["corpus_root"] / "stale.json"
    write_manifest(manifest, manifest_path)

    ok = publish(
        corpus_path=str(bundle["corpus_path"]),
        db_path=str(bundle["corpus_root"] / "corpus.db"),
        next_db_path=str(bundle["corpus_root"] / "corpus.next.db"),
        backup_dir=str(bundle["corpus_root"] / "backups"),
        manifest_path=str(manifest_path),
        repo_root=str(bundle["repo_root"]),
    )
    assert ok is False
    assert not (bundle["corpus_root"] / "corpus.db").exists()


# ── A4 — publish follows the manifest, not the legacy HTML tree ──────────────

def _publish(bundle, manifest_path, db_name="corpus.db"):
    return publish(
        corpus_path=str(bundle["corpus_path"]),
        db_path=str(bundle["corpus_root"] / db_name),
        next_db_path=str(bundle["corpus_root"] / "corpus.next.db"),
        backup_dir=str(bundle["corpus_root"] / "backups"),
        manifest_path=str(manifest_path),
        repo_root=str(bundle["repo_root"]),
    )


def test_a4_publish_uses_jsonl_content_not_stale_html(bundle):
    manifest_path = write_bundle_manifest(bundle)
    assert _publish(bundle, manifest_path) is True

    con = sqlite3.connect(bundle["corpus_root"] / "corpus.db")
    try:
        texts = [r[0] for r in con.execute("SELECT line_text FROM corpus_lines").fetchall()]
        titles = [r[0] for r in con.execute("SELECT title FROM sources").fetchall()]
        rows = con.execute("SELECT COUNT(*) FROM corpus_lines").fetchone()[0]
    finally:
        con.close()

    assert rows == 5, "tombstoned record must not be published"
    assert any("svasti arjuna" in t for t in texts)
    assert not any("stale desktop body" in t for t in texts)
    assert not any("STALE HTML TITLE" in (t or "") for t in titles)


def test_a4_publish_aborts_when_selected_jsonl_is_mutated(bundle):
    from ingest.validate import validate_corpus

    manifest_path = write_bundle_manifest(bundle)
    mutate_one_byte(bundle["jsonl_dir"] / "fixture-alpha.jsonl")

    # The legacy tree check still passes — it never looks at the JSONL. This is
    # precisely the gap A4 closes, so assert it rather than assume it.
    assert validate_corpus(str(bundle["corpus_path"])).ok

    assert _publish(bundle, manifest_path) is False
    assert not (bundle["corpus_root"] / "corpus.db").exists()


def test_a4_published_db_records_its_input_manifest(bundle):
    manifest_path = write_bundle_manifest(bundle)
    assert _publish(bundle, manifest_path) is True

    identity = corpus_identity(str(bundle["corpus_root"] / "corpus.db"))
    manifest = load_manifest(manifest_path)
    assert identity["input_manifest_hash"] == manifest["content_hash"]
    assert identity["corpus_version"] == manifest["bundle"]["bundle_version"]


# ── A6 — every generated view names one input manifest ───────────────────────

def test_a6_web_db_and_offline_pack_reports_name_the_same_manifest(bundle, tmp_path):
    from scripts.build_offline_pack import build_pack, write_pack_report

    manifest_path = write_bundle_manifest(bundle)
    db_path = bundle["corpus_root"] / "corpus.db"
    assert _publish(bundle, manifest_path) is True

    db_report_path = db_path.with_suffix("").with_name("corpus.build-report.json")
    db_report = load_report(db_report_path)
    assert validate_report(db_report) == []
    assert db_report["artifact"]["kind"] == "web-db"

    pack_out = str(tmp_path / "packs" / "base.db")
    stats = build_pack(str(db_path), pack_out, "base")
    pack_report = load_report(write_pack_report(pack_out, stats))
    assert validate_report(pack_report) == []
    assert pack_report["artifact"]["kind"] == "offline-pack"

    # Desktop views are rendered from the manifest directly rather than from
    # corpus.db, so they are the generator most likely to drift — assert them
    # into the same join.
    from corpus_builder.build_corpus_html import write_desktop_report

    data_dir = tmp_path / "Data"
    data_dir.mkdir()
    (data_dir / "fixture-alpha.html").write_text(
        "<!-- Fixture Alpha -->\n<p>body</p>\n", encoding="utf-8")
    (data_dir / "fixture-alpha.no_tags").write_text(
        "<!-- Fixture Alpha -->\nbody\n", encoding="utf-8")
    desktop_report = load_report(write_desktop_report(
        manifest_path=str(manifest_path),
        data_dir=data_dir,
        filenames=["fixture-alpha.html"],
        record_count=3,
        slug="fixture-alpha",
    ))
    assert validate_report(desktop_report) == []
    assert desktop_report["artifact"]["kind"] == "desktop-view"
    assert len(desktop_report["outputs"]) == 2, "the .no_tags sidecar must be registered too"

    agree, hashes = agree_on_input([db_report, pack_report, desktop_report])
    assert agree, f"generated views disagree on their input manifest: {hashes}"
    assert hashes.pop() == load_manifest(manifest_path)["content_hash"]


def test_a6_pack_carries_the_manifest_hash_in_its_own_meta(bundle, tmp_path):
    from scripts.build_offline_pack import build_pack

    manifest_path = write_bundle_manifest(bundle)
    assert _publish(bundle, manifest_path) is True
    pack_out = str(tmp_path / "packs" / "base.db")
    build_pack(str(bundle["corpus_root"] / "corpus.db"), pack_out, "base")

    con = sqlite3.connect(pack_out)
    try:
        meta = dict(con.execute("SELECT key, value FROM pack_meta").fetchall())
    finally:
        con.close()
    assert meta["input_manifest_hash"] == load_manifest(manifest_path)["content_hash"]


def test_a6_report_from_manifestless_db_is_refused(bundle):
    """A derivative of an unregistered corpus must not fabricate a lineage."""
    from corpus_builder.build_report import BuildReportError, manifest_reference_from_meta

    with pytest.raises(BuildReportError):
        manifest_reference_from_meta({"corpus_version": "v2026.01.01"})


# ── A7 — rollback rehearsal ──────────────────────────────────────────────────

def test_a7_prior_bundle_survives_a_failed_candidate_publication(bundle):
    manifest_v1 = write_bundle_manifest(bundle, version="test-1")
    db_path = bundle["corpus_root"] / "corpus.db"
    assert _publish(bundle, manifest_v1) is True
    before = corpus_identity(str(db_path))
    assert before["corpus_version"] == "test-1"

    # A candidate bundle whose content rotted after the manifest was cut.
    manifest_v2 = bundle["corpus_root"] / "corpus-manifest-v2.json"
    write_manifest(make_manifest(bundle, version="test-2"), manifest_v2)
    mutate_one_byte(bundle["jsonl_dir"] / "fixture-alpha.jsonl")

    assert _publish(bundle, manifest_v2) is False

    after = corpus_identity(str(db_path))
    assert after == before, "a failed candidate publication changed the live bundle"

    con = sqlite3.connect(db_path)
    try:
        assert con.execute("SELECT COUNT(*) FROM corpus_lines").fetchone()[0] == 5
    finally:
        con.close()


def test_a7_restore_backup_reactivates_the_previous_bundle(bundle):
    db_path = bundle["corpus_root"] / "corpus.db"
    backup_dir = bundle["corpus_root"] / "backups"

    manifest_v1 = write_bundle_manifest(bundle, version="test-1")
    assert _publish(bundle, manifest_v1) is True
    v1_identity = corpus_identity(str(db_path))

    # A second, entirely valid publication supersedes it…
    (bundle["jsonl_dir"] / "fixture-gamma.jsonl").write_text(
        '{"id": "gamma.1.1", "seq": 1, "chapter": "C", "passage": "1.1", '
        '"text": "navam", "html": "<p>navam</p>"}\n',
        encoding="utf-8",
    )
    manifest_v2 = bundle["corpus_root"] / "corpus-manifest-v2.json"
    write_manifest(make_manifest(bundle, version="test-2"), manifest_v2)
    assert _publish(bundle, manifest_v2) is True
    assert corpus_identity(str(db_path))["corpus_version"] == "test-2"

    # …and the prior bundle is still activatable from its backup.
    backups = sorted(backup_dir.glob("corpus_*.db"))
    assert backups, "publish did not record a backup to roll back to"
    assert restore_backup(str(backups[-1]), str(db_path)) is True
    assert corpus_identity(str(db_path)) == v1_identity


def test_a7_rollback_refuses_a_corrupt_backup(bundle, tmp_path):
    db_path = bundle["corpus_root"] / "corpus.db"
    assert _publish(bundle, write_bundle_manifest(bundle)) is True

    junk = tmp_path / "not-a-database.db"
    junk.write_bytes(b"this is not a sqlite file" * 40)
    assert restore_backup(str(junk), str(db_path)) is False
    # The live DB must be untouched by a refused rollback.
    assert corpus_identity(str(db_path))["corpus_version"] == "test-1"

    assert restore_backup(str(tmp_path / "missing.db"), str(db_path)) is False


# ── diff ─────────────────────────────────────────────────────────────────────

def test_diff_reports_added_removed_and_changed(bundle):
    before = make_manifest(bundle)

    (bundle["jsonl_dir"] / "fixture-gamma.jsonl").write_text(
        '{"id": "gamma.1.1", "seq": 1, "text": "navam", "html": "<p>navam</p>"}\n',
        encoding="utf-8",
    )
    mutate_one_byte(bundle["jsonl_dir"] / "fixture-alpha.jsonl")
    after = make_manifest(bundle)

    diff = diff_manifests(before, after)
    assert diff["identical"] is False
    assert diff["added"] == ["fixture-gamma"]
    assert diff["removed"] == []
    changed = {c["slug"]: c["fields"] for c in diff["changed"]}
    assert "content" in changed["fixture-alpha"]
    assert "fixture-beta" not in changed


def test_diff_of_identical_manifests_is_identical(bundle):
    diff = diff_manifests(make_manifest(bundle), make_manifest(bundle))
    assert diff["identical"] is True
    assert diff["added"] == diff["removed"] == [] and diff["changed"] == []


# ── the committed fixture manifest stays valid ───────────────────────────────

def test_committed_fixture_manifest_validates_against_its_files():
    """The checked-in fixture is a live example, not decoration.

    It is validated against the real repository tree, so a fixture JSONL edited
    without rebuilding the manifest fails here rather than misleading a reader.
    """
    web_dir = Path(__file__).resolve().parent.parent
    manifest_path = web_dir / "corpus_builder" / "manifest" / "corpus-manifest.fixture.json"
    report = validate_manifest(load_manifest(manifest_path), repo_root=web_dir.parent)
    assert report.ok, report.errors


def test_schema_file_is_valid_json_schema():
    import jsonschema

    from corpus_builder.corpus_manifest import SCHEMA_PATH

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


def test_round_trip_through_disk_preserves_bytes(bundle, tmp_path):
    manifest = make_manifest(bundle)
    path = tmp_path / "m.json"
    write_manifest(manifest, path)
    assert load_manifest(path) == manifest
    reserialized = copy.deepcopy(load_manifest(path))
    assert content_hash(reserialized["bundle"]) == manifest["content_hash"]
