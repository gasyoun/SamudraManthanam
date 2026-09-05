_Created: 25-08-2026 · Last updated: 05-09-2026_

# Sanskrit↔Russian Alignment Spec — Phase 1, Session S3

**Status:** Draft for review · 2026-06-12
**Builds on:** [CONVERTER_SPEC.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/CONVERTER_SPEC.md) (the converter emits the group key
this spec defines) and [LINE_ID_SCHEME.md](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/LINE_ID_SCHEME.md) (frozen).
**Grounded in:** live `corpus.db` measurement of all 119 verse sources (2026-06-12).

---

## 0. The decisive finding: alignment is extraction, not inference

In this corpus, the Sanskrit and its Russian translation are **already interleaved as
sibling divs inside one `citation_block`** (`chapter_block iast` + `chapter_block
translation`). The editors aligned the texts by hand when they built the HTML. Therefore:

> **v1 alignment is a markup-extraction problem, not a sentence-alignment problem.**
> No statistical aligner, no heuristic matching, no embedding similarity is needed.
> The converter reads the pairing straight out of the source structure.

Measured support for this (all 119 verse sources):

| Block shape | Count | Treatment |
|---|---|---|
| both sides present (Sanskrit + Russian siblings) | 78,219 | Tier-1 group, 1:1, markup-certain |
| Russian-only (empty `iast`) | 10,145 | monolingual group (see §3) |
| Sanskrit-only (empty `translation`) | 1 | monolingual group |

This reframes S3's job: **formalize the group model, handle the one-sided and special
cases, define what the reader toggle consumes, and specify a gold standard that *verifies
the extraction is faithful*** — not one that scores a guessing algorithm.

---

## 1. Alignment-group data model

The atomic alignable unit is the **`citation_block`** (a verse or an atomic range), not
the individual pada or sentence. Each block yields one **alignment group**, keyed by the
canonical passage:

```json
{
  "group": "01_rigveda:1.1",      // {work}:{passage} — the group key
  "work": "01_rigveda",
  "passage": "1.1",
  "members": {
    "sa": "01_rigveda:1.1#sa",    // record id, or null
    "ru": "01_rigveda:1.1#ru",    // record id, or null
    "comm": ["01_rigveda:1.1#comm1", "01_rigveda:1.1#comm2"]
  },
  "cardinality": "1:1",           // 1:1 | 1:0 | 0:1  (see §2)
  "alignment": "markup",          // markup | monolingual | none
  "confidence": "certain"         // certain | review
}
```

Group membership comes directly from the converter's segment records (`#sa`, `#ru`,
`#comm{n}`) sharing a `group` key — it is **derived, not stored redundantly**. This spec
defines the *semantics* of the group; the JSONL already carries the parts.

### 1.1 Why ranges stay atomic (the apparent n:m case, resolved)

A range block like `01_rigveda:65.1-2` contains two ॥-delimited Sanskrit verses but **one**
Russian block — the source already merged the Sanskrit to the translation's granularity.
At the group level this is still **1:1** (`#sa` ↔ `#ru`); the two interior verses are
sub-segment structure that v1 does **not** split (scheme §4: ranges are atomic, individual
members not separately addressable). The "n:m problem" flagged in CONVERTER_SPEC §9.1 is
**pre-solved by the source markup** — wherever a translation spans multiple verses, the
editors emitted one range-keyed block. There is no n:m alignment to infer.

---

## 2. Cardinality and the `alignment` field

| `cardinality` | `alignment` | Meaning | Reader behaviour |
|---|---|---|---|
| `1:1` | `markup` | both segments present, paired in source | both panes; toggle works |
| `0:1` | `monolingual` | Russian only (no Sanskrit) | Russian pane only; `lang=sa` shows "no Sanskrit for this passage" |
| `1:0` | `monolingual` | Sanskrit only (no translation) | Sanskrit pane only |

`monolingual` is a **first-class, expected state**, not an error — see §3. Commentary
(`#comm{n}`) is **not** part of the sa/ru cardinality; it attaches to the group via its
own `annotates` link (CONVERTER_SPEC §4) and renders as annotation, not as a translation
pane.

---

## 3. Monolingual content (the real edge cases)

Measured, bounded, and itemized — these are the only departures from clean 1:1:

1. **Whole translation-only verse texts** (Russian, no Sanskrit at all):
   - `buddhacharita-balmont` — 8,852/8,852 blocks Russian-only (Balmont rendered Aśvaghoṣa
     from Edwin Arnold's English, not the Sanskrit).
   - `mify-drind` — 1,172/1,172 Russian-only.
   - These stay `structure: verse` (verse-form Russian) but every group is `0:1`
     monolingual. **Cross-source alignment** to a Sanskrit Buddhacarita is explicitly
     **out of scope for v1** (it is inter-source inference — the thing §0 says we are not
     doing yet). Flag as a future opportunity, do not attempt.
2. **Partially parallel text:** `vedanga_jyotisha` — 119/203 (59%) Russian-only;
   per-block cardinality decides each group independently.
3. **Stray in-text interpolations:** isolated one-sided blocks inside otherwise-parallel
   texts (`ch-up` 1/629, `raghuvamsha` 1/400) — section breaks or editorial insertions.
   Handled automatically by per-block cardinality; no special-casing.

Rule: **cardinality is computed per block from which sides are non-empty.** A whole-text
pattern is just the aggregate of its blocks — no source-level switch needed.

---

## 4. Special intra-group structures

1. **Refrain (`dhruva`)** — Gītagovinda songs carry a repeated refrain: the Sanskrit
   `<b>…॥dhruva॥…</b>` and the Russian `<span class="translation_dhruva">`. Tag the
   refrain segments with `role: "dhruva"` so the reader can render the repeat without
   duplicating it as a separate verse. The refrain stays inside its verse group.
2. **Secondary numbering** — Gītagovinda blocks carry both a global verse key (`gg_1.5`)
   and a song-relative `(1.1)`. The canonical `passage` uses the **global** key (`1.5`);
   the song-relative number is preserved as a display field `alt_ref: "1.1"`, never as the
   ID (scheme: one immutable ID per passage).
3. **Interleaved nav headings** — song/chapter titles (`chapter_1C`, `chapter_title`
   divs) appear *between* verse blocks. They are navigation, **not** alignment members:
   they get `c.N` nav IDs (scheme §4) and are excluded from every group.
4. **`translation_author` spans** — speaker labels ("Дритараштра") inside the Russian
   block are split into an `author` display field, not alignment content (CONVERTER_SPEC
   §3 A-clean step 3).

---

## 5. What the reader `lang` toggle consumes

The reader already has a `lang=ru|sa|both` toggle. It reads the group:

- `both` (default): render `#sa` and `#ru` panes; `#comm` as collapsible annotation.
- `lang=sa`: render `#sa`; for a `0:1` group show a muted "— нет санскрита для этого
  стиха —" placeholder so verse numbering stays continuous.
- `lang=ru`: render `#ru`; symmetric placeholder for `1:0`.

The compare route (`/compare/{work}/{ch}.{v}`) keys on the group `passage`, so multiple
translations of the same verse (the 14 Bhagavadgītā editions, etc.) line up by shared
`{ch}.{v}` across works — alignment *within* a source and comparison *across* sources use
the same passage key.

---

## 6. Gold standard (verifies extraction fidelity)

Because alignment is markup-derived, the gold standard checks that the **converter
extracted the existing pairing faithfully**, not that an algorithm guessed correctly.

- **~25 hand-verified groups** spanning every shape: clean 1:1 (Rigveda, a Bhagavadgītā
  edition), atomic range (Rigveda `65.1-2`), refrain (Gītagovinda song), monolingual `0:1`
  (buddhacharita-balmont), partial-parallel (vedanga_jyotisha), commentary-bearing
  (Rigveda with `comment_1_1`), and an interleaved nav heading.
- For each: assert the group's `members`, `cardinality`, `alignment`, and that `#sa`/`#ru`
  text matches the source block. Stored as `tests/fixtures/alignment_gold.jsonl`.
- This is a **regression oracle**: any converter change that silently drops a side,
  mis-pairs, or splits a range fails the gold set.

---

## 7. Validation gates (CI, in addition to CONVERTER_SPEC §7)

1. **Group completeness:** every verse-source `citation_block` produces exactly one group;
   group count == block count per source.
2. **Cardinality correctness:** the 0:1 / 1:0 counts per source match the measured
   baseline (buddhacharita-balmont 8,852×0:1; rigveda mostly 1:1; etc.) within tolerance;
   deviations itemized, not swallowed.
3. **No phantom pairing:** a `monolingual` group never carries a non-empty opposite
   segment; a `markup` group always has both.
4. **Gold set green:** all ~25 hand-verified groups (§6) pass.
5. **Reader toggle parity:** `lang=sa` + `lang=ru` rendered fragments together cover
   exactly the content of `lang=both` (no segment shown twice or dropped).

---

## 8. Out of scope for v1 (stated, so silence isn't mistaken for coverage)

- **Cross-source alignment** (Balmont's Russian Buddhacarita ↔ a Sanskrit Buddhacarita;
  aligning independent translations to a shared Sanskrit). This is inference, not
  extraction — a separate future initiative.
- **Sub-verse / word alignment** (pada ↔ phrase). Ranges stay atomic; word-level is the
  morphology/treebank track, not this one.
- **Sentence-aligning the monolingual texts** against any external Sanskrit source.

## 9. Open questions → M.G.

1. **Compare-route monolingual rows.** When a `0:1` translation-only text (Balmont)
   appears in a cross-edition compare view, show it with an empty Sanskrit cell, or omit
   it from the Sanskrit-keyed compare entirely? **Recommendation: show with empty cell** —
   it is still a valid Russian witness of the verse.
2. **`vedanga_jyotisha` 59% gap.** Is the missing Sanskrit a digitization gap (recoverable
   later) or genuinely absent in the print edition? Affects whether those groups are
   `monolingual` (expected) or `review` (defect). Needs a source check.

## 10. Acceptance criteria

- [ ] Every verse-source block yields exactly one alignment group with correct
      `cardinality`/`alignment`/`members`.
- [ ] All five validation gates (§7) green; gold set (§6) committed and passing.
- [ ] Reader `lang` toggle renders monolingual groups with continuity placeholders.
- [ ] The two whole translation-only texts produce 100% `0:1` groups, flagged, not errored.
- [ ] Refrain and secondary-numbering structures preserved per §4; nav headings excluded
      from all groups.
- [ ] One text demonstrably queryable + readable across both panes with the toggle, end to
      end (roadmap Phase 1 acceptance, alignment half).

_Dr. Mārcis Gasūns_
