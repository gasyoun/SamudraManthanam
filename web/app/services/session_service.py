"""Verified-session identity for public write endpoints (H1926, C4/C6).

The rule this module exists to enforce: **submitted email text is never
identity proof.** Before H1926, ``POST /api/corrections/propose`` looked up
whatever address the request body contained and attached the matching account
to the correction. Typing a scholar's address was therefore enough to file
corrections under their name — attribution with no verification step anywhere
in the loop.

Identity here is a two-step, out-of-band loop instead:

1. **Request a challenge** — the caller names an address; the server mints a
   single-use token with a short expiry. The response is identical whether or
   not the address is known, so the endpoint is not an account-enumeration
   oracle.
2. **Redeem the challenge** — presenting the token (which only reaches the
   address's owner) creates a session. The session, not the body text, is what
   later grants attribution and elevated actions.

**Delivery is out of scope for this lane and deliberately not faked.** No mail
is sent: in a non-production environment the token is returned in the response
so the whole loop is testable end to end, and in production it is written to
the application log for an operator to relay. That is a stated limitation, not
a silent one — see web/IDENTITY_TRUST_CONTRACT.md § Delivery.

Only token *hashes* are stored. A leaked state.db then yields no usable
session, the same reason password hashes exist.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import secrets
from dataclasses import dataclass

import aiosqlite

logger = logging.getLogger(__name__)

#: Trust tiers recorded on every correction and audit row.
TRUST_ANONYMOUS = "anonymous"
TRUST_VERIFIED = "verified"

#: Header carrying a redeemed session token.
SESSION_HEADER = "X-Session-Token"

#: Cookie fallback for browser clients.
SESSION_COOKIE = "sm_session"

VERIFICATION_TTL_MINUTES = 30
SESSION_TTL_DAYS = 30


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(moment: datetime.datetime) -> str:
    return moment.isoformat()


@dataclass
class VerifiedSession:
    """A redeemed session. Its mere existence is the proof of verification."""

    user_id: int
    email: str
    expires_at: str


async def create_verification_challenge(
    db: aiosqlite.Connection, email: str
) -> str | None:
    """Mint a single-use verification token for ``email``.

    Returns the raw token, or None when the address has no account — the caller
    must still answer identically in both cases (no enumeration oracle).
    """
    async with db.execute("SELECT id FROM users WHERE email = ?", (email,)) as cursor:
        row = await cursor.fetchone()
    if not row:
        return None

    token = secrets.token_urlsafe(32)
    expires = _now() + datetime.timedelta(minutes=VERIFICATION_TTL_MINUTES)
    await db.execute(
        """INSERT INTO email_verifications (token_hash, user_id, created_at, expires_at)
           VALUES (?, ?, ?, ?)""",
        (_hash_token(token), row[0], _iso(_now()), _iso(expires)),
    )
    await db.commit()
    return token


async def redeem_verification(
    db: aiosqlite.Connection, token: str
) -> tuple[VerifiedSession, str] | None:
    """Exchange a valid, unexpired, unused challenge token for a session.

    Returns None for anything else — expired, already redeemed, or unknown.
    The three are not distinguished in the response: telling a caller which
    one it was is telling an attacker which token guess was closer.
    """
    token_hash = _hash_token(token)
    async with db.execute(
        """SELECT user_id, expires_at, redeemed_at
           FROM email_verifications WHERE token_hash = ?""",
        (token_hash,),
    ) as cursor:
        row = await cursor.fetchone()
    if not row:
        return None

    user_id, expires_at, redeemed_at = row[0], row[1], row[2]
    if redeemed_at:
        return None
    try:
        if datetime.datetime.fromisoformat(expires_at) < _now():
            return None
    except ValueError:
        logger.warning("verification row has unparsable expires_at — treating as expired")
        return None

    await db.execute(
        "UPDATE email_verifications SET redeemed_at = ? WHERE token_hash = ?",
        (_iso(_now()), token_hash),
    )

    session_token = secrets.token_urlsafe(32)
    session_expires = _now() + datetime.timedelta(days=SESSION_TTL_DAYS)
    await db.execute(
        """INSERT INTO user_sessions (token_hash, user_id, created_at, expires_at)
           VALUES (?, ?, ?, ?)""",
        (_hash_token(session_token), user_id, _iso(_now()), _iso(session_expires)),
    )
    await db.commit()

    async with db.execute("SELECT email FROM users WHERE id = ?", (user_id,)) as cursor:
        user_row = await cursor.fetchone()

    # The raw session token travels back to the caller once; only its hash is
    # kept. `VerifiedSession.expires_at` is what the caller stores alongside it.
    session = VerifiedSession(
        user_id=user_id,
        email=user_row[0] if user_row else "",
        expires_at=_iso(session_expires),
    )
    return session, session_token


async def resolve_session(
    db: aiosqlite.Connection, token: str | None
) -> VerifiedSession | None:
    """Resolve a presented session token to its verified user, or None."""
    if not token:
        return None
    async with db.execute(
        """SELECT s.user_id, s.expires_at, u.email
           FROM user_sessions s JOIN users u ON u.id = s.user_id
           WHERE s.token_hash = ?""",
        (_hash_token(token),),
    ) as cursor:
        row = await cursor.fetchone()
    if not row:
        return None
    try:
        if datetime.datetime.fromisoformat(row[1]) < _now():
            return None
    except ValueError:
        return None
    return VerifiedSession(user_id=row[0], email=row[2], expires_at=row[1])


def session_token_from_request(headers, cookies) -> str | None:
    """Read a session token from the header first, then the cookie."""
    token = headers.get(SESSION_HEADER)
    if token and token.strip():
        return token.strip()
    token = cookies.get(SESSION_COOKIE)
    return token.strip() if token and token.strip() else None
