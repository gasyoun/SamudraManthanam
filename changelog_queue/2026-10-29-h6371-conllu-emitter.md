# 2026-10-29 — H6371 W7: 4th emitter — CoNLL-U from DCS path B

Added the 4th emitter to [`web/corpus_builder/nkrya_export.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py) (v0.3.0, `--conllu`): Sanskrit-side
CoNLL-U serialized from the DCS crosswalk (path B, CC BY 4.0) through the W2 three-tier
text-keyed crosswalk — UPOS + lemma + FEATS per token, sandhi modeled as multiword-token
range rows (sandhied surface = range row, desandhied words = interior rows). Data half in
new `web/corpus_builder/dcs_conllu.py`: reads the pinned public snapshot
[gasyoun/dcs-conllu](https://github.com/gasyoun/dcs-conllu) (sparse clone, no Mac-local
sqlite needed) and carries the explicit DCS→UD UPOS table (`CONJ`→`CCONJ` is the only
real map; unmapped tags pass through verbatim, counted, and trip the validator — 0
observed in the pilot). New stdlib-only validator
`web/corpus_builder/conllu_validate.py` (E1–E8 structural rules + W1–W3 tripwires) and
hermetic + corpus test suite `web/tests/test_dcs_conllu.py` (10 passed). Real pilot run:
32,655 sentences / 225,972 words / 36,246 sandhi MWTs, 0 validator errors, byte-identical
across runs; coverage reproduces W2 exactly — MBh 3 99.81%, Rām kāṇḍas 54.28–76.32%
(partial by construction), overall 81.09%. Honesty ledger: 17 damaged DCS lemmas kept
verbatim + counted, 332 DCS text↔token mismatches repaired transparently (`# dcs_text`
keeps the original), 362 ambiguous line matches recorded per sentence. Committed evidence:
[`nkrya-parallel/export/CONLLU_W7_EMISSION_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/CONLLU_W7_EMISSION_REPORT.md)
+ `conllu_coverage.json`; per-source `.sa.conllu` bulk stays gitignored (release-asset
material). Positions Classical Sanskrit for the UD ecosystem (UD_Sanskrit-Vedic is Vedic
only); official UD inclusion stays a follow-up decision after A41. Handoff:
[H6371](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6371-Opus_SamudraManthanam_nkrya-w7-conllu-dcs-morph-emitter_10.10.26.md).
