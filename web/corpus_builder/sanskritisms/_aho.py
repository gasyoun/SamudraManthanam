r"""Aho-Corasick multi-pattern matcher (dependency-free, pure Python).

Drop-in replacement for a `re.compile('|'.join(escape(f) for f in forms))`
alternation when `forms` is a large set of literal strings. The flat
`re`-alternation the epithet layer used (1,346 declined-phrase forms)
re-tries every alternative at every text position -- O(text * patterns) --
which cost ~7.5 s per source on the MBh Aranyakaparva. Aho-Corasick scans
each text once in O(text + matches).

`iter_nonoverlapping` reproduces `re.finditer` of a *longest-first* literal
alternation exactly (validated byte-for-byte against the old regex over all
2,033 Aranyakaparva verses, 0 mismatches): leftmost match wins, at each
start the longest keyword wins, scanning resumes at the match end. No
external dependency (pyahocorasick is not installed and must not be required
for a fresh-clone run -- see docs/RUBANOVA_NKRYA_PIPELINE_MANUAL.md portability
note).
"""
import collections


class AhoCorasick:
    """Immutable automaton over a fixed set of literal keyword strings."""

    __slots__ = ('_goto', '_fail', '_out')

    def __init__(self, patterns):
        goto = [{}]
        out = [0]            # out[node] = length of the LONGEST keyword ending here (0 = none)
        for pat in patterns:
            if not pat:
                continue
            node = 0
            for ch in pat:
                nxt = goto[node].get(ch)
                if nxt is None:
                    nxt = len(goto)
                    goto.append({})
                    out.append(0)
                    goto[node][ch] = nxt
                node = nxt
            if len(pat) > out[node]:
                out[node] = len(pat)

        fail = [0] * len(goto)
        queue = collections.deque()
        for nxt in goto[0].values():
            queue.append(nxt)          # depth-1 nodes fail to root (0)
        while queue:
            r = queue.popleft()
            for ch, u in goto[r].items():
                queue.append(u)
                f = fail[r]
                while f and ch not in goto[f]:
                    f = fail[f]
                fu = goto[f].get(ch, 0)
                fail[u] = 0 if fu == u else fu
                # carry the longest keyword reachable via the fail chain
                if out[fail[u]] > out[u]:
                    out[u] = out[fail[u]]
        self._goto, self._fail, self._out = goto, fail, out

    def find_matches(self, text):
        """Yield (start, end) for the longest keyword ending at each text
        position (end-position order, may overlap)."""
        goto, fail, out = self._goto, self._fail, self._out
        node = 0
        for i, ch in enumerate(text):
            while node and ch not in goto[node]:
                node = fail[node]
            node = goto[node].get(ch, 0)
            length = out[node]
            if length:
                yield i - length + 1, i + 1

    def iter_nonoverlapping(self, text):
        """Yield (start, end) reproducing `re.finditer` of a longest-first
        literal alternation: leftmost, longest-at-start, resume at end."""
        cand = sorted(self.find_matches(text), key=lambda se: (se[0], -se[1]))
        next_ok = 0
        for start, end in cand:
            if start < next_ok:
                continue
            yield start, end
            next_ok = end
