# Corpus Builder — dependency inventory (Phase 1)

_Created: 01-08-2026 · Last updated: 01-08-2026_

Source: [Corpus_builder/ROADMAP.md](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/ROADMAP.md) Phase 1 item
«Инвентаризация зависимостей». Closed by the `/roadmap-item-exec` pass that
produced this file (Grok 4.5 `grok-4.5`).

Scope: every unit reachable from
[`PSRCBuilder/cb.dpr`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/cb.dpr),
with each `uses` clause classified as **VCL/WinAPI**, **RTL/portable**, or
**project-local**. This is the prep map for Phase 1 «отделить движок от формы»
and Phase 3 Lazarus/FPC port — not a port itself.

---

## 1. Reachability from `cb.dpr`

Entry point:

```pascal
program cb;
uses Forms, fMainForm, fCheckDialog, uMhHTML;
```

BFS over project units (interface + implementation `uses`) pulls in **every**
`dcu/*.pas` source. **No dead local unit** relative to `cb.exe` — all eleven
Pascal files participate.

| Unit | Path | ~LOC | Role |
|---|---|---:|---|
| `cb` | `PSRCBuilder/cb.dpr` | 17 | program entry, creates `Form1` + `OKBottomDlg` |
| `fMainForm` | `PSRCBuilder/fMainForm.pas` | 1539 | main window, menus, multi-book orchestration |
| `fCheckDialog` | `PSRCBuilder/fCheckDialog.pas` | 295 | integrity-check dialog (`TOKBottomDlg`) |
| `uMhHTML` | `PSRCBuilder/uMhHTML.pas` | 1877 | `TMhHTMLBuilder` — HTML corpus engine |
| `TextU` | `PSRCBuilder/dcu/TextU.pas` | 1442 | string/UTF-8/IAST helpers (+ some VCL list helpers) |
| `uTypes` | `PSRCBuilder/dcu/uTypes.pas` | 79 | shared array/record aliases |
| `myutils` | `PSRCBuilder/dcu/myutils.pas` | 227 | `PutFile1ToFile2`, `MergeFiles` |
| `mytypes` | `PSRCBuilder/dcu/mytypes.pas` | 12 | basic type aliases for `myutils` |
| `CalcSimU` | `PSRCBuilder/dcu/CalcSimU.pas` | 326 | calculator-sim helpers (via `TextU`) |
| `StatProcs` | `PSRCBuilder/dcu/statprocs.pas` | 605 | stats/arithmetic (via `TextU`) |
| `uSort` | `PSRCBuilder/dcu/uSort.pas` | 177 | sorting (via `StatProcs`) |
| `ArtMath` | `PSRCBuilder/dcu/ArtMath.pas` | 679 | arithmetic (via `uSort`) |

Dependency graph (project-local edges only):

```
cb
├── fMainForm ──┬── fCheckDialog ── TextU ──┬── CalcSimU
│               │                           ├── StatProcs ── uSort ── ArtMath
│               │                           └── uTypes
│               ├── uMhHTML ──┬── TextU (as above)
│               │             ├── myutils ── mytypes
│               │             └── fMainForm   ← engine→GUI reverse edge (see §3)
│               ├── myutils
│               └── uTypes
└── uMhHTML / fCheckDialog (also direct from cb.dpr)
```

---

## 2. External units — VCL/WinAPI vs RTL

### VCL / WinAPI (not portable as-is; need LCL or extraction)

| Unit | Imported by |
|---|---|
| `Forms` | `cb`, `fMainForm`, `fCheckDialog`, **`uMhHTML`** |
| `Dialogs` | `fMainForm`, `fCheckDialog`, **`uMhHTML`**, `uSort` (import only — see §4) |
| `Controls` | `fMainForm`, `fCheckDialog`, **`uMhHTML`** |
| `Graphics` | `fMainForm`, `fCheckDialog` |
| `StdCtrls` | `fMainForm`, `fCheckDialog`, **`TextU`** |
| `Buttons` | `fCheckDialog` |
| `ExtCtrls` | `fCheckDialog` |
| `Menus` | `fMainForm` |
| `ComCtrls` | `fMainForm`, **`TextU`** |
| `CheckLst` | **`TextU`** |
| `ClipBrd` | `fMainForm`, **`TextU`** |
| `Messages` | `fMainForm` |
| `Windows` | `fMainForm`, `fCheckDialog`, **`uMhHTML`**, **`TextU`** |
| `ShellApi` | `fMainForm`, **`uMhHTML`** |

### RTL / portable under FPC `{$MODE Delphi}`

| Unit | Imported by |
|---|---|
| `SysUtils` | almost every unit |
| `Classes` | `uMhHTML`, `fMainForm`, `fCheckDialog`, `TextU` |
| `IniFiles` | `uMhHTML`, `fMainForm` |
| `Math` | `TextU`, `CalcSimU`, `StatProcs`, `uSort`, `ArtMath` |
| `Variants` | `fMainForm`, `TextU` |
| `DateUtils` | `TextU` |

---

## 3. Engine is **not** GUI-free today

The roadmap / CLAUDE.md claim that
[`uMhHTML.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/uMhHTML.pas)
«почти не зависит от GUI» is **aspirational, not current fact**. Concrete VCL
call sites inside the builder engine:

| File | Line(s) | Call | Effect |
|---|---|---|---|
| `uMhHTML.pas` | 225 | `MessageDlg(...)` | blocks on empty-path confirm |
| `uMhHTML.pas` | 245 | `ShellExecute` + `Application.Handle` | opens `Err.txt` in default app |
| `uMhHTML.pas` | 672, 1003, 1143 | `ShowMessage(...)` | error popups mid-load |
| `uMhHTML.pas` | 809, 1259 | `Application.ProcessMessages` | GUI pump during long load/output |
| `uMhHTML.pas` | 556–557, 808, 891–892, 1041–1042, 1258 | `Form1.StatusBar1...` | **direct form coupling** |
| `fCheckDialog.pas` | 178, 214 | `ShowMessage(...)` | checker error popups |
| `TextU.pas` | 718–742 | `Clipboard.*` | `CopyStringToClipboard` |
| `TextU.pas` | 43 / 1382, 75 / 491 | `TCheckListBox` / `TListBox` helpers | UI-only list bridges |

Phase 1 «Отделить движок от формы» must therefore:

1. Replace `Form1.StatusBar1` progress with a callback / nil-safe progress sink
   (no reference to `fMainForm` from `uMhHTML`).
2. Route `ShowMessage` / `MessageDlg` through `ErrList` only (or a logging sink);
   never block the engine.
3. Drop `ShellExecute` of error files from the engine (caller/GUI may open them).
4. Drop `Application.ProcessMessages` from the engine (or gate behind `Assigned(Application)`
   for GUI builds only).
5. Split `TextU` into pure string helpers (engine path) vs VCL list/clipboard helpers
   (GUI path) — the latter are unused by the load/build core.

---

## 4. Dead / soft VCL imports

| Unit | Import | Evidence |
|---|---|---|
| `uSort.pas` | `Dialogs` | no `ShowMessage` / `MessageDlg` / `Dialogs.` reference in body — safe to delete from `uses` |
| `TextU.pas` | `CheckLst`, `StdCtrls`, `ComCTRLS` | only used by `CBListToList` / `ListBoxToStringList`; not on the `TMhHTMLBuilder` call path |
| `TextU.pas` | `clipbrd` / `Windows` (clipboard) | only `CopyStringToClipboard`; engine path does not need them |

These are cheap Phase 1 cleanups after the engine is cut free of `fMainForm`.

---

## 5. Portable core (Phase 1 / 3 target)

Units that already have **no VCL call sites** and only RTL + local deps — the
first candidates to compile under FPC without LCL:

| Unit | External deps | Notes |
|---|---|---|
| `mytypes` | (none) | trivial |
| `myutils` | `SysUtils`, `mytypes` | file merge/insert — pure I/O |
| `uTypes` | `SysUtils` | type aliases only |
| `ArtMath` | `Math`, `uTypes` | numeric |
| `CalcSimU` | `Math`, `uTypes` | numeric |
| `StatProcs` | `Math`, `uTypes`, `uSort` | numeric |
| `uSort` | `Math`, `uTypes`, `ArtMath` (+ dead `Dialogs`) | drop dead import → portable |

**Not yet portable:** `uMhHTML`, `TextU` (partial), `fMainForm`, `fCheckDialog`.

---

## 6. Overlap with main app `Units/` (Phase 2 preview)

| File | Builder | Main app [`Units/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Units) | Identical? |
|---|---|---|---|
| `TextU.pas` | 37 202 B | 11 651 B | **No** — builder copy is ~3× larger |
| `uTypes.pas` | 1 735 B | 1 697 B | **No** — small drift |
| `ArtMath`, `CalcSimU`, `mytypes`, `myutils`, `statprocs`, `uSort` | builder only | — | no main-app twin under those names |
| `UpdateChecker.pas`, `_Math.pas`, `_textu.pas`, `_winutils.pas` | — | main only | not used by corpus builder |

Phase 2 must pick a **canonical** `TextU`/`uTypes` and re-diff; do not assume the
builder copy is a subset of the main app.

---

## 7. Recommended Phase 1 order (from this inventory)

1. **Inventory** — this document (done).
2. **Cut `uMhHTML` ↔ `fMainForm`** — progress sink + no `ShowMessage`/`ShellExecute`/`ProcessMessages` in engine.
3. **Split or `#ifdef` the VCL half of `TextU`** — keep string/IAST/UTF helpers on the engine path.
4. **Drop dead `Dialogs` from `uSort`**; audit remaining soft imports.
5. **Encoding layer** (roadmap item) and `{$MODE Delphi}` directives once the engine unit set is stable under Delphi 7 still.

Golden-file residual (Phase 0 `[~]`) remains blocked on interactive `cb.exe`
capture — independent of this inventory.

---

## 8. How this was produced

```text
# extract uses + BFS from cb.dpr + classify VCL/RTL
# (stdlib Python, no Delphi compile required)
python -c "<uses-graph script against PSRCBuilder/**/*.pas + cb.dpr>"
# VCL call sites via ripgrep: ShowMessage|MessageDlg|ShellExecute|Form1\.|Clipboard
```

Verified on tree at `origin/main` @ `12ac858` (post-PR #123 `cb.cfg` cleanup).

_Dr. Mārcis Gasūns_
