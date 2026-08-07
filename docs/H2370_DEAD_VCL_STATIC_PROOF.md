# H2370 — dead VCL cleanup static proof

_Created: 07-08-2026 · Last updated: 07-08-2026_

**Handoff:** [H2370](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2370-Grok_SamudraManthanam_corpus-builder-dead-vcl-cleanup_07.08.26.md)  
**Executor:** Grok 4.5 (`grok-4.5`)  
**Toolchain:** no `dcc32` / `fpc` / `lazbuild` on this host — proof is source-level only.

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

## Non-goals (not done here)

- Unified encoding layer (`AnsiToUTF8` rewrite) — separate roadmap unit
- `{$MODE Delphi}` mass add — separate roadmap unit
- `dcc32` interactive rebuild of `cb.exe` — human residual when Delphi 7 is available
- corpus-manifest pin (H2351)

## Human residual

On a machine with Delphi 7: open `PSRCBuilder/cb.dpr`, full rebuild. Expect no
change to runtime for the current call graph (forms never called the four
helpers). Optional: `uses TextUVCL` from a form if those helpers are needed later.

_Dr. Mārcis Gasūns_
