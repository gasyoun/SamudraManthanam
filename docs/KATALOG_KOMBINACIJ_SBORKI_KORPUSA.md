# Каталог комбинаций сборки корпуса

_Created: 14-08-2026 · Last updated: 14-08-2026_

Для человека (как устроена книга) и для агента (какую команду не выдумывать). Один шаблон на все тексты **невозможен**: Атхарваведа собирается иначе, чем Ригведа, Игнатьев иначе, чем старый HTML. Ниже — оси и готовые рецепты, не новый пайплайн.

Связанные контракты (не переписывать отсюда):

- [CONVERTER_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CONVERTER_SPEC.md) — четыре parse path HTML→JSONL
- [LINE_ID_SCHEME.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LINE_ID_SCHEME.md) — стабильный `work:passage`
- [PDF_INGESTION_PIPELINE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md) — PDF Игнатьева → JSONL → HTML
- [H2449 census](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2449_IGNATIEV_BACKMATTER_LAYERS_CENSUS.md) — предисловия / словари / библиография
- Заметка Анатолию: [DLYA_ANATOLIYA_DOBAVLENIE_IGNATIEVA_VS_STARAYA_SBORKA.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/DLYA_ANATOLIYA_DOBAVLENIE_IGNATIEVA_VS_STARAYA_SBORKA.md)
- Опечатка → автопересборка: [apply_errata.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/apply_errata.py) (H2720)

Человек 14-08-2026: `cb.exe` как переводчик **никто не открывает**. Пересобирать **будем**. Путь к старой папке `01/02/03` **неизвестен**.

---

## 1. Книга — это связка, не три файла

Старый `cb` делал вид, что книга = `01_Sanskrit.txt` + `02_Transl.txt` + `03_Comments.txt`. На самом деле у издания есть слои. Их уже начали регистрировать **отдельными slug**, а не префиксом `ManyBooks_`.

| Слой | Что это | Как уже лежит | `structure` |
|---|---|---|---|
| Тело | шлоки / главы | `kama-samuha`, `01_rigveda`, `devibhagavata-purana-1` | `verse` (или `prose`) |
| Примечания | аппарат к стихам | `#commN` внутри того же jsonl; прозаический хвост — [H2450](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2450-Grok_SamudraManthanam_h2415-ignatiev-prose-commentary-layer_08.08.26.md) | сегмент `comm*` |
| Предисловие | front matter | `kama-samuha-preface` ([H2449](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2449_IGNATIEV_BACKMATTER_LAYERS_CENSUS.md)) | `prose` |
| Статья / об авторе | отдельный текст | `…-ob-avtore` | `prose` |
| Указатели / библиография / источники | back matter | `…-literatura`, `…-istochniki`, `…-antologii` | `prose` |
| Словарь издания | имена, предметы, топонимы, флора | `…-slovar-imen` и т.д. как `.txt` | `dictionary` |
| Корпусные словари | MW, Апте, Кочергина… | `dic_mw`, `kochergina` в `data.txt` | `dictionary` |

Связка = один **родительский** slug + список дочерних слоёв в `meta.json` / манифесте. Не склеивать всё в один `ManyBooks_01_Sanskrit.txt`.

---

## 2. Зачем был префикс `ManyBooks_` (и почему его не продолжаем)

В меню `cb` **две разные** команды. Имя путает.

**Команда 1** (`CorpushtmlbuildManyBooks1Click` в [fMainForm.pas](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fMainForm.pas)) — **список готовых книг**. Человек выбирает текстовый файл, в каждой строке путь к своему `config.ini`. Движок гоняет их по одной. Префикс `ManyBooks_` **не нужен**.

**Команда 2** (`CorpushtmlbuildManyBooks2Click`) — **один склеенный том**. Все мандалы/книги лежат в трёх гигантских файлах:

- `ManyBooks_01_Sanskrit.txt`
- `ManyBooks_02_Transl.txt`
- `ManyBooks_03_Comments.txt`

Граница книги — строка с `BookSign` из `many_books_config.ini`. GUI режет том на временные `01_Sanskrit.txt` на каждую книгу, вызывает однокнижный движок, склеивает HTML обратно.

Префикс нужен был только затем, чтобы **не затереть** однокнижные `01_Sanskrit.txt` в той же папке. Это имя рабочей копии, не модель данных.

В клоне таких файлов **ноль**. В новом мире том = несколько slug (`01_rigveda` … `10_rigveda`), не один `ManyBooks_*`. Префикс в рецепты не берём.

---

## 3. Два направления Python (это и есть «Ригведа не как ДБхП»)

| | Старые веды/эпос (Ригведа, Атхарваведа, МБх, Рамаяна…) | Новый Игнатьев (ДБхП, тантры…) |
|---|---|---|
| Что уже есть | готовый HTML в `Data/` (когда-то из `cb` или раннего скрипта) | PDF / `.doc` / `.docx` в `archive_ignatiev_2026/` (gitignored) |
| Что делает Python | **разбирает HTML** → JSONL ([`html_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/html_to_canonical.py), [CONVERTER_SPEC](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CONVERTER_SPEC.md)) | **создаёт** JSONL из PDF/Word, потом HTML ([PDF_INGESTION_PIPELINE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md)) |
| Опечатка в теле | править канонический JSONL (или HTML, потом снова конвертер) — **не** `cb`, пока не найдены `01/02/03` | править канонический JSONL (или исходный PDF-парсер) и перегнать `build_corpus_html.py` |
| Санскрит | уже внутри HTML (`chapter_block iast`) | отдельный join по ключу главы.стиха (`align_sanskrit.py`) |

Оба конца сходятся в **одном** JSONL-схеме и в `Data/<slug>.html`. Различаются **вход** и **ключ стиха**, не «ещё один корпус».

---

## 4. Каталог комбинаций

Оси (перемножать не надо — ниже живые клетки).

**Вход** · **ключ стиха** · **слой связки** · **режим сносок**.

### 4.1 Вход

| Код | Вход | Кто гоняет | Пример |
|---|---|---|---|
| `IN-HTML` | уже есть `Data/*.html` | `html_to_canonical.py` | `01_rigveda` … `10_rigveda`, 19 книг Атхарваведы, парвы МБх |
| `IN-PDF-IGN` | PDF Игнатьева, колофоны + `(N)` | `ignatjev_pdf_to_canonical.py` / `ignatiev_book_to_canonical.py` | ДБхП, Нирвана-тантра… |
| `IN-DOC-IGN` | `.doc`/`.docx` Игнатьева | тот же book-parser + `antiword`/pandoc | часть Калика, Йонини |
| `IN-ITX` | ITRANS с sanskritdocuments | `sanskritdocuments_dbhp_to_canonical.py` | санскрит ДБхП |
| `IN-TEI` | GRETIL TEI | `gretil_tei_to_canonical.py`, `gretil_ramayana_kanda_to_canonical.py` | Хитападеша, Рамаяна 6–7 |
| `IN-DICT-TXT` | строка = статья | конвертер path B | `dic_mw`, Кочергина |
| `IN-CB-TXT` | `01/02/03` + `config.ini` | `cb` / `cb_headless` | **только** golden `tests/golden/case01`; живой папки нет |

Новые книги Игнатьева: `IN-PDF-IGN` или `IN-DOC-IGN`, не `IN-CB-TXT`.

Пересборка Ригведы **сегодня**: `IN-HTML` (перегнать HTML→JSONL или править JSONL). Вернуться к `IN-CB-TXT` нельзя, пока не найдена папка сырья.

### 4.2 Ключ стиха (только verse)

| Код | Как берётся ключ | Где живёт | Не путать |
|---|---|---|---|
| `KEY-CLEAN` | `citation_block id="1.1"` | 66 файлов, [CONVERTER_SPEC §3 Path A-clean](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CONVERTER_SPEC.md) | |
| `KEY-RANGE` | title у `div.range`: «Ригведа. I. 1. 1» | **все 10 Ригведы, 19 Атхарваведы, 18 парв МБх, 4 канды Рамаяны** — Path A-range | эвристика TAG_CENSUS помечала их «prose» — не верить |
| `KEY-SKANDHA` | `SKANDHA.CHAPTER.VERSE` из колофона + `(N)` | ДБхП / обобщённый Игнатьев | не range-title |
| `KEY-TEI` | `xml:id` на `<lg>` или маркер `// Hit_ch.v //` | GRETIL | у Рамаяны GRETIL другой, чем у Хитападеши |

Атхарваведа ≠ Ригведа не потому что «другой Python», а потому что **другой вход и другой ключ** (часто тот же `KEY-RANGE` на HTML, но другая нарезка книг, другие комментарии, другой range-title). Рецепт пишется **на работу**, не «все веды = Ригведа».

### 4.3 Слой связки

| Код | Рецепт |
|---|---|
| `LY-BODY` | основное jsonl, `verse` или `prose` |
| `LY-NOTES` | `#comm*` в том же jsonl **или** H2450, если это проза `N. Источник:` |
| `LY-PREF` | отдельный slug `*-preface`, `ignatiev_backmatter.py` |
| `LY-GLOSS` | отдельный slug `*-slovar-*`, `.txt`, `structure=dictionary` |
| `LY-BIBL` | `*-literatura` / `*-istochniki` |
| `LY-ABOUT` | `*-ob-avtore` |
| `LY-INDEX` | указатель, которого ещё нет как отдельного kind — класть как `LY-BIBL` или новый slug, не в тело |

### 4.4 Режим сносок (Игнатьев / PDF)

| Код | Когда | Флаг |
|---|---|---|
| `FN-END` | примечания **после** последней главы (`Комментарий`) | default `ignatiev_book_to_canonical` |
| `FN-GLUE` | постраничные надстрочные цифры в теле | `--footnote-mode glued-digit` ([ingest-mode-rebaseline](https://github.com/gasyoun/claude-config/blob/main/commands/ingest-mode-rebaseline.md); Майя-тантра, часть ДБхП-PDF) |

`auto` на чужой книге не переключать: ломает уже залитые тексты.

### 4.5 Живые клетки (не абстрактное декартово произведение)

| Работа | Вход | Ключ | Слои | Сноски |
|---|---|---|---|---|
| Ригведа 1–10 | `IN-HTML` | `KEY-RANGE` | `LY-BODY` + `LY-NOTES` в HTML | — |
| Атхарваведа 1–19 | `IN-HTML` | `KEY-RANGE` | то же, **другая** нарезка книг | — |
| МБх парвы (старые) | `IN-HTML` | `KEY-RANGE` | тело + comm в HTML | — |
| МБх статьи + указатели (H2738) | `IN-DOC` (полка «Для Пахтания») | нет стиха | `LY-PREF` `mahabharata-stati` + `LY-INDEX` четыре `.txt` | — |
| Рамаяна 1–4 (старые) | `IN-HTML` | `KEY-RANGE` | тело | — |
| Рамаяна 6–7 | `IN-TEI` | `KEY-TEI` (`xml:id`) | тело | — |
| ДБхП | `IN-PDF-IGN` + `IN-ITX` | `KEY-SKANDHA` | тело по скандхам; предисловие/словарь — отдельные слои, если вырезаны | часто `FN-GLUE` на PDF |
| Тантры Игнатьева (Нирвана, Йони…) | `IN-PDF-IGN` или `IN-DOC-IGN` | `KEY-SKANDHA` / главы | `LY-BODY`; back matter — H2449 если есть `ПРЕДИСЛОВИЕ`/`СЛОВАРЬ` | `FN-END` или `FN-GLUE` по книге |
| Кама-самуха | `IN-DOC-IGN` | тело + 9 слоёв H2449 | полный набор `LY-PREF/GLOSS/BIBL/ABOUT` | — |
| Хитападеша | `IN-TEI` | inline `// Hit_ch.v //` | пока без русской стороны | — |
| Словари корпуса | `IN-DICT-TXT` | нет стиха, `eN` | сами себе слой | — |
| Golden `case01` | `IN-CB-TXT` | однокнижный `cb_headless` | только тест | — |

Новую работу **сначала** кладут в эту таблицу (одна строка), потом пишут парсер. Не наоборот.

---

## 5. Что делать, когда нашлась опечатка

1. Записать строку в `web/corpus_builder/errata/<slug>/errata.yml` (схема как в [SanskritGrammar Knauer `errata.yml`](https://github.com/gasyoun/SanskritGrammar/blob/main/KnauerFrazy_1908/errata.yml): `read` / `instead` / `found_by` / `date_added` / `fixed_in`). Для корпуса добавить `work` + `passage` (или `id` сегмента), не «стр. 117», если страницы печати нет. Пилот: [bhagavati-manasa-puja-stotra](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/errata/bhagavati-manasa-puja-stotra/errata.yml).
2. Один скрипт патчит канонический JSONL и гоняет рецепт `html-from-jsonl` из [recipes.json](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/errata/recipes.json) (машина для §4.5). Человек **не** запускает `cb.exe`. Не перегонять PDF/Word заново — это сотрёт патч.

```
python web/corpus_builder/apply_errata.py --work bhagavati-manasa-puja-stotra --rebuild --data-dir Index/lib/x86_64-win64/Data
python web/corpus_builder/build_errata.py bhagavati-manasa-puja-stotra
```

Доказать на фикстуре (без живого JSONL):

```
python -m pytest tests/test_apply_errata.py -v
```

Коды `IN-*` / `KEY-*` в §4.5 говорят, **какой** вход у книги. После правки JSONL пересборка всегда `html-from-jsonl` ([build_corpus_html.py](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_corpus_html.py)).

Старые HTML «году и больше» — это долг `IN-HTML` / `IN-PDF-IGN` по строкам таблицы, не долг `ManyBooks_`.

---

## 6. Агенту: чего не делать

- Не предлагать `ManyBooks_` как имя новых файлов.
- Не кормить Ригведу `ignatjev_pdf_to_canonical.py`.
- Не кормить ДБхП `html_to_canonical.py`, пока канон — PDF-jsonl.
- Не включать `FN-GLUE` по умолчанию на книгу с `FN-END`.
- Не класть предисловие в то же jsonl, что шлоки, если для этой семьи уже принят отдельный slug (H2449).
- Не выдумывать пятый parse path, пока не заполнена строка в §4.5.

## 7. Человеку: чего не делать

- Не искать «кнопку Пересобрать всё» в `cb.exe`.
- Не ждать, пока найдётся папка `01_Sanskrit.txt` — пересборка Ригведы идёт от HTML/JSONL.
- Прислать опечатку текстом «в X вместо Y, место Z» — этого достаточно, чтобы завести строку errata.

_Dr. Mārcis Gasūns_
