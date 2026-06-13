"""A1 — Font subset + woff2 conversion.

Reads all codepoints from the JSONL corpus, then uses fonttools pyftsubset to:
  - Charis SIL (×3 variants): Latin + IAST + Cyrillic + Greek + IPA + misc
  - Sahitya:  Devanagari + Basic Latin only

Outputs web/static/fonts/*.woff2. Overwrites previous runs safely (idempotent).
Run from the repo root:
  python web/scripts/subset_fonts.py
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).parent.parent.parent
JSONL_DIR  = REPO_ROOT / "web" / "corpus_builder" / "jsonl"
FONTS_DIR  = REPO_ROOT / "web" / "static" / "fonts"

# ------------------------------------------------------------------
# Step 1: collect all unique codepoints across the full corpus
# ------------------------------------------------------------------

def collect_codepoints() -> set[int]:
    cps: set[int] = set()
    for p in sorted(JSONL_DIR.glob("*.jsonl")):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                for field in ("text", "html"):
                    for ch in (rec.get(field) or ""):
                        cps.add(ord(ch))
    return cps

# ------------------------------------------------------------------
# Step 2: subset helpers
# ------------------------------------------------------------------

def cps_to_unicodes_arg(cps: set[int]) -> str:
    """Convert a set of codepoints to a pyftsubset --unicodes= value."""
    return ",".join(f"U+{cp:04X}" for cp in sorted(cps))

def run_subset(src: Path, dst: Path, unicodes_arg: str, layout_features: str = "*") -> None:
    cmd = [
        sys.executable, "-m", "fontTools.subset",
        str(src),
        f"--output-file={dst}",
        "--flavor=woff2",
        f"--unicodes={unicodes_arg}",
        f"--layout-features={layout_features}",
        "--no-hinting",
        "--desubroutinize",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:400]}", file=sys.stderr)
    src_kb  = src.stat().st_size  // 1024
    dst_kb  = dst.stat().st_size  // 1024 if dst.exists() else 0
    print(f"  {src.name} → {dst.name}: {src_kb} KB → {dst_kb} KB")


# ------------------------------------------------------------------
# Step 3: main
# ------------------------------------------------------------------

def main() -> None:
    print("Collecting corpus codepoints…")
    all_cps = collect_codepoints()
    print(f"  {len(all_cps)} unique codepoints in corpus")

    # Devanagari block — served by Sahitya only
    devanagari = {cp for cp in all_cps if 0x0900 <= cp <= 0x097F or 0x1CD0 <= cp <= 0x1CFF}
    # Everything else → Charis SIL
    charis_cps = (all_cps - devanagari) | {
        # Always keep basic control chars and common punctuation even if not
        # in corpus (they appear in template chrome and site UI)
        0x0009, 0x000A, 0x000D,                  # tab, LF, CR
        *range(0x0020, 0x0080),                   # full Basic Latin
        *range(0x00A0, 0x0100),                   # Latin-1 Supplement
    }

    # Add Devanagari + Basic Latin for Sahitya subset
    sahitya_cps = devanagari | set(range(0x0020, 0x0080)) | {0x00A0}

    charis_arg  = cps_to_unicodes_arg(charis_cps)
    sahitya_arg = cps_to_unicodes_arg(sahitya_cps)

    fonts = [
        ("charis-sil.ttf",        "charis-sil.woff2",        charis_arg),
        ("charis-sil-bold.ttf",   "charis-sil-bold.woff2",   charis_arg),
        ("charis-sil-italic.ttf", "charis-sil-italic.woff2", charis_arg),
        ("Sahitya-Regular.ttf",   "Sahitya-Regular.woff2",   sahitya_arg),
    ]

    print("\nSubsetting and converting to woff2…")
    total_src = total_dst = 0
    for src_name, dst_name, uarg in fonts:
        src = FONTS_DIR / src_name
        dst = FONTS_DIR / dst_name
        if not src.exists():
            print(f"  SKIP {src_name} — not found")
            continue
        run_subset(src, dst, uarg)
        total_src += src.stat().st_size
        total_dst += dst.stat().st_size if dst.exists() else 0

    print(f"\nTotal: {total_src // 1024} KB TTF → {total_dst // 1024} KB woff2")
    print(f"Reduction: {100 * (1 - total_dst / total_src):.0f}%")

if __name__ == "__main__":
    main()
