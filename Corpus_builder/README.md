# Corpus Builder (`cb.exe`)

_Создано: 05-07-2026 · Обновлено: 01-08-2026_

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

Открыть и собрать в **Delphi 7 IDE**:

- Файл проекта: [`PSRCBuilder/cb.dpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.dpr)
- Опции компилятора: [`PSRCBuilder/cb.cfg`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.cfg)
- Выходной каталог DCU: `PSRCBuilder/dcu/`

Скрипта командной строки для сборки нет — компилятор `dcc32.exe` из Borland
Delphi 7. Готовый `cb.exe` уже лежит в репозитории, так что для простого запуска
IDE не требуется.

> ⚠️ Delphi 7 (2002 г.) — платный проприетарный тулчейн. Стратегическое
> направление проекта — **перенос на бесплатный Lazarus / Free Pascal**, на
> котором уже собирается основное приложение. Подробности и этапы — в
> [`ROADMAP.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md).

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
   проверяет перекрестные ссылки и по главам/шлокам пишет HTML.
3. **Многокнижная сборка** ([`fMainForm.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fMainForm.pas)) —
   разбивает `ManyBooks_0N_*.txt` на отдельные книги, собирает каждую и склеивает
   результаты в единый выходной HTML между маркерами вставки.

Результат — HTML-файл, имя которого задано в `KeyWords.OutputHTML`; он копируется
в каталог `Data/` приложения «Пахтанье океана».

---

## Структура кода

```
PSRCBuilder/
  cb.dpr               точка входа проекта
  cb.cfg / cb.dof      опции компилятора Delphi 7
  cb.res               ресурсы приложения (иконка и т.п.)
  cb.exe               собранный исполняемый файл

  fMainForm.pas/.dfm   TForm1 — главное окно, все операции из меню
  fCheckDialog.pas     TOKBottomDlg — диалог проверки целостности перед сборкой
  uMhHTML.pas          TMhHTMLBuilder — ядро сборщика HTML-корпуса

  dcu/                 общие утилиты (исходники .pas + скомпилированные .dcu)
    TextU.pas            строки: UTF-8/WideString, разделители, IAST-хелперы
    uTypes.pas           общие псевдонимы типов (TIntArr, TStringArr, …)
    uSort.pas            сортировка
    myutils.pas          слияние/вставка файлов (PutFile1ToFile2, MergeFiles)
    mytypes.pas          базовые псевдонимы типов
    StatProcs.pas        статистические/арифметические процедуры
    ArtMath.pas          арифметические утилиты
```

---

## Кодировки и соглашения (кратко)

- **Кодировка**: исходные файлы — Windows CP-1251 (ANSI); на границах ввода-вывода
  используется `AnsiToUTF8` / `UTF8ToAnsi`. Для санскрита (IAST) внутри — WideString.
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
