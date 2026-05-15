import pytest
from fastapi.testclient import TestClient
from app.settings import settings
from importlib import reload
import app.main

def test_cors_development_unset_origins_uses_wildcard():
    """In development WITHOUT ALLOWED_ORIGINS set, allow any origin (`*`).
    This is the convenience default for local frontend development."""
    settings.APP_ENV = "development"
    settings.ALLOWED_ORIGINS = ""

    reload(app.main)
    client = TestClient(app.main.app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://random.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "*"
    assert response.headers.get("access-control-allow-credentials") is None


def test_cors_development_with_explicit_origins_respects_list():
    """If the dev sets an explicit allowlist, that wins over the wildcard."""
    settings.APP_ENV = "development"
    settings.ALLOWED_ORIGINS = "https://example.com"

    reload(app.main)
    client = TestClient(app.main.app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://random.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Random origin must NOT be allowed when the operator set a specific list
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_production_unset_origins_fails_closed():
    """REGRESSION: production with unset ALLOWED_ORIGINS used to default to '*'.
    It must now default to no origins — no cross-origin requests at all."""
    settings.APP_ENV = "production"
    settings.ALLOWED_ORIGINS = ""

    reload(app.main)
    client = TestClient(app.main.app)

    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Wildcard must NOT be sent for unset prod origins (the bug)
    assert response.headers.get("access-control-allow-origin") != "*"
    # Nor should any specific origin be allowed
    assert response.headers.get("access-control-allow-origin") is None

def test_cors_production():
    settings.APP_ENV = "production"
    settings.ALLOWED_ORIGINS = "https://example.com, https://app.samskrtam.ru"
    
    reload(app.main)
    client = TestClient(app.main.app)
    
    # Allowed origin
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "https://example.com"
    assert response.headers.get("access-control-allow-credentials") == "true"
    
    # Disallowed origin
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") is None
