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
- **Resource Constraints**: Regex searches are currently full-table scans. Future optimizations should maintain substring-match semantics.

## 4. Morphological Search (`mode="morphological"`)
- **Expansion**: Uses the Sanskrit Heritage API (via `morph_service.py`) to expand a query into its stems and variants.
- **Search Logic**: Performs a UNION search of all variants.
- **Transparency**: The stems and variants used for expansion must be returned in `search_metadata`.

## 5. Result Ordering
- **Primary Sort**: Sources are sorted by their `sort_order` defined in the `sources` table.
- **Secondary Sort**: Within a source, lines are sorted by `line_num`.

## 6. Constraints & Safety
- **Limits**: Standard searches are capped at 5,000 results by default to prevent browser crashes.
- **Timeouts**: Morphological expansions have a 5-second timeout for the external API call.
