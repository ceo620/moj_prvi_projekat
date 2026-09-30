import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# =========================================================
# 1. AUDIT & LOGGING ENGINE (Forenzički trag)
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | [TITAN-AUDIT] | %(message)s",
    handlers=[logging.FileHandler("TITAN_MASTER_AUDIT.log"), logging.StreamHandler()]
)

class TitanForensicArchitect:
    def __init__(self, project_name, owner):
        self.doc = Document()
        self.project = project_name
        self.owner = owner
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._setup_iso_style()
        logging.info(f"Inicijalizacija: {project_name} | Autor: {owner}")

    def _setup_iso_style(self):
        """Postavljanje EU bankarskih standarda (ISO margina)."""
        for section in self.doc.sections:
            section.top_margin, section.bottom_margin = Cm(2.5), Cm(2.5)
            section.left_margin, section.right_margin = Cm(2.5), Cm(2.5)
        
        style = self.doc.styles['Normal']
        style.font.name = 'Arial'
        style.font.size = Pt(10.5)

    def add_audit_header(self, doc_id):
        """Header koji revizori koriste za verifikaciju verzije."""
        header = self.doc.sections[0].header.paragraphs[0]
        header.text = f"CONFIDENTIAL | ID: {doc_id} | VER: 2026.4.1 | TIMESTAMP: {self.timestamp}"
        header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        # Metadata za file properties (ključno za forenziku)
        self.doc.core_properties.author = self.owner
        self.doc.core_properties.title = f"{self.project} Master Audit"

    def inject_strategic_content(self):
        """Integracija v13 Autonomous Factory & v11 CFO logike."""
        self.doc.add_heading(self.project, 0)
        
        # Tehnički stub (v13)
        self.doc.add_heading('1. TEHNIČKA ARHITEKTURA (Industry 4.0)', level=1)
        p = self.doc.add_paragraph()
        p.add_run("Lokacija: Tuzi, Montenegro (Greenfield site 22,742 m²).\n").bold = True
        p.add_run("Sistem: Digital Twin procesna logika sa integrisanim 1.4 MWp solarnim sistemom (ESG).")

    def add_bankable_table(self, title, data):
        """Tabela formatirana za Tier-1 investitore."""
        self.doc.add_heading(title, level=2)
        table = self.doc.add_table(rows=1, cols=len(data[0]))
        table.style = 'Table Grid'
        
        # Header formatting
        hdr_cells = table.rows[0].cells
        for i, name in enumerate(data[0]):
            hdr_cells[i].text = name
            run = hdr_cells[i].paragraphs[0].runs[0]
            run.bold = True
            run.font.color.rgb = RGBColor(30, 50, 100)

        # Data injection
        for row_data in data[1:]:
            row_cells = table.add_row().cells
            for i, item in enumerate(row_data):
                row_cells[i].text = str(item)
        logging.info(f"Tabela generisana: {title}")

    def finalize(self, filename):
        """Sigurno snimanje i pokretanje."""
        save_path = Path.cwd() / filename
        self.doc.save(str(save_path))
        logging.info(f"DOKUMENT SPREMAN: {save_path}")
        if os.name == 'nt':
            os.startfile(save_path)

# =========================================================
# 2. IZVRŠNI MODUL (Onur - CFO Command)
# =========================================================
if __name__ == "__main__":
    # Podaci iz tvog profila i v4/v7/v13 skripti
    OWNER_INFO = "Onur - CFO & Owner Marel Engineering"
    
    architect = TitanForensicArchitect("TITAN GRID - ARS METAL", OWNER_INFO)
    architect.add_audit_header("TG-ME-2026-X1")
    architect.inject_strategic_content()
    
    # CAPEX podaci integrisani iz tvog Excel outputa
    capex_data = [
        ["Kategorija", "Iznos (€)", "Status Revizije"],
        ["Civil Works (Tuzi)", "2.500.000", "Potvrđeno (v4)"],
        ["Robotics (Autonomous)", "1.200.000", "Tender (v13)"],
        ["Solar (ESG Compliance)", "450.000", "Planirano"],
        ["Rezerva (Risk Buffer)", "622.500", "Kalkulisano (v11)"]
    ]
    
    architect.add_bankable_table("STRATEŠKA ALOKACIJA KAPITALA", capex_data)
    
    architect.finalize("TITAN_MASTER_AUDIT_REPORT.docx")