# H2428 — Corpus_builder Phase 1: unified lazUTF8 encoding layer

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2428](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2428-Grok_SamudraManthanam_corpus-builder-p1-lazutf8-encoding-layer_08.08.26.md)  
**Executor:** Grok 4.5 (`grok-4.5`)  
**Depends on:** [H2417](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2417-Grok_SamudraManthanam_corpus-builder-phase3-lazarus-lcl-port_08.08.26.md) LCL port · [H2427](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2427-Grok_SamudraManthanam_corpus-builder-p0-golden-capture-and-p3-verify_08.08.26.md) golden (rebaselined this pass)

## Goal

Roadmap Phase 1 «Единый слой кодировок»: replace scattered raw `AnsiToUTF8` /
`UTF8ToAnsi` with a single helper unit backed by LazUTF8-style APIs (Index already
uses LazUTF8).

## Delivered

| Item | Result |
|---|---|
| Unit | [`Corpus_builder/PSRCBuilder/dcu/uEncoding.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uEncoding.pas) — `ToUTF8` / `FromUTF8` / `EncUTF8Length` / `EncUTF8Copy` |
| Engine path | `uMhHTML`, `fMainForm`, `fCheckDialog`, `TextU` — **0** active raw `AnsiToUTF8`/`UTF8ToAnsi` |
| Projects | `cb.lpi` + `cb_headless.lpi` list `uEncoding` |
| `lazbuild cb.lpi` | **PASS** — 7385 lines, exit 0 ([log](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2428_LAZARUS_BUILD_WIN64.log)) |
| `lazbuild cb_headless.lpi` | **PASS** — 6003 lines, exit 0 |
| Golden case01 | **PASS** after rebaseline (`--capture` then `--verify` ×1) |
| Roadmap | Phase 1 encoding unit ticked |

## Before / after census (active code)

| File | Before `AnsiToUTF8`/`AnsiToUtf8` | Before `UTF8ToAnsi`/`Utf8ToAnsi` | After raw |
|---|---:|---:|---|
| `uMhHTML.pas` | 10 | 18 | 0 |
| `fMainForm.pas` | 8 | 9 | 0 |
| `fCheckDialog.pas` | 2 | 0 | 0 |
| `dcu/TextU.pas` | 1 | 0 | 0 |
| **Total** | **21** | **27** | **0** |

Commented-out historical call sites (5+2 in `uMhHTML`) were renamed in place so
greps for the raw SysUtils/System names stay empty; they remain comments only.

## Design

```
call site  →  ToUTF8 / FromUTF8  →  (string) identity under UTF8_RTL
                                   (WideString) UTF8Encode via LazUTF8
             EncUTF8Length/Copy  →  LazUTF8.UTF8Length / UTF8Copy
```

Under Lazarus 4 + FPC 3.2.2 **`UTF8_RTL`**, LazUTF8’s `SysToUTF8`/`UTF8ToSys`
are themselves identity. The named helpers still earn their keep: one import
surface, call-site intent (`emit UTF-8` vs `legacy bridge`), and a single place
to retarget if pure UTF-8 I/O ever needs an explicit code-page pin.

## Golden rebaseline (not silent)

H2427 `expected/Err.txt` was **CP-1251** bytes (`CF F0 EE…` = «Проверка…»).
After identity UTF-8 layer, the same message is emitted as **UTF-8** (and HTML
sizes shifted: `case01_out.html` 1096→1002 B, `Res_html.txt` 920→826 B). That is
the intended Phase-1 move away from CP-1251 I/O, so golden was **re-captured**
with `run_golden_case01.py --capture` and re-verified **PASS**.

## Side fix (headless program end)

`cb_headless.lpr` ended with `end;` — FPC requires `end.` for programs. Broken
on `main` after H2432 (GUI `cb.lpi` still built). Fixed in this PR so golden can
run.

## Residual table

| Residual | Why |
|---|---|
| Source `.pas` file encodings still mixed on disk | Historical CP-1251 string literals in some units; not rewritten this pass |
| `TextFile` global `HTF` still raw `Write` | Stream abstraction is a separate architecture item |
| Linux `lazbuild` | Still H2431 / Phase 3 residual |
| Physical one-copy of units vs `Units/` | H2430 Phase 2 |

## Reproduce

```text
lazbuild Corpus_builder/PSRCBuilder/cb.lpi
lazbuild Corpus_builder/PSRCBuilder/cb_headless.lpi
python Corpus_builder/tests/golden/run_golden_case01.py --verify
```

_Dr. Mārcis Gasūns_
