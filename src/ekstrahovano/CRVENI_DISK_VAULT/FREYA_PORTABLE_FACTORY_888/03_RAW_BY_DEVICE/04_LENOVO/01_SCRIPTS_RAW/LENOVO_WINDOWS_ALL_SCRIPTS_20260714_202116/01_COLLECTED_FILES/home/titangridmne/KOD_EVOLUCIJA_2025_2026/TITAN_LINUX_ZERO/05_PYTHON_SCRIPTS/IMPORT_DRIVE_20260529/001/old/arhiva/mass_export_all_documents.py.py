import os
import subprocess
from pathlib import Path
import win32com.client as win32

# ====================== KONFIGURACIJA ======================
BASE = Path(r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL")

FOLDERS = {
    "00_ADMIN & CONTROL": BASE / "00_ADMIN & CONTROL",
    "01_EXECUTIVE & INVESTMENT CASE": BASE / "01_EXECUTIVE & INVESTMENT CASE",
    "02_CORPORATE & LEGAL": BASE / "02_CORPORATE & LEGAL",
}

def create_folder(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)

def write_document(file_path: Path, title: str, content_lines: list):
    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Add()
    sel = word.Selection

    # Naslov
    sel.Font.Name = "Arial"
    sel.Font.Size = 24
    sel.Font.Bold = True
    sel.TypeText(title)
    sel.TypeParagraph()

    # Sadržaj
    for line in content_lines:
        sel.Font.Size = 11
        sel.Font.Bold = False
        sel.TypeText(line)
        sel.TypeParagraph()

    doc.SaveAs(str(file_path), FileFormat=16)  # .docx
    doc.Close()
    word.Quit()
    print(f"✅ Kreiran: {file_path.name}")

def open_explorer():
    subprocess.Popen(f'explorer "{BASE}"')
    print("🗂️ Otvoren glavni Data Room folder na desktopu")

# ====================== GLAVNI BUILD ======================
def build_all_documents():
    print("🔨 Krećem masovni export svih dokumenata...\n")

    # Kreiranje foldera
    for name, path in FOLDERS.items():
        create_folder(path)

    # 00_ADMIN & CONTROL
    write_document(
        FOLDERS["00_ADMIN & CONTROL"] / "00.02_DOCUMENT_REGISTER.docx",
        "DOCUMENT REGISTER",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Purpose", "The Document Register ensures full traceability...",
         "2. Core Principles", "Single source of truth..."]
    )

    write_document(
        FOLDERS["00_ADMIN & CONTROL"] / "00.03_VERSION_CONTROL_LOG.docx",
        "VERSION CONTROL LOG",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Purpose", "This document establishes a full audit trail..."]
    )

    write_document(
        FOLDERS["00_ADMIN & CONTROL"] / "00.04_ACCESS_PERMISSIONS_MATRIX.docx",
        "ACCESS & PERMISSIONS MATRIX",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Purpose", "Defines controlled access and data security..."]
    )

    write_document(
        FOLDERS["00_ADMIN & CONTROL"] / "00.05_NDA_TEMPLATE.docx",
        "NON-DISCLOSURE AGREEMENT (NDA)",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Purpose", "This Agreement governs confidentiality..."]
    )

    write_document(
        FOLDERS["00_ADMIN & CONTROL"] / "00.06_COMMUNICATION_LOG.docx",
        "COMMUNICATION LOG (Q&A WITH LENDERS)",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Purpose", "This document tracks all communication..."]
    )

    # 01_EXECUTIVE & INVESTMENT CASE
    write_document(
        FOLDERS["01_EXECUTIVE & INVESTMENT CASE"] / "01.01_EXECUTIVE_SUMMARY.docx",
        "EXECUTIVE SUMMARY",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Positioning", "TITAN GRID is a scalable industrial manufacturing platform..."]
    )

    write_document(
        FOLDERS["01_EXECUTIVE & INVESTMENT CASE"] / "01.02_INVESTMENT_MEMORANDUM.docx",
        "INVESTMENT MEMORANDUM",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Executive Summary", "TITAN GRID is a scalable industrial manufacturing platform..."]
    )

    write_document(
        FOLDERS["01_EXECUTIVE & INVESTMENT CASE"] / "01.03_TEASER.docx",
        "TITAN GRID",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "Investment Snapshot", "Near-shoring manufacturing platform..."]
    )

    write_document(
        FOLDERS["01_EXECUTIVE & INVESTMENT CASE"] / "01.04_STRATEGIC_RATIONALE.docx",
        "STRATEGIC RATIONALE",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Positioning", "TITAN GRID is a structural response..."]
    )

    write_document(
        FOLDERS["01_EXECUTIVE & INVESTMENT CASE"] / "01.05_KEY_METRICS_SHEET.docx",
        "KEY METRICS SHEET",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Headline Metrics", "CAPEX €19.92m, IRR ~32%, DSCR ≥1.35x..."]
    )

    # Bonus – 02.01
    write_document(
        FOLDERS["02_CORPORATE & LEGAL"] / "02.01_COMPANY_REGISTRATION.docx",
        "COMPANY REGISTRATION DOCUMENTS",
        ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "",
         "1. Purpose", "Confirms legal existence..."]
    )

    print("\n🎉 SVI DOKUMENTI SU KREIRANI!")
    open_explorer()

if __name__ == "__main__":
    build_all_documents()