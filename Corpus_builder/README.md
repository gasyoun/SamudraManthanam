# Corpus Builder (`cb.exe`)

_Создано: 05-07-2026 · Обновлено: 08-08-2026_

**Сборщик корпуса** — настольная утилита для Windows, которая готовит и собирает
параллельный санскритско-русский корпус в формате HTML. Это **авторский/сборочный
инструмент**: из простых текстовых файлов (санскрит в IAST, русский перевод,
комментарии) он производит HTML-файлы корпуса, которые затем читает поисковое
приложение [«Пахтанье океана»](https://github.com/gasyoun/SamudraManthanam/blob/main/Index/Index_pr.lpi)
(Samudra Manthanam / Churning of the Ocean).

Написан на **Delphi 7** (классический VCL, 32-битный Win32). Исходники и собранный
`cb.exe` лежат в подпапке [`PSRCBuilder/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder/PSRCBuilder).

> Для агентов и разработчиков подробные внутренние соглашения — в
> [`CLAUDE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/CLAUDE.md).
> Этот README — обзор для человека; стратегический план — в
> [`ROADMAP.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md);
> карта uses/VCL для порта — в
> [`DEPENDENCY_INVENTORY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/DEPENDENCY_INVENTORY.md) (H2064).

---

## Место в конвейере

```
   тексты (.txt)              cb.exe                 HTML-корпус            «Пахтанье океана»
 ┌──────────────┐        ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
 │ 01_Sanskrit  │        │  Corpus      │        │  Data/*.html │        │  поиск по    │
 │ 02_Transl    │ ─────► │  Builder     │ ─────► │  (+.no_tags) │ ─────► │  корпусу     │
 │ 03_Comments  │        │  (Delphi 7)  │        │              │        │  (Lazarus)   │
 └──────────────┘        └──────────────┘        └──────────────┘        └──────────────┘
   переводчик              этот репозиторий          Data/                  Index/
```

Корпус, собранный этим инструментом, — источник ряда «gate»-словарей для смежного
проекта `pwg_ru` (PWG→RU). Данные отсюда **запрашиваются, а не дублируются**.

---

## Сборка

### Lazarus / Free Pascal (primary since H2417)

```text
lazbuild Corpus_builder/PSRCBuilder/cb.lpi            # GUI
lazbuild Corpus_builder/PSRCBuilder/cb_headless.lpi   # headless CLI
```

Outputs land under `PSRCBuilder/lib/<cpu-os>/` (e.g. `lib/x86_64-win64/cb.exe`
and `cb_headless.exe`).

### Delphi 7 (legacy binary still in tree)

- Файл проекта: [`PSRCBuilder/cb.dpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.dpr)
- Опции компилятора: [`PSRCBuilder/cb.cfg`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.cfg)
- Выходной каталог DCU: `PSRCBuilder/dcu/`

Компилятор `dcc32.exe` (Borland Delphi 7). Готовый legacy `cb.exe` лежит в
`PSRCBuilder/` — GUI-only; headless is the Lazarus `cb_headless` target.

> ⚠️ Delphi 7 (2002 г.) — платный проприетарный тулчейн. Стратегическое
> направление проекта — **Lazarus / Free Pascal** (Фаза 3–4 роадмапа).
> Подробности — в
> [`ROADMAP.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md).

---

## Headless CLI (H2432 · Phase 4)

Сборка корпуса **без окна** — консольный бинарь `cb_headless` (не GUI `cb`):

```text
# documented Phase-4 form
cb_headless --build path\to\config.ini --out path\to\corpus.html

# work-dir form (looks for config.ini inside)
cb_headless --build path\to\work-dir --out corpus.html

# optional integrity check before build (writes 02_Transl_check.json/.tsv)
cb_headless --build path\to\work-dir --check --out corpus.html

# H2427 golden / legacy (still supported)
cb_headless path\to\work-dir check
```

| Flag | Meaning |
|---|---|
| `--build` / `-b` | Config `.ini` **or** directory containing `config.ini` |
| `--out` / `-o` | Output HTML (overrides INI `Common\OutputHTML` via `OutFileOverride`) |
| `--check` | Run `TOKBottomDlg.CheckAll` on `02_Transl.txt` first |
| `--help` | Usage |

**Behaviour:** constructs `TMhHTMLBuilder`, assigns log sinks (progress/errors to
stdout; Confirm always auto-yes — no `MessageDlg` hang), calls `Execute`, exits
with code **0** on success, **1** if `HasErrors` (see `Err.txt` next to the
config), **2** on usage / missing config. Pure `--build` never creates the main
form; only `--check` creates the check dialog.

Golden re-verify still uses the legacy positional form via
[`tests/golden/run_golden_case01.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/tests/golden/run_golden_case01.py).

---

## Входные файлы

Сборщик читает текстовые файлы (UTF-8, одна запись на строку) из того же каталога,
что и конфиг проекта (`.ini` / `.cfg`). Для одной книги:

| Файл | Содержимое |
|---|---|
| `01_Sanskrit.txt` | Санскрит в транслитерации IAST, одна шлока на строку |
| `02_Transl.txt` | Русский перевод, размеченный маркерами шлок |
| `03_Comments.txt` | Комментарии/примечания: заголовок `ПРИМЕЧАНИЯ`, затем `-999-` |

Для многокнижной сборки соответствующие файлы `ManyBooks_0N_*.txt` объединяют все
книги; границы книг помечаются настраиваемым `BookSign` (задается в
`many_books_config.ini`, ключ `Common\BookSign`).

### Нумерация шлок

Идентификатор шлоки — `КНИГА.ГЛАВА.ШЛОКА` (например `1.002.052`), поля с
ведущими нулями. Диапазоны — через дефис: `1.002.052-055`. Двойная данда `॥`
отделяет текст шлоки от ее номера в строках санскрита.

---

## Как это работает

1. **Проверка целостности** ([`fCheckDialog.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fCheckDialog.pas)) —
   перед сборкой прогоняет четыре последовательных проверки исходника: главы
   пронумерованы подряд, номера шлок монотонно растут без дубликатов и ведущих
   нулей, нумерация комментариев корректна, ссылки на страницы валидны. Ошибки
   собираются в `ErrList` и пишутся в `<input>_err.txt`.
2. **Сборка HTML** ([`uMhHTML.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/uMhHTML.pas),
   `TMhHTMLBuilder`) — читает `.ini`-конфиг, загружает все входные файлы в массивы
   записей (`SlokasArr`, `SanskritArr`, `CommentsArr`, `FootNotesArr`),
   проверяет перекрестные ссылки и по главам/шлокам пишет HTML. С 04-08-2026
   (H1485) движок не зависит от VCL: прогресс, подтверждения и ошибки идут через
   nil-safe sink-и, которые назначает форма-хозяин, а `Err.txt` открывает
   вызывающий (`HasErrors` / `ErrFileFullPath`).
3. **Многокнижная сборка** ([`fMainForm.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fMainForm.pas)) —
   разбивает `ManyBooks_0N_*.txt` на отдельные книги, собирает каждую и склеивает
   результаты в единый выходной HTML между маркерами вставки.

Результат — HTML-файл, имя которого задано в `KeyWords.OutputHTML`; он копируется
в каталог `Data/` приложения «Пахтанье океана».

---

## Структура кода

```
PSRCBuilder/
  cb.dpr / cb.lpr      GUI entry (Delphi 7 / Lazarus)
  cb_headless.lpr/.lpi headless CLI entry (H2427 + H2432 --build/--out)
  cb.cfg               опции компилятора Delphi 7
  cb.res               ресурсы приложения (иконка и т.п.)
  cb.exe               legacy GUI binary (Delphi 7)

  fMainForm.pas/.dfm   TForm1 — главное окно, все операции из меню
  fCheckDialog.pas     TOKBottomDlg — диалог проверки целостности перед сборкой
  uMhHTML.pas          TMhHTMLBuilder — ядро сборщика HTML-корпуса

  dcu/                 общие утилиты (исходники .pas + скомпилированные .dcu)
    TextU.pas            строки: UTF-8/WideString, разделители, IAST-хелперы (без VCL)
    TextUVCL.pas         VCL-хелперы (списки/clipboard/RichEdit), вынесены из TextU (H2370)
    uTypes.pas           общие псевдонимы типов (TIntArr, TStringArr, …)
    uSort.pas            сортировка (без Dialogs)
    myutils.pas          слияние/вставка файлов (PutFile1ToFile2, MergeFiles)
    mytypes.pas          базовые псевдонимы типов
    StatProcs.pas        статистические/арифметические процедуры
    ArtMath.pas          арифметические утилиты
```

---

## Кодировки и соглашения (кратко)

- **Кодировка**: единый слой [`dcu/uEncoding.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uEncoding.pas)
  (`ToUTF8` / `FromUTF8` → LazUTF8). Сырые `AnsiToUTF8`/`UTF8ToAnsi` на пути
  движка убраны (H2428). Для санскрита (IAST) внутри — WideString.
- **Индексы циклов**: 1-based (`for i:=1 to List.Count`) с 0-based доступом
  (`List[i-1]`) — единое соглашение всего семейства проектов.
- **Данды**: одиночная `।` и двойная `॥` — через константы `S_danda1` / `S_danda2`
  из `TextU`, не сырыми Unicode-литералами.
- **Ошибки**: всегда добавлять в `ErrList: TStringList`; не вызывать `ShowMessage`
  внутри логики сборщика (это блокирует пакетную обработку).

Полный список соглашений — в
[`CLAUDE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/CLAUDE.md).

---

## См. также

- [`ROADMAP.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) — план развития (перенос на Lazarus/FPC, поэтапно).
- [`ARCHITECTURE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ARCHITECTURE.md) — текущая и целевая архитектура (ядро/фронтенды, модель данных).
- [`CLAUDE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/CLAUDE.md) — внутренние соглашения для разработчиков/агентов.
- [Основное приложение «Пахтанье океана»](https://github.com/gasyoun/SamudraManthanam/blob/main/README.md) — поиск по собранному корпусу.

_Dr. Mārcis Gasūns_
