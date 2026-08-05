"""Site-wide template context and the Systema Sanscriticum cross-link.

Extracted from `app.main` by H1927 / Lane D2.
"""

from urllib.parse import urlencode, urlparse

from app.settings import settings


def ss_link(medium: str) -> str:
    """Build a UTM-tagged link to Systema Sanscriticum.
    Handles the case where SYSTEMA_SANSCRITICUM_URL already contains a query string."""
    base = settings.SYSTEMA_SANSCRITICUM_URL
    if not base:
        return ""
    qs = urlencode({
        "utm_source": "samudramanthanam",
        "utm_medium": medium,
        "utm_campaign": "cross_link",
    })
    sep = "&" if urlparse(base).query else "?"
    return f"{base}{sep}{qs}"


def template_context(*, ss_medium: str = "", **extra) -> dict:
    """Common template context — site metadata + cross-link target."""
    base = {
        "site_name": "Пахтанье океана",
        "site_description": settings.SITE_DESCRIPTION,
        "public_base_url": settings.PUBLIC_BASE_URL,
        "ss_url": settings.SYSTEMA_SANSCRITICUM_URL,  # presence-check only
        "ss_link": ss_link(ss_medium) if ss_medium else "",
    }
    base.update(extra)
    return base
