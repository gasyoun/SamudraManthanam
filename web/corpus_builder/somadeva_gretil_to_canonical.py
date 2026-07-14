#!/usr/bin/env python3
"""Somadeva Kathāsaritsāgara books 11-18 — parse the in-repo GRETIL Sanskrit and
Serebryakov Russian .txt for LLM-assisted śloka↔prose alignment (H910).

Source: ``Marc-Winner/somadeva`` @ 99a72bd, files
``chapters_san/…_chap_{N}.txt`` (IAST Sanskrit, ``// sokss_L,T.S //`` śloka refs)
and ``chapters_rus/…_chap_{N}.txt`` (Serebryakov Russian prose).

This module is the deterministic half of the H910 pipeline:
* ``parse_sanskrit`` — one record per śloka, keyed ``(lambaka, taraṅga, śloka)``.
* ``parse_russian``  — the ordered Russian sentences, each tagged with its
  ``(lambaka, taraṅga)`` from the ``КНИГА`` / ``## L.T.`` headers.

The alignment itself (which śloka range each Russian sentence renders) is the
LLM step, kept separate. ``emit_jsonl`` turns an alignment mapping back into
canonical JSONL matching the platform contract (see build_corpus_html.py).
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

# The śloka ref may carry a dual annotation before the closing "//", e.g.
# "// sokss_12,10.1 (vet_3.1) //" for the Vetālapañcaviṃśati tales in book 12.
SOKSS = re.compile(r"//\s*sokss_(\d+),(\d+)\.(\d+)(?:\s*\([^)]*\))?\s*//")
RU_BOOK = re.compile(r"^КНИГА\s+", re.IGNORECASE)
RU_WAVE = re.compile(r"^##\s*(\d+)\.(\d+)\.?")  # "## 11.1. ВОЛНА ПЕРВАЯ" — trailing
# dot is inconsistently present upstream: books 1-10's *first* wave header of
# every chapter (".1 ВОЛНА ПЕРВАЯ") is missing it while all later ones have it
# ("## 2.1 ВОЛНА ПЕРВАЯ" vs "## 2.2. ВОЛНА ВТОРАЯ") — a strict trailing-dot
# match silently misattributed taraṅga-1's Russian prose to taraṅga 0 (H928
# discovery). Optional dot fixes it without affecting books 11-18, whose
# headers all carry the dot.


def iast_to_slp1(s: str) -> str:
    return transliterate(s, sanscript.IAST, sanscript.SLP1)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def parse_sanskrit(path: Path):
    """Yield {lambaka, taranga, sloka, iast, slp1} per śloka, in order.

    A śloka is the run of text lines up to and including its ``// sokss_L,T.S //``
    marker; the marker and internal ``/`` pāda dividers are kept out of the plain
    text (the ``//`` before the ref is dropped, single ``/`` kept as daṇḍa)."""
    buf: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("%") or line.startswith("#"):
            # lambaka (#) / file (%) / taraṅga (##) header — keys come from the
            # sokss ref itself, so headers are only structural; skip text-wise.
            continue
        m = SOKSS.search(line)
        if m:
            lam, tar, slo = int(m.group(1)), int(m.group(2)), int(m.group(3))
            pre = line[: m.start()].rstrip()
            if pre:
                buf.append(pre)
            iast = norm(" ".join(buf)).rstrip("/ ").strip()
            buf = []
            if iast:
                yield {
                    "lambaka": lam, "taranga": tar, "sloka": slo,
                    "iast": iast, "slp1": iast_to_slp1(iast),
                }
        else:
            buf.append(line)


def parse_russian(path: Path):
    """Yield {lambaka, taranga, idx, text} per Russian prose sentence, in order.

    Headers: ``КНИГА …`` (book), ``# …`` (title), ``## L.T. ВОЛНА …`` (taraṅga).
    Content before the first ``## L.T.`` (the maṅgala) is tagged taraṅga 0.
    A chapter file = one book, so the lambaka is taken from the first wave header
    and backfilled onto the maṅgala."""
    lines = path.read_text(encoding="utf-8").splitlines()
    # book lambaka = first "## L.T." wave header's L (fallback 0)
    book_lam = 0
    for raw in lines:
        w = RU_WAVE.match(raw.strip())
        if w:
            book_lam = int(w.group(1))
            break
    tar = 0
    idx = 0
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        w = RU_WAVE.match(line)
        if w:
            tar = int(w.group(2))
            continue
        if RU_BOOK.match(line):
            continue
        if line.startswith("#"):  # title line "# Книга о …"
            continue
        idx += 1
        yield {"lambaka": book_lam, "taranga": tar, "idx": idx, "text": line}


def emit_jsonl(sa_recs, ru_recs, mapping, slug="kathasaritsagara"):
    """Turn a monotonic śloka-range alignment into canonical JSONL records.

    Each mapping entry {ru_idx, taranga, sloka_start, sloka_end, confidence}
    becomes one group keyed ``lambaka.taraṅga.START`` (or ``…START-END`` for a
    multi-śloka range): the Sanskrit side concatenates ślokas START..END, the
    Russian side is that sentence. structure="verse" (true śloka keying)."""
    import html as _html
    lam = sa_recs[0]["lambaka"]
    sa_by_key = {(r["taranga"], r["sloka"]): r for r in sa_recs}
    ru_by_idx = {r["idx"]: r for r in ru_recs}
    records = []
    seq = 0
    for m in sorted(mapping, key=lambda x: (x["taranga"], x["sloka_start"])):
        t, a, b = m["taranga"], m["sloka_start"], m["sloka_end"]
        chunk = [sa_by_key[(t, s)] for s in range(a, b + 1) if (t, s) in sa_by_key]
        if not chunk:
            continue
        passage = f"{lam}.{t}.{a}" if a == b else f"{lam}.{t}.{a}-{b}"
        group = f"{slug}:{passage}"
        conf = m.get("confidence")
        iast = " ".join(c["iast"] for c in chunk)
        slp1 = " ".join(c["slp1"] for c in chunk)
        seq += 1
        records.append({
            "id": f"{group}#sa", "work": slug, "passage": passage, "seg": "sa",
            "group": group, "lang": "sa", "script": "iast",
            "text": iast, "html": _html.escape(iast) + "<br>", "slp1": slp1,
            "structure": "verse", "chapter": str(t), "seq": seq,
            "confidence": conf, "deleted": False,
        })
        ru = ru_by_idx.get(m["ru_idx"])
        if ru and ru["text"].strip():
            seq += 1
            records.append({
                "id": f"{group}#ru", "work": slug, "passage": passage, "seg": "ru",
                "group": group, "lang": "ru", "script": "cyrillic",
                "text": ru["text"], "html": _html.escape(ru["text"]) + "<br>",
                "structure": "verse", "chapter": str(t), "seq": seq,
                "confidence": conf, "deleted": False,
            })
    return records


def validate_mapping(sa_recs, mapping):
    """Return a list of problems: gaps/overlaps/uncovered ślokas per taraṅga."""
    problems = []
    by_tar: dict[int, list] = {}
    for m in mapping:
        by_tar.setdefault(m["taranga"], []).append(m)
    sa_tar_max = {}
    for r in sa_recs:
        sa_tar_max[r["taranga"]] = max(sa_tar_max.get(r["taranga"], 0), r["sloka"])
    for t, ms in by_tar.items():
        ms = sorted(ms, key=lambda x: x["sloka_start"])
        expect = 1
        for m in ms:
            if m["sloka_start"] != expect:
                problems.append(f"t{t}: gap/overlap — expected start {expect}, got {m['sloka_start']} (ru_idx {m['ru_idx']})")
            if m["sloka_end"] < m["sloka_start"]:
                problems.append(f"t{t}: inverted range {m['sloka_start']}-{m['sloka_end']} (ru_idx {m['ru_idx']})")
            expect = m["sloka_end"] + 1
        last = expect - 1
        if t in sa_tar_max and last != sa_tar_max[t]:
            problems.append(f"t{t}: coverage ends at {last}, taraṅga has {sa_tar_max[t]} ślokas")
    return problems


if __name__ == "__main__":
    import argparse
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--book", type=int, required=True)
    ap.add_argument("--dump", choices=["sa", "ru", "both"], default="both")
    ap.add_argument("--align", help="alignment mapping JSON → emit canonical JSONL")
    ap.add_argument("--out", help="output JSONL path (with --align)")
    ap.add_argument("--slug", default="kathasaritsagara")
    ap.add_argument("--ru-book", type=int, default=None,
                    help="Russian source chapter file, if it differs from --book "
                         "(the upstream repo swaps the SA/RU files for lambakas "
                         "14↔15). Passage keys always come from the SA --book.")
    args = ap.parse_args()
    src = Path(args.src)
    ru_book = args.ru_book if args.ru_book is not None else args.book
    sa_path = src / "chapters_san" / f"kathasaritsagara_san_cleant_chap_{args.book:02d}.txt"
    ru_path = src / "chapters_rus" / f"kathasaritsagara_rus_cleant_chap_{ru_book:02d}.txt"
    sa = list(parse_sanskrit(sa_path))
    ru = list(parse_russian(ru_path))
    print(f"book {args.book}: {len(sa)} ślokas, {len(ru)} Russian sentences")

    if args.align:
        mapping = json.loads(Path(args.align).read_text(encoding="utf-8"))
        problems = validate_mapping(sa, mapping)
        if problems:
            print("VALIDATION PROBLEMS:")
            for p in problems:
                print("  -", p)
        recs = emit_jsonl(sa, ru, mapping, slug=args.slug)
        confs = [m.get("confidence", 1.0) for m in mapping]
        low = [m["ru_idx"] for m in mapping if (m.get("confidence") or 1.0) < 0.6]
        Path(args.out).write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n",
            encoding="utf-8")
        print(f"wrote {len(recs)} records ({len(mapping)} groups) → {args.out}")
        print(f"confidence: min {min(confs):.2f}, mean {sum(confs)/len(confs):.2f}; "
              f"{len(low)} groups < 0.6 (ru_idx {low})")
        if problems:
            print("NOTE: fix validation problems before ingest.")
    else:
        print("SA taraṅgas:", sorted({(r['lambaka'], r['taranga']) for r in sa}))
        print("RU taraṅgas:", sorted({(r['lambaka'], r['taranga']) for r in ru}))
        for r in sa[:3]:
            print(f"  {r['lambaka']}.{r['taranga']}.{r['sloka']}: {r['iast'][:70]}")
        for r in ru[:3]:
            print(f"  [{r['idx']}] ({r['lambaka']}.{r['taranga']}): {r['text'][:70]}")
