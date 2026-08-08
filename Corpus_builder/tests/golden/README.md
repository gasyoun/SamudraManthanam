# Golden-file regression fixtures — Corpus Builder

_Created: 05-07-2026 · Last updated: 08-08-2026_

Byte-exact reference outputs of the **current Lazarus/FPC engine**
(`TMhHTMLBuilder` via [`cb_headless`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpr)).
They are the acceptance criterion for the Lazarus/FPC port (Фаза 3 of the
[ROADMAP](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md)):
re-running the headless driver on `input/` must reproduce every file under
[`expected/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder/tests/golden)
**byte-for-byte**. See
[ARCHITECTURE.md §2.2](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ARCHITECTURE.md).

> **Baseline source (H2427).** Fixtures are captured from the **Lazarus engine**,
> not the May-2026 Delphi `cb.exe` binary (stale vs H1485/H2370/H2417 source, GUI-only).
> `cb_headless` calls the same `TMhHTMLBuilder.Execute` + `TOKBottomDlg.CheckAll`
> paths the LCL form uses.

## Layout

```
tests/golden/
  run_golden_case01.py      capture + re-verify helper
  case01/
    input/
      config.ini            build config (Common section keys — see LoadKeyWords)
      01_Sanskrit.txt       BOOK.CHAPTER.SHLOKA + tab + IAST (UTF-8; book zero-padded to BookLettersCount)
      02_Transl.txt         Глава N / -page- / [N] markers (UTF-8)
      03_Comments.txt       header + optional page marker (UTF-8)
      case01_out.html       shell HTML with Insert code block markers (reset each run)
    expected/
      case01_out.html       HTML after PutFile1ToFile2 insert
      Res_html.txt          raw engine body block
      Err.txt               engine ErrList (CP-1251)
      02_Transl_err.txt     CheckAll message list
      02_Transl_check.json  machine-readable check report (UTF-8)
      02_Transl_check.tsv   machine-readable check report (UTF-8)
```

## Marker / format contract

The integrity checker's default markers (from
[`fCheckDialog.lfm`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fCheckDialog.lfm))
define the `02_Transl.txt` structure:

| Element | Marker | Example line |
|---|---|---|
| Chapter | `Глава` prefix | `Глава 1` |
| Śloka   | `[N]`          | `[1] перевод шлоки …` |
| Comment | `(N)`          | `(1) комментарий …` |
| Page    | `-N-`          | `-1-` (place **before** ślokas so `data-page` is set) |

Sanskrit numbering in the engine is `BB.CCC.SSS` with zero-padded fields
(`BookLettersCount` default 2 → `01.001.001`), tab-separated from the IAST text.

Do **not** change this contract — it is consumed by «Пахтанье океана» and the web
pipeline (see the repo
[CLAUDE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/CLAUDE.md)).

## Encoding

- Input `.txt` and `config.ini`: **UTF-8, no BOM** (engine applies `UTF8ToAnsi` on read).
- Output HTML / `Res_html.txt`: **UTF-8**.
- `Err.txt`: **CP-1251** (engine `TStringList.SaveToFile` default).
- `_check.json` / `_check.tsv`: **UTF-8**.
- When snapshotting, copy bytes verbatim — never let an editor re-save/normalize
  line endings or add a BOM.

## Capture / verify (automated)

```sh
# build headless driver (once per toolchain install)
lazbuild Corpus_builder/PSRCBuilder/cb_headless.lpi

# re-verify against committed expected/ (Phase 3 gate)
python Corpus_builder/tests/golden/run_golden_case01.py --verify

# recapture expected/ after an intentional engine change
python Corpus_builder/tests/golden/run_golden_case01.py --capture
```

Manual equivalent:

```sh
# from a case folder, after building with cb_headless into input/
diff -rq expected/ <produced-copies>   # must report no differences
```

## Status

✅ **case01 baselines captured 08-08-2026 (H2427, Grok 4.5 `grok-4.5`).**  
Two consecutive `--verify` runs matched all six expected files byte-for-byte.
Report: [`docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2427_GOLDEN_CAPTURE_P3_VERIFY.md).

_Dr. Mārcis Gasūns_
