import pandas as pd
import numpy as np
import time

INPUT = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL\OUTPUT\LIVE_DATASET.xlsx"

TARGET_DSCR = 1.30
TARGET_MARGIN = 0.25

def autonomous_decision(df):

    decisions = []

    dscr = df["DSCR"].min()
    margin = (df["Revenue"] - df["OPEX"]).mean() / df["Revenue"].mean()

    # =========================
    # DSCR CONTROL
    # =========================
    if dscr < TARGET_DSCR:
        decisions.append("Increase price 5%")
        df["Revenue"] *= 1.05

    # =========================
    # MARGIN CONTROL
    # =========================
    if margin < TARGET_MARGIN:
        decisions.append("Reduce OPEX 5%")
        df["OPEX"] *= 0.95

    # =========================
    # ENERGY OPTIMIZATION
    # =========================
    if df["OPEX"].pct_change().mean() > 0.1:
        decisions.append("Switch to solar / reduce energy load")

    # =========================
    # RECALCULATE
    # =========================
    df["EBITDA"] = df["Revenue"] - df["OPEX"]
    df["CFADS"] = df["EBITDA"] * 0.91
    df["DSCR"] = df["CFADS"] / df["Debt_Service"]

    return df, decisions


while True:

    try:
        df = pd.read_excel(INPUT, sheet_name="MODEL")

        df_new, decisions = autonomous_decision(df)

        df_new.to_excel(INPUT, sheet_name="MODEL", index=False)

        print("🤖 AI CFO ACTIONS:", decisions)

    except Exception as e:
        print("❌ ERROR:", e)

    time.sleep(60)