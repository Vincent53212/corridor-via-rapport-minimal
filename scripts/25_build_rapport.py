"""Étape 25 — Rendu Word du rapport : rapport.md → livrables/rapport_corridor.docx.
Citations APA via --citeproc (sources/refs.bib + sources/apa.csl). Corps justifié
par post-traitement python-docx, pandoc ne sachant pas le faire à l'export.

Le PDF ne sort PLUS d'ici. Il est composé à l'identité du document par les
étapes 29 (rapport.md → HTML) et 30 (HTML → PDF paginé, sommaire à folios réels).
La sortie xelatex qui vivait ici écrivait au même chemin et écrasait donc le PDF
composé selon l'ordre de lancement. Le docx, lui, reste un livrable : c'est le
format dans lequel le client annote et renvoie ses commentaires."""
import subprocess
import sys
from utils import PROJECT_ROOT, DELIVERABLES

DOCX = DELIVERABLES / "rapport_corridor.docx"

CMD = [
    "pandoc", "rapport.md", "--citeproc",
    "--bibliography", "sources/refs.bib", "--csl", "sources/apa.csl",
    "-o", str(DOCX),
]

r = subprocess.run(CMD, cwd=PROJECT_ROOT, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout); print(r.stderr)
    sys.exit("Échec : pandoc (docx)")
if r.stderr.strip():
    print(r.stderr.strip())

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
doc = Document(str(DOCX))
for name in ("Normal", "Body Text", "First Paragraph"):
    try:
        doc.styles[name].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    except KeyError:
        pass
# Lignes de total en gras, comme dans le PDF (première cellule « Total… »).
n_totaux = 0
for table in doc.tables:
    for row in table.rows:
        if row.cells and row.cells[0].text.strip().startswith("Total"):
            n_totaux += 1
            for cell in row.cells:
                for par in cell.paragraphs:
                    for run in par.runs:
                        run.bold = True
doc.save(str(DOCX))
print(f"Écrit {DOCX.name} (corps justifié, {n_totaux} lignes de total en gras)")
