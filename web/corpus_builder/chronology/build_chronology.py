#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_chronology.py — crosswalk corpus texts onto a chronological spine.

Produces texts_chronology.json: the data layer for a chronology index page
(in the spirit of dharmamitra's sanskrit_chronology_interactive.html).

DATE SOURCE — we do NOT re-date anything. All dates come from VisualDCS:
  ../../../../VisualDCS/visual/dcs_scatter.json   (85 individually dated texts)
  ../../../../VisualDCS/visual/dcs_genres.json    (18 period/genre buckets)

Matching policy, in priority order, per the agreed rule
("most rows get a DCS date for free; the residue inherits its bucket's date"):
  1. dcs-exact   — work name matches a dated DCS text  -> that text's date
  2. dcs-bucket  — no exact hit, but the work's period is known -> bucket date
  3. manual      — author-datable medieval work where the bucket would mislead
                   (e.g. Abhinavagupta ~1000); flagged, scholarly consensus date
  4. (none)      — reference works (dictionaries) and modern studies/translations
                   get date_ce=null and are excluded from the timeline

Two corpora are covered:
  parallel-ru  — the verse-aligned Sanskrit-Russian parallel corpus
                 (samskrtam.ru/parallel-corpus); driven by conversion_report.json
  wisdomlib-en — the 848-text Sanskrit-English corpus (books_full.jsonl)
"""
import sys, os, re, json, unicodedata
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
CB   = os.path.normpath(os.path.join(HERE, '..'))                  # corpus_builder
GH   = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))# GitHub root
DCS_SCATTER = os.path.join(GH, 'VisualDCS', 'visual', 'dcs_scatter.json')
DCS_GENRES  = os.path.join(GH, 'VisualDCS', 'visual', 'dcs_genres.json')
CONV_REPORT = os.path.join(CB, 'conversion_report.json')
BOOKS_FULL  = os.path.join(CB, 'wisdomlib', 'books_full.jsonl')

OUT_JSON   = os.path.join(HERE, 'texts_chronology.json')
OUT_REPORT = os.path.join(HERE, 'chronology_report.md')
OUT_HTML   = os.path.join(HERE, 'index.html')


def fold(s):
    """Diacritic-insensitive, punctuation-free lowercase key for name matching."""
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]', '', s.lower())


# ---------------------------------------------------------------- DCS date source
def load_dcs():
    scatter = json.load(open(DCS_SCATTER, encoding='utf-8'))
    genres  = json.load(open(DCS_GENRES, encoding='utf-8'))
    by_name = {}                       # fold(name) -> {date, genre, name}
    for r in scatter:
        k = fold(r['n'])
        if k and k not in by_name:
            by_name[k] = {'date': r['d'], 'genre': r['g'], 'name': r['n'].strip()}
    bucket = {g: int(round(v['date'])) for g, v in genres.items()}
    return by_name, bucket


# ---------------------------------------------------------------- corpus A registry
# Multi-file works whose slugs carry a leading "NN_" or a translator suffix are
# collapsed to a single group. Order matters: first matching rule wins.
GROUP_RULES = [
    (re.compile(r'^\d+_rigveda$'),            'rigveda'),
    (re.compile(r'^\d+_atharvaveda$'),        'atharvaveda'),
    (re.compile(r'^\d+_mahabharata-'),        'mahabharata'),
    (re.compile(r'^\d+_ramayana-'),           'ramayana'),
    (re.compile(r'^bhagavadgit'),             'bhagavadgita'),
    (re.compile(r'^buddhacharita'),           'buddhacarita'),
    (re.compile(r'^shatakatrayam'),           'shatakatraya'),
    (re.compile(r'^yoga-sutry'),              'yogasutra'),
    (re.compile(r'^shiva-sutry'),             'shivasutra'),
]

# group -> presentation + how to date it.
#   dcs   : DCS text name to look up (-> dcs-exact)
#   bucket: DCS genre bucket name    (-> dcs-bucket)
#   manual: (date_ce, period)        (-> manual, author-datable)
#   kind  : primary | commentary | historical-source
GROUPS = {
    # --- Veda --------------------------------------------------------------
    'rigveda':      dict(title='Ṛgveda',                 dcs='Ṛgveda',                       kind='primary'),
    'atharvaveda':  dict(title='Atharvaveda (Śaunaka)',  dcs='Atharvaveda Śaunaka)',         kind='primary'),
    # --- Epic --------------------------------------------------------------
    'mahabharata':  dict(title='Mahābhārata',            dcs='Mahābhārata',                  kind='primary'),
    'ramayana':     dict(title='Rāmāyaṇa',               dcs='Rāmāyaṇa',                     kind='primary'),
    'bhagavadgita': dict(title='Bhagavadgītā',           manual=(0, 'Epic'),                 kind='primary'),
    # --- Kāvya / classical poetry -----------------------------------------
    'kumarasambhava':           dict(title='Kumārasaṃbhava',     dcs='Kumārasaṃbhava',  kind='primary'),
    'megha-duta':               dict(title='Meghadūta',          dcs='Meghadūta',       kind='primary'),
    'raghuvamsha':              dict(title='Raghuvaṃśa',         bucket='Kāvya',        kind='primary'),
    'amaru-shataka':            dict(title='Amaruśataka',        dcs='Amaruśataka',     kind='primary'),
    'shatakatraya':             dict(title='Śatakatraya (Bhartṛhari)', dcs='Śatakatraya', kind='primary'),
    'gitagovinda':              dict(title='Gītagovinda',        dcs='Gītagovinda',     kind='primary'),
    'buddhacarita':             dict(title='Buddhacarita',       dcs='Buddhacarita',    kind='primary'),
    'chaurapanchashika':        dict(title='Caurapañcāśikā',     bucket='Kāvya',        kind='primary'),
    'shukasaptati':             dict(title='Śukasaptati',        dcs='Śukasaptati',     kind='primary'),
    # --- Śāstra / Sūtra ----------------------------------------------------
    'kama-sutra':               dict(title='Kāmasūtra',          dcs='Kāmasūtra',       kind='primary'),
    'manavadharmashastra':      dict(title='Mānavadharmaśāstra (Manusmṛti)', dcs='Manusmṛti', kind='primary'),
    'sankhya-karika':           dict(title='Sāṃkhyakārikā',      dcs='Sāṃkhyakārikābhāṣya', kind='primary'),
    'nyaya-bhashya':            dict(title='Nyāyabhāṣya',        bucket='Philosophy',   kind='primary'),
    'yogasutra':                dict(title='Yogasūtra (with bhāṣya)', dcs='Yogasūtrabhāṣya', kind='primary'),
    'hatha-yoga-pradipika':     dict(title='Haṭhayogapradīpikā', manual=(1400, 'Tantra/Āgama'), kind='primary'),
    'vedanga_jyotisha':         dict(title='Vedāṅgajyotiṣa',     manual=(-400, 'Vedic Saṃhitā'), kind='primary'),
    'shivasutra':               dict(title='Śivasūtra (Kashmir Śaivism)', manual=(850, 'Philosophy'), kind='primary'),
    # --- Purāṇa ------------------------------------------------------------
    'vishnu-purana':            dict(title='Viṣṇupurāṇa',        dcs='Viṣṇupurāṇa',     kind='primary'),
    'devi-gita':                dict(title='Devīgītā',           bucket='Purāṇa',       kind='primary'),
    # --- Medieval philosophical commentaries (author-datable) -------------
    'paramarthasara-abhinavagupta':   dict(title='Paramārthasāra (Abhinavagupta)',      manual=(1000, 'Philosophy'), kind='commentary'),
    'gitarthasamgraha-abhinavagupta': dict(title='Gītārthasaṃgraha (Abhinavagupta)',    manual=(1000, 'Philosophy'), kind='commentary'),
    'gitartha-samgraha_yamunacharya': dict(title='Gītārthasaṃgraha (Yāmunācārya)',      manual=(1050, 'Philosophy'), kind='commentary'),
    'ramanuja_gitabhashya':           dict(title='Gītābhāṣya (Rāmānuja)',               manual=(1100, 'Philosophy'), kind='commentary'),
    'vedartha-samgraha_ramanuja':     dict(title='Vedārthasaṃgraha (Rāmānuja)',         manual=(1100, 'Philosophy'), kind='commentary'),
    'pratyabhijna-hridaya_kshemaraja':dict(title='Pratyabhijñāhṛdaya (Kṣemarāja)',      manual=(1050, 'Philosophy'), kind='commentary'),
    # --- Historical source -------------------------------------------------
    'biruni':                   dict(title="al-Bīrūnī, India (Taḥqīq mā li-l-Hind)", manual=(1030, 'Other'), kind='historical-source'),
}

# Upaniṣads: DCS dates only the four below individually; the rest inherit the
# Upaniṣad bucket (-330). conf=low marks the minor/sectarian (later, CE) ones.
UPANISHADS = {
    'br-up':   ('Bṛhadāraṇyaka Upaniṣad', 'Bṛhadāraṇyakopaniṣad', 'high'),
    'ch-up':   ('Chāndogya Upaniṣad',     'Chāndogyopaniṣad',     'high'),
    'shv-up':  ('Śvetāśvatara Upaniṣad',  'Śvetāśvataropaniṣad',  'high'),
    'kat-up':  ('Kaṭha Upaniṣad',         'Kaṭhopaniṣad',         'high'),
    'ait-up':  ('Aitareya Upaniṣad',  None, 'med'),
    'tai-up':  ('Taittirīya Upaniṣad', None, 'med'),
    'kena-up': ('Kena Upaniṣad',      None, 'med'),
    'isha-up': ('Īśa Upaniṣad',       None, 'med'),
    'mun-up':  ('Muṇḍaka Upaniṣad',   None, 'med'),
    'man-up':  ('Māṇḍūkya Upaniṣad',  None, 'med'),
    'pr-up':   ('Praśna Upaniṣad',    None, 'med'),
    'kau-up':  ('Kauṣītaki Upaniṣad', None, 'med'),
    'mai-up':  ('Maitrāyaṇī Upaniṣad', None, 'med'),
    'sub-up':  ('Subāla Upaniṣad',    None, 'low'),
    'jab-up':  ('Jābāla Upaniṣad',    None, 'low'),
    'jabala-up':('Jābāla Upaniṣad (var.)', None, 'low'),
    'kai-up':  ('Kaivalya Upaniṣad',  None, 'low'),
    'kan-up':  ('Kaṇṭhaśruti Upaniṣad', None, 'low'),
    'atma-up': ('Ātmā Upaniṣad',      None, 'low'),
    'nr-up':   ('Nṛsiṃhatāpanīya Upaniṣad', None, 'low'),
    'rampt-up':('Rāmatāpanīya Upaniṣad', None, 'low'),
    'vajs-up': ('Vajrasūcī Upaniṣad', None, 'low'),
    'yotat-up':('Yogatattva Upaniṣad', None, 'low'),
    'mnar-up': ('Mahānārāyaṇa Upaniṣad', None, 'low'),
    'pai-up':  ('Paiṅgala Upaniṣad',  None, 'low'),
    'chag-up': ('Chāgaleya Upaniṣad', None, 'low'),
    'brb-up':  ('Brahmabindu Upaniṣad', None, 'low'),
}

# Modern scholarship / translations / readers in the "prose" group, plus all
# dictionaries: not datable as ancient Sanskrit texts -> excluded from timeline.
MODERN_PROSE = {
    'erman-temkin', 'frish', 'iliada_gnedich', 'induizm-dzhaynizm-sikkhizm',
    'kommentarii-k-makhabkharate', 'mify-drind', 'mify_759_ind', 'pandey',
    'stati-makhabkharaty', 'stepanyants', 'syrkin_tom_1_utf',
    'ukazateli-makhabkharaty',
    'yoga-bessmertie-i-cvoboda-mircha-eliade-per-pakhomova',
}


def group_of(slug):
    for rx, g in GROUP_RULES:
        if rx.match(slug):
            return g
    return slug


def date_for(spec, dcs_by_name, bucket):
    """Resolve a GROUPS/UPANISHADS spec to (date, period, dcs_match, method, conf)."""
    if 'dcs' in spec:
        k = fold(spec['dcs'])
        hit = dcs_by_name.get(k)
        if hit:
            return hit['date'], hit['genre'], hit['name'], 'dcs-exact', 'high'
        # name we expected isn't in DCS after all -> fall through to bucket if given
    if 'manual' in spec:
        d, p = spec['manual']
        return d, p, None, 'manual', spec.get('conf', 'med')
    if 'bucket' in spec:
        b = spec['bucket']
        return bucket.get(b), b, None, 'dcs-bucket', 'low'
    return None, None, None, 'unresolved', 'low'


# ---------------------------------------------------------------- corpus A build
def build_corpus_a(dcs_by_name, bucket):
    conv = json.load(open(CONV_REPORT, encoding='utf-8'))
    # collapse to groups so the 18 parvas / 10 RV maṇḍalas / 12 Gītās become one row
    seen = {}
    rows = []
    for s in conv['sources']:
        slug = s['slug']
        structure = s.get('structure')
        ru_title = s.get('filename', '')
        g = group_of(slug)

        # dictionaries -> reference
        if structure == 'dictionary':
            rows.append(dict(corpus='parallel-ru', slug=slug, group='dictionary',
                             title=ru_title, ru_title=ru_title, date_ce=None,
                             period='Reference', dcs_match=None, method='n/a',
                             kind='dictionary', confidence='n/a'))
            continue
        # modern studies / translations -> excluded from timeline
        if slug in MODERN_PROSE:
            rows.append(dict(corpus='parallel-ru', slug=slug, group='modern',
                             title=ru_title, ru_title=ru_title, date_ce=None,
                             period='Modern scholarship', dcs_match=None, method='n/a',
                             kind='modern-study', confidence='n/a'))
            continue
        # Upaniṣads
        if slug in UPANISHADS:
            title, dcs_name, conf = UPANISHADS[slug]
            if dcs_name:
                hit = dcs_by_name[fold(dcs_name)]
                d, p, m, meth = hit['date'], hit['genre'], hit['name'], 'dcs-exact'
            else:
                d, p, m, meth = bucket['Upaniṣad'], 'Upaniṣad', None, 'dcs-bucket'
            rows.append(dict(corpus='parallel-ru', slug=slug, group=slug,
                             title=title, ru_title=ru_title, date_ce=d, period=p,
                             dcs_match=m, method=meth, kind='primary', confidence=conf))
            continue
        # known primary-text groups (collapsed)
        if g in GROUPS:
            if g in seen:
                seen[g]['members'].append(slug)   # already emitted; just record member
                continue
            spec = GROUPS[g]
            d, p, m, meth, conf = date_for(spec, dcs_by_name, bucket)
            row = dict(corpus='parallel-ru', slug=g, group=g, title=spec['title'],
                       ru_title=ru_title, date_ce=d, period=p, dcs_match=m,
                       method=meth, kind=spec['kind'], confidence=conf, members=[slug])
            seen[g] = row
            rows.append(row)
            continue
        # anything left over -> flag for manual review
        rows.append(dict(corpus='parallel-ru', slug=slug, group=g, title=ru_title or slug,
                         ru_title=ru_title, date_ce=None, period=None, dcs_match=None,
                         method='UNRESOLVED', kind='unknown', confidence='low'))
    return rows


# ---------------------------------------------------------------- corpus B build
# Title fragments that map a wisdomlib entry to a dated DCS text. Kept small and
# high-precision: corpus B is overwhelmingly modern English books/essays, so we
# only assign a date on a confident primary-text hit and leave the rest undated.
WISDOM_HINTS = [
    ('rgveda', 'Ṛgveda'), ('rigveda', 'Ṛgveda'),
    ('atharvaveda', 'Atharvaveda Śaunaka)'), ('atharva veda', 'Atharvaveda Śaunaka)'),
    ('mahabharata', 'Mahābhārata'),
    ('ramayana', 'Rāmāyaṇa'),
    ('manusmrti', 'Manusmṛti'), ('manu smriti', 'Manusmṛti'), ('laws of manu', 'Manusmṛti'),
    ('kamasutra', 'Kāmasūtra'), ('kama sutra', 'Kāmasūtra'),
    ('arthashastra', 'Arthaśāstra'), ('arthasastra', 'Arthaśāstra'),
    ('amarakosa', 'Amarakośa'), ('amarakosha', 'Amarakośa'),
    ('meghaduta', 'Meghadūta'),
    ('kumarasambhava', 'Kumārasaṃbhava'),
    ('gitagovinda', 'Gītagovinda'),
    ('buddhacarita', 'Buddhacarita'), ('buddhacharita', 'Buddhacarita'),
    ('bhagavatapurana', 'Bhāgavatapurāṇa'), ('bhagavata purana', 'Bhāgavatapurāṇa'),
    ('vishnupurana', 'Viṣṇupurāṇa'), ('visnupurana', 'Viṣṇupurāṇa'),
    ('agnipurana', 'Agnipurāṇa'),
    ('garudapurana', 'Garuḍapurāṇa'),
    ('skandapurana', 'Skandapurāṇa'),
    ('kurmapurana', 'Kūrmapurāṇa'),
    ('lingapurana', 'Liṅgapurāṇa'),
    ('matsyapurana', 'Matsyapurāṇa'),
    ('kalikapurana', 'Kālikāpurāṇa'),
    ('hitopadesa', 'Hitopadeśa'), ('hitopadesha', 'Hitopadeśa'),
    ('kathasaritsagara', 'Kathāsaritsāgara'),
    ('carakasamhita', 'Carakasaṃhitā'), ('caraka samhita', 'Carakasaṃhitā'),
    ('susrutasamhita', 'Suśrutasaṃhitā'), ('sushruta samhita', 'Suśrutasaṃhitā'),
    ('astangahrdaya', 'Aṣṭāṅgahṛdayasaṃhitā'), ('astanga hrdaya', 'Aṣṭāṅgahṛdayasaṃhitā'),
    ('bhavaprakasa', 'Bhāvaprakāśa'),
    ('yajnavalkya', 'Yājñavalkyasmṛti'),
    ('naradasmrti', 'Nāradasmṛti'),
    ('lalitavistara', 'Lalitavistara'),
    ('divyavadana', 'Divyāvadāna'),
    ('bodhicaryavatara', 'Bodhicaryāvatāra'),
    ('natyasastra', 'Nāṭyaśāstra'), ('natya shastra', 'Nāṭyaśāstra'),
    ('kiratarjuniya', 'Kirātārjunīya'),
    ('dasakumaracarita', 'Daśakumāracarita'),
    ('sankhyakarika', 'Sāṃkhyakārikābhāṣya'), ('samkhyakarika', 'Sāṃkhyakārikābhāṣya'),
    ('brhadaranyaka', 'Bṛhadāraṇyakopaniṣad'),
    ('chandogya', 'Chāndogyopaniṣad'),
    ('svetasvatara', 'Śvetāśvataropaniṣad'),
    ('katha upanisad', 'Kaṭhopaniṣad'),
]


def build_corpus_b(dcs_by_name):
    rows = []
    hints = [(h, fold(name)) for h, name in WISDOM_HINTS]
    with open(BOOKS_FULL, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            b = json.loads(line)
            title = b.get('title', '')
            tf = fold(title)
            matched = None
            for hint, namekey in hints:
                if fold(hint) in tf:
                    matched = dcs_by_name.get(namekey)
                    if matched:
                        break
            if matched:
                rows.append(dict(corpus='wisdomlib-en', slug=b['slug'], group=matched['name'],
                                 title=title, date_ce=matched['date'], period=matched['genre'],
                                 dcs_match=matched['name'], method='dcs-exact',
                                 kind='primary', confidence='med',
                                 source_lang=b.get('source_lang'), words=b.get('words')))
            else:
                rows.append(dict(corpus='wisdomlib-en', slug=b['slug'], group=None,
                                 title=title, date_ce=None, period=None, dcs_match=None,
                                 method='n/a', kind='modern-or-unmatched', confidence='n/a',
                                 source_lang=b.get('source_lang'), words=b.get('words')))
    return rows


# ---------------------------------------------------------------- index page
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chronology of the Sanskrit corpus — samskrtam.ru</title>
<style>
  :root { --bg:#fbfaf7; --ink:#2b2620; --mut:#8a8276; --line:#e4ded2; }
  * { box-sizing:border-box; }
  body { margin:0; font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;
         background:#fbfaf7; color:#2b2620; }
  header { padding:22px 26px 10px; }
  h1 { margin:0 0 4px; font-size:22px; font-weight:650; }
  .sub { color:#6f685c; font-size:13.5px; max-width:760px; }
  .sub a { color:#9a5b2a; }
  .controls { padding:10px 26px 4px; display:flex; flex-wrap:wrap; gap:8px 18px;
              align-items:center; border-bottom:1px solid var(--line); }
  .controls label { font-size:13px; color:#534c40; cursor:pointer; user-select:none; }
  .seg button { font:13px inherit; border:1px solid #d8d1c2; background:#fff;
                padding:4px 11px; cursor:pointer; }
  .seg button:first-child { border-radius:6px 0 0 6px; }
  .seg button:last-child { border-radius:0 6px 6px 0; border-left:none; }
  .seg button.on { background:#9a5b2a; color:#fff; border-color:#9a5b2a; }
  #plot { width:100%; display:block; }
  .lane-bg:nth-child(even) { fill:#f3efe6; }
  .lane-lbl { font-size:11.5px; fill:#6f685c; }
  .axis { stroke:#cfc7b6; stroke-width:1; }
  .axis-lbl { font-size:11px; fill:#8a8276; text-anchor:middle; }
  circle.dot { stroke:#fff; stroke-width:0.8; cursor:pointer; }
  circle.dot.lc { stroke-dasharray:1.5 1.2; opacity:.78; }
  .tip { position:fixed; pointer-events:none; background:#2b2620; color:#fdfbf6;
         padding:7px 10px; border-radius:6px; font-size:12.5px; max-width:300px;
         opacity:0; transition:opacity .08s; z-index:9; }
  .tip b { color:#f1c79a; }
  table { border-collapse:collapse; width:100%; font-size:13px; }
  th,td { text-align:left; padding:5px 10px; border-bottom:1px solid var(--line);
          vertical-align:top; }
  th { position:sticky; top:0; background:#f3efe6; cursor:pointer; font-weight:600; }
  .wrap { padding:14px 26px 60px; }
  .pill { font-size:11px; padding:1px 7px; border-radius:10px; background:#eee5d4; color:#6a4a28; }
  .muted { color:#9a9388; }
  td.n { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
  .conf-low { color:#b06a2a; } .conf-high { color:#3c7a3c; }
</style>
</head>
<body>
<header>
  <h1>Chronology of the Sanskrit corpus</h1>
  <div class="sub">Every datable text in the
    <a href="https://samskrtam.ru/parallel-corpus/">Параллельный санскритско-русский корпус</a>
    and the Sanskrit&ndash;English corpus, placed on a timeline.
    Dates are taken from the <b>VisualDCS</b> chronology (not re-derived):
    a text either carries its own DCS date, inherits its period bucket's date,
    or &mdash; for author-datable medieval works &mdash; a flagged scholarly date.
    Classification scheme after
    <a href="https://dharmamitra.github.io/sanskrit-dating/sanskrit_chronology_interactive.html">DharmaMitra&nbsp;sanskrit-dating</a>.
  </div>
</header>
<div class="controls">
  <span class="seg" id="corpus">
    <button data-v="both" class="on">Both corpora</button>
    <button data-v="parallel-ru">Sanskrit&ndash;Russian</button>
    <button data-v="wisdomlib-en">Sanskrit&ndash;English</button>
  </span>
  <label><input type="checkbox" id="lowconf" checked> show low-confidence dates</label>
  <span style="flex:1"></span>
  <span class="muted" id="count"></span>
</div>
<svg id="plot"></svg>
<div class="wrap"><table id="tbl"><thead><tr>
  <th data-k="date_ce" class="n">Date</th><th data-k="period">Period</th>
  <th data-k="title">Work</th><th data-k="corpus">Corpus</th>
  <th data-k="method">Source of date</th><th data-k="confidence">Conf.</th>
</tr></thead><tbody></tbody></table></div>
<div class="tip" id="tip"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
const DB = JSON.parse(document.getElementById('data').textContent);
const PERIODS = DB.periods.map(p=>p.period);
const PAL = ['#5b8db8','#6aa0c0','#7d9b6a','#b5a23e','#c98a3e','#c2693e','#b04d54',
             '#9a5b8a','#7a6aa0','#4f8a86','#a08a5a','#8a8276','#b07a3a','#6a8a5a',
             '#9a9aa0','#a06a4a','#8a5a7a','#7a5a4a'];
const COLOR = Object.fromEntries(PERIODS.map((p,i)=>[p,PAL[i%PAL.length]]));
const LANE = Object.fromEntries(PERIODS.map((p,i)=>[p,i]));
let corpus='both', showLow=true, sortK='date_ce', sortDir=1;

const dated = DB.texts.filter(t=>t.date_ce!==null);
function visible(){
  return dated.filter(t=>(corpus==='both'||t.corpus===corpus)
                       &&(showLow||t.confidence!=='low'));
}
const fmtDate = d => d<0 ? (-d)+' BCE' : (d===0?'c. 0':d+' CE');

function draw(){
  const rows=visible();
  const W=Math.max(document.body.clientWidth,720), PADL=150, PADR=24, PADT=14;
  const laneH=26, H=PADT + PERIODS.length*laneH + 34;
  const ds=rows.map(r=>r.date_ce), dmin=Math.min(-1400,...ds), dmax=Math.max(1600,...ds);
  const x=d=> PADL + (d-dmin)/(dmax-dmin)*(W-PADL-PADR);
  const svg=document.getElementById('plot'); svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  svg.setAttribute('height',H);
  let s='';
  PERIODS.forEach((p,i)=>{
    const y=PADT+i*laneH;
    s+=`<rect class="lane-bg" x="0" y="${y}" width="${W}" height="${laneH}"></rect>`;
    s+=`<text class="lane-lbl" x="10" y="${y+laneH/2+4}">${p}</text>`;
  });
  for(let yr=-1500;yr<=1600;yr+=500){ if(yr<dmin||yr>dmax)continue;
    s+=`<line class="axis" x1="${x(yr)}" y1="${PADT}" x2="${x(yr)}" y2="${PADT+PERIODS.length*laneH}"></line>`;
    s+=`<text class="axis-lbl" x="${x(yr)}" y="${H-12}">${fmtDate(yr)}</text>`;
  }
  // jitter overlapping dots within a lane
  const used={};
  rows.forEach(r=>{
    const lane=LANE[r.period]??0, y0=PADT+lane*laneH+laneH/2;
    const key=r.period+'|'+Math.round(x(r.date_ce)/7);
    const n=(used[key]=(used[key]||0)+1);
    const off=((n%2)?1:-1)*Math.ceil(n/2)*4.2;
    const yy=Math.max(PADT+lane*laneH+5,Math.min(PADT+lane*laneH+laneH-5,y0+off));
    const lc=r.confidence==='low'?' lc':'';
    s+=`<circle class="dot${lc}" data-i="${dated.indexOf(r)}" cx="${x(r.date_ce).toFixed(1)}" cy="${yy.toFixed(1)}" r="5" fill="${COLOR[r.period]||'#888'}"></circle>`;
  });
  svg.innerHTML=s;
  document.getElementById('count').textContent=
    `${rows.length} dated works shown · ${dated.length} total`;
  drawTable(rows);
}
function drawTable(rows){
  rows=rows.slice().sort((a,b)=>{
    let x=a[sortK],y=b[sortK]; if(x===null)x=1e9; if(y===null)y=1e9;
    return (x>y?1:x<y?-1:0)*sortDir;
  });
  const tb=document.querySelector('#tbl tbody');
  tb.innerHTML=rows.map(r=>`<tr>
    <td class="n">${fmtDate(r.date_ce)}</td>
    <td><span class="pill" style="background:${(COLOR[r.period]||'#999')}22;color:${COLOR[r.period]||'#666'}">${r.period}</span></td>
    <td>${r.title}${r.dcs_match&&r.dcs_match!==r.title?` <span class="muted">→ ${r.dcs_match}</span>`:''}</td>
    <td>${r.corpus==='parallel-ru'?'SA–RU':'SA–EN'}</td>
    <td class="muted">${r.method}</td>
    <td class="conf-${r.confidence}">${r.confidence}</td></tr>`).join('');
}
// interactions
const tip=document.getElementById('tip');
document.getElementById('plot').addEventListener('mousemove',e=>{
  const c=e.target.closest('circle.dot');
  if(!c){tip.style.opacity=0;return;}
  const r=dated[+c.dataset.i];
  tip.innerHTML=`<b>${r.title}</b><br>${fmtDate(r.date_ce)} · ${r.period}<br>`+
    `<span style="opacity:.7">${r.method}${r.dcs_match?' · '+r.dcs_match:''} · ${r.confidence} conf.</span>`;
  tip.style.left=Math.min(e.clientX+14,innerWidth-310)+'px';
  tip.style.top=(e.clientY+16)+'px'; tip.style.opacity=1;
});
document.getElementById('plot').addEventListener('mouseleave',()=>tip.style.opacity=0);
document.querySelectorAll('#corpus button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('#corpus button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); corpus=b.dataset.v; draw();
});
document.getElementById('lowconf').onchange=e=>{showLow=e.target.checked;draw();};
document.querySelectorAll('#tbl th').forEach(th=>th.onclick=()=>{
  const k=th.dataset.k; sortDir=(sortK===k)?-sortDir:1; sortK=k; drawTable(visible());
});
addEventListener('resize',draw);
draw();
</script>
</body>
</html>
"""


def write_html(out):
    payload = json.dumps({'periods': out['periods'], 'texts': out['texts']},
                         ensure_ascii=False)
    payload = payload.replace('</', '<\\/')   # safe inside <script>
    open(OUT_HTML, 'w', encoding='utf-8').write(
        HTML_TEMPLATE.replace('__DATA__', payload))


# ---------------------------------------------------------------- main
def main():
    dcs_by_name, bucket = load_dcs()
    a = build_corpus_a(dcs_by_name, bucket)
    b = build_corpus_b(dcs_by_name)

    periods = [dict(period=g, bucket_date=int(round(v))) for g, v in
               sorted(bucket.items(), key=lambda x: x[1])]

    out = dict(
        about=("Chronological crosswalk of the samskrtam.ru parallel corpus and the "
               "wisdomlib Sanskrit-English corpus onto VisualDCS dates. Dates are not "
               "re-derived: dcs-exact = the text's own DCS date; dcs-bucket = its period "
               "bucket's date; manual = author-datable medieval work (flagged)."),
        date_source='VisualDCS/visual/dcs_scatter.json + dcs_genres.json',
        periods=periods,
        texts=a + b,
    )
    json.dump(out, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    write_html(out)

    # ---- report
    from collections import Counter
    def tally(rows, field):
        return Counter(r.get(field) for r in rows)
    a_dated = [r for r in a if r['date_ce'] is not None]
    b_dated = [r for r in b if r['date_ce'] is not None]
    unresolved = [r for r in a if r['method'] == 'UNRESOLVED']

    L = []
    L.append('# Chronology crosswalk — build report\n')
    L.append(f'Date source: `VisualDCS/visual/dcs_scatter.json` (85 dated texts) '
             f'+ `dcs_genres.json` (18 period buckets).\n')
    L.append('## parallel-ru (samskrtam.ru parallel corpus)\n')
    L.append(f'- Source rows collapsed to **{len(a)} works** '
             f'(from 148 corpus files).')
    L.append(f'- **{len(a_dated)} dated** primary texts placed on the timeline.')
    L.append(f'- Method split: ' +
             ', '.join(f'`{k}`={v}' for k, v in tally(a, "method").most_common()))
    L.append(f'- Kind split: ' +
             ', '.join(f'`{k}`={v}' for k, v in tally(a, "kind").most_common()))
    if unresolved:
        L.append(f'- ⚠️ UNRESOLVED ({len(unresolved)}): ' +
                 ', '.join(r['slug'] for r in unresolved))
    L.append('')
    L.append('### Dated parallel-ru works (oldest first)\n')
    L.append('| date CE | period | work | method | conf |')
    L.append('|--:|---|---|---|---|')
    for r in sorted(a_dated, key=lambda x: x['date_ce']):
        L.append(f"| {r['date_ce']} | {r['period']} | {r['title']} | "
                 f"{r['method']} | {r['confidence']} |")
    L.append('')
    L.append('## wisdomlib-en (Sanskrit-English corpus)\n')
    L.append(f'- **{len(b)} entries** scanned; **{len(b_dated)} matched** a dated DCS text.')
    L.append(f'- The remainder are modern English books/essays/articles with no ancient '
             f'composition date (left undated by design).')
    if b_dated:
        L.append('')
        L.append('| date CE | period | wisdomlib title | DCS match |')
        L.append('|--:|---|---|---|')
        for r in sorted(b_dated, key=lambda x: (x['date_ce'], x['title'])):
            L.append(f"| {r['date_ce']} | {r['period']} | {r['title']} | {r['dcs_match']} |")
    open(OUT_REPORT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')

    # ---- console summary
    print(f"corpus A (parallel-ru): {len(a)} works, {len(a_dated)} dated, "
          f"{len(unresolved)} unresolved")
    print(f"corpus B (wisdomlib-en): {len(b)} entries, {len(b_dated)} dated")
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_REPORT}")


if __name__ == '__main__':
    main()
