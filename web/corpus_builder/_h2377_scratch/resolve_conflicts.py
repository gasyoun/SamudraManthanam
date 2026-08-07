#!/usr/bin/env python3
"""Resolve remaining merge conflicts in ignatiev_book_to_canonical.py."""
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

path = Path(__file__).resolve().parents[1] / "ignatiev_book_to_canonical.py"
text = path.read_text(encoding="utf-8")

# --- conflict 1: extractors (keep both pymupdf + pypdf + rtf) ---
pat1 = re.compile(
    r"<<<<<<< HEAD\n"
    r"(def _extract_pdf_pymupdf[\s\S]*?return \"\\x0c\"\.join\(parts\))\n"
    r"=======\n"
    r"(def _extract_pdf_pypdf[\s\S]*?return text \+ \"\\n\")\n"
    r">>>>>>> origin/main\n",
)
m = pat1.search(text)
if m:
    repl = m.group(1) + "\n\n" + m.group(2) + "\n"
    text = text[: m.start()] + repl + text[m.end() :]
    print("resolved extractors")
else:
    print("pat1 no match")

# --- conflict 2: pdf comment ---
pat2 = re.compile(
    r"<<<<<<< HEAD\n"
    r"(?P<head>        # Prefer poppler[\s\S]*?H2377\)\.\n)"
    r"=======\n"
    r"(?P<theirs>        # Prefer pdftotext[\s\S]*?H2376[^\n]*\n)"
    r">>>>>>> origin/main\n",
)
if pat2.search(text):
    text = pat2.sub(
        "        # Prefer pdftotext (form-feeds for glued-digit H2377).\n"
        "        # Fall back: pymupdf (keeps page markers) then pypdf (H2376).\n",
        text,
        count=1,
    )
    print("resolved pdf comment")
else:
    print("pat2 no match")

# --- conflict 3: pdf return ---
pat3 = re.compile(
    r"<<<<<<< HEAD\n"
    r"            # Keep \\x0c as page markers for strip_glued_digit_page_notes;\n"
    r"            # only normalise when the caller reflows \(body path\)\.\n"
    r"            return out\.stdout\n"
    r"        return _extract_pdf_pymupdf\(path\)\n"
    r"=======\n"
    r"            # pdftotext prepends a form-feed to the first line of every page\.\n"
    r"            return out\.stdout\.replace\(\"\\x0c\", \"\\n\"\)\n"
    r"        return _extract_pdf_pypdf\(path\)\n"
    r">>>>>>> origin/main\n",
)
def _merge_one(m):
    head, theirs = m.group(1), m.group(2)
    if "aggressive_debris" in head:
        return (
            "        verses = split_verses(\n"
            "            body, aggressive_debris=(mode == \"glued-digit\"),\n"
            "        )\n"
            "        # H2376: some partials (Bhāgavata-purāṇa RTF) are prose with chapter\n"
            "        # heads but no trailing ``(N)`` verse markers. Fall back to\n"
            "        # blank-line paragraphs as sequential units so the chapter is not\n"
            "        # silently emptied. Flagged in the report as prose_paragraph_split.\n"
            "        if not verses and any(ln.strip() for ln in ch[\"body\"]):\n"
            "            paras = [\n"
            "                re.sub(r\"\\s+\", \" \", p).strip()\n"
            "                for p in re.split(r\"\\n\\s*\\n\", \"\\n\".join(ch[\"body\"]))\n"
            "                if p.strip()\n"
            "            ]\n"
            "            verses = [\n"
            "                {\"verse\": str(i), \"text\": para, \"author\": None}\n"
            "                for i, para in enumerate(paras, 1)\n"
            "                if para\n"
            "            ]\n"
            "            if verses:\n"
            "                report.setdefault(\n"
            "                    \"prose_paragraph_split_chapters\", []\n"
            "                ).append(chn)\n"
            "        if mode == \"glued-digit\":\n"
            "            fn_numbers = all_fn_numbers\n"
            "            link_fn = link_footnotes_glued\n"
            "        else:\n"
            "            fn_numbers = {\n"
            "                fn for fn, note in fn_map.items()\n"
            "                if note.get(\"chapter\") == chn\n"
            "            }\n"
            "            link_fn = link_footnotes\n"
        )
    if "Keep" in head and "pypdf" in theirs:
        return (
            "            # Keep \\x0c as page markers for strip_glued_digit_page_notes.\n"
            "            return out.stdout\n"
            "        try:\n"
            "            return _extract_pdf_pymupdf(path)\n"
            "        except RuntimeError:\n"
            "            return _extract_pdf_pypdf(path)\n"
        )
    if "Prefer poppler" in head or "Prefer pdftotext" in theirs:
        return (
            "        # Prefer pdftotext (form-feeds for glued-digit H2377).\n"
            "        # Fall back: pymupdf (keeps page markers) then pypdf (H2376).\n"
        )
    if "_extract_pdf_pymupdf" in head:
        return head + "\n" + theirs
    print("UNHANDLED conflict:", head[:80].replace("\n", " "))
    return head + theirs


pat_any = re.compile(
    r"<<<<<<< HEAD\n([\s\S]*?)=======\n([\s\S]*?)>>>>>>> origin/main\n",
)
text, n = pat_any.subn(_merge_one, text)
print("remaining conflicts resolved", n)

path.write_text(text, encoding="utf-8")
left = text.count("<<<<<<<")
print("conflicts left", left)
try:
    ast.parse(text)
    print("syntax OK")
except SyntaxError as e:
    print("syntax error", e, "line", e.lineno)
