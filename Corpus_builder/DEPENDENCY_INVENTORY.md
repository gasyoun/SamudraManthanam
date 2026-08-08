# Corpus Builder — dependency inventory (Phase 1)

_Created: 01-08-2026 · Last updated: 08-08-2026_

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
| `TextU` | `PSRCBuilder/dcu/TextU.pas` | ~1360 | string/UTF-8/IAST helpers (VCL-free since H2370) |
| `TextUVCL` | `PSRCBuilder/dcu/TextUVCL.pas` | ~100 | VCL list/clipboard/RichEdit helpers (H2370; not on `cb.dpr` BFS until a form `uses` it) |
| `uTypes` | `PSRCBuilder/dcu/uTypes.pas` | 79 | shared array/record aliases |
| `myutils` | `PSRCBuilder/dcu/myutils.pas` | 227 | `PutFile1ToFile2`, `MergeFiles` |
| `mytypes` | `PSRCBuilder/dcu/mytypes.pas` | 12 | basic type aliases for `myutils` |
| `CalcSimU` | `PSRCBuilder/dcu/CalcSimU.pas` | 326 | calculator-sim helpers (via `TextU`) |
| `StatProcs` | `PSRCBuilder/dcu/statprocs.pas` | 605 | stats/arithmetic (via `TextU`) |
| `uSort` | `PSRCBuilder/dcu/uSort.pas` | 176 | sorting (via `StatProcs`); no `Dialogs` since H2370 |
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
| `Forms` | `cb`, `fMainForm`, `fCheckDialog` |
| `Dialogs` | `fMainForm`, `fCheckDialog` |
| `Controls` | `fMainForm`, `fCheckDialog` |
| `Graphics` | `fMainForm`, `fCheckDialog` |
| `StdCtrls` | `fMainForm`, `fCheckDialog`, **`TextUVCL`** |
| `Buttons` | `fCheckDialog` |
| `ExtCtrls` | `fCheckDialog` |
| `Menus` | `fMainForm` |
| `ComCtrls` | `fMainForm`, **`TextUVCL`** |
| `CheckLst` | **`TextUVCL`** |
| `ClipBrd` | `fMainForm`, **`TextUVCL`** |
| `Messages` | `fMainForm` |
| `Windows` | `fMainForm`, `fCheckDialog`, **`uMhHTML`**, **`TextUVCL`** |
| `ShellApi` | `fMainForm` |

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

## 3. Engine was **not** GUI-free — closed by H1485 (04-08-2026)

> **Status update, 04-08-2026 ([H1485](https://github.com/gasyoun/Uprava/blob/main/handoffs/H1485-Opus_SamudraManthanam_corpus-builder-engine-gui-decouple_22.07.26.md),
> Opus 5 `claude-opus-5[1m]`).** Every `uMhHTML.pas` row in the table below is
> **gone**; the engine's implementation `uses` is now `SysUtils, textu, windows,
> MyUtils` (§3a). The `fCheckDialog.pas` and `TextU.pas` rows are **untouched** —
> they belong to the separate Phase 1 items 3–5 in §7. The table is kept as the
> audit baseline the refactor was checked against, not as a description of the
> current tree.

The roadmap / CLAUDE.md claim that
[`uMhHTML.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/uMhHTML.pas)
«почти не зависит от GUI» was **aspirational, not current fact**. Concrete VCL
call sites inside the builder engine, measured at `12ac858`:

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

Items 1–4 are **done** (H1485); item 5 is **done** (H2370) — VCL helpers live in
[`TextUVCL.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextUVCL.pas);
`TextU` is VCL-free.

---

## 3a. Engine after H1485 — the seam that replaced those call sites

`uMhHTML.pas` implementation `uses` went from

```pascal
uses SysUtils, dialogs, textu , fMainForm, Forms, controls, windows, ShellApi, MyUtils;
```

to

```pascal
uses SysUtils, textu, windows, MyUtils;
```

`windows` is retained solely for `GlobalMemoryStatus`/`TMemoryStatus` (WinAPI, not
VCL). The reverse edge `uMhHTML → fMainForm` in the §1 graph is **cut**.

Three nil-safe sink types are declared next to `TMhHTMLBuilder`; the host assigns
them after `Create` and a headless caller simply leaves them `nil`:

| Sink | Signature | Replaces | Nil behaviour |
|---|---|---|---|
| `TProgressSink` | `procedure (APanel:integer; const AText:string) of object` | `Form1.StatusBar1.Panels[n].Text` + `Refresh` + `Application.ProcessMessages` | no-op |
| `TConfirmSink` | `function (const AText:string):boolean of object` | `MessageDlg(…,mbOKCancel,…) = mrOk` | returns `True` (batch proceeds with defaults) |
| `TErrorSink` | `procedure (const AText:string) of object` | `ShowMessage(…)` ×3 | none needed — `ReportError` always writes `ErrList` first |

Wrappers inside the engine: `Progress` / `Confirm` / `ReportError`. `ReportError`
appends to `ErrList` **unconditionally**, so the `CLAUDE.md` rule «`ErrList` is the
sole error channel; do not `ShowMessage` inside builder logic» now holds by
construction rather than by convention — the sink is an optional mirror on top,
not an alternative channel.

The error file is no longer opened by the engine. `Execute` still writes
`Err.txt`; the host asks `HasErrors` / `ErrFileFullPath` and does its own
`ShellExecute`, at all three `TMhHTMLBuilder` construction sites in `fMainForm.pas`
(single-book, book-list loop, many-books loop) — with the ordering relative to
`RenameErrFile` preserved.

**Two deliberate behaviour deltas**, both host-side:

1. The engine previously called `StatusBar1.Refresh` at some sites and
   `Application.ProcessMessages` at others. `TForm1.BuilderProgress` now does
   **both** everywhere — a strict superset of the old responsiveness, at the cost
   of a message pump in the comments/translation load loops that did not have one.
2. `ShowMessage` on a load error was modal and blocked batch processing (the exact
   thing `CLAUDE.md` forbids). `TForm1.BuilderError` appends to `Memo1` instead, so
   a multi-book run no longer stops on the first malformed line. The error still
   reaches `ErrList` → `Err.txt`, and `HasErrors` still surfaces it.

   **Second-order effect, intended:** the old `ShowMessage` sites did *not* touch
   `ErrList`, so a load error that produced no other complaint left `Err.txt`
   empty and nothing opened afterwards. `ReportError` writes `ErrList`
   unconditionally, so those same lines now land in `Err.txt` and can make
   `HasErrors` true — i.e. the error file will auto-open in cases where it
   previously stayed shut. That is the point of making `ErrList` the sole channel;
   it is a visible change in what a run reports, not just where.

Because progress now pumps messages inside the comments/translation load loops
(delta 1), the build menu handlers become re-enterable mid-build and have no
re-entrancy guard. Pre-existing in `OutPutText`/`LoadSanskrit`, which already
pumped; newly reachable in the other three loops.

### Verification (no compiler)

There is no Delphi 7 machine in this session, so **`dcc32` was not run** — the
same standing caveat as the `cb.cfg` cleanup (PR #123). What was checked
source-level:

- `grep` for `ShowMessage|MessageDlg|ShellExecute|Application\.|Form1\.|SW_SHOW|mrOk|mtConfirm`
  over `uMhHTML.pas` returns only **comment** lines (2 pre-existing commented-out
  `ShowMessage`s at 376/1809, one commented `Form1.OpenDialog1` at 1284, and the
  new comment naming `fMainForm`).
- Every identifier the engine still uses resolves through the reduced `uses`:
  `TStringList`/`TIniFile` (interface `classes`, `INIFiles`), `GlobalMemoryStatus`
  (`windows`), `AnsiToUTF8`/`UTF8ToAnsi` (`SysUtils`), `PutFile1ToFile2` (`MyUtils`).
  Delphi does not re-export a used unit's own `uses`, so `TextU`'s VCL imports
  never leaked identifiers into `uMhHTML` and their removal here changes nothing.
- `MessageDlg`/`mtConfirmation`/`mbOKCancel`/`mrOk` are reachable in `fMainForm`
  via its interface `uses Dialogs, Controls`; `ShellExecute`/`SW_SHOWNORMAL` via
  the implementation `uses shellapi` already present for three other call sites.
- CP-1251 encoding and LF line endings preserved (patch applied via an
  encoding-explicit script, not an editor).
- An independent adversarial audit (Opus 5 `claude-opus-5[1m]`) re-derived the
  whole thing from `git show HEAD:` — 415-identifier token census over the reduced
  `uses`, declaration↔implementation signature match, `except`-block control flow
  (`break` present at both translation sites, absent at the comments site, as
  before), panel indices (all 5, including the single `Panels[1]`), `Path` set
  before the `Confirm` early exit, `ErrFileName` an *interface* const so the new
  body at the top of the implementation still sees it. **CONFIRMED**, no
  build-breaking defect. It found the two doc errors fixed above: the changelog
  said ×6 status-bar sites (there are 5) and this section did not spell out the
  auto-open second-order effect.
- `ShellExecute`'s window handle changed from `Application.Handle` to the form's
  `Handle` — both valid `HWND`s, no user-visible difference.

**Human residual:** a `dcc32` build on Delphi 7, plus one interactive run of
`cb.exe` to confirm the status bar still ticks and `Err.txt` still opens.

---

## 4. Dead / soft VCL imports — **cleared H2370 (07-08-2026)**

| Unit | Import | Outcome |
|---|---|---|
| `uSort.pas` | `Dialogs` | **Removed** — no `ShowMessage` / `MessageDlg` / `Dialogs.` in body |
| `TextU.pas` | `CheckLst`, `StdCtrls`, `ComCTRLS` | **Moved** to [`TextUVCL.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextUVCL.pas) with `CBListToList` / `ListBoxToStringList` / `Search_And_Replace` |
| `TextU.pas` | `clipbrd` / `Windows` (clipboard) | **Moved** to `TextUVCL` with `CopyStringToClipboard` |

`TextU` interface `uses` is now `uTypes, classes` only; implementation drops
`Windows` and `clipbrd`. No remaining `Dialogs` in any `dcu/*.pas` unit.

Static proof (no Delphi/FPC on this machine): see
[`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md).

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
| `uSort` | `Math`, `uTypes`, `ArtMath` | portable after H2370 (dead `Dialogs` gone) |
| `TextU` | `SysUtils`, `Classes`, `Math`, `DateUtils`, `CalcSimU`, `StatProcs`, `Variants`, `uTypes` | VCL-free after H2370 |

**Not yet portable:** `fMainForm`, `fCheckDialog`, `TextUVCL` (VCL by design).

`uMhHTML` moved out of that list on 04-08-2026 (H1485): VCL-free aside from
`windows`/`GlobalMemoryStatus`. TextU VCL half no longer blocks the engine path.

---

## 6. Overlap with main app `Units/` (Phase 2)

**H2429 (08-08-2026) closed the canonical pick** — full table + API lists:
[`docs/H2429_DCU_UNITS_CANONICAL_DIFF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2429_DCU_UNITS_CANONICAL_DIFF.md).

| File | Builder | Main app [`Units/`](https://github.com/gasyoun/SamudraManthanam/tree/main/Units) | Status after H2429 |
|---|---|---|---|
| `TextU.pas` | 35 658 B (VCL-free) + `TextUVCL` 2 381 B | **`textu.pas` 11 651 B** is Index/FPC helpers (name collision); true twin is **`_textu.pas` 33 006 B** (stale, still VCL) | **Split:** builder `TextU` canonical for `cb`; Index `textu` stays separate |
| `uTypes.pas` | 1 735 B (`TWideStringArr` extra) | 1 697 B | **Builder master** (sole type delta) |
| `ArtMath`, `CalcSimU`, `mytypes`, `myutils`, `statprocs`, `uSort` | builder only | — | no main-app twin under those names |
| `UpdateChecker.pas`, `_Math.pas`, `_textu.pas`, `_winutils.pas` | — | main only | `_textu` = non-canonical twin; not used by corpus builder |

Do **not** assume builder TextU is a subset of Index `Units/textu` — it is not.
Shared-path work → H2430; never drop builder-only APIs used by `uMhHTML`.

---

## 7. Recommended Phase 1 order (from this inventory)

1. **Inventory** — this document (done, H2064).
2. **Cut `uMhHTML` ↔ `fMainForm`** — progress sink + no `ShowMessage`/`ShellExecute`/`ProcessMessages` in engine. **Done 04-08-2026 (H1485)** — see §3a.
3. **Split the VCL half of `TextU`** — keep string/IAST/UTF helpers on the engine path. **Done 07-08-2026 (H2370)** — helpers in `TextUVCL.pas`.
4. **Drop dead `Dialogs` from `uSort`**; audit remaining soft imports. **Done 07-08-2026 (H2370)**.
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
