# Phase 1 Implementation Hand-off — Converter + Alignment

**For:** a fresh implementation session (Sonnet-tier is fine — the design is settled).
**Status:** ready to start · 2026-06-12
**Premise:** all design decisions are frozen in three specs. This document is the build
order. **You do not need the conversation that produced the specs** — read the three specs
and this brief, then implement. Do not redesign; if a spec seems wrong, stop and flag it,
don't silently deviate.

---

## 0. Read first (frozen — do not re-litigate)

1. [LINE_ID_SCHEME.md](LINE_ID_SCHEME.md) — the `{work}:{passage}` ID contract. **FROZEN.**
2. [CONVERTER_SPEC.md](CONVERTER_SPEC.md) — HTML→JSONL converter: schema, 4 parse paths,
   commentary, SLP1/accents, 7 gates.
3. [ALIGNMENT_SPEC.md](ALIGNMENT_SPEC.md) — alignment groups (extraction not inference),
   cardinality, gold oracle, 5 gates.
4. [TAG_CENSUS.md](TAG_CENSUS.md) / `.json` — the measured corpus inventory the specs cite.

The key mental model (from ALIGNMENT_SPEC §0): **one source line = one `citation_block`
bundling Sanskrit + Russian + commentary as sibling divs.** The converter explodes it into
grouped records. Alignment is read straight out of the markup — there is no aligner to write.

---

## 1. Rights guardrail (non-negotiable, applies to all Phase 1 work)

Corpus texts are **not** cleared for open redistribution. Phase 1 produces JSONL that ships
*inside* the app and search service only. **Do not** add a public corpus-download endpoint,
commit a bulk corpus dump to a public artifact, or emit a Zenodo/DOI/TEI export. The JSONL
master lives in the repo the same way the corpus HTML already does — no wider exposure.

---

## 2. Repo facts you'll need

| Thing | Location |
|---|---|
| Corpus source files (148) | `Index/lib/x86_64-win64/Data/*.{html,htm,txt}` |
| Manifest (ordered active sources) | `Index/lib/x86_64-win64/Programdata/data.txt` |
| Per-source metadata (148, has `structure`) | `…/Data/<file>.meta.json` |
| Existing extraction logic to reuse | [web/ingest/parse_html.py](../web/ingest/parse_html.py) (range-title regex, `VEDIC_MAP`, tag stripping) |
| Current HTML→DB ingest (to be rebased onto JSONL) | [web/ingest/ingest.py](../web/ingest/ingest.py) |
| DB build entry point | [build-web-db.ps1](../build-web-db.ps1) → `ingest.py --corpus-path … --db-path …` |
| Tests | `web/tests/` — `pytest -m "not corpus"` hermetic, `pytest -m corpus` real |
| Transliteration (installed) | `indic_transliteration.sanscript` — `IAST`, `SLP1`, `DEVANAGARI` |

**New code goes in `web/corpus_builder/`** (create it). Keep `parse_html.py` helpers; import
and reuse rather than reimplement the range-title regex and accent map.

> ⚠️ **Name collision warning.** A root-level `Corpus_builder/` already exists — it is the
> **Delphi `cb.exe` authoring tool** that *produces* the corpus HTML (different thing). On
> Windows' case-insensitive filesystem a root `corpus_builder/` would collide with it. Put
> the new Python converter under **`web/corpus_builder/`** (note the `web/` prefix) — never
> at the repo root. Your converter *consumes* the HTML that the Delphi tool *produces*; they
> are opposite ends of the pipeline and must stay separate.

Windows/encoding rules (from project CLAUDE.md): every script does
`sys.stdout.reconfigure(encoding='utf-8')`; write files `encoding='utf-8'` **without** BOM;
no PowerShell script-blocks `{}` or subexpressions `$()`.

---

## 3. Build order

Each step ends green before the next starts. Commit per step with `ai-wip:` prefix.

### Step 1 — `web/corpus_builder/html_to_canonical.py` (the converter)

Implements CONVERTER_SPEC. Input: one source file + its meta.json (`structure` routes the
parse path). Output: `web/corpus_builder/jsonl/<slug>.jsonl`.

- Dispatch on `structure`: `verse` → A-clean or A-range (sniff: `citation_block id="N.N"`
  present → clean, else range-title); `dictionary` → B (tab-count sniff per CONVERTER_SPEC
  §3); `prose` → C.
- Emit records per CONVERTER_SPEC §2 schema with `#sa`/`#ru`/`#comm{n}` segment suffixes.
- Mint IDs per LINE_ID_SCHEME (letter-suffix dups, frozen sequences, commentary `…commN`).
- Compute SLP1 for every `#sa` via `sanscript.transliterate(text, IAST, SLP1)`; store
  accented + stripped forms (CONVERTER_SPEC §5).
- Write `web/corpus_builder/conversion_report.json` (CONVERTER_SPEC §8).
- **Gate:** CONVERTER_SPEC §7 gates 1 (ID round-trip stability), 3 (range coverage on the
  53 range files), 4 (uniqueness + dup suffixes), 5 (commentary linkage).

### Step 2 — alignment groups (same converter pass or a thin second pass)

Implements ALIGNMENT_SPEC. The group is derived from segment records sharing a `group` key —
compute `cardinality`/`alignment` per block from which sides are non-empty (§2).

- Tag refrain (`dhruva`), `alt_ref` secondary numbering, exclude nav headings (§4).
- **Gate:** ALIGNMENT_SPEC §7 gates 1–3 (group completeness, cardinality vs baseline, no
  phantom pairing). Baselines to assert: buddhacharita-balmont = 8,852 × `0:1`;
  mify-drind = 1,172 × `0:1`; vedanga_jyotisha ≈ 119/203 `0:1`.

### Step 3 — gold-standard fixtures

Create `web/tests/fixtures/alignment_gold.jsonl` (~25 hand-verified groups, ALIGNMENT_SPEC
§6) and the matching converter-output fixtures for CONVERTER_SPEC gates. Add
`web/tests/test_converter.py` + `test_alignment.py` asserting the gates.

### Step 4 — rebase ingest onto JSONL

Switch `ingest.py` (or a new `ingest_jsonl.py` invoked by `build-web-db.ps1`) to read
`corpus_builder/jsonl/*.jsonl` instead of parsing HTML directly. Add the `canonical_id`
column + unique index on `corpus_lines` (LINE_ID_SCHEME §6); carry IDs from JSONL.

- **Gate:** CONVERTER_SPEC §7 gate 6 + ALIGNMENT_SPEC §7 gate 4/5 — **golden-query suite
  returns identical hits** from a JSONL-built DB vs the current HTML-built DB. This is the
  no-regression contract; `web/tests/test_golden_queries.py` already exists — run it both
  ways and diff.

### Step 5 — HTML round-trip (roadmap Phase 1 acceptance)

A renderer reproduces the reader HTML from JSONL; diff against current reader output for a
sample (CONVERTER_SPEC §7 gate 2). Byte-identical is not required — **zero search-relevant
divergence** is.

---

## 4. Definition of done

- [ ] All 148 sources convert; every non-empty source line → ≥ 1 JSONL record; no silent drops.
- [ ] Every CONVERTER_SPEC §7 gate (7) and ALIGNMENT_SPEC §7 gate (5) green in CI.
- [ ] `corpus.db` builds from JSONL; `pytest -m "not corpus"` and the golden-query suite
      pass with **identical** results to the pre-change HTML-built DB.
- [ ] LINE_ID_SCHEME §9 + CONVERTER_SPEC §10 + ALIGNMENT_SPEC §10 acceptance lists satisfied.
- [ ] `.ai_state.md` updated; conversion report committed.

## 5. Decided vs. open

**Decided (build to these — do not ask):** all of LINE_ID_SCHEME §8 (MBh book-num kept;
dict `e{n}` minted now; commentary addressable). Structure classes assigned on all 148
meta.json. Alignment is extraction, ranges atomic, monolingual is a first-class state.

**Open but NON-blocking (implement the recommended default, leave a TODO, surface at review):**
- ALIGNMENT_SPEC §9.1 — compare-route monolingual rows → default: show with empty Sanskrit cell.
- ALIGNMENT_SPEC §9.2 — `vedanga_jyotisha` 59% gap: treat as `monolingual` (expected) for now;
  flag in the conversion report so a later source check can reclassify as defect if needed.
- CONVERTER_SPEC §9.2 — non-tab dictionary `forms`: single-script now, backfill later.

**Out of scope (do not build):** cross-source alignment, sub-verse/word alignment, any
public corpus export, TEI. (ALIGNMENT_SPEC §8.)

## 6. Unrelated finding parked for M.G. (not part of this hand-off)

4 dharmaśāstra texts (`naradasmriti`, `vishnu-smriti`, `yajnavalkyasmriti`,
`yajnavalkyasmriti_add`) exist in `Data/` but are absent from `data.txt` — so they are NOT
in the 148 and NOT in scope here. If M.G. re-adds them to `data.txt`, re-run the census +
structure backfill, then they flow through this same pipeline. Until then, ignore.
