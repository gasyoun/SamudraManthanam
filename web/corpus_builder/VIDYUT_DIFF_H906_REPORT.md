# vidyut second-opinion diff vs DCS gold — agreement report (H906)

_Created: 23-07-2026 · Last updated: 23-07-2026_

The vidyut layer H906's goal asks for, **diffed against the DCS gold**. DCS is
gold; vidyut is the **second opinion, not the arbiter** — this report says where
the two agree and where they diverge, so a reviewer can read the gold with the
analyzer's dissent visible, without ever letting vidyut override DCS. Sibling of
the gold build report
[`SA_MORPHOLOGY_H906_REPORT.md`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SA_MORPHOLOGY_H906_REPORT.md);
model: Opus 4.8 (`claude-opus-4-8[1m]`).

## Method

[`vidyut_diff.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/vidyut_diff.py)
runs [vidyut](https://github.com/ambuda-org/vidyut) 0.4.0's `cheda.Chedaka`
(segment → analyse) on each `seg=sa` group's SLP1 surface and pairs its tokens
against the DCS gold tokens of the same group. The join is **at the group level
on the SLP1 form, as a multiset match**: vidyut and DCS each sandhi-split the
verse independently, so their token boundaries can differ; a form present in
both is compared feature-by-feature, a form in only one side is a **segmentation
divergence**, reported but not scored as a wrong feature. DCS forms/lemmas are
IAST, vidyut works in SLP1, so DCS is transliterated to SLP1
(`indic_transliteration.sanscript`) and both are folded on the anusvara/visarga
surface (`M`→`m`, `H`→`s`) before matching — a measured +14 pp form-match
(35 %→49 %), since DCS keeps the printed surface (`evaM`, `pArTAH`) while vidyut
returns the underlying pada form (`evam`, `pArTAs`). Both sides are mapped into
the **DCS feature vocabulary** (UPOS / Nom-Acc-… / Masc-Fem-Neut / Sing-Dual-Plur)
so the comparison is like-for-like; POS is compared coarsely
(nominal / verbal / indeclinable), since DCS's fine UPOS and vidyut's
subanta/tinanta/avyaya split do not line up 1-to-1.

Emitted behind `nkrya_export.py --vidyut-diff` as `<slug>.vidyut_diff.tsv` (one
row per matched / dcs-only / vidyut-only token, with the two analyses and a
tri-state agree flag per feature). Deterministic — vidyut's segmentation is
fixed for a given input + data pack, and the pairing walks tokens in index
order; two runs are byte-identical. The vidyut data pack (`~/vidyut-data`,
`$VIDYUT_DATA` to override) is a large local-only `download_data` fetch; absent
it, the layer degrades to empty (never guessed), exactly like the DCS sqlite.

## Agreement — Mahābhārata Āraṇyakaparva (the fully-covered gold text)

2033 pairs · **152,196 DCS gold tokens** · 154,394 vidyut tokens.

| Measure | Value | Reading |
|---|---:|---|
| **form-match rate** | **49.2 %** | 74,932 of 152,196 gold tokens have a same-form vidyut token |
| lemma agreement | 69.3 % | over the matched tokens where both carry a lemma |
| POS agreement (coarse) | 69.3 % | nominal / verbal / indeclinable |
| case agreement | 70.5 % | over matched tokens where both carry a case |
| gender agreement | 73.7 % | |
| number agreement | 90.4 % | the most robust feature |

**The headline is the 49 % form-match, and it is a property of vidyut, not a
bug in the diff.** vidyut's unsupervised segmenter chooses different token
boundaries from DCS on roughly half of this compound-heavy epic text — e.g. it
breaks `dyūtajitāḥ` into `dyU·ut·ajitAs` and `dhārtarāṣṭraiḥ` into
`DA·artar·a·azwf·Es`. Feeding it danda-delimited hemistichs instead of the whole
group changed this by <0.1 pp, so it is the analyzer's behaviour on epic Sanskrit,
not an artifact of the input framing. This is exactly why **DCS is the gold and
vidyut only the second opinion**: on this register vidyut is not close enough to
be an arbiter, but on the ~49 % it does segment identically it is a useful
independent check.

## Categorised disagreement sample (matched tokens, Āraṇyakaparva)

**Case** (DCS → vidyut): `Nom→Acc` 2511 · `Nom→Voc` 2022 · `Acc→Nom` 1392 ·
`Cpd→Voc` 913 · `Acc→Voc` 817 · `Gen→Nom` 580. The Nom/Acc/Voc cluster is the
neuter/a-stem syncretism (identical endings), plus vidyut reading compound
members (DCS case `Cpd`) as vocatives.

**Gender**: `Neut→Masc` 5474 · `Masc→Neut` 1713 · `Fem→Masc` 1374 · `Masc→Fem`
882. vidyut systematically over-assigns masculine (the default gender of the
commonest declension) where DCS has neuter/feminine.

**Number**: `Sing→Plur` 1811 · `Plur→Sing` 1613 · `Sing→Dual` 932. Still the
best-agreeing feature at 90 %.

**POS (coarse)**: `VERB→NOUN` 5975 · `CONJ→NOUN` 5574 · `PART→NOUN` 4301 ·
`VERB→ADV` 2756 · `ADV→NOUN` 2063. vidyut's subanta fallback labels an
unanalysable token NOUN, so most POS disagreements are vidyut nominalising a word
DCS reads as a verb or an indeclinable.

**Lemma** (form · DCS · vidyut): `kim·ka·kim`, `mama·mad·mA`, `sA·tad·sA`,
`vAcaH·vAc·vac`, `varzARi·varza·vfz`. Two classes: pronouns, where DCS
lemmatises to a canonical stem (`ka`, `mad`, `tad`) and vidyut keeps the
inflected/gendered stem; and genuine wrong segmentations that drag the lemma with
them (`varza`→`vfz`).

## Coverage note (the other texts)

The diff runs wherever DCS gold exists; coverage of the gold itself is unchanged
from the [gold report](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/SA_MORPHOLOGY_H906_REPORT.md)
(MBh ~99 %, Rāmāyaṇa 62–80 %, Bhagavadgītā absent). The agreement rates above are
reported on Āraṇyakaparva because it is the largest fully-covered gold text; the
`--vidyut-diff` flag produces the same TSV + `vidyut_diff` aggregate block in
`export_report.json` for any source.

## Status

| Piece | Status |
|---|---|
| vidyut layer (`cheda.Chedaka` → DCS vocabulary) | ✅ [`vidyut_diff.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/corpus_builder/vidyut_diff.py) |
| diff vs DCS gold + per-token TSV (`--vidyut-diff`) | ✅ |
| agreement report (match rate + per-feature) | ✅ this file |
| categorised disagreement sample | ✅ above |
| determinism + tests | ✅ (+5 tests) |

DCS stays gold; vidyut is a second opinion for review, never an override.

_Dr. Mārcis Gasūns_
