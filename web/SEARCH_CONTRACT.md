# Samudra Manthanam — Search Contract

_Created: 15-05-2026 · Last updated: 05-08-2026_

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

Every bound below is implemented in one place — [`app/services/regex_executor.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/app/services/regex_executor.py) — and asserted in [`tests/test_regex_bounded.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_regex_bounded.py). The constants in this section are the source-of-truth names, not copied numbers.

### 3.1 Accepted syntax

- **Superset of Python `re`.** Patterns are compiled by the [`regex`](https://pypi.org/project/regex/) package in its `re`-compatible mode, chosen for one reason: it is the only such engine with a genuine per-match `timeout=` that aborts backtracking mid-call. Everything the previous stdlib engine accepted still compiles.
- **Supported and covered by the compatibility corpus** ([`tests/fixtures/regex_compat_scholarly.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/fixtures/regex_compat_scholarly.json)): literals with IAST diacritics and Cyrillic, character classes, alternation, bounded and unbounded quantifiers, `^`/`$` anchors, `\b` word boundaries (Unicode-aware), capturing/non-capturing groups, backreferences, and lookahead/lookbehind.
- **No construct is syntactically disallowed.** A pattern is refused for *shape* (below), never for using a particular feature — including the nested quantifiers usually blacklisted as "ReDoS patterns". They are permitted because the timeout makes them harmless, and because a blacklist would reject legitimate scholarly patterns while missing novel catastrophic ones.

### 3.2 Scope, Unicode and case

- Matching runs against the **plain-text** rendering of each corpus line (`line_text`), never the HTML.
- Case-insensitive by default; `case_sensitive=true` switches to exact case. Case folding is Unicode-aware, so it applies to Cyrillic as well as ASCII.
- Diacritics are matched **literally**: `a` does not match `ā`. No normalization or transliteration layer is applied in this mode.

### 3.3 Caps

| Bound | Value | Constant |
|---|---|---|
| Pattern length | 512 characters | `MAX_PATTERN_LENGTH` |
| Patterns per request (one per input line) | 10 | `MAX_PATTERNS` |
| Query length | 1000 characters | `SearchRequest.query` |
| Rows scanned | 1,000,000 | `MAX_SCANNED_ROWS` |
| Results returned | 5000 | `limit` |

### 3.4 Deadlines

| Bound | Value | Constant |
|---|---|---|
| Per-match wall clock | 0.05 s | `PER_MATCH_TIMEOUT` |
| Whole-scan hard deadline | 2 s | `HARD_DEADLINE_SECONDS` |
| Teardown allowance after the deadline | 0.5 s | `TEARDOWN_ALLOWANCE_SECONDS` |

The per-match timeout is the load-bearing one: it interrupts a match **in progress**, which the scan-level budget cannot do. Before H1930/H1926 the only check ran *between* rows, so one pathological pattern against one line could occupy a worker indefinitely.

A scan that hits either bound returns the results it has, with `truncated: true` in `search_metadata` — never a silent short answer.

### 3.5 Stable timeout and error responses

Regex failures return the **same payload from every entry point** (`POST /api/search`, `GET /api/search/export`, `GET /api/search/stream`): `{"error": "<code>", "detail": "<short message>"}`. Neither field carries engine text, pattern echoes, offsets, or paths.

| Code | Status | Meaning |
|---|---|---|
| `invalid_regex` | 400 | The pattern does not compile. |
| `regex_too_long` | 400 | Over `MAX_PATTERN_LENGTH`. |
| `too_many_regex_patterns` | 400 | Over `MAX_PATTERNS`. |
| `regex_unavailable` | 503 | No timeout-capable engine is installed on this deployment. |

`regex_unavailable` is a deliberate refusal, not a degradation: without the `regex` package the endpoint is **closed** rather than served by unbounded `re.search` in the event loop. An unprotected endpoint that looks healthy is worse than one that reports itself unavailable.

A scan that completes within its bounds always answers 200, whatever it had to abandon; `search_metadata` then carries `scanned_rows`, `timeout`, `budget_exceeded`, `match_timeouts`, `match_errors`, `regex_timeout_engine`, `hard_deadline_s` and `truncated`.

### 3.6 Engine note — measured, and load-bearing

The `regex` package's optimizer **defuses** the textbook ReDoS shapes: `(a+)+$`, `(a*)*b`, `(x+x+)+y` and `(.*a){20}` all complete in under 4 ms at 40 characters, no timeout involved. The adversarial fixture ([`tests/fixtures/regex_adversarial_backtracking.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/fixtures/regex_adversarial_backtracking.json)) therefore uses overlapping-alternation shapes (`(a|aa)+$`, `([ab]|[ab][ab])+$`, and Unicode/Cyrillic variants), each **measured** to exhaust the per-match budget on this engine. The same cases do not finish in 120 s under stdlib `re` at length 24.

That gap is the mitigation. The engine choice is part of this contract, not an implementation detail, and a fixture of patterns that the engine happens to optimize away would look rigorous while proving nothing.

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
- **Regex**: see §3.3–3.5 — those bounds are the enforced ones.

## 7. Related contracts

Public-boundary trust (admin authentication transport, anonymous vs verified correction intake, rate limits) is specified in [IDENTITY_TRUST_CONTRACT.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/IDENTITY_TRUST_CONTRACT.md).

_Dr. Mārcis Gasūns_
