r"""The shared inline `<w><ana/>` per-token scheme for both corpus sides (H906).

НКРЯ marks a token as ``<w><ana lex="…" gr="…"/>surface</w>``, with **several**
``<ana>`` children when a token is ambiguous or is analysed as more than one
unit. H905 (Russian) and H906 (Sanskrit) each deliberately shipped their
morphology as a companion TSV and deferred the inline fold, so that neither side
would fix the attribute scheme before the other agreed to it. This module is
that agreement: one element shape, one attribute set, both languages.

Shared contract
---------------
* the annotated unit is the **surface word** — the `<se>` text is never
  rewritten, re-segmented or sandhi-resolved. Round-tripping the `<w>` text
  content reproduces the segment exactly.
* every ``<ana>`` carries ``lex`` (lemma) and ``gr`` (grammar), plus
  ``gramset`` naming the tagset the ``gr`` string is written in — ``opencorpora``
  for Russian (pymorphy3) and ``dcs-ud`` for Sanskrit (DCS gold). One shape, two
  honest tagsets: OpenCorpora and DCS/UD do not map onto one another 1-to-1 and
  pretending otherwise would silently corrupt the grammar.
* a word with no analysis is emitted as bare text, never as a guessed ``<ana>``.

Why the two sides are not symmetric
-----------------------------------
The Russian layer tokenizes its own surface, so ``<w>`` wrapping is 1-to-1 by
construction. The Sanskrit gold is **sandhi-split**: DCS resolves ``prītisamāyukto``
into ``prīti`` + ``samāyuktaḥ`` and ``sumahad`` into ``su`` + ``mahat``, so its
token sequence neither matches the surface word count (measured: gold has more
tokens than surface words in ~89 % of Yuddhakāṇḍa verses) nor re-concatenates to
the surface string (sandhi is *undone*, so the characters differ). On top of that
DCS carries speaker tags (``janamejaya uvāca``) absent from our text, and our MBh
groups are verse *ranges* covering several DCS sentences.

So the Sanskrit side attaches gold to surface words only through
:func:`align_gold_to_words`, which must account for the verse **end-to-end** or
returns ``None``. Where it returns ``None`` the words are emitted bare and the
complete gold stays in the ``sa_morph.tsv`` sidecar. This follows the rule
``align_sanskrit.py`` already sets for verse alignment in this repo: where the
join cannot be proven, fall back and report it — never fabricate.
"""
import re
import unicodedata
from xml.sax.saxutils import escape, quoteattr

GRAMSET_RU = 'opencorpora'
GRAMSET_SA = 'dcs-ud'

# Cyrillic word tokens — same class ru_morph.py tags, so the inline layer and
# the TSV sidecar cannot disagree about what a Russian token is.
_RU_TOKEN_RE = re.compile(r'[а-яА-ЯёЁ]+(?:-[а-яА-ЯёЁ]+)*')

# Sanskrit surface: dandas, verse markers and digits are structure, not words.
_SA_STRUCT_RE = re.compile(r'[।॥\d]+')


def split_ru(text):
    """[(is_word, chunk)] over a Russian segment, preserving every character."""
    return _split_by(text or '', _RU_TOKEN_RE)


def split_sa(text):
    """[(is_word, chunk)] over a Sanskrit segment, preserving every character.
    Dandas/verse numbers are non-word chunks so they survive untouched."""
    out = []
    for is_struct, chunk in _split_by(text or '', _SA_STRUCT_RE):
        if is_struct:
            out.append((False, chunk))
            continue
        for piece in re.split(r'(\s+)', chunk):
            if not piece:
                continue
            out.append((not piece.isspace(), piece))
    return out


def _split_by(text, rx):
    """[(matched, chunk)] covering `text` exactly."""
    out = []
    pos = 0
    for m in rx.finditer(text):
        if m.start() > pos:
            out.append((False, text[pos:m.start()]))
        out.append((True, m.group(0)))
        pos = m.end()
    if pos < len(text):
        out.append((False, text[pos:]))
    return out


# --------------------------------------------------------------------------- #
# Sanskrit: sandhi-tolerant attachment of DCS gold onto surface words          #
# --------------------------------------------------------------------------- #
_LONG = str.maketrans({'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṝ': 'ṛ', 'ḹ': 'ḷ'})

# Stop voicing/place + sibilant neutralization (see fold()). Sanskrit sandhi
# rewrites a stop across a seam to agree with what follows, and the seam is
# invisible in the surface spelling, so these fold globally rather than finally.
_NEUTRAL = str.maketrans({
    # stops: voicing + place neutralized
    'g': 'k', 'c': 'k', 'j': 'k',
    'd': 't', 'ḍ': 't', 'ṭ': 't',
    'b': 'p',
    # nasals: a nasal before a stop is homorganic in the surface spelling
    # (puṃ- written puṅ- before g), so every nasal folds together
    'ṅ': 'n', 'ñ': 'n', 'ṇ': 'n', 'm': 'n',
    # sibilants
    'ś': 's', 'ṣ': 's',
})


def fold(s):
    """Sandhi-tolerant skeleton of a Sanskrit surface form.

    A *match* key only — displayed forms always keep their real spelling. It
    folds exactly the alternations external sandhi introduces at a word seam,
    because the surface writes the sandhi'd form while DCS stores the underlying
    pada:

    * vowel length (``ā``→``a``) — sandhi lengthens across a seam;
    * the visarga/anusvara surface (``ḥ``→``s``, ``ṃ``→``m``), mirroring
      ``vidyut_diff._join_key``;
    * word-final ``-o`` ← ``-aḥ`` (``samāyuktaḥ`` written ``samāyukto`` before a
      voiced initial), the single commonest mismatch measured;
    * stop voicing/place neutralization (``g/c/j/k``→``k``, ``d/t``→``t``,
      ``b/p``→``p``, sibilants→``s``). These are applied **everywhere**, not just
      finally: the seam falls inside the surface word (``vāc``+``vidām`` is
      written ``vāgvidāṃ``), so a final-position-only rule cannot see it.

    Over-folding is contained by the caller: :func:`align_gold_to_words` still
    requires an exact per-word length match *and* a complete end-to-end cover of
    the verse, so a chance skeleton collision cannot silently shift analyses.
    """
    s = unicodedata.normalize('NFC', (s or '').lower()).translate(_LONG)
    s = s.replace('ḥ', 's').replace('ṃ', 'm').replace('ṁ', 'm')
    s = re.sub(r"[^a-zṛḷṅñṭḍṇśṣ']", '', s)
    s = re.sub(r'o$', 'as', s)
    s = s.translate(_NEUTRAL)
    return s


def _seam(s):
    """Collapse what vowel sandhi merges *across* a token seam.

    savarṇa-dīrgha fuses two like vowels into one (``manasā`` + ``api`` is
    written ``manasāpi``), so the concatenated gold carries a doubled vowel the
    surface never shows. Applied to the accumulated gold string and to the
    surface word alike, so the comparison stays symmetric."""
    return re.sub(r'([aiu])\1+', r'\1', s or '')


def align_gold_to_words(words, gold):
    """Attach DCS gold tokens to surface words, or return None.

    `words` is the list of surface word strings, `gold` the DCS token dicts for
    the same passage. Returns a list parallel to `words`, each entry the list of
    gold-token indices belonging to that word — or **None** when the verse
    cannot be accounted for end-to-end, which is the common case (DCS speaker
    tags, verse-range groups, recension divergence).

    The walk is strictly left-to-right and greedy: a word absorbs gold tokens
    until their folded skeletons cover its own, and any mismatch, leftover token
    or exhausted-gold condition fails the whole verse. Failing whole is
    deliberate — a partially-aligned verse would silently attach a word's
    morphology to its neighbour.
    """
    if not words or not gold:
        return None
    folded = [fold(t.get('form', '')) for t in gold]
    out = []
    gi = 0
    for w in words:
        target = _seam(fold(w))
        if not target:
            out.append([])
            continue
        acc = ''
        start = gi
        # absorb gold tokens until the seam-collapsed skeleton covers the word
        while gi < len(gold) and len(_seam(acc)) < len(target):
            acc += folded[gi]
            gi += 1
        acc = _seam(acc)
        if not acc or acc != target:
            return None
        out.append(list(range(start, gi)))
    if gi != len(gold):
        return None
    return out


# --------------------------------------------------------------------------- #
# emitters                                                                     #
# --------------------------------------------------------------------------- #
def _ana(lex, gr, gramset):
    return '<ana lex=%s gr=%s gramset="%s"/>' % (
        quoteattr(lex or ''), quoteattr(gr or ''), gramset)


def ru_gr(tok):
    """OpenCorpora grammar string for a ru_morph token: POS plus the case and
    number the sidecar already exposes, comma-joined in a fixed order."""
    return ','.join([p for p in (tok.get('pos'), tok.get('case'),
                                 tok.get('number')) if p])


def sa_gr(tok):
    """DCS/UD grammar string for one gold token, fixed field order so the
    output is byte-stable."""
    parts = [tok.get('upos') or '']
    for key in ('case', 'gender', 'number', 'tense', 'mood', 'person', 'voice'):
        v = tok.get(key)
        if v:
            parts.append(v)
    return ','.join(p for p in parts if p)


def annotate_ru(text, tokens):
    """Russian `<se>` inner XML with inline `<w><ana/>`.

    `tokens` is ru_morph.analyze(text) — one entry per word token, in order, so
    the pairing is positional and total.
    """
    parts = []
    ti = 0
    for is_word, chunk in split_ru(text):
        if not is_word:
            parts.append(escape(chunk))
            continue
        tok = tokens[ti] if ti < len(tokens) else None
        ti += 1
        if tok and (tok.get('lemma') or tok.get('pos')):
            parts.append('<w>%s%s</w>' % (
                _ana(tok.get('lemma'), ru_gr(tok), GRAMSET_RU), escape(chunk)))
        else:
            parts.append(escape(chunk))
    return ''.join(parts)


def annotate_sa(text, gold):
    """Sanskrit `<se>` inner XML with inline `<w><ana/>`, or None when the gold
    cannot be attached to the surface (caller then emits the plain segment).

    A surface word carries as many `<ana>` children as DCS tokens it resolves
    into — the sandhi-split compound `prītisamāyukto` yields two.
    """
    chunks = split_sa(text)
    words = [c for is_w, c in chunks if is_w]
    mapping = align_gold_to_words(words, gold)
    if mapping is None:
        return None
    parts = []
    wi = 0
    for is_word, chunk in chunks:
        if not is_word:
            parts.append(escape(chunk))
            continue
        idxs = mapping[wi]
        wi += 1
        if not idxs:
            parts.append(escape(chunk))
            continue
        anas = ''.join(_ana(gold[i].get('lemma'), sa_gr(gold[i]), GRAMSET_SA)
                       for i in idxs)
        parts.append('<w>%s%s</w>' % (anas, escape(chunk)))
    return ''.join(parts)
