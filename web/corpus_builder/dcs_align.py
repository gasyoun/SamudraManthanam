r"""DCS-anchored per-token Sanskrit morphology for the seg=sa side (H906).

НКРЯ needs the Sanskrit side morphologically tagged; the shipped export carries
only an SLP1 transliteration. MG: "the Sanskrit side initially used **DCS** as
the markup source… DCS is gold, vidyut is the second opinion." The
[Digital Corpus of Sanskrit](http://www.sanskrit-linguistics.org/dcs/) is a
sandhi-split, hand-/model-annotated gold corpus; its `token` table gives, per
word, lemma · UPOS · case · gender · number (+ tense/mood/person/voice/…). This
module aligns each seg=sa verse to the matching DCS chapter and returns those
gold analyses.

Alignment key (proven on MBh Āraṇyakaparva 3.1 → DCS `MBh, 3, 1`):

  * our source slug  → DCS text name + a chapter-ref template
  * our `passage`    → (book/kāṇḍa, chapter, verse-range)
  * DCS `sentence.sent_counter` == our verse number within the chapter

The DCS sqlite (`dcs_full.sqlite`, 920 MB) is **local-only** (it lives in the
sibling VisualDCS repo, not committed here). Set `DCS_SQLITE` to override the
path; if the file is absent every lookup returns `[]` so the pipeline degrades
gracefully (the sa_morph layer is simply not produced). DCS coverage is
per-text: it carries all 18 MBh books and the Rāmāyaṇa (by kāṇḍa), but e.g. the
Bhagavadgītā is absent (H848) — uncovered verses yield no gold rows, reported as
a coverage gap rather than silently guessed.
"""
import os
import re
import sqlite3

DCS_SQLITE = os.environ.get(
    'DCS_SQLITE',
    r'C:/Users/user/Documents/GitHub/VisualDCS/src/DCS-data-2026/dcs_full.sqlite')

# our source-slug family → (DCS text name, how to build the chapter ref).
# MBh: passage is "book.chapter.verse[-verse]" → ref "MBh, {book}, {chapter}".
# Rāmāyaṇa: book (kāṇḍa) is fixed by the slug; passage is "chapter.verse" →
#   ref "Rām, {kāṇḍa-abbrev}, {chapter}".
_RAMA_KANDA = {
    'balakanda': 'Bā', 'ayodhyakanda': 'Ay', 'aranyakanda': 'Ār',
    'kishkindhakanda': 'Ki', 'sundarakanda': 'Su', 'yuddhakanda': 'Yu',
    'uttarakanda': 'Utt',
}


def dcs_target(slug, passage):
    """(dcs_text_name, chapter_ref, verse_lo, verse_hi) for one seg=sa
    passage, or None when the slug/passage is not a DCS-mappable epic verse."""
    if not passage:
        return None
    m = re.match(r'^(\d+)\.(\d+)(?:\.(\d+)(?:-(\d+))?)?', passage)
    if 'mahabharata' in slug and m:
        book, chapter = int(m.group(1)), int(m.group(2))
        vlo = int(m.group(3)) if m.group(3) else 1
        vhi = int(m.group(4)) if m.group(4) else vlo
        return ('Mahābhārata', 'MBh, %d, %d' % (book, chapter), vlo, vhi)
    if 'ramayana' in slug:
        kanda = next((v for k, v in _RAMA_KANDA.items() if k in slug), None)
        mr = re.match(r'^(\d+)\.(\d+)(?:-(\d+))?', passage)
        if kanda and mr:
            chapter = int(mr.group(1))
            vlo = int(mr.group(2))
            vhi = int(mr.group(3)) if mr.group(3) else vlo
            return ('Rāmāyaṇa', 'Rām, %s, %d' % (kanda, chapter), vlo, vhi)
    return None


class DcsGold:
    """Read-only DCS lookup with a per-chapter token cache. One instance is
    reused across a whole export run (the sqlite open + chapter queries are the
    cost). `available` is False when the sqlite is absent."""

    _FIELDS = ('form', 'lemma', 'upos', 'feat_case', 'feat_gender',
               'feat_number', 'feat_tense', 'feat_mood', 'feat_person',
               'feat_voice')

    def __init__(self, db_path=DCS_SQLITE):
        self.available = bool(db_path) and os.path.exists(db_path)
        self._con = None
        self._text_ids = {}
        self._chapter_cache = {}  # (text_name, ref) -> {verse: [token dicts]}
        if self.available:
            self._con = sqlite3.connect('file:%s?mode=ro' % db_path, uri=True)

    def _text_id(self, name):
        if name not in self._text_ids:
            row = self._con.execute(
                'SELECT text_id FROM text WHERE name=?', (name,)).fetchone()
            self._text_ids[name] = row[0] if row else None
        return self._text_ids[name]

    def _chapter(self, text_name, ref):
        """{verse_no: [ {idx, form, lemma, upos, case, gender, number, ...} ]}
        for a DCS chapter, cached. DCS sent_counter is the verse number."""
        key = (text_name, ref)
        if key in self._chapter_cache:
            return self._chapter_cache[key]
        out = {}
        tid = self._text_id(text_name)
        if tid is not None:
            row = self._con.execute(
                'SELECT chapter_id FROM chapter WHERE text_id=? AND ref=?',
                (tid, ref)).fetchone()
            if row:
                cid = row[0]
                sents = self._con.execute(
                    'SELECT id, sent_counter FROM sentence WHERE chapter_id=? '
                    'ORDER BY sent_counter, sent_subcounter, id',
                    (cid,)).fetchall()
                for sid, counter in sents:
                    toks = self._con.execute(
                        'SELECT idx, %s FROM token WHERE sentence_id=? '
                        'ORDER BY idx' % ', '.join(self._FIELDS),
                        (sid,)).fetchall()
                    verse = out.setdefault(int(counter or 0), [])
                    for t in toks:
                        verse.append({
                            'idx': t[0], 'form': t[1] or '', 'lemma': t[2] or '',
                            'upos': t[3] or '', 'case': t[4] or '',
                            'gender': t[5] or '', 'number': t[6] or '',
                            'tense': t[7] or '', 'mood': t[8] or '',
                            'person': t[9] or '', 'voice': t[10] or '',
                        })
        self._chapter_cache[key] = out
        return out

    def gold_tokens(self, slug, passage):
        """Gold DCS tokens for one seg=sa passage, in (verse, idx) order.
        Each token dict also carries its `verse`. Empty list when DCS does not
        cover the passage (or the sqlite is absent)."""
        if not self.available:
            return []
        target = dcs_target(slug, passage)
        if target is None:
            return []
        text_name, ref, vlo, vhi = target
        chapter = self._chapter(text_name, ref)
        out = []
        for verse in range(vlo, vhi + 1):
            for t in chapter.get(verse, ()):
                out.append({'verse': verse, **t})
        return out
