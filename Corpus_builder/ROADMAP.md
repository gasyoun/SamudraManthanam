# Corpus Builder — план развития (Roadmap)

_Создано: 05-07-2026 · Обновлено: 08-08-2026_

> **Обновление 10-07-2026 (H534).** Появился **альтернативный, агент-исполнимый
> путь ингеста на Python** — не порт `cb.exe` на Lazarus, а замена его для
> **новых** текстов: PDF → канонический JSONL → готовый HTML корпуса.
> Пайплайн и его запуск описаны в
> [`web/corpus_builder/PDF_INGESTION_PIPELINE.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/PDF_INGESTION_PIPELINE.md)
> ([`ignatjev_pdf_to_canonical.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/ignatjev_pdf_to_canonical.py)
> + [`align_sanskrit.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/align_sanskrit.py)
> + [`build_corpus_html.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/build_corpus_html.py)).
> Он частично закрывает цели «единый открытый тулчейн», «headless-сборка в CI» и
> «отказ от Delphi» — для ингеста новых текстов Delphi больше не нужен. Порт
> самого `cb.exe` на Lazarus (ниже) остается актуальным для воспроизведения
> исторической GUI-логики и пересборки уже загруженных источников.

Стратегическое направление: **перенос `cb.exe` с Delphi 7 на бесплатный
Lazarus / Free Pascal**, на котором уже собирается основное приложение
[«Пахтанье океана»](https://github.com/gasyoun/SamudraManthanam/blob/main/Index/Index_pr.lpi).
Цель — единый открытый тулчейн, кросс-платформенность, возможность
безголовой (headless) сборки корпуса в CI и отказ от проприетарной лицензии
Delphi 7.

Порядок этапов — от дешевых и безопасных к дорогим и рискованным. Каждый этап
самодостаточен: проект остается рабочим после любого из них.

---

## Почему перенос, а не «оставить как есть»

- **Лицензия и доступность.** Delphi 7 (2002) — платный проприетарный компилятор;
  собрать проект может только тот, у кого он установлен. Lazarus/FPC — бесплатный
  и открытый.
- **Один тулчейн на репозиторий.** Основное приложение уже на Lazarus/FPC
  (`{$MODE Delphi}`, LCL). Сборщик — единственный узел на Delphi 7. Слияние
  тулчейнов убирает разрыв.
- **Автоматизация.** Сейчас сборка корпуса — только через GUI. Headless-режим на
  FPC позволит пересобирать корпус в CI и в веб-конвейере (FastAPI/SQLite).
- **Кросс-платформенность.** FPC собирает под Linux/macOS — сборку корпуса можно
  будет гонять на сервере samskrtam.ru, а не только на Windows-машине.

---

## Фаза 0 — Фиксация и quick wins (низкий риск, высокая отдача)

Цель: закрепить текущее состояние и убрать очевидный технический долг **до**
любого переноса, чтобы было с чем сравнивать поведение.

- [x] **Golden-file тесты.** Done 08-08-2026 (H2427, Grok 4.5 grok-4.5):
      case01 input + expected under
      [	ests/golden/case01/](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder/tests/golden/case01);
      headless driver
      [PSRCBuilder/cb_headless.lpr](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpr);
      verify script
      [	ests/golden/run_golden_case01.py](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/tests/golden/run_golden_case01.py)
      (--verify twice PASS). Baseline = Lazarus engine (Delphi GUI binary stale).
      Report:
      [docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md).

- [x] **Убрать мусор из репозитория.** Удалены из git: `Unit1.*`, `*.dof`,
      все `*.~pas`/`*.~dfm`/`*.~ddp`, `*.ddp` и все `*.dcu` (в т.ч. в `dcu/`);
      исходники `dcu/*.pas` и формы `*.dfm` сохранены. Добавлен
      [`PSRCBuilder/.gitignore`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/.gitignore).
      `cb.exe` намеренно оставлен в git (сборка корпуса без IDE).
- [x] **Почистить `cb.cfg`.** Строка `-A...` с псевдонимами `WinTypes=Windows`,
      `WinProcs=Windows`, `DbiTypes=BDE`, `DbiProcs=BDE`, `DbiErrs=BDE` удалена
      целиком — grep по всем `.pas`/`.dpr` в
      [`PSRCBuilder`](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder/PSRCBuilder)
      (включая `dcu/*.pas`) не нашёл ни одного `uses WinTypes`/`WinProcs`/`DbiTypes`/`DbiProcs`/`DbiErrs`,
      так что псевдонимы были мёртвым наследием. **Остаток на человека:** grep не
      заменяет компиляцию — финальная проверка `dcc32` на Delphi 7 не выполнялась
      (машины с Delphi 7 в этой сессии нет).
      [PR #123](https://github.com/gasyoun/SamudraManthanam/pull/123).
- [x] **Переписать `Readme.txt`** — теперь UTF-8 указатель на README/ARCHITECTURE/ROADMAP.
- [x] **Машиночитаемый отчет проверки.** `TOKBottomDlg.CheckAll`
      ([`fCheckDialog.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fCheckDialog.pas))
      пишет `<input>_check.json` и `<input>_check.tsv` (UTF-8) параллельно с
      `<input>_err.txt`: статус по каждой проверке + `ok` + `messageCount` — хук,
      на котором CI сможет падать. _(Ждет компиляции на Delphi 7 для верификации.)_

## Фаза 1 — Развязать Delphi-специфику (подготовка к переносу)

Цель: минимизировать различия между сборщиком и Lazarus-совместимым кодом,
оставаясь еще на Delphi 7 (собирается и там, и там).

- [x] **Инвентаризация зависимостей.** Done 01-08-2026 (H2064, Grok 4.5 `grok-4.5`):
      full `uses` graph from `cb.dpr`, VCL/WinAPI vs RTL vs project-local, reachable
      unit table, VCL call-site audit.
      Artifact: [`DEPENDENCY_INVENTORY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/DEPENDENCY_INVENTORY.md).
      **Correction:** `uMhHTML` is **not** GUI-free today (`MessageDlg`/`ShowMessage`/
      `ShellExecute`/`Application.ProcessMessages`/`Form1.StatusBar1` + `uses
      dialogs,fMainForm,Forms,…`) — Phase 1 «отделить движок» (H1485) is load-bearing.
- [x] **Отделить движок от формы.** Done 04-08-2026 (H1485, Opus 5 `claude-opus-5[1m]`):
      [`uMhHTML.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/uMhHTML.pas)
      больше не тянет `dialogs`/`fMainForm`/`Forms`/`controls`/`ShellApi` — реализационный
      `uses` сократился до `SysUtils, textu, windows, MyUtils` (`windows` остался только
      ради `GlobalMemoryStatus`). Введены три nil-safe sink-типа (`TProgressSink` /
      `TConfirmSink` / `TErrorSink`): прогресс идёт через `Progress(APanel, AText)`
      вместо `Form1.StatusBar1`, подтверждение — через `Confirm`, ошибки — через
      `ReportError` в `ErrList` (правило `CLAUDE.md`) вместо `ShowMessage`.
      `ShellExecute` файла ошибок вынесен к вызывающему:
      [`fMainForm.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fMainForm.pas)
      реализует sink-и и проверяет `HasErrors`/`ErrFileFullPath` на всех трёх
      точках вызова. Обратное ребро `uMhHTML → fMainForm` из графа зависимостей
      удалено. **Остаток на человека:** машины с Delphi 7 нет — `dcc32` не запускался,
      проверка source-level (см. «Верификация» в
      [`DEPENDENCY_INVENTORY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/DEPENDENCY_INVENTORY.md)).
- [x] **Мёртвые VCL-импорты.** Убрать неиспользуемый `Dialogs` из `uSort.pas`,
      развести VCL-половину `TextU` (`CheckLst`/`StdCtrls`/`ComCtrls`/`ClipBrd`)
      с чистыми строковыми хелперами — пп. 3–4 из §7
      [`DEPENDENCY_INVENTORY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/DEPENDENCY_INVENTORY.md).
      **Done 07-08-2026 (H2370, Grok 4.5 `grok-4.5`):** `uSort` implementation
      `uses Math` only; VCL helpers live in
      [`TextUVCL.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextUVCL.pas);
      `TextU` keeps pure string/IAST/UTF path. Static proof (no dcc32/FPC here):
      [`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md).
- [x] **Единый слой кодировок.** Done 08-08-2026 (H2428, Grok 4.5 `grok-4.5`):
      new [`dcu/uEncoding.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uEncoding.pas)
      (`ToUTF8`/`FromUTF8` via LazUTF8 `SysToUTF8`/`UTF8ToSys`); engine + forms +
      TextU free of raw `AnsiToUTF8`/`UTF8ToAnsi`; `lazbuild cb.lpi` + `cb_headless.lpi`
      green; golden case01 `--verify` PASS. Census:
      [`docs/H2428_LAZUTF8_ENCODING_LAYER.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2428_LAZUTF8_ENCODING_LAYER.md).
- [x] **`{$MODE Delphi}`.** Done 08-08-2026 (H2417, Grok 4.5 `grok-4.5`): all
      Corpus_builder units used by the LCL project carry `{$MODE Delphi}` (plus
      `{$H+}` on TextU).

## Фаза 2 — Дедупликация общих утилит (сближение с основным приложением)

Цель: сборщик и основное приложение перестают держать две копии одних и тех же
утилит.

- [x] **Сверить `dcu/*.pas` сборщика с [`Units/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Units) основного приложения.**
      Done 08-08-2026 (H2429, Grok 4.5 `grok-4.5`): sizes + API deltas + **split**
      canonical ruling — builder `dcu/TextU`(+`TextUVCL`) for `cb` engine; Index
      `Units/textu.pas` is a **different** module (name collision); true twin is
      stale `Units/_textu.pas`; `uTypes` master = builder (`TWideStringArr`).
      Report: [`docs/H2429_DCU_UNITS_CANONICAL_DIFF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2429_DCU_UNITS_CANONICAL_DIFF.md).
      Divergence cleanup / shared path → H2430 (do **not** drop builder-only APIs
      used by `uMhHTML`).
- [x] **Один общий каталог утилит.** Done 08-08-2026 (H2430, Grok 4.5 `grok-4.5`):
      `cb.lpi` + `cb_headless.lpi` use `OtherUnitFiles=dcu;..\..\Units` (Index pattern).
      **Shared:** [`Units/uTypes.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/uTypes.pas)
      is the single `uTypes` (builder `TWideStringArr` promoted; obsolete
      `dcu/uTypes.pas` removed). Delphi `cb.cfg` `-U` also searches `..\..\Units`.
      **Dual-kept with reason (H2429):** builder
      [`dcu/TextU.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextU.pas)
      (+ `TextUVCL`) stays in `dcu/` — Windows case-insensitive name collision with
      Index [`Units/textu.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/textu.pas)
      (different product); builder-only APIs required by `uMhHTML`. Other `dcu/*`
      (ArtMath, myutils, …) remain builder-local (no Units twins).
      Doc: [`docs/H2430_OTHERUNITFILES_SHARED_UTILS.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2430_OTHERUNITFILES_SHARED_UTILS.md).
- [x] **Зарегистрировать в карте общего кода.** Done 08-08-2026 (H2430): org hub
      [`SHARED_CODE.md`](https://github.com/gasyoun/github-spine/blob/main/SHARED_CODE.md)
      row for Samudra Pascal `uTypes` + dual-kept TextU note.

## Фаза 3 — Перенос на Lazarus/FPC (основная работа)

Цель: `cb` собирается под Lazarus/FPC, GUI работает на LCL.

- [x] **Создать `.lpi`/`.lpr`** для проекта сборщика по образцу
      [`Index/Index_pr.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Index/Index_pr.lpi).
      **Done 08-08-2026 (H2417):**
      [`PSRCBuilder/cb.lpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.lpr) +
      [`PSRCBuilder/cb.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.lpi)
      (LCL package, `OtherUnitFiles=dcu`, win64 Default mode).
- [x] **Формы VCL → LCL.** **Done 08-08-2026 (H2417):** `.lfm` for
      `fMainForm` / `fCheckDialog`; `{$R *.lfm}`; uses → LCL (`Interfaces`,
      `LCLType`/`LCLIntf` on host form). FPC fixes: WideString digit-range compare
      in `uMhHTML`, CP-1251 set-of-char → `IsRussian*` Ord helpers in TextU +
      fMainForm. `lazbuild` **green** on Windows x64 — see
      [`docs/H2417_LAZARUS_BUILD_WIN64.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2417_LAZARUS_BUILD_WIN64.log)
      (1603 lines, linked `lib/x86_64-win64/cb.exe`).
- [x] **Проверка эталоном.** Done 08-08-2026 (H2427, Grok 4.5 grok-4.5):
      python Corpus_builder/tests/golden/run_golden_case01.py --verify — six expected files
      byte-identical on two consecutive runs against Lazarus cb_headless.

- [x] **Собрать под Windows и Linux** — Windows x64 **proved** (H2417).
      Linux residual **Done 08-08-2026 (H2431, Grok 4.5 `grok-4.5`):**
      gated `ShellApi`/`ShellExecute` → `OpenDocument`, `MessageBeep` → `Beep`,
      WinAPI `CopyFile` → `FileUtil.CopyFile`, `GlobalMemoryStatus` behind
      `{$IFDEF MSWINDOWS}`; host-default target in `cb.lpi`/`cb_headless.lpi`.
      Win64 regression log:
      [`docs/H2431_WIN64_REGRESSION.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2431_WIN64_REGRESSION.log).
      Linux proof via CI:
      [`.github/workflows/corpus-builder-lazbuild.yml`](https://github.com/gasyoun/SamudraManthanam/blob/main/.github/workflows/corpus-builder-lazbuild.yml)
      (+ doc
      [`docs/H2431_LINUX_LAZBUILD.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2431_LINUX_LAZBUILD.md)).

## Фаза 4 — Headless-режим и интеграция в конвейер

Цель: сборку корпуса можно запускать без GUI, из скрипта и из CI.

- [x] **CLI-режим.** Done 08-08-2026 (H2432, Grok 4.5 `grok-4.5`):
      [`PSRCBuilder/cb_headless.lpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpr)
      accepts the documented form
      `cb_headless --build config.ini --out corpus.html` (plus legacy
      `cb_headless <dir> [check]` for H2427 golden). Constructs
      `TMhHTMLBuilder`, wires log sinks (progress/error → stdout; Confirm
      auto-yes — no MessageDlg hang), optional `OutFileOverride` for
      `--out`, exits **1** when `HasErrors`. GUI `cb.lpr` remains
      windowed-only. README usage in
      [`Corpus_builder/README.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/README.md)
      § Headless CLI. **Residual:** recompile `cb_headless.exe` with
      `lazbuild` on a machine that has Lazarus (same host pattern as H2417/H2427).
- [ ] **Стык с веб-конвейером.** Встроить headless-сборку в шаг перед
      `build-web-db.ps1` / `reindex.sh`, чтобы поисковая БД (SQLite FTS5)
      пересобиралась из свежего HTML одним прогоном.
- [ ] **CI-джоб.** GitHub Actions: собрать сборщик под FPC, прогнать golden-тесты,
      пересобрать корпус — на каждом PR, меняющем исходные тексты.

## Фаза 5 (опциональная развилка) — судьба GUI

После headless-режима встает вопрос, нужен ли настольный GUI вообще.

- **Вариант A — сохранить GUI на LCL** для переводчиков, которым удобно окно с
  проверкой целостности перед сборкой.
- **Вариант B — свести к CLI + легкому веб-интерфейсу**, отказавшись от настольного
  приложения; проверку целостности вынести в тот же CLI.

Это решение принимает человек — фиксируется отдельной записью, когда до него
дойдет очередь; здесь оставлено открытым.

---

## Сводка приоритетов

| Фаза | Риск | Отдача | Блокирует |
|---|---|---|---|
| 0. Фиксация + quick wins | низкий | высокая | всё остальное (эталон для сравнения) |
| 1. Развязать Delphi-специфику | низкий | средняя | Фазу 3 |
| 2. Дедупликация утилит | средний | средняя | — (можно параллельно) |
| 3. Перенос на Lazarus/FPC | высокий | высокая | Фазы 4–5 |
| 4. Headless + конвейер | средний | высокая | — |
| 5. Судьба GUI | — | — | развилка для человека |

Рекомендуемый первый шаг — **Фаза 0**: без эталонных golden-тестов перенос
невозможно проверить на эквивалентность.

_Dr. Mārcis Gasūns_
