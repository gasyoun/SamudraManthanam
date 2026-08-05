#!/usr/bin/env python3
"""Canonical JSONL -> app-ready corpus HTML (production emitter).

H534 Phase 3. Promotes ``render_for_reader.py`` (validation-only) to a full
emitter that writes the exact artifact the desktop reader «Пахтанье океана»
loads from ``Data/`` and the web platform ingests: the ``<!-- Title --!>``
first line, the shared head/CSS/Yandex-Metrika wrapper, the
``chapters -> chapter -> citation_block`` body (``chapter_block iast`` +
``chapter_block translation`` + ``comments``), plus the ``.no_tags`` and
``.html.meta.json`` sidecars.

Output granularity is a parameter and BOTH forms are first-class house
conventions:

* ``--split skandha``  — one ``<slug>-<skandha>.html`` per skandha (~12 files).
* ``--combined``       — one ``<slug>.html`` for the whole work.

Every emitted filename is appended (idempotently) to ``Programdata/data.txt``.

The emitter is source-agnostic: it renders whatever segments a group carries.
A group with only a ``ru`` segment renders Russian-only (the sanctioned
DBhP fallback where no confident Sanskrit alignment exists); a group that also
carries an ``sa`` segment (added by ``align_sanskrit.py``) renders the IAST
pane above it, exactly like ``devi-gita.html``.

Usage:
    python web/corpus_builder/build_corpus_html.py \
        --jsonl web/corpus_builder/jsonl/devibhagavata-purana_s1.aligned.jsonl \
        --report web/corpus_builder/jsonl/devibhagavata-purana_s1.report.json \
        --meta   web/corpus_builder/devibhagavata-purana.meta.json \
        --data-dir Index/lib/x86_64-win64/Data \
        --data-txt Index/lib/x86_64-win64/Programdata/data.txt \
        --split skandha --combined
"""
from __future__ import annotations

import argparse
import html as _htmllib
import json
import re
from pathlib import Path

import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_STRIP_TAGS = re.compile(r"<[^>]+>")
_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)

# Roman numerals for skandha display in the range-div title (I..XII).
_ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
          "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]

# Head template. {title} = <title> + first-line comment text; {counter} =
# Yandex-Metrika id (reuse the corpus-wide counter). CSS + favicon are shared
# assets already shipped under Data/src/.
_HEAD = (
    '<html><head> <title>{title}</title> '
    '<meta http-equiv="content-type" content="text/html; charset=UTF-8" /> '
    '<link rel="stylesheet" href="./src/style.css"> '
    '<link rel="shortcut icon" href="./src/favicon/dg.ico" type="image/xicon"> '
    '<link rel="icon" href="./src/favicon/dg.ico" type="image/xicon">'
    '<!-- Yandex.Metrika counter --> <script type="text/javascript" > '
    '(function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}}; '
    'm[i].l=1*new Date(); for (var j = 0; j < document.scripts.length; j++) '
    '{{if (document.scripts[j].src === r) {{ return; }}}} '
    'k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,'
    'a.parentNode.insertBefore(k,a)}}) (window, document, "script", '
    '"https://mc.yandex.ru/metrika/tag.js", "ym"); ym({counter}, "init", '
    '{{ clickmap:true, trackLinks:true, accurateTrackBounce:true, webvisor:true, '
    'ecommerce:"dataLayer" }});</script><noscript><div><img '
    'src="https://mc.yandex.ru/watch/{counter}" style="position:absolute; '
    'left:-9999px;" alt="" /></div></noscript><!-- /Yandex.Metrika counter -->'
    '</head><body>'
)
_YM_COUNTER = "18296974"


def strip_tags(s: str) -> str:
    s = _BR.sub(" ", s)
    s = _STRIP_TAGS.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def load_jsonl(path: Path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                if not rec.get("deleted"):
                    out.append(rec)
    return out


def _headers_block(meta: dict, skandha: int | None) -> str:
    """The top matter (title / credit / imprint) as in devi-gita.html."""
    title_main = meta.get("title_display", meta.get("title_en", ""))
    role = meta.get("credit_role", "")
    credit = meta.get("credit", "")
    year = meta.get("year", "")
    imprint = meta.get("imprint", "")
    sk_line = f"Скандха {skandha}" if skandha else ""
    parts = [f'<div class="header header_1">{_htmllib.escape(title_main)}</div>',
             '<div style="height: 30px"></div>']
    if role:
        parts.append(f'<div class="header header_4">{_htmllib.escape(role)}</div>')
    if credit:
        parts.append(f'<div class="header header_5">{_htmllib.escape(credit)}</div>')
    loc = ", ".join([p for p in [imprint, str(year) if year else ""] if p])
    if loc:
        parts.append(f'<div class="header header_5">{_htmllib.escape(loc)}</div>')
    if sk_line:
        parts.append(f'<div class="header header_2">{_htmllib.escape(sk_line)}</div>')
    return '<div class="headers">' + "".join(parts) + '</div>'


def _range_div(meta: dict, skandha: int | None, chapter: int, verse: str,
               fn_label: str) -> str:
    sk_seg = f'{_ROMAN[skandha]}. ' if skandha else ''
    title = f'{meta.get("title_display", "")} {sk_seg}{chapter}. {verse}'
    src = f'{meta.get("title_display","")} ' \
          f'({meta.get("credit","")}, {meta.get("year","")}): {fn_label}'
    return (f'<div class="range" title="{_htmllib.escape(title)}" '
            f'id="{_htmllib.escape(src)}">{fn_label}</div>')


def render_citation_block(group_recs: list[dict], meta: dict) -> str:
    """Render one verse group as a citation_block, mirroring devi-gita.html."""
    recs = sorted(group_recs, key=lambda r: r.get("seq", 0))
    passage = recs[0]["passage"]
    # Flat single-book works (2-part "CHAPTER.VERSE" passage ids) carry no
    # "skandha" field at all -- None here, not a value derived from the
    # passage (whose first component is the CHAPTER for these works, and
    # was previously misread as a skandha number, overflowing _ROMAN's
    # I..XX table on any single-book work past chapter 20 -- H1438 Wave B).
    sk_raw = recs[0].get("skandha")
    sk = int(sk_raw) if sk_raw is not None else None
    ch = int(recs[0].get("chapter") or passage.split(".")[-2])
    verse_disp = passage.split(".")[-1].lstrip("0") or "0"

    sa = next((r for r in recs if r["seg"] == "sa"), None)
    ru = next((r for r in recs if r["seg"] == "ru"), None)
    comms = [r for r in recs if str(r.get("seg", "")).startswith("comm")]

    inner = []
    rng = _range_div(meta, sk, ch, verse_disp, verse_disp)
    content = []
    if sa:
        author_sa = sa.get("author")
        a = (f'<span class="iast_author">{_htmllib.escape(author_sa)}<br></span>'
             if author_sa else "")
        content.append(f'<div class="chapter_block iast">{a}{sa["html"]}</div>')
    if ru:
        author_ru = ru.get("author")
        a = (f'<span class="translation_author">'
             f'{_htmllib.escape(author_ru)}:<br></span>' if author_ru else "")
        content.append(
            f'<div class="chapter_block translation">{a}{ru["html"]}</div>')
    inner.append(rng)
    if content:
        inner.append('<div class="chapter_content">' + "".join(content) + '</div>')
    if comms:
        items = []
        for c in comms:
            cid = f'comment_{c.get("fn", "")}'
            items.append(f'<div class="comment_item" id="{cid}">{c["html"]}</div>')
        inner.append('<div class="comments">' + "".join(items) + '</div>')
    return f'<div class="citation_block" id="{passage}">' + "".join(inner) + '</div>'


def render_document(records: list[dict], meta: dict, titles: dict,
                    skandha: int | None) -> list[str]:
    """Render one HTML document as a list of lines (for .html/.no_tags parity).

    Line 1 is the ``<!-- Title --!>`` marker; line 2 is head+headers+chapters
    open; then one line per chapter heading and one line per citation_block;
    the last line closes the document.
    """
    # group records by their alignment group, preserve first-seen order
    groups: dict[str, list[dict]] = {}
    for r in records:
        groups.setdefault(r.get("group") or r["id"], []).append(r)

    # order groups by (skandha, chapter, verse, seq)
    def _key(g):
        r0 = min(g, key=lambda x: x.get("seq", 0))
        p = r0["passage"].split(".")
        def _n(x):
            # leading digits only: tolerates a range ("013-015") and the
            # disambiguation suffix the parser adds to a colliding verse id
            # ("013b", from an OCR-merged chapter).
            m = re.match(r"\d+", x)
            return int(m.group()) if m else 0
        return (_n(p[0]), _n(p[1]) if len(p) > 1 else 0,
                _n(p[2]) if len(p) > 2 else 0, r0.get("seq", 0))
    ordered = sorted(groups.values(), key=_key)

    title_ru = meta.get("title_ru", meta.get("title_display", ""))
    if skandha:
        title_ru = f"{title_ru}. Скандха {skandha}"
    first_line = f"<!-- {title_ru} --!>"
    head = _HEAD.format(title=_htmllib.escape(title_ru), counter=_YM_COUNTER)
    headers = _headers_block(meta, skandha)

    lines = [first_line, head + headers + '<div class="chapters">']

    cur_ch = None
    for g in ordered:
        r0 = min(g, key=lambda x: x.get("seq", 0))
        sk = int(r0.get("skandha") or r0["passage"].split(".")[0])
        ch = int(r0.get("chapter") or r0["passage"].split(".")[1])
        if (sk, ch) != cur_ch:
            if cur_ch is not None:
                lines.append('</div>')  # close previous chapter
            t = titles.get((sk, ch), "")
            heading = (f'ГЛАВА {_num_ru(ch)}. {t.upper()}' if t
                       else f'ГЛАВА {_num_ru(ch)}')
            anchor = f'{sk}.{ch}'
            lines.append(
                f'<div class="chapter"><div class="chapter_title" '
                f'id="{anchor}">{_htmllib.escape(heading)}</div>')
            cur_ch = (sk, ch)
        lines.append(render_citation_block(g, meta))
    if cur_ch is not None:
        lines.append('</div>')
    lines.append('</div></body></html>')
    return lines


_NUM_RU = ["", "ПЕРВАЯ", "ВТОРАЯ", "ТРЕТЬЯ", "ЧЕТВЁРТАЯ", "ПЯТАЯ", "ШЕСТАЯ",
           "СЕДЬМАЯ", "ВОСЬМАЯ", "ДЕВЯТАЯ", "ДЕСЯТАЯ"]


def _num_ru(n: int) -> str:
    """Display chapter number: word for 1..10, else the digit."""
    return _NUM_RU[n] if 1 <= n < len(_NUM_RU) else str(n)


def write_document(lines: list[str], data_dir: Path, filename: str,
                   meta: dict, skandha: int | None) -> None:
    html_path = data_dir / filename
    html_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # .no_tags sidecar: tags stripped per line, first line kept verbatim.
    notag_lines = [lines[0]] + [strip_tags(ln) for ln in lines[1:]]
    (data_dir / (filename.replace(".html", "") + ".no_tags")).write_text(
        "\n".join(notag_lines) + "\n", encoding="utf-8")
    # .html.meta.json sidecar.
    m = dict(meta)
    m["filename"] = filename
    if skandha:
        m["skandha"] = skandha
    (data_dir / (filename + ".meta.json")).write_text(
        json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def append_data_txt(data_txt: Path, filenames: list[str]) -> list[str]:
    existing = []
    if data_txt.exists():
        existing = data_txt.read_text(encoding="utf-8").splitlines()
    existing_set = set(x.strip() for x in existing)
    added = []
    for fn in filenames:
        if fn not in existing_set:
            existing.append(fn)
            existing_set.add(fn)
            added.append(fn)
    if added:
        data_txt.write_text("\n".join(existing) + "\n", encoding="utf-8")
    return added


def write_desktop_report(*, manifest_path: str, data_dir: Path, filenames: list[str],
                         record_count: int, slug: str, out_path: str | None = None) -> str:
    """Register emitted desktop views against the bundle they were rendered from.

    The desktop HTML is a generated view of the same canonical JSONL the web DB
    and the offline packs consume, so it names the same input manifest hash
    (criterion A6). Every emitted file — including the `.no_tags` sidecar the
    reader actually searches — is hashed, so a desktop artifact can be traced to
    its bundle without guessing from timestamps.
    """
    import sys as _sys

    web_dir = str(Path(__file__).resolve().parent.parent)
    if web_dir not in _sys.path:
        _sys.path.insert(0, web_dir)
    from corpus_builder.build_report import build_report, output_entry, write_report
    from corpus_builder.corpus_manifest import load_manifest

    outputs = []
    for filename in filenames:
        outputs.append(output_entry(data_dir / filename))
        notags = data_dir / (filename.replace(".html", "") + ".no_tags")
        if notags.exists():
            outputs.append(output_entry(notags))

    report = build_report(
        artifact_name=f"{slug}-desktop-html",
        artifact_kind="desktop-view",
        manifest=load_manifest(manifest_path),
        outputs=outputs,
        counts={"documents": len(filenames), "records": record_count},
        generator="build_corpus_html/1",
    )
    target = out_path or str(data_dir / f"{slug}.build-report.json")
    return str(write_report(report, target))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--report", help="parser report.json for chapter titles")
    ap.add_argument("--meta", required=True, help="work-level meta.json")
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--data-txt")
    ap.add_argument("--split", choices=["skandha", "none"], default="none")
    ap.add_argument("--combined", action="store_true")
    ap.add_argument("--slug", default="devibhagavata-purana")
    ap.add_argument("--manifest", help="Corpus manifest these views are rendered from; "
                                       "emits a build report naming its content hash")
    ap.add_argument("--build-report", help="Where to write that report "
                                           "(default: <data-dir>/<slug>.build-report.json)")
    args = ap.parse_args()

    records = load_jsonl(Path(args.jsonl))
    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    titles: dict[tuple[int, int], str] = {}
    if args.report:
        rep = json.loads(Path(args.report).read_text(encoding="utf-8"))
        for ct in rep.get("chapter_titles", []):
            titles[(int(ct["skandha"]), int(ct["chapter"]))] = ct.get("title", "")

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    skandhas = sorted({int(r.get("skandha") or r["passage"].split(".")[0])
                       for r in records})

    if args.split == "skandha":
        for sk in skandhas:
            sk_recs = [r for r in records
                       if int(r.get("skandha") or r["passage"].split(".")[0]) == sk]
            lines = render_document(sk_recs, meta, titles, sk)
            fn = f"{args.slug}-{sk}.html"
            write_document(lines, data_dir, fn, meta, sk)
            written.append(fn)
            print(f"  wrote {fn} ({len(sk_recs)} records)")

    if args.combined or args.split == "none":
        lines = render_document(records, meta, titles, None)
        fn = f"{args.slug}.html"
        write_document(lines, data_dir, fn, meta, None)
        written.append(fn)
        print(f"  wrote {fn} ({len(records)} records)")

    if args.data_txt:
        added = append_data_txt(Path(args.data_txt), written)
        print(f"data.txt: appended {len(added)} of {len(written)} filenames")

    if args.manifest:
        report_path = write_desktop_report(
            manifest_path=args.manifest,
            data_dir=data_dir,
            filenames=written,
            record_count=len(records),
            slug=args.slug,
            out_path=args.build_report,
        )
        print(f"build report: {report_path}")


if __name__ == "__main__":
    main()
