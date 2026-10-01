import sys
import os
from datetime import datetime
from pathlib import Path

# Univerzalna putanja za izlaz
ROOT = Path.home() / "projekti" / "moj_prvi_projekat" / "izlaz" / "dokumenti"
ROOT.mkdir(parents=True, exist_ok=True)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
except ModuleNotFoundError:
    print("RESULT=HOLD")
    print("MISSING_PYTHON_MODULE=No module named 'reportlab'")
    sys.exit(20)

def napravi_memorandum(klijent="INTERNA KOMANDA", predmet="Status Sistema", tekst="Titan Protokol 888 je potpuno operativan na svim čvorovima."):
    # Generisanje jedinstvenog imena fajla sa vremenskim žigom
    vrijeme_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    naziv_fajla = f"Memorandum_{vrijeme_str}.pdf"
    target = ROOT / naziv_fajla
    
    doc = SimpleDocTemplate(str(target), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Naslov
    story.append(Paragraph("TITAN GRID - SLUŽBENI MEMORANDUM", styles['Title']))
    story.append(Spacer(1, 20))

    # Tabela za zaglavlje (Meta podaci)
    podaci_zaglavlja = [
        ["Datum:", datetime.now().strftime("%d.%m.%Y")],
        ["Klijent/Sektor:", klijent],
        ["Predmet:", predmet]
    ]
    tabela = Table(podaci_zaglavlja, colWidths=[100, 300])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    story.append(tabela)
    story.append(Spacer(1, 30))

    # Glavni tekst
    story.append(Paragraph(tekst, styles['Normal']))
    
    # Izrada PDF-a
    doc.build(story)
    return str(target)

if __name__ == "__main__":
    out_path = napravi_memorandum(
        klijent="DIREKCIJA (Test)",
        predmet="Implementacija novog PDF šablona",
        tekst="Ovo je automatski generisan dokument. Arhitektura sa zaglavljima, tabelama i dinamičkim nazivima fajlova je uspješno integrisana."
    )
    print(f"MEMORANDUM_CREATED={out_path}")
