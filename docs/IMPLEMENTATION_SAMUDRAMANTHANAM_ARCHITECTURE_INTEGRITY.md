# IMPLEMENTATION — SamudraManthanam architecture-integrity Wave 1

_Created: 30-07-2026 · Last updated: 05-08-2026_

Ordered implementation companion to
[PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md).

## 0. Common preamble

Every executor:

1. fetches `origin`;
2. checks `.ai_state.md`, Uprava GTD, linked worktrees, and relevant handoffs;
3. creates a fresh worktree from current `origin/main`;
4. reads this document and the matching verification section;
5. stages only scoped files;
6. records a concise `.ai_state.md` micro-milestone;
7. commits, opens a PR, and merges only after every lane gate passes.

Do not modify H1485 files under its active claim. Do not recreate H1438 work
already present in `h1438-ignatjev-waveb`.

## Lane A — canonical manifest and immutable bundle

**Owner:** [H1924](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1924-Opus_SamudraManthanam_canonical-manifest-artifact-bundle_30.07.26.md)

**Dependencies:** none. This is the Wave-1 foundation.

**Status: ✅ shipped 05-08-2026** (A1–A5 below all landed; A6/A7 covered by the
verification suite). The contract as built is written up in
[CORPUS_BUNDLE_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CORPUS_BUNDLE_SPEC.md),
which also records what was deliberately left open — `generated_artifacts` is
declarative rather than gated (Lane D), and the manifest-less `data.txt`
publication path still exists behind a warning.

### A1. Specify schema and fixtures

Create:

- `web/corpus_builder/manifest/schema-v1.json`;
- `web/corpus_builder/manifest/corpus-manifest.fixture.json`;
- `docs/CORPUS_BUNDLE_SPEC.md`;
- representative JSONL fixtures under `web/tests/fixtures/corpus_bundle/`.

Define required source metadata, file hashes/counts, schema/bundle versions,
generated-artifact inventory, deterministic ordering, and build revision.

### A2. Build manifest tooling

Create a focused module such as:

- `web/corpus_builder/corpus_manifest.py`;
- `web/tests/test_corpus_manifest.py`.

Commands must build, validate, and diff manifests. Output is byte-deterministic
for the same inputs. Reuse current metadata extraction and JSONL parsing; do not
introduce another transliterator or source catalogue.

### A3. Make ingest consume the manifest

Modify:

- `web/ingest/ingest.py`;
- `web/ingest/validate.py`;
- `web/ingest/publish.py`;
- targeted ingest/publish tests.

The manifest supplies enumeration and canonical metadata. Legacy
`Programdata/data.txt` may be generated or used only by an explicit
compatibility adapter. Validation must open and hash the JSONL that will
actually be published.

### A4. Define immutable artifact resolution

Create a small resolver/downloader under `web/ingest/` or `web/scripts/` that:

- accepts bundle version, URL/object name, and expected SHA-256;
- downloads to a temporary/staging path;
- rejects mismatches before extraction;
- never logs credentials;
- supports a local-file transport for tests and development.

Do not bind the architecture to one cloud vendor.

### A5. Register generated views

Extend build reports for:

- `corpus.db`;
- offline packs;
- desktop HTML/no-tags/catalogue outputs.

Each report points to its input manifest hash and records output hashes/counts.
Do not require all generators to move in this lane; establish and test the
contract and register currently available outputs.

## Lane B — durable identity and zero-orphan migration

**Owner:** [H1925](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1925-Opus_SamudraManthanam_durable-reference-zero-orphan_30.07.26.md)

**Dependencies:** Lane A schema/identity fields merged.

### B1. Inventory durable references

Create a checked report or test inventory covering:

- `web/app/models.py`;
- `web/app/services/search_service.py`;
- `web/app/routers/search.py`;
- reader/citation paths;
- `web/app/state_db.py`;
- correction and AI/cache routers/services;
- offline result payloads.

No retained reference may be omitted because it is currently unused by the UI.

### B2. Propagate the canonical tuple

Modify models, SQL selects, serializers, templates, and export fields so every
result/reference can carry:

- `source_slug`;
- `canonical_id`;
- `corpus_version`.

Preserve current fields during compatibility. Update
`web/SEARCH_CONTRACT.md` when the additive public fields are final.

### B3. Add compatibility mapping and state columns

Add ordered state migrations for canonical-reference columns and a mapping
table from legacy ordinal tuples. Backfill from a pinned corpus version.
Migration must be idempotent, transactional, and reversible through a recorded
backup/down procedure or deterministic restoration step.

### B4. Migrate corrections and retained AI/cache references

Dual-read:

1. prefer canonical tuple;
2. resolve legacy mapping;
3. reject or report ambiguity rather than silently choosing a line.

Write new records with the canonical tuple and compatibility fields until the
zero-orphan gate permits deprecation.

### B5. Produce zero-orphan evidence

Add a command/report that verifies every retained reference before and after a
candidate corpus rebuild. It must compare resolved identity and content/source
fingerprints and support rollback rehearsal.

## Lane C — bounded regex and trusted public boundaries

**Owner:** [H1926](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1926-Opus_SamudraManthanam_bounded-regex-correction-trust_30.07.26.md)

**Dependencies:** none; keep public response shape compatible.

**Status: ✅ SHIPPED 05-08-2026** (Opus 5 1M, `claude-opus-5[1m]`). C1–C7 all
delivered; steps C1–C4 below are the as-built record. Contracts:
[SEARCH_CONTRACT.md §3](https://github.com/gasyoun/SamudraManthanam/blob/main/web/SEARCH_CONTRACT.md)
and
[IDENTITY_TRUST_CONTRACT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/IDENTITY_TRUST_CONTRACT.md).
Two deliberate deltas from the text below, both recorded rather than silently
absorbed: the response shape for a *refused* pattern **did** change (three
entry points that disagreed — POST 422 echoing the pattern, GET 400 — now share
one payload), and no timed compatibility path was kept for query-string admin
credentials, because the only callers were this repo's tests and the operator
runbook. Verification-token *delivery* remains out of scope and is not faked.

### C1. Measure and specify regex compatibility

Extend `web/SEARCH_CONTRACT.md` with:

- accepted syntax;
- input/result caps;
- hard deadline and stable timeout response;
- Unicode/case behavior;
- disallowed constructs, if any.

Build a compatibility fixture from current legitimate regex tests and a
catastrophic-backtracking adversarial set.

### C2. Implement a killable deadline

Refactor `web/app/services/search_service.py` behind a small regex executor
interface. Default to a timeout-capable Unicode engine. If compatible coverage
is insufficient, use a killable subprocess/process worker with strict input,
output, memory, and wall-clock bounds.

Never run unbounded Python `re.search` in the application event loop.

### C3. Secure admin authentication transport

Modify `web/app/routers/admin.py` and related configuration/tests:

- accept authorization header or verified admin session;
- reject query-string credentials;
- ensure nginx/application logs do not contain credentials;
- keep a documented, time-bounded compatibility path only if necessary.

### C4. Separate anonymous and verified correction trust

Modify identity/correction routes, state schema, and tests:

- anonymous proposals receive low-trust actor metadata and rate limits;
- verified session identity, not submitted email text, grants attribution and
  elevated actions;
- audit records carry actor/trust tier and canonical corpus identity;
- lead capture does not expose internal identifiers unnecessarily.

## Lane D — migrations, composition root, and deployment contracts

**Owner:** [H1927](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1927-Opus_SamudraManthanam_runtime-migrations-dual-deploy_30.07.26.md)

**Dependencies:** may begin independently; final smoke consumes Lane A bundle
fixture and Lane B/C public contracts where merged.

### D1. Introduce ordered checksum migrations

Create a migration package, for example:

```text
web/app/migrations/
  runner.py
  state/
    0001_....sql
  README.md
```

Move mutable-state startup alterations into ordered files. Record immutable
checksums and fail on edited applied migrations. Define `corpus.db` schema
versions as rebuild requirements, not in-place state migrations.

### D2. Extract bounded `main.py` responsibilities

Create focused modules for:

- application factory/lifespan;
- security/cache headers;
- static/PWA/service-worker routes;
- robots/sitemaps.

Keep router registration and configuration obvious in `main.py`. Preserve
route behavior byte-for-byte where feasible. Do not introduce a new framework
or repository-wide layering scheme.

### D3. Align runtime versions

Choose one supported Python production version already exercisable by project
dependencies. Test the exact production version in CI or align the image to the
tested matrix. Build and boot the image against fixture databases, then probe
health and representative search.

### D4. Build one deployment contract suite

Create a transport-neutral smoke script under `web/scripts/` that tests:

- configuration validation and migration completion;
- readiness/health;
- plain search and bounded regex;
- reader/static/PWA assets;
- bundle/corpus version exposure;
- no credential-bearing URLs;
- clean stop/rollback behavior.

Run it against Docker in ordinary CI and against an ephemeral bare
systemd/nginx profile in scheduled/pre-release automation.

### D5. Add full-corpus workflow

Create a corpus-changing path filter and full-data workflow that:

- resolves the pinned bundle including any large objects;
- rebuilds and validates the complete corpus;
- runs corpus tests and performance budgets;
- uploads only reports/checksums needed for review;
- runs on every corpus-changing PR and every release.

Replace the stale `<=200` duplicate-suffix ceiling only after a categorised
report defines the invariant and justified exceptions.

## Lane E — Wisdomlib Stage C

**Owner:** existing issue #17; do not mint a duplicate.

1. Continue from the partial scrape.
2. Verify shard completeness and deterministic enumeration.
3. Produce structural counts, anomalies, and stratified review sample.
4. Convert accepted content through existing Wisdomlib tooling.
5. Register outputs through Lane A's manifest contract.
6. Run the full corpus-changing PR gate.

## Lane F — H1438 Wave-B recovery

**Owner:** existing H1438; do not mint a duplicate.

1. Fetch and inspect `h1438-ignatjev-waveb` and its linked worktree.
2. Diff it against current `origin/main`; inventory raw and derived additions.
3. Preserve existing valid work; do not regenerate it from scratch.
4. Review any root raw-text artifact against the raw-personal-archive fence.
5. Run per-work round-trip, structural, anomaly, and stratified review checks.
6. Rebase/reconcile, register through Lane A's manifest, and merge under H1438.

## Documentation truth pass

The planning PR updates:

- `DOCUMENTATION_INDEX.md`;
- `README.md`;
- `.ai_state.md`;
- the residual PLAN/ROADMAP supersession banners;
- the H2 Wisdomlib status;
- Uprava `ROADMAP_INDEX.md` and stale GTD rows.

No completed historical specification is deleted. Status authority points to
the new PLAN and ROADMAP.

_Dr. Mārcis Gasūns_
