# H2429 — dcu vs Units: sizes, API deltas, canonical pick

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Handoff:** [H2429 (Grok 4.5) — Corpus_builder Phase 2: diff dcu vs Units pick canonical](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2429-Grok_SamudraManthanam_corpus-builder-p2-dcu-units-diff-canonical_08.08.26.md)  
**Model:** Grok 4.5 (`grok-4.5`)  
**Scope:** written comparison only — no delete of builder-only APIs, no OtherUnitFiles merge (that is [H2430](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2430-Grok_SamudraManthanam_corpus-builder-p2-shared-otherunitfiles_08.08.26.md)).

---

## 1. Inventory (bytes / lines)

| Path | Role | Bytes | Lines |
|---|---|---:|---:|
| [`Corpus_builder/PSRCBuilder/dcu/TextU.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextU.pas) | Builder string/IAST/UTF helpers (VCL-free since H2370) | 35 658 | 1 362 |
| [`Corpus_builder/PSRCBuilder/dcu/TextUVCL.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/TextUVCL.pas) | VCL list/clipboard/RichEdit helpers split from TextU | 2 381 | 100 |
| [`Corpus_builder/PSRCBuilder/dcu/uTypes.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/dcu/uTypes.pas) | Builder array/record aliases | 1 735 | 79 |
| [`Units/_textu.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/_textu.pas) | **True historical twin** of builder TextU (unit `_textu`, still VCL in `uses`) | 33 006 | 1 299 |
| [`Units/textu.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/textu.pas) | **Index/Lazarus search helpers** — name collision, **not** the same module | 11 651 | 367 |
| [`Units/uTypes.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Units/uTypes.pas) | Index/app twin of builder uTypes | 1 697 | 78 |

**Size note from the handoff (“builder TextU ~3× main Units copy”):** that ratio holds for **`dcu/TextU` vs `Units/textu.pas`** (35 658 / 11 651 ≈ **3.06**). That comparison is a **name collision**, not a fork of one implementation. Against the real twin `Units/_textu.pas`, builder TextU is only ~1.08× larger (and post-H2370 parks ~2.4 KB of former VCL surface in `TextUVCL`).

### dcu units with no Units twin

| File | Bytes | Lines | Note |
|---|---:|---:|---|
| `ArtMath.pas` | 17 439 | 679 | builder-only math |
| `CalcSimU.pas` | 8 588 | 326 | via TextU |
| `statprocs.pas` | 16 495 | 605 | via TextU |
| `myutils.pas` | 5 760 | 227 | engine (`uMhHTML`) |
| `uSort.pas` | 4 501 | 177 | H2370 Dialogs cleanup |
| `mytypes.pas` | 236 | 12 | tiny aliases |
| `TextUVCL.pas` | 2 381 | 100 | H2370 split |

These stay under `dcu/` until a later shared-units design; H2429 does not rehome them.

---

## 2. Divergence table — TextU lineage

### 2.1 Three files, two products

| Pair | Relationship |
|---|---|
| `dcu/TextU` ↔ `Units/_textu` | **Same lineage** (Delphi-era shared utilities). Interface overlap high. |
| `dcu/TextU` ↔ `Units/textu` | **Different product.** Unit names collide case-insensitively (`TextU` / `textu`). Only **3** shared function names. |
| `Units/_textu` ↔ `Units/textu` | Coexist in `Units/`; underscore file is legacy copy, lowercase is live Index FPC unit. |

### 2.2 API counts (interface `function`/`procedure` names)

| Pair | Builder / left | Right | Shared | Only left | Only right |
|---|---:|---:|---:|---:|---:|
| `dcu/TextU` vs `Units/textu` (Index) | 76 | 15 | **3** | 73 | 12 |
| `dcu/TextU` vs `Units/_textu` (true twin) | 76 | 70 | **68** | 8 | 2 |

**Shared with Index `textu` only:** `CutNextFromEnd`, `CutNextUseDelimiterNoTrim`, `GetNilsBefore`.

**Only in Index `Units/textu` (examples):** Russian search morphology (`Sklonenie_*`, `GetCountSuffix`), HTML strip (`RemoveHTMLTags` / `DelHTMLTagsFromString`), `IsUtf8CharInLimits` (lazutf8), `LastPos`, `GetIDStr`, `CopyStringsToClipboard`.

**Only in builder vs true twin `_textu` (8):**  
`BoolArrToPackedByteArr`, `BoolArrToPackedStr`, `PackedByteArrToBoolArr`, `PackedStrToBoolArr`, `GetStrCoreCoef`, `IsRussianLowerCase`, `IsRussianUpperCase`, `StrToBytesArr`.

**Only in `_textu` vs builder TextU (2):**  
`CBListToList`, `ListBoxToStringList` — still inlined in `_textu`; on the builder side these live in **`TextUVCL`** (H2370), not in pure `TextU`.

### 2.3 Platform / encoding posture

| Axis | `dcu/TextU` | `Units/_textu` | `Units/textu` (Index) |
|---|---|---|---|
| Compiler mode | Delphi-7 style (no `{$mode}`) | `{$MODE Delphi}` | `{$mode objfpc}{$H+}` |
| Interface `uses` | `uTypes`, `classes` | `uTypes`, `classes`, **CheckLst/StdCtrls/ComCtrls** | `Classes`, `SysUtils`, **lazutf8**, clipbrd |
| Encoding | manual WideString/UTF helpers; CP-1251 char-set residue (H2370 FPC note) | same family | **lazutf8**-native |
| VCL | stripped to `TextUVCL` | still in unit | clipboard only |

### 2.4 Builder consumers that **must** keep builder-only APIs

Static name use of interface symbols (false positives from local params filtered for “must keep”):

| Consumer | Builder-only TextU APIs in live use |
|---|---|
| [`uMhHTML.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/uMhHTML.pas) | `CutNextUseDelimiter`, `UTF8CutNextUseDelimiterNoTrim`, `WSCutNextUseDelimiterNoTrim`, `IntToStrNils`, `ArabicToRoman`, `IsRussianUpperCase` (also references `WSExtractDigits` in commented/legacy paths) |
| [`fMainForm.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fMainForm.pas) | `CutNext`, `CutNextUseDelimiter`, `UTF8CutNextUseDelimiterNoTrim`, `IntToStrNils`, `AddBracketsToNums` |
| [`fCheckDialog.pas`](https://github.com/gasyoun/SamudraManthanam/blob/main/Corpus_builder/PSRCBuilder/fCheckDialog.pas) | `CutNextUseDelimiter` |

**Fail condition of H2429:** merging a “use only Index `Units/textu`” ruling would **delete** these builder-only APIs and break `uMhHTML` / forms. That path is **rejected**.

---

## 3. Divergence table — uTypes

| Axis | Builder `dcu/uTypes` | `Units/uTypes` |
|---|---|---|
| Bytes / lines | 1 735 / 79 | 1 697 / 78 |
| Procedures | `CopyIntArr`, `Copy2DIntArr`, `Copy2DDoubleArr` | same |
| Shared types | 17 aliases (`TIntArr`, `TStringArr`, …) | same 17 |
| **Only builder** | **`TWideStringArr = array of widestring`** | — |
| Implementation | byte-identical copy loops + `DecimalSeparator`/`DateSeparator` init | same |

`fMainForm` uses `TWideStringArr`. Canonical merge must **carry that type** (add to Units then share, or keep builder file as master until H2430).

---

## 4. Canonical ruling

### Verdict: **split** (with per-module winners)

| Module | Canonical | Why |
|---|---|---|
| **TextU (builder engine path)** | **`Corpus_builder/PSRCBuilder/dcu/TextU.pas` (+ `TextUVCL.pas`)** | Live consumer of `uMhHTML` / forms; VCL already split (H2370); supersedes stale `Units/_textu`. |
| **TextU (Index search path)** | **`Units/textu.pas`** | Different API (FPC + lazutf8 + RU morphology). **Not** a twin of builder TextU; do not replace either with the other. |
| **Legacy twin** | **`Units/_textu.pas` = non-canonical** | Historical fork; still VCL-coupled; lagging builder+TextUVCL. Treat as archive candidate after H2430, not as merge source. |
| **uTypes** | **Builder `dcu/uTypes.pas` as master** for the next shared copy | Sole delta is `TWideStringArr`; procedures already identical. H2430 may promote this file (or Units after adding the type) into one `OtherUnitFiles` path. |
| **Other dcu modules** | **builder-local until designed** | No Units twins; out of scope for “pick TextU/uTypes canonical”. |

### What “one source of utilities” (ARCHITECTURE §2.1.6 / ROADMAP Phase 2) means after this ruling

1. **Do not** point the corpus builder at Index `Units/textu.pas` as a drop-in replacement.
2. **Do** treat builder `TextU` + `TextUVCL` as the string-util stack for `cb` until a deliberate FPC port expands a shared module **without dropping** the consumer list in §2.4.
3. **Do** plan H2430 `OtherUnitFiles` around: shared **uTypes** (builder master) + either (a) keep builder TextU in-tree for `cb`, or (b) lift builder TextU into a shared path under a **non-colliding unit name** if Index `textu` stays as-is.
4. **Never** delete builder-only APIs used by `uMhHTML` as part of a “dedupe by Units/textu” shortcut.

---

## 5. Method / reproduce

Interface symbols extracted with a stdlib scan (unit interface section: `function`/`procedure` names, `type` aliases). Sizes from filesystem. Consumer use = word-boundary search of builder interface names in `uMhHTML` / `fMainForm` / `fCheckDialog`.

No Delphi `dcc32` / full FPC `cb` rebuild in this pass (doc-first acceptance). Prior FPC notes for portable stack remain under [`docs/H2370_DEAD_VCL_STATIC_PROOF.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/H2370_DEAD_VCL_STATIC_PROOF.md).

---

## 6. Feeds

- **H2430** — shared directory / `OtherUnitFiles` (must honour split + builder TextU master).
- Corpus_builder ROADMAP Phase 2 first checkbox (this report).

_Dr. Mārcis Gasūns_
