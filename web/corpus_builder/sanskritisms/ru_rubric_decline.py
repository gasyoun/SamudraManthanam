r"""Generator for `rus_index_declined.txt` -- the declined Russian rubric
forms consumed by the epithet layer (`annotations.load_rus_index_declined`
-> `extract.py`'s Aho-Corasick matcher, H1204).

Re-implements the intent of the 2024-11 work note (Marsel's continuation of
Rubanova's pipeline) natively in the port. The note's own artifacts --
`Index_items_declension.ipynb`, `index_lone_declined_manual.json`,
`pyphrasy` -- are not in this repo NOR in the upstream
github.com/evgeniarubanova/sanskrit_stemmer (checked H1207: its tree has
only the same 18 flat files already known, no notebook, no manual-gold
json). This is a re-derivation from `rus_index.txt` + the observed defects
in the committed `rus_index_declined.txt` (see
docs/RUBANOVA_NKRYA_RUBRIC_DECLENSION_STATUS_2024_11.md), not a port of
`sans_stemmer.ipynb`'s `decline()` -- whose curated `both`/`tcsh`/
`except_last`/`last` tables are subsumed by the general rules below (and
whose `tcsh` case only ever emitted 5 of 6 case forms, a bug not worth
reproducing).

Method
------
1. **Numeral-governed phrases** ("три мира", "восемь чаш", "пять великих
   элементов"): the leading numeral word(s) inflect on their own NUMR
   paradigm; the noun tail agrees per standard Russian numeral government
   -- genitive SINGULAR in nom/acc for два/две/три/четыре (and compounds
   ending in them), genitive PLURAL in nom/acc for five and up; genitive/
   dative/instrumental/locative ALWAYS take the plural noun form in the
   numeral's own case. This is the fix for the "три мира" defect: the
   original notebook blindly re-inflected the already-genitive-singular
   "мира" through pymorphy2's default (wrong) top parse instead of
   applying numeral-noun agreement, producing "три мир" for nominative.

2. **Everything else**: every Cyrillic word in the phrase is inflected
   independently to the target case (preserving its own grammatical
   number), spliced into the original string by regex span so punctuation,
   hyphens and en-dashes survive untouched. A word is left FIXED (kept
   verbatim across all 6 output cases) when it is:
     - a function word (preposition/particle/conjunction/adverb) or a
       short-form adjective/participle (no case forms in Russian at all);
     - already in a non-nominative case in the base rubric, i.e. a
       governed complement ("сын дхармы", "по небу", "владеющий ...
       рукой" all stay put -- this is also what fixes "чрева" and every
       plain "<head> <genitive-tail>" rubric without a curated list);
     - not recognised by pymorphy3 at all (`is_known=False` -- an
       unadapted Sanskrit name such as "бхагиратхи"/"вивасвана").
   Single-word declension prefers a nominative-singular ADJF/PRTF parse
   over a same-scored NOUN homograph -- this is the fix for the
   "вездесущия" defect: pymorphy2/3 tie-breaks "вездесущий" between
   `ADJF,masc,sing,nomn` and `NOUN,neut,plur,gent` (both score 0.333) and
   the notebook's raw `.inflect()` on whichever comes first sometimes
   picks the noun reading, producing a spurious plural-noun paradigm.

3. **"тот, ..." relative-clause rubrics** ("тот, чьё знамя – бык", "тот,
   кто рожден под созвездием пхальгуни") are the one genuinely
   non-compositional pattern: only "тот" inflects; the whole clause after
   it is frozen verbatim (its internal words are themselves nominative --
   "чьё знамя" / "бык" as clause-internal subject+predicate -- so rule 2's
   non-nominative-only fixing would not catch them).

ё is stripped from the output (project house style, "никогда не писать
ё" -- see the @DECIDE note in H1207; this also removes the stress-mark
inconsistency the old file had, e.g. "быкознамённого" -> "быкознаменного").
"""

import argparse
import json
import re
import sys

from ._paths import diplom_path

CASES = ("nomn", "gent", "datv", "accs", "ablt", "loct")
CASE_LABELS = {
    "nomn": "nom",
    "gent": "gen",
    "datv": "dat",
    "accs": "acc",
    "ablt": "ins",
    "loct": "loc",
}

RUS_INDEX_FILE = "rus_index.txt"
RUS_INDEX_DECLINED_FILE = "rus_index_declined.txt"

_WORD_RE = re.compile(r"[а-яёА-ЯЁ]+")

_DECLINABLE_POS = frozenset({"NOUN", "ADJF", "PRTF", "NUMR"})
_FUNCTION_OR_INVARIANT_POS = frozenset(
    {
        "PREP",
        "CONJY",
        "CONJ",
        "PRCL",
        "INTJ",
        "ADVB",
        "COMP",
        "PRED",
        "VERB",
        "INFN",
    }
)
_SHORT_FORM_GRAMMEMES = frozenset({"ADJS", "PRTS"})

# Numeral words the rubrics actually use. "тридесять" is archaic
# Church-Slavonic for "thirty" (fairy-tale idiom) -- pymorphy3 does not
# know it at all (misparses it as an infinitive verb), so its paradigm is
# hand-supplied, mirroring "тридцать"'s regular -дцать/-десять pattern.
_GOV_SINGULAR_NUMERALS = frozenset({"два", "две", "три", "четыре"})
_NUMERAL_WORDS = _GOV_SINGULAR_NUMERALS | frozenset(
    {
        "пять",
        "шесть",
        "семь",
        "восемь",
        "девять",
        "десять",
        "одиннадцать",
        "двенадцать",
        "тринадцать",
        "четырнадцать",
        "пятнадцать",
        "шестнадцать",
        "семнадцать",
        "восемнадцать",
        "девятнадцать",
        "двадцать",
        "тридцать",
        "тридесять",
    }
)
_IRREGULAR_NUMERAL_FORMS = {
    "тридесять": {
        "nomn": "тридесять",
        "gent": "тридесяти",
        "datv": "тридесяти",
        "accs": "тридесять",
        "ablt": "тридесятью",
        "loct": "тридесяти",
    },
}

# A handful of irreducible pymorphy homograph traps, hand-verified against
# `rus_index.txt` (H1207): every occurrence of these lowercased surface
# forms in this corpus is a fixed genitive/accusative tail whose top
# pymorphy parse nonetheless lands on an unrelated, more frequent common
# word's nominative/accusative-plural reading with no genitive candidate
# to fall back on (unlike "палицы"/"раковины", which DO carry a
# competitive genitive parse and so are already handled generally):
#   паки   -> "Пака" (demon name) gen.sg, NOT ADVB "паки" (archaic
#             "again") or NOUN,masc,plur,nomn "пак"
#   балы   -> "Бала" (demon name) gen.sg, NOT NOUN,masc,plur,nomn "бал"
#   ганги  -> "Ганга" (river name) gen.sg, NOT NOUN,masc,Geox,plur,nomn
#             "ганг"
#   манасы -> "Манаса" (name) gen.sg, NOT NOUN,masc,Geox,plur,nomn "манас"
#   знак   -> object of "несущий" ("bearing a sign"), accusative-
#             inanimate == nominative surface form, so no case-based
#             signal distinguishes it from an agreeing nominative noun.
#   лука   -> "лук" (bow) gen.sg in "владетель лука" ("holder of the
#             bow"), NOT NOUN,anim,masc,Name,sing,nomn "Лука" (the given
#             name Luka) or NOUN,femn,sing,nomn "лука" (a meander/bend) --
#             its top parse (0.556) beats the correct gen.sg "лук"
#             reading (0.333).
#   гады   -> "Гада" (demon name) gen.sg in "брат гады" ("brother of
#             Gada"); pymorphy has no genitive candidate at all here,
#             ONLY NOUN,anim,masc,plur,nomn "гад" ("reptile/scoundrel",
#             plural) at 1.0 confidence -- an unrecoverable collision
#             with a common word, not a scoring artefact.
#   дроны  -> "Дрона" (teacher name) gen.sg in "сын дроны" ("son of
#             Drona"), NOT NOUN,masc,plur,nomn/accs "дрон" (the modern
#             loanword "drone" -- a post-2020 OpenCorpora addition
#             Rubanova's original pipeline never had to contend with).
_TAIL_FORCE_FIXED = frozenset(
    {
        "паки",
        "балы",
        "ганги",
        "манасы",
        "знак",
        "лука",
        "гады",
        "дроны",
    }
)

# "индра" (Indra): pymorphy doesn't know it and its fake-dictionary guess
# tags it "Fixd" (indeclinable), all 6 cases tied at the same score --
# but Sanskrit deity names transliterated with a final -а are routinely
# declined in Russian scholarship (Индры, Индре, Индрой, ...), and here
# it is the agreeing head noun of "великий индра" (not a genitive tail),
# so it is force-declined via the regular masc.-a noun paradigm.
_HEAD_FORCE_DECLINE = {
    "индра": {
        "nomn": "индра",
        "gent": "индры",
        "datv": "индре",
        "accs": "индру",
        "ablt": "индрой",
        "loct": "индре",
    },
    # "пасть" (mouth/jaw, the head of "пасть кобылицы") loses the parse
    # tie-break to the unrelated INFN homograph "пасть" ("to fall") at
    # 0.5 vs 0.25 -- decisively ahead by score, so the usual ADJF/PRTF-
    # preference heuristics don't fire, and the intended femn.-sing noun
    # paradigm is hand-supplied instead.
    "пасть": {
        "nomn": "пасть",
        "gent": "пасти",
        "datv": "пасти",
        "accs": "пасть",
        "ablt": "пастью",
        "loct": "пасти",
    },
}


def load_morph():
    import pymorphy3

    return pymorphy3.MorphAnalyzer()


def _strip_yo(text):
    return text.replace("ё", "е").replace("Ё", "Е")


_COMPETITIVE_SCORE_RATIO = 0.99


def _best_parse(word, morph):
    """Prefer a nominative-singular ADJF/PRTF/NOUN parse over a
    SAME-SCORED (or near-tied) homograph mis-tag -- the "вездесущий"
    tie-break defect (ADJF,masc,sing,nomn vs NOUN,neut,plur,gent, both
    0.333). Never overrides a parse that is clearly ahead on score (e.g.
    "мира" NOUN,masc,sing,gent мир @0.994 vs the unrelated homograph
    NOUN,neut,plur,nomn миро @0.002 -- overriding that produced the
    "три мира" -> "три мир" defect; "раковины" NOUN,femn,sing,gent
    раковина @0.4 vs NOUN,femn,plur,nomn раковина @0.2 -- same class of
    bug for any genitive-singular tail whose surface is nom-plural-
    ambiguous)."""
    parses = morph.parse(word)
    if not parses:
        return None
    if not parses[0].is_known:
        # Unknown word: pymorphy's guesser hedges across several fake-
        # dictionary lexeme candidates, sometimes putting a spurious NOUN
        # guess ahead of an equally-guessed ADJF one by a wide score
        # margin (e.g. "десятиликий" NOUN,femn,plur,gent @0.35 vs
        # ADJF,masc,sing,nomn @0.15). Every compound epithet in this
        # corpus that pymorphy doesn't know ("десятиликий", "тысячеокий",
        # "самосущий", ...) IS in fact an adjective, so prefer an ADJF/
        # PRTF nomn guess unconditionally rather than by score.
        for p in parses:
            if p.tag.POS in ("ADJF", "PRTF") and p.tag.case == "nomn":
                return p
        return parses[0]
    top_score = parses[0].score
    threshold = top_score * _COMPETITIVE_SCORE_RATIO
    competitive = [p for p in parses if p.score >= threshold]
    for p in competitive:
        if p.tag.POS in ("ADJF", "PRTF") and p.tag.case == "nomn":
            return p
    for p in competitive:
        if p.tag.POS == "NOUN" and p.tag.case == "nomn":
            return p
    return parses[0]


def _word_number(parse):
    return "plur" if "plur" in parse.tag else "sing"


def _is_fixed_pos(parse):
    tag = parse.tag
    if tag.POS in _FUNCTION_OR_INVARIANT_POS:
        return True
    if tag.POS in _SHORT_FORM_GRAMMEMES:
        return True
    return tag.POS not in _DECLINABLE_POS


def _has_competitive_genitive(parses):
    """True if a genitive-case reading is among the top-scored parses --
    not necessarily THE top parse. Many fem/masc -а/-я nouns are exactly
    tied (or near-tied) between {nom.plur} and {gen.sg} with no context to
    break the tie ("палицы", "раковины"); in this corpus, a position>0
    noun that COULD be a genitive tail overwhelmingly IS one ("владетель
    раковины, диска и палицы" = "holder of the conch, disc and mace"), so
    genitive is preferred over nominative-plural whenever it's plausible,
    rather than trusting whichever tied parse pymorphy lists first."""
    if not parses:
        return False
    threshold = parses[0].score * _COMPETITIVE_SCORE_RATIO
    return any(p.score >= threshold and p.tag.case == "gent" for p in parses)


def _classify(word, morph, position):
    """'decline' or 'fixed' for one lowercased word at `position` in its
    phrase (position 0 = the head)."""
    if word in _HEAD_FORCE_DECLINE:
        return "decline"
    if word in _TAIL_FORCE_FIXED:
        return "fixed"
    parses = morph.parse(word)
    if not parses:
        return "fixed"
    best = _best_parse(word, morph)
    if _is_fixed_pos(best):
        return "fixed"
    if position == 0:
        # The head word: decline it even when pymorphy doesn't recognise
        # the lexeme (is_known=False), as long as it *guessed* a
        # declinable ADJF/PRTF/NOUN/NUMR paradigm -- this is exactly how
        # compound adjectives like "десятиликий"/"одиннадцатителый" (not
        # in OpenCorpora, but a confident suffix-analogy ADJF guess) get
        # declined. Tail words keep the stricter is_known gate below,
        # since an unrecognised TAIL is usually an unadapted Sanskrit
        # proper name ("бхагиратхи") that should stay fixed, not a
        # regular Russian compound.
        return "decline"
    if not best.is_known:
        return "fixed"
    if _has_competitive_genitive(parses):
        return "fixed"
    if best.tag.case not in (None, "nomn"):
        return "fixed"  # already a governed complement (dat/ins/loc/...)
    return "decline"


def _inflect_generic(word, case, morph):
    if word in _HEAD_FORCE_DECLINE:
        return _HEAD_FORCE_DECLINE[word][case]
    best = _best_parse(word, morph)
    number = _word_number(best)
    infl = best.inflect({case, number}) or best.inflect({case})
    return infl.word if infl else None


def _inflect_numeral(word, case, morph):
    if word in _IRREGULAR_NUMERAL_FORMS:
        return _IRREGULAR_NUMERAL_FORMS[word][case]
    for p in morph.parse(word):
        if p.tag.POS == "NUMR":
            infl = p.inflect({case})
            if infl:
                return infl.word
    infl = morph.parse(word)[0].inflect({case})
    return infl.word if infl else word


def _numeral_prefix(words_lower):
    """(count_of_leading_numeral_tokens, gov_singular) or None."""
    n = 0
    for w in words_lower:
        if w in _NUMERAL_WORDS:
            n += 1
        else:
            break
    if n == 0:
        return None
    return n, words_lower[n - 1] in _GOV_SINGULAR_NUMERALS


def _match_case(template, form):
    """Mirror the leading-capital of `template` onto `form`."""
    if template[:1].isupper():
        return form[:1].upper() + form[1:]
    return form


def decline_phrase(phrase, morph):
    """Return {case: declined_phrase_string} for all 6 CASES."""
    spans = [(m.start(), m.end(), m.group(0)) for m in _WORD_RE.finditer(phrase)]
    words_lower = [s[2].lower() for s in spans]
    if not spans:
        return {case: phrase for case in CASES}

    numeral_info = _numeral_prefix(words_lower)
    tot_clause = len(spans) > 1 and words_lower[0] == "тот"

    result = {}
    for case in CASES:
        pieces = []
        cursor = 0
        for i, (start, end, surface) in enumerate(spans):
            pieces.append(phrase[cursor:start])
            lower = words_lower[i]
            form = None
            if numeral_info is not None:
                n_prefix, gov_singular = numeral_info
                if i < n_prefix:
                    form = _inflect_numeral(lower, case, morph)
                else:
                    tail_case = "gent" if case in ("nomn", "accs") else case
                    if case in ("nomn", "accs"):
                        tail_number = "sing" if gov_singular else "plur"
                    else:
                        tail_number = "plur"
                    best = _best_parse(lower, morph)
                    if best.is_known and not _is_fixed_pos(best):
                        infl = best.inflect({tail_case, tail_number}) or best.inflect(
                            {tail_case}
                        )
                        form = infl.word if infl else None
            elif tot_clause and i > 0:
                form = None
            else:
                if _classify(lower, morph, i) == "decline":
                    form = _inflect_generic(lower, case, morph)
            pieces.append(_match_case(surface, form) if form else surface)
            cursor = end
        pieces.append(phrase[cursor:])
        out = "".join(pieces)
        result[case] = _strip_yo(out)
    return result


def _read_lines(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield line


def generate_declined_index(rus_index_path=None, morph=None):
    """[(base_lower, [form_nom, form_gen, form_dat, form_acc, form_ins,
    form_loc]), ...] for every rubric in `rus_index.txt`."""
    rus_index_path = rus_index_path or diplom_path(RUS_INDEX_FILE)
    morph = morph or load_morph()
    out = []
    for base in _read_lines(rus_index_path):
        forms_by_case = decline_phrase(base.lower(), morph)
        forms = [forms_by_case[c] for c in CASES]
        out.append((_strip_yo(base.lower()), forms))
    return out


def format_line(base, forms):
    return "%s : %r" % (base, forms)


def write_declined_index(entries, out_path=None):
    out_path = out_path or diplom_path(RUS_INDEX_DECLINED_FILE)
    with open(out_path, "w", encoding="utf-8", newline="\r\n") as f:
        for base, forms in entries:
            f.write(format_line(base, forms) + "\n")


def score_against_gold(entries, gold):
    """gold: {base_lower: [6 case forms]}. Returns a report dict with
    per-rubric form accuracy and paradigm (whole-rubric) accuracy, only
    over rubrics present in `gold`."""
    by_base = dict(entries)
    total_forms = 0
    correct_forms = 0
    total_paradigms = 0
    correct_paradigms = 0
    mismatches = []
    for base, gold_forms in gold.items():
        if base not in by_base:
            mismatches.append({"base": base, "reason": "missing from generated output"})
            continue
        got_forms = by_base[base]
        total_paradigms += 1
        paradigm_ok = True
        for case_label, got, want in zip(CASE_LABELS.values(), got_forms, gold_forms):
            total_forms += 1
            if got == want:
                correct_forms += 1
            else:
                paradigm_ok = False
                mismatches.append(
                    {
                        "base": base,
                        "case": case_label,
                        "got": got,
                        "want": want,
                    }
                )
        if paradigm_ok:
            correct_paradigms += 1
    return {
        "form_accuracy": correct_forms / total_forms if total_forms else None,
        "paradigm_accuracy": (
            correct_paradigms / total_paradigms if total_paradigms else None
        ),
        "total_forms": total_forms,
        "correct_forms": correct_forms,
        "total_paradigms": total_paradigms,
        "correct_paradigms": correct_paradigms,
        "mismatches": mismatches,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rus-index", default=None, help="input rus_index.txt path")
    ap.add_argument("--out", default=None, help="output rus_index_declined.txt path")
    ap.add_argument("--gold", default=None, help="manual gold JSON to score against")
    ap.add_argument(
        "--report", default=None, help="write the accuracy report JSON here"
    )
    ap.add_argument("--dry-run", action="store_true", help="do not write --out")
    args = ap.parse_args(argv)

    morph = load_morph()
    entries = generate_declined_index(args.rus_index, morph=morph)

    if not args.dry_run:
        write_declined_index(entries, args.out)
        print(
            "wrote %d rubrics to %s"
            % (len(entries), args.out or diplom_path(RUS_INDEX_DECLINED_FILE)),
            file=sys.stderr,
        )

    if args.gold:
        with open(args.gold, encoding="utf-8") as f:
            gold_raw = json.load(f)
        gold = {k.lower(): v for k, v in gold_raw.items()}
        report = score_against_gold(entries, gold)
        print(
            "paradigm accuracy: %.1f%% (%d/%d)  form accuracy: %.1f%% (%d/%d)"
            % (
                (report["paradigm_accuracy"] or 0) * 100,
                report["correct_paradigms"],
                report["total_paradigms"],
                (report["form_accuracy"] or 0) * 100,
                report["correct_forms"],
                report["total_forms"],
            ),
            file=sys.stderr,
        )
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        return report

    return None


if __name__ == "__main__":
    main()
