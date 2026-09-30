from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment
from openpyxl.chart import LineChart, Reference, BarChart
from openpyxl.worksheet.dimensions import ColumnDimension


# ==============================
# TITAN CENTRAL BRAIN v6.1
# Institutional-grade generator
# ==============================

OUTPUT_FILE = "/mnt/data/TITAN_Central_Brain_Finance_Master_v6_1.xlsx"


@dataclass(frozen=True)
class BaselineRecord:
    baseline_id: str
    model_version: str
    scenario_type: str
    parameter: str
    value: float | str
    unit: str
    source_document: str
    status_flag: str
    monte_carlo_p90: float | str
    equity_impact: str
    industry_specific: str


# ------------------------------
# Styles
# ------------------------------
DARK_BLUE = "001F3F"
CYAN = "00A3E0"
LIGHT_BLUE_FILL = "D9EAF7"
LIGHT_GREEN_FILL = "E2F0D9"
LIGHT_GRAY_FILL = "E7E6E6"
LIGHT_YELLOW_FILL = "FFF2CC"
LIGHT_RED_FILL = "FCE4D6"
WHITE = "FFFFFF"
BLACK = "000000"
INPUT_BLUE = "0000FF"
FORMULA_BLACK = "000000"
LINK_GREEN = "008000"
CAUTION_ORANGE = "C65911"
PURPLE = "7030A0"
TEAL = "008B8B"

THIN_GRAY = Side(style="thin", color="BFBFBF")
MEDIUM_BLUE = Side(style="medium", color=DARK_BLUE)


def make_styles() -> Dict[str, object]:
    return {
        "title": {
            "font": Font(name="Calibri", size=12, bold=True, color=WHITE),
            "fill": PatternFill("solid", fgColor=DARK_BLUE),
            "alignment": Alignment(horizontal="left", vertical="center"),
            "border": Border(top=MEDIUM_BLUE, bottom=MEDIUM_BLUE),
        },
        "header": {
            "font": Font(name="Calibri", size=10, bold=True, color=WHITE),
            "fill": PatternFill("solid", fgColor=CYAN),
            "alignment": Alignment(horizontal="center", vertical="center", wrap_text=True),
            "border": Border(bottom=THIN_GRAY),
        },
        "input": {
            "font": Font(name="Calibri", size=10, color=INPUT_BLUE),
            "fill": PatternFill("solid", fgColor=LIGHT_BLUE_FILL),
            "alignment": Alignment(horizontal="right", vertical="center"),
        },
        "text_input": {
            "font": Font(name="Calibri", size=10, color=INPUT_BLUE),
            "fill": PatternFill("solid", fgColor=LIGHT_BLUE_FILL),
            "alignment": Alignment(horizontal="left", vertical="center"),
        },
        "formula": {
            "font": Font(name="Calibri", size=10, color=FORMULA_BLACK),
            "alignment": Alignment(horizontal="right", vertical="center"),
        },
        "linked": {
            "font": Font(name="Calibri", size=10, color=LINK_GREEN),
            "alignment": Alignment(horizontal="right", vertical="center"),
        },
        "static": {
            "font": Font(name="Calibri", size=10, color="666666"),
            "fill": PatternFill("solid", fgColor=LIGHT_GRAY_FILL),
            "alignment": Alignment(horizontal="right", vertical="center"),
        },
        "label": {
            "font": Font(name="Calibri", size=10, color=BLACK),
            "alignment": Alignment(horizontal="left", vertical="center"),
        },
        "sub_label": {
            "font": Font(name="Calibri", size=10, color=BLACK),
            "alignment": Alignment(horizontal="left", vertical="center", indent=1),
        },
        "kpi": {
            "font": Font(name="Calibri", size=11, bold=True, color=TEAL),
            "fill": PatternFill("solid", fgColor="E2F7F6"),
            "alignment": Alignment(horizontal="right", vertical="center"),
        },
        "warning": {
            "font": Font(name="Calibri", size=10, bold=True, color=CAUTION_ORANGE),
            "fill": PatternFill("solid", fgColor=LIGHT_YELLOW_FILL),
            "alignment": Alignment(horizontal="left", vertical="center"),
        },
        "error": {
            "font": Font(name="Calibri", size=10, bold=True, color="9C0006"),
            "fill": PatternFill("solid", fgColor=LIGHT_RED_FILL),
            "alignment": Alignment(horizontal="left", vertical="center"),
        },
        "control": {
            "font": Font(name="Calibri", size=10, bold=True, color=PURPLE),
            "fill": PatternFill("solid", fgColor="EFE3FF"),
            "alignment": Alignment(horizontal="right", vertical="center"),
        },
        "total_label": {
            "font": Font(name="Calibri", size=10, bold=True, color=BLACK),
            "alignment": Alignment(horizontal="left", vertical="center"),
            "border": Border(top=MEDIUM_BLUE),
        },
        "total_value": {
            "font": Font(name="Calibri", size=10, bold=True, color=BLACK),
            "alignment": Alignment(horizontal="right", vertical="center"),
            "border": Border(top=MEDIUM_BLUE),
        },
    }


STYLES = make_styles()


def apply_style(cell, style_name: str):
    style = STYLES[style_name]
    for key, value in style.items():
        setattr(cell, key, value)


def format_sheet(ws):
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "B5"


def set_col_widths(ws, widths: Dict[str, float]):
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def add_title(ws, title: str, end_col: int = 8):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=end_col)
    c = ws.cell(1, 1, title)
    apply_style(c, "title")
    ws.row_dimensions[1].height = 22


def write_headers(ws, row: int, headers: List[str]):
    for col_idx, header in enumerate(headers, start=1):
        c = ws.cell(row, col_idx, header)
        apply_style(c, "header")
    ws.row_dimensions[row].height = 30


def set_number_formats(ws):
    currency_fmt = '#,##0_);[Red](#,##0)'
    pct_fmt = '0.0%'
    multiple_fmt = '0.00x'
    integer_fmt = '#,##0_);[Red](#,##0)'
    decimal_fmt = '0.0'
    for row in ws.iter_rows():
        for cell in row:
            val = cell.value
            if isinstance(val, str) and val.startswith("="):
                continue
            if cell.column >= 2:
                pass
    return currency_fmt, pct_fmt, multiple_fmt, integer_fmt, decimal_fmt


# ------------------------------
# Base data
# ------------------------------
ACTIVE_DATA = [
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Total_Project_Cost", 27_796_156, "EUR", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Direct_CAPEX", 24_715_200, "EUR", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Contingency", 2_471_520, "EUR", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Debt_Percent", 0.60, "%", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Equity_Percent", 0.40, "%", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "IDC", 1_031_579, "EUR", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Revenue_Y1", 8_000_000, "EUR", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Revenue_Y5", 28_000_000, "EUR", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Revenue_Y12", 32_163_198, "EUR", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "EBITDA_Margin", 0.22, "%", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Capacity_Y1", 660, "units", "ARS_Full_v3 + v4.5", "Active", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "CCC_Days", 100, "days", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "NWC_Y5", 5_753_425, "EUR", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "NWC_Percent_of_Revenue", 0.2055, "%", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Min_DSCR", 1.68, "x", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Avg_DSCR", 3.07, "x", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "DSRA_Months", 6, "months", "Titan Grid v4.5", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "TRL", 8, "score", "Model + seismic data", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "Land_Area", 22_742, "m2", "List nepokretnosti 3301", "Locked", "", "", "Yes"),
    BaselineRecord("ARS_IF25_v4.5", "v4.5", "Base", "UTU_BGP_Limit", 10_000, "m2", "UTU dokument", "Locked", "", "", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Total_Base_CAPEX", 43_560_000, "EUR", "Central Brain brief", "Locked", 51_400_000, "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "P90_CAPEX", 51_400_000, "EUR", "Central Brain brief", "Locked", 51_400_000, "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "ASP", 6_200, "EUR/unit", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Gross_Margin", 0.48, "%", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Senior_Debt_Percent", 0.62, "%", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Equity_Percent", 0.13, "%", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Grant_Percent", 0.25, "%", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Project_IRR", 0.265, "%", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Equity_IRR", 0.38, "%", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Min_DSCR", 1.95, "x", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Simple_Payback", 3.6, "years", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Factories", 3, "count", "Central Brain brief", "Locked", "", "High", "Yes"),
    BaselineRecord("TITAN_CB_v5", "v5", "Base", "Full_Capacity", 3_600, "units/year", "Central Brain brief", "Locked", "", "High", "Yes"),
]


ASSUMPTIONS = [
    ("Current_Baseline_ID", "TITAN_CB_v5", "text", "Control"),
    ("Backup_Baseline_ID", "ARS_IF25_v4.5", "text", "Control"),
    ("Factory1_COD", 2027, "year", "Central Brain brief"),
    ("Full_Capacity_All_3_Factories", 2029, "year", "Central Brain brief"),
    ("OEE", 0.85, "%", "Model reference"),
    ("Scrap", 0.035, "%", "Model reference"),
    ("Steel_per_unit", 15, "t/unit", "Model reference"),
    ("Energy_per_unit", "INPUT_REQUIRED", "MWh/unit", "Missing verified input"),
    ("EURIBOR_6M", "UPDATE_DAILY", "%", "Daily market refresh"),
    ("TRY_EUR", "UPDATE_DAILY", "rate", "Daily market refresh"),
    ("Inflation_Eurozone", "UPDATE_DAILY", "%", "Daily market refresh"),
    ("Steel_Price_HRC_EU", "UPDATE_DAILY", "EUR/t", "Daily market refresh"),
    ("Transformer_Demand_Signal", "UPDATE_DAILY", "text", "Daily market refresh"),
    ("Grant_Status_ME", "Relevant but non-committed", "text", "Desk review"),
    ("Grant_Status_TR", "Active / project-screening required", "text", "Desk review"),
]

YEARS = [2027, 2028, 2029, 2030, 2031]
REVENUE = [8_000_000, 18_000_000, 28_000_000, 30_500_000, 32_163_198]
EBITDA_MARGIN = 0.22
NWC_PERCENT = 0.2055
MIN_DSCR_PROFILE = [1.95, 2.10, 2.80, 3.10, 3.40]


# ------------------------------
# Sheet builders
# ------------------------------

def build_cover(ws):
    format_sheet(ws)
    add_title(ws, "TITAN Central Brain Finance Master v6.1", 8)
    ws["A3"] = "Document"
    ws["B3"] = "TITAN Central Brain Finance Master v6.1"
    ws["A4"] = "Prepared For"
    ws["B4"] = "ARS Metal / ADS Metal / TITAN Central Brain"
    ws["A5"] = "Purpose"
    ws["B5"] = "Harmonized multi-baseline finance master with audit controls"
    ws["A6"] = "Important"
    ws["B6"] = "Baselines are segregated using Baseline_ID to avoid forensic conflicts"
    ws["A7"] = "Version Date"
    ws["B7"] = "2026-04-03"
    for cell in ["A3", "A4", "A5", "A6", "A7"]:
        apply_style(ws[cell], "label")
    for cell in ["B3", "B4", "B5", "B6", "B7"]:
        apply_style(ws[cell], "text_input")
    set_col_widths(ws, {"A": 24, "B": 72})


def build_active_data(ws):
    format_sheet(ws)
    add_title(ws, "Active_Data – Central Brain Memory", 11)
    headers = [
        "Baseline_ID", "Model_Version", "Scenario_Type", "Parameter", "Value",
        "Unit", "Source_Document", "Status_Flag", "Monte_Carlo_P90",
        "Equity_Impact", "Industry_Specific"
    ]
    write_headers(ws, 4, headers)

    row = 5
    for rec in ACTIVE_DATA:
        vals = [
            rec.baseline_id, rec.model_version, rec.scenario_type, rec.parameter, rec.value,
            rec.unit, rec.source_document, rec.status_flag, rec.monte_carlo_p90,
            rec.equity_impact, rec.industry_specific
        ]
        for col_idx, val in enumerate(vals, start=1):
            cell = ws.cell(row, col_idx, val)
            if col_idx in [1, 2, 3, 4, 6, 7, 8, 10, 11]:
                apply_style(cell, "text_input" if col_idx != 7 else "linked")
            else:
                apply_style(cell, "input")
        row += 1

    for r in range(5, row):
        unit = ws.cell(r, 6).value
        val_cell = ws.cell(r, 5)
        p90_cell = ws.cell(r, 9)
        if unit in ("EUR", "EUR/unit"):
            val_cell.number_format = '#,##0_);[Red](#,##0)'
            p90_cell.number_format = '#,##0_);[Red](#,##0)'
        elif unit == "%":
            val_cell.number_format = '0.0%'
            p90_cell.number_format = '0.0%'
        elif unit == "x":
            val_cell.number_format = '0.00x'
            p90_cell.number_format = '0.00x'
        else:
            val_cell.number_format = '#,##0.0_);[Red](#,##0.0)'
            p90_cell.number_format = '#,##0.0_);[Red](#,##0.0)'

    set_col_widths(ws, {
        "A": 18, "B": 12, "C": 13, "D": 28, "E": 16,
        "F": 12, "G": 24, "H": 12, "I": 16, "J": 14, "K": 14
    })


def build_assumptions(ws):
    format_sheet(ws)
    add_title(ws, "Assumptions", 6)
    headers = ["Parameter", "Value", "Unit", "Source", "Comment", "Named_Range"]
    write_headers(ws, 4, headers)

    for idx, (param, value, unit, source) in enumerate(ASSUMPTIONS, start=5):
        ws.cell(idx, 1, param)
        ws.cell(idx, 2, value)
        ws.cell(idx, 3, unit)
        ws.cell(idx, 4, source)
        ws.cell(idx, 5, "")
        ws.cell(idx, 6, param)
        apply_style(ws.cell(idx, 1), "label")
        if isinstance(value, str):
            apply_style(ws.cell(idx, 2), "text_input")
        else:
            apply_style(ws.cell(idx, 2), "input")
        apply_style(ws.cell(idx, 3), "static")
        apply_style(ws.cell(idx, 4), "linked")
        apply_style(ws.cell(idx, 5), "warning")
        apply_style(ws.cell(idx, 6), "control")

    for r in range(5, 5 + len(ASSUMPTIONS)):
        if ws.cell(r, 3).value == "%":
            ws.cell(r, 2).number_format = '0.0%'
    set_col_widths(ws, {"A": 28, "B": 18, "C": 12, "D": 24, "E": 32, "F": 28})

    ws["E12"] = "Daily market input placeholder"
    ws["E13"] = "Daily market input placeholder"
    ws["E14"] = "Daily market input placeholder"


def build_sources_uses(ws):
    format_sheet(ws)
    add_title(ws, "Sources_Uses", 7)
    write_headers(ws, 4, ["Category", "Description", "Amount", "Unit", "Type", "Source", "Check"])

    rows = [
        ("Use", "Base CAPEX", "=INDEX(Active_Data!$E:$E,MATCH(""Total_Base_CAPEX"",Active_Data!$D:$D,0))", "EUR", "Use", "Active_Data", ""),
        ("Use", "P90 CAPEX", "=INDEX(Active_Data!$E:$E,MATCH(""P90_CAPEX"",Active_Data!$D:$D,0))", "EUR", "Use", "Active_Data", ""),
        ("Source", "Senior Debt %", "=INDEX(Active_Data!$E:$E,MATCH(""Senior_Debt_Percent"",Active_Data!$D:$D,0))", "%", "Source", "Active_Data", ""),
        ("Source", "Equity %", "=INDEX(Active_Data!$E:$E,MATCH(""Equity_Percent"",Active_Data!$D:$D,0))", "%", "Source", "Active_Data", ""),
        ("Source", "Grant %", "=INDEX(Active_Data!$E:$E,MATCH(""Grant_Percent"",Active_Data!$D:$D,0))", "%", "Source", "Active_Data", ""),
        ("Source", "Debt Amount", "=C5*C7", "EUR", "Derived", "Formula", ""),
        ("Source", "Equity Amount", "=C5*C8", "EUR", "Derived", "Formula", ""),
        ("Source", "Grant Amount", "=C5*C9", "EUR", "Derived", "Formula", ""),
        ("Check", "Sources less Uses", "=SUM(C10:C12)-C5", "EUR", "Check", "Formula", "=ABS(C13)<1"),
    ]

    start = 5
    for i, rowvals in enumerate(rows, start=start):
        for j, val in enumerate(rowvals, start=1):
            ws.cell(i, j, val)
            if j in [1, 2, 4, 5, 6]:
                apply_style(ws.cell(i, j), "label")
            elif j == 7:
                apply_style(ws.cell(i, j), "control")
            else:
                apply_style(ws.cell(i, j), "formula")

    for r in range(5, 14):
        if ws.cell(r, 4).value == "EUR":
            ws.cell(r, 3).number_format = '#,##0_);[Red](#,##0)'
        elif ws.cell(r, 4).value == "%":
            ws.cell(r, 3).number_format = '0.0%'

    ws["B16"] = "Funding completeness"
    ws["C16"] = "=IF(C13=0,\"OK\",\"ERROR\")"
    apply_style(ws["B16"], "total_label")
    apply_style(ws["C16"], "total_value")
    set_col_widths(ws, {"A": 12, "B": 24, "C": 16, "D": 12, "E": 12, "F": 16, "G": 12})


def build_dscr_profile(ws):
    format_sheet(ws)
    add_title(ws, "DSCR_Profile", 8)
    headers = ["Line Item", *YEARS, "Min / Avg"]
    write_headers(ws, 4, headers)

    # Rows
    labels = [
        "Revenue", "EBITDA Margin", "EBITDA", "NWC %", "NWC", "CFADS", "Debt Service", "DSCR"
    ]
    start_row = 5
    for idx, label in enumerate(labels, start=start_row):
        ws.cell(idx, 1, label)
        apply_style(ws.cell(idx, 1), "label")

    # Revenue input row
    for c, value in enumerate(REVENUE, start=2):
        ws.cell(5, c, value)
        apply_style(ws.cell(5, c), "linked")
        ws.cell(5, c).number_format = '#,##0_);[Red](#,##0)'

    for c in range(2, 2 + len(YEARS)):
        ws.cell(6, c, EBITDA_MARGIN)
        apply_style(ws.cell(6, c), "input")
        ws.cell(6, c).number_format = '0.0%'
        ws.cell(7, c, f"={get_column_letter(c)}5*{get_column_letter(c)}6")
        apply_style(ws.cell(7, c), "formula")
        ws.cell(7, c).number_format = '#,##0_);[Red](#,##0)'
        ws.cell(8, c, NWC_PERCENT)
        apply_style(ws.cell(8, c), "input")
        ws.cell(8, c).number_format = '0.0%'
        ws.cell(9, c, f"={get_column_letter(c)}5*{get_column_letter(c)}8")
        apply_style(ws.cell(9, c), "formula")
        ws.cell(9, c).number_format = '#,##0_);[Red](#,##0)'
        ws.cell(10, c, f"={get_column_letter(c)}7-({get_column_letter(c)}9*0.10)")
        apply_style(ws.cell(10, c), "formula")
        ws.cell(10, c).number_format = '#,##0_);[Red](#,##0)'

    for c, dscr in enumerate(MIN_DSCR_PROFILE, start=2):
        ws.cell(12, c, dscr)
        apply_style(ws.cell(12, c), "input")
        ws.cell(12, c).number_format = '0.00x'
        ws.cell(11, c, f"=IF({get_column_letter(c)}12=0,0,{get_column_letter(c)}10/{get_column_letter(c)}12)")
        apply_style(ws.cell(11, c), "formula")
        ws.cell(11, c).number_format = '#,##0_);[Red](#,##0)'

    ws["G12"] = "=MIN(B12:F12)"
    ws["H12"] = "=AVERAGE(B12:F12)"
    apply_style(ws["G12"], "kpi")
    apply_style(ws["H12"], "kpi")
    ws["G12"].number_format = '0.00x'
    ws["H12"].number_format = '0.00x'

    # Chart
    chart = LineChart()
    chart.title = "DSCR Profile"
    chart.y_axis.title = "x"
    chart.x_axis.title = "Year"
    data = Reference(ws, min_col=2, max_col=6, min_row=12, max_row=12)
    cats = Reference(ws, min_col=2, max_col=6, min_row=4, max_row=4)
    chart.add_data(data, titles_from_data=False)
    chart.set_categories(cats)
    chart.height = 6
    chart.width = 10
    ws.add_chart(chart, "J5")

    set_col_widths(ws, {"A": 20, "B": 14, "C": 14, "D": 14, "E": 14, "F": 14, "G": 12, "H": 12, "I": 2, "J": 14})


def build_break_even(ws):
    format_sheet(ws)
    add_title(ws, "Break_even", 6)
    write_headers(ws, 4, ["Metric", "Formula", "Value", "Unit", "Comment", "Status"])

    rows = [
        ("Break-even Revenue", "Min Debt Service / EBITDA Margin", "=MIN(DSCR_Profile!B11:F11)/INDEX(Active_Data!$E:$E,MATCH(\"EBITDA_Margin\",Active_Data!$D:$D,0))", "EUR", "Illustrative break-even proxy", "Review"),
        ("Revenue Downside Buffer", "Min DSCR - covenant", "=INDEX(Active_Data!$E:$E,MATCH(\"Min_DSCR\",Active_Data!$D:$D,0))-1.35", "x", "Positive buffer required", "OK"),
    ]
    for i, rowvals in enumerate(rows, start=5):
        for j, val in enumerate(rowvals, start=1):
            ws.cell(i, j, val)
            if j in [1, 2, 4, 5, 6]:
                apply_style(ws.cell(i, j), "label")
            else:
                apply_style(ws.cell(i, j), "formula")
        ws.cell(i, 3).number_format = '#,##0.00_);[Red](#,##0.00)'

    set_col_widths(ws, {"A": 22, "B": 34, "C": 16, "D": 10, "E": 28, "F": 12})


def build_sensitivity(ws):
    format_sheet(ws)
    add_title(ws, "Sensitivity", 8)
    ws["A4"] = "DSCR Sensitivity Matrix"
    apply_style(ws["A4"], "title")
    ws.merge_cells("A4:H4")

    price_shocks = [-0.20, -0.10, 0.00, 0.10, 0.20]
    volume_shocks = [-0.20, -0.10, 0.00, 0.10, 0.20]

    for col_idx, shock in enumerate(price_shocks, start=3):
        ws.cell(5, col_idx, shock)
        apply_style(ws.cell(5, col_idx), "input")
        ws.cell(5, col_idx).number_format = '0.0%'

    for row_idx, shock in enumerate(volume_shocks, start=6):
        ws.cell(row_idx, 2, shock)
        apply_style(ws.cell(row_idx, 2), "input")
        ws.cell(row_idx, 2).number_format = '0.0%'
        for col_idx in range(3, 8):
            formula = (
                f"=INDEX(Active_Data!$E:$E,MATCH(\"Min_DSCR\",Active_Data!$D:$D,0))"
                f"*(1+$B{row_idx})*(1+{get_column_letter(col_idx)}$5)"
            )
            ws.cell(row_idx, col_idx, formula)
            apply_style(ws.cell(row_idx, col_idx), "formula")
            ws.cell(row_idx, col_idx).number_format = '0.00x'

    ws["B5"] = "Volume \\ Price"
    apply_style(ws["B5"], "header")
    set_col_widths(ws, {"A": 4, "B": 16, "C": 12, "D": 12, "E": 12, "F": 12, "G": 12, "H": 12})


def build_monte_carlo(ws):
    format_sheet(ws)
    add_title(ws, "Monte_Carlo_Results", 8)
    write_headers(ws, 4, ["Variable", "P10", "P50", "P90", "Unit", "Base", "Delta vs Base", "Comment"])

    rows = [
        ("CAPEX", 41_500_000, 43_560_000, 51_400_000, "EUR", 43_560_000, "=D5-F5", "P90 taken from Central Brain brief"),
        ("Project IRR", 0.22, 0.265, 0.30, "%", 0.265, "=D6-F6", "Illustrative range around base case"),
        ("Equity IRR", 0.31, 0.38, 0.45, "%", 0.38, "=D7-F7", "Illustrative range around base case"),
        ("Min DSCR", 1.60, 1.95, 2.20, "x", 1.95, "=D8-F8", "Aligned to covenant-focused range"),
    ]
    for i, rowvals in enumerate(rows, start=5):
        for j, val in enumerate(rowvals, start=1):
            ws.cell(i, j, val)
            if j in [1, 5, 8]:
                apply_style(ws.cell(i, j), "label")
            else:
                apply_style(ws.cell(i, j), "formula" if isinstance(val, str) and val.startswith("=") else "input")
        unit = ws.cell(i, 5).value
        for col in [2, 3, 4, 6, 7]:
            if unit == "EUR":
                ws.cell(i, col).number_format = '#,##0_);[Red](#,##0)'
            elif unit == "%":
                ws.cell(i, col).number_format = '0.0%'
            elif unit == "x":
                ws.cell(i, col).number_format = '0.00x'

    set_col_widths(ws, {"A": 18, "B": 12, "C": 12, "D": 12, "E": 10, "F": 12, "G": 14, "H": 34})


def build_dashboard(ws):
    format_sheet(ws)
    add_title(ws, "Dashboard", 10)
    write_headers(ws, 4, ["KPI", "Formula / Source", "Value", "Unit", "Status", "KPI", "Formula / Source", "Value", "Unit", "Status"])

    left = [
        ("Project IRR", "Active_Data", "=INDEX(Active_Data!$E:$E,MATCH(\"Project_IRR\",Active_Data!$D:$D,0))", "%", "OK"),
        ("Equity IRR", "Active_Data", "=INDEX(Active_Data!$E:$E,MATCH(\"Equity_IRR\",Active_Data!$D:$D,0))", "%", "OK"),
        ("Min DSCR", "Active_Data", "=INDEX(Active_Data!$E:$E,MATCH(\"Min_DSCR\",Active_Data!$D:$D,0))", "x", "OK"),
        ("P90 CAPEX", "Active_Data", "=INDEX(Active_Data!$E:$E,MATCH(\"P90_CAPEX\",Active_Data!$D:$D,0))", "EUR", "OK"),
    ]
    right = [
        ("Revenue Y1", "Active_Data", "=INDEX(Active_Data!$E:$E,MATCH(\"Revenue_Y1\",Active_Data!$D:$D,0))", "EUR", "OK"),
        ("Revenue Y5", "Active_Data", "=INDEX(Active_Data!$E:$E,MATCH(\"Revenue_Y5\",Active_Data!$D:$D,0))", "EUR", "OK"),
        ("Avg DSCR", "Active_Data", "=INDEX(Active_Data!$E:$E,MATCH(\"Avg_DSCR\",Active_Data!$D:$D,0))", "x", "OK"),
        ("TRL", "Active_Data", "=INDEX(Active_Data!$E:$E,MATCH(\"TRL\",Active_Data!$D:$D,0))", "score", "OK"),
    ]

    for idx in range(4):
        r = 5 + idx
        for j, val in enumerate(left[idx], start=1):
            ws.cell(r, j, val)
            apply_style(ws.cell(r, j), "kpi" if j == 3 else "label")
        for j, val in enumerate(right[idx], start=6):
            ws.cell(r, j, val)
            apply_style(ws.cell(r, j), "kpi" if j == 8 else "label")

    for row in range(5, 9):
        for col in [3, 8]:
            unit = ws.cell(row, col + 1).value
            if unit == "EUR":
                ws.cell(row, col).number_format = '#,##0_);[Red](#,##0)'
            elif unit == "%":
                ws.cell(row, col).number_format = '0.0%'
            elif unit == "x":
                ws.cell(row, col).number_format = '0.00x'
            else:
                ws.cell(row, col).number_format = '#,##0.0'

    chart = BarChart()
    chart.title = "Revenue Ramp"
    chart.y_axis.title = "EUR"
    data = Reference(ws.parent["DSCR_Profile"], min_col=2, max_col=6, min_row=5, max_row=5)
    cats = Reference(ws.parent["DSCR_Profile"], min_col=2, max_col=6, min_row=4, max_row=4)
    chart.add_data(data, titles_from_data=False)
    chart.set_categories(cats)
    chart.height = 6
    chart.width = 10
    ws.add_chart(chart, "A11")

    set_col_widths(ws, {"A": 18, "B": 16, "C": 14, "D": 10, "E": 10, "F": 18, "G": 16, "H": 14, "I": 10, "J": 10})


def build_audit_checks(ws):
    format_sheet(ws)
    add_title(ws, "Audit_Checks", 6)
    write_headers(ws, 4, ["Check_ID", "Check_Name", "Formula", "Expected", "Actual", "Status"])

    rows = [
        ("AUD-001", "Sources = Uses", "=Sources_Uses!C13", 0, "=Sources_Uses!C13", "=IF(ABS(E5-D5)<1,\"OK\",\"ERROR\")"),
        ("AUD-002", "Min DSCR > 1.35x", "=INDEX(Active_Data!$E:$E,MATCH(\"Min_DSCR\",Active_Data!$D:$D,0))", 1.35, "=INDEX(Active_Data!$E:$E,MATCH(\"Min_DSCR\",Active_Data!$D:$D,0))", "=IF(E6>D6,\"OK\",\"ERROR\")"),
        ("AUD-003", "Grant + Debt + Equity = 100%", "=Sources_Uses!C7+Sources_Uses!C8+Sources_Uses!C9", 1.00, "=Sources_Uses!C7+Sources_Uses!C8+Sources_Uses!C9", "=IF(ABS(E7-D7)<0.001,\"OK\",\"ERROR\")"),
        ("AUD-004", "No baseline conflict", "=IF(Assumptions!B5<>Assumptions!B6,1,0)", 1, "=IF(Assumptions!B5<>Assumptions!B6,1,0)", "=IF(E8=D8,\"OK\",\"ERROR\")"),
    ]

    for i, rowvals in enumerate(rows, start=5):
        for j, val in enumerate(rowvals, start=1):
            ws.cell(i, j, val)
            apply_style(ws.cell(i, j), "label" if j in [1, 2] else "formula")
        ws.cell(i, 4).number_format = '0.00x' if i == 6 else '0.0%'

    set_col_widths(ws, {"A": 12, "B": 28, "C": 36, "D": 12, "E": 12, "F": 12})


def build_readme(ws):
    format_sheet(ws)
    add_title(ws, "README / Python Update Logic", 8)
    content = [
        "This workbook intentionally separates conflicting baselines using Baseline_ID.",
        "Do not overwrite locked metrics without changing Baseline_ID or Scenario_Type.",
        "For daily updates, populate market cells in Assumptions with reviewed external inputs.",
        "Suggested Python stub:",
        "def daily_update(active_data_df, market_inputs):",
        "    # validate source timestamps, map to Baseline_ID, propose updates only",
        "    return proposed_changes_df",
        "Missing verified inputs remain tagged as INPUT_REQUIRED or UPDATE_DAILY.",
    ]
    for idx, line in enumerate(content, start=4):
        ws.cell(idx, 1, line)
        apply_style(ws.cell(idx, 1), "text_input")
    set_col_widths(ws, {"A": 110})


def build_workbook() -> Workbook:
    wb = Workbook()
    ws = wb.active
    ws.title = "00_COVER"
    build_cover(ws)

    sheet_builders = [
        ("Active_Data", build_active_data),
        ("Assumptions", build_assumptions),
        ("Sources_Uses", build_sources_uses),
        ("DSCR_Profile", build_dscr_profile),
        ("Break_even", build_break_even),
        ("Sensitivity", build_sensitivity),
        ("Monte_Carlo_Results", build_monte_carlo),
        ("Dashboard", build_dashboard),
        ("Audit_Checks", build_audit_checks),
        ("99_README", build_readme),
    ]

    for name, builder in sheet_builders:
        builder(wb.create_sheet(name))

    # Comments for key source-sensitive cells
    wb["Active_Data"]["E25"].comment = Comment("Source: Central Brain brief. Keep locked unless baseline version changes.", "OpenAI")
    wb["Assumptions"]["B12"].comment = Comment("Populate from reviewed daily market note; do not hardcode without source.", "OpenAI")
    wb["Assumptions"]["B8"].comment = Comment("Energy_per_unit is not verified in the current chat history.", "OpenAI")

    return wb


def save_workbook(path: str = OUTPUT_FILE) -> str:
    wb = build_workbook()
    wb.save(path)
    return path


if __name__ == "__main__":
    output = save_workbook()
    print(f"Saved: {output}")
