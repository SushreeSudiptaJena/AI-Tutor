"""Render the team-facing markdown docs to PDF.

    .venv/Scripts/python.exe scripts/make_docs_pdf.py

Needs fpdf2 (a docs-only tool, deliberately NOT in backend/requirements.txt):

    .venv/Scripts/python.exe -m pip install fpdf2

Supports the small subset of markdown the docs actually use: headings,
paragraphs, bullet and numbered lists, fenced code, tables, blockquotes,
horizontal rules, and inline **bold** / `code`.
"""

import re
import sys
import unicodedata
from pathlib import Path

from fpdf import FPDF

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
OUT = DOCS / "pdf"

PAGES = [
    ("team-roles.md", "Team Roles and How It Merges"),
    ("frontend-guide.md", "Frontend Guide"),
    ("database-guide.md", "Database Guide"),
    ("ai-guide.md", "AI / ML Guide"),
    ("api-contract.md", "API Contract"),
]

INK = (17, 17, 17)
MUTED = (110, 110, 110)
RULE = (215, 215, 215)
CODE_BG = (245, 245, 245)
ACCENT = (150, 40, 40)

# The built-in fonts are latin-1 only; map the typography we use down to ASCII.
SUBS = {
    "—": "-", "–": "-", "‘": "'", "’": "'",
    "“": '"', "”": '"', "…": "...", "→": "->",
    "←": "<-", "≤": "<=", "≥": ">=", "·": "-",
    "•": "-", " ": " ", "‑": "-", "×": "x",
    "✓": "[ok]", "✗": "[x]",
}


def ascii_safe(text: str) -> str:
    for bad, good in SUBS.items():
        text = text.replace(bad, good)
    text = unicodedata.normalize("NFKD", text)
    return text.encode("latin-1", "replace").decode("latin-1")


class Doc(FPDF):
    def __init__(self, title: str):
        super().__init__(format="A4", unit="mm")
        self.doc_title = title
        self.set_auto_page_break(True, margin=18)
        self.set_margins(20, 18, 20)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", size=7)
        self.set_text_color(*MUTED)
        self.cell(0, 5, ascii_safe(f"AI Tutor - {self.doc_title}"), align="L")
        self.cell(0, 5, str(self.page_no()), align="R")

    # -- inline **bold** and `code` ------------------------------------------
    def rich(self, text: str, size: float = 9.5, height: float = 5.0):
        parts = re.split(r"(\*\*[^*]+\*\*|\*[^*`]+\*|`[^`]+`)", text)
        for part in parts:
            if not part:
                continue
            if part.startswith("**") and part.endswith("**"):
                self.set_font("Helvetica", "B", size)
                self.set_text_color(*INK)
                body = part[2:-2]
            elif part.startswith("*") and part.endswith("*") and len(part) > 2:
                self.set_font("Helvetica", "I", size)
                self.set_text_color(*INK)
                body = part[1:-1]
            elif part.startswith("`") and part.endswith("`"):
                self.set_font("Courier", "", size - 0.5)
                self.set_text_color(*ACCENT)
                body = part[1:-1]
            else:
                self.set_font("Helvetica", "", size)
                self.set_text_color(*INK)
                body = part
            self.write(height, ascii_safe(body))
        self.ln(height)


def render(md_path: Path, title: str, out_path: Path) -> int:
    lines = md_path.read_text(encoding="utf-8").split("\n")
    pdf = Doc(title)
    pdf.add_page()

    # cover block
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*INK)
    pdf.multi_cell(0, 9, ascii_safe(title))
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 6, ascii_safe("AI Tutor - SOAIDEATHON-S28 - 6 people, 36 hours"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    i, n = 0, len(lines)
    while i < n:
        raw = lines[i].rstrip()
        stripped = raw.strip()

        # skip the markdown H1, the cover already shows it
        if stripped.startswith("# ") and pdf.page_no() == 1 and pdf.get_y() < 60:
            i += 1
            continue

        # fenced code
        if stripped.startswith("```"):
            i += 1
            block = []
            while i < n and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            pdf.ln(1.5)
            pdf.set_font("Courier", "", 7.6)
            pdf.set_text_color(40, 40, 40)
            pdf.set_fill_color(*CODE_BG)
            for cl in block:
                text = ascii_safe(cl.replace("\t", "    "))
                while len(text) > 96:                     # hard-wrap long code
                    pdf.cell(0, 3.9, "  " + text[:96], new_x="LMARGIN", new_y="NEXT", fill=True)
                    text = text[96:]
                pdf.cell(0, 3.9, "  " + text, new_x="LMARGIN", new_y="NEXT", fill=True)
            pdf.ln(2.5)
            continue

        # table
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            avail = pdf.w - pdf.l_margin - pdf.r_margin
            widths = [avail / len(header)] * len(header)
            if len(header) == 2:
                widths = [avail * 0.34, avail * 0.66]
            pdf.ln(1.5)
            pdf.set_font("Helvetica", "B", 8.2)
            pdf.set_text_color(*INK)
            pdf.set_fill_color(238, 238, 238)
            for w, cell in zip(widths, header):
                pdf.cell(w, 6, ascii_safe(re.sub(r"[*`]", "", cell))[:60], border=0, fill=True)
            pdf.ln(6)
            pdf.set_font("Helvetica", "", 8.2)
            for r in rows:
                cells = [ascii_safe(re.sub(r"[*`]", "", c)) for c in r]
                heights = [max(1, int(len(c) / max(8, int(w / 1.7))) + 1) for c, w in zip(cells, widths)]
                rh = max(heights) * 4.4
                if pdf.get_y() + rh > pdf.h - 20:
                    pdf.add_page()
                y0 = pdf.get_y()
                x = pdf.l_margin
                for w, c in zip(widths, cells):
                    pdf.set_xy(x, y0)
                    pdf.multi_cell(w, 4.4, c, align="L")
                    x += w
                pdf.set_xy(pdf.l_margin, y0 + rh)
                pdf.set_draw_color(*RULE)
                pdf.line(pdf.l_margin, pdf.get_y() - 0.6, pdf.w - pdf.r_margin, pdf.get_y() - 0.6)
            pdf.ln(2.5)
            continue

        if not stripped:
            pdf.ln(2.2)
            i += 1
            continue

        if stripped.startswith("---"):
            pdf.ln(1.5)
            pdf.set_draw_color(*RULE)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)
            i += 1
            continue

        if stripped.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(*INK)
            pdf.multi_cell(0, 5.6, ascii_safe(re.sub(r"[*`]", "", stripped[4:])))
            pdf.ln(0.8)
            i += 1
            continue

        if stripped.startswith("## "):
            if pdf.get_y() > pdf.h - 45:
                pdf.add_page()
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(*INK)
            pdf.multi_cell(0, 7, ascii_safe(re.sub(r"[*`]", "", stripped[3:])))
            pdf.set_draw_color(*RULE)
            pdf.line(pdf.l_margin, pdf.get_y() + 0.6, pdf.w - pdf.r_margin, pdf.get_y() + 0.6)
            pdf.ln(3)
            i += 1
            continue

        if stripped.startswith("# "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 15)
            pdf.set_text_color(*INK)
            pdf.multi_cell(0, 8, ascii_safe(re.sub(r"[*`]", "", stripped[2:])))
            pdf.ln(1.5)
            i += 1
            continue

        if stripped.startswith("> "):
            pdf.set_fill_color(249, 246, 240)
            pdf.set_draw_color(210, 180, 120)
            y0 = pdf.get_y()
            pdf.set_font("Helvetica", "I", 9.5)
            pdf.set_text_color(70, 60, 45)
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 3, 5, ascii_safe(re.sub(r"[*`]", "", stripped[2:])), fill=True)
            pdf.line(pdf.l_margin + 0.8, y0, pdf.l_margin + 0.8, pdf.get_y())
            pdf.ln(2)
            i += 1
            continue

        m_ol = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if stripped.startswith("- ") or m_ol:
            marker = f"{m_ol.group(1)}." if m_ol else "-"
            body = m_ol.group(2) if m_ol else stripped[2:]
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(*MUTED)
            pdf.cell(6, 5, marker)
            pdf.set_x(pdf.l_margin + 6)
            pdf.rich(body, size=9.5)
            i += 1
            continue

        pdf.rich(stripped, size=9.5, height=5.0)
        i += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return pdf.page_no()


def main() -> None:
    made = []
    for name, title in PAGES:
        src = DOCS / name
        if not src.exists():
            print(f"  skip (missing): {name}")
            continue
        dst = OUT / (src.stem + ".pdf")
        pages = render(src, title, dst)
        made.append((dst.relative_to(REPO_ROOT).as_posix(), pages, dst.stat().st_size))
    print(f"wrote {len(made)} PDFs to docs/pdf/")
    for path, pages, size in made:
        print(f"  {path:38} {pages:>2} pages  {size/1024:6.1f} KB")


if __name__ == "__main__":
    sys.exit(main())
