# Deployment Guide — Samudra Manthanam (No-Docker VPS)

_Created: 19-06-2026 · Last updated: 13-08-2026_

This guide covers a plain-Python deployment on a Debian/Ubuntu VPS using
**systemd + nginx**. No Docker is required.

**Day-2 operator path (pull / pip / restart / code rollback / smoke):** see
[OPS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md) — that
file is the single copy-paste surface for live deploys. This document remains
the first-time install + corpus publish reference.

**Current production (Wave P, LXC `samskrtam150` / `193.232.229.92`):**
`/opt/samudra`, public
`https://samudra.193.232.229.92.sslip.io/`, unit `samudra`. Do not point
nginx `server_name` at `samskrte.ru` (separate product on the same host).

---

## Prerequisites

| Software | Minimum version | Install |
|---|---|---|
| Python | 3.11+ (prod runs 3.13) | `apt install python3 python3-venv` |
| git | any | `apt install git` |
| nginx | any | `apt install nginx` |
| certbot | any | `apt install certbot python3-certbot-nginx` |

A dedicated system user (`samudra`) with no login shell is assumed throughout.
Create it once:

```bash
adduser --system --group --no-create-home samudra
```

---

## Directory layout on the VPS

Canonical production layout (probed 08-08-2026 on `193.232.229.92`):

```
/opt/samudra/
├── repo/               ← git clone lives here
├── web -> repo/web     ← symlink; systemd WorkingDirectory + nginx static root
├── venv/               ← Python virtual environment
├── corpus/             ← corpus source files (Data/ + Programdata/) when present
│   ├── Data/
│   └── Programdata/
│       └── data.txt
├── db/
│   ├── corpus.db       ← live search database
│   ├── state.db        ← mutable state (morph cache, corrections, migrations)
│   ├── corpus.next.db  ← temp DB built during publish (absent when idle)
│   └── backups/        ← timestamped corpus_*.db backups
└── .env                ← environment variables (not in git; mode 600)
```

Set `STATE_DB_PATH=/opt/samudra/db/state.db` and
`DB_PATH=/opt/samudra/db/corpus.db` in `.env` so the unit and tools agree.
Older drafts put `state.db` at `/opt/samudra/state.db` — prefer the `db/` path
on new installs so `ReadWritePaths=/opt/samudra` stays one tree.

---

## First-time setup

### 1. Clone the repository

```bash
mkdir -p /opt/samudra
cd /opt/samudra
git clone https://github.com/gasyoun/SamudraManthanam.git repo
```

### 2. Create the virtual environment

```bash
python3.11 -m venv /opt/samudra/venv
/opt/samudra/venv/bin/pip install --upgrade pip
/opt/samudra/venv/bin/pip install -r /opt/samudra/repo/web/requirements.txt
```

### 3. Create the `.env` file

```bash
cat > /opt/samudra/.env <<'EOF'
APP_ENV=production

# Corpus database (read-only after ingest)
DB_PATH=/opt/samudra/db/corpus.db

# Mutable state database (morph cache, corrections, leads)
# Prefer under db/ (prod layout). Older installs may use /opt/samudra/state.db.
STATE_DB_PATH=/opt/samudra/db/state.db

# URL the app is reachable at (used for export link generation)
PUBLIC_BASE_URL=https://<YOUR_DOMAIN>

# CORS — comma-separated list of allowed origins
ALLOWED_ORIGINS=https://<YOUR_DOMAIN>

# Admin API key (for /api/admin/vacuum and /api/corrections/pending).
# Sent as a HEADER, never as ?key= — a query-string credential is refused with
# 400 because the access log has already recorded it by then. See
# web/IDENTITY_TRUST_CONTRACT.md §1.
#   curl -X POST -H "X-Admin-Key: $ADMIN_SECRET_KEY" https://<host>/api/admin/vacuum
# Unset in production = the admin surface is closed (403), not open with a default.
ADMIN_SECRET_KEY=<generate a long random string>

# Cross-link target — paid course platform (leave blank to hide the CTA banner)
SYSTEMA_SANSCRITICUM_URL=https://systema-sanscriticum.ru

# Custom site description used in OG tags + meta description (optional)
SITE_DESCRIPTION=Поисковая система по санскрито-русскому параллельному корпусу.

# AI explanation backend (optional — leave blank to disable)
AI_PROVIDER=openai-compatible
AI_BASE_URL=
AI_API_KEY=
AI_MODEL=
EOF
chmod 600 /opt/samudra/.env
chown root:samudra /opt/samudra/.env
# Parent must NOT be group-writable: 775 lets the samudra user unlink .env
# and drop a replacement even though the file itself is 600.
chmod 755 /opt/samudra
chown root:samudra /opt/samudra
```

Generate a random admin key: `python3 -c "import secrets; print(secrets.token_hex(32))"`

**Do not leave `.env.bak*` next to the live file.** Copies default to `644`
and then `nobody` / `www-data` (Systema on the same LXC) can read
`ADMIN_SECRET_KEY`. Park backups under `/root/samudra-env-backups/` mode
`700`, files `600`. Day-2 rotation and the permission check live in
[OPS.md § Admin key / env hardening](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md).

### 4. Create required directories

```bash
mkdir -p /opt/samudra/db/backups
# Symlink so systemd WorkingDirectory=/opt/samudra/web matches nginx static root
ln -sfn /opt/samudra/repo/web /opt/samudra/web
chown -R samudra:samudra /opt/samudra/db 2>/dev/null || true
```

### 5. Install the corpus

Copy your corpus files to the VPS (rsync, scp, or mount):

```
/opt/samudra/corpus/Programdata/data.txt   ← one filename per line
/opt/samudra/corpus/Data/*.html             ← corpus HTML files
```

### 6. Build the initial corpus database

```bash
CORPUS_PATH=/opt/samudra/corpus \
DB_PATH=/opt/samudra/db/corpus.db \
NEXT_DB_PATH=/opt/samudra/db/corpus.next.db \
BACKUP_DIR=/opt/samudra/db/backups \
VENV=/opt/samudra/venv \
  /opt/samudra/repo/reindex.sh
```

Verify success:

```bash
/opt/samudra/venv/bin/python /opt/samudra/repo/web/scripts/smoke_check.py \
    --db-path /opt/samudra/db/corpus.db \
    --min-sources 1
# Expected output: OK    sources=N  lines=N  version=vYYYY.MM.DD
```

---

## systemd service

```bash
cp /opt/samudra/repo/deploy/samudra.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now samudra
systemctl status samudra
```

The unit file (`deploy/samudra.service`) starts uvicorn on `127.0.0.1:8000`
with 2 workers. Edit `--workers` to match available CPU cores.

Check logs:

```bash
journalctl -u samudra -f
```

---

## nginx reverse proxy

```bash
cp /opt/samudra/repo/deploy/samudra.nginx /etc/nginx/sites-available/samudra
# Edit the file: replace <YOUR_DOMAIN> with your actual domain
nano /etc/nginx/sites-available/samudra

ln -s /etc/nginx/sites-available/samudra /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### Add HTTPS (Let's Encrypt)

```bash
certbot --nginx -d <YOUR_DOMAIN>
```

Certbot rewrites the nginx config and installs an auto-renewal cron job.

### Security headers (Wave P10b / H2398) — only after HTTPS is stable

Do **not** paste `Strict-Transport-Security` into the listen-80 bootstrap
file above. HSTS on a host that is still HTTP-only (or whose cert is broken)
pins browsers to a service they cannot reach.

After `curl -sS https://<YOUR_DOMAIN>/api/health` returns 200 and HTTP
301s to HTTPS:

```bash
python3 /opt/samudra/repo/scripts/enable_security_headers.py
# expect: GATE GO

python3 /opt/samudra/repo/scripts/enable_security_headers.py --apply

curl -sI https://<YOUR_DOMAIN>/ | grep -i strict
# expect: strict-transport-security: max-age=31536000; includeSubDomains
```

The snippet is [`deploy/samudra-security-headers.conf`](https://github.com/gasyoun/SamudraManthanam/blob/main/deploy/samudra-security-headers.conf).
It is included only in `listen 443` servers. The `always` flag is required
because this app answers HEAD `/` with 405 (`curl -sI` is HEAD).

Status: [`docs/H2398_NGINX_HSTS_SECURITY_HEADERS_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2398_NGINX_HSTS_SECURITY_HEADERS_STATUS.md).

### Branded hostname (Wave P5 / H2391) — human DNS first

Production today is reachable at the free sslip fallback:

`https://samudra.193.232.229.92.sslip.io/`

A **branded** name (recommended: `samudra.samskrte.ru`) is **not done** until:

1. A human creates an **A-record** → `193.232.229.92` (apex `samskrte.ru` NS is reg.ru).
2. Certbot issues a cert for that name and nginx serves HTTPS.
3. `curl -I https://<name>/api/health` returns **200**.
4. The sslip Host still returns 200 (permanent fallback; P11 keeps `samskrte.ru` Systema vhost separate).

**Do not treat missing DNS as done.** The gate script exits **2** on NXDOMAIN / wrong IP:

```bash
# On the LXC as root, after git pull of this repo under /opt/samudra/repo:
python3 /opt/samudra/repo/scripts/enable_branded_hostname.py \
  --hostname samudra.samskrte.ru
# → REFUSE exit 2 while DNS is missing

# After the A-record propagates (GATE GO):
python3 /opt/samudra/repo/scripts/enable_branded_hostname.py \
  --hostname samudra.samskrte.ru --apply

curl -I https://samudra.samskrte.ru/api/health
curl -I https://samudra.193.232.229.92.sslip.io/api/health
```

What `--apply` does: injects the branded name into every `server_name` line that
already carries the sslip Host (never removes sslip), `nginx -t` + reload,
`certbot --nginx -d <name> --redirect`, then dual HTTPS smoke.

Status snapshot (why this may still be blocked):  
[`docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md) · live notes [`OPS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md).

Optional after branded HTTPS is green: set `PUBLIC_BASE_URL` / `ALLOWED_ORIGINS` in
`/opt/samudra/.env` to include the branded origin, then `systemctl restart samudra`.

### Offline-search packs — do NOT touch the gzip encoding

The optional offline-search feature serves large SQLite packs pre-compressed
(`/api/offline-packs/{base,dict}.db`, sent with `Content-Encoding: gzip`). The
shipped `deploy/samudra.nginx` already handles this with a dedicated
`location /api/offline-packs/` block. Two rules for any nginx edit:

- **Never** add `application/octet-stream` to `gzip_types`, and **never** set
  `gunzip on;`. Either one corrupts the packs: re-gzipping double-encodes the
  body (the browser inflates only the outer layer → invalid `.db`), and `gunzip`
  inflates + strips `Content-Encoding`, ballooning the wire to ~206 MB and
  breaking the client's progress math. Pass the body through untouched.
- The `location /static/` block intentionally sets `Cross-Origin-Resource-Policy`
  and `Cross-Origin-Embedder-Policy` headers. These are **required** — they let
  the cross-origin-isolated `/offline-settings` page load the search worker.
  Removing them breaks offline search (the worker fails to load).

Note: the offline-pack page uses `crypto.subtle` (SHA-256 verification), which
browsers expose only in a **secure context** — serve over HTTPS (or localhost).

Packs are built with `python scripts/build_offline_pack.py` (writes
`{type}.db`, `{type}.db.gz`, and `{type}.db.sha256` into `web/offline-packs/`).
The gate is on the gzipped wire size.

---

## Ongoing corpus publish

After updating the corpus files under `/opt/samudra/corpus/`:

```bash
CORPUS_PATH=/opt/samudra/corpus \
DB_PATH=/opt/samudra/db/corpus.db \
NEXT_DB_PATH=/opt/samudra/db/corpus.next.db \
BACKUP_DIR=/opt/samudra/db/backups \
VENV=/opt/samudra/venv \
  /opt/samudra/repo/reindex.sh
```

The script validates the corpus, builds a fresh DB into `corpus.next.db`,
runs `PRAGMA integrity_check`, smoke-checks row counts, backs up the old DB,
then atomically swaps the new one in. The live app continues serving requests
during the build phase and picks up the new DB on the next connection.

### Automate with cron

```bash
crontab -e   # as root or the samudra user
```

```cron
# Rebuild corpus at 03:00 every day
0 3 * * * CORPUS_PATH=/opt/samudra/corpus DB_PATH=/opt/samudra/db/corpus.db NEXT_DB_PATH=/opt/samudra/db/corpus.next.db BACKUP_DIR=/opt/samudra/db/backups VENV=/opt/samudra/venv /opt/samudra/repo/reindex.sh >> /var/log/samudra-reindex.log 2>&1
```

---

## Smoke-test command

Run at any time to verify the live DB:

```bash
/opt/samudra/venv/bin/python /opt/samudra/repo/web/scripts/smoke_check.py \
    --db-path /opt/samudra/db/corpus.db \
    --min-sources 5
```

Exit code is `0` on success, `1` if the DB is missing, unreadable, or below
`--min-sources`. Safe to call from a cron health check or monitoring script.

---

## Updating the application code

**Authoritative copy-paste runbook (record PREV SHA, ff-only pull, pip,
restart, smoke, code rollback):**
[OPS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md).

Short form (app code / dependency bumps only — not corpus reindex):

```bash
cd /opt/samudra/repo
PREV=$(git rev-parse --short HEAD)
git pull --ff-only origin main
/opt/samudra/venv/bin/pip install -r web/requirements.txt
systemctl restart samudra
curl -fsS -o /dev/null -w "local_home=%{http_code}\n" http://127.0.0.1:8000/
systemctl is-active samudra
echo "ROLLBACK_SHA=$PREV"
```

- Prefer `git pull --ff-only origin main` over bare `git pull` so a divergent
  prod checkout fails loudly instead of inventing a merge commit.
- Always capture `PREV` before pull if you may need a code rollback.
- After restart, smoke **local** `127.0.0.1:8000` first; public sslip.io can
  hairpin-fail from inside the LXC while the app is healthy.

### Code rollback

```bash
cd /opt/samudra/repo
git reset --hard "$ROLLBACK_SHA"   # the SHA printed before the bad deploy
/opt/samudra/venv/bin/pip install -r web/requirements.txt
systemctl restart samudra
curl -fsS -o /dev/null -w "local_home=%{http_code}\n" http://127.0.0.1:8000/
```

Full notes (unit re-sync, nginx caveats, what not to force-push):
[OPS.md § Code rollback](https://github.com/gasyoun/SamudraManthanam/blob/main/OPS.md#code-rollback).

---

## Rollback a corpus publish

Backups are stored as `corpus_YYYYMMDD_HHMMSS.db` in `/opt/samudra/db/backups/`.
To revert:

```bash
# Stop traffic briefly (optional — swap is atomic but keeps connections warm)
ls -lt /opt/samudra/db/backups/       # find the backup to restore
cp /opt/samudra/db/backups/corpus_YYYYMMDD_HHMMSS.db /opt/samudra/db/corpus.db
```

The app reads `corpus.db` fresh on each request, so the rollback takes effect
immediately on the next search without a restart.

This is **independent** of code rollback: restoring a DB does not change
`/opt/samudra/repo` HEAD, and `git reset --hard` does not restore a corpus
backup.
