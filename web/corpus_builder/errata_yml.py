"""SanskritGrammar-shaped errata.yml: load, apply, generate ERRATA.md.

Schema is the Knauer/Kochergina row (read / instead / found_by / date_added /
fixed_in / page / line / kind / locus / note). The corpus catalog
(docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md §5) adds work + passage (or id)
so a row can target a JSONL record when there is no printed page.

PyYAML is deliberately not imported: the CI test job installs only
requirements.txt + pytest (see web/tests/test_runtime_alignment.py).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
ERRATA_ROOT = _HERE / "errata"
RECIPES_PATH = ERRATA_ROOT / "recipes.json"
DEFAULT_KIND = "print"
DEFAULT_TIER = "erratum"
CHECKSUM_LEN = 12

_SCALAR_NULL = {"", "null", "~", "None"}


def ddmmyyyy(d: date | None = None) -> str:
    return (d or date.today()).strftime("%d-%m-%Y")


def _unquote(raw: str) -> str:
    s = raw.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def _parse_scalar(raw: str) -> Any:
    s = raw.strip()
    if s in _SCALAR_NULL:
        return ""
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if (s.startswith('"') and s.endswith('"')) or (
        s.startswith("'") and s.endswith("'")
    ):
        return s[1:-1]
    return s


def _split_flow_pairs(body: str) -> list[str]:
    """Split `{a: 1, b: "x, y"}` contents on top-level commas."""
    parts: list[str] = []
    buf: list[str] = []
    quote = None
    for ch in body:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
            continue
        if ch == ",":
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
            continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_flow_mapping(text: str) -> dict[str, Any]:
    body = text.strip()
    if body.startswith("{") and body.endswith("}"):
        body = body[1:-1]
    out: dict[str, Any] = {}
    for part in _split_flow_pairs(body):
        if ":" not in part:
            continue
        key, val = part.split(":", 1)
        out[key.strip()] = _parse_scalar(val)
    return out


def load_errata_yml(path: Path) -> dict[str, Any]:
    """Load one errata.yml (block list + Knauer flow-style rows)."""
    text = path.read_text(encoding="utf-8")
    work = ""
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    fold_key: str | None = None
    fold_lines: list[str] = []
    in_entries = False

    def flush_fold() -> None:
        nonlocal fold_key, fold_lines, current
        if fold_key and current is not None:
            current[fold_key] = " ".join(ln.strip() for ln in fold_lines if ln.strip())
        fold_key = None
        fold_lines = []

    def start_entry(entry: dict[str, Any]) -> None:
        nonlocal current
        flush_fold()
        if current is not None:
            entries.append(current)
        current = entry

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if fold_key and raw.startswith(" "):
                fold_lines.append(stripped)
            continue
        if fold_key and (raw.startswith("  ") or raw.startswith("\t")) and not stripped.startswith("-"):
            fold_lines.append(stripped)
            continue
        flush_fold()

        if stripped.startswith("work:") and current is None:
            work = str(_parse_scalar(stripped.split(":", 1)[1]))
            continue
        if stripped.startswith("entries:"):
            in_entries = True
            rest = stripped.split(":", 1)[1].strip()
            if rest in ("[]",):
                in_entries = True
            continue
        if not in_entries:
            continue
        if stripped.startswith("-"):
            rest = stripped[1:].strip()
            if rest.startswith("{"):
                start_entry(_parse_flow_mapping(rest))
            elif rest and ":" in rest:
                key, val = rest.split(":", 1)
                start_entry({key.strip(): _parse_scalar(val)})
            else:
                start_entry({})
            continue
        if current is not None and ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val in (">", ">-", "|", "|-"):
                fold_key = key
                fold_lines = []
            else:
                current[key] = _parse_scalar(val)
    flush_fold()
    if current is not None:
        entries.append(current)
    return {"work": work, "entries": entries, "path": path}


def checksum(entry: dict[str, Any]) -> str:
    payload = "|".join(
        [
            str(entry.get("page", "")),
            str(entry.get("line", "")),
            str(entry.get("read", "")),
            str(entry.get("instead", "")),
            str(entry.get("id") or ""),
            str(entry.get("passage") or ""),
            str(entry.get("locus") or ""),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:CHECKSUM_LEN]


def load_recipes(path: Path | None = None) -> dict[str, Any]:
    src = path or RECIPES_PATH
    if not src.exists():
        return {"schema_version": 1, "works": {}}
    return json.loads(src.read_text(encoding="utf-8"))


def recipe_for(slug: str, recipes: dict[str, Any] | None = None) -> dict[str, Any]:
    data = recipes if recipes is not None else load_recipes()
    works = data.get("works") or {}
    if slug not in works:
        raise KeyError(
            f"no catalog recipe for {slug!r}; add a row to {RECIPES_PATH.name} "
            "(machine form of KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md §4.5)"
        )
    return works[slug]


def _repo_path(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else _REPO / p


def load_jsonl(path: Path) -> list[tuple[str, dict[str, Any]]]:
    """Return (original_line, record) pairs so unchanged lines stay byte-stable."""
    out: list[tuple[str, dict[str, Any]]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            raw = line.rstrip("\n")
            if not raw.strip():
                continue
            out.append((raw, json.loads(raw)))
    return out


def write_jsonl(path: Path, rows: list[tuple[str, dict[str, Any]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for original, rec in rows:
            fh.write(original if original else json.dumps(rec, ensure_ascii=False))
            fh.write("\n")


def _record_matches(rec: dict[str, Any], entry: dict[str, Any]) -> bool:
    entry_id = str(entry.get("id") or "").strip()
    if entry_id:
        return rec.get("id") == entry_id
    passage = str(entry.get("passage") or "").strip()
    if not passage:
        return False
    if rec.get("passage") != passage:
        return False
    work = str(entry.get("work") or "").strip()
    if work and rec.get("work") != work:
        return False
    seg = str(entry.get("seg") or "").strip()
    if seg and rec.get("seg") != seg:
        return False
    return True


def _replace_once(value: str, instead: str, read: str) -> tuple[str, int]:
    count = value.count(instead)
    if count == 0:
        return value, 0
    return value.replace(instead, read, 1), count


def apply_entries(
    rows: list[tuple[str, dict[str, Any]]],
    entries: list[dict[str, Any]],
) -> tuple[list[tuple[str, dict[str, Any]]], list[dict[str, Any]]]:
    """Patch JSONL rows. Fail loud if a non-retraction row cannot be placed."""
    report: list[dict[str, Any]] = []
    out = list(rows)
    for idx, entry in enumerate(entries):
        tier = entry.get("tier") or DEFAULT_TIER
        if tier == "retraction":
            report.append({"index": idx, "status": "skipped_retraction"})
            continue
        instead = str(entry.get("instead") or "")
        read = str(entry.get("read") or "")
        if not instead:
            raise ValueError(f"errata row {idx}: empty `instead`")
        if read == instead:
            raise ValueError(f"errata row {idx}: `read` equals `instead`")
        hits = [i for i, (_raw, rec) in enumerate(out) if _record_matches(rec, entry)]
        if not hits:
            raise ValueError(
                f"errata row {idx}: no JSONL record for "
                f"id={entry.get('id')!r} passage={entry.get('passage')!r}"
            )
        applied = 0
        already = 0
        for i in hits:
            original, rec = out[i]
            text = str(rec.get("text") or "")
            html = str(rec.get("html") or "")
            if instead not in text and instead not in html:
                if read in text or read in html:
                    already += 1
                    continue
                raise ValueError(
                    f"errata row {idx}: `instead`={instead!r} not in "
                    f"record {rec.get('id')}"
                )
            new_rec = dict(rec)
            changed = False
            if instead in text:
                new_text, n = _replace_once(text, instead, read)
                if n != 1:
                    raise ValueError(
                        f"errata row {idx}: `instead` occurs {n} times in "
                        f"text of {rec.get('id')} (want 1)"
                    )
                new_rec["text"] = new_text
                changed = True
            if instead in html:
                new_html, n = _replace_once(html, instead, read)
                if n != 1:
                    raise ValueError(
                        f"errata row {idx}: `instead` occurs {n} times in "
                        f"html of {rec.get('id')} (want 1)"
                    )
                new_rec["html"] = new_html
                changed = True
            if changed:
                out[i] = (json.dumps(new_rec, ensure_ascii=False), new_rec)
                applied += 1
        report.append(
            {
                "index": idx,
                "status": "applied" if applied else "already_applied",
                "records": applied or already,
                "id": entry.get("id"),
                "passage": entry.get("passage"),
            }
        )
    return out, report


def generate_errata_md(work: str, entries: list[dict[str, Any]], source_name: str = "errata.yml") -> str:
    n = len(entries)
    fixed = sum(1 for e in entries if e.get("fixed_in"))
    header = [
        f"# Errata — {work}",
        "",
        f"_Auto-generated from `{source_name}` by "
        "`web/corpus_builder/build_errata.py`. Do not edit by hand._",
        "",
        f"_Generated: {ddmmyyyy()} · {n} errata "
        f"({n - fixed} open · {fixed} fixed in the digital edition)._",
        "",
        "`read` = the correct form · `instead` = what the source showed. "
        "Corpus rows target a JSONL `passage` or segment `id` "
        "(see [catalog §5](https://github.com/gasyoun/SamudraManthanam/blob/main/docs/KATALOG_KOMBINACIJ_SBORKI_KORPUSA.md)). "
        "Schema matches [SanskritGrammar errata.yml](https://github.com/gasyoun/SanskritGrammar/blob/main/KnauerFrazy_1908/errata.yml).",
        "",
    ]
    if n == 0:
        header += [
            "No corrections have been catalogued for this work yet. "
            "Add a row to `errata.yml` (`read` / `instead` / `found_by` / "
            "`date_added` / `passage` or `id`) and run "
            "`python web/corpus_builder/apply_errata.py --work <slug> --rebuild`.",
            "",
        ]
        return "\n".join(header)
    lines = header + [
        "| # | Passage / id | Kind | Read | Instead of | Found by | Added | Status |",
        "|--:|--|--|--|--|--|--|--|",
    ]
    for i, e in enumerate(entries, 1):
        target = str(e.get("id") or e.get("passage") or e.get("locus") or "")
        kind = e.get("kind") or DEFAULT_KIND
        fx = e.get("fixed_in")
        status = f"fixed in {fx}" if fx else "open"
        found = str(e.get("found_by") or "").replace("|", "\\|")
        read = str(e.get("read") or "").replace("|", "\\|")
        instead = str(e.get("instead") or "").replace("|", "\\|")
        added = str(e.get("date_added") or "")
        lines.append(
            f"| {i} | `{target}` | {kind} | {read} | {instead} | {found} | {added} | {status} |"
        )
    lines.append("")
    return "\n".join(lines)
