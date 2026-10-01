_Created: 23-09-2026 · Last updated: 23-09-2026_

# NKRYa parallel-corpus submission — decisions (23-09-2026)

MG asked how to make [samskrtam.ru/parallel-corpus](https://samskrtam.ru/parallel-corpus/) NKRYa-friendly so it can be submitted one day. Roadmap: [ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/ROADMAP_NKRYA_PARALLEL_RUSCORPORA_2026_2027.md) — waves 0–4 already done (full triple export of 131 sources, 13-07-2026); wave 5 (outreach) open. Session: Claude Code, Opus 5.5 (`claude-opus-5-5`). Sibling record: SanskritLexicography [GRILL_NKRYA_USES_ROUND2_DECISIONS_23-09-2026.md](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/docs/GRILL_NKRYA_USES_ROUND2_DECISIONS_23-09-2026.md).

## Live findings (NKRYa API, 23-09-2026)

1. **Hindi is there, Sanskrit is not.** PARA/hin: 9 texts, 9,490 sentences, 122,486 words. PARA/san: HTTP 500 (read as "does not exist"; not a clean 404). Our export: 78,219 clean 1:1 pairs.
2. **NKRYa's real metadata fields** for parallel texts (from `/api/v1/para-lex-gramm/search-form`): `translator`, `authors_all`, `created`, `date_trans`, `lang_orig`, `sphere`, `headers_all`. The exporter (`web/corpus_builder/nkrya_export.py` ~l.220–233) emits guessed names: `author`, `year`, `lang_source`, `date_source_ce`, etc.
3. **Rights table is wrong, not the data.** [RIGHTS_TABLE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/RIGHTS_TABLE.md): no translator in 127/131 rows, slug-as-title in 47, `needs_review` on all 131. The meta files (`Index/lib/x86_64-win64/Data/*.meta.json`) carry a `credit` in 204/231 (e.g. `07_rigveda`: Т.Я. Елизаренкова, Наука, 1999).

## MG rulings (23-09-2026, verbatim where given)

| # | Question | Ruling |
|---|---|---|
| P1 | When to write to NKRYa | **«сейчас делай для соннета»** — write now; the metadata work goes to Sonnet (H5281) |
| P2 | Three asks in one letter (format, intake owner, API quota) | **«да, напиши также письмо за меня об увеличенных лимитах»** — yes, plus a separate quota letter |
| P3 | First delivery | **«витрина»** — showcase: Rigveda, Bhagavadgītā, MBh III, Rām I–III |
| P4 | Needs-review check | recommendation: agent fills from meta + 10-card spot-check sheet |
| P5 | Sanskrit script | recommendation: ask NKRYa; IAST until they answer |
| P6 | `sphere` | recommendation: agent from series + ≤10-card sheet |
| P7 | DCS morphology in the first delivery | recommendation: yes where DCS covers it (CC BY 4.0) |
| P8 | samskrtam.ru corpus-linguist page | recommendation: yes, public-domain downloads only |
| P9 | Commentaries | recommendation: excluded in v1; offered on request |
| — | Check whether our texts are already in NKRYa | **«none are, we want to submit ours to them»** |

## Artifacts

1. Letter drafts (MG sends; agent never sends): [LETTER_DRAFT_NKRYA_SANSKRIT_PARALLEL_AND_API_QUOTA_23-09-2026.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LETTER_DRAFT_NKRYA_SANSKRIT_PARALLEL_AND_API_QUOTA_23-09-2026.md) — letter 1 to Д. В. Сичинава (cc В. А. Плунгян) with the three asks; letter 2 to NKRYa API support on the quota.
2. Handoff [H5281](https://github.com/gasyoun/Uprava/blob/main/handoffs/H5281-Opus_SamudraManthanam_nkrya-parallel-showcase-metadata_23.09.26.md) (Sonnet 5 executes, 🔴3 hard): showcase package with NKRYa field names, rights-table fix, sphere + spot-check sheet, PD-only corpus-linguist page.

_Гасунс_
