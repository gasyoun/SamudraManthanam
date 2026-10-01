_Created: 25-08-2026 · Last updated: 05-09-2026_

# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project overview

**Corpus Builder** (`cb.exe`) is a Windows desktop utility for preparing and building parallel Sanskrit–Russian text corpora in HTML format. It is the **authoring/build tool** that produces the corpus HTML files consumed by the search application ("Пахтанье океана").

**Primary toolchain (H2417, 08-08-2026):** **Lazarus / Free Pascal** (LCL), same family as `Index/Index_pr.lpi`. Legacy Delphi 7 `cb.dpr` remains as a secondary reference; prefer the LCL project for new work.

## Build

### Lazarus / FPC (preferred)

```text
lazbuild Corpus_builder/PSRCBuilder/cb.lpi
```

### Headless golden driver (H2427)

```text
lazbuild Corpus_builder/PSRCBuilder/cb_headless.lpi
python Corpus_builder/tests/golden/run_golden_case01.py --verify
```

- Project: `PSRCBuilder/cb_headless.lpr` + `cb_headless.lpi` (console, no GUI)
- Calls `TMhHTMLBuilder.Execute` + optional `TOKBottomDlg.CheckAll`
- Golden fixtures: `tests/golden/case01/` — see `tests/golden/README.md`


- Project: `PSRCBuilder/cb.lpr` + `PSRCBuilder/cb.lpi` (LCL package, `{$MODE Delphi}`)
- Forms: `fMainForm.lfm`, `fCheckDialog.lfm` (VCL `.dfm` kept for historical reference)
- Output: `PSRCBuilder/lib/$(TargetCPU)-$(TargetOS)/cb.exe` (gitignored under `lib/`)
- Units search path: `PSRCBuilder/dcu/`
- Proven Windows x64 build log: `docs/H2417_LAZARUS_BUILD_WIN64.log`

### Delphi 7 (legacy)

Open and build with **Delphi 7 IDE**:

- Project file: `PSRCBuilder/cb.dpr`
- Compiler options: `PSRCBuilder/cb.cfg`

The committed root-level `cb.exe` may still be a Delphi binary until a human replaces it with a Lazarus build.

## Code structure

```
PSRC/
  cb.dpr               Project entry point
  cb.cfg               Delphi compiler options (Delphi 7)
  cb.res               Application resources (icon etc.)
  cb.txt               Brief internal notes

  fMainForm.pas/.dfm   TForm1 — main window, all menu-driven operations
  fCheckDialog.pas     TOKBottomDlg — pre-build integrity check dialog
  uMhHTML.pas          TMhHTMLBuilder — core HTML corpus builder engine

  dcu/
    TextU.pas          String utilities: UTF-8/WideString ops, delimiters, IAST helpers
    uTypes.pas         Shared array/record type aliases (TIntArr, TStringArr, etc.)
    uSort.pas          Sorting utilities
    myutils.pas        File merge/insert helpers (PutFile1ToFile2, MergeFiles)
    mytypes.pas        Basic type aliases (TSingleArr etc.)
    StatProcs.pas      Statistical/arithmetic procedures
    CalcSimU.pas       Calculator simulation unit
    ArtMath.pas        Arithmetic utilities
```

## Input file conventions

The builder reads plain-text files (UTF-8, one entry per line) from the same directory as the project config (`.ini`/`.cfg`). For a single book:

| File | Content |
|---|---|
| `01_Sanskrit.txt` | Sanskrit text in IAST transliteration, one śloka per line |
| `02_Transl.txt` | Russian translation, structured with shloka markers |
| `03_Comments.txt` | Comments/notes, starting with `ПРИМЕЧАНИЯ` header then `-999-` |

For multi-book builds, the corresponding `ManyBooks_0N_*.txt` files aggregate all books, with book boundaries marked by a configurable `BookSign` (set in `many_books_config.ini`, key `Common\BookSign`).

### Shloka numbering format

Shloka identifiers use `BOOK.CHAPTER.SHLOKA` (e.g. `1.002.052`), stored with zero-padded fields. Ranges use a hyphen: `1.002.052-055`. The double-daṇḍa `॥` separates the shloka text from its number in Sanskrit source lines.

## Core build flow (TMhHTMLBuilder)

1. **`Execute(AFileName)`** — entry point; reads a `.ini` config (same path as `AFileName`) via `LoadKeyWords`, then loads all input files and calls `OutputText`.
2. **`LoadKeyWords`** — reads `TKeyWords` record from INI: structural keywords (`Skazanie`, `Glava`, `Skazal`, …), feature flags (`OnlyRus`, `b2Transl`, `ManyTransl`, `IsFootNotes`, …), output filename, citation metadata.
3. **`LoadPerevod` / `LoadSanskrit` / `LoadComments` / `LoadFootNotes`** — populate `SlokasArr`, `SanskritArr`, `CommentsArr`, `FootNotesArr` (arrays of records).
4. **`Check`** — validates cross-references between loaded arrays; errors go to `ErrList` and `Err.txt`.
5. **`OutputText`** — iterates chapters/shlokas, writing HTML via `HTML_*` methods to `HTF` (the output HTML text file).
6. Output is written to `OutFileOverride` if set (H2432 CLI `--out`), else `KeyWords.OutputHTML`; intermediate result accumulates in `Res.txt` / `Res_html.txt`.

## Headless CLI (H2432 Phase 4)

Console program [`cb_headless.lpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpr) — not the GUI `cb.lpr`:

```
cb_headless --build <config.ini|dir> [--out <file.html>] [--check]
cb_headless <config.ini|dir> [check]   # H2427 legacy (golden runner)
```

Wires `OnProgress`/`OnError` to stdout log sinks and `OnConfirm` to auto-yes (never `MessageDlg`). Exit **1** when `HasErrors`, **2** on usage/missing config. Pure `--build` does not create the main form.

## Multi-book build flow (fMainForm)

`CorpushtmlbuildManyBooks2Click`:
1. Opens a config file via `OpenDialog`.
2. Calls `LoadBooksCount` — reads `ManyBooks_01_Sanskrit.txt` to count books from the last line's book number.
3. For each book `i`: `PrepareBook` splits `ManyBooks_0N_*.txt` into single-book `0N_*.txt` files, then `TMhHTMLBuilder.Execute` builds the HTML.
4. `RenameErrFile` archives `Err.txt` / `Res.txt` / `Res_html.txt` with a numeric suffix per book.
5. `ConcatAllHTMLFiles` merges all `Res_html_N.txt` into `Res_html_buff.txt`.
6. `PutFile1ToFile2` inserts the merged result into the master output HTML between `InsertBlockLab1` / `InsertBlockLab2` markers.

## Integrity checker (fCheckDialog / TOKBottomDlg)

Invoked from the main menu before building. `CheckAll(AFileName)` runs four sequential checks on a loaded source file, each returning `false` on first error:

- `CheckChapters` — verifies chapter markers are consecutively numbered.
- `CheckShlokas` — verifies shloka numbers increase monotonically within chapters, no duplicates, no leading zeros, page numbers valid.
- `CheckComments` — verifies comment numbering sequence per chapter.
- `CheckPages` — validates page number references.

Errors are collected in `ErrList` (shown in `Memo1`) and saved to `<input>_err.txt`.

## Key conventions

- **Encoding**: centralized in [`dcu/uEncoding.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uEncoding.pas) (`ToUTF8`/`FromUTF8` → LazUTF8 `SysToUTF8`/`UTF8ToSys`). No raw `AnsiToUTF8`/`UTF8ToAnsi` on the engine path (H2428). WideString is used for Sanskrit IAST text internally.
- **Loop indices**: 1-based (`for i:=1 to List.Count`) with zero-based array access (`List[i-1]`), consistent with the shared `uTypes`/`TextU` conventions used across the project family.
- **String utilities** (`TextU.pas`): use `CutNextUseDelimiter` (modifies `var Source`) to tokenize lines, `UTF8CutNextUseDelimiterNoTrim` for WideString. Do not use byte-level `Pos`/`Copy` on UTF-8 WideString data.
- **File helpers** (`myutils.pas`): `PutFile1ToFile2(F1, F2, MarkerBegin, MarkerEnd)` inserts the full content of `F1` into `F2` between the two marker strings (saves `.old` backup); `MergeFiles(Fn1, Fn2, Sum)` concatenates two files into a third.
- **IAST / Daṇḍa constants**: the single daṇḍa (`।`) and double daṇḍa (`॥`) are referenced as `S_danda1` / `S_danda2` (defined in `TextU`); use these constants, not raw Unicode literals.
- **Error reporting**: always append to `ErrList: TStringList` — inside the engine, call `ReportError`, which does exactly that. Never `ShowMessage` inside builder logic (it blocks batch processing).
- **The engine is GUI-free — keep it that way** (H1485, 04-08-2026). `uMhHTML.pas` uses only `SysUtils, textu, windows, MyUtils` in its implementation, and `windows` is there for `GlobalMemoryStatus` alone. Anything the engine needs from the UI goes through a nil-safe sink the host assigns after `Create`:
  - progress → `Progress(APanel, AText)` (`TProgressSink`), never `Form1.StatusBar1`;
  - a yes/no question → `Confirm(AText)` (`TConfirmSink`), never `MessageDlg`; unassigned means "proceed", so a batch run cannot hang on a modal;
  - an error → `ReportError(AText)` (`TErrorSink` is only a mirror on top of `ErrList`), never `ShowMessage`;
  - opening `Err.txt` is the **caller's** job — the engine writes the file and exposes `HasErrors` / `ErrFileFullPath`; `fMainForm` does the `ShellExecute`.

  Putting `Forms`, `Dialogs`, `Controls`, `ShellApi` or `fMainForm` back into `uMhHTML.pas` re-creates the reverse dependency edge this removed. Before/after map: `DEPENDENCY_INVENTORY.md` §3/§3a.
- **`TextU.pas` is VCL-free** (H2370, 07-08-2026). List/clipboard/RichEdit helpers live in `TextUVCL.pas` — do not pull `CheckLst`/`StdCtrls`/`ComCtrls`/`ClipBrd` back into `TextU`. `fCheckDialog.pas` remains GUI-coupled by design.
- **`uSort.pas` has no `Dialogs`** (H2370) — keep it portable (`uses Math` in implementation).

_Dr. Mārcis Gasūns_
