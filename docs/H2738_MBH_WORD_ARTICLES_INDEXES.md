# H2738 — MBH Smirnov articles and indexes from Anatoly Drive

_Created: 14-08-2026 · Last updated: 14-08-2026_

**Handoff:** [H2738-Grok_SamudraManthanam_mbh-word-articles-indexes_14.08.26](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2738-Grok_SamudraManthanam_mbh-word-articles-indexes_14.08.26.md)
**Executor:** Grok 4.6 (`grok-4.6`)
**Shelf map:** [ANATOLIY_GOOGLE_DRIVE_CORPUS_SHELVES](https://github.com/gasyoun/Uprava/blob/main/docs/ANATOLIY_GOOGLE_DRIVE_CORPUS_SHELVES_14-08-2026.md)

## Source

Anatoliy Artemenko shared tree, folder **Для Пахтания** (`1m1tDLvWJu4DrK9-q0DVbAfnNaLiiLC8Y`). Live warehouse is **Корпус (подготовка)**; this shelf is the old Word dump, not the verse ingest.

| File | Drive id | Bytes | Used as |
|---|---|---:|---|
| Все статьи Махабхараты (для чтения).docx | `1nC44pql_elrD63Ip2BTKpFwLi03dPHRZ` | 2 393 843 | **Articles.** Authoritative (2024-10-04). |
| Все статьи Махабхараты.docx | `1nAXSTdYlG37v1nAFuBCFRPWhgKoKkUta` | 805 140 | Older twin (2023-10-30); leftover `<H1>` tags. Not ingested. |
| Комментарии Махабхараты.docx | `1nAOongGWnXlz1ABbV5Lf08DV8_0nzLDA` | 1 976 242 | **Not ingested.** Already verse-attached `comment_item` in the 18 parva HTML files. Book 13 (Anuśāsana) has 0 comments in HTML and no section in this dump. |
| Махабхарата -все указатели.doc | `1nCImawGZ6mjVinlDUx2C9DJsrFIwWkgV` | 2 075 136 | **Indexes** (2022-10-26). |

Raw bytes stay gitignored under `archive_anatoly_mbh_word/` (Drive is the backup). Re-extract: `gdown https://drive.google.com/uc?id=<id>`.

## Emitted layers

Parent work `mahabharata`. Same Nauka / AN SSSR volume family as the already-public parva HTML. Rights uncertainty is not a stop.

| Slug | Kind | Records | RT | Desktop file |
|---|---|---:|---:|---|
| `mahabharata-stati` | prose (25 articles) | 2430 | 99.96% (28 Latin-accent soft + 1 same class) | `.html` |
| `mahabharata-ukazatel-imen` | dictionary | 9980 | 100% | `.txt` |
| `mahabharata-ukazatel-geo` | dictionary | 3449 | 100% | `.txt` |
| `mahabharata-ukazatel-predmet` | dictionary | 4122 | 100% | `.txt` |
| `mahabharata-ukazatel-flora` | dictionary | 103 | 100% | `.txt` |

Index entries carry a volume tag (`[1]`, `[10-11]`, `[15-18]`). Print page numbers stay as in the book; they are not verse keys.

## Articles (25)

1. Послесловие — А. П. Баранников
1. Краткие сведения о Махабхарате — В. И. Кальянов
2. Послесловие — В. И. Кальянов
3. Предисловие — Я. В. Васильков, С. Л. Невелева
4. Послесловие — В. И. Кальянов
4. Некоторые военные вопросы в древнеиндийском эпосе — В. И. Кальянов
5. Послесловие — В. И. Кальянов
5. Некоторые вопросы внешнеполитических воззрений — В. И. Кальянов
6. От переводчика — В. Г. Эрман
6. Книга о Бхишме как сюжетное ядро — С. Д. Серебряный
6. Многозначное откровение «Бхагавадгиты» — В. Г. Эрман
7. Послесловие — В. И. Кальянов
7. О воинском кодексе чести — В. И. Кальянов
8. Предисловие — Я. В. Васильков, С. Л. Невелева
9. Послесловие — В. И. Кальянов
10–11. От переводчиков — Я. В. Васильков, С. Л. Невелева
10–11. О содержании «Сауптикапарвы» — С. Л. Невелева
10–11. О центральных образах «Стрипарвы» — Я. В. Васильков
14. От переводчиков — Я. В. Васильков, С. Л. Невелева
14. «Анугита» и «Бхагавадгита» — Я. В. Васильков
14. Эпическая Ашвамедха — Я. В. Васильков, С. Л. Невелева
15–18. От переводчиков — Я. В. Васильков, С. Л. Невелева
15–18. I. Основные темы «О жизни в обители» — С. Л. Невелева
15–18. II. О чужеродности «Маусалапарвы» — С. Л. Невелева
15–18. III. Завершение «Махабхараты» — С. Л. Невелева

No articles or indexes for books 12–13 (Śānti / Anuśāsana) in this dump.

## Reproduce

```
python web/corpus_builder/h2738_mbh_word_ingest.py --source-dir archive_anatoly_mbh_word
python -m pytest web/tests/test_mbh_word_layers.py -q
```

Parser: [web/corpus_builder/mbh_word_layers.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/mbh_word_layers.py)
Driver: [web/corpus_builder/h2738_mbh_word_ingest.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/h2738_mbh_word_ingest.py)

_Dr. Mārcis Gasūns_
