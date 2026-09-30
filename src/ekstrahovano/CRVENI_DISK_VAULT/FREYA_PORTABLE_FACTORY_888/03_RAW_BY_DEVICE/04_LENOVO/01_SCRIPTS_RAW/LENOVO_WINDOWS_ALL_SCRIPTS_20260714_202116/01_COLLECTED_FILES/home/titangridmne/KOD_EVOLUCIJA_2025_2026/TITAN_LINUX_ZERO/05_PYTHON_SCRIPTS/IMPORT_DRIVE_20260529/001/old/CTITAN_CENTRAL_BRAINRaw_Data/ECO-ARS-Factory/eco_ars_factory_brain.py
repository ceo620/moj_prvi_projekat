import streamlit as st
import pandas as pd
import subprocess
from pathlib import Path

st.set_page_config(page_title="ECO + ARS Factory Brain", layout="wide")

# =========================
# HELPERS
# =========================
def safe_download_button(label, file_path, file_name=None):
    path = Path(file_path)
    if path.exists():
        with open(path, "rb") as f:
            st.download_button(
                label=label,
                data=f.read(),
                file_name=file_name or path.name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.caption(f"File not found yet: {path.name}")


def run_python_script(script_name, spinner_text="Processing..."):
    try:
        with st.spinner(spinner_text):
            subprocess.run(["python", script_name], check=True)
        return True, None
    except Exception as e:
        return False, str(e)


# =========================
# HEADER / SIDEBAR
# =========================
lang = st.sidebar.selectbox("🌍 Language / Jezik", ["English", "Türkçe"])

if lang == "English":
    st.title("🧠 ECO + ARS Factory Brain")
    st.caption("3-Factory Ecosystem | ECO • ARS Tank (19M€) • Titan 2 (>1 MVA)")
else:
    st.title("🧠 ECO + ARS Fabrika Mozak")
    st.caption("3-Fabrika Ekosistem | ECO • ARS Tank (19M€) • Titan 2 (>1 MVA)")

st.sidebar.success("✅ 13 PDF-ova + Master Data + IC Memo + Lender v7 + PPTX + Central Brain v6")
st.sidebar.info("Version 1.9 – Excel Viewer added, v6/v7 flow preserved")

# =========================
# FILE PATHS
# =========================
lender_file = "TITAN_Central_Brain_Finance_Master_v7_Lender.xlsx"
v6_file = "TITAN_Central_Brain_Finance_Master_v6.xlsx"

# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "💰 Money Overview",
    "📁 Documents & Data Room",
    "📊 Master Parameters",
    "📄 IC Memo Generator",
    "📈 Lender Finance Master v7",
    "📊 TITAN Central Brain Finance Master v6",
    "📂 Excel Viewer",
])

# =========================
# TAB 1 - MONEY OVERVIEW
# =========================
with tab1:
    st.subheader("💰 Money Overview – TITAN GRID" if lang == "English" else "💰 Pregled Novca – TITAN GRID")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total CAPEX", "43.56 M€")
    with col2:
        st.metric("Equity IRR", "38–43 %")
    with col3:
        st.metric("Breakeven", "2,856 units/year")

    st.markdown("---")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("P90 CAPEX", "51.40 M€")
    with k2:
        st.metric("Gross Margin", "48%")
    with k3:
        st.metric("Min DSCR", "1.95x")
    with k4:
        st.metric("Payback", "3.6 years")

    st.info("This page is the high-level project finance snapshot for TITAN / ARS Metal DOO.")

# =========================
# TAB 2 - DOCUMENTS
# =========================
with tab2:
    st.subheader("📁 Documents & Data Room" if lang == "English" else "📁 Dokumenti & Data Room")
    st.success("✅ Data room section ready")

    st.markdown("### Available / Expected Documents")

    docs_df = pd.DataFrame({
        "Document": [
            "Investment Teaser",
            "IC Memo Draft",
            "Lender Presentation",
            "Financial Model v6",
            "Financial Model v7",
            "Factory Bridge Add-on",
            "PPTX Deck",
            "Market / Industry PDFs",
        ],
        "Status": [
            "Expected",
            "Expected",
            "Expected",
            "Active",
            "Planned",
            "Planned",
            "Expected",
            "Available in data room",
        ],
        "Type": [
            "PDF", "DOCX", "PPTX", "XLSX", "XLSX", "XLSX", "PPTX", "PDF",
        ],
    })

    st.dataframe(docs_df, use_container_width=True)

    st.markdown("### Quick Notes")
    st.write("• Use this page as the control room for uploaded documents and generated outputs.")
    st.write("• Keep Grok core files unchanged; append only new outputs.")
    st.write("• Add live download links here later as files become available.")

# =========================
# TAB 3 - MASTER PARAMETERS
# =========================
with tab3:
    st.subheader("📊 Master Parameters" if lang == "English" else "📊 Master Parametri")
    st.success("✅ Core financial parameters loaded")

    parameters_df = pd.DataFrame({
        "Parameter": [
            "Company",
            "Sponsor",
            "Product",
            "Base CAPEX",
            "P90 CAPEX",
            "Full Capacity",
            "ASP",
            "Gross Margin",
            "Senior Debt",
            "Equity",
            "Grant",
            "Project IRR",
            "Equity IRR",
            "Min DSCR",
            "Covenant DSCR",
            "Simple Payback",
        ],
        "Value": [
            "ARS Metal DOO",
            "Hamza Yavuz",
            "Oil-filled transformer tanks",
            43.56,
            51.40,
            3600,
            6200,
            "48%",
            "62%",
            "13%",
            "25%",
            "26.5%",
            "38%",
            1.95,
            1.35,
            3.6,
        ],
        "Unit": [
            "", "", "",
            "EURm", "EURm", "units/year", "EUR/unit", "%",
            "%", "%", "%", "%", "%", "x", "x", "years",
        ],
    })

    st.dataframe(parameters_df, use_container_width=True)

    st.markdown("### Operating Phasing")
    phasing_df = pd.DataFrame({
        "Factory": ["Factory 1", "Factory 2", "Factory 3"],
        "COD / Ramp Start": [2027, 2028, 2029],
        "Capacity Units/Year": [1200, 1200, 1200],
        "Status": ["Active Base Case", "Planned", "Planned"],
    })
    st.dataframe(phasing_df, use_container_width=True)

# =========================
# TAB 4 - IC MEMO GENERATOR
# =========================
with tab4:
    st.subheader("📄 IC Memo Generator" if lang == "English" else "📄 IC Memo Generator")
    st.success("✅ Ready for IC memo input")

    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name", "TITAN GRID")
        sponsor = st.text_input("Sponsor", "Hamza Yavuz")
        company = st.text_input("Company", "ARS Metal DOO")
    with col2:
        investment = st.number_input("Investment (€m)", value=43.56, step=0.01)
        target_irr = st.text_input("Target Equity IRR", "38%")
        target_dscr = st.text_input("Minimum DSCR", "1.95x")

    thesis = st.text_area(
        "Investment Thesis",
        value="Nearshored manufacturing platform for oil-filled transformer tanks serving EU grid reinforcement demand.",
        height=140,
    )

    risks = st.text_area(
        "Key Risks",
        value="Steel price volatility, ramp-up execution, working capital intensity, grant timing, lender covenants.",
        height=120,
    )

    mitigants = st.text_area(
        "Mitigants",
        value="ADS Turkey industrial base, phased rollout, covenant headroom, blended capital stack, factory-level scaling.",
        height=120,
    )

    if st.button("Generate IC Memo Preview", use_container_width=True):
        st.success("✅ IC Memo preview generated")
        preview_df = pd.DataFrame({
            "Field": [
                "Project Name",
                "Sponsor",
                "Company",
                "Investment (€m)",
                "Target Equity IRR",
                "Minimum DSCR",
                "Investment Thesis",
                "Key Risks",
                "Mitigants",
            ],
            "Value": [
                project_name,
                sponsor,
                company,
                investment,
                target_irr,
                target_dscr,
                thesis,
                risks,
                mitigants,
            ],
        })
        st.dataframe(preview_df, use_container_width=True)

# =========================
# TAB 5 - LENDER v7
# =========================
with tab5:
    st.subheader("📈 Lender Finance Master v7" if lang == "English" else "📈 Lender Finance Master v7")
    st.success("✅ v7 section ready in non-destructive mode")
    st.info("Generate v7 only as a separate workflow. Do not overwrite the validated v6 flow.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Generate v7 Lender Model", use_container_width=True):
            ok, err = run_python_script(
                "titan_central_brain_v7_lender.py",
                "Generating v7 lender workbook...",
            )
            if ok:
                st.success("✅ v7 lender workbook generated")
            else:
                st.error(f"Generation failed: {err}")

    with col2:
        if st.button("🏭 Add Factory Bridge (F1/F2/F3)", use_container_width=True):
            if not Path(lender_file).exists():
                st.warning("Generate v7 model first")
            else:
                ok, err = run_python_script(
                    "titan_factory_bridge_v71.py",
                    "Appending factory bridge sheets...",
                )
                if ok:
                    st.success("✅ Factory sheets added")
                else:
                    st.error(f"Factory bridge append failed: {err}")

    safe_download_button(
        "📥 Download TITAN_Central_Brain_Finance_Master_v7_Lender.xlsx",
        lender_file,
    )

# =========================
# TAB 6 - v6 LIVE FLOW
# =========================
with tab6:
    st.subheader("📊 TITAN Central Brain Finance Master v6" if lang == "English" else "📊 TITAN Central Brain Finance Master v6")
    st.success("✅ ChatGPT-ov najkompletniji Excel exporter je učitan")
    st.info("Jednim klikom generišeš puni, formatirani Excel sa Active_Data, Assumptions, Sources_Uses, DSCR, Sensitivity, Monte Carlo, Dashboard, Audit_Checks i chartovima.")

    if st.button("🚀 Generate TITAN Central Brain Finance Master v6 Excel", type="primary", use_container_width=True):
        ok, err = run_python_script(
            "titan_central_brain_v6.py",
            "Generišem Excel (može potrajati 15-20 sekundi)...",
        )
        if ok:
            st.success("✅ Excel generated!")
        else:
            st.error(f"v6 generation failed: {err}")

    safe_download_button(
        "📥 Download TITAN_Central_Brain_Finance_Master_v6.xlsx",
        v6_file,
    )

# =========================
# TAB 7 - EXCEL VIEWER
# =========================
with tab7:
    st.subheader("📂 Excel Viewer" if lang == "English" else "📂 Excel Görüntüleyici")
    st.success("✅ Live workbook reader is active")

    available_files = []
    if Path(lender_file).exists():
        available_files.append(lender_file)
    if Path(v6_file).exists():
        available_files.append(v6_file)

    if not available_files:
        st.warning("No workbook found. Generate or place the Excel file in the app folder first.")
    else:
        selected_workbook = st.selectbox(
            "Select workbook" if lang == "English" else "Workbook seç",
            available_files,
        )

        try:
            excel_file = pd.ExcelFile(selected_workbook)
            available_sheets = excel_file.sheet_names

            control_col1, control_col2, control_col3 = st.columns([2, 1, 1])

            with control_col1:
                selected_sheet = st.selectbox(
                    "Select sheet to view" if lang == "English" else "Görüntülenecek sheet seç",
                    available_sheets,
                )

            with control_col2:
                row_limit = st.number_input(
                    "Rows to show" if lang == "English" else "Gösterilecek satır",
                    min_value=5,
                    max_value=5000,
                    value=100,
                    step=5,
                )

            with control_col3:
                show_shape = st.checkbox(
                    "Show sheet size" if lang == "English" else "Boyutu göster",
                    value=True,
                )

            df = pd.read_excel(selected_workbook, sheet_name=selected_sheet)

            st.markdown(f"### Preview — {selected_sheet}")

            if show_shape:
                st.caption(f"Rows: {df.shape[0]} | Columns: {df.shape[1]}")

            st.dataframe(df.head(int(row_limit)), use_container_width=True)

            st.markdown("### Quick Workbook Status")

            quick_cols = st.columns(4)
            with quick_cols[0]:
                st.metric("Workbook", Path(selected_workbook).name)

            with quick_cols[1]:
                st.metric("Sheets", len(available_sheets))

            with quick_cols[2]:
                st.metric(
                    "Audit_Checks",
                    "Present" if "Audit_Checks" in available_sheets else "Missing",
                )

            with quick_cols[3]:
                st.metric(
                    "Dashboard",
                    "Present" if "Dashboard" in available_sheets else "Missing",
                )

            if "Audit_Checks" in available_sheets:
                st.markdown("### Audit_Checks Preview")
                audit_df = pd.read_excel(selected_workbook, sheet_name="Audit_Checks")
                st.dataframe(audit_df.head(50), use_container_width=True)

            safe_download_button(
                "📥 Download current workbook" if lang == "English" else "📥 Mevcut workbook'u indir",
                selected_workbook,
            )

        except Exception as e:
            st.error(f"Could not read workbook: {e}")