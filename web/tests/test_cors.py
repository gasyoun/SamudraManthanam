import pytest
from fastapi.testclient import TestClient
from app.settings import settings
from importlib import reload
import app.main

def test_cors_development():
    # settings is a singleton, but app.main imports it.
    # We might need to reload app.main if we change settings before it's imported,
    # or just check current state.
    settings.APP_ENV = "development"
    settings.ALLOWED_ORIGINS = "https://example.com"
    
    # Reload main to re-run middleware setup logic
    reload(app.main)
    client = TestClient(app.main.app)
    
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://random.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # In dev, wildcard should allow random origin
    assert response.headers.get("access-control-allow-origin") == "*"
    assert response.headers.get("access-control-allow-credentials") is None # False means omitted

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
