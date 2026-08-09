# H2392 / Wave P6 — offline packs build + serve on prod: status

_Created: 09-08-2026 · Last updated: 09-08-2026_

**Handoff:** [H2392](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2392-Sonnet_SamudraManthanam_prod-offline-packs-build-serve_07.08.26.md)
**Executor:** Sonnet 5 (`claude-sonnet-5`)
**Verdict 09-08-2026: DONE** — both packs built from the live prod `corpus.db`, size gates pass, `/api/offline-packs/{base,dict}.db` serve 200 with correct gzip headers.

## Acceptance (locked in the handoff)

| Criterion | Status 09-08-2026 |
|---|---|
| base/dict packs present | **yes** — `/opt/samudra/web/offline-packs/{base,dict}.db{,.gz,.sha256}` |
| `/api/offline-packs` responds | **yes** — both endpoints 200, correct `Content-Encoding`/`X-Db-Bytes` |
| Build script exit 0 | **yes** |
| Size gates pass | **yes** — base 109.5 MB / 130 MB wire limit; dict 36.8 MB / 90 MB wire limit |

## What was built (prod LXC `samskrtam150`, `193.232.229.92`)

Source: `/opt/samudra/db/corpus.db` (`corpus_version = "2026.08"`, 228 sources).

| Pack | Sources | Rows | Raw | Wire (gzip) | Limit | Gate |
|---|---|---|---|---|---|---|
| `base.db` | 228 − 2 dict = 226 | 469,192 | 283.9 MB | **109.5 MB** | 130 MB | OK |
| `dict.db` | 2 (MW + Apte) | 254,037 | 86.8 MB | **36.8 MB** | 90 MB | OK |

SHA-256 (raw `.db`, over the decoded bytes the client verifies against):
- base: `6d4536a9911b7fe6820688de8fdd4a16a6feb2399d18d80632912dcde380bbb6`
- dict: `8e3d0af50670302d06708effa9e8ddeabeff56933579caa9b84462868ff91d1d`

Both inherit `input_manifest_hash` `sha256:5e915453252c5739d3c9f59d73372b1274bb665d51ba70a963f0c21fa173a772` from `corpus.db`'s own `corpus_meta` (H1924 manifest contract — the packs are a derivative view of the same pinned input, not a re-derivation).

## API verification

```
$ curl -fsS http://127.0.0.1:8000/api/corpus-version
{"corpus_version":"2026.08","pack_sha256":{"base":"6d4536a9...","dict":"8e3d0af5..."},
 "pack_bytes":{"base":297693184,"dict":91029504}}

$ curl -fsS -o /dev/null -D - http://127.0.0.1:8000/api/offline-packs/base.db
HTTP/1.1 200 OK
x-db-bytes: 297693184
content-encoding: gzip
content-length: 114846719

$ curl -fsS -o /dev/null -D - http://127.0.0.1:8000/api/offline-packs/dict.db
HTTP/1.1 200 OK
x-db-bytes: 91029504
content-encoding: gzip
content-length: 38600721
```

Both endpoints serve the gzip artifact via `StreamingResponse` (per H2 Phase 3d — no `Range` handling), matching the shipped [`offline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/offline.py) contract. `HEAD` returns 405 by design (the router only declares `GET`) — verified via `GET` instead, which is what the offline-search client actually issues.

## Real blocker found + fixed: output directory not writable by the app user

First build attempt failed:

```
ERROR building base pack: unable to open database file
ERROR building dict pack: unable to open database file
```

`corpus.db` itself was readable by `samudra` (`stat` + a manual `sqlite3.connect(...,mode=ro)` both confirmed this — not the read side). The actual fault: `/opt/samudra/repo/web/offline-packs/` (symlinked from `/opt/samudra/web/offline-packs/`) was `root:samudra`, mode `755` — group `samudra` (the app's own group) had **no write bit**, so `build_offline_pack.py`'s temp-file-then-atomic-swap write (`out_path + ".tmp"`) couldn't create its first file. This directory was never populated by the first-time install (`DEPLOYMENT.md` creates it via `.gitkeep` only, ownership left at the clone's default `root:samudra`).

Fix applied on prod:

```bash
chown samudra:samudra /opt/samudra/repo/web/offline-packs
chmod 775 /opt/samudra/repo/web/offline-packs
```

**First-time-install gap this exposes:** [`DEPLOYMENT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/DEPLOYMENT.md) never chowns `offline-packs/` to the `samudra` user at install time, so any fresh install hits this same 405→ERROR the first time someone tries to build packs. Documented as a follow-up step in `OPS.md`'s offline-pack build recipe (added this pass) rather than editing the install doc's historical narrative.

## Build recipe (added to OPS.md this pass)

```bash
# One-time per install (if offline-packs/ was never chown'd to samudra):
chown samudra:samudra /opt/samudra/repo/web/offline-packs
chmod 775 /opt/samudra/repo/web/offline-packs

cd /opt/samudra/repo/web
sudo -u samudra /opt/samudra/venv/bin/python scripts/build_offline_pack.py \
  --db /opt/samudra/db/corpus.db --out /opt/samudra/web/offline-packs --pack both

curl -fsS http://127.0.0.1:8000/api/corpus-version
```

Runs `sudo -u samudra` so the `.db`/`.gz`/`.sha256` files land owned by the same user the systemd unit runs as (avoids a second permission fix on the next rebuild). No `systemctl restart` is needed — the router reads the pack files fresh on every request.

## Rebuild cadence

Packs are a derivative view of `corpus.db` and go stale whenever the corpus is re-indexed (`reindex.sh`). Not yet wired to run automatically after a corpus publish — flagged as a residual, not part of P6's stated acceptance (which is build-once-and-serve, not automation). A natural follow-up is appending the pack-build step to `reindex.sh` so packs and `corpus.db` never drift; left for a separate handoff since P6's own exit condition (size gates pass, API responds) is met without it.

## Provenance

- Wave P6 / H2392 (Sonnet 5 `claude-sonnet-5`, 09-08-2026): first prod offline-pack build; found + fixed the `offline-packs/` ownership gap; verified API + gzip headers.

_Dr. Mārcis Gasūns_
