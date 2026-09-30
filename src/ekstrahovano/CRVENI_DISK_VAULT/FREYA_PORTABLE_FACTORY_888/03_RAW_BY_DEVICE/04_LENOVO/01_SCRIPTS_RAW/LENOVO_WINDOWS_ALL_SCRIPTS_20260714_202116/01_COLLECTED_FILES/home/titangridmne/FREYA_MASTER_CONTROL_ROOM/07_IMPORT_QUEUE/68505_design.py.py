from fpdf import FPDF

class TITAN_DataRoom_Architect(FPDF):
    def header(self):
        # Professional Header for EU Standards
        self.set_font('Arial', 'B', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'TITAN GRID | PROJECT CONFIDENTIAL', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        # Version Control and EU Compliance footer
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Doc ID: TG-EU-2026-04 | Montenegro Facility', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 16)
        self.set_fill_color(30, 50, 100)  # Deep Industrial Blue
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, f"  {title}", 0, 1, 'L', True)
        self.ln(8)

    def create_table(self, header, data):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(0)
        
        # Column Widths
        w = [90, 50, 50]
        
        # Header
        for i, col in enumerate(header):
            self.cell(w[i], 10, col, 1, 0, 'C', True)
        self.ln()
        
        # Data
        self.set_font('Arial', '', 10)
        for row in data:
            self.cell(w[0], 9, row[0], 1)
            self.cell(w[1], 9, row[1], 1, 0, 'R')
            self.cell(w[2], 9, row[2], 1, 0, 'R')
            self.ln()

# --- Execution ---
pdf = TITAN_DataRoom_Architect()
pdf.add_page()

# 1. Executive Summary Section
pdf.chapter_title("EXECUTIVE SUMMARY - SMART FACTORY")
pdf.set_font("Arial", '', 11)
pdf.set_text_color(0)
summary_text = (
    "This document outlines the strategic expansion of TITAN GRID in Tuzi, Montenegro. "
    "The facility is designed to meet EU Tier-1 industrial standards for transformer tank production, "
    "integrating automated welding and smart logistics."
)
pdf.multi_cell(0, 7, summary_text)
pdf.ln(10)

# 2. Financial Overview (CAPEX Table)
pdf.chapter_title("FINANCIAL INDICATORS (CAPEX)")
header = ['Expenditure Item', 'Allocation (€)', 'EU Status']
data = [
    ['Industrial Facility - Tuzi', '2,500,000', 'Confirmed'],
    ['Automated Welding Robotics', '1,200,000', 'In Tender'],
    ['Energy Efficiency Systems (ESG)', '450,000', 'Planned'],
]
pdf.create_table(header, data)

# Save the File
pdf.output("TITAN_EU_Document.pdf")
print("Data Room Document Generated Successfully.")