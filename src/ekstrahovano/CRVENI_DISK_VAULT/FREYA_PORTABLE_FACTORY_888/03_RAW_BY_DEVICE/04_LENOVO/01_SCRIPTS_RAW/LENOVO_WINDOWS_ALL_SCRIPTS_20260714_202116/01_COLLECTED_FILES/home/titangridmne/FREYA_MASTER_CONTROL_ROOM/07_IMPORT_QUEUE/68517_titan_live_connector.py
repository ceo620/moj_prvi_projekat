import pandas as pd
import time
import os

BASE = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL"
SOURCE = os.path.join(BASE, "OUTPUT", "TITAN_v7_INVESTMENT.xlsx")
LIVE = os.path.join(BASE, "OUTPUT", "LIVE_DATASET.xlsx")

print("▶ TITAN LIVE SYSTEM STARTED")

while True:
    try:
        df_model = pd.read_excel(SOURCE, sheet_name="MODEL")
        df_kpi = pd.read_excel(SOURCE, sheet_name="KPI")

        # KPI agregacija
        live_kpi = pd.DataFrame({
            "Metric": ["Revenue", "EBITDA", "DSCR", "Debt"],
            "Value": [
                df_model["Revenue"].sum(),
                df_model["EBITDA"].sum(),
                df_model["DSCR"].min(),
                df_model["Remaining_Debt"].iloc[-1]
            ]
        })

        with pd.ExcelWriter(LIVE, engine="openpyxl") as writer:
            df_model.to_excel(writer, sheet_name="MODEL", index=False)
            live_kpi.to_excel(writer, sheet_name="LIVE_KPI", index=False)

        print("✅ Updated LIVE DATA")

    except Exception as e:
        print("❌ Error:", e)

    time.sleep(30)  # refresh every 30 sec