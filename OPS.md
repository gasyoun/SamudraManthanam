# OPS.md — Samudra Manthanam production operator path

_Created: 08-08-2026 · Last updated: 17-08-2026_  
_(+ H2391 branded hostname live · H2398 HSTS/security headers · H2397 logs-bounded · H2396 admin-env hardening)_

**Purpose:** one copy-paste path for code deploy, smoke, and rollback on the live box.
First-time install, systemd unit, nginx, and corpus reindex live in
[DEPLOYMENT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md).
This file is the **day-2 operator** surface.

**Host (as of 08-08-2026 probe):** LXC `samskrtam150` · `root@193.232.229.92` ·
layout under `/opt/samudra/`. Public search:
`https://samudra.samskrte.ru/` (TLS via certbot; sslip remains fallback;
apex `samskrte.ru` is a different vhost and must not be edited for Samudra).

---

## Live layout (ground truth)

```
/opt/samudra/
├── .env                 # EnvironmentFile for systemd (mode 600, root:samudra; parent 755)
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
    └── backups/         # {corpus,state}_YYYYMMDD_HHMMSS.db (7-day retention)
```

| Surface | Path / command |
|---|---|
| App unit | `systemctl {status,restart,stop,start} samudra` |
| Unit file on disk | `/etc/systemd/system/samudra.service` (source: `deploy/samudra.service`) |
| uvicorn (bound) | `127.0.0.1:8000`, 2 workers, user `samudra` |
| nginx site | `/etc/nginx/sites-enabled/samudra` (`samudra.samskrte.ru` + sslip) |
| Repo | `/opt/samudra/repo` |
| Venv Python | `/opt/samudra/venv/bin/python` (3.13.x on prod) |
| Logs | `journalctl -u samudra -f` |

Env keys expected in `/opt/samudra/.env` (values never committed):
`APP_ENV`, `DB_PATH`, `STATE_DB_PATH`, `PUBLIC_BASE_URL`, `ALLOWED_ORIGINS`,
`ADMIN_SECRET_KEY`, `SYSTEMA_SANSCRITICUM_URL`, `SITE_DESCRIPTION`,
`AI_PROVIDER`, `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL`,
`AI_ENABLED`, `AI_MAX_OUTPUT_TOKENS`, `AI_MAX_COST_PER_CALL`,
`AI_COST_CURRENCY`, `AI_MODEL_PRICES`.

### Paid-AI kill switch (H2866)

`AI_ENABLED` is the one lever that stops all provider spend. It is **false**
by default and false on this box; while it is false, `/api/ai/explain` and
`/api/ai/compare-translations` answer 503 for authenticated callers and no
provider request is dispatched at all — funding the key changes nothing.

Confirm the current posture from the log, not from memory:

```bash
journalctl -u samudra --since "-5 min" | grep ai_policy
# ai_policy: paid AI DISABLED (AI_ENABLED=false) — zero provider calls possible
```

**To enable** (two steps, both required — either alone still fails closed):

```bash
# 1. price the model you actually run, per 1M tokens, from the provider's
#    current price list; nothing in the app can verify these numbers
echo 'AI_MODEL_PRICES={"currency":"USD","models":{"<model>":{"input_per_1m":0.15,"output_per_1m":0.60}}}' >> /opt/samudra/.env
# 2. flip the switch
sed -i 's/^AI_ENABLED=.*/AI_ENABLED=true/' /opt/samudra/.env
systemctl restart samudra
journalctl -u samudra --since "-2 min" | grep ai_policy   # must say ENABLED, no "misconfigured"
```

**To roll back instantly** — this is the kill switch, use it without
hesitation if spend looks wrong:

```bash
sed -i 's/^AI_ENABLED=.*/AI_ENABLED=false/' /opt/samudra/.env
systemctl restart samudra
```

Never rotate, reveal or re-fund `AI_API_KEY` as part of this procedure, and
never clear the `rate_limits` rows that hold the monthly quota — the quota is
per-user spend history, not a cache.

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

## DB backups (cron)

Scheduled daily at **03:07 UTC** via `/etc/cron.d/samudra-db-backup`.
Both `corpus.db` and `state.db` are backed up using `sqlite3 .backup`
(WAL-safe — no `-shm`/`-wal` inconsistency). Retention: 7 days; files older
than 7 days (including stale `-shm`/`-wal` sidecars) are pruned automatically.

| Item | Path |
|---|---|
| Script on host | `/usr/local/sbin/samudra-db-backup.sh` |
| Source in repo | [`scripts/db_backup.sh`](https://github.com/gasyoun/SamudraManthanam/blob/main/scripts/db_backup.sh) |
| Cron drop-in | `/etc/cron.d/samudra-db-backup` |
| Log | `/var/log/samudra-backup.log` |

### Manual backup (one-off)

```bash
/usr/local/sbin/samudra-db-backup.sh
```

### Verify / restore dry-run

```bash
ls -lt /opt/samudra/db/backups/
# Check a backup is a valid SQLite file:
sqlite3 /opt/samudra/db/backups/corpus_YYYYMMDD_HHMMSS.db ".tables"
# Or restore to a temp path and run smoke check:
cp /opt/samudra/db/backups/corpus_YYYYMMDD_HHMMSS.db /tmp/corpus_restore_test.db
/opt/samudra/venv/bin/python /opt/samudra/repo/web/scripts/smoke_check.py \
  --db-path /tmp/corpus_restore_test.db --min-sources 5
```

To roll back `corpus.db` to a backup: stop is not required (SQLite handles
concurrent readers). Copy the backup over live; restart for certainty.

```bash
cp /opt/samudra/db/backups/corpus_YYYYMMDD_HHMMSS.db /opt/samudra/db/corpus.db
systemctl restart samudra
```

---

## Admin key / env hardening (Wave P10 / H2396)

**Contract on the live box (measured 13-08-2026 after this pass):**

| Path | Mode · owner | Why |
|---|---|---|
| `/opt/samudra` | `755` `root:samudra` | **Not** `775`. Group-write on the parent lets `samudra` unlink `.env` and drop a replacement even though the file is `600`. nginx/`www-data` still needs `+x` here to follow `/opt/samudra/web`. |
| `/opt/samudra/.env` | `600` `root:samudra` | systemd `EnvironmentFile=` is read by PID 1 as root; the app user must **not** be able to read the file. |
| `/root/samudra-admin-key.txt` | `600` `root:root` | operator copy of `ADMIN_SECRET_KEY` only. |
| `/root/samudra-env-backups/` | dir `700`, files `600` | the only legal home for `.env` copies. |
| `/opt/samudra/db/state.db` | `640` `samudra:samudra` | corrections / session hashes; not world-readable. |

**Never** leave `.env.bak*` next to the live file. On 13-08-2026 three such copies
(`.env.bak-ai`, `.env.bak-before-true-openrouter`, `.env.bak-true-or-key`)
were `644 root:root` and contained `ADMIN_SECRET_KEY`. `nobody`, `www-data`
(Systema PHP on the same LXC) and `samudra` could all read them. They were
moved to `/root/samudra-env-backups/` and the live key was **rotated** the
same day.

Permission check (prints modes only, never values):

```bash
python3 /opt/samudra/repo/scripts/check_env_hardening.py
# expect: VERDICT=PASS
stat -c '%A %a %U:%G %n' /opt/samudra /opt/samudra/.env
```

Admin API uses **headers**, not `?key=` (refused with 400). Prefer
`GET /api/corrections/pending` as a smoke — `POST /api/admin/vacuum`
actually VACUUMs `state.db`.

```bash
# Extract the key in Python (do not `source` .env — values can contain quotes)
# then pass it only as a header. Never echo it.
python3 - <<'PY'
import os, urllib.request, urllib.error
from pathlib import Path

def key_from(path):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("ADMIN_SECRET_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("no ADMIN_SECRET_KEY")

key = key_from("/opt/samudra/.env")
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/corrections/pending",
    headers={"X-Admin-Key": key},
)
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print("header_ok", r.status)
except urllib.error.HTTPError as e:
    print("header_ok", e.code)
PY
```

Expect: missing header → **403**, dummy `?key=` → **400**, wrong header →
**403**, correct `X-Admin-Key` / `Authorization: Bearer` → **200**.

### Rotate `ADMIN_SECRET_KEY`

Do this after any world-readable copy, a leaked access log, a departed
operator, or a suspected compromise. The new value must never appear in
chat, tickets, or git.

```bash
# As root. Prints statuses only.
python3 - <<'PY'
import os, shutil, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path

env = Path("/opt/samudra/.env")
bak_dir = Path("/root/samudra-env-backups")
keyfile = Path("/root/samudra-admin-key.txt")
bak_dir.mkdir(mode=0o700, exist_ok=True)
ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
copy = bak_dir / f".env.pre-rotate.{ts}"
shutil.copy2(env, copy)
os.chmod(copy, 0o600)

def load(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("ADMIN_SECRET_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("no ADMIN_SECRET_KEY")

old = load(copy)
new = os.urandom(32).hex()
text = env.read_text(encoding="utf-8")
out = []
for line in text.splitlines(keepends=True):
    if line.startswith("ADMIN_SECRET_KEY="):
        nl = "\n" if line.endswith("\n") else ""
        out.append(f"ADMIN_SECRET_KEY={new}{nl}")
    else:
        out.append(line)
tmp = env.with_name(".env.rotate.tmp")
tmp.write_text("".join(out), encoding="utf-8")
os.chmod(tmp, 0o600)
shutil.chown(tmp, user="root", group="samudra")
tmp.replace(env)
os.chmod(env, 0o600)
shutil.chown(env, user="root", group="samudra")
keyfile.write_text(new + "\n", encoding="utf-8")
os.chmod(keyfile, 0o600)

os.system("systemctl restart samudra")
time.sleep(3)

def hit(headers=None):
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/corrections/pending",
        headers=headers or {},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code

print("new_header", hit({"X-Admin-Key": new}))
print("old_header", hit({"X-Admin-Key": old}))
req = urllib.request.Request("http://127.0.0.1:8000/")
with urllib.request.urlopen(req, timeout=10) as r:
    print("local_home", r.status)
PY
chmod 600 /opt/samudra/.env
chown root:samudra /opt/samudra/.env
chmod 755 /opt/samudra
```

Expect after rotate: new header **200**, old header **403**, `local_home` **200**.

AI / OpenRouter key edits use the same file and the same `chmod 600` + restart.
Do not `cp .env .env.bak` in `/opt/samudra/` — copy into
`/root/samudra-env-backups/` instead.

HSTS / extra nginx security headers are the next section (Wave P10b / H2398),
not this env-hardening recipe.

Status: [docs/H2396_ADMIN_ENV_HARDENING_STATUS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2396_ADMIN_ENV_HARDENING_STATUS.md).

---

## HSTS + nginx security headers (Wave P10b / H2398)

**Only on the HTTPS vhost, and only after HTTPS is already stable.** HSTS on
an HTTP-only or broken-TLS host pins browsers to a service they then cannot
reach — that is this handoff's fail condition.

Live public Host (14-08-2026): `https://samudra.samskrte.ru/` (H2391).
sslip fallback still serves the same vhost + HSTS.

```bash
# Gate only (exit 2 if HTTPS is down or HTTP does not 301→HTTPS):
python3 /opt/samudra/repo/scripts/enable_security_headers.py

# When GATE GO:
python3 /opt/samudra/repo/scripts/enable_security_headers.py --apply

# Handoff prove-with:
curl -sI https://samudra.193.232.229.92.sslip.io/ | grep -i strict
# expect: strict-transport-security: max-age=31536000; includeSubDomains
```

What `--apply` does: copies
[`deploy/samudra-security-headers.conf`](https://github.com/gasyoun/SamudraManthanam/blob/main/deploy/samudra-security-headers.conf)
to `/etc/nginx/snippets/`, includes it in every `listen 443` server (and in
every `location` that already has `add_header`, because nginx does not inherit
those), runs `nginx -t`, reloads. It **refuses** to touch a listen-80 server.

On-box note: `https://samudra.193.232.229.92.sslip.io` times out from the
LXC itself (no hairpin NAT). The script falls back to
`curl --resolve host:443:127.0.0.1`, which still hits the real nginx 443
listener + cert. Prove-with from a machine that can reach the public name.

Snippet also sets `X-Content-Type-Options`, `X-Frame-Options`,
`Referrer-Policy`, `Permissions-Policy`. The `always` flag is required: the
app answers HEAD `/` with 405, and `curl -sI` is HEAD.

Status: [docs/H2398_NGINX_HSTS_SECURITY_HEADERS_STATUS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2398_NGINX_HSTS_SECURITY_HEADERS_STATUS.md).

---

## Branded hostname + TLS (Wave P5 / H2391)

**Live 14-08-2026.** Public name: `https://samudra.samskrte.ru/`.
sslip remains the permanent fallback on the same vhost. Apex `samskrte.ru`
is still the Systema vhost (P11 — do not merge them).

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://samudra.samskrte.ru/api/health
curl -sS -o /dev/null -w '%{http_code}\n' https://samudra.193.232.229.92.sslip.io/api/health
# both 200
```

`--apply` injects the branded name into nginx `server_name` (keeps sslip),
issues one cert covering branded + both sslip names (`--expand`), dual GET
smoke (HEAD `/api/health` is 405; on-box hairpin uses `--resolve`).
`PUBLIC_BASE_URL` / `ALLOWED_ORIGINS` on prod now include the branded origin.

Status: [docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2391_BRANDED_HOSTNAME_TLS_STATUS.md).

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

## Health monitor + smoke systemd timer (Wave P4 / H2390)

Script: `scripts/health_monitor.py` — hits `/api/health` and one search probe
every invocation. Designed for a 15-minute periodic call; keeps state in
`/opt/samudra/logs/.health_monitor_state.json`.

**Not root crontab.** Samudra shares this box with Systema Sanscriticum,
whose `scripts/server_guards_apply.sh` treats the *entire* root crontab as a
managed file — it renders `scripts/server_guards/cron/root.crontab` and calls
`crontab "$CRON_TMP"` (full overwrite), keyed only off `AUTO_DEPLOY_SCHEDULE`.
A hand-added Samudra line in root's crontab would silently vanish the next
time that script re-runs. A systemd timer is a separate unit outside that
managed file, so it survives.

### systemd timer + service (`193.232.229.92`)

Units: [`deploy/samudra-health-monitor.service`](https://github.com/gasyoun/SamudraManthanam/blob/main/deploy/samudra-health-monitor.service),
[`deploy/samudra-health-monitor.timer`](https://github.com/gasyoun/SamudraManthanam/blob/main/deploy/samudra-health-monitor.timer).

```bash
cp /opt/samudra/repo/deploy/samudra-health-monitor.service /etc/systemd/system/
cp /opt/samudra/repo/deploy/samudra-health-monitor.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now samudra-health-monitor.timer
systemctl list-timers samudra-health-monitor.timer   # confirm next run
```

Re-sync after an edit to either unit file:

```bash
cp /opt/samudra/repo/deploy/samudra-health-monitor.service /etc/systemd/system/
cp /opt/samudra/repo/deploy/samudra-health-monitor.timer /etc/systemd/system/
systemctl daemon-reload
systemctl restart samudra-health-monitor.timer
```

### Log files

| File | Content |
|---|---|
| `/opt/samudra/logs/health_monitor.log` | Every check: `PASS` / `FAIL` + health and search detail |
| `/opt/samudra/logs/health_monitor_journal.log` | Recoveries and `CRITICAL` alerts (5+ consecutive failures) |
| `/opt/samudra/logs/.health_monitor_state.json` | Consecutive-failure counter (state between timer runs) |

### Alert path

After **5 consecutive failures** the script writes a `CRITICAL:` line to
`health_monitor_journal.log` and prints to stderr (visible via
`journalctl -u samudra-health-monitor.service`). The circuit-breaker threshold
is `ALERT_THRESHOLD = 5` in the script. The timer keeps firing every 15
minutes — it does not silence itself; the CRITICAL line fires on every
subsequent failure until recovery is logged.

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

## Performance baseline against prod (Wave P8 / H2395)

Re-run after a corpus publish or a search/reader perf-sensitive change to
catch a regression against the recorded floor:

```bash
python web/scripts/performance_baseline.py \
  --base-url https://samudra.193.232.229.92.sslip.io
```

Writes a fresh measurement table; commit the updated
[docs/PERFORMANCE_BASELINES.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PERFORMANCE_BASELINES.md)
(do not hand-edit it — re-run the script). Budgets are defined in
[docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/VERIFICATION_SAMUDRAMANTHANAM_ARCHITECTURE_INTEGRITY.md)
§ Performance budgets; an over-budget measurement is recorded as an
exception there, never silently dropped.

---

## Logs bounded — journald + app logrotate (Wave P11 / H2397)

- **journald** was already capped org-wide (Systema's shared
  `/etc/systemd/journald.conf.d/99-persistent.conf`: `SystemMaxUse=3G`,
  `SystemKeepFree=2G`, `SystemMaxFileSize=128M`, `MaxRetentionSec=180day`) —
  `journalctl --disk-usage` measured ~1.1G in use, well inside the cap. No
  samudra-specific journald change needed.
- **App logs** (`/opt/samudra/logs/health_monitor.log`,
  `/opt/samudra/logs/health_monitor_journal.log`) had **no rotation since
  install**. Added `/etc/logrotate.d/samudra`:

  ```
  /opt/samudra/logs/*.log
  {
      daily
      rotate 14
      maxsize 50M
      missingok
      notifempty
      compress
      delaycompress
      copytruncate
      su root root
      create 0644 root root
  }
  ```

  Verified with `logrotate -d /etc/logrotate.d/samudra` (clean dry-run,
  no errors). Host-local proof also logged in `/opt/samudra/OPS.md`
  (short-notes pointer file, not canonical — this section is the
  canonical record).

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
- Wave P3 / H2389 (Sonnet 5 `claude-sonnet-5`): DB backup cron (`corpus.db` + `state.db`), 7-day retention, restore dry-run PASS.
- Wave P4 / H2390 (Sonnet 5 `claude-sonnet-5`): health + search smoke monitor and alert path; `scripts/health_monitor.py` + this OPS section. Delivered as a systemd timer (`deploy/samudra-health-monitor.{service,timer}`), not root crontab — Systema's `server_guards_apply.sh` fully overwrites root's crontab on every re-run and would have silently dropped a hand-added cron line.
- Wave P5 / H2391 (Grok 4.5 `grok-4.5`): DNS-gated branded hostname path; agent half only until human A-record.
- Wave P6 / H2392 (Sonnet 5 `claude-sonnet-5`): offline-pack build recipe; found + fixed `offline-packs/` ownership gap.
- Wave P8 / H2395 (Sonnet 5 `claude-sonnet-5`): performance baseline re-run against the live public sslip URL instead of localhost; recipe above.
- Wave P11 / H2397 (Sonnet 5 `claude-sonnet-5`): confirmed journald already bounded org-wide; added `/etc/logrotate.d/samudra` for the previously-unrotated app logs; recipe above.
- Wave P10 / H2396 (Grok 4.6 `grok-4.6`): live `.env` already `600`; found three world-readable `.env.bak*` holding `ADMIN_SECRET_KEY`; moved them under `/root/samudra-env-backups/`, set parent `755`, rotated the admin key, `X-Admin-Key` 200 / old key 403. HSTS left to H2398.
- Wave P10b / H2398 (Grok 4.6 `grok-4.6`): HSTS + security headers on the live sslip HTTPS vhost after a 6-day-stable Let's Encrypt cert; gate refuses HTTP-only; snippet committed under `deploy/`.
- Live layout probed 08-08-2026 on `193.232.229.92` (`samudra` active; local `/` → 200).
- Host-local `/opt/samudra/OPS.md` may lag the git copy; after deploy, prefer
  `/opt/samudra/repo/OPS.md` as the source of truth.

_Dr. Mārcis Gasūns_
