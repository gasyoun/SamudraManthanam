_Created: 25-08-2026 · Last updated: 05-09-2026_

# Stable Line-ID Scheme (`work.chapter.verse`) — Phase 0 Design

**Status:** FROZEN for Phase 1 · 2026-06-12 (all §8 decisions settled — see §8)
**Scope:** Defines the canonical passage-identifier scheme used by citations, permalinks,
exports, and the Phase 1 JSONL master format. This document is the contract; Phase 1
implements it.

---

## 1. Goals

1. **Citable.** A scholar can cite `bhagavadgita-1909:1.1` in a footnote and the
   reference resolves for the lifetime of the project (CTS-style persistent identifier).
2. **Stable across re-ingest.** Re-running ingest, reordering `data.txt`, or correcting a
   typo in a verse must never change an ID. (Ordinal `source_id` and `line_num` fail this
   today; slugs already survive — see `make_unique_slug`.)
3. **URL-routable.** The ID embeds directly in a permalink with no escaping surprises:
   `/text/bhagavadgita-1909?highlight=1.1` and later `/passage/bhagavadgita-1909:1.1`.
4. **Alignment-ready.** Phase 1 alignment groups (Sanskrit ↔ Russian) attach to canonical
   IDs, not to line numbers.
5. **Honest about structure.** Sources without canonical structure (prose articles,
   anthologies, dictionaries) get IDs that don't pretend to be verse references.

Non-goal: full CTS URN syntax (`urn:cts:sanskritLit:...`). We adopt its *semantics*
(work + hierarchical passage, immutable once published) with a lighter syntax. A CTS URN
mapping can be layered on later without renumbering.

## 2. Empirical landscape (measured on corpus.db, 2026-06-12)

148 sources, 460,669 lines. `link_id` coverage: **15 sources full, 106 partial, 27 none**;
only 21.3% of lines carry any anchor. Formats found in the wild:

| Format | Count | Example | Meaning |
|---|---|---|---|
| `N.N` | 76,259 | `1.1` | chapter.verse (citation_block id) |
| `N.N-N` | 8,321 | `1.3-6` | merged-stanza range |
| `N.N.N` | 3,506 | `6.1.4` | book.chapter.verse |
| `N` | 5,668 | `42` | verse within single-chapter work |
| `chapter_N` | 3,956 | `chapter_4` | chapter heading anchor, not a verse |
| other | 406 | `chapter_4C`, `comment_1_0`, `0` | commentary anchors, misc |

### Census findings (2026-06-12, `web/ingest/tag_census.py` → `docs/TAG_CENSUS.md`)

Two facts from the full 148-file census change assumptions made above:

1. **Verse-ID extraction is bimodal.** Of 119 files with `citation_block` divs,
   **66 carry clean `id="N.N"` anchors; 53 carry none** and depend entirely on the
   `range`-div title regex (`parse_html.py`) to recover a verse number. The 53 are not
   marginal — they are the whole Vedic+Epic core: **all 10 Rigveda, 19 Atharvaveda, 18
   Mahābhārata parvans, 4 Rāmāyaṇa kāṇḍas, Raghuvaṃśa, Gītagovinda.** The converter
   therefore cannot treat clean `id=` as the primary path; range-title parsing is
   first-class for the most-cited texts, and any fragility there silently de-anchors the
   crown jewels. (The structure-class heuristic mis-flagged exactly these 53 as
   low-confidence "prose" because it only counted clean ids — a useful canary, not a
   classification to trust.)
2. **Commentary is pervasive, not an edge case.** `comment_*` anchors number **43,739
   across 117 sources** (more than the 27,519 `N.N` verse anchors). Treating commentary
   as a footnote (as §4 currently does, mapping it only to nav anchors) under-serves a
   third of the addressable, *searchable* content. See open question §8.4.

Known defects the scheme must absorb:

- **41 duplicated `(source, link_id)` pairs** — e.g. `13_mahabharata-anushasanaparva`
  `154.34` ×2 (genuine repeated verse number in the print edition), `isha-up` `0` ×3,
  Atharvaveda `chapter_NC` commentary anchors ×7.
- **Multi-file works**: the Mahābhārata ships as ~18 files (`06_mahabharata-bhishmaparva`,
  `13_mahabharata-anushasanaparva`, …), Atharvaveda as numbered books. The *file* is the
  unit of search and display, so the work-part stays file-level (slug), not corpus-level.
- **Three structural classes** of source (next section), only one of which has native
  verse anchors.

## 3. Source classes

Every source is assigned exactly one class in its `.meta.json` (`structure` field, new):

| Class | `structure` | Examples | Native anchor |
|---|---|---|---|
| A — canonical verse text | `verse` | Bhagavadgītā, Upaniṣads, Mahābhārata parvans, Gītagovinda | `citation_block` id / range title |
| B — dictionary / lexicon | `dictionary` | dic_mw, dic_apte, kochergina, kossovich, slovar-* (13+ sources) | none (headword per line) |
| C — prose / article / commentary / anthology | `prose` | Статьи Махабхараты, Комментарии к Махабхарате, yoga-sutry (anthology), translator forewords | none or sparse |

## 4. The scheme

```
{work}:{passage}
```

- **`work`** = the existing source slug (filename-derived, already stable and unique;
  e.g. `bhagavadgita-1909`). Hyphens internal to the slug; never contains `:` or `.`.
- **`:`** separates work from passage (CTS convention; URL-safe, cannot collide with
  slug hyphens or passage dots).
- **`passage`** depends on class:

### Class A (verse) — `chapter.verse` hierarchy

- Normalized native anchor: `1.1`, `6.1.4` (up to three levels: book.chapter.verse).
- Merged stanzas keep the range as the atom: `gitagovinda:1.3-6` is one citable unit
  (that is how the translation was published). Individual members of a range are *not*
  separately addressable in v1; a resolver may map `1.4` → containing range `1.3-6`.
- Single-chapter works with bare-`N` anchors are normalized to one level: `chaurapanchashika:42`.
- Chapter headings get `chapter` IDs only for navigation (`:c.1`), never cited as verses.
  Existing `chapter_N` anchors map to `c.N`.

### Class A — commentary blocks (per §8.4 decision)

Commentary (`comment_*` anchors — 43,739 across 117 sources) is **addressable, citable
content**, not a nav anchor. Each commentary block is keyed to the verse it annotates,
with a 1-based sequence for multiple blocks on the same verse:

- `06_mahabharata-bhishmaparva:6.1.4.comm1` — first commentary block on verse 6.1.4.
- Commentary attached at chapter level (the `chapter_NC` anchors) keys to the chapter:
  `08_atharvaveda:c.10.comm1`.
- Sequence freezes at first mint (same rule as `e{n}`/`p{n}`); an inserted block appends
  a letter (`comm1b`), never renumbers later blocks.
- A commentary block whose target verse can't be determined falls back to a document-order
  paragraph ID within the chapter (`c.10.p7`), flagged for review — never silently dropped.

### Class B (dictionary) — `e{n}` entry sequence

- `dic_mw:e15482` — `e` + 1-based entry sequence number within the file, frozen at first
  mint. Headword-based IDs were considered and rejected for v1: homonyms, multi-headword
  lines, and unstable lemma normalization make them collision-prone. The headword belongs
  in metadata, not in the identifier.

### Class C (prose) — `p{n}` paragraph sequence

- `stati-makhabkharaty:p17` — `p` + 1-based paragraph sequence, frozen at first mint.
  Where chapter structure exists, two levels: `c2.p17`.

### Disambiguation of genuine duplicates (Class A)

When the print edition genuinely repeats a verse number (`154.34` ×2), the second and
subsequent occurrences get a letter suffix in document order: `154.34`, `154.34b`,
`154.34c`. Letters (not `-2`) because `-` is taken by stanza ranges. The first
occurrence keeps the bare number so the common case cites cleanly.

## 5. Stability and minting rules

1. **IDs are minted once, by the Phase 1 HTML→JSONL converter, and stored in the JSONL
   master.** Ingest *carries IDs through*; it never regenerates them. This is the single
   most important rule: today `link_id` is re-derived from HTML on every ingest, so a
   markup fix can silently renumber. After Phase 1, the JSONL is the system of record.
2. **Published IDs are immutable.** Text corrections never renumber. If a verse is
   discovered to be misnumbered, the ID keeps the (wrong) number and a `corrected_ref`
   field records the right one — same policy as csl-orig `printchange.txt`.
3. **Sequence-based IDs (`e{n}`, `p{n}`) freeze at first mint.** Inserting a missed
   paragraph later appends a letter (`p17b`), never shifts `p18+`.
4. **Deletions tombstone.** A removed line keeps its ID in the JSONL with
   `"deleted": true`; the resolver returns 410, not 404, and never reassigns.

## 6. Storage and API changes

- `corpus_lines` gains `canonical_id TEXT` (nullable until Phase 1 backfills) with a
  unique index on `(source_id, canonical_id)` — this *enforces* the duplicate policy
  at ingest time instead of trusting the converter.
- `link_id` stays as the legacy display/anchor value during transition; reader anchors
  and `?highlight=` accept both; new citations emit only canonical IDs.
- New resolver route (Phase 4): `GET /passage/{work}:{passage}` → 301 to the reader
  with highlight. Cheap to add once the column exists.
- Citation strings (Phase 4) become:
  `Бхагавадгита 1.1 (пер. А.П. Казначеевой, 1909) — Samudra Manthanam corpus v2026.06,
  bhagavadgita-1909:1.1`.

## 7. Worked examples

| Today | Canonical | Class |
|---|---|---|
| `bhagavadgita-1909` + link_id `1.1` | `bhagavadgita-1909:1.1` | A |
| `gitagovinda` + `1.3-6` | `gitagovinda:1.3-6` (atomic range) | A |
| `06_mahabharata-bhishmaparva` + `6.1.4` | `06_mahabharata-bhishmaparva:6.1.4` | A |
| `13_…anushasanaparva` + second `154.34` | `13_mahabharata-anushasanaparva:154.34b` | A |
| `08_atharvaveda` + `chapter_10C` | `08_atharvaveda:c.10.comm1` | A (commentary) |
| `06_mahabharata-bhishmaparva` comment block on 6.1.4 | `06_mahabharata-bhishmaparva:6.1.4.comm1` | A (commentary) |
| `dic_mw` line 15482 (no anchor) | `dic_mw:e15482` | B |
| `Статьи Махабхараты` ¶17 | `stati-makhabkharaty:p17` | C |
| `yoga-sutry` (anthology, undated web text) | `yoga-sutry:p{n}` — *prose*, not verse: the compilation has no canonical sūtra numbering of its own | C |

## 8. Decisions (all settled 2026-06-12 — scheme frozen for Phase 1)

1. **Mahābhārata book number duplication → KEEP AS-IS.** `06_mahabharata-bhishmaparva:6.1.4`
   keeps the book number in both slug and passage. Lossless; the passage is exactly the
   native printed anchor, and the slug prefix is a filing accident, not part of the
   citation a scholar reads. No per-file transformation.
2. **Dictionaries in v1 → MINT `e{n}` NOW.** Every dictionary line gets a sequence ID
   (`dic_mw:e15482`) in the converter; richer headword metadata is deferred to the
   lexicon workstream. Cheap now, makes dictionary hits citable immediately.
3. ~~Cyrillic-named sources.~~ **Resolved (verified 2026-06-12):** all 20+ Cyrillic
   filenames already transliterate to stable ASCII slugs
   (`Статьи Махабхараты.txt` → `stati-makhabkharaty`); no action needed.
4. **Commentary addressability → ADDRESSABLE IDs.** Each `comment_*` block gets a citable
   ID keyed to the verse (or chapter) it annotates: `6.1.4.comm1`, `c.10.comm1` (see §4
   "Class A — commentary blocks"). Commentary is a third of the anchored corpus and is
   cited by scholars; the cost is one extra passage sub-type in the converter.

## 9. Acceptance criteria (for the Phase 1 implementation)

- [ ] Every line in every source has exactly one `canonical_id`; unique per source
      (enforced by index).
- [ ] Round-trip: ingest → DB → re-ingest produces byte-identical `canonical_id` columns.
- [ ] All 41 known duplicates resolve per §4 disambiguation; zero unsuffixed collisions.
- [ ] All existing `link_id` values map deterministically to canonical IDs
      (table-driven normalization, covered by tests per format class).
- [ ] `structure` field present in all 148 `.meta.json` files (A/B/C assignment).
- [ ] All 43,739 `comment_*` blocks get addressable `…commN` IDs; blocks whose target
      verse is indeterminate fall back to `c.N.pM` and are flagged, not dropped.
- [ ] Range-title verse extraction covers all 53 range-dependent files (Rigveda,
      Atharvaveda, Mahābhārata, Rāmāyaṇa, Raghuvaṃśa, Gītagovinda) — tested per file.
- [ ] Legacy `?highlight={link_id}` URLs keep working.

_Dr. Mārcis Gasūns_
