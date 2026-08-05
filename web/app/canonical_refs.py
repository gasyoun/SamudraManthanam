"""Durable corpus references — the canonical tuple and its dual-read resolver.

Lane B of the Wave-1 architecture-integrity plan (H1925). Lane A (H1924) made a
corpus *build* reproducible; this module makes a *reference into* that corpus
survive the next rebuild.

The canonical tuple
------------------
``(source_slug, canonical_id, corpus_version)``

- ``source_slug`` — stable, filename-derived source identity (``sources.slug``).
  ``sources.id`` is an ingest ordinal and changes when ``data.txt`` is reordered.
- ``canonical_id`` — the LINE_ID_SCHEME passage id (``docs/LINE_ID_SCHEME.md``),
  minted once by the converter and carried through ingest, never re-derived.
- ``corpus_version`` — which corpus the reference was recorded against
  (``corpus_meta.corpus_version``; with a Lane A manifest this IS the bundle
  version, so it is content-addressed rather than a wall-clock stamp).

Why ordinals are not enough
---------------------------
``(source_id, line_num)`` is the pair every retained record used before this
module. Both are re-assigned on every ingest: ``source_id`` follows enumeration
order, ``line_num`` follows document order within the file. A single inserted
line silently re-points every stored reference below it at the *wrong verse* —
and nothing in the system could tell, because both old and new references are
valid-looking integers.

The one rule that governs everything here
-----------------------------------------
**Never silently bind an ambiguous or unmappable legacy reference to a line.**
A legacy ordinal recorded against corpus version *X* may only be resolved in
corpus version *Y* through an explicit mapping (``legacy_ref_map``) built from a
pinned corpus, or when *X == Y*. Anything else resolves to
:attr:`ResolutionStatus.ORPHAN` / :attr:`ResolutionStatus.AMBIGUOUS` and is
reported, never guessed.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Optional, Sequence

#: The additive public field set every durable reference carries.
CANONICAL_TUPLE_FIELDS = ("source_slug", "canonical_id", "corpus_version")

_WS = re.compile(r"\s+")
_TAGS = re.compile(r"<[^>]+>")


def normalise_plain(text: str | None) -> str:
    """Markup-stripped, NFC-normalised, whitespace-collapsed plain text.

    The comparable form behind both :func:`content_fingerprint` and the
    backfill's evidence check.
    """
    if not text:
        return ""
    plain = _TAGS.sub(" ", text)
    plain = unicodedata.normalize("NFC", plain)
    return _WS.sub(" ", plain).strip()


def content_fingerprint(text: str | None) -> str:
    """Stable fingerprint of a line's *content*, independent of markup.

    Used by the zero-orphan gate to answer the second half of "does this
    reference still resolve?" — namely, does it still resolve to the same
    *text*. NFC + whitespace collapse so a re-wrapped or re-normalised source
    file does not read as a content change; HTML tags are stripped so a markup
    fix does not either.
    """
    plain = normalise_plain(text)
    if not plain:
        return ""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


class ResolutionStatus(str, Enum):
    """How a durable reference was resolved (or refused)."""

    #: Resolved directly from ``(source_slug, canonical_id)``.
    CANONICAL = "canonical"
    #: Resolved from a legacy ordinal through an explicit ``legacy_ref_map`` row.
    LEGACY_MAPPED = "legacy_mapped"
    #: Resolved from a legacy ordinal within the SAME corpus_version it was
    #: recorded against — no rebuild has happened, so the ordinal is still valid.
    LEGACY_DIRECT = "legacy_direct"
    #: More than one line matched. Never bound.
    AMBIGUOUS = "ambiguous"
    #: Nothing matched, or a cross-version ordinal had no mapping. Never bound.
    ORPHAN = "orphan"


_OK_STATUSES = frozenset(
    {ResolutionStatus.CANONICAL, ResolutionStatus.LEGACY_MAPPED, ResolutionStatus.LEGACY_DIRECT}
)


@dataclass(frozen=True)
class DurableRef:
    """A reference as it was *stored*, in whichever form the record has.

    Either half may be absent: pre-migration records carry only the legacy
    ordinals, records written after B4 carry the canonical tuple (and keep the
    ordinals as compatibility fields until the zero-orphan gate permits their
    deprecation).
    """

    source_slug: Optional[str] = None
    canonical_id: Optional[str] = None
    corpus_version: Optional[str] = None
    source_id: Optional[int] = None
    line_num: Optional[int] = None
    #: Free-form label used in reports (e.g. ``"corrections#42"``).
    origin: str = ""

    @property
    def has_canonical(self) -> bool:
        return bool(self.source_slug and self.canonical_id)

    @property
    def has_legacy(self) -> bool:
        return self.source_id is not None and self.line_num is not None


@dataclass
class Resolution:
    """The outcome of resolving one :class:`DurableRef` against a corpus."""

    status: ResolutionStatus
    ref: DurableRef
    source_id: Optional[int] = None
    line_num: Optional[int] = None
    source_slug: Optional[str] = None
    canonical_id: Optional[str] = None
    corpus_version: Optional[str] = None
    fingerprint: str = ""
    reason: str = ""
    candidates: list[dict[str, Any]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status in _OK_STATUSES

    def as_dict(self) -> dict[str, Any]:
        return {
            "origin": self.ref.origin,
            "status": self.status.value,
            "source_id": self.source_id,
            "line_num": self.line_num,
            "source_slug": self.source_slug,
            "canonical_id": self.canonical_id,
            "corpus_version": self.corpus_version,
            "fingerprint": self.fingerprint,
            "reason": self.reason,
            "candidate_count": len(self.candidates),
        }


class ReferenceResolutionError(Exception):
    """Raised when a caller demands a binding the resolver refuses to make."""

    def __init__(self, resolution: Resolution):
        self.resolution = resolution
        super().__init__(f"{resolution.status.value}: {resolution.reason}")


# --------------------------------------------------------------------------
# Corpus identity index
# --------------------------------------------------------------------------
#
# `corpus_lines` is an FTS5 virtual table: its non-indexed columns cannot carry
# a B-tree index, so every single-reference lookup is a scan. That is fine for
# one correction being filed; it is ruinous for a zero-orphan sweep over every
# retained reference. Bulk callers therefore build ONE index in a single pass
# and resolve against it in memory.


@dataclass
class CorpusIdentityIndex:
    """In-memory identity view of one corpus DB, built in a single scan."""

    corpus_version: Optional[str]
    by_canonical: dict[tuple[str, str], list[dict[str, Any]]]
    by_ordinal: dict[tuple[int, int], dict[str, Any]]

    @property
    def line_count(self) -> int:
        return len(self.by_ordinal)


def build_identity_index(conn: sqlite3.Connection) -> CorpusIdentityIndex:
    """Read every line's identity fields out of a corpus DB in one pass."""
    conn.row_factory = sqlite3.Row
    corpus_version = None
    try:
        row = conn.execute(
            "SELECT value FROM corpus_meta WHERE key = 'corpus_version'"
        ).fetchone()
        if row:
            corpus_version = row[0]
    except sqlite3.Error:
        corpus_version = None

    by_canonical: dict[tuple[str, str], list[dict[str, Any]]] = {}
    by_ordinal: dict[tuple[int, int], dict[str, Any]] = {}
    sql = (
        "SELECT cl.source_id, cl.line_num, cl.canonical_id, cl.link_id, "
        "       cl.line_text, s.slug AS source_slug "
        "FROM corpus_lines cl JOIN sources s ON s.id = cl.source_id"
    )
    for row in conn.execute(sql):
        plain = normalise_plain(row["line_text"])
        rec = {
            "source_id": int(row["source_id"]),
            "line_num": int(row["line_num"]),
            "canonical_id": row["canonical_id"],
            "link_id": row["link_id"],
            "source_slug": row["source_slug"],
            "fingerprint": content_fingerprint(row["line_text"]),
            # Kept so the backfill can CHECK a pinned corpus against the text a
            # stored record remembers, instead of trusting the pin.
            "text": plain,
        }
        by_ordinal[(rec["source_id"], rec["line_num"])] = rec
        if rec["source_slug"] and rec["canonical_id"]:
            by_canonical.setdefault((rec["source_slug"], rec["canonical_id"]), []).append(rec)
    return CorpusIdentityIndex(
        corpus_version=corpus_version, by_canonical=by_canonical, by_ordinal=by_ordinal
    )


# --------------------------------------------------------------------------
# The resolver
# --------------------------------------------------------------------------


def resolve_against_index(
    ref: DurableRef,
    index: CorpusIdentityIndex,
    legacy_map: dict[tuple[str, int, int], dict[str, Any]] | None = None,
    *,
    assume_current_version: bool = False,
) -> Resolution:
    """Dual-read one reference against a corpus identity index.

    Order of preference, per the Lane B contract:

    1. the canonical tuple;
    2. an explicit legacy mapping pinned to the recorded corpus version;
    3. the legacy ordinal, but **only** inside the corpus version it was
       recorded against;

    and otherwise report — never bind.

    ``assume_current_version`` distinguishes the two ways an *unversioned*
    ordinal can reach us, which is a caller's fact and not the resolver's to
    guess. A live client posting ``(source_id, line_num)`` read those ordinals
    off the corpus being served right now, so treating them as current is
    correct. A row already sitting in ``state.db`` with no recorded version has
    unknown provenance — binding it would be exactly the silent mis-binding
    this module exists to prevent — so the backfill and the zero-orphan report
    leave the flag off.
    """
    legacy_map = legacy_map or {}

    if ref.has_canonical:
        rows = index.by_canonical.get((ref.source_slug or "", ref.canonical_id or ""), [])
        if len(rows) == 1:
            return _hit(ResolutionStatus.CANONICAL, ref, rows[0], index)
        if len(rows) > 1:
            return Resolution(
                status=ResolutionStatus.AMBIGUOUS,
                ref=ref,
                source_slug=ref.source_slug,
                canonical_id=ref.canonical_id,
                corpus_version=index.corpus_version,
                reason=(
                    f"{len(rows)} lines share canonical id "
                    f"{ref.canonical_id} (source {ref.source_slug}) — refusing to pick one"
                ),
                candidates=rows,
            )
        # Canonical id absent from this corpus: fall through to the legacy path
        # so a rename/re-mint can still be caught by an explicit mapping. If
        # there is no legacy half either, this is an orphan.
        if not ref.has_legacy:
            return Resolution(
                status=ResolutionStatus.ORPHAN,
                ref=ref,
                source_slug=ref.source_slug,
                canonical_id=ref.canonical_id,
                corpus_version=index.corpus_version,
                reason=(
                    f"canonical id {ref.canonical_id} (source {ref.source_slug}) does not exist "
                    f"in corpus_version={index.corpus_version}"
                ),
            )

    if not ref.has_legacy:
        return Resolution(
            status=ResolutionStatus.ORPHAN,
            ref=ref,
            corpus_version=index.corpus_version,
            reason="reference carries neither a canonical tuple nor a legacy ordinal pair",
        )

    pinned = ref.corpus_version or ""
    mapped = legacy_map.get((pinned, int(ref.source_id or 0), int(ref.line_num or 0)))
    if mapped:
        key = (mapped["source_slug"], mapped["canonical_id"])
        rows = index.by_canonical.get(key, [])
        if len(rows) == 1:
            res = _hit(ResolutionStatus.LEGACY_MAPPED, ref, rows[0], index)
            res.reason = f"legacy ordinal mapped via pinned corpus_version={pinned}"
            return res
        if len(rows) > 1:
            return Resolution(
                status=ResolutionStatus.AMBIGUOUS,
                ref=ref,
                source_slug=mapped["source_slug"],
                canonical_id=mapped["canonical_id"],
                corpus_version=index.corpus_version,
                reason=(
                    f"mapped canonical id {key[1]} (source {key[0]}) matches {len(rows)} lines"
                ),
                candidates=rows,
            )
        return Resolution(
            status=ResolutionStatus.ORPHAN,
            ref=ref,
            source_slug=mapped["source_slug"],
            canonical_id=mapped["canonical_id"],
            corpus_version=index.corpus_version,
            reason=(
                f"legacy ordinal maps to {key[1]} (source {key[0]}), which no longer exists "
                f"in corpus_version={index.corpus_version}"
            ),
        )

    same_version = bool(pinned) and pinned == (index.corpus_version or "")
    unversioned_but_current = not pinned and (
        assume_current_version or index.corpus_version is None
    )
    if same_version or unversioned_but_current:
        rec = index.by_ordinal.get((int(ref.source_id or 0), int(ref.line_num or 0)))
        if rec:
            res = _hit(ResolutionStatus.LEGACY_DIRECT, ref, rec, index)
            res.reason = "legacy ordinal resolved inside its own corpus version"
            return res
        return Resolution(
            status=ResolutionStatus.ORPHAN,
            ref=ref,
            corpus_version=index.corpus_version,
            reason=(
                f"legacy ordinal (source_id={ref.source_id}, line_num={ref.line_num}) "
                f"is absent from corpus_version={index.corpus_version}"
            ),
        )

    # The dangerous case, and the whole point of this module: the ordinal WOULD
    # resolve — to a line that may be a different verse entirely.
    return Resolution(
        status=ResolutionStatus.ORPHAN,
        ref=ref,
        corpus_version=index.corpus_version,
        reason=(
            f"legacy ordinal recorded against corpus_version={pinned or 'unknown'} "
            f"cannot be bound in corpus_version={index.corpus_version} without an "
            f"explicit mapping — refusing to guess"
        ),
    )


def _hit(
    status: ResolutionStatus,
    ref: DurableRef,
    rec: dict[str, Any],
    index: CorpusIdentityIndex,
) -> Resolution:
    return Resolution(
        status=status,
        ref=ref,
        source_id=rec["source_id"],
        line_num=rec["line_num"],
        source_slug=rec["source_slug"],
        canonical_id=rec["canonical_id"],
        corpus_version=index.corpus_version,
        fingerprint=rec["fingerprint"],
    )


def load_legacy_map(
    state_conn: sqlite3.Connection,
) -> dict[tuple[str, int, int], dict[str, Any]]:
    """Load ``legacy_ref_map`` keyed by ``(corpus_version, source_id, line_num)``."""
    try:
        state_conn.row_factory = sqlite3.Row
        rows = state_conn.execute(
            "SELECT corpus_version, source_id, line_num, source_slug, canonical_id, fingerprint "
            "FROM legacy_ref_map"
        ).fetchall()
    except sqlite3.Error:
        return {}
    return {
        (r["corpus_version"], int(r["source_id"]), int(r["line_num"])): {
            "source_slug": r["source_slug"],
            "canonical_id": r["canonical_id"],
            "fingerprint": r["fingerprint"],
        }
        for r in rows
    }


# --------------------------------------------------------------------------
# Single-reference lookup on the request path (async, aiosqlite)
# --------------------------------------------------------------------------


async def resolve_one_async(
    corpus_db, state_db, ref: DurableRef, *, assume_current_version: bool = True
) -> Resolution:
    """Resolve a single reference on the request path.

    Same decision table as :func:`resolve_against_index`, but issuing targeted
    queries instead of building a whole-corpus index — one correction being
    filed must not scan the corpus twice. The default
    ``assume_current_version=True`` reflects the request path: an ordinal a
    client just posted was read off the corpus being served.
    """
    corpus_version = await _corpus_version_async(corpus_db)
    index = CorpusIdentityIndex(corpus_version=corpus_version, by_canonical={}, by_ordinal={})

    if ref.has_canonical:
        rows = await _fetch_async(
            corpus_db,
            "SELECT cl.source_id, cl.line_num, cl.canonical_id, cl.link_id, cl.line_text, "
            "       s.slug AS source_slug "
            "FROM corpus_lines cl JOIN sources s ON s.id = cl.source_id "
            "WHERE s.slug = ? AND cl.canonical_id = ?",
            (ref.source_slug, ref.canonical_id),
        )
        index.by_canonical[(ref.source_slug or "", ref.canonical_id or "")] = rows

    legacy_map: dict[tuple[str, int, int], dict[str, Any]] = {}
    if ref.has_legacy:
        rows = await _fetch_async(
            corpus_db,
            "SELECT cl.source_id, cl.line_num, cl.canonical_id, cl.link_id, cl.line_text, "
            "       s.slug AS source_slug "
            "FROM corpus_lines cl JOIN sources s ON s.id = cl.source_id "
            "WHERE cl.source_id = ? AND cl.line_num = ?",
            (ref.source_id, ref.line_num),
        )
        if rows:
            index.by_ordinal[(int(ref.source_id or 0), int(ref.line_num or 0))] = rows[0]
        if state_db is not None:
            legacy_map = await _fetch_legacy_map_async(state_db, ref)
            for mapped in legacy_map.values():
                key = (mapped["source_slug"], mapped["canonical_id"])
                if key not in index.by_canonical:
                    index.by_canonical[key] = await _fetch_async(
                        corpus_db,
                        "SELECT cl.source_id, cl.line_num, cl.canonical_id, cl.link_id, "
                        "       cl.line_text, s.slug AS source_slug "
                        "FROM corpus_lines cl JOIN sources s ON s.id = cl.source_id "
                        "WHERE s.slug = ? AND cl.canonical_id = ?",
                        key,
                    )

    return resolve_against_index(
        ref, index, legacy_map, assume_current_version=assume_current_version
    )


async def _fetch_async(db, sql: str, params: Sequence[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    async with db.execute(sql, tuple(params)) as cursor:
        for row in await cursor.fetchall():
            d = dict(row)
            out.append(
                {
                    "source_id": int(d["source_id"]),
                    "line_num": int(d["line_num"]),
                    "canonical_id": d.get("canonical_id"),
                    "link_id": d.get("link_id"),
                    "source_slug": d.get("source_slug"),
                    "fingerprint": content_fingerprint(d.get("line_text")),
                    "text": normalise_plain(d.get("line_text")),
                }
            )
    return out


async def _corpus_version_async(db) -> Optional[str]:
    try:
        async with db.execute(
            "SELECT value FROM corpus_meta WHERE key = 'corpus_version'"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
    except Exception:
        return None


async def _fetch_legacy_map_async(
    state_db, ref: DurableRef
) -> dict[tuple[str, int, int], dict[str, Any]]:
    try:
        async with state_db.execute(
            "SELECT corpus_version, source_id, line_num, source_slug, canonical_id, fingerprint "
            "FROM legacy_ref_map WHERE source_id = ? AND line_num = ?",
            (ref.source_id, ref.line_num),
        ) as cursor:
            rows = await cursor.fetchall()
    except Exception:
        return {}
    return {
        (r[0], int(r[1]), int(r[2])): {
            "source_slug": r[3],
            "canonical_id": r[4],
            "fingerprint": r[5],
        }
        for r in rows
    }


def summarise(resolutions: Iterable[Resolution]) -> dict[str, int]:
    """Count resolutions by status — the shape every Lane B report prints."""
    counts = {s.value: 0 for s in ResolutionStatus}
    for r in resolutions:
        counts[r.status.value] += 1
    return counts
