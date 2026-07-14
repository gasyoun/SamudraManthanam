"""Multi-candidate lemma disambiguation — ported from ВКР §3.3.3.

Implements the 9 suffix->number rules and the attested-elsewhere /
plural-singular merge steps that do NOT require deeppavlov's case tagger.
The deeppavlov-tier residual (~20% of multi-candidate cases in the thesis)
is intentionally not ported — see SPEC.md §2.5. Those cases surface here as
`needs_review` entries with `lemma_candidates` populated, never a guess.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .stemmer import Detection


def _ends_plural(lemma: str) -> bool:
    return lemma.endswith(("и", "ы"))


_STEM_CONSONANTS = set("слрнзфвпдмтб")


def refine_by_suffix_rules(surface_lower: str, candidates: set[str]) -> set[str]:
    """The 9 rules (thesis §3.3.3). Each rule narrows `candidates` toward a
    required plural/singular ending; a rule that would empty the set is
    skipped (order-independent per the thesis's own note)."""
    s = surface_lower
    constraints: list[bool | None] = []

    if s.endswith("в"):
        constraints.append(True)  # rule 1
    if s.endswith("ой"):
        constraints.append(False)  # rule 2
    if s.endswith("ми"):
        constraints.append(True)  # rule 3
    if s.endswith("х"):
        constraints.append(True)  # rule 4
    if s.endswith(("у", "е", "ю", "о")):
        constraints.append(False)  # rule 5
    if s.endswith(("ам", "ям")):
        constraints.append(True)  # rule 6
    if s.endswith(("ом", "ем")):
        constraints.append(False)  # rule 7

    refined = set(candidates)
    for want_plural in constraints:
        narrowed = {c for c in refined if _ends_plural(c) == want_plural}
        if narrowed:
            refined = narrowed

    # rules 8/9: preceded-by-consonant vowel ending constrains -и specifically
    if len(s) >= 2 and s[-2] in _STEM_CONSONANTS and s[-1] not in "йх":
        want_i = s[-1] == "и"
        narrowed = {c for c in refined if c.endswith("и") == want_i}
        if narrowed:
            refined = narrowed

    return refined


@dataclass
class ResolvedDetection:
    surface: str
    candidates: set[str]
    capitalization_rescued: bool


def resolve(detections: list[Detection]) -> list[ResolvedDetection]:
    stage1 = [
        ResolvedDetection(
            surface=d.surface,
            candidates=refine_by_suffix_rules(d.surface.lower(), d.lemma_candidates),
            capitalization_rescued=d.capitalization_rescued,
        )
        for d in detections
    ]

    lemma_surface_forms: dict[str, set[str]] = defaultdict(set)
    for r in stage1:
        for c in r.candidates:
            lemma_surface_forms[c].add(r.surface.lower())

    resolved: list[ResolvedDetection] = []
    for r in stage1:
        cands = set(r.candidates)
        if len(cands) > 1:
            attested = set()
            for c in cands:
                attested |= lemma_surface_forms[c]
            if len(attested) > 1:
                # declinable: indeclinable-only endings (-и/-у/-ю) are ruled out
                narrowed = {c for c in cands if not c.endswith(("и", "у", "ю"))}
                if narrowed:
                    cands = narrowed
            elif r.surface.lower() in cands:
                cands = {r.surface.lower()}
        resolved.append(ResolvedDetection(surface=r.surface, candidates=cands, capitalization_rescued=r.capitalization_rescued))
    return resolved


@dataclass
class LemmaEntry:
    lemma: str
    surface_forms: set[str]
    count: int
    capitalization_rescued_count: int
    needs_review: bool = False
    lemma_candidates: list[str] | None = None


def aggregate(resolved: list[ResolvedDetection]) -> list[LemmaEntry]:
    by_lemma: dict[str, LemmaEntry] = {}
    review: list[LemmaEntry] = []
    for r in resolved:
        if len(r.candidates) == 1:
            lemma = next(iter(r.candidates))
            e = by_lemma.setdefault(
                lemma, LemmaEntry(lemma=lemma, surface_forms=set(), count=0, capitalization_rescued_count=0)
            )
            e.surface_forms.add(r.surface)
            e.count += 1
            if r.capitalization_rescued:
                e.capitalization_rescued_count += 1
        elif r.candidates:
            review.append(
                LemmaEntry(
                    lemma=r.surface.lower(),
                    surface_forms={r.surface},
                    count=1,
                    capitalization_rescued_count=int(r.capitalization_rescued),
                    needs_review=True,
                    lemma_candidates=sorted(r.candidates),
                )
            )
    return merge_plural_singular(list(by_lemma.values())) + review


def _merge_key(lemma: str) -> str:
    # Only а/я (singular) <-> ы (plural) are merged. -и is excluded: it is
    # ambiguous between indeclinable and -и-plural (thesis §3.3.1/§3.3.3),
    # and stripping it caused false merges between unrelated names that
    # happen to share a stem only after the -и is removed (e.g. бхарата
    # (a name) vs бхарати (a different name) both collapsing to "бхарат").
    return lemma[:-1] if lemma.endswith(("а", "я", "ы")) else lemma


def merge_plural_singular(entries: list[LemmaEntry]) -> list[LemmaEntry]:
    """Thesis §3.3.3 final step: merge singular/plural pseudo-duplicate
    rubrics (апсара/апсары), keeping the plural form as canonical."""
    groups: dict[str, list[LemmaEntry]] = defaultdict(list)
    for e in entries:
        groups[_merge_key(e.lemma)].append(e)

    merged: list[LemmaEntry] = []
    for group in groups.values():
        if len(group) == 1:
            merged.append(group[0])
            continue
        plural = [e for e in group if e.lemma.endswith(("и", "ы"))]
        canonical, rest = (plural[0], [e for e in group if e is not plural[0]]) if plural else (group[0], group[1:])
        for e in rest:
            canonical.surface_forms |= e.surface_forms
            canonical.count += e.count
            canonical.capitalization_rescued_count += e.capitalization_rescued_count
        merged.append(canonical)
    return merged
