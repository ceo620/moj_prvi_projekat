# ================================================
#   MASS GENERATOR – MAJKA TITANA v1.6 (Polars + GPU)
#   + Automatsko otvaranje foldera
#   + EIB Due Diligence Ready fajl (stroga EU praksa)
# ================================================

import polars as pl
import cudf
import cupy as cp
import numpy as np
from datetime import datetime
import os
import time
import argparse
import subprocess
import pandas as pd

np.random.seed(42)

def open_folder(path: str):
    """Automatsko otvaranje foldera u Exploreru"""
    subprocess.Popen(f'explorer "{path}"')
    print(f"🗂️ Folder automatski otvoren: {path}")

def generate_majka_titana_mass(
    n_rows: int = 50214,
    output_folder: str = "MAJKA_TITANA_BIBLIJA_GPU",
    gpu: bool = True
):
    start = time.time()
    print(f"🚀 MASS GENERATOR v1.6 – Krećem sa {n_rows:,} redova (GPU: {gpu})...")

    years = list(range(2026, 2041))
    scenarios = ["Low", "Base", "High"]
    pillars = ["STRATEGIJA", "TEHNOLOGIJA", "FINANSIJE", "ESG", "UPRAVLJANJE_RIZICIMA", "KORPORATIVNO_LEGAL"]
    titan_factories = ["TITAN_1_Core", "TITAN_2_Expansion", "TITAN_3_Portfolio"]

    if gpu:
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
    else:
        df = pl.DataFrame({
            "ROW_ID": np.arange(1, n_rows + 1),
            "DNA_FORMULA": "MAJKA_TITANA_v1.6",
            "PILLAR": np.random.choice(pillars, n_rows),
            "TITAN_FACTORY": np.random.choice(titan_factories, n_rows),
            "Scenario": np.random.choice(scenarios, n_rows),
            "Year": np.tile(years, n_rows // len(years) + 1)[:n_rows],
            "CAPEX_EUR": np.random.normal(19920000, 800000, n_rows).astype("int32"),
            "Revenue_EUR": np.random.normal(35800000, 3200000, n_rows).astype("int32"),
            "EBITDA_margin": np.random.normal(20.5, 3, n_rows).round(2).astype("float32"),
            "IRR": np.random.normal(32.0, 4, n_rows).round(2).astype("float32"),
            "DSCR": np.random.normal(1.60, 0.15, n_rows).round(2).astype("float32"),
            "Risk_Score": np.random.randint(1, 6, n_rows).astype("int8"),
            "Owner": np.random.choice(["Danijela Keskin", "Hamza Yavuz", "Onur Keskin"], n_rows),
            "Status": np.random.choice(["Lender_Ready", "Audit_Ready", "For_Approval"], n_rows),
            "Notes": "Derivirano iz MASTER RAW MATRIX v3.0 | Portfolio TITAN 1-2-3"
        }).with_columns([
            (pl.col("CAPEX_EUR") * 51.7).cast(pl.Int64).alias("Stock_Value_TRY"),
            (pl.col("Revenue_EUR") / 365 / 2200).round(2).cast(pl.Float32).alias("Daily_Demand_ton"),
            (pl.col("Revenue_EUR") * 0.85 * (1 - (1 + 0.08) ** -15) / 0.08).cast(pl.Int64).alias("NPV_EUR"),
            pl.Series("Solar_Offset_%", np.random.normal(28, 4, n_rows).round(1)).cast(pl.Float32),
            pl.lit("YES").alias("CBAM_Compliant"),
            pl.col("TITAN_FACTORY").map_dict({
                "TITAN_1_Core": "Standalone Anchor",
                "TITAN_2_Expansion": "Internal FCF funded",
                "TITAN_3_Portfolio": "Cross-default + Upside"
            }).alias("Portfolio_Derivation")
        ])

    # ====================== SNIMANJE ======================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    os.makedirs(output_folder, exist_ok=True)
    base = f"{output_folder}/MAJKA_TITANA_BIBLIJA_GPU_{timestamp}"

    df.write_parquet(f"{base}.parquet", compression="snappy")
    df.write_csv(f"{base}.csv")

    # Excel + Pivot
    pdf = df.to_pandas()
    with pd.ExcelWriter(f"{base}.xlsx", engine="openpyxl") as writer:
        pdf.to_excel(writer, sheet_name="MAJKA_TITANA", index=False)
        pivot = pdf.pivot_table(
            index=["PILLAR", "TITAN_FACTORY", "Scenario"],
            values=["Revenue_EUR", "EBITDA_margin", "IRR", "DSCR"],
            aggfunc={"Revenue_EUR": "sum", "EBITDA_margin": "mean", "IRR": "mean", "DSCR": "mean"}
        )
        pivot.to_excel(writer, sheet_name="PIVOT_MAJKA")

    # ====================== EIB DUE DILIGENCE READY FAJL ======================
    eib_file = f"{output_folder}/EIB_DUE_DILIGENCE_READY_{timestamp}.xlsx"
    with pd.ExcelWriter(eib_file, engine="openpyxl") as writer:
        # Sheet 1 - Executive Summary
        exec_df = pd.DataFrame([{
            "Project": "TITAN GRID",
            "CAPEX": 19920000,
            "IRR": 32.0,
            "DSCR": 1.60,
            "Payback": 4.8,
            "EBITDA_margin": 20.5
        }])
        exec_df.to_excel(writer, sheet_name="01_Executive_Summary", index=False)

        # Sheet 2 - Key Metrics
        pdf[["CAPEX_EUR", "Revenue_EUR", "EBITDA_margin", "IRR", "DSCR"]].head(10).to_excel(
            writer, sheet_name="02_Key_Metrics", index=False)

        # Sheet 3 - Risk Matrix
        risk_df = pd.DataFrame({
            "Risk": ["Steel Price Volatility", "CBAM", "Construction Delay", "Market Demand"],
            "Probability": [4, 3, 2, 3],
            "Impact": [5, 4, 4, 3],
            "Score": [20, 12, 8, 9]
        })
        risk_df.to_excel(writer, sheet_name="03_Risk_Matrix", index=False)

        # Sheet 4 - ESG
        esg_df = pd.DataFrame([{
            "Solar_Offset": "1.4 MWp",
            "CBAM_Compliant": "YES",
            "EU_Taxonomy": "Section 3.20",
            "Carbon_Footprint": "Low"
        }])
        esg_df.to_excel(writer, sheet_name="04_ESG", index=False)

    print(f"📄 EIB Due Diligence Ready fajl kreiran: EIB_DUE_DILIGENCE_READY_{timestamp}.xlsx")

    # ====================== AUTOMATSKO OTVARANJE ======================
    open_folder(output_folder)

    elapsed = time.time() - start
    print(f"✅ MASS GENERATOR v1.6 – GOTOVO za {elapsed:.2f} sekundi!")
    print(f"   • Redova: {n_rows:,}")
    print(f"   • Parquet + Excel + CSV + EIB Ready fajl kreirani")
    print(f"   • Folder automatski otvoren na desktopu")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=50214, help="Broj redova (default 50k)")
    parser.add_argument("--folder", type=str, default="MAJKA_TITANA_BIBLIJA_GPU", help="Izlazni folder")
    parser.add_argument("--no-gpu", action="store_true", help="Koristi CPU umjesto GPU")
    args = parser.parse_args()

    generate_majka_titana_mass(
        n_rows=args.rows,
        output_folder=args.folder,
        gpu=not args.no_gpu
    )