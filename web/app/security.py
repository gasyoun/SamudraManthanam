"""Admin authentication transport and credential log hygiene (H1926, C3/C5).

Administrative endpoints used to take their secret as ``?key=…``. A query
string is the worst possible place for a credential: it is written verbatim to
the nginx access log and the uvicorn access log, kept in browser history, and
forwarded in ``Referer`` headers to any third party the page links to. Rotating
the key does not undo any of that, because the leak already happened at request
time.

So this module does two things:

1. :func:`require_admin` — a dependency that accepts the secret **only** from a
   request header (``Authorization: Bearer …`` or ``X-Admin-Key: …``) and
   actively *rejects* a request that carries one in the query string, rather
   than quietly accepting both. A silent dual path never expires: clients keep
   using the leaky form indefinitely because nothing tells them to stop.
2. :func:`install_credential_log_redaction` — a logging filter that scrubs
   credential-shaped query parameters out of every log record, so the rejected
   request's own access-log line cannot preserve the value that the rejection
   was meant to protect.

Comparisons use :func:`hmac.compare_digest` so a wrong key cannot be recovered
byte-by-byte from response timing.
"""

from __future__ import annotations

import hmac
import logging
import re
from typing import Iterable

from fastapi import HTTPException, Request

from app.settings import settings

logger = logging.getLogger(__name__)

#: Query parameters that may carry a secret. A request presenting one of these
#: to an admin route is refused; the value is never compared or logged.
CREDENTIAL_QUERY_PARAMS = ("key", "token", "secret", "api_key", "admin_key")

#: Header names accepted for the admin secret, in precedence order.
ADMIN_HEADER = "X-Admin-Key"
AUTHORIZATION_HEADER = "Authorization"

#: Stable error codes (mirrored in web/IDENTITY_TRUST_CONTRACT.md).
ERROR_CREDENTIAL_IN_QUERY = "credential_in_query"
ERROR_ADMIN_FORBIDDEN = "forbidden"

_DEV_KEY = "dev"

# `key=<value>` in a URL/query fragment, up to the next separator.
_CREDENTIAL_PATTERN = re.compile(
    r"(?i)\b(" + "|".join(CREDENTIAL_QUERY_PARAMS) + r")=[^&\s\"']*"
)
_REDACTED = "REDACTED"


def redact_credentials(text: str) -> str:
    """Replace credential-shaped query values in ``text`` with ``REDACTED``."""
    return _CREDENTIAL_PATTERN.sub(lambda m: f"{m.group(1)}={_REDACTED}", text)


class CredentialRedactingFilter(logging.Filter):
    """Scrub credential values from a log record before it is emitted.

    Access logs interpolate the request line lazily, so the secret can live in
    ``record.msg``, in ``record.args``, or be split across the two — a template
    of ``"GET %s?key=%s"`` hides it from any inspection of either half alone.
    So the record is rendered first and the *rendered* text is redacted.

    Rendering collapses lazy formatting, which is why it only happens when a
    redaction actually fired: records with nothing to hide keep their template
    and args untouched. Redacting the template in place was the tempting
    alternative and is wrong — it rewrites ``key=%s`` to ``key=REDACTED``,
    dropping a placeholder while its argument remains, and the handler then
    dies with "not all arguments converted" instead of logging. A logging
    filter that can break logging is worse than the leak it prevents.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D102
        try:
            message = record.getMessage()
        except Exception:  # pragma: no cover - malformed record; never block it
            return True
        redacted = redact_credentials(message)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True


def install_credential_log_redaction(
    logger_names: Iterable[str] = ("uvicorn.access", "uvicorn.error", "app"),
) -> None:
    """Attach :class:`CredentialRedactingFilter` where log records are emitted.

    Two attachment points, because a filter on a *logger* only sees records
    logged directly to it — records propagated up from child loggers skip it
    entirely. So the named application/server loggers are covered directly, and
    the root **handlers** are covered too: a handler filter runs on every record
    that reaches it, whatever logger produced it. That second half is what
    catches a third-party library logging a URL we never formatted ourselves.

    Idempotent — re-running (e.g. across test app instances) does not stack
    duplicate filters.
    """
    for name in logger_names:
        target = logging.getLogger(name)
        if not any(isinstance(f, CredentialRedactingFilter) for f in target.filters):
            target.addFilter(CredentialRedactingFilter())

    for handler in logging.getLogger().handlers:
        if not any(isinstance(f, CredentialRedactingFilter) for f in handler.filters):
            handler.addFilter(CredentialRedactingFilter())


def _expected_admin_key() -> str | None:
    """The secret this deployment accepts, or None when admin access is closed."""
    if settings.ADMIN_SECRET_KEY:
        return settings.ADMIN_SECRET_KEY
    if settings.APP_ENV != "production":
        # Development convenience only. In production an unset key means the
        # admin surface is closed, never that a default password works.
        return _DEV_KEY
    return None


def _presented_admin_key(request: Request) -> str | None:
    header = request.headers.get(AUTHORIZATION_HEADER)
    if header:
        scheme, _, value = header.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            return value.strip()
    value = request.headers.get(ADMIN_HEADER)
    return value.strip() if value and value.strip() else None


async def require_admin(request: Request) -> None:
    """FastAPI dependency guarding an administrative endpoint.

    Refuses, in order:

    * 400 when a credential-shaped query parameter is present at all — the
      request has already leaked its secret to the access log and any proxy in
      front of it, so the correct answer is "resend it as a header", not
      "authenticated";
    * 403 when the deployment has no admin key configured, or the presented
      header does not match.
    """
    for param in CREDENTIAL_QUERY_PARAMS:
        if param in request.query_params:
            # Log the parameter NAME only; the value is exactly what must not
            # reach the log.
            logger.warning(
                "admin auth refused: credential passed in query parameter %r "
                "(path=%s) — use the %s header",
                param,
                request.url.path,
                ADMIN_HEADER,
            )
            raise HTTPException(
                status_code=400,
                detail=(
                    "Administrative credentials must be sent in the "
                    f"{ADMIN_HEADER} or {AUTHORIZATION_HEADER} header, never in "
                    "the query string."
                ),
            )

    expected = _expected_admin_key()
    presented = _presented_admin_key(request)
    if not expected or not presented or not hmac.compare_digest(presented, expected):
        raise HTTPException(status_code=403, detail="Forbidden")
