# ARCHITECTURE — SamudraManthanam canonical dual-product platform

_Created: 30-07-2026 · Last updated: 30-07-2026_

Companion to
[PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md).

## 1. System context

```text
Canonical corpus bundle
  manifest + JSONL + hashes + provenance + schema/version
      |
      +--> web corpus.db (FTS5, rebuildable)
      +--> offline packs (rebuildable)
      +--> desktop HTML/no-tags/catalogues (rebuildable)
      +--> validation/anomaly/review reports

Browser/PWA -------------------- FastAPI ---------------- corpus.db
  reader/search/corrections        |                         read-mostly
                                   +--------------------- state.db
Desktop Lazarus client                                      mutable
  generated corpus views

Immutable bundles: versioned release/object-storage artifacts
Deployments: Docker Compose/VPS AND bare systemd/uvicorn/nginx
```

## 2. Canonical bundle

### 2.1 Authority

The canonical unit is a manifest entry plus its JSONL payload. Legacy
`Programdata/data.txt`, HTML title comments, `.no_tags` files, SQLite rows, and
offline packs are generated representations, never competing metadata
authorities.

Suggested manifest path and shape:

```text
web/corpus_builder/manifest/
  schema-v1.json
  corpus-manifest.json
```

Each source entry carries:

- `source_slug`;
- stable work/source identifiers;
- canonical JSONL object name, byte size, SHA-256, and record count;
- schema version and corpus version;
- title/language/structure/provenance metadata;
- expected segment/cardinality counts;
- generated artifact names and hashes where committed;
- anomaly and review-report references.

The top level carries bundle version, build-tool revision, creation timestamp,
source count, aggregate counts, and artifact inventory. Ordering is explicit
and deterministic.

### 2.2 Artifact channel

Large canonical payloads and generated databases are published as immutable,
checksum-pinned release/object-storage bundles. Application Git keeps schemas,
builders, representative fixtures, current manifest, checksums, and reports.
No implementation step is triggered, delayed, or rejected because of rights.

### 2.3 Publication transaction

1. Resolve an immutable bundle by version and expected checksum.
2. Validate manifest schema, file hashes, counts, canonical-ID uniqueness,
   segment/cardinality contracts, and generated-view correspondence.
3. Build the next web/desktop artifacts in a staging directory.
4. Run fixture and full-corpus gates as required.
5. Record a release report with input/output hashes.
6. Atomically activate the new web database and publish desktop outputs.
7. Retain the prior manifest/bundle pointer for rollback.

## 3. Durable identity

### 3.1 Public key

The external reference tuple is:

```text
source_slug + canonical_id + corpus_version
```

An optional content hash provides forensic confirmation but is not the logical
identity. Numeric `source_id`, `line_num`, and insertion order are internal
database implementation details.

### 3.2 Propagation

The tuple is carried by:

- search and reader models;
- JSON/CSV/HTML exports and citation URLs;
- correction proposals and annotation/audit records;
- AI/cache requests whose output may be retained;
- offline search results;
- generated desktop anchors or a deterministic desktop mapping table.

### 3.3 Compatibility

During migration, old ordinal references remain readable. A mapping table binds
the old tuple to the canonical tuple and the corpus version in which the
mapping was observed. Migration is transactional, idempotent, reversible, and
produces a zero-orphan report before any legacy column is deprecated.

## 4. Database policies

### 4.1 `corpus.db`

- Generated from the canonical bundle.
- Schema version belongs to the bundle/build contract.
- Never mutated as a long-lived migration target.
- A schema change rebuilds a candidate database and verifies it before swap.

### 4.2 `state.db`

- Mutable application state.
- Uses ordered SQL migrations with immutable checksums.
- A migration ledger records version, checksum, applied timestamp, and tool
  revision.
- Migration execution is single-writer safe, transactional where SQLite
  permits, idempotently detectable, and backed up before destructive changes.

## 5. Application boundaries

Keep existing routers and service modules. Extract only accumulated
composition-root responsibilities:

- application factory and lifespan/startup;
- database migration/bootstrap;
- security and cache headers;
- static/PWA/service-worker routes;
- robots/sitemap generation.

`web/app/main.py` remains the assembly point, not the implementation home for
these concerns. No domain/application/infrastructure rewrite is authorized.

## 6. Search and regex

Plain, FTS, morphology, source-filter, and export semantics stay under the
existing search contract. Regex remains public but executes outside the event
loop with a hard deadline that can terminate the work, not merely check elapsed
time between matches.

Default: use a timeout-capable, Unicode-capable regex implementation compatible
with the documented scholarly subset. If compatibility requires Python `re`,
run it in a killable worker process with input/result caps. The API returns a
stable timeout/error response and never strands an application worker.

## 7. Identity, corrections, and administration

- Anonymous users may submit low-trust correction proposals under rate limits
  and moderation.
- Verified magic-link/session users gain durable attribution and elevated
  contribution capabilities.
- Email text supplied in a request is contact metadata, never proof of identity.
- Admin credentials travel in an authorization header or authenticated session,
  never query parameters.
- Audit records use durable corpus identity and record actor/trust tier.

## 8. Dual deployment contract

Both profiles implement the same inputs and externally observable behavior:

- pinned application revision and corpus bundle;
- identical environment/config validation;
- state migration before serving;
- readiness only after database and bundle verification;
- health, representative search, bounded-regex, reader/static/PWA, and rollback
  checks;
- no secret-bearing URLs or logs.

Container smoke runs in normal CI. Bare systemd/nginx rehearsal runs scheduled
and pre-release against an ephemeral test host or equivalent harness. The same
contract assertions drive both.

## 9. Dual-product contract

The Lazarus desktop product remains supported. Its corpus inputs are generated
from the canonical manifest and verified through:

- deterministic `data.txt` ordering;
- HTML/no-tags count and hash reports;
- stable anchor/mapping output;
- golden search/reader samples shared with the web corpus where behavior is
  expected to match;
- compile/package smoke on the supported Windows toolchain.

H1485 remains owned by its existing claim. This architecture consumes its
reviewed interfaces but does not redesign or duplicate them.

## 10. Corpus ingestion boundary

Converters may remain format-specific. They all emit the same canonical JSONL
contract and reports. Wisdomlib and H1438 reuse their existing code and work:

- Wisdomlib Stage C finishes the current partial scrape, then validates and
  registers accepted outputs.
- H1438 begins from the existing Wave-B branch and audits raw-versus-derived
  files before merge.

Every corpus-changing PR supplies deterministic hashes/counts, structural
validation, an anomaly report, and a stratified human-review artifact.

## 11. Build-vs-reuse verdict

| Concern | Verdict |
|---|---|
| Search engine | Reuse FTS5 and current services |
| Transliteration | Reuse shared `sanskrit-util` adapter |
| Canonical conversion | Reuse current JSONL converters; add manifest emission |
| Corpus publication | Reuse atomic swap; strengthen validation inputs |
| Offline search | Reuse sqlite-wasm packs |
| Desktop | Maintain product; generate corpus views from manifest |
| NKРЯ/Somadeva | Reuse completed pipelines and data |
| Wisdomlib/Ignatiev | Integrate existing work; do not rebuild |
| Manifest/bundle contract | New gap |
| Durable identity migration | New gap |
| Hard regex isolation | New gap |
| Migration/deployment contract harness | New gap |

_Dr. Mārcis Gasūns_
