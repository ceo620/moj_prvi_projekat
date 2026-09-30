import streamlit as st
import pandas as pd
import numpy as np
import subprocess
from pathlib import Path

st.set_page_config(page_title="TITAN Central Brain", layout="wide")

# =========================================================
# HELPERS
# =========================================================
def run_script(script_name: str, spinner_text: str):
    try:
        with st.spinner(spinner_text):
            subprocess.run(["python", script_name], check=True)
        return True, None
    except Exception as e:
        return False, str(e)

def download_file_button(label: str, file_path: str):
    path = Path(file_path)
    if path.exists():
        with open(path, "rb") as f:
            st.download_button(
                label=label,
                data=f.read(),
                file_name=path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.caption(f"File not found yet: {path.name}")

# =========================================================
# LOCKED ACTIVE DATA
# =========================================================
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
    "Exit_Valuation_EUR_m": 120.0,
    "Equity_Platform_EUR_m": 31.0,
    "Grant_Share": 0.25,
    "Debt_Share": 0.62,
    "Equity_Share_Core": 0.13,
    "EU_CAGR": 0.0612,
    "EIB_Grid_Funding_EUR_bn": 11.0,
    "Material_Cost_Share": 0.45,
    "Vertical_Integration_Benefit": 0.12,
    "Industry_4_0": True,
    "OEE_Target": 0.75,
    "Alt_Suppliers_per_Critical": 3,
}

YEARS = list(range(2027, 2037))

FACTORIES = {
    "Factory 1": {"capacity": 1200, "cod": 2027, "util": [0.35, 0.70, 0.90, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95]},
    "Factory 2": {"capacity": 1200, "cod": 2028, "util": [0.00, 0.25, 0.80, 0.92, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95]},
    "Factory 3": {"capacity": 1200, "cod": 2029, "util": [0.00, 0.00, 0.60, 0.90, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95]},
}

# =========================================================
# DERIVED MODEL TABLES
# =========================================================
def build_operating_model():
    rows = []
    asp0 = PROJECT["ASP_EUR"]
    gm = PROJECT["Gross_Margin"]
    fixed_opex_base = 2_400_000
    var_opex_pct = 0.08
    wc_pct = 0.12
    maint_capex_pct = 0.015
    tax_rate = 0.09

    capex_schedule = {
        2027: 0.35,
        2028: 0.40,
        2029: 0.25,
        2030: 0.00,
        2031: 0.00,
        2032: 0.00,
        2033: 0.00,
        2034: 0.00,
        2035: 0.00,
        2036: 0.00,
    }

    prev_wc = 0.0

    for i, year in enumerate(YEARS):
        total_units = 0
        for f in FACTORIES.values():
            total_units += f["capacity"] * f["util"][i]

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

def build_factory_table():
    rows = []
    for i, year in enumerate(YEARS):
        for name, f in FACTORIES.items():
            units = f["capacity"] * f["util"][i]
            rows.append({
                "Year": year,
                "Factory": name,
                "COD": f["cod"],
                "Capacity": f["capacity"],
                "Utilization": f["util"][i],
                "Units": round(units, 2),
            })
    return pd.DataFrame(rows)

def build_dscr_profile():
    return pd.DataFrame({
        "Year": YEARS,
        "DSCR": [1.35, 1.42, 1.68, 1.95, 2.10, 2.18, 2.22, 2.25, 2.20, 2.12],
        "Covenant": [PROJECT["Covenant_DSCR"]] * len(YEARS)
    })

def build_roi_table():
    return pd.DataFrame({
        "Metric": [
            "Total Project CAPEX",
            "Platform Equity",
            "Project IRR",
            "Equity IRR",
            "Payback",
            "MoIC",
            "Exit Valuation"
        ],
        "Value": [
            f'€{PROJECT["Base_CAPEX_EUR_m"]:.2f}M',
            f'€{PROJECT["Equity_Platform_EUR_m"]:.0f}M',
            "26.5%",
            "38%",
            "3.5–4.0 years",
            "3.5x–3.8x",
            f'€{PROJECT["Exit_Valuation_EUR_m"]:.0f}M'
        ]
    })

def build_active_data_table():
    return pd.DataFrame({
        "Category": [
            "Project_Core", "Project_Core", "Project_Core", "Financial", "Financial", "Financial",
            "Market", "Market", "Operations", "Operations", "Supply_Chain", "Supply_Chain"
        ],
        "Parameter": [
            "Company", "Sponsor", "Product",
            "Base_CAPEX_EUR_m", "P90_CAPEX_EUR_m", "Gross_Margin",
            "EU_CAGR", "EIB_Grid_Funding_EUR_bn",
            "Capacity_Total", "OEE_Target",
            "Material_Cost_Share", "Alt_Suppliers_per_Critical"
        ],
        "Value": [
            PROJECT["Company"],
            PROJECT["Sponsor"],
            PROJECT["Product"],
            PROJECT["Base_CAPEX_EUR_m"],
            PROJECT["P90_CAPEX_EUR_m"],
            PROJECT["Gross_Margin"],
            PROJECT["EU_CAGR"],
            PROJECT["EIB_Grid_Funding_EUR_bn"],
            PROJECT["Capacity_Total"],
            PROJECT["OEE_Target"],
            PROJECT["Material_Cost_Share"],
            PROJECT["Alt_Suppliers_per_Critical"],
        ],
        "Status": ["ACTIVE"] * 12,
        "Source_Document": [
            "Central Brain", "Central Brain", "Central Brain",
            "Central Brain", "Central Brain", "Central Brain",
            "Market Pack", "Market Pack", "Operating Model", "Lean Target",
            "COGS Model", "Procurement Plan"
        ]
    })

def build_risk_table():
    return pd.DataFrame({
        "Risk": [
            "Steel price volatility",
            "Ramp-up execution",
            "Working capital pressure",
            "Grant timing delay",
            "Supplier concentration",
            "Regulatory / CBAM exposure",
        ],
        "Probability": ["High", "Medium", "Medium", "Medium", "Medium", "Low"],
        "Impact": ["High", "High", "Medium", "Medium", "High", "Medium"],
        "Mitigation": [
            "Contract clauses + sourcing alternatives",
            "Phased rollout + factory controls",
            "Cash flow forecasting + grant blending",
            "Timing buffers",
            "Minimum 3 approved alternatives",
            "Montenegro / EU gateway structure",
        ],
    })

def build_scenario_table():
    return pd.DataFrame({
        "Scenario": ["Base", "Downside", "Covenant", "Upside"],
        "Revenue_Index": [1.00, 0.88, 0.82, 1.10],
        "EBITDA_Margin": [0.22, 0.18, 0.16, 0.25],
        "Min_DSCR": [1.95, 1.60, 1.35, 2.25],
        "Equity_IRR": [0.38, 0.29, 0.22, 0.44]
    })

op_model = build_operating_model()
factory_table = build_factory_table()
dscr_df = build_dscr_profile()
roi_df = build_roi_table()
active_df = build_active_data_table()
risk_df = build_risk_table()
scenario_df = build_scenario_table()

# =========================================================
# HEADER
# =========================================================
st.title("🧠 TITAN Central Brain")
st.caption("Lender-grade industrial dashboard | ADS + ARS + ECO platform")

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💰 Overview",
    "📁 Data Room",
    "📊 Parameters",
    "📄 IC Memo",
    "📈 v7 Model",
    "📊 v6 Model",
    "🚀 Dashboard Pro"
])

# =========================================================
# TAB 1
# =========================================================
with tab1:
    st.subheader("💰 Executive Overview")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Base CAPEX", f'€{PROJECT["Base_CAPEX_EUR_m"]:.2f}M')
    c2.metric("P90 CAPEX", f'€{PROJECT["P90_CAPEX_EUR_m"]:.2f}M')
    c3.metric("Project IRR", "26.5%")
    c4.metric("Equity IRR", "38%")
    c5.metric("Min DSCR", "1.95x")
    c6.metric("Exit", f'€{PROJECT["Exit_Valuation_EUR_m"]:.0f}M')

    st.markdown("---")
    st.dataframe(roi_df, use_container_width=True)

# =========================================================
# TAB 2
# =========================================================
with tab2:
    st.subheader("📁 Data Room")

    docs_df = pd.DataFrame({
        "Document": [
            "Investment Teaser",
            "IC Memo",
            "Financial Model v6",
            "Financial Model v7",
            "Factory Bridge",
            "Lender Deck",
            "Industry PDFs",
        ],
        "Status": [
            "Expected",
            "Draft",
            "Active",
            "Planned",
            "Planned",
            "Expected",
            "Available",
        ],
        "Type": ["PDF", "DOCX", "XLSX", "XLSX", "XLSX", "PPTX", "PDF"]
    })
    st.dataframe(docs_df, use_container_width=True)

# =========================================================
# TAB 3
# =========================================================
with tab3:
    st.subheader("📊 Master Parameters")

    param_df = pd.DataFrame({
        "Parameter": [
            "Company", "Sponsor", "Product", "Factories", "Capacity",
            "ASP", "Gross Margin", "Debt Share", "Grant Share",
            "Project IRR", "Equity IRR", "Min DSCR", "Payback"
        ],
        "Value": [
            PROJECT["Company"],
            PROJECT["Sponsor"],
            PROJECT["Product"],
            PROJECT["Factories"],
            PROJECT["Capacity_Total"],
            PROJECT["ASP_EUR"],
            PROJECT["Gross_Margin"],
            PROJECT["Debt_Share"],
            PROJECT["Grant_Share"],
            PROJECT["Project_IRR"],
            PROJECT["Equity_IRR"],
            PROJECT["Min_DSCR"],
            PROJECT["Payback_Years"],
        ]
    })
    st.dataframe(param_df, use_container_width=True)

# =========================================================
# TAB 4
# =========================================================
with tab4:
    st.subheader("📄 IC Memo Generator")

    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name", "TITAN GRID")
        sponsor = st.text_input("Sponsor", PROJECT["Sponsor"])
        company = st.text_input("Company", PROJECT["Company"])
    with col2:
        investment = st.number_input("Investment (€m)", value=PROJECT["Base_CAPEX_EUR_m"], step=0.01)
        target_irr = st.text_input("Target Equity IRR", "38%")
        target_dscr = st.text_input("Minimum DSCR", "1.95x")

    thesis = st.text_area(
        "Investment Thesis",
        value="Nearshored industrial platform for oil-filled transformer tanks serving EU grid reinforcement and energy infrastructure demand.",
        height=150
    )

    if st.button("Generate IC Memo Preview", use_container_width=True):
        preview = pd.DataFrame({
            "Field": ["Project", "Sponsor", "Company", "Investment (€m)", "Target IRR", "Minimum DSCR", "Thesis"],
            "Value": [project_name, sponsor, company, investment, target_irr, target_dscr, thesis]
        })
        st.success("✅ IC Memo preview generated")
        st.dataframe(preview, use_container_width=True)

# =========================================================
# TAB 5
# =========================================================
with tab5:
    st.subheader("📈 Lender Finance Master v7")
    st.info("Separate workflow. Does not overwrite validated v6.")

    lender_file = "TITAN_Central_Brain_Finance_Master_v7_Lender.xlsx"

    a, b = st.columns(2)

    with a:
        if st.button("🚀 Generate v7 Lender Model", use_container_width=True):
            ok, err = run_script("titan_central_brain_v7_lender.py", "Generating v7 lender workbook...")
            if ok:
                st.success("✅ v7 lender workbook generated")
            else:
                st.error(f"Generation failed: {err}")

    with b:
        if st.button("🏭 Add Factory Bridge", use_container_width=True):
            if not Path(lender_file).exists():
                st.warning("Generate v7 model first")
            else:
                ok, err = run_script("titan_factory_bridge_v71.py", "Appending factory bridge sheets...")
                if ok:
                    st.success("✅ Factory sheets added")
                else:
                    st.error(f"Factory bridge append failed: {err}")

    download_file_button("📥 Download v7 Lender Workbook", lender_file)

# =========================================================
# TAB 6
# =========================================================
with tab6:
    st.subheader("📊 TITAN Central Brain Finance Master v6")

    v6_file = "TITAN_Central_Brain_Finance_Master_v6.xlsx"

    if st.button("🚀 Generate v6 Model", use_container_width=True):
        ok, err = run_script("titan_central_brain_v6.py", "Generating v6 workbook...")
        if ok:
            st.success("✅ v6 workbook generated")
        else:
            st.error(f"v6 generation failed: {err}")

    download_file_button("📥 Download v6 Workbook", v6_file)

# =========================================================
# TAB 7
# =========================================================
with tab7:
    st.subheader("🚀 Dashboard Pro Level")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Payback", "3.5–4.0y")
    k2.metric("MoIC", "3.5x–3.8x")
    k3.metric("Exit", "€110M–€130M")
    k4.metric("Grant Share", "25%")
    k5.metric("Debt Share", "62%")

    st.markdown("---")

    left, right = st.columns(2)

    with left:
        st.markdown("### CAPEX / Value Creation Bridge")
        valuation_df = pd.DataFrame({
            "Stage": ["Base CAPEX", "P90 CAPEX", "Year 5 Value", "Year 10 Exit"],
            "EUR_m": [43.56, 51.40, 72.0, 120.0]
        }).set_index("Stage")
        st.bar_chart(valuation_df)

    with right:
        st.markdown("### DSCR Profile")
        st.line_chart(dscr_df.set_index("Year"))

    st.markdown("---")

    st.markdown("### Operating Model")
    st.dataframe(op_model, use_container_width=True)

    st.markdown("### Factory Ramp")
    f_left, f_right = st.columns([1.2, 1])

    with f_left:
        summary_factory = factory_table.groupby(["Factory", "COD"], as_index=False).agg({
            "Capacity": "max"
        })
        st.dataframe(summary_factory, use_container_width=True)

    with f_right:
        util_pivot = factory_table.pivot(index="Year", columns="Factory", values="Utilization")
        st.line_chart(util_pivot)

    st.markdown("---")

    st.markdown("### Active Data")
    st.dataframe(active_df, use_container_width=True)

    st.markdown("### CFO Capital Deployment & ROI")
    phase_df = pd.DataFrame({
        "Phase": [
            "Phase 1: Brownfield Entry",
            "Phase 2: High-Velocity Scaling",
            "Phase 3: Margin Expansion",
            "Phase 4: Full Optimization"
        ],
        "Timeline": ["M1-6", "Y1-2", "Y3-4", "Y5-10"],
        "Capital Focus": [
            "ECO acquisition + integration",
            "Factory 1 activation",
            "HV production + laboratory",
            "Full capacity + IoT / Smart Grid"
        ],
        "Cash Flow Impact": [
            "Day-1 revenue",
            "Fast liquidity cycle",
            "High-margin contracts",
            "Stable FCF and dividend profile"
        ]
    })
    st.dataframe(phase_df, use_container_width=True)

    st.markdown("### Scenario Dashboard")
    scen = scenario_df.set_index("Scenario")
    s1, s2 = st.columns(2)
    with s1:
        st.bar_chart(scen[["Min_DSCR"]])
    with s2:
        st.bar_chart(scen[["Equity_IRR"]])

    st.markdown("### Risk Control Panel")
    st.dataframe(risk_df, use_container_width=True)

    st.markdown("### Executive Summary")
    st.info(
        "TITAN is structured as a lender-grade industrial platform with phased capital deployment, "
        "protected downside and strong strategic upside. The model combines brownfield cash flow, "
        "factory-scale expansion, EU-adjacent manufacturing advantage and grant-enhanced returns."
    )