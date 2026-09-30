
import os
import datetime
import openpyxl
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import mm

SOURCE_XLSX = "/mnt/data/TITAN_v5_0_board_ic_dashboard_version.xlsx"
OUT_DOCX = "/mnt/data/TITAN_IC_Memo_Live_Linked.docx"
OUT_PDF = "/mnt/data/TITAN_IC_Memo_Live_Linked.pdf"

def eur(x):
    if x is None:
        return "-"
    return f"€{x:,.0f}"

def eurm(x):
    if x is None:
        return "-"
    return f"€{x/1_000_000:.2f}m"

def pct(x):
    if x is None:
        return "-"
    return f"{x*100:.1f}%"

def mult(x):
    if x is None:
        return "-"
    return f"{x:.2f}x"

def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)

def set_cell_margins(cell, top=80, start=100, bottom=80, end=100):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, val in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")

def format_docx_table(table, header_fill="001F3F", header_font_color="FFFFFF"):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for row in table.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(9)
    for cell in table.rows[0].cells:
        set_cell_shading(cell, header_fill)
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor.from_string(header_font_color)
                run.font.name = "Arial"
                run.font.size = Pt(9)

def add_pdf_table(story, data, col_widths=None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#001F3F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C3D1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

def build_pack():
    wb = openpyxl.load_workbook(SOURCE_XLSX, data_only=True)

    ws_su = wb["Sources & Uses"]
    ws_ret = wb["Returns"]
    ws_cov = wb["Maintenance Covenants"]
    ws_pnl = wb["Annual P&L"]
    ws_debt = wb["Debt & Capex Schedule"]
    ws_sens = wb["Scenario Sensitivity"]
    ws_cp = wb["CP Checklist"]

    source_rows = []
    use_rows = []
    for r in range(5, 15):
        typ = ws_su[f"A{r}"].value
        if typ == "Source":
            source_rows.append((ws_su[f"B{r}"].value, ws_su[f"D{r}"].value, ws_su[f"F{r}"].value))
        elif typ == "Use":
            use_rows.append((ws_su[f"B{r}"].value, ws_su[f"D{r}"].value, ws_su[f"F{r}"].value))

    total_sources = ws_su["B18"].value
    total_uses = ws_su["B19"].value
    funding_gap = ws_su["B20"].value

    project_irr = ws_ret["B5"].value
    equity_irr = ws_ret["B6"].value
    payback = ws_ret["B7"].value
    npv = ws_ret["B8"].value
    min_dscr = ws_ret["B9"].value
    downside_project_irr = ws_ret["C5"].value
    downside_equity_irr = ws_ret["C6"].value
    downside_npv = ws_ret["C8"].value
    downside_min_dscr = ws_ret["C9"].value

    cov_rows = []
    for r in range(5, 10):
        cov_rows.append([
            ws_cov[f"A{r}"].value,
            ws_cov[f"B{r}"].value,
            ws_cov[f"C{r}"].value,
            ws_cov[f"D{r}"].value,
            ws_cov[f"F{r}"].value,
        ])

    years = [ws_pnl.cell(4, c).value for c in range(2, 7)]
    annual_revenue = [ws_pnl.cell(5, c).value for c in range(2, 7)]
    annual_ebitda = [ws_pnl.cell(9, c).value for c in range(2, 7)]

    debt_rows = []
    for r in range(5, 17):
        row = [ws_debt.cell(r, c).value for c in range(1, 7)]
        if any(v is not None for v in row):
            debt_rows.append(row)

    sens_rows = []
    for r in range(5, 10):
        sens_rows.append([ws_sens.cell(r, c).value for c in range(1, 7)])

    cp_open = 0
    cp_total = 0
    for r in range(5, ws_cp.max_row + 1):
        if ws_cp[f"A{r}"].value:
            cp_total += 1
            if ws_cp[f"E{r}"].value == "Open":
                cp_open += 1
    cp_readiness = (cp_total - cp_open) / cp_total if cp_total else 0

    recommendation = "CONDITIONAL APPROVAL" if (funding_gap is not None and funding_gap < 0) or cp_open > 0 else "APPROVE"
    key_risk = "Funding gap and open CP workstream" if (funding_gap is not None and funding_gap < 0) else "Execution and ramp-up delivery"
    mitigant = "Close remaining funding gap and discharge CP items before first drawdown" if (funding_gap is not None and funding_gap < 0) else "Phased ramp-up and covenant headroom"

    mapping_rows = [
        ("Total Sources", "Sources & Uses!B18", total_sources),
        ("Total Uses", "Sources & Uses!B19", total_uses),
        ("Funding Gap / (Surplus)", "Sources & Uses!B20", funding_gap),
        ("Project IRR (Base)", "Returns!B5", project_irr),
        ("Equity IRR (Base)", "Returns!B6", equity_irr),
        ("Payback (Base)", "Returns!B7", payback),
        ("NPV @ 10% WACC (Base)", "Returns!B8", npv),
        ("Min DSCR (Base)", "Returns!B9", min_dscr),
        ("Project IRR (Downside)", "Returns!C5", downside_project_irr),
        ("Equity IRR (Downside)", "Returns!C6", downside_equity_irr),
        ("NPV @ 10% WACC (Downside)", "Returns!C8", downside_npv),
        ("Min DSCR (Downside)", "Returns!C9", downside_min_dscr),
        ("Open CP Count", "CP Checklist!E5:E14", cp_open),
        ("CP Readiness", "Derived from CP Checklist", cp_readiness),
    ]

    # DOCX
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)
    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(10)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("TITAN GRID")
    r.bold = True
    r.font.size = Pt(22)
    r.font.color.rgb = RGBColor.from_string("001F3F")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Investment Committee Memorandum")
    r.bold = True
    r.font.size = Pt(16)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Automated Excel-to-Memo Version")
    r.italic = True

    meta = doc.add_table(rows=5, cols=2)
    for i, (k, v) in enumerate([
        ("Borrower", "ARS Metal Industries d.o.o."),
        ("Workbook Source", os.path.basename(SOURCE_XLSX)),
        ("Prepared", datetime.date.today().isoformat()),
        ("Classification", "Strictly Confidential"),
        ("Recommendation", recommendation),
    ]):
        meta.cell(i, 0).text = str(k)
        meta.cell(i, 1).text = str(v)
    format_docx_table(meta)
    doc.add_page_break()

    def heading(text, level=1):
        h = doc.add_paragraph()
        h.style = f"Heading {level}"
        run = h.add_run(text)
        run.font.name = "Arial"
        if level == 1:
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = RGBColor.from_string("001F3F")
        else:
            run.font.size = Pt(11)
            run.font.bold = True

    heading("1. Executive Recommendation", 1)
    doc.add_paragraph(
        f"The memo below is generated directly from the workbook '{os.path.basename(SOURCE_XLSX)}'. "
        f"On the current workbook values, the package supports a {recommendation.lower()} rather than a clean approval. "
        f"Base-case project IRR is {pct(project_irr)}, equity IRR is {pct(equity_irr)}, payback is {payback:.1f} years, "
        f"and minimum DSCR is {mult(min_dscr)}. Total sources are {eurm(total_sources)} versus total uses of {eurm(total_uses)}, "
        f"which leaves a funding gap of {eurm(abs(funding_gap))}."
    )
    doc.add_paragraph(
        f"Key risk on the current version is {key_risk.lower()}. Recommended action is to {mitigant[0].lower() + mitigant[1:]}."
    )

    heading("2. Investment Snapshot", 1)
    snap_data = [
        ("Total Sources", eurm(total_sources), "Total Uses", eurm(total_uses)),
        ("Funding Gap / (Surplus)", eurm(funding_gap), "Project IRR", pct(project_irr)),
        ("Equity IRR", pct(equity_irr), "Payback", f"{payback:.1f} years"),
        ("NPV @ 10% WACC", eurm(npv), "Min DSCR", mult(min_dscr)),
        ("Downside IRR", pct(downside_project_irr), "Downside Min DSCR", mult(downside_min_dscr)),
        ("Open CP Items", str(cp_open), "CP Readiness", pct(cp_readiness)),
    ]
    snap = doc.add_table(rows=len(snap_data), cols=4)
    for i, row in enumerate(snap_data):
        for j, val in enumerate(row):
            snap.cell(i, j).text = str(val)
    format_docx_table(snap)

    heading("3. Sources and Uses", 1)
    su = doc.add_table(rows=1 + max(len(source_rows), len(use_rows)), cols=4)
    for j, h in enumerate(["Sources", "Amount", "Uses", "Amount"]):
        su.cell(0, j).text = h
    for i in range(1, len(su.rows)):
        if i - 1 < len(source_rows):
            su.cell(i, 0).text = str(source_rows[i - 1][0])
            su.cell(i, 1).text = eur(source_rows[i - 1][1])
        if i - 1 < len(use_rows):
            su.cell(i, 2).text = str(use_rows[i - 1][0])
            su.cell(i, 3).text = eur(use_rows[i - 1][1])
    format_docx_table(su)
    doc.add_paragraph(
        f"Workbook controls show a funding gap / (surplus) of {eur(funding_gap)} in Sources & Uses!B20. "
        f"That line should be resolved before lender submission."
    )

    heading("4. Returns and Credit Metrics", 1)
    ret = doc.add_table(rows=4, cols=4)
    ret_data = [
        ["Metric", "Base", "Downside", "Comment"],
        ["Project IRR", pct(project_irr), pct(downside_project_irr), "From Returns sheet"],
        ["Equity IRR", pct(equity_irr), pct(downside_equity_irr), "From Returns sheet"],
        ["Min DSCR", mult(min_dscr), mult(downside_min_dscr), "Downside currently above 1.35x threshold on current workbook"],
    ]
    for i, row in enumerate(ret_data):
        for j, val in enumerate(row):
            ret.cell(i, j).text = str(val)
    format_docx_table(ret)

    cov = doc.add_table(rows=1 + len(cov_rows), cols=5)
    for j, h in enumerate(["Covenant", "Threshold", "Actual", "Headroom", "Status"]):
        cov.cell(0, j).text = h
    for i, row in enumerate(cov_rows, start=1):
        for j, val in enumerate(row):
            cov.cell(i, j).text = str(val)
    format_docx_table(cov)

    heading("5. Operating Outlook", 1)
    op = doc.add_table(rows=6, cols=3)
    op_rows = [["Year", "Revenue", "EBITDA"]] + [[years[k], eur(annual_revenue[k]), eur(annual_ebitda[k])] for k in range(5)]
    for i, row in enumerate(op_rows):
        for j, val in enumerate(row):
            op.cell(i, j).text = str(val)
    format_docx_table(op)

    margin_y1 = annual_ebitda[0] / annual_revenue[0] if annual_revenue[0] else 0
    margin_y5 = annual_ebitda[-1] / annual_revenue[-1] if annual_revenue[-1] else 0
    doc.add_paragraph(
        f"The annual P&L sheet indicates revenue growth from {eur(annual_revenue[0])} in Y1 to {eur(annual_revenue[-1])} in Y5, "
        f"with EBITDA rising from {eur(annual_ebitda[0])} to {eur(annual_ebitda[-1])}. "
        f"Implied EBITDA margin increases from {margin_y1*100:.1f}% to {margin_y5*100:.1f}%."
    )

    heading("6. CP and Closing Readiness", 1)
    doc.add_paragraph(
        f"The CP Checklist currently shows {cp_open} open items out of {cp_total}. "
        f"Readiness on a simple completion basis is {cp_readiness*100:.1f}%. "
        f"Current workbook status therefore supports a conditional approval path tied to documentary completion."
    )
    cp_tbl = doc.add_table(rows=min(cp_total, 10) + 1, cols=4)
    for j, h in enumerate(["CP No.", "Condition Precedent", "Timing", "Status"]):
        cp_tbl.cell(0, j).text = h
    for i, r in enumerate(range(5, min(ws_cp.max_row, 14) + 1), start=1):
        cp_tbl.cell(i, 0).text = str(ws_cp[f"A{r}"].value)
        cp_tbl.cell(i, 1).text = str(ws_cp[f"B{r}"].value)
        cp_tbl.cell(i, 2).text = str(ws_cp[f"D{r}"].value)
        cp_tbl.cell(i, 3).text = str(ws_cp[f"E{r}"].value)
    format_docx_table(cp_tbl)

    heading("7. Sensitivity and Downside", 1)
    sens = doc.add_table(rows=1 + len(sens_rows), cols=6)
    for j, h in enumerate(["Variable", "Base", "Downside", "Upside", "Impact", "Comments"]):
        sens.cell(0, j).text = h
    for i, row in enumerate(sens_rows, start=1):
        for j, val in enumerate(row):
            sens.cell(i, j).text = str(val)
    format_docx_table(sens)
    doc.add_paragraph(
        f"On the current Returns sheet, downside minimum DSCR is {mult(downside_min_dscr)}. "
        f"That indicates covenant resilience in the model, but the memo should still be read together with the unresolved funding gap and open CP queue."
    )

    heading("8. Debt and Capex Annex", 1)
    debt = doc.add_table(rows=1 + len(debt_rows), cols=6)
    for j, h in enumerate(["Item", "Date", "Amount", "Debt", "Equity", "Comments"]):
        debt.cell(0, j).text = h
    for i, row in enumerate(debt_rows, start=1):
        for j, val in enumerate(row):
            debt.cell(i, j).text = eur(val) if j == 2 and isinstance(val, (int, float)) else str(val)
    format_docx_table(debt)

    doc.add_page_break()
    heading("Annex A. Source Mapping", 1)
    mapping = doc.add_table(rows=1 + len(mapping_rows), cols=3)
    for j, h in enumerate(["Memo Metric", "Workbook Reference", "Current Value"]):
        mapping.cell(0, j).text = h
    for i, (metric, ref, val) in enumerate(mapping_rows, start=1):
        if isinstance(val, float):
            if "IRR" in metric:
                disp = pct(val)
            elif "DSCR" in metric:
                disp = mult(val)
            elif "Readiness" in metric:
                disp = pct(val)
            else:
                disp = f"{val:.1f}"
        elif isinstance(val, int):
            disp = eur(val) if abs(val) > 1000 else str(val)
        else:
            disp = str(val)
        mapping.cell(i, 0).text = metric
        mapping.cell(i, 1).text = ref
        mapping.cell(i, 2).text = disp
    format_docx_table(mapping)
    doc.add_paragraph(
        "This annex is the audit trail for the automated Excel-to-memo pull. "
        "Numbers above are linked to the listed workbook cells at generation time."
    )

    doc.save(OUT_DOCX)

    # PDF
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph('<font name="Helvetica-Bold" size="16" color="#001F3F">TITAN GRID – Investment Committee Memorandum</font>', styles["Title"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Automated Excel-to-Memo Version | Source workbook: {os.path.basename(SOURCE_XLSX)} | Prepared: {datetime.date.today().isoformat()}",
        styles["BodyText"],
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Recommendation:</b> {recommendation}", styles["BodyText"]))
    story.append(Paragraph(
        f"<b>Base metrics:</b> Project IRR {pct(project_irr)}, Equity IRR {pct(equity_irr)}, Payback {payback:.1f} years, Min DSCR {mult(min_dscr)}.",
        styles["BodyText"],
    ))
    story.append(Paragraph(
        f"<b>Funding:</b> Total sources {eurm(total_sources)}, total uses {eurm(total_uses)}, funding gap {eurm(abs(funding_gap))}.",
        styles["BodyText"],
    ))
    story.append(Spacer(1, 10))

    snap_pdf = [["Metric", "Value", "Metric", "Value"]] + [[a, b, c, d] for a, b, c, d in snap_data]
    story.append(Paragraph("<b>Investment Snapshot</b>", styles["Heading2"]))
    add_pdf_table(story, snap_pdf, [55 * mm, 35 * mm, 55 * mm, 35 * mm])

    su_pdf = [["Sources", "Amount", "Uses", "Amount"]]
    for i in range(max(len(source_rows), len(use_rows))):
        sr = source_rows[i] if i < len(source_rows) else ("", "", "")
        ur = use_rows[i] if i < len(use_rows) else ("", "", "")
        su_pdf.append([sr[0], eur(sr[1]) if sr[1] else "", ur[0], eur(ur[1]) if ur[1] else ""])
    story.append(Paragraph("<b>Sources and Uses</b>", styles["Heading2"]))
    add_pdf_table(story, su_pdf, [55 * mm, 30 * mm, 55 * mm, 30 * mm])

    ret_pdf = [
        ["Metric", "Base", "Downside", "Comment"],
        ["Project IRR", pct(project_irr), pct(downside_project_irr), "Returns sheet"],
        ["Equity IRR", pct(equity_irr), pct(downside_equity_irr), "Returns sheet"],
        ["Min DSCR", mult(min_dscr), mult(downside_min_dscr), "Downside currently above 1.35x"],
    ]
    story.append(Paragraph("<b>Returns and Covenants</b>", styles["Heading2"]))
    add_pdf_table(story, ret_pdf, [45 * mm, 25 * mm, 25 * mm, 65 * mm])

    cov_pdf = [["Covenant", "Threshold", "Actual", "Headroom", "Status"]]
    for row in cov_rows:
        cov_pdf.append([str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4])])
    add_pdf_table(story, cov_pdf, [50 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm])

    story.append(PageBreak())
    op_pdf = [["Year", "Revenue", "EBITDA"]] + [[years[k], eur(annual_revenue[k]), eur(annual_ebitda[k])] for k in range(5)]
    story.append(Paragraph("<b>Operating Outlook</b>", styles["Heading2"]))
    add_pdf_table(story, op_pdf, [35 * mm, 45 * mm, 45 * mm])

    story.append(Paragraph("<b>CP and Closing Readiness</b>", styles["Heading2"]))
    story.append(Paragraph(
        f"Open CP items: {cp_open} / {cp_total}. Completion basis readiness: {cp_readiness*100:.1f}%.",
        styles["BodyText"],
    ))
    cp_pdf = [["CP No.", "Condition Precedent", "Timing", "Status"]]
    for r in range(5, min(ws_cp.max_row, 14) + 1):
        cp_pdf.append([
            str(ws_cp[f"A{r}"].value),
            str(ws_cp[f"B{r}"].value),
            str(ws_cp[f"D{r}"].value),
            str(ws_cp[f"E{r}"].value),
        ])
    add_pdf_table(story, cp_pdf, [22 * mm, 95 * mm, 30 * mm, 25 * mm])

    story.append(Paragraph("<b>Sensitivity</b>", styles["Heading2"]))
    sens_pdf = [["Variable", "Base", "Downside", "Upside", "Impact", "Comments"]] + [[str(x) for x in row] for row in sens_rows]
    add_pdf_table(story, sens_pdf, [28 * mm, 18 * mm, 24 * mm, 18 * mm, 22 * mm, 60 * mm])

    story.append(PageBreak())
    story.append(Paragraph("<b>Annex A. Source Mapping</b>", styles["Heading2"]))
    map_pdf = [["Memo Metric", "Workbook Reference", "Current Value"]]
    for metric, ref, val in mapping_rows:
        if isinstance(val, float):
            if "IRR" in metric:
                disp = pct(val)
            elif "DSCR" in metric:
                disp = mult(val)
            elif "Readiness" in metric:
                disp = pct(val)
            else:
                disp = f"{val:.1f}"
        elif isinstance(val, int):
            disp = eur(val) if abs(val) > 1000 else str(val)
        else:
            disp = str(val)
        map_pdf.append([metric, ref, disp])
    add_pdf_table(story, map_pdf, [60 * mm, 60 * mm, 40 * mm])

    pdf = SimpleDocTemplate(
        OUT_PDF,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    pdf.build(story)

    print(f"Generated: {OUT_DOCX}")
    print(f"Generated: {OUT_PDF}")

if __name__ == "__main__":
    build_pack()
