# HTML→JSONL Converter Spec — Phase 1, Session S2

**Status:** Draft for review · 2026-06-12
**Implements:** [LINE_ID_SCHEME.md](LINE_ID_SCHEME.md) (frozen) · grounded in
[TAG_CENSUS.md](TAG_CENSUS.md) and live `corpus.db` samples.
**Consumed by:** the Phase 1 converter `corpus_builder/html_to_canonical.py`; the
alignment work (S3) reads the records this produces.

This is the contract for turning the 148 presentational corpus files into the canonical
JSONL master. It does **not** cover alignment-group *inference* (S3) — but it specifies
the alignment *hook* the converter emits, because the Sanskrit↔Russian pairing is already
present in the source markup and is free to capture here.

---

## 1. The one structural insight

A single corpus "line" (as stored in `corpus_lines` today) is **not** an atomic passage.
For verse sources it is one `citation_block` div bundling several addressable units:

```html
<div class="citation_block" id="1.1">                      ← verse key (clean path)
  <div class="range" title="Ригведа. I. 1. 1" id="…">1</div>  ← verse key (range path)
  <div class="chapter_content">
    <div class="chapter_block iast">agnim īḷe … ॥1॥</div>      ← SANSKRIT segment
    <div class="chapter_block translation">Агни призываю …</div> ← RUSSIAN segment
  </div>
  <div class="comments">
    <div class="comment_item" id="comment_1_1">…</div>          ← COMMENTARY segment(s)
  </div>
</div>
```

The converter's job is to **explode** each block into multiple canonical records that
share a verse key, and to record that they belong together (the alignment hook). This
shape is uniform across all 119 verse files — verified: `chapter_block` only ever takes
the variants `iast` and `translation`, in both clean-id and range-id files.

---

## 2. JSONL record schema

One JSON object per line. One source file → one `.jsonl` file (named by slug).

```json
{
  "id": "01_rigveda:1.1#sa",          // canonical_id + segment suffix (see §2.1)
  "work": "01_rigveda",               // source slug
  "passage": "1.1",                   // canonical passage (no segment suffix)
  "seg": "sa",                        // segment role: sa | ru | comm1 | comm2 | …
  "group": "01_rigveda:1.1",          // alignment-group key (shared by sa+ru+comm*)
  "lang": "sa",                       // sa | ru
  "script": "iast",                   // iast | slp1 | deva | cyrillic | mixed
  "text": "agnim īḷe purohitaṃ …",    // tag-stripped plain text (search payload)
  "html": "agnim īḷe … <br>…",        // inner display HTML (no outer wrappers)
  "structure": "verse",               // verse | dictionary | prose
  "chapter": "1",                     // running chapter label (display)
  "annotates": "1.1",                 // commentary only: verse it comments on
  "seq": 5,                           // 1-based document order within the source
  "deleted": false
}
```

### 2.1 Segment suffix on `id`

The canonical passage ID (`work:passage`) addresses a *logical* verse; a verse explodes
into Sanskrit + Russian + commentary records. The record `id` disambiguates with a
`#segment` suffix:

- `01_rigveda:1.1#sa` — Sanskrit
- `01_rigveda:1.1#ru` — Russian translation
- `01_rigveda:1.1#comm1` — first commentary block on the verse

Citations to "the verse" use the bare `work:passage` (`01_rigveda:1.1`); the resolver
returns the group. Citations to a specific layer use the suffixed form. `#sa`/`#ru` are
fixed; commentary is `#comm{n}` per §8.4 of the scheme.

---

## 3. The four parse paths

Each source is routed to one path by its `structure` class (meta.json) plus a markup
sniff. The census fixes the population of each.

### Path A-clean — verse, `citation_block id="N.N"` (66 files)

1. Verse key = the `citation_block` `id` attribute (`1.1`, `6.1.4`).
2. Sanskrit segment = `div.chapter_block.iast` inner HTML → `lang=sa`, `script=iast`.
3. Russian segment = `div.chapter_block.translation` → `lang=ru`, `script=cyrillic`.
   Strip `translation_author` spans into a separate `author` field (display); strip
   inline `a.comment_sub` refs from `text` but keep them in `html`.
4. Commentary = each complete `div.comment_item` subtree → `#comm{n}`,
   `annotates` from its `comment_{ch}_{v}` id (see §4). The extractor must
   depth-count nested `<div>` elements inside a commentary item; a regex that
   stops at the first `</div>` is invalid because long commentaries can contain
   nested presentational blocks.

### Path A-range — verse, no clean id, range-title regex (53 files)

**Identical inner extraction to A-clean.** The *only* difference: the verse key is not in
an `id` attribute. Recover it from the `div.range` `title`:
`"Ригведа. I. 1. 1"` → strip the work-name + book numeral → `1.1` (the existing
`_RANGE_TITLE_VERSE` regex in `parse_html.py`). These 53 files are the Vedic+Epic core
(all Rigveda, Atharvaveda, Mahābhārata, Rāmāyaṇa, Raghuvaṃśa, Gītagovinda) — range-title
parsing is **first-class**, not a fallback, and gets its own test per file (§7).

Per scheme §8.1: where the slug already encodes the book (`06_mahabharata-bhishmaparva`),
the passage **keeps** the book level too (`6.1.4`) — no stripping.

### Path B-dict — dictionary, tab-delimited (15 files)

Two sub-formats (verified — do not assume one):

- **5-field** (`dic_mw`, `dic_apte`): `/{deva}/ ⇥ /{iast}/ ⇥ /{slp1}/ ⇥ /{cyrillic}/ ⇥ {gloss}`.
  One headword line → one record with `seg="head"`, but **all four scripts captured** as
  `forms: {deva, iast, slp1, cyrillic}` — this is the Phase 1 cross-script layer arriving
  for free. `text` = gloss + all forms (so search hits any script). ID = `{slug}:e{n}`.
- **non-tab** (`kochergina`, `kossovich`, …): single-script entry per line; `forms` holds
  only the script present (detect per §5). ID = `{slug}:e{n}`.

The converter must dispatch on tab-count per file, recorded in the census, not guess.

### Path C-prose — prose/article/commentary-anthology (.txt, plain) (67 files)

Plain-text paragraphs (`kommentarii-k-makhabkharate`: `1 Нараяна и Нара (nārāyaṇa) – …`).
One non-empty line → one record, `seg` omitted, ID = `{slug}:p{n}`. Where a leading
integer is a stable note number, prefer it (`p` + that number) over raw line ordinal;
otherwise document order. Detect inline IAST inside Russian prose for `script=mixed`.

---

## 4. Commentary handling (scheme §8.4 — addressable)

The `comment_item` id encodes its target: `comment_{chapter}_{verse}` →
`comment_1_1` annotates verse `1.1`; `comment_1_5c` annotates pada *c* of `1.5`
(keep the pada letter in `annotates`: `1.5c`); `comment_2_0` (verse 0) is **chapter-level**
commentary on chapter 2 → `annotates="c.2"`, id `…:c.2.comm1`.

- Multiple comment blocks on one verse → `#comm1`, `#comm2` in document order; sequence
  frozen at first mint.
- A `comment_item` whose id doesn't parse to a known verse → fall back to
  `c.{ch}.p{n}`, set `"needs_review": true`. **Never drop.**
- Commentary extraction is subtree-based: preserve the full inner HTML of each
  `comment_item`, including nested `<div>` content, before stripping tags for
  plain `text`.

---

## 5. Script detection & normalization

- Sanskrit display blocks are tagged `iast` in markup — trust the tag for `script`.
- Compute **SLP1** for every Sanskrit segment via `indic_transliteration` (already a
  dependency) and store as a sibling `slp1` field; the query layer expands across
  `{iast, slp1, deva}`. This is the converter's half of the Phase 1 cross-script fix.
- **Vedic accents**: `chapter_block.iast` and `comment_text` contain combining accents
  (`ṛ́ṣi-`, `rā́jantam`). Preserve them in `html`; produce an accent-stripped form in
  `text` for search (port `VEDIC_MAP` from `parse_html.py`). Store both — do not lose the
  accented form, scholars need it.

---

## 6. What the converter must NOT do

- **Not mint new IDs on re-run.** First run mints and writes JSONL; the JSONL is then the
  system of record (scheme §5.1). Re-running against unchanged HTML must produce
  byte-identical IDs. A later run that finds an existing JSONL **carries IDs forward** and
  only mints for genuinely new content.
- **Not renumber on correction.** Text fix → same ID. Sequence IDs (`e{n}`, `p{n}`,
  `comm{n}`) never shift; insertions get letter suffixes (`p17b`).
- **Not silently drop** any non-empty source line. Unparseable → emit with
  `needs_review: true` and a diagnostic, count it in the run report.

---

## 7. Validation gates (CI)

1. **Round-trip ID stability:** convert → convert again → JSONL `id` columns
   byte-identical. (Catches accidental ordinal dependence.)
2. **HTML round-trip fidelity:** render JSONL → reader HTML; diff against current reader
   output for a sample set; zero search-relevant divergence. (Roadmap Phase 1 acceptance.)
3. **Per-file range-title coverage:** each of the 53 A-range files yields a non-empty
   verse key for ≥ 99% of its `citation_block`s; the shortfall is listed, not swallowed.
4. **Commentary subtree coverage:** hermetic parser tests must prove nested
   `<div>` elements inside `comment_item` do not truncate commentary content.
5. **Uniqueness:** `(work, id)` unique; all 41 known duplicate verse numbers carry the
   letter-suffix disambiguation from scheme §4.
6. **Commentary linkage:** every `#comm{n}` record's `annotates` resolves to an existing
   verse or chapter in the same work, or is flagged `needs_review`.
7. **Golden queries:** the existing golden-query suite returns identical hits when run
   against a DB built from JSONL vs. the current HTML-ingest DB (no search regression).
8. **Count parity:** line/verse/comment counts per source match a pre-computed census
   baseline within a declared tolerance; deviations itemized.

---

## 8. Run report (every conversion emits)

A `conversion_report.json`: per source — records emitted by seg type, IDs minted vs
carried, `needs_review` count with reasons, range-title miss list, duplicate-suffix list.
This is the audit trail (Cologne `printchange.txt` discipline) and the review surface.

---

## 9. Open questions → handed to S3 (alignment) or M.G.

1. **n:m alignment beyond the 1:1 sibling case.** The `iast`/`translation` sibling pair
   gives a clean 1:1 group per verse. But range-merged stanzas (`gitagovinda:1.3-6`) pair
   one Russian block to a 4-verse Sanskrit range, and translator interpolations have no
   Sanskrit source. The converter emits the *group key*; deciding the n:m edge semantics
   is **S3's job** — this spec just guarantees the group key is present and correct.
2. **Dictionary `forms` for non-tab files.** 5-field dicts give all four scripts; the
   non-tab dicts (`kochergina`, `kossovich`) give one. Is single-script `forms` enough for
   v1 cross-script dictionary search, or does S3/lexicon need transliteration backfill?
   **Recommendation: single-script now, backfill in the lexicon workstream.**
3. **`structure` class assignment.** The census heuristic is low-confidence on the 53
   range-dependent files (it mis-reads them as prose). The `structure` field in meta.json
   must be set authoritatively before conversion — propose: derive `verse` for any file
   with `citation_block` > 0, overriding the heuristic. Confirm.

## 10. Acceptance criteria

- [ ] All 148 sources convert; every non-empty source line maps to ≥ 1 JSONL record.
- [ ] All seven validation gates (§7) green in CI.
- [ ] `corpus.db` build switched to read JSONL; golden queries identical pre/post.
- [ ] Sanskrit, Russian, and each commentary block independently addressable and
      grouped; alignment group key present on every verse record.
- [ ] SLP1 computed for every Sanskrit segment; accented + stripped forms both stored.
- [ ] Conversion report produced and committed per corpus version.
