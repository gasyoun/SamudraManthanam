---
name: per-source-meta-lives-in-index-lib-data
description: Per-source bibliographic meta (credit/title_ru/year/publisher) lives in Index/lib/x86_64-win64/Data/<slug>.html.meta.json, not only in web/corpus_builder sidecars
metadata:
  type: project
---

The authoritative per-source bibliographic meta is the desktop client's `Index/lib/x86_64-win64/Data/<slug>.html.meta.json` (231 files, `credit` on 204; some `.htm.meta.json`). The `web/corpus_builder/<slug>.meta.json` sidecars cover only a curated subset (54). Read through `nkrya_export.load_meta`, which merges both plus `nkrya_showcase_bib.json`.

**Why:** H821 read only the sidecars, concluded ~143 translator fills were "lost", and RIGHTS_TABLE shipped 127/131 translator-less; H5281 found them all in `Index/lib` (coverage 130/131).

**How to apply:** never declare meta missing after checking only `web/corpus_builder/`; `Index/lib/` is "generated build output" per CLAUDE.md but its `Data/*.meta.json` is the only home of this data — do not delete or regenerate it blindly.

_Created: 23-09-2026 · Гасунс_
