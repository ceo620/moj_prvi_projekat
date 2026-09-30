import sys
import os
from pathlib import Path

# Prilagođavanje putanje prema R8-25 (Android/Termux fallback)
primary_root = Path("/mnt/c/Users/ceo/OneDrive/Desktop/FIRMA_DOKUMENTACIJA")

try:
    if os.path.exists("/mnt/c"):
        ROOT = primary_root
    else:
        ROOT = Path.home() / "projekti" / "moj_prvi_projekat" / "out" / "FIRMA_DOKUMENTACIJA"
    ROOT.mkdir(parents=True, exist_ok=True)
except Exception:
    ROOT = Path.home() / "projekti" / "moj_prvi_projekat" / "out" / "FIRMA_DOKUMENTACIJA"
    ROOT.mkdir(parents=True, exist_ok=True)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except ModuleNotFoundError:
    print("RESULT=HOLD")
    print("MISSING_PYTHON_MODULE=No module named 'reportlab'")
    sys.exit(20)

def napravi_memorandum(naziv_fajla="memorandum.pdf", naslov="TITAN GRID", tekst="Sistem aktivan"):
    target = ROOT / naziv_fajla
    doc = SimpleDocTemplate(str(target), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(naslov, styles['Heading1']), Spacer(1, 12), Paragraph(tekst, styles['Normal'])]
    doc.build(story)
    return str(target)

if __name__ == "__main__":
    out_path = napravi_memorandum()
    print(f"MEMORANDUM_CREATED={out_path}")
