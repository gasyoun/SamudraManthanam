# H2427 — Phase 0 golden capture + Phase 3 Lazarus re-verify

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2427](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2427-Grok_SamudraManthanam_corpus-builder-p0-golden-capture-and-p3-verify_08.08.26.md)  
**Executor:** Grok 4.5 (`grok-4.5`)  
**Depends on:** [H2417](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2417-Grok_SamudraManthanam_corpus-builder-phase3-lazarus-lcl-port_08.08.26.md) Lazarus/FPC LCL port

## Goal

Close the Phase 0 residual (byte-exact golden fixtures) and run Phase 3 **«Проверка эталоном»** against the Lazarus `cb` engine — without interactive Delphi GUI.

## Why not the old Delphi `cb.exe`

- Tracked `PSRCBuilder/cb.exe` is a **May 2026 Delphi** binary, pre-H1485/H2370/H2417 source.
- GUI-only (no CLI until Phase 4) blocked automated capture on agent sessions.
- H1485 made `TMhHTMLBuilder` **nil-safe / GUI-free** — a thin console driver can call the same engine the LCL form uses.

Golden baseline is therefore taken from the **current Lazarus engine** via `cb_headless`, which is the regression target going forward.

## Delivered

| Item | Path / result |
|---|---|
| Headless driver | [`Corpus_builder/PSRCBuilder/cb_headless.lpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpr) + [`cb_headless.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpi) (console app) |
| Golden case01 inputs | [`tests/golden/case01/input/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder/tests/golden/case01/input) — 2 ślokas, `Глава`/`[N]`/`-1-` markers, shell HTML with insert markers |
| Golden expected | [`tests/golden/case01/expected/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Corpus_builder/tests/golden/case01/expected) — HTML, `Res_html.txt`, `Err.txt`, check JSON/TSV |
| Capture/verify script | [`tests/golden/run_golden_case01.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/tests/golden/run_golden_case01.py) |
| CheckPages fix | `fCheckDialog.CheckPages` used `Result:=ErrList.Count=1` after prior stages had already filled `ErrList` → **pages always false**. Now compares against pre-check base count. `ShowMessage` on parse error → `ErrList` (headless-safe). |
| Portable check JSON | `SaveReport` stores `ExtractFileName(AFileName)` for `"input"`. |
| Stable `data-page` | `LoadPerevod` initializes `RusPage:=0`. |

### Reproduce

```text
lazbuild Corpus_builder/PSRCBuilder/cb_headless.lpi
python Corpus_builder/tests/golden/run_golden_case01.py --verify
```

Measured this session: **two consecutive `--verify` runs → PASS** (all six expected files byte-identical).

Optional recapture (overwrites `expected/`):

```text
python Corpus_builder/tests/golden/run_golden_case01.py --capture
```

## Phase 3 acceptance

Roadmap item **«Проверка эталоном»**: rebuild golden with the Lazarus engine and match `expected/` — **PASS** via `cb_headless` + `--verify`.

## Explicit residuals

| Residual | Why |
|---|---|
| Delphi GUI golden (historical binary) | Optional; stale binary vs current source. Not required for Lazarus regression. |
| Full Phase 4 CLI (`cb --build …`) | `cb_headless` is a thin engine driver, not the full CLI contract. |
| Linux `lazbuild` | Still H2431 / Phase 3 residual. |
| Check message encoding in JSON | Russian summary strings in `_check.json` still show mojibake from engine codepage; byte-stable, not fixed here. |

## Non-goals

Phase 1 lazUTF8 layer · Phase 2 unit dedupe · Phase 5 GUI fate.

_Dr. Mārcis Gasūns_
