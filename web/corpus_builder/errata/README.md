# Corpus errata (H2720)

_Created: 14-08-2026 · Last updated: 14-08-2026_

Hand-edited `errata.yml` per work, same row shape as
[SanskritGrammar Knauer `errata.yml`](https://github.com/gasyoun/SanskritGrammar/blob/main/KnauerFrazy_1908/errata.yml)
(`read` / `instead` / `found_by` / `date_added` / `fixed_in`). Corpus targeting
adds `passage` or segment `id` when there is no printed page
([catalog §5](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md)).

`ERRATA.md` in each work folder is generated — do not edit it.

```
python web/corpus_builder/apply_errata.py --work bhagavati-manasa-puja-stotra --rebuild
python web/corpus_builder/build_errata.py
```

`recipes.json` is the machine form of catalog §4.5. After a JSONL patch the
rebuild is always `html-from-jsonl`. Do not re-ingest from PDF/Word (that
wipes the patch). Do not launch `cb.exe`.

Hermetic proof: `python -m pytest tests/test_apply_errata.py`.

_Dr. Mārcis Gasūns_
