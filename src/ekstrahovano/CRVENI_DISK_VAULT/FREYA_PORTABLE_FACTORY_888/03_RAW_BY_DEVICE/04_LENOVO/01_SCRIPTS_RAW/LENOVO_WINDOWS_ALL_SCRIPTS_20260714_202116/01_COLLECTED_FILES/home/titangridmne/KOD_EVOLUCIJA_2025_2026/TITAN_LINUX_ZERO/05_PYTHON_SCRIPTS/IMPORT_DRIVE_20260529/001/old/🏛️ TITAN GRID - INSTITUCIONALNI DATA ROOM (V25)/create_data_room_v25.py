import os
import subprocess
from pathlib import Path
import win32com.client as win32
import pandas as pd
import polars as pl
import cudf
import cupy as cp
import numpy as np
from datetime import datetime

np.random.seed(42)

# ====================== GLAVNA PUTANJA ======================
DESKTOP = Path(r"C:\Users\Lenovo\Desktop")
DATA_ROOM = DESKTOP / "🏛️ TITAN GRID - INSTITUCIONALNI DATA ROOM (V25)"

# Folder struktura po EU/EIB standardu
FOLDERS = {
    "00_ADMIN_&_CONTROL": DATA_ROOM / "00_ADMIN & CONTROL",
    "01_EXECUTIVE_&_INVESTMENT_CASE": DATA_ROOM / "01_EXECUTIVE & INVESTMENT CASE",
    "02_CORPORATE_&_LEGAL": DATA_ROOM / "02_CORPORATE & LEGAL",
    "03_TECHNICAL_&_PRODUCTION": DATA_ROOM / "03_TECHNICAL & PRODUCTION",
    "04_FINANCIAL_&_MODEL": DATA_ROOM / "04_FINANCIAL & MODEL",
    "05_RISK_&_ESG": DATA_ROOM / "05_RISK & ESG",
}

def create_folders():
    for folder in FOLDERS.values():
        folder.mkdir(parents=True, exist_ok=True)
    print("📁 Kreirana kompletna institucionalna struktura Data Room-a (V25)")

def write_word(file_path: Path, title: str, lines: list):
    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Add()
    sel = word.Selection

    sel.Font.Name = "Arial"
    sel.Font.Size = 24
    sel.Font.Bold = True
    sel.TypeText(title)
    sel.TypeParagraph()

    for line in lines:
        sel.Font.Size = 11
        sel.Font.Bold = False
        sel.TypeText(line)
        sel.TypeParagraph()

    doc.SaveAs(str(file_path), FileFormat=16)
    doc.Close()
    word.Quit()
    print(f"✅ {file_path.name}")

def build_all_documents():
    create_folders()

    # 00_ADMIN & CONTROL
    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.02_DOCUMENT_REGISTER.docx", 
               "DOCUMENT REGISTER", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "Full traceability and version control."])

    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.03_VERSION_CONTROL_LOG.docx", 
               "VERSION CONTROL LOG", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "Every change is recorded and approved."])

    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.04_ACCESS_PERMISSIONS_MATRIX.docx", 
               "ACCESS & PERMISSIONS MATRIX", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "Controlled access based on necessity."])

    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.05_NDA_TEMPLATE.docx", 
               "NON-DISCLOSURE AGREEMENT (NDA)", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "Mandatory for Data Room access."])

    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.06_COMMUNICATION_LOG.docx", 
               "COMMUNICATION LOG", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "Q&A with lenders and stakeholders."])

    # 01_EXECUTIVE & INVESTMENT CASE
    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.01_EXECUTIVE_SUMMARY.docx", 
               "EXECUTIVE SUMMARY", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "TITAN GRID – Scalable industrial platform."])

    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.02_INVESTMENT_MEMORANDUM.docx", 
               "INVESTMENT MEMORANDUM", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "TITAN GRID 2026–2030"])

    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.03_TEASER.docx", 
               "TITAN GRID TEASER", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "Investment Snapshot"])

    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.04_STRATEGIC_RATIONALE.docx", 
               "STRATEGIC RATIONALE", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "Structural response to EU transformer shortage."])

    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.05_KEY_METRICS_SHEET.docx", 
               "KEY METRICS SHEET", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "CAPEX €19.92m | IRR ~32% | DSCR ≥1.35x"])

    # 02_CORPORATE & LEGAL
    write_word(FOLDERS["02_CORPORATE_&_LEGAL"] / "02.01_COMPANY_REGISTRATION.docx", 
               "COMPANY REGISTRATION DOCUMENTS", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz", "", "ARS Metal Industries DOO – Legal identity."])

    # ====================== EIB DUE DILIGENCE READY ======================
    eib_path = DATA_ROOM / f"EIB_DUE_DILIGENCE_READY_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    with pd.ExcelWriter(eib_path, engine="openpyxl") as writer:
        pd.DataFrame([{"Project": "TITAN GRID", "CAPEX": 19920000, "IRR": 32.0, "DSCR": 1.60, "Payback": 4.8}]).to_excel(writer, "01_Executive", index=False)
        pd.DataFrame([{"Risk": "Steel Volatility", "Score": 20}, {"Risk": "CBAM", "Score": 12}]).to_excel(writer, "02_Risk_Matrix", index=False)
        pd.DataFrame([{"Metric": "Solar Offset", "Value": "1.4 MWp"}, {"Metric": "CBAM Compliant", "Value": "YES"}]).to_excel(writer, "03_ESG", index=False)

    print(f"📄 EIB Due Diligence Ready fajl kreiran.")

    # ====================== OTVARANJE FOLDERA ======================
    subprocess.Popen(f'explorer "{DATA_ROOM}"')
    print(f"\n🎉 INSTITUCIONALNI DATA ROOM (V25) je kreiran i otvoren na desktopu!")
    print(f"Putanja: {DATA_ROOM}")

if __name__ == "__main__":
    build_all_documents()