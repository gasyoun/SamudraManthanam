# H2391 / Wave P5 — branded hostname + TLS status

_Created: 08-08-2026 · Last updated: 14-08-2026_

**Handoff:** [H2391](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2391-Grok_SamudraManthanam_prod-branded-hostname-tls_07.08.26.md)  
**Executor (agent half):** Grok 4.5 (`grok-4.5`)  
**Executor (apply):** Grok 4.6 (`grok-4.6`)  
**Verdict 14-08-2026: DONE** — A-record live, certbot issued, GET `/api/health` 200 on branded + sslip.

## Acceptance (locked)

| Criterion | Status 14-08-2026 |
|---|---|
| HTTPS 200 on branded host (`GET https://samudra.samskrte.ru/api/health`) | **200** (public fetch + `--resolve` on-box) |
| nginx `server_name` includes branded host | `samudra.samskrte.ru` + both sslip names |
| cert path under `/etc/letsencrypt/live/<name>/` | lineage `samudra.193.232.229.92.sslip.io` with SANs branded + both sslip |
| Fail = DNS missing treated as done | **honoured** 08-08; DNS GO 14-08 then `--apply` |

## Measured prod state (LXC `samskrtam150` / `193.232.229.92`)

| Probe | Result 14-08-2026 |
|---|---|
| Local app | `http://127.0.0.1:8000/api/health` → `{"status":"ok",…}` corpus 235 sources |
| Public branded | `https://samudra.samskrte.ru/api/health` **200** |
| Public fallback | `https://samudra.193.232.229.92.sslip.io/` still **200** |
| nginx `server_name` | `samudra.samskrte.ru samudra.193.232.229.92.sslip.io 193.232.229.92.sslip.io` — **apex `samskrte.ru` untouched** (P11) |
| Cert SANs | `samudra.samskrte.ru`, `samudra.193.232.229.92.sslip.io`, `193.232.229.92.sslip.io` (expiry 2026-11-12) |
| `samudra.samskrte.ru` DNS | A → `193.232.229.92` (TTL 86400) |
| `samudra.samskrtam.ru` | still NXDOMAIN (not used) |
| `PUBLIC_BASE_URL` | `https://samudra.samskrte.ru` |
| First `--apply` footgun | branded-only cert broke sslip SNI; expanded SANs same pass; script now issues all three names |

Script gate (must exit **2** while DNS missing)::

```bash
python3 scripts/enable_branded_hostname.py --hostname samudra.samskrte.ru
# expected: REFUSE exit 2
```

## What shipped this pass (agent half)

1. **DNS-gated enabler** — [`scripts/enable_branded_hostname.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/enable_branded_hostname.py)  
   - exit 2 on NXDOMAIN / wrong A  
   - `--apply` only after gate GO: inject `server_name`, `nginx -t` + reload, certbot, dual smoke (branded + sslip)
2. **Operator path** — [`DEPLOYMENT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md) § Branded hostname (Wave P5)  
3. **Repo OPS mirror** — [`OPS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md) (incl. branded section; prod copy at `/opt/samudra/OPS.md`)

## Human checkpoint (reg.ru)

Recommended record (a human chooses the final label; this is the default recommendation):

| Type | Name | Value |
|---|---|---|
| A | `samudra` (FQDN `samudra.samskrte.ru`) | `193.232.229.92` |

Optional AAAA only if the LXC has a stable public IPv6 (none required for H2391).

After the A-record propagates:

```bash
ssh root@193.232.229.92
cd /opt/samudra/repo && git pull --ff-only origin main
python3 scripts/enable_branded_hostname.py --hostname samudra.samskrte.ru
# when GATE GO:
python3 scripts/enable_branded_hostname.py --hostname samudra.samskrte.ru --apply
curl -I https://samudra.samskrte.ru/api/health   # expect 200
curl -I https://samudra.193.232.229.92.sslip.io/api/health  # still 200
```

Closed 14-08-2026: nginx `server_name` includes branded + sslip; cert lineage `/etc/letsencrypt/live/samudra.193.232.229.92.sslip.io/`; `GET https://samudra.samskrte.ru/api/health` 200.

## Explicit non-goals this pass

- Inventing or guessing a paid TLD purchase  
- Taking over `samskrte.ru` / `www` vhost (P11 co-host safety)  
- Enabling HSTS on a hostname that is not yet live (see H2398; now live on the shared vhost)  
- Treating sslip-only HTTPS as branded-host done  

_Dr. Mārcis Gasūns_
