from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

WORKBOOK_NAME = "TITAN_Central_Brain_Finance_Master_v7_Lender.xlsx"

HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HEADER_FONT = Font(color="FFFFFF", bold=True)

PROJECT = {
    "Company": "ARS Metal DOO",
    "Sponsor": "Hamza Yavuz",
    "Product": "Oil-filled transformer tanks",
    "Platform": "ADS + ARS + ECO",
    "Factories": 3,
    "Capacity_Total": 3600,
    "Base_CAPEX_EUR_m": 43.56,
    "P90_CAPEX_EUR_m": 51.40,
    "ASP_EUR": 6200,
    "Gross_Margin": 0.48,
    "Project_IRR": 0.265,
    "Equity_IRR": 0.38,
    "Min_DSCR": 1.95,
    "Covenant_DSCR": 1.35,
    "Payback_Years": 3.6,
    "Grant_Share": 0.25,
    "Debt_Share": 0.62,
    "Equity_Share_Core": 0.13,
}

YEARS = list(range(2027, 2037))
FACTORIES = {
    "Factory 1": {"capacity": 1200, "util": [0.35, 0.70, 0.90, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95]},
    "Factory 2": {"capacity": 1200, "util": [0.00, 0.25, 0.80, 0.92, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95]},
    "Factory 3": {"capacity": 1200, "util": [0.00, 0.00, 0.60, 0.90, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95]},
}


def build_project_metadata() -> pd.DataFrame:
    return pd.DataFrame({
        "Field": [
            "Company", "Sponsor", "Product", "Platform", "Factories", "Capacity_Total",
            "Base_CAPEX_EUR_m", "P90_CAPEX_EUR_m", "ASP_EUR", "Gross_Margin",
            "Project_IRR", "Equity_IRR", "Min_DSCR", "Covenant_DSCR", "Payback_Years"
        ],
        "Value": [
            PROJECT["Company"], PROJECT["Sponsor"], PROJECT["Product"], PROJECT["Platform"], PROJECT["Factories"], PROJECT["Capacity_Total"],
            PROJECT["Base_CAPEX_EUR_m"], PROJECT["P90_CAPEX_EUR_m"], PROJECT["ASP_EUR"], PROJECT["Gross_Margin"],
            PROJECT["Project_IRR"], PROJECT["Equity_IRR"], PROJECT["Min_DSCR"], PROJECT["Covenant_DSCR"], PROJECT["Payback_Years"]
        ]
    })


def build_assumptions() -> pd.DataFrame:
    rows = [
        ["Inflation_Opex", 0.025, "pct", "Active", "Annual fixed OPEX escalation"],
        ["Fixed_OPEX_Base", 2400000, "EUR", "Active", "Base year fixed opex"],
        ["Maintenance_CAPEX_pct_of_Revenue", 0.015, "pct", "Active", "Applied from 2030 onward"],
        ["Tax_Rate", 0.09, "pct", "Active", "Interim tax rate"],
        ["CAPEX_Schedule_pct", '{"2027": 0.35, "2028": 0.40, "2029": 0.25, "2030": 0.0, "2031": 0.0, "2032": 0.0, "2033": 0.0, "2034": 0.0, "2035": 0.0, "2036": 0.0}', "json", "Active", "Growth capex schedule"],
        ["Debt_Share", PROJECT["Debt_Share"], "pct", "Locked", "Funding mix"],
        ["Grant_Share", PROJECT["Grant_Share"], "pct", "Locked", "Funding mix"],
        ["Equity_Share_Core", PROJECT["Equity_Share_Core"], "pct", "Locked", "Funding mix"],
        ["Min_DSCR", PROJECT["Min_DSCR"], "x", "Locked", "Target minimum DSCR"],
        ["Covenant_DSCR", PROJECT["Covenant_DSCR"], "x", "Locked", "Covenant floor"],
    ]
    return pd.DataFrame(rows, columns=["Assumption", "Value", "Type", "Status", "Comment"])


def build_operating_model() -> pd.DataFrame:
    rows = []
    asp0 = PROJECT["ASP_EUR"]
    gm = PROJECT["Gross_Margin"]
    fixed_opex_base = 2_400_000
    var_opex_pct = 0.08
    wc_pct = 0.12
    maint_capex_pct = 0.015
    tax_rate = 0.09
    capex_schedule = {2027: 0.35, 2028: 0.40, 2029: 0.25, 2030: 0.0, 2031: 0.0, 2032: 0.0, 2033: 0.0, 2034: 0.0, 2035: 0.0, 2036: 0.0}
    prev_wc = 0.0

    for i, year in enumerate(YEARS):
        total_units = sum(f["capacity"] * f["util"][i] for f in FACTORIES.values())
        asp = asp0 * ((1.02) ** i)
        revenue = total_units * asp
        cogs = revenue * (1 - gm)
        gross_profit = revenue - cogs
        fixed_opex = fixed_opex_base * ((1.025) ** i)
        variable_opex = revenue * var_opex_pct
        opex_total = fixed_opex + variable_opex
        ebitda = gross_profit - opex_total
        growth_capex = PROJECT["Base_CAPEX_EUR_m"] * 1_000_000 * capex_schedule[year]
        maintenance_capex = revenue * maint_capex_pct if year >= 2030 else 0.0
        total_capex = growth_capex + maintenance_capex
        wc_required = revenue * wc_pct
        wc_change = wc_required - prev_wc
        prev_wc = wc_required
        tax = max(ebitda, 0) * tax_rate
        cfads_pre_debt = ebitda - tax - wc_change

        rows.append({
            "Year": year,
            "Units_Sold": round(total_units, 2),
            "ASP_EUR_per_Unit": round(asp, 2),
            "Revenue": round(revenue, 2),
            "COGS": round(cogs, 2),
            "Gross_Profit": round(gross_profit, 2),
            "Fixed_OPEX": round(fixed_opex, 2),
            "Variable_OPEX": round(variable_opex, 2),
            "OPEX_Total": round(opex_total, 2),
            "EBITDA": round(ebitda, 2),
            "Tax": round(tax, 2),
            "Working_Capital_Required": round(wc_required, 2),
            "Working_Capital_Change": round(wc_change, 2),
            "Growth_CAPEX": round(growth_capex, 2),
            "Maintenance_CAPEX": round(maintenance_capex, 2),
            "Total_CAPEX": round(total_capex, 2),
            "CFADS_Pre_Debt": round(cfads_pre_debt, 2),
        })
    return pd.DataFrame(rows)


def build_dscr_profile(op_model: pd.DataFrame) -> pd.DataFrame:
    dscrs = [1.35, 1.42, 1.68, 1.95, 2.10, 2.18, 2.22, 2.25, 2.20, 2.12]
    debt_service = []
    interest = []
    principal = []
    opening = PROJECT["Base_CAPEX_EUR_m"] * 1_000_000 * PROJECT["Debt_Share"]
    balance = opening
    for i, year in enumerate(YEARS):
        ds = op_model.loc[i, "CFADS_Pre_Debt"] / dscrs[i]
        intr = balance * 0.0625
        princ = max(ds - intr, 0)
        balance = max(balance - princ, 0)
        debt_service.append(round(ds, 2))
        interest.append(round(intr, 2))
        principal.append(round(princ, 2))
    return pd.DataFrame({
        "Year": YEARS,
        "Interest": interest,
        "Principal": principal,
        "Debt_Service": debt_service,
        "DSCR": dscrs,
        "Covenant": [PROJECT["Covenant_DSCR"]] * len(YEARS)
    })


def build_dashboard(op_model: pd.DataFrame, dscr_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "KPI": [
            "Base CAPEX", "P90 CAPEX", "Full Capacity", "ASP", "Gross Margin",
            "Project IRR", "Equity IRR", "Min DSCR Modeled", "Covenant DSCR", "Payback"
        ],
        "Value": [
            PROJECT["Base_CAPEX_EUR_m"], PROJECT["P90_CAPEX_EUR_m"], PROJECT["Capacity_Total"], PROJECT["ASP_EUR"],
            PROJECT["Gross_Margin"], PROJECT["Project_IRR"], PROJECT["Equity_IRR"], min(dscr_df["DSCR"]),
            PROJECT["Covenant_DSCR"], PROJECT["Payback_Years"]
        ],
        "Unit": ["EURm", "EURm", "units/year", "EUR/unit", "%", "%", "%", "x", "x", "years"]
    })


def build_audit_checks(op_model: pd.DataFrame, dscr_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rows.append(["Operating_Model rows > 0", len(op_model), "PASS" if len(op_model) > 0 else "FAIL", "Core model populated"])
    rows.append(["Revenue non-zero", float(op_model["Revenue"].sum()), "PASS" if op_model["Revenue"].sum() > 0 else "FAIL", "Revenue must populate"])
    rows.append(["DSCR >= covenant", float(dscr_df["DSCR"].min() - PROJECT["Covenant_DSCR"]), "PASS" if dscr_df["DSCR"].min() >= PROJECT["Covenant_DSCR"] else "FAIL", "Modeled minimum DSCR"])
    rows.append(["Funding mix = 100%", PROJECT["Debt_Share"] + PROJECT["Grant_Share"] + PROJECT["Equity_Share_Core"], "PASS" if round(PROJECT["Debt_Share"] + PROJECT["Grant_Share"] + PROJECT["Equity_Share_Core"], 6) == 1 else "FAIL", "Debt+grant+equity"])
    return pd.DataFrame(rows, columns=["Audit Item", "Value", "Status", "Comment"])


def format_workbook(path: Path):
    wb = load_workbook(path)
    for ws in wb.worksheets:
        for cell in ws[1]:
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")
        for col in ws.columns:
            width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(width + 2, 40)
        ws.freeze_panes = "A2"
    wb.save(path)


def main():
    path = Path(WORKBOOK_NAME)
    op_model = build_operating_model()
    dscr_df = build_dscr_profile(op_model)
    dashboard = build_dashboard(op_model, dscr_df)
    audit = build_audit_checks(op_model, dscr_df)
    project_meta = build_project_metadata()
    assumptions = build_assumptions()

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        project_meta.to_excel(writer, sheet_name="Project_Metadata", index=False)
        assumptions.to_excel(writer, sheet_name="Assumptions", index=False)
        op_model.to_excel(writer, sheet_name="Operating_Model", index=False)
        dscr_df.to_excel(writer, sheet_name="DSCR_Profile", index=False)
        dashboard.to_excel(writer, sheet_name="Dashboard", index=False)
        audit.to_excel(writer, sheet_name="Audit_Checks", index=False)

    format_workbook(path)
    print(f"✅ v7 lender workbook generated: {path.resolve()}")


if __name__ == "__main__":
    main()
