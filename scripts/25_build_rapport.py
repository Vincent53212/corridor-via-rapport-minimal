"""Étape 25 — Rendu du rapport : rapport.md → livrables/rapport_corridor.{docx,pdf}.
Citations APA via --citeproc (sources/refs.bib + sources/apa.csl). Texte justifié
partout : par défaut en LaTeX (PDF) ; pour le docx, post-traitement python-docx
qui met les styles de corps en alignement justifié."""
import subprocess
import sys
from utils import PROJECT_ROOT, DELIVERABLES

DOCX = DELIVERABLES / "rapport_corridor.docx"
PDF = DELIVERABLES / "rapport_corridor.pdf"

COMMON = [
    "pandoc", "rapport.md", "--citeproc",
    "--bibliography", "sources/refs.bib", "--csl", "sources/apa.csl",
]

def run(args):
    r = subprocess.run(args, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout); print(r.stderr)
        sys.exit(f"Échec : {' '.join(args[:3])}…")
    if r.stderr.strip():
        print(r.stderr.strip())

# 1) DOCX, puis justification des styles de corps
run(COMMON + ["-o", str(DOCX)])
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
doc = Document(str(DOCX))
for name in ("Normal", "Body Text", "First Paragraph"):
    try:
        doc.styles[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    except KeyError:
        pass
doc.save(str(DOCX))
print(f"Écrit {DOCX.name} (corps justifié)")

# 2) PDF (xelatex ; LaTeX justifie par défaut)
run(COMMON + ["--pdf-engine=xelatex",
              "-V", "geometry:margin=2.5cm", "-V", "fontsize=11pt",
              "-V", "mainfont:Cambria",  # Latin Modern n'a pas « ≤ » (U+2264)
              "-o", str(PDF)])
print(f"Écrit {PDF.name}")
