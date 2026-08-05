"""H1926 Lane C, acceptance C4–C7: admin transport and correction trust.

C4 — admin endpoints reject query-string credentials.
C5 — logs contain no credential values.
C6 — submitted email text alone grants neither verified identity nor elevated
     capability.
C7 — anonymous proposals remain possible under the low-trust/rate-limit path.
"""

import logging
import os

import aiosqlite
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.security import ADMIN_HEADER, redact_credentials
from app.services.rate_limit import ANONYMOUS_CORRECTION_LIMIT
from app.services.session_service import SESSION_HEADER, TRUST_ANONYMOUS, TRUST_VERIFIED
from app.settings import settings
from app.state_db import init_state_db

client = TestClient(app)

ADMIN_KEY = "s3cret-admin-key"


@pytest_asyncio.fixture(autouse=True)
async def state_db(tmp_path):
    db_path = str(tmp_path / "state_trust.db")
    settings.STATE_DB_PATH = db_path
    async with aiosqlite.connect(db_path) as db:
        await init_state_db(db)
    old_key, old_env = settings.ADMIN_SECRET_KEY, settings.APP_ENV
    settings.ADMIN_SECRET_KEY = ADMIN_KEY
    settings.APP_ENV = "development"
    yield db_path
    settings.ADMIN_SECRET_KEY, settings.APP_ENV = old_key, old_env
    if os.path.exists(db_path):
        os.remove(db_path)


def _propose(**overrides):
    payload = {
        "source_id": 1,
        "line_num": 10,
        "old_text": "old",
        "new_text": "new",
    }
    payload.update(overrides.pop("json", {}))
    return client.post("/api/corrections/propose", json=payload, **overrides)


def _register(email: str) -> None:
    response = client.post(
        "/api/identity/lead",
        json={"email": email, "consent_data": True, "consent_marketing": False},
    )
    assert response.status_code == 200


def _verified_session(email: str) -> str:
    """Run the real two-step verification loop and return a session token."""
    _register(email)
    requested = client.post("/api/identity/verify/request", json={"email": email})
    assert requested.status_code == 202
    token = requested.json()["verification_token"]
    confirmed = client.post("/api/identity/verify/confirm", json={"token": token})
    assert confirmed.status_code == 200
    return confirmed.json()["session_token"]


# ── C4: admin transport ──────────────────────────────────────────────────────


@pytest.mark.parametrize("path", ["/api/admin/vacuum", "/api/corrections/pending"])
def test_admin_endpoints_reject_query_string_credentials(path):
    """Even the CORRECT key in the query string is refused, not accepted.

    Accepting it "just this once" is what keeps clients on the leaky form
    forever; by the time the server sees it, the access log already has it.
    """
    method = client.post if "vacuum" in path else client.get
    response = method(f"{path}?key={ADMIN_KEY}")
    assert response.status_code == 400
    assert "header" in response.json()["detail"].lower()


@pytest.mark.parametrize("path", ["/api/admin/vacuum", "/api/corrections/pending"])
def test_admin_endpoints_accept_header_credentials(path):
    method = client.post if "vacuum" in path else client.get
    response = method(path, headers={ADMIN_HEADER: ADMIN_KEY})
    assert response.status_code == 200


def test_admin_endpoints_accept_bearer_authorization():
    response = client.get(
        "/api/corrections/pending",
        headers={"Authorization": f"Bearer {ADMIN_KEY}"},
    )
    assert response.status_code == 200


def test_admin_endpoints_reject_wrong_and_missing_header():
    assert client.get("/api/corrections/pending").status_code == 403
    assert client.get(
        "/api/corrections/pending", headers={ADMIN_HEADER: "wrong"}
    ).status_code == 403


def test_production_without_configured_key_closes_admin_surface():
    """An unset key must not fall back to the development default."""
    old_key, old_env = settings.ADMIN_SECRET_KEY, settings.APP_ENV
    settings.ADMIN_SECRET_KEY = ""
    settings.APP_ENV = "production"
    try:
        assert client.get(
            "/api/corrections/pending", headers={ADMIN_HEADER: "dev"}
        ).status_code == 403
    finally:
        settings.ADMIN_SECRET_KEY, settings.APP_ENV = old_key, old_env


# ── C5: log hygiene ──────────────────────────────────────────────────────────


def test_redactor_scrubs_credential_query_values():
    line = f'GET /api/corrections/pending?key={ADMIN_KEY}&mode=x HTTP/1.1" 400'
    scrubbed = redact_credentials(line)
    assert ADMIN_KEY not in scrubbed
    assert "key=REDACTED" in scrubbed
    assert "mode=x" in scrubbed  # non-credential params survive


@pytest.mark.parametrize("param", ["key", "token", "secret", "api_key", "admin_key"])
def test_redactor_covers_every_credential_parameter_name(param):
    assert ADMIN_KEY not in redact_credentials(f"/x?{param}={ADMIN_KEY}")


def test_filter_does_not_break_records_whose_template_holds_the_parameter_name():
    """Regression: redacting the *template* dropped a `%s` and broke logging.

    `"GET %s?key=%s"` has the credential split across template and args, so an
    in-place template rewrite turns `key=%s` into `key=REDACTED` while its
    argument survives — the handler then raises "not all arguments converted"
    and the record is lost. A filter that can silence logging is a worse
    failure than the leak it was added to prevent.
    """
    from app.security import CredentialRedactingFilter

    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="GET %s?key=%s", args=("/api/admin/vacuum", ADMIN_KEY), exc_info=None,
    )
    assert CredentialRedactingFilter().filter(record) is True
    rendered = record.getMessage()  # must not raise
    assert ADMIN_KEY not in rendered
    assert "/api/admin/vacuum" in rendered


def test_filter_leaves_clean_records_lazily_formatted():
    """No credential → no rewrite, so ordinary logging keeps its lazy args."""
    from app.security import CredentialRedactingFilter

    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="search mode=%s total=%d", args=("plain", 3), exc_info=None,
    )
    CredentialRedactingFilter().filter(record)
    assert record.msg == "search mode=%s total=%d"
    assert record.args == ("plain", 3)


def test_rejected_admin_request_logs_no_credential_value(caplog):
    """The refusal itself must not become the leak it was preventing.

    Scoped to server-side records: `httpx` also logs the outbound URL, but that
    is the *test client* narrating its own request, not application logging —
    no such logger exists in the deployed server. The filter still covers it
    wherever it reaches a real handler, which
    test_installed_filter_scrubs_third_party_records asserts directly.
    """
    with caplog.at_level(logging.DEBUG):
        client.get(f"/api/corrections/pending?key={ADMIN_KEY}")

    server_records = [r for r in caplog.records if not r.name.startswith("httpx")]
    assert server_records, "expected at least the refusal warning"
    for record in server_records:
        assert ADMIN_KEY not in record.getMessage()
    # …while still saying enough to diagnose the refusal.
    assert any(
        "credential passed in query parameter" in r.getMessage() for r in server_records
    )


def test_installed_filter_scrubs_third_party_records():
    """A record from any library is redacted once it reaches a filtered handler."""
    from app.security import CredentialRedactingFilter

    handler = logging.Handler()
    emitted: list[str] = []
    handler.emit = lambda record: emitted.append(record.getMessage())  # type: ignore[method-assign]
    handler.addFilter(CredentialRedactingFilter())

    third_party = logging.getLogger("some.third.party.client")
    third_party.addHandler(handler)
    third_party.setLevel(logging.INFO)
    try:
        third_party.info("HTTP Request: GET http://x/api?key=%s", ADMIN_KEY)
    finally:
        third_party.removeHandler(handler)

    assert emitted
    assert ADMIN_KEY not in emitted[0]
    assert "REDACTED" in emitted[0]


def test_access_log_record_is_redacted_by_the_installed_filter(caplog):
    """The uvicorn access logger carries the filter, not just our own logger."""
    access_logger = logging.getLogger("uvicorn.access")
    with caplog.at_level(logging.INFO, logger="uvicorn.access"):
        access_logger.info('%s - "%s"', "127.0.0.1", f"GET /x?key={ADMIN_KEY}")
    assert ADMIN_KEY not in caplog.text
    assert "REDACTED" in caplog.text


# ── C6: email text is not identity ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_submitted_email_does_not_link_a_correction_to_that_account(state_db):
    """The central C6 case: an account exists, someone else types its address."""
    _register("scholar@example.com")

    response = _propose(json={"email": "scholar@example.com"})
    assert response.status_code == 200
    assert response.json()["trust_tier"] == TRUST_ANONYMOUS

    async with aiosqlite.connect(state_db) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM corrections") as cursor:
            row = await cursor.fetchone()
    assert row["user_id"] is None, "typed email text must not bind an account"
    assert row["trust_tier"] == TRUST_ANONYMOUS
    assert row["contact_email"] == "scholar@example.com"  # kept as contact only


@pytest.mark.asyncio
async def test_verified_session_grants_attribution(state_db):
    token = _verified_session("verified@example.com")

    response = _propose(headers={SESSION_HEADER: token})
    assert response.status_code == 200
    assert response.json()["trust_tier"] == TRUST_VERIFIED

    async with aiosqlite.connect(state_db) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM corrections") as cursor:
            row = await cursor.fetchone()
    assert row["user_id"] is not None
    assert row["trust_tier"] == TRUST_VERIFIED


def test_forged_session_token_grants_nothing():
    response = _propose(headers={SESSION_HEADER: "not-a-real-session-token"})
    assert response.status_code == 200
    assert response.json()["trust_tier"] == TRUST_ANONYMOUS


def test_verification_challenge_is_single_use():
    email = "onceonly@example.com"
    _register(email)
    token = client.post("/api/identity/verify/request", json={"email": email}).json()[
        "verification_token"
    ]
    assert client.post("/api/identity/verify/confirm", json={"token": token}).status_code == 200
    replay = client.post("/api/identity/verify/confirm", json={"token": token})
    assert replay.status_code == 400


def test_verification_request_does_not_enumerate_accounts():
    """Unknown and known addresses must be indistinguishable in status/shape."""
    known = "known@example.com"
    _register(known)
    known_response = client.post("/api/identity/verify/request", json={"email": known})
    unknown_response = client.post(
        "/api/identity/verify/request", json={"email": "nobody@example.com"}
    )
    assert known_response.status_code == unknown_response.status_code == 202
    assert known_response.json()["status"] == unknown_response.json()["status"]


def test_lead_capture_does_not_expose_internal_user_id():
    response = client.post(
        "/api/identity/lead",
        json={"email": "lead@example.com", "consent_data": True, "consent_marketing": False},
    )
    assert response.status_code == 200
    assert "user_id" not in response.json()


# ── C7: anonymous intake stays open, under a cap ─────────────────────────────


def test_anonymous_proposal_is_accepted_without_any_identity():
    response = _propose()
    assert response.status_code == 200
    assert response.json()["trust_tier"] == TRUST_ANONYMOUS


def test_anonymous_proposals_are_rate_limited():
    for i in range(ANONYMOUS_CORRECTION_LIMIT):
        assert _propose().status_code == 200, f"proposal {i} should be accepted"

    blocked = _propose()
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_verified_session_gets_a_higher_cap_than_anonymous(state_db):
    """A verified actor is not merely labelled differently — it is treated so."""
    token = _verified_session("bulk@example.com")
    for _ in range(ANONYMOUS_CORRECTION_LIMIT + 1):
        response = _propose(headers={SESSION_HEADER: token})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_every_proposal_writes_an_audit_row_naming_its_trust_tier(state_db):
    _propose()
    token = _verified_session("audited@example.com")
    _propose(headers={SESSION_HEADER: token})

    async with aiosqlite.connect(state_db) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM correction_audit ORDER BY id"
        ) as cursor:
            rows = await cursor.fetchall()

    assert len(rows) == 2
    assert [r["trust_tier"] for r in rows] == [TRUST_ANONYMOUS, TRUST_VERIFIED]
    assert all(r["action"] == "proposed" for r in rows)
    assert all(r["actor_ip_hash"] for r in rows)
    assert rows[0]["actor_user_id"] is None
    assert rows[1]["actor_user_id"] is not None


@pytest.mark.asyncio
async def test_correction_records_canonical_link_id_when_supplied(state_db):
    _propose(json={"link_id": "1.10"})
    async with aiosqlite.connect(state_db) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT link_id FROM corrections") as cursor:
            row = await cursor.fetchone()
    assert row["link_id"] == "1.10"
