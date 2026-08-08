# H2430 — OtherUnitFiles shared utils + SHARED_CODE

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2430 (Grok 4.5) — Corpus_builder Phase 2: OtherUnitFiles shared utils + SHARED_CODE](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2430-Grok_SamudraManthanam_corpus-builder-p2-shared-otherunitfiles_08.08.26.md)  
**Model:** Grok 4.5 (`grok-4.5`)  
**Depends on:** [H2429](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2429_DCU_UNITS_CANONICAL_DIFF.md) (canonical split ruling)

---

## Goal

Wire corpus-builder `.lpi` files so shareable units come from the main app
`Units/` directory via `OtherUnitFiles` (Index pattern), remove the obsolete
duplicate where safe, register in org `SHARED_CODE.md`, leave Phase 2 roadmap
checkboxes done.

## What changed

| Item | Action |
|---|---|
| [`Units/uTypes.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/uTypes.pas) | Added `TWideStringArr` (builder delta from H2429); now the **only** `uTypes` source |
| `Corpus_builder/PSRCBuilder/dcu/uTypes.pas` | **Removed** (obsolete copy) |
| [`cb.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.lpi) / [`cb_headless.lpi`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb_headless.lpi) | Unit path `..\..\Units\uTypes.pas`; `OtherUnitFiles=dcu;..\..\Units` |
| [`cb.cfg`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.cfg) | Delphi `-U` includes `..\..\Units\` |
| Org [`SHARED_CODE.md`](https://github.com/gasyoun/github-spine/blob/main/SHARED_CODE.md) | Row for Samudra Pascal shared `uTypes` + dual-kept TextU note |
| ROADMAP Phase 2 | Common-dir + registration checkboxes ticked |

## Dual-kept (not merged) — with reason

| Module | Location | Why not single-file under `Units/` |
|---|---|---|
| **TextU** (+ TextUVCL) | `dcu/` | Windows case-insensitive collision with Index `Units/textu.pas` (different product, H2429). Builder needs builder-only APIs used by `uMhHTML` / forms. |
| ArtMath, CalcSimU, myutils, mytypes, statprocs, uSort | `dcu/` | No Units twins; builder-local stack. |

## Build verification (08-08-2026, Lazarus 4.0 / FPC 3.2.2 win64)

| Project | Result | Evidence |
|---|---|---|
| `cb.lpi` | PASS — 7318 lines, linked `lib/x86_64-win64/cb.exe` | [`docs/H2430_LAZBUILD_CB_WIN64.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2430_LAZBUILD_CB_WIN64.log) |
| `cb_headless.lpi` | PASS — 221 lines; requires `end.` terminator fix (was `end;`) | [`docs/H2430_LAZBUILD_CB_HEADLESS_WIN64.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2430_LAZBUILD_CB_HEADLESS_WIN64.log) |
| `Index/Index_pr.lpi` | PASS if rebuilt this pass (additive `TWideStringArr` only) | [`docs/H2430_LAZBUILD_INDEX_WIN64.log`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2430_LAZBUILD_INDEX_WIN64.log) |

Compiler search path for cb now includes `-Fu…\Units` (OtherUnitFiles).

## Non-goals

- Merging builder TextU into Index textu (rejected by H2429).
- Rehoming builder-only dcu modules.
- Phase 1 lazUTF8 encoding layer (H2428 / open roadmap item).

_Dr. Mārcis Gasūns_
