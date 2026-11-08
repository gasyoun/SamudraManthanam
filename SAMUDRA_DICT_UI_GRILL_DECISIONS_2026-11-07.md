# Samudra dict UI — grill decisions (MG × GLM, 07-11-2026)

_Created: 07-11-2026 · Last updated: 07-11-2026_

Decisions record for the question «do we have a working Sanskrit–Russian
dictionary (at least Frish) visible on samskrtam.ru?» — answered by live
probes the same day, then a two-round interactive grill with MG. This
document is the durable artifact; the two minted handoffs carry the
executable contracts.

## 1. Live state probed 07-11-2026 (all verified same pass)

- Working dictionary search **with Frish is LIVE** at
  [samudra.samskrte.ru](https://samudra.samskrte.ru/) («Пахтанье океана»,
  corpus `2026.08`, 235 sources, `/api/health` ok).
- Frish-scoped search works: [/s/frish/deva](https://samudra.samskrte.ru/s/frish/deva)
  → 20 hits; reverse Russian lookup works: [/s/frish/бог](https://samudra.samskrte.ru/s/frish/бог)
  → 141 hits (full-text over Cyrillic glosses).
- BUT: [samskrtam.ru](https://samskrtam.ru/) links it **nowhere** —
  [/c/slovari/](https://samskrtam.ru/c/slovari/) lists printed books only
  (incl. [Frish tom 2](https://samskrtam.ru/p/frish-tom2)); the
  «Словари санскрита» page ([/slovari-sanskrita/](https://samskrtam.ru/slovari-sanskrita/))
  has no online-dictionary link. [samskrte.ru](https://samskrte.ru/) (courses)
  also links nothing. Cologne's homepage does not surface Frish.
- Data (all in
  [web/corpus_builder/jsonl/](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/jsonl)):
  kochergina 29 180 · kossovich 13 488 · frish 8 156 · slovar-smirnova
  3 641 · knauer 3 271 ≈ 57.7k records. Rights clean: koch/smirnov/fri
  approved-modern
  ([REUSE_MAP.md](https://github.com/gasyoun/SanskritLexicography/blob/main/RussianTranslation/REUSE_MAP.md)),
  kna/kow public domain. Frish entries are 100% Cyrillic-glossed
  (Devanagari / IAST / SLP1 / Cyrillic translit / gloss).
- Known defect class: Cyrillic↔Latin mojibake in Frish headwords/glosses
  (ргаdA, араnI…), documented in
  [SanskritLexicography/.ai_state.md](https://github.com/gasyoun/SanskritLexicography/blob/main/.ai_state.md),
  unfixed in the serving data.

## 2. MG verdicts (grill rounds 1–2, AskUserQuestion 07-11-2026)

| # | Decision | Verdict |
|---|---|---|
| Q1 | Surface | Links samskrtam.ru → samudra.samskrte.ru (no new infra, no dict.samskrtam.ru) |
| Q2 | Dict UX scope | **Full dictionary UI** (beyond the minimum proposed) |
| Q3 | Frish mojibake | Bounded repair pass **now**, before any SEO push |
| Q4 | Cologne surfacing | **Out of scope** — own surfaces only |
| R1 | Coverage | **All 5 dictionaries**, Frish verified end-to-end first |
| R2 | Executors | Lane A (dict UI + repair) = **GLM**; Lane B (links) = **DeepSeek-flash** |
| R3 | Sequencing | Lane B lands immediately, Lane A follows |

## 3. The two lanes (contracts ride in the minted handoffs)

- **Lane A — SamudraManthanam dict layer (GLM, hard):** first-class dictionary
  layer on samudra.samskrte.ru for all five RU dictionaries — dict landing
  page, per-dict structured dictionary entries (headword, homonyms, POS,
  glosses) parsed from the corpus passages, per-dict alphabet index,
  headword lookup accepting Devanagari/IAST/SLP1 input, reverse RU→Sa gloss
  search with dict badges; Frish verified first end-to-end; mojibake census +
  bounded repair of the dict jsonl files in the same lane; corpus_db regen +
  prod deploy. Cologne untouched (Q4). dict.samskrtam.ru not built (Q1).
- **Lane B — samskrtam.ru visibility (DeepSeek-flash, ~30 min):** menu link
  «Онлайн-словарь» → [samudra.samskrte.ru](https://samudra.samskrte.ru/) plus
  body links on «Словари санскрита» and /c/slovari/; if no WP admin access
  from the estate, the executor delivers paste-ready steps for MG instead of
  blocking; verified by live HTML probe after landing.

## 4. Non-decisions kept open deliberately

- Reverse-index curation stays automatic-from-glosses with provenance badges
  (no human sense-curation — that is the Apresyan-portrait lane, separate).
- Cologne surfacing of `fri` stays parked with MG's Q4 verdict; revisit only
  if MG re-opens it.

_Dr. Mārcis Gasūns_
