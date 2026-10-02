from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.chart import BarChart, DoughnutChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.utils import get_column_letter
import os

SRC = "/mnt/data/TITAN_v5_0_dashboard_version.xlsx"
OUT = "/mnt/data/TITAN_v5_0_board_ic_dashboard_version.xlsx"

wb = load_workbook(SRC)
if 'Board & IC Dashboard' in wb.sheetnames:
    del wb['Board & IC Dashboard']
ws = wb.create_sheet('Board & IC Dashboard', 2)
ws.sheet_view.showGridLines = False
ws.freeze_panes = 'A7'

# ---------------------- Theme ----------------------
NAVY = '0B1F3A'
BLUE = '173F73'
TEAL = '177E89'
LIGHT = 'EEF3F8'
MID = 'D9E3F0'
GREEN = 'E8F3EC'
GREEN_TX = '207245'
RED = 'F8E7E7'
RED_TX = '9C2F2F'
AMBER = 'FFF4D6'
AMBER_TX = '9C6B00'
WHITE = 'FFFFFF'
TEXT = '1F2937'
MUTED = '6B7280'
BORDER = 'CBD5E1'

thin = Side(style='thin', color=BORDER)
medium = Side(style='medium', color=NAVY)
box_border = Border(left=thin, right=thin, top=thin, bottom=thin)
section_border = Border(left=thin, right=thin, top=medium, bottom=thin)

fill_navy = PatternFill('solid', fgColor=NAVY)
fill_blue = PatternFill('solid', fgColor=BLUE)
fill_teal = PatternFill('solid', fgColor=TEAL)
fill_light = PatternFill('solid', fgColor=LIGHT)
fill_mid = PatternFill('solid', fgColor=MID)
fill_green = PatternFill('solid', fgColor=GREEN)
fill_red = PatternFill('solid', fgColor=RED)
fill_amber = PatternFill('solid', fgColor=AMBER)

font_title = Font(name='Calibri', size=20, bold=True, color=WHITE)
font_subtitle = Font(name='Calibri', size=10, color=TEXT)
font_section = Font(name='Calibri', size=11, bold=True, color=WHITE)
font_kpi_label = Font(name='Calibri', size=9, bold=True, color=MUTED)
font_kpi_value = Font(name='Calibri', size=18, bold=True, color=BLUE)
font_body = Font(name='Calibri', size=10, color=TEXT)
font_small = Font(name='Calibri', size=9, color=TEXT)
font_white = Font(name='Calibri', size=10, bold=True, color=WHITE)
font_white_big = Font(name='Calibri', size=11, bold=True, color=WHITE)
font_green = Font(name='Calibri', size=10, bold=True, color=GREEN_TX)
font_red = Font(name='Calibri', size=10, bold=True, color=RED_TX)
font_amber = Font(name='Calibri', size=10, bold=True, color=AMBER_TX)
font_link = Font(name='Calibri', size=9, underline='single', color='0563C1')

center = Alignment(horizontal='center', vertical='center', wrap_text=True)
left = Alignment(horizontal='left', vertical='center', wrap_text=True)
right = Alignment(horizontal='right', vertical='center', wrap_text=True)

# ---------------------- Layout ----------------------
for c, w in {
    'A': 16, 'B': 16, 'C': 16, 'D': 16, 'E': 16, 'F': 16, 'G': 16, 'H': 16,
    'I': 16, 'J': 16, 'K': 14, 'L': 14, 'M': 14, 'N': 14, 'O': 16
}.items():
    ws.column_dimensions[c].width = w

for r, h in {
    1: 24, 2: 24, 3: 20, 4: 22, 5: 22, 6: 20, 7: 20, 8: 28, 9: 16, 10: 16,
    12: 20, 13: 24, 14: 24, 15: 24, 16: 24, 17: 24, 18: 24,
    20: 20, 36: 20, 46: 20
}.items():
    ws.row_dimensions[r].height = h

for r in range(1, 60):
    for c in range(1, 16):
        ws.cell(r, c).border = box_border
        ws.cell(r, c).alignment = left

# ---------------------- Title ----------------------
ws.merge_cells('A1:O2')
ws['A1'] = 'TITAN v5.0 | Board & IC Dashboard'
ws['A1'].font = font_title
ws['A1'].fill = fill_navy
ws['A1'].alignment = Alignment(horizontal='left', vertical='center')
for row in ws['A1:O2']:
    for cell in row:
        cell.fill = fill_navy
        cell.border = section_border

ws.merge_cells('A3:O3')
ws['A3'] = 'Presentation-style summary for board and investment committee review: headline metrics, downside view, decision framing and closing path.'
ws['A3'].font = font_subtitle
ws['A3'].fill = fill_light
ws['A3'].alignment = left

# ---------------------- Ribbon ----------------------
blocks = [
    ('A4:C5', 'Version', 'v5.0-board-ic', fill_mid, BLUE),
    ('D4:F5', 'Prepared Date', '2026-03-28', fill_mid, BLUE),
    ('G4:I5', 'Recommendation', 'Proceed subject to DD / CP closure', fill_teal, WHITE),
    ('J4:L5', 'Primary View', 'Board / IC', fill_mid, BLUE),
    ('M4:O5', 'Quick Link', 'Go to Committee Summary', fill_mid, BLUE),
]
for rng, label, value, fill, color in blocks:
    ws.merge_cells(rng)
    c = ws[rng.split(':')[0]]
    c.value = f'{label}\n{value}'
    c.fill = fill
    c.font = Font(name='Calibri', size=10, bold=True, color=color)
    c.alignment = center
    # color merged block
    start_col = ws[rng.split(':')[0]].column
    start_row = ws[rng.split(':')[0]].row
    end_col = ws[rng.split(':')[1]].column
    end_row = ws[rng.split(':')[1]].row
    for rr in range(start_row, end_row + 1):
        for cc in range(start_col, end_col + 1):
            ws.cell(rr, cc).fill = fill
            ws.cell(rr, cc).border = box_border

ws['M4'].hyperlink = "#'Committee Summary'!A1"

# ---------------------- Section helper ----------------------
def section_header(row, text):
    ws.merge_cells(f'A{row}:O{row}')
    ws[f'A{row}'] = text
    ws[f'A{row}'].fill = fill_teal
    ws[f'A{row}'].font = font_section
    ws[f'A{row}'].alignment = left
    for cell in ws[row]:
        cell.fill = fill_teal
        cell.border = section_border

# ---------------------- KPI Cards ----------------------
section_header(6, 'Investment committee snapshot')

card_specs = [
    ('A7:C10', 'Total Sources (€m)', "='Dashboard Data'!X1", 'Indicative financing stack', 'currency'),
    ('D7:F10', 'Project IRR', "='Dashboard Data'!X7", 'Base case project return', 'pct'),
    ('G7:I10', 'Equity IRR', "='Dashboard Data'!X8", 'Base case sponsor return', 'pct'),
    ('J7:L10', 'Min DSCR', "='Dashboard Data'!X6", 'Lender protection metric', 'multiple'),
    ('M7:O10', 'Debt Share', "='Dashboard Data'!X4", 'Senior debt as % of sources', 'pct'),
]
for rng, label, formula, subtitle, fmt in card_specs:
    tl, br = rng.split(':')
    sc, sr = ws[tl].column, ws[tl].row
    ec, er = ws[br].column, ws[br].row
    # card background
    for rr in range(sr, er + 1):
        for cc in range(sc, ec + 1):
            ws.cell(rr, cc).fill = fill_light
            ws.cell(rr, cc).border = box_border
    ws.merge_cells(f'{get_column_letter(sc)}{sr}:{get_column_letter(ec)}{sr}')
    ws.cell(sr, sc).value = label
    ws.cell(sr, sc).font = font_kpi_label
    ws.cell(sr, sc).alignment = center

    val_row = sr + 1
    ws.merge_cells(f'{get_column_letter(sc)}{val_row}:{get_column_letter(ec)}{val_row+1}')
    val_cell = ws.cell(val_row, sc)
    val_cell.value = formula
    val_cell.font = font_kpi_value
    val_cell.alignment = center
    if fmt == 'currency':
        val_cell.number_format = '€0.0'
    elif fmt == 'pct':
        val_cell.number_format = '0.0%'
    elif fmt == 'multiple':
        val_cell.number_format = '0.00x'

    sub_row = er
    ws.merge_cells(f'{get_column_letter(sc)}{sub_row}:{get_column_letter(ec)}{sub_row}')
    ws.cell(sub_row, sc).value = subtitle
    ws.cell(sub_row, sc).font = font_small
    ws.cell(sub_row, sc).alignment = center

# ---------------------- Narrative panels ----------------------
section_header(12, 'Decision framing')

# Investment case panel
for r in range(13, 19):
    for c in range(1, 7):
        ws.cell(r, c).fill = fill_light
for c in range(1, 7):
    ws.cell(13, c).fill = fill_blue
ws.merge_cells('A13:F13')
ws['A13'] = 'Investment case at a glance'
ws['A13'].font = font_white_big
ws['A13'].alignment = left
bullets = [
    'Near-shoring positioning supports strategic relevance and delivery responsiveness.',
    'Industrial capex is visible and security package can be tied to tangible assets.',
    'Base case economics remain strong: project IRR and equity IRR materially above hurdle rates.',
    'Debt structure benefits from covenant cushion, reserve mechanics and sponsor support concept.',
    'Primary execution focus remains document readiness, diligence closure and funding gap resolution.',
]
for i, text in enumerate(bullets, start=14):
    ws.merge_cells(f'A{i}:F{i}')
    ws[f'A{i}'] = '• ' + text
    ws[f'A{i}'].font = font_body
    ws[f'A{i}'].alignment = left
    ws[f'A{i}'].fill = fill_light

# Recommendation panel
for r in range(13, 19):
    for c in range(7, 11):
        ws.cell(r, c).fill = fill_green
ws.merge_cells('G13:J13')
ws['G13'] = 'IC recommendation'
ws['G13'].font = Font(name='Calibri', size=11, bold=True, color=GREEN_TX)
ws['G13'].alignment = left
recos = {
    'G14:J14': 'Proceed to diligence-backed negotiation and closing workstream.',
    'G15:J15': 'Condition 1: lock funding gap treatment and updated sources plan.',
    'G16:J16': 'Condition 2: close CP package, model acceptance and core diligence items.',
    'G17:J17': 'Condition 3: complete security perfection path and documentary readiness.',
    'G18:J18': 'Committee stance: supportive, but not yet ready for unconditional approval.',
}
for rng, txt in recos.items():
    ws.merge_cells(rng)
    ws[rng.split(':')[0]] = txt
    ws[rng.split(':')[0]].font = font_body
    ws[rng.split(':')[0]].alignment = left
    ws[rng.split(':')[0]].fill = fill_green

# Downside summary table
for r in range(13, 19):
    for c in range(11, 16):
        ws.cell(r, c).fill = fill_light
ws.merge_cells('K13:O13')
ws['K13'] = 'Base vs downside'
ws['K13'].font = font_white_big
ws['K13'].fill = fill_blue
ws['K13'].alignment = left
headers = ['Scenario', 'Project IRR', 'Equity IRR', 'NPV (€m)', 'Min DSCR']
for idx, h in enumerate(headers, start=11):
    cell = ws.cell(14, idx)
    cell.value = h
    cell.font = font_white
    cell.fill = fill_navy
    cell.alignment = center
scenarios = [
    ('Base', "='Returns'!B5", "='Returns'!B6", "='Returns'!B8/1000000", "='Returns'!B9"),
    ('Downside', "='Returns'!C5", "='Returns'!C6", "='Returns'!C8/1000000", "='Returns'!C9"),
    ('Severe Downside', "='Returns'!D5", "='Returns'!D6", "='Returns'!D8/1000000", "='Returns'!D9"),
]
for row_idx, row in enumerate(scenarios, start=15):
    for col_idx, val in enumerate(row, start=11):
        cell = ws.cell(row_idx, col_idx)
        cell.value = val
        cell.alignment = center
        cell.font = font_body
        cell.fill = fill_light
        if col_idx in [12, 13]:
            cell.number_format = '0.0%'
        elif col_idx == 14:
            cell.number_format = '€0.0'
        elif col_idx == 15:
            cell.number_format = '0.00x'
for c in range(11, 16):
    ws.cell(18, c).fill = fill_light

# ---------------------- Charts ----------------------
section_header(20, 'Headline visuals')

# Left chart background
for r in range(21, 35):
    for c in range(1, 9):
        ws.cell(r, c).fill = fill_light
# Right chart background
for r in range(21, 35):
    for c in range(9, 16):
        ws.cell(r, c).fill = fill_light

ws.merge_cells('A21:H21')
ws['A21'] = 'Scale-up economics'
ws['A21'].fill = fill_blue
ws['A21'].font = font_white_big
ws['A21'].alignment = left

ws.merge_cells('I21:O21')
ws['I21'] = 'Capital structure'
ws['I21'].fill = fill_blue
ws['I21'].font = font_white_big
ws['I21'].alignment = left

# Bar chart Revenue vs EBITDA
bar = BarChart()
bar.type = 'col'
bar.style = 10
bar.title = 'Annual Revenue vs EBITDA'
bar.y_axis.title = '€m'
bar.x_axis.title = 'Year'
bar.height = 7.5
bar.width = 12
cats = Reference(wb['Dashboard Data'], min_col=1, min_row=2, max_row=6)
data = Reference(wb['Dashboard Data'], min_col=2, min_row=1, max_col=3, max_row=6)
bar.add_data(data, titles_from_data=True)
bar.set_categories(cats)
bar.legend.position = 'r'
bar.varyColors = False
ws.add_chart(bar, 'A23')

# Doughnut chart Sources Mix
pie = DoughnutChart()
pie.title = 'Sources Mix'
pie.holeSize = 55
pie.height = 7.0
pie.width = 8.0
labels = Reference(wb['Dashboard Data'], min_col=8, min_row=2, max_row=4)
vals = Reference(wb['Dashboard Data'], min_col=9, min_row=1, max_row=4)
pie.add_data(vals, titles_from_data=True)
pie.set_categories(labels)
pie.dataLabels = DataLabelList()
pie.dataLabels.showPercent = True
pie.legend.position = 'r'
ws.add_chart(pie, 'I23')

# ---------------------- Decision gates ----------------------
section_header(36, 'Decision gates and closing pathway')
for r in range(37, 44):
    for c in range(1, 16):
        ws.cell(r, c).fill = fill_light
headers2 = ['Gate', 'Current View', 'Target / Rule', 'Status', 'Source', 'Committee Readout']
cols = [1, 5, 8, 10, 12, 14]
# merge blocks width mapping
ranges = ['A37:D37', 'E37:G37', 'H37:I37', 'J37:K37', 'L37:M37', 'N37:O37']
for rng, h in zip(ranges, headers2):
    ws.merge_cells(rng)
    ws[rng.split(':')[0]] = h
    ws[rng.split(':')[0]].fill = fill_navy
    ws[rng.split(':')[0]].font = font_white
    ws[rng.split(':')[0]].alignment = center

gate_rows = [
    ('Funding gap', "=IF('Dashboard Data'!X3<=0,ABS('Dashboard Data'!X3),0)", '€0.0m unresolved gap', "='Dashboard Data'!X20", 'Sources & Uses', 'Must be closed or explicitly funded'),
    ('Conditions precedent', "='Dashboard Data'!X11", '0 open items', "='Dashboard Data'!X21", 'CP Checklist', 'Open items block unconditional approval'),
    ('Maintenance covenants', "='Dashboard Data'!X16", '100% pass rate', "='Dashboard Data'!X22", 'Maintenance Covenants', 'Current screen is supportive'),
    ('Negotiation closure', "='Dashboard Data'!X19", '>=80% closure', '=IF(\'Dashboard Data\'!X19>=0.8,"On track","Open")', 'Term Sheet Summary', 'Commercial work remains active'),
    ('Model and returns', "='Dashboard Data'!X7", 'Base case IRR retained', '=IF(\'Dashboard Data\'!X7>=0.25,"Supportive","Review")', 'Returns', 'Economics remain investable'),
    ('Security / DD readiness', 'In progress', 'DD + security perfected', 'Open', 'Committee Summary', 'Proceed with conditions only'),
]
for idx, row in enumerate(gate_rows, start=38):
    blocks = [
        ('A','D', row[0]), ('E','G', row[1]), ('H','I', row[2]), ('J','K', row[3]), ('L','M', row[4]), ('N','O', row[5])
    ]
    for start_col, end_col, val in blocks:
        ws.merge_cells(f'{start_col}{idx}:{end_col}{idx}')
        cell = ws[f'{start_col}{idx}']
        cell.value = val
        cell.fill = fill_light
        cell.font = font_body
        cell.alignment = left if start_col in ['A','N'] else center
    # number formats
    ws[f'E{idx}'].number_format = '€0.0'
    if idx == 41:
        ws[f'E{idx}'].number_format = '0.0%'
    if idx == 42:
        ws[f'E{idx}'].number_format = '0.0%'
    # color status cell
    status_text = ws[f'J{idx}'].value
    # keep formula-based cells neutral; apply fills after openpyxl save? static approximate by row
    if idx in [38, 39, 43]:
        fill = fill_red
        font = font_red
    elif idx in [40, 42]:
        fill = fill_green
        font = font_green
    else:
        fill = fill_amber
        font = font_amber
    for c in range(ws[f'J{idx}'].column, ws[f'K{idx}'].column + 1):
        ws.cell(idx, c).fill = fill
        ws.cell(idx, c).font = font
        ws.cell(idx, c).alignment = center

# ---------------------- Timeline ----------------------
section_header(46, 'Indicative committee-to-close timeline')
for r in range(47, 53):
    for c in range(1, 16):
        ws.cell(r, c).fill = fill_light

# headers
for rng, h in zip(['A47:C47','D47:F47','G47:I47','J47:L47','M47:O47'], ['Phase','Objective','Primary Deliverable','Owner','Indicative Timing']):
    ws.merge_cells(rng)
    ws[rng.split(':')[0]] = h
    ws[rng.split(':')[0]].fill = fill_navy
    ws[rng.split(':')[0]].font = font_white
    ws[rng.split(':')[0]].alignment = center

timeline = [
    ('IC review', 'Confirm conditional support', 'Committee feedback and action list', 'Board / IC', 'Week 0'),
    ('Diligence close-out', 'Resolve technical, legal and E&S gaps', 'Final DD pack', 'Advisors / CFO', 'Weeks 1-3'),
    ('Documentation', 'Close term sheet and facility documents', 'Near-final debt docs', 'Counsel / Lenders', 'Weeks 2-4'),
    ('CP closure', 'Complete documentary and evidence package', 'Drawdown-ready CP binder', 'Borrower / Sponsor', 'Weeks 3-5'),
    ('Financial close', 'Authorize signing and first utilisation', 'Signed close pack', 'All parties', 'Weeks 5-6'),
]
for idx, row in enumerate(timeline, start=48):
    for rng, val in zip(['A:C','D:F','G:I','J:L','M:O'], row):
        start_col, end_col = rng.split(':')
        ws.merge_cells(f'{start_col}{idx}:{end_col}{idx}')
        ws[f'{start_col}{idx}'] = val
        ws[f'{start_col}{idx}'].font = font_body
        ws[f'{start_col}{idx}'].alignment = left if rng != 'M:O' else center
        ws[f'{start_col}{idx}'].fill = fill_light

# ---------------------- Quick links ----------------------
section_header(54, 'Navigation')
links = [
    ('A55:C56', 'Go to Cover', 'Cover'),
    ('D55:F56', 'Go to Executive Dashboard', 'Executive Dashboard'),
    ('G55:I56', 'Go to Sources & Uses', 'Sources & Uses'),
    ('J55:L56', 'Go to Returns', 'Returns'),
    ('M55:O56', 'Go to CP Checklist', 'CP Checklist'),
]
for rng, label, target in links:
    ws.merge_cells(rng)
    c = ws[rng.split(':')[0]]
    c.value = label
    c.font = Font(name='Calibri', size=10, bold=True, color=WHITE)
    c.fill = fill_teal
    c.alignment = center
    c.hyperlink = f"#'{target}'!A1"
    start_col = ws[rng.split(':')[0]].column
    start_row = ws[rng.split(':')[0]].row
    end_col = ws[rng.split(':')[1]].column
    end_row = ws[rng.split(':')[1]].row
    for rr in range(start_row, end_row + 1):
        for cc in range(start_col, end_col + 1):
            ws.cell(rr, cc).fill = fill_teal
            ws.cell(rr, cc).border = box_border

# Footer note
ws.merge_cells('A58:O59')
ws['A58'] = 'Board / IC dashboard notes: this layer is intentionally simplified for committee use. Detailed operational build, source tabs and static closing schedules remain in the underlying workbook.'
ws['A58'].font = font_small
ws['A58'].fill = fill_amber
ws['A58'].alignment = left

# Print setup
ws.page_setup.orientation = 'landscape'
ws.page_setup.fitToPage = True
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.page_margins.left = 0.35
ws.page_margins.right = 0.35
ws.page_margins.top = 0.45
ws.page_margins.bottom = 0.45
ws.oddFooter.center.text = 'TITAN v5.0 | Board & IC Dashboard | Confidential | Page &[Page] of &[Pages]'

# Add link from navigation sheet if present
if 'Index & Navigation' in wb.sheetnames:
    nav = wb['Index & Navigation']
    next_row = nav.max_row + 1
    nav.cell(next_row, 1, 'Board & IC Dashboard')
    nav.cell(next_row, 2, 'Presentation dashboard for board and investment committee use')
    nav.cell(next_row, 3, 'Headline metrics / downside / decision gates')
    nav.cell(next_row, 4, 'Finance')
    nav.cell(next_row, 5, 'v5.0-board-ic')
    nav.cell(next_row, 6, 'Added')
    nav.cell(next_row, 1).hyperlink = "#'Board & IC Dashboard'!A1"
    nav.cell(next_row, 1).style = 'Hyperlink'

if 'Version Control & Audit' in wb.sheetnames:
    vc = wb['Version Control & Audit']
    next_row = vc.max_row + 1
    vc.cell(next_row, 1, 'v5.0-board-ic')
    vc.cell(next_row, 2, '2026-03-28')
    vc.cell(next_row, 3, 'OpenAI')
    vc.cell(next_row, 4, 'Added board / IC presentation dashboard with cleaner visuals and simplified committee framing')
    vc.cell(next_row, 5, 'Internal')
    vc.cell(next_row, 6, 'Added')

wb.save(OUT)
print(OUT)
