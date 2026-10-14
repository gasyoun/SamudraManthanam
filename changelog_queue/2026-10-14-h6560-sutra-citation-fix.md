# 2026-10-14 — H6560 canon sutra-citation fix (sym-/syn- section)

Fixed the canonically defective sūtra citation in four artifacts (canon doc
`docs/MORPHONOLOGY_NASAL_PREFIX_SYM_SYN_SANSKRITISM_VARIANTS_12-10-2026.md`, draft §4.1
`docs/ARTICLE_SANSKRITISMS_VJ_DRAFT_12-10-2026.md`, concept doc
`docs/CONCEPT_SANSKRITISMS_IN_RUSSIAN_VJ_ARTICLE_10-10-2026.md`, CHANGELOG bullets
0.19.61/0.19.63 + doc metadoc). The previously quoted «rasābhyāṃ no ṇaḥ samānatarasya» as
«Aṣṭādhyāyī 8.3.24» licensing an optional [n] after a/ā before sibilants is wrong: the canonical
resolver (ashtadhyayi.com dataset via SanskritGrammar/GasunsDhatu_2014/revision-2026/panini_sutra.py)
gives 8.3.24 = naś cāpadāntasya jhali (non-apadānta n/m → anusvāra before jhal, mandatory); the
quoted line is a corruption of 8.4.1 raṣābhyāṃ no ṇaḥ samānapade (ṇatva after r/ṣ); parasavarṇa
is 8.4.58 anusvārasya yayi parasavarṇaḥ with sibilants outside yay (Vasu's own ākraṃsyate). No
mūla-sūtra licenses an optional [n] before sibilants. Reframed: самсара/сансара variability is
recipient-side transmission of the anusvāra (written anglo-Latin channel copies the m-graph,
oral recitation renders [n]), not a Paninian option. Also removed the unconfirmed §3 mechanism
insertion «(ложный hit — субстрок БАТМАНа)» — absent from the 10-10 cross-report and unverifiable
from Rubanova's 2020 ВКР (predates СИС-2024); the АТМАН dictionary-absence example itself is kept
and re-sourced to the cross-report census row (атман, OUT, 5 710 НКРЯ).
