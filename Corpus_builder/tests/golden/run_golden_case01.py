"""H2427 golden capture / re-verify for Corpus_builder case01."""
from __future__ import annotations
import hashlib, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # Corpus_builder/
CASE = Path(__file__).resolve().parent / "case01"
INP = CASE / "input"
EXP = CASE / "expected"
EXE_CANDIDATES = [
    ROOT / "PSRCBuilder" / "lib" / "x86_64-win64" / "cb_headless.exe",
    ROOT / "PSRCBuilder" / "lib" / "i386-win32" / "cb_headless.exe",
    ROOT / "PSRCBuilder" / "lib" / "x86_64-linux" / "cb_headless",
]
SHELL = (
    "<!DOCTYPE html>\n"
    "<html><head><meta charset=\"UTF-8\"><title>golden case01</title></head>\n"
    "<body>\n"
    "<!-- Insert code block beginning -->\n"
    "<!-- Insert code block end -->\n"
    "</body></html>\n"
)
TRACKED = [
    "case01_out.html",
    "Err.txt",
    "Res_html.txt",
    "02_Transl_err.txt",
    "02_Transl_check.json",
    "02_Transl_check.tsv",
]


def find_exe() -> Path:
    for p in EXE_CANDIDATES:
        if p.is_file():
            return p
    raise SystemExit(
        "cb_headless.exe not found — run: lazbuild Corpus_builder/PSRCBuilder/cb_headless.lpi"
    )


def to_repo_bytes(data: bytes) -> bytes:
    """Match org * text=auto eol=lf — engine Writeln on Windows emits CRLF."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def normalize_file(path: Path) -> None:
    raw = path.read_bytes()
    norm = to_repo_bytes(raw)
    if norm != raw:
        path.write_bytes(norm)


def clean_ephemeral() -> None:
    keep = {
        "01_Sanskrit.txt",
        "02_Transl.txt",
        "03_Comments.txt",
        "config.ini",
        "case01_out.html",
    }
    for p in list(INP.iterdir()):
        if p.name not in keep:
            p.unlink()
    (INP / "case01_out.html").write_text(SHELL, encoding="utf-8", newline="\n")


def run_headless() -> None:
    exe = find_exe()
    clean_ephemeral()
    r = subprocess.run(
        [str(exe), str(INP), "check"],
        cwd=str(INP),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    missing = [n for n in TRACKED if not (INP / n).is_file()]
    if missing:
        raise SystemExit(f"headless did not produce: {missing}")
    for n in TRACKED:
        normalize_file(INP / n)


def capture() -> None:
    run_headless()
    EXP.mkdir(parents=True, exist_ok=True)
    for n in TRACKED:
        shutil.copy2(INP / n, EXP / n)
        h = hashlib.sha256((EXP / n).read_bytes()).hexdigest()[:12]
        print(f"captured {n} sha256={h}")


def verify() -> int:
    if not EXP.is_dir() or not any(EXP.iterdir()):
        raise SystemExit("expected/ empty — run with --capture first")
    run_headless()
    bad = []
    for n in TRACKED:
        a, b = EXP / n, INP / n
        if not b.is_file():
            bad.append(f"missing produced {n}")
            continue
        ea, eb = to_repo_bytes(a.read_bytes()), to_repo_bytes(b.read_bytes())
        if ea != eb:
            bad.append(f"DIFF {n} expected={len(ea)}B got={len(eb)}B")
        else:
            print(f"MATCH {n}")
    if bad:
        print("FAIL:")
        for line in bad:
            print(" ", line)
        return 1
    print("PASS: all golden files byte-identical (LF-normalized)")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in {"--capture", "--verify"}:
        print("Usage: run_golden_case01.py --capture | --verify")
        return 2
    if argv[1] == "--capture":
        capture()
        return 0
    return verify()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
