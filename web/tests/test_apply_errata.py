"""H2720: errata.yml apply + html-from-jsonl rebuild (hermetic fixture)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_WEB = Path(__file__).resolve().parents[1]
_CB = _WEB / "corpus_builder"
_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "errata"
sys.path.insert(0, str(_CB))

import errata_yml as ey  # noqa: E402
import build_errata as be  # noqa: E402


def test_load_fixture_errata_yml():
    loaded = ey.load_errata_yml(_FIXTURE / "errata.yml")
    assert loaded["work"].startswith("Errata apply fixture")
    assert len(loaded["entries"]) == 1
    row = loaded["entries"][0]
    assert row["read"] == "исправление"
    assert row["instead"] == "опечатка"
    assert row["id"] == "errata-pilot:1.1#ru"
    assert row["passage"] == "1.1"
    assert row["kind"] == "digitization"
    assert row["found_by"] == "H2720 fixture"
    assert row["date_added"] == "2026-08-14"


def test_load_knauer_flow_style_row():
    text = (
        'work: "Knauer fixture"\n'
        "entries:\n"
        '  - { page: 117, line: "8 сн.",  read: "gañgāyā",'
        ' instead: "gaṉgāyā", found_by: "Knauer 1908 print",'
        ' date_added: "2026-07-06" }\n'
    )
    path = _FIXTURE / "_flow.yml"
    try:
        path.write_text(text, encoding="utf-8")
        loaded = ey.load_errata_yml(path)
    finally:
        if path.exists():
            path.unlink()
    assert loaded["entries"][0]["read"] == "gañgāyā"
    assert loaded["entries"][0]["page"] == 117 or loaded["entries"][0]["page"] == "117"
    assert loaded["entries"][0]["line"] == "8 сн."


def test_apply_one_erratum_and_diff_jsonl(tmp_path: Path):
    src = tmp_path / "work.jsonl"
    shutil.copyfile(_FIXTURE / "work.jsonl", src)
    loaded = ey.load_errata_yml(_FIXTURE / "errata.yml")
    before = ey.load_jsonl(src)
    patched, report = ey.apply_entries(before, loaded["entries"])
    assert report[0]["status"] == "applied"
    dest = tmp_path / "patched.jsonl"
    ey.write_jsonl(dest, patched)
    recs = [json.loads(ln) for ln in dest.read_text(encoding="utf-8").splitlines() if ln]
    assert recs[0]["text"] == "Напечатано слово исправление здесь."
    assert recs[0]["html"] == "Напечатано слово исправление здесь."
    assert recs[1]["text"] == "Второй стих без правки."
    original = (_FIXTURE / "work.jsonl").read_text(encoding="utf-8")
    assert "опечатка" in original
    assert "исправление" not in original
    assert "опечатка" not in dest.read_text(encoding="utf-8")


def test_apply_is_idempotent(tmp_path: Path):
    src = tmp_path / "work.jsonl"
    shutil.copyfile(_FIXTURE / "work.jsonl", src)
    loaded = ey.load_errata_yml(_FIXTURE / "errata.yml")
    once, _ = ey.apply_entries(ey.load_jsonl(src), loaded["entries"])
    ey.write_jsonl(src, once)
    twice, report = ey.apply_entries(ey.load_jsonl(src), loaded["entries"])
    assert report[0]["status"] == "already_applied"
    recs = [r for _raw, r in twice]
    assert recs[0]["text"].count("исправление") == 1


def test_apply_missing_instead_fails_loud(tmp_path: Path):
    src = tmp_path / "work.jsonl"
    src.write_text(
        json.dumps(
            {
                "id": "errata-pilot:1.1#ru",
                "work": "errata-pilot",
                "passage": "1.1",
                "seg": "ru",
                "text": "нет такого слова",
                "html": "нет такого слова",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    loaded = ey.load_errata_yml(_FIXTURE / "errata.yml")
    with pytest.raises(ValueError, match="not in"):
        ey.apply_entries(ey.load_jsonl(src), loaded["entries"])


def test_cli_apply_and_rebuild_html(tmp_path: Path):
    jsonl = tmp_path / "work.jsonl"
    shutil.copyfile(_FIXTURE / "work.jsonl", jsonl)
    html_dir = tmp_path / "html"
    cmd = [
        sys.executable,
        str(_CB / "apply_errata.py"),
        "--errata",
        str(_FIXTURE / "errata.yml"),
        "--jsonl",
        str(jsonl),
        "--out",
        str(tmp_path / "patched.jsonl"),
        "--rebuild",
        "--meta",
        str(_FIXTURE / "work.meta.json"),
        "--data-dir",
        str(html_dir),
        "--slug",
        "errata-pilot",
    ]
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    patched = (tmp_path / "patched.jsonl").read_text(encoding="utf-8")
    assert "исправление" in patched
    assert "опечатка" not in patched
    html = (html_dir / "errata-pilot.html").read_text(encoding="utf-8")
    assert "исправление" in html
    assert "опечатка" not in html
    notags = (html_dir / "errata-pilot.no_tags").read_text(encoding="utf-8")
    assert "исправление" in notags


def test_generate_errata_md_contains_row(tmp_path: Path):
    work_dir = tmp_path / "errata-pilot"
    work_dir.mkdir()
    shutil.copyfile(_FIXTURE / "errata.yml", work_dir / "errata.yml")
    dest = be.generate_one(work_dir)
    text = dest.read_text(encoding="utf-8")
    assert "исправление" in text
    assert "опечатка" in text
    assert "errata-pilot:1.1#ru" in text
    assert "H2720 fixture" in text


def test_pilot_work_errata_yml_loads_empty():
    path = _CB / "errata" / "bhagavati-manasa-puja-stotra" / "errata.yml"
    loaded = ey.load_errata_yml(path)
    assert loaded["entries"] == []
    assert "Bhagavatī" in loaded["work"] or "Bhagavati" in loaded["work"]


def test_pilot_recipe_is_html_from_jsonl():
    recipe = ey.recipe_for("bhagavati-manasa-puja-stotra")
    assert recipe["rebuild"] == "html-from-jsonl"
    assert recipe["input"] == "IN-DOC-IGN"
    assert Path(recipe["jsonl"]).as_posix().endswith(
        "bhagavati-manasa-puja-stotra.jsonl"
    )
