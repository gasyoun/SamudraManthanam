#!/usr/bin/env python3
"""Checksum-pinned, vendor-neutral artifact resolution.

A bundle names large immutable objects (corpus archives, offline packs, model
files) that do not live in git. This module fetches one such object and refuses
to hand it to a caller unless its SHA-256 matches what the bundle declared.

Three properties are load-bearing:

* **Verify before use, always.** The object lands in a staging file, is hashed
  there, and is only moved into place after the hash matches. Nothing extracts,
  opens, or imports an unverified download — a corrupt or substituted archive
  never gets a chance to be interpreted.
* **Transport-neutral.** `file://`, plain filesystem paths, and `http(s)://` all
  go through one interface. Tests and offline development use the local
  transport; nothing in the architecture binds to one cloud vendor. A new
  transport is a `Transport` subclass, not a change to callers.
* **Credentials never reach a log.** Every URL that appears in a message,
  exception, or progress line passes through `redact_url`, which strips
  userinfo and replaces query values. Object stores routinely authenticate with
  pre-signed query strings, so an un-redacted URL in a build log is a leaked
  credential.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_READ_CHUNK = 1 << 20
DEFAULT_TIMEOUT = 60


class ArtifactError(Exception):
    """Raised when an artifact cannot be fetched or fails verification."""


class ChecksumMismatch(ArtifactError):
    """Raised when a fetched artifact's digest differs from the expected one.

    Deliberately a distinct type: a caller may reasonably retry a transport
    error, but a checksum mismatch must never be retried into acceptance.
    """


def redact_url(url: str) -> str:
    """Return a log-safe form of `url` with credentials and query values removed."""
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return "<unparseable-url>"
    if not parts.scheme:
        return url
    netloc = parts.hostname or ""
    if parts.username:
        netloc = f"***@{netloc}"
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    query = ""
    if parts.query:
        redacted = [
            (key, "***")
            for key, _ in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        ]
        query = urllib.parse.urlencode(redacted)
    return urllib.parse.urlunsplit((parts.scheme, netloc, parts.path, query, ""))


def sha256_file(path: str | os.PathLike[str]) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_READ_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_digest(expected: str) -> str:
    """Accept both `sha256:<hex>` and bare `<hex>`; reject anything else."""
    value = expected.strip().lower()
    if value.startswith("sha256:"):
        value = value[len("sha256:"):]
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ArtifactError(f"Not a SHA-256 digest: {expected!r}")
    return value


# ── transports ───────────────────────────────────────────────────────────────

class Transport:
    """Fetches a URI into an already-open staging file. One method, no state."""

    scheme: str = ""

    def fetch(self, uri: str, dest: Path, timeout: int = DEFAULT_TIMEOUT) -> None:
        raise NotImplementedError


class LocalFileTransport(Transport):
    """`file://` URLs and bare filesystem paths.

    Present so that tests, air-gapped builds, and development all exercise the
    same verification path as production rather than a bypass.
    """

    scheme = "file"

    def fetch(self, uri: str, dest: Path, timeout: int = DEFAULT_TIMEOUT) -> None:
        parts = urllib.parse.urlsplit(uri)
        if parts.scheme == "file":
            src = Path(urllib.request.url2pathname(parts.path))
        else:
            src = Path(uri)
        if not src.exists():
            raise ArtifactError(f"Local artifact not found: {redact_url(uri)}")
        if src.is_dir():
            raise ArtifactError(f"Local artifact is a directory, not a file: {redact_url(uri)}")
        shutil.copyfile(src, dest)


class HttpTransport(Transport):
    """`http://` and `https://`, stdlib only — no vendor SDK."""

    scheme = "https"

    def fetch(self, uri: str, dest: Path, timeout: int = DEFAULT_TIMEOUT) -> None:
        request = urllib.request.Request(uri, headers={"User-Agent": "samudra-artifact-resolver/1"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                with open(dest, "wb") as fh:
                    shutil.copyfileobj(response, fh, _READ_CHUNK)
        except ArtifactError:
            raise
        except Exception as exc:
            # `exc` can embed the full URL (pre-signed query included), so the
            # message is built from the redacted form and the exception type only.
            raise ArtifactError(
                f"Fetch failed for {redact_url(uri)}: {type(exc).__name__}"
            ) from None


_TRANSPORTS: dict[str, Transport] = {
    "": LocalFileTransport(),
    "file": LocalFileTransport(),
    "http": HttpTransport(),
    "https": HttpTransport(),
}


def transport_for(uri: str) -> Transport:
    scheme = urllib.parse.urlsplit(uri).scheme.lower()
    # A bare Windows path like C:\... parses with scheme 'c'; treat any
    # single-letter scheme as a drive letter, not a protocol.
    if len(scheme) == 1:
        scheme = ""
    try:
        return _TRANSPORTS[scheme]
    except KeyError:
        raise ArtifactError(f"No transport for scheme {scheme!r} ({redact_url(uri)})") from None


# ── resolution ───────────────────────────────────────────────────────────────

@dataclass
class ResolvedArtifact:
    path: Path
    sha256: str
    bytes: int
    from_cache: bool
    uri: str

    @property
    def safe_uri(self) -> str:
        return redact_url(self.uri)


def resolve_artifact(
    uri: str,
    expected_sha256: str,
    dest_dir: str | os.PathLike[str],
    *,
    name: str | None = None,
    bundle_version: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    force: bool = False,
    quiet: bool = False,
) -> ResolvedArtifact:
    """Fetch `uri` into `dest_dir`, verifying its SHA-256 before it is usable.

    A previously-resolved file is reused only after re-hashing it, so a cache
    entry that rotted on disk is caught rather than trusted.
    """
    expected = normalize_digest(expected_sha256)
    dest_root = Path(dest_dir)
    if bundle_version:
        dest_root = dest_root / bundle_version
    dest_root.mkdir(parents=True, exist_ok=True)

    filename = name or Path(urllib.parse.urlsplit(uri).path or uri).name
    if not filename or filename in {".", ".."} or os.sep in filename or "/" in filename:
        raise ArtifactError(f"Refusing unsafe artifact filename: {filename!r}")
    final_path = dest_root / filename

    if final_path.exists() and not force:
        actual = sha256_file(final_path)
        if actual == expected:
            if not quiet:
                print(f"  cached {filename} ({expected[:12]}…)")
            return ResolvedArtifact(final_path, actual, final_path.stat().st_size, True, uri)
        if not quiet:
            print(f"  cached {filename} failed verification, refetching")
        final_path.unlink()

    transport = transport_for(uri)
    if not quiet:
        print(f"  fetching {filename} from {redact_url(uri)}")

    # Stage in the destination directory so the final move is same-filesystem
    # and therefore atomic — a half-written artifact is never visible at the
    # path callers read.
    fd, staging_name = tempfile.mkstemp(prefix=f".{filename}.", suffix=".part", dir=str(dest_root))
    os.close(fd)
    staging = Path(staging_name)
    try:
        transport.fetch(uri, staging, timeout=timeout)
        actual = sha256_file(staging)
        if actual != expected:
            raise ChecksumMismatch(
                f"Checksum mismatch for {filename} from {redact_url(uri)}: "
                f"expected {expected}, got {actual}"
            )
        size = staging.stat().st_size
        os.replace(staging, final_path)
    finally:
        if staging.exists():
            staging.unlink()

    if not quiet:
        print(f"  verified {filename} ({size} bytes, {expected[:12]}…)")
    return ResolvedArtifact(final_path, expected, size, False, uri)


def extract_verified(artifact: ResolvedArtifact, dest_dir: str | os.PathLike[str]) -> Path:
    """Extract a *verified* archive. Refuses paths that escape `dest_dir`.

    Takes a `ResolvedArtifact` rather than a path by design: there is no way to
    call this on something that was never checksum-verified.
    """
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    resolved_dest = dest.resolve()

    def _guard(member_name: str) -> None:
        target = (resolved_dest / member_name).resolve()
        if target != resolved_dest and resolved_dest not in target.parents:
            raise ArtifactError(f"Archive member escapes destination: {member_name!r}")

    if zipfile.is_zipfile(artifact.path):
        with zipfile.ZipFile(artifact.path) as zf:
            for member in zf.namelist():
                _guard(member)
            zf.extractall(dest)
    elif tarfile.is_tarfile(artifact.path):
        with tarfile.open(artifact.path) as tf:
            for member in tf.getmembers():
                if member.islnk() or member.issym():
                    raise ArtifactError(f"Archive contains a link member: {member.name!r}")
                _guard(member.name)
            tf.extractall(dest)
    else:
        raise ArtifactError(f"Not a supported archive: {artifact.path.name}")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve a checksum-pinned bundle artifact (local or HTTP)."
    )
    parser.add_argument("uri", help="file://, https://, or a filesystem path")
    parser.add_argument("--sha256", required=True, help="Expected digest (sha256:<hex> or <hex>)")
    parser.add_argument("--dest", default="artifacts", help="Destination directory")
    parser.add_argument("--name", default=None, help="Override the stored filename")
    parser.add_argument("--bundle-version", default=None,
                        help="Store under <dest>/<bundle-version>/")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--force", action="store_true", help="Ignore any cached copy")
    parser.add_argument("--extract-to", default=None, help="Extract the verified archive here")
    args = parser.parse_args()

    try:
        artifact = resolve_artifact(
            args.uri,
            args.sha256,
            args.dest,
            name=args.name,
            bundle_version=args.bundle_version,
            timeout=args.timeout,
            force=args.force,
        )
        if args.extract_to:
            extract_verified(artifact, args.extract_to)
            print(f"  extracted to {args.extract_to}")
    except ArtifactError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(artifact.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
