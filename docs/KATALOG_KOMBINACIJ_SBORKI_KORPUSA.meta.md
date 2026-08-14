# Metadoc — KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md

_Created: 14-08-2026 · Last updated: 14-08-2026_

**Purpose.** Living catalog of *actual* corpus-build combinations (inbound × verse-key × bundle layer × footnote mode). Stops the next session inventing a third pipeline or a `ManyBooks_` prefix.

**Audience.** Agents picking a recipe; humans who need to know why Rigveda ≠ DBhP.

**Provenance.** [H2719](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2719-Grok_SamudraManthanam_corpus-build-combinations-catalog_14.08.26.md), Grok 4.6 (`grok-4.6`). Facts from CONVERTER_SPEC, H2449, PDF_INGESTION_PIPELINE, fMainForm ManyBooks1/2. Human lock 14-08-2026: no translator uses `cb.exe`; rebuilds wanted; source folder unknown.

**Ranked backlog.**

1. Fill §4.5 for every slug in `conversion_report.json` (148), not just the crown jewels.
2. Point each row at the exact driver script + one reproduce command.
3. ~~After H2720 lands, add the apply command per recipe.~~ Done 14-08-2026: §5 + [recipes.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/errata/recipes.json) (`html-from-jsonl`).
4. Derive the §4.5 table from the manifest (`--check`) so it cannot drift.

**Limitations.** Counts 66/53/15 are from CONVERTER_SPEC / TAG_CENSUS (2026-06), not re-counted this pass. Atharvaveda vs Rigveda difference is stated as “do not reuse the Rigveda recipe blindly”; a per-book tech note is still owed. Source `01/02/03` folder still missing.

**Revision history.**

| Date | What |
|---|---|
| 14-08-2026 | H2719 first catalog. |
| 14-08-2026 | H2720: §5 is the apply+rebuild command; recipes.json machine form. |

_Dr. Mārcis Gasūns_
