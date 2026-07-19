# Contributing to SamudraManthanam

> Part of the [Sanskrit Lexicon](https://github.com/sanskrit-lexicon) project. Inherits the [org-wide contribution standard](https://github.com/sanskrit-lexicon/COLOGNE/blob/main/CONTRIBUTING.md).

1. Fork the repository.
2. Create a feature branch.
3. Run the relevant gates below.
4. Submit a pull request, referencing any related issue.

See [`CLAUDE.md`](CLAUDE.md) for repo-specific commands and conventions.

## Python hermetic gate

Install the application and test dependencies:

```bash
cd web
python -m pip install -r requirements.txt pytest pytest-asyncio pytest-timeout
```

Linux/macOS:

```bash
PYTHONPATH=. python -m pytest -m "not corpus" -v --tb=short
```

PowerShell:

```powershell
$env:PYTHONPATH = "."
python -m pytest -m "not corpus" -v --tb=short
```

Zero collected tests is a failure. The full corpus is deliberately excluded from
hosted pull-request CI.

## Manual full-corpus gate

The 521 MB database stays local. Before a release, point `DB_PATH` at an existing
full database and use the launcher, which enables `USE_REAL_CORPUS=1`, reports
progress, and applies a 180-second timeout to each test.

Linux/macOS, from `web/`:

```bash
DB_PATH=/absolute/path/to/corpus.db python scripts/run_corpus_tests.py
```

PowerShell, from `web\`:

```powershell
$env:DB_PATH = "C:\absolute\path\to\corpus.db"
python scripts\run_corpus_tests.py
```

## НКРЯ site gate

From `nkrya-parallel/`:

```bash
npm ci
npm audit --omit=dev --audit-level=high
npm run build
```

## Optional Docker smoke gate

Docker is not the primary production deployment path, but its runtime image must
remain buildable. The image runs as fixed UID/GID `10001`. On Linux, the writable
database bind mount must therefore be owned by that identity; corpus and offline
pack files only need to be readable.

```bash
mkdir -p corpus web/offline-packs
test -f web/corpus.db
sudo chown 10001:10001 web/corpus.db
docker build --progress=plain -t samudra-manthanam:smoke .
docker compose up -d --build
docker compose ps
docker exec samudra_manthanam_web id -u
curl --fail --silent http://127.0.0.1:8000/api/health | python -m json.tool
curl --fail --silent -X POST -H "Content-Type: application/json" \
  -d '{"query":"dharma","mode":"plain","limit":1}' \
  http://127.0.0.1:8000/api/search | python -m json.tool
```

`docker exec ... id -u` must print `10001`. The container healthcheck requires
`corpus_db.ok == true`; an absent or degraded state database does not make the
container unhealthy. Stop the smoke stack with `docker compose down`.
