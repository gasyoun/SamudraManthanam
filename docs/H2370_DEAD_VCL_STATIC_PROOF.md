# H2370 — dead VCL cleanup static proof

_Created: 07-08-2026 · Last updated: 07-08-2026_

**Handoff:** [H2370](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2370-Grok_SamudraManthanam_corpus-builder-dead-vcl-cleanup_07.08.26.md)  
**Executor:** Grok 4.5 (`grok-4.5`)  
**Toolchain (first pass):** no `dcc32` / `fpc` on host → source-level grep only.  
**Toolchain (optional follow-up, same day):** Free Pascal **3.2.2** i386-win32 installed under `%USERPROFILE%\tools\fpc\` (no Delphi 7 / no admin choco).

## Files touched

| Path | Change |
|---|---|
| [`Corpus_builder/PSRCBuilder/dcu/uSort.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uSort.pas) | implementation `uses dialogs, Math` → `uses Math` |
| [`Corpus_builder/PSRCBuilder/dcu/TextU.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextU.pas) | drop VCL `uses` + four VCL helpers |
| [`Corpus_builder/PSRCBuilder/dcu/TextUVCL.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextUVCL.pas) | **new** — `CBListToList`, `ListBoxToStringList`, `CopyStringToClipboard`, `Search_And_Replace` |
| docs / roadmap / inventory / CLAUDE / CHANGELOG | status sync |

## Grep invariants (must hold after change)

Run from repo root (or worktree) with any ripgrep-class searcher, or stdlib Python:

```python
# tools/check or one-shot:
from pathlib import Path
import re
root = Path("Corpus_builder/PSRCBuilder/dcu")
dcu = list(root.glob("*.pas"))
assert not any(re.search(r"dialogs", p.read_text(encoding="utf-8", errors="replace"), re.I) for p in dcu)
textu = (root / "TextU.pas").read_text(encoding="utf-8", errors="replace")
assert not re.search(r"CheckLst|StdCtrls|ComCTRLS|ComCtrls|clipbrd|Clipboard|TCheckListBox|TListBox|TRichEdit|\bWindows\b", textu, re.I)
hits = []
for p in dcu:
    for m in re.finditer(r"CBListToList|ListBoxToStringList|CopyStringToClipboard|Search_And_Replace", p.read_text(encoding="utf-8", errors="replace")):
        hits.append(p.name)
assert set(hits) == {"TextUVCL.pas"}
usort = (root / "uSort.pas").read_text(encoding="utf-8", errors="replace")
assert re.search(r"implementation\s+uses Math;", usort)
print("H2370 static proof OK")
```

## Measured results (this pass)

| Check | Result |
|---|---|
| `dialogs` in `dcu/*.pas` | **0 hits** |
| VCL tokens in `TextU.pas` | **0 hits** |
| Four helpers location | **TextUVCL.pas only** (no remaining defs in TextU) |
| Callers of the four helpers in Corpus_builder | **none** (already true pre-split; helpers were soft/unused by engine + forms) |
| `uSort` implementation uses | `Math` only |

## FPC compile proof (optional residual, 07-08-2026)

Delphi 7 `dcc32` is **still absent** (proprietary; `cb.cfg` points at
`c:\program files (x86)\borland\delphi7\…` which does not exist on this host).
Full GUI `cb.dpr` cannot be rebuilt without VCL. As a surrogate, the portable
stack that H2370 made Dialogs-free was compiled with **FPC 3.2.2**:

| Unit (from `origin/main` `dcu/`) | FPC result |
|---|---|
| `mytypes`, `myutils`, `uTypes`, `ArtMath`, `CalcSimU`, `statprocs`, **`uSort`** | **OK** — linked into smoke exe |
| `TextU` (VCL-free after H2370) | **1 pre-existing FPC error** at `NumCapsRus` — CP-1251 set-of-char range (`S[i] in ['А'..'Я']`-class) → `Ordinal expression expected` under FPC; **not introduced by H2370** (VCL split did not touch that function) |

Smoke program (not committed as a product binary — local only under
`%USERPROFILE%\tools\fpc\h2370-compile\`):

```pascal
{$MODE Delphi}{$H+}
program h2370_usort_smoke;
uses SysUtils, mytypes, myutils, uTypes, ArtMath, CalcSimU, statprocs, uSort;
```

- **Compile log:** [H2370_FPC_USORT_COMPILE.log](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_FPC_USORT_COMPILE.log) — `16 lines compiled, 0.5 sec`, exit 0  
- **Run:** [H2370_FPC_USORT_SMOKE_RUN.txt](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_FPC_USORT_SMOKE_RUN.txt) — `H2370 uSort smoke OK: 5 4 3 2 1`  
  (sort order is `SortIntArr` semantics as-shipped; not a correctness claim beyond “links and runs”)

### What this does / does not prove

| Claim | Status |
|---|---|
| `uSort` without `Dialogs` is FPC-portable | **proved** |
| H2370 VCL split did not break the numeric dependency chain | **proved** (ArtMath→uSort→statprocs compile) |
| Full `cb.exe` Delphi 7 rebuild | **not proved** — needs `dcc32` + VCL |
| `TextU` FPC-clean | **not proved** — one CP-1251 char-set residual (Phase 3 / encoding work) |

## Non-goals (not done here)

- Unified encoding layer (`AnsiToUTF8` rewrite) — separate roadmap unit
- `{$MODE Delphi}` mass add — separate roadmap unit
- Full `dcc32` rebuild of `cb.exe` — still blocked on Delphi 7 licence/install
- corpus-manifest pin (H2351)

## Remaining human residual

On a machine with **Delphi 7**: open `PSRCBuilder/cb.dpr`, full rebuild. Expect no
change to runtime for the current call graph (forms never called the four
helpers). Optional: `uses TextUVCL` from a form if those helpers are needed later.

_Dr. Mārcis Gasūns_
