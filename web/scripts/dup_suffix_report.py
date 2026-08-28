"""Categorised duplicate-suffix invariant report (H1927 / Lane D5-D7).

VERIFICATION D7: "Duplicate-suffix validation uses a categorised invariant, not
an unexplained stale count ceiling."

Background. When a work legitimately carries two distinct verses under one
passage number, the converter disambiguates the second with a letter suffix:
`work:1.1` and `work:1.1b`. A *bug* in verse splitting produces the same shape,
so for a long time the only gate was a bare count ceiling — `<= 200`, with no
recorded derivation. H1829 (02-08-2026) found that ceiling hiding a real defect:
nirvana-tantra alone held 284 of 429 suffixed ids because footnote markers
``(N)`` were being read as verse boundaries. The ceiling was then lowered to a
measured 180.

A lower ceiling is still a ceiling. It answers "how many?" when the question
that separates a real collision from splitter debris is "what shape?". This
module answers the second one, and the gate asserts its categories.

The invariants, each derived from the measured corpus (see
`docs/DUP_SUFFIX_INVARIANT_REPORT.md`), and each with a stated failure meaning:

* **base_present** — every suffixed id has its un-suffixed twin. A `1.1b` with
  no `1.1` means the splitter invented a boundary rather than disambiguating a
  genuine collision. This is the H1829 signature, and it is structural: it
  cannot be satisfied by a bug that merely stays under a count.
* **suffix_depth** — collisions are pairs, so the only suffix letter is `b`.
  A `c`/`d`/`e` run is a splitter walking through one passage repeatedly.
* **segment_pairing** — a suffixed record belongs to a `sa`/`ru` parallel pair
  or is a commentary; a suffix on some other segment class is unexplained.
* **concentration** — no single work may dominate the population. The old bug
  was 79% in one work.

Counts are still *reported* — they are useful for review — but they no longer
gate on their own.

Usage
-----
    python web/scripts/dup_suffix_report.py                 # human report
    python web/scripts/dup_suffix_report.py --json out.json # machine-readable
    python web/scripts/dup_suffix_report.py --markdown docs/DUP_SUFFIX_INVARIANT_REPORT.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

WEB_ROOT = Path(__file__).resolve().parents[1]
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))

from app.services.slug import make_unique_slug  # noqa: E402

# `work:1.1b#sa`, `work:1.1b.comm`, … — a letter suffix on the passage number.
# The suffix class is deliberately WIDE on the upper end: the legacy Ignatiev
# exporter minted collision suffixes with a bare `chr(ord(c) + 1)` run that
# overflowed past 'z' into `{ | } ~` DEL and C1 controls (H3614 — 12 such ids
# hid from a plain `[b-z]` class while the same run violated the depth rule 24
# times). The mint starts at 'b', so the whole debris space is `b`..`z` plus
# the contiguous chr() range above it. 'a' stays excluded on purpose: it is a
# GRETIL pada letter (Rigveda `1.1a`), not a disambiguation suffix.
DUP_ID_RE = re.compile(
    r"^(?P<base>.+:[0-9.]+)(?P<suffix>[b-z{|}~\x7f-\x9f])(?P<tail>(?:#|\.comm).*)$"
)

# Concentration is only meaningful once the population is large enough that a
# ratio means something; below this a single multi-verse work is 100% and fine.
CONCENTRATION_MIN_POPULATION = 30
CONCENTRATION_MAX_SHARE = 0.60

# Retained as a coarse backstop only — the categorised invariants above are the
# actual gate. Measured 147 on 05-08-2026; headroom for genuine new dups.
POPULATION_BACKSTOP = 300

EXPECTED_SEGMENTS = {"sa", "ru"}


@dataclass
class Violation:
    invariant: str
    record_id: str
    work: str
    detail: str


@dataclass
class DupSuffixReport:
    total_records: int = 0
    dup_records: int = 0
    by_work: dict[str, int] = field(default_factory=dict)
    by_suffix: dict[str, int] = field(default_factory=dict)
    by_segment: dict[str, int] = field(default_factory=dict)
    violations: list[Violation] = field(default_factory=list)

    def violations_for(self, invariant: str) -> list[Violation]:
        return [v for v in self.violations if v.invariant == invariant]

    @property
    def ok(self) -> bool:
        return not self.violations

    @property
    def top_work(self) -> tuple[str, int] | None:
        if not self.by_work:
            return None
        return max(self.by_work.items(), key=lambda kv: kv[1])

    def to_dict(self) -> dict:
        return {
            "total_records": self.total_records,
            "dup_records": self.dup_records,
            "by_work": self.by_work,
            "by_suffix": self.by_suffix,
            "by_segment": self.by_segment,
            "violations": [
                {
                    "invariant": v.invariant,
                    "id": v.record_id,
                    "work": v.work,
                    "detail": v.detail,
                }
                for v in self.violations
            ],
            "ok": self.ok,
        }


def canonical_jsonl_files(web_root: Path | None = None) -> list[Path]:
    """The JSONL files `ingest.py` actually reads — never a directory glob.

    `corpus_builder/jsonl/` also holds build-time staging artifacts (per-book
    split files consumed only by a combine step, `.raw.jsonl` pre-alignment
    dumps) that ingest never reads. Globbing them double-counts records against
    the same canonical ids and manufactures "duplicates" that were never
    ingested twice — the exact false positive this report must not produce.

    This is the single definition; `tests/test_converter.py` imports it rather
    than keeping a second copy that could drift.
    """
    web_root = web_root or WEB_ROOT
    jsonl_dir = web_root / "corpus_builder" / "jsonl"
    data_txt = (
        web_root.parent / "Index" / "lib" / "x86_64-win64" / "Programdata" / "data.txt"
    )
    if not data_txt.exists() or not jsonl_dir.exists():
        return []

    seen_slugs: set[str] = set()
    files: list[Path] = []
    for line in data_txt.read_text(encoding="utf-8").splitlines():
        filename = line.strip()
        if not filename:
            continue
        slug = make_unique_slug(filename, seen_slugs)
        seen_slugs.add(slug)
        candidate = jsonl_dir / f"{slug}.jsonl"
        if candidate.exists():
            files.append(candidate)
    return sorted(files)


class CorpusUnavailableError(Exception):
    """A canonical source exists as a path but its content cannot be read."""


_LFS_POINTER_PREFIX = "version https://git-lfs.github.com/spec/"


def load_records(files: list[Path]) -> list[dict]:
    """Load every record, refusing to quietly drop a source it cannot parse.

    `web/corpus_builder/jsonl/dic_mw.jsonl` is LFS-tracked, so a checkout
    without LFS leaves a pointer stub on disk. Reading that used to raise a bare
    JSONDecodeError pointing at "line 1 column 1", which says nothing about the
    cause. Worse would be skipping the file: the gate would then report a
    full-corpus pass over a corpus it had not fully read.
    """
    records: list[dict] = []
    for path in files:
        with open(path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                if lineno == 1 and line.startswith(_LFS_POINTER_PREFIX):
                    raise CorpusUnavailableError(
                        f"{path.name} is a Git LFS pointer, not corpus content. "
                        f"Run `git lfs pull` (or check out with lfs: true in CI). "
                        f"Refusing to report on a corpus this process cannot read."
                    )
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise CorpusUnavailableError(
                        f"{path.name}:{lineno} is not valid JSON ({exc}). "
                        f"Refusing to report on a partially-readable corpus."
                    ) from exc
    return records


def build_report(records: list[dict]) -> DupSuffixReport:
    report = DupSuffixReport(total_records=len(records))
    all_ids = {r["id"] for r in records}

    dup_records = []
    for record in records:
        match = DUP_ID_RE.match(record["id"])
        if match:
            dup_records.append((record, match))

    report.dup_records = len(dup_records)
    report.by_work = dict(Counter(r["work"] for r, _ in dup_records).most_common())
    report.by_suffix = dict(Counter(m.group("suffix") for _, m in dup_records))
    report.by_segment = dict(Counter(r.get("seg") for r, _ in dup_records))

    for record, match in dup_records:
        work = record.get("work", "?")

        # base_present — the structural anti-debris invariant.
        base_id = match.group("base") + match.group("tail")
        if base_id not in all_ids:
            report.violations.append(
                Violation(
                    "base_present",
                    record["id"],
                    work,
                    f"un-suffixed base {base_id!r} is absent — the suffix marks a "
                    f"boundary the splitter invented, not a genuine collision",
                )
            )

        # suffix_depth — collisions are pairs.
        if match.group("suffix") != "b":
            report.violations.append(
                Violation(
                    "suffix_depth",
                    record["id"],
                    work,
                    f"suffix {match.group('suffix')!r} beyond 'b' — a run of suffixes "
                    f"means the splitter walked through one passage repeatedly",
                )
            )

        # segment_pairing.
        seg = record.get("seg")
        if seg not in EXPECTED_SEGMENTS and not record["id"].endswith(".comm"):
            report.violations.append(
                Violation(
                    "segment_pairing",
                    record["id"],
                    work,
                    f"segment {seg!r} is neither a parallel sa/ru pair nor a commentary",
                )
            )

    # concentration — a whole-population invariant, so it is checked once.
    top = report.top_work
    if top and report.dup_records >= CONCENTRATION_MIN_POPULATION:
        work, count = top
        share = count / report.dup_records
        if share > CONCENTRATION_MAX_SHARE:
            report.violations.append(
                Violation(
                    "concentration",
                    "-",
                    work,
                    f"{count}/{report.dup_records} ({share:.0%}) of all suffixed ids are in "
                    f"one work; ceiling {CONCENTRATION_MAX_SHARE:.0%}. The H1829 bug was 79%.",
                )
            )

    if report.dup_records > POPULATION_BACKSTOP:
        report.violations.append(
            Violation(
                "population_backstop",
                "-",
                "-",
                f"{report.dup_records} suffixed ids exceeds the coarse backstop "
                f"{POPULATION_BACKSTOP}; the categorised invariants passed, so this "
                f"is a prompt to re-derive them, not a known defect",
            )
        )

    return report


def render_text(report: DupSuffixReport) -> str:
    lines = [
        "Duplicate-suffix invariant report",
        "=" * 60,
        f"records scanned      : {report.total_records:,}",
        f"suffixed ids         : {report.dup_records}",
        f"works involved       : {len(report.by_work)}",
        f"suffix letters used  : {report.by_suffix or '-'}",
        f"segment distribution : {report.by_segment or '-'}",
        "",
        "Top works:",
    ]
    for work, count in list(report.by_work.items())[:10]:
        share = count / report.dup_records if report.dup_records else 0
        lines.append(f"  {count:>4}  ({share:>4.0%})  {work}")

    lines.append("")
    if report.ok:
        lines.append("PASS  every categorised invariant holds")
    else:
        lines.append(f"FAIL  {len(report.violations)} violation(s)")
        for violation in report.violations[:40]:
            lines.append(f"  [{violation.invariant}] {violation.record_id} ({violation.work})")
            lines.append(f"      {violation.detail}")
    return "\n".join(lines)


def render_markdown(report: DupSuffixReport) -> str:
    today = date.today().strftime("%d-%m-%Y")
    top = report.top_work
    share = (top[1] / report.dup_records) if top and report.dup_records else 0
    rows = "\n".join(
        f"| {work} | {count} | {count / report.dup_records:.0%} |"
        for work, count in list(report.by_work.items())[:15]
    )
    status = "✅ all invariants hold" if report.ok else f"❌ {len(report.violations)} violation(s)"
    return f"""# Duplicate-suffix invariant report

_Created: {today} · Last updated: {today}_

Generated by [`web/scripts/dup_suffix_report.py`](https://github.com/gasyoun/SamudraManthanam/blob/main/web/scripts/dup_suffix_report.py).
Do not hand-edit — re-run the script.

## What this replaces

Duplicate-suffix validation used to be a bare count ceiling with no recorded
derivation (`<= 200`). [H1829](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H1829-Opus_SamudraManthanam_nirvana-tantra-split-verses-footnote-debris_02.08.26.md)
found that ceiling concealing a real defect — nirvana-tantra alone held 284 of
429 suffixed ids because footnote `(N)` markers were read as verse boundaries —
and lowered it to a measured 180. H1927 replaces the ceiling as the *gate* with
categorised structural invariants, per VERIFICATION D7. Counts are still
reported; they no longer decide on their own.

## Measurement

| Metric | Value |
|---|---|
| Records scanned | {report.total_records:,} |
| Suffixed ids | {report.dup_records} |
| Works involved | {len(report.by_work)} |
| Suffix letters used | {report.by_suffix} |
| Segment distribution | {report.by_segment} |
| Largest single work | {top[0] if top else "—"} ({top[1] if top else 0}, {share:.0%}) |
| Status | {status} |

### Distribution by work

| Work | Suffixed ids | Share |
|---|---|---|
{rows}

## The invariants

| Invariant | Rule | What a failure means |
|---|---|---|
| `base_present` | Every `X:N.Nb` has its un-suffixed `X:N.N` | The splitter invented a boundary — the H1829 footnote-debris signature |
| `suffix_depth` | Only `b` is used; collisions are pairs | A `c`/`d` run means the splitter walked through one passage repeatedly |
| `segment_pairing` | Suffixed records are `sa`/`ru` parallel pairs or commentaries | An unexplained segment class carrying a disambiguation suffix |
| `concentration` | No work exceeds {CONCENTRATION_MAX_SHARE:.0%} of the population (once ≥ {CONCENTRATION_MIN_POPULATION}) | One work dominating is the runaway-splitting shape; the H1829 bug was 79% |
| `population_backstop` | Total ≤ {POPULATION_BACKSTOP} | Coarse only. Prompts re-derivation, is not itself evidence of a defect |

Why structural rather than numeric: a count ceiling can only ask *how many*,
and a splitting bug that stays under the number is invisible to it. Three of
the five invariants above cannot be satisfied by any amount of debris, because
debris has the wrong shape — an orphaned suffix, a suffix run, or a single work
carrying the population.

_Dr. Mārcis Gasūns_
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", help="Write the machine-readable report here")
    parser.add_argument("--markdown", help="Write the human report here")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when any invariant is violated (for CI)",
    )
    args = parser.parse_args()

    files = canonical_jsonl_files()
    if not files:
        print(
            "SKIP  canonical JSONL not built (or Programdata/data.txt missing) — "
            "nothing to report on.",
            file=sys.stderr,
        )
        return 0

    try:
        report = build_report(load_records(files))
    except CorpusUnavailableError as exc:
        # Loud and non-zero: an unreadable corpus is not a pass. Reporting
        # "SKIP, exit 0" here is precisely the false-passing gate this report
        # was written to replace.
        print(f"FAIL  corpus unavailable — {exc}", file=sys.stderr)
        return 2

    print(render_text(report))

    if args.json:
        Path(args.json).write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\njson report  -> {args.json}")
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(report), encoding="utf-8")
        print(f"markdown     -> {args.markdown}")

    return 1 if (args.strict and not report.ok) else 0


if __name__ == "__main__":
    raise SystemExit(main())
