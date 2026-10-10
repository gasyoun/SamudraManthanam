# MATURITY_PARALLEL_CORPUS_FOR_NKRYA_INCLUSION_10-10-2026 — степень зрелости русско-санскритского параллельного корпуса для включения в НКРЯ

_Created: 10-10-2026 · Last updated: 10-10-2026_

Запрошено MG 10-10-2026 («сперва покажи и опиши степень зрелости») до отправки W5-писем
([черновики](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LETTER_DRAFT_NKRYA_SANSKRIT_PARALLEL_AND_API_QUOTA_23-09-2026.md)).
Все цифры — из живых артефактов репо (пробы 10-10: DOI резолвится, страница 200);
источник каждой строки указан. Оценки 0–5 в стиле эстейт-аудитов зрелости.

## Verdict

**Витрина готова к подаче сегодня; полный корпус — 4/5, и его зрелость подаче не мешает —
расписание решает неизвестность формата приёма НКРЯ.** Публичной процедуры приёма текстов у
НКРЯ нет (пополнение через продуктовый комитет, проба 23-09), поэтому «включение» — это
переговоры с владельцем параллельного модуля (Д. В. Сичинава; В. А. Плунгян сам предлагал
санскрит рядом с хинди в «Другие индоевропейские»), а не заявка на форму. Письма W5 —
ровно этот канал.

## Scorecard

| Ось | Оценка | Факт | Доказательство |
|---|:---:|---|---|
| Битекст и выравнивание | **5/5** | **95 260 экспортированных пар / 131 источник**; 78 219 чистых 1:1 стих↔проза в замороженном 148-источниковом фрейме; выравнивание по издательской разметке (без статистического алайнера — тезис A41); байт-стабильность 4 прогона; mono-RU 10 148 и untransl-SA 80 помечены, не выброшены молча; комментарии (45 464) исключены по дизайну | [FULL_CORPUS_VALIDATION.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/FULL_CORPUS_VALIDATION.md) (итоговая строка), [conversion_report.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/conversion_report.json) (574 939 записей / 148 источников) |
| Масштаб против НКРЯ PARA | **первенец** | PARA/san не существует (HTTP 500, проба 23-09); PARA/hin = 9 текстов / 9 490 предложений / 122 486 слов. Витрина 24 текста / 28 440 пар уже втрое больше хинди-модуля по текстам; полный корпус — на порядок | [DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DECISIONS_NKRYA_PARALLEL_SUBMISSION_23-09-2026.md) |
| Санскритская сторона | **4/5** | SLP1+IAST на каждом сегменте (путь A — всегда); DCS-морфология CC BY 4.0 через трёхуровневый text-keyed кроссуок (путь B): MBh-3 99,8%, Rām I–III 54–76%, итого 81,1%; путь C (vidyut) отвергнут (over-segmentation 1,44×, Jaccard ~0,30). Остаток: вердикт 51-групповой адьюдикации → A41 §6.4; CoNLL-U-эмиттер = W7 ([H6371](https://github.com/gasyoun/Uprava/blob/main/handoffs/H6371-Opus_SamudraManthanam_nkrya-w7-conllu-dcs-morph-emitter_10.10.26.md) queued) | [ANNOTATION_3PATH_COMPARISON.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/ANNOTATION_3PATH_COMPARISON.md) |
| Русская сторона | **4/5 по замыслу** | Отдаётся плоской — НКРЯ аннотирует своим пайплайном; наша добавка — санскритизм-слой корпус-wide + proper-name индексы: закрывает ровно класс слов, на котором их лемматизаторы ломаются (находка ВКР Рубановой: базовая точность лемм на санскритизмах 47%) | W3 ([H760](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H760-Sonnet_SamudraManthanam_nkrya-wave3-sanskritism-layer-corpus-package_12.07.26.md)/[H919](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H919-Sonnet_SamudraManthanam_nkrya-wave3-sanskritisms-layer_14.07.26.md)) |
| Метаданные в словаре НКРЯ | **5/5** | Экспортёр v2.0 пишет реальные поля API (`translator, authors_all, created, date_trans, lang_orig, sphere, headers_all, words`); переводчики 130/131; 24 витринные записи курируются с evidence-URL; сферы — из словаря НКРЯ («художественная» / «нехудожественная: церковно-богословская»), виза 10/10 ✅ проголосована 10-10 интерактивно | [nkrya_showcase_bib.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_showcase_bib.json), [аудит вердиктов](https://github.com/gasyoun/Uprava/blob/main/review/weekly/archive/decisions_applied_10-10-2026_nkrya-showcase-bib_spotcheck10.md) |
| Права | **4/5, финал за НКРЯ** | Per-text таблица на 131 источник (ship-all рулинг MG 08-08/H2440, переводчики документированы); PD-подмножество классифицировано одним флагом; витринные пакеты: full + public-domain-only; фолбэк = PD-транш, если юристы НКРЯ откажут | [RIGHTS_TABLE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/export/RIGHTS_TABLE.md) |
| Форматы | **4/5** | Тройной детерминированный экспорт (НКРЯ para-XML best-guess + TMX 1.4b + TSV) из одного JSONL; CI-гейты: паритет пар с conversion_report, XML well-formedness + TMX DTD, round-trip байт-идентичность, ноль пустых сторон. Риск: формат их пост-2023 платформы не опубликован — поглощён тройкой + прямым вопросом в письме №1 | [nkrya_export.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/nkrya_export.py) |
| Цитируемость / воспроизводимость | **5/5** | Zenodo dataset DOI: концепт [10.5281/zenodo.22149933](https://doi.org/10.5281/zenodo.22149933), v1.0.0 = [10.5281/zenodo.22149934](https://doi.org/10.5281/zenodo.22149934), open access, MD5-верифицирован (резолв подтверждён 10-10); release-envelope sha256 + stdlib-чекер; [CITATION.cff](https://github.com/gasyoun/SamudraManthanam/blob/main/CITATION.cff); data statement (Bender & Friedman 2018 + Gebru et al. 2021) + ARR Responsible-NLP чеклист; A41-дескриптор readiness 4/5 | H2611 / H4254 / H2403 |
| Документация / провенанс | **5/5** | Требования рецензии Архангельского (2020) закрыты: задокументированные тестируемые экспортёры вместо ipynb-ноутбуков; сайт ВКР жив ([gasyoun.github.io/SamudraManthanam](https://gasyoun.github.io/SamudraManthanam/)); публичный поиск [samskrtam.ru/parallel-corpus](https://samskrtam.ru/parallel-corpus/) (HTTP 200, 10-10); провенанс на каждый источник | Arkhangelskiy's review = engineering spec роадмапа §1 |

## Открытые остатки (ранжировано; ни один не блокирует подачу витрины)

1. **Формат приёма НКРЯ неизвестен** — главный; закрывается вопросом в письме №1 (три ask: формат, intake-owner, квота API).
2. **Adjudication51** (51 группа B↔C) → A41 §6.4 — лист [жив](https://gasyoun.github.io/vote/sheets/samudramanthanam_nkrya_adjudication51.html), parked до ответа НКРЯ (рулинг 12 от 10-10).
3. **121 post-report источников** (199 379 записей) не влиты — W8/H6372 queued (рулинг FOLD); после влива корпус записи ≈774k.
4. **Corpus-linguist downloads-страница** — черновик написан, не задеплоена (P8, PD-only).
5. **A41 freeze/venue** — paper lane; §6.4 и fold-вердикт должны лечь до заморозки цифр.

## Что от нас — что от них

От нас (готово): витринный пакет 24/28 440 с реальными полями и правами, полный оффер 131/95 260
с честной таблицей прав, DOI для цитирования, санскритизм-добавка к их русскому пайплайну.
От них: формат, решение продуктового комитета, их разметка русской стороны, платформа.
Ингестия, русская аннотация и платформенная работа — их сторона (роадмап §4 W5).

_Др. М. Гасунс_ / Session: ZCode GLM-5.3 (`account:zai-individual-coding-plan/GLM-5.3`), 10-10-2026.
