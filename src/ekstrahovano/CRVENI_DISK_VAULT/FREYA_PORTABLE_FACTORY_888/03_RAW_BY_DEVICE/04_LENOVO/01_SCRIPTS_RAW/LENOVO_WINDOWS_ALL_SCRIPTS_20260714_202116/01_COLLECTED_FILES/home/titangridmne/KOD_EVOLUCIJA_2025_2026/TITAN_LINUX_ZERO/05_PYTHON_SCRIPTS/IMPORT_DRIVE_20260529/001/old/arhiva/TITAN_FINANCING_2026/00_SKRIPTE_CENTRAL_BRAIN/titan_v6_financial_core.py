import pandas as pd
import numpy as np
from datetime import datetime

# =========================
# MODEL PARAMETERS
# =========================

YEARS = 15

REVENUE = 5_000_000
OPEX = 2_500_000
TAX_RATE = 0.09
MAINT_CAPEX = 200_000
WC_CHANGE = 100_000

DEBT = 8_000_000
INTEREST_RATE = 0.06
TENOR = 10

TARGET_DSCR = 1.30

# =========================
# BUILD MODEL
# =========================

data = []

remaining_debt = DEBT

for year in range(1, YEARS + 1):

    revenue = REVENUE * (1.05 ** year)
    opex = OPEX * (1.03 ** year)

    ebitda = revenue - opex

    tax = ebitda * TAX_RATE

    cfads = ebitda - tax - WC_CHANGE - MAINT_CAPEX

    interest = remaining_debt * INTEREST_RATE

    # sculpted debt service
    debt_service = cfads / TARGET_DSCR

    principal = max(debt_service - interest, 0)

    remaining_debt = max(remaining_debt - principal, 0)

    dscr = cfads / (interest + principal) if (interest + principal) > 0 else 0

    data.append({
        "Year": year,
        "Revenue": revenue,
        "OPEX": opex,
        "EBITDA": ebitda,
        "Tax": tax,
        "CFADS": cfads,
        "Interest": interest,
        "Principal": principal,
        "Debt_Service": interest + principal,
        "DSCR": dscr,
        "Remaining_Debt": remaining_debt
    })

df = pd.DataFrame(data)

# =========================
# SUMMARY
# =========================

summary = pd.DataFrame({
    "Metric": [
        "Min DSCR",
        "Avg DSCR",
        "Final Debt",
        "Total CFADS"
    ],
    "Value": [
        df["DSCR"].min(),
        df["DSCR"].mean(),
        remaining_debt,
        df["CFADS"].sum()
    ]
})

# =========================
# EXPORT
# =========================

OUTPUT = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL\OUTPUT\TITAN_v6_MODEL.xlsx"

with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="MODEL", index=False)
    summary.to_excel(writer, sheet_name="SUMMARY", index=False)

print("✅ TITAN v6 MODEL CREATED:", OUTPUT)