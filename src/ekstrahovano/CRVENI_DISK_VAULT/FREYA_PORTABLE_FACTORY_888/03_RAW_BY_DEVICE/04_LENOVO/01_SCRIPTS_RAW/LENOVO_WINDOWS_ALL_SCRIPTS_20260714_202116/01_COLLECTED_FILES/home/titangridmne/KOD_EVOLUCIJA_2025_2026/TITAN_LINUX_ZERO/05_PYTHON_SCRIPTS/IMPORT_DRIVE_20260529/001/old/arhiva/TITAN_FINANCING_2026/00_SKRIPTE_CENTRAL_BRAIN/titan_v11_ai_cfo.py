import pandas as pd
import time
import os

BASE = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL"
INPUT = os.path.join(BASE, "OUTPUT", "LIVE_DATASET.xlsx")
OUTPUT = os.path.join(BASE, "OUTPUT", "AI_CFO_ALERTS.xlsx")

print("▶ AI CFO SYSTEM STARTED")

def analyze(df):

    alerts = []

    min_dscr = df["DSCR"].min()
    avg_ebitda = df["EBITDA"].mean()

    # =========================
    # DSCR CHECK
    # =========================
    if min_dscr < 1.3:
        alerts.append({
            "Type": "CRITICAL",
            "Issue": "DSCR BELOW THRESHOLD",
            "Value": min_dscr,
            "Action": "Increase pricing or reduce debt service"
        })

    # =========================
    # EBITDA CHECK
    # =========================
    if avg_ebitda < 0:
        alerts.append({
            "Type": "CRITICAL",
            "Issue": "NEGATIVE EBITDA",
            "Value": avg_ebitda,
            "Action": "Reduce OPEX immediately"
        })

    # =========================
    # OPEX CHECK
    # =========================
    if df["OPEX"].pct_change().mean() > 0.1:
        alerts.append({
            "Type": "WARNING",
            "Issue": "OPEX GROWTH HIGH",
            "Value": "10%+",
            "Action": "Energy optimization required"
        })

    # =========================
    # DEBT CHECK
    # =========================
    if df["Remaining_Debt"].iloc[-1] > 0:
        alerts.append({
            "Type": "INFO",
            "Issue": "DEBT NOT FULLY REPAID",
            "Value": df["Remaining_Debt"].iloc[-1],
            "Action": "Extend tenor or refinance"
        })

    return pd.DataFrame(alerts)

# =========================
# LIVE LOOP
# =========================

while True:
    try:
        df = pd.read_excel(INPUT, sheet_name="MODEL")

        alerts_df = analyze(df)

        alerts_df.to_excel(OUTPUT, index=False)

        print("✅ AI CFO updated alerts")

    except Exception as e:
        print("❌ Error:", e)

    time.sleep(30)