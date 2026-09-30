import pandas as pd
import os

BASE = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL"
INPUT = os.path.join(BASE, "OUTPUT", "TITAN_v4_OUTPUT.xlsx")
OUTPUT = os.path.join(BASE, "OUTPUT", "CONTROL_TOWER.xlsx")

df = pd.read_excel(INPUT)

# =========================
# KPI AGGREGATION
# =========================

summary = pd.DataFrame({
    "Metric": [
        "Total Signals",
        "CAPEX Signals",
        "OPEX Signals",
        "FINANCING Signals",
        "RISK Signals",
        "CRITICAL Flags"
    ],
    "Value": [
        len(df),
        len(df[df["Pillars"]=="CAPEX"]),
        len(df[df["Pillars"]=="OPEX"]),
        len(df[df["Pillars"]=="FINANCING"]),
        len(df[df["Pillars"]=="RISK"]),
        len(df[df["Level"]=="CRITICAL"])
    ]
})

# =========================
# DSCR RISK SIMULATION
# =========================

df["DSCR_FLAG"] = df["Sub"].apply(lambda x: "YES" if "DSCR" in str(x).upper() else "NO")

dscr_summary = pd.DataFrame({
    "Metric": ["DSCR Signals"],
    "Value": [len(df[df["DSCR_FLAG"]=="YES"])]
})

# =========================
# PIVOT TABLE
# =========================

pivot = pd.pivot_table(
    df,
    index="Pillars",
    values="ID",
    aggfunc="count"
).reset_index()

pivot.columns = ["Pillar", "Count"]

# =========================
# RISK TABLE
# =========================

risk_table = df[df["Level"]=="CRITICAL"]

# =========================
# EXPORT MULTI-SHEET
# =========================

with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="RAW_DATA", index=False)
    summary.to_excel(writer, sheet_name="SUMMARY", index=False)
    pivot.to_excel(writer, sheet_name="PILLAR_VIEW", index=False)
    risk_table.to_excel(writer, sheet_name="CRITICAL_RISKS", index=False)
    dscr_summary.to_excel(writer, sheet_name="DSCR_MONITOR", index=False)

print("✅ CONTROL TOWER CREATED:", OUTPUT)