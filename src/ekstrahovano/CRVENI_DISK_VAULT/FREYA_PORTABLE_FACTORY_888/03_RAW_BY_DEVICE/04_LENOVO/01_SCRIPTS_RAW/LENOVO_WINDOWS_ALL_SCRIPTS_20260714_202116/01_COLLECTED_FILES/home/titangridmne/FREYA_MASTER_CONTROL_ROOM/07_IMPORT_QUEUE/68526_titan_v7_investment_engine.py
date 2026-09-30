import pandas as pd
import numpy as np

# =========================
# INPUT ASSUMPTIONS
# =========================

YEARS = 15
CAPEX = -20_000_000

REVENUE = 6_000_000
OPEX = 3_000_000
GROWTH = 0.05

TAX = 0.09
WACC = 0.10

DEBT = 10_000_000
INTEREST = 0.06
TENOR = 10
TARGET_DSCR = 1.30

# =========================
# FUNCTIONS
# =========================

def calculate_irr(cashflows):
    return np.irr(cashflows)

def calculate_npv(rate, cashflows):
    return np.npv(rate, cashflows)

# =========================
# MODEL BUILD
# =========================

data = []
cashflows = [CAPEX]
remaining_debt = DEBT

for year in range(1, YEARS+1):

    revenue = REVENUE * (1 + GROWTH) ** year
    opex = OPEX * (1.03 ** year)

    ebitda = revenue - opex
    tax = ebitda * TAX

    cfads = ebitda - tax

    interest_payment = remaining_debt * INTEREST

    debt_service = cfads / TARGET_DSCR
    principal = max(debt_service - interest_payment, 0)

    remaining_debt -= principal
    remaining_debt = max(remaining_debt, 0)

    dscr = cfads / (interest_payment + principal) if (interest_payment + principal) > 0 else 0

    cashflows.append(cfads - (interest_payment + principal))

    data.append({
        "Year": year,
        "Revenue": revenue,
        "OPEX": opex,
        "EBITDA": ebitda,
        "CFADS": cfads,
        "Debt_Service": interest_payment + principal,
        "DSCR": dscr,
        "Remaining_Debt": remaining_debt
    })

df = pd.DataFrame(data)

# =========================
# KPI CALCULATION
# =========================

irr = calculate_irr(cashflows)
npv = calculate_npv(WACC, cashflows)

summary = pd.DataFrame({
    "Metric": ["IRR", "NPV", "Min DSCR", "Avg DSCR"],
    "Value": [irr, npv, df["DSCR"].min(), df["DSCR"].mean()]
})

# =========================
# SCENARIOS
# =========================

scenarios = pd.DataFrame({
    "Scenario": ["Base", "Downside", "Upside"],
    "Revenue Multiplier": [1.0, 0.8, 1.2],
    "OPEX Multiplier": [1.0, 1.15, 0.9]
})

# =========================
# EXPORT
# =========================

OUTPUT = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL\OUTPUT\TITAN_v7_INVESTMENT.xlsx"

with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="MODEL", index=False)
    summary.to_excel(writer, sheet_name="KPI", index=False)
    scenarios.to_excel(writer, sheet_name="SCENARIOS", index=False)

print("✅ TITAN v7 INVESTMENT MODEL READY:", OUTPUT)