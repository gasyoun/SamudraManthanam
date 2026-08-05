"""Lane A criterion A5 — checksum-pinned, vendor-neutral artifact resolution.

The claim under test: *local and HTTP/object transports enforce the same
expected checksum*. The suite runs each assertion through both transports so a
transport that skips verification cannot pass by being tested only on the path
where verification happens to be easy.

The HTTP side is served by a real loopback `http.server` rather than a mock —
the failure mode worth catching is a transport that streams bytes to disk
without ever hashing them, and a mocked socket cannot show that.
"""
import hashlib
import http.server
import os
import tarfile
import threading
import zipfile
from pathlib import Path

import pytest

from ingest.artifact_resolver import (
    ArtifactError,
    ChecksumMismatch,
    extract_verified,
    normalize_digest,
    redact_url,
    resolve_artifact,
    transport_for,
)

PAYLOAD = b"canonical bundle payload \xc3\xa4\xc3\xb6 " * 64


@pytest.fixture
def served(tmp_path):
    """A directory published over loopback HTTP for the duration of one test."""
    root = tmp_path / "served"
    root.mkdir()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, *args):  # keep pytest output readable
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield root, f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def artifact(tmp_path, served):
    """One artifact, reachable by BOTH transports, with its true digest."""
    root, base_url = served
    path = root / "bundle.bin"
    path.write_bytes(PAYLOAD)
    digest = hashlib.sha256(PAYLOAD).hexdigest()
    return {
        "path": path,
        "digest": digest,
        "uris": {
            "local": path.as_uri(),
            "http": f"{base_url}/bundle.bin",
        },
    }


@pytest.mark.parametrize("transport", ["local", "http"])
def test_a5_correct_checksum_resolves(artifact, tmp_path, transport):
    resolved = resolve_artifact(
        artifact["uris"][transport], artifact["digest"], tmp_path / "dest", quiet=True
    )
    assert resolved.path.read_bytes() == PAYLOAD
    assert resolved.sha256 == artifact["digest"]
    assert resolved.bytes == len(PAYLOAD)
    assert resolved.from_cache is False


@pytest.mark.parametrize("transport", ["local", "http"])
def test_a5_wrong_checksum_is_rejected_on_every_transport(artifact, tmp_path, transport):
    wrong = "0" * 64
    dest = tmp_path / "dest"
    with pytest.raises(ChecksumMismatch):
        resolve_artifact(artifact["uris"][transport], wrong, dest, quiet=True)

    # Nothing usable may survive a rejection — no final file, no staging residue.
    assert list(dest.glob("*")) == []


@pytest.mark.parametrize("transport", ["local", "http"])
def test_a5_mutated_payload_is_rejected(artifact, tmp_path, transport):
    """The digest is pinned to the bundle; the bytes changed underneath it."""
    original_digest = artifact["digest"]
    artifact["path"].write_bytes(PAYLOAD.replace(b"canonical", b"tampered!", 1))
    with pytest.raises(ChecksumMismatch):
        resolve_artifact(
            artifact["uris"][transport], original_digest, tmp_path / "dest", quiet=True
        )


@pytest.mark.parametrize("transport", ["local", "http"])
def test_a5_digest_prefix_forms_are_equivalent(artifact, tmp_path, transport):
    for expected in (artifact["digest"], "sha256:" + artifact["digest"],
                     "SHA256:" + artifact["digest"].upper()):
        resolved = resolve_artifact(
            artifact["uris"][transport], expected, tmp_path / f"dest-{transport}",
            force=True, quiet=True,
        )
        assert resolved.sha256 == artifact["digest"]


def test_a5_cached_copy_is_rehashed_not_trusted(artifact, tmp_path):
    dest = tmp_path / "dest"
    first = resolve_artifact(artifact["uris"]["local"], artifact["digest"], dest, quiet=True)
    second = resolve_artifact(artifact["uris"]["local"], artifact["digest"], dest, quiet=True)
    assert second.from_cache is True

    # Rot the cached file. A cache that is trusted rather than re-hashed would
    # hand this back as verified.
    first.path.write_bytes(b"rotted")
    third = resolve_artifact(artifact["uris"]["local"], artifact["digest"], dest, quiet=True)
    assert third.from_cache is False
    assert third.path.read_bytes() == PAYLOAD


def test_a5_bundle_version_partitions_the_cache(artifact, tmp_path):
    dest = tmp_path / "dest"
    a = resolve_artifact(artifact["uris"]["local"], artifact["digest"], dest,
                         bundle_version="2026.07", quiet=True)
    b = resolve_artifact(artifact["uris"]["local"], artifact["digest"], dest,
                         bundle_version="2026.08", quiet=True)
    assert a.path != b.path
    assert a.path.parent.name == "2026.07" and b.path.parent.name == "2026.08"


def test_missing_local_artifact_raises_artifact_error(tmp_path):
    with pytest.raises(ArtifactError):
        resolve_artifact(str(tmp_path / "absent.bin"), "0" * 64, tmp_path / "dest", quiet=True)


def test_http_404_does_not_become_a_silent_success(served, tmp_path):
    _, base_url = served
    with pytest.raises(ArtifactError):
        resolve_artifact(f"{base_url}/absent.bin", "0" * 64, tmp_path / "dest", quiet=True)
    assert list((tmp_path / "dest").glob("*")) == []


# ── credentials never reach a log or an exception ────────────────────────────

@pytest.mark.parametrize(
    "url,must_not_contain",
    [
        ("https://user:hunter2@objects.example/bundle.tar?X-Amz-Signature=deadbeef",
         ["hunter2", "deadbeef"]),
        ("https://objects.example/b.tar?token=s3cr3t&expires=99", ["s3cr3t"]),
        ("https://user@objects.example/b.tar", ["user@objects.example"]),
    ],
)
def test_redact_url_strips_credentials(url, must_not_contain):
    safe = redact_url(url)
    for secret in must_not_contain:
        assert secret not in safe
    assert "objects.example" in safe  # still diagnosable


def test_fetch_failure_message_carries_no_credentials(tmp_path):
    url = "https://127.0.0.1:1/bundle.bin?X-Amz-Signature=deadbeefcafe&token=hunter2"
    with pytest.raises(ArtifactError) as exc:
        resolve_artifact(url, "0" * 64, tmp_path / "dest", timeout=2, quiet=True)
    message = str(exc.value)
    assert "deadbeefcafe" not in message
    assert "hunter2" not in message


def test_checksum_mismatch_message_carries_no_credentials(served, tmp_path):
    root, base_url = served
    (root / "bundle.bin").write_bytes(PAYLOAD)
    url = f"{base_url}/bundle.bin?X-Amz-Signature=deadbeefcafe"
    with pytest.raises(ChecksumMismatch) as exc:
        resolve_artifact(url, "0" * 64, tmp_path / "dest", quiet=True)
    assert "deadbeefcafe" not in str(exc.value)


# ── transport selection and input hygiene ────────────────────────────────────

def test_transport_selection_covers_paths_urls_and_unknown_schemes():
    assert transport_for("/tmp/x.bin").scheme == "file"
    assert transport_for("C:\\data\\x.bin").scheme == "file"
    assert transport_for("file:///tmp/x.bin").scheme == "file"
    assert transport_for("https://example/x").scheme == "https"
    with pytest.raises(ArtifactError):
        transport_for("s3://bucket/key")


def test_normalize_digest_rejects_non_sha256():
    assert normalize_digest("sha256:" + "a" * 64) == "a" * 64
    for bad in ("", "abc", "md5:" + "a" * 32, "z" * 64, "a" * 63):
        with pytest.raises(ArtifactError):
            normalize_digest(bad)


def test_unsafe_artifact_filename_is_refused(artifact, tmp_path):
    for bad in ("../escape.bin", "sub/dir.bin", ".."):
        with pytest.raises(ArtifactError):
            resolve_artifact(artifact["uris"]["local"], artifact["digest"],
                             tmp_path / "dest", name=bad, quiet=True)


# ── extraction happens only after verification ───────────────────────────────

def _zip_with(tmp_path: Path, members: dict[str, bytes]) -> Path:
    path = tmp_path / "archive.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return path


def test_verified_archive_extracts(tmp_path):
    archive = _zip_with(tmp_path, {"inner/file.txt": b"payload"})
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    resolved = resolve_artifact(str(archive), digest, tmp_path / "dest", quiet=True)
    out = extract_verified(resolved, tmp_path / "extracted")
    assert (out / "inner" / "file.txt").read_bytes() == b"payload"


def test_zip_slip_member_is_refused(tmp_path):
    archive = _zip_with(tmp_path, {"../escaped.txt": b"pwned"})
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    resolved = resolve_artifact(str(archive), digest, tmp_path / "dest", quiet=True)
    with pytest.raises(ArtifactError):
        extract_verified(resolved, tmp_path / "extracted")
    assert not (tmp_path / "escaped.txt").exists()


def test_tar_link_member_is_refused(tmp_path):
    payload = tmp_path / "real.txt"
    payload.write_bytes(b"ok")
    archive = tmp_path / "archive.tar"
    with tarfile.open(archive, "w") as tf:
        tf.add(payload, arcname="real.txt")
        link = tarfile.TarInfo("link.txt")
        link.type = tarfile.SYMTYPE
        link.linkname = "/etc/passwd"
        tf.addfile(link)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    resolved = resolve_artifact(str(archive), digest, tmp_path / "dest", quiet=True)
    with pytest.raises(ArtifactError):
        extract_verified(resolved, tmp_path / "extracted")


def test_non_archive_is_not_extracted(artifact, tmp_path):
    resolved = resolve_artifact(artifact["uris"]["local"], artifact["digest"],
                                tmp_path / "dest", quiet=True)
    with pytest.raises(ArtifactError):
        extract_verified(resolved, tmp_path / "extracted")
