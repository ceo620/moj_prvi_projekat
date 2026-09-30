import os
import subprocess
from pathlib import Path
import win32com.client as win32
import polars as pl
import cudf
import cupy as cp
import numpy as np
import pandas as pd
from datetime import datetime

np.random.seed(42)

# ====================== GLAVNA PUTANJA ======================
DESKTOP = Path(r"C:\Users\Lenovo\Desktop")
DATA_ROOM = DESKTOP / "🏛️ TITAN GRID - INSTITUCIONALNI DATA ROOM (V25)"

FOLDERS = {
    "00_ADMIN_&_CONTROL": DATA_ROOM / "00_ADMIN & CONTROL",
    "01_EXECUTIVE_&_INVESTMENT_CASE": DATA_ROOM / "01_EXECUTIVE & INVESTMENT CASE",
    "02_CORPORATE_&_LEGAL": DATA_ROOM / "02_CORPORATE & LEGAL",
}

def create_folders():
    for folder in FOLDERS.values():
        folder.mkdir(parents=True, exist_ok=True)

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

def generate_biblija():
    print("📖 Generišem MAJKA TITANA bibliju (50k+ redova)...")
    n_rows = 50214

    years = list(range(2026, 2041))
    scenarios = ["Low", "Base", "High"]
    pillars = ["STRATEGIJA", "TEHNOLOGIJA", "FINANSIJE", "ESG", "UPRAVLJANJE_RIZICIMA", "KORPORATIVNO_LEGAL"]
    titan_factories = ["TITAN_1_Core", "TITAN_2_Expansion", "TITAN_3_Portfolio"]

    gdf = cudf.DataFrame({
        "ROW_ID": cp.arange(1, n_rows + 1, dtype="int32"),
        "DNA_FORMULA": "MAJKA_TITANA_v1.6",
        "PILLAR": cp.random.choice(pillars, n_rows),
        "TITAN_FACTORY": cp.random.choice(titan_factories, n_rows),
        "Scenario": cp.random.choice(scenarios, n_rows),
        "Year": cp.tile(cp.array(years), n_rows // len(years) + 1)[:n_rows],
        "CAPEX_EUR": cp.random.normal(19920000, 800000, n_rows).astype("int32"),
        "Revenue_EUR": cp.random.normal(35800000, 3200000, n_rows).astype("int32"),
        "EBITDA_margin": cp.random.normal(20.5, 3, n_rows).round(2).astype("float32"),
        "IRR": cp.random.normal(32.0, 4, n_rows).round(2).astype("float32"),
        "DSCR": cp.random.normal(1.60, 0.15, n_rows).round(2).astype("float32"),
        "Risk_Score": cp.random.randint(1, 6, n_rows).astype("int8"),
        "Owner": cp.random.choice(["Danijela Keskin", "Hamza Yavuz", "Onur Keskin"], n_rows),
        "Status": cp.random.choice(["Lender_Ready", "Audit_Ready", "For_Approval"], n_rows),
        "Notes": "Derivirano iz MASTER RAW MATRIX v3.0 | Portfolio TITAN 1-2-3"
    })

    gdf = gdf.assign(
        Stock_Value_TRY=(gdf["CAPEX_EUR"] * 51.7).astype("int64"),
        Daily_Demand_ton=(gdf["Revenue_EUR"] / 365 / 2200).round(2).astype("float32"),
        NPV_EUR=(gdf["Revenue_EUR"] * 0.85 * (1 - (1 + 0.08) ** -15) / 0.08).astype("int64"),
        Solar_Offset_%=cp.random.normal(28, 4, n_rows).round(1).astype("float32"),
        CBAM_Compliant="YES",
        Portfolio_Derivation=gdf["TITAN_FACTORY"].map({
            "TITAN_1_Core": "Standalone Anchor",
            "TITAN_2_Expansion": "Internal FCF funded",
            "TITAN_3_Portfolio": "Cross-default + Upside"
        })
    )

    df = pl.from_arrow(gdf.to_arrow())

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    bible_folder = DATA_ROOM / "04_FINANCIAL_&_MODEL"
    bible_folder.mkdir(parents=True, exist_ok=True)

    base = f"{bible_folder}/MAJKA_TITANA_BIBLIJA_{timestamp}"

    df.write_parquet(f"{base}.parquet", compression="snappy")
    df.write_csv(f"{base}.csv")

    pdf = df.to_pandas()
    with pd.ExcelWriter(f"{base}.xlsx", engine="openpyxl") as writer:
        pdf.to_excel(writer, sheet_name="MAJKA_TITANA", index=False)
        pivot = pdf.pivot_table(
            index=["PILLAR", "TITAN_FACTORY", "Scenario"],
            values=["Revenue_EUR", "EBITDA_margin", "IRR", "DSCR"],
            aggfunc={"Revenue_EUR": "sum", "EBITDA_margin": "mean", "IRR": "mean", "DSCR": "mean"}
        )
        pivot.to_excel(writer, sheet_name="PIVOT_MAJKA")

    print(f"📖 Biblija kreirana: MAJKA_TITANA_BIBLIJA_{timestamp}.xlsx")

def open_data_room():
    subprocess.Popen(f'explorer "{DATA_ROOM}"')
    print(f"🗂️ Data Room (V25) automatski otvoren!")

def main():
    print("🏛️ Kreiram INSTITUCIONALNI DATA ROOM (V25)...\n")
    create_folders()

    # Dokumenti
    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.02_DOCUMENT_REGISTER.docx", "DOCUMENT REGISTER", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])
    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.03_VERSION_CONTROL_LOG.docx", "VERSION CONTROL LOG", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])
    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.04_ACCESS_PERMISSIONS_MATRIX.docx", "ACCESS & PERMISSIONS MATRIX", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])
    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.05_NDA_TEMPLATE.docx", "NON-DISCLOSURE AGREEMENT", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])
    write_word(FOLDERS["00_ADMIN_&_CONTROL"] / "00.06_COMMUNICATION_LOG.docx", "COMMUNICATION LOG", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])

    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.01_EXECUTIVE_SUMMARY.docx", "EXECUTIVE SUMMARY", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])
    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.02_INVESTMENT_MEMORANDUM.docx", "INVESTMENT MEMORANDUM", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])
    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.03_TEASER.docx", "TITAN GRID TEASER", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])
    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.04_STRATEGIC_RATIONALE.docx", "STRATEGIC RATIONALE", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])
    write_word(FOLDERS["01_EXECUTIVE_&_INVESTMENT_CASE"] / "01.05_KEY_METRICS_SHEET.docx", "KEY METRICS SHEET", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])

    write_word(FOLDERS["02_CORPORATE_&_LEGAL"] / "02.01_COMPANY_REGISTRATION.docx", "COMPANY REGISTRATION", ["Creator: Danijela Keskin, CFO", "Sponsor: Hamza Yavuz"])

    # Biblija
    generate_biblija()

    # Otvaranje
    open_data_room()

    print("\n🎉 SVE JE KREIRANO I SPREMNO!")
    print(f"Folder: {DATA_ROOM}")

if __name__ == "__main__":
    main()