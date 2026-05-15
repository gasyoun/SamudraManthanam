# Deployment Guide — Samudra Manthanam (No-Docker VPS)

This guide covers a plain-Python deployment on a Debian/Ubuntu VPS using
**systemd + nginx**. No Docker is required.

---

## Prerequisites

| Software | Minimum version | Install |
|---|---|---|
| Python | 3.11 | `apt install python3.11 python3.11-venv` |
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

```
/opt/samudra/
├── repo/               ← git clone lives here
├── venv/               ← Python virtual environment
├── corpus/             ← corpus source files (Data/ + Programdata/)
│   ├── Data/
│   └── Programdata/
│       └── data.txt
├── db/
│   ├── corpus.db       ← live search database
│   ├── corpus.next.db  ← temp DB built during publish (deleted on success)
│   └── backups/        ← timestamped DB backups
├── state.db            ← mutable state (morph cache, corrections, leads)
└── .env                ← environment variables (not in git)
```

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
STATE_DB_PATH=/opt/samudra/state.db

# URL the app is reachable at (used for export link generation)
PUBLIC_BASE_URL=https://<YOUR_DOMAIN>

# CORS — comma-separated list of allowed origins
ALLOWED_ORIGINS=https://<YOUR_DOMAIN>

# Admin API key (for /api/admin/vacuum and /api/corrections/pending)
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
```

Generate a random admin key: `python3 -c "import secrets; print(secrets.token_hex(32))"`

### 4. Create required directories

```bash
mkdir -p /opt/samudra/db/backups
chown -R samudra:samudra /opt/samudra/db /opt/samudra/state.db 2>/dev/null || true
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

```bash
cd /opt/samudra/repo
git pull
/opt/samudra/venv/bin/pip install -r web/requirements.txt
systemctl restart samudra
```

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
