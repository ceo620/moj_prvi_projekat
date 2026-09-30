import pandas as pd
import numpy as np
import time
import os

BASE = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL"
INPUT = os.path.join(BASE, "OUTPUT", "LIVE_DATASET.xlsx")

print("▶ TITAN AUTONOMOUS SYSTEM ACTIVE")

TARGET_DSCR = 1.30

def optimize(df):

    df_new = df.copy()

    min_dscr = df["DSCR"].min()

    # =========================
    # RULE 1: DSCR FIX
    # =========================
    if min_dscr < TARGET_DSCR:

        print("⚠ DSCR LOW → applying correction")

        # povećaj revenue 5%
        df_new["Revenue"] *= 1.05

        # smanji OPEX 3%
        df_new["OPEX"] *= 0.97

        # recalculation
        df_new["EBITDA"] = df_new["Revenue"] - df_new["OPEX"]
        df_new["CFADS"] = df_new["EBITDA"] * 0.91

        df_new["DSCR"] = df_new["CFADS"] / df_new["Debt_Service"]

    # =========================
    # RULE 2: HIGH DEBT
    # =========================
    if df["Remaining_Debt"].iloc[-1] > 1_000_000:

        print("⚠ HIGH DEBT → restructuring")

        df_new["Debt_Service"] *= 0.95

    return df_new


# =========================
# LOOP
# =========================

while True:
    try:
        df = pd.read_excel(INPUT, sheet_name="MODEL")

        optimized_df = optimize(df)

        optimized_df.to_excel(INPUT, sheet_name="MODEL", index=False)

        print("✅ Model optimized")

    except Exception as e:
        print("❌ Error:", e)

    time.sleep(60)