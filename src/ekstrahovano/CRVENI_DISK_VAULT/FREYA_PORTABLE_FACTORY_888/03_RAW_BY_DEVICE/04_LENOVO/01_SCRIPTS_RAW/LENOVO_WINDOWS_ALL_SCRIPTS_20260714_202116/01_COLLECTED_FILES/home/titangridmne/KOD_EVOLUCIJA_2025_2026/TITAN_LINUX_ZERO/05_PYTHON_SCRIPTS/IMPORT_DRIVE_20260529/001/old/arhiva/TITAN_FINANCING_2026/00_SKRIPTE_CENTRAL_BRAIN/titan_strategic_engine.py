import pandas as pd
import os

# =========================
# INPUT / OUTPUT
# =========================
INPUT = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL\OUTPUT\EXTRACTION_SMART.xlsx"
OUTPUT = r"C:\Users\Lenovo\Desktop\DATA_ROOM_FINAL\OUTPUT\TITAN_STRATEGIC.xlsx"

df = pd.read_excel(INPUT, sheet_name="RAW_DATA")

# =========================
# STRATEGIC LOGIC
# =========================

def assign_priority(level):
    if level == "CRITICAL":
        return "HIGH"
    elif level == "HIGH":
        return "MEDIUM"
    else:
        return "LOW"

def assign_owner(pillar):
    mapping = {
        "CAPEX": "Finance Director",
        "OPEX": "Operations Manager",
        "FINANCING": "CFO",
        "RISK": "Risk Manager",
        "TAX": "Legal/Tax"
    }
    return mapping.get(pillar, "General Manager")

def assign_phase(pillar):
    mapping = {
        "CAPEX": "Construction",
        "OPEX": "Operations",
        "FINANCING": "Financing",
        "RISK": "All Phases",
        "TAX": "Setup"
    }
    return mapping.get(pillar, "General")

def generate_action(row):
    if row["Pillars"] == "CAPEX":
        return "Validate investment cost and supplier quotes"
    elif row["Pillars"] == "OPEX":
        return "Optimize operational cost structure"
    elif row["Pillars"] == "FINANCING":
        return "Check DSCR and financing structure"
    elif row["Pillars"] == "RISK":
        return "Perform risk mitigation analysis"
    elif row["Pillars"] == "TAX":
        return "Review tax compliance"
    else:
        return "Review data"

# =========================
# APPLY TRANSFORMATION
# =========================

df["Priority"] = df["Level"].apply(assign_priority)
df["Owner"] = df["Pillars"].apply(assign_owner)
df["Project_Phase"] = df["Pillars"].apply(assign_phase)
df["Action"] = df.apply(generate_action, axis=1)

# =========================
# STRATEGIC TABLE
# =========================

strategic = df[[
    "ID",
    "Source",
    "Value",
    "Pillars",
    "Sub",
    "Priority",
    "Owner",
    "Project_Phase",
    "Action",
    "Date"
]]

# =========================
# SUMMARY TABLE
# =========================

summary = strategic.groupby(["Pillars","Priority"]).size().reset_index(name="Count")

# =========================
# EXPORT
# =========================

with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
    strategic.to_excel(writer, sheet_name="STRATEGIC_TABLE", index=False)
    summary.to_excel(writer, sheet_name="SUMMARY", index=False)

print("✅ STRATEGIC DOCUMENT CREATED →", OUTPUT)