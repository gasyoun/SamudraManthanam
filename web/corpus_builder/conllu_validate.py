#!/usr/bin/env python
r"""CoNLL-U structural validator, stdlib-only (H6371 / Wave 7).

Validates the CoNLL-U format rules this repo's emitted files must obey
(format v2, https://universaldependencies.org/format.html -- the structural
subset; no treebank-specific checks):

  E1  node lines have exactly 10 tab-separated columns
  E2  ID column: integer, or ``n-m`` range (n < m), strictly increasing, no
      overlapping/nested ranges, range interior ids contiguous and consumed
  E3  range rows (``n-m``): FORM non-empty; LEMMA UPOS XPOS FEATS HEAD
      DEPREL DEPS must be ``_``; MISC may carry SpaceAfter etc.
  E4  word rows: FORM and UPOS non-empty (LEMMA may be ``_`` -- an unlemmatized
      word is DATA, reported as warning W3, never faked)
  E5  FEATS / DEPS / MISC: ``_`` or well-formed ``Key=Value`` lists joined by
      ``|`` (no whitespace, no empty keys/values; DEPS pairs ``head:deprel``)
  E6  HEAD: ``_`` or integer
  E7  sentence framing: non-empty sentence has exactly one ``# sent_id =``
      comment; sent_id unique per file; ``# text =`` present; sentences
      separated by exactly one blank line; file ends with a blank line
  E8  ``# text`` reconstruction: the surface forms (range-row FORM inside a
      range, word FORM otherwise) joined per SpaceAfter flags must equal the
      ``# text`` value (the DCS convention: single spaces, no trailing space)
  W1  UPOS outside the 17-tag UD inventory -> reported per tag (the DCS->UD
      table in dcs_conllu.py maps everything observed; this is the tripwire
      that a NEW unmapped tag never slips through silently)
  W2  DCS feature extensions (Formation=*, Case=Cpd, ...) -> counted, not
      errors (documented passthrough, see dcs_conllu.py)
  W3  LEMMA ``_`` on a word row -> counted (lemma-coverage gap, feeds the
      per-source coverage report)

Exit code 0 iff no E-errors in any file; warnings never fail the run but are
always printed and summarized. Deterministic: no clock, sorted file order.

Usage:
  python conllu_validate.py FILE.conllu [FILE.conllu ...]
  python conllu_validate.py --quiet FILE ...     # summary line only
"""
import argparse
import collections
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

VERSION = '0.1.0'

UD_UPOS = frozenset(('ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON '
                     'PROPN PUNCT SCONJ SYM VERB X').split())
DCS_FEAT_EXTENSIONS = {'Formation'}
DCS_FEATVAL_EXTENSIONS = {('Case', 'Cpd')}

_ID_INT = re.compile(r'^\d+$')
_ID_RANGE = re.compile(r'^(\d+)-(\d+)$')
_FEATS = re.compile(r'^[A-Z0-9][A-Za-z0-9]*=[^\s|=]+(\|[A-Z0-9][A-Za-z0-9]*=[^\s|=]+)*$')
_DEPS = re.compile(r'^\d+:[a-z][^\s|=]*(:\w+)?(\|\d+:[a-z][^\s|=]*(:\w+)?)*$')
_MISC = re.compile(r'^[^\s|=]+=[^\s|=]+(\|[^\s|=]+=[^\s|=]+)*$')


def validate_text(text, path='<text>'):
    """Validate one CoNLL-U document (str). -> (errors, warnings, n_sentences).

    errors / warnings: lists of 'L<lineno>: code: message' strings (lineno 0
    when the defect is not line-anchored). warnings is a dict code->count via
    collections.Counter for the summary; the lists carry human messages.
    """
    errors, warns = [], []
    warn_counts = collections.Counter()

    def warn(code, msg, lineno=0):
        warn_counts[code] += 1
        warns.append('%s:%s: %s: %s' % (path, lineno, code, msg))

    if not text.endswith('\n'):
        errors.append('%s:0: E7: file does not end with a newline' % path)
    raw = text.split('\n')
    if raw and raw[-1] == '':
        raw.pop()  # trailing newline -> last element empty

    sent_ids_seen = set()
    lineno = 0
    i = 0
    n_sents = 0
    while i < len(raw):
        line = raw[i]
        lineno = i + 1
        if line == '':
            errors.append('%s:%d: E7: empty line outside a sentence boundary'
                          % (path, lineno))
            i += 1
            continue
        if not (line.startswith('#') or '\t' in line):
            errors.append('%s:%d: E1: line is neither comment nor 10-column '
                          'node row' % (path, lineno))
            i += 1
            continue
        # ---- one sentence: comments then node rows, then a blank line
        sent_comments = []
        node_lines = []          # (lineno, columns)
        while i < len(raw) and raw[i] != '':
            line = raw[i]
            if line.startswith('#'):
                if node_lines:
                    errors.append('%s:%d: E7: comment line inside node rows'
                                  % (path, i + 1))
                else:
                    sent_comments.append((i + 1, line))
            else:
                node_lines.append((i + 1, line.split('\t')))
            i += 1
        # at a blank line (or EOF)
        if i < len(raw):
            i += 1  # consume the single separator
            if i < len(raw) and raw[i] == '':
                errors.append('%s:%d: E7: two consecutive blank lines'
                              % (path, i + 1))
        if not node_lines:
            if sent_comments:
                errors.append('%s:%d: E7: sentence has comments but no node '
                              'rows' % (path, sent_comments[0][0]))
            continue
        n_sents += 1

        # ---- comments: sent_id + text
        sent_id = None
        text_val = None
        n_sentid = 0
        for cl, c in sent_comments:
            m = re.match(r'#\s*sent_id\s*=\s*(\S+)\s*$', c)
            if m:
                n_sentid += 1
                sent_id = m.group(1)
            m = re.match(r'#\s*text\s*=\s*(.*)$', c)
            if m and text_val is None:
                text_val = m.group(1)
        if n_sentid != 1:
            errors.append('%s:%d: E7: sentence needs exactly one sent_id '
                          'comment, found %d' % (path, lineno, n_sentid))
        elif sent_id in sent_ids_seen:
            errors.append('%s:%d: E7: duplicate sent_id %s'
                          % (path, lineno, sent_id))
        else:
            sent_ids_seen.add(sent_id)
        if text_val is None or not text_val.strip():
            errors.append('%s:%d: E7: sentence %s has no # text'
                          % (path, lineno, sent_id or '?'))

        # ---- node rows
        expect = 1            # next expected word id
        in_range = None       # (lo, hi) of the currently open range
        surface = []          # (form, space_after) for E8; interior words of
                              # a range are covered by the range FORM and do
                              # NOT contribute
        for nl, cols in node_lines:
            if len(cols) != 10:
                errors.append('%s:%d: E1: %d columns, expected 10'
                              % (path, nl, len(cols)))
                continue
            cid, form, lemma, upos, xpos, feats, head, deprel, deps, misc = cols
            m = _ID_RANGE.match(cid)
            if m:
                lo, hi = int(m.group(1)), int(m.group(2))
                if hi <= lo:
                    errors.append('%s:%d: E2: range %s has hi<=lo'
                                  % (path, nl, cid))
                if lo != expect:
                    errors.append('%s:%d: E2: range %s out of order, expected '
                                  'id %d' % (path, nl, cid, expect))
                if not form:
                    errors.append('%s:%d: E3: range row with empty FORM'
                                  % (path, nl))
                for col, name in ((lemma, 'LEMMA'), (upos, 'UPOS'),
                                  (xpos, 'XPOS'), (feats, 'FEATS'),
                                  (head, 'HEAD'), (deprel, 'DEPREL'),
                                  (deps, 'DEPS')):
                    if col != '_':
                        errors.append('%s:%d: E3: range row %s must be "_", '
                                      'got %r' % (path, nl, name, col))
                in_range = (lo, hi)
                expect = lo
                surface.append((form, _space_after(misc)))
                continue
            if not _ID_INT.match(cid):
                errors.append('%s:%d: E2: bad ID %r' % (path, nl, cid))
                continue
            wid = int(cid)
            interior = in_range is not None and in_range[0] <= wid <= in_range[1]
            if interior:
                if wid != expect:
                    errors.append('%s:%d: E2: word %d inside range %d-%d out '
                                  'of order' % (path, nl, wid,
                                                in_range[0], in_range[1]))
                if wid >= in_range[1]:
                    in_range = None  # range consumed; next word is hi+1
            else:
                in_range = None
                if wid != expect:
                    errors.append('%s:%d: E2: word id %d out of order, '
                                  'expected %d' % (path, nl, wid, expect))
                surface.append((form, _space_after(misc)))
            if not form:
                errors.append('%s:%d: E4: empty FORM' % (path, nl))
            if not upos:
                errors.append('%s:%d: E4: empty UPOS' % (path, nl))
            elif upos != '_' and upos not in UD_UPOS:
                warn('W1', 'UPOS %r outside the UD inventory (unmapped DCS '
                     'tag passed through)' % upos, nl)
            if lemma in ('', '_'):
                warn('W3', 'word %s has no lemma' % cid, nl)
            for col, name, rx in ((feats, 'FEATS', _FEATS),
                                  (deps, 'DEPS', _DEPS),
                                  (misc, 'MISC', _MISC)):
                if col not in ('', '_') and not rx.match(col):
                    errors.append('%s:%d: E5: malformed %s %r'
                                  % (path, nl, name, col))
            if head not in ('', '_',) and not _ID_INT.match(head):
                errors.append('%s:%d: E6: bad HEAD %r' % (path, nl, head))
            if feats not in ('', '_'):
                for f in feats.split('|'):
                    k, _, v = f.partition('=')
                    if k in DCS_FEAT_EXTENSIONS or (k, v) in DCS_FEATVAL_EXTENSIONS:
                        warn('W2', 'DCS feature extension %s' % f, nl)
            expect = wid + 1
        # ---- E8 text reconstruction
        if text_val is not None and surface:
            joined = ''.join(form + ('' if sa else ' ')
                             for form, sa in surface).rstrip(' ')
            if joined != text_val:
                errors.append('%s:%d: E8: # text does not match the token '
                              'surfaces (text=%r vs tokens=%r)'
                              % (path, lineno, text_val, joined))
    return errors, warns, warn_counts, n_sents


def _space_after(misc):
    return misc == 'SpaceAfter=No' or (
        bool(misc) and misc != '_' and 'SpaceAfter=No' in misc.split('|'))


def validate_file(path):
    # newline=None: universal newlines -- a CRLF-written file validates the
    # same as the LF file the emitter produces (no stray \r in column 10).
    with open(path, encoding='utf-8', newline=None) as f:
        return validate_text(f.read(), path)


def main(argv=None):
    ap = argparse.ArgumentParser(description='CoNLL-U structural validator '
                                            '(stdlib-only, H6371).')
    ap.add_argument('files', nargs='+', help='.conllu files')
    ap.add_argument('--quiet', action='store_true', help='summary line only')
    ap.add_argument('--max-print', type=int, default=20,
                    help='max messages printed per file (default 20)')
    a = ap.parse_args(argv)
    total_err = 0
    total_sents = 0
    total_warns = collections.Counter()
    for path in a.files:
        errors, warns, wcounts, n = validate_file(path)
        total_err += len(errors)
        total_sents += n
        total_warns.update(wcounts)
        if not a.quiet:
            for msg in errors[:a.max_print]:
                print(msg)
            if len(errors) > a.max_print:
                print('%s: ... and %d more errors' % (path, len(errors) - a.max_print))
            for msg in warns[:a.max_print]:
                print(msg)
        print('%s: %d sentences, %d errors, %s' %
              (path, n, len(errors),
               ' '.join('%s=%d' % kv for kv in sorted(wcounts.items())) or 'no warnings'))
    print('TOTAL %d file(s): %d sentences, %d errors%s'
          % (len(a.files), total_sents, total_err,
             (' ' + ' '.join('%s=%d' % kv for kv in sorted(total_warns.items())))
             if total_warns else ''))
    return 1 if total_err else 0


if __name__ == '__main__':
    sys.exit(main())
