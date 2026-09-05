_Created: 25-08-2026 · Last updated: 05-09-2026_

# Corpus Builder — архитектурный план

_Создано: 05-07-2026 · Обновлено: 08-08-2026_

Документ описывает **текущую** архитектуру сборщика (`cb.exe`, Delphi 7) и
**целевую** архитектуру после переноса на Lazarus / Free Pascal. Дополняет
[`ROADMAP.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md)
(там — этапы и очередность; здесь — структура и зависимости) и
[`README.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/README.md)
(обзор для пользователя).

---

## 1. Текущая архитектура (as-is)

Три слоя, но границы между ними местами размыты.

```
┌─────────────────────────────────────────────────────────────┐
│  Слой GUI (VCL, Windows-only)                                │
│    fMainForm.pas   TForm1     — меню, все операции, диалоги   │
│    fCheckDialog.pas TOKBottomDlg — проверка целостности        │
├─────────────────────────────────────────────────────────────┤
│  Слой движка                                                 │
│    uMhHTML.pas     TMhHTMLBuilder                            │
│      • модель данных (records)                               │
│      • загрузка входа (Load*)                                │
│      • проверка (Check)                                      │
│      • генерация HTML (HTML_*, OutputText)                   │
├─────────────────────────────────────────────────────────────┤
│  Слой утилит (dcu/)                                          │
│    TextU · uTypes · uSort · myutils · mytypes · StatProcs …  │
└─────────────────────────────────────────────────────────────┘
        │ файловый ввод-вывод, граница кодировок CP-1251 ↔ UTF-8
        ▼
   01_Sanskrit.txt / 02_Transl.txt / 03_Comments.txt + <config>.ini
        ▼  cb.exe
   OutputHTML  →  Data/*.html  (потребляется «Пахтаньем океана»)
```

### 1.1. Модель данных (ядро `uMhHTML.pas`)

Всё держится в массивах записей в памяти на время сборки:

| Запись | Что описывает | Ключевые поля |
|---|---|---|
| `TSlokaRec` | одна шлока: тексты + позиция | `Text`, `UvacaText`, `GlavaText`, `info`, `RusPage1/2` |
| `TSlocaInfoRec` | координаты шлоки | `NBook`, `NChapter`, `Num1/Num2`, `S_Num`, флаги `bNum*Crossing` |
| `TCommentRec` / `TCommentInfoRec` | комментарий и его привязка | `Text`, `NBook`, `NChapter1/2`, `Num` |
| `TFootNoteRec` | сноска | `Text`, `info`, `RusPage1/2` |
| `TKeyWords` | вся конфигурация сборки из INI | структурные слова (`Skazanie`, `Glava`, `Skazal`…), флаги (`OnlyRus`, `b2Transl`, `ManyTransl`, `IsFootNotes`…), `OutputHTML`, метаданные цитаты |

Санскрит (IAST) хранится в `widestring`; русский/служебный текст — в `string`
(CP-1251 на границе).

### 1.2. Поток управления

**Одна книга** — `TMhHTMLBuilder.Execute(AFileName)`:
`LoadKeyWords` (INI) → `LoadSanskrit` / `LoadPerevod` / `LoadComments` /
`LoadFootNotes` → `Check` → `OutputText` (итерация глав/шлок, вызовы `HTML_*`,
запись в `HTF`) → выход в `KeyWords.OutputHTML`.

**Много книг** — `fMainForm.CorpushtmlbuildManyBooks2Click`:
`LoadBooksCount` → на каждую книгу `PrepareBook` (разбить `ManyBooks_0N_*`) +
`Execute` → `RenameErrFile` → `ConcatAllHTMLFiles` → `PutFile1ToFile2` (вставка
между маркерами).

### 1.3. Проблемные точки связности (что чинит перенос)

- **GUI ↔ движок.** Многокнижная оркестрация (`PrepareBook`, склейка) живет в
  `fMainForm`, а не в движке, — ее нельзя запустить без формы. → В целевой
  архитектуре оркестрация переезжает в ядро.
- **Границы кодировок.** ✅ H2428: [`dcu/uEncoding.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uEncoding.pas)
  (`ToUTF8`/`FromUTF8` via LazUTF8); raw `AnsiToUTF8`/`UTF8ToAnsi` cleared from
  engine path. Residual: process still may bridge host ANSI when not UTF-8.
- **Вывод через глобальный `HTF: textFile`.** Генерация пишет в файловую
  переменную напрямую — трудно тестировать. → Писать в абстрактный поток/буфер.
- **Дубли утилит.** `TextU.pas`, `uTypes.pas` существуют и здесь, и в
  [`Units/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Units)
  основного приложения. → **H2429 split ruling:** builder `dcu/TextU`(+`TextUVCL`)
  is canonical for `cb`; Index `Units/textu.pas` is a **different** module (name
  collision only); true twin `Units/_textu` is stale; `uTypes` master = builder.
  Full table: [`docs/H2429_DCU_UNITS_CANONICAL_DIFF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2429_DCU_UNITS_CANONICAL_DIFF.md).
  Physical one-copy via `OtherUnitFiles` remains H2430.
- **Отчет об ошибках — только текст.** `ErrList` → `Err.txt`. → Плюс
  машиночитаемый формат для CI.

---

## 2. Целевая архитектура (to-be, Lazarus/FPC)

Принцип: **ядро без GUI**, над ним — три тонких фронтенда (CLI, LCL GUI, CI).
Ядро и утилиты собираются чистым FPC без LCL.

```
        ┌────────────┐   ┌────────────┐   ┌────────────┐
        │  CLI        │   │  LCL GUI   │   │   CI-джоб   │
        │ cb --build  │   │ окно +     │   │ golden +    │
        │ config.ini  │   │ проверка   │   │ пересборка  │
        └─────┬──────┘   └─────┬──────┘   └─────┬──────┘
              └────────────────┼────────────────┘
                               ▼
             ┌──────────────────────────────────────┐
             │  Ядро (модуль, без GUI, {$MODE Delphi})│
             │                                        │
             │  CorpusBuilder     фасад: Build(cfg)   │
             │  ├ Model           records (§1.1)      │
             │  ├ Loaders         Load* → массивы     │
             │  ├ Validator       Check* → отчет      │
             │  ├ HtmlWriter      HTML_* → поток      │
             │  ├ MultiBook       оркестрация книг    │
             │  └ Report          ошибки: текст+JSON  │
             └───────────────┬──────────────────────┘
                             ▼
             ┌──────────────────────────────────────┐
             │  Общие утилиты (Units/, один источник) │
             │  TextU · uTypes · encoding (lazUTF8)   │
             └──────────────────────────────────────┘
```

### 2.1. Ключевые архитектурные решения

1. **Ядро — самостоятельный модуль.** ✅ Сделано 04-08-2026 (H1485, Opus 5
   `claude-opus-5[1m]`): `TMhHTMLBuilder` очищен от VCL/`ShowMessage`, реализационный
   `uses` — `SysUtils, textu, windows, MyUtils`. Связь с UI идёт через nil-safe
   sink-и (`TProgressSink`/`TConfirmSink`/`TErrorSink`), так что headless-вызов
   просто оставляет их `nil`. Остаётся сделать публичный фасад `Build(config)`
   поверх нынешнего `Execute(AFileName)` и проверить сборку на Delphi 7 —
   компилятора в сессии не было. Детали:
   [`DEPENDENCY_INVENTORY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/DEPENDENCY_INVENTORY.md) §3a.
2. **Оркестрация многокнижной сборки — в ядре.** `PrepareBook`, `ConcatAllHTMLFiles`,
   `PutFile1ToFile2` переезжают из `fMainForm` в модуль `MultiBook`, чтобы CLI/CI
   собирали весь корпус без формы.
3. **Вывод — в абстрактный поток.** Заменить `HTF: textFile` на интерфейс
   «писателя» (файл, буфер, память), что делает генерацию проверяемой golden-тестами
   без файловой системы.
4. **Кодировки — один UTF-8 слой.** ✅ H2428: `uEncoding` (LazUTF8
   `SysToUTF8`/`UTF8ToSys`); call sites use `ToUTF8`/`FromUTF8`. Санскрит
   остается в WideString; character-safe ops available as `EncUTF8Length`/`EncUTF8Copy`.
5. **Отчет — структурируемый.** `Validator`/`Report` отдают ошибки и текстом
   (`Err.txt`, обратная совместимость), и в JSON/TSV — для автоматического падения
   CI.
6. **Утилиты — один источник (частично, H2430).** `cb.lpi` / `cb_headless.lpi`
   set `OtherUnitFiles=dcu;..\..\Units`. **Shared today:** `Units/uTypes.pas`
   (single copy; builder `TWideStringArr` promoted; `dcu/uTypes` removed).
   **Still dual-kept in `dcu/` with reason:** `TextU` (+`TextUVCL`) — case-insensitive
   name collision with Index `Units/textu.pas` (different product; H2429 split);
   builder-only modules (`ArtMath`, `myutils`, …) have no Units twins. See
   [`SHARED_CODE.md`](https://github.com/gasyoun/github-spine/blob/main/SHARED_CODE.md)
   and [`docs/H2430_OTHERUNITFILES_SHARED_UTILS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2430_OTHERUNITFILES_SHARED_UTILS.md).

### 2.2. Границы и контракты

- **Вход ядра:** путь к `<config>.ini` (или готовый `TKeyWords`) + каталог входных
  `.txt`. Никаких обращений к GUI.
- **Выход ядра:** HTML-текст (в поток) + объект отчета (ошибки/предупреждения).
  Побайтовая совместимость с текущим выходом — критерий приемки переноса.
- **Стабильно наружу:** формат входных `.txt` (см. README) и формат имен/маркеров
  выходного HTML не меняются — иначе сломается «Пахтанье океана» и веб-конвейер.

### 2.3. Тестируемость

- **Golden-file тесты** (Фаза 0 роадмапа): фиксированный вход → эталонный HTML;
  прогоняются и Delphi-, и FPC-сборкой во время переноса.
- **Юнит-тесты валидатора**: подать заведомо битые номера шлок/глав → ожидаемый
  отчет об ошибках.
- Абстрактный писатель (§2.1.3) позволяет тестировать генерацию без диска.

---

## 3. Соответствие этапам роадмапа

| Архитектурное решение | Фаза в [`ROADMAP.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) |
|---|---|
| Golden-тесты, структурированный отчет | Фаза 0 |
| Ядро без VCL, `{$MODE Delphi}`, UTF-8 слой | Фаза 1 |
| Один источник утилит (`Units/`) | Фаза 2 |
| `.lpi`/`.lpr`, формы VCL→LCL, приемка эталоном | Фаза 3 |
| Оркестрация в ядре, абстрактный поток, CLI | Фаза 4 — CLI done H2432 (`cb_headless --build/--out`); multi-book orchestration + abstract stream still residual |
| Судьба GUI (LCL vs CLI-only) | Фаза 5 |

Порядок реализации архитектуры совпадает с очередностью фаз: сперва «сеть
безопасности» (эталон), затем развязка ядра, и только потом сам перенос.

_Dr. Mārcis Gasūns_
