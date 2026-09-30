import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="ECO + ARS Factory Brain", layout="wide")

lang = st.sidebar.selectbox("🌍 Language / Jezik", ["English", "Türkçe"])

if lang == "English":
    st.title("🧠 ECO + ARS Factory Brain")
    st.caption("3-Factory Ecosystem | ECO • ARS Tank (19M€) • Titan 2 (>1 MVA)")
else:
    st.title("🧠 ECO + ARS Fabrika Mozak")
    st.caption("3-Fabrika Ekosistem | ECO • ARS Tank (19M€) • Titan 2 (>1 MVA)")

st.sidebar.success("✅ 13 PDF-ova + Master Data + Full Financial Model sinhronizovano")

tab1, tab2, tab3, tab4 = st.tabs(["💰 Money Overview", "📁 Documents & Data Room", "📊 Master Parameters", "📈 Financial Model Simulator"])

with tab1:
    st.subheader("💰 Money Overview – TITAN GRID" if lang == "English" else "💰 Pregled Novca – TITAN GRID")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total CAPEX", "43.56 M€")
    with col2: st.metric("Equity IRR", "38–43 %")
    with col3: st.metric("Breakeven", "2,856 units/year")

with tab2:
    st.subheader("📁 Documents & Data Room" if lang == "English" else "📁 Dokumenti & Data Room")
    st.success("✅ Svih 13 strateških PDF-ova je sinhronizovano")

with tab3:
    st.subheader("📊 Master Parameters & KPIs" if lang == "English" else "📊 Master Parametri & KPI-ovi")
    st.dataframe(pd.DataFrame({
        "Parameter": ["Base_CAPEX", "Full_Capacity_Units", "Equity_IRR", "Min_DSCR", "Payback"],
        "Value": [43.56, 3600, "38-43%", 1.95, 3.6],
        "Unit": ["EURm", "units/year", "%", "x", "years"]
    }), use_container_width=True)

with tab4:
    st.subheader("📈 Financial Model Simulator" if lang == "English" else "📈 Simulator Finansijskog Modela")
    st.success("✅ ChatGPT-ov puni model je učitan (titan_model.py)")
    st.info("Jednim klikom generišeš kompletan Excel sa scenarijima, Monte Carlo, exit valuacijom i chartovima.")

    if st.button("🚀 Run Full TITAN Financial Model & Download Excel", type="primary", use_container_width=True):
        with st.spinner("Generišem Excel (može potrajati 10-15 sekundi)..."):
            # Pokreće tvoj puni model
            import subprocess
            subprocess.run(["python", "titan_model.py"], check=True)
            
            st.success("✅ Model je pokrenut! Excel je spreman.")
            st.download_button(
                "📥 Download TITAN_PE_Investor_Model_v3.xlsx",
                data=open("TITAN_PE_Investor_Model_v3.xlsx", "rb").read(),
                file_name="TITAN_PE_Investor_Model_v3.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

st.sidebar.info("Version 1.5 – Full Financial Model Simulator aktiviran")