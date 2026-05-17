"""Registry mapping corpus filenames to their parent works.

Used by `source_metadata.build_source_jsonld` to add a `Book` entry to the
`Book.isPartOf` array — telling search engines "this source is a volume of
/ a translation of / a commentary on the named parent work." Knowledge Graph
linking benefits when many translations share the same parent entity.

Three relationship kinds are collapsed into `isPartOf` for simplicity:

1. **Volume**: parvan of the Mahābhārata, maṇḍala of the Ṛgveda, book of the
   Atharvaveda, kāṇḍa of the Rāmāyaṇa. Strict `isPartOf` semantics.
2. **Edition / translation**: each of the 10 Bhagavadgītā translations is an
   edition of the same abstract work. Schema.org would prefer `exampleOfWork`
   here, but Google accepts `isPartOf` as a coarser hint and treating volumes
   and translations uniformly keeps the registry simple.
3. **Commentary**: Rāmānuja's Gītābhāṣya, Abhinavagupta's Gītārthasaṃgraha,
   etc. — strictly these are *about* the parent work, not parts of it.
   Same lenient `isPartOf` treatment for v1.

Filename patterns are matched in order; the first hit wins. More-specific
patterns (e.g. the commentary-specific filenames) come before more general
ones (e.g. `bhagavadgita.*`).
"""
import re

# (compiled_pattern, parent_dict). Order matters — first match wins.
_PARENT_WORK_PATTERNS: list[tuple[re.Pattern, dict[str, str]]] = [
    # ── Volumes ──────────────────────────────────────────────────────────────
    (re.compile(r"^\d+_mahabharata-.*\.html$"), {
        "name": "Махабхарата",
        "alternateName": "Mahābhārata",
    }),
    (re.compile(r"^\d+_rigveda\.html$"), {
        "name": "Ригведа",
        "alternateName": "Ṛgveda",
    }),
    (re.compile(r"^\d+_atharvaveda\.html$"), {
        "name": "Атхарваведа",
        "alternateName": "Atharvaveda",
    }),
    (re.compile(r"^\d+_ramayana-.*\.html$"), {
        "name": "Рамаяна",
        "alternateName": "Rāmāyaṇa",
    }),

    # ── Bhagavadgītā: translations, anthology, commentaries ──────────────────
    # The commentary-specific filenames are listed before the broad bhagavadgita
    # pattern so a future "bhagavadgita-commentary-foo.html" would still match
    # the broad pattern correctly. As-is the order is informational only.
    (re.compile(r"^ramanuja_gitabhashya\.html$"), {
        "name": "Бхагавадгита",
        "alternateName": "Bhagavadgītā",
    }),
    (re.compile(r"^gitartha(samgraha|-samgraha).*\.html$"), {
        "name": "Бхагавадгита",
        "alternateName": "Bhagavadgītā",
    }),
    (re.compile(r"^bhagavadgita.*\.html$"), {
        "name": "Бхагавадгита",
        "alternateName": "Bhagavadgītā",
    }),
    (re.compile(r"^bhagavadgity\.html$"), {
        "name": "Бхагавадгита",
        "alternateName": "Bhagavadgītā",
    }),

    # ── Yoga-Sūtra: editions + anthology ─────────────────────────────────────
    (re.compile(r"^yoga-sutry.*\.html?$"), {
        "name": "Йога-сутры",
        "alternateName": "Yoga-Sūtra",
    }),

    # ── Śatakatraya: two editions ────────────────────────────────────────────
    (re.compile(r"^shatakatrayam.*\.html$"), {
        "name": "Шатакатраям",
        "alternateName": "Śatakatraya",
    }),

    # ── Buddhacarita: Sanskrit edition + Balmont's expanded edition ──────────
    (re.compile(r"^buddhacharita.*\.html$"), {
        "name": "Буддхачарита",
        "alternateName": "Buddhacarita",
    }),
]


def detect_parent_work(filename: str) -> dict[str, str] | None:
    """Return a parent-work dict (with `name` and `alternateName`) when
    `filename` matches a known volume/edition/commentary pattern, else None.
    """
    if not filename:
        return None
    for pattern, parent in _PARENT_WORK_PATTERNS:
        if pattern.match(filename):
            return parent
    return None
