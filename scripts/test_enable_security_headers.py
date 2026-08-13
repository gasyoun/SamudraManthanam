"""Hermetic tests for H2398 nginx HSTS inject + HTTP-only refuse."""

from __future__ import annotations

from pathlib import Path

import pytest

import enable_security_headers as esh

ROOT = Path(__file__).resolve().parent.parent
SNIPPET = "/etc/nginx/snippets/samudra-security-headers.conf"

# Live prod vhost as probed 13-08-2026 on 193.232.229.92 (before H2398).
LIVE_PROD = """\
# Samudra Manthanam — public via sslip.io (agent install 2026-08-07)
server {
    server_name samudra.193.232.229.92.sslip.io 193.232.229.92.sslip.io;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
        allow all;
    }

    location ~* (^/static/wasm/|^/static/.+\\.(woff2|woff|ttf)$) {
        root /opt/samudra/web;
        access_log off;
        add_header Cache-Control                "public, max-age=31536000, immutable";
        add_header Cross-Origin-Resource-Policy "same-origin";
        add_header Cross-Origin-Embedder-Policy "require-corp";
    }

    location /static/ {
        alias /opt/samudra/web/static/;
        access_log off;
        add_header Cache-Control                "no-cache";
        add_header Cross-Origin-Resource-Policy "same-origin";
        add_header Cross-Origin-Embedder-Policy "require-corp";
    }

    location /api/offline-packs/ {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        gzip               off;
    }

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_buffering    off;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/samudra.193.232.229.92.sslip.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/samudra.193.232.229.92.sslip.io/privkey.pem;
}

server {
    if ($host = samudra.193.232.229.92.sslip.io) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    listen [::]:80;
    server_name samudra.193.232.229.92.sslip.io 193.232.229.92.sslip.io;
    return 404; # managed by Certbot
}
"""

HTTP_ONLY = """\
server {
    listen 80;
    server_name example.test;
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
"""


def test_snippet_file_has_hsts_and_always():
    src = ROOT / "deploy" / "samudra-security-headers.conf"
    text = src.read_text(encoding="utf-8")
    assert "Strict-Transport-Security" in text
    assert "max-age=31536000" in text
    assert "X-Content-Type-Options" in text
    assert "X-Frame-Options" in text
    assert "Referrer-Policy" in text
    assert "Permissions-Policy" in text
    # `always` is required: prod HEAD / is 405, curl -sI would miss HSTS without it.
    assert text.count(" always;") >= 5


def test_inject_live_prod_https_only():
    new, stats = esh.inject_security_headers(LIVE_PROD, snippet_dst=SNIPPET)
    assert stats["https_servers"] == 1
    assert stats["http_only_servers"] == 1
    assert stats["https_touched"] == 1
    assert not esh.https_include_leaked_into_http(new, SNIPPET)

    servers = esh.iter_braced_blocks(new, "server")
    https = [b for _s, _e, b in servers if esh.is_https_server(b)]
    http = [b for _s, _e, b in servers if esh.is_http_only_server(b)]
    assert len(https) == 1
    assert len(http) == 1
    assert SNIPPET in https[0]
    assert SNIPPET not in http[0]
    # Locations that already use add_header must repeat the include
    # (nginx does not inherit add_header into them).
    for _loc_start, _loc_end, loc in esh.iter_braced_blocks(https[0], "location"):
        if "add_header" in loc:
            assert SNIPPET in loc


def test_inject_idempotent():
    once, _ = esh.inject_security_headers(LIVE_PROD, snippet_dst=SNIPPET)
    twice, stats = esh.inject_security_headers(once, snippet_dst=SNIPPET)
    assert twice == once
    assert stats["https_touched"] == 0


def test_refuse_http_only_site():
    new, stats = esh.inject_security_headers(HTTP_ONLY, snippet_dst=SNIPPET)
    assert stats["https_servers"] == 0
    assert stats["http_only_servers"] == 1
    assert new == HTTP_ONLY
    assert SNIPPET not in new


def test_refuse_existing_leak_into_http():
    leaked = HTTP_ONLY.replace(
        "listen 80;",
        f"    include {SNIPPET};\n    listen 80;",
    )
    with pytest.raises(RuntimeError, match="listen-80"):
        esh.inject_security_headers(leaked, snippet_dst=SNIPPET)


def test_https_stable_gate_refuses_http_200(monkeypatch):
    def fake_fetch(url, *, method="GET", timeout=20.0):
        if url.startswith("https://"):
            return 200, {"content-type": "application/json"}, b'{"status":"ok"}'
        return 200, {"content-type": "text/html"}, b"<html>app</html>"

    monkeypatch.setattr(esh, "fetch", fake_fetch)
    ok, reason, probe = esh.https_stable_gate("example.test")
    assert ok is False
    assert "fail condition" in reason
    assert probe["http_status"] == 200


def test_https_stable_gate_refuses_https_down(monkeypatch):
    def fake_fetch(url, *, method="GET", timeout=20.0):
        raise ConnectionError("tls handshake failed")

    monkeypatch.setattr(esh, "fetch", fake_fetch)
    ok, reason, _probe = esh.https_stable_gate("example.test")
    assert ok is False
    assert "refuse HSTS" in reason


def test_https_stable_gate_go(monkeypatch):
    def fake_fetch(url, *, method="GET", timeout=20.0):
        if url.startswith("https://"):
            return 200, {}, b"{}"
        return 301, {"location": "https://example.test/"}, b""

    monkeypatch.setattr(esh, "fetch", fake_fetch)
    ok, reason, probe = esh.https_stable_gate("example.test")
    assert ok is True
    assert probe["https_health_status"] == 200
    assert "301" in reason
