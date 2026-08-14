#!/usr/bin/env python3
"""Generate ERRATA.md from each work's errata.yml (SanskritGrammar shape).

    python web/corpus_builder/build_errata.py
    python web/corpus_builder/build_errata.py bhagavati-manasa-puja-stotra
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import errata_yml as ey  # noqa: E402


def generate_one(work_dir: Path) -> Path:
    src = work_dir / "errata.yml"
    if not src.is_file():
        raise SystemExit(f"no errata.yml in {work_dir}")
    loaded = ey.load_errata_yml(src)
    md = ey.generate_errata_md(
        loaded.get("work") or work_dir.name,
        loaded["entries"],
        source_name="errata.yml",
    )
    dest = work_dir / "ERRATA.md"
    dest.write_text(md, encoding="utf-8")
    return dest


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        dirs = [ey.ERRATA_ROOT / a for a in args]
    else:
        dirs = sorted(p for p in ey.ERRATA_ROOT.iterdir() if p.is_dir()) if ey.ERRATA_ROOT.exists() else []
    if not dirs:
        raise SystemExit(f"no errata works under {ey.ERRATA_ROOT}")
    for work_dir in dirs:
        dest = generate_one(work_dir)
        print(f"wrote {dest.relative_to(ey._REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
