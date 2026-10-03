
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.chart import LineChart, BarChart, Reference
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment
from openpyxl.worksheet.page import PageMargins


OUTPUT_ROOT_NAME = "Titan_Grid_v52_Data_Room_Ready"
WORKBOOK_NAME = "Titan_Grid_v52_Credit_Committee_Pack.xlsx"
PDF_NAME = "Titan_Grid_v52_Credit_Committee_Pack.pdf"
EXPORT_WORKBOOK_NAME = "Titan_Grid_v52_PDF_Export_Copy.xlsx"
ZIP_NAME = OUTPUT_ROOT_NAME + ".zip"


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def safe_remove(path: Path):
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def create_styles():
    navy_fill = PatternFill("solid", fgColor="0F243E")
    dark_blue_fill = PatternFill("solid", fgColor="1F4E78")
    light_blue_fill = PatternFill("solid", fgColor="D9EAF7")
    input_fill = PatternFill("solid", fgColor="FFF2CC")
    caution_fill = PatternFill("solid", fgColor="FCE4D6")
    green_fill = PatternFill("solid", fgColor="E2F0D9")
    gray_fill = PatternFill("solid", fgColor="E7E6E6")
    teal_fill = PatternFill("solid", fgColor="DDEBF7")
    red_fill = PatternFill("solid", fgColor="F4CCCC")
    yellow_fill = PatternFill("solid", fgColor="FFF2CC")
    status_green_fill = PatternFill("solid", fgColor="C6E0B4")

    white_bold = Font(color="FFFFFF", bold=True, size=11)
    white_bold_big = Font(color="FFFFFF", bold=True, size=16)
    bold = Font(bold=True)
    body = Font(name="Calibri", size=10, color="000000")
    input_font = Font(name="Calibri", size=10, color="0000FF")
    linked_font = Font(name="Calibri", size=10, color="008000")
    static_font = Font(name="Calibri", size=10, color="666666")
    caution_font = Font(name="Calibri", size=10, color="C55A11")
    title_font = Font(name="Calibri", size=22, bold=True, color="0F243E")

    thin = Side(style="thin", color="D9D9D9")
    medium = Side(style="medium", color="7F7F7F")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    top_border = Border(top=medium)

    return {
        "fills": {
            "navy": navy_fill, "dark_blue": dark_blue_fill, "light_blue": light_blue_fill,
            "input": input_fill, "caution": caution_fill, "green": green_fill,
            "gray": gray_fill, "teal": teal_fill, "red": red_fill,
            "yellow": yellow_fill, "status_green": status_green_fill,
        },
        "fonts": {
            "white_bold": white_bold, "white_bold_big": white_bold_big, "bold": bold,
            "body": body, "input": input_font, "linked": linked_font,
            "static": static_font, "caution": caution_font, "title": title_font,
        },
        "border": border,
        "top_border": top_border,
    }


def apply_number_format(cell, kind):
    formats = {
        "eur": '€#,##0;[Red](€#,##0);-',
        "eur1": '€#,##0.0;[Red](€#,##0.0);-',
        "pct": '0.0%;[Red](0.0%);-',
        "pct2": '0.00%;[Red](0.00%);-',
        "x": '0.00x;[Red](0.00x);-',
        "int": '#,##0;[Red](#,##0);-',
        "dec": '#,##0.0;[Red](#,##0.0);-',
    }
    cell.number_format = formats[kind]


def style_cell(cell, font=None, fill=None, border=None, align=None):
    if font:
        cell.font = font
    if fill:
        cell.fill = fill
    if border:
        cell.border = border
    if align:
        cell.alignment = align


def merge_header(ws, row, start_col, end_col, title, styles):
    ws.merge_cells(start_row=row, start_column=start_col, end_row=row, end_column=end_col)
    c = ws.cell(row=row, column=start_col, value=title)
    style_cell(
        c,
        font=styles["fonts"]["white_bold_big"] if row == 1 else styles["fonts"]["white_bold"],
        fill=styles["fills"]["navy"],
        border=styles["border"],
        align=Alignment(horizontal="left", vertical="center"),
    )
    for col in range(start_col, end_col + 1):
        style_cell(ws.cell(row=row, column=col), fill=styles["fills"]["navy"], border=styles["border"])
    ws.row_dimensions[row].height = 24 if row == 1 else 20


def add_subheader_row(ws, row, labels, styles, start_col=1):
    for i, lab in enumerate(labels, start=start_col):
        cell = ws.cell(row=row, column=i, value=lab)
        style_cell(cell, font=styles["fonts"]["bold"], fill=styles["fills"]["light_blue"],
                   border=styles["border"], align=Alignment(horizontal="center", vertical="center", wrap_text=True))
    ws.row_dimensions[row].height = 22


def set_widths(ws, widths):
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width


def add_comment(cell, text):
    cell.comment = Comment(text, "OpenAI")


def apply_print_setup(ws, area, orientation="landscape"):
    ws.print_area = area
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = orientation
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins = PageMargins(left=0.6, right=0.6, top=0.6, bottom=0.6, header=0.3, footer=0.3)
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A4"
    ws.oddHeader.left.text = "TITAN GRID - Credit Committee Pack"
    ws.oddHeader.center.text = "Version v5.2"
    ws.oddHeader.right.text = "Confidential"
    ws.oddFooter.left.text = "ARS Metal Industries d.o.o."
    ws.oddFooter.center.text = "Page &P of &N"
    ws.oddFooter.right.text = "25.03.2026"


def cover_sheet(wb, styles):
    ws = wb.create_sheet("Cover")
    ws["A2"] = "TITAN GRID"
    ws["A3"] = "Credit Committee Model Pack"
    ws["A2"].font = styles["fonts"]["title"]
    ws["A3"].font = Font(name="Calibri", size=16, bold=True, color="1F4E78")

    for rng in ["A1:F1", "A5:F5", "A15:F15"]:
        start = ws[rng.split(":")[0]]
        end = ws[rng.split(":")[1]]
        ws.merge_cells(rng)
        c = ws[rng.split(":")[0]]
        c.fill = styles["fills"]["navy"]

    ws["A5"] = "Document Metadata"
    ws["A5"].font = styles["fonts"]["white_bold"]
    ws["A5"].alignment = Alignment(horizontal="left")
    meta = [
        ("Project", "ARS Metal Industries / TITAN GRID"),
        ("Document type", "Credit Committee Pack"),
        ("Version", "v5.2"),
        ("Date", "25.03.2026"),
        ("Classification", "Confidential"),
        ("Prepared for", "EIB / EBRD / Bank / Internal IC"),
        ("Prepared by", "ARS Metal Industries sponsor team"),
        ("Scope", "Integrated bank + grant model with committee print pack"),
    ]
    row = 6
    for k, v in meta:
        ws[f"A{row}"] = k
        ws[f"B{row}"] = v
        ws[f"A{row}"].font = styles["fonts"]["bold"]
        ws[f"A{row}"].fill = styles["fills"]["light_blue"]
        for col in range(1, 7):
            style_cell(ws.cell(row=row, column=col), border=styles["border"])
        row += 1

    ws["A15"] = "Pack Contents"
    ws["A15"].font = styles["fonts"]["white_bold"]
    contents = [
        "1. Executive Summary",
        "2. Recommendation",
        "3. Covenant Pack",
        "4. Scenario Matrix",
        "5. Funding and Uses",
        "6. Key Risks & Mitigants",
        "7. Dashboard",
        "8. Technical Appendix",
    ]
    for i, item in enumerate(contents, start=16):
        ws[f"A{i}"] = item
        ws[f"A{i}"].font = styles["fonts"]["body"]

    set_widths(ws, {1: 24, 2: 42, 3: 14, 4: 14, 5: 14, 6: 14})
    apply_print_setup(ws, "A1:F30", orientation="portrait")
    return ws


def instructions_sheet(wb, styles):
    ws = wb.create_sheet("Instructions")
    merge_header(ws, 1, 1, 6, "Instructions", styles)
    add_subheader_row(ws, 3, ["Section", "Description", "Control", "Location", "Output", "Print"], styles)
    rows = [
        ("Purpose", "Credit committee decision support workbook", "", "", "Committee pack + model", "Yes"),
        ("Scenario Switch", "Change Base / Downside / Upside", "Active Scenario", "Inputs!B42", "Updates core engine", "Yes"),
        ("Grant Logic", "Grant enters only during construction as source of funds", "", "Grant_Model / Construction_Funding", "No grant in DSCR", "Yes"),
        ("Debt Logic", "Operational DSCR excludes grant and uses actual opening debt after construction", "", "Debt_DSCR", "Lender-ready ratios", "Yes"),
        ("Print Guidance", "Committee sheets are optimized for A4 export", "", "All CC_* sheets", "PDF-ready", "Yes"),
        ("Reading Order", "Executive Summary -> Recommendation -> Covenant Pack -> Scenario Matrix -> Funding & Uses", "", "", "", "Yes"),
    ]
    for r, row in enumerate(rows, start=4):
        for c, val in enumerate(row, start=1):
            ws.cell(r, c, val)
            style_cell(ws.cell(r, c), border=styles["border"], font=styles["fonts"]["body"],
                       align=Alignment(vertical="center", wrap_text=True))
    set_widths(ws, {1: 18, 2: 42, 3: 18, 4: 24, 5: 22, 6: 12})
    apply_print_setup(ws, "A1:F16")
    return ws


def inputs_sheet(wb, styles):
    ws = wb.create_sheet("Inputs")
    merge_header(ws, 1, 1, 7, "Inputs / Controls / Locked Basis", styles)
    add_subheader_row(ws, 3, ["Parameter", "Value", "Unit", "Status", "Comment", "", ""], styles)

    inputs = [
        ("Total Project Cost (TPC)", 27796156, "EUR", "LOCKED", "v4.5 basis"),
        ("Direct CAPEX (BoQ)", 24715200, "EUR", "LOCKED", "v4.5 basis"),
        ("Contingency", 2471520, "EUR", "LOCKED", "v4.5 basis"),
        ("Escalation", 609436, "EUR", "LOCKED", "v4.5 basis"),
        ("Debt", 16677694, "EUR", "LOCKED", "v4.5 basis"),
        ("Equity", 11118462, "EUR", "LOCKED", "v4.5 basis"),
        ("Total IDC (capitalized) - locked ref", 1031579, "EUR", "LOCKED", "Reference check"),
        ("Average DSCR", 3.07, "x", "LOCKED", "Reference"),
        ("Minimum DSCR", 1.68, "x", "LOCKED", "Reference"),
        ("Minimum DSCR Year", 2, "year", "LOCKED", "Reference"),
        ("Revenue Year 1", 8000000, "EUR", "LOCKED", "Operating model"),
        ("Revenue Year 5", 28000000, "EUR", "LOCKED", "Operating model"),
        ("Revenue Year 12", 32163198, "EUR", "LOCKED", "Operating model"),
        ("Steady-state EBITDA margin", 0.22, "%", "LOCKED", "Operating model"),
        ("Perpetual growth after Year 5", 0.02, "%", "ASSUMPTION", "Operating model"),
        ("Cash Conversion Cycle", 100, "days", "ASSUMPTION", "Operating model"),
        ("Net WC Year 5", 5753425, "EUR", "LOCKED", "Reference"),
        ("Net WC as % of Revenue", 0.2054794643, "%", "LOCKED", "Derived"),
        ("Working days", 250, "days/year", "ASSUMPTION", "Operating model"),
        ("Shifts", 2, "count", "ASSUMPTION", "Operating model"),
        ("Target normalized units/year", 291, "units", "ASSUMPTION", "Operating model"),
        ("Interest Rate", 0.045, "%", "ASSUMPTION", "Debt engine"),
        ("Tenor", 10, "years", "ASSUMPTION", "Debt engine"),
        ("Grace Period (Principal)", 2, "years", "ASSUMPTION", "Debt engine"),
        ("Target Minimum DSCR", 1.30, "x", "ASSUMPTION", "Debt engine"),
        ("DSRA months", 6, "months", "ASSUMPTION", "Debt engine"),
        ("Tax Rate", 0.00, "%", "ASSUMPTION", "Debt engine"),
        ("Maintenance CAPEX % Revenue", 0.015, "%", "ASSUMPTION", "Debt engine"),
        ("Cash Interest During Operations?", 1, "flag", "ASSUMPTION", "Debt engine"),
        ("Sculpt Principal to DSCR?", 1, "flag", "ASSUMPTION", "Debt engine"),
        ("Discount Rate for LLCR/PLCR", 0.10, "%", "ASSUMPTION", "Coverage engine"),
        ("Debt Start Year", 3, "year", "ASSUMPTION", "Coverage engine"),
        ("Debt End Year", 12, "year", "ASSUMPTION", "Coverage engine"),
        ("DSCR Lock Test Start Year", 3, "year", "ASSUMPTION", "Coverage engine"),
        ("Debt Tail Years for PLCR", 0, "years", "ASSUMPTION", "Coverage engine"),
        ("Use Post-DSRA CFADS for LLCR?", 1, "flag", "ASSUMPTION", "Coverage engine"),
        ("Balloon Allowed?", 0, "flag", "ASSUMPTION", "Coverage engine"),
        ("Balloon Amount", 0, "EUR", "ASSUMPTION", "Coverage engine"),
        ("Active Scenario", "Base", "text", "CONTROL", "Base / Downside / Upside"),
        ("Revenue Shock - Base", 0.00, "%", "ASSUMPTION", "Scenario"),
        ("Revenue Shock - Downside", -0.20, "%", "ASSUMPTION", "Scenario"),
        ("Revenue Shock - Upside", 0.10, "%", "ASSUMPTION", "Scenario"),
        ("EBITDA Margin Shock - Base", 0.00, "%", "ASSUMPTION", "Scenario"),
        ("EBITDA Margin Shock - Downside", -0.03, "%", "ASSUMPTION", "Scenario"),
        ("EBITDA Margin Shock - Upside", 0.02, "%", "ASSUMPTION", "Scenario"),
        ("Delay Months - Base", 0, "months", "ASSUMPTION", "Scenario"),
        ("Delay Months - Downside", 6, "months", "ASSUMPTION", "Scenario"),
        ("Delay Months - Upside", 0, "months", "ASSUMPTION", "Scenario"),
        ("WC Shock - Base", 0.00, "%", "ASSUMPTION", "Scenario"),
        ("WC Shock - Downside", 0.05, "%", "ASSUMPTION", "Scenario"),
        ("WC Shock - Upside", -0.02, "%", "ASSUMPTION", "Scenario"),
        ("Maintenance CAPEX Shock - Base", 0.00, "%", "ASSUMPTION", "Scenario"),
        ("Maintenance CAPEX Shock - Downside", 0.005, "%", "ASSUMPTION", "Scenario"),
        ("Maintenance CAPEX Shock - Upside", -0.002, "%", "ASSUMPTION", "Scenario"),
        ("Covenant Watch Buffer", 0.10, "x", "ASSUMPTION", "Scenario"),
        ("LLCR Minimum", 1.20, "x", "ASSUMPTION", "Scenario"),
        ("PLCR Minimum", 1.30, "x", "ASSUMPTION", "Scenario"),
        ("Grant Amount", 1198356, "EUR", "ASSUMPTION", "Balancing grant"),
        ("Grant % of Eligible CAPEX", 0.07, "%", "ASSUMPTION", "Grant logic"),
        ("Eligible CAPEX % of Direct CAPEX", 0.70, "%", "ASSUMPTION", "Grant logic"),
        ("Non-Eligible CAPEX % of Direct CAPEX", "=1-B63", "%", "FORMULA", "Derived"),
        ("Grant Disbursement Start Year", 1, "year", "ASSUMPTION", "Grant logic"),
        ("Grant Disbursement End Year", 2, "year", "ASSUMPTION", "Grant logic"),
        ("Debt Drawdown Start Year", 1, "year", "ASSUMPTION", "Construction"),
        ("Debt Drawdown End Year", 2, "year", "ASSUMPTION", "Construction"),
        ("Equity First Loss Funding?", 1, "flag", "ASSUMPTION", "Construction"),
        ("Equity Funding % of Non-Grant Residual", 1.00, "%", "ASSUMPTION", "Construction"),
        ("Construction Period Years", 2, "years", "ASSUMPTION", "Construction"),
        ("Initial DSRA Funding Required", 0, "flag", "ASSUMPTION", "Construction"),
        ("Initial DSRA Funding Timing", 2, "year", "ASSUMPTION", "Construction"),
        ("Upfront Fees % of Debt", 0.010, "%", "ASSUMPTION", "Construction"),
        ("Commitment Fee % on Undrawn Debt", 0.005, "%", "ASSUMPTION", "Construction"),
        ("IDC Rate During Construction", "=B25", "%", "FORMULA", "Linked to debt rate"),
        ("Grant Taxable?", 0, "flag", "ASSUMPTION", "Grant logic"),
        ("Debt Funds IDC?", 1, "flag", "ASSUMPTION", "Construction"),
        ("Equity Funds Fees?", 1, "flag", "ASSUMPTION", "Construction"),
        ("COD Year", 3, "year", "ASSUMPTION", "Construction / operations handoff"),
    ]

    start_row = 4
    for i, row in enumerate(inputs, start=start_row):
        for c, val in enumerate(row, start=1):
            ws.cell(i, c, val)
            style_cell(ws.cell(i, c), border=styles["border"], font=styles["fonts"]["body"],
                       align=Alignment(vertical="center"))
        status = ws.cell(i, 4).value
        if status in ("ASSUMPTION", "CONTROL"):
            ws.cell(i, 2).fill = styles["fills"]["input"]
            ws.cell(i, 2).font = styles["fonts"]["input"]
        elif status == "FORMULA":
            ws.cell(i, 2).font = styles["fonts"]["linked"]
            ws.cell(i, 2).fill = styles["fills"]["green"]
        else:
            ws.cell(i, 2).font = styles["fonts"]["static"]
            ws.cell(i, 2).fill = styles["fills"]["gray"]

        unit = ws.cell(i, 3).value
        if unit == "EUR":
            apply_number_format(ws.cell(i, 2), "eur")
        elif unit == "%":
            apply_number_format(ws.cell(i, 2), "pct2")
        elif unit == "x":
            apply_number_format(ws.cell(i, 2), "x")
        elif unit in ("days", "days/year", "years", "year", "months", "units", "count", "flag"):
            apply_number_format(ws.cell(i, 2), "int")
        add_comment(ws.cell(i, 2), f"Source: v5.2 model basis; status={status}; note={ws.cell(i,5).value}")

    # Scenario resolution block
    ws["F42"] = "Scenario Driver"
    ws["G42"] = "Active Value"
    style_cell(ws["F42"], font=styles["fonts"]["bold"], fill=styles["fills"]["light_blue"], border=styles["border"])
    style_cell(ws["G42"], font=styles["fonts"]["bold"], fill=styles["fills"]["light_blue"], border=styles["border"])
    driver_rows = {
        43: ("Revenue Shock", '=IF(B42="Base",B43,IF(B42="Downside",B44,B45))', "pct2"),
        44: ("EBITDA Margin Shock", '=IF(B42="Base",B46,IF(B42="Downside",B47,B48))', "pct2"),
        45: ("Delay Months", '=IF(B42="Base",B49,IF(B42="Downside",B50,B51))', "int"),
        46: ("WC Shock", '=IF(B42="Base",B52,IF(B42="Downside",B53,B54))', "pct2"),
        47: ("Maintenance CAPEX Shock", '=IF(B42="Base",B55,IF(B42="Downside",B56,B57))', "pct2"),
    }
    for r, (lab, formula, fmt) in driver_rows.items():
        ws[f"F{r}"] = lab
        ws[f"G{r}"] = formula
        style_cell(ws[f"F{r}"], border=styles["border"], fill=styles["fills"]["light_blue"], font=styles["fonts"]["bold"])
        style_cell(ws[f"G{r}"], border=styles["border"], fill=styles["fills"]["green"], font=styles["fonts"]["linked"])
        apply_number_format(ws[f"G{r}"], fmt)

    set_widths(ws, {1: 36, 2: 16, 3: 12, 4: 12, 5: 24, 6: 24, 7: 14})
    apply_print_setup(ws, "A1:G82")
    return ws


def sources_uses_sheet(wb, styles):
    ws = wb.create_sheet("Sources_Uses")
    merge_header(ws, 1, 1, 5, "Sources & Uses", styles)
    add_subheader_row(ws, 3, ["Line Item", "Amount (EUR)", "Type", "% of Total Uses", "Comment"], styles)
    lines = [
        ("Direct CAPEX", "=Inputs!B5", "Use", '=IF($B$11=0,0,B4/$B$11)', "Locked"),
        ("Contingency", "=Inputs!B6", "Use", '=IF($B$11=0,0,B5/$B$11)', "Locked"),
        ("Escalation", "=Inputs!B7", "Use", '=IF($B$11=0,0,B6/$B$11)', "Locked"),
        ("Base TPC", "=SUM(B4:B6)", "Use", '=IF($B$11=0,0,B7/$B$11)', "Calculated"),
        ("IDC", "=Inputs!B10", "Use", '=IF($B$11=0,0,B8/$B$11)', "Locked reference"),
        ("Upfront Fees", "=Inputs!B74*Inputs!B8", "Use", '=IF($B$11=0,0,B9/$B$11)', "Calculated"),
        ("Initial DSRA Funding", '=IF(Inputs!B72=1,Debt_DSCR!D13,0)', "Use", '=IF($B$11=0,0,B10/$B$11)', "Optional"),
        ("Total Uses", "=SUM(B7:B10)", "Use", '=IF($B$11=0,0,1)', "All-in"),
        ("Grant", "=Inputs!B61", "Source", '=IF($B$11=0,0,B12/$B$11)', "Construction source"),
        ("Debt", "=Inputs!B8", "Source", '=IF($B$11=0,0,B13/$B$11)', "Committed debt"),
        ("Equity", "=Inputs!B9", "Source", '=IF($B$11=0,0,B14/$B$11)', "Sponsor equity"),
        ("Total Sources", "=SUM(B12:B14)", "Source", '=IF($B$11=0,0,B15/$B$11)', "All sources"),
        ("Sources minus Uses", "=B15-B11", "Check", "", "Must be 0"),
    ]
    row = 4
    for name, amt, typ, pct, cmt in lines:
        ws.cell(row, 1, name)
        ws.cell(row, 2, amt)
        ws.cell(row, 3, typ)
        ws.cell(row, 4, pct)
        ws.cell(row, 5, cmt)
        for c in range(1, 6):
            style_cell(ws.cell(row, c), border=styles["border"], font=styles["fonts"]["body"])
        if name in ("Total Uses", "Total Sources", "Sources minus Uses", "Base TPC"):
            ws.cell(row, 1).font = styles["fonts"]["bold"]
            ws.cell(row, 2).font = styles["fonts"]["bold"]
            ws.cell(row, 2).border = styles["top_border"]
        ws.cell(row, 2).font = styles["fonts"]["linked"]
        apply_number_format(ws.cell(row, 2), "eur")
        if pct:
            apply_number_format(ws.cell(row, 4), "pct")
        row += 1
    set_widths(ws, {1: 28, 2: 18, 3: 12, 4: 16, 5: 24})
    apply_print_setup(ws, "A1:E20")
    return ws


def capex_phasing_sheet(wb, styles):
    ws = wb.create_sheet("CAPEX_Phasing")
    merge_header(ws, 1, 1, 15, "CAPEX Phasing / Drawdown Basis", styles)
    years = ["Metric"] + [f"Y{i}" for i in range(1, 13)] + ["Comment", "Check"]
    add_subheader_row(ws, 3, years, styles)
    for i in range(1, 13):
        ws.cell(2, i + 1, i)

    # Phasing defaults
    phasing_cells = {2: 0.40, 3: 0.60}
    ws["A4"] = "Direct CAPEX Phasing %"
    ws["A5"] = "Direct CAPEX Amount"
    ws["A6"] = "Contingency Phasing %"
    ws["A7"] = "Contingency Amount"
    ws["A8"] = "Escalation Phasing %"
    ws["A9"] = "Escalation Amount"
    ws["A10"] = "Total Construction Uses Before IDC"
    ws["A11"] = "Grant Eligible CAPEX"
    ws["A12"] = "Non-Eligible CAPEX"
    ws["A13"] = "Upfront Fees"
    ws["A14"] = "Initial DSRA Funding"
    ws["A15"] = "IDC"
    ws["A16"] = "Total Uses"

    for y in range(1, 13):
        col = get_column_letter(y + 1)
        ws[f"{col}4"] = phasing_cells.get(y + 1, 0) if y in (1,2) else 0  # overwritten below
    # Correct exact phasing
    for col_idx in range(2, 14):
        cell = ws.cell(4, col_idx)
        if col_idx == 2:
            cell.value = 0.40
        elif col_idx == 3:
            cell.value = 0.60
        else:
            cell.value = 0
        cell.fill = styles["fills"]["input"]
        cell.font = styles["fonts"]["input"]
        apply_number_format(cell, "pct")
    for col_idx in range(2, 14):
        col = get_column_letter(col_idx)
        ws[f"{col}5"] = f"={col}4*Inputs!B5"
        ws[f"{col}6"] = f"={col}4"
        ws[f"{col}7"] = f"={col}6*Inputs!B6"
        ws[f"{col}8"] = f"={col}4"
        ws[f"{col}9"] = f"={col}8*Inputs!B7"
        ws[f"{col}10"] = f"={col}5+{col}7+{col}9"
        ws[f"{col}11"] = f"={col}5*Inputs!B63"
        ws[f"{col}12"] = f"={col}5-{col}11"
        if col_idx == 2:
            ws[f"{col}13"] = 0
        elif col_idx == 3:
            ws[f"{col}13"] = "=Inputs!B8*Inputs!B75"
        else:
            ws[f"{col}13"] = 0
        ws[f"{col}14"] = f'=IF(Inputs!B72=1,IF({col}$2=Inputs!B73,Debt_DSCR!D13,0),0)'
        ws[f"{col}15"] = f"=Construction_Funding!{col}12"
        ws[f"{col}16"] = f"={col}10+{col}13+{col}14+{col}15"
        for r in range(4, 17):
            style_cell(ws[f"{col}{r}"], border=styles["border"], font=styles["fonts"]["linked"] if r>=5 else styles["fonts"]["body"])
        for r in (5,7,9,10,11,12,13,14,15,16):
            apply_number_format(ws[f"{col}{r}"], "eur")
        for r in (4,6,8):
            apply_number_format(ws[f"{col}{r}"], "pct")
    for r in range(4, 17):
        style_cell(ws[f"A{r}"], font=styles["fonts"]["bold"], border=styles["border"])
        ws[f"N{r}"] = ""
        ws[f"O{r}"] = ""
    ws["N4"] = "Default phasing 40% / 60%"
    ws["N11"] = "Eligible share of direct CAPEX"
    ws["N15"] = "Modeled IDC from construction sheet"
    set_widths(ws, {1: 30, **{i: 12 for i in range(2,14)}, 14: 24, 15: 16})
    apply_print_setup(ws, "A1:O20")
    return ws


def grant_model_sheet(wb, styles):
    ws = wb.create_sheet("Grant_Model")
    merge_header(ws, 1, 1, 15, "Grant Model", styles)
    add_subheader_row(ws, 3, ["Metric"] + [f"Y{i}" for i in range(1, 13)] + ["Comment", "Check"], styles)
    for i in range(1, 13):
        ws.cell(2, i + 1, i)
    labels = {
        4: "Grant Eligible CAPEX",
        5: "Grant Rate",
        6: "Theoretical Grant",
        7: "Grant Amount Applied",
        8: "Grant Phasing %",
        9: "Grant Drawdown",
        10: "Cumulative Grant Drawn",
        11: "Undrawn Grant Balance",
    }
    for r, lab in labels.items():
        ws[f"A{r}"] = lab
        style_cell(ws[f"A{r}"], font=styles["fonts"]["bold"], border=styles["border"])
    for col_idx in range(2, 14):
        col = get_column_letter(col_idx)
        ws[f"{col}4"] = f"=CAPEX_Phasing!{col}11"
        ws[f"{col}5"] = "=Inputs!B62"
        ws[f"{col}6"] = f"={col}4*{col}5"
        ws[f"{col}7"] = f"={col}6"
        ws[f"{col}8"] = f"=CAPEX_Phasing!{col}4"
        ws[f"{col}9"] = f"=Inputs!B61*{col}8"
        if col_idx == 2:
            ws[f"{col}10"] = f"={col}9"
        else:
            prev = get_column_letter(col_idx - 1)
            ws[f"{col}10"] = f"={prev}10+{col}9"
        ws[f"{col}11"] = f"=MAX(0,Inputs!B61-{col}10)"
        for r in range(4, 12):
            style_cell(ws[f"{col}{r}"], border=styles["border"], font=styles["fonts"]["linked"])
        for r in (4,6,7,9,10,11):
            apply_number_format(ws[f"{col}{r}"], "eur")
        for r in (5,8):
            apply_number_format(ws[f"{col}{r}"], "pct")
    ws["N4"] = "Eligible CAPEX imported"
    ws["N9"] = "Draws per phasing"
    set_widths(ws, {1: 26, **{i: 12 for i in range(2,14)}, 14: 22, 15: 14})
    apply_print_setup(ws, "A1:O18")
    return ws


def construction_funding_sheet(wb, styles):
    ws = wb.create_sheet("Construction_Funding")
    merge_header(ws, 1, 1, 15, "Construction Funding Waterfall", styles)
    add_subheader_row(ws, 3, ["Metric"] + [f"Y{i}" for i in range(1, 13)] + ["Comment", "Check"], styles)
    for i in range(1, 13):
        ws.cell(2, i + 1, i)

    labels = {
        4: "Construction Uses Before Financing",
        5: "Grant Drawdown",
        6: "Residual Uses After Grant",
        7: "Equity Drawdown",
        8: "Debt Drawdown Before IDC",
        9: "Opening Debt During Construction",
        10: "Average Debt During Construction",
        11: "IDC Rate",
        12: "IDC",
        13: "Commitment Fee",
        14: "Total Financing Cost During Construction",
        15: "Debt Drawdown Including IDC",
        16: "Closing Debt During Construction",
        17: "Sources",
        18: "Uses",
        19: "Sources minus Uses",
        20: "Cumulative Debt Drawn",
        21: "Undrawn Debt Commitment",
        22: "Cumulative Equity Drawn",
        23: "Undrawn Equity Commitment",
        24: "Cumulative Sources",
        25: "Cumulative Uses",
        26: "Cumulative Sources minus Uses",
    }
    for r, lab in labels.items():
        ws[f"A{r}"] = lab
        style_cell(ws[f"A{r}"], font=styles["fonts"]["bold"], border=styles["border"])

    for col_idx in range(2, 14):
        col = get_column_letter(col_idx)
        ws[f"{col}4"] = f"=CAPEX_Phasing!{col}10+CAPEX_Phasing!{col}13+CAPEX_Phasing!{col}14"
        ws[f"{col}5"] = f"=Grant_Model!{col}9"
        ws[f"{col}6"] = f"=MAX(0,{col}4-{col}5)"
        ws[f"{col}7"] = f"=IF(Inputs!B70=1,MIN({col}6,Inputs!B9*CAPEX_Phasing!{col}4),MIN({col}6,Inputs!B9*Inputs!B70*CAPEX_Phasing!{col}4))"
        ws[f"{col}8"] = f"=MAX(0,{col}6-{col}7)"
        if col_idx == 2:
            ws[f"{col}9"] = 0
        else:
            prev = get_column_letter(col_idx - 1)
            ws[f"{col}9"] = f"={prev}16"
        ws[f"{col}10"] = f"={col}9+({col}8/2)"
        ws[f"{col}11"] = "=Inputs!B76"
        ws[f"{col}12"] = f"=IF(Inputs!B78=1,{col}10*{col}11,0)"
        ws[f"{col}13"] = f"=MAX(0,(Inputs!B8-({col}9+{col}8)))*Inputs!B75"
        ws[f"{col}14"] = f"={col}12+{col}13"
        ws[f"{col}15"] = f"={col}8+IF(Inputs!B78=1,{col}14,0)"
        ws[f"{col}16"] = f"={col}9+{col}15"
        ws[f"{col}17"] = f"={col}5+{col}7+{col}15"
        ws[f"{col}18"] = f"={col}4+{col}14"
        ws[f"{col}19"] = f"={col}17-{col}18"
        if col_idx == 2:
            ws[f"{col}20"] = f"={col}15"
            ws[f"{col}22"] = f"={col}7"
            ws[f"{col}24"] = f"={col}17"
            ws[f"{col}25"] = f"={col}18"
        else:
            prev = get_column_letter(col_idx - 1)
            ws[f"{col}20"] = f"={prev}20+{col}15"
            ws[f"{col}22"] = f"={prev}22+{col}7"
            ws[f"{col}24"] = f"={prev}24+{col}17"
            ws[f"{col}25"] = f"={prev}25+{col}18"
        ws[f"{col}21"] = f"=Inputs!B8-{col}20"
        ws[f"{col}23"] = f"=Inputs!B9-{col}22"
        ws[f"{col}26"] = f"={col}24-{col}25"
        for r in range(4, 27):
            style_cell(ws[f"{col}{r}"], border=styles["border"], font=styles["fonts"]["linked"])
        for r in [4,5,6,7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26]:
            apply_number_format(ws[f"{col}{r}"], "eur")
        apply_number_format(ws[f"{col}11"], "pct2")
    ws["N4"] = "Before IDC"
    ws["N15"] = "Debt including financed IDC/fees"
    ws["N19"] = "Should be ~0"
    set_widths(ws, {1: 34, **{i: 12 for i in range(2,14)}, 14: 22, 15: 14})
    apply_print_setup(ws, "A1:O30")
    return ws


def funding_structure_sheet(wb, styles):
    ws = wb.create_sheet("Funding_Structure")
    merge_header(ws, 1, 1, 4, "Funding Structure", styles)
    add_subheader_row(ws, 3, ["Metric", "Value", "Unit", "Comment"], styles)
    rows = [
        ("Total Uses", "=Sources_Uses!B11", "EUR", "All-in uses"),
        ("Grant", "=Sources_Uses!B12", "EUR", "Construction source"),
        ("Debt", "=Sources_Uses!B13", "EUR", "Committed debt"),
        ("Equity", "=Sources_Uses!B14", "EUR", "Sponsor equity"),
        ("Total Sources", "=Sources_Uses!B15", "EUR", "All sources"),
        ("Grant % of Uses", '=IF(B4=0,0,B5/B4)', "%", "Coverage"),
        ("Debt % of Uses", '=IF(B4=0,0,B6/B4)', "%", "Coverage"),
        ("Equity % of Uses", '=IF(B4=0,0,B7/B4)', "%", "Coverage"),
        ("Debt / Equity", '=IF(B7=0,0,B6/B7)', "x", "Leverage"),
        ("Net Debt After Grant", '=MAX(0,B6-B5)', "EUR", "Net senior exposure"),
        ("Grant Coverage of Eligible CAPEX", '=IF(SUM(CAPEX_Phasing!B11:M11)=0,0,B5/SUM(CAPEX_Phasing!B11:M11))', "%", "Grant discipline"),
        ("Funding Gap / (Surplus)", '=B8-B4', "EUR", "Should be 0"),
    ]
    r = 4
    for name, formula, unit, cmt in rows:
        ws.cell(r, 1, name)
        ws.cell(r, 2, formula)
        ws.cell(r, 3, unit)
        ws.cell(r, 4, cmt)
        for c in range(1, 5):
            style_cell(ws.cell(r, c), border=styles["border"], font=styles["fonts"]["body"])
        if unit == "EUR":
            apply_number_format(ws.cell(r, 2), "eur")
        elif unit == "%":
            apply_number_format(ws.cell(r, 2), "pct")
        elif unit == "x":
            apply_number_format(ws.cell(r, 2), "x")
        r += 1
    set_widths(ws, {1: 32, 2: 18, 3: 10, 4: 24})
    apply_print_setup(ws, "A1:D18")
    return ws


def grant_eligibility_sheet(wb, styles):
    ws = wb.create_sheet("Grant_Eligibility")
    merge_header(ws, 1, 1, 6, "Grant Eligibility", styles)
    add_subheader_row(ws, 3, ["Category", "Amount", "Eligible %", "Eligible Amount", "Non-Eligible Amount", "Comment"], styles)
    rows = [
        ("Direct CAPEX", "=Inputs!B5", "=Inputs!B63", "=B4*C4", "=B4-D4", "Eligible share per rules"),
        ("Contingency", "=Inputs!B6", 0, "=B5*C5", "=B5-D5", "Assumed non-eligible"),
        ("Escalation", "=Inputs!B7", 0, "=B6*C6", "=B6-D6", "Assumed non-eligible"),
        ("IDC", "=Inputs!B10", 0, "=B7*C7", "=B7-D7", "Assumed non-eligible"),
        ("Fees", "=Inputs!B74*Inputs!B8", 0, "=B8*C8", "=B8-D8", "Assumed non-eligible"),
        ("DSRA", '=IF(Inputs!B72=1,Debt_DSCR!D13,0)', 0, "=B9*C9", "=B9-D9", "Assumed non-eligible"),
        ("Total", "=SUM(B4:B9)", "", "=SUM(D4:D9)", "=SUM(E4:E9)", "Audit total"),
    ]
    r = 4
    for row in rows:
        for c, val in enumerate(row, start=1):
            ws.cell(r, c, val)
            style_cell(ws.cell(r, c), border=styles["border"], font=styles["fonts"]["body"])
        apply_number_format(ws.cell(r, 2), "eur")
        if r < 10:
            apply_number_format(ws.cell(r, 3), "pct")
        apply_number_format(ws.cell(r, 4), "eur")
        apply_number_format(ws.cell(r, 5), "eur")
        if r == 10:
            ws.cell(r, 1).font = styles["fonts"]["bold"]
        r += 1
    set_widths(ws, {1: 22, 2: 16, 3: 12, 4: 18, 5: 20, 6: 24})
    apply_print_setup(ws, "A1:F15")
    return ws


def revenue_ebitda_sheet(wb, styles):
    ws = wb.create_sheet("Revenue_EBITDA")
    merge_header(ws, 1, 1, 16, "Revenue Ramp & EBITDA", styles)
    add_subheader_row(ws, 3, ["Metric"] + [f"Y{i}" for i in range(1, 13)] + ["Notes", "Formula Logic", "Status"], styles)
    for i in range(1, 13):
        ws.cell(2, i + 1, i)

    ws["A4"] = "Revenue"
    ws["B4"] = "=Inputs!B14*(1+Inputs!G43)*MAX(0,1-Inputs!G45/12)"
    ws["C4"] = "=(Inputs!B14+(1/4)*(Inputs!B15-Inputs!B14))*(1+Inputs!G43)"
    ws["D4"] = "=(Inputs!B14+(2/4)*(Inputs!B15-Inputs!B14))*(1+Inputs!G43)"
    ws["E4"] = "=(Inputs!B14+(3/4)*(Inputs!B15-Inputs!B14))*(1+Inputs!G43)"
    ws["F4"] = "=Inputs!B15*(1+Inputs!G43)"
    for col_idx in range(7, 14):
        col = get_column_letter(col_idx)
        ws[f"{col}4"] = f"=F4*(1+Inputs!B18)^({col_idx-6})"
    ws["N4"] = "Scenario-aware revenue"
    ws["O4"] = "Y1 delay + shock; Y5 anchor; 2% growth after Y5"
    ws["P4"] = "ACTIVE"

    ws["A5"] = "EBITDA Margin"
    for col_idx in range(2, 14):
        col = get_column_letter(col_idx)
        ws[f"{col}5"] = "=MAX(0,Inputs!B17+Inputs!G44)"
    ws["N5"] = "Scenario-aware margin"

    ws["A6"] = "EBITDA"
    ws["A7"] = "Revenue Growth"
    ws["A8"] = "EBITDA Margin Check"
    for col_idx in range(2, 14):
        col = get_column_letter(col_idx)
        ws[f"{col}6"] = f"={col}4*{col}5"
        if col_idx == 2:
            ws[f"{col}7"] = ""
        else:
            prev = get_column_letter(col_idx - 1)
            ws[f"{col}7"] = f"=IF({prev}4=0,0,{col}4/{prev}4-1)"
        ws[f"{col}8"] = f"=IF({col}4=0,0,{col}6/{col}4)"
        for r in range(4, 9):
            style_cell(ws[f"{col}{r}"], border=styles["border"],
                       font=styles["fonts"]["linked"] if r in (4,5,6,7,8) else styles["fonts"]["body"])
        apply_number_format(ws[f"{col}4"], "eur")
        apply_number_format(ws[f"{col}5"], "pct")
        apply_number_format(ws[f"{col}6"], "eur")
        if col_idx > 2:
            apply_number_format(ws[f"{col}7"], "pct")
        apply_number_format(ws[f"{col}8"], "pct")

    for r in range(4, 9):
        style_cell(ws[f"A{r}"], font=styles["fonts"]["bold"], border=styles["border"])
        for c in range(14, 17):
            style_cell(ws.cell(r, c), border=styles["border"], font=styles["fonts"]["body"],
                       align=Alignment(wrap_text=True, vertical="center"))
    set_widths(ws, {1: 22, **{i: 12 for i in range(2,14)}, 14: 22, 15: 30, 16: 12})

    chart = LineChart()
    chart.title = "Revenue and EBITDA"
    chart.y_axis.title = "EUR"
    chart.x_axis.title = "Year"
    data = Reference(ws, min_col=2, max_col=13, min_row=4, max_row=6)
    cats = Reference(ws, min_col=2, max_col=13, min_row=3, max_row=3)
    chart.add_data(data, titles_from_data=False, from_rows=True)
    chart.set_categories(cats)
    chart.height = 7
    chart.width = 16
    ws.add_chart(chart, "A11")
    apply_print_setup(ws, "A1:P28")
    return ws


def working_capital_sheet(wb, styles):
    ws = wb.create_sheet("Working_Capital")
    merge_header(ws, 1, 1, 16, "Working Capital Model", styles)
    add_subheader_row(ws, 3, ["Metric"] + [f"Y{i}" for i in range(1, 13)] + ["Notes", "Status", "Comment"], styles)
    for i in range(1, 13):
        ws.cell(2, i + 1, i)

    labels = {4: "Revenue", 5: "Net WC / Revenue", 6: "Net WC", 7: "Change in Net WC", 8: "CCC (days)", 10: "Y5 WC Check", 11: "Status"}
    for r, lab in labels.items():
        ws[f"A{r}"] = lab
        style_cell(ws[f"A{r}"], font=styles["fonts"]["bold"], border=styles["border"])

    for col_idx in range(2, 14):
        col = get_column_letter(col_idx)
        ws[f"{col}4"] = f"=Revenue_EBITDA!{col}4"
        ws[f"{col}5"] = "=Inputs!B21+Inputs!G46"
        ws[f"{col}6"] = f"={col}4*{col}5"
        if col_idx == 2:
            ws[f"{col}7"] = f"={col}6"
        else:
            prev = get_column_letter(col_idx - 1)
            ws[f"{col}7"] = f"={col}6-{prev}6"
        ws[f"{col}8"] = "=Inputs!B19"
        for r in range(4, 9):
            style_cell(ws[f"{col}{r}"], border=styles["border"], font=styles["fonts"]["linked"])
        apply_number_format(ws[f"{col}4"], "eur")
        apply_number_format(ws[f"{col}5"], "pct2")
        apply_number_format(ws[f"{col}6"], "eur")
        apply_number_format(ws[f"{col}7"], "eur")
        apply_number_format(ws[f"{col}8"], "int")

    ws["B10"] = "=F6"
    ws["C10"] = "=Inputs!B20"
    ws["D10"] = "=B10-C10"
    ws["B11"] = '=IF(ABS(D10)<=1,"OK","REVIEW")'
    for cell in ("B10","C10","D10"):
        style_cell(ws[cell], border=styles["border"], font=styles["fonts"]["linked"])
        apply_number_format(ws[cell], "eur")
    style_cell(ws["B11"], border=styles["border"], font=styles["fonts"]["bold"])
    ws["N6"] = "Y5 should match locked value under Base"
    ws["O6"] = "Check"
    ws["P6"] = "Expected = 5,753,425"
    set_widths(ws, {1: 22, **{i: 12 for i in range(2,14)}, 14: 26, 15: 12, 16: 22})
    apply_print_setup(ws, "A1:P20")
    return ws


def operational_model_sheet(wb, styles):
    ws = wb.create_sheet("Operational_Model")
    merge_header(ws, 1, 1, 10, "Operational Model - Capacity vs Revenue", styles)
    add_subheader_row(ws, 3, ["Product", "Mix %", "Unit Price", "Revenue @ Y5", "Units @ Y5", "Complexity Factor", "Normalized Units", "Comment", "Editable", "Status"], styles)
    products = [
        ("Transformer tank", 0.50, 120000, None, None, 1.00, None, "Base reference product", "Yes", "ASSUMPTION"),
        ("Radiator panels", 0.30, 25000, None, None, 0.35, None, "Normalized vs tank", "Yes", "ASSUMPTION"),
        ("Heavy structures", 0.20, 60000, None, None, 0.60, None, "Normalized vs tank", "Yes", "ASSUMPTION"),
    ]
    row = 4
    for prod, mix, price, _, _, cf, _, cmt, edit, status in products:
        ws.cell(row, 1, prod)
        ws.cell(row, 2, mix)
        ws.cell(row, 3, price)
        ws.cell(row, 4, f"=Inputs!B15*B{row}")
        ws.cell(row, 5, f"=IF(C{row}=0,0,D{row}/C{row})")
        ws.cell(row, 6, cf)
        ws.cell(row, 7, f"=E{row}*F{row}")
        ws.cell(row, 8, cmt)
        ws.cell(row, 9, edit)
        ws.cell(row, 10, status)
        for c in range(1, 11):
            style_cell(ws.cell(row, c), border=styles["border"], font=styles["fonts"]["body"])
        for c in (2,3,6):
            ws.cell(row, c).fill = styles["fills"]["input"]
            ws.cell(row, c).font = styles["fonts"]["input"]
        apply_number_format(ws.cell(row, 2), "pct")
        apply_number_format(ws.cell(row, 3), "eur")
        apply_number_format(ws.cell(row, 4), "eur")
        apply_number_format(ws.cell(row, 5), "dec")
        apply_number_format(ws.cell(row, 6), "dec")
        apply_number_format(ws.cell(row, 7), "dec")
        row += 1
    ws[f"A{row}"] = "Total"
    ws[f"D{row}"] = "=SUM(D4:D6)"
    ws[f"E{row}"] = "=SUM(E4:E6)"
    ws[f"G{row}"] = "=SUM(G4:G6)"
    for c in ("A", "D", "E", "G"):
        ws[f"{c}{row}"].font = styles["fonts"]["bold"]

    merge_header(ws, 10, 1, 6, "Capacity by Zone", styles)
    add_subheader_row(ws, 12, ["Zone", "Capacity Units/Year", "Bottleneck?", "Comment", "Editable", "Status"], styles)
    capacity_data = [
        ("Raw material warehouse", 350, "No", "Support function", "Yes", "ASSUMPTION"),
        ("Cutting", 335, "No", "Automated", "Yes", "ASSUMPTION"),
        ("Forming", 300, "No", "Adequate", "Yes", "ASSUMPTION"),
        ("Welding", 295, "Yes", "Primary bottleneck", "Yes", "ASSUMPTION"),
        ("Blasting / Painting", 290, "Yes", "Secondary bottleneck", "Yes", "ASSUMPTION"),
        ("Assembly", 305, "No", "Balanced", "Yes", "ASSUMPTION"),
        ("Testing / QA", 300, "No", "Balanced", "Yes", "ASSUMPTION"),
    ]
    row2 = 13
    for rec in capacity_data:
        for c, val in enumerate(rec, start=1):
            ws.cell(row2, c, val)
            style_cell(ws.cell(row2, c), border=styles["border"], font=styles["fonts"]["body"])
        ws.cell(row2, 2).fill = styles["fills"]["input"]
        ws.cell(row2, 2).font = styles["fonts"]["input"]
        apply_number_format(ws.cell(row2, 2), "dec")
        row2 += 1

    ws[f"A{row2}"] = "Plant Effective Capacity"
    ws[f"B{row2}"] = "=MIN(B13:B19)"
    ws[f"A{row2+1}"] = "Required Normalized Units"
    ws[f"B{row2+1}"] = "=Inputs!B24"
    ws[f"A{row2+2}"] = "Capacity Headroom / (Shortfall)"
    ws[f"B{row2+2}"] = f"=B{row2}-B{row2+1}"
    ws[f"A{row2+3}"] = "Implied Revenue Capacity"
    ws[f"B{row2+3}"] = f"=Inputs!B15*(B{row2}/B{row2+1})"
    for rr in range(row2, row2+4):
        style_cell(ws[f"A{rr}"], font=styles["fonts"]["bold"], border=styles["border"])
        style_cell(ws[f"B{rr}"], border=styles["border"], font=styles["fonts"]["linked"])
    apply_number_format(ws[f"B{row2}"], "dec")
    apply_number_format(ws[f"B{row2+1}"], "dec")
    apply_number_format(ws[f"B{row2+2}"], "dec")
    apply_number_format(ws[f"B{row2+3}"], "eur")
    set_widths(ws, {1: 24, 2: 14, 3: 14, 4: 18, 5: 14, 6: 16, 7: 16, 8: 22, 9: 10, 10: 12})
    apply_print_setup(ws, "A1:J28")
    return ws


def manpower_sheet(wb, styles):
    ws = wb.create_sheet("Manpower")
    merge_header(ws, 1, 1, 8, "Detailed Manpower Plan by Zone and Shift", styles)
    add_subheader_row(ws, 3, ["Zone", "Role", "Per Shift", "Shifts", "Total HC", "Category", "Comment", "Status"], styles)
    rows = [
        ("Receiving & Warehouse", "Forklift + Store + Receiving QC", 6, 2, "=C4*D4", "Indirect", "From prior layout model", "ASSUMPTION"),
        ("Cutting", "CNC operators + helpers + programmer share", 5.5, 2, "=C5*D5", "Direct", "Rounded blended staffing", "ASSUMPTION"),
        ("Forming", "Operators + helpers", 3, 2, "=C6*D6", "Direct", "Press / rolling", "ASSUMPTION"),
        ("Welding", "Welders + SAW + fitters + inspectors + supervisors", 33, 2, "=C7*D7", "Direct", "Main bottleneck", "ASSUMPTION"),
        ("Blasting / Painting", "Operators + painters + QC", 8, 2, "=C8*D8", "Direct", "Batch process", "ASSUMPTION"),
        ("Assembly", "Assemblers + mechanics + supervisor", 10, 2, "=C9*D9", "Direct", "Balanced line", "ASSUMPTION"),
        ("Testing / QA", "Engineers + technicians + QA", 7, 2, "=C10*D10", "Indirect", "Critical release gate", "ASSUMPTION"),
        ("Maintenance & Utilities", "Mechanical + electrical + utilities", 13, 1, "=C11*D11", "Indirect", "Plant support", "ASSUMPTION"),
        ("Internal Logistics", "Drivers + dispatch", 11, 1, "=C12*D12", "Indirect", "Shared across plant", "ASSUMPTION"),
        ("Engineering / Admin", "Production eng + QA + planning + admin", 27, 1, "=C13*D13", "Overhead", "Day shift support", "ASSUMPTION"),
    ]
    r = 4
    for row in rows:
        for c, val in enumerate(row, start=1):
            ws.cell(r, c, val)
            style_cell(ws.cell(r, c), border=styles["border"], font=styles["fonts"]["body"])
        ws.cell(r, 3).fill = styles["fills"]["input"]
        ws.cell(r, 4).fill = styles["fills"]["input"]
        ws.cell(r, 3).font = styles["fonts"]["input"]
        ws.cell(r, 4).font = styles["fonts"]["input"]
        apply_number_format(ws.cell(r, 3), "dec")
        apply_number_format(ws.cell(r, 4), "int")
        apply_number_format(ws.cell(r, 5), "dec")
        r += 1

    summaries = [
        ("Total Headcount", "=SUM(E4:E13)"),
        ("Direct Production HC", '=SUMIF(F4:F13,"Direct",E4:E13)'),
        ("Indirect HC", '=SUMIF(F4:F13,"Indirect",E4:E13)'),
        ("Overhead HC", '=SUMIF(F4:F13,"Overhead",E4:E13)'),
        ("Normalized Units / Direct HC", "=Operational_Model!G7/E15"),
    ]
    for name, formula in summaries:
        ws[f"A{r}"] = name
        ws[f"E{r}"] = formula
        ws[f"A{r}"].font = styles["fonts"]["bold"]
        style_cell(ws[f"E{r}"], border=styles["border"], font=styles["fonts"]["linked"])
        apply_number_format(ws[f"E{r}"], "dec")
        r += 1
    set_widths(ws, {1: 24, 2: 38, 3: 12, 4: 10, 5: 12, 6: 12, 7: 24, 8: 12})
    apply_print_setup(ws, "A1:H22")
    return ws


def debt_dscr_sheet(wb, styles):
    ws = wb.create_sheet("Debt_DSCR")
    merge_header(ws, 1, 1, 18, "Debt / Coverage / Covenant Engine", styles)
    add_subheader_row(ws, 3, ["Metric"] + [f"Y{i}" for i in range(1, 13)] + ["Comment", "Threshold", "Audit", "Status", "Notes"], styles)
    for i in range(1, 13):
        ws.cell(2, i + 1, i)

    labels = {
        4: "Opening Debt Balance",
        5: "Interest Rate",
        6: "Interest Expense",
        7: "Revenue",
        8: "EBITDA",
        9: "Change in Net WC",
        10: "Maintenance CAPEX",
        11: "Cash Taxes",
        12: "CFADS Pre-DSRA",
        13: "DSRA Target",
        14: "DSRA Opening",
        15: "DSRA Funding / (Release)",
        16: "CFADS Post-DSRA",
        17: "Target DSCR",
        18: "Allowed Debt Service",
        19: "Sculpted Principal",
        20: "Total Debt Service",
        21: "Closing Debt Balance",
        22: "Actual DSCR",
        23: "Min DSCR Threshold",
        24: "Covenant Flag",
        25: "Discount Factor",
        26: "PV of CFADS",
        27: "Remaining PV of CFADS",
        28: "LLCR",
        29: "Remaining PV to Project End",
        30: "PLCR",
        31: "In Loan Life?",
        32: "Debt Fully Repaid by End?",
        33: "Final Debt Balance",
        34: "Overall Covenant Status",
    }
    for r, lab in labels.items():
        ws[f"A{r}"] = lab
        style_cell(ws[f"A{r}"], font=styles["fonts"]["bold"], border=styles["border"])

    for col_idx in range(2, 14):
        col = get_column_letter(col_idx)
        if col_idx == 2:
            ws[f"{col}4"] = "=INDEX(Construction_Funding!B16:M16,1,Inputs!B80-1)"
        else:
            prev = get_column_letter(col_idx - 1)
            ws[f"{col}4"] = f"={prev}21"
        ws[f"{col}5"] = "=Inputs!B25"
        ws[f"{col}6"] = f"={col}4*{col}5"
        ws[f"{col}7"] = f"=Revenue_EBITDA!{col}4"
        ws[f"{col}8"] = f"=Revenue_EBITDA!{col}6"
        ws[f"{col}9"] = f"=Working_Capital!{col}7"
        ws[f"{col}10"] = f"={col}7*(Inputs!B31+Inputs!G47)"
        ws[f"{col}11"] = f"=MAX(0,({col}8-{col}6)*Inputs!B30)"
        ws[f"{col}12"] = f"={col}8-{col}9-{col}10-{col}11"
        ws[f"{col}17"] = "=Inputs!B28"
        ws[f"{col}18"] = f'=IF(OR({col}$2<Inputs!B35,{col}$2>Inputs!B36),0,{col}12/{col}17)'
        ws[f"{col}19"] = f'=IF({col}18=0,0,IF({col}$2=Inputs!B36,IF(Inputs!B40=1,MAX(0,{col}4-Inputs!B41),{col}4),MIN({col}4,MAX(0,{col}18-{col}6))))'
        ws[f"{col}20"] = f"={col}6+{col}19"
        ws[f"{col}13"] = f"={col}20*(Inputs!B29/12)"
        if col_idx == 2:
            ws[f"{col}14"] = 0
        else:
            prev = get_column_letter(col_idx - 1)
            ws[f"{col}14"] = f"={prev}13"
        ws[f"{col}15"] = f"={col}13-{col}14"
        ws[f"{col}16"] = f"={col}12-{col}15"
        ws[f"{col}21"] = f"=MAX(0,{col}4-{col}19)"
        ws[f"{col}22"] = f'=IF({col}20=0,"",{col}12/{col}20)'
        ws[f"{col}23"] = "=Inputs!B28"
        ws[f"{col}24"] = f'=IF({col}22="","NO DEBT SERVICE",IF({col}22<{col}23,"BREACH",IF({col}22<{col}23+Inputs!B58,"WATCH","OK")))'
        ws[f"{col}25"] = f"=1/(1+Inputs!B34)^{col}$2"
        ws[f"{col}26"] = f"=IF(Inputs!B39=1,{col}16*{col}25,{col}12*{col}25)"
        ws[f"{col}31"] = f"=IF(AND({col}$2>=Inputs!B35,{col}$2<=Inputs!B36),1,0)"
        ws[f"{col}27"] = f"=SUMPRODUCT({col}26:$M$26,{col}31:$M$31)"
        ws[f"{col}28"] = f'=IF({col}4=0,"",{col}27/{col}4)'
        ws[f"{col}29"] = f"=SUM({col}26:$M$26)"
        ws[f"{col}30"] = f'=IF({col}4=0,"",{col}29/{col}4)'
        for r in range(4, 32):
            style_cell(ws[f"{col}{r}"], border=styles["border"],
                       font=styles["fonts"]["linked"] if r not in (24,) else styles["fonts"]["body"])
        for r in (4,6,7,8,9,10,11,12,13,14,15,16,18,19,20,21,26,27,29):
            # choose appropriate formats
            if r in (22,23,28,30,17):
                pass
        apply_number_format(ws[f"{col}4"], "eur")
        apply_number_format(ws[f"{col}5"], "pct2")
        apply_number_format(ws[f"{col}6"], "eur")
        apply_number_format(ws[f"{col}7"], "eur")
        apply_number_format(ws[f"{col}8"], "eur")
        apply_number_format(ws[f"{col}9"], "eur")
        apply_number_format(ws[f"{col}10"], "eur")
        apply_number_format(ws[f"{col}11"], "eur")
        apply_number_format(ws[f"{col}12"], "eur")
        apply_number_format(ws[f"{col}13"], "eur")
        apply_number_format(ws[f"{col}14"], "eur")
        apply_number_format(ws[f"{col}15"], "eur")
        apply_number_format(ws[f"{col}16"], "eur")
        apply_number_format(ws[f"{col}17"], "x")
        apply_number_format(ws[f"{col}18"], "eur")
        apply_number_format(ws[f"{col}19"], "eur")
        apply_number_format(ws[f"{col}20"], "eur")
        apply_number_format(ws[f"{col}21"], "eur")
        apply_number_format(ws[f"{col}22"], "x")
        apply_number_format(ws[f"{col}23"], "x")
        apply_number_format(ws[f"{col}25"], "pct2")
        apply_number_format(ws[f"{col}26"], "eur")
        apply_number_format(ws[f"{col}27"], "eur")
        apply_number_format(ws[f"{col}28"], "x")
        apply_number_format(ws[f"{col}29"], "eur")
        apply_number_format(ws[f"{col}30"], "x")

    ws["B32"] = '=IF(M21<=0.01,"OK","REVIEW")'
    ws["B33"] = "=M21"
    ws["B34"] = '=IF(COUNTIF(B24:M24,"BREACH")>0,"BREACH",IF(COUNTIF(B24:M24,"WATCH")>0,"WATCH","OK"))'
    style_cell(ws["B32"], border=styles["border"], font=styles["fonts"]["bold"])
    style_cell(ws["B33"], border=styles["border"], font=styles["fonts"]["linked"])
    style_cell(ws["B34"], border=styles["border"], font=styles["fonts"]["bold"])
    apply_number_format(ws["B33"], "eur")
    ws["N4"] = "Opening op debt = construction closing debt pre-COD"
    ws["N24"] = "WATCH buffer driven by Inputs!B58"
    ws["N32"] = "Key audit"
    set_widths(ws, {1: 28, **{i: 11 for i in range(2,14)}, 14: 32, 15: 14, 16: 14, 17: 12, 18: 22})
    apply_print_setup(ws, "A1:R36")
    return ws


def scenario_summary_sheet(wb, styles):
    ws = wb.create_sheet("Scenario_Summary")
    merge_header(ws, 1, 1, 8, "Scenario Summary - Screening View", styles)
    add_subheader_row(ws, 3, ["Metric", "Base", "Downside", "Upside", "Threshold", "Base Flag", "Downside Flag", "Upside Flag"], styles)
    metrics = [
        ("Revenue Y5", '=Inputs!B15*(1+Inputs!B43)', '=Inputs!B15*(1+Inputs!B44)', '=Inputs!B15*(1+Inputs!B45)', "", "", "", ""),
        ("EBITDA Y5", '=B4*MAX(0,Inputs!B17+Inputs!B46)', '=C4*MAX(0,Inputs!B17+Inputs!B47)', '=D4*MAX(0,Inputs!B17+Inputs!B48)', "", "", "", ""),
        ("Net WC Y5", '=B4*(Inputs!B21+Inputs!B52)', '=C4*(Inputs!B21+Inputs!B53)', '=D4*(Inputs!B21+Inputs!B54)', "", "", "", ""),
        ("Maint. CAPEX Y5", '=B4*(Inputs!B31+Inputs!B55)', '=C4*(Inputs!B31+Inputs!B56)', '=D4*(Inputs!B31+Inputs!B57)', "", "", "", ""),
        ("Approx CFADS Y5", '=B5-B7', '=C5-C7', '=D5-D7', "", "", "", ""),
        ("Approx DSCR Y5", '=IF(Debt_DSCR!F20=0,"",B8/Debt_DSCR!F20)', '=IF(Debt_DSCR!F20=0,"",C8/Debt_DSCR!F20)', '=IF(Debt_DSCR!F20=0,"",D8/Debt_DSCR!F20)', '=Inputs!B28', '=IF(B9="","",IF(B9<E9,"BREACH",IF(B9<E9+Inputs!B58,"WATCH","OK")))', '=IF(C9="","",IF(C9<E9,"BREACH",IF(C9<E9+Inputs!B58,"WATCH","OK")))', '=IF(D9="","",IF(D9<E9,"BREACH",IF(D9<E9+Inputs!B58,"WATCH","OK")))' ),
        ("Approx LLCR proxy", '=IF(Inputs!B8=0,"",B8/Inputs!B8*Inputs!B26)', '=IF(Inputs!B8=0,"",C8/Inputs!B8*Inputs!B26)', '=IF(Inputs!B8=0,"",D8/Inputs!B8*Inputs!B26)', '=Inputs!B59', '=IF(B10<E10,"REVIEW","OK")', '=IF(C10<E10,"REVIEW","OK")', '=IF(D10<E10,"REVIEW","OK")'),
        ("Grant % of Uses", '=Funding_Structure!B9', '=Funding_Structure!B9', '=Funding_Structure!B9', "", "", "", ""),
        ("Sources minus Uses", '=Sources_Uses!B16', '=Sources_Uses!B16', '=Sources_Uses!B16', 0, '=IF(ABS(B12)<=1,"OK","REVIEW")', '=IF(ABS(C12)<=1,"OK","REVIEW")', '=IF(ABS(D12)<=1,"OK","REVIEW")'),
    ]
    r = 4
    for row in metrics:
        for c, val in enumerate(row, start=1):
            ws.cell(r, c, val)
            style_cell(ws.cell(r, c), border=styles["border"], font=styles["fonts"]["body"])
        for c in [2,3,4]:
            apply_number_format(ws.cell(r,c), "eur" if r in (4,5,6,7,8,12) else "x" if r in (9,10) else "pct")
        r += 1
    ws["A14"] = "Note"
    ws["B14"] = "Base / Downside / Upside columns are screening outputs unless the corresponding scenario is active in Inputs!B42."
    ws["B14"].alignment = Alignment(wrap_text=True)
    set_widths(ws, {1: 24, 2: 16, 3: 16, 4: 16, 5: 14, 6: 14, 7: 16, 8: 14})
    apply_print_setup(ws, "A1:H18")
    return ws


def dashboard_sheet(wb, styles):
    ws = wb.create_sheet("Dashboard")
    merge_header(ws, 1, 1, 8, "TITAN GRID - Integrated Dashboard", styles)
    add_subheader_row(ws, 3, ["Metric", "Value", "Status", "Comment"], styles, start_col=1)
    items = [
        ("Total Uses", "=Sources_Uses!B11", "CHECK", "All-in uses"),
        ("Grant", "=Inputs!B61", "CHECK", "Construction source"),
        ("Debt", "=Inputs!B8", "CHECK", "Committed debt"),
        ("Equity", "=Inputs!B9", "CHECK", "Sponsor equity"),
        ("Revenue Y5", "=Inputs!B15", "INFO", "Locked basis"),
        ("EBITDA Y5", "=Revenue_EBITDA!F6", "INFO", "Scenario-aware output"),
        ("Net WC Y5", "=Working_Capital!F6", "CHECK", "Compare to locked ref"),
        ("Plant Effective Capacity", "=Operational_Model!B20", "INFO", "Capacity bottleneck"),
        ("Capacity Headroom / (Shortfall)", "=Operational_Model!B22", "CHECK", "Capacity gap"),
        ("Total Headcount", "=Manpower!E14", "INFO", "Staffing plan"),
        ("Direct HC", "=Manpower!E15", "INFO", "Direct staffing"),
        ("Min DSCR", "=MIN(Debt_DSCR!D22:M22)", "COVENANT", "Primary coverage"),
        ("LLCR Start", "=Debt_DSCR!B28", "COVENANT", "Primary coverage"),
        ("PLCR Start", "=Debt_DSCR!B30", "COVENANT", "Primary coverage"),
        ("Final Debt Balance", "=Debt_DSCR!M21", "CHECK", "Must be 0"),
        ("Sources minus Uses", "=Sources_Uses!B16", "CHECK", "Must be 0"),
    ]
    r = 4
    for metric, formula, status, comment in items:
        ws.cell(r, 1, metric)
        ws.cell(r, 2, formula)
        ws.cell(r, 3, status)
        ws.cell(r, 4, comment)
        for c in range(1, 5):
            style_cell(ws.cell(r, c), border=styles["border"], font=styles["fonts"]["body"])
        # rough formatting
        if metric in ("Total Uses","Grant","Debt","Equity","Revenue Y5","EBITDA Y5","Net WC Y5","Final Debt Balance","Sources minus Uses"):
            apply_number_format(ws.cell(r,2), "eur")
        elif metric in ("Plant Effective Capacity","Capacity Headroom / (Shortfall)","Total Headcount","Direct HC"):
            apply_number_format(ws.cell(r,2), "dec")
        else:
            apply_number_format(ws.cell(r,2), "x")
        r += 1

    # Charts
    bar = BarChart()
    bar.title = "Capacity by Zone"
    bar.y_axis.title = "Units / Year"
    bar.x_axis.title = "Zone"
    data = Reference(wb["Operational_Model"], min_col=2, max_col=2, min_row=13, max_row=19)
    cats = Reference(wb["Operational_Model"], min_col=1, max_col=1, min_row=13, max_row=19)
    bar.add_data(data, titles_from_data=False)
    bar.set_categories(cats)
    bar.height = 7
    bar.width = 14
    ws.add_chart(bar, "F3")

    line = LineChart()
    line.title = "DSCR Profile"
    line.y_axis.title = "x"
    data2 = Reference(wb["Debt_DSCR"], min_col=2, max_col=13, min_row=22, max_row=23)
    cats2 = Reference(wb["Debt_DSCR"], min_col=2, max_col=13, min_row=3, max_row=3)
    line.add_data(data2, titles_from_data=False, from_rows=True)
    line.set_categories(cats2)
    line.height = 7
    line.width = 14
    ws.add_chart(line, "F20")

    set_widths(ws, {1: 28, 2: 16, 3: 12, 4: 22, 5: 4, 6: 14, 7: 14, 8: 14})
    apply_print_setup(ws, "A1:L40")
    return ws


def covenant_dashboard_sheet(wb, styles):
    ws = wb.create_sheet("Covenant_Dashboard")
    merge_header(ws, 1, 1, 10, "Covenant Dashboard", styles)
    # cards
    cards = [
        ("Active Scenario", "=Inputs!B42"),
        ("Min DSCR", "=MIN(Debt_DSCR!D22:M22)"),
        ("Avg DSCR", "=AVERAGE(Debt_DSCR!D22:M22)"),
        ("LLCR Start", "=Debt_DSCR!B28"),
        ("PLCR Start", "=Debt_DSCR!B30"),
        ("Overall Covenant Status", "=Debt_DSCR!B34"),
    ]
    c = 1
    for title, formula in cards:
        ws.merge_cells(start_row=3, start_column=c, end_row=3, end_column=c+1)
        ws.cell(3, c, title)
        style_cell(ws.cell(3,c), font=styles["fonts"]["white_bold"], fill=styles["fills"]["dark_blue"],
                   border=styles["border"], align=Alignment(horizontal="center"))
        ws.merge_cells(start_row=4, start_column=c, end_row=5, end_column=c+1)
        ws.cell(4, c, formula)
        style_cell(ws.cell(4,c), font=Font(size=12, bold=True), fill=styles["fills"]["teal"],
                   border=styles["border"], align=Alignment(horizontal="center", vertical="center"))
        c += 2

    add_subheader_row(ws, 10, ["Year", "DSCR", "Threshold", "Headroom", "Status", "LLCR", "PLCR"], styles)
    for i in range(1, 13):
        r = 10 + i
        col = get_column_letter(i + 1)
        ws.cell(r, 1, i)
        ws.cell(r, 2, f"=Debt_DSCR!{col}22")
        ws.cell(r, 3, f"=Debt_DSCR!{col}23")
        ws.cell(r, 4, f'=IF(OR(B{r}="",C{r}=""),"",B{r}-C{r})')
        ws.cell(r, 5, f"=Debt_DSCR!{col}24")
        ws.cell(r, 6, f"=Debt_DSCR!{col}28")
        ws.cell(r, 7, f"=Debt_DSCR!{col}30")
        for c in range(1, 8):
            style_cell(ws.cell(r, c), border=styles["border"], font=styles["fonts"]["body"])
        apply_number_format(ws.cell(r,2), "x")
        apply_number_format(ws.cell(r,3), "x")
        apply_number_format(ws.cell(r,4), "x")
        apply_number_format(ws.cell(r,6), "x")
        apply_number_format(ws.cell(r,7), "x")

    chart = LineChart()
    chart.title = "DSCR vs Threshold"
    data = Reference(ws, min_col=2, max_col=3, min_row=10, max_row=22)
    cats = Reference(ws, min_col=1, max_col=1, min_row=11, max_row=22)
    chart.add_data(data, titles_from_data=True, from_rows=False)
    chart.set_categories(cats)
    chart.height = 7
    chart.width = 14
    ws.add_chart(chart, "I10")

    set_widths(ws, {1: 8, 2: 12, 3: 12, 4: 12, 5: 16, 6: 12, 7: 12, 9: 16, 10: 16})
    apply_print_setup(ws, "A1:N28")
    return ws



def cc_executive_summary(wb, styles):
    ws = wb.create_sheet("CC_Executive_Summary")
    merge_header(ws, 1, 1, 12, "Credit Committee Executive Summary", styles)

    kpis = [
        ("Total Uses", "=Sources_Uses!B11", "eur", 3, 1),
        ("Grant", "=Sources_Uses!B12", "eur", 3, 4),
        ("Debt", "=Sources_Uses!B13", "eur", 3, 7),
        ("Equity", "=Sources_Uses!B14", "eur", 3, 10),
        ("Revenue Y5", "=Inputs!B15", "eur", 6, 1),
        ("EBITDA Y5", "=Revenue_EBITDA!F6", "eur", 6, 4),
        ("Min DSCR", "=MIN(Debt_DSCR!D22:M22)", "x", 6, 7),
        ("LLCR Start", "=Debt_DSCR!B28", "x", 6, 10),
    ]
    for title, formula, fmt, row, col in kpis:
        ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col+2)
        ws.cell(row, col, title)
        style_cell(ws.cell(row, col), font=styles["fonts"]["white_bold"], fill=styles["fills"]["dark_blue"],
                   border=styles["border"], align=Alignment(horizontal="center"))
        ws.merge_cells(start_row=row+1, start_column=col, end_row=row+2, end_column=col+2)
        ws.cell(row+1, col, formula)
        style_cell(ws.cell(row+1, col), font=Font(size=12, bold=True), fill=styles["fills"]["teal"],
                   border=styles["border"], align=Alignment(horizontal="center", vertical="center"))
        apply_number_format(ws.cell(row+1, col), fmt)

    merge_header(ws, 10, 1, 6, "Project Overview", styles)
    merge_header(ws, 10, 7, 12, "Financing Overview", styles)
    merge_header(ws, 20, 1, 6, "Credit Metrics", styles)
    merge_header(ws, 20, 7, 12, "Audit Summary", styles)

    project = [
        ("Sponsor", "ARS Metal Industries d.o.o."),
        ("Project Type", "Transformer component manufacturing"),
        ("Location", "Tuzi Industrial Zone, Montenegro"),
        ("Construction Period", "=Inputs!B71"),
        ("COD Year", "=Inputs!B80"),
        ("Working Days", "=Inputs!B22"),
        ("Shifts", "=Inputs!B23"),
        ("Target Normalized Capacity", "=Inputs!B24"),
    ]
    finance = [
        ("Total Uses", "=Sources_Uses!B11"),
        ("Grant", "=Sources_Uses!B12"),
        ("Senior Debt", "=Sources_Uses!B13"),
        ("Equity", "=Sources_Uses!B14"),
        ("Grant % of Uses", "=Funding_Structure!B9"),
        ("Debt % of Uses", "=Funding_Structure!B10"),
        ("Equity % of Uses", "=Funding_Structure!B11"),
        ("Sources minus Uses", "=Sources_Uses!B16"),
    ]
    credit = [
        ("Min DSCR", "=MIN(Debt_DSCR!D22:M22)"),
        ("Avg DSCR", "=AVERAGE(Debt_DSCR!D22:M22)"),
        ("LLCR at Start", "=Debt_DSCR!B28"),
        ("PLCR at Start", "=Debt_DSCR!B30"),
        ("Final Debt Balance", "=Debt_DSCR!M21"),
        ("Covenant Status", "=Debt_DSCR!B34"),
    ]
    audits = [
        ("Sources = Uses", '=IF(ABS(Sources_Uses!B16)<=1,"OK","REVIEW")'),
        ("Debt fully repaid", '=IF(Debt_DSCR!M21<=0.01,"OK","REVIEW")'),
        ("No DSCR breach", '=IF(Debt_DSCR!B34="BREACH","REVIEW","OK")'),
        ("Grant within eligible cap", '=IF(Inputs!B61<=SUM(CAPEX_Phasing!B11:M11)*Inputs!B62,"OK","REVIEW")'),
        ("IDC variance acceptable", '=IF(ABS((SUM(Construction_Funding!B12:M12)+SUM(Construction_Funding!B13:M13))-Inputs!B10)<=250000,"OK","REVIEW")'),
    ]

    def write_block(start_row, start_col, items):
        r = start_row
        for label, formula in items:
            ws.cell(r, start_col, label)
            ws.cell(r, start_col + 1, formula)
            style_cell(ws.cell(r, start_col), font=styles["fonts"]["bold"], border=styles["border"], fill=styles["fills"]["light_blue"])
            style_cell(ws.cell(r, start_col + 1), border=styles["border"], font=styles["fonts"]["body"])
            r += 1

    write_block(11, 1, project)
    write_block(11, 7, finance)
    write_block(21, 1, credit)
    write_block(21, 7, audits)

    set_widths(ws, {1: 20, 2: 18, 3: 18, 4: 14, 5: 14, 6: 14, 7: 20, 8: 18, 9: 14, 10: 14, 11: 14, 12: 14})
    apply_print_setup(ws, "A1:L32")
    return ws


def cc_recommendation(wb, styles):
    ws = wb.create_sheet("CC_Recommendation")
    merge_header(ws, 1, 1, 12, "Credit Committee Recommendation", styles)
    merge_header(ws, 3, 1, 12, "Proposed Decision", styles)
    ws["A4"] = '=IF(OR(Debt_DSCR!B34="BREACH",ABS(Sources_Uses!B16)>1),"HOLD / REWORK",IF(AND(MIN(Debt_DSCR!D22:M22)>=Inputs!B28,Debt_DSCR!M21<=0.01),"PROCEED","PROCEED WITH CONDITIONS"))'
    ws["A4"].font = Font(size=14, bold=True, color="1F1F1F")
    ws["A4"].alignment = Alignment(wrap_text=True)

    merge_header(ws, 7, 1, 6, "Conditions Precedent", styles)
    cps = [
        "Confirm grant eligibility and timing.",
        "Validate construction phasing and modeled IDC.",
        "Confirm debt pricing, tenor and covenant package.",
        "Re-test downside case with final contractual debt service schedule.",
        "Lock pipeline and ramp assumptions before lender circulation.",
    ]
    for i, txt in enumerate(cps, start=8):
        ws[f"A{i}"] = f"{i-7}. {txt}"

    merge_header(ws, 7, 7, 12, "Decision Metrics", styles)
    metrics = [
        ("Base Covenant Status", "=Debt_DSCR!B34"),
        ("Sources minus Uses", "=Sources_Uses!B16"),
        ("Final Debt Balance", "=Debt_DSCR!M21"),
        ("Grant Coverage", "=Funding_Structure!B14"),
        ("Active Scenario", "=Inputs!B42"),
    ]
    r = 8
    for label, formula in metrics:
        ws.cell(r, 7, label)
        ws.cell(r, 8, formula)
        style_cell(ws.cell(r, 7), font=styles["fonts"]["bold"], border=styles["border"], fill=styles["fills"]["light_blue"])
        style_cell(ws.cell(r, 8), border=styles["border"])
        r += 1

    merge_header(ws, 15, 1, 12, "Credit Conclusion", styles)
    ws["A16"] = (
        "Recommendation logic is automated for screening and should be read together with the covenant pack, "
        "scenario matrix and funding tie-out. Proceed only if sources and uses are balanced, debt is fully repaid "
        "and no DSCR breach remains in the selected scenario."
    )
    ws["A16"].alignment = Alignment(wrap_text=True)
    set_widths(ws, {1: 34, 2: 4, 3: 4, 4: 4, 5: 4, 6: 4, 7: 22, 8: 18, 9: 4, 10: 4, 11: 4, 12: 4})
    apply_print_setup(ws, "A1:L24")
    return ws


def cc_covenant_pack(wb, styles):
    ws = wb.create_sheet("CC_Covenant_Pack")
    merge_header(ws, 1, 1, 14, "Covenant Pack", styles)

    cards = [
        ("Active Scenario", "=Inputs!B42", 1),
        ("Min DSCR", "=MIN(Debt_DSCR!D22:M22)", 3),
        ("Avg DSCR", "=AVERAGE(Debt_DSCR!D22:M22)", 5),
        ("LLCR Start", "=Debt_DSCR!B28", 7),
        ("PLCR Start", "=Debt_DSCR!B30", 9),
        ("Overall Status", "=Debt_DSCR!B34", 11),
    ]
    for title, formula, col in cards:
        ws.merge_cells(start_row=3, start_column=col, end_row=3, end_column=col+1)
        ws.cell(3, col, title)
        style_cell(ws.cell(3,col), font=styles["fonts"]["white_bold"], fill=styles["fills"]["dark_blue"], border=styles["border"])
        ws.merge_cells(start_row=4, start_column=col, end_row=5, end_column=col+1)
        ws.cell(4, col, formula)
        style_cell(ws.cell(4,col), border=styles["border"], fill=styles["fills"]["teal"],
                   align=Alignment(horizontal="center", vertical="center"), font=Font(size=12, bold=True))

    add_subheader_row(ws, 8, ["Year", "Revenue", "CFADS", "Debt Service", "DSCR", "Threshold", "Headroom", "LLCR", "PLCR", "Status"], styles)
    for i in range(1, 13):
        r = 8 + i
        col = get_column_letter(i + 1)
        vals = [i, f"=Debt_DSCR!{col}7", f"=Debt_DSCR!{col}16", f"=Debt_DSCR!{col}20", f"=Debt_DSCR!{col}22",
                f"=Debt_DSCR!{col}23", f'=IF(OR(E{r}="",F{r}=""),"",E{r}-F{r})', f"=Debt_DSCR!{col}28", f"=Debt_DSCR!{col}30", f"=Debt_DSCR!{col}24"]
        for c, val in enumerate(vals, start=1):
            ws.cell(r, c, val)
            style_cell(ws.cell(r,c), border=styles["border"], font=styles["fonts"]["body"])
        for c in (2,3,4):
            apply_number_format(ws.cell(r,c), "eur")
        for c in (5,6,7,8,9):
            apply_number_format(ws.cell(r,c), "x")

    chart = LineChart()
    chart.title = "DSCR vs Threshold"
    data = Reference(ws, min_col=5, max_col=6, min_row=8, max_row=20)
    cats = Reference(ws, min_col=1, max_col=1, min_row=9, max_row=20)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.height = 7
    chart.width = 13
    ws.add_chart(chart, "L8")

    set_widths(ws, {1: 8, 2: 14, 3: 14, 4: 14, 5: 10, 6: 10, 7: 10, 8: 10, 9: 10, 10: 16, 12: 14, 13: 14, 14: 14})
    apply_print_setup(ws, "A1:N28")
    return ws


def cc_scenario_matrix(wb, styles):
    ws = wb.create_sheet("CC_Scenario_Matrix")
    merge_header(ws, 1, 1, 8, "Scenario Matrix", styles)
    add_subheader_row(ws, 3, ["Metric", "Base", "Downside", "Upside", "Threshold", "Base Flag", "Downside Flag", "Upside Flag"], styles)
    matrix_rows = [
        ("Revenue Y5", '=Scenario_Summary!B4', '=Scenario_Summary!C4', '=Scenario_Summary!D4', "", "", "", ""),
        ("EBITDA Y5", '=Scenario_Summary!B5', '=Scenario_Summary!C5', '=Scenario_Summary!D5', "", "", "", ""),
        ("Net WC Y5", '=Scenario_Summary!B6', '=Scenario_Summary!C6', '=Scenario_Summary!D6', "", "", "", ""),
        ("Approx DSCR Y5", '=Scenario_Summary!B9', '=Scenario_Summary!C9', '=Scenario_Summary!D9', '=Inputs!B28', '=Scenario_Summary!F9', '=Scenario_Summary!G9', '=Scenario_Summary!H9'),
        ("Approx LLCR", '=Scenario_Summary!B10', '=Scenario_Summary!C10', '=Scenario_Summary!D10', '=Inputs!B59', '=Scenario_Summary!F10', '=Scenario_Summary!G10', '=Scenario_Summary!H10'),
        ("Grant % of Uses", '=Scenario_Summary!B11', '=Scenario_Summary!C11', '=Scenario_Summary!D11', "", "", "", ""),
        ("Sources minus Uses", '=Scenario_Summary!B12', '=Scenario_Summary!C12', '=Scenario_Summary!D12', 0, '=Scenario_Summary!F12', '=Scenario_Summary!G12', '=Scenario_Summary!H12'),
    ]
    r = 4
    for row in matrix_rows:
        for c, val in enumerate(row, start=1):
            ws.cell(r, c, val)
            style_cell(ws.cell(r,c), border=styles["border"], font=styles["fonts"]["body"])
        r += 1
    ws["A13"] = "Disclosure"
    ws["B13"] = "Non-active scenarios are screening outputs; activate the scenario in Inputs!B42 for exact debt-engine results."
    ws["B13"].alignment = Alignment(wrap_text=True)
    set_widths(ws, {1: 22, 2: 16, 3: 16, 4: 16, 5: 14, 6: 14, 7: 16, 8: 14})
    apply_print_setup(ws, "A1:H18")
    return ws


def cc_funding_uses(wb, styles):
    ws = wb.create_sheet("CC_Funding_and_Uses")
    merge_header(ws, 1, 1, 11, "Funding and Uses", styles)
    merge_header(ws, 3, 1, 5, "Uses", styles)
    merge_header(ws, 3, 7, 11, "Sources / Grant Eligibility", styles)
    add_subheader_row(ws, 4, ["Item", "Amount", "% of Uses", "", "", "Item", "Amount", "% of Uses", "Eligible CAPEX", "Grant Coverage", "Comment"], styles)
    uses = [
        ("Direct CAPEX", "=Sources_Uses!B4"),
        ("Contingency", "=Sources_Uses!B5"),
        ("Escalation", "=Sources_Uses!B6"),
        ("IDC", "=Sources_Uses!B8"),
        ("Fees", "=Sources_Uses!B9"),
        ("Initial DSRA", "=Sources_Uses!B10"),
        ("Total Uses", "=Sources_Uses!B11"),
    ]
    sources = [
        ("Grant", "=Sources_Uses!B12"),
        ("Debt", "=Sources_Uses!B13"),
        ("Equity", "=Sources_Uses!B14"),
        ("Total Sources", "=Sources_Uses!B15"),
        ("Eligible CAPEX", "=SUM(CAPEX_Phasing!B11:M11)"),
        ("Grant Coverage of Eligible CAPEX", "=Funding_Structure!B14"),
        ("Sources minus Uses", "=Sources_Uses!B16"),
    ]
    for i, (name, formula) in enumerate(uses, start=5):
        ws.cell(i,1,name)
        ws.cell(i,2,formula)
        ws.cell(i,3,f'=IF($B$11=0,0,B{i}/$B$11)')
        for c in range(1,4):
            style_cell(ws.cell(i,c), border=styles["border"], font=styles["fonts"]["body"])
        apply_number_format(ws.cell(i,2), "eur")
        apply_number_format(ws.cell(i,3), "pct")
    for i, (name, formula) in enumerate(sources, start=5):
        ws.cell(i,6,name)
        ws.cell(i,7,formula)
        if i <= 8:
            ws.cell(i,8,f'=IF($B$11=0,0,G{i}/$B$11)')
        for c in range(6,12):
            style_cell(ws.cell(i,c), border=styles["border"], font=styles["fonts"]["body"])
        if i in (9,10,11):
            pass
        apply_number_format(ws.cell(i,7), "eur" if i != 10 else "pct")
        if i <= 8:
            apply_number_format(ws.cell(i,8), "pct")
    ws["I5"] = "=SUM(CAPEX_Phasing!B11:M11)"
    ws["J5"] = "=Funding_Structure!B14"
    ws["K5"] = "Key grant metrics"
    apply_number_format(ws["I5"], "eur")
    apply_number_format(ws["J5"], "pct")
    set_widths(ws, {1: 20, 2: 16, 3: 12, 6: 26, 7: 16, 8: 12, 9: 16, 10: 16, 11: 22})
    apply_print_setup(ws, "A1:K20")
    return ws


def cc_risks(wb, styles):
    ws = wb.create_sheet("CC_Key_Risks_Mitigants")
    merge_header(ws, 1, 1, 6, "Key Risks and Mitigants", styles)
    add_subheader_row(ws, 3, ["Risk Category", "Description", "Impact", "Probability", "Mitigant", "Residual Rating"], styles)
    rows = [
        ("Construction delay", "COD slips by 6 months", "High", "Medium", "Phased procurement, contingency, contractor controls", "Medium"),
        ("Cost overrun", "Base budget exceeded", "High", "Medium", "Contingency and staged drawdown control", "Medium"),
        ("Revenue ramp", "Order intake slower than base case", "High", "Medium", "Diversified market pipeline and phased ramp", "Medium"),
        ("EBITDA compression", "Margins below plan", "High", "Medium", "Pricing discipline and productivity measures", "Medium"),
        ("Working capital expansion", "DSO/inventory exceed base case", "Medium", "Medium", "Cash discipline and supplier terms", "Medium"),
        ("Grant timing", "Grant reimbursement delayed", "Medium", "Medium", "Bridge planning and timing covenant", "Medium"),
        ("Debt disbursement", "Lender conditions delay draw", "Medium", "Low", "Clear CP tracker and lender pre-clearance", "Low"),
        ("Energy / steel cost", "Input cost volatility", "Medium", "Medium", "Hedging / pass-through as feasible", "Medium"),
        ("Covenant breach", "Coverage compression under downside", "High", "Medium", "Sculpted debt, DSRA and grant support", "Medium"),
    ]
    r = 4
    for row in rows:
        for c, val in enumerate(row, start=1):
            ws.cell(r, c, val)
            style_cell(ws.cell(r,c), border=styles["border"], font=styles["fonts"]["body"],
                       align=Alignment(wrap_text=True, vertical="center"))
        r += 1
    set_widths(ws, {1: 20, 2: 34, 3: 10, 4: 12, 5: 36, 6: 14})
    apply_print_setup(ws, "A1:F18")
    return ws


def add_committee_tabs(wb, styles):
    cc_executive_summary(wb, styles)
    cc_recommendation(wb, styles)
    cc_covenant_pack(wb, styles)
    cc_scenario_matrix(wb, styles)
    cc_funding_uses(wb, styles)
    cc_risks(wb, styles)


def create_workbook(output_path: Path):
    wb = Workbook()
    default = wb.active
    wb.remove(default)

    styles = create_styles()

    cover_sheet(wb, styles)
    instructions_sheet(wb, styles)
    add_committee_tabs(wb, styles)
    inputs_sheet(wb, styles)
    sources_uses_sheet(wb, styles)
    capex_phasing_sheet(wb, styles)
    grant_model_sheet(wb, styles)
    construction_funding_sheet(wb, styles)
    funding_structure_sheet(wb, styles)
    grant_eligibility_sheet(wb, styles)
    revenue_ebitda_sheet(wb, styles)
    working_capital_sheet(wb, styles)
    operational_model_sheet(wb, styles)
    manpower_sheet(wb, styles)
    debt_dscr_sheet(wb, styles)
    scenario_summary_sheet(wb, styles)
    dashboard_sheet(wb, styles)
    covenant_dashboard_sheet(wb, styles)

    # Audit / formatting pass
    for ws in wb.worksheets:
        if ws.max_row > 2 and ws.title not in ("Cover",):
            if not ws.print_area:
                apply_print_setup(ws, f"A1:{get_column_letter(min(ws.max_column, 12))}{min(ws.max_row, 40)}")
        if ws.title not in ("Cover",):
            ws.sheet_view.showGridLines = False

    # Print-specific tweaks
    wb["Cover"].freeze_panes = None
    wb["Cover"].sheet_view.showGridLines = False
    wb["Cover"].page_setup.orientation = "portrait"
    wb["Instructions"].page_setup.orientation = "portrait"

    wb.save(output_path)
    return output_path


def prepare_pdf_export_copy(source_xlsx: Path, export_copy_xlsx: Path):
    shutil.copy2(source_xlsx, export_copy_xlsx)


def export_pdf_with_libreoffice(xlsx_path: Path, out_dir: Path):
    ensure_dir(out_dir)
    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(xlsx_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pdf_path = out_dir / (xlsx_path.stem + ".pdf")
    return pdf_path


def write_readme(readme_path: Path):
    readme_path.write_text(
        "TITAN GRID v5.2 Data Room Ready package\n\n"
        "01_Model: editable Excel workbook\n"
        "02_PDF: PDF committee pack exported from Excel\n"
        "03_Exports: export copy used for PDF generation\n"
        "99_Admin: generator script and notes\n"
    )


def zip_folder(folder: Path, zip_path: Path):
    safe_remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in folder.rglob("*"):
            zf.write(file, file.relative_to(folder.parent))


def main():
    base_dir = Path("/mnt/data") / OUTPUT_ROOT_NAME
    safe_remove(base_dir)
    ensure_dir(base_dir)
    model_dir = base_dir / "01_Model"
    pdf_dir = base_dir / "02_PDF"
    export_dir = base_dir / "03_Exports"
    admin_dir = base_dir / "99_Admin"
    for d in (model_dir, pdf_dir, export_dir, admin_dir):
        ensure_dir(d)

    workbook_path = model_dir / WORKBOOK_NAME
    export_copy_path = export_dir / EXPORT_WORKBOOK_NAME
    script_copy_path = admin_dir / "Titan_Grid_v52_OneClick_Generator.py"
    readme_path = admin_dir / "README.txt"

    create_workbook(workbook_path)
    prepare_pdf_export_copy(workbook_path, export_copy_path)
    pdf_path = export_pdf_with_libreoffice(export_copy_path, pdf_dir)
    final_pdf_path = pdf_dir / PDF_NAME
    if pdf_path != final_pdf_path:
        if final_pdf_path.exists():
            final_pdf_path.unlink()
        pdf_path.rename(final_pdf_path)
        pdf_path = final_pdf_path

    # Copy this script for one-click reuse
    shutil.copy2(Path(__file__), script_copy_path)
    write_readme(readme_path)

    zip_folder(base_dir, Path("/mnt/data") / ZIP_NAME)

    print(f"Workbook: {workbook_path}")
    print(f"PDF: {pdf_path}")
    print(f"Data room folder: {base_dir}")
    print(f"ZIP: {Path('/mnt/data') / ZIP_NAME}")


if __name__ == "__main__":
    main()
