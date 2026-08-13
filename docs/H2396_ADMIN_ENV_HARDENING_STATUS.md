# H2396 / Wave P10 — admin key / env hardening: status

_Created: 13-08-2026 · Last updated: 13-08-2026_

**Handoff:** [H2396](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2396-Grok_SamudraManthanam_prod-admin-env-hardening_07.08.26.md)
**Executor:** Grok 4.6 (`grok-4.6`)
**Verdict 13-08-2026: DONE** (env half). HSTS / extra nginx security headers are
[H2398](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2398-Grok_SamudraManthanam_prod-nginx-hsts-security-headers_07.08.26.md), not this pass.

## Acceptance (locked in the handoff)

| Criterion | Status 13-08-2026 |
|---|---|
| chmod / ownership correct | **yes** — live `.env` `600 root:samudra`; parent `/opt/samudra` `755` (was `775`) |
| Admin key not world-readable | **yes after this pass** — three `644` `.env.bak*` siblings held `ADMIN_SECRET_KEY`; moved to `/root/samudra-env-backups/` `600` |
| Rotation steps in OPS | **yes** — [OPS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md) § Admin key / env hardening |
| `X-Admin-Key` still works | **yes** — `GET /api/corrections/pending` **200** with header / Bearer; old key **403** after rotate |
| Key never printed | **yes** — probes and apply script print lengths and HTTP statuses only |

Prove-with commands from the handoff (`ssh ls -l .env`; curl admin with header)
were run as `stat -c` + a Python header probe so the value never hit the session
transcript.

## Before (prod LXC `samskrtam150`, `193.232.229.92`)

| Path | Mode · owner | World-readable? |
|---|---|---|
| `/opt/samudra` | `775` `root:samudra`, no sticky bit | group-writable — `samudra` could unlink `.env` |
| `/opt/samudra/.env` | `600` `root:samudra` | no |
| `/opt/samudra/.env.bak-ai` | `644` `root:root` | **yes** — contains `ADMIN_SECRET_KEY` (len 64) |
| `/opt/samudra/.env.bak-before-true-openrouter` | `644` `root:root` | **yes** — same |
| `/opt/samudra/.env.bak-true-or-key` | `644` `root:root` | **yes** — same |
| `/root/samudra-admin-key.txt` | `600` `root:root` | no |
| `/opt/samudra/db/state.db` | `644` `samudra:samudra` | yes (PII / session hashes) |

`sudo -u {samudra,www-data,nobody} test -r` on each `.env.bak*`: **readable**.
`samudra` could not read the live `.env` but **could write the parent**.

Admin transport (live key, pre-rotate):

| Probe | Status |
|---|---|
| no header | 403 |
| `?key=not-the-real-key` | 400 |
| wrong `X-Admin-Key` | 403 |
| correct `X-Admin-Key` | 200 |
| `Authorization: Bearer` | 200 |

`ADMIN_SECRET_KEY` length 64, not empty. Public HTTPS had no
`Strict-Transport-Security` — left for H2398.

## What this pass changed on the host

1. Moved the three `.env.bak*` files to `/root/samudra-env-backups/` (`700` dir,
   files `600`).
2. Copied the live `.env` there as `.env.pre-h2396.20260813T185330Z` (`600`).
3. **Rotated** `ADMIN_SECRET_KEY` (new len 64) in `/opt/samudra/.env` and
   `/root/samudra-admin-key.txt`.
4. `chmod 755 /opt/samudra` — `samudra_can_write_parent=False`.
5. `chmod 640` on `/opt/samudra/db/state.db`.
6. Installed `/etc/systemd/system/samudra.service.d/umask.conf` (`UMask=0077`)
   and `systemctl daemon-reload && systemctl restart samudra`.
7. Host pointer `/opt/samudra/OPS.md` now points at the repo section.

## After (apply script `VERDICT=PASS`, 13-08-2026 18:53 UTC)

| Check | Result |
|---|---|
| unit | `active` |
| `local_home` | 200 |
| no header | 403 |
| query dummy | 400 |
| wrong header | 403 |
| **old** key after rotate | **403** |
| **new** `X-Admin-Key` | **200** |
| **new** Bearer | **200** |
| leftover `.env*` siblings under `/opt/samudra` | none |
| world-readable `.env*` under `/opt/samudra` | none |
| `samudra`/`www-data`/`nobody` can read live `.env` | no |
| public `https://samudra.193.232.229.92.sslip.io/` | 200 |
| public `/api/health` | 200 |

Re-check later:

```bash
python3 /opt/samudra/repo/scripts/check_env_hardening.py
```

## Out of scope (intentionally)

- **HSTS / nginx security-header paste** — sibling
  [H2398](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2398-Grok_SamudraManthanam_prod-nginx-hsts-security-headers_07.08.26.md).
- Narrowing systemd `ReadWritePaths=/opt/samudra` to `db/` + `logs/` +
  `offline-packs/` — would also stop a replaced `.env` from being rewritten
  *from inside the unit*, but it can break an unexpected write path. Parent
  `755` already blocks unlink. Left as a later tightening, not this exit.
- `/root/env-backups/` — those are **Systema** Laravel `.env` copies (PayPal,
  CRM, homework flags), not Samudra.

_Dr. Mārcis Gasūns_
