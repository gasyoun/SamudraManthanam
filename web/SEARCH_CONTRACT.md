# Samudra Manthanam — Search Contract

This document defines the expected behavior of the search engine for the Samudra Manthanam web platform. All future changes must adhere to these semantics.

## 1. Plain Search (`mode="plain"`)
The default search mode designed for scholarly inquiries.

- **Multi-token Logic**: Multiple tokens separated by spaces are treated as an **AND** operation. All tokens must appear on the same line.
- **Substring Matching**: By default, search performs **prefix matching** for each token. For example, `arjun` matches `arjuna`.
- **Whole Word**: When `whole_word=True` is set, tokens must match exactly (no prefix/suffix allowed).
- **IAST/Sanskrit Support**: Diacritics (e.g., `ā`, `ṭ`) are supported and matched exactly unless a normalization layer is explicitly active.
- **Russian Support**: Matches substrings within Russian translations.

## 2. Multi-line Search
- **Logic**: Each line in the search box is treated as a separate, independent query.
- **Operation**: The results are a **UNION (OR)** of all queries.
- **Example**: 
  ```
  arjuna
  krishna
  ```
  Returns lines containing "arjuna" OR lines containing "krishna".

## 3. Regex Search (`mode="regex"`)
- **Syntax**: Supports standard Python `re` syntax.
- **Scope**: Matches are performed against the plain-text version of the corpus lines.
- **Resource Constraints**: Regex searches have a **5-second timeout** and a **1-million row scan budget** to prevent CPU exhaustion. If the budget is exceeded, results are truncated and the `truncated` flag is set in `search_metadata`.

## 4. Morphological Search (`mode="morphological"`)
- **Expansion**: Uses the Sanskrit Heritage API (via `morph_service.py`) to expand a query into its stems and variants.
- **Search Logic**: Performs a UNION search of all variants.
- **Transparency**: The stems and variants used for expansion must be returned in `search_metadata`.

## 5. Result Ordering
- **Primary Sort**: Sources are sorted by their `sort_order` defined in the `sources` table.
- **Secondary Sort**: Within a source, lines are sorted by `line_num`.

## 6. Canonical identity (additive, H1925 Lane B)

Every result and export row carries the canonical tuple alongside the legacy
ordinals. These fields are **additive** — no existing field changed meaning or
was removed.

| Field | Where | Meaning |
|---|---|---|
| `source_slug` | each result item, JSON/CSV export row | stable filename-derived source identity (`sources.slug`) |
| `canonical_id` | each result item, JSON/CSV export row | passage id per [LINE_ID_SCHEME.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LINE_ID_SCHEME.md), e.g. `bhagavadgita-1909:1.1` |
| `corpus_version` | search response, `/api/search/context`, export `metadata` | which corpus the results were read from |

- **Durability.** `source_id` and `line_num` are re-assigned on every ingest;
  `(source_slug, canonical_id)` is not. A stored or exported citation must use
  the canonical pair — the ordinals are compatibility fields for the migration
  span, and any client that persists a reference should record the version too.
- **Nullability.** `canonical_id` / `source_slug` are `null` only on a
  pre-migration corpus DB whose lines have no canonical id yet. Clients degrade
  (fall back to the ordinals) rather than failing.
- **Corrections.** `POST /api/corrections/propose` accepts either address form:
  `(source_slug, canonical_id)` or the legacy `(source_id, line_num)`. Both are
  resolved against the live corpus before storage, and the stored row always
  carries the canonical tuple. A reference that cannot be resolved
  unambiguously is rejected with **409** — it is never bound to a nearby line.

Full census: [docs/DURABLE_REFERENCE_INVENTORY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DURABLE_REFERENCE_INVENTORY.md).

## 7. Constraints & Safety
- **Limits**: Standard searches are capped at 5,000 results by default to prevent browser crashes.
- **Timeouts**: Morphological expansions have a 5-second timeout for the external API call.
