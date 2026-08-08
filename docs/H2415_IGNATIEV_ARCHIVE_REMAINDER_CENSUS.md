# H2415 — Ignatiev archive remainder census

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Residuals (minted as real work 08-08-2026):** back-matter glossaries → [H2449 (Grok 4.5) — Ignatiev prefaces + glossary/bibliography layers](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2449-Grok_SamudraManthanam_h2415-ignatiev-backmatter-glossaries_08.08.26.md) (**done**); prose commentary apparatus → [H2450 (Grok 4.5) — non-pandoc `N. Источник:` commentary layer](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2450-Grok_SamudraManthanam_h2415-ignatiev-prose-commentary-layer_08.08.26.md) (**done** — pilot Kāma-samūha 685v / 489 comments).

**Handoff:** [H2415-Grok_SamudraManthanam_ignatiev-archive-remainder-ingest_07.08.26](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2415-Grok_SamudraManthanam_ignatiev-archive-remainder-ingest_07.08.26.md)  
**Executor:** Grok 4.5 (`grok-4.5`)  
**Gate:** every remaining work under `archive_ignatiev_2026/Переводы с санскрита` either registered in `Programdata/data.txt` **or** documented as deliberate skip; each ingested work HTML→JSONL RT ≥99% or documented residue.

## Scope of this handoff

H1438 waves A–D + H2377/H2385/H2412–14 covered the main tantra/purāṇa set. H2415 closed the residual folders that were still archive-only:

| Archive folder | Source file(s) | Disposition | Slug(s) | Ch | Verses | RT % |
|---|---|---|---|---:|---:|---:|
| Кама-самуха | `Кама-самуха.docx` | **ingested** (full translation; synthetic ch.1 after preface strip) | `kama-samuha` | 1 | 685 | 100 |
| Кадамбара-свикарана-карика | `Кадамбара-свикарана-карика.doc` | **ingested** (OLE extract; start at post-preface title) | `kadambara-svikarana-karika` | 1 | 128 | 100 |
| Махабхарата | `Махабхарата Три заключительные книги.docx` | **ingested** as **three** works (ch numbers restart per book) | `mahabharata-mausalaparva-ignatiev` | 8 | 285 | 100 |
| | | | `mahabharata-mahaprasthanikaparva-ignatiev` | 3 | 110 | 100 |
| | | | `mahabharata-svargarohanikaparva-ignatiev` | 6 | 319 | 100 |
| Прочее | `Тексты по йони-пудже.docx` | **ingested** (short liturgical miscellany) | `yoni-puja-texts` | 1 | 16 | 100 |
| Прочее | `Шри-Бхагавати-манаса-пуджа-стотра.doc` | **ingested** (stotra; OLE) | `bhagavati-manasa-puja-stotra` | 1 | 69 | 100 |

**Totals this pass:** 7 HTML sources, **1 612** RU verses, all **ru_only**, all RT **100%**. No silent empty chapters.

## Deliberate non-goals / skips (not H2415 remainder)

| Item | Reason | Residual |
|---|---|---|
| Devībhāgavata-purāṇa (12 skandha multi-file) | Separate multi-skandha pipeline (already ingested H534/H558); out of handoff scope | n/a (already done) |
| Prefaces, dictionaries, bibliographies inside remainder books | Back-matter; not verse units (cut at `КОММЕНТАРИЙ` / `СЛОВАРЬ` / `ЛИТЕРАТУРА`) | **H2449 done** — [census](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2449_IGNATIEV_BACKMATTER_LAYERS_CENSUS.md) (17 layers) |
| Prose / free commentary after translation | `N. Источник:` (Kāma) and free `[N]` text (MBH/yoni) were honest zeros until H2450/H2491 | **H2450 + H2491 done** — prose + `bracket-free`; kama 489; MBH 154+55+127; yoni 13; kadambara/bhagavati residue; [reparse doc](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2450_REMAINDER_REPARSE.md) |
| Vasilkov/Neveleva MBH 16–18 already in corpus | **Different translator.** Ignatiev triple is registered under `*-ignatiev` slugs so the two editions coexist | n/a (parallel edition already present) |

## Full `Переводы с санскрита` folder map (post-H2415)

Every top-level folder under the gitignored archive is accounted for (prior waves + this pass). DBhP remains the multi-skandha special case.

| Folder | Status (as of 08-08-2026) |
|---|---|
| Адбхута-Рамаяна | prior wave → `adbhuta-ramayana` |
| Бриханнила-тантра | Wave D selected → `brihannila-tantra` |
| Бхагавата-пурана | Wave D partial → `bhagavata-purana` |
| Гуптасадхана-тантра | Wave A / H2412–14 re-baseline → `guptasadhana-tantra` |
| Деви-махатмья | Wave C → `devimahatmya` |
| Деви-пурана | Wave D ch.22 → `devi-purana` |
| Девибхагавата-пурана | multi-skandha pipeline (not H2415) |
| Йогини-тантра | Wave B → `yogini-tantra` |
| Йони-тантра | Wave A / H2412–14 → `yoni-tantra` |
| Кадамбара-свикарана-карика | **H2415** → `kadambara-svikarana-karika` |
| Калика-пурана | Wave C → `kalika-purana` |
| Кама-самуха | **H2415** → `kama-samuha` |
| Куларнава-тантра | Wave B → `kularnava-tantra` |
| Линга-пурана | Wave D partial → `linga-purana` |
| Майя-тантра | H2377 → `maya-tantra` |
| Махабхагавата-пурана | Wave B → `mahabhagavata-purana` |
| Махабхарата | **H2415** → three `mahabharata-*-ignatiev` |
| Ниламата-пурана | Wave B fragment → `nilamata-purana` |
| Нирвана-тантра | Wave A / H2385 re-baseline → `nirvana-tantra` |
| Нируттара-тантра | Wave A / H2412–14 → `niruttara-tantra` |
| Падма-пурана | Wave D Jālandhara → `padma-purana` |
| Прочее | **H2415** → `yoni-puja-texts` + `bhagavati-manasa-puja-stotra` |
| Чиначара-тантра | pilot / Wave A → `chinachara-tantra` |
| Шактисангама-тантра | Wave D selected → `shaktisangama-tantra` |

**No remaining unregistered Sanskrit-translation folder** under the archive for H1438-class single-book ingest.

## Parser / prep hardenings (this pass)

1. **Chapter open allows trailing pandoc footnote** — `Глава четвертая[249]` (H2415). Without this, MBH book 18 dropped ch.4–5 into ch.3. Unit test: `test_chapter_open_allows_trailing_footnote_ref`.
2. **`h2415_remainder_ingest.py`** — prep (synthetic ch.1 / book split / OLE clean) → parse → ru_only align → HTML emit → RT summary. Re-runnable against the local archive root.
3. **Corpus-manifest pin** rebuilt: **209** sources / **693 990** records (`bundle_version` 2026.08).

## Reproduce

```sh
# requires local gitignored archive_ignatiev_2026/
python web/corpus_builder/h2415_remainder_ingest.py \
  --archive-root "path/to/archive_ignatiev_2026/Переводы с санскрита"

# unit tests (from web/)
cd web && PYTHONPATH=. python -m pytest tests/test_ignatiev_book_units.py -q
```

Summary machine artifact: [`web/corpus_builder/jsonl/wave_h2415_remainder_summary.json`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl/wave_h2415_remainder_summary.json).

_Dr. Mārcis Gasūns_
