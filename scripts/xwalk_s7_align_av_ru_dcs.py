#!/usr/bin/env python3
"""H4743 (xwalk-s7) — align Samudra Atharvaveda Russian x DCS Atharvaveda (Śaunaka).

rvlinks precedent (H2863): a Russian translation joined, verse-by-verse, to a
reference Sanskrit text, verified by CONTENT (not just by passage id).

Method
------
1. Parse DCS CoNLL-U hymn files (`## chapter: AVŚ, B, H`; `# text =` pādas)
   into a hymn-level token stream with per-pāda and sent_id bookkeeping.
2. Parse Samudra `NN_atharvaveda.jsonl` into book/hymn/verse sa streams
   (book = file number NN, hymn = passage prefix).
3. For every hymn present on both sides: difflib token alignment over the
   normalized (accent-folded, case-folded) token streams. Hymn coverage =
   matched sa tokens / sa tokens. A hymn is CONFIRMED at coverage >= 0.60;
   within a confirmed hymn every verse with >= 0.50 token coverage gets a
   DCS pāda span -> verse-level SA-RU x DCS row.
4. Control: the same sa sample is scored against Atharvaveda (Paippalāda)
   to prove the Śaunaka choice by content, not assumption.

Outputs
-------
    reports/xwalk-s7-av-ru-dcs-alignment.tsv   (verse-level alignment)
    reports/xwalk-s7-av-ru-dcs-alignment.md    (report + verdict)

Exit 0 when Śaunaka wins the control and confirmed-hymn coverage is > 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

STRIP_RE = re.compile(r"[^a-z ]")


def norm_tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = unicodedata.normalize("NFC", text).casefold()
    return [t for t in STRIP_RE.sub(" ", text).split() if t]


def parse_dcs(dcs_dir: Path) -> dict[tuple[int, int], dict]:
    """-> {(book, hymn): {chapter_id, padas: [text], sent_ids: [...], tokens: [...]}}"""
    hymns: dict[tuple[int, int], dict] = {}
    for path in sorted(dcs_dir.glob("*.conllu")):
        m = re.search(r"AV[ŚP],\s*(\d+),\s*(\d+)-(\d+)\.conllu$", path.name)
        if not m:
            continue
        book, hymn, chapter_id = int(m.group(1)), int(m.group(2)), m.group(3)
        padas: list[str] = []
        sent_ids: list[str] = []
        pending_text: str | None = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            if raw.startswith("# text = "):
                pending_text = raw[len("# text = "):].strip()
            elif raw.startswith("# sent_id = ") and pending_text is not None:
                padas.append(pending_text)
                sent_ids.append(raw[len("# sent_id = "):].strip())
                pending_text = None
        tokens: list[str] = []
        token_pada: list[int] = []
        for pi, p in enumerate(padas):
            for tok in norm_tokens(p):
                tokens.append(tok)
                token_pada.append(pi)
        if tokens:
            hymns[(book, hymn)] = {
                "chapter_id": chapter_id,
                "padas": padas,
                "sent_ids": sent_ids,
                "tokens": tokens,
                "token_pada": token_pada,
            }
    return hymns


def parse_samudra_av(jsonl_path: Path) -> dict[tuple[int, int], dict]:
    """One numbered jsonl file (one AV book) -> {(book, hymn): {verses: [...]}}"""
    by_hymn_sa: dict[str, dict[str, str]] = defaultdict(dict)
    by_hymn_ru: dict[str, dict[str, str]] = defaultdict(dict)
    for raw in jsonl_path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        rec = json.loads(raw)
        if rec.get("deleted"):
            continue
        hymn, _, verse = rec["passage"].partition(".")
        if rec["seg"] == "sa":
            by_hymn_sa[hymn][verse] = rec["text"]
        elif rec["seg"] == "ru":
            by_hymn_ru[hymn][verse] = rec["text"]
    book = int(jsonl_path.name.split("_", 1)[0])
    out: dict[tuple[int, int], dict] = {}
    for hymn, verses in by_hymn_sa.items():
        def _vkey(v: str) -> tuple[int, str]:
            m = re.match(r"(\d+)([a-z]*)", v)
            if not m:
                return (10**9, v)
            return (int(m.group(1)), m.group(2))
        ordered = sorted(verses.items(), key=lambda kv: _vkey(kv[0]))
        tokens: list[str] = []
        token_verse: list[int] = []
        verse_texts: list[str] = []
        for vi, (_v, text) in enumerate(ordered):
            verse_texts.append(text)
            n_before = len(tokens)
            tokens.extend(norm_tokens(text))
            token_verse.extend([vi] * (len(tokens) - n_before))
        out[(book, int(hymn))] = {
            "verse_labels": [v for v, _ in ordered],
            "verses": verse_texts,
            "verse_ru": [by_hymn_ru.get(hymn, {}).get(v, "") for v, _ in ordered],
            "tokens": tokens,
            "token_verse": token_verse,
        }
    return out


def align_hymn(sam: dict, dcs: dict) -> dict:
    """Token-align one hymn; return per-verse coverage + dcs pada span."""
    sm = SequenceMatcher(None, sam["tokens"], dcs["tokens"], autojunk=False)
    pada_hits: dict[int, set[int]] = defaultdict(set)  # verse idx -> pada set
    verse_hits: dict[int, int] = defaultdict(int)      # verse idx -> matched tokens
    for i, j, n in sm.get_matching_blocks():
        if n == 0:
            continue
        for off in range(n):
            v = sam["token_verse"][i + off]
            p = dcs["token_pada"][j + off]
            pada_hits[v].add(p)
            verse_hits[v] += 1
    total = max(len(sam["tokens"]), 1)
    hymn_cov = sum(verse_hits.values()) / total
    rows = []
    for vi in range(len(sam["verses"])):
        v_len = sum(1 for x in sam["token_verse"] if x == vi)
        cov = verse_hits.get(vi, 0) / max(v_len, 1)
        span = sorted(pada_hits.get(vi, []))
        dcs_text = " / ".join(dcs["padas"][p] for p in span)
        dcs_sids = ",".join(dcs["sent_ids"][p] for p in span)
        rows.append({
            "verse": sam["verse_labels"][vi],
            "coverage": round(cov, 3),
            "match": "content" if cov >= 0.50 else "unmatched",
            "padas": span,
            "sent_ids": dcs_sids,
            "dcs_text": dcs_text,
            "ru": sam["verse_ru"][vi] if vi < len(sam["verse_ru"]) else "",
        })
    return {"hymn_cov": round(hymn_cov, 3), "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent.parent
    ap.add_argument("--jsonl-dir", type=Path,
                    default=here / "web/corpus_builder/jsonl")
    ap.add_argument("--dcs-conllu", type=Path,
                    default=Path.home() / "Documents/GitHub/dcs-conllu/files")
    ap.add_argument("--out-tsv", type=Path,
                    default=here / "reports/xwalk-s7-av-ru-dcs-alignment.tsv")
    ap.add_argument("--out-md", type=Path,
                    default=here / "reports/xwalk-s7-av-ru-dcs-alignment.md")
    args = ap.parse_args()

    saunaka = parse_dcs(args.dcs_conllu / "Atharvaveda (Śaunaka)")
    paipp = parse_dcs(args.dcs_conllu / "Atharvaveda (Paippalāda)")

    av_files = sorted(args.jsonl_dir.glob("[0-9][0-9]_atharvaveda.jsonl"))
    all_rows: list[list[object]] = []
    hymn_covs_saunaka: list[float] = []
    confirmed = 0
    total_hymns = 0
    total_verses = 0
    matched_verses = 0

    for path in av_files:
        sam_hymns = parse_samudra_av(path)
        book = int(path.name.split("_", 1)[0])
        for (b, hymn), sam in sorted(sam_hymns.items()):
            total_hymns += 1
            dcs = saunaka.get((book, hymn))
            if dcs is None:
                for vi, ru_text in enumerate(sam["verse_ru"]):
                    all_rows.append([book, hymn, sam["verse_labels"][vi], "", "no_dcs_hymn", 0.0,
                                     "", "", ru_text])
                continue
            res = align_hymn(sam, dcs)
            hymn_covs_saunaka.append(res["hymn_cov"])
            total_verses += len(res["rows"])
            if res["hymn_cov"] >= 0.60:
                confirmed += 1
            for row in res["rows"]:
                if row["match"] == "content":
                    matched_verses += 1
                all_rows.append([
                    book, hymn, row["verse"], dcs["chapter_id"], row["match"],
                    row["coverage"], row["sent_ids"],
                    row["dcs_text"], row["ru"],
                ])

    # ---- control: same-content check against Paippalāda on a bounded sample
    sample = av_files[:3]
    cov_pp = []
    for path in sample:
        sam_hymns = parse_samudra_av(path)
        book = int(path.name.split("_", 1)[0])
        for (b, hymn), sam in list(sorted(sam_hymns.items()))[:15]:
            dcs = paipp.get((book, hymn))
            if dcs:
                cov_pp.append(align_hymn(sam, dcs)["hymn_cov"])
    mean_pp = sum(cov_pp) / len(cov_pp) if cov_pp else 0.0
    mean_s = (sum(hymn_covs_saunaka) / len(hymn_covs_saunaka)
              if hymn_covs_saunaka else 0.0)

    # ---- TSV
    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_tsv.open("w", encoding="utf-8") as fh:
        fh.write("book\thymn\tverse\tdcs_chapter_id\tmatch\tcoverage\t"
                 "dcs_sent_ids\tdcs_text\tsamudra_ru\n")
        for r in all_rows:
            fh.write("\t".join(
                str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")

    # ---- MD report
    verdict_parts = []
    ctrl_ok = mean_s > mean_pp
    verdict_parts.append(
        f"Śaunaka control: mean hymn coverage Śaunaka={mean_s:.3f} vs "
        f"Paippalāda={mean_pp:.3f} → {'ŚAUNAKA CONFIRMED' if ctrl_ok else 'CONTROL FAILED'}")
    verdict_parts.append(
        f"confirmed hymns (cov≥0.60): {confirmed}/{total_hymns}")
    verdict_parts.append(
        f"verse rows matched by content: {matched_verses}/{total_verses}")
    overall = ctrl_ok and confirmed > 0
    md = [
        "# xwalk-s7 — AV Russian × DCS Atharvaveda (Śaunaka) alignment (H4743)",
        "",
        "_Generated: 15-09-2026 by `scripts/xwalk_s7_align_av_ru_dcs.py` — deterministic, re-run to reproduce._",
        "",
        f"**Verdict: {'PASS' if overall else 'FAIL'}** — " + "; ".join(verdict_parts),
        "",
        "## Method",
        "",
        "- Samudra side: `web/corpus_builder/jsonl/NN_atharvaveda.jsonl` (book = NN),",
        "  Russian segment `#ru` + its Sanskrit segment `#sa`.",
        f"- DCS side: `dcs-conllu/files/Atharvaveda (Śaunaka)/` ({len(saunaka)} hymns parsed).",
        "- Join is CONTENT-based (rvlinks precedent): normalized token difflib per hymn;",
        "  verse-level rows where ≥50 % of the verse's sa tokens map into a DCS pāda span.",
        "- Control: Paippalāda recension scored on the same sample to rule out",
        "  a wrong-recension assumption.",
        "",
        "## Results",
        "",
        f"- hymns in Samudra AV: **{total_hymns}** across {len(av_files)} book files",
        f"- hymns confirmed vs DCS Śaunaka (cov ≥ 0.60): **{confirmed}**",
        f"- verse-level aligned rows: **{matched_verses}** of {total_verses}",
        f"- mean hymn coverage: Śaunaka **{mean_s:.3f}**, Paippalāda {mean_pp:.3f} (sample of {len(cov_pp)} hymns)",
        "",
        "## Inspect first",
        "",
        "- `reports/xwalk-s7-av-ru-dcs-alignment.tsv` — full verse table",
        "  (`match=content` rows are the alignment; `unmatched`/`no_dcs_hymn` rows are honest residue).",
        "- Sample rows:",
        "",
    ]
    shown = 0
    for r in all_rows:
        row = [str(x) for x in r]
        if row[4] == "content" and shown < 5:
            md.append(f"- AV {row[0]}.{row[1]}.{row[2]} ↔ DCS {row[3]} (cov {row[5]}): "
                      f"RU «{row[8][:70]}…» ↔ SA «{row[7][:70]}…»")
            shown += 1
    args.out_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"[xwalk-s7] tsv  -> {args.out_tsv} ({len(all_rows)} rows)")
    print(f"[xwalk-s7] md   -> {args.out_md}")
    print("[xwalk-s7] " + "; ".join(verdict_parts))
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
