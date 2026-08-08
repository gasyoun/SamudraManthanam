# H2391 / Wave P5 — branded hostname + TLS status

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2391](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2391-Grok_SamudraManthanam_prod-branded-hostname-tls_07.08.26.md)  
**Executor (agent half):** Grok 4.5 (`grok-4.5`)  
**Verdict 08-08-2026: NOT DONE** — human DNS missing (fail condition of the handoff).

## Acceptance (locked)

| Criterion | Status 08-08-2026 |
|---|---|
| HTTPS 200 on branded host (`curl -I https://<name>/api/health`) | **blocked** — no branded A-record |
| nginx `server_name` includes branded host | only sslip today |
| cert path under `/etc/letsencrypt/live/<name>/` | only sslip + samskrte.ru |
| Fail = DNS missing treated as done | **honoured** — refused |

## Measured prod state (LXC `samskrtam150` / `193.232.229.92`)

| Probe | Result |
|---|---|
| Local app | `http://127.0.0.1:8000/api/health` → `{"status":"ok",…}` corpus 230 sources |
| Public fallback | `https://samudra.193.232.229.92.sslip.io/` TLS live (certbot, expiry ~2026-11-05) |
| nginx `server_name` | `samudra.193.232.229.92.sslip.io` (+ bare sslip) only — **samskrte.ru untouched** (P11) |
| `samudra.samskrte.ru` | **NXDOMAIN** (`host` → not found) |
| `samudra.samskrtam.ru` | **NXDOMAIN** |
| Apex `samskrte.ru` NS | `ns1.reg.ru` / `ns2.reg.ru` (human DNS panel) |
| Apex A | `samskrte.ru` / `www` → `193.232.229.92` (same LXC) |

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

Then close H2391 with evidence: nginx `server_name` line + `/etc/letsencrypt/live/<name>/` path + the 200 curl.

## Explicit non-goals this pass

- Inventing or guessing a paid TLD purchase  
- Taking over `samskrte.ru` / `www` vhost (P11 co-host safety)  
- Enabling HSTS on a hostname that is not yet live (see H2398)  
- Treating sslip-only HTTPS as branded-host done  

_Dr. Mārcis Gasūns_
