# The shared inline `<w><ana/>` scheme — RU + SA (H905/H906)

_Created: 25-07-2026 · Last updated: 25-07-2026_

The last open item of [H906](https://github.com/gasyoun/Uprava/blob/main/handoffs/H906-Opus_SamudraManthanam_nkrya-sa-morphology-dcs-vidyut_14.07.26.md),
and the one H905 was waiting on: fold both morphology layers **into** the
para-XML as НКРЯ `<w><ana lex= gr=/>` per token, in a single scheme both sides
share. Model: Opus 5 (`claude-opus-5[1m]`). Siblings:
[`RU_MORPHOLOGY_H905_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RU_MORPHOLOGY_H905_REPORT.md),
[`SA_MORPHOLOGY_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SA_MORPHOLOGY_H906_REPORT.md),
[`RAMAYANA_VERSE_MAP_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/RAMAYANA_VERSE_MAP_H906_REPORT.md).

Both handoffs deliberately shipped a TSV sidecar and deferred this fold so that
neither side would fix the attribute scheme before the other agreed to it. H905
called the remaining step "small, mechanical". **It is not** — the Sanskrit side
turned out to carry a real alignment problem, and the headline of this report is
how far that problem can honestly be pushed and where it stops.

## The scheme

```xml
<se lang="ru" ana="opencorpora">
  <w><ana lex="преданный" gr="ADJF,accs,sing" gramset="opencorpora"/>Преданного</w> …
</se>
<se lang="san" script="iast" slp1="…" ana="dcs-ud">
  <w><ana lex="tapas"     gr="NOUN,Cpd"  gramset="dcs-ud"/>
     <ana lex="svādhyāya" gr="NOUN,Cpd"  gramset="dcs-ud"/>
     <ana lex="nirata"    gr="VERB,Acc,Masc,Sing" gramset="dcs-ud"/>tapaḥsvādhyāyanirataṃ</w> …
</se>
```

Three rules, identical on both sides:

1. **The annotated unit is the surface word.** The `<se>` text is never
   rewritten, re-segmented or sandhi-resolved; concatenating the `<w>` content
   reproduces the segment byte-for-byte (test-enforced). The edition's text stays
   authoritative.
2. **`lex` + `gr` + `gramset`.** `gramset` names the tagset `gr` is written in —
   `opencorpora` (pymorphy3) for Russian, `dcs-ud` (DCS gold) for Sanskrit.
   OpenCorpora and DCS/UD do **not** map onto one another 1-to-1, so a single
   merged tagset would have silently corrupted the grammar. One element shape,
   two honest tagsets — that is what "shared" means here.
3. **No analysis ⇒ bare text.** A word without an analysis is emitted as plain
   text, never as a guessed `<ana>`.

A word may carry **several** `<ana>` children — the RNC construct for ambiguity,
reused here for the sandhi-split compound: `tapaḥsvādhyāyanirataṃ` is one surface
word and three DCS tokens.

## Why the two sides are not symmetric

The Russian layer tokenizes its own surface, so `<w>` wrapping is 1-to-1 by
construction and coverage is total. The Sanskrit gold is **sandhi-split**, and
measurement showed the gap is structural, not cosmetic:

- DCS holds **more tokens than surface words in ~89 %** of Yuddhakāṇḍa verses
  (`prītisamāyukto` → `prīti` + `samāyuktaḥ`; `sumahad` → `su` + `mahat`).
- The gold does not re-concatenate to the surface — **sandhi is undone**, so the
  characters differ, not merely the boundaries (surface `manasāpi`, gold
  `manasā` + `api`).
- DCS carries speaker tags (`janamejaya uvāca`) absent from our text, and our MBh
  groups are verse **ranges** spanning several DCS sentences.

So the Sanskrit side attaches gold through a sandhi-tolerant matcher
([`inline_ana.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/inline_ana.py))
that must account for the verse **end-to-end or not at all**. A partial cover is
rejected outright, because it would attach a word's morphology to its neighbour.
This follows the rule
[`align_sanskrit.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/align_sanskrit.py)
already sets in this repo: where the join cannot be proven, fall back and report
it — never fabricate.

The fold collapses exactly the alternations external sandhi introduces at a seam:
vowel length; the visarga/anusvara surface (`ḥ`→`s`, `ṃ`→`m`, mirroring
`vidyut_diff._join_key`); word-final `-o` ← `-aḥ`; stop voicing/place and nasal
neutralization applied *globally* (the seam is invisible inside `vāgvidāṃ` =
`vāc` + `vidām`); and vowel coalescence across the seam. Each rule was added only
after it showed up as the dominant measured failure — 6.3 % → 8.1 % → **15.5 %**.

## Coverage (real sweep)

| Source | verses with gold | inline-annotated | % |
|---|---:|---:|---:|
| 06_ramayana-yuddhakanda | 4435 | 1667 | **37.6 %** |
| 07_ramayana-uttarakanda | 2688 | 939 | **34.9 %** |
| 03_mahabharata-aranyakaparva | 2032 | 30 | 1.5 % |
| 01_ramayana-balakanda | 1812 | 23 | 1.3 % |
| 02_ramayana-ayodhyakanda | 2668 | 19 | 0.7 % |
| 03_ramayana-aranyakanda | 1770 | 4 | 0.2 % |
| 05_ramayana-sundarakanda | 1943 | 3 | 0.2 % |
| **total** | **17,348** | **2,685** | **15.5 %** |

Russian: **100 %** of pairs (2268/2268 on Bālakāṇḍa) wherever pymorphy3 is
installed.

**The 25× spread between the GRETIL kāṇḍas and the rest is the finding.** The
GRETIL editions are printed analytically — compounds spaced close to how DCS
splits them — while the bilingual editions write long unresolved compounds
(`tapaḥsvādhyāyanirataṃ`). The matcher is not weaker on those texts; their
orthography is simply further from DCS's segmentation. MBh adds its own
structural blockers (speaker tags, verse-range groups) on top.

## Precision

Coverage was never allowed to buy errors. On the 18,228 Yuddhakāṇḍa words the
matcher did annotate, an automatic gate compared each word's initial consonant
with that of its first attached gold token: **0 disagreements (0.00 %)**.
Hand-read samples confirm the decompositions and lemmas —
`prītisamāyukto` → `prīti` + `samāyuktaḥ` [`prīti` + `samāyuj`],
`manasāpi` → `manasā` + `api`, `dharaṇītale` → `dharaṇī` + `tale`,
`abravīt` → `brū`. High precision, deliberately traded against recall.

## Validation

- Two `--inline-ana` runs of Bālakāṇḍa are **byte-identical**; the XML parses
  (38,412 `<w>`, 38,523 `<ana>`).
- Every `<ana>` is empty and carries `lex`/`gr`/`gramset`; segment text round-trips.
- +6 tests (23 pass, 2 vidyut-data-pack-gated skips).

## What remains

- **SA inline coverage on the bilingual editions is ~1 %.** The sidecar
  `sa_morph.tsv` still carries **100 %** of the gold, so nothing is lost — but
  the *inline* layer is thin exactly where the parallel corpus is. Raising it
  needs a real sandhi splitter over the surface, not more fold rules; the
  in-repo vidyut segmenter is the obvious candidate and its 49 % agreement with
  DCS ([`VIDYUT_DIFF_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/VIDYUT_DIFF_H906_REPORT.md))
  sets expectations.
- **The GRETIL kāṇḍas have the best alignment (37 %) but produce no para-XML at
  all**, because they are untranslated and the XML is the *parallel* artifact. A
  monolingual SA XML would surface that annotation; out of scope here.
- `gr` strings are each tagset's native short forms. If НКРЯ requires one
  controlled vocabulary at ingest, that is a mapping layer on top — deliberately
  not invented here without their spec.

_Dr. Mārcis Gasūns_
