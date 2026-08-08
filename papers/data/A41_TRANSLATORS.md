# A41 / Samudra — translator inventory (ship-all residual)

_Created: 08-08-2026 · Last updated: 08-08-2026_

**Policy:** MG 08-08-2026 (H2440) — **ship all** RU text for A41/A42 paths. This file **documents the different translators**; it is not a ship/no-ship gate.

**Machine twin:** [`A41_TRANSLATORS.tsv`](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_TRANSLATORS.tsv) (63 source rows · 19 distinct translator/credit strings).

Sources: committed `web/corpus_builder/*.meta.json` `credit` fields + [`A41_gita_editions.tsv`](https://github.com/gasyoun/SamudraManthanam/blob/main/papers/data/A41_gita_editions.tsv). Rows still `—` on the 131-source НКРЯ RIGHTS_TABLE lack a committed meta credit (H821 metadata-loss residual) — fill when meta is restored, not by guessing.

## Distinct translators / credits

| Translator / credit | # sources | Example slugs |
|---|--:|---|
| А. Игнатьев | 44 | `adbhuta-ramayana`, `bhagavata-purana`, `bhagavati-manasa-puja-stotra`, `brihannila-tantra`, … (+40) |
| П. А. Гринцер | 2 | `01_ramayana-balakanda`, `02_ramayana-ayodhyakanda` |
| А.А. Каменской и И.В. де Манциарли | 1 | `bhagavadgita-1914` |
| Б.Л.Смирнов | 1 | `bhagavadgita-smirnov` |
| В.Г.Эрман | 1 | `bhagavadgita-erman` |
| В.С. Семенцова, | 1 | `ramanuja_gitabhashya` |
| В.С.Семенцов | 1 | `bhagavadgita-sementsov` |
| Д. Бурба | 1 | `bhagavadgita-burba` |
| И. Д. Серебряков и др. | 1 | `kathasaritsagara` |
| Институт исследования санскрита | 1 | `bhagavadgity` |
| О.Н. Ерченков | 1 | `gitarthasamgraha-abhinavagupta` |
| П. А. Гринцер (атрибуция требует проверки) | 1 | `03_ramayana-aranyakanda` |
| Переводчик: А.А. Петров. | 1 | `bhagavadgita-1788` |
| Переводъ въ стихахъ А. П. Казначеевой | 1 | `bhagavadgita-1909` |
| Р.В. Псху | 1 | `gitartha-samgraha_yamunacharya` |
| Р.Т.Блиндерман | 1 | `bhagavadgita-radha` |
| Шайлендра Шарма | 1 | `bhagavadgita-sharma` |
| Шри Шримад А.Ч. Бхактиведанта Свами Прабхупада | 1 | `bhagavadgita-prabhupada` |
| Я. В. Васильков, С. Л. Невелева | 1 | `03_mahabharata-aranyakaparva` |

## Per-source table

| Slug | Translator | Role | Year | Title | Source |
|---|---|---|---|---|---|
| `01_ramayana-balakanda` | П. А. Гринцер | Перевод с санскрита, комментарий | 2006 | Рамаяна I (Балаканда) | meta.json |
| `02_ramayana-ayodhyakanda` | П. А. Гринцер | Перевод с санскрита, комментарий | 2006 | Рамаяна II (Айодхьяканда) | meta.json |
| `03_mahabharata-aranyakaparva` | Я. В. Васильков, С. Л. Невелева | Перевод с санскрита, предисловие и комментарий | 1987 | Махабхарата III (Араньякапарва) | meta.json |
| `03_ramayana-aranyakanda` | П. А. Гринцер (атрибуция требует проверки) | Перевод с санскрита | — | Рамаяна III (Араньяканда) | meta.json |
| `adbhuta-ramayana` | А. Игнатьев | Перевод с санскрита | — | Адбхута-Рамаяна | meta.json |
| `bhagavata-purana` | А. Игнатьев | Перевод с санскрита | — | Бхагавата-пурана (фрагменты) | meta.json |
| `bhagavati-manasa-puja-stotra` | А. Игнатьев | Перевод с санскрита | — | Гимн мысленного поклонения Бхагавати | meta.json |
| `brihannila-tantra` | А. Игнатьев | Перевод с санскрита | — | Бриханнила-тантра (избранное) | meta.json |
| `chinachara-tantra` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Чиначара-тантра | meta.json |
| `devi-purana` | А. Игнатьев | Перевод с санскрита | — | Деви-пурана | meta.json |
| `devibhagavata-purana` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | 2018 | Девибхагавата-пурана | meta.json |
| `devimahatmya` | А. Игнатьев | Перевод с санскрита | — | Деви-махатмья | meta.json |
| `guptasadhana-tantra` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Гуптасадхана-тантра | meta.json |
| `kadambara-svikarana-karika` | А. Игнатьев | Перевод с санскрита | — | Кадамбара-свикарана-карика | meta.json |
| `kadambara-svikarana-karika-literatura` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кадамбара-свикарана-карика: ЛИТЕРАТУРА | meta.json |
| `kadambara-svikarana-karika-ob-avtore` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кадамбара-свикарана-карика: Об авторе перевода | meta.json |
| `kadambara-svikarana-karika-preface` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кадамбара-свикарана-карика: Предисловие | meta.json |
| `kalika-purana` | А. Игнатьев | Перевод с санскрита | — | Калика-пурана | meta.json |
| `kama-samuha` | А. Игнатьев | Перевод с санскрита | — | Кама-самуха | meta.json |
| `kama-samuha-antologii` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кама-самуха: ИЗВЕСТНЫЕ АНТОЛОГИИ САНСКРИТСКОЙ ПОЭЗИИ | meta.json |
| `kama-samuha-istochniki` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кама-самуха: ИСТОЧНИКИ «КАМА-САМУХИ» | meta.json |
| `kama-samuha-literatura` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кама-самуха: ЛИТЕРАТУРА | meta.json |
| `kama-samuha-ob-avtore` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кама-самуха: Об авторе перевода | meta.json |
| `kama-samuha-preface` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кама-самуха: Предисловие | meta.json |
| `kama-samuha-slovar-flory` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кама-самуха: СЛОВАРЬ ФЛОРЫ И ФАУНЫ | meta.json |
| `kama-samuha-slovar-imen` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кама-самуха: СЛОВАРЬ ИМЕН | meta.json |
| `kama-samuha-slovar-predmetov` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кама-самуха: СЛОВАРЬ ПРЕДМЕТОВ И ТЕРМИНОВ | meta.json |
| `kama-samuha-slovar-toponimov` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Кама-самуха: СЛОВАРЬ ТОПОНИМОВ И ЭТНОНИМОВ | meta.json |
| `kathasaritsagara` | И. Д. Серебряков и др. | Перевод с санскрита | 1967 | Океан сказаний (Катхасаритсагара) | meta.json |
| `kularnava-tantra` | А. Игнатьев | Перевод с санскрита | — | Куларнава-тантра | meta.json |
| `linga-purana` | А. Игнатьев | Перевод с санскрита | — | Линга-пурана | meta.json |
| `mahabhagavata-purana` | А. Игнатьев | Перевод с санскрита | — | Махабхагавата-пурана | meta.json |
| `mahabharata-ignatiev-xvi-xviii-literatura` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Махабхарата XVI–XVIII (Игнатьев): БИБЛИОГРАФИЯ | meta.json |
| `mahabharata-ignatiev-xvi-xviii-ob-avtore` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Махабхарата XVI–XVIII (Игнатьев): Об авторе перевода | meta.json |
| `mahabharata-ignatiev-xvi-xviii-preface` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Махабхарата XVI–XVIII (Игнатьев): Предисловие | meta.json |
| `mahabharata-ignatiev-xvi-xviii-slovar-imen` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Махабхарата XVI–XVIII (Игнатьев): СЛОВАРЬ ИМЕН ЭПИЧЕСКИХ ПЕРСОНАЖЕЙ | meta.json |
| `mahabharata-ignatiev-xvi-xviii-slovar-predmetov` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Махабхарата XVI–XVIII (Игнатьев): СЛОВАРЬ ПРЕДМЕТОВ И ТЕРМИНОВ | meta.json |
| `mahabharata-mahaprasthanikaparva-ignatiev` | А. Игнатьев | Перевод с санскрита | — | Махабхарата XVII. Махапрастханика-парва | meta.json |
| `mahabharata-mausalaparva-ignatiev` | А. Игнатьев | Перевод с санскрита | — | Махабхарата XVI. Маусала-парва | meta.json |
| `mahabharata-svargarohanikaparva-ignatiev` | А. Игнатьев | Перевод с санскрита | — | Махабхарата XVIII. Сварга-арохана-парва | meta.json |
| `maya-tantra` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | 2023 | Майя-тантра | meta.json |
| `nilamata-purana` | А. Игнатьев | Перевод с санскрита | — | Ниламата-пурана | meta.json |
| `niruttara-tantra` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Нируттара-тантра | meta.json |
| `nirvana-tantra` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Нирвана-тантра | meta.json |
| `padma-purana` | А. Игнатьев | Перевод с санскрита | — | Падма-пурана (Джаландхара) | meta.json |
| `shaktisangama-tantra` | А. Игнатьев | Перевод с санскрита | — | Шактисангама-тантра (избранное) | meta.json |
| `yogini-tantra` | А. Игнатьев | Перевод с санскрита | — | Йогини-тантра | meta.json |
| `yoni-puja-texts` | А. Игнатьев | Перевод с санскрита | — | Тексты для йони-пуджи | meta.json |
| `yoni-tantra` | А. Игнатьев | Перевод с санскрита, предисловие и комментарий | — | Йони-тантра | meta.json |
| `bhagavadgita-1788` | Переводчик: А.А. Петров. | translation | 1788 | Bhagavadgītā · Переводчик: А.А. Петров. | A41_gita_editions.tsv |
| `bhagavadgita-1909` | Переводъ въ стихахъ А. П. Казначеевой | translation | 1909 | Bhagavadgītā · Переводъ въ стихахъ А. П. Казначеевой | A41_gita_editions.tsv |
| `bhagavadgita-1914` | А.А. Каменской и И.В. де Манциарли | translation | 1914 | Bhagavadgītā · А.А. Каменской и И.В. де Манциарли | A41_gita_editions.tsv |
| `bhagavadgita-smirnov` | Б.Л.Смирнов | translation | 1977 | Bhagavadgītā · Б.Л.Смирнов | A41_gita_editions.tsv |
| `bhagavadgita-sementsov` | В.С.Семенцов | translation | 1999 | Bhagavadgītā · В.С.Семенцов | A41_gita_editions.tsv |
| `bhagavadgita-erman` | В.Г.Эрман | translation | 2009 | Bhagavadgītā · В.Г.Эрман | A41_gita_editions.tsv |
| `bhagavadgita-burba` | Д. Бурба | translation | 2009 | Bhagavadgītā · Д. Бурба | A41_gita_editions.tsv |
| `bhagavadgita-prabhupada` | Шри Шримад А.Ч. Бхактиведанта Свами Прабхупада | translation | 1984 | Bhagavadgītā · Шри Шримад А.Ч. Бхактиведанта Свами Прабхупада | A41_gita_editions.tsv |
| `bhagavadgita-radha` | Р.Т.Блиндерман | translation | 2016 | Bhagavadgītā · Р.Т.Блиндерман | A41_gita_editions.tsv |
| `bhagavadgita-sharma` | Шайлендра Шарма | translation | 2015 | Bhagavadgītā · Шайлендра Шарма | A41_gita_editions.tsv |
| `bhagavadgity` | Институт исследования санскрита | translation | 2026 | Bhagavadgītā · Институт исследования санскрита | A41_gita_editions.tsv |
| `ramanuja_gitabhashya` | В.С. Семенцова, | translation | 2021 | Bhagavadgītā · В.С. Семенцова, | A41_gita_editions.tsv |
| `gitartha-samgraha_yamunacharya` | Р.В. Псху | translation | 2021 | Bhagavadgītā · Р.В. Псху | A41_gita_editions.tsv |
| `gitarthasamgraha-abhinavagupta` | О.Н. Ерченков | translation | 2008 | Bhagavadgītā · О.Н. Ерченков | A41_gita_editions.tsv |

_Dr. Mārcis Gasūns_
