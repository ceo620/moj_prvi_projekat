import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Registracija DejaVuSans TTF fonta za punu č, ć, đ, š, ž podršku
FONT_NAME = "Helvetica"
DEJAVU_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DEJAVU_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

if os.path.exists(DEJAVU_PATH):
    pdfmetrics.registerFont(TTFont('DejaVuSans', DEJAVU_PATH))
    FONT_NAME = 'DejaVuSans'

if os.path.exists(DEJAVU_BOLD_PATH):
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', DEJAVU_BOLD_PATH))
    FONT_BOLD_NAME = 'DejaVuSans-Bold'
else:
    FONT_BOLD_NAME = FONT_NAME

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont(FONT_NAME, 9)
        self.setFillColor(colors.HexColor("#666666"))
        
        # Zaglavlje
        self.setStrokeColor(colors.HexColor("#1A365D"))
        self.setLineWidth(1)
        self.line(40, 800, 555, 800)
        self.drawString(40, 808, "TITAN GRID 888 — AUTOMATIZOVANI SISTEM")
        
        # Podnožje
        self.line(40, 45, 555, 45)
        page_text = f"Stranica {self._pageNumber} od {page_count}"
        self.drawRightString(555, 30, page_text)
        self.drawString(40, 30, "POVJERLJIVO — Za internu upotrebu")
        self.restoreState()

def napravi_memorandum(klijent="N/A", predmet="N/A", tekst=""):
    izlaz_dir = os.path.join(os.getcwd(), "izlaz", "dokumenti")
    os.makedirs(izlaz_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Memorandum_{timestamp}.pdf"
    filepath = os.path.join(izlaz_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=60,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=FONT_BOLD_NAME,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=15
    )
    
    label_style = ParagraphStyle(
        'MetaLabel',
        fontName=FONT_BOLD_NAME,
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#2B6CB0")
    )
    
    val_style = ParagraphStyle(
        'MetaVal',
        fontName=FONT_NAME,
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#2D3748")
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#1A202C"),
        spaceBefore=10
    )

    elements = []
    elements.append(Paragraph("TITAN GRID - SLUŽBENI MEMORANDUM", title_style))
    elements.append(Spacer(1, 10))

    datum_str = datetime.now().strftime("%d.%m.%Y.")
    data = [
        [Paragraph("Datum:", label_style), Paragraph(datum_str, val_style)],
        [Paragraph("Klijent/Sektor:", label_style), Paragraph(klijent, val_style)],
        [Paragraph("Predmet:", label_style), Paragraph(predmet, val_style)]
    ]

    t = Table(data, colWidths=[110, 405])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(tekst.replace('\n', '<br/>'), body_style))

    doc.build(elements, canvasmaker=NumberedCanvas)
    return filepath

if __name__ == "__main__":
    p = napravi_memorandum("TEST KLIJENT", "Test ŽĆČŠĐ Fonta", "Potvrđujemo da su slova č, ć, đ, š, ž 100% ispravno prikazana.")
    print(f"[OK] Test memorandum kreiran: {p}")
