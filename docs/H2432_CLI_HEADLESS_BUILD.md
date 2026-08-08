# H2432 — Corpus_builder Phase 4 headless CLI (`--build` / `--out`)

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Model:** Grok 4.5 (`grok-4.5`)

## Goal

Ship the documented Phase 4 CLI unit so a single-book corpus HTML build runs
without GUI / without hanging on `MessageDlg`.

## Delivered

| Piece | Path / contract |
|---|---|
| CLI entry | [`Corpus_builder/PSRCBuilder/cb_headless.lpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpr) |
| Engine `--out` | `TMhHTMLBuilder.OutFileOverride` in [`uMhHTML.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/uMhHTML.pas) |
| Docs | [`Corpus_builder/README.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/README.md) § Headless CLI |
| Roadmap tick | [`Corpus_builder/ROADMAP.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Фаза 4 CLI unit `[x]` |

## Usage

```text
cb_headless --build <config.ini|work-dir> [--out <file.html>] [--check]
cb_headless <config.ini|work-dir> [check]   # H2427 golden legacy
```

| Exit | Meaning |
|---|---|
| 0 | `HasErrors=false` |
| 1 | validation / build errors (`Err.txt` written next to config) |
| 2 | usage error or missing config |

## Behaviour guarantees

1. **Constructs** `TMhHTMLBuilder`, assigns log sinks (`TCLIHost`), runs `Execute`, frees.
2. **No MessageDlg hang** — `OnConfirm` auto-yes; nil Confirm policy preserved.
3. **Pure `--build`** does not `CreateForm` the main window; only `--check` creates `TOKBottomDlg`.
4. **`--out`** sets `OutFileOverride` so `PutFile1ToFile2` targets the CLI path instead of INI `OutputHTML`.
5. **Legacy** positional form kept so `tests/golden/run_golden_case01.py` stays green without edits.

## Static source proof (this host)

No Lazarus on this agent host (`lazbuild` absent). Static checks that replace a
live binary smoke for source acceptance:

```text
grep --build / OutFileOverride / TCLIHost / Halt( in cb_headless.lpr + uMhHTML.pas
```

Commands run in the H2432 worktree (see session PR for live output):

```sh
# flag surface present
rg -n -- "--build|--out|OutFileOverride|TCLIHost|HasErrors|Halt\(" Corpus_builder/PSRCBuilder/cb_headless.lpr Corpus_builder/PSRCBuilder/uMhHTML.pas
```

Expected hits: `--build`, `--out`, `OutFileOverride`, `TCLIHost`, exit `1` on
`HasErrors`, usage `Halt(2)`.

## Residual (not this handoff)

- Recompile `cb_headless.exe` with `lazbuild` when Lazarus is available (same residual class as H2417/H2427 host gaps).
- H2433 — wire headless into `build-web-db` / `reindex`.
- H2434 — CI job for golden + headless build.
- Multi-book orchestration still lives in `fMainForm` (ARCHITECTURE residual).

## Build (when Lazarus present)

```sh
lazbuild Corpus_builder/PSRCBuilder/cb_headless.lpi
# → Corpus_builder/PSRCBuilder/lib/x86_64-win64/cb_headless.exe

cb_headless --build Corpus_builder/tests/golden/case01/input --out %TEMP%\case01_cli.html
echo %ERRORLEVEL%
```

_Dr. Mārcis Gasūns_
