# H2417 — Corpus_builder Phase 3 Lazarus/FPC LCL port

_Created: 08-08-2026 · Last updated: 08-08-2026_

> **H2431 (same day):** Linux residual closed — WinAPI gates + CI `lazbuild` on ubuntu. See [`H2431_LINUX_LAZBUILD.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2431_LINUX_LAZBUILD.md).

**Handoff:** [H2417](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2417-Grok_SamudraManthanam_corpus-builder-phase3-lazarus-lcl-port_08.08.26.md)  
**Executor:** Grok 4.5 (`grok-4.5`)  
**Toolchain:** Lazarus 4.0 + FPC 3.2.2 x86_64-win64 (`C:\Users\user\tools\lazarus\lazarus-4.0\`)

## Goal

Roadmap Phase 3: `cb` builds under Lazarus/FPC with LCL GUI (not Delphi 7).

## Delivered

| Item | Path / result |
|---|---|
| Lazarus project | `Corpus_builder/PSRCBuilder/cb.lpr`, `cb.lpi` |
| Forms LCL | `fMainForm.lfm`, `fCheckDialog.lfm` (`{$R *.lfm}`) |
| `{$MODE Delphi}` | all `dcu/*.pas` + forms + `uMhHTML` + `cb.lpr` |
| Windows x64 build | **PASS** — see [H2417_LAZARUS_BUILD_WIN64.log](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2417_LAZARUS_BUILD_WIN64.log) |

### Reproduce

```text
lazbuild Corpus_builder/PSRCBuilder/cb.lpi
# → Corpus_builder/PSRCBuilder/lib/x86_64-win64/cb.exe
```

Measured: `(1008) 1603 lines compiled, 15.7 sec`, exit 0.

## Portability fixes (required for FPC)

1. **`uMhHTML`:** `(S[i+1] in [c1..c9])` → `(S[i+1] >= c1) and (S[i+1] <= c9)` (WideString vs set-of-Char).
2. **`TextU`:** `IsRussianUpperCase`/`LowerCase` use Ord CP-1251 ranges; `NumCapsRus` calls them (no set-of-char literals).
3. **`fMainForm`:** digit-space-letter split uses `IsRussianUpperCase`/`IsRussianLowerCase` instead of CP-1251 set literals.

## Explicit residuals (not done)

| Residual | Why |
|---|---|
| Phase 0 golden `expected/` re-run | No mini-set / expected capture yet; GUI-only until Phase 4 CLI |
| ~~Linux `lazbuild`~~ | **Closed H2431** — portable gates + CI workflow |
| Replace tracked root `cb.exe` with Lazarus binary | Optional human step; `lib/` is gitignored |
| lazUTF8 encoding layer | Phase 1 still-open unit |
| Phase 2 unit dedupe vs `Units/` | Separate phase |

## Non-goals

Phase 4 headless CLI · Phase 5 GUI fate decision · full golden parity proof.

_Dr. Mārcis Gasūns_
