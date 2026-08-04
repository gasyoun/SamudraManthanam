# Rubric declension for index search — is it accounted for, does it exist?

_Created: 17-07-2026 · Last updated: 18-07-2026_

Answer to the question "**учтено ли, есть ли такой функционал?**" about the
**declension of index rubrics** (склонение рубрик указателя) — the 2024-11 work
note pasted below (Marsel's continuation of E. A. Rubanova's pipeline). Written
as a standalone record because the answer is "partly yes, partly no" and the
distinction matters for the НКРЯ export workstream. Companion to
[`RUBANOVA_NKRYA_PIPELINE_MANUAL.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md)
(the pipeline of record) and follow-on to the 17-07-2026 speedup pass
([H1204](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1204-Opus_SamudraManthanam_rubanova-nkrya-speedup_17.07.26.md)).

## TL;DR

| Layer | In the repo? |
|---|---|
| The **output** — declined rubric forms for in-text search (single-word **and** synonym-split multiword phrases) | ✅ **Yes**, as the tracked static file [`rus_index_declined.txt`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/rus_index_declined.txt) (292 base rubrics, 1 346 declined forms, 1 148 of them multiword). |
| That output is **consumed** and searched in the running text | ✅ **Yes** — it feeds the port's epithet layer ([`extract.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/extract.py) → the Aho-Corasick matcher optimized in H1204). |
| A **generator** for single-word rubrics (rule-based + pymorphy2 fallback) | ⚠️ **Only Rubanova's simpler one** — [`sans_stemmer.ipynb`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/sans_stemmer.ipynb) `decline()`. |
| The **specific 2024-11 generator** — `Index_items_declension.ipynb`, `index_lone_declined_manual.json`, `pyphrasy` phrase declension, synonym-splitting from bracket markup, the 89.6 % / 86.5 % accuracy log | ❌ **No** — none of these are in the repo (not tracked, not on disk, `pyphrasy` used nowhere). |

**So:** the *functionality's result* exists and is already wired into search (and is
what H1204 sped up). The *newer, more general generation method* described in the
note is **not** mirrored into this repo — it lives only in Marsel's local /
upstream workspace. The H1204 speedup is **downstream** of declension (it makes the
search over already-declined forms fast); it neither uses nor reproduces the
declension *generator*, so nothing there was missed.

## What exists in the repo

1. **`rus_index_declined.txt`** — the declined-rubric data, `rubric : ['form', …]`
   per line, 6 cases each. It carries exactly the synonym-split multiword phrases
   the note describes producing — e.g. `вкуситель жертв`, `сын деваки`, `три мира`,
   `тройственная вселенная` — **and** it carries the same imperfect declensions the
   note measured (`три мира → ['три мир', 'трёх мира', 'трём миру', …]`). It was
   **imported as a curated artifact on 2026-07-12** (H753, ["land curated
   diplom-rubanova artifacts", PR #40](https://github.com/gasyoun/SamudraManthanam/pull/40)),
   not generated in-repo. Format + content strongly match the note's output, so it
   is most plausibly the committed export of that 2024-11 declension work — but the
   generating notebook is absent, so this cannot be confirmed from the repo alone.
2. **`decline(rus_index)`** in [`sans_stemmer.ipynb`](https://github.com/gasyoun/SamudraManthanam/blob/main/nkrya-parallel/diplom-rubanova/sans_stemmer.ipynb)
   (Rubanova, 2020) — declines **single-word** Russian rubrics across 6 cases via
   pymorphy2, plus a **hand-coded special-case table** for ~50 multiword rubrics
   (`both` / `tcsh` / `except_last` / `last` lists). This is a curated per-phrase
   table, **not** the general synonym-splitting + `pyphrasy` method of the note.
3. **Consumption** — [`annotations.load_rus_index_declined`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/annotations.py)
   loads the declined forms and [`extract.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/extract.py)
   searches them in each verse's text via the Aho-Corasick automaton
   ([`_aho.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/_aho.py),
   H1204). So the epithet/rubric layer of the index **is** driven by these declined
   forms today.

## What is NOT in the repo (the note's specific artifacts)

- `Index_items_declension.ipynb` — the notebook the note is about. Absent (the four
  tracked notebooks are `sans_stemmer` / `deeppavlov_parsing` / `corpus_marker`; the
  `.gitignore` allow-list has no fourth). 
- `index_lone_declined_manual.json` — the manual single-word declension output. Absent.
- `pyphrasy` — the phrase-declension package. Used nowhere in the repo.
- The **synonym-splitting-from-markup** logic (`"царь (=владыка, или государь)
  Видехи (=Митхилы)"` → 6 phrases) as *code*. Only its *result* survives, baked
  into `rus_index_declined.txt`.
- The **accuracy log** (89.6 % forms / 86.5 % paradigms auto-vs-manual). Absent.

## Recommendation (for the НКРЯ workstream, not urgent)

**RESOLVED 18-07-2026 ([H1207](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1207-Sonnet_SamudraManthanam_nkrya-ru-rubric-declension-port_17.07.26.md), Sonnet 5 `claude-sonnet-5`).** Re-implemented rather
than mirrored — `Index_items_declension.ipynb` / `index_lone_declined_manual.json`
were also confirmed absent **upstream**
(`github.com/evgeniarubanova/sanskrit_stemmer`'s full tree is the same 18 flat
files already known here, no notebook, no manual gold), so the "mirror it in"
option below was not available. Instead:
[`web/corpus_builder/sanskritisms/ru_rubric_decline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/ru_rubric_decline.py)
regenerates `rus_index_declined.txt` from `rus_index.txt` — reproducible,
testable, no `pyphrasy` dependency, folded into the port's own
[`sanskritisms/`](https://github.com/gasyoun/SamudraManthanam/tree/main/web/corpus_builder/sanskritisms)
package as this doc originally recommended. Fixes the `три мира` defect quoted
below (numeral-noun agreement), the `вездесущия` defect (an ADJF/NOUN parse
tie-break), a `both`-class truncation bug that silently dropped a phrase's 3rd+
word (15+ rubrics), and 11 rubrics the old file left with **empty** form lists
(comma-list permutations and every "тот, …" relative clause). Paradigm accuracy
against a hand-built gold: **100%** (was 86.5% in the 2024-11 note). Full
before/after + test coverage: `CHANGELOG.md` `[Unreleased]` and
[`web/tests/test_ru_rubric_decline.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/tests/test_ru_rubric_decline.py).
This closes the
[pipeline-manual metadoc](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.meta.md)
backlog item #1 ("diff Marsel's update vs Evgeniya's original") for the declension
piece specifically.

Original recommendation, kept for context: the declined forms were already in
use, so search worked. But because only the *static output* was in the repo, the
declension was **not reproducible or improvable** — and the file had visible
quality holes (`три мира` above). Options considered were mirroring Marsel's
notebook + manual gold in (like the other three notebooks were), or
re-implementing the generation folded into the port's own paradigm machinery
([`paradigms.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/paradigms.py)/[`disambiguate.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/sanskritisms/disambiguate.py))
rather than kept as a pymorphy2/pyphrasy Colab side-notebook — the second path is
what shipped, since the first was never available.

## Source — the 2024-11 work note (verbatim, provenance)

> **2024-11-16 — Склонение рубрик указателя.** Цель: выделить слова
> (словосочетания) из рубрики указателя, наиболее вероятные в тексте Рамаяны, и
> просклонять их в разных падежах для поиска; добавить в файл указателей. Задачи:
> просклонять однословные рубрики; выделить из фразовых рубрик слова и
> словосочетания (синонимы одной сущности) и просклонять их.
> Прогресс: однословные рубрики просклонены в полуавтоматическом режиме (результат
> `index_lone_declined_manual.json`, код в `Index_items_declension.ipynb`; сделан
> грубый rule-based склонятель, т.к. pymorphy2 не везде идеален). Склонение
> словосочетаний сложнее: найден пакет `pyphrasy` (на pymorphy2), но работает пока
> плохо; план — разметить многословные рубрики и разбить на синонимичные фразы,
> склоняя каждую независимо.
> **UPD 2024-11-17.** Добавлена разбивка многословных рубрик (с разметкой) на
> синонимичные фразы: `"царь (=владыка, или государь) Видехи (=Митхилы)"` →
> `['царь Видехи', 'владыка Видехи', 'государь Видехи', 'царь Митхилы', 'владыка
> Митхилы', 'государь Митхилы']`.
> **UPD 2024-11-18.** Добавлен код склонения фраз (при ошибке `pyphrasy` — ручное
> пословное склонение, верно лишь в ограниченных случаях, напр. «сын Каусальи»).
> Все парадигмы проверены вручную. Лог авто-vs-ручное: **правильных форм 89.6 %,
> верных парадигм 86.5 %**. Проверенные формы можно вставлять в эксель указателя
> для поиска.

_Dr. Mārcis Gasūns_
