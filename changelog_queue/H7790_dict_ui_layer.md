**2026-11-18 — H7790 dict UI layer: five RU dictionaries as a first-class surface + bounded mojibake repair**
  New `/slovari` dictionary layer on samudra.samskrte.ru: dict landing page
  (Фриш, Кочергина, Коссович, Кнауэр, Смирнов with live entry counts), per-dict
  pages with a varṇamālā alphabet index, structured headword entry pages
  (Devanagari/IAST/SLP1/Cyrillic, homonyms, POS tags, glosses, cross-dict
  links), headword lookup accepting Devanagari/IAST/SLP1, and reverse
  RU→Sa gloss search returning headword cards with dict badges.
  `web/corpus_builder/repair_dict_mojibake.py`: bounded token-level
  Cyrillic↔Latin homoglyph repair over the five dict JSONL files
  (124 lines repaired; census before/after committed in
  `web/corpus_builder/mojibake_report/`; 333 unrepairable instances
  flagged for a human, never silently rewritten).
