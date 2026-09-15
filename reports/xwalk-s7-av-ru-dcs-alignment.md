# xwalk-s7 — AV Russian × DCS Atharvaveda (Śaunaka) alignment (H4743)

_Generated: 15-09-2026 by `scripts/xwalk_s7_align_av_ru_dcs.py` — deterministic, re-run to reproduce._

**Verdict: PASS** — Śaunaka control: mean hymn coverage Śaunaka=0.688 vs Paippalāda=0.028 → ŚAUNAKA CONFIRMED; confirmed hymns (cov≥0.60): 367/563; verse rows matched by content: 4031/4516

## Method

- Samudra side: `web/corpus_builder/jsonl/NN_atharvaveda.jsonl` (book = NN),
  Russian segment `#ru` + its Sanskrit segment `#sa`.
- DCS side: `dcs-conllu/files/Atharvaveda (Śaunaka)/` (518 hymns parsed).
- Join is CONTENT-based (rvlinks precedent): normalized token difflib per hymn;
  verse-level rows where ≥50 % of the verse's sa tokens map into a DCS pāda span.
- Control: Paippalāda recension scored on the same sample to rule out
  a wrong-recension assumption.

## Results

- hymns in Samudra AV: **563** across 19 book files
- hymns confirmed vs DCS Śaunaka (cov ≥ 0.60): **367**
- verse-level aligned rows: **4031** of 4516
- mean hymn coverage: Śaunaka **0.688**, Paippalāda 0.028 (sample of 15 hymns)

## Inspect first

- `reports/xwalk-s7-av-ru-dcs-alignment.tsv` — full verse table
  (`match=content` rows are the alignment; `unmatched`/`no_dcs_hymn` rows are honest residue).
- Sample rows:

- AV 1.1.1 ↔ DCS 10439 (cov 0.786): RU «Те трижды семь, что вокруг движутся, Неся все формы, — Пусть Повелител…» ↔ SA «ye triṣaptāḥ pariyanti viśvā rūpāṇi bibhrataḥ vācaspatiḥ balā teṣām ta…»
- AV 1.1.2 ↔ DCS 10439 (cov 0.667): RU «Снова приди, о Повелитель Речи, Вместе с божественной мыслью! О Повели…» ↔ SA «punar ehi vācaspate devena manasā saha / vasoḥ pate ni ramaya / mayi e…»
- AV 1.1.3 ↔ DCS 10439 (cov 0.5): RU «Вот здесь стяни, Как два конца лука — тетивой! Пусть Повелитель Речи у…» ↔ SA «iha eva abhi vi tanu ubhe ārtnī iva jyayā / vācaspatiḥ ni yacchatu / m…»
- AV 1.1.4 ↔ DCS 10439 (cov 0.615): RU «Призван Повелитель Речи. Нас пусть призовет Повелитель Речи! Да соедин…» ↔ SA «upa asmān vācaspatiḥ hvayatām / sam śrutena gamemahi / mā śrutena vi r…»
- AV 1.2.1 ↔ DCS 10440 (cov 0.636): RU «Знаем мы отца тростника, Парджанью, обильно насыщающего. Знаем хорошо …» ↔ SA «vidma śarasya pitaram parjanyam bhūri dhāyasam / vidma u su asya mātar…»
