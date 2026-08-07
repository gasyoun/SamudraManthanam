#!/usr/bin/env python3
"""Russian ordinal-word -> integer, feminine forms, 1..99.

The Ignatjev Devībhāgavata-purāṇa PDFs spell every chapter and skandha number
as a *feminine* ordinal word in the colophon
(``... заканчивается двадцатая глава ...``, ``ТАК ЗАКАНЧИВАЕТСЯ ПЕРВАЯ КНИГА ...``)
rather than as a digit. This module turns those words back into integers so the
parser can build the ``SKANDHA.CHAPTER.VERSE`` passage IDs.

Feminine because both nouns are feminine: ``глава`` (chapter) and ``книга``
(book/skandha). Only 1..99 is needed (DBhP has 12 skandhas; the longest skandha
has ~68 chapters).
"""
from __future__ import annotations

# Feminine ordinals 1..19 (irregular stems). Nominative + genitive: the
# genitive appears in excerpt headings like «Из двадцать второй главы»
# (H2376 Devī-purāṇa ch.22) where the ordinal agrees with «главы».
_UNITS_F = {
    "первая": 1, "первой": 1,
    "вторая": 2, "второй": 2,
    "третья": 3, "третьей": 3,
    "четвертая": 4, "четвёртая": 4, "четвертой": 4, "четвёртой": 4,
    "пятая": 5, "пятой": 5,
    "шестая": 6, "шестой": 6,
    "седьмая": 7, "седьмой": 7,
    "восьмая": 8, "восьмой": 8,
    "девятая": 9, "девятой": 9,
    "десятая": 10, "десятой": 10,
    "одиннадцатая": 11, "одиннадцатой": 11,
    "двенадцатая": 12, "двенадцатой": 12,
    "тринадцатая": 13, "тринадцатой": 13,
    "четырнадцатая": 14, "четырнадцатой": 14,
    "пятнадцатая": 15, "пятнадцатой": 15,
    "шестнадцатая": 16, "шестнадцатой": 16,
    "семнадцатая": 17, "семнадцатой": 17,
    "восемнадцатая": 18, "восемнадцатой": 18,
    "девятнадцатая": 19, "девятнадцатой": 19,
}
# Feminine round-tens ordinals (used when the number is an exact ten:
# двадцатая = 20, тридцатая = 30, ...). Genitive forms for «из N-ой главы».
_TENS_ORD_F = {
    "двадцатая": 20, "двадцатой": 20,
    "тридцатая": 30, "тридцатой": 30,
    "сороковая": 40, "сороковой": 40,
    "пятидесятая": 50, "пятидесятой": 50,
    "шестидесятая": 60, "шестидесятой": 60,
    "семидесятая": 70, "семидесятой": 70,
    "восьмидесятая": 80, "восьмидесятой": 80,
    "девяностая": 90, "девяностой": 90,
}
# Tens *prefix* words used in compound ordinals (двадцать первая = 21):
# here the tens part stays cardinal-looking and only the unit is ordinal.
_TENS_PREFIX = {
    "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
    "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80, "девяносто": 90,
}


def ordinal_f_to_int(phrase: str) -> int | None:
    """Convert a feminine ordinal phrase to an int, or None if unrecognised.

    Handles single words (``первая``, ``двадцатая``) and two-word compounds
    (``двадцать первая`` -> 21, ``сорок восьмая`` -> 48). Case-insensitive.
    """
    words = phrase.strip().lower().replace("ё", "ё").split()
    if not words:
        return None
    if len(words) == 1:
        w = words[0]
        if w in _UNITS_F:
            return _UNITS_F[w]
        if w in _TENS_ORD_F:
            return _TENS_ORD_F[w]
        return None
    if len(words) == 2:
        tens = _TENS_PREFIX.get(words[0])
        unit = _UNITS_F.get(words[1])
        if tens is not None and unit is not None and 1 <= unit <= 9:
            return tens + unit
        return None
    return None


# Regex-friendly alternation of every ordinal word we recognise, longest first
# so ``двадцать первая`` matches before bare ``первая``.
_ALL_ORD_WORDS = sorted(
    set(_UNITS_F) | set(_TENS_ORD_F) | set(_TENS_PREFIX),
    key=len, reverse=True,
)
ORDINAL_WORD_PATTERN = "(?:" + "|".join(_ALL_ORD_WORDS) + ")"


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for t in ["первая", "двадцатая", "двадцать первая", "сорок восьмая",
              "шестьдесят восьмая", "девяностая", "тарабарщина"]:
        print(f"{t!r} -> {ordinal_f_to_int(t)}")
