# OPS.md — Samudra Manthanam production operator path

_Created: 08-08-2026 · Last updated: 09-08-2026_  
_(+ H2391 branded-hostname section)_

**Purpose:** one copy-paste path for code deploy, smoke, and rollback on the live box.
First-time install, systemd unit, nginx, and corpus reindex live in
[DEPLOYMENT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md).
This file is the **day-2 operator** surface.

**Host (as of 08-08-2026 probe):** LXC `samskrtam150` · `root@193.232.229.92` ·
layout under `/opt/samudra/`. Public search:
`https://samudra.193.232.229.92.sslip.io/` (TLS via certbot; `samskrte.ru` is a
different vhost and must not be edited for Samudra).

---

## Live layout (ground truth)

```
/opt/samudra/
├── .env                 # EnvironmentFile for systemd (mode 600, root:samudra)
├── OPS.md               # Host-local short notes (optional; repo copy is canonical)
├── repo/                # git clone of gasyoun/SamudraManthanam (branch main)
├── web -> repo/web      # symlink used by WorkingDirectory + nginx static root
├── venv/                # Python 3.13 venv (do not replace casually)
├── corpus/              # source HTML / data.txt for reindex (optional empty)
└── db/
    ├── corpus.db        # live search DB
    ├── state.db         # morph cache, corrections, schema_migrations
    ├── corpus.next.db   # temp during reindex (absent when idle)
    ├── corpus.build-report.json
    └── backups/         # corpus_YYYYMMDD_HHMMSS.db
```

| Surface | Path / command |
|---|---|
| App unit | `systemctl {status,restart,stop,start} samudra` |
| Unit file on disk | `/etc/systemd/system/samudra.service` (source: `deploy/samudra.service`) |
| uvicorn (bound) | `127.0.0.1:8000`, 2 workers, user `samudra` |
| nginx site | `/etc/nginx/sites-enabled/samudra` (sslip.io server_name only) |
| Repo | `/opt/samudra/repo` |
| Venv Python | `/opt/samudra/venv/bin/python` (3.13.x on prod) |
| Logs | `journalctl -u samudra -f` |

Env keys expected in `/opt/samudra/.env` (values never committed):
`APP_ENV`, `DB_PATH`, `STATE_DB_PATH`, `PUBLIC_BASE_URL`, `ALLOWED_ORIGINS`,
`ADMIN_SECRET_KEY`, `SYSTEMA_SANSCRITICUM_URL`, `SITE_DESCRIPTION`,
`AI_PROVIDER`, `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL`.

---

## One-command code deploy (happy path)

Use this after a merge lands on `origin/main` and the change is **app code or
Python deps** (not a multi-GB corpus reindex — that is a separate step).

```bash
# As root on 193.232.229.92
set -euo pipefail
cd /opt/samudra/repo
PREV=$(git rev-parse --short HEAD)
echo "BEFORE: $PREV  $(git log -1 --oneline)"

git fetch origin --quiet
git pull --ff-only origin main

/opt/samudra/venv/bin/pip install -r web/requirements.txt
systemctl restart samudra

# Local smoke (always available; does not depend on public DNS hairpin)
curl -fsS -o /dev/null -w "local_home=%{http_code}\n" http://127.0.0.1:8000/
systemctl is-active samudra
echo "AFTER:  $(git rev-parse --short HEAD)  $(git log -1 --oneline)"
echo "ROLLBACK_SHA=$PREV   # keep this if you need to roll back"
```

**Why `--ff-only`:** refuse a dirty/divergent checkout instead of creating a
merge commit on prod. If pull fails, stop and inspect — do not force-reset
without a human.

**Why pip every time:** cheap insurance when `web/requirements.txt` moved;
no-op when pins are unchanged.

**Not this path:** corpus reindex (`reindex.sh`), nginx/cert edits, `.env`
secret rotates, OpenRouter key swaps — see sections below and DEPLOYMENT.md.

### Agent / skill short form

Same recipe as the org standing deploy rule (`deploy-without-reask`):

```bash
cd /opt/samudra/repo && git pull --ff-only origin main \
  && /opt/samudra/venv/bin/pip install -r web/requirements.txt \
  && systemctl restart samudra
```

Then one smoke that proves the shipped surface (local `/` HTTP 200, or a
feature-specific fragment check).

---

## Smoke checks

### Always (post-restart)

```bash
systemctl is-active samudra          # expect: active
curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/
# expect: 200

journalctl -u samudra -n 40 --no-pager
```

### DB integrity (optional, heavier)

```bash
/opt/samudra/venv/bin/python /opt/samudra/repo/web/scripts/smoke_check.py \
  --db-path /opt/samudra/db/corpus.db \
  --min-sources 5
# expect: OK … sources=N lines=N …
```

### Public HTTPS

```bash
curl -fsS -o /dev/null -w "%{http_code}\n" \
  https://samudra.193.232.229.92.sslip.io/
```

**Note:** hairpin from the LXC itself to the public sslip.io name can fail
(timeout) while the app is healthy on `127.0.0.1:8000`. Prefer local smoke for
post-deploy gates; confirm public from an external client when TLS/nginx is
what changed.

### Search fragment (example)

```bash
curl -fsS "http://127.0.0.1:8000/api/search?q=dharma" | head -c 200
echo
```

---

## Code rollback

Record `PREV` **before** every deploy (the happy-path block prints it). To
undo a bad app deploy:

```bash
set -euo pipefail
# Replace with the SHA printed as ROLLBACK_SHA / BEFORE
BAD_SHA_OR_PREV=<short-or-full-sha>

cd /opt/samudra/repo
git fetch origin --quiet
git rev-parse --verify "${BAD_SHA_OR_PREV}^{commit}"

# Hard reset to the last known-good commit (prod is not a feature branch)
git checkout main
git reset --hard "$BAD_SHA_OR_PREV"

/opt/samudra/venv/bin/pip install -r web/requirements.txt
systemctl restart samudra
curl -fsS -o /dev/null -w "local_home=%{http_code}\n" http://127.0.0.1:8000/
systemctl is-active samudra
echo "NOW: $(git rev-parse --short HEAD)  $(git log -1 --oneline)"
```

**After rollback:** the next happy-path `git pull --ff-only` will re-advance to
`origin/main`. If main still contains the bad change, either leave the host
pinned until a fix merges, or cherry-pick a fix onto a temporary branch — do
**not** force-push main from the VPS.

**Unit / nginx rollback:** the on-disk unit is a copy of
`deploy/samudra.service`. To re-sync from the current repo revision:

```bash
cp /opt/samudra/repo/deploy/samudra.service /etc/systemd/system/samudra.service
systemctl daemon-reload
systemctl restart samudra
```

nginx is host-managed under `/etc/nginx/sites-enabled/samudra` (not always
identical to `deploy/samudra.nginx` placeholders). Diff before overwrite;
`nginx -t && systemctl reload nginx` after any edit.

---

## Corpus publish / rollback (separate ladder)

Code restart does **not** rebuild `corpus.db`. After corpus source changes:

```bash
CORPUS_PATH=/opt/samudra/corpus \
DB_PATH=/opt/samudra/db/corpus.db \
NEXT_DB_PATH=/opt/samudra/db/corpus.next.db \
BACKUP_DIR=/opt/samudra/db/backups \
VENV=/opt/samudra/venv \
  /opt/samudra/repo/reindex.sh
```

Corpus DB rollback (no service restart required for the next query):

```bash
ls -lt /opt/samudra/db/backups/
cp /opt/samudra/db/backups/corpus_YYYYMMDD_HHMMSS.db /opt/samudra/db/corpus.db
```

Full detail: [DEPLOYMENT.md § Ongoing corpus publish](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md#ongoing-corpus-publish)
and § Rollback a corpus publish.

---

## Env / AI key changes

```bash
# Edit only as root; never commit .env
nano /opt/samudra/.env
chmod 600 /opt/samudra/.env
chown root:samudra /opt/samudra/.env
systemctl restart samudra
```

Admin API uses **headers**, not `?key=` (refused with 400):

```bash
# ADMIN_SECRET_KEY from /opt/samudra/.env or /root/samudra-admin-key.txt
curl -fsS -X POST -H "X-Admin-Key: $ADMIN_SECRET_KEY" \
  http://127.0.0.1:8000/api/admin/vacuum
```

---

## Branded hostname + TLS (Wave P5 / H2391)

**Human DNS first.** Until an A-record for the chosen FQDN points at
`193.232.229.92`, P5 is **not done** (sslip remains the only public name).

Measured 08-08-2026: `samudra.samskrte.ru` and `samudra.samskrtam.ru` are
**NXDOMAIN**. Recommended record at reg.ru: `samudra.samskrte.ru` A →
`193.232.229.92`. Do not put Samudra on the Systema `samskrte.ru` vhost (P11).

Gate script (exit **2** while DNS is missing — never treat that as done):

```bash
python3 /opt/samudra/repo/scripts/enable_branded_hostname.py \
  --hostname samudra.samskrte.ru

# After A-record propagates (GATE GO):
python3 /opt/samudra/repo/scripts/enable_branded_hostname.py \
  --hostname samudra.samskrte.ru --apply

curl -I https://samudra.samskrte.ru/api/health
curl -I https://samudra.193.232.229.92.sslip.io/api/health
```

What `--apply` does: injects the branded name into nginx `server_name` (keeps
sslip), `nginx -t` + reload, certbot, dual HTTPS smoke.

Status: [docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md).
Optional after branded HTTPS is 200: extend `PUBLIC_BASE_URL` /
`ALLOWED_ORIGINS` in `/opt/samudra/.env`, then `systemctl restart samudra`.

---

## Offline packs — build and serve (Wave P6 / H2392)

Build once against the live `corpus.db` and the FastAPI router serves the
result at `/api/offline-packs/{base,dict}.db` — no restart needed, the router
reads the pack files fresh on every request.

```bash
# One-time per install — offline-packs/ is created by DEPLOYMENT.md with
# .gitkeep only, still owned root:samudra mode 755 (no group-write). Without
# this, build_offline_pack.py's temp-file write fails "unable to open
# database file" even though corpus.db itself is readable.
chown samudra:samudra /opt/samudra/repo/web/offline-packs
chmod 775 /opt/samudra/repo/web/offline-packs

cd /opt/samudra/repo/web
sudo -u samudra /opt/samudra/venv/bin/python scripts/build_offline_pack.py \
  --db /opt/samudra/db/corpus.db --out /opt/samudra/web/offline-packs --pack both

# Verify
curl -fsS http://127.0.0.1:8000/api/corpus-version
curl -fsS -o /dev/null -D - http://127.0.0.1:8000/api/offline-packs/base.db \
  | grep -iE 'HTTP|content-encoding|content-length|x-db-bytes'
curl -fsS -o /dev/null -D - http://127.0.0.1:8000/api/offline-packs/dict.db \
  | grep -iE 'HTTP|content-encoding|content-length|x-db-bytes'
```

`sudo -u samudra` keeps the produced `.db`/`.gz`/`.sha256` owned by the same
user the systemd unit runs as, so the next rebuild doesn't need a second
permission fix. Size gates are on the **wire** (`.gz`) size: base ≤130 MB,
dict ≤90 MB — see [`scripts/build_offline_pack.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/build_offline_pack.py)
`SIZE_LIMIT_MB`.

**Rebuild cadence:** packs are a derivative view of `corpus.db` and go stale
after every `reindex.sh` run. Not yet wired to rebuild automatically — rerun
the recipe above after a corpus publish. Full build/API detail:
[docs/H2392_OFFLINE_PACKS_PROD_STATUS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2392_OFFLINE_PACKS_PROD_STATUS.md).

---

## Health monitor + smoke cron (Wave P4 / H2390)

Script: `scripts/health_monitor.py` — hits `/api/health` and one search probe
every invocation. Designed for a 15-minute cron call; keeps state in
`/opt/samudra/logs/.health_monitor_state.json`.

### Cron entry (root crontab on `193.232.229.92`)

```
*/15 * * * * /opt/samudra/venv/bin/python /opt/samudra/repo/scripts/health_monitor.py >> /opt/samudra/logs/health_monitor.log 2>&1
```

### Log files

| File | Content |
|---|---|
| `/opt/samudra/logs/health_monitor.log` | Every check: `PASS` / `FAIL` + health and search detail |
| `/opt/samudra/logs/health_monitor_journal.log` | Recoveries and `CRITICAL` alerts (5+ consecutive failures) |
| `/opt/samudra/logs/.health_monitor_state.json` | Consecutive-failure counter (state between cron runs) |

### Alert path

After **5 consecutive failures** the script writes a `CRITICAL:` line to
`health_monitor_journal.log` and prints to stderr (visible in cron mail and
`journalctl`). The circuit-breaker threshold is `ALERT_THRESHOLD = 5` in the
script. The cron continues running — it does not silence itself; the CRITICAL
line fires on every subsequent failure until recovery is logged.

Recovery from a transient outage is logged automatically as `RECOVERY after N
failure(s)` in both files, and the counter resets to 0.

### Manual fail-inject / smoke

```bash
# Inject failure: point at a dead port, run once, check journal
SAMUDRA_BASE_URL=http://127.0.0.1:19999 \
  /opt/samudra/venv/bin/python /opt/samudra/repo/scripts/health_monitor.py
# expect: FAIL lines in stdout, no CRITICAL yet (counter=1)

# Simulate 5 consecutive failures by patching state:
echo '{"consecutive_failures":4,"last_alert_at":null}' \
  > /opt/samudra/logs/.health_monitor_state.json
SAMUDRA_BASE_URL=http://127.0.0.1:19999 \
  /opt/samudra/venv/bin/python /opt/samudra/repo/scripts/health_monitor.py
# expect: CRITICAL line in stderr AND in health_monitor_journal.log

# Restore
echo '{"consecutive_failures":0,"last_alert_at":null}' \
  > /opt/samudra/logs/.health_monitor_state.json
/opt/samudra/venv/bin/python /opt/samudra/repo/scripts/health_monitor.py
# expect: PASS + RECOVERY logged if counter was nonzero
```

### Env overrides

| Variable | Default | Purpose |
|---|---|---|
| `SAMUDRA_BASE_URL` | `http://127.0.0.1:8000` | Target URL |
| `SAMUDRA_LOG_DIR` | `/opt/samudra/logs` | Log directory |

---

## What this runbook deliberately excludes

| Topic | Where |
|---|---|
| First-time clone / venv / certbot | [DEPLOYMENT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md) |
| Offline-pack nginx gzip rules | DEPLOYMENT.md § Offline-search packs |
| Multi-GB reindex ops / rights | reindex path above; do not conflate with code pull |
| Systema Laravel on same host | `/var/www/html` — different product |
| Creating the public DNS A-record | human at reg.ru (this section + H2391) |

---

## Provenance

- Wave P2 / H2388 (Grok 4.5 `grok-4.5`): expand operator pull/pip/restart/rollback.
- Wave P4 / H2390 (Sonnet 5 `claude-sonnet-5`): health + search smoke cron and alert path; `scripts/health_monitor.py` + this OPS section.
- Wave P5 / H2391 (Grok 4.5 `grok-4.5`): DNS-gated branded hostname path; agent half only until human A-record.
- Wave P6 / H2392 (Sonnet 5 `claude-sonnet-5`): offline-pack build recipe; found + fixed `offline-packs/` ownership gap.
- Live layout probed 08-08-2026 on `193.232.229.92` (`samudra` active; local `/` → 200).
- Host-local `/opt/samudra/OPS.md` may lag the git copy; after deploy, prefer
  `/opt/samudra/repo/OPS.md` as the source of truth.

_Dr. Mārcis Gasūns_
