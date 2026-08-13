# H2398 / Wave P10b — HSTS + nginx security headers: status

_Created: 13-08-2026 · Last updated: 13-08-2026_

**Handoff:** [H2398](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2398-Grok_SamudraManthanam_prod-nginx-hsts-security-headers_07.08.26.md)
**Executor:** Grok 4.6 (`grok-4.6`)
**Verdict 13-08-2026: DONE** on the live sslip HTTPS vhost. Branded-host
DNS (`samudra.samskrte.ru`) is still NXDOMAIN (H2391); that name is not
in `server_name` and does not receive HSTS.

## Acceptance (locked in the handoff)

| Criterion | Status 13-08-2026 |
|---|---|
| Headers present on `curl -sI` | **yes** — `Strict-Transport-Security: max-age=31536000; includeSubDomains` on HEAD `/` (405 from the app; nginx `always` still attaches the header) |
| Prove-with `curl -sI \| grep -i strict` | **yes** — see evidence below |
| On our data: prod nginx | **yes** — `/etc/nginx/sites-available/samudra` + `/etc/nginx/snippets/samudra-security-headers.conf` |
| Fail = HSTS on broken HTTP-only | **honoured** — gate refuses unless HTTPS `/api/health` is 200 **and** HTTP is a 3xx to `https://` |

Also set on the HTTPS vhost (same snippet): `X-Content-Type-Options: nosniff`,
`X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`,
`Permissions-Policy: geolocation=(), microphone=(), camera=()`.

## Before (prod LXC `samskrtam150`, `193.232.229.92`)

| Probe | Result |
|---|---|
| `GET https://samudra.193.232.229.92.sslip.io/` | 200, COOP only — **no** HSTS / nosniff / frame / referrer |
| `HEAD https://samudra.193.232.229.92.sslip.io/` | 405 (FastAPI) — no HSTS |
| `GET https://…/api/health` | 200 |
| `GET http://samudra.193.232.229.92.sslip.io/` | 301 → `https://samudra.193.232.229.92.sslip.io/` |
| Cert | Let's Encrypt, CN=`samudra.193.232.229.92.sslip.io`, 07-08-2026 → 05-11-2026 |
| Live vhost | certbot-rewritten `/etc/nginx/sites-available/samudra` (443 + 80), no security-header include |

HTTPS has been serving that cert since 07-08-2026 (six days at this pass).
HTTP already redirected. Gate GO.

## What this pass changed

1. Committed snippet [`deploy/samudra-security-headers.conf`](https://github.com/gasyoun/SamudraManthanam/blob/main/deploy/samudra-security-headers.conf).
2. Gate + apply script [`scripts/enable_security_headers.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/enable_security_headers.py)
   (exit 2 if HTTPS is down or HTTP still serves the app).
3. Installed the snippet on the box at `/etc/nginx/snippets/samudra-security-headers.conf`.
4. Included it in the **listen 443** server and in every `location` that already
   had `add_header` (nginx does not inherit `add_header` into those). The
   listen-80 server was left untouched.
5. `nginx -t` + `systemctl reload nginx`.
6. H2391's [`scripts/enable_branded_hostname.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/enable_branded_hostname.py)
   now re-applies the same include after certbot (certbot rewrites the vhost).

## After (apply script `DONE`, 13-08-2026 20:28 UTC)

`inject: https_servers=1 http_only_servers=1 https_touched=1` · `nginx -t`
ok · `systemctl reload nginx`. Listen-80 server has **no** include.

| Probe (public, from outside the LXC) | Result |
|---|---|
| `curl -sI https://samudra.193.232.229.92.sslip.io/` | **405** + `Strict-Transport-Security: max-age=31536000; includeSubDomains` + nosniff + SAMEORIGIN + referrer + permissions |
| `GET https://…/` | **200** + same HSTS set + COOP |
| `GET https://…/api/health` | **200** + HSTS set |
| `GET http://…/` | **301** → `https://samudra.193.232.229.92.sslip.io/` — **no** HSTS |
| `HEAD https://…/static/style.css` | **200** + HSTS set + CORP/COEP + `Cache-Control: no-cache` |

On-box gate used a hairpin fallback (`curl --resolve …:127.0.0.1`): the LXC
cannot open its own public sslip name (no hairpin NAT); that is not a TLS
failure. Public prove-with above is the handoff evidence.

Operator re-check:

```bash
python3 /opt/samudra/repo/scripts/enable_security_headers.py
# expect: GATE GO (exit 0, dry)

curl -sI https://samudra.193.232.229.92.sslip.io/ | grep -i strict
# expect: strict-transport-security: max-age=31536000; includeSubDomains

curl -sS -o /dev/null -w "%{http_code}\n" https://samudra.193.232.229.92.sslip.io/api/health
# expect: 200
```

## Out of scope (intentionally)

- **Branded hostname HSTS** — there is no branded 443 vhost yet (H2391,
  human A-record). When that lands, `enable_branded_hostname.py --apply`
  re-includes this snippet.
- **`preload`** — not in the locked snippet; HSTS preload is hard to undo.
- **FastAPI `security_headers` middleware** — that path is HTTP-behind-nginx
  in prod and must not emit HSTS on a development HTTP origin.

_Dr. Mārcis Gasūns_
