"""Hermetic tests for scripts/run_headless_cb.py (H2433)."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts" / "run_headless_cb.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("run_headless_cb", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_headless_cb"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def rhc():
    return _load_mod()


def test_parse_jobs_text_basic(rhc):
    text = """
# comment
{"build": "a/config.ini", "out": "Data/a.html"}
{"build": "b/", "out": "Data/b.html", "check": true}
"""
    jobs = rhc.parse_jobs_text(text)
    assert len(jobs) == 2
    assert jobs[0].build == "a/config.ini"
    assert jobs[0].out == "Data/a.html"
    assert jobs[0].check is False
    assert jobs[1].check is True


def test_parse_jobs_text_rejects_bad_json(rhc):
    with pytest.raises(ValueError, match="line 1"):
        rhc.parse_jobs_text("{not json")


def test_parse_jobs_text_requires_build(rhc):
    with pytest.raises(ValueError, match="build"):
        rhc.parse_jobs_text('{"out": "x.html"}')


def test_job_argv(rhc, tmp_path):
    job = rhc.HeadlessJob(build="work", out="Data/o.html", check=True)
    binary = tmp_path / "cb_headless"
    binary.write_text("", encoding="utf-8")
    argv = job.argv(binary, tmp_path)
    assert argv[0] == str(binary)
    assert "--build" in argv
    assert "--out" in argv
    assert "--check" in argv


def test_main_skip_env(rhc, monkeypatch):
    monkeypatch.setenv("SKIP_HEADLESS_CB", "1")
    assert rhc.main(["--repo-root", str(_REPO)]) == 0


def test_main_no_jobs_file(rhc, tmp_path):
    # empty repo tree without pipeline jobs
    assert rhc.main(["--repo-root", str(tmp_path)]) == 0


def test_main_empty_jobs_file(rhc, tmp_path):
    jobs = tmp_path / "jobs.jsonl"
    jobs.write_text("# only comments\n\n", encoding="utf-8")
    assert rhc.main(["--repo-root", str(tmp_path), "--jobs", str(jobs)]) == 0


def test_main_missing_binary_fails(rhc, tmp_path):
    jobs = tmp_path / "jobs.jsonl"
    jobs.write_text(
        json.dumps({"build": "src", "out": "Data/x.html"}) + "\n",
        encoding="utf-8",
    )
    # no binary anywhere under tmp_path
    assert rhc.main(["--repo-root", str(tmp_path), "--jobs", str(jobs)]) == 1


def test_main_allow_missing_binary(rhc, tmp_path):
    jobs = tmp_path / "jobs.jsonl"
    jobs.write_text(
        json.dumps({"build": "src", "out": "Data/x.html"}) + "\n",
        encoding="utf-8",
    )
    assert (
        rhc.main(
            [
                "--repo-root",
                str(tmp_path),
                "--jobs",
                str(jobs),
                "--allow-missing-binary",
            ]
        )
        == 0
    )


def test_run_jobs_invokes_and_fails(rhc, tmp_path):
    binary = tmp_path / "cb_headless.exe"
    binary.write_text("", encoding="utf-8")
    job = rhc.HeadlessJob(build="cfg", out="out/x.html")
    calls: list[list[str]] = []

    def fake_run(cmd, check=False):
        calls.append(list(cmd))
        return SimpleNamespace(returncode=1)

    code = rhc.run_jobs(
        [job],
        binary=binary,
        repo_root=tmp_path,
        runner=fake_run,
    )
    assert code == 1
    assert calls and calls[0][0] == str(binary)
    assert "--build" in calls[0]
    assert "--out" in calls[0]


def test_run_jobs_success(rhc, tmp_path):
    binary = tmp_path / "cb_headless"
    binary.write_text("", encoding="utf-8")
    job = rhc.HeadlessJob(build="cfg")

    def fake_run(cmd, check=False):
        return SimpleNamespace(returncode=0)

    assert (
        rhc.run_jobs([job], binary=binary, repo_root=tmp_path, runner=fake_run)
        == 0
    )


def test_main_dry_run_with_binary(rhc, tmp_path):
    binary = tmp_path / "cb_headless"
    binary.write_text("", encoding="utf-8")
    jobs = tmp_path / "jobs.jsonl"
    jobs.write_text(
        json.dumps({"build": "work", "out": "Data/x.html"}) + "\n",
        encoding="utf-8",
    )
    code = rhc.main(
        [
            "--repo-root",
            str(tmp_path),
            "--jobs",
            str(jobs),
            "--binary",
            str(binary),
            "--dry-run",
        ]
    )
    assert code == 0


def test_resolve_jobs_from_corpus_path(rhc, tmp_path):
    corpus = tmp_path / "corpus"
    (corpus / "Programdata").mkdir(parents=True)
    jobs_file = corpus / "Programdata" / "headless_jobs.jsonl"
    jobs_file.write_text(
        json.dumps({"build": "a", "out": "b"}) + "\n", encoding="utf-8"
    )
    found = rhc.resolve_jobs_path(
        tmp_path / "repo", corpus_path=str(corpus)
    )
    assert found == jobs_file
