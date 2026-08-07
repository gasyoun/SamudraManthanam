# Durable reference inventory — every place a corpus reference is retained

_Created: 05-08-2026 · Last updated: 05-08-2026_

Lane B (B1) of
[PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/PLAN_SAMUDRAMANTHANAM_ARCHITECTURE_2026_2027.md),
delivered under
[H1925](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1925-Opus_SamudraManthanam_durable-reference-zero-orphan_30.07.26.md).
The census below is paired with
[web/tests/test_durable_reference_inventory.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_durable_reference_inventory.py),
which asserts every row — including the rows whose verdict is "carries no corpus
reference". A site cannot quietly drop out of this table without a red test.

## The canonical tuple

`(source_slug, canonical_id, corpus_version)`

| Member | Source of truth | Why it is durable |
|---|---|---|
| `source_slug` | `sources.slug` | derived from the filename, stable across re-ingest; `sources.id` is enumeration order |
| `canonical_id` | `corpus_lines.canonical_id` | minted once by the converter per [LINE_ID_SCHEME.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LINE_ID_SCHEME.md), carried through ingest, never re-derived |
| `corpus_version` | `corpus_meta.corpus_version` | with a Lane A manifest this **is** the bundle version, so it is content-addressed rather than a wall-clock stamp ([CORPUS_BUNDLE_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CORPUS_BUNDLE_SPEC.md)) |

The pair being replaced is `(source_id, line_num)`. Both are re-assigned on every
ingest: `source_id` follows enumeration order, `line_num` follows document order.
One inserted line silently re-points every stored reference below it at the wrong
verse, and nothing in the system could tell — both the old and the new value are
valid-looking integers pointing at real rows.

## The census

Implementation: [web/app/canonical_refs.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/canonical_refs.py).

| # | Site | File | Reference held | Status after H1925 |
|---|---|---|---|---|
| 1 | Search results (plain / regex / morphological) | [search_service.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/search_service.py) · [models.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/models.py) | per-hit line identity | ✅ every hit carries `source_slug` + `canonical_id`; the response carries `corpus_version`. All three modes read one SELECT, so none can drift |
| 2 | Search context window | [routers/search.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/search.py) `/api/search/context` | neighbouring lines | ✅ joins `sources`, returns `canonical_id` + `source_slug` + `corpus_version` |
| 3 | JSON export | [routers/search.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/search.py) | a saved citation set | ✅ per-row `source_slug` + `canonical_id`; version once in `metadata` |
| 4 | CSV export | [routers/search.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/search.py) | a saved citation set | ✅ two new columns, version in the `#` preamble |
| 5 | Reader / citation JSON-LD | [reader.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/reader.py) · [source_metadata.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/source_metadata.py) | `Quotation` entities crawled and cited off-site | ✅ `identifier` is the passage canonical id; the merge no longer drops it. The `?highlight=` anchor stays as the human-facing URL |
| 6 | Corrections queue | [routers/corrections.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/corrections.py) · `state.db` | **the highest-risk store** — rows outlive many rebuilds | ✅ canonical columns + `ref_status`; writes resolve before storing; unresolvable proposals are refused with 409 |
| 7 | Legacy ordinal mapping | `state.db` `legacy_ref_map` | the bridge for pre-migration rows | ✅ new table, keyed `(corpus_version, source_id, line_num)`, built by backfill from a pinned corpus |
| 8 | Offline packs | [scripts/build_offline_pack.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/build_offline_pack.py) | a payload a user keeps on disk across rebuilds | ✅ already carried `canonical_id` + `pack_sources.source_slug` (pre-existing); asserted by test so it stays that way |
| 9 | Corpus sync manifest | [routers/corpus_sync.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/routers/corpus_sync.py) | file-level, not line-level | ⚪ n/a — addresses files by name + sha256, holds no line reference |
| 10 | Retained AI responses | [services/ai_cache.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/ai_cache.py) | keyed by hash of (system prompt, user prompt, model) | ⚪ n/a — **asserted, not assumed**: a test pins the exact column set, so adding corpus coordinates here fails the build until the row joins the migration path |
| 11 | Morph cache | `state.db` `morph_cache` | keyed by query string | ⚪ n/a — no corpus coordinates |
| 12 | Users / consent | `state.db` | no corpus coordinates | ⚪ n/a |

B1's instruction — *no retained reference may be omitted because it is currently
unused by the UI* — is why rows 9–12 are present with an explicit verdict rather
than silently absent.

## Resolution order (dual-read)

Implemented once, in `resolve_against_index`, and used by the request path, the
backfill and the zero-orphan gate alike:

1. **canonical tuple** — `(source_slug, canonical_id)`; exactly one match wins;
2. **explicit legacy mapping** — `legacy_ref_map`, pinned to the version the
   reference was recorded against;
3. **legacy ordinal, same version only** — valid because no rebuild has happened;
4. otherwise **report** — `ambiguous` or `orphan`, never a binding.

The one rule the whole lane rests on: **a legacy ordinal recorded against corpus
version X is never bound in version Y without an explicit mapping.** The ordinal
would resolve — that is exactly the danger.

`assume_current_version` is the single deliberate exception, and it is a
*caller's* fact rather than a resolver guess: ordinals a live client just posted
were read off the corpus being served, so the request path passes it; a row
already sitting in `state.db` has unknown provenance, so the backfill and the
report do not.

## Migration, backfill and the gate

| Step | Command | Guarantees |
|---|---|---|
| Schema | applied automatically at state-DB init | ordered, checksum-recorded, idempotent via D1 runner (`0004`/`0005`; H2354 absorbed the H1925 B ledger — see [migrations/README.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/migrations/README.md)) |
| Backfill | `python scripts/backfill_canonical_refs.py --corpus corpus.db --state state.db --apply` | pinned to one corpus version, backs up `state.db` first, idempotent, refuses a mis-pinned corpus |
| Gate | `python scripts/zero_orphan_report.py --before before.db --candidate candidate.db --state state.db --rollback-rehearsal` | fails on orphaned / ambiguous / re-bound; rehearses rollback |

The backfill binds an unversioned pre-migration ordinal only on the operator's
`--corpus` pin, and then **checks that pin** against the text the correction
itself remembers (`old_text`). A wrong pin surfaces as `text_mismatch` and the
row stays unresolved — it is never bound to a plausible-looking wrong line.

Gate verdicts: `stable` · `content_changed` (reported, not fatal — corrected text
is the point of the project) · `identity_changed` · `orphaned` · `ambiguous` ·
`unresolved_before`. The last three fail the gate.

## Measured evidence

Fixture-level proof lives in the tests. Real-scale proof, measured 05-08-2026
against the production `corpus.db` (`corpus_version=v2026.07.15`, read-only) with
a simulated rebuild that shifts every `source_id` and `line_num`:

| Measurement | Result |
|---|---|
| Corpus lines indexed | 611,569 |
| Lines carrying `canonical_id` | 611,569 (100.0%) |
| Lines carrying `source_slug` | 611,569 (100.0%) |
| Duplicate `(slug, canonical_id)` pairs | 0 |
| Sample of retained references | 5,000 |
| Canonical-addressed refs surviving the rebuild | 5,000 / 5,000 `canonical` |
| …whose ordinals moved while identity held | 5,000 |
| Ordinal-only refs after the rebuild | 5,000 / 5,000 `orphan` (refused) |
| Ordinal-only refs silently re-bound to another line | **0** |

The last two rows are the point of the lane: without the canonical tuple every
one of those 5,000 references would have resolved — to the wrong verse.

The duplicate count deserves a note. [LINE_ID_SCHEME.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LINE_ID_SCHEME.md)
§2 recorded 41 duplicated `(source, link_id)` pairs in the June-2026 corpus; the
current corpus has zero duplicate canonical ids, i.e. the §4 letter-suffix
disambiguation is doing its job in the converter. The resolver still treats
duplicates as `ambiguous` rather than assuming they cannot occur — a converter
regression would be caught, not silently bound.

## Known limitations

- **`canonical_id` may be `NULL`** on a pre-JSONL-ingest corpus. Such a reference
  resolves on slug + ordinal within its own version and is labelled
  `legacy_direct`; the fallback identity check in the gate is the content
  fingerprint. The production corpus is at 100% coverage, so this is a
  compatibility path, not the normal one.
- **Ordinals are still stored.** They remain compatibility fields until the
  zero-orphan gate has run clean over a real rebuild cycle in production; B2
  bars new records from depending on them *alone*, not from carrying them.
- **`corpus_lines` is an FTS5 table**, so identity lookups cannot use an index.
  Single lookups are targeted queries; bulk callers build one in-memory index
  per corpus (611k lines indexed in a few seconds).
- **The gate compares two corpus DBs**, so it needs the candidate build to exist
  before it can pass judgement. It is a pre-publication gate, not a live monitor.

_Dr. Mārcis Gasūns_
