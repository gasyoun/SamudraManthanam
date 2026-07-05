# Golden-file regression fixtures — Corpus Builder

_Created: 05-07-2026 · Last updated: 05-07-2026_

Byte-exact reference outputs of the **current** `cb.exe` (Delphi 7). They are the
acceptance criterion for the planned Lazarus/FPC port (Фаза 3 of the
[ROADMAP](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md)):
the ported binary must reproduce every file under [`expected/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder/tests/golden)
**byte-for-byte** from the same inputs. See
[ARCHITECTURE.md §2.2](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ARCHITECTURE.md).

## Layout

```
tests/golden/
  <case>/
    input/
      config.ini          build config (Common section keys — see LoadKeyWords)
      01_Sanskrit.txt      Sanskrit IAST, one śloka per line (CP-1251)
      02_Transl.txt        Russian translation: Глава N / [N] / (N) / -N- markers (CP-1251)
      03_Comments.txt      comments block: ПРИМЕЧАНИЯ header then -999- (CP-1251)
    expected/
      <OutputHTML>          the exact HTML cb.exe produced (UTF-8)
      *_err.txt             the exact integrity-check log (CP-1251)
      *_check.json          machine-readable check report (UTF-8) — new in Фаза 0
      *_check.tsv           machine-readable check report (UTF-8) — new in Фаза 0
```

## Marker / format contract

The integrity checker's default markers (from
[`fCheckDialog.dfm`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fCheckDialog.dfm))
define the `02_Transl.txt` structure:

| Element | Marker | Example line |
|---|---|---|
| Chapter | `Глава` prefix | `Глава 1` |
| Śloka   | `[N]`          | `[1] перевод шлоки …` |
| Comment | `(N)`          | `(1) комментарий …` |
| Page    | `-N-`          | `-12-` |

Śloka numbering in the Sanskrit source is `BOOK.CHAPTER.SHLOKA` (zero-padded,
e.g. `1.002.052`; ranges `1.002.052-055`), with `॥` separating text from number.
Do **not** change this contract — it is consumed by «Пахтанье океана» and the web
pipeline (see the repo
[CLAUDE.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/CLAUDE.md)).

## Encoding (critical for byte-exactness)

- Input `.txt` and `config.ini`: **CP-1251 (ANSI), no BOM**.
- Output HTML: **UTF-8** (the builder converts via `AnsiToUTF8`).
- `_check.json` / `_check.tsv`: **UTF-8**.
- When snapshotting, copy bytes verbatim — never let an editor re-save/normalize
  line endings or add a BOM, or the diff against the port will be spurious.

## Capture procedure (must be run on a machine with `cb.exe`)

`cb.exe` is a GUI Delphi 7 tool with **no CLI/headless mode** (adding one is Фаза 4),
so the baseline is captured interactively:

1. Place a case's `input/` files together in one working folder (the builder reads
   `config.ini` from the same folder as the file you open).
2. Run [`cb.exe`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.exe).
3. Run the integrity check first (menu → check) against `02_Transl.txt`; it writes
   `02_Transl_err.txt` **and** (after Фаза 0) `02_Transl_check.json` /
   `02_Transl_check.tsv`.
4. Run the single-book HTML build; it writes the file named in `config.ini`
   `Common\OutputHTML`.
5. Copy the produced HTML + `_err.txt` + `_check.*` into this case's `expected/`
   **without re-encoding**.
6. Commit. From then on, re-running the port on `input/` must reproduce `expected/`
   byte-for-byte.

## Verifying a port against the baseline

```sh
# from a case folder, after building with the ported binary into out/
diff -rq expected/ out/     # must report no differences
```

## Status

⚠️ **Baselines not yet captured.** This session (Opus 4.8, `claude-opus-4-8`) had no
Delphi 7 toolchain and `cb.exe` needs interactive GUI use, so the `expected/` outputs
must be captured on a Windows machine running `cb.exe` (steps above). No input set is
committed yet either: the shipped corpus's real source `.txt`/`config.ini` are **not**
in this repo, so a representative minimal case should be assembled from real book data
(preferred) rather than fabricated, to make the baseline a meaningful regression anchor.

_Dr. Mārcis Gasūns_
